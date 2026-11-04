"""Tests for the ATM case study. Run: python3 -m unittest discover -s <this folder> -v"""

from __future__ import annotations

import threading
import unittest
from datetime import date, timedelta
from decimal import Decimal

from alternatives import (
    CommandJournal,
    DepositCommand,
    IfElseATM,
    JammingDispenser,
    Phase,
    TinyBank,
    WithdrawCommand,
    chain_plan,
    debit_then_dispense_naive,
    debit_then_dispense_with_reversal,
    dispense_then_debit,
    greedy_plan,
    hold_then_capture,
)
from atm import (
    ATM,
    AccountType,
    AuthResult,
    BankUnavailable,
    CashCassettes,
    FakeDispenser,
    InMemoryBank,
    PinVault,
    RecordingCardReader,
    RecordingDisplay,
    Status,
)

CARD = "4000-0001"
PIN = "2468"
CHK = AccountType.CHECKING
SAV = AccountType.SAVINGS


class Clock:
    def __init__(self) -> None:
        self.day = date(2026, 1, 1)

    def __call__(self) -> date:
        return self.day


def make_bank(clock: Clock | None = None, daily_limit: str = "500") -> InMemoryBank:
    bank = InMemoryBank(daily_limit=Decimal(daily_limit), today=clock or Clock())
    bank.issue_card(CARD, PIN)
    bank.open_account(CARD, CHK, "CHK-1", Decimal("1000"))
    bank.open_account(CARD, SAV, "SAV-1", Decimal("100"))
    return bank


def make_atm(bank=None, cassettes=None, dispenser=None, atm_id="ATM-1") -> ATM:
    return ATM(
        atm_id,
        bank or make_bank(),
        CashCassettes(cassettes or {50: 10, 20: 50}),
        RecordingCardReader(),
        dispenser or FakeDispenser(),
        RecordingDisplay(),
    )


def logged_in(atm: ATM) -> ATM:
    atm.insert_card(CARD)
    atm.enter_pin(PIN)
    return atm


class PinVaultTests(unittest.TestCase):
    def test_record_does_not_contain_raw_pin(self) -> None:
        record = PinVault().enroll("2468")
        self.assertNotIn(b"2468", record.salt + record.digest)

    def test_verify_right_and_wrong_pin(self) -> None:
        vault = PinVault()
        record = vault.enroll("2468")
        self.assertTrue(vault.verify("2468", record))
        self.assertFalse(vault.verify("2469", record))

    def test_same_pin_gets_different_digests(self) -> None:
        vault = PinVault()
        self.assertNotEqual(vault.enroll("1111").digest, vault.enroll("1111").digest)

    def test_other_vault_key_cannot_verify(self) -> None:
        record = PinVault(b"k" * 32).enroll("2468")
        self.assertFalse(PinVault(b"x" * 32).verify("2468", record))

    def test_rejects_malformed_pin(self) -> None:
        with self.assertRaises(ValueError):
            PinVault().enroll("12a4")


class SessionStateTests(unittest.TestCase):
    def test_happy_path_states(self) -> None:
        atm = make_atm()
        self.assertEqual(atm.state, "idle")
        atm.insert_card(CARD)
        self.assertEqual(atm.state, "card inserted")
        atm.enter_pin(PIN)
        self.assertEqual(atm.state, "authenticated")
        atm.eject_card()
        self.assertEqual(atm.state, "idle")
        self.assertEqual(atm.card_reader.ejected, [CARD])

    def test_transaction_before_pin_is_rejected(self) -> None:
        atm = make_atm()
        atm.insert_card(CARD)
        self.assertIsNone(atm.withdraw(CHK, 20))
        self.assertIn("PIN", atm.display.last)

    def test_pin_without_card_is_rejected(self) -> None:
        atm = make_atm()
        atm.enter_pin(PIN)
        self.assertEqual(atm.state, "idle")
        self.assertIn("insert", atm.display.last.lower())

    def test_second_card_rejected_while_busy(self) -> None:
        atm = logged_in(make_atm())
        atm.insert_card("other")
        self.assertEqual(atm.card_number, CARD)

    def test_eject_while_idle_is_harmless(self) -> None:
        atm = make_atm()
        atm.eject_card()
        self.assertEqual(atm.card_reader.ejected, [])

    def test_unknown_card_is_ejected(self) -> None:
        atm = make_atm()
        atm.insert_card("9999")
        atm.enter_pin("1234")
        self.assertEqual(atm.state, "idle")
        self.assertEqual(atm.card_reader.ejected, ["9999"])

    def test_three_wrong_pins_retain_card(self) -> None:
        atm = make_atm()
        atm.insert_card(CARD)
        atm.enter_pin("0000")
        atm.enter_pin("0001")
        self.assertEqual(atm.state, "card inserted")
        atm.enter_pin("0002")
        self.assertEqual(atm.state, "idle")
        self.assertEqual(atm.card_reader.retained, [CARD])
        self.assertEqual(atm.card_reader.ejected, [])

    def test_try_counter_survives_moving_to_another_atm(self) -> None:
        bank = make_bank()
        first = make_atm(bank)
        first.insert_card(CARD)
        first.enter_pin("0000")
        first.enter_pin("0001")
        first.eject_card()
        second = make_atm(bank, atm_id="ATM-2")
        second.insert_card(CARD)
        second.enter_pin("0002")
        self.assertEqual(second.card_reader.retained, [CARD])
        # Even the right PIN no longer works once the card is blocked.
        self.assertIs(bank.authorize_pin(CARD, PIN), AuthResult.RETAIN_CARD)

    def test_correct_pin_resets_counter(self) -> None:
        bank = make_bank()
        for _ in range(2):
            bank.authorize_pin(CARD, "0000")
        self.assertIs(bank.authorize_pin(CARD, PIN), AuthResult.APPROVED)
        self.assertIs(bank.authorize_pin(CARD, "0000"), AuthResult.WRONG_PIN)

    def test_events_during_transaction_are_rejected(self) -> None:
        seen: list[str] = []

        class ImpatientDispenser(FakeDispenser):
            def dispense(self, notes) -> None:
                seen.append(atm.state)
                atm.eject_card()  # customer mashes "cancel" mid-dispense
                super().dispense(notes)

        atm = logged_in(make_atm(dispenser=ImpatientDispenser()))
        result = atm.withdraw(CHK, 40)
        self.assertTrue(result.ok)
        self.assertEqual(seen, ["transaction"])
        self.assertEqual(atm.card_reader.ejected, [])
        self.assertEqual(atm.state, "authenticated")


class TransactionTests(unittest.TestCase):
    def test_balance_inquiry(self) -> None:
        atm = logged_in(make_atm())
        self.assertEqual(atm.check_balance(SAV).balance, Decimal("100"))

    def test_withdraw_debits_and_dispenses(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank))
        result = atm.withdraw(CHK, 120)
        self.assertTrue(result.ok)
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("880"))
        self.assertEqual(sum(atm.dispenser.presented), 120)
        self.assertEqual(atm.cassettes.counts, {50: 8, 20: 49})

    def test_insufficient_funds(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank))
        result = atm.withdraw(SAV, 120)
        self.assertFalse(result.ok)
        self.assertIn("insufficient", result.message)
        self.assertEqual(bank.account_balance("SAV-1"), Decimal("100"))
        self.assertEqual(atm.dispenser.presented, [])

    def test_amount_machine_cannot_pay_never_reaches_bank(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank))
        result = atm.withdraw(CHK, 35)
        self.assertFalse(result.ok)
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("1000"))

    def test_daily_limit(self) -> None:
        clock = Clock()
        bank = make_bank(clock, daily_limit="300")
        atm = logged_in(make_atm(bank))
        self.assertTrue(atm.withdraw(CHK, 200).ok)
        self.assertIn("limit", atm.withdraw(CHK, 120).message)
        clock.day += timedelta(days=1)
        self.assertTrue(atm.withdraw(CHK, 120).ok)

    def test_deposit_credits_and_refills_cassettes(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank))
        result = atm.deposit(SAV, {20: 3, 50: 1})
        self.assertTrue(result.ok)
        self.assertEqual(bank.account_balance("SAV-1"), Decimal("210"))
        self.assertEqual(atm.cassettes.counts, {50: 11, 20: 53})

    def test_empty_deposit(self) -> None:
        atm = logged_in(make_atm())
        self.assertFalse(atm.deposit(SAV, {}).ok)

    def test_journal_records_unique_keys(self) -> None:
        atm = logged_in(make_atm())
        atm.check_balance(CHK)
        atm.withdraw(CHK, 20)
        keys = [key for key, _, _ in atm.journal]
        self.assertEqual(keys, ["ATM-1-000001", "ATM-1-000002"])


class ConsistencyTests(unittest.TestCase):
    def test_full_jam_reverses_debit(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank, dispenser=FakeDispenser(jam_after=0)))
        result = atm.withdraw(CHK, 100)
        self.assertFalse(result.ok)
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("1000"))
        self.assertEqual(atm.cassettes.counts, {50: 10, 20: 50})

    def test_partial_jam_charges_only_what_came_out(self) -> None:
        bank = make_bank()
        atm = logged_in(make_atm(bank, dispenser=FakeDispenser(jam_after=1)))
        atm.withdraw(CHK, 100)  # planned as 2 x 50, only one is presented
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("950"))
        self.assertEqual(atm.cassettes.counts[50], 9)

    def test_jam_also_restores_daily_limit(self) -> None:
        bank = make_bank(daily_limit="100")
        atm = logged_in(make_atm(bank, dispenser=FakeDispenser(jam_after=0)))
        atm.withdraw(CHK, 100)
        atm.dispenser.jam_after = None
        self.assertTrue(atm.withdraw(CHK, 100).ok)

    def test_timeout_after_apply_is_reversed(self) -> None:
        real = make_bank()

        class TimesOutAfterApplying:
            def __getattr__(self, name):
                return getattr(real, name)

            def withdraw(self, *args):
                real.withdraw(*args)  # the bank applied it...
                raise BankUnavailable  # ...but the answer was lost

        atm = logged_in(make_atm(TimesOutAfterApplying()))
        result = atm.withdraw(CHK, 100)
        self.assertFalse(result.ok)
        self.assertEqual(real.account_balance("CHK-1"), Decimal("1000"))
        self.assertEqual(atm.dispenser.presented, [])

    def test_timeout_before_apply_blocks_late_original(self) -> None:
        bank = make_bank()
        # Reversal arrives first; the delayed original must then be refused.
        self.assertFalse(bank.reverse("ATM-1-000001"))
        late = bank.withdraw(CARD, CHK, Decimal("100"), "ATM-1-000001")
        self.assertIs(late.status, Status.ALREADY_REVERSED)
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("1000"))

    def test_retry_with_same_key_is_idempotent(self) -> None:
        bank = make_bank()
        first = bank.withdraw(CARD, CHK, Decimal("100"), "k-1")
        second = bank.withdraw(CARD, CHK, Decimal("100"), "k-1")
        self.assertEqual(first, second)
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("900"))

    def test_reversal_is_idempotent(self) -> None:
        bank = make_bank()
        bank.withdraw(CARD, CHK, Decimal("100"), "k-1")
        self.assertTrue(bank.reverse("k-1"))
        self.assertFalse(bank.reverse("k-1"))
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("1000"))

    def test_deposit_reversal(self) -> None:
        bank = make_bank()
        bank.deposit(CARD, SAV, Decimal("40"), "d-1")
        bank.reverse("d-1")
        self.assertEqual(bank.account_balance("SAV-1"), Decimal("100"))

    def test_concurrent_withdrawals_never_overdraw(self) -> None:
        bank = make_bank(daily_limit="100000")
        approved: list[bool] = []
        lock = threading.Lock()

        def worker(n: int) -> None:
            response = bank.withdraw(CARD, CHK, Decimal("30"), f"t-{n}")
            with lock:
                approved.append(response.approved)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(approved.count(True), 33)  # 33 * 30 = 990 <= 1000
        self.assertEqual(bank.account_balance("CHK-1"), Decimal("10"))


class DispensingTests(unittest.TestCase):
    def test_dp_finds_plan_greedy_misses(self) -> None:
        counts = {50: 1, 20: 3}
        self.assertIsNone(greedy_plan(60, counts))
        self.assertIsNone(chain_plan(60, counts))
        self.assertEqual(CashCassettes(counts).plan(60), {20: 3})

    def test_dp_uses_fewest_notes(self) -> None:
        self.assertEqual(CashCassettes({50: 5, 20: 5, 10: 5}).plan(80), {50: 1, 20: 1, 10: 1})

    def test_dp_respects_counts(self) -> None:
        self.assertIsNone(CashCassettes({20: 2}).plan(60))

    def test_dp_rejects_nonpositive(self) -> None:
        self.assertIsNone(CashCassettes({20: 2}).plan(0))

    def test_greedy_and_chain_agree_when_stock_is_plentiful(self) -> None:
        counts = {50: 100, 20: 100, 10: 100}
        for amount in range(10, 500, 10):
            self.assertEqual(greedy_plan(amount, counts), chain_plan(amount, counts))
            self.assertEqual(greedy_plan(amount, counts), CashCassettes(counts).plan(amount))

    def test_remove_more_than_loaded_raises(self) -> None:
        with self.assertRaises(ValueError):
            CashCassettes({20: 1}).remove({20: 2})


class AlternativeTests(unittest.TestCase):
    def test_if_else_atm_flow(self) -> None:
        atm = IfElseATM("2468")
        atm.insert_card()
        atm.enter_pin("2468")
        self.assertIs(atm.phase, Phase.AUTHENTICATED)
        atm.eject_card()
        self.assertIs(atm.phase, Phase.IDLE)

    def test_command_journal_undo(self) -> None:
        bank = TinyBank(Decimal("100"))
        journal = CommandJournal(bank)
        journal.run(WithdrawCommand("a", Decimal("30")))
        journal.run(DepositCommand("b", Decimal("5")))
        self.assertTrue(journal.reverse("a"))
        self.assertEqual(bank.balance, Decimal("105"))
        self.assertFalse(journal.reverse("missing"))

    def test_ordering_strategies_on_jam(self) -> None:
        results = {}
        for strategy in (debit_then_dispense_naive, debit_then_dispense_with_reversal, hold_then_capture):
            bank = TinyBank(Decimal("100"))
            strategy(bank, JammingDispenser(jam=True), "k", Decimal("40"))
            results[strategy.__name__] = bank.balance
        self.assertEqual(results["debit_then_dispense_naive"], Decimal("60"))
        self.assertEqual(results["debit_then_dispense_with_reversal"], Decimal("100"))
        self.assertEqual(results["hold_then_capture"], Decimal("100"))

    def test_dispense_first_loses_cash_on_timeout(self) -> None:
        bank = TinyBank(Decimal("100"), fail_next=True)
        dispenser = JammingDispenser(jam=False)
        dispense_then_debit(bank, dispenser, "k", Decimal("40"))
        self.assertEqual((bank.balance, dispenser.cash_out), (Decimal("100"), Decimal("40")))

    def test_hold_blocks_overspending(self) -> None:
        bank = TinyBank(Decimal("100"))
        self.assertTrue(bank.hold("a", Decimal("80")))
        self.assertFalse(bank.hold("b", Decimal("30")))


if __name__ == "__main__":
    unittest.main()
