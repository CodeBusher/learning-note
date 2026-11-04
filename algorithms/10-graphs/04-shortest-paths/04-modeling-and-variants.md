# Modeling with State Graphs — Dijkstra Variants and A*

## 1. Network delay: the answer is a maximum of distances

**Problem.** A signal leaves server `k` at time 0. Directed links `(u, v, t)` deliver it from `u` to `v` after `t` milliseconds. When has **every** server received it? If some server never does, answer −1.

Example with servers 1 to 4 (numbered as in many problem statements), source 2, links `2→1 = 1`, `2→3 = 1`, `3→4 = 1`. Server 4 hears the signal at time 2, the last of all. Answer: 2.

**Observation.** Each server receives the signal at its shortest-path distance from `k`, since the signal follows every link at once. "Every server has it" happens at the largest of those distances. So: one [Dijkstra](02-dijkstra.md), then `max(dist)`.

```python
import random
from heapq import heappop, heappush
from math import inf


def network_delay(times, n, k):
    """times: (u, v, t) with servers numbered 1..n. Returns the delay or -1."""
    adj = [[] for _ in range(n + 1)]
    for u, v, t in times:
        adj[u].append((v, t))
    dist = [inf] * (n + 1)
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue
        for v, t in adj[u]:
            if d + t < dist[v]:
                dist[v] = d + t
                heappush(heap, (dist[v], v))
    worst = max(dist[1:])
    return -1 if worst == inf else worst


def brute_force(times, n, k):
    """Bellman-Ford style: relax every link n times."""
    dist = [inf] * (n + 1)
    dist[k] = 0
    for _ in range(n):
        for u, v, t in times:
            dist[v] = min(dist[v], dist[u] + t)
    worst = max(dist[1:])
    return -1 if worst == inf else worst


def main():
    assert network_delay([(2, 1, 1), (2, 3, 1), (3, 4, 1)], 4, 2) == 2
    assert network_delay([(1, 2, 1)], 2, 2) == -1
    assert network_delay([], 1, 1) == 0
    rng = random.Random(19)
    for _ in range(300):
        n = rng.randint(1, 6)
        times = [(rng.randint(1, n), rng.randint(1, n), rng.randint(0, 9))
                 for _ in range(rng.randint(0, 12))]
        k = rng.randint(1, n)
        assert network_delay(times, n, k) == brute_force(times, n, k)


if __name__ == "__main__":
    main()
```

Time O((V + E) log V). The only modeling step was "the answer is a function of all distances".

## 2. Most reliable route: multiply instead of add

**Problem.** An undirected network where each link `u–v` works with probability `p` (between 0 and 1), independently. Find the route from `start` to `end` with the **highest** probability that every link on it works. The probability of a route is the **product** of its links' probabilities.

Example: links `0–1: 0.5`, `1–2: 0.5`, `0–2: 0.2`. Route `0–1–2` succeeds with `0.5 × 0.5 = 0.25`, better than the direct `0.2`.

**Why Dijkstra still works.** Dijkstra's proof needed one thing: extending a route can never make it *better* (step 2 in [chapter 2, §6](02-dijkstra.md#6-why-it-is-correct)). Multiplying by a number in `[0, 1]` can never increase a probability. So the vertex with the **highest** tentative probability is final, and we use a max-heap (store negated values in `heapq`) and relax with `prob[u] × p > prob[v]`.

Trace from 0 (heap shows `(probability, vertex)`, highest first):

| Pop | Improvements | `prob[0..2]` after | Heap after |
|---|---|---|---|
| start | — | `1 0 0` | `(1, 0)` |
| `(1, 0)` | 1 → 0.5, 2 → 0.2 | `1 0.5 0.2` | `(0.5, 1) (0.2, 2)` |
| `(0.5, 1)` | 2 → 0.5 × 0.5 = 0.25 > 0.2 | `1 0.5 0.25` | `(0.25, 2) (0.2, 2)` |
| `(0.25, 2)` | target reached | final 0.25 | — |

An equivalent view: take `−log p` as an edge weight. It is nonnegative (since `p ≤ 1`), and maximizing a product of `p` is minimizing a sum of `−log p`. Plain Dijkstra then applies. Working with products directly avoids rounding errors from logarithms; a link with `p = 0` is never useful.

```python
import random
from fractions import Fraction
from heapq import heappop, heappush


def max_probability(n, links, start, end):
    """links: (u, v, p), undirected, 0 <= p <= 1. Best product of probabilities."""
    adj = [[] for _ in range(n)]
    for u, v, p in links:
        if not 0 <= p <= 1:
            raise ValueError("probability out of range")
        adj[u].append((v, p))
        adj[v].append((u, p))
    prob = [0] * n
    prob[start] = 1
    heap = [(-1, start)]
    while heap:
        neg, u = heappop(heap)
        if -neg != prob[u]:
            continue
        if u == end:
            return prob[u]
        for v, p in adj[u]:
            if prob[u] * p > prob[v]:
                prob[v] = prob[u] * p
                heappush(heap, (-prob[v], v))
    return prob[end]


def brute_force(n, links, start, end):
    best = 0

    def dfs(u, value, seen):
        nonlocal best
        if u == end:
            best = max(best, value)
            return
        for a, b, p in links:
            for x, y in ((a, b), (b, a)):
                if x == u and y not in seen:
                    dfs(y, value * p, seen | {y})

    dfs(start, 1, {start})
    return best


def main():
    half, fifth = Fraction(1, 2), Fraction(1, 5)
    links = [(0, 1, half), (1, 2, half), (0, 2, fifth)]
    assert max_probability(3, links, 0, 2) == Fraction(1, 4)
    assert max_probability(3, [(0, 1, half)], 0, 2) == 0
    assert max_probability(2, [], 1, 1) == 1
    assert abs(max_probability(3, [(0, 1, 0.5), (1, 2, 0.5), (0, 2, 0.2)], 0, 2) - 0.25) < 1e-12

    rng = random.Random(20)
    for _ in range(300):
        n = rng.randint(2, 6)
        links = [(rng.randrange(n), rng.randrange(n), Fraction(rng.randint(0, 4), 4))
                 for _ in range(rng.randint(0, 9))]
        s, t = rng.randrange(n), rng.randrange(n)
        assert max_probability(n, links, s, t) == brute_force(n, links, s, t)


if __name__ == "__main__":
    main()
```

The tests use exact fractions so that equal products compare equal; real inputs use floats.

## 3. Minimum effort: the cost of a route is its worst step

**Problem.** A hiker crosses a grid of heights from the top-left to the bottom-right cell, moving up, down, left or right. The **effort** of a route is the largest absolute height difference between two consecutive cells on it. Find the minimum effort.

```text
heights          differences along the best route
1 2 2            1 → 3 → 5 → 3 → 5: steps 2, 2, 2, 2
3 8 2            effort = 2
5 3 5
```

**Observation.** Replace `+` by `max` in relaxation: the candidate effort to `v` through `u` is `max(effort[u], |h[u] − h[v]|)`. Extending a route never lowers its maximum, so the same "smallest tentative value is final" argument holds. This is the **bottleneck** (minimax) version of Dijkstra. ([Variants and spanning forests](../03-minimum-spanning-trees/05-forests-and-variants.md#4-minimum-bottleneck-the-largest-edge-on-a-route) shows that a minimum spanning tree also answers minimax routes; here Dijkstra answers it for one pair.)

Trace on the grid, cells written `(row, col)`:

| Pop `(effort, cell)` | Improvements |
|---|---|
| `(0, (0,0))` | (0,1) → 1, (1,0) → 2 |
| `(1, (0,1))` | (0,2) → max(1, 0) = 1, (1,1) → max(1, 6) = 6 |
| `(1, (0,2))` | (1,2) → max(1, 0) = 1 |
| `(1, (1,2))` | (1,1) stays 6 (max(1, 6)), (2,2) → max(1, 3) = 3 |
| `(2, (1,0))` | (2,0) → max(2, 2) = 2, (1,1) → max(2, 5) = 5 < 6 |
| `(2, (2,0))` | (2,1) → max(2, 2) = 2 |
| `(2, (2,1))` | (2,2) → max(2, 2) = 2 < 3; (1,1) stays 5 |
| `(2, (2,2))` | target: answer 2 |

```python
import random
from collections import deque
from heapq import heappop, heappush


def minimum_effort(heights):
    rows, cols = len(heights), len(heights[0])
    best = [[float("inf")] * cols for _ in range(rows)]
    best[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        e, r, c = heappop(heap)
        if e != best[r][c]:
            continue
        if (r, c) == (rows - 1, cols - 1):
            return e
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols:
                cand = max(e, abs(heights[r][c] - heights[nr][nc]))
                if cand < best[nr][nc]:
                    best[nr][nc] = cand
                    heappush(heap, (cand, nr, nc))
    raise AssertionError("unreachable")


def by_binary_search(heights):
    """Independent check: binary search on the answer, BFS using steps <= limit."""
    rows, cols = len(heights), len(heights[0])

    def ok(limit):
        seen = {(0, 0)}
        queue = deque([(0, 0)])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen
                        and abs(heights[r][c] - heights[nr][nc]) <= limit):
                    seen.add((nr, nc))
                    queue.append((nr, nc))
        return (rows - 1, cols - 1) in seen

    lo, hi = 0, max(map(max, heights)) - min(map(min, heights))
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def main():
    assert minimum_effort([[1, 2, 2], [3, 8, 2], [5, 3, 5]]) == 2
    assert minimum_effort([[1, 2, 3], [3, 8, 4], [5, 3, 5]]) == 1
    assert minimum_effort([[7]]) == 0
    rng = random.Random(21)
    for _ in range(200):
        rows, cols = rng.randint(1, 3), rng.randint(1, 3)
        grid = [[rng.randint(1, 9) for _ in range(cols)] for _ in range(rows)]
        assert minimum_effort(grid) == by_binary_search(grid)
    for _ in range(30):
        rows, cols = rng.randint(1, 12), rng.randint(1, 12)
        grid = [[rng.randint(1, 50) for _ in range(cols)] for _ in range(rows)]
        assert minimum_effort(grid) == by_binary_search(grid)


if __name__ == "__main__":
    main()
```

Time O(RC log(RC)) for an `R × C` grid.

**The general rule.** Dijkstra works for any way of combining a route's cost with one more edge, as long as (a) extending a route never makes it better, and (b) if route A is at least as good as route B to the same vertex, extending both by the same edge keeps A at least as good. Sum of nonnegative weights, maximum of weights, and product of probabilities all qualify.

## 4. State-augmented graphs: cheapest flights within `k` stops

**Problem.** Directed flights `(from, to, price)`. Find the cheapest trip from `src` to `dst` with **at most `k` stops**, meaning at most `k + 1` flights. Return −1 if impossible.

```text
flights: 0 → 1 (1)   1 → 2 (1)   2 → 3 (1)   0 → 2 (5)
src = 0, dst = 3, k = 1  (at most 2 flights)
```

The cheapest trip overall is `0 → 1 → 2 → 3` for 3, but it takes 3 flights. With at most 2 flights, the best is `0 → 2 → 3` for 6.

### Why "one vertex per city" fails

Plain Dijkstra with a city as the vertex settles city 2 at price 2 (via 1, using 2 flights). From there, `2 → 3` would be a third flight: not allowed. Later the entry for city 2 at price 5 (1 flight) is popped, but city 2 is already settled at 2, so it is skipped as stale. Dijkstra answers −1, which is wrong.

The trouble: two arrivals at city 2 are **not interchangeable**. Arriving at price 2 with 0 flights left is worse for the future than arriving at price 5 with 1 flight left. A vertex must remember everything that affects what can happen next.

### Add the missing information to the vertex

Make a vertex the pair **`(city, flights used)`**. A flight `u → v` with price `p` becomes an edge from `(u, f)` to `(v, f + 1)` whenever `f + 1 ≤ k + 1`. This **state graph** has `V · (k + 2)` vertices, nonnegative weights, and plain Dijkstra on it is correct. The first time any state with city `dst` is popped, its price is the answer.

Trace, heap entries written `(price, city, flights)`:

| Pop | Pushes | Comment |
|---|---|---|
| `(0, 0, 0)` | `(1, 1, 1)`, `(5, 2, 1)` | |
| `(1, 1, 1)` | `(2, 2, 2)` | |
| `(2, 2, 2)` | none | `2 → 3` would be flight 3 > 2 |
| `(5, 2, 1)` | `(6, 3, 2)` | a *different state* from `(2, 2, 2)`, not stale |
| `(6, 3, 2)` | — | `dst` popped: answer 6 |

### Two correct methods and a brute force

The layered Bellman–Ford from chapter 3 also solves it: `k + 1` rounds, each reading only the previous round. Both are below, checked against brute force.

```python
import random
from heapq import heappop, heappush
from math import inf


def cheapest_flights_dijkstra(n, flights, src, dst, k):
    adj = [[] for _ in range(n)]
    for u, v, p in flights:
        adj[u].append((v, p))
    limit = k + 1
    best = {(src, 0): 0}
    heap = [(0, src, 0)]
    while heap:
        price, u, used = heappop(heap)
        if best.get((u, used)) != price:
            continue
        if u == dst:
            return price
        if used == limit:
            continue
        for v, p in adj[u]:
            state = (v, used + 1)
            if price + p < best.get(state, inf):
                best[state] = price + p
                heappush(heap, (price + p, v, used + 1))
    return -1


def cheapest_flights_layers(n, flights, src, dst, k):
    previous = [inf] * n
    previous[src] = 0
    for _ in range(k + 1):
        current = previous[:]
        for u, v, p in flights:
            if previous[u] + p < current[v]:
                current[v] = previous[u] + p
        previous = current
    return -1 if previous[dst] == inf else previous[dst]


def city_only_dijkstra_wrong(n, flights, src, dst, k):
    adj = [[] for _ in range(n)]
    for u, v, p in flights:
        adj[u].append((v, p))
    dist, used = [inf] * n, [0] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue
        for v, p in adj[u]:
            if used[u] + 1 <= k + 1 and d + p < dist[v]:
                dist[v], used[v] = d + p, used[u] + 1
                heappush(heap, (dist[v], v))
    return -1 if dist[dst] == inf else dist[dst]


def brute_force(n, flights, src, dst, k):
    best = inf

    def dfs(u, price, count, seen):
        nonlocal best
        if u == dst:
            best = min(best, price)
            return
        if count == k + 1:
            return
        for a, b, p in flights:
            if a == u and b not in seen:
                dfs(b, price + p, count + 1, seen | {b})

    dfs(src, 0, 0, {src})
    return -1 if best == inf else best


def main():
    flights = [(0, 1, 1), (1, 2, 1), (2, 3, 1), (0, 2, 5)]
    assert cheapest_flights_dijkstra(4, flights, 0, 3, 1) == 6
    assert cheapest_flights_layers(4, flights, 0, 3, 1) == 6
    assert city_only_dijkstra_wrong(4, flights, 0, 3, 1) == -1   # the trap
    assert cheapest_flights_dijkstra(4, flights, 0, 3, 2) == 3
    assert cheapest_flights_dijkstra(4, flights, 0, 3, 0) == -1
    assert cheapest_flights_dijkstra(2, [], 1, 1, 0) == 0

    rng = random.Random(22)
    for _ in range(500):
        n = rng.randint(2, 6)
        flights = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 9))
                   for _ in range(rng.randint(0, 12))]
        flights = [(u, v, p) for u, v, p in flights if u != v]
        src, dst, k = rng.randrange(n), rng.randrange(n), rng.randint(0, 4)
        expected = brute_force(n, flights, src, dst, k)
        assert cheapest_flights_dijkstra(n, flights, src, dst, k) == expected
        assert cheapest_flights_layers(n, flights, src, dst, k) == expected


if __name__ == "__main__":
    main()
```

| Method | Time | Space |
|---|---:|---:|
| Dijkstra on `(city, flights)` | O(k (V + E) log(kE)) | O(k V) states |
| Layered Bellman–Ford | O(k (V + E)) | O(V) |

### The modeling question to ask every time

> **If two different routes arrive at the same place, can the rest of the trip treat them the same?**

If not, the vertex is missing information. Add it to the state:

| Problem | Vertex must be | Why |
|---|---|---|
| Limited number of flights / edges | `(city, edges used)` | Remaining budget changes future options |
| Collect all keys before the exit | `(cell, set of keys)` as a bitmask | Doors open only with the right keys |
| One free coupon on any edge | `(vertex, coupon used?)` | The coupon can be spent only once |
| Fuel tank of capacity `C` | `(city, fuel left)` | Fuel limits the next legs |
| Moves alternate between two colors of edges | `(vertex, color of last edge)` | Next allowed edges depend on it |
| Arrival time matters modulo `m` (traffic lights) | `(vertex, time mod m)` | Waiting rules repeat every `m` |

The cost is a bigger graph: `V ×` (number of extra values). A state with 10 keys multiplies the graph by `2¹⁰ = 1024`. If the extra information is large, look for a smaller summary that still answers the question above.

## 5. A* search (bonus): Dijkstra with a sense of direction

Dijkstra expands vertices in order of distance from the source, in every direction equally. When there is one target and you can **estimate** the remaining distance, you can expand the promising vertices first.

**Idea.** Let `g(v)` be the best known cost from the source to `v` (Dijkstra's `dist`), and `h(v)` an estimate of the remaining cost from `v` to the target, called a **heuristic**. Pop vertices in order of

$$
f(v) = g(v) + h(v),
$$

an estimate of the total cost of the best route through `v`. With `h = 0`, this is exactly Dijkstra.

**When is it correct?** A heuristic is **admissible** if it never overestimates: `h(v) ≤` the true remaining cost. It is **consistent** if for every edge `u → v` of cost `w`, `h(u) ≤ w + h(v)` (the estimate drops by at most the edge you walk), and `h(target) = 0`. A consistent heuristic is admissible, and with it A* is Dijkstra on the reweighted edges `w' = w − h(u) + h(v) ≥ 0`, the same telescoping trick as Johnson's algorithm in chapter 3. So everything proved for Dijkstra carries over: the first time the target is popped, its `g` is optimal.

On a grid with unit-cost moves in four directions, the **Manhattan distance** `|r − r_t| + |c − c_t|` is consistent: one move changes it by at most 1.

### Trace: around a wall

Start `S = (2,0)`, target `T = (2,4)`, `#` is a wall:

```text
      col 0 1 2 3 4
row 0     . . . . .
row 1     . . # . .
row 2     S . # . T
row 3     . . # . .
row 4     . . . . .
```

Expanded cells in order, with ties in `f` broken by smaller `h`:

| Pops | Cells (`g`, `h`) | `f` | What happens |
|---|---|---:|---|
| 1–2 | (2,0) (0, 4), (2,1) (1, 3) | 4 | straight at the wall |
| 3–6 | (1,1) (2, 4), (3,1) (2, 4), (1,0) (1, 5), (3,0) (1, 5) | 6 | blocked; the estimate rises by 2 |
| 7–12 | (0,1) (0,2) (0,3) (0,4) (1,4) (2,4), `g` = 3 … 8 | 8 | over the top of the wall to `T` |

A* runs straight at the wall (`f = 4`), finds the way blocked, and the `f` values rise to 6 and then 8 as it learns the detour is needed. It expands **12** cells; Dijkstra expands **22** on the same grid before popping the target. Both report the shortest distance 8.

```python
import random
from heapq import heappop, heappush


def a_star(grid, start, target):
    """Fewest moves on a grid of '.' and '#', or -1. Manhattan heuristic."""
    rows, cols = len(grid), len(grid[0])

    def h(cell):
        return abs(cell[0] - target[0]) + abs(cell[1] - target[1])

    g = {start: 0}
    heap = [(h(start), h(start), start)]
    expanded = 0
    while heap:
        f, hv, cell = heappop(heap)
        if f - hv != g[cell]:
            continue  # stale
        expanded += 1
        if cell == target:
            return g[cell], expanded
        r, c = cell
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            nr, nc = nxt
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == ".":
                cand = g[cell] + 1
                if cand < g.get(nxt, float("inf")):
                    g[nxt] = cand
                    heappush(heap, (cand + h(nxt), h(nxt), nxt))
    return -1, expanded


def bfs(grid, start, target):
    rows, cols = len(grid), len(grid[0])
    dist = {start: 0}
    frontier = [start]
    while frontier:
        nxt_frontier = []
        for r, c in frontier:
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "."
                        and (nr, nc) not in dist):
                    dist[nr, nc] = dist[r, c] + 1
                    nxt_frontier.append((nr, nc))
        frontier = nxt_frontier
    return dist.get(target, -1)


def main():
    grid = [".....", "..#..", "..#..", "..#..", "....."]
    assert a_star(grid, (2, 0), (2, 4)) == (8, 12)
    assert a_star([".#.", ".#.", ".#."], (0, 0), (0, 2))[0] == -1
    assert a_star(["."], (0, 0), (0, 0)) == (0, 1)

    rng = random.Random(23)
    for _ in range(300):
        rows, cols = rng.randint(1, 8), rng.randint(1, 8)
        grid = ["".join("#" if rng.random() < 0.3 else "." for _ in range(cols))
                for _ in range(rows)]
        cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == "."]
        if not cells:
            continue
        s, t = rng.choice(cells), rng.choice(cells)
        assert a_star(grid, s, t)[0] == bfs(grid, s, t)


if __name__ == "__main__":
    main()
```

**Cautions.** An inadmissible heuristic (one that overestimates) can make A* return a longer route. An admissible but inconsistent one is still correct if settled vertices may be reopened, but the code above, which treats each popped vertex like Dijkstra does, relies on consistency. The worst case is no better than Dijkstra; the gain depends on how informative `h` is. With diagonal moves, teleporters, or varying costs, the Manhattan distance may stop being admissible, so re-check it. For the wider theory of informed search (greedy best-first, IDA*, heuristic design), see the [AI search notes](../../../Foundation%20of%20AI/01-search.md).

## 6. Summary

| Problem shape | Vertex | Combine rule | Algorithm |
|---|---|---|---|
| Time until everyone is reached | place | `d + w` | Dijkstra, then `max(dist)` |
| Most reliable route | place | `p · q`, maximize | Dijkstra with a max-heap (or `−log p`) |
| Easiest route (worst step) | place | `max(e, step)` | Bottleneck Dijkstra |
| Budget of edges, fuel, keys, coupons | `(place, extra info)` | `d + w` | Dijkstra or BFS on the state graph |
| One target, good lower bound on remaining cost | place | `d + w`, ordered by `g + h` | A* with a consistent heuristic |

Check rules (a) and (b) of §3 before using a new combine rule, and the modeling question of §4 before choosing a vertex.

## 7. Pitfalls and practice

1. Using a city as the vertex when the problem has a budget (stops, fuel, coupons). Two arrivals with different budgets are different states.
2. Running Dijkstra with a cost rule that can *improve* when a route is extended, for example a product of numbers greater than 1, or a widest-route problem run with a min-heap instead of a max-heap. Check rule (a) of §3 first.
3. In the probability problem, using a min-heap without negating, which pops the *worst* route first.
4. Forgetting that the layered method must copy the previous round (chapter 3, §4).
5. Counting stops as flights. "At most `k` stops" means at most `k + 1` flights.
6. Using an A* heuristic that overestimates. It then returns non-optimal routes without any warning.
7. Letting the state space explode. Estimate `V × (extra values)` before coding.

Practice: network delay time; path with maximum probability; path with minimum effort; swim in rising water (minimax on a grid); cheapest flights within `k` stops; shortest path to get all keys (state with a key bitmask); shortest path in a grid with obstacles elimination (state with remaining eliminations); sliding puzzle with A*.

Back to the [shortest paths overview](README.md).
