# Breadth-First Search — Layer by Layer, Fewest Edges First

## 1. Fewest edges from a start

What is the smallest number of edges on a path from `s` to each vertex? That number is the **distance**, and a path achieving it is a **shortest path in an unweighted graph**.

```text
    0 ─── 1 ─── 3 ─── 5         adj[0] = [1, 2]
    │           │               adj[1] = [0, 3]
    │           │               adj[2] = [0, 4]
    2 ─── 4 ─── 6               adj[3] = [1, 5, 6]
                                adj[4] = [2, 6]
                                adj[5] = [3]
                                adj[6] = [3, 4]
```

[DFS](02-dfs.md) from 0 walks `0, 1, 3, 5`, backs up, takes `3 → 6 → 4`, so its tree path to 4 has four edges, while `0, 2, 4` has two. DFS commits to the first branch it sees.

**Brute force.** Set `dist[s] = 0` and every other distance to infinity. For every edge `u – v`, if `dist[u] + 1 < dist[v]`, lower `dist[v]`. A shortest path has at most V − 1 edges and each full round fixes at least one more of them, so V − 1 rounds suffice: O(V · E). The tests below use it as the reference.

**Key observation.** Process vertices **in the order they were discovered**. Then every vertex at distance `d` is processed before any at distance `d + 1`, and the first discovery of a vertex comes from a vertex one layer closer. "First discovered, first processed" is a **queue**; `collections.deque` adds at the back and removes from the front in O(1).

1. `dist[s] = 0`; put `s` in the queue.
2. Remove the front vertex `u`. For each neighbor `v` with no distance yet: `dist[v] = dist[u] + 1`, `parent[v] = u`, add `v` at the back.
3. Repeat until the queue is empty.

| Step | Remove | Discovered (distance) | Queue after (front left) | `dist` for 0..6 |
|---:|---:|---|---|---|
| 0 | | 0 (0) | [0] | 0 · · · · · · |
| 1 | 0 | 1 (1), 2 (1) | [1, 2] | 0 1 1 · · · · |
| 2 | 1 | 3 (2) | [2, 3] | 0 1 1 2 · · · |
| 3 | 2 | 4 (2) | [3, 4] | 0 1 1 2 2 · · |
| 4 | 3 | 5 (3), 6 (3) | [4, 5, 6] | 0 1 1 2 2 3 3 |
| 5–7 | 4, 5, 6 | none | [] | unchanged |

At step 5, vertex 4 meets 6 again by `0, 2, 4, 6`, also three edges, so nothing changes and 6 is not added twice. The layers are `{0}`, `{1, 2}`, `{3, 4}`, `{5, 6}`. Following parents back from 4 gives `4, 2, 0`, so the shortest path is `0, 2, 4`.

## 2. The code

```python
import math
import random
from collections import deque


def bfs(adj, source):
    """Fewest-edge distances from source; dist is -1 for unreachable vertices."""
    n = len(adj)
    if not 0 <= source < n:
        raise ValueError("source out of range")
    dist = [-1] * n
    parent = [-1] * n
    dist[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if dist[v] == -1:  # mark on enqueue
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return dist, parent


def restore_path(parent, dist, target):
    """Vertices from the source to target, or [] if target is unreachable."""
    if dist[target] == -1:
        return []
    path = [target]
    while parent[path[-1]] != -1:
        path.append(parent[path[-1]])
    return path[::-1]


def brute_distances(n, arrows, source):
    """Repeated relaxation, O(V * E). arrows are directed (u, v) pairs."""
    dist = [math.inf] * n
    dist[source] = 0
    for _ in range(max(n - 1, 0)):
        for u, v in arrows:
            if dist[u] + 1 < dist[v]:
                dist[v] = dist[u] + 1
    return [-1 if d == math.inf else d for d in dist]


def pushes_mark_on_dequeue(adj, s):
    """The tempting variant of section 4: count how many entries it queues."""
    seen, queue, pushes = set(), deque([s]), 1
    while queue:
        u = queue.popleft()
        if u in seen:
            continue
        seen.add(u)
        for v in adj[u]:
            if v not in seen:
                queue.append(v)
                pushes += 1
    return pushes


def main():
    adj = [[1, 2], [0, 3], [0, 4], [1, 5, 6], [2, 6], [3], [3, 4]]
    dist, parent = bfs(adj, 0)
    assert dist == [0, 1, 1, 2, 2, 3, 3]
    assert restore_path(parent, dist, 4) == [0, 2, 4]
    assert restore_path(parent, dist, 6) == [0, 1, 3, 6]
    assert restore_path(parent, dist, 0) == [0]
    assert bfs([[], []], 0)[0] == [0, -1]

    rng = random.Random(7)
    for trial in range(400):
        n = rng.randint(1, 9)
        directed = trial % 2 == 0
        adj = [[] for _ in range(n)]
        arrows = []
        for _ in range(rng.randint(0, 14)):
            u, v = rng.randrange(n), rng.randrange(n)
            adj[u].append(v)
            arrows.append((u, v))
            if not directed:
                adj[v].append(u)
                arrows.append((v, u))
        s = rng.randrange(n)
        dist, parent = bfs(adj, s)
        assert dist == brute_distances(n, arrows, s)
        for t in range(n):
            path = restore_path(parent, dist, t)
            assert len(path) == dist[t] + 1  # an unreachable target gives []
            assert all(b in adj[a] for a, b in zip(path, path[1:]))

    n = 50  # complete graph: marking on dequeue queues 1,226 entries instead of 50
    complete = [[v for v in range(n) if v != u] for u in range(n)]
    assert pushes_mark_on_dequeue(complete, 0) == 1 + (n - 1) + sum(n - 1 - k for k in range(1, n))


if __name__ == "__main__":
    main()
```

**Time** O(V + E): each vertex enters the queue once and its list is scanned once. **Space** O(V). The same code works on directed graphs, following arrows only. Use `deque.popleft()`, never `list.pop(0)`, which shifts every element and makes BFS O(V²).

## 3. Why the first visit is the shortest

**Invariant.** The distances in the queue, front to back, are nondecreasing and differ by at most 1: `d, …, d, d+1, …, d+1`. It holds at the start, and each step removes a `d` from the front and appends `d + 1`s at the back, which keeps the pattern. So vertices leave the queue in nondecreasing `dist` order.

Now suppose some vertex got a value that is too large, and let `v` be such a vertex with the smallest true distance `k`. Its shortest path ends `…, w, v` with `w` at true distance `k − 1`, and by the choice of `v`, `dist[w] = k − 1` is correct. When `w` left the queue, it examined `v`: either `v` was new and got `k`, or it already had a value from a vertex that left no later than `w`, so at most `k`. Either way `dist[v] ≤ k`, a contradiction. No value is ever too small, since each is the length of a real path through parents.

The proof uses that **every edge costs the same**. With weights, three cheap edges can beat one expensive edge, and the first discovery is no longer the best: see [0–1 BFS and Dijkstra](../04-shortest-paths/README.md).

## 4. Mark when you enqueue, not when you dequeue

`bfs` sets `dist[v]` the moment `v` is **added** to the queue. Marking only when a vertex is **removed** still gives correct distances (later copies are skipped), but the same vertex can be queued many times. On a complete graph of 50 vertices, every vertex removed from the first layer queues all the not-yet-removed vertices again: 1,226 queue entries instead of 50, checked at the end of the §2 script. Marking on enqueue keeps the queue at most V long.

## 5. BFS on a grid

**Problem.** Fewest moves (up, down, left, right) from the top-left to the bottom-right open cell of a maze, or −1.

```text
     c0 c1 c2 c3          BFS distances
r0    .  .  .  #           0  1  2  #
r1    #  #  .  #           #  #  3  #
r2    .  .  .  .           6  5  4  5
r3    .  #  #  .           7  #  #  6
```

The grid is the implicit graph of [What a Graph Is](01-what-a-graph-is.md#5-grids-are-graphs-you-never-build): neighbors come from four offsets, and `dist` is a 2-D array. The target `(3, 3)` is reached at distance 6 via `(0,0) (0,1) (0,2) (1,2) (2,2) (2,3) (3,3)`.

The code is §2's loop with `(r, c)` pairs in the queue; `maze_distance` sits in the §6 script, tested against a cell-by-cell simulation. O(RC) time and space. Returning when the target is removed is safe; returning when it is added is also correct and slightly faster.

Variants: 8-direction moves (add four diagonal offsets, each a step of 1); nearest exit on the border (the target test becomes "on the border and not the start"); knight moves (eight L-shaped offsets).

## 6. Many sources at once: rotting oranges

**Problem.** A grid holds `2` (rotten), `1` (fresh) and `0` (empty). Each minute, every fresh orange beside a rotten one rots. How many minutes until none is fresh, or −1 if some never rot?

```text
minute 0      minute 1      minute 2      minute 3      minute 4
2 1 1         2 2 1         2 2 2         2 2 2         2 2 2
1 1 0         2 1 0         2 2 0         2 2 0         2 2 0
0 1 1         0 1 1         0 1 1         0 2 1         0 2 2
```

The answer is 4. **Brute force:** simulate minute by minute, rescanning the grid each time: O(RC) per minute and up to RC minutes.

**Key observation.** An orange rots at the minute equal to its BFS distance from the **nearest** initially rotten orange. Put **all** rotten oranges in the queue at distance 0 and run ordinary BFS: **multi-source BFS**. It is exactly a BFS from one invisible extra vertex joined to every source, with the first layer already done, so §3's proof still applies.

To count minutes, process the queue **one layer at a time**: read the queue length, remove that many cells, and count one minute.

| Minute | Layer removed | Cells rotted |
|---:|---|---|
| 0 → 1 | (0,0) | (0,1), (1,0) |
| 1 → 2 | (0,1), (1,0) | (0,2), (1,1) |
| 2 → 3 | (0,2), (1,1) | (2,1) |
| 3 → 4 | (2,1) | (2,2) |

```python
import random
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def maze_distance(grid):
    """Fewest moves from (0, 0) to the bottom-right cell of a '.'/'#' grid; -1 if impossible."""
    if not grid or not grid[0] or grid[0][0] == "#" or grid[-1][-1] == "#":
        return -1
    rows, cols = len(grid), len(grid[0])
    dist = [[-1] * cols for _ in range(rows)]
    dist[0][0] = 0
    queue = deque([(0, 0)])
    while queue:
        r, c = queue.popleft()
        if (r, c) == (rows - 1, cols - 1):
            return dist[r][c]
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != "#" and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return -1


def oranges_rotting(grid):
    """Minutes until no fresh orange remains, or -1. The input is not modified."""
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    state = [row[:] for row in grid]
    queue = deque((r, c) for r in range(rows) for c in range(cols) if state[r][c] == 2)
    fresh = sum(row.count(1) for row in state)
    minutes = 0
    while queue and fresh:
        for _ in range(len(queue)):  # exactly one layer
            r, c = queue.popleft()
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and state[nr][nc] == 1:
                    state[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))
        minutes += 1
    return minutes if fresh == 0 else -1


def oranges_simulate(grid):
    rows, cols = len(grid), len(grid[0])
    state = [row[:] for row in grid]
    minutes = 0
    while True:
        rot = [(r, c) for r in range(rows) for c in range(cols) if state[r][c] == 1
               and any(0 <= r + dr < rows and 0 <= c + dc < cols and state[r + dr][c + dc] == 2
                       for dr, dc in DIRS)]
        if not rot:
            break
        for r, c in rot:
            state[r][c] = 2
        minutes += 1
    return -1 if any(1 in row for row in state) else minutes


def main():
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert oranges_rotting([[0, 2]]) == 0
    assert oranges_rotting([[1]]) == -1
    assert oranges_rotting([[0]]) == 0
    assert oranges_rotting([]) == 0

    assert maze_distance(["...#", "##.#", "....", ".##."]) == 6
    assert maze_distance(["."]) == 0 and maze_distance(["#"]) == -1
    assert maze_distance([".#", "#."]) == -1 and maze_distance([]) == -1

    rng = random.Random(9)
    for _ in range(400):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        g = [[rng.choice((0, 1, 1, 2)) for _ in range(cols)] for _ in range(rows)]
        assert oranges_rotting(g) == oranges_simulate(g)
        maze = ["".join("#" if rng.random() < 0.3 else "." for _ in range(cols)) for _ in range(rows)]
        expected = -1  # the maze as oranges: the start is rotten, open cells are fresh
        if maze[0][0] == "." and maze[-1][-1] == ".":
            spread = [[1 if ch == "." else 0 for ch in row] for row in maze]
            spread[0][0] = 2
            for minute in range(rows * cols + 1):
                if spread[-1][-1] == 2:
                    expected = minute
                    break
                spread = [[2 if spread[r][c] == 1 and any(
                    0 <= r + dr < rows and 0 <= c + dc < cols and spread[r + dr][c + dc] == 2
                    for dr, dc in DIRS) else spread[r][c] for c in range(cols)] for r in range(rows)]
        assert maze_distance(maze) == expected


if __name__ == "__main__":
    main()
```

O(RC) time and space. The loop condition `while queue and fresh` stops before the last rotted layer is counted as an extra minute. The same pattern answers "distance to the nearest 0" (01 matrix), "distance to the nearest gate", and "as far from land as possible" (sources are all land cells; report the largest distance).

## 7. An implicit graph of words: word ladder

**Problem.** Change a start word into an end word one letter at a time, every intermediate word in a dictionary. How many words does the shortest sequence have (both ends counted), or 0 if impossible? `hit → hot → dot → dog → cog` with dictionary `{hot, dot, dog, lot, log, cog}` has 5.

Vertices are words; two words are joined when they differ in exactly one position. Comparing a word with every dictionary word costs O(N · L) per word, O(N² · L) in total for `N` words of length `L`.

**Better neighbor generation.** Put each word in `L` **buckets** by replacing one position with a wildcard: `hot` goes into `*ot`, `h*t`, `ho*`. Two words are neighbors exactly when they share a bucket.

| Bucket | Words |
|---|---|
| `*ot` | hot, dot, lot |
| `h*t` | hit, hot |
| `do*` | dot, dog |
| `*og` | dog, log, cog |
| `lo*` | lot, log |

BFS layers from `hit`: `{hit}`, `{hot}`, `{dot, lot}`, `{dog, log}`, `{cog}`. The end is in layer 4, so the ladder has 5 words.

```python
import random
from collections import defaultdict, deque


def ladder_length(begin, end, words):
    """Number of words in the shortest ladder from begin to end, or 0."""
    words = set(words)
    if end not in words:
        return 0
    if begin == end:
        return 1
    buckets = defaultdict(list)
    for w in words | {begin}:
        for i in range(len(w)):
            buckets[w[:i] + "*" + w[i + 1:]].append(w)
    dist = {begin: 1}
    queue = deque([begin])
    while queue:
        w = queue.popleft()
        for i in range(len(w)):
            key = w[:i] + "*" + w[i + 1:]
            for nxt in buckets.pop(key, ()):  # each bucket is used once
                if nxt not in dist:
                    dist[nxt] = dist[w] + 1
                    if nxt == end:
                        return dist[nxt]
                    queue.append(nxt)
    return 0


def ladder_brute(begin, end, words):
    """Explicit graph by comparing every pair, then repeated relaxation."""
    nodes = sorted(set(words) | {begin})
    if end not in set(words):
        return 0

    def close(a, b):
        return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1

    dist = {w: float("inf") for w in nodes}
    dist[begin] = 1
    for _ in range(len(nodes)):
        for a in nodes:
            for b in nodes:
                if close(a, b) and dist[a] + 1 < dist[b]:
                    dist[b] = dist[a] + 1
    return 0 if dist[end] == float("inf") else dist[end]


def main():
    words = ["hot", "dot", "dog", "lot", "log", "cog"]
    assert ladder_length("hit", "cog", words) == 5
    assert ladder_length("hit", "cog", words[:-1]) == 0
    assert ladder_length("hot", "hot", ["hot"]) == 1
    assert ladder_length("a", "c", ["a", "b", "c"]) == 2

    rng = random.Random(10)
    for _ in range(300):
        alphabet = "abc"
        vocab = list({"".join(rng.choice(alphabet) for _ in range(3)) for _ in range(rng.randint(1, 15))})
        begin = "".join(rng.choice(alphabet) for _ in range(3))
        end = rng.choice(vocab)
        assert ladder_length(begin, end, vocab) == ladder_brute(begin, end, vocab)


if __name__ == "__main__":
    main()
```

Building the buckets costs O(N · L²): `L` keys per word, each `L` characters long. `buckets.pop` uses each bucket once, since all its words get distances the first time it is opened, so the BFS also stays within O(N · L²) time and space. With both ends known and a huge graph, searching from both ends at once is faster: [bidirectional BFS](04-state-space-search.md#6-bidirectional-bfs-search-from-both-ends).

## 8. Two-coloring: is the graph bipartite?

**Problem.** Can every vertex be colored red or blue so that every edge joins two colors? Such a graph is **bipartite**: its vertices split into two sides with edges only across. A square `0 – 1 – 2 – 3 – 0` is (0, 2 red; 1, 3 blue). A triangle is not: 0 ≠ 1 and 1 ≠ 2 force 0 = 2, but 0 – 2 is an edge.

**Brute force.** Try all `2^V` colorings.

**Key observation.** One color fixes the whole component: neighbors get the other color, their neighbors the first, and so on. BFS colors even layers red and odd layers blue; the graph is bipartite exactly when no edge joins two vertices of the same color.

Square plus a triangle hanging off vertex 2 (edges `0–1, 1–2, 2–3, 3–0, 2–4, 4–5, 5–2`), showing the rows where something happens:

| Remove | Neighbor | Its color | Action |
|---:|---:|---|---|
| 0 (R) | 1, 3 | none | color both B |
| 1 (B) | 2 | none | color 2 R |
| 3 (B) | 2 | R | fine |
| 2 (R) | 4, 5 | none | color both B |
| 4 (B) | 5 | **B** | **conflict** |

The conflict exposes the odd cycle `2, 4, 5`. In general a graph is bipartite **if and only if it has no odd cycle**: going around an odd cycle flips the color an odd number of times and returns with the wrong color; conversely, a conflict on edge `u – v` with `u`, `v` in the same layer gives the odd cycle `u →` (up the BFS tree to their common ancestor) `→ v → u`.

```python
import itertools
import random
from collections import deque


def two_color(n, edges):
    """Return a list of 0/1 colors with every edge two-colored, or None."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    color = [-1] * n
    for s in range(n):  # every component needs its own start
        if color[s] != -1:
            continue
        color[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return None  # includes self-loops: u == v
    return color


def bipartite_brute(n, edges):
    return any(all(c[u] != c[v] for u, v in edges) for c in itertools.product((0, 1), repeat=n))


def main():
    square = [(0, 1), (1, 2), (2, 3), (3, 0)]
    assert two_color(4, square) == [0, 1, 0, 1]
    assert two_color(3, [(0, 1), (1, 2), (2, 0)]) is None
    assert two_color(6, square + [(2, 4), (4, 5), (5, 2)]) is None
    assert two_color(1, [(0, 0)]) is None
    assert two_color(3, []) == [0, 0, 0]
    assert two_color(0, []) == []

    rng = random.Random(11)
    for _ in range(400):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 9))]
        colors = two_color(n, edges)
        assert (colors is not None) == bipartite_brute(n, edges)
        if colors is not None:
            assert all(colors[u] != colors[v] for u, v in edges)


if __name__ == "__main__":
    main()
```

O(V + E) time and space. DFS works equally well; BFS makes the even/odd layers concrete. When edges arrive one at a time and the answer is needed after each, a disjoint-set union that tracks parity does it incrementally ([Disjoint Set Union](../02-connectivity-and-ordering/01-disjoint-set-union.md#102-parity-is-the-graph-still-two-colorable)).

## 9. Summary: BFS or DFS?

| Need | BFS | DFS |
|---|---|---|
| Reachability, components, flood fill | works | works |
| Fewest edges from a source | **yes** | no |
| Nearest of many sources | **yes** (multi-source) | no |
| Finishing order, topological sort, bridges | no | **yes** (frames) |
| Directed cycle detection | via Kahn's algorithm | **yes** (colors) |
| Memory on a wide, shallow graph | a whole layer | one path |
| Memory on a long, thin graph | small | the whole path |

BFS template: mark and set `dist` when a vertex is **added**; remove from the front of a `deque`; for rounds, process `len(queue)` vertices per round.

## 10. Pitfalls and practice

1. Marking on dequeue instead of enqueue: the queue grows to O(E) entries (§4).
2. `list.pop(0)`: each removal is O(V).
3. BFS on weighted edges. It finds the fewest *edges*, not the least *cost*.
4. Forgetting the layer loop when the answer is a number of rounds, or counting one extra round at the end.
5. Running multi-source BFS one source at a time: O(S · (V + E)) instead of O(V + E).
6. Two-coloring only the component of vertex 0.
7. Using `dist[target]` without checking for −1 (unreachable).

Practice: shortest path in binary matrix; rotting oranges; 01 matrix; walls and gates; as far from land as possible; nearest exit from entrance in maze; open the lock; word ladder; is graph bipartite; possible bipartition; minimum knight moves.

Next: [State-Space Search](04-state-space-search.md).
