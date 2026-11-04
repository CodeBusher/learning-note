# Range Queries — Prefix Sums, Fenwick Trees, Segment Trees

A range query asks for a summary of a contiguous part of an array: the sum of `a[l..r]`, its minimum, how many values in it are even, how many distinct values it holds. Scanning the range answers any of these in O(n), which is too slow when there are many questions. Each structure here fixes one limitation of the one before it: prefix sums answer static sums with one subtraction; a Fenwick tree keeps those sums correct under updates; a segment tree handles summaries that cannot be subtracted and updates to whole ranges; sparse tables, square-root blocks and Mo's algorithm cover static, awkward or offline cases with less machinery.

> **Learning path:** [Prefix Sums](01-prefix-sums.md) → [Fenwick Tree](02-fenwick-tree.md) → [Segment Tree](03-segment-tree.md) → [Sparse Table and Square-Root Decomposition](04-sparse-table-and-sqrt.md)

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Prefix Sums and Difference Arrays](01-prefix-sums.md) | Running totals; range sum in O(1); counting with 0/1 arrays; difference arrays for batch range updates; 2D prefix sums and 2D difference arrays; prefix sums plus a hash map | Range sum (immutable), 2D range sum, subarray sum equals k, contiguous array, corporate flight bookings |
| 2 | [Fenwick Tree](02-fenwick-tree.md) | Blocks of power-of-two length; `lowbit`; O(log n) point update and prefix sum; O(n) build; range add with one or two trees; counting smaller elements; k-th smallest by binary lifting; 2D Fenwick; prefix maximum | Range sum (mutable), count of smaller numbers after self, reverse pairs, k-th element of a multiset |
| 3 | [Segment Tree](03-segment-tree.md) | Halving the array; queries with three cases; any associative summary; designing node summaries; descending search; lazy propagation with add, and with assign plus add; dynamic and persistent trees (advanced) | Range minimum with updates, maximum subarray in a range, falling squares, my calendar III, k-th smallest in a range |
| 4 | [Sparse Table and Square-Root Decomposition](04-sparse-table-and-sqrt.md) | O(1) static range minimum via overlapping windows; √n blocks with block tags; Mo's algorithm for offline window queries | Static range minimum, range GCD, distinct values in ranges |

## Recognizing the pattern

| The problem says… | Structure | Query | Update |
|---|---|---:|---:|
| Many range sums, array never changes | [Prefix sums](01-prefix-sums.md#3-code-staticrangesum) | O(1) | — |
| Many range additions, read the array once at the end | [Difference array](01-prefix-sums.md#5-difference-arrays-many-range-updates-one-final-read) | O(n) once | O(1) |
| Count subarrays with a given sum, negatives allowed | [Prefix sums + hash map](01-prefix-sums.md#8-counting-subarrays-with-sum-k-prefix-sums-plus-a-hash-map) | O(n) total | — |
| Rectangle sums on a fixed grid | [2D prefix sums](01-prefix-sums.md#6-two-dimensional-prefix-sums) | O(1) | — |
| Point changes mixed with range sums | [Fenwick tree](02-fenwick-tree.md#7-code-fenwick) | O(log n) | O(log n) |
| Range additions mixed with point reads or range sums | [Fenwick on differences](02-fenwick-tree.md#9-range-add-range-sum-two-fenwick-trees) | O(log n) | O(log n) |
| "How many earlier elements are smaller?", k-th smallest so far | [Fenwick over values](02-fenwick-tree.md#10-counting-with-a-fenwick-tree-how-many-smaller-elements) | O(log n) | O(log n) |
| Range min / max / GCD with point changes | [Segment tree](03-segment-tree.md#6-code-a-generic-segment-tree) | O(log n) | O(log n) |
| First position where a running total or value reaches `x` | [Segment tree descent](03-segment-tree.md#9-descending-search-the-first-position-that-meets-a-condition) | O(log n) | O(log n) |
| Range add or range assign mixed with range sum / min | [Lazy segment tree](03-segment-tree.md#10-lazy-propagation-range-add-range-sum) | O(log n) | O(log n) |
| Range min / max on a fixed array, very many queries | [Sparse table](04-sparse-table-and-sqrt.md#5-code-sparsetable) | O(1) | — |
| Offline questions about the contents of a range (distinct values) | [Mo's algorithm](04-sparse-table-and-sqrt.md#8-mos-algorithm-reorder-offline-queries) | O(√n) amortized | — |

Two questions decide most cases: **does the array change between queries?** and **can the summary be undone by subtraction?** Sums, counts and XOR can; minimum, maximum and GCD cannot.

## Conventions

- **Ranges are inclusive** `[l, r]` in every public query and update method: `query(l, r)` includes both `a[l]` and `a[r]`. Most other folders use half-open `[l, r)` intervals ([overview](../README.md)); each chapter here states it again where it matters.
- **Public indices are 0-based** everywhere, including the Fenwick tree. The Fenwick tree numbers its positions from 1 internally, because `lowbit(0) = 0`; its methods convert, and its `prefix_sum(k)` means "the first `k` elements", the same as `P[k]` for prefix sums.
- **Prefix arrays** have a leading zero: `P[0] = 0` and `P[k] = a[0] + … + a[k − 1]`, so `sum(l, r) = P[r + 1] − P[l]`.
- **Code style:** each structure is a class; invalid ranges raise `ValueError`; every script has `main()` with asserts and a fixed-seed random comparison against a brute force.
- Each implementation is followed by its time and space costs, in terms of `n` (array length) and `q` (number of requests).

## Connections to other folders

- [Trees](../03-trees/README.md): binary trees and tree recursion, which the segment tree uses throughout.
- [Sliding Window](../05-sliding-window/README.md): prefix sums plus a hash map handle the sums with negative values that a window cannot; Mo's algorithm reuses the frequency-window bookkeeping.
- [Monotonic Stack and Deque](../06-monotonic-stack-and-deque/README.md): sliding-window maximum is a special case of range maximum, solved in O(n) total with a deque.
- [Sweep Line](../08-sweep-line/README.md): an endpoint sweep is a sparse difference array; offline sweeps pair sorting with a Fenwick tree; area-of-union sweeps keep a segment tree over the cross section.
- [Dynamic Programming](../09-dynamic-programming/README.md): prefix sums, Fenwick trees and segment trees speed up DP transitions that sum or maximize over a range of earlier states.
- [Graphs](../10-graphs/README.md): a DFS entry order turns subtrees into array ranges, and an Euler tour plus a sparse table answers lowest common ancestor queries.
- [Bit Manipulation](../11-bit-manipulation/README.md): [two's complement](../11-bit-manipulation/01-binary-numbers.md) explains `i & -i`.

## Practice order

1. Range sum query, immutable (prefix sums).
2. Range sum query 2D, immutable (inclusion–exclusion).
3. Subarray sum equals k; contiguous array; subarray sums divisible by K (prefix sums plus hash map).
4. Corporate flight bookings; car pooling (difference arrays).
5. Range sum query, mutable (Fenwick tree, then segment tree).
6. Count of smaller numbers after self; reverse pairs (Fenwick over values).
7. Range minimum query with updates; maximum subarray sum in a range (segment tree with summaries).
8. Booking concert tickets in groups (segment tree descent).
9. Falling squares; my calendar III (lazy and dynamic segment trees).
10. Static range minimum; distinct values in ranges (sparse table; Mo's algorithm).
