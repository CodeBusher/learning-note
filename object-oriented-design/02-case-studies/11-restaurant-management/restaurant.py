"""Restaurant management system: reservations, seating, orders, kitchen routing and billing.

This is the recommended design from the "Design a Restaurant Management System"
case study. Run ``python3 restaurant.py`` to see a short dinner-service scenario.
"""

from __future__ import annotations

import itertools
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Protocol

CENT = Decimal("0.01")


def to_money(value: Decimal | int | str) -> Decimal:
    """Round a value to whole cents using the rounding rule most tills use."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- errors


class RestaurantError(Exception):
    """Base class for every domain error raised by this module."""


class NoTableAvailable(RestaurantError):
    """No table (or table combination) can seat the party for the requested slot."""


class ReservationNotFound(RestaurantError):
    """The reservation id or party name does not match a live booking."""


class InvalidTransition(RestaurantError):
    """A lifecycle change that the state machine does not allow."""


class MenuError(RestaurantError):
    """Unknown, duplicate or unavailable menu item or modifier."""


class BillingError(RestaurantError):
    """A bill cannot be produced or split as requested."""


# --------------------------------------------------------------------------- menu


class Category(Enum):
    APPETIZER = "appetizer"
    MAIN = "main"
    DESSERT = "dessert"
    DRINK = "drink"


class Station(Enum):
    """Kitchen stations a ticket can be routed to."""

    GRILL = "grill"
    FRY = "fry"
    COLD = "cold"
    PASTRY = "pastry"
    BAR = "bar"


@dataclass(frozen=True)
class Modifier:
    """An option a guest can attach to a dish, e.g. "no onion" or "add bacon"."""

    name: str
    price_delta: Decimal = Decimal("0")


@dataclass(frozen=True)
class MenuItem:
    """An immutable menu entry. Orders reference it; they never change it."""

    item_id: str
    name: str
    price: Decimal
    category: Category
    station: Station
    modifiers: tuple[Modifier, ...] = ()

    def modifier(self, name: str) -> Modifier:
        for option in self.modifiers:
            if option.name == name:
                return option
        raise MenuError(f"{self.name!r} has no modifier {name!r}")


class Menu:
    """The catalog of dishes, plus which ones the kitchen has run out of ("86'd")."""

    def __init__(self, items: Iterable[MenuItem] = ()) -> None:
        self._items: dict[str, MenuItem] = {}
        self._eighty_sixed: set[str] = set()
        for item in items:
            self.add(item)

    def add(self, item: MenuItem) -> None:
        if item.item_id in self._items:
            raise MenuError(f"duplicate menu item id {item.item_id!r}")
        self._items[item.item_id] = item

    def get(self, item_id: str) -> MenuItem:
        try:
            return self._items[item_id]
        except KeyError:
            raise MenuError(f"unknown menu item {item_id!r}") from None

    def eighty_six(self, item_id: str) -> None:
        self.get(item_id)
        self._eighty_sixed.add(item_id)

    def restock(self, item_id: str) -> None:
        self._eighty_sixed.discard(item_id)

    def is_available(self, item_id: str) -> bool:
        return item_id in self._items and item_id not in self._eighty_sixed

    def available_items(self) -> list[MenuItem]:
        return [i for i in self._items.values() if i.item_id not in self._eighty_sixed]


# --------------------------------------------------------------------------- tables & time


@dataclass(frozen=True)
class Table:
    """A physical table. Zone lets a combining strategy only push together neighbours."""

    table_id: int
    capacity: int
    zone: str = "main"


@dataclass(frozen=True)
class TimeSlot:
    """A half-open interval [start, end): a 19:00-20:30 slot does not clash with 20:30-22:00."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("a time slot must end after it starts")

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end


def default_turn_time(party_size: int) -> timedelta:
    """How long a party is expected to occupy a table. Bigger groups linger longer."""
    if party_size <= 2:
        return timedelta(minutes=75)
    if party_size <= 4:
        return timedelta(minutes=90)
    return timedelta(minutes=120)


# --------------------------------------------------------------------------- reservations


class ReservationStatus(Enum):
    BOOKED = "booked"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


RESERVATION_TRANSITIONS: dict[ReservationStatus, frozenset[ReservationStatus]] = {
    ReservationStatus.BOOKED: frozenset(
        {ReservationStatus.SEATED, ReservationStatus.CANCELLED, ReservationStatus.NO_SHOW}
    ),
    ReservationStatus.SEATED: frozenset({ReservationStatus.COMPLETED}),
    ReservationStatus.COMPLETED: frozenset(),
    ReservationStatus.CANCELLED: frozenset(),
    ReservationStatus.NO_SHOW: frozenset(),
}


@dataclass(eq=False)
class Reservation:
    """A claim on one or more tables for a time slot. Walk-ins are reservations that start seated."""

    reservation_id: int
    party_name: str
    party_size: int
    slot: TimeSlot
    tables: tuple[Table, ...]
    walk_in: bool = False
    status: ReservationStatus = ReservationStatus.BOOKED

    @property
    def holds_tables(self) -> bool:
        return self.status in (ReservationStatus.BOOKED, ReservationStatus.SEATED)

    @property
    def table_label(self) -> str:
        return "+".join(str(t.table_id) for t in self.tables)

    def move_to(self, target: ReservationStatus) -> None:
        if target not in RESERVATION_TRANSITIONS[self.status]:
            raise InvalidTransition(
                f"reservation {self.reservation_id}: {self.status.value} -> {target.value}"
            )
        self.status = target


class TableAssignmentStrategy(Protocol):
    """Picks tables for a party from the tables that are free for the whole slot."""

    def choose(
        self, party_size: int, free_tables: Sequence[Table]
    ) -> tuple[Table, ...] | None: ...


class BestFitAssignment:
    """Smallest single table that fits, so a couple never ties up an eight-top."""

    def choose(
        self, party_size: int, free_tables: Sequence[Table]
    ) -> tuple[Table, ...] | None:
        candidates = [t for t in free_tables if t.capacity >= party_size]
        if not candidates:
            return None
        return (min(candidates, key=lambda t: (t.capacity, t.table_id)),)


class ReservationBook:
    """Owns every reservation and answers "is this table free for this slot?".

    The check-then-book sequence runs under one lock so two hosts cannot both
    grab the last table for the same slot.
    """

    def __init__(
        self,
        tables: Iterable[Table],
        strategy: TableAssignmentStrategy | None = None,
        turn_time: Callable[[int], timedelta] = default_turn_time,
    ) -> None:
        self._tables = sorted(tables, key=lambda t: t.table_id)
        if len({t.table_id for t in self._tables}) != len(self._tables):
            raise ValueError("table ids must be unique")
        self._strategy = strategy or BestFitAssignment()
        self._turn_time = turn_time
        self._by_table: dict[int, list[Reservation]] = {t.table_id: [] for t in self._tables}
        self._by_id: dict[int, Reservation] = {}
        self._ids = itertools.count(1)
        self._lock = threading.RLock()

    def slot_for(self, party_size: int, start: datetime) -> TimeSlot:
        return TimeSlot(start, start + self._turn_time(party_size))

    def _is_free(self, table: Table, slot: TimeSlot) -> bool:
        return not any(
            r.holds_tables and r.slot.overlaps(slot) for r in self._by_table[table.table_id]
        )

    def free_tables(self, slot: TimeSlot) -> list[Table]:
        with self._lock:
            return [t for t in self._tables if self._is_free(t, slot)]

    def available_starts(
        self,
        party_size: int,
        window_start: datetime,
        window_end: datetime,
        step: timedelta = timedelta(minutes=15),
    ) -> list[datetime]:
        _check_party_size(party_size)
        starts: list[datetime] = []
        with self._lock:
            start = window_start
            while start <= window_end:
                slot = self.slot_for(party_size, start)
                if self._strategy.choose(party_size, self.free_tables(slot)) is not None:
                    starts.append(start)
                start += step
        return starts

    def book(
        self, party_name: str, party_size: int, start: datetime, *, walk_in: bool = False
    ) -> Reservation:
        _check_party_size(party_size)
        slot = self.slot_for(party_size, start)
        with self._lock:
            tables = self._strategy.choose(party_size, self.free_tables(slot))
            if tables is None:
                raise NoTableAvailable(
                    f"no table for {party_size} at {start:%Y-%m-%d %H:%M}"
                )
            reservation = Reservation(
                reservation_id=next(self._ids),
                party_name=party_name,
                party_size=party_size,
                slot=slot,
                tables=tables,
                walk_in=walk_in,
                status=ReservationStatus.SEATED if walk_in else ReservationStatus.BOOKED,
            )
            for table in tables:
                self._by_table[table.table_id].append(reservation)
            self._by_id[reservation.reservation_id] = reservation
            return reservation

    def get(self, reservation_id: int) -> Reservation:
        try:
            return self._by_id[reservation_id]
        except KeyError:
            raise ReservationNotFound(f"no reservation {reservation_id}") from None

    def find_booked(self, party_name: str, day: date) -> list[Reservation]:
        wanted = party_name.strip().casefold()
        with self._lock:
            return sorted(
                (
                    r
                    for r in self._by_id.values()
                    if r.status is ReservationStatus.BOOKED
                    and r.party_name.casefold() == wanted
                    and r.slot.start.date() == day
                ),
                key=lambda r: r.slot.start,
            )

    def check_in(self, party_name: str, now: datetime) -> Reservation:
        """Seat the booking under this name whose start time is closest to now."""
        with self._lock:
            matches = self.find_booked(party_name, now.date())
            if not matches:
                raise ReservationNotFound(f"no booking today for {party_name!r}")
            reservation = min(matches, key=lambda r: abs(r.slot.start - now))
            reservation.move_to(ReservationStatus.SEATED)
            return reservation

    def cancel(self, reservation_id: int) -> Reservation:
        return self._move(reservation_id, ReservationStatus.CANCELLED)

    def mark_no_show(self, reservation_id: int) -> Reservation:
        return self._move(reservation_id, ReservationStatus.NO_SHOW)

    def complete(self, reservation_id: int) -> Reservation:
        return self._move(reservation_id, ReservationStatus.COMPLETED)

    def _move(self, reservation_id: int, target: ReservationStatus) -> Reservation:
        with self._lock:
            reservation = self.get(reservation_id)
            reservation.move_to(target)
            return reservation


def _check_party_size(party_size: int) -> None:
    if party_size < 1:
        raise ValueError("party size must be at least 1")


# --------------------------------------------------------------------------- orders


class LineStatus(Enum):
    PENDING = "pending"  # entered on the POS, not yet sent to the kitchen
    FIRED = "fired"  # on a kitchen ticket, being cooked
    READY = "ready"  # station bumped it; waiting at the pass
    SERVED = "served"
    VOIDED = "voided"


LINE_TRANSITIONS: dict[LineStatus, frozenset[LineStatus]] = {
    LineStatus.PENDING: frozenset({LineStatus.FIRED, LineStatus.VOIDED}),
    LineStatus.FIRED: frozenset({LineStatus.READY, LineStatus.VOIDED}),
    LineStatus.READY: frozenset({LineStatus.SERVED}),
    LineStatus.SERVED: frozenset(),
    LineStatus.VOIDED: frozenset(),
}


@dataclass(eq=False)
class OrderLine:
    """One line on a check: a menu item, its chosen modifiers, a quantity and a status."""

    line_id: int
    item: MenuItem
    quantity: int = 1
    modifiers: tuple[Modifier, ...] = ()
    seat: int | None = None
    note: str = ""
    status: LineStatus = LineStatus.PENDING

    @property
    def unit_price(self) -> Decimal:
        return self.item.price + sum((m.price_delta for m in self.modifiers), Decimal("0"))

    @property
    def total(self) -> Decimal:
        if self.status is LineStatus.VOIDED:
            return Decimal("0")
        return self.unit_price * self.quantity

    def advance(self, target: LineStatus) -> None:
        if target not in LINE_TRANSITIONS[self.status]:
            raise InvalidTransition(
                f"line {self.line_id} ({self.item.name}): "
                f"{self.status.value} -> {target.value}"
            )
        self.status = target

    def describe(self) -> str:
        text = f"{self.quantity}x {self.item.name}"
        if self.modifiers:
            text += " (" + ", ".join(m.name for m in self.modifiers) + ")"
        if self.note:
            text += f" [{self.note}]"
        return text


class OrderSource(Enum):
    DINE_IN = "dine-in"
    TAKEOUT = "takeout"
    DELIVERY = "delivery"


class Order:
    """A check: the lines a party has ordered. Dine-in orders point at their reservation."""

    def __init__(
        self,
        order_id: int,
        label: str,
        source: OrderSource = OrderSource.DINE_IN,
        reservation: Reservation | None = None,
    ) -> None:
        self.order_id = order_id
        self.label = label
        self.source = source
        self.reservation = reservation
        self.closed = False
        self._lines: dict[int, OrderLine] = {}
        self._line_ids = itertools.count(1)
        self._lock = threading.Lock()

    @property
    def lines(self) -> list[OrderLine]:
        return list(self._lines.values())

    def line(self, line_id: int) -> OrderLine:
        try:
            return self._lines[line_id]
        except KeyError:
            raise RestaurantError(f"order {self.order_id} has no line {line_id}") from None

    def add(
        self,
        item: MenuItem,
        quantity: int = 1,
        modifier_names: Sequence[str] = (),
        seat: int | None = None,
        note: str = "",
    ) -> OrderLine:
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        modifiers = tuple(item.modifier(name) for name in modifier_names)
        with self._lock:
            self._ensure_open()
            line = OrderLine(next(self._line_ids), item, quantity, modifiers, seat, note)
            self._lines[line.line_id] = line
            return line

    def change_quantity(self, line_id: int, quantity: int) -> OrderLine:
        if quantity < 1:
            raise ValueError("quantity must be at least 1; void the line instead")
        with self._lock:
            self._ensure_open()
            line = self.line(line_id)
            if line.status is not LineStatus.PENDING:
                raise InvalidTransition("only unsent lines can change quantity; void and re-ring")
            line.quantity = quantity
            return line

    def void(self, line_id: int) -> tuple[OrderLine, LineStatus]:
        """Void a line and report the status it had, so the caller knows if the kitchen must hear."""
        with self._lock:
            self._ensure_open()
            line = self.line(line_id)
            previous = line.status
            line.advance(LineStatus.VOIDED)
            return line, previous

    def take_pending(self) -> list[OrderLine]:
        """Mark every unsent line as fired and return them, atomically."""
        with self._lock:
            self._ensure_open()
            pending = [l for l in self._lines.values() if l.status is LineStatus.PENDING]
            for line in pending:
                line.advance(LineStatus.FIRED)
            return pending

    @property
    def subtotal(self) -> Decimal:
        return sum((line.total for line in self._lines.values()), Decimal("0"))

    def close(self) -> None:
        with self._lock:
            self._ensure_open()
            unfinished = [
                l
                for l in self._lines.values()
                if l.status not in (LineStatus.SERVED, LineStatus.VOIDED)
            ]
            if unfinished:
                names = ", ".join(l.item.name for l in unfinished)
                raise BillingError(f"cannot close order {self.order_id}; still open: {names}")
            self.closed = True

    def _ensure_open(self) -> None:
        if self.closed:
            raise RestaurantError(f"order {self.order_id} is closed")


# --------------------------------------------------------------------------- kitchen


@dataclass(eq=False)
class KitchenTicket:
    """What one station sees for one fire: the lines it must cook for one order."""

    ticket_id: int
    order_id: int
    label: str
    station: Station
    lines: tuple[OrderLine, ...]
    fired_at: datetime


@dataclass(frozen=True)
class TicketFired:
    ticket: KitchenTicket


@dataclass(frozen=True)
class ItemVoided:
    order_id: int
    line: OrderLine
    station: Station


type KitchenEvent = TicketFired | ItemVoided


class KitchenSubscriber(Protocol):
    def notify(self, event: KitchenEvent) -> None: ...


class KitchenRouter:
    """Publish/subscribe hub. Front of house publishes; each station's screen subscribes."""

    def __init__(self) -> None:
        self._subscribers: dict[Station | None, list[KitchenSubscriber]] = defaultdict(list)

    def subscribe(self, subscriber: KitchenSubscriber, station: Station | None = None) -> None:
        """Subscribe to one station, or pass None to see every station (the expo screen)."""
        self._subscribers[station].append(subscriber)

    def publish(self, event: KitchenEvent) -> None:
        station = event.ticket.station if isinstance(event, TicketFired) else event.station
        for subscriber in [*self._subscribers[station], *self._subscribers[None]]:
            subscriber.notify(event)


class KitchenDisplay:
    """A kitchen display screen (KDS): shows open tickets, the cook "bumps" them when done."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._open: dict[int, KitchenTicket] = {}
        self.messages: list[str] = []

    def notify(self, event: KitchenEvent) -> None:
        match event:
            case TicketFired(ticket=ticket):
                self._open[ticket.ticket_id] = ticket
                self.messages.append(
                    f"NEW #{ticket.ticket_id} {ticket.label}: "
                    + "; ".join(l.describe() for l in ticket.lines)
                )
            case ItemVoided(line=line):
                self.messages.append(f"VOID {line.describe()}")
                for ticket_id, ticket in list(self._open.items()):
                    if all(l.status is LineStatus.VOIDED for l in ticket.lines):
                        del self._open[ticket_id]

    def open_tickets(self) -> list[KitchenTicket]:
        return list(self._open.values())

    def bump(self, ticket_id: int) -> KitchenTicket:
        try:
            ticket = self._open.pop(ticket_id)
        except KeyError:
            raise RestaurantError(f"{self.name} has no open ticket {ticket_id}") from None
        for line in ticket.lines:
            if line.status is LineStatus.FIRED:
                line.advance(LineStatus.READY)
        return ticket


# --------------------------------------------------------------------------- billing


@dataclass(frozen=True)
class Bill:
    """A snapshot of what an order owes. Splitting never changes the total."""

    order_id: int
    lines: tuple[OrderLine, ...]
    subtotal: Decimal
    tax: Decimal
    service_charge: Decimal

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax + self.service_charge

    @classmethod
    def for_order(
        cls, order: Order, tax_rate: Decimal, service_rate: Decimal = Decimal("0")
    ) -> Bill:
        billable = tuple(l for l in order.lines if l.status is not LineStatus.VOIDED)
        subtotal = to_money(sum((l.total for l in billable), Decimal("0")))
        return cls(
            order_id=order.order_id,
            lines=billable,
            subtotal=subtotal,
            tax=to_money(subtotal * tax_rate),
            service_charge=to_money(subtotal * service_rate),
        )

    def split(self, strategy: SplitStrategy) -> dict[str, Decimal]:
        shares = strategy.split(self)
        if sum(shares.values()) != self.total:
            raise BillingError("split strategy changed the bill total")
        return shares

    def render(self) -> str:
        rows = [f"  {l.describe():<40}{l.total:>8}" for l in self.lines]
        rows.append(f"  {'Subtotal':<40}{self.subtotal:>8}")
        rows.append(f"  {'Tax':<40}{self.tax:>8}")
        if self.service_charge:
            rows.append(f"  {'Service charge':<40}{self.service_charge:>8}")
        rows.append(f"  {'TOTAL':<40}{self.total:>8}")
        return "\n".join(rows)


def allocate(total: Decimal, weights: Mapping[str, Decimal]) -> dict[str, Decimal]:
    """Split `total` into whole cents in proportion to `weights`.

    Uses the largest-remainder method so the shares always add up to the
    total exactly; naive rounding of each share can gain or lose a cent.
    """
    if not weights:
        raise BillingError("nobody to split the bill between")
    weight_sum = sum(weights.values(), Decimal("0"))
    if weight_sum <= 0 or any(w < 0 for w in weights.values()):
        raise BillingError("split weights must be non-negative and not all zero")
    cents = int(to_money(total) / CENT)
    exact = {name: cents * w / weight_sum for name, w in weights.items()}
    shares = {name: int(value) for name, value in exact.items()}
    leftover = cents - sum(shares.values())
    by_remainder = sorted(weights, key=lambda n: exact[n] - shares[n], reverse=True)
    for name in by_remainder[:leftover]:
        shares[name] += 1
    return {name: Decimal(c) * CENT for name, c in shares.items()}


class SplitStrategy(ABC):
    """A rule for dividing one bill between several payers."""

    @abstractmethod
    def split(self, bill: Bill) -> dict[str, Decimal]: ...


class EqualSplit(SplitStrategy):
    def __init__(self, payers: Sequence[str]) -> None:
        if not payers:
            raise BillingError("need at least one payer")
        self.payers = list(payers)

    def split(self, bill: Bill) -> dict[str, Decimal]:
        return allocate(bill.total, {p: Decimal(1) for p in self.payers})


class ByItemSplit(SplitStrategy):
    """Each payer pays for what they ate; shared lines are divided among the sharers.

    Tax and service charge are spread in proportion to each payer's food total.
    """

    def __init__(self, assignments: Mapping[int, Sequence[str]]) -> None:
        self.assignments = {line_id: list(p) for line_id, p in assignments.items()}

    def split(self, bill: Bill) -> dict[str, Decimal]:
        weights: dict[str, Decimal] = {}
        for line in bill.lines:
            payers = self.assignments.get(line.line_id)
            if not payers:
                raise BillingError(f"line {line.line_id} ({line.item.name}) is not assigned")
            for payer in payers:
                weights[payer] = weights.get(payer, Decimal("0")) + line.total / len(payers)
        unknown = set(self.assignments) - {l.line_id for l in bill.lines}
        if unknown:
            raise BillingError(f"assigned lines not on the bill: {sorted(unknown)}")
        return allocate(bill.total, weights)


class CustomSplit(SplitStrategy):
    """Payers name their own amounts ("put $50 on mine, the rest on hers")."""

    def __init__(self, amounts: Mapping[str, Decimal]) -> None:
        self.amounts = {p: to_money(a) for p, a in amounts.items()}

    def split(self, bill: Bill) -> dict[str, Decimal]:
        if any(a < 0 for a in self.amounts.values()):
            raise BillingError("amounts cannot be negative")
        if sum(self.amounts.values()) != bill.total:
            raise BillingError(
                f"custom amounts add to {sum(self.amounts.values())}, bill is {bill.total}"
            )
        return dict(self.amounts)


# --------------------------------------------------------------------------- facade


class Restaurant:
    """Facade the host stand, servers' handhelds and the kitchen talk to."""

    def __init__(
        self,
        name: str,
        menu: Menu,
        tables: Iterable[Table],
        *,
        tax_rate: Decimal = Decimal("0.08"),
        assignment: TableAssignmentStrategy | None = None,
        turn_time: Callable[[int], timedelta] = default_turn_time,
        clock: Callable[[], datetime] = datetime.now,
        large_party_size: int = 6,
        large_party_service_rate: Decimal = Decimal("0.18"),
    ) -> None:
        self.name = name
        self.menu = menu
        self.reservations = ReservationBook(tables, assignment, turn_time)
        self.kitchen = KitchenRouter()
        self.tax_rate = tax_rate
        self.large_party_size = large_party_size
        self.large_party_service_rate = large_party_service_rate
        self._clock = clock
        self._orders: dict[int, Order] = {}
        self._order_ids = itertools.count(1)
        self._ticket_ids = itertools.count(1)
        self._lock = threading.Lock()

    # ---- reservations and seating
    def available_times(
        self, party_size: int, window_start: datetime, window_end: datetime
    ) -> list[datetime]:
        return self.reservations.available_starts(party_size, window_start, window_end)

    def book(self, party_name: str, party_size: int, start: datetime) -> Reservation:
        if start < self._clock():
            raise ValueError("cannot book a time in the past")
        return self.reservations.book(party_name, party_size, start)

    def cancel_reservation(self, reservation_id: int) -> Reservation:
        return self.reservations.cancel(reservation_id)

    def check_in(self, party_name: str) -> Order:
        reservation = self.reservations.check_in(party_name, self._clock())
        return self._open_order(f"Table {reservation.table_label}", reservation=reservation)

    def seat_walk_in(self, party_name: str, party_size: int) -> Order:
        reservation = self.reservations.book(
            party_name, party_size, self._clock(), walk_in=True
        )
        return self._open_order(f"Table {reservation.table_label}", reservation=reservation)

    # ---- orders
    def open_off_premise(self, customer: str, source: OrderSource) -> Order:
        if source is OrderSource.DINE_IN:
            raise ValueError("dine-in orders start from check_in or seat_walk_in")
        return self._open_order(f"{source.value.title()}: {customer}", source=source)

    def order(self, order_id: int) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise RestaurantError(f"no order {order_id}") from None

    def add_item(
        self,
        order_id: int,
        item_id: str,
        quantity: int = 1,
        modifiers: Sequence[str] = (),
        seat: int | None = None,
        note: str = "",
    ) -> OrderLine:
        if not self.menu.is_available(item_id):
            raise MenuError(f"{item_id!r} is not available")
        return self.order(order_id).add(self.menu.get(item_id), quantity, modifiers, seat, note)

    def change_quantity(self, order_id: int, line_id: int, quantity: int) -> OrderLine:
        return self.order(order_id).change_quantity(line_id, quantity)

    def void_item(self, order_id: int, line_id: int) -> OrderLine:
        line, previous = self.order(order_id).void(line_id)
        if previous is LineStatus.FIRED:
            self.kitchen.publish(ItemVoided(order_id, line, line.item.station))
        return line

    def fire(self, order_id: int) -> list[KitchenTicket]:
        """Send every unsent line to the kitchen, one ticket per station."""
        order = self.order(order_id)
        by_station: dict[Station, list[OrderLine]] = defaultdict(list)
        for line in order.take_pending():
            by_station[line.item.station].append(line)
        tickets = []
        for station, lines in by_station.items():
            with self._lock:
                ticket_id = next(self._ticket_ids)
            ticket = KitchenTicket(
                ticket_id, order_id, order.label, station, tuple(lines), self._clock()
            )
            self.kitchen.publish(TicketFired(ticket))
            tickets.append(ticket)
        return tickets

    def serve(self, order_id: int, line_id: int) -> OrderLine:
        line = self.order(order_id).line(line_id)
        line.advance(LineStatus.SERVED)
        return line

    # ---- billing
    def bill(self, order_id: int) -> Bill:
        order = self.order(order_id)
        party = order.reservation.party_size if order.reservation else 1
        service = (
            self.large_party_service_rate if party >= self.large_party_size else Decimal("0")
        )
        return Bill.for_order(order, self.tax_rate, service)

    def close_check(self, order_id: int) -> Bill:
        order = self.order(order_id)
        order.close()
        if order.reservation is not None:
            self.reservations.complete(order.reservation.reservation_id)
        return self.bill(order_id)

    def _open_order(
        self,
        label: str,
        source: OrderSource = OrderSource.DINE_IN,
        reservation: Reservation | None = None,
    ) -> Order:
        with self._lock:
            order = Order(next(self._order_ids), label, source, reservation)
            self._orders[order.order_id] = order
            return order


# --------------------------------------------------------------------------- demo


def sample_menu() -> Menu:
    return Menu(
        [
            MenuItem("wings", "Chicken Wings", Decimal("12.00"), Category.APPETIZER, Station.FRY),
            MenuItem(
                "burger",
                "Smash Burger",
                Decimal("16.50"),
                Category.MAIN,
                Station.GRILL,
                (Modifier("no onion"), Modifier("add bacon", Decimal("2.50"))),
            ),
            MenuItem("salmon", "Grilled Salmon", Decimal("24.00"), Category.MAIN, Station.GRILL),
            MenuItem("salad", "Caesar Salad", Decimal("11.00"), Category.APPETIZER, Station.COLD),
            MenuItem("cake", "Chocolate Cake", Decimal("9.00"), Category.DESSERT, Station.PASTRY),
            MenuItem("lemonade", "Lemonade", Decimal("4.00"), Category.DRINK, Station.BAR),
        ]
    )


def sample_tables() -> list[Table]:
    return [
        Table(1, 2, "window"),
        Table(2, 2, "window"),
        Table(3, 4, "main"),
        Table(4, 4, "main"),
        Table(5, 6, "main"),
        Table(6, 8, "patio"),
    ]


class ManualClock:
    """A clock you set by hand, so demos and tests are deterministic."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def demo() -> None:
    clock = ManualClock(datetime(2026, 11, 6, 17, 0))
    restaurant = Restaurant("Bistro 11", sample_menu(), sample_tables(), clock=clock)
    screens = {station: KitchenDisplay(station.value) for station in Station}
    for station, screen in screens.items():
        restaurant.kitchen.subscribe(screen, station)
    expo = KitchenDisplay("expo")
    restaurant.kitchen.subscribe(expo)  # expo sees every station

    print(f"== {restaurant.name}: Friday dinner ==")
    seven = datetime(2026, 11, 6, 19, 0)
    times = restaurant.available_times(4, seven, seven + timedelta(hours=1))
    print("Start times for 4 between 19:00 and 20:00:", [t.strftime("%H:%M") for t in times])
    booking = restaurant.book("Garcia", 4, seven)
    print(
        f"Booked Garcia x4 -> table {booking.table_label}, "
        f"{booking.slot.start:%H:%M}-{booking.slot.end:%H:%M}"
    )

    clock.now = datetime(2026, 11, 6, 19, 5)
    order = restaurant.check_in("garcia")
    print(f"Garcia checked in -> order #{order.order_id} at {order.label}")
    burger = restaurant.add_item(order.order_id, "burger", 2, ["add bacon"], seat=1)
    restaurant.add_item(order.order_id, "salad", seat=2)
    salmon = restaurant.add_item(order.order_id, "salmon", seat=3)
    restaurant.add_item(order.order_id, "lemonade", 3)
    tickets = restaurant.fire(order.order_id)
    print("Fired tickets to:", ", ".join(t.station.value for t in tickets))
    print("Grill screen:", screens[Station.GRILL].messages)

    restaurant.void_item(order.order_id, salmon.line_id)
    print("Grill screen after void:", screens[Station.GRILL].messages[-1])

    for screen in screens.values():  # each station bumps its tickets when cooked
        for ticket in screen.open_tickets():
            screen.bump(ticket.ticket_id)
    for line in order.lines:
        if line.status is LineStatus.READY:
            restaurant.serve(order.order_id, line.line_id)
    print("Burger line is now:", burger.status.value)
    print("Expo saw", len(expo.messages), "kitchen events")

    bill = restaurant.close_check(order.order_id)
    print("Bill:\n" + bill.render())
    shares = bill.split(EqualSplit(["Ana", "Ben", "Cy"]))
    print("Split three ways:", {name: str(amount) for name, amount in shares.items()})

    walk_in = restaurant.seat_walk_in("Lee", 2)
    print(f"Walk-in Lee x2 seated at {walk_in.label}")


if __name__ == "__main__":
    demo()
