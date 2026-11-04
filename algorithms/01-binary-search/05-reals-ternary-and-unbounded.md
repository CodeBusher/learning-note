# Real Numbers and Unbounded Ranges — Bisection, Ternary Search, Galloping

## 1. Binary search on real numbers

**Problem.** Find the real number `x ≥ 0` with `x³ = 10` (the cube root of 10, about 2.15443), using only multiplication.

**The key observation.** `x³ ≥ 10` is monotone in `x`, but there is no "next number": the range never shrinks to one point, so you must decide when it is narrow enough. Both ends move to `mid`, with no `+ 1`.

**Trace**, starting from `[0, 10]`:

| Step | `lo` | `hi` | `mid` | `mid³` | `≥ 10`? | Action |
|---:|---:|---:|---:|---:|---|---|
| 1 | 0 | 10 | 5 | 125 | yes | `hi = 5` |
| 2 | 0 | 5 | 2.5 | 15.625 | yes | `hi = 2.5` |
| 3 | 0 | 2.5 | 1.25 | 1.953 | no | `lo = 1.25` |
| 4 | 1.25 | 2.5 | 1.875 | 6.592 | no | `lo = 1.875` |
| 5 | 1.875 | 2.5 | 2.1875 | 10.468 | yes | `hi = 2.1875` |

Each step halves the width, so after `s` steps it is `10 / 2ˢ`; it never reaches 0.

**When to stop: two styles.**

- **Fixed iteration count.** Run exactly 100 iterations. A 64-bit float has a 53-bit mantissa, so by then `lo` and `hi` are adjacent floats or equal. It always ends and needs no tuning.
- **Epsilon loop.** `while hi − lo > eps`. It can **loop forever**: near 10⁸, neighboring floats are about 1.5 · 10⁻⁸ apart. With `eps = 1e−9`, once `lo` and `hi` are neighbors, `mid` rounds to one of them and the width stays above `eps`. Use a relative tolerance, `eps · max(1, |lo|)`, or a fixed count.

**A practical example: maximum average subarray of length at least `k`.** Given numbers `a` and `k`, find the largest average of any contiguous subarray with at least `k` elements. For `a = [1, 12, −5, −6, 50, 3]`, `k = 4`, the answer is 12.75, from `[12, −5, −6, 50]`.

The answer is real, so search on it. `ok(v)`: "some subarray of length `≥ k` has average `≥ v`". Subtracting `v` from every element turns "average `≥ v`" into "sum `≥ 0`". With prefix sums `P` of `a[i] − v` ([Range Queries](../04-range-queries/README.md)), `a[s:e]` has sum `P[e] − P[s]`, so we need some `e` with `P[e] − min(P[0..e−k]) ≥ 0`: one O(n) pass. A smaller target is easier, so `ok` is `T … T F … F` and the answer is its last `True`:

| `v` | 10 | 12 | 12.75 | 13 |
|---|---|---|---|---|
| `ok(v)` | T | T | T | F |

```python
import math
import random


def bisect_real(lo: float, hi: float, ok, iterations: int = 100) -> float:
    """ok is False..False True..True on [lo, hi]; return the boundary."""
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid  # No + 1 and no - 1: reals have no neighbor.
        else:
            lo = mid
    return hi


def cube_root(x: float) -> float:
    if x < 0:
        raise ValueError("x must be nonnegative")
    return bisect_real(0.0, max(1.0, x), lambda m: m * m * m >= x)


def epsilon_loop_steps(x: float, eps: float, max_steps: int = 10_000) -> int:
    """Run the epsilon-style loop; return the step count, or max_steps if stuck."""
    lo, hi = 0.0, max(1.0, x)
    steps = 0
    while hi - lo > eps and steps < max_steps:
        mid = (lo + hi) / 2
        if mid * mid * mid >= x:
            hi = mid
        else:
            lo = mid
        steps += 1
    return steps


def max_average(a: list[float], k: int) -> float:
    if not 1 <= k <= len(a):
        raise ValueError("need 1 <= k <= len(a)")

    def ok(v: float) -> bool:
        prefix = [0.0]
        for x in a:
            prefix.append(prefix[-1] + x - v)
        best_start = math.inf
        for e in range(k, len(a) + 1):
            best_start = min(best_start, prefix[e - k])
            if prefix[e] - best_start >= 0:
                return True
        return False

    # ok is T..T F..F on [min, max]; the answer is where "not ok" starts.
    return bisect_real(min(a), max(a), lambda v: not ok(v))


def max_average_brute(a: list[float], k: int) -> float:
    n = len(a)
    return max(sum(a[s:e]) / (e - s) for s in range(n) for e in range(s + k, n + 1))


def main():
    assert abs(cube_root(10) - 10 ** (1 / 3)) < 1e-12
    assert abs(cube_root(1e24) - 1e8) < 1e-6
    assert cube_root(0) < 1e-15
    assert epsilon_loop_steps(10, 1e-9) < 100  # Small numbers: fine.
    assert epsilon_loop_steps(1e24, 1e-9) == 10_000  # Near 1e8: stuck forever.

    assert abs(max_average([1, 12, -5, -6, 50, 3], 4) - 12.75) < 1e-9
    rng = random.Random(18)
    for _ in range(500):
        a = [rng.randint(-20, 20) for _ in range(rng.randint(1, 9))]
        k = rng.randint(1, len(a))
        assert abs(max_average(a, k) - max_average_brute(a, k)) < 1e-7


if __name__ == "__main__":
    main()
```

**Time:** O(I · cost of `ok`), where `I` is the iteration count: O(I) for the cube root, O(I · n) for the maximum average. **Space:** O(1) and O(n).

## 2. Ternary search on unimodal functions

**Problem.** A function `f` is **unimodal** on `[lo, hi]` if it strictly increases up to a single maximum and strictly decreases after it. Find the maximum. Example: `f(x) = x · e^(−x)` on `[0, 10]`, whose maximum is at `x = 1`, with value `1/e ≈ 0.3679`.

**The key observation.** Pick `m1 < m2` inside the range. If `f(m1) < f(m2)`, the maximum can't be left of `m1`, where `f` is still climbing; discard `[lo, m1]`. Otherwise discard `[m2, hi]`. With `m1`, `m2` at the thirds, each step keeps 2/3 of the range: **ternary search**.

**Trace** on `[0, 10]`:

| Step | `lo` | `hi` | `m1` | `m2` | `f(m1)` | `f(m2)` | Action |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0 | 10 | 3.333 | 6.667 | 0.1189 | 0.0085 | `hi = 6.667` |
| 2 | 0 | 6.667 | 2.222 | 4.444 | 0.2408 | 0.0522 | `hi = 4.444` |
| 3 | 0 | 4.444 | 1.481 | 2.963 | 0.3367 | 0.1531 | `hi = 2.963` |
| 4 | 0 | 2.963 | 0.988 | 1.975 | 0.3679 | 0.2740 | `hi = 1.975` |
| 5 | 0 | 1.975 | 0.658 | 1.317 | 0.3408 | 0.3529 | `lo = 0.658` |

The range closes in on 1. Use a fixed count again: 200 iterations shrink it by (2/3)²⁰⁰ ≈ 10⁻³⁵.

**The integer-domain pitfall.** On integers, two things go wrong.

1. **Termination.** With integer thirds, a range of width 2 or less can produce `m1 == lo` and `m2 == hi`, and the range stops shrinking. Stop when `hi − lo ≤ 2` and check the last few points directly.
2. **Plateaus.** If `f` is only *weakly* unimodal (flat stretches allowed), `f(m1) == f(m2)` gives no information. On `f = [0, 0, 0, 0, 0, 0, 0, 9, 0]`, the first step has `m1 = 2`, `m2 = 6`, both 0, and discarding `[m2, hi]` throws away the 9. No method beats a scan on such inputs.

For a strictly unimodal function on integers there is a cleaner way: "`f(i) > f(i + 1)`" is monotone, so `first_true` finds the maximum in O(log n) with fewer evaluations than ternary search. This is the peak search from [Beyond Sorted Arrays](04-beyond-sorted-arrays.md#2-finding-a-peak).

**Time:** O(log(range)) evaluations of `f`; the code is in the script after §3.

## 3. Exponential (galloping) search

**Problem.** Sometimes the range has no known end: a sorted array hidden behind a reader whose `get(i)` returns a huge sentinel past the end, with no way to ask for the length, or a search on the answer with no obvious upper bound. Find the first index with `get(i) ≥ target`.

**The key observation.** Find an upper end by **doubling**: check positions 1, 2, 4, 8, … until the predicate becomes true. The last false position and the first true one bracket the answer, and an ordinary `first_true` finishes the job.

**Trace** for `target = 9` in a hidden array `[−1, 0, 3, 5, 9, 12]` (the sentinel is returned past index 5):

| Step | Checked index | `get` | `≥ 9`? | Bracket so far |
|---:|---:|---:|---|---|
| 1 | 0 | −1 | no | answer > 0 |
| 2 | 1 | 0 | no | answer > 1 |
| 3 | 2 | 3 | no | answer > 2 |
| 4 | 4 | 9 | yes | answer in `[3, 4]` |
| 5 | `first_true(3, 4)`: checks 3 | 5 | no | answer 4 |

If the answer is at position `p`, doubling takes about log₂ p steps and the final search another log₂ p, so the total is O(log p), independent of the (unknown) array length. This is why the method is also used when the answer is likely to be **near the start**: Timsort's merge step "gallops" this way to skip long runs, and intersecting a short sorted list with a very long one can use it to jump ahead.

One script for §2 and §3:

```python
import math
import random


def first_true(lo: int, hi: int, ok) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def first_true_unbounded(start: int, ok) -> int:
    """Smallest i >= start with ok(i). ok must be F..F T..T and True somewhere."""
    if ok(start):
        return start
    last_false, step = start, 1
    while not ok(start + step):
        last_false = start + step
        step *= 2
    return first_true(last_false + 1, start + step, ok)


def ternary_max_real(f, lo: float, hi: float, iterations: int = 200) -> float:
    for _ in range(iterations):
        m1 = lo + (hi - lo) / 3
        m2 = hi - (hi - lo) / 3
        if f(m1) < f(m2):
            lo = m1
        else:
            hi = m2
    return (lo + hi) / 2


def ternary_max_int(f, lo: int, hi: int) -> int:
    """Argmax of a strictly unimodal f on the closed range [lo, hi]."""
    while hi - lo > 2:
        m1 = lo + (hi - lo) // 3
        m2 = hi - (hi - lo) // 3
        if f(m1) < f(m2):
            lo = m1 + 1
        else:
            hi = m2 - 1
    return max(range(lo, hi + 1), key=f)


def binary_max_int(f, lo: int, hi: int) -> int:
    """Argmax of a strictly unimodal f on [lo, hi], via the first descent."""
    return first_true(lo, hi, lambda i: f(i) > f(i + 1))


def random_unimodal(rng: random.Random) -> list[int]:
    left = sorted(rng.sample(range(50), rng.randint(0, 8)))
    right = sorted(rng.sample(range(50), rng.randint(0, 8)), reverse=True)
    return left + [100] + right


class Reader:
    SENTINEL = 2**31 - 1

    def __init__(self, data: list[int]):
        self._data = data
        self.calls = 0

    def get(self, i: int) -> int:
        self.calls += 1
        return self._data[i] if 0 <= i < len(self._data) else self.SENTINEL


def search_unknown_size(reader: Reader, target: int) -> int:
    i = first_true_unbounded(0, lambda k: reader.get(k) >= target)
    return i if reader.get(i) == target else -1


def main():
    reader = Reader([-1, 0, 3, 5, 9, 12])
    assert search_unknown_size(reader, 9) == 4
    assert search_unknown_size(reader, 2) == -1
    assert first_true_unbounded(0, lambda v: v * v >= 10**12) == 10**6

    rng = random.Random(20)
    for _ in range(2000):
        data = sorted(rng.sample(range(-50, 50), rng.randint(0, 20)))
        target = rng.randint(-55, 55)
        expected = data.index(target) if target in data else -1
        assert search_unknown_size(Reader(data), target) == expected

    big = Reader(list(range(10**6)))
    assert search_unknown_size(big, 5) == 5
    assert big.calls < 15  # O(log p) calls, where p = 5, not O(log 10**6).

    x = ternary_max_real(lambda t: t * math.exp(-t), 0.0, 10.0)
    assert abs(x - 1.0) < 1e-6

    plateau = [0, 0, 0, 0, 0, 0, 0, 9, 0]
    m1, m2 = 0 + 8 // 3, 8 - 8 // 3
    assert (m1, m2) == (2, 6) and plateau[m1] == plateau[m2]  # No information.

    rng = random.Random(19)
    for _ in range(3000):
        f = random_unimodal(rng)
        best = f.index(max(f))
        g = f.__getitem__
        assert ternary_max_int(g, 0, len(f) - 1) == best
        assert binary_max_int(g, 0, len(f) - 1) == best


if __name__ == "__main__":
    main()
```

**Time:** O(log p), where `p` is the answer's position. **Space:** O(1).

## 4. Summary

| Situation | Loop | Update | Stop |
|---|---|---|---|
| Integer, known range | `first_true(lo, hi, ok)` | `hi = mid` / `lo = mid + 1` | `lo == hi` |
| Real, monotone | bisection | `hi = mid` / `lo = mid` | fixed count (100), or relative tolerance |
| Real, unimodal | ternary search | drop the third beyond the lower of `f(m1)`, `f(m2)` | fixed count (200) |
| Integer, strictly unimodal | `first_true` on `f(i) > f(i + 1)` | as for integers | `lo == hi` |
| Integer, no known upper end | double until `ok`, then `first_true` | — | O(log p) total |

## 5. Pitfalls and practice

1. **Epsilon loops on large real values.** Near 10⁸, neighboring floats are 1.5 · 10⁻⁸ apart (§1). Use a fixed count or a relative tolerance.
2. **Writing `lo = mid + 1` on reals.** Real-valued searches move both ends to `mid`; there is no "next" real number.
3. **Comparing floating answers with `==`.** Test with a tolerance.
4. **Ternary search on plateaus.** It needs strict unimodality; with flat stretches, `f(m1) == f(m2)` tells you nothing.
5. **Ternary search on tiny integer ranges.** Integer thirds stop shrinking at width 2; finish with a scan, or use the first-descent binary search instead.
6. **Doubling without a guaranteed true value.** Exponential search runs forever if the predicate never becomes true. Make sure a sentinel or bound exists, and in fixed-width languages make sure `start + step` can't overflow.

Practice: sqrt(x) to a given precision; cube root by bisection; maximum average subarray II; minimize max distance to gas station; find in mountain array; peak index in a mountain array (as ternary search, then as binary search); search in a sorted array of unknown size; find the smallest `k` with a property and no known upper bound (exponential search plus `first_true`).

Back to the [Binary Search overview](README.md).
