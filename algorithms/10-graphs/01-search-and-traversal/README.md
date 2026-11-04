# Search and Traversal — Exploring a Graph from Zero

Almost every graph algorithm starts by **exploring**: which vertices can be reached, in what order, and how far away they are. Depth-first search goes deep and records finishing order; breadth-first search goes layer by layer and finds fewest-edge distances. Making the vertices richer (a cell plus keys held, a vertex plus the set visited) lets the same two searches solve puzzles, mazes with rules, and "list every arrangement" problems.

> **Learning path:** [1 What a Graph Is](01-what-a-graph-is.md) → [2 Depth-First Search](02-dfs.md) → [3 Breadth-First Search](03-bfs.md) → [4 State-Space Search](04-state-space-search.md) · then [Connectivity and Ordering](../02-connectivity-and-ordering/README.md)

Parent: [Graph Algorithms](../README.md).

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [What a Graph Is](01-what-a-graph-is.md) | Vertices and edges; directed, undirected, weighted; edge list vs adjacency matrix vs adjacency list and their costs; building graphs from input; grids as implicit graphs; a slow but honest reachability check | Find if path exists, town judge, star center |
| 2 | [Depth-First Search](02-dfs.md) | DFS traced step by step; recursive vs explicit stack vs stack of frames; recursion limits; components; flood fill; path recovery; undirected cycles (with parallel edges); directed cycles with three colors; entry and exit times | Number of islands, max area of island, graph valid tree, course schedule |
| 3 | [Breadth-First Search](03-bfs.md) | BFS traced with its queue; why the first visit is the shortest; marking on enqueue; grid BFS; multi-source BFS with layer counting; word ladder; two-coloring; BFS vs DFS | Shortest path in binary matrix, rotting oranges, 01 matrix, word ladder, is graph bipartite |
| 4 | [State-Space Search](04-state-space-search.md) | What a state must remember; counting states; dominance; backtracking (permutations, subsets, simple paths); pruning (N-queens, word search); bidirectional BFS; a preview of A\* | Obstacles elimination, visit all nodes, N-queens, word search, open the lock |

## Recognizing the pattern

| The problem says… | Model | Tool | Cost | Chapter |
|---|---|---|---:|---|
| "Can I get from A to B?", "how many groups?" | Graph or grid | DFS or BFS from every unvisited vertex | O(V + E) | [2](02-dfs.md) |
| "Fill / count regions of a grid" | Grid as implicit graph | Flood fill with an explicit stack | O(RC) | [2](02-dfs.md#4-variant-flood-fill-and-number-of-islands) |
| "Is there a cycle?" (undirected) | Edges with ids | DFS, skip only the arrival edge | O(V + E) | [2](02-dfs.md#6-cycles-in-an-undirected-graph) |
| "Is there a circular dependency?" | Directed graph | DFS with white/gray/black | O(V + E) | [2](02-dfs.md#7-cycles-in-a-directed-graph) |
| "Fewest moves / steps / hops" (every move costs 1) | Unweighted graph | BFS | O(V + E) | [3](03-bfs.md) |
| "Distance to the nearest X", "how many minutes until it spreads" | Many starting points | Multi-source BFS, layer by layer | O(V + E) | [3](03-bfs.md#6-many-sources-at-once-rotting-oranges) |
| "Change one letter / digit at a time" | Implicit graph of strings | BFS with generated neighbors | O(N · L²) | [3](03-bfs.md#7-an-implicit-graph-of-words-word-ladder) |
| "Split into two groups with no conflict inside a group" | Undirected graph | Two-coloring with BFS or DFS | O(V + E) | [3](03-bfs.md#8-two-coloring-is-the-graph-bipartite) |
| "Fewest moves, but you carry keys / budget / fuel" | State = (place, extra info) | BFS on the state space | O(states × moves) | [4](04-state-space-search.md) |
| "List all orderings / subsets / placements" | Tree of partial choices | Backtracking with undo and pruning | Output-sized, often exponential | [4](04-state-space-search.md#4-backtracking-listing-every-answer) |
| "Fewest moves" with a huge space and a known goal | Implicit graph | Bidirectional BFS | Often about `b^(d/2)` | [4](04-state-space-search.md#6-bidirectional-bfs-search-from-both-ends) |
| Edges have different costs | Weighted graph | Not BFS: see [Shortest Paths](../04-shortest-paths/README.md) | | |

## Conventions

- Vertices are numbered `0..V-1`; `adj[u]` lists the neighbors of `u`. An undirected edge is stored in both lists. `E` counts edges once.
- Unreachable distances are `-1` in this subfolder (BFS) unless a chapter says otherwise.
- Searches that may go deep use an explicit stack. The "stack of frames" pattern, `(vertex, iterator over its neighbors)`, reproduces recursive DFS exactly, including finishing order. Recursion is used only where the depth is small (backtracking over at most a dozen or so levels).
- Every Python block is a complete script with its own asserts, most comparing against a brute force on random small inputs. The slow reachability scan of Chapter 1 (§6) is the brute force behind many of them.

## Connections

- [Trees](../../03-trees/01-binary-trees-and-traversals.md): DFS on a tree needs no visited set; preorder and postorder are entry and finish order.
- [Connectivity and Ordering](../02-connectivity-and-ordering/README.md): DSU, topological sort, strongly connected components, and bridges all build on DFS and BFS.
- [Shortest Paths](../04-shortest-paths/README.md): BFS generalizes to 0–1 BFS and Dijkstra when edges have weights.
- [Dynamic Programming](../../09-dynamic-programming/README.md): BFS over states with memo-like `seen` sets is close to DP; bitmask states reappear in bitmask DP.
- [Bit Manipulation](../../11-bit-manipulation/README.md): visited-set masks.
- [AI search notes](../../../Foundation%20of%20AI/01-search.md): uninformed and heuristic search from the AI perspective.

## Practice order

1. Find if path exists in graph → number of islands → max area of island → flood fill
2. Number of connected components → graph valid tree → keys and rooms
3. Course schedule (directed cycle) → surrounded regions → number of closed islands
4. Shortest path in binary matrix → rotting oranges → 01 matrix → as far from land as possible
5. Word ladder → is graph bipartite → possible bipartition
6. Shortest path with obstacles elimination → shortest path visiting all nodes → shortest path to get all keys
7. Subsets → permutations → combination sum → N-queens → word search
8. Open the lock (try bidirectional BFS) → sliding puzzle
