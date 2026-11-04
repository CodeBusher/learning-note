# BFS and 0–1 BFS — Shortest Paths Without a Heap

## 1. Fewest stops on a subway map

Seven stations, numbered 0 to 6. A line segment joins two stations if a train runs directly between them, in both directions:

```text
   0 ─── 1 ─── 3 ─── 5 ─── 6
   │           │     │
   2 ──────────┘     │
   │                 │
   4 ────────────────┘
```

Segments: `0–1`, `0–2`, `1–3`, `2–3`, `2–4`, `3–5`, `4–5`, `5–6`.

**Problem.** From station 0, what is the fewest number of segments needed to reach each station? And what route achieves it for station 6?

| Station | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fewest segments `dist[v]` | 0 | 1 | 1 | 2 | 2 | 3 | 4 |

Every edge has the same cost, so the graph is **unweighted** and "cost" means "number of edges". A route is a **shortest path** when no route has smaller total cost.

**Brute force.** A shortest route never revisits a vertex (cutting out the loop only shortens it), so trying every **simple path** (no repeated vertex) with a depth-first search is correct. But on a `k × k` grid the corner-to-corner simple paths number 8,512 for `k = 5` and more than 10²⁴ for `k = 12`. It is a test oracle, not a solution.

## 2. BFS: visit in order of distance

**The key observation.** Every station at distance `d + 1` is a neighbor of some station at distance `d`, and of no station at distance less than `d`. So if we process all stations at distance 0, then all at distance 1, and so on, the first time we see a station we have found its distance. ([Search and traversal](../01-search-and-traversal/03-bfs.md) introduces BFS as exploration; here the point is the distance proof.)

A **queue** (first in, first out) gives that order automatically: stations are added at the back and removed from the front, so all distance-`d` stations leave the queue before any distance-`d + 1` station.

**Invariant.** The queue holds stations in nondecreasing order of distance, and its first and last entries differ by at most 1.

The algorithm:

1. Set `dist[source] = 0`, every other `dist` to "unseen", and put the source in the queue.
2. Remove the front station `u`. For each neighbor `v` that is still unseen, set `dist[v] = dist[u] + 1`, record `parent[v] = u`, and add `v` to the back.
3. Repeat until the queue is empty.

`parent[v]` remembers which station discovered `v`. Following parents back from any station traces a shortest route in reverse.

### Trace from station 0

| Step | Remove | Unseen neighbors found | `dist[0..6]` after the step (`·` = unseen) | Queue after the step |
|---:|---|---|---|---|
| 0 | — | — | `0 · · · · · ·` | `[0]` |
| 1 | 0 | 1, 2 | `0 1 1 · · · ·` | `[1, 2]` |
| 2 | 1 | 3 | `0 1 1 2 · · ·` | `[2, 3]` |
| 3 | 2 | 4 (3 already seen) | `0 1 1 2 2 · ·` | `[3, 4]` |
| 4 | 3 | 5 | `0 1 1 2 2 3 ·` | `[4, 5]` |
| 5 | 4 | none (5 already seen) | unchanged | `[5]` |
| 6 | 5 | 6 | `0 1 1 2 2 3 4` | `[6]` |
| 7 | 6 | none | unchanged | `[]` |

Parents: `parent[1] = 0`, `parent[2] = 0`, `parent[3] = 1`, `parent[4] = 2`, `parent[5] = 3`, `parent[6] = 5`. From 6: `6 → 5 → 3 → 1 → 0`. Reversed, the route is `0 → 1 → 3 → 5 → 6`.

Look at step 3: station 3 is a neighbor of 2, but it was already seen with distance 2. The route through 2 would also have length 2, never shorter. That is why a station can be marked when it is **first added** to the queue.

## 3. Code: distances, routes, and the number of shortest routes

A common follow-up asks **how many** different shortest routes reach each vertex. BFS gives this almost for free. `ways[v]` counts the shortest routes to `v`. When `u` is removed and `v` is a neighbor with `dist[v] == dist[u] + 1`, every shortest route to `u` extends to a shortest route to `v`, so add `ways[u]` to `ways[v]`. On the subway map, station 3 is reached in two segments both via 1 and via 2, so `ways[3] = 2`.

```python
import random
from collections import deque


def bfs(adj, source):
    """Unweighted shortest paths. Returns (dist, parent, ways); dist is None if unreachable."""
    n = len(adj)
    if not 0 <= source < n:
        raise ValueError("source out of range")
    dist = [None] * n
    parent = [None] * n
    ways = [0] * n
    dist[source] = 0
    ways[source] = 1
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if dist[v] is None:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
            if dist[v] == dist[u] + 1:
                ways[v] += ways[u]
    return dist, parent, ways


def route_to(parent, dist, target):
    """Shortest route from the source to target, or [] if unreachable."""
    if dist[target] is None:
        return []
    route = []
    while target is not None:
        route.append(target)
        target = parent[target]
    return route[::-1]


def brute_force(adj, source):
    """Try every simple path; return (dist, ways) by enumeration."""
    n = len(adj)
    dist, ways = [None] * n, [0] * n

    def dfs(u, length, on_path):
        if dist[u] is None or length < dist[u]:
            dist[u], ways[u] = length, 1
        elif length == dist[u]:
            ways[u] += 1
        for v in adj[u]:
            if v not in on_path:
                on_path.add(v)
                dfs(v, length + 1, on_path)
                on_path.remove(v)

    dfs(source, 0, {source})
    return dist, ways


def undirected(n, pairs):
    adj = [[] for _ in range(n)]
    for u, v in pairs:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def main():
    subway = undirected(7, [(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (5, 6)])
    dist, parent, ways = bfs(subway, 0)
    assert dist == [0, 1, 1, 2, 2, 3, 4]
    assert route_to(parent, dist, 6) == [0, 1, 3, 5, 6]
    assert ways == [1, 1, 1, 2, 1, 3, 3]

    lonely = [[1], [0], []]
    dist, parent, _ = bfs(lonely, 0)
    assert dist == [0, 1, None] and route_to(parent, dist, 2) == []
    assert route_to(parent, dist, 0) == [0]

    rng = random.Random(11)
    for _ in range(300):
        n = rng.randint(1, 7)
        directed = rng.random() < 0.5
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 12)):
            u, v = rng.randrange(n), rng.randrange(n)
            if u == v:
                continue
            if v not in adj[u]:
                adj[u].append(v)
            if not directed and u not in adj[v]:
                adj[v].append(u)
        source = rng.randrange(n)
        dist, parent, ways = bfs(adj, source)
        assert (dist, ways) == brute_force(adj, source)
        for t in range(n):
            route = route_to(parent, dist, t)
            if dist[t] is not None:
                assert len(route) == dist[t] + 1 and route[0] == source and route[-1] == t
                assert all(b in adj[a] for a, b in zip(route, route[1:]))


if __name__ == "__main__":
    main()
```

Time **O(V + E)**: each vertex enters the queue once and each adjacency list is scanned once. Space O(V) beyond the graph. The route counts can grow exponentially; Python integers handle that, but fixed-width languages usually ask for the count modulo a prime.

**Why it is correct.** By induction on `d`: when the first vertex at distance `d + 1` is removed from the queue, every vertex at distance `≤ d` has already been removed and has already discovered all its unseen neighbors. A vertex `v` at true distance `d + 1` has a neighbor at distance `d`, which discovered it with `dist[v] = d + 1`. It could not have been discovered earlier with a smaller value, because then it would have a neighbor at distance less than `d`, giving it distance at most `d`.

**If every edge costs the same positive amount `c`**, run BFS and multiply the edge counts by `c`. **With several sources** (for example "distance from the nearest hospital"), put every source in the queue at distance 0 before starting; this is **multi-source BFS**.

## 4. Zero-cost edges break plain BFS

Now let some edges be free. A road network where some links are toll roads (cost 1) and others are free (cost 0):

```text
         1
   0 ───────→ 1 ───1───→ 4
   │          ↑          ↑
   0          0          │
   ↓          │          │
   2 ───0───→ 3 ────1────┘
```

Directed edges: `0→1 = 1`, `0→2 = 0`, `2→3 = 0`, `3→1 = 0`, `1→4 = 1`, `3→4 = 1`.

The true cheapest cost to reach 1 is **0**, via `0 → 2 → 3 → 1`. Plain BFS from 0 discovers 1 first, directly, and marks it with cost 1. When the free route arrives later, 1 is already marked and the improvement is thrown away.

Plain BFS assumed "found first means found cheapest". With 0-cost edges, a route with *more* edges can be *cheaper*, so that assumption fails.

## 5. 0–1 BFS: a deque keeps the order

**The key observation.** BFS worked because the queue stayed sorted by distance. When we process a vertex at distance `d`:

- a 0-edge gives a neighbor a candidate distance `d`, which is the smallest possible value right now, so it belongs at the **front**;
- a 1-edge gives a candidate distance `d + 1`, which belongs at the **back**, exactly as in BFS.

A **deque** (double-ended queue) supports adding and removing at both ends in O(1). Python has `collections.deque` with `appendleft`, `append` and `popleft`.

**Invariant.** The deque holds entries `(distance, vertex)` in nondecreasing order of distance, using at most two consecutive values `d` and `d + 1`.

Because a vertex's distance can improve after it was added, we use **relaxation** instead of "mark when first seen": whenever `dist[u] + w < dist[v]`, set `dist[v] = dist[u] + w` and add `v` again. An old entry for `v` stays in the deque; when it is removed, its saved distance no longer matches `dist[v]`, so it is **stale** and skipped.

### Trace from vertex 0

`inf` means not reached yet. Entries are written `(distance, vertex)`.

| Step | Remove | Relaxations | `dist[0..4]` after | Deque after |
|---:|---|---|---|---|
| 0 | — | — | `0 inf inf inf inf` | `[(0,0)]` |
| 1 | `(0,0)` | `0→1`: 0+1 < inf, back. `0→2`: 0+0 < inf, front | `0 1 0 inf inf` | `[(0,2), (1,1)]` |
| 2 | `(0,2)` | `2→3`: 0+0 < inf, front | `0 1 0 0 inf` | `[(0,3), (1,1)]` |
| 3 | `(0,3)` | `3→1`: 0+0 < 1, **improve**, front. `3→4`: 0+1 < inf, back | `0 0 0 0 1` | `[(0,1), (1,1), (1,4)]` |
| 4 | `(0,1)` | `1→4`: 0+1 < 1? no | unchanged | `[(1,1), (1,4)]` |
| 5 | `(1,1)` | stale: saved 1 ≠ `dist[1]` = 0, skip | unchanged | `[(1,4)]` |
| 6 | `(1,4)` | no outgoing edges | unchanged | `[]` |

Final distances: `[0, 0, 0, 0, 1]`. Step 3 is exactly the improvement plain BFS lost.

## 6. Code: 0–1 BFS, tested against brute force

```python
import random
from collections import deque
from math import inf


def zero_one_bfs(adj, source):
    """adj[u] holds (v, w) with w in {0, 1}. Returns (dist, parent)."""
    n = len(adj)
    if not 0 <= source < n:
        raise ValueError("source out of range")
    if any(w not in (0, 1) for row in adj for _, w in row):
        raise ValueError("0-1 BFS needs every weight to be 0 or 1")
    dist = [inf] * n
    parent = [None] * n
    dist[source] = 0
    dq = deque([(0, source)])
    while dq:
        d, u = dq.popleft()
        if d != dist[u]:
            continue  # stale entry
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                parent[v] = u
                if w == 0:
                    dq.appendleft((dist[v], v))
                else:
                    dq.append((dist[v], v))
    return dist, parent


def brute_force(adj, source):
    """Cheapest simple path to every vertex, by trying them all."""
    best = [inf] * len(adj)

    def dfs(u, cost, on_path):
        best[u] = min(best[u], cost)
        for v, w in adj[u]:
            if v not in on_path:
                on_path.add(v)
                dfs(v, cost + w, on_path)
                on_path.remove(v)

    dfs(source, 0, {source})
    return best


def min_obstacles(grid):
    """Fewest obstacle cells (1s) to clear to walk from top-left to bottom-right."""
    rows, cols = len(grid), len(grid[0])
    adj = [[] for _ in range(rows * cols)]
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    adj[r * cols + c].append((nr * cols + nc, grid[nr][nc]))
    dist, _ = zero_one_bfs(adj, 0)
    return dist[-1] + grid[0][0]


def main():
    roads = [[(1, 1), (2, 0)], [(4, 1)], [(3, 0)], [(1, 0), (4, 1)], []]
    dist, parent = zero_one_bfs(roads, 0)
    assert dist == [0, 0, 0, 0, 1]
    assert parent == [None, 3, 0, 2, 3]
    assert zero_one_bfs([[(0, 0)]], 0) == ([0], [None])  # zero-weight self-loop
    try:
        zero_one_bfs([[(0, 2)]], 0)
    except ValueError:
        pass
    else:
        raise AssertionError("weight 2 accepted")

    assert min_obstacles([[0, 1, 1], [1, 1, 0], [1, 1, 0]]) == 2
    assert min_obstacles([[0, 1, 0, 0, 0], [0, 1, 0, 1, 0], [0, 0, 0, 1, 0]]) == 0

    rng = random.Random(12)
    for _ in range(400):
        n = rng.randint(1, 7)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 14)):
            adj[rng.randrange(n)].append((rng.randrange(n), rng.randint(0, 1)))
        source = rng.randrange(n)
        dist, parent = zero_one_bfs(adj, source)
        assert dist == brute_force(adj, source)
        for v in range(n):  # every parent edge is tight
            if parent[v] is not None:
                assert any(x == v and dist[parent[v]] + w == dist[v] for x, w in adj[parent[v]])


if __name__ == "__main__":
    main()
```

Time **O(V + E)**: an entry is added only after a strict improvement, and a distance can improve at most once per incoming edge processed, so there are O(E) entries; stale ones are skipped in O(1). Space O(V + E) in the worst case for the deque.

**Why it is correct.** The deque invariant means the next non-stale entry always has the smallest distance among everything waiting, exactly like the heap in [Dijkstra](02-dijkstra.md). With nonnegative weights, no later route can undercut it, so its distance is final when it is removed. The proof in [Dijkstra](02-dijkstra.md#6-why-it-is-correct) applies word for word; 0–1 BFS is Dijkstra with a deque in place of a heap, which works because only two distance values are ever waiting at once.

## 7. Summary and variants

| | BFS | 0–1 BFS |
|---|---|---|
| Weights | all equal | 0 or 1 |
| Container | queue | deque: 0-edges to the front, 1-edges to the back |
| Final when | first discovered | popped and not stale |
| Invariant | queue sorted by distance, values `d` and `d + 1` | same |
| Time | O(V + E) | O(V + E) |

Problems that reduce to 0–1 BFS:

| Situation | Model | Edge weights |
|---|---|---|
| Fewest obstacles to remove in a grid | Step into a free cell / an obstacle cell | 0 / 1 |
| Fewest arrow changes to cross a grid of arrows | Follow the arrow / change it | 0 / 1 |
| Fewest reversals to make every node reachable from 0 | Original edge / added reverse edge | 0 / 1 |
| Weights only `0` or `c > 0` | Divide by `c`, run 0–1 BFS, multiply back | 0 / 1 |
| Weights in `{1, …, k}` with small `k` | Split each edge into a chain of unit edges, or use `k + 1` buckets (Dial's algorithm) | 1 |

Weights `{a, b}` with `0 < a < b` cannot be reduced to `{0, 1}` by subtracting `a`: that would change costs by `a` times the number of edges, which favors routes with more edges. Use [Dijkstra](02-dijkstra.md).

## 8. Pitfalls and practice

1. Marking a vertex "visited" when it is first discovered, in a graph with 0-cost edges. Use relaxation and stale checks instead.
2. Pushing 0-edges to the back of the deque. The deque stops being sorted and the result can be wrong.
3. Forgetting the stale check in 0–1 BFS. The answer stays correct but vertices are expanded repeatedly, losing the linear bound.
4. Confusing "unreachable" with "distance 0". Use `None` or `inf`, never 0, as the "not reached" marker.
5. In multi-source BFS, adding sources one at a time with separate BFS runs. One run seeded with all sources is enough.
6. Counting shortest routes by adding `ways[u]` only when `v` is first discovered. Every later neighbor at distance `dist[v] − 1` must also contribute.

Practice: shortest path in a binary matrix; rotting oranges (multi-source); word ladder; number of shortest paths; minimum obstacle removal to reach a corner; minimum cost to make at least one valid path in a grid; reorder routes to make all paths lead to city zero.

Next: [Dijkstra's Algorithm](02-dijkstra.md).
