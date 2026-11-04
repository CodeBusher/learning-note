# Minimum Spanning Trees — Connect Everything at the Lowest Total Cost

Given places and the price of every possible link between two of them, a **minimum spanning tree** (MST) is the cheapest set of links that connects all the places. Two facts, the cut property and the cycle property, decide edge by edge which links are safe; Kruskal's and Prim's algorithms are those facts applied in two different orders. The variants that follow (forests, implicit point graphs, virtual vertices, bottleneck routes, second-best trees) reuse the same two algorithms. Prerequisites: an undirected graph as an edge list; the disjoint set union from [Connectivity and ordering](../02-connectivity-and-ordering/README.md) for Kruskal; a heap from [Heaps and priority queues](../../07-heaps-and-priority-queues/README.md) for Prim.

> **Learning path:** [1 Spanning trees](01-spanning-trees.md) → [2 Cut and cycle properties](02-cut-and-cycle-properties.md) → [3 Kruskal](03-kruskal.md) → [4 Prim](04-prim.md) → [5 Variants and forests](05-forests-and-variants.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [Spanning Trees](01-spanning-trees.md) | What a spanning tree is, why the cheapest connecting set is a tree, three tree facts, brute force over edge subsets, Cayley's formula | Network cabling by hand |
| 2 | [The Cut and Cycle Properties](02-cut-and-cycle-properties.md) | Cuts, the exchange argument, safe edges, the cycle property, ties and uniqueness, classifying every edge | Which edges are in some / every MST |
| 3 | [Kruskal's Algorithm](03-kruskal.md) | Sorted-edge trace, DSU recap, correctness proof, maximum spanning tree, critical edges, offline threshold queries | Connecting cities, critical and pseudo-critical edges, edge-length-limited paths |
| 4 | [Prim's Algorithm](04-prim.md) | `best`-array Prim in O(V²), heap Prim with lazy deletion, when each wins, the one-line difference from Dijkstra | Connect all points, connecting cities |
| 5 | [Variants and Spanning Forests](05-forests-and-variants.md) | Spanning forests, implicit complete graphs, virtual vertices, minimum bottleneck routes, second-best MST, why an MST is not a shortest-path tree | Water distribution, minimax paths, second minimum spanning tree |

## Recognizing the pattern

| The problem says… | Model | Tool |
|---|---|---|
| "Connect all … at minimum total cost" | MST | Kruskal (edge list) or Prim (adjacency) |
| "Every pair of points can be linked, cost = distance" | MST on an implicit complete graph | Dense Prim, O(n²) |
| "Each node can also be served on its own for a price" | Add a virtual vertex | Kruskal on the enlarged graph |
| "Minimize the largest edge used on a route" | Minimum bottleneck path | Route inside the MST, or Kruskal-style DSU sweep |
| "Can `p` reach `q` using only edges below a limit?", many queries | Offline threshold connectivity | Sort queries and edges, DSU sweep |
| "Which edges must / may appear in the cheapest network?" | Edge classification | Cut and cycle properties, or Kruskal with forced / skipped edges |
| "Cheapest network that is not the cheapest" | Second-best MST | One swap per non-tree edge |
| "Graph may be in pieces" | Minimum spanning forest | Kruskal unchanged; Prim restarted per component |
| "Shortest route from a source" | **Not** an MST | [Shortest paths](../04-shortest-paths/README.md) |

## Conventions

- Graphs are undirected. Edges are triples `(u, v, w)` with vertices `0..V−1`; `V` counts vertices and `E` counts edges.
- Weights may be negative, zero, or repeated. Parallel edges and self-loops may appear in tests; a self-loop is never chosen.
- Functions return `None` when a required spanning tree does not exist, or a forest together with its number of components when the chapter says so.
- Every Python block is a runnable script with assertions; solutions are checked against brute force over edge subsets with a fixed random seed.
- With repeated weights several MSTs may exist. Tests compare costs and check that the output is a spanning tree, never a particular edge list.

## Connections to other folders

- [Connectivity and ordering](../02-connectivity-and-ordering/README.md): the disjoint set union behind Kruskal.
- [Heaps and priority queues](../../07-heaps-and-priority-queues/README.md): the min-heap behind Prim, with the same lazy-deletion pattern as Dijkstra.
- [Shortest paths](../04-shortest-paths/README.md): Dijkstra is Prim with a different key; the two trees answer different questions.
- [Trees and advanced topics](../05-trees-and-advanced/README.md): binary lifting answers maximum-edge-on-route queries in O(log V), which speeds up bottleneck queries and second-best MST.
- [Range queries](../../04-range-queries/README.md): the Fenwick-tree sweep behind the O(n log n) Manhattan MST.

## Practice order

1. Network cabling by hand (chapter 1), then the same graph with one cost changed.
2. Prove that the lightest edge at any vertex is in some MST (chapter 2).
3. Connecting cities with minimum cost (Kruskal), then redundant connection.
4. Min cost to connect all points (dense Prim).
5. Optimize water distribution in a village (virtual vertex).
6. Find critical and pseudo-critical edges in an MST.
7. Path with minimum maximum edge; checking existence of edge-length-limited paths.
8. Second minimum spanning tree.

For every accepted edge, be able to name the cut that justifies it.
