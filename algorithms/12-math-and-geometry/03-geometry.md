# Computational Geometry — Vectors, Orientation, Polygons, and Hulls

## 1. Left or right?

You walk from `A = (0, 0)` to `B = (4, 1)` and then on to `C`. Do you turn left or right at `B`? Try three choices of `C`:

```text
 4 |        *C1 (3,4)
 3 |
 2 |                       *C2 (8,2)
 1 |           *B (4,1)
 0 *A (0,0)          *C3 (6,0)
   0  1  2  3  4  5  6  7  8   x
```

By eye, going on to `C1` is a sharp left turn and going to `C3` is a right turn. `C2` is hard to call: is it slightly above the line through `A` and `B`, slightly below, or exactly on it? We need a formula that answers exactly, with integers.

### Points and vectors

A **point** is a position `(x, y)`; a **vector** is a displacement "move `dx` right and `dy` up". Subtracting two points gives the vector between them: `B − A = (4, 1)`. Both are stored as tuples. A vector's length is `√(dx² + dy²)`; compare **squared** lengths whenever you can, since they stay integers.

## 2. Dot and cross products

For vectors `u = (u_x, u_y)` and `v = (v_x, v_y)`:

$$
u\cdot v = u_x v_x + u_y v_y,\qquad u\times v = u_x v_y - u_y v_x.
$$

Both are one line of integer arithmetic. Their meaning, with `θ` the angle that turns `u` toward `v` (counterclockwise positive):

$$
u\cdot v = |u||v|\cos\theta,\qquad u\times v = |u||v|\sin\theta.
$$

```text
 dot: how much v goes ALONG u          cross: how much v goes to the LEFT of u

        v                                       v
       /                                       /|
      /  θ                                    / | height h = |v| sin θ
     ●────────u──────►                       ●──┴──────u──────►
     └── |v| cos θ ──┘                       u × v = |u| · h = area of the parallelogram

 u·v > 0: angle < 90°                    u × v > 0: v is counterclockwise (left) of u
 u·v = 0: perpendicular                  u × v = 0: parallel or opposite (collinear)
 u·v < 0: angle > 90°                    u × v < 0: v is clockwise (right) of u
```

Example: `u = (4, 1)`, `v = (1, 3)`. Dot: `4·1 + 1·3 = 7 > 0`, so the angle is acute. Cross: `4·3 − 1·1 = 11 > 0`, so `v` points to the left of `u`, and the parallelogram they span has area 11.

The cross product does most of the work below: its sign gives direction, and its size gives area.

## 3. The orientation test

**Problem.** Given three points `A, B, C`, is the turn `A → B → C` left, right, or straight?

**Key observation.** The turn is left exactly when `C` lies to the left of the direction `A → B`, that is when the cross product of `B − A` and `C − A` is positive:

$$
\text{orient}(A, B, C) = (B - A)\times(C - A).
$$

Positive means **counterclockwise** (left turn), negative means **clockwise** (right turn), zero means **collinear**.

**Trace** for §1, with `A = (0, 0)` and `B = (4, 1)`, so `B − A = (4, 1)`:

| C | C − A | (4)(C_y) − (1)(C_x) | Result |
|---|---|---|---|
| C1 = (3, 4) | (3, 4) | 16 − 3 = 13 | left turn |
| C2 = (8, 2) | (8, 2) | 8 − 8 = 0 | straight (collinear) |
| C3 = (6, 0) | (6, 0) | 0 − 6 = −6 | right turn |

The hard case, `C2`, is exactly collinear, and integer arithmetic says so with no doubt.

`|orient(A, B, C)|` is twice the area of triangle `ABC`. That fact powers the area formula in §6 and the calipers in §9.

## 4. Distance from a point to a segment

**Problem.** How far is point `P` from the segment `AB`? The closest point of the segment is either the foot of the perpendicular from `P`, if it falls between `A` and `B`, or the nearer endpoint.

**Key observation.** Every point of the segment is `A + t·(B − A)` for some `t` in `[0, 1]`. The `t` of the perpendicular foot is the projection of `P − A` onto `B − A`:

$$
t = \frac{(P - A)\cdot(B - A)}{|B - A|^2}.
$$

Clamp `t` to `[0, 1]`: below 0 means the foot is past `A`, above 1 past `B`.

**Trace** with `A = (0, 0)`, `B = (4, 0)`, so `B − A = (4, 0)` and `|B − A|² = 16`:

| P | (P − A)·(B − A) | t | clamped | closest point | distance |
|---|---:|---:|---:|---|---|
| (3, 4) | 12 | 0.75 | 0.75 | (3, 0) | 4 |
| (6, 2) | 24 | 1.5 | 1 | (4, 0) | √8 ≈ 2.83 |
| (−1, 1) | −4 | −0.25 | 0 | (0, 0) | √2 ≈ 1.41 |

If `A = B`, the segment is a point and `|B − A|² = 0`; handle it separately to avoid dividing by zero.

The distance from `P` to the **infinite line** through `A, B` needs no clamping: `|orient(A, B, P)| / |B − A|`, the parallelogram area divided by its base.

Each query is O(1). The code is with segment intersection at the end of §5.

## 5. Do two segments intersect?

**Problem.** Do segments `AB` and `CD` share at least one point? Touching at an endpoint counts.

**Key observation.** In the general case, the segments cross exactly when `C` and `D` are on **opposite sides** of line `AB`, **and** `A` and `B` are on opposite sides of line `CD`. One condition is not enough: a short segment can straddle the line through a long one without reaching it.

```text
  crossing:                     straddles the line, but no crossing:
        C                              C
         \                              \
  A───────X───────B             A────B   \   (line AB continues →)
           \                              \
            D                              D
```

Compute four orientations:

```text
d1 = orient(A, B, C)    d2 = orient(A, B, D)    d3 = orient(C, D, A)    d4 = orient(C, D, B)
```

- **Proper crossing:** `d1, d2` have strictly opposite signs, and `d3, d4` too.
- **Touching and collinear cases:** if some `dᵢ = 0`, the corresponding point is on the other segment's **line**; it is on the **segment** if it also lies within the segment's bounding box. Check each of the four endpoints this way.

**Trace:**

| AB | CD | d1 | d2 | d3 | d4 | Verdict |
|---|---|---:|---:|---:|---:|---|
| (0,0)–(4,4) | (0,4)–(4,0) | 16 | −16 | −16 | 16 | proper crossing at (2, 2) |
| (0,0)–(2,2) | (2,2)–(3,0) | 0 | −6 | −6 | 0 | C = B = (2,2): touch at an endpoint |
| (0,0)–(2,0) | (1,0)–(3,0) | 0 | 0 | 0 | 0 | collinear; C on AB: overlap |
| (0,0)–(1,0) | (2,0)–(3,0) | 0 | 0 | 0 | 0 | collinear; no endpoint on the other: disjoint |
| (0,0)–(4,0) | (1,1)–(3,5) | 4 | 20 | … | … | same side: no intersection |

The fourth row is the classic bug: all four orientations are zero (all points on one line), and code that only tests "signs differ or zero" would wrongly report an intersection. The bounding-box check rejects it.

```python
import math
import random
from fractions import Fraction


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def orient(a, b, c):
    """> 0 left turn (counterclockwise), < 0 right turn, 0 collinear."""
    return cross(sub(b, a), sub(c, a))


def dist_point_segment(p, a, b) -> float:
    ab, ap = sub(b, a), sub(p, a)
    length_sq = dot(ab, ab)
    if length_sq == 0:  # a == b: the segment is a point
        return math.hypot(*ap)
    t = max(0.0, min(1.0, dot(ap, ab) / length_sq))
    return math.hypot(p[0] - (a[0] + t * ab[0]), p[1] - (a[1] + t * ab[1]))


def on_segment(p, a, b) -> bool:
    """Is p on the closed segment ab?"""
    return (
        orient(a, b, p) == 0
        and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
        and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
    )


def segments_intersect(a, b, c, d) -> bool:
    def sign(x):
        return (x > 0) - (x < 0)

    d1, d2 = sign(orient(a, b, c)), sign(orient(a, b, d))
    d3, d4 = sign(orient(c, d, a)), sign(orient(c, d, b))
    if d1 * d2 < 0 and d3 * d4 < 0:
        return True
    return on_segment(c, a, b) or on_segment(d, a, b) or on_segment(a, c, d) or on_segment(b, c, d)


def intersect_brute(a, b, c, d) -> bool:
    """Any common point is an endpoint or the one point where two non-parallel lines meet."""
    candidates = [a, b, c, d]
    r, s = sub(b, a), sub(d, c)
    den = cross(r, s)
    if den != 0:
        t = Fraction(cross(sub(c, a), s), den)
        candidates.append((a[0] + t * r[0], a[1] + t * r[1]))
    return any(on_segment(p, a, b) and on_segment(p, c, d) for p in candidates)


def main():
    a, b = (0, 0), (4, 1)
    assert [orient(a, b, c) for c in [(3, 4), (8, 2), (6, 0)]] == [13, 0, -6]
    assert dot((4, 1), (1, 3)) == 7 and cross((4, 1), (1, 3)) == 11

    A, B = (0, 0), (4, 0)
    assert dist_point_segment((3, 4), A, B) == 4
    assert math.isclose(dist_point_segment((6, 2), A, B), math.sqrt(8))
    assert math.isclose(dist_point_segment((-1, 1), A, B), math.sqrt(2))
    assert dist_point_segment((5, 5), (2, 2), (2, 2)) == math.sqrt(18)
    rng = random.Random(12)
    for _ in range(300):  # brute force: no dense sample of the segment is closer
        p, a, b = [(rng.randint(-6, 6), rng.randint(-6, 6)) for _ in range(3)]
        samples = [(a[0] + k / 400 * (b[0] - a[0]), a[1] + k / 400 * (b[1] - a[1])) for k in range(401)]
        best = min(math.hypot(p[0] - x, p[1] - y) for x, y in samples)
        assert dist_point_segment(p, a, b) <= best + 1e-9 <= dist_point_segment(p, a, b) + 0.05

    assert segments_intersect((0, 0), (4, 4), (0, 4), (4, 0))
    assert segments_intersect((0, 0), (2, 2), (2, 2), (3, 0))
    assert segments_intersect((0, 0), (2, 0), (1, 0), (3, 0))
    assert not segments_intersect((0, 0), (1, 0), (2, 0), (3, 0))  # collinear, disjoint
    assert not segments_intersect((0, 0), (4, 0), (1, 1), (3, 5))
    assert segments_intersect((1, 1), (1, 1), (0, 0), (2, 2))  # a point on a segment
    for _ in range(20000):
        pts = [(rng.randint(0, 4), rng.randint(0, 4)) for _ in range(4)]
        assert segments_intersect(*pts) == intersect_brute(*pts)


if __name__ == "__main__":
    main()
```

O(1) per pair, exact with integer coordinates. The brute force tests the four endpoints and the one point where two non-parallel lines meet, computed exactly with `Fraction`: any shared point of two segments is one of these.

To report **all** crossing pairs among many segments, or to detect whether any pair crosses in O(n log n), see the segment sweep in [Ordered-Set and Angular Sweeps](../08-sweep-line/07-ordered-set-and-angular-sweeps.md).

## 6. Polygon area: the shoelace formula

**Problem.** A plot of land has corners `(0,0), (4,0), (4,3), (2,5), (0,3)`, listed counterclockwise. What is its area?

```text
 5 |       *(2,5)
 4 |
 3 *(0,3)          *(4,3)
 2 |
 1 |
 0 *(0,0)          *(4,0)
   0   1   2   3   4   x
```

Edges join the corners in the listed order, so the shape is a rectangle with a triangular roof. By hand: a 4 × 3 rectangle (12) plus a triangle with base 4 and height 2 (4) gives 16. We want a formula that works for any simple polygon.

**Key observation.** Pick the origin `O` and fan out triangles `O, Pᵢ, Pᵢ₊₁` for each edge. `cross(Pᵢ, Pᵢ₊₁)` is twice the **signed** area of that triangle: positive when the edge goes counterclockwise around `O`, negative otherwise. Triangles outside the polygon are added once and subtracted once, so they cancel, and what remains is the polygon:

$$
\text{Area} = \frac{1}{2}\left|\sum_{i=0}^{n-1} \left(x_i\,y_{i+1} - x_{i+1}\,y_i\right)\right|,\qquad P_n = P_0.
$$

The name comes from writing the coordinates in two columns and cross-multiplying diagonally, like lacing a shoe.

**Trace:**

| i | Pᵢ | Pᵢ₊₁ | xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ | running sum |
|---:|---|---|---|---:|
| 0 | (0, 0) | (4, 0) | 0·0 − 4·0 = 0 | 0 |
| 1 | (4, 0) | (4, 3) | 4·3 − 4·0 = 12 | 12 |
| 2 | (4, 3) | (2, 5) | 4·5 − 2·3 = 14 | 26 |
| 3 | (2, 5) | (0, 3) | 2·3 − 0·5 = 6 | 32 |
| 4 | (0, 3) | (0, 0) | 0·0 − 0·3 = 0 | 32 |

Area `= 32 / 2 = 16`. ✓ The sum is **positive** because the vertices are counterclockwise; a clockwise listing gives −32. So the sign of the sum tells you the orientation of a polygon for free.

Keep the sum (twice the area) as an integer and divide by 2 only at the end, or return it doubled. It is exact for integer coordinates.

**Pick's theorem** links area to lattice points for a polygon with integer vertices: `Area = I + B/2 − 1`, where `I` counts lattice points strictly inside and `B` those on the boundary. An edge from `P` to `Q` contains `gcd(|Δx|, |Δy|)` boundary points, not counting one endpoint ([Number Theory §2](01-number-theory.md#2-greatest-common-divisor-euclids-algorithm)). For the plot: the edges contribute `4 + 3 + 2 + 2 + 3 = 14` boundary points, so `I = 16 − 7 + 1 = 10`. The test below uses Pick's theorem as an independent check of both the area and the point-in-polygon code of §7.

## 7. Is a point inside a polygon?

**Problem.** Given a simple polygon (edges don't cross) and a point `P`, is `P` inside, outside, or on the boundary?

### Ray casting

**Key observation.** Shoot a ray from `P` to the right. Every time it crosses an edge, it switches between inside and outside. Far to the right it is outside, so `P` is inside exactly when the number of crossings is **odd**.

The danger is a ray passing **through a vertex**: is that one crossing or two? The fix is a **half-open rule**: an edge counts only if one endpoint is strictly above the ray and the other is not, `(a_y > P_y) != (b_y > P_y)`. A vertex exactly on the ray then counts as "below", so two edges meeting there count once if they continue on opposite sides, and zero or two times if both go the same way. Horizontal edges never count.

**Trace** on the plot from §6, with `P = (1, 3)`. The ray `y = 3` passes exactly through the vertices `(0, 3)` and `(4, 3)`:

| Edge | a_y > 3? | b_y > 3? | Counts? | Crossing x | Right of P? | crossings |
|---|---|---|---|---:|---|---:|
| (0,0)→(4,0) | no | no | no | | | 0 |
| (4,0)→(4,3) | no | no | no | | | 0 |
| (4,3)→(2,5) | no | yes | yes | 4 | yes | 1 |
| (2,5)→(0,3) | yes | no | yes | 0 | no | 1 |
| (0,3)→(0,0) | no | no | no | | | 1 |

One crossing, odd, so `(1, 3)` is inside. ✓ Without the half-open rule, the vertex `(4, 3)` would count for both of its edges and give the wrong parity.

To decide "right of P" without division, use orientation: for an upward edge `a → b`, the crossing is right of `P` exactly when `P` is left of the edge (`orient(a, b, P) > 0`); for a downward edge, when `orient < 0`.

**Boundary.** Check `on_segment(P, a, b)` for every edge **first**. Ray casting alone gives an arbitrary answer for boundary points.

### Winding number

The **winding number** counts how many times the polygon wraps around `P` counterclockwise. Walk along the edges: an edge crossing the ray **upward** with `P` on its left adds 1; one crossing **downward** with `P` on its right subtracts 1. `P` is inside when the total is nonzero.

On the same trace, `(4,3)→(2,5)` crosses upward with `P` on its left: `+1`. `(2,5)→(0,3)` crosses downward, but its crossing is left of `P`, so `P` is on its left, not its right: `0`. Winding number 1: inside.

| | Ray casting (even–odd) | Winding number |
|---|---|---|
| Simple polygons | same answer | same answer |
| Self-intersecting polygons | "inside" = odd crossings | "inside" = wrapped around at least once |
| Cost | O(n) | O(n) |

For a **convex** polygon in counterclockwise order, there is an O(log n) test: binary search for the wedge from vertex 0 that contains `P`, then check one orientation. [Binary Search](../01-binary-search/README.md) covers the search itself.

```python
import math
import random
from fractions import Fraction

INSIDE, BOUNDARY, OUTSIDE = 1, 0, -1


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(p, a, b) -> bool:
    return (
        orient(a, b, p) == 0
        and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
        and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
    )


def twice_area(poly) -> int:
    """Signed: positive for counterclockwise vertex order."""
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def locate_ray(poly, p) -> int:
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if on_segment(p, a, b):
            return BOUNDARY
        if (a[1] > p[1]) != (b[1] > p[1]):
            if (orient(a, b, p) > 0) == (b[1] > a[1]):
                inside = not inside
    return INSIDE if inside else OUTSIDE


def locate_winding(poly, p) -> int:
    winding = 0
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if on_segment(p, a, b):
            return BOUNDARY
        if a[1] <= p[1] < b[1] and orient(a, b, p) > 0:
            winding += 1
        elif b[1] <= p[1] < a[1] and orient(a, b, p) < 0:
            winding -= 1
    return INSIDE if winding != 0 else OUTSIDE


def random_star_polygon(rng, k):
    """A simple polygon: integer points sorted by angle around a center point."""
    cx, cy = 0.5, 0.25  # not a lattice point, so no vertex coincides with it
    by_angle = {}
    for _ in range(k):
        x, y = rng.randint(-6, 6), rng.randint(-6, 6)
        angle = round(math.atan2(y - cy, x - cx), 12)
        dist = (x - cx) ** 2 + (y - cy) ** 2
        if angle not in by_angle or dist < by_angle[angle][0]:
            by_angle[angle] = (dist, (x, y))
    angles = sorted(by_angle)
    gaps = [b - a for a, b in zip(angles, angles[1:])] + [2 * math.pi + angles[0] - angles[-1]]
    if max(gaps) >= math.pi - 1e-9:
        return []  # the center would not be inside: edges could cross
    return [by_angle[a][1] for a in angles]


def main():
    plot = [(0, 0), (4, 0), (4, 3), (2, 5), (0, 3)]
    assert twice_area(plot) == 32 and twice_area(plot[::-1]) == -32
    assert locate_ray(plot, (1, 3)) == INSIDE == locate_winding(plot, (1, 3))
    assert locate_ray(plot, (5, 1)) == OUTSIDE
    assert locate_ray(plot, (4, 1)) == BOUNDARY == locate_winding(plot, (2, 0))
    assert locate_ray(plot, (5, 3)) == OUTSIDE == locate_winding(plot, (5, 3))
    assert locate_ray(plot, (2, 6)) == OUTSIDE

    rng = random.Random(14)
    tested = 0
    for _ in range(400):
        poly = random_star_polygon(rng, rng.randint(3, 12))
        if len(poly) < 3 or twice_area(poly) == 0:
            continue
        tested += 1
        interior = boundary = 0
        for x in range(-7, 8):
            for y in range(-7, 8):
                r, w = locate_ray(poly, (x, y)), locate_winding(poly, (x, y))
                assert r == w
                interior += r == INSIDE
                boundary += r == BOUNDARY
        edge_points = sum(
            math.gcd(abs(poly[i][0] - poly[i - 1][0]), abs(poly[i][1] - poly[i - 1][1]))
            for i in range(len(poly))
        )
        assert boundary == edge_points
        assert Fraction(abs(twice_area(poly)), 2) == interior + Fraction(boundary, 2) - 1  # Pick
    assert tested > 100


if __name__ == "__main__":
    main()
```

Area is O(n); each point query is O(n). The test generates star-shaped polygons: vertices sorted by angle around a center point, kept only when every angular gap is below 180°, so the center sees every edge and edges never cross, then checks that both point-location methods agree on every lattice point in a window, and that the counts satisfy Pick's theorem.

## 8. Convex hull: Andrew's monotone chain

**Problem.** Given `n` points (trees), find the smallest convex polygon containing all of them (the shortest fence). A polygon is **convex** if every turn along its boundary goes the same way. Its corners are always input points, and they form the **convex hull**.

**Brute force.** A pair `(P, Q)` is a hull edge when every other point is on the left of `P → Q`. Testing all pairs against all points is O(n³).

**Key observation.** Sort the points by `x` (then `y`). Walking left to right, the **lower hull** only ever turns left (counterclockwise). So keep a stack of the current lower hull; before pushing a new point, pop the top while the last two stack points and the new point **do not** make a left turn. Then do the same right to left for the **upper hull**, and join them.

**Invariant:** after processing a prefix of the sorted points, the stack is the lower hull of that prefix, with every consecutive triple turning strictly left.

**Trace** on 8 points. Sorted: `(0,0) (0,3) (1,2) (2,1) (2,4) (3,2) (4,0) (4,3)`.

```text
 4 |           *(2,4)
 3 *(0,3)                  *(4,3)
 2 |     *(1,2)      *(3,2)
 1 |           *(2,1)
 0 *(0,0)                  *(4,0)
   0     1     2     3     4   x
```

Lower hull, left to right (`orient` of the last two stack points with the new point; pop while `≤ 0`):

| New point | Pops (orient value) | Stack after |
|---|---|---|
| (0,0) | | (0,0) |
| (0,3) | | (0,0) (0,3) |
| (1,2) | (0,3): −3 | (0,0) (1,2) |
| (2,1) | (1,2): −3 | (0,0) (2,1) |
| (2,4) | | (0,0) (2,1) (2,4) |
| (3,2) | (2,4): −3 | (0,0) (2,1) (3,2) |
| (4,0) | (3,2): −3, then (2,1): −4 | (0,0) (4,0) |
| (4,3) | | (0,0) (4,0) (4,3) |

Upper hull, right to left, with the same rule: it starts `(4,3) (4,0)`, and each of `(4,0)`, `(3,2)`, `(2,1)`, `(1,2)` is pushed and later popped with orient −3, leaving `(4,3) (2,4) (0,3) (0,0)`.

Each chain ends with the first point of the other, so drop the last point of each and concatenate: hull `(0,0) (4,0) (4,3) (2,4) (0,3)`, counterclockwise.

**Why it is correct.** A point popped from the lower stack makes a non-left turn between its neighbors, so it lies on or above the segment joining them, and can't be a lower-hull corner of any longer prefix either. A point kept makes a left turn with everything after it so far. Each point is pushed once and popped at most once per chain, so after sorting the work is O(n).

**Collinear points.** Popping on `≤ 0` drops points in the middle of a hull edge. To **keep** them (some problems want every fence post on the boundary), pop only on `< 0`, and take care with the all-collinear case, where the two chains would retrace the same points.

Time O(n log n) for the sort plus O(n) for the chains; space O(n). The code is with the calipers at the end of §9. Its brute force uses the fact that a point is **not** a corner exactly when it lies on a segment between two other points or in a triangle of three others (Carathéodory's theorem in the plane), checked in O(n⁴) on tiny inputs.

## 9. Rotating calipers: the farthest pair

**Problem.** Among `n` points, find the largest distance between two of them (the **diameter**). Checking all pairs is O(n²).

**Key observation 1.** The farthest pair are both hull corners. (Moving a point outward to the hull can only increase distances.) So compute the hull first; often it is much smaller than `n`.

**Key observation 2.** For each hull edge, the hull corner **farthest from that edge's line** is its **antipodal** point. As the edge advances counterclockwise, its antipodal point also only moves forward. So two pointers walk around the hull together, like the two jaws of a caliper rotating around it, in O(h) total for `h` hull corners. The farthest pair is always among the (edge endpoint, antipodal point) pairs.

"Farthest from the line of edge `i → i+1`" is measured by `|orient(Hᵢ, Hᵢ₊₁, H_j)|`, twice a triangle's area: advance `j` while the next corner gives a bigger area.

**Trace** on the hull from §8, `H = (0,0) (4,0) (4,3) (2,4) (0,3)`:

| Edge | Antipodal corner | dist² to edge's endpoints | Best so far |
|---|---|---|---:|
| (0,0)→(4,0) | (2,4) | 20, 20 | 20 |
| (4,0)→(4,3) | (0,3) | 25, 16 | 25 |
| (4,3)→(2,4) | (0,0) | 25, 20 | 25 |
| (2,4)→(0,3) | (4,0) | 20, 25 | 25 |
| (0,3)→(0,0) | (4,0) | 25, 16 | 25 |

The diameter is `√25 = 5`, between `(0,3)` and `(4,0)` (also `(0,0)` and `(4,3)`). The antipodal pointer moved forward only: `(2,4) → (0,3) → (0,0) → (4,0)`.

The same calipers give the **minimum width** of the point set (the smallest antipodal edge-to-corner distance) and the minimum-area bounding rectangle.

```python
import random
from itertools import combinations


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def dist_sq(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def convex_hull(points):
    """Hull corners counterclockwise from the lowest-leftmost point; no collinear points."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and orient(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and orient(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]  # each chain ends where the other starts


def diameter_sq(points) -> int:
    """Largest squared distance between two of the points (rotating calipers)."""
    if not points:
        raise ValueError("need at least one point")
    hull = convex_hull(points)
    h = len(hull)
    if h <= 2:
        return dist_sq(hull[0], hull[-1])
    best, j = 0, 1
    for i in range(h):
        a, b = hull[i], hull[(i + 1) % h]
        while abs(orient(a, b, hull[(j + 1) % h])) > abs(orient(a, b, hull[j])):
            j = (j + 1) % h  # the antipodal pointer only moves forward
        best = max(best, dist_sq(a, hull[j]), dist_sq(b, hull[j]))
    return best


def hull_corners_brute(points):
    """p is not a corner iff it lies on a segment or in a triangle of other points."""
    pts = sorted(set(points))

    def in_triangle(p, a, b, c):
        d = [orient(a, b, p), orient(b, c, p), orient(c, a, p)]
        return min(d) >= 0 or max(d) <= 0

    def covered(p):
        others = [q for q in pts if q != p]
        on_seg = any(
            orient(a, b, p) == 0 and min(a, b) <= p <= max(a, b) for a, b in combinations(others, 2)
        )
        return on_seg or any(
            orient(a, b, c) != 0 and in_triangle(p, a, b, c) for a, b, c in combinations(others, 3)
        )

    return {p for p in pts if not covered(p)}


def main():
    pts = [(0, 0), (4, 0), (2, 1), (1, 2), (4, 3), (2, 4), (0, 3), (3, 2)]
    assert convex_hull(pts) == [(0, 0), (4, 0), (4, 3), (2, 4), (0, 3)]
    assert convex_hull([]) == [] and convex_hull([(1, 1), (1, 1)]) == [(1, 1)]
    assert convex_hull([(0, 0), (1, 1), (2, 2), (3, 3)]) == [(0, 0), (3, 3)]
    assert convex_hull([(0, 0), (2, 0), (1, 0), (1, 1)]) == [(0, 0), (2, 0), (1, 1)]
    assert diameter_sq(pts) == 25
    assert diameter_sq([(3, 3)]) == 0 and diameter_sq([(0, 0), (3, 4), (3, 4)]) == 25
    rng = random.Random(15)
    for _ in range(1500):
        points = [(rng.randint(0, 5), rng.randint(0, 5)) for _ in range(rng.randint(1, 9))]
        hull = convex_hull(points)
        assert set(hull) == hull_corners_brute(points)
        k = len(hull)
        assert k < 3 or all(orient(hull[i], hull[(i + 1) % k], hull[(i + 2) % k]) > 0 for i in range(k))
    for _ in range(2000):
        points = [(rng.randint(-20, 20), rng.randint(-20, 20)) for _ in range(rng.randint(1, 30))]
        assert diameter_sq(points) == max(dist_sq(p, q) for p in points for q in points)


if __name__ == "__main__":
    main()
```

Time O(n log n) for the hull, then O(h) for the calipers; space O(n).

## 10. Precision: integers, fractions, floats, epsilons

Every algorithm above uses only `+`, `−` and `×` on the input coordinates (and one division in §4). With integer inputs that is **exact**, and that is a deliberate choice.

**Floats break orientation.** The points `(0, 0)`, `(0.1, 0.7)`, `(0.3, 2.1)` lie on the line `y = 7x`. In floating point, `0.1`, `0.7`, `0.3` and `2.1` are all slightly off, and

```text
0.1 · 2.1 − 0.7 · 0.3  =  2.7755575615628914e-17    (should be 0)
```

so the test reports a left turn, and a hull or point-location loop built on it can contradict itself. Options, from best to worst:

| Approach | When to use | Cost |
|---|---|---|
| **Integers** | Integer inputs (most problems). Scale decimals with a fixed number of places by `10^k` first. | Exact. In C++ watch overflow: a cross product of coordinates up to `10^9` reaches about `4·10^18`, near the signed 64-bit limit. |
| **`Fraction`** | Rational intermediate points (intersections) that feed later tests. | Exact; slower, and numbers can grow. |
| **Floats with an epsilon** | Inputs are real numbers, or you need square roots and angles. | Compare `x > eps`, `abs(x) <= eps`, `x < -eps` instead of `> 0`, `== 0`, `< 0`. |

**Choosing an epsilon.** An absolute `1e-9` suits coordinates of size about 1 to `10^3`. The rounding error of a cross product grows with the **square** of the coordinate size, so for coordinates near `10^6` an error of `10^-4` is normal. Scale the tolerance to your data, and never compare floats with `==`.

**Keep things squared.** Compare `dist_sq(a, b) < dist_sq(c, d)` instead of distances, and compare angles with cross products instead of `atan2` when you can. The square root and the arctangent are where exactness is lost.

```python
from fractions import Fraction

EPS = 1e-9


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def orient_sign_eps(a, b, c, eps=EPS) -> int:
    value = orient(a, b, c)
    return 1 if value > eps else -1 if value < -eps else 0


def main():
    a, b, c = (0.0, 0.0), (0.1, 0.7), (0.3, 2.1)
    assert orient(a, b, c) != 0  # floats: a spurious left turn
    assert orient_sign_eps(a, b, c) == 0  # tolerance: collinear
    # Fraction("0.1") is exactly one tenth; Fraction(0.1) would be the float's binary value.
    exact = [(Fraction(0), Fraction(0)), (Fraction("0.1"), Fraction("0.7")), (Fraction("0.3"), Fraction("2.1"))]
    assert orient(*exact) == 0
    scaled = [(0, 0), (1, 7), (3, 21)]  # multiply by 10 and use integers
    assert orient(*scaled) == 0
    assert 0.1 + 0.2 != 0.3 and abs((0.1 + 0.2) - 0.3) <= EPS


if __name__ == "__main__":
    main()
```

## 11. Summary

| Question | Tool | Cost | Section |
|---|---|---|---|
| Angle acute, right or obtuse | sign of `u · v` | O(1) | §2 |
| Left turn, right turn, collinear | sign of `orient(a, b, c) = (b − a) × (c − a)` | O(1) | §3 |
| Triangle area | `abs(orient(a, b, c)) / 2` | O(1) | §3 |
| Distance from a point to a segment | project, clamp `t` to `[0, 1]` | O(1) | §4 |
| Do two segments meet | four orientations, then `on_segment` for zeros | O(1) | §5 |
| Polygon area and orientation | shoelace sum, sign = orientation | O(n) | §6 |
| Lattice points inside | Pick: `A = I + B/2 − 1` | O(n) | §6 |
| Point in polygon | boundary first, then ray casting (half-open) or winding | O(n) | §7 |
| Convex hull | sort, then lower and upper chains with a stack | O(n log n) | §8 |
| Farthest pair, width | rotating calipers on the hull | O(h) after the hull | §9 |

**Exactness.** With integer coordinates every test above uses only `+`, `−`, `×` and is exact. Compare squared distances, compare angles with cross products, and use an epsilon only for real-number inputs (§10).

Sweep-based geometry, including the closest pair of points, union area of rectangles and the skyline, is in [Sweep Line](../08-sweep-line/README.md).

## 12. Pitfalls and practice

1. Using floats when the input is integer. Keep every test in integer arithmetic until you truly need a square root or a division.
2. Forgetting that `orient` can be zero. Decide for each algorithm whether collinear means "keep" or "drop" (§8).
3. Testing segment intersection with signs only, so collinear but disjoint segments (§5, fourth row) are reported as crossing.
4. Taking `abs()` of the shoelace sum too early, losing the orientation information (counterclockwise vs clockwise).
5. Ray casting without the half-open rule, so a ray through a vertex counts twice; or forgetting to test the boundary first.
6. In the monotone chain, not removing duplicate points, or concatenating the two chains without dropping their shared endpoints.
7. Running rotating calipers on a hull with collinear points or with fewer than 3 corners. Remove collinear points and handle `h ≤ 2` separately.
8. Overflow in C++/Java: products of coordinates near `10^9` need 64 bits; products of such products (for example, comparing two cross products multiplied together) need 128 bits.
9. Dividing by zero for a degenerate segment (`A = B`) in projections (§4).

Practice: valid boomerang (orientation); check if it is a straight line; minimum time visiting all points; largest triangle area; erect the fence (convex hull, keeping collinear points); convex polygon (all turns the same way); minimum area rectangle; max points on a line (normalized direction with `gcd`); rectangle overlap and rectangle area; is a point in a polygon (classic); the farthest-pair problem on a hull of up to `10^5` points.

Next: [Counting Distributions](04-counting-distributions/README.md), or back to the [Math and Geometry overview](README.md).
