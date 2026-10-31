# Prefix Sums and Difference Arrays — From First Principles

> **Learning path:** [Prefix Sums](01-prefix-sums.md) → [Fenwick Tree](02-fenwick-tree.md) → [Segment Tree](03-segment-tree.md)  
> **Goal:** Derive the methods yourself, explain *why* they work, recognize variants, and implement them correctly in Python.

## 0. Which problem motivates this technique?

Suppose an array is queried many times:

- `sum(l, r)`: sum elements from `l` through `r`.
- The array **does not change** between queries.

A naive query scans the interval: `O(r-l+1)`. For `q` long queries this can cost `O(nq)`.

**Design question:** Can we precompute something once, then answer each query in constant time?

Yes. Instead of recomputing the same left-hand portion of the array, preserve a cumulative summary.

| Representation | Preprocessing | Sum of arbitrary [l, r] | Point update |
|---|---:|---:|---:|
| Original array only | O(1) | O(n) | O(1) |
| Prefix-sum array | O(n) | **O(1)** | O(n) |
| Fenwick Tree | O(n) build | O(log n) | O(log n) |
| Segment Tree | O(n) build | O(log n) | O(log n) |

The prefix-sum array is best when the data are static and the aggregation is invertible (for sums, subtracting works).

## 1. Derive the invariant

Use a **zero-based** input array `a[0..n-1]` and a prefix array of length `n+1`:

$$
P[0]=0,\qquad P[k]=\sum_{j=0}^{k-1}a[j].
$$

In words, **`P[k]` is the sum of the first `k` elements**. This interpretation avoids almost all off-by-one mistakes.

Example:

```text
index:   0  1  2  3  4
a:       2  1  3  4  5
P:    0  2  3  6 10 15
      ↑
      P[0] = empty-prefix sum
```

We want the inclusive sum `a[l] + ... + a[r]`.

- `P[r+1]` includes elements `0..r`.
- `P[l]` includes elements `0..l-1`.
- Subtract the common part.

$$
\boxed{\operatorname{sum}(l,r)=P[r+1]-P[l]}\qquad(0\le l\le r<n).
$$

For `l=1, r=3`: `P[4]-P[1]=10-2=8=1+3+4`.

**Why subtraction?** Prefixes are nested. The larger prefix is exactly the smaller prefix plus the requested interval.

### Basic implementation

```python
def build_prefix(a: list[int]) -> list[int]:
    p = [0] * (len(a) + 1)
    for i, x in enumerate(a):
        p[i + 1] = p[i] + x
    return p

def range_sum(p: list[int], l: int, r: int) -> int:
    """Inclusive 0-based range [l, r]."""
    return p[r + 1] - p[l]

a = [2, 1, 3, 4, 5]
p = build_prefix(a)
assert p == [0, 2, 3, 6, 10, 15]
assert range_sum(p, 1, 3) == 8
```

Building `P` takes O(n) time and O(n) extra space; a range query takes O(1).

### Common misconception: why not write `P[r]-P[l]`?

Under this convention, `P[r]` stops **before** `a[r]`. The correct expression includes `P[r+1]`. With **1-based** input indices and `P[i] = a[1]+...+a[i]`, the formula instead becomes `P[r]-P[l-1]`. Both are valid; never mix conventions.

## 2. Prefix sums as discrete integration

Think of `P` as a *discrete integral*: it accumulates local values.

$$
P[i+1]-P[i]=a[i].
$$

The array `a` is the **discrete difference** (derivative) of `P`. This explains two inverse operations:

- **Accumulate** consecutive local values to obtain a prefix array.
- **Subtract** consecutive prefix values to recover the original array.

The telescoping identity is the proof:

$$
\sum_{i=l}^{r}(P[i+1]-P[i])
=P[r+1]-P[l].
$$

This perspective is useful because the next technique—**difference arrays**—reverses the role of values and updates.

## 3. Difference arrays: make many range updates cheap

**New problem:** Apply many operations `add(l, r, delta)`, then recover the final array **once**.

Applying each update element by element costs O(n). Instead define a 0-based difference array:

$$
D[0]=a[0],\qquad D[i]=a[i]-a[i-1]\ \ (i>0).
$$

The original value is the prefix sum of differences:

$$
a[i]=\sum_{j=0}^{i}D[j].
$$

What happens if we add `delta` to every element in `[l,r]`?

- At `l`, values suddenly rise by `delta`: `D[l] += delta`.
- Within the range, adjacent elements rose by the same amount: their *difference* does not change.
- At `r+1`, the added amount stops: `D[r+1] -= delta` (if it exists).

Therefore, **two boundary changes encode an entire range update**.

```python
def batch_range_add(a, updates):
    """Updates contain (l, r, delta), inclusive and 0-based."""
    n = len(a)
    d = [0] * (n + 1)  # +1 sentinel allows r+1 == n

    for l, r, delta in updates:
        d[l] += delta
        d[r + 1] -= delta

    running = 0
    result = []
    for i, value in enumerate(a):
        running += d[i]
        result.append(value + running)
    return result

assert batch_range_add(
    [1, 2, 3, 4, 5], [(1, 3, 3)]
) == [1, 5, 6, 7, 5]
```

This version stores only **changes**, not the full difference array of the original values. It is equivalent when you add reconstructed changes back to the original array.

Costs for `q` updates: **O(q+n)** time and O(n) auxiliary space.

### Why is a difference array not enough for online queries?

It represents the updates efficiently, but reconstructing an arbitrary current value requires a prefix accumulation: O(n) with a plain array. We cannot retain a prefix-sum table after every update without making updates expensive again.

**This exact gap motivates a Fenwick Tree:** store the difference array in a dynamically updatable prefix-sum structure. See [Fenwick Tree](02-fenwick-tree.md#6-range-add--point-query-one-bit-on-differences).

## 4. Prefix sums of counts, not just numeric sums

If a question asks, "How many values in `[l,r]` satisfy a condition?", first turn the condition into 0/1:

$$
b[i]=\begin{cases}1&\text{if }a[i]\text{ satisfies the condition}\\0&\text{otherwise.}\end{cases}
$$

Then prefix-sum `b`.

```python
a = [4, 7, 2, 9, 6]
even = [int(x % 2 == 0) for x in a]
p = build_prefix(even)
assert range_sum(p, 1, 4) == 2  # indices 2 and 4
```

Examples: vowels in a substring, count of zeros, number of events in a time interval, and count of items below a threshold (when the threshold is fixed).

## 5. Two-dimensional prefix sums: inclusion–exclusion

Given matrix `grid` with `R` rows and `C` columns, define a prefix table with an extra zero row/column:

$$
S[r+1][c+1]=\sum_{0\le i\le r,\ 0\le j\le c}grid[i][j].
$$

To build each cell, combine the rectangle above and left, subtract their overlap, and add the new cell:

$$
\boxed{S[r+1][c+1]=grid[r][c]+S[r][c+1]+S[r+1][c]-S[r][c].}
$$

To query the inclusive rectangle from `(r_1,c_1)` to `(r_2,c_2)`:

$$
\boxed{
S[r_2+1][c_2+1]-S[r_1][c_2+1]
-S[r_2+1][c_1]+S[r_1][c_1]
}
$$

**Why add the top-left intersection back?** It was subtracted twice, once with the top region and once with the left region. This is inclusion–exclusion.

```python
def build_prefix_2d(grid):
    if not grid:
        return [[0]]
    rows, cols = len(grid), len(grid[0])
    s = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(rows):
        for c in range(cols):
            s[r + 1][c + 1] = (
                grid[r][c]
                + s[r][c + 1] + s[r + 1][c]
                - s[r][c]
            )
    return s

def rectangle_sum(s, r1, c1, r2, c2):
    return (
        s[r2 + 1][c2 + 1]
        - s[r1][c2 + 1]
        - s[r2 + 1][c1]
        + s[r1][c1]
    )

g = [[1, 2, 3], [4, 5, 6]]
s = build_prefix_2d(g)
assert rectangle_sum(s, 0, 1, 1, 2) == 16  # 2+3+5+6
```

Build: O(RC). Each rectangle query: O(1). Negative values are fine.

## 6. Count subarrays with sum k: prefix sums + a hash map

**Different problem:** Count **all** subarrays whose sum equals `k`, not just answer a given interval.

Let `P[j]` be the sum before index `j`. A subarray `[i,j-1]` has sum `k` exactly when

$$
P[j]-P[i]=k\quad\Longleftrightarrow\quad P[i]=P[j]-k.
$$

As we scan from left to right, maintain how many earlier prefixes have value `current_prefix-k`.

```python
from collections import defaultdict

def count_subarrays_sum_k(nums, k):
    freq = defaultdict(int)
    freq[0] = 1  # the empty prefix
    running = 0
    answer = 0

    for x in nums:
        running += x
        answer += freq[running - k]
        freq[running] += 1

    return answer

assert count_subarrays_sum_k([1, 1, 1], 2) == 2
assert count_subarrays_sum_k([1, -1, 0], 0) == 3
```

**Why record the current prefix *after* querying?** Otherwise the current endpoint could pair with itself, creating an empty subarray. We want nonempty subarrays only.

**Why not use a standard sliding window?** With negative numbers, increasing the right endpoint can decrease the sum; the monotonic reasoning used by a typical positive-only sliding window fails. Hashing prefixes does not depend on positivity.

Complexity: expected O(n) time, O(n) space.

### Useful variations

- **Longest subarray summing to `k`:** store the *earliest* index of each prefix, rather than a frequency.
- **Equal number of 0s and 1s:** map 0 → -1 and 1 → +1, then find a longest zero-sum subarray.
- **Subarrays divisible by `k`:** equal prefix remainders identify differences divisible by `k` (for `k ≠ 0`). Normalize remainders if your language permits negative remainders.
- **Prefix XOR:** replace addition/subtraction with XOR. Since `x ^ x = 0`, an interval XOR is `PX[r+1] ^ PX[l]`.
- **Prefix products:** division is not always valid (zeros, integer truncation, modular noninvertible values). Don't assume every aggregation supports subtraction.

## 7. Why some prefix queries cannot be answered with two prefix values

A range sum works because we can **cancel** the unwanted prefix. For XOR, cancellation works too.

For a **minimum**, however, `min(prefix through r)` and `min(prefix through l-1)` are generally insufficient to recover `min(l..r)`. There is no inverse to `min`.

Example: both arrays `[1,5,6]` and `[1,2,6]` have overall prefix minimum 1, but their `[1,2]` range minima differ.

This distinction predicts data-structure choice:

- Static sum / count / XOR: prefix-based cancellation.
- Dynamic sum: Fenwick Tree (or Segment Tree).
- Dynamic range min/max, or more general associative aggregations: Segment Tree.
- Static idempotent min/max may use a **Sparse Table** for O(1) queries after O(n log n) preprocessing.

## 8. Interview Q&A: derive, don't memorize

**Q: Why does the prefix array need a leading zero?**  
A: It represents the empty prefix and makes the same formula work when `l=0`. It is a modeling choice that simplifies boundaries, not a mathematical requirement.

**Q: If I only have one range query, should I build prefixes?**  
A: Usually no. Scanning that interval is O(n) worst-case, while building prefixes is O(n) plus memory. Prefixes become useful when there are many queries or other prefix-dependent computations.

**Q: What if each point changes after queries?**  
A: Changing `a[i]` alters every `P[j]` with `j>i`. A plain prefix array therefore has O(n) update time. Move to a Fenwick Tree for dynamic sums, or to a Segment Tree for more flexible range operations.

**Q: Are negative numbers a problem?**  
A: No for prefix sums and difference arrays. They *are* a problem for sliding-window strategies that rely on monotonically increasing sums.

**Q: How do I distinguish an offline batch update from an online dynamic problem?**  
A: If all updates happen before a single reconstruction, use a difference array. If the problem interleaves updates with queries, maintain a dynamic aggregate.

**Q: What's the unifying viewpoint?**  
A: Prefix sums accumulate information; difference arrays record changes at boundaries; Fenwick and Segment Trees maintain aggregates under modifications.

## 9. Complexity summary and boundaries

| Variant | Build | Update | Query |
|---|---:|---:|---:|
| 1D prefix sum | O(n) | O(n) | O(1) range sum |
| 2D prefix sum | O(RC) | O(RC) if rebuilt | O(1) rectangle sum |
| Difference array, batch | O(n) reconstruction | O(1) range add | O(n) to reconstruct current values |
| Prefix + hash map (subarray count) | O(n) single pass | Not applicable | O(n) full counting problem |

Checklist: specify 0/1-based indexing; inclusive vs half-open ranges; empty input; `r+1` boundary; signed values; integer overflow in fixed-width languages; and whether operations are online.

## 10. Recommended practice order

1. **LeetCode 303 — Range Sum Query: Immutable:** build `P`; explain why `P[r+1]-P[l]` works.
2. **LeetCode 304 — Range Sum Query 2D: Immutable:** derive inclusion–exclusion.
3. **LeetCode 560 — Subarray Sum Equals K:** derive `P[j]-P[i]=k`, then count earlier prefixes.
4. **LeetCode 525 — Contiguous Array:** transform 0/1 into -1/+1 and keep earliest prefixes.
5. **LeetCode 523 — Continuous Subarray Sum:** work with equal prefix remainders and the minimum subarray-length constraint.
6. **Range Addition (difference-array pattern):** represent each inclusive range modification using two boundary changes.

## 11. Next step and references

Move to [Fenwick Tree](02-fenwick-tree.md) when you need both **updates and prefix/range queries** online. Move to [Segment Tree](03-segment-tree.md) when the aggregator is more general or you need rich lazy range operations.

- [CP-Algorithms: Prefix Sums / inclusion–exclusion applications](https://cp-algorithms.com/)
- [USACO Guide: Prefix Sums](https://usaco.guide/silver/prefix-sums)
- [LeetCode 303](https://leetcode.com/problems/range-sum-query-immutable/)
