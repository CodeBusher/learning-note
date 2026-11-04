# Interval DP — Solve Short Pieces, Then Glue Them

## 1. Matrix-chain multiplication

Matrix `A_i` has shape `d[i] × d[i+1]`. Multiplying a `p × q` matrix by a `q × r` matrix costs `p·q·r` scalar multiplications. Matrix multiplication is associative, so the parentheses change only the cost, never the result. Find the cheapest parenthesization.

With `d = [10, 30, 5, 60]` there are three matrices `A0: 10×30`, `A1: 30×5`, `A2: 5×60`, and two orders:

- `((A0 A1) A2)`: `10·30·5 = 1500` gives a `10×5` matrix, then `10·5·60 = 3000`. Total **4500**.
- `(A0 (A1 A2))`: `30·5·60 = 9000` gives a `30×60` matrix, then `10·30·60 = 18000`. Total **27000**.

Same product, six times the work.

### 1.1 Brute force

Every parenthesization has one **final** multiplication. It splits the chain into a left part `A_l … A_{k-1}` and a right part `A_k … A_{r-1}`, and each part is parenthesized on its own. So the number of parenthesizations of `n` matrices is

$$
P(1) = 1, \qquad P(n) = \sum_{k=1}^{n-1} P(k)\,P(n-k).
$$

These are the **Catalan numbers** `1, 1, 2, 5, 14, 42, …`; 20 matrices already have 1,767,263,190 orders, and the growth is roughly `4^n`. But the recursion already repeats itself: the best way to multiply `A1 A2` is needed by many different outer splits. That is the opening for DP.

### 1.2 The state is an interval

Earlier chapters used prefixes ("the first `i` items"). Here a subproblem is a **contiguous block in the middle**, so the state is an interval. Intervals are half-open: `[l, r)` covers matrices `l, …, r-1`.

- **State.** `dp[l][r]` = the minimum cost to multiply `A_l … A_{r-1}`.
- **Transition.** Choose the final multiplication, between `A_{k-1}` and `A_k`. The left part becomes a `d[l] × d[k]` matrix and the right part a `d[k] × d[r]` matrix, so the final step costs `d[l]·d[k]·d[r]`:

$$
dp[l][r] = \min_{l<k<r} \bigl\{ dp[l][k] + dp[k][r] + d[l]\,d[k]\,d[r] \bigr\}.
$$

- **Base.** A single matrix needs no work: `dp[l][l+1] = 0`.
- **Reconstruction.** Store the best `k` in `split[l][r]`.

**Order.** Both `[l, k)` and `[k, r)` are strictly **shorter** than `[l, r)`. So fill the table by increasing length:

```text
length 1:  [0,1) [1,2) [2,3) [3,4)       base cases
length 2:  [0,2) [1,3) [2,4)             read length-1 cells
length 3:  [0,3) [1,4)                   read length-1 and length-2 cells
length 4:  [0,4)                         the answer
```

### 1.3 Trace

Take `d = [40, 20, 30, 10, 30]`, four matrices.

Length 2 has one split each: `[0,2)` = `40·20·30 = 24000`, `[1,3)` = `6000`, `[2,4)` = `9000`. Length 3 and 4 compare splits; the winning `k` is starred:

| Interval | `k = 1` | `k = 2` | `k = 3` | `dp` |
|---|---|---|---|---|
| `[0,3)` | `0 + 6000 + 8000 = 14000`* | `24000 + 0 + 12000 = 36000` | | 14000 |
| `[1,4)` | | `0 + 9000 + 18000 = 27000` | `6000 + 0 + 6000 = 12000`* | 12000 |
| `[0,4)` | `0 + 12000 + 24000 = 36000` | `24000 + 9000 + 36000 = 69000` | `14000 + 0 + 12000 = 26000`* | **26000** |

| `dp[l][r]` | r=1 | r=2 | r=3 | r=4 |
|---|---|---|---|---|
| l=0 | 0 | 24000 | 14000 | **26000** |
| l=1 | | 0 | 6000 | 12000 |
| l=2 | | | 0 | 9000 |
| l=3 | | | | 0 |

Following splits: `[0,4)` splits at 3, `[0,3)` splits at 1, giving `((A0 (A1 A2)) A3)`.

```python
import random
from math import inf


def matrix_chain(d: list[int]) -> tuple[int, str]:
    """A_i is d[i] x d[i+1]. Return (min cost, parenthesization)."""
    if not d or any(x <= 0 for x in d):
        raise ValueError("need at least one positive dimension")
    n = len(d) - 1
    if n == 0:
        return 0, ""
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    split = [[-1] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            dp[l][r] = inf
            for k in range(l + 1, r):
                cost = dp[l][k] + dp[k][r] + d[l] * d[k] * d[r]
                if cost < dp[l][r]:
                    dp[l][r], split[l][r] = cost, k

    def show(l: int, r: int) -> str:
        if r - l == 1:
            return f"A{l}"
        k = split[l][r]
        return f"({show(l, k)} {show(k, r)})"

    return dp[0][n], show(0, n)


def all_costs(d: list[int], l: int, r: int) -> list[int]:
    """Brute force: cost of every parenthesization of A_l..A_{r-1}."""
    if r - l == 1:
        return [0]
    out = []
    for k in range(l + 1, r):
        for left in all_costs(d, l, k):
            for right in all_costs(d, k, r):
                out.append(left + right + d[l] * d[k] * d[r])
    return out


def row_major_bug(d: list[int]) -> int:
    """Wrong order: l ascending reads dp[k][r] before row k is filled."""
    n = len(d) - 1
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for l in range(n):
        for r in range(l + 2, n + 1):
            dp[l][r] = min(dp[l][k] + dp[k][r] + d[l] * d[k] * d[r] for k in range(l + 1, r))
    return dp[0][n]


def main():
    assert matrix_chain([10, 30, 5, 60]) == (4500, "((A0 A1) A2)")
    assert row_major_bug([40, 20, 30, 10, 30]) == 20000  # too small: read unfilled zeros
    assert matrix_chain([40, 20, 30, 10, 30]) == (26000, "((A0 (A1 A2)) A3)")
    assert matrix_chain([5, 7]) == (0, "A0") and matrix_chain([5]) == (0, "")
    assert [len(all_costs([1] * (n + 1), 0, n)) for n in range(1, 7)] == [1, 1, 2, 5, 14, 42]
    rng = random.Random(1)
    for _ in range(200):
        d = [rng.randint(1, 20) for _ in range(rng.randint(2, 8))]
        assert matrix_chain(d)[0] == min(all_costs(d, 0, len(d) - 1))


if __name__ == "__main__":
    main()
```

O(n²) intervals, each trying O(n) splits: O(n³) time, O(n²) space.

**Why it is correct.** Every parenthesization has exactly one final multiplication, so some `k` describes it: the cases are exhaustive. Given `k`, the final cost is fixed and the two sides do not affect each other. If either side were not optimal, swapping in a cheaper one would lower the total.

### 1.4 Fill order: the silent bug

Filling "row by row" (`l = 0, 1, …`, each row left to right) looks natural and is wrong: `dp[0][4]` reads `dp[1][4]` before row 1 exists. It does not crash. On the trace above it reads zeros and returns 20000 instead of 26000 (`row_major_bug` in the script).

`dp[l][r]` reads `dp[l][k]` (same `l`, smaller `r`) and `dp[k][r]` (larger `l`, same `r`). So any of these is safe: by increasing length; by **decreasing `l`, then increasing `r`** (common in contest code); or memoized recursion, which finds the order itself. Because the wrong order fails silently, always test a bottom-up table against a brute force or a memoized version.

## 2. Burst balloons: choose the *last* event

**Problem.** Balloons in a row have values `nums`. Bursting balloon `i` earns `left · nums[i] · right`, where `left` and `right` are its **current** neighbors (a missing neighbor counts as 1). After a burst, its neighbors become adjacent. Burst all balloons; maximize the total. For `[3, 1, 5, 8]` the answer is 167: burst 1 (`3·1·5 = 15`), then 5 (`3·5·8 = 120`), then 3 (`1·3·8 = 24`), then 8 (`1·8·1 = 8`).

**Brute force.** Try all `n!` burst orders: 3.6 million for 10 balloons.

**Why "first" fails.** Copy matrix chain and pick the balloon `k` burst **first** in `[l, r)`. Afterwards `k-1` and `k+1` are neighbors, so the score of bursting `k-1` later depends on what is left on the right side. The halves interact, and `dp[l][k] + dp[k+1][r]` is wrong. A split is only valid when choices inside one half do not change what is legal or what things cost in the other.

**"Last" works.** Pad the array: `b = [1] + nums + [1]`. Use an **open** interval between two balloons `i` and `j` that are still standing.

- **State.** `dp[i][j]` = the most coins from bursting every balloon strictly between `i` and `j`, while `i` and `j` stay.
- **Transition.** Let `k` be the **last** balloon burst between them. When `k` goes, everything else between `i` and `j` is gone, so its neighbors are exactly `b[i]` and `b[j]`. Before that, `k` stands between `(i, k)` and `(k, j)` and separates them, so the two sides are independent.

$$
dp[i][j] = \max_{i<k<j} \bigl\{ dp[i][k] + dp[k][j] + b[i]\,b[k]\,b[j] \bigr\}.
$$

- **Base.** `dp[i][i+1] = 0`: nothing between adjacent positions.
- **Order.** By increasing `j - i`. The answer is `dp[0][n+1]`.

**Trace** for `b = [1, 3, 1, 5, 8, 1]`:

| `dp[i][j]` | j=2 | j=3 | j=4 | j=5 |
|---|---|---|---|---|
| i=0 | 3 | 30 | 159 | **167** |
| i=1 | | 15 | 135 | 159 |
| i=2 | | | 40 | 48 |
| i=3 | | | | 40 |

`dp[1][3]` has only balloon 2 (value 1) between 3 and 5: `3·1·5 = 15`. For `dp[0][5]`, bursting `k = 4` (value 8) last gives `dp[0][4] + dp[4][5] + 1·8·1 = 159 + 0 + 8 = 167`.

```python
import random
from itertools import permutations


def burst_balloons(nums: list[int]) -> int:
    if any(x < 0 for x in nums):
        raise ValueError("values must be nonnegative")
    b = [1] + nums + [1]
    m = len(b)
    dp = [[0] * m for _ in range(m)]
    for gap in range(2, m):
        for i in range(m - gap):
            j = i + gap
            dp[i][j] = max(dp[i][k] + dp[k][j] + b[i] * b[k] * b[j]
                           for k in range(i + 1, j))
    return dp[0][m - 1]


def brute(nums: list[int]) -> int:
    best = 0
    for order in permutations(range(len(nums))):
        alive, total = list(range(len(nums))), 0
        for idx in order:
            pos = alive.index(idx)
            left = nums[alive[pos - 1]] if pos > 0 else 1
            right = nums[alive[pos + 1]] if pos + 1 < len(alive) else 1
            total += left * nums[idx] * right
            alive.pop(pos)
        best = max(best, total)
    return best


def main():
    assert burst_balloons([3, 1, 5, 8]) == 167
    assert burst_balloons([1, 5]) == 10
    assert burst_balloons([]) == 0
    rng = random.Random(2)
    for _ in range(150):
        nums = [rng.randint(0, 9) for _ in range(rng.randint(0, 6))]
        assert burst_balloons(nums) == brute(nums)


if __name__ == "__main__":
    main()
```

O(n³) time, O(n²) space. The padding 1s are the outside neighbors and are never burst.

**The general rule.** For deletion problems, "last" is the useful event: when something is deleted last, everything else in the interval is gone, so its neighbors are the interval's own boundaries, which the state already knows.

## 3. Merging adjacent stones: the join cost is a range sum

**Problem.** Piles of stones sit in a row. A move merges **two adjacent** piles into one, costing the size of the new pile. Merge everything into one pile at minimum cost. For `[3, 5, 1, 2]` the answer is 22: merge `3+5` (8), merge `1+2` (3), merge `8+3` (11).

Only neighbors may merge, so the Huffman greedy (always merge the two smallest piles) does not apply.

**State and transition.** `dp[l][r]` = the minimum cost to merge `stones[l:r]` into one pile. The **last** merge joins a pile made from `[l, k)` with one made from `[k, r)`. Whatever happened before, that final merge costs the interval's total:

$$
dp[l][r] = \min_{l<k<r} \bigl\{ dp[l][k] + dp[k][r] \bigr\} + \mathrm{sum}(l, r), \qquad \mathrm{sum}(l, r) = P[r] - P[l].
$$

`P` is the prefix-sum array from [Prefix Sums](../04-range-queries/01-prefix-sums.md), so each interval sum is O(1). Base: `dp[l][l+1] = 0`.

**Trace** for `[3, 5, 1, 2]` (prefix sums `0, 3, 8, 9, 11`):

| `dp[l][r]` | r=2 | r=3 | r=4 |
|---|---|---|---|
| l=0 | 8 | 15 | **22** |
| l=1 | | 6 | 11 |
| l=2 | | | 3 |

`dp[0][4] = min(0 + 11, 8 + 3, 15 + 0) + 11 = 22`.

### 3.1 Variant: merge exactly `K` piles per move

Each move now merges `K` **consecutive** piles, reducing the count by `K - 1`. Going from `n` piles to 1 is possible only if

$$
(n - 1) \bmod (K - 1) = 0,
$$

otherwise return `-1`. What changes in the DP:

- `dp[l][r]` = the minimum cost to merge `[l, r)` into **as few piles as possible**, which is `(r - l - 1) mod (K - 1) + 1` piles.
- Split off a left part that becomes exactly one pile. Its length `k - l` must be `1, K, 2K-1, …`, so `k` steps by `K - 1`.
- Add `sum(l, r)` only when `[l, r)` can collapse to one pile, that is `(r - l - 1) mod (K - 1) = 0`.

For `K = 2` every step is allowed and the sum is always added: the formula above.

```python
import random
from functools import cache
from math import inf


def merge_stones(stones: list[int], k: int = 2) -> int:
    """Min cost to merge into one pile, merging k adjacent piles per move."""
    if k < 2:
        raise ValueError("k must be at least 2")
    n = len(stones)
    if n == 0:
        return 0
    if (n - 1) % (k - 1):
        return -1
    prefix = [0]
    for x in stones:
        prefix.append(prefix[-1] + x)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            dp[l][r] = min(dp[l][m] + dp[m][r] for m in range(l + 1, r, k - 1))
            if (length - 1) % (k - 1) == 0:
                dp[l][r] += prefix[r] - prefix[l]
    return dp[0][n]


def brute(stones: list[int], k: int) -> int:
    @cache
    def go(piles: tuple) -> float:
        if len(piles) == 1:
            return 0
        best = inf
        for i in range(len(piles) - k + 1):
            s = sum(piles[i:i + k])
            best = min(best, s + go(piles[:i] + (s,) + piles[i + k:]))
        return best

    ans = go(tuple(stones)) if stones else 0
    return -1 if ans == inf else ans


def main():
    assert merge_stones([3, 5, 1, 2]) == 22
    assert merge_stones([3, 2, 4, 1], 2) == 20
    assert merge_stones([3, 2, 4, 1], 3) == -1
    assert merge_stones([3, 5, 1, 2, 6], 3) == 25
    assert merge_stones([7]) == 0
    rng = random.Random(3)
    for _ in range(300):
        k = rng.randint(2, 4)
        stones = [rng.randint(1, 9) for _ in range(rng.randint(1, 7))]
        assert merge_stones(stones, k) == brute(stones, k), (stones, k)


if __name__ == "__main__":
    main()
```

O(n³ / (K-1)) time and O(n²) space. Recomputing `sum(stones[l:r])` inside the split loop would make it O(n⁴); precompute prefix sums.

## 4. Palindrome partitioning: when a prefix DP is enough

**Problem.** Cut a string into pieces that are all palindromes, with as few cuts as possible. For `"aab"` the answer is 1 (`"aa" | "b"`). For `"abacdc"` it is 1 (`"aba" | "cdc"`). Brute force tries all `2^(n-1)` ways to cut the `n - 1` gaps.

Both methods below use the palindrome table `pal[l][r]` built by length in [Sequences and Strings](06-sequences-and-strings.md).

**Interval version.** `cuts[l][r]` = 0 if `s[l:r]` is a palindrome, else `1 + min over k of cuts[l][k] + cuts[k][r]`. It is correct but O(n³), and it solves every substring's problem when the question needs only prefixes.

**Prefix version.** Every subproblem we actually need starts at index 0. So use a prefix state: `best[i]` = the minimum number of **pieces** for `s[:i]`, and the last piece is some palindrome `s[j:i]`:

$$
best[i] = \min_{\substack{0 \le j < i \\ pal[j][i]}} \bigl\{ best[j] + 1 \bigr\}, \qquad best[0] = 0.
$$

The answer is `best[n] - 1` cuts, in O(n²) time. For `"aab"`: `best = [0, 1, 1, 2]` (`best[2] = 1` from the piece `"aa"`, `best[3] = best[2] + 1` from `"b"`), so 1 cut.

The lesson: when the outer problem only grows from one end, a prefix DP over a precomputed interval table beats a full interval DP by one dimension.

```python
import random
from math import inf


def pal_table(s: str) -> list[list[bool]]:
    n = len(s)
    pal = [[True] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            pal[l][l + length] = s[l] == s[l + length - 1] and pal[l + 1][l + length - 1]
    return pal


def min_cut_prefix(s: str) -> tuple[int, list[str]]:
    n = len(s)
    if n == 0:
        return 0, []
    pal = pal_table(s)
    best = [0] + [inf] * n
    start = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(i):
            if pal[j][i] and best[j] + 1 < best[i]:
                best[i], start[i] = best[j] + 1, j
    pieces, i = [], n
    while i > 0:
        pieces.append(s[start[i]:i])
        i = start[i]
    return best[n] - 1, pieces[::-1]


def brute(s: str) -> int:
    n, best = len(s), inf
    for mask in range(1 << max(n - 1, 0)):
        bounds = [0] + [g + 1 for g in range(n - 1) if mask >> g & 1] + [n]
        parts = [s[a:b] for a, b in zip(bounds, bounds[1:])]
        if all(p == p[::-1] for p in parts):
            best = min(best, len(parts) - 1)
    return best if n else 0


def main():
    assert min_cut_prefix("aab") == (1, ["aa", "b"])
    assert min_cut_prefix("abacdc") == (1, ["aba", "cdc"])
    assert min_cut_prefix("") == (0, []) and min_cut_prefix("a") == (0, ["a"])
    rng = random.Random(4)
    for _ in range(300):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 10)))
        cuts, pieces = min_cut_prefix(s)
        assert cuts == brute(s)
        assert "".join(pieces) == s and all(p == p[::-1] for p in pieces)


if __name__ == "__main__":
    main()
```

The table costs O(n²) space; expanding around each center marks palindromes with O(n) extra space instead.

## 5. Trees over intervals: the root is the split

A binary tree whose in-order sequence is fixed is another interval split: the root divides the keys (or leaves) into a left interval and a right interval. [Binary search trees](../03-trees/03-binary-search-trees.md) are the standard example.

### 5.1 Optimal binary search tree

**Problem.** Sorted keys `0 … n-1` are searched with frequencies `freq`. A key at depth `d` (root depth 1) costs `d` comparisons per search. Build a BST minimizing `Σ freq[i] · depth(i)`. For `freq = [34, 8, 50]` the best tree has key 2 at the root, key 0 below it, and key 1 below key 0: `50·1 + 34·2 + 8·3 = 142`.

**State.** `cost[l][r]` = the minimum cost of a BST on keys `[l, r)`, depths counted from that subtree's root.

**Transition.** Choose the root `k`. The left subtree holds `[l, k)` and the right holds `[k+1, r)`. Hanging them under `k` pushes every key one level deeper, adding each frequency once more; the root costs `freq[k]`. Together that adds `W(l, r) = Σ_{l≤i<r} freq[i]`, whatever `k` is:

$$
cost[l][r] = \min_{l \le k < r} \bigl\{ cost[l][k] + cost[k+1][r] \bigr\} + W(l, r), \qquad cost[l][l] = 0.
$$

What differs from matrix chain: the root key belongs to **neither** side (`[l, k)` and `[k+1, r)`), and empty sides are allowed, so the base is the empty interval and the loop starts at length 1.

### 5.2 Minimum cost tree from leaf values

**Problem.** `arr` lists, in order, the leaves of a binary tree in which every internal node has two children. An internal node's value is (largest leaf on its left) × (largest leaf on its right). Minimize the sum of internal values. For `[6, 2, 4]`: `((6 2) 4)` gives `12 + 24 = 36`; `(6 (2 4))` gives `8 + 24 = 32`. Answer 32.

This is matrix chain with a different join:

$$
dp[l][r] = \min_{l<k<r} \bigl\{ dp[l][k] + dp[k][r] + \max(arr[l:k]) \cdot \max(arr[k:r]) \bigr\}, \qquad dp[l][l+1] = 0.
$$

Precompute range maxima `mx[l][r]` in O(n²) so the join is O(1). A greedy with a [monotonic stack](../06-monotonic-stack-and-deque/README.md) solves this specific problem in O(n); the interval DP is the general tool and the reference to test it against.

```python
import random


def optimal_bst(freq: list[int]) -> int:
    if any(f < 0 for f in freq):
        raise ValueError("frequencies must be nonnegative")
    n = len(freq)
    prefix = [0]
    for f in freq:
        prefix.append(prefix[-1] + f)
    cost = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(1, n + 1):
        for l in range(n - length + 1):
            r = l + length
            cost[l][r] = min(cost[l][k] + cost[k + 1][r] for k in range(l, r)) \
                + prefix[r] - prefix[l]
    return cost[0][n]


def leaf_tree(arr: list[int]) -> int:
    if not arr:
        raise ValueError("need at least one leaf")
    n = len(arr)
    mx = [[0] * (n + 1) for _ in range(n + 1)]
    for l in range(n):
        for r in range(l + 1, n + 1):
            mx[l][r] = max(mx[l][r - 1], arr[r - 1])
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            dp[l][r] = min(dp[l][k] + dp[k][r] + mx[l][k] * mx[k][r]
                           for k in range(l + 1, r))
    return dp[0][n]


def all_bsts(l: int, r: int):
    """Yield every BST on keys [l, r) as {key: depth}."""
    if l == r:
        yield {}
        return
    for k in range(l, r):
        for left in all_bsts(l, k):
            for right in all_bsts(k + 1, r):
                depths = {key: d + 1 for key, d in {**left, **right}.items()}
                depths[k] = 1
                yield depths


def all_leaf_trees(arr: list[int]):
    """Yield (internal sum, max leaf) for every full binary tree over arr."""
    if len(arr) == 1:
        yield 0, arr[0]
        return
    for k in range(1, len(arr)):
        for ls, lm in all_leaf_trees(arr[:k]):
            for rs, rm in all_leaf_trees(arr[k:]):
                yield ls + rs + lm * rm, max(lm, rm)


def main():
    assert optimal_bst([34, 8, 50]) == 142
    assert optimal_bst([]) == 0 and optimal_bst([5]) == 5
    assert leaf_tree([6, 2, 4]) == 32 and leaf_tree([4, 11]) == 44
    rng = random.Random(5)
    for _ in range(200):
        freq = [rng.randint(0, 20) for _ in range(rng.randint(0, 7))]
        brute = min(sum(freq[k] * d for k, d in t.items())
                    for t in all_bsts(0, len(freq)))
        assert optimal_bst(freq) == brute
        arr = [rng.randint(1, 15) for _ in range(rng.randint(1, 7))]
        assert leaf_tree(arr) == min(s for s, _ in all_leaf_trees(arr))


if __name__ == "__main__":
    main()
```

Both are O(n³) time and O(n²) space.

## 6. The pattern

Every problem above except palindrome partitioning fits one recurrence:

$$
dp[l][r] = \operatorname{best}_{k} \bigl\{ dp[l][k] + dp[k][r] + \mathrm{join}(l, k, r) \bigr\},
$$

filled so that shorter intervals come first. Two things must be true:

1. **The halves are independent.** What happens inside one side must not change what is legal or what things cost in the other. If it does, add boundary information to the state or pick a different event.
2. **The join depends only on what the state knows**: the boundaries `l`, `k`, `r`, and precomputed range facts (sums, maxima).

Which event to call "the split" is the real design choice. Pick the one whose surroundings are known when it happens:

| Problem | Event chosen as the split | Why its surroundings are known |
|---|---|---|
| Matrix chain | Final multiplication | Outer dimensions `d[l]`, `d[r]` are fixed by the interval |
| Burst balloons | Last balloon burst | Its neighbors are the interval's boundaries |
| Merge stones | Final merge | It always costs the interval sum |
| Optimal BST | Root | Every other key sinks one level: add the interval weight |
| Leaf-value tree | Root | Join is the product of two range maxima |

### 6.1 A glimpse of Knuth's optimization

All of these cost O(n³): O(n²) intervals times O(n) splits. For some of them the best split point is **monotone**:

$$
opt[l][r-1] \le opt[l][r] \le opt[l+1][r].
$$

Then the scan for `[l, r)` only needs the range between two known split points, and the total work telescopes to O(n²). This is **Knuth's optimization**. It holds for the optimal BST and for two-pile stone merging. It does **not** hold for matrix chain in general, and burst balloons does not fit it either. Check the monotonicity on random inputs before relying on it; [Faster Transitions](12-faster-transitions.md) gives the conditions and the proof.

## 7. Pitfalls and practice

1. **Row-major order reads unfinished cells** and returns a plausible, too-small answer. Fill by length, or by decreasing `l` with increasing `r`.
2. **Half-open versus closed intervals.** Decide whether `r` is included and keep the base case (`r - l == 1` or `l == r`) consistent with it.
3. **"First" versus "last".** In burst balloons, the first burst makes the halves interact; the last one has fixed neighbors. Pad the ends with 1s instead of special-casing them.
4. **Recomputing sums or maxima inside the split loop** turns O(n³) into O(n⁴). Precompute prefix sums or a range-maximum table.
5. **Check feasibility first** in merge-stones with `K` piles: `(n - 1) mod (K - 1) = 0`.
6. **Optimal BST splits exclude the root.** Use `[l, k)` and `[k+1, r)`, and allow empty sides.
7. **Use a prefix DP when only prefixes matter.** Palindrome partitioning is O(n²) that way instead of O(n³).
8. **Greedy shortcuts need proof.** Merging the two smallest adjacent piles is not optimal; test greedy ideas against the DP.

Practice: Matrix Chain Multiplication, Burst Balloons, Minimum Cost to Merge Stones, Palindrome Partitioning II, Minimum Cost Tree From Leaf Values, Optimal Binary Search Tree, Minimum Score Triangulation of Polygon, Minimum Cost to Cut a Stick, Strange Printer, Remove Boxes, Guess Number Higher or Lower II, Zuma Game.

Next: [Tree and DAG DP](08-tree-and-dag-dp.md).
