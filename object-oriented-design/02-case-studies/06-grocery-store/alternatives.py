"""Competing designs compared in the grocery store post.

Each section is a small, runnable version of one approach so you can see where
it shines and where it breaks. Run `python3 alternatives.py` for a side-by-side demo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from typing import Protocol

from grocery_store import (
    AmountOffEach,
    BuyXGetYFree,
    ForProducts,
    InCategory,
    LineItem,
    PercentOff,
    PricingContext,
    Product,
    Promotion,
    PromotionEngine,
    SoldBy,
    TaxTable,
    to_money,
)

CENT = Decimal("0.01")

# ===========================================================================
# Decision 1: the discount engine
# ===========================================================================


@dataclass
class SimpleItem:
    sku: str
    category: str
    price: Decimal
    qty: int


# --- 1A. Hard-coded if/elif ----------------------------------------------------


def ifelse_discount(item: SimpleItem) -> Decimal:
    """Every promotion is a branch. Changing a promo means editing and redeploying code."""
    line = item.price * item.qty
    if item.sku == "COLA-6" and item.qty >= 3:
        return (item.qty // 3) * item.price          # buy 2 get 1
    elif item.category == "beverages":
        return to_money(line * Decimal("0.10"))      # 10% off beverages
    elif item.sku == "MILK-1G":
        return Decimal("0.50") * item.qty            # 50c off milk
    return Decimal("0")


# --- 1B. One Strategy object per promotion ---------------------------------


class DiscountStrategy(ABC):
    """Strategy pattern: each promotion type is a class; each promo knows its targets."""

    @abstractmethod
    def applies_to(self, item: SimpleItem) -> bool: ...

    @abstractmethod
    def discount(self, item: SimpleItem) -> Decimal: ...


@dataclass
class CategoryPercentStrategy(DiscountStrategy):
    category: str
    percent: Decimal

    def applies_to(self, item: SimpleItem) -> bool:
        return item.category == self.category

    def discount(self, item: SimpleItem) -> Decimal:
        return to_money(item.price * item.qty * self.percent / 100)


@dataclass
class SkuBuyXGetYStrategy(DiscountStrategy):
    sku: str
    buy: int
    get: int

    def applies_to(self, item: SimpleItem) -> bool:
        return item.sku == self.sku

    def discount(self, item: SimpleItem) -> Decimal:
        return (item.qty // (self.buy + self.get)) * self.get * item.price


# Notice the smell: "category + percent" and "sku + buy-x-get-y" are welded together.
# A "category + buy-x-get-y" promo needs a third class -> class explosion (targets x rewards).


def best_strategy_discount(item: SimpleItem, strategies: list[DiscountStrategy]) -> Decimal:
    return max((s.discount(item) for s in strategies if s.applies_to(item)), default=Decimal("0"))


# --- 1C. Composable criterion + reward (the recommended design) -------------


def composable_discount(product: Product, qty: int) -> Decimal:
    """Same promos built from reusable parts in grocery_store.py; any target x any reward."""
    engine = PromotionEngine()
    engine.add(Promotion("B2G1", "Cola buy 2 get 1", ForProducts(frozenset({"COLA-6"})), BuyXGetYFree(2, 1)))
    engine.add(Promotion("BEV10", "Beverages 10%", InCategory("beverages"), PercentOff(Decimal("10"))))
    engine.add(Promotion("CAT-B2G1", "Snacks buy 2 get 1", InCategory("snacks"), BuyXGetYFree(2, 1)))
    order = engine.price([LineItem(1, product, Decimal(qty))], PricingContext(), TaxTable("none", {}))
    return order.savings


# --- 1D. Decorator stacking -------------------------------------------------


class PriceCalc(Protocol):
    def price(self, base: Decimal) -> Decimal: ...


class BasePrice:
    def price(self, base: Decimal) -> Decimal:
        return base


@dataclass
class PercentOffDecorator:
    inner: PriceCalc
    percent: Decimal

    def price(self, base: Decimal) -> Decimal:
        return to_money(self.inner.price(base) * (1 - self.percent / 100))


@dataclass
class AmountOffDecorator:
    inner: PriceCalc
    amount: Decimal

    def price(self, base: Decimal) -> Decimal:
        return max(Decimal("0"), self.inner.price(base) - self.amount)


def decorator_order_matters(base: Decimal) -> tuple[Decimal, Decimal]:
    """$2 off then 10% off vs 10% off then $2 off: same promos, different totals."""
    amount_then_percent = PercentOffDecorator(AmountOffDecorator(BasePrice(), Decimal("2")), Decimal("10"))
    percent_then_amount = AmountOffDecorator(PercentOffDecorator(BasePrice(), Decimal("10")), Decimal("2"))
    return amount_then_percent.price(base), percent_then_amount.price(base)


# ===========================================================================
# Decision 2: how conflicting promotions combine
# ===========================================================================


def stack_best_only(price: Decimal, percents: list[Decimal]) -> Decimal:
    """Only the single best promo applies (what the interview spec asks for)."""
    best = max(percents, default=Decimal("0"))
    return to_money(price * best / 100)


def stack_sequential(price: Decimal, percents: list[Decimal]) -> Decimal:
    """Each promo applies to what the previous ones left (compounding)."""
    remaining = price
    for p in percents:
        remaining -= to_money(remaining * p / 100)
    return price - remaining


def stack_on_original_price(price: Decimal, percents: list[Decimal]) -> Decimal:
    """Every promo uses the original price. Can exceed the price itself: a real bug."""
    return sum((to_money(price * p / 100) for p in percents), Decimal("0"))


# ===========================================================================
# Decision 3: money representation
# ===========================================================================


def float_total(prices: list[str]) -> float:
    # A running total, the way a register adds each scan. (Python 3.12+'s built-in
    # sum() uses compensated summation and can hide this error, so we don't use it.)
    total = 0.0
    for p in prices:
        total += float(p)
    return total


def decimal_total(prices: list[str]) -> Decimal:
    return sum((Decimal(p) for p in prices), Decimal("0"))


def cents_total(prices: list[str]) -> int:
    """Integer minor units (what Stripe-style APIs use). Exact, but rounding is on you."""
    return sum(int(Decimal(p) * 100) for p in prices)


def format_cents(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def rounding_modes(value: str) -> tuple[Decimal, Decimal]:
    """Half-up (typical retail) vs half-even (banker's rounding, Python's default)."""
    d = Decimal(value)
    return d.quantize(CENT, ROUND_HALF_UP), d.quantize(CENT, ROUND_HALF_EVEN)


# ===========================================================================
# Decision 4: catalog vs inventory
# ===========================================================================


@dataclass
class ItemWithStock:
    """Merged design: product facts and stock count live in one object."""

    sku: str
    name: str
    price: Decimal
    stock: int


class MergedStore:
    def __init__(self) -> None:
        self.items: dict[str, ItemWithStock] = {}

    def update_from_head_office(self, sku: str, name: str, price: Decimal) -> None:
        # Head office pushes catalog data with no stock field -- so a naive overwrite wipes stock.
        self.items[sku] = ItemWithStock(sku, name, price, stock=0)


@dataclass
class SplitStore:
    """Separate design: catalog updates can't touch stock, and vice versa."""

    catalog: dict[str, tuple[str, Decimal]] = field(default_factory=dict)
    stock: dict[str, int] = field(default_factory=dict)

    def update_from_head_office(self, sku: str, name: str, price: Decimal) -> None:
        self.catalog[sku] = (name, price)


# ===========================================================================
# Decision 5: receipt generation
# ===========================================================================


@dataclass
class LiveOrder:
    """Receipt as a live view: prints by reading current catalog prices."""

    catalog: dict[str, Decimal]
    skus: list[str]

    def receipt_total(self) -> Decimal:
        return sum((self.catalog[s] for s in self.skus), Decimal("0"))


@dataclass(frozen=True)
class SnapshotReceipt:
    """Receipt as a value object: copied at sale time, never recomputed."""

    lines: tuple[tuple[str, Decimal], ...]

    @property
    def total(self) -> Decimal:
        return sum((p for _, p in self.lines), Decimal("0"))


# ===========================================================================
# Decision 6: weighted items
# ===========================================================================


@dataclass
class IntQtyLine:
    """Quantity as int: can't represent 1.235 kg of bananas at all."""

    price: Decimal
    qty: int

    def total(self) -> Decimal:
        return self.price * self.qty


class PricedThing(ABC):
    @abstractmethod
    def line_total(self) -> Decimal: ...


@dataclass
class CountedItem(PricedThing):
    unit_price: Decimal
    count: int

    def line_total(self) -> Decimal:
        return to_money(self.unit_price * self.count)


@dataclass
class WeighedItem(PricedThing):
    """Subclass per pricing mode: works, but every promo must type-check which kind it got."""

    price_per_kg: Decimal
    kg: Decimal

    def line_total(self) -> Decimal:
        return to_money(self.price_per_kg * self.kg)


def soldby_line_total(product: Product, qty: str) -> Decimal:
    """Recommended: one Product with a SoldBy flag and a Decimal quantity."""
    return LineItem(1, product, Decimal(qty)).extended_price


# ===========================================================================
# Demo
# ===========================================================================


def demo() -> None:
    print("== 1. Discount engine ==")
    cola = SimpleItem("COLA-6", "beverages", Decimal("4.49"), 3)
    print("if/elif           :", ifelse_discount(cola))
    strategies: list[DiscountStrategy] = [
        SkuBuyXGetYStrategy("COLA-6", 2, 1),
        CategoryPercentStrategy("beverages", Decimal("10")),
    ]
    print("strategy (best)   :", best_strategy_discount(cola, strategies))
    cola_p = Product("COLA-6", "Cola", "beverages", Decimal("4.49"))
    chips_p = Product("CHIPS", "Chips", "snacks", Decimal("3.49"))
    print("composable cola x3 :", composable_discount(cola_p, 3))
    print("composable chips x3:", composable_discount(chips_p, 3), "(category + B2G1, no new class)")
    a, b = decorator_order_matters(Decimal("10.00"))
    print(f"decorators on $10 : $2-then-10% = {a}, 10%-then-$2 = {b}")

    print("\n== 2. Combining promos (20% + 15% + 70% on $10) ==")
    pcts = [Decimal("20"), Decimal("15"), Decimal("70")]
    print("best only   :", stack_best_only(Decimal("10.00"), pcts))
    print("sequential  :", stack_sequential(Decimal("10.00"), pcts))
    print("on original :", stack_on_original_price(Decimal("10.00"), pcts), "<- more than the price!")

    print("\n== 3. Money ==")
    prices = ["0.10", "0.20", "0.30"]
    print("float  :", float_total(prices), "== 0.6 ?", float_total(prices) == 0.6)
    print("Decimal:", decimal_total(prices))
    print("cents  :", format_cents(cents_total(prices)))
    print("round 0.125 (half-up, half-even):", rounding_modes("0.125"))

    print("\n== 4. Catalog vs inventory ==")
    merged = MergedStore()
    merged.items["MILK"] = ItemWithStock("MILK", "Milk", Decimal("3.99"), stock=40)
    merged.update_from_head_office("MILK", "Milk", Decimal("4.19"))
    split = SplitStore({"MILK": ("Milk", Decimal("3.99"))}, {"MILK": 40})
    split.update_from_head_office("MILK", "Milk", Decimal("4.19"))
    print("merged stock after price push:", merged.items["MILK"].stock)
    print("split stock after price push :", split.stock["MILK"])

    print("\n== 5. Receipts ==")
    catalog = {"MILK": Decimal("3.99")}
    live = LiveOrder(catalog, ["MILK"])
    snap = SnapshotReceipt((("MILK", catalog["MILK"]),))
    catalog["MILK"] = Decimal("4.19")  # price changes the next morning
    print("live view reprint :", live.receipt_total(), "(wrong: customer paid 3.99)")
    print("snapshot reprint  :", snap.total)

    print("\n== 6. Weighted items ==")
    print("int qty            :", IntQtyLine(Decimal("1.49"), int(Decimal("1.235"))).total(), "(lost the weight)")
    print("WeighedItem class  :", WeighedItem(Decimal("1.49"), Decimal("1.235")).line_total())
    bananas = Product("BAN", "Bananas", "produce", Decimal("1.49"), SoldBy.WEIGHT)
    print("SoldBy + Decimal   :", soldby_line_total(bananas, "1.235"))
    print("AmountOffEach on weight (30c/kg off):",
          AmountOffEach(Decimal("0.30")).discount(LineItem(1, bananas, Decimal("1.235")), Decimal("1.84")))


if __name__ == "__main__":
    demo()
