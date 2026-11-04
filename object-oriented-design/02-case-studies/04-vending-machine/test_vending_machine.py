"""Unit tests for the vending machine (standard library unittest only)."""

from __future__ import annotations

import threading
import unittest
from datetime import date

from alternatives import (
    Event,
    StatusEnumMachine,
    TableDrivenMachine,
    Unit,
    UnitTrackedSlot,
    dp_change,
    find_greedy_counterexample,
    greedy_change,
    greedy_change_limited,
)
from vending_machine import (
    AuthorizationError,
    CoinBank,
    Coin,
    ExactChangeRequiredError,
    InMemoryGateway,
    InsufficientCreditError,
    InvalidStateError,
    PaymentDeclinedError,
    Product,
    SimulatedDispenser,
    Slot,
    SoldOutError,
    TelemetryLog,
    TxStatus,
    UnknownSlotError,
    VendingMachine,
    coins_value,
    make_change,
)

PIN = "2468"
COLA = Product("SKU-COLA", "Cola")
WATER = Product("SKU-WATER", "Water")


def make_machine(
    *,
    bank: dict[Coin, int] | None = None,
    cola_qty: int = 5,
    jammed: set[str] | None = None,
    balances: dict[str, int] | None = None,
) -> tuple[VendingMachine, SimulatedDispenser, InMemoryGateway, TelemetryLog]:
    dispenser = SimulatedDispenser(jammed)
    gateway = InMemoryGateway(balances or {"good": 1_000, "poor": 10})
    vm = VendingMachine(
        bank=CoinBank(bank if bank is not None else {Coin.QUARTER: 10, Coin.DIME: 10, Coin.NICKEL: 10}),
        dispenser=dispenser,
        gateway=gateway,
        service_pin=PIN,
        low_stock_threshold=1,
    )
    log = TelemetryLog()
    vm.subscribe(log)
    vm.enter_service_mode(PIN)
    vm.add_slot(Slot("A1", COLA, price_cents=125, capacity=10, quantity=cola_qty))
    vm.add_slot(Slot("A2", WATER, price_cents=100, capacity=10, quantity=0))
    vm.exit_service_mode()
    return vm, dispenser, gateway, log


class CashFlowTests(unittest.TestCase):
    def test_exact_payment_vends_with_no_change(self) -> None:
        vm, dispenser, _, _ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.QUARTER)
        result = vm.select("A1")
        self.assertTrue(result.success)
        self.assertEqual(result.product, COLA)
        self.assertEqual(result.coins_returned, {})
        self.assertEqual(vm.inventory.slot("A1").quantity, 4)
        self.assertEqual(dispenser.vended, ["A1"])
        self.assertEqual(vm.state_name, "idle")

    def test_overpayment_returns_change_and_updates_tubes(self) -> None:
        vm, *_ = make_machine()
        before = vm.coin_levels()
        for _ in range(2):
            vm.insert_coin(Coin.DOLLAR)
        result = vm.select("A1")
        self.assertEqual(coins_value(result.coins_returned), 75)
        after = vm.coin_levels()
        self.assertEqual(after[Coin.DOLLAR], before[Coin.DOLLAR] + 2)
        self.assertEqual(after[Coin.QUARTER], before[Coin.QUARTER] - 3)

    def test_credit_accumulates_and_display_shows_it(self) -> None:
        vm, *_ = make_machine()
        self.assertEqual(vm.display, "INSERT COINS OR TAP CARD")
        vm.insert_coin(Coin.QUARTER)
        vm.insert_coin(Coin.DIME)
        self.assertEqual(vm.credit_cents, 35)
        self.assertEqual(vm.display, "CREDIT $0.35")

    def test_insufficient_credit_keeps_session_open(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(InsufficientCreditError):
            vm.select("A1")
        self.assertEqual(vm.state_name, "has credit")
        vm.insert_coin(Coin.QUARTER)
        self.assertTrue(vm.select("A1").success)

    def test_cancel_refunds_inserted_coins(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.DIME)
        self.assertEqual(vm.cancel(), {Coin.DOLLAR: 1, Coin.DIME: 1})
        self.assertEqual(vm.state_name, "idle")
        self.assertEqual(vm.history()[-1].status, TxStatus.CANCELLED)

    def test_cancel_when_idle_is_harmless(self) -> None:
        vm, *_ = make_machine()
        self.assertEqual(vm.cancel(), {})

    def test_exact_change_required_when_tubes_cannot_pay(self) -> None:
        vm, *_ = make_machine(bank={})
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(ExactChangeRequiredError):
            vm.select("A1")
        self.assertEqual(vm.inventory.slot("A1").quantity, 5)
        self.assertEqual(vm.cancel(), {Coin.DOLLAR: 2})

    def test_customers_own_coins_can_pay_their_change(self) -> None:
        vm, *_ = make_machine(bank={})
        for coin in (Coin.DOLLAR, Coin.QUARTER, Coin.QUARTER):
            vm.insert_coin(coin)
        result = vm.select("A1")  # 150 for 125: one of their own quarters comes back
        self.assertEqual(result.coins_returned, {Coin.QUARTER: 1})


class SelectionErrorTests(unittest.TestCase):
    def test_select_without_credit_shows_price(self) -> None:
        vm, *_ = make_machine()
        with self.assertRaisesRegex(InsufficientCreditError, r"\$1\.25"):
            vm.select("A1")

    def test_sold_out_slot_rejected_and_credit_kept(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(SoldOutError):
            vm.select("A2")
        self.assertEqual(vm.credit_cents, 100)

    def test_unknown_slot(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(UnknownSlotError):
            vm.select("Z9")

    def test_last_unit_then_sold_out(self) -> None:
        vm, *_ = make_machine(cola_qty=1)
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.QUARTER)
        vm.select("A1")
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.QUARTER)
        with self.assertRaises(SoldOutError):
            vm.select("A1")


class CardFlowTests(unittest.TestCase):
    def test_card_purchase_captures_exact_price(self) -> None:
        vm, _, gateway, _ = make_machine()
        vm.tap_card("good")
        self.assertEqual(vm.display, "CARD READY - MAKE A SELECTION")
        result = vm.select("A1")
        self.assertTrue(result.success)
        self.assertEqual(gateway.balances["good"], 875)
        self.assertEqual(gateway.holds, {})
        self.assertEqual(vm.history()[-1].method, "card")

    def test_declined_card_does_not_vend(self) -> None:
        vm, dispenser, _, _ = make_machine()
        vm.tap_card("poor")
        with self.assertRaises(PaymentDeclinedError):
            vm.select("A1")
        self.assertEqual(dispenser.vended, [])
        self.assertEqual(vm.cancel(), {})
        self.assertEqual(vm.state_name, "idle")

    def test_coins_rejected_during_card_session(self) -> None:
        vm, *_ = make_machine()
        vm.tap_card("good")
        with self.assertRaises(InvalidStateError):
            vm.insert_coin(Coin.QUARTER)

    def test_card_rejected_during_cash_session(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.QUARTER)
        with self.assertRaises(InvalidStateError):
            vm.tap_card("good")

    def test_machine_without_reader_rejects_card(self) -> None:
        vm = VendingMachine()
        with self.assertRaises(InvalidStateError):
            vm.tap_card("good")


class VendFailureTests(unittest.TestCase):
    def test_jam_refunds_cash_and_keeps_stock(self) -> None:
        vm, _, _, log = make_machine(jammed={"A1"})
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.DOLLAR)
        result = vm.select("A1")
        self.assertFalse(result.success)
        self.assertEqual(result.coins_returned, {Coin.DOLLAR: 2})
        self.assertEqual(vm.inventory.slot("A1").quantity, 5)
        self.assertEqual(vm.history()[-1].status, TxStatus.VEND_FAILED)
        self.assertIn("vend_failed", [e for e, _ in log.events])

    def test_jam_voids_card_hold(self) -> None:
        vm, _, gateway, _ = make_machine(jammed={"A1"})
        vm.tap_card("good")
        self.assertFalse(vm.select("A1").success)
        self.assertEqual(gateway.balances["good"], 1_000)
        self.assertEqual(gateway.holds, {})


class ServiceModeTests(unittest.TestCase):
    def test_wrong_pin(self) -> None:
        vm, _, _, log = make_machine()
        with self.assertRaises(AuthorizationError):
            vm.enter_service_mode("0000")
        self.assertEqual(log.events[-1][0], "bad_pin")

    def test_admin_ops_require_service_mode(self) -> None:
        vm, *_ = make_machine()
        with self.assertRaises(InvalidStateError):
            vm.restock("A2", 3)
        with self.assertRaises(InvalidStateError):
            vm.set_price("A1", 150)

    def test_cannot_enter_service_mid_sale(self) -> None:
        vm, *_ = make_machine()
        vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(InvalidStateError):
            vm.enter_service_mode(PIN)

    def test_customer_actions_blocked_in_service_mode(self) -> None:
        vm, *_ = make_machine()
        vm.enter_service_mode(PIN)
        self.assertEqual(vm.display, "OUT OF SERVICE")
        with self.assertRaises(InvalidStateError):
            vm.insert_coin(Coin.DOLLAR)
        with self.assertRaises(InvalidStateError):
            vm.select("A1")

    def test_restock_price_and_coin_collection(self) -> None:
        vm, *_ = make_machine()
        vm.enter_service_mode(PIN)
        vm.restock("A2", 4)
        vm.set_price("A1", 150)
        with self.assertRaises(ValueError):
            vm.restock("A2", 100)  # over capacity
        collected = vm.collect_coins(keep={Coin.QUARTER: 4})
        self.assertEqual(collected, 6 * 25 + 10 * 10 + 10 * 5)
        self.assertEqual(vm.coin_levels()[Coin.QUARTER], 4)
        vm.exit_service_mode()
        self.assertEqual(vm.inventory.slot("A2").quantity, 4)
        self.assertEqual(vm.inventory.slot("A1").price_cents, 150)

    def test_low_stock_event(self) -> None:
        vm, _, _, log = make_machine(cola_qty=2)
        vm.tap_card("good")
        vm.select("A1")
        self.assertIn(("low_stock", {"slot": "A1", "quantity": 1}), log.events)


class ModelValidationTests(unittest.TestCase):
    def test_slot_rejects_bad_values(self) -> None:
        with self.assertRaises(ValueError):
            Slot("X", COLA, price_cents=0, capacity=5)
        with self.assertRaises(ValueError):
            Slot("X", COLA, price_cents=100, capacity=5, quantity=6)

    def test_duplicate_slot(self) -> None:
        vm, *_ = make_machine()
        vm.enter_service_mode(PIN)
        with self.assertRaises(ValueError):
            vm.add_slot(Slot("A1", WATER, price_cents=100, capacity=5))


class ChangeMakingTests(unittest.TestCase):
    def test_bounded_dp_beats_greedy_with_limited_tubes(self) -> None:
        tubes = {25: 1, 10: 3, 5: 0}
        self.assertIsNone(greedy_change_limited(30, tubes))
        self.assertEqual(make_change(30, tubes), {10: 3})

    def test_bounded_dp_minimises_coin_count(self) -> None:
        plan = make_change(40, {25: 5, 10: 5, 5: 5})
        self.assertEqual(plan, {25: 1, 10: 1, 5: 1})

    def test_impossible_change(self) -> None:
        self.assertIsNone(make_change(15, {10: 3}))
        self.assertEqual(make_change(0, {}), {})

    def test_greedy_fails_on_non_canonical_system(self) -> None:
        self.assertEqual(greedy_change(6, [1, 3, 4]), [4, 1, 1])
        self.assertEqual(dp_change(6, [1, 3, 4]), [3, 3])
        self.assertEqual(find_greedy_counterexample([1, 3, 4]), 6)
        self.assertIsNone(find_greedy_counterexample([1, 5, 10, 25]))

    def test_dp_matches_bruteforce_on_small_cases(self) -> None:
        denoms = [5, 10, 25]
        for amount in range(0, 120, 5):
            for limits in [(1, 1, 1), (3, 2, 1), (0, 5, 2)]:
                available = dict(zip(denoms, limits))
                best = None
                for a in range(limits[0] + 1):
                    for b in range(limits[1] + 1):
                        for c in range(limits[2] + 1):
                            if 5 * a + 10 * b + 25 * c == amount:
                                if best is None or a + b + c < best:
                                    best = a + b + c
                plan = make_change(amount, available)
                if best is None:
                    self.assertIsNone(plan)
                else:
                    assert plan is not None
                    self.assertEqual(sum(plan.values()), best)


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_coin_inserts_are_not_lost(self) -> None:
        vm, *_ = make_machine()
        threads = [threading.Thread(target=lambda: [vm.insert_coin(Coin.NICKEL) for _ in range(200)])
                   for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(vm.credit_cents, 8 * 200 * 5)

    def test_two_racing_selections_vend_once(self) -> None:
        vm, dispenser, _, _ = make_machine(cola_qty=1)
        vm.insert_coin(Coin.DOLLAR)
        vm.insert_coin(Coin.QUARTER)
        errors: list[Exception] = []

        def press() -> None:
            try:
                vm.select("A1")
            except Exception as exc:  # noqa: BLE001 - collecting for the assertion
                errors.append(exc)

        threads = [threading.Thread(target=press) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(dispenser.vended, ["A1"])
        self.assertEqual(len(errors), 1)


class AlternativeStateMachineTests(unittest.TestCase):
    def test_enum_machine(self) -> None:
        m = StatusEnumMachine({"A1": 100}, {"A1": 1})
        with self.assertRaises(RuntimeError):
            m.select("A1")
        m.insert_coin(125)
        self.assertEqual(m.select("A1"), 25)

    def test_table_machine(self) -> None:
        m = TableDrivenMachine({"A1": 100}, {"A1": 1})
        with self.assertRaises(RuntimeError):
            m.handle(Event.SELECT, "A1")
        m.handle(Event.COIN, 50)
        with self.assertRaises(RuntimeError):  # guard: not enough credit
            m.handle(Event.SELECT, "A1")
        m.handle(Event.COIN, 50)
        self.assertEqual(m.handle(Event.SELECT, "A1"), 0)
        m.handle(Event.SERVICE_OPEN)
        with self.assertRaises(RuntimeError):
            m.handle(Event.COIN, 25)

    def test_unit_tracked_slot_fifo_and_expiry(self) -> None:
        s = UnitTrackedSlot("C1", "Salad", 500)
        s.load(Unit("old", date(2026, 1, 1)))
        s.load(Unit("new", date(2026, 1, 9)))
        self.assertEqual(s.vend(date(2026, 1, 1)).lot, "old")
        with self.assertRaises(RuntimeError):
            s.vend(date(2026, 1, 10))


if __name__ == "__main__":
    unittest.main()
