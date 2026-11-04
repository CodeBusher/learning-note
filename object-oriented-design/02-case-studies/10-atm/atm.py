"""ATM system: the recommended object-oriented design.

The ATM is modelled as a small state machine (State pattern) that talks to
three kinds of collaborators through narrow interfaces:

* a ``BankService`` (the card issuer / bank host, faked in memory here),
* hardware devices (card reader, cash dispenser, display), and
* ``CashCassettes``, the ATM's own inventory of banknotes.

Each customer request is a Command object with ``execute`` and ``undo``.
Withdrawals follow "debit first, dispense second, reverse on failure", and
every bank call carries an idempotency key so retries never double-charge.

Run ``python3 atm.py`` for a short demo.
"""

from __future__ import annotations

import hashlib
import hmac
import itertools
import secrets
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Protocol


# ---------------------------------------------------------------------------
# Domain values
# ---------------------------------------------------------------------------


class AccountType(Enum):
    CHECKING = "checking"
    SAVINGS = "savings"


class AuthResult(Enum):
    """What the bank says about a card + PIN pair."""

    APPROVED = "approved"
    WRONG_PIN = "wrong PIN"
    RETAIN_CARD = "retain card"
    INVALID_CARD = "invalid card"


class Status(Enum):
    """Outcome of a financial request (think: ISO 8583 response code)."""

    APPROVED = "approved"
    INSUFFICIENT_FUNDS = "insufficient funds"
    DAILY_LIMIT_EXCEEDED = "daily withdrawal limit exceeded"
    NO_SUCH_ACCOUNT = "no such account"
    INVALID_CARD = "invalid card"
    ALREADY_REVERSED = "already reversed"


@dataclass(frozen=True)
class BankResponse:
    status: Status
    balance: Decimal | None = None

    @property
    def approved(self) -> bool:
        return self.status is Status.APPROVED


class BankUnavailable(Exception):
    """The bank did not answer in time. The request may or may not have been applied."""


# ---------------------------------------------------------------------------
# PIN handling: never store or compare raw PINs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PinRecord:
    """What the bank stores instead of a PIN: a random salt and a keyed digest."""

    salt: bytes
    digest: bytes


class PinVault:
    """Toy stand-in for a hardware security module (HSM).

    The secret key lives only inside this object. Because the digest is an
    HMAC keyed with that secret, a stolen table of PinRecords cannot be
    brute-forced offline, even though a 4-digit PIN has only 10,000 values.
    """

    def __init__(self, secret_key: bytes | None = None) -> None:
        self._key = secret_key or secrets.token_bytes(32)

    def enroll(self, pin: str) -> PinRecord:
        if not (pin.isdigit() and 4 <= len(pin) <= 12):
            raise ValueError("PIN must be 4-12 digits")
        salt = secrets.token_bytes(16)
        return PinRecord(salt, self._digest(pin, salt))

    def verify(self, pin: str, record: PinRecord) -> bool:
        # compare_digest takes the same time whether the first or last byte
        # differs, so response timing leaks nothing about the stored digest.
        return hmac.compare_digest(self._digest(pin, record.salt), record.digest)

    def _digest(self, pin: str, salt: bytes) -> bytes:
        return hmac.new(self._key, salt + pin.encode(), hashlib.sha256).digest()


# ---------------------------------------------------------------------------
# The bank side (issuer host), behind an interface
# ---------------------------------------------------------------------------


class BankService(Protocol):
    """Everything the ATM needs from the bank. A network client would implement this too."""

    def authorize_pin(self, card_number: str, pin: str) -> AuthResult: ...

    def balance(self, card_number: str, account_type: AccountType) -> BankResponse: ...

    def withdraw(
        self, card_number: str, account_type: AccountType, amount: Decimal, key: str
    ) -> BankResponse: ...

    def deposit(
        self, card_number: str, account_type: AccountType, amount: Decimal, key: str
    ) -> BankResponse: ...

    def reverse(self, key: str, amount: Decimal | None = None) -> bool: ...


@dataclass
class Account:
    number: str
    account_type: AccountType
    balance: Decimal = Decimal("0")


@dataclass
class Card:
    number: str
    pin: PinRecord
    accounts: dict[AccountType, str] = field(default_factory=dict)
    failed_pin_attempts: int = 0
    blocked: bool = False


@dataclass
class LedgerEntry:
    """One applied money movement, remembered by its idempotency key."""

    key: str
    card_number: str
    account_number: str
    delta: Decimal  # negative for withdrawals, positive for deposits
    day: date
    reversed_amount: Decimal = Decimal("0")


class InMemoryBank:
    """Deterministic fake of a bank host, good enough to test the ATM against."""

    def __init__(
        self,
        vault: PinVault | None = None,
        daily_limit: Decimal = Decimal("500"),
        max_pin_attempts: int = 3,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._vault = vault or PinVault()
        self._daily_limit = daily_limit
        self._max_pin_attempts = max_pin_attempts
        self._today = today
        self._lock = threading.Lock()
        self._cards: dict[str, Card] = {}
        self._accounts: dict[str, Account] = {}
        self._ledger: dict[str, LedgerEntry] = {}
        self._responses: dict[str, BankResponse] = {}
        self._reversed_before_seen: set[str] = set()
        self._withdrawn: dict[tuple[str, date], Decimal] = {}

    # -- setup -------------------------------------------------------------

    def issue_card(self, card_number: str, pin: str) -> None:
        self._cards[card_number] = Card(card_number, self._vault.enroll(pin))

    def open_account(
        self,
        card_number: str,
        account_type: AccountType,
        account_number: str,
        balance: Decimal = Decimal("0"),
    ) -> None:
        self._accounts[account_number] = Account(account_number, account_type, balance)
        self._cards[card_number].accounts[account_type] = account_number

    def account_balance(self, account_number: str) -> Decimal:
        return self._accounts[account_number].balance

    # -- BankService ---------------------------------------------------------

    def authorize_pin(self, card_number: str, pin: str) -> AuthResult:
        with self._lock:
            card = self._cards.get(card_number)
            if card is None:
                return AuthResult.INVALID_CARD
            if card.blocked:
                return AuthResult.RETAIN_CARD
            if self._vault.verify(pin, card.pin):
                card.failed_pin_attempts = 0
                return AuthResult.APPROVED
            # The try counter lives at the bank, not the ATM, so a thief
            # cannot reset it by walking to another machine.
            card.failed_pin_attempts += 1
            if card.failed_pin_attempts >= self._max_pin_attempts:
                card.blocked = True
                return AuthResult.RETAIN_CARD
            return AuthResult.WRONG_PIN

    def balance(self, card_number: str, account_type: AccountType) -> BankResponse:
        with self._lock:
            account = self._find_account(card_number, account_type)
            if account is None:
                return BankResponse(Status.NO_SUCH_ACCOUNT)
            return BankResponse(Status.APPROVED, account.balance)

    def withdraw(
        self, card_number: str, account_type: AccountType, amount: Decimal, key: str
    ) -> BankResponse:
        return self._apply(card_number, account_type, -amount, key)

    def deposit(
        self, card_number: str, account_type: AccountType, amount: Decimal, key: str
    ) -> BankResponse:
        return self._apply(card_number, account_type, amount, key)

    def reverse(self, key: str, amount: Decimal | None = None) -> bool:
        """Undo all (or part) of an earlier request. Safe to call any number of times."""
        with self._lock:
            entry = self._ledger.get(key)
            if entry is None:
                # The reversal overtook the original request (or the original
                # never arrived). Remember the key so a late original is refused.
                self._reversed_before_seen.add(key)
                return False
            remaining = abs(entry.delta) - entry.reversed_amount
            to_reverse = remaining if amount is None else min(amount, remaining)
            if to_reverse <= 0:
                return False
            account = self._accounts[entry.account_number]
            if entry.delta < 0:
                account.balance += to_reverse
                self._withdrawn[(entry.card_number, entry.day)] -= to_reverse
            else:
                account.balance -= to_reverse
            entry.reversed_amount += to_reverse
            return True

    # -- internals -----------------------------------------------------------

    def _apply(
        self, card_number: str, account_type: AccountType, delta: Decimal, key: str
    ) -> BankResponse:
        if delta == 0:
            raise ValueError("amount must be positive")
        with self._lock:
            if key in self._responses:  # a retry: answer exactly as before
                return self._responses[key]
            response = self._decide(card_number, account_type, delta, key)
            self._responses[key] = response
            return response

    def _decide(
        self, card_number: str, account_type: AccountType, delta: Decimal, key: str
    ) -> BankResponse:
        if key in self._reversed_before_seen:
            return BankResponse(Status.ALREADY_REVERSED)
        card = self._cards.get(card_number)
        if card is None or card.blocked:
            return BankResponse(Status.INVALID_CARD)
        account = self._find_account(card_number, account_type)
        if account is None:
            return BankResponse(Status.NO_SUCH_ACCOUNT)
        today = self._today()
        if delta < 0:
            spent = self._withdrawn.get((card_number, today), Decimal("0"))
            if spent - delta > self._daily_limit:
                return BankResponse(Status.DAILY_LIMIT_EXCEEDED, account.balance)
            if account.balance + delta < 0:
                return BankResponse(Status.INSUFFICIENT_FUNDS, account.balance)
            self._withdrawn[(card_number, today)] = spent - delta
        account.balance += delta
        self._ledger[key] = LedgerEntry(key, card_number, account.number, delta, today)
        return BankResponse(Status.APPROVED, account.balance)

    def _find_account(self, card_number: str, account_type: AccountType) -> Account | None:
        card = self._cards.get(card_number)
        if card is None or account_type not in card.accounts:
            return None
        return self._accounts[card.accounts[account_type]]


# ---------------------------------------------------------------------------
# Hardware interfaces and simple fakes
# ---------------------------------------------------------------------------


class DispenseError(Exception):
    """The dispenser failed. ``notes_presented`` says what actually reached the customer."""

    def __init__(self, message: str, notes_presented: Mapping[int, int] | None = None) -> None:
        super().__init__(message)
        self.notes_presented: dict[int, int] = dict(notes_presented or {})


class CardReader(Protocol):
    def eject(self, card_number: str) -> None: ...

    def retain(self, card_number: str) -> None: ...


class CashDispenser(Protocol):
    def dispense(self, notes: Mapping[int, int]) -> None: ...


class Display(Protocol):
    def show(self, message: str) -> None: ...


class RecordingCardReader:
    """Fake card reader that remembers what happened to each card."""

    def __init__(self) -> None:
        self.ejected: list[str] = []
        self.retained: list[str] = []

    def eject(self, card_number: str) -> None:
        self.ejected.append(card_number)

    def retain(self, card_number: str) -> None:
        self.retained.append(card_number)


class FakeDispenser:
    """Fake dispenser. Set ``jam_after`` to make it fail after presenting that many notes."""

    def __init__(self, jam_after: int | None = None) -> None:
        self.jam_after = jam_after
        self.presented: list[int] = []

    def dispense(self, notes: Mapping[int, int]) -> None:
        handed: dict[int, int] = {}
        for denomination, count in sorted(notes.items(), reverse=True):
            for _ in range(count):
                if self.jam_after is not None and len(self.presented) >= self.jam_after:
                    raise DispenseError("note jam", handed)
                self.presented.append(denomination)
                handed[denomination] = handed.get(denomination, 0) + 1


class RecordingDisplay:
    """Fake screen: keeps every message, optionally echoing to stdout."""

    def __init__(self, echo: bool = False) -> None:
        self.messages: list[str] = []
        self.echo = echo

    def show(self, message: str) -> None:
        self.messages.append(message)
        if self.echo:
            print(f"  [screen] {message}")

    @property
    def last(self) -> str:
        return self.messages[-1] if self.messages else ""


# ---------------------------------------------------------------------------
# Cash inventory and the dispensing algorithm
# ---------------------------------------------------------------------------


class CashCassettes:
    """The banknotes loaded in the ATM, keyed by denomination."""

    def __init__(self, counts: Mapping[int, int]) -> None:
        self._counts = {d: c for d, c in counts.items() if c > 0}

    @property
    def counts(self) -> dict[int, int]:
        return dict(self._counts)

    def total(self) -> int:
        return sum(d * c for d, c in self._counts.items())

    def plan(self, amount: int) -> dict[int, int] | None:
        """Fewest notes that make exactly ``amount`` using only notes we have.

        Dynamic programming over reachable totals: after processing each
        denomination, ``best`` maps every reachable total to the cheapest note
        mix that produces it. Unlike greedy, this never paints itself into a
        corner when a cassette runs low.
        """
        if amount <= 0:
            return None
        best: dict[int, dict[int, int]] = {0: {}}
        for denom in sorted(self._counts, reverse=True):
            usable = min(self._counts[denom], amount // denom)
            nxt: dict[int, dict[int, int]] = {}
            for total, mix in best.items():
                for k in range(usable + 1):
                    value = total + k * denom
                    if value > amount:
                        break
                    candidate = {**mix, denom: k} if k else mix
                    current = nxt.get(value)
                    if current is None or sum(candidate.values()) < sum(current.values()):
                        nxt[value] = candidate
            best = nxt
        return best.get(amount)

    def remove(self, notes: Mapping[int, int]) -> None:
        for denom, count in notes.items():
            if self._counts.get(denom, 0) < count:
                raise ValueError(f"not enough {denom} notes")
        for denom, count in notes.items():
            self._counts[denom] -= count

    def add(self, notes: Mapping[int, int]) -> None:
        for denom, count in notes.items():
            self._counts[denom] = self._counts.get(denom, 0) + count


# ---------------------------------------------------------------------------
# Transactions as Command objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransactionResult:
    ok: bool
    message: str
    balance: Decimal | None = None


class Transaction(ABC):
    """A customer request. Knows how to run itself and how to undo itself."""

    def __init__(self, account_type: AccountType) -> None:
        self.account_type = account_type
        self.key = ""  # assigned by the ATM just before execution

    @abstractmethod
    def execute(self, atm: ATM, card_number: str) -> TransactionResult: ...

    def undo(self, atm: ATM, amount: Decimal | None = None) -> bool:
        """Compensate a completed request by asking the bank to reverse it."""
        return atm.bank.reverse(self.key, amount)


class BalanceInquiry(Transaction):
    def execute(self, atm: ATM, card_number: str) -> TransactionResult:
        response = atm.bank.balance(card_number, self.account_type)
        if not response.approved:
            return TransactionResult(False, f"Declined: {response.status.value}.")
        return TransactionResult(True, f"Available balance: {response.balance}", response.balance)

    def undo(self, atm: ATM, amount: Decimal | None = None) -> bool:
        return False  # a read changes nothing, so there is nothing to undo


class Withdrawal(Transaction):
    def __init__(self, account_type: AccountType, amount: int) -> None:
        super().__init__(account_type)
        self.amount = amount

    def execute(self, atm: ATM, card_number: str) -> TransactionResult:
        # 1. Can this machine physically pay this amount? Ask before touching money.
        notes = atm.cassettes.plan(self.amount)
        if notes is None:
            return TransactionResult(False, f"This ATM cannot dispense {self.amount}.")

        # 2. Debit the account first. The idempotency key makes retries safe.
        amount = Decimal(self.amount)
        try:
            response = atm.bank.withdraw(card_number, self.account_type, amount, self.key)
        except BankUnavailable:
            # We do not know whether the debit happened, so we cancel it
            # (a "timeout reversal"). If it never happened, reverse is a no-op.
            self.undo(atm)
            return TransactionResult(False, "Bank unavailable. You have not been charged.")
        if not response.approved:
            return TransactionResult(False, f"Declined: {response.status.value}.", response.balance)

        # 3. Dispense. If hardware fails, refund whatever did not come out.
        try:
            atm.dispenser.dispense(notes)
        except DispenseError as error:
            atm.cassettes.remove(error.notes_presented)
            paid = sum(d * c for d, c in error.notes_presented.items())
            self.undo(atm, amount - paid)
            return TransactionResult(
                False, f"Dispenser fault. Dispensed {paid}; the rest was returned to your account."
            )
        atm.cassettes.remove(notes)
        return TransactionResult(True, f"Please take your cash: {self.amount}.", response.balance)


class Deposit(Transaction):
    def __init__(self, account_type: AccountType, notes: Mapping[int, int]) -> None:
        super().__init__(account_type)
        self.notes = dict(notes)

    def execute(self, atm: ATM, card_number: str) -> TransactionResult:
        amount = Decimal(sum(d * c for d, c in self.notes.items()))
        if amount <= 0:
            return TransactionResult(False, "No notes detected.")
        try:
            response = atm.bank.deposit(card_number, self.account_type, amount, self.key)
        except BankUnavailable:
            self.undo(atm)
            return TransactionResult(False, "Bank unavailable. Please take your notes back.")
        if not response.approved:
            return TransactionResult(False, f"Declined: {response.status.value}.")
        atm.cassettes.add(self.notes)  # a recycling ATM can pay these notes out again
        return TransactionResult(True, f"Deposited {amount}.", response.balance)


# ---------------------------------------------------------------------------
# Session states (State pattern)
# ---------------------------------------------------------------------------


class ATMState(ABC):
    """One stage of a customer session. Each event is rejected unless a state overrides it."""

    name = "abstract"

    def insert_card(self, atm: ATM, card_number: str) -> None:
        atm.display.show("Please finish the current session first.")

    def enter_pin(self, atm: ATM, pin: str) -> None:
        atm.display.show("Please insert your card.")

    def run(self, atm: ATM, transaction: Transaction) -> TransactionResult | None:
        atm.display.show("Please enter your PIN first.")
        return None

    def eject_card(self, atm: ATM) -> None:
        atm.display.show("There is no card to eject.")


class IdleState(ATMState):
    name = "idle"

    def insert_card(self, atm: ATM, card_number: str) -> None:
        atm.card_number = card_number
        atm.display.show("Please enter your PIN.")
        atm.transition(CardInsertedState())


class CardInsertedState(ATMState):
    name = "card inserted"

    def enter_pin(self, atm: ATM, pin: str) -> None:
        result = atm.bank.authorize_pin(atm.require_card(), pin)
        if result is AuthResult.APPROVED:
            atm.display.show("PIN accepted. Choose a transaction.")
            atm.transition(AuthenticatedState())
        elif result is AuthResult.WRONG_PIN:
            atm.display.show("Incorrect PIN. Please try again.")
        elif result is AuthResult.RETAIN_CARD:
            atm.display.show("Too many incorrect PINs. Your card has been retained.")
            atm.end_session(retain=True)
        else:
            atm.display.show("This card cannot be used.")
            atm.end_session()

    def eject_card(self, atm: ATM) -> None:
        atm.end_session()


class AuthenticatedState(ATMState):
    name = "authenticated"

    def run(self, atm: ATM, transaction: Transaction) -> TransactionResult:
        atm.transition(TransactionState())
        try:
            transaction.key = atm.next_key()
            result = transaction.execute(atm, atm.require_card())
            atm.journal.append((transaction.key, type(transaction).__name__, result))
            atm.display.show(result.message)
            return result
        finally:
            atm.transition(AuthenticatedState())

    def eject_card(self, atm: ATM) -> None:
        atm.end_session()


class TransactionState(ATMState):
    """Money is moving. Every other event must wait."""

    name = "transaction"

    def insert_card(self, atm: ATM, card_number: str) -> None:
        atm.display.show("Please wait, transaction in progress.")

    def enter_pin(self, atm: ATM, pin: str) -> None:
        atm.display.show("Please wait, transaction in progress.")

    def run(self, atm: ATM, transaction: Transaction) -> None:
        atm.display.show("Please wait, transaction in progress.")

    def eject_card(self, atm: ATM) -> None:
        atm.display.show("Please wait, transaction in progress.")


# ---------------------------------------------------------------------------
# The ATM itself: context of the state machine and facade over the hardware
# ---------------------------------------------------------------------------


class ATM:
    """Coordinates one physical machine. Holds state; delegates every event to it."""

    def __init__(
        self,
        atm_id: str,
        bank: BankService,
        cassettes: CashCassettes,
        card_reader: CardReader,
        dispenser: CashDispenser,
        display: Display,
    ) -> None:
        self.atm_id = atm_id
        self.bank = bank
        self.cassettes = cassettes
        self.card_reader = card_reader
        self.dispenser = dispenser
        self.display = display
        self.card_number: str | None = None
        self.journal: list[tuple[str, str, TransactionResult]] = []
        self._state: ATMState = IdleState()
        self._sequence = itertools.count(1)
        # Reentrant: a device callback fired during a transaction runs on the
        # same thread and must reach TransactionState, not deadlock.
        self._lock = threading.RLock()

    @property
    def state(self) -> str:
        return self._state.name

    # -- events from the customer / hardware ---------------------------------

    def insert_card(self, card_number: str) -> None:
        with self._lock:
            self._state.insert_card(self, card_number)

    def enter_pin(self, pin: str) -> None:
        with self._lock:
            self._state.enter_pin(self, pin)

    def check_balance(self, account_type: AccountType) -> TransactionResult | None:
        return self._run(BalanceInquiry(account_type))

    def withdraw(self, account_type: AccountType, amount: int) -> TransactionResult | None:
        return self._run(Withdrawal(account_type, amount))

    def deposit(self, account_type: AccountType, notes: Mapping[int, int]) -> TransactionResult | None:
        return self._run(Deposit(account_type, notes))

    def eject_card(self) -> None:
        with self._lock:
            self._state.eject_card(self)

    # -- helpers used by states and commands ---------------------------------

    def _run(self, transaction: Transaction) -> TransactionResult | None:
        with self._lock:
            return self._state.run(self, transaction)

    def transition(self, state: ATMState) -> None:
        self._state = state

    def require_card(self) -> str:
        if self.card_number is None:
            raise RuntimeError("no card in the reader")
        return self.card_number

    def next_key(self) -> str:
        # Unique per machine, like the trace number an ATM stamps on each message.
        return f"{self.atm_id}-{next(self._sequence):06d}"

    def end_session(self, retain: bool = False) -> None:
        card = self.require_card()
        if retain:
            self.card_reader.retain(card)
        else:
            self.card_reader.eject(card)
            self.display.show("Please take your card.")
        self.card_number = None
        self.transition(IdleState())


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def build_demo_atm(jam_after: int | None = None) -> tuple[ATM, InMemoryBank]:
    bank = InMemoryBank(daily_limit=Decimal("300"))
    bank.issue_card("4000-0001", "2468")
    bank.open_account("4000-0001", AccountType.CHECKING, "CHK-1", Decimal("1000"))
    bank.open_account("4000-0001", AccountType.SAVINGS, "SAV-1", Decimal("50"))
    atm = ATM(
        "ATM-07",
        bank,
        CashCassettes({50: 2, 20: 20}),
        RecordingCardReader(),
        FakeDispenser(jam_after=jam_after),
        RecordingDisplay(echo=True),
    )
    return atm, bank


def demo() -> None:
    print("== A normal session ==")
    atm, bank = build_demo_atm()
    atm.insert_card("4000-0001")
    atm.enter_pin("1111")
    atm.enter_pin("2468")
    atm.check_balance(AccountType.CHECKING)
    atm.withdraw(AccountType.CHECKING, 60)  # three 20s
    atm.withdraw(AccountType.CHECKING, 35)  # no 5s loaded
    atm.withdraw(AccountType.CHECKING, 260)  # over the 300 daily limit
    atm.deposit(AccountType.SAVINGS, {20: 2})
    atm.eject_card()
    print(f"  checking balance now {bank.account_balance('CHK-1')}, cassettes {atm.cassettes.counts}")

    print("\n== The dispenser jams after one note ==")
    atm, bank = build_demo_atm(jam_after=1)
    atm.insert_card("4000-0001")
    atm.enter_pin("2468")
    atm.withdraw(AccountType.CHECKING, 100)
    atm.eject_card()
    print(f"  checking balance now {bank.account_balance('CHK-1')} (only the dispensed 50 was charged)")

    print("\n== Three wrong PINs ==")
    atm, _ = build_demo_atm()
    atm.insert_card("4000-0001")
    for guess in ("0000", "1234", "9999"):
        atm.enter_pin(guess)
    print(f"  state={atm.state!r}, retained cards={atm.card_reader.retained}")


if __name__ == "__main__":
    demo()
