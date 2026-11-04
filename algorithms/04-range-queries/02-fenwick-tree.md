# Fenwick Tree — Prefix Sums That Survive Updates

## 1. The problem and two brute forces

A scoreboard holds the points of 8 players. Two kinds of requests arrive in any order:

- `add(i, delta)`: player `i` gains `delta` points (`delta` may be negative).
- `query(l, r)`: total points of players `l` through `r`, both included.

```text
player i     0    1    2    3    4    5    6    7
points       3    2   −1    6    5    4   −3    3
```

Example requests, in order:

1. `query(2, 6)` → `−1 + 6 + 5 + 4 − 3 = 11`
2. `add(2, +2)` → player 2 now has 1
3. `query(2, 6)` → `1 + 6 + 5 + 4 − 3 = 13`

Two simple designs, and why each fails:

| Design | `add` | `query` | Bad case |
|---|---:|---:|---|
| Keep the raw array | O(1): change one cell | O(n): add up the range | many queries |
| Keep a prefix-sum table `P` | O(n): every `P[k]` with `k > i` shifts | O(1) | many updates |

With `n = q = 100,000` and requests split evenly, either design does about `5 · 10⁹` steps. The goal is a middle ground where each operation touches only O(log n) stored numbers. The structure that does this is the **Fenwick tree**, also called a **binary indexed tree** (BIT): one array and two four-line loops.

## 2. The observation: store sums of a few well-chosen blocks

The prefix-sum table stores, for every length `k`, the sum of the **whole** prefix of that length. That is why an update is expensive: one element sits inside `n − i` stored prefixes.

Instead, store sums of **blocks** (short consecutive runs) and build each prefix out of a few blocks. Two demands pull against each other:

- Few blocks per prefix, so queries are fast.
- Each element inside few blocks, so updates are fast.

Powers of two satisfy both. Every positive whole number is a sum of distinct powers of two, its binary digits. For example `13 = 8 + 4 + 1` (binary `1101`). So the first 13 elements split into three blocks of lengths 8, 4 and 1:

```text
positions   1 2 3 4 5 6 7 8 | 9 10 11 12 | 13
            block of 8      | block of 4 | block of 1
```

If the structure stores exactly those blocks, the prefix of 13 costs three additions. A number up to `n` has at most `log₂ n + 1` binary digits, so any prefix needs at most that many blocks.

**Positions start at 1.** From here on, the tree numbers its positions `1, 2, …, n`. Element `a[i]` of the ordinary 0-based list lives at position `i + 1`. Section 7 explains why position 0 must be avoided; the code converts so that callers always use 0-based indices.

### Which block does each position store?

Each position `i` stores one block that **ends at `i`**. Its length is the value of the lowest `1` bit of `i` in binary, called `lowbit(i)`. For example `6 = 0110` has `lowbit(6) = 2`, so `tree[6]` covers `[5, 6]`; `8 = 1000` has `lowbit(8) = 8`, so `tree[8]` covers `[1, 8]`; `12 = 1100` covers `[9, 12]`; `13 = 1101` covers `[13, 13]`. Odd positions always store a single element.

**Invariant.** `tree[i]` is the sum of the `lowbit(i)` elements ending at position `i`:

$$
tree[i] = \sum_{j=i-\operatorname{lowbit}(i)+1}^{i} a[j] \qquad(\text{positions } 1..n).
$$

### Computing `lowbit` with one operation

In Python, `i & -i` gives `lowbit(i)`. Why? A negative number is stored in **two's complement**: `-i` equals "flip every bit of `i`, then add 1". Take `i = 12`:

```text
 i          = 0000 1100
 flip bits  = 1111 0011
 add 1      = 1111 0100   (this is −12)
 i & −i     = 0000 0100   = 4
```

Flipping turns the trailing zeros of `i` into ones; adding 1 carries through them and stops at the first zero, which is exactly where `i` had its lowest `1`. Every bit above that position is flipped relative to `i`, so it vanishes in the AND. Only the lowest `1` survives. [Binary Numbers](../11-bit-manipulation/01-binary-numbers.md) covers two's complement in more depth.

## 3. The responsibility ranges, drawn

The block each position stores is called its **responsibility range**. For `n = 16`:

```text
            1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16
tree[16]   [==============================================================]  [1, 16]
tree[8]    [==============================]                                  [1, 8]
tree[4]    [==============]                                                  [1, 4]
tree[12]                                   [==============]                  [9, 12]
tree[2]    [======]                                                          [1, 2]
tree[6]                    [======]                                          [5, 6]
tree[10]                                   [======]                          [9, 10]
tree[14]                                                   [======]          [13, 14]
tree[odd]  [==]    [==]    [==]    [==]    [==]    [==]    [==]    [==]      [i, i]
```

The two loops come straight from two properties of this picture:

- **Reading leftward.** The bar of `tree[i]` ends at `i`. Directly to its left, the next bar ends at `i − lowbit(i)`. Hopping from bar to bar leftward tiles a prefix with no gaps or overlaps.
- **Nesting upward.** Two bars are either disjoint or one contains the other. The bars containing position 5 are `tree[5]`, `tree[6]`, `tree[8]`, `tree[16]`, a chain where each contains the previous one.

This nesting is why it is called a *tree*: each bar's **parent** is the next larger bar that contains it. There are no pointers; the parent is computed from the index.

Below, every trace uses the scoreboard from §1. In positions 1–8, the values and the stored blocks are:

```text
position         1    2    3    4    5    6    7    8
a                3    2   −1    6    5    4   −3    3
block         [1,1][1,2][3,3][1,4][5,5][5,6][7,7][1,8]
tree             3    5   −1   10    5    9   −3   19
```

Check two of them: `tree[4] = 3 + 2 − 1 + 6 = 10`, and `tree[6] = 5 + 4 = 9`.

## 4. Prefix query: walk left by removing the lowest bit

**Goal.** `prefix(k)` = sum of positions `1..k`, the first `k` elements.

`tree[k]` is the last block of that prefix, covering `[k − lowbit(k) + 1, k]`. After adding it, what remains is the prefix of length `k − lowbit(k)`. Repeat until nothing remains. Subtracting `lowbit(k)` clears the lowest `1` bit of `k`.

**Trace** for `prefix(7)`. Binary `7 = 0111`:

| Step | `k` | Binary | `tree[k]` covers | `tree[k]` | Running total | Next `k = k − lowbit(k)` |
|---:|---:|:---:|---|---:|---:|---:|
| 1 | 7 | `0111` | `[7, 7]` | −3 | −3 | 6 |
| 2 | 6 | `0110` | `[5, 6]` | 9 | 6 | 4 |
| 3 | 4 | `0100` | `[1, 4]` | 10 | 16 | 0, stop |

`prefix(7) = 16`. Check: `3 + 2 − 1 + 6 + 5 + 4 − 3 = 16`. ✓ The three blocks `[1, 4]`, `[5, 6]`, `[7, 7]` match `7 = 4 + 2 + 1`.

Each step clears one `1` bit, so the loop runs once per `1` bit of `k`: at most `log₂ n + 1` times. It is correct because each step adds the block that ends at `k` and continues with the prefix that ends right before it: the blocks are consecutive, never overlap, and stop when the prefix is empty.

A range sum is two prefixes, exactly as in Chapter 1. For the 0-based request `query(2, 6)`, the elements live at positions 3–7:

$$
\operatorname{query}(2, 6) = \operatorname{prefix}(7) - \operatorname{prefix}(2) = 16 - 5 = 11.
$$

`prefix(2)` is a single step: `tree[2] = 5`.

## 5. Point update: walk up by adding the lowest bit

**Goal.** `a` at position `p` changes by `delta`. Every stored block that **contains** `p` must change by `delta`; no other block may change.

From the diagram, the blocks containing `p` form a chain: `tree[p]` itself, its parent, its parent's parent, and so on. The parent of `i` is `i + lowbit(i)`.

**Trace** for `add` of `+2` at position 3 (player 2 in 0-based terms):

| Step | `i` | Binary | `tree[i]` covers | Contains 3? | `tree[i]` before → after | Next `i = i + lowbit(i)` |
|---:|---:|:---:|---|:---:|---|---:|
| 1 | 3 | `0011` | `[3, 3]` | yes | −1 → 1 | 4 |
| 2 | 4 | `0100` | `[1, 4]` | yes | 10 → 12 | 8 |
| 3 | 8 | `1000` | `[1, 8]` | yes | 19 → 21 | 16 > 8, stop |

Positions 5, 6 and 7 were skipped, correctly: their blocks `[5, 5]`, `[5, 6]`, `[7, 7]` do not contain 3. Now `query(2, 6) = prefix(7) − prefix(2) = (−3 + 9 + 12) − 5 = 13`, matching request 3 in §1.

### Why exactly `i + lowbit(i)`?

Write `i` in binary as some higher bits, then its lowest `1`, then zeros. Its block has length `lowbit(i)` and ends at `i`.

1. **The parent contains the child.** Adding `lowbit(i)` to `i` carries into a higher bit, so `j = i + lowbit(i)` has `lowbit(j) ≥ 2 · lowbit(i)`. Its block ends at `j > i` and starts right after `j − lowbit(j) ≤ j − 2 · lowbit(i) = i − lowbit(i)`, and `i`'s block starts right after `i − lowbit(i)`. So `j`'s block contains all of `i`'s block.
2. **Nothing between them contains `i`.** Any `m` with `i < m < j` is `i + t` for some `t` from 1 to `lowbit(i) − 1`. The low bits of `i` are zero, so `lowbit(m) = lowbit(t) ≤ t`, and `m`'s block starts at `m − lowbit(m) + 1 ≥ i + 1`. It cannot contain `i`.

Example with `i = 4` (`0100`): `j = 8`. The positions in between, 5, 6, 7, have blocks `[5, 5]`, `[5, 6]`, `[7, 7]`, none of which reach back to 4.

3. **No block containing `p` is skipped.** Suppose `m` contains `p` and lies strictly between two chain steps `c < m < c + lowbit(c)`. Blocks either nest or are disjoint (§3); both `m`'s and `c`'s blocks contain `p`, so they overlap, and since `m` ends later, `m`'s block contains `c`, which point 2 rules out.

So the update changes exactly the blocks that contain `p`, each once. Each step moves to a strictly larger lowbit, so there are at most `log₂ n + 1` steps.

## 6. Build in O(n)

The plain way to build is to start with all zeros and call `add` for every element: O(n log n). There is a faster way that uses the parent relation directly.

Start with `tree[i] = a[i]` (each block holds only its last element). Then go through positions **in increasing order**. When we reach `i`, its block is complete, so we pass its sum up to its parent `i + lowbit(i)`.

**Trace** with `a = [3, 2, −1, 6, 5, 4, −3, 3]`:

| `i` | parent | Action | `tree[1..8]` after |
|---:|---:|---|---|
| start | — | copy `a` | `[3, 2, −1, 6, 5, 4, −3, 3]` |
| 1 | 2 | `tree[2] += 3` | `[3, 5, −1, 6, 5, 4, −3, 3]` |
| 2 | 4 | `tree[4] += 5` | `[3, 5, −1, 11, 5, 4, −3, 3]` |
| 3 | 4 | `tree[4] += −1` | `[3, 5, −1, 10, 5, 4, −3, 3]` |
| 4 | 8 | `tree[8] += 10` | `[3, 5, −1, 10, 5, 4, −3, 13]` |

Positions 5–7 repeat the pattern on the right half (`tree[6]` becomes 9, then `tree[8]` gains `9` and `−3`), giving `[3, 5, −1, 10, 5, 9, −3, 19]`, the table in §3.

**Why increasing order?** Every child of `i` is smaller than `i`. So by the time the loop reaches `i`, all children have already forwarded their sums, and `tree[i]` is complete before it is forwarded in turn. Going in decreasing order would forward `tree[2]` to `tree[4]` before `tree[1]` reached `tree[2]`, losing `a[1]` from `tree[4]`. By induction, each `tree[p]` is complete when forwarded: its children's blocks plus `a[p]` tile its block exactly.

## 7. Code: `Fenwick`

The public methods take 0-based indices, like every structure in this folder. Internally, element `i` lives at position `i + 1`.

`prefix_sum(k)` returns the sum of the first `k` elements, `a[0] + … + a[k − 1]`, the same meaning as `P[k]` in Chapter 1. Because "the first `k` elements" are exactly positions `1..k`, this method needs no conversion. `query(l, r)` is then `prefix_sum(r + 1) − prefix_sum(l)`, the Chapter 1 formula.

**Why must positions avoid 0?** `lowbit(0) = 0 & -0 = 0`. An update loop at position 0 would add 0 forever and never terminate. The `+ 1` conversion in `add` prevents that, and the bounds check stops bad input before it reaches the loop.

```python
from random import Random


class Fenwick:
    """Point add and inclusive range sum, 0-based API, 1-based inside."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.tree = [0] + list(nums)          # tree[p] starts as a[p - 1]
        for p in range(1, self.n + 1):        # O(n) build, increasing order
            parent = p + (p & -p)
            if parent <= self.n:
                self.tree[parent] += self.tree[p]

    def add(self, i: int, delta: int) -> None:
        """a[i] += delta."""
        if not 0 <= i < self.n:
            raise ValueError(f"index {i} out of range")
        p = i + 1
        while p <= self.n:
            self.tree[p] += delta
            p += p & -p

    def prefix_sum(self, k: int) -> int:
        """Sum of the first k elements, a[0] + ... + a[k - 1]."""
        if not 0 <= k <= self.n:
            raise ValueError(f"prefix length {k} out of range")
        total = 0
        while k > 0:
            total += self.tree[k]
            k -= k & -k
        return total

    def query(self, l: int, r: int) -> int:
        """Sum of a[l..r], both ends included."""
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")
        return self.prefix_sum(r + 1) - self.prefix_sum(l)


def main():
    bit = Fenwick([3, 2, -1, 6, 5, 4, -3, 3])
    assert bit.tree[1:] == [3, 5, -1, 10, 5, 9, -3, 19]   # §6 trace
    assert bit.prefix_sum(7) == 16                         # §4 trace
    assert bit.query(2, 6) == 11
    bit.add(2, 2)                                          # §5 trace
    assert bit.tree[1:] == [3, 5, 1, 12, 5, 9, -3, 21]
    assert bit.query(2, 6) == 13
    assert bit.prefix_sum(0) == 0

    assert Fenwick([]).prefix_sum(0) == 0
    for bad in [lambda: bit.add(8, 1), lambda: bit.add(-1, 1),
                lambda: bit.query(3, 2), lambda: bit.prefix_sum(9)]:
        try:
            bad()
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = Random(11)
    for _ in range(300):
        n = rng.randint(1, 20)
        a = [rng.randint(-9, 9) for _ in range(n)]
        bit = Fenwick(a)
        for _ in range(30):
            if rng.random() < 0.5:
                i, delta = rng.randrange(n), rng.randint(-5, 5)
                a[i] += delta
                bit.add(i, delta)
            else:
                l = rng.randrange(n)
                r = rng.randrange(l, n)
                assert bit.query(l, r) == sum(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Build O(n); `add`, `prefix_sum` and `query` are O(log n) each; space O(n).

A Fenwick tree only understands **changes** ("add 2"). To overwrite `a[i]` with `v`, keep a copy of the values and call `add(i, v − values[i])`.

## 8. Range add, point query: one Fenwick tree on differences

### The problem

Now updates are on **ranges**: "add `delta` to every element in `[l, r]`". Queries ask for **one** current value: "what is `a[i]` now?". Requests interleave.

[Chapter 1 §5](01-prefix-sums.md#5-difference-arrays-many-range-updates-one-final-read) solved the batch version with a difference array `d`: a range add is two point changes to `d`, and a value is a prefix sum of `d`. Reading needed O(n) because `d`'s prefix sums were recomputed from scratch. Put `d` in a Fenwick tree and both become O(log n):

| Request on `a` | Becomes, on the Fenwick tree of `d` |
|---|---|
| `range_add(l, r, delta)` | `add(l, +delta)` and, if `r + 1 < n`, `add(r + 1, −delta)` |
| `point_query(i)` | `prefix_sum(i + 1)` = `d[0] + … + d[i]` |

### Trace

`a = [1, 2, 3, 4, 5]`, so `d = [1, 1, 1, 1, 1]` (each value minus its left neighbor, with `d[0] = a[0]`).

| Request | Changes to `d` | `d` after | Answer |
|---|---|---|---|
| start | — | `[1, 1, 1, 1, 1]` | — |
| `range_add(1, 3, +3)` | `d[1] += 3`, `d[4] −= 3` | `[1, 4, 1, 1, −2]` | — |
| `point_query(2)` | — | — | `1 + 4 + 1 = 6` |
| `range_add(0, 4, −1)` | `d[0] −= 1`; `r + 1 = 5` is past the end | `[0, 4, 1, 1, −2]` | — |
| `point_query(4)` | — | — | `0 + 4 + 1 + 1 − 2 = 4` |

Check: `a` became `[1, 5, 6, 7, 5]` and then `[0, 4, 5, 6, 4]`. ✓

The code for this structure is in the combined script of §9.

## 9. Range add, range sum: two Fenwick trees

### The problem

Updates are on ranges and queries are on ranges. We need `sum(a[0..k−1])` while `a` is stored only through its differences `d`.

### Deriving the formula

Use positions `1..x` for the first `x` elements. Every value is a prefix of differences, `a[i] = d[1] + … + d[i]`. Write the prefix of `a` out as a triangle, for `x = 4`:

```text
a[1] = d[1]
a[2] = d[1] + d[2]
a[3] = d[1] + d[2] + d[3]
a[4] = d[1] + d[2] + d[3] + d[4]
       ----   ----   ----   ----
        ×4     ×3     ×2     ×1
```

`d[j]` appears in every row from `j` down to `x`, which is `x − j + 1` rows. So:

$$
\begin{aligned}
\operatorname{prefixA}(x)
&= \sum_{j=1}^{x} (x - j + 1)\, d[j] \\
&= (x + 1) \sum_{j=1}^{x} d[j] \;-\; \sum_{j=1}^{x} j\, d[j].
\end{aligned}
$$

The first sum is a prefix of `d`; the second is a prefix of `j · d[j]`. Both are ordinary prefix sums, so keep two Fenwick trees:

- `B1` stores `d[j]`.
- `B2` stores `j · d[j]`.

$$
\operatorname{prefixA}(x) = (x + 1)\cdot B_1.\operatorname{prefix}(x) - B_2.\operatorname{prefix}(x).
$$

A range add on positions `L..R` changes `d[L]` by `+Δ` and `d[R + 1]` by `−Δ`. In `B2` the same changes are multiplied by their own position:

| Position | Change to `B1` | Change to `B2` |
|---|---:|---:|
| `L` | `+Δ` | `+L · Δ` |
| `R + 1` (only if `≤ n`) | `−Δ` | `−(R + 1) · Δ` |

### Trace

`a = [0, 0, 0, 0, 0]`, then `range_add` of `+3` on 0-based `[1, 3]`, which is positions `L = 2`, `R = 4`.

| Position `j` | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| `d[j]` (in `B1`) | 0 | 3 | 0 | 0 | −3 |
| `j · d[j]` (in `B2`) | 0 | 6 | 0 | 0 | −15 |

| `x` | `B1.prefix(x)` | `B2.prefix(x)` | `(x + 1)·B1 − B2` | Check: `a` is `[0, 3, 3, 3, 0]` |
|---:|---:|---:|---:|---|
| 1 | 0 | 0 | 0 | `0` |
| 2 | 3 | 6 | `3·3 − 6 = 3` | `0 + 3` |
| 4 | 3 | 6 | `5·3 − 6 = 9` | `0 + 3 + 3 + 3` |
| 5 | 0 | −9 | `6·0 + 9 = 9` | the whole array |

No special case is needed past the end of the updated range: the `−Δ` at position 5 cancels in `B1`, and `B2` carries the correction.

### Code

```python
from random import Random


class Fenwick:
    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.tree = [0] + list(nums)
        for p in range(1, self.n + 1):
            parent = p + (p & -p)
            if parent <= self.n:
                self.tree[parent] += self.tree[p]

    def add(self, i: int, delta: int) -> None:
        p = i + 1
        while p <= self.n:
            self.tree[p] += delta
            p += p & -p

    def prefix_sum(self, k: int) -> int:
        total = 0
        while k > 0:
            total += self.tree[k]
            k -= k & -k
        return total


def differences(nums: list[int]) -> list[int]:
    return [x - (nums[i - 1] if i else 0) for i, x in enumerate(nums)]


class RangeAddPointQuery:
    """range_add on [l, r] and point_query(i); 0-based, inclusive."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.bit = Fenwick(differences(nums))

    def range_add(self, l: int, r: int, delta: int) -> None:
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")
        self.bit.add(l, delta)
        if r + 1 < self.n:
            self.bit.add(r + 1, -delta)

    def point_query(self, i: int) -> int:
        if not 0 <= i < self.n:
            raise ValueError(f"index {i} out of range")
        return self.bit.prefix_sum(i + 1)


class RangeAddRangeSum:
    """range_add on [l, r] and query(l, r); 0-based, inclusive."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        d = differences(nums)
        self.b1 = Fenwick(d)                                   # d[j]
        self.b2 = Fenwick([(i + 1) * x for i, x in enumerate(d)])  # j * d[j]

    def _add_diff(self, i: int, delta: int) -> None:
        self.b1.add(i, delta)
        self.b2.add(i, (i + 1) * delta)      # position j = i + 1

    def range_add(self, l: int, r: int, delta: int) -> None:
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")
        self._add_diff(l, delta)
        if r + 1 < self.n:
            self._add_diff(r + 1, -delta)

    def prefix_sum(self, k: int) -> int:
        """Sum of the first k elements."""
        if not 0 <= k <= self.n:
            raise ValueError(f"prefix length {k} out of range")
        return (k + 1) * self.b1.prefix_sum(k) - self.b2.prefix_sum(k)

    def query(self, l: int, r: int) -> int:
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")
        return self.prefix_sum(r + 1) - self.prefix_sum(l)


def main():
    rp = RangeAddPointQuery([1, 2, 3, 4, 5])                # §8 trace
    rp.range_add(1, 3, 3)
    assert rp.point_query(2) == 6
    rp.range_add(0, 4, -1)
    assert [rp.point_query(i) for i in range(5)] == [0, 4, 5, 6, 4]

    rr = RangeAddRangeSum([0, 0, 0, 0, 0])                  # §9 trace
    rr.range_add(1, 3, 3)
    assert [rr.prefix_sum(x) for x in range(6)] == [0, 0, 3, 6, 9, 9]
    assert rr.query(1, 3) == 9

    rng = Random(12)
    for _ in range(300):
        n = rng.randint(1, 15)
        a = [rng.randint(-5, 5) for _ in range(n)]
        rp, rr = RangeAddPointQuery(a), RangeAddRangeSum(a)
        for _ in range(25):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            if rng.random() < 0.5:
                delta = rng.randint(-4, 4)
                for i in range(l, r + 1):
                    a[i] += delta
                rp.range_add(l, r, delta)
                rr.range_add(l, r, delta)
            else:
                assert rr.query(l, r) == sum(a[l:r + 1])
                assert rp.point_query(l) == a[l]


if __name__ == "__main__":
    main()
```

Both structures build in O(n) and answer every request in O(log n): `RangeAddPointQuery` uses 2 Fenwick adds per update; `RangeAddRangeSum` uses 4 adds per update and 4 prefixes per query, with two trees of O(n) space.

A pitfall: `B2` must receive the **change** in `j · d[j]`, which is `j · Δ`, not a recomputed total.

## 10. Counting with a Fenwick tree: how many smaller elements?

A Fenwick tree over **values** instead of positions turns into a dynamic counter: `tree` holds how many times each value has been seen, and a prefix sum answers "how many seen values are below `v`?".

### The problem

For each element, count how many elements **to its right** are strictly smaller. For `[5, 2, 6, 1]` the answer is `[2, 1, 1, 0]`: right of 5 are 2 and 1; right of 2 is 1; right of 6 is 1; nothing is right of 1.

**Brute force.** For each `i`, scan everything to its right: O(n²).

**Observation.** Scan from right to left. When we stand at `i`, the "elements to its right" are exactly those already scanned. Keep a count per value; the answer for `i` is the number of scanned values smaller than `nums[i]`, a prefix sum over values.

Values may be huge or negative, so first replace each value by its **rank** among the distinct sorted values (called **coordinate compression**): for `[5, 2, 6, 1]`, sorted distinct values are `[1, 2, 5, 6]`, so the ranks are 1 → 0, 2 → 1, 5 → 2, 6 → 3. The count array then needs only as many slots as there are distinct values.

### Trace

`counts` is indexed by rank; "smaller than rank `t`" is `prefix_sum(t)`.

| `i` | `nums[i]` | rank `t` | `prefix_sum(t)` = answer | `counts` after adding rank `t` |
|---:|---:|---:|---:|---|
| 3 | 1 | 0 | 0 | `[1, 0, 0, 0]` |
| 2 | 6 | 3 | `1 + 0 + 0 = 1` | `[1, 0, 0, 1]` |
| 1 | 2 | 1 | `1 = 1` | `[1, 1, 0, 1]` |
| 0 | 5 | 2 | `1 + 1 = 2` | `[1, 1, 1, 1]` |

Answer `[2, 1, 1, 0]`. Summing the answers gives the number of **inversions** (pairs `i < j` with `nums[i] > nums[j]`): here 4.

The code is `count_smaller_after` in the script of §11, which adds a k-th search to the same counting tree. Time O(n log n): sorting for ranks plus one add and one prefix per element. Space O(n).

**Variants.** "Count larger before" scans left to right and asks `seen_so_far − prefix_sum(t + 1)`. "Reverse pairs" (`nums[i] > 2 · nums[j]`) compresses the values `2 · nums[j]` as well and uses binary search to find the rank threshold. "Count of range sum" applies this counting to prefix sums from Chapter 1. [Offline Sweeps and Fenwick](../08-sweep-line/05-offline-sweeps-and-fenwick.md) uses the same pattern with sorted events.

## 11. Finding the k-th smallest: binary lifting

### The problem

Keep a **multiset** (a set that allows repeats) of small whole numbers `0..m−1` under insert and delete, and answer "what is the `k`-th smallest value?". For `{2, 3, 3, 5, 7, 8}` (values below 9), the 4th smallest is 5.

The counts per value form an array, and its prefix sums count how many stored values are `≤` each value. The `k`-th smallest is the smallest value whose prefix count reaches `k`. Counts are nonnegative, so these prefix counts never decrease, and we could binary-search over `prefix_sum`: O(log m) probes of O(log m) each, O(log² m).

### The observation: descend the tree directly

The Fenwick tree's blocks fit binary search perfectly. Build the answer position one bit at a time, from the highest power of two down:

- `pos` starts at 0; `remaining` starts at `k`.
- For `step` = largest power of two `≤ m`, then half of it, …, down to 1: if `pos + step ≤ m` and `tree[pos + step] < remaining`, then the whole block `[pos + 1, pos + step]` is too small to contain the answer. Skip it: `remaining −= tree[pos + step]`, `pos += step`.

**Why is `tree[pos + step]` exactly the block after `pos`?** `pos` is built from powers of two larger than `step`, so `lowbit(pos + step) = step`, and the block of `pos + step` is `[pos + 1, pos + step]`. No prefix query is needed.

At the end, `pos` is the largest position whose prefix count is `< k`, so the answer is position `pos + 1`, which is value `pos` in 0-based terms.

### Trace

Values `{2, 3, 3, 5, 7, 8}`, `m = 9` (values 0–8, positions 1–9). Counts by position:

```text
position     1   2   3   4   5   6   7   8   9
value        0   1   2   3   4   5   6   7   8
count        0   0   1   2   0   1   0   1   1
tree         0   0   1   3   0   1   0   5   1
```

Find `k = 4`:

| `step` | `pos + step` | `tree[pos + step]` | `< remaining`? | `pos` after | `remaining` after |
|---:|---:|---:|:---:|---:|---:|
| start | — | — | — | 0 | 4 |
| 8 | 8 | 5 (values 0–7) | no, `5 ≥ 4` | 0 | 4 |
| 4 | 4 | 3 (values 0–3) | yes | 4 | 1 |
| 2 | 6 | 1 (values 4–5) | no, `1 ≥ 1` | 4 | 1 |
| 1 | 5 | 0 (value 4) | yes | 5 | 1 |

Answer: value `pos = 5`. ✓ (The sorted multiset is 2, 3, 3, **5**, 7, 8.)

```python
from random import Random


class FenwickMultiset:
    """Multiset of integers in [0, m) with insert, remove, rank and k-th."""

    def __init__(self, m: int):
        self.m = m
        self.tree = [0] * (m + 1)
        self.size = 0
        self.top = 1 << (m.bit_length() - 1) if m else 0   # largest 2^j <= m

    def _add(self, value: int, delta: int) -> None:
        p = value + 1
        while p <= self.m:
            self.tree[p] += delta
            p += p & -p

    def count_less(self, value: int) -> int:
        """How many stored values are < value."""
        k, total = max(0, min(value, self.m)), 0
        while k > 0:
            total += self.tree[k]
            k -= k & -k
        return total

    def insert(self, value: int) -> None:
        if not 0 <= value < self.m:
            raise ValueError("value out of range")
        self._add(value, 1)
        self.size += 1

    def remove(self, value: int) -> None:
        if not 0 <= value < self.m:
            raise ValueError("value out of range")
        if self.count_less(value + 1) - self.count_less(value) == 0:
            raise ValueError("value not present")
        self._add(value, -1)
        self.size -= 1

    def kth(self, k: int) -> int:
        """k-th smallest stored value, k counted from 1."""
        if not 1 <= k <= self.size:
            raise ValueError("k out of range")
        pos, remaining, step = 0, k, self.top
        while step:
            nxt = pos + step
            if nxt <= self.m and self.tree[nxt] < remaining:
                pos = nxt
                remaining -= self.tree[nxt]
            step //= 2
        return pos          # position pos + 1 holds value pos


def count_smaller_after(nums: list[int]) -> list[int]:
    """§10: for each i, how many elements to its right are strictly smaller."""
    rank = {v: t for t, v in enumerate(sorted(set(nums)))}
    seen = FenwickMultiset(len(rank))
    answer = [0] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        t = rank[nums[i]]
        answer[i] = seen.count_less(t)    # ranks 0..t-1 are strictly smaller
        seen.insert(t)
    return answer


def main():
    assert count_smaller_after([5, 2, 6, 1]) == [2, 1, 1, 0]
    assert sum(count_smaller_after([5, 2, 6, 1])) == 4    # inversions
    assert count_smaller_after([]) == []
    assert count_smaller_after([-1, -1]) == [0, 0]         # equal is not smaller
    assert count_smaller_after([10**12, -10**12]) == [1, 0]

    ms = FenwickMultiset(9)
    for v in [2, 3, 3, 5, 7, 8]:
        ms.insert(v)
    assert ms.tree[1:] == [0, 0, 1, 3, 0, 1, 0, 5, 1]
    assert [ms.kth(k) for k in range(1, 7)] == [2, 3, 3, 5, 7, 8]
    assert ms.count_less(5) == 3
    ms.remove(3)
    assert [ms.kth(k) for k in range(1, 6)] == [2, 3, 5, 7, 8]
    for bad in [lambda: ms.kth(6), lambda: ms.remove(4), lambda: ms.insert(9)]:
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    rng = Random(14)
    for _ in range(300):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(0, 12))]
        assert count_smaller_after(nums) == [
            sum(nums[j] < nums[i] for j in range(i + 1, len(nums)))
            for i in range(len(nums))]
        m = rng.randint(1, 20)
        ms, ref = FenwickMultiset(m), []
        for _ in range(40):
            if ref and rng.random() < 0.3:
                v = rng.choice(ref)
                ref.remove(v)
                ms.remove(v)
            else:
                v = rng.randrange(m)
                ref.append(v)
                ms.insert(v)
            ref.sort()
            if ref:
                k = rng.randint(1, len(ref))
                assert ms.kth(k) == ref[k - 1]
            v = rng.randrange(m + 1)
            assert ms.count_less(v) == sum(x < v for x in ref)


if __name__ == "__main__":
    main()
```

Each operation is O(log m); space O(m). With coordinate compression, the same structure gives a running median, "the k-th smallest among values seen so far", or the order statistics needed by many sweep problems.

**Requirement.** The descent assumes every count is **nonnegative**, so the prefix counts never decrease. With negative entries, "skip the block if its total is too small" is no longer valid.

## 12. Two-dimensional Fenwick tree

**Problem.** A grid where single cells change and rectangle sums are queried, interleaved. Chapter 1's 2D table needs O(R · C) per change.

**Observation.** Apply the Fenwick idea in each dimension. `tree[x][y]` holds the sum over rows `(x − lowbit(x), x]` and columns `(y − lowbit(y), y]`. An update walks up in `x`, and for each `x` walks up in `y`. A prefix query walks down both. A rectangle sum then uses the four-corner inclusion–exclusion formula from [Chapter 1 §6](01-prefix-sums.md#6-two-dimensional-prefix-sums).

**Trace** of one update on a 4 × 4 grid: `add` at cell `(0, 2)` is position `(1, 3)`. The `x` chain is `1 → 2 → 4`; the `y` chain is `3 → 4`. So six entries change: `tree[1][3]`, `tree[1][4]`, `tree[2][3]`, `tree[2][4]`, `tree[4][3]`, `tree[4][4]`. Each of these blocks contains cell `(1, 3)`; no other does.

```python
from random import Random


class Fenwick2D:
    """Point add and inclusive rectangle sum on an R x C grid, 0-based API."""

    def __init__(self, rows: int, cols: int):
        self.rows, self.cols = rows, cols
        self.tree = [[0] * (cols + 1) for _ in range(rows + 1)]

    def add(self, r: int, c: int, delta: int) -> None:
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            raise ValueError("cell out of range")
        x = r + 1
        while x <= self.rows:
            y = c + 1
            while y <= self.cols:
                self.tree[x][y] += delta
                y += y & -y
            x += x & -x

    def prefix_sum(self, k_rows: int, k_cols: int) -> int:
        """Sum of the top-left block with k_rows rows and k_cols columns."""
        total = 0
        x = k_rows
        while x > 0:
            y = k_cols
            while y > 0:
                total += self.tree[x][y]
                y -= y & -y
            x -= x & -x
        return total

    def query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise ValueError("bad rectangle")
        s = self.prefix_sum
        return s(r2 + 1, c2 + 1) - s(r1, c2 + 1) - s(r2 + 1, c1) + s(r1, c1)


def main():
    f = Fenwick2D(4, 4)
    f.add(0, 2, 5)
    changed = {(x, y) for x in range(5) for y in range(5) if f.tree[x][y]}
    assert changed == {(1, 3), (1, 4), (2, 3), (2, 4), (4, 3), (4, 4)}
    assert f.query(0, 0, 3, 3) == 5
    assert f.query(1, 0, 3, 3) == 0

    rng = Random(15)
    for _ in range(200):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        f, g = Fenwick2D(rows, cols), [[0] * cols for _ in range(rows)]
        for _ in range(30):
            r, c = rng.randrange(rows), rng.randrange(cols)
            delta = rng.randint(-5, 5)
            g[r][c] += delta
            f.add(r, c, delta)
            r1 = rng.randrange(rows)
            r2 = rng.randrange(r1, rows)
            c1 = rng.randrange(cols)
            c2 = rng.randrange(c1, cols)
            expected = sum(g[i][j] for i in range(r1, r2 + 1)
                           for j in range(c1, c2 + 1))
            assert f.query(r1, c1, r2, c2) == expected


if __name__ == "__main__":
    main()
```

Each update and each prefix query is O(log R · log C). Space O(R · C). When the grid is huge but only `q` points matter, compress the coordinates first, or answer the queries offline with a sweep over one dimension and a 1D Fenwick tree over the other.

## 13. Beyond sums: prefix maximum when values only grow

A Fenwick tree needs to **undo** a prefix for a range query: `query(l, r)` subtracts `prefix(l)`. Maximum cannot be undone ([Chapter 1 §9](01-prefix-sums.md#9-what-prefix-sums-cannot-do)). But a **prefix** maximum, "largest value among positions `1..k`", needs no undoing. It works if every update only **raises** a value, because then each stored block maximum can be updated by taking `max` with the new value.

This is the shape of many DP speedups, such as the longest increasing subsequence: process elements in order, and for each one ask "best answer among smaller values so far?", then record a new, never-decreasing answer ([Faster Transitions](../09-dynamic-programming/12-faster-transitions.md)).

```python
from random import Random


class PrefixMaxFenwick:
    """raise_to(i, v): a[i] = max(a[i], v). prefix_max(k): max of a[:k]."""

    def __init__(self, n: int):
        self.n = n
        self.tree = [float("-inf")] * (n + 1)

    def raise_to(self, i: int, value) -> None:
        if not 0 <= i < self.n:
            raise ValueError("index out of range")
        p = i + 1
        while p <= self.n:
            if value > self.tree[p]:
                self.tree[p] = value
            p += p & -p

    def prefix_max(self, k: int):
        best = float("-inf")
        while k > 0:
            best = max(best, self.tree[k])
            k -= k & -k
        return best


def lis_length(nums: list[int]) -> int:
    """Longest strictly increasing subsequence in O(n log n)."""
    rank = {v: t for t, v in enumerate(sorted(set(nums)))}
    best = PrefixMaxFenwick(len(rank))
    answer = 0
    for x in nums:
        t = rank[x]
        length = max(0, best.prefix_max(t)) + 1   # ranks < t are smaller values
        best.raise_to(t, length)
        answer = max(answer, length)
    return answer


def lis_brute(nums):
    best = [1] * len(nums)
    for j in range(len(nums)):
        for i in range(j):
            if nums[i] < nums[j]:
                best[j] = max(best[j], best[i] + 1)
    return max(best, default=0)


def main():
    assert lis_length([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert lis_length([]) == 0
    assert lis_length([7, 7, 7]) == 1
    rng = Random(16)
    for _ in range(300):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(0, 12))]
        assert lis_length(nums) == lis_brute(nums)
    f = PrefixMaxFenwick(4)
    f.raise_to(2, 9)
    assert f.prefix_max(2) == float("-inf") and f.prefix_max(3) == 9


if __name__ == "__main__":
    main()
```

O(log n) per operation. If a value can **decrease**, or if you need the maximum of an arbitrary range `[l, r]`, use a [Segment Tree](03-segment-tree.md).

## 14. Summary

Every Fenwick tree is the same two loops over positions `1..n`; only what is stored changes.

```text
add at position p:      while p <= n: tree[p] += delta; p += p & -p     # walk up the parents
prefix of length k:     while k > 0:  total += tree[k];  k -= k & -k    # walk left over blocks
range [l, r] (0-based): prefix(r + 1) - prefix(l)
```

| Variant | What the tree stores | Update | Query |
|---|---|---|---|
| Point add, range sum (§7) | `a` | `add(i, Δ)` | `prefix(r + 1) − prefix(l)` |
| Range add, point query (§8) | differences `d` | `add(l, Δ)`, `add(r + 1, −Δ)` | `prefix(i + 1)` |
| Range add, range sum (§9) | `d` and `j · d[j]` | two adds in each tree | `(x + 1)·B1(x) − B2(x)` |
| Counting smaller elements (§10) | count per value rank | `add(rank, 1)` | `prefix(rank)` |
| k-th smallest (§11) | count per value | `add(v, ±1)` | descend by powers of two |
| 2D (§12) | block sums in both dimensions | nested walk up | four corners |
| Prefix max (§13) | block maxima, values only grow | `max` on the way up | `max` on the way left |

Every operation is O(log n) (O(log R · log C) in 2D), the build is O(n), and the space is one array of `n + 1`. When a summary cannot be undone, or a range must be arbitrary for min or max, use a [Segment Tree](03-segment-tree.md).

## 15. Pitfalls and practice

1. Running the update loop from position 0. `lowbit(0) = 0`, so the loop never ends. Convert 0-based indices with `+ 1` and validate first.
2. Mixing 0-based and 1-based. Decide once: here, the API is 0-based, `prefix_sum(k)` means "first `k` elements", and positions are 1-based only inside the loops.
3. Using `prefix(r) − prefix(l − 1)` with a "first `k` elements" prefix. With this chapter's convention, the inclusive range `[l, r]` is `prefix_sum(r + 1) − prefix_sum(l)`.
4. Treating `add` as `set`. A Fenwick tree stores sums of changes; to overwrite, add `new − old`.
5. Forgetting the `r + 1` cancellation in range updates, or weighting both `B2` updates by `l` instead of `l` and `r + 1`.
6. Building in decreasing order in the O(n) build.
7. Using binary lifting for the k-th element when some counts can be negative.
8. Expecting a range minimum or maximum. Only prefix max with growing values works; general ranges need a [Segment Tree](03-segment-tree.md).

Practice: range sum query (mutable); count of smaller numbers after self; reverse pairs; count of range sum; create sorted array through instructions; queue reconstruction by height (k-th empty slot); number of longest increasing subsequence (pairs of length and count); range sum query 2D (mutable); sliding window median with a Fenwick multiset.

Next: [Segment Tree](03-segment-tree.md).
