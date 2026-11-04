# Segment Tree — Any Range Summary, Any Update

## 1. The problem and the brute force

Eight sensors report temperatures. Two kinds of requests arrive in any order:

- `set(i, value)`: sensor `i` now reads `value`.
- `query(l, r)`: the **lowest** reading among sensors `l` through `r`, both included.

```text
sensor i     0   1   2   3   4   5   6   7
reading      5   8   6   3   2   7   2   6
```

Requests in order:

1. `query(1, 6)` → `min(8, 6, 3, 2, 7, 2) = 2`
2. `set(4, 9)`
3. `query(3, 5)` → `min(3, 9, 7) = 3`

**Brute force.** Store the raw array. `set` is O(1); `query` scans the range, O(n). For 100,000 requests on 100,000 sensors, that is up to `10¹⁰` steps.

**Why the earlier tools fail.** [Prefix sums](01-prefix-sums.md) and the [Fenwick tree](02-fenwick-tree.md) answer a range by subtracting two prefixes. A prefix-minimum table cannot be "subtracted": `[1, 5, 6]` and `[1, 2, 6]` have the same prefix minima but different minima on `[1, 2]` ([Chapter 1 §9](01-prefix-sums.md#9-what-prefix-sums-cannot-do)). The Fenwick tree has the same limitation, and its prefix-max variant also breaks as soon as a value goes down.

## 2. The observation: store the answer for every half, quarter, eighth

Cut the array in half, then each half in half, until single elements remain. Store the minimum of every piece:

```text
                             [0,7]:2
                ┌───────────────┴───────────────┐
             [0,3]:3                         [4,7]:2
        ┌───────┴───────┐               ┌───────┴───────┐
     [0,1]:5         [2,3]:3         [4,5]:2         [6,7]:2
    ┌───┴───┐       ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    5       8       6       3       2       7       2       6
```

This is a **segment tree**. Each box is a **node**. `[2,3]:3` means "this node covers sensors 2 and 3, and their minimum is 3". The bottom row holds the **leaves**, one per element. The top node is the **root**, covering everything. (Binary trees, roots, leaves and recursion on trees are introduced from scratch in [Trees](../03-trees/README.md).)

Two facts make this useful:

- **A parent's answer comes from its two children.** The minimum of `[0, 3]` is `min(minimum of [0, 1], minimum of [2, 3]) = min(5, 3) = 3`. No other element needs to be looked at.
- **Any range is a union of a few nodes.** The range `[1, 6]` is `{1} ∪ [2,3] ∪ [4,5] ∪ {6}`: four nodes, and the answer is the minimum of their four stored values, `min(8, 3, 2, 2) = 2`.

So a query combines a few stored answers instead of scanning, and an update only has to repair the nodes above one leaf.

**Invariant.** Every node stores the summary (here, the minimum) of exactly the elements in its range.

Nothing here used subtraction. The only requirement is a way to **combine** two neighboring summaries into the summary of their union. Section 6 states that requirement precisely.

### Storing the tree in a list

Number the root 1. The children of node `v` are `2v` (left) and `2v + 1` (right):

```text
                                1
                ┌───────────────┴───────────────┐
                2                               3
        ┌───────┴───────┐               ┌───────┴───────┐
        4               5               6               7
    ┌───┴───┐       ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    8       9      10      11      12      13      14      15
```

No pointers are needed: a list `tree` of size `4n` is enough. **Why `4n`?** When `n` is not a power of two, the halves are uneven and the tree is not perfectly full; its depth is `⌈log₂ n⌉`, so the largest index is below `2 · 2^⌈log₂ n⌉ < 4n`. It is a safe bound, not an exact count.

## 3. Building, traced level by level

Build recursively: a node covering one element stores that element; any other node builds its two children, then combines them. The split point is `mid = (l + r) // 2`; the left child covers `[l, mid]`, the right child `[mid + 1, r]`.

The recursion finishes the leaves first and the root last, so the values appear bottom-up:

| Level | Nodes finished, as `range: value` | How |
|---|---|---|
| leaves | `0:5`, `1:8`, `2:6`, `3:3`, `4:2`, `5:7`, `6:2`, `7:6` | copy the array |
| pairs | `[0,1]: min(5, 8) = 5`, `[2,3]: min(6, 3) = 3`, `[4,5]: min(2, 7) = 2`, `[6,7]: min(2, 6) = 2` | combine two leaves |
| halves | `[0,3]: min(5, 3) = 3`, `[4,7]: min(2, 2) = 2` | combine two pairs |
| root | `[0,7]: min(3, 2) = 2` | combine two halves |

There are `n` leaves and `n − 1` inner nodes, each combined once, so building is O(n).

## 4. Query: three cases at every node

To answer `query(ql, qr)`, start at the root. At a node covering `[l, r]`, exactly one of three cases holds:

1. **No overlap** (`qr < l` or `r < ql`): this node contributes nothing. Return the **identity**, a value that does not change the answer. For minimum the identity is `+∞`, since `min(x, +∞) = x`.
2. **Full cover** (`ql ≤ l` and `r ≤ qr`): the node's stored value is exactly its contribution. Return it without looking deeper.
3. **Partial overlap**: the node contains some wanted and some unwanted elements. Ask both children and combine their answers.

**Trace** of `query(1, 6)`:

| Node | Range | Case | Returns |
|---:|---|---|---|
| 1 | `[0, 7]` | partial | `min(3, 2) = 2` |
| 2 | `[0, 3]` | partial | `min(8, 3) = 3` |
| 4 | `[0, 1]` | partial | `min(∞, 8) = 8` |
| 8 | `[0, 0]` | no overlap | `∞` |
| 9 | `[1, 1]` | full cover | `8` |
| 5 | `[2, 3]` | full cover | `3` |
| 3 | `[4, 7]` | partial | `min(2, 2) = 2` |
| 6 | `[4, 5]` | full cover | `2` |
| 7 | `[6, 7]` | partial | `min(2, ∞) = 2` |
| 14 | `[6, 6]` | full cover | `2` |
| 15 | `[7, 7]` | no overlap | `∞` |

The answer 2 came from the four full-cover nodes 9, 5, 6 and 14, which are exactly the pieces `{1}`, `[2, 3]`, `[4, 5]`, `{6}` from §2. Eleven nodes were visited out of fifteen, but for long arrays the fraction visited shrinks to almost nothing, as §7 shows.

## 5. Point update: fix one leaf, then its ancestors

`set(i, value)` changes one element. Only the nodes whose range contains `i` can change: the leaf for `i` and every node on the path from it up to the root. Walk down to the leaf, overwrite it, and on the way back up recompute each node from its two children.

**Trace** of `set(4, 9)`:

| Node | Range | Before | After | How |
|---:|---|---:|---:|---|
| 12 | `[4, 4]` | 2 | 9 | overwrite the leaf |
| 6 | `[4, 5]` | 2 | 7 | `min(9, 7)` |
| 3 | `[4, 7]` | 2 | 2 | `min(7, 2)` |
| 1 | `[0, 7]` | 2 | 2 | `min(3, 2)` |

Four nodes changed, one per level. Now `query(3, 5)` uses node 11 (`[3, 3]`, value 3) and node 6 (`[4, 5]`, value 7) and returns `min(3, 7) = 3`. ✓

## 6. Code: a generic segment tree

The tree never needs to know *what* it is combining. It needs two things from the caller:

- `combine(x, y)`: the summary of a left range `x` followed by a right range `y`.
- `identity`: a value with `combine(identity, x) = combine(x, identity) = x`, returned for no-overlap nodes.

`combine` must be **associative**: `combine(combine(x, y), z) = combine(x, combine(y, z))`. That is what lets the tree group the elements however its shape dictates and still get the same answer as combining them left to right. It does **not** need to be commutative (order-independent), but then the code must always keep the left child on the left.

| Summary | `combine(x, y)` | Identity |
|---|---|---|
| Sum | `x + y` | `0` |
| Minimum | `min(x, y)` | `+∞` |
| Maximum | `max(x, y)` | `−∞` |
| GCD | `gcd(x, y)` | `0` |
| Product | `x * y` | `1` |
| String concatenation | `x + y` (order matters) | `""` |

```python
from functools import reduce
from math import gcd, inf
from random import Random
from typing import Any, Callable


class SegmentTree:
    """Point set and inclusive range query for any associative combine."""

    def __init__(self, nums: list, combine: Callable[[Any, Any], Any], identity: Any):
        self.n = len(nums)
        self.combine = combine
        self.identity = identity
        self.tree = [identity] * (4 * max(1, self.n))
        if self.n:
            self._build(1, 0, self.n - 1, nums)

    def _build(self, node: int, l: int, r: int, nums: list) -> None:
        if l == r:
            self.tree[node] = nums[l]
            return
        mid = (l + r) // 2
        self._build(2 * node, l, mid, nums)
        self._build(2 * node + 1, mid + 1, r, nums)
        self.tree[node] = self.combine(self.tree[2 * node], self.tree[2 * node + 1])

    def set(self, i: int, value: Any) -> None:
        if not 0 <= i < self.n:
            raise ValueError(f"index {i} out of range")
        self._set(1, 0, self.n - 1, i, value)

    def _set(self, node: int, l: int, r: int, i: int, value: Any) -> None:
        if l == r:
            self.tree[node] = value
            return
        mid = (l + r) // 2
        if i <= mid:
            self._set(2 * node, l, mid, i, value)
        else:
            self._set(2 * node + 1, mid + 1, r, i, value)
        self.tree[node] = self.combine(self.tree[2 * node], self.tree[2 * node + 1])

    def query(self, ql: int, qr: int) -> Any:
        """Summary of nums[ql..qr], both ends included."""
        if not 0 <= ql <= qr < self.n:
            raise ValueError(f"bad range [{ql}, {qr}]")
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node: int, l: int, r: int, ql: int, qr: int) -> Any:
        if qr < l or r < ql:                      # no overlap
            return self.identity
        if ql <= l and r <= qr:                   # full cover
            return self.tree[node]
        mid = (l + r) // 2                        # partial overlap
        left = self._query(2 * node, l, mid, ql, qr)
        right = self._query(2 * node + 1, mid + 1, r, ql, qr)
        return self.combine(left, right)          # left stays on the left


def main():
    temps = SegmentTree([5, 8, 6, 3, 2, 7, 2, 6], min, inf)
    assert temps.tree[1:8] == [2, 3, 2, 5, 3, 2, 2]       # §3 trace
    assert temps.query(1, 6) == 2                          # §4 trace
    temps.set(4, 9)                                        # §5 trace
    assert temps.tree[12] == 9 and temps.tree[6] == 7
    assert temps.query(3, 5) == 3

    words = SegmentTree(list("segment"), lambda x, y: x + y, "")
    assert words.query(1, 4) == "egme"                     # order preserved
    for bad in [lambda: temps.query(0, 8), lambda: temps.set(8, 0),
                lambda: temps.query(5, 4)]:
        try:
            bad()
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = Random(21)
    kinds = [(min, inf, min), (max, -inf, max),
             (lambda x, y: x + y, 0, sum), (gcd, 0, lambda seq: reduce(gcd, seq, 0))]
    for _ in range(200):
        n = rng.randint(1, 17)                  # includes non-powers of two
        for combine, identity, brute in kinds:
            a = [rng.randint(0, 9) for _ in range(n)]
            st = SegmentTree(a, combine, identity)
            for _ in range(20):
                if rng.random() < 0.4:
                    i, v = rng.randrange(n), rng.randint(0, 9)
                    a[i] = v
                    st.set(i, v)
                else:
                    l = rng.randrange(n)
                    r = rng.randrange(l, n)
                    assert st.query(l, r) == brute(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Build O(n); `set` and `query` O(log n) time and O(log n) recursion depth; space O(n) for `tree` (size `4n`). Each `combine` call is assumed to cost O(1). For a summary that costs more, such as a string, multiply by that cost.

## 7. Why it's correct, and why a query is O(log n)

**Build.** By induction from the leaves up: a leaf holds its element; if both children hold the correct summaries of `[l, mid]` and `[mid + 1, r]`, then `combine` of the two is the summary of `[l, r]`, because the two ranges are neighbors and `combine` is associative.

**Query.** By induction on the node: a no-overlap node contributes no wanted element, and the identity changes nothing. A full-cover node's stored summary is exactly its wanted elements. A partial node's wanted elements split into the wanted elements of its left child followed by those of its right child, and combining the two children's answers in that order gives their summary.

**Point update.** Only nodes whose range contains `i` can change. Those are exactly the nodes on the root-to-leaf path. Recomputing them bottom-up restores the invariant for each one, because its children are already correct when it is recomputed.

**Query cost.** Look at one level of the tree. The nodes at that level cover disjoint ranges side by side. A node where the query **continues** (partial overlap) holds a wanted element right next to an unwanted one, so the boundary `ql` or the boundary `qr` passes through it. At most one node per level contains the `ql` boundary and at most one the `qr` boundary, so **at most two nodes per level continue**. Each continuing node has two children, so at most four nodes per level are visited. With `⌈log₂ n⌉ + 1` levels, a query visits at most about `4 log₂ n` nodes: O(log n).

## 8. Designing a node summary: maximum subarray sum

The power of a segment tree is that the "summary" can be anything with an associative combine. Designing one means asking: **what must a node remember so that two neighbors can be merged without looking inside them?**

### The problem

Point updates, and queries asking for the **largest sum of a nonempty contiguous run** inside `[l, r]`. For `[2, −5, 3, 4, −1, 2]`, the best run in the whole array is `3 + 4 − 1 + 2 = 8`.

### What a node must remember

Storing only the best sum of each half is not enough: the best run of the union may **cross** the middle, made of a run ending at the right edge of the left half plus a run starting at the left edge of the right half. So a node keeps four numbers:

| Field | Meaning |
|---|---|
| `total` | sum of the whole range |
| `pref` | best sum of a nonempty run that **starts** at the left edge |
| `suff` | best sum of a nonempty run that **ends** at the right edge |
| `best` | best sum of any nonempty run inside |

Merging left `L` with right `R`:

$$
\begin{aligned}
total &= L.total + R.total \\
pref &= \max(L.pref,\; L.total + R.pref) \\
suff &= \max(R.suff,\; R.total + L.suff) \\
best &= \max(L.best,\; R.best,\; L.suff + R.pref)
\end{aligned}
$$

Each formula lists the only ways a run of that kind can sit relative to the split. For example, a prefix run of the union either stays inside `L`, or covers all of `L` and continues into `R`.

**Trace** merging `[3, 4]` with `[−1, 2]`:

| Summary | `total` | `pref` | `suff` | `best` |
|---|---:|---:|---:|---:|
| `L = [3, 4]` | 7 | 7 | 7 | 7 |
| `R = [−1, 2]` | 1 | 1 | 2 | 2 |
| merged | `7 + 1 = 8` | `max(7, 7 + 1) = 8` | `max(2, 1 + 7) = 8` | `max(7, 2, 7 + 1) = 8` |

The merged `best = 8` is the crossing run `3 + 4 − 1 + 2`. The identity is "no elements"; `None` stands for it, and `combine` skips it.

```python
from random import Random


def leaf(x: int):
    return (x, x, x, x)          # total, pref, suff, best


def merge(a, b):
    if a is None:                # identity: no elements
        return b
    if b is None:
        return a
    return (a[0] + b[0],
            max(a[1], a[0] + b[1]),
            max(b[2], b[0] + a[2]),
            max(a[3], b[3], a[2] + b[1]))


def fold(seq, rng):
    """Merge leaves split at random points, as some tree shape would."""
    if not seq:
        return None
    if len(seq) == 1:
        return leaf(seq[0])
    cut = rng.randint(1, len(seq) - 1)
    return merge(fold(seq[:cut], rng), fold(seq[cut:], rng))


def best_run_brute(seq):
    return max(sum(seq[i:j]) for i in range(len(seq))
               for j in range(i + 1, len(seq) + 1))


def main():
    assert merge(merge(leaf(3), leaf(4)), merge(leaf(-1), leaf(2))) == (8, 8, 8, 8)
    assert merge(None, leaf(5)) == leaf(5)
    rng = Random(22)
    for _ in range(2000):
        a = [rng.randint(-6, 6) for _ in range(rng.randint(1, 12))]
        assert fold(a, rng)[3] == best_run_brute(a)


if __name__ == "__main__":
    main()
```

To use it, pass `[leaf(x) for x in a]`, `merge` and `None` to the `SegmentTree` of §6, and replace `set(i, x)` by `set(i, leaf(x))`; the answer is field `best` of the query. The test above merges the leaves along random split points, so it checks every tree shape the segment tree could use.


Each merge is O(1), so every operation stays O(log n). The same recipe designs summaries for "longest run of equal values", "count of distinct adjacent pairs", or "is this range sorted?".

## 9. Descending search: the first position that meets a condition

### The problem

The array holds nonnegative amounts (stock in bins, seats per row). Find the **first index `k` whose prefix sum `a[0] + … + a[k]` reaches at least `x`**, while amounts keep changing. For `a = [2, 0, 3, 1, 4, 1, 0, 5]` and `x = 7`, the prefix sums are `2, 2, 5, 6, 10, …`, so the answer is index 4.

**Brute force.** Scan prefix sums: O(n). **Binary search over `query(0, k)`**: O(log n) probes, each O(log n), so O(log² n).

### The observation: let the tree steer

Start at the root with target `x`. At each node, look at the **left child's sum**:

- If it is `≥ x`, the answer is inside the left child. Go left with the same `x`.
- Otherwise, the whole left child is used up. Go right with `x − left sum`.

One step per level: O(log n). Nonnegative values guarantee that prefix sums never decrease, so "the left part is not enough" means the answer cannot be on the left.

**Trace** with `x = 7` on the sum tree:

```text
                            [0,7]:16
                ┌───────────────┴───────────────┐
             [0,3]:6                        [4,7]:10
        ┌───────┴───────┐               ┌───────┴───────┐
     [0,1]:2         [2,3]:4         [4,5]:5         [6,7]:5
    ┌───┴───┐       ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    2       0       3       1       4       1       0       5
```

| Node | Range | Left child sum | `x` | Decision |
|---|---|---:|---:|---|
| root | `[0, 7]` | 6 | 7 | `6 < 7`: go right, `x = 7 − 6 = 1` |
| | `[4, 7]` | 5 | 1 | `5 ≥ 1`: go left |
| | `[4, 5]` | 4 | 1 | `4 ≥ 1`: go left |
| leaf | `[4, 4]` | — | 1 | answer: index 4 |

If the root's total is below `x`, no index works; return −1.

### A second search: first index `≥ l` with value `≥ x`

A max tree supports a related search: "first position at or after `l` whose value is at least `x`" (for example, the first bin from `l` onward that can hold an item of size `x`). Recurse left-first, and **prune** any node that lies entirely before `l` or whose maximum is below `x`. A pruned node costs O(1). A node whose range is fully inside `[l, n − 1]` and whose maximum is `≥ x` is guaranteed to contain an answer, so the search descends into it once and never backtracks out of it. Only the O(log n) nodes on the boundary at `l` can fail after being entered. The total is O(log n).

```python
from math import inf
from random import Random


class SumMaxTree:
    """Point set; prefix-sum search and first-at-least search. 0-based."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        size = 4 * max(1, self.n)
        self.sum = [0] * size
        self.max = [-inf] * size
        if self.n:
            self._build(1, 0, self.n - 1, nums)

    def _pull(self, node: int) -> None:
        self.sum[node] = self.sum[2 * node] + self.sum[2 * node + 1]
        self.max[node] = max(self.max[2 * node], self.max[2 * node + 1])

    def _build(self, node, l, r, nums):
        if l == r:
            self.sum[node] = self.max[node] = nums[l]
            return
        mid = (l + r) // 2
        self._build(2 * node, l, mid, nums)
        self._build(2 * node + 1, mid + 1, r, nums)
        self._pull(node)

    def set(self, i: int, value: int, node=1, l=0, r=None) -> None:
        r = self.n - 1 if r is None else r
        if l == r:
            self.sum[node] = self.max[node] = value
            return
        mid = (l + r) // 2
        if i <= mid:
            self.set(i, value, 2 * node, l, mid)
        else:
            self.set(i, value, 2 * node + 1, mid + 1, r)
        self._pull(node)

    def first_prefix_at_least(self, x: int) -> int:
        """Smallest k with a[0] + ... + a[k] >= x; values must be >= 0."""
        if self.n == 0 or self.sum[1] < x:
            return -1
        node, l, r = 1, 0, self.n - 1
        while l < r:
            mid = (l + r) // 2
            left_sum = self.sum[2 * node]
            if left_sum >= x:
                node, r = 2 * node, mid
            else:
                x -= left_sum
                node, l = 2 * node + 1, mid + 1
        return l

    def first_at_least(self, start: int, x: int) -> int:
        """Smallest i >= start with a[i] >= x, or -1."""
        if not 0 <= start < self.n:
            return -1
        return self._first(1, 0, self.n - 1, start, x)

    def _first(self, node, l, r, start, x):
        if r < start or self.max[node] < x:      # prune
            return -1
        if l == r:
            return l
        mid = (l + r) // 2
        found = self._first(2 * node, l, mid, start, x)
        if found != -1:
            return found
        return self._first(2 * node + 1, mid + 1, r, start, x)


def main():
    t = SumMaxTree([2, 0, 3, 1, 4, 1, 0, 5])
    assert t.first_prefix_at_least(7) == 4          # §9 trace
    assert t.first_prefix_at_least(1) == 0
    assert t.first_prefix_at_least(16) == 7
    assert t.first_prefix_at_least(17) == -1
    assert t.first_prefix_at_least(0) == 0
    assert t.first_at_least(5, 4) == 7
    assert t.first_at_least(0, 6) == -1
    t.set(6, 9)
    assert t.first_at_least(5, 4) == 6

    rng = Random(23)
    for _ in range(300):
        n = rng.randint(1, 16)
        a = [rng.randint(0, 5) for _ in range(n)]
        t = SumMaxTree(a)
        for _ in range(20):
            if rng.random() < 0.3:
                i, v = rng.randrange(n), rng.randint(0, 5)
                a[i] = v
                t.set(i, v)
            x = rng.randint(0, 5 * n + 2)
            running, expected = 0, -1
            for k, v in enumerate(a):
                running += v
                if running >= x:
                    expected = k
                    break
            assert t.first_prefix_at_least(x) == expected
            s, y = rng.randrange(n), rng.randint(0, 6)
            assert t.first_at_least(s, y) == next(
                (i for i in range(s, n) if a[i] >= y), -1)


if __name__ == "__main__":
    main()
```

Both searches are O(log n). The [Fenwick tree's binary lifting](02-fenwick-tree.md#11-finding-the-k-th-smallest-binary-lifting) does the prefix search too, but only a segment tree supports the "starting at `l`, by maximum" search.

## 10. Lazy propagation: range add, range sum

### The problem

Now updates cover ranges: `range_add(l, r, delta)` adds `delta` to every element in `[l, r]`, and `query(l, r)` returns the sum. Requests interleave.

**Brute force with the tree.** Do a point update for each element in the range: up to `n` updates of O(log n) each, so O(n log n) per request. Worse than the raw array.

### The observation: update a whole node at once, tell its children later

A range update visits the same O(log n) nodes as a query, and the full-cover nodes among them exactly tile the range. If a full-cover node covers `len = r − l + 1` elements and each grows by `delta`, its sum grows by `delta · len`. We can fix that node's sum immediately without visiting its descendants.

The descendants are now out of date. Instead of fixing them, leave a note on the node: "every element below me still needs `+delta`". This note is called a **lazy tag**. The descendants are fixed only if a later request needs to go below this node. At that moment, **push** the tag one level down: apply it to both children (fixing their sums and adding to their tags), then clear it.

**Invariant.** Every node's stored sum is correct for its range, taking into account every update applied so far, **except** updates still waiting in the tags of its ancestors.

So a node's value is trustworthy whenever every ancestor's tag has been pushed, which is exactly the case for every node a request reaches, because requests push on their way down.

### Trace

Start with eight zeros. Each node is written `sum` or `sum(tag)`.

**`range_add(2, 5, +3)`** visits the same nodes a query for `[2, 5]` would. The two full-cover nodes, `[2, 3]` and `[4, 5]`, each get `sum += 3 · 2` and `tag += 3` and stop. On the way back up, `[0, 3]`, `[4, 7]` and the root are recomputed from their children:

```text
                            [0,7]:12
                ┌───────────────┴───────────────┐
             [0,3]:6                         [4,7]:6
        ┌───────┴───────┐               ┌───────┴───────┐
     [0,1]:0       [2,3]:6(+3)     [4,5]:6(+3)       [6,7]:0
    ┌───┴───┐       ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    0       0       0       0       0       0       0       0
```

The leaves under `[2, 3]` and `[4, 5]` still say 0. That is allowed: their ancestors carry the tag.

**`query(5, 6)`** (the true array is `[0, 0, 3, 3, 3, 3, 0, 0]`, so the answer is `3 + 0 = 3`):

| Node | Range | Case | Action | Returns |
|---|---|---|---|---:|
| root, `[4, 7]` | | partial | no tag to push, recurse | 3 |
| | `[4, 5]` | partial | **push `+3`**: leaves 4 and 5 become 3; clear the tag | 3 |
| | `[5, 5]` | full cover | return stored 3 | 3 |
| | `[6, 7]` | partial | no tag to push, recurse | 0 |
| | `[6, 6]` | full cover | return stored 0 | 0 |

The no-overlap nodes `[0, 3]`, `[4, 4]` and `[7, 7]` return 0. The push happened only where the query had to go deeper. The tag on `[2, 3]` is still waiting, and that is fine.

**Why keep the node's sum correct, instead of only storing the tag?** A later query that fully covers `[2, 3]` returns the stored sum without looking down. If the sum were stale, that answer would be wrong.

```python
from random import Random


class LazyRangeSum:
    """range_add(l, r, delta) and query(l, r) = sum; 0-based, inclusive."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        size = 4 * max(1, self.n)
        self.sum = [0] * size
        self.tag = [0] * size        # pending add for every element below
        if self.n:
            self._build(1, 0, self.n - 1, nums)

    def _build(self, node, l, r, nums):
        if l == r:
            self.sum[node] = nums[l]
            return
        mid = (l + r) // 2
        self._build(2 * node, l, mid, nums)
        self._build(2 * node + 1, mid + 1, r, nums)
        self.sum[node] = self.sum[2 * node] + self.sum[2 * node + 1]

    def _apply(self, node, l, r, delta):
        self.sum[node] += delta * (r - l + 1)   # every element grows by delta
        self.tag[node] += delta                 # children still need it

    def _push(self, node, l, r):
        if self.tag[node] and l < r:
            mid = (l + r) // 2
            self._apply(2 * node, l, mid, self.tag[node])
            self._apply(2 * node + 1, mid + 1, r, self.tag[node])
            self.tag[node] = 0

    def range_add(self, ql: int, qr: int, delta: int) -> None:
        if not 0 <= ql <= qr < self.n:
            raise ValueError(f"bad range [{ql}, {qr}]")
        self._add(1, 0, self.n - 1, ql, qr, delta)

    def _add(self, node, l, r, ql, qr, delta):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self._apply(node, l, r, delta)
            return
        self._push(node, l, r)
        mid = (l + r) // 2
        self._add(2 * node, l, mid, ql, qr, delta)
        self._add(2 * node + 1, mid + 1, r, ql, qr, delta)
        self.sum[node] = self.sum[2 * node] + self.sum[2 * node + 1]

    def query(self, ql: int, qr: int) -> int:
        if not 0 <= ql <= qr < self.n:
            raise ValueError(f"bad range [{ql}, {qr}]")
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node, l, r, ql, qr):
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return self.sum[node]
        self._push(node, l, r)
        mid = (l + r) // 2
        return (self._query(2 * node, l, mid, ql, qr)
                + self._query(2 * node + 1, mid + 1, r, ql, qr))


def main():
    st = LazyRangeSum([0] * 8)
    st.range_add(2, 5, 3)                    # §10 trace
    assert st.sum[1] == 12 and st.tag[5] == 3 and st.tag[6] == 3
    assert st.query(5, 6) == 3
    assert st.tag[6] == 0 and st.tag[5] == 3  # only [4,5] was pushed

    st = LazyRangeSum([1, 2, 3, 4, 5])
    st.range_add(1, 3, 3)
    assert st.query(1, 3) == 18 and st.query(0, 4) == 24
    st.range_add(0, 4, -2)
    assert st.query(0, 4) == 14 and st.query(2, 2) == 4

    rng = Random(24)
    for _ in range(300):
        n = rng.randint(1, 15)
        a = [rng.randint(-5, 5) for _ in range(n)]
        st = LazyRangeSum(a)
        for _ in range(25):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            if rng.random() < 0.5:
                delta = rng.randint(-4, 4)
                for i in range(l, r + 1):
                    a[i] += delta
                st.range_add(l, r, delta)
            else:
                assert st.query(l, r) == sum(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Build O(n); `range_add` and `query` O(log n) each; space O(n) for `sum` and `tag`. The update visits the same nodes a query would (§7), and each push is O(1).

**What makes a lazy tag work?** Two questions must have O(1) answers:

1. **Apply:** given a node's summary and a tag covering the whole node, what is the new summary? For sum with add: `sum + delta · len`. For minimum with add: `min + delta`.
2. **Compose:** if a node already has a tag and a new one arrives, what single tag means "old, then new"? For add after add: `old + new`.

If either answer needs to look inside the node, lazy propagation does not apply directly. (For example, "replace every `x` with `x mod m`" changes each element differently.)

## 11. Two kinds of updates: assignment and addition

### The problem

Now three requests: `range_assign(l, r, v)` sets every element in `[l, r]` to `v`; `range_add(l, r, delta)` adds; and queries ask for the range **sum** and the range **minimum**.

### The observation: a tag is a small program, and programs compose

Represent a tag as the pair `(set_to, add)`, read as "if `set_to` is not empty, set every element to `set_to`; then add `add`". Every combination of updates collapses into this shape:

| Existing tag | New update | Combined tag | Why |
|---|---|---|---|
| `(s, a)` | add `d` | `(s, a + d)` | adding twice adds the total |
| `(s, a)` | assign `v` | `(v, 0)` | assignment erases everything before it |
| empty `(None, 0)` | anything | the new update alone | nothing to combine with |

Order matters: "add 5, then set to 2" leaves 2, while "set to 2, then add 5" leaves 7. That is why the pair is read in one fixed order, set first, then add.

Applying a tag `(s, a)` to a node of length `len`:

| Field | If `s` is not empty | Then always |
|---|---|---|
| `sum` | `s · len` | `+ a · len` |
| `min` | `s` | `+ a` |

**Pitfall: empty is not zero.** "Set every element to 0" is a real update. If a tag used `0` to mean "no assignment", that update would vanish. Use `None`.

### Trace

Start with `[4, 1, 3, 2]`. Tags are written `(set, add)`.

| Request | Nodes fully covered | Their tags after | True array |
|---|---|---|---|
| `range_add(0, 3, +2)` | root `[0, 3]` | root `(None, 2)` | `[6, 3, 5, 4]` |
| `range_assign(1, 2, 0)` | push root to `[0, 1]`, `[2, 3]`, which get `(None, 2)`; then leaves `[1, 1]` and `[2, 2]` after pushing their parents | leaves 1, 2: `(0, 0)` | `[6, 0, 0, 4]` |
| `range_add(0, 1, +5)` | `[0, 1]` | `[0, 1]`: `(None, 5)` | `[11, 5, 0, 4]` |

Then `query_sum(0, 3) = 11 + 5 + 0 + 4 = 20` and `query_min(1, 3) = 0`. At the third step, `[0, 1]`'s earlier tag had already been pushed during the assignment, so its tag starts empty and becomes `(None, 5)`. Had it still held `(None, 2)`, composition would give `(None, 7)`.

```python
from math import inf
from random import Random


class AssignAddTree:
    """range_assign, range_add; range sum and range min. 0-based, inclusive."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        size = 4 * max(1, self.n)
        self.sum = [0] * size
        self.min = [inf] * size
        self.set_to = [None] * size   # None means "no pending assignment"
        self.add = [0] * size
        if self.n:
            self._build(1, 0, self.n - 1, nums)

    def _pull(self, node):
        self.sum[node] = self.sum[2 * node] + self.sum[2 * node + 1]
        self.min[node] = min(self.min[2 * node], self.min[2 * node + 1])

    def _build(self, node, l, r, nums):
        if l == r:
            self.sum[node] = self.min[node] = nums[l]
            return
        mid = (l + r) // 2
        self._build(2 * node, l, mid, nums)
        self._build(2 * node + 1, mid + 1, r, nums)
        self._pull(node)

    def _apply(self, node, l, r, set_to, add):
        """Apply 'set to set_to (if not None), then add add' to a whole node."""
        length = r - l + 1
        if set_to is not None:
            self.sum[node] = set_to * length
            self.min[node] = set_to
            self.set_to[node] = set_to
            self.add[node] = 0          # assignment erases older adds
        if add:
            self.sum[node] += add * length
            self.min[node] += add
            self.add[node] += add

    def _push(self, node, l, r):
        if l < r and (self.set_to[node] is not None or self.add[node]):
            mid = (l + r) // 2
            for child, cl, cr in ((2 * node, l, mid), (2 * node + 1, mid + 1, r)):
                self._apply(child, cl, cr, self.set_to[node], self.add[node])
            self.set_to[node] = None
            self.add[node] = 0

    def _update(self, node, l, r, ql, qr, set_to, add):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self._apply(node, l, r, set_to, add)
            return
        self._push(node, l, r)
        mid = (l + r) // 2
        self._update(2 * node, l, mid, ql, qr, set_to, add)
        self._update(2 * node + 1, mid + 1, r, ql, qr, set_to, add)
        self._pull(node)

    def _check(self, ql, qr):
        if not 0 <= ql <= qr < self.n:
            raise ValueError(f"bad range [{ql}, {qr}]")

    def range_assign(self, ql: int, qr: int, value: int) -> None:
        self._check(ql, qr)
        self._update(1, 0, self.n - 1, ql, qr, value, 0)

    def range_add(self, ql: int, qr: int, delta: int) -> None:
        self._check(ql, qr)
        self._update(1, 0, self.n - 1, ql, qr, None, delta)

    def _query(self, node, l, r, ql, qr):
        if qr < l or r < ql:
            return 0, inf
        if ql <= l and r <= qr:
            return self.sum[node], self.min[node]
        self._push(node, l, r)
        mid = (l + r) // 2
        ls, lm = self._query(2 * node, l, mid, ql, qr)
        rs, rm = self._query(2 * node + 1, mid + 1, r, ql, qr)
        return ls + rs, min(lm, rm)

    def query_sum(self, ql: int, qr: int) -> int:
        self._check(ql, qr)
        return self._query(1, 0, self.n - 1, ql, qr)[0]

    def query_min(self, ql: int, qr: int) -> int:
        self._check(ql, qr)
        return self._query(1, 0, self.n - 1, ql, qr)[1]


def main():
    t = AssignAddTree([4, 1, 3, 2])                # §11 trace
    t.range_add(0, 3, 2)
    t.range_assign(1, 2, 0)                        # assigning 0 must not vanish
    t.range_add(0, 1, 5)
    assert t.query_sum(0, 3) == 20 and t.query_min(1, 3) == 0
    t.range_assign(0, 3, 7)
    t.range_add(2, 3, -10)
    assert t.query_sum(0, 3) == 8 and t.query_min(0, 3) == -3

    rng = Random(25)
    for _ in range(400):
        n = rng.randint(1, 14)
        a = [rng.randint(-5, 5) for _ in range(n)]
        t = AssignAddTree(a)
        for _ in range(30):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            op = rng.randrange(3)
            if op == 0:
                v = rng.randint(-3, 3)
                a[l:r + 1] = [v] * (r - l + 1)
                t.range_assign(l, r, v)
            elif op == 1:
                d = rng.randint(-3, 3)
                for i in range(l, r + 1):
                    a[i] += d
                t.range_add(l, r, d)
            else:
                assert t.query_sum(l, r) == sum(a[l:r + 1])
                assert t.query_min(l, r) == min(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Every operation is O(log n); space O(n). The same pattern handles "multiply then add" (tag `(m, a)` meaning `x → m·x + a`, composed as `(m₂m₁, m₂a₁ + a₂)`), which appears in modular-arithmetic problems.

## 12. Advanced: dynamic and persistent segment trees

### Dynamic segment tree: huge index ranges

**Problem.** Bookings arrive as ranges of times between 0 and 10⁹. After each booking, report the maximum number of overlapping bookings. An array of size `4 · 10⁹` is impossible.

**Observation.** Only nodes that a request actually visits ever hold anything other than the starting value 0. Create nodes **on demand**: a node gets children only when a push needs them. Each request creates O(log U) nodes, where `U` is the size of the index range, so `q` requests need O(q log U) memory. When all requests are known in advance, [coordinate compression](02-fenwick-tree.md#10-counting-with-a-fenwick-tree-how-many-smaller-elements) with a normal tree is simpler. A dynamic tree is for when they are not.

```python
from random import Random


class DynamicMaxTree:
    """range_add and range max over integer indices [lo, hi], all starting at 0."""

    def __init__(self, lo: int, hi: int):
        if lo > hi:
            raise ValueError("empty domain")
        self.lo, self.hi = lo, hi
        self.left, self.right = [0], [0]     # node 0 is the root; 0 = no child
        self.max, self.tag = [0], [0]

    def _new(self) -> int:
        for arr in (self.left, self.right, self.max, self.tag):
            arr.append(0)
        return len(self.max) - 1

    def _push(self, node: int) -> None:
        if self.left[node] == 0:                 # create children on demand
            self.left[node] = self._new()
            self.right[node] = self._new()
        if self.tag[node]:
            for child in (self.left[node], self.right[node]):
                self.max[child] += self.tag[node]
                self.tag[child] += self.tag[node]
            self.tag[node] = 0

    def range_add(self, ql: int, qr: int, delta: int, node=0, l=None, r=None) -> None:
        if l is None:
            if not self.lo <= ql <= qr <= self.hi:
                raise ValueError("bad range")
            l, r = self.lo, self.hi
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self.max[node] += delta
            self.tag[node] += delta
            return
        self._push(node)
        mid = (l + r) // 2
        self.range_add(ql, qr, delta, self.left[node], l, mid)
        self.range_add(ql, qr, delta, self.right[node], mid + 1, r)
        self.max[node] = max(self.max[self.left[node]], self.max[self.right[node]])

    def query_max(self, ql: int, qr: int, node=0, l=None, r=None) -> int:
        if l is None:
            if not self.lo <= ql <= qr <= self.hi:
                raise ValueError("bad range")
            l, r = self.lo, self.hi
        if qr < l or r < ql:
            return -(10 ** 18)
        if ql <= l and r <= qr:
            return self.max[node]
        self._push(node)
        mid = (l + r) // 2
        return max(self.query_max(ql, qr, self.left[node], l, mid),
                   self.query_max(ql, qr, self.right[node], mid + 1, r))


def main():
    cal = DynamicMaxTree(0, 10 ** 9)
    for start, end in [(10, 20), (50, 60), (10, 40), (5, 15), (5, 10), (25, 55)]:
        cal.range_add(start, end - 1, 1)          # half-open booking [start, end)
    assert cal.query_max(0, 10 ** 9) == 3
    assert len(cal.max) < 400                    # nodes created on demand

    rng = Random(26)
    for _ in range(200):
        hi = rng.randint(0, 40)
        tree, a = DynamicMaxTree(0, hi), [0] * (hi + 1)
        for _ in range(20):
            l = rng.randint(0, hi)
            r = rng.randint(l, hi)
            if rng.random() < 0.5:
                d = rng.randint(-3, 3)
                for i in range(l, r + 1):
                    a[i] += d
                tree.range_add(l, r, d)
            else:
                assert tree.query_max(l, r) == max(a[l:r + 1])


if __name__ == "__main__":
    main()
```

Each request is O(log U) time and creates O(log U) nodes.

### Persistent segment tree: every past version, cheaply

**Problem.** Answer "what is the `k`-th smallest value in `a[l..r]`?" for many ranges of a fixed array. For `a = [3, 1, 4, 1, 5]`, the 2nd smallest in `[1, 3]` (values `1, 4, 1`) is 1, and the 3rd is 4.

**Observation 1: prefix versions.** Build a count tree over **values**, like the [Fenwick multiset](02-fenwick-tree.md#11-finding-the-k-th-smallest-binary-lifting). Let version `i` hold the counts of `a[0..i−1]`. The counts of `a[l..r]` are "version `r + 1` minus version `l`", node by node. Descend both versions together: at each node, `left_count = cnt(left child in version r+1) − cnt(left child in version l)`. If `k ≤ left_count`, go left; otherwise go right with `k − left_count`.

**Observation 2: path copying.** Storing `n + 1` full trees costs O(n²). But version `i + 1` differs from version `i` only along one root-to-leaf path (one point update). So build version `i + 1` by copying **only that path**, and let the new nodes point to the old, unchanged children. Each version adds O(log m) nodes, where `m` is the number of distinct values. A structure that keeps every old version available after updates is called **persistent**.

```text
version i                      version i+1  (insert a value in the left half)
      R                              R'            new nodes: R', A', C'
     / \                            /  \           shared with version i: B, D
    A   B                         A'    B
   / \                           /  \
  C   D                        C'    D
```

```python
from random import Random


class PersistentKth:
    """k-th smallest in a[l..r] for a fixed array, via prefix versions."""

    def __init__(self, a: list[int]):
        self.values = sorted(set(a))
        rank = {v: t for t, v in enumerate(self.values)}
        self.m = len(self.values)
        # Node 0 is the shared empty tree: its children are itself, count 0.
        self.left, self.right, self.cnt = [0], [0], [0]
        self.roots = [0]
        for x in a:
            self.roots.append(self._insert(self.roots[-1], 0, self.m - 1, rank[x]))

    def _insert(self, old: int, l: int, r: int, pos: int) -> int:
        new = len(self.cnt)                       # copy the node on the path
        self.left.append(self.left[old])
        self.right.append(self.right[old])
        self.cnt.append(self.cnt[old] + 1)
        if l < r:
            mid = (l + r) // 2
            if pos <= mid:
                self.left[new] = self._insert(self.left[old], l, mid, pos)
            else:
                self.right[new] = self._insert(self.right[old], mid + 1, r, pos)
        return new

    def kth(self, l: int, r: int, k: int) -> int:
        """k-th smallest (k from 1) among a[l..r], both ends included."""
        if not 0 <= l <= r < len(self.roots) - 1 or not 1 <= k <= r - l + 1:
            raise ValueError("bad query")
        u, v = self.roots[l], self.roots[r + 1]
        lo, hi = 0, self.m - 1
        while lo < hi:
            mid = (lo + hi) // 2
            left_count = self.cnt[self.left[v]] - self.cnt[self.left[u]]
            if k <= left_count:
                u, v, hi = self.left[u], self.left[v], mid
            else:
                k -= left_count
                u, v, lo = self.right[u], self.right[v], mid + 1
        return self.values[lo]


def main():
    pk = PersistentKth([3, 1, 4, 1, 5])
    assert pk.kth(1, 3, 2) == 1 and pk.kth(1, 3, 3) == 4
    assert pk.kth(0, 4, 5) == 5 and pk.kth(2, 2, 1) == 4

    rng = Random(27)
    for _ in range(200):
        a = [rng.randint(-5, 5) for _ in range(rng.randint(1, 12))]
        pk = PersistentKth(a)
        for _ in range(15):
            l = rng.randrange(len(a))
            r = rng.randrange(l, len(a))
            k = rng.randint(1, r - l + 1)
            assert pk.kth(l, r, k) == sorted(a[l:r + 1])[k - 1]


if __name__ == "__main__":
    main()
```

Build O(n log n) time and O(n log n) nodes; each query O(log n). Persistence also answers "what did the array look like after the `t`-th update?" in general: keep one root per version.

## 13. Summary

**The recursive template.** Every function in this chapter has the same shape:

```text
f(node, l, r):
    if [l, r] misses the request:   return identity / do nothing
    if [l, r] is inside the request: use or update the node's stored summary (apply a tag)
    push(node)                        # lazy trees only
    mid = (l + r) // 2
    recurse into (2·node, l, mid) and (2·node + 1, mid + 1, r)
    pull(node)                        # after updates: recompute from the children
```

**What the caller must supply.**

| Tree | Requirement | Example |
|---|---|---|
| Plain (§6) | associative `combine` with an `identity` | `min`, `+∞` |
| Designed summary (§8) | a node record that two neighbors can merge in O(1) | `(total, pref, suff, best)` |
| Descent (§9) | a monotone condition: "not in the left child" rules the left out | prefix sum ≥ `x` with values ≥ 0 |
| Lazy (§10, §11) | O(1) **apply** of a tag to a node, O(1) **compose** of two tags | add: `sum += Δ·len`, `tag += Δ` |
| Dynamic (§12) | children created on first push | index range up to 10⁹ |
| Persistent (§12) | copy only the root-to-leaf path on each update | one root per version |

All of them are O(log n) per request (O(log U) for a dynamic tree over `U` indices), with O(n) nodes, or O(n log n) for a persistent tree.

Other variants worth knowing by name: the **iterative bottom-up segment tree** (leaves at `tree[n..2n−1]`, a loop instead of recursion, often faster in practice); the **merge-sort tree** (each node keeps its range sorted, for "how many values below `x` in `[l, r]`" in O(log² n)); and **segment tree beats** (range "set to `min(a[i], x)`" with amortized analysis). The [next chapter](04-sparse-table-and-sqrt.md#9-summary-choosing-a-structure) compares the segment tree with every other structure in this folder.

## 14. Pitfalls and practice

1. Returning the wrong identity on no-overlap nodes: 0 for minimum corrupts every answer when values are positive. Use `+∞` for min, `−∞` for max.
2. Swapping the children in `combine` for an order-dependent summary such as concatenation or the max-subarray tuple.
3. Allocating `2n` nodes for the recursive layout. Use `4n`.
4. Forgetting to recompute (pull) a node after updating its children.
5. Forgetting to push before descending into children, in both updates and queries.
6. Storing only the tag and leaving the node's own summary stale.
7. Using 0 as "no pending assignment". An assignment of 0 then disappears.
8. Composing assignment and addition in the wrong order. "Set, then add" is not "add, then set".
9. Using the prefix-sum descent with negative values. Prefix sums then go up and down and "the left part is not enough" no longer rules out the left.
10. Deep recursion in Python. For `n` up to about 10⁶ the depth is only about 20, but recursion is slow; for speed-critical code, use the iterative layout.

Practice: range sum query (mutable), with both a Fenwick tree and a segment tree; range minimum query with updates; maximum subarray sum in a range with point updates (the four-field summary); falling squares (range assign, range max, coordinates compressed); my calendar III (dynamic tree with range add, global max); count of smaller numbers after self (segment tree over values); booking concert tickets in groups (descending search on max and sum); the k-th smallest in a range (persistent tree); range add and range multiply under a modulus (composed affine tags).

Next: [Sparse Table and Square-Root Decomposition](04-sparse-table-and-sqrt.md).
