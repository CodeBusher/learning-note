# Fenwick Tree (Binary Indexed Tree) — Derivation, Proofs, and Variants

> Study sequence: [Prefix Sums](01-prefix-sums.md) → **Fenwick Tree** → [Segment Tree](03-segment-tree.md)  
> **Learning target:** Not merely recall `i += i & -i`, but *derive* both traversals from the interval stored by each node.

## 1. The problem that forces this design

A static prefix-sum array supports a range sum in O(1), but changing one element changes every later prefix: O(n). A raw array updates one item in O(1), but requires O(n) for a long range sum.

**Can we store fewer, strategically chosen partial sums so that both operations are O(log n)?** Yes: use power-of-two-aligned blocks.

| Structure | Build | Point add | Range sum | Space |
|---|---:|---:|---:|---:|
| Raw array | O(n) | O(1) | O(n) | O(n) |
| Prefix-sum array | O(n) | O(n) | O(1) | O(n) |
| Fenwick Tree | O(n) | **O(log n)** | **O(log n)** | O(n) |
| Segment Tree | O(n) | O(log n) | O(log n) | O(n) |

All indices in this note are **1-based**, unless explicitly stated otherwise. The input Python list passed into construction remains 0-based.

## 2. Inventing the blocks: why powers of two?

Any positive integer is a sum of powers of two: e.g. `13=8+4+1`. A prefix of length 13 could therefore be partitioned into only three appropriately placed blocks. We want to precompute blocks of lengths 1, 2, 4, 8, ... while using only one stored sum per array position.

**Rule:** Each index `i` stores the largest *power-of-two-aligned* block ending at `i`.

A block of length `2^k` ending at `i` is aligned when `2^k` divides `i`. Its maximal possible size is the largest power of two that divides `i`, called `lowbit(i)`:

$$
lowbit(i)=i\ \&\ (-i).
$$

Why does bitwise AND work? In two's complement, negative `i` is `~i+1`. The bits below the lowest set bit cancel, and only that lowest set bit remains when `i` is ANDed with `-i`.

For `i=12` (binary `1100`), `lowbit(12)=4`. Hence `tree[12]` stores elements 9–12.

**Fundamental invariant:**

$$
\boxed{tree[i]=\sum_{j=i-lowbit(i)+1}^{i}a[j].}
$$

| i | Binary | lowbit | Stored interval |
|---:|:---:|---:|---|
| 1 | 0001 | 1 | [1,1] |
| 2 | 0010 | 2 | [1,2] |
| 3 | 0011 | 1 | [3,3] |
| 4 | 0100 | 4 | [1,4] |
| 5 | 0101 | 1 | [5,5] |
| 6 | 0110 | 2 | [5,6] |
| 7 | 0111 | 1 | [7,7] |
| 8 | 1000 | 8 | [1,8] |
| 12 | 1100 | 4 | [9,12] |
| 13 | 1101 | 1 | [13,13] |

## 3. Derive the prefix query: i -= lowbit(i)

Want `sum(a[1..x])`. The interval stored at `tree[x]` is `[x-lowbit(x)+1,x]`, the **last block of that prefix**.

After adding it, the unprocessed prefix ends at `x-lowbit(x)`. Repeat. These disjoint blocks cover the requested prefix exactly, with no gaps or overlaps.

For `x=14`:

- `tree[14]` covers [13,14] (lowbit 2).
- `tree[12]` covers [9,12] (lowbit 4).
- `tree[8]` covers [1,8] (lowbit 8).
- Finish at index 0.

Thus `prefix_sum(14)=tree[14]+tree[12]+tree[8]`.

```python
def prefix_sum(self, i):
    total = 0
    while i > 0:
        total += self.tree[i]
        i -= i & -i
    return total
```

**Proof of termination and complexity:** Each subtraction clears the least significant set bit. A positive `n` has at most `floor(log2(n))+1` bits, so there are O(log n) iterations.

**Range sum:** `sum(l,r)=prefix_sum(r)-prefix_sum(l-1)`.

## 4. Derive the update: i += lowbit(i)

Suppose the original `a[p]` changes by `delta`. Every stored interval *containing position `p`* must change by `delta`.

Starting at node `p`, the **next** larger-indexed node whose interval contains `p` is `p+lowbit(p)`. Repeatedly adding the lowest set bit walks up the implicit parent chain.

**Why exactly this parent?** Write `i` in binary as a higher-bit prefix followed by its rightmost 1 and zeros. Adding `lowbit(i)` carries into a higher bit, producing an aligned block that contains the old block. Any index strictly between `i` and that parent has a lower lowbit and its block starts *after* `i`, so it cannot contain `i` (or the original updated position).

Example `p=7`, `n=16`:

- `tree[7]` covers [7,7].
- `tree[8]` covers [1,8].
- `tree[16]` covers [1,16].
- Next node 32 is out of range.

```python
def add(self, i, delta):
    while i <= self.n:
        self.tree[i] += delta
        i += i & -i
```

Each jump increases the position and yields O(log n) updates.

### Crucial indexing pitfall

The 1-based update loop must **never start at zero**: `lowbit(0)=0` would cause an infinite loop. Convert 0-based external indices with `i += 1`, or explicitly validate the index.

## 5. Build in O(n) instead of O(n log n)

Naive construction calls `add(i,a[i])` for every element, costing O(n log n). We can do better.

Initialize each `tree[i]` with its original element. Scan indices in **ascending order**; forward the completed block sum into its parent `i+lowbit(i)`.

```python
@classmethod
def from_values(cls, values):
    bit = cls(len(values))
    bit.tree[1:] = values

    for i in range(1, bit.n + 1):
        parent = i + (i & -i)
        if parent <= bit.n:
            bit.tree[parent] += bit.tree[i]
    return bit
```

**Invariant:** When processing `i`, all smaller-index children that contribute to `tree[i]` have already forwarded their completed sums. Thus `tree[i]` is complete before it is forwarded.

**Why not reverse the iteration?** With values [1,2,3,4], processing 4,3,2,1 sends the incomplete value of `tree[2]` to `tree[4]` before `tree[1]` contributes to `tree[2]`. The result would incorrectly be `tree[4]=9` rather than 10.

## 6. Range add + point query: one BIT on differences

Define the **1-based** difference array `d[1]=a[1]` and `d[i]=a[i]-a[i-1]` for `i≥2`.

Then `a[x]=sum(d[1..x])`. So a point query in the *original* array is a prefix query over differences.

An inclusive range addition `[l,r] += delta` is exactly:

$$
d[l]\mathrel{+}=\Delta,\qquad d[r+1]\mathrel{-}=\Delta
$$

(the latter is omitted if `r=n`).

A Fenwick Tree over `d` therefore supports O(log n) range adds and O(log n) point queries.

## 7. Range add + range sum: derive two BITs mathematically

Now we need `prefixA(x)=sum(a[1..x])` as well as range updates.

Substitute `a[i]=sum(d[1..i])`:

$$
\begin{aligned}
prefixA(x)
&=\sum_{i=1}^{x}\sum_{j=1}^{i}d[j]\\
&=\sum_{j=1}^{x}(x-j+1)d[j]\\
&=(x+1)\sum_{j=1}^{x}d[j]-\sum_{j=1}^{x}j\,d[j].
\end{aligned}
$$

Why does `d[j]` appear `x-j+1` times? It contributes to every `a[i]` where `j≤i≤x`.

This expression consists of **two separately maintainable prefix sums**:

- `BIT1` stores `d[j]`.
- `BIT2` stores `j*d[j]`.

Therefore:

$$
\boxed{prefixA(x)=(x+1)\cdot BIT1.prefix(x)-BIT2.prefix(x).}
$$

To apply `range_add(l,r,delta)`:

| Position | Change to BIT1 | Change to BIT2 |
|---|---:|---:|
| l | `+delta` | `+l*delta` |
| r+1 (when ≤n) | `-delta` | `-(r+1)*delta` |

**Important:** BIT2 must receive the **change in weighted difference**, not the entire existing value.

### Worked example

Start with `a=[0,0,0,0,0]`. Execute `range_add(2,4,3)`:

- Difference array becomes [0,3,0,0,-3].
- Weighted differences become [0,6,0,0,-15].
- `BIT1.prefix(4)=3`; `BIT2.prefix(4)=6`.
- `prefixA(4)=5*3-6=9`, matching `0+3+3+3`.
- `BIT1.prefix(5)=0`; `BIT2.prefix(5)=-9`, so `prefixA(5)=6*0-(-9)=9`.

No special case is needed when querying after the updated interval.

## 8. Full, working Python implementation

```python
class Fenwick:
    """1-based point-add, prefix-sum Fenwick Tree."""
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    @classmethod
    def from_values(cls, values):
        bit = cls(len(values))
        bit.tree[1:] = values
        for i in range(1, bit.n + 1):
            parent = i + (i & -i)
            if parent <= bit.n:
                bit.tree[parent] += bit.tree[i]
        return bit

    def add(self, i, delta):
        if not 1 <= i <= self.n:
            raise IndexError("Index out of bounds")
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, i):
        if not 0 <= i <= self.n:
            raise IndexError("Index out of bounds")
        total = 0
        while i:
            total += self.tree[i]
            i -= i & -i
        return total

    def range_sum(self, l, r):
        if not 1 <= l <= r <= self.n:
            raise IndexError("Range out of bounds")
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


class RangeAddPointQuery:
    def __init__(self, nums):
        diff = [x - (nums[i-1] if i else 0)
                for i, x in enumerate(nums)]
        self.bit = Fenwick.from_values(diff)
        self.n = len(nums)

    def range_add(self, l, r, delta):
        if not 1 <= l <= r <= self.n:
            raise IndexError("Range out of bounds")
        self.bit.add(l, delta)
        if r + 1 <= self.n:
            self.bit.add(r + 1, -delta)

    def point_query(self, i):
        return self.bit.prefix_sum(i)


class RangeAddRangeSum:
    def __init__(self, nums):
        diff = [x - (nums[i-1] if i else 0)
                for i, x in enumerate(nums)]
        self.n = len(nums)
        self.bit1 = Fenwick.from_values(diff)
        self.bit2 = Fenwick.from_values(
            [(i + 1) * d for i, d in enumerate(diff)]
        )

    def range_add(self, l, r, delta):
        if not 1 <= l <= r <= self.n:
            raise IndexError("Range out of bounds")
        self.bit1.add(l, delta)
        self.bit2.add(l, l * delta)
        if r + 1 <= self.n:
            self.bit1.add(r + 1, -delta)
            self.bit2.add(r + 1, -(r + 1) * delta)

    def prefix_sum(self, x):
        b1 = self.bit1.prefix_sum(x)
        b2 = self.bit2.prefix_sum(x)
        return (x + 1) * b1 - b2

    def range_sum(self, l, r):
        if not 1 <= l <= r <= self.n:
            raise IndexError("Range out of bounds")
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

    def point_query(self, i):
        return self.bit1.prefix_sum(i)


bit = Fenwick.from_values([2, 1, 3, 4, 5])
assert bit.range_sum(2, 4) == 8
bit.add(3, 7)
assert bit.range_sum(2, 4) == 15

rp = RangeAddPointQuery([1, 2, 3, 4, 5])
rp.range_add(2, 4, 3)
assert rp.point_query(3) == 6

rr = RangeAddRangeSum([1, 2, 3, 4, 5])
rr.range_add(2, 4, 3)
assert rr.range_sum(2, 4) == 18
assert rr.prefix_sum(4) == 19
```

Building each structure: O(n) time and space. Each update/query: O(log n).

## 9. Additional important uses and limitations

### Frequency tables / order statistics

If `tree` stores counts of discrete values, then `prefix_sum(v)` counts values up through index `v`. With coordinate compression, indices represent sorted distinct coordinate values, making a BIT effective for **inversion counts**, **count of smaller elements**, and **dynamic ranks**.

For an inversion count: scan values from right to left; query how many previously seen values have rank below the current one; then add 1 to the current rank. Compress values to ranks 1..m if they are large, negative, or sparse. Time O(n log n).

### Find the k-th frequency

If all frequencies are nonnegative, prefix sums are nondecreasing. Binary lifting through powers of two can find the smallest index whose prefix count reaches `k` in O(log n). This depends on monotonicity, not merely on using a BIT.

### Not a drop-in solution for every aggregation

The classic Fenwick structure excels when an invertible prefix aggregate (notably sum, XOR, count) lets you compute intervals from prefix values. Arbitrary point assignments require knowing the old value to compute `delta`. General mutable range minima/maxima and rich lazy range operations are usually simpler with a Segment Tree.

### Common bugs

1. Calling `add(0,delta)` with a 1-based implementation (infinite loop without validation).
2. Confusing a 0-based input list with 1-based BIT indices.
3. Using `prefix(r)-prefix(l)` rather than `prefix(r)-prefix(l-1)` for inclusive 1-based ranges.
4. Forgetting the right boundary cancellation at `r+1` in difference-array updates.
5. Weighting both BIT2 boundary updates by `l` instead of `l` and `r+1`.
6. Building by descending rather than ascending index in the O(n) push algorithm.
7. Assuming prefix minimum can be subtracted like prefix sum.

## 10. Frequently asked “why?” questions

**Q: Why is a Fenwick Tree called a tree when it is stored in an array?**  
A: The next-containing-block relation `parent(i)=i+lowbit(i)` forms implicit upward links. We never need explicit pointers.

**Q: Why does a query use subtraction and an update use addition?**  
A: A query *consumes* the current ending block and moves to the remaining prefix. An update must reach every *larger block containing* the modified position.

**Q: Why not store every power-of-two interval explicitly?**  
A: That is another valid family of decompositions, but the Fenwick arrangement uses only one canonical aligned block ending at each index: O(n) storage and simple bitwise navigation.

**Q: How do two BITs arise?**  
A: First express range additions as point changes to a difference array; then re-order a double sum to reveal two weighted prefix sums. The algebra dictates the data structures.

**Q: Does a Fenwick Tree require nonnegative values?**  
A: No for ordinary sums/updates. Nonnegative frequencies are required for monotone order-statistics queries such as “find the k-th count.”

## 11. Interview readiness and practice

Explain aloud, in order:

1. Why static prefixes fail under frequent point updates.
2. Why aligned power-of-two blocks provide O(log n) prefix decomposition.
3. Derive `tree[i]`'s exact interval; calculate lowbit(12), lowbit(13), and lowbit(14).
4. Reconstruct both traversals from interval containment, without memorized code.
5. Explain why O(n) construction must flow left to right.
6. Derive both difference-array variants and the two-BIT identity.

Practice: **LeetCode 307** (Range Sum Query – Mutable), **315** (Count of Smaller Numbers After Self), **493** (Reverse Pairs; careful with value thresholds), and **327** (Count of Range Sum).

Next: [Segment Tree](03-segment-tree.md) for arbitrary associative range aggregates and lazy propagation.

## References

- [CP-Algorithms: Fenwick Tree](https://cp-algorithms.com/data_structures/fenwick.html)
- [USACO Guide: Point Update Range Sum](https://usaco.guide/gold/PURS)
