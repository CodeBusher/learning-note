"""Competing designs for the shipping locker, side by side.

Each section is a self-contained alternative to one decision made in
shipping_locker.py, so the trade-offs can be run and compared.
"""

from __future__ import annotations

import hashlib
import hmac
import random
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable

from shipping_locker import (
    Account,
    Compartment,
    CompartmentSize,
    Dimensions,
    InvalidTransitionError,
    SmallestFitAssigner,
)

# ==========================================================================
# 1. Compartment assignment
# ==========================================================================


class FirstFreeAssigner:
    """Take the first free compartment the box fits in, in door order."""

    def choose(self, dims: Dimensions, compartments: Iterable[Compartment]) -> Compartment | None:
        return next((c for c in compartments if c.is_free and dims.fits_inside(c.size.inner)), None)


@dataclass(eq=False)
class FreeformCompartment:
    """A compartment with its own measured interior instead of a size class."""

    compartment_id: str
    inner: Dimensions
    occupied: bool = False


class BestFitVolumeAssigner:
    """Pick the free compartment that leaves the least empty space around the box."""

    def choose(self, dims: Dimensions, compartments: Iterable[FreeformCompartment]) -> FreeformCompartment | None:
        candidates = [c for c in compartments if not c.occupied and dims.fits_inside(c.inner)]
        return min(candidates, key=lambda c: (c.inner.volume - dims.volume, c.compartment_id), default=None)


def fill_until_rejected(assigner, boxes: list[Dimensions], layout: dict[CompartmentSize, int]) -> list[str]:
    """Place boxes in order with a given assigner; report where each one went."""
    # Large doors first, as on many real banks where big doors sit at the bottom.
    compartments = [Compartment(f"{size.name[0]}{n}", size)
                    for size in reversed(CompartmentSize)
                    for n in range(1, layout.get(size, 0) + 1)]
    placements = []
    for box in boxes:
        chosen = assigner.choose(box, compartments)
        if chosen is None:
            placements.append("REJECTED")
        else:
            chosen.package = object()  # any non-None marker means "occupied"
            placements.append(chosen.compartment_id)
    return placements


# ==========================================================================
# 2. Access codes
# ==========================================================================


class NaiveRandomCodes:
    """random.randint and no collision check. Two problems in four lines."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)  # Mersenne Twister: predictable from output
        self.by_code: dict[str, str] = {}

    def issue(self, tracking_id: str) -> str:
        code = f"{self._rng.randint(0, 999_999):06d}"
        self.by_code[code] = tracking_id  # silently overwrites an existing package!
        return code


class TokenCodes:
    """Long URL-safe tokens, meant to be shown as a QR code in an app."""

    def __init__(self) -> None:
        self.by_token: dict[str, str] = {}

    def issue(self, tracking_id: str) -> str:
        token = secrets.token_urlsafe(16)  # 128 bits: collisions are not a practical concern
        self.by_token[token] = tracking_id
        return token


class HashedCodeStore:
    """Store only a keyed hash of each code, so a leaked database reveals no codes."""

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or secrets.token_bytes(32)
        self._by_digest: dict[str, str] = {}

    def _digest(self, code: str) -> str:
        return hmac.new(self._key, code.encode(), hashlib.sha256).hexdigest()

    def issue(self, tracking_id: str) -> str:
        while True:
            code = f"{secrets.randbelow(1_000_000):06d}"
            digest = self._digest(code)
            if digest not in self._by_digest:
                self._by_digest[digest] = tracking_id
                return code  # handed to the customer once, never stored in clear

    def lookup(self, code: str) -> str | None:
        return self._by_digest.get(self._digest(code))


def scan_for_code(compartments: list[tuple[str, str | None]], code: str) -> str | None:
    """Code lookup without a map: walk every door and compare (O(n) per keypress)."""
    for compartment_id, stored in compartments:
        if stored is not None and hmac.compare_digest(stored, code):
            return compartment_id
    return None


def brute_force_odds(active_codes: int, guesses: int, code_space: int = 1_000_000) -> float:
    """Probability that `guesses` distinct random guesses hit at least one active code."""
    miss = 1.0
    for i in range(guesses):
        miss *= (code_space - active_codes - i) / (code_space - i)
    return 1 - miss


# ==========================================================================
# 3. Package lifecycle: the State pattern instead of an enum + transition table
# ==========================================================================


class PackageState(ABC):
    """Each state object knows which events it accepts."""

    name = "?"

    def deposit(self, pkg: StatefulPackage) -> None:
        self._reject("deposit")

    def pick_up(self, pkg: StatefulPackage) -> None:
        self._reject("pick up")

    def expire(self, pkg: StatefulPackage) -> None:
        self._reject("expire")

    def return_to_sender(self, pkg: StatefulPackage) -> None:
        self._reject("return")

    def _reject(self, action: str) -> None:
        raise InvalidTransitionError(f"cannot {action} a package that is {self.name}")


class AssignedState(PackageState):
    name = "assigned"

    def deposit(self, pkg: StatefulPackage) -> None:
        pkg.state = DepositedState()


class DepositedState(PackageState):
    name = "deposited"

    def pick_up(self, pkg: StatefulPackage) -> None:
        pkg.state = PickedUpState()

    def expire(self, pkg: StatefulPackage) -> None:
        pkg.state = ExpiredState()


class ExpiredState(PackageState):
    name = "expired"

    def return_to_sender(self, pkg: StatefulPackage) -> None:
        pkg.state = ReturnedState()


class PickedUpState(PackageState):
    name = "picked up"


class ReturnedState(PackageState):
    name = "returned"


class StatefulPackage:
    """The context object: it forwards every event to its current state."""

    def __init__(self, tracking_id: str) -> None:
        self.tracking_id = tracking_id
        self.state: PackageState = AssignedState()

    def deposit(self) -> None:
        self.state.deposit(self)

    def pick_up(self) -> None:
        self.state.pick_up(self)

    def expire(self) -> None:
        self.state.expire(self)

    def return_to_sender(self) -> None:
        self.state.return_to_sender(self)


# ==========================================================================
# 4. Fees: hard-coded branches instead of a FeePolicy strategy
# ==========================================================================


def hardcoded_fee(size: CompartmentSize, stored_for: timedelta, is_member: bool) -> Decimal:
    """Every new pricing idea becomes another branch in this one function."""
    days = -(-stored_for // timedelta(days=1))
    if is_member:
        return Decimal("0.00")
    elif days <= 3:
        return Decimal("0.00")
    elif size is CompartmentSize.LARGE:
        return Decimal("3.00") * (days - 3)
    elif size is CompartmentSize.MEDIUM:
        return Decimal("2.00") * (days - 3)
    else:
        return Decimal("1.00") * (days - 3)


# ==========================================================================
# 5. Notification: a direct call instead of Observer
# ==========================================================================


class SmsGateway:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, account: Account, text: str) -> None:
        self.sent.append(f"{account.account_id}: {text}")


class DirectCallLocker:
    """The locker calls the SMS gateway itself. Simple, but every new listener edits this class."""

    def __init__(self, sms: SmsGateway) -> None:
        self._sms = sms
        self.deposited: dict[str, Account] = {}

    def confirm_deposit(self, tracking_id: str, owner: Account, code: str) -> None:
        self.deposited[tracking_id] = owner
        self._sms.send(owner, f"{tracking_id} is ready, code {code}")
        # Want an email too? An audit log? A fraud monitor? Add more lines here,
        # and if the SMS call raises, the deposit above is half-done.


# ==========================================================================
def demo() -> None:
    print("== 1. Assignment: S, M, L arrive; the bank has 1 small, 1 medium, 1 large ==")
    boxes = [Dimensions(20, 15, 8), Dimensions(40, 30, 18), Dimensions(55, 40, 35)]
    layout = {CompartmentSize.SMALL: 1, CompartmentSize.MEDIUM: 1, CompartmentSize.LARGE: 1}
    print("first free  :", fill_until_rejected(FirstFreeAssigner(), boxes, layout))
    print("smallest fit:", fill_until_rejected(SmallestFitAssigner(), boxes, layout))

    custom = [FreeformCompartment("tall", Dimensions(20, 20, 60)),
              FreeformCompartment("wide", Dimensions(50, 40, 12))]
    poster_tube = Dimensions(8, 8, 55)
    print("best fit for a poster tube:", BestFitVolumeAssigner().choose(poster_tube, custom).compartment_id)

    print("\n== 2. Access codes ==")
    naive = NaiveRandomCodes(seed=7)
    issued = [naive.issue(f"PKG-{i}") for i in range(3000)]
    print(f"naive: {len(issued)} codes issued, {len(naive.by_code)} still resolvable (collisions overwrote the rest)")
    store = HashedCodeStore()
    code = store.issue("PKG-42")
    print("hashed store finds PKG-42:", store.lookup(code), "| stored value looks like:", next(iter(store._by_digest))[:16], "...")
    print("token example:", TokenCodes().issue("PKG-1")[:10], "...")
    print(f"odds 300 active codes are hit by 1,000 guesses (no rate limit): {brute_force_odds(300, 1000):.0%}")
    print(f"odds with a 5-try lockout (5 guesses):                 {brute_force_odds(300, 5):.2%}")

    print("\n== 3. State pattern ==")
    pkg = StatefulPackage("PKG-9")
    pkg.deposit()
    pkg.expire()
    try:
        pkg.pick_up()
    except InvalidTransitionError as err:
        print("rejected:", err)
    pkg.return_to_sender()
    print("final state:", pkg.state.name)

    print("\n== 4. Hard-coded fees ==")
    print("medium, 5 days, non-member:", hardcoded_fee(CompartmentSize.MEDIUM, timedelta(days=5), False))

    print("\n== 5. Direct call ==")
    sms = SmsGateway()
    DirectCallLocker(sms).confirm_deposit("PKG-1", Account("A1", "Ana"), "123456")
    print(sms.sent)


if __name__ == "__main__":
    demo()
