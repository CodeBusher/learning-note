"""Competing designs for the elevator system, each small and runnable.

1. Per-car scheduling: FCFS vs SSTF vs SCAN vs LOOK (with a starvation demo).
2. Multi-car dispatch: the three strategies from elevator_system.py, measured.
3. Car state: the State pattern version of a car.
4. Event flow: a polling controller vs an observer-based one.
5. Hall calls vs car calls: one mixed queue vs typed calls vs destination dispatch.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Callable, Protocol, Sequence

from elevator_system import (
    Direction,
    DispatchStrategy,
    ElevatorCar,
    ElevatorSystem,
    EstimatedTimeStrategy,
    EventKind,
    LeastLoadedStrategy,
    NearestCarStrategy,
)


# ==========================================================================
# 1. Per-car scheduling
# ==========================================================================


@dataclass(frozen=True)
class Request:
    floor: int
    arrival: int


class Scheduler(Protocol):
    name: str

    def next_target(self, floor: int, direction: int, pending: Sequence[Request]) -> int: ...


class FcfsScheduler:
    """Serve requests strictly in arrival order."""

    name = "FCFS"

    def next_target(self, floor: int, direction: int, pending: Sequence[Request]) -> int:
        return min(pending, key=lambda r: r.arrival).floor


class SstfScheduler:
    """Shortest seek time first: always go to the nearest pending floor."""

    name = "SSTF"

    def next_target(self, floor: int, direction: int, pending: Sequence[Request]) -> int:
        return min(pending, key=lambda r: (abs(r.floor - floor), r.arrival)).floor


class ScanScheduler:
    """Sweep to the very end of the shaft, then reverse (disk-arm SCAN)."""

    name = "SCAN"

    def __init__(self, bottom: int, top: int) -> None:
        self.bottom, self.top = bottom, top

    def next_target(self, floor: int, direction: int, pending: Sequence[Request]) -> int:
        d = direction or 1
        end = self.top if d > 0 else self.bottom
        if floor != end:
            return end
        return self.bottom if d > 0 else self.top


class LookScheduler:
    """Like SCAN, but reverse at the last request instead of the shaft end."""

    name = "LOOK"

    def next_target(self, floor: int, direction: int, pending: Sequence[Request]) -> int:
        d = direction or 1
        ahead = [r.floor for r in pending if (r.floor - floor) * d > 0]
        if ahead:
            return min(ahead, key=lambda f: abs(f - floor))
        behind = [r.floor for r in pending if (r.floor - floor) * d < 0]
        return min(behind, key=lambda f: abs(f - floor)) if behind else floor


@dataclass
class SingleCarResult:
    served: list[tuple[Request, int]] = field(default_factory=list)  # (request, served_at)
    unserved: list[Request] = field(default_factory=list)
    floors_travelled: int = 0

    def waits(self) -> list[int]:
        return [served_at - r.arrival for r, served_at in self.served]

    def wait_for(self, floor: int) -> int | None:
        for r, served_at in self.served:
            if r.floor == floor:
                return served_at - r.arrival
        return None


def simulate_single_car(
    scheduler: Scheduler, arrivals: dict[int, list[int]], ticks: int, start_floor: int = 0
) -> SingleCarResult:
    """One car, one floor per tick, everyone at the current floor is served on arrival."""
    result = SingleCarResult()
    floor, direction = start_floor, 0
    pending: list[Request] = []
    for t in range(ticks):
        pending.extend(Request(f, t) for f in arrivals.get(t, []))
        here = [r for r in pending if r.floor == floor]
        for r in here:
            result.served.append((r, t))
        pending = [r for r in pending if r.floor != floor]
        if not pending:
            direction = 0
            continue
        target = scheduler.next_target(floor, direction, pending)
        step = (target > floor) - (target < floor)
        if step:
            floor += step
            direction = step
            result.floors_travelled += 1
    result.unserved = pending
    return result


def starvation_arrivals(ticks: int = 40) -> dict[int, list[int]]:
    """One request at floor 9, then a steady trickle around floors 2-4."""
    arrivals: dict[int, list[int]] = {0: [9, 2]}
    for t in range(1, ticks):
        arrivals.setdefault(t, []).append(2 if t % 2 else 4)
    return arrivals


def random_arrivals(seed: int, ticks: int = 300, floors: int = 20, rate: float = 0.6) -> dict[int, list[int]]:
    rng = random.Random(seed)
    return {t: [rng.randrange(floors)] for t in range(ticks) if rng.random() < rate}


def compare_schedulers(seeds: Sequence[int] = range(1, 11), floors: int = 20) -> dict[str, tuple[float, int]]:
    """Average wait and single worst wait for each scheduler over several random runs."""
    results: dict[str, tuple[float, int]] = {}
    for scheduler in (FcfsScheduler(), SstfScheduler(), ScanScheduler(0, floors - 1), LookScheduler()):
        waits: list[int] = []
        for seed in seeds:
            waits += simulate_single_car(scheduler, random_arrivals(seed, floors=floors), ticks=2_000).waits()
        results[scheduler.name] = (mean(waits), max(waits))
    return results


# ==========================================================================
# 2. Multi-car dispatch, measured on the real system
# ==========================================================================


def compare_dispatchers(
    seed: int = 7, ticks: int = 400, floors: int = 16, cars: int = 4, call_rate: float = 0.35
) -> dict[str, tuple[float, int]]:
    """Run identical random traffic through each strategy; return (mean wait, max wait)."""
    strategies: dict[str, DispatchStrategy] = {
        "nearest car": NearestCarStrategy(),
        "least loaded": LeastLoadedStrategy(),
        "estimated time": EstimatedTimeStrategy(),
    }
    results: dict[str, tuple[float, int]] = {}
    for name, strategy in strategies.items():
        rng = random.Random(seed)
        system = ElevatorSystem(floors, cars, strategy=strategy)
        waiting: dict[tuple[int, Direction], list[int]] = defaultdict(list)

        def board(event, system=system, waiting=waiting) -> None:
            for destination in waiting.pop((event.floor, event.direction), []):
                system.press_car_button(event.car_id, destination)

        system.bus.subscribe(board, EventKind.HALL_CALL_SERVED)
        for _ in range(ticks):
            if rng.random() < call_rate:
                origin, destination = rng.sample(range(floors), 2)
                direction = Direction.UP if destination > origin else Direction.DOWN
                waiting[(origin, direction)].append(destination)
                system.press_hall_button(origin, direction)
            system.step()
        system.run_until_idle(max_ticks=5_000)
        results[name] = (mean(system.wait_times), max(system.wait_times))
    return results


# ==========================================================================
# 3. Car state with the State pattern
# ==========================================================================


class CarStateBehavior(ABC):
    """One object per state; the car delegates every event to its current state."""

    name = "abstract"

    def press(self, car: StatefulCar, floor: int) -> bool:
        car.stops.add(floor)
        return True

    @abstractmethod
    def tick(self, car: StatefulCar) -> None: ...


class IdleBehavior(CarStateBehavior):
    name = "idle"

    def tick(self, car: StatefulCar) -> None:
        if not car.stops:
            return
        if car.floor in car.stops:
            car.change(DoorsOpenBehavior(car.dwell))
            return
        nearest = min(car.stops, key=lambda f: abs(f - car.floor))
        car.change(MovingBehavior(1 if nearest > car.floor else -1))


class MovingBehavior(CarStateBehavior):
    name = "moving"

    def __init__(self, step: int) -> None:
        self.step = step

    def tick(self, car: StatefulCar) -> None:
        car.floor += self.step
        if car.floor in car.stops:
            car.change(DoorsOpenBehavior(car.dwell))
        elif not any((f - car.floor) * self.step > 0 for f in car.stops):
            car.change(IdleBehavior())


class DoorsOpenBehavior(CarStateBehavior):
    name = "doors open"

    def __init__(self, dwell: int) -> None:
        self.remaining = dwell

    def press(self, car: StatefulCar, floor: int) -> bool:
        if floor == car.floor:
            self.remaining = car.dwell  # hold the doors
            return True
        return super().press(car, floor)

    def tick(self, car: StatefulCar) -> None:
        car.stops.discard(car.floor)
        self.remaining -= 1
        if self.remaining <= 0:
            car.change(IdleBehavior())


class OutOfServiceBehavior(CarStateBehavior):
    name = "out of service"

    def press(self, car: StatefulCar, floor: int) -> bool:
        return False

    def tick(self, car: StatefulCar) -> None:
        pass


class StatefulCar:
    """Context object for the State pattern version."""

    def __init__(self, dwell: int = 2) -> None:
        self.floor = 0
        self.dwell = dwell
        self.stops: set[int] = set()
        self.state: CarStateBehavior = IdleBehavior()
        self.history: list[str] = []

    def press(self, floor: int) -> bool:
        return self.state.press(self, floor)

    def step(self) -> None:
        self.state.tick(self)

    def change(self, new: CarStateBehavior) -> None:
        self.history.append(f"{self.state.name} -> {new.name} @ {self.floor}")
        self.state = new


# ==========================================================================
# 4. Event flow: polling vs observer
# ==========================================================================


class PollingHallPanel:
    """Buttons just light a lamp; someone has to come and look."""

    def __init__(self) -> None:
        self.lamps: set[tuple[int, Direction]] = set()

    def press(self, floor: int, direction: Direction) -> None:
        self.lamps.add((floor, direction))


class PollingController:
    """Scans every panel on each tick and assigns anything new."""

    def __init__(self, panel: PollingHallPanel, scan_every: int = 1) -> None:
        self.panel = panel
        self.scan_every = scan_every
        self.assigned_at: dict[tuple[int, Direction], int] = {}
        self.tick = 0

    def step(self) -> None:
        self.tick += 1
        if self.tick % self.scan_every:
            return
        for key in self.panel.lamps:
            self.assigned_at.setdefault(key, self.tick)


HallListener = Callable[[int, Direction], None]


class ObservableHallPanel:
    """Buttons notify subscribers the moment they are pressed."""

    def __init__(self) -> None:
        self._listeners: list[HallListener] = []

    def subscribe(self, listener: HallListener) -> None:
        self._listeners.append(listener)

    def press(self, floor: int, direction: Direction) -> None:
        for listener in self._listeners:
            listener(floor, direction)


class ListeningController:
    def __init__(self, panel: ObservableHallPanel) -> None:
        self.tick = 0
        self.assigned_at: dict[tuple[int, Direction], int] = {}
        panel.subscribe(self.on_hall_call)

    def on_hall_call(self, floor: int, direction: Direction) -> None:
        self.assigned_at.setdefault((floor, direction), self.tick)

    def step(self) -> None:
        self.tick += 1


# ==========================================================================
# 5. Hall calls vs car calls
# ==========================================================================


class SingleQueueCar:
    """Every button, inside or outside, becomes a bare floor in one FIFO queue."""

    def __init__(self, floor: int = 0) -> None:
        self.floor = floor
        self.queue: list[int] = []
        self.stops_made: list[tuple[int, int]] = []  # (floor, travel direction when stopping)
        self._last_step = 0

    def request(self, floor: int) -> None:
        if floor not in self.queue:
            self.queue.append(floor)

    def step(self) -> None:
        if not self.queue:
            return
        target = self.queue[0]
        step = (target > self.floor) - (target < self.floor)
        self.floor += step
        self._last_step = step or self._last_step
        if self.floor in self.queue:  # stops at any queued floor it passes
            self.queue.remove(self.floor)
            self.stops_made.append((self.floor, self._last_step))


@dataclass
class DestinationCar:
    car_id: str
    floor: int
    stops: set[int] = field(default_factory=set)
    passengers: list[tuple[int, int]] = field(default_factory=list)


class DestinationDispatcher:
    """Destination dispatch: passengers key in their floor at a lobby kiosk.

    Because the controller knows each trip's destination before boarding, it
    can group people going to the same floors into the same car.
    """

    STOP_COST = 3  # ticks a single extra stop adds for everyone on the car

    def __init__(self, cars: Sequence[DestinationCar]) -> None:
        self.cars = list(cars)

    def cost(self, car: DestinationCar, origin: int, destination: int) -> int:
        new_stops = len({origin, destination} - car.stops)
        riders_delayed = len(car.passengers) + 1
        return abs(car.floor - origin) + new_stops * self.STOP_COST * riders_delayed

    def request(self, origin: int, destination: int) -> str:
        if origin == destination:
            raise ValueError("origin and destination must differ")
        car = min(self.cars, key=lambda c: (self.cost(c, origin, destination), c.car_id))
        car.stops |= {origin, destination}
        car.passengers.append((origin, destination))
        return car.car_id


# ==========================================================================
# Demo
# ==========================================================================


def demo() -> None:
    print("1) Per-car scheduling, starvation scenario (car starts at 4)")
    arrivals = starvation_arrivals()
    for scheduler in (FcfsScheduler(), SstfScheduler(), ScanScheduler(0, 9), LookScheduler()):
        r = simulate_single_car(scheduler, arrivals, ticks=40, start_floor=4)
        wait9 = r.wait_for(9)
        print(f"   {scheduler.name:<5} floor-9 wait: {('never' if wait9 is None else wait9):>5}  "
              f"served: {len(r.served):>2}  travelled: {r.floors_travelled:>2} floors")

    print("\n   Random traffic, 20 floors, 10 seeds (mean / worst wait, ticks)")
    for name, (avg, worst) in compare_schedulers().items():
        print(f"   {name:<5} {avg:5.1f} / {worst}")

    print("\n2) Multi-car dispatch on identical random traffic (mean / max wait, ticks)")
    for name, (avg, worst) in compare_dispatchers().items():
        print(f"   {name:<15} {avg:6.1f} / {worst}")

    print("\n3) State pattern car")
    car = StatefulCar()
    car.press(3)
    for _ in range(8):
        car.step()
    print("   " + "; ".join(car.history))

    print("\n4) Polling every 3 ticks vs observer: when was a press at tick 1 noticed?")
    poll_panel, obs_panel = PollingHallPanel(), ObservableHallPanel()
    poller, listener = PollingController(poll_panel, scan_every=3), ListeningController(obs_panel)
    for t in range(1, 5):
        poller.step()
        listener.step()
        if t == 1:
            poll_panel.press(5, Direction.UP)
            obs_panel.press(5, Direction.UP)
    print(f"   polling: tick {poller.assigned_at[(5, Direction.UP)]}, "
          f"observer: tick {listener.assigned_at[(5, Direction.UP)]}")

    print("\n5a) Mixed queue: car heading to 8, someone on 5 wants DOWN")
    naive = SingleQueueCar()
    naive.request(8)
    naive.step()
    naive.request(5)
    for _ in range(12):
        naive.step()
    print(f"   single queue stops (floor, travel dir): {naive.stops_made}")
    typed = ElevatorCar(0, 0, 9, door_dwell_ticks=1)
    stops: list[tuple[int, str]] = []
    typed.bus.subscribe(lambda e: stops.append((e.floor, e.direction.name if e.direction else "-")),
                        EventKind.DOORS_OPENED)
    typed.press_button(8)
    typed.step(1)
    typed.add_hall_call(5, Direction.DOWN)
    for t in range(2, 20):
        typed.step(t)
    print(f"   typed calls stops (floor, leaving dir):  {stops}")

    print("\n5b) Destination dispatch at the lobby kiosk")
    dispatcher = DestinationDispatcher([DestinationCar("A", 0), DestinationCar("B", 0)])
    for destination in (7, 7, 12, 12, 7):
        print(f"   lobby -> {destination:>2}: go to car {dispatcher.request(0, destination)}")


if __name__ == "__main__":
    demo()
