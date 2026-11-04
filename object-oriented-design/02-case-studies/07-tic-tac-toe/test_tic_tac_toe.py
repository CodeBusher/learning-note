"""Unit tests for the tic-tac-toe design (standard library unittest only)."""

from __future__ import annotations

import random
import threading
import unittest

from tic_tac_toe import (
    Board,
    ConsoleHumanStrategy,
    ConsoleView,
    Game,
    GameOverError,
    GameRoom,
    GameRunner,
    GameState,
    InvalidMoveError,
    LastMoveWinChecker,
    MinimaxStrategy,
    NothingToUndoError,
    NotYourTurnError,
    Player,
    Position,
    RandomStrategy,
    RuleBasedStrategy,
    ScoreTracker,
    ScriptedStrategy,
    StaleMoveError,
    render,
)
from alternatives import (
    CommandHistory,
    ConnectFourGame,
    CounterWinChecker,
    FlagsGame,
    FullScanWinChecker,
    MonolithicTicTacToe,
    PlaceMarkCommand,
    PlainMinimaxStrategy,
    SnapshotHistory,
    StatePatternGame,
    compare_search_effort,
)

X = Player("Xena", "X")
O = Player("Omar", "O")


def play_all(game: Game, moves: list[tuple[int, int]]) -> GameState:
    state = game.state
    for r, c in moves:
        state = game.play(r, c)
    return state


class BoardTests(unittest.TestCase):
    def test_place_get_and_full(self) -> None:
        board = Board(1, 2)
        board.place(Position(0, 0), X)
        self.assertEqual(board.get(Position(0, 0)), X)
        self.assertFalse(board.is_full())
        board.place(Position(0, 1), O)
        self.assertTrue(board.is_full())

    def test_rejects_occupied_and_out_of_bounds(self) -> None:
        board = Board()
        board.place(Position(1, 1), X)
        with self.assertRaises(InvalidMoveError):
            board.place(Position(1, 1), O)
        with self.assertRaises(InvalidMoveError):
            board.place(Position(3, 0), O)
        with self.assertRaises(InvalidMoveError):
            board.get(Position(-1, 0))

    def test_clear_and_empty_positions(self) -> None:
        board = Board(2, 2)
        board.place(Position(0, 1), X)
        self.assertNotIn(Position(0, 1), board.empty_positions())
        board.clear(Position(0, 1))
        self.assertEqual(len(board.empty_positions()), 4)
        with self.assertRaises(ValueError):
            board.clear(Position(0, 1))

    def test_render_shows_symbols(self) -> None:
        board = Board()
        board.place(Position(0, 2), O)
        self.assertIn("O", render(board))


class WinDetectionTests(unittest.TestCase):
    """Every checker must agree on every kind of line."""

    LINES = {
        "row": [(1, 0), (0, 0), (1, 1), (0, 1), (1, 2)],
        "column": [(0, 2), (0, 0), (1, 2), (0, 1), (2, 2)],
        "diagonal": [(0, 0), (0, 1), (1, 1), (0, 2), (2, 2)],
        "anti-diagonal": [(0, 2), (0, 0), (1, 1), (0, 1), (2, 0)],
    }

    def checkers(self):
        return [LastMoveWinChecker(3), FullScanWinChecker(3), CounterWinChecker(3)]

    def test_all_lines_with_all_checkers(self) -> None:
        for checker in self.checkers():
            for name, moves in self.LINES.items():
                with self.subTest(checker=type(checker).__name__, line=name):
                    game = Game([X, O], win_checker=checker.fresh())
                    self.assertEqual(play_all(game, moves), GameState.WON)
                    self.assertEqual(game.winner, X)

    def test_draw(self) -> None:
        moves = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0), (1, 2), (2, 1), (2, 0), (2, 2)]
        for checker in self.checkers():
            with self.subTest(checker=type(checker).__name__):
                game = Game([X, O], win_checker=checker.fresh())
                self.assertEqual(play_all(game, moves), GameState.DRAW)
                self.assertIsNone(game.winner)

    def test_k_smaller_than_n(self) -> None:
        game = Game([X, O], rows=5, cols=5, k=4)
        moves = [(4, 1), (0, 0), (3, 2), (0, 1), (2, 3), (0, 2), (1, 4)]
        self.assertEqual(play_all(game, moves), GameState.WON)

    def test_three_of_four_is_not_a_win_when_k_is_four(self) -> None:
        game = Game([X, O], rows=4, cols=4, k=4)
        state = play_all(game, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
        self.assertEqual(state, GameState.IN_PROGRESS)

    def test_counter_checker_rejects_wrong_board(self) -> None:
        game = Game([X, O], rows=4, cols=4, k=3, win_checker=CounterWinChecker(3))
        with self.assertRaises(ValueError):
            game.play(0, 0)

    def test_checkers_agree_on_random_games(self) -> None:
        rng = random.Random(42)
        for _ in range(200):
            cells = [(r, c) for r in range(4) for c in range(4)]
            rng.shuffle(cells)
            results = []
            for checker in (LastMoveWinChecker(4), FullScanWinChecker(4), CounterWinChecker(4)):
                game = Game([X, O], rows=4, cols=4, k=4, win_checker=checker)
                for r, c in cells:
                    game.play(r, c)
                    if game.is_over:
                        break
                results.append((game.state, game.winner, game.move_count))
            self.assertEqual(len(set(results)), 1, results)


class GameRuleTests(unittest.TestCase):
    def test_turns_alternate(self) -> None:
        game = Game([X, O])
        self.assertEqual(game.current_player, X)
        game.play(0, 0)
        self.assertEqual(game.current_player, O)

    def test_not_your_turn(self) -> None:
        game = Game([X, O])
        with self.assertRaises(NotYourTurnError):
            game.play(0, 0, O)

    def test_invalid_move_does_not_change_state(self) -> None:
        game = Game([X, O])
        game.play(1, 1)
        with self.assertRaises(InvalidMoveError):
            game.play(1, 1)
        self.assertEqual(game.move_count, 1)
        self.assertEqual(game.current_player, O)

    def test_no_moves_after_game_over(self) -> None:
        game = Game([X, O])
        play_all(game, WinDetectionTests.LINES["row"])
        with self.assertRaises(GameOverError):
            game.play(2, 2)
        self.assertEqual(game.legal_moves(), [])

    def test_constructor_validation(self) -> None:
        with self.assertRaises(ValueError):
            Game([X])
        with self.assertRaises(ValueError):
            Game([X, Player("Other", "X")])
        with self.assertRaises(ValueError):
            Game([X, O], rows=3, cols=3, k=4)
        with self.assertRaises(ValueError):
            Player("Bad", "XO")

    def test_three_player_game(self) -> None:
        z = Player("Zed", "Z")
        game = Game([X, O, z], rows=4, cols=4, k=3)
        game.play(0, 0)
        game.play(1, 0)
        self.assertEqual(game.current_player, z)


class UndoRedoTests(unittest.TestCase):
    def test_undo_restores_cell_and_turn(self) -> None:
        game = Game([X, O])
        game.play(0, 0)
        game.play(1, 1)
        move = game.undo()
        self.assertEqual(move.player, O)
        self.assertIsNone(game.board.get(Position(1, 1)))
        self.assertEqual(game.current_player, O)

    def test_undo_winning_move_reopens_game(self) -> None:
        for checker in (LastMoveWinChecker(3), CounterWinChecker(3)):
            with self.subTest(checker=type(checker).__name__):
                game = Game([X, O], win_checker=checker)
                play_all(game, WinDetectionTests.LINES["row"])
                game.undo()
                self.assertEqual(game.state, GameState.IN_PROGRESS)
                self.assertIsNone(game.winner)
                game.play(2, 2)  # Xena plays elsewhere: must not be a win
                self.assertEqual(game.state, GameState.IN_PROGRESS)

    def test_redo_and_new_move_clears_redo(self) -> None:
        game = Game([X, O])
        game.play(0, 0)
        game.undo()
        game.redo()
        self.assertEqual(game.board.get(Position(0, 0)), X)
        game.undo()
        game.play(2, 2)
        with self.assertRaises(NothingToUndoError):
            game.redo()

    def test_undo_on_empty_game(self) -> None:
        with self.assertRaises(NothingToUndoError):
            Game([X, O]).undo()

    def test_clone_is_independent(self) -> None:
        game = Game([X, O])
        game.play(0, 0)
        copy = game.clone()
        copy.play(1, 1)
        self.assertEqual(game.move_count, 1)
        self.assertEqual(copy.move_count, 2)


class StrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        # X: (0,0) (0,1); O: (1,0) (1,1). X to move can win at (0,2).
        self.game = Game([X, O])
        play_all(self.game, [(0, 0), (1, 0), (0, 1), (1, 1)])

    def test_rule_based_takes_win(self) -> None:
        self.assertEqual(RuleBasedStrategy().choose_move(self.game), Position(0, 2))

    def test_rule_based_blocks(self) -> None:
        game = Game([X, O])
        play_all(game, [(0, 0), (1, 1), (0, 1)])  # O must block at (0, 2)
        self.assertEqual(RuleBasedStrategy().choose_move(game), Position(0, 2))

    def test_minimax_takes_win_and_blocks(self) -> None:
        self.assertEqual(MinimaxStrategy().choose_move(self.game), Position(0, 2))
        game = Game([X, O])
        play_all(game, [(0, 0), (1, 1), (0, 1)])
        self.assertEqual(MinimaxStrategy().choose_move(game), Position(0, 2))

    def test_minimax_does_not_mutate_game(self) -> None:
        before = self.game.board.snapshot()
        MinimaxStrategy().choose_move(self.game)
        self.assertEqual(self.game.board.snapshot(), before)

    def test_minimax_self_play_is_a_draw(self) -> None:
        game = Game([X, O])
        ai = MinimaxStrategy()
        GameRunner(game, {X: ai, O: ai}, ConsoleView(lambda _: None)).run()
        self.assertEqual(game.state, GameState.DRAW)

    def test_minimax_never_loses_to_random(self) -> None:
        ai = MinimaxStrategy()
        for seed in range(20):
            for ai_first in (True, False):
                players = [X, O] if ai_first else [O, X]
                game = Game(players)
                rand = RandomStrategy(random.Random(seed))
                GameRunner(game, {X: ai, O: rand}, ConsoleView(lambda _: None)).run()
                self.assertNotEqual(game.winner, O, f"seed {seed}")

    def test_memo_and_pruning_search_less(self) -> None:
        effort = compare_search_effort()
        self.assertLess(effort["alpha-beta"], effort["plain minimax"])
        self.assertLess(effort["alpha-beta + memo"], effort["alpha-beta"])

    def test_plain_minimax_agrees_on_forced_win(self) -> None:
        self.assertEqual(PlainMinimaxStrategy().choose_move(self.game), Position(0, 2))

    def test_depth_limited_minimax_on_large_board(self) -> None:
        game = Game([X, O], rows=5, cols=5, k=4)
        play_all(game, [(2, 0), (0, 0), (2, 1), (0, 4), (2, 2)])
        # O must block one end of X's open three.
        move = MinimaxStrategy(max_depth=2).choose_move(game)
        self.assertIn(move, (Position(2, 3),))

    def test_minimax_on_finished_game(self) -> None:
        game = Game([X, O])
        play_all(game, WinDetectionTests.LINES["row"])
        with self.assertRaises(GameOverError):
            MinimaxStrategy().choose_move(game)


class IoAdapterTests(unittest.TestCase):
    def test_runner_reports_invalid_moves_and_result(self) -> None:
        out: list[str] = []
        game = Game([X, O])
        human_x = ConsoleHumanStrategy(
            input_fn=lambda _prompt, it=iter(["oops", "0 0", "0 1", "0 2"]): next(it),
            output=out.append,
        )
        # Omar tries the taken centre first, then plays elsewhere.
        omar = ScriptedStrategy([(1, 0), (0, 0), (1, 1)])
        state = GameRunner(game, {X: human_x, O: omar}, ConsoleView(out.append)).run()
        self.assertEqual(state, GameState.WON)
        text = "\n".join(out)
        self.assertIn("Please type two numbers", text)
        self.assertIn("Invalid move", text)
        self.assertIn("Xena wins!", text)

    def test_runner_requires_all_controllers(self) -> None:
        with self.assertRaises(ValueError):
            GameRunner(Game([X, O]), {X: RandomStrategy()}, ConsoleView(lambda _: None))

    def test_monolithic_version_also_works_but_needs_fake_stdin(self) -> None:
        script = iter(["0 0", "1 0", "0 1", "1 1", "0 2"])
        result = MonolithicTicTacToe(lambda _: next(script), lambda _: None).play()
        self.assertEqual(result, "X")


class ScoreTrackerTests(unittest.TestCase):
    def test_win_updates_records_and_ratings(self) -> None:
        tracker = ScoreTracker()
        tracker.record_result(X, O, X)
        x, o = tracker.record_for("Xena"), tracker.record_for("Omar")
        self.assertEqual((x.wins, o.losses), (1, 1))
        self.assertAlmostEqual(x.rating, 1216.0)
        self.assertAlmostEqual(o.rating, 1184.0)

    def test_draw_between_equals_changes_nothing(self) -> None:
        tracker = ScoreTracker()
        tracker.record_result(X, O, None)
        self.assertAlmostEqual(tracker.record_for("Xena").rating, 1200.0)
        self.assertEqual(tracker.record_for("Omar").draws, 1)

    def test_leaderboard_and_rank(self) -> None:
        tracker = ScoreTracker()
        z = Player("Zed", "Z")
        tracker.record_result(X, O, X)
        tracker.record_result(X, z, X)
        tracker.record_result(O, z, O)
        names = [name for name, _ in tracker.leaderboard()]
        self.assertEqual(names, ["Xena", "Omar", "Zed"])
        self.assertEqual(tracker.rank("Zed"), 3)
        self.assertEqual(len(tracker.leaderboard(top=1)), 1)
        with self.assertRaises(KeyError):
            tracker.rank("Nobody")

    def test_report_requires_finished_game(self) -> None:
        with self.assertRaises(ValueError):
            ScoreTracker().report(Game([X, O]))

    def test_concurrent_reports_are_not_lost(self) -> None:
        tracker = ScoreTracker()

        def worker() -> None:
            for _ in range(200):
                tracker.record_result(X, O, None)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(tracker.record_for("Xena").draws, 1600)


class GameRoomTests(unittest.TestCase):
    def test_stale_and_unknown_players_rejected(self) -> None:
        room = GameRoom(Game([X, O]))
        room.submit_move("Xena", 0, 0, 0)
        with self.assertRaises(StaleMoveError):
            room.submit_move("Omar", 1, 1, 0)
        with self.assertRaises(NotYourTurnError):
            room.submit_move("Mallory", 1, 1, 1)
        with self.assertRaises(NotYourTurnError):
            room.submit_move("Xena", 1, 1, 1)
        self.assertEqual(room.snapshot()["to_move"], "Omar")

    def test_result_reported_exactly_once_and_take_back_closes(self) -> None:
        tracker = ScoreTracker()
        room = GameRoom(Game([X, O]), tracker)
        for i, (r, c) in enumerate(WinDetectionTests.LINES["row"]):
            name = "Xena" if i % 2 == 0 else "Omar"
            room.submit_move(name, r, c, i)
        self.assertEqual(tracker.record_for("Xena").wins, 1)
        with self.assertRaises(GameOverError):
            room.take_back("Xena")
        self.assertEqual(room.snapshot()["winner"], "Xena")

    def test_take_back_only_own_last_move(self) -> None:
        room = GameRoom(Game([X, O]))
        room.submit_move("Xena", 0, 0, 0)
        with self.assertRaises(NotYourTurnError):
            room.take_back("Omar")
        room.take_back("Xena")
        self.assertEqual(room.snapshot()["move_number"], 0)

    def test_concurrent_submissions_only_one_wins_the_race(self) -> None:
        room = GameRoom(Game([X, O]))
        results: list[str] = []
        barrier = threading.Barrier(9)

        def client(cell: int) -> None:
            barrier.wait()  # release all nine clients at once
            try:
                room.submit_move("Xena", cell // 3, cell % 3, expected_move_number=0)
                results.append("ok")
            except StaleMoveError:
                results.append("stale")

        threads = [threading.Thread(target=client, args=(i,)) for i in range(9)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("stale"), 8)
        self.assertEqual(room.snapshot()["move_number"], 1)


class AlternativeDesignTests(unittest.TestCase):
    def test_flags_game_basic_win(self) -> None:
        game = FlagsGame([X, O])
        for r, c in WinDetectionTests.LINES["row"]:
            game.play(r, c)
        self.assertTrue(game.is_over)
        self.assertEqual(game.winner, X)

    def test_state_pattern_game(self) -> None:
        game = StatePatternGame([X, O])
        for r, c in WinDetectionTests.LINES["diagonal"]:
            game.play(r, c)
        self.assertEqual(game.state.name, "WON")
        with self.assertRaises(GameOverError):
            game.play(2, 0)

    def test_snapshot_history(self) -> None:
        board = Board()
        history = SnapshotHistory()
        history.save(board)
        board.place(Position(0, 0), X)
        restored = history.restore()
        self.assertIsNone(restored.get(Position(0, 0)))
        with self.assertRaises(IndexError):
            history.restore()

    def test_command_history(self) -> None:
        board = Board()
        history = CommandHistory()
        history.run(PlaceMarkCommand(board, Position(2, 2), O))
        history.undo()
        self.assertIsNone(board.get(Position(2, 2)))
        history.redo()
        self.assertEqual(board.get(Position(2, 2)), O)

    def test_connect_four_gravity_and_win(self) -> None:
        game = ConnectFourGame([X, O])
        game.drop(3)
        game.drop(3)
        self.assertEqual(game.board.get(Position(5, 3)), X)
        self.assertEqual(game.board.get(Position(4, 3)), O)
        for col in (4, 4, 5, 5, 6):
            game.drop(col)
        self.assertEqual(game.winner, X)

    def test_connect_four_full_column_and_direct_play(self) -> None:
        game = ConnectFourGame([X, O])
        for _ in range(6):
            game.drop(0)
        with self.assertRaises(InvalidMoveError):
            game.drop(0)
        with self.assertRaises(InvalidMoveError):
            game.play(5, 1)
        self.assertNotIn(0, {p.col for p in game.legal_moves()})


if __name__ == "__main__":
    unittest.main()
