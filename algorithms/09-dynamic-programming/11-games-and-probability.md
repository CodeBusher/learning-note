# Games and Probability — Opponents and Dice

## 1. Win and lose states: a subtraction game

A pile has `n` stones. Players alternate; on your turn you must remove 1, 2 or 3 stones. The player who cannot move (empty pile) loses. Who wins with perfect play? With `n = 4` the first player loses: whatever you take, the opponent takes the rest.

All games in §1–§4 are **finite, deterministic, with perfect information**: no dice, both players see everything, players alternate. A **position** is everything needed to continue, including whose turn it is.

**Brute force.** Search the game tree: about `3**n` leaves. The same pile sizes recur (from 10, taking 1 then 2 and 2 then 1 both reach 7), so DP applies.

**State.** `win[n]` = `True` if the player **about to move** with `n` stones wins. Defining it from the mover's view lets one table serve both players.

**Transition.** You win if **some** move leaves the opponent, now the mover, in a losing position:

$$
\text{win}[n] = \bigvee_{t \in \{1,2,3\},\ t \le n} \neg\,\text{win}[n - t], \qquad \text{win}[0] = \text{False}.
$$

With no moves, "some" is over an empty set and is false: you lose. Fill `n = 0, 1, 2, …`.

| `n` | Moves lead to | Any losing child? | `win[n]` |
|---|---|---|---|
| 0 | — | no moves | L |
| 1, 2, 3 | include 0 (L) | yes | W |
| 4 | 3, 2, 1 (all W) | no | L |
| 5, 6, 7 | include 4 (L) | yes | W |
| 8 | 7, 6, 5 (all W) | no | L |

The losing positions are the multiples of 4; from any other `n`, take `n % 4`. For other move sets the pattern is less obvious, and the DP is the reliable tool.

**Why it is correct.** If some move reaches a position losing for the opponent, that move forces a win. If every move reaches a position winning for the opponent, the opponent can force a win whatever we do. The recurrence is the definition.

### 1.1 Variant: any game graph without cycles

Positions are nodes; an edge `u → v` means the mover at `u` may move to `v`. A node with no outgoing edges is a loss for its mover. If the graph is a **DAG**, the same rule works, evaluated children first ([Tree and DAG DP](08-tree-and-dag-dp.md)):

$$
\text{win}(u) = \bigvee_{u \to v} \neg\,\text{win}(v).
$$

Memoized recursion visits children first and can detect a cycle, because on a cycle a position would ask about itself.

```python
import random
from functools import cache


def winning_positions(n_max: int, moves: tuple[int, ...]) -> list[bool]:
    """win[n] for 0 <= n <= n_max, where a move removes t stones for t in moves."""
    if n_max < 0 or not moves or min(moves) <= 0:
        raise ValueError("need n_max >= 0 and positive moves")
    win = [False] * (n_max + 1)
    for n in range(1, n_max + 1):
        win[n] = any(t <= n and not win[n - t] for t in moves)
    return win


def brute_win(n: int, moves: tuple[int, ...]) -> bool:
    """Plain game-tree search with no memo: exponential."""
    return any(t <= n and not brute_win(n - t, moves) for t in moves)


def solve_dag_game(graph: dict[str, list[str]]) -> dict[str, bool]:
    """Return win[u] for every node. Raise ValueError if the game graph has a cycle."""
    nodes = set(graph) | {v for vs in graph.values() for v in vs}
    state = {}  # "active" while on the recursion stack, then True/False

    def win(u: str) -> bool:
        if state.get(u) == "active":
            raise ValueError("game graph has a cycle")
        if u in state:
            return state[u]
        state[u] = "active"
        result = False
        for v in graph.get(u, []):
            if not win(v):
                result = True  # keep looping so every child is checked for cycles
        state[u] = result
        return result

    for u in sorted(nodes):
        win(u)
    return {u: state[u] for u in nodes}


def main():
    win = winning_positions(40, (1, 2, 3))
    assert [n for n in range(41) if not win[n]] == list(range(0, 41, 4))
    rng = random.Random(1)
    for _ in range(50):
        moves = tuple(sorted(rng.sample(range(1, 7), rng.randrange(1, 4))))
        win = winning_positions(16, moves)
        for n in range(17):
            assert win[n] == brute_win(n, moves)
    try:
        winning_positions(5, (0, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    # a -> b -> d, a -> c -> d, c -> e. d and e are terminal (player to move loses).
    graph = {"a": ["b", "c"], "b": ["d"], "c": ["d", "e"]}
    result = solve_dag_game(graph)
    assert result == {"a": False, "b": True, "c": True, "d": False, "e": False}
    # The subtraction game above, as a graph.
    stones = {str(n): [str(n - t) for t in (1, 2, 3) if t <= n] for n in range(13)}
    result = solve_dag_game(stones)
    assert all(result[str(n)] == (n % 4 != 0) for n in range(13))
    try:
        solve_dag_game({"x": ["y"], "y": ["x"]})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on a cycle")


if __name__ == "__main__":
    main()
```

O(n·|moves|) for the pile game, O(V + E) for a game graph.

**Cycles (overview).** When positions can repeat (chess, a token moving around a graph), some positions are **draws**, and recursion has no base to stand on. **Retrograde analysis** works backward instead: label terminal positions as losses and queue them; a predecessor of a loss is a win; at a predecessor of a win, decrease a counter of unresolved moves, and when it hits 0 every move hands the opponent a win, so it is a loss. Positions never labeled are draws. This is a BFS on the reversed graph, closer to [Graphs](../10-graphs/README.md) than to plain recursion.

## 2. Score difference: taking from either end

A row of piles `a[0..n-1]`. On your turn you take the left or the right end pile and add its value to your score. With perfect play, by how much does the first player win?

For `a = [3, 9, 1, 2]`, greedy takes 3, the opponent takes 9 and wins 10 to 5. Perfect play takes the 2: the opponent faces `[3, 9, 1]`, and whichever end they take, we get the 9. The first player wins 11 to 4, a difference of 7. Brute force tries `2**n` move sequences.

**Why a difference?** "Best score for player 1 on `[l, r)`" would also need whose turn it is and what the opponent scored. Measure from the mover's view instead:

**State.** `dp[l][r]` = (my total − opponent's total) on `a[l:r]` when I am to move.

**Transition.** After my move, the opponent is the mover on a shorter interval and, by definition, beats me there by `dp` of it. So my difference is my pile minus theirs:

$$
dp[l][r] = \max\big(a[l] - dp[l+1][r],\ \ a[r-1] - dp[l][r-1]\big), \qquad dp[l][l] = 0.
$$

This sign flip is **minimax** (I maximize, the opponent minimizes) written as a single max, a style called **negamax**. Fill by increasing length ([Interval DP](07-interval-dp.md)). The first player's score is `(total + dp[0][n]) / 2`.

| Interval | Piles | Take left | Take right | `dp` |
|---|---|---|---|---|
| length 1 | one pile | — | — | 3, 9, 1, 2 |
| `[0,2)` | 3, 9 | 3 − 9 = −6 | 9 − 3 = 6 | 6 |
| `[1,3)` | 9, 1 | 9 − 1 = 8 | 1 − 9 = −8 | 8 |
| `[2,4)` | 1, 2 | 1 − 2 = −1 | 2 − 1 = 1 | 1 |
| `[0,3)` | 3, 9, 1 | 3 − 8 = −5 | 1 − 6 = −5 | −5 |
| `[1,4)` | 9, 1, 2 | 9 − 1 = 8 | 2 − 8 = −6 | 8 |
| `[0,4)` | 3, 9, 1, 2 | 3 − 8 = −5 | 2 − (−5) = 7 | **7** |

```python
import random


def best_difference(a: list[int]) -> int:
    """First player's score minus second player's score under perfect play."""
    n = len(a)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(1, n + 1):
        for l in range(n - length + 1):
            r = l + length
            dp[l][r] = max(a[l] - dp[l + 1][r], a[r - 1] - dp[l][r - 1])
    return dp[0][n]


def first_player_score(a: list[int]) -> int:
    return (sum(a) + best_difference(a)) // 2


def brute(a: list[int], l: int, r: int, first_to_move: bool) -> tuple[int, int]:
    """Return (first player's score, second player's score) by explicit minimax."""
    if l == r:
        return (0, 0)
    options = []
    for value, nl, nr in ((a[l], l + 1, r), (a[r - 1], l, r - 1)):
        f, s = brute(a, nl, nr, not first_to_move)
        options.append((f + value, s) if first_to_move else (f, s + value))
    if first_to_move:
        return max(options, key=lambda p: p[0] - p[1])
    return min(options, key=lambda p: p[0] - p[1])


def main():
    assert best_difference([3, 9, 1, 2]) == 7
    assert first_player_score([3, 9, 1, 2]) == 11
    assert best_difference([]) == 0
    rng = random.Random(2)
    for _ in range(300):
        a = [rng.randrange(0, 20) for _ in range(rng.randrange(0, 11))]
        f, s = brute(a, 0, len(a), True)
        assert best_difference(a) == f - s
        assert first_player_score(a) == f


if __name__ == "__main__":
    main()
```

O(n²) time and space; a rolling array gives O(n) space.

**Why it is correct.** After any first move, the rest is a game on a shorter interval with roles swapped, whose value by induction is the opponent's best difference. The mover picks the better of the only two moves.

**Variants and traps.** *Predict the Winner* asks whether `dp[0][n] >= 0` (ties often count as a first-player win). With an **even** number of piles the first player can always take all even-indexed or all odd-indexed piles, so they never lose; the DP gives the exact margin. Writing `a[l] + dp[l+1][r]` is the classic bug: the child value belongs to the opponent.

## 3. Sums of games: Sprague–Grundy numbers

Several piles; on your turn you choose **one** pile and remove 1, 3 or 4 stones from it. The player who cannot move loses. Who wins from `(5, 6, 9)`?

The position is the whole tuple, about `n**k` positions for `k` piles: fine as a check, not in general. A game of independent parts where each turn moves in exactly one part is a **sum of games**. Win/lose labels of the parts do not decide the sum (two winning piles can make a losing sum), so each part needs a finer number.

The **mex** (minimum excluded value) of a set of nonnegative integers is the smallest nonnegative integer not in it: `mex({0, 1, 3}) = 2`, `mex({}) = 0`. The **Grundy number** of a position is the mex of its children's Grundy numbers:

$$
g(n) = \operatorname{mex}\{\, g(n - t) : t \in \text{moves},\ t \le n \,\}.
$$

A terminal position has `g = 0`, and a position is losing exactly when `g = 0`, so this refines §1.

**Sprague–Grundy theorem.** A sum of games is losing for the mover exactly when the XOR of the parts' Grundy numbers is 0.

**Why XOR (sketch).** Treat each part as a Nim pile of size `g`. By the mex, a part with value `g` can move to **any** smaller value and never to `g` itself. If the XOR is 0, any move changes one part's value, so the XOR becomes nonzero. If the XOR `X` is nonzero, some part's `g` has `X`'s highest set bit; then `g ⊕ X < g`, so move that part to `g ⊕ X` and the XOR becomes 0. The player who always hands over XOR 0 never gets stuck first. (A move that increases a part's value can be undone by the opponent, so it does not break the argument.)

**Trace** for moves {1, 3, 4}:

| `n` | Children's `g` | `g(n)` |
|---|---|---|
| 0 | {} | 0 |
| 1 | {g(0)=0} | 1 |
| 2 | {g(1)=1} | 0 |
| 3 | {g(2)=0, g(0)=0} | 1 |
| 4 | {1, 1, 0} | 2 |
| 5 | {2, 0, 1} | 3 |
| 6 | {3, 1, 0} | 2 |
| 7 | {2, 1} | 0 |

For `(5, 6, 9)`: `3 ⊕ 2 ⊕ 0 = 1 ≠ 0`, so the first player wins. The values repeat with period 7.

```python
import random
from functools import cache


def mex(values: set[int]) -> int:
    m = 0
    while m in values:
        m += 1
    return m


def grundy_table(n_max: int, moves: tuple[int, ...]) -> list[int]:
    if n_max < 0 or not moves or min(moves) <= 0:
        raise ValueError("need n_max >= 0 and positive moves")
    g = [0] * (n_max + 1)
    for n in range(1, n_max + 1):
        g[n] = mex({g[n - t] for t in moves if t <= n})
    return g


def first_player_wins(piles: tuple[int, ...], moves: tuple[int, ...]) -> bool:
    g = grundy_table(max(piles, default=0), moves)
    x = 0
    for p in piles:
        x ^= g[p]
    return x != 0


def brute_wins(piles: tuple[int, ...], moves: tuple[int, ...]) -> bool:
    """Search the full product game. Sorting the tuple merges equal positions."""

    @cache
    def win(state: tuple[int, ...]) -> bool:
        for i, p in enumerate(state):
            for t in moves:
                if t <= p:
                    child = tuple(sorted(state[:i] + (p - t,) + state[i + 1:]))
                    if not win(child):
                        return True
        return False

    return win(tuple(sorted(piles)))


def main():
    g = grundy_table(14, (1, 3, 4))
    assert g == [0, 1, 0, 1, 2, 3, 2] * 2 + [0]
    assert first_player_wins((5, 6, 9), (1, 3, 4))
    assert grundy_table(20, (1, 2, 3)) == [n % 4 for n in range(21)]  # the pile game of §1
    assert grundy_table(10, tuple(range(1, 11))) == list(range(11))  # Nim: g(n) = n
    assert mex({0, 1, 3}) == 2 and mex(set()) == 0
    rng = random.Random(4)
    for _ in range(60):
        moves = tuple(sorted(rng.sample(range(1, 6), rng.randrange(1, 4))))
        for _ in range(10):
            piles = tuple(rng.randrange(0, 10) for _ in range(rng.randrange(1, 4)))
            assert first_player_wins(piles, moves) == brute_wins(piles, moves)


if __name__ == "__main__":
    main()
```

Grundy table O(n·|moves|); a sum of `k` piles is then O(k), versus `n**k` positions.

**Traps.** The theorem needs **normal play** (the player who cannot move loses) and truly independent parts. Under **misère** play (taking the last stone loses) the XOR rule fails in general. Combine Grundy numbers with XOR, never `+`.

## 4. Expected rolls to reach a target

Now the next step is chosen by chance, and a state's value is a **probability** or an **expected value**: the sum of each possible value times its probability. Tests use `fractions.Fraction` for exact arithmetic; float versions are compared with a tolerance.

Start at total 0, roll a fair die and add, until the total reaches `T` or more. Expected number of rolls? `T = 1`: always 1. `T = 2`: a first roll of 1 (probability 1/6) needs one more, so `1 + 1/6 = 7/6`. Listing roll sequences grows exponentially.

**State.** `E[t]` = expected **additional** rolls from total `t`. Roll once (cost 1), then each face `d` moves to `t + d`:

$$
E[t] = 1 + \frac{1}{6}\sum_{d=1}^{6} E[t + d] \quad (t < T), \qquad E[t] = 0 \quad (t \ge T).
$$

`E[t]` depends on larger totals, so fill **from the end**. Expectation DPs usually run backward, because the future is what we average over.

**Trace** for `T = 4`:

| `t` | `E[t+1..t+6]` | `E[t]` |
|---|---|---|
| 3 | all 0 | 1 |
| 2 | 1, 0, … | 7/6 |
| 1 | 7/6, 1, 0, … | 1 + 13/36 = 49/36 |
| 0 | 49/36, 7/6, 1, 0, … | 1 + 127/216 = 343/216 |

For `T <= 6` the answer is `(7/6)**(T-1)`.

**Why the `1 + …`: linearity of expectation.** For any random numbers, even dependent ones, `E[X + Y] = E[X] + E[Y]`. Total rolls = this roll + the rest, so the expectation splits the same way. Linearity also solves problems with no DP at all:

- **Fixed points of a shuffle.** Card `i` stays in place with probability `1/n`; summing `n` indicators gives an expected 1 fixed point for every `n`.
- **Distinct faces in `r` rolls.** Face `f` never appears with probability `(5/6)**r`, so the expected count is `6(1 − (5/6)**r)`, even though the indicators are dependent.

**Independent check: tail sums.** For a count `N`, `E[N] = Σ_{k≥0} P(N > k)`, and `N > k` means the total after `k` rolls is still below `T`. A forward DP over the distribution of the total computes this without `E`.

```python
import random
from fractions import Fraction

from itertools import permutations, product


def expected_rolls(target: int, faces: int = 6) -> Fraction:
    if target < 0 or faces <= 0:
        raise ValueError("need target >= 0 and faces > 0")
    expected = [Fraction(0)] * (target + faces + 1)
    for t in range(target - 1, -1, -1):
        expected[t] = 1 + sum(expected[t + d] for d in range(1, faces + 1)) / faces
    return expected[0]


def expected_rolls_tail_sum(target: int, faces: int = 6) -> Fraction:
    """E[N] = sum over k of P(total after k rolls < target)."""
    dist = {0: Fraction(1)} if target > 0 else {}  # totals still below target
    answer = Fraction(0)
    while dist:
        answer += sum(dist.values())
        nxt = {}
        for t, p in dist.items():
            for d in range(1, faces + 1):
                if t + d < target:
                    nxt[t + d] = nxt.get(t + d, 0) + p / faces
        dist = nxt
    return answer


def expected_fixed_points_brute(n: int) -> Fraction:
    perms = list(permutations(range(n)))
    total = sum(sum(p[i] == i for i in range(n)) for p in perms)
    return Fraction(total, len(perms))


def expected_distinct_faces(rolls: int, faces: int = 6) -> Fraction:
    if rolls < 0 or faces <= 0:
        raise ValueError("need rolls >= 0 and faces > 0")
    return faces * (1 - Fraction(faces - 1, faces) ** rolls)


def expected_distinct_faces_brute(rolls: int, faces: int = 6) -> Fraction:
    outcomes = list(product(range(faces), repeat=rolls))
    return Fraction(sum(len(set(o)) for o in outcomes), len(outcomes))


def simulate(target: int, trials: int, rng: random.Random) -> float:
    total_rolls = 0
    for _ in range(trials):
        t = 0
        while t < target:
            t += rng.randint(1, 6)
            total_rolls += 1
    return total_rolls / trials


def main():
    assert expected_rolls(0) == 0
    assert expected_rolls(1) == 1
    assert expected_rolls(2) == Fraction(7, 6)
    assert expected_rolls(4) == Fraction(343, 216)
    for target in range(1, 7):
        assert expected_rolls(target) == Fraction(7, 6) ** (target - 1)
    for target in range(0, 25):
        for faces in (2, 3, 6):
            assert expected_rolls(target, faces) == expected_rolls_tail_sum(target, faces)
    for n in range(1, 8):
        assert expected_fixed_points_brute(n) == 1
    for rolls in range(0, 6):
        assert expected_distinct_faces(rolls) == expected_distinct_faces_brute(rolls)
    for faces in range(1, 5):
        for rolls in range(0, 6):
            assert expected_distinct_faces(rolls, faces) == expected_distinct_faces_brute(rolls, faces)
    assert expected_distinct_faces(2) == Fraction(11, 6)
    # Long run: each roll adds 3.5 on average, so about T / 3.5 rolls (plus a small overshoot term).
    rng = random.Random(6)
    estimate = simulate(30, 20000, rng)
    assert abs(estimate - float(expected_rolls(30))) < 0.05


if __name__ == "__main__":
    main()
```

O(T·faces) time; with a running sum of the last `faces` values, O(T) (the window trick of §6).

## 5. Knight staying on the board

A knight on cell `(r, c)` of an `n × n` board makes `k` moves, each one of its 8 L-shaped moves chosen uniformly, even if it leaves the board; once off, it stays off. Probability that it is still on after `k` moves? Brute force enumerates `8**k` sequences.

**State.** `p[s][i][j]` = probability that a knight on `(i, j)` with `s` moves left stays on for all of them.

$$
p[s][i][j] = \frac{1}{8}\sum_{(di, dj)} \big[(i+di, j+dj) \text{ on board}\big]\cdot p[s-1][i+di][j+dj], \qquad p[0][i][j] = 1.
$$

An off-board move contributes 0. Layer `s` uses only layer `s − 1`, so keep two grids.

**Trace** (`n = 3`, `k = 2`, start `(0, 0)`). Layer 1: the center has no on-board moves (0); every other cell has exactly 2 (2/8 = 1/4). Layer 2 at `(0, 0)`: its neighbors `(1, 2)` and `(2, 1)` hold 1/4 each, so `(1/4 + 1/4)/8 = 1/16`.

```python
import random
from fractions import Fraction
from itertools import product


MOVES = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]


def knight_probability(n: int, k: int, row: int, col: int, one=Fraction(1)):
    """Probability of staying on the board for k random moves. Pass one=1.0 for floats."""
    if n <= 0 or k < 0:
        raise ValueError("need n > 0 and k >= 0")
    if not (0 <= row < n and 0 <= col < n):
        return one * 0
    current = [[one] * n for _ in range(n)]  # s = 0 moves left
    for _ in range(k):
        nxt = [[one * 0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                total = one * 0
                for di, dj in MOVES:
                    a, b = i + di, j + dj
                    if 0 <= a < n and 0 <= b < n:
                        total += current[a][b]
                nxt[i][j] = total / 8
        current = nxt
    return current[row][col]


def brute(n: int, k: int, row: int, col: int) -> Fraction:
    stays = 0
    for seq in product(MOVES, repeat=k):
        i, j = row, col
        ok = 0 <= i < n and 0 <= j < n
        for di, dj in seq:
            i, j = i + di, j + dj
            ok = ok and 0 <= i < n and 0 <= j < n
        stays += ok
    return Fraction(stays, 8**k)


def main():
    assert knight_probability(3, 2, 0, 0) == Fraction(1, 16)
    assert knight_probability(1, 0, 0, 0) == 1
    assert knight_probability(1, 1, 0, 0) == 0
    rng = random.Random(7)
    for _ in range(40):
        n = rng.randrange(1, 7)
        k = rng.randrange(0, 4)
        r, c = rng.randrange(n), rng.randrange(n)
        assert knight_probability(n, k, r, c) == brute(n, k, r, c)
    exact = knight_probability(8, 10, 3, 4)
    approx = knight_probability(8, 10, 3, 4, one=1.0)
    assert abs(float(exact) - approx) < 1e-12


if __name__ == "__main__":
    main()
```

O(k·n²·8) time, O(n²) space.

**Trap.** Do not renormalize over legal moves. The knight chooses among all 8; off-board choices are failures and stay in the denominator.

## 6. Sliding-window probability: the "new 21" game

Start with 0 points. While below `K`, draw a card worth a uniform integer from 1 to `W` and add it. You stop at `K` or more. Probability that the final score is at most `N`? For `K = 1`, `W = 10`, `N = 6`: one draw, probability 6/10.

**State.** `P[x]` = probability that the running total is **ever exactly** `x`. You reach `x` from a total `j` with `j < K` (still drawing) and `x − W <= j <= x − 1` (the card was `x − j`):

$$
P[x] = \frac{1}{W}\sum_{j=\max(0,\,x-W)}^{\min(x-1,\,K-1)} P[j], \qquad P[0] = 1.
$$

You stop at exactly one total `x >= K`, so the stopping events are disjoint: the answer is `Σ_{x=K}^{N} P[x]`. Totals never exceed `K − 1 + W`, so if `N >= K − 1 + W` (or `K = 0`) the answer is 1.

**The window trick.** Summing up to `W` terms for each `x` costs O(N·W). But the sum covers consecutive `j`, and moving to `x + 1` slides the window by one: add `P[x]` if `x < K`, remove `P[x − W]` if `0 <= x − W < K`. A running sum makes it O(N), the fixed-size window of [Sliding Window](../05-sliding-window/README.md) applied to a recurrence.

**Trace** (`K = 2`, `W = 3`, `N = 3`):

| `x` | window holds `P[j]` for | `window` | `P[x] = window / 3` |
|---|---|---|---|
| 1 | `j = 0` | 1 | 1/3 |
| 2 | `j = 0, 1` | 4/3 | 4/9 |
| 3 | `j = 0, 1` (2 is not `< K`) | 4/3 | 4/9 |

Answer `P[2] + P[3] = 8/9`. Check: you lose only by reaching 1 and then drawing 3, probability `1/3 · 1/3 = 1/9`.

```python
import random
from fractions import Fraction


def new21_fast(n: int, k: int, w: int, one=Fraction(1)):
    """O(n) DP with a running window sum."""
    if n < 0 or k < 0 or w <= 0:
        raise ValueError("need n >= 0, k >= 0, w > 0")
    if k == 0 or n >= k - 1 + w:
        return one
    p = [one * 0] * (n + 1)
    p[0] = one
    window = one  # sum of P[j] over the current window; starts as P[0]
    answer = one * 0
    for x in range(1, n + 1):
        p[x] = window / w
        if x < k:
            window += p[x]
        else:
            answer += p[x]
        if x - w >= 0 and x - w < k:
            window -= p[x - w]
    return answer


def new21_slow(n: int, k: int, w: int, one=Fraction(1)):
    """O(n * w) direct DP."""
    if n < 0 or k < 0 or w <= 0:
        raise ValueError("need n >= 0, k >= 0, w > 0")
    if k == 0 or n >= k - 1 + w:
        return one
    p = [one * 0] * (n + 1)
    p[0] = one
    for x in range(1, n + 1):
        p[x] = sum(p[j] for j in range(max(0, x - w), min(x - 1, k - 1) + 1)) / w
    return sum(p[k:n + 1], one * 0)


def main():
    assert new21_fast(6, 1, 10) == Fraction(6, 10)
    assert new21_fast(3, 2, 3) == Fraction(8, 9)
    rng = random.Random(8)
    for _ in range(300):
        n, k, w = rng.randrange(0, 30), rng.randrange(0, 20), rng.randrange(1, 12)
        slow = new21_slow(n, k, w)
        assert new21_fast(n, k, w) == slow
    assert abs(new21_fast(21, 17, 10, one=1.0) - 0.73278) < 1e-5
    big = new21_fast(10**5, 9 * 10**4, 10**4, one=1.0)  # O(n) handles large inputs
    assert 0.0 <= big <= 1.0


if __name__ == "__main__":
    main()
```

Slow: O(N·W). Fast: O(N) time and space. With floats, a long chain of `+=` and `-=` can drift slightly negative; compare with the exact `Fraction` version on small inputs, as above.

## 7. Expected values with self-loops

Roll a die until you see a 6. Expected number of rolls?

**The trap.** From the start state, roll once; with probability 1/6 you are done, with 5/6 you are back where you started: `E = 1 + (5/6)·E`. Coded as recursion, `E()` calls `E()` with the same argument forever. Memoization does not help: a value is stored only after it is computed. The dependency graph has a **self-loop**, so no evaluation order exists.

**The fix: solve the equation.** `E = 1 + (5/6)E` gives `E = 6`. In general, if state `s` stays in itself with probability `q < 1`,

$$
E[s] = 1 + q\,E[s] + \sum_{t \ne s} P(s \to t)\,E[t] \;\Longrightarrow\; E[s] = \frac{1 + \sum_{t \ne s} P(s \to t)\,E[t]}{1 - q}.
$$

If the other dependencies form a DAG, a normal DP with this division works.

**Example: see all six faces (coupon collector).** State `k` = distinct faces seen. A new face appears with probability `(6−k)/6`, otherwise the state stays:

$$
E[k] = \frac{1 + \frac{6-k}{6}E[k+1]}{1 - \frac{k}{6}} = \frac{6}{6-k} + E[k+1], \qquad E[6] = 0,
$$

so `E[0] = 6(1 + 1/2 + … + 1/6) = 14.7`.

**Longer cycles.** Roll until two 6s **in a row**. State `A`: last roll not a 6 (or none yet); `B`: last roll a 6.

$$
E_A = 1 + \tfrac{5}{6}E_A + \tfrac{1}{6}E_B, \qquad E_B = 1 + \tfrac{5}{6}E_A.
$$

`A` and `B` depend on each other, so dividing out one self-loop is not enough. Substituting gives `(1/36)E_A = 7/6`, `E_A = 42`. For larger systems, solve the linear equations, for example by Gaussian elimination over `Fraction`s, as the code does.

```python
import random
from fractions import Fraction


def naive_expected_until_six():
    return 1 + Fraction(5, 6) * naive_expected_until_six()  # never terminates


def expected_until_six() -> Fraction:
    # E = 1 + (5/6) E  =>  E = 1 / (1 - 5/6)
    return 1 / (1 - Fraction(5, 6))


def expected_all_faces(faces: int = 6) -> Fraction:
    if faces <= 0:
        raise ValueError("faces must be positive")
    e = Fraction(0)  # E[faces] = 0
    for k in range(faces - 1, -1, -1):
        stay = Fraction(k, faces)
        e = (1 + (1 - stay) * e) / (1 - stay)
    return e


def solve_linear(a: list[list[Fraction]], b: list[Fraction]) -> list[Fraction]:
    """Gaussian elimination over Fractions for a square, nonsingular system."""
    n = len(a)
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if m[r][col] != 0), None)
        if pivot is None:
            raise ValueError("singular system")
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r != col and m[r][col] != 0:
                factor = m[r][col] / m[col][col]
                m[r] = [x - factor * y for x, y in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def expected_two_sixes() -> Fraction:
    # Unknowns [E_A, E_B]. Rewrite E = 1 + sum p E' as E - sum p E' = 1.
    s = Fraction(1, 6)
    a = [[1 - 5 * s, -s], [-5 * s, Fraction(1)]]
    return solve_linear(a, [Fraction(1), Fraction(1)])[0]


def simulate(stop, trials: int, rng: random.Random) -> float:
    total = 0
    for _ in range(trials):
        history = []
        while not stop(history):
            history.append(rng.randint(1, 6))
        total += len(history)
    return total / trials


def main():
    try:
        naive_expected_until_six()
    except RecursionError:
        pass
    else:
        raise AssertionError("the naive recursion should never finish")
    assert expected_until_six() == 6
    assert expected_all_faces() == Fraction(147, 10)
    assert expected_all_faces(1) == 1
    assert expected_all_faces(2) == 3
    assert expected_two_sixes() == 42
    rng = random.Random(9)
    assert abs(simulate(lambda h: h[-1:] == [6], 20000, rng) - 6) < 0.15
    assert abs(simulate(lambda h: len(set(h)) == 6, 20000, rng) - 14.7) < 0.2
    assert abs(simulate(lambda h: h[-2:] == [6, 6], 20000, rng) - 42) < 1.5


if __name__ == "__main__":
    main()
```

One self-loop per state costs one extra division; a general cyclic system of `s` states costs O(s³).

## 8. Summary: how children are combined

The DP skeleton never changed: state, transition from the next move, base cases, an order. What changed is how children combine:

| Setting | State value | Combine children | Order |
|---|---|---|---|
| Win/lose game | mover wins? | "some child is losing" | smaller games first |
| Zero-sum score game | mover's score minus opponent's | `max(gain − child)` (negamax) | smaller games first |
| Sum of independent games | Grundy number | `mex` per part, XOR across parts | smaller games first |
| Game with cycles | win / lose / draw | retrograde BFS from terminals | backward from the end |
| Expected remaining cost | `E[state]` | `1 + Σ p · E[child]` | from the end |
| Probability of a path event | `P[state]` | `Σ p · P[neighbor]` | layer by layer |
| Self-loop or cycle | `E[state]` | divide by `1 − q`, or solve the system | algebra, not order |

## 9. Pitfalls and practice

1. **Forgetting whose turn it is.** Define values from the mover's view so one table serves both players.
2. **Adding the child's score difference.** It belongs to the opponent: `a[l] - dp[l+1][r]`.
3. **Wrong terminal rule.** Under normal play, no moves is a loss. Misère games change this, and the XOR rule no longer applies directly.
4. **Cycles in a game graph.** Use retrograde analysis and allow draws.
5. **Adding Grundy numbers.** Combine with XOR.
6. **Filling expectation DPs forward.** Expected "remaining" quantities depend on the future: fill from the end.
7. **Renormalizing probabilities.** Off-board knight moves and "bust" outcomes stay in the denominator.
8. **Self-loops.** Use algebra (`E = (1 + rest) / (1 − q)`) or a linear solve, not recursion.
9. **Floating-point drift.** Test the float version against `Fraction` on small inputs.
10. **Simulation tests without a seed.** Use `random.Random(seed)` and a tolerance several standard errors wide.

Practice: Nim Game, Stone Game, Predict the Winner, Stone Game II, Can I Win, Divisor Game, Cat and Mouse (retrograde analysis), Knight Probability in Chessboard, New 21 Game, Soup Servings, Dice Roll Simulation, Toss Strange Coins, Number of Dice Rolls With Target Sum.

Next: [Faster Transitions](12-faster-transitions.md).
