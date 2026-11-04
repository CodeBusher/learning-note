"""Grocery store system: catalog, inventory, promotions, tax and checkout.

The recommended design from the "Design a Grocery Store System" post.
Standard library only; run `python3 grocery_store.py` for a demo.
"""

from __future__ import annotations

import itertools
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

# ---------------------------------------------------------------------------
# Money and quantities
# ---------------------------------------------------------------------------

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def to_money(value: Decimal | int | str) -> Decimal:
    """Round to whole cents, half away from zero (the usual retail rule)."""
    if isinstance(value, float):
        # Decimal(0.1) silently captures the binary error; make callers say what they mean.
        raise TypeError("use Decimal or str for money, never float")
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def to_quantity(value: Decimal | int | str) -> Decimal:
    """Parse a quantity (a count or a weight) without going through float."""
    if isinstance(value, float):
        raise TypeError("use Decimal or str for quantities, never float")
    return Decimal(value)


def allocate(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    """Split `total` across `weights` proportionally, in whole cents.

    Uses the largest-remainder method so the parts always add up to exactly
    `total` -- no cent is created or lost by rounding.
    """
    cents = int(total / CENT)
    weight_sum = sum(weights)
    if weight_sum <= 0:
        raise ValueError("cannot allocate across zero weight")
    raw = [Decimal(cents) * w / weight_sum for w in weights]
    parts = [int(r) for r in raw]  # all values are >= 0, so int() floors
    leftover = cents - sum(parts)
    by_remainder = sorted(range(len(raw)), key=lambda i: raw[i] - parts[i], reverse=True)
    for i in by_remainder[:leftover]:
        parts[i] += 1
    return [Decimal(p) * CENT for p in parts]


# ---------------------------------------------------------------------------
# Errors shown to the cashier
# ---------------------------------------------------------------------------


class GroceryError(Exception):
    """Base class for errors with a cashier-friendly message."""


class UnknownCodeError(GroceryError):
    """The scanned or typed code is not in the catalog."""


class InvalidQuantityError(GroceryError):
    """A quantity or weight that makes no sense for the product."""


class InsufficientStockError(GroceryError):
    """Selling this basket would drive recorded stock below zero."""


class CheckoutStateError(GroceryError):
    """The operation is not allowed in the checkout's current state."""


class PaymentError(GroceryError):
    """A tender that cannot be accepted."""


# ---------------------------------------------------------------------------
# Catalog: what we sell (slow-changing reference data)
# ---------------------------------------------------------------------------


class SoldBy(Enum):
    EACH = "each"
    WEIGHT = "kg"


class TaxClass(Enum):
    GROCERY = "grocery"            # staple food, often exempt or reduced
    PREPARED_FOOD = "prepared"     # hot deli food, often taxed like general goods
    GENERAL = "general"            # soap, batteries, soda in many places


@dataclass(frozen=True)
class Product:
    """A sellable product definition. Immutable: a price change is a new Product."""

    sku: str
    name: str
    category: str
    unit_price: Decimal  # per item, or per kg when sold by weight
    sold_by: SoldBy = SoldBy.EACH
    tax_class: TaxClass = TaxClass.GROCERY

    def __post_init__(self) -> None:
        price = to_money(self.unit_price)
        if price < 0:
            raise ValueError("price cannot be negative")
        object.__setattr__(self, "unit_price", price)


class Catalog:
    """Products by SKU, plus every scannable code (UPC, EAN, PLU) mapped to a SKU."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}
        self._codes: dict[str, str] = {}
        self._lock = threading.Lock()

    def upsert(self, product: Product, codes: Iterable[str] = ()) -> None:
        with self._lock:
            self._products[product.sku] = product
            for code in codes:
                self._codes[code.strip()] = product.sku

    def set_price(self, sku: str, new_price: Decimal | str) -> Product:
        with self._lock:
            updated = replace(self._require(sku), unit_price=to_money(new_price))
            self._products[sku] = updated
            return updated

    def remove(self, sku: str) -> None:
        with self._lock:
            self._require(sku)
            del self._products[sku]
            self._codes = {c: s for c, s in self._codes.items() if s != sku}

    def get(self, sku: str) -> Product:
        with self._lock:
            return self._require(sku)

    def lookup(self, code: str) -> Product:
        """Resolve whatever the cashier scanned or typed: a barcode, a PLU or a SKU."""
        code = code.strip()
        with self._lock:
            sku = self._codes.get(code, code)
            product = self._products.get(sku)
        if product is None:
            raise UnknownCodeError(f"No product for code '{code}'. Re-scan or key it in.")
        return product

    def _require(self, sku: str) -> Product:
        try:
            return self._products[sku]
        except KeyError:
            raise UnknownCodeError(f"Unknown SKU '{sku}'") from None


# ---------------------------------------------------------------------------
# Inventory: how much we have (fast-changing operational data)
# ---------------------------------------------------------------------------


class Inventory:
    """Stock on hand per SKU. Shared by every lane, so every operation takes the lock."""

    def __init__(self, allow_negative: bool = False) -> None:
        # Real stores usually allow negative stock: the item is physically in the
        # customer's hand, so the record is what's wrong. Strict mode is for the interview spec.
        self.allow_negative = allow_negative
        self._on_hand: dict[str, Decimal] = defaultdict(Decimal)
        self._lock = threading.Lock()

    def receive(self, sku: str, quantity: Decimal | int | str) -> Decimal:
        qty = to_quantity(quantity)
        if qty <= 0:
            raise InvalidQuantityError("shipment quantity must be positive")
        with self._lock:
            self._on_hand[sku] += qty
            return self._on_hand[sku]

    def on_hand(self, sku: str) -> Decimal:
        with self._lock:
            return self._on_hand[sku]

    def commit_sale(self, sold: Mapping[str, Decimal]) -> None:
        """Decrement stock for a whole basket, all or nothing."""
        with self._lock:
            if not self.allow_negative:
                short = [sku for sku, qty in sold.items() if self._on_hand[sku] < qty]
                if short:
                    raise InsufficientStockError(f"Not enough stock for: {', '.join(sorted(short))}")
            for sku, qty in sold.items():
                self._on_hand[sku] -= qty


# ---------------------------------------------------------------------------
# Basket lines and pricing context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineItem:
    """One line on the receipt. Holds the Product *as it was when scanned*."""

    line_no: int
    product: Product
    quantity: Decimal  # count, or kg for weighed products

    @property
    def unit_price(self) -> Decimal:
        return self.product.unit_price

    @property
    def extended_price(self) -> Decimal:
        return to_money(self.product.unit_price * self.quantity)


@dataclass(frozen=True)
class PricingContext:
    """Everything outside the basket that can change the price."""

    loyalty_id: str | None = None
    coupons: frozenset[str] = frozenset()
    at: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Promotions: criterion (WHO qualifies) x reward (HOW MUCH they save)
# ---------------------------------------------------------------------------


class Criterion(ABC):
    """Decides whether a line qualifies. Combine with &, | and ~."""

    @abstractmethod
    def matches(self, line: LineItem, ctx: PricingContext) -> bool: ...

    def __and__(self, other: Criterion) -> Criterion:
        return AllOf((self, other))

    def __or__(self, other: Criterion) -> Criterion:
        return AnyOf((self, other))

    def __invert__(self) -> Criterion:
        return Not(self)


@dataclass(frozen=True)
class EveryItem(Criterion):
    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return True


@dataclass(frozen=True)
class ForProducts(Criterion):
    skus: frozenset[str]

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return line.product.sku in self.skus


@dataclass(frozen=True)
class InCategory(Criterion):
    category: str

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return line.product.category == self.category


@dataclass(frozen=True)
class LoyaltyMember(Criterion):
    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return ctx.loyalty_id is not None


@dataclass(frozen=True)
class CouponPresented(Criterion):
    code: str

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return self.code in ctx.coupons


@dataclass(frozen=True)
class AllOf(Criterion):
    parts: tuple[Criterion, ...]

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return all(p.matches(line, ctx) for p in self.parts)


@dataclass(frozen=True)
class AnyOf(Criterion):
    parts: tuple[Criterion, ...]

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return any(p.matches(line, ctx) for p in self.parts)


@dataclass(frozen=True)
class Not(Criterion):
    inner: Criterion

    def matches(self, line: LineItem, ctx: PricingContext) -> bool:
        return not self.inner.matches(line, ctx)


class Reward(ABC):
    """Computes the saving on a line, given the price still payable on it."""

    @abstractmethod
    def discount(self, line: LineItem, payable: Decimal) -> Decimal: ...


@dataclass(frozen=True)
class PercentOff(Reward):
    percent: Decimal

    def discount(self, line: LineItem, payable: Decimal) -> Decimal:
        return to_money(payable * Decimal(self.percent) / 100)


@dataclass(frozen=True)
class AmountOffEach(Reward):
    """A fixed saving per unit (or per kg for weighed items)."""

    amount: Decimal

    def discount(self, line: LineItem, payable: Decimal) -> Decimal:
        return min(payable, to_money(Decimal(self.amount) * line.quantity))


@dataclass(frozen=True)
class BuyXGetYFree(Reward):
    buy: int
    get: int

    def discount(self, line: LineItem, payable: Decimal) -> Decimal:
        if line.product.sold_by is not SoldBy.EACH:
            return ZERO
        free_units = (int(line.quantity) // (self.buy + self.get)) * self.get
        return min(payable, to_money(free_units * line.unit_price))


@dataclass(frozen=True)
class MultiBuyPrice(Reward):
    """'3 for $5': every complete bundle costs `bundle_price`."""

    count: int
    bundle_price: Decimal

    def discount(self, line: LineItem, payable: Decimal) -> Decimal:
        if line.product.sold_by is not SoldBy.EACH:
            return ZERO
        bundles = int(line.quantity) // self.count
        regular = bundles * self.count * line.unit_price
        return min(payable, max(ZERO, to_money(regular - bundles * Decimal(self.bundle_price))))


class Stacking(Enum):
    EXCLUSIVE = "exclusive"  # competes with other exclusive promos; best one per line wins
    STACKABLE = "stackable"  # applied on top, in priority order, to what is still payable


def _in_window(starts: datetime | None, ends: datetime | None, at: datetime) -> bool:
    return (starts is None or starts <= at) and (ends is None or at < ends)


@dataclass(frozen=True)
class Promotion:
    """A line-level promotion: a criterion plus a reward, with a stacking rule."""

    promo_id: str
    name: str
    criterion: Criterion
    reward: Reward
    stacking: Stacking = Stacking.EXCLUSIVE
    priority: int = 100  # lower runs first; also breaks ties between equal discounts
    starts: datetime | None = None
    ends: datetime | None = None

    def is_active(self, at: datetime) -> bool:
        return _in_window(self.starts, self.ends, at)


@dataclass(frozen=True)
class BasketPromotion:
    """An order-level promotion such as '$5 off when you spend $40'."""

    promo_id: str
    name: str
    min_spend: Decimal
    amount_off: Decimal
    criterion: Criterion = EveryItem()  # which lines count toward the spend and share the saving
    priority: int = 100
    starts: datetime | None = None
    ends: datetime | None = None

    def is_active(self, at: datetime) -> bool:
        return _in_window(self.starts, self.ends, at)


# ---------------------------------------------------------------------------
# Pricing results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Adjustment:
    promo_id: str
    description: str
    amount: Decimal  # positive number = money saved


@dataclass(frozen=True)
class PricedLine:
    line: LineItem
    gross: Decimal
    adjustments: tuple[Adjustment, ...] = ()
    basket_share: Decimal = ZERO  # this line's slice of order-level discounts

    @property
    def line_savings(self) -> Decimal:
        return sum((a.amount for a in self.adjustments), ZERO)

    @property
    def net(self) -> Decimal:
        return self.gross - self.line_savings

    @property
    def taxable(self) -> Decimal:
        return self.net - self.basket_share


@dataclass(frozen=True)
class TaxTable:
    """Tax rates for one jurisdiction, keyed by product tax class."""

    jurisdiction: str
    rates: Mapping[TaxClass, Decimal]

    def tax_on(self, lines: Iterable[PricedLine]) -> Decimal:
        by_class: dict[TaxClass, Decimal] = defaultdict(Decimal)
        for pl in lines:
            by_class[pl.line.product.tax_class] += pl.taxable
        # Round once per tax class, not once per line, so many small lines don't drift.
        return sum(
            (to_money(amount * self.rates.get(cls, ZERO)) for cls, amount in by_class.items()),
            ZERO,
        )


@dataclass(frozen=True)
class PricedOrder:
    lines: tuple[PricedLine, ...]
    basket_adjustments: tuple[Adjustment, ...]
    tax: Decimal

    @property
    def subtotal(self) -> Decimal:
        return sum((pl.gross for pl in self.lines), ZERO)

    @property
    def savings(self) -> Decimal:
        line = sum((pl.line_savings for pl in self.lines), ZERO)
        basket = sum((a.amount for a in self.basket_adjustments), ZERO)
        return line + basket

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.savings + self.tax


# ---------------------------------------------------------------------------
# Promotion engine
# ---------------------------------------------------------------------------


class PromotionEngine:
    """Holds the active promotions and prices a whole basket from scratch.

    Policy:
      1. Per line, the single best EXCLUSIVE promotion applies.
      2. STACKABLE line promotions then apply in priority order to what is left.
      3. Basket promotions apply last, in priority order, to the post-line amounts,
         and their savings are allocated back to lines (needed for tax and refunds).
    """

    def __init__(self) -> None:
        self._line_promos: dict[str, Promotion] = {}
        self._basket_promos: dict[str, BasketPromotion] = {}
        self._lock = threading.Lock()

    def add(self, promo: Promotion | BasketPromotion) -> None:
        with self._lock:
            if isinstance(promo, BasketPromotion):
                self._basket_promos[promo.promo_id] = promo
            else:
                self._line_promos[promo.promo_id] = promo

    def remove(self, promo_id: str) -> None:
        with self._lock:
            self._line_promos.pop(promo_id, None)
            self._basket_promos.pop(promo_id, None)

    def price(self, lines: Iterable[LineItem], ctx: PricingContext, tax_table: TaxTable) -> PricedOrder:
        with self._lock:  # take a consistent snapshot, then price without holding the lock
            line_promos = sorted(
                (p for p in self._line_promos.values() if p.is_active(ctx.at)),
                key=lambda p: (p.priority, p.promo_id),
            )
            basket_promos = sorted(
                (p for p in self._basket_promos.values() if p.is_active(ctx.at)),
                key=lambda p: (p.priority, p.promo_id),
            )
        priced = [self._price_line(line, line_promos, ctx) for line in lines]
        priced, basket_adjustments = self._apply_basket(priced, basket_promos, ctx)
        return PricedOrder(tuple(priced), tuple(basket_adjustments), tax_table.tax_on(priced))

    @staticmethod
    def _price_line(line: LineItem, promos: list[Promotion], ctx: PricingContext) -> PricedLine:
        gross = line.extended_price
        payable = gross
        adjustments: list[Adjustment] = []
        matching = [p for p in promos if p.criterion.matches(line, ctx)]

        exclusive = [p for p in matching if p.stacking is Stacking.EXCLUSIVE]
        if exclusive:
            # max() keeps the first of equal values, and the list is already in priority order.
            best, amount = max(
                ((p, min(payable, p.reward.discount(line, payable))) for p in exclusive),
                key=lambda pair: pair[1],
            )
            if amount > 0:
                adjustments.append(Adjustment(best.promo_id, best.name, amount))
                payable -= amount

        for promo in (p for p in matching if p.stacking is Stacking.STACKABLE):
            amount = min(payable, promo.reward.discount(line, payable))
            if amount > 0:
                adjustments.append(Adjustment(promo.promo_id, promo.name, amount))
                payable -= amount

        return PricedLine(line, gross, tuple(adjustments))

    @staticmethod
    def _apply_basket(
        priced: list[PricedLine], promos: list[BasketPromotion], ctx: PricingContext
    ) -> tuple[list[PricedLine], list[Adjustment]]:
        shares: dict[int, Decimal] = defaultdict(Decimal)
        adjustments: list[Adjustment] = []
        for promo in promos:
            eligible = [
                pl for pl in priced
                if promo.criterion.matches(pl.line, ctx) and pl.net - shares[pl.line.line_no] > 0
            ]
            remaining = [pl.net - shares[pl.line.line_no] for pl in eligible]
            base = sum(remaining, ZERO)
            if not eligible or base < to_money(promo.min_spend):
                continue
            amount = min(to_money(promo.amount_off), base)
            for pl, part in zip(eligible, allocate(amount, remaining)):
                shares[pl.line.line_no] += part
            adjustments.append(Adjustment(promo.promo_id, promo.name, amount))
        return [replace(pl, basket_share=shares[pl.line.line_no]) for pl in priced], adjustments


# ---------------------------------------------------------------------------
# Checkout and receipt
# ---------------------------------------------------------------------------


class CheckoutState(Enum):
    SCANNING = "scanning"
    TENDERING = "tendering"  # at least one partial payment taken; basket is frozen
    COMPLETED = "completed"
    VOIDED = "voided"


class TenderType(Enum):
    CASH = "cash"
    CARD = "card"


@dataclass(frozen=True)
class Tender:
    kind: TenderType
    amount: Decimal


@dataclass(frozen=True)
class Receipt:
    """An immutable snapshot of a finished sale. Never recomputed later."""

    receipt_id: str
    store_name: str
    lane: str
    issued_at: datetime
    order: PricedOrder
    tenders: tuple[Tender, ...]
    change: Decimal
    loyalty_id: str | None


def render_text(receipt: Receipt, width: int = 42) -> str:
    """Format a receipt for a thermal printer. Presentation only; no business logic."""

    def row(left: str, right: str = "") -> str:
        return f"{left[: width - len(right) - 1]:<{width - len(right)}}{right}".rstrip()

    o = receipt.order
    out = [
        receipt.store_name.center(width),
        f"Lane {receipt.lane}  {receipt.receipt_id}  {receipt.issued_at:%Y-%m-%d %H:%M}",
        "-" * width,
    ]
    for pl in o.lines:
        p, line = pl.line.product, pl.line
        if p.sold_by is SoldBy.WEIGHT:
            detail = f"  {line.quantity} kg @ {p.unit_price}/kg"
        else:
            detail = f"  {line.quantity} @ {p.unit_price}" if line.quantity != 1 else ""
        out.append(row(p.name, f"{pl.gross}"))
        if detail:
            out.append(row(detail))
        for adj in pl.adjustments:
            out.append(row(f"    {adj.description}", f"-{adj.amount}"))
    for adj in o.basket_adjustments:
        out.append(row(adj.description, f"-{adj.amount}"))
    out += [
        "-" * width,
        row("SUBTOTAL", f"{o.subtotal}"),
        row("YOU SAVED", f"{o.savings}"),
        row("TAX", f"{o.tax}"),
        row("TOTAL", f"{o.total}"),
    ]
    for t in receipt.tenders:
        out.append(row(t.kind.value.upper(), f"{t.amount}"))
    out.append(row("CHANGE", f"{receipt.change}"))
    if receipt.loyalty_id:
        out.append(row(f"Member {receipt.loyalty_id}"))
    return "\n".join(out)


class Checkout:
    """One customer's transaction at one lane. Used by a single cashier thread."""

    def __init__(self, store: GroceryStore, lane: str) -> None:
        self._store = store
        self.lane = lane
        self.state = CheckoutState.SCANNING
        self.receipt: Receipt | None = None
        self._lines: dict[int, LineItem] = {}
        self._line_numbers = itertools.count(1)
        self._ctx = PricingContext()
        self._tenders: list[Tender] = []

    # --- building the basket -------------------------------------------------

    def scan(self, code: str, quantity: int | str | Decimal = 1) -> PricedOrder:
        self._require(CheckoutState.SCANNING)
        product = self._store.catalog.lookup(code)
        if product.sold_by is SoldBy.WEIGHT:
            raise InvalidQuantityError(f"{product.name} is sold by weight: place it on the scale")
        qty = to_quantity(quantity)
        if qty <= 0 or qty != qty.to_integral_value():
            raise InvalidQuantityError(f"Quantity for {product.name} must be a whole number above 0")
        existing = next((ln for ln in self._lines.values() if ln.product.sku == product.sku), None)
        if existing is not None:
            # Keep the product snapshot from the first scan so one basket has one price.
            self._lines[existing.line_no] = replace(existing, quantity=existing.quantity + qty)
        else:
            self._add_line(product, qty)
        return self.current()

    def scan_weighed(
        self, code: str, gross_kg: Decimal | str, tare_kg: Decimal | str = "0"
    ) -> PricedOrder:
        self._require(CheckoutState.SCANNING)
        product = self._store.catalog.lookup(code)
        if product.sold_by is not SoldBy.WEIGHT:
            raise InvalidQuantityError(f"{product.name} is sold per item, not by weight")
        net = to_quantity(gross_kg) - to_quantity(tare_kg)
        if net <= 0:
            raise InvalidQuantityError("Net weight must be above zero; check the scale and tare")
        self._add_line(product, net)  # every weighing is its own line
        return self.current()

    def void_line(self, line_no: int) -> PricedOrder:
        self._require(CheckoutState.SCANNING)
        if self._lines.pop(line_no, None) is None:
            raise CheckoutStateError(f"No line {line_no} to void")
        return self.current()

    def identify_member(self, loyalty_id: str) -> PricedOrder:
        self._require(CheckoutState.SCANNING)
        self._ctx = replace(self._ctx, loyalty_id=loyalty_id)
        return self.current()

    def add_coupon(self, code: str) -> PricedOrder:
        self._require(CheckoutState.SCANNING)
        self._ctx = replace(self._ctx, coupons=self._ctx.coupons | {code})
        return self.current()

    def current(self) -> PricedOrder:
        """Re-price the whole basket. Promotions like 'buy 2 get 1' depend on the whole basket."""
        return self._store.promotions.price(self._lines.values(), self._ctx, self._store.tax_table)

    # --- payment -------------------------------------------------------------

    def amount_due(self) -> Decimal:
        return self.current().total - self._paid()

    def pay(self, kind: TenderType, amount: Decimal | str) -> Receipt | None:
        """Take a tender. Returns the Receipt once the sale is fully paid, else None."""
        self._require(CheckoutState.SCANNING, CheckoutState.TENDERING)
        amount = to_money(amount)
        if amount <= 0:
            raise PaymentError("Tender amount must be positive")
        order = self.current()
        if not order.lines:
            raise CheckoutStateError("Nothing to pay for yet")
        due = order.total - self._paid()
        if kind is TenderType.CARD and amount > due:
            raise PaymentError(f"Card amount {amount} exceeds amount due {due}")

        if amount < due:
            self._tenders.append(Tender(kind, amount))
            self.state = CheckoutState.TENDERING
            return None

        # This tender completes the sale. Commit stock first: if it fails, nothing is recorded.
        sold: dict[str, Decimal] = defaultdict(Decimal)
        for line in self._lines.values():
            sold[line.product.sku] += line.quantity
        self._store.inventory.commit_sale(sold)

        self._tenders.append(Tender(kind, amount))
        self.state = CheckoutState.COMPLETED
        self.receipt = Receipt(
            receipt_id=self._store.next_receipt_id(),
            store_name=self._store.name,
            lane=self.lane,
            issued_at=datetime.now(),
            order=order,
            tenders=tuple(self._tenders),
            change=self._paid() - order.total,
            loyalty_id=self._ctx.loyalty_id,
        )
        return self.receipt

    def void(self) -> None:
        self._require(CheckoutState.SCANNING, CheckoutState.TENDERING)
        self.state = CheckoutState.VOIDED  # partial tenders would be refunded here

    # --- helpers -------------------------------------------------------------

    def _add_line(self, product: Product, qty: Decimal) -> None:
        line_no = next(self._line_numbers)
        self._lines[line_no] = LineItem(line_no, product, qty)

    def _paid(self) -> Decimal:
        return sum((t.amount for t in self._tenders), ZERO)

    def _require(self, *allowed: CheckoutState) -> None:
        if self.state not in allowed:
            raise CheckoutStateError(f"Not allowed while checkout is {self.state.value}")


# ---------------------------------------------------------------------------
# Facade
# ---------------------------------------------------------------------------


class GroceryStore:
    """Facade wiring the modules together; each module is replaceable on its own."""

    def __init__(self, name: str, tax_table: TaxTable, *, allow_negative_stock: bool = False) -> None:
        self.name = name
        self.tax_table = tax_table
        self.catalog = Catalog()
        self.inventory = Inventory(allow_negative=allow_negative_stock)
        self.promotions = PromotionEngine()
        self._receipt_numbers = itertools.count(1)
        self._receipt_lock = threading.Lock()

    def add_product(self, product: Product, *codes: str, stock: Decimal | int | str = 0) -> None:
        self.catalog.upsert(product, codes)
        if to_quantity(stock) > 0:
            self.inventory.receive(product.sku, stock)

    def receive_shipment(self, sku: str, quantity: Decimal | int | str) -> Decimal:
        self.catalog.get(sku)  # reject stock for products we don't sell
        return self.inventory.receive(sku, quantity)

    def add_promotion(self, promo: Promotion | BasketPromotion) -> None:
        self.promotions.add(promo)

    def open_checkout(self, lane: str) -> Checkout:
        return Checkout(self, lane)

    def next_receipt_id(self) -> str:
        with self._receipt_lock:
            return f"R-{next(self._receipt_numbers):06d}"


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def build_demo_store() -> GroceryStore:
    tax = TaxTable(
        "Example County",  # illustrative rates, not any real jurisdiction's
        {TaxClass.GROCERY: Decimal("0"), TaxClass.GENERAL: Decimal("0.0625"),
         TaxClass.PREPARED_FOOD: Decimal("0.07")},
    )
    store = GroceryStore("FreshMart #12", tax)
    store.add_product(Product("MILK-1G", "Whole Milk 1 gal", "dairy", Decimal("3.99")),
                      "041303001714", stock=40)
    store.add_product(Product("BAN", "Bananas", "produce", Decimal("1.49"), SoldBy.WEIGHT),
                      "4011", stock="50")
    store.add_product(Product("COLA-6", "Cola 6-pack", "beverages", Decimal("4.49"),
                              tax_class=TaxClass.GENERAL), "049000028911", stock=24)
    store.add_product(Product("SPARK-W", "Sparkling Water", "beverages", Decimal("1.25"),
                              tax_class=TaxClass.GENERAL), "012000161155", stock=60)
    store.add_product(Product("CHIPS", "Sea Salt Chips", "snacks", Decimal("3.49")),
                      "028400090858", stock=30)

    store.add_promotion(Promotion("P-COLA-B2G1", "Cola buy 2 get 1",
                                  ForProducts(frozenset({"COLA-6"})), BuyXGetYFree(2, 1)))
    store.add_promotion(Promotion("P-BEV-10", "Beverages 10% off",
                                  InCategory("beverages"), PercentOff(Decimal("10"))))
    store.add_promotion(Promotion("P-MILK-MBR", "Member price",
                                  ForProducts(frozenset({"MILK-1G"})) & LoyaltyMember(),
                                  AmountOffEach(Decimal("0.50")), Stacking.STACKABLE))
    store.add_promotion(BasketPromotion("C-SAVE5", "Coupon $5 off $25+", Decimal("25"),
                                        Decimal("5"), CouponPresented("SAVE5")))
    return store


def demo() -> None:
    store = build_demo_store()
    lane = store.open_checkout("3")
    lane.scan("041303001714", 2)               # milk x2
    lane.scan_weighed("4011", "1.335", "0.100")  # bananas, minus the bag
    lane.scan("049000028911", 3)               # cola: buy 2 get 1 beats 10% off
    lane.scan("012000161155", 4)               # sparkling water: only 10% off applies
    lane.scan("028400090858")                  # chips
    lane.identify_member("LOY-4471")
    order = lane.add_coupon("SAVE5")
    print(f"Amount due: {order.total}\n")

    receipt = lane.pay(TenderType.CASH, "30.00")
    assert receipt is not None
    print(render_text(receipt))
    print(f"\nCola left in stock: {store.inventory.on_hand('COLA-6')}")


if __name__ == "__main__":
    demo()
