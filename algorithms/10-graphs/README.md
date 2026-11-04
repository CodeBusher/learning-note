# Graph Algorithms — From First Traversal to Flows

A **graph** is a set of objects (**vertices**) and connections between them (**edges**): cities and roads, people and friendships, cells of a maze and the moves between them, tasks and the prerequisites that order them. A small set of algorithms answers most questions about a graph: what can be reached, what belongs together, in what order things can happen, how to connect everything cheaply, and what the shortest route is. The material runs from building a first graph out of a word problem to maximum flow, bipartite matching, and contest-level tree techniques.

> **Learning path:** [1 Search and traversal](01-search-and-traversal/README.md) → [2 Connectivity and ordering](02-connectivity-and-ordering/README.md) → [3 Minimum spanning trees](03-minimum-spanning-trees/README.md) → [4 Shortest paths](04-shortest-paths/README.md) → [5 Trees and advanced topics](05-trees-and-advanced/README.md)

## Subfolders

| # | Subfolder | Main questions | You will learn |
|---|---|---|---|
| 1 | [Search and traversal](01-search-and-traversal/README.md) | What is reachable? How do I explore a maze or a puzzle's states? | Adjacency lists, BFS, DFS, flood fill, multi-source search, state-space search, backtracking, bidirectional search |
| 2 | [Connectivity and ordering](02-connectivity-and-ordering/README.md) | Which vertices belong together? Which tasks can run first? Which links are fragile? | Disjoint set union, topological sort, strongly connected components, bridges and articulation points |
| 3 | [Minimum spanning trees](03-minimum-spanning-trees/README.md) | How do I connect everything at minimum total cost? | Brute force over spanning trees, cut and cycle properties, Kruskal, Prim, forests, bottleneck routes, second-best MST |
| 4 | [Shortest paths](04-shortest-paths/README.md) | What is the cheapest route, and how do the edge weights change the method? | BFS, 0–1 BFS, Dijkstra, DAG relaxation, Bellman–Ford, Floyd–Warshall, Johnson, state graphs, A* |
| 5 | [Trees and advanced topics](05-trees-and-advanced/README.md) | How do I exploit a tree? What comes after the core tools? | Rooting, subtree ranges, LCA by binary lifting and sparse table, diameter, max flow and min cut, matching, Euler paths, roadmap |

Subfolders 1 and 2 are the foundation; read them first, in order. Subfolders 3 and 4 can be read in either order after that. Subfolder 5 assumes BFS/DFS and uses ideas from all the others. Binary trees and their traversals come earlier, in [Trees](../03-trees/01-binary-trees-and-traversals.md); subfolder 5 here handles general rooted and unrooted trees.

## Choose from the question and its assumptions

The same graph supports many questions, and the right tool depends on the question and on what you know about the edges.

| Problem property | First tool | Why it works | Subfolder |
|---|---|---|---|
| Reachability or connected components | DFS / BFS | Each reachable vertex needs one visit | [1](01-search-and-traversal/README.md) |
| Fewest edges in an unweighted graph | BFS | The queue holds vertices in nondecreasing distance order | [1](01-search-and-traversal/README.md), [4](04-shortest-paths/README.md) |
| Edge weights are only 0 and 1 | 0–1 BFS | A deque keeps distance order: 0-edges to the front, 1-edges to the back | [4](04-shortest-paths/README.md) |
| All edge weights are nonnegative | Dijkstra | The smallest tentative distance can be finalized | [4](04-shortest-paths/README.md) |
| Directed and acyclic, weights may be negative | Relaxation in topological order | Every predecessor is final before its successors | [4](04-shortest-paths/README.md) |
| Negative edges, one source | Bellman–Ford | `V − 1` rounds of relaxation; one more round detects reachable negative cycles | [4](04-shortest-paths/README.md) |
| All pairs, modest vertex count | Floyd–Warshall | An O(V³) DP over allowed intermediate vertices | [4](04-shortest-paths/README.md) |
| Route cost is a budget, keys, or fuel, not only a place | Shortest path on `(vertex, extra state)` | Two arrivals with different budgets are different vertices | [4](04-shortest-paths/README.md) |
| Undirected connectivity as edges are added | Disjoint set union | Merges components without searching them again | [2](02-connectivity-and-ordering/README.md) |
| Connect every vertex at minimum total cost | Minimum spanning tree | Cut property: the lightest edge across any cut is safe | [3](03-minimum-spanning-trees/README.md) |
| Minimize the largest edge on a route | MST route, or bottleneck Dijkstra | The MST route has the smallest possible maximum edge | [3](03-minimum-spanning-trees/README.md), [4](04-shortest-paths/README.md) |
| Dependency scheduling | Topological sort | Process prerequisites before dependents | [2](02-connectivity-and-ordering/README.md) |
| Directed mutual reachability | Strongly connected components | Contract cycles into a DAG | [2](02-connectivity-and-ordering/README.md) |
| Edges or vertices whose removal disconnects | Bridges / articulation points | DFS low-links record alternate routes to ancestors | [2](02-connectivity-and-ordering/README.md) |
| Ancestor, LCA, or path queries on a tree | Rooting + binary lifting | Jumps of size `2^j` reach any ancestor in O(log V) | [5](05-trees-and-advanced/README.md) |
| How much can move from `s` to `t`; fewest links to cut | Max flow / min cut | Augmenting paths in the residual graph | [5](05-trees-and-advanced/README.md) |
| Assign items to slots, each used once | Bipartite matching | Augmenting paths that reassign earlier choices | [5](05-trees-and-advanced/README.md) |
| Use every edge exactly once | Euler path (Hierholzer) | A degree test plus splicing closed detours | [5](05-trees-and-advanced/README.md) |

### Two trees that are easy to confuse

A **minimum spanning tree** (MST) and a **shortest-path tree** are both spanning trees, but they optimize different things. With edges `s–a = 2`, `a–b = 2`, `s–b = 3`:

```text
        s
      ╱   ╲
     2     3
    ╱       ╲
   a ───2─── b
```

- The MST takes the two cheapest edges, `s–a` and `a–b`, total **4**. Inside it, the route from `s` to `b` costs 4.
- The shortest route from `s` to `b` is the direct edge, cost **3**. A shortest-path tree from `s` uses `s–a` and `s–b`, total 5.

The MST minimizes the **sum of the tree's edges**; the shortest-path tree minimizes **each vertex's distance from one source**. [Variants and spanning forests](03-minimum-spanning-trees/05-forests-and-variants.md#6-an-mst-is-not-a-shortest-path-tree) works this example and a second one where the shortest-path tree costs almost twice as much.

## Conventions

- Vertices are `0..V−1`; `V` counts vertices and `E` counts edges. An undirected edge appears in both endpoints' adjacency lists, so lists hold `2E` entries.
- Unweighted adjacency: `adj[u]` lists neighbor IDs. Weighted adjacency: `adj[u]` lists `(neighbor, weight)` pairs. Edge lists are `(u, v, w)` triples unless a chapter states otherwise.
- `math.inf` means unreachable and `-math.inf` means unbounded below (a reachable negative cycle). Distance 0 never means "unknown".
- Traversals use explicit stacks and queues: Python's recursion limit (about 1000) is far below the depth of a long path. Recursive code says when its depth is bounded.
- Every Python block is a complete script using only the standard library, with assertions, and is tested against a brute force (all simple paths, all edge subsets, all spanning trees) on small random graphs with a fixed seed.
- Before choosing an algorithm, check: directed or undirected, weight signs, disconnected pieces, isolated vertices, parallel edges, self-loops, and whether the route itself or only its cost is required.

## Connections to other folders

- [Trees](../03-trees/01-binary-trees-and-traversals.md): binary trees, traversals and BSTs; DFS on a tree is the special case with no cycles, so no visited set is needed.
- [Dynamic programming](../09-dynamic-programming/README.md): a DAG gives a DP its evaluation order; Floyd–Warshall and Bellman–Ford are DPs; tree DP computes diameters and rerooting answers.
- [Heaps and priority queues](../07-heaps-and-priority-queues/README.md): the min-heap and lazy deletion behind Dijkstra and Prim.
- [Range queries](../04-range-queries/README.md): DFS entry order turns subtrees into array ranges; sparse tables answer LCA in O(1).
- [Monotonic stacks and deques](../06-monotonic-stack-and-deque/README.md): a deque with a different invariant than 0–1 BFS.
- [Binary search](../01-binary-search/README.md): "smallest limit for which a route exists" is binary search on the answer plus BFS.
- [Bit manipulation](../11-bit-manipulation/README.md): bitmask states for key-collecting searches.
- [AI search notes](../../Foundation%20of%20AI/01-search.md): uninformed and heuristic search, including A*, in a broader setting.

## Study checkpoints

After working through the subfolders, you should be able to:

1. Model islands, word transformations, dependency chains, and key-collecting mazes as graphs without relying on a drawing, and say what a vertex must remember.
2. Explain when marking `visited` on discovery is safe (BFS) and when a distance must still be allowed to improve (0-weight edges, Dijkstra).
3. Derive BFS, DSU, Kruskal, Prim, and Dijkstra from their invariants, and prove the cut property with an exchange argument.
4. Give a counterexample to Dijkstra with a negative edge, and to using an MST as a shortest-path tree.
5. Reconstruct a route from parent pointers, and distinguish unreachable (`inf`), distance zero, and unbounded (`-inf`).
6. Answer LCA, distance, and subtree-sum queries on a tree in O(log V) after preprocessing.
7. Find a maximum flow by hand and point to the minimum cut that proves it optimal.
8. Test your code on ties, parallel edges, self-loops, a disconnected piece, a long chain, and a negative cycle the source cannot reach.
