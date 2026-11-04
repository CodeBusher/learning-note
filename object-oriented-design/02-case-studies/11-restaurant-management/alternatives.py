"""Competing designs for the restaurant case study, so they can be run and compared.

Each section matches a "Comparing approaches" decision point in README.md.
Run ``python3 alternatives.py`` for a side-by-side demo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import combinations

from restaurant import (
    BestFitAssignment,
    BillingError,
    InvalidTransition,
    MenuError,
    MenuItem,
    Table,
    TimeSlot,
    allocate,
    sample_menu,
    sample_tables,
    to_money,
)

# =========================================================================
# Decision 1a: which table(s) does a party get?
# =========================================================================


class FirstFitAssignment:
    """First free table (by id) that is big enough. Simple, but wastes big tables."""

    def choose(
        self, party_size: int, free_tables: Sequence[Table]
    ) -> tuple[Table, ...] | None:
        for table in sorted(free_tables, key=lambda t: t.table_id):
            if table.capacity >= party_size:
                return (table,)
        return None


class CombineTablesAssignment:
    """Best single table if one fits; otherwise push together tables in one zone.

    Among combinations it prefers fewest tables, then fewest empty seats.
    Brute force is fine: a zone rarely has more than a dozen tables.
    """

    def __init__(self, max_tables: int = 3) -> None:
        self.max_tables = max_tables
        self._single = BestFitAssignment()

    def choose(
        self, party_size: int, free_tables: Sequence[Table]
    ) -> tuple[Table, ...] | None:
        single = self._single.choose(party_size, free_tables)
        if single is not None:
            return single
        zones: dict[str, list[Table]] = {}
        for table in free_tables:
            zones.setdefault(table.zone, []).append(table)
        best: tuple[Table, ...] | None = None
        for size in range(2, self.max_tables + 1):
            for tables in zones.values():
                for combo in combinations(sorted(tables, key=lambda t: t.table_id), size):
                    seats = sum(t.capacity for t in combo)
                    if seats >= party_size and (
                        best is None or seats < sum(t.capacity for t in best)
                    ):
                        best = combo
            if best is not None:
                return best
        return None


# =========================================================================
# Decision 1b: how do we know a table is free at a time?
# =========================================================================


class ExactStartTimeBook:
    """Availability keyed by exact start time (one fixed-length slot per key).

    Looks fine until two bookings start at different times but overlap:
    19:00 and 19:30 are different keys, so both "fit" on the same table.
    """

    def __init__(self) -> None:
        self._taken: dict[int, set[datetime]] = {}

    def is_free(self, table: Table, start: datetime) -> bool:
        return start not in self._taken.get(table.table_id, set())

    def book(self, table: Table, start: datetime) -> None:
        self._taken.setdefault(table.table_id, set()).add(start)


class IntervalBook:
    """Availability by interval overlap, as the recommended ReservationBook does."""

    def __init__(self, turn_time: timedelta) -> None:
        self.turn_time = turn_time
        self._taken: dict[int, list[TimeSlot]] = {}

    def is_free(self, table: Table, start: datetime) -> bool:
        wanted = TimeSlot(start, start + self.turn_time)
        return not any(wanted.overlaps(s) for s in self._taken.get(table.table_id, []))

    def book(self, table: Table, start: datetime) -> None:
        self._taken.setdefault(table.table_id, []).append(
            TimeSlot(start, start + self.turn_time)
        )


# =========================================================================
# Decision 2: how does an order reach the kitchen?
# =========================================================================


class DirectKitchen:
    """Option A: the order calls the kitchen object directly."""

    def __init__(self) -> None:
        self.queue: list[str] = []

    def cook(self, table: str, item: MenuItem) -> None:
        self.queue.append(f"{table}: {item.name}")


class DirectCallOrder:
    """Couples the order to one concrete kitchen. Adding a bar printer means editing this class."""

    def __init__(self, table: str, kitchen: DirectKitchen) -> None:
        self.table = table
        self.kitchen = kitchen

    def fire(self, item: MenuItem) -> None:
        self.kitchen.cook(self.table, item)


class KitchenCommand(ABC):
    """Option B: every kitchen request is an object that can be queued, logged and undone."""

    @abstractmethod
    def execute(self, board: dict[str, list[str]]) -> None: ...

    @abstractmethod
    def undo(self, board: dict[str, list[str]]) -> None: ...


@dataclass(frozen=True)
class FireItem(KitchenCommand):
    table: str
    item: MenuItem

    def execute(self, board: dict[str, list[str]]) -> None:
        board.setdefault(self.item.station.value, []).append(f"{self.table}: {self.item.name}")

    def undo(self, board: dict[str, list[str]]) -> None:
        board[self.item.station.value].remove(f"{self.table}: {self.item.name}")


@dataclass(frozen=True)
class RushTable(KitchenCommand):
    table: str

    def execute(self, board: dict[str, list[str]]) -> None:
        for tickets in board.values():
            # move this table's tickets to the front of every station queue
            tickets.sort(key=lambda t: not t.startswith(f"{self.table}:"))

    def undo(self, board: dict[str, list[str]]) -> None:
        pass  # re-ordering is not worth reversing


class CommandQueueKitchen:
    """Invoker: buffers commands (e.g. while the network is down) and keeps a history."""

    def __init__(self) -> None:
        self.board: dict[str, list[str]] = {}
        self._pending: deque[KitchenCommand] = deque()
        self.history: list[KitchenCommand] = []

    def submit(self, command: KitchenCommand) -> None:
        self._pending.append(command)

    def drain(self) -> int:
        count = 0
        while self._pending:
            command = self._pending.popleft()
            command.execute(self.board)
            self.history.append(command)
            count += 1
        return count

    def undo_last(self) -> KitchenCommand:
        command = self.history.pop()
        command.undo(self.board)
        return command


# Option C, the Observer / event bus, is the recommended KitchenRouter in restaurant.py.


# =========================================================================
# Decision 3: order-line lifecycle as the State pattern
# =========================================================================


class LineState(ABC):
    """One class per state. Each state decides which events it accepts."""

    name = "abstract"

    def fire(self, line: StatefulLine) -> None:
        self._reject("fire")

    def bump(self, line: StatefulLine) -> None:
        self._reject("bump")

    def serve(self, line: StatefulLine) -> None:
        self._reject("serve")

    def void(self, line: StatefulLine) -> None:
        self._reject("void")

    def _reject(self, event: str) -> None:
        raise InvalidTransition(f"cannot {event} a {self.name} line")


class PendingState(LineState):
    name = "pending"

    def fire(self, line: StatefulLine) -> None:
        line.state = FiredState()

    def void(self, line: StatefulLine) -> None:
        line.state = VoidedState()


class FiredState(LineState):
    name = "fired"

    def bump(self, line: StatefulLine) -> None:
        line.state = ReadyState()

    def void(self, line: StatefulLine) -> None:
        line.waste_logged = True  # food may already be on the grill
        line.state = VoidedState()


class ReadyState(LineState):
    name = "ready"

    def serve(self, line: StatefulLine) -> None:
        line.state = ServedState()


class ServedState(LineState):
    name = "served"


class VoidedState(LineState):
    name = "voided"


class StatefulLine:
    """Context object: forwards each event to its current state."""

    def __init__(self, item: MenuItem) -> None:
        self.item = item
        self.state: LineState = PendingState()
        self.waste_logged = False

    def fire(self) -> None:
        self.state.fire(self)

    def bump(self) -> None:
        self.state.bump(self)

    def serve(self) -> None:
        self.state.serve(self)

    def void(self) -> None:
        self.state.void(self)


# =========================================================================
# Decision 4: splitting the bill without a Strategy
# =========================================================================


def split_with_if_else(
    mode: str, total: Decimal, payers: Sequence[str], amounts: dict[str, Decimal] | None = None
) -> dict[str, Decimal]:
    """Every new split rule adds a branch here, and every branch must be retested."""
    if mode == "equal":
        return allocate(total, {p: Decimal(1) for p in payers})
    elif mode == "custom":
        if amounts is None or sum(amounts.values()) != total:
            raise BillingError("custom amounts must add up to the total")
        return dict(amounts)
    else:
        raise BillingError(f"unknown split mode {mode!r}")


def naive_equal_split(total: Decimal, payers: int) -> list[Decimal]:
    """Rounds each share independently, so the shares may not add up to the total."""
    return [to_money(total / payers)] * payers


# =========================================================================
# Decision 5: modifiers as Decorators instead of composition
# =========================================================================


class Dish(ABC):
    @abstractmethod
    def price(self) -> Decimal: ...

    @abstractmethod
    def description(self) -> str: ...


class BaseDish(Dish):
    def __init__(self, item: MenuItem) -> None:
        self.item = item

    def price(self) -> Decimal:
        return self.item.price

    def description(self) -> str:
        return self.item.name


class DishDecorator(Dish):
    def __init__(self, inner: Dish) -> None:
        self.inner = inner


class AddBacon(DishDecorator):
    def price(self) -> Decimal:
        return self.inner.price() + Decimal("2.50")

    def description(self) -> str:
        return self.inner.description() + ", add bacon"


class NoOnion(DishDecorator):
    def price(self) -> Decimal:
        return self.inner.price()

    def description(self) -> str:
        return self.inner.description() + ", no onion"


# =========================================================================
# Going deeper: adapting a third-party delivery payload
# =========================================================================


class DeliveryOrderAdapter:
    """Adapter: turns a marketplace's order payload into (item, quantity, modifiers) rows.

    Each delivery platform names things differently, so the restaurant keeps a
    mapping from the platform's item ids to its own menu ids.
    """

    def __init__(self, platform: str, item_map: dict[str, str]) -> None:
        self.platform = platform
        self.item_map = item_map

    def to_lines(self, payload: dict) -> list[tuple[str, int, list[str]]]:
        rows = []
        for entry in payload["items"]:
            try:
                item_id = self.item_map[entry["external_id"]]
            except KeyError:
                raise MenuError(
                    f"{self.platform} item {entry['external_id']!r} is not mapped"
                ) from None
            rows.append((item_id, int(entry.get("qty", 1)), list(entry.get("options", []))))
        return rows


# =========================================================================
# Demo
# =========================================================================


def demo() -> None:
    tables = sample_tables()
    patio = [Table(1, 8, "patio"), Table(2, 4, "patio"), Table(3, 2, "patio")]
    print("== A couple arrives; patio has an 8-top, a 4-top and a 2-top ==")
    print("first-fit:", [t.table_id for t in FirstFitAssignment().choose(2, patio) or ()])
    print("best-fit: ", [t.table_id for t in BestFitAssignment().choose(2, patio) or ()])
    print("== Party of 10, no single table fits ==")
    print("best-fit:   ", BestFitAssignment().choose(10, tables))
    combo = CombineTablesAssignment().choose(10, tables) or ()
    print("combine:    ", [t.table_id for t in combo], "seats", sum(t.capacity for t in combo))

    print("== Overlap check: book 19:00, then ask about 19:30 on the same table ==")
    seven = datetime(2026, 11, 6, 19, 0)
    table = tables[0]
    exact, interval = ExactStartTimeBook(), IntervalBook(timedelta(minutes=90))
    exact.book(table, seven)
    interval.book(table, seven)
    later = seven + timedelta(minutes=30)
    print("exact-start says free:", exact.is_free(table, later), "(double booking!)")
    print("interval says free:   ", interval.is_free(table, later))

    menu = sample_menu()
    burger, lemonade = menu.get("burger"), menu.get("lemonade")
    print("== Kitchen flow ==")
    direct = DirectKitchen()
    DirectCallOrder("T3", direct).fire(burger)
    print("direct call queue:", direct.queue)
    kitchen = CommandQueueKitchen()
    kitchen.submit(FireItem("T3", burger))
    kitchen.submit(FireItem("T4", lemonade))
    kitchen.submit(FireItem("T4", burger))
    kitchen.submit(RushTable("T4"))
    print("commands drained:", kitchen.drain(), "board:", kitchen.board)
    kitchen.undo_last()
    undone = kitchen.undo_last()
    print("undid", type(undone).__name__, "-> board:", kitchen.board)

    print("== State pattern line ==")
    line = StatefulLine(burger)
    line.fire()
    line.void()
    print("voided after firing ->", line.state.name, "| waste logged:", line.waste_logged)
    try:
        line.serve()
    except InvalidTransition as exc:
        print("rejected:", exc)

    print("== Splitting $100.00 three ways ==")
    naive = naive_equal_split(Decimal("100.00"), 3)
    print("naive:   ", [str(s) for s in naive], "sum", sum(naive))
    fair = split_with_if_else("equal", Decimal("100.00"), ["A", "B", "C"])
    print("allocate:", [str(s) for s in fair.values()], "sum", sum(fair.values()))

    print("== Decorator modifiers ==")
    dish = NoOnion(AddBacon(BaseDish(burger)))
    print(dish.description(), dish.price())

    print("== Delivery adapter ==")
    adapter = DeliveryOrderAdapter("MarketplaceX", {"mx-991": "burger", "mx-12": "lemonade"})
    payload = {"items": [{"external_id": "mx-991", "qty": 2, "options": ["no onion"]},
                         {"external_id": "mx-12"}]}
    print(adapter.to_lines(payload))


if __name__ == "__main__":
    demo()
