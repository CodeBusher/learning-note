# Spanning Trees — Connecting Everything at Minimum Cost

## 1. A cabling problem

A company has four offices, numbered 0 to 3. An engineer has priced every cable that could be laid between two offices:

```text
        4
   0 ------- 1
   |       / |
 1 |    2 /  | 5
   |     /   |
   2 ------- 3
        8
```

| Cable | Offices | Cost |
|---|---|---:|
| `e0` | 0–1 | 4 |
| `e1` | 0–2 | 1 |
| `e2` | 1–2 | 2 |
| `e3` | 1–3 | 5 |
| `e4` | 2–3 | 8 |

A signal can travel through intermediate offices, so 0 and 3 only need *some* chain of cables between them. **Which cables should be laid so that every office can reach every other one, at the lowest total cost?**

"Take the three cheapest cables" gives `e1` (1), `e2` (2), `e0` (4). Office 3 is left out, and `e0` is wasted: 0 and 1 were already linked through 2. Swapping `e0` for `e3` (5) gives `1 + 2 + 5 = 8`, which reaches everyone. Is 8 the best?

## 2. Words for the problem

- The offices are **vertices** and the possible cables are **edges**. Each edge is **undirected** (a cable works both ways) and has a **weight** (its cost). Graphs are introduced in [Search and traversal](../01-search-and-traversal/README.md).
- A set of edges **connects** the graph if, using only those edges, every vertex can reach every other vertex.
- A **cycle** is a route that leaves a vertex and returns to it without reusing an edge. The cables `e0, e1, e2` form the cycle `0 → 1 → 2 → 0`.
- A **tree** is a set of edges that connects its vertices and contains no cycle.
- A **spanning tree** of a graph is a tree that uses *all* of the graph's vertices. "Spanning" means it reaches every vertex.
- A **minimum spanning tree** (MST) is a spanning tree whose total weight is as small as possible.

**Why must the cheapest connecting set be a tree?** Suppose your chosen cables contain a cycle. Remove any one cable on that cycle. Everything stays connected, because any route that used the removed cable can go the other way around the cycle instead. If cable costs are positive, removing one makes the total cheaper. So an optimal choice never contains a cycle, which means it is a tree.

When some weights are zero or negative, a cheapest *connected subgraph* might include extra edges (a negative cable pays you to lay it). The MST problem still asks for a tree, and every algorithm in this folder returns a tree regardless of signs. If a problem really wants "any connected set of edges", take every negative edge first, then build the MST on top.

### Three facts about trees that every later chapter uses

Take a tree on `V` vertices.

1. **It has exactly `V − 1` edges.** Start with `V` separate vertices, that is, `V` groups. Each edge of a tree joins two different groups (otherwise it would close a cycle), so each edge reduces the group count by one. To reach one group, you need exactly `V − 1` edges.
2. **There is exactly one route between any two vertices.** If there were two different routes, together they would contain a cycle.
3. **Adding any extra edge creates exactly one cycle, and removing any tree edge splits the tree into exactly two pieces.** The new edge `u–v` plus the unique tree route from `u` to `v` is the cycle. Removing an edge cuts the only route between its two sides.

Fact 1 gives a quick test: a set of `V − 1` edges that connects all `V` vertices is automatically a spanning tree. Fact 3 is the engine of every MST proof in [The Cut and Cycle Properties](02-cut-and-cycle-properties.md).

## 3. Brute force: try every set of `V − 1` edges

By fact 1, a spanning tree on four offices has exactly three cables. There are `C(5, 3) = 10` ways to choose 3 of the 5 cables. Check each one:

| Chosen cables | Edges | Connects all four? | Cost |
|---|---|---|---:|
| `e0 e1 e2` | 0–1, 0–2, 1–2 | No: cycle 0–1–2, office 3 unreached | — |
| `e0 e1 e3` | 0–1, 0–2, 1–3 | Yes | 10 |
| `e0 e1 e4` | 0–1, 0–2, 2–3 | Yes | 13 |
| `e0 e2 e3` | 0–1, 1–2, 1–3 | Yes | 11 |
| `e0 e2 e4` | 0–1, 1–2, 2–3 | Yes | 14 |
| `e0 e3 e4` | 0–1, 1–3, 2–3 | Yes | 17 |
| `e1 e2 e3` | 0–2, 1–2, 1–3 | Yes | **8** |
| `e1 e2 e4` | 0–2, 1–2, 2–3 | Yes | 11 |
| `e1 e3 e4` | 0–2, 1–3, 2–3 | Yes | 14 |
| `e2 e3 e4` | 1–2, 1–3, 2–3 | No: cycle 1–2–3, office 0 unreached | — |

Eight of the ten choices are spanning trees, and the cheapest costs 8. Our guess was right, and now we have proof.

The brute force translates directly into code. For each combination of `V − 1` edges, check connectivity with a small search; keep the cheapest.

```python
from itertools import combinations


def connects_all(n, chosen):
    """True if the undirected edges (u, v, w) in `chosen` connect vertices 0..n-1."""
    if n == 0:
        return True
    adj = [[] for _ in range(n)]
    for u, v, _ in chosen:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == n


def all_spanning_trees(n, edges):
    """Every spanning tree, as a tuple of edges (u, v, w)."""
    if n == 0:
        return [()]
    return [chosen for chosen in combinations(edges, n - 1)
            if connects_all(n, chosen)]


def brute_force_mst(n, edges):
    """Minimum total weight of a spanning tree, or None if none exists."""
    trees = all_spanning_trees(n, edges)
    if not trees:
        return None
    return min(sum(w for _, _, w in tree) for tree in trees)


def main():
    offices = [(0, 1, 4), (0, 2, 1), (1, 2, 2), (1, 3, 5), (2, 3, 8)]
    trees = all_spanning_trees(4, offices)
    assert len(trees) == 8
    assert sorted(sum(w for _, _, w in t) for t in trees) == [8, 10, 11, 11, 13, 14, 14, 17]
    assert brute_force_mst(4, offices) == 8

    # A graph that cannot be connected has no spanning tree.
    assert brute_force_mst(3, [(0, 1, 5)]) is None
    # One vertex: the empty tree, cost 0.
    assert brute_force_mst(1, []) == 0
    # Negative weights are allowed; the answer is still a tree.
    assert brute_force_mst(3, [(0, 1, -2), (1, 2, -3), (0, 2, -1)]) == -5

    # Cayley's formula: the complete graph on n vertices has n^(n-2) spanning trees.
    for n in range(2, 7):
        complete = [(u, v, 1) for u in range(n) for v in range(u + 1, n)]
        assert len(all_spanning_trees(n, complete)) == n ** (n - 2)


if __name__ == "__main__":
    main()
```

Time: `C(E, V − 1)` combinations, each checked in O(V) time. Space: O(V) per check.

## 4. Why brute force cannot scale

When every pair of `n` vertices has a possible cable (a **complete graph**), **Cayley's formula** says there are exactly `n^(n−2)` spanning trees. The script above confirms it up to `n = 6`.

| Offices `n` | Spanning trees of the complete graph |
|---:|---:|
| 4 | 16 |
| 6 | 1,296 |
| 10 | 100,000,000 |
| 20 | about 2.6 × 10²³ |
| 100 | about 10¹⁹⁶ |

At 20 offices, checking a billion trees per second would take about eight million years.

What replaces brute force is visible in the winning tree `{e1, e2, e3}`:

- It contains the two cheapest cables, `e1` (1) and `e2` (2).
- It avoids `e0` (4), the most expensive cable on the cycle `0–1–2`, and `e4` (8), the most expensive cable on the cycle `1–2–3`.

"The cheapest edge that does not close a cycle is safe" and "the most expensive edge on a cycle is never needed" are the cut and cycle properties, proved in [the next chapter](02-cut-and-cycle-properties.md). They let an algorithm decide edges one at a time.

## 5. Summary

| Fact | Use |
|---|---|
| The cheapest connecting set is a tree (positive weights) | MST algorithms return `V − 1` edges |
| A tree on `V` vertices has `V − 1` edges | Stop after `V − 1` accepted edges |
| Exactly one route joins two tree vertices | Bottleneck routes, path queries |
| Adding an edge closes one cycle; removing one splits the tree in two | Every exchange proof |
| `K_n` has `n^(n−2)` spanning trees | Brute force is only a test oracle |

## 6. Pitfalls and practice

1. Confusing "connect everything" with "shortest route from one place". An MST minimizes the **total** of the chosen edges, not the distance between any particular pair. [Variants and Spanning Forests](05-forests-and-variants.md#6-an-mst-is-not-a-shortest-path-tree) shows a concrete case where they differ.
2. Forgetting that a disconnected graph has **no** spanning tree. Report it, or build a spanning *forest* (one tree per piece) if the problem allows.
3. Counting edges instead of checking connectivity. `V − 1` edges is necessary for a spanning tree, not sufficient: `e0 e1 e2` has three edges and still misses office 3.
4. Assuming an MST is unique. With repeated weights there may be several trees of the same minimum cost; the minimum **cost** is unique.
5. Applying MST algorithms to directed graphs. "Every vertex reachable from a root along directed edges" is a different problem (minimum arborescence) and needs different algorithms.

Practice: by hand, list the spanning trees of a 4-cycle and of a triangle with a pendant vertex; count the spanning trees of the complete graph on 5 vertices and check against `5³ = 125`; on the office graph, change `e2` to cost 6 and find the new MST.

Next: [The Cut and Cycle Properties](02-cut-and-cycle-properties.md).
