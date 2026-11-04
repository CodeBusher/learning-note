# Shortest Paths — The Cheapest Route, Under Every Kind of Edge Weight

A **shortest path** is a route between two vertices whose total edge weight is as small as possible. The right algorithm depends on what the weights look like: all equal, only 0 or 1, nonnegative, possibly negative, or "every pair". All of them repeat one step, relaxation, and differ only in the order they relax edges and in why that order is enough. Modeling then turns reliability, effort, and budget-limited trips into shortest-path problems on the right state graph. Prerequisites: adjacency lists from [Search and traversal](../01-search-and-traversal/README.md); a heap from [Heaps and priority queues](../../07-heaps-and-priority-queues/README.md) for Dijkstra.

> **Learning path:** [1 BFS and 0–1 BFS](01-bfs-and-zero-one-bfs.md) → [2 Dijkstra](02-dijkstra.md) → [3 Negative weights and all pairs](03-negative-weights-and-all-pairs.md) → [4 Modeling and A*](04-modeling-and-variants.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [BFS and 0–1 BFS](01-bfs-and-zero-one-bfs.md) | BFS as a distance algorithm, routes from parents, counting shortest routes, why 0-weight edges break BFS, the deque invariant, stale entries | Shortest path in a binary matrix, rotting oranges, minimum obstacle removal |
| 2 | [Dijkstra's Algorithm](02-dijkstra.md) | Relaxation, array and heap versions, lazy deletion, path reconstruction, the correctness proof, the negative-edge counterexample, early exit | Network delay, cheapest route, number of ways to arrive |
| 3 | [Negative Weights and All Pairs](03-negative-weights-and-all-pairs.md) | DAG relaxation, Bellman–Ford with negative-cycle detection, edge-limited rounds, the SPFA caveat, Floyd–Warshall as a DP, Johnson's reweighting | Arbitrage detection, city with fewest neighbors within a threshold |
| 4 | [Modeling with State Graphs](04-modeling-and-variants.md) | Answers built from distances, products and maxima instead of sums, `(vertex, extra info)` states, A* with admissible and consistent heuristics | Max-probability path, minimum effort path, cheapest flights within `k` stops, shortest path to get all keys |

## Recognizing the pattern

| Edge weights / question | Algorithm | Time | Chapter |
|---|---|---:|---|
| All equal (count edges) | BFS | O(V + E) | [1](01-bfs-and-zero-one-bfs.md) |
| Only 0 or 1 | 0–1 BFS with a deque | O(V + E) | [1](01-bfs-and-zero-one-bfs.md#5-01-bfs-a-deque-keeps-the-order) |
| Nonnegative | Dijkstra, lazy heap | O((V + E) log V) | [2](02-dijkstra.md) |
| Nonnegative, dense graph | Dijkstra, array scan | O(V² + E) | [2](02-dijkstra.md#3-trace-with-a-plain-array) |
| DAG, any signs | Relax in topological order | O(V + E) | [3](03-negative-weights-and-all-pairs.md#2-graphs-without-cycles-relax-in-topological-order) |
| Negative weights, one source, detect cycles | Bellman–Ford | O(V E) | [3](03-negative-weights-and-all-pairs.md#3-bellmanford-relax-everything-repeatedly) |
| At most `k` edges | Layered Bellman–Ford, or Dijkstra on `(vertex, edges used)` | O(k (V + E)) | [3](03-negative-weights-and-all-pairs.md#4-at-most-k-edges-keep-the-previous-round), [4](04-modeling-and-variants.md#4-state-augmented-graphs-cheapest-flights-within-k-stops) |
| All pairs, `V` up to a few hundred | Floyd–Warshall | O(V³) | [3](03-negative-weights-and-all-pairs.md#5-floydwarshall-every-pair-at-once-as-a-dp) |
| All pairs, sparse, negative edges | Johnson | O(V E log V) | [3](03-negative-weights-and-all-pairs.md#6-johnsons-algorithm-all-pairs-on-a-sparse-graph-with-negative-edges-advanced) |
| Route cost is a max, or a product of probabilities | Dijkstra with a different combine rule | O((V + E) log V) | [4](04-modeling-and-variants.md#3-minimum-effort-the-cost-of-a-route-is-its-worst-step) |
| Budget, keys, coupons, fuel | Dijkstra or BFS on an augmented state | depends on state count | [4](04-modeling-and-variants.md#4-state-augmented-graphs-cheapest-flights-within-k-stops) |
| One target, good distance estimate | A* | ≤ Dijkstra in practice | [4](04-modeling-and-variants.md#5-a-search-bonus-dijkstra-with-a-sense-of-direction) |

### One operation, different schedules

Every method in this folder repeats the same step, **relaxation** of an edge `u → v` with weight `w`:

$$
\text{if } dist[u] + w < dist[v]:\quad dist[v] \leftarrow dist[u] + w.
$$

They differ only in the order in which they relax edges and in why that order is enough:

- **BFS** relaxes in order of edge count; first discovery is final.
- **0–1 BFS** keeps a deque sorted by distance by pushing 0-edges to the front.
- **Dijkstra** relaxes from the closest unsettled vertex; nonnegative weights make it final.
- **DAG relaxation** follows a topological order; every predecessor is final first.
- **Bellman–Ford** relaxes everything `V − 1` times; no order is needed.
- **Floyd–Warshall** allows one more intermediate vertex per round, for all pairs at once.

## Conventions

- Vertices are `0..V−1` unless a problem numbers them from 1. `V` counts vertices, `E` counts edges.
- Weighted adjacency lists hold `(neighbor, weight)` pairs; edge lists hold `(u, v, w)`. Graphs are directed unless a chapter says undirected; an undirected edge is stored in both directions.
- `inf` (from `math`) means unreachable, `-inf` means unbounded below because of a negative cycle. Distance 0 is never used as "unknown".
- Parents are updated only on strict improvement, so route reconstruction cannot loop.
- Every Python block is a runnable script; algorithms are checked against brute-force enumeration of simple paths (and against each other) on random small graphs with a fixed seed.

## Common modeling moves

- **Many sources** (nearest hospital): start them all at distance 0, the same as a virtual source with 0-weight edges.
- **Distances to one target** in a directed graph: reverse every edge and run from the target.
- **Shortest path visiting a required vertex `m`**: `dist(s, m) + dist(m, t)`, two runs.
- **Edge weight depends on arrival time** (waiting at lights): put the time, or time modulo the period, in the state.
- **Simple-path constraints with negative cycles** ("cheapest route that never repeats a vertex"): a different and much harder problem; the algorithms here use the usual definition, where routes may repeat vertices.

## Connections to other folders

- [Minimum spanning trees](../03-minimum-spanning-trees/README.md): Prim is Dijkstra with a different key; an MST answers minimax routes, not shortest routes.
- [Connectivity and ordering](../02-connectivity-and-ordering/README.md): topological order for DAG relaxation.
- [Dynamic programming](../../09-dynamic-programming/README.md): DAG relaxation and Floyd–Warshall are DPs; Bellman–Ford's rounds are a DP over the number of edges.
- [Heaps and priority queues](../../07-heaps-and-priority-queues/README.md): lazy deletion of stale heap entries.
- [Monotonic stacks and deques](../../06-monotonic-stack-and-deque/README.md): a different deque invariant from 0–1 BFS.
- [AI search notes](../../../Foundation%20of%20AI/01-search.md): A* and heuristic search in a broader setting.

## Practice order

1. Shortest path in a binary matrix; rotting oranges (BFS, multi-source BFS).
2. Minimum obstacle removal; minimum cost to make a valid path (0–1 BFS).
3. Network delay time; cheapest route with reconstruction (Dijkstra).
4. Path with maximum probability; path with minimum effort (combine rules).
5. Cheapest flights within `k` stops (both methods).
6. Course schedule with weights (DAG); arbitrage detection (Bellman–Ford).
7. City with the fewest neighbors within a threshold (Floyd–Warshall).
8. Shortest path to get all keys; sliding puzzle with A*.

For every problem, state the source(s), whether edges are directed, the sign of the weights, and how unreachable or unbounded answers are reported.
