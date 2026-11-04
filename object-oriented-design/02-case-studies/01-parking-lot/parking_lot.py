"""Parking lot: the recommended object-oriented design.

Run it with ``python3 parking_lot.py`` to see a short scenario.

Main pieces:
    Vehicle, ParkingSpot      -- the physical things (plain data plus small invariants)
    SpotAllocator             -- owns the spots and picks the best free one
    Ticket, Receipt           -- immutable records of a parking session
    FeePolicy + subclasses    -- Strategy pattern for pricing (and one Decorator)
    ParkingLot                -- Facade that gates, pay stations and apps talk to
"""

from __future__ import annotations

import heapq
import itertools
import math
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum


# ---------------------------------------------------------------------------
# Vocabulary: vehicle types, spot types and which fits where
# ---------------------------------------------------------------------------

class VehicleType(Enum):
    """The kinds of vehicle the lot accepts."""

    MOTORCYCLE = "motorcycle"
    CAR = "car"
    ELECTRIC_CAR = "electric car"
    TRUCK = "truck"


class SpotType(Enum):
    """The kinds of spot painted on the floor."""

    COMPACT = "compact"
    REGULAR = "regular"
    EV_CHARGING = "ev charging"
    OVERSIZED = "oversized"


# Which spot types each vehicle may use, best choice first.
# This is business policy, so it lives in data rather than in a class hierarchy:
# supporting a new vehicle or spot type means adding a row, not a subclass.
DEFAULT_COMPATIBILITY: Mapping[VehicleType, tuple[SpotType, ...]] = {
    VehicleType.MOTORCYCLE: (SpotType.COMPACT, SpotType.REGULAR, SpotType.OVERSIZED),
    VehicleType.CAR: (SpotType.REGULAR, SpotType.OVERSIZED),
    VehicleType.ELECTRIC_CAR: (SpotType.EV_CHARGING, SpotType.REGULAR, SpotType.OVERSIZED),
    VehicleType.TRUCK: (SpotType.OVERSIZED,),
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ParkingError(Exception):
    """Base class for every error the parking lot raises on purpose."""


class LotFullError(ParkingError):
    """No compatible spot is free for this vehicle."""


class AlreadyParkedError(ParkingError):
    """A vehicle with this plate is already inside."""


class UnknownTicketError(ParkingError):
    """The ticket (or plate) does not match an active parking session."""


class SpotStateError(ParkingError):
    """Someone tried to occupy a taken spot or vacate an empty one."""


# ---------------------------------------------------------------------------
# Physical entities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Vehicle:
    """A vehicle identified by its license plate. Immutable: a car does not change plates mid-visit."""

    plate: str
    vehicle_type: VehicleType

    def __post_init__(self) -> None:
        normalized = self.plate.strip().upper()
        if not normalized:
            raise ValueError("license plate must not be empty")
        # Cameras and humans write plates differently ("abc 123" vs "ABC 123").
        object.__setattr__(self, "plate", normalized)


@dataclass(eq=False)
class ParkingSpot:
    """One painted spot. It only guards its own invariant: at most one occupant."""

    spot_id: str
    spot_type: SpotType
    level: int = 0
    distance: int = 0  # rank from the entrance or elevator; lower is better
    occupant: str | None = field(default=None, init=False)

    @property
    def is_free(self) -> bool:
        return self.occupant is None

    def occupy(self, plate: str) -> None:
        if self.occupant is not None:
            raise SpotStateError(f"spot {self.spot_id} is already taken by {self.occupant}")
        self.occupant = plate

    def vacate(self) -> str:
        if self.occupant is None:
            raise SpotStateError(f"spot {self.spot_id} is already empty")
        plate, self.occupant = self.occupant, None
        return plate


def build_level(level: int, *, compact: int = 0, regular: int = 0,
                ev: int = 0, oversized: int = 0) -> list[ParkingSpot]:
    """Create the spots for one floor.

    Spot ids look like ``L1-R03``. Distance grows along the floor and with the
    floor number, so lower floors and lower numbers are handed out first.
    """
    layout = [(SpotType.COMPACT, "C", compact), (SpotType.REGULAR, "R", regular),
              (SpotType.EV_CHARGING, "E", ev), (SpotType.OVERSIZED, "O", oversized)]
    spots: list[ParkingSpot] = []
    position = 0
    for spot_type, letter, count in layout:
        for number in range(1, count + 1):
            spots.append(ParkingSpot(f"L{level}-{letter}{number:02d}", spot_type,
                                     level=level, distance=level * 1000 + position))
            position += 1
    return spots


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

class SpotAllocator:
    """Owns every spot and hands out the best free one for a vehicle.

    Free spots live in one min-heap per spot type, ordered by distance. Finding
    a spot checks at most a handful of heaps (one per compatible type), so it
    costs O(log n) instead of a scan over the whole garage.
    """

    def __init__(self, spots: Iterable[ParkingSpot],
                 compatibility: Mapping[VehicleType, Sequence[SpotType]] = DEFAULT_COMPATIBILITY) -> None:
        self._compatibility = dict(compatibility)
        self._spots: dict[str, ParkingSpot] = {}
        self._free: dict[SpotType, list[tuple[int, str]]] = {t: [] for t in SpotType}
        for spot in spots:
            if spot.spot_id in self._spots:
                raise ValueError(f"duplicate spot id {spot.spot_id}")
            self._spots[spot.spot_id] = spot
            if spot.is_free:
                heapq.heappush(self._free[spot.spot_type], (spot.distance, spot.spot_id))

    def allocate(self, vehicle: Vehicle) -> ParkingSpot | None:
        """Claim the nearest spot of the most preferred compatible type, or return None."""
        for spot_type in self._compatibility.get(vehicle.vehicle_type, ()):
            heap = self._free[spot_type]
            if heap:
                _, spot_id = heapq.heappop(heap)
                spot = self._spots[spot_id]
                spot.occupy(vehicle.plate)
                return spot
        return None

    def release(self, spot_id: str) -> None:
        spot = self._spots[spot_id]
        spot.vacate()
        heapq.heappush(self._free[spot.spot_type], (spot.distance, spot.spot_id))

    def spot(self, spot_id: str) -> ParkingSpot:
        return self._spots[spot_id]

    def free_count(self, spot_type: SpotType) -> int:
        return len(self._free[spot_type])


# ---------------------------------------------------------------------------
# Session records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ticket:
    """Proof that a vehicle entered: who, where and when. Never mutated after issue."""

    ticket_id: str
    plate: str
    vehicle_type: VehicleType
    spot_id: str
    level: int
    entry_time: datetime


@dataclass(frozen=True)
class Receipt:
    """What the driver gets at the exit: the ticket, when they left and what they paid."""

    ticket: Ticket
    exit_time: datetime
    fee: Decimal

    @property
    def duration(self) -> timedelta:
        return self.exit_time - self.ticket.entry_time


# ---------------------------------------------------------------------------
# Pricing (Strategy pattern)
# ---------------------------------------------------------------------------

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def billable_hours(duration: timedelta, grace: timedelta = timedelta(0)) -> int:
    """Every started hour is charged, but a stay inside the grace period is free."""
    if duration <= grace:
        return 0
    return math.ceil(duration.total_seconds() / 3600)


class FeePolicy(ABC):
    """A pricing rule. The lot asks 'how much for this ticket if they leave now?'."""

    @abstractmethod
    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        ...


class FlatFee(FeePolicy):
    """One price per visit, like an event-night lot."""

    def __init__(self, amount: Decimal) -> None:
        self.amount = amount.quantize(CENTS)

    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        return self.amount


class HourlyFee(FeePolicy):
    """A per-hour rate that depends on the vehicle type, with a free grace period."""

    def __init__(self, rates: Mapping[VehicleType, Decimal],
                 grace: timedelta = timedelta(minutes=10)) -> None:
        self.rates = dict(rates)
        self.grace = grace

    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        hours = billable_hours(exit_time - ticket.entry_time, self.grace)
        return (self.rates[ticket.vehicle_type] * hours).quantize(CENTS)


class TieredFee(FeePolicy):
    """Price bands ("up to 1h", "up to 3h", ...) capped by a daily maximum.

    ``tiers`` is a list of ``(up_to_hours, price)`` pairs in increasing order.
    Each full 24 hours costs ``daily_max``; the leftover part is priced by band.
    """

    def __init__(self, tiers: Sequence[tuple[int, Decimal]], daily_max: Decimal,
                 grace: timedelta = timedelta(minutes=10)) -> None:
        if list(tiers) != sorted(tiers):
            raise ValueError("tiers must be sorted by hours")
        self.tiers = list(tiers)
        self.daily_max = daily_max
        self.grace = grace

    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        duration = exit_time - ticket.entry_time
        if duration <= self.grace:
            return ZERO
        full_days, remainder = divmod(duration, timedelta(days=1))
        total = self.daily_max * full_days
        if remainder > timedelta(0):
            total += min(self._band_price(billable_hours(remainder)), self.daily_max)
        return total.quantize(CENTS)

    def _band_price(self, hours: int) -> Decimal:
        for up_to, price in self.tiers:
            if hours <= up_to:
                return price
        return self.daily_max


class PeakHourSurcharge(FeePolicy):
    """Decorator: wraps any other policy and multiplies its fee for stays that began at peak time."""

    def __init__(self, inner: FeePolicy, multiplier: Decimal, peak_hours: Iterable[int]) -> None:
        self.inner = inner
        self.multiplier = multiplier
        self.peak_hours = frozenset(peak_hours)

    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        base = self.inner.fee(ticket, exit_time)
        if ticket.entry_time.hour in self.peak_hours:
            return (base * self.multiplier).quantize(CENTS)
        return base


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

Clock = Callable[[], datetime]


class ManualClock:
    """A clock you move by hand, so demos and tests can 'wait three hours' instantly."""

    def __init__(self, start: datetime) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, **kwargs: float) -> None:
        self._now += timedelta(**kwargs)


# ---------------------------------------------------------------------------
# The facade
# ---------------------------------------------------------------------------

class ParkingLot:
    """Facade: the single object that entry gates, exit gates and pay stations talk to.

    It coordinates the allocator, the active tickets and the fee policy, and
    holds one lock so that "find a free spot and claim it" is atomic.
    """

    def __init__(self, spots: Iterable[ParkingSpot], fee_policy: FeePolicy,
                 clock: Clock = datetime.now,
                 compatibility: Mapping[VehicleType, Sequence[SpotType]] = DEFAULT_COMPATIBILITY) -> None:
        self._allocator = SpotAllocator(spots, compatibility)
        self._fee_policy = fee_policy
        self._clock = clock
        self._active: dict[str, Ticket] = {}       # ticket_id -> ticket
        self._ticket_by_plate: dict[str, str] = {}  # plate -> ticket_id
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def enter(self, vehicle: Vehicle) -> Ticket:
        """Assign a spot and issue a ticket, or raise if that is impossible."""
        with self._lock:
            if vehicle.plate in self._ticket_by_plate:
                raise AlreadyParkedError(f"{vehicle.plate} is already parked")
            spot = self._allocator.allocate(vehicle)
            if spot is None:
                raise LotFullError(f"no free spot for a {vehicle.vehicle_type.value}")
            ticket = Ticket(
                ticket_id=f"T{next(self._ids):06d}",
                plate=vehicle.plate,
                vehicle_type=vehicle.vehicle_type,
                spot_id=spot.spot_id,
                level=spot.level,
                entry_time=self._clock(),
            )
            self._active[ticket.ticket_id] = ticket
            self._ticket_by_plate[ticket.plate] = ticket.ticket_id
            return ticket

    def quote(self, ticket_id: str) -> Decimal:
        """What the pay station shows: the fee if the driver left right now."""
        with self._lock:
            ticket = self._get_active(ticket_id)
            return self._fee_policy.fee(ticket, self._clock())

    def exit(self, ticket_id: str) -> Receipt:
        """Charge the fee, free the spot and close the session."""
        with self._lock:
            ticket = self._get_active(ticket_id)
            exit_time = self._clock()
            # Price first: if the policy raises, nothing has been changed yet.
            fee = self._fee_policy.fee(ticket, exit_time)
            del self._active[ticket_id]
            del self._ticket_by_plate[ticket.plate]
            self._allocator.release(ticket.spot_id)
            return Receipt(ticket, exit_time, fee)

    def exit_by_plate(self, plate: str) -> Receipt:
        """Ticketless exit: a license-plate camera read the plate at the gate."""
        with self._lock:
            ticket_id = self._ticket_by_plate.get(plate.strip().upper())
        if ticket_id is None:
            raise UnknownTicketError(f"no active session for plate {plate!r}")
        return self.exit(ticket_id)

    def find_vehicle(self, plate: str) -> Ticket | None:
        """'Where did I park?' kiosks look a car up by plate."""
        with self._lock:
            ticket_id = self._ticket_by_plate.get(plate.strip().upper())
            return self._active.get(ticket_id) if ticket_id else None

    def availability(self) -> dict[SpotType, int]:
        """Free spots per type, for the 'SPACES AVAILABLE' sign at the entrance."""
        with self._lock:
            return {t: self._allocator.free_count(t) for t in SpotType}

    def _get_active(self, ticket_id: str) -> Ticket:
        ticket = self._active.get(ticket_id)
        if ticket is None:
            raise UnknownTicketError(f"ticket {ticket_id!r} is not active")
        return ticket


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> None:
    clock = ManualClock(datetime(2026, 3, 2, 8, 30))  # a Monday morning
    hourly = HourlyFee({
        VehicleType.MOTORCYCLE: Decimal("1.50"),
        VehicleType.CAR: Decimal("3.00"),
        VehicleType.ELECTRIC_CAR: Decimal("3.00"),
        VehicleType.TRUCK: Decimal("6.00"),
    })
    pricing = PeakHourSurcharge(hourly, Decimal("1.5"), peak_hours=range(7, 10))
    spots = build_level(1, compact=1, regular=2, ev=1, oversized=1) + build_level(2, regular=2)
    lot = ParkingLot(spots, pricing, clock=clock)

    print("Free spots:", {t.value: n for t, n in lot.availability().items()})
    arrivals = [Vehicle("moto-1", VehicleType.MOTORCYCLE), Vehicle("car-1", VehicleType.CAR),
                Vehicle("ev-1", VehicleType.ELECTRIC_CAR), Vehicle("truck-1", VehicleType.TRUCK),
                Vehicle("car-2", VehicleType.CAR)]
    tickets = {}
    for vehicle in arrivals:
        ticket = lot.enter(vehicle)
        tickets[vehicle.plate] = ticket
        print(f"  {vehicle.plate:8} ({vehicle.vehicle_type.value}) -> spot {ticket.spot_id}")

    try:
        lot.enter(Vehicle("truck-2", VehicleType.TRUCK))
    except LotFullError as error:
        print("  truck-2 turned away:", error)

    clock.advance(hours=2, minutes=15)
    print("Pay station quote for car-1:", lot.quote(tickets["CAR-1"].ticket_id))
    receipt = lot.exit(tickets["CAR-1"].ticket_id)
    print(f"car-1 leaves after {receipt.duration}, pays {receipt.fee} (peak-hour entry)")

    clock.advance(hours=4)
    receipt = lot.exit_by_plate("TRUCK-1")  # ticketless: the exit camera read the plate
    print(f"truck-1 leaves via plate camera after {receipt.duration}, pays {receipt.fee}")
    print("Free spots:", {t.value: n for t, n in lot.availability().items()})


if __name__ == "__main__":
    demo()
