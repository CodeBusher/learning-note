"""Competing designs for the blackjack decision points discussed in the post.

Each section is self-contained and runnable so you can compare approaches
side by side. The recommended choices live in ``blackjack.py``.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from blackjack import Card, HandValue, Outcome, Rank, Shoe, cards, fresh_decks

# ==========================================================================
# Decision 1: hand value with aces
# ==========================================================================


def values_multi_sum(hand: Sequence[Card]) -> list[int]:
    """Approach A: track every possible total (ace = 1 or 11), sorted.

    Faithful to the rules on paper, but the list grows with each ace and
    every caller must then pick the best total itself.
    """
    totals = {0}
    for card in hand:
        if card.rank is Rank.ACE:
            totals = {t + 1 for t in totals} | {t + 11 for t in totals}
        else:
            totals = {t + card.rank.points for t in totals}
    return sorted(totals)


def best_of_multi_sum(hand: Sequence[Card]) -> int:
    totals = values_multi_sum(hand)
    under = [t for t in totals if t <= 21]
    return max(under) if under else min(totals)


def value_soft_hard(hand: Sequence[Card]) -> HandValue:
    """Approach B (recommended): one pass, aces as 1, upgrade one ace if it fits."""
    hard = sum(card.rank.points for card in hand)
    if any(card.rank is Rank.ACE for card in hand) and hard + 10 <= 21:
        return HandValue(hard + 10, soft=True)
    return HandValue(hard, soft=False)


def value_ace_always_11(hand: Sequence[Card]) -> int:
    """Approach C (buggy on purpose): a hard-coded ace value of 11.

    A-A is 22 here and counts as a bust. Shown because it is the most common
    first attempt in interviews.
    """
    return sum(11 if c.rank is Rank.ACE else c.rank.points for c in hand)


# ==========================================================================
# Decision 2: modelling players vs the dealer
# ==========================================================================


class TemplateParticipant(ABC):
    """Approach A: inheritance with a Template Method.

    ``play_turn`` fixes the skeleton (draw while the hook says so); subclasses
    fill in ``should_hit``. Every new behaviour needs a new subclass.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.hand: list[Card] = []

    def play_turn(self, draw: Callable[[], Card]) -> int:
        while value_soft_hard(self.hand).total <= 21 and self.should_hit():
            self.hand.append(draw())
        return value_soft_hard(self.hand).total

    @abstractmethod
    def should_hit(self) -> bool: ...


class TemplateDealer(TemplateParticipant):
    def should_hit(self) -> bool:
        return value_soft_hard(self.hand).total < 17


class TemplateDealerH17(TemplateDealer):
    """A new house rule means a new subclass..."""

    def should_hit(self) -> bool:
        v = value_soft_hard(self.hand)
        return v.total < 17 or (v.total == 17 and v.soft)


class TemplateCautiousPlayer(TemplateParticipant):
    """...and so does every new player personality."""

    def should_hit(self) -> bool:
        return value_soft_hard(self.hand).total < 12


HitRule = Callable[[HandValue], bool]


def dealer_rule(hits_soft_17: bool) -> HitRule:
    return lambda v: v.total < 17 or (hits_soft_17 and v.total == 17 and v.soft)


def threshold_rule(stand_on: int) -> HitRule:
    return lambda v: v.total < stand_on


@dataclass
class ComposedParticipant:
    """Approach B (recommended): one class, behaviour plugged in as a strategy.

    The rule can be swapped at runtime (a human disconnects and an auto-stand
    bot takes over) without changing the participant's type.
    """

    name: str
    rule: HitRule
    hand: list[Card] = field(default_factory=list)

    def play_turn(self, draw: Callable[[], Card]) -> int:
        while (v := value_soft_hard(self.hand)).total <= 21 and self.rule(v):
            self.hand.append(draw())
        return value_soft_hard(self.hand).total


# ==========================================================================
# Decision 3: game flow
# ==========================================================================


def procedural_round(
    shoe: Shoe,
    bets: dict[str, Decimal],
    stand_on: int = 17,
    dealer_hits_soft_17: bool = False,
) -> dict[str, Decimal]:
    """Approach A: one function, one loop, no explicit states.

    Easy to read for hit/stand only. Returns each player's net result. Note
    what is missing: no way to pause for a remote player's input, no guard
    against a command arriving at the wrong time, and every new rule (split,
    double, insurance) has to be threaded through this single body.
    """
    hands: dict[str, list[Card]] = {name: [] for name in bets}
    dealer: list[Card] = []
    for _ in range(2):
        for name in bets:
            hands[name].append(shoe.draw())
        dealer.append(shoe.draw())

    for name, hand in hands.items():
        while value_soft_hard(hand).total < stand_on:
            hand.append(shoe.draw())

    if any(value_soft_hard(h).total <= 21 for h in hands.values()):
        while dealer_rule(dealer_hits_soft_17)(value_soft_hard(dealer)):
            dealer.append(shoe.draw())

    d = value_soft_hard(dealer).total
    dealer_bj = len(dealer) == 2 and d == 21
    net: dict[str, Decimal] = {}
    for name, hand in hands.items():
        p = value_soft_hard(hand).total
        player_bj = len(hand) == 2 and p == 21
        bet = bets[name]
        if p > 21:
            net[name] = -bet
        elif player_bj and not dealer_bj:
            net[name] = bet * Decimal("1.5")
        elif dealer_bj and not player_bj:
            net[name] = -bet
        elif d > 21 or p > d:
            net[name] = bet
        elif p == d:
            net[name] = Decimal("0")
        else:
            net[name] = -bet
    return net


# The recommended alternative is blackjack.Round: an explicit state machine
# with BETTING -> INSURANCE -> PLAYER_TURNS -> DEALER_TURN -> SETTLED.


# ==========================================================================
# Decision 4: payouts
# ==========================================================================


def payout_if_else(outcome: Outcome, bet: Decimal) -> Decimal:
    """Approach A: a conditional chain. Fine until the rules vary per table."""
    if outcome is Outcome.BLACKJACK:
        return bet + bet * Decimal("1.5")
    elif outcome is Outcome.WIN:
        return bet * 2
    elif outcome is Outcome.PUSH:
        return bet
    else:
        return Decimal("0")


PAYOUT_TABLE_3_TO_2: dict[Outcome, Decimal] = {
    Outcome.BLACKJACK: Decimal("2.5"),
    Outcome.WIN: Decimal("2"),
    Outcome.PUSH: Decimal("1"),
    Outcome.LOSS: Decimal("0"),
}
PAYOUT_TABLE_6_TO_5 = {**PAYOUT_TABLE_3_TO_2, Outcome.BLACKJACK: Decimal("2.2")}


def payout_from_table(
    outcome: Outcome, bet: Decimal, table: dict[Outcome, Decimal]
) -> Decimal:
    """Approach B (recommended): data, not code. A 6:5 table is a new dict."""
    return bet * table[outcome]


# ==========================================================================
# Decision 5 (real world): when to shuffle
# ==========================================================================


class ShufflePerRound:
    """Single deck, reshuffled before every round. Simple; slow at a real table."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._cards: list[Card] = []

    def start_round(self) -> None:
        self._cards = fresh_decks(1)
        self._rng.shuffle(self._cards)

    def draw(self) -> Card:
        return self._cards.pop()

    def end_round(self, used: list[Card]) -> None:
        pass


class CutCardShoe:
    """Multi-deck shoe; reshuffle only when the cut card has come out."""

    def __init__(self, rng: random.Random, decks: int = 6, penetration: float = 0.75):
        self._shoe = Shoe(decks, penetration, rng)

    def start_round(self) -> None:
        if self._shoe.cut_card_reached:
            self._shoe.shuffle()

    def draw(self) -> Card:
        return self._shoe.draw()

    def end_round(self, used: list[Card]) -> None:
        pass  # discards go to the discard tray until the next shuffle


class ContinuousShuffler:
    """A continuous shuffling machine (CSM): used cards go straight back in.

    Each draw picks a random card from everything not on the table, so the
    composition barely changes between rounds and card counting stops working.
    """

    def __init__(self, rng: random.Random, decks: int = 4) -> None:
        self._rng = rng
        self._pool = fresh_decks(decks)

    def start_round(self) -> None:
        pass

    def draw(self) -> Card:
        index = self._rng.randrange(len(self._pool))
        self._pool[index], self._pool[-1] = self._pool[-1], self._pool[index]
        return self._pool.pop()

    def end_round(self, used: list[Card]) -> None:
        self._pool.extend(used)

    @property
    def size(self) -> int:
        return len(self._pool)


# ==========================================================================
# Demo
# ==========================================================================
def demo() -> None:
    print("Decision 1: ace handling")
    for labels in [("A", "6"), ("A", "A", "9"), ("A", "6", "10"), ("A", "A", "A", "A")]:
        hand = cards(*labels)
        print(
            f"  {' '.join(labels):10} multi-sum {values_multi_sum(hand)!s:22}"
            f" soft/hard {value_soft_hard(hand)!s:8}  always-11 {value_ace_always_11(hand)}"
        )

    print("\nDecision 2: participants")
    order = cards("A", "6", "4")  # dealer holds A-6 (soft 17); next card is a 4
    for participant in (TemplateDealer("S17"), TemplateDealerH17("H17")):
        shoe = Shoe.stacked(order)
        participant.hand = [shoe.draw(), shoe.draw()]
        print(f"  template {participant.name}: finishes on {participant.play_turn(shoe.draw)}")
    for name, hits in (("S17", False), ("H17", True)):
        shoe = Shoe.stacked(order)
        composed = ComposedParticipant(name, dealer_rule(hits), [shoe.draw(), shoe.draw()])
        print(f"  composed {name}: finishes on {composed.play_turn(shoe.draw)}")

    print("\nDecision 3: procedural round")
    shoe = Shoe(decks=6, rng=random.Random(7))
    print("  ", procedural_round(shoe, {"Ana": Decimal("10"), "Ben": Decimal("10")}))

    print("\nDecision 4: payouts for a $10 blackjack")
    print("  if/else 3:2 ->", payout_if_else(Outcome.BLACKJACK, Decimal("10")))
    print("  table   6:5 ->", payout_from_table(Outcome.BLACKJACK, Decimal("10"), PAYOUT_TABLE_6_TO_5))

    print("\nDecision 5: continuous shuffler keeps its size")
    csm = ContinuousShuffler(random.Random(1), decks=1)
    used = [csm.draw() for _ in range(5)]
    print(f"  after dealing 5: {csm.size} cards in the machine")
    csm.end_round(used)
    print(f"  after returning them: {csm.size}")


if __name__ == "__main__":
    demo()
