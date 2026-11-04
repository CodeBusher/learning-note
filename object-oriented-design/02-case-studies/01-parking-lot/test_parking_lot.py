"""Tests for the parking lot. Run: python3 -m unittest discover -s <this folder> -v"""

from __future__ import annotations

import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

import alternatives
from parking_lot import (
    AlreadyParkedError,
    FlatFee,
    HourlyFee,
    LotFullError,
    ManualClock,
    ParkingLot,
    ParkingSpot,
    PeakHourSurcharge,
    SpotAllocator,
    SpotStateError,
    SpotType,
    Ticket,
    TieredFee,
    UnknownTicketError,
    Vehicle,
    VehicleType,
    billable_hours,
    build_level,
)

START = datetime(2026, 3, 2, 12, 0)  # midday: outside any peak window used below
RATES = {
    VehicleType.MOTORCYCLE: Decimal("1.50"),
    VehicleType.CAR: Decimal("3.00"),
    VehicleType.ELECTRIC_CAR: Decimal("3.00"),
    VehicleType.TRUCK: Decimal("6.00"),
}


def car(plate: str = "CAR-1") -> Vehicle:
    return Vehicle(plate, VehicleType.CAR)


def ticket_at(entry: datetime, vehicle_type: VehicleType = VehicleType.CAR) -> Ticket:
    return Ticket("T1", "X", vehicle_type, "L1-R01", 1, entry)


class VehicleAndSpotTest(unittest.TestCase):
    def test_plate_is_normalized(self):
        self.assertEqual(Vehicle("  abc 123 ", VehicleType.CAR).plate, "ABC 123")

    def test_empty_plate_rejected(self):
        with self.assertRaises(ValueError):
            Vehicle("   ", VehicleType.CAR)

    def test_spot_cannot_be_double_occupied_or_double_vacated(self):
        spot = ParkingSpot("S1", SpotType.REGULAR)
        spot.occupy("A")
        with self.assertRaises(SpotStateError):
            spot.occupy("B")
        self.assertEqual(spot.vacate(), "A")
        with self.assertRaises(SpotStateError):
            spot.vacate()

    def test_build_level_ids_and_distances(self):
        spots = build_level(2, compact=1, regular=2)
        self.assertEqual([s.spot_id for s in spots], ["L2-C01", "L2-R01", "L2-R02"])
        self.assertEqual([s.distance for s in spots], [2000, 2001, 2002])
        self.assertTrue(all(s.level == 2 for s in spots))


class AllocationTest(unittest.TestCase):
    def test_duplicate_spot_ids_rejected(self):
        with self.assertRaises(ValueError):
            SpotAllocator([ParkingSpot("S", SpotType.REGULAR), ParkingSpot("S", SpotType.COMPACT)])

    def test_nearest_spot_of_preferred_type_wins(self):
        allocator = SpotAllocator(build_level(2, regular=2) + build_level(1, regular=2))
        self.assertEqual(allocator.allocate(car("A")).spot_id, "L1-R01")
        self.assertEqual(allocator.allocate(car("B")).spot_id, "L1-R02")
        self.assertEqual(allocator.allocate(car("C")).spot_id, "L2-R01")

    def test_released_spot_is_reused_first(self):
        allocator = SpotAllocator(build_level(1, regular=3))
        first = allocator.allocate(car("A"))
        allocator.allocate(car("B"))
        allocator.release(first.spot_id)
        self.assertEqual(allocator.allocate(car("C")).spot_id, first.spot_id)

    def test_motorcycle_falls_back_to_bigger_spots(self):
        allocator = SpotAllocator(build_level(1, compact=1, regular=1, oversized=1))
        types = [allocator.allocate(Vehicle(f"M{i}", VehicleType.MOTORCYCLE)).spot_type for i in range(3)]
        self.assertEqual(types, [SpotType.COMPACT, SpotType.REGULAR, SpotType.OVERSIZED])
        self.assertIsNone(allocator.allocate(Vehicle("M4", VehicleType.MOTORCYCLE)))

    def test_truck_only_fits_oversized(self):
        allocator = SpotAllocator(build_level(1, compact=3, regular=3, ev=3))
        self.assertIsNone(allocator.allocate(Vehicle("T", VehicleType.TRUCK)))

    def test_ev_prefers_charger_and_car_never_takes_it(self):
        allocator = SpotAllocator(build_level(1, regular=1, ev=1))
        self.assertEqual(allocator.allocate(car("A")).spot_type, SpotType.REGULAR)
        self.assertIsNone(allocator.allocate(car("B")))
        self.assertEqual(allocator.allocate(Vehicle("E", VehicleType.ELECTRIC_CAR)).spot_type,
                         SpotType.EV_CHARGING)

    def test_custom_compatibility_table(self):
        relaxed = {VehicleType.CAR: (SpotType.REGULAR, SpotType.EV_CHARGING)}
        allocator = SpotAllocator(build_level(1, regular=1, ev=1), relaxed)
        allocator.allocate(car("A"))
        self.assertEqual(allocator.allocate(car("B")).spot_type, SpotType.EV_CHARGING)


class FeeTest(unittest.TestCase):
    def test_billable_hours(self):
        self.assertEqual(billable_hours(timedelta(minutes=5), timedelta(minutes=10)), 0)
        self.assertEqual(billable_hours(timedelta(minutes=11), timedelta(minutes=10)), 1)
        self.assertEqual(billable_hours(timedelta(hours=2)), 2)
        self.assertEqual(billable_hours(timedelta(hours=2, seconds=1)), 3)

    def test_flat_fee(self):
        self.assertEqual(FlatFee(Decimal("20")).fee(ticket_at(START), START + timedelta(hours=9)),
                         Decimal("20.00"))

    def test_hourly_fee_depends_on_vehicle_type(self):
        policy = HourlyFee(RATES)
        exit_time = START + timedelta(hours=1, minutes=30)
        self.assertEqual(policy.fee(ticket_at(START), exit_time), Decimal("6.00"))
        self.assertEqual(policy.fee(ticket_at(START, VehicleType.TRUCK), exit_time), Decimal("12.00"))
        self.assertEqual(policy.fee(ticket_at(START), START + timedelta(minutes=8)), Decimal("0.00"))

    def test_tiered_fee_bands_and_daily_cap(self):
        policy = TieredFee([(1, Decimal("5")), (3, Decimal("12")), (6, Decimal("20"))], Decimal("30"))
        fee = lambda **kw: policy.fee(ticket_at(START), START + timedelta(**kw))
        self.assertEqual(fee(minutes=5), Decimal("0.00"))
        self.assertEqual(fee(minutes=50), Decimal("5.00"))
        self.assertEqual(fee(hours=2, minutes=30), Decimal("12.00"))
        self.assertEqual(fee(hours=10), Decimal("30.00"))           # beyond last band: daily max
        self.assertEqual(fee(days=2, hours=2), Decimal("72.00"))    # 2 x 30 + 12

    def test_tiers_must_be_sorted(self):
        with self.assertRaises(ValueError):
            TieredFee([(3, Decimal("12")), (1, Decimal("5"))], Decimal("30"))

    def test_peak_surcharge_only_for_peak_entries(self):
        policy = PeakHourSurcharge(HourlyFee(RATES), Decimal("1.5"), range(7, 10))
        morning = datetime(2026, 3, 2, 8, 0)
        self.assertEqual(policy.fee(ticket_at(morning), morning + timedelta(hours=2)), Decimal("9.00"))
        self.assertEqual(policy.fee(ticket_at(START), START + timedelta(hours=2)), Decimal("6.00"))


class ParkingLotTest(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock(START)
        self.lot = ParkingLot(build_level(1, compact=1, regular=2, oversized=1),
                              HourlyFee(RATES), clock=self.clock)

    def test_enter_issues_ticket_with_spot_and_time(self):
        ticket = self.lot.enter(car("abc"))
        self.assertEqual((ticket.plate, ticket.spot_id, ticket.level, ticket.entry_time),
                         ("ABC", "L1-R01", 1, START))
        self.assertEqual(self.lot.availability()[SpotType.REGULAR], 1)

    def test_ticket_ids_are_unique(self):
        ids = {self.lot.enter(car(f"C{i}")).ticket_id for i in range(3)}
        self.assertEqual(len(ids), 3)

    def test_same_plate_cannot_enter_twice(self):
        self.lot.enter(car("A"))
        with self.assertRaises(AlreadyParkedError):
            self.lot.enter(car("a"))

    def test_full_lot_raises(self):
        self.lot.enter(car("A"))
        self.lot.enter(car("B"))
        self.lot.enter(car("C"))  # falls back to the oversized spot
        with self.assertRaises(LotFullError):
            self.lot.enter(car("D"))

    def test_exit_charges_and_frees_spot(self):
        ticket = self.lot.enter(car("A"))
        self.clock.advance(hours=2, minutes=20)
        self.assertEqual(self.lot.quote(ticket.ticket_id), Decimal("9.00"))
        self.assertEqual(self.lot.availability()[SpotType.REGULAR], 1)  # quote changes nothing
        receipt = self.lot.exit(ticket.ticket_id)
        self.assertEqual(receipt.fee, Decimal("9.00"))
        self.assertEqual(receipt.duration, timedelta(hours=2, minutes=20))
        self.assertEqual(self.lot.availability()[SpotType.REGULAR], 2)
        self.assertIsNone(self.lot.find_vehicle("A"))
        self.lot.enter(car("A"))  # the same car may come back later

    def test_exit_twice_or_unknown_ticket_raises(self):
        ticket = self.lot.enter(car("A"))
        self.lot.exit(ticket.ticket_id)
        with self.assertRaises(UnknownTicketError):
            self.lot.exit(ticket.ticket_id)
        with self.assertRaises(UnknownTicketError):
            self.lot.quote("nope")

    def test_ticketless_exit_by_plate(self):
        self.lot.enter(Vehicle("TRK 9", VehicleType.TRUCK))
        self.clock.advance(hours=1)
        receipt = self.lot.exit_by_plate("trk 9")
        self.assertEqual((receipt.ticket.spot_id, receipt.fee), ("L1-O01", Decimal("6.00")))
        with self.assertRaises(UnknownTicketError):
            self.lot.exit_by_plate("trk 9")

    def test_find_vehicle(self):
        ticket = self.lot.enter(car("A"))
        self.assertEqual(self.lot.find_vehicle("a"), ticket)

    def test_failing_fee_policy_leaves_state_unchanged(self):
        class Broken(FlatFee):
            def fee(self, ticket, exit_time):
                raise RuntimeError("pricing service down")

        lot = ParkingLot(build_level(1, regular=1), Broken(Decimal("1")), clock=self.clock)
        ticket = lot.enter(car("A"))
        with self.assertRaises(RuntimeError):
            lot.exit(ticket.ticket_id)
        self.assertEqual(lot.find_vehicle("A"), ticket)
        self.assertEqual(lot.availability()[SpotType.REGULAR], 0)

    def test_concurrent_entries_never_share_a_spot(self):
        lot = ParkingLot(build_level(1, regular=10), FlatFee(Decimal("5")), clock=self.clock)
        tickets, failures = [], []
        start = threading.Barrier(40)

        def drive_in(i):
            start.wait()
            try:
                tickets.append(lot.enter(car(f"C{i}")))
            except LotFullError:
                failures.append(i)

        threads = [threading.Thread(target=drive_in, args=(i,)) for i in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(tickets), 10)
        self.assertEqual(len(failures), 30)
        self.assertEqual(len({t.spot_id for t in tickets}), 10)


class AlternativesTest(unittest.TestCase):
    ALLOCATORS = (alternatives.FirstAvailableScanAllocator, alternatives.NearestFirstHeapAllocator,
                  alternatives.PerTypeFreeListAllocator, SpotAllocator)

    def test_all_allocators_respect_compatibility_and_capacity(self):
        for cls in self.ALLOCATORS:
            with self.subTest(cls.__name__):
                allocator = cls(build_level(1, compact=1, regular=1, oversized=1))
                self.assertEqual(allocator.allocate(Vehicle("T", VehicleType.TRUCK)).spot_type,
                                 SpotType.OVERSIZED)
                self.assertEqual(allocator.allocate(car("A")).spot_type, SpotType.REGULAR)
                self.assertIsNone(allocator.allocate(car("B")))
                self.assertEqual(allocator.allocate(Vehicle("M", VehicleType.MOTORCYCLE)).spot_type,
                                 SpotType.COMPACT)

    def test_heap_allocator_restores_skipped_spots(self):
        allocator = alternatives.NearestFirstHeapAllocator(build_level(1, compact=2, regular=1))
        allocator.allocate(car("A"))  # has to skip both compact spots
        self.assertEqual(allocator.allocate(Vehicle("M", VehicleType.MOTORCYCLE)).spot_id, "L1-C01")

    def test_free_list_ignores_distance(self):
        allocator = alternatives.PerTypeFreeListAllocator(build_level(1, regular=3))
        first = allocator.allocate(car("A"))
        allocator.release(first.spot_id)
        self.assertEqual(allocator.allocate(car("B")).spot_id, "L1-R02")

    def test_hard_coded_fee_matches_strategy_version(self):
        strategy = PeakHourSurcharge(HourlyFee(RATES), Decimal("1.5"), range(7, 10))
        for vehicle_type in VehicleType:
            for entry in (datetime(2026, 3, 2, 8, 30), START):
                exit_time = entry + timedelta(hours=3, minutes=5)
                with self.subTest(vehicle_type=vehicle_type, entry=entry):
                    self.assertEqual(alternatives.hard_coded_fee(vehicle_type, entry, exit_time),
                                     strategy.fee(ticket_at(entry, vehicle_type), exit_time))

    def test_demand_multiplier(self):
        occupancy = [0.5]
        policy = alternatives.DemandMultiplier(FlatFee(Decimal("10")), lambda: occupancy[0])
        ticket = ticket_at(START)
        self.assertEqual(policy.fee(ticket, START), Decimal("10.00"))
        occupancy[0] = 0.75
        self.assertEqual(policy.fee(ticket, START), Decimal("12.00"))
        occupancy[0] = 0.95
        self.assertEqual(policy.fee(ticket, START), Decimal("15.00"))

    def test_compatibility_approaches(self):
        hierarchy = {VehicleType.MOTORCYCLE: alternatives.Motorcycle("m"), VehicleType.CAR: alternatives.Car("c"),
                     VehicleType.ELECTRIC_CAR: alternatives.ElectricCar("e"), VehicleType.TRUCK: alternatives.Truck("t")}
        for vehicle_type, vehicle in hierarchy.items():
            for spot_type in SpotType:
                with self.subTest(vehicle=vehicle_type, spot=spot_type):
                    self.assertEqual(vehicle.can_park_in(spot_type),
                                     alternatives.table_fits(vehicle_type, spot_type))
        # The size rule cannot express "keep petrol cars off EV chargers".
        self.assertTrue(alternatives.size_fits(VehicleType.CAR, SpotType.EV_CHARGING))
        self.assertFalse(alternatives.table_fits(VehicleType.CAR, SpotType.EV_CHARGING))

    def test_unsafe_board_double_books(self):
        claims = alternatives.race_two_drivers(alternatives.UnsafeSpotBoard(["S1", "S2"]))
        self.assertEqual([spot for spot, _ in claims], ["S1", "S1"])

    def test_locked_and_optimistic_boards_do_not(self):
        for board in (alternatives.LockedSpotBoard(["S1", "S2"]), alternatives.OptimisticSpotBoard(["S1", "S2"])):
            with self.subTest(type(board).__name__):
                claims = alternatives.race_two_drivers(board)
                self.assertEqual(sorted(spot for spot, _ in claims), ["S1", "S2"])

    def test_optimistic_board_retries_after_conflict(self):
        board = alternatives.OptimisticSpotBoard(["S1", "S2"])
        alternatives.race_two_drivers(board)
        self.assertEqual(board.retries, 1)

    def test_boards_return_none_when_full(self):
        for board in (alternatives.UnsafeSpotBoard(["S1"]), alternatives.LockedSpotBoard(["S1"]),
                      alternatives.OptimisticSpotBoard(["S1"])):
            with self.subTest(type(board).__name__):
                self.assertEqual(board.claim("A"), "S1")
                self.assertIsNone(board.claim("B"))


if __name__ == "__main__":
    unittest.main()
