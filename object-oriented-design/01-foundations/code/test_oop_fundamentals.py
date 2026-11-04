"""Tests for the OOP fundamentals examples.

Run from inside code/:  python3 -m unittest test_oop_fundamentals -v
"""
from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import unittest
from datetime import date
from decimal import Decimal

import oop_basics as b
import oop_domain_modeling as dm
import oop_internals as i
import oop_pillars as p
import oop_relationships as r
import oop_solid as s

D = Decimal


class EncapsulationTests(unittest.TestCase):
    def test_procedural_dict_allows_invalid_state(self) -> None:
        acct = p.proc_open_account("ana")
        acct["balance"] = D("-999")  # the problem OOP solves
        self.assertEqual(acct["balance"], D("-999"))

    def test_balance_has_no_setter(self) -> None:
        a = p.BankAccount("ana")
        with self.assertRaises(AttributeError):
            a.balance = D("10")  # type: ignore[misc]

    def test_overdraft_limit_enforced(self) -> None:
        a = p.BankAccount("ana", overdraft_limit=D("20"))
        a.deposit(D("10"))
        a.withdraw(D("30"))
        self.assertEqual(a.balance, D("-20"))
        with self.assertRaises(p.InsufficientFunds):
            a.withdraw(D("0.01"))

    def test_property_setter_validates(self) -> None:
        with self.assertRaises(ValueError):
            p.BankAccount("ana", overdraft_limit=D("-1"))

    def test_history_is_a_copy(self) -> None:
        a = p.BankAccount("ana")
        a.deposit(D("5"))
        self.assertIsInstance(a.history, tuple)
        self.assertEqual(len(a.history), 1)

    def test_rejects_non_positive_amounts(self) -> None:
        with self.assertRaises(ValueError):
            p.BankAccount("ana").deposit(D("0"))

    def test_frozen_account_blocks_movement(self) -> None:
        a = p.BankAccount("ana")
        a.freeze()
        with self.assertRaises(p.AccountFrozen):
            a.deposit(D("1"))

    def test_name_mangling_keeps_subclass_attribute_separate(self) -> None:
        sa = p.SavingsAccount("ben", D("0.12"))
        sa.deposit(D("100"))
        self.assertEqual(sa.balance, D("100"))
        self.assertIn("_SavingsAccount__balance", vars(sa))
        self.assertEqual(sa.add_monthly_interest(), D("1.00"))
        self.assertEqual(sa.balance, D("101.00"))


class AbstractionPolymorphismTests(unittest.TestCase):
    def test_abc_cannot_be_instantiated(self) -> None:
        with self.assertRaises(TypeError):
            p.PaymentGateway()  # type: ignore[abstract]

    def test_base_class_validation_shared_by_subclasses(self) -> None:
        for gw in (p.CardGateway(), p.BankTransferGateway()):
            with self.assertRaises(ValueError):
                gw.charge(D("0"), "tok")
            with self.assertRaises(ValueError):
                gw.charge(D("1"), "")

    def test_protocol_accepts_unrelated_class(self) -> None:
        wallet = p.GiftCardWallet(D("10"))
        self.assertIsInstance(wallet, p.SupportsCharge)
        self.assertNotIsInstance(wallet, p.PaymentGateway)
        receipt = p.checkout(wallet, D("4"), "x")
        self.assertEqual((receipt.gateway, wallet.credit), ("gift_card", D("6")))

    def test_receipts_are_immutable(self) -> None:
        receipt = p.CardGateway().charge(D("5"), "tok")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            receipt.amount = D("500")  # type: ignore[misc]

    def test_singledispatch_picks_by_type(self) -> None:
        self.assertEqual(p.describe(7), "the integer 7")
        self.assertEqual(p.describe(True), "the integer True")  # bool is an int
        self.assertEqual(p.describe(1.5), "something of type float")


class MixinAndDunderTests(unittest.TestCase):
    def test_mro_order(self) -> None:
        names = [c.__name__ for c in p.CustomerRecord.__mro__]
        self.assertEqual(names, ["CustomerRecord", "JsonMixin", "RedactMixin",
                                 "TypeTagMixin", "Serializable", "object"])

    def test_every_mixin_in_the_chain_runs(self) -> None:
        data = json.loads(p.CustomerRecord("ana", "4111").to_json())
        self.assertEqual(data, {"name": "ana", "card_number": "***",
                                "_type": "CustomerRecord"})

    def test_sequence_abc_supplies_methods(self) -> None:
        pl = p.Playlist("x", [p.Track("a", 1), p.Track("b", 2), p.Track("a", 1)])
        self.assertEqual(len(pl), 3)
        self.assertIn(p.Track("b", 2), pl)
        self.assertEqual(pl.count(p.Track("a", 1)), 2)
        self.assertEqual(pl.index(p.Track("b", 2)), 1)
        self.assertIsInstance(pl[0:2], p.Playlist)
        self.assertEqual(pl.duration, 4)

    def test_add_and_eq(self) -> None:
        a = p.Playlist("a", [p.Track("x", 1)])
        b = p.Playlist("b", [p.Track("y", 2)])
        self.assertEqual(a + b, p.Playlist("other name", [p.Track("x", 1), p.Track("y", 2)]))
        with self.assertRaises(TypeError):
            a + 5  # type: ignore[operator]
        with self.assertRaises(TypeError):
            hash(a)

    def test_dataclass_ordering_ignores_non_compare_fields(self) -> None:
        self.assertEqual(p.Ticket(1, "a"), p.Ticket(1, "b"))
        self.assertLess(p.Ticket(1, "z"), p.Ticket(2, "a"))


class RelationshipTests(unittest.TestCase):
    def test_composition_and_dependency(self) -> None:
        order = r.Order("o1", r.Customer("c1", "Ana"))
        order.add_line("mug", D("10"), 2)
        self.assertEqual(order.total(r.FlatTax(D("0.10"))), D("22.00"))
        with self.assertRaises(ValueError):
            order.add_line("mug", D("10"), 0)
        self.assertIsInstance(order.lines, tuple)

    def test_inheritance_overrides_subtotal(self) -> None:
        order = r.ExpressOrder("o2", r.Customer("c1", "Ana"))
        order.add_line("mug", D("10"))
        self.assertEqual(order.subtotal(), D("19.99"))

    def test_realization(self) -> None:
        order = r.Order("o3", r.Customer("c1", "Ana"))
        order.add_line("tea", D("8"))
        self.assertIn("Invoice o3 for Ana", r.PlainTextInvoice().render(order))

    def test_aggregation_members_outlive_team(self) -> None:
        bo = r.Employee("bo")
        team = r.Team("t", [bo])
        members = team.members
        del team
        self.assertIs(members[0], bo)

    def test_fragile_base_class_double_counts(self) -> None:
        inherited = r.CountingTagSetInherited()
        inherited.add_many(["a", "b"])
        self.assertEqual(inherited.attempts, 4)  # the bug

    def test_composition_counts_correctly(self) -> None:
        composed = r.CountingTagSet()
        composed.add_many(["a", "b"])
        composed.add("c")
        self.assertEqual((composed.attempts, len(composed)), (3, 3))

    def test_dict_subclass_override_is_bypassed(self) -> None:
        d = r.LowerKeyDict({"A": 1})
        d.update({"B": 2})
        self.assertEqual(set(d), {"A", "B"})
        u = r.LowerKeyUserDict({"A": 1})
        u.update({"B": 2})
        self.assertEqual(set(u), {"a", "b"})

    def test_composed_report_and_mixin(self) -> None:
        rows = [{"k": 1}]
        dest = r.MemoryDestination()
        uri = r.Report("x.json", r.JsonFormatter(), dest).publish(rows)
        self.assertEqual((uri, dest.files["x.json"]), ("memory://x.json", '[{"k": 1}]'))
        self.assertEqual(r.CountedCsvExporter(rows).summary(), "CountedCsvExporter: 1 rows")
        self.assertEqual(r.CsvToMemoryExporter(rows).export(), r.CsvFormatter().format(rows))


class SolidTests(unittest.TestCase):
    def test_srp_before_and_after_agree(self) -> None:
        raw = [("kb", D("80"), 1), ("cable", D("12"), 2)]
        items = [s.LineItem(*t) for t in raw]
        mailer = s.InvoiceMailer()
        after = s.InvoiceService(s.InvoiceCalculator(), s.InvoiceFormatter(), mailer)
        self.assertEqual(s.InvoiceServiceBefore().process("a@x.io", raw),
                         after.process("a@x.io", items))
        self.assertEqual(mailer.outbox[0][0], "a@x.io")

    def test_srp_calculator_alone(self) -> None:
        self.assertEqual(s.InvoiceCalculator().total([s.LineItem("x", D("50"), 1)]), D("50.00"))

    def test_ocp_new_rate_without_editing_calculator(self) -> None:
        calc = s.ShippingCalculator([s.LinearRate("ground", D("5"), D("0.5"))])
        self.assertEqual(calc.cost("ground", D("4")), s.shipping_cost_before("ground", D("4")))
        calc.register(s.TieredRate("locker", ((D("2"), D("3")),)))
        self.assertEqual(calc.cost("locker", D("1")), D("3"))
        with self.assertRaises(ValueError):
            calc.cost("locker", D("5"))
        with self.assertRaises(ValueError):
            calc.cost("drone", D("1"))

    def test_lsp_violation_and_fix(self) -> None:
        with self.assertRaises(NotImplementedError):
            s.pay_rent_before(s.FixedDepositBefore(D("100")), D("10"))
        acct = s.CheckingAccount(D("100"))
        s.pay_rent(acct, D("10"))
        self.assertEqual(acct.balance, D("90"))
        self.assertFalse(hasattr(s.FixedDeposit(D("1"), 6), "withdraw"))
        self.assertEqual(s.total_assets([acct, s.FixedDeposit(D("10"), 6)]), D("100"))

    def test_isp(self) -> None:
        with self.assertRaises(NotImplementedError):
            s.CheapPrinterBefore().scan()
        self.assertEqual(s.print_payslips(s.CheapPrinter(), ["a"]), ["printed payslip-a"])
        self.assertEqual(s.archive_contract(s.MultiFunctionPrinter()), "archived scan.pdf")

    def test_dip_injected_fake(self) -> None:
        fake = s.InMemoryNotifier()
        svc = s.SignupService(fake)
        svc.register("a@x.io")
        self.assertEqual(fake.sent, [("a@x.io", "Welcome!")])
        with self.assertRaises(ValueError):
            svc.register("a@x.io")

    def test_dip_before_is_welded_to_smtp(self) -> None:
        self.assertIsInstance(s.SignupServiceBefore().mailer, s.SmtpMailer)


class DomainModelingTests(unittest.TestCase):
    def test_money_equality_rounding_and_hash(self) -> None:
        a = dm.Money(D("1.005"), "USD")
        self.assertEqual(a, dm.Money(D("1.00"), "USD"))  # banker's rounding
        self.assertEqual(len({a, dm.Money(D("1"), "USD")}), 1)

    def test_money_validation(self) -> None:
        with self.assertRaises(TypeError):
            dm.Money(1.5, "USD")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            dm.Money(D("1"), "usd")
        with self.assertRaises(dm.CurrencyMismatch):
            dm.Money(D("1"), "USD") + dm.Money(D("1"), "EUR")

    def test_money_is_immutable_and_arithmetic_returns_new(self) -> None:
        a = dm.Money(D("2"), "USD")
        b = a * 3
        self.assertEqual((a.amount, b.amount), (D("2.00"), D("6.00")))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.amount = D("5")  # type: ignore[misc]
        self.assertEqual((b - a).amount, D("4.00"))

    def test_email_value_object(self) -> None:
        e = dm.EmailAddress(" Bo@Shop.IO ")
        self.assertEqual((e.value, e.domain), ("bo@shop.io", "shop.io"))
        with self.assertRaises(ValueError):
            dm.EmailAddress("not-an-email")

    def test_entity_identity(self) -> None:
        w = dm.Wallet(dm.Money(D("1"), "USD"))
        a = dm.Customer("c1", "A", dm.EmailAddress("a@x.io"), w)
        b = dm.Customer("c1", "B", dm.EmailAddress("b@x.io"), w)
        c = dm.Customer("c2", "A", dm.EmailAddress("a@x.io"), w)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len({a, b, c}), 2)

    def test_tell_dont_ask(self) -> None:
        c = dm.Customer("c1", "A", dm.EmailAddress("a@x.io"), dm.Wallet(dm.Money(D("10"), "USD")))
        dm.checkout_tell(c, dm.Money(D("4"), "USD"))
        self.assertTrue(c.can_afford(dm.Money(D("6"), "USD")))
        with self.assertRaises(ValueError):
            dm.checkout_tell(c, dm.Money(D("7"), "USD"))

    def test_demeter_violation_skips_currency_check(self) -> None:
        # The "ask" version compares raw amounts (no currency check); only the
        # later subtraction, which goes back through Money, catches the mistake.
        c = dm.Customer("c1", "A", dm.EmailAddress("a@x.io"), dm.Wallet(dm.Money(D("10"), "USD")))
        with self.assertRaises(dm.CurrencyMismatch):
            dm.checkout_demeter_violation(c, dm.Money(D("4"), "EUR"))

    def test_shallow_vs_deep_immutability(self) -> None:
        shallow = dm.ShallowConfig("eu", ["1"])
        shallow.allowed_ips.append("2")
        self.assertEqual(shallow.allowed_ips, ["1", "2"])
        deep = dm.DeepConfig("eu", ("1",))
        newer = deep.with_ip("2")
        self.assertEqual((deep.allowed_ips, newer.allowed_ips), (("1",), ("1", "2")))

    def test_rich_model_enforces_transitions(self) -> None:
        sub = dm.Subscription(dm.Money(D("5"), "USD"))
        sub.activate()
        sub.cancel(date(2026, 1, 1))
        self.assertEqual((sub.status, sub.cancelled_on), (dm.SubStatus.CANCELLED, date(2026, 1, 1)))
        with self.assertRaises(ValueError):
            sub.activate()
        with self.assertRaises(ValueError):
            sub.cancel(date(2026, 1, 2))

    def test_anemic_model_cannot_protect_itself(self) -> None:
        sub = dm.AnemicSubscription()
        dm.SubscriptionService().cancel(sub, date(2026, 1, 1))
        sub.status = dm.SubStatus.ACTIVE  # nothing prevents an illegal jump
        self.assertIs(sub.status, dm.SubStatus.ACTIVE)


class BasicsTests(unittest.TestCase):
    def setUp(self) -> None:
        importlib.reload(b)  # the parallel-list script keeps module-level state

    def test_parallel_lists_misalign_after_removal(self) -> None:
        b.discontinue("mug")
        self.assertEqual(b.sell_by_name("tea", 1), D("12.50"))  # mug's price

    def test_attributes_can_be_bolted_onto_any_object(self) -> None:
        thing = b.EmptyProduct()
        thing.name = "x"  # type: ignore[attr-defined]
        self.assertEqual(vars(thing), {"name": "x"})

    def test_simple_product_has_no_rules(self) -> None:
        mug = b.SimpleProduct("mug", D("12.50"), 10)
        mug.sell(100)
        self.assertEqual(mug.stock, -90)  # why Product adds checks

    def test_product_sell_and_restock(self) -> None:
        mug = b.Product("mug", D("12.50"), 10)
        self.assertEqual(mug.sell(2), D("25.00"))
        self.assertEqual(b.Product.sell(mug, 1), D("12.50"))  # explicit self
        mug.restock(5)
        self.assertEqual(mug.stock, 12)

    def test_product_guards_its_rules(self) -> None:
        with self.assertRaises(ValueError):
            b.Product("mug", D("-1"))
        mug = b.Product("mug", D("1"), 1)
        for bad in (0, 2):
            with self.assertRaises(ValueError):
                mug.sell(bad)
        self.assertEqual(mug.stock, 1)

    def test_inventory_keeps_rows_together(self) -> None:
        shop = b.Inventory()
        shop.add(b.Product("mug", D("12.50"), 10))
        shop.add(b.Product("tea", D("4.00"), 50))
        shop.discontinue("mug")
        self.assertEqual(shop.sell("tea", 1), D("4.00"))
        self.assertEqual(len(shop), 1)
        with self.assertRaises(ValueError):
            shop.sell("mug", 1)
        with self.assertRaises(ValueError):
            shop.add(b.Product("tea", D("1")))

    def test_coupon_class_and_static_methods(self) -> None:
        c = b.Coupon.from_text("SHOP-SPRING-15")
        self.assertEqual((c.code, c.percent_off), ("SPRING", 15))
        self.assertEqual(c.apply(D("40")), D("34.00"))
        self.assertFalse(b.Coupon.is_valid_percent(95))
        with self.assertRaises(ValueError):
            b.Coupon.from_text("OTHER-X-10")

    def test_shared_mutable_class_attribute(self) -> None:
        b.BuggyBasket.items.clear()
        x, y = b.BuggyBasket(), b.BuggyBasket()
        x.add("mug")
        self.assertEqual(y.items, ["mug"])
        b.BuggyBasket.items.clear()
        p1, p2 = b.Basket(), b.Basket()
        p1.add("mug")
        self.assertEqual(p2.items, [])


class InternalsTests(unittest.TestCase):
    def test_descriptor_validates_and_stores_privately(self) -> None:
        box = i.ShippingBox(3, 2, 1)
        self.assertEqual(sorted(vars(box)), ["_depth", "_height", "_width"])
        with self.assertRaises(ValueError):
            box.width = -1
        self.assertIsInstance(i.ShippingBox.width, i.Positive)

    def test_cached_property_computes_once(self) -> None:
        box = i.ShippingBox(3, 2, 1)
        self.assertEqual(box.volume, 6)
        self.assertIn("volume", vars(box))

    def test_functions_are_descriptors(self) -> None:
        box = i.ShippingBox(1, 1, 1)
        bound = i.ShippingBox.fits.__get__(box)
        self.assertIs(bound.__self__, box)
        self.assertTrue(bound(i.ShippingBox(2, 2, 2)))

    def test_diamond_runs_each_init_once(self) -> None:
        c = i.Copier(serial="s", dpi=600, color=False)
        self.assertEqual([k.__name__ for k in i.Copier.__mro__],
                         ["Copier", "Printer", "Scanner", "Device", "object"])
        self.assertEqual(c.boot_log, ["Device", "Scanner", "Printer", "Copier"])
        self.assertEqual((c.serial, c.dpi, c.color), ("s", 600, False))

    def test_context_manager_rolls_back(self) -> None:
        ledger = i.StockLedger(mug=3, tea=1)
        with self.assertRaises(ValueError):
            with ledger.batch() as led:
                led.take("mug", 2)
                led.take("tea", 5)
        self.assertEqual(list(ledger), [("mug", 3), ("tea", 1)])
        with ledger.batch() as led:
            led.take("tea", 1)
        self.assertNotIn("tea", ledger)
        self.assertEqual(len(ledger), 1)

    def test_dataclass_generated_members(self) -> None:
        self.assertEqual(list(inspect.signature(i.LineItem).parameters),
                         ["sku", "quantity", "tags"])
        self.assertIsNone(i.LineItem.__hash__)
        self.assertEqual(i.LineItem("a"), i.LineItem("a"))
        self.assertIsNot(i.LineItem("a").tags, i.LineItem("a").tags)
        self.assertEqual(i.LineItem.__match_args__, ("sku", "quantity", "tags"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            i.Sku("A").code = "B"  # type: ignore[misc]

    def test_hand_written_equivalent_behaves_the_same(self) -> None:
        h = i.HandWrittenLineItem("a")
        self.assertEqual(h, i.HandWrittenLineItem("a"))
        self.assertIsNone(i.HandWrittenLineItem.__hash__)
        self.assertNotEqual(h, i.LineItem("a"))

    def test_slots(self) -> None:
        self.assertFalse(hasattr(i.PointSlots(1, 2), "__dict__"))
        self.assertTrue(hasattr(i.PointSlotsChild(1, 2), "__dict__"))
        with self.assertRaises(AttributeError):
            i.PointSlots(1, 2).z = 3  # type: ignore[attr-defined]
        self.assertLess(i.bytes_per_instance(i.PointSlots, 2000),
                        i.bytes_per_instance(i.PointDict, 2000))


if __name__ == "__main__":
    unittest.main()
