# Algorithms — From Zero to Deep, by Problem Pattern

Every chapter starts from a concrete problem, introduces the ideas that solve it, shows their variants on the same example, and summarizes at the end. Every code block is a runnable Python script that checks itself against a brute force.

## Topics in learning order

| # | Folder | What you will learn |
|---|---|---|
| 1 | [Binary search](01-binary-search/README.md) | Halving a search space, boundaries (lower/upper bound), searching on the answer, rotated arrays, real-valued and ternary search |
| 2 | [Linked lists](02-linked-lists/README.md) | Nodes and pointers, dummy heads, reversal, fast and slow pointers, merging and sorting lists, LRU cache |
| 3 | [Trees](03-trees/README.md) | Binary trees, traversals, recursion on trees, binary search trees, construction and LCA, tries, balanced trees |
| 4 | [Range queries](04-range-queries/README.md) | Prefix sums, difference arrays, Fenwick trees, segment trees, lazy propagation, sparse tables |
| 5 | [Two pointers and sliding window](05-sliding-window/README.md) | Opposite-end pointers, fixed and variable windows, frequency windows, exact-k counting, windows with negative values |
| 6 | [Stacks, queues, monotonic stacks and deques](06-monotonic-stack-and-deque/README.md) | Stack and queue basics, next greater element, window extrema, histograms, contribution counting |
| 7 | [Heaps and priority queues](07-heaps-and-priority-queues/README.md) | Binary heaps from scratch, top-k, streaming medians, merging k lists, greedy scheduling, indexed heaps |
| 8 | [Sweep line](08-sweep-line/README.md) | Events and endpoint ties, interval scenarios, offline queries, rectangle area and perimeter, skyline, closest pair, angular sweep |
| 9 | [Dynamic programming](09-dynamic-programming/README.md) | From recursion to tables; knapsack, grids, sequences, intervals, trees, bitmasks, digits, games, probability, faster transitions |
| 10 | [Graphs](10-graphs/README.md) | BFS/DFS, state-space search, union-find, topological order, SCCs, bridges, MSTs, shortest paths, general trees and LCA, flows |
| 11 | [Bit manipulation](11-bit-manipulation/README.md) | Binary numbers, everyday bit tricks, XOR puzzles and bases, masks and subset enumeration |
| 12 | [Math and geometry](12-math-and-geometry/README.md) | Number theory, combinatorics, computational geometry, and counting distributions (balls into boxes, partitions, generating functions) |

## Suggested path

You don't have to finish one folder before starting the next:

1. **Start here:** binary search (1), linked lists (2), binary trees and tree recursion (3, chapters 1–3), prefix sums (4, chapter 1), two pointers and sliding window (5), stacks and queues (6).
2. **Core structures:** the rest of trees (3) and range queries (4), heaps (7), and the first chapters of graphs (10: BFS, DFS, union-find).
3. **Core techniques:** dynamic programming chapters 1–8 (9), shortest paths and MSTs (10), sweep line (8).
4. **Deep end:** advanced DP (9, chapters 9–12), advanced graphs (10), bit manipulation (11), math and geometry (12).

Chapter 1 of every folder assumes no background.

## Choose a technique from the problem

| Signal in the problem | Technique to investigate | Condition to check first |
|---|---|---|
| Sorted data, or a yes/no question that flips once as a number grows | Binary search | Is the predicate monotone? |
| Nodes linked by `next` pointers; reorder or detect cycles | Linked-list pointers | Keep a handle on `next` before rewiring |
| Hierarchies, nested structure, a root with children | Tree recursion | What must each call return to its parent? |
| Ordered data with inserts and deletes, prefix lookups on strings | BST / balanced tree / trie | Do you need order, rank, or prefixes? |
| Repeated sums over ranges | Prefix sums / Fenwick / segment tree | Static or changing data? Which aggregate? |
| A contiguous interval that grows and shrinks | Sliding window | Does validity change monotonically as endpoints move? |
| Pairs in a sorted array | Two pointers | Does moving one pointer rule out a whole row of pairs? |
| Nearest greater/smaller value, or a moving-window max/min | Monotonic stack / deque | Which equal value owns a tie? |
| Repeatedly take the smallest/largest, top-k, merge sorted streams | Heap | Do you need the full order, or only the current best? |
| Many intervals or events along an axis | Sweep line | Endpoint semantics and same-coordinate event order |
| Choices lead to repeated smaller subproblems | Dynamic programming | Does the state contain everything the future needs? |
| Objects connected by relations or moves | Graph search and graph algorithms | Directed? Weighted? What exactly is a vertex? |
| Sets of up to ~20 items, XOR, parity, powers of two | Bit manipulation | Fixed width or Python's unbounded integers? |
| Divisibility, primes, counting arrangements, points and polygons | Math and geometry | Exact integers or floating point? |

These patterns combine. Rectangle union uses a sweep plus a segment tree; shortest subarray with negative numbers uses prefix sums plus a monotonic deque; Dijkstra is BFS with a heap; an implicit graph can carry DP over its states.

## Reading and running examples

- Code uses Python 3.10+ and only the standard library. Copy any complete block into a file and run it with `python3 filename.py`; its assertions check the result.
- Indexing is zero-based. Python slices and most intervals are half-open `[l, r)`; the range-query APIs use inclusive `[l, r]`. Every chapter labels which one it uses.
- Complexity statements name their parameters (`n`, `q`, `V`, `E`, …).
- Practice lists are progressions of patterns. Work out why a technique applies before treating a problem name as a template.
- [REVIEW-CHECKLIST.md](REVIEW-CHECKLIST.md) tracks which chapters have been reviewed.
