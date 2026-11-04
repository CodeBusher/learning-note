"""Tests for the restaurant case study. Run: python3 -m unittest discover -s <this folder> -v"""

from __future__ import annotations

import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from alternatives import (
    AddBacon,
    BaseDish,
    CombineTablesAssignment,
    CommandQueueKitchen,
    DeliveryOrderAdapter,
    ExactStartTimeBook,
    FireItem,
    FirstFitAssignment,
    IntervalBook,
    NoOnion,
    StatefulLine,
    naive_equal_split,
)
from restaurant import (
    BestFitAssignment,
    Bill,
    BillingError,
    ByItemSplit,
    CustomSplit,
    EqualSplit,
    InvalidTransition,
    KitchenDisplay,
    LineStatus,
    ManualClock,
    MenuError,
    NoTableAvailable,
    OrderSource,
    ReservationBook,
    ReservationNotFound,
    ReservationStatus,
    Restaurant,
    RestaurantError,
    Station,
    Table,
    TimeSlot,
    allocate,
    sample_menu,
    sample_tables,
)

FRIDAY_5PM = datetime(2026, 11, 6, 17, 0)
SEVEN = datetime(2026, 11, 6, 19, 0)


def make_restaurant(**kwargs) -> tuple[Restaurant, ManualClock]:
    clock = ManualClock(FRIDAY_5PM)
    return Restaurant("Test", sample_menu(), sample_tables(), clock=clock, **kwargs), clock


class TimeSlotTests(unittest.TestCase):
    def test_overlap_rules_are_half_open(self) -> None:
        a = TimeSlot(SEVEN, SEVEN + timedelta(minutes=90))
        self.assertTrue(a.overlaps(TimeSlot(SEVEN + timedelta(minutes=30), SEVEN + timedelta(hours=2))))
        back_to_back = TimeSlot(a.end, a.end + timedelta(hours=1))
        self.assertFalse(a.overlaps(back_to_back))

    def test_empty_slot_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TimeSlot(SEVEN, SEVEN)


class ReservationTests(unittest.TestCase):
    def test_best_fit_picks_smallest_table(self) -> None:
        r, _ = make_restaurant()
        self.assertEqual(r.book("Ana", 2, SEVEN).tables[0].capacity, 2)
        self.assertEqual(r.book("Bo", 3, SEVEN).tables[0].capacity, 4)

    def test_overlapping_bookings_use_different_tables(self) -> None:
        r, _ = make_restaurant()
        first = r.book("Ana", 2, SEVEN)
        second = r.book("Bo", 2, SEVEN + timedelta(minutes=30))
        self.assertNotEqual(first.tables, second.tables)

    def test_back_to_back_bookings_share_a_table(self) -> None:
        book = ReservationBook([Table(1, 2)], turn_time=lambda _: timedelta(hours=1))
        book.book("Ana", 2, SEVEN)
        nine = book.book("Bo", 2, SEVEN + timedelta(hours=1))
        self.assertEqual(nine.tables[0].table_id, 1)

    def test_no_table_raises(self) -> None:
        r, _ = make_restaurant()
        with self.assertRaises(NoTableAvailable):
            r.book("Huge", 20, SEVEN)

    def test_cancel_frees_the_table(self) -> None:
        book = ReservationBook([Table(1, 4)])
        res = book.book("Ana", 4, SEVEN)
        with self.assertRaises(NoTableAvailable):
            book.book("Bo", 4, SEVEN)
        book.cancel(res.reservation_id)
        self.assertEqual(book.book("Bo", 4, SEVEN).party_name, "Bo")

    def test_cannot_cancel_twice(self) -> None:
        r, _ = make_restaurant()
        res = r.book("Ana", 2, SEVEN)
        r.cancel_reservation(res.reservation_id)
        with self.assertRaises(InvalidTransition):
            r.cancel_reservation(res.reservation_id)

    def test_available_times_skip_full_slots(self) -> None:
        book = ReservationBook([Table(1, 4)], turn_time=lambda _: timedelta(hours=1))
        book.book("Ana", 4, SEVEN)
        starts = book.available_starts(4, SEVEN - timedelta(hours=1), SEVEN + timedelta(hours=1),
                                       step=timedelta(minutes=30))
        self.assertEqual(starts, [SEVEN - timedelta(hours=1), SEVEN + timedelta(hours=1)])

    def test_booking_in_past_rejected(self) -> None:
        r, _ = make_restaurant()
        with self.assertRaises(ValueError):
            r.book("Ana", 2, FRIDAY_5PM - timedelta(minutes=1))

    def test_bad_party_size(self) -> None:
        r, _ = make_restaurant()
        with self.assertRaises(ValueError):
            r.book("Ana", 0, SEVEN)

    def test_check_in_by_name_case_insensitive(self) -> None:
        r, clock = make_restaurant()
        res = r.book("Garcia", 4, SEVEN)
        clock.now = SEVEN - timedelta(minutes=10)
        order = r.check_in("  garcia ")
        self.assertIs(order.reservation, res)
        self.assertIs(res.status, ReservationStatus.SEATED)

    def test_check_in_unknown_name(self) -> None:
        r, _ = make_restaurant()
        with self.assertRaises(ReservationNotFound):
            r.check_in("Nobody")

    def test_walk_in_blocked_by_upcoming_reservation(self) -> None:
        clock = ManualClock(SEVEN - timedelta(minutes=30))
        r = Restaurant("Tiny", sample_menu(), [Table(1, 2)], clock=clock)
        r.book("Ana", 2, SEVEN)
        with self.assertRaises(NoTableAvailable):
            r.seat_walk_in("Bo", 2)

    def test_no_show_and_completion(self) -> None:
        r, _ = make_restaurant()
        res = r.book("Ana", 2, SEVEN)
        r.reservations.mark_no_show(res.reservation_id)
        self.assertFalse(res.holds_tables)
        with self.assertRaises(InvalidTransition):
            r.reservations.complete(res.reservation_id)

    def test_concurrent_hosts_cannot_double_book(self) -> None:
        book = ReservationBook([Table(1, 4)])
        results: list[str] = []
        barrier = threading.Barrier(8)

        def host(n: int) -> None:
            barrier.wait()
            try:
                book.book(f"party{n}", 4, SEVEN)
                results.append("ok")
            except NoTableAvailable:
                results.append("full")

        threads = [threading.Thread(target=host, args=(n,)) for n in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("full"), 7)


class OrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.r, self.clock = make_restaurant()
        self.order = self.r.seat_walk_in("Ana", 2)
        self.grill = KitchenDisplay("grill")
        self.expo = KitchenDisplay("expo")
        self.r.kitchen.subscribe(self.grill, Station.GRILL)
        self.r.kitchen.subscribe(self.expo)

    def test_modifiers_change_price(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger", 2, ["add bacon", "no onion"])
        self.assertEqual(line.unit_price, Decimal("19.00"))
        self.assertEqual(line.total, Decimal("38.00"))

    def test_unknown_modifier_and_item(self) -> None:
        with self.assertRaises(MenuError):
            self.r.add_item(self.order.order_id, "burger", 1, ["extra unicorn"])
        with self.assertRaises(MenuError):
            self.r.add_item(self.order.order_id, "lobster")

    def test_eighty_sixed_item_cannot_be_ordered(self) -> None:
        self.r.menu.eighty_six("salmon")
        with self.assertRaises(MenuError):
            self.r.add_item(self.order.order_id, "salmon")
        self.r.menu.restock("salmon")
        self.r.add_item(self.order.order_id, "salmon")

    def test_fire_routes_one_ticket_per_station(self) -> None:
        self.r.add_item(self.order.order_id, "burger")
        self.r.add_item(self.order.order_id, "salmon")
        self.r.add_item(self.order.order_id, "lemonade")
        tickets = self.r.fire(self.order.order_id)
        self.assertEqual({t.station for t in tickets}, {Station.GRILL, Station.BAR})
        self.assertEqual(len(self.grill.open_tickets()), 1)
        self.assertEqual(len(self.grill.open_tickets()[0].lines), 2)
        self.assertEqual(len(self.expo.open_tickets()), 2)

    def test_fire_twice_only_sends_new_lines(self) -> None:
        self.r.add_item(self.order.order_id, "burger")
        self.r.fire(self.order.order_id)
        self.assertEqual(self.r.fire(self.order.order_id), [])
        self.r.add_item(self.order.order_id, "salmon")
        (ticket,) = self.r.fire(self.order.order_id)
        self.assertEqual(ticket.lines[0].item.item_id, "salmon")

    def test_full_lifecycle(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        self.r.fire(self.order.order_id)
        self.assertIs(line.status, LineStatus.FIRED)
        self.grill.bump(self.grill.open_tickets()[0].ticket_id)
        self.assertIs(line.status, LineStatus.READY)
        self.r.serve(self.order.order_id, line.line_id)
        self.assertIs(line.status, LineStatus.SERVED)

    def test_cannot_serve_before_ready(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        with self.assertRaises(InvalidTransition):
            self.r.serve(self.order.order_id, line.line_id)

    def test_quantity_change_only_before_fire(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        self.r.change_quantity(self.order.order_id, line.line_id, 3)
        self.assertEqual(line.quantity, 3)
        self.r.fire(self.order.order_id)
        with self.assertRaises(InvalidTransition):
            self.r.change_quantity(self.order.order_id, line.line_id, 1)

    def test_void_fired_line_notifies_kitchen_and_drops_empty_ticket(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        self.r.fire(self.order.order_id)
        self.r.void_item(self.order.order_id, line.line_id)
        self.assertTrue(self.grill.messages[-1].startswith("VOID"))
        self.assertEqual(self.grill.open_tickets(), [])

    def test_void_pending_line_is_silent(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        self.r.void_item(self.order.order_id, line.line_id)
        self.assertEqual(self.grill.messages, [])
        self.assertEqual(self.r.fire(self.order.order_id), [])

    def test_cannot_void_served_line(self) -> None:
        line = self.r.add_item(self.order.order_id, "burger")
        self.r.fire(self.order.order_id)
        self.grill.bump(self.grill.open_tickets()[0].ticket_id)
        self.r.serve(self.order.order_id, line.line_id)
        with self.assertRaises(InvalidTransition):
            self.r.void_item(self.order.order_id, line.line_id)

    def test_close_requires_everything_served(self) -> None:
        self.r.add_item(self.order.order_id, "burger")
        with self.assertRaises(BillingError):
            self.r.close_check(self.order.order_id)

    def test_close_completes_reservation_and_locks_order(self) -> None:
        line = self.r.add_item(self.order.order_id, "lemonade")
        bar = KitchenDisplay("bar")
        self.r.kitchen.subscribe(bar, Station.BAR)
        self.r.fire(self.order.order_id)
        bar.bump(bar.open_tickets()[0].ticket_id)
        self.r.serve(self.order.order_id, line.line_id)
        self.r.close_check(self.order.order_id)
        self.assertIs(self.order.reservation.status, ReservationStatus.COMPLETED)
        with self.assertRaises(RestaurantError):
            self.r.add_item(self.order.order_id, "cake")

    def test_takeout_order_has_no_table(self) -> None:
        order = self.r.open_off_premise("Kim", OrderSource.TAKEOUT)
        self.assertIsNone(order.reservation)
        self.assertEqual(order.label, "Takeout: Kim")
        with self.assertRaises(ValueError):
            self.r.open_off_premise("Kim", OrderSource.DINE_IN)


class BillingTests(unittest.TestCase):
    def _bill(self, party_size: int = 2):
        r, _ = make_restaurant()
        order = r.seat_walk_in("Ana", party_size)
        a = r.add_item(order.order_id, "burger")  # 16.50
        b = r.add_item(order.order_id, "salad")  # 11.00
        c = r.add_item(order.order_id, "cake")  # 9.00
        return r.bill(order.order_id), (a, b, c)

    def test_totals(self) -> None:
        bill, _ = self._bill()
        self.assertEqual(bill.subtotal, Decimal("36.50"))
        self.assertEqual(bill.tax, Decimal("2.92"))
        self.assertEqual(bill.total, Decimal("39.42"))

    def test_voided_lines_not_billed(self) -> None:
        r, _ = make_restaurant()
        order = r.seat_walk_in("Ana", 2)
        line = r.add_item(order.order_id, "burger")
        r.add_item(order.order_id, "cake")
        r.void_item(order.order_id, line.line_id)
        self.assertEqual(r.bill(order.order_id).subtotal, Decimal("9.00"))

    def test_large_party_gets_service_charge(self) -> None:
        bill, _ = self._bill(party_size=6)
        self.assertEqual(bill.service_charge, Decimal("6.57"))

    def test_equal_split_sums_to_total(self) -> None:
        bill, _ = self._bill()
        shares = bill.split(EqualSplit(["A", "B", "C"]))
        self.assertEqual(sum(shares.values()), bill.total)
        self.assertLessEqual(max(shares.values()) - min(shares.values()), Decimal("0.01"))

    def test_by_item_split_with_shared_dish(self) -> None:
        bill, (burger, salad, cake) = self._bill()
        shares = bill.split(
            ByItemSplit({burger.line_id: ["A"], salad.line_id: ["B"], cake.line_id: ["A", "B"]})
        )
        self.assertEqual(sum(shares.values()), bill.total)
        self.assertGreater(shares["A"], shares["B"])

    def test_by_item_split_requires_every_line(self) -> None:
        bill, (burger, _, _) = self._bill()
        with self.assertRaises(BillingError):
            bill.split(ByItemSplit({burger.line_id: ["A"]}))

    def test_custom_split_must_match_total(self) -> None:
        bill, _ = self._bill()
        ok = bill.split(CustomSplit({"A": Decimal("30.00"), "B": Decimal("9.42")}))
        self.assertEqual(ok["B"], Decimal("9.42"))
        with self.assertRaises(BillingError):
            bill.split(CustomSplit({"A": Decimal("30.00")}))

    def test_allocate_largest_remainder(self) -> None:
        shares = allocate(Decimal("100.00"), {"A": Decimal(1), "B": Decimal(1), "C": Decimal(1)})
        self.assertEqual(sorted(shares.values()), [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")])
        with self.assertRaises(BillingError):
            allocate(Decimal("10"), {})

    def test_bill_is_empty_for_empty_order(self) -> None:
        r, _ = make_restaurant()
        order = r.seat_walk_in("Ana", 2)
        self.assertEqual(Bill.for_order(order, Decimal("0.08")).total, Decimal("0.00"))


class AlternativesTests(unittest.TestCase):
    def test_first_fit_wastes_big_table(self) -> None:
        tables = [Table(1, 8), Table(2, 2)]
        self.assertEqual(FirstFitAssignment().choose(2, tables)[0].table_id, 1)
        self.assertEqual(BestFitAssignment().choose(2, tables)[0].table_id, 2)

    def test_combine_tables_stays_in_one_zone(self) -> None:
        tables = [Table(1, 4, "a"), Table(2, 4, "b"), Table(3, 4, "b")]
        combo = CombineTablesAssignment().choose(7, tables)
        self.assertEqual([t.table_id for t in combo], [2, 3])
        self.assertIsNone(CombineTablesAssignment(max_tables=2).choose(13, tables))

    def test_combine_tables_plugs_into_reservation_book(self) -> None:
        book = ReservationBook(sample_tables(), CombineTablesAssignment())
        res = book.book("Big group", 12, SEVEN)
        self.assertGreaterEqual(sum(t.capacity for t in res.tables), 12)

    def test_exact_start_book_misses_overlap(self) -> None:
        table = Table(1, 2)
        exact, interval = ExactStartTimeBook(), IntervalBook(timedelta(minutes=90))
        exact.book(table, SEVEN)
        interval.book(table, SEVEN)
        later = SEVEN + timedelta(minutes=30)
        self.assertTrue(exact.is_free(table, later))
        self.assertFalse(interval.is_free(table, later))

    def test_command_queue_undo(self) -> None:
        kitchen = CommandQueueKitchen()
        burger = sample_menu().get("burger")
        kitchen.submit(FireItem("T1", burger))
        self.assertEqual(kitchen.board, {})  # nothing happens until drained
        kitchen.drain()
        self.assertEqual(kitchen.board["grill"], ["T1: Smash Burger"])
        kitchen.undo_last()
        self.assertEqual(kitchen.board["grill"], [])

    def test_state_pattern_rejects_bad_events(self) -> None:
        line = StatefulLine(sample_menu().get("burger"))
        with self.assertRaises(InvalidTransition):
            line.serve()
        line.fire()
        line.bump()
        line.serve()
        self.assertEqual(line.state.name, "served")

    def test_naive_split_loses_a_cent(self) -> None:
        self.assertEqual(sum(naive_equal_split(Decimal("100.00"), 3)), Decimal("99.99"))

    def test_decorator_stacks(self) -> None:
        dish = NoOnion(AddBacon(BaseDish(sample_menu().get("burger"))))
        self.assertEqual(dish.price(), Decimal("19.00"))
        self.assertIn("no onion", dish.description())

    def test_delivery_adapter(self) -> None:
        adapter = DeliveryOrderAdapter("X", {"x1": "burger"})
        self.assertEqual(adapter.to_lines({"items": [{"external_id": "x1", "qty": 2}]}),
                         [("burger", 2, [])])
        with self.assertRaises(MenuError):
            adapter.to_lines({"items": [{"external_id": "nope"}]})


if __name__ == "__main__":
    unittest.main()
