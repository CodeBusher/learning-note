# Euler Paths and Further Topics — Using Every Edge Once (Advanced)

## 1. Draw the house in one stroke

A child's drawing of a house: a square with both diagonals, and a roof.

```text
            4
          ╱   ╲
         3 ──── 2
         │ ╲  ╱ │
         │  ╲╱  │
         │  ╱╲  │
         │ ╱  ╲ │
         0 ──── 1
```

Edges: `0–1`, `1–2`, `2–3`, `3–0`, `0–2`, `1–3`, `2–4`, `3–4` (8 edges).

**Problem.** Draw all 8 edges in one continuous stroke without repeating an edge. Where must you start?

One answer: `0 → 1 → 2 → 0 → 3 → 2 → 4 → 3 → 1`. Starting at 4 gets stuck every time. A route that uses **every edge exactly once** is an **Euler path**. (Visiting every *vertex* once is a Hamiltonian path, which has no known fast algorithm.)

**Brute force** backtracks over unused edges: up to about `E!` orders, hopeless at 30 edges.

## 2. The degree test

The **degree** of a vertex is the number of edge ends at it. In the house: `deg(0) = 3`, `deg(1) = 3`, `deg(2) = 4`, `deg(3) = 4`, `deg(4) = 2`.

**Observation.** Every time a stroke passes **through** a vertex, it uses two edges there: one in, one out. Only the start and the end of the stroke use a single edge at a vertex. So:

- At every vertex other than the start and the end, the degree must be **even**.
- If the stroke starts and ends at the same vertex (an **Euler circuit**), every degree is even.
- If it starts and ends at different vertices (an **Euler path**), exactly those two have **odd** degree.

The house has exactly two odd vertices, 0 and 1, so an Euler path must run from 0 to 1 (or 1 to 0). That is why starting at 4 fails.

**The full rule (undirected).** Ignore vertices with no edges. An Euler circuit exists exactly when the remaining vertices are connected and every degree is even. An Euler path exists exactly when they are connected and there are zero or two odd-degree vertices; with two, the path runs between them.

**Directed graphs.** Each vertex has an **in-degree** and an **out-degree**. An Euler circuit needs `in = out` everywhere. An Euler path needs one start vertex with `out = in + 1`, one end vertex with `in = out + 1`, and `in = out` everywhere else. In both cases, all edges must lie in one connected piece when directions are ignored (with the degree condition, that is enough).

The conditions are also sufficient, as the algorithm below proves by construction.

## 3. Hierholzer's algorithm: walk, get stuck, splice

**The idea.** Start at the right vertex and walk along unused edges, choosing any. You can only get stuck at the end vertex (every other vertex you enter has an unused edge left to leave by, since its degree is even). You may get stuck before using every edge. Then back up along your walk to the last vertex that still has unused edges, take a detour from there, and **splice** the detour into the route.

The iterative version does this automatically with a stack:

1. Push the start vertex.
2. Look at the top vertex `u`. If it has an unused edge `u–v`, mark it used and push `v`.
3. Otherwise pop `u` and append it to the output.
4. Repeat until the stack is empty. The output, reversed, is the Euler path.

Vertices are popped exactly when all their edges are used, so they come out in the reverse of a valid order.

### Trace on the house (neighbors tried in increasing order)

| Step | Top | Action | Stack (bottom → top) | Output |
|---:|---|---|---|---|
| 1 | 0 | use `0–1` | `0 1` | |
| 2 | 1 | use `1–2` | `0 1 2` | |
| 3 | 2 | use `2–0` | `0 1 2 0` | |
| 4 | 0 | use `0–3` | `0 1 2 0 3` | |
| 5 | 3 | use `3–1` | `0 1 2 0 3 1` | |
| 6 | 1 | stuck: pop | `0 1 2 0 3` | `1` |
| 7 | 3 | use `3–2` | `0 1 2 0 3 2` | `1` |
| 8 | 2 | use `2–4` | `0 1 2 0 3 2 4` | `1` |
| 9 | 4 | use `4–3` | `0 1 2 0 3 2 4 3` | `1` |
| 10–17 | | everything is used: pop all | empty | `1 3 4 2 3 0 2 1 0` |

Reversed output: `0 → 1 → 2 → 0 → 3 → 2 → 4 → 3 → 1`.

Step 6 is the interesting moment. The first walk `0 → 1 → 2 → 0 → 3 → 1` reached the end vertex 1 with three edges (`3–2`, `2–4`, `4–3`) still unused. Popping back to 3 found the loop `3 → 2 → 4 → 3`, and the stack order spliced it into the route right after the first visit to 3.

## 4. Code: undirected and directed, tested against backtracking

The directed version also solves the classic itinerary puzzle: given airline tickets `(from, to)`, use all of them in one trip starting from a given airport, and among all valid trips return the **lexicographically smallest** one. Sorting each adjacency list and always taking the smallest unused edge makes Hierholzer produce exactly that trip.

```python
import random
from collections import defaultdict


def euler_path_undirected(n, edges):
    """Returns a vertex list using every edge once, or None if impossible."""
    if not edges:
        return [0] if n else []
    adj = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        adj[u].append((v, i))
        adj[v].append((u, i))
    for row in adj:
        row.sort()
    odd = [v for v in range(n) if len(adj[v]) % 2]
    if len(odd) not in (0, 2):
        return None
    start = odd[0] if odd else edges[0][0]
    used = [False] * len(edges)
    pointer = [0] * n
    stack, out = [start], []
    while stack:
        u = stack[-1]
        while pointer[u] < len(adj[u]) and used[adj[u][pointer[u]][1]]:
            pointer[u] += 1
        if pointer[u] < len(adj[u]):
            v, i = adj[u][pointer[u]]
            used[i] = True
            stack.append(v)
        else:
            out.append(stack.pop())
    if len(out) != len(edges) + 1:
        return None  # edges were not all in one connected piece
    return out[::-1]


def euler_path_directed(edges, start):
    """Lexicographically smallest trip from `start` using every edge, or None."""
    adj = defaultdict(list)
    balance = defaultdict(int)  # out-degree minus in-degree
    for u, v in edges:
        adj[u].append(v)
        balance[u] += 1
        balance[v] -= 1
    unbalanced = {x: b for x, b in balance.items() if b != 0}
    if unbalanced and (unbalanced.get(start) != 1 or len(unbalanced) != 2
                       or sorted(unbalanced.values()) != [-1, 1]):
        return None  # degree test failed, or the trip cannot start here
    for row in adj.values():
        row.sort(reverse=True)  # pop() then yields the smallest
    stack, out = [start], []
    while stack:
        u = stack[-1]
        if adj[u]:
            stack.append(adj[u].pop())
        else:
            out.append(stack.pop())
    if len(out) != len(edges) + 1:
        return None  # some edges were never reached
    return out[::-1]


def all_euler_paths(edges, directed, start=None):
    """Backtracking brute force over edge orders."""
    found = []

    def extend(path, used):
        if len(path) == len(edges) + 1:
            found.append(path[:])
            return
        u = path[-1]
        for i, (a, b) in enumerate(edges):
            if used[i]:
                continue
            for x, y in ((a, b),) if directed else ((a, b), (b, a)):
                if x == u:
                    used[i] = True
                    path.append(y)
                    extend(path, used)
                    path.pop()
                    used[i] = False

    vertices = {x for e in edges for x in e}
    for s in ([start] if start is not None else vertices):
        extend([s], [False] * len(edges))
    return found


def uses_every_edge(path, edges, directed):
    remaining = list(edges)
    for a, b in zip(path, path[1:]):
        if (a, b) in remaining:
            remaining.remove((a, b))
        elif not directed and (b, a) in remaining:
            remaining.remove((b, a))
        else:
            return False
    return not remaining


def main():
    house = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3), (2, 4), (3, 4)]
    assert euler_path_undirected(5, house) == [0, 1, 2, 0, 3, 2, 4, 3, 1]
    assert euler_path_undirected(4, [(0, 1), (2, 3)]) is None          # two pieces
    assert euler_path_undirected(4, [(0, 1), (0, 2), (0, 3)]) is None  # four odd vertices
    assert euler_path_undirected(1, [(0, 0)]) == [0, 0]                # a self-loop

    tickets = [("JFK", "SFO"), ("JFK", "ATL"), ("SFO", "ATL"), ("ATL", "JFK"), ("ATL", "SFO")]
    assert euler_path_directed(tickets, "JFK") == ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]
    assert euler_path_directed([("A", "B"), ("C", "D")], "A") is None

    rng = random.Random(31)
    for _ in range(300):
        n = rng.randint(1, 4)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(1, 6))]
        brute = all_euler_paths(edges, directed=False)
        path = euler_path_undirected(n, edges)
        assert (path is not None) == bool(brute)
        if path is not None:
            assert uses_every_edge(path, edges, directed=False)

        start = rng.randrange(n)
        brute = all_euler_paths(edges, directed=True, start=start)
        trip = euler_path_directed(edges, start)
        assert trip == (min(brute) if brute else None)


if __name__ == "__main__":
    main()
```

Each edge is marked used once and each vertex's pointer only moves forward, so Hierholzer runs in **O(V + E)** time (plus O(E log E) for sorting when the smallest order is required). Space O(V + E).

**Why it is correct.** Each push uses one unused edge, so every edge is used at most once, and the stack always holds a walk along used edges from the start. A vertex is popped only when it has no unused edges left. When the walk gets stuck early at the end vertex, popping backs up to the most recent vertex with unused edges; with the degree test satisfied, any walk from there must return to that same vertex (every other vertex it enters has an even number of unused edges, so it can always leave). That closed detour is popped before the vertex it hangs from, which places it, in the reversed output, exactly where it branches off the main walk. If some edges lie in a different piece of the graph, they are never reached and the output is too short, which the length check catches.

**Variants.**

- **De Bruijn sequences** (the shortest string containing every `k`-digit code, as in "crack the safe"): vertices are `(k − 1)`-digit strings, each `k`-digit code is an edge, and an Euler circuit spells the answer.
- **Valid arrangement of pairs**: the pairs are directed edges; find an Euler path, starting at the vertex with `out = in + 1` if there is one.
- **Chinese postman** (**advanced**): when some degrees are odd, the cheapest closed route that uses every edge *at least* once duplicates a minimum-cost set of paths pairing up the odd vertices.

## 5. Roadmap of further topics (advanced)

Each technique below exists because the simpler tools in this folder cannot do a particular operation fast enough. Learn one when a problem needs that operation.

| Topic | What it adds | Builds on | Typical cost |
|---|---|---|---|
| **Rerooting DP** | The answer for *every* choice of root (sum of distances to all nodes, best root) | Tree DP from [chapter 2](02-tree-diameter.md) | O(V) |
| **Small-to-large merging** ("DSU on tree") | Per-subtree statistics such as "number of distinct colors in each subtree" | Subtree sizes | O(V log V) |
| **Heavy-light decomposition** (HLD) | **Updates and queries on paths** (add to every vertex on `u–v`, maximum on `u–v`) | Rooting, subtree sizes, [segment trees](../../04-range-queries/README.md) | O(log² V) per operation |
| **Centroid decomposition** | Questions about **all paths** through the tree: count pairs at distance `k`, nearest marked vertex under updates | Subtree sizes, diameter ideas | O(V log V) build; O(log V) levels per query |
| **Binary lifting on other jumps** | "Jump while a condition holds" (first ancestor with value ≥ x) | [Chapter 1](01-rooting-and-lca.md) | O(log V) per query |
| **Virtual (auxiliary) trees** | Many queries each touching a small set of `k` vertices | LCA, entry times | O(k log k) per query |
| **Dinic and min-cost flow** | Fast max flow; flow with costs (assignment, transport) | [Chapter 3](03-flow-and-matching.md), Bellman–Ford / Dijkstra with potentials | O(V² E); depends on flow value |
| **Hungarian algorithm** | Maximum-weight perfect bipartite matching | Matching, potentials | O(V³) |
| **2-SAT, bridges, articulation points** | Logic constraints; fragile links | [Connectivity and ordering](../02-connectivity-and-ordering/README.md) | O(V + E) |
| **Link-cut trees / Euler-tour trees** | Trees whose edges are added and removed online | Splay trees | O(log V) amortized |

### Heavy-light decomposition in one paragraph

Root the tree. At each vertex, call the child with the largest subtree **heavy** and the others **light**. Following only heavy edges splits the tree into vertical **chains**. Any path from a vertex up to the root crosses at most O(log V) light edges, because each light edge at least doubles the subtree size you are in. Number vertices so that every chain is a contiguous block of an array (a DFS that visits the heavy child first does this), and put a segment tree on the array. A path query then becomes O(log V) range queries: **O(log² V)** per operation.

### Centroid decomposition in one paragraph

A **centroid** is a vertex whose removal leaves pieces of at most half the size. Every tree has one, found by walking from any vertex toward its biggest piece. Remove it, recurse on each piece, and record the "centroid tree" of these choices: it has depth O(log V). Every path in the original tree passes through exactly one centroid that is the highest-level centroid on it, so a question about all paths becomes, for each centroid, a question about paths through that centroid, which is usually easy with sorting or counting. Total **O(V log V)** for many path-counting problems.

## 6. Pitfalls and practice

1. Checking degrees but not connectivity. Two separate triangles have all degrees even but no Euler circuit; the length check in the code catches it.
2. Starting at an arbitrary vertex when there are two odd-degree vertices. The path must start at one of them.
3. Removing used edges from a Python list with `list.remove`, which is O(degree) each time. Use a pointer per vertex or pop from the end.
4. For the lexicographically smallest itinerary, greedily following the smallest edge **without** Hierholzer's backtracking. The greedy walk can get stuck early; the stack splices the rest in correctly.
5. Confusing Euler (every edge once, linear time) with Hamiltonian (every vertex once, exponential in general; see bitmask DP in [Dynamic programming](../../09-dynamic-programming/README.md)).
6. Recursion depth in a recursive Hierholzer on long paths. Use the iterative stack.

Practice: reconstruct itinerary; valid arrangement of pairs; cracking the safe (De Bruijn); check whether a figure can be drawn in one stroke; then, when ready for the roadmap, sum of distances in a tree (rerooting), path queries with updates (HLD), count pairs of nodes at distance `k` (centroid decomposition).

Back to the [trees and advanced topics overview](README.md).
