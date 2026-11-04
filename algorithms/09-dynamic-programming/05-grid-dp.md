# Grid DP — Paths Through a Rectangle

## 1. Counting paths

A grid has `R` rows and `C` columns; cell `(r, c)` is zero-based, the start `(0, 0)` is the top-left and the end `(R-1, C-1)` the bottom-right. Walk from the top-left to the bottom-right, one step right or one step down at a time. How many different paths are there? For a 2 × 3 grid there are 3: `RRD`, `RDR`, `DRR`. For a 3 × 3 grid there are 6. For a 3 × 7 grid there are 28.

**Brute force.** Try every path recursively, branching right and down from each cell. Every path has exactly `R - 1 + C - 1` moves, and the tree branches up to twice per move. On a 16 × 16 grid there are over 155 million paths, so listing them one at a time is hopeless. But many paths share the same middle cell, and the number of ways to finish from a cell does not depend on how you reached it. That is the repeated work DP removes.

**State.** `ways[r][c]` = the number of paths from `(0, 0)` to `(r, c)`.

**Transition.** Look at the last move into `(r, c)`. It came either from above, `(r-1, c)`, or from the left, `(r, c-1)`. These are different paths, and every path into `(r, c)` (other than the start) has one of them as its last move. So we add:

$$
ways[r][c] = ways[r-1][c] + ways[r][c-1]
$$

A neighbor outside the grid contributes 0.

**Base case.** `ways[0][0] = 1`. The empty sequence of moves is one path from the start to itself.

**Evaluation order.** Row by row, left to right. The cell above was filled in the previous row; the cell to the left was filled one step earlier.

**Trace** on a 3 × 4 grid:

| | c=0 | c=1 | c=2 | c=3 |
|---|---|---|---|---|
| r=0 | 1 | 1 | 1 | 1 |
| r=1 | 1 | 2 | 3 | 4 |
| r=2 | 1 | 3 | 6 | 10 |

The top row is all 1s: you can only arrive from the left. The left column is all 1s: you can only arrive from above. The cell `(2, 3)` is `6 + 4 = 10`.

**A combinatorics cross-check.** Every path from `(0, 0)` to `(R-1, C-1)` makes exactly `R - 1` down moves and `C - 1` right moves, in some order. A path is decided by choosing which of the `R + C - 2` moves are the down moves. So the count is

$$
\binom{R + C - 2}{R - 1}.
$$

For 3 × 4 that is `C(5, 2) = 10`, matching the table. The DP table is Pascal's triangle, tilted 45 degrees: each entry is the sum of its two "parents". This formula only works on an empty grid; with obstacles we need the DP.

```python
import random
from math import comb


def unique_paths(rows: int, cols: int) -> int:
    if rows <= 0 or cols <= 0:
        raise ValueError("the grid needs at least one row and one column")
    ways = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                ways[r][c] = 1
            else:
                up = ways[r - 1][c] if r > 0 else 0
                left = ways[r][c - 1] if c > 0 else 0
                ways[r][c] = up + left
    return ways[rows - 1][cols - 1]


def brute_paths(rows: int, cols: int, r: int = 0, c: int = 0) -> int:
    if r == rows - 1 and c == cols - 1:
        return 1
    total = 0
    if r + 1 < rows:
        total += brute_paths(rows, cols, r + 1, c)
    if c + 1 < cols:
        total += brute_paths(rows, cols, r, c + 1)
    return total


def main():
    assert unique_paths(2, 3) == 3
    assert unique_paths(3, 3) == 6
    assert unique_paths(3, 4) == 10
    assert unique_paths(3, 7) == 28
    assert unique_paths(1, 1) == 1
    assert unique_paths(16, 16) == comb(30, 15) == 155117520

    rng = random.Random(1)
    for _ in range(100):
        rows, cols = rng.randint(1, 8), rng.randint(1, 8)
        expected = brute_paths(rows, cols)
        assert unique_paths(rows, cols) == expected
        assert comb(rows + cols - 2, rows - 1) == expected


if __name__ == "__main__":
    main()
```

Time and space are O(RC). The next section shrinks space to O(C).

## 2. Obstacles and the rolling row

Some cells are blocked (`True`), and paths may not enter them. Example:

```
. . .
. # .
. . .
```

The 6 paths of an empty 3 × 3 grid drop to **2**: around the top-right, or around the bottom-left. Every other path passes through the center.

A blocked cell has `ways = 0`, no matter what its neighbors say. That one rule is enough: a zero in a blocked cell stops every path through it. The start cell needs care too. If the start itself is blocked, there are 0 paths, not 1.

**Trace** for the grid above:

| | c=0 | c=1 | c=2 |
|---|---|---|---|
| r=0 | 1 | 1 | 1 |
| r=1 | 1 | **0** (blocked) | 1 |
| r=2 | 1 | 1 | 2 |

**One row is enough.** Cell `(r, c)` reads only the row above and the current row. Keep one array `ways` of length `C`. When we are about to update `ways[c]` in row `r`:

- `ways[c]` still holds row `r-1` (the cell above), because we have not touched it yet in this row.
- `ways[c-1]` already holds row `r` (the cell to the left), because we updated it a moment ago.

So `ways[c] += ways[c-1]` adds exactly "above + left". Compare with [Knapsack and Coins §3](04-knapsack-and-coins.md#3-shrinking-the-table-to-one-row): there, reading an already-updated cell was a bug. Here it is what we want, because "left" belongs to the current row. Always ask which row each read should come from.

```python
import random


def count_grid_paths(blocked: list[list[bool]]) -> int:
    rows = len(blocked)
    cols = len(blocked[0]) if rows else 0
    if any(len(row) != cols for row in blocked):
        raise ValueError("grid must be rectangular")
    if rows == 0 or cols == 0:
        return 0
    ways = [0] * cols
    ways[0] = 1  # Becomes 0 below if the start is blocked.
    for r in range(rows):
        for c in range(cols):
            if blocked[r][c]:
                ways[c] = 0
            elif c > 0:
                ways[c] += ways[c - 1]  # Above (old value) + left (new value).
    return ways[-1]


def brute(blocked, r=0, c=0):
    rows, cols = len(blocked), len(blocked[0])
    if blocked[r][c]:
        return 0
    if (r, c) == (rows - 1, cols - 1):
        return 1
    total = 0
    if r + 1 < rows:
        total += brute(blocked, r + 1, c)
    if c + 1 < cols:
        total += brute(blocked, r, c + 1)
    return total


def main():
    assert count_grid_paths([[False] * 3 for _ in range(3)]) == 6
    assert count_grid_paths([
        [False, False, False],
        [False, True, False],
        [False, False, False],
    ]) == 2
    assert count_grid_paths([[False]]) == 1
    assert count_grid_paths([[True]]) == 0  # Blocked start.
    assert count_grid_paths([[False, True, False]]) == 0
    assert count_grid_paths([[False, False], [False, True]]) == 0  # Blocked end.
    assert count_grid_paths([]) == 0
    assert count_grid_paths([[]]) == 0

    rng = random.Random(2)
    for _ in range(300):
        rows, cols = rng.randint(1, 7), rng.randint(1, 7)
        grid = [[rng.random() < 0.25 for _ in range(cols)] for _ in range(rows)]
        assert count_grid_paths(grid) == brute(grid)


if __name__ == "__main__":
    main()
```

Time O(RC), space O(C). If `C` is much larger than `R`, roll over columns instead and use O(R) space.

## 3. Minimum path sum

Each cell has a nonnegative cost. Walk right or down from the top-left to the bottom-right, paying for every cell you visit, including both corners. Find the cheapest path. Example:

```
1 3 1
1 5 1
4 2 1
```

The best path is `1 → 3 → 1 → 1 → 1`, total **7** (right, right, down, down).

Brute force tries every path, which is the same exponential count as §1.

**State.** `cost[r][c]` = the cheapest total of a path from `(0, 0)` to `(r, c)`, including both ends.

**Transition.** The last move came from above or from the left. Whichever we came from, the part of the path before `(r, c)` should be as cheap as possible, because the rest of the path (from `(r, c)` onward) does not care how we got here. So:

$$
cost[r][c] = grid[r][c] + \min\big(cost[r-1][c],\; cost[r][c-1]\big)
$$

A neighbor outside the grid counts as `inf`, so it never wins the `min`.

**Base case.** `cost[0][0] = grid[0][0]`. The start cell is charged explicitly. Forgetting this is a common off-by-one.

**Trace:**

| | c=0 | c=1 | c=2 |
|---|---|---|---|
| r=0 | 1 | 1+3 = 4 | 4+1 = 5 |
| r=1 | 1+1 = 2 | 5 + min(4, 2) = 7 | 1 + min(5, 7) = 6 |
| r=2 | 2+4 = 6 | 2 + min(7, 6) = 8 | 1 + min(6, 8) = **7** |

**Rebuilding the path.** Walk back from the end. At `(r, c)`, the predecessor is the neighbor (above or left) whose cost equals `cost[r][c] - grid[r][c]`. In the trace: at `(2, 2)`, `7 - 1 = 6`, and the cell above, `(1, 2)`, has 6. At `(1, 2)`, `6 - 1 = 5`, which is `(0, 2)`. Then left, left. Reversed, the moves are `R R D D`.

```python
import random
from itertools import combinations
from math import inf


def min_path_sum(grid: list[list[int]]) -> tuple[int, str]:
    """Return the cheapest cost and its moves ('R' and 'D')."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    rows, cols = len(grid), len(grid[0])
    cost = [[inf] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                cost[r][c] = grid[0][0]
                continue
            up = cost[r - 1][c] if r > 0 else inf
            left = cost[r][c - 1] if c > 0 else inf
            cost[r][c] = grid[r][c] + min(up, left)

    moves = []
    r, c = rows - 1, cols - 1
    while (r, c) != (0, 0):
        before = cost[r][c] - grid[r][c]
        if r > 0 and cost[r - 1][c] == before:
            moves.append("D")
            r -= 1
        else:
            moves.append("R")
            c -= 1
    return cost[rows - 1][cols - 1], "".join(reversed(moves))


def all_move_strings(rows: int, cols: int):
    n = rows + cols - 2
    for downs in combinations(range(n), rows - 1):
        yield "".join("D" if i in downs else "R" for i in range(n))


def path_cost(grid, moves):
    r = c = 0
    total = grid[0][0]
    for m in moves:
        r, c = (r + 1, c) if m == "D" else (r, c + 1)
        total += grid[r][c]
    return total


def main():
    grid = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    assert min_path_sum(grid) == (7, "RRDD")
    assert min_path_sum([[5]]) == (5, "")
    assert min_path_sum([[1, 2, 3]]) == (6, "RR")

    rng = random.Random(3)
    for _ in range(300):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        g = [[rng.randint(-3, 9) for _ in range(cols)] for _ in range(rows)]
        best, moves = min_path_sum(g)
        assert best == min(path_cost(g, m) for m in all_move_strings(rows, cols))
        assert path_cost(g, moves) == best


if __name__ == "__main__":
    main()
```

Time and space O(RC). Without reconstruction, a rolling row gives O(C) space.

**Why it is correct.** Every path to `(r, c)` arrives from exactly one of the two neighbors. Among paths arriving from above, the cheapest one uses a cheapest path to the cell above; otherwise we could swap in a cheaper prefix. The same holds from the left. Negative costs are fine (the random test uses them), because right/down moves can never return to a cell, so there are no cycles to exploit.

## 4. Triangle: compute backward to remove the edge cases

A triangle of numbers has row `i` with `i + 1` entries. From entry `j` in row `i`, you may step to entry `j` or `j + 1` in the next row. Find the smallest sum from the top to any entry of the bottom row.

```
      2
     3 4
    6 5 7
   4 1 8 3
```

The answer is **11**: `2 + 3 + 5 + 1`.

A forward DP (`best[i][j]` = cheapest path from the top to `(i, j)`) works, but it needs care at both edges of every row (the leftmost entry has only one parent, and so does the rightmost), and the answer is a `min` over the whole last row.

Flip the direction. **State.** `down[i][j]` = the cheapest sum of a path that starts at `(i, j)` and goes to the bottom.

**Transition.** From `(i, j)` you pay the entry and then continue from one of the two children:

$$
down[i][j] = tri[i][j] + \min\big(down[i+1][j],\; down[i+1][j+1]\big)
$$

**Base case.** The bottom row: `down[n-1][j] = tri[n-1][j]`.

**Order.** From the bottom row upward. Every entry has exactly two children, so there are no edge cases, and the answer is the single value `down[0][0]`.

**Trace** (one row, overwritten as we go up):

| after row | `down` |
|---|---|
| 3 (base) | `[4, 1, 8, 3]` |
| 2 | `[6+min(4,1), 5+min(1,8), 7+min(8,3)]` = `[7, 6, 10]` |
| 1 | `[3+min(7,6), 4+min(6,10)]` = `[9, 10]` |
| 0 | `[2+min(9,10)]` = `[11]` |

When computing `down[j]` for the new row, we read `down[j]` and `down[j+1]` from the old row. Going left to right, `down[j+1]` has not been overwritten yet, so one array works.

```python
import random


def triangle_min_path(tri: list[list[int]]) -> int:
    if not tri or any(len(row) != i + 1 for i, row in enumerate(tri)):
        raise ValueError("row i must have i + 1 entries")
    down = list(tri[-1])
    for i in range(len(tri) - 2, -1, -1):
        for j in range(i + 1):
            down[j] = tri[i][j] + min(down[j], down[j + 1])
    return down[0]


def brute(tri, i=0, j=0):
    if i == len(tri) - 1:
        return tri[i][j]
    return tri[i][j] + min(brute(tri, i + 1, j), brute(tri, i + 1, j + 1))


def main():
    assert triangle_min_path([[2], [3, 4], [6, 5, 7], [4, 1, 8, 3]]) == 11
    assert triangle_min_path([[-10]]) == -10
    assert triangle_min_path([[1], [2, 3]]) == 3

    rng = random.Random(4)
    for _ in range(200):
        n = rng.randint(1, 10)
        tri = [[rng.randint(-9, 9) for _ in range(i + 1)] for i in range(n)]
        assert triangle_min_path(tri) == brute(tri)


if __name__ == "__main__":
    main()
```

Time O(n²) for `n` rows (one step per entry), extra space O(n).

The lesson generalizes: **if many cells are possible endings but there is one start, compute "cost from here to the end" backward**, and the answer lands in a single cell. §6 shows a problem where going backward is not only cleaner but necessary.

## 5. Maximal square of 1s

Given a grid of 0s and 1s, find the area of the largest square made only of 1s.

```
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```

The answer is **4**: the 2 × 2 square in rows 1–2, columns 2–3 (also columns 3–4).

**Brute force.** For every top-left corner and every size, check every cell in the square. That is O(RC · min(R,C)³) in the worst case.

A square is not a path, so "which cell did I come from" does not apply. Instead we pick a cell that every square has exactly one of: its bottom-right corner.

**State.** `side[r][c]` = the side length of the largest all-1 square whose bottom-right corner is `(r, c)`. If `grid[r][c] == 0`, it is 0.

**Transition.** If `grid[r][c] == 1`:

$$
side[r][c] = 1 + \min\big(side[r-1][c],\; side[r][c-1],\; side[r-1][c-1]\big)
$$

Outside the grid counts as 0.

**Why the minimum of three.** Let `k = 1 + min(...)`.

- *A square of side `k` fits.* All three neighbors anchor squares of side at least `k - 1`. Picture the `k × k` square ending at `(r, c)`. The `(k-1)`-square ending at `(r-1, c)` covers its top `k - 1` rows, except the leftmost column. The `(k-1)`-square ending at `(r, c-1)` covers its leftmost `k - 1` columns, except the top row. The `(k-1)`-square ending at `(r-1, c-1)` covers the top-left corner region, including the top-left cell. Together with `grid[r][c] = 1`, every cell of the `k × k` square is 1.
- *No bigger square fits.* If a square of side `k + 1` ended at `(r, c)`, then removing its bottom row would give a square of side `k` ending at `(r-1, c)`, and similarly for the other two neighbors. Then all three would be at least `k`, so the minimum would be at least `k`, a contradiction.

**Trace** for the example (the answer is the largest entry, squared):

| | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---|---|---|---|---|
| r=0 | 1 | 0 | 1 | 0 | 0 |
| r=1 | 1 | 0 | 1 | 1 | 1 |
| r=2 | 1 | 1 | 1 | **2** | **2** |
| r=3 | 1 | 0 | 0 | 1 | 0 |

At `(2, 3)`: neighbors `side[1][3] = 1`, `side[2][2] = 1`, `side[1][2] = 1`, so `1 + 1 = 2`. Largest side 2, area 4.

```python
import random


def maximal_square(grid: list[list[int]]) -> int:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")
    side = [[0] * (cols + 1) for _ in range(rows + 1)]  # Padded with zeros.
    best = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                side[r + 1][c + 1] = 1 + min(side[r][c + 1], side[r + 1][c], side[r][c])
                best = max(best, side[r + 1][c + 1])
    return best * best


def brute(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    best = 0
    for top in range(rows):
        for left in range(cols):
            k = 1
            while top + k <= rows and left + k <= cols:
                if all(grid[top + i][left + j] == 1 for i in range(k) for j in range(k)):
                    best = max(best, k)
                k += 1
    return best * best


def main():
    grid = [
        [1, 0, 1, 0, 0],
        [1, 0, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 0, 0, 1, 0],
    ]
    assert maximal_square(grid) == 4
    assert maximal_square([[0]]) == 0
    assert maximal_square([[1]]) == 1
    assert maximal_square([]) == 0
    assert maximal_square([[1] * 3 for _ in range(3)]) == 9

    rng = random.Random(5)
    for _ in range(300):
        rows, cols = rng.randint(1, 7), rng.randint(1, 7)
        g = [[int(rng.random() < 0.75) for _ in range(cols)] for _ in range(rows)]
        assert maximal_square(g) == brute(g)


if __name__ == "__main__":
    main()
```

Time and space O(RC); a rolling row plus one saved diagonal value brings space to O(C). The padding trick (an extra zero row and column) removes all the boundary checks.

The "anchor at the bottom-right corner" idea is the grid version of "ending at `i`" from Kadane's algorithm in [Designing a Recurrence](02-designing-a-recurrence.md#4-maximum-subarray-ending-exactly-at-i). It works whenever every object has exactly one natural anchor cell.

## 6. Backward DP: minimum starting health

A hero starts at the top-left with some health `h` and must reach the bottom-right, moving right or down. Entering each cell (including the first and the last) adds that cell's number to the health; negative numbers are damage, positive numbers are potions. The health must stay at least 1 at every moment. What is the smallest starting `h`?

Example:

```
 3  -5   4
 1  -4  -4
```

The three paths and the health after each cell, starting from `h`:

| Moves | Cells | Running sums | Lowest running sum | Needed `h` |
|---|---|---|---|---|
| R R D | 3, -5, 4, -4 | 3, -2, 2, -2 | -2 | 3 |
| R D R | 3, -5, -4, -4 | 3, -2, -6, -10 | -10 | 11 |
| D R R | 3, 1, -4, -4 | 3, 4, 0, -4 | -4 | 5 |

For one path, the health after a cell is `h + (running sum)`, so we need `h + lowest >= 1`, that is `h >= 1 - lowest`, and also `h >= 1`. The answer is the best path: **3**.

**Why forward DP fails.** The natural first attempt: `f[r][c]` = the smallest starting health needed to reach `(r, c)` alive. Then take the better of the two predecessors. Try it at the last cell `(1, 2)`:

- Arriving from above, via `R R`: needs start 3, and the health on arrival is `3 + 2 = 5`.
- Arriving from the left, via `D R`: needs only start 1, but the health on arrival is `1 + 0 = 1`.

The left route looks better (needs 1 instead of 3), so forward DP picks it. Then the final `-4` hits a hero with health 1, and fixing that needs start 5. The route from above had more health in reserve and finishes with start 3.

The problem: a partial path is described by **two** numbers, "what start did it need" and "how much health does it carry". Neither route is better in both. So the state "needed start" alone fails the history test: it forgets the health in reserve, and that reserve changes which futures the hero survives. Keeping the route with "more health" instead fails too: on `[[0, -1, 5], [1, -1, 3]]` that rule ends with the route `R R D`, which needs 2, while `D R R` needs only 1.

**Turn around.** Ask the question from the other end. **State.** `need[r][c]` = the smallest health the hero must have *just before entering* `(r, c)` to finish alive.

This passes the history test. What happens from `(r, c)` onward depends only on the health the hero brings in, not on how it got here. And it is one number: a threshold.

**Transition.** After entering `(r, c)` the health is `h + grid[r][c]`. It must be at least 1, and it must be enough for the better next cell, `m = min(need[r+1][c], need[r][c+1])`. So `h + grid[r][c] >= max(1, m)`. Since `m >= 1` always, this becomes:

$$
need[r][c] = \max\big(1,\; \min(need[r+1][c],\; need[r][c+1]) - grid[r][c]\big)
$$

The outer `max(1, ...)` says the hero must be alive before entering, even if the cell is a big potion.

**Base case.** At the last cell there is no next cell; the hero only needs to survive it: `need[R-1][C-1] = max(1, 1 - grid[R-1][C-1])`. A neat way to code this is to pretend the cell below the end needs 1 and treat all other outside cells as `inf`.

**Order.** From the bottom-right, going up and left. Each cell reads the cells below and to the right, which are done.

**Trace:**

| cell | below | right | `min - grid` | `need` |
|---|---|---|---|---|
| (1,2) | (end: 1) | inf | 1 - (-4) = 5 | 5 |
| (1,1) | inf | 5 | 5 - (-4) = 9 | 9 |
| (1,0) | inf | 9 | 9 - 1 = 8 | 8 |
| (0,2) | 5 | inf | 5 - 4 = 1 | 1 |
| (0,1) | 9 | 1 | 1 - (-5) = 6 | 6 |
| (0,0) | 8 | 6 | 6 - 3 = 3 | **3** |

```python
import random
from itertools import combinations
from math import inf


def min_start_health(grid: list[list[int]]) -> int:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    rows, cols = len(grid), len(grid[0])
    need = [[inf] * (cols + 1) for _ in range(rows + 1)]
    need[rows][cols - 1] = 1  # A pretend exit below the end cell.
    for r in range(rows - 1, -1, -1):
        for c in range(cols - 1, -1, -1):
            after = min(need[r + 1][c], need[r][c + 1])
            need[r][c] = max(1, after - grid[r][c])
    return need[0][0]


def brute(grid):
    rows, cols = len(grid), len(grid[0])
    n = rows + cols - 2
    best = inf
    for downs in combinations(range(n), rows - 1):
        r = c = 0
        running = lowest = grid[0][0]
        for i in range(n):
            r, c = (r + 1, c) if i in downs else (r, c + 1)
            running += grid[r][c]
            lowest = min(lowest, running)
        best = min(best, max(1, 1 - lowest))
    return best


def main():
    grid = [[3, -5, 4], [1, -4, -4]]
    assert min_start_health(grid) == 3
    assert min_start_health([[0, -1, 5], [1, -1, 3]]) == 1
    assert min_start_health([[0]]) == 1
    assert min_start_health([[-5]]) == 6
    assert min_start_health([[100]]) == 1

    rng = random.Random(6)
    for _ in range(300):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        g = [[rng.randint(-8, 6) for _ in range(cols)] for _ in range(rows)]
        assert min_start_health(g) == brute(g)


if __name__ == "__main__":
    main()
```

Time and space O(RC). A rolling row going upward gives O(C) space.

**When to think backward.** Run DP in the direction where the state summarizes everything that matters. Here the *future* is captured by one number (the threshold) while the *past* needs two. The same idea shows up in games and probability, where "value from this position onward" is the natural state; see [Games and Probability](11-games-and-probability.md).

## 7. Two walkers at once

Each cell holds some cherries (a nonnegative number), or is blocked (`-1`). Two walkers both go from the top-left to the bottom-right, moving right or down. A walker collects the cherries of each cell it visits. If both visit the same cell, its cherries count only once. Find the largest total. If no path exists, report that.

This is the core of the well-known "cherry pickup" problem, where one person walks to the corner and back. Reversing the return trip turns it into a second forward walk, so the round trip is two forward walkers.

Example:

```
0 2 0
1 1 1
1 2 0
```

Two walkers can collect all 8 cherries: A goes `R D R D` through `2, 1, 1`; B goes `D D R R` through `1, 1, 2`.

**Why two greedy passes fail.** A tempting plan: find the best single path, take its cherries, then find the best path on what is left. The best single path is `(0,0) → (0,1) → (1,1) → (2,1) → (2,2)` with `2 + 1 + 2 = 5`. What remains is `1` at `(1,0)`, `1` at `(1,2)`, and `1` at `(2,0)`. No right/down path reaches both `(1,2)` and `(2,0)`, so the second pass gets 2. Total **7**, not 8: the first path was best alone but blocked a good partner, so the two paths must be chosen together.

**The state: move both walkers in step.** A first try is `(r1, c1, r2, c2)`, the positions of both walkers. The trouble is the "count once" rule: if walker A passed through a cell earlier, we would need to remember that, and the history test fails.

The fix is to move the walkers in lockstep, one move each per step. After `t` moves, each walker is on a cell with `r + c = t`. Two walkers can only share a cell if they are there **at the same step**, since a cell's `r + c` is fixed. So "do they share this cell?" is answered by comparing the current positions, with no memory of the past.

And since `c = t - r`, the step and the two rows determine everything:

**State.** `dp[t][r1][r2]` = the most cherries collected after `t` moves each, with walker A at `(r1, t - r1)` and walker B at `(r2, t - r2)`, or `-inf` if that pair of positions is unreachable.

**Transition.** Each walker made its last move either down (its row was one less) or right (its row was the same). That gives four predecessor states:

$$
dp[t][r_1][r_2] = gain + \max_{a, b \in \{0, 1\}} dp[t-1][r_1 - a][r_2 - b]
$$

where `gain = grid[r1][c1] + grid[r2][c2]` if the walkers are on different cells, and `grid[r1][c1]` if they are on the same cell (`r1 == r2`). If either cell is blocked, the state is `-inf`.

**Base case.** `dp[0][0][0] = grid[0][0]`, if the start is not blocked.

**Answer.** `dp[R+C-2][R-1][R-1]`, both walkers at the end.

**Order.** Step `t` reads only step `t - 1`, so keep two layers.

**Trace** for the example. Each entry is `(r1, r2) → best`. Swapping the walkers gives the same total, so the table lists only `r1 <= r2`. The column `c` of each walker is `t - r`.

| t | reachable `(r1, r2)` → best |
|---|---|
| 0 | (0,0) → 0 |
| 1 | (0,0) → 2, (0,1) → 3, (1,1) → 1 |
| 2 | (0,0) → 2, (0,1) → 4, (0,2) → 4, (1,1) → 4, (1,2) → 5, (2,2) → 2 |
| 3 | (1,1) → 5, (1,2) → 8, (2,2) → 7 |
| 4 | (2,2) → **8** |

The entries where something interesting happens:

- `t = 2`, `(1, 2)`: A at `(1,1)`, B at `(2,0)`. The best predecessor is `(0, 1)` at step 1 (value 3), A moving down and B moving down. Gain `1 + 1 = 2`, total 5.
- `t = 3`, `(1, 2)`: A at `(1,2)`, B at `(2,1)`. From `(1, 2)` at step 2 (value 5), A moves right and B moves right. Gain `1 + 2 = 3`, total 8.
- `t = 3`, `(2, 2)`: both at `(2,1)`. The shared cell counts once: from `(1, 2)` (value 5) plus 2 gives 7.

```python
import random
from itertools import combinations
from math import inf


def two_walkers(grid: list[list[int]]) -> int | None:
    """Most cherries two right/down walkers collect together, or None."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    if any(x < -1 for row in grid for x in row):
        raise ValueError("cells must be -1 (blocked) or nonnegative")
    rows, cols = len(grid), len(grid[0])
    if grid[0][0] == -1:
        return None
    dp = [[-inf] * rows for _ in range(rows)]
    dp[0][0] = grid[0][0]
    for t in range(1, rows + cols - 1):
        new = [[-inf] * rows for _ in range(rows)]
        low, high = max(0, t - cols + 1), min(rows - 1, t)  # Valid rows at step t.
        for r1 in range(low, high + 1):
            c1 = t - r1
            if grid[r1][c1] == -1:
                continue
            for r2 in range(low, high + 1):
                c2 = t - r2
                if grid[r2][c2] == -1:
                    continue
                best = -inf
                for a in (0, 1):
                    for b in (0, 1):
                        p1, p2 = r1 - a, r2 - b
                        if p1 >= 0 and p2 >= 0:
                            best = max(best, dp[p1][p2])
                if best == -inf:
                    continue
                gain = grid[r1][c1] if r1 == r2 else grid[r1][c1] + grid[r2][c2]
                new[r1][r2] = best + gain
        dp = new
    answer = dp[rows - 1][rows - 1]
    return None if answer == -inf else answer


def all_paths(grid):
    rows, cols = len(grid), len(grid[0])
    n = rows + cols - 2
    for downs in combinations(range(n), rows - 1):
        r = c = 0
        cells = [(0, 0)]
        for i in range(n):
            r, c = (r + 1, c) if i in downs else (r, c + 1)
            cells.append((r, c))
        if all(grid[r][c] != -1 for r, c in cells):
            yield cells


def brute(grid):
    paths = list(all_paths(grid))
    if not paths:
        return None
    return max(
        sum(grid[r][c] for r, c in set(a) | set(b)) for a in paths for b in paths
    )


def main():
    grid = [[0, 2, 0], [1, 1, 1], [1, 2, 0]]
    assert two_walkers(grid) == 8
    assert two_walkers([[5]]) == 5  # Both walkers share the only cell.
    assert two_walkers([[-1]]) is None
    assert two_walkers([[0, -1], [-1, 0]]) is None
    assert two_walkers([[1, 1, -1], [1, -1, 1], [-1, 1, 1]]) is None

    rng = random.Random(7)
    for _ in range(300):
        rows, cols = rng.randint(1, 4), rng.randint(1, 4)
        g = [[rng.choice([-1, 0, 0, 1, 2, 3]) for _ in range(cols)] for _ in range(rows)]
        assert two_walkers(g) == brute(g)


if __name__ == "__main__":
    main()
```

There are `R + C - 1` steps and at most `R²` row pairs per step, each with four predecessors: O((R + C) · R²) time and O(R²) space. Swap the roles of rows and columns if `C < R`.

**Why it is correct.** Any pair of paths can be cut at every step `t` into a pair of shorter paths, ending at some `(r1, r2)` at step `t - 1`. The cells collected at step `t` depend only on the two current cells. Cells from earlier steps cannot be the current cells, because their `r + c` is smaller. So the best total at step `t` is the best total at some predecessor plus this step's gain, and the four predecessor pairs cover every possible pair of last moves.

**Symmetry.** Swapping the walkers gives the same total, so you may keep only `r1 <= r2` and halve the work. The code above keeps both orders for clarity.

## 8. Variants and when a grid is not a DP

| Variant | Change | Watch out for |
|---|---|---|
| Maximum path score | `max` instead of `min` | Unreachable cells need `-inf` when scores can be negative |
| Diagonal moves allowed | Add the top-left predecessor | Only if the move is legal |
| At most `k` obstacles removed | Add a dimension: `dp[r][c][j]` | Exactly `k` versus at most `k` |
| Path sum divisible by `m` | Add `sum mod m` as a dimension | Counts per remainder, not one best value |
| Falling path (any column below) | Row-to-row DP with three or `C` predecessors | Edge columns |
| Count paths with obstacles modulo `M` | Same DP, reduce after each addition | Zero modulo `M` is not impossibility |
| Four-direction moves | **Not a plain DP** | Use BFS or shortest paths |

The last row deserves a warning. Right/down moves always increase `r + c`, so the dependency graph has no cycles and a row-by-row order works. This stays true even with negative costs. Once you allow up and left moves, cell A can depend on cell B while B depends on A. There is no order in which to fill the table. Use breadth-first search for unit costs or Dijkstra's algorithm for nonnegative costs instead; see [Graphs](../10-graphs/README.md). A grid DP is a shortest-path problem on a DAG, and that view is what [Tree and DAG DP](08-tree-and-dag-dp.md) makes general.

## 9. Pitfalls and practice

1. **A blocked start.** It has 0 paths, not 1. Test the 1 × 1 blocked grid.
2. **Not resetting blocked cells in a rolling row.** Set `ways[c] = 0`; do not `continue`.
3. **Forgetting to charge the start cell** in path sums.
4. **Using 0 for unreachable in `min` or `max` problems.** Use `inf` or `-inf`.
5. **Assuming the combinatorics formula works with obstacles.** It counts only obstacle-free grids.
6. **Forward DP when the past needs two numbers.** Minimum starting health must be computed backward.
7. **Forgetting the outer `max(1, ...)`** in the health recurrence. A big potion cannot revive a dead hero.
8. **Optimizing two paths one at a time.** Two greedy passes can lose; move both walkers together.
9. **Moving walkers out of step.** Without the shared step `t`, you cannot tell whether a cell was already collected.
10. **Grid DP with four-direction moves.** The dependencies form cycles; use a graph algorithm.

Practice: Unique Paths, Unique Paths II, Minimum Path Sum, Triangle, Minimum Falling Path Sum, Maximal Square, Count Square Submatrices with All Ones, Dungeon Game, Cherry Pickup, Cherry Pickup II, Paths in Matrix Whose Sum Is Divisible by K, Out of Boundary Paths.

Next: [Sequences and Strings](06-sequences-and-strings.md).
