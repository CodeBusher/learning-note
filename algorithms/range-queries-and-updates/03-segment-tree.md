# Segment Tree — From Interval Decomposition to Lazy Propagation

> Study sequence: [Prefix Sums](01-prefix-sums.md) → [Fenwick Tree](02-fenwick-tree.md) → **Segment Tree**  
> **Learning goal:** Reconstruct the tree, query logic, and lazy-update invariant from first principles instead of memorizing recursive templates.

## 1. Why invent a Segment Tree?

We have an array and must answer online interval queries while values change. Prefix sums offer O(1) interval sums but O(n) point updates; Fenwick Trees handle dynamic sums elegantly.

**New challenge:** What if we want minimum, maximum, greatest common divisor (GCD), or a more complex aggregate? For minimum, `min(prefix(r))` and `min(prefix(l-1))` cannot be subtracted to recover `min(l..r)`.

The key is to keep **aggregates of intervals**, and combine disjoint intervals to answer queries.

| Structure | Typical range sum | Point change | General range min/max | Lazy range add + sum |
|---|---|---|---|---|
| Static prefix sums | O(1) | O(n) | Not from two prefix minima | No |
| Fenwick Tree | O(log n) | O(log n) | Not with basic BIT | Requires specialized variants |
| Segment Tree | O(log n) | O(log n) | **Yes, O(log n)** | **Yes, O(log n)** |

## 2. Invent the binary interval decomposition

Given `a[0..n-1]`, represent the whole interval `[0,n-1]` at the root.

Split it in two: `[0,mid]` and `[mid+1,n-1]`. Continue recursively until each leaf stores one element.

For `n=8`:

```text
                       [0..7]
                     /        \
                 [0..3]      [4..7]
                /     \      /     \
             [0..1] [2..3] [4..5] [6..7]
              /  \    /  \   /  \    /  \
             0    1  2    3 4    5 6    7
```

At every node maintain one invariant:

$$
\boxed{tree[node]=\operatorname{aggregate}(a[l..r]).}
$$

For sums, `aggregate` means addition; for min, it means minimum.

Because children form a disjoint partition of their parent's interval:

$$
tree[node]=combine(tree[left],tree[right]).
$$

This works when `combine` is **associative**: `combine(combine(a,b),c)=combine(a,combine(b,c))`.

Examples:

| Aggregate | combine(x,y) | Identity for empty interval |
|---|---|---|
| Sum | x+y | 0 |
| Minimum | min(x,y) | +infinity |
| Maximum | max(x,y) | -infinity |
| GCD | gcd(x,y) | 0 |
| Product | x*y | 1 |
| String concatenation | x+y | empty string |

An identity satisfies `combine(x,identity)=combine(identity,x)=x`. For noncommutative operations such as concatenation, preserve **left-to-right order**.

## 3. Derive interval querying from overlap

Ask for aggregate over an inclusive interval `[ql,qr]`. At a node representing `[l,r]`, exactly three cases exist.

1. **No overlap:** its interval does not contribute. Return the identity.
2. **Complete overlap:** its stored aggregate already answers the contribution. Return it immediately.
3. **Partial overlap:** recursively query the children and combine their results.

The third case must recurse because the node's entire interval includes values outside the query.

Example: query sum `[2,6]` in an 8-element array:

- Left half `[0,3]` contributes its `[2,3]` node.
- Right half `[4,7]` contributes `[4,5]` and `[6,6]`.
- Add the three stored values.

We can skip whole subtrees. At each depth, at most two partially intersecting boundary nodes require expansion; fully covered middle intervals are accepted immediately. A balanced tree has O(log n) levels, so range querying is **O(log n)**.

## 4. Derive point update

To assign a new value at index `i`:

1. Descend to the single leaf for `i`.
2. Replace its stored value.
3. On the way back, recompute every ancestor from its two children.

Only one root-to-leaf path changes, hence O(log n).

The distinction from a Fenwick Tree: a Segment Tree stores an **explicit recursive partition**, while a Fenwick Tree stores one special aligned block at each array index.

## 5. Complete generic implementation (0-based, inclusive)

```python
from math import inf, gcd

class SegmentTree:
    """General point assignment + inclusive interval aggregate."""
    def __init__(self, values, combine, identity):
        self.n = len(values)
        self.combine = combine
        self.identity = identity
        self.tree = [identity] * (4 * max(1, self.n))
        if self.n:
            self._build(1, 0, self.n - 1, values)

    def _build(self, node, l, r, values):
        if l == r:
            self.tree[node] = values[l]
            return
        mid = (l + r) // 2
        self._build(node * 2, l, mid, values)
        self._build(node * 2 + 1, mid + 1, r, values)
        self.tree[node] = self.combine(
            self.tree[node * 2], self.tree[node * 2 + 1]
        )

    def set(self, index, value):
        if not 0 <= index < self.n:
            raise IndexError("Index out of bounds")
        self._set(1, 0, self.n - 1, index, value)

    def _set(self, node, l, r, index, value):
        if l == r:
            self.tree[node] = value
            return
        mid = (l + r) // 2
        if index <= mid:
            self._set(node * 2, l, mid, index, value)
        else:
            self._set(node * 2 + 1, mid + 1, r, index, value)
        self.tree[node] = self.combine(
            self.tree[node * 2], self.tree[node * 2 + 1]
        )

    def query(self, ql, qr):
        if not 0 <= ql <= qr < self.n:
            raise IndexError("Range out of bounds")
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node, l, r, ql, qr):
        if qr < l or r < ql:       # no overlap
            return self.identity
        if ql <= l and r <= qr:    # complete overlap
            return self.tree[node]

        mid = (l + r) // 2        # partial overlap
        left = self._query(node * 2, l, mid, ql, qr)
        right = self._query(node * 2 + 1, mid + 1, r, ql, qr)
        return self.combine(left, right)


nums = [2, 1, 3, 4, 5, 6, 7, 8]
sums = SegmentTree(nums, lambda x, y: x + y, 0)
assert sums.query(2, 6) == 25
sums.set(3, 10)
assert sums.query(2, 6) == 31

mins = SegmentTree(nums, min, inf)
assert mins.query(2, 6) == 3

gc = SegmentTree([6, 9, 15], gcd, 0)
assert gc.query(0, 2) == 3
```

Build: O(n). Point assignment: O(log n). Query: O(log n). Memory: O(n); the common recursive allocation `4*n` is a safe upper bound, not an exact node count.

## 6. Why basic point updates are not enough for range additions

Suppose you must execute `range_add(l,r,delta)` and `range_sum(l,r)` frequently. Repeating a point update for every affected element takes O(n log n) in the worst case.

We need to update a **whole stored interval** without descending to its leaves each time.

If a node represents `[l,r]` and every element within it increases by `delta`, its sum changes by:

$$
\boxed{delta\times(r-l+1).}
$$

That is enough to update this node's stored sum immediately. But what about its children? They have not changed yet.

This suggests **lazy propagation**.

## 7. Derive lazy propagation from its invariant

Maintain two arrays:

- `tree[node]`: the correct sum of the node's current interval, accounting for all updates.
- `lazy[node]`: an addition still waiting to be propagated to descendants.

### Apply an update to an entire node

For interval `[l,r]` and addition `delta`:

```python
tree[node] += delta * (r - l + 1)
lazy[node] += delta
```

**Why multiply by length?** Every element in the interval changes by `delta`.

### Push before descending

If we later need to examine a child, propagate the parent's pending addition to both children, adjusting each child's stored sum according to its interval length. Then clear the parent's lazy marker.

**Core invariant:** The parent sum is always correct, even when its children's sums are temporarily missing a pending addition.

For **range add**, tags compose by addition. For **range assignment**, tags compose differently: a new assignment overrides previous assignments. Mixing assign/add tags requires carefully defined composition and precedence.

## 8. Complete lazy-propagation implementation: range add + range sum

```python
class LazyRangeSum:
    """0-based inclusive range_add and range_sum."""
    def __init__(self, values):
        self.n = len(values)
        size = 4 * max(1, self.n)
        self.tree = [0] * size
        self.lazy = [0] * size
        if self.n:
            self._build(1, 0, self.n - 1, values)

    def _build(self, node, l, r, values):
        if l == r:
            self.tree[node] = values[l]
            return
        mid = (l + r) // 2
        self._build(node * 2, l, mid, values)
        self._build(node * 2 + 1, mid + 1, r, values)
        self.tree[node] = self.tree[node * 2] + self.tree[node * 2 + 1]

    def _apply(self, node, l, r, delta):
        self.tree[node] += delta * (r - l + 1)
        self.lazy[node] += delta

    def _push(self, node, l, r):
        if self.lazy[node] == 0 or l == r:
            return
        mid = (l + r) // 2
        delta = self.lazy[node]
        self._apply(node * 2, l, mid, delta)
        self._apply(node * 2 + 1, mid + 1, r, delta)
        self.lazy[node] = 0

    def range_add(self, ql, qr, delta):
        if not 0 <= ql <= qr < self.n:
            raise IndexError("Range out of bounds")
        self._add(1, 0, self.n - 1, ql, qr, delta)

    def _add(self, node, l, r, ql, qr, delta):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self._apply(node, l, r, delta)
            return
        self._push(node, l, r)
        mid = (l + r) // 2
        self._add(node * 2, l, mid, ql, qr, delta)
        self._add(node * 2 + 1, mid + 1, r, ql, qr, delta)
        self.tree[node] = self.tree[node * 2] + self.tree[node * 2 + 1]

    def range_sum(self, ql, qr):
        if not 0 <= ql <= qr < self.n:
            raise IndexError("Range out of bounds")
        return self._sum(1, 0, self.n - 1, ql, qr)

    def _sum(self, node, l, r, ql, qr):
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return self.tree[node]
        self._push(node, l, r)
        mid = (l + r) // 2
        return (
            self._sum(node * 2, l, mid, ql, qr)
            + self._sum(node * 2 + 1, mid + 1, r, ql, qr)
        )


st = LazyRangeSum([1, 2, 3, 4, 5])
st.range_add(1, 3, 3)
assert st.range_sum(1, 3) == 18
assert st.range_sum(0, 4) == 24
st.range_add(0, 4, -2)
assert st.range_sum(0, 4) == 14
assert st.range_sum(2, 2) == 4
```

Each range update and range query is O(log n), with O(n) construction and storage.

## 9. Worked trace of a lazy update

Start with eight zeros. Execute `range_add(0,7,3)`.

- The root covers [0,7]; its sum becomes 24.
- Its lazy tag becomes +3.
- We **do not** visit its children yet.

Now query `range_sum(2,3)`:

1. Root overlaps partially; push +3 to children [0,3] and [4,7], clearing the root tag.
2. Node [0,3] overlaps partially; push +3 to [0,1] and [2,3].
3. Node [2,3] overlaps completely: return stored sum 6 immediately.
4. Other branches return identity 0.

Every visited node's aggregate was updated correctly before being used.

### Common misconception: why not just store a lazy tag?

If `tree[node]` were left stale, a full-cover query could not return its sum immediately. The point of lazy propagation is to keep the current node's aggregate correct while deferring the lower-level work.

## 10. Segment Tree variations and how to choose

| Requirement | Suggested structure | Why |
|---|---|---|
| Static range sum | Prefix sum | O(1) query, simpler |
| Dynamic point update + sum | Fenwick Tree | Less code and memory |
| Dynamic point update + min/max/GCD | Segment Tree | Associative merge |
| Range add + point query | Difference-array Fenwick | Compact |
| Range add + range sum | Two Fenwick Trees **or** lazy Segment Tree | Both O(log n) |
| Range add + range minimum | Lazy Segment Tree | Min increases by delta on full-cover nodes |
| Range assignment + range sum | Lazy Segment Tree | Assignment tags override older tags |
| Find first position whose accumulated count reaches k | Fenwick binary lifting or Segment Tree descent | Needs monotone/nonnegative counts |
| Huge sparse coordinate domain | Dynamic Segment Tree | Allocate nodes as needed |
| Historical versions / immutable snapshots | Persistent Segment Tree | Path-copy changed nodes |
| Static range min, no updates | Sparse Table | O(1) query after O(n log n) preprocessing |

Other common variations include iterative bottom-up segment trees, merge-sort trees (sorted lists per node, typical O(log² n) count query), segment trees storing maximum subarray-sum summaries (sum, best prefix/suffix/subarray), and segment-tree beats (advanced conditional range modifications).

### Example: maximum subarray sum in a node

Store a four-field summary:
- `total`: sum of the interval.
- `pref`: maximum nonempty prefix sum.
- `suff`: maximum nonempty suffix sum.
- `best`: maximum nonempty subarray sum.

To merge left `L` and right `R`:

$$
total=L.total+R.total
$$
$$
pref=\max(L.pref,\ L.total+R.pref)
$$
$$
suff=\max(R.suff,\ R.total+L.suff)
$$
$$
best=\max(L.best,\ R.best,\ L.suff+R.pref)
$$

**Why?** Any best subarray lies wholly in the left child, wholly in the right child, or crosses the split as a left suffix plus a right prefix. This is an example of how *inventing a compact mergeable summary* makes Segment Trees powerful.

## 11. Why it works: correctness summary

**Build (induction on interval length):** A leaf stores its element. If both children store the correct aggregate, combining them yields the parent's correct aggregate by associativity. Thus the root and all nodes are correct.

**Query (induction on recursive overlap):** No overlap contributes the identity; complete overlap returns the maintained aggregate; partial overlap splits into disjoint subqueries whose results combine correctly.

**Point update:** Only ancestors of the changed leaf can differ; recomputing them in reverse path order re-establishes the invariant.

**Lazy update:** Full-coverage changes are reflected immediately in the current aggregate, while tags record the equivalent deferred transformations for children. Pushing maintains the same logical array while allowing correct deeper queries and updates.

## 12. Interview Q&A and edge cases

**Q: Why O(log n), not O(n), for arbitrary interval queries?**  
A: Each level has at most two boundary regions that need further splitting. Fully covered interior regions stop immediately, and the tree's height is logarithmic.

**Q: Do we need to pad n to a power of two?**  
A: Not for the recursive implementation above. Some iterative layouts do pad; it simplifies indexing.

**Q: Why do we return infinity for a disjoint minimum-query node?**  
A: Because `min(x,+infinity)=x`. Returning 0 would corrupt results whenever values are positive (and can also fail with negatives).

**Q: Does every associative operation support lazy range add?**  
A: No. You must define how a range update changes a node's aggregate *without visiting all elements*, and how pending update tags compose. Sum+add and min+add are straightforward; arbitrary operations may not be.

**Q: Why do range assignment and range addition need different tags?**  
A: Addition composes by summing deltas. Assignment overwrites earlier pending assignments and additions, so a marker for “set to 0” cannot be represented by simply storing zero as “no tag.”

**Q: Which data structure should I choose in a Google SWE interview?**  
A: Clarify update and query types first. Prefer a simple prefix sum for static sums, BIT for dynamic sums, and Segment Tree when the interval aggregate or update operation requires greater flexibility. State the invariant before writing code.

**Q: What are common mistakes?**  
A: Confusing inclusive/half-open ranges; wrong identity; forgetting to pull after point updates or partial range updates; forgetting to push before descending; treating a zero assignment as “no pending assignment”; insufficient tree allocation; not preserving order for noncommutative merges; and assuming range-add lazy tags apply to every aggregate.

## 13. Practice roadmap

1. **LeetCode 307 — Range Sum Query: Mutable:** implement both BIT and Segment Tree; compare their invariants.
2. **LeetCode 315 — Count of Smaller Numbers After Self:** coordinate compression + BIT or Segment Tree frequencies.
3. **LeetCode 699 — Falling Squares:** coordinate compression + lazy range assignment/range maximum.
4. **LeetCode 729 — My Calendar I:** consider ordered intervals first; discuss when a segment tree is overkill.
5. **LeetCode 732 — My Calendar III:** dynamic range-increment and global maximum; compare sweep-line/difference map and dynamic Segment Tree.
6. **LeetCode 53 — Maximum Subarray:** use the four-value merge summary to design a Segment Tree variant.

## 14. One-page mental model

- **Prefix sum:** store every cumulative total; static range sums become subtraction.
- **Fenwick Tree:** store selected aligned ending blocks; bitwise parent navigation supports dynamic prefix sums.
- **Segment Tree:** explicitly divide the full interval into mergeable child intervals; arbitrary associative aggregates can be queried and recomputed.
- **Lazy propagation:** maintain correct summaries for whole updated intervals, but postpone descendant updates until necessary.

**Study sequence:** derive the segment node invariant → trace a partial-overlap query → implement point updates → derive lazy tags from the effect of adding to an entire interval → verify tag composition.

## References

- [CP-Algorithms: Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html)
- [USACO Guide: Range Queries](https://usaco.guide/gold/PURS)
- [LeetCode 307](https://leetcode.com/problems/range-sum-query-mutable/)
