# Search on the Answer — Binary Search Over a Yes/No Question

## 1. The integer square root

**Problem.** Given a whole number `n ≥ 0`, find the largest whole number `r` with `r · r ≤ n`. For `n = 40` the answer is 6: 6² = 36 ≤ 40 and 7² = 49 > 40.

**Brute force.** Try `r = 0, 1, 2, …` until `r²` passes `n`: about √n steps, a million for `n = 10¹²`.

**The key observation.** There is no array, but every candidate `r` has a yes/no question, "is `r² > n`?", and the answers are monotone because squares grow with `r`:

```text
r        :  0  1  2  3  4  5  6  7  8  9 ...
r*r > 40 :  F  F  F  F  F  F  F  T  T  T ...
```

So this is `first_true` from [Boundaries](02-boundaries.md#4-one-search-the-first-true-of-a-monotone-predicate), searching over **candidate answers** instead of array indexes. The answer is the first `True` minus 1.

**The search range.** `r = 0` is the smallest candidate, and `(n + 1)² > n`, so the first `True` is at most `n + 1`. Search `[0, n + 1)`.

**Trace** for `n = 40`:

| Step | `lo` | `hi` | `mid` | `mid²` | `ok(mid)` | Action |
|---:|---:|---:|---:|---:|---|---|
| 1 | 0 | 41 | 20 | 400 | T | `hi = 20` |
| 2 | 0 | 20 | 10 | 100 | T | `hi = 10` |
| 3 | 0 | 10 | 5 | 25 | F | `lo = 6` |
| 4 | 6 | 10 | 8 | 64 | T | `hi = 8` |
| 5 | 6 | 8 | 7 | 49 | T | `hi = 7` |
| 6 | 6 | 7 | 6 | 36 | F | `lo = 7` |
| 7 | 7 | 7 | — | — | — | first `True` is 7, answer 6 |

For `n = 10¹²` the search makes about 40 checks instead of a million.

```python
import math
import random


def first_true(lo: int, hi: int, ok) -> int:
    """Smallest i in [lo, hi) with ok(i), or hi. ok must be F..F T..T."""
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def isqrt(n: int) -> int:
    """Largest r with r * r <= n."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    # For r >= 1, r > n // r is the same test as r * r > n, without the big product.
    return first_true(0, n + 1, lambda r: r > 0 and r > n // r) - 1


def main():
    assert isqrt(40) == 6
    rng = random.Random(9)
    for n in list(range(2000)) + [rng.randint(0, 10**30) for _ in range(2000)]:
        assert isqrt(n) == math.isqrt(n)


if __name__ == "__main__":
    main()
```

**Time:** O(log n) checks, each O(1). **Space:** O(1).

**Why `r > n // r`?** In C++ or Java, `mid * mid` overflows a 64-bit integer once `mid` passes about 3·10⁹, and the range for a 64-bit `n` contains such values. For `r ≥ 1`, `r · r > n` holds exactly when `r > ⌊n / r⌋`, which never overflows.

## 2. Minimum eating speed

**Problem.** Pile `i` holds `piles[i]` bananas. An eater picks a speed `k`; each hour it eats `k` bananas from one pile, or the rest of that pile if fewer remain. Find the **smallest** `k` that finishes everything within `h` hours. For `piles = [3, 6, 7, 11]`, `h = 8`, the answer is 4.

**Brute force.** Try `k = 1, 2, 3, …`: O(n · max(piles)), too slow for piles of a billion.

**Checking one speed.** A pile of `p` takes ⌈p / k⌉ hours, which is `(p + k - 1) // k` in integer arithmetic. Eating faster never takes longer, so `ok(k)`: "`hours(k) ≤ h`" is monotone:

```text
k        :  1   2   3   4   5   6  ...  11
hours(k) : 27  15  10   8   8   6  ...   4
ok(k)    :  F   F   F   T   T   T  ...   T
```

**Range.** `k = max(piles)` takes `n` hours, one per pile, and nothing can do better, so a solution exists exactly when `h ≥ n`. Search `[1, max(piles) + 1)`.

**Trace:**

| Step | `lo` | `hi` | `mid` | `hours(mid)` | `ok` | Action |
|---:|---:|---:|---:|---:|---|---|
| 1 | 1 | 12 | 6 | 6 | T | `hi = 6` |
| 2 | 1 | 6 | 3 | 10 | F | `lo = 4` |
| 3 | 4 | 6 | 5 | 8 | T | `hi = 5` |
| 4 | 4 | 5 | 4 | 8 | T | `hi = 4` → answer 4 |

**Time:** O(n log M), with `M = max(piles)`. The code is in the script after §4.

## 3. Ship packages within `D` days: a greedy check

**Problem.** Packages with weights `w[0], w[1], …` ship **in order**. Each day the ship loads from the front of the line until the next package would exceed its capacity `c`. Find the smallest `c` that ships everything within `D` days. For `w = [1, 2, …, 10]`, `D = 5`, the answer is 15: `[1 2 3 4 5] [6 7] [8] [9] [10]`.

**Brute force.** Try every way to cut the line into at most `D` groups. Exponential, but a good independent test.

**Checking one capacity.** Eating speed had a formula; here the check is a **greedy** simulation: load each day while the next package fits, then start a new day.

**Why greedy is right.** Compare it with any valid schedule for capacity `c`. On day 1 greedy ships as many packages as fit, so it is at least level. If it is level or ahead at the start of a day, it can load at least as far as the other schedule that day. So greedy never needs more days.

**Monotone.** A schedule that works with capacity `c` also works with `c + 1`.

**Range.** The heaviest package must fit, so `c ≥ max(w)`; `c = sum(w)` ships everything on day 1. Search `[max(w), sum(w) + 1)`.

**Trace:**

| Step | `lo` | `hi` | `mid` | Greedy days | `ok` (≤ 5) | Action |
|---:|---:|---:|---:|---|---|---|
| 1 | 10 | 56 | 33 | `[1..7] [8 9 10]` = 2 | T | `hi = 33` |
| 2 | 10 | 33 | 21 | `[1..6] [7 8] [9 10]` = 3 | T | `hi = 21` |
| 3 | 10 | 21 | 15 | `[1..5] [6 7] [8] [9] [10]` = 5 | T | `hi = 15` |
| 4 | 10 | 15 | 12 | `[1..4] [5 6] [7] [8] [9] [10]` = 6 | F | `lo = 13` |
| 5 | 13 | 15 | 14 | same as 12 = 6 | F | `lo = 15` → answer 15 |

**Time:** O(n log S), with `S = sum(w)`.

## 4. Variant: split array, largest sum

**Problem.** Cut an array of nonnegative numbers into `k` nonempty contiguous pieces so that the **largest piece sum** is as small as possible. For `[7, 2, 5, 10, 8]`, `k = 2`, the best cut is `[7 2 5] [10 8]`, so the answer is 18.

**The key observation.** This is shipping with capacity `c` in `k` days. The only difference is *exactly* `k` pieces versus *at most* `k` days, and they give the same answer: if greedy uses fewer than `k` pieces, split any piece of two or more elements. That never raises a piece sum (the numbers are nonnegative), and with `k ≤ n` there are enough elements to reach exactly `k`.

| `c` | 17 | 18 |
|---|---|---|
| Greedy pieces | `[7 2 5] [10] [8]` = 3 | `[7 2 5] [10 8]` = 2 |
| `ok` (≤ 2) | F | T |

The same shape appears as painters partitioning boards or workers splitting a queue of jobs. If the pieces need not be contiguous, the problem contains bin packing and this greedy check no longer works.

One script for §2–§4. The brute force for shipping and splitting tries every set of cut positions, which checks the greedy argument independently.

```python
import random
from itertools import combinations


def first_true(lo: int, hi: int, ok) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def hours_needed(piles: list[int], k: int) -> int:
    return sum((p + k - 1) // k for p in piles)


def min_eating_speed(piles: list[int], h: int) -> int:
    if not piles or any(p <= 0 for p in piles):
        raise ValueError("need at least one pile, each with a positive count")
    if h < len(piles):
        raise ValueError("impossible: every pile needs at least one hour")
    return first_true(1, max(piles) + 1, lambda k: hours_needed(piles, k) <= h)


def groups_needed(w: list[int], capacity: int) -> int:
    """Greedy: fill each group as far as possible. Requires capacity >= max(w)."""
    groups, load = 1, 0
    for x in w:
        if load + x > capacity:
            groups += 1
            load = 0
        load += x
    return groups


def ship_within_days(w: list[int], days: int) -> int:
    if not w or days < 1 or any(x < 0 for x in w):
        raise ValueError("need nonnegative weights and at least one day")
    return first_true(max(w), sum(w) + 1, lambda c: groups_needed(w, c) <= days)


def split_array(a: list[int], k: int) -> int:
    if not 1 <= k <= len(a):
        raise ValueError("need 1 <= k <= len(a)")
    return ship_within_days(a, k)


def split_brute(a: list[int], k: int) -> int:
    """Try every way to cut a into exactly k nonempty pieces."""
    n = len(a)
    return min(
        max(sum(a[b[j]:b[j + 1]]) for j in range(k))
        for cuts in combinations(range(1, n), k - 1)
        for b in [(0, *cuts, n)]
    )


def main():
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([10**9], 2) == 500_000_000
    try:
        min_eating_speed([1, 1, 1], 2)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    assert ship_within_days(list(range(1, 11)), 5) == 15
    assert split_array([7, 2, 5, 10, 8], 2) == 18
    assert split_array([0, 0, 0], 2) == 0

    rng = random.Random(10)
    for _ in range(2000):
        piles = [rng.randint(1, 30) for _ in range(rng.randint(1, 6))]
        h = rng.randint(len(piles), 40)
        brute = next(k for k in range(1, 31) if hours_needed(piles, k) <= h)
        assert min_eating_speed(piles, h) == brute

        n = rng.randint(1, 8)
        a = [rng.randint(0, 12) for _ in range(n)]
        k = rng.randint(1, n)
        assert split_array(a, k) == split_brute(a, k)
        days = rng.randint(1, n + 2)  # More days than items is fine.
        assert ship_within_days(a, days) == split_brute(a, min(days, n))


if __name__ == "__main__":
    main()
```

**Space:** O(1) for all three.

## 5. Variant: maximize the minimum gap (aggressive cows)

**Problem.** Stalls sit at positions `x[0], x[1], …` on a line. Put `m ≥ 2` cows in different stalls so that the **smallest distance** between two cows is as **large** as possible (the same problem as placing balls to maximize the minimum magnetic force). For stalls `[1, 2, 4, 8, 9]`, `m = 3`, cows at 1, 4, 8 give gaps 3 and 4, so the answer is 3. Gap 4 is impossible: after a cow at 1 the next is at 8 at the earliest, and the third would need 12.

**Checking one gap.** `ok(d)`: "all `m` cows fit with every gap `≥ d`". Greedy: sort, put a cow in the first stall, then in each first stall at least `d` past the previous cow. Placing each cow as far left as possible never hurts, because any valid placement can slide its earliest cow left without breaking a gap.

**Monotone, in the other direction.** If gap `d` works, every smaller gap works with the same placement. So `ok` is `T … T F … F` and we want the **last** `True`: search `bad(d) = not ok(d)` and subtract 1, as in [Boundaries](02-boundaries.md#2-variant-the-last-copy-with-no-lo--mid). Range: `d` in `[1, x[-1] − x[0] + 1)`.

| Step | `lo` | `hi` | `mid` | Greedy placement | `ok` | `bad` | Action |
|---:|---:|---:|---:|---|---|---|---|
| 1 | 1 | 9 | 5 | 1, 8 | F | T | `hi = 5` |
| 2 | 1 | 5 | 3 | 1, 4, 8 | T | F | `lo = 4` |
| 3 | 4 | 5 | 4 | 1, 8 | F | T | `hi = 4` → first bad 4, answer 3 |

**Time:** O(n log n + n log R), with `R = x[-1] − x[0]`. Code after §6.

## 6. Variant: the k-th smallest number in a multiplication table

**Problem.** An `m × n` table holds `i · j` in row `i`, column `j` (from 1). Find the `k`-th smallest value, counting duplicates. For `m = n = 3` the sorted values are `1 2 2 3 3 4 6 6 9`, so the 5th smallest is 3.

**Brute force.** List and sort all `m · n` values: 900 million for a `30,000 × 30,000` table.

**The key observation.** Counting is easy even when listing is not. Row `i` is `i, 2i, …, ni`, so it has `min(v // i, n)` values `≤ v`:

$$
count(v)=\sum_{i=1}^{m}\min\left(\left\lfloor v/i\right\rfloor,\ n\right).
$$

`count` never shrinks as `v` grows, so `ok(v)`: "`count(v) ≥ k`" is monotone and the answer is its first `True`, in `[1, m · n + 1)`.

**Why the answer is a value in the table.** At the first `True` `v`, `count(v − 1) < k ≤ count(v)`. The count rises from `v − 1` to `v` only if some cell equals `v`.

| Step | `lo` | `hi` | `mid` | `count(mid)` by row | Total | `≥ 5`? | Action |
|---:|---:|---:|---:|---|---:|---|---|
| 1 | 1 | 10 | 5 | 3, 2, 1 | 6 | T | `hi = 5` |
| 2 | 1 | 5 | 3 | 3, 1, 1 | 5 | T | `hi = 3` |
| 3 | 1 | 3 | 2 | 2, 1, 0 | 3 | F | `lo = 3` → answer 3 |

The same "count values `≤ v`, then search on `v`" idea finds the k-th smallest in a matrix with sorted rows and columns (count with a staircase walk), the k-th smallest pair distance (count pairs with two pointers), and the k-th smallest fraction.

```python
import random
from itertools import combinations


def first_true(lo: int, hi: int, ok) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def cows_placed(stalls: list[int], gap: int) -> int:
    """Greedy count of cows that fit with every gap >= gap. stalls must be sorted."""
    count, last = 1, stalls[0]
    for x in stalls[1:]:
        if x - last >= gap:
            count += 1
            last = x
    return count


def max_min_gap(stalls: list[int], m: int) -> int:
    if m < 2 or m > len(stalls):
        raise ValueError("need 2 <= m <= number of stalls")
    x = sorted(stalls)
    if len(set(x)) < m:
        return 0  # Two cows must share a position.
    return first_true(1, x[-1] - x[0] + 1, lambda d: cows_placed(x, d) < m) - 1


def kth_in_table(m: int, n: int, k: int) -> int:
    if m < 1 or n < 1 or not 1 <= k <= m * n:
        raise ValueError("need m, n >= 1 and 1 <= k <= m * n")
    if m > n:
        m, n = n, m  # Count over the shorter side.

    def count_at_most(v: int) -> int:
        return sum(min(v // i, n) for i in range(1, m + 1))

    return first_true(1, m * n + 1, lambda v: count_at_most(v) >= k)


def main():
    assert max_min_gap([1, 2, 4, 8, 9], 3) == 3
    assert max_min_gap([5, 4, 3, 2, 1, 1000000000], 2) == 999999999
    assert max_min_gap([4, 4, 4], 2) == 0
    assert kth_in_table(3, 3, 5) == 3
    assert kth_in_table(30000, 30000, 1) == 1

    rng = random.Random(12)
    for _ in range(2000):
        stalls = [rng.randint(0, 30) for _ in range(rng.randint(2, 8))]
        m = rng.randint(2, len(stalls))
        brute = max(min(b - a for a, b in zip(c, c[1:]))
                    for c in combinations(sorted(stalls), m))
        assert max_min_gap(stalls, m) == brute

        rows, cols = rng.randint(1, 9), rng.randint(1, 9)
        k = rng.randint(1, rows * cols)
        values = sorted(i * j for i in range(1, rows + 1) for j in range(1, cols + 1))
        assert kth_in_table(rows, cols, k) == values[k - 1]


if __name__ == "__main__":
    main()
```

**Time:** O(min(m, n) · log(m n)) for the table. **Space:** O(n) for the sorted stalls, O(1) for the table.

## 7. Summary

**The recipe.** When a problem asks for the smallest (or largest) value that makes something possible:

1. **Name the predicate.** Write `ok(v)` as a sentence ("speed `v` finishes in time") and a function that checks it, usually a greedy pass.
2. **Prove it is monotone.** If `v` works, why does `v + 1` (for "smallest") or `v − 1` (for "largest")? This is the step people skip.
3. **Pick the range.** A `lo` at or below the answer, a `hi` past the last value to test. Decide what "nothing works" means.
4. **Search.** Smallest working value: `first_true(lo, hi, ok)`. Largest: `first_true(lo, hi, not ok) − 1`.
5. **Test the checker alone** against a brute force before trusting the search.

The cost is O(log(range) × cost of one check).

| Problem | `ok(v)` | Pattern | Range | Answer | Check |
|---|---|---|---|---|---|
| Integer square root | `v² > n` | `F … T` | `[0, n + 1)` | first `T` − 1 | O(1) |
| Minimum eating speed | hours at `v` ≤ `h` | `F … T` | `[1, max + 1)` | first `T` | O(n) |
| Ship within `D` days | greedy days ≤ `D` | `F … T` | `[max, sum + 1)` | first `T` | O(n) |
| Split array largest sum | greedy pieces ≤ `k` | `F … T` | `[max, sum + 1)` | first `T` | O(n) |
| Aggressive cows | `m` cows fit with gap `v` | `T … F` | `[1, span + 1)` | first `F` − 1 | O(n) |
| k-th in multiplication table | `count(v) ≥ k` | `F … T` | `[1, m n + 1)` | first `T` | O(min(m, n)) |

The wording gives the direction. "**Minimize** the **maximum**" is `F … T`, a first `True`. "**Maximize** the **minimum**" is `T … F`, a last `True`. "k-th smallest" is "first `v` whose count reaches `k`".

## 8. Pitfalls and practice

1. **Skipping the monotonicity argument.** If `ok` is not monotone, binary search returns a confident wrong answer. Print `ok(v)` for a small range and look at the pattern.
2. **A range that misses the answer.** Starting the shipping search at 1 makes the greedy check meaningless (a package heavier than the ship); starting at `max(w) + 1` misses the answer when the heaviest package sets it.
3. **Forgetting the impossible case.** Decide what `first_true` returning `hi` means: often "no solution", which should be an error or a sentinel.
4. **Rounding the wrong way.** ⌈p / k⌉ is `(p + k - 1) // k`, not `p // k + 1` (wrong when `k` divides `p`).
5. **Overflow inside the check.** `mid * mid`, a sum of loads, or a count can overflow a fixed-width integer even when the answer fits.
6. **Exactly `k` versus at most `k`.** Make sure they are equivalent for your problem (§4), or adjust the check.
7. **Real-valued answers.** The integer loop doesn't apply; see [Real Numbers and Unbounded Ranges](05-reals-ternary-and-unbounded.md).

Practice: sqrt(x); valid perfect square; Koko eating bananas; capacity to ship packages within D days; split array largest sum; minimum number of days to make m bouquets; find the smallest divisor given a threshold; magnetic force between two balls; aggressive cows; kth smallest number in multiplication table; kth smallest element in a sorted matrix; find k-th smallest pair distance; minimized maximum of products distributed to any store.

Next: [Beyond Sorted Arrays](04-beyond-sorted-arrays.md).
