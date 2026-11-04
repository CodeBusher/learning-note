"""Tests for the grocery store design. Run: python3 -m unittest discover -s <folder> -v"""

from __future__ import annotations

import threading
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

import alternatives as alt
from grocery_store import (
    AmountOffEach,
    BasketPromotion,
    BuyXGetYFree,
    CheckoutState,
    CheckoutStateError,
    CouponPresented,
    ForProducts,
    GroceryStore,
    InCategory,
    InsufficientStockError,
    InvalidQuantityError,
    LoyaltyMember,
    MultiBuyPrice,
    PaymentError,
    PercentOff,
    Product,
    Promotion,
    SoldBy,
    Stacking,
    TaxClass,
    TaxTable,
    TenderType,
    UnknownCodeError,
    allocate,
    build_demo_store,
    render_text,
    to_money,
)

D = Decimal
NO_TAX = TaxTable("none", {})


def small_store(**kwargs) -> GroceryStore:
    store = GroceryStore("Test Mart", NO_TAX, **kwargs)
    store.add_product(Product("MILK", "Milk", "dairy", D("3.99")), "111", stock=10)
    store.add_product(Product("COLA", "Cola", "beverages", D("4.49")), "222", stock=10)
    store.add_product(Product("BAN", "Bananas", "produce", D("1.49"), SoldBy.WEIGHT), "4011", stock="20")
    return store


class MoneyTests(unittest.TestCase):
    def test_to_money_rounds_half_up(self):
        self.assertEqual(to_money("0.125"), D("0.13"))
        self.assertEqual(to_money("2.675"), D("2.68"))

    def test_float_rejected(self):
        with self.assertRaises(TypeError):
            to_money(0.1)

    def test_allocate_sums_exactly(self):
        parts = allocate(D("1.00"), [D("1"), D("1"), D("1")])
        self.assertEqual(sum(parts), D("1.00"))
        self.assertEqual(sorted(parts), [D("0.33"), D("0.33"), D("0.34")])

    def test_allocate_never_exceeds_weight(self):
        weights = [D("0.01"), D("9.99")]
        parts = allocate(D("10.00"), weights)
        self.assertEqual(parts, weights)


class CatalogInventoryTests(unittest.TestCase):
    def test_lookup_by_barcode_plu_and_sku(self):
        store = small_store()
        self.assertEqual(store.catalog.lookup("111").sku, "MILK")
        self.assertEqual(store.catalog.lookup(" 4011 ").sku, "BAN")
        self.assertEqual(store.catalog.lookup("COLA").name, "Cola")

    def test_unknown_code(self):
        with self.assertRaises(UnknownCodeError):
            small_store().catalog.lookup("999")

    def test_remove_drops_codes(self):
        store = small_store()
        store.catalog.remove("MILK")
        with self.assertRaises(UnknownCodeError):
            store.catalog.lookup("111")

    def test_price_change_does_not_touch_stock(self):
        store = small_store()
        store.catalog.set_price("MILK", "4.19")
        self.assertEqual(store.catalog.get("MILK").unit_price, D("4.19"))
        self.assertEqual(store.inventory.on_hand("MILK"), 10)

    def test_receive_shipment(self):
        store = small_store()
        self.assertEqual(store.receive_shipment("MILK", 5), 15)
        with self.assertRaises(UnknownCodeError):
            store.receive_shipment("NOPE", 5)
        with self.assertRaises(InvalidQuantityError):
            store.receive_shipment("MILK", 0)

    def test_commit_sale_is_all_or_nothing(self):
        store = small_store()
        with self.assertRaises(InsufficientStockError):
            store.inventory.commit_sale({"MILK": D(2), "COLA": D(50)})
        self.assertEqual(store.inventory.on_hand("MILK"), 10)

    def test_negative_stock_allowed_when_configured(self):
        store = small_store(allow_negative_stock=True)
        store.inventory.commit_sale({"MILK": D(12)})
        self.assertEqual(store.inventory.on_hand("MILK"), -2)

    def test_concurrent_lanes_cannot_oversell(self):
        store = GroceryStore("T", NO_TAX)
        store.add_product(Product("LAST", "Last one", "x", D("1")), stock=1)
        wins, losses = [], []

        def sell():
            try:
                store.inventory.commit_sale({"LAST": D(1)})
                wins.append(1)
            except InsufficientStockError:
                losses.append(1)

        threads = [threading.Thread(target=sell) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual((len(wins), len(losses)), (1, 19))
        self.assertEqual(store.inventory.on_hand("LAST"), 0)


class ScanTests(unittest.TestCase):
    def test_repeat_scans_merge_into_one_line(self):
        lane = small_store().open_checkout("1")
        lane.scan("111")
        order = lane.scan("111", 2)
        self.assertEqual(len(order.lines), 1)
        self.assertEqual(order.lines[0].line.quantity, 3)
        self.assertEqual(order.subtotal, D("11.97"))

    def test_weighed_item_uses_net_weight_and_rounds(self):
        lane = small_store().open_checkout("1")
        order = lane.scan_weighed("4011", "1.335", "0.100")
        self.assertEqual(order.lines[0].line.quantity, D("1.235"))
        self.assertEqual(order.subtotal, D("1.84"))  # 1.84015 -> 1.84

    def test_weighed_item_rejects_plain_scan_and_vice_versa(self):
        lane = small_store().open_checkout("1")
        with self.assertRaises(InvalidQuantityError):
            lane.scan("4011")
        with self.assertRaises(InvalidQuantityError):
            lane.scan_weighed("111", "1.0")
        with self.assertRaises(InvalidQuantityError):
            lane.scan_weighed("4011", "0.1", "0.1")

    def test_bad_quantities(self):
        lane = small_store().open_checkout("1")
        for bad in (0, -1, "1.5"):
            with self.assertRaises(InvalidQuantityError):
                lane.scan("111", bad)

    def test_void_line(self):
        lane = small_store().open_checkout("1")
        lane.scan("111")
        lane.scan("222")
        order = lane.void_line(1)
        self.assertEqual([pl.line.product.sku for pl in order.lines], ["COLA"])
        with self.assertRaises(CheckoutStateError):
            lane.void_line(99)

    def test_price_change_mid_basket_keeps_scanned_price(self):
        store = small_store()
        lane = store.open_checkout("1")
        lane.scan("111")
        store.catalog.set_price("MILK", "9.99")
        order = lane.scan("111")
        self.assertEqual(order.subtotal, D("7.98"))


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.store = small_store()
        self.lane = self.store.open_checkout("1")

    def test_best_exclusive_promo_wins(self):
        self.store.add_promotion(Promotion("B2G1", "Cola B2G1", ForProducts(frozenset({"COLA"})), BuyXGetYFree(2, 1)))
        self.store.add_promotion(Promotion("BEV10", "Bev 10%", InCategory("beverages"), PercentOff(D("10"))))
        two = self.lane.scan("222", 2)
        self.assertEqual([a.promo_id for a in two.lines[0].adjustments], ["BEV10"])  # B2G1 not reached
        three = self.lane.scan("222")
        self.assertEqual([a.promo_id for a in three.lines[0].adjustments], ["B2G1"])
        self.assertEqual(three.savings, D("4.49"))

    def test_stackable_applies_after_exclusive_on_remaining(self):
        self.store.add_promotion(Promotion("P10", "10%", InCategory("dairy"), PercentOff(D("10"))))
        self.store.add_promotion(Promotion("MBR", "Member 20%", InCategory("dairy") & LoyaltyMember(),
                                           PercentOff(D("20")), Stacking.STACKABLE))
        self.lane.scan("111", 2)  # 7.98
        self.assertEqual(self.lane.current().savings, D("0.80"))
        order = self.lane.identify_member("L1")
        # 7.98 - 0.80 = 7.18; 20% of 7.18 = 1.436 -> 1.44
        self.assertEqual(order.savings, D("2.24"))

    def test_discount_never_exceeds_line(self):
        self.store.add_promotion(Promotion("BIG", "$10 off", ForProducts(frozenset({"MILK"})), AmountOffEach(D("10"))))
        self.store.add_promotion(Promotion("ST", "stack", ForProducts(frozenset({"MILK"})),
                                           AmountOffEach(D("1")), Stacking.STACKABLE))
        order = self.lane.scan("111")
        self.assertEqual(order.total, D("0.00"))

    def test_multibuy(self):
        self.store.add_promotion(Promotion("M", "2 for $7", ForProducts(frozenset({"COLA"})), MultiBuyPrice(2, D("7"))))
        order = self.lane.scan("222", 5)  # 2 bundles at 7 + 1 at 4.49
        self.assertEqual(order.total, D("18.49"))

    def test_criteria_operators(self):
        self.store.add_promotion(Promotion("NOT-DAIRY", "5% non-dairy", ~InCategory("dairy"), PercentOff(D("5"))))
        self.lane.scan("111")
        order = self.lane.scan("222")
        self.assertEqual(order.savings, D("0.22"))  # 5% of 4.49 = 0.2245 -> 0.22

    def test_expired_promotion_ignored(self):
        past = datetime.now() - timedelta(days=1)
        self.store.add_promotion(Promotion("OLD", "old", InCategory("dairy"), PercentOff(D("50")), ends=past))
        self.assertEqual(self.lane.scan("111").savings, D("0.00"))

    def test_coupon_basket_promotion_threshold_and_allocation(self):
        self.store.add_promotion(BasketPromotion("C5", "$5 off $10", D("10"), D("5"), CouponPresented("SAVE5")))
        self.lane.scan("111", 2)
        self.lane.scan("222")
        self.assertEqual(self.lane.current().savings, D("0.00"))  # no coupon yet
        order = self.lane.add_coupon("SAVE5")
        self.assertEqual(order.savings, D("5.00"))
        self.assertEqual(sum(pl.basket_share for pl in order.lines), D("5.00"))

    def test_basket_threshold_not_met(self):
        self.store.add_promotion(BasketPromotion("C5", "$5 off $50", D("50"), D("5")))
        self.assertEqual(self.lane.scan("111").savings, D("0.00"))

    def test_removed_promotion_no_longer_applies(self):
        self.store.add_promotion(Promotion("P", "p", InCategory("dairy"), PercentOff(D("10"))))
        self.store.promotions.remove("P")
        self.assertEqual(self.lane.scan("111").savings, D("0.00"))


class TaxTests(unittest.TestCase):
    def test_tax_by_class_after_discounts(self):
        tax = TaxTable("X", {TaxClass.GENERAL: D("0.10")})
        store = GroceryStore("T", tax)
        store.add_product(Product("SOAP", "Soap", "home", D("5.00"), tax_class=TaxClass.GENERAL), stock=5)
        store.add_product(Product("BREAD", "Bread", "bakery", D("5.00")), stock=5)
        store.add_promotion(BasketPromotion("B", "$2 off", D("0"), D("2")))
        lane = store.open_checkout("1")
        lane.scan("SOAP")
        order = lane.scan("BREAD")
        # $2 split $1/$1; soap taxable 4.00 -> tax 0.40; bread untaxed.
        self.assertEqual(order.tax, D("0.40"))
        self.assertEqual(order.total, D("8.40"))


class PaymentTests(unittest.TestCase):
    def test_cash_with_change_and_stock_decrement(self):
        store = small_store()
        lane = store.open_checkout("1")
        lane.scan("111", 2)
        receipt = lane.pay(TenderType.CASH, "10")
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.change, D("2.02"))
        self.assertEqual(lane.state, CheckoutState.COMPLETED)
        self.assertEqual(store.inventory.on_hand("MILK"), 8)

    def test_split_tender_freezes_basket(self):
        lane = small_store().open_checkout("1")
        lane.scan("111", 2)  # 7.98
        self.assertIsNone(lane.pay(TenderType.CASH, "5"))
        self.assertEqual(lane.state, CheckoutState.TENDERING)
        self.assertEqual(lane.amount_due(), D("2.98"))
        with self.assertRaises(CheckoutStateError):
            lane.scan("222")
        receipt = lane.pay(TenderType.CARD, "2.98")
        self.assertEqual(receipt.change, D("0.00"))
        self.assertEqual(len(receipt.tenders), 2)

    def test_card_cannot_overpay(self):
        lane = small_store().open_checkout("1")
        lane.scan("111")
        with self.assertRaises(PaymentError):
            lane.pay(TenderType.CARD, "100")

    def test_empty_and_invalid_payment(self):
        lane = small_store().open_checkout("1")
        with self.assertRaises(CheckoutStateError):
            lane.pay(TenderType.CASH, "5")
        lane.scan("111")
        with self.assertRaises(PaymentError):
            lane.pay(TenderType.CASH, "0")

    def test_out_of_stock_blocks_completion_without_recording_tender(self):
        store = small_store()
        lane = store.open_checkout("1")
        lane.scan("111", 11)
        with self.assertRaises(InsufficientStockError):
            lane.pay(TenderType.CASH, "100")
        self.assertEqual(lane.state, CheckoutState.SCANNING)
        self.assertIsNone(lane.receipt)

    def test_completed_and_voided_are_terminal(self):
        lane = small_store().open_checkout("1")
        lane.scan("111")
        lane.pay(TenderType.CASH, "5")
        with self.assertRaises(CheckoutStateError):
            lane.scan("111")
        other = small_store().open_checkout("2")
        other.void()
        with self.assertRaises(CheckoutStateError):
            other.pay(TenderType.CASH, "1")

    def test_receipt_ids_are_unique_and_sequential(self):
        store = small_store()
        ids = []
        for lane_no in range(3):
            lane = store.open_checkout(str(lane_no))
            lane.scan("111")
            ids.append(lane.pay(TenderType.CASH, "4").receipt_id)
        self.assertEqual(ids, ["R-000001", "R-000002", "R-000003"])


class DemoAndReceiptTests(unittest.TestCase):
    def test_demo_scenario_totals(self):
        store = build_demo_store()
        lane = store.open_checkout("3")
        lane.scan("041303001714", 2)
        lane.scan_weighed("4011", "1.335", "0.100")
        lane.scan("049000028911", 3)
        lane.scan("012000161155", 4)
        lane.scan("028400090858")
        lane.identify_member("LOY-1")
        order = lane.add_coupon("SAVE5")
        self.assertEqual(order.subtotal, D("31.78"))
        self.assertEqual(order.savings, D("10.99"))
        self.assertEqual(order.tax, D("0.68"))
        self.assertEqual(order.total, D("21.47"))
        receipt = lane.pay(TenderType.CASH, "30")
        text = render_text(receipt)
        self.assertIn("Cola buy 2 get 1", text)
        self.assertIn("TOTAL", text)
        self.assertIn("8.53", text)

    def test_receipt_is_a_snapshot(self):
        store = small_store()
        lane = store.open_checkout("1")
        lane.scan("111")
        receipt = lane.pay(TenderType.CASH, "5")
        store.catalog.set_price("MILK", "99")
        self.assertEqual(receipt.order.total, D("3.99"))


class AlternativesTests(unittest.TestCase):
    def test_all_discount_engines_agree_on_cola(self):
        cola = alt.SimpleItem("COLA-6", "beverages", D("4.49"), 3)
        strategies = [alt.SkuBuyXGetYStrategy("COLA-6", 2, 1), alt.CategoryPercentStrategy("beverages", D("10"))]
        product = Product("COLA-6", "Cola", "beverages", D("4.49"))
        self.assertEqual(alt.ifelse_discount(cola), D("4.49"))
        self.assertEqual(alt.best_strategy_discount(cola, strategies), D("4.49"))
        self.assertEqual(alt.composable_discount(product, 3), D("4.49"))

    def test_decorator_order_changes_result(self):
        a, b = alt.decorator_order_matters(D("10.00"))
        self.assertNotEqual(a, b)

    def test_stacking_on_original_can_exceed_price(self):
        pcts = [D("20"), D("15"), D("70")]
        self.assertGreater(alt.stack_on_original_price(D("10"), pcts), D("10"))
        self.assertLess(alt.stack_sequential(D("10"), pcts), D("10"))

    def test_float_drift_vs_exact(self):
        prices = ["0.10", "0.20", "0.30"]
        self.assertNotEqual(alt.float_total(prices), 0.6)
        self.assertEqual(alt.decimal_total(prices), D("0.60"))
        self.assertEqual(alt.cents_total(prices), 60)

    def test_merged_catalog_loses_stock(self):
        merged = alt.MergedStore()
        merged.items["M"] = alt.ItemWithStock("M", "Milk", D("3.99"), 40)
        merged.update_from_head_office("M", "Milk", D("4.19"))
        self.assertEqual(merged.items["M"].stock, 0)

    def test_live_receipt_drifts(self):
        catalog = {"M": D("3.99")}
        live = alt.LiveOrder(catalog, ["M"])
        snap = alt.SnapshotReceipt((("M", D("3.99")),))
        catalog["M"] = D("4.19")
        self.assertEqual(live.receipt_total(), D("4.19"))
        self.assertEqual(snap.total, D("3.99"))


if __name__ == "__main__":
    unittest.main()
