"""Behavioral design patterns, each shown on a small, interview-flavoured scenario.

Patterns in this file:
    Strategy                - parking fees that can be swapped at runtime
                              (starting from the if/elif chain it replaces)
    State                   - a vending machine whose behaviour depends on its status,
                              plus a transition table and a reconcile loop for contrast
    Observer                - an elevator that announces arrivals to displays and loggers
    Command                 - a waiter queueing (and undoing) kitchen orders
    Template Method         - a blackjack turn whose skeleton is fixed but hit/stand varies
    Chain of Responsibility - an ATM handing a withdrawal down a chain of note dispensers
    Iterator                - visiting requested elevator floors in SCAN order

Run ``python3 patterns_behavioral.py`` for a short demo of each.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


# ===========================================================================
# Strategy
# ===========================================================================

def charge_with_if_chain(minutes: int, mode: str) -> Decimal:
    """The "before" picture: every new pricing rule is another branch here."""
    if minutes < 0:
        raise ValueError("duration cannot be negative")
    if mode == "hourly":
        return Decimal("4") * max(1, math.ceil(minutes / 60))
    elif mode == "flat":
        return Decimal("10")
    elif mode == "first_hour_free":
        if minutes <= 60:
            return Decimal("0")
        return Decimal("4") * math.ceil((minutes - 60) / 60)
    else:
        raise ValueError(f"unknown pricing mode {mode!r}")


class PricingStrategy(ABC):
    """An interchangeable algorithm for turning a stay (in minutes) into a fee."""

    @abstractmethod
    def fee(self, minutes: int) -> Decimal:
        """Return the fee for a stay of ``minutes`` minutes."""


class HourlyPricing(PricingStrategy):
    """Charge per started hour, with a one-hour minimum."""

    def __init__(self, rate_per_hour: Decimal) -> None:
        self.rate_per_hour = rate_per_hour

    def fee(self, minutes: int) -> Decimal:
        hours = max(1, math.ceil(minutes / 60))
        return self.rate_per_hour * hours


class FlatRatePricing(PricingStrategy):
    """One price regardless of duration (event parking, weekends)."""

    def __init__(self, flat_fee: Decimal) -> None:
        self.flat_fee = flat_fee

    def fee(self, minutes: int) -> Decimal:
        return self.flat_fee


class FirstHourFreePricing(PricingStrategy):
    """Free grace period, then hourly. Shopping malls love this one."""

    def __init__(self, rate_per_hour: Decimal) -> None:
        self.rate_per_hour = rate_per_hour

    def fee(self, minutes: int) -> Decimal:
        if minutes <= 60:
            return Decimal("0")
        return self.rate_per_hour * math.ceil((minutes - 60) / 60)


class ParkingCheckout:
    """The *context*: it uses a strategy but does not know which one."""

    def __init__(self, strategy: PricingStrategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: PricingStrategy) -> None:
        self._strategy = strategy

    def charge(self, minutes: int) -> Decimal:
        if minutes < 0:
            raise ValueError("duration cannot be negative")
        return self._strategy.fee(minutes)


# The Pythonic shortcut: a strategy is just a callable.
FeeFunction = Callable[[int], Decimal]


def hourly(rate_per_hour: Decimal) -> FeeFunction:
    """Build an hourly fee function (a closure stands in for a strategy object)."""

    def fee(minutes: int) -> Decimal:
        return rate_per_hour * max(1, math.ceil(minutes / 60))

    return fee


def weekend_flat(minutes: int) -> Decimal:
    return Decimal("15")


class FunctionalCheckout:
    """Same context, but the strategy is any function ``int -> Decimal``."""

    def __init__(self, fee: FeeFunction) -> None:
        self.fee = fee

    def charge(self, minutes: int) -> Decimal:
        return self.fee(minutes)


# ===========================================================================
# State
# ===========================================================================

class InvalidAction(Exception):
    """Raised when an action is not allowed in the machine's current state."""


@dataclass
class Slot:
    """One product row in the machine. Prices are in cents (coins are integers)."""

    price: int
    quantity: int


class VendingState(ABC):
    """Base state. Every action is illegal unless a concrete state allows it."""

    name = "abstract"

    def insert_coin(self, machine: VendingMachine, cents: int) -> None:
        raise InvalidAction(f"cannot insert coins while {self.name}")

    def select(self, machine: VendingMachine, product: str) -> int:
        raise InvalidAction(f"cannot select a product while {self.name}")

    def refund(self, machine: VendingMachine) -> int:
        return machine.take_balance()


class IdleState(VendingState):
    name = "idle"

    def insert_coin(self, machine: VendingMachine, cents: int) -> None:
        machine.balance += cents
        machine.state = HAS_MONEY

    def select(self, machine: VendingMachine, product: str) -> int:
        raise InvalidAction("insert money first")


class HasMoneyState(VendingState):
    name = "has_money"

    def insert_coin(self, machine: VendingMachine, cents: int) -> None:
        machine.balance += cents

    def select(self, machine: VendingMachine, product: str) -> int:
        slot = machine.inventory.get(product)
        if slot is None or slot.quantity == 0:
            raise InvalidAction(f"{product!r} is not available")
        if machine.balance < slot.price:
            raise InvalidAction(f"{product!r} costs {slot.price}, balance is {machine.balance}")
        slot.quantity -= 1
        machine.balance -= slot.price
        change = machine.take_balance()
        machine.state = IDLE if machine.has_stock() else SOLD_OUT
        return change

    def refund(self, machine: VendingMachine) -> int:
        machine.state = IDLE
        return machine.take_balance()


class SoldOutState(VendingState):
    name = "sold_out"


# State objects hold no data of their own, so one shared instance each is enough.
IDLE = IdleState()
HAS_MONEY = HasMoneyState()
SOLD_OUT = SoldOutState()


class VendingMachine:
    """The context. It forwards every action to whatever state it is in."""

    def __init__(self, inventory: dict[str, Slot]) -> None:
        self.inventory = inventory
        self.balance = 0
        self.state: VendingState = IDLE if self.has_stock() else SOLD_OUT

    def has_stock(self) -> bool:
        return any(slot.quantity > 0 for slot in self.inventory.values())

    def take_balance(self) -> int:
        amount, self.balance = self.balance, 0
        return amount

    def insert_coin(self, cents: int) -> None:
        if cents <= 0:
            raise ValueError("coin value must be positive")
        self.state.insert_coin(self, cents)

    def select(self, product: str) -> int:
        """Vend ``product`` and return the change in cents."""
        return self.state.select(self, product)

    def refund(self) -> int:
        return self.state.refund(self)


# The lighter alternative: when states differ only in which moves are legal,
# a transition table is enough. It is data, so it can be printed and tested.
TURNSTILE_TRANSITIONS: dict[tuple[str, str], str] = {
    ("locked", "coin"): "unlocked",
    ("locked", "push"): "locked",
    ("unlocked", "push"): "locked",
    ("unlocked", "coin"): "unlocked",
}


def next_state(state: str, event: str) -> str:
    try:
        return TURNSTILE_TRANSITIONS[(state, event)]
    except KeyError:
        raise InvalidAction(f"no transition from {state!r} on {event!r}") from None


# Level-triggered control, as in Kubernetes controllers: instead of reacting
# to each event, compare desired with actual state and emit corrective actions.
def reconcile(desired: dict[str, int], actual: dict[str, int]) -> list[str]:
    """Return the actions that move ``actual`` replica counts toward ``desired``."""
    actions: list[str] = []
    for name in sorted(desired.keys() | actual.keys()):
        want, have = desired.get(name, 0), actual.get(name, 0)
        if have < want:
            actions.append(f"start {want - have} x {name}")
        elif have > want:
            actions.append(f"stop {have - want} x {name}")
    return actions


# ===========================================================================
# Observer
# ===========================================================================

@dataclass(frozen=True)
class ElevatorEvent:
    elevator_id: str
    floor: int
    direction: str  # "up", "down" or "idle"


class ElevatorObserver(Protocol):
    def on_elevator_event(self, event: ElevatorEvent) -> None: ...


class Elevator:
    """The *subject*: it knows only that observers have ``on_elevator_event``."""

    def __init__(self, elevator_id: str, floor: int = 0) -> None:
        self.elevator_id = elevator_id
        self.floor = floor
        self._observers: list[ElevatorObserver] = []

    def subscribe(self, observer: ElevatorObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: ElevatorObserver) -> None:
        self._observers.remove(observer)

    def move_to(self, target: int) -> None:
        step = 1 if target > self.floor else -1
        while self.floor != target:
            self.floor += step
            self._notify(ElevatorEvent(self.elevator_id, self.floor, "up" if step > 0 else "down"))
        self._notify(ElevatorEvent(self.elevator_id, self.floor, "idle"))

    def _notify(self, event: ElevatorEvent) -> None:
        # Iterate over a copy so an observer may unsubscribe while being notified.
        for observer in list(self._observers):
            observer.on_elevator_event(event)


class HallDisplay:
    """Shows the car position on one floor's lobby display."""

    def __init__(self) -> None:
        self.text = ""

    def on_elevator_event(self, event: ElevatorEvent) -> None:
        arrow = {"up": "^", "down": "v", "idle": "-"}[event.direction]
        self.text = f"{event.elevator_id} {arrow} {event.floor}"


class TripLogger:
    """Records every floor passed, e.g. for maintenance analytics."""

    def __init__(self) -> None:
        self.events: list[ElevatorEvent] = []

    def on_elevator_event(self, event: ElevatorEvent) -> None:
        self.events.append(event)


class Signal:
    """Pythonic observer: subscribers are plain callables (cf. Django signals)."""

    def __init__(self) -> None:
        self._handlers: list[Callable[..., None]] = []

    def connect(self, handler: Callable[..., None]) -> Callable[..., None]:
        """Register ``handler``; returns it so ``@signal.connect`` works as a decorator."""
        self._handlers.append(handler)
        return handler

    def disconnect(self, handler: Callable[..., None]) -> None:
        self._handlers.remove(handler)

    def emit(self, *args: object, **kwargs: object) -> None:
        for handler in list(self._handlers):
            handler(*args, **kwargs)

    def emit_robust(self, *args: object, **kwargs: object) -> list[Exception]:
        """Like ``emit``, but one failing handler cannot silence the others."""
        errors: list[Exception] = []
        for handler in list(self._handlers):
            try:
                handler(*args, **kwargs)
            except Exception as exc:  # isolate each subscriber's failure
                errors.append(exc)
        return errors


# ===========================================================================
# Command
# ===========================================================================

class Kitchen:
    """The *receiver*: it knows how to actually do the work."""

    def __init__(self) -> None:
        self.tickets: list[str] = []

    def cook(self, table: int, dish: str) -> None:
        self.tickets.append(f"table {table}: {dish}")

    def cancel(self, table: int, dish: str) -> None:
        self.tickets.remove(f"table {table}: {dish}")


class Command(ABC):
    """A request turned into an object, so it can be queued, logged or undone."""

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


@dataclass
class CookDish(Command):
    kitchen: Kitchen
    table: int
    dish: str

    def execute(self) -> None:
        self.kitchen.cook(self.table, self.dish)

    def undo(self) -> None:
        self.kitchen.cancel(self.table, self.dish)


class Waiter:
    """The *invoker*: it collects commands and decides when to run them."""

    def __init__(self) -> None:
        self.pending: deque[Command] = deque()
        self.history: list[Command] = []

    def take_order(self, command: Command) -> None:
        self.pending.append(command)

    def send_to_kitchen(self) -> int:
        sent = 0
        while self.pending:
            command = self.pending.popleft()
            command.execute()
            self.history.append(command)
            sent += 1
        return sent

    def undo_last(self) -> None:
        if not self.history:
            raise InvalidAction("nothing to undo")
        self.history.pop().undo()


# ===========================================================================
# Template Method
# ===========================================================================

def hand_value(cards: Iterable[int]) -> int:
    """Blackjack value of ranks 1-10 (1 = ace). One ace counts 11 if that doesn't bust."""
    cards = list(cards)
    total = sum(cards)
    if 1 in cards and total + 10 <= 21:
        total += 10
    return total


class BlackjackParticipant(ABC):
    """``play_turn`` is the template method: a fixed skeleton with one abstract step."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.cards: list[int] = []
        self.busted = False

    def play_turn(self, draw: Callable[[], int]) -> int:
        while True:
            total = hand_value(self.cards)
            if total > 21:
                self.busted = True
                self.on_bust()
                return total
            if not self.should_hit(total):
                return total
            self.cards.append(draw())

    @abstractmethod
    def should_hit(self, total: int) -> bool:
        """The step subclasses must supply."""

    def on_bust(self) -> None:
        """A *hook*: optional step with a do-nothing default."""


class Dealer(BlackjackParticipant):
    """House rule: hit until 17 or more."""

    def should_hit(self, total: int) -> bool:
        return total < 17


class CautiousPlayer(BlackjackParticipant):
    """Stands early to avoid busting."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.messages: list[str] = []

    def should_hit(self, total: int) -> bool:
        return total < 12

    def on_bust(self) -> None:
        self.messages.append(f"{self.name} busts!")


# ===========================================================================
# Chain of Responsibility
# ===========================================================================

class InsufficientCash(Exception):
    """The ATM cannot make the requested amount from the notes it holds."""


class NoteDispenser:
    """One link in the chain: pays what it can in its denomination, passes on the rest."""

    def __init__(self, denomination: int, count: int) -> None:
        self.denomination = denomination
        self.count = count
        self.next: NoteDispenser | None = None

    def set_next(self, handler: NoteDispenser) -> NoteDispenser:
        self.next = handler
        return handler  # returning the next link lets callers write a.set_next(b).set_next(c)

    def plan(self, amount: int, plan: dict[int, int]) -> int:
        """Fill ``plan`` with notes to use; return the amount nobody could cover."""
        notes = min(amount // self.denomination, self.count)
        if notes:
            plan[self.denomination] = notes
        remaining = amount - notes * self.denomination
        if remaining and self.next is not None:
            return self.next.plan(remaining, plan)
        return remaining


class CashDispenser:
    """Builds the chain from largest to smallest note; plans first, then commits."""

    def __init__(self, cassettes: dict[int, int]) -> None:
        links = [NoteDispenser(d, n) for d, n in sorted(cassettes.items(), reverse=True)]
        for current, nxt in zip(links, links[1:]):
            current.set_next(nxt)
        self._links = {link.denomination: link for link in links}
        self._head = links[0]

    def withdraw(self, amount: int) -> dict[int, int]:
        if amount <= 0:
            raise ValueError("amount must be positive")
        plan: dict[int, int] = {}
        if self._head.plan(amount, plan) != 0:
            raise InsufficientCash(f"cannot dispense {amount} with the notes available")
        for denomination, notes in plan.items():  # commit only once the whole plan works
            self._links[denomination].count -= notes
        return plan

    def notes_left(self) -> dict[int, int]:
        return {d: link.count for d, link in self._links.items()}


# ===========================================================================
# Iterator
# ===========================================================================

class ScanRoute:
    """Iterable over requested floors in SCAN ("elevator algorithm") order.

    Keep going in the current direction, serving every request on the way,
    then reverse and serve the rest. ``__iter__`` is a generator, which is the
    idiomatic way to write an iterator in Python.
    """

    def __init__(self, current_floor: int, requests: Iterable[int], going_up: bool = True) -> None:
        self.current_floor = current_floor
        self.requests = set(requests)
        self.going_up = going_up

    def __iter__(self) -> Iterator[int]:
        above = sorted(f for f in self.requests if f >= self.current_floor)
        below = sorted((f for f in self.requests if f < self.current_floor), reverse=True)
        if self.going_up:
            yield from above
            yield from below
        else:
            yield from below
            yield from above


class ExplicitScanIterator:
    """The same traversal written the long way, with ``__next__`` and saved state."""

    def __init__(self, route: ScanRoute) -> None:
        self._order = list(iter(route))
        self._index = 0

    def __iter__(self) -> ExplicitScanIterator:
        return self

    def __next__(self) -> int:
        if self._index >= len(self._order):
            raise StopIteration
        floor = self._order[self._index]
        self._index += 1
        return floor


# ===========================================================================
# Demo
# ===========================================================================

def demo() -> None:
    print("== Strategy ==")
    print("  if-chain, first hour free, 130 min:", charge_with_if_chain(130, "first_hour_free"))
    checkout = ParkingCheckout(HourlyPricing(Decimal("4")))
    print("  hourly, 130 min:", checkout.charge(130))
    checkout.set_strategy(FirstHourFreePricing(Decimal("4")))
    print("  first hour free, 130 min:", checkout.charge(130))
    print("  functional weekend flat:", FunctionalCheckout(weekend_flat).charge(600))

    print("== State ==")
    machine = VendingMachine({"cola": Slot(price=125, quantity=1)})
    machine.insert_coin(100)
    machine.insert_coin(50)
    print("  state after coins:", machine.state.name)
    print("  change from cola:", machine.select("cola"))
    print("  state now:", machine.state.name)
    print("  turnstile after a coin:", next_state("locked", "coin"))
    print("  reconcile:", reconcile({"web": 3, "worker": 1}, {"web": 1, "cron": 1}))

    print("== Observer ==")
    elevator, display, log = Elevator("A"), HallDisplay(), TripLogger()
    elevator.subscribe(display)
    elevator.subscribe(log)
    elevator.move_to(3)
    print("  display shows:", display.text, "| events logged:", len(log.events))

    print("== Command ==")
    kitchen, waiter = Kitchen(), Waiter()
    waiter.take_order(CookDish(kitchen, 4, "ramen"))
    waiter.take_order(CookDish(kitchen, 4, "gyoza"))
    waiter.send_to_kitchen()
    waiter.undo_last()
    print("  kitchen tickets:", kitchen.tickets)

    print("== Template Method ==")
    deck = iter([5, 6, 9])
    dealer = Dealer("dealer")
    dealer.cards = [6]
    print("  dealer finishes on:", dealer.play_turn(lambda: next(deck)))

    print("== Chain of Responsibility ==")
    atm = CashDispenser({100: 2, 50: 1, 20: 5})
    print("  withdraw 290:", atm.withdraw(290), "left:", atm.notes_left())

    print("== Iterator ==")
    print("  SCAN from 5 going up:", list(ScanRoute(5, [2, 9, 6, 1, 7])))


if __name__ == "__main__":
    demo()
