"""The deep end: how Python's object model actually works.

Descriptors (how @property and methods work), cooperative __init__ in a
diamond, dunder protocols (context managers, iteration, equality/hash),
what @dataclass generates, and __slots__.

Run:  python3 oop_internals.py
"""
from __future__ import annotations

import dataclasses
import inspect
import tracemalloc
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# 1. Descriptors: the machinery behind @property, methods and ORM fields
# ---------------------------------------------------------------------------

class Positive:
    """A reusable validated attribute. A *data descriptor*: it defines
    __get__ and __set__, so it wins over the instance __dict__."""

    def __set_name__(self, owner: type, name: str) -> None:
        # Called once, when the owning class body finishes executing.
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, obj: object | None, objtype: type | None = None) -> Any:
        if obj is None:
            return self                     # accessed on the class itself
        return getattr(obj, self.private_name)

    def __set__(self, obj: object, value: Decimal | int) -> None:
        if value <= 0:
            raise ValueError(f"{self.public_name} must be positive, got {value}")
        setattr(obj, self.private_name, value)


class ShippingBox:
    """Three validated fields from one descriptor class, no copy-paste."""

    width = Positive()
    height = Positive()
    depth = Positive()

    def __init__(self, width: int, height: int, depth: int) -> None:
        self.width, self.height, self.depth = width, height, depth

    @cached_property
    def volume(self) -> int:
        # A non-data descriptor: computed once, then stored in __dict__,
        # which shadows the descriptor on every later lookup.
        print("  (computing volume)")
        return self.width * self.height * self.depth

    def fits(self, other: ShippingBox) -> bool:
        return (self.width <= other.width and self.height <= other.height
                and self.depth <= other.depth)


# ---------------------------------------------------------------------------
# 2. A diamond, cooperative __init__ and **kwargs
# ---------------------------------------------------------------------------

class Device:
    def __init__(self, *, serial: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)          # keep the chain going to object
        self.serial = serial
        self.boot_log: list[str] = ["Device"]


class Printer(Device):
    def __init__(self, *, dpi: int = 300, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dpi = dpi
        self.boot_log.append("Printer")


class Scanner(Device):
    def __init__(self, *, color: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.color = color
        self.boot_log.append("Scanner")


class Copier(Printer, Scanner):
    """Printer and Scanner both inherit Device: a diamond. Device.__init__
    still runs exactly once, because super() follows Copier's MRO."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.boot_log.append("Copier")


# ---------------------------------------------------------------------------
# 3. Dunder protocols: context manager + iteration + equality/hash
# ---------------------------------------------------------------------------

class StockLedger:
    """Quantities per SKU, with all-or-nothing batches via `with`."""

    def __init__(self, **quantities: int) -> None:
        self._qty = dict(quantities)

    def take(self, sku: str, n: int) -> None:
        if self._qty.get(sku, 0) < n:
            raise ValueError(f"not enough {sku}")
        self._qty[sku] -= n

    def batch(self) -> LedgerBatch:
        return LedgerBatch(self)

    def __iter__(self) -> Iterator[tuple[str, int]]:
        return iter(sorted(self._qty.items()))

    def __contains__(self, sku: object) -> bool:
        return self._qty.get(sku, 0) > 0  # type: ignore[arg-type]

    def __len__(self) -> int:
        return sum(1 for _ in self if _[1] > 0)


class LedgerBatch:
    """Context manager: snapshot on enter, roll back on any exception."""

    def __init__(self, ledger: StockLedger) -> None:
        self._ledger = ledger

    def __enter__(self) -> StockLedger:
        self._snapshot = dict(self._ledger._qty)
        return self._ledger

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._ledger._qty = self._snapshot   # undo every take() in the block
        return False                             # never swallow the exception


# ---------------------------------------------------------------------------
# 4. What @dataclass writes for you
# ---------------------------------------------------------------------------

@dataclass
class LineItem:
    sku: str
    quantity: int = 1
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Sku:
    code: str


class HandWrittenLineItem:
    """Roughly what @dataclass generated for LineItem, written out by hand."""

    __match_args__ = ("sku", "quantity", "tags")

    def __init__(self, sku: str, quantity: int = 1, tags: list[str] | None = None) -> None:
        self.sku = sku
        self.quantity = quantity
        self.tags = [] if tags is None else tags

    def __repr__(self) -> str:
        return f"HandWrittenLineItem(sku={self.sku!r}, quantity={self.quantity!r}, tags={self.tags!r})"

    def __eq__(self, other: object) -> bool:
        if other.__class__ is not self.__class__:
            return NotImplemented
        return (self.sku, self.quantity, self.tags) == (other.sku, other.quantity, other.tags)

    __hash__ = None  # type: ignore[assignment]  # eq without frozen -> unhashable


# ---------------------------------------------------------------------------
# 5. __slots__: fixed attribute layout, no per-instance __dict__
# ---------------------------------------------------------------------------

class PointDict:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y


class PointSlots:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y


class PointSlotsChild(PointSlots):
    """Forgot to declare __slots__, so instances get a __dict__ again."""


def bytes_per_instance(cls: type, n: int = 100_000) -> float:
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    objs = [cls(1.0, 2.0) for _ in range(n)]
    after = tracemalloc.take_snapshot()
    tracemalloc.stop()
    used = sum(s.size_diff for s in after.compare_to(before, "filename"))
    del objs
    return used / n


def demo() -> None:
    print("== Descriptors ==")
    box = ShippingBox(30, 20, 10)
    print("box dims stored as:", sorted(vars(box)))
    try:
        box.height = 0
    except ValueError as exc:
        print("refused:", exc)
    print("volume:", box.volume, "| again:", box.volume)
    bound = ShippingBox.fits.__get__(box)   # what box.fits does behind the scenes
    print("methods are descriptors too:", bound.__self__ is box,
          bound(ShippingBox(40, 40, 40)))

    print("\n== Diamond + cooperative super() ==")
    c = Copier(serial="CX-1", dpi=600, color=False)
    print("MRO:", [k.__name__ for k in Copier.__mro__])
    print("init order:", c.boot_log, "| dpi", c.dpi, "| color", c.color)

    print("\n== Context manager + iteration ==")
    ledger = StockLedger(mug=3, tea=1)
    try:
        with ledger.batch() as led:
            led.take("mug", 2)
            led.take("tea", 5)            # fails: the mug take is undone too
    except ValueError as exc:
        print("batch failed:", exc)
    print("after rollback:", list(ledger), "| 'tea' in ledger:", "tea" in ledger)

    print("\n== What @dataclass generated ==")
    print("signature:", inspect.signature(LineItem))
    print("fields:", [f.name for f in dataclasses.fields(LineItem)])
    print("LineItem.__hash__ is None:", LineItem.__hash__ is None,
          "| Sku hashable:", hash(Sku("A1")) == hash(Sku("A1")))
    try:
        Sku("A1").code = "B2"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError as exc:
        print("frozen:", exc)
    match LineItem("mug", 2):
        case LineItem(sku, qty):
            print("pattern matched:", sku, qty)

    print("\n== __slots__ ==")
    for cls in (PointDict, PointSlots, PointSlotsChild):
        print(f"  {cls.__name__:<16} ~{bytes_per_instance(cls):.0f} bytes/instance")
    p = PointSlots(1, 2)
    try:
        p.z = 3  # type: ignore[attr-defined]
    except AttributeError as exc:
        print("  typo protection:", exc)


if __name__ == "__main__":
    demo()
