"""Tests for the blackjack design. Run: python3 -m unittest discover -s <folder> -v"""

from __future__ import annotations

import random
import threading
import unittest
from decimal import Decimal

import alternatives as alt
from blackjack import (
    Action,
    Card,
    DealerStrategy,
    Hand,
    HouseRules,
    IllegalAction,
    InsufficientFunds,
    InvalidPhase,
    NotYourTurn,
    Outcome,
    Phase,
    Player,
    Rank,
    Round,
    ScriptedStrategy,
    Shoe,
    ShoeEmpty,
    StaleCommand,
    Suit,
    Table,
    ThresholdStrategy,
    cards,
)

D = Decimal


def hand_of(*labels: str, **kwargs) -> Hand:
    return Hand(cards=cards(*labels), **kwargs)


def make_table(order: list[str], rules: HouseRules | None = None, **players) -> Table:
    """A table with a stacked shoe. ``players`` maps name -> list of actions."""
    table = Table(rules or HouseRules(), shoe=Shoe.stacked(cards(*order)))
    for name, actions in players.items():
        table.seat(Player(name, D("100"), ScriptedStrategy(*actions)))
    return table


def started_round(table: Table, bet: str = "10") -> Round:
    rnd = table.new_round()
    for player in table.players:
        rnd.place_bet(player, D(bet))
    rnd.deal()
    return rnd


# --------------------------------------------------------------------------
class HandValueTests(unittest.TestCase):
    def test_soft_and_hard_totals(self):
        self.assertEqual(str(hand_of("A", "6").value()), "soft 17")
        self.assertEqual(str(hand_of("A", "6", "10").value()), "hard 17")
        self.assertEqual(str(hand_of("A", "A", "9").value()), "soft 21")
        self.assertEqual(str(hand_of("A", "A", "A", "A").value()), "soft 14")
        self.assertEqual(hand_of("K", "Q", "5").total, 25)

    def test_blackjack_needs_two_cards_and_no_split(self):
        self.assertTrue(hand_of("A", "K").is_blackjack)
        self.assertFalse(hand_of("7", "7", "7").is_blackjack)
        self.assertFalse(hand_of("A", "K", from_split=True).is_blackjack)

    def test_bust_and_pair(self):
        self.assertTrue(hand_of("10", "6", "9").is_bust)
        self.assertTrue(hand_of("8", "8").is_pair)
        self.assertFalse(hand_of("K", "Q").is_pair)  # same value, different rank


class ShoeTests(unittest.TestCase):
    def test_seeded_shoes_are_reproducible(self):
        a = Shoe(decks=6, rng=random.Random(42))
        b = Shoe(decks=6, rng=random.Random(42))
        self.assertEqual([a.draw() for _ in range(50)], [b.draw() for _ in range(50)])

    def test_six_deck_shoe_has_312_cards(self):
        self.assertEqual(Shoe(decks=6, rng=random.Random(1)).remaining, 312)

    def test_cut_card(self):
        shoe = Shoe(decks=1, penetration=0.5, rng=random.Random(1))
        for _ in range(25):
            shoe.draw()
        self.assertFalse(shoe.cut_card_reached)
        shoe.draw()
        self.assertTrue(shoe.cut_card_reached)
        shoe.shuffle()
        self.assertEqual(shoe.remaining, 52)
        self.assertFalse(shoe.cut_card_reached)

    def test_stacked_shoe_order_and_empty(self):
        shoe = Shoe.stacked(cards("A", "2"))
        self.assertEqual(shoe.draw().rank, Rank.ACE)
        self.assertEqual(shoe.draw().rank, Rank.TWO)
        with self.assertRaises(ShoeEmpty):
            shoe.draw()

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            Shoe(decks=0)
        with self.assertRaises(ValueError):
            Shoe(penetration=1.5)


class DealerStrategyTests(unittest.TestCase):
    up = Card(Rank.SIX, Suit.CLUBS)
    allowed = frozenset({Action.HIT, Action.STAND})

    def test_s17_stands_on_soft_17(self):
        s17 = DealerStrategy(hits_soft_17=False)
        self.assertIs(s17.decide(hand_of("A", "6"), self.up, self.allowed), Action.STAND)
        self.assertIs(s17.decide(hand_of("10", "6"), self.up, self.allowed), Action.HIT)

    def test_h17_hits_soft_17_but_not_hard_17(self):
        h17 = DealerStrategy(hits_soft_17=True)
        self.assertIs(h17.decide(hand_of("A", "6"), self.up, self.allowed), Action.HIT)
        self.assertIs(h17.decide(hand_of("10", "7"), self.up, self.allowed), Action.STAND)


# --------------------------------------------------------------------------
class SettlementTests(unittest.TestCase):
    def _play(self, order, actions, rules=None, bet="10"):
        table = make_table(order, rules, Ana=actions)
        rnd = table.play_round({"Ana": D(bet)})
        return rnd, table.players[0]

    def test_win_pays_one_to_one(self):
        # Ana 10,9 = 19; dealer 10,7 = 17
        rnd, ana = self._play(["10", "10", "9", "7"], [Action.STAND])
        self.assertEqual(rnd.results[0].outcome, Outcome.WIN)
        self.assertEqual(ana.bankroll, D("110"))

    def test_push_returns_stake(self):
        rnd, ana = self._play(["10", "10", "8", "8"], [Action.STAND])
        self.assertEqual(rnd.results[0].outcome, Outcome.PUSH)
        self.assertEqual(ana.bankroll, D("100"))

    def test_loss(self):
        rnd, ana = self._play(["10", "10", "6", "8"], [Action.STAND])
        self.assertEqual(rnd.results[0].outcome, Outcome.LOSS)
        self.assertEqual(ana.bankroll, D("90"))

    def test_player_bust_loses_even_if_dealer_would_bust(self):
        # Ana 10,6 hits K -> 26. Dealer 10,6 does not need to draw at all.
        rnd, ana = self._play(["10", "10", "6", "6", "K", "K"], [Action.HIT])
        self.assertEqual(rnd.results[0].outcome, Outcome.LOSS)
        self.assertEqual(len(rnd.dealer.hand.cards), 2)
        self.assertEqual(ana.bankroll, D("90"))

    def test_dealer_bust(self):
        rnd, ana = self._play(["10", "10", "2", "6", "K"], [Action.STAND])
        self.assertEqual(rnd.results[0].outcome, Outcome.WIN)

    def test_blackjack_pays_three_to_two(self):
        rnd, ana = self._play(["A", "9", "K", "7"], [], bet="5")
        self.assertEqual(rnd.results[0].outcome, Outcome.BLACKJACK)
        self.assertEqual(ana.bankroll, D("107.50"))

    def test_six_to_five_table(self):
        rules = HouseRules(blackjack_pays=D("1.2"))
        rnd, ana = self._play(["A", "9", "K", "7"], [], rules=rules)
        self.assertEqual(ana.bankroll, D("112"))

    def test_both_blackjack_is_push(self):
        rnd, ana = self._play(["A", "A", "K", "K"], [], rules=HouseRules(offer_insurance=False))
        self.assertEqual(rnd.results[0].outcome, Outcome.PUSH)
        self.assertEqual(ana.bankroll, D("100"))

    def test_dealer_peek_with_ten_up_ends_round_immediately(self):
        table = make_table(["9", "K", "8", "A"], Ana=[Action.HIT])
        rnd = started_round(table)
        self.assertIs(rnd.phase, Phase.SETTLED)
        self.assertEqual(rnd.results[0].outcome, Outcome.LOSS)
        self.assertEqual(len(table.players[0].hands[0].cards), 2)

    def test_dealer_draws_to_soft_17_under_h17(self):
        # dealer A,6; H17 hits and draws 4 -> soft 21 beats Ana's 20.
        order = ["10", "A", "10", "6", "4"]
        rules = HouseRules(dealer_hits_soft_17=True, offer_insurance=False)
        rnd, _ = self._play(order, [Action.STAND], rules=rules)
        self.assertEqual(rnd.dealer.hand.total, 21)
        self.assertEqual(rnd.results[0].outcome, Outcome.LOSS)
        rnd, _ = self._play(order, [Action.STAND], rules=HouseRules(offer_insurance=False))
        self.assertEqual(rnd.dealer.hand.total, 17)
        self.assertEqual(rnd.results[0].outcome, Outcome.WIN)


class InsuranceTests(unittest.TestCase):
    def test_insurance_pays_two_to_one_on_dealer_blackjack(self):
        table = make_table(["10", "A", "9", "K"], Ana=[])
        rnd = started_round(table)
        self.assertIs(rnd.phase, Phase.INSURANCE)
        ana = table.players[0]
        rnd.take_insurance(ana)
        self.assertEqual(ana.bankroll, D("85"))
        rnd.close_insurance()
        self.assertIs(rnd.phase, Phase.SETTLED)
        # main bet lost (-10), insurance 5 wins 10: net zero
        self.assertEqual(ana.bankroll, D("100"))

    def test_insurance_lost_when_no_blackjack(self):
        table = make_table(["10", "A", "9", "7"], Ana=[Action.STAND])
        rnd = started_round(table)
        ana = table.players[0]
        rnd.take_insurance(ana)
        rnd.close_insurance()
        self.assertIs(rnd.phase, Phase.PLAYER_TURNS)
        rnd.act(ana, Action.STAND)
        # wins 19 vs 18 (+10) but loses the 5 insurance
        self.assertEqual(ana.bankroll, D("105"))

    def test_insurance_only_in_insurance_phase(self):
        table = make_table(["10", "6", "9", "7"], Ana=[])
        rnd = started_round(table)
        with self.assertRaises(InvalidPhase):
            rnd.take_insurance(table.players[0])


class DoubleAndSplitTests(unittest.TestCase):
    def test_double_takes_exactly_one_card(self):
        table = make_table(["6", "10", "5", "7", "K", "10"], Ana=[Action.DOUBLE])
        rnd = table.play_round({"Ana": D("10")})
        hand = table.players[0].hands[0]
        self.assertEqual(len(hand.cards), 3)
        self.assertEqual(hand.bet, D("20"))
        self.assertEqual(rnd.results[0].outcome, Outcome.WIN)
        self.assertEqual(table.players[0].bankroll, D("120"))

    def test_cannot_double_after_hitting(self):
        table = make_table(["2", "10", "3", "7", "4"], Ana=[])
        rnd = started_round(table)
        ana = table.players[0]
        rnd.act(ana, Action.HIT)
        self.assertNotIn(Action.DOUBLE, rnd.allowed_actions())
        with self.assertRaises(IllegalAction):
            rnd.act(ana, Action.DOUBLE)

    def test_split_creates_two_independent_hands(self):
        # Ana 8,8 vs dealer 6,10; split -> 8,3 and 8,10; dealer draws 7 -> 23
        order = ["8", "6", "8", "10", "3", "10", "7"]
        table = make_table(order, Ana=[Action.SPLIT, Action.STAND, Action.STAND])
        rnd = table.play_round({"Ana": D("10")})
        ana = table.players[0]
        self.assertEqual([h.total for h in ana.hands], [11, 18])
        self.assertEqual([r.outcome for r in rnd.results], [Outcome.WIN, Outcome.WIN])
        self.assertEqual(ana.bankroll, D("120"))

    def test_split_aces_get_one_card_and_21_is_not_blackjack(self):
        order = ["A", "6", "A", "10", "K", "9", "2"]
        table = make_table(order, Ana=[Action.SPLIT])
        rnd = table.play_round({"Ana": D("10")})
        ana = table.players[0]
        self.assertEqual([len(h.cards) for h in ana.hands], [2, 2])
        self.assertEqual([h.total for h in ana.hands], [21, 20])
        self.assertEqual(rnd.results[0].outcome, Outcome.WIN)  # paid 1:1, not 3:2
        self.assertEqual(ana.bankroll, D("120"))

    def test_no_double_after_split_rule(self):
        rules = HouseRules(double_after_split=False)
        table = make_table(["8", "6", "8", "10", "3", "2"], rules, Ana=[])
        rnd = started_round(table)
        rnd.act(table.players[0], Action.SPLIT)
        self.assertNotIn(Action.DOUBLE, rnd.allowed_actions())

    def test_split_limited_by_max_hands(self):
        rules = HouseRules(max_hands_per_player=2)
        table = make_table(["8", "6", "8", "10", "8", "2"], rules, Ana=[])
        rnd = started_round(table)
        rnd.act(table.players[0], Action.SPLIT)
        self.assertTrue(rnd.current[1].is_pair)
        self.assertNotIn(Action.SPLIT, rnd.allowed_actions())

    def test_split_needs_money(self):
        table = make_table(["8", "6", "8", "10"], Ana=[])
        rnd = table.new_round()
        ana = table.players[0]
        rnd.place_bet(ana, D("100"))
        rnd.deal()
        self.assertNotIn(Action.SPLIT, rnd.allowed_actions())
        self.assertNotIn(Action.DOUBLE, rnd.allowed_actions())


class ProtocolTests(unittest.TestCase):
    """The round is server-authoritative: bad commands are rejected."""

    def test_bet_validation(self):
        table = make_table([], Ana=[])
        rnd = table.new_round()
        ana = table.players[0]
        with self.assertRaises(IllegalAction):
            rnd.place_bet(ana, D("1"))  # below table minimum
        ana.bankroll = D("20")
        with self.assertRaises(InsufficientFunds):
            rnd.place_bet(ana, D("50"))
        rnd.place_bet(ana, D("10"))
        with self.assertRaises(IllegalAction):
            rnd.place_bet(ana, D("10"))

    def test_deal_without_bets(self):
        table = make_table([], Ana=[])
        with self.assertRaises(IllegalAction):
            table.new_round().deal()

    def test_wrong_phase_and_wrong_turn(self):
        table = make_table(["10", "10", "6", "6", "7", "2"], Ana=[], Ben=[])
        rnd = table.new_round()
        ana, ben = table.players
        with self.assertRaises(InvalidPhase):
            rnd.act(ana, Action.HIT)
        rnd.place_bet(ana, D("10"))
        rnd.place_bet(ben, D("10"))
        rnd.deal()
        with self.assertRaises(NotYourTurn):
            rnd.act(ben, Action.STAND)
        with self.assertRaises(InvalidPhase):
            rnd.deal()

    def test_player_who_sits_out_gets_no_cards(self):
        table = make_table(["10", "10", "9", "7"], Ana=[], Ben=[])
        rnd = table.play_round({"Ana": D("10")})
        self.assertEqual(table.players[1].hands, [])
        self.assertEqual(len(rnd.results), 1)

    def test_stale_command_rejected(self):
        table = make_table(["2", "10", "3", "7", "4", "5"], Ana=[])
        rnd = started_round(table)
        ana = table.players[0]
        version = rnd.version
        rnd.act(ana, Action.HIT, expected_version=version)
        with self.assertRaises(StaleCommand):
            rnd.act(ana, Action.HIT, expected_version=version)  # double click

    def test_concurrent_duplicate_commands_apply_once(self):
        table = make_table(["2", "10", "3", "7"] + ["2"] * 10, Ana=[])
        rnd = started_round(table)
        ana = table.players[0]
        version = rnd.version
        outcomes: list[str] = []
        barrier = threading.Barrier(8)

        def click():
            barrier.wait()
            try:
                rnd.act(ana, Action.HIT, expected_version=version)
                outcomes.append("ok")
            except StaleCommand:
                outcomes.append("stale")

        threads = [threading.Thread(target=click) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(outcomes.count("ok"), 1)
        self.assertEqual(len(ana.hands[0].cards), 3)

    def test_table_reshuffles_only_between_rounds(self):
        rules = HouseRules(decks=1, penetration=0.2)
        table = Table(rules, rng=random.Random(3))
        table.seat(Player("Bot", D("1000"), ThresholdStrategy(17)))
        while not table.shoe.cut_card_reached:
            table.play_round({"Bot": D("10")})
        dealt_before = table.shoe.dealt
        table.new_round()
        self.assertEqual(table.shoe.dealt, 0)
        self.assertGreater(dealt_before, 0)

    def test_bankroll_change_matches_results_over_many_rounds(self):
        table = Table(HouseRules(), rng=random.Random(2024))
        bot = Player("Bot", D("10000"), ThresholdStrategy(17))
        table.seat(bot)
        for _ in range(300):
            before = bot.bankroll
            rnd = table.play_round({"Bot": D("10")})
            self.assertIs(rnd.phase, Phase.SETTLED)
            self.assertEqual(bot.bankroll - before, sum(r.net for r in rnd.results))


# --------------------------------------------------------------------------
class AlternativesTests(unittest.TestCase):
    def test_multi_sum_and_single_pass_agree(self):
        rng = random.Random(9)
        ranks = list(Rank)
        for _ in range(3000):
            hand = [Card(rng.choice(ranks), Suit.SPADES) for _ in range(rng.randint(2, 7))]
            self.assertEqual(alt.best_of_multi_sum(hand), alt.value_soft_hard(hand).total)

    def test_ace_always_11_is_wrong(self):
        self.assertEqual(alt.value_ace_always_11(cards("A", "A")), 22)
        self.assertEqual(alt.value_soft_hard(cards("A", "A")).total, 12)

    def test_template_and_composed_participants_agree(self):
        order = cards("A", "6", "4")
        for template, hits in ((alt.TemplateDealer("d"), False), (alt.TemplateDealerH17("d"), True)):
            s1, s2 = Shoe.stacked(order), Shoe.stacked(order)
            template.hand = [s1.draw(), s1.draw()]
            composed = alt.ComposedParticipant("d", alt.dealer_rule(hits), [s2.draw(), s2.draw()])
            self.assertEqual(template.play_turn(s1.draw), composed.play_turn(s2.draw))

    def test_procedural_round_matches_state_machine_for_hit_stand(self):
        for seed in range(60):
            bets = {"Ana": D("10"), "Ben": D("10")}
            procedural = alt.procedural_round(Shoe(6, rng=random.Random(seed)), bets)
            table = Table(HouseRules(), rng=random.Random(seed))
            for name in bets:
                table.seat(Player(name, D("100"), ThresholdStrategy(17)))
            table.play_round(bets)
            for player in table.players:
                self.assertEqual(player.bankroll - D("100"), procedural[player.name], seed)

    def test_payout_styles_agree(self):
        for outcome in Outcome:
            self.assertEqual(
                alt.payout_if_else(outcome, D("10")),
                alt.payout_from_table(outcome, D("10"), alt.PAYOUT_TABLE_3_TO_2),
            )

    def test_shuffle_policies(self):
        csm = alt.ContinuousShuffler(random.Random(1), decks=2)
        used = [csm.draw() for _ in range(10)]
        csm.end_round(used)
        self.assertEqual(csm.size, 104)
        per_round = alt.ShufflePerRound(random.Random(1))
        per_round.start_round()
        per_round.draw()
        per_round.start_round()
        self.assertEqual(len(per_round._cards), 52)


if __name__ == "__main__":
    unittest.main()
