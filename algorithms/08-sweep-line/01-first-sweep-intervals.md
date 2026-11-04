# Your First Sweep — Overlap and Union of Intervals

## 1. The problem and the brute force

A meeting room is booked by three meetings:

| Meeting | Time |
|---|---|
| A | `[2, 5)` |
| B | `[4, 7)` |
| C | `[7, 9)` |

`[2, 5)` is a **half-open** interval: A starts at 2 and leaves at 5, so A is in the room at time 4.9 but not at time 5. Half-open intervals model "leave at 5, the next person may enter at 5" without any overlap.

Two questions:

1. What is the **maximum number of meetings** in the room at the same time?
2. For how long is the room **occupied** (the length of the union)?

**Brute force.** Look at every unit of time `[t, t + 1)` and count the meetings that contain it:

```text
time         0   1   2   3   4   5   6   7   8   9
A [2, 5)             ■   ■   ■
B [4, 7)                     ■   ■   ■
C [7, 9)                                 ■   ■
count        0   0   1   1   2   1   1   1   1   0
```

The maximum count is 2, during `[4, 5)`. Seven unit cells have a positive count, so the room is occupied for 7 time units.

This costs O(domain size × n). It is fine for times 0–9, but impossible for timestamps such as `10**18`, and meaningless for real-valued times, where there are no "unit cells" to scan.

## 2. The observation: the count changes only at endpoints

Look at the `count` row again, with a bar drawn at every interval **endpoint**: 2, 4, 5, 7, 9.

```text
count        0   0 | 1   1 | 2 | 1   1 | 1   1 | 0
                   2       4   5       7       9
```

Between two bars the count never changes. Every change happens at a bar, although a bar does not have to change it: at 7 the count stays 1. This is no coincidence. Between two consecutive endpoints no meeting starts or stops, so the set of meetings in the room cannot change.

So instead of visiting every moment, record what happens at each endpoint:

- At a start, one meeting enters: an **event** `+1`.
- At an end, one meeting leaves: an **event** `−1`.

| Meeting | Start event | End event |
|---|---|---|
| A `[2, 5)` | `(2, +1)` | `(5, −1)` |
| B `[4, 7)` | `(4, +1)` | `(7, −1)` |
| C `[7, 9)` | `(7, +1)` | `(9, −1)` |

Sort the events by coordinate and add up the changes at each coordinate:

| Coordinate | Events there | Net change |
|---:|---|---:|
| 2 | A starts | +1 |
| 4 | B starts | +1 |
| 5 | A ends | −1 |
| 7 | B ends, C starts | 0 |
| 9 | C ends | −1 |

At 4 there is only `+1`: B arrives, and nobody leaves until A's end at 5. At 7 two events happen at the same coordinate and cancel.

The region between two consecutive event coordinates is called a **slab**. The count is constant on each slab, so the sweep does one unit of work per event instead of one per moment.

## 3. Run the sweep step by step

Keep two variables:

- `active`: the number of meetings in the room on the current slab.
- `previous`: the coordinate where the current slab began.

At each event coordinate `x`, do two things in this order:

1. **Measure the slab that ends at x**, `[previous, x)`. `active` still describes it, so add its width `x − previous` to the union if `active > 0`.
2. **Apply all events at `x`.** `active` now describes the next slab, which starts at `x`.

| Step | x | Slab ending at x | `active` on it | Width | Union so far | Net change at x | `active` after | Max so far |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | 2 | — | 0 | — | 0 | +1 | 1 | 1 |
| 2 | 4 | `[2, 4)` | 1 | 2 | 2 | +1 | 2 | 2 |
| 3 | 5 | `[4, 5)` | 2 | 1 | 3 | −1 | 1 | 2 |
| 4 | 7 | `[5, 7)` | 1 | 2 | 5 | 0 | 1 | 2 |
| 5 | 9 | `[7, 9)` | 1 | 2 | 7 | −1 | 0 | 2 |

Final answers: maximum 2, union length 7, the same as the brute force. The work is five steps, however large the coordinates are.

The order inside a step matters. If step 2 applied the `+1` first and then measured `[2, 4)`, it would multiply by `active = 2` and count part of the union twice.

### What happens exactly at 7?

B ends at 7 and C starts at 7. Step 4 treated this as one net change of 0. Split it into its two events and look at `active` after each one.

**Half-open, `[4, 7)` and `[7, 9)`.** B is gone at time 7 and C is already there, so the true count at the instant 7 is 1.

| Order at x = 7 | `active` before | After 1st event | After 2nd event | True count at 7 |
|---|---:|---:|---:|---:|
| end B, then start C | 1 | 0 | 1 | 1 |
| start C, then end B | 1 | **2** | 1 | 1 |

The second order passes through `active = 2`. If the code records the maximum between the two events, it reports a moment with two meetings that never happened. Applying the net change in one step, as the trace did, never shows the 2.

**Closed, `[4, 7]` and `[7, 9]`.** Now both meetings contain the instant 7, so the true count there is 2.

| Order at x = 7 | `active` before | After 1st event | After 2nd event | True count at 7 |
|---|---:|---:|---:|---:|
| start C, then end B | 1 | **2** | 1 | 2 |
| net change 0 | 1 | 1 | — | 2 |

This time the 2 is real, and the net-change shortcut hides it.

So the same events need different handling:

| | Half-open `[l, r)` | Closed `[l, r]` |
|---|---|---|
| Who is in the room at a shared endpoint x | Only the one starting at x | Both |
| Correct work at x | Apply all changes at x together | Add starts, read the count, then remove ends |
| Union length | 7 | 7 (one point has zero length) |
| Maximum for `[1, 2]`, `[2, 3]` | 1 | 2 |

Lengths never depend on this choice. Point counts, including the maximum, do. The rest of this chapter uses half-open intervals. [Endpoint Semantics](02-endpoint-semantics-and-queries.md) builds the closed and open versions.

## 4. One counter answers several questions

The same `active` value on each slab supports more than maximum and union:

- `max(active)` over all slabs is the maximum overlap.
- A slab belongs to the union exactly when `active > 0`.
- A slab's width belongs to the **coverage bucket** `active`: the length covered by exactly that many intervals.

For the running example:

| Slab | Meetings | `active` | Width |
|---|---|---:|---:|
| `[2, 4)` | A | 1 | 2 |
| `[4, 5)` | A, B | 2 | 1 |
| `[5, 7)` | B | 1 | 2 |
| `[7, 9)` | C | 1 | 2 |

Length covered exactly once is `2 + 2 + 2 = 6`. Length covered exactly twice is 1. Union length is `6 + 1 = 7`.

## 5. Full half-open interval implementation

This function returns `(maximum_overlap, union_length, exact_coverage_lengths)`. The dictionary omits coverage zero, because the uncovered space outside all intervals is unbounded unless a finite domain is given.

```python
from random import Random


def interval_statistics(intervals):
    """Continuous half-open [l, r); integer examples use exact lengths."""
    delta = {}
    for left, right in intervals:
        if left > right:
            raise ValueError("reversed interval")
        if left == right:
            continue
        delta[left] = delta.get(left, 0) + 1
        delta[right] = delta.get(right, 0) - 1
    if not delta:
        return 0, 0, {}

    active = 0
    maximum = 0
    union_length = 0
    exact = {}
    previous = min(delta)
    for x, change in sorted(delta.items()):
        width = x - previous
        # Before changes at x, active describes [previous, x).
        if active > 0 and width > 0:
            union_length += width
            exact[active] = exact.get(active, 0) + width
        active += change
        maximum = max(maximum, active)
        previous = x
    assert active == 0
    return maximum, union_length, exact


def integer_interval_statistics(intervals):
    """Closed integer [l, r]; length becomes the count of integer positions."""
    converted = []
    for left, right in intervals:
        if left > right:
            raise ValueError("reversed integer interval")
        converted.append((left, right + 1))
    return interval_statistics(converted)


def main():
    # The running example: meetings A, B, C.
    assert interval_statistics([(2, 5), (4, 7), (7, 9)]) == (
        2, 7, {1: 6, 2: 1})
    assert interval_statistics([(1, 5), (2, 4), (4, 6)]) == (
        2, 5, {1: 2, 2: 3})
    assert interval_statistics([(0, 2), (2, 5)]) == (1, 5, {1: 5})
    assert interval_statistics([(1, 4), (1, 4)]) == (2, 3, {2: 3})
    assert interval_statistics([(2, 2)]) == (0, 0, {})
    assert interval_statistics([]) == (0, 0, {})
    # Closed [1, 2] and [2, 3] share integer point 2.
    assert integer_interval_statistics([(1, 2), (2, 3)]) == (
        2, 3, {1: 2, 2: 1})
    assert integer_interval_statistics([(4, 4)]) == (1, 1, {1: 1})

    rng = Random(19)
    for _ in range(200):
        intervals = [tuple(sorted((rng.randrange(-4, 5), rng.randrange(-4, 5))))
                     for _ in range(rng.randrange(10))]
        # Integer endpoints make each unit slab have a constant count.
        counts = [sum(l <= x < r for l, r in intervals)
                  for x in range(-4, 4)]
        exact = {k: counts.count(k) for k in set(counts) if k > 0}
        assert interval_statistics(intervals) == (
            max(counts, default=0), sum(c > 0 for c in counts), exact)


if __name__ == "__main__":
    main()
```

The `delta` dictionary does the grouping from §2: all events at one coordinate are added into one net change before the sweep sees them. `integer_interval_statistics` handles closed **integer** ranges, which [Endpoint Semantics §4](02-endpoint-semantics-and-queries.md#4-closed-integer-ranges-count-positions-not-length) explains.

Each interval contributes at most two events. Sorting costs O(n log n) and the sweep costs O(n). The event dictionary and coverage histogram use O(n) extra space.

## 6. Why the coverage sum is correct

The distinct event coordinates cut the covered domain into disjoint slabs. No endpoint lies inside a slab, so each interval covers either all of it or none of it, and the count is constant on the slab. Adding the slab's width to exactly one positive coverage bucket counts every covered location once. Summing all positive buckets gives the union length.

A consistency check:

`sum(k * exact[k] for k in exact) == sum(r - l for l, r in intervals)`.

Both sides count interval length with multiplicity. For the running example, `1·6 + 2·1 = 8 = 3 + 3 + 2`. This identity catches bugs that a union-length assertion alone can miss.

## 7. Merging intervals is another route to union length

Sort intervals by start, then extend the current merged interval whenever the next start is at most its end. For half-open intervals, touching intervals merge into a single union interval: `[1, 3) ∪ [3, 5) = [1, 5)`. This does not mean their occupants overlap at 3.

Merging gives the union itself in O(n log n) time and O(n) output space. The counter sweep fits better when you also need multiplicities, maximum overlap, or coverage by exactly k intervals. Merge bookkeeping loses those multiplicities.

## 8. Extensions

### Minimum rooms

When each meeting occupies a half-open interval, the minimum number of rooms equals the maximum overlap. At a moment with k active meetings, at least k rooms are necessary. A greedy allocation that reuses the earliest finishing available room attains that bound. Use a heap if you need the actual assignments. The counter sweep gives only the minimum count.

### Coverage by at least k intervals

Sum `exact[c]` for all `c >= k`. For many k-queries, compute suffix sums over the coverage histogram. Distinguish "at least k intervals" from "at least k units of time."

### Weighted events

Replace `+1/-1` with `+weight/-weight` for resource usage or load. The union test `active > 0` is valid for nonnegative weights when positive weight means coverage. With negative weights, the signed sum may cancel even when objects are present. Maintain a separate object count if you need the geometric union.

## 9. Pitfalls and practice

1. Measuring a slab after applying the events at its right boundary.
2. Removing duplicate intervals when overlap multiplicity matters.
3. Computing "uncovered length" without specifying a bounded observation domain.
4. Forgetting that Python integers grow automatically. Fixed-width languages need wide enough arithmetic for coordinate differences and sums.

Practice: meeting concurrency; total covered road length; length painted exactly twice; minimum rooms with assignments.

Next: [Endpoint Semantics and Point Queries](02-endpoint-semantics-and-queries.md).
