# Designing a Sweep — Events, Invariants, and Honest Analysis

## 1. Two sweeps side by side

Put the two sweeps built so far next to each other, on the meetings `[2, 5)`, `[4, 7)`, `[7, 9)` with one extra question: how many meetings are in the room at time 7?

| | Union length ([First Sweep](01-first-sweep-intervals.md#3-run-the-sweep-step-by-step)) | Point query at 7 ([Endpoint Semantics](02-endpoint-semantics-and-queries.md#5-point-queries-are-events-too)) |
|---|---|---|
| What the line moves along | Time | Time |
| Where something happens | Endpoints 2, 4, 5, 7, 9 | Endpoints, plus the query at 7 |
| What is remembered between events | `active`, the count on the current slab | `active`, the count at the current point |
| When `active` is read | Before the changes at x: it describes the slab `[previous, x)` | After the changes at `<= 7`: it describes the point 7 |
| Answer | 7 | 1 |

The two columns differ in one row, *when the state is read*, and that row decides correctness. The other rows are choices too. Any new sweep needs the same four.

## 2. The four decisions

Each decision below comes with the smallest example of getting it wrong.

### Choose the sweep coordinate

For meetings it was time. It can be any sortable key: x-position, a value threshold ([Offline Sweeps](05-offline-sweeps-and-fenwick.md)), an array position, an end time for a greedy choice ([Interval Scenarios §4](04-interval-scenarios.md#4-greedy-by-end-time-keep-remove-or-pierce)), or an angle ([Angular Sweep](07-ordered-set-and-angular-sweeps.md#3-angular-sweep-turn-instead-of-slide)).

**The order must respect every dependency.** Squares dropped onto a line land on whatever fell **earlier in time**. Drop `[2, 4)` first and `[0, 3)` second: the second lands on the first. Sorted by x, `[0, 3)` would be placed first and land on the ground. Sweeping by x is wrong here ([Geometric Sweeps §9](06-geometric-sweeps.md#9-where-sweeping-by-x-stops-falling-squares)).

### List every state change as an event

An interval becomes active at its start and inactive at its end, so the count can change only at endpoints. An offline threshold query `value <= t` makes each item eligible once, when `t` reaches its value, and it never expires.

**If the answer can change between events, the event list is incomplete.** Two line segments that cross between their endpoints swap their up–down order at the crossing. A sweep that keeps segments in that order must add the crossing as an event ([Ordered-Set Sweeps §2](07-ordered-set-and-angular-sweeps.md#2-does-any-pair-of-segments-intersect)).

### Define exactly what the state means

The invariant behind the union-length sweep is:

> After processing all events at x, `active` counts the intervals covering every point in `[x, next_x)`.

It names a moment in the algorithm ("after processing all events at x") and a set of points ("every point in `[x, next_x)`"). With that sentence, the order "measure `[previous, x)`, then apply the events" follows. Without it, a natural-looking reorder breaks: apply the `+1` at x = 4 first, and the slab `[2, 4)` is multiplied by `active = 2`, adding 2 extra units to the union. "Maintain the current overlaps" is too vague to rule this out.

### Keep the cheapest summary that answers the question

Union length and maximum overlap need only a count. The point query needs only a count, and a count splits into starts minus ends, so even the sweep loop can go ([Endpoint Semantics §6](02-endpoint-semantics-and-queries.md#6-point-queries-without-a-loop-two-sorted-arrays)).

**A summary that is too small cannot answer.** Buildings `[0, 4)` of height 3 and `[1, 2)` of height 7 give `active = 2` on `[1, 2)`. The count does not say the skyline there is 7. That question needs the maximum active height, kept in a heap ([Geometric Sweeps §4](06-geometric-sweeps.md#4-skyline-maximum-active-height-instead-of-union-length)). Later chapters replace the counter with heaps, Fenwick trees, segment trees and ordered sets; the [scenario catalog](README.md#scenario-catalog) lists which problem uses which.

## 3. Two shapes of sweep

The "when is the state read" row from §1 splits all sweeps in this folder into two shapes.

**Measuring slabs** (union length, area):

1. Before the events at x, the state describes the slab `[previous_x, x)`.
2. Add `slab_measure(state) * (x - previous_x)`.
3. Apply every event at x.
4. The state now describes `[x, next_x)`.

Endpoint ties do not matter here: a slab of width 0 adds nothing.

**Answering at points** (point queries, maximum overlap). Read the state *at* x. Whether objects starting or ending at x are visible is part of the problem statement, and it fixes the order of work at x ([Endpoint Semantics §2](02-endpoint-semantics-and-queries.md#2-the-processing-order-rule)).

## 4. Proving a sweep correct

Use induction over the sorted event coordinates. For the point-query sweep:

1. **Initialization:** before the first endpoint, no interval is active.
2. **Maintenance:** a start adds one interval and an end removes one. After all changes at coordinates `<= x`, the count is exactly the intervals with `l <= x < r`.
3. **Completeness:** every change in membership happens at an endpoint, so nothing is hidden between events.
4. **Answer:** the query reads the maintained count.

When the state is a data structure instead of a counter, prove two invariants: one for the sweep (which objects are active) and one for the structure (its stored aggregate matches those objects).

## 5. Analyzing a sweep honestly

Write the cost as

$$\text{sort cost} + (\text{number of events}) \times (\text{cost per event}) + \text{query and output cost}.$$

The middle term is where analyses go wrong:

- "Each object is inserted and removed once" gives O(n) *operations*. With a heap or a tree, each costs O(log n).
- If each event scans every active object, the cost per event is O(n) and the total is O(n²), even though the events were sorted in O(n log n).
- If events are discovered during the sweep (segment crossings), bound their number separately. n segments can have Θ(n²) crossings.

## 6. Pitfalls and practice

1. Sorting ties by tuple order without deciding what a reading at an endpoint should see.
2. Measuring a slab after updating the state for the next slab.
3. Deduplicating identical intervals when they represent distinct participants.
4. Treating compressed rank differences as physical distances.
5. Using `r + 1` to convert closed **continuous** intervals. That works only on an integer lattice.
6. Using an offline sweep when answers must be returned before future queries or updates are known.

Practice: before writing any code, write the four decisions and the invariant for restaurant occupancy, jobs with cooldown intervals, points covered by closed integer ranges, and queries asking how many values have become eligible at each threshold.

Next: [Interval Scenarios](04-interval-scenarios.md).
