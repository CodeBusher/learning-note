"""Unit tests for the shipping locker. Run: python3 -m unittest discover -s <this folder> -v"""

from __future__ import annotations

import threading
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alternatives import (
    BestFitVolumeAssigner,
    FirstFreeAssigner,
    FreeformCompartment,
    HashedCodeStore,
    NaiveRandomCodes,
    StatefulPackage,
    brute_force_odds,
    fill_until_rejected,
    hardcoded_fee,
)
from shipping_locker import (
    AccessCodeBook,
    Account,
    AttemptLimiter,
    BusinessDaysHold,
    CompartmentSize,
    CustomerNotifier,
    Dimensions,
    EventType,
    FixedHoldPeriod,
    FreeThenDailyFee,
    InMemoryOutbox,
    InvalidAccessCodeError,
    InvalidTransitionError,
    KeypadLockedError,
    LockerError,
    LockerPolicy,
    LockerService,
    ManualClock,
    NoCompartmentAvailableError,
    NoFee,
    Package,
    PackageExpiredError,
    PackageStatus,
    PackageTooLargeError,
    SmallestFitAssigner,
    StaffTaskQueue,
)

SMALL_BOX = Dimensions(25, 15, 8)
MEDIUM_BOX = Dimensions(40, 30, 18)
LARGE_BOX = Dimensions(55, 40, 35)


class RecordingObserver:
    def __init__(self) -> None:
        self.events = []

    def notify(self, event) -> None:
        self.events.append(event)


class LockerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = ManualClock()
        self.locker = LockerService.with_layout(
            "TEST-01",
            {CompartmentSize.SMALL: 2, CompartmentSize.MEDIUM: 1, CompartmentSize.LARGE: 1},
            clock=self.clock,
        )
        self.account = Account("A1", "Ana")
        self.recorder = RecordingObserver()
        self.locker.subscribe(self.recorder)
        self._next_id = 0

    def new_package(self, dims: Dimensions = SMALL_BOX, owner: Account | None = None) -> Package:
        self._next_id += 1
        return Package(f"PKG-{self._next_id}", owner or self.account, dims)

    def deliver(self, dims: Dimensions = SMALL_BOX, owner: Account | None = None) -> tuple[Package, str]:
        pkg = self.new_package(dims, owner)
        self.locker.assign(pkg)
        return pkg, self.locker.confirm_deposit(pkg.tracking_id)


class TestDimensions(unittest.TestCase):
    def test_rotation_is_allowed(self):
        self.assertTrue(Dimensions(10, 30, 20).fits_inside(Dimensions(30, 20, 10)))

    def test_one_edge_too_long_does_not_fit(self):
        self.assertFalse(Dimensions(31, 5, 5).fits_inside(Dimensions(30, 20, 10)))

    def test_non_positive_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            Dimensions(0, 10, 10)

    def test_smallest_fitting_size(self):
        self.assertIs(CompartmentSize.smallest_fitting(SMALL_BOX), CompartmentSize.SMALL)
        self.assertIs(CompartmentSize.smallest_fitting(MEDIUM_BOX), CompartmentSize.MEDIUM)
        self.assertIsNone(CompartmentSize.smallest_fitting(Dimensions(100, 100, 100)))


class TestAssignment(LockerTestCase):
    def test_small_box_goes_to_small_compartment(self):
        self.assertIs(self.locker.assign(self.new_package(SMALL_BOX)).size, CompartmentSize.SMALL)

    def test_overflows_to_next_size_when_smaller_full(self):
        self.locker.assign(self.new_package())
        self.locker.assign(self.new_package())
        self.assertIs(self.locker.assign(self.new_package()).size, CompartmentSize.MEDIUM)

    def test_no_compartment_available(self):
        self.locker.assign(self.new_package(LARGE_BOX))
        with self.assertRaises(NoCompartmentAvailableError):
            self.locker.assign(self.new_package(LARGE_BOX))

    def test_too_large_for_any_compartment(self):
        with self.assertRaises(PackageTooLargeError):
            self.locker.assign(self.new_package(Dimensions(100, 10, 10)))

    def test_failed_assignment_leaves_package_in_transit(self):
        self.locker.assign(self.new_package(LARGE_BOX))
        pkg = self.new_package(LARGE_BOX)
        with self.assertRaises(NoCompartmentAvailableError):
            self.locker.assign(pkg)
        self.assertIs(pkg.status, PackageStatus.IN_TRANSIT)

    def test_out_of_service_compartment_is_skipped(self):
        first = self.locker.assign(self.new_package())
        self.locker.cancel_assignment("PKG-1")
        first.in_service = False
        self.assertNotEqual(self.locker.assign(self.new_package()).compartment_id, first.compartment_id)

    def test_cancel_assignment_frees_compartment(self):
        pkg = self.new_package()
        self.locker.assign(pkg)
        self.locker.cancel_assignment(pkg.tracking_id)
        self.assertEqual(self.locker.free_count(), 4)
        self.assertIs(pkg.status, PackageStatus.IN_TRANSIT)


class TestPickup(LockerTestCase):
    def test_happy_path(self):
        pkg, code = self.deliver()
        self.clock.advance(timedelta(hours=5))
        receipt = self.locker.pick_up(code)
        self.assertIs(receipt.package, pkg)
        self.assertEqual(receipt.fee, Decimal("0"))
        self.assertIs(pkg.status, PackageStatus.PICKED_UP)
        self.assertEqual(self.locker.free_count(), 4)

    def test_code_is_six_digits(self):
        _, code = self.deliver()
        self.assertRegex(code, r"^\d{6}$")

    def test_code_cannot_be_reused(self):
        _, code = self.deliver()
        self.locker.pick_up(code)
        with self.assertRaises(InvalidAccessCodeError):
            self.locker.pick_up(code)

    def test_cannot_return_a_package_that_never_expired(self):
        pkg = self.new_package()
        self.locker.assign(pkg)
        with self.assertRaises(InvalidTransitionError):
            self.locker.return_to_sender(pkg.tracking_id)

    def test_fee_after_free_period_is_charged_to_account(self):
        _, code = self.deliver(MEDIUM_BOX)
        self.clock.advance(timedelta(days=4, hours=1))  # 5 started days, 3 free
        receipt = self.locker.pick_up(code)
        self.assertEqual(receipt.fee, Decimal("4.00"))
        self.assertEqual(self.account.balance_due, Decimal("4.00"))

    def test_fee_due_preview(self):
        pkg, _ = self.deliver(LARGE_BOX)
        self.clock.advance(timedelta(days=3, minutes=1))
        self.assertEqual(self.locker.fee_due(pkg.tracking_id), Decimal("3.00"))

    def test_account_policy_overrides_default(self):
        member = Account("M1", "Member", policy=LockerPolicy(NoFee(), FixedHoldPeriod(10)))
        _, code = self.deliver(owner=member)
        self.clock.advance(timedelta(days=9))
        self.assertEqual(self.locker.pick_up(code).fee, Decimal("0"))


class TestExpiry(LockerTestCase):
    def test_pickup_after_deadline_raises_and_expires(self):
        pkg, code = self.deliver()
        self.clock.advance(timedelta(days=7))
        with self.assertRaises(PackageExpiredError):
            self.locker.pick_up(code)
        self.assertIs(pkg.status, PackageStatus.EXPIRED)
        with self.assertRaises(InvalidAccessCodeError):  # code was revoked
            self.locker.pick_up(code)

    def test_one_second_before_deadline_still_works(self):
        _, code = self.deliver()
        self.clock.advance(timedelta(days=7) - timedelta(seconds=1))
        self.locker.pick_up(code)

    def test_sweep_then_return_frees_compartment(self):
        pkg, _ = self.deliver()
        self.deliver()
        self.clock.advance(timedelta(days=8))
        expired = self.locker.expire_overdue()
        self.assertEqual(len(expired), 2)
        self.assertEqual(self.locker.free_count(), 2)  # still physically occupied
        self.locker.return_to_sender(pkg.tracking_id)
        self.assertIs(pkg.status, PackageStatus.RETURNED)
        self.assertEqual(self.locker.free_count(), 3)

    def test_sweep_ignores_packages_inside_window(self):
        self.deliver()
        self.clock.advance(timedelta(days=2))
        self.assertEqual(self.locker.expire_overdue(), [])

    def test_business_days_hold_skips_weekend(self):
        friday = datetime(2026, 1, 9, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(BusinessDaysHold(2).deadline(friday), datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc))


class TestFeePolicy(unittest.TestCase):
    def test_partial_day_counts_as_a_day(self):
        policy = FreeThenDailyFee(free_days=1)
        self.assertEqual(policy.fee(CompartmentSize.SMALL, timedelta(days=1, seconds=1)), Decimal("1.00"))

    def test_zero_duration_is_free(self):
        self.assertEqual(FreeThenDailyFee(0).fee(CompartmentSize.LARGE, timedelta(0)), Decimal("0"))

    def test_negative_free_days_rejected(self):
        with self.assertRaises(ValueError):
            FreeThenDailyFee(-1)


class TestAccessCodes(unittest.TestCase):
    def test_collision_is_retried(self):
        codes = iter(["111111", "111111", "222222"])
        book = AccessCodeBook(generate=lambda: next(codes))
        account = Account("A", "A")
        first = book.issue(Package("P1", account, SMALL_BOX))
        second = book.issue(Package("P2", account, SMALL_BOX))
        self.assertEqual((first, second), ("111111", "222222"))

    def test_gives_up_after_max_tries(self):
        book = AccessCodeBook(generate=lambda: "111111", max_tries=3)
        account = Account("A", "A")
        book.issue(Package("P1", account, SMALL_BOX))
        with self.assertRaises(LockerError):
            book.issue(Package("P2", account, SMALL_BOX))

    def test_revoke_removes_code(self):
        book = AccessCodeBook()
        pkg = Package("P1", Account("A", "A"), SMALL_BOX)
        code = book.issue(pkg)
        book.revoke(pkg)
        self.assertIsNone(book.lookup(code))
        self.assertEqual(len(book), 0)


class TestRateLimiting(LockerTestCase):
    def guess_wrong(self, times: int) -> None:
        for _ in range(times):
            with self.assertRaises(InvalidAccessCodeError):
                self.locker.pick_up("not-a-code")

    def test_lockout_after_five_failures_blocks_even_valid_code(self):
        _, code = self.deliver()
        self.guess_wrong(5)
        with self.assertRaises(KeypadLockedError):
            self.locker.pick_up(code)
        self.assertIn(EventType.KEYPAD_LOCKED, [e.type for e in self.recorder.events])

    def test_lockout_expires(self):
        _, code = self.deliver()
        self.guess_wrong(5)
        self.clock.advance(timedelta(minutes=16))
        self.locker.pick_up(code)

    def test_failures_outside_window_are_forgotten(self):
        limiter = AttemptLimiter(self.clock, max_failures=3, window=timedelta(minutes=10))
        limiter.record_failure()
        limiter.record_failure()
        self.clock.advance(timedelta(minutes=11))
        self.assertFalse(limiter.record_failure())
        limiter.check()

    def test_success_resets_counter(self):
        _, code = self.deliver()
        self.guess_wrong(4)
        self.locker.pick_up(code)
        self.guess_wrong(4)  # would lock on the 5th if the counter had not reset


class TestObservers(LockerTestCase):
    def test_event_sequence(self):
        _, code = self.deliver()
        self.locker.pick_up(code)
        self.assertEqual([e.type for e in self.recorder.events],
                         [EventType.ASSIGNED, EventType.DEPOSITED, EventType.PICKED_UP])

    def test_customer_gets_code_and_staff_gets_task(self):
        outbox, staff = InMemoryOutbox(), StaffTaskQueue()
        self.locker.subscribe(CustomerNotifier(outbox))
        self.locker.subscribe(staff)
        pkg, code = self.deliver()
        self.assertIn(code, outbox.sent[0][1])
        self.clock.advance(timedelta(days=8))
        self.locker.expire_overdue()
        self.assertTrue(any(pkg.tracking_id in task for task in staff.tasks))

    def test_failing_observer_does_not_break_pickup(self):
        class Broken:
            def notify(self, event):
                raise RuntimeError("SMS gateway down")

        self.locker.subscribe(Broken())
        with self.assertLogs("shipping_locker", level="ERROR"):
            pkg, code = self.deliver()
            self.locker.pick_up(code)
        self.assertIs(pkg.status, PackageStatus.PICKED_UP)

    def test_events_published_for_failed_pickup_of_expired_package(self):
        _, code = self.deliver()
        self.clock.advance(timedelta(days=7))
        with self.assertRaises(PackageExpiredError):
            self.locker.pick_up(code)
        self.assertEqual(self.recorder.events[-1].type, EventType.EXPIRED)


class TestConcurrency(LockerTestCase):
    def test_parallel_assignments_never_double_book(self):
        results, errors = [], []
        barrier = threading.Barrier(20)

        def worker(i: int) -> None:
            barrier.wait()
            try:
                results.append(self.locker.assign(Package(f"T{i}", self.account, SMALL_BOX)))
            except NoCompartmentAvailableError:
                errors.append(i)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 4)
        self.assertEqual(len({c.compartment_id for c in results}), 4)
        self.assertEqual(len(errors), 16)


class TestAlternatives(unittest.TestCase):
    def test_first_free_wastes_large_compartment(self):
        layout = {CompartmentSize.SMALL: 1, CompartmentSize.MEDIUM: 1, CompartmentSize.LARGE: 1}
        boxes = [SMALL_BOX, MEDIUM_BOX, LARGE_BOX]
        self.assertEqual(fill_until_rejected(FirstFreeAssigner(), boxes, layout)[-1], "REJECTED")
        self.assertNotIn("REJECTED", fill_until_rejected(SmallestFitAssigner(), boxes, layout))

    def test_best_fit_prefers_tightest(self):
        spaces = [FreeformCompartment("big", Dimensions(60, 60, 60)),
                  FreeformCompartment("snug", Dimensions(30, 20, 10))]
        self.assertEqual(BestFitVolumeAssigner().choose(SMALL_BOX, spaces).compartment_id, "snug")

    def test_naive_codes_can_collide(self):
        naive = NaiveRandomCodes(seed=7)
        for i in range(3000):
            naive.issue(f"P{i}")
        self.assertLess(len(naive.by_code), 3000)

    def test_hashed_store_round_trip(self):
        store = HashedCodeStore()
        code = store.issue("P1")
        self.assertEqual(store.lookup(code), "P1")
        self.assertIsNone(store.lookup("not-it"))

    def test_brute_force_odds_drop_with_limit(self):
        self.assertGreater(brute_force_odds(300, 1000), 0.2)
        self.assertLess(brute_force_odds(300, 5), 0.01)

    def test_state_pattern_rejects_illegal_event(self):
        pkg = StatefulPackage("P1")
        with self.assertRaises(InvalidTransitionError):
            pkg.pick_up()
        pkg.deposit()
        pkg.pick_up()
        self.assertEqual(pkg.state.name, "picked up")

    def test_hardcoded_fee_matches_strategy(self):
        strategy = FreeThenDailyFee(3)
        for days in range(0, 8):
            stored = timedelta(days=days)
            self.assertEqual(hardcoded_fee(CompartmentSize.MEDIUM, stored, False),
                             strategy.fee(CompartmentSize.MEDIUM, stored))


if __name__ == "__main__":
    unittest.main()
