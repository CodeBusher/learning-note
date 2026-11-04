# Endpoint Semantics — Ties, Closed Intervals, and Point Queries

## 1. One coordinate, three meanings

Two intervals meet at 3. Write them three ways:

| Kind | Intervals | At x = 3 | Count at 3 | Union length |
|---|---|---|---:|---:|
| Half-open | `[1, 3)`, `[3, 6)` | First has left, second has arrived | 1 | 5 |
| Closed | `[1, 3]`, `[3, 6]` | Both contain 3 | **2** | 5 |
| Open | `(1, 3)`, `(3, 6)` | Neither contains 3 | **0** | 5 |

The events at 3 are the same in every row: one end and one start. The union length is the same too, because a single point has zero length. Only the **count at 3** differs. Lengths do not care about endpoint ties; point counts do, and the maximum overlap is a point count.

[Your First Sweep](01-first-sweep-intervals.md#what-happens-exactly-at-7) applied all changes at a coordinate as one net change. That is right for the first row and wrong for the other two.

## 2. The processing-order rule

Split the work at x into three steps: add the intervals starting at x, remove those ending at x, and read the count. Each row of §1 puts the read in a different place:

| Interval semantics | Active at its own endpoint x? | Order of work at x |
|---|---|---|
| Half-open `[l, r)` | Start yes, end no | Remove ends, add starts, then read |
| Closed `[l, r]` | Start yes, end yes | Add starts, read, then remove ends |
| Open `(l, r)` | Start no, end no | Remove ends, read, then add starts |

For half-open intervals both changes come before the read, so they may be added into one net change. For closed intervals the read sits between them, and a net change skips the moment when both are active.

Two degenerate cases:

- An empty half-open interval such as `[4, 4)` contains no point. Skip it before creating events.
- A closed singleton `[4, 4]` contains the point 4. It has length 0, but it can still raise the maximum count at 4.

## 3. Closed continuous intervals: maximum overlap

Intervals: `[1, 3]`, `[3, 6]`, `[3, 3]`. Keep starts and ends in separate tables, because the order of work needs them apart.

| x | Starts at x | Ends at x | `active` before | After adding starts | Read: max so far | After removing ends |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 | 1 | 1 | 1 |
| 3 | 2 | 2 | 1 | **3** | 3 | 1 |
| 6 | 0 | 1 | 1 | 1 | 3 | 0 |

At x = 3 all three intervals contain the point 3: `[1, 3]` by its right end, `[3, 6]` by its left end, and the singleton. The count 3 exists only between the add and the remove, which is where the read happens.

```python
from random import Random


def maximum_closed_overlap(intervals):
    """Closed continuous [l, r], including singleton point intervals."""
    starts = {}
    ends = {}
    for left, right in intervals:
        if left > right:
            raise ValueError("reversed interval")
        starts[left] = starts.get(left, 0) + 1
        ends[right] = ends.get(right, 0) + 1
    active = maximum = 0
    for x in sorted(starts.keys() | ends.keys()):
        active += starts.get(x, 0)
        maximum = max(maximum, active)
        active -= ends.get(x, 0)
    return maximum


def main():
    assert maximum_closed_overlap([(1, 3), (3, 6), (3, 3)]) == 3
    assert maximum_closed_overlap([(1, 3), (3, 6)]) == 2
    assert maximum_closed_overlap([(1, 2), (2, 3)]) == 2
    assert maximum_closed_overlap([(2, 2), (2, 2), (1, 3)]) == 3
    assert maximum_closed_overlap([]) == 0

    rng = Random(5)
    for _ in range(300):
        intervals = [tuple(sorted((rng.randrange(-4, 5), rng.randrange(-4, 5))))
                     for _ in range(rng.randrange(8))]
        # With integer endpoints, the maximum is reached at an integer point.
        expected = max((sum(l <= x <= r for l, r in intervals)
                        for x in range(-4, 5)), default=0)
        assert maximum_closed_overlap(intervals) == expected


if __name__ == "__main__":
    main()
```

Time O(n log n), space O(n).

The maximum is always reached at an endpoint: between endpoints the set of containing intervals is fixed, and at an endpoint it includes everything active on either side. So one read per endpoint suffices.

## 4. Closed integer ranges: count positions, not length

Sometimes the coordinates are discrete, such as seats 1, 2, 3, …. The closed integer range `[2, 5]` then means the seats `{2, 3, 4, 5}`: **4 positions**, although its continuous length is 3.

For integers, the next position after r is r + 1, so `[l, r]` covers exactly the same seats as the half-open `[l, r + 1)`. Convert once and reuse the half-open sweep. This is what `integer_interval_statistics` does in [Your First Sweep §5](01-first-sweep-intervals.md#5-full-half-open-interval-implementation):

- `[1, 2]` and `[2, 3]` become `[1, 3)` and `[2, 4)`. They share seat 2, so the maximum is 2 and 3 seats are covered.
- The singleton `[4, 4]` becomes `[4, 5)` and covers one seat.

**Do not use r + 1 for continuous intervals.** There is no "next real number" after r, and shifting r changes the interval: `[1, 2]` would gain the whole stretch `(2, 3)`. Use the processing order of §2 instead.

## 5. Point queries are events too

New question: for each query point x, how many half-open intervals contain x?

Intervals: `[1, 3)`, `[3, 6)`, `[1, 3)` again, and the empty `[4, 4)`. Queries, in the order asked: `6, 3, 1, 0, 3, 2`.

**Brute force:** test every interval against every query, O(nq).

**Observation.** A query does not change the count; it reads it. So treat each query as one more event on the same line. Sort the queries, walk through the endpoint changes in order, and answer a query when the sweep reaches it. For half-open intervals the reading at x must include every start at x and exclude every end at x (§2), so apply all changes at coordinates `<= x` before answering.

The net changes are `+2` at 1 (two copies start), `−2 + 1 = −1` at 3, and `−1` at 6. `[4, 4)` is skipped.

| Query x (sorted) | Changes applied now | `active` | Answer |
|---:|---|---:|---:|
| 0 | none | 0 | 0 |
| 1 | at 1: +2 | 2 | 2 |
| 2 | none | 2 | 2 |
| 3 | at 3: −1 | 1 | 1 |
| 3 | none | 1 | 1 |
| 6 | at 6: −1 | 0 | 0 |

At 3 the one active interval is `[3, 6)`. Both copies of `[1, 3)` end at 3 and no longer count. Each query carries its original index, so the answers go back in the order `6, 3, 1, 0, 3, 2`: `[0, 1, 2, 0, 1, 2]`.

```python
from random import Random


def count_covering_points(intervals, queries):
    """Intervals are continuous half-open [l, r); queries are exact points."""
    changes = {}
    for left, right in intervals:
        if left > right:
            raise ValueError("reversed interval")
        if left == right:  # [x, x) is empty.
            continue
        changes[left] = changes.get(left, 0) + 1
        changes[right] = changes.get(right, 0) - 1

    events = sorted(changes.items())
    answer = [0] * len(queries)
    active = 0
    event_index = 0
    for x, query_index in sorted((x, i) for i, x in enumerate(queries)):
        while event_index < len(events) and events[event_index][0] <= x:
            active += events[event_index][1]
            event_index += 1
        answer[query_index] = active
    return answer


def main():
    intervals = [(1, 3), (3, 6), (1, 3), (4, 4)]
    queries = [6, 3, 1, 0, 3, 2]
    assert count_covering_points(intervals, queries) == [0, 1, 2, 0, 1, 2]
    assert count_covering_points([], [0, 1]) == [0, 0]
    assert count_covering_points([(0, 1)], []) == []
    assert count_covering_points([(2, 2)], [2]) == [0]

    rng = Random(7)
    for _ in range(100):
        pairs = [sorted((rng.randrange(-4, 5), rng.randrange(-4, 5)))
                 for _ in range(rng.randrange(12))]
        xs = list(range(-5, 6))
        expected = [sum(l <= x < r for l, r in pairs) for x in xs]
        assert count_covering_points(pairs, xs) == expected


if __name__ == "__main__":
    main()
```

Sorting costs O(n log n + q log q) and the sweep O(n + q). Extra space is O(n + q).

[Designing a Sweep §4](03-designing-a-sweep.md#4-proving-a-sweep-correct) proves this sweep correct by induction.

Answering in sorted order rather than in the order asked is called an **offline** sweep: all queries must be known in advance. [Offline Sweeps](05-offline-sweeps-and-fenwick.md) builds on this.

## 6. Point queries without a loop: two sorted arrays

When the state is only a count, the sweep can be replaced by two binary searches. An interval contains x exactly when it has started by x and has not yet ended:

$$\text{count}(x) = \#\{\text{starts by } x\} - \#\{\text{ends by } x\}.$$

The endpoint semantics decide what "by x" means:

| Semantics | Started by x | Ended by x | Count at x |
|---|---|---|---|
| Half-open `[l, r)` | `l <= x` | `r <= x` | `bisect_right(starts, x) - bisect_right(ends, x)` |
| Closed `[l, r]` | `l <= x` | `r < x` | `bisect_right(starts, x) - bisect_left(ends, x)` |

**Example: flowers in full bloom.** Flower i blooms during the closed day range `[l, r]`. For each visitor's arrival day, how many flowers are blooming?

Flowers `[1, 6]`, `[3, 7]`, `[9, 12]`, `[4, 13]` give `starts = [1, 3, 4, 9]` and `ends = [6, 7, 12, 13]`. A visitor on day 7: three flowers have started (`bisect_right(starts, 7) = 3`), and one has ended before day 7 (`bisect_left(ends, 7) = 1`, the flower ending on day 6). The flower ending on day 7 still blooms that day. Answer: 2.

```python
from bisect import bisect_left, bisect_right
from random import Random


def flowers_in_bloom(flowers, visitors):
    """Closed [l, r] bloom ranges; answer each visitor day independently."""
    for left, right in flowers:
        if left > right:
            raise ValueError("reversed interval")
    starts = sorted(left for left, _ in flowers)
    ends = sorted(right for _, right in flowers)
    return [bisect_right(starts, day) - bisect_left(ends, day) for day in visitors]


def main():
    flowers = [(1, 6), (3, 7), (9, 12), (4, 13)]
    assert flowers_in_bloom(flowers, [2, 3, 7, 11]) == [1, 2, 2, 2]
    assert flowers_in_bloom([(1, 10), (3, 3)], [3, 3, 2]) == [2, 2, 1]
    assert flowers_in_bloom([], [5]) == [0]

    rng = Random(61)
    for _ in range(200):
        flowers = [tuple(sorted((rng.randrange(0, 10), rng.randrange(0, 10))))
                   for _ in range(rng.randrange(10))]
        days = [rng.randrange(-1, 11) for _ in range(10)]
        expected = [sum(l <= d <= r for l, r in flowers) for d in days]
        assert flowers_in_bloom(flowers, days) == expected


if __name__ == "__main__":
    main()
```

Preprocessing costs O(n log n). Each query then costs O(log n) **and can arrive at any time**, so unlike §5 this works online. It works only because a count splits into "started" minus "ended". A maximum height or a covered length does not split this way; those still need a real sweep.

## 7. Pitfalls and practice

1. Sorting ties by tuple order without deciding what a reading at an endpoint should see.
2. Recording a maximum between a half-open start and a half-open end at the same x. It reports a count that never exists.
3. Grouping closed starts and ends into one net change. It hides the count at the shared point.
4. Ignoring closed singletons in maximum concurrency.
5. Treating continuous length as an integer position count: `[2, 5]` has length 3 but contains 4 integer positions.
6. Using `r + 1` to convert closed **continuous** intervals.

Practice: minimum platforms with explicitly stated arrival and departure ties; number of integer seats covered by closed booking ranges; for each query time, how many restaurant guests are present, with guests leaving at the query time not counted; number of flowers in full bloom.

Next: [Designing a Sweep](03-designing-a-sweep.md).
