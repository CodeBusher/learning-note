# Faster Transitions — Same Recurrence, Cheaper Best Predecessor

## 1. A sliding-window minimum: the monotonic deque

Stones `0 … n−1` have landing costs `cost[i]`. You start on stone 0 (paying its cost), jump forward by 1 to `K` stones at a time, and must end on stone `n − 1`. Minimize the total cost of the stones you land on. For `cost = [1, 3, 2, 5, 1, 4, 2]`, `K = 3`, the path `0 → 2 → 4 → 6` costs `1 + 2 + 1 + 2 = 6`, the best.

**The slow DP is correct.** `dp[i]` = the cheapest path ending on stone `i`; the last decision is the stone `j` jumped from:

$$
dp[i] = cost[i] + \min_{\max(0,\, i-K) \le j < i} dp[j], \qquad dp[0] = cost[0].
$$

**It is too slow.** DP time is roughly (number of states) × (work per transition). Here that is `n` states × up to `K` predecessors = O(nK): 15 billion comparisons for `n = 200,000`, `K = 100,000`. There are two ways out: fewer states (a modeling change, as in earlier chapters) or a **cheaper transition**, keeping every state but finding the best predecessor in less than O(K). Every technique below is the second kind, and each works only under a condition that must be checked. (Rolling arrays are a third thing: they save memory, rarely time.)

**The condition here.** The inner `min` runs over a window of indices that slides right as `i` grows: candidates **enter in order and expire in order**, and a candidate's value `dp[j]` does not depend on `i`.

**Dominance.** Take `j1 < j2` with `dp[j2] <= dp[j1]`. `j2` is at least as cheap and expires later, so every future window containing `j1` also contains `j2`: `j1` can never be needed again and may be deleted. After deleting dominated candidates, the survivors have increasing indices and strictly increasing `dp`, so the front holds the minimum. Each index is appended once and removed at most once: O(n) in total ([Monotonic Stack and Deque](../06-monotonic-stack-and-deque/README.md)).

Each step: drop expired indices from the front, read the front, then pop dominated indices from the back and append `i`.

| i | expire from front | front used | dp[i] | pop from back (dp ≥ dp[i]) | deque after |
|---|---|---|---|---|---|
| 0 | — | — | 1 | — | [0] |
| 1 | — | 0 (dp 1) | 3 + 1 = 4 | — | [0, 1] |
| 2 | — | 0 (dp 1) | 2 + 1 = 3 | 1 (dp 4) | [0, 2] |
| 3 | — | 0 (dp 1) | 5 + 1 = 6 | — | [0, 2, 3] |
| 4 | 0 | 2 (dp 3) | 1 + 3 = 4 | 3 (dp 6) | [2, 4] |
| 5 | — | 2 (dp 3) | 4 + 3 = 7 | — | [2, 4, 5] |
| 6 | 2 | 4 (dp 4) | 2 + 4 = 6 | 5 (dp 7) | [4, 6] |

```python
import random
from collections import deque


def min_jump_cost_slow(cost: list[int], k: int) -> int:
    if not cost or k < 1:
        raise ValueError("need non-empty cost and k >= 1")
    dp = [0] * len(cost)
    dp[0] = cost[0]
    for i in range(1, len(cost)):
        dp[i] = cost[i] + min(dp[j] for j in range(max(0, i - k), i))
    return dp[-1]


def min_jump_cost(cost: list[int], k: int) -> int:
    """O(n): the deque holds window indices with strictly increasing dp values."""
    if not cost or k < 1:
        raise ValueError("need non-empty cost and k >= 1")
    n = len(cost)
    dp = [0] * n
    window: deque[int] = deque()
    for i in range(n):
        while window and window[0] < i - k:       # expired: too far back to jump from
            window.popleft()
        dp[i] = cost[i] + (dp[window[0]] if i > 0 else 0)
        while window and dp[window[-1]] >= dp[i]:  # dominated by the newer index i
            window.pop()
        window.append(i)
    return dp[-1]


def main():
    assert min_jump_cost([1, 3, 2, 5, 1, 4, 2], 3) == 6
    assert min_jump_cost([4], 1) == 4
    assert min_jump_cost([1, -5, 2, -3], 1) == -5
    rng = random.Random(23)
    for _ in range(1000):
        n = rng.randint(1, 40)
        k = rng.randint(1, 8)
        cost = [rng.randint(-10, 10) for _ in range(n)]
        assert min_jump_cost(cost, k) == min_jump_cost_slow(cost, k)


if __name__ == "__main__":
    main()
```

O(n) time, O(K) extra space. For `i > 0` the deque is never empty after expiry: index `i − 1` was appended last and is still in the window.

**Variant: max.** "Pick a subsequence whose consecutive indices are at most `K` apart; maximize the sum" is `dp[i] = a[i] + max(0, max dp[j])` over the same window. Keep `dp` strictly decreasing and pop while `dp[back] <= dp[i]`.

**When it fails.** If the transition is `dp[j] + f(j, i)` and two candidates can swap order as `i` grows, a deleted candidate might have become best later. Dominance is gone, and so is the deque.

## 2. A sliding-window sum: prefix sums

Count the ways to climb from step 0 to step `n` when each move climbs between `lo` and `hi` steps, order mattering, modulo `1,000,000,007`. For `n = 6`, `lo = 2`, `hi = 3`: `3 + 3` and `2 + 2 + 2`, so 2.

$$
dp[i] = \sum_{j = i - hi}^{i - lo} dp[j] \quad (\text{only } j \ge 0), \qquad dp[0] = 1.
$$

Slow: O(n · (hi − lo + 1)). **What differs from §1:** the inner operation is a **sum** over a range with known ends, and sums can be undone by subtraction. With `P[x] = dp[0] + … + dp[x − 1]`, the range sum is `P[right + 1] − P[left]` ([Prefix Sums](../04-range-queries/01-prefix-sums.md)). `P` grows as we go: the range for `dp[i]` ends at `i − lo < i`, so its prefix sums are ready.

| i | range of j | dp[i] = P[right+1] − P[left] | P[i+1] |
|---|---|---|---|
| 0 | base case | 1 | 1 |
| 1 | empty | 0 | 1 |
| 2 | [0, 0] | P[1] − P[0] = 1 | 2 |
| 3 | [0, 1] | P[2] − P[0] = 1 | 3 |
| 4 | [1, 2] | P[3] − P[1] = 1 | 4 |
| 5 | [2, 3] | P[4] − P[2] = 2 | 6 |
| 6 | [3, 4] | P[5] − P[3] = 2 | 8 |

```python
import random


MOD = 1_000_000_007


def count_ways_slow(n: int, lo: int, hi: int) -> int:
    """O(n * (hi - lo + 1)) reference."""
    if n < 0 or not 1 <= lo <= hi:
        raise ValueError("need n >= 0 and 1 <= lo <= hi")
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        total = 0
        for j in range(max(0, i - hi), i - lo + 1):
            total += dp[j]
        dp[i] = total % MOD
    return dp[n]


def count_ways(n: int, lo: int, hi: int) -> int:
    """O(n): each range sum is one subtraction of prefix sums."""
    if n < 0 or not 1 <= lo <= hi:
        raise ValueError("need n >= 0 and 1 <= lo <= hi")
    dp = [0] * (n + 1)
    prefix = [0] * (n + 2)          # prefix[x] = dp[0] + ... + dp[x-1]
    dp[0] = 1
    prefix[1] = 1
    for i in range(1, n + 1):
        right = i - lo
        if right >= 0:
            left = max(0, i - hi)
            dp[i] = (prefix[right + 1] - prefix[left]) % MOD
        prefix[i + 1] = (prefix[i] + dp[i]) % MOD
    return dp[n]


def main():
    assert count_ways(6, 2, 3) == 2
    assert count_ways(0, 1, 1) == 1
    assert count_ways(1, 2, 5) == 0
    assert count_ways(10, 1, 2) == 89          # Fibonacci stairs
    rng = random.Random(12)
    for _ in range(500):
        n = rng.randint(0, 60)
        lo = rng.randint(1, 6)
        hi = rng.randint(lo, 9)
        assert count_ways(n, lo, hi) == count_ways_slow(n, lo, hi)
    try:
        count_ways(5, 3, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

O(n) time and space. Python's `%` is never negative; in C++ or Java add `MOD` before taking the remainder of a difference.

**When it fails.** `min` and `max` cannot be undone: the minimum of `dp[0..9]` and of `dp[0..4]` says nothing about `dp[5..9]`. That is why §1 needed a deque.

## 3. The best predecessor with a smaller key: a Fenwick tree

Find the maximum sum of a non-empty **strictly increasing subsequence**. For `a = [3, 1, 4, 1, 5, 9, 2, 6]` it is `3 + 4 + 5 + 9 = 21`.

`dp[i]` = the best sum of an increasing subsequence **ending at `i`**; the previous element `j` needs `j < i` and `a[j] < a[i]`:

$$
dp[i] = a[i] + \max\Bigl(0,\ \max_{j < i,\ a[j] < a[i]} dp[j]\Bigr).
$$

This is the weighted longest increasing subsequence ([Sequences and Strings](06-sequences-and-strings.md)), O(n²) as written.

**What differs.** The legal predecessors are scattered, not a window. But each legality rule can be handled by an **order**:

- `j < i`: process indices left to right, so exactly the `j < i` are inserted when `i` is reached.
- `a[j] < a[i]`: store each finished `dp[j]` at position `rank(a[j])`, where `rank` numbers the distinct values `1, 2, 3, …` in sorted order (**coordinate compression**). "Smaller values" becomes "positions `1 … rank(a[i]) − 1`", a prefix.

Each state asks a **prefix maximum**; each finished state makes a **point update that only increases**. A [Fenwick tree](../04-range-queries/02-fenwick-tree.md) does both in O(log n). A prefix-max Fenwick tree works only because stored values never decrease; for arbitrary updates or ranges use a [segment tree](../04-range-queries/03-segment-tree.md). Strictly increasing queries up to `rank − 1`; non-decreasing would query up to `rank`.

Ranks for `[1, 2, 3, 4, 5, 6, 9]` are `1..7`. The tree starts at zeros, and a zero answer means "start fresh", the `max(0, …)`.

| i | a[i] | rank | prefix max over ranks < rank | dp[i] |
|---|---|---|---|---|
| 0 | 3 | 3 | 0 | 3 |
| 1 | 1 | 1 | 0 | 1 |
| 2 | 4 | 4 | 3 | 7 |
| 3 | 1 | 1 | 0 | 1 |
| 4 | 5 | 5 | 7 | 12 |
| 5 | 9 | 7 | 12 | **21** |
| 6 | 2 | 2 | 1 | 3 |
| 7 | 6 | 6 | 12 | 18 |

```python
import random


class PrefixMaxFenwick:
    """Positions 1..size. update raises a value; query returns max over 1..pos (0 if empty)."""

    def __init__(self, size: int):
        self.tree = [0] * (size + 1)

    def update(self, pos: int, value: int) -> None:
        while pos < len(self.tree):
            if value > self.tree[pos]:
                self.tree[pos] = value
            pos += pos & -pos

    def query(self, pos: int) -> int:
        best = 0
        while pos > 0:
            if self.tree[pos] > best:
                best = self.tree[pos]
            pos -= pos & -pos
        return best


def max_increasing_sum_slow(a: list[int]) -> int:
    if not a:
        raise ValueError("a must be non-empty")
    dp = []
    for i, value in enumerate(a):
        best = 0
        for j in range(i):
            if a[j] < value:
                best = max(best, dp[j])
        dp.append(value + best)
    return max(dp)


def max_increasing_sum(a: list[int]) -> int:
    """O(n log n) with coordinate compression and a prefix-max Fenwick tree."""
    if not a:
        raise ValueError("a must be non-empty")
    rank = {v: r for r, v in enumerate(sorted(set(a)), start=1)}
    tree = PrefixMaxFenwick(len(rank))
    answer = None
    for value in a:
        r = rank[value]
        dp_i = value + tree.query(r - 1)   # strictly smaller values only
        tree.update(r, dp_i)
        answer = dp_i if answer is None else max(answer, dp_i)
    return answer


def main():
    assert max_increasing_sum([3, 1, 4, 1, 5, 9, 2, 6]) == 21
    assert max_increasing_sum([5, 5, 5]) == 5
    assert max_increasing_sum([-3, -1, -2]) == -1
    rng = random.Random(34)
    for _ in range(1000):
        n = rng.randint(1, 30)
        a = [rng.randint(-8, 12) for _ in range(n)]
        assert max_increasing_sum(a) == max_increasing_sum_slow(a)


if __name__ == "__main__":
    main()
```

O(n log n) time, O(n) space. A negative `dp[j]` is never stored, since the tree only keeps larger values than 0; that is right, because extending a negative-sum subsequence never beats starting fresh.

**Variants.** Separate weights `w[i]`: replace `value + …` with `w[i] + …`. Two-dimensional conditions (`x[j] < x[i]` and `y[j] < y[i]`, no index order): sort by `x`, process equal `x` as a group so they cannot see each other, and index the tree by `y`.

## 4. Monotone choices across layers: divide-and-conquer optimization

Split an array of **non-negative** integers into exactly `t` non-empty consecutive groups; a group costs the square of its sum. Minimize the total. For `a = [1, 3, 2, 4]`, `t = 2`: `[1 | 3, 2, 4]` costs 82, `[1, 3 | 2, 4]` costs 52, `[1, 3, 2 | 4]` costs 52. Answer 52.

With prefix sums `P`, the group `a[k:j]` costs `C(k, j) = (P[j] − P[k])²`, and

$$
dp[g][j] = \min_{g-1 \le k < j} \bigl(dp[g-1][k] + C(k, j)\bigr), \qquad dp[0][0] = 0,
$$

with other `dp[0][j] = inf`; `k >= g − 1` lets the first `k` elements form `g − 1` groups. O(t n²).

**The property.** Let `opt(j)` be the **smallest** best `k` for `dp[g][j]`. The method needs `opt(j) <= opt(j + 1)`: as the prefix grows, the best start of the last group never moves left.

**How it is used.** To fill `j ∈ [lo, hi]` knowing the answers lie in `[opt_lo, opt_hi]`: take the middle `mid`, scan `k` from `opt_lo` to `min(opt_hi, mid − 1)`, record the best `k*`. Then `j < mid` searches `[opt_lo, k*]` and `j > mid` searches `[k*, opt_hi]`. At each recursion depth the scanned ranges overlap only at endpoints, so a depth costs O(n), a layer O(n log n), and the DP O(t n log n).

**Trace.** `P = [0, 1, 4, 6, 10]`; layer 1 is `dp[1][j] = P[j]²` = `[inf, 1, 16, 36, 100]`.

| call | mid | k scanned | values `dp[1][k] + (P[mid] − P[k])²` | best k | dp[2][mid] |
|---|---|---|---|---|---|
| j ∈ [2,4], k ∈ [1,3] | 3 | 1, 2 | 1 + 25 = 26, 16 + 4 = 20 | 2 | 20 |
| j ∈ [2,2], k ∈ [1,2] | 2 | 1 | 1 + 9 = 10 | 1 | 10 |
| j ∈ [4,4], k ∈ [2,3] | 4 | 2, 3 | 16 + 36 = 52, 36 + 16 = 52 | 2 | 52 |

The last call never looked at `k = 1` and still found 52.

### 4.1 Proof that `opt` is monotone

A sufficient condition is the **quadrangle inequality** (Monge condition): for all `a ≤ b ≤ c ≤ d`,

$$
C(a, c) + C(b, d) \le C(a, d) + C(b, c),
$$

"two crossing intervals cost no more than one long plus one nested short interval".

**It holds for squared sums.** With `u, v, w, z = P[a], P[b], P[c], P[d]`,

$$
C(a,d) + C(b,c) - C(a,c) - C(b,d) = (z-u)^2 + (w-v)^2 - (w-u)^2 - (z-v)^2 = 2\,(v-u)(z-w),
$$

and non-negative values make `P` non-decreasing, so both factors are `>= 0`.

**It implies monotone `opt`.** Let `F(k, j) = dp[g−1][k] + C(k, j)`; adding a term in `k` alone keeps the inequality. Suppose `j1 < j2` but `k2 = opt(j2) < k1 = opt(j1)`, so `k2 < k1 < j1 < j2`. Since `k1` is the smallest best choice for `j1`, `F(k2, j1) > F(k1, j1)`. The inequality with `(a, b, c, d) = (k2, k1, j1, j2)` gives `F(k2, j1) + F(k1, j2) <= F(k2, j2) + F(k1, j1)`. Subtracting: `F(k1, j2) < F(k2, j2)`, so `k2` was not optimal for `j2`. Contradiction. The proof works for an arbitrary previous layer, so every layer may use the trick.

### 4.2 Do not infer the property from examples

Monotone choices look natural and hold on many small inputs. If they fail, the fast method silently skips the optimum. Allow **negative** values and the proof breaks at `2(v − u)(z − w)`. The smallest failure: `a = [-1, 1, 0, -2]`, `t = 2`. The true best is `[-1 | 1, 0, -2]` with cost `1 + 1 = 2`, so `opt(4) = 1`; but `opt(3) = 2` (`[-1, 1 | 0]` costs 0), and the recursion searches `j = 4` only in `k ∈ [2, 3]`, returning 4. Random tests against the slow DP catch bugs, and sometimes a method used outside its conditions, but a passing test never proves a condition.

```python
import random
from math import inf


def prefix_sums(a: list[int]) -> list[int]:
    prefix = [0]
    for x in a:
        prefix.append(prefix[-1] + x)
    return prefix


def check(a: list[int], t: int, allow_negative: bool) -> None:
    if not 1 <= t <= len(a):
        raise ValueError("need 1 <= t <= len(a)")
    if not allow_negative and any(x < 0 for x in a):
        raise ValueError("the monotone-opt proof needs non-negative values")


def min_split_cost_slow(a: list[int], t: int) -> int:
    """O(t n^2) reference; correct for any integers."""
    check(a, t, allow_negative=True)
    n, prefix = len(a), prefix_sums(a)
    prev = [0] + [inf] * n
    for g in range(1, t + 1):
        cur = [inf] * (n + 1)
        for j in range(g, n + 1):
            for k in range(g - 1, j):
                cur[j] = min(cur[j], prev[k] + (prefix[j] - prefix[k]) ** 2)
        prev = cur
    return prev[n]


def min_split_cost(a: list[int], t: int, allow_negative: bool = False) -> int:
    """O(t n log n) divide-and-conquer optimization."""
    check(a, t, allow_negative)
    n, prefix = len(a), prefix_sums(a)
    prev = [0] + [inf] * n

    for g in range(1, t + 1):
        cur = [inf] * (n + 1)

        def solve(lo: int, hi: int, opt_lo: int, opt_hi: int) -> None:
            if lo > hi:
                return
            mid = (lo + hi) // 2
            best, best_k = inf, -1
            for k in range(opt_lo, min(opt_hi, mid - 1) + 1):
                value = prev[k] + (prefix[mid] - prefix[k]) ** 2
                if value < best:            # strict: keeps the smallest best k
                    best, best_k = value, k
            cur[mid] = best
            solve(lo, mid - 1, opt_lo, best_k)
            solve(mid + 1, hi, best_k, opt_hi)

        solve(g, n, g - 1, n - 1)
        prev = cur
    return prev[n]


def main():
    assert min_split_cost([1, 3, 2, 4], 2) == 52
    assert min_split_cost([1, 3, 2, 4], 1) == 100
    assert min_split_cost([1, 3, 2, 4], 4) == 1 + 9 + 4 + 16
    assert min_split_cost([0, 0, 5], 2) == 25
    rng = random.Random(45)
    for _ in range(600):
        n = rng.randint(1, 25)
        t = rng.randint(1, n)
        a = [rng.randint(0, 9) for _ in range(n)]
        assert min_split_cost(a, t) == min_split_cost_slow(a, t)
    # Outside the proof's conditions the shortcut silently skips the optimum.
    assert min_split_cost_slow([-1, 1, 0, -2], 2) == 2
    assert min_split_cost([-1, 1, 0, -2], 2, allow_negative=True) == 4


if __name__ == "__main__":
    main()
```

O(t n log n) time, O(n) space for two layers, recursion depth O(log n).

## 5. Nested choices in an interval DP: Knuth optimization

Piles `w[0..n-1]` (non-negative) stand in a row; merging two **adjacent** piles costs the new pile's size. Merge into one pile at minimum cost. For `w = [3, 1, 2, 4]`: `1 + 2` (3), `3 + 3` (6), `6 + 4` (10), total 19.

This is the interval DP of [Interval DP](07-interval-dp.md): the last merge joins `w[l:k]` and `w[k:r]` and costs `W(l, r) = P[r] − P[l]` wherever the split is:

$$
dp[l][r] = W(l, r) + \min_{l < k < r} \bigl(dp[l][k] + dp[k][r]\bigr), \qquad dp[l][l+1] = 0.
$$

O(n³) as written.

**The property.** With `opt[l][r]` a best split,

$$
opt[l][r-1] \le opt[l][r] \le opt[l+1][r],
$$

so the scan for `[l, r)` only covers the splits between the best splits of its two one-shorter sub-intervals. This is a theorem with conditions. A standard sufficient set (Yao): the recurrence has exactly this form, and for all `a ≤ b ≤ c ≤ d`,

1. the **quadrangle inequality** `W(a, c) + W(b, d) ≤ W(a, d) + W(b, c)`, and
2. **monotonicity on inclusion** `W(b, c) ≤ W(a, d)`.

For `W = P[r] − P[l]`, condition 1 holds with equality and condition 2 because weights are non-negative. The optimal BST qualifies the same way. Matrix chain does **not** fit: its join cost depends on the split `k` itself.

**Why O(n²).** For a fixed length `L`, the scan for `[l, l + L)` costs `opt[l+1][l+L] − opt[l][l+L−1] + 1`. Summing over `l`, the terms telescope to at most `n` plus one per interval: O(n) per length, O(n²) total.

**Trace** (`P = [0, 3, 4, 6, 10]`; length-2 intervals have one split each, so `opt[0][2] = 1`, `opt[1][3] = 2`, `opt[2][4] = 3`, with `dp` = 4, 3, 6):

| interval | allowed splits | candidates `dp[l][k] + dp[k][r]` | best k | dp = W + best |
|---|---|---|---|---|
| [0,3) | 1 .. 2 | k=1: 0+3, k=2: 4+0 | 1 | 6 + 3 = 9 |
| [1,4) | 2 .. 3 | k=2: 0+6, k=3: 3+0 | 3 | 7 + 3 = 10 |
| [0,4) | 1 .. 3 | k=1: 0+10, k=2: 4+6, k=3: 9+0 | 3 | 10 + 9 = 19 |

On this tiny input the ranges cover everything; on longer inputs they shrink to a few candidates.

```python
import random
from math import inf


def merge_cost_slow(w: list[int]) -> int:
    """O(n^3) interval DP reference."""
    if not w or any(x < 0 for x in w):
        raise ValueError("need a non-empty list of non-negative sizes")
    n = len(w)
    prefix = [0]
    for x in w:
        prefix.append(prefix[-1] + x)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            dp[l][r] = prefix[r] - prefix[l] + min(dp[l][k] + dp[k][r] for k in range(l + 1, r))
    return dp[0][n]


def merge_cost(w: list[int]) -> int:
    """O(n^2) with Knuth's bound opt[l][r-1] <= opt[l][r] <= opt[l+1][r]."""
    if not w or any(x < 0 for x in w):
        raise ValueError("need a non-empty list of non-negative sizes")
    n = len(w)
    prefix = [0]
    for x in w:
        prefix.append(prefix[-1] + x)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    opt = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n):
        opt[i][i + 1] = i + 1
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            best, best_k = inf, -1
            lo = max(opt[l][r - 1], l + 1)
            hi = min(opt[l + 1][r], r - 1)
            for k in range(lo, hi + 1):
                value = dp[l][k] + dp[k][r]
                if value < best:
                    best, best_k = value, k
            dp[l][r] = prefix[r] - prefix[l] + best
            opt[l][r] = best_k
    return dp[0][n]


def main():
    assert merge_cost([3, 1, 2, 4]) == 19
    assert merge_cost([5]) == 0
    assert merge_cost([1, 2]) == 3
    rng = random.Random(56)
    for _ in range(500):
        n = rng.randint(1, 22)
        w = [rng.randint(0, 20) for _ in range(n)]
        assert merge_cost(w) == merge_cost_slow(w)


if __name__ == "__main__":
    main()
```

O(n²) time and space.

## 6. A min over lines: convex hull trick with a Li Chao tree

A frog on stones with heights `h[i]` goes from stone 0 to stone `n − 1`. From `j` it may jump to any later `i`, paying `(h[i] − h[j])² + C` (`C >= 0`). For `h = [1, 5, 2, 4]`, `C = 3`: `0 → 2 → 3` costs `1 + 3 + 4 + 3 = 11`, the best.

$$
dp[i] = \min_{j < i} \bigl(dp[j] + (h[i] - h[j])^2 + C\bigr), \qquad dp[0] = 0,
$$

O(n²). **Key observation.** Expand the square and group terms by who they depend on:

$$
dp[i] = h[i]^2 + C + \min_{j < i} \bigl(\underbrace{-2h[j]}_{m_j} \cdot h[i] + \underbrace{dp[j] + h[j]^2}_{b_j}\bigr).
$$

Each predecessor `j` is a **line** `y = m_j x + b_j`, and state `i` asks for the lowest line at `x = h[i]`. The condition: the mixed term is a product of a `j`-only number and an `i`-only number. A term like `min(h[i], h[j])` does not qualify. The minimum of lines is their **lower envelope**, which is convex, hence the name **convex hull trick**. With slopes and queries both sorted, a deque of lines gives O(n); in any order (as here: heights are not sorted), use a **Li Chao tree**.

**Li Chao tree.** A segment tree over the integer range `[x_lo, x_hi]`; each node keeps one line. To insert at a node: compare the new and stored lines at the midpoint and keep the lower; carry the other down. Two lines cross at most once, and the carried line lost at the midpoint, so it can only win on one side: go left if it is better at the left end, right if better at the right end, else stop. A query at `x` walks root to leaf and takes the minimum along the path. **Why that is enough:** for any `x`, the best line was either kept on `x`'s path, or carried away from it, which happens only after losing to the kept line on the half containing `x`. Both operations are O(log(x_hi − x_lo)).

**Trace.** Each finished `j` adds the line `(m, b) = (−2h[j], dp[j] + h[j]²)`.

| i | x = h[i] | lines present (m, b) | values at x | dp[i] = min + x² + C |
|---|---|---|---|---|
| 1 | 5 | (−2, 1) | −9 | −9 + 25 + 3 = 19 |
| 2 | 2 | (−2, 1), (−10, 44) | −3, 24 | −3 + 4 + 3 = 4 |
| 3 | 4 | (−2, 1), (−10, 44), (−4, 8) | −7, 4, −8 | −8 + 16 + 3 = 11 |

The best line at `x = 4` came from `j = 2`, the stone the frog jumped from.

```python
import random


class LiChaoTree:
    """Minimum of lines y = m*x + b over integer x in [x_lo, x_hi]."""

    def __init__(self, x_lo: int, x_hi: int):
        if x_lo > x_hi:
            raise ValueError("empty x range")
        self.x_lo, self.x_hi = x_lo, x_hi
        self.line: list[tuple[int, int] | None] = [None]
        self.left = [-1]
        self.right = [-1]

    @staticmethod
    def _at(line: tuple[int, int], x: int) -> int:
        return line[0] * x + line[1]

    def _child(self, node: int, go_left: bool) -> int:
        children = self.left if go_left else self.right
        if children[node] == -1:
            children[node] = len(self.line)
            self.line.append(None)
            self.left.append(-1)
            self.right.append(-1)
        return children[node]

    def insert(self, m: int, b: int) -> None:
        new = (m, b)
        node, lo, hi = 0, self.x_lo, self.x_hi
        while True:
            cur = self.line[node]
            if cur is None:
                self.line[node] = new
                return
            mid = (lo + hi) // 2
            if self._at(new, mid) < self._at(cur, mid):
                self.line[node], new = new, cur      # keep the winner at mid
                cur = self.line[node]
            if lo == hi:
                return
            if self._at(new, lo) < self._at(cur, lo):
                node, hi = self._child(node, True), mid
            elif self._at(new, hi) < self._at(cur, hi):
                node, lo = self._child(node, False), mid + 1
            else:
                return

    def query(self, x: int) -> int:
        if not self.x_lo <= x <= self.x_hi:
            raise ValueError("x outside the tree's range")
        node, lo, hi = 0, self.x_lo, self.x_hi
        best = None
        while node != -1:
            cur = self.line[node]
            if cur is not None:
                value = self._at(cur, x)
                best = value if best is None or value < best else best
            if lo == hi:
                break
            mid = (lo + hi) // 2
            if x <= mid:
                node, hi = self.left[node], mid
            else:
                node, lo = self.right[node], mid + 1
        if best is None:
            raise ValueError("no lines inserted")
        return best


def frog_cost_slow(h: list[int], c: int) -> int:
    if not h or c < 0:
        raise ValueError("need non-empty heights and c >= 0")
    dp = [0] * len(h)
    for i in range(1, len(h)):
        dp[i] = min(dp[j] + (h[i] - h[j]) ** 2 + c for j in range(i))
    return dp[-1]


def frog_cost(h: list[int], c: int) -> int:
    """O(n log X): each finished stone j becomes the line (-2h[j]) x + dp[j] + h[j]^2."""
    if not h or c < 0:
        raise ValueError("need non-empty heights and c >= 0")
    tree = LiChaoTree(min(h), max(h))
    dp = [0] * len(h)
    tree.insert(-2 * h[0], dp[0] + h[0] ** 2)
    for i in range(1, len(h)):
        x = h[i]
        dp[i] = tree.query(x) + x * x + c
        tree.insert(-2 * x, dp[i] + x * x)
    return dp[-1]


def main():
    assert frog_cost([1, 5, 2, 4], 3) == 11
    assert frog_cost([7], 10) == 0
    assert frog_cost([-4, 6], 0) == 100
    rng = random.Random(67)
    for _ in range(800):
        n = rng.randint(1, 30)
        h = [rng.randint(-20, 20) for _ in range(n)]
        c = rng.randint(0, 50)
        assert frog_cost(h, c) == frog_cost_slow(h, c)
    tree = LiChaoTree(-50, 50)                  # direct check against a brute-force envelope
    lines = []
    for _ in range(200):
        m, b = rng.randint(-30, 30), rng.randint(-500, 500)
        tree.insert(m, b)
        lines.append((m, b))
        x = rng.randint(-50, 50)
        assert tree.query(x) == min(mm * x + bb for mm, bb in lines)


if __name__ == "__main__":
    main()
```

O(n log X) time with `X = max(h) − min(h) + 1`; O(n) nodes, since an insertion creates at most one node per level it reaches. If `x` values are huge but known in advance, build the tree over the sorted query points instead.

## 7. A fixed linear recurrence for huge `n`: matrix exponentiation

Count the ways to climb `n` stairs with steps of 1, 2 or 3, modulo `1,000,000,007`, for `n` up to `10^18`. The DP `f(n) = f(n−1) + f(n−2) + f(n−3)` with `f(0) = f(1) = 1`, `f(2) = 2` gives `1, 1, 2, 4, 7, 13, 24, …`, but even O(n) is impossible.

**What differs.** The bottleneck is the number of states, not the inner operation. But every step is the same step. If the recurrence is **linear**, with **constant** coefficients, looking back a **fixed** `d` steps, then the last `d` values form a vector and one step multiplies it by a fixed `d × d` matrix:

$$
\begin{pmatrix} f(i+1) \\ f(i) \\ f(i-1) \end{pmatrix}
=
\begin{pmatrix} 1 & 1 & 1 \\ 1 & 0 & 0 \\ 0 & 1 & 0 \end{pmatrix}
\begin{pmatrix} f(i) \\ f(i-1) \\ f(i-2) \end{pmatrix}.
$$

`n − 2` steps from `i = 2` are one multiplication by `M^{n−2}`, computed by **repeated squaring** (`M, M², M⁴, …`, multiplying in the powers matching the exponent's 1-bits): O(log n) products of O(d³) each.

**Trace** for `f(6)`: start `(f(2), f(1), f(0)) = (2, 1, 1)`, exponent `4 = 100₂`, so only `M⁴` is needed. `M² = [[2, 2, 1], [1, 1, 1], [1, 0, 0]]`, `M⁴ = [[7, 6, 4], [4, 3, 2], [2, 2, 1]]`, and `M⁴ · (2, 1, 1) = (24, 13, 7)` = `(f(6), f(5), f(4))`.

```python
import random


MOD = 1_000_000_007


def mat_mul(x: list[list[int]], y: list[list[int]]) -> list[list[int]]:
    size, inner, cols = len(x), len(y), len(y[0])
    out = [[0] * cols for _ in range(size)]
    for i in range(size):
        row = x[i]
        for k in range(inner):
            if row[k]:
                factor = row[k]
                yk = y[k]
                out_i = out[i]
                for j in range(cols):
                    out_i[j] = (out_i[j] + factor * yk[j]) % MOD
    return out


def mat_pow(m: list[list[int]], power: int) -> list[list[int]]:
    d = len(m)
    result = [[int(i == j) for j in range(d)] for i in range(d)]
    while power:
        if power & 1:
            result = mat_mul(result, m)
        m = mat_mul(m, m)
        power >>= 1
    return result


def linear_recurrence(coeffs: list[int], initial: list[int], n: int) -> int:
    """f(n) mod MOD where f(i) = sum(coeffs[t] * f(i-1-t)) and f(0..d-1) = initial."""
    d = len(coeffs)
    if d == 0 or len(initial) != d or n < 0:
        raise ValueError("need d >= 1 coefficients, d initial values, and n >= 0")
    if n < d:
        return initial[n] % MOD
    m = [[c % MOD for c in coeffs]] + [[int(j == i) for j in range(d)] for i in range(d - 1)]
    vector = [[initial[d - 1 - i] % MOD] for i in range(d)]   # (f(d-1), ..., f(0))
    return mat_mul(mat_pow(m, n - (d - 1)), vector)[0][0]


def linear_recurrence_slow(coeffs: list[int], initial: list[int], n: int) -> int:
    values = [v % MOD for v in initial]
    while len(values) <= n:
        values.append(sum(c * values[-1 - t] for t, c in enumerate(coeffs)) % MOD)
    return values[n]


def main():
    stairs = ([1, 1, 1], [1, 1, 2])
    assert [linear_recurrence(*stairs, n) for n in range(7)] == [1, 1, 2, 4, 7, 13, 24]
    assert linear_recurrence([1, 1], [0, 1], 90) == 2880067194370816120 % MOD
    big = linear_recurrence(*stairs, 10**18)          # O(27 log n) work
    assert 0 <= big < MOD
    rng = random.Random(78)
    for _ in range(300):
        d = rng.randint(1, 4)
        coeffs = [rng.randint(-5, 5) for _ in range(d)]
        initial = [rng.randint(-10, 10) for _ in range(d)]
        n = rng.randint(0, 200)
        assert linear_recurrence(coeffs, initial, n) == linear_recurrence_slow(coeffs, initial, n)


if __name__ == "__main__":
    main()
```

O(d³ log n) time, O(d²) space; worth it only when `n` is far larger than `d³`.

**When it fails.** A coefficient that depends on `i` (`f(i) = i · f(i−1)`) changes the matrix every step. A `min` instead of a sum is not ordinary matrix multiplication, though the same squaring works in the min-plus algebra for fixed-length shortest paths.

## 8. Summary: reading the transition's shape

Every speed-up follows the same steps: write the slow recurrence and test it; read the shape of its inner `min`, `max` or `sum`; name the property a faster method needs; **prove** it for your recurrence; then compare fast against slow on random inputs with a fixed seed. Tests never replace the proof (§4.2).

| Transition shape | Technique | Condition to check | Complexity |
|---|---|---|---|
| `cost[i] + min/max dp[j]` over a sliding window | Monotonic deque | Candidates enter and expire in index order; values do not depend on `i` | O(n) |
| `Σ dp[j]` over `j ∈ [i − hi, i − lo]` | Prefix sums | Range ends known; operation invertible (sum, xor, sum mod p) | O(n) |
| `w[i] + max dp[j]` over `j < i`, `key[j] < key[i]` | Fenwick or segment tree + coordinate compression | Processing order handles one rule; the other becomes a prefix of ranks | O(n log n) |
| `min_k dp[g−1][k] + C(k, j)` | Divide-and-conquer optimization | `opt(j) ≤ opt(j+1)`, e.g. from the quadrangle inequality on `C` | O(t n log n) |
| `W(l, r) + min_k dp[l][k] + dp[k][r]` | Knuth optimization | `W` has the quadrangle inequality and is monotone on inclusion | O(n²) |
| `min_j dp[j] + A(j)·B(i) + D(j) + E(i)` | Convex hull trick / Li Chao tree | The mixed term is a product of a `j`-part and an `i`-part | O(n log X), or O(n) with sorted slopes and queries |
| `f(n) = Σ c_t f(n − 1 − t)`, fixed `d` | Matrix exponentiation | Linear, constant coefficients, fixed order | O(d³ log n) |

## 9. Pitfalls and practice

1. **Optimizing a wrong recurrence.** Every speed-up preserves the slow answer, mistakes included. Test the slow DP first.
2. **Confusing memory savings with time savings.** Rolling arrays cut space, not transitions.
3. **Prefix sums on `min` or `max`.** Not invertible; use a deque, sparse table or segment tree.
4. **Off-by-one window bounds.** Write the window as `[max(0, i − K), i − 1]` before coding the expiry test `window[0] < i − K`.
5. **Deque with `i`-dependent values.** If candidates can swap order as `i` grows, dominance fails.
6. **Strict versus non-strict Fenwick queries.** Strictly increasing queries `rank − 1`; non-decreasing queries `rank`.
7. **Assuming monotone `opt` because it looked monotone.** §4.2 shows the failure. Prove the inequality.
8. **Inconsistent tie-breaking.** The proofs talk about a specific best choice (the smallest); use strict `<` so the code picks it.
9. **Knuth on matrix chain.** Its join cost depends on the split point.
10. **Li Chao `x` range too small.** Every query point must lie in `[x_lo, x_hi]`.
11. **Overflow in other languages.** `m·x + b` and squared sums grow fast; Python is unbounded, C++ and Java are not.
12. **Matrix powers with varying coefficients.** No single matrix exists.

Practice: Frog Jump with K steps, Constrained Subsequence Sum, Jump Game VI, Count Ways to Build Good Strings, Maximum Sum Increasing Subsequence, Number of Longest Increasing Subsequence, Minimum Cost to Merge Stones, Optimal Binary Search Tree, Guardians of the Lunatics (divide-and-conquer DP), Frog 3 (convex hull trick), Kalila and Dimna, N-th Tribonacci Number, Domino and Tromino Tiling (for huge `n`).

Return to the [DP overview](README.md).
