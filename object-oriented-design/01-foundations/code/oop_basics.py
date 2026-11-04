"""From a messy shop script to your first classes, one idea at a time.

Run:  python3 oop_basics.py
"""
from __future__ import annotations

from decimal import Decimal


# ---------------------------------------------------------------------------
# 0. The script before objects: parallel lists that must stay in step
# ---------------------------------------------------------------------------

names = ["mug", "tea", "kettle"]
prices = [Decimal("12.50"), Decimal("4.00"), Decimal("30.00")]
stock = [10, 50, 3]


def sell_by_name(name: str, quantity: int) -> Decimal:
    i = names.index(name)          # position in one list...
    stock[i] -= quantity           # ...is trusted to mean the same in the others
    return prices[i] * quantity


def discontinue(name: str) -> None:
    names.remove(name)             # removes from ONE list; prices and stock
                                   # still hold the old row, so everything after
                                   # it is now misaligned


# ---------------------------------------------------------------------------
# 1. A class is a blueprint; an object is one thing built from it
# ---------------------------------------------------------------------------

class EmptyProduct:
    """The smallest possible class: a name for a new kind of thing."""


# ---------------------------------------------------------------------------
# 2. __init__ sets up attributes; methods are functions that receive self
# ---------------------------------------------------------------------------

class SimpleProduct:
    """First version: data plus one method, no rules yet."""

    def __init__(self, name: str, price: Decimal, stock: int) -> None:
        self.name = name
        self.price = price
        self.stock = stock

    def sell(self, quantity: int) -> Decimal:
        self.stock -= quantity
        return self.price * quantity


class Product:
    """One item the shop sells: its data and the rules for changing it."""

    def __init__(self, name: str, price: Decimal, stock: int = 0) -> None:
        if price < 0:
            raise ValueError("price cannot be negative")
        if stock < 0:
            raise ValueError("stock cannot be negative")
        self.name = name
        self.price = price
        self.stock = stock

    def sell(self, quantity: int) -> Decimal:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if quantity > self.stock:
            raise ValueError(f"only {self.stock} {self.name} left")
        self.stock -= quantity
        return self.price * quantity

    def restock(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.stock += quantity

    def __repr__(self) -> str:
        return f"Product({self.name!r}, {self.price}, stock={self.stock})"


# ---------------------------------------------------------------------------
# 3. Objects working together: an Inventory holds Products by name
# ---------------------------------------------------------------------------

class Inventory:
    """The whole shop's stock. One dict of whole Product objects, so a row
    can never fall out of step with itself."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    def add(self, product: Product) -> None:
        if product.name in self._products:
            raise ValueError(f"{product.name} already listed")
        self._products[product.name] = product

    def sell(self, name: str, quantity: int) -> Decimal:
        return self._find(name).sell(quantity)

    def discontinue(self, name: str) -> None:
        del self._products[name]  # the whole row goes at once

    def stock_value(self) -> Decimal:
        return sum((p.price * p.stock for p in self._products.values()), Decimal("0"))

    def _find(self, name: str) -> Product:
        try:
            return self._products[name]
        except KeyError:
            raise ValueError(f"unknown product {name!r}") from None

    def __len__(self) -> int:
        return len(self._products)


# ---------------------------------------------------------------------------
# 4. Class attributes, alternative constructors and helper functions
# ---------------------------------------------------------------------------

class Coupon:
    """Shows a class attribute, a classmethod and a staticmethod."""

    prefix = "SHOP"                       # class attribute: shared by every coupon

    def __init__(self, code: str, percent_off: int) -> None:
        if not self.is_valid_percent(percent_off):
            raise ValueError("percent_off must be 1..90")
        self.code = code                  # instance attributes: one per coupon
        self.percent_off = percent_off

    @classmethod
    def from_text(cls, text: str) -> Coupon:
        """Alternative constructor: parse 'SHOP-SPRING-15'."""
        prefix, name, percent = text.split("-")
        if prefix != cls.prefix:
            raise ValueError(f"not one of our coupons: {text!r}")
        return cls(name, int(percent))

    @staticmethod
    def is_valid_percent(percent: int) -> bool:
        return 1 <= percent <= 90

    def apply(self, amount: Decimal) -> Decimal:
        return (amount * (100 - self.percent_off) / 100).quantize(Decimal("0.01"))


class BuggyBasket:
    """The shared-mutable-class-attribute trap."""

    items: list[str] = []                 # ONE list, shared by every basket

    def add(self, item: str) -> None:
        self.items.append(item)           # mutates the shared class-level list


class Basket:
    def __init__(self) -> None:
        self.items: list[str] = []        # a fresh list for each basket

    def add(self, item: str) -> None:
        self.items.append(item)


def demo() -> None:
    print("== Parallel lists ==")
    print("sell 2 mugs:", sell_by_name("mug", 2), "| stock:", stock)
    discontinue("mug")
    print("after discontinuing mug: names", names, "prices", prices)
    print("selling 1 tea now charges", sell_by_name("tea", 1), "(the mug's price!)")

    print("\n== One object, step by step ==")
    thing = EmptyProduct()
    thing.name = "anything"               # attributes can be bolted on...
    print(type(thing).__name__, vars(thing), "(...but nothing checks them)")
    mug = Product("mug", Decimal("12.50"), stock=10)
    print("new:", mug)
    print("mug.sell(2) ->", mug.sell(2), "| stock now", mug.stock)
    print("Product.sell(mug, 1) ->", Product.sell(mug, 1), "| stock now", mug.stock)
    try:
        mug.sell(100)
    except ValueError as exc:
        print("refused:", exc)

    print("\n== An inventory of objects ==")
    shop = Inventory()
    for p in (Product("mug", Decimal("12.50"), 10),
              Product("tea", Decimal("4.00"), 50),
              Product("kettle", Decimal("30.00"), 3)):
        shop.add(p)
    shop.discontinue("mug")
    print("after discontinuing mug, 1 tea costs", shop.sell("tea", 1),
          "| products:", len(shop), "| stock value:", shop.stock_value())

    print("\n== Class attributes, classmethod, staticmethod ==")
    c = Coupon.from_text("SHOP-SPRING-15")
    print(c.code, c.percent_off, "->", c.apply(Decimal("40")))
    a, b = BuggyBasket(), BuggyBasket()
    a.add("mug")
    print("buggy: b.items =", b.items, "| fixed:", Basket().items)


if __name__ == "__main__":
    demo()
