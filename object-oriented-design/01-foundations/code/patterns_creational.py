"""Creational design patterns, shown on a parcel-locker scenario.

Patterns in this file:
    Simple Factory   - one function that turns a size into the right Locker class
                       (with a registry so new sizes need no edit to the factory)
    Factory Method   - a notifier whose subclasses decide which channel to create
    Abstract Factory - families of matching hardware parts (real vendor vs simulator)
    Singleton        - the classic thread-safe version, and the Pythonic alternatives
    Builder          - fluent, step-by-step construction of a validated search query

Run ``python3 patterns_creational.py`` for a short demo of each.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from typing import Self


# ===========================================================================
# Simple Factory (+ registry)
# ===========================================================================

class LockerSize(Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"


class Locker(ABC):
    """A compartment in a parcel-locker station."""

    capacity_liters: int = 0

    def __init__(self, locker_id: str) -> None:
        self.locker_id = locker_id

    def fits(self, parcel_liters: int) -> bool:
        return parcel_liters <= self.capacity_liters


_LOCKER_TYPES: dict[LockerSize, type[Locker]] = {}


def register_locker(size: LockerSize) -> Callable[[type[Locker]], type[Locker]]:
    """Class decorator: adding a size means adding a class, not editing the factory."""

    def decorator(cls: type[Locker]) -> type[Locker]:
        _LOCKER_TYPES[size] = cls
        return cls

    return decorator


@register_locker(LockerSize.SMALL)
class SmallLocker(Locker):
    capacity_liters = 10


@register_locker(LockerSize.MEDIUM)
class MediumLocker(Locker):
    capacity_liters = 30


@register_locker(LockerSize.LARGE)
class LargeLocker(Locker):
    capacity_liters = 80


def create_locker(size: LockerSize, locker_id: str) -> Locker:
    """The simple factory: callers name *what* they want, not *which class*."""
    try:
        cls = _LOCKER_TYPES[size]
    except KeyError:
        raise ValueError(f"no locker registered for {size}") from None
    return cls(locker_id)


# ===========================================================================
# Factory Method
# ===========================================================================

class Channel(ABC):
    """The *product* created by the factory method."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> str: ...


class EmailChannel(Channel):
    def send(self, recipient: str, message: str) -> str:
        return f"EMAIL to {recipient}: {message}"


class SmsChannel(Channel):
    def send(self, recipient: str, message: str) -> str:
        return f"SMS to {recipient}: {message[:160]}"  # one SMS segment


class PickupNotifier(ABC):
    """The *creator*. ``notify_pickup`` is shared; ``create_channel`` is the factory method."""

    @abstractmethod
    def create_channel(self) -> Channel: ...

    def notify_pickup(self, recipient: str, locker_id: str, code: str) -> str:
        channel = self.create_channel()
        return channel.send(recipient, f"Your parcel is in locker {locker_id}. Pickup code {code}.")


class EmailPickupNotifier(PickupNotifier):
    def create_channel(self) -> Channel:
        return EmailChannel()


class SmsPickupNotifier(PickupNotifier):
    def create_channel(self) -> Channel:
        return SmsChannel()


# ===========================================================================
# Abstract Factory
# ===========================================================================

class DoorLock(ABC):
    @abstractmethod
    def unlock(self, locker_id: str) -> str: ...


class Screen(ABC):
    @abstractmethod
    def show(self, text: str) -> str: ...


class HardwareFactory(ABC):
    """Creates a *family* of parts that must match each other."""

    @abstractmethod
    def create_lock(self) -> DoorLock: ...

    @abstractmethod
    def create_screen(self) -> Screen: ...


class VendorLock(DoorLock):
    def unlock(self, locker_id: str) -> str:
        return f"[vendor bus] solenoid {locker_id} released"


class VendorScreen(Screen):
    def show(self, text: str) -> str:
        return f"[vendor lcd] {text}"


class VendorHardware(HardwareFactory):
    def create_lock(self) -> DoorLock:
        return VendorLock()

    def create_screen(self) -> Screen:
        return VendorScreen()


class SimulatedLock(DoorLock):
    def __init__(self) -> None:
        self.opened: list[str] = []

    def unlock(self, locker_id: str) -> str:
        self.opened.append(locker_id)
        return f"[sim] {locker_id} open"


class SimulatedScreen(Screen):
    def __init__(self) -> None:
        self.lines: list[str] = []

    def show(self, text: str) -> str:
        self.lines.append(text)
        return f"[sim] {text}"


class SimulatedHardware(HardwareFactory):
    """Used in tests and on developer laptops: no real solenoids required."""

    def create_lock(self) -> DoorLock:
        return SimulatedLock()

    def create_screen(self) -> Screen:
        return SimulatedScreen()


class LockerStation:
    """Client code: it only ever talks to the abstract factory and abstract parts."""

    def __init__(self, hardware: HardwareFactory, codes: dict[str, str]) -> None:
        self.lock = hardware.create_lock()
        self.screen = hardware.create_screen()
        self._codes = codes  # pickup code -> locker id

    def enter_code(self, code: str) -> str:
        locker_id = self._codes.pop(code, None)
        if locker_id is None:
            return self.screen.show("Invalid code")
        self.lock.unlock(locker_id)
        return self.screen.show(f"Locker {locker_id} is open")


# ===========================================================================
# Singleton
# ===========================================================================

class ConfigRegistry:
    """Classic GoF singleton: every ``ConfigRegistry()`` call returns the same object.

    Double-checked locking keeps two threads from both creating an instance.
    Shown for completeness; prefer the module-level alternatives below.
    """

    _instance: ConfigRegistry | None = None
    _lock = threading.Lock()
    _settings: dict[str, str]

    def __new__(cls) -> ConfigRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._settings = {}
                    cls._instance = instance
        return cls._instance

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._settings.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._settings[key] = value

    @classmethod
    def _reset_for_tests(cls) -> None:
        cls._instance = None


@dataclass
class Settings:
    """A plain class. Nothing stops tests from creating their own instance."""

    currency: str = "USD"
    max_hold_days: int = 3
    extras: dict[str, str] = field(default_factory=dict)


# Pythonic alternative 1: a module is imported once, so a module-level object
# is already shared by every importer.
settings = Settings()


# Pythonic alternative 2: a cached accessor creates the object lazily, once.
@cache
def get_settings() -> Settings:
    return Settings()


# ===========================================================================
# Builder
# ===========================================================================

@dataclass(frozen=True, kw_only=True)
class SearchQuery:
    """An immutable, validated search request (think ``find`` with many flags)."""

    root: str
    name_pattern: str | None = None
    extensions: tuple[str, ...] = ()
    min_size: int | None = None
    max_size: int | None = None
    max_depth: int | None = None
    follow_symlinks: bool = False

    def __post_init__(self) -> None:
        if not self.root:
            raise ValueError("root is required")
        if self.min_size is not None and self.max_size is not None and self.min_size > self.max_size:
            raise ValueError("min_size cannot exceed max_size")
        if self.max_depth is not None and self.max_depth < 0:
            raise ValueError("max_depth cannot be negative")


class SearchQueryBuilder:
    """Collects options step by step, then produces one immutable ``SearchQuery``."""

    def __init__(self, root: str) -> None:
        self._fields: dict[str, object] = {"root": root}
        self._extensions: list[str] = []

    def named(self, pattern: str) -> Self:
        self._fields["name_pattern"] = pattern
        return self

    def with_extension(self, *extensions: str) -> Self:
        self._extensions.extend(e.lower().lstrip(".") for e in extensions)
        return self

    def larger_than(self, size: int) -> Self:
        self._fields["min_size"] = size
        return self

    def smaller_than(self, size: int) -> Self:
        self._fields["max_size"] = size
        return self

    def max_depth(self, depth: int) -> Self:
        self._fields["max_depth"] = depth
        return self

    def follow_symlinks(self) -> Self:
        self._fields["follow_symlinks"] = True
        return self

    def build(self) -> SearchQuery:
        return SearchQuery(extensions=tuple(self._extensions), **self._fields)  # type: ignore[arg-type]


# ===========================================================================
# Demo
# ===========================================================================

def demo() -> None:
    print("== Simple Factory ==")
    locker = create_locker(LockerSize.MEDIUM, "B-07")
    print(" ", type(locker).__name__, locker.locker_id, "fits 25 L:", locker.fits(25))

    print("== Factory Method ==")
    contacts = [(EmailPickupNotifier(), "ana@example.com"), (SmsPickupNotifier(), "+1-555-0100")]
    for notifier, recipient in contacts:
        print(" ", notifier.notify_pickup(recipient, "B-07", "481516"))

    print("== Abstract Factory ==")
    station = LockerStation(VendorHardware(), {"481516": "B-07"})
    print(" ", station.enter_code("481516"))
    print(" ", station.enter_code("000000"))

    print("== Singleton ==")
    a, b = ConfigRegistry(), ConfigRegistry()
    a.set("region", "us-east")
    print("  same object:", a is b, "| region via b:", b.get("region"))
    print("  cached accessor shared:", get_settings() is get_settings())

    print("== Builder ==")
    query = (
        SearchQueryBuilder("/var/log")
        .named("*error*")
        .with_extension(".log", "gz")
        .larger_than(1_000_000)
        .max_depth(2)
        .build()
    )
    print(" ", query)


if __name__ == "__main__":
    demo()
