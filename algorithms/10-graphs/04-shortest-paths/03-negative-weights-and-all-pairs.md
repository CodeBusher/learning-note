# Negative Weights and All Pairs — DAGs, Bellman–Ford, Floyd–Warshall

## 1. A trip with rebates

A traveler moves between five towns along one-way legs. Some legs come with a rebate larger than the ticket price, so their net cost is negative. [Dijkstra](02-dijkstra.md) cannot be used: it settles a vertex for good, and a negative edge can make a route cheaper later.

```text
0 → 1 (1)    0 → 2 (5)    0 → 4 (6)
1 → 2 (3)
2 → 3 (−2)
3 → 4 (2)
```

**Problem.** What is the cheapest net cost from town 0 to each town?

| Town | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| Cheapest | 0 | 1 | 4 | 2 | 4 |

Town 4 is reached for 4 by `0 → 1 → 2 → 3 → 4` (`1 + 3 − 2 + 2`), beating the direct leg of cost 6.

### When "cheapest" does not exist

Add one more leg, `3 → 2` with cost −1. Now `2 → 3 → 2` costs `−2 − 1 = −3`: a **negative cycle**. Going around it again and again lowers the cost without limit. Every town reachable *after* that cycle (2, 3 and 4) has no cheapest cost; we say its distance is `−∞`. Towns that can only be reached *without* passing the cycle (0 and 1) keep their normal values. And a negative cycle the traveler can never reach changes nothing at all.

So a correct algorithm must report three kinds of answers: a finite distance, `+∞` (unreachable), or `−∞` (unbounded below).

## 2. Graphs without cycles: relax in topological order

The rebate graph above has no cycle: every leg goes from a lower-numbered town to a higher one. A directed graph with no cycle is a **DAG** (directed acyclic graph).

**Key observation.** A **topological order** lists the vertices so that every edge goes from an earlier vertex to a later one. If we process vertices in that order and relax each vertex's outgoing edges, then by the time we reach `v`, *every* edge into `v` has already been relaxed from a vertex whose distance was already final. So `dist[v]` is final too, whatever the signs of the weights.

Here the order `0, 1, 2, 3, 4` works. One pass:

| Process | Relaxations | `dist[0..4]` after |
|---|---|---|
| start | — | `0 ∞ ∞ ∞ ∞` |
| 0 | 1 → 1, 2 → 5, 4 → 6 | `0 1 5 ∞ 6` |
| 1 | 2: 1 + 3 = 4 < 5 | `0 1 4 ∞ 6` |
| 2 | 3: 4 − 2 = 2 | `0 1 4 2 6` |
| 3 | 4: 2 + 2 = 4 < 6 | `0 1 4 2 4` |
| 4 | none | `0 1 4 2 4` |

To find a topological order ([Topological Sort and SCC](../02-connectivity-and-ordering/02-topological-sort-and-scc.md) covers it in depth), use **Kahn's algorithm**: count each vertex's incoming edges (its **in-degree**), start with the vertices whose in-degree is 0, and every time a vertex is output, decrease its neighbors' in-degrees, outputting any that reach 0. If some vertices never reach 0, the graph has a cycle.

```python
import random
from collections import deque
from math import inf


def topological_order(adj):
    n = len(adj)
    indegree = [0] * n
    for row in adj:
        for v, _ in row:
            indegree[v] += 1
    ready = deque(u for u in range(n) if indegree[u] == 0)
    order = []
    while ready:
        u = ready.popleft()
        order.append(u)
        for v, _ in adj[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                ready.append(v)
    if len(order) != n:
        raise ValueError("graph has a cycle")
    return order


def dag_shortest_paths(adj, source):
    """adj[u] holds (v, w); any signs. Returns (dist, parent)."""
    n = len(adj)
    if not 0 <= source < n:
        raise ValueError("source out of range")
    dist = [inf] * n
    parent = [None] * n
    dist[source] = 0
    for u in topological_order(adj):
        if dist[u] == inf:
            continue
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                parent[v] = u
    return dist, parent


def brute_force(adj, source):
    best = [inf] * len(adj)

    def dfs(u, cost):
        best[u] = min(best[u], cost)
        for v, w in adj[u]:
            dfs(v, cost + w)  # no cycles, so this terminates

    dfs(source, 0)
    return best


def main():
    trip = [[(1, 1), (2, 5), (4, 6)], [(2, 3)], [(3, -2)], [(4, 2)], []]
    dist, parent = dag_shortest_paths(trip, 0)
    assert dist == [0, 1, 4, 2, 4] and parent == [None, 0, 1, 2, 3]
    assert dag_shortest_paths([[]], 0) == ([0], [None])
    try:
        dag_shortest_paths([[(1, 1)], [(0, 1)]], 0)
    except ValueError:
        pass
    else:
        raise AssertionError("cycle accepted")

    rng = random.Random(14)
    for _ in range(400):
        n = rng.randint(1, 7)
        label = list(range(n))
        rng.shuffle(label)  # hide the order: edges go from smaller to larger label
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 12)):
            a, b = sorted(rng.sample(range(n), 2)) if n > 1 else (0, 0)
            if a != b:
                adj[label[a]].append((label[b], rng.randint(-5, 5)))
        source = rng.randrange(n)
        assert dag_shortest_paths(adj, source)[0] == brute_force(adj, source)


if __name__ == "__main__":
    main()
```

Time **O(V + E)**, space O(V). For the **longest** path in a DAG (for example the critical path of a project schedule), use `max` instead of `min` and `-inf` instead of `inf`. That is only easy because there are no cycles; longest simple path in a general graph is a famously hard problem. [Dynamic programming](../../09-dynamic-programming/README.md) treats DAG relaxation as a DP whose evaluation order is the topological order.

## 3. Bellman–Ford: relax everything, repeatedly

With cycles, there is no topological order. Bellman–Ford replaces "the right order" with "enough repetition".

**Key observation.** If no negative cycle is reachable, some shortest route is **simple** (it never repeats a vertex: removing a cycle of nonnegative cost never makes a route worse). A simple route has at most `V − 1` edges. Now relax **every** edge once; call that a **round**.

> After round `k`, `dist[v]` is at most the cost of the cheapest route to `v` that uses at most `k` edges.

By induction: the cheapest route with at most `k` edges ends with an edge `u → v`, and the part before it is a route to `u` with at most `k − 1` edges. After round `k − 1`, `dist[u]` is at most that part's cost, and round `k` relaxes `u → v`. So after `V − 1` rounds every shortest distance is found.

### Trace with a deliberately bad edge order

Relax the rebate graph's edges in this order: `3→4`, `2→3`, `1→2`, `0→1`, `0→2`, `0→4`. Each edge is listed before the edges that feed it, the worst order for in-place updates.

| Round | Changes during the round, in edge order | `dist[0..4]` after |
|---:|---|---|
| start | — | `0 ∞ ∞ ∞ ∞` |
| 1 | `0→1`: 1. `0→2`: 5. `0→4`: 6. (Earlier edges start at `∞`, skipped.) | `0 1 5 ∞ 6` |
| 2 | `2→3`: 5 − 2 = 3. `1→2`: 1 + 3 = 4 < 5. | `0 1 4 3 6` |
| 3 | `3→4`: 3 + 2 = 5 < 6. `2→3`: 4 − 2 = 2 < 3. | `0 1 4 2 5` |
| 4 | `3→4`: 2 + 2 = 4 < 5. | `0 1 4 2 4` |
| 5 (check) | no change | `0 1 4 2 4` |

It took all `V − 1 = 4` rounds because the best route to 4 has 4 edges. With a friendly order (topological order), one round would do; that is the DAG method of §2. An early exit, "stop when a round changes nothing", makes friendly inputs fast.

### Detecting negative cycles

If a reachable negative cycle exists, relaxations never stop. So after `V − 1` rounds, do one more check: any edge `u → v` that can still improve `dist[v]` means `v` is affected by a negative cycle. Every vertex reachable from such a `v` is also unbounded, so mark them all `−∞` with a search.

Add the leg `3 → 2 = −1` to the rebate graph. After 4 rounds, the edge `2→3` or `3→2` still improves, so the check marks 2 or 3, and the search spreads `−∞` to 2, 3 and 4. Towns 0 and 1 keep their values 0 and 1.

### SPFA: relax only what changed (a caveat)

Most edges in a round do nothing: their tail did not change in the last round. The **Shortest Path Faster Algorithm** (SPFA) keeps a queue of vertices whose distance has improved and relaxes only their outgoing edges. On many random inputs it is much faster.

The caveat: **its worst case is still O(V · E)**, and there are well-known inputs, and contest tests built on purpose, that drive it there. It is not a guaranteed improvement. Negative-cycle detection also needs care: a common method tracks how many edges the current best route to each vertex uses, and reports a cycle when that count reaches `V`.

```python
import random
from collections import deque
from math import inf


def bellman_ford(n, edges, source):
    """Directed edges (u, v, w). Returns (dist, parent) with -inf for unbounded."""
    if not 0 <= source < n:
        raise ValueError("source out of range")
    dist = [inf] * n
    parent = [None] * n
    dist[source] = 0
    for _ in range(n - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] != inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                parent[v] = u
                changed = True
        if not changed:
            break
    adj = [[] for _ in range(n)]
    queue = deque()
    unbounded = [False] * n
    for u, v, w in edges:
        adj[u].append(v)
        if dist[u] != inf and dist[u] + w < dist[v] and not unbounded[v]:
            unbounded[v] = True
            queue.append(v)
    while queue:
        u = queue.popleft()
        dist[u], parent[u] = -inf, None
        for v in adj[u]:
            if not unbounded[v]:
                unbounded[v] = True
                queue.append(v)
    return dist, parent


def spfa(n, edges, source):
    """Returns dist, or None if a negative cycle is reachable from source."""
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    dist = [inf] * n
    hops = [0] * n          # edges on the current best route
    in_queue = [False] * n
    dist[source] = 0
    queue = deque([source])
    in_queue[source] = True
    while queue:
        u = queue.popleft()
        in_queue[u] = False
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                hops[v] = hops[u] + 1
                if hops[v] >= n:
                    return None
                if not in_queue[v]:
                    in_queue[v] = True
                    queue.append(v)
    return dist


def brute_force(n, edges, source):
    """Simple paths for finite answers; negative simple cycles for -inf."""
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))

    def reach(starts):
        seen, stack = set(starts), list(starts)
        while stack:
            u = stack.pop()
            for v, _ in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        return seen

    on_negative_cycle = set()
    for start in range(n):
        def walk(u, cost, path):
            for v, w in adj[u]:
                if v == start and cost + w < 0:
                    on_negative_cycle.update(path)
                elif v not in path:
                    walk(v, cost + w, path + [v])
        walk(start, 0, [start])

    best = [inf] * n

    def dfs(u, cost, on_path):
        best[u] = min(best[u], cost)
        for v, w in adj[u]:
            if v not in on_path:
                dfs(v, cost + w, on_path | {v})

    dfs(source, 0, {source})
    bad = reach(on_negative_cycle & reach([source]))
    return [-inf if v in bad else best[v] for v in range(n)]


def main():
    trip = [(3, 4, 2), (2, 3, -2), (1, 2, 3), (0, 1, 1), (0, 2, 5), (0, 4, 6)]
    dist, parent = bellman_ford(5, trip, 0)
    assert dist == [0, 1, 4, 2, 4] and parent == [None, 0, 1, 2, 3]
    dist, _ = bellman_ford(5, trip + [(3, 2, -1)], 0)
    assert dist == [0, 1, -inf, -inf, -inf]
    # A negative cycle the source cannot reach changes nothing.
    assert bellman_ford(4, [(0, 1, 2), (2, 3, -5), (3, 2, 1)], 0)[0] == [0, 2, inf, inf]
    assert bellman_ford(1, [(0, 0, -1)], 0)[0] == [-inf]   # negative self-loop
    assert bellman_ford(1, [], 0) == ([0], [None])
    assert spfa(5, trip, 0) == [0, 1, 4, 2, 4] and spfa(1, [(0, 0, -1)], 0) is None

    rng = random.Random(15)
    for _ in range(500):
        n = rng.randint(1, 5)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 6))
                 for _ in range(rng.randint(0, 8))]
        source = rng.randrange(n)
        dist = bellman_ford(n, edges, source)[0]
        assert dist == brute_force(n, edges, source)
        assert spfa(n, edges, source) == (None if -inf in dist else dist)


if __name__ == "__main__":
    main()
```

Time **O(V · E)** for the rounds plus O(V + E) for the check and the search. Space O(V + E).

**Why the check is complete.** Suppose a negative cycle `x₁ → x₂ → … → x_k → x₁` is reachable, but no cycle edge can improve after round `V − 1`. Then `dist[x_{i+1}] ≤ dist[x_i] + w(x_i, x_{i+1})` for every edge of the cycle, and all these values are finite. Adding the inequalities around the cycle, the `dist` terms cancel and leave `0 ≤` (cycle weight), contradicting that the cycle is negative. So some cycle edge still improves, and the search from it marks the whole cycle and everything downstream.

**Global negative-cycle detection.** To ask "does the graph have a negative cycle anywhere?", start every vertex at distance 0 instead of only the source. That is the same as adding a virtual source with 0-weight edges to every vertex.

## 4. At most `k` edges: keep the previous round

Some problems limit the number of edges, for example "at most `k` flights". After round `k`, Bellman–Ford guarantees that `dist` is *at most* the best route with `k` edges, but in-place updates can sneak in longer routes within a single round, because an edge may read a value set earlier in the same round. For plain Bellman–Ford that only speeds things up; here it is a bug.

Edges in order `0→1 (1)`, `1→2 (1)`, with `0→2 (10)`, limit `k = 1`. In-place round 1: `dist[1] = 1`, then `1→2` immediately uses it: `dist[2] = 2`. That route has **2** edges, which is over the limit; the correct answer with one edge is 10.

The fix is to read only the **previous** round's values. Let `D[t][v]` be the cheapest route to `v` with at most `t` edges:

$$
D[t][v] = \min\Bigl(D[t-1][v],\ \min_{u \to v} D[t-1][u] + w(u, v)\Bigr).
$$

```python
from math import inf


def shortest_with_edge_limit(n, edges, source, k):
    """Cheapest route to each vertex using at most k edges."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    previous = [inf] * n
    previous[source] = 0
    for _ in range(k):
        current = previous[:]
        for u, v, w in edges:
            if previous[u] != inf and previous[u] + w < current[v]:
                current[v] = previous[u] + w
        previous = current
    return previous


def in_place_wrong(n, edges, source, k):
    dist = [inf] * n
    dist[source] = 0
    for _ in range(k):
        for u, v, w in edges:
            if dist[u] != inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


def main():
    edges = [(0, 1, 1), (1, 2, 1), (0, 2, 10)]
    assert shortest_with_edge_limit(3, edges, 0, 1) == [0, 1, 10]
    assert in_place_wrong(3, edges, 0, 1) == [0, 1, 2]   # used two edges
    assert shortest_with_edge_limit(3, edges, 0, 2) == [0, 1, 2]
    assert shortest_with_edge_limit(3, edges, 0, 0) == [0, inf, inf]
    # A negative cycle is harmless with a finite edge limit.
    assert shortest_with_edge_limit(1, [(0, 0, -1)], 0, 3) == [-3]


if __name__ == "__main__":
    main()
```

Time O(k · (V + E)), space O(V). [Modeling with State Graphs](04-modeling-and-variants.md) uses this for cheapest flights within `k` stops, and compares it with a state-augmented Dijkstra.

## 5. Floyd–Warshall: every pair at once, as a DP

**Problem.** Four warehouses, one-way roads with travel times. Fill in a table of the shortest time from every warehouse to every other one.

```text
0 → 1 (3)   0 → 3 (7)
1 → 0 (8)   1 → 2 (2)
2 → 0 (5)   2 → 3 (1)
3 → 0 (2)
```

Running Bellman–Ford from every vertex costs O(V² E). Floyd–Warshall does it in **O(V³)** with three nested loops and no data structures, which is the simplest choice when `V` is a few hundred.

### The DP state

Number the vertices `0 … V − 1`. Let `D_k[i][j]` be the shortest route from `i` to `j` whose **intermediate** vertices (all except the two ends) are among `0, …, k − 1`.

- `D_0[i][j]` allows no intermediate vertex: it is the direct edge weight (the smallest, if there are parallel edges), 0 when `i = j`, `∞` otherwise.
- Going from `D_k` to `D_{k+1}` allows vertex `k` as well. The best route either avoids `k` (cost `D_k[i][j]`) or passes through `k` once, splitting into `i ⇝ k` and `k ⇝ j`, each using only vertices below `k`:

$$
D_{k+1}[i][j] = \min\bigl(D_k[i][j],\ D_k[i][k] + D_k[k][j]\bigr).
$$

- `D_V[i][j]` allows every vertex, so it is the answer.

This is the DP pattern from [Dynamic programming](../../09-dynamic-programming/README.md): a state (`k, i, j`), a transition (use `k` or not), a base case (direct edges), and an evaluation order (increasing `k`, so the **`k` loop must be the outermost**).

**Why one matrix is enough.** Updating in place would mix `D_k` and `D_{k+1}` values. But during round `k`, row `k` and column `k` do not change: `D[i][k]` could only improve via `D[i][k] + D[k][k]`, and `D[k][k] = 0` when there is no negative cycle. So reading the matrix in place gives the same result.

### Trace

Each matrix shows the table after allowing one more intermediate vertex; changed entries are explained below it.

```text
D_0 (direct)        D_1 (via 0)         D_2 (via 0,1)       D_3 (via 0,1,2)     D_4 (all)
  0  3  ∞  7          0  3  ∞  7          0  3  5  7          0  3  5  6          0  3  5  6
  8  0  2  ∞          8  0  2 15          8  0  2 15          7  0  2  3          5  0  2  3
  5  ∞  0  1          5  8  0  1          5  8  0  1          5  8  0  1          3  6  0  1
  2  ∞  ∞  0          2  5  ∞  0          2  5  7  0          2  5  7  0          2  5  7  0
```

| Allow | Improvements |
|---|---|
| 0 | `1→3`: 8 + 7 = 15. `2→1`: 5 + 3 = 8. `3→1`: 2 + 3 = 5. |
| 1 | `0→2`: 3 + 2 = 5. `3→2`: 5 + 2 = 7. |
| 2 | `0→3`: 5 + 1 = 6 < 7. `1→0`: 2 + 5 = 7 < 8. `1→3`: 2 + 1 = 3 < 15. |
| 3 | `1→0`: 3 + 2 = 5 < 7. `2→0`: 1 + 2 = 3 < 5. `2→1`: 3 + 3 = 6 < 8. |

Read one entry back: `1 → 0` is 5, via `1 → 2 → 3 → 0` (`2 + 1 + 2`).

### Negative cycles and path reconstruction

If `D[k][k] < 0` after the loops, vertex `k` lies on a negative cycle. Then any pair `(i, j)` where `i` can reach `k` and `k` can reach `j` has distance `−∞`. Marking the whole matrix would be wrong: pairs that never touch the cycle keep finite values.

To rebuild routes, keep `nxt[i][j]`, the first vertex after `i` on the best route to `j`. Initially `nxt[i][j] = j` for each direct edge. When the route through `k` wins, set `nxt[i][j] = nxt[i][k]`. Then walk `i, nxt[i][j], nxt[nxt[i][j]][j], …` until `j`.

```python
import random
from math import inf


def floyd_warshall(n, edges):
    """Returns (dist, nxt). dist[i][j] is -inf when a negative cycle lies between."""
    dist = [[inf] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        nxt[i][i] = i
    for u, v, w in edges:
        if w < dist[u][v]:
            dist[u][v] = w
            nxt[u][v] = v
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == inf:
                continue
            di = dist[i]
            for j in range(n):
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
                    nxt[i][j] = nxt[i][k]
    negative = [k for k in range(n) if dist[k][k] < 0]
    for k in negative:
        for i in range(n):
            if dist[i][k] != inf:
                for j in range(n):
                    if dist[k][j] != inf:
                        dist[i][j] = -inf
                        nxt[i][j] = None
    return dist, nxt


def route(dist, nxt, i, j):
    if dist[i][j] in (inf, -inf):
        return []
    path = [i]
    while i != j:
        i = nxt[i][j]
        path.append(i)
    return path


def bellman_ford(n, edges, source):
    dist = [inf] * n
    dist[source] = 0
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    adj = [[] for _ in range(n)]
    stack = []
    for u, v, w in edges:
        adj[u].append(v)
        if dist[u] != inf and dist[u] + w < dist[v]:
            stack.append(v)
    seen = set(stack)
    while stack:
        u = stack.pop()
        dist[u] = -inf
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return dist


def main():
    roads = [(0, 1, 3), (0, 3, 7), (1, 0, 8), (1, 2, 2), (2, 0, 5), (2, 3, 1), (3, 0, 2)]
    dist, nxt = floyd_warshall(4, roads)
    assert dist == [[0, 3, 5, 6], [5, 0, 2, 3], [3, 6, 0, 1], [2, 5, 7, 0]]
    assert route(dist, nxt, 1, 0) == [1, 2, 3, 0]
    assert route(dist, nxt, 2, 2) == [2]

    cyc = [(0, 1, 1), (1, 2, -2), (2, 1, 1), (2, 3, 2)]
    dist, nxt = floyd_warshall(4, cyc)
    assert dist[0] == [0, -inf, -inf, -inf] and dist[3] == [inf, inf, inf, 0]
    assert dist[1][0] == inf and route(dist, nxt, 0, 3) == []
    assert floyd_warshall(0, []) == ([], [])

    rng = random.Random(17)
    for _ in range(400):
        n = rng.randint(1, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-2, 7))
                 for _ in range(rng.randint(0, 10))]
        dist, nxt = floyd_warshall(n, edges)
        weight = {}
        for u, v, w in edges:
            weight[u, v] = min(weight.get((u, v), inf), w)
        for s in range(n):
            assert dist[s] == bellman_ford(n, edges, s)
            for t in range(n):
                path = route(dist, nxt, s, t)
                if path:
                    assert sum(weight[a, b] for a, b in zip(path, path[1:])) == dist[s][t]


if __name__ == "__main__":
    main()
```

Time **O(V³ + E)**, space **O(V²)**. The inner loop is plain arithmetic, so in Python it handles `V` around 300–400 comfortably.

**Related uses of the same loop.** Replace `min`/`+` with `or`/`and` to get **transitive closure** (who can reach whom). Replace them with `min`/`max` to get all-pairs **bottleneck** routes. With `k` outermost, the same correctness argument applies.

## 6. Johnson's algorithm: all pairs on a sparse graph with negative edges (advanced)

Floyd–Warshall costs O(V³) even when the graph has few edges. Dijkstra from every vertex costs O(V (V + E) log V), which is better for sparse graphs, but needs nonnegative weights. Johnson's algorithm makes the weights nonnegative **without** changing which routes are shortest.

1. Add a virtual vertex `q` with a 0-weight edge to every vertex. Run Bellman–Ford from `q` to get `h[v]`, a **potential** for each vertex. If a negative cycle exists, stop.
2. Reweight every edge: `w'(u, v) = w(u, v) + h[u] − h[v]`. Since `h[v] ≤ h[u] + w(u, v)` (a shortest-path property), `w' ≥ 0`.
3. Run Dijkstra from every vertex with `w'`. Convert back: `dist(s, t) = dist'(s, t) − h[s] + h[t]`.

**Why routes keep their order.** Along any route `s = x₀ → x₁ → … → x_m = t`, the reweighted cost is the original cost plus `h[x₀] − h[x₁] + h[x₁] − h[x₂] + … − h[x_m]`. The middle terms cancel (they **telescope**), leaving original cost `+ h[s] − h[t]`. Every route between the same `s` and `t` shifts by the same amount, so the cheapest stays the cheapest. Compare [§7 of the Dijkstra chapter](02-dijkstra.md#7-negative-edges-break-it): adding a constant to every edge shifts each route by a different amount.

```python
import random
from heapq import heappop, heappush
from math import inf


def johnson(n, edges):
    """All-pairs distances; raises ValueError on a negative cycle."""
    h = [0] * n  # Bellman-Ford from a virtual source with 0-edges to all
    for _ in range(n):
        changed = False
        for u, v, w in edges:
            if h[u] + w < h[v]:
                h[v] = h[u] + w
                changed = True
        if not changed:
            break
    else:
        if any(h[u] + w < h[v] for u, v, w in edges):
            raise ValueError("negative cycle")
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w + h[u] - h[v]))
    result = []
    for s in range(n):
        dist = [inf] * n
        dist[s] = 0
        heap = [(0, s)]
        while heap:
            d, u = heappop(heap)
            if d != dist[u]:
                continue
            for v, w in adj[u]:
                if d + w < dist[v]:
                    dist[v] = d + w
                    heappush(heap, (dist[v], v))
        result.append([d - h[s] + h[t] if d < inf else inf for t, d in enumerate(dist)])
    return result


def floyd(n, edges):
    d = [[0 if i == j else inf for j in range(n)] for i in range(n)]
    for u, v, w in edges:
        d[u][v] = min(d[u][v], w)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


def main():
    trip = [(0, 1, 1), (0, 2, 5), (0, 4, 6), (1, 2, 3), (2, 3, -2), (3, 4, 2)]
    assert johnson(5, trip)[0] == [0, 1, 4, 2, 4]
    try:
        johnson(2, [(0, 1, -1), (1, 0, -1)])
    except ValueError:
        pass
    else:
        raise AssertionError("negative cycle missed")

    rng = random.Random(18)
    checked = 0
    while checked < 300:
        n = rng.randint(1, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 8))
                 for _ in range(rng.randint(0, 10))]
        expected = floyd(n, edges)
        if any(expected[i][i] < 0 for i in range(n)):
            continue
        assert johnson(n, edges) == expected
        checked += 1


if __name__ == "__main__":
    main()
```

Time O(V E + V (V + E) log V), space O(V + E) plus the O(V²) output.

## 7. Summary: choosing a method

| Graph | Question | Method | Time |
|---|---|---|---:|
| DAG, any weights | One source | Topological relaxation | O(V + E) |
| Any, some negative weights | One source, detect negative cycles | Bellman–Ford | O(V E) |
| Any | One source, at most `k` edges | Layered Bellman–Ford | O(k (V + E)) |
| Dense, any weights | All pairs | Floyd–Warshall | O(V³) |
| Sparse, negative weights, no negative cycle | All pairs | Johnson | O(V E + V (V + E) log V) |
| Nonnegative weights | One source | [Dijkstra](02-dijkstra.md) | O((V + E) log V) |

## 8. Pitfalls and practice

1. Putting the `k` loop of Floyd–Warshall inside the `i` or `j` loop. The DP order is then wrong and some distances are missed.
2. Declaring the whole answer invalid because the graph has a negative cycle somewhere. Only vertices reachable *through* a reachable cycle are `−∞`.
3. Relaxing from an `inf` vertex. `inf + (−5)` is still `inf` in Python, but in fixed-width languages a large sentinel plus a negative weight looks like a real distance. Skip `inf` tails explicitly.
4. Using in-place updates for an edge-limited question. Copy the previous round.
5. An **undirected** edge with negative weight is a negative cycle by itself: go across and back. Model it as two directed edges and expect `−∞`.
6. Treating SPFA as linear time. It is Bellman–Ford with a better average, not a better worst case.
7. Forgetting `dist[i][i] = 0` in Floyd–Warshall, or taking the last parallel edge instead of the smallest.

Practice: course schedule with weighted prerequisites (DAG longest path); cheapest flights within `k` stops (layered Bellman–Ford); detect an arbitrage opportunity in a currency table (negative cycle on `−log` rates); find the city with the smallest number of neighbors at a threshold distance (Floyd–Warshall); transitive closure for course prerequisite queries.

Next: [Modeling with State Graphs](04-modeling-and-variants.md).
