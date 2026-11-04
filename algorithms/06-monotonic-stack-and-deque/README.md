# Monotonic Stacks and Deques — Keep Only the Candidates That Can Still Win

From the plain stack and queue to the largest rectangle in a histogram and the shortest subarray with sum at least `K` over negative numbers. One idea runs through it, **dominance**: when a new element arrives, some older elements can never be the answer again, for anyone, so they are thrown away for good. A stack throws them away from one end; a deque also lets old candidates expire from the other end. Because every element is added once and removed at most once, loops that look quadratic run in linear time.

> **Learning path:** [Stacks and Queues](01-stacks-and-queues.md) → [Monotonic Stack](02-monotonic-stack.md) → [Stack Applications](03-stack-applications.md) → [Monotonic Deque](04-monotonic-deque.md) → [Contributions and Boundaries](05-contributions-and-boundaries.md)

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Stacks and Queues](01-stacks-and-queues.md) | LIFO and FIFO; `list` versus `collections.deque` costs; amortized analysis | Valid parentheses, min stack, decode string, queue from two stacks |
| 2 | [Monotonic Stack](02-monotonic-stack.md) | Nearest greater or smaller neighbor on either side; the push-once, pop-once argument; strict versus non-strict ties | Daily temperatures, next greater element I and II, online stock span |
| 3 | [Stack Applications](03-stack-applications.md) | Greedy removal with a stack; water by layers versus two pointers; scanning from the right | Remove k digits, remove duplicate letters, trapping rain water, 132 pattern, car fleet |
| 4 | [Monotonic Deque](04-monotonic-deque.md) | Expiry at the front, dominance at the back; deques inside variable windows, DPs and prefix sums | Sliding window maximum, longest subarray with bounded difference, jump game VI, constrained subsequence sum, shortest subarray with sum at least K |
| 5 | [Contributions and Boundaries](05-contributions-and-boundaries.md) | How far each element reaches; counting subarrays per element; exactly one owner for ties | Largest rectangle in histogram, maximal rectangle, sum of subarray minimums, sum of subarray ranges |

Chapter 2 needs chapter 1; chapters 3, 4 and 5 each need chapter 2 and can be read in any order.

## Recognizing the pattern

| The question sounds like… | Tool | Why candidates leave | Where |
|---|---|---|---|
| "Does every opener have a matching closer?", nested structure | Stack | The most recent open item closes first | [1 §1](01-stacks-and-queues.md#1-do-the-brackets-match), [1 §3](01-stacks-and-queues.md#3-variant-decode-string-a-stack-of-unfinished-contexts) |
| "For each element, the nearest bigger / smaller one to the right or left" | Monotonic stack | Answered, or beaten by a newer element | [2 §3](02-monotonic-stack.md#3-worked-trace), [2 §8](02-monotonic-stack.md#8-all-eight-neighbor-queries) |
| "How many consecutive previous days were at most today?", online | Stack of `(value, span)` | Absorbed into a newer, larger value | [2 §5](02-monotonic-stack.md#5-variant-online-stock-span) |
| "Delete `k` items to make the smallest sequence" | Greedy stack | A larger item before a smaller one is worth deleting | [3 §1](03-stack-applications.md#1-remove-k-digits-the-smallest-number-left) |
| "Water between bars" | Stack (layers) or two pointers | A taller right wall closes a pool | [3 §3](03-stack-applications.md#3-trapping-rain-water-three-ways) |
| "Max or min of every window of size `k`" | Monotonic deque | Too old (front) or beaten (back) | [4 §3](04-monotonic-deque.md#3-worked-trace) |
| "Longest window whose max − min stays within a limit" | Two deques plus a variable window | Same as above, with a moving left end | [4 §7](04-monotonic-deque.md#7-a-variable-window-longest-stretch-with-max--min--limit) |
| `dp[i] = value + max(dp[j])` over the last `k` indices | Deque over DP values | Too old, or a newer state is at least as good | [4 §8](04-monotonic-deque.md#8-a-deque-inside-a-dynamic-program) |
| "Shortest subarray with sum at least `K`", negatives allowed | Deque of prefix indices | Used up, or a newer lower prefix is better | [4 §9](04-monotonic-deque.md#9-a-deque-of-prefix-sums-shortest-subarray-with-sum-at-least-k) |
| "Largest rectangle", "for how many subarrays is this the min/max?" | Boundary stack | A smaller element closes its reach | [5 §1](05-contributions-and-boundaries.md#1-largest-rectangle-in-a-histogram), [5 §3](05-contributions-and-boundaries.md#3-sum-of-subarray-minimums-count-each-elements-share) |

A one-line test: if a candidate becomes useless **only because something newer beat it**, a stack is enough. If it can also become useless **because it is too old**, you need a deque.

## Conventions

- Zero-based indexing. A subarray is written `[l..r]` with both ends included, which is `nums[l:r + 1]` in Python. Prefix sums follow [Prefix Sums](../04-range-queries/01-prefix-sums.md): `P[j]` is the sum of the first `j` elements, so `[i..j − 1]` sums to `P[j] − P[i]`.
- Stacks and deques store **indices**, not values. An index gives the value, the position (for distances and widths), and the age (for expiry), and keeps equal values distinct.
- Missing neighbors use the sentinels `−1` (nothing to the left) and `n` (nothing to the right). They are never used to index the array; in Python `nums[−1]` would silently read the last element.
- Every comparison states its strictness in words first ("strictly greater", "greater or equal"), and every chapter tests runs of equal values.
- Python stacks are `list` (`append`, `pop`, `[-1]`); queues and deques are `collections.deque`. Never `list.pop(0)`.
- Every Python block is a complete script with assertions and a fixed-seed brute-force comparison.

## Connections to other folders

- [Sliding Window](../05-sliding-window/README.md): chapter 4 adds a max/min query to a moving window; the shrink-the-left rule comes from there.
- [Range Queries](../04-range-queries/README.md): prefix sums power the shortest-sum deque. Segment trees and sparse tables answer arbitrary range max/min queries, which a monotonic stack cannot.
- [Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md): a heap with lazy deletion also gives sliding-window maxima, in `O(n log n)`; it is the fallback when candidates do not enter and leave in order.
- [Dynamic Programming](../09-dynamic-programming/README.md): [Faster Transitions](../09-dynamic-programming/12-faster-transitions.md) uses the monotonic deque to speed up `min`/`max` over a sliding range of states.
- [Sweep Line](../08-sweep-line/README.md): a sweep schedules when objects become active and inactive; a monotonic structure discards objects through dominance.
- [Graphs](../10-graphs/README.md): breadth-first search uses a FIFO queue, and 0–1 BFS uses a deque ordered by distance rather than by dominance.

## Practice order

1. Basics: valid parentheses, min stack, evaluate reverse Polish notation, implement queue using stacks, decode string, asteroid collision.
2. Nearest neighbors: daily temperatures, next greater element I, next greater element II (circular), online stock span, final prices with a special discount.
3. Greedy and patterns: remove k digits, remove duplicate letters, trapping rain water (all three methods), 132 pattern, car fleet.
4. Windows: sliding window maximum, longest subarray with absolute difference at most limit, jump game VI, constrained subsequence sum, shortest subarray with sum at least K.
5. Boundaries and contributions: largest rectangle in histogram, maximal rectangle, sum of subarray minimums, sum of subarray ranges, maximum subarray min-product, sum of total strength of wizards.

For every problem, before coding, say what the structure holds, in what order, and what each pop proves: **answered**, **dominated**, **expired**, or **boundary found**.
