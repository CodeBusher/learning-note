# Kruskal's Algorithm — Cheapest Edge First, Skip Cycles

## 1. The problem and the greedy idea

Seven sites, numbered 0 to 6, need to be linked by fiber. The possible links and their costs:

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

| Edge | Cost | Edge | Cost | Edge | Cost |
|---|---:|---|---:|---|---:|
| 0–1 | 7 | 1–4 | 7 | 3–5 | 6 |
| 0–3 | 5 | 2–4 | 5 | 4–5 | 8 |
| 1–2 | 8 | 3–4 | 15 | 4–6 | 9 |
| 1–3 | 9 | | | 5–6 | 11 |

There are 11 edges and a spanning tree needs 6, so brute force would examine `C(11, 6) = 462` subsets. That is fine for seven sites and hopeless for seven thousand.

**The greedy idea.** Sort the edges by cost. Walk through them in that order. Keep an edge if its two endpoints are not yet connected by the edges kept so far; otherwise skip it, because it would close a cycle. Stop after `V − 1` edges. Each decision is one of the two facts from [The Cut and Cycle Properties](02-cut-and-cycle-properties.md), as §5 proves.

## 2. Trace

Sorted order (ties broken by endpoint, which does not change the total): `0–3=5`, `2–4=5`, `3–5=6`, `0–1=7`, `1–4=7`, `1–2=8`, `4–5=8`, `1–3=9`, `4–6=9`, `5–6=11`, `3–4=15`.

The "components" column lists the groups of sites already linked to each other by kept edges.

| Step | Edge | Endpoints already connected? | Action | Components after the step | Total |
|---:|---|---|---|---|---:|
| 0 | — | — | start | `{0} {1} {2} {3} {4} {5} {6}` | 0 |
| 1 | 0–3 = 5 | no | keep | `{0,3} {1} {2} {4} {5} {6}` | 5 |
| 2 | 2–4 = 5 | no | keep | `{0,3} {2,4} {1} {5} {6}` | 10 |
| 3 | 3–5 = 6 | no | keep | `{0,3,5} {2,4} {1} {6}` | 16 |
| 4 | 0–1 = 7 | no | keep | `{0,1,3,5} {2,4} {6}` | 23 |
| 5 | 1–4 = 7 | no | keep | `{0,1,2,3,4,5} {6}` | 30 |
| 6 | 1–2 = 8 | yes, via 1–4–2 | skip | unchanged | 30 |
| 7 | 4–5 = 8 | yes, via 4–1–0–3–5 | skip | unchanged | 30 |
| 8 | 1–3 = 9 | yes, via 1–0–3 | skip | unchanged | 30 |
| 9 | 4–6 = 9 | no | keep | `{0,1,2,3,4,5,6}` | 39 |

After step 9 we have kept 6 = `V − 1` edges, so the tree is complete and the last two edges are never examined. The MST is `{0–3, 2–4, 3–5, 0–1, 1–4, 4–6}` with cost **39**.

Each skipped edge is the most expensive edge on the cycle it would have closed: `1–2=8` closes `1–4–2` (costs 7, 5, 8). That is the cycle property, applied automatically.

## 3. "Already connected?" in near-constant time

Step 7 asked whether 4 and 5 were connected. Searching the kept edges each time would cost O(V) per edge. A **disjoint set union** (DSU) answers it in near-constant time. [Disjoint Set Union](../02-connectivity-and-ordering/01-disjoint-set-union.md) builds it from scratch; this is the part Kruskal uses.

A DSU stores every component as a little tree of vertices. `parent[x]` points toward the component's **root** (a representative vertex), and the root points to itself.

- `find(x)` follows `parent` pointers up to the root. Two vertices are in the same component exactly when they have the same root.
- `union(a, b)` finds both roots; if they differ, it points one root at the other.

Two tricks keep the trees shallow. **Union by size** points the smaller component's root at the larger one's. **Path halving** makes each visited vertex skip to its grandparent during `find`. Together they make each operation take O(α(V)) amortized time, where α is the inverse Ackermann function, which is at most 4 for any input that fits in a computer.

In step 5 of the trace, `union(1, 4)` finds root 0 for vertex 1 (component of size 4) and root 2 for vertex 4 (size 2), and attaches 2 under 0. Vertex 4 still points to 2; the next `find(4)` walks `4 → 2 → 0`, and path halving shortens it to `4 → 0`.

## 4. Full implementation

`kruskal` returns `(total, chosen_edges)` for a connected graph and `None` when no spanning tree exists. The test compares it with the brute force from [chapter 1](01-spanning-trees.md) on random small graphs that include negative weights, ties, parallel edges and self-loops.

```python
import random
from itertools import combinations


class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        """Merge the components of a and b. Returns False if already merged."""
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        self.components -= 1
        return True


def kruskal(n, edges):
    """Undirected edges (u, v, w). Returns (total, chosen) or None if disconnected."""
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge endpoint out of range")
    dsu = DisjointSet(n)
    chosen, total = [], 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if dsu.union(u, v):
            chosen.append((u, v, w))
            total += w
            if len(chosen) == n - 1:
                break
    if n > 0 and dsu.components != 1:
        return None
    return total, chosen


def brute_force_mst(n, edges):
    def connects_all(chosen):
        dsu = DisjointSet(n)
        for u, v, _ in chosen:
            dsu.union(u, v)
        return dsu.components <= 1

    costs = [sum(w for _, _, w in c) for c in combinations(edges, max(n - 1, 0))
             if connects_all(c)]
    return min(costs) if costs else None


def is_spanning_tree(n, chosen):
    dsu = DisjointSet(n)
    return len(chosen) == max(n - 1, 0) and all(dsu.union(u, v) for u, v, _ in chosen)


def main():
    sites = [(0, 1, 7), (0, 3, 5), (1, 2, 8), (1, 3, 9), (1, 4, 7), (2, 4, 5),
             (3, 4, 15), (3, 5, 6), (4, 5, 8), (4, 6, 9), (5, 6, 11)]
    total, chosen = kruskal(7, sites)
    assert total == 39
    assert chosen == [(0, 3, 5), (2, 4, 5), (3, 5, 6), (0, 1, 7), (1, 4, 7), (4, 6, 9)]

    assert kruskal(0, []) == (0, [])
    assert kruskal(1, [(0, 0, -5)]) == (0, [])          # a self-loop is never used
    assert kruskal(2, [(0, 1, 9), (0, 1, 3)]) == (3, [(0, 1, 3)])  # parallel edges
    assert kruskal(3, [(0, 1, 1)]) is None             # vertex 2 unreachable
    try:
        kruskal(2, [(0, 2, 1)])
    except ValueError:
        pass
    else:
        raise AssertionError("bad endpoint accepted")

    rng = random.Random(3)
    for _ in range(500):
        n = rng.randint(1, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 5))
                 for _ in range(rng.randint(0, 8))]
        result = kruskal(n, edges)
        expected = brute_force_mst(n, edges)
        if expected is None:
            assert result is None
        else:
            total, chosen = result
            assert total == expected and is_spanning_tree(n, chosen)


if __name__ == "__main__":
    main()
```

Time: sorting takes O(E log E); the DSU work is O(E α(V)). Total **O(E log E)**, which is the same as O(E log V) for a graph without parallel edges, since then `E < V²`. Space: O(V) for the DSU plus O(E) for the sorted copy.

## 5. Why it is correct

Kruskal makes two kinds of decisions, and chapter 2 justifies each.

**Keeping an edge `e = u–v`.** At that moment `u` and `v` are in different components. Let `S` be `u`'s component. No kept edge crosses the cut `S` versus the rest, because kept edges only run inside components. Any edge crossing that cut that is *cheaper* than `e` was examined earlier; at that earlier moment its endpoints were also in different components (components only grow, so if they are apart now they were apart then), so Kruskal would have kept it, and then it would lie inside a component now, not across the cut. So no cheaper crossing edge exists: `e` is a lightest edge crossing the cut. The safe-edge rule says the kept edges remain part of some MST.

**Skipping an edge.** Its endpoints are already joined by kept edges, all of which were examined earlier and so cost no more. The skipped edge is a heaviest edge on the cycle it would close, and an MST never needs it.

By induction, the kept edges are always part of some MST. At the end they form a spanning tree (if the graph is connected), so they *are* an MST.

## 6. Variants built on the same loop

### Maximum spanning tree

Sort in **decreasing** order and keep the same rule. The cut property with "heaviest" in place of "lightest" has the same proof. (Equivalently, negate every weight.)

### Critical and pseudo-critical edges

Chapter 2 classified edges with connectivity tests. The usual Kruskal-based method compares MST costs instead:

- `e` is **critical** (in every MST) if deleting it makes the MST cost go up, or disconnects the graph.
- `e` is **pseudo-critical** (in some MSTs but not all) if it is not critical, and forcing it into the tree first still achieves the original MST cost.

Forcing works by calling `union` on `e`'s endpoints before the main loop and adding its weight to the total. Each test is a full Kruskal run, so the whole classification is O(E² α(V)) after one sort.

### Offline "is there a route using only cheap edges?"

Given queries "can `p` reach `q` using only edges of cost below `limit`?", sort the queries by `limit` and sweep the sorted edges once, uniting endpoints of every edge cheaper than the current query's limit. Then answer the query with `find(p) == find(q)`. This is Kruskal's loop with queries interleaved: O((E + Q) log(E + Q)) in total instead of one search per query.

```python
import random


def make_find(n):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        parent[a] = b
        return a != b

    return find, union


def mst_cost(n, edges, skip=None, force=None):
    """Kruskal on `edges` minus index `skip`, with index `force` taken first."""
    find, union = make_find(n)
    total, used = 0, 0
    if force is not None:
        u, v, w = edges[force]
        if not union(u, v):
            return None  # a forced self-loop cannot be in a tree
        total, used = w, 1
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    for i in order:
        if i == skip or i == force:
            continue
        u, v, w = edges[i]
        if union(u, v):
            total += w
            used += 1
    return total if used == n - 1 else None


def classify_edges(n, edges):
    """Returns (critical, pseudo_critical) index lists for a connected graph."""
    best = mst_cost(n, edges)
    if best is None:
        raise ValueError("graph must be connected")
    critical, pseudo = [], []
    for i in range(len(edges)):
        without = mst_cost(n, edges, skip=i)
        if without is None or without > best:
            critical.append(i)
        elif mst_cost(n, edges, force=i) == best:
            pseudo.append(i)
    return critical, pseudo


def limited_routes(n, edges, queries):
    """queries: (p, q, limit). Answer: can p reach q using edges with w < limit?"""
    find, union = make_find(n)
    edges = sorted(edges, key=lambda e: e[2])
    answers = [False] * len(queries)
    j = 0
    for k in sorted(range(len(queries)), key=lambda k: queries[k][2]):
        p, q, limit = queries[k]
        while j < len(edges) and edges[j][2] < limit:
            union(edges[j][0], edges[j][1])
            j += 1
        answers[k] = find(p) == find(q)
    return answers


def reachable_brute(n, edges, p, q, limit):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        if w < limit:
            adj[u].append(v)
            adj[v].append(u)
    seen, stack = {p}, [p]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return q in seen


def in_some_mst(n, edges, i):  # chapter 2's connectivity test
    u, v, w = edges[i]
    return not reachable_brute(n, edges, u, v, w)


def in_every_mst(n, edges, i):
    u, v, w = edges[i]
    others = [e for j, e in enumerate(edges) if j != i]
    return not reachable_brute(n, others, u, v, w + 1)  # weights are integers


def main():
    edges = [(0, 1, 1), (1, 2, 1), (2, 3, 2), (0, 3, 2), (0, 4, 3), (3, 4, 3), (1, 4, 6)]
    assert classify_edges(5, edges) == ([0, 1], [2, 3, 4, 5])

    rng = random.Random(4)
    for _ in range(300):
        n = rng.randint(2, 6)
        tree = [(rng.randrange(v), v, rng.randint(1, 3)) for v in range(1, n)]
        extra = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 3))
                 for _ in range(rng.randint(0, 5))]
        graph = tree + extra
        rng.shuffle(graph)
        critical, pseudo = classify_edges(n, graph)
        for i in range(len(graph)):
            assert (i in critical) == in_every_mst(n, graph, i)
            assert (i in critical or i in pseudo) == in_some_mst(n, graph, i)

        queries = [(rng.randrange(n), rng.randrange(n), rng.randint(0, 5)) for _ in range(6)]
        expected = [reachable_brute(n, graph, p, q, lim) for p, q, lim in queries]
        assert limited_routes(n, graph, queries) == expected


if __name__ == "__main__":
    main()
```

## 7. Summary

```text
sort edges by weight                       # O(E log E)
dsu = V singletons
for (u, v, w) in sorted order:
    if find(u) != find(v):                 # different components: lightest edge across that cut
        union(u, v); keep (u, v, w)
    # else: heaviest on the cycle it would close, skip
connected  <=>  kept V - 1 edges
```

## 8. Pitfalls and practice

1. Sorting by the wrong field. Edge lists come as `(u, v, w)` or `(w, u, v)`; sort by the weight.
2. Using the DSU root as a tree edge. The root is only a label for a component. Store the actual graph edge `(u, v, w)` you accepted.
3. Returning a cost for a disconnected graph. If fewer than `V − 1` edges were kept, there is no spanning tree; say so.
4. Forgetting that equal weights allow several MSTs. Tests should compare **costs** and check that the output is a spanning tree, not compare edge lists.
5. Building all `V²` edges of a complete graph when `V` is large. Kruskal then spends O(V² log V); dense Prim in [the next chapter](04-prim.md) does O(V²) without storing the edges.
6. Forgetting validation of vertex IDs. A bad ID usually shows up as an `IndexError` deep inside `find`.

Practice: connecting cities with minimum cost; redundant connection (the first edge that closes a cycle); find critical and pseudo-critical edges in a minimum spanning tree; checking existence of edge-length-limited paths; the maximum spanning tree of a graph.

Next: [Prim's Algorithm](04-prim.md).
