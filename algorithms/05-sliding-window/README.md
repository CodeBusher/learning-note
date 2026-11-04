# Two Pointers and Sliding Window — Move Forward, Never Back

Pair and window problems have `O(n²)` candidates. Two pointers and sliding windows check `O(n)` of them by moving indices only forward, so each element is added once and removed once. Everything in this folder rests on one question: **why is it safe to throw a candidate away and never look back?** Sorted order, an area formula, monotone validity, counting identities and dominance each give an answer; when none applies (sums with negative values), prefix sums and deques take over.

> **Learning path:** [Two Pointers](01-two-pointers.md) → [Fixed and Variable Windows](02-fixed-and-variable-windows.md) → [Counting and Frequency Windows](03-counting-and-frequency-windows.md) → [Advanced Window Patterns](04-advanced-patterns.md)

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Two Pointers](01-two-pointers.md) | Opposite-end pointers on sorted data; reader/writer pointers; three-way partition; why each move discards only useless candidates | Two Sum II, Container With Most Water, 3Sum, Remove Duplicates, Sort Colors |
| 2 | [Fixed and Variable Windows](02-fixed-and-variable-windows.md) | Fixed windows with a running sum; monotone validity and why `left` never moves back; the longest and shortest templates; why nested loops are still linear | Maximum Average Subarray, Longest Substring Without Repeating Characters, At Most K Distinct, Max Consecutive Ones III, Minimum Size Subarray Sum |
| 3 | [Counting and Frequency Windows](03-counting-and-frequency-windows.md) | Counting `right - left + 1` windows per step; exactly `k` = at most `k` − at most `k − 1`; letter-count windows with a `missing` counter | Subarray Product Less Than K, Subarrays with K Different Integers, Find All Anagrams, Permutation in String, Minimum Window Substring |
| 4 | [Advanced Window Patterns](04-advanced-patterns.md) | The never-decreasing `max_freq` shortcut and its proof; why negatives break sum windows; prefix sums with a hash map or a monotonic deque; window maximum; max − min windows | Longest Repeating Character Replacement, Subarray Sum Equals K, Shortest Subarray with Sum at Least K, Sliding Window Maximum, Longest Subarray with Absolute Diff ≤ Limit |

Chapter 1 starts from zero. Each later chapter assumes the ones before it.

## Recognizing the pattern

| The problem asks for… | Why a pointer can move one way | Method | Where |
|---|---|---|---|
| A pair with a given sum in **sorted** data | A too-small left value is too small with every remaining partner | Opposite-end pointers | [1 §1](01-two-pointers.md#1-two-values-that-add-up-to-a-target) |
| The best pair under a formula like `width × min(height)` | The shorter side cannot do better with any closer partner | Opposite-end pointers | [1 §2](01-two-pointers.md#2-container-with-most-water) |
| All distinct triples with a target sum | Fix one value, then pair sum; skip equal neighbors | Sort, then a loop of opposite-end pointers | [1 §3](01-two-pointers.md#3-three-values-that-sum-to-zero) |
| Filter or deduplicate in place | The written prefix holds exactly the kept values | Reader and writer pointers | [1 §4](01-two-pointers.md#4-reader-and-writer-remove-duplicates-in-place) |
| Best window of exactly `k` neighbors | Window size alone decides who leaves | Fixed window | [2 §1](02-fixed-and-variable-windows.md#1-a-fixed-size-window-the-largest-sum-of-k-neighbors) |
| Longest window satisfying a "not too much" rule (no repeats, at most `k` kinds, at most `k` zeros) | Extending an invalid window keeps it invalid | Shrink while invalid, then record | [2 §2–§3](02-fixed-and-variable-windows.md#2-a-variable-size-window-the-longest-substring-without-repeats) |
| Shortest window satisfying a "at least enough" rule, nonnegative values | Extending a valid window keeps it valid | Record and shrink while valid | [2 §4](02-fixed-and-variable-windows.md#4-the-shortest-window-that-reaches-a-total) |
| **How many** windows satisfy a monotone rule | All shorter windows with the same right end are valid too | Add `right - left + 1` per step | [3 §1](03-counting-and-frequency-windows.md#1-counting-windows-subarrays-with-product-less-than-k) |
| How many windows have **exactly** `k` of something | "At most" is monotone; "exactly" is not | `at_most(k) - at_most(k - 1)` | [3 §2](03-counting-and-frequency-windows.md#2-exactly-k-subtract-two-at-most-counts) |
| Rearrangements of a pattern inside a text | Fixed length; counts change by two letters per move | Fixed letter-count window | [3 §3](03-counting-and-frequency-windows.md#3-find-all-anagrams-a-fixed-window-of-letter-counts) |
| Shortest substring covering a pattern's letters | Coverage survives extension | Shortest template with a `missing` counter | [3 §4](03-counting-and-frequency-windows.md#4-minimum-window-substring-the-shortest-cover) |
| Longest window fixable with `k` changes | Changes needed never fall as the window grows | Longest template; optional lazy `max_freq` | [4 §1](04-advanced-patterns.md#1-longest-repeating-character-replacement) |
| Count windows with an exact sum, **negatives allowed** | No window rule works | Prefix sums and a hash map | [4 §2](04-advanced-patterns.md#2-exact-sums-with-negative-values-prefix-sums-and-a-map) |
| Shortest window with sum at least `k`, **negatives allowed** | Finished and dominated starts can be dropped | Prefix sums and a monotonic deque | [4 §3](04-advanced-patterns.md#3-shortest-window-with-sum-at-least-k-negatives-allowed) |
| Maximum or minimum of every window | A newer, larger value outlives an older, smaller one | Monotonic deque | [4 §4](04-advanced-patterns.md#4-sliding-window-maximum-when-the-state-is-not-one-number) |
| Longest window with `max - min <= limit` | The range never shrinks as the window grows | Longest template plus two deques | [4 §5](04-advanced-patterns.md#5-combining-both-longest-window-with-max---min--limit) |

A window needs a **contiguous** stretch and a reason to discard. Neighboring positions alone are not enough: if you cannot say why a removed left end can never start an answer again, use one of the alternatives in [4 §6](04-advanced-patterns.md#6-choosing-a-method-derive-a-window-or-decide-not-to).

## Conventions

- Zero-based indices. Windows are written `[left, right]` with **both ends included**, so the length is `right - left + 1` and the Python slice is `nums[left:right + 1]`. Prefix sums follow the convention of Range Queries: `P[j]` is the sum of `nums[:j]`, and `P[j] - P[i]` is the sum of `nums[i:j]`.
- Functions that return a window return its endpoints, or `None` (or `""` for substrings) when no window exists. Each function states what it returns for empty input.
- Every Python block is a complete script with a `main()` that runs asserts and a fixed-seed brute-force comparison. Run any block with `python3 file.py`.
- Time bounds assume `O(1)` expected dictionary operations. Space bounds count extra memory, not the input or output.

## Connections

- [Range Queries](../04-range-queries/README.md): prefix sums, which replace windows when values can be negative ([Advanced Window Patterns](04-advanced-patterns.md)).
- [Monotonic Stacks and Deques](../06-monotonic-stack-and-deque/README.md): the deque behind window maxima and shortest sums with negatives, studied in depth.
- [Sweep Line](../08-sweep-line/README.md): also moves forward through an ordered domain, but over sorted events rather than a contiguous stretch of the input.
- [Dynamic Programming](../09-dynamic-programming/README.md): Kadane's maximum subarray, and DP transitions that need a sliding window minimum.

## Practice order

1. Two Sum II, Valid Palindrome, Container With Most Water, 3Sum, Remove Duplicates from Sorted Array, Sort Colors.
2. Maximum Average Subarray I, Longest Substring Without Repeating Characters, Max Consecutive Ones III, Fruit Into Baskets, Minimum Size Subarray Sum.
3. Subarray Product Less Than K, Binary Subarrays With Sum, Subarrays with K Different Integers, Find All Anagrams in a String, Permutation in String, Minimum Window Substring.
4. Longest Repeating Character Replacement, Subarray Sum Equals K, Sliding Window Maximum, Longest Subarray with Absolute Diff ≤ Limit, Shortest Subarray with Sum at Least K.

Before moving on, try one exercise without code: explain why the shortest-window template fails on `[1, -1, 5]` with target 5. If you can, you understand the proof and not only the template.
