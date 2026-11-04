"""Tests for patterns_behavioral, patterns_creational and patterns_structural.

Run from this folder with:  python3 -m unittest test_patterns -v
"""

from __future__ import annotations

import threading
import unittest
from decimal import Decimal

import patterns_behavioral as b
import patterns_creational as c
import patterns_structural as s


# ---------------------------------------------------------------------------
# Behavioral
# ---------------------------------------------------------------------------

class StrategyTests(unittest.TestCase):
    def test_hourly_rounds_up_with_one_hour_minimum(self) -> None:
        pricing = b.HourlyPricing(Decimal("4"))
        self.assertEqual(pricing.fee(0), Decimal("4"))
        self.assertEqual(pricing.fee(60), Decimal("4"))
        self.assertEqual(pricing.fee(61), Decimal("8"))

    def test_strategy_can_be_swapped_at_runtime(self) -> None:
        checkout = b.ParkingCheckout(b.HourlyPricing(Decimal("4")))
        self.assertEqual(checkout.charge(130), Decimal("12"))
        checkout.set_strategy(b.FlatRatePricing(Decimal("10")))
        self.assertEqual(checkout.charge(130), Decimal("10"))

    def test_first_hour_free(self) -> None:
        pricing = b.FirstHourFreePricing(Decimal("4"))
        self.assertEqual(pricing.fee(45), Decimal("0"))
        self.assertEqual(pricing.fee(130), Decimal("8"))

    def test_negative_duration_rejected(self) -> None:
        with self.assertRaises(ValueError):
            b.ParkingCheckout(b.FlatRatePricing(Decimal("1"))).charge(-5)

    def test_strategies_match_the_if_chain_they_replace(self) -> None:
        pairs = {
            "hourly": b.HourlyPricing(Decimal("4")),
            "flat": b.FlatRatePricing(Decimal("10")),
            "first_hour_free": b.FirstHourFreePricing(Decimal("4")),
        }
        for mode, strategy in pairs.items():
            for minutes in (0, 45, 60, 61, 130, 600):
                self.assertEqual(b.charge_with_if_chain(minutes, mode), strategy.fee(minutes))

    def test_if_chain_rejects_unknown_mode(self) -> None:
        with self.assertRaises(ValueError):
            b.charge_with_if_chain(30, "hourley")

    def test_functional_strategies(self) -> None:
        self.assertEqual(b.FunctionalCheckout(b.hourly(Decimal("2"))).charge(125), Decimal("6"))
        self.assertEqual(b.FunctionalCheckout(b.weekend_flat).charge(1), Decimal("15"))


class StateTests(unittest.TestCase):
    def make(self, quantity: int = 2) -> b.VendingMachine:
        return b.VendingMachine({"cola": b.Slot(price=125, quantity=quantity)})

    def test_happy_path_returns_change_and_goes_idle(self) -> None:
        machine = self.make()
        machine.insert_coin(100)
        self.assertIs(machine.state, b.HAS_MONEY)
        machine.insert_coin(100)
        self.assertEqual(machine.select("cola"), 75)
        self.assertIs(machine.state, b.IDLE)
        self.assertEqual(machine.balance, 0)

    def test_select_without_money_is_rejected(self) -> None:
        with self.assertRaises(b.InvalidAction):
            self.make().select("cola")

    def test_insufficient_balance_keeps_money(self) -> None:
        machine = self.make()
        machine.insert_coin(100)
        with self.assertRaises(b.InvalidAction):
            machine.select("cola")
        self.assertEqual(machine.balance, 100)
        self.assertIs(machine.state, b.HAS_MONEY)

    def test_refund_returns_balance(self) -> None:
        machine = self.make()
        machine.insert_coin(50)
        self.assertEqual(machine.refund(), 50)
        self.assertIs(machine.state, b.IDLE)

    def test_last_item_moves_to_sold_out(self) -> None:
        machine = self.make(quantity=1)
        machine.insert_coin(125)
        machine.select("cola")
        self.assertIs(machine.state, b.SOLD_OUT)
        with self.assertRaises(b.InvalidAction):
            machine.insert_coin(25)

    def test_empty_machine_starts_sold_out(self) -> None:
        self.assertIs(self.make(quantity=0).state, b.SOLD_OUT)

    def test_unknown_product(self) -> None:
        machine = self.make()
        machine.insert_coin(200)
        with self.assertRaises(b.InvalidAction):
            machine.select("water")

    def test_non_positive_coin_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.make().insert_coin(0)

    def test_transition_table(self) -> None:
        self.assertEqual(b.next_state("locked", "coin"), "unlocked")
        self.assertEqual(b.next_state("unlocked", "push"), "locked")
        with self.assertRaises(b.InvalidAction):
            b.next_state("broken", "coin")

    def test_reconcile_is_idempotent(self) -> None:
        desired = {"web": 3, "worker": 1}
        self.assertEqual(
            b.reconcile(desired, {"web": 1, "cron": 1}),
            ["stop 1 x cron", "start 2 x web", "start 1 x worker"],
        )
        self.assertEqual(b.reconcile(desired, desired), [])  # converged: nothing to do


class ObserverTests(unittest.TestCase):
    def test_all_observers_notified_per_floor(self) -> None:
        elevator, display, log = b.Elevator("A"), b.HallDisplay(), b.TripLogger()
        elevator.subscribe(display)
        elevator.subscribe(log)
        elevator.move_to(2)
        self.assertEqual([e.floor for e in log.events], [1, 2, 2])
        self.assertEqual(log.events[-1].direction, "idle")
        self.assertEqual(display.text, "A - 2")

    def test_unsubscribe_stops_notifications(self) -> None:
        elevator, log = b.Elevator("A"), b.TripLogger()
        elevator.subscribe(log)
        elevator.unsubscribe(log)
        elevator.move_to(3)
        self.assertEqual(log.events, [])

    def test_duplicate_subscribe_is_ignored(self) -> None:
        elevator, log = b.Elevator("A", floor=5), b.TripLogger()
        elevator.subscribe(log)
        elevator.subscribe(log)
        elevator.move_to(4)
        self.assertEqual(len(log.events), 2)

    def test_observer_may_unsubscribe_during_notify(self) -> None:
        elevator = b.Elevator("A")
        seen: list[int] = []

        class OneShot:
            def on_elevator_event(self, event: b.ElevatorEvent) -> None:
                seen.append(event.floor)
                elevator.unsubscribe(self)

        elevator.subscribe(OneShot())
        elevator.move_to(3)
        self.assertEqual(seen, [1])

    def test_signal_with_callables(self) -> None:
        signal = b.Signal()
        received: list[str] = []

        @signal.connect
        def handler(order_id: str) -> None:
            received.append(order_id)

        signal.emit("o-1")
        signal.disconnect(handler)
        signal.emit("o-2")
        self.assertEqual(received, ["o-1"])

    def test_emit_robust_isolates_failures(self) -> None:
        signal = b.Signal()
        received: list[str] = []

        def broken(order_id: str) -> None:
            raise RuntimeError("mail server down")

        signal.connect(broken)
        signal.connect(received.append)
        errors = signal.emit_robust("o-1")
        self.assertEqual(received, ["o-1"])
        self.assertEqual([str(e) for e in errors], ["mail server down"])
        with self.assertRaises(RuntimeError):
            signal.emit("o-2")  # plain emit lets the first failure stop the rest


class CommandTests(unittest.TestCase):
    def test_commands_queue_until_sent(self) -> None:
        kitchen, waiter = b.Kitchen(), b.Waiter()
        waiter.take_order(b.CookDish(kitchen, 1, "soup"))
        self.assertEqual(kitchen.tickets, [])
        self.assertEqual(waiter.send_to_kitchen(), 1)
        self.assertEqual(kitchen.tickets, ["table 1: soup"])

    def test_undo_reverses_last_command(self) -> None:
        kitchen, waiter = b.Kitchen(), b.Waiter()
        waiter.take_order(b.CookDish(kitchen, 1, "soup"))
        waiter.take_order(b.CookDish(kitchen, 1, "steak"))
        waiter.send_to_kitchen()
        waiter.undo_last()
        self.assertEqual(kitchen.tickets, ["table 1: soup"])

    def test_undo_with_empty_history(self) -> None:
        with self.assertRaises(b.InvalidAction):
            b.Waiter().undo_last()


class TemplateMethodTests(unittest.TestCase):
    def test_hand_value_soft_ace(self) -> None:
        self.assertEqual(b.hand_value([1, 6]), 17)
        self.assertEqual(b.hand_value([1, 6, 10]), 17)
        self.assertEqual(b.hand_value([1, 1]), 12)

    def test_dealer_hits_to_17(self) -> None:
        dealer = b.Dealer("d")
        dealer.cards = [6]
        deck = iter([5, 6, 9])
        self.assertEqual(dealer.play_turn(lambda: next(deck)), 17)
        self.assertFalse(dealer.busted)

    def test_cautious_player_stands_at_12_or_more(self) -> None:
        player = b.CautiousPlayer("p")
        player.cards = [2, 3]
        deck = iter([6, 10, 10])
        self.assertEqual(player.play_turn(lambda: next(deck)), 21)  # 5 -> 11 -> 21
        self.assertEqual(player.cards, [2, 3, 6, 10])

    def test_bust_sets_flag_and_calls_hook(self) -> None:
        player = b.CautiousPlayer("p")
        player.cards = [10, 10, 5]  # already over 21 when the turn starts
        self.assertEqual(player.play_turn(lambda: 1), 25)
        self.assertTrue(player.busted)
        self.assertEqual(player.messages, ["p busts!"])


class ChainOfResponsibilityTests(unittest.TestCase):
    def test_largest_notes_first(self) -> None:
        atm = b.CashDispenser({100: 2, 50: 1, 20: 5})
        self.assertEqual(atm.withdraw(290), {100: 2, 50: 1, 20: 2})
        self.assertEqual(atm.notes_left(), {100: 0, 50: 0, 20: 3})

    def test_falls_through_when_a_cassette_runs_low(self) -> None:
        atm = b.CashDispenser({100: 1, 20: 10})
        self.assertEqual(atm.withdraw(240), {100: 1, 20: 7})

    def test_failure_does_not_remove_notes(self) -> None:
        atm = b.CashDispenser({50: 1, 20: 1})
        with self.assertRaises(b.InsufficientCash):
            atm.withdraw(100)
        self.assertEqual(atm.notes_left(), {50: 1, 20: 1})

    def test_greedy_chain_limitation(self) -> None:
        # 60 = 3 x 20, but a greedy chain takes the 50 first and is left with 10.
        atm = b.CashDispenser({50: 1, 20: 3})
        with self.assertRaises(b.InsufficientCash):
            atm.withdraw(60)

    def test_invalid_amount(self) -> None:
        with self.assertRaises(ValueError):
            b.CashDispenser({20: 1}).withdraw(0)


class IteratorTests(unittest.TestCase):
    def test_scan_going_up(self) -> None:
        self.assertEqual(list(b.ScanRoute(5, [2, 9, 6, 1, 7])), [6, 7, 9, 2, 1])

    def test_scan_going_down(self) -> None:
        self.assertEqual(list(b.ScanRoute(5, [2, 9, 6, 1, 7], going_up=False)), [2, 1, 6, 7, 9])

    def test_duplicates_collapsed_and_route_reusable(self) -> None:
        route = b.ScanRoute(0, [3, 3, 1])
        self.assertEqual(list(route), [1, 3])
        self.assertEqual(list(route), [1, 3])  # a fresh generator each time

    def test_explicit_iterator_matches_and_exhausts(self) -> None:
        route = b.ScanRoute(5, [2, 9, 6])
        it = b.ExplicitScanIterator(route)
        self.assertEqual(list(it), list(route))
        with self.assertRaises(StopIteration):
            next(it)


# ---------------------------------------------------------------------------
# Creational
# ---------------------------------------------------------------------------

class SimpleFactoryTests(unittest.TestCase):
    def test_creates_right_class(self) -> None:
        locker = c.create_locker(c.LockerSize.LARGE, "L-1")
        self.assertIsInstance(locker, c.LargeLocker)
        self.assertTrue(locker.fits(80))
        self.assertFalse(c.create_locker(c.LockerSize.SMALL, "S-1").fits(11))

    def test_registry_extension_without_editing_factory(self) -> None:
        saved = dict(c._LOCKER_TYPES)
        try:
            @c.register_locker(c.LockerSize.SMALL)
            class TinyLocker(c.Locker):
                capacity_liters = 5

            self.assertIsInstance(c.create_locker(c.LockerSize.SMALL, "T"), TinyLocker)
        finally:
            c._LOCKER_TYPES.clear()
            c._LOCKER_TYPES.update(saved)

    def test_unregistered_size(self) -> None:
        saved = dict(c._LOCKER_TYPES)
        try:
            c._LOCKER_TYPES.pop(c.LockerSize.MEDIUM)
            with self.assertRaises(ValueError):
                c.create_locker(c.LockerSize.MEDIUM, "M")
        finally:
            c._LOCKER_TYPES.update(saved)


class FactoryMethodTests(unittest.TestCase):
    def test_subclass_chooses_channel(self) -> None:
        self.assertTrue(c.EmailPickupNotifier().notify_pickup("a@x.io", "B1", "1").startswith("EMAIL"))
        self.assertTrue(c.SmsPickupNotifier().notify_pickup("+1", "B1", "1").startswith("SMS"))

    def test_sms_is_truncated(self) -> None:
        self.assertLessEqual(len(c.SmsChannel().send("+1", "x" * 500)), len("SMS to +1: ") + 160)


class AbstractFactoryTests(unittest.TestCase):
    def test_simulated_family(self) -> None:
        station = c.LockerStation(c.SimulatedHardware(), {"123": "B-2"})
        station.enter_code("123")
        self.assertIsInstance(station.lock, c.SimulatedLock)
        self.assertEqual(station.lock.opened, ["B-2"])  # type: ignore[attr-defined]
        self.assertEqual(station.screen.lines, ["Locker B-2 is open"])  # type: ignore[attr-defined]

    def test_code_is_single_use(self) -> None:
        station = c.LockerStation(c.SimulatedHardware(), {"123": "B-2"})
        station.enter_code("123")
        self.assertEqual(station.enter_code("123"), "[sim] Invalid code")

    def test_vendor_family_matches(self) -> None:
        station = c.LockerStation(c.VendorHardware(), {})
        self.assertIsInstance(station.lock, c.VendorLock)
        self.assertIsInstance(station.screen, c.VendorScreen)


class SingletonTests(unittest.TestCase):
    def setUp(self) -> None:
        c.ConfigRegistry._reset_for_tests()

    def tearDown(self) -> None:
        c.ConfigRegistry._reset_for_tests()

    def test_same_instance_and_shared_state(self) -> None:
        a, b_ = c.ConfigRegistry(), c.ConfigRegistry()
        self.assertIs(a, b_)
        a.set("k", "v")
        self.assertEqual(b_.get("k"), "v")

    def test_thread_safe_creation(self) -> None:
        instances: list[c.ConfigRegistry] = []
        barrier = threading.Barrier(8)

        def make() -> None:
            barrier.wait()
            instances.append(c.ConfigRegistry())

        threads = [threading.Thread(target=make) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len({id(i) for i in instances}), 1)

    def test_module_level_alternatives(self) -> None:
        self.assertIs(c.get_settings(), c.get_settings())
        self.assertIsNot(c.Settings(), c.settings)  # still easy to make a fresh one in tests


class BuilderTests(unittest.TestCase):
    def test_fluent_build(self) -> None:
        query = c.SearchQueryBuilder("/").named("*.py").with_extension(".PY").larger_than(10).build()
        self.assertEqual(query.extensions, ("py",))
        self.assertEqual(query.min_size, 10)
        self.assertFalse(query.follow_symlinks)

    def test_validation_in_product(self) -> None:
        with self.assertRaises(ValueError):
            c.SearchQueryBuilder("/").larger_than(10).smaller_than(5).build()
        with self.assertRaises(ValueError):
            c.SearchQueryBuilder("/").max_depth(-1).build()
        with self.assertRaises(ValueError):
            c.SearchQuery(root="")

    def test_product_is_immutable(self) -> None:
        query = c.SearchQueryBuilder("/").build()
        with self.assertRaises(AttributeError):
            query.root = "/etc"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------

class AdapterTests(unittest.TestCase):
    def test_converts_dollars_to_cents_and_returns_ref(self) -> None:
        calls: list[int] = []

        class SpyGateway(s.LegacyBankGateway):
            def make_payment(self, amount_cents: int, token: str, currency: str = "USD") -> dict[str, str]:
                calls.append(amount_cents)
                return super().make_payment(amount_cents, token, currency)

        ref = s.checkout(s.LegacyBankAdapter(SpyGateway()), Decimal("19.995"), "tok")
        self.assertTrue(ref.startswith("LB-"))
        self.assertEqual(calls, [2000])

    def test_decline_becomes_exception(self) -> None:
        with self.assertRaises(s.PaymentError):
            s.LegacyBankAdapter(s.LegacyBankGateway()).charge(Decimal("0"), "tok")


class FacadeTests(unittest.TestCase):
    def test_enter_and_exit(self) -> None:
        lot = s.ParkingLotFacade(["A1"], Decimal("3"))
        ticket = lot.enter("P1", now=10)
        self.assertEqual(lot.free_spots(), 0)
        self.assertEqual(lot.exit(ticket.ticket_id, now=131), Decimal("9"))
        self.assertEqual(lot.free_spots(), 1)

    def test_full_lot_and_unknown_ticket(self) -> None:
        lot = s.ParkingLotFacade(["A1"], Decimal("3"))
        lot.enter("P1", now=0)
        with self.assertRaises(LookupError):
            lot.enter("P2", now=1)
        with self.assertRaises(LookupError):
            lot.exit(999, now=5)


class DecoratorTests(unittest.TestCase):
    def test_stacked_discounts(self) -> None:
        item = s.AmountOff(s.PercentOff(s.Product("oil", Decimal("12.50"), 2), Decimal("10")), Decimal("1"))
        self.assertEqual(item.price(), Decimal("21.50"))
        self.assertEqual(item.description(), "2 x oil [-10%] [-$1]")

    def test_order_of_decoration_matters(self) -> None:
        base = s.Product("oil", Decimal("10.00"))
        percent_then_amount = s.AmountOff(s.PercentOff(base, Decimal("50")), Decimal("2"))
        amount_then_percent = s.PercentOff(s.AmountOff(base, Decimal("2")), Decimal("50"))
        self.assertEqual(percent_then_amount.price(), Decimal("3.00"))
        self.assertEqual(amount_then_percent.price(), Decimal("4.00"))

    def test_price_never_negative(self) -> None:
        self.assertEqual(s.AmountOff(s.Product("gum", Decimal("1.00")), Decimal("5")).price(), Decimal("0.00"))

    def test_retry_function_decorator(self) -> None:
        attempts = {"n": 0}

        @s.retry(times=3, exceptions=(ConnectionError,))
        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ConnectionError
            return "ok"

        self.assertEqual(flaky(), "ok")
        self.assertEqual(flaky.__name__, "flaky")

    def test_retry_gives_up_and_ignores_other_errors(self) -> None:
        @s.retry(times=2, exceptions=(ConnectionError,))
        def always_down() -> None:
            raise ConnectionError

        with self.assertRaises(ConnectionError):
            always_down()

        calls = {"n": 0}

        @s.retry(times=5, exceptions=(ConnectionError,))
        def bug() -> None:
            calls["n"] += 1
            raise KeyError

        with self.assertRaises(KeyError):
            bug()
        self.assertEqual(calls["n"], 1)


class ProxyTests(unittest.TestCase):
    def test_caches_calls(self) -> None:
        remote = s.RemotePriceService({"milk": Decimal("3.49"), "eggs": Decimal("4.00")})
        proxy = s.CachingPriceProxy(remote)
        for _ in range(3):
            proxy.price_of("milk")
        proxy.price_of("eggs")
        self.assertEqual(remote.calls, 2)


class CompositeAndSpecificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = s.sample_tree()

    def test_size_is_recursive(self) -> None:
        self.assertEqual(self.tree.size(), 145_100)
        self.assertEqual(s.File("a.txt", 7).size(), 7)

    def test_iter_files_flattens(self) -> None:
        names = [f.name for f in self.tree.iter_files()]
        self.assertEqual(names, ["README.md", "app.py", "utils.py", "old_app.py", "logo.png", "notes.txt"])

    def test_extension(self) -> None:
        self.assertEqual(s.File("Archive.TAR.GZ", 1).extension, "gz")
        self.assertEqual(s.File("Makefile", 1).extension, "")

    def test_spec_combinators(self) -> None:
        spec = s.ExtensionIs("py") & s.LargerThan(1_000) & ~s.NameContains("old")
        self.assertEqual(s.search(self.tree, spec), ["app.py"])
        either = s.ExtensionIs("md") | s.ExtensionIs("txt")
        self.assertEqual(s.search(self.tree, either), ["README.md", "notes.txt"])

    def test_functional_predicates(self) -> None:
        pred = s.all_of(lambda f: f.extension == "py", s.any_of(lambda f: f.size() < 1_000, lambda f: "old" in f.name))
        self.assertEqual([f.name for f in self.tree.iter_files() if pred(f)], ["utils.py", "old_app.py"])


if __name__ == "__main__":
    unittest.main()
