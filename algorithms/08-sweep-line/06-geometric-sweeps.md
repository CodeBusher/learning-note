# Geometric Sweeps — Area, Perimeter, Skyline, and Tilings

Rectangles here are half-open, `[x1, x2) × [y1, y2)`, and buildings are `[left, right) × [0, height)`. Empty objects contribute nothing; reversed endpoints and negative heights raise `ValueError`. Integer coordinates keep the arithmetic exact.

## 1. Rectangle union area

Two rectangles, `[0, 3) × [0, 2)` and `[1, 4) × [1, 3)`. What area do they cover together?

```text
y
3 .  B  B  B
2 .  B  B  B          A = [0,3) x [0,2)
1 A  AB AB B          B = [1,4) x [1,3)
0 A  A  A  .
  0  1  2  3  4  x
```

**Brute force:** count unit cells, 10 here. That costs time proportional to the area, which is useless for large or real coordinates. Inclusion–exclusion (`6 + 6 − 2 = 10`) does not scale to many rectangles either.

**Observation.** Move a vertical line from left to right. At each x it crosses some set of rectangles, and the line's **covered y-length** is the length of the union of their y-intervals. That set changes only at rectangle x-endpoints, so on each slab between consecutive x-endpoints the covered y-length is constant. This is [union length](01-first-sweep-intervals.md#3-run-the-sweep-step-by-step) one dimension up: measure each slab before applying its right-boundary events.

$$\text{area} \mathrel{+}= \text{covered\_y\_length} \times (x - \text{previous\_x}).$$

| x-slab | Active rectangles | Active y-union | Covered y-length | Slab area |
|---|---|---|---:|---:|
| `[0, 1)` | A | `[0, 2)` | 2 | 2 |
| `[1, 3)` | A, B | `[0, 3)` | 3 | 6 |
| `[3, 4)` | B | `[1, 3)` | 2 | 2 |

Total 10. The hard part is the third column: maintaining the covered y-length while y-intervals are added and removed. Summing the active heights double-counts overlaps (it would give 4 on `[1, 3)`), and a Fenwick tree of point counts knows nothing about the length of a union.

## 2. The coverage tree: compress gaps, not endpoints

The distinct y-endpoints are `ys = [0, 1, 2, 3]`. Every active y-interval is a union of the **gaps** between consecutive values: `[0, 1)`, `[1, 2)`, `[2, 3)`. Build a segment tree whose leaves are these gaps. Gap i has physical length `ys[i + 1] − ys[i]`, so unequal gaps such as `[2, 5)` and `[5, 9)` keep their true lengths 3 and 4.

A node spanning gap indices `[lo, hi)` stores two numbers:

- `cover[node]`: how many active intervals cover this **whole node** and stopped here when the update was split into tree nodes.
- `length[node]`: the covered length inside the node.

The pull rule, applied on the way back up from every update:

1. If `cover[node] > 0`, the whole node is covered: `length = ys[hi] − ys[lo]`.
2. Otherwise, a leaf has `length = 0`.
3. Otherwise, `length` is the sum of the children's lengths.

The tree for three gaps: root `[0,3)` with children `[0,1)` (a leaf) and `[1,3)`, which splits into `[1,2)` and `[2,3)`. Sweep the example:

| x | Update | Nodes whose `cover` changes | `length` of `[0,1)`, `[1,2)`, `[1,3)` | Root length |
|---:|---|---|---|---:|
| 0 | add A's `[0, 2)` | `[0,1)` → 1, `[1,2)` → 1 | 1, 1, 1 | 2 |
| 1 | add B's `[1, 3)` | `[1,3)` → 1 | 1, 1, **2** | 3 |
| 3 | remove A's `[0, 2)` | `[0,1)` → 0, `[1,2)` → 0 | 0, 0, **2** | 2 |
| 4 | remove B's `[1, 3)` | `[1,3)` → 0 | 0, 0, 0 | 0 |

Row x = 3 is the subtle one. The leaf `[1,2)` loses its cover, but its parent `[1,3)` still has `cover = 1` from B, so rule 1 keeps the parent's length at 2. Child counts are never pushed down. They stay where the update left them, hidden while a parent covers them, and they show again once the parent's cover drops to 0. That is why this tree needs no lazy propagation, and also why it only supports removing intervals that were added before: every removal hits exactly the nodes its insertion hit.

## 3. Full implementation: rectangle union area

```python
class CoveredLengthTree:
    """Leaves are half-open coordinate gaps [ys[i], ys[i + 1])."""

    def __init__(self, ys):
        self.ys = ys
        self.n = len(ys) - 1
        self.cover = [0] * (4 * max(1, self.n))
        self.length = [0] * (4 * max(1, self.n))

    def _pull(self, node, lo, hi):
        if self.cover[node] > 0:
            self.length[node] = self.ys[hi] - self.ys[lo]
        elif hi - lo == 1:
            self.length[node] = 0
        else:
            self.length[node] = self.length[node * 2] + self.length[node * 2 + 1]

    def add(self, left, right, delta):
        """Add to gap-index range [left, right), using half-open indices."""
        if not 0 <= left <= right <= self.n:
            raise IndexError("gap range out of bounds")
        if left < right:
            self._add(1, 0, self.n, left, right, delta)

    def _add(self, node, lo, hi, left, right, delta):
        if left <= lo and hi <= right:
            self.cover[node] += delta
        else:
            mid = (lo + hi) // 2
            if left < mid:
                self._add(node * 2, lo, mid, left, right, delta)
            if mid < right:
                self._add(node * 2 + 1, mid, hi, left, right, delta)
        self._pull(node, lo, hi)

    @property
    def covered_length(self):
        return self.length[1] if self.n else 0


def rectangle_union_area(rectangles):
    """Area of the union of half-open rectangles (x1, y1, x2, y2)."""
    valid = []
    for x1, y1, x2, y2 in rectangles:
        if x1 > x2 or y1 > y2:
            raise ValueError("reversed rectangle")
        if x1 < x2 and y1 < y2:
            valid.append((x1, y1, x2, y2))
    if not valid:
        return 0
    ys = sorted({y for _, y1, _, y2 in valid for y in (y1, y2)})
    rank = {y: i for i, y in enumerate(ys)}
    events = []
    for x1, y1, x2, y2 in valid:
        events.append((x1, 1, rank[y1], rank[y2]))
        events.append((x2, -1, rank[y1], rank[y2]))
    events.sort()
    tree = CoveredLengthTree(ys)
    previous_x = events[0][0]
    area = 0
    index = 0
    while index < len(events):
        x = events[index][0]
        # Current tree describes the preceding slab [previous_x, x).
        area += tree.covered_length * (x - previous_x)
        while index < len(events) and events[index][0] == x:
            _, delta, left, right = events[index]
            tree.add(left, right, delta)
            index += 1
        previous_x = x
    assert tree.covered_length == 0
    return area


def main():
    assert rectangle_union_area([(0, 0, 3, 2), (1, 1, 4, 3)]) == 10
    assert rectangle_union_area([(0, 0, 2, 2), (2, 0, 4, 2)]) == 8
    assert rectangle_union_area([(0, 0, 4, 4), (1, 1, 2, 2)]) == 16
    assert rectangle_union_area([(0, 0, 2, 3), (0, 0, 2, 3)]) == 6
    assert rectangle_union_area([(1, 0, 1, 5), (0, 3, 5, 3)]) == 0
    assert rectangle_union_area([]) == 0
    assert rectangle_union_area([(0, 0, 1, 10**12)]) == 10**12

    from random import Random
    rng = Random(31)
    for _ in range(300):
        rectangles = []
        cells = set()
        for _ in range(rng.randrange(10)):
            x1, x2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            y1, y2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            rectangles.append((x1, y1, x2, y2))
            cells.update((x, y) for x in range(x1, x2) for y in range(y1, y2))
        assert rectangle_union_area(rectangles) == len(cells)


if __name__ == "__main__":
    main()
```

**Why it is correct.** By induction over the tree: a positive `cover` covers the whole node, and otherwise only the children can supply coverage, over disjoint parts. So the root length is exactly the active y-union. After the events at x it describes the slab `[x, next_x)`, and the slabs partition the plane, so summing width × length gives the area.

There are 2n events and at most 2n y-values. Each update visits O(log n) nodes and reading the root is O(1): O(n log n) time, O(n) space, recursion depth O(log n).

## 4. Skyline: maximum active height instead of union length

Buildings `(left, right, height)`. Report the **key points** `(x, new_height)` where the visible outline changes height.

Buildings `(1, 5, 3)` and `(2, 4, 7)` give `(1, 3), (2, 7), (4, 3), (5, 0)`.

The cross section is now the **maximum active height**, so keep the started buildings in a max-heap of `(−height, right)`. Ended buildings are removed lazily: at x, pop the top while its `right <= x`. An ended building buried under a taller live one does no harm; it is popped when it reaches the top. At each x, push every building starting at x before reading, so a coordinate gets at most one key point.

| x | Pushed | Popped (`right <= x`) | Top height | Key point |
|---:|---|---|---:|---|
| 1 | `(−3, 5)` | — | 3 | `(1, 3)` |
| 2 | `(−7, 4)` | — | 7 | `(2, 7)` |
| 4 | — | `(−7, 4)` | 3 | `(4, 3)` |
| 5 | — | `(−3, 5)` | 0 | `(5, 0)` |

Touching buildings `(1, 3, 2)` and `(3, 5, 2)` produce no key point at 3: the height stays 2.

## 5. Full implementation: skyline with lazy expiration

```python
from heapq import heappop, heappush


def skyline(buildings):
    """Buildings occupy half-open [left, right) with nonnegative heights."""
    starts = {}
    coordinates = set()
    for left, right, height in buildings:
        if left > right or height < 0:
            raise ValueError("invalid building")
        if left == right or height == 0:
            continue
        starts.setdefault(left, []).append((-height, right))
        coordinates.add(left)
        coordinates.add(right)
    heap = []
    result = []
    previous_height = 0
    for x in sorted(coordinates):
        for entry in starts.get(x, ()):
            heappush(heap, entry)
        while heap and heap[0][1] <= x:
            heappop(heap)
        current_height = -heap[0][0] if heap else 0
        if current_height != previous_height:
            result.append((x, current_height))
            previous_height = current_height
    return result


def main():
    assert skyline([(1, 3, 2), (3, 5, 2)]) == [(1, 2), (5, 0)]
    assert skyline([(1, 5, 3), (2, 4, 7)]) == [(1, 3), (2, 7), (4, 3), (5, 0)]
    assert skyline([(1, 4, 5), (1, 4, 5)]) == [(1, 5), (4, 0)]
    assert skyline([(0, 2, 2), (1, 3, 5), (2, 4, 3)]) == [
        (0, 2), (1, 5), (3, 3), (4, 0)]
    assert skyline([(1, 1, 8), (0, 3, 0)]) == []
    assert skyline([]) == []

    from random import Random
    rng = Random(37)
    for _ in range(200):
        buildings = []
        for _ in range(rng.randrange(12)):
            left, right = sorted((rng.randrange(-3, 5), rng.randrange(-3, 5)))
            buildings.append((left, right, rng.randrange(6)))
        xs = sorted({x for l, r, h in buildings if l < r and h > 0 for x in (l, r)})
        expected = []
        previous = 0
        for x in xs:
            height = max((h for l, r, h in buildings if l <= x < r), default=0)
            if height != previous:
                expected.append((x, height))
                previous = height
        assert skyline(buildings) == expected


if __name__ == "__main__":
    main()
```

Every building is pushed once and popped at most once: O(n log n) time, O(n) space. One x can pop many buildings, but each pop is charged to its own building.

## 6. Area covered at least k times

Same sweep, but count only area covered by **at least k** rectangles, for example where two ads overlap.

Replace the single `length[node]` by a row `at_least[node][c]` for `c = 1..k`: the length inside the node covered by at least c active intervals. The pull rule generalizes §2:

1. If `cover[node] >= c`, intervals stored right here cover the whole node c times: full length.
2. Otherwise, a leaf gets 0.
3. Otherwise, this node already supplies `cover[node]` layers everywhere, so the children must supply the remaining `c − cover[node]`: `left.at_least[c − cover] + right.at_least[c − cover]`.

With k = 1 this is exactly §2. Each update now costs O(k log n).

```python
class KCoverTree:
    """at_least[node][c] = length in the node covered by >= c active intervals."""

    def __init__(self, ys, k):
        self.ys = ys
        self.k = k
        self.n = len(ys) - 1
        size = 4 * max(1, self.n)
        self.cover = [0] * size
        self.at_least = [[0] * (k + 1) for _ in range(size)]

    def _pull(self, node, lo, hi):
        full = self.ys[hi] - self.ys[lo]
        here = self.cover[node]
        row = self.at_least[node]
        for c in range(1, self.k + 1):
            if here >= c:
                row[c] = full
            elif hi - lo == 1:
                row[c] = 0
            else:
                row[c] = (self.at_least[node * 2][c - here]
                          + self.at_least[node * 2 + 1][c - here])

    def add(self, left, right, delta):
        if left < right:
            self._add(1, 0, self.n, left, right, delta)

    def _add(self, node, lo, hi, left, right, delta):
        if left <= lo and hi <= right:
            self.cover[node] += delta
        else:
            mid = (lo + hi) // 2
            if left < mid:
                self._add(node * 2, lo, mid, left, right, delta)
            if mid < right:
                self._add(node * 2 + 1, mid, hi, left, right, delta)
        self._pull(node, lo, hi)


def area_covered_at_least(rectangles, k):
    """Half-open rectangles (x1, y1, x2, y2); area covered by >= k of them."""
    if k < 1:
        raise ValueError("k must be positive")
    valid = []
    for x1, y1, x2, y2 in rectangles:
        if x1 > x2 or y1 > y2:
            raise ValueError("reversed rectangle")
        if x1 < x2 and y1 < y2:
            valid.append((x1, y1, x2, y2))
    if not valid:
        return 0
    ys = sorted({y for _, y1, _, y2 in valid for y in (y1, y2)})
    rank = {y: i for i, y in enumerate(ys)}
    events = sorted([(x1, 1, rank[y1], rank[y2]) for x1, y1, _, y2 in valid]
                    + [(x2, -1, rank[y1], rank[y2]) for _, y1, x2, y2 in valid])
    tree = KCoverTree(ys, k)
    area = 0
    previous_x = events[0][0]
    for x, delta, left, right in events:
        area += tree.at_least[1][k] * (x - previous_x)
        tree.add(left, right, delta)
        previous_x = x
    return area


def main():
    rects = [(0, 0, 3, 2), (1, 1, 4, 3), (2, 0, 5, 3)]
    assert area_covered_at_least(rects, 1) == 14
    assert area_covered_at_least(rects, 2) == 6
    assert area_covered_at_least(rects, 3) == 1
    assert area_covered_at_least(rects, 4) == 0

    from random import Random
    rng = Random(79)
    for _ in range(300):
        rects = []
        for _ in range(rng.randrange(8)):
            x1, x2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            y1, y2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            rects.append((x1, y1, x2, y2))
        for k in (1, 2, 3):
            cells = sum(sum(x1 <= x < x2 and y1 <= y < y2 for x1, y1, x2, y2 in rects) >= k
                        for x in range(-3, 4) for y in range(-3, 4))
            assert area_covered_at_least(rects, k) == cells


if __name__ == "__main__":
    main()
```

The loop measures before every single event rather than once per x. Two events at the same x leave a slab of width 0 between them, which adds nothing.

## 7. Union perimeter

The boundary of a union of rectangles is made of vertical and horizontal edges. Count them separately.

**Vertical edges.** Let L be the covered y-set immediately left of x and R the covered y-set immediately right of x. A boundary edge at x exists exactly where y is covered on one side and not the other, so its length is the symmetric difference `|L Δ R|`.

The net change `|R| − |L|` is **not** enough. Rectangles `[0, 1) × [0, 2)` and `[1, 2) × [1, 3)`: at x = 1, the stretch `[0, 1)` stops being covered while `[2, 3)` starts. The net change is 0, but the boundary there has length 2.

The tree gives lengths, not sets, but one extra reading suffices. At each x read three lengths:

- `left` = |L|, before any event at x;
- `left_or_starts` after adding the rectangles starting at x but before removing those ending there. Every y in R is either still covered from the left or covered by a start, so this is |L ∪ R|;
- `right` = |R|, after both.

$$|L \,\Delta\, R| = 2\,|L \cup R| - |L| - |R| = 2 \cdot \text{left\_or\_starts} - \text{left} - \text{right}.$$

In the example at x = 1: `left = 2`, `left_or_starts = 3`, `right = 2`, so the edge length is `6 − 4 = 2`. For two unit squares touching at x = 1, all three readings are 1 and the formula gives 0: that line is inside the union.

Horizontal edges are the same computation with x and y swapped.

```python
class CoveredLengthTree:
    """Leaves are half-open coordinate gaps [ys[i], ys[i + 1])."""

    def __init__(self, ys):
        self.ys = ys
        self.n = len(ys) - 1
        self.cover = [0] * (4 * max(1, self.n))
        self.length = [0] * (4 * max(1, self.n))

    def _pull(self, node, lo, hi):
        if self.cover[node] > 0:
            self.length[node] = self.ys[hi] - self.ys[lo]
        elif hi - lo == 1:
            self.length[node] = 0
        else:
            self.length[node] = self.length[node * 2] + self.length[node * 2 + 1]

    def add(self, left, right, delta):
        if left < right:
            self._add(1, 0, self.n, left, right, delta)

    def _add(self, node, lo, hi, left, right, delta):
        if left <= lo and hi <= right:
            self.cover[node] += delta
        else:
            mid = (lo + hi) // 2
            if left < mid:
                self._add(node * 2, lo, mid, left, right, delta)
            if mid < right:
                self._add(node * 2 + 1, mid, hi, left, right, delta)
        self._pull(node, lo, hi)

    @property
    def covered_length(self):
        return self.length[1] if self.n else 0


def _vertical_boundary(rects):
    """Total length of vertical edges of the union of half-open rectangles."""
    ys = sorted({y for _, y1, _, y2 in rects for y in (y1, y2)})
    rank = {y: i for i, y in enumerate(ys)}
    starts, ends = {}, {}
    for x1, y1, x2, y2 in rects:
        starts.setdefault(x1, []).append((rank[y1], rank[y2]))
        ends.setdefault(x2, []).append((rank[y1], rank[y2]))
    tree = CoveredLengthTree(ys)
    total = 0
    for x in sorted(starts.keys() | ends.keys()):
        left = tree.covered_length
        for low, high in starts.get(x, ()):
            tree.add(low, high, 1)
        left_or_starts = tree.covered_length
        for low, high in ends.get(x, ()):
            tree.add(low, high, -1)
        right = tree.covered_length
        total += 2 * left_or_starts - left - right
    return total


def union_perimeter(rectangles):
    valid = []
    for x1, y1, x2, y2 in rectangles:
        if x1 > x2 or y1 > y2:
            raise ValueError("reversed rectangle")
        if x1 < x2 and y1 < y2:
            valid.append((x1, y1, x2, y2))
    if not valid:
        return 0
    transposed = [(y1, x1, y2, x2) for x1, y1, x2, y2 in valid]
    return _vertical_boundary(valid) + _vertical_boundary(transposed)


def main():
    assert union_perimeter([(0, 0, 2, 2)]) == 8
    assert union_perimeter([(0, 0, 1, 1), (1, 0, 2, 1)]) == 6   # touching side
    assert union_perimeter([(0, 0, 4, 4), (1, 1, 2, 2)]) == 16  # nested
    assert union_perimeter([(0, 0, 2, 1), (1, 1, 3, 2)]) == 10  # share edge y=1, x in [1, 2)
    assert union_perimeter([(0, 0, 1, 1), (1, 1, 2, 2)]) == 8   # touch only at a corner
    assert union_perimeter([(0, 0, 1, 2), (1, 1, 2, 3)]) == 10  # x=1: one ends, one starts

    from random import Random
    rng = Random(83)
    for _ in range(400):
        rects, cells = [], set()
        for _ in range(rng.randrange(7)):
            x1, x2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            y1, y2 = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
            rects.append((x1, y1, x2, y2))
            cells.update((x, y) for x in range(x1, x2) for y in range(y1, y2))
        expected = sum((x + dx, y + dy) not in cells
                       for x, y in cells
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        assert union_perimeter(rects) == expected


if __name__ == "__main__":
    main()
```

The random test counts unit cell sides that face an uncovered cell. Time O(n log n), space O(n).

## 8. Perfect rectangle: do the pieces tile a rectangle exactly?

Given rectangles with positive area, decide whether together they cover their bounding box with **no gaps and no overlaps**.

**With the area sweep, O(n log n).** Using `rectangle_union_area` from §3:

- no positive-area overlap ⟺ union area = sum of the individual areas;
- no gap ⟺ union area = bounding-box area.

**Corner parity, O(n).** Toggle each rectangle's four corners in a set. In an exact tiling, a corner point inside the box is shared by 2 or 4 pieces, and one on the box's edge by 2, so they all cancel. Only the four box corners belong to exactly one piece. So the set must end as exactly those four points, and the areas must also add up to the box area. Proving that these two conditions rule out every overlap takes a short case analysis; the random test below checks the claim against a cell-count brute force.

```python
def is_perfect_rectangle(rectangles):
    """Half-open integer rectangles (x1, y1, x2, y2), each with positive area."""
    if not rectangles:
        return False
    corners = set()
    area = 0
    for x1, y1, x2, y2 in rectangles:
        if x1 >= x2 or y1 >= y2:
            raise ValueError("rectangles must have positive area")
        area += (x2 - x1) * (y2 - y1)
        for corner in ((x1, y1), (x1, y2), (x2, y1), (x2, y2)):
            corners ^= {corner}
    bx1 = min(r[0] for r in rectangles)
    by1 = min(r[1] for r in rectangles)
    bx2 = max(r[2] for r in rectangles)
    by2 = max(r[3] for r in rectangles)
    return (area == (bx2 - bx1) * (by2 - by1)
            and corners == {(bx1, by1), (bx1, by2), (bx2, by1), (bx2, by2)})


def main():
    tiling = [(1, 1, 3, 3), (3, 1, 4, 2), (3, 2, 4, 4), (1, 3, 2, 4), (2, 3, 3, 4)]
    assert is_perfect_rectangle(tiling)
    assert not is_perfect_rectangle([(1, 1, 2, 3), (1, 3, 2, 4), (3, 1, 4, 2), (3, 2, 4, 4)])
    assert not is_perfect_rectangle([(1, 1, 3, 3), (3, 1, 4, 2), (1, 3, 2, 4), (2, 2, 4, 4)])

    from random import Random
    rng = Random(89)

    def split(x1, y1, x2, y2, depth):
        """Random guillotine tiling of a box."""
        if depth == 0 or rng.random() < 0.3:
            return [(x1, y1, x2, y2)]
        if x2 - x1 > 1 and (y2 - y1 == 1 or rng.random() < 0.5):
            m = rng.randrange(x1 + 1, x2)
            return split(x1, y1, m, y2, depth - 1) + split(m, y1, x2, y2, depth - 1)
        if y2 - y1 > 1:
            m = rng.randrange(y1 + 1, y2)
            return split(x1, y1, x2, m, depth - 1) + split(x1, m, x2, y2, depth - 1)
        return [(x1, y1, x2, y2)]

    for _ in range(400):
        rects = split(0, 0, rng.randrange(1, 6), rng.randrange(1, 6), 4)
        if rng.random() < 0.6:  # perturb: drop, duplicate, or move a piece
            i = rng.randrange(len(rects))
            choice = rng.randrange(3)
            if choice == 0 and len(rects) > 1:
                rects.pop(i)
            elif choice == 1:
                rects.append(rects[i])
            else:
                x1, y1, x2, y2 = rects[i]
                dx, dy = rng.randrange(-1, 2), rng.randrange(-1, 2)
                rects[i] = (x1 + dx, y1 + dy, x2 + dx, y2 + dy)
        counts = {}
        for x1, y1, x2, y2 in rects:
            for x in range(x1, x2):
                for y in range(y1, y2):
                    counts[x, y] = counts.get((x, y), 0) + 1
        bx1, by1 = min(r[0] for r in rects), min(r[1] for r in rects)
        bx2, by2 = max(r[2] for r in rects), max(r[3] for r in rects)
        expected = (all(c == 1 for c in counts.values())
                    and len(counts) == (bx2 - bx1) * (by2 - by1))
        assert is_perfect_rectangle(rects) == expected


if __name__ == "__main__":
    main()
```

## 9. Where sweeping by x stops: falling squares

Squares fall one at a time. Square i has left edge `left` and side `side`, so it occupies `[left, left + side)`. It lands on the highest square below it that overlaps it horizontally, or on the ground. After each drop, report the tallest stack.

This looks like a skyline, but **a sweep over x doesn't work**. Drop `[2, 4)` first and `[0, 3)` second: the second lands on the first, at height 2. Processed in x order, `[0, 3)` would land on the ground. The landing height depends on squares dropped *earlier in time*, so the state must be updated in drop order. Per drop: take the maximum height on `[left, right)`, then raise that range to the new top.

```python
def falling_squares(drops):
    """drops: (left, side) with side > 0. Returns the tallest stack after each drop."""
    landed = []  # (left, right, top)
    tallest = 0
    answer = []
    for left, side in drops:
        if side <= 0:
            raise ValueError("side must be positive")
        right = left + side
        base = max((top for l, r, top in landed if l < right and left < r), default=0)
        top = base + side
        landed.append((left, right, top))
        tallest = max(tallest, top)
        answer.append(tallest)
    return answer


def main():
    assert falling_squares([(1, 2), (2, 3), (6, 1)]) == [2, 5, 5]
    assert falling_squares([(100, 100), (200, 100)]) == [100, 100]  # touching, not stacked
    assert falling_squares([]) == []

    from random import Random
    rng = Random(97)
    for _ in range(200):
        drops = [(rng.randrange(0, 8), rng.randrange(1, 4)) for _ in range(rng.randrange(10))]
        heights = [0] * 12
        expected = []
        for left, side in drops:
            top = max(heights[left:left + side]) + side
            heights[left:left + side] = [top] * side
            expected.append(max(heights))
        assert falling_squares(drops) == expected


if __name__ == "__main__":
    main()
```

This version is O(n²). The fast version keeps the height profile in a segment tree over compressed x-coordinates, with **range maximum** queries and **range assignment** updates using lazy propagation ([Segment Trees](../04-range-queries/03-segment-tree.md)), for O(n log n). Every coordinate is known in advance, so compression is still possible even though updates must follow time order.

## 10. Geometric sweep variants and their limits

| Problem | Sweep | Maintained summary | Where |
|---|---|---|---|
| Union area | x | Coverage tree over y-gaps | §3 |
| Area covered at least k times | x | Coverage tree with k lengths per node | §6 |
| Union perimeter | x, then y | Coverage tree, three readings per x | §7 |
| Skyline | x | Max-heap with lazy expiration | §5 |
| Perfect tiling | none | Corner parity set | §8 |
| Falling squares | Drop order | Height profile | §9 |
| Horizontal–vertical segment intersection counts | x | Fenwick over active y-values | [Offline Sweeps §5](05-offline-sweeps-and-fenwick.md#5-horizontalvertical-segment-intersections) |
| Does any pair of general segments intersect? | x | Active segments ordered by y | [Ordered-Set Sweeps §2](07-ordered-set-and-angular-sweeps.md#2-does-any-pair-of-segments-intersect) |
| Report all intersections of general segments | x | Same, plus crossing events (Bentley–Ottmann) | Beyond these notes: up to Θ(n²) intersections, and ties and collinear overlaps need careful handling |
| Closest pair of points | x | Points in an x-band, ordered by y | [Ordered-Set Sweeps §1](07-ordered-set-and-angular-sweeps.md#1-closest-pair-of-points) |
| Directions around a point | Angle | Sorted angles | [Ordered-Set Sweeps §3](07-ordered-set-and-angular-sweeps.md#3-angular-sweep-turn-instead-of-slide) |

With floating-point coordinates, equality and tie grouping need a stated numerical model; putting an epsilon inside a sort comparison can break transitivity. Integer or rational coordinates avoid the issue.

## 11. Pitfalls and practice

1. Building a leaf for every y-endpoint rather than every gap between consecutive y-values.
2. Using compressed rank distance as covered length.
3. Adding a slab's area after applying the events at its right boundary.
4. Summing heights of active rectangles instead of measuring their union.
5. Deleting a heap element by linear search at every end event.
6. Emitting several skyline points at one x before all starts and expirations there are applied.
7. Using the net change in covered length as the perimeter contribution at x (§7).
8. Sweeping by x when the input order carries a dependency (§9).

Practice: rectangle area II; the skyline problem; rectangle area covered at least twice; union perimeter (the IOI "Picture" problem); perfect rectangle; falling squares, first O(n²), then with a lazy segment tree.

Next: [Ordered-Set and Angular Sweeps](07-ordered-set-and-angular-sweeps.md).
