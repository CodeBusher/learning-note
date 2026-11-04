"""Competing designs for the movie booking system, side by side.

Four decision points:

1. Seat modeling:     seat objects per screening / shared layout + map / bitmap
2. Double booking:    no lock / global lock / per-screening lock /
                      temporary hold with expiry / optimistic versioning
3. Pricing:           if/else / per-seat rate objects / rule pipeline
4. Search:            linear scan / hash indexes / time-sorted list + bisect

Run ``python3 alternatives.py`` to see each comparison in action.
"""

from __future__ import annotations

import threading
import time
import tracemalloc
from bisect import bisect_left, insort
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from movie_booking import (
    Cinema,
    FormatSurcharge,
    MatineeDiscount,
    Movie,
    Room,
    RuleBasedPricing,
    Screening,
    SeatLayout,
    SeatType,
    ShowtimeIndex,
    WeekendSurcharge,
)

# ==========================================================================
# 1. Seat modeling
# ==========================================================================
SEAT_IDS = [f"{row}{n}" for row in "ABCDEFGHIJKL" for n in range(1, 26)]  # 300 seats


@dataclass
class BookableSeat:
    """Approach A: a mutable seat object that knows if it is booked."""

    seat_id: str
    seat_type: str
    is_booked: bool = False


class SeatObjectsPerScreening:
    """Approach A: every screening gets its own copy of every seat object."""

    def __init__(self, seat_ids: list[str]) -> None:
        self.seats = {s: BookableSeat(s, "standard") for s in seat_ids}

    def book(self, seat_id: str) -> bool:
        seat = self.seats[seat_id]
        if seat.is_booked:
            return False
        seat.is_booked = True
        return True

    def available(self) -> list[str]:
        return [s.seat_id for s in self.seats.values() if not s.is_booked]


class LayoutWithAvailabilityMap:
    """Approach B (recommended): shared immutable layout + a set of taken ids."""

    def __init__(self, layout_ids: tuple[str, ...]) -> None:
        self.layout_ids = layout_ids  # shared by all screenings in the room
        self.booked: set[str] = set()

    def book(self, seat_id: str) -> bool:
        if seat_id in self.booked:
            return False
        self.booked.add(seat_id)
        return True

    def available(self) -> list[str]:
        return [s for s in self.layout_ids if s not in self.booked]


class BitmapAvailability:
    """Approach C: one bit per seat in an int. Compact and fast set maths."""

    def __init__(self, layout_ids: tuple[str, ...], position: dict[str, int]) -> None:
        self.layout_ids = layout_ids
        self.position = position  # seat id -> bit number, shared like the layout
        self.bits = 0

    def book(self, seat_id: str) -> bool:
        mask = 1 << self.position[seat_id]
        if self.bits & mask:
            return False
        self.bits |= mask
        return True

    def available(self) -> list[str]:
        return [s for i, s in enumerate(self.layout_ids) if not self.bits >> i & 1]


def measure_memory(make: Callable[[], object], copies: int, sold: int = 120) -> int:
    """Bytes allocated by ``copies`` inventories with ``sold`` seats booked each."""
    tracemalloc.start()
    kept = [make() for _ in range(copies)]
    for inventory in kept:
        for seat_id in SEAT_IDS[:sold]:
            inventory.book(seat_id)
    size, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del kept
    return size


# ==========================================================================
# 2. Preventing double booking
# ==========================================================================
class Booker(Protocol):
    def book(self, screening_id: str, seat_id: str, customer: str) -> bool: ...


class NaiveBooker:
    """No locking. Check-then-act with a gap: the classic race condition."""

    def __init__(self, work_seconds: float = 0.001) -> None:
        self.booked: dict[tuple[str, str], str] = {}
        self.work_seconds = work_seconds

    def book(self, screening_id: str, seat_id: str, customer: str) -> bool:
        key = (screening_id, seat_id)
        if key in self.booked:  # check ...
            return False
        time.sleep(self.work_seconds)  # ... another thread runs here ...
        self.booked[key] = customer  # ... act (overwrites the other buyer!)
        return True


class GlobalLockBooker:
    """One lock for the whole system. Correct, but every show waits in one line."""

    def __init__(self, work_seconds: float = 0.001) -> None:
        self.booked: dict[tuple[str, str], str] = {}
        self.work_seconds = work_seconds
        self._lock = threading.Lock()

    def book(self, screening_id: str, seat_id: str, customer: str) -> bool:
        with self._lock:
            key = (screening_id, seat_id)
            if key in self.booked:
                return False
            time.sleep(self.work_seconds)
            self.booked[key] = customer
            return True


class PerScreeningLockBooker:
    """One lock per screening ("lock striping"). Shows don't block each other."""

    def __init__(self, work_seconds: float = 0.001) -> None:
        self.booked: dict[str, dict[str, str]] = defaultdict(dict)
        self.work_seconds = work_seconds
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, screening_id: str) -> threading.Lock:
        # Creating the lock must itself be atomic, or two threads could each
        # create (and use) a different lock for the same screening.
        with self._locks_guard:
            return self._locks.setdefault(screening_id, threading.Lock())

    def book(self, screening_id: str, seat_id: str, customer: str) -> bool:
        with self._lock_for(screening_id):
            seats = self.booked[screening_id]
            if seat_id in seats:
                return False
            time.sleep(self.work_seconds)
            seats[seat_id] = customer
            return True


class HoldWithExpiryBooker:
    """Reserve first (short lock), pay outside the lock, then confirm.

    A hold that is never confirmed simply expires, so an abandoned checkout
    cannot keep a seat forever.
    """

    def __init__(self, ttl: timedelta, clock: Callable[[], datetime] = datetime.now) -> None:
        self.ttl = ttl
        self.clock = clock
        self.holds: dict[tuple[str, str], tuple[str, datetime]] = {}
        self.booked: dict[tuple[str, str], str] = {}
        self._lock = threading.Lock()

    def hold(self, screening_id: str, seat_id: str, customer: str) -> bool:
        key = (screening_id, seat_id)
        with self._lock:
            if key in self.booked:
                return False
            current = self.holds.get(key)
            if current is not None and current[1] > self.clock():
                return False
            self.holds[key] = (customer, self.clock() + self.ttl)
            return True

    def confirm(self, screening_id: str, seat_id: str, customer: str) -> bool:
        key = (screening_id, seat_id)
        with self._lock:
            current = self.holds.get(key)
            if current is None or current[0] != customer or current[1] <= self.clock():
                return False
            del self.holds[key]
            self.booked[key] = customer
            return True

    def book(self, screening_id: str, seat_id: str, customer: str) -> bool:
        return self.hold(screening_id, seat_id, customer) and self.confirm(
            screening_id, seat_id, customer
        )


class OptimisticBooker:
    """No lock while working; a version check at write time detects conflicts.

    This mimics ``UPDATE screening SET ..., version = v + 1 WHERE id = ? AND
    version = v``: the write succeeds only if nobody changed the row since we
    read it. The tiny lock below plays the role of the database's atomic
    compare-and-set; it is held for microseconds, never during the "work".
    """

    def __init__(self, work_seconds: float = 0.001, max_retries: int = 50) -> None:
        self.state: dict[str, tuple[int, frozenset[str]]] = defaultdict(lambda: (0, frozenset()))
        self.owner: dict[tuple[str, str], str] = {}
        self.work_seconds = work_seconds
        self.max_retries = max_retries
        self.conflicts = 0
        self._cas_lock = threading.Lock()

    def book(self, screening_id: str, seat_id: str, customer: str) -> bool:
        for _ in range(self.max_retries):
            version, booked = self.state[screening_id]  # read a snapshot
            if seat_id in booked:
                return False
            time.sleep(self.work_seconds)  # slow work, no lock held
            with self._cas_lock:  # compare-and-set
                if self.state[screening_id][0] != version:
                    self.conflicts += 1
                    continue  # someone else wrote first: re-read and retry
                self.state[screening_id] = (version + 1, booked | {seat_id})
                self.owner[(screening_id, seat_id)] = customer
                return True
        raise RuntimeError("too much contention, giving up")


def race_for_one_seat(booker: Booker, buyers: int = 20) -> int:
    """Many threads try to book the same seat at once. Returns the winners."""
    start = threading.Barrier(buyers)
    wins: list[str] = []
    wins_lock = threading.Lock()

    def attempt(name: str) -> None:
        start.wait()  # release every thread at the same instant
        if booker.book("premiere", "F7", name):
            with wins_lock:
                wins.append(name)

    threads = [threading.Thread(target=attempt, args=(f"fan{i}",)) for i in range(buyers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return len(wins)


def time_independent_shows(booker: Booker, shows: int = 8, seats_each: int = 5) -> float:
    """Each thread books seats in its OWN screening. Measures lock contention."""

    def worker(show: int) -> None:
        for n in range(seats_each):
            booker.book(f"show{show}", f"A{n}", f"user{show}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(shows)]
    began = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - began


# ==========================================================================
# 3. Pricing
# ==========================================================================
def price_if_else(seat_type: str, start: datetime, fmt: str) -> Decimal:
    """Approach A: everything in one function. Every new rule edits this."""
    if seat_type == "vip":
        price = Decimal("24.00")
    elif seat_type == "premium":
        price = Decimal("16.00")
    else:
        price = Decimal("12.00")
    if start.hour < 16:
        price = price * Decimal("0.8")
    if start.weekday() >= 5:
        price += Decimal("2.00")
    if fmt == "IMAX":
        price += Decimal("5.00")
    return price.quantize(Decimal("0.01"))


class SeatRate(Protocol):
    def price(self) -> Decimal: ...


@dataclass(frozen=True)
class NormalRate:
    amount: Decimal = Decimal("12.00")

    def price(self) -> Decimal:
        return self.amount


@dataclass(frozen=True)
class PremiumRate:
    amount: Decimal = Decimal("16.00")

    def price(self) -> Decimal:
        return self.amount


@dataclass(frozen=True)
class VipRate:
    amount: Decimal = Decimal("24.00")

    def price(self) -> Decimal:
        return self.amount


@dataclass(frozen=True)
class SeatWithRate:
    """Approach B: each seat carries its own rate object (Strategy per seat).

    Clean for seat tiers, but the rate knows nothing about the screening, so
    time-of-day or format pricing has nowhere natural to live.
    """

    seat_id: str
    rate: SeatRate

    def price(self) -> Decimal:
        return self.rate.price()


def make_rule_pricing() -> RuleBasedPricing:
    """Approach C (recommended): seat-type table + a pipeline of rules."""
    return RuleBasedPricing(
        base_prices={
            SeatType.STANDARD: Decimal("12.00"),
            SeatType.ACCESSIBLE: Decimal("12.00"),
            SeatType.PREMIUM: Decimal("16.00"),
            SeatType.VIP: Decimal("24.00"),
        },
        rules=[MatineeDiscount(), WeekendSurcharge(), FormatSurcharge({"IMAX": Decimal("5")})],
    )


# ==========================================================================
# 4. Search
# ==========================================================================
class LinearScanCatalog:
    """Approach A: a flat list, filtered on every query. O(n) per search."""

    def __init__(self) -> None:
        self.screenings: list[Screening] = []

    def add(self, screening: Screening) -> None:
        self.screenings.append(screening)

    def search(self, movie_id: str | None = None, city: str | None = None,
               on: date | None = None) -> list[Screening]:
        return [
            s
            for s in self.screenings
            if (movie_id is None or s.movie.movie_id == movie_id)
            and (city is None or s.cinema.city.lower() == city.lower())
            and (on is None or s.start.date() == on)
        ]


class TimeSortedCatalog:
    """Approach C: screenings kept sorted by start, answered with bisect.

    Good for "what starts in the next two hours?", which hash indexes
    (approach B, ``movie_booking.ShowtimeIndex``) cannot answer directly.
    """

    def __init__(self) -> None:
        self._sorted: list[Screening] = []

    def add(self, screening: Screening) -> None:
        insort(self._sorted, screening, key=lambda s: s.start)

    def starting_between(self, begin: datetime, end: datetime) -> list[Screening]:
        lo = bisect_left(self._sorted, begin, key=lambda s: s.start)
        hi = bisect_left(self._sorted, end, key=lambda s: s.start)
        return self._sorted[lo:hi]


def build_big_catalog(n_cinemas: int = 200, shows_per_room: int = 5):
    """Create many screenings spread over cities, rooms and movies."""
    layout = SeatLayout.grid("AB", 2)
    movies = [Movie(f"m{i}", f"Movie {i}", timedelta(minutes=100)) for i in range(20)]
    cities = ["Boston", "Austin", "Denver", "Seattle", "Miami"]
    screenings = []
    for c in range(n_cinemas):
        cinema = Cinema(f"c{c}", f"Cinema {c}", cities[c % len(cities)])
        for r in range(4):
            room = Room(f"r{r}", f"Room {r}", layout)
            cinema.add_room(room)
            for k in range(shows_per_room):
                start = datetime(2026, 11, 1 + (c + k) % 7, 10 + 2 * k, 0)
                movie = movies[(c + r + k) % len(movies)]
                screenings.append(Screening(f"s{c}-{r}-{k}", movie, cinema, room, start))
    return screenings


# ==========================================================================
# Demo
# ==========================================================================
def demo() -> None:
    print("1) Seat modeling: memory for 500 screenings, 300 seats, 120 sold each")
    layout = tuple(SEAT_IDS)
    positions = {s: i for i, s in enumerate(layout)}
    for name, make in [
        ("seat objects per screening", lambda: SeatObjectsPerScreening(SEAT_IDS)),
        ("shared layout + booked set", lambda: LayoutWithAvailabilityMap(layout)),
        ("shared layout + bitmap", lambda: BitmapAvailability(layout, positions)),
    ]:
        print(f"   {name:<28} {measure_memory(make, 500) / 1024:>9,.0f} KiB")

    print("\n2) Double booking: 20 threads race for seat F7")
    for booker in [
        NaiveBooker(),
        GlobalLockBooker(),
        PerScreeningLockBooker(),
        HoldWithExpiryBooker(timedelta(minutes=5)),
        OptimisticBooker(),
    ]:
        print(f"   {type(booker).__name__:<24} winners = {race_for_one_seat(booker)}")

    print("\n   8 different shows booked in parallel (5 ms of work per booking)")
    for booker in [GlobalLockBooker(0.005), PerScreeningLockBooker(0.005), OptimisticBooker(0.005)]:
        elapsed = time_independent_shows(booker)
        print(f"   {type(booker).__name__:<24} {elapsed * 1000:6.0f} ms")

    print("\n3) Pricing a VIP seat, Saturday 13:00 IMAX (only two of three get it right)")
    sat_matinee = datetime(2026, 11, 7, 13, 0)
    print(f"   if/else:        {price_if_else('vip', sat_matinee, 'IMAX')}")
    print(f"   per-seat rate:  {SeatWithRate('D1', VipRate()).price()}  (ignores time and format!)")
    cinema = Cinema("c", "Demo", "Boston")
    room = Room("r", "IMAX", SeatLayout.grid("D", 1, {"D": SeatType.VIP}))
    show = Screening("s", Movie("m", "Orbit", timedelta(minutes=120)), cinema, room,
                     sat_matinee, "IMAX")
    print(f"   rule pipeline:  {make_rule_pricing().price(show, room.layout.seat('D1'))}")

    print("\n4) Search: 'Boston on Nov 3' over 4,000 screenings, 200 queries")
    screenings = build_big_catalog()
    linear, indexed, by_time = LinearScanCatalog(), ShowtimeIndex(), TimeSortedCatalog()
    for s in screenings:
        linear.add(s)
        indexed.add(s)
        by_time.add(s)
    for name, catalog in [("linear scan", linear), ("hash indexes", indexed)]:
        began = time.perf_counter()
        for _ in range(200):
            hits = catalog.search(city="Boston", on=date(2026, 11, 3))
        print(f"   {name:<13} {len(hits)} hits, {(time.perf_counter() - began) * 1000:6.1f} ms")
    window = by_time.starting_between(datetime(2026, 11, 3, 12), datetime(2026, 11, 3, 14))
    print(f"   time-sorted   {len(window)} shows start Nov 3 between 12:00 and 14:00")


if __name__ == "__main__":
    demo()
