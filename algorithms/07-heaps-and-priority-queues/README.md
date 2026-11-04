# Heaps and Priority Queues — From Zero to Advanced

A priority queue answers one question over and over: "of everything waiting, which item is most urgent right now?", while items keep arriving. A binary heap answers it in O(log n) per operation by keeping a complete binary tree, stored in a plain list, only partly sorted: every parent is no larger than its children. The same structure solves top-k queries, running medians, k-way merges, greedy scheduling, and the priority-queue graph algorithms (Dijkstra, Prim); the advanced end covers lazy deletion, indexed priority queues, `d`-ary heaps, mergeable heaps and Fibonacci-heap bounds.

> **Learning path:** [Trees](../03-trees/README.md) (vocabulary) → [1 What a Heap Is](01-what-a-heap-is.md) → [2 Top-K and Streams](02-top-k-and-streams.md) → [3 Merging and Scheduling](03-merging-and-scheduling.md) → [4 Advanced Heaps](04-advanced-heaps.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [What a Heap Is](01-what-a-heap-is.md) | Sorted vs unsorted list vs heap; the complete tree in a list; sift-up and sift-down traced; a `MinHeap` from scratch; O(n) build-heap; heap sort; `heapq`, negation for max-heaps, counters for ties, `heapreplace`/`heappushpop`/`nlargest` | Help desk, heap sort |
| 2 | [Top-K and Streams](02-top-k-and-streams.md) | Size-`k` heaps and why "k largest" uses a min-heap; quickselect and buckets as alternatives; two heaps for a running median; lazy deletion for a sliding window | Kth largest, top k frequent, k closest points, nearly sorted array, median of a stream, sliding window median |
| 3 | [Merging and Scheduling](03-merging-and-scheduling.md) | The heap as "best available choice"; k-way merge; greedy algorithms with exchange arguments | Merge k sorted lists, kth smallest in a sorted matrix, smallest range, task scheduler, reorganize string, meeting rooms, IPO, course schedule III, connect sticks, Huffman coding |
| 4 | [Advanced Heaps](04-advanced-heaps.md) | Lazy deletion in general; decrease-key and Dijkstra's re-insertion; an indexed priority queue; `d`-ary heaps; leftist heaps; Fibonacci heap bounds | Removable heap, Dijkstra, Prim, mergeable priority queues |

Chapters 2 and 3 build on chapter 1 and can be read in either order. Chapter 4 is the advanced part and uses all three.

## Recognizing the pattern

| The problem says or implies… | Heap shape | Typical cost | Where |
|---|---|---:|---|
| "Repeatedly take the smallest/largest" while items keep arriving | One min-heap (negate for max) | O(log n) per operation | [1](01-what-a-heap-is.md) |
| "k-th largest", "top k", "k closest" | Size-`k` heap whose root is the weakest kept item | O(n log k) | [2 §1–§2](02-top-k-and-streams.md#1-the-k-th-largest-element) |
| Each element is at most `k` places out of order | Heap of `k + 1` | O(n log k) | [2 §3](02-top-k-and-streams.md#3-sorting-a-nearly-sorted-array) |
| Median, or any fixed percentile, of a growing collection | Max-heap of the lower part, min-heap of the upper part | O(log n) per insert | [2 §4](02-top-k-and-streams.md#4-median-of-a-data-stream) |
| Values leave a window from the middle of a heap | Lazy deletion with a counter | O(n log n) | [2 §5](02-top-k-and-streams.md#5-sliding-window-median-and-lazy-deletion), [4 §1](04-advanced-heaps.md#1-lazy-deletion-in-general) |
| Several sorted sources, produce them in order | One entry per source; pop and push its successor | O(N log k) | [3 §1–§3](03-merging-and-scheduling.md#1-merge-k-sorted-lists) |
| "Most frequent first, with a cooldown" | Max-heap of counts plus a waiting queue | O(T log σ) | [3 §4](03-merging-and-scheduling.md#4-task-scheduler-and-reorganize-string) |
| Intervals sorted by start; reuse whatever frees first | Min-heap of end times | O(n log n) | [3 §5](03-merging-and-scheduling.md#5-meeting-rooms-a-heap-of-end-times) |
| Options unlock over time; take the best unlocked one | Sorted list feeding a max-heap | O(n log n) | [3 §6](03-merging-and-scheduling.md#6-ipo-two-heaps-for-affordable-and-best) |
| Keep a feasible set; when it breaks, drop the worst member | Max-heap of the chosen items | O(n log n) | [3 §7](03-merging-and-scheduling.md#7-course-schedule-iii-greedy-with-an-exchange-argument) |
| Repeatedly combine the two smallest | Min-heap | O(n log n) | [3 §8](03-merging-and-scheduling.md#8-connect-sticks-and-huffman-coding) |
| Priorities change after insertion | Re-insert with a stale check, or an indexed queue | O(log n) per change | [4 §2–§3](04-advanced-heaps.md#2-decrease-key-and-why-pythons-dijkstra-re-inserts) |
| Whole heaps must be merged often | Leftist or pairing heap | O(log n) merge | [4 §5](04-advanced-heaps.md#5-mergeable-heaps-the-leftist-heap) |

When the question is about **all** items in order, `sorted` is usually simpler. When the "most urgent" item is always the newest or the oldest, a stack or queue is enough. When you need both the minimum and the maximum of a window that slides by one, a monotonic deque does it in O(1) amortized ([Monotonic Stacks and Deques](../06-monotonic-stack-and-deque/README.md)).

## Conventions

- **Min-heap by default**, matching Python's `heapq`. Max-heaps store negated numbers; every chapter negates on the way in and on the way out.
- Zero-based list layout: children of `i` at `2i + 1` and `2i + 2`, parent at `(i − 1) // 2`. Only `heap[0]` has a guaranteed meaning.
- Heap entries that may tie are tuples with a tie-breaker in second place: a list index, a position, or a running counter. Payloads that cannot be compared (nodes, dictionaries) never reach a comparison.
- Intervals are half-open `[start, end)` unless a section says otherwise; a meeting ending at 10 frees its room for one starting at 10.
- Every Python block is a complete runnable script using only the standard library. Each compares the heap solution with a brute force (sorting, exhaustive search, or a simple model) on fixed-seed random inputs, including empty inputs, duplicates and negative values.
- Running times name their parameters: `n` items, `k` heap size or number of lists, `N` total items across lists, `V` and `E` vertices and edges.

## How to study

1. Read chapter 1 with paper. Redraw the sift-up and sift-down traces from §4–§5 in both the tree and the list form before reading the code.
2. For each problem in chapters 2 and 3, decide **what one heap entry represents** and **what the root means** before reading the solution. "The root is the weakest of the top k" or "the root is the source whose next item comes first" is the sentence the code follows from.
3. For greedy sections, read the correctness argument and then try to break it: change the greedy rule (drop the newest course instead of the longest, join the two largest sticks) and watch the brute-force comparison fail.
4. Chapter 4 is optional for interviews except §2 (Dijkstra's re-insertion), which you will use constantly.

## Connections to other topics

- [Trees](../03-trees/README.md): binary-tree vocabulary (root, leaf, height, complete tree). A heap is a complete binary tree with a weaker order than a binary search tree: it finds the minimum in O(1) but cannot search for an arbitrary value.
- [Sweep Line](../08-sweep-line/README.md): meeting rooms, room assignment, skylines and "smallest interval containing a query" all sweep sorted events and keep the active set in a heap with lazy expiration.
- [Graphs](../10-graphs/README.md): Dijkstra's shortest paths and Prim's minimum spanning tree are priority-queue algorithms; [Advanced Heaps §2–§3](04-advanced-heaps.md#2-decrease-key-and-why-pythons-dijkstra-re-inserts) explains the decrease-key choices they depend on.
- [Linked Lists](../02-linked-lists/README.md): merging k sorted linked lists uses a heap of nodes with a counter for ties ([Merging and Scheduling §1](03-merging-and-scheduling.md#1-merge-k-sorted-lists)); merging two lists is the pointer exercise underneath.
- [Sliding Window](../05-sliding-window/README.md): the sliding window median combines a fixed-size window with two heaps and lazy deletion.
- [Binary Search](../01-binary-search/README.md): the k-th smallest in a sorted matrix can also be found by binary searching on the value.
- [Dynamic Programming](../09-dynamic-programming/README.md): Dijkstra is DP over a graph whose evaluation order is discovered by the heap.

## Practice order

1. **Basics:** last stone weight; kth largest element in a stream; implement heap sort; check whether a list is a valid heap.
2. **Top-k:** kth largest element in an array (heap and quickselect); top k frequent elements; top k frequent words; k closest points to origin; find k closest elements.
3. **Two heaps:** find median from data stream; sliding window median; IPO.
4. **Merging:** merge k sorted lists; kth smallest element in a sorted matrix; find k pairs with smallest sums; smallest range covering elements from k lists.
5. **Scheduling and greedy:** meeting rooms II; task scheduler; reorganize string; single-threaded CPU; course schedule III; minimum cost to connect sticks; minimum cost to hire k workers.
6. **Graphs and advanced:** network delay time; path with minimum effort; cheapest flights within k stops; Prim's algorithm with an indexed priority queue.
