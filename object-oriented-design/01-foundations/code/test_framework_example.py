"""Tests for the library book-lending running example."""

import threading
import unittest
from datetime import date, timedelta
from decimal import Decimal

from framework_example import (
    Book,
    BorrowingBlockedError,
    CopyStatus,
    FineFree,
    FlatDailyFine,
    HighDemandSurcharge,
    LendingError,
    Library,
    Member,
    MembershipTier,
    NotAvailableError,
    ThreadSafeLibrary,
    UnknownItemError,
)

DUNE = Book("111", "Dune", "Frank Herbert")
EMMA = Book("222", "Emma", "Jane Austen")


class LibraryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.now = date(2026, 1, 10)
        self.library = Library(today=lambda: self.now)
        self.library.add_book(DUNE, copies=2)
        self.library.add_book(EMMA, copies=1)
        self.ada = Member("M1", "Ada")
        self.grace = Member("M2", "Grace")
        self.library.register_member(self.ada)
        self.library.register_member(self.grace)

    def advance(self, days: int) -> None:
        self.now += timedelta(days=days)


class TestCheckout(LibraryTestCase):
    def test_checkout_creates_loan_with_due_date(self):
        loan = self.library.checkout("M1", DUNE.isbn)
        self.assertEqual(loan.due_on, date(2026, 1, 31))
        self.assertIs(loan.copy.status, CopyStatus.ON_LOAN)
        self.assertEqual(self.ada.active_loans, [loan])
        self.assertEqual(self.library.available_count(DUNE.isbn), 1)

    def test_no_copies_left(self):
        self.library.checkout("M1", EMMA.isbn)
        with self.assertRaises(NotAvailableError):
            self.library.checkout("M2", EMMA.isbn)

    def test_loan_limit_depends_on_tier(self):
        for i in range(3):
            self.library.add_book(Book(f"x{i}", f"Book {i}", "Anon"))
            self.library.checkout("M1", f"x{i}")
        with self.assertRaises(BorrowingBlockedError):
            self.library.checkout("M1", DUNE.isbn)
        self.ada.tier = MembershipTier.PREMIUM
        self.library.checkout("M1", DUNE.isbn)  # now allowed

    def test_unpaid_fines_block_borrowing(self):
        self.ada.fines_owed = Decimal("5.00")
        with self.assertRaises(BorrowingBlockedError):
            self.library.checkout("M1", DUNE.isbn)

    def test_unknown_member_and_book(self):
        with self.assertRaises(UnknownItemError):
            self.library.checkout("nobody", DUNE.isbn)
        with self.assertRaises(UnknownItemError):
            self.library.checkout("M1", "no-such-isbn")


class TestReturnAndFines(LibraryTestCase):
    def test_on_time_return_is_free(self):
        loan = self.library.checkout("M1", DUNE.isbn)
        self.advance(21)
        self.assertEqual(self.library.return_copy(loan.copy.copy_id), Decimal("0"))
        self.assertIs(loan.copy.status, CopyStatus.AVAILABLE)
        self.assertEqual(loan.returned_on, self.now)
        self.assertEqual(self.ada.active_loans, [])

    def test_late_return_charges_per_day(self):
        loan = self.library.checkout("M1", DUNE.isbn)
        self.advance(21 + 3)
        self.assertEqual(self.library.return_copy(loan.copy.copy_id), Decimal("0.75"))
        self.assertEqual(self.ada.fines_owed, Decimal("0.75"))

    def test_fine_is_capped(self):
        loan = self.library.checkout("M1", DUNE.isbn)
        self.advance(365)
        self.assertEqual(self.library.return_copy(loan.copy.copy_id), Decimal("10.00"))

    def test_fine_policy_is_swappable(self):
        library = Library(fine_policy=FineFree(), today=lambda: self.now)
        library.add_book(DUNE)
        library.register_member(Member("M9", "Linus"))
        loan = library.checkout("M9", DUNE.isbn)
        self.advance(100)
        self.assertEqual(library.return_copy(loan.copy.copy_id), Decimal("0.00"))

    def test_custom_flat_fine(self):
        policy = FlatDailyFine(per_day=Decimal("1.00"), cap=Decimal("3.00"))
        library = Library(fine_policy=policy, today=lambda: self.now)
        library.add_book(DUNE)
        library.register_member(Member("M9", "Linus"))
        loan = library.checkout("M9", DUNE.isbn)
        self.advance(21 + 2)
        self.assertEqual(library.return_copy(loan.copy.copy_id), Decimal("2.00"))

    def test_high_demand_surcharge_decorates_another_policy(self):
        policy = HighDemandSurcharge(FlatDailyFine(), isbns={DUNE.isbn})
        library = Library(fine_policy=policy, today=lambda: self.now)
        library.add_book(DUNE)
        library.add_book(EMMA)
        library.register_member(Member("M9", "Linus"))
        dune_loan = library.checkout("M9", DUNE.isbn)
        emma_loan = library.checkout("M9", EMMA.isbn)
        self.advance(21 + 3)
        self.assertEqual(library.return_copy(dune_loan.copy.copy_id), Decimal("1.50"))
        self.assertEqual(library.return_copy(emma_loan.copy.copy_id), Decimal("0.75"))

    def test_returning_a_copy_twice_fails(self):
        loan = self.library.checkout("M1", DUNE.isbn)
        self.library.return_copy(loan.copy.copy_id)
        with self.assertRaises(UnknownItemError):
            self.library.return_copy(loan.copy.copy_id)

    def test_pay_fine(self):
        self.ada.fines_owed = Decimal("2.50")
        self.assertEqual(self.library.pay_fine("M1", Decimal("1.00")), Decimal("1.50"))
        with self.assertRaises(ValueError):
            self.library.pay_fine("M1", Decimal("9.00"))
        with self.assertRaises(ValueError):
            self.library.pay_fine("M1", Decimal("0"))


class TestHolds(LibraryTestCase):
    def test_returned_copy_goes_to_first_holder(self):
        loan = self.library.checkout("M1", EMMA.isbn)
        self.assertEqual(self.library.place_hold("M2", EMMA.isbn), 1)
        self.library.return_copy(loan.copy.copy_id)
        self.assertIs(loan.copy.status, CopyStatus.ON_HOLD_SHELF)
        self.assertEqual(self.library.available_count(EMMA.isbn), 0)
        with self.assertRaises(NotAvailableError):
            self.library.checkout("M1", EMMA.isbn)  # someone else is waiting
        grace_loan = self.library.checkout("M2", EMMA.isbn)
        self.assertIs(grace_loan.copy, loan.copy)

    def test_holds_are_first_come_first_served(self):
        self.library.register_member(Member("M3", "Alan"))
        loan = self.library.checkout("M1", EMMA.isbn)
        self.library.place_hold("M2", EMMA.isbn)
        self.assertEqual(self.library.place_hold("M3", EMMA.isbn), 2)
        self.library.return_copy(loan.copy.copy_id)
        with self.assertRaises(NotAvailableError):
            self.library.checkout("M3", EMMA.isbn)
        self.library.checkout("M2", EMMA.isbn)

    def test_cannot_hold_when_copy_on_shelf(self):
        with self.assertRaises(LendingError):
            self.library.place_hold("M1", DUNE.isbn)

    def test_duplicate_hold_rejected(self):
        self.library.checkout("M1", EMMA.isbn)
        self.library.place_hold("M2", EMMA.isbn)
        with self.assertRaises(LendingError):
            self.library.place_hold("M2", EMMA.isbn)


class TestHoldNotifications(LibraryTestCase):
    def test_listener_hears_when_hold_is_ready(self):
        heard = []

        class Recorder:
            def hold_ready(self, member, copy):
                heard.append((member.name, copy.copy_id))

        self.library.subscribe(Recorder())
        loan = self.library.checkout("M1", EMMA.isbn)
        self.library.place_hold("M2", EMMA.isbn)
        self.assertEqual(heard, [])
        self.library.return_copy(loan.copy.copy_id)
        self.assertEqual(heard, [("Grace", loan.copy.copy_id)])

    def test_no_notification_without_waiting_members(self):
        heard = []

        class Recorder:
            def hold_ready(self, member, copy):
                heard.append(member)

        self.library.subscribe(Recorder())
        loan = self.library.checkout("M1", DUNE.isbn)
        self.library.return_copy(loan.copy.copy_id)
        self.assertEqual(heard, [])


class TestConcurrency(unittest.TestCase):
    def test_many_kiosks_racing_for_the_last_copy_create_one_loan(self):
        library = ThreadSafeLibrary(today=lambda: date(2026, 1, 10))
        library.add_book(EMMA, copies=1)
        kiosks = 20
        for i in range(kiosks):
            library.register_member(Member(f"K{i}", f"Kiosk user {i}"))
        start = threading.Barrier(kiosks)
        loans, refusals = [], []

        def borrow(member_id: str) -> None:
            start.wait()  # release every thread at once to maximise overlap
            try:
                loans.append(library.checkout(member_id, EMMA.isbn))
            except NotAvailableError:
                refusals.append(member_id)

        threads = [threading.Thread(target=borrow, args=(f"K{i}",)) for i in range(kiosks)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(loans), 1)
        self.assertEqual(len(refusals), kiosks - 1)


class TestSearch(LibraryTestCase):
    def test_search_matches_title_or_author_case_insensitively(self):
        self.assertEqual(self.library.search("dune"), [DUNE])
        self.assertEqual(self.library.search("AUSTEN"), [EMMA])
        self.assertEqual(self.library.search("zzz"), [])


if __name__ == "__main__":
    unittest.main()
