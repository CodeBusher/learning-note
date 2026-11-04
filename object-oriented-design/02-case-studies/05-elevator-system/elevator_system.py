"""Elevator system: a discrete-time simulation of a bank of elevator cars.

Time advances in ticks. On every call to ``ElevatorSystem.step()`` each car
does exactly one thing: moves one floor, counts down its door timer, or
decides where to go next. Because nothing depends on wall-clock time, every
scenario is deterministic and easy to test.

Design summary
--------------
* ``ElevatorCar``      - one car: its stops, its state machine, its doors.
* ``DispatchStrategy`` - Strategy pattern: which car answers a hall call.
* ``EventBus``         - Observer pattern: cars publish what happened.
* ``ElevatorSystem``   - the group controller (facade) that owns the cars,
                         the lit hall buttons and the building operating mode.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Protocol, Sequence


# --------------------------------------------------------------------------
# Small value types
# --------------------------------------------------------------------------


class Direction(Enum):
    UP = 1
    DOWN = -1

    @property
    def opposite(self) -> Direction:
        return Direction.DOWN if self is Direction.UP else Direction.UP


class CarState(Enum):
    IDLE = "idle"
    MOVING_UP = "moving up"
    MOVING_DOWN = "moving down"
    DOORS_OPEN = "doors open"
    OUT_OF_SERVICE = "out of service"


class DoorState(Enum):
    OPEN = "open"
    CLOSED = "closed"


# The whole state machine in one table. Anything not listed is a bug.
ALLOWED_TRANSITIONS: dict[CarState, frozenset[CarState]] = {
    CarState.IDLE: frozenset(
        {CarState.MOVING_UP, CarState.MOVING_DOWN, CarState.DOORS_OPEN, CarState.OUT_OF_SERVICE}
    ),
    CarState.MOVING_UP: frozenset({CarState.DOORS_OPEN, CarState.IDLE}),
    CarState.MOVING_DOWN: frozenset({CarState.DOORS_OPEN, CarState.IDLE}),
    CarState.DOORS_OPEN: frozenset({CarState.IDLE, CarState.OUT_OF_SERVICE}),
    CarState.OUT_OF_SERVICE: frozenset({CarState.IDLE}),
}


class OperatingMode(Enum):
    NORMAL = "normal"
    UP_PEAK = "up-peak"
    DOWN_PEAK = "down-peak"
    FIRE_RECALL = "fire recall"


class ElevatorError(Exception):
    """Base class for errors raised by the elevator system."""


class InvalidTransition(ElevatorError):
    """A car was asked to move between two states the state machine forbids."""


class SafetyInterlockError(ElevatorError):
    """A command would have moved a car with its doors open."""


# --------------------------------------------------------------------------
# Events (Observer pattern)
# --------------------------------------------------------------------------


class EventKind(Enum):
    STATE_CHANGED = "state changed"
    DOORS_OPENED = "doors opened"
    DOORS_CLOSED = "doors closed"
    HALL_CALL_SERVED = "hall call served"
    OVERLOAD = "overload"


@dataclass(frozen=True)
class CarEvent:
    """Something that happened to one car at one tick."""

    tick: int
    car_id: int
    kind: EventKind
    floor: int
    direction: Direction | None = None
    state: CarState | None = None


Handler = Callable[[CarEvent], None]


class EventBus:
    """A minimal synchronous publish/subscribe hub."""

    def __init__(self) -> None:
        self._handlers: list[tuple[EventKind | None, Handler]] = []

    def subscribe(self, handler: Handler, kind: EventKind | None = None) -> None:
        """Register ``handler`` for one kind of event, or for all if ``kind`` is None."""
        self._handlers.append((kind, handler))

    def publish(self, event: CarEvent) -> None:
        for kind, handler in list(self._handlers):
            if kind is None or kind is event.kind:
                handler(event)


# --------------------------------------------------------------------------
# The elevator car
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CarStatus:
    """Read-only snapshot of a car, used by displays and dispatch."""

    car_id: int
    floor: int
    state: CarState
    direction: Direction | None
    stops: tuple[int, ...]

    def display(self) -> str:
        arrow = {Direction.UP: "up", Direction.DOWN: "down", None: "-"}[self.direction]
        return f"Car {self.car_id}: floor {self.floor:>2} | {self.state.value:<14} | heading {arrow}"


HallKey = tuple[int, Direction]


class ElevatorCar:
    """One elevator car, scheduled with the LOOK ("elevator") algorithm.

    The car keeps two kinds of stops:
    * car calls - floors pressed inside the car (no direction attached);
    * hall calls - (floor, direction) pairs assigned by the group controller.

    A hall call is only picked up when the car is travelling in the caller's
    direction, or when the car turns around at that floor. That is what stops a
    car going up from collecting someone who wants to go down.
    """

    def __init__(
        self,
        car_id: int,
        min_floor: int,
        max_floor: int,
        *,
        served_floors: Iterable[int] | None = None,
        door_dwell_ticks: int = 2,
        capacity_kg: int = 1000,
        ignore_opposite_car_calls: bool = True,
        bus: EventBus | None = None,
    ) -> None:
        if min_floor >= max_floor:
            raise ValueError("a car needs at least two floors")
        if door_dwell_ticks < 1:
            raise ValueError("door_dwell_ticks must be at least 1")
        self.car_id = car_id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.served_floors = frozenset(
            served_floors if served_floors is not None else range(min_floor, max_floor + 1)
        )
        self.door_dwell_ticks = door_dwell_ticks
        self.capacity_kg = capacity_kg
        self.ignore_opposite_car_calls = ignore_opposite_car_calls
        self.bus = bus or EventBus()

        self.floor = min_floor
        self.state = CarState.IDLE
        self.door = DoorState.CLOSED
        self.direction: Direction | None = None
        self.load_kg = 0
        self.recalled = False
        self._recall_floor: int | None = None
        self._car_stops: set[int] = set()
        self._hall_stops: set[HallKey] = set()
        self._door_timer = 0
        self._tick = 0

    # ---- queries -------------------------------------------------------

    @property
    def in_service(self) -> bool:
        return self.state is not CarState.OUT_OF_SERVICE

    @property
    def has_work(self) -> bool:
        return bool(self._car_stops or self._hall_stops)

    @property
    def workload(self) -> int:
        return len(self._car_stops) + len(self._hall_stops)

    @property
    def hall_stops(self) -> frozenset[HallKey]:
        return frozenset(self._hall_stops)

    def can_serve(self, floor: int) -> bool:
        return self.in_service and not self.recalled and floor in self.served_floors

    def stop_floors(self) -> set[int]:
        return self._car_stops | {floor for floor, _ in self._hall_stops}

    def has_stops_ahead(self, direction: Direction) -> bool:
        return any((f - self.floor) * direction.value > 0 for f in self.stop_floors())

    def furthest_stop(self, direction: Direction) -> int:
        """Furthest pending stop in ``direction``, or the current floor if none."""
        ahead = [f for f in self.stop_floors() if (f - self.floor) * direction.value > 0]
        if not ahead:
            return self.floor
        return max(ahead) if direction is Direction.UP else min(ahead)

    def status(self) -> CarStatus:
        return CarStatus(self.car_id, self.floor, self.state, self.direction, tuple(sorted(self.stop_floors())))

    # ---- commands from passengers and the controller -------------------

    def press_button(self, floor: int) -> bool:
        """A passenger inside the car pressed ``floor``. Returns True if accepted."""
        self._check_floor(floor)
        if self.recalled or not self.in_service:
            return False
        if floor == self.floor and self.state is CarState.DOORS_OPEN:
            self._door_timer = self.door_dwell_ticks  # behaves like "door open" button
            return True
        if floor == self.floor and self.state is CarState.IDLE:
            self._car_stops.add(floor)
            return True
        if (
            self.ignore_opposite_car_calls
            and self.direction is not None
            and (floor - self.floor) * self.direction.value <= 0
            and self.has_stops_ahead(self.direction)
        ):
            return False  # committed to the other direction: likely a mis-press
        self._car_stops.add(floor)
        return True

    def add_hall_call(self, floor: int, direction: Direction) -> None:
        """The controller assigned the hall call (floor, direction) to this car."""
        self._check_floor(floor)
        if (
            self.state is CarState.DOORS_OPEN
            and floor == self.floor
            and self.direction in (None, direction)
        ):
            # Already standing here with doors open, heading the right way.
            self.direction = direction
            self._door_timer = self.door_dwell_ticks
            self._emit(EventKind.HALL_CALL_SERVED, direction=direction)
            return
        self._hall_stops.add((floor, direction))

    def cancel_hall_call(self, floor: int, direction: Direction) -> bool:
        """Another car answered this call first; drop it. Returns True if it was ours."""
        if (floor, direction) not in self._hall_stops:
            return False
        self._hall_stops.discard((floor, direction))
        return True

    def park_at(self, floor: int) -> None:
        """Send an idle car to a parking floor (used by traffic modes)."""
        self._check_floor(floor)
        self._car_stops.add(floor)

    def set_load(self, kg: int) -> None:
        """Update the reading from the load-weighing sensor."""
        if kg < 0:
            raise ValueError("load cannot be negative")
        self.load_kg = kg

    def recall_to(self, floor: int) -> list[HallKey]:
        """Fire service Phase I: drop all calls and return to ``floor``.

        Returns the hall calls this car was holding so the controller can
        account for them.
        """
        self._check_floor(floor)
        orphaned = sorted(self._hall_stops, key=lambda k: (k[0], k[1].value))
        self._hall_stops.clear()
        self.recalled = True
        self._recall_floor = floor
        if self.floor == floor and self.state is CarState.DOORS_OPEN:
            self._car_stops = set()
        else:
            self._car_stops = {floor}
            if self.state is CarState.DOORS_OPEN:
                self._door_timer = 1  # close at once, even if dwell time remains
        return orphaned

    def release_recall(self) -> None:
        self.recalled = False
        self._recall_floor = None
        if self.state is CarState.DOORS_OPEN:
            self._door_timer = self.door_dwell_ticks

    def take_out_of_service(self) -> list[HallKey]:
        """Maintenance key switch. Only allowed when the car is stopped."""
        self._require_transition(CarState.OUT_OF_SERVICE)
        orphaned = sorted(self._hall_stops, key=lambda k: (k[0], k[1].value))
        self._hall_stops.clear()
        self._car_stops.clear()
        if self.door is DoorState.OPEN:
            self.door = DoorState.CLOSED
            self._emit(EventKind.DOORS_CLOSED)
        self.direction = None
        self._set_state(CarState.OUT_OF_SERVICE)
        return orphaned

    def return_to_service(self) -> None:
        self._set_state(CarState.IDLE)

    # ---- the simulation tick -------------------------------------------

    def step(self, tick: int) -> None:
        self._tick = tick
        match self.state:
            case CarState.OUT_OF_SERVICE:
                return
            case CarState.DOORS_OPEN:
                self._step_doors()
            case CarState.IDLE:
                self._decide()
            case CarState.MOVING_UP | CarState.MOVING_DOWN:
                self._step_moving()

    def _step_doors(self) -> None:
        if self.recalled and self.floor == self._recall_floor:
            return  # parked for firefighters with doors open
        self._door_timer -= 1
        if self._door_timer > 0:
            return
        if self.load_kg > self.capacity_kg:
            self._door_timer = 1  # interlock: an overloaded car keeps its doors open
            self._emit(EventKind.OVERLOAD)
            return
        self.door = DoorState.CLOSED
        self._emit(EventKind.DOORS_CLOSED)
        self._set_state(CarState.IDLE)
        self._decide()

    def _step_moving(self) -> None:
        assert self.direction is not None
        self.floor += self.direction.value
        if self._should_stop_here():
            self._open_doors()
        elif not self.has_stops_ahead(self.direction):
            # The stops ahead were cancelled (another car took them).
            self._set_state(CarState.IDLE)
            self._decide()

    def _decide(self) -> None:
        """Called whenever the car is stopped with doors closed."""
        if not self.has_work:
            self.direction = None
            return
        if self._should_stop_here():
            self._open_doors()
            return
        self.direction = self._choose_direction()
        self._set_state(CarState.MOVING_UP if self.direction is Direction.UP else CarState.MOVING_DOWN)

    # ---- LOOK scheduling ----------------------------------------------

    def _should_stop_here(self) -> bool:
        floor, d = self.floor, self.direction
        if floor in self._car_stops:
            return True
        if d is None:
            return any(f == floor for f, _ in self._hall_stops)
        if (floor, d) in self._hall_stops:
            return True
        # Turn-around point: someone wants the other way and nothing is beyond us.
        return (floor, d.opposite) in self._hall_stops and not self.has_stops_ahead(d)

    def _choose_direction(self) -> Direction:
        d = self.direction
        if d is not None and self.has_stops_ahead(d):
            return d
        if d is not None and self.has_stops_ahead(d.opposite):
            return d.opposite
        nearest = min(self.stop_floors(), key=lambda f: (abs(f - self.floor), -f))
        return Direction.UP if nearest >= self.floor else Direction.DOWN

    def _departure_direction(self) -> Direction | None:
        """Which way the car will leave this floor (what the hall lantern shows)."""
        floor, d = self.floor, self.direction
        if d is None:
            for candidate in (Direction.UP, Direction.DOWN):
                if (floor, candidate) in self._hall_stops:
                    return candidate
            return None
        if (floor, d) in self._hall_stops or self.has_stops_ahead(d):
            return d
        if (floor, d.opposite) in self._hall_stops or self.has_stops_ahead(d.opposite):
            return d.opposite
        return None

    def _open_doors(self) -> None:
        self._car_stops.discard(self.floor)
        depart = self._departure_direction()
        if depart is not None:
            self._hall_stops.discard((self.floor, depart))
        self.direction = depart
        self._set_state(CarState.DOORS_OPEN)
        self.door = DoorState.OPEN
        self._door_timer = self.door_dwell_ticks
        self._emit(EventKind.DOORS_OPENED, direction=depart)
        if depart is not None and not self.recalled:
            self._emit(EventKind.HALL_CALL_SERVED, direction=depart)

    # ---- state machine plumbing ---------------------------------------

    def _require_transition(self, new: CarState) -> None:
        if new not in ALLOWED_TRANSITIONS[self.state]:
            raise InvalidTransition(f"car {self.car_id}: {self.state.value} -> {new.value}")

    def _set_state(self, new: CarState) -> None:
        self._require_transition(new)
        if new in (CarState.MOVING_UP, CarState.MOVING_DOWN) and self.door is DoorState.OPEN:
            raise SafetyInterlockError(f"car {self.car_id} cannot move with doors open")
        self.state = new
        self._emit(EventKind.STATE_CHANGED, state=new)

    def _check_floor(self, floor: int) -> None:
        if floor not in self.served_floors:
            raise ValueError(f"car {self.car_id} does not serve floor {floor}")

    def _emit(self, kind: EventKind, *, direction: Direction | None = None, state: CarState | None = None) -> None:
        self.bus.publish(CarEvent(self._tick, self.car_id, kind, self.floor, direction, state))


# --------------------------------------------------------------------------
# Dispatch strategies (Strategy pattern)
# --------------------------------------------------------------------------


class DispatchStrategy(Protocol):
    """Pick which car answers a hall call. ``cars`` is never empty."""

    def choose(self, cars: Sequence[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar: ...


class NearestCarStrategy:
    """Closest car by floor distance, ignoring where it is heading."""

    def choose(self, cars: Sequence[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar:
        return min(cars, key=lambda c: (abs(c.floor - floor), c.car_id))


class LeastLoadedStrategy:
    """Car with the fewest pending stops; distance breaks ties."""

    def choose(self, cars: Sequence[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar:
        return min(cars, key=lambda c: (c.workload, abs(c.floor - floor), c.car_id))


def estimate_arrival_ticks(car: ElevatorCar, floor: int, direction: Direction) -> int:
    """Rough time for ``car`` to reach a hall call, following its LOOK route."""
    stop_cost = car.door_dwell_ticks + 1
    d = car.direction
    if d is None or not car.has_work:
        return abs(floor - car.floor)
    call_ahead = (floor - car.floor) * d.value >= 0
    if call_ahead and direction is d:
        # On the way: pay for the stops between here and there.
        between = [f for f in car.stop_floors() if 0 < (f - car.floor) * d.value < (floor - car.floor) * d.value]
        return abs(floor - car.floor) + len(between) * stop_cost
    # Must finish this sweep first, then come back.
    turn = car.furthest_stop(d)
    if call_ahead:
        turn = max(turn, floor) if d is Direction.UP else min(turn, floor)
    travel = abs(turn - car.floor) + abs(turn - floor)
    return travel + car.workload * stop_cost


class EstimatedTimeStrategy:
    """Direction-aware cost: lowest estimated arrival time wins."""

    def choose(self, cars: Sequence[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar:
        return min(cars, key=lambda c: (estimate_arrival_ticks(c, floor, direction), c.car_id))


# --------------------------------------------------------------------------
# The group controller
# --------------------------------------------------------------------------


@dataclass
class HallCall:
    floor: int
    direction: Direction
    registered_at: int
    car_id: int | None = None


class ElevatorSystem:
    """Facade and group controller for a bank of cars serving one building."""

    def __init__(
        self,
        num_floors: int,
        num_cars: int = 0,
        *,
        strategy: DispatchStrategy | None = None,
        door_dwell_ticks: int = 2,
        lobby: int = 0,
        cars: Sequence[ElevatorCar] | None = None,
    ) -> None:
        if num_floors < 2:
            raise ValueError("a building needs at least two floors")
        self.min_floor = 0
        self.max_floor = num_floors - 1
        self.lobby = lobby
        self.bus = EventBus()
        if cars is None:
            if num_cars < 1:
                raise ValueError("need at least one car")
            cars = [
                ElevatorCar(i, self.min_floor, self.max_floor, door_dwell_ticks=door_dwell_ticks)
                for i in range(num_cars)
            ]
        self.cars = list(cars)
        for car in self.cars:
            car.bus = self.bus
        self._cars_by_id = {car.car_id: car for car in self.cars}
        self.strategy: DispatchStrategy = strategy or EstimatedTimeStrategy()
        self.mode = OperatingMode.NORMAL
        self.tick = 0
        self.wait_times: list[int] = []
        self._hall_calls: dict[HallKey, HallCall] = {}
        # Re-entrant because event handlers run inside step() and call back in.
        self._lock = threading.RLock()
        self.bus.subscribe(self._on_hall_call_served, EventKind.HALL_CALL_SERVED)

    # ---- passenger-facing API -----------------------------------------

    def press_hall_button(self, floor: int, direction: Direction) -> int | None:
        """Register a hall call. Returns the id of the assigned car, if any."""
        with self._lock:
            self._validate_hall_button(floor, direction)
            if self.mode is OperatingMode.FIRE_RECALL:
                return None  # hall buttons are disabled during recall
            key = (floor, direction)
            if key in self._hall_calls:
                return self._hall_calls[key].car_id  # pressing again changes nothing
            call = HallCall(floor, direction, registered_at=self.tick)
            self._hall_calls[key] = call  # register before assigning: the car may serve it at once
            self._assign(call)
            return call.car_id

    def press_car_button(self, car_id: int, floor: int) -> bool:
        with self._lock:
            return self.car(car_id).press_button(floor)

    def lit_hall_buttons(self) -> set[HallKey]:
        with self._lock:
            return set(self._hall_calls)

    def assigned_car(self, floor: int, direction: Direction) -> int | None:
        with self._lock:
            call = self._hall_calls.get((floor, direction))
            return call.car_id if call else None

    # ---- operator-facing API ------------------------------------------

    def car(self, car_id: int) -> ElevatorCar:
        try:
            return self._cars_by_id[car_id]
        except KeyError:
            raise ValueError(f"no car {car_id}") from None

    def set_strategy(self, strategy: DispatchStrategy) -> None:
        with self._lock:
            self.strategy = strategy

    def set_mode(self, mode: OperatingMode) -> None:
        with self._lock:
            if mode is OperatingMode.FIRE_RECALL:
                raise ValueError("use activate_fire_recall() so a recall floor is chosen")
            if self.mode is OperatingMode.FIRE_RECALL:
                raise ValueError("clear the fire recall first")
            self.mode = mode

    def activate_fire_recall(self, recall_floor: int | None = None) -> None:
        """Phase I recall: cancel every call and send all cars to the recall floor."""
        with self._lock:
            floor = self.lobby if recall_floor is None else recall_floor
            self.mode = OperatingMode.FIRE_RECALL
            self._hall_calls.clear()
            for car in self.cars:
                if car.in_service:
                    car.recall_to(floor)

    def clear_fire_recall(self) -> None:
        with self._lock:
            self.mode = OperatingMode.NORMAL
            for car in self.cars:
                if car.recalled:
                    car.release_recall()

    def take_car_out_of_service(self, car_id: int) -> None:
        with self._lock:
            orphaned = self.car(car_id).take_out_of_service()
            for key in orphaned:
                call = self._hall_calls.get(key)
                if call is not None:
                    call.car_id = None
                    self._assign(call)

    def return_car_to_service(self, car_id: int) -> None:
        with self._lock:
            self.car(car_id).return_to_service()

    # ---- simulation ----------------------------------------------------

    def step(self) -> None:
        with self._lock:
            self.tick += 1
            for call in list(self._hall_calls.values()):
                if call.car_id is None:
                    self._assign(call)
            for car in self.cars:
                car.step(self.tick)
            self._park_idle_cars()

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()

    def run_until_idle(self, max_ticks: int = 1_000) -> int:
        """Step until no calls are pending and every car has settled."""
        for elapsed in range(1, max_ticks + 1):
            self.step()
            if self.is_idle():
                return elapsed
        raise ElevatorError(f"system still busy after {max_ticks} ticks")

    def is_idle(self) -> bool:
        with self._lock:
            if self._hall_calls:
                return False
            for car in self.cars:
                if car.state is CarState.OUT_OF_SERVICE:
                    continue
                if car.recalled and car.state is CarState.DOORS_OPEN and not car.has_work:
                    continue
                if car.state is not CarState.IDLE or car.has_work:
                    return False
            return True

    def status(self) -> list[CarStatus]:
        with self._lock:
            return [car.status() for car in self.cars]

    # ---- internals -----------------------------------------------------

    def _validate_hall_button(self, floor: int, direction: Direction) -> None:
        if not self.min_floor <= floor <= self.max_floor:
            raise ValueError(f"no floor {floor}")
        if floor == self.max_floor and direction is Direction.UP:
            raise ValueError("the top floor has no up button")
        if floor == self.min_floor and direction is Direction.DOWN:
            raise ValueError("the bottom floor has no down button")

    def _assign(self, call: HallCall) -> None:
        eligible = [car for car in self.cars if car.can_serve(call.floor)]
        if not eligible:
            return  # stays unassigned; retried every tick
        chosen = self.strategy.choose(eligible, call.floor, call.direction)
        call.car_id = chosen.car_id
        chosen.add_hall_call(call.floor, call.direction)

    def _on_hall_call_served(self, event: CarEvent) -> None:
        assert event.direction is not None
        key = (event.floor, event.direction)
        call = self._hall_calls.pop(key, None)
        if call is None:
            return
        self.wait_times.append(event.tick - call.registered_at)
        if call.car_id is not None and call.car_id != event.car_id:
            # Another car got there first: release the assigned one.
            self.car(call.car_id).cancel_hall_call(*key)

    def _park_idle_cars(self) -> None:
        if self.mode not in (OperatingMode.UP_PEAK, OperatingMode.DOWN_PEAK):
            return
        available = [c for c in self.cars if c.in_service and not c.recalled]
        for index, car in enumerate(available):
            if car.state is CarState.IDLE and not car.has_work:
                home = self._home_floor(index, len(available))
                if car.floor != home and home in car.served_floors:
                    car.park_at(home)

    def _home_floor(self, index: int, count: int) -> int:
        if self.mode is OperatingMode.UP_PEAK:
            return self.lobby
        spacing = max(1, (self.max_floor - self.min_floor) // (2 * count))
        return max(self.min_floor, self.max_floor - index * spacing)


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------


def demo() -> None:
    system = ElevatorSystem(num_floors=10, num_cars=3)
    log: list[str] = []
    system.bus.subscribe(
        lambda e: log.append(f"t={e.tick:>2} car {e.car_id} opened doors at floor {e.floor}"),
        EventKind.DOORS_OPENED,
    )

    # Spread the cars out first so dispatch has a real choice.
    system.car(1).park_at(5)
    system.car(2).park_at(9)
    system.run_until_idle()
    log.clear()
    print("Starting positions:")
    for s in system.status():
        print("  " + s.display())

    print("\nHall calls:")
    for floor, direction in [(4, Direction.UP), (8, Direction.DOWN), (1, Direction.UP)]:
        car_id = system.press_hall_button(floor, direction)
        print(f"  floor {floor} {direction.name:<4} -> car {car_id}")

    system.run(3)
    print("\nPassengers board and choose floors:")
    for car_id, floor in [(1, 7), (2, 0), (0, 3)]:
        print(f"  car {car_id} button {floor}: {'accepted' if system.press_car_button(car_id, floor) else 'ignored'}")
    print(f"  car 2 button 9 while heading down: "
          f"{'accepted' if system.press_car_button(2, 9) else 'ignored'}")

    ticks = system.run_until_idle()
    print(f"\nAll calls served after {ticks} more ticks. Door openings:")
    for line in log:
        print("  " + line)
    print(f"Hall-call wait times (ticks): {system.wait_times}")

    print("\nFire alarm! Recalling every car to the lobby.")
    system.press_hall_button(6, Direction.DOWN)
    system.run(1)
    system.activate_fire_recall()
    system.run_until_idle()
    for s in system.status():
        print("  " + s.display())


if __name__ == "__main__":
    demo()
