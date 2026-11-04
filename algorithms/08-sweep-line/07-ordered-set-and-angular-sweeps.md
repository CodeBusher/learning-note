# Ordered-Set and Angular Sweeps — Closest Pair, Segment Intersection, and Directions

## 1. Closest pair of points

Find the smallest distance between two of n points. Example: `(0,0)`, `(5,5)`, `(1,1)`, `(9,0)`; the closest pair is `(0,0)`–`(1,1)` at squared distance 2.

**Brute force:** all pairs, O(n²).

**Observation.** Sweep the points by x and let `d` be the best distance found so far. A point more than `d` to the left of the current point p cannot beat `d`, so it can leave for good. The remaining points form a **band** of width `d`, kept sorted by y, and p only needs the band points whose y is within `d` of its own. Here the state is not a number but the **y-order** of the active points.

**Why that is O(1) candidates.** They all lie in a `d × 2d` rectangle to the left of p. Any two band points are at least `d` apart, so only a constant number fit in that rectangle (at most 6 besides p).

> **Invariant:** when p is visited, the band holds exactly the earlier points q with `(p.x − q.x)² <= d²`, sorted by y.

The code works with **squared** distances so that integer inputs stay exact, and starts `d²` at the distance of any one pair: the true minimum can only be smaller. The y-window uses `isqrt(best) + 1`, slightly too wide, which can only add candidates.

Points sorted by x: `(0,0)`, `(1,1)`, `(5,5)`, `(9,0)`. Start with `best = 2`, the first two points.

| Visit | Evicted (`dx² > best`) | Band candidates (y within reach 2) | Best after | Band after |
|---|---|---|---:|---|
| `(0,0)` | — | — | 2 | `(0,0)` |
| `(1,1)` | — | `(0,0)`: distance 2, not smaller | 2 | `(0,0) (1,1)` |
| `(5,5)` | `(0,0)` (25), `(1,1)` (16) | — | 2 | `(5,5)` |
| `(9,0)` | `(5,5)` (16) | — | 2 | `(9,0)` |

Python's standard library has no balanced search tree. The code keeps the band in a plain list with `bisect`, which searches in O(log n) but inserts and deletes in O(n).

```python
from bisect import bisect_left, bisect_right, insort
from math import isqrt


def closest_pair_squared(points):
    """Smallest squared distance among integer points; None if fewer than two."""
    pts = sorted(points)
    if len(pts) < 2:
        return None
    # Any one pair gives an upper bound to start from.
    best = (pts[1][0] - pts[0][0]) ** 2 + (pts[1][1] - pts[0][1]) ** 2
    band = []  # (y, x) for earlier points still inside the x-band, sorted
    left = 0   # pts[left] is the oldest point possibly still in the band
    for x, y in pts:
        while (x - pts[left][0]) ** 2 > best:
            lx, ly = pts[left]
            band.pop(bisect_left(band, (ly, lx)))
            left += 1
        reach = isqrt(best) + 1
        lo = bisect_left(band, (y - reach, float("-inf")))
        hi = bisect_right(band, (y + reach, float("inf")))
        for by, bx in band[lo:hi]:
            distance = (x - bx) ** 2 + (y - by) ** 2
            if distance < best:
                best = distance
        insort(band, (y, x))
    return best


def main():
    assert closest_pair_squared([(0, 0), (5, 5), (1, 1), (9, 0)]) == 2
    assert closest_pair_squared([(3, 4), (3, 4)]) == 0
    assert closest_pair_squared([(0, 0)]) is None
    assert closest_pair_squared([(0, 0), (10**9, 10**9)]) == 2 * 10**18

    from itertools import combinations
    from random import Random
    rng = Random(101)
    for _ in range(400):
        pts = [(rng.randrange(-20, 21), rng.randrange(-20, 21))
               for _ in range(rng.randrange(2, 25))]
        expected = min((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                       for a, b in combinations(pts, 2))
        assert closest_pair_squared(pts) == expected


if __name__ == "__main__":
    main()
```

Every point enters and leaves the band once and checks O(1) candidates. With a balanced tree this is O(n log n). With the list, `insort` and `pop` shift elements, so the worst case is O(n²) element moves, though they are fast in practice.

## 2. Does any pair of segments intersect?

Given n line segments, decide whether any two of them intersect. All pairs is O(n²). The Shamos–Hoyos sweep answers in O(n log n) with a balanced tree.

Sweep x. The state is the list of segments crossing the current vertical line, **ordered by their y at that line**. A segment is inserted at its left endpoint and deleted at its right endpoint. The key rule: test only segments that have **just become neighbors** in the order.

- After inserting s, test s against the segments directly above and below it.
- Before deleting s, the segments above and below it become neighbors: test them against each other.

Segments `s0 = (0,0)–(10,10)`, `s1 = (1,4)–(4,5)`, `s2 = (2,8)–(11,2)`. s0 and s2 cross near x = 5.6, but s1 sits between them until x = 4:

| x | Event | Order, bottom to top | New neighbor pair tested | Intersect? |
|---:|---|---|---|---|
| 0 | insert s0 | s0 | — | |
| 1 | insert s1 | s0, s1 | s1–s0 | no |
| 2 | insert s2 | s0, s1, s2 | s2–s1 | no |
| 4 | delete s1 | s0, s2 | s0–s2 | **yes** |

Without the test at deletion, this input would be reported as intersection-free.

**Why neighbors are enough.** Let p be the leftmost intersection point, between segments a and b. Just left of p, no other segment lies between a and b in the y-order; such a segment would have to end, or cross a or b, before p. So a and b become neighbors at some event no later than p's x-coordinate: when the second of them is inserted, or when a segment between them is deleted. The test at that event finds them. Before p no two segments have crossed, so the stored y-order is still correct.

**Assumptions (general position).** No segment is vertical, and all 2n endpoint x-coordinates are distinct, so each event's place in the order is unambiguous. Real implementations handle vertical segments, shared endpoints and collinear overlaps with careful tie rules; that is where most bugs live.

y-values at the sweep line are computed with `Fraction`, so integer inputs never suffer rounding. The pairwise test uses the **orientation** (cross product) test and counts touching as intersecting.

```python
from fractions import Fraction


def orientation(p, q, r):
    """Sign of the cross product (q - p) x (r - p): 1 left turn, -1 right, 0 collinear."""
    value = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (value > 0) - (value < 0)


def on_segment(p, q, r):
    """For collinear p, q, r: does q lie on segment pr?"""
    return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))


def segments_intersect(s, t):
    """Closed segments; touching counts."""
    p1, p2 = s
    p3, p4 = t
    d1, d2 = orientation(p3, p4, p1), orientation(p3, p4, p2)
    d3, d4 = orientation(p1, p2, p3), orientation(p1, p2, p4)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return True
    return ((d1 == 0 and on_segment(p3, p1, p4)) or (d2 == 0 and on_segment(p3, p2, p4))
            or (d3 == 0 and on_segment(p1, p3, p2)) or (d4 == 0 and on_segment(p1, p4, p2)))


def y_at(segment, x):
    (x1, y1), (x2, y2) = segment
    return Fraction(y1) + Fraction((y2 - y1) * (x - x1), x2 - x1)


def any_segments_intersect(segments):
    """General position: no vertical segments, all endpoint x-coordinates distinct."""
    segs = [tuple(sorted(s)) for s in segments]  # left endpoint first
    events = []
    for i, (p, q) in enumerate(segs):
        if p[0] == q[0]:
            raise ValueError("vertical segment")
        events.append((p[0], 0, i))  # insert
        events.append((q[0], 1, i))  # delete
    active = []  # segment ids, ordered by y at the current x
    for x, kind, i in sorted(events):
        if kind == 0:
            y = y_at(segs[i], x)
            lo, hi = 0, len(active)
            while lo < hi:  # binary search by y at this x
                mid = (lo + hi) // 2
                if y_at(segs[active[mid]], x) < y:
                    lo = mid + 1
                else:
                    hi = mid
            active.insert(lo, i)
            for j in (lo - 1, lo + 1):
                if 0 <= j < len(active) and segments_intersect(segs[i], segs[active[j]]):
                    return True
        else:
            k = active.index(i)
            if 0 < k < len(active) - 1 and segments_intersect(
                    segs[active[k - 1]], segs[active[k + 1]]):
                return True
            active.pop(k)
    return False


def main():
    assert any_segments_intersect([((0, 0), (4, 4)), ((1, 3), (5, -1))])     # crossing
    assert not any_segments_intersect([((0, 0), (4, 1)), ((1, 3), (5, 4))])  # parallel-ish
    assert any_segments_intersect([((0, 0), (4, 4)), ((2, 2), (5, 0))])      # touching
    assert not any_segments_intersect([])
    # Found only when s1 is deleted and s0, s2 become neighbors.
    assert any_segments_intersect([((0, 0), (10, 10)), ((1, 4), (4, 5)), ((2, 8), (11, 2))])

    from itertools import combinations
    from random import Random
    rng = Random(103)
    tested = 0
    while tested < 400:
        n = rng.randrange(1, 8)
        xs = rng.sample(range(40), 2 * n)  # distinct endpoint x-coordinates
        segs = [((xs[2 * i], rng.randrange(-15, 16)), (xs[2 * i + 1], rng.randrange(-15, 16)))
                for i in range(n)]
        expected = any(segments_intersect(a, b) for a, b in combinations(segs, 2))
        assert any_segments_intersect(segs) == expected
        tested += 1


if __name__ == "__main__":
    main()
```

**Costs.** 2n events. With a balanced tree, each insert, delete and neighbor lookup is O(log n): O(n log n) in total. With the list here, `insert`, `index` and `pop` are O(n). **Reporting every** intersection is a different problem: the Bentley–Ottmann sweep also schedules each discovered crossing as a future event where two neighbors swap, and runs in O((n + k) log n) for k intersections.

## 3. Angular sweep: turn instead of slide

You stand at `location` and see everything within a field of view of `angle` degrees. Turning freely, how many points can you see at once? Points exactly at your location are always visible.

The sweep coordinate is the **direction** of each point as seen from the location, its polar angle from `atan2`. Sort the angles; a view is a window of sorted angles whose width is at most `angle`, so this is a [sliding window](../05-sliding-window/README.md) over the sorted list.

**Wrap-around.** Directions are circular. From `(0, 0)`, the points `(−10, 1)` and `(−10, −1)` are at 174.3° and −174.3°, only 11.4° apart across the 180° line, but far apart in sorted order. Append every angle plus 360 and slide over the doubled list:

```text
sorted:  -174.3   174.3
doubled: -174.3   174.3   185.7   534.3
                  └─ 11.4 ─┘   a 30° view sees both
```

```python
from math import atan2, degrees
from random import Random


def max_visible_points(points, angle, location):
    """Field of view `angle` degrees; points at the location are always visible."""
    ox, oy = location
    at_location = 0
    angles = []
    for x, y in points:
        if (x, y) == (ox, oy):
            at_location += 1
        else:
            angles.append(degrees(atan2(y - oy, x - ox)))
    angles.sort()
    doubled = angles + [a + 360 for a in angles]
    best = 0
    left = 0
    for right in range(len(doubled)):
        while doubled[right] - doubled[left] > angle + 1e-9:
            left += 1
        best = max(best, right - left + 1)
    return at_location + min(best, len(angles))


def main():
    assert max_visible_points([(2, 1), (2, 2), (3, 3)], 90, (1, 1)) == 3
    assert max_visible_points([(2, 1), (2, 2), (3, 4), (1, 1)], 90, (1, 1)) == 4
    assert max_visible_points([(1, 0), (2, 1)], 13, (1, 1)) == 1
    assert max_visible_points([(0, 1), (0, -1)], 180, (0, 0)) == 2   # exactly 180
    assert max_visible_points([(1, 0), (-1, 0)], 360, (0, 0)) == 2   # no double counting
    assert max_visible_points([], 45, (0, 0)) == 0
    assert max_visible_points([(-10, 1), (-10, -1)], 30, (0, 0)) == 2  # wraps past 180

    rng = Random(107)
    for _ in range(300):
        pts = [(rng.randrange(-4, 5), rng.randrange(-4, 5)) for _ in range(rng.randrange(10))]
        view = rng.choice([0, 30, 45, 90, 135, 180, 270, 360])
        here = [p for p in pts if p == (0, 0)]
        dirs = [degrees(atan2(y, x)) % 360 for x, y in pts if (x, y) != (0, 0)]
        # Brute force: a best view can start at some point's direction.
        best = max((sum((d - s) % 360 <= view + 1e-9 or abs((d - s) % 360 - 360) < 1e-9
                        for d in dirs) for s in dirs), default=0)
        assert max_visible_points(pts, view, (0, 0)) == len(here) + best


if __name__ == "__main__":
    main()
```

**Numerical model.** `atan2` returns floats, so two points in exactly the same direction can come out a few ulps apart. Sorting floats is still a valid total order. The tolerance `1e-9` appears only in the window-width comparison, never inside the sort, so the sort stays transitive. For exact work with integer points, compare directions by quadrant and cross product instead.

Sorting costs O(n log n), and each pointer moves at most 2n times.

**More angular sweeps.**

| Problem | Events around a center | State |
|---|---|---|
| Most points on a dartboard of radius r | For each point as a pivot, every other point within 2r gives an entry angle and an exit angle for a circle of radius r through the pivot | Counter over angles, as in [Your First Sweep](01-first-sweep-intervals.md); O(n² log n) overall |
| Visibility among segments from a viewpoint | Segment endpoints by angle | Segments ordered by distance along the current ray, as in §2 |
| Sorting points around a center (convex hull, polygon area) | Points by angle | None; the sorted order is the answer |

## 4. Pitfalls and practice

1. Comparing a new object with every active object instead of only its new neighbors.
2. Forgetting the neighbors that meet when an object is *removed* (§2).
3. Mixing exact and floating-point comparisons in one ordering.
4. Forgetting wrap-around in angular sweeps, or counting a point twice when the window covers the full circle.
5. Assuming `bisect.insort` gives O(log n) updates.

Practice: closest pair of points; detecting whether any two segments intersect; maximum number of visible points; maximum number of darts inside a circular dartboard.

Return to the [Sweep Line guide](README.md).
