# Monotonic Deque — The Best Candidate in a Moving Window

## 1. The problem: the maximum of every window

Report the maximum of every window of `k = 3` consecutive elements.

```text
index      0   1   2   3   4   5   6   7
reading    1   3  -1  -3   5   3   6   7

window [0..2]  1  3 -1        max 3
window [1..3]  3 -1 -3        max 3
window [2..4] -1 -3  5        max 5
window [3..5] -3  5  3        max 5
window [4..6]  5  3  6        max 6
window [5..7]  3  6  7        max 7
```

Answer: `[3, 3, 5, 5, 6, 7]`. A window `[l..r]` includes both ends.

**Brute force.** `max` of each window from scratch is `O(nk)`: about 2.5 billion steps for `n = 10⁵`, `k = 5 × 10⁴`.

**Why one variable is not enough.** A running maximum handles the reading that enters, not the one that leaves. Moving from `[1..3]` to `[2..4]` drops the `3`, and the maximum of what remains, `-1`, was never recorded.

A heap of the window's readings answers this in `O(log k)` per step ([Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md)). The method below takes `O(1)` amortized.

## 2. The key observation: newer and at least as large wins forever

Take two readings in the window, an older one at index `i` and a newer one at index `j > i`, with `nums[i] <= nums[j]`. Can `i` ever be the reported maximum again?

- Every future window that still contains `i` also contains `j`: windows slide right, and `j` is to the right of `i`, so `j` leaves **later**.
- In every such window, `nums[j] >= nums[i]`, so `j` is at least as good.

So `i` is useless from the moment `j` arrives. This is the **dominance** of [Monotonic Stack §4](02-monotonic-stack.md#4-variant-look-left-previous-greater-and-dominance): `j` is no worse in value and lasts longer. Delete `i` forever.

After deleting every dominated index, what is left? Reading the survivors from oldest to newest, each one must be **strictly larger** than every newer survivor (otherwise it would have been dominated). So:

> **Invariant.** The deque holds indices in increasing order (oldest at the front) whose values are strictly decreasing from front to back. Every index in it is inside the current window.

The front is then the largest value in the window. Each step does three things:

1. **Expire** from the front: drop the front index if it has slid out of the window.
2. **Dominate** from the back: drop back indices whose values are `<=` the new value.
3. **Append** the new index at the back, and read the answer at the front.

Front removals happen because of age, back removals because of value. A monotonic stack only has the second kind; with both ends changing, the container is a **deque** ([Stacks and Queues §4](01-stacks-and-queues.md#4-queues-and-deques)).

## 3. Worked trace

`k = 3`. At step `r`, the window is `[r − 2 .. r]`. The deque is written front to back as `index:value`.

| `r` | Value | Window | Expire from front | Pop from back (dominated) | Deque after | Output |
|---:|---:|---|---|---|---|---:|
| 0 | 1 | — | — | — | `0:1` | — |
| 1 | 3 | — | — | `0:1` | `1:3` | — |
| 2 | −1 | `[0..2]` | — | — | `1:3  2:−1` | 3 |
| 3 | −3 | `[1..3]` | — | — | `1:3  2:−1  3:−3` | 3 |
| 4 | 5 | `[2..4]` | `1:3` (index 1 < 2) | `3:−3`, `2:−1` | `4:5` | 5 |
| 5 | 3 | `[3..5]` | — | — | `4:5  5:3` | 5 |
| 6 | 6 | `[4..6]` | — | `5:3`, `4:5` | `6:6` | 6 |
| 7 | 7 | `[5..7]` | — | `6:6` | `7:7` | 7 |

Output `[3, 3, 5, 5, 6, 7]`. At step 4, both kinds of removal happen: the `3` at index 1 is too old, and the `−1` and `−3` are beaten by the `5`. The values in the deque always decrease from front to back.

At step 3, the deque holds `3, −1, −3`. The `−1` and `−3` are not useless: if the `3` expires before anything larger arrives, they become the maximum. That is exactly what the deque is for.

## 4. Code and tests

The function returns the **index** of each window's maximum, which `sliding_max` turns into values. The `earliest` flag picks which of several equal maxima is reported; §6 explains it.

```python
import random
from collections import deque


def sliding_max_index(nums: list[int], k: int, earliest: bool = False) -> list[int]:
    """Index of a maximum of every window nums[r-k+1 .. r]; requires 1 <= k <= len(nums)."""
    if not 1 <= k <= len(nums):
        raise ValueError("need 1 <= k <= len(nums)")
    dq: deque[int] = deque()          # indices; values decreasing front -> back
    out = []
    for r, x in enumerate(nums):
        left = r - k + 1              # first index of the window ending at r
        if dq and dq[0] < left:       # expire (at most one per step)
            dq.popleft()
        while dq and (nums[dq[-1]] < x if earliest else nums[dq[-1]] <= x):
            dq.pop()                  # dominated by r
        dq.append(r)
        if left >= 0:
            out.append(dq[0])
    return out


def sliding_max(nums: list[int], k: int) -> list[int]:
    return [nums[i] for i in sliding_max_index(nums, k)]


def main():
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    assert sliding_max(nums, 3) == [3, 3, 5, 5, 6, 7]
    neg = [-x for x in nums]          # window minimum = maximum of negated values (§6)
    assert [nums[i] for i in sliding_max_index(neg, 3)] == [-1, -3, -3, -3, 3, 3]
    assert sliding_max([4, 4, 4], 2) == [4, 4]
    assert sliding_max([-2], 1) == [-2]
    assert sliding_max([1, 2, 3], 1) == [1, 2, 3]
    assert sliding_max_index([5, 5, 1], 3, earliest=True) == [0]
    assert sliding_max_index([5, 5, 1], 3, earliest=False) == [1]
    for bad_k in (0, 4):
        try:
            sliding_max([1, 2, 3], bad_k)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = random.Random(30)
    for _ in range(3000):
        n = rng.randrange(1, 13)
        nums = [rng.randrange(-2, 3) for _ in range(n)]       # many ties
        k = rng.randrange(1, n + 1)
        windows = [nums[l:l + k] for l in range(n - k + 1)]
        assert sliding_max(nums, k) == [max(w) for w in windows]
        neg = [-x for x in nums]
        assert [nums[i] for i in sliding_max_index(neg, k)] == [min(w) for w in windows]
        first = [l + w.index(max(w)) for l, w in enumerate(windows)]
        last = [l + k - 1 - w[::-1].index(max(w)) for l, w in enumerate(windows)]
        assert sliding_max_index(nums, k, earliest=True) == first
        assert sliding_max_index(nums, k, earliest=False) == last


if __name__ == "__main__":
    main()
```

The expire step is an `if`: the window moves by one, so at most one index falls out per step.

## 5. Why it is linear, and why it is correct

**Linear.** Each index is appended once. It is removed at most once, either from the front (expired) or from the back (dominated), never both. So the total number of deque operations over the whole run is at most `2n`, and the time is `O(n)` no matter how many pops one step does. The deque holds at most `k` indices, so extra space is `O(k)`, plus `O(n − k + 1)` for the output.

**Correct.** Look at any window `[l..r]` and its maximum value, at some index `m`. Every index removed from the back was dominated by a newer index with at least its value, which is still in the window when the older one would have been. Following those dominations, some index still in the deque has value at least `nums[m]`, so the deque's maximum equals the window's maximum. Expiration removes exactly the indices `< l`. The values in the deque decrease from front to back, so the front is that maximum.

## 6. Minimum, ties, and why indices beat values

**Minimum.** Flip the dominance: a newer value `<=` an older one dominates it, so pop from the back while `nums[back] >= x`; the values then increase from front to back. Equivalently, take the maximum of the negated values, which is how the tests in §4 check it.

**Which equal value owns a tie?** If the window `[5, 5, 1]` has two maxima, which index does the front report? It depends on the back comparison:

| Pop from the back while | Equal older values | Front reports, among equal maxima |
|---|---|---|
| `nums[back] <= x` | removed by the newer equal | the **latest** index |
| `nums[back] < x` | kept, in front of the newer one | the **earliest** index |

Both give the same maximum **value**; the `earliest` flag in §4 switches between them. When the problem asks for an index ("return the position of the leftmost maximum"), the comparison decides the answer.

**Indices, not values.** With a deque of values for `[5, 5, 1]`, when the first `5` leaves the window, which `5` in the deque should go? Values alone cannot tell. Indices carry each candidate's lifetime, and the expiry test `dq[0] < left` is exact.

## 7. A variable window: longest stretch with max − min ≤ limit

**Problem.** Find the length of the longest subarray whose largest and smallest values differ by at most `limit`.

`nums = [10, 1, 2, 4, 7, 2]`, `limit = 5`: the answer is 4, from `[2, 4, 7, 2]` (max 7, min 2, difference 5).

**Brute force.** Try every start, extend to the right while tracking max and min, stop when the difference exceeds the limit: `O(n²)`.

**The key observation.** This is a variable-size sliding window ([Sliding Window](../05-sliding-window/README.md)). If `[l..r]` is too spread out, so is every longer window `[l..r']`, because adding values cannot shrink `max − min`. So when the window becomes invalid, `l` must move right, and it never has to move back. What is new is the validity test: it needs the window's max **and** min after every move of either end. Keep two deques: a decreasing one for the max, an increasing one for the min. When `l` moves past a front index, that index expires.

Trace, deques written front to back as `index:value`:

| `r` | Value | Max deque | Min deque | `max − min` | Move `l`? | Window | Best |
|---:|---:|---|---|---:|---|---|---:|
| 0 | 10 | `0:10` | `0:10` | 0 | — | `[0..0]` | 1 |
| 1 | 1 | `0:10  1:1` | `1:1` | 9 | `l = 1`, expire `0:10` from max | `[1..1]` | 1 |
| 2 | 2 | `2:2` | `1:1  2:2` | 1 | — | `[1..2]` | 2 |
| 3 | 4 | `3:4` | `1:1  2:2  3:4` | 3 | — | `[1..3]` | 3 |
| 4 | 7 | `4:7` | `1:1  2:2  3:4  4:7` | 6 | `l = 2`, expire `1:1` from min | `[2..4]` | 3 |
| 5 | 2 | `4:7  5:2` | `5:2` | 5 | — | `[2..5]` | 4 |

At `r = 1`, the deques show `max − min = 10 − 1 = 9` *before* moving `l`; after `l = 1` it is `0`. At `r = 5`, the new `2` pops `7`, `4`, and `2` from the min deque (each is `>= 2`), and the window `[2..5]` is valid.

```python
import random
from collections import deque


def longest_within_limit(nums: list[int], limit: int) -> int:
    """Longest subarray with max - min <= limit; 0 if none (empty input or limit < 0)."""
    if limit < 0:
        return 0
    max_dq: deque[int] = deque()      # values strictly decreasing
    min_dq: deque[int] = deque()      # values strictly increasing
    left = best = 0
    for right, x in enumerate(nums):
        while max_dq and nums[max_dq[-1]] <= x:
            max_dq.pop()
        max_dq.append(right)
        while min_dq and nums[min_dq[-1]] >= x:
            min_dq.pop()
        min_dq.append(right)
        while nums[max_dq[0]] - nums[min_dq[0]] > limit:
            left += 1
            if max_dq[0] < left:
                max_dq.popleft()
            if min_dq[0] < left:
                min_dq.popleft()
        best = max(best, right - left + 1)
    return best


def longest_within_limit_brute(nums: list[int], limit: int) -> int:
    best = 0
    for l in range(len(nums)):
        for r in range(l, len(nums)):
            if max(nums[l:r + 1]) - min(nums[l:r + 1]) <= limit:
                best = max(best, r - l + 1)
    return best


def main():
    assert longest_within_limit([10, 1, 2, 4, 7, 2], 5) == 4
    assert longest_within_limit([8, 2, 4, 7], 4) == 2
    assert longest_within_limit([4, 2, 2, 2, 4, 4, 2, 2], 0) == 3
    assert longest_within_limit([], 3) == 0
    assert longest_within_limit([1], -1) == 0
    rng = random.Random(32)
    for _ in range(3000):
        nums = [rng.randrange(-4, 5) for _ in range(rng.randrange(12))]
        limit = rng.randrange(-1, 6)
        assert longest_within_limit(nums, limit) == longest_within_limit_brute(nums, limit)


if __name__ == "__main__":
    main()
```

Why the fronts are safe to read: with `limit >= 0`, a one-element window is always valid, so the inner `while` stops by the time `left == right`, and both deques still hold `right`. Both pointers move right at most `n` times, and each index enters and leaves each deque at most once: `O(n)` time, `O(n)` deque space in the worst case.

## 8. A deque inside a dynamic program

The windows so far slid over the **input**. The same deque works when the window slides over values **computed earlier in the same scan**, as in a dynamic program (DP). [Faster Transitions](../09-dynamic-programming/12-faster-transitions.md) puts this next to other ways of speeding up a DP.

### Jump game VI

**Problem.** You start at index 0 of `nums` and must reach the last index. From index `i` you may jump forward 1 to `k` steps. Your score is the sum of `nums` over every index you land on, including the first and last. Maximize the score.

`nums = [1, −1, −2, 4, −7, 3]`, `k = 2`: the best path is `0 → 1 → 3 → 5`, scoring `1 − 1 + 4 + 3 = 7`.

**The slow DP.** Let `dp[i]` be the best score of a path that ends on index `i`. The last jump came from one of the `k` indices before `i`:

$$
dp[i]=nums[i]+\max_{\max(0,\,i-k)\le j<i}dp[j],\qquad dp[0]=nums[0].
$$

Taking the max over `k` values for each `i` costs `O(nk)`.

**The observation.** The candidates `j` form a window `[i − k .. i − 1]` that slides right as `i` grows, and each `dp[j]` is fixed once computed. That is exactly the sliding-window maximum, over `dp` instead of `nums`. An older `j` with `dp[j] <=` a newer `dp[j']` is dominated.

The order inside one step matters: expire, read the front to compute `dp[i]`, and only then pop dominated indices and append `i`.

| `i` | Window | Expire | Front used | `dp[i]` | Pop from back | Deque after (`index:dp`) |
|---:|---|---|---|---|---|---|
| 0 | — | — | — | 1 | — | `0:1` |
| 1 | `[0..0]` | — | `0:1` | −1 + 1 = 0 | — | `0:1  1:0` |
| 2 | `[0..1]` | — | `0:1` | −2 + 1 = −1 | — | `0:1  1:0  2:−1` |
| 3 | `[1..2]` | `0:1` | `1:0` | 4 + 0 = 4 | `2:−1`, `1:0` | `3:4` |
| 4 | `[2..3]` | — | `3:4` | −7 + 4 = −3 | — | `3:4  4:−3` |
| 5 | `[3..4]` | — | `3:4` | 3 + 4 = 7 | `4:−3`, `3:4` | `5:7` |

The answer is `dp[5] = 7`.

### Constrained subsequence sum

**Problem.** Choose a **nonempty** subsequence of `nums` such that any two consecutive chosen indices are at most `k` apart. Maximize its sum.

`nums = [10, 2, −10, 5, 20]`, `k = 2`: choose `10, 2, 5, 20` for 37 (indices 0, 1, 3, 4; the gaps are 1, 2, 1).

This is jump game VI with two changes. A subsequence may **start anywhere**, so a chain can begin fresh at `i` instead of extending a negative best: `dp[i] = nums[i] + max(0, best in window)`. And it may **end anywhere**, so the answer is `max(dp)`, not `dp[n − 1]`.

On the example the deque runs exactly as in jump game VI: `dp = [10, 12, 2, 17, 37]` and the answer is `max(dp) = 37`. Both changes show on `[5, −10, −10, 3]` with `k = 1`: `dp = [5, −5, −15, 3]`, where `dp[3] = 3 + max(0, −15)` starts fresh, and the answer `5` is `dp[0]`, not the last entry.

```python
import random
from collections import deque
from itertools import combinations


def jump_game_vi(nums: list[int], k: int) -> int:
    if not nums or k < 1:
        raise ValueError("need nonempty nums and k >= 1")
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dq: deque[int] = deque([0])           # dp values strictly decreasing
    for i in range(1, len(nums)):
        if dq[0] < i - k:
            dq.popleft()                  # expired
        dp[i] = nums[i] + dp[dq[0]]
        while dq and dp[dq[-1]] <= dp[i]:
            dq.pop()                      # dominated
        dq.append(i)
    return dp[-1]


def constrained_subsequence_sum(nums: list[int], k: int) -> int:
    if not nums or k < 1:
        raise ValueError("need nonempty nums and k >= 1")
    dp = [0] * len(nums)
    dq: deque[int] = deque()
    for i, x in enumerate(nums):
        if dq and dq[0] < i - k:
            dq.popleft()
        dp[i] = x + max(0, dp[dq[0]] if dq else 0)
        while dq and dp[dq[-1]] <= dp[i]:
            dq.pop()
        dq.append(i)
    return max(dp)


def gaps_ok(chosen: tuple[int, ...], k: int) -> bool:
    return all(b - a <= k for a, b in zip(chosen, chosen[1:]))


def jump_game_vi_brute(nums: list[int], k: int) -> int:
    n = len(nums)
    return max(sum(nums[i] for i in chosen)
               for size in range(1, n + 1)
               for chosen in combinations(range(n), size)
               if chosen[0] == 0 and chosen[-1] == n - 1 and gaps_ok(chosen, k))


def constrained_brute(nums: list[int], k: int) -> int:
    n = len(nums)
    return max(sum(nums[i] for i in chosen)
               for size in range(1, n + 1)
               for chosen in combinations(range(n), size)
               if gaps_ok(chosen, k))


def main():
    assert jump_game_vi([1, -1, -2, 4, -7, 3], 2) == 7
    assert jump_game_vi([10, -5, -2, 4, 0, 3], 3) == 17
    assert jump_game_vi([5], 1) == 5
    assert constrained_subsequence_sum([10, 2, -10, 5, 20], 2) == 37
    assert constrained_subsequence_sum([-1, -2, -3], 1) == -1
    assert constrained_subsequence_sum([5, -10, -10, 3], 1) == 5
    assert constrained_subsequence_sum([10, -2, -10, -5, 20], 2) == 23

    rng = random.Random(33)
    for _ in range(1500):
        n = rng.randrange(1, 9)
        nums = [rng.randrange(-6, 7) for _ in range(n)]
        k = rng.randrange(1, n + 1)
        assert jump_game_vi(nums, k) == jump_game_vi_brute(nums, k), (nums, k)
        assert constrained_subsequence_sum(nums, k) == constrained_brute(nums, k), (nums, k)


if __name__ == "__main__":
    main()
```

Each runs in `O(n)` time with `O(n)` for `dp` and `O(k)` for the deque, down from `O(nk)`. The method needs two things, and it is worth checking both before using it on a new DP: the candidate window **slides** (indices enter and leave in order), and a candidate's value **does not change** after it is computed.

## 9. A deque of prefix sums: shortest subarray with sum at least K

**Problem.** Given integers that may be **negative**, find the length of the shortest nonempty subarray whose sum is at least `K`, or `−1` if none exists.

`nums = [84, −37, 32, 40, 95]`, `K = 167`: the answer is 3, from `[32, 40, 95]` (sum 167).

### Why the usual sliding window fails

For nonnegative numbers, the shortest-window template of [Sliding Window](../05-sliding-window/README.md) works: extend right until the sum reaches `K`, then shrink from the left. It relies on "removing an element never increases the sum". With negatives, that is false. In `[1, −1, 5]` with `K = 5`, the window `[1, −1, 5]` sums to 5; dropping the `1` makes the sum 4, which looks like the wrong way to go, yet dropping the `−1` next gives `[5]`, the true answer of length 1.

### Move to prefix sums

Let `P[j]` be the sum of the first `j` elements (`P[0] = 0`), as in [Prefix Sums](../04-range-queries/01-prefix-sums.md). The subarray covering indices `i .. j − 1` has

$$
\text{sum}=P[j]-P[i],\qquad \text{length}=j-i,\qquad 0\le i<j\le n.
$$

So for each end `j`, we want the **latest** start `i < j` with `P[i] <= P[j] − K`. Checking every `i` is the `O(n²)` brute force.

### Two reasons a start can be thrown away

Keep a deque of candidate starts `i`, oldest at the front.

**Front: it has been used.** If `P[j] − P[front] >= K`, record the length `j − front`. Any later end `j' > j` paired with this same start gives a longer subarray, so this start can never improve the answer again. Pop it and test the next front.

**Back: a newer, lower prefix dominates it.** If a new prefix index `j` has `P[j] <= P[i]` for some older candidate `i`, then for every future end `t`:

$$
P[t]-P[j]\ \ge\ P[t]-P[i]\qquad\text{and}\qquad t-j<t-i.
$$

Starting at `j` gives at least as large a sum and a shorter subarray. Pop `i` from the back.

After both rules, the prefix values in the deque **strictly increase** from front to back. That is what makes the front test enough: if the front does not satisfy `P[j] − P[front] >= K`, no later candidate (with a larger `P`) does either.

### Worked trace

Prefix sums of `[84, −37, 32, 40, 95]`: `P = [0, 84, 47, 79, 119, 214]`.

| `j` | `P[j]` | Front: `P[j] − P[front] >= 167`? | Back: pop `P[back] >= P[j]` | Deque after (`index:P`) | Best |
|---:|---:|---|---|---|---:|
| 0, 1 | 0, 84 | 84 − 0 = 84, no | — | `0:0  1:84` | — |
| 2 | 47 | 47 − 0, no | `1:84` | `0:0  2:47` | — |
| 3, 4 | 79, 119 | no | — | `0:0  2:47  3:79  4:119` | — |
| 5 | 214 | 214 − 0 = 214: length 5, pop; 214 − 47 = 167: length 3, pop; 214 − 79 = 135, stop | — | `3:79  4:119  5:214` | 3 |

At `j = 2`, prefix index 2 dominates prefix index 1: for every future end, starting at prefix index 2 (input index 2) gives a subarray that is shorter and, because `47 < 84`, has a larger sum. At `j = 5`, two starts are used up in one step, and the second gives the answer 3: indices `2 .. 4`.

```python
import random
from collections import deque


def shortest_subarray_at_least(nums: list[int], K: int) -> int:
    """Shortest nonempty subarray with sum >= K (any signs); -1 if none."""
    prefix = [0]
    for x in nums:
        prefix.append(prefix[-1] + x)
    dq: deque[int] = deque()          # prefix indices; prefix values strictly increasing
    best = len(nums) + 1
    for j, pj in enumerate(prefix):
        while dq and pj - prefix[dq[0]] >= K:
            best = min(best, j - dq.popleft())       # used: cannot get shorter
        while dq and prefix[dq[-1]] >= pj:
            dq.pop()                                 # dominated by j
        dq.append(j)
    return best if best <= len(nums) else -1


def shortest_subarray_brute(nums: list[int], K: int) -> int:
    best = -1
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            if total >= K and (best == -1 or j - i + 1 < best):
                best = j - i + 1
    return best


def main():
    assert shortest_subarray_at_least([84, -37, 32, 40, 95], 167) == 3
    assert shortest_subarray_at_least([1, -1, 5], 5) == 1
    assert shortest_subarray_at_least([2, -1, 2], 3) == 3
    assert shortest_subarray_at_least([1, 2], 4) == -1
    assert shortest_subarray_at_least([], 0) == -1          # no nonempty subarray
    assert shortest_subarray_at_least([-1], 0) == -1
    assert shortest_subarray_at_least([0], 0) == 1
    assert shortest_subarray_at_least([-3, -2], -2) == 1
    rng = random.Random(34)
    for _ in range(4000):
        nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(10))]
        K = rng.randrange(-4, 12)
        assert shortest_subarray_at_least(nums, K) == shortest_subarray_brute(nums, K), (nums, K)


if __name__ == "__main__":
    main()
```

`O(n)` time: each prefix index enters once and leaves once. `O(n)` space for the prefix array and deque.

The front loop runs **before** the current index is appended. If it ran after, a start equal to the end (`i = j`, an empty subarray with sum 0) would be accepted whenever `K <= 0`. The tests `[-1]` with `K = 0` and `[-3, -2]` with `K = −2` catch exactly that.

## 10. Summary

Every deque in this chapter holds indices in increasing order and removes from both ends, for two different reasons:

| Problem | Entries | Values front → back | Front removal means | Back removal means |
|---|---|---|---|---|
| Window maximum (§4) | input indices | strictly decreasing | expired (left the window) | dominated by a newer `>=` value |
| Window minimum (§6) | input indices | strictly increasing | expired | dominated by a newer `<=` value |
| Longest with max − min ≤ limit (§7) | two deques, as above | one of each | `left` moved past it | dominated |
| DP over the last `k` states (§8) | DP indices | `dp` strictly decreasing | expired | dominated by a newer `>=` state |
| Shortest sum ≥ `K` (§9) | prefix indices | `P` strictly increasing | **used**: no shorter answer left | dominated by a newer `<=` prefix |

The step order is always: remove from the front, read the front, remove from the back, append. Only the DP reads the front **before** appending the current index, because the current index cannot be its own predecessor; the prefix-sum deque tests the front before appending so that an empty subarray is never counted. Before reusing a template, name what the entries are and why each removal is safe.

## 11. Pitfalls and practice

1. Reading the front before expiring old indices. Expire first, then read.
2. In a DP deque, appending `i` before reading the front for `dp[i]`. Then `i` would be its own predecessor.
3. Storing values instead of indices. Expiry needs the index; equal values need distinct identities.
4. Using `list.pop(0)` for the front. It is `O(n)` per call and can make the whole algorithm `O(n²)`; use `collections.deque`.
5. Picking `<` or `<=` in the back pop without deciding the tie rule. The maximum value is the same either way, but the reported **index** is not (§6).
6. Assuming a back pop means "expired". A back pop means **dominated**; only front pops mean expired (or, for prefix sums, used).
7. Using the sliding-window shrink rule for sums with negative numbers. Switch to prefix sums with a deque.
8. Forgetting the `max(0, …)` (fresh start) or the `max(dp)` (end anywhere) in constrained subsequence sum.

Practice: sliding window maximum; sliding window minimum and maximum together (sum of max − min over all windows of size `k`); longest continuous subarray with absolute difference at most limit; jump game VI; constrained subsequence sum; shortest subarray with sum at least K; max value of equation (`yᵢ + yⱼ + |xᵢ − xⱼ|` with a window on `x`); continuous subarrays (count windows with max − min ≤ 2); bounded knapsack with a sliding-window maximum per residue class.

Next: [Contributions and Boundaries](05-contributions-and-boundaries.md).
