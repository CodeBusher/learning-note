"""Design a Vending Machine: the recommended solution.

Design summary
--------------
* ``VendingMachine`` is a thin facade and the *context* of the State pattern.
  Every customer action is forwarded to the current ``MachineState`` object.
* States: Idle -> HasCredit -> Dispensing -> Idle, plus OutOfService for
  maintenance.  Illegal actions are rejected by the state, not by scattered ifs.
* Payments are Strategies (``CashPayment``, ``CardPayment``) behind one
  authorize / capture / release interface, the same three-phase shape that real
  cashless readers use.
* Money is always integer cents.  Change is planned with a bounded dynamic
  programme so the machine never promises change its coin tubes cannot pay.
* Hardware (motor + drop sensor, card gateway) sits behind small Protocols so
  the core logic is testable without a physical machine.
"""

from __future__ import annotations

import hmac
import itertools
import threading
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# Money and coins
# ---------------------------------------------------------------------------

def format_cents(cents: int) -> str:
    """Render integer cents as dollars, e.g. 125 -> '$1.25'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


class Coin(Enum):
    """Coins the coin mechanism accepts. The value is the coin's worth in cents."""

    NICKEL = 5
    DIME = 10
    QUARTER = 25
    DOLLAR = 100

    @property
    def cents(self) -> int:
        return self.value


def coins_value(coins: Mapping[Coin, int]) -> int:
    """Total value in cents of a {coin: count} mapping."""
    return sum(coin.cents * count for coin, count in coins.items())


def make_change(amount: int, available: Mapping[int, int]) -> dict[int, int] | None:
    """Fewest coins that sum to ``amount`` using at most ``available[d]`` coins of value d.

    This is a bounded-knapsack dynamic programme.  ``best[s]`` is the fewest-coin
    combination found so far that totals ``s`` cents.  We add one denomination at a
    time; keeping only the best combination per subtotal is safe because the
    denominations still to come do not care *how* a subtotal was reached.

    Returns ``None`` when no combination exists (the caller must refuse the sale).
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")
    best: dict[int, dict[int, int]] = {0: {}}
    for denom, limit in sorted(available.items(), reverse=True):
        if denom <= 0 or limit <= 0:
            continue
        extended = dict(best)
        for subtotal, combo in best.items():
            used = sum(combo.values())
            for k in range(1, limit + 1):
                total = subtotal + k * denom
                if total > amount:
                    break
                current = extended.get(total)
                if current is None or used + k < sum(current.values()):
                    extended[total] = {**combo, denom: k}
        best = extended
    return best.get(amount)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class VendingError(Exception):
    """Base class for every error the machine reports to its display."""


class InvalidStateError(VendingError):
    """The action is not allowed in the machine's current state."""


class UnknownSlotError(VendingError):
    """No slot with that code exists."""


class SoldOutError(VendingError):
    """The selected slot is empty."""


class InsufficientCreditError(VendingError):
    """The customer has not paid enough for the selection."""


class ExactChangeRequiredError(VendingError):
    """The machine cannot pay the change this sale would need."""


class PaymentDeclinedError(VendingError):
    """The card processor refused the authorization."""


class AuthorizationError(VendingError):
    """Wrong service PIN."""


# ---------------------------------------------------------------------------
# Catalogue and inventory
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Product:
    """What an item *is*. Immutable, shared by every slot that stocks it."""

    sku: str
    name: str


@dataclass
class Slot:
    """One physical spiral/column: a product, its selling price and how many units are loaded.

    Price lives here rather than on Product because operators price per machine
    and per position (the same can may cost more in an airport than in a factory).
    """

    code: str
    product: Product
    price_cents: int
    capacity: int
    quantity: int = 0

    def __post_init__(self) -> None:
        if self.price_cents <= 0:
            raise ValueError("price must be positive")
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if not 0 <= self.quantity <= self.capacity:
            raise ValueError("quantity must be between 0 and capacity")

    @property
    def is_sold_out(self) -> bool:
        return self.quantity == 0

    def remove_one(self) -> Product:
        if self.is_sold_out:
            raise SoldOutError(f"{self.code} is sold out")
        self.quantity -= 1
        return self.product

    def restock(self, units: int) -> None:
        if units <= 0:
            raise ValueError("units must be positive")
        if self.quantity + units > self.capacity:
            raise ValueError(
                f"{self.code} holds at most {self.capacity}; has {self.quantity}"
            )
        self.quantity += units


class Inventory:
    """All slots in the machine, looked up by the code the customer types (e.g. 'A1')."""

    def __init__(self) -> None:
        self._slots: dict[str, Slot] = {}

    def add_slot(self, slot: Slot) -> None:
        if slot.code in self._slots:
            raise ValueError(f"slot {slot.code} already exists")
        self._slots[slot.code] = slot

    def remove_slot(self, code: str) -> Slot:
        return self._slots.pop(self.slot(code).code)

    def slot(self, code: str) -> Slot:
        try:
            return self._slots[code]
        except KeyError:
            raise UnknownSlotError(f"no slot {code!r}") from None

    def __iter__(self) -> Iterator[Slot]:
        return iter(sorted(self._slots.values(), key=lambda s: s.code))


class CoinBank:
    """The coin tubes the machine pays change from."""

    def __init__(self, counts: Mapping[Coin, int] | None = None) -> None:
        self._counts: Counter[Coin] = Counter()
        if counts:
            self.deposit(counts)

    def count(self, coin: Coin) -> int:
        return self._counts[coin]

    def total_cents(self) -> int:
        return coins_value(self._counts)

    def deposit(self, coins: Mapping[Coin, int]) -> None:
        for coin, n in coins.items():
            if n < 0:
                raise ValueError("cannot deposit a negative number of coins")
            self._counts[coin] += n

    def withdraw(self, coins: Mapping[Coin, int]) -> None:
        for coin, n in coins.items():
            if self._counts[coin] < n:
                raise ValueError(f"not enough {coin.name} coins in the bank")
        for coin, n in coins.items():
            self._counts[coin] -= n

    def plan_change(
        self, amount: int, extra: Mapping[Coin, int] | None = None
    ) -> Counter[Coin] | None:
        """Coins to return for ``amount``, counting ``extra`` coins as if already in the tubes."""
        pool = Counter(self._counts)
        if extra:
            pool.update(extra)
        by_value = {coin.cents: n for coin, n in pool.items()}
        plan = make_change(amount, by_value)
        if plan is None:
            return None
        return Counter({Coin(value): n for value, n in plan.items()})

    def snapshot(self) -> dict[Coin, int]:
        return {coin: self._counts[coin] for coin in Coin}


# ---------------------------------------------------------------------------
# Payments (Strategy)
# ---------------------------------------------------------------------------

class PaymentMethod(ABC):
    """Strategy for one customer's payment session.

    Three phases, mirroring cashless vending: ``authorize`` reserves the price
    before the motor turns, ``capture`` finalises after the drop sensor confirms
    the vend, ``release`` undoes everything on cancel or failed vend.
    """

    name: str = "abstract"

    def accept_coin(self, coin: Coin) -> None:
        raise InvalidStateError(f"{self.name} session in progress; coins not accepted")

    @abstractmethod
    def credit_cents(self) -> int:
        """How much the customer can spend right now (shown on the display)."""

    @abstractmethod
    def authorize(self, price_cents: int) -> None:
        """Reserve ``price_cents`` or raise a VendingError."""

    @abstractmethod
    def capture(self, price_cents: int) -> Counter[Coin]:
        """Finalise the sale. Returns change coins (empty for card)."""

    @abstractmethod
    def release(self) -> Counter[Coin]:
        """Abort the session. Returns coins to hand back (empty for card)."""


class CashPayment(PaymentMethod):
    """Coins inserted by the customer, with change paid from the machine's CoinBank."""

    name = "cash"

    def __init__(self, bank: CoinBank) -> None:
        self._bank = bank
        self._inserted: Counter[Coin] = Counter()
        self._change_plan: Counter[Coin] | None = None

    def accept_coin(self, coin: Coin) -> None:
        self._inserted[coin] += 1

    def credit_cents(self) -> int:
        return coins_value(self._inserted)

    def authorize(self, price_cents: int) -> None:
        credit = self.credit_cents()
        if credit < price_cents:
            raise InsufficientCreditError(
                f"price {format_cents(price_cents)}, credit {format_cents(credit)}"
            )
        # The customer's own coins can be used to pay their change.
        plan = self._bank.plan_change(credit - price_cents, extra=self._inserted)
        if plan is None:
            raise ExactChangeRequiredError("cannot make change; use exact change")
        self._change_plan = plan

    def capture(self, price_cents: int) -> Counter[Coin]:
        if self._change_plan is None:
            raise InvalidStateError("capture before authorize")
        change = self._change_plan
        self._bank.deposit(self._inserted)
        self._bank.withdraw(change)
        self._inserted, self._change_plan = Counter(), None
        return change

    def release(self) -> Counter[Coin]:
        refund = self._inserted
        self._inserted, self._change_plan = Counter(), None
        return refund


class PaymentGateway(Protocol):
    """What the machine needs from a card processor (via the cashless reader)."""

    def authorize(self, card_token: str, amount_cents: int) -> str: ...
    def capture(self, auth_id: str, amount_cents: int) -> None: ...
    def void(self, auth_id: str) -> None: ...


class CardPayment(PaymentMethod):
    """A tapped card: authorize the exact price, capture only after a confirmed vend."""

    name = "card"

    def __init__(self, gateway: PaymentGateway, card_token: str, session_limit_cents: int) -> None:
        self._gateway = gateway
        self._token = card_token
        self._limit = session_limit_cents
        self._auth_id: str | None = None

    def credit_cents(self) -> int:
        return self._limit

    def authorize(self, price_cents: int) -> None:
        if price_cents > self._limit:
            raise InsufficientCreditError("price exceeds the card session limit")
        self._auth_id = self._gateway.authorize(self._token, price_cents)

    def capture(self, price_cents: int) -> Counter[Coin]:
        if self._auth_id is None:
            raise InvalidStateError("capture before authorize")
        self._gateway.capture(self._auth_id, price_cents)
        self._auth_id = None
        return Counter()

    def release(self) -> Counter[Coin]:
        if self._auth_id is not None:
            self._gateway.void(self._auth_id)
            self._auth_id = None
        return Counter()


class InMemoryGateway:
    """A fake card processor for demos and tests: per-card balances and holds."""

    def __init__(self, balances: Mapping[str, int]) -> None:
        self.balances = dict(balances)
        self.holds: dict[str, tuple[str, int]] = {}
        self._ids = itertools.count(1)

    def authorize(self, card_token: str, amount_cents: int) -> str:
        held = sum(a for t, a in self.holds.values() if t == card_token)
        if self.balances.get(card_token, 0) - held < amount_cents:
            raise PaymentDeclinedError("card declined")
        auth_id = f"auth-{next(self._ids)}"
        self.holds[auth_id] = (card_token, amount_cents)
        return auth_id

    def capture(self, auth_id: str, amount_cents: int) -> None:
        token, held = self.holds.pop(auth_id)
        if amount_cents > held:
            raise PaymentDeclinedError("cannot capture more than authorized")
        self.balances[token] -= amount_cents

    def void(self, auth_id: str) -> None:
        self.holds.pop(auth_id, None)


# ---------------------------------------------------------------------------
# Hardware and telemetry boundaries
# ---------------------------------------------------------------------------

class Dispenser(Protocol):
    """Motor + drop sensor. ``vend`` returns True only if an item was seen falling."""

    def vend(self, slot_code: str) -> bool: ...


class SimulatedDispenser:
    """Pretend hardware. Slots listed in ``jammed`` never drop their item."""

    def __init__(self, jammed: set[str] | None = None) -> None:
        self.jammed = set(jammed or ())
        self.vended: list[str] = []

    def vend(self, slot_code: str) -> bool:
        if slot_code in self.jammed:
            return False
        self.vended.append(slot_code)
        return True


class MachineListener(Protocol):
    """Observer for telemetry: sales, failures, stock levels, service events."""

    def on_event(self, event: str, data: dict[str, Any]) -> None: ...


class TelemetryLog:
    """Collects events in memory; a real one would batch-upload them to the operator's cloud."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def on_event(self, event: str, data: dict[str, Any]) -> None:
        self.events.append((event, data))


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

class TxStatus(Enum):
    COMPLETED = "completed"
    VEND_FAILED = "vend_failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Transaction:
    """Immutable audit record of one customer session."""

    tx_id: int
    status: TxStatus
    method: str
    slot_code: str | None = None
    product_name: str | None = None
    price_cents: int = 0
    returned_cents: int = 0
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class VendResult:
    """What the customer walks away with."""

    product: Product | None
    coins_returned: dict[Coin, int]
    message: str

    @property
    def success(self) -> bool:
        return self.product is not None


# ---------------------------------------------------------------------------
# States (State pattern)
# ---------------------------------------------------------------------------

class MachineState(ABC):
    """One mode of the machine. Every action is rejected unless a state overrides it.

    States hold no data of their own (the machine does), so one shared instance
    of each is enough.
    """

    name: str = "abstract"

    def insert_coin(self, m: VendingMachine, coin: Coin) -> None:
        raise InvalidStateError(f"cannot insert coins while {self.name}")

    def tap_card(self, m: VendingMachine, card_token: str) -> None:
        raise InvalidStateError(f"cannot tap a card while {self.name}")

    def select(self, m: VendingMachine, code: str) -> VendResult:
        raise InvalidStateError(f"cannot select while {self.name}")

    def cancel(self, m: VendingMachine) -> dict[Coin, int]:
        raise InvalidStateError(f"cannot cancel while {self.name}")

    @abstractmethod
    def display(self, m: VendingMachine) -> str:
        """Text for the customer display."""


class IdleState(MachineState):
    name = "idle"

    def insert_coin(self, m: VendingMachine, coin: Coin) -> None:
        m._payment = CashPayment(m._bank)
        m._payment.accept_coin(coin)
        m._set_state(HAS_CREDIT)

    def tap_card(self, m: VendingMachine, card_token: str) -> None:
        if m._gateway is None:
            raise InvalidStateError("this machine has no card reader")
        m._payment = CardPayment(m._gateway, card_token, m._card_session_limit)
        m._set_state(HAS_CREDIT)

    def select(self, m: VendingMachine, code: str) -> VendResult:
        slot = m.inventory.slot(code)
        raise InsufficientCreditError(
            f"{slot.product.name} costs {format_cents(slot.price_cents)}; insert coins or tap card"
        )

    def cancel(self, m: VendingMachine) -> dict[Coin, int]:
        return {}  # nothing to give back; pressing the coin-return lever is harmless

    def display(self, m: VendingMachine) -> str:
        return "INSERT COINS OR TAP CARD"


class HasCreditState(MachineState):
    name = "has credit"

    def insert_coin(self, m: VendingMachine, coin: Coin) -> None:
        assert m._payment is not None
        m._payment.accept_coin(coin)

    def select(self, m: VendingMachine, code: str) -> VendResult:
        assert m._payment is not None
        slot = m.inventory.slot(code)
        if slot.is_sold_out:
            raise SoldOutError(f"{slot.code} is sold out; choose another")
        # May raise InsufficientCredit / ExactChangeRequired / PaymentDeclined.
        # We stay in HasCredit so the customer can add coins, choose again or cancel.
        m._payment.authorize(slot.price_cents)
        m._set_state(DISPENSING)
        return DISPENSING.dispense(m, slot)

    def cancel(self, m: VendingMachine) -> dict[Coin, int]:
        assert m._payment is not None
        refund = m._payment.release()
        m._record(TxStatus.CANCELLED, returned_cents=coins_value(refund))
        m._end_session()
        return dict(refund)

    def display(self, m: VendingMachine) -> str:
        assert m._payment is not None
        if m._payment.name == "card":
            return "CARD READY - MAKE A SELECTION"
        return f"CREDIT {format_cents(m._payment.credit_cents())}"


class DispensingState(MachineState):
    """The motor is turning. Every customer input is rejected until the vend resolves."""

    name = "dispensing"

    def dispense(self, m: VendingMachine, slot: Slot) -> VendResult:
        assert m._payment is not None
        if m._dispenser.vend(slot.code):
            product = slot.remove_one()
            change = m._payment.capture(slot.price_cents)
            m._record(TxStatus.COMPLETED, slot, returned_cents=coins_value(change))
            m._emit("sale", {"slot": slot.code, "price_cents": slot.price_cents,
                             "method": m._payment.name})
            if slot.quantity <= m._low_stock_threshold:
                m._emit("low_stock", {"slot": slot.code, "quantity": slot.quantity})
            m._end_session()
            return VendResult(product, dict(change), f"ENJOY YOUR {product.name.upper()}")

        # Drop sensor saw nothing: never charge for an item the customer didn't get.
        refund = m._payment.release()
        m._record(TxStatus.VEND_FAILED, slot, returned_cents=coins_value(refund))
        m._emit("vend_failed", {"slot": slot.code})
        m._end_session()
        return VendResult(None, dict(refund), "VEND FAILED - PAYMENT RETURNED")

    def display(self, m: VendingMachine) -> str:
        return "DISPENSING..."


class OutOfServiceState(MachineState):
    """Service door open (or a fault). Only admin operations are allowed."""

    name = "out of service"

    def display(self, m: VendingMachine) -> str:
        return "OUT OF SERVICE"


IDLE = IdleState()
HAS_CREDIT = HasCreditState()
DISPENSING = DispensingState()
OUT_OF_SERVICE = OutOfServiceState()


# ---------------------------------------------------------------------------
# The machine (facade + State context)
# ---------------------------------------------------------------------------

class VendingMachine:
    """Entry point for the keypad, coin mech, card reader and service menu.

    It owns the collaborators and the current state, and serialises every
    public call with one lock: the controller is a single physical session,
    and hardware events, telemetry and remote commands may arrive on
    different threads.
    """

    def __init__(
        self,
        *,
        inventory: Inventory | None = None,
        bank: CoinBank | None = None,
        dispenser: Dispenser | None = None,
        gateway: PaymentGateway | None = None,
        service_pin: str = "0000",
        card_session_limit_cents: int = 2_000,
        low_stock_threshold: int = 2,
    ) -> None:
        self.inventory = inventory or Inventory()
        self._bank = bank or CoinBank()
        self._dispenser: Dispenser = dispenser or SimulatedDispenser()
        self._gateway = gateway
        self._service_pin = service_pin
        self._card_session_limit = card_session_limit_cents
        self._low_stock_threshold = low_stock_threshold
        self._state: MachineState = IDLE
        self._payment: PaymentMethod | None = None
        self._history: list[Transaction] = []
        self._listeners: list[MachineListener] = []
        self._tx_ids = itertools.count(1)
        self._lock = threading.RLock()

    # -- customer actions: all delegated to the current state --------------
    def insert_coin(self, coin: Coin) -> None:
        with self._lock:
            self._state.insert_coin(self, coin)

    def tap_card(self, card_token: str) -> None:
        with self._lock:
            self._state.tap_card(self, card_token)

    def select(self, code: str) -> VendResult:
        with self._lock:
            return self._state.select(self, code)

    def cancel(self) -> dict[Coin, int]:
        with self._lock:
            return self._state.cancel(self)

    # -- read-only views ---------------------------------------------------
    @property
    def state_name(self) -> str:
        return self._state.name

    @property
    def display(self) -> str:
        with self._lock:
            return self._state.display(self)

    @property
    def credit_cents(self) -> int:
        with self._lock:
            return self._payment.credit_cents() if self._payment else 0

    def history(self) -> tuple[Transaction, ...]:
        with self._lock:
            return tuple(self._history)

    def coin_levels(self) -> dict[Coin, int]:
        with self._lock:
            return self._bank.snapshot()

    def subscribe(self, listener: MachineListener) -> None:
        self._listeners.append(listener)

    # -- service (admin) operations ----------------------------------------
    def enter_service_mode(self, pin: str) -> None:
        with self._lock:
            if not hmac.compare_digest(pin, self._service_pin):
                self._emit("bad_pin", {})
                raise AuthorizationError("wrong service PIN")
            if self._state is not IDLE:
                raise InvalidStateError("finish or cancel the current sale first")
            self._set_state(OUT_OF_SERVICE)
            self._emit("service_mode", {"open": True})

    def exit_service_mode(self) -> None:
        with self._lock:
            self._require_service()
            self._set_state(IDLE)
            self._emit("service_mode", {"open": False})

    def add_slot(self, slot: Slot) -> None:
        with self._lock:
            self._require_service()
            self.inventory.add_slot(slot)

    def remove_slot(self, code: str) -> Slot:
        with self._lock:
            self._require_service()
            return self.inventory.remove_slot(code)

    def restock(self, code: str, units: int) -> None:
        with self._lock:
            self._require_service()
            self.inventory.slot(code).restock(units)

    def set_price(self, code: str, price_cents: int) -> None:
        with self._lock:
            self._require_service()
            if price_cents <= 0:
                raise ValueError("price must be positive")
            self.inventory.slot(code).price_cents = price_cents

    def load_coins(self, coins: Mapping[Coin, int]) -> None:
        with self._lock:
            self._require_service()
            self._bank.deposit(coins)

    def collect_coins(self, keep: Mapping[Coin, int]) -> int:
        """Empty the tubes down to ``keep`` (the change float). Returns cents collected."""
        with self._lock:
            self._require_service()
            taken = {c: max(0, self._bank.count(c) - keep.get(c, 0)) for c in Coin}
            self._bank.withdraw(taken)
            return coins_value(taken)

    # -- internals used by the states --------------------------------------
    def _set_state(self, state: MachineState) -> None:
        self._state = state

    def _require_service(self) -> None:
        if self._state is not OUT_OF_SERVICE:
            raise InvalidStateError("enter service mode first")

    def _end_session(self) -> None:
        self._payment = None
        self._set_state(IDLE)

    def _record(self, status: TxStatus, slot: Slot | None = None, *, returned_cents: int = 0) -> None:
        assert self._payment is not None
        self._history.append(Transaction(
            tx_id=next(self._tx_ids),
            status=status,
            method=self._payment.name,
            slot_code=slot.code if slot else None,
            product_name=slot.product.name if slot else None,
            price_cents=slot.price_cents if slot and status is TxStatus.COMPLETED else 0,
            returned_cents=returned_cents,
        ))

    def _emit(self, event: str, data: dict[str, Any]) -> None:
        for listener in self._listeners:
            listener.on_event(event, data)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def build_demo_machine() -> tuple[VendingMachine, TelemetryLog, InMemoryGateway, SimulatedDispenser]:
    gateway = InMemoryGateway({"card-alice": 500, "card-bob": 50})
    dispenser = SimulatedDispenser()
    vm = VendingMachine(
        bank=CoinBank({Coin.QUARTER: 4, Coin.DIME: 5, Coin.NICKEL: 2}),
        dispenser=dispenser,
        gateway=gateway,
        service_pin="4321",
    )
    telemetry = TelemetryLog()
    vm.subscribe(telemetry)

    vm.enter_service_mode("4321")
    cola = Product("SKU-COLA", "Cola")
    chips = Product("SKU-CHIPS", "Chips")
    vm.add_slot(Slot("A1", cola, price_cents=125, capacity=10, quantity=3))
    vm.add_slot(Slot("B1", chips, price_cents=90, capacity=8, quantity=1))
    vm.exit_service_mode()
    return vm, telemetry, gateway, dispenser


def demo() -> None:
    vm, telemetry, gateway, dispenser = build_demo_machine()

    def show_coins(coins: Mapping[Coin, int]) -> str:
        if not coins:
            return "none"
        return ", ".join(f"{n}x{c.name.lower()}" for c, n in coins.items() if n)

    print("Display:", vm.display)
    vm.insert_coin(Coin.DOLLAR)
    vm.insert_coin(Coin.QUARTER)
    vm.insert_coin(Coin.QUARTER)
    print("Display:", vm.display)
    result = vm.select("A1")
    print(f"{result.message}; change = {show_coins(result.coins_returned)}")

    try:
        vm.select("B1")
    except VendingError as exc:
        print("Rejected:", exc)

    vm.tap_card("card-alice")
    print("Display:", vm.display)
    result = vm.select("B1")
    print(f"{result.message}; card balance now {format_cents(gateway.balances['card-alice'])}")

    vm.insert_coin(Coin.DOLLAR)
    try:
        vm.select("B1")
    except VendingError as exc:
        print("Rejected:", exc)
    print("Coin return:", show_coins(vm.cancel()))

    dispenser.jammed.add("A1")
    vm.tap_card("card-alice")
    result = vm.select("A1")
    print(f"{result.message}; card balance still {format_cents(gateway.balances['card-alice'])}")

    print("\nTransactions:")
    for tx in vm.history():
        print(f"  #{tx.tx_id} {tx.status.value:<11} {tx.method:<5} "
              f"{tx.slot_code or '-':<3} paid {format_cents(tx.price_cents)}")
    print("Telemetry events:", [name for name, _ in telemetry.events])


if __name__ == "__main__":
    demo()
