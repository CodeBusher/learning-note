# Offline Sweeps — Remove One Dimension by Sorting

## 1. Range counts below a threshold

Given a static array, answer many queries `(l, r, t)`: how many elements in the inclusive index range `[l, r]` have value at most `t`?

```text
index: 0  1  2  3
a    : 5  1  4  2        queries: (0, 2, t=3) -> 1     (1, 3, t=4) -> 3
```

**Brute force:** scan `a[l..r]` for every query, O(nq).

**Observation.** Each query has two conditions: an index range and a value threshold. A [Fenwick tree](../04-range-queries/02-fenwick-tree.md) handles an index range quickly, if the elements that pass the threshold are marked 1 and the rest 0. Marking changes with `t`, but only in one direction: as `t` grows, elements switch on and never switch off. So sort the elements by value, sort the queries by `t`, and sweep `t` upward, switching elements on as `t` passes them. The value condition disappears into the sorting.

> **Invariant:** immediately before answering a query with threshold `t`, position i holds 1 exactly when `a[i] <= t`.

Elements in activation order: `(value, index) = (1, 1), (2, 3), (4, 2), (5, 0)`.

| Query (sorted by t) | Activated now | Marked positions | Count in `[l, r]` | Answer |
|---|---|---|---|---:|
| `t = 3`, `[0, 2]` | values 1, 2 → positions 1, 3 | `0 1 0 1` | positions 0..2 | 1 |
| `t = 4`, `[1, 3]` | value 4 → position 2 | `0 1 1 1` | positions 1..3 | 3 |

Activation uses `value <= t`, so all equal values switch on before the query. For a strict `< t` query, change that one comparison.

The Fenwick wrapper exposes a **0-based inclusive** `query(left, right)`, built from a helper `prefix(end)` that sums the half-open index prefix `[0, end)`.

```python
from random import Random


class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, index, delta):
        if not 0 <= index < self.n:
            raise IndexError("index out of bounds")
        index += 1
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def prefix(self, end):
        """Sum of half-open index prefix [0, end)."""
        if not 0 <= end <= self.n:
            raise IndexError("prefix endpoint out of bounds")
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total

    def query(self, left, right):
        """Inclusive array index range [left, right]."""
        return self.prefix(right + 1) - self.prefix(left)


def range_count_leq(nums, queries):
    """Each query is (left, right, threshold); [left, right] is inclusive."""
    for left, right, _ in queries:
        if not 0 <= left <= right < len(nums):
            raise IndexError("range out of bounds")
    items = sorted((value, i) for i, value in enumerate(nums))
    ordered_queries = sorted((threshold, left, right, qid)
                             for qid, (left, right, threshold) in enumerate(queries))
    bit = Fenwick(len(nums))
    answers = [0] * len(queries)
    next_item = 0
    for threshold, left, right, qid in ordered_queries:
        while next_item < len(items) and items[next_item][0] <= threshold:
            bit.add(items[next_item][1], 1)
            next_item += 1
        answers[qid] = bit.query(left, right)
    return answers


def main():
    assert range_count_leq([5, 1, 4, 2], [(0, 2, 3), (1, 3, 4)]) == [1, 3]
    assert range_count_leq([2, 2, -1], [(0, 2, 2), (0, 1, 1), (2, 2, -1)]) == [3, 0, 1]
    assert range_count_leq([], []) == []

    rng = Random(23)
    for _ in range(100):
        nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(1, 15))]
        queries = []
        for _ in range(15):
            left, right = sorted((rng.randrange(len(nums)), rng.randrange(len(nums))))
            queries.append((left, right, rng.randrange(-4, 5)))
        expected = [sum(v <= t for v in nums[l:r + 1]) for l, r, t in queries]
        assert range_count_leq(nums, queries) == expected


if __name__ == "__main__":
    main()
```

O((n + q) log(n + q)) time including the sorts, O(n + q) space. Each query carries its index `qid`, so answers return in the original order. This only works **offline**: if updates to `a` arrive between queries, sorting by `t` would break their time order.

## 2. Point counts in rectangles: sweep x, compress y

Given points `(x, y)`, count how many fall in each half-open rectangle `[x1, x2) × [y1, y2)`. Duplicate points count separately.

```text
points: (0,0) (1,1) (1,1) (2,2) (2,0)          rectangle [0,2) x [0,2) -> 3
```

**Brute force:** test every point against every rectangle, O(nq).

**Observation.** Now there are two coordinate conditions. Sweep x to remove one of them, as §1 removed the threshold. Let

$$F(X, y_1, y_2) = \#\{\text{points with } x < X \text{ and } y_1 \le y < y_2\}.$$

Then the rectangle's count is `F(x2, y1, y2) − F(x1, y1, y2)`. Each rectangle becomes two query events on the x-axis: sign `+1` at `x2` and `−1` at `x1`. Sweep x upward; before a query at X, insert every point with `x < X` into a Fenwick tree indexed by y. The query then asks for a y-range count.

**Compression.** y-values can be huge or negative, so index the tree by **rank**: `ys` is the sorted list of distinct point y-values, and `bisect_left(ys, Y)` is the number of distinct values below Y. The tree prefix of that length counts all points with `y < Y`, including duplicates. Query boundaries do not need to appear in `ys`.

For the rectangle above, `ys = [0, 1, 2]`:

| Event | Points inserted (`x < X`) | Count with `0 <= y < 2` | Contribution |
|---|---|---:|---:|
| `x1 = 0`, sign −1 | none | 0 | 0 |
| `x2 = 2`, sign +1 | `(0,0)`, `(1,1)`, `(1,1)` | 3 | +3 |

`(2, 0)` and `(2, 2)` lie on the right boundary `x = 2`. The strict `x < X` keeps them out, as the half-open rectangle requires.

```python
from bisect import bisect_left
from random import Random


class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, index, delta):
        index += 1
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def prefix(self, end):
        """Sum of half-open index prefix [0, end)."""
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total


def count_points_in_rectangles(points, rectangles):
    """Rectangles [x1, x2) x [y1, y2); duplicate points count separately."""
    events = []
    answers = [0] * len(rectangles)
    for qid, (x1, y1, x2, y2) in enumerate(rectangles):
        if x1 > x2 or y1 > y2:
            raise ValueError("reversed rectangle")
        if x1 == x2 or y1 == y2:
            continue
        events.append((x2, 1, y1, y2, qid))
        events.append((x1, -1, y1, y2, qid))
    ordered_points = sorted(points)
    ys = sorted({y for _, y in points})
    bit = Fenwick(len(ys))
    point_index = 0
    for x_limit, sign, y1, y2, qid in sorted(events):
        while point_index < len(ordered_points) and ordered_points[point_index][0] < x_limit:
            _, y = ordered_points[point_index]
            bit.add(bisect_left(ys, y), 1)
            point_index += 1
        below_y2 = bit.prefix(bisect_left(ys, y2))
        below_y1 = bit.prefix(bisect_left(ys, y1))
        answers[qid] += sign * (below_y2 - below_y1)
    return answers


def main():
    points = [(0, 0), (1, 1), (1, 1), (2, 2), (2, 0)]
    rectangles = [(0, 0, 2, 2), (1, 1, 2, 2), (2, 0, 3, 3),
                  (0, 0, 0, 4), (-10, -10, 10, 10)]
    assert count_points_in_rectangles(points, rectangles) == [3, 2, 2, 0, 5]
    assert count_points_in_rectangles([], rectangles) == [0] * len(rectangles)

    rng = Random(29)
    for _ in range(100):
        pts = [(rng.randrange(-3, 4), rng.randrange(-3, 4)) for _ in range(15)]
        rects = []
        for _ in range(15):
            x1, x2 = sorted((rng.randrange(-4, 5), rng.randrange(-4, 5)))
            y1, y2 = sorted((rng.randrange(-4, 5), rng.randrange(-4, 5)))
            rects.append((x1, y1, x2, y2))
        expected = [sum(x1 <= x < x2 and y1 <= y < y2 for x, y in pts)
                    for x1, y1, x2, y2 in rects]
        assert count_points_in_rectangles(pts, rects) == expected


if __name__ == "__main__":
    main()
```

n insertions and 2q queries, each O(log n), plus the sorts: O((n + q) log(n + q)) time, O(n + q) space.

For closed integer rectangles, convert the upper bounds to `x2 + 1` and `y2 + 1` first.

**Compression keeps order, not distance.** Values `10, 20, 1000000` get ranks `0, 1, 2`. A count only needs the order, so ranks suffice. An area or a length does not: the gap from 20 to 1000000 is still 999980, which is why the area sweep in [Geometric Sweeps](06-geometric-sweeps.md#2-the-coverage-tree-compress-gaps-not-endpoints) keeps the real coordinates.

## 3. A heap instead of a Fenwick tree: smallest interval containing each query

Given closed intervals `[l, r]` and query points, find for each query the **length** `r − l` of the shortest interval containing it, or `None` if no interval does.

```text
intervals: [1,4] [2,4] [3,6] [4,4]       queries: 2 3 4 5  ->  2 2 0 3
```

A count cannot answer "shortest". Sweep the queries in increasing order, as before. An interval becomes a candidate once the sweep reaches its start, and stays valid until the sweep passes its end. Among the started intervals we want the shortest one that has not ended, so keep them in a min-heap of `(length, end)`.

Removing an ended interval from the middle of a heap is expensive. Instead remove it **lazily**: before answering, pop the top while the top has ended. An ended interval buried deeper does no harm until it reaches the top. Queries only increase, so an interval that has ended never becomes valid again.

> **Invariant:** before answering query q, the heap holds every interval with `l <= q`, and its top, if any, has `r >= q`.

| Query | Pushed now `(length, end)` | Popped (ended before q) | Top | Answer |
|---:|---|---|---|---:|
| 2 | `(3,4)`, `(2,4)` | — | `(2,4)` | 2 |
| 3 | `(3,6)` | — | `(2,4)` | 2 |
| 4 | `(0,4)` | — | `(0,4)` | 0 |
| 5 | — | `(0,4)`, `(2,4)`, `(3,4)` | `(3,6)` | 3 |

At query 4 the interval `[4, 4]` still counts: closed intervals contain their end, so only `end < q` is popped.

```python
from heapq import heappop, heappush
from random import Random


def smallest_containing_interval(intervals, queries):
    """Closed [l, r]; returns r - l of the shortest interval containing each query."""
    for left, right in intervals:
        if left > right:
            raise ValueError("reversed interval")
    by_start = sorted(intervals)
    heap = []
    answers = [None] * len(queries)
    next_interval = 0
    for q, qid in sorted((q, i) for i, q in enumerate(queries)):
        while next_interval < len(by_start) and by_start[next_interval][0] <= q:
            left, right = by_start[next_interval]
            heappush(heap, (right - left, right))
            next_interval += 1
        while heap and heap[0][1] < q:  # closed: an interval ending at q still counts
            heappop(heap)
        if heap:
            answers[qid] = heap[0][0]
    return answers


def main():
    intervals = [(1, 4), (2, 4), (3, 6), (4, 4)]
    assert smallest_containing_interval(intervals, [2, 3, 4, 5]) == [2, 2, 0, 3]
    assert smallest_containing_interval([(2, 3), (2, 5), (1, 8), (20, 25)],
                                        [2, 19, 5, 22]) == [1, None, 3, 5]
    assert smallest_containing_interval([], [1]) == [None]

    rng = Random(67)
    for _ in range(300):
        intervals = [tuple(sorted((rng.randrange(0, 10), rng.randrange(0, 10))))
                     for _ in range(rng.randrange(8))]
        queries = [rng.randrange(-1, 11) for _ in range(8)]
        expected = [min((r - l for l, r in intervals if l <= q <= r), default=None)
                    for q in queries]
        assert smallest_containing_interval(intervals, queries) == expected


if __name__ == "__main__":
    main()
```

Each interval is pushed and popped at most once: O(n log n + q log q) time, O(n + q) space.

## 4. Sweep over positions: count smaller elements to the right

For each index i, count the indices j > i with `a[j] < a[i]`. Summing the counts gives the number of **inversions**.

This time the sweep runs over **positions**, from right to left, and the Fenwick tree is indexed by compressed **values**. When the sweep reaches i, the tree holds exactly the elements to its right. The answer for i is the number of stored values strictly below `a[i]`: a prefix count up to the rank of `a[i]`, with `bisect_left` so that equal values are excluded.

`a = [5, 2, 6, 1]`, distinct sorted values `[1, 2, 5, 6]` with ranks 0–3:

| i | `a[i]` | Rank | Stored ranks before | Stored ranks `< rank` | Answer |
|---:|---:|---:|---|---:|---:|
| 3 | 1 | 0 | — | 0 | 0 |
| 2 | 6 | 3 | 0 | 1 | 1 |
| 1 | 2 | 1 | 0, 3 | 1 | 1 |
| 0 | 5 | 2 | 0, 3, 1 | 2 | 2 |

Compare with §1: there, sorting by value decided which elements were eligible and the tree answered a question about positions. Here, scanning positions decides eligibility and the tree answers a question about values. Either dimension can be the sweep.

```python
from bisect import bisect_left
from random import Random


class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, index, delta):
        index += 1
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def prefix(self, end):
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total


def count_smaller_to_the_right(nums):
    values = sorted(set(nums))
    bit = Fenwick(len(values))
    counts = [0] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        rank = bisect_left(values, nums[i])
        counts[i] = bit.prefix(rank)  # stored values with smaller rank
        bit.add(rank, 1)
    return counts


def main():
    assert count_smaller_to_the_right([5, 2, 6, 1]) == [2, 1, 1, 0]
    assert count_smaller_to_the_right([2, 2, 1]) == [1, 1, 0]
    assert count_smaller_to_the_right([]) == []

    rng = Random(71)
    for _ in range(200):
        nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(12))]
        expected = [sum(nums[j] < nums[i] for j in range(i + 1, len(nums)))
                    for i in range(len(nums))]
        assert count_smaller_to_the_right(nums) == expected


if __name__ == "__main__":
    main()
```

Time O(n log n), space O(n).

## 5. Horizontal–vertical segment intersections

Count the intersecting pairs between horizontal segments `(x1, x2, y)` and vertical segments `(x, y1, y2)`. All segments are **closed**, so touching at an endpoint counts.

Sweep x. A horizontal segment is active from `x1` through `x2`; its y-value goes into a Fenwick tree over compressed y-values while it is active. A vertical segment at x is a **query**: how many active y-values lie in `[y1, y2]`? Closed segments need the closed order from [Endpoint Semantics §2](02-endpoint-semantics-and-queries.md#2-the-processing-order-rule): at each x, **add starts, answer queries, then remove ends**. Encoding the event kind as 0, 1, 2 makes tuple sorting produce that order.

Horizontals `[0,4]` at y=1, `[2,6]` at y=3, `[5,7]` at y=0; verticals at x = 1 (`[0,2]`), 4 (`[1,3]`), 6 (`[3,5]`), 8 (`[0,9]`):

| Query at x | Active horizontals' y (added at `x1 <= x`, removed after `x2 < x`) | Count in `[y1, y2]` | Total |
|---|---|---:|---:|
| 1, `[0,2]` | {1} | 1 | 1 |
| 4, `[1,3]` | {1, 3} | 2 | 3 |
| 6, `[3,5]` | {3, 0} | 1 | 4 |
| 8, `[0,9]` | {} | 0 | 4 |

At x = 4 the horizontal `[0, 4]` ends exactly where a vertical stands. The query runs before the removal, so the touching pair counts.

```python
from bisect import bisect_left, bisect_right
from random import Random


class Fenwick:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, index, delta):
        index += 1
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def prefix(self, end):
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total


ADD, QUERY, REMOVE = 0, 1, 2  # closed segments: add, then query, then remove


def count_hv_intersections(horizontals, verticals):
    """Closed horizontals (x1, x2, y) and verticals (x, y1, y2)."""
    events = []
    for x1, x2, y in horizontals:
        if x1 > x2:
            raise ValueError("reversed segment")
        events.append((x1, ADD, y, None))
        events.append((x2, REMOVE, y, None))
    for x, y1, y2 in verticals:
        if y1 > y2:
            raise ValueError("reversed segment")
        events.append((x, QUERY, y1, y2))
    ys = sorted({y for _, _, y in horizontals})
    bit = Fenwick(len(ys))
    total = 0
    for _, kind, a, b in sorted(events, key=lambda e: (e[0], e[1])):
        if kind == ADD:
            bit.add(bisect_left(ys, a), 1)
        elif kind == REMOVE:
            bit.add(bisect_left(ys, a), -1)
        else:  # y in [a, b], inclusive on both sides
            total += bit.prefix(bisect_right(ys, b)) - bit.prefix(bisect_left(ys, a))
    return total


def main():
    horizontals = [(0, 4, 1), (2, 6, 3), (5, 7, 0)]
    verticals = [(1, 0, 2), (4, 1, 3), (6, 3, 5), (8, 0, 9)]
    assert count_hv_intersections(horizontals, verticals) == 4
    assert count_hv_intersections([(0, 2, 0)], [(2, 0, 0)]) == 1  # touching corners
    assert count_hv_intersections([], [(0, 0, 1)]) == 0

    rng = Random(73)
    for _ in range(300):
        hs = [(*sorted((rng.randrange(0, 6), rng.randrange(0, 6))), rng.randrange(0, 6))
              for _ in range(rng.randrange(7))]
        vs = [(rng.randrange(0, 6), *sorted((rng.randrange(0, 6), rng.randrange(0, 6))))
              for _ in range(rng.randrange(7))]
        expected = sum(x1 <= x <= x2 and y1 <= y <= y2
                       for x1, x2, y in hs for x, y1, y2 in vs)
        assert count_hv_intersections(hs, vs) == expected


if __name__ == "__main__":
    main()
```

2h + v events, each O(log h): O((h + v) log(h + v)) time, O(h + v) space. *Reporting* every pair instead of counting costs O(k) more for k pairs, and k can be as large as h·v.

## 6. Summary

| Problem | Sweep coordinate | Never expires? | State | Section |
|---|---|---|---|---|
| Range counts `a[i] <= t` | Threshold t | Yes | Fenwick over positions | §1 |
| Points in rectangles | x | Yes | Fenwick over compressed y | §2 |
| Shortest interval containing a point | Query point | No: lazy pops | Min-heap by length | §3 |
| Count smaller to the right | Position, right to left | Yes | Fenwick over compressed values | §4 |
| Horizontal–vertical intersections | x | No: explicit remove | Fenwick over compressed y | §5 |

The recipe in all of them: sort by one dimension to decide **which objects are eligible**, and let a data structure answer the question about **the remaining dimension**. A count needs a Fenwick tree; a minimum or maximum among eligible objects needs a heap with lazy expiration. For static one-dimensional range sums with no threshold, plain prefix sums are enough.

## 7. Pitfalls and practice

1. Answering in sorted order but returning answers in that order instead of by query index.
2. Using `<` instead of `<=` for activation (or the reverse), which drops or adds elements equal to the threshold.
3. Deduplicating the point multiset. Deduplicate only the list used for compression.
4. Measuring distances with compressed ranks.
5. Using an offline sweep when updates are interleaved with queries.
6. Removing ended intervals from the middle of a heap instead of popping lazily from the top.

Practice: array range counts above a threshold; minimum interval to include each query; count of smaller numbers after self; reverse pairs; count dominated points; weighted points in rectangles; horizontal–vertical segment intersections with open instead of closed endpoints.

Next: [Geometric Sweeps](06-geometric-sweeps.md).
