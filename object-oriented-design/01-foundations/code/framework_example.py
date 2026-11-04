"""Library book-lending system.

The running example for "The OOD Interview Framework" post. It is deliberately
small: the point is to show how each step of the framework (requirements ->
core objects -> class diagram -> code -> extensions) ends up as real code.
"""

from __future__ import annotations

import itertools
import threading
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Callable, Protocol


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LendingError(Exception):
    """Base class for every rule the library refuses to break."""


class UnknownItemError(LendingError):
    """A member, book or copy id that the library has never heard of."""


class NotAvailableError(LendingError):
    """No copy of the requested title can be lent right now."""


class BorrowingBlockedError(LendingError):
    """The member is not allowed to borrow (loan limit or unpaid fines)."""


# ---------------------------------------------------------------------------
# Value objects and entities
# ---------------------------------------------------------------------------


class CopyStatus(Enum):
    AVAILABLE = "available"
    ON_LOAN = "on loan"
    ON_HOLD_SHELF = "on hold shelf"  # set aside for the next member in the queue


class MembershipTier(Enum):
    STANDARD = 3  # the value is the maximum number of simultaneous loans
    PREMIUM = 10

    @property
    def loan_limit(self) -> int:
        return self.value


@dataclass(frozen=True)
class Book:
    """A title in the catalog. Immutable: one record shared by all its copies."""

    isbn: str
    title: str
    author: str


@dataclass(eq=False)  # an entity: identity matters, not field equality
class BookCopy:
    """One physical copy on a shelf. This is the thing that is actually lent."""

    copy_id: str
    book: Book
    status: CopyStatus = CopyStatus.AVAILABLE


@dataclass(eq=False)  # an entity: identity matters, not field equality
class Member:
    """A library card holder."""

    member_id: str
    name: str
    tier: MembershipTier = MembershipTier.STANDARD
    fines_owed: Decimal = Decimal("0.00")
    active_loans: list[Loan] = field(default_factory=list)

    def can_borrow(self, fine_block_threshold: Decimal) -> bool:
        return (
            len(self.active_loans) < self.tier.loan_limit
            and self.fines_owed < fine_block_threshold
        )


@dataclass(eq=False)  # an entity: identity matters, not field equality
class Loan:
    """Records that one member has one copy, from a date until a due date."""

    loan_id: int
    copy: BookCopy
    member: Member
    borrowed_on: date
    due_on: date
    returned_on: date | None = None

    def days_overdue(self, on: date) -> int:
        return max(0, (on - self.due_on).days)


# ---------------------------------------------------------------------------
# Fine policies (Strategy pattern): the rule that changes most often
# ---------------------------------------------------------------------------


class FinePolicy(ABC):
    """Decides how much a late return costs."""

    @abstractmethod
    def fine_for(self, loan: Loan, returned_on: date) -> Decimal: ...


class FlatDailyFine(FinePolicy):
    """A fixed amount per late day, capped so a lost-in-a-drawer book is not ruinous."""

    def __init__(self, per_day: Decimal = Decimal("0.25"), cap: Decimal = Decimal("10.00")):
        self.per_day = per_day
        self.cap = cap

    def fine_for(self, loan: Loan, returned_on: date) -> Decimal:
        return min(self.per_day * loan.days_overdue(returned_on), self.cap)


class FineFree(FinePolicy):
    """Many public libraries have dropped overdue fines entirely."""

    def fine_for(self, loan: Loan, returned_on: date) -> Decimal:
        return Decimal("0.00")


class HighDemandSurcharge(FinePolicy):
    """Decorator: multiplies another policy's fine for titles on a high-demand list."""

    def __init__(self, inner: FinePolicy, isbns: set[str], factor: Decimal = Decimal("2")):
        self.inner = inner
        self.isbns = frozenset(isbns)
        self.factor = factor

    def fine_for(self, loan: Loan, returned_on: date) -> Decimal:
        fine = self.inner.fine_for(loan, returned_on)
        return fine * self.factor if loan.copy.book.isbn in self.isbns else fine


# ---------------------------------------------------------------------------
# Notifications (Observer pattern): the library announces, listeners react
# ---------------------------------------------------------------------------


class HoldListener(Protocol):
    def hold_ready(self, member: Member, copy: BookCopy) -> None: ...


# ---------------------------------------------------------------------------
# The facade that coordinates everything
# ---------------------------------------------------------------------------


class Library:
    """Entry point for the lending use cases: check out, return, place a hold."""

    def __init__(
        self,
        fine_policy: FinePolicy | None = None,
        loan_period: timedelta = timedelta(days=21),
        fine_block_threshold: Decimal = Decimal("5.00"),
        today: Callable[[], date] = date.today,
    ):
        self._fine_policy = fine_policy or FlatDailyFine()
        self._loan_period = loan_period
        self._fine_block_threshold = fine_block_threshold
        self._today = today  # injected so tests can control time
        self._books: dict[str, Book] = {}
        self._copies_by_isbn: dict[str, list[BookCopy]] = {}
        self._members: dict[str, Member] = {}
        self._open_loans: dict[str, Loan] = {}  # copy_id -> loan
        self._holds: dict[str, deque[Member]] = {}  # isbn -> waiting members
        self._held_for: dict[str, Member] = {}  # copy_id -> member it is set aside for
        self._loan_ids = itertools.count(1)
        self._listeners: list[HoldListener] = []

    # -- setup -------------------------------------------------------------

    def add_book(self, book: Book, copies: int = 1) -> list[BookCopy]:
        self._books.setdefault(book.isbn, book)
        shelf = self._copies_by_isbn.setdefault(book.isbn, [])
        new_copies = []
        for _ in range(copies):
            copy = BookCopy(f"{book.isbn}-{len(shelf) + 1}", book)
            shelf.append(copy)
            new_copies.append(copy)
        return new_copies

    def register_member(self, member: Member) -> None:
        self._members[member.member_id] = member

    def subscribe(self, listener: HoldListener) -> None:
        self._listeners.append(listener)

    # -- queries -------------------------------------------------------------

    def search(self, text: str) -> list[Book]:
        needle = text.casefold()
        return [
            b for b in self._books.values()
            if needle in b.title.casefold() or needle in b.author.casefold()
        ]

    def available_count(self, isbn: str) -> int:
        return sum(c.status is CopyStatus.AVAILABLE for c in self._shelf(isbn))

    # -- use cases -------------------------------------------------------------

    def checkout(self, member_id: str, isbn: str) -> Loan:
        member = self._member(member_id)
        if not member.can_borrow(self._fine_block_threshold):
            raise BorrowingBlockedError(
                f"{member.name} has {len(member.active_loans)} loans "
                f"and owes ${member.fines_owed}"
            )
        copy = self._copy_for(member, isbn)
        today = self._today()
        loan = Loan(next(self._loan_ids), copy, member, today, today + self._loan_period)
        copy.status = CopyStatus.ON_LOAN
        self._held_for.pop(copy.copy_id, None)
        member.active_loans.append(loan)
        self._open_loans[copy.copy_id] = loan
        return loan

    def return_copy(self, copy_id: str) -> Decimal:
        """Close the loan, charge any fine, and route the copy to the next holder."""
        loan = self._open_loans.pop(copy_id, None)
        if loan is None:
            raise UnknownItemError(f"copy {copy_id} is not on loan")
        today = self._today()
        loan.returned_on = today
        loan.member.active_loans.remove(loan)
        fine = self._fine_policy.fine_for(loan, today)
        loan.member.fines_owed += fine
        self._route_returned_copy(loan.copy)
        return fine

    def place_hold(self, member_id: str, isbn: str) -> int:
        """Join the waiting list for a title. Returns the 1-based queue position."""
        member = self._member(member_id)
        self._shelf(isbn)  # validates the isbn
        if self.available_count(isbn) > 0:
            raise LendingError("a copy is on the shelf; check it out instead")
        queue = self._holds.setdefault(isbn, deque())
        if member in queue:
            raise LendingError(f"{member.name} already has a hold on {isbn}")
        queue.append(member)
        return len(queue)

    def pay_fine(self, member_id: str, amount: Decimal) -> Decimal:
        member = self._member(member_id)
        if amount <= 0 or amount > member.fines_owed:
            raise ValueError(f"payment must be between $0.01 and ${member.fines_owed}")
        member.fines_owed -= amount
        return member.fines_owed

    # -- helpers -------------------------------------------------------------

    def _member(self, member_id: str) -> Member:
        try:
            return self._members[member_id]
        except KeyError:
            raise UnknownItemError(f"no member {member_id}") from None

    def _shelf(self, isbn: str) -> list[BookCopy]:
        try:
            return self._copies_by_isbn[isbn]
        except KeyError:
            raise UnknownItemError(f"no book with ISBN {isbn}") from None

    def _copy_for(self, member: Member, isbn: str) -> BookCopy:
        # A copy waiting on the hold shelf for this member wins over the open shelf.
        for copy in self._shelf(isbn):
            if copy.status is CopyStatus.ON_HOLD_SHELF and self._held_for.get(copy.copy_id) is member:
                return copy
        for copy in self._shelf(isbn):
            if copy.status is CopyStatus.AVAILABLE:
                return copy
        raise NotAvailableError(f"no copy of {isbn} is available")

    def _route_returned_copy(self, copy: BookCopy) -> None:
        queue = self._holds.get(copy.book.isbn)
        if queue:
            member = queue.popleft()
            self._held_for[copy.copy_id] = member
            copy.status = CopyStatus.ON_HOLD_SHELF
            for listener in self._listeners:
                listener.hold_ready(member, copy)
        else:
            copy.status = CopyStatus.AVAILABLE


class ThreadSafeLibrary(Library):
    """Same rules, but each use case runs as one atomic step under a lock.

    One lock for the whole library is the simplest correct choice: it turns
    every check-then-act sequence (is a copy free? then lend it) into a single
    indivisible operation. Finer-grained locks are an optimisation for later.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def checkout(self, member_id: str, isbn: str) -> Loan:
        with self._lock:
            return super().checkout(member_id, isbn)

    def return_copy(self, copy_id: str) -> Decimal:
        with self._lock:
            return super().return_copy(copy_id)

    def place_hold(self, member_id: str, isbn: str) -> int:
        with self._lock:
            return super().place_hold(member_id, isbn)

    def pay_fine(self, member_id: str, amount: Decimal) -> Decimal:
        with self._lock:
            return super().pay_fine(member_id, amount)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


class PrintNotifier:
    """Stands in for an email or SMS sender in the demo."""

    def hold_ready(self, member: Member, copy: BookCopy) -> None:
        print(f"  [notify] {member.name}: '{copy.book.title}' is waiting for you")


def demo() -> None:
    clock = [date(2026, 3, 1)]
    library = Library(today=lambda: clock[0])
    library.subscribe(PrintNotifier())
    dune = Book("9780441172719", "Dune", "Frank Herbert")
    library.add_book(dune, copies=1)
    library.register_member(Member("M1", "Ada"))
    library.register_member(Member("M2", "Grace"))

    loan = library.checkout("M1", dune.isbn)
    print(f"Ada borrows '{dune.title}' (copy {loan.copy.copy_id}), due {loan.due_on}")

    position = library.place_hold("M2", dune.isbn)
    print(f"Grace places a hold, position {position} in the queue")

    clock[0] = loan.due_on + timedelta(days=4)
    fine = library.return_copy(loan.copy.copy_id)
    print(f"Ada returns it 4 days late on {clock[0]} and is fined ${fine}")
    print(f"Copy status is now: {loan.copy.status.value}")

    try:
        library.checkout("M1", dune.isbn)
    except NotAvailableError as exc:
        print(f"Ada tries to borrow it again: refused ({exc})")

    grace_loan = library.checkout("M2", dune.isbn)
    print(f"Grace picks up her hold, due {grace_loan.due_on}")


if __name__ == "__main__":
    demo()
