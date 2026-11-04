"""Shipping locker system (in the style of Amazon Hub Locker) - recommended design.

One `LockerService` object runs one physical locker location. Carriers drop
packages off, customers pick them up with a one-time code, and staff clear out
packages that were never collected so they can be returned to the sender.
"""

from __future__ import annotations

import logging
import secrets
import threading
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable, Iterator, Protocol

log = logging.getLogger(__name__)
ONE_DAY = timedelta(days=1)


# --------------------------------------------------------------------------
# Time: every time-dependent rule asks a Clock, never datetime.now() directly.
# --------------------------------------------------------------------------
class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """Real wall-clock time, in UTC."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class ManualClock:
    """A clock that only moves when told to. Used by tests and the demo."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)  # a Monday

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class LockerError(Exception):
    """Base class for every error raised by the locker domain."""


class PackageTooLargeError(LockerError):
    """The package does not fit in any compartment size this locker has."""


class NoCompartmentAvailableError(LockerError):
    """Every compartment that could hold the package is in use."""


class InvalidAccessCodeError(LockerError):
    """The code typed on the keypad does not match an active package."""


class KeypadLockedError(LockerError):
    """Too many wrong codes were entered; the keypad is temporarily locked."""


class InvalidTransitionError(LockerError):
    """A package was asked to move to a status its lifecycle does not allow."""


class PackageExpiredError(LockerError):
    """The pickup window closed; the package is waiting to be returned."""


class UnknownPackageError(LockerError):
    """No package with that tracking id is known to this locker."""


# --------------------------------------------------------------------------
# Sizes and compartments
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Dimensions:
    """Outer size of a box, or inner size of a compartment, in centimetres."""

    length: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if min(self.length, self.width, self.height) <= 0:
            raise ValueError("dimensions must be positive")

    def __iter__(self) -> Iterator[int]:
        return iter((self.length, self.width, self.height))

    @property
    def volume(self) -> int:
        return self.length * self.width * self.height

    def fits_inside(self, space: Dimensions) -> bool:
        # A box can be turned on its side, so compare shortest edge with
        # shortest edge, middle with middle, longest with longest.
        return all(mine <= theirs for mine, theirs in zip(sorted(self), sorted(space)))


class CompartmentSize(Enum):
    """The fixed set of door sizes a locker bank is built with."""

    SMALL = (Dimensions(30, 20, 10), Decimal("1.00"))
    MEDIUM = (Dimensions(45, 35, 20), Decimal("2.00"))
    LARGE = (Dimensions(60, 45, 40), Decimal("3.00"))

    def __init__(self, inner: Dimensions, daily_rate: Decimal) -> None:
        self.inner = inner
        self.daily_rate = daily_rate

    @property
    def rank(self) -> int:
        """0 for the smallest size, growing with size (definition order)."""
        return list(CompartmentSize).index(self)

    @classmethod
    def smallest_fitting(cls, dims: Dimensions) -> CompartmentSize | None:
        return next((size for size in cls if dims.fits_inside(size.inner)), None)


@dataclass(eq=False)
class Compartment:
    """One physical door in the locker bank."""

    compartment_id: str
    size: CompartmentSize
    package: Package | None = None
    in_service: bool = True  # False when a door is jammed or under repair

    @property
    def is_free(self) -> bool:
        return self.in_service and self.package is None

    def occupy(self, package: Package) -> None:
        if not self.is_free:
            raise LockerError(f"compartment {self.compartment_id} is not free")
        self.package = package

    def release(self) -> None:
        self.package = None


# --------------------------------------------------------------------------
# Policies (Strategy pattern): how much to charge, when to give up waiting
# --------------------------------------------------------------------------
class FeePolicy(ABC):
    """Decides what a customer owes for keeping a package in a compartment."""

    @abstractmethod
    def fee(self, size: CompartmentSize, stored_for: timedelta) -> Decimal: ...


class NoFee(FeePolicy):
    """Storage is always free (e.g. a membership perk or a returns drop-off)."""

    def fee(self, size: CompartmentSize, stored_for: timedelta) -> Decimal:
        return Decimal("0.00")


class FreeThenDailyFee(FeePolicy):
    """A free period, then the compartment's daily rate for each started day."""

    def __init__(self, free_days: int) -> None:
        if free_days < 0:
            raise ValueError("free_days cannot be negative")
        self.free_days = free_days

    def fee(self, size: CompartmentSize, stored_for: timedelta) -> Decimal:
        days_started = -(-stored_for // ONE_DAY)  # ceiling division: a partial day counts
        chargeable = max(0, days_started - self.free_days)
        return size.daily_rate * chargeable


class ExpiryPolicy(ABC):
    """Decides the moment a deposited package stops being collectable."""

    @abstractmethod
    def deadline(self, deposited_at: datetime) -> datetime: ...


class FixedHoldPeriod(ExpiryPolicy):
    """Hold for a fixed number of calendar days."""

    def __init__(self, days: int) -> None:
        if days <= 0:
            raise ValueError("hold period must be positive")
        self.days = days

    def deadline(self, deposited_at: datetime) -> datetime:
        return deposited_at + timedelta(days=self.days)


class BusinessDaysHold(ExpiryPolicy):
    """Hold for N business days, so a weekend does not eat into the window."""

    def __init__(self, days: int) -> None:
        if days <= 0:
            raise ValueError("hold period must be positive")
        self.days = days

    def deadline(self, deposited_at: datetime) -> datetime:
        moment, remaining = deposited_at, self.days
        while remaining:
            moment += ONE_DAY
            if moment.weekday() < 5:  # Monday=0 .. Friday=4
                remaining -= 1
        return moment


@dataclass(frozen=True)
class LockerPolicy:
    """The pair of rules that apply to one customer's packages."""

    fees: FeePolicy
    expiry: ExpiryPolicy


STANDARD_POLICY = LockerPolicy(fees=FreeThenDailyFee(free_days=3), expiry=FixedHoldPeriod(days=7))


# --------------------------------------------------------------------------
# Accounts and packages
# --------------------------------------------------------------------------
@dataclass(eq=False)
class Account:
    """A customer. Payment itself is handled by an outside billing service."""

    account_id: str
    name: str
    policy: LockerPolicy | None = None  # None means "use the locker's default"
    balance_due: Decimal = Decimal("0.00")

    def add_charge(self, amount: Decimal) -> None:
        if amount < 0:
            raise ValueError("charge cannot be negative")
        self.balance_due += amount


class PackageStatus(Enum):
    IN_TRANSIT = "in transit"
    ASSIGNED = "assigned"      # compartment reserved, carrier at the door
    DEPOSITED = "deposited"    # door closed, customer has a code
    PICKED_UP = "picked up"
    EXPIRED = "expired"        # window closed, still physically in the locker
    RETURNED = "returned"      # staff removed it; it goes back to the sender


# The whole lifecycle in one table: from-status -> statuses it may move to.
ALLOWED_TRANSITIONS: dict[PackageStatus, frozenset[PackageStatus]] = {
    PackageStatus.IN_TRANSIT: frozenset({PackageStatus.ASSIGNED}),
    PackageStatus.ASSIGNED: frozenset({PackageStatus.DEPOSITED, PackageStatus.IN_TRANSIT}),
    PackageStatus.DEPOSITED: frozenset({PackageStatus.PICKED_UP, PackageStatus.EXPIRED}),
    PackageStatus.EXPIRED: frozenset({PackageStatus.RETURNED}),
    PackageStatus.PICKED_UP: frozenset(),
    PackageStatus.RETURNED: frozenset(),
}


@dataclass(eq=False)
class Package:
    """A parcel addressed to a customer at this locker location."""

    tracking_id: str
    owner: Account
    dimensions: Dimensions
    status: PackageStatus = PackageStatus.IN_TRANSIT
    compartment: Compartment | None = None
    deposited_at: datetime | None = None
    pickup_deadline: datetime | None = None

    def move_to(self, new_status: PackageStatus) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransitionError(
                f"{self.tracking_id}: cannot go from {self.status.value} to {new_status.value}"
            )
        self.status = new_status


# --------------------------------------------------------------------------
# Compartment assignment (Strategy)
# --------------------------------------------------------------------------
class CompartmentAssigner(Protocol):
    def choose(self, dims: Dimensions, compartments: Iterable[Compartment]) -> Compartment | None: ...


class SmallestFitAssigner:
    """Pick a free compartment of the smallest size class the box fits in."""

    def choose(self, dims: Dimensions, compartments: Iterable[Compartment]) -> Compartment | None:
        candidates = [c for c in compartments if c.is_free and dims.fits_inside(c.size.inner)]
        return min(candidates, key=lambda c: (c.size.rank, c.compartment_id), default=None)


# --------------------------------------------------------------------------
# Access codes and brute-force protection
# --------------------------------------------------------------------------
def random_six_digit_code() -> str:
    # secrets, not random: random's generator can be predicted from its output.
    return f"{secrets.randbelow(1_000_000):06d}"


class AccessCodeBook:
    """Issues pickup codes unique within this locker and maps them to packages."""

    def __init__(self, generate: Callable[[], str] = random_six_digit_code, max_tries: int = 20) -> None:
        self._generate = generate
        self._max_tries = max_tries
        self._by_code: dict[str, Package] = {}
        self._by_tracking_id: dict[str, str] = {}

    def issue(self, package: Package) -> str:
        for _ in range(self._max_tries):
            code = self._generate()
            if code not in self._by_code:  # collision check: codes must be unambiguous
                self._by_code[code] = package
                self._by_tracking_id[package.tracking_id] = code
                return code
        raise LockerError("could not generate a unique access code")

    def lookup(self, code: str) -> Package | None:
        return self._by_code.get(code)

    def revoke(self, package: Package) -> None:
        code = self._by_tracking_id.pop(package.tracking_id, None)
        if code is not None:
            del self._by_code[code]

    def __len__(self) -> int:
        return len(self._by_code)


class AttemptLimiter:
    """Locks the keypad after too many wrong codes inside a sliding window."""

    def __init__(
        self,
        clock: Clock,
        max_failures: int = 5,
        window: timedelta = timedelta(minutes=10),
        lockout: timedelta = timedelta(minutes=15),
    ) -> None:
        self._clock = clock
        self._max_failures = max_failures
        self._window = window
        self._lockout = lockout
        self._failures: deque[datetime] = deque()
        self._locked_until: datetime | None = None

    def check(self) -> None:
        if self._locked_until and self._clock.now() < self._locked_until:
            raise KeypadLockedError(f"keypad locked until {self._locked_until:%H:%M}")

    def record_failure(self) -> bool:
        """Remember a wrong code. Returns True if this failure triggered a lockout."""
        now = self._clock.now()
        self._failures.append(now)
        while self._failures and now - self._failures[0] > self._window:
            self._failures.popleft()
        if len(self._failures) >= self._max_failures:
            self._locked_until = now + self._lockout
            self._failures.clear()
            return True
        return False

    def record_success(self) -> None:
        self._failures.clear()


# --------------------------------------------------------------------------
# Events and observers
# --------------------------------------------------------------------------
class EventType(Enum):
    ASSIGNED = "assigned"
    DEPOSITED = "deposited"
    PICKED_UP = "picked up"
    EXPIRED = "expired"
    RETURNED = "returned"
    KEYPAD_LOCKED = "keypad locked"


@dataclass(frozen=True)
class LockerEvent:
    type: EventType
    location_id: str
    at: datetime
    package: Package | None = None
    access_code: str | None = None
    fee: Decimal | None = None


class LockerObserver(Protocol):
    def notify(self, event: LockerEvent) -> None: ...


class MessageSender(Protocol):
    def send(self, account: Account, text: str) -> None: ...


class InMemoryOutbox:
    """Stands in for an SMS / email / push gateway."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, account: Account, text: str) -> None:
        self.sent.append((account.account_id, text))


class CustomerNotifier:
    """Turns locker events into messages for the package owner."""

    def __init__(self, sender: MessageSender) -> None:
        self._sender = sender

    def notify(self, event: LockerEvent) -> None:
        pkg = event.package
        if pkg is None:
            return
        if event.type is EventType.DEPOSITED:
            text = (f"Your package {pkg.tracking_id} is ready at locker {event.location_id}. "
                    f"Code {event.access_code}, collect by {pkg.pickup_deadline:%a %d %b %H:%M}.")
        elif event.type is EventType.PICKED_UP:
            text = f"Package {pkg.tracking_id} collected. Storage fee: ${event.fee}."
        elif event.type is EventType.EXPIRED:
            text = f"Package {pkg.tracking_id} was not collected in time and will be returned."
        else:
            return
        self._sender.send(pkg.owner, text)


class StaffTaskQueue:
    """Collects work for the site associate: expired parcels, locked keypads."""

    def __init__(self) -> None:
        self.tasks: list[str] = []

    def notify(self, event: LockerEvent) -> None:
        if event.type is EventType.EXPIRED and event.package and event.package.compartment:
            self.tasks.append(f"Remove {event.package.tracking_id} from "
                              f"{event.package.compartment.compartment_id} for return")
        elif event.type is EventType.KEYPAD_LOCKED:
            self.tasks.append(f"Keypad locked at {event.location_id}: check for tampering")


# --------------------------------------------------------------------------
# The facade
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PickupReceipt:
    package: Package
    compartment_id: str
    fee: Decimal


class LockerService:
    """Everything that happens at one locker location: drop-off, pickup, clean-up."""

    def __init__(
        self,
        location_id: str,
        compartments: Iterable[Compartment],
        *,
        clock: Clock | None = None,
        default_policy: LockerPolicy = STANDARD_POLICY,
        assigner: CompartmentAssigner | None = None,
        codes: AccessCodeBook | None = None,
        limiter: AttemptLimiter | None = None,
    ) -> None:
        self.location_id = location_id
        self._compartments = {c.compartment_id: c for c in compartments}
        self._clock = clock or SystemClock()
        self._default_policy = default_policy
        self._assigner = assigner or SmallestFitAssigner()
        self._codes = codes or AccessCodeBook()
        self._limiter = limiter or AttemptLimiter(self._clock)
        self._packages: dict[str, Package] = {}
        self._observers: list[LockerObserver] = []
        self._lock = threading.RLock()

    @classmethod
    def with_layout(cls, location_id: str, layout: dict[CompartmentSize, int], **kwargs) -> LockerService:
        """Factory: build a locker bank from a count of doors per size."""
        compartments = [
            Compartment(f"{size.name[0]}{n:02d}", size)
            for size, how_many in layout.items()
            for n in range(1, how_many + 1)
        ]
        return cls(location_id, compartments, **kwargs)

    # ----- observers --------------------------------------------------------
    def subscribe(self, observer: LockerObserver) -> None:
        self._observers.append(observer)

    def _publish(self, event: LockerEvent) -> None:
        for observer in list(self._observers):
            try:
                observer.notify(event)
            except Exception:  # one broken observer must not undo a pickup
                log.exception("observer %r failed on %s", observer, event.type)

    def _transaction(self, operation: Callable[[list[LockerEvent]], object]):
        """Run `operation` under the lock; publish its events after releasing it."""
        events: list[LockerEvent] = []
        try:
            with self._lock:
                return operation(events)
        finally:
            for event in events:
                self._publish(event)

    def _event(self, type_: EventType, package: Package | None = None, **extra) -> LockerEvent:
        return LockerEvent(type_, self.location_id, self._clock.now(), package, **extra)

    # ----- queries ----------------------------------------------------------
    def free_count(self, size: CompartmentSize | None = None) -> int:
        with self._lock:
            return sum(1 for c in self._compartments.values()
                       if c.is_free and (size is None or c.size is size))

    def package(self, tracking_id: str) -> Package:
        try:
            return self._packages[tracking_id]
        except KeyError:
            raise UnknownPackageError(tracking_id) from None

    def policy_for(self, package: Package) -> LockerPolicy:
        return package.owner.policy or self._default_policy

    def fee_due(self, tracking_id: str) -> Decimal:
        with self._lock:
            pkg = self.package(tracking_id)
            if pkg.status is not PackageStatus.DEPOSITED:
                return Decimal("0.00")
            return self.policy_for(pkg).fees.fee(pkg.compartment.size, self._clock.now() - pkg.deposited_at)

    # ----- carrier flow -----------------------------------------------------
    def assign(self, package: Package) -> Compartment:
        """Carrier scans a parcel: reserve a compartment and open its door."""

        def op(events: list[LockerEvent]) -> Compartment:
            if CompartmentSize.smallest_fitting(package.dimensions) is None:
                raise PackageTooLargeError(f"{package.tracking_id} is larger than any compartment")
            compartment = self._assigner.choose(package.dimensions, self._compartments.values())
            if compartment is None:
                raise NoCompartmentAvailableError(f"no free compartment fits {package.tracking_id}")
            package.move_to(PackageStatus.ASSIGNED)
            compartment.occupy(package)
            package.compartment = compartment
            self._packages[package.tracking_id] = package
            events.append(self._event(EventType.ASSIGNED, package))
            return compartment

        return self._transaction(op)

    def confirm_deposit(self, tracking_id: str) -> str:
        """Door sensor reports closed with the parcel inside: start the clock."""

        def op(events: list[LockerEvent]) -> str:
            pkg = self.package(tracking_id)
            pkg.move_to(PackageStatus.DEPOSITED)
            pkg.deposited_at = self._clock.now()
            pkg.pickup_deadline = self.policy_for(pkg).expiry.deadline(pkg.deposited_at)
            code = self._codes.issue(pkg)
            events.append(self._event(EventType.DEPOSITED, pkg, access_code=code))
            return code

        return self._transaction(op)

    def cancel_assignment(self, tracking_id: str) -> None:
        """Carrier could not load the parcel (door jammed, box bulged): undo."""

        def op(events: list[LockerEvent]) -> None:
            pkg = self.package(tracking_id)
            pkg.move_to(PackageStatus.IN_TRANSIT)
            pkg.compartment.release()
            pkg.compartment = None
            del self._packages[tracking_id]

        self._transaction(op)

    # ----- customer flow ----------------------------------------------------
    def pick_up(self, code: str) -> PickupReceipt:
        """Customer types a code at the keypad."""

        def op(events: list[LockerEvent]) -> PickupReceipt:
            self._limiter.check()
            pkg = self._codes.lookup(code)
            if pkg is None:
                if self._limiter.record_failure():
                    events.append(self._event(EventType.KEYPAD_LOCKED))
                raise InvalidAccessCodeError("unknown or already-used code")
            self._limiter.record_success()
            now = self._clock.now()
            if now >= pkg.pickup_deadline:
                self._expire(pkg, events)
                raise PackageExpiredError(f"{pkg.tracking_id} expired at {pkg.pickup_deadline}")
            fee = self.policy_for(pkg).fees.fee(pkg.compartment.size, now - pkg.deposited_at)
            if fee:
                pkg.owner.add_charge(fee)
            compartment = pkg.compartment
            pkg.move_to(PackageStatus.PICKED_UP)
            self._codes.revoke(pkg)
            compartment.release()
            events.append(self._event(EventType.PICKED_UP, pkg, fee=fee))
            return PickupReceipt(pkg, compartment.compartment_id, fee)

        return self._transaction(op)

    # ----- staff / scheduled flow -------------------------------------------
    def _expire(self, pkg: Package, events: list[LockerEvent]) -> None:
        pkg.move_to(PackageStatus.EXPIRED)
        self._codes.revoke(pkg)  # the customer's code stops working immediately
        events.append(self._event(EventType.EXPIRED, pkg))

    def expire_overdue(self) -> list[Package]:
        """Run periodically (e.g. every few minutes) to close lapsed pickup windows."""

        def op(events: list[LockerEvent]) -> list[Package]:
            now = self._clock.now()
            overdue = [p for p in self._packages.values()
                       if p.status is PackageStatus.DEPOSITED and now >= p.pickup_deadline]
            for pkg in overdue:
                self._expire(pkg, events)
            return overdue

        return self._transaction(op)

    def return_to_sender(self, tracking_id: str) -> Package:
        """Staff removed an expired parcel; free the compartment."""

        def op(events: list[LockerEvent]) -> Package:
            pkg = self.package(tracking_id)
            pkg.move_to(PackageStatus.RETURNED)
            pkg.compartment.release()
            events.append(self._event(EventType.RETURNED, pkg))
            return pkg

        return self._transaction(op)


# --------------------------------------------------------------------------
def demo() -> None:
    clock = ManualClock()
    locker = LockerService.with_layout(
        "SEA-CAPITOL-HILL-01",
        {CompartmentSize.SMALL: 2, CompartmentSize.MEDIUM: 2, CompartmentSize.LARGE: 1},
        clock=clock,
    )
    outbox, staff = InMemoryOutbox(), StaffTaskQueue()
    locker.subscribe(CustomerNotifier(outbox))
    locker.subscribe(staff)

    ana = Account("A1", "Ana")
    ben = Account("B2", "Ben")
    cy = Account("C3", "Cy", policy=LockerPolicy(NoFee(), FixedHoldPeriod(days=3)))

    print("== Carrier drop-off ==")
    codes = {}
    for pkg in (Package("TBA-001", ana, Dimensions(25, 15, 8)),
                Package("TBA-002", ben, Dimensions(40, 30, 18)),
                Package("TBA-003", cy, Dimensions(28, 12, 9))):
        compartment = locker.assign(pkg)
        codes[pkg.tracking_id] = locker.confirm_deposit(pkg.tracking_id)
        print(f"{pkg.tracking_id} -> {compartment.compartment_id} ({compartment.size.name})")
    print("free compartments:", locker.free_count())

    print("\n== Customers ==")
    clock.advance(timedelta(hours=20))
    receipt = locker.pick_up(codes["TBA-001"])
    print(f"Ana collects {receipt.package.tracking_id} from {receipt.compartment_id}, fee ${receipt.fee}")

    for wrong in ("000000", "123456", "111111", "222222", "333333"):
        try:
            locker.pick_up(wrong)
        except InvalidAccessCodeError:
            pass
    try:
        locker.pick_up(codes["TBA-002"])
    except KeypadLockedError as err:
        print("Ben is blocked after someone guessed codes:", err)

    clock.advance(timedelta(days=4))
    receipt = locker.pick_up(codes["TBA-002"])
    print(f"Ben collects on day 5, fee ${receipt.fee}, balance due ${ben.balance_due}")

    print("\n== Nightly sweep ==")
    for pkg in locker.expire_overdue():
        print(f"{pkg.tracking_id} expired; returning to sender")
        locker.return_to_sender(pkg.tracking_id)
    print("free compartments:", locker.free_count())

    print("\n== Messages sent ==")
    for account_id, text in outbox.sent:
        print(f"[{account_id}] {text}")
    print("\n== Staff tasks ==")
    for task in staff.tasks:
        print("-", task)


if __name__ == "__main__":
    demo()
