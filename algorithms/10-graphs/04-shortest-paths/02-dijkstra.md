# Dijkstra's Algorithm — Finalize the Closest Vertex First

## 1. Delivery times

A courier starts at depot 0. Roads are one-way, and each has a travel time in minutes:

```text
from 0:  → 1 (4 min)   → 2 (1 min)
from 1:  → 3 (1 min)
from 2:  → 1 (2 min)   → 3 (5 min)   → 4 (8 min)
from 3:  → 4 (3 min)   → 5 (6 min)
from 4:  → 5 (2 min)
from 5:  no roads out
```

**Problem.** What is the shortest travel time from 0 to every place, and which route achieves it for place 5?

The answer:

| Place | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| Shortest time | 0 | 3 | 1 | 4 | 7 | 9 |

The route to 5 is `0 → 2 → 1 → 3 → 4 → 5`: `1 + 2 + 1 + 3 + 2 = 9`.

**Brute force** over simple paths is correct (with nonnegative weights a loop never helps) but exponential, as in [BFS and 0–1 BFS](01-bfs-and-zero-one-bfs.md). **BFS** minimizes the *number of roads*: it settles place 1 by the direct 4-minute road, while `0 → 2 → 1` takes 3. Fewer edges is not less time.

## 2. The key observation

Keep a **tentative distance** `dist[v]` for every place: the best travel time found so far, `inf` if none. Initially `dist[0] = 0` and everything else is `inf`.

The basic step is **relaxation** of an edge `u → v` with weight `w`: if going through `u` is better than what we know, take it.

$$
\text{if } dist[u] + w < dist[v]:\quad dist[v] \leftarrow dist[u] + w,\quad parent[v] \leftarrow u.
$$

Now the observation that makes Dijkstra work:

> **Among all places not yet settled, the one with the smallest tentative distance already has its true shortest distance.**

Why: any other route to it must leave the settled region at some point, through some unsettled place `x`. Reaching `x` already costs at least `dist[x]`, which is no less than the smallest tentative distance. The rest of that route has nonnegative weights, so it can only add. No route can beat the current value.

So the algorithm **settles** (finalizes) the closest unsettled place, relaxes its outgoing edges, and repeats.

**Invariant.** Every settled place has its true shortest distance; every unsettled place's `dist` is the shortest route whose every vertex except the last is settled.

## 3. Trace with a plain array

Find the closest unsettled place by scanning all of them. ✓ marks settled places.

| Round | Settle (distance) | Relaxations that improve something | `dist[0..5]` after the round |
|---:|---|---|---|
| 0 | — | — | `0 ∞ ∞ ∞ ∞ ∞` |
| 1 | 0 (0) | 0→1: 4, 0→2: 1 | `0✓ 4 1 ∞ ∞ ∞` |
| 2 | 2 (1) | 2→1: 1+2 = 3 < 4, 2→3: 6, 2→4: 9 | `0✓ 3 1✓ 6 9 ∞` |
| 3 | 1 (3) | 1→3: 3+1 = 4 < 6 | `0✓ 3✓ 1✓ 4 9 ∞` |
| 4 | 3 (4) | 3→4: 4+3 = 7 < 9, 3→5: 10 | `0✓ 3✓ 1✓ 4✓ 7 10` |
| 5 | 4 (7) | 4→5: 7+2 = 9 < 10 | `0✓ 3✓ 1✓ 4✓ 7✓ 9` |
| 6 | 5 (9) | none | all ✓ |

Follow place 1: it starts at 4 (direct road), improves to 3 in round 2 when place 2 is settled, and is settled at 3 in round 3. Place 5 improves twice: 10 via 3, then 9 via 4.

Each round scans `V` places, so this version takes **O(V² + E)**. That is fine for dense graphs, but slow when `V` is large and each place has only a few roads.

## 4. A heap, with lazy deletion

A **min-heap** of `(distance, place)` pairs returns the smallest pair in O(log size); Python's `heapq` provides one ([Heaps and priority queues](../../07-heaps-and-priority-queues/README.md) builds it). The catch: Python's heap cannot **lower** the priority of an entry already inside it. When `dist[1]` improves from 4 to 3, the entry `(4, 1)` is stuck in the heap.

**Lazy deletion** solves it: push a fresh entry `(3, 1)` and leave the old one. When an entry is popped, compare its distance with `dist[place]`. If they differ, the entry is **stale** (a better value was found after it was pushed) and is skipped.

Trace, with the heap shown sorted. Only the pops differ from the array version: the non-stale ones settle 0, 2, 1, 3, 4, 5 in the same order, and four stale entries are skipped.

| Pop | Stale? | `dist[0..5]` after | Heap after |
|---|---|---|---|
| `(0,0)` | no | `0 4 1 ∞ ∞ ∞` | `(1,2) (4,1)` |
| `(1,2)` | no | `0 3 1 6 9 ∞` | `(3,1) (4,1) (6,3) (9,4)` |
| `(3,1)` | no | `0 3 1 4 9 ∞` | `(4,1) (4,3) (6,3) (9,4)` |
| `(4,1)` | **yes**: `dist[1]` = 3 | unchanged | `(4,3) (6,3) (9,4)` |
| `(4,3)` | no | `0 3 1 4 7 10` | `(6,3) (7,4) (9,4) (10,5)` |
| `(6,3)` | **yes**: `dist[3]` = 4 | unchanged | `(7,4) (9,4) (10,5)` |
| `(7,4)` | no | `0 3 1 4 7 9` | `(9,4) (9,5) (10,5)` |
| `(9,4)`, `(9,5)`, `(10,5)` | yes, no, yes | final | empty |

**Path reconstruction.** Each improvement recorded `parent[v] = u`. At the end, `parent = [None, 2, 0, 1, 3, 4]`. Follow from 5: `5 → 4 → 3 → 1 → 2 → 0`; reversed, `0 → 2 → 1 → 3 → 4 → 5`.

## 5. Code, tested against two independent methods

The script checks Dijkstra (heap and array versions) against brute-force enumeration of simple paths and against Bellman–Ford, a simpler but slower method from [the next chapter](03-negative-weights-and-all-pairs.md): relax every edge `V − 1` times.

```python
import random
from heapq import heappop, heappush
from math import inf


def dijkstra(adj, source):
    """adj[u] holds (v, w) with w >= 0. Returns (dist, parent)."""
    n = len(adj)
    if not 0 <= source < n:
        raise ValueError("source out of range")
    if any(w < 0 for row in adj for _, w in row):
        raise ValueError("Dijkstra needs nonnegative weights")
    dist = [inf] * n
    parent = [None] * n
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue  # stale entry
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                parent[v] = u
                heappush(heap, (dist[v], v))
    return dist, parent


def dijkstra_dense(adj, source):
    """O(V^2 + E) version: scan for the closest unsettled vertex."""
    n = len(adj)
    dist = [inf] * n
    settled = [False] * n
    dist[source] = 0
    for _ in range(n):
        u = min((x for x in range(n) if not settled[x]), key=dist.__getitem__)
        if dist[u] == inf:
            break  # everything left is unreachable
        settled[u] = True
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


def restore_path(parent, dist, target):
    if dist[target] == inf:
        return []
    path = []
    while target is not None:
        path.append(target)
        target = parent[target]
    return path[::-1]


def bellman_ford(adj, source):
    n = len(adj)
    dist = [inf] * n
    dist[source] = 0
    for _ in range(n - 1):
        for u in range(n):
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
    return dist


def brute_force(adj, source):
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


def main():
    roads = [[(1, 4), (2, 1)], [(3, 1)], [(1, 2), (3, 5), (4, 8)],
             [(4, 3), (5, 6)], [(5, 2)], []]
    dist, parent = dijkstra(roads, 0)
    assert dist == [0, 3, 1, 4, 7, 9]
    assert parent == [None, 2, 0, 1, 3, 4]
    assert restore_path(parent, dist, 5) == [0, 2, 1, 3, 4, 5]
    assert restore_path(parent, dist, 0) == [0]
    assert dijkstra_dense(roads, 0) == dist

    # Negative edges: rejected, and the true answers differ (§7).
    s, a, b, c = range(4)
    negative = [[(a, 2), (b, 5)], [(c, 1)], [(a, -10)], []]
    assert bellman_ford(negative, s) == [0, -5, 5, -4]  # Dijkstra would settle a at 2
    s, t, a = range(3)
    original = [[(t, 0), (a, 1)], [], [(t, -2)]]
    shifted = [[(v, w + 2) for v, w in row] for row in original]
    assert bellman_ford(original, s)[t] == -1 and bellman_ford(shifted, s)[t] == 2

    dist, parent = dijkstra([[(1, 7)], [], []], 0)
    assert dist == [0, 7, inf] and restore_path(parent, dist, 2) == []
    assert dijkstra([[(0, 0), (1, 0)], [(0, 0)]], 0)[0] == [0, 0]  # zero cycles
    try:
        dijkstra([[(1, -1)], []], 0)
    except ValueError:
        pass
    else:
        raise AssertionError("negative weight accepted")

    rng = random.Random(13)
    for _ in range(500):
        n = rng.randint(1, 7)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 14)):
            adj[rng.randrange(n)].append((rng.randrange(n), rng.randint(0, 9)))
        source = rng.randrange(n)
        dist, parent = dijkstra(adj, source)
        assert dist == brute_force(adj, source) == bellman_ford(adj, source)
        assert dist == dijkstra_dense(adj, source)
        for t in range(n):
            path = restore_path(parent, dist, t)
            if dist[t] < inf:
                cost = sum(min(w for x, w in adj[a] if x == b) for a, b in zip(path, path[1:]))
                assert path[0] == source and path[-1] == t and cost == dist[t]


if __name__ == "__main__":
    main()
```

There are at most `E` successful relaxations, hence at most `E + 1` heap entries; each push and pop costs O(log E). Since `log E ≤ 2 log V` for a graph without parallel edges, the heap bound is usually written **O((V + E) log V)**.

## 6. Why it is correct

We prove: **when a place `u` is popped and is not stale, `dist[u]` is its true shortest distance.**

Suppose not, and let `u` be the first place settled with a wrong value. Take a truly shortest route `P` from the source to `u`. The source is settled, and `u` was not yet settled when it was popped, so `P` has a first vertex `y` that is not settled at that moment, with a settled predecessor `x` right before it on `P`.

1. `x` was settled correctly (`u` is the first mistake), and when `x` was settled its edge `x → y` was relaxed. So `dist[y] ≤ (true distance to x) + w(x, y) =` the cost of `P` up to `y`.
2. The remaining part of `P` from `y` to `u` has nonnegative weights, so the cost of `P` up to `y` is at most the cost of all of `P`, which is the true distance to `u`.
3. The heap popped `u` rather than `y`, so `dist[u] ≤ dist[y]`.

Chaining: `dist[u] ≤ dist[y] ≤ true distance to u`. And `dist[u]` is the cost of an actual route, so it is at least the true distance. Hence equality, a contradiction.

Step 2 is the only place nonnegative weights are used. It is exactly what breaks next.

## 7. Negative edges break it

```text
        2
   s ───────→ a ───1───→ c
   │          ↑
   5         −10
   ↓          │
   b ─────────┘
```

Edges: `s→a = 2`, `s→b = 5`, `b→a = −10`, `a→c = 1`. True distances: `a = 5 − 10 = −5` via `b`, and `c = −4`.

Textbook Dijkstra, which never revisits a settled place:

| Round | Settle | Result |
|---:|---|---|
| 1 | `s` (0) | `a = 2`, `b = 5` |
| 2 | `a` (2) | `c = 3` — but `a` is not really at 2 |
| 3 | `c` (3) | nothing |
| 4 | `b` (5) | `b→a` gives −5, but `a` is already settled; `c` stays 3 |

Settling `a` at 2 was premature: a route through the farther place `b` came back cheaper. In the proof, step 2 failed: the rest of the route had negative weight.

What about the lazy-heap version, which re-pushes `a` when it improves? It does fix this example, because it re-expands `a`. But it is no longer Dijkstra's guarantee: with negative edges a place can be re-expanded many times, and there are graphs where this takes exponential time. And with a negative **cycle** it never stops. Use Bellman–Ford from [the next chapter](03-negative-weights-and-all-pairs.md) instead. The code above rejects negative weights with a `ValueError` for that reason.

**"Add a constant to make every weight nonnegative" does not work either.** Take `s→t = 0`, `s→a = 1`, `a→t = −2`. The best route to `t` is `s→a→t` with cost −1. Add 2 to every edge: `s→t = 2`, `s→a = 3`, `a→t = 0`. Now the direct edge (cost 2) beats `s→a→t` (cost 3). A route with `k` edges gains `2k`, so routes with more edges are penalized more. (Johnson's algorithm in chapter 3 fixes weights in a way that *does* preserve shortest routes.)

## 8. Practical details and summary

**Stop early for one target.** If only `dist[target]` is needed, return when `target` is popped and is not stale. Returning when it is first *pushed* is wrong: a better route may still be waiting (place 1 was first pushed at 4, true distance 3).

**Update parents only on strict improvement.** With `<=`, two places joined by a 0-weight edge in both directions can become each other's parents, and path reconstruction loops forever.

**Ties between non-comparable states.** The heap compares tuples element by element. If two entries have the same distance, Python compares the next field. Integers are fine; objects such as dictionaries are not comparable and raise `TypeError`. Insert a running counter: `(distance, counter, state)`.

**Many sources.** Seed the heap with every source at distance 0. This is the same as adding a virtual source with 0-weight edges to each of them.

**Distances *to* one target in a directed graph.** Reverse every edge and run from the target.

**All pairs on a sparse graph.** Run Dijkstra from every vertex: O(V (V + E) log V). For dense graphs, Floyd–Warshall in chapter 3 is simpler.

### Summary

```text
dist = [inf] * n; dist[s] = 0; heap = [(0, s)]
while heap:
    d, u = heappop(heap)
    if d != dist[u]: continue            # stale
    for v, w in adj[u]:                  # w >= 0 required
        if d + w < dist[v]:              # strict: parents never cycle
            dist[v] = d + w; parent[v] = u; heappush(heap, (dist[v], v))
```

| Version | Time | Extra space | Use when |
|---|---:|---:|---|
| Heap with lazy deletion | O((V + E) log E) | O(V + E) | Sparse graphs (most problems) |
| Array scan | O(V² + E) | O(V) | Dense graphs, `E` close to `V²` |

A popped, non-stale vertex is final because every unsettled route to it passes a vertex at least as far, and nonnegative edges only add.

## 9. Pitfalls and practice

1. Marking a place settled when it is pushed instead of when it is popped. A cheaper route may still be found.
2. Forgetting the stale check. Results stay correct, but stale entries re-scan edges, and the time bound is lost.
3. Running Dijkstra with negative edges, or "fixing" them by adding a constant to every weight.
4. Returning as soon as the target is discovered rather than when it is popped.
5. Updating parents on `<=`, which can create parent cycles through 0-weight edges.
6. Using `0` or `-1` as "unreachable". Use `inf`, so that `min` comparisons work and unreachable is never confused with distance 0.
7. Counting shortest routes when a cycle of 0-weight edges lies on them. There are then infinitely many shortest *walks*; decide whether the problem counts simple paths, or rule out 0-weight cycles first.

Practice: network delay time; cheapest route with path reconstruction; find the city with the smallest number of neighbors within a threshold distance; number of ways to arrive at destination (count shortest routes, as in chapter 1, inside Dijkstra); second minimum time to reach destination.

Next: [Negative Weights and All Pairs](03-negative-weights-and-all-pairs.md).
