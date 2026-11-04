# Sweep Line — Events, Active Sets, and Scenario Catalog

A sweep replaces a problem over many coordinates with the few moments when the answer can change. Sort those moments (events), keep exactly the information that matters between them (the active state), and pay per event instead of per coordinate. The folder starts with counting overlapping meetings and ends with rectangle areas, perimeters, closest pairs and segment intersections.

> **Learning path:** [1 First Sweep](01-first-sweep-intervals.md) → [2 Endpoint Semantics](02-endpoint-semantics-and-queries.md) → [3 Designing a Sweep](03-designing-a-sweep.md) → [4 Interval Scenarios](04-interval-scenarios.md) → [5 Offline Sweeps](05-offline-sweeps-and-fenwick.md) → [6 Geometric Sweeps](06-geometric-sweeps.md) → [7 Ordered-Set and Angular Sweeps](07-ordered-set-and-angular-sweeps.md)

## Chapters

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [Your First Sweep](01-first-sweep-intervals.md) | Why the count changes only at endpoints; events and slabs; a full step-by-step dry run; what happens at a shared endpoint for half-open vs closed intervals; coverage histograms | Maximum overlap, union length, length covered exactly k times, minimum rooms, car pooling |
| 2 | [Endpoint Semantics](02-endpoint-semantics-and-queries.md) | The order of work at one coordinate for half-open, closed and open intervals; closed integer ranges; queries as events; two sorted arrays instead of a loop | Closed maximum overlap, points covered by intervals, flowers in full bloom |
| 3 | [Designing a Sweep](03-designing-a-sweep.md) | The four decisions every sweep makes, each with its smallest failing example; slab vs point sweeps; proof by induction over events; honest cost analysis | — |
| 4 | [Interval Scenarios](04-interval-scenarios.md) | Heaps of busy and free rooms; two-pointer intersection; merging and gaps; greedy by end time with an exchange argument; online bookings | Meeting rooms with assignments, interval list intersections, employee free time, non-overlapping intervals, minimum arrows, my calendar I and III |
| 5 | [Offline Sweeps and Fenwick Trees](05-offline-sweeps-and-fenwick.md) | Sorting away one dimension; Fenwick tree over the other; coordinate compression; a heap with lazy expiration | Range counts below a threshold, points in rectangles, minimum interval for each query, count smaller to the right, horizontal–vertical intersections |
| 6 | [Geometric Sweeps](06-geometric-sweeps.md) | The coverage segment tree over y-gaps; skyline with a lazy heap; k-fold coverage; perimeter from three readings; when x is the wrong sweep order | Rectangle area II, skyline, area covered twice, union perimeter, perfect rectangle, falling squares |
| 7 | [Ordered-Set and Angular Sweeps](07-ordered-set-and-angular-sweeps.md) | The y-order of active objects as the state; testing only new neighbors; sweeping an angle with wrap-around | Closest pair, any segment intersection, maximum visible points |

Chapters 1–3 build the method on one running example. Chapters 4–7 apply it and can be read in any order; chapter 5 uses [Fenwick trees](../04-range-queries/02-fenwick-tree.md) and chapter 6 uses [segment trees](../04-range-queries/03-segment-tree.md).

## Recognizing the pattern

| The problem says or implies… | Sweep over | State | Where |
|---|---|---|---|
| "At the same time", "at once", "how many overlap", "how many rooms" | Endpoints | Counter | [1](01-first-sweep-intervals.md) |
| Total covered length or area, overlaps counted once | Endpoints / x | Counter, or coverage tree | [1](01-first-sweep-intervals.md), [6](06-geometric-sweeps.md) |
| Many queries, each with "value at most t" plus a range | The threshold | Fenwick tree | [5](05-offline-sweeps-and-fenwick.md) |
| "Shortest / tallest among those active at this point" | Points or x | Heap with lazy expiration | [5 §3](05-offline-sweeps-and-fenwick.md#3-a-heap-instead-of-a-fenwick-tree-smallest-interval-containing-each-query), [6 §4](06-geometric-sweeps.md#4-skyline-maximum-active-height-instead-of-union-length) |
| Keep / remove / pierce intervals with the fewest choices | End time | Last chosen end | [4 §4](04-interval-scenarios.md#4-greedy-by-end-time-keep-remove-or-pierce) |
| Pairs of nearby or crossing objects in the plane | x | Active objects ordered by y | [7](07-ordered-set-and-angular-sweeps.md) |
| "Field of view", "around a point" | Angle | Window of sorted angles | [7 §3](07-ordered-set-and-angular-sweeps.md#3-angular-sweep-turn-instead-of-slide) |

When each answer depends on what happened **earlier in time** rather than earlier along the line, process in time order instead ([6 §9](06-geometric-sweeps.md#9-where-sweeping-by-x-stops-falling-squares)).

## Scenario catalog

| Scenario | Sort by | Maintained structure | Time | Where |
|---|---|---|---:|---|
| Maximum simultaneous intervals, minimum rooms | Endpoint | Counter | O(n log n) | [1 §3](01-first-sweep-intervals.md#3-run-the-sweep-step-by-step) |
| Union length; length covered exactly or at least k times | Endpoint | Counter and histogram | O(n log n) | [1 §4–§5](01-first-sweep-intervals.md#4-one-counter-answers-several-questions) |
| Weighted load (car pooling) | Endpoint | Weighted counter | O(n log n) | [1 §8](01-first-sweep-intervals.md#weighted-events) |
| Maximum overlap of closed intervals | Endpoint, starts before ends | Counter | O(n log n) | [2 §3](02-endpoint-semantics-and-queries.md#3-closed-continuous-intervals-maximum-overlap) |
| How many intervals contain each query point | Endpoints and queries | Counter | O((n + q) log(n + q)) | [2 §5](02-endpoint-semantics-and-queries.md#5-point-queries-are-events-too) |
| Same, answered online (flowers in bloom) | — | Two sorted endpoint arrays | O((n + q) log n) | [2 §6](02-endpoint-semantics-and-queries.md#6-point-queries-without-a-loop-two-sorted-arrays) |
| Assign a room to each meeting | Start | Heaps of busy and free rooms | O(n log n) | [4 §1](04-interval-scenarios.md#1-room-assignment-which-room-does-each-meeting-get) |
| Intersection of two interval lists | Two pointers | Current interval of each list | O(n + m) | [4 §2](04-interval-scenarios.md#2-intersection-of-two-interval-lists) |
| Merge intervals; common free time | Start | Merge cursor | O(n log n) | [4 §3](04-interval-scenarios.md#3-free-time-the-gaps-in-a-union) |
| Most non-overlapping intervals; fewest removals; fewest arrows | End | Last kept end | O(n log n) | [4 §4](04-interval-scenarios.md#4-greedy-by-end-time-keep-remove-or-pierce) |
| Online bookings: reject double bookings, report maximum overlap | Arrival | Sorted list; difference map | O(n) per request here | [4 §5](04-interval-scenarios.md#5-online-bookings-when-requests-arrive-one-at-a-time) |
| Range counts `a[i] <= threshold` | Threshold | Fenwick over array positions | O((n + q) log(n + q)) | [5 §1](05-offline-sweeps-and-fenwick.md#1-range-counts-below-a-threshold) |
| Count points in rectangles | x | Fenwick over point y-values | O((n + q) log(n + q)) | [5 §2](05-offline-sweeps-and-fenwick.md#2-point-counts-in-rectangles-sweep-x-compress-y) |
| Smallest interval containing each query | Query point | Min-heap with lazy expiration | O((n + q) log n) | [5 §3](05-offline-sweeps-and-fenwick.md#3-a-heap-instead-of-a-fenwick-tree-smallest-interval-containing-each-query) |
| Count smaller to the right; inversions | Position, right to left | Fenwick over values | O(n log n) | [5 §4](05-offline-sweeps-and-fenwick.md#4-sweep-over-positions-count-smaller-elements-to-the-right) |
| Horizontal–vertical segment intersection counts | x | Fenwick over horizontal y-values | O((h + v) log(h + v)) | [5 §5](05-offline-sweeps-and-fenwick.md#5-horizontalvertical-segment-intersections) |
| Union area of rectangles | x | Coverage segment tree over y-gaps | O(n log n) | [6 §3](06-geometric-sweeps.md#3-full-implementation-rectangle-union-area) |
| Skyline | x | Heap with lazy expiration | O(n log n) | [6 §5](06-geometric-sweeps.md#5-full-implementation-skyline-with-lazy-expiration) |
| Area covered at least k times | x | Coverage tree with k lengths per node | O(kn log n) | [6 §6](06-geometric-sweeps.md#6-area-covered-at-least-k-times) |
| Union perimeter | x, then y | Coverage segment tree | O(n log n) | [6 §7](06-geometric-sweeps.md#7-union-perimeter) |
| Exact tiling (perfect rectangle) | — | Corner parity set, or two area sweeps | O(n) or O(n log n) | [6 §8](06-geometric-sweeps.md#8-perfect-rectangle-do-the-pieces-tile-a-rectangle-exactly) |
| Falling squares | Drop order, not x | Height profile | O(n²), or O(n log n) with a lazy segment tree | [6 §9](06-geometric-sweeps.md#9-where-sweeping-by-x-stops-falling-squares) |
| Closest pair of points | x | Points in an x-band, ordered by y | O(n log n) with a balanced tree | [7 §1](07-ordered-set-and-angular-sweeps.md#1-closest-pair-of-points) |
| Does any pair of segments intersect? | Endpoint x | Segments ordered by y at the sweep line | O(n log n) with a balanced tree | [7 §2](07-ordered-set-and-angular-sweeps.md#2-does-any-pair-of-segments-intersect) |
| Maximum points within a viewing angle | Polar angle | Sliding window over doubled angles | O(n log n) | [7 §3](07-ordered-set-and-angular-sweeps.md#3-angular-sweep-turn-instead-of-slide) |

Sorting is only part of the cost. A sweep that rebuilds its active set at every event can still be quadratic, and general segment sweeps can meet Θ(n²) intersections, so the interval and rectangle bounds above do not carry over to every geometric sweep.

## Conventions

- **Continuous intervals and geometry:** half-open `[l, r)` and rectangles `[x1, x2) × [y1, y2)`. Empty intervals and zero-area rectangles contribute nothing. Touching boundaries create no positive-length overlap or positive-area intersection.
- **Closed integer intervals:** `[l, r]` includes both integer endpoints. When counting integer positions, convert to `[l, r + 1)` and reuse the half-open code; `[4, 4]` becomes `[4, 5)`, one position.
- **Array query ranges** stay inclusive `[l, r]`, matching [Range Queries](../04-range-queries/README.md).
- **Coordinates** in the examples are integers, for exact arithmetic. Coordinate compression keeps order but not distance; lengths and areas use the original coordinates.
- **Inputs:** reversed endpoints raise `ValueError`; duplicate intervals keep their multiplicity.
- Every Python block is a complete script using only the standard library, with assertions on boundary cases and a fixed-seed brute-force comparison.

## Connections to other topics

- [Prefix Sums and Difference Arrays](../04-range-queries/01-prefix-sums.md): an endpoint sweep is a sparse difference array followed by a prefix sum.
- [Fenwick Trees](../04-range-queries/02-fenwick-tree.md) and [Segment Trees](../04-range-queries/03-segment-tree.md): sorting decides which objects are active; the tree answers questions about the remaining dimension or maintains a covered length.
- [Heaps](../07-heaps-and-priority-queues/README.md): room assignment, skyline and shortest-containing-interval keep their active set in a heap with lazy expiration.
- [Sliding Window](../05-sliding-window/README.md): both move through an ordered domain; a window keeps one contiguous run, while a sweep may expire any active object.
- [Monotonic Stacks and Deques](../06-monotonic-stack-and-deque/README.md): these discard candidates by dominance; a sweep instead schedules when objects become relevant and stop being relevant.
- [Math and Geometry](../12-math-and-geometry/README.md): orientation tests, cross products and polar angles used in chapter 7.

## Suggested practice order

1. Maximum meeting concurrency with half-open and with closed endpoints.
2. Union length and the lengths covered exactly once, twice and three times.
3. Point queries: flowers in full bloom, first with a sweep, then with two sorted arrays.
4. Interval scenarios: meeting rooms with assignments, interval list intersections, employee free time, non-overlapping intervals, minimum arrows, my calendar I and III.
5. Offline sweeps: range counts below a threshold, minimum interval to include each query, count of smaller numbers after self.
6. Points in rectangles with duplicate points on boundaries; horizontal–vertical segment intersections.
7. Skyline with duplicate buildings and equal x-events.
8. Rectangle union area with nested, touching and repeated rectangles; then area covered at least twice, union perimeter and perfect rectangle.
9. Closest pair, segment intersection detection and maximum visible points.

For every solution, write the active-state invariant and the order of work at equal coordinates before writing the event tuple.
