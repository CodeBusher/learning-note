# Tree Diameter and Centers — The Longest Route in Linear Time

## 1. The longest route in the org chart

The **diameter** of a tree is the length of its longest route: the largest distance between two vertices. The org chart from [Rooting and LCA](01-rooting-and-lca.md), every link of length 1:

```text
              0
            ╱   ╲
           1     2
         ╱   ╲     ╲
        3     4     5
            ╱   ╲
           6     7
           │
           8
```

**Problem.** Which two vertices are farthest apart, and how far?

The deepest vertex, 8, is a good guess for one end. From 8, the farthest vertex is 5: `8–6–4–1–0–2–5`, 6 links. No pair does better, so the **diameter is 6**.

**Brute force.** One traversal from `s` gives the distance from `s` to every vertex (there is only one route to each). Doing it from every vertex costs **O(V²)**.

## 2. Two traversals are enough

**The algorithm.**

1. Start anywhere, say at `a`. Find a vertex `x` farthest from `a`.
2. Find a vertex `y` farthest from `x`.
3. The distance from `x` to `y` is the diameter, and `x–y` is a longest route.

Trace starting from `a = 3`:

```text
vertex           0  1  2  3  4  5  6  7  8
dist from 3      2  1  3  0  2  4  3  3  4     farthest: 5 or 8 (both 4); take x = 5
dist from 5      2  3  1  4  4  0  5  5  6     farthest: y = 8, distance 6
```

Diameter 6, between 5 and 8. ✓ Two traversals, **O(V)** time.

### Why the first sweep lands on an end of some longest route

The claim is: **with nonnegative edge weights, a vertex farthest from any start `a` is an endpoint of some diameter.**

Let `x` be farthest from `a`, and let `p–q` be a diameter of length `D`. Write `d(u, v)` for the length of the unique route between `u` and `v`.

```text
     p ─────────── m ─────────── q        the diameter route
                   │
                   │  (route from a joins p–q at m)
                   a
```

Let `m` be the vertex of the route `p–q` closest to `a`. Every route from `a` to a vertex of `p–q` passes through `m`, so `d(a, p) = d(a, m) + d(m, p)` and likewise for `q`.

1. `x` is farthest from `a`, so `d(a, x) ≥ d(a, p) = d(a, m) + d(m, p)`.
2. With nonnegative weights, going from `a` to `x` directly is never longer than going via `m`: `d(a, x) ≤ d(a, m) + d(m, x)`.
3. Together: `d(m, x) ≥ d(m, p)`, and in the same way `d(m, x) ≥ d(m, q)`.
4. The route from `m` to `x` can head along at most one of the two directions of `p–q` (toward `p` or toward `q`). Say it does not head toward `q` (otherwise swap the names). Then walking `q → m → x` repeats no vertex, so it is the tree route, and `d(q, x) = d(q, m) + d(m, x) ≥ d(q, m) + d(m, p) = D`.

So `q–x` is at least as long as a diameter, which makes it a diameter, and `x` is one of its ends. The second sweep starts at an end of a diameter, and the farthest vertex from there is the other end.

Step 2 is where **nonnegative** weights are needed. It also needs a tree: in a general graph the two-sweep answer is only a lower bound.

### Negative weights break it

```text
   0 ──(−6)── 1 ──(5)── 2
```

The diameter (largest route sum) is 5, between 1 and 2. Start the two sweeps at 0: distances from 0 are `0, −6, −1`, so the farthest vertex is 0 itself (distance 0). The second sweep from 0 again gives 0. The answer 0 is wrong. The next section's DP handles this.

## 3. Tree DP: combine the best two branches

Root the tree. For each vertex `v`, compute

- `down[v]`: the length of the longest route that starts at `v` and goes **down** into `v`'s subtree (0 for the empty route).

Any route in the tree has a unique **highest** vertex `v`. From there it goes down into at most two different child subtrees. So the longest route whose highest vertex is `v` takes the best two values among `down[c] + w(v, c)` over children `c` (counting a missing or negative branch as 0).

$$
down[v] = \max\Bigl(0,\ \max_{c} \bigl(down[c] + w(v, c)\bigr)\Bigr),
\qquad
\text{through}[v] = \text{best} + \text{second best of } \max(0,\ down[c] + w(v, c)).
$$

The diameter is the largest `through[v]`. Children must be finished before their parent, so process vertices in **reverse** order of a DFS visit (a post-order).

Trace on the org chart (all weights 1). Branch values are `down[c] + 1`:

| Vertex (children first) | Branch values | `down` | `through` |
|---|---|---:|---:|
| 8, 7, 3, 5 (leaves) | none | 0 | 0 |
| 6 | 8: 1 | 1 | 1 |
| 4 | 6: 2, 7: 1 | 2 | 3 |
| 1 | 3: 1, 4: 3 | 3 | 4 |
| 2 | 5: 1 | 1 | 1 |
| 0 | 1: 4, 2: 2 | 4 | **6** |

The largest `through` is 6, at vertex 0, the highest vertex of `8–6–4–1–0–2–5`. ✓

On the negative example, rooted at 0: `down[2] = 0`; at 1 the branch to 2 is `0 + 5 = 5`, so `down[1] = 5`, `through[1] = 5`; at 0 the branch to 1 is `5 − 6 = −1`, clipped to 0, so `through[0] = 0`. Diameter 5. ✓

This is a [tree DP](../../09-dynamic-programming/08-tree-and-dag-dp.md): the state is a vertex, the transition combines its children. On a binary tree given as node objects, the same "best two branches" recursion is [diameter and maximum path sum](../../03-trees/02-recursion-on-trees.md); here it runs iteratively on an edge list with any number of children.

## 4. Centers: where to put the server

The **eccentricity** of a vertex is its distance to the farthest vertex. A **center** is a vertex with the smallest eccentricity; that smallest value is the **radius**. A server at a center minimizes the worst-case delay. If you hang the tree from a center, its height is as small as possible, which is the "minimum height trees" problem.

**Key facts (nonnegative weights).**

1. For every vertex `v`, its eccentricity is `max(dist(v, x), dist(v, y))`, where `x–y` is any diameter. The farthest vertex from anywhere is always an end of a diameter (the proof of §2).
2. So two extra traversals (from `x` and from `y`) give every eccentricity in O(V), and the centers are the minimizers.
3. In an unweighted tree, the centers are the middle vertex (if the diameter `D` is even) or the two middle vertices (if `D` is odd) of the route `x–y`, and the radius is `⌈D / 2⌉`.

On the org chart, the diameter route is `5–2–0–1–4–6–8` with `D = 6`. Its positions 0 to 6 hold `5, 2, 0, 1, 4, 6, 8`, so the middle (position 3) is vertex **1**. Its eccentricity is 3 (to 5 and to 8), and the radius is `⌈6/2⌉ = 3`. ✓

## 5. Code: diameter three ways, eccentricities, centers

```python
import random


def adjacency(n, edges):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj


def distances_from(adj, s):
    dist = [None] * len(adj)
    dist[s] = 0
    stack = [s]
    while stack:
        u = stack.pop()
        for v, w in adj[u]:
            if dist[v] is None:
                dist[v] = dist[u] + w
                stack.append(v)
    return dist


def diameter_two_sweeps(n, edges):
    """Nonnegative weights only. Returns (length, x, y)."""
    if any(w < 0 for _, _, w in edges):
        raise ValueError("two sweeps need nonnegative weights")
    adj = adjacency(n, edges)
    d = distances_from(adj, 0)
    x = max(range(n), key=d.__getitem__)
    d = distances_from(adj, x)
    y = max(range(n), key=d.__getitem__)
    return d[y], x, y


def diameter_dp(n, edges):
    """Any weights. Largest route sum over all pairs (a single vertex counts as 0)."""
    adj = adjacency(n, edges)
    parent = [-1] * n
    parent[0] = 0
    order = [0]
    for u in order:  # BFS order: parents before children
        for v, _ in adj[u]:
            if parent[v] == -1:
                parent[v] = u
                order.append(v)
    down = [0] * n
    best = 0
    for u in reversed(order):  # children before parents
        top1 = top2 = 0
        for v, w in adj[u]:
            if v != u and parent[v] == u:  # v is a child of u
                branch = max(0, down[v] + w)
                if branch > top1:
                    top1, top2 = branch, top1
                elif branch > top2:
                    top2 = branch
        down[u] = top1
        best = max(best, top1 + top2)
    return best


def eccentricities(n, edges):
    """Nonnegative weights. Every vertex's eccentricity in three sweeps."""
    adj = adjacency(n, edges)
    d0 = distances_from(adj, 0)
    x = max(range(n), key=d0.__getitem__)
    dx = distances_from(adj, x)
    y = max(range(n), key=dx.__getitem__)
    dy = distances_from(adj, y)
    return [max(dx[v], dy[v]) for v in range(n)]


def centers(n, edges):
    ecc = eccentricities(n, edges)
    radius = min(ecc)
    return [v for v in range(n) if ecc[v] == radius], radius


def diameter_brute(n, edges):
    adj = adjacency(n, edges)
    return max(max(distances_from(adj, s)) for s in range(n))


def random_tree(rng, n, low, high):
    edges = [(rng.randrange(v), v, rng.randint(low, high)) for v in range(1, n)]
    label = list(range(n))
    rng.shuffle(label)
    return [(label[u], label[v], w) for u, v, w in edges]


def main():
    chart = [(0, 1, 1), (0, 2, 1), (1, 3, 1), (1, 4, 1), (2, 5, 1),
             (4, 6, 1), (4, 7, 1), (6, 8, 1)]
    length, x, y = diameter_two_sweeps(9, chart)
    assert length == 6 and {x, y} == {5, 8}
    assert diameter_dp(9, chart) == 6 == diameter_brute(9, chart)

    negative = [(0, 1, -6), (1, 2, 5)]
    assert diameter_dp(3, negative) == 5 == diameter_brute(3, negative)
    assert diameter_dp(1, []) == 0 and diameter_two_sweeps(1, [])[0] == 0
    assert diameter_dp(2, [(0, 1, -3)]) == 0  # best is a single vertex
    assert centers(9, chart) == ([1], 3)
    assert centers(2, [(0, 1, 1)]) == ([0, 1], 1)  # odd diameter: two centers
    assert centers(1, []) == ([0], 0)

    rng = random.Random(27)
    for _ in range(400):
        n = rng.randint(1, 15)
        edges = random_tree(rng, n, 0, 9)
        expected = diameter_brute(n, edges)
        assert diameter_two_sweeps(n, edges)[0] == expected == diameter_dp(n, edges)
        adj = adjacency(n, edges)
        brute_ecc = [max(distances_from(adj, v)) for v in range(n)]
        assert eccentricities(n, edges) == brute_ecc
        unit = [(u, v, 1) for u, v, _ in edges]
        found, radius = centers(n, unit)
        d = diameter_brute(n, unit)
        assert radius == (d + 1) // 2 and len(found) == 1 + d % 2
        edges = random_tree(rng, n, -9, 9)
        assert diameter_dp(n, edges) == diameter_brute(n, edges)


if __name__ == "__main__":
    main()
```


All fast methods take **O(V)** time and space; the brute force takes O(V²).

A second classic method for unweighted trees **peels leaves**: repeatedly remove all current leaves (vertices of degree 1) in rounds, like peeling an onion. The last one or two vertices left are the centers. It reaches the same answer and is a good exercise in BFS by layers.

## 6. Summary

| Question | Method | Weights | Time |
|---|---|---|---:|
| Diameter | Two sweeps: farthest from anywhere, then farthest from that | nonnegative | O(V) |
| Diameter | Tree DP: best two clipped branches at each highest vertex | any | O(V) |
| Every eccentricity | `max(dist(v, x), dist(v, y))` for a diameter `x–y` | nonnegative | O(V) |
| Centers, radius | Minimizers of eccentricity; middle of the diameter when unweighted | nonnegative | O(V) |

## 7. Pitfalls and practice

1. Using two sweeps with negative weights. Use the DP.
2. Running two sweeps on a general graph with cycles. It is not exact there; exact diameter of a general graph needs all-pairs shortest paths.
3. Counting the diameter in vertices instead of edges. State which one the problem wants; they differ by 1.
4. In the DP, adding the best two branches from the **same** child. The two branches must come from different children.
5. Forgetting that the empty route is allowed (diameter 0 for one vertex). Problems about "a path with at least one edge" need a different base case.
6. Recursion on deep trees. Process vertices in reverse BFS order, as above.

Practice: tree diameter from an edge list; minimum height trees (centers); maximum path sum with negative weights (the DP); longest path with different adjacent characters (DP with a condition on branches); sum of distances in a tree (rerooting DP, in [Tree and DAG DP](../../09-dynamic-programming/08-tree-and-dag-dp.md)).

Next: [Maximum Flow and Bipartite Matching](03-flow-and-matching.md).
