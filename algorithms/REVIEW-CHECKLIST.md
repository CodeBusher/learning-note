# Review Checklist

Tracks my review of the algorithms notes. Tick a box once a chapter has been read end to end, its examples make sense from zero, and its code blocks run. Each folder ends with a check that its README still describes the chapters, plus a place for notes.

## What "reviewed" means

For each chapter:

1. It opens with the real problem and needs nothing from later chapters.
2. Every trace can be followed by hand, and the code matches the trace.
3. Ideas come first, variants are shown on examples, and the summary comes at the end.
4. Nothing obvious takes up space; the length goes to the hard parts.
5. Anything to change goes under that folder's **Notes**, or inline as a `[** ...]` comment in the chapter.

Progress: count the ticked boxes with

```bash
grep -c '^\s*- \[x\]' algorithms/REVIEW-CHECKLIST.md
```

out of **107** items.

- [ ] [Top-level README](README.md) — learning order, suggested path, technique table

## Binary Search — From Sorted Arrays to Searching on Answers

- [ ] [The Idea of Binary Search — Throw Away Half, Keep the Range Honest](01-binary-search/01-the-idea.md) · 250 lines
- [ ] [Boundaries — Lower Bound, Upper Bound, and the First True](01-binary-search/02-boundaries.md) · 451 lines
- [ ] [Search on the Answer — Binary Search Over a Yes/No Question](01-binary-search/03-search-on-the-answer.md) · 382 lines
- [ ] [Beyond Sorted Arrays — Rotations, Peaks, Matrices and Medians](01-binary-search/04-beyond-sorted-arrays.md) · 450 lines
- [ ] [Real Numbers and Unbounded Ranges — Bisection, Ternary Search, Galloping](01-binary-search/05-reals-ternary-and-unbounded.md) · 299 lines
- [ ] [Folder README](01-binary-search/README.md) still matches the chapters

**Notes:**

- 

## Linked Lists — Pointers, Dummy Nodes, Fast/Slow, Reversal

- [ ] [Nodes and Pointers — Building, Walking, and Editing a Linked List](02-linked-lists/01-nodes-and-pointers.md) · 603 lines
- [ ] [Reversal — Turning Arrows Around Without Losing the List](02-linked-lists/02-reversal.md) · 488 lines
- [ ] [Fast and Slow Pointers — Finding Positions by Moving at Different Speeds](02-linked-lists/03-fast-and-slow-pointers.md) · 517 lines
- [ ] [Merging and Design — Splicing Lists and Building an LRU Cache](02-linked-lists/04-merging-and-design.md) · 885 lines
- [ ] [Folder README](02-linked-lists/README.md) still matches the chapters

**Notes:**

- 

## Trees — Traversals, Tree Recursion, BSTs, Tries, Balanced Trees

- [ ] [Binary Trees and Traversals — Building a Tree and Visiting Every Node](03-trees/01-binary-trees-and-traversals.md) · 480 lines
- [ ] [Recursion on Trees — Decide What Each Call Returns](03-trees/02-recursion-on-trees.md) · 448 lines
- [ ] [Binary Search Trees — Sorted Order You Can Insert Into](03-trees/03-binary-search-trees.md) · 487 lines
- [ ] [Construction, Paths and LCA — Rebuilding Trees and Asking About Paths](03-trees/04-construction-paths-and-lca.md) · 532 lines
- [ ] [Tries — A Tree Keyed by Letters](03-trees/05-tries.md) · 312 lines
- [ ] [Balanced Trees — Rotations, Treaps and AVL Trees (Advanced)](03-trees/06-balanced-trees.md) · 497 lines
- [ ] [Folder README](03-trees/README.md) still matches the chapters

**Notes:**

- 

## Range Queries — Prefix Sums, Fenwick Trees, Segment Trees

- [ ] [Prefix Sums and Difference Arrays — Answer Range Questions with One Subtraction](04-range-queries/01-prefix-sums.md) · 771 lines
- [ ] [Fenwick Tree — Prefix Sums That Survive Updates](04-range-queries/02-fenwick-tree.md) · 878 lines
- [ ] [Segment Tree — Any Range Summary, Any Update](04-range-queries/03-segment-tree.md) · 1069 lines
- [ ] [Sparse Table and Square-Root Decomposition — Trading Generality for Simplicity](04-range-queries/04-sparse-table-and-sqrt.md) · 475 lines
- [ ] [Folder README](04-range-queries/README.md) still matches the chapters

**Notes:**

- 

## Two Pointers and Sliding Window — Move Forward, Never Back

- [ ] [Two Pointers — Discard Candidates Without Checking Them](05-sliding-window/01-two-pointers.md) · 524 lines
- [ ] [Fixed and Variable Windows — Why the Left End Never Moves Back](05-sliding-window/02-fixed-and-variable-windows.md) · 481 lines
- [ ] [Counting and Frequency Windows — Count Every Window, Track Every Letter](05-sliding-window/03-counting-and-frequency-windows.md) · 501 lines
- [ ] [Advanced Window Patterns — When the Simple Proof Bends or Breaks](05-sliding-window/04-advanced-patterns.md) · 509 lines
- [ ] [Folder README](05-sliding-window/README.md) still matches the chapters

**Notes:**

- 

## Monotonic Stacks and Deques — Keep Only the Candidates That Can Still Win

- [ ] [Stacks and Queues — Last In First Out, First In First Out](06-monotonic-stack-and-deque/01-stacks-and-queues.md) · 435 lines
- [ ] [Monotonic Stack — The Nearest Greater or Smaller Neighbor](06-monotonic-stack-and-deque/02-monotonic-stack.md) · 407 lines
- [ ] [Stack Applications — Greedy Removal, Trapped Water, Patterns, Fleets](06-monotonic-stack-and-deque/03-stack-applications.md) · 484 lines
- [ ] [Monotonic Deque — The Best Candidate in a Moving Window](06-monotonic-stack-and-deque/04-monotonic-deque.md) · 493 lines
- [ ] [Contributions and Boundaries — How Far Can Each Element Reach?](06-monotonic-stack-and-deque/05-contributions-and-boundaries.md) · 436 lines
- [ ] [Folder README](06-monotonic-stack-and-deque/README.md) still matches the chapters

**Notes:**

- 

## Heaps and Priority Queues — From Zero to Advanced

- [ ] [What a Heap Is — Always Serve the Most Urgent Task](07-heaps-and-priority-queues/01-what-a-heap-is.md) · 434 lines
- [ ] [Top-K and Streams — Keep Only What Can Still Win](07-heaps-and-priority-queues/02-top-k-and-streams.md) · 512 lines
- [ ] [Merging and Scheduling — A Heap as the Next-Event Chooser](07-heaps-and-priority-queues/03-merging-and-scheduling.md) · 637 lines
- [ ] [Advanced Heaps — Deleting, Updating, and Merging](07-heaps-and-priority-queues/04-advanced-heaps.md) · 589 lines
- [ ] [Folder README](07-heaps-and-priority-queues/README.md) still matches the chapters

**Notes:**

- 

## Sweep Line — Events, Active Sets, and Scenario Catalog

- [ ] [Your First Sweep — Overlap and Union of Intervals](08-sweep-line/01-first-sweep-intervals.md) · 269 lines
- [ ] [Endpoint Semantics — Ties, Closed Intervals, and Point Queries](08-sweep-line/02-endpoint-semantics-and-queries.md) · 244 lines
- [ ] [Designing a Sweep — Events, Invariants, and Honest Analysis](08-sweep-line/03-designing-a-sweep.md) · 96 lines
- [ ] [Interval Scenarios — Assignment, Intersection, Gaps, Greedy, and Online Bookings](08-sweep-line/04-interval-scenarios.md) · 433 lines
- [ ] [Offline Sweeps — Remove One Dimension by Sorting](08-sweep-line/05-offline-sweeps-and-fenwick.md) · 469 lines
- [ ] [Geometric Sweeps — Area, Perimeter, Skyline, and Tilings](08-sweep-line/06-geometric-sweeps.md) · 637 lines
- [ ] [Ordered-Set and Angular Sweeps — Closest Pair, Segment Intersection, and Directions](08-sweep-line/07-ordered-set-and-angular-sweeps.md) · 288 lines
- [ ] [Folder README](08-sweep-line/README.md) still matches the chapters

**Notes:**

- 

## Dynamic Programming — From Zero to Advanced

- [ ] [What Dynamic Programming Is — From Recursion to a Table](09-dynamic-programming/01-what-is-dp.md) · 284 lines
- [ ] [Designing a Recurrence — The Last-Decision Method](09-dynamic-programming/02-designing-a-recurrence.md) · 359 lines
- [ ] [Choosing the State and Rebuilding the Answer — What to Remember, and How to Get the Solution Back](09-dynamic-programming/03-states-and-reconstruction.md) · 450 lines
- [ ] [Knapsack and Coins — Choosing Items Under a Budget](09-dynamic-programming/04-knapsack-and-coins.md) · 892 lines
- [ ] [Grid DP — Paths Through a Rectangle](09-dynamic-programming/05-grid-dp.md) · 765 lines
- [ ] [Sequences and Strings — Prefixes, Endings, and Matches](09-dynamic-programming/06-sequences-and-strings.md) · 809 lines
- [ ] [Interval DP — Solve Short Pieces, Then Glue Them](09-dynamic-programming/07-interval-dp.md) · 567 lines
- [ ] [Tree and DAG DP — Solve Every Subtree Once](09-dynamic-programming/08-tree-and-dag-dp.md) · 946 lines
- [ ] [Bitmask DP — When the State Is a Set](09-dynamic-programming/09-bitmask-dp.md) · 598 lines
- [ ] [Digit DP — Counting Numbers Under a Bound](09-dynamic-programming/10-digit-dp.md) · 639 lines
- [ ] [Games and Probability — Opponents and Dice](09-dynamic-programming/11-games-and-probability.md) · 729 lines
- [ ] [Faster Transitions — Same Recurrence, Cheaper Best Predecessor](09-dynamic-programming/12-faster-transitions.md) · 779 lines
- [ ] [Folder README](09-dynamic-programming/README.md) still matches the chapters

**Notes:**

- 

## Graph Algorithms — From First Traversal to Flows

**Search and Traversal — Exploring a Graph from Zero**

- [ ] [What a Graph Is — Vertices, Edges, and How to Store Them](10-graphs/01-search-and-traversal/01-what-a-graph-is.md) · 319 lines
- [ ] [Depth-First Search — Go Deep, Then Back Up](10-graphs/01-search-and-traversal/02-dfs.md) · 656 lines
- [ ] [Breadth-First Search — Layer by Layer, Fewest Edges First](10-graphs/01-search-and-traversal/03-bfs.md) · 493 lines
- [ ] [State-Space Search — Choosing What a Vertex Remembers](10-graphs/01-search-and-traversal/04-state-space-search.md) · 741 lines
- [ ] [Section README](10-graphs/01-search-and-traversal/README.md) still matches the chapters

**Connectivity and Ordering — Groups, Dependencies, and Weak Spots**

- [ ] [Disjoint Set Union — Merging Groups as Edges Arrive](10-graphs/02-connectivity-and-ordering/01-disjoint-set-union.md) · 656 lines
- [ ] [Topological Sort and Strongly Connected Components — Order and Cycles in Directed Graphs](10-graphs/02-connectivity-and-ordering/02-topological-sort-and-scc.md) · 671 lines
- [ ] [Bridges and Articulation Points — Single Points of Failure](10-graphs/02-connectivity-and-ordering/03-bridges-and-articulation.md) · 474 lines
- [ ] [Section README](10-graphs/02-connectivity-and-ordering/README.md) still matches the chapters

**Minimum Spanning Trees — Connect Everything at the Lowest Total Cost**

- [ ] [Spanning Trees — Connecting Everything at Minimum Cost](10-graphs/03-minimum-spanning-trees/01-spanning-trees.md) · 179 lines
- [ ] [The Cut and Cycle Properties — Which Edges Are Safe](10-graphs/03-minimum-spanning-trees/02-cut-and-cycle-properties.md) · 281 lines
- [ ] [Kruskal's Algorithm — Cheapest Edge First, Skip Cycles](10-graphs/03-minimum-spanning-trees/03-kruskal.md) · 349 lines
- [ ] [Prim's Algorithm — Grow One Tree Outward](10-graphs/03-minimum-spanning-trees/04-prim.md) · 249 lines
- [ ] [Variants and Spanning Forests — Beyond One Connected Tree](10-graphs/03-minimum-spanning-trees/05-forests-and-variants.md) · 599 lines
- [ ] [Section README](10-graphs/03-minimum-spanning-trees/README.md) still matches the chapters

**Shortest Paths — The Cheapest Route, Under Every Kind of Edge Weight**

- [ ] [BFS and 0–1 BFS — Shortest Paths Without a Heap](10-graphs/04-shortest-paths/01-bfs-and-zero-one-bfs.md) · 359 lines
- [ ] [Dijkstra's Algorithm — Finalize the Closest Vertex First](10-graphs/04-shortest-paths/02-dijkstra.md) · 313 lines
- [ ] [Negative Weights and All Pairs — DAGs, Bellman–Ford, Floyd–Warshall](10-graphs/04-shortest-paths/03-negative-weights-and-all-pairs.md) · 647 lines
- [ ] [Modeling with State Graphs — Dijkstra Variants and A*](10-graphs/04-shortest-paths/04-modeling-and-variants.md) · 552 lines
- [ ] [Section README](10-graphs/04-shortest-paths/README.md) still matches the chapters

**Trees and Advanced Topics — Rooted Trees, Flows, Matchings, Euler Paths**

- [ ] [Rooting a Tree and Lowest Common Ancestors — Jumping Up in Powers of Two](10-graphs/05-trees-and-advanced/01-rooting-and-lca.md) · 628 lines
- [ ] [Tree Diameter and Centers — The Longest Route in Linear Time](10-graphs/05-trees-and-advanced/02-tree-diameter.md) · 276 lines
- [ ] [Maximum Flow and Bipartite Matching — Augmenting Paths (Advanced)](10-graphs/05-trees-and-advanced/03-flow-and-matching.md) · 372 lines
- [ ] [Euler Paths and Further Topics — Using Every Edge Once (Advanced)](10-graphs/05-trees-and-advanced/04-euler-paths-and-roadmap.md) · 258 lines
- [ ] [Section README](10-graphs/05-trees-and-advanced/README.md) still matches the chapters

- [ ] [Folder README](10-graphs/README.md) still matches the chapters

**Notes:**

- 

## Bit Manipulation — Binary, Tricks, XOR, and Masks

- [ ] [Binary Numbers — Bits, Operators, and Negative Numbers](11-bit-manipulation/01-binary-numbers.md) · 355 lines
- [ ] [Everyday Bit Tricks — Single Bits, Lowest Bits, and Counting](11-bit-manipulation/02-everyday-tricks.md) · 560 lines
- [ ] [XOR — Cancelling Pairs, Prefix XOR, Tries, and Linear Bases](11-bit-manipulation/03-xor.md) · 665 lines
- [ ] [Masks and Subsets — Sets as Integers, Submasks, Gray Codes, Bitsets](11-bit-manipulation/04-masks-and-subsets.md) · 565 lines
- [ ] [Folder README](11-bit-manipulation/README.md) still matches the chapters

**Notes:**

- 

## Math and Geometry — Number Theory, Counting, and Computational Geometry

**Counting Distributions — Balls into Boxes, Partitions, Generating Functions**

- [ ] [Four Ways to Put 4 Balls in 2 Boxes — Distinct or Identical, Labeled or Not](12-math-and-geometry/04-counting-distributions/01-modeling.md) · 107 lines
- [ ] [Labeled Boxes, Identical Items — Stars and Bars, Capacities, Prefix-Sum DP](12-math-and-geometry/04-counting-distributions/02-labeled-boxes.md) · 187 lines
- [ ] [Generating Functions — Choices as Factors, Factors as DP Passes](12-math-and-geometry/04-counting-distributions/03-generating-functions.md) · 211 lines
- [ ] [Identical Boxes: Integer Partitions — Ferrers Diagrams and Coin-Change DP](12-math-and-geometry/04-counting-distributions/04-integer-partitions.md) · 200 lines
- [ ] [Distinct Items: Set Partitions — Surjections, Exponential Generating Functions, Stirling Numbers](12-math-and-geometry/04-counting-distributions/05-set-partitions.md) · 197 lines
- [ ] [Synthesis — A Modeling Checklist and the Four Cases Side by Side](12-math-and-geometry/04-counting-distributions/06-synthesis.md) · 116 lines
- [ ] [Constraints on the Boxes — Nonempty Counts and Capacities](12-math-and-geometry/04-counting-distributions/07-box-constraints.md) · 95 lines
- [ ] [Constraints on Part Sizes — Allowed Sizes, Multiplicity Caps, Distinct Parts](12-math-and-geometry/04-counting-distributions/08-part-size-constraints.md) · 277 lines
- [ ] [Advanced Topics — Pentagonal Numbers, Burnside's Lemma, Other Partition Families](12-math-and-geometry/04-counting-distributions/09-advanced-topics.md) · 183 lines
- [ ] [Toolkit — Tested Code, Worked Traps, Cheat Sheet](12-math-and-geometry/04-counting-distributions/10-toolkit.md) · 350 lines
- [ ] [Section README](12-math-and-geometry/04-counting-distributions/README.md) still matches the chapters

- [ ] [Number Theory — Remainders, GCD, Primes, and Modular Arithmetic](12-math-and-geometry/01-number-theory.md) · 705 lines
- [ ] [Combinatorics — Counting Without Listing](12-math-and-geometry/02-combinatorics.md) · 580 lines
- [ ] [Computational Geometry — Vectors, Orientation, Polygons, and Hulls](12-math-and-geometry/03-geometry.md) · 674 lines
- [ ] [Folder README](12-math-and-geometry/README.md) still matches the chapters

**Notes:**

- 
