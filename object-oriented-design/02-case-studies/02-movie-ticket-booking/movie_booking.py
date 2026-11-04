"""Movie ticket booking system: the recommended design.

Layers, from the bottom up:

* Catalog (static data): Movie, Seat, SeatLayout, Room, Cinema, Screening.
* Live state (one per screening): SeatInventory, with its own lock and
  time-limited SeatHolds.
* Money: PricingStrategy / PricingRule, PaymentGateway, RefundPolicy.
* Search: ShowtimeIndex.
* Facade: BookingService, the single entry point clients talk to.

Standard library only. Run ``python3 movie_booking.py`` for a demo.
"""

from __future__ import annotations

import itertools
import threading
from abc import ABC, abstractmethod
from bisect import insort
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Protocol

Clock = Callable[[], datetime]
CENTS = Decimal("0.01")


def money(value: Decimal | int | str) -> Decimal:
    """Round to whole cents. Money is always Decimal, never float."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class BookingError(Exception):
    """Base class for every error this module raises on purpose."""


class NotFoundError(BookingError):
    """An id (movie, cinema, room, screening, seat, hold, booking) is unknown."""


class SchedulingConflictError(BookingError):
    """Two screenings would overlap in the same room."""


class SeatUnavailableError(BookingError):
    """At least one requested seat is already held or booked."""


class HoldExpiredError(BookingError):
    """The seat hold timed out (or was released) before checkout finished."""


class PaymentDeclinedError(BookingError):
    """The payment gateway refused the charge."""


class InvalidStateError(BookingError):
    """The operation is not allowed in the object's current state."""


# --------------------------------------------------------------------------
# Catalog: things that rarely change
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Movie:
    """A film, independent of where or when it is shown."""

    movie_id: str
    title: str
    duration: timedelta
    genre: str = ""
    rating: str = "NR"


class SeatType(Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"
    ACCESSIBLE = "accessible"


@dataclass(frozen=True)
class Seat:
    """A physical seat. It knows its position and type, not whether it is sold."""

    row: str
    number: int
    seat_type: SeatType = SeatType.STANDARD

    @property
    def seat_id(self) -> str:
        return f"{self.row}{self.number}"


class SeatLayout:
    """The immutable seat map of a room, shared by every screening in it."""

    def __init__(self, seats: Iterable[Seat]) -> None:
        self._seats: dict[str, Seat] = {}
        for seat in seats:
            if seat.seat_id in self._seats:
                raise ValueError(f"duplicate seat {seat.seat_id}")
            self._seats[seat.seat_id] = seat
        if not self._seats:
            raise ValueError("a layout needs at least one seat")

    @classmethod
    def grid(
        cls,
        rows: str,
        seats_per_row: int,
        row_types: dict[str, SeatType] | None = None,
    ) -> SeatLayout:
        """Build a rectangular layout; ``row_types`` upgrades whole rows."""
        row_types = row_types or {}
        return cls(
            Seat(row, number, row_types.get(row, SeatType.STANDARD))
            for row in rows
            for number in range(1, seats_per_row + 1)
        )

    def seat(self, seat_id: str) -> Seat:
        try:
            return self._seats[seat_id]
        except KeyError:
            raise NotFoundError(f"no seat {seat_id!r} in this room") from None

    def __contains__(self, seat_id: object) -> bool:
        return seat_id in self._seats

    def __iter__(self) -> Iterator[Seat]:
        return iter(self._seats.values())

    def __len__(self) -> int:
        return len(self._seats)


@dataclass(frozen=True)
class Room:
    """An auditorium inside a cinema."""

    room_id: str
    name: str
    layout: SeatLayout


@dataclass(eq=False)
class Cinema:
    """A physical venue at one location; it owns (composes) its rooms."""

    cinema_id: str
    name: str
    city: str
    rooms: dict[str, Room] = field(default_factory=dict)

    def add_room(self, room: Room) -> None:
        if room.room_id in self.rooms:
            raise ValueError(f"room {room.room_id} already exists")
        self.rooms[room.room_id] = room

    def room(self, room_id: str) -> Room:
        try:
            return self.rooms[room_id]
        except KeyError:
            raise NotFoundError(f"no room {room_id!r} in {self.name}") from None


# Time to clean the room and let people out before the next show.
TURNOVER = timedelta(minutes=20)


@dataclass(frozen=True)
class Screening:
    """One showing of a movie in a room at a time ("showtime")."""

    screening_id: str
    movie: Movie
    cinema: Cinema
    room: Room
    start: datetime
    format: str = "2D"

    @property
    def end(self) -> datetime:
        return self.start + self.movie.duration

    def overlaps(self, other: Screening) -> bool:
        """True if both use the same room and their busy windows intersect."""
        if self.room is not other.room:
            return False
        return self.start < other.end + TURNOVER and other.start < self.end + TURNOVER


# --------------------------------------------------------------------------
# Pricing: Strategy for the overall policy, small rules inside it
# --------------------------------------------------------------------------
class PricingStrategy(Protocol):
    """Anything that can price one seat at one screening."""

    def price(self, screening: Screening, seat: Seat) -> Decimal: ...


class PricingRule(ABC):
    """One adjustment step. Rules are chained, each sees the previous result."""

    @abstractmethod
    def adjust(self, price: Decimal, screening: Screening, seat: Seat) -> Decimal: ...


@dataclass(frozen=True)
class MatineeDiscount(PricingRule):
    """Percentage off for shows that start before ``before_hour``."""

    before_hour: int = 16
    percent_off: Decimal = Decimal("20")

    def adjust(self, price: Decimal, screening: Screening, seat: Seat) -> Decimal:
        if screening.start.hour < self.before_hour:
            return price * (1 - self.percent_off / 100)
        return price


@dataclass(frozen=True)
class WeekendSurcharge(PricingRule):
    """Flat surcharge on Saturday and Sunday shows."""

    amount: Decimal = Decimal("2.00")

    def adjust(self, price: Decimal, screening: Screening, seat: Seat) -> Decimal:
        return price + self.amount if screening.start.weekday() >= 5 else price


@dataclass(frozen=True)
class FormatSurcharge(PricingRule):
    """Extra charge for premium formats such as IMAX or 3D."""

    surcharges: dict[str, Decimal] = field(default_factory=dict)

    def adjust(self, price: Decimal, screening: Screening, seat: Seat) -> Decimal:
        return price + self.surcharges.get(screening.format, Decimal("0"))


class RuleBasedPricing:
    """Base price by seat type, then a pipeline of rules. Never below zero."""

    def __init__(
        self, base_prices: dict[SeatType, Decimal], rules: Sequence[PricingRule] = ()
    ) -> None:
        missing = set(SeatType) - base_prices.keys()
        if missing:
            raise ValueError(f"no base price for {sorted(t.value for t in missing)}")
        self._base = dict(base_prices)
        self._rules = tuple(rules)

    def price(self, screening: Screening, seat: Seat) -> Decimal:
        amount = self._base[seat.seat_type]
        for rule in self._rules:
            amount = rule.adjust(amount, screening, seat)
        return money(max(amount, Decimal("0")))


# --------------------------------------------------------------------------
# Live seat state, one inventory per screening
# --------------------------------------------------------------------------
class SeatStatus(Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


@dataclass(frozen=True)
class SeatHold:
    """A short-lived reservation of seats while the customer pays."""

    hold_id: str
    screening_id: str
    customer_id: str
    seat_ids: frozenset[str]
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


_hold_ids = itertools.count(1)


class SeatInventory:
    """Which seats of ONE screening are free, held or booked.

    Every screening gets its own lock, so a rush on one blockbuster show never
    slows down bookings for any other show. All public methods are atomic.
    """

    def __init__(self, screening: Screening, clock: Clock, hold_ttl: timedelta) -> None:
        self.screening = screening
        self._layout = screening.room.layout
        self._clock = clock
        self._hold_ttl = hold_ttl
        self._lock = threading.Lock()
        self._booked: dict[str, str] = {}  # seat_id -> booking_id
        self._held_by: dict[str, str] = {}  # seat_id -> hold_id
        self._holds: dict[str, SeatHold] = {}  # hold_id -> hold

    # -- reads ------------------------------------------------------------
    def status(self, seat_id: str) -> SeatStatus:
        self._layout.seat(seat_id)  # validates the id
        with self._lock:
            self._expire_stale_holds()
            return self._status_unlocked(seat_id)

    def seat_map(self) -> dict[str, SeatStatus]:
        with self._lock:
            self._expire_stale_holds()
            return {s.seat_id: self._status_unlocked(s.seat_id) for s in self._layout}

    def get_hold(self, hold_id: str) -> SeatHold:
        with self._lock:
            self._expire_stale_holds()
            try:
                return self._holds[hold_id]
            except KeyError:
                raise HoldExpiredError(f"hold {hold_id} expired or released") from None

    # -- writes -----------------------------------------------------------
    def hold(self, seat_ids: Iterable[str], customer_id: str) -> SeatHold:
        """Hold all requested seats or none of them."""
        requested = list(seat_ids)
        if not requested:
            raise ValueError("select at least one seat")
        if len(set(requested)) != len(requested):
            raise ValueError("the same seat was selected twice")
        for seat_id in requested:
            self._layout.seat(seat_id)

        with self._lock:
            self._expire_stale_holds()
            taken = [s for s in requested if self._status_unlocked(s) is not SeatStatus.AVAILABLE]
            if taken:
                raise SeatUnavailableError(f"seats no longer available: {', '.join(taken)}")
            hold = SeatHold(
                hold_id=f"H{next(_hold_ids)}",
                screening_id=self.screening.screening_id,
                customer_id=customer_id,
                seat_ids=frozenset(requested),
                expires_at=self._clock() + self._hold_ttl,
            )
            self._holds[hold.hold_id] = hold
            for seat_id in requested:
                self._held_by[seat_id] = hold.hold_id
            return hold

    def release(self, hold_id: str) -> None:
        """Give held seats back. Safe to call twice."""
        with self._lock:
            self._drop_hold(hold_id)

    def confirm(self, hold_id: str, booking_id: str) -> None:
        """Turn a live hold into a permanent booking."""
        with self._lock:
            self._expire_stale_holds()
            hold = self._drop_hold(hold_id)
            if hold is None:
                raise HoldExpiredError(f"hold {hold_id} expired before payment finished")
            for seat_id in hold.seat_ids:
                self._booked[seat_id] = booking_id

    def free(self, seat_ids: Iterable[str], booking_id: str) -> None:
        """Release booked seats after a cancellation (only that booking's seats)."""
        with self._lock:
            for seat_id in seat_ids:
                if self._booked.get(seat_id) == booking_id:
                    del self._booked[seat_id]

    # -- helpers, caller must hold self._lock -----------------------------
    def _status_unlocked(self, seat_id: str) -> SeatStatus:
        if seat_id in self._booked:
            return SeatStatus.BOOKED
        if seat_id in self._held_by:
            return SeatStatus.HELD
        return SeatStatus.AVAILABLE

    def _drop_hold(self, hold_id: str) -> SeatHold | None:
        hold = self._holds.pop(hold_id, None)
        if hold is not None:
            for seat_id in hold.seat_ids:
                self._held_by.pop(seat_id, None)
        return hold

    def _expire_stale_holds(self) -> None:
        # Lazy expiry: no background thread, stale holds are swept whenever
        # someone looks. Correct because every read and write calls this first.
        now = self._clock()
        for hold_id in [h.hold_id for h in self._holds.values() if h.is_expired(now)]:
            self._drop_hold(hold_id)


# --------------------------------------------------------------------------
# Bookings, tickets, payments, refunds
# --------------------------------------------------------------------------
class BookingStatus(Enum):
    PENDING = "pending"  # seats held, payment in flight
    CONFIRMED = "confirmed"
    FAILED = "failed"  # payment declined or hold expired
    CANCELLED = "cancelled"  # confirmed, then cancelled by the customer


_ALLOWED = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.FAILED},
    BookingStatus.CONFIRMED: {BookingStatus.CANCELLED},
    BookingStatus.FAILED: set(),
    BookingStatus.CANCELLED: set(),
}


@dataclass(frozen=True)
class Ticket:
    """One seat at one screening. The price is frozen at purchase time."""

    ticket_id: str
    booking_id: str
    screening_id: str
    seat_id: str
    price: Decimal


@dataclass
class Booking:
    """An order: several tickets for one screening, paid for together."""

    booking_id: str
    customer_id: str
    screening: Screening
    tickets: tuple[Ticket, ...]
    created_at: datetime
    status: BookingStatus = BookingStatus.PENDING
    payment_id: str | None = None
    refunded: Decimal = Decimal("0.00")

    @property
    def total(self) -> Decimal:
        return money(sum((t.price for t in self.tickets), Decimal("0")))

    @property
    def seat_ids(self) -> list[str]:
        return [t.seat_id for t in self.tickets]

    def transition(self, new_status: BookingStatus) -> None:
        if new_status not in _ALLOWED[self.status]:
            raise InvalidStateError(
                f"booking {self.booking_id}: {self.status.value} -> {new_status.value} not allowed"
            )
        self.status = new_status


@dataclass(frozen=True)
class PaymentReceipt:
    payment_id: str
    amount: Decimal


class PaymentGateway(Protocol):
    """Stripe/Adyen-style gateway. ``idempotency_key`` makes retries safe."""

    def charge(self, customer_id: str, amount: Decimal, idempotency_key: str) -> PaymentReceipt: ...

    def refund(self, payment_id: str, amount: Decimal) -> None: ...


class FakePaymentGateway:
    """In-memory gateway for demos and tests."""

    def __init__(self, declined_customers: Iterable[str] = ()) -> None:
        self.declined = set(declined_customers)
        self.charges: dict[str, PaymentReceipt] = {}  # idempotency_key -> receipt
        self.refunds: list[tuple[str, Decimal]] = []
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def charge(self, customer_id: str, amount: Decimal, idempotency_key: str) -> PaymentReceipt:
        with self._lock:
            if idempotency_key in self.charges:  # a retry: do not charge twice
                return self.charges[idempotency_key]
            if customer_id in self.declined:
                raise PaymentDeclinedError(f"card declined for {customer_id}")
            receipt = PaymentReceipt(f"P{next(self._ids)}", amount)
            self.charges[idempotency_key] = receipt
            return receipt

    def refund(self, payment_id: str, amount: Decimal) -> None:
        with self._lock:
            self.refunds.append((payment_id, amount))


class RefundPolicy(Protocol):
    def refund_amount(self, booking: Booking, now: datetime) -> Decimal: ...


@dataclass(frozen=True)
class CutoffRefundPolicy:
    """Full refund up to ``cutoff`` before showtime, nothing after that."""

    cutoff: timedelta = timedelta(hours=2)

    def refund_amount(self, booking: Booking, now: datetime) -> Decimal:
        if now <= booking.screening.start - self.cutoff:
            return booking.total
        return Decimal("0.00")


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------
class ShowtimeIndex:
    """Secondary indexes so search never scans every screening."""

    def __init__(self) -> None:
        self._by_movie: dict[str, list[Screening]] = defaultdict(list)
        self._by_city_day: dict[tuple[str, date], list[Screening]] = defaultdict(list)

    def add(self, screening: Screening) -> None:
        by_start = lambda s: (s.start, s.screening_id)  # noqa: E731
        insort(self._by_movie[screening.movie.movie_id], screening, key=by_start)
        key = (screening.cinema.city.lower(), screening.start.date())
        insort(self._by_city_day[key], screening, key=by_start)

    def search(
        self,
        movie_id: str | None = None,
        city: str | None = None,
        on: date | None = None,
    ) -> list[Screening]:
        # Start from the most selective index, then filter the small result.
        if city is not None and on is not None:
            candidates = self._by_city_day.get((city.lower(), on), [])
        elif movie_id is not None:
            candidates = self._by_movie.get(movie_id, [])
        else:
            raise ValueError("search by movie, or by city and day")
        return [
            s
            for s in candidates
            if (movie_id is None or s.movie.movie_id == movie_id)
            and (city is None or s.cinema.city.lower() == city.lower())
            and (on is None or s.start.date() == on)
        ]


# --------------------------------------------------------------------------
# Facade
# --------------------------------------------------------------------------
class BookingService:
    """The one class clients call: browse, hold, pay, cancel."""

    def __init__(
        self,
        pricing: PricingStrategy,
        payments: PaymentGateway,
        refund_policy: RefundPolicy | None = None,
        clock: Clock = datetime.now,
        hold_ttl: timedelta = timedelta(minutes=8),
    ) -> None:
        self._pricing = pricing
        self._payments = payments
        self._refund_policy = refund_policy or CutoffRefundPolicy()
        self._clock = clock
        self._hold_ttl = hold_ttl
        self._movies: dict[str, Movie] = {}
        self._cinemas: dict[str, Cinema] = {}
        self._screenings: dict[str, Screening] = {}
        self._inventories: dict[str, SeatInventory] = {}
        self._screening_of_hold: dict[str, str] = {}
        self._bookings: dict[str, Booking] = {}
        self._index = ShowtimeIndex()
        self._booking_ids = itertools.count(1)
        # Guards the registries above. It is held only for dict updates,
        # never while seats are checked or a payment is in flight.
        self._registry_lock = threading.Lock()

    # -- catalog management -----------------------------------------------
    def add_movie(self, movie: Movie) -> None:
        with self._registry_lock:
            self._movies[movie.movie_id] = movie

    def add_cinema(self, cinema: Cinema) -> None:
        with self._registry_lock:
            self._cinemas[cinema.cinema_id] = cinema

    def schedule_screening(
        self,
        screening_id: str,
        movie_id: str,
        cinema_id: str,
        room_id: str,
        start: datetime,
        format: str = "2D",
    ) -> Screening:
        with self._registry_lock:
            if screening_id in self._screenings:
                raise ValueError(f"screening {screening_id} already exists")
            movie = self._lookup(self._movies, movie_id, "movie")
            cinema = self._lookup(self._cinemas, cinema_id, "cinema")
            screening = Screening(screening_id, movie, cinema, cinema.room(room_id), start, format)
            clash = next((s for s in self._screenings.values() if s.overlaps(screening)), None)
            if clash is not None:
                raise SchedulingConflictError(
                    f"{room_id} is busy with {clash.movie.title} at {clash.start:%H:%M}"
                )
            self._screenings[screening_id] = screening
            self._inventories[screening_id] = SeatInventory(screening, self._clock, self._hold_ttl)
            self._index.add(screening)
            return screening

    # -- browsing -----------------------------------------------------------
    def search_showtimes(
        self, movie_id: str | None = None, city: str | None = None, on: date | None = None
    ) -> list[Screening]:
        return self._index.search(movie_id=movie_id, city=city, on=on)

    def seat_map(self, screening_id: str) -> dict[str, SeatStatus]:
        return self._inventory(screening_id).seat_map()

    def available_seats(self, screening_id: str) -> list[Seat]:
        inventory = self._inventory(screening_id)
        layout = inventory.screening.room.layout
        return [
            layout.seat(seat_id)
            for seat_id, status in inventory.seat_map().items()
            if status is SeatStatus.AVAILABLE
        ]

    def quote(self, screening_id: str, seat_ids: Iterable[str]) -> dict[str, Decimal]:
        screening = self._inventory(screening_id).screening
        layout = screening.room.layout
        return {s: self._pricing.price(screening, layout.seat(s)) for s in seat_ids}

    # -- booking flow: hold -> pay -> confirm --------------------------------
    def hold_seats(self, screening_id: str, customer_id: str, seat_ids: Iterable[str]) -> SeatHold:
        hold = self._inventory(screening_id).hold(seat_ids, customer_id)
        with self._registry_lock:
            self._screening_of_hold[hold.hold_id] = screening_id
        return hold

    def release_hold(self, hold_id: str) -> None:
        inventory = self._inventory_for_hold(hold_id)
        inventory.release(hold_id)

    def checkout(self, hold_id: str, customer_id: str) -> Booking:
        """Charge the customer for a live hold, then make the seats permanent."""
        inventory = self._inventory_for_hold(hold_id)
        hold = inventory.get_hold(hold_id)
        if hold.customer_id != customer_id:
            raise InvalidStateError("this hold belongs to another customer")

        screening = inventory.screening
        booking_id = f"B{next(self._booking_ids)}"
        tickets = tuple(
            Ticket(
                ticket_id=f"{booking_id}-{seat_id}",
                booking_id=booking_id,
                screening_id=screening.screening_id,
                seat_id=seat_id,
                price=self._pricing.price(screening, screening.room.layout.seat(seat_id)),
            )
            for seat_id in sorted(hold.seat_ids)
        )
        booking = Booking(booking_id, customer_id, screening, tickets, self._clock())
        with self._registry_lock:
            self._bookings[booking_id] = booking

        # Phase 1: take the money. No lock is held during this slow call.
        try:
            receipt = self._payments.charge(customer_id, booking.total, idempotency_key=hold_id)
        except PaymentDeclinedError:
            booking.transition(BookingStatus.FAILED)
            inventory.release(hold_id)
            raise

        # Phase 2: commit the seats. If the hold ran out meanwhile, undo phase 1.
        try:
            inventory.confirm(hold_id, booking_id)
        except HoldExpiredError:
            self._payments.refund(receipt.payment_id, receipt.amount)
            booking.transition(BookingStatus.FAILED)
            raise

        booking.payment_id = receipt.payment_id
        booking.transition(BookingStatus.CONFIRMED)
        return booking

    def cancel_booking(self, booking_id: str, customer_id: str) -> Decimal:
        """Cancel a confirmed booking, free its seats, refund per policy."""
        booking = self.booking(booking_id)
        if booking.customer_id != customer_id:
            raise InvalidStateError("this booking belongs to another customer")
        now = self._clock()
        if now >= booking.screening.start:
            raise InvalidStateError("the show has already started")
        booking.transition(BookingStatus.CANCELLED)  # raises unless CONFIRMED
        refund = self._refund_policy.refund_amount(booking, now)
        if refund > 0 and booking.payment_id is not None:
            self._payments.refund(booking.payment_id, refund)
        booking.refunded = refund
        self._inventory(booking.screening.screening_id).free(booking.seat_ids, booking_id)
        return refund

    def booking(self, booking_id: str) -> Booking:
        with self._registry_lock:
            return self._lookup(self._bookings, booking_id, "booking")

    # -- internals --------------------------------------------------------
    def _inventory(self, screening_id: str) -> SeatInventory:
        with self._registry_lock:
            return self._lookup(self._inventories, screening_id, "screening")

    def _inventory_for_hold(self, hold_id: str) -> SeatInventory:
        with self._registry_lock:
            screening_id = self._lookup(self._screening_of_hold, hold_id, "hold")
            return self._inventories[screening_id]

    @staticmethod
    def _lookup[T](table: dict[str, T], key: str, kind: str) -> T:
        try:
            return table[key]
        except KeyError:
            raise NotFoundError(f"unknown {kind} {key!r}") from None


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------
class ManualClock:
    """A clock you move by hand, so demos and tests can fast-forward time."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


def demo() -> None:
    clock = ManualClock(datetime(2026, 11, 6, 9, 0))  # a Friday morning
    pricing = RuleBasedPricing(
        base_prices={
            SeatType.STANDARD: Decimal("12.00"),
            SeatType.ACCESSIBLE: Decimal("12.00"),
            SeatType.PREMIUM: Decimal("16.00"),
            SeatType.VIP: Decimal("24.00"),
        },
        rules=[
            MatineeDiscount(),
            WeekendSurcharge(),
            FormatSurcharge({"IMAX": Decimal("5.00")}),
        ],
    )
    payments = FakePaymentGateway(declined_customers={"mallory"})
    service = BookingService(pricing, payments, clock=clock, hold_ttl=timedelta(minutes=8))

    cinema = Cinema("c1", "Riverside 8", "Boston")
    cinema.add_room(Room("r1", "IMAX", SeatLayout.grid("ABCD", 6, {"D": SeatType.VIP})))
    service.add_cinema(cinema)
    service.add_movie(Movie("m1", "Orbit", timedelta(minutes=130), "Sci-fi", "PG-13"))
    service.schedule_screening("s1", "m1", "c1", "r1", datetime(2026, 11, 7, 19, 30), "IMAX")
    service.schedule_screening("s2", "m1", "c1", "r1", datetime(2026, 11, 7, 13, 0), "IMAX")
    try:
        service.schedule_screening("s3", "m1", "c1", "r1", datetime(2026, 11, 7, 15, 0))
    except SchedulingConflictError as err:
        print(f"Scheduling rejected: {err}")

    print("\nSaturday showtimes in Boston:")
    for s in service.search_showtimes(city="boston", on=date(2026, 11, 7)):
        print(f"  {s.screening_id} {s.movie.title} {s.format} at {s.start:%H:%M}")

    print("\nQuote for s1:", {k: str(v) for k, v in service.quote("s1", ["A1", "D3"]).items()})

    hold = service.hold_seats("s1", "alice", ["D3", "D4"])
    print(f"\nalice holds {sorted(hold.seat_ids)} until {hold.expires_at:%H:%M}")
    try:
        service.hold_seats("s1", "bob", ["D4", "D5"])
    except SeatUnavailableError as err:
        print(f"bob is refused: {err}")

    booking = service.checkout(hold.hold_id, "alice")
    print(f"alice paid {booking.total} -> {booking.booking_id} {booking.status.value}")

    slow = service.hold_seats("s1", "carol", ["B1"])
    clock.advance(timedelta(minutes=9))
    print(f"\ncarol waited too long; B1 is now {service.seat_map('s1')['B1'].value}")
    try:
        service.checkout(slow.hold_id, "carol")
    except HoldExpiredError as err:
        print(f"carol's checkout fails: {err}")

    bad = service.hold_seats("s1", "mallory", ["C1"])
    try:
        service.checkout(bad.hold_id, "mallory")
    except PaymentDeclinedError as err:
        print(f"mallory: {err}; C1 is {service.seat_map('s1')['C1'].value} again")

    refund = service.cancel_booking(booking.booking_id, "alice")
    print(f"\nalice cancels and gets {refund} back; D3 is {service.seat_map('s1')['D3'].value}")
    print(f"Seats left for s1: {len(service.available_seats('s1'))} of 24")


if __name__ == "__main__":
    demo()
