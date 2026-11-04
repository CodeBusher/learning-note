# Sparse Table and Square-Root Decomposition — Trading Generality for Simplicity

## 1. The problem: many range-minimum queries on a fixed array

A fixed array, and a very large number of questions "what is the minimum of `a[l..r]`?". No updates ever happen.

```text
i        0   1   2   3   4   5   6   7
a[i]     5   8   6   3   2   7   2   6
```

The minimum of `a[1..6]` is 2; of `a[0..3]`, 3.

**Options so far.**

| Method | Build | Per query | Problem |
|---|---:|---:|---|
| Scan the range | — | O(n) | too slow for many queries |
| Table of every `[l, r]` | O(n²) | O(1) | `n = 10⁵` needs `5 · 10⁹` entries |
| [Segment tree](03-segment-tree.md) | O(n) | O(log n) | fine, but with 10⁷ queries the log factor hurts |
| Prefix minima | O(n) | — | cannot be undone ([Chapter 1 §9](01-prefix-sums.md#9-what-prefix-sums-cannot-do)) |

We want O(1) per query with far less than O(n²) memory.

## 2. The observation: for minimum, overlapping pieces are harmless

A sum must be built from **disjoint** pieces; counting an element twice changes the sum. A minimum does not care: `min(x, x) = x`. So the minimum of a range can be taken over two pieces that **overlap**, as long as together they cover the range and stay inside it.

An operation with `f(x, x) = x` is called **idempotent**. Minimum, maximum, GCD, bitwise AND and bitwise OR are idempotent; sum, product and XOR are not.

Now store only windows whose length is a power of two: for every start `i` and every `j`, the minimum of the `2^j` elements starting at `i`. Any range of length `len` is covered by **two** such windows of the same length `2^k`, where `2^k` is the largest power of two `≤ len`: one starting at `l`, one ending at `r`. Since `2^k > len / 2`, the two windows together reach across the whole range.

```text
query [1, 6], length 6, so 2^k = 4
i            0   1   2   3   4   5   6   7
a            5   8   6   3   2   7   2   6
window 1        [8   6   3   2]               min 2, starts at l = 1
window 2                [3   2   7   2]       min 2, ends at r = 6
overlap                 [3   2]               counted twice, harmless
```

**Invariant.** `sp[j][i]` is the minimum of `a[i .. i + 2^j − 1]`.

There are about `log₂ n` values of `j` and up to `n` starts each, so the table has O(n log n) entries. For `n = 10⁵` that is about 1.7 million, not 5 billion. The name **sparse table** comes from keeping only this sparse subset of all ranges.

## 3. Building the table, traced

Row `j = 0` is the array itself. Each longer window is two half-length windows side by side:

$$
sp[j][i] = \min\bigl(sp[j-1][i],\; sp[j-1][i + 2^{j-1}]\bigr).
$$

```text
         i:    0   1   2   3   4   5   6   7
j=0 (len 1)    5   8   6   3   2   7   2   6
j=1 (len 2)    5   6   3   2   2   2   2
j=2 (len 4)    3   2   2   2   2
j=3 (len 8)    2
```

For example `sp[2][1]`, the minimum of `a[1..4]`, is `min(sp[1][1], sp[1][3]) = min(6, 2) = 2`.

Row `j` has `n − 2^j + 1` entries, because a window of length `2^j` must fit inside the array.

## 4. Query, traced

For `[l, r]`: `len = r − l + 1`, `k = ⌊log₂ len⌋`, and the answer is

$$
\min\bigl(sp[k][l],\; sp[k][r - 2^k + 1]\bigr).
$$

| Query | `len` | `k` | Window from `l` | Window ending at `r` | Answer |
|---|---:|---:|---|---|---:|
| `[1, 3]` | 3 | 1 | `sp[1][1]` = `a[1..2]` → 6 | `sp[1][2]` = `a[2..3]` → 3 | 3 |
| `[1, 6]` | 6 | 2 | `sp[2][1]` = `a[1..4]` → 2 | `sp[2][3]` = `a[3..6]` → 2 | 2 |
| `[0, 3]` | 4 | 2 | `sp[2][0]` = `a[0..3]` → 3 | `sp[2][0]` = `a[0..3]` → 3 | 3 |
| `[5, 5]` | 1 | 0 | `sp[0][5]` → 7 | `sp[0][5]` → 7 | 7 |

When the length is a power of two, the two windows are the same window. In Python, `k = len.bit_length() − 1`.

## 5. Code: `SparseTable`

The class accepts any idempotent `combine`, so the same code serves min, max, GCD, AND and OR.

```python
from functools import reduce
from math import gcd
from random import Random
from typing import Any, Callable


class SparseTable:
    """O(1) inclusive range queries for an idempotent combine; no updates."""

    def __init__(self, nums: list, combine: Callable[[Any, Any], Any] = min):
        self.n = len(nums)
        self.combine = combine
        self.sp = [list(nums)]                     # sp[j][i] covers 2**j items
        j = 1
        while (1 << j) <= self.n:
            prev, half = self.sp[j - 1], 1 << (j - 1)
            self.sp.append([combine(prev[i], prev[i + half])
                            for i in range(self.n - (1 << j) + 1)])
            j += 1

    def query(self, l: int, r: int) -> Any:
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")
        k = (r - l + 1).bit_length() - 1           # largest 2**k <= length
        return self.combine(self.sp[k][l], self.sp[k][r - (1 << k) + 1])


def main():
    st = SparseTable([5, 8, 6, 3, 2, 7, 2, 6])
    assert st.sp[1] == [5, 6, 3, 2, 2, 2, 2]       # §3 trace
    assert st.sp[2] == [3, 2, 2, 2, 2]
    assert st.sp[3] == [2]
    assert st.query(1, 3) == 3 and st.query(1, 6) == 2   # §4 trace
    assert st.query(0, 3) == 3 and st.query(5, 5) == 7
    try:
        st.query(3, 8)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = Random(31)
    ops = [(min, min), (max, max), (gcd, lambda s: reduce(gcd, s)),
           (lambda x, y: x & y, lambda s: reduce(lambda x, y: x & y, s)),
           (lambda x, y: x | y, lambda s: reduce(lambda x, y: x | y, s))]
    for _ in range(300):
        n = rng.randint(1, 20)
        a = [rng.randint(0, 31) for _ in range(n)]
        for combine, brute in ops:
            st = SparseTable(a, combine)
            for _ in range(10):
                l = rng.randrange(n)
                r = rng.randrange(l, n)
                assert st.query(l, r) == brute(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Build O(n log n) time and space; each `query` is **O(1)**. Updates are not supported: one change can affect O(n log n) entries.

## 6. Why it's correct, and where it stops working

**Build.** A window of length `2^j` starting at `i` splits exactly into the window of length `2^(j−1)` at `i` and the one at `i + 2^(j−1)`. By induction on `j`, every entry is the minimum of its window.

**Query.** With `2^k ≤ len < 2^(k+1)`, the window `[l, l + 2^k − 1]` starts at `l` and stays inside the range; the window `[r − 2^k + 1, r]` ends at `r` and stays inside. Their union is all of `[l, r]` because `2 · 2^k > len`, so they meet or overlap. Every element of the range is in at least one window, and nothing outside is in either. Because `min` is idempotent, elements counted twice do not change the result.

**Non-idempotent operations.** For a sum, the overlap would be counted twice. A sparse table can still answer sums by splitting the range into **disjoint** power-of-two windows, one per `1` bit of the length (the [Fenwick](02-fenwick-tree.md#2-the-observation-store-sums-of-a-few-well-chosen-blocks) idea), but that costs O(log n) per query, so a prefix sum or Fenwick tree is better.

**Where it shines.** Many queries on a fixed array: lowest common ancestor via an Euler tour ([Rooting and LCA](../10-graphs/05-trees-and-advanced/01-rooting-and-lca.md)), longest common prefix of suffixes, and range GCD.

## 7. Square-root decomposition: blocks of size √n

### The problem

Range add and range queries (sum and minimum), interleaved. A [lazy segment tree](03-segment-tree.md#10-lazy-propagation-range-add-range-sum) solves it, but it takes care to write. Is there something simpler that is still much faster than O(n) per request?

### The observation: two levels instead of log n levels

Cut the array into blocks of size `B`. Keep one summary per block. Any range `[l, r]` then consists of:

- a **partial block** at the left end (at most `B − 1` elements, handled one by one),
- some **full blocks** in the middle (at most `n / B` of them, handled by their summaries),
- a partial block at the right end.

Work per request is about `2B + n / B`. That is smallest when `B ≈ √n`, giving O(√n). For `n = 10⁵`, that is about 600 steps instead of 100,000.

For range **add**, a full block gets a block-level tag (like a one-level lazy tag), and partial blocks are updated element by element and their summaries recomputed.

**State per block `b`:** `add[b]` is an amount added to every element of the block but not yet written into the elements; `total[b]` and `low[b]` are the sum and minimum of the elements **without** `add[b]`. So the true sum of block `b` is `total[b] + add[b] · size`, and its true minimum is `low[b] + add[b]`.

### Trace

`a = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]`, `n = 10`, `B = 3` (`√10 ≈ 3.2`, rounded down), so the blocks are `[0..2]`, `[3..5]`, `[6..8]`, `[9]`.

```text
i        0  1  2 | 3  4  5 | 6  7  8 | 9
a        3  1  4 | 1  5  9 | 2  6  5 | 3
block       0    |    1    |    2    | 3
total       8    |   15    |   13    | 3
low         1    |    1    |    2    | 3
```

**`query_sum(2, 8)`:**

| Part | Indices | How | Contribution |
|---|---|---|---:|
| left partial (block 0) | 2 | element by element | 4 |
| full block 1 | 3–5 | `total[1] + add[1]·3 = 15 + 0` | 15 |
| full block 2 | 6–8 | `total[2] + add[2]·3 = 13 + 0` | 13 |
| | | | **32** |

Check: `4 + 1 + 5 + 9 + 2 + 6 + 5 = 32`. ✓

**`range_add(1, 6, +10)`:**

| Part | Indices | Action | Block state after |
|---|---|---|---|
| left partial (block 0) | 1, 2 | `a[1] = 11`, `a[2] = 14`; recompute | `total[0] = 28`, `low[0] = 3` |
| full block 1 | 3–5 | `add[1] += 10` | `total[1] = 15`, `low[1] = 1`, `add[1] = 10` |
| right partial (block 2) | 6 | `a[6] = 12`; recompute | `total[2] = 23`, `low[2] = 5` |

Then `query_min(3, 7)`: block 1 is full, `low[1] + add[1] = 1 + 10 = 11`; index 6 gives `12 + add[2] = 12`; index 7 gives `6`. Answer 6. ✓ (The true array is `[3, 11, 14, 11, 15, 19, 12, 6, 5, 3]`.)

```python
from math import inf, isqrt
from random import Random


class SqrtBlocks:
    """range_add, range sum and range min; 0-based, inclusive."""

    def __init__(self, nums: list[int], block: int | None = None):
        self.n = len(nums)
        self.B = block or max(1, isqrt(self.n))     # about sqrt(n), at least 1
        self.a = list(nums)
        count = (self.n + self.B - 1) // self.B
        self.add = [0] * count
        self.total = [0] * count
        self.low = [inf] * count
        for b in range(count):
            self._rebuild(b)

    def _span(self, b: int) -> range:
        return range(b * self.B, min(self.n, (b + 1) * self.B))

    def _rebuild(self, b: int) -> None:
        part = [self.a[i] for i in self._span(b)]
        self.total[b], self.low[b] = sum(part), min(part)

    def _check(self, l: int, r: int) -> None:
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}]")

    def range_add(self, l: int, r: int, delta: int) -> None:
        self._check(l, r)
        bl, br = l // self.B, r // self.B
        if bl == br:                                  # inside one block
            for i in range(l, r + 1):
                self.a[i] += delta
            self._rebuild(bl)
            return
        for i in range(l, (bl + 1) * self.B):         # left partial block
            self.a[i] += delta
        self._rebuild(bl)
        for b in range(bl + 1, br):                   # full blocks: tag only
            self.add[b] += delta
        for i in range(br * self.B, r + 1):           # right partial block
            self.a[i] += delta
        self._rebuild(br)

    def _scan(self, l: int, r: int):
        """Yield (sum, min) for the pieces that cover [l, r]."""
        bl, br = l // self.B, r // self.B
        if bl == br:
            vals = [self.a[i] + self.add[bl] for i in range(l, r + 1)]
            yield sum(vals), min(vals)
            return
        left = [self.a[i] + self.add[bl] for i in range(l, (bl + 1) * self.B)]
        yield sum(left), min(left)
        for b in range(bl + 1, br):
            yield self.total[b] + self.add[b] * len(self._span(b)), self.low[b] + self.add[b]
        right = [self.a[i] + self.add[br] for i in range(br * self.B, r + 1)]
        yield sum(right), min(right)

    def query_sum(self, l: int, r: int) -> int:
        self._check(l, r)
        return sum(s for s, _ in self._scan(l, r))

    def query_min(self, l: int, r: int) -> int:
        self._check(l, r)
        return min(m for _, m in self._scan(l, r))


def main():
    sb = SqrtBlocks([3, 1, 4, 1, 5, 9, 2, 6, 5, 3])   # §7 trace
    assert sb.B == 3
    assert sb.total == [8, 15, 13, 3] and sb.low == [1, 1, 2, 3]
    assert sb.query_sum(2, 8) == 32
    sb.range_add(1, 6, 10)
    assert sb.total == [28, 15, 23, 3] and sb.add == [0, 10, 0, 0]
    assert sb.query_min(3, 7) == 6
    assert sb.query_sum(0, 9) == 99

    rng = Random(32)
    for _ in range(300):
        n = rng.randint(1, 30)
        a = [rng.randint(-9, 9) for _ in range(n)]
        sb = SqrtBlocks(a, block=rng.choice([None, 1, 2, 5]))
        for _ in range(30):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            if rng.random() < 0.4:
                d = rng.randint(-5, 5)
                for i in range(l, r + 1):
                    a[i] += d
                sb.range_add(l, r, d)
            else:
                assert sb.query_sum(l, r) == sum(a[l:r + 1])
                assert sb.query_min(l, r) == min(a[l:r + 1])


if __name__ == "__main__":
    main()
```

With `B ≈ √n`: build O(n); each `range_add`, `query_sum` and `query_min` is O(√n). Space O(n).

**When to prefer blocks over a tree.** When the per-block summary is easy to rebuild but hard to merge or tag lazily. Classic examples: "count of values `≥ x` in `[l, r]` with point updates" (keep each block sorted and binary-search it, O(√n log n)), and operations such as "reverse a range" or "move a range" done by rebuilding blocks periodically.

## 8. Mo's algorithm: reorder offline queries

### The problem

A fixed array and many queries "how many **distinct** values are in `a[l..r]`?". All queries are known in advance, so they may be answered in any order (**offline**).

```text
i        0  1  2  3  4  5  6  7
a        1  2  1  3  2  2  4  1
```

| Query | Elements | Distinct |
|---|---|---:|
| `[0, 3]` | 1 2 1 3 | 3 |
| `[2, 5]` | 1 3 2 2 | 3 |
| `[1, 6]` | 2 1 3 2 2 4 | 4 |
| `[5, 7]` | 2 4 1 | 3 |

A segment tree does not fit: the distinct values of two halves cannot be merged from two counts (the halves may share values). But a **window** that grows or shrinks by one element is easy to maintain: keep `count[v]` for each value and a running `distinct`. Adding `v` raises `distinct` when `count[v]` goes from 0 to 1; removing it lowers `distinct` when `count[v]` returns to 0. This is the same bookkeeping as a [frequency window](../05-sliding-window/README.md).

**Brute force.** Answer queries in the given order by moving the window's ends. The ends can jump back and forth across the whole array: O(n) per query, O(n · q) total.

### The observation: sort queries so the ends move little

Cut the indices into blocks of size `B`. Sort queries by **the block of `l`**, and within the same block by `r`. Then:

- Inside one block of `l`, `r` only moves to the right: at most `n` steps per block, `n / B` blocks, `n² / B` in total.
- `l` stays within one block (or moves to the next), so it moves at most about `B` per query: `q · B` in total.

The total, `n² / B + q · B`, is smallest at `B ≈ n / √q`; with `q ≈ n` that is `B ≈ √n`, and the total is O((n + q) √n). For `n = q = 10⁵`, about `6 · 10⁷` window moves instead of `10¹⁰`.

**State.** `cur_l`, `cur_r` describe the current window `a[cur_l..cur_r]`; `count` and `distinct` describe its contents.

### Trace

`B = 3`. The block of `l` is `l // 3`: the queries `[0, 3]`, `[2, 5]`, `[1, 6]` are in block 0 and `[5, 7]` is in block 1. Sorted order: `[0, 3]`, `[2, 5]`, `[1, 6]`, `[5, 7]` (block 0 sorted by `r`, then block 1).

The window starts empty, `cur_l = 0`, `cur_r = −1`. For each query, first extend the window (move `cur_l` left, then `cur_r` right), then shrink it (move `cur_l` right, then `cur_r` left). Extending first keeps the window valid.

| Query | Moves | Window after | `distinct` |
|---|---|---|---:|
| `[0, 3]` | add `a[0..3]` = 1, 2, 1, 3 | `[0, 3]` | 3 |
| `[2, 5]` | add `a[4]` = 2, `a[5]` = 2; remove `a[0]` = 1, `a[1]` = 2 | `[2, 5]` | 3 |
| `[1, 6]` | add `a[1]` = 2; add `a[6]` = 4 (new) | `[1, 6]` | 4 |
| `[5, 7]` | add `a[7]` = 1; remove `a[1]` = 2, `a[2]` = 1, `a[3]` = 3 (gone), `a[4]` = 2 | `[5, 7]` | 3 |

Answers are stored at each query's **original** position, then returned in the original order.

```python
from math import isqrt
from random import Random


def distinct_in_ranges(a: list[int], queries: list[tuple[int, int]],
                       block: int | None = None) -> list[int]:
    """Mo's algorithm: number of distinct values in each a[l..r], offline."""
    n = len(a)
    for l, r in queries:
        if not 0 <= l <= r < n:
            raise ValueError(f"bad range [{l}, {r}]")
    if not queries:
        return []
    B = block or max(1, n // max(1, isqrt(len(queries))))
    order = sorted(range(len(queries)),
                   key=lambda k: (queries[k][0] // B, queries[k][1]))

    count: dict[int, int] = {}
    distinct = 0

    def add(i: int) -> None:
        nonlocal distinct
        count[a[i]] = count.get(a[i], 0) + 1
        if count[a[i]] == 1:
            distinct += 1

    def remove(i: int) -> None:
        nonlocal distinct
        count[a[i]] -= 1
        if count[a[i]] == 0:
            distinct -= 1

    answers = [0] * len(queries)
    cur_l, cur_r = 0, -1                       # empty window
    for k in order:
        l, r = queries[k]
        while cur_l > l:                       # extend first...
            cur_l -= 1
            add(cur_l)
        while cur_r < r:
            cur_r += 1
            add(cur_r)
        while cur_l < l:                       # ...then shrink
            remove(cur_l)
            cur_l += 1
        while cur_r > r:
            remove(cur_r)
            cur_r -= 1
        answers[k] = distinct
    return answers


def main():
    a = [1, 2, 1, 3, 2, 2, 4, 1]
    qs = [(5, 7), (0, 3), (1, 6), (2, 5)]       # given out of order
    assert distinct_in_ranges(a, qs, block=3) == [3, 3, 4, 3]
    assert distinct_in_ranges(a, []) == []
    assert distinct_in_ranges([7], [(0, 0), (0, 0)]) == [1, 1]

    rng = Random(33)
    for _ in range(300):
        n = rng.randint(1, 20)
        a = [rng.randint(0, 5) for _ in range(n)]
        qs = []
        for _ in range(rng.randint(0, 15)):
            l = rng.randrange(n)
            qs.append((l, rng.randrange(l, n)))
        expected = [len(set(a[l:r + 1])) for l, r in qs]
        assert distinct_in_ranges(a, qs) == expected
        assert distinct_in_ranges(a, qs, block=1) == expected


if __name__ == "__main__":
    main()
```

Time O((n + q) √n) window moves plus O(q log q) for sorting; space O(n + q).

**Requirements and variants.**

- Queries must be **offline**: all known before answering. If each query depends on the previous answer, Mo's algorithm does not apply.
- `add` and `remove` must be cheap (O(1) here). Any statistic that a frequency window maintains works: distinct count, number of pairs of equal values (`Σ count·(count − 1)/2`), the most frequent count (with a second array of "how many values have each count").
- A common speedup: in odd-numbered blocks sort by `r` descending, so `r` sweeps back instead of jumping to the left.
- Extensions exist for point updates (**Mo with updates**, adding time as a third coordinate) and for paths in trees, both advanced.

## 9. Summary: choosing a structure

| Situation | Tool | Per-query cost |
|---|---|---:|
| Static, sum / count / XOR | [Prefix sums](01-prefix-sums.md) | O(1) |
| Static, min / max / GCD, very many queries | Sparse table (§5) | O(1) |
| Point updates, sum | [Fenwick tree](02-fenwick-tree.md) | O(log n) |
| Point or range updates, any mergeable summary | [Segment tree](03-segment-tree.md) | O(log n) |
| Updates or summaries awkward to merge or tag | Square-root blocks (§7) | O(√n) |
| Offline queries about a window's contents (distinct, pairs) | Mo's algorithm (§8) | O(√n) amortized |

## 10. Pitfalls and practice

1. Using a sparse table for sums. The overlap counts elements twice.
2. Off-by-one in the row length: row `j` has `n − 2^j + 1` entries, not `n`.
3. Computing `k` with floating-point `log2`, which can round wrong near powers of two. Use `bit_length() − 1`.
4. Forgetting the block tag when reading a partial block in square-root decomposition, or when reading a full block's minimum.
5. In Mo's algorithm, shrinking before extending, which can make `cur_l > cur_r + 1` and remove elements never added.
6. Returning Mo's answers in sorted order instead of the original query order.
7. Picking a block size of 0 for tiny inputs. Clamp it to at least 1.

Practice: static range minimum query (sparse table); range GCD queries; sliding window maximum with a sparse table (compare with a [monotonic deque](../06-monotonic-stack-and-deque/README.md)); lowest common ancestor via Euler tour and sparse table; range add with range sum (square-root blocks, then compare with a lazy segment tree); count values `≥ x` in a range with updates (sorted blocks); distinct elements in ranges (Mo's algorithm); count pairs of equal elements in ranges (Mo's algorithm).

Next: back to the [Range Queries overview](README.md).
