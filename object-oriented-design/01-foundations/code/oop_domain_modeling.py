"""Value objects vs entities, immutability, Law of Demeter, tell-don't-ask,
and two classic anti-patterns (primitive obsession, anemic domain model).

Run:  python3 oop_domain_modeling.py
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum


# ---------------------------------------------------------------------------
# Value objects: defined entirely by their values, immutable, self-validating
# ---------------------------------------------------------------------------

class CurrencyMismatch(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    """Two Money objects with the same amount and currency are the same money."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("use Decimal for money, never float")
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError(f"bad ISO 4217 code: {self.currency!r}")
        # Frozen dataclasses block normal assignment, so normalise via object.__setattr__.
        object.__setattr__(self, "amount",
                           self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> Money:
        return Money(self.amount * Decimal(factor), self.currency)

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount <= other.amount

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclass(frozen=True, slots=True)
class EmailAddress:
    """Cure for primitive obsession: the rules for an email live in one place."""

    value: str

    def __post_init__(self) -> None:
        normalised = self.value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalised):
            raise ValueError(f"invalid email: {self.value!r}")
        object.__setattr__(self, "value", normalised)

    @property
    def domain(self) -> str:
        return self.value.split("@", 1)[1]


# ---------------------------------------------------------------------------
# Entities: defined by identity that persists while attributes change
# ---------------------------------------------------------------------------

class Wallet:
    """Tell-don't-ask: callers tell the wallet to pay; the wallet decides."""

    def __init__(self, balance: Money) -> None:
        self._balance = balance

    @property
    def balance(self) -> Money:
        return self._balance

    def can_pay(self, amount: Money) -> bool:
        return amount <= self._balance

    def pay(self, amount: Money) -> None:
        if not self.can_pay(amount):
            raise ValueError("insufficient balance")
        self._balance = self._balance - amount


class Customer:
    """An entity: same id means same customer, even after a rename."""

    def __init__(self, customer_id: str, name: str, email: EmailAddress, wallet: Wallet) -> None:
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self._wallet = wallet

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self.customer_id == other.customer_id

    def __hash__(self) -> int:
        return hash(self.customer_id)  # identity never changes, so hash is stable

    # Law of Demeter: expose the behaviour, not the wallet.
    def pay(self, amount: Money) -> None:
        self._wallet.pay(amount)

    def can_afford(self, amount: Money) -> bool:
        return self._wallet.can_pay(amount)

    @property
    def wallet_for_reporting(self) -> Wallet:
        return self._wallet


def checkout_demeter_violation(customer: Customer, price: Money) -> None:
    """Asks, then decides on the wallet's behalf, reaching two levels deep.
    It also duplicates the 'enough money?' rule that Wallet already owns."""
    wallet = customer.wallet_for_reporting
    if wallet.balance.amount >= price.amount:      # asking...
        wallet._balance = wallet.balance - price   # ...then poking internals
    else:
        raise ValueError("insufficient balance")


def checkout_tell(customer: Customer, price: Money) -> None:
    customer.pay(price)  # tell the object what you want; it knows how


# ---------------------------------------------------------------------------
# Immutability: frozen dataclasses, replace(), and the shallow-freeze trap
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShallowConfig:
    """Frozen... but the list inside can still be mutated."""

    region: str
    allowed_ips: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeepConfig:
    region: str
    allowed_ips: tuple[str, ...] = ()

    def with_ip(self, ip: str) -> DeepConfig:
        # "Changing" an immutable object means building a new one.
        return dataclasses.replace(self, allowed_ips=(*self.allowed_ips, ip))


# ---------------------------------------------------------------------------
# Anemic vs rich domain model: a subscription
# ---------------------------------------------------------------------------

class SubStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass
class AnemicSubscription:
    """Just a bag of fields. Every rule lives somewhere else, maybe twice."""

    status: SubStatus = SubStatus.TRIAL
    cancelled_on: date | None = None


class SubscriptionService:
    """The anemic model's partner: all logic outside the data."""

    def cancel(self, sub: AnemicSubscription, today: date) -> None:
        if sub.status is SubStatus.CANCELLED:
            raise ValueError("already cancelled")
        sub.status = SubStatus.CANCELLED
        sub.cancelled_on = today
    # Nothing stops other code from writing sub.status = ACTIVE after this.


class Subscription:
    """Rich model: the object owns its state machine and enforces it."""

    _ALLOWED = {
        SubStatus.TRIAL: {SubStatus.ACTIVE, SubStatus.CANCELLED},
        SubStatus.ACTIVE: {SubStatus.CANCELLED},
        SubStatus.CANCELLED: set(),
    }

    def __init__(self, plan_price: Money) -> None:
        self.plan_price = plan_price
        self._status = SubStatus.TRIAL
        self._cancelled_on: date | None = None

    @property
    def status(self) -> SubStatus:
        return self._status

    @property
    def cancelled_on(self) -> date | None:
        return self._cancelled_on

    def _move_to(self, new: SubStatus) -> None:
        if new not in self._ALLOWED[self._status]:
            raise ValueError(f"cannot go from {self._status.value} to {new.value}")
        self._status = new

    def activate(self) -> None:
        self._move_to(SubStatus.ACTIVE)

    def cancel(self, today: date) -> None:
        self._move_to(SubStatus.CANCELLED)
        self._cancelled_on = today


def demo() -> None:
    print("== Value objects ==")
    a, b = Money(Decimal("10.005"), "USD"), Money(Decimal("10.00"), "USD")
    print(f"{a} == {b}? {a == b}  (rounded half-even on creation)")
    print("sum:", a + b * 2, "| usable as dict key:", {a: "ten"}[b])
    try:
        a + Money(Decimal("1"), "EUR")
    except CurrencyMismatch as exc:
        print("refused to add:", exc)
    print("email normalised:", EmailAddress("  Ana@Example.COM ").value)

    print("\n== Entities ==")
    wallet = Wallet(Money(Decimal("50"), "USD"))
    c1 = Customer("c-1", "Ana", EmailAddress("ana@example.com"), wallet)
    c2 = Customer("c-1", "Ana Lima", EmailAddress("ana@lima.dev"), wallet)
    print("same id, different name -> equal:", c1 == c2)

    print("\n== Tell, don't ask ==")
    checkout_tell(c1, Money(Decimal("20"), "USD"))
    print("balance after telling:", c1.wallet_for_reporting.balance)

    print("\n== Immutability ==")
    shallow = ShallowConfig("eu-west", ["10.0.0.1"])
    shallow.allowed_ips.append("6.6.6.6")
    print("frozen but mutated:", shallow.allowed_ips)
    deep = DeepConfig("eu-west", ("10.0.0.1",))
    print("new object:", deep.with_ip("10.0.0.2"), "| old untouched:", deep)

    print("\n== Rich model ==")
    sub = Subscription(Money(Decimal("9.99"), "USD"))
    sub.activate()
    sub.cancel(date(2026, 10, 31))
    try:
        sub.activate()
    except ValueError as exc:
        print("state machine guard:", exc)


if __name__ == "__main__":
    demo()
