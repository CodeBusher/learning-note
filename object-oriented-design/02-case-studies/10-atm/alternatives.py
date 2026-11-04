"""Competing designs for the ATM case study, kept runnable so they can be compared.

Decision points:
1. Session states: if/elif on an enum  vs  State pattern (see atm.py).
2. Cash dispensing: greedy  vs  Chain of Responsibility  vs  dynamic programming.
3. Transactions: methods on the ATM  vs  Command objects with execute/undo.
4. Money consistency: dispense-then-debit  vs  debit-then-dispense without
   compensation  vs  debit-then-dispense with reversal (atm.py)  vs  hold-then-capture.

Run ``python3 alternatives.py`` for a side-by-side demo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto

from atm import CashCassettes, DispenseError

# ---------------------------------------------------------------------------
# 1. Session states with an enum and if/elif
# ---------------------------------------------------------------------------


class Phase(Enum):
    IDLE = auto()
    CARD_INSERTED = auto()
    AUTHENTICATED = auto()


class IfElseATM:
    """Every event checks the current phase by hand.

    Fine for three phases; each new phase (out of service, maintenance,
    awaiting deposit envelope...) adds a branch to every method.
    """

    def __init__(self, correct_pin: str) -> None:
        self._correct_pin = correct_pin
        self.phase = Phase.IDLE
        self.messages: list[str] = []

    def insert_card(self) -> None:
        if self.phase is Phase.IDLE:
            self.phase = Phase.CARD_INSERTED
            self.messages.append("Enter PIN")
        else:
            self.messages.append("Busy")

    def enter_pin(self, pin: str) -> None:
        if self.phase is Phase.CARD_INSERTED:
            if pin == self._correct_pin:  # toy only: real code never compares raw PINs
                self.phase = Phase.AUTHENTICATED
                self.messages.append("Choose transaction")
            else:
                self.messages.append("Wrong PIN")
        elif self.phase is Phase.IDLE:
            self.messages.append("Insert card first")
        else:
            self.messages.append("Already authenticated")

    def withdraw(self, amount: int) -> None:
        if self.phase is Phase.AUTHENTICATED:
            self.messages.append(f"Dispensing {amount}")
        elif self.phase is Phase.CARD_INSERTED:
            self.messages.append("Enter PIN first")
        else:
            self.messages.append("Insert card first")

    def eject_card(self) -> None:
        if self.phase is Phase.IDLE:
            self.messages.append("No card")
        else:
            self.phase = Phase.IDLE
            self.messages.append("Card ejected")


# ---------------------------------------------------------------------------
# 2. Cash dispensing
# ---------------------------------------------------------------------------


def greedy_plan(amount: int, counts: Mapping[int, int]) -> dict[int, int] | None:
    """Take as many of the largest note as possible, then move down."""
    plan: dict[int, int] = {}
    remaining = amount
    for denom in sorted(counts, reverse=True):
        take = min(counts[denom], remaining // denom)
        if take:
            plan[denom] = take
            remaining -= take * denom
    return plan if remaining == 0 else None


class NoteHandler:
    """One link in a Chain of Responsibility: pays what it can, passes the rest on."""

    def __init__(self, denomination: int, count: int, successor: NoteHandler | None = None) -> None:
        self.denomination = denomination
        self.count = count
        self.successor = successor

    def handle(self, remaining: int, plan: dict[int, int]) -> int:
        take = min(self.count, remaining // self.denomination)
        if take:
            plan[self.denomination] = take
            remaining -= take * self.denomination
        if remaining and self.successor:
            return self.successor.handle(remaining, plan)
        return remaining


def build_chain(counts: Mapping[int, int]) -> NoteHandler | None:
    chain: NoteHandler | None = None
    for denom in sorted(counts):  # build smallest-last so the chain starts at the largest
        chain = NoteHandler(denom, counts[denom], chain)
    return chain


def chain_plan(amount: int, counts: Mapping[int, int]) -> dict[int, int] | None:
    chain = build_chain(counts)
    plan: dict[int, int] = {}
    if chain is None:
        return None
    return plan if chain.handle(amount, plan) == 0 else None


def dp_plan(amount: int, counts: Mapping[int, int]) -> dict[int, int] | None:
    """The recommended planner from atm.py, wrapped for side-by-side comparison."""
    return CashCassettes(counts).plan(amount)


# ---------------------------------------------------------------------------
# A tiny ledger shared by the transaction and consistency alternatives
# ---------------------------------------------------------------------------


class Unreachable(Exception):
    """The bank timed out."""


@dataclass
class TinyBank:
    balance: Decimal
    fail_next: bool = False
    holds: dict[str, Decimal] = field(default_factory=dict)
    applied: dict[str, Decimal] = field(default_factory=dict)

    def debit(self, key: str, amount: Decimal) -> bool:
        if self.fail_next:
            self.fail_next = False
            raise Unreachable
        if key in self.applied:
            return True  # idempotent replay
        if amount > self.available():
            return False
        self.balance -= amount
        self.applied[key] = amount
        return True

    def credit(self, key: str, amount: Decimal) -> None:
        if key not in self.applied:
            self.balance += amount
            self.applied[key] = -amount

    def reverse(self, key: str) -> None:
        amount = self.applied.pop(key, None)
        if amount is not None:
            self.balance += amount

    # two-phase variant
    def available(self) -> Decimal:
        return self.balance - sum(self.holds.values())

    def hold(self, key: str, amount: Decimal) -> bool:
        if amount > self.available():
            return False
        self.holds[key] = amount
        return True

    def capture(self, key: str) -> None:
        self.balance -= self.holds.pop(key)

    def release(self, key: str) -> None:
        self.holds.pop(key, None)


class JammingDispenser:
    def __init__(self, jam: bool) -> None:
        self.jam = jam
        self.cash_out = Decimal("0")

    def dispense(self, amount: Decimal) -> None:
        if self.jam:
            raise DispenseError("jam")
        self.cash_out += amount


# ---------------------------------------------------------------------------
# 3. Transactions: methods on the ATM vs Command objects
# ---------------------------------------------------------------------------


class MethodsATM:
    """All business rules live in ATM methods. Simple, but the class grows with every feature."""

    def __init__(self, bank: TinyBank) -> None:
        self.bank = bank
        self._seq = 0

    def _key(self) -> str:
        self._seq += 1
        return f"m-{self._seq}"

    def withdraw(self, amount: Decimal) -> bool:
        return self.bank.debit(self._key(), amount)

    def deposit(self, amount: Decimal) -> None:
        self.bank.credit(self._key(), amount)

    # Undo has nowhere natural to live: the caller must remember keys itself.


class Command(ABC):
    def __init__(self, key: str) -> None:
        self.key = key

    @abstractmethod
    def execute(self, bank: TinyBank) -> bool: ...

    def undo(self, bank: TinyBank) -> None:
        bank.reverse(self.key)


class WithdrawCommand(Command):
    def __init__(self, key: str, amount: Decimal) -> None:
        super().__init__(key)
        self.amount = amount

    def execute(self, bank: TinyBank) -> bool:
        return bank.debit(self.key, self.amount)


class DepositCommand(Command):
    def __init__(self, key: str, amount: Decimal) -> None:
        super().__init__(key)
        self.amount = amount

    def execute(self, bank: TinyBank) -> bool:
        bank.credit(self.key, self.amount)
        return True


class CommandJournal:
    """Runs commands and remembers them, so any of them can be reversed later."""

    def __init__(self, bank: TinyBank) -> None:
        self.bank = bank
        self.history: list[Command] = []

    def run(self, command: Command) -> bool:
        ok = command.execute(self.bank)
        if ok:
            self.history.append(command)
        return ok

    def reverse(self, key: str) -> bool:
        for command in self.history:
            if command.key == key:
                command.undo(self.bank)
                self.history.remove(command)
                return True
        return False


# ---------------------------------------------------------------------------
# 4. Consistency between dispensing cash and debiting the account
# ---------------------------------------------------------------------------


def dispense_then_debit(bank: TinyBank, dispenser: JammingDispenser, key: str, amount: Decimal) -> str:
    """WRONG: the cash is gone before we know the bank will pay for it."""
    try:
        dispenser.dispense(amount)
    except DispenseError:
        return "dispense failed"
    try:
        return "ok" if bank.debit(key, amount) else "cash out, but declined: bank loses money"
    except Unreachable:
        return "cash out, bank unreachable: bank may lose money"


def debit_then_dispense_naive(
    bank: TinyBank, dispenser: JammingDispenser, key: str, amount: Decimal
) -> str:
    """WRONG: no compensation, so a jam leaves the customer charged with no cash."""
    if not bank.debit(key, amount):
        return "declined"
    try:
        dispenser.dispense(amount)
    except DispenseError:
        return "charged but no cash: customer loses money"
    return "ok"


def debit_then_dispense_with_reversal(
    bank: TinyBank, dispenser: JammingDispenser, key: str, amount: Decimal
) -> str:
    """Recommended (and what atm.py does): compensate every failure after the debit."""
    try:
        if not bank.debit(key, amount):
            return "declined"
    except Unreachable:
        bank.reverse(key)  # unknown outcome: cancel it; harmless if never applied
        return "bank unreachable, nothing charged"
    try:
        dispenser.dispense(amount)
    except DispenseError:
        bank.reverse(key)
        return "jam, reversed"
    return "ok"


def hold_then_capture(bank: TinyBank, dispenser: JammingDispenser, key: str, amount: Decimal) -> str:
    """Two-phase: reserve funds, dispense, then capture (or release on failure)."""
    if not bank.hold(key, amount):
        return "declined"
    try:
        dispenser.dispense(amount)
    except DispenseError:
        bank.release(key)
        return "jam, hold released"
    bank.capture(key)
    return "ok"


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def demo() -> None:
    print("== 1. if/elif session ==")
    atm = IfElseATM("2468")
    atm.withdraw(20)
    atm.insert_card()
    atm.enter_pin("2468")
    atm.withdraw(20)
    atm.eject_card()
    print("  " + " | ".join(atm.messages))

    print("\n== 2. Dispensing plans (None means 'cannot pay') ==")
    cases = [
        (80, {50: 5, 20: 5, 10: 5}),
        (60, {50: 1, 20: 3}),
        (110, {50: 1, 20: 5}),
        (30, {25: 2, 10: 3}),
    ]
    for amount, counts in cases:
        print(
            f"  {amount:>4} from {counts}: greedy={greedy_plan(amount, counts)}, "
            f"chain={chain_plan(amount, counts)}, dp={dp_plan(amount, counts)}"
        )

    print("\n== 3. Command journal with undo ==")
    bank = TinyBank(Decimal("100"))
    journal = CommandJournal(bank)
    journal.run(WithdrawCommand("t1", Decimal("40")))
    journal.run(DepositCommand("t2", Decimal("10")))
    print(f"  after two commands: {bank.balance}")
    journal.reverse("t1")
    print(f"  after reversing t1: {bank.balance}")

    print("\n== 4. Dispense vs debit ordering when the dispenser jams ==")
    for strategy in (
        dispense_then_debit,
        debit_then_dispense_naive,
        debit_then_dispense_with_reversal,
        hold_then_capture,
    ):
        bank = TinyBank(Decimal("100"))
        outcome = strategy(bank, JammingDispenser(jam=True), "k1", Decimal("40"))
        print(f"  {strategy.__name__:<34} -> {outcome:<45} balance={bank.balance}")

    print("\n== 4b. Same, but the bank times out and the dispenser works ==")
    for strategy in (dispense_then_debit, debit_then_dispense_with_reversal):
        bank = TinyBank(Decimal("100"), fail_next=True)
        dispenser = JammingDispenser(jam=False)
        outcome = strategy(bank, dispenser, "k1", Decimal("40"))
        print(
            f"  {strategy.__name__:<34} -> {outcome:<45} "
            f"balance={bank.balance} cash out={dispenser.cash_out}"
        )


if __name__ == "__main__":
    demo()
