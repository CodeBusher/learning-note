# Trees and Advanced Topics — Rooted Trees, Flows, Matchings, Euler Paths

A **tree** is a connected graph with no cycles, so every two vertices are joined by exactly one route. Binary trees given as node objects (traversals, recursion, BSTs, tries) are covered in [Trees](../../03-trees/README.md). Here a tree arrives as an unrooted edge list with any number of children per vertex: rooting it once turns subtrees into array ranges, lowest common ancestors and path queries into O(log V) or O(1) jumps, and the longest route (diameter) and best central vertex into two linear sweeps. The second half, marked advanced, covers three graph topics that need new ideas: maximum flow with minimum cuts, bipartite matching, and Euler paths, followed by a roadmap of further techniques (heavy-light and centroid decomposition, and more). Prerequisites: BFS/DFS from [Search and traversal](../01-search-and-traversal/README.md); Fenwick trees and sparse tables from [Range queries](../../04-range-queries/README.md).

> **Learning path:** [1 Rooting and LCA](01-rooting-and-lca.md) → [2 Diameter and centers](02-tree-diameter.md) → Advanced: [3 Flow and matching](03-flow-and-matching.md) → [4 Euler paths and roadmap](04-euler-paths-and-roadmap.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [Rooting a Tree and LCA](01-rooting-and-lca.md) | Parent/depth arrays without recursion, entry/exit times, subtrees as ranges with a Fenwick tree, binary lifting (traced jump table), path distances and path maxima, Euler walk + sparse table for O(1) LCA | Kth ancestor, LCA of an unrooted tree, distance between nodes, subtree sums with updates |
| 2 | [Tree Diameter and Centers](02-tree-diameter.md) | Two-sweep diameter and its proof, why negative weights break it, the two-branch tree DP, eccentricities, centers and radius | Tree diameter from an edge list, minimum height trees |
| 3 | [Maximum Flow and Bipartite Matching](03-flow-and-matching.md) **(advanced)** | Why greedy paths fail, residual graphs, Edmonds–Karp traced, the min-cut certificate, augmenting paths in matchings, Kuhn and Hopcroft–Karp | Max flow / min cut, job assignment, edge-disjoint paths |
| 4 | [Euler Paths and Further Topics](04-euler-paths-and-roadmap.md) **(advanced)** | The degree test, Hierholzer's splice-by-stack algorithm traced, smallest itinerary; roadmap: rerooting, small-to-large, HLD, centroid decomposition, min-cost flow | Reconstruct itinerary, valid arrangement of pairs, cracking the safe |

## Recognizing the pattern

| The problem says… | Technique | Cost | Chapter |
|---|---|---:|---|
| "Parent", "depth", "is `u` above `v`?" | Root once; entry/exit times | O(V), then O(1) | [1](01-rooting-and-lca.md) |
| "Sum / count over the subtree of `v`", with updates | Entry-time ranges + Fenwick or segment tree | O(log V) per operation | [1](01-rooting-and-lca.md#3-entry-times-every-subtree-is-a-range) |
| "Lowest common ancestor", "`k`-th ancestor" | Binary lifting | O(V log V) build, O(log V) query | [1](01-rooting-and-lca.md#5-binary-lifting-jump-2j-levels-at-once) |
| Many LCA queries, nothing else | Euler walk + sparse table | O(1) query | [1](01-rooting-and-lca.md#8-lca-by-euler-walk-and-sparse-table) |
| "Distance between `u` and `v`", "largest edge on the path" | Root distances + LCA; lifting with maxima | O(log V) | [1](01-rooting-and-lca.md#6-distances-and-other-path-queries) |
| "Longest route", "farthest pair" | Two sweeps (nonnegative) or tree DP (any weights) | O(V) | [2](02-tree-diameter.md) |
| "Best root", "minimize the height" | Centers from the diameter | O(V) | [2](02-tree-diameter.md#4-centers-where-to-put-the-server) |
| "How much can flow from `s` to `t`?", "cheapest links to cut" | Max flow / min cut | O(V E²) Edmonds–Karp | [3](03-flow-and-matching.md) |
| "Assign workers to jobs, each at most once" | Bipartite matching | O(E √V) Hopcroft–Karp | [3](03-flow-and-matching.md#6-bipartite-matching) |
| "Use every edge / ticket exactly once" | Euler path, Hierholzer | O(V + E) | [4](04-euler-paths-and-roadmap.md) |
| "Update or query every vertex on a path" | Heavy-light decomposition | O(log² V) | [4](04-euler-paths-and-roadmap.md#5-roadmap-of-further-topics-advanced) |
| "Count paths with a property over all pairs" | Centroid decomposition | O(V log V) | [4](04-euler-paths-and-roadmap.md#5-roadmap-of-further-topics-advanced) |

## Conventions

- Trees arrive as `V − 1` undirected edges `(u, v)` or `(u, v, w)` on vertices `0..V−1`; code validates that they really form a tree. The root is vertex 0 unless stated.
- The root is its own parent in jump tables, so jumping past the top stays at the root.
- Subtree ranges are half-open `[tin[v], tout[v])` over the entry order. The Euler walk for LCA is a different, longer array (length `2V − 1`).
- Traversals are iterative: Python's recursion limit is far below the depth of a long chain. The only recursive code (matching DFS) states its depth bound.
- Flow networks are directed with nonnegative integer capacities; an undirected pipe is two directed edges.
- Every Python block is a runnable script, checked against a naive or brute-force method on random inputs with a fixed seed.

## Connections to other folders

- [Trees](../../03-trees/README.md): binary trees as node objects, recursive traversals, LCA of a binary tree by recursion ([Construction, paths and LCA](../../03-trees/04-construction-paths-and-lca.md)), diameter and maximum path sum of a binary tree ([Recursion on trees](../../03-trees/02-recursion-on-trees.md)).

- [Range queries](../../04-range-queries/README.md): Fenwick and segment trees over entry-time ranges; sparse tables for range minimum.
- [Dynamic programming](../../09-dynamic-programming/README.md): tree DP (diameter, rerooting) and bitmask DP for Hamiltonian paths, the hard cousin of Euler paths.
- [Minimum spanning trees](../03-minimum-spanning-trees/README.md): maximum edge on a tree path powers bottleneck queries and second-best MST.
- [Shortest paths](../04-shortest-paths/README.md): BFS inside Edmonds–Karp; Bellman–Ford and Dijkstra with potentials inside min-cost flow.
- [Connectivity and ordering](../02-connectivity-and-ordering/README.md): DSU (offline LCA), bridges, 2-SAT.

## Practice order

1. Kth ancestor of a tree node; LCA queries on a tree given as an edge list.
2. Distance between two nodes; maximum edge weight on a tree path.
3. Subtree sum queries with point updates.
4. Tree diameter from an edge list (with and without negative weights); minimum height trees.
5. Maximum flow and minimum cut on a small network by hand, then in code.
6. Maximum bipartite matching; maximum number of edge-disjoint paths.
7. Reconstruct itinerary; valid arrangement of pairs.
8. When ready: sum of distances in a tree (rerooting), path updates with HLD, count pairs at distance `k` (centroid decomposition).
