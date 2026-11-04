# Rooting a Tree and Lowest Common Ancestors — Jumping Up in Powers of Two

## 1. An org chart

A company has nine people, 0 to 8. You are given who works directly with whom, as eight undirected links, with no hint of who is the boss:

```text
links: 0–1  0–2  1–3  1–4  2–5  4–6  4–7  6–8
```

Person 0 is the CEO. Drawn with the CEO on top:

```text
              0              depth 0
            ╱   ╲
           1     2           depth 1
         ╱   ╲     ╲
        3     4     5        depth 2
            ╱   ╲
           6     7           depth 3
           │
           8                 depth 4
```

Questions arrive by the thousands:

- **Who is the lowest manager above both `u` and `v`?** For 8 and 7 it is 4; for 8 and 5 it is 0; for 3 and 4 it is 1; for 4 and 8 it is 4 itself.
- **How many links separate `u` and `v`?** 8 and 5 are 6 links apart: `8–6–4–1–0–2–5`.
- **What is the total salary in `u`'s department** (`u` and everyone under `u`), when salaries change over time?

The vertex in the first question is the **lowest common ancestor** (LCA): the deepest vertex that is an ancestor of both. A vertex counts as its own ancestor, which is why `LCA(4, 8) = 4`.

## 2. Rooting: parent and depth arrays

The words **root**, **parent**, **child**, **depth** and **subtree** mean what they mean for [binary trees](../../03-trees/01-binary-trees-and-traversals.md). The difference here is the input: an edge list names no root and no parent, and a vertex may have any number of children. **Rooting** picks a root and orients every edge away from it with one traversal: when the traversal moves from `u` to a neighbor `v` that is not `u`'s parent, set `parent[v] = u` and `depth[v] = depth[u] + 1`.

```text
vertex   0  1  2  3  4  5  6  7  8
parent   0  0  0  1  1  2  4  4  6      (the root is its own parent)
depth    0  1  1  2  2  2  3  3  4
```

Two choices save trouble later:

- **The root is its own parent**, so a jump "above the root" stays at the root with no special case.
- **An explicit stack, not recursion.** Python's recursion limit (about 1000) is far below the depth of a chain of 10⁵ vertices.

**Validating a tree.** A graph on `V` vertices is a tree exactly when it has `V − 1` edges and is connected. The traversal checks both: count the edges, and confirm all `V` vertices were reached.

## 3. Entry times: every subtree is a range

During the same traversal, give each vertex an **entry time** `tin[v]`, its position in the order vertices are first visited, and an **exit time** `tout[v]`, the number of vertices visited by the time `v`'s whole subtree is finished.

```text
visit order   0  1  3  4  6  8  7  2  5
position      0  1  2  3  4  5  6  7  8

vertex   0  1  2  3  4  5  6  7  8
tin      0  1  7  2  3  8  4  6  5
tout     9  7  9  3  7  9  6  7  6
```

**Key observation.** A depth-first traversal enters a vertex, then visits its entire subtree, and only then moves elsewhere. So the subtree of `v` occupies exactly the positions `[tin[v], tout[v])` of the visit order, a half-open range with `tout[v] − tin[v]` vertices.

Check vertex 4: positions `[3, 7)` hold `4, 6, 8, 7`, which is exactly its department. Vertex 1: `[1, 7)` holds `1, 3, 4, 6, 8, 7`.

Two consequences:

- **`u` is an ancestor of `v`** exactly when `tin[u] ≤ tin[v] < tout[u]`. An O(1) test.
- **Subtree sums with updates.** Put `salary[v]` at array position `tin[v]`. "Total salary in `v`'s department" becomes a range sum over `[tin[v], tout[v])`, and "change `v`'s salary" becomes a point update at `tin[v]`. A **Fenwick tree** (binary indexed tree) does both in O(log V); [Range queries](../../04-range-queries/README.md) builds it from scratch.

This flattening is often called an **Euler tour** of the tree. (Section 8 uses a longer walk with the same name; the two are different arrays.)

```python
import random


def root_tree(n, edges, root=0):
    """Iterative DFS. Returns parent, depth, tin, tout, order. Validates the tree."""
    if n < 1 or not 0 <= root < n:
        raise ValueError("need a nonempty tree and a valid root")
    if len(edges) != n - 1:
        raise ValueError("a tree on n vertices has n - 1 edges")
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    depth = [0] * n
    tin = [0] * n
    tout = [0] * n
    order = []
    parent[root] = root
    stack = [(root, False)]
    while stack:
        u, leaving = stack.pop()
        if leaving:
            tout[u] = len(order)
            continue
        tin[u] = len(order)
        order.append(u)
        stack.append((u, True))
        for v in reversed(adj[u]):
            if parent[v] == -1:
                parent[v] = u
                depth[v] = depth[u] + 1
                stack.append((v, False))
    if len(order) != n:
        raise ValueError("edges do not form a tree")
    return parent, depth, tin, tout, order


class Fenwick:
    def __init__(self, n):
        self.tree = [0] * (n + 1)

    def add(self, i, delta):
        i += 1
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i

    def prefix(self, i):
        """Sum of positions [0, i)."""
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total


class SubtreeSums:
    def __init__(self, n, edges, values, root=0):
        self.parent, self.depth, self.tin, self.tout, _ = root_tree(n, edges, root)
        self.values = list(values)
        self.fenwick = Fenwick(n)
        for v in range(n):
            self.fenwick.add(self.tin[v], self.values[v])

    def update(self, v, new_value):
        self.fenwick.add(self.tin[v], new_value - self.values[v])
        self.values[v] = new_value

    def subtree_sum(self, v):
        return self.fenwick.prefix(self.tout[v]) - self.fenwick.prefix(self.tin[v])

    def is_ancestor(self, u, v):
        return self.tin[u] <= self.tin[v] < self.tout[u]


def random_tree(rng, n):
    edges = [(rng.randrange(v), v) for v in range(1, n)]
    label = list(range(n))
    rng.shuffle(label)
    return [(label[u], label[v]) for u, v in edges]


def main():
    chart = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (4, 6), (4, 7), (6, 8)]
    parent, depth, tin, tout, order = root_tree(9, chart)
    assert parent == [0, 0, 0, 1, 1, 2, 4, 4, 6]
    assert depth == [0, 1, 1, 2, 2, 2, 3, 3, 4]
    assert order == [0, 1, 3, 4, 6, 8, 7, 2, 5]
    assert tin == [0, 1, 7, 2, 3, 8, 4, 6, 5] and tout == [9, 7, 9, 3, 7, 9, 6, 7, 6]
    assert sorted(order[tin[4]:tout[4]]) == [4, 6, 7, 8]

    sums = SubtreeSums(9, chart, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    assert sums.subtree_sum(4) == 50 + 70 + 80 + 90
    sums.update(8, 0)
    assert sums.subtree_sum(1) == 20 + 40 + 50 + 70 + 80
    assert sums.is_ancestor(1, 8) and not sums.is_ancestor(2, 8) and sums.is_ancestor(5, 5)

    for bad in ([(0, 1), (1, 2), (2, 0)], [(0, 1)]):
        try:
            root_tree(4, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("non-tree accepted")
    assert root_tree(1, [])[:2] == ([0], [0])
    root_tree(100_000, [(v - 1, v) for v in range(1, 100_000)])  # long chain, no recursion

    rng = random.Random(24)
    for _ in range(200):
        n = rng.randint(1, 30)
        edges = random_tree(rng, n)
        root = rng.randrange(n)
        values = [rng.randint(-5, 5) for _ in range(n)]
        sums = SubtreeSums(n, edges, values, root)
        parent = sums.parent

        def in_subtree(v, top):
            while True:
                if v == top:
                    return True
                if v == parent[v]:
                    return False
                v = parent[v]

        for _ in range(20):
            if rng.random() < 0.5:
                v = rng.randrange(n)
                values[v] = rng.randint(-5, 5)
                sums.update(v, values[v])
            else:
                top = rng.randrange(n)
                expected = sum(values[v] for v in range(n) if in_subtree(v, top))
                assert sums.subtree_sum(top) == expected
                other = rng.randrange(n)
                assert sums.is_ancestor(top, other) == in_subtree(other, top)


if __name__ == "__main__":
    main()
```

Rooting takes O(V) time and space. Each subtree query or update takes O(log V).

## 4. Lowest common ancestor, the slow way

**Naive method.**

1. Walk the deeper vertex up until both are at the same depth.
2. While they differ, move both up one step.
3. Where they meet is the LCA.

Trace for `LCA(8, 7)`: depths 4 and 3. Step 1 moves 8 up to 6 (depth 3). Step 2: `6 ≠ 7`, move both up: 4 and 4. Equal, so the LCA is **4**.

Each query costs O(depth): on a chain of 10⁵ vertices, 10⁵ queries take 10¹⁰ steps.

## 5. Binary lifting: jump `2^j` levels at once

**Key observation.** Any climb of `k` levels can be split into jumps whose sizes are powers of two, following the binary digits of `k`. Climbing 5 levels is a jump of 4 then a jump of 1, because `5 = 101` in binary. If we know, for every vertex, its ancestor 1, 2, 4, 8, … levels up, any climb takes at most `log₂ V` jumps.

Let `up[j][v]` be the ancestor of `v` that is `2^j` levels up (the root if that goes past the top). Then

$$
up[0][v] = parent[v], \qquad up[j][v] = up[j-1]\bigl[\,up[j-1][v]\,\bigr],
$$

because jumping `2^j` levels is two jumps of `2^{j−1}`. The table for the org chart:

```text
vertex           0  1  2  3  4  5  6  7  8
up[0] (1 up)     0  0  0  1  1  2  4  4  6
up[1] (2 up)     0  0  0  0  0  0  1  1  4
up[2] (4 up)     0  0  0  0  0  0  0  0  0
up[3] (8 up)     0  0  0  0  0  0  0  0  0
```

Read one entry: `up[1][8] = up[0][up[0][8]] = up[0][6] = 4`. And `up[2][8] = up[1][up[1][8]] = up[1][4] = 0`.

**`k`-th ancestor.** For each set bit `j` of `k`, do `v = up[j][v]`. Example: the 3rd ancestor of 8 (`3 = 11` in binary): `up[0][8] = 6`, then `up[1][6] = 1`. Check: `8 → 6 → 4 → 1`. ✓

**LCA with jumps.**

1. Lift the deeper vertex by the depth difference, using the `k`-th ancestor jump. If the two are now equal, that vertex is the LCA (one was an ancestor of the other).
2. Otherwise, for `j` from the largest down to 0: if `up[j][u] ≠ up[j][v]`, jump both: `u = up[j][u]`, `v = up[j][v]`.
3. Answer `parent[u]`.

**Invariant of step 2:** `u` and `v` are at the same depth, different, and both strictly below the LCA. A jump that lands them on *different* vertices stays below the LCA, so it is safe to take. A jump that lands them on the *same* vertex might overshoot the LCA, so it is skipped. After trying every size from large to small, they sit directly below the LCA, as its two different children.

Trace `LCA(8, 5)`: depths 4 and 2, difference `2 = 10` in binary, so `u = up[1][8] = 4`. Now `u = 4`, `v = 5`, both depth 2, different.

| `j` | `up[j][u]` | `up[j][v]` | Equal? | Action | `u, v` after |
|---:|---:|---:|---|---|---|
| 3 | 0 | 0 | yes | skip | 4, 5 |
| 2 | 0 | 0 | yes | skip | 4, 5 |
| 1 | 0 | 0 | yes | skip | 4, 5 |
| 0 | 1 | 2 | no | jump | 1, 2 |

Answer `parent[1] = 0`. ✓

Trace `LCA(8, 7)`: lift 8 by 1 to 6. Then `u = 6`, `v = 7`: `up[3]`, `up[2]`, `up[1]` and `up[0]` are all equal (0, 0, 1, 4), so nothing jumps. Answer `parent[6] = 4`. ✓

## 6. Distances and other path queries

The route between `u` and `v` goes up from `u` to `a = LCA(u, v)` and down to `v`. So

$$
\text{dist}(u, v) = depth[u] + depth[v] - 2\,depth[a].
$$

For 8 and 5: `4 + 2 − 2·0 = 6`. ✓ For 8 and 7, the LCA is 4 at depth 2: `4 + 3 − 2·2 = 3`, the route `8–6–4–7`. ✓

**Weighted edges.** Replace depth by `root_dist[v]`, the sum of edge weights from the root to `v`. The same formula gives the weighted path length, even with negative weights, because the shared part above the LCA is subtracted twice and nothing else is. (This is the length of the unique *simple* route. If a problem allowed walks that repeat edges, a single negative undirected edge could be crossed back and forth forever, and "shortest" would be unbounded.)

**Values on vertices instead of edges.** With `root_sum[v]` summing vertex values from the root down to `v` inclusive, the path sum is `root_sum[u] + root_sum[v] − 2·root_sum[a] + value[a]`: the LCA's own value was subtracted twice but lies on the path once.

**Maximum edge on a path.** Sums cancel, but maxima do not, so the subtraction trick fails. Instead store, next to each jump, the largest edge weight it passes over: `mx[0][v] = w(v, parent[v])`, and `mx[j][v] = max(mx[j−1][v], mx[j−1][up[j−1][v]])`. While lifting `u` and `v` to the LCA, take the maximum of the `mx` values of every jump. This answers bottleneck questions on a [minimum spanning tree](../03-minimum-spanning-trees/05-forests-and-variants.md#4-minimum-bottleneck-the-largest-edge-on-a-route) in O(log V), and is the speed-up for second-best MST.

## 7. Code: binary lifting, tested against walking the path

```python
import random


class LiftingTree:
    def __init__(self, n, edges, root=0):
        """edges: (u, v, w) undirected; use w = 1 for unweighted trees."""
        if n < 1 or not 0 <= root < n or len(edges) != n - 1:
            raise ValueError("need n >= 1, a valid root and n - 1 edges")
        adj = [[] for _ in range(n)]
        for u, v, w in edges:
            adj[u].append((v, w))
            adj[v].append((u, w))
        self.n = n
        self.depth = [0] * n
        self.root_dist = [0] * n
        parent = [-1] * n
        up_weight = [-float("inf")] * n  # weight of the edge to the parent
        parent[root] = root
        stack = [root]
        seen = 1
        while stack:
            u = stack.pop()
            for v, w in adj[u]:
                if parent[v] == -1:
                    parent[v] = u
                    up_weight[v] = w
                    self.depth[v] = self.depth[u] + 1
                    self.root_dist[v] = self.root_dist[u] + w
                    stack.append(v)
                    seen += 1
        if seen != n:
            raise ValueError("edges do not form a tree")
        self.up = [parent]
        self.mx = [up_weight]
        for _ in range(1, max(1, (n - 1).bit_length())):
            prev_up, prev_mx = self.up[-1], self.mx[-1]
            self.up.append([prev_up[prev_up[v]] for v in range(n)])
            self.mx.append([max(prev_mx[v], prev_mx[prev_up[v]]) for v in range(n)])

    def kth_ancestor(self, v, k):
        if k > self.depth[v]:
            return None
        j = 0
        while k:
            if k & 1:
                v = self.up[j][v]
            k >>= 1
            j += 1
        return v

    def _lift(self, v, k, best):
        j = 0
        while k:
            if k & 1:
                best = max(best, self.mx[j][v])
                v = self.up[j][v]
            k >>= 1
            j += 1
        return v, best

    def lca_and_max(self, u, v):
        best = -float("inf")
        if self.depth[u] < self.depth[v]:
            u, v = v, u
        u, best = self._lift(u, self.depth[u] - self.depth[v], best)
        if u == v:
            return u, best
        for j in range(len(self.up) - 1, -1, -1):
            if self.up[j][u] != self.up[j][v]:
                best = max(best, self.mx[j][u], self.mx[j][v])
                u, v = self.up[j][u], self.up[j][v]
        best = max(best, self.mx[0][u], self.mx[0][v])
        return self.up[0][u], best

    def lca(self, u, v):
        return self.lca_and_max(u, v)[0]

    def edges_between(self, u, v):
        return self.depth[u] + self.depth[v] - 2 * self.depth[self.lca(u, v)]

    def weighted_distance(self, u, v):
        a = self.lca(u, v)
        return self.root_dist[u] + self.root_dist[v] - 2 * self.root_dist[a]

    def path_max(self, u, v):
        """Largest edge weight on the path, -inf when u == v."""
        return self.lca_and_max(u, v)[1]


def naive_path(n, edges, u, v):
    """The unique u-v path as a list of edge weights, plus its vertices."""
    adj = [[] for _ in range(n)]
    for a, b, w in edges:
        adj[a].append((b, w))
        adj[b].append((a, w))
    came = {u: None}
    stack = [u]
    while stack:
        x = stack.pop()
        for y, w in adj[x]:
            if y not in came:
                came[y] = (x, w)
                stack.append(y)
    weights, vertices = [], [v]
    while came[v] is not None:
        v, w = came[v]
        weights.append(w)
        vertices.append(v)
    return weights, vertices


def main():
    chart = [(0, 1, 1), (0, 2, 1), (1, 3, 1), (1, 4, 1), (2, 5, 1),
             (4, 6, 1), (4, 7, 1), (6, 8, 1)]
    tree = LiftingTree(9, chart)
    assert tree.up[0] == [0, 0, 0, 1, 1, 2, 4, 4, 6]
    assert tree.up[1] == [0, 0, 0, 0, 0, 0, 1, 1, 4]
    assert tree.lca(8, 7) == 4 and tree.lca(8, 5) == 0
    assert tree.lca(3, 4) == 1 and tree.lca(4, 8) == 4
    assert tree.edges_between(8, 5) == 6 and tree.edges_between(8, 7) == 3
    assert tree.kth_ancestor(8, 3) == 1 and tree.kth_ancestor(8, 5) is None

    single = LiftingTree(1, [])
    assert single.lca(0, 0) == 0 and single.path_max(0, 0) == -float("inf")
    chain = LiftingTree(50_000, [(v - 1, v, 1) for v in range(1, 50_000)])
    assert chain.lca(49_999, 25_000) == 25_000

    rng = random.Random(25)
    for _ in range(300):
        n = rng.randint(1, 25)
        edges = [(rng.randrange(v), v, rng.randint(-5, 9)) for v in range(1, n)]
        label = list(range(n))
        rng.shuffle(label)
        edges = [(label[a], label[b], w) for a, b, w in edges]
        root = rng.randrange(n)
        tree = LiftingTree(n, edges, root)
        parent = tree.up[0]
        for _ in range(15):
            u, v = rng.randrange(n), rng.randrange(n)
            weights, vertices = naive_path(n, edges, u, v)
            assert tree.lca(u, v) == min(vertices, key=tree.depth.__getitem__)  # highest path vertex
            assert tree.edges_between(u, v) == len(weights)
            assert tree.weighted_distance(u, v) == sum(weights)
            assert tree.path_max(u, v) == max(weights, default=-float("inf"))
            k = rng.randint(0, n)
            expected = u
            for _ in range(k):
                expected = None if expected is None or expected == root else parent[expected]
            assert tree.kth_ancestor(u, k) == expected


if __name__ == "__main__":
    main()
```

Building the table takes **O(V log V)** time and space. Each `kth_ancestor`, `lca`, distance, or path-maximum query takes **O(log V)**.

**Why it is correct.** The table recurrence is correct because a `2^j` climb is two `2^{j−1}` climbs. The `k`-th ancestor is correct because the jumps for the set bits of `k` add up to `k`. The LCA loop keeps its invariant (both strictly below the LCA) at every step; at the end, no jump size from `2^{L−1}` down to 1 keeps them apart, so their distance to the LCA is less than 1 jump of every size, which means exactly 1 level: their parent is the LCA.

## 8. LCA by Euler walk and sparse table

Binary lifting answers each query in O(log V). With a different preprocessing, LCA queries take **O(1)**.

**The Euler walk.** Walk around the tree with a DFS and write down the current vertex every time you **arrive** at it, including when you come back up from a child. Each edge is walked down once and up once, so the walk has `2V − 1` entries. Record `first[v]`, the position where `v` first appears.

```text
position  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
walk      0  1  3  1  4  6  8  6  4  7  4  1  0  2  5  2  0
depth     0  1  2  1  2  3  4  3  2  3  2  1  0  1  2  1  0

vertex    0  1  2  3  4  5  6  7  8
first     0  1 13  2  4 14  5  9  6
```

**Key observation.** Between the first visits of `u` and `v`, the walk travels from `u` to `v`. To get from one to the other it must pass through their LCA, and it never goes above the LCA (that would mean leaving the LCA's subtree, which only happens after both are done). So:

> `LCA(u, v)` is the vertex of smallest depth in `walk[first[u] .. first[v]]` (inclusive, with `first[u] ≤ first[v]`).

`LCA(8, 5)`: positions 6 to 14 hold `8 6 4 7 4 1 0 2 5`, depths `4 3 2 3 2 1 0 1 2`. The shallowest is 0. ✓
`LCA(8, 7)`: positions 6 to 9 hold `8 6 4 7`, depths `4 3 2 3`. The shallowest is 4. ✓

LCA has become a **range minimum query** (RMQ) on a fixed array.

**The sparse table.** Precompute, for every start `i` and every power of two `2^j`, the shallowest vertex in `walk[i .. i + 2^j − 1]`:

$$
sp[0][i] = walk[i], \qquad sp[j][i] = \text{shallower of } sp[j-1][i] \text{ and } sp[j-1][i + 2^{j-1}].
$$

```text
position   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
sp[0]      0  1  3  1  4  6  8  6  4  7  4  1  0  2  5  2  0
sp[1]      0  1  1  1  4  6  6  4  4  4  1  0  0  2  2  0
sp[2]      0  1  1  1  4  4  4  4  1  0  0  0  0  0
sp[3]      0  1  1  1  1  0  0  0  0  0
sp[4]      0  0
```

A query on `[l, r]` covers the range with **two overlapping blocks** of the same size `2^j`, where `2^j` is the largest power of two not exceeding the length: one block starting at `l`, one ending at `r`. Overlap is harmless for a minimum (counting an element twice does not change the minimum), so the answer is the shallower of `sp[j][l]` and `sp[j][r − 2^j + 1]`.

Query `[6, 14]` for `LCA(8, 5)`: length 9, so `2^j = 8`, `j = 3`. Blocks `sp[3][6] = 0` (positions 6–13) and `sp[3][7] = 0` (positions 7–14). Answer 0. ✓
Query `[6, 9]` for `LCA(8, 7)`: length 4, `j = 2`. Blocks `sp[2][6] = 4` and `sp[2][6] = 4`. Answer 4. ✓

```python
import random


class EulerLCA:
    def __init__(self, n, edges, root=0):
        adj = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        self.depth = [0] * n
        self.first = [-1] * n
        walk = []
        # Iterative DFS that records a vertex on arrival and on every return.
        parent = [-1] * n
        parent[root] = root
        stack = [(root, 0)]
        while stack:
            u, i = stack.pop()
            if i == 0:
                self.first[u] = len(walk)
            walk.append(u)
            while i < len(adj[u]) and adj[u][i] == parent[u]:
                i += 1
            if i < len(adj[u]):
                v = adj[u][i]
                if parent[v] != -1:
                    raise ValueError("edges contain a cycle")
                stack.append((u, i + 1))
                parent[v] = u
                self.depth[v] = self.depth[u] + 1
                stack.append((v, 0))
        if len(walk) != 2 * n - 1 or -1 in self.first:
            raise ValueError("edges do not form a tree")
        self.walk = walk
        self.sp = [walk[:]]
        j = 1
        while (1 << j) <= len(walk):
            prev, half = self.sp[-1], 1 << (j - 1)
            self.sp.append([self._shallower(prev[i], prev[i + half])
                            for i in range(len(walk) - (1 << j) + 1)])
            j += 1

    def _shallower(self, a, b):
        return a if self.depth[a] <= self.depth[b] else b

    def lca(self, u, v):
        l, r = sorted((self.first[u], self.first[v]))
        j = (r - l + 1).bit_length() - 1
        return self._shallower(self.sp[j][l], self.sp[j][r - (1 << j) + 1])


def naive_lca(n, edges, root, u, v):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    parent = {root: None}
    stack = [root]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in parent:
                parent[y] = x
                stack.append(y)
    ancestors = set()
    while u is not None:
        ancestors.add(u)
        u = parent[u]
    while v not in ancestors:
        v = parent[v]
    return v


def main():
    chart = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (4, 6), (4, 7), (6, 8)]
    euler = EulerLCA(9, chart)
    assert euler.walk == [0, 1, 3, 1, 4, 6, 8, 6, 4, 7, 4, 1, 0, 2, 5, 2, 0]
    assert euler.first == [0, 1, 13, 2, 4, 14, 5, 9, 6]
    assert euler.sp[3] == [0, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    assert euler.lca(8, 5) == 0 and euler.lca(8, 7) == 4 and euler.lca(4, 8) == 4
    assert EulerLCA(1, []).lca(0, 0) == 0
    for bad in ([(0, 1), (1, 2), (2, 0)], [(0, 1), (2, 3)]):
        try:
            EulerLCA(4, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("non-tree accepted")

    rng = random.Random(26)
    for _ in range(300):
        n = rng.randint(1, 30)
        edges = [(rng.randrange(v), v) for v in range(1, n)]
        root = rng.randrange(n)
        euler = EulerLCA(n, edges, root)
        for _ in range(20):
            u, v = rng.randrange(n), rng.randrange(n)
            assert euler.lca(u, v) == naive_lca(n, edges, root, u, v)


if __name__ == "__main__":
    main()
```

Building takes **O(V log V)** time and space; each query takes **O(1)**: two table lookups.

## 9. Choosing a method

| Method | Build | Query | Extra abilities |
|---|---:|---:|---|
| Naive climb | O(V) | O(depth), up to O(V) | Nothing to build |
| Binary lifting | O(V log V) | O(log V) | `k`-th ancestor, path maximum/minimum, jumping "while a condition holds" |
| Euler walk + sparse table | O(V log V) | O(1) | Fastest pure LCA; no path aggregates |
| Offline Tarjan LCA (DSU, all queries known in advance) | O(V + Q α(V)) | — | Good when every query is known up front |

All of these assume the tree does not change shape. If edges are added or removed, the tables must be rebuilt (or a dynamic structure such as a link-cut tree is needed, which is beyond this guide). If only **values** on vertices change, the entry-time flattening of §3 with a Fenwick or segment tree still works.

## 10. Pitfalls and practice

1. Recursive DFS on a chain of 10⁵ vertices. Python raises `RecursionError`; use an explicit stack.
2. Off-by-one in the number of levels. The table needs `2^{L−1} ≥` the maximum depth; `(n − 1).bit_length()` levels are enough, with at least one level for `n = 1`.
3. Forgetting the "already equal after leveling" check, which happens when one vertex is an ancestor of the other.
4. Mixing half-open `[tin, tout)` with an inclusive range API. Convert once, in one place.
5. Using the depth formula for weighted distance, or the root-distance formula for path maximum. Sums cancel; maxima do not.
6. Confusing the entry-order array (length `V`) with the Euler walk (length `2V − 1`).
7. Assuming the input is a tree. Check `V − 1` edges and connectivity.

Practice: kth ancestor of a tree node; LCA queries on an edge-list tree (the recursive binary-tree LCA is in [Construction, paths and LCA](../../03-trees/04-construction-paths-and-lca.md)); distance between two nodes in a tree; subtree sum queries with updates; maximum edge weight on a tree path; minimum edge weight queries on a path; count nodes in a subtree with a given label (entry-time ranges).

Next: [Tree Diameter and Centers](02-tree-diameter.md).
