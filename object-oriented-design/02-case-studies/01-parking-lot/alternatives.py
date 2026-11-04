"""Competing designs for the parking lot, so they can be compared side by side.

Run it with ``python3 alternatives.py``.

1. Spot allocation:   FirstAvailableScanAllocator, NearestFirstHeapAllocator,
                      PerTypeFreeListAllocator (the recommended SpotAllocator is in parking_lot.py)
2. Fee calculation:   hard_coded_fee() versus the FeePolicy strategies, plus DemandMultiplier
3. Compatibility:     a Vehicle class hierarchy, a size-ordering rule, and the table in parking_lot.py
4. Concurrency:       UnsafeSpotBoard, LockedSpotBoard, OptimisticSpotBoard
"""

from __future__ import annotations

import heapq
import threading
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from enum import IntEnum

from parking_lot import (
    CENTS,
    DEFAULT_COMPATIBILITY,
    FeePolicy,
    ParkingSpot,
    SpotType,
    Ticket,
    Vehicle,
    VehicleType,
    billable_hours,
    build_level,
)

Compatibility = Mapping[VehicleType, Sequence[SpotType]]


# ===========================================================================
# 1. Spot allocation
# ===========================================================================

class FirstAvailableScanAllocator:
    """Approach A: walk the list of spots and take the first one that is free and fits.

    O(n) per car. Trivial to write and to reason about; fine for a 50-spot lot.
    """

    def __init__(self, spots: Iterable[ParkingSpot], compatibility: Compatibility = DEFAULT_COMPATIBILITY) -> None:
        self._spots = sorted(spots, key=lambda s: s.distance)
        self._by_id = {s.spot_id: s for s in self._spots}
        self._compatibility = compatibility

    def allocate(self, vehicle: Vehicle) -> ParkingSpot | None:
        for wanted in self._compatibility.get(vehicle.vehicle_type, ()):
            for spot in self._spots:
                if spot.is_free and spot.spot_type is wanted:
                    spot.occupy(vehicle.plate)
                    return spot
        return None

    def release(self, spot_id: str) -> None:
        self._by_id[spot_id].vacate()


class NearestFirstHeapAllocator:
    """Approach B: one global min-heap of free spots ordered by distance.

    Great when every spot fits every vehicle. With mixed spot types, incompatible
    spots near the top must be popped, set aside and pushed back.
    """

    def __init__(self, spots: Iterable[ParkingSpot], compatibility: Compatibility = DEFAULT_COMPATIBILITY) -> None:
        self._by_id = {s.spot_id: s for s in spots}
        self._heap = [(s.distance, s.spot_id) for s in self._by_id.values() if s.is_free]
        heapq.heapify(self._heap)
        self._compatibility = compatibility

    def allocate(self, vehicle: Vehicle) -> ParkingSpot | None:
        allowed = set(self._compatibility.get(vehicle.vehicle_type, ()))
        skipped = []
        chosen = None
        while self._heap:
            entry = heapq.heappop(self._heap)
            if self._by_id[entry[1]].spot_type in allowed:
                chosen = self._by_id[entry[1]]
                break
            skipped.append(entry)
        for entry in skipped:
            heapq.heappush(self._heap, entry)
        if chosen is not None:
            chosen.occupy(vehicle.plate)
        return chosen

    def release(self, spot_id: str) -> None:
        spot = self._by_id[spot_id]
        spot.vacate()
        heapq.heappush(self._heap, (spot.distance, spot.spot_id))


class PerTypeFreeListAllocator:
    """Approach C: one FIFO queue of free spots per spot type.

    O(1) allocate and release, but it ignores distance: a freed spot goes to the
    back of the queue even if it is right next to the elevator.
    """

    def __init__(self, spots: Iterable[ParkingSpot], compatibility: Compatibility = DEFAULT_COMPATIBILITY) -> None:
        self._by_id = {s.spot_id: s for s in spots}
        self._free: dict[SpotType, deque[str]] = {t: deque() for t in SpotType}
        for spot in sorted(self._by_id.values(), key=lambda s: s.distance):
            if spot.is_free:
                self._free[spot.spot_type].append(spot.spot_id)
        self._compatibility = compatibility

    def allocate(self, vehicle: Vehicle) -> ParkingSpot | None:
        for wanted in self._compatibility.get(vehicle.vehicle_type, ()):
            if self._free[wanted]:
                spot = self._by_id[self._free[wanted].popleft()]
                spot.occupy(vehicle.plate)
                return spot
        return None

    def release(self, spot_id: str) -> None:
        spot = self._by_id[spot_id]
        spot.vacate()
        self._free[spot.spot_type].append(spot_id)


# ===========================================================================
# 2. Fee calculation
# ===========================================================================

def hard_coded_fee(vehicle_type: VehicleType, entry: datetime, exit_time: datetime) -> Decimal:
    """Approach A: every pricing rule written inline as if/elif branches.

    Works, and is easy to read today. Every new rule (weekend rate, event night,
    validation from the cinema next door) means editing and re-testing this function.
    """
    hours = billable_hours(exit_time - entry, timedelta(minutes=10))
    if vehicle_type is VehicleType.MOTORCYCLE:
        rate = Decimal("1.50")
    elif vehicle_type is VehicleType.TRUCK:
        rate = Decimal("6.00")
    else:
        rate = Decimal("3.00")
    fee = rate * hours
    if 7 <= entry.hour < 10:
        fee *= Decimal("1.5")
    return fee.quantize(CENTS)


class DemandMultiplier(FeePolicy):
    """Approach D (dynamic pricing): scale another policy's fee by how full the lot is.

    ``occupancy`` is a callable returning 0.0-1.0. Note the weakness: it reads
    occupancy when the driver *leaves*, so the driver could not know the price
    on the way in. Real systems lock the multiplier into the ticket or reservation.
    """

    def __init__(self, inner: FeePolicy, occupancy: Callable[[], float],
                 bands: Sequence[tuple[float, Decimal]] = ((0.9, Decimal("1.5")), (0.7, Decimal("1.2")))) -> None:
        self.inner = inner
        self.occupancy = occupancy
        self.bands = sorted(bands, reverse=True)  # highest threshold first

    def fee(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        base = self.inner.fee(ticket, exit_time)
        level = self.occupancy()
        for threshold, multiplier in self.bands:
            if level >= threshold:
                return (base * multiplier).quantize(CENTS)
        return base


# ===========================================================================
# 3. Vehicle-to-spot compatibility
# ===========================================================================

class HierarchyVehicle(ABC):
    """Approach A: each vehicle subclass decides for itself which spots it fits."""

    def __init__(self, plate: str) -> None:
        self.plate = plate

    @abstractmethod
    def allowed_spots(self) -> tuple[SpotType, ...]:
        ...

    def can_park_in(self, spot_type: SpotType) -> bool:
        return spot_type in self.allowed_spots()


class Motorcycle(HierarchyVehicle):
    def allowed_spots(self) -> tuple[SpotType, ...]:
        return (SpotType.COMPACT, SpotType.REGULAR, SpotType.OVERSIZED)


class Car(HierarchyVehicle):
    def allowed_spots(self) -> tuple[SpotType, ...]:
        return (SpotType.REGULAR, SpotType.OVERSIZED)


class ElectricCar(Car):
    def allowed_spots(self) -> tuple[SpotType, ...]:
        return (SpotType.EV_CHARGING,) + super().allowed_spots()


class Truck(HierarchyVehicle):
    def allowed_spots(self) -> tuple[SpotType, ...]:
        return (SpotType.OVERSIZED,)


class Size(IntEnum):
    """Approach B: give vehicles and spots a size and compare numbers."""

    SMALL = 1
    MEDIUM = 2
    LARGE = 3


VEHICLE_SIZE = {VehicleType.MOTORCYCLE: Size.SMALL, VehicleType.CAR: Size.MEDIUM,
                VehicleType.ELECTRIC_CAR: Size.MEDIUM, VehicleType.TRUCK: Size.LARGE}
SPOT_SIZE = {SpotType.COMPACT: Size.SMALL, SpotType.REGULAR: Size.MEDIUM,
             SpotType.EV_CHARGING: Size.MEDIUM, SpotType.OVERSIZED: Size.LARGE}


def size_fits(vehicle_type: VehicleType, spot_type: SpotType) -> bool:
    """A vehicle fits any spot at least as big as itself.

    Elegant, but it cannot say "petrol cars may not block EV chargers": the EV
    spot is MEDIUM, so a regular car fits by size alone.
    """
    return VEHICLE_SIZE[vehicle_type] <= SPOT_SIZE[spot_type]


def table_fits(vehicle_type: VehicleType, spot_type: SpotType,
               compatibility: Compatibility = DEFAULT_COMPATIBILITY) -> bool:
    """Approach C (recommended, used in parking_lot.py): look the pair up in a table."""
    return spot_type in compatibility.get(vehicle_type, ())


# ===========================================================================
# 4. Two cars grabbing the same spot
# ===========================================================================

Pause = Callable[[], None]


def _no_pause() -> None:
    pass


class UnsafeSpotBoard:
    """Approach A: check-then-act with no protection. Two threads can claim one spot."""

    def __init__(self, spot_ids: Iterable[str]) -> None:
        self.occupant: dict[str, str | None] = {s: None for s in spot_ids}
        self.claims: list[tuple[str, str]] = []  # every (spot, plate) handed out

    def claim(self, plate: str, pause: Pause = _no_pause) -> str | None:
        free = next((s for s, who in self.occupant.items() if who is None), None)
        if free is None:
            return None
        pause()  # the gap between "check" and "act" is where the race lives
        self.occupant[free] = plate
        self.claims.append((free, plate))
        return free


class LockedSpotBoard(UnsafeSpotBoard):
    """Approach B (pessimistic): hold a lock across check and act, so only one thread is inside."""

    def __init__(self, spot_ids: Iterable[str]) -> None:
        super().__init__(spot_ids)
        self._lock = threading.Lock()

    def claim(self, plate: str, pause: Pause = _no_pause) -> str | None:
        with self._lock:
            return super().claim(plate, pause)


class OptimisticSpotBoard:
    """Approach C (optimistic): read without locking, then write only if nothing changed.

    Each spot row carries a version number, like a database row. The write is a
    compare-and-set (in SQL: UPDATE ... SET occupant=?, version=version+1
    WHERE id=? AND version=?). If someone else got there first, retry.
    """

    def __init__(self, spot_ids: Iterable[str]) -> None:
        self.rows: dict[str, tuple[str | None, int]] = {s: (None, 0) for s in spot_ids}
        self.claims: list[tuple[str, str]] = []
        self.retries = 0
        self._row_lock = threading.Lock()  # stands in for the database's atomic single-row update

    def _compare_and_set(self, spot_id: str, expected_version: int, plate: str) -> bool:
        with self._row_lock:
            occupant, version = self.rows[spot_id]
            if version != expected_version or occupant is not None:
                return False
            self.rows[spot_id] = (plate, version + 1)
            self.claims.append((spot_id, plate))
            return True

    def claim(self, plate: str, pause: Pause = _no_pause, max_attempts: int = 10) -> str | None:
        for _ in range(max_attempts):
            snapshot = dict(self.rows)
            free = next((s for s, (who, _) in snapshot.items() if who is None), None)
            if free is None:
                return None
            pause()
            if self._compare_and_set(free, snapshot[free][1], plate):
                return free
            self.retries += 1
        raise RuntimeError("too much contention, giving up")


def race_two_drivers(board: UnsafeSpotBoard | OptimisticSpotBoard) -> list[tuple[str, str]]:
    """Make two threads both pass the 'check' before either 'acts', then report the claims."""
    barrier = threading.Barrier(2, timeout=0.2)

    def pause() -> None:
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass  # the other thread is blocked on a lock, or already finished: carry on

    threads = [threading.Thread(target=board.claim, args=(plate, pause)) for plate in ("CAR-A", "CAR-B")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return board.claims


# ===========================================================================
# Demo
# ===========================================================================

def demo() -> None:
    print("1. Allocation: where does each approach put a car after L1-R01 is freed?")
    for cls in (FirstAvailableScanAllocator, NearestFirstHeapAllocator, PerTypeFreeListAllocator):
        allocator = cls(build_level(1, regular=3))
        first = allocator.allocate(Vehicle("a", VehicleType.CAR))
        allocator.allocate(Vehicle("b", VehicleType.CAR))
        allocator.release(first.spot_id)
        again = allocator.allocate(Vehicle("c", VehicleType.CAR))
        print(f"   {cls.__name__:28} -> {again.spot_id}")

    print("2. Fees: hard-coded function for a car parked 08:30-10:45:",
          hard_coded_fee(VehicleType.CAR, datetime(2026, 3, 2, 8, 30), datetime(2026, 3, 2, 10, 45)))

    print("3. Compatibility: may a petrol car use an EV charger?")
    print("   class hierarchy:", Car("x").can_park_in(SpotType.EV_CHARGING))
    print("   size ordering:  ", size_fits(VehicleType.CAR, SpotType.EV_CHARGING))
    print("   table lookup:   ", table_fits(VehicleType.CAR, SpotType.EV_CHARGING))

    print("4. Two cars racing for a two-spot board:")
    for board in (UnsafeSpotBoard(["S1", "S2"]), LockedSpotBoard(["S1", "S2"]), OptimisticSpotBoard(["S1", "S2"])):
        claims = race_two_drivers(board)
        spots = [spot for spot, _ in claims]
        verdict = "DOUBLE-BOOKED" if len(set(spots)) < len(spots) else "ok"
        print(f"   {type(board).__name__:20} claims={claims} -> {verdict}")


if __name__ == "__main__":
    demo()
