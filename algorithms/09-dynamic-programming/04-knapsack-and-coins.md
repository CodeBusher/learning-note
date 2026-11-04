# Knapsack and Coins — Choosing Items Under a Budget

## 1. The knapsack problem

A bag holds at most 4 kilograms. Each item can be taken at most once:

| Item | Weight | Value |
|---|---|---|
| 0 | 1 | 15 |
| 1 | 3 | 20 |
| 2 | 4 | 30 |

The best is items 0 and 1: weight 4, value **35**. Grabbing the most valuable item (item 2, value 30) is worse, and greedy rules like "best value per kilogram first" fail on other inputs.

**Brute force.** Each item is in or out: `2^n` subsets, O(2^n · n) time, about 30 billion steps for 30 items. Yet the capacity is often small, say 1,000. Many subsets have the same total weight, and what can still be added depends only on that weight, not on which subset produced it. That repeated information is what DP removes.

The word "knapsack" covers a family, by how often each item may be used:

| Rule | Meaning | Example |
|---|---|---|
| 0/1 | Each item at most once | Packing distinct objects |
| Unbounded | Each item *type* any number of times | Coins of a currency |
| Bounded | Type `i` at most `limit[i]` times | A shop with limited stock |

Two equal items are still two items in the 0/1 problem; in coin problems a repeated denomination such as `[2, 2]` is the same coin type, so we remove duplicates. Each rule also comes in two versions: **exact** (weights add up to exactly the budget) and **at most** (anything up to the budget). They use different base cases and can give different answers.

## 2. The two-dimensional table

The [history test](03-states-and-reconstruction.md#1-what-must-a-state-remember) tells us what to remember. Two partial selections of the first `i` items that weigh the same have exactly the same futures: any set of later items fits after one exactly when it fits after the other. So the state is "how many items have I decided on, and how much weight have I used".

**State.** `dp[i][c]` = the maximum value using only the first `i` items (items `0` to `i-1`) with total weight **exactly** `c`.

**Transition.** Look at the last item among the first `i`, which is item `i-1`. There are two cases:

1. Skip it. The best value is whatever the first `i-1` items could do with weight `c`: `dp[i-1][c]`.
2. Take it. It adds `v[i-1]` and uses `w[i-1]`, so the earlier items must weigh exactly `c - w[i-1]`. This case exists only when `c >= w[i-1]`.

$$
dp[i][c] = \max\big(dp[i-1][c],\; dp[i-1][c - w_{i-1}] + v_{i-1}\big)
$$

**Base cases.** With zero items, the only possible weight is 0, with value 0. So `dp[0][0] = 0`, and `dp[0][c] = -inf` for every `c > 0`. Here `-inf` means "impossible", not "worth nothing". Using 0 instead would claim that 3 kilograms of nothing is a valid selection.

**Evaluation order.** Row `i` reads only row `i-1`. Fill rows from top to bottom; inside a row, any column order works.

**Answer.** For the exact version, `dp[n][W]`. For the at-most version, `max(dp[n][0..W])`.

**Trace.** Items `(w, v)` = `(1, 15)`, `(3, 20)`, `(4, 30)`; capacity 4. A dash means `-inf`.

| `i` (items allowed) | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---|---|---|---|---|
| 0 (none) | 0 | – | – | – | – |
| 1 (+ item 0: w1, v15) | 0 | 15 | – | – | – |
| 2 (+ item 1: w3, v20) | 0 | 15 | – | 20 | 35 |
| 3 (+ item 2: w4, v30) | 0 | 15 | – | 20 | 35 |

Some cells in detail:

- Row 2, `c=4`: skip gives `dp[1][4] = –`; take gives `dp[1][1] + 20 = 35`. Result 35.
- Row 3, `c=4`: skip gives `dp[2][4] = 35`; take gives `dp[2][0] + 30 = 30`. Result 35.
- Row 2, `c=2`: no subset of `{1, 3}` weighs exactly 2, so it stays `–`.

The exact answer is `dp[3][4] = 35`. The at-most answer is `max(0, 15, –, 20, 35) = 35`.

**Rebuilding the chosen items.** The table stores values, not choices, but we can recover the choices by walking backward. Start at `(n, W)`. If `dp[i][c] == dp[i-1][c]`, skipping item `i-1` explains the value, so skip it. Otherwise the take branch must have produced it: record item `i-1` and move to `c - w[i-1]`. In the trace: at `(3, 4)`, 35 equals the row above, so skip item 2. At `(2, 4)`, 35 differs from `–`, so take item 1 and move to `c = 1`. At `(1, 1)`, take item 0. The items are `[0, 1]`.

```python
import random
from itertools import product
from math import inf


def knapsack_01_exact(
    weights: list[int], values: list[int], capacity: int
) -> tuple[int, list[int]] | None:
    """Best value and chosen indices with total weight exactly capacity, or None."""
    if len(weights) != len(values) or capacity < 0 or any(w <= 0 for w in weights):
        raise ValueError("use matching arrays, positive weights, and capacity >= 0")
    n = len(weights)
    dp = [[-inf] * (capacity + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        weight, value = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]  # Skip item i-1.
            if c >= weight and dp[i - 1][c - weight] != -inf:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - weight] + value)

    if dp[n][capacity] == -inf:
        return None
    chosen = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:  # Skipping cannot explain the value.
            chosen.append(i - 1)
            c -= weights[i - 1]
    chosen.reverse()
    return dp[n][capacity], chosen


def knapsack_01_at_most(weights: list[int], values: list[int], capacity: int) -> int:
    """At most capacity: the best exact weight from 0 to capacity, or the empty set."""
    return max(
        [0] + [r[0] for c in range(capacity + 1) if (r := knapsack_01_exact(weights, values, c))]
    )


def brute_exact(weights, values, capacity):
    best = None
    for picks in product((0, 1), repeat=len(weights)):
        if sum(w for w, p in zip(weights, picks) if p) == capacity:
            value = sum(v for v, p in zip(values, picks) if p)
            best = value if best is None else max(best, value)
    return best


def main():
    weights, values = [1, 3, 4], [15, 20, 30]
    assert knapsack_01_exact(weights, values, 4) == (35, [0, 1])
    assert knapsack_01_exact(weights, values, 2) is None
    assert knapsack_01_at_most(weights, values, 2) == 15
    assert knapsack_01_exact([], [], 0) == (0, [])
    assert knapsack_01_exact([], [], 1) is None
    assert knapsack_01_exact([1], [-5], 1) == (-5, [0])  # Exact forces the item.
    assert knapsack_01_at_most([1], [-5], 1) == 0  # At most may leave it out.

    rng = random.Random(4)
    for _ in range(300):
        n = rng.randint(0, 7)
        ws = [rng.randint(1, 6) for _ in range(n)]
        vs = [rng.randint(-3, 10) for _ in range(n)]
        cap = rng.randint(0, 15)
        got = knapsack_01_exact(ws, vs, cap)
        expected = brute_exact(ws, vs, cap)
        if expected is None:
            assert got is None
        else:
            best, chosen = got
            assert best == expected
            assert sum(ws[i] for i in chosen) == cap
            assert sum(vs[i] for i in chosen) == best


if __name__ == "__main__":
    main()
```

**Complexity.** There are `(n+1)(W+1)` cells, each filled in O(1), so time and space are O(nW). Reconstruction takes O(n).

This is called **pseudo-polynomial** time. It is polynomial in the *value* of `W`, but `W` takes only about `log W` bits to write down. With `W = 10^12` the table is far too large. §9 shows what to do then.

**Why it is correct.** Every selection of the first `i` items either includes item `i-1` or not, so the two cases cover everything. If it includes item `i-1`, removing that item leaves a selection of the first `i-1` items with weight exactly `c - w[i-1]`. The best such selection is `dp[i-1][c - w[i-1]]` by induction. The same holds for the skip case.

**At most versus exact, done directly.** You can also define `dp[i][c]` as the best value with weight *at most* `c`. Then row 0 is all zeros, because the empty selection fits in any budget. The recurrence is the same. The one mistake to avoid is mixing the two: an exact-weight definition with an all-zero row 0 silently becomes the at-most problem.

## 3. Shrinking the table to one row

Row `i` reads only row `i-1`. So we can keep one array `dp` of length `W+1` and overwrite it as we go. This saves memory: O(W) instead of O(nW). But there is a trap.

**The ascending loop bug.** Use the at-most version (start with all zeros), a capacity of 4, and only item 0 (weight 1, value 15). Update `dp[c] = max(dp[c], dp[c-1] + 15)` with `c` going **up**:

| Step | Reads | `dp` after the step |
|---|---|---|
| start | | `[0, 0, 0, 0, 0]` |
| c=1 | `dp[0] = 0` (old) | `[0, 15, 0, 0, 0]` |
| c=2 | `dp[1] = 15` (**already updated**) | `[0, 15, 30, 0, 0]` |
| c=3 | `dp[2] = 30` (updated) | `[0, 15, 30, 45, 0]` |
| c=4 | `dp[3] = 45` (updated) | `[0, 15, 30, 45, 60]` |

The final value 60 means "take item 0 four times". But there is only one item 0. At step `c=2`, the formula wanted `dp[i-1][1]` (the old row, value 0), but the array already held the new row's value `dp[i][1] = 15`. The loop silently changed the problem into unbounded knapsack.

**The fix: go down.** Run `c` from 4 down to 1. Now `c=4` reads `dp[3] = 0`, `c=3` reads `dp[2] = 0`, and so on: every read is still the old row, and the row ends as `[0, 15, 15, 15, 15]`. Each read looks at a smaller index, and smaller indices have not been touched yet in this pass. So every read sees the previous row. That is the invariant: **when we update `dp[c]`, every `dp[c']` with `c' < c` still holds row `i-1`.**

```python
import random
from itertools import product


def knapsack_01_one_row(weights: list[int], values: list[int], capacity: int) -> int:
    if len(weights) != len(values) or capacity < 0 or any(w <= 0 for w in weights):
        raise ValueError("invalid items or capacity")
    dp = [0] * (capacity + 1)  # At most: the empty selection fits everywhere.
    for weight, value in zip(weights, values):
        for c in range(capacity, weight - 1, -1):  # Descending.
            dp[c] = max(dp[c], dp[c - weight] + value)
    return dp[capacity]


def unbounded_knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    """The ascending loop: wrong for 0/1, right when every item type is reusable (§6)."""
    if len(weights) != len(values) or capacity < 0 or any(w <= 0 for w in weights):
        raise ValueError("invalid items or capacity")
    dp = [0] * (capacity + 1)
    for weight, value in zip(weights, values):
        for c in range(weight, capacity + 1):  # Ascending: reuses items.
            dp[c] = max(dp[c], dp[c - weight] + value)
    return dp[capacity]


def brute(weights, values, capacity, copies=1):
    """Try every count 0..copies of every item."""
    best = 0
    for picks in product(range(copies + 1), repeat=len(weights)):
        if sum(w * p for w, p in zip(weights, picks)) <= capacity:
            best = max(best, sum(v * p for v, p in zip(values, picks)))
    return best


def main():
    assert knapsack_01_one_row([1, 3, 4], [15, 20, 30], 4) == 35
    assert unbounded_knapsack([1, 3, 4], [15, 20, 30], 4) == 60
    assert knapsack_01_one_row([1], [15], 4) == 15
    assert unbounded_knapsack([1], [15], 4) == 60  # The buggy trace above.
    assert knapsack_01_one_row([1], [-5], 1) == 0
    assert knapsack_01_one_row([], [], 8) == 0

    rng = random.Random(7)
    for _ in range(300):
        n = rng.randint(0, 8)
        ws = [rng.randint(1, 6) for _ in range(n)]
        vs = [rng.randint(-2, 10) for _ in range(n)]
        cap = rng.randint(0, 20)
        assert knapsack_01_one_row(ws, vs, cap) == brute(ws, vs, cap)
        if n <= 3 and cap <= 8:  # Up to cap copies of each item is enough.
            assert unbounded_knapsack(ws, vs, cap) == brute(ws, vs, cap, copies=cap)


if __name__ == "__main__":
    main()
```

Time stays O(nW); space drops to O(W).

**Reconstruction needs the full table.** A single row forgets which items produced each value. Storing one "parent" per cell of the row is also unsafe, because a later item overwrites cells that earlier parents point to. If you need the chosen items, keep the 2D table (or at least one bit per `(i, c)` saying "taken").

## 4. Subset sum and equal partition

Given positive integers, can some of them add up to exactly `target`? For `[3, 34, 4, 12, 5, 2]` and target 9, yes: `4 + 5`. For target 30, no.

This is 0/1 knapsack where we only care about weight, so values disappear and `max` becomes `or`. This is the feasibility flavor from [Designing a Recurrence](02-designing-a-recurrence.md).

**State.** `can[c]` = whether some subset of the items seen so far sums to exactly `c`.

**Transition.** For item `x`: `can[c]` becomes true if it was already true (skip `x`) or if `can[c - x]` was true before this item (take `x`).

$$
can_i[c] = can_{i-1}[c] \;\lor\; can_{i-1}[c - x_{i-1}]
$$

**Base case.** `can[0] = True` (the empty subset), everything else `False`. Loop `c` downward for the same reason as §3.

**Equal partition.** Can the list be split into two groups with equal sums? If the total is odd, no. Otherwise we need one group summing to `total // 2`; the rest automatically sums to the other half. For `[1, 5, 11, 5]`, the total is 22 and `{11}` versus `{1, 5, 5}` works. For `[1, 2, 3, 5]`, the total is 11, which is odd, so no.

**A bitset speedup.** A Python integer can serve as a row of bits: bit `c` is 1 when sum `c` is reachable. Taking item `x` shifts every reachable sum up by `x`, which is `bits << x`. So one item updates the whole row with `bits |= bits << x`. The shift reads the old value of `bits`, so no item is reused. This is still O(nW) bit operations, but the machine does many bits per word, so it runs much faster in practice.

```python
import random
from itertools import combinations


def subset_sum(nums: list[int], target: int) -> bool:
    if target < 0 or any(x <= 0 for x in nums):
        raise ValueError("positive numbers and target >= 0 are required")
    can = [False] * (target + 1)
    can[0] = True
    for x in nums:
        for c in range(target, x - 1, -1):
            if can[c - x]:
                can[c] = True
    return can[target]


def subset_sum_bits(nums: list[int], target: int) -> bool:
    if target < 0 or any(x <= 0 for x in nums):
        raise ValueError("positive numbers and target >= 0 are required")
    mask = (1 << (target + 1)) - 1  # Drop sums above target.
    bits = 1  # Only sum 0 is reachable.
    for x in nums:
        bits = (bits | (bits << x)) & mask
    return (bits >> target) & 1 == 1


def can_partition(nums: list[int]) -> bool:
    total = sum(nums)
    return total % 2 == 0 and subset_sum(nums, total // 2)


def brute(nums, target):
    return any(
        sum(combo) == target
        for k in range(len(nums) + 1)
        for combo in combinations(nums, k)
    )


def main():
    assert subset_sum([3, 34, 4, 12, 5, 2], 9)
    assert not subset_sum([3, 34, 4, 12, 5, 2], 30)
    assert subset_sum([], 0) and not subset_sum([], 1)
    assert can_partition([1, 5, 11, 5])
    assert not can_partition([1, 2, 3, 5])
    assert not subset_sum([2], 4)  # One 2, not two.

    rng = random.Random(11)
    for _ in range(300):
        nums = [rng.randint(1, 9) for _ in range(rng.randint(0, 8))]
        target = rng.randint(0, 30)
        expected = brute(nums, target)
        assert subset_sum(nums, target) == expected
        assert subset_sum_bits(nums, target) == expected


if __name__ == "__main__":
    main()
```

Time O(nT), space O(T).

## 5. Target sum: signs become a subset

Put a `+` or `-` in front of every number so the total equals `target`. Count the ways. For `[1, 1, 1, 1, 1]` and target 3, there are **5** ways: choose which single `1` gets the minus sign.

**Brute force.** Each number has 2 signs, so there are `2^n` sign patterns. Try them all.

**The reduction.** Let `P` be the sum of numbers with `+`, and `N` the sum of numbers with `-`. Then:

$$
P - N = target, \qquad P + N = total.
$$

Adding the two equations gives `2P = total + target`, so

$$
P = \frac{total + target}{2}.
$$

So a sign pattern is the same thing as a choice of the "plus" subset, and we need that subset to sum to `P`. If `total + target` is odd or negative, or `|target| > total`, there are zero ways. For the example, `P = (5 + 3) / 2 = 4`: pick four of the five 1s to be positive, which is `C(5, 4) = 5` ways.

**State.** `ways[c]` = the number of subsets of the items so far whose sum is exactly `c`.

**Transition.** Each subset either skips or takes the current item, and these are different subsets, so we add:

$$
ways_i[c] = ways_{i-1}[c] + ways_{i-1}[c - x_{i-1}]
$$

**Base case.** `ways[0] = 1`: the empty subset is one way to make 0. The empty construction counts once, as in [What DP Is](01-what-is-dp.md).

Zeros need care. A `0` can be `+0` or `-0`, which are two different sign patterns with the same sum. The counting recurrence handles this on its own: with `x = 0`, the update `ways[c] += ways[c - 0]` doubles every count, and each cell is read and written exactly once in the pass. The brute force below checks this case.

```python
import random
from itertools import product


def count_subsets_with_sum(nums: list[int], target: int) -> int:
    if target < 0 or any(x < 0 for x in nums):
        raise ValueError("nonnegative numbers and target >= 0 are required")
    ways = [0] * (target + 1)
    ways[0] = 1
    for x in nums:
        for c in range(target, x - 1, -1):
            ways[c] += ways[c - x]
    return ways[target]


def target_sum_ways(nums: list[int], target: int) -> int:
    if any(x < 0 for x in nums):
        raise ValueError("numbers must be nonnegative")
    total = sum(nums)
    if abs(target) > total or (total + target) % 2 != 0:
        return 0
    return count_subsets_with_sum(nums, (total + target) // 2)


def brute(nums, target):
    return sum(
        1
        for signs in product((1, -1), repeat=len(nums))
        if sum(s * x for s, x in zip(signs, nums)) == target
    )


def main():
    assert target_sum_ways([1, 1, 1, 1, 1], 3) == 5
    assert target_sum_ways([1], 2) == 0
    assert target_sum_ways([0, 0, 1], 1) == 4  # Each zero doubles the count.
    assert target_sum_ways([], 0) == 1
    assert target_sum_ways([2, 3], -1) == 1  # +2 - 3.

    rng = random.Random(5)
    for _ in range(300):
        nums = [rng.randint(0, 5) for _ in range(rng.randint(0, 9))]
        target = rng.randint(-12, 12)
        assert target_sum_ways(nums, target) == brute(nums, target)


if __name__ == "__main__":
    main()
```

Time O(n · P), space O(P). The lesson: when a problem gives each item two roles, write down what the two roles sum to, and see if one role alone determines the answer.

## 6. Unbounded knapsack and the minimum number of coins

Now each item type can be used any number of times. Let `dp[i][c]` be the best value using the first `i` types with weight at most `c`. The last decision is still about type `i-1`, but taking one copy does **not** remove the type. So the take branch stays in row `i`:

$$
dp[i][c] = \max\big(dp[i-1][c],\; dp[i][c - w_{i-1}] + v_{i-1}\big)
$$

Compare with 0/1, which read `dp[i-1][c - w]`. Because the take branch reads the **current** row at a smaller capacity, the one-row loop must go **up**. The "bug" in §3 is exactly the right algorithm here; `unbounded_knapsack` there is tested against a brute force. Positive weights guarantee `c - w < c`, so the dependency never loops back on itself.

**Minimum coins.** Given coin values and a target amount, use the fewest coins that sum exactly to the target, with unlimited coins of each value. Example: coins `[1, 3, 4]`, target 6.

- Greedy (largest coin first): `4 + 1 + 1`, three coins.
- Best: `3 + 3`, **two** coins.

Greedy works for some coin systems (like 1, 5, 10, 25) but not in general, so we use DP.

**State.** `best[t]` = the fewest coins summing to exactly `t`, or `inf` if impossible.

**Transition.** Look at the last coin placed. If it is `coin`, the rest sums to `t - coin` and should use as few coins as possible:

$$
best[t] = 1 + \min_{coin \le t} best[t - coin]
$$

**Base case.** `best[0] = 0`. All other entries start at `inf`, because "unreachable" must lose every `min`.

**Order.** `best[t]` reads only smaller totals, so fill `t = 1, 2, ..., T`.

**Trace** for coins `[1, 3, 4]`:

| t | from coin 1 | from coin 3 | from coin 4 | `best[t]` | last coin |
|---|---|---|---|---|---|
| 0 | | | | 0 | |
| 1 | best[0]+1 = 1 | | | 1 | 1 |
| 2 | best[1]+1 = 2 | | | 2 | 1 |
| 3 | best[2]+1 = 3 | best[0]+1 = 1 | | 1 | 3 |
| 4 | best[3]+1 = 2 | best[1]+1 = 2 | best[0]+1 = 1 | 1 | 4 |
| 5 | best[4]+1 = 2 | best[2]+1 = 3 | best[1]+1 = 2 | 2 | 1 |
| 6 | best[5]+1 = 3 | best[3]+1 = 2 | best[2]+1 = 3 | 2 | 3 |

To rebuild the coins, follow `last`: at 6 take a 3, at 3 take a 3, done. Answer `[3, 3]`.

```python
import random
from math import inf


def minimum_coins(coins: list[int], target: int) -> list[int] | None:
    if target < 0 or any(coin <= 0 for coin in coins):
        raise ValueError("positive coins and target >= 0 are required")
    coins = sorted(set(coins))
    best = [inf] * (target + 1)
    last = [0] * (target + 1)
    best[0] = 0
    for t in range(1, target + 1):
        for coin in coins:
            if coin > t:
                break
            if best[t - coin] + 1 < best[t]:
                best[t] = best[t - coin] + 1
                last[t] = coin
    if best[target] == inf:
        return None
    answer = []
    while target > 0:
        answer.append(last[target])
        target -= last[target]
    return answer


def greedy_coins(coins: list[int], target: int) -> list[int] | None:
    answer = []
    for coin in sorted(set(coins), reverse=True):
        while target >= coin:
            answer.append(coin)
            target -= coin
    return answer if target == 0 else None


def brute_min_coins(coins, target):
    """Breadth-first over 'add one coin' finds the fewest coins."""
    frontier, seen, steps = {0}, {0}, 0
    while frontier:
        if target in frontier:
            return steps
        frontier = {s + c for s in frontier for c in coins if s + c <= target} - seen
        seen |= frontier
        steps += 1
    return None


def main():
    assert minimum_coins([1, 3, 4], 6) == [3, 3]
    assert greedy_coins([1, 3, 4], 6) == [4, 1, 1]  # Greedy uses one more coin.
    assert minimum_coins([2], 3) is None
    assert minimum_coins([], 0) == []
    assert minimum_coins([2, 2], 4) == [2, 2]

    rng = random.Random(3)
    for _ in range(300):
        coins = [rng.randint(1, 9) for _ in range(rng.randint(0, 4))]
        target = rng.randint(0, 30)
        answer = minimum_coins(coins, target)
        expected = brute_min_coins(coins, target)
        if expected is None:
            assert answer is None
        else:
            assert len(answer) == expected and sum(answer) == target
            assert all(c in coins for c in answer)


if __name__ == "__main__":
    main()
```

With `m` distinct coins and target `T`, time is O(mT) and space O(T). A coin of value 0 or a negative value breaks the "smaller total" argument, and the dependency order is no longer guaranteed; such inputs need a different model.

## 7. Counting coin ways: combinations versus sequences

With coins `{1, 2}` and target 3:

- **Combinations** (order does not matter): `{1,1,1}` and `{1,2}`. Answer **2**.
- **Sequences** (order matters): `(1,1,1)`, `(1,2)`, `(2,1)`. Answer **3**.

The two DPs use the same line of code, `ways[t] += ways[t - coin]`. Only the loop nesting differs. Getting it backwards is one of the most common DP bugs.

**Combinations: coins outside, totals inside.** A combination is fully described by how many of each coin type it uses. So decide the coin types one at a time. Let `ways[i][t]` be the number of combinations of the first `i` types summing to `t`. The last decision is "use type `i-1` zero times, or at least once". Using it at least once leaves `t - coin`, still allowing type `i-1`:

$$
ways[i][t] = ways[i-1][t] + ways[i][t - c_{i-1}]
$$

In one row, this is: outer loop over coins, inner loop over totals going up. Each combination is built in only one order (all 1s first, then all 2s), so it is counted once.

**Sequences: totals outside, coins inside.** For sequences, use the "last decision" literally: the last coin of the sequence. Every sequence summing to `t` is a sequence summing to `t - coin` followed by `coin`, for exactly one `coin`:

$$
seq[t] = \sum_{coin \le t} seq[t - coin]
$$

In code: outer loop over totals, inner loop over coins.

**Trace** for coins `{1, 2}`, combinations (coins outside):

| after processing | t=0 | t=1 | t=2 | t=3 |
|---|---|---|---|---|
| start | 1 | 0 | 0 | 0 |
| coin 1 | 1 | 1 | 1 | 1 |
| coin 2 | 1 | 1 | 2 | 2 |

Sequences (totals outside): `seq[0]=1`, `seq[1]=seq[0]=1`, `seq[2]=seq[1]+seq[0]=2`, `seq[3]=seq[2]+seq[1]=3`.

```python
import random
from itertools import product


def count_coin_ways(coins: list[int], target: int, ordered: bool = False) -> int:
    if target < 0 or any(coin <= 0 for coin in coins):
        raise ValueError("positive coins and target >= 0 are required")
    coins = sorted(set(coins))
    ways = [0] * (target + 1)
    ways[0] = 1
    if ordered:
        for t in range(1, target + 1):
            for coin in coins:
                if coin <= t:
                    ways[t] += ways[t - coin]
    else:
        for coin in coins:
            for t in range(coin, target + 1):
                ways[t] += ways[t - coin]
    return ways[target]


def brute_combinations(coins, target):
    coins = sorted(set(coins))
    ranges = [range(target // c + 1) for c in coins]
    return sum(
        1
        for counts in product(*ranges)
        if sum(k * c for k, c in zip(counts, coins)) == target
    )


def brute_sequences(coins, target):
    if target == 0:
        return 1
    return sum(brute_sequences(coins, target - c) for c in set(coins) if c <= target)


def main():
    assert count_coin_ways([1, 2], 3) == 2
    assert count_coin_ways([1, 2], 3, ordered=True) == 3
    assert count_coin_ways([1, 1, 2], 3) == 2  # Duplicate types removed.
    assert count_coin_ways([], 0) == 1  # The empty construction.
    assert count_coin_ways([], 4) == 0
    assert count_coin_ways([2, 4], 3) == 0

    rng = random.Random(9)
    for _ in range(200):
        coins = [rng.randint(1, 6) for _ in range(rng.randint(0, 4))]
        target = rng.randint(0, 14)
        assert count_coin_ways(coins, target) == brute_combinations(coins, target)
        assert count_coin_ways(coins, target, True) == brute_sequences(coins, target)


if __name__ == "__main__":
    main()
```

Both take O(mT) time and O(T) space. Counts grow fast; problems often ask for the answer modulo some `M`. Then reduce after each addition. A count of 0 modulo `M` does not prove the target is impossible, so track feasibility separately if you need it.

**Link to generating functions.** Unordered coin counting is the coefficient of `x^T` in the product of `(1 + x^c + x^{2c} + ...)` over coin types `c`. There is one factor per type, which is why processing one type at a time avoids counting orderings. See [Counting and Distributions](../12-math-and-geometry/04-counting-distributions/README.md) for that viewpoint.

## 8. Bounded knapsack

Now type `i` has weight `w[i]`, value `v[i]`, and at most `limit[i]` copies.

Decide how many copies `k` of the last type to take:

$$
dp[i][c] = \max_{0 \le k \le \min(limit_{i-1},\, c / w_{i-1})} \big(dp[i-1][c - k\,w_{i-1}] + k\,v_{i-1}\big)
$$

This is correct but slow: each cell may try up to `limit` values of `k`, giving O(W · sum of limits).

**Binary grouping for maximum value.** Replace "type with limit 13" by a few 0/1 items that can express any count from 0 to 13. Use groups of sizes 1, 2, 4, and then the remainder 6. Every count 0..13 is a sum of some of these groups: for example, 11 = 1 + 4 + 6, and 13 = 1 + 2 + 4 + 6. A group of size `s` becomes one 0/1 item with weight `s·w` and value `s·v`. Now `limit` copies cost only about `log2(limit)` items.

Why can every count be formed? The groups 1, 2, 4, ..., 2^(k-1) make every count from 0 to 2^k - 1 (binary numbers). The remainder `r` is at most 2^k, so adding it covers `r` to `r + 2^k - 1`, which reaches the limit with no gap.

**Why grouping breaks counting.** For maximum value, it does not matter if the same count can be formed two ways: the `max` is the same. For **counting**, it matters a lot. With limit 5, the groups are 1, 2, 2. A count of 2 can be formed as "the first 2-group" or "the second 2-group", so it would be counted twice. The original problem has only one way to take 2 copies. Never use binary grouping for counting.

```python
import random
from itertools import product


def bounded_knapsack_max(
    weights: list[int], values: list[int], limits: list[int], capacity: int
) -> int:
    if not (len(weights) == len(values) == len(limits)):
        raise ValueError("item arrays must have equal length")
    if capacity < 0 or any(w <= 0 for w in weights) or any(k < 0 for k in limits):
        raise ValueError("invalid capacity, weight, or limit")
    dp = [0] * (capacity + 1)
    for weight, value, limit in zip(weights, values, limits):
        remaining = min(limit, capacity // weight)
        size = 1
        while remaining > 0:
            copies = min(size, remaining)
            gw, gv = copies * weight, copies * value
            for c in range(capacity, gw - 1, -1):  # Each group is a 0/1 item.
                dp[c] = max(dp[c], dp[c - gw] + gv)
            remaining -= copies
            size *= 2
    return dp[capacity]


def groups(limit: int) -> list[int]:
    result, size = [], 1
    while limit > 0:
        result.append(min(size, limit))
        limit -= result[-1]
        size *= 2
    return result


def grouped_count_wrong(weight: int, limit: int, target: int) -> int:
    """Counts group subsets, which overcounts copy counts."""
    ways = [0] * (target + 1)
    ways[0] = 1
    for g in groups(limit):
        for c in range(target, g * weight - 1, -1):
            ways[c] += ways[c - g * weight]
    return ways[target]


def brute_max(weights, values, limits, capacity):
    best = 0
    for counts in product(*(range(k + 1) for k in limits)):
        if sum(k * w for k, w in zip(counts, weights)) <= capacity:
            best = max(best, sum(k * v for k, v in zip(counts, values)))
    return best


def main():
    assert groups(13) == [1, 2, 4, 6]
    assert groups(5) == [1, 2, 2]
    assert bounded_knapsack_max([2], [3], [3], 8) == 9
    assert bounded_knapsack_max([2, 3], [3, 5], [2, 1], 7) == 11
    assert bounded_knapsack_max([1], [2], [13], 12) == 24
    assert bounded_knapsack_max([1], [-2], [10], 10) == 0
    assert bounded_knapsack_max([], [], [], 0) == 0
    assert grouped_count_wrong(1, 5, 2) == 2  # But there is only 1 way.

    rng = random.Random(13)
    for _ in range(300):
        n = rng.randint(0, 3)
        ws = [rng.randint(1, 5) for _ in range(n)]
        vs = [rng.randint(-2, 9) for _ in range(n)]
        ls = [rng.randint(0, 6) for _ in range(n)]
        cap = rng.randint(0, 20)
        assert bounded_knapsack_max(ws, vs, ls, cap) == brute_max(ws, vs, ls, cap)


if __name__ == "__main__":
    main()
```

Let `L_i = min(limit[i], W // w[i])`. Each type becomes O(log(L_i + 1)) groups, so time is O(W · sum of log(L_i + 1)) and space O(W).

**Bounded counting with a sliding sum.** How many ways can we pick copy counts `k_i` with `0 <= k_i <= limit[i]` and `sum k_i · w[i] = T`? Here we need the direct recurrence, but we can make it fast. For one type with weight `w` and limit `L`:

$$
new[c] = \sum_{k=0}^{L} old[c - k\,w]
$$

Look at which cells this sum touches: `c, c - w, c - 2w, ...`. All of them have the same remainder `c mod w`. So split the capacities into `w` chains by remainder. For remainder `r`, the chain is `r, r + w, r + 2w, ...`. Along a chain, `new` at position `j` is the sum of the last `L + 1` entries of `old` ending at position `j`. That is a **sliding window sum**: add the entry entering the window, subtract the one leaving it. Each capacity is visited once per type.

**Trace.** Weight 2, limit 1, `old = [1] * 7` (capacities 0..6). The window holds `L + 1 = 2` entries. Chain for remainder 0 is capacities 0, 2, 4, 6:

| position j | capacity | add `old` | remove `old` at position j − 2 | window = `new` |
|---|---|---|---|---|
| 0 | 0 | 1 | | 1 |
| 1 | 2 | 1 | | 2 |
| 2 | 4 | 1 | capacity 0: 1 | 2 |
| 3 | 6 | 1 | capacity 2: 1 | 2 |

`new[4] = 2`: zero copies (`old[4]`) or one copy (`old[2]`); two copies would exceed the limit, which is why `old[0]` left the window.

```python
import random
from itertools import product


def count_bounded(weights: list[int], limits: list[int], target: int) -> int:
    """Number of copy-count vectors with 0 <= k_i <= limits[i] and total weight target."""
    if len(weights) != len(limits):
        raise ValueError("weights and limits must have equal length")
    if target < 0 or any(w <= 0 for w in weights) or any(k < 0 for k in limits):
        raise ValueError("invalid target, weight, or limit")
    ways = [0] * (target + 1)
    ways[0] = 1
    for weight, limit in zip(weights, limits):
        new = [0] * (target + 1)
        for r in range(min(weight, target + 1)):
            chain = range(r, target + 1, weight)
            window = 0
            for j, c in enumerate(chain):
                window += ways[c]  # Entry k = 0 enters the window.
                if j > limit:
                    window -= ways[chain[j - limit - 1]]  # k = limit + 1 leaves.
                new[c] = window
        ways = new
    return ways[target]


def brute(weights, limits, target):
    return sum(
        1
        for counts in product(*(range(k + 1) for k in limits))
        if sum(k * w for k, w in zip(counts, weights)) == target
    )


def main():
    assert count_bounded([2], [2], 4) == 1
    assert count_bounded([2], [1], 4) == 0
    assert count_bounded([1, 2], [3, 1], 3) == 2  # 1+1+1 or 1+2.
    assert count_bounded([1], [5], 2) == 1  # Grouping would say 2.
    assert count_bounded([], [], 0) == 1
    assert count_bounded([3], [0], 0) == 1

    rng = random.Random(17)
    for _ in range(400):
        n = rng.randint(0, 4)
        ws = [rng.randint(1, 5) for _ in range(n)]
        ls = [rng.randint(0, 4) for _ in range(n)]
        target = rng.randint(0, 20)
        expected = brute(ws, ls, target)
        assert count_bounded(ws, ls, target) == expected


if __name__ == "__main__":
    main()
```

Each type costs O(T) time no matter how large its limit is, so the total is O(nT) time and O(T) space. The same residue-chain idea also speeds up bounded *maximization* to O(nT), using a sliding window maximum with a monotonic deque; see [Monotonic Stack and Deque](../06-monotonic-stack-and-deque/README.md).

## 9. When the capacity is huge: index by value

Suppose there are 100 items with weights up to `10^9` and capacity `10^11`, but each value is at most 100. A table of size `W` is impossible. But the total value is at most `100 · 100 = 10^4`, which is small.

Swap the roles: make value the index and weight the stored number.

**State.** `minw[v]` = the smallest total weight of a subset with total value **exactly** `v`, or `inf` if no subset has that value.

**Transition.** For item `(w, x)`, either skip it or take it:

$$
minw_i[v] = \min\big(minw_{i-1}[v],\; minw_{i-1}[v - x_{i-1}] + w_{i-1}\big)
$$

**Base case.** `minw[0] = 0`, all others `inf`. Loop `v` downward (it is still 0/1).

**Answer.** The largest `v` with `minw[v] <= W`.

**Trace.** Items `(w, v)` = `(1, 15)`, `(3, 20)`, `(4, 30)`, capacity 4. The reachable values and their lightest weights end up as: 0 → 0, 15 → 1, 20 → 3, 30 → 4, 35 → 4, 45 → 5, 50 → 7, 65 → 8. The largest value with weight at most 4 is 35, matching §1.

```python
import random
from itertools import product
from math import inf


def knapsack_by_value(weights: list[int], values: list[int], capacity: int) -> int:
    if len(weights) != len(values) or capacity < 0:
        raise ValueError("matching arrays and capacity >= 0 are required")
    if any(w < 0 for w in weights) or any(v < 0 for v in values):
        raise ValueError("weights and values must be nonnegative")
    total = sum(values)
    minw = [inf] * (total + 1)
    minw[0] = 0
    for weight, value in zip(weights, values):
        for v in range(total, value - 1, -1):
            if minw[v - value] + weight < minw[v]:
                minw[v] = minw[v - value] + weight
    return max(v for v in range(total + 1) if minw[v] <= capacity)


def brute(weights, values, capacity):
    best = 0
    for picks in product((0, 1), repeat=len(weights)):
        if sum(w for w, p in zip(weights, picks) if p) <= capacity:
            best = max(best, sum(v for v, p in zip(values, picks) if p))
    return best


def main():
    assert knapsack_by_value([1, 3, 4], [15, 20, 30], 4) == 35
    big = 10**12
    assert knapsack_by_value([big, big, 2 * big], [3, 4, 6], 2 * big) == 7
    assert knapsack_by_value([], [], 5) == 0

    rng = random.Random(21)
    for _ in range(300):
        n = rng.randint(0, 8)
        ws = [rng.randint(1, 10**9) for _ in range(n)]
        vs = [rng.randint(0, 8) for _ in range(n)]
        cap = rng.randint(0, 4 * 10**9)
        assert knapsack_by_value(ws, vs, cap) == brute(ws, vs, cap)


if __name__ == "__main__":
    main()
```

Time O(n · V) and space O(V), where `V` is the sum of values. The general rule: **index the table by whichever quantity is small**, and store the other one. Negative values break this, because the range of reachable value sums is no longer `0..V`.

## 10. Summary: state choices

| Constraint | Adaptation | Caution |
|---|---|---|
| Huge weights, small values | `minw[value]` instead of `best[weight]` | Negative values break the index range |
| Feasibility only | Boolean `can[c]`, or an integer bitset | Descending loop for 0/1 |
| Count subsets | `ways[c]`, `ways[0] = 1` | Zeros double counts; that is correct for distinct indices |
| Exactly `k` items | Add a count dimension: `dp[k][c]` | Loop both `k` and `c` downward |
| Two budgets (weight and volume) | `dp[c1][c2]` | Memory is the product of both budgets |
| Count optimal selections | Store `(best, ways)` per cell | Add counts on ties |
| Recover copies after grouping | Keep group sizes and the full table | One group stands for several copies |

## 11. Pitfalls and practice

1. **Ascending loop in 0/1 knapsack.** It reuses items. Trace a single item with capacity `2w` to catch it.
2. **Wrong loop nesting for coin counts.** Coins outside counts combinations; totals outside counts sequences. Test with coins `{1, 2}`, target 3: answers 2 and 3.
3. **Mixing exact and at-most.** An exact definition needs `-inf` for positive capacities in row 0. All zeros means at-most.
4. **Using 0 for "impossible" in a min problem.** Unreachable must be `inf` so it never wins a `min`.
5. **Reconstructing from a single row.** Later items overwrite the information. Keep the full table.
6. **Binary grouping for counting.** It counts the same copy count more than once.
7. **Forgetting the parity check in target sum.** `(total + target)` must be even and nonnegative.
8. **Not deduplicating coin types.** `[2, 2]` as coin types would double-count combinations.
9. **Pseudo-polynomial blowup.** A table of size `W = 10^12` will not fit. Index by value, or use a different method.
10. **Trusting greedy for coins.** Coins `[1, 3, 4]` and target 6 break it.

Practice: Partition Equal Subset Sum, Target Sum, Last Stone Weight II, Ones and Zeroes, Coin Change, Coin Change II, Combination Sum IV, Perfect Squares, Profitable Schemes, Number of Ways to Earn Points, Partition to K Equal Sum Subsets (revisit after [Bitmask DP](09-bitmask-dp.md)).

Next: [Grid DP](05-grid-dp.md).
