# State-Space Search — Choosing What a Vertex Remembers

## 1. When "where am I" is not enough

**Problem.** A grid has open cells `0` and walls `1`. You may walk through at most `k` walls (each wall entered uses up one "elimination"). Find the fewest moves from the top-left to the bottom-right cell, or −1.

Take `k = 1` and this grid:

```text
      c0 c1
r0  [  0  0 ]
r1  [  1  0 ]
r2  [  0  1 ]
r3  [  1  0 ]
```

By hand: go right to `(0,1)`, down to `(1,1)`, down through the wall at `(2,1)` (using the one elimination), and down to `(3,1)`. That is **4 moves**.

**The tempting wrong answer.** Run the [grid BFS](03-bfs.md#5-bfs-on-a-grid), remembering in each queue entry how many eliminations are left, and mark each **cell** visited the first time it is reached.

| Distance | Cells reached (eliminations left) |
|---:|---|
| 0 | (0,0) left 1 |
| 1 | (1,0) left **0** (broke a wall); (0,1) left 1 |
| 2 | from (1,0): (2,0) left 0, **(1,1) left 0**. From (0,1): (1,1) is already marked, skipped |
| 3 | from (2,0) and (1,1): every way on is a wall, and nothing is left. Stuck |

It answers −1. The trouble is at distance 2: cell `(1,1)` was reached twice at the same distance, once having spent the elimination and once not. Marking the cell kept the worse arrival and threw away the one that could still break through `(2,1)`.

**The key observation.** Two arrivals can share a visited mark only if **everything about the future is the same** for both. Here the future depends on the cell *and* on how many eliminations remain. So make the vertex the pair, or rather the triple:

$$
\text{state} = (\text{row},\ \text{col},\ \text{eliminations left}).
$$

Edges go from a state to the states one move away, and moving into a wall lowers the third coordinate. This new graph is called the **state space**. Every vertex of the original grid has turned into `k + 1` vertices, one per budget, and plain BFS on the state space is correct because every move still costs one.

Trace the state BFS on the same grid. A state is written `(r,c|left)`.

| Distance | New states discovered |
|---:|---|
| 0 | (0,0\|1) |
| 1 | (1,0\|0), (0,1\|1) |
| 2 | from (1,0\|0): (2,0\|0), (1,1\|0). From (0,1\|1): **(1,1\|1)**, a different state, so it is kept |
| 3 | from (1,1\|0): (0,1\|0). From (1,1\|1): (2,1\|0), breaking the wall |
| 4 | from (0,1\|0): (0,0\|0). From (2,1\|0): **(3,1\|0)**, the target. Answer 4 |

```python
import random
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def shortest_with_eliminations(grid, k):
    """Fewest moves from (0,0) to the bottom-right in a 0/1 grid, entering at most k walls.

    Entering a wall uses one elimination, including a wall at the start cell. Returns -1
    if impossible.
    """
    if k < 0:
        raise ValueError("k must be nonnegative")
    if not grid or not grid[0]:
        return -1
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")
    left = k - grid[0][0]
    if left < 0:
        return -1
    start = (0, 0, left)
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (r, c, left), dist = queue.popleft()
        if (r, c) == (rows - 1, cols - 1):
            return dist
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                state = (nr, nc, left - grid[nr][nc])
                if state[2] >= 0 and state not in seen:
                    seen.add(state)
                    queue.append((state, dist + 1))
    return -1


def shortest_with_dominance(grid, k):
    rows, cols = len(grid), len(grid[0])
    left = k - grid[0][0]
    if left < 0:
        return -1
    best_left = [[-1] * cols for _ in range(rows)]
    best_left[0][0] = left
    queue = deque([(0, 0, left, 0)])
    while queue:
        r, c, left, dist = queue.popleft()
        if (r, c) == (rows - 1, cols - 1):
            return dist
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                new_left = left - grid[nr][nc]
                if new_left > best_left[nr][nc]:  # strictly better than every earlier arrival
                    best_left[nr][nc] = new_left
                    queue.append((nr, nc, new_left, dist + 1))
    return -1


def cell_only_bfs(grid, k):
    """The WRONG version: one visited mark per cell."""
    rows, cols = len(grid), len(grid[0])
    if k - grid[0][0] < 0:
        return -1
    seen = {(0, 0)}
    queue = deque([(0, 0, k - grid[0][0], 0)])
    while queue:
        r, c, left, dist = queue.popleft()
        if (r, c) == (rows - 1, cols - 1):
            return dist
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen:
                if left - grid[nr][nc] >= 0:
                    seen.add((nr, nc))
                    queue.append((nr, nc, left - grid[nr][nc], dist + 1))
    return -1


def brute_force(grid, k):
    """Try every simple path (no repeated cell). A shortest answer never repeats a cell,
    because cutting out the loop saves moves and never uses more eliminations."""
    rows, cols = len(grid), len(grid[0])
    best = -1
    on_path = set()

    def walk(r, c, used, length):
        nonlocal best
        used += grid[r][c]
        if used > k:
            return
        if (r, c) == (rows - 1, cols - 1):
            if best == -1 or length < best:
                best = length
            return
        on_path.add((r, c))
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in on_path:
                walk(nr, nc, used, length + 1)
        on_path.remove((r, c))

    walk(0, 0, 0, 0)
    return best


def main():
    grid = [[0, 0], [1, 0], [0, 1], [1, 0]]
    assert shortest_with_eliminations(grid, 1) == 4
    assert cell_only_bfs(grid, 1) == -1  # the trap
    assert shortest_with_dominance(grid, 1) == 4
    assert shortest_with_eliminations([[0, 1], [1, 0]], 1) == 2
    assert shortest_with_eliminations([[0, 1], [1, 0]], 0) == -1
    assert shortest_with_eliminations([[0]], 0) == 0
    assert shortest_with_eliminations([[1]], 0) == -1
    assert shortest_with_eliminations([[1]], 1) == 0

    rng = random.Random(12)
    for _ in range(300):
        rows, cols = rng.randint(1, 4), rng.randint(1, 4)
        g = [[int(rng.random() < 0.4) for _ in range(cols)] for _ in range(rows)]
        k = rng.randint(0, 2)
        assert shortest_with_eliminations(g, k) == brute_force(g, k)
    for _ in range(500):  # dominance pruning (section 3) against the full state search
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        g = [[int(rng.random() < 0.45) for _ in range(cols)] for _ in range(rows)]
        k = rng.randint(0, 3)
        assert shortest_with_dominance(g, k) == shortest_with_eliminations(g, k)


if __name__ == "__main__":
    main()
```

**Cost.** There are at most `R · C · (k + 1)` states, each with four moves, so O(RCk) time and space. When `k ≥ R + C − 2`, you can afford to break every wall on a straight route, so the answer is `R + C − 2` immediately; capping `k` there keeps the state count at O(RC(R + C)).

## 2. Count the states before you code

**Problem.** An undirected connected graph has `n ≤ 12` vertices. Find the length of the shortest walk that visits every vertex at least once. You may start and end anywhere, and may reuse vertices and edges.

For the star with center 0 and leaves 1, 2, 3, the answer is 4: `1, 0, 2, 0, 3`.

What must a state remember? The current vertex, and **which vertices have been visited so far**. The future does not care about the order of past visits, only the set. A set of up to 12 vertices fits in a 12-bit integer called a **bitmask**: bit `i` is 1 when vertex `i` has been visited ([Bit Manipulation](../../11-bit-manipulation/README.md) covers masks in depth).

$$
\text{state} = (\text{vertex},\ \text{visited mask}), \qquad \text{at most } n \cdot 2^n = 12 \cdot 4096 = 49{,}152 \text{ states}.
$$

The start can be anywhere, so begin a **multi-source BFS** ([Breadth-First Search](03-bfs.md#6-many-sources-at-once-rotting-oranges)) from every `(i, only bit i set)`. The first state removed whose mask has every bit set gives the answer.

A few layers on the star (`mask` written as a set):

| Distance | Some states |
|---:|---|
| 0 | (0, {0}), (1, {1}), (2, {2}), (3, {3}) |
| 1 | (1, {0,1}), (2, {0,2}), (3, {0,3}), (0, {0,1}), (0, {0,2}), (0, {0,3}) |
| 2 | (2, {0,1,2}), (3, {0,1,3}), … |
| 3 | (0, {0,1,2}), … |
| 4 | (3, {0,1,2,3}): all visited |

**Brute force.** Any walk visits the vertices first in some order `p1, p2, …, pn`. Between consecutive first visits it needs at least the BFS distance, and following shortest paths achieves exactly that. So the answer is the minimum over all `n!` orders of the sum of consecutive distances.

```python
import itertools
import random
from collections import deque


def shortest_path_visiting_all(adj):
    """Length of the shortest walk visiting every vertex of a connected graph."""
    n = len(adj)
    if n == 0:
        return 0
    full = (1 << n) - 1
    seen = set()
    queue = deque()
    for i in range(n):
        state = (i, 1 << i)
        seen.add(state)
        queue.append((state, 0))
    while queue:
        (u, mask), dist = queue.popleft()
        if mask == full:
            return dist
        for v in adj[u]:
            state = (v, mask | (1 << v))
            if state not in seen:
                seen.add(state)
                queue.append((state, dist + 1))
    raise ValueError("graph is not connected")


def brute_force(adj):
    n = len(adj)
    dist = []
    for s in range(n):  # all-pairs distances by BFS
        d = [-1] * n
        d[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if d[v] == -1:
                    d[v] = d[u] + 1
                    q.append(v)
        dist.append(d)
    return min(sum(dist[a][b] for a, b in zip(order, order[1:]))
               for order in itertools.permutations(range(n)))


def main():
    star = [[1, 2, 3], [0], [0], [0]]
    assert shortest_path_visiting_all(star) == 4
    assert shortest_path_visiting_all([[]]) == 0
    assert shortest_path_visiting_all([[1], [0]]) == 1

    rng = random.Random(13)
    for _ in range(150):
        n = rng.randint(1, 6)
        adj = [[] for _ in range(n)]
        for v in range(1, n):  # a random tree keeps the graph connected
            u = rng.randrange(v)
            adj[u].append(v)
            adj[v].append(u)
        for _ in range(rng.randint(0, 4)):
            u, v = rng.randrange(n), rng.randrange(n)
            if u != v and v not in adj[u]:
                adj[u].append(v)
                adj[v].append(u)
        assert shortest_path_visiting_all(adj) == brute_force(adj)


if __name__ == "__main__":
    main()
```

O(2ⁿ · (n + E)) time: each of the `n · 2ⁿ` states scans its vertex's neighbors, which totals `2ⁿ · 2E` over all vertices. O(n · 2ⁿ) space. The brute force is O(n! · n), already 479 million orders at `n = 12`. The state space is bigger than the graph you see; the table in §8 lists common extra state and its multiplier.

## 3. Dominance: skipping states that cannot help

In §1, `(1,1|0)` and `(1,1|1)` were both reached at distance 2. The second has the same place and distance and more eliminations left, so anything the first can do, the second can too: it **dominates** the first.

BFS removes states in order of distance, so every earlier arrival at a cell was no farther. If one of them also had at least as many eliminations left, the newcomer is dominated and can be skipped. So it is enough to keep, per cell, the **largest** number of eliminations left so far and accept a new arrival only if it beats it (`shortest_with_dominance` in the §1 script, tested against the full state search).

Each cell can be accepted at most `k + 1` times (its best value only goes up, through values `0..k`), so the worst case is still O(RCk), but typical runs are far faster, and memory drops to O(RC) for the table plus the queue.

The argument needs **both** facts: later arrivals are never closer (BFS order), and fewer eliminations are never better. In a search that is not ordered by distance, such as DFS, "most eliminations left" alone is not a safe reason to skip.

## 4. Backtracking: listing every answer

Some problems ask for **every** arrangement, not one route: all orderings, all subsets, all queen placements. The tool is DFS over a tree of **partial choices**: make one more choice, recurse, then **undo** it before trying the next. This is **backtracking**.

### 4.1 Permutations

**Problem.** List all orderings of `[1, 2, 3]`. There are `3! = 6`.

The choice tree, where each level fixes one more position:

```text
                         []
          ┌──────────────┼──────────────┐
         [1]            [2]            [3]
       ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
    [1,2]  [1,3]   [2,1]  [2,3]   [3,1]  [3,2]
      │      │       │      │       │      │
  [1,2,3] [1,3,2] [2,1,3] [2,3,1] [3,1,2] [3,2,1]
```

The walk down the leftmost branch and back:

| Step | Action | `path` | `used` |
|---:|---|---|---|
| 1 | choose 1 | [1] | {1} |
| 2 | choose 2 | [1, 2] | {1, 2} |
| 3 | choose 3, record [1,2,3] | [1, 2, 3] | {1, 2, 3} |
| 4–5 | undo 3, undo 2 (nothing left to try under [1, 2]) | [1] | {1} |
| 6–7 | choose 3, choose 2, record [1,3,2] | [1, 3, 2] | {1, 2, 3} |

### 4.2 Subsets

**Problem.** List all subsets of `[1, 2, 3]`. There are `2³ = 8`.

Here every node of the tree is an answer, not only the leaves. To avoid listing `{1, 2}` and `{2, 1}` separately, only choose items **after** the last one chosen.

```text
[]  →  [1]  →  [1,2]  →  [1,2,3]
                [1,3]
       [2]  →  [2,3]
       [3]
```

### 4.3 Simple paths

**Problem.** List every path from `source` to `target` that never repeats a vertex. The `on_path` set is the path-local record: a vertex may appear in many answers, but only once within each.

```python
import itertools
import random


def permutations(items):
    result, path, used = [], [], [False] * len(items)

    def go():
        if len(path) == len(items):  # check
            result.append(path.copy())
            return
        for i, x in enumerate(items):
            if not used[i]:
                used[i] = True        # choose
                path.append(x)
                go()                  # explore
                path.pop()            # undo
                used[i] = False

    go()
    return result


def subsets(items):
    result, path = [], []

    def go(start):
        result.append(path.copy())  # every node is an answer
        for i in range(start, len(items)):
            path.append(items[i])
            go(i + 1)
            path.pop()

    go(0)
    return result


def simple_paths(adj, source, target):
    result, path, on_path = [], [source], {source}

    def go(u):
        if u == target:
            result.append(path.copy())
            return
        for v in adj[u]:
            if v not in on_path:
                on_path.add(v)
                path.append(v)
                go(v)
                path.pop()
                on_path.remove(v)

    go(source)
    return result


def main():
    assert permutations([1, 2, 3]) == [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    assert permutations([]) == [[]]
    assert subsets([1, 2, 3]) == [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    assert subsets([]) == [[]]
    assert simple_paths([[1, 2], [0, 2], []], 0, 2) == [[0, 1, 2], [0, 2]]
    assert simple_paths([[]], 0, 0) == [[0]]
    assert simple_paths([[], []], 0, 1) == []

    rng = random.Random(15)
    for n in range(6):
        items = rng.sample(range(100), n)
        assert permutations(items) == [list(p) for p in itertools.permutations(items)]
        assert sorted(map(tuple, subsets(items))) == sorted(
            c for r in range(n + 1) for c in itertools.combinations(items, r))

    for _ in range(200):  # simple paths against trying every vertex sequence
        n = rng.randint(1, 5)
        adj = [sorted(rng.sample(range(n), rng.randint(0, n))) for _ in range(n)]
        s, t = rng.randrange(n), rng.randrange(n)
        brute = []
        for length in range(1, n + 1):
            for seq in itertools.permutations(range(n), length):
                if seq[0] == s and seq[-1] == t and all(b in adj[a] for a, b in zip(seq, seq[1:])):
                    brute.append(list(seq))
        assert sorted(simple_paths(adj, s, t)) == sorted(brute)


if __name__ == "__main__":
    main()
```

All three follow one template:

1. **Check**: if the partial answer is complete, record a **copy**.
2. **Choose**: pick an option that is still legal.
3. **Explore**: recurse.
4. **Undo**: restore exactly the state before the choice.

The global `visited` set of ordinary DFS is wrong here: two different partial answers may pass through the same vertex, and both must be explored. The record of what is used (`used`, `on_path`) is **path-local** and undone on the way back.

**Cost.** Permutations: `n!` answers, each copied in O(n), so O(n · n!). Subsets: O(n · 2ⁿ). Simple paths can number exponentially many even in sparse graphs. Backtracking has **no** O(V + E) bound merely because it looks like DFS: the output itself can be enormous. The recursion depth is at most `n` (or V), which is small for any input whose output is small enough to list, so recursion is fine here.

## 5. Pruning: cutting dead branches early

**Problem (N-queens).** Place `n` queens on an `n × n` board so that no two attack each other: no shared row, column, or diagonal. For `n = 4` there are 2 solutions; for `n = 8`, 92.

**Brute force.** Put one queen in each row (two queens in a row attack, so this loses nothing) and try every column for each: `nⁿ` boards, 16,777,216 for `n = 8`, and check each one at the end.

**Better.** Choose columns as a permutation, so columns never clash: `n! = 40,320` boards for `n = 8`. Still checked only at the end.

**Key observation.** If the first two queens already attack each other, no way of placing the remaining six can fix it. Check each queen **as it is placed**, and abandon the branch the moment a conflict appears. That is **pruning**.

To check in O(1), notice that all squares on one "↘" diagonal share `row − col`, and all squares on one "↙" diagonal share `row + col`. Keep three sets: used columns, used `row − col` values, used `row + col` values.

Trace for `n = 4`, placing row by row (`r` = row, `c` = column):

| Step | Partial board (column per row) | Try | Result |
|---:|---|---|---|
| 1 | [] | r0 c0 | place |
| 2 | [0] | r1 c0, c1 | c0 column, c1 diagonal (`r−c = 0`) |
| 3 | [0] | r1 c2 | place |
| 4 | [0, 2] | r2 c0..c3 | c0 column, c1 diagonal (`r+c = 3`), c2 column, c3 diagonal (`r−c = −1`): dead end, undo |
| 5 | [0] | r1 c3 | place |
| 6 | [0, 3] | r2 c1 | place (c0 column clash skipped) |
| 7 | [0, 3, 1] | r3 c0..c3 | all attacked: undo twice, then undo r0 c0 |
| 8 | [] | r0 c1 | place |
| 9 | [1] | r1 c3 | place (c0, c1, c2 attacked) |
| 10 | [1, 3] | r2 c0 | place |
| 11 | [1, 3, 0] | r3 c2 | place: **solution [1, 3, 0, 2]** |

How much does pruning save? The script below counts the nodes each method visits.

| n | Every column per row (`nⁿ`) | Permutations (`n!`) | Pruned search nodes | Solutions |
|---:|---:|---:|---:|---:|
| 4 | 256 | 24 | 17 | 2 |
| 6 | 46,656 | 720 | 153 | 4 |
| 8 | 16,777,216 | 40,320 | 2,057 | 92 |

```python
import itertools


def n_queens(n):
    """Return (solutions, search_nodes). A solution lists the column for each row."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    solutions, cols = [], []
    used_col, used_diff, used_sum = set(), set(), set()
    nodes = 0

    def place(r):
        nonlocal nodes
        nodes += 1
        if r == n:
            solutions.append(cols.copy())
            return
        for c in range(n):
            if c in used_col or r - c in used_diff or r + c in used_sum:
                continue  # prune: this queen is attacked already
            used_col.add(c); used_diff.add(r - c); used_sum.add(r + c); cols.append(c)
            place(r + 1)
            used_col.remove(c); used_diff.remove(r - c); used_sum.remove(r + c); cols.pop()

    place(0)
    return solutions, nodes


def n_queens_brute(n):
    return [list(p) for p in itertools.permutations(range(n))
            if len({r - c for r, c in enumerate(p)}) == n and len({r + c for r, c in enumerate(p)}) == n]


def main():
    solutions, nodes = n_queens(4)
    assert solutions == [[1, 3, 0, 2], [2, 0, 3, 1]] and nodes == 17
    assert n_queens(6)[1] == 153
    assert len(n_queens(8)[0]) == 92 and n_queens(8)[1] == 2057
    assert n_queens(0)[0] == [[]]
    assert n_queens(2)[0] == [] and n_queens(3)[0] == []
    for n in range(1, 8):
        assert n_queens(n)[0] == n_queens_brute(n)


if __name__ == "__main__":
    main()
```

The running time is proportional to the number of search nodes times `n`. There is no simple formula for the node count, but it is far below `n!`, as the table shows. The recursion depth is `n`.

### 5.1 Word search: backtracking on a grid

**Problem.** Given a grid of letters and a word, can the word be spelled by a path of side-adjacent cells, using each cell at most once?

```text
A B C E
S F C S
A D E E
```

`ABCCED` is present (start at the top-left `A`, then right, right, down, down, left); `ABCB` is not, because the only `B` would have to be reused.

The state is the current cell and how many letters are matched. Prune as soon as a cell's letter doesn't match the next letter of the word. The path-local "used" mark can live in the grid itself: overwrite the cell with `#` while it is on the path, and restore it on the way back.

```python
import itertools
import random

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def exist(board, word):
    if not word:
        return True
    if not board or not board[0]:
        return False
    rows, cols = len(board), len(board[0])
    grid = [list(row) for row in board]  # private copy we can mark

    def match(r, c, i):
        if grid[r][c] != word[i]:
            return False  # prune
        if i == len(word) - 1:
            return True
        saved, grid[r][c] = grid[r][c], "#"  # choose
        found = any(0 <= r + dr < rows and 0 <= c + dc < cols and match(r + dr, c + dc, i + 1)
                    for dr, dc in DIRS)
        grid[r][c] = saved  # undo
        return found

    return any(match(r, c, 0) for r in range(rows) for c in range(cols))


def exist_brute(board, word):
    cells = [(r, c) for r in range(len(board)) for c in range(len(board[0]))]
    for seq in itertools.permutations(cells, len(word)):
        if all(board[r][c] == ch for (r, c), ch in zip(seq, word)) and all(
                abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(seq, seq[1:])):
            return True
    return False


def main():
    board = ["ABCE", "SFCS", "ADEE"]
    assert exist(board, "ABCCED")
    assert exist(board, "SEE")
    assert not exist(board, "ABCB")
    assert exist(["A"], "A") and not exist(["A"], "AA")
    assert exist(board, "")

    rng = random.Random(16)
    for _ in range(300):
        rows, cols = rng.randint(1, 3), rng.randint(1, 3)
        b = ["".join(rng.choice("ab") for _ in range(cols)) for _ in range(rows)]
        w = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
        assert exist(b, w) == exist_brute(b, w)


if __name__ == "__main__":
    main()
```

O(RC · 3^L) time in the worst case for a word of length `L`: each start cell, then at most 3 new directions per later letter (the fourth leads back). Recursion depth is `L`.

## 6. Bidirectional BFS: search from both ends

With both ends known, BFS from the start explores a ball of radius `d`, the distance. Searching from both ends, each side only needs radius about `d / 2`. With about `b` neighbors per state, that is roughly `2 · b^(d/2)` states instead of `b^d`: 2,000 instead of 1,000,000 for `b = 10`, `d = 6`. On a directed graph the backward search asks "who can reach me?", so it follows the **reversed** graph.

**The stopping rule is the subtle part.** Stopping at the first vertex both sides have touched can be wrong. Safe rule: expand **one whole layer** at a time, alternating sides; whenever an examined vertex is known to the other side, record the sum of the two distances; after a layer with any meeting, return the smallest sum. Why: before the layer, forward has depth `a`, backward depth `b`, and no meeting, so every path is longer than `a + b`. The layer finds every path of length `a + b + 1`, and the minimum over the whole layer can't miss the best one.

Trace on the word ladder from [Breadth-First Search](03-bfs.md#7-an-implicit-graph-of-words-word-ladder), `hit → cog`, with numbered words `hit 0, hot 1, dot 2, lot 3, dog 4, log 5, cog 6`:

| Round | Side | Layer expanded | New (distance on that side) | Meetings |
|---:|---|---|---|---|
| 1 | forward | {hit} | hot (1) | none |
| 2 | backward | {cog} | dog (1), log (1) | none |
| 3 | forward | {hot} | dot (2), lot (2) | none |
| 4 | backward | {dog, log} | dot (2) and lot (2) are forward's | dot: 2 + 2 = 4; lot: 2 + 2 = 4 |

The shortest route has 4 edges: `hit, hot, dot, dog, cog`, five words.

```python
import random
from collections import deque


def bidirectional_distance(adj, source, target):
    """Fewest directed edges from source to target, or -1. Expands whole layers alternately."""
    n = len(adj)
    if not (0 <= source < n and 0 <= target < n):
        raise ValueError("endpoint out of range")
    if source == target:
        return 0
    reverse = [[] for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            reverse[v].append(u)
    dist_f, dist_b = {source: 0}, {target: 0}
    frontier_f, frontier_b = [source], [target]

    def expand(frontier, own, other, graph):
        nxt, best = [], None
        for u in frontier:
            for v in graph[u]:
                if v not in own:
                    own[v] = own[u] + 1
                    nxt.append(v)
                if v in other:
                    meet = own[u] + 1 + other[v]
                    best = meet if best is None else min(best, meet)
        return nxt, best

    forward_turn = True
    while frontier_f and frontier_b:
        if forward_turn:
            frontier_f, best = expand(frontier_f, dist_f, dist_b, adj)
        else:
            frontier_b, best = expand(frontier_b, dist_b, dist_f, reverse)
        if best is not None:
            return best
        forward_turn = not forward_turn
    return -1


def bfs_distance(adj, s, t):
    dist = [-1] * len(adj)
    dist[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist[t]


def main():
    ladder = [[1], [0, 2, 3], [1, 3, 4], [1, 2, 5], [2, 5, 6], [3, 4, 6], [4, 5]]
    assert bidirectional_distance(ladder, 0, 6) == 4
    assert bidirectional_distance([[1], [2], []], 0, 2) == 2
    assert bidirectional_distance([[1], [2], []], 2, 0) == -1  # arrows point the other way
    assert bidirectional_distance([[]], 0, 0) == 0

    rng = random.Random(17)
    for _ in range(1000):
        n = rng.randint(1, 10)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 20)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        s, t = rng.randrange(n), rng.randrange(n)
        assert bidirectional_distance(adj, s, t) == bfs_distance(adj, s, t)


if __name__ == "__main__":
    main()
```

The worst case on an explicit graph is still O(V + E) time and space, including building the reversed graph; the `b^(d/2)` saving is an intuition for wide, tree-like search spaces, not a guarantee. A common refinement expands the **smaller** frontier each round instead of strictly alternating; the layer-at-a-time stopping rule keeps it correct. For implicit graphs such as word ladders, the backward neighbors are generated by the same rule, so no reversed graph is stored.

## 7. Looking ahead: guided search

BFS treats every direction alike. **A\*** orders states by `f = g + h`: `g` is the cost so far and `h` an **estimate** of the cost left. If `h` never overestimates (**admissible**), A\* is optimal with nonnegative costs; if also `h(u) ≤ cost(u, v) + h(v)` for every move (**consistent**), each state is final when it first leaves the priority queue. On a four-direction unit-cost grid, Manhattan distance to the goal is admissible and consistent. With `h = 0`, A\* is Dijkstra. Both are developed in [Shortest Paths](../04-shortest-paths/04-modeling-and-variants.md); broader heuristic search is in the [AI search notes](../../../Foundation%20of%20AI/01-search.md).

## 8. Summary

**What a state must hold:** everything that can change the future. Two arrivals may share a visited mark only if their futures are identical. Multiply out the state count before coding:

| Problem | State | Factor over the plain graph |
|---|---|---|
| Walls you may break | (cell, eliminations left) | `k + 1` |
| Keys you have collected | (cell, key mask) | `2^keys` |
| Visit every vertex | (vertex, visited mask) | `2^n` |
| Fuel tank | (city, fuel left) | `capacity + 1` |
| Direction you face | (cell, direction) | 4 |
| Number of stops used | (city, stops so far) | `max_stops + 1` |

| Question | Tool | Visited record |
|---|---|---|
| Fewest moves with extra rules | BFS over `(place, extra)` states | Global, per state; dominance can shrink it |
| Every arrangement / path | Backtracking: check, choose, explore, undo | Path-local, undone on return |
| Every arrangement, many dead ends | Backtracking plus pruning | Path-local, with O(1) conflict tests |
| Fewest moves, both ends known, huge space | Bidirectional BFS | One distance map per side; stop after a whole layer |
| Nonnegative costs plus a good estimate | A\* | Like Dijkstra |

## 9. Pitfalls and practice

1. Marking cells instead of states. If two arrivals at a cell can have different futures, the visited set must include whatever differs (§1).
2. Forgetting to count states. A key mask over 10 keys multiplies a 50 × 50 grid by 1,024; check that the product fits in time and memory before coding.
3. Pruning by dominance in a search that is not ordered by distance (§3).
4. Using a global `visited` in backtracking. Enumeration needs a path-local record that is undone.
5. Forgetting to undo exactly what was done, such as removing from `used_col` but not from `used_sum`.
6. Recording `path` instead of `path.copy()`. Every recorded answer then points at the same list, which ends up empty.
7. Stopping bidirectional BFS at the first touch without finishing the layer, or searching backward along forward arrows in a directed graph.
8. Treating A\* as optimal with a heuristic that can overestimate.

Practice: shortest path in a grid with obstacles elimination; shortest path visiting all nodes; shortest path to get all keys; open the lock; sliding puzzle; cheapest flights within k stops (state with stops used); permutations; permutations II (with duplicates); subsets; combination sum; N-queens; word search; palindrome partitioning; word ladder (bidirectional).

Back to the [Search and Traversal overview](README.md).
