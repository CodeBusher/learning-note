"""Competing designs for the decision points discussed in the post.

Each section is runnable on its own and plugs into the recommended model in
tic_tac_toe.py wherever that makes the comparison fair.
"""

from __future__ import annotations

import copy
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from tic_tac_toe import (
    Board,
    Game,
    GameOverError,
    GameState,
    InvalidMoveError,
    LastMoveWinChecker,
    MinimaxStrategy,
    Move,
    Player,
    Position,
    render,
)


# ==========================================================================
# Decision 1: win detection
# ==========================================================================


class FullScanWinChecker:
    """Approach A: after every move, scan every line on the whole board.

    Simple and obviously correct, but O(rows * cols * K) per move.
    """

    def __init__(self, k: int) -> None:
        self.k = k

    def after_place(self, board: Board, move: Move) -> bool:
        return self.find_winner(board) is not None

    def find_winner(self, board: Board) -> Player | None:
        for r in range(board.rows):
            for c in range(board.cols):
                first = board.get(Position(r, c))
                if first is None:
                    continue
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    end_r, end_c = r + dr * (self.k - 1), c + dc * (self.k - 1)
                    if not board.in_bounds(Position(end_r, end_c)):
                        continue
                    if all(board.get(Position(r + dr * i, c + dc * i)) == first
                           for i in range(self.k)):
                        return first
        return None

    def after_undo(self, board: Board, move: Move) -> None:
        pass

    def fresh(self) -> FullScanWinChecker:
        return FullScanWinChecker(self.k)


class CounterWinChecker:
    """Approach C: keep a running count per (player, line). O(1) per move.

    Only valid when K == N on an N x N board, because a "line" is a whole
    row, column or diagonal. Undo has to decrement the same counters.
    """

    def __init__(self, n: int) -> None:
        self.n = n
        self._rows: dict[tuple[Player, int], int] = {}
        self._cols: dict[tuple[Player, int], int] = {}
        self._diag: dict[Player, int] = {}
        self._anti: dict[Player, int] = {}

    def after_place(self, board: Board, move: Move) -> bool:
        if board.rows != self.n or board.cols != self.n:
            raise ValueError("CounterWinChecker needs an N x N board with K == N")
        return self._update(move, +1)

    def after_undo(self, board: Board, move: Move) -> None:
        self._update(move, -1)

    def _update(self, move: Move, step: int) -> bool:
        p, r, c = move.player, move.position.row, move.position.col
        counts = [self._bump(self._rows, (p, r), step), self._bump(self._cols, (p, c), step)]
        if r == c:
            counts.append(self._bump(self._diag, p, step))
        if r + c == self.n - 1:
            counts.append(self._bump(self._anti, p, step))
        return any(count == self.n for count in counts)

    @staticmethod
    def _bump(table: dict, key: object, step: int) -> int:
        table[key] = table.get(key, 0) + step
        return table[key]

    def fresh(self) -> CounterWinChecker:
        return CounterWinChecker(self.n)


def benchmark_win_checkers(n: int = 25, games: int = 2, seed: int = 1) -> dict[str, float]:
    """Average microseconds per move for each checker on an N x N, K = N board."""
    results: dict[str, float] = {}
    a, b = Player("A", "X"), Player("B", "O")
    factories: dict[str, Callable[[], object]] = {
        "full scan": lambda: FullScanWinChecker(n),
        "last move": lambda: LastMoveWinChecker(n),
        "counters": lambda: CounterWinChecker(n),
    }
    for name, factory in factories.items():
        rng = random.Random(seed)
        moves, elapsed = 0, 0.0
        for _ in range(games):
            game = Game([a, b], rows=n, cols=n, k=n, win_checker=factory())
            cells = game.board.empty_positions()
            rng.shuffle(cells)
            for pos in cells:
                start = time.perf_counter()
                game.play(pos.row, pos.col)
                elapsed += time.perf_counter() - start
                moves += 1
                if game.is_over:
                    break
        results[name] = elapsed / moves * 1e6
    return results


# ==========================================================================
# Decision 2: player types
# ==========================================================================


def choose_move_with_if_else(kind: str, game: Game,
                             input_fn: Callable[[str], str] = input) -> Position:
    """Approach A: one function that switches on a type tag. Every new AI
    level means editing this function (violates the Open/Closed Principle)."""
    if kind == "human":
        row, col = map(int, input_fn("row col: ").split())
        return Position(row, col)
    if kind == "random":
        return random.choice(game.legal_moves())
    if kind == "first-free":
        return game.legal_moves()[0]
    raise ValueError(f"unknown player kind {kind!r}")


class InheritedPlayer(ABC):
    """Approach B: behaviour baked into a Player subclass hierarchy. Identity
    (name, symbol) and behaviour (how to pick a move) are welded together, so
    a human cannot switch to 'AI takes over' mid-game without a new object."""

    def __init__(self, name: str, symbol: str) -> None:
        self.identity = Player(name, symbol)

    @abstractmethod
    def next_move(self, game: Game) -> Position: ...


class FirstFreeCellPlayer(InheritedPlayer):
    def next_move(self, game: Game) -> Position:
        return game.legal_moves()[0]


class PlainMinimaxStrategy:
    """Minimax without pruning or memoisation, for comparing search effort."""

    def __init__(self) -> None:
        self.nodes_searched = 0

    def choose_move(self, game: Game) -> Position:
        sim = game.clone()
        best, best_score = None, float("-inf")
        for pos in sim.legal_moves():
            sim.play(pos.row, pos.col)
            score = -self._negamax(sim)
            sim.undo()
            if score > best_score:
                best, best_score = pos, score
        assert best is not None
        return best

    def _negamax(self, game: Game) -> float:
        self.nodes_searched += 1
        if game.state is GameState.WON:
            return -(1 + len(game.board.empty_positions()))
        if game.state is GameState.DRAW:
            return 0
        best = float("-inf")
        for pos in game.legal_moves():
            game.play(pos.row, pos.col)
            best = max(best, -self._negamax(game))
            game.undo()
        return best


def compare_search_effort() -> dict[str, int]:
    """Nodes searched to answer one opening move on 3x3 (X already in a corner)."""
    a, b = Player("A", "X"), Player("B", "O")
    game = Game([a, b])
    game.play(0, 0)
    results: dict[str, int] = {}
    for name, strategy in [
        ("plain minimax", PlainMinimaxStrategy()),
        ("alpha-beta", MinimaxStrategy(memoize=False)),
        ("alpha-beta + memo", MinimaxStrategy()),
    ]:
        strategy.choose_move(game)
        results[name] = strategy.nodes_searched
    return results


# ==========================================================================
# Decision 3: game state and turn management
# ==========================================================================


class FlagsGame:
    """Approach A: booleans and a mutable turn index.

    Nothing stops `is_over=False` with `winner` set, or a forgotten turn
    flip after undo: the flags can drift into combinations that mean nothing.
    """

    def __init__(self, players: list[Player]) -> None:
        self.board = Board()
        self.players = players
        self.turn = 0
        self.is_over = False
        self.is_draw = False
        self.winner: Player | None = None
        self._checker = LastMoveWinChecker(3)

    def play(self, row: int, col: int) -> None:
        if self.is_over:
            raise GameOverError("game over")
        player = self.players[self.turn]
        move = Move(Position(row, col), player)
        self.board.place(move.position, player)
        if self._checker.after_place(self.board, move):
            self.is_over, self.winner = True, player
        elif self.board.is_full():
            self.is_over, self.is_draw = True, True
        self.turn = (self.turn + 1) % len(self.players)


class _State(ABC):
    """Approach C: the State pattern. Each state object decides what `play` means."""

    @abstractmethod
    def play(self, game: StatePatternGame, row: int, col: int) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class _InProgress(_State):
    name = "IN_PROGRESS"

    def play(self, game: StatePatternGame, row: int, col: int) -> None:
        player = game.players[len(game.history) % 2]
        move = Move(Position(row, col), player)
        game.board.place(move.position, player)
        game.history.append(move)
        if game.checker.after_place(game.board, move):
            game.state = _Won(player)
        elif game.board.is_full():
            game.state = _Drawn()


class _Won(_State):
    name = "WON"

    def __init__(self, winner: Player) -> None:
        self.winner = winner

    def play(self, game: StatePatternGame, row: int, col: int) -> None:
        raise GameOverError(f"{self.winner.name} already won")


class _Drawn(_State):
    name = "DRAW"

    def play(self, game: StatePatternGame, row: int, col: int) -> None:
        raise GameOverError("the game was a draw")


class StatePatternGame:
    """Context object that delegates `play` to its current state."""

    def __init__(self, players: list[Player]) -> None:
        self.board = Board()
        self.players = players
        self.history: list[Move] = []
        self.checker = LastMoveWinChecker(3)
        self.state: _State = _InProgress()

    def play(self, row: int, col: int) -> None:
        self.state.play(self, row, col)


# ==========================================================================
# Decision 4: undo
# ==========================================================================


@dataclass(frozen=True)
class BoardMemento:
    """Approach A (classic Memento): a full deep copy of the board."""

    board: Board


class SnapshotHistory:
    """Caretaker that stores a snapshot before every move. O(N^2) memory per move."""

    def __init__(self) -> None:
        self._stack: list[BoardMemento] = []

    def save(self, board: Board) -> None:
        self._stack.append(BoardMemento(copy.deepcopy(board)))

    def restore(self) -> Board:
        if not self._stack:
            raise IndexError("nothing to undo")
        return self._stack.pop().board


class PlaceMarkCommand:
    """Approach B (Command): an object that knows how to do and undo itself."""

    def __init__(self, board: Board, position: Position, player: Player) -> None:
        self.board, self.position, self.player = board, position, player

    def execute(self) -> None:
        self.board.place(self.position, self.player)

    def undo(self) -> None:
        self.board.clear(self.position)


class CommandHistory:
    """Invoker with undo and redo stacks of commands."""

    def __init__(self) -> None:
        self._done: list[PlaceMarkCommand] = []
        self._undone: list[PlaceMarkCommand] = []

    def run(self, command: PlaceMarkCommand) -> None:
        command.execute()
        self._done.append(command)
        self._undone.clear()

    def undo(self) -> None:
        command = self._done.pop()
        command.undo()
        self._undone.append(command)

    def redo(self) -> None:
        command = self._undone.pop()
        command.execute()
        self._done.append(command)


# ==========================================================================
# Decision 5: game logic vs I/O
# ==========================================================================


class MonolithicTicTacToe:
    """Approach A: rules, input and printing tangled in one loop.

    To test it you must fake stdin; to put it on the web you must rewrite it.
    """

    def __init__(self, input_fn: Callable[[str], str] = input,
                 print_fn: Callable[[str], None] = print) -> None:
        self.grid = [[" "] * 3 for _ in range(3)]
        self.input, self.print = input_fn, print_fn

    def play(self) -> str:
        symbol = "X"
        for _ in range(9):
            while True:
                row, col = map(int, self.input(f"{symbol} row col: ").split())
                if self.grid[row][col] == " ":
                    break
                self.print("taken, try again")
            self.grid[row][col] = symbol
            lines = self.grid + [list(c) for c in zip(*self.grid)]
            lines += [[self.grid[i][i] for i in range(3)], [self.grid[i][2 - i] for i in range(3)]]
            if any(line == [symbol] * 3 for line in lines):
                self.print(f"{symbol} wins")
                return symbol
            symbol = "O" if symbol == "X" else "X"
        self.print("draw")
        return "draw"


# ==========================================================================
# Extension: Connect Four reuses the model with a gravity rule
# ==========================================================================


class ConnectFourGame(Game):
    """6 x 7 board, 4 in a row, and pieces fall to the lowest empty cell."""

    def __init__(self, players: list[Player]) -> None:
        super().__init__(players, rows=6, cols=7, k=4)

    def drop(self, col: int, player: Player | None = None) -> GameState:
        if not 0 <= col < self.board.cols:
            raise InvalidMoveError(f"column {col} does not exist")
        for row in range(self.board.rows - 1, -1, -1):
            if self.board.get(Position(row, col)) is None:
                return super().play(row, col, player)
        raise InvalidMoveError(f"column {col} is full")

    def play(self, row: int, col: int, player: Player | None = None) -> GameState:
        raise InvalidMoveError("Connect Four moves pick a column: use drop(col)")

    def legal_moves(self) -> list[Position]:
        # Only the lowest empty cell of each column is playable.
        if self.is_over:
            return []
        moves = []
        for col in range(self.board.cols):
            for row in range(self.board.rows - 1, -1, -1):
                if self.board.get(Position(row, col)) is None:
                    moves.append(Position(row, col))
                    break
        return moves


# ==========================================================================
# Demo
# ==========================================================================


def demo() -> None:
    a, b = Player("Ann", "X"), Player("Ben", "O")

    print("=== Win detection: microseconds per move on 25x25, K=25 ===")
    for name, micros in benchmark_win_checkers().items():
        print(f"  {name:<10} {micros:9.1f} us")

    print("\n=== Search effort for one move (3x3, X in a corner) ===")
    for name, nodes in compare_search_effort().items():
        print(f"  {name:<18} {nodes:>7,} nodes")

    print("\n=== State pattern game ===")
    g = StatePatternGame([a, b])
    for r, c in [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)]:
        g.play(r, c)
    print(f"  state={g.state.name}")
    try:
        g.play(2, 2)
    except GameOverError as exc:
        print(f"  rejected: {exc}")

    print("\n=== Command-based undo/redo ===")
    board = Board()
    history = CommandHistory()
    history.run(PlaceMarkCommand(board, Position(1, 1), a))
    history.run(PlaceMarkCommand(board, Position(0, 0), b))
    history.undo()
    print(f"  after undo, (0,0) is {board.get(Position(0, 0))}")
    history.redo()
    print(f"  after redo, (0,0) is {board.get(Position(0, 0)).name}")

    print("\n=== Monolithic game with scripted input ===")
    script = iter(["0 0", "1 0", "0 1", "1 1", "0 2"])
    MonolithicTicTacToe(lambda _: next(script), lambda s: print("  " + s)).play()

    print("\n=== Connect Four on the same model ===")
    c4 = ConnectFourGame([a, b])
    for col in [3, 3, 4, 4, 5, 5, 6]:
        c4.drop(col)
    print(render(c4.board))
    print(f"  {c4.state.name}: {c4.winner.name}")

    print("\n=== Gomoku is just configuration ===")
    gomoku = Game([a, b], rows=15, cols=15, k=5)
    for i in range(4):
        gomoku.play(7, 3 + i)
        gomoku.play(0, i)
    gomoku.play(7, 7)
    print(f"  15x15, K=5: {gomoku.state.name}, winner {gomoku.winner.name}")


if __name__ == "__main__":
    demo()
