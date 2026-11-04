# Variants and Spanning Forests — Beyond One Connected Tree

## 1. Spanning forests: when the graph is in pieces

Two islands, with no bridge between them:

```text
   island A                 island B
   0 ──2── 1                4 ──1── 5
   │     ╱                  │
   4   3                    7
   │ ╱                      │
   2                        6        3 (no edges at all)
```

Edges: `0–1=2`, `1–2=3`, `0–2=4`, `4–5=1`, `4–6=7`. Vertex 3 has no edges.

No spanning tree exists: nothing links island A to island B. But it is still natural to ask for the cheapest way to connect everything that *can* be connected. A **connected component** is a maximal group of vertices that can all reach each other. A **minimum spanning forest** is an MST inside every component, here `{0–1, 1–2}` (cost 5), `{4–5, 4–6}` (cost 8), and nothing for `{3}`. The total is 13 and there are 3 components.

**Kruskal needs no change.** Its loop never assumed connectivity: it keeps every edge that joins two different components. When the edges run out, the DSU holds one tree per component. The number of kept edges is `V − (number of components)`, so `components = V − len(chosen)`.

**Prim needs a restart.** One run from vertex 0 stops once island A is done. Loop over all vertices and start a new run from each vertex not yet reached.

Why is the forest optimal? Edges never join different components, so the forest splits into independent problems, one per component, and the cut property argument works inside each component unchanged.

```python
import random
from heapq import heappop, heappush
from itertools import combinations


def kruskal_forest(n, edges):
    """Returns (total, chosen, components) for undirected edges (u, v, w)."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, chosen = 0, []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
            total += w
            chosen.append((u, v, w))
    return total, chosen, n - len(chosen)


def prim_forest(n, edges):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    in_tree = [False] * n
    total, chosen, components = 0, [], 0
    for start in range(n):
        if in_tree[start]:
            continue
        components += 1  # restart: a new component
        heap = [(0, start, None)]
        while heap:
            w, u, parent = heappop(heap)
            if in_tree[u]:
                continue
            in_tree[u] = True
            if parent is not None:
                total += w
                chosen.append((parent, u, w))
            for v, cost in adj[u]:
                if not in_tree[v]:
                    heappush(heap, (cost, v, u))
    return total, chosen, components


def count_components(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v, _ in edges:
        parent[find(u)] = find(v)
    return sum(find(x) == x for x in range(n))


def brute_force_forest(n, edges):
    """Cheapest n - c edges that leave the same c components."""
    c = count_components(n, edges)
    costs = [sum(w for *_, w in chosen) for chosen in combinations(edges, n - c)
             if count_components(n, chosen) == c]
    return min(costs), c


def main():
    islands = [(0, 1, 2), (1, 2, 3), (0, 2, 4), (4, 5, 1), (4, 6, 7)]
    assert kruskal_forest(7, islands)[::2] == (13, 3)
    assert prim_forest(7, islands)[::2] == (13, 3)
    assert kruskal_forest(0, []) == (0, [], 0)
    assert prim_forest(3, []) == (0, [], 3)

    rng = random.Random(6)
    for _ in range(400):
        n = rng.randint(1, 7)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-2, 5))
                 for _ in range(rng.randint(0, 7))]
        expected = brute_force_forest(n, edges)
        k_total, k_chosen, k_count = kruskal_forest(n, edges)
        p_total, p_chosen, p_count = prim_forest(n, edges)
        assert (k_total, k_count) == expected == (p_total, p_count)
        assert len(k_chosen) == len(p_chosen) == n - k_count


if __name__ == "__main__":
    main()
```

Both run in O(V + E log E) time and O(V + E) space. A problem that requires one connected tree should check `components == 1` (for `V ≥ 1`) and report failure otherwise.

## 2. Connecting points: the graph you never build

**Problem.** Points sit on a grid. Connecting two points costs their **Manhattan distance**, `|x1 − x2| + |y1 − y2|`. Connect all points at minimum total cost.

Points: `P0=(0,0)`, `P1=(2,2)`, `P2=(3,10)`, `P3=(5,2)`, `P4=(7,0)`. The answer is 20.

Every pair of points is a possible edge, so with `n` points there are `n(n − 1)/2` edges. For 1,000 points that is about 500,000 edges, which Kruskal would build, store, and sort. **Dense Prim** (chapter 4, §2) needs only the `best` array and computes each distance when it needs it: O(n²) time, O(n) memory.

Dense Prim from `P0` adds `P1` (4), `P3` (3, via `P1`), `P4` (4, via `P3`), `P2` (9, via `P1`): total 20. The trace is the one in [Prim](04-prim.md#2-the-simple-version-one-best-value-per-vertex), with each `best` update computing a distance on the fly.

```python
import random
from itertools import combinations
from math import inf


def connect_points(points):
    """Minimum total Manhattan cost to connect all points (dense Prim)."""
    n = len(points)
    best = [inf] * n
    in_tree = [False] * n
    total = 0
    if n:
        best[0] = 0
    for _ in range(n):
        u = min((x for x in range(n) if not in_tree[x]), key=best.__getitem__)
        in_tree[u] = True
        total += best[u]
        ux, uy = points[u]
        for v in range(n):
            if not in_tree[v]:
                d = abs(ux - points[v][0]) + abs(uy - points[v][1])
                if d < best[v]:
                    best[v] = d
    return total


def brute_force_points(points):
    """Every set of n - 1 pair edges that connects all points."""
    n = len(points)
    edges = [(u, v, abs(points[u][0] - points[v][0]) + abs(points[u][1] - points[v][1]))
             for u in range(n) for v in range(u + 1, n)]
    best = None
    for chosen in combinations(edges, n - 1):
        seen, stack = {0}, [0]
        while stack:
            x = stack.pop()
            for u, v, _ in chosen:
                for a, b in ((u, v), (v, u)):
                    if a == x and b not in seen:
                        seen.add(b)
                        stack.append(b)
        if len(seen) == n:
            cost = sum(w for *_, w in chosen)
            best = cost if best is None or cost < best else best
    return best


def main():
    assert connect_points([(0, 0), (2, 2), (3, 10), (5, 2), (7, 0)]) == 20
    assert connect_points([]) == 0
    assert connect_points([(4, -1)]) == 0
    assert connect_points([(1, 1), (1, 1), (1, 1)]) == 0  # duplicate points

    rng = random.Random(7)
    for _ in range(300):
        pts = [(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(rng.randint(1, 5))]
        assert connect_points(pts) == brute_force_points(pts)


if __name__ == "__main__":
    main()
```

For very large inputs there is an O(n log n) method (**advanced**): for Manhattan distance, each point only needs an edge to its nearest neighbor in each of 8 angular regions, which leaves O(n) candidate edges for Kruskal. Finding those neighbors needs a sweep with a [Fenwick tree](../../04-range-queries/README.md).

## 3. A virtual vertex: wells and pipes

**Problem.** Each house `i` can get water by digging its own well for `well[i]`, or by laying a pipe to a house that already has water. Pipes `(a, b, cost)` work both ways. Supply every house at minimum total cost.

Example: `well = [1, 2, 2]`, pipes `0–1 = 1`, `1–2 = 1`. Dig at house 0 (cost 1) and lay both pipes (cost 2): total 3.

This is not yet an MST problem, because a well is attached to one house, not to an edge. **The trick:** add a **virtual vertex** `W`, "the water source", and an edge `W–i` with cost `well[i]` for every house. A house gets water exactly when it is connected to `W`. So the cheapest plan is an MST of the enlarged graph.

```text
          W
       ╱  │  ╲
     1    2    2          edges W–0, W–1, W–2 are the wells
    ╱     │     ╲
   0 ──1── 1 ──1── 2      the pipes
```

Kruskal on the enlarged graph: `0–1=1` keep, `1–2=1` keep, `W–0=1` keep. Three edges for four vertices, total 3. Every house is now connected to `W`.

```python
import random
from itertools import product


def min_cost_water(wells, pipes):
    """wells[i]: cost of a well at house i. pipes: (a, b, cost), 0-based."""
    n = len(wells)
    edges = [(n, i, cost) for i, cost in enumerate(wells)] + list(pipes)
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
            total += w
    return total


def brute_force_water(wells, pipes):
    """Try every set of wells and every set of pipes."""
    n = len(wells)
    best = None
    for dig in product((False, True), repeat=n):
        for lay in product((False, True), repeat=len(pipes)):
            parent = list(range(n))

            def find(x):
                while parent[x] != x:
                    x = parent[x]
                return x

            for (a, b, _), used in zip(pipes, lay):
                if used:
                    parent[find(a)] = find(b)
            watered_roots = {find(i) for i in range(n) if dig[i]}
            if all(find(i) in watered_roots for i in range(n)):
                cost = sum(c for c, d in zip(wells, dig) if d)
                cost += sum(p[2] for p, used in zip(pipes, lay) if used)
                best = cost if best is None else min(best, cost)
    return best


def main():
    assert min_cost_water([1, 2, 2], [(0, 1, 1), (1, 2, 1)]) == 3
    assert min_cost_water([1, 1], [(0, 1, 5)]) == 2  # two wells beat the pipe
    assert min_cost_water([], []) == 0

    rng = random.Random(8)
    for _ in range(200):
        n = rng.randint(1, 4)
        wells = [rng.randint(1, 6) for _ in range(n)]
        pipes = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 6))
                 for _ in range(rng.randint(0, 5))]
        assert min_cost_water(wells, pipes) == brute_force_water(wells, pipes)


if __name__ == "__main__":
    main()
```

Time O((V + E) log(V + E)) for `V` houses and `E` pipes. The same trick handles "some vertices may connect to a shared hub", "airports versus roads", and similar choices between a per-vertex cost and per-edge costs.

## 4. Minimum bottleneck: the largest edge on a route

**Problem.** Reuse the seven-site network from [Kruskal](03-kruskal.md), but read each weight as how steep that road is. A heavy truck must drive from site 0 to site 6, and its trip is only as hard as the **steepest** road it uses. Which route makes the largest edge weight as small as possible? The largest edge on a route is called its **bottleneck**.

```text
      0 ───7─── 1 ───8─── 2
      │       ╱ │         │
      5     9   7         5
      │   ╱     │         │
      3 ──15─── 4 ────────┘
      │       ╱ │
      6     8   9
      │   ╱     │
      5 ──11─── 6
```

Some routes from 0 to 6, by brute force:

| Route | Edge weights | Bottleneck |
|---|---|---:|
| 0–1–4–6 | 7, 7, 9 | **9** |
| 0–3–5–6 | 5, 6, 11 | 11 |
| 0–3–4–6 | 5, 15, 9 | 15 |
| 0–3–5–4–6 | 5, 6, 8, 9 | **9** |

The best bottleneck is 9. Now look at the MST from chapter 3: `{0–3, 2–4, 3–5, 0–1, 1–4, 4–6}`. Its unique route from 0 to 6 is `0–1–4–6`, with bottleneck 9.

> **For any two vertices, the route between them inside an MST has the smallest possible bottleneck among all routes in the graph.**

**Why.** Let `e` be the heaviest edge on the MST route from `u` to `v`. Removing `e` splits the MST into two pieces, with `u` on one side and `v` on the other. Any route from `u` to `v` in the graph must cross between the pieces using some edge `f`. Since `e` is a lightest edge across that cut (if `f` were lighter, swapping `e` for `f` would give a cheaper spanning tree), `w(f) ≥ w(e)`. So every route has a bottleneck of at least `w(e)`, and the MST route achieves exactly `w(e)`.

A related fact: an MST also minimizes the largest edge of the whole tree (it is a **minimum bottleneck spanning tree**). The converse is false: a tree can have the smallest largest edge while its total is not minimum.

The script computes the MST, then the bottleneck between every pair by walking the tree from each vertex (O(V²) total), and compares with a brute force over all simple routes.

```python
import random


def mst_adjacency(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree = [[] for _ in range(n)]
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
            tree[u].append((v, w))
            tree[v].append((u, w))
    return tree


def all_pairs_bottleneck(n, edges):
    """bottleneck[s][t] = smallest possible largest edge on an s-t route (None if none)."""
    tree = mst_adjacency(n, edges)
    table = [[None] * n for _ in range(n)]
    for s in range(n):
        table[s][s] = -float("inf")  # the empty route has no edges
        stack = [s]
        while stack:
            u = stack.pop()
            for v, w in tree[u]:
                if table[s][v] is None:
                    table[s][v] = max(table[s][u], w)
                    stack.append(v)
    return table


def brute_force_bottleneck(n, edges, s, t):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    best = None

    def dfs(u, seen, worst):
        nonlocal best
        if u == t:
            best = worst if best is None else min(best, worst)
            return
        for v, w in adj[u]:
            if v not in seen:
                seen.add(v)
                dfs(v, seen, max(worst, w))
                seen.remove(v)

    dfs(s, {s}, -float("inf"))
    return best


def main():
    sites = [(0, 1, 7), (0, 3, 5), (1, 2, 8), (1, 3, 9), (1, 4, 7), (2, 4, 5),
             (3, 4, 15), (3, 5, 6), (4, 5, 8), (4, 6, 9), (5, 6, 11)]
    table = all_pairs_bottleneck(7, sites)
    assert table[0][6] == 9 == brute_force_bottleneck(7, sites, 0, 6)
    assert table[3][4] == 7  # 3-0-1-4 beats the direct 15 edge

    rng = random.Random(9)
    for _ in range(300):
        n = rng.randint(1, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 6))
                 for _ in range(rng.randint(0, 9))]
        table = all_pairs_bottleneck(n, edges)
        for s in range(n):
            for t in range(n):
                assert table[s][t] == brute_force_bottleneck(n, edges, s, t)


if __name__ == "__main__":
    main()
```

Building the table takes O(E log E + V²) time and O(V²) space. For many queries on a large graph, answer each with binary lifting over the MST in O(log V) ([Rooting a tree and LCA](../05-trees-and-advanced/01-rooting-and-lca.md)), or offline with the Kruskal query sweep from chapter 3.

## 5. Second-best MST

**Problem.** Find the cheapest spanning tree whose cost is **strictly greater** than the MST cost. (Some problems instead want "the cheapest tree different from the MST", which may cost the same; the method below adapts easily.)

**Brute force.** List all spanning trees, sort their distinct costs, take the second. Exponential, but a fine checker.

**Key observation.** Some second-best tree differs from an MST `T` by a single **swap**: add one non-tree edge `e = u–v`, then remove one edge `f` on the tree route from `u` to `v` (the cycle that `e` closes). This is the classic exchange result (CLRS, problem 23-1); the intuition is that a tree two or more swaps away from `T` can be improved toward `T` one swap at a time without dropping to the minimum cost, so the cheapest non-minimum tree is reachable in one.

The swap changes the cost by `w(e) − w(f)`. To keep the change as small as possible but **positive**:

- If the heaviest edge on the route is lighter than `w(e)`, remove it.
- If the heaviest edge ties with `w(e)` (swapping gives the same cost, another MST), remove instead the heaviest edge that is **strictly lighter** than `w(e)`.

So for every pair of vertices we need the largest and the second-largest **distinct** edge weights on their tree route. A walk from each vertex fills that table in O(V²).

Example: square `0–1=1`, `1–2=2`, `2–3=3`, `3–0=4`, plus diagonal `0–2=5`. MST = `{0–1, 1–2, 2–3}`, cost 6.

| Non-tree edge | Tree route | Largest, second-largest | Best swap | New cost |
|---|---|---|---|---:|
| `3–0 = 4` | 3–2–1–0: 3, 2, 1 | 3, 2 | remove `2–3` (3) | 6 + 4 − 3 = **7** |
| `0–2 = 5` | 0–1–2: 1, 2 | 2, 1 | remove `1–2` (2) | 6 + 5 − 2 = 9 |

Second-best cost: 7.

```python
import random
from itertools import combinations

NEG = -float("inf")


def top_two(pair, w):
    """Add weight w to (largest, second largest distinct) and return the new pair."""
    first, second = pair
    if w > first:
        return w, first
    if first > w > second:
        return first, w
    return first, second


def second_best_mst(n, edges):
    """Smallest spanning-tree cost strictly above the MST cost, or None."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree = [[] for _ in range(n)]
    in_tree = [False] * len(edges)
    total, used = 0, 0
    for i in sorted(range(len(edges)), key=lambda i: edges[i][2]):
        u, v, w = edges[i]
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
            tree[u].append((v, w))
            tree[v].append((u, w))
            in_tree[i] = True
            total += w
            used += 1
    if used != n - 1:
        return None  # no spanning tree at all

    route = [[None] * n for _ in range(n)]
    for s in range(n):
        route[s][s] = (NEG, NEG)
        stack = [s]
        while stack:
            x = stack.pop()
            for y, w in tree[x]:
                if route[s][y] is None:
                    route[s][y] = top_two(route[s][x], w)
                    stack.append(y)

    best = None
    for i, (u, v, w) in enumerate(edges):
        if in_tree[i] or u == v:
            continue
        first, second = route[u][v]
        remove = first if first < w else second  # first <= w by the cycle property
        if remove != NEG:
            candidate = total + w - remove
            best = candidate if best is None else min(best, candidate)
    return best


def brute_force_second_best(n, edges):
    costs = set()
    for chosen in combinations(edges, n - 1):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x

        ok = True
        for u, v, _ in chosen:
            a, b = find(u), find(v)
            if a == b:
                ok = False
                break
            parent[a] = b
        if ok:
            costs.add(sum(w for _, _, w in chosen))
    ordered = sorted(costs)
    return ordered[1] if len(ordered) > 1 else None


def main():
    square = [(0, 1, 1), (1, 2, 2), (2, 3, 3), (3, 0, 4), (0, 2, 5)]
    assert second_best_mst(4, square) == 7
    assert second_best_mst(3, [(0, 1, 1), (1, 2, 1)]) is None   # only one tree
    assert second_best_mst(2, [(0, 1, 3), (0, 1, 3)]) is None   # two trees, same cost
    assert second_best_mst(2, [(0, 1, 3), (0, 1, 8)]) == 8
    assert second_best_mst(3, [(0, 1, 1)]) is None             # disconnected

    rng = random.Random(10)
    for _ in range(500):
        n = rng.randint(2, 6)
        edges = [(rng.randrange(v), v, rng.randint(1, 4)) for v in range(1, n)]
        edges += [(rng.randrange(n), rng.randrange(n), rng.randint(1, 4))
                  for _ in range(rng.randint(0, 5))]
        rng.shuffle(edges)
        assert second_best_mst(n, edges) == brute_force_second_best(n, edges)


if __name__ == "__main__":
    main()
```

Time O(E log E + V² + E), space O(V²). To handle large graphs, replace the V² table with binary lifting that stores the top two weights for every jump; each non-tree edge is then answered in O(log V), for O(E log V) overall. [Rooting a tree and LCA](../05-trees-and-advanced/01-rooting-and-lca.md) builds that jump table.

## 6. An MST is not a shortest-path tree

A **shortest-path tree** from a source `s` contains a shortest route from `s` to every vertex; [Dijkstra](../04-shortest-paths/02-dijkstra.md) builds one. Both are spanning trees, but they rarely coincide.

**Counterexample 1: the triangle.**

```text
        s
      ╱   ╲
     2     3
    ╱       ╲
   a ───2─── b
```

The MST takes the two cheapest edges, `s–a = 2` and `a–b = 2`, total 4. Inside it, the route from `s` to `b` is `s–a–b`, cost 4. But the direct edge `s–b` costs 3. So the MST does not contain the shortest route from `s` to `b`.

**Counterexample 2: the shortest-path tree can be much heavier.** A hub `0` with edges of cost 3 to vertices 1, 2 and 3, and a chain `1–2 = 1`, `2–3 = 1`:

| Tree | Edges | Total weight | Distance 0 → 3 inside the tree |
|---|---|---:|---:|
| MST | `1–2`, `2–3`, `0–1` | 5 | 5 |
| Shortest-path tree from 0 | `0–1`, `0–2`, `0–3` | 9 | 3 |

**They optimize different objectives**: the sum of the tree's edges versus each vertex's distance from one source. Both counterexamples are small enough to check by hand.

## 7. Summary: variants in one table

| Variant | Change to Kruskal or Prim | Why it works |
|---|---|---|
| Graph in pieces | Kruskal unchanged; Prim restarted per component | Components are independent problems (§1) |
| Implicit complete graph of points | Dense Prim, distances computed on demand | O(n²) time, O(n) memory (§2) |
| Per-vertex cost | Virtual vertex with an edge to every vertex | A vertex is served iff it reaches the virtual vertex (§3) |
| Minimize the largest edge on a route | Route inside the MST | MST path is a minimum bottleneck path (§4) |
| Second-best tree | Best single swap per non-tree edge | Some second-best tree is one swap from an MST (§5) |
| Maximum spanning tree | Sort in decreasing order | Cut property with "heaviest" |
| Some edges are mandatory | `union` them first, add their cost, then run Kruskal | The rest is an MST problem on the contracted graph |
| Some vertices are already connected | Pre-union them at cost 0 | Same as zero-cost edges |
| Minimize product of positive weights | Kruskal on `log(w)`, or directly on `w` | Sorting by `w` and by `log w` gives the same order |
| Only the order of weights matters | Any order-preserving change of weights | Kruskal only compares weights |
| Count how many MSTs exist (**advanced**) | Group equal weights; matrix-tree theorem per group | Each group's choices are independent |

The last row hints at a useful fact: Kruskal only ever *compares* weights. Any change that keeps their order (adding a constant to all, squaring nonnegative weights, taking logarithms of positive weights) leaves the MST edges unchanged. That is very different from shortest paths, where adding a constant to every edge favors routes with fewer edges.

## 8. Pitfalls and practice

1. Reporting a total for a disconnected graph as if it were a spanning tree. Return the forest **and** the component count, and let the caller decide.
2. Building all `n²/2` edges for a points problem when `n` is in the thousands. Dense Prim avoids the edge list.
3. Forgetting the virtual vertex when there is a per-vertex cost. Without it, the problem is not an MST problem at all.
4. Using an MST to answer "shortest route" questions. It answers "smallest largest edge" questions, not "smallest sum" questions.
5. In second-best MST, removing the heaviest route edge when it ties with the added edge. That produces another MST of the same cost, not a strictly larger one.
6. Thinking an order-preserving change of weights matters for MST. It does not; only the order of weights does.

Practice: number of connected components plus the forest cost; min cost to connect all points; optimize water distribution in a village; path with minimum maximum edge (also solvable by binary search plus BFS); second minimum spanning tree; find critical and pseudo-critical edges; connecting cities with a shared hub.

Back to the [minimum spanning trees overview](README.md).
