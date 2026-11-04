"""Blackjack: the recommended object-oriented design.

Key ideas
- Cards come from a ``Shoe`` that takes an injectable ``random.Random`` (or a
  stacked card order) so every round can be replayed exactly in tests.
- ``Hand.value()`` computes the best total and whether it is "soft" in a
  single pass: count every ace as 1, then upgrade one ace to 11 if it fits.
- Players and the dealer are *composed* with a ``DecisionStrategy``. The
  dealer's "hit until 17" rule is just one strategy, configured by house rules.
- A ``Round`` is an explicit state machine (BETTING -> INSURANCE ->
  PLAYER_TURNS -> DEALER_TURN -> SETTLED). It is server-authoritative: it
  validates whose turn it is and which actions are legal before changing state.
"""

from __future__ import annotations

import random
import threading
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from enum import Enum, auto
from typing import Protocol

CENT = Decimal("0.01")


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class BlackjackError(Exception):
    """Base class for every rule violation raised by the game."""


class InvalidPhase(BlackjackError):
    """A command arrived in a phase of the round where it is not allowed."""


class NotYourTurn(BlackjackError):
    """A player tried to act while another hand is in play."""


class IllegalAction(BlackjackError):
    """The action is not legal for the current hand (e.g. double on 3 cards)."""


class InsufficientFunds(BlackjackError):
    """The player's bankroll cannot cover the stake."""


class StaleCommand(BlackjackError):
    """The command was built against an older version of the round."""


class ShoeEmpty(BlackjackError):
    """No cards are left to draw."""


# --------------------------------------------------------------------------
# Cards and the shoe
# --------------------------------------------------------------------------
class Suit(Enum):
    CLUBS = "♣"
    DIAMONDS = "♦"
    HEARTS = "♥"
    SPADES = "♠"


class Rank(Enum):
    """Each rank carries its label and its *hard* point value (ace = 1)."""

    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 10)
    QUEEN = ("Q", 10)
    KING = ("K", 10)
    ACE = ("A", 1)

    def __init__(self, label: str, points: int) -> None:
        self.label = label
        self.points = points

    @classmethod
    def from_label(cls, label: str) -> Rank:
        for rank in cls:
            if rank.label == label.upper():
                return rank
        raise ValueError(f"unknown rank {label!r}")


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.label}{self.suit.value}"


def cards(*labels: str) -> list[Card]:
    """Build cards from rank labels, cycling suits. Handy for stacked shoes."""
    suits = list(Suit)
    return [Card(Rank.from_label(lbl), suits[i % 4]) for i, lbl in enumerate(labels)]


def fresh_decks(count: int) -> list[Card]:
    return [Card(rank, suit) for _ in range(count) for suit in Suit for rank in Rank]


class Shoe:
    """A multi-deck shoe with a cut card.

    The cut card is placed at ``penetration`` of the way through the shoe.
    Once it has been reached, the *current* round finishes normally and the
    table reshuffles before the next one, exactly like a casino shoe.
    """

    def __init__(
        self,
        decks: int = 6,
        penetration: float = 0.75,
        rng: random.Random | None = None,
    ) -> None:
        if decks < 1:
            raise ValueError("a shoe needs at least one deck")
        if not 0 < penetration <= 1:
            raise ValueError("penetration must be in (0, 1]")
        self._decks = decks
        self._penetration = penetration
        # Production code would pass a certified generator (e.g. SystemRandom
        # or a hardware RNG); tests pass random.Random(seed).
        self._rng = rng if rng is not None else random.SystemRandom()
        self._cards: list[Card] = []
        self._cut_index = 0
        self.dealt = 0
        self.shuffle()

    @classmethod
    def stacked(cls, order: Sequence[Card]) -> Shoe:
        """A shoe that deals exactly ``order`` (first element first). For tests."""
        shoe = cls.__new__(cls)
        shoe._decks = 0
        shoe._penetration = 1.0
        shoe._rng = random.Random(0)
        shoe._cards = list(reversed(order))  # pop() from the end is O(1)
        shoe._cut_index = len(order)
        shoe.dealt = 0
        return shoe

    def shuffle(self) -> None:
        if self._decks == 0:  # stacked shoes are never reshuffled
            return
        self._cards = fresh_decks(self._decks)
        self._rng.shuffle(self._cards)
        self._cut_index = int(len(self._cards) * self._penetration)
        self.dealt = 0

    def draw(self) -> Card:
        if not self._cards:
            raise ShoeEmpty("the shoe is empty")
        self.dealt += 1
        return self._cards.pop()

    @property
    def remaining(self) -> int:
        return len(self._cards)

    @property
    def cut_card_reached(self) -> bool:
        return self.dealt >= self._cut_index


# --------------------------------------------------------------------------
# Hands
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class HandValue:
    total: int
    soft: bool  # True when an ace is currently counted as 11

    def __str__(self) -> str:
        return f"{'soft' if self.soft else 'hard'} {self.total}"


@dataclass
class Hand:
    """Cards plus the wager riding on them. One player may own several hands."""

    bet: Decimal = Decimal("0")
    cards: list[Card] = field(default_factory=list)
    from_split: bool = False
    doubled: bool = False
    finished: bool = False

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def value(self) -> HandValue:
        hard = sum(card.rank.points for card in self.cards)
        has_ace = any(card.rank is Rank.ACE for card in self.cards)
        # At most one ace can ever count as 11 (two would already be 22).
        if has_ace and hard + 10 <= 21:
            return HandValue(hard + 10, soft=True)
        return HandValue(hard, soft=False)

    @property
    def total(self) -> int:
        return self.value().total

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    @property
    def is_blackjack(self) -> bool:
        # 21 on a split hand is just 21, not a natural blackjack.
        return len(self.cards) == 2 and self.total == 21 and not self.from_split

    @property
    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank is self.cards[1].rank

    def __str__(self) -> str:
        shown = " ".join(str(c) for c in self.cards)
        return f"[{shown}] = {self.value()}"


# --------------------------------------------------------------------------
# House rules
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class HouseRules:
    """Table configuration. Everything a casino might print on the felt."""

    decks: int = 6
    penetration: float = 0.75
    dealer_hits_soft_17: bool = False  # False = "S17", True = "H17"
    blackjack_pays: Decimal = Decimal("1.5")  # 3:2. A 6:5 table uses 1.2
    min_bet: Decimal = Decimal("5")
    max_bet: Decimal = Decimal("500")
    max_hands_per_player: int = 4  # i.e. up to three splits
    double_after_split: bool = True
    offer_insurance: bool = True


# --------------------------------------------------------------------------
# Decisions (Strategy pattern)
# --------------------------------------------------------------------------
class Action(Enum):
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    SPLIT = auto()


class DecisionStrategy(Protocol):
    """Anything that can pick an action for a hand: a bot, a UI, the dealer."""

    def decide(
        self, hand: Hand, dealer_upcard: Card, allowed: frozenset[Action]
    ) -> Action: ...


class DealerStrategy:
    """The house rule: draw to 17. Optionally also hit a soft 17 (H17)."""

    def __init__(self, hits_soft_17: bool = False) -> None:
        self.hits_soft_17 = hits_soft_17

    def decide(
        self, hand: Hand, dealer_upcard: Card, allowed: frozenset[Action]
    ) -> Action:
        value = hand.value()
        if value.total < 17:
            return Action.HIT
        if value.total == 17 and value.soft and self.hits_soft_17:
            return Action.HIT
        return Action.STAND


class ThresholdStrategy:
    """A simple bot: hit below a threshold, otherwise stand."""

    def __init__(self, stand_on: int = 17) -> None:
        self.stand_on = stand_on

    def decide(
        self, hand: Hand, dealer_upcard: Card, allowed: frozenset[Action]
    ) -> Action:
        return Action.HIT if hand.total < self.stand_on else Action.STAND


class ScriptedStrategy:
    """Plays a fixed list of actions, then stands. Used by tests and demos."""

    def __init__(self, *actions: Action) -> None:
        self._actions = list(actions)

    def decide(
        self, hand: Hand, dealer_upcard: Card, allowed: frozenset[Action]
    ) -> Action:
        return self._actions.pop(0) if self._actions else Action.STAND


# --------------------------------------------------------------------------
# Participants (composition, not inheritance)
# --------------------------------------------------------------------------
@dataclass(eq=False)
class Player:
    """A seat at the table: identity, money and a way of deciding."""

    name: str
    bankroll: Decimal
    strategy: DecisionStrategy
    takes_insurance: bool = False
    hands: list[Hand] = field(default_factory=list)
    insurance: Decimal = Decimal("0")

    def debit(self, amount: Decimal) -> None:
        if amount > self.bankroll:
            raise InsufficientFunds(
                f"{self.name} has {self.bankroll}, needs {amount}"
            )
        self.bankroll -= amount

    def credit(self, amount: Decimal) -> None:
        self.bankroll += amount


@dataclass(eq=False)
class Dealer:
    """The house. It has a hand and a rule, but no bankroll and no bets."""

    strategy: DecisionStrategy
    hand: Hand = field(default_factory=Hand)

    @property
    def upcard(self) -> Card:
        return self.hand.cards[0]


# --------------------------------------------------------------------------
# Settlement
# --------------------------------------------------------------------------
class Outcome(Enum):
    BLACKJACK = auto()
    WIN = auto()
    PUSH = auto()
    LOSS = auto()


def decide_outcome(hand: Hand, dealer_hand: Hand) -> Outcome:
    if hand.is_bust:
        return Outcome.LOSS  # a busted player loses even if the dealer busts
    if hand.is_blackjack:
        return Outcome.PUSH if dealer_hand.is_blackjack else Outcome.BLACKJACK
    if dealer_hand.is_blackjack:
        return Outcome.LOSS
    if dealer_hand.is_bust or hand.total > dealer_hand.total:
        return Outcome.WIN
    if hand.total == dealer_hand.total:
        return Outcome.PUSH
    return Outcome.LOSS


def payout_multipliers(rules: HouseRules) -> dict[Outcome, Decimal]:
    """Total returned per unit staked (stake included)."""
    return {
        Outcome.BLACKJACK: 1 + rules.blackjack_pays,
        Outcome.WIN: Decimal("2"),
        Outcome.PUSH: Decimal("1"),
        Outcome.LOSS: Decimal("0"),
    }


@dataclass(frozen=True)
class HandResult:
    player: str
    hand: str
    outcome: Outcome
    bet: Decimal
    returned: Decimal

    @property
    def net(self) -> Decimal:
        return self.returned - self.bet


# --------------------------------------------------------------------------
# The round: an explicit state machine
# --------------------------------------------------------------------------
class Phase(Enum):
    BETTING = auto()
    INSURANCE = auto()
    PLAYER_TURNS = auto()
    DEALER_TURN = auto()
    SETTLED = auto()


TRANSITIONS: dict[Phase, frozenset[Phase]] = {
    Phase.BETTING: frozenset({Phase.INSURANCE, Phase.PLAYER_TURNS, Phase.SETTLED}),
    Phase.INSURANCE: frozenset({Phase.PLAYER_TURNS, Phase.SETTLED}),
    Phase.PLAYER_TURNS: frozenset({Phase.DEALER_TURN, Phase.SETTLED}),
    Phase.DEALER_TURN: frozenset({Phase.SETTLED}),
    Phase.SETTLED: frozenset(),
}


class Round:
    """One round of blackjack, from bets to payouts.

    Every public method is a *command*. Each one checks the phase, the turn
    and the legality of the move before mutating anything, so a remote client
    can never push the round into an invalid state. A lock serialises
    commands, and ``version`` lets clients reject double-submitted clicks.
    """

    def __init__(
        self,
        players: Sequence[Player],
        dealer: Dealer,
        shoe: Shoe,
        rules: HouseRules,
    ) -> None:
        self.players = list(players)
        self.dealer = dealer
        self.shoe = shoe
        self.rules = rules
        self.phase = Phase.BETTING
        self.version = 0
        self.results: list[HandResult] = []
        self.events: list[str] = []
        self._turn: tuple[int, int] = (0, 0)  # (player index, hand index)
        self._lock = threading.RLock()
        self.dealer.hand = Hand()
        for player in self.players:
            player.hands = []
            player.insurance = Decimal("0")

    # ---- state machine plumbing ------------------------------------------
    def _require(self, phase: Phase) -> None:
        if self.phase is not phase:
            raise InvalidPhase(f"expected {phase.name}, round is in {self.phase.name}")

    def _move_to(self, phase: Phase) -> None:
        if phase not in TRANSITIONS[self.phase]:
            raise InvalidPhase(f"cannot go from {self.phase.name} to {phase.name}")
        self._log(f"phase {self.phase.name} -> {phase.name}")
        self.phase = phase

    def _log(self, message: str) -> None:
        self.version += 1
        self.events.append(message)

    def _deal_to(self, hand: Hand) -> Card:
        card = self.shoe.draw()
        hand.add(card)
        return card

    # ---- BETTING ------------------------------------------------------------
    def place_bet(self, player: Player, amount: Decimal) -> None:
        with self._lock:
            self._require(Phase.BETTING)
            if player not in self.players:
                raise BlackjackError(f"{player.name} is not seated at this table")
            if player.hands:
                raise IllegalAction(f"{player.name} has already bet")
            if not self.rules.min_bet <= amount <= self.rules.max_bet:
                raise IllegalAction(
                    f"bet must be between {self.rules.min_bet} and {self.rules.max_bet}"
                )
            player.debit(amount)
            player.hands = [Hand(bet=amount)]
            self._log(f"{player.name} bets {amount}")

    def deal(self) -> None:
        with self._lock:
            self._require(Phase.BETTING)
            seated = [p for p in self.players if p.hands]
            if not seated:
                raise IllegalAction("nobody has placed a bet")
            self.players = seated  # players who sat out do not get cards
            for _ in range(2):  # one card each, dealer last, twice
                for player in self.players:
                    self._deal_to(player.hands[0])
                self._deal_to(self.dealer.hand)
            self._log(f"dealer shows {self.dealer.upcard}")
            if self.rules.offer_insurance and self.dealer.upcard.rank is Rank.ACE:
                self._move_to(Phase.INSURANCE)
            else:
                self._peek_then_play()

    # ---- INSURANCE ------------------------------------------------------------
    def take_insurance(self, player: Player) -> None:
        with self._lock:
            self._require(Phase.INSURANCE)
            if player.insurance:
                raise IllegalAction(f"{player.name} is already insured")
            cost = (player.hands[0].bet / 2).quantize(CENT, ROUND_DOWN)
            player.debit(cost)
            player.insurance = cost
            self._log(f"{player.name} takes insurance for {cost}")

    def close_insurance(self) -> None:
        with self._lock:
            self._require(Phase.INSURANCE)
            self._peek_then_play()

    def _peek_then_play(self) -> None:
        # US-style "peek": with an ace or ten showing, the dealer checks the
        # hole card first so players never lose extra money to a natural.
        if self.dealer.upcard.rank.points in (1, 10) and self.dealer.hand.is_blackjack:
            self._log("dealer peeks: blackjack")
            self._settle()
            return
        self._move_to(Phase.PLAYER_TURNS)
        self._turn = (0, 0)
        self._advance()

    # ---- PLAYER_TURNS -------------------------------------------------------
    @property
    def current(self) -> tuple[Player, Hand] | None:
        if self.phase is not Phase.PLAYER_TURNS:
            return None
        p, h = self._turn
        player = self.players[p]
        return player, player.hands[h]

    def allowed_actions(self) -> frozenset[Action]:
        turn = self.current
        if turn is None:
            return frozenset()
        player, hand = turn
        allowed = {Action.HIT, Action.STAND}
        can_afford = player.bankroll >= hand.bet
        if (
            len(hand.cards) == 2
            and can_afford
            and (not hand.from_split or self.rules.double_after_split)
        ):
            allowed.add(Action.DOUBLE)
        if (
            hand.is_pair
            and can_afford
            and len(player.hands) < self.rules.max_hands_per_player
        ):
            allowed.add(Action.SPLIT)
        return frozenset(allowed)

    def act(
        self, player: Player, action: Action, expected_version: int | None = None
    ) -> None:
        with self._lock:
            if expected_version is not None and expected_version != self.version:
                raise StaleCommand(
                    f"command built for v{expected_version}, round is at v{self.version}"
                )
            self._require(Phase.PLAYER_TURNS)
            current_player, hand = self.current  # type: ignore[misc]
            if player is not current_player:
                raise NotYourTurn(f"it is {current_player.name}'s turn")
            if action not in self.allowed_actions():
                raise IllegalAction(f"{action.name} is not allowed on {hand}")
            handler = {
                Action.HIT: self._hit,
                Action.STAND: self._stand,
                Action.DOUBLE: self._double,
                Action.SPLIT: self._split,
            }[action]
            handler(player, hand)
            self._advance()

    def _hit(self, player: Player, hand: Hand) -> None:
        card = self._deal_to(hand)
        self._log(f"{player.name} hits, draws {card}: {hand}")
        if hand.total >= 21:  # bust, or 21 with nothing left to decide
            hand.finished = True

    def _stand(self, player: Player, hand: Hand) -> None:
        hand.finished = True
        self._log(f"{player.name} stands on {hand.total}")

    def _double(self, player: Player, hand: Hand) -> None:
        player.debit(hand.bet)
        hand.bet *= 2
        hand.doubled = True
        card = self._deal_to(hand)
        hand.finished = True  # exactly one card after doubling
        self._log(f"{player.name} doubles to {hand.bet}, draws {card}: {hand}")

    def _split(self, player: Player, hand: Hand) -> None:
        player.debit(hand.bet)
        moved = hand.cards.pop()
        twin = Hand(bet=hand.bet, cards=[moved], from_split=True)
        hand.from_split = True
        index = player.hands.index(hand)
        player.hands.insert(index + 1, twin)
        self._deal_to(hand)
        self._deal_to(twin)
        split_aces = moved.rank is Rank.ACE
        for h in (hand, twin):
            # Split aces get one card each and no more: a near-universal rule.
            if split_aces or h.total == 21:
                h.finished = True
        self._log(f"{player.name} splits: {hand} and {twin}")

    def _advance(self) -> None:
        """Move the turn cursor to the first unfinished hand, or end the turns."""
        p, h = self._turn
        while p < len(self.players):
            hands = self.players[p].hands
            while h < len(hands):
                hand = hands[h]
                if hand.is_blackjack or hand.total >= 21:
                    hand.finished = True
                if not hand.finished:
                    self._turn = (p, h)
                    return
                h += 1
            p, h = p + 1, 0
        self._finish_player_turns()

    def _finish_player_turns(self) -> None:
        live = [
            hand
            for player in self.players
            for hand in player.hands
            if not hand.is_bust and not hand.is_blackjack
        ]
        if live:
            self._move_to(Phase.DEALER_TURN)
            self._play_dealer()
        self._settle()

    # ---- DEALER_TURN -------------------------------------------------------
    def _play_dealer(self) -> None:
        hand = self.dealer.hand
        self._log(f"dealer reveals {hand}")
        allowed = frozenset({Action.HIT, Action.STAND})
        while not hand.is_bust:
            action = self.dealer.strategy.decide(hand, self.dealer.upcard, allowed)
            if action is not Action.HIT:
                break
            card = self._deal_to(hand)
            self._log(f"dealer draws {card}: {hand}")
        self._log(f"dealer finishes with {hand}")

    # ---- SETTLED -------------------------------------------------------------
    def _settle(self) -> None:
        self._move_to(Phase.SETTLED)
        dealer_hand = self.dealer.hand
        multipliers = payout_multipliers(self.rules)
        for player in self.players:
            if player.insurance:
                if dealer_hand.is_blackjack:
                    player.credit(player.insurance * 3)  # pays 2:1, stake back
                    self._log(f"{player.name}'s insurance pays")
            for hand in player.hands:
                outcome = decide_outcome(hand, dealer_hand)
                returned = (hand.bet * multipliers[outcome]).quantize(CENT, ROUND_DOWN)
                player.credit(returned)
                self.results.append(
                    HandResult(player.name, str(hand), outcome, hand.bet, returned)
                )
                self._log(f"{player.name} {hand}: {outcome.name}, returned {returned}")


# --------------------------------------------------------------------------
# The table: runs rounds and owns the shoe between them
# --------------------------------------------------------------------------
class Table:
    """Owns the long-lived pieces (shoe, seats, rules) and drives rounds."""

    def __init__(
        self,
        rules: HouseRules | None = None,
        shoe: Shoe | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.rules = rules or HouseRules()
        self.shoe = shoe or Shoe(self.rules.decks, self.rules.penetration, rng)
        self.dealer = Dealer(DealerStrategy(self.rules.dealer_hits_soft_17))
        self.players: list[Player] = []

    def seat(self, player: Player) -> None:
        if any(p.name == player.name for p in self.players):
            raise BlackjackError(f"{player.name} is already seated")
        self.players.append(player)

    def new_round(self) -> Round:
        if self.shoe.cut_card_reached:
            self.shoe.shuffle()  # only between rounds, never mid-round
        return Round(self.players, self.dealer, self.shoe, self.rules)

    def play_round(self, bets: dict[str, Decimal]) -> Round:
        """Run a full round, asking each player's strategy for decisions."""
        rnd = self.new_round()
        for player in self.players:
            if player.name in bets:
                rnd.place_bet(player, bets[player.name])
        rnd.deal()
        if rnd.phase is Phase.INSURANCE:
            for player in rnd.players:
                if player.takes_insurance:
                    rnd.take_insurance(player)
            rnd.close_insurance()
        while (turn := rnd.current) is not None:
            player, hand = turn
            action = player.strategy.decide(
                hand, self.dealer.upcard, rnd.allowed_actions()
            )
            rnd.act(player, action)
        return rnd


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------
def demo() -> None:
    # A stacked shoe makes the demo tell the same story every time.
    # Deal order: Ana, Ben, dealer, Ana, Ben, dealer, then draws.
    order = cards(
        "8", "A", "6",   # first card: Ana 8, Ben A, dealer 6 (upcard)
        "8", "K", "10",  # second card: Ana 8 (pair!), Ben K (blackjack), dealer 10
        "3", "10",       # Ana splits 8s: first hand gets 3, second gets 10
        "9",             # Ana doubles 8+3=11 and draws 9 -> 20
        "7",             # dealer 16 must hit, draws 7 -> 23, bust
    )
    table = Table(HouseRules(), shoe=Shoe.stacked(order))
    ana = Player("Ana", Decimal("100"), ScriptedStrategy(Action.SPLIT, Action.DOUBLE))
    ben = Player("Ben", Decimal("100"), ThresholdStrategy(17))
    table.seat(ana)
    table.seat(ben)

    rnd = table.play_round({"Ana": Decimal("10"), "Ben": Decimal("10")})
    for line in rnd.events:
        print("  ", line)
    print()
    for r in rnd.results:
        print(f"  {r.player:4} {r.hand:28} {r.outcome.name:9} bet {r.bet:>6} net {r.net:+}")
    print(f"\n  Bankrolls: Ana {ana.bankroll}, Ben {ben.bankroll}")


if __name__ == "__main__":
    demo()
