import threading
import unittest

from alternatives import (
    DestinationCar,
    DestinationDispatcher,
    FcfsScheduler,
    ListeningController,
    LookScheduler,
    ObservableHallPanel,
    OutOfServiceBehavior,
    PollingController,
    PollingHallPanel,
    SstfScheduler,
    StatefulCar,
    compare_dispatchers,
    compare_schedulers,
    simulate_single_car,
    starvation_arrivals,
)
from elevator_system import (
    ALLOWED_TRANSITIONS,
    CarState,
    Direction,
    DoorState,
    ElevatorCar,
    ElevatorError,
    ElevatorSystem,
    EventKind,
    InvalidTransition,
    LeastLoadedStrategy,
    NearestCarStrategy,
    OperatingMode,
    SafetyInterlockError,
    estimate_arrival_ticks,
)


def run_car(car: ElevatorCar, ticks: int, start: int = 1) -> None:
    for t in range(start, start + ticks):
        car.step(t)


def door_openings(car: ElevatorCar) -> list[tuple[int, Direction | None]]:
    opened: list[tuple[int, Direction | None]] = []
    car.bus.subscribe(lambda e: opened.append((e.floor, e.direction)), EventKind.DOORS_OPENED)
    return opened


class CarMovementTests(unittest.TestCase):
    def test_car_call_moves_car_and_opens_doors(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=2)
        opened = door_openings(car)
        self.assertTrue(car.press_button(3))
        run_car(car, 4)  # 1 tick to decide + 3 floors
        self.assertEqual(car.floor, 3)
        self.assertEqual(car.state, CarState.DOORS_OPEN)
        self.assertEqual(car.door, DoorState.OPEN)
        self.assertEqual(opened, [(3, None)])

    def test_doors_close_after_dwell_and_car_goes_idle(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=2)
        car.press_button(1)
        run_car(car, 2 + 2)
        self.assertEqual(car.state, CarState.IDLE)
        self.assertEqual(car.door, DoorState.CLOSED)
        self.assertIsNone(car.direction)

    def test_look_serves_in_sweep_order(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=1)
        opened = door_openings(car)
        for floor in (7, 2, 5):
            car.press_button(floor)
        run_car(car, 30)
        self.assertEqual([f for f, _ in opened], [2, 5, 7])

    def test_hall_call_in_opposite_direction_is_skipped_until_turnaround(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=1)
        opened = door_openings(car)
        car.press_button(8)
        car.step(1)
        car.add_hall_call(5, Direction.DOWN)
        run_car(car, 30, start=2)
        self.assertEqual(opened, [(8, Direction.DOWN), (5, Direction.DOWN)])

    def test_hall_call_in_same_direction_is_picked_up_on_the_way(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=1)
        opened = door_openings(car)
        car.press_button(8)
        car.step(1)
        car.add_hall_call(5, Direction.UP)
        run_car(car, 30, start=2)
        self.assertEqual([f for f, _ in opened], [5, 8])

    def test_opposite_car_call_is_ignored_while_committed(self):
        car = ElevatorCar(0, 0, 9)
        car.press_button(8)
        run_car(car, 4)  # now moving up around floor 3
        self.assertFalse(car.press_button(1))
        self.assertTrue(car.press_button(6))

    def test_opposite_car_call_accepted_when_policy_disabled(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=1, ignore_opposite_car_calls=False)
        opened = door_openings(car)
        car.press_button(8)
        run_car(car, 4)
        self.assertTrue(car.press_button(1))
        run_car(car, 40, start=5)
        self.assertEqual([f for f, _ in opened], [8, 1])

    def test_unserved_floor_rejected(self):
        car = ElevatorCar(0, 0, 9, served_floors=[0, 5, 9])
        with self.assertRaises(ValueError):
            car.press_button(3)

    def test_pressing_current_floor_while_doors_open_holds_doors(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=2)
        car.press_button(0)
        car.step(1)
        self.assertEqual(car.state, CarState.DOORS_OPEN)
        car.step(2)
        car.press_button(0)
        car.step(3)
        self.assertEqual(car.state, CarState.DOORS_OPEN)


class StateMachineAndSafetyTests(unittest.TestCase):
    def test_every_state_has_transition_entry(self):
        self.assertEqual(set(ALLOWED_TRANSITIONS), set(CarState))

    def test_cannot_go_out_of_service_while_moving(self):
        car = ElevatorCar(0, 0, 9)
        car.press_button(5)
        run_car(car, 2)
        self.assertEqual(car.state, CarState.MOVING_UP)
        with self.assertRaises(InvalidTransition):
            car.take_out_of_service()

    def test_interlock_prevents_moving_with_doors_open(self):
        car = ElevatorCar(0, 0, 9)
        car.door = DoorState.OPEN  # simulate a faulty door sensor
        car.press_button(4)
        with self.assertRaises(SafetyInterlockError):
            car.step(1)

    def test_overload_keeps_doors_open(self):
        car = ElevatorCar(0, 0, 9, door_dwell_ticks=1, capacity_kg=800)
        events: list[EventKind] = []
        car.bus.subscribe(lambda e: events.append(e.kind), EventKind.OVERLOAD)
        car.press_button(0)
        car.step(1)
        car.press_button(5)
        car.set_load(900)
        run_car(car, 5, start=2)
        self.assertEqual(car.state, CarState.DOORS_OPEN)
        self.assertEqual(car.floor, 0)
        self.assertTrue(events)
        car.set_load(700)
        run_car(car, 10, start=7)
        self.assertEqual(car.floor, 5)

    def test_negative_load_rejected(self):
        with self.assertRaises(ValueError):
            ElevatorCar(0, 0, 9).set_load(-1)


class DispatchTests(unittest.TestCase):
    def make_cars(self) -> list[ElevatorCar]:
        cars = [ElevatorCar(i, 0, 19) for i in range(3)]
        cars[0].floor, cars[1].floor, cars[2].floor = 0, 9, 15
        return cars

    def test_nearest_car(self):
        cars = self.make_cars()
        self.assertEqual(NearestCarStrategy().choose(cars, 12, Direction.UP).car_id, 1)

    def test_least_loaded(self):
        cars = self.make_cars()
        cars[1].press_button(18)
        cars[2].press_button(19)
        self.assertEqual(LeastLoadedStrategy().choose(cars, 12, Direction.UP).car_id, 0)

    def test_eta_prefers_car_already_heading_toward_call(self):
        car = ElevatorCar(0, 0, 19)
        car.floor = 5
        car.press_button(15)
        car.step(1)  # committed upward
        on_the_way = estimate_arrival_ticks(car, 10, Direction.UP)
        wrong_way = estimate_arrival_ticks(car, 10, Direction.DOWN)
        self.assertEqual(on_the_way, 5)
        self.assertGreater(wrong_way, on_the_way)

    def test_system_assigns_and_serves_hall_call(self):
        system = ElevatorSystem(10, 2)
        car_id = system.press_hall_button(6, Direction.DOWN)
        self.assertIn(car_id, (0, 1))
        self.assertIn((6, Direction.DOWN), system.lit_hall_buttons())
        system.run_until_idle()
        self.assertEqual(system.lit_hall_buttons(), set())
        self.assertEqual(len(system.wait_times), 1)

    def test_duplicate_press_is_idempotent(self):
        system = ElevatorSystem(10, 2)
        first = system.press_hall_button(6, Direction.UP)
        second = system.press_hall_button(6, Direction.UP)
        self.assertEqual(first, second)
        self.assertEqual(system.car(first).workload, 1)

    def test_invalid_hall_buttons(self):
        system = ElevatorSystem(10, 1)
        with self.assertRaises(ValueError):
            system.press_hall_button(9, Direction.UP)
        with self.assertRaises(ValueError):
            system.press_hall_button(0, Direction.DOWN)
        with self.assertRaises(ValueError):
            system.press_hall_button(42, Direction.DOWN)

    def test_call_at_floor_where_car_stands_with_open_doors_is_served_at_once(self):
        system = ElevatorSystem(10, 1)
        system.press_car_button(0, 0)
        system.step()
        self.assertEqual(system.car(0).state, CarState.DOORS_OPEN)
        system.press_hall_button(0, Direction.UP)
        self.assertEqual(system.lit_hall_buttons(), set())
        self.assertEqual(system.wait_times, [0])

    def test_other_car_serving_a_call_releases_the_assigned_car(self):
        mover = ElevatorCar(0, 0, 9, door_dwell_ticks=1)
        holder = ElevatorCar(1, 0, 9, door_dwell_ticks=20)
        holder.floor = 8
        system = ElevatorSystem(10, cars=[mover, holder], strategy=NearestCarStrategy())
        system.press_car_button(1, 8)  # car 1 opens its doors at 8 and holds them
        system.press_car_button(0, 9)  # car 0 heads up from the lobby...
        system.press_car_button(0, 7)  # ...with a passenger getting off at 7
        system.run(6)
        self.assertEqual((mover.floor, holder.state), (5, CarState.DOORS_OPEN))
        # Car 1 is nearer, so it gets the call, but car 0 stops at 7 going up first.
        self.assertEqual(system.press_hall_button(7, Direction.UP), 1)
        system.run(2)
        self.assertEqual(mover.floor, 7)
        self.assertEqual(system.lit_hall_buttons(), set())
        self.assertEqual(holder.hall_stops, frozenset())
        system.run_until_idle()
        self.assertEqual(holder.floor, 8)

    def test_zoned_cars_only_get_calls_for_their_floors(self):
        express = ElevatorCar(0, 0, 19, served_floors=[0, 10, 15, 19])
        local = ElevatorCar(1, 0, 19)
        system = ElevatorSystem(20, cars=[express, local], strategy=NearestCarStrategy())
        self.assertEqual(system.press_hall_button(3, Direction.UP), 1)
        self.assertEqual(system.press_hall_button(0, Direction.UP), 0)

    def test_out_of_service_car_hands_back_its_calls(self):
        system = ElevatorSystem(10, 2, strategy=NearestCarStrategy())
        system.car(1).park_at(9)
        system.run_until_idle()
        self.assertEqual(system.press_hall_button(2, Direction.UP), 0)
        system.take_car_out_of_service(0)
        self.assertEqual(system.assigned_car(2, Direction.UP), 1)
        system.run_until_idle()
        self.assertEqual(system.lit_hall_buttons(), set())

    def test_call_waits_while_no_car_is_in_service(self):
        system = ElevatorSystem(10, 1)
        system.take_car_out_of_service(0)
        self.assertIsNone(system.press_hall_button(5, Direction.UP))
        system.run(3)
        self.assertIn((5, Direction.UP), system.lit_hall_buttons())
        system.return_car_to_service(0)
        system.run_until_idle()
        self.assertEqual(system.lit_hall_buttons(), set())

    def test_run_until_idle_raises_when_stuck(self):
        system = ElevatorSystem(10, 1)
        system.take_car_out_of_service(0)
        system.press_hall_button(5, Direction.UP)
        with self.assertRaises(ElevatorError):
            system.run_until_idle(max_ticks=20)


class ModeTests(unittest.TestCase):
    def test_fire_recall_brings_every_car_to_lobby_and_disables_calls(self):
        system = ElevatorSystem(12, 3)
        system.press_car_button(0, 11)
        system.press_car_button(1, 6)
        system.run(5)
        system.activate_fire_recall()
        self.assertIsNone(system.press_hall_button(4, Direction.UP))
        self.assertFalse(system.press_car_button(0, 9))
        system.run_until_idle()
        for car in system.cars:
            self.assertEqual(car.floor, 0)
            self.assertEqual(car.state, CarState.DOORS_OPEN)
        system.run(10)
        self.assertTrue(all(c.state is CarState.DOORS_OPEN for c in system.cars))

    def test_clearing_fire_recall_restores_normal_service(self):
        system = ElevatorSystem(12, 1)
        system.activate_fire_recall()
        system.run_until_idle()
        system.clear_fire_recall()
        self.assertEqual(system.mode, OperatingMode.NORMAL)
        system.press_hall_button(5, Direction.DOWN)
        system.run_until_idle()
        self.assertEqual(system.car(0).floor, 5)

    def test_fire_recall_must_use_dedicated_method(self):
        system = ElevatorSystem(5, 1)
        with self.assertRaises(ValueError):
            system.set_mode(OperatingMode.FIRE_RECALL)

    def test_up_peak_parks_idle_cars_at_lobby(self):
        system = ElevatorSystem(12, 2)
        for car in system.cars:
            car.park_at(8)
        system.run_until_idle()
        system.set_mode(OperatingMode.UP_PEAK)
        system.run(30)
        self.assertTrue(all(car.floor == 0 for car in system.cars))

    def test_down_peak_spreads_idle_cars_high(self):
        system = ElevatorSystem(20, 3)
        system.set_mode(OperatingMode.DOWN_PEAK)
        system.run(60)
        floors = sorted(car.floor for car in system.cars)
        self.assertEqual(len(set(floors)), 3)
        self.assertTrue(all(f >= 10 for f in floors))


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_button_presses_are_all_served(self):
        system = ElevatorSystem(20, 4)
        stop = threading.Event()

        def ticker() -> None:
            while not stop.is_set():
                system.step()

        def presser(offset: int) -> None:
            for floor in range(1, 19):
                system.press_hall_button((floor + offset) % 18 + 1, Direction.UP if offset % 2 else Direction.DOWN)

        clock = threading.Thread(target=ticker)
        clock.start()
        workers = [threading.Thread(target=presser, args=(i,)) for i in range(6)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        stop.set()
        clock.join()
        system.run_until_idle(max_ticks=5_000)
        self.assertEqual(system.lit_hall_buttons(), set())


class AlternativesTests(unittest.TestCase):
    def test_sstf_starves_the_far_request(self):
        arrivals = starvation_arrivals()
        sstf = simulate_single_car(SstfScheduler(), arrivals, ticks=40, start_floor=4)
        look = simulate_single_car(LookScheduler(), arrivals, ticks=40, start_floor=4)
        self.assertIsNone(sstf.wait_for(9))
        self.assertIsNotNone(look.wait_for(9))

    def test_look_bounds_worst_wait_better_than_fcfs_and_sstf(self):
        results = compare_schedulers(seeds=range(1, 6))
        self.assertLess(results["LOOK"][1], results["SSTF"][1])
        self.assertLess(results["LOOK"][1], results["FCFS"][1])

    def test_fcfs_serves_oldest_first(self):
        result = simulate_single_car(FcfsScheduler(), {0: [9, 1]}, ticks=30, start_floor=5)
        self.assertEqual([r.floor for r, _ in result.served], [9, 1])

    def test_estimated_time_beats_nearest_car_on_average(self):
        results = compare_dispatchers(ticks=200)
        self.assertLess(results["estimated time"][0], results["nearest car"][0])

    def test_state_pattern_car(self):
        car = StatefulCar(dwell=1)
        car.press(2)
        for _ in range(5):
            car.step()
        self.assertEqual(car.floor, 2)
        self.assertEqual(car.state.name, "idle")
        car.state = OutOfServiceBehavior()
        self.assertFalse(car.press(4))

    def test_observer_reacts_before_poller(self):
        poll_panel, obs_panel = PollingHallPanel(), ObservableHallPanel()
        poller = PollingController(poll_panel, scan_every=3)
        listener = ListeningController(obs_panel)
        poller.step()
        listener.step()
        poll_panel.press(4, Direction.UP)
        obs_panel.press(4, Direction.UP)
        self.assertEqual(listener.assigned_at[(4, Direction.UP)], 1)
        poller.step()
        poller.step()
        self.assertEqual(poller.assigned_at[(4, Direction.UP)], 3)

    def test_destination_dispatch_groups_same_destinations(self):
        dispatcher = DestinationDispatcher([DestinationCar("A", 0), DestinationCar("B", 0)])
        cars = [dispatcher.request(0, d) for d in (7, 7, 12, 12)]
        self.assertEqual(cars, ["A", "A", "B", "B"])
        with self.assertRaises(ValueError):
            dispatcher.request(3, 3)


if __name__ == "__main__":
    unittest.main()
