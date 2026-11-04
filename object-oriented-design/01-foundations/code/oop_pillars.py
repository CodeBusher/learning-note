"""The four pillars of OOP (encapsulation, abstraction, inheritance,
polymorphism) shown with Python's own tools.

Run:  python3 oop_pillars.py
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from functools import singledispatch
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# 0. The procedural starting point: data in a dict, rules in loose functions
# ---------------------------------------------------------------------------

def proc_open_account(owner: str) -> dict:
    return {"owner": owner, "balance": Decimal("0"), "history": []}


def proc_deposit(account: dict, amount: Decimal) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    account["balance"] += amount
    account["history"].append(("deposit", amount))


def proc_withdraw(account: dict, amount: Decimal) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if amount > account["balance"]:
        raise ValueError("insufficient funds")
    account["balance"] -= amount
    account["history"].append(("withdraw", amount))


# ---------------------------------------------------------------------------
# 1. Encapsulation: the object guards its own invariants
# ---------------------------------------------------------------------------

class InsufficientFunds(Exception):
    """Raised when a withdrawal would break the overdraft rule."""


class AccountFrozen(Exception):
    """Raised when money tries to move through a frozen account."""


class AccountStatus(Enum):
    """Lifecycle of an account. Members carry behaviour, not just labels."""

    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

    @property
    def can_move_money(self) -> bool:
        return self is AccountStatus.ACTIVE


class BankAccount:
    """A balance that can only change through deposit() and withdraw().

    Invariant: balance >= -overdraft_limit, always.
    """

    def __init__(self, owner: str, overdraft_limit: Decimal = Decimal("0")) -> None:
        self.owner = owner                      # public: fine to read and write
        self.overdraft_limit = overdraft_limit  # goes through the property setter
        self.__balance = Decimal("0")           # mangled to _BankAccount__balance
        self._history: list[tuple[str, Decimal]] = []
        self.status = AccountStatus.ACTIVE

    # Read-only view of the balance: there is deliberately no setter.
    @property
    def balance(self) -> Decimal:
        return self.__balance

    @property
    def overdraft_limit(self) -> Decimal:
        return self._overdraft_limit

    @overdraft_limit.setter
    def overdraft_limit(self, value: Decimal) -> None:
        if value < 0:
            raise ValueError("overdraft limit cannot be negative")
        self._overdraft_limit = value

    @property
    def history(self) -> tuple[tuple[str, Decimal], ...]:
        # Hand out a copy so callers cannot append fake transactions.
        return tuple(self._history)

    def deposit(self, amount: Decimal) -> None:
        self._check_can_move(amount)
        self.__balance += amount
        self._history.append(("deposit", amount))

    def withdraw(self, amount: Decimal) -> None:
        self._check_can_move(amount)
        if self.__balance - amount < -self._overdraft_limit:
            raise InsufficientFunds(f"{self.owner} cannot withdraw {amount}")
        self.__balance -= amount
        self._history.append(("withdraw", amount))

    def freeze(self) -> None:
        self.status = AccountStatus.FROZEN

    def _check_can_move(self, amount: Decimal) -> None:
        if not self.status.can_move_money:
            raise AccountFrozen(f"account is {self.status.value}")
        if amount <= 0:
            raise ValueError("amount must be positive")

    def __repr__(self) -> str:
        return f"BankAccount(owner={self.owner!r}, balance={self.__balance})"


# ---------------------------------------------------------------------------
# 3a. Single inheritance + super(): a SavingsAccount IS-A BankAccount
# ---------------------------------------------------------------------------

class SavingsAccount(BankAccount):
    """Adds interest. Reuses every rule of BankAccount via super()."""

    def __init__(self, owner: str, annual_rate: Decimal) -> None:
        super().__init__(owner, overdraft_limit=Decimal("0"))
        self.annual_rate = annual_rate
        # This does NOT touch the parent's balance: it becomes
        # _SavingsAccount__balance, a different attribute. Name mangling
        # exists to prevent exactly this kind of accidental clash.
        self.__balance = "not the real balance"

    def add_monthly_interest(self) -> Decimal:
        interest = (self.balance * self.annual_rate / 12).quantize(Decimal("0.01"))
        if interest > 0:
            self.deposit(interest)  # go through the public API, keep invariants
        return interest


# ---------------------------------------------------------------------------
# 2. Abstraction: callers see "charge a card", not HTTP, retries, signatures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Receipt:
    """Immutable record of a successful charge."""

    gateway: str
    amount: Decimal
    reference: str


class PaymentGateway(ABC):
    """What every payment provider must offer. Cannot be instantiated."""

    name: str = "abstract"

    def __init__(self) -> None:
        self._counter = 0

    @abstractmethod
    def _submit(self, amount: Decimal, token: str) -> str:
        """Talk to the provider; return its transaction reference."""

    def charge(self, amount: Decimal, token: str) -> Receipt:
        # Shared, provider-independent rules live once, in the base class.
        if amount <= 0:
            raise ValueError("amount must be positive")
        if not token:
            raise ValueError("missing payment token")
        return Receipt(self.name, amount, self._submit(amount, token))

    def _next_ref(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:04d}"


class CardGateway(PaymentGateway):
    """Pretend card-network provider."""

    name = "card"

    def _submit(self, amount: Decimal, token: str) -> str:
        return self._next_ref("ch")


class BankTransferGateway(PaymentGateway):
    """Pretend account-to-account provider."""

    name = "bank_transfer"

    def _submit(self, amount: Decimal, token: str) -> str:
        return self._next_ref("bt")


# ---------------------------------------------------------------------------
# 4a. Polymorphism without inheritance: Protocol (static duck typing)
# ---------------------------------------------------------------------------

@runtime_checkable
class SupportsCharge(Protocol):
    def charge(self, amount: Decimal, token: str) -> Receipt: ...


class GiftCardWallet:
    """Does not inherit from PaymentGateway, yet fits SupportsCharge."""

    def __init__(self, credit: Decimal) -> None:
        self.credit = credit

    def charge(self, amount: Decimal, token: str) -> Receipt:
        if amount > self.credit:
            raise InsufficientFunds("gift card credit too low")
        self.credit -= amount
        return Receipt("gift_card", amount, f"gc_{token}")


def checkout(payer: SupportsCharge, amount: Decimal, token: str) -> Receipt:
    """One call site, many implementations: that is polymorphism."""
    return payer.charge(amount, token)


# ---------------------------------------------------------------------------
# 3b. Multiple inheritance, MRO and cooperative super(): mixins
# ---------------------------------------------------------------------------

class Serializable:
    """Base of the chain: turns public attributes into a dict."""

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}


class RedactMixin:
    """Masks sensitive fields. Calls super() so others can join the chain."""

    redacted_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        data = super().to_dict()
        for name in self.redacted_fields:
            if name in data:
                data[name] = "***"
        return data


class TypeTagMixin:
    """Adds the class name so a reader knows what it is deserializing."""

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["_type"] = type(self).__name__
        return data


class JsonMixin:
    """Adds a capability (to_json) on top of whatever to_dict() returns."""

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)


class CustomerRecord(JsonMixin, RedactMixin, TypeTagMixin, Serializable):
    """Mixins first, the real base last: the conventional ordering."""

    redacted_fields = ("card_number",)

    def __init__(self, name: str, card_number: str) -> None:
        self.name = name
        self.card_number = card_number


# ---------------------------------------------------------------------------
# 4b. Dunder methods: make your object behave like a built-in
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Track:
    title: str
    seconds: int


class Playlist(Sequence[Track]):
    """Implements only __getitem__ and __len__; collections.abc.Sequence
    then supplies __contains__, __iter__, __reversed__, index() and count()."""

    def __init__(self, name: str, tracks: list[Track] | None = None) -> None:
        self.name = name
        self._tracks = list(tracks or [])

    def __getitem__(self, index):  # type: ignore[override]
        if isinstance(index, slice):
            return Playlist(self.name, self._tracks[index])
        return self._tracks[index]

    def __len__(self) -> int:
        return len(self._tracks)

    def __add__(self, other: Playlist) -> Playlist:
        if not isinstance(other, Playlist):
            return NotImplemented
        return Playlist(f"{self.name} + {other.name}", self._tracks + other._tracks)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playlist):
            return NotImplemented
        return self._tracks == other._tracks

    __hash__ = None  # type: ignore[assignment]  # mutable container: unhashable

    def __repr__(self) -> str:
        return f"Playlist({self.name!r}, {len(self)} tracks)"

    @property
    def duration(self) -> int:
        return sum(t.seconds for t in self)


# ---------------------------------------------------------------------------
# 4c. "Overloading" in Python: one name, implementation chosen by type
# ---------------------------------------------------------------------------

@singledispatch
def describe(value: object) -> str:
    return f"something of type {type(value).__name__}"


@describe.register
def _(value: int) -> str:
    return f"the integer {value}"


@describe.register
def _(value: list) -> str:
    return f"a list of {len(value)} items"


@describe.register
def _(value: BankAccount) -> str:
    return f"{value.owner}'s account"


# ---------------------------------------------------------------------------
# dataclass: a class whose job is mostly to hold data
# ---------------------------------------------------------------------------

@dataclass(order=True)
class Ticket:
    """Generated __init__, __repr__, __eq__ and ordering (by priority first)."""

    priority: int
    title: str = field(compare=False)
    tags: list[str] = field(default_factory=list, compare=False)


def demo() -> None:
    print("== Procedural: nothing stops a bad write ==")
    acct = proc_open_account("ana")
    proc_deposit(acct, Decimal("50"))
    acct["balance"] = Decimal("-1000")  # any code anywhere can do this
    print("dict balance after a stray write:", acct["balance"])

    print("\n== Encapsulation ==")
    a = BankAccount("ana", overdraft_limit=Decimal("20"))
    a.deposit(Decimal("50"))
    a.withdraw(Decimal("65"))
    print(a, "| history:", a.history)
    try:
        a.balance = Decimal("1000")  # type: ignore[misc]
    except AttributeError as exc:
        print("cannot assign balance:", exc)
    print("mangled name exists:", "_BankAccount__balance" in vars(a))

    print("\n== Inheritance ==")
    s = SavingsAccount("ben", annual_rate=Decimal("0.06"))
    s.deposit(Decimal("1000"))
    print("interest:", s.add_monthly_interest(), "->", s.balance)
    print("both mangled attributes:", sorted(k for k in vars(s) if "balance" in k))

    print("\n== Abstraction + polymorphism ==")
    try:
        PaymentGateway()  # type: ignore[abstract]
    except TypeError as exc:
        print("ABC refuses:", exc)
    for payer in (CardGateway(), BankTransferGateway(), GiftCardWallet(Decimal("30"))):
        print(" ", type(payer).__name__, isinstance(payer, SupportsCharge),
              checkout(payer, Decimal("25"), "tok_1"))

    print("\n== Mixins and the MRO ==")
    print([c.__name__ for c in CustomerRecord.__mro__])
    print(CustomerRecord("ana", "4242424242424242").to_json())

    print("\n== Dunder methods ==")
    p = Playlist("focus", [Track("a", 200), Track("b", 180)])
    q = Playlist("chill", [Track("c", 240)])
    both = p + q
    print(both, "duration", both.duration, "| Track('c',240) in both:",
          Track("c", 240) in both, "| reversed:", [t.title for t in reversed(both)])

    print("\n== singledispatch ==")
    for v in (3, [1, 2], a, 2.5):
        print(" ", describe(v))

    print("\n== dataclass(order=True) ==")
    print(sorted([Ticket(3, "typo"), Ticket(1, "outage"), Ticket(2, "slow page")]))


if __name__ == "__main__":
    demo()
