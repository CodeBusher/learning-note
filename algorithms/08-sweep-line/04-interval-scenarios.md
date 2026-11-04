# Interval Scenarios — Assignment, Intersection, Gaps, Greedy, and Online Bookings

All intervals here are half-open `[l, r)` unless a section says otherwise. Empty intervals are skipped and reversed ones raise `ValueError`.

## 1. Room assignment: which room does each meeting get?

Meetings `[1, 3)`, `[2, 5)`, `[4, 7)`, `[7, 9)`. The overlap is at most 2, so [two rooms suffice](01-first-sweep-intervals.md#minimum-rooms). Now produce the assignment: a room number for every meeting, with no two overlapping meetings in one room.

**Brute force:** for each meeting, try rooms 0, 1, 2, … and check it against every meeting already in that room. That is O(n²) checks.

**Observation.** Handle meetings in order of start time. When a meeting starts at `s`, a room is free exactly when its last meeting ended at or before `s`. So keep the busy rooms in a min-heap by end time: the earliest-ending room is on top, and every room that has ended by `s` can be popped from the top. The `<=` is the half-open rule: a meeting ending at `s` has already left. Popped rooms go into a second heap of free room numbers, so the lowest free number is reused.

| Start | Rooms released (end `<= start`) | Room given | `busy` after, as `(end, room)` |
|---:|---|---:|---|
| 1 | — | 0 (new) | `(3,0)` |
| 2 | — | 1 (new) | `(3,0) (5,1)` |
| 4 | room 0 (ended at 3) | 0 | `(5,1) (7,0)` |
| 7 | room 1 (ended at 5), room 0 (ended at 7) | 0 | `(9,0)` |

At 7 the meeting `[4, 7)` frees room 0 at the very moment `[7, 9)` needs it.

```python
from heapq import heappop, heappush
from random import Random


def assign_rooms(meetings):
    """Half-open [start, end). Returns (room_count, room per meeting).

    Empty meetings get room None. Released rooms are reused lowest number first.
    """
    for start, end in meetings:
        if start > end:
            raise ValueError("reversed interval")
    order = sorted(range(len(meetings)), key=lambda i: meetings[i])
    busy = []  # (end, room) for rooms in use
    free = []  # released room numbers
    rooms = [None] * len(meetings)
    room_count = 0
    for i in order:
        start, end = meetings[i]
        if start == end:
            continue
        while busy and busy[0][0] <= start:
            _, room = heappop(busy)
            heappush(free, room)
        if free:
            room = heappop(free)
        else:
            room = room_count
            room_count += 1
        rooms[i] = room
        heappush(busy, (end, room))
    return room_count, rooms


def main():
    assert assign_rooms([(2, 5), (4, 7), (7, 9), (1, 3)]) == (2, [1, 0, 0, 0])
    assert assign_rooms([]) == (0, [])
    assert assign_rooms([(3, 3)]) == (0, [None])

    rng = Random(41)
    for _ in range(300):
        meetings = [tuple(sorted((rng.randrange(-4, 6), rng.randrange(-4, 6))))
                    for _ in range(rng.randrange(10))]
        count, rooms = assign_rooms(meetings)
        overlap = max((sum(l <= x < r for l, r in meetings)
                       for x in range(-4, 6)), default=0)
        assert count == overlap
        for i, (l1, r1) in enumerate(meetings):
            for j, (l2, r2) in enumerate(meetings[:i]):
                if rooms[i] is not None and rooms[i] == rooms[j]:
                    assert r1 <= l2 or r2 <= l1  # same room, no overlap


if __name__ == "__main__":
    main()
```

**Why the room count is optimal.** A new room opens only when every existing room is busy at `s`. Then all those meetings and the new one contain `s`, so the overlap at `s` equals the new room count. No assignment can use fewer rooms than the maximum overlap.

Each meeting enters and leaves each heap at most once: O(n log n) time, O(n) space.

## 2. Intersection of two interval lists

Two people each have a sorted list of pairwise disjoint busy intervals. When are both busy?

```text
a: [0,2)  [5,10)  [13,23)  [24,25)
b: [1,5)  [8,12)  [15,24)  [25,26)
```

**Brute force:** intersect every pair, O(|a|·|b|).

**Observation.** Look at the current interval of each list. They overlap on `[max(starts), min(ends))` if that is nonempty. Then whichever of the two ends first cannot meet anything later in the other list, because everything later there starts after the current one ends. So advance that one. Two pointers, one pass.

| Step | `a[i]` | `b[j]` | `[max start, min end)` | Output | Ends first → advance |
|---:|---|---|---|---|---|
| 1 | `[0,2)` | `[1,5)` | `[1,2)` | `[1,2)` | a |
| 2 | `[5,10)` | `[1,5)` | `[5,5)` empty | — | b |
| 3 | `[5,10)` | `[8,12)` | `[8,10)` | `[8,10)` | a |
| 4 | `[13,23)` | `[8,12)` | `[13,12)` empty | — | b |
| 5 | `[13,23)` | `[15,24)` | `[15,23)` | `[15,23)` | a |
| 6 | `[24,25)` | `[15,24)` | `[24,24)` empty | — | b |
| 7 | `[24,25)` | `[25,26)` | `[25,25)` empty | — | a, list ends |

Step 7 is the shared-endpoint case: `[24, 25)` and `[25, 26)` touch at 25 but share no time. With **closed** intervals the test becomes `low <= high`, and the pair would intersect at the single point 25.

```python
from random import Random


def intersect_interval_lists(a, b):
    """Each list is sorted and pairwise disjoint, half-open [l, r)."""
    i = j = 0
    result = []
    while i < len(a) and j < len(b):
        low = max(a[i][0], b[j][0])
        high = min(a[i][1], b[j][1])
        if low < high:
            result.append((low, high))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return result


def random_disjoint(rng):
    points = sorted(rng.sample(range(20), 2 * rng.randrange(5)))
    return list(zip(points[::2], points[1::2]))


def cells(intervals):
    return {c for l, r in intervals for c in range(l, r)}


def main():
    a = [(0, 2), (5, 10), (13, 23), (24, 25)]
    b = [(1, 5), (8, 12), (15, 24), (25, 26)]
    assert intersect_interval_lists(a, b) == [(1, 2), (8, 10), (15, 23)]
    assert intersect_interval_lists([], b) == []

    rng = Random(43)
    for _ in range(300):
        a, b = random_disjoint(rng), random_disjoint(rng)
        got = intersect_interval_lists(a, b)
        assert cells(got) == cells(a) & cells(b)
        assert all(l < r for l, r in got) and got == sorted(got)


if __name__ == "__main__":
    main()
```

Time O(|a| + |b|). If the lists are not already sorted and disjoint, merge each first (§3).

## 3. Free time: the gaps in a union

Busy intervals of three people, and a working window `[0, 10)`. When is everyone free?

```text
alice: [1,3) [6,7)      bob: [2,4)      carol: [2,5) [9,12)
```

Everyone is free exactly where nobody is busy: the gaps in the union, clipped to the window. The window is required; "uncovered" has no finite answer otherwise.

**Step 1, merge** the intervals as in [Your First Sweep §7](01-first-sweep-intervals.md#7-merging-intervals-is-another-route-to-union-length): sort by start, extend the last run while the next start is `<=` its end. This gives `[1,5) [6,7) [9,12)`. The `<=` merges touching runs, so `[1, 3)` and `[3, 5)` become `[1, 5)` with no zero-length gap between them.

**Step 2, walk the runs** with `cursor`, the first moment not yet known to be busy, starting at the window's left end:

| Run | `cursor` before | Gap output | `cursor` after |
|---|---:|---|---:|
| `[1,5)` | 0 | `[0,1)` | 5 |
| `[6,7)` | 5 | `[5,6)` | 7 |
| `[9,12)` | 7 | `[7,9)` | 12 |
| end | 12 | none, 12 ≥ 10 | — |

```python
from random import Random


def merge_intervals(intervals):
    """Union of half-open intervals as sorted, disjoint, non-touching runs."""
    merged = []
    for left, right in sorted(intervals):
        if left > right:
            raise ValueError("reversed interval")
        if left == right:
            continue
        if merged and left <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], right)
        else:
            merged.append([left, right])
    return [tuple(run) for run in merged]


def free_time(busy, lo, hi):
    """Gaps inside [lo, hi) not covered by any busy interval."""
    gaps = []
    cursor = lo
    for left, right in merge_intervals(busy):
        if left >= hi:
            break
        if left > cursor:
            gaps.append((cursor, left))
        cursor = max(cursor, right)
    if cursor < hi:
        gaps.append((cursor, hi))
    return gaps


def main():
    busy = [(1, 3), (6, 7), (2, 4), (2, 5), (9, 12)]
    assert merge_intervals(busy) == [(1, 5), (6, 7), (9, 12)]
    assert free_time(busy, 0, 10) == [(0, 1), (5, 6), (7, 9)]
    assert free_time([], 0, 3) == [(0, 3)]
    assert free_time([(0, 3)], 0, 3) == []

    rng = Random(47)
    for _ in range(300):
        busy = [tuple(sorted((rng.randrange(-3, 12), rng.randrange(-3, 12))))
                for _ in range(rng.randrange(8))]
        covered = {c for l, r in busy for c in range(l, r)}
        gaps = free_time(busy, 0, 10)
        assert {c for l, r in gaps for c in range(l, r)} == set(range(10)) - covered
        # Maximal: consecutive gaps never touch.
        assert all(g[1] < h[0] for g, h in zip(gaps, gaps[1:]))


if __name__ == "__main__":
    main()
```

Time O(n log n) for the sort, space O(n).

## 4. Greedy by end time: keep, remove, or pierce

These look like optimization problems, but they are sweeps whose coordinate is the **end time**.

### 4.1 Maximum number of non-overlapping intervals

Keep as many pairwise non-overlapping intervals as possible (also called activity selection). Example: `[1, 2)`, `[2, 3)`, `[3, 4)`, `[1, 3)`.

**Rule:** sort by end; keep an interval when it starts at or after the end of the last kept one.

| Sorted by end | Last kept end | Start ≥ last end? | Kept so far |
|---|---:|---|---:|
| `[1,2)` | — | yes | 1 |
| `[2,3)` | 2 | 2 ≥ 2, yes | 2 |
| `[1,3)` | 3 | 1 < 3, no | 2 |
| `[3,4)` | 3 | yes | 3 |

**Why not sort by start?** For `[0, 10)`, `[1, 2)`, `[3, 4)` the earliest start is the long interval, which blocks both short ones: 1 kept instead of 2.

**Why end order is optimal (exchange argument).** Let `e` be the interval that ends first. Take any optimal solution and replace its first interval with `e`. Since `e` ends no later, everything after it still fits, so the solution is still optimal and starts with `e`. Repeat on the intervals that start at or after `e`'s end.

**Minimum removals** so that the rest don't overlap is `n − (maximum kept)`.

### 4.2 Minimum arrows to burst balloons

Each balloon is a **closed** interval `[l, r]`. An arrow at x bursts every balloon with `l <= x <= r`. Find the fewest arrows. Example: `[10, 16]`, `[2, 8]`, `[1, 6]`, `[7, 12]`.

**Rule:** sort by end; when a balloon is not yet burst, shoot at its end. The end is the latest point that still hits it, so it reaches as many later-starting balloons as possible.

| Sorted by end | Last shot | Burst already (`l <= shot`)? | Arrows |
|---|---:|---|---:|
| `[1,6]` | — | no: shoot at 6 | 1 |
| `[2,8]` | 6 | 2 ≤ 6, yes | 1 |
| `[7,12]` | 6 | 7 > 6, no: shoot at 12 | 2 |
| `[10,16]` | 12 | 10 ≤ 12, yes | 2 |

The tie test is the only difference from §4.1, and it comes from closed versus half-open. Balloons `[1, 2]` and `[2, 3]` share the point 2, so one arrow bursts both. Meetings `[1, 2)` and `[2, 3)` don't overlap, so both can be kept.

```python
from itertools import combinations
from random import Random


def max_non_overlapping(intervals):
    """Half-open [l, r); touching intervals are compatible. Empty ones are ignored."""
    kept = 0
    last_end = None
    for left, right in sorted(intervals, key=lambda p: p[1]):
        if left > right:
            raise ValueError("reversed interval")
        if left == right:
            continue
        if last_end is None or left >= last_end:
            kept += 1
            last_end = right
    return kept


def min_removals_for_no_overlap(intervals):
    nonempty = [(l, r) for l, r in intervals if l != r]
    return len(nonempty) - max_non_overlapping(nonempty)


def min_arrows(balloons):
    """Closed [l, r]; an arrow at x bursts every balloon with l <= x <= r."""
    arrows = 0
    shot = None
    for left, right in sorted(balloons, key=lambda p: p[1]):
        if left > right:
            raise ValueError("reversed interval")
        if shot is None or left > shot:
            arrows += 1
            shot = right
    return arrows


def main():
    assert max_non_overlapping([(1, 2), (2, 3), (3, 4), (1, 3)]) == 3
    assert max_non_overlapping([(0, 10), (1, 2), (3, 4)]) == 2
    assert min_removals_for_no_overlap([(1, 2), (1, 2), (1, 2)]) == 2
    assert min_arrows([(10, 16), (2, 8), (1, 6), (7, 12)]) == 2
    assert min_arrows([(1, 2), (2, 3), (3, 4), (4, 5)]) == 2
    assert min_arrows([]) == 0

    rng = Random(53)
    for _ in range(300):
        items = [tuple(sorted((rng.randrange(0, 8), rng.randrange(0, 8))))
                 for _ in range(rng.randrange(8))]
        # Brute force: largest pairwise-compatible subset.
        nonempty = [p for p in items if p[0] < p[1]]
        best = max(size for size in range(len(nonempty) + 1)
                   for subset in combinations(nonempty, size)
                   if all(a[1] <= b[0] or b[1] <= a[0]
                          for a, b in combinations(subset, 2)))
        assert max_non_overlapping(items) == best
        # Brute force: fewest points hitting every closed interval.
        # Right endpoints suffice: an arrow can slide right to the nearest end it hits.
        points = sorted({r for _, r in items})
        fewest = next(size for size in range(len(points) + 1)
                      if any(all(any(l <= x <= r for x in chosen) for l, r in items)
                             for chosen in combinations(points, size)))
        assert min_arrows(items) == fewest


if __name__ == "__main__":
    main()
```

Both greedies cost O(n log n) for the sort plus O(n).

## 5. Online bookings: when requests arrive one at a time

Every sweep so far was **offline**: all intervals were known before sorting. A booking system must answer each request as it arrives.

**Reject double bookings.** Keep the accepted bookings as two parallel sorted lists, `starts` and `ends`. A new booking `[s, e)` can only conflict with its two neighbors in start order: the last booking starting at or before `s` (conflict if it ends after `s`) and the first starting after `s` (conflict if it starts before `e`).

| Request | Neighbors | Test | Result |
|---|---|---|---|
| `[10,20)` | none | — | accept |
| `[15,25)` | before: `[10,20)` | 20 > 15 | reject |
| `[20,30)` | before: `[10,20)` | 20 > 20? no | accept |
| `[5,10)` | after: `[10,20)` | 10 < 10? no | accept |

**Report the maximum overlap so far** (accept everything, like my calendar III): keep the difference map of [Your First Sweep §2](01-first-sweep-intervals.md#2-the-observation-the-count-changes-only-at-endpoints) between requests and re-run the counter sweep over its sorted keys after each booking. That costs O(n) per request.

```python
from bisect import bisect_right
from random import Random


class SingleCalendar:
    """Accept a half-open booking only if it overlaps no accepted booking."""

    def __init__(self):
        self.starts = []
        self.ends = []  # ends[i] belongs to starts[i]; both sorted

    def book(self, start, end):
        if start > end:
            raise ValueError("reversed interval")
        if start == end:
            return True
        i = bisect_right(self.starts, start)
        if i > 0 and self.ends[i - 1] > start:
            return False  # previous booking still running at start
        if i < len(self.starts) and self.starts[i] < end:
            return False  # next booking begins before end
        self.starts.insert(i, start)
        self.ends.insert(i, end)
        return True


def main():
    single = SingleCalendar()
    assert [single.book(*b) for b in [(10, 20), (15, 25), (20, 30), (5, 10)]] == [
        True, False, True, True]

    rng = Random(59)
    for _ in range(200):
        single, accepted = SingleCalendar(), []
        for _ in range(12):
            s, e = sorted((rng.randrange(0, 15), rng.randrange(0, 15)))
            ok = all(e <= l or r <= s for l, r in accepted) or s == e
            assert single.book(s, e) == ok
            if ok and s < e:
                accepted.append((s, e))


if __name__ == "__main__":
    main()
```

**Costs.** `SingleCalendar.book` searches in O(log n), but `list.insert` shifts elements in O(n). Python's standard library has no balanced search tree. For many requests, use a sorted-container library, or a segment tree over compressed or dynamically created coordinates ([Segment Trees](../04-range-queries/03-segment-tree.md)), for O(log n) per request.

## 6. Summary: which interval tool?

| Question | Sweep coordinate | State | Invariant | Section |
|---|---|---|---|---|
| How many rooms? | Endpoints | Counter | Count on the current slab | [First Sweep §8](01-first-sweep-intervals.md#minimum-rooms) |
| Which room for each meeting? | Start times | Heap of busy rooms, heap of free rooms | `busy` holds exactly the rooms whose meeting ends after the current start | §1 |
| Where do two schedules overlap? | Two pointers | Current interval of each list | Every intersection ending before `min(ends)` is output | §2 |
| When is everyone free? | Start times | Merge cursor | Every gap before `cursor` is output | §3 |
| Keep the most / remove the fewest | End times | Last kept end | Kept set is optimal among intervals seen | §4.1 |
| Fewest points hitting every interval | End times | Last shot position | Every balloon seen is burst | §4.2 |
| Bookings arrive online | Arrival order | Sorted lists of accepted bookings | Accepted bookings are disjoint and sorted | §5 |

## 7. Pitfalls and practice

1. Releasing a room only when `end < start` for half-open meetings. A meeting ending at `s` frees its room for a meeting starting at `s`.
2. Sorting by start for activity selection. One long early interval can block many short ones.
3. Using the half-open tie rule for closed balloons, or the reverse.
4. Reporting free time without a bounded window.
5. Assuming `bisect.insort` is O(log n). The search is; the list insertion is not.

Practice: meeting rooms with assignments; interval list intersections; employee free time; non-overlapping intervals; minimum arrows; my calendar I and III; car pooling (a [weighted overlap](01-first-sweep-intervals.md#weighted-events)).

Next: [Offline Sweeps and Fenwick Trees](05-offline-sweeps-and-fenwick.md).
