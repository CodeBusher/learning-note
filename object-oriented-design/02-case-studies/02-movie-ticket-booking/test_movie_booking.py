"""Tests for the movie booking system and its key alternatives.

Run with: python3 -m unittest discover -s <this folder> -v
"""

from __future__ import annotations

import threading
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from alternatives import (
    BitmapAvailability,
    GlobalLockBooker,
    HoldWithExpiryBooker,
    LayoutWithAvailabilityMap,
    LinearScanCatalog,
    OptimisticBooker,
    PerScreeningLockBooker,
    SeatObjectsPerScreening,
    TimeSortedCatalog,
    build_big_catalog,
    price_if_else,
    race_for_one_seat,
)
from movie_booking import (
    BookingService,
    BookingStatus,
    Cinema,
    CutoffRefundPolicy,
    FakePaymentGateway,
    FormatSurcharge,
    HoldExpiredError,
    InvalidStateError,
    ManualClock,
    MatineeDiscount,
    Movie,
    NotFoundError,
    PaymentDeclinedError,
    PaymentReceipt,
    Room,
    RuleBasedPricing,
    SchedulingConflictError,
    Screening,
    SeatLayout,
    SeatStatus,
    SeatType,
    SeatUnavailableError,
    ShowtimeIndex,
    WeekendSurcharge,
)

FRIDAY_9AM = datetime(2026, 11, 6, 9, 0)
SATURDAY_EVENING = datetime(2026, 11, 7, 19, 30)
BASE_PRICES = {
    SeatType.STANDARD: Decimal("12.00"),
    SeatType.ACCESSIBLE: Decimal("12.00"),
    SeatType.PREMIUM: Decimal("16.00"),
    SeatType.VIP: Decimal("24.00"),
}


def make_service(
    payments: FakePaymentGateway | None = None, clock: ManualClock | None = None
) -> tuple[BookingService, ManualClock, FakePaymentGateway]:
    clock = clock or ManualClock(FRIDAY_9AM)
    payments = payments or FakePaymentGateway(declined_customers={"mallory"})
    service = BookingService(
        RuleBasedPricing(BASE_PRICES), payments, clock=clock, hold_ttl=timedelta(minutes=8)
    )
    cinema = Cinema("c1", "Riverside", "Boston")
    cinema.add_room(Room("r1", "Main", SeatLayout.grid("ABC", 4, {"C": SeatType.VIP})))
    cinema.add_room(Room("r2", "Small", SeatLayout.grid("A", 2)))
    service.add_cinema(cinema)
    service.add_movie(Movie("m1", "Orbit", timedelta(minutes=120)))
    service.add_movie(Movie("m2", "Tides", timedelta(minutes=90)))
    service.schedule_screening("s1", "m1", "c1", "r1", SATURDAY_EVENING)
    return service, clock, payments


class LayoutTests(unittest.TestCase):
    def test_grid_assigns_row_types(self) -> None:
        layout = SeatLayout.grid("AB", 3, {"B": SeatType.PREMIUM})
        self.assertEqual(len(layout), 6)
        self.assertIs(layout.seat("B2").seat_type, SeatType.PREMIUM)
        self.assertIs(layout.seat("A2").seat_type, SeatType.STANDARD)

    def test_unknown_seat_raises(self) -> None:
        with self.assertRaises(NotFoundError):
            SeatLayout.grid("A", 2).seat("Z9")

    def test_duplicate_and_empty_layouts_rejected(self) -> None:
        from movie_booking import Seat

        with self.assertRaises(ValueError):
            SeatLayout([Seat("A", 1), Seat("A", 1)])
        with self.assertRaises(ValueError):
            SeatLayout([])


class SchedulingAndSearchTests(unittest.TestCase):
    def test_overlap_in_same_room_rejected(self) -> None:
        service, _, _ = make_service()
        with self.assertRaises(SchedulingConflictError):
            # starts during s1 (19:30-21:30)
            service.schedule_screening("s2", "m2", "c1", "r1", datetime(2026, 11, 7, 21, 0))

    def test_turnover_buffer_respected(self) -> None:
        service, _, _ = make_service()
        with self.assertRaises(SchedulingConflictError):
            service.schedule_screening("s2", "m2", "c1", "r1", datetime(2026, 11, 7, 21, 40))
        service.schedule_screening("s3", "m2", "c1", "r1", datetime(2026, 11, 7, 21, 50))

    def test_same_time_in_other_room_is_fine(self) -> None:
        service, _, _ = make_service()
        service.schedule_screening("s2", "m2", "c1", "r2", SATURDAY_EVENING)
        self.assertEqual(len(service.search_showtimes(city="BOSTON", on=SATURDAY_EVENING.date())), 2)

    def test_unknown_ids_raise_not_found(self) -> None:
        service, _, _ = make_service()
        with self.assertRaises(NotFoundError):
            service.schedule_screening("x", "nope", "c1", "r1", SATURDAY_EVENING)
        with self.assertRaises(NotFoundError):
            service.schedule_screening("x", "m1", "c1", "r9", SATURDAY_EVENING)
        with self.assertRaises(NotFoundError):
            service.seat_map("missing")

    def test_search_by_movie_is_sorted_by_start(self) -> None:
        service, _, _ = make_service()
        service.schedule_screening("early", "m1", "c1", "r2", datetime(2026, 11, 7, 10, 0))
        ids = [s.screening_id for s in service.search_showtimes(movie_id="m1")]
        self.assertEqual(ids, ["early", "s1"])

    def test_search_needs_a_selective_filter(self) -> None:
        service, _, _ = make_service()
        with self.assertRaises(ValueError):
            service.search_showtimes(city="Boston")


class PricingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cinema = Cinema("c", "X", "Boston")
        self.room = Room("r", "R", SeatLayout.grid("AD", 1, {"D": SeatType.VIP}))
        self.movie = Movie("m", "M", timedelta(minutes=100))
        self.pricing = RuleBasedPricing(
            BASE_PRICES,
            [MatineeDiscount(), WeekendSurcharge(), FormatSurcharge({"IMAX": Decimal("5")})],
        )

    def show(self, start: datetime, fmt: str = "2D") -> Screening:
        return Screening("s", self.movie, self.cinema, self.room, start, fmt)

    def test_weekday_evening_is_base_price(self) -> None:
        price = self.pricing.price(self.show(datetime(2026, 11, 4, 20)), self.room.layout.seat("A1"))
        self.assertEqual(price, Decimal("12.00"))

    def test_rules_stack_in_order(self) -> None:
        # VIP 24 -> matinee 20% off = 19.20 -> weekend +2 = 21.20 -> IMAX +5 = 26.20
        show = self.show(datetime(2026, 11, 7, 13), "IMAX")
        self.assertEqual(self.pricing.price(show, self.room.layout.seat("D1")), Decimal("26.20"))

    def test_rule_pipeline_matches_if_else_version(self) -> None:
        start = datetime(2026, 11, 8, 11)
        show = self.show(start, "IMAX")
        self.assertEqual(
            self.pricing.price(show, self.room.layout.seat("D1")),
            price_if_else("vip", start, "IMAX"),
        )

    def test_missing_base_price_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RuleBasedPricing({SeatType.STANDARD: Decimal("10")})


class BookingFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service, self.clock, self.payments = make_service()

    def test_happy_path_hold_pay_confirm(self) -> None:
        hold = self.service.hold_seats("s1", "alice", ["A1", "C1"])
        self.assertEqual(self.service.seat_map("s1")["A1"], SeatStatus.HELD)
        booking = self.service.checkout(hold.hold_id, "alice")
        self.assertIs(booking.status, BookingStatus.CONFIRMED)
        self.assertEqual(booking.total, Decimal("36.00"))  # 12 standard + 24 VIP
        self.assertEqual(self.service.seat_map("s1")["C1"], SeatStatus.BOOKED)
        self.assertEqual(len(self.service.available_seats("s1")), 10)

    def test_hold_is_all_or_nothing(self) -> None:
        self.service.hold_seats("s1", "alice", ["A2"])
        with self.assertRaises(SeatUnavailableError):
            self.service.hold_seats("s1", "bob", ["A1", "A2"])
        self.assertEqual(self.service.seat_map("s1")["A1"], SeatStatus.AVAILABLE)

    def test_invalid_selections(self) -> None:
        with self.assertRaises(ValueError):
            self.service.hold_seats("s1", "alice", [])
        with self.assertRaises(ValueError):
            self.service.hold_seats("s1", "alice", ["A1", "A1"])
        with self.assertRaises(NotFoundError):
            self.service.hold_seats("s1", "alice", ["Z1"])

    def test_hold_expires_and_seat_becomes_free(self) -> None:
        hold = self.service.hold_seats("s1", "alice", ["B1"])
        self.clock.advance(timedelta(minutes=8))
        self.assertEqual(self.service.seat_map("s1")["B1"], SeatStatus.AVAILABLE)
        with self.assertRaises(HoldExpiredError):
            self.service.checkout(hold.hold_id, "alice")
        self.assertEqual(self.payments.charges, {})  # never charged
        self.service.hold_seats("s1", "bob", ["B1"])  # someone else can take it

    def test_release_hold_is_idempotent(self) -> None:
        hold = self.service.hold_seats("s1", "alice", ["B1"])
        self.service.release_hold(hold.hold_id)
        self.service.release_hold(hold.hold_id)
        self.assertEqual(self.service.seat_map("s1")["B1"], SeatStatus.AVAILABLE)

    def test_other_customer_cannot_checkout_hold(self) -> None:
        hold = self.service.hold_seats("s1", "alice", ["B1"])
        with self.assertRaises(InvalidStateError):
            self.service.checkout(hold.hold_id, "bob")

    def test_declined_payment_releases_seats(self) -> None:
        hold = self.service.hold_seats("s1", "mallory", ["B2"])
        with self.assertRaises(PaymentDeclinedError):
            self.service.checkout(hold.hold_id, "mallory")
        self.assertEqual(self.service.seat_map("s1")["B2"], SeatStatus.AVAILABLE)
        failed = self.service.booking("B1")
        self.assertIs(failed.status, BookingStatus.FAILED)

    def test_hold_expiring_during_payment_is_refunded(self) -> None:
        clock = self.clock

        class SlowGateway(FakePaymentGateway):
            def charge(self, customer_id, amount, idempotency_key) -> PaymentReceipt:
                receipt = super().charge(customer_id, amount, idempotency_key)
                clock.advance(timedelta(minutes=10))  # bank took ages
                return receipt

        payments = SlowGateway()
        service, _, _ = make_service(payments=payments, clock=clock)
        hold = service.hold_seats("s1", "alice", ["A3"])
        with self.assertRaises(HoldExpiredError):
            service.checkout(hold.hold_id, "alice")
        self.assertEqual(len(payments.refunds), 1)
        self.assertEqual(payments.refunds[0][1], Decimal("12.00"))
        self.assertEqual(service.seat_map("s1")["A3"], SeatStatus.AVAILABLE)

    def test_payment_charge_is_idempotent(self) -> None:
        first = self.payments.charge("alice", Decimal("10"), "key-1")
        again = self.payments.charge("alice", Decimal("10"), "key-1")
        self.assertEqual(first, again)
        self.assertEqual(len(self.payments.charges), 1)

    def test_ticket_price_frozen_at_purchase(self) -> None:
        hold = self.service.hold_seats("s1", "alice", ["A1"])
        booking = self.service.checkout(hold.hold_id, "alice")
        self.service._pricing = RuleBasedPricing({t: Decimal("99") for t in SeatType})
        self.assertEqual(booking.tickets[0].price, Decimal("12.00"))


class CancellationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service, self.clock, self.payments = make_service()
        hold = self.service.hold_seats("s1", "alice", ["A1", "A2"])
        self.booking = self.service.checkout(hold.hold_id, "alice")

    def test_early_cancel_full_refund_and_seats_freed(self) -> None:
        refund = self.service.cancel_booking(self.booking.booking_id, "alice")
        self.assertEqual(refund, Decimal("24.00"))
        self.assertEqual(self.payments.refunds, [(self.booking.payment_id, Decimal("24.00"))])
        self.assertIs(self.booking.status, BookingStatus.CANCELLED)
        self.assertEqual(self.service.seat_map("s1")["A1"], SeatStatus.AVAILABLE)

    def test_late_cancel_no_refund(self) -> None:
        self.clock.now = SATURDAY_EVENING - timedelta(hours=1)
        self.assertEqual(self.service.cancel_booking(self.booking.booking_id, "alice"), Decimal("0.00"))
        self.assertEqual(self.payments.refunds, [])

    def test_cannot_cancel_after_start_or_twice_or_as_stranger(self) -> None:
        with self.assertRaises(InvalidStateError):
            self.service.cancel_booking(self.booking.booking_id, "bob")
        self.service.cancel_booking(self.booking.booking_id, "alice")
        with self.assertRaises(InvalidStateError):
            self.service.cancel_booking(self.booking.booking_id, "alice")

    def test_cannot_cancel_after_show_started(self) -> None:
        self.clock.now = SATURDAY_EVENING
        with self.assertRaises(InvalidStateError):
            self.service.cancel_booking(self.booking.booking_id, "alice")

    def test_refund_policy_boundary(self) -> None:
        policy = CutoffRefundPolicy(timedelta(hours=2))
        self.assertEqual(
            policy.refund_amount(self.booking, SATURDAY_EVENING - timedelta(hours=2)),
            self.booking.total,
        )


class ConcurrencyTests(unittest.TestCase):
    def test_many_threads_one_seat_one_winner(self) -> None:
        service, _, _ = make_service()
        winners: list[str] = []
        lock = threading.Lock()
        barrier = threading.Barrier(30)

        def attempt(i: int) -> None:
            barrier.wait()
            try:
                hold = service.hold_seats("s1", f"fan{i}", ["C2"])
                service.checkout(hold.hold_id, f"fan{i}")
                with lock:
                    winners.append(f"fan{i}")
            except SeatUnavailableError:
                pass

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(winners), 1)
        self.assertEqual(service.seat_map("s1")["C2"], SeatStatus.BOOKED)

    def test_parallel_buyers_of_different_seats_all_succeed(self) -> None:
        service, _, _ = make_service()
        seats = [s.seat_id for s in service.available_seats("s1")]
        errors: list[Exception] = []

        def buy(seat_id: str) -> None:
            try:
                hold = service.hold_seats("s1", f"u-{seat_id}", [seat_id])
                service.checkout(hold.hold_id, f"u-{seat_id}")
            except Exception as err:  # noqa: BLE001
                errors.append(err)

        threads = [threading.Thread(target=buy, args=(s,)) for s in seats]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(service.available_seats("s1"), [])


class AlternativesTests(unittest.TestCase):
    def test_seat_models_agree(self) -> None:
        ids = ["A1", "A2", "A3"]
        models = [
            SeatObjectsPerScreening(ids),
            LayoutWithAvailabilityMap(tuple(ids)),
            BitmapAvailability(tuple(ids), {s: i for i, s in enumerate(ids)}),
        ]
        for model in models:
            self.assertTrue(model.book("A2"))
            self.assertFalse(model.book("A2"))
            self.assertEqual(model.available(), ["A1", "A3"])

    def test_safe_bookers_allow_exactly_one_winner(self) -> None:
        for booker in [
            GlobalLockBooker(),
            PerScreeningLockBooker(),
            HoldWithExpiryBooker(timedelta(minutes=5)),
            OptimisticBooker(),
        ]:
            with self.subTest(booker=type(booker).__name__):
                self.assertEqual(race_for_one_seat(booker, buyers=15), 1)

    def test_hold_booker_expired_hold_can_be_taken(self) -> None:
        clock = ManualClock(FRIDAY_9AM)
        booker = HoldWithExpiryBooker(timedelta(minutes=5), clock)
        self.assertTrue(booker.hold("s", "A1", "alice"))
        self.assertFalse(booker.hold("s", "A1", "bob"))
        clock.advance(timedelta(minutes=6))
        self.assertTrue(booker.hold("s", "A1", "bob"))
        self.assertFalse(booker.confirm("s", "A1", "alice"))
        self.assertTrue(booker.confirm("s", "A1", "bob"))

    def test_search_approaches_agree(self) -> None:
        screenings = build_big_catalog(n_cinemas=20)
        linear, indexed, by_time = LinearScanCatalog(), ShowtimeIndex(), TimeSortedCatalog()
        for s in screenings:
            linear.add(s)
            indexed.add(s)
            by_time.add(s)
        day = date(2026, 11, 3)
        key = lambda s: s.screening_id  # noqa: E731
        self.assertEqual(
            sorted(linear.search(city="Boston", on=day), key=key),
            sorted(indexed.search(city="Boston", on=day), key=key),
        )
        self.assertEqual(
            sorted(linear.search(movie_id="m3"), key=key),
            sorted(indexed.search(movie_id="m3"), key=key),
        )
        window = by_time.starting_between(datetime(2026, 11, 3), datetime(2026, 11, 4))
        self.assertEqual(
            sorted(window, key=key), sorted(linear.search(on=day), key=key)
        )


if __name__ == "__main__":
    unittest.main()
