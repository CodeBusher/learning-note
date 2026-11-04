"""Class relationships, and why composition usually beats inheritance.

Run:  python3 oop_relationships.py
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


# ---------------------------------------------------------------------------
# The five relationships, in one small online-store model
# ---------------------------------------------------------------------------

class Customer:
    """Lives on its own. Orders merely point at it (association)."""

    def __init__(self, customer_id: str, name: str) -> None:
        self.customer_id = customer_id
        self.name = name


class Employee:
    def __init__(self, name: str) -> None:
        self.name = name


class Team:
    """Aggregation: a team groups employees it did not create and does not
    own. Disband the team and the employees still exist."""

    def __init__(self, name: str, members: list[Employee] | None = None) -> None:
        self.name = name
        self.members = list(members or [])

    def add(self, employee: Employee) -> None:
        self.members.append(employee)


@dataclass(frozen=True)
class OrderLine:
    sku: str
    unit_price: Decimal
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class TaxPolicy(Protocol):
    def tax_for(self, amount: Decimal) -> Decimal: ...


class FlatTax:
    def __init__(self, rate: Decimal) -> None:
        self.rate = rate

    def tax_for(self, amount: Decimal) -> Decimal:
        return (amount * self.rate).quantize(Decimal("0.01"))


class Order:
    """Association to Customer, composition of OrderLines, dependency on
    TaxPolicy (used only as a parameter, never stored)."""

    def __init__(self, order_id: str, customer: Customer) -> None:
        self.order_id = order_id
        self.customer = customer          # association
        self._lines: list[OrderLine] = []  # composition: created and owned here

    def add_line(self, sku: str, unit_price: Decimal, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self._lines.append(OrderLine(sku, unit_price, quantity))

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        return tuple(self._lines)

    def subtotal(self) -> Decimal:
        return sum((line.subtotal for line in self._lines), Decimal("0"))

    def total(self, tax: TaxPolicy) -> Decimal:  # dependency
        sub = self.subtotal()
        return sub + tax.tax_for(sub)


class ExpressOrder(Order):
    """Inheritance (generalization): an ExpressOrder IS-AN Order."""

    FEE = Decimal("9.99")

    def subtotal(self) -> Decimal:
        return super().subtotal() + self.FEE


class InvoiceRenderer(ABC):
    @abstractmethod
    def render(self, order: Order) -> str: ...


class PlainTextInvoice(InvoiceRenderer):
    """Realization: implements the InvoiceRenderer contract."""

    def render(self, order: Order) -> str:
        rows = [f"{l.quantity} x {l.sku} @ {l.unit_price}" for l in order.lines]
        return "\n".join([f"Invoice {order.order_id} for {order.customer.name}", *rows])


# ---------------------------------------------------------------------------
# Fragile base class, example 1: a subclass that relies on self-use
# ---------------------------------------------------------------------------

class TagSet:
    """Base class written by another team. add_many() happens to call add()."""

    def __init__(self) -> None:
        self._tags: set[str] = set()

    def add(self, tag: str) -> None:
        self._tags.add(tag.lower())

    def add_many(self, tags: list[str]) -> None:
        for t in tags:
            self.add(t)

    def __len__(self) -> int:
        return len(self._tags)


class CountingTagSetInherited(TagSet):
    """Wants to count how many add attempts happened. Looks right; is wrong."""

    def __init__(self) -> None:
        super().__init__()
        self.attempts = 0

    def add(self, tag: str) -> None:
        self.attempts += 1
        super().add(tag)

    def add_many(self, tags: list[str]) -> None:
        self.attempts += len(tags)
        super().add_many(tags)  # ...which calls self.add() -> counted twice


class CountingTagSet:
    """Composition: wraps a TagSet and forwards. Immune to how TagSet
    implements add_many internally, because it only uses the public API."""

    def __init__(self, inner: TagSet | None = None) -> None:
        self._inner = inner if inner is not None else TagSet()
        self.attempts = 0

    def add(self, tag: str) -> None:
        self.attempts += 1
        self._inner.add(tag)

    def add_many(self, tags: list[str]) -> None:
        self.attempts += len(tags)
        self._inner.add_many(tags)

    def __len__(self) -> int:
        return len(self._inner)


# ---------------------------------------------------------------------------
# Fragile base class, example 2: subclassing a C-implemented built-in
# ---------------------------------------------------------------------------

class LowerKeyDict(dict):
    """Overrides __setitem__, but dict.__init__ and dict.update skip it."""

    def __setitem__(self, key: str, value: object) -> None:
        super().__setitem__(key.lower(), value)


class LowerKeyUserDict(UserDict):
    """UserDict is written in Python and routes every write through
    __setitem__, so the override is honoured everywhere."""

    def __setitem__(self, key: str, value: object) -> None:
        super().__setitem__(key.lower(), value)


# ---------------------------------------------------------------------------
# Inheritance vs composition vs mixins: exporting a report
# ---------------------------------------------------------------------------

# (a) Inheritance: one subclass per (format x destination) pair.
class ReportExporter:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows


class CsvToMemoryExporter(ReportExporter):
    def export(self) -> str:
        header = ",".join(self.rows[0])
        body = [",".join(str(v) for v in r.values()) for r in self.rows]
        return "\n".join([header, *body])


class JsonToMemoryExporter(ReportExporter):
    def export(self) -> str:
        return json.dumps(self.rows)
# ...CsvToS3Exporter, JsonToS3Exporter, CsvToEmailExporter: N x M classes.


# (b) Composition: two small roles, plugged together at runtime.
class Formatter(Protocol):
    def format(self, rows: list[dict]) -> str: ...


class Destination(Protocol):
    def send(self, name: str, payload: str) -> str: ...


class CsvFormatter:
    def format(self, rows: list[dict]) -> str:
        header = ",".join(rows[0])
        body = [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join([header, *body])


class JsonFormatter:
    def format(self, rows: list[dict]) -> str:
        return json.dumps(rows)


class MemoryDestination:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def send(self, name: str, payload: str) -> str:
        self.files[name] = payload
        return f"memory://{name}"


class Report:
    """N formats + M destinations = N + M classes, any combination."""

    def __init__(self, name: str, formatter: Formatter, destination: Destination) -> None:
        self.name = name
        self.formatter = formatter
        self.destination = destination

    def publish(self, rows: list[dict]) -> str:
        return self.destination.send(self.name, self.formatter.format(rows))


# (c) Mixin: add an orthogonal capability (row counting) to any exporter.
class RowCountMixin:
    def summary(self) -> str:
        return f"{type(self).__name__}: {len(self.rows)} rows"  # type: ignore[attr-defined]


class CountedCsvExporter(RowCountMixin, CsvToMemoryExporter):
    pass


def demo() -> None:
    print("== Relationships ==")
    ana = Customer("c1", "Ana")
    order = ExpressOrder("o-100", ana)
    order.add_line("mug", Decimal("12.50"), 2)
    order.add_line("tea", Decimal("8.00"))
    print(PlainTextInvoice().render(order))
    print("total with 10% tax:", order.total(FlatTax(Decimal("0.10"))))

    team = Team("platform", [Employee("bo"), Employee("cy")])
    survivors = team.members
    del team
    print("employees outlive their team:", [e.name for e in survivors])

    print("\n== Fragile base class ==")
    inherited, composed = CountingTagSetInherited(), CountingTagSet()
    for s in (inherited, composed):
        s.add_many(["python", "ood", "solid"])
        print(f"  {type(s).__name__}: attempts={s.attempts}, size={len(s)}")

    d = LowerKeyDict({"Content-Type": "json"})
    d.update({"X-Trace": "1"})
    d["Accept"] = "*/*"
    print("  dict subclass keys:    ", sorted(d))
    u = LowerKeyUserDict({"Content-Type": "json"})
    u.update({"X-Trace": "1"})
    u["Accept"] = "*/*"
    print("  UserDict subclass keys:", sorted(u))

    print("\n== Inheritance vs composition vs mixin ==")
    rows = [{"day": "mon", "orders": 12}, {"day": "tue", "orders": 9}]
    print(" inheritance:", JsonToMemoryExporter(rows).export())
    dest = MemoryDestination()
    print(" composition:", Report("daily.csv", CsvFormatter(), dest).publish(rows))
    print(" mixin:", CountedCsvExporter(rows).summary())


if __name__ == "__main__":
    demo()
