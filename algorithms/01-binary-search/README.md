# Binary Search — From Sorted Arrays to Searching on Answers

Binary search finds what you are looking for by asking a yes/no question at the middle of what is still possible and throwing away the half that can't contain the answer. Each question halves the work, so a billion candidates need only about 30 questions. The folder starts from a plain search in a sorted array and ends with boundaries in sorted data, binary search over the *answer* to optimization problems, rotated arrays, two-array medians, real numbers, unimodal functions and ranges with no known end.

> **Learning path:** Foundations [1](01-the-idea.md) → [2](02-boundaries.md) · Core technique [3](03-search-on-the-answer.md) · Advanced [4](04-beyond-sorted-arrays.md) → [5](05-reals-ternary-and-unbounded.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [The Idea of Binary Search](01-the-idea.md) | The half-open range `[lo, hi)` and its invariant, missing targets and edge cases, duplicates, closed vs half-open, overflow-safe midpoints, the `lo = mid` infinite loop, why it takes ⌊log₂ n⌋ + 1 steps | Search a sorted array, guess number higher or lower |
| 2 | [Boundaries](02-boundaries.md) | Lower and upper bound, first/last occurrence without `lo = mid`, counts, insert positions, "first true of a monotone predicate", Python's `bisect` exactly, records and `key=` | First and last position, search insert position, first bad version, time-based key–value store, LIS in O(n log n) |
| 3 | [Search on the Answer](03-search-on-the-answer.md) | Turning "smallest value that works" into a monotone yes/no check, greedy checkers, minimize-the-maximum vs maximize-the-minimum | Integer square root, Koko eating bananas, ship packages within D days, split array largest sum, aggressive cows, k-th in a multiplication table |
| 4 | [Beyond Sorted Arrays](04-beyond-sorted-arrays.md) | Binary search when only a local test is available; why any `F → T` boundary is found even for non-monotone predicates; partitioning two arrays | Rotated sorted array (with duplicates), find a peak, sorted matrix (two shapes), median of two sorted arrays |
| 5 | [Real Numbers and Unbounded Ranges](05-reals-ternary-and-unbounded.md) | Bisection on reals and when to stop, ternary search and its integer traps, exponential (galloping) search | Cube root, maximum average subarray II, maximum of a unimodal function, search in a sorted array of unknown size |

Chapters 1–2 are the foundation; read them in order. Chapter 3 is the most useful technique in interviews and contests. Chapters 4 and 5 can be read in either order after chapter 3.

## Recognizing the pattern

| The problem says or implies… | Technique | Predicate or test | Chapter |
|---|---|---|---|
| Sorted array, find a value | Plain binary search | `a[mid]` vs `target` | [1](01-the-idea.md) |
| Sorted array with duplicates; first/last/count/insert position | Lower / upper bound | `a[i] ≥ x` or `a[i] > x` | [2](02-boundaries.md) |
| "First version / day / index where something becomes true" | First true | The given yes/no question | [2](02-boundaries.md) |
| "Minimum speed / capacity / time such that it's possible" | Search on the answer, first true | Greedy feasibility check | [3](03-search-on-the-answer.md) |
| "Minimize the maximum" of contiguous groups | Search on the answer | Greedy count of groups `≤ k` | [3](03-search-on-the-answer.md) |
| "Maximize the minimum" distance or gap | Search on the answer, last true | Greedy placement fits | [3](03-search-on-the-answer.md) |
| "k-th smallest" in a huge implicit set | Search on the value, count `≤ v` | `count(v) ≥ k` | [3](03-search-on-the-answer.md) |
| Sorted, then rotated | Compare with an end element | `a[i] ≤ a[-1]` | [4](04-beyond-sorted-arrays.md) |
| Any local maximum, neighbors differ | First descent | `a[i] > a[i + 1]` | [4](04-beyond-sorted-arrays.md) |
| Matrix with sorted rows and columns | Flatten, or staircase walk | — | [4](04-beyond-sorted-arrays.md) |
| Median or k-th of two sorted arrays | Binary search on a cut | `B[j − 1] ≤ A[i]` | [4](04-beyond-sorted-arrays.md) |
| Answer is a real number | Bisection, fixed iteration count | Monotone real check | [5](05-reals-ternary-and-unbounded.md) |
| Function goes up then down | Ternary search, or first descent on integers | `f(m1) < f(m2)` | [5](05-reals-ternary-and-unbounded.md) |
| No known upper bound | Exponential search, then binary search | Double until true | [5](05-reals-ternary-and-unbounded.md) |

The common thread: find a yes/no question whose answers form `False, …, False, True, …, True` over the candidates. If you can state that question and argue why it is monotone, the rest is the same ten-line loop.

## Conventions

- Zero-based indexing. Ranges are **half-open** `[lo, hi)`: `lo` is included, `hi` is not, and the loop runs `while lo < hi`. The few closed-range functions say so in a comment. This differs from the inclusive query API in [Range Queries](../04-range-queries/README.md).
- The midpoint is always written `lo + (hi - lo) // 2`, even in Python, so the code carries over to fixed-width languages.
- The workhorse is `first_true(lo, hi, ok)`: the smallest `i` in `[lo, hi)` with `ok(i)`, or `hi` if none. "Last true" is "first false, minus 1"; the guide never writes `lo = mid` with a rounded-down midpoint.
- Every Python block is a complete runnable script using only the standard library (Python 3.10+, for `bisect`'s `key=`), with its own assertions. Most compare against a brute force on small random inputs with a fixed seed.

## How to study

1. Read chapters 1–2 in order. Everything later is `first_true` with a different predicate.
2. For each problem, **write the predicate as a sentence and argue that it is monotone** before reading the code.
3. Fill in the trace tables by hand, then run the script.
4. Break the code on purpose: change `hi = mid` to `hi = mid - 1`, or drop a `+ 1`, and see which assertion fails or which loop hangs.
5. When a new problem asks for "the smallest" or "the largest" value with a property, try search on the answer first.

## Connections to other topics

- [Range Queries](../04-range-queries/README.md): prefix sums power the feasibility checks of search-on-the-answer problems, and binary searching over prefix sums (or descending a Fenwick tree) finds the first prefix reaching a total.
- [Sliding Window](../05-sliding-window/README.md): many "longest/shortest subarray with a property" problems can be solved by binary searching the length with a fixed-window check; the two-pointer window usually removes the log factor.
- [Dynamic Programming](../09-dynamic-programming/README.md): the O(n log n) longest increasing subsequence keeps a sorted list of tails and updates it with lower bound ([Boundaries](02-boundaries.md#7-advanced-longest-increasing-subsequence-in-on-log-n)). Some DP transitions binary search for the last compatible item, as in weighted interval scheduling.
- [Graphs](../10-graphs/README.md): "minimize the largest edge on a path" can be solved by binary searching the threshold and running BFS or union-find on the allowed edges.

## Practice order

1. **Warm-up:** binary search; guess number higher or lower; first bad version; search insert position.
2. **Boundaries:** find first and last position of element in sorted array; count occurrences in a sorted array; time-based key–value store; longest increasing subsequence; Russian doll envelopes.
3. **Search on the answer:** sqrt(x); Koko eating bananas; capacity to ship packages within D days; minimum number of days to make m bouquets; split array largest sum; magnetic force between two balls; kth smallest number in multiplication table; find k-th smallest pair distance.
4. **Beyond sorted arrays:** find minimum in rotated sorted array (I, II); search in rotated sorted array (I, II); find peak element; search a 2D matrix (I, II); median of two sorted arrays.
5. **Reals and unbounded:** maximum average subarray II; minimize max distance to gas station; find in mountain array; search in a sorted array of unknown size.
