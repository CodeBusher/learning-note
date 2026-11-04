"""SOLID, one before/after pair per principle.

Run:  python3 oop_solid.py
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol


# ===========================================================================
# S - Single Responsibility: one reason to change per class
# ===========================================================================

class InvoiceServiceBefore:
    """Calculates, formats AND delivers. Finance, design and ops all edit it."""

    def __init__(self) -> None:
        self.outbox: list[tuple[str, str]] = []

    def process(self, customer_email: str, items: list[tuple[str, Decimal, int]]) -> str:
        total = sum((price * qty for _, price, qty in items), Decimal("0"))
        if total > 100:
            total *= Decimal("0.95")  # bulk discount: a finance rule
        lines = [f"{name:<10}{qty:>3} x {price}" for name, price, qty in items]
        text = "\n".join([*lines, f"TOTAL {total:.2f}"])  # a layout rule
        self.outbox.append((customer_email, text))         # a delivery rule
        return text


@dataclass(frozen=True)
class LineItem:
    name: str
    price: Decimal
    quantity: int


class InvoiceCalculator:
    """Changes only when pricing rules change."""

    def total(self, items: list[LineItem]) -> Decimal:
        total = sum((i.price * i.quantity for i in items), Decimal("0"))
        if total > 100:
            total *= Decimal("0.95")
        return total.quantize(Decimal("0.01"))


class InvoiceFormatter:
    """Changes only when the invoice layout changes."""

    def format(self, items: list[LineItem], total: Decimal) -> str:
        lines = [f"{i.name:<10}{i.quantity:>3} x {i.price}" for i in items]
        return "\n".join([*lines, f"TOTAL {total}"])


class InvoiceMailer:
    """Changes only when delivery changes (SMTP -> SES, say)."""

    def __init__(self) -> None:
        self.outbox: list[tuple[str, str]] = []

    def send(self, to: str, body: str) -> None:
        self.outbox.append((to, body))


class InvoiceService:
    """Thin coordinator. Its only job is the order of the steps."""

    def __init__(self, calc: InvoiceCalculator, fmt: InvoiceFormatter, mailer: InvoiceMailer) -> None:
        self.calc, self.fmt, self.mailer = calc, fmt, mailer

    def process(self, to: str, items: list[LineItem]) -> str:
        text = self.fmt.format(items, self.calc.total(items))
        self.mailer.send(to, text)
        return text


# ===========================================================================
# O - Open/Closed: add behaviour by adding code, not editing old code
# ===========================================================================

def shipping_cost_before(carrier: str, weight_kg: Decimal) -> Decimal:
    """Every new carrier means editing (and re-testing) this function."""
    if carrier == "ground":
        return Decimal("5") + weight_kg * Decimal("0.5")
    elif carrier == "air":
        return Decimal("15") + weight_kg * Decimal("2")
    elif carrier == "pickup":
        return Decimal("0")
    raise ValueError(f"unknown carrier {carrier}")


class ShippingRate(Protocol):
    code: str

    def cost(self, weight_kg: Decimal) -> Decimal: ...


@dataclass(frozen=True)
class LinearRate:
    """Covers most carriers: a base fee plus a per-kg fee."""

    code: str
    base: Decimal
    per_kg: Decimal

    def cost(self, weight_kg: Decimal) -> Decimal:
        return self.base + weight_kg * self.per_kg


@dataclass(frozen=True)
class TieredRate:
    """A new kind of pricing, added later without touching anything above."""

    code: str
    tiers: tuple[tuple[Decimal, Decimal], ...]  # (max_kg, price), ascending

    def cost(self, weight_kg: Decimal) -> Decimal:
        for max_kg, price in self.tiers:
            if weight_kg <= max_kg:
                return price
        raise ValueError("too heavy for this carrier")


class ShippingCalculator:
    """Closed for modification: it never mentions a specific carrier."""

    def __init__(self, rates: list[ShippingRate] | None = None) -> None:
        self._rates: dict[str, ShippingRate] = {}
        for r in rates or []:
            self.register(r)

    def register(self, rate: ShippingRate) -> None:
        self._rates[rate.code] = rate

    def cost(self, carrier: str, weight_kg: Decimal) -> Decimal:
        try:
            return self._rates[carrier].cost(weight_kg)
        except KeyError:
            raise ValueError(f"unknown carrier {carrier}") from None


# ===========================================================================
# L - Liskov Substitution: a subtype must keep the parent's promises
# ===========================================================================

class AccountBefore:
    def __init__(self, balance: Decimal = Decimal("0")) -> None:
        self.balance = balance

    def withdraw(self, amount: Decimal) -> None:
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance -= amount


class FixedDepositBefore(AccountBefore):
    """A term deposit cannot be withdrawn early, so it breaks the promise."""

    def withdraw(self, amount: Decimal) -> None:
        raise NotImplementedError("locked until maturity")


def pay_rent_before(account: AccountBefore, rent: Decimal) -> None:
    account.withdraw(rent)  # crashes for one particular subclass


class Account:
    """What every account can do: report a balance."""

    def __init__(self, balance: Decimal = Decimal("0")) -> None:
        self._balance = balance

    @property
    def balance(self) -> Decimal:
        return self._balance


class WithdrawableAccount(Account):
    """Only accounts that can really honour withdraw() promise it."""

    def withdraw(self, amount: Decimal) -> None:
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._balance -= amount


class CheckingAccount(WithdrawableAccount):
    pass


class FixedDeposit(Account):
    """No withdraw() at all, so nobody can be surprised by it."""

    def __init__(self, balance: Decimal, months: int) -> None:
        super().__init__(balance)
        self.months = months


def pay_rent(account: WithdrawableAccount, rent: Decimal) -> None:
    account.withdraw(rent)  # the type checker now rejects a FixedDeposit


def total_assets(accounts: list[Account]) -> Decimal:
    return sum((a.balance for a in accounts), Decimal("0"))


# ===========================================================================
# I - Interface Segregation: no client should depend on methods it never uses
# ===========================================================================

class OfficeDeviceBefore(ABC):
    @abstractmethod
    def print_doc(self, doc: str) -> str: ...

    @abstractmethod
    def scan(self) -> str: ...

    @abstractmethod
    def fax(self, number: str, doc: str) -> str: ...


class CheapPrinterBefore(OfficeDeviceBefore):
    def print_doc(self, doc: str) -> str:
        return f"printed {doc}"

    def scan(self) -> str:
        raise NotImplementedError  # forced to lie about its abilities

    def fax(self, number: str, doc: str) -> str:
        raise NotImplementedError


class Printer(Protocol):
    def print_doc(self, doc: str) -> str: ...


class Scanner(Protocol):
    def scan(self) -> str: ...


class CheapPrinter:
    def print_doc(self, doc: str) -> str:
        return f"printed {doc}"


class MultiFunctionPrinter:
    def print_doc(self, doc: str) -> str:
        return f"printed {doc} (duplex)"

    def scan(self) -> str:
        return "scan.pdf"


def print_payslips(printer: Printer, names: list[str]) -> list[str]:
    """Needs printing only, so it asks for exactly that."""
    return [printer.print_doc(f"payslip-{n}") for n in names]


def archive_contract(scanner: Scanner) -> str:
    return f"archived {scanner.scan()}"


# ===========================================================================
# D - Dependency Inversion: depend on abstractions, inject the details
# ===========================================================================

class SmtpMailer:
    """A low-level detail. Imagine a real network connection in here."""

    def __init__(self, host: str = "smtp.internal") -> None:
        self.host = host
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, subject: str) -> None:
        self.sent.append((to, subject))


class SignupServiceBefore:
    """High-level policy welded to a low-level detail: hard to test or swap."""

    def __init__(self) -> None:
        self.mailer = SmtpMailer()  # the dependency is created, not received
        self.users: list[str] = []

    def register(self, email: str) -> None:
        self.users.append(email)
        self.mailer.send(email, "Welcome!")


class Notifier(Protocol):
    """The abstraction is owned by the high-level code that needs it."""

    def send(self, to: str, subject: str) -> None: ...


@dataclass
class InMemoryNotifier:
    """A test double. Fits Notifier without inheriting anything."""

    sent: list[tuple[str, str]] = field(default_factory=list)

    def send(self, to: str, subject: str) -> None:
        self.sent.append((to, subject))


class SignupService:
    def __init__(self, notifier: Notifier) -> None:
        self.notifier = notifier
        self.users: list[str] = []

    def register(self, email: str) -> None:
        if email in self.users:
            raise ValueError("already registered")
        self.users.append(email)
        self.notifier.send(email, "Welcome!")


def demo() -> None:
    items = [LineItem("keyboard", Decimal("80"), 1), LineItem("cable", Decimal("12"), 2)]
    print("== SRP ==")
    service = InvoiceService(InvoiceCalculator(), InvoiceFormatter(), InvoiceMailer())
    print(service.process("ana@example.com", items))

    print("\n== OCP ==")
    calc = ShippingCalculator([LinearRate("ground", Decimal("5"), Decimal("0.5")),
                               LinearRate("air", Decimal("15"), Decimal("2"))])
    calc.register(TieredRate("locker", ((Decimal("2"), Decimal("3")), (Decimal("10"), Decimal("6")))))
    for carrier in ("ground", "air", "locker"):
        print(f"  {carrier}: {calc.cost(carrier, Decimal('4'))}")

    print("\n== LSP ==")
    try:
        pay_rent_before(FixedDepositBefore(Decimal("5000")), Decimal("900"))
    except NotImplementedError as exc:
        print("  before: substitution blew up ->", exc)
    checking = CheckingAccount(Decimal("2000"))
    pay_rent(checking, Decimal("900"))
    print("  after: rent paid, assets =", total_assets([checking, FixedDeposit(Decimal("5000"), 12)]))

    print("\n== ISP ==")
    print(" ", print_payslips(CheapPrinter(), ["ana", "bo"]))
    print(" ", archive_contract(MultiFunctionPrinter()))

    print("\n== DIP ==")
    fake = InMemoryNotifier()
    signup = SignupService(fake)
    signup.register("cy@example.com")
    print("  notifications captured without a mail server:", fake.sent)


if __name__ == "__main__":
    demo()
