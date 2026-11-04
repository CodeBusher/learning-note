"""Tic Tac Toe: the recommended object-oriented design.

Supports any rows x cols board with K-in-a-row to win (3x3/K=3 is classic
tic-tac-toe, 15x15/K=5 is Gomoku). The pure game model (Board, Game) knows
nothing about input or output; players are driven by pluggable strategies;
a GameRoom plays the role of an authoritative game server.
"""

from __future__ import annotations

import math
import random
import threading
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Callable, Iterable, Protocol, Sequence


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


class GameError(Exception):
    """Base class for every rule violation the game can report."""


class InvalidMoveError(GameError):
    """The target cell is off the board or already taken."""


class NotYourTurnError(GameError):
    """Someone tried to move out of turn."""


class GameOverError(GameError):
    """A move was attempted after the game finished."""


class NothingToUndoError(GameError):
    """Undo or redo was requested but there is nothing to revert."""


class StaleMoveError(GameError):
    """A client sent a move based on an out-of-date view of the game."""


# --------------------------------------------------------------------------
# Value objects
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Player:
    """A participant identified by name, playing with a one-character symbol."""

    name: str
    symbol: str

    def __post_init__(self) -> None:
        if len(self.symbol) != 1 or self.symbol in ". ":
            raise ValueError(f"symbol must be one visible character, got {self.symbol!r}")


@dataclass(frozen=True)
class Position:
    """A cell coordinate, zero-based, row first."""

    row: int
    col: int


@dataclass(frozen=True)
class Move:
    """An immutable record of who placed a mark where."""

    position: Position
    player: Player


class GameState(Enum):
    """The three states a game can be in. WON and DRAW are terminal."""

    IN_PROGRESS = auto()
    WON = auto()
    DRAW = auto()


# --------------------------------------------------------------------------
# Board
# --------------------------------------------------------------------------


class Board:
    """A rows x cols grid of cells. Owns cell storage and cell-level rules only."""

    def __init__(self, rows: int = 3, cols: int = 3) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("board needs at least one row and one column")
        self.rows = rows
        self.cols = cols
        self._cells: list[list[Player | None]] = [[None] * cols for _ in range(rows)]
        self._filled = 0

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def get(self, pos: Position) -> Player | None:
        if not self.in_bounds(pos):
            raise InvalidMoveError(f"{pos} is off the board")
        return self._cells[pos.row][pos.col]

    def place(self, pos: Position, player: Player) -> None:
        if self.get(pos) is not None:
            raise InvalidMoveError(f"cell ({pos.row}, {pos.col}) is already taken")
        self._cells[pos.row][pos.col] = player
        self._filled += 1

    def clear(self, pos: Position) -> None:
        if self.get(pos) is None:
            raise ValueError(f"cell ({pos.row}, {pos.col}) is already empty")
        self._cells[pos.row][pos.col] = None
        self._filled -= 1

    def is_full(self) -> bool:
        # A running counter makes this O(1) instead of scanning every cell.
        return self._filled == self.rows * self.cols

    def empty_positions(self) -> list[Position]:
        return [
            Position(r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self._cells[r][c] is None
        ]

    def snapshot(self) -> tuple[str, ...]:
        """A hashable picture of the board, used as a cache key by the AI."""
        return tuple(
            cell.symbol if cell else "." for row in self._cells for cell in row
        )


# --------------------------------------------------------------------------
# Win detection (Strategy)
# --------------------------------------------------------------------------


class WinChecker(Protocol):
    """Decides whether the move just placed on the board wins the game."""

    def after_place(self, board: Board, move: Move) -> bool: ...

    def after_undo(self, board: Board, move: Move) -> None: ...

    def fresh(self) -> WinChecker: ...


DIRECTIONS: tuple[tuple[int, int], ...] = ((0, 1), (1, 0), (1, 1), (1, -1))


class LastMoveWinChecker:
    """Looks only at the four lines through the last move.

    A new win must include the cell just played, so nothing else can have
    changed. Cost is O(K) per move, it works for any board shape and any K,
    and it keeps no state, so undo is free.
    """

    def __init__(self, k: int) -> None:
        if k < 1:
            raise ValueError("k must be at least 1")
        self.k = k

    def after_place(self, board: Board, move: Move) -> bool:
        for dr, dc in DIRECTIONS:
            run = 1
            run += self._count(board, move, dr, dc)
            run += self._count(board, move, -dr, -dc)
            if run >= self.k:
                return True
        return False

    def _count(self, board: Board, move: Move, dr: int, dc: int) -> int:
        """Count consecutive marks of the mover, walking away from the move."""
        count = 0
        r, c = move.position.row + dr, move.position.col + dc
        while count < self.k - 1:
            pos = Position(r, c)
            if not board.in_bounds(pos) or board.get(pos) != move.player:
                break
            count += 1
            r, c = r + dr, c + dc
        return count

    def after_undo(self, board: Board, move: Move) -> None:
        pass  # stateless: nothing to roll back

    def fresh(self) -> LastMoveWinChecker:
        return LastMoveWinChecker(self.k)


# --------------------------------------------------------------------------
# Game: the pure model
# --------------------------------------------------------------------------


class Game:
    """Rules and state of a single game. No printing, no input, no networking.

    The move history is the single source of truth: whose turn it is is
    derived from it, and undo/redo simply pop and push moves.
    """

    def __init__(
        self,
        players: Sequence[Player],
        rows: int = 3,
        cols: int = 3,
        k: int = 3,
        win_checker: WinChecker | None = None,
    ) -> None:
        if len(players) < 2:
            raise ValueError("need at least two players")
        if len({p.symbol for p in players}) != len(players):
            raise ValueError("players must use distinct symbols")
        if not 1 <= k <= max(rows, cols):
            raise ValueError(f"k={k} cannot fit on a {rows}x{cols} board")
        self.board = Board(rows, cols)
        self.k = k
        self._players = tuple(players)
        self._win_checker = win_checker or LastMoveWinChecker(k)
        self._history: list[Move] = []
        self._redo: list[Move] = []
        self._state = GameState.IN_PROGRESS
        self._winner: Player | None = None

    # ---- queries ---------------------------------------------------------
    @property
    def players(self) -> tuple[Player, ...]:
        return self._players

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def winner(self) -> Player | None:
        return self._winner

    @property
    def is_over(self) -> bool:
        return self._state is not GameState.IN_PROGRESS

    @property
    def history(self) -> tuple[Move, ...]:
        return tuple(self._history)

    @property
    def move_count(self) -> int:
        return len(self._history)

    @property
    def current_player(self) -> Player:
        return self._players[len(self._history) % len(self._players)]

    def legal_moves(self) -> list[Position]:
        return [] if self.is_over else self.board.empty_positions()

    # ---- commands --------------------------------------------------------
    def play(self, row: int, col: int, player: Player | None = None) -> GameState:
        """Place the current player's mark. Validates everything before mutating."""
        if self.is_over:
            raise GameOverError(f"game already finished: {self._state.name}")
        mover = self.current_player
        if player is not None and player != mover:
            raise NotYourTurnError(f"it is {mover.name}'s turn, not {player.name}'s")
        self._apply(Move(Position(row, col), mover))
        self._redo.clear()  # a new move invalidates the redo branch
        return self._state

    def undo(self) -> Move:
        if not self._history:
            raise NothingToUndoError("no moves to undo")
        move = self._history.pop()
        self.board.clear(move.position)
        self._win_checker.after_undo(self.board, move)
        # Any finished game becomes unfinished once its last move is removed.
        self._state, self._winner = GameState.IN_PROGRESS, None
        self._redo.append(move)
        return move

    def redo(self) -> Move:
        if not self._redo:
            raise NothingToUndoError("no moves to redo")
        move = self._redo.pop()
        self._apply(move)
        return move

    def clone(self) -> Game:
        """An independent copy (same rules, same history) for AI look-ahead."""
        copy = Game(
            self._players,
            self.board.rows,
            self.board.cols,
            self.k,
            self._win_checker.fresh(),
        )
        for move in self._history:
            copy._apply(move)
        return copy

    def _apply(self, move: Move) -> None:
        self.board.place(move.position, move.player)  # raises before any change
        self._history.append(move)
        if self._win_checker.after_place(self.board, move):
            self._state, self._winner = GameState.WON, move.player
        elif self.board.is_full():
            self._state = GameState.DRAW


# --------------------------------------------------------------------------
# Player strategies
# --------------------------------------------------------------------------


class MoveStrategy(Protocol):
    """Anything that can pick the next move for the player whose turn it is."""

    def choose_move(self, game: Game) -> Position: ...


class ScriptedStrategy:
    """Plays a fixed list of moves. Handy for demos, tests and replays."""

    def __init__(self, moves: Iterable[tuple[int, int]]) -> None:
        self._moves = iter(moves)

    def choose_move(self, game: Game) -> Position:
        row, col = next(self._moves)
        return Position(row, col)


class RandomStrategy:
    """Picks any legal cell uniformly at random."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def choose_move(self, game: Game) -> Position:
        return self._rng.choice(game.legal_moves())


def _wins_at(game: Game, pos: Position, player: Player) -> bool:
    """Would `player` win by marking `pos`? Works for either player."""
    board = game.clone().board
    board.place(pos, player)
    return LastMoveWinChecker(game.k).after_place(board, Move(pos, player))


class RuleBasedStrategy:
    """Classic heuristics: win, else block, else centre, else corner, else anything."""

    def choose_move(self, game: Game) -> Position:
        me = game.current_player
        moves = game.legal_moves()
        for pos in moves:
            if _wins_at(game, pos, me):
                return pos
        for opponent in (p for p in game.players if p != me):
            for pos in moves:
                if _wins_at(game, pos, opponent):
                    return pos
        centre = Position(game.board.rows // 2, game.board.cols // 2)
        if centre in moves:
            return centre
        last_r, last_c = game.board.rows - 1, game.board.cols - 1
        for corner in (Position(0, 0), Position(0, last_c), Position(last_r, 0), Position(last_r, last_c)):
            if corner in moves:
                return corner
        return moves[0]


class _Bound(Enum):
    EXACT = auto()
    LOWER = auto()
    UPPER = auto()


class MinimaxStrategy:
    """Perfect play via negamax with alpha-beta pruning and a transposition table.

    Scores are from the point of view of the side to move: a win is worth
    more the sooner it happens, a draw is 0. `max_depth` turns this into a
    depth-limited search for boards too large to solve completely.
    """

    def __init__(self, max_depth: int | None = None, memoize: bool = True) -> None:
        self.max_depth = max_depth
        self.memoize = memoize
        self.nodes_searched = 0
        self._table: dict[tuple, tuple[float, _Bound]] = {}

    def choose_move(self, game: Game) -> Position:
        if game.is_over:
            raise GameOverError("no move to choose in a finished game")
        sim = game.clone()  # never mutate the caller's game while thinking
        best_pos, best_score = None, -math.inf
        alpha, beta = -math.inf, math.inf
        for pos in self._ordered(sim):
            sim.play(pos.row, pos.col)
            score = -self._negamax(sim, 1, -beta, -alpha)
            sim.undo()
            if score > best_score:
                best_pos, best_score = pos, score
            alpha = max(alpha, score)
        assert best_pos is not None
        return best_pos

    def _negamax(self, game: Game, depth: int, alpha: float, beta: float) -> float:
        self.nodes_searched += 1
        if game.state is GameState.WON:
            # The player who just moved won, so this is a loss for the side to move.
            return -(1 + len(game.board.empty_positions()))
        if game.state is GameState.DRAW:
            return 0
        if self.max_depth is not None and depth >= self.max_depth:
            return 0  # unknown: treat as neutral

        key = self._key(game, depth)
        alpha_orig = alpha
        if self.memoize and key in self._table:
            value, bound = self._table[key]
            if bound is _Bound.EXACT:
                return value
            if bound is _Bound.LOWER:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        best = -math.inf
        for pos in self._ordered(game):
            game.play(pos.row, pos.col)
            score = -self._negamax(game, depth + 1, -beta, -alpha)
            game.undo()
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break  # the opponent will never allow this line

        if self.memoize:
            if best <= alpha_orig:
                bound = _Bound.UPPER
            elif best >= beta:
                bound = _Bound.LOWER
            else:
                bound = _Bound.EXACT
            self._table[key] = (best, bound)
        return best

    def _key(self, game: Game, depth: int) -> tuple:
        board = game.board
        remaining = None if self.max_depth is None else self.max_depth - depth
        return (board.rows, board.cols, game.k, board.snapshot(),
                game.current_player.symbol, remaining)

    @staticmethod
    def _ordered(game: Game) -> list[Position]:
        """Centre-first ordering makes alpha-beta cut off much earlier."""
        mid_r, mid_c = (game.board.rows - 1) / 2, (game.board.cols - 1) / 2
        return sorted(
            game.legal_moves(),
            key=lambda p: abs(p.row - mid_r) + abs(p.col - mid_c),
        )


# --------------------------------------------------------------------------
# I/O adapters: the only code that talks to a human
# --------------------------------------------------------------------------


def render(board: Board) -> str:
    """Pure function: board -> text. Any UI can reuse it or ignore it."""
    header = "    " + "   ".join(str(c) for c in range(board.cols))
    lines = [header]
    for r in range(board.rows):
        cells = [board.get(Position(r, c)) for c in range(board.cols)]
        marks = " | ".join(cell.symbol if cell else " " for cell in cells)
        lines.append(f"{r}   {marks}")
        if r < board.rows - 1:
            lines.append("   " + "+".join(["---"] * board.cols))
    return "\n".join(lines)


class GameView(Protocol):
    """Output port: whatever displays the game (console, GUI, websocket...)."""

    def show_board(self, board: Board) -> None: ...

    def show_message(self, text: str) -> None: ...


class ConsoleView:
    """Writes to a text stream; `output` is injectable so tests can capture it."""

    def __init__(self, output: Callable[[str], None] = print) -> None:
        self._output = output

    def show_board(self, board: Board) -> None:
        self._output(render(board))

    def show_message(self, text: str) -> None:
        self._output(text)


class ConsoleHumanStrategy:
    """Input adapter: turns typed text like '1 2' into a Position."""

    def __init__(self, input_fn: Callable[[str], str] = input,
                 output: Callable[[str], None] = print) -> None:
        self._input = input_fn
        self._output = output

    def choose_move(self, game: Game) -> Position:
        while True:
            raw = self._input(f"{game.current_player.name} ({game.current_player.symbol}), row col: ")
            parts = raw.replace(",", " ").split()
            if len(parts) == 2 and all(p.lstrip("-").isdigit() for p in parts):
                return Position(int(parts[0]), int(parts[1]))
            self._output("Please type two numbers, e.g. '1 2'.")


class GameRunner:
    """Application layer for a local game: asks strategies for moves, feeds the
    model, and tells the view what happened."""

    def __init__(self, game: Game, controllers: dict[Player, MoveStrategy],
                 view: GameView) -> None:
        missing = [p.name for p in game.players if p not in controllers]
        if missing:
            raise ValueError(f"no controller for {missing}")
        self.game = game
        self._controllers = controllers
        self._view = view

    def run(self) -> GameState:
        self._view.show_board(self.game.board)
        while not self.game.is_over:
            player = self.game.current_player
            pos = self._controllers[player].choose_move(self.game)
            try:
                self.game.play(pos.row, pos.col, player)
            except InvalidMoveError as exc:
                self._view.show_message(f"Invalid move: {exc}. Try again.")
                continue
            self._view.show_message(f"{player.name} plays ({pos.row}, {pos.col})")
            self._view.show_board(self.game.board)
        if self.game.state is GameState.WON:
            self._view.show_message(f"{self.game.winner.name} wins!")
        else:
            self._view.show_message("It's a draw.")
        return self.game.state


# --------------------------------------------------------------------------
# Scoreboard
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PlayerRecord:
    """Lifetime stats for one player across many games."""

    wins: int = 0
    losses: int = 0
    draws: int = 0
    rating: float = 1200.0

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws


class ScoreTracker:
    """Cross-game win/loss/draw counts and Elo ratings, keyed by player name.

    Lives outside Game because ratings depend on many games and many players.
    Thread-safe so a server can report finished games concurrently.
    """

    def __init__(self, k_factor: float = 32.0, initial_rating: float = 1200.0) -> None:
        self._k = k_factor
        self._initial = initial_rating
        self._records: dict[str, PlayerRecord] = {}
        self._lock = threading.Lock()

    def report(self, game: Game) -> None:
        if not game.is_over:
            raise ValueError("cannot report a game that is still in progress")
        if len(game.players) != 2:
            raise ValueError("ratings are defined for two-player games only")
        self.record_result(game.players[0], game.players[1], game.winner)

    def record_result(self, a: Player, b: Player, winner: Player | None) -> None:
        if winner is not None and winner not in (a, b):
            raise ValueError("winner must be one of the two players")
        score_a = 0.5 if winner is None else (1.0 if winner == a else 0.0)
        with self._lock:
            ra = self._records.get(a.name, PlayerRecord(rating=self._initial))
            rb = self._records.get(b.name, PlayerRecord(rating=self._initial))
            expected_a = 1 / (1 + 10 ** ((rb.rating - ra.rating) / 400))
            delta = self._k * (score_a - expected_a)
            self._records[a.name] = self._bump(ra, score_a, ra.rating + delta)
            self._records[b.name] = self._bump(rb, 1 - score_a, rb.rating - delta)

    @staticmethod
    def _bump(rec: PlayerRecord, score: float, rating: float) -> PlayerRecord:
        if score == 1.0:
            return replace(rec, wins=rec.wins + 1, rating=rating)
        if score == 0.0:
            return replace(rec, losses=rec.losses + 1, rating=rating)
        return replace(rec, draws=rec.draws + 1, rating=rating)

    def record_for(self, name: str) -> PlayerRecord:
        with self._lock:
            return self._records.get(name, PlayerRecord(rating=self._initial))

    def leaderboard(self, top: int | None = None) -> list[tuple[str, PlayerRecord]]:
        with self._lock:
            ranked = sorted(self._records.items(),
                            key=lambda item: (-item[1].rating, -item[1].wins, item[0]))
        return ranked if top is None else ranked[:top]

    def rank(self, name: str) -> int:
        for position, (player_name, _) in enumerate(self.leaderboard(), start=1):
            if player_name == name:
                return position
        raise KeyError(f"{name} has no recorded games")


# --------------------------------------------------------------------------
# Authoritative server-side room
# --------------------------------------------------------------------------


class GameRoom:
    """Server-side owner of one game. Clients only *request* moves; the room
    validates them, applies them one at a time, and reports the result once."""

    def __init__(self, game: Game, tracker: ScoreTracker | None = None) -> None:
        self.game = game
        self._tracker = tracker
        self._lock = threading.Lock()
        self._reported = False
        self._by_name = {p.name: p for p in game.players}

    def submit_move(self, player_name: str, row: int, col: int,
                    expected_move_number: int) -> GameState:
        with self._lock:
            player = self._player(player_name)
            # Optimistic concurrency: reject moves made against an old board.
            if expected_move_number != self.game.move_count:
                raise StaleMoveError(
                    f"move #{expected_move_number} is stale; game is at #{self.game.move_count}"
                )
            state = self.game.play(row, col, player)
            if self.game.is_over and self._tracker and not self._reported:
                self._tracker.report(self.game)
                self._reported = True
            return state

    def take_back(self, player_name: str) -> Move:
        """Let a player retract their own last move while the game is still open."""
        with self._lock:
            player = self._player(player_name)
            if self._reported:
                raise GameOverError("result already recorded; take-backs are closed")
            history = self.game.history
            if not history or history[-1].player != player:
                raise NotYourTurnError("you can only take back your own last move")
            return self.game.undo()

    def snapshot(self) -> dict[str, object]:
        """What a server would broadcast to every connected client."""
        with self._lock:
            g = self.game
            return {
                "board": g.board.snapshot(),
                "move_number": g.move_count,
                "state": g.state.name,
                "to_move": None if g.is_over else g.current_player.name,
                "winner": g.winner.name if g.winner else None,
            }

    def _player(self, name: str) -> Player:
        try:
            return self._by_name[name]
        except KeyError:
            raise NotYourTurnError(f"{name} is not seated in this game") from None


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------


def demo() -> None:
    alice, bob = Player("Alice", "X"), Player("Bob", "O")
    tracker = ScoreTracker()
    view = ConsoleView()

    print("=== 1. Scripted 3x3 game (Alice wins on the diagonal) ===")
    game = Game([alice, bob])
    GameRunner(game, {
        alice: ScriptedStrategy([(0, 0), (1, 1), (2, 2)]),
        bob: ScriptedStrategy([(0, 1), (0, 2)]),
    }, view).run()
    tracker.report(game)

    print("\n=== 2. Undo and redo ===")
    game = Game([alice, bob])
    game.play(1, 1)
    game.play(0, 0)
    undone = game.undo()
    print(f"undid {undone.player.name} at {undone.position}; now {game.current_player.name} to move")
    game.redo()
    print(f"redo restores it; move count = {game.move_count}")
    try:
        game.play(1, 1)
    except InvalidMoveError as exc:
        print(f"rejected: {exc}")

    print("\n=== 3. AI vs AI on 3x3 ===")
    perfect = MinimaxStrategy()
    for label, opponent in [("minimax", MinimaxStrategy()), ("rule-based", RuleBasedStrategy()),
                            ("random", RandomStrategy(random.Random(7)))]:
        g = Game([alice, bob])
        GameRunner(g, {alice: perfect, bob: opponent}, ConsoleView(lambda _: None)).run()
        tracker.report(g)
        result = f"{g.winner.name} wins" if g.winner else "draw"
        print(f"minimax (Alice) vs {label} (Bob): {result} in {g.move_count} moves")

    print("\n=== 4. 5x5 board, 4 in a row ===")
    g = Game([alice, bob], rows=5, cols=5, k=4)
    GameRunner(g, {alice: RuleBasedStrategy(), bob: RandomStrategy(random.Random(3))},
               ConsoleView(lambda _: None)).run()
    print(render(g.board))
    print(f"result: {g.state.name}, winner: {g.winner.name if g.winner else '-'}")

    print("\n=== 5. Authoritative game room ===")
    room = GameRoom(Game([alice, bob]), tracker)
    room.submit_move("Alice", 1, 1, expected_move_number=0)
    try:
        room.submit_move("Bob", 0, 0, expected_move_number=0)  # Bob's client is behind
    except StaleMoveError as exc:
        print(f"rejected: {exc}")
    room.submit_move("Bob", 0, 0, expected_move_number=1)
    print(room.snapshot())

    print("\n=== Leaderboard ===")
    for rank, (name, rec) in enumerate(tracker.leaderboard(), start=1):
        print(f"{rank}. {name:<6} rating={rec.rating:7.1f}  W{rec.wins} L{rec.losses} D{rec.draws}")


if __name__ == "__main__":
    demo()
