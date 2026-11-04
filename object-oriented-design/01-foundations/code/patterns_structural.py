"""Structural design patterns (plus Specification, which is built on Composite).

Patterns in this file:
    Adapter       - make a legacy bank SDK look like our PaymentProcessor interface
    Facade        - one simple front door to a parking lot's subsystems
    Decorator     - stackable grocery discounts, and Python's own @decorator syntax
    Proxy         - a caching stand-in for a slow price service (for comparison)
    Composite     - files and directories treated uniformly
    Specification - composable search filters: ExtensionIs("py") & LargerThan(1000)

Run ``python3 patterns_structural.py`` for a short demo of each.
"""

from __future__ import annotations

import functools
import itertools
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import ParamSpec, Protocol, TypeVar

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# ===========================================================================
# Adapter
# ===========================================================================

class PaymentError(Exception):
    """A charge was declined or failed."""


class PaymentProcessor(Protocol):
    """The interface *our* code is written against."""

    def charge(self, amount: Decimal, card_token: str) -> str:
        """Charge ``amount`` dollars and return a transaction id."""
        ...


class LegacyBankGateway:
    """A third-party SDK we cannot change: integer cents, dict responses."""

    _ids = itertools.count(1)

    def make_payment(self, amount_cents: int, token: str, currency: str = "USD") -> dict[str, str]:
        if amount_cents <= 0 or not token:
            return {"status": "DECLINED", "reason": "invalid request"}
        return {"status": "OK", "ref": f"LB-{next(self._ids):05d}"}


class LegacyBankAdapter:
    """Wraps the gateway and translates units, return values and errors."""

    def __init__(self, gateway: LegacyBankGateway) -> None:
        self._gateway = gateway

    def charge(self, amount: Decimal, card_token: str) -> str:
        cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
        response = self._gateway.make_payment(cents, card_token)
        if response["status"] != "OK":
            raise PaymentError(response.get("reason", "declined"))
        return response["ref"]


def checkout(processor: PaymentProcessor, amount: Decimal, card_token: str) -> str:
    """Client code that knows nothing about the legacy SDK."""
    return processor.charge(amount, card_token)


# ===========================================================================
# Facade
# ===========================================================================

@dataclass(frozen=True)
class Ticket:
    ticket_id: int
    plate: str
    spot: str
    entered_at: int  # minutes since opening, to keep the example deterministic


class SpotAllocator:
    def __init__(self, spots: list[str]) -> None:
        self._free = list(spots)

    def allocate(self) -> str:
        if not self._free:
            raise LookupError("lot is full")
        return self._free.pop(0)

    def release(self, spot: str) -> None:
        self._free.append(spot)

    def free_count(self) -> int:
        return len(self._free)


class TicketOffice:
    def __init__(self) -> None:
        self._ids = itertools.count(1)
        self.open_tickets: dict[int, Ticket] = {}

    def issue(self, plate: str, spot: str, now: int) -> Ticket:
        ticket = Ticket(next(self._ids), plate, spot, now)
        self.open_tickets[ticket.ticket_id] = ticket
        return ticket

    def close(self, ticket_id: int) -> Ticket:
        try:
            return self.open_tickets.pop(ticket_id)
        except KeyError:
            raise LookupError(f"unknown ticket {ticket_id}") from None


class Tariff:
    def __init__(self, rate_per_hour: Decimal) -> None:
        self.rate_per_hour = rate_per_hour

    def fee(self, minutes: int) -> Decimal:
        hours = max(1, -(-minutes // 60))  # ceiling division
        return self.rate_per_hour * hours


class ParkingLotFacade:
    """Two methods hide three collaborating subsystems from the entry/exit kiosks."""

    def __init__(self, spots: list[str], rate_per_hour: Decimal) -> None:
        self._spots = SpotAllocator(spots)
        self._tickets = TicketOffice()
        self._tariff = Tariff(rate_per_hour)

    def enter(self, plate: str, now: int) -> Ticket:
        spot = self._spots.allocate()
        return self._tickets.issue(plate, spot, now)

    def exit(self, ticket_id: int, now: int) -> Decimal:
        ticket = self._tickets.close(ticket_id)
        self._spots.release(ticket.spot)
        return self._tariff.fee(now - ticket.entered_at)

    def free_spots(self) -> int:
        return self._spots.free_count()


# ===========================================================================
# Decorator (object decorator)
# ===========================================================================

class LineItem(ABC):
    """Anything on a receipt that has a price and a description."""

    @abstractmethod
    def price(self) -> Decimal: ...

    @abstractmethod
    def description(self) -> str: ...


@dataclass
class Product(LineItem):
    name: str
    unit_price: Decimal
    quantity: int = 1

    def price(self) -> Decimal:
        return money(self.unit_price * self.quantity)

    def description(self) -> str:
        return f"{self.quantity} x {self.name}"


class Discount(LineItem):
    """Base decorator: same interface as what it wraps, delegates by default."""

    def __init__(self, inner: LineItem) -> None:
        self.inner = inner

    def price(self) -> Decimal:
        return self.inner.price()

    def description(self) -> str:
        return self.inner.description()


class PercentOff(Discount):
    def __init__(self, inner: LineItem, percent: Decimal) -> None:
        super().__init__(inner)
        self.percent = percent

    def price(self) -> Decimal:
        return money(self.inner.price() * (100 - self.percent) / 100)

    def description(self) -> str:
        return f"{self.inner.description()} [-{self.percent}%]"


class AmountOff(Discount):
    def __init__(self, inner: LineItem, amount: Decimal) -> None:
        super().__init__(inner)
        self.amount = amount

    def price(self) -> Decimal:
        return max(Decimal("0.00"), self.inner.price() - self.amount)

    def description(self) -> str:
        return f"{self.inner.description()} [-${self.amount}]"


# Python's @decorator syntax is the same idea applied to functions.
P = ParamSpec("P")
R = TypeVar("R")


def retry(times: int, exceptions: tuple[type[Exception], ...] = (Exception,)) -> Callable[
    [Callable[P, R]], Callable[P, R]
]:
    """Wrap a function so transient failures are retried up to ``times`` attempts."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise
            raise AssertionError("unreachable")

        return wrapper

    return decorator


# ===========================================================================
# Proxy (included so it can be compared with Decorator and Adapter)
# ===========================================================================

class PriceService(Protocol):
    def price_of(self, sku: str) -> Decimal: ...


class RemotePriceService:
    """Pretend this is a slow network call."""

    def __init__(self, prices: dict[str, Decimal]) -> None:
        self._prices = prices
        self.calls = 0

    def price_of(self, sku: str) -> Decimal:
        self.calls += 1
        return self._prices[sku]


class CachingPriceProxy:
    """Same interface as the real service; controls *access* to it (here: caching)."""

    def __init__(self, real: PriceService) -> None:
        self._real = real
        self._cache: dict[str, Decimal] = {}

    def price_of(self, sku: str) -> Decimal:
        if sku not in self._cache:
            self._cache[sku] = self._real.price_of(sku)
        return self._cache[sku]


# ===========================================================================
# Composite
# ===========================================================================

class Node(ABC):
    """Component: the interface shared by leaves (files) and composites (directories)."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def size(self) -> int: ...

    @abstractmethod
    def iter_files(self) -> Iterator[File]: ...


class File(Node):
    def __init__(self, name: str, size: int) -> None:
        super().__init__(name)
        self._size = size

    @property
    def extension(self) -> str:
        return self.name.rsplit(".", 1)[-1].lower() if "." in self.name else ""

    def size(self) -> int:
        return self._size

    def iter_files(self) -> Iterator[File]:
        yield self


class Directory(Node):
    def __init__(self, name: str, children: list[Node] | None = None) -> None:
        super().__init__(name)
        self.children: list[Node] = list(children or [])

    def add(self, node: Node) -> Node:
        self.children.append(node)
        return node

    def size(self) -> int:
        # The composite does not care whether a child is a file or another directory.
        return sum(child.size() for child in self.children)

    def iter_files(self) -> Iterator[File]:
        for child in self.children:
            yield from child.iter_files()


# ===========================================================================
# Specification
# ===========================================================================

class Spec(ABC):
    """A business rule as an object, combinable with &, | and ~."""

    @abstractmethod
    def is_satisfied_by(self, item: File) -> bool: ...

    def __and__(self, other: Spec) -> Spec:
        return AllOf(self, other)

    def __or__(self, other: Spec) -> Spec:
        return AnyOf(self, other)

    def __invert__(self) -> Spec:
        return Not(self)


class AllOf(Spec):
    def __init__(self, *specs: Spec) -> None:
        self.specs = specs

    def is_satisfied_by(self, item: File) -> bool:
        return all(spec.is_satisfied_by(item) for spec in self.specs)


class AnyOf(Spec):
    def __init__(self, *specs: Spec) -> None:
        self.specs = specs

    def is_satisfied_by(self, item: File) -> bool:
        return any(spec.is_satisfied_by(item) for spec in self.specs)


class Not(Spec):
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def is_satisfied_by(self, item: File) -> bool:
        return not self.spec.is_satisfied_by(item)


class ExtensionIs(Spec):
    def __init__(self, extension: str) -> None:
        self.extension = extension.lower().lstrip(".")

    def is_satisfied_by(self, item: File) -> bool:
        return item.extension == self.extension


class LargerThan(Spec):
    def __init__(self, size: int) -> None:
        self.size = size

    def is_satisfied_by(self, item: File) -> bool:
        return item.size() > self.size


class NameContains(Spec):
    def __init__(self, text: str) -> None:
        self.text = text

    def is_satisfied_by(self, item: File) -> bool:
        return self.text in item.name


def search(root: Node, spec: Spec) -> list[str]:
    return [f.name for f in root.iter_files() if spec.is_satisfied_by(f)]


# Pythonic shortcut: predicates are functions; combine them with small helpers.
Predicate = Callable[[File], bool]


def all_of(*predicates: Predicate) -> Predicate:
    return lambda item: all(p(item) for p in predicates)


def any_of(*predicates: Predicate) -> Predicate:
    return lambda item: any(p(item) for p in predicates)


# ===========================================================================
# Demo
# ===========================================================================

def sample_tree() -> Directory:
    return Directory("project", [
        File("README.md", 2_000),
        Directory("src", [
            File("app.py", 12_000),
            File("utils.py", 800),
            Directory("legacy", [File("old_app.py", 40_000)]),
        ]),
        Directory("assets", [File("logo.png", 90_000), File("notes.txt", 300)]),
    ])


def demo() -> None:
    print("== Adapter ==")
    print("  charged, txn id:", checkout(LegacyBankAdapter(LegacyBankGateway()), Decimal("19.99"), "tok_visa"))

    print("== Facade ==")
    lot = ParkingLotFacade(["A1", "A2"], Decimal("3"))
    ticket = lot.enter("7ABC123", now=0)
    print("  ticket:", ticket, "| fee after 95 min:", lot.exit(ticket.ticket_id, now=95))

    print("== Decorator ==")
    item = AmountOff(PercentOff(Product("olive oil", Decimal("12.50"), 2), Decimal("10")), Decimal("1"))
    print(" ", item.description(), "=>", item.price())

    print("== Proxy ==")
    remote = RemotePriceService({"milk": Decimal("3.49")})
    proxy = CachingPriceProxy(remote)
    proxy.price_of("milk")
    proxy.price_of("milk")
    print("  remote calls after two lookups:", remote.calls)

    print("== Composite ==")
    tree = sample_tree()
    print("  total bytes:", tree.size())

    print("== Specification ==")
    big_python = ExtensionIs("py") & LargerThan(1_000) & ~NameContains("old")
    print("  big python files (not legacy):", search(tree, big_python))


if __name__ == "__main__":
    demo()
