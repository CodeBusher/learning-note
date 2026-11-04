# Prim's Algorithm — Grow One Tree Outward

## 1. The idea on the fiber network

[Kruskal](03-kruskal.md) grows many small trees and merges them. Prim grows **one** tree from a starting vertex. Same seven sites:

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

Start with the tree containing only site 0. Look at every edge with exactly one endpoint in the tree. Take the cheapest one; it brings in a new vertex. Repeat until every vertex is in.

The edges with exactly one endpoint in the tree are precisely the edges crossing the cut "tree versus not yet in the tree". No chosen edge crosses that cut, since chosen edges lie inside the tree. So by the safe-edge rule, the cheapest crossing edge is always safe.

## 2. The simple version: one `best` value per vertex

Keep, for every vertex `v` not yet in the tree:

- `best[v]`: the cost of the cheapest edge from the tree to `v` found so far (`inf` if none);
- `via[v]`: the tree vertex at the other end of that edge.

Each step picks the outside vertex with the smallest `best`, adds it to the tree, and then looks at its edges: for each outside neighbor `x`, if the edge cost is less than `best[x]`, update `best[x]` and `via[x]`.

**Invariant:** before each step, `best[v]` is the cheapest edge between the current tree and `v`.

Trace from site 0. A ✓ marks vertices already in the tree (their `best` is frozen at the edge that brought them in).

| Step | Add vertex (edge used) | `best[0..6]` after scanning the new vertex's edges | Total |
|---:|---|---|---:|
| 1 | 0 (start) | `0✓ 7 ∞ 5 ∞ ∞ ∞` | 0 |
| 2 | 3 via 0–3 = 5 | `0✓ 7 ∞ 5✓ 15 6 ∞` | 5 |
| 3 | 5 via 3–5 = 6 | `0✓ 7 ∞ 5✓ 8 6✓ 11` | 11 |
| 4 | 1 via 0–1 = 7 | `0✓ 7✓ 8 5✓ 7 6✓ 11` | 18 |
| 5 | 4 via 1–4 = 7 | `0✓ 7✓ 5 5✓ 7✓ 6✓ 9` | 25 |
| 6 | 2 via 4–2 = 5 | `0✓ 7✓ 5✓ 5✓ 7✓ 6✓ 9` | 30 |
| 7 | 6 via 4–6 = 9 | all ✓ | 39 |

Follow vertex 4's column: it starts at `∞`, drops to 15 when 3 joins (edge 3–4), to 8 when 5 joins (edge 5–4), and to 7 when 1 joins (edge 1–4). Each drop is a cheaper way into 4 from the growing tree.

The total is **39**, the same as Kruskal, with the same six edges. The order is different: Prim takes `4–2 = 5` *after* `1–4 = 7`, because edge `4–2` does not cross the cut until 4 is in the tree. Prim orders edges by when they become available, not globally.

Each step scans all `V` vertices to find the smallest `best`, and every edge is examined once (from each end), so this version runs in **O(V² + E)** time. For a **dense** graph, where `E` is close to `V²`, that is optimal: any algorithm must at least read the edges.

## 3. The heap version for sparse graphs

When `E` is much smaller than `V²`, scanning all `V` vertices per step is wasteful. Store candidate edges in a **min-heap** (a priority queue that hands back its smallest item; see [Heaps and priority queues](../../07-heaps-and-priority-queues/README.md)) of `(cost, vertex, parent)` and pop the cheapest.

Python's heap cannot lower a stored priority. So when a cheaper edge to `x` appears, push a new entry and leave the old one in place. When an entry is popped for a vertex already in the tree, it is **stale**: skip it. This is called **lazy deletion**.

Trace from site 0, writing entries as `(cost, vertex, parent)`. The heap is shown sorted for readability.

| Pop | Result | Heap after pushing the new vertex's edges |
|---|---|---|
| `(0, 0, —)` | add 0 | `(5,3,0) (7,1,0)` |
| `(5, 3, 0)` | add 3 via 0–3 | `(6,5,3) (7,1,0) (9,1,3) (15,4,3)` |
| `(6, 5, 3)` | add 5 via 3–5 | `(7,1,0) (8,4,5) (9,1,3) (11,6,5) (15,4,3)` |
| `(7, 1, 0)` | add 1 via 0–1 | `(7,4,1) (8,2,1) (8,4,5) (9,1,3) (11,6,5) (15,4,3)` |
| `(7, 4, 1)` | add 4 via 1–4 | `(5,2,4) (8,2,1) (8,4,5) (9,1,3) (9,6,4) (11,6,5) (15,4,3)` |
| `(5, 2, 4)` | add 2 via 4–2 | `(8,2,1) (8,4,5) (9,1,3) (9,6,4) (11,6,5) (15,4,3)` |
| `(8,2,1)`, `(8,4,5)`, `(9,1,3)` | stale: 2, 4, 1 already in the tree | unchanged |
| `(9, 6, 4)` | add 6 via 4–6 | `(11,6,5) (15,4,3)` |

The code can stop as soon as all `V` vertices are in; the two remaining entries are stale anyway.

Every edge is pushed at most twice (once from each end), so the heap holds O(E) entries and each push or pop costs O(log E). Total **O(E log E)**, usually written O(E log V).

## 4. Full implementation

Both versions return `(total, chosen_edges)` or `None` for a disconnected graph, and are tested against brute force.

```python
import random
from heapq import heappop, heappush
from itertools import combinations
from math import inf


def adjacency(n, edges):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge endpoint out of range")
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj


def prim_dense(n, edges):
    """O(V^2 + E) Prim. Undirected edges (u, v, w)."""
    adj = adjacency(n, edges)
    best = [inf] * n
    via = [None] * n
    in_tree = [False] * n
    chosen, total = [], 0
    if n:
        best[0] = 0
    for _ in range(n):
        u = -1
        for x in range(n):
            if not in_tree[x] and (u == -1 or best[x] < best[u]):
                u = x
        if best[u] == inf:
            return None  # the rest of the graph is unreachable
        in_tree[u] = True
        if via[u] is not None:
            chosen.append((via[u], u, best[u]))
            total += best[u]
        for v, w in adj[u]:
            if not in_tree[v] and w < best[v]:
                best[v] = w
                via[v] = u
    return total, chosen


def prim_heap(n, edges):
    """O(E log E) Prim with a lazy min-heap."""
    adj = adjacency(n, edges)
    if n == 0:
        return 0, []
    in_tree = [False] * n
    chosen, total, added = [], 0, 0
    heap = [(0, 0, None)]  # (cost, vertex, parent)
    while heap and added < n:
        w, u, parent = heappop(heap)
        if in_tree[u]:
            continue  # stale entry
        in_tree[u] = True
        added += 1
        if parent is not None:
            chosen.append((parent, u, w))
            total += w
        for v, cost in adj[u]:
            if not in_tree[v]:
                heappush(heap, (cost, v, u))
    return (total, chosen) if added == n else None


def brute_force_cost(n, edges):
    best = None
    for chosen in combinations(edges, max(n - 1, 0)):
        if is_spanning_tree(n, chosen):
            cost = sum(w for _, _, w in chosen)
            best = cost if best is None else min(best, cost)
    return best


def is_spanning_tree(n, chosen):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v, _ in chosen:
        a, b = find(u), find(v)
        if a == b:
            return False
        parent[a] = b
    return len(chosen) == max(n - 1, 0)


def main():
    sites = [(0, 1, 7), (0, 3, 5), (1, 2, 8), (1, 3, 9), (1, 4, 7), (2, 4, 5),
             (3, 4, 15), (3, 5, 6), (4, 5, 8), (4, 6, 9), (5, 6, 11)]
    expected_order = [(0, 3, 5), (3, 5, 6), (0, 1, 7), (1, 4, 7), (4, 2, 5), (4, 6, 9)]
    assert prim_dense(7, sites) == (39, expected_order)
    assert prim_heap(7, sites) == (39, expected_order)

    for prim in (prim_dense, prim_heap):
        assert prim(0, []) == (0, [])
        assert prim(1, [(0, 0, 4)]) == (0, [])
        assert prim(3, [(0, 1, 2)]) is None
        assert prim(2, [(0, 1, 5), (1, 0, -1)]) == (-1, [(0, 1, -1)])

    rng = random.Random(5)
    for _ in range(500):
        n = rng.randint(1, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 6))
                 for _ in range(rng.randint(0, 9))]
        expected = brute_force_cost(n, edges)
        for prim in (prim_dense, prim_heap):
            result = prim(n, edges)
            if expected is None:
                assert result is None
            else:
                assert result[0] == expected and is_spanning_tree(n, result[1])

    # Larger graphs: the two versions agree.
    for _ in range(20):
        n = rng.randint(50, 120)
        edges = [(rng.randrange(v), v, rng.randint(1, 1000)) for v in range(1, n)]
        edges += [(rng.randrange(n), rng.randrange(n), rng.randint(1, 1000))
                  for _ in range(4 * n)]
        assert prim_dense(n, edges)[0] == prim_heap(n, edges)[0]


if __name__ == "__main__":
    main()
```

## 5. Why it is correct

**Claim:** after every step, the chosen edges are part of some MST.

At the start no edge is chosen, which is part of every MST. At each step, let `S` be the current tree's vertices. All chosen edges lie inside `S`, so none crosses the cut `S` versus the rest. The popped edge (dense version: the edge `via[u]–u` with `u` minimizing `best`) is a cheapest edge with one end in `S` and one outside: in the dense version, the invariant says `best[x]` is the cheapest edge from `S` to `x`, and we take the smallest over all `x`; in the heap version, every edge leaving `S` has been pushed (when its inside endpoint joined), stale entries are skipped, and the heap returns the minimum. The safe-edge rule from chapter 2 says the chosen set stays part of some MST. After `V − 1` additions it is a spanning tree, hence an MST.

If the heap empties, or the dense version finds `best = inf`, no edge leaves `S`: the graph is disconnected.

## 6. Prim and Dijkstra are one line apart

[Dijkstra's shortest-path algorithm](../04-shortest-paths/02-dijkstra.md) has the same shape: a heap of candidates, pop the smallest, skip stale entries, push the neighbors. The only difference is the key of a pushed entry:

| Algorithm | Key pushed for neighbor `v` of `u` | Meaning of the key |
|---|---|---|
| Prim | `w(u, v)` | cost of the one edge that would attach `v` |
| Dijkstra | `dist[u] + w(u, v)` | cost of the whole route from the source to `v` |

That one change makes them answer different questions. Prim minimizes the total of the tree; Dijkstra minimizes each vertex's distance from the source. [Variants and Spanning Forests](05-forests-and-variants.md#6-an-mst-is-not-a-shortest-path-tree) shows a graph where the two trees differ.

## 7. Summary

| Version | Time | Extra space | Best for |
|---|---:|---:|---|
| Dense Prim (`best` array) | O(V² + E) | O(V) plus adjacency | Dense graphs; all-pairs costs given by a formula |
| Heap Prim (lazy) | O(E log E) | O(V + E) | Sparse graphs given as adjacency lists |
| Kruskal | O(E log E) | O(V + E) | Edge lists; also gives forests for free |

The cut Prim uses is always "tree so far versus the rest"; mark a vertex when it is **popped**, push the edge weight (not a distance), skip stale entries.

## 8. Pitfalls and practice

1. Marking a vertex as "in the tree" when it is pushed rather than when it is popped. A cheaper edge to it may still be waiting; marking early locks in the wrong edge.
2. Forgetting to skip stale heap entries. Without the check, a vertex is added twice and its edges are added to the total twice.
3. Pushing `dist + w` instead of `w`. That is Dijkstra, and it does not produce an MST.
4. Starting Prim once on a disconnected graph and reporting the partial total. Check that all `V` vertices were added.
5. Using heap Prim on a complete graph of `V` points. It pushes about `V²` entries; dense Prim is both faster and lighter there.

Practice: minimum cost to connect all points (dense Prim, no edge list); connecting cities with minimum cost (heap Prim); compare the edge order of Prim and Kruskal on the same graph and explain the difference.

Next: [Variants and Spanning Forests](05-forests-and-variants.md).
