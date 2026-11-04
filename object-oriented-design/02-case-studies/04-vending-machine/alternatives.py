"""Competing designs for the vending machine, so they can be compared side by side.

Sections
  1. State handling:   if/elif on a status enum  vs  table-driven state machine
                       (the State pattern version is vending_machine.py)
  2. Change-making:    greedy vs dynamic programming, unlimited and limited coins
  3. Inventory model:  quantity on Product  vs  unit-tracked slot with expiry
                       (count-on-Slot is vending_machine.py)
  4. Payments:         if/elif on a method string  vs  Strategy
  5. Money:            float vs Decimal vs integer cents
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum, auto

from vending_machine import make_change


# ===========================================================================
# 1. State handling
# ===========================================================================

class Status(Enum):
    IDLE = auto()
    HAS_CREDIT = auto()
    OUT_OF_SERVICE = auto()


class StatusEnumMachine:
    """Approach A: one status field, and every method branches on it."""

    def __init__(self, prices: Mapping[str, int], stock: Mapping[str, int]) -> None:
        self.prices = dict(prices)
        self.stock = dict(stock)
        self.status = Status.IDLE
        self.credit = 0

    def insert_coin(self, cents: int) -> None:
        if self.status is Status.IDLE or self.status is Status.HAS_CREDIT:
            self.credit += cents
            self.status = Status.HAS_CREDIT
        elif self.status is Status.OUT_OF_SERVICE:
            raise RuntimeError("out of service")

    def select(self, code: str) -> int:
        """Vend and return change in cents."""
        if self.status is Status.IDLE:
            raise RuntimeError("insert coins first")
        elif self.status is Status.HAS_CREDIT:
            if self.stock.get(code, 0) == 0:
                raise RuntimeError("sold out")
            if self.credit < self.prices[code]:
                raise RuntimeError("insufficient credit")
            self.stock[code] -= 1
            change, self.credit = self.credit - self.prices[code], 0
            self.status = Status.IDLE
            return change
        elif self.status is Status.OUT_OF_SERVICE:
            raise RuntimeError("out of service")
        raise AssertionError("unreachable")

    def cancel(self) -> int:
        if self.status is Status.HAS_CREDIT:
            refund, self.credit = self.credit, 0
            self.status = Status.IDLE
            return refund
        elif self.status is Status.IDLE:
            return 0
        raise RuntimeError("out of service")


class Event(Enum):
    COIN = auto()
    SELECT = auto()
    CANCEL = auto()
    SERVICE_OPEN = auto()
    SERVICE_CLOSE = auto()


Action = Callable[["TableDrivenMachine", object], object]


class TableDrivenMachine:
    """Approach C: the transition table is data; the engine is a few lines.

    Each entry maps (state, event) to (guard, action, next_state).  The guard
    decides whether the transition fires; a missing key means "illegal here".
    """

    def __init__(self, prices: Mapping[str, int], stock: Mapping[str, int]) -> None:
        self.prices = dict(prices)
        self.stock = dict(stock)
        self.status = Status.IDLE
        self.credit = 0

    # actions --------------------------------------------------------------
    def _add_credit(self, cents: object) -> None:
        assert isinstance(cents, int)
        self.credit += cents

    def _can_vend(self, code: object) -> bool:
        assert isinstance(code, str)
        return self.stock.get(code, 0) > 0 and self.credit >= self.prices[code]

    def _vend(self, code: object) -> int:
        assert isinstance(code, str)
        self.stock[code] -= 1
        change, self.credit = self.credit - self.prices[code], 0
        return change

    def _refund(self, _: object) -> int:
        refund, self.credit = self.credit, 0
        return refund

    @staticmethod
    def _always(_m: "TableDrivenMachine", _p: object) -> bool:
        return True

    TABLE: dict[tuple[Status, Event], tuple[Callable[..., bool], Action | None, Status]] = {
        (Status.IDLE, Event.COIN): (_always, _add_credit, Status.HAS_CREDIT),
        (Status.IDLE, Event.CANCEL): (_always, None, Status.IDLE),
        (Status.IDLE, Event.SERVICE_OPEN): (_always, None, Status.OUT_OF_SERVICE),
        (Status.HAS_CREDIT, Event.COIN): (_always, _add_credit, Status.HAS_CREDIT),
        (Status.HAS_CREDIT, Event.SELECT): (_can_vend, _vend, Status.IDLE),
        (Status.HAS_CREDIT, Event.CANCEL): (_always, _refund, Status.IDLE),
        (Status.OUT_OF_SERVICE, Event.SERVICE_CLOSE): (_always, None, Status.IDLE),
    }

    def handle(self, event: Event, payload: object = None) -> object:
        entry = self.TABLE.get((self.status, event))
        if entry is None:
            raise RuntimeError(f"{event.name} not allowed in {self.status.name}")
        guard, action, next_status = entry
        if not guard(self, payload):
            raise RuntimeError(f"guard rejected {event.name} in {self.status.name}")
        result = action(self, payload) if action else None
        self.status = next_status
        return result


# ===========================================================================
# 2. Change-making
# ===========================================================================

def greedy_change(amount: int, denominations: list[int]) -> list[int] | None:
    """Largest coin first, unlimited supply. Optimal only for 'canonical' coin systems."""
    coins: list[int] = []
    for d in sorted(denominations, reverse=True):
        while amount >= d:
            amount -= d
            coins.append(d)
    return coins if amount == 0 else None


def dp_change(amount: int, denominations: list[int]) -> list[int] | None:
    """Fewest coins, unlimited supply. Classic O(amount * len(denominations)) DP."""
    INF = float("inf")
    fewest = [0] + [INF] * amount
    last_coin = [0] * (amount + 1)
    for a in range(1, amount + 1):
        for d in denominations:
            if d <= a and fewest[a - d] + 1 < fewest[a]:
                fewest[a] = fewest[a - d] + 1
                last_coin[a] = d
    if fewest[amount] == INF:
        return None
    coins = []
    while amount:
        coins.append(last_coin[amount])
        amount -= last_coin[amount]
    return sorted(coins, reverse=True)


def greedy_change_limited(amount: int, available: Mapping[int, int]) -> dict[int, int] | None:
    """Greedy, but each denomination has a finite count (real coin tubes)."""
    plan: dict[int, int] = {}
    for d in sorted(available, reverse=True):
        take = min(available[d], amount // d)
        if take:
            plan[d] = take
            amount -= take * d
    return plan if amount == 0 else None


def dp_change_limited(amount: int, available: Mapping[int, int]) -> dict[int, int] | None:
    """Bounded DP: the algorithm the recommended solution uses."""
    return make_change(amount, available)


def find_greedy_counterexample(denominations: list[int]) -> int | None:
    """Smallest amount where greedy uses more coins than optimal, or None if canonical.

    A classic result (Kozen and Zaks) says that if a counterexample exists, one
    exists below the sum of the two largest coins, so the search is bounded.
    """
    ds = sorted(denominations)
    bound = ds[-1] + ds[-2] if len(ds) >= 2 else ds[-1]
    for amount in range(1, bound):
        g, o = greedy_change(amount, ds), dp_change(amount, ds)
        if o is not None and (g is None or len(g) > len(o)):
            return amount
    return None


# ===========================================================================
# 3. Inventory modelling
# ===========================================================================

@dataclass
class ProductWithQuantity:
    """Approach A: stock count lives on the product itself.

    Breaks as soon as the same product sits in two slots, or two machines share
    one catalogue entry: whose count is it?
    """

    code: str
    name: str
    price_cents: int
    quantity: int = 0


@dataclass(frozen=True)
class Unit:
    """One physical item, for machines that must track expiry (fresh food)."""

    lot: str
    best_before: date


@dataclass
class UnitTrackedSlot:
    """Approach C: the slot is a FIFO queue of individual units.

    Needed for fresh-food machines and smart fridges where each item has a
    date; overkill for cans of soda.
    """

    code: str
    name: str
    price_cents: int
    units: deque[Unit] = field(default_factory=deque)

    @property
    def quantity(self) -> int:
        return len(self.units)

    def load(self, unit: Unit) -> None:
        self.units.append(unit)  # back of the spiral

    def sellable(self, today: date) -> bool:
        return bool(self.units) and self.units[0].best_before >= today

    def vend(self, today: date) -> Unit:
        if not self.sellable(today):
            raise RuntimeError(f"{self.code}: empty or front item expired")
        return self.units.popleft()  # front of the spiral drops first

    def pull_expired(self, today: date) -> list[Unit]:
        expired = [u for u in self.units if u.best_before < today]
        self.units = deque(u for u in self.units if u.best_before >= today)
        return expired


# ===========================================================================
# 4. Payments
# ===========================================================================

def checkout_if_else(method: str, price_cents: int, **details: object) -> str:
    """Approach A: one function that knows every payment type."""
    if method == "cash":
        inserted = int(details["inserted_cents"])  # type: ignore[arg-type]
        if inserted < price_cents:
            raise RuntimeError("insufficient cash")
        return f"cash ok, change {inserted - price_cents}c"
    elif method == "card":
        balance = int(details["balance_cents"])  # type: ignore[arg-type]
        if balance < price_cents:
            raise RuntimeError("card declined")
        return "card captured"
    elif method == "mobile":
        if not details.get("wallet_token"):
            raise RuntimeError("no wallet token")
        return "mobile wallet captured"
    raise ValueError(f"unknown payment method {method!r}")


# The Strategy version is CashPayment / CardPayment in vending_machine.py; adding
# a QR or mobile-wallet method there means one new class and zero edits to states.


# ===========================================================================
# 5. Money representation
# ===========================================================================

def float_total(prices: list[float]) -> float:
    return sum(prices)


def decimal_total(prices: list[str]) -> Decimal:
    return sum((Decimal(p) for p in prices), Decimal("0"))


def cents_total(prices: list[int]) -> int:
    return sum(prices)


# ===========================================================================
# Demo
# ===========================================================================

def demo() -> None:
    print("== 1. State handling ==")
    enum_vm = StatusEnumMachine({"A1": 125}, {"A1": 1})
    enum_vm.insert_coin(100)
    enum_vm.insert_coin(50)
    print("enum-flag machine change:", enum_vm.select("A1"))
    table_vm = TableDrivenMachine({"A1": 125}, {"A1": 1})
    table_vm.handle(Event.COIN, 100)
    table_vm.handle(Event.COIN, 50)
    print("table-driven machine change:", table_vm.handle(Event.SELECT, "A1"))
    try:
        table_vm.handle(Event.SELECT, "A1")
    except RuntimeError as exc:
        print("table-driven rejects:", exc)

    print("\n== 2. Change-making ==")
    odd = [1, 3, 4]
    print(f"coins {odd}, amount 6: greedy {greedy_change(6, odd)}, dp {dp_change(6, odd)}")
    print("first greedy counterexample for", odd, "->", find_greedy_counterexample(odd))
    print("first greedy counterexample for US coins ->",
          find_greedy_counterexample([1, 5, 10, 25]))
    tubes = {25: 1, 10: 3, 5: 0}
    print(f"tubes {tubes}, owe 30c: greedy {greedy_change_limited(30, tubes)}, "
          f"dp {dp_change_limited(30, tubes)}")

    print("\n== 3. Inventory ==")
    slot = UnitTrackedSlot("C1", "Sandwich", 450)
    slot.load(Unit("L1", date(2026, 10, 30)))
    slot.load(Unit("L2", date(2026, 11, 3)))
    today = date(2026, 10, 31)
    print("sellable with expired item at front:", slot.sellable(today))
    print("pulled:", [u.lot for u in slot.pull_expired(today)], "| now sellable:", slot.sellable(today))

    print("\n== 4. Payments ==")
    print(checkout_if_else("cash", 125, inserted_cents=150))
    print(checkout_if_else("card", 125, balance_cents=500))

    print("\n== 5. Money ==")
    print("float  0.10 + 0.20 =", float_total([0.10, 0.20]))
    print("Decimal 0.10 + 0.20 =", decimal_total(["0.10", "0.20"]))
    print("cents   10 + 20     =", cents_total([10, 20]))


if __name__ == "__main__":
    demo()
