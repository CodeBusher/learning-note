# Toolkit — Tested Code, Worked Traps, Cheat Sheet

## 26. Code catalog and tests

One script for the main cases. Python integers grow without limit, so every count is exact. `main` compares each function with a brute force over all nonincreasing part lists (or all labeled vectors) on random small inputs, including the edge cases $k=0$, $n=0$, cap 0, $r=0$ and $k>nL$.

```python
from itertools import product
from math import comb
import random


# A. Original problem: identical items, identical boxes, empties allowed.
def count_partitions(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    dp = [1] + [0] * k
    for size in range(1, min(n, k) + 1):
        for total in range(size, k + 1):
            dp[total] += dp[total - size]
    return dp[k]


# B. Exactly r positive identical boxes.
def count_exact_boxes(k: int, r: int) -> int:
    if k < 0 or r < 0 or k < r:
        return 0
    return count_partitions(k - r, r)


# C. Part sizes restricted to a set S; unlimited copies of each.
def count_allowed_parts(k: int, sizes) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size in sorted(set(sizes)):
        if size <= 0:
            raise ValueError("Part sizes must be positive")
        for total in range(size, k + 1):
            dp[total] += dp[total - size]
    return dp[k]


# D. At most one copy of each allowed part size.
def count_distinct_parts(k: int, sizes) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size in sorted(set(sizes)):
        if size <= 0:
            raise ValueError("Part sizes must be positive")
        for total in range(k, size - 1, -1):
            dp[total] += dp[total - size]
    return dp[k]


# E. Size-specific multiplicity caps, e.g. {1: 2, 2: 1, 3: 2}.
# Keys are allowed part sizes, values are maximum copy counts.
def count_bounded_multiplicities(k: int, caps: dict[int, int]) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size, max_copies in sorted(caps.items()):
        if size <= 0 or max_copies < 0:
            raise ValueError("Require positive size and nonnegative cap")

        shift = (max_copies + 1) * size

        # Multiply old polynomial by (1 - x^shift).
        # Backward iteration preserves OLD coefficients.
        for total in range(k, shift - 1, -1):
            dp[total] -= dp[total - shift]

        # Divide by (1 - x^size); forward iteration
        # reuses NEW coefficients. The two passes together
        # allow exactly 0..max_copies copies of this size.
        for total in range(size, k + 1):
            dp[total] += dp[total - size]

    return dp[k]


# F. Identical boxes, each containing at most L identical items.
# Counts partitions of k into <= n parts, each <= L.
def count_rectangle(k: int, n: int, L: int) -> int:
    if min(k, n, L) < 0 or k > n * L:
        return 0

    # dp[used_boxes][total] for processed occupancy sizes.
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 1

    for size in range(1, min(L, k) + 1):
        # Increasing used_boxes allows multiple copies of
        # this occupancy size in different identical boxes.
        for used_boxes in range(1, n + 1):
            for total in range(size, k + 1):
                dp[used_boxes][total] += dp[used_boxes - 1][total - size]

    return sum(dp[used_boxes][k] for used_boxes in range(n + 1))


# G. Exactly r occupied identical boxes, each occupancy in [a,b].
def count_exact_boxes_with_bounds(k: int, r: int, a: int, b: int) -> int:
    if k < 0 or r < 0 or a < 1 or b < a:
        return 0
    return count_rectangle(k - r * a, r, b - a)


# H. Exactly r DISTINCT positive parts, no size bound.
def count_exact_distinct_parts(k: int, r: int) -> int:
    if k < 0 or r < 0:
        return 0
    return count_partitions(k - r * (r + 1) // 2, r)


# I. Exactly r positive parts, adjacent gap >= d.
def count_exact_parts_with_gap(k: int, r: int, d: int) -> int:
    if k < 0 or r < 0 or d < 0:
        return 0
    return count_exact_boxes(k - d * r * (r - 1) // 2, r)


# J. Stirling numbers of second kind: distinct items, identical nonempty boxes.
def stirling2(k: int, r: int) -> int:
    if min(k, r) < 0:
        return 0
    dp = [0] * (r + 1)
    dp[0] = 1
    for total_items in range(1, k + 1):
        for groups in range(min(total_items, r), 0, -1):
            dp[groups] = groups * dp[groups] + dp[groups - 1]
        dp[0] = 0
    return dp[r]


# K. Labeled boxes, identical items: stars and bars.
def identical_items_labeled_boxes(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    if n == 0:
        return int(k == 0)
    return comb(k + n - 1, n - 1)


# L. Labeled boxes, identical items, all boxes nonempty.
def labeled_boxes_nonempty(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    if n == 0:
        return int(k == 0)
    return comb(k - 1, n - 1) if k >= n else 0


# M. Labeled boxes, identical items, each capacity <= L.
def labeled_boxes_capacity(k: int, n: int, L: int) -> int:
    if min(k, n, L) < 0 or k > n * L:
        return 0
    if n == 0:
        return int(k == 0)
    ways = 0
    for t in range(min(n, k // (L + 1)) + 1):
        remainder = k - t * (L + 1)
        ways += (-1) ** t * comb(n, t) * comb(remainder + n - 1, n - 1)
    return ways


# N. Unrestricted partition numbers, via pentagonal recurrence.
def unrestricted_partition_numbers(k: int) -> list[int]:
    if k < 0:
        return []
    p = [0] * (k + 1)
    p[0] = 1

    for target in range(1, k + 1):
        m = 1
        while m * (3 * m - 1) // 2 <= target:
            left = m * (3 * m - 1) // 2
            right = m * (3 * m + 1) // 2
            sign = 1 if m % 2 else -1
            p[target] += sign * p[target - left]
            if right <= target:
                p[target] += sign * p[target - right]
            m += 1

    return p


# O. Enumerate actual partitions, rather than only counting them.
# Careful: output size grows quickly.
def enumerate_partitions(k: int, max_parts: int):
    def dfs(remaining: int, slots: int, largest: int, path: list[int]):
        if remaining == 0:
            yield tuple(path)
            return
        if slots == 0:
            return
        for current in range(min(remaining, largest), 0, -1):
            path.append(current)
            yield from dfs(remaining - current, slots - 1, current, path)
            path.pop()

    if k < 0 or max_parts < 0:
        return
    yield from dfs(k, max_parts, k, [])


def all_partitions(k: int) -> list[tuple[int, ...]]:
    """Brute force: every partition of k as a nonincreasing tuple."""
    return list(enumerate_partitions(k, k))


def brute_stirling2(k: int, r: int) -> int:
    groupings = set()
    for f in product(range(r), repeat=k):
        if len(set(f)) == r:
            groupings.add(frozenset(
                frozenset(i for i in range(k) if f[i] == g) for g in range(r)))
    return len(groupings)


def main():
    assert count_partitions(5, 3) == 5
    assert count_exact_boxes(5, 3) == 2  # (3,1,1), (2,2,1)
    assert count_rectangle(4, 3, 2) == 2
    assert count_bounded_multiplicities(5, {1: 2, 2: 1, 3: 2}) == 2
    assert unrestricted_partition_numbers(6)[6] == 11
    assert list(enumerate_partitions(5, 3)) == [
        (5,), (4, 1), (3, 2), (3, 1, 1), (2, 2, 1)
    ]
    rng = random.Random(10)
    for _ in range(300):
        k = rng.randint(0, 12)
        n, r, L = rng.randint(0, 5), rng.randint(0, 5), rng.randint(0, 5)
        d = rng.randint(0, 3)
        a = rng.randint(1, 3)
        b = rng.randint(a, 5)
        sizes = {rng.randint(1, 6) for _ in range(rng.randint(0, 4))}
        caps = {s: rng.randint(0, 3) for s in sizes}
        parts = all_partitions(k)

        def count(pred) -> int:
            return sum(1 for q in parts if pred(q))

        assert count_partitions(k, n) == count(lambda q: len(q) <= n)
        assert count_exact_boxes(k, r) == count(lambda q: len(q) == r)
        assert count_allowed_parts(k, sizes) == count(
            lambda q: set(q) <= sizes)
        assert count_distinct_parts(k, sizes) == count(
            lambda q: set(q) <= sizes and len(set(q)) == len(q))
        assert count_bounded_multiplicities(k, caps) == count(
            lambda q: set(q) <= sizes and all(q.count(s) <= caps[s] for s in q))
        assert count_rectangle(k, n, L) == count(
            lambda q: len(q) <= n and all(x <= L for x in q))
        assert count_exact_boxes_with_bounds(k, r, a, b) == count(
            lambda q: len(q) == r and all(a <= x <= b for x in q))
        assert count_exact_distinct_parts(k, r) == count(
            lambda q: len(q) == r and len(set(q)) == r)
        assert count_exact_parts_with_gap(k, r, d) == count(
            lambda q: len(q) == r and all(x - y >= d for x, y in zip(q, q[1:])))
        assert unrestricted_partition_numbers(k)[k] == len(parts)

        m = min(n, 3)  # labeled boxes: keep (k + 1) ** m small
        vectors = [v for v in product(range(k + 1), repeat=m) if sum(v) == k]
        assert identical_items_labeled_boxes(k, m) == len(vectors)
        assert labeled_boxes_nonempty(k, m) == sum(1 for v in vectors if all(v))
        assert labeled_boxes_capacity(k, m, L) == sum(
            1 for v in vectors if max(v, default=0) <= L)

    for k in range(6):
        for r in range(5):
            assert stirling2(k, r) == brute_stirling2(k, r)


if __name__ == "__main__":
    main()
```

### 26.1 Complexity

| Problem / implementation | Time | Extra space |
|---|---|---|
| `count_partitions` | $O(k\min(n,k))$ | $O(k)$ |
| `count_allowed_parts`, $s$ allowed sizes | $O(sk)$ | $O(k)$ |
| `count_distinct_parts`, $s$ sizes | $O(sk)$ | $O(k)$ |
| `count_bounded_multiplicities`, $s$ sizes | $O(sk)$ | $O(k)$ |
| `count_rectangle` | $O(Lnk)$ | $O(nk)$ |
| `stirling2(k,r)` | $O(kr)$ | $O(r)$ |
| `unrestricted_partition_numbers(k)` | $O(k\sqrt{k})$ | $O(k)$ |
| `enumerate_partitions` | output-dependent; potentially very large | $O(k)$ recursion, excluding output |

A part size larger than $k$ contributes only its constant term 1 below degree $k+1$, so skip it.

## 27. Worked examples and interview checklist

### Example A: no box can hold more than 2

For $k=5,n=3,L=2$, the only partition is $(2,2,1)$. Answer: 1.

Do **not** use $\prod_{i=1}^3(1+x^i+x^{2i})$: that limits **copies of each part size** after conjugation, not the size of each original box.

### Example B: each *part size* can occur at most twice

For $k=5$ and allowed sizes $1,2,3$, permitted partitions are:

$(3,2)$, $(3,1,1)$, and $(2,2,1)$; $(2,1,1,1)$ and $(1,1,1,1,1)$ use 1 too often. Answer: **3**. With the cap for size 2 lowered to one (`{1:2,2:1,3:2}`), $(2,2,1)$ drops out: **2**.

### Interview derivation template

1. **Restate distinguishability:** Are items and boxes labeled?
2. **Write a canonical state:** For identical boxes, sorted nonnegative occupancy vectors.
3. **List small examples:** $k=3,4,5$ and edge cases.
4. **Find the mathematical family:** stars and bars, integer partitions, compositions, Stirling/Bell, or inclusion-exclusion.
5. **Write the generating function:** What does each factor count? Which exponent is the total? Is the factor $1+x^i$, $1/(1-x^i)$, or bounded?
6. **Derive DP by cases:** zero vs one-or-more, or exact number of copies.
7. **Compress safely:** Verify whether the dependency uses **old** or **new** coefficients. Descend for old; ascend for new.
8. **Explain complexity** and whether you need an exact value, a value modulo $M$, or an approximation.
9. **Test special cases:** empty, impossible, distinct vs identical boxes, zero limits, max occupancy, and performance.

## 28. Cheat sheet

- $n^k$: distinct items, labeled boxes, empty allowed.
- $\binom{k+n-1}{n-1}$: identical items, labeled boxes, empty allowed.
- $\sum_{r\le n}S(k,r)$: distinct items, identical boxes.
- $p_{\le n}(k)$: identical items, identical boxes.
- **Generating functions:** addition collects alternatives; multiplication combines choices; $x^k$ tracks size; coefficient counts ways.
- **0/1 usage:** $1+x^i$ → backward addition.
- **Unlimited usage:** $1/(1-x^i)$ → forward addition.
- **At most $m$ copies:** $(1-x^{(m+1)i})/(1-x^i)$ → backward subtraction + forward addition.
- **Original-box capacity ≤ $L$:** both length and largest part bounded → partition in an $n\times L$ rectangle.
- **More conditions:** introduce additional DP dimensions or auxiliary generating-function variables.

## 29. References

1. **NIST Digital Library of Mathematical Functions**, [§26.9: Integer Partitions — Restricted Number and Part Size](https://dlmf.nist.gov/26.9). Gaussian binomial coefficients, exact-size restrictions, and generating functions.
2. **NIST Digital Library of Mathematical Functions**, [§26.10: Integer Partitions — Other Restrictions](https://dlmf.nist.gov/26.10). Distinct parts, odd parts, difference restrictions, and identities.
3. **Applied Combinatorics**, [Partitions of an Integer](https://appliedcombinatorics.org/book/s_genfunction_partitions-integer.html). A friendly treatment of generating functions and Euler's odd/distinct identity.
4. **NIST DLMF**, [§26.8: Set Partitions — Stirling Numbers](https://dlmf.nist.gov/26.8) and [§26.12: Plane Partitions](https://dlmf.nist.gov/26.12). Background for [§12](05-set-partitions.md#12-distinct-items-identical-boxes-stirling-and-bell-numbers) and the MacMahon formula in [§25](09-advanced-topics.md#25-other-partition-families).
5. **NIST DLMF**, [§26.17: The Twelvefold Way](https://dlmf.nist.gov/26.17). The full distinguishable/identical × injective/surjective/any table that [§14](06-synthesis.md#14-the-four-cases-side-by-side) summarizes.

## Pitfalls and practice

1. **Capacity vs multiplicity** (Examples A and B): the most common modeling error in this folder.
2. **Loop direction** after compressing a 2D table: old values sweep down, new values sweep up ([§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates)).
3. **Edge cases** $k=0$, $n=0$, cap 0, $r=0$, $k>nL$: test each, as `main` does.
4. **Exact vs modular vs approximate.** Know which one the problem asks for before choosing a method.

Practice: coin change II; partition numbers mod $10^9+7$; distribute candies with limits; partition a set into $k$ nonempty subsets; count partitions into distinct parts; necklace counting with Burnside.

Back to the [Counting Distributions overview](README.md).
