# Connectivity and Ordering — Groups, Dependencies, and Weak Spots

Four questions about how a graph hangs together. Which undirected groups exist as edges keep arriving (disjoint set union)? In what order can dependent tasks run (topological sort)? Which directed vertices are mutually reachable (strongly connected components)? Which single edge or vertex failure disconnects the network (bridges and articulation points)? All but DSU are built on the DFS of [Search and Traversal](../01-search-and-traversal/README.md).

> **Learning path:** [1 Disjoint Set Union](01-disjoint-set-union.md) → [2 Topological Sort and SCCs](02-topological-sort-and-scc.md) → [3 Bridges and Articulation Points](03-bridges-and-articulation.md) · then [Minimum Spanning Trees](../03-minimum-spanning-trees/README.md)

Parent: [Graph Algorithms](../README.md). Prerequisite: [Search and Traversal](../01-search-and-traversal/README.md), especially DFS with a stack of frames, three-color cycle detection, and entry/exit times.

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [Disjoint Set Union](01-disjoint-set-union.md) | From a label array to a parent forest; union by size with the doubling proof; path compression and halving traced on arrays; α(n) amortized time; DSU with sizes, parity, and ratios | Number of provinces, redundant connection, accounts merge, evaluate division, online bipartiteness |
| 2 | [Topological Sort and SCCs](02-topological-sort-and-scc.md) | Kahn's algorithm with traced in-degrees; course schedule I/II; lexicographically smallest order; DFS reverse postorder and why it works; longest path in a DAG; Kosaraju and Tarjan traced; condensation DAG | Course schedule, parallel courses, alien dictionary, strongly connected components, minimum arrows to strongly connect |
| 3 | [Bridges and Articulation Points](03-bridges-and-articulation.md) | DFS trees and back edges; `tin`/`low` traced; strict vs non-strict tests; the root rule; parallel edges via edge ids; bridge tree; biconnected components | Critical connections, cut vertices, minimum days to disconnect an island |

Chapters 2 and 3 are independent of each other; both need the DFS of Search and Traversal. Chapter 1 needs only basic graph vocabulary.

## Recognizing the pattern

| The problem says… | Graph | Tool | Cost | Chapter |
|---|---|---|---:|---|
| "Edges arrive over time; are `a` and `b` connected now?" | Undirected, only additions | DSU | O(α(V)) per operation | [1](01-disjoint-set-union.md) |
| "Which edge closes a cycle?", "is this a valid tree?" | Undirected edge list | DSU: a failed union | O(E α(V)) | [1](01-disjoint-set-union.md#8-redundant-connection-the-edge-that-closes-a-cycle) |
| "Group records that share any key" | Records joined by keys | DSU over records, first owner per key | O(N α(N)) | [1](01-disjoint-set-union.md#9-accounts-merge-union-by-shared-keys) |
| "Given `a/b = k` facts, answer `x/y`", "still two-colorable?" | Relations along edges | Weighted or parity DSU | O(α(V)) per operation | [1](01-disjoint-set-union.md#10-dsu-with-extra-data) |
| "Prerequisites", "build order", "can all tasks finish?" | Directed | Topological sort (Kahn or DFS) | O(V + E) | [2](02-topological-sort-and-scc.md) |
| "Minimum rounds / semesters", "longest chain" | DAG | DP in topological order | O(V + E) | [2](02-topological-sort-and-scc.md#4-preview-longest-path-in-a-dag) |
| "Mutually reachable", "cycles in a directed graph as groups" | Directed | SCCs (Kosaraju or Tarjan), then the condensation DAG | O(V + E) | [2](02-topological-sort-and-scc.md#5-when-cycles-are-the-point-strongly-connected-components) |
| "Which single link / node failure disconnects the network?" | Undirected | `tin` / `low` DFS | O(V + E) | [3](03-bridges-and-articulation.md) |

## A useful distinction

For directed edges `0→1, 1→2, 2→1, 2→3`, the SCCs are `{0}`, `{1, 2}`, `{3}`. Collapsing each group gives the DAG `{0} → {1,2} → {3}`. There is no topological order of the original vertices, because 1 and 2 form a cycle, but there is one of the components.

Ignoring direction gives **weak connectivity**: here everything is one weak component. Ordinary DSU computes weak components, because it ignores direction, but it cannot compute directed reachability or SCCs.

## Beyond the core

- **Bipartiteness.** BFS or DFS two-coloring ([Search and Traversal](../01-search-and-traversal/03-bfs.md#8-two-coloring-is-the-graph-bipartite)) answers it once in O(V + E); parity DSU ([Chapter 1](01-disjoint-set-union.md#102-parity-is-the-graph-still-two-colorable)) keeps answering as edges are added.
- **Deletions.** Plain DSU cannot split sets. If all deletions are known in advance, process time backwards so they become additions; for mixed insertions and deletions offline, divide and conquer over time with a rollback DSU (union by size, no path compression, an undo stack) works.
- **2-SAT.** Turn each clause into two implication arrows and compute SCCs; the formula is satisfiable exactly when no variable shares an SCC with its negation ([Chapter 2 §8](02-topological-sort-and-scc.md#8-using-the-condensation)).
- **Euler paths.** A route that uses every **edge** exactly once. In a connected undirected graph (ignoring isolated vertices), a closed Euler circuit exists exactly when every degree is even, and an open Euler trail exactly when two degrees are odd. Directed graphs need in-degree equal to out-degree at every vertex (except at the two ends of an open trail) plus connectivity. Hierholzer's algorithm builds one in O(V + E) ([Euler Paths](../05-trees-and-advanced/04-euler-paths-and-roadmap.md)). Visiting every **vertex** exactly once (a Hamiltonian path) is a different, much harder problem; see the bitmask state in [State-Space Search](../01-search-and-traversal/04-state-space-search.md#2-count-the-states-before-you-code).

## Conventions

- Vertices are `0..V-1` unless a problem uses `1..n`, in which case the code says so. `adj[u]` lists out-neighbors; undirected edges appear in both lists.
- When edges can be parallel, they carry ids (`eid`) and the DFS skips only the edge it arrived on.
- Every DFS here uses the explicit stack of frames `(vertex, iterator)`, so a path of 10⁵ vertices does not hit Python's recursion limit.
- Every Python block is a complete script; the tests compare against brute force (BFS reachability, trying every permutation, removing each edge or vertex) on random small graphs with fixed seeds.

## Connections

- [Search and Traversal](../01-search-and-traversal/README.md): the DFS and BFS everything here is built on.
- [Minimum Spanning Trees](../03-minimum-spanning-trees/README.md): Kruskal's algorithm is DSU plus sorting.
- [Shortest Paths](../04-shortest-paths/README.md): shortest paths in a DAG use topological order.
- [Dynamic Programming](../../09-dynamic-programming/README.md): DP on a DAG evaluates states in topological order.

## Practice order

1. Number of provinces → redundant connection → graph valid tree → accounts merge
2. Satisfiability of equality equations → evaluate division → number of islands II
3. Course schedule → course schedule II → parallel courses → alien dictionary
4. Find eventual safe states → strongly connected components → minimum arrows to make a graph strongly connected
5. Critical connections in a network → articulation points → minimum number of days to disconnect an island
6. For each, state whether the graph is directed and which kind of connectivity the question needs.
