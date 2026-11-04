# Tree and DAG DP — Solve Every Subtree Once

## 1. Maximum-weight independent set on a tree

Each vertex of a tree has a weight. Choose vertices so that no two chosen vertices are joined by an edge, and maximize the total weight. The empty set is allowed, so the answer is never negative. (House Robber III is this problem on a binary tree: robbing two directly linked houses sets off an alarm.)

This tree runs through the first half of the chapter. The number in parentheses is each vertex's weight; vertex 0 is the root. Roots, parents, children and subtrees are defined in [Binary Trees and Traversals](../03-trees/01-binary-trees-and-traversals.md).

```text
              0 (3)
            /       \
        1 (2)       2 (1)
        /   \           \
    3 (4)   4 (5)       5 (6)
```

The answer is `18`: choose `{0, 3, 4, 5}` for `3 + 4 + 5 + 6`.

**Brute force.** Try all `2^n` subsets and discard those with an adjacent pair. At `n = 40` that is a trillion subsets; it is only a checker.

### 1.1 Why subtrees can be solved separately

The subtree of `1` is `{1, 3, 4}` and the subtree of `2` is `{2, 5}`. No edge joins them; the only route between them passes through `0`. So once we decide what happens at `0`, the two child subtrees are separate, smaller problems: choices inside one cannot affect the other. In a general graph this fails, since an extra edge `4 — 5` would let them interfere. This independence is what every tree DP rests on.

### 1.2 State and transition

What does a parent need to know about a child's subtree? Only whether the child itself is chosen, because that is the only vertex of the subtree the parent touches. So keep two numbers per vertex:

- `take[v]` = the best total inside `v`'s subtree **with `v` chosen**.
- `skip[v]` = the best total inside `v`'s subtree **with `v` not chosen**.

If `v` is chosen, no child may be; if not, each child is free:

$$
take[v] = weight[v] + \sum_{c \text{ child of } v} skip[c],
\qquad
skip[v] = \sum_{c \text{ child of } v} \max(take[c],\ skip[c]).
$$

Summing is allowed because the child subtrees are independent: maximizing each one separately maximizes their total. A leaf has `take = weight`, `skip = 0`. The answer is `max(take[root], skip[root])`.

**Order: children before parents** (**postorder**). A recursive DFS gives this for free, but Python's recursion limit (about 1000) crashes on a path-shaped tree of 100,000 vertices. The iterative fix: BFS from the root lists every parent before its children, so **reversed BFS order** lists every child before its parent. All the tree code below uses it.

### 1.3 Trace

| Vertex | Children | `take` | `skip` |
|---|---|---|---|
| 3 | — | 4 | 0 |
| 4 | — | 5 | 0 |
| 5 | — | 6 | 0 |
| 1 | 3, 4 | 2 + 0 + 0 = 2 | max(4,0) + max(5,0) = 9 |
| 2 | 5 | 1 + 0 = 1 | max(6,0) = 6 |
| 0 | 1, 2 | 3 + 9 + 6 = **18** | max(2,9) + max(1,6) = 15 |

The answer is `max(18, 15) = 18`.

**Reconstruction.** Walk **down** from the root carrying one bit: "was my parent chosen?" If so, `v` is skipped; otherwise choose `v` exactly when `take[v] > skip[v]`. At `0`, `18 > 15`, so choose `0`; then `1` and `2` must be skipped; their children see an unchosen parent and are chosen (`4 > 0`, `5 > 0`, `6 > 0`). Result `{0, 3, 4, 5}`.

```python
import random
from itertools import combinations


def root_tree(n: int, edges: list[tuple[int, int]]) -> tuple[list[int], list[int], list[list[int]]]:
    """Return (parent, bfs_order, children) for the tree rooted at 0."""
    if n == 0:
        if edges:
            raise ValueError("an empty tree cannot have edges")
        return [], [], []
    if len(edges) != n - 1:
        raise ValueError("a tree must have n-1 edges")
    adjacency = [[] for _ in range(n)]
    for a, b in edges:
        if not (0 <= a < n and 0 <= b < n) or a == b:
            raise ValueError("invalid tree edge")
        adjacency[a].append(b)
        adjacency[b].append(a)
    parent = [-2] * n
    parent[0] = -1
    order = [0]
    children = [[] for _ in range(n)]
    for v in order:
        for u in adjacency[v]:
            if u == parent[v]:
                continue
            if parent[u] != -2:
                raise ValueError("input contains a cycle or parallel edge")
            parent[u] = v
            children[v].append(u)
            order.append(u)
    if len(order) != n:
        raise ValueError("input is disconnected")
    return parent, order, children


def tree_independent_set(weights: list[int], edges: list[tuple[int, int]]) -> tuple[int, list[int]]:
    n = len(weights)
    _, order, children = root_tree(n, edges)
    if n == 0:
        return 0, []
    take = weights.copy()
    skip = [0] * n
    for v in reversed(order):  # children before parents
        for c in children[v]:
            take[v] += skip[c]
            skip[v] += max(take[c], skip[c])

    selected = []
    stack = [(0, False)]  # (vertex, was its parent chosen?)
    while stack:
        v, parent_chosen = stack.pop()
        choose_v = not parent_chosen and take[v] > skip[v]
        if choose_v:
            selected.append(v)
        for c in children[v]:
            stack.append((c, choose_v))
    return max(take[0], skip[0]), sorted(selected)


def brute_force(weights: list[int], edges: list[tuple[int, int]]) -> int:
    n = len(weights)
    best = 0
    for size in range(1, n + 1):
        for chosen in combinations(range(n), size):
            s = set(chosen)
            if all(not (a in s and b in s) for a, b in edges):
                best = max(best, sum(weights[v] for v in chosen))
    return best


def random_tree(rng: random.Random, n: int) -> list[tuple[int, int]]:
    labels = list(range(n))
    rng.shuffle(labels)
    return [(labels[i], labels[rng.randrange(i)]) for i in range(1, n)]


def main():
    weights = [3, 2, 1, 4, 5, 6]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]
    assert tree_independent_set(weights, edges) == (18, [0, 3, 4, 5])
    assert tree_independent_set([-5, -2], [(0, 1)]) == (0, [])
    assert tree_independent_set([7], []) == (7, [0])
    assert tree_independent_set([], []) == (0, [])
    # A 2000-vertex path would overflow a recursive DFS; the iterative order is fine.
    assert tree_independent_set([1] * 2000, [(i, i + 1) for i in range(1999)])[0] == 1000
    for bad in ([(0, 1), (1, 0)], [(0, 1)], [(0, 0), (1, 2)]):
        try:
            tree_independent_set([1, 1, 1], bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid tree accepted")

    rng = random.Random(8)
    for _ in range(300):
        n = rng.randint(1, 10)
        w = [rng.randint(-3, 9) for _ in range(n)]
        e = random_tree(rng, n)
        value, chosen = tree_independent_set(w, e)
        assert value == brute_force(w, e)
        assert sum(w[v] for v in chosen) == value
        s = set(chosen)
        assert all(not (a in s and b in s) for a, b in e)


if __name__ == "__main__":
    main()
```

O(n) time and space: each edge is read a constant number of times.

**Why it is correct.** A valid selection either contains `v` or not. If it does, the children are excluded and each child subtree holds a valid selection without its root, worth at most `skip[c]`. If not, each child subtree holds any valid selection, worth at most `max(take[c], skip[c])`. Combining the optimal child selections reaches both bounds, and they never conflict because the child subtrees share no edge.

### 1.4 Variant: node objects instead of an edge list

House Robber III hands you nodes with `left` and `right` pointers. The recurrence is the same; each node returns its pair `(take, skip)`, and a missing child contributes `(0, 0)`. Reversed preorder is again children-before-parents, with no recursion.

```python
import random
from dataclasses import dataclass


@dataclass
class Node:
    value: int
    left: "Node | None" = None
    right: "Node | None" = None


def rob(root: Node | None) -> int:
    order, stack = [], [root] if root else []
    while stack:  # preorder; reversed, it lists children before parents
        node = stack.pop()
        order.append(node)
        stack += [c for c in (node.left, node.right) if c is not None]
    pair = {None: (0, 0)}  # node id -> (take, skip); a missing child adds nothing
    for node in reversed(order):
        lt, ls = pair[id(node.left) if node.left else None]
        rt, rs = pair[id(node.right) if node.right else None]
        pair[id(node)] = (node.value + ls + rs, max(lt, ls) + max(rt, rs))
    return max(pair[id(root)]) if root else 0


def brute_force(node: Node | None, parent_taken: bool = False) -> int:
    if node is None:
        return 0
    skip = brute_force(node.left) + brute_force(node.right)
    if parent_taken:
        return skip
    return max(skip, node.value + brute_force(node.left, True) + brute_force(node.right, True))


def random_binary_tree(rng: random.Random, n: int) -> Node | None:
    if n == 0:
        return None
    k = rng.randrange(n)
    return Node(rng.randint(0, 9), random_binary_tree(rng, k), random_binary_tree(rng, n - 1 - k))


def main():
    assert rob(Node(3, Node(2, Node(4), Node(5)), Node(1, None, Node(6)))) == 18
    assert rob(None) == 0
    deep = Node(1)
    for _ in range(5000):  # a 5001-node chain: still no recursion
        deep = Node(1, deep)
    assert rob(deep) == 2501
    rng = random.Random(3)
    for _ in range(300):
        tree = random_binary_tree(rng, rng.randint(0, 12))
        assert rob(tree) == brute_force(tree)


if __name__ == "__main__":
    main()
```

The checker `brute_force` is plain recursion with no table: it re-solves the same subtrees many times and takes exponential time.

**More variants.** If the set must be nonempty and every weight is negative, return the largest single weight instead of 0. **Minimum vertex cover** on a tree (every edge needs a chosen endpoint) uses the same two states with `min` and the rule "if `v` is skipped, every child must be taken."

## 2. Tree diameter: the top two child depths

The **diameter** is the length of the longest path in the tree, in edges (or total weight, with nonnegative edge weights). In the running tree it is `3 — 1 — 0 — 2 — 5`, 4 edges. Brute force runs BFS from every vertex: O(n²).

**Key observation.** Every path in a rooted tree has a unique **highest vertex**. From there it goes down into at most two **different** child subtrees (entering the same child twice would repeat the edge to it). So organize paths by their highest vertex.

- `down[v]` = the longest path from `v` going only downward.

$$
down[v] = \max\Big(0,\ \max_{c}\big(down[c] + w(v,c)\big)\Big),
$$

$$
through[v] = \text{largest} + \text{second largest of } \{down[c] + w(v,c)\} \cup \{0, 0\}.
$$

The diameter is `max(through[v])`. The two zeros mean "do not go down on that side", so a single vertex is a path of length 0.

**Trace** (unweighted, `w = 1`):

| Vertex | Child values `down[c] + 1` | `down[v]` | `through[v]` |
|---|---|---|---|
| 3, 4, 5 | — | 0 | 0 |
| 1 | 1 (from 3), 1 (from 4) | 1 | 1 + 1 = 2 |
| 2 | 1 (from 5) | 1 | 1 + 0 = 1 |
| 0 | 2 (from 1), 2 (from 2) | 2 | 2 + 2 = **4** |

To rebuild the path, store `best_child[v]` (the child giving `down[v]`) and follow it down from both chosen children of the top vertex.

```python
import random
from collections import deque


def root_tree(n, adjacency):
    parent = [-2] * n
    parent[0] = -1
    order = [0]
    children = [[] for _ in range(n)]
    for v in order:
        for u, w in adjacency[v]:
            if u == parent[v]:
                continue
            if parent[u] != -2:
                raise ValueError("input contains a cycle")
            parent[u] = v
            children[v].append((u, w))
            order.append(u)
    if len(order) != n:
        raise ValueError("input is disconnected")
    return order, children


def tree_diameter(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[int]]:
    """Edges (a, b, length) with length >= 0. Returns (diameter, path)."""
    if n <= 0:
        raise ValueError("a tree needs at least one vertex")
    if len(edges) != n - 1:
        raise ValueError("a tree must have n-1 edges")
    adjacency = [[] for _ in range(n)]
    for a, b, w in edges:
        if not (0 <= a < n and 0 <= b < n) or a == b or w < 0:
            raise ValueError("invalid edge")
        adjacency[a].append((b, w))
        adjacency[b].append((a, w))
    order, children = root_tree(n, adjacency)

    down = [0] * n
    best_child = [-1] * n
    best, top, top_pair = 0, 0, (-1, -1)
    for v in reversed(order):
        first, second = (0, -1), (0, -1)  # (value, child) of the two best branches
        for c, w in children[v]:
            candidate = (down[c] + w, c)
            if candidate[0] > first[0]:
                first, second = candidate, first
            elif candidate[0] > second[0]:
                second = candidate
        down[v], best_child[v] = first
        if first[0] + second[0] > best:
            best, top, top_pair = first[0] + second[0], v, (first[1], second[1])

    def walk(v: int) -> list[int]:
        path = []
        while v != -1:
            path.append(v)
            v = best_child[v]
        return path

    left = walk(top_pair[0]) if top_pair[0] != -1 else []
    right = walk(top_pair[1]) if top_pair[1] != -1 else []
    return best, list(reversed(left)) + [top] + right


def brute_force(n, edges):
    adjacency = [[] for _ in range(n)]
    for a, b, w in edges:
        adjacency[a].append((b, w))
        adjacency[b].append((a, w))
    best = 0
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        queue = deque([s])
        while queue:  # in a tree every vertex is reached by exactly one path
            v = queue.popleft()
            for u, w in adjacency[v]:
                if dist[u] == -1:
                    dist[u] = dist[v] + w
                    queue.append(u)
        best = max(best, max(dist))
    return best


def main():
    edges = [(0, 1, 1), (0, 2, 1), (1, 3, 1), (1, 4, 1), (2, 5, 1)]
    length, path = tree_diameter(6, edges)
    assert length == 4 and path in ([3, 1, 0, 2, 5], [5, 2, 0, 1, 3], [4, 1, 0, 2, 5])
    assert tree_diameter(1, []) == (0, [0])
    assert tree_diameter(2, [(0, 1, 7)]) == (7, [1, 0])
    assert tree_diameter(3000, [(i, i + 1, 1) for i in range(2999)])[0] == 2999

    rng = random.Random(42)
    for _ in range(300):
        n = rng.randint(1, 12)
        labels = list(range(n))
        rng.shuffle(labels)
        e = [(labels[i], labels[rng.randrange(i)], rng.randint(0, 5)) for i in range(1, n)]
        length, path = tree_diameter(n, e)
        assert length == brute_force(n, e)
        weight = {frozenset((a, b)): w for a, b, w in e}
        assert len(set(path)) == len(path)
        assert sum(weight[frozenset(p)] for p in zip(path, path[1:])) == length


if __name__ == "__main__":
    main()
```

O(n) time and space. The "two BFS" trick (BFS to the farthest vertex `x`, then BFS from `x`; see [Tree Diameter](../10-graphs/05-trees-and-advanced/02-tree-diameter.md)) is also O(n), but it needs nonnegative weights. The DP stays correct with **negative** weights if the `w < 0` check is removed, because the `0` baseline never prefers a negative branch over stopping.

## 3. Rerooting: sum of distances from every vertex

For **every** vertex `v`, compute the sum of distances from `v` to all others (unweighted). In the running tree:

| Vertex | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Sum of distances | 8 | 8 | 10 | 12 | 12 | 14 |

For vertex `5`: 1 (to 2) + 2 (to 0) + 3 (to 1) + 4 (to 3) + 4 (to 4) = 14. BFS from every vertex is O(n²): ten billion steps at `n = 100,000`.

**Pass 1: one root.** Root at `0` and compute subtree sizes bottom-up, `size[v] = 1 + Σ size[c]`. The root's answer is the sum of depths: `1 + 1 + 2 + 2 + 2 = 8`.

**Pass 2: move the root one edge.** Going from `v` to its child `c`, the `size[c]` vertices in `c`'s subtree get one step closer and the other `n - size[c]` get one step farther:

$$
answer[c] = answer[v] - size[c] + (n - size[c]) = answer[v] + n - 2\,size[c].
$$

This is **rerooting**: compute one root's answer bottom-up, then push answers top-down with an O(1) correction per edge.

Sizes: `size[3] = size[4] = size[5] = 1`, `size[1] = 3`, `size[2] = 2`, `size[0] = 6`.

| Move | Formula | Answer |
|---|---|---|
| root | sum of depths | `answer[0] = 8` |
| 0 → 1 | 8 + 6 − 2·3 | `answer[1] = 8` |
| 0 → 2 | 8 + 6 − 2·2 | `answer[2] = 10` |
| 1 → 3 | 8 + 6 − 2·1 | `answer[3] = 12` |
| 1 → 4 | 8 + 6 − 2·1 | `answer[4] = 12` |
| 2 → 5 | 10 + 6 − 2·1 | `answer[5] = 14` |

For a weighted edge of length `w`, the change is `w · (n − 2·size[c])`.

The code for both rerooting problems is one script, at the end of §4. Two linear passes: O(n) time and space.

**Why it is correct.** Pass 1 uses `depth_sum[p] += depth_sum[v] + size[v]`: each vertex in `v`'s subtree is one edge farther from `p` than from `v`. Pass 2 visits parents before children, so `answer[parent[v]]` is final when `v` reads it.

## 4. General rerooting: excluding one child with prefix and suffix

Sum of distances was lucky: sums can be subtracted, so "everything except child `c`" was easy. `max` cannot be undone that way.

**Problem.** For every vertex `v`, find the tree's **height** when rooted at `v`: the largest distance from `v` to any vertex (its **eccentricity**).

| Vertex | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Height | 2 | 3 | 3 | 4 | 4 | 4 |

The vertices of minimum height (here only `0`) are the **centers**; Minimum Height Trees asks for them.

**Two directions.** A path from `v` either goes down into `v`'s subtree or leaves through its parent.

- `down[v]` = longest path going down, as in §2.
- `up[v]` = longest path from `v` that **avoids `v`'s subtree**; `up[root] = 0`.

The height is `max(down[v], up[v])`. For a child `c` of `v`, a path leaving `c`'s subtree takes the edge `c → v` and then goes anywhere **except back into `c`**: up from `v`, or down into a sibling `s ≠ c`:

$$
up[c] = 1 + \max\Big(up[v],\ \max_{s \text{ child of } v,\ s \ne c}\big(down[s] + 1\big)\Big).
$$

**The hard part** is "max over all siblings except `c`". Recomputing it per child is O(degree²) per vertex, O(n²) on a star. Knowing the max of all children does not give the max without one of them.

**Prefix and suffix maxima.** List `v`'s children `c_0 … c_{k-1}` with contributions `x_i = down[c_i] + 1`. Let `prefix[i] = max(x_0 … x_{i-1})` and `suffix[i] = max(x_{i+1} … x_{k-1})`. Then "all except `c_i`" is `max(prefix[i], suffix[i])`, and both arrays cost O(k). This is the "product of array except self" trick; it works for any associative combine (max, min, gcd, products), which makes it the **general** rerooting tool.

**Trace.** `down`: leaves 0, `down[1] = down[2] = 1`, `down[0] = 2`. At `v = 0`, children `[1, 2]`, contributions `[2, 2]`, `up[0] = 0`:

| Child | prefix | suffix | `up[child]` |
|---|---|---|---|
| 1 | −∞ | 2 | 1 + max(0, 2) = 3 |
| 2 | 2 | −∞ | 1 + max(0, 2) = 3 |

At `v = 1`, contributions `[1, 1]`: `up[3] = up[4] = 1 + max(3, 1) = 4`. At `v = 2`: `up[5] = 1 + max(3, −∞) = 4`. Heights `max(down, up)` = `2, 3, 3, 4, 4, 4`.

```python
import random
from collections import deque
from math import inf


def root_tree(n: int, edges: list[tuple[int, int]]):
    """Return (parent, bfs_order, children) for the tree rooted at 0."""
    if len(edges) != n - 1:
        raise ValueError("a tree must have n-1 edges")
    adjacency = [[] for _ in range(n)]
    for a, b in edges:
        if not (0 <= a < n and 0 <= b < n) or a == b:
            raise ValueError("invalid edge")
        adjacency[a].append(b)
        adjacency[b].append(a)
    parent = [-2] * n
    parent[0] = -1
    order, children = [0], [[] for _ in range(n)]
    for v in order:
        for u in adjacency[v]:
            if u == parent[v]:
                continue
            if parent[u] != -2:
                raise ValueError("input contains a cycle")
            parent[u] = v
            children[v].append(u)
            order.append(u)
    if len(order) != n:
        raise ValueError("input is disconnected")
    return parent, order, children


def sum_of_distances(n: int, edges: list[tuple[int, int]]) -> list[int]:
    if n == 0:
        return []
    parent, order, _ = root_tree(n, edges)
    size = [1] * n
    depth_sum = [0] * n  # sum of distances from v to the vertices of its subtree
    for v in reversed(order):  # pass 1: children before parents
        p = parent[v]
        if p >= 0:
            size[p] += size[v]
            depth_sum[p] += depth_sum[v] + size[v]
    answer = [0] * n
    answer[0] = depth_sum[0]
    for v in order[1:]:  # pass 2: parents before children
        answer[v] = answer[parent[v]] + n - 2 * size[v]
    return answer


def height_from_every_root(n: int, edges: list[tuple[int, int]]) -> list[int]:
    if n == 0:
        return []
    _, order, children = root_tree(n, edges)
    down = [0] * n
    for v in reversed(order):
        for c in children[v]:
            down[v] = max(down[v], down[c] + 1)
    up = [0] * n
    for v in order:  # parents before children
        x = [down[c] + 1 for c in children[v]]
        k = len(x)
        prefix = [-inf] * (k + 1)  # prefix[i] = max(x[:i])
        for i in range(k):
            prefix[i + 1] = max(prefix[i], x[i])
        suffix = [-inf] * (k + 1)  # suffix[i] = max(x[i:])
        for i in range(k - 1, -1, -1):
            suffix[i] = max(suffix[i + 1], x[i])
        for i, c in enumerate(children[v]):
            others = max(prefix[i], suffix[i + 1])  # every sibling except c
            up[c] = 1 + max(up[v], others)
    return [max(d, u) for d, u in zip(down, up)]


def all_distances(n, edges):
    """Brute force: BFS from every vertex."""
    adjacency = [[] for _ in range(n)]
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    result = []
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        queue = deque([s])
        while queue:
            v = queue.popleft()
            for u in adjacency[v]:
                if dist[u] == -1:
                    dist[u] = dist[v] + 1
                    queue.append(u)
        result.append(dist)
    return result


def main():
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]
    assert sum_of_distances(6, edges) == [8, 8, 10, 12, 12, 14]
    assert height_from_every_root(6, edges) == [2, 3, 3, 4, 4, 4]
    assert sum_of_distances(1, []) == [0] and height_from_every_root(1, []) == [0]
    assert sum_of_distances(0, []) == []
    n = 5000  # long path: no recursion
    assert sum_of_distances(n, [(i, i + 1) for i in range(n - 1)])[0] == n * (n - 1) // 2
    star = [(0, i) for i in range(1, 2000)]  # one vertex with 1999 children
    assert height_from_every_root(2000, star) == [1] + [2] * 1999

    rng = random.Random(4)
    for _ in range(300):
        n = rng.randint(1, 30)
        labels = list(range(n))
        rng.shuffle(labels)
        e = [(labels[i], labels[rng.randrange(i)]) for i in range(1, n)]
        dist = all_distances(n, e)
        assert sum_of_distances(n, e) == [sum(d) for d in dist]
        heights = height_from_every_root(n, e)
        assert heights == [max(d) for d in dist]
        # The centers (minimum height) are one vertex or two adjacent vertices.
        assert len([v for v in range(n) if heights[v] == min(heights)]) in (1, 2)


if __name__ == "__main__":
    main()
```

Both are O(n) time and space.

The classic bug is including `c`'s own contribution in `up[c]`: the path from `3` would go up to `1` and straight back down to `3`, counting a fake length.

## 5. DAG DP: longest path in topological order

A **DAG** is a directed graph with no directed cycle. Given edge weights (possibly negative) and a source `s`, find for every vertex the largest weight of a path from `s` to it.

Edges `0→1 (2)`, `0→2 (1)`, `1→3 (−5)`, `2→3 (4)`; vertex `4` has no edges.

```text
        2         -5
   0 ------> 1 ------> 3
    \                 ^
   1 \               / 4
      +----> 2 -----+
                              4 (alone)
```

The best path to `3` is `0 → 2 → 3`, weight 5; vertex `4` is unreachable. Enumerating paths is exponential (a chain of `k` diamonds has `2^k` paths).

**State and transition.** `best[v]` = the largest weight of a path from `s` to `v`, or `-inf` if none. The last decision is the last edge `u → v`:

$$
best[v] = \max_{u \to v}\big(best[u] + w(u, v)\big), \qquad best[s] = 0.
$$

**Order.** Every predecessor must be final first: a **topological order**, where every edge goes from earlier to later. It exists exactly when the graph is acyclic. **Kahn's algorithm** builds it by repeatedly removing a vertex with no remaining incoming edges; leftover vertices lie on a cycle ([Topological Sort](../10-graphs/02-connectivity-and-ordering/02-topological-sort-and-scc.md)). Vertex numbers are **not** a topological order unless the problem promises it.

Negative edges are safe: with no cycles, no path can loop forever.

**Trace.** Indegrees `0:0, 1:1, 2:1, 3:2, 4:0`; Kahn's order is `[0, 4, 1, 2, 3]`. The code pushes from `u` to its successors, which is the same recurrence.

| Process | Updates | `best` after |
|---|---|---|
| start | `best[0] = 0` | `[0, −∞, −∞, −∞, −∞]` |
| 0 | `best[1] = 2`, `best[2] = 1` | `[0, 2, 1, −∞, −∞]` |
| 4 | unreachable, skip | same |
| 1 | `best[3] = 2 − 5 = −3` | `[0, 2, 1, −3, −∞]` |
| 2 | `best[3] = max(−3, 1 + 4) = 5` | `[0, 2, 1, 5, −∞]` |
| 3 | no outgoing edges | final |

The code for this section and the next is one script, at the end of §6. O(V + E) time and space. Check `best[target]` before following `previous`: `None` means "this is the source" only when `best` is finite.

**Variants.** Shortest path in a DAG: `min` and `inf`. Longest path **starting anywhere**: start every `best[v]` at 0. The longest **simple** path in a graph with cycles is NP-hard; with no topological order, this DP does not apply. Shortest paths with cycles belong to [Graphs](../10-graphs/README.md).

## 6. Counting paths in a DAG

Count the paths from `s` to `t`. Edges `0→1`, `0→2`, `1→2`, `1→3`, `2→3`, `s = 0`, `t = 3`: the paths are `0-1-3`, `0-1-2-3`, `0-2-3`, so 3.

Each path to `v` has exactly one last edge `u → v`, and different last edges give different paths. The cases are disjoint and complete, so add them:

$$
ways[v] = \sum_{u \to v} ways[u], \qquad ways[s] = 1.
$$

Why is the base 1? The empty path from `s` to itself is one path. Unreachable vertices stay 0, which is right for counting; `-inf` is not needed.

| Vertex (topological order) | Incoming | `ways` |
|---|---|---|
| 0 | — | 1 |
| 1 | from 0 | 1 |
| 2 | from 0, 1 | 1 + 1 = 2 |
| 3 | from 1, 2 | 1 + 2 = 3 |

```python
import random
from collections import deque
from math import inf


def topological_order(n: int, adjacency: list[list[tuple[int, int]]]) -> list[int]:
    """Kahn's algorithm. adjacency[u] holds (v, weight) pairs."""
    indegree = [0] * n
    for u in range(n):
        for v, _ in adjacency[u]:
            indegree[v] += 1
    queue = deque(v for v in range(n) if indegree[v] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v, _ in adjacency[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    if len(order) != n:
        raise ValueError("graph must be acyclic")
    return order


def build(n: int, edges: list[tuple[int, int, int]]) -> list[list[tuple[int, int]]]:
    adjacency = [[] for _ in range(n)]
    for u, v, w in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("invalid edge endpoint")
        adjacency[u].append((v, w))
    return adjacency


def dag_longest_paths(n: int, edges: list[tuple[int, int, int]], source: int):
    if not (0 <= source < n):
        raise ValueError("source must be a vertex")
    adjacency = build(n, edges)
    best = [-inf] * n
    previous = [None] * n
    best[source] = 0
    for u in topological_order(n, adjacency):
        if best[u] == -inf:
            continue
        for v, w in adjacency[u]:  # push to successors
            if best[u] + w > best[v]:
                best[v] = best[u] + w
                previous[v] = u
    return best, previous


def path_to(best, previous, target):
    if best[target] == -inf:
        return None  # unreachable: do not follow pointers
    path = []
    while target is not None:
        path.append(target)
        target = previous[target]
    return path[::-1]


def count_paths(n: int, edges: list[tuple[int, int]], source: int, target: int,
                mod: int | None = None) -> int:
    if not (0 <= source < n and 0 <= target < n):
        raise ValueError("source and target must be vertices")
    adjacency = build(n, [(u, v, 0) for u, v in edges])
    ways = [0] * n
    ways[source] = 1
    for u in topological_order(n, adjacency):
        for v, _ in adjacency[u]:  # parallel edges count as different paths
            ways[v] += ways[u]
            if mod is not None:
                ways[v] %= mod
    return ways[target]


def all_paths(n, edges, source):
    """Brute force: (end vertex, total weight) of every path from source."""
    out = [[] for _ in range(n)]
    for u, v, w in edges:
        out[u].append((v, w))
    stack = [(source, 0)]
    while stack:
        u, total = stack.pop()
        yield u, total
        stack.extend((v, total + w) for v, w in out[u])


def main():
    edges = [(0, 1, 2), (0, 2, 1), (1, 3, -5), (2, 3, 4)]
    best, previous = dag_longest_paths(5, edges, 0)
    assert best == [0, 2, 1, 5, -inf]
    assert path_to(best, previous, 3) == [0, 2, 3] and path_to(best, previous, 4) is None
    assert dag_longest_paths(1, [], 0)[0] == [0]
    for bad in (lambda: dag_longest_paths(2, [(0, 1, 1), (1, 0, 1)], 0),
                lambda: count_paths(2, [(0, 1), (1, 0)], 0, 1)):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("a cycle must be rejected")

    simple = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
    assert count_paths(4, simple, 0, 3) == 3 and count_paths(4, simple, 3, 0) == 0
    assert count_paths(1, [], 0, 0) == 1 and count_paths(2, [(0, 1), (0, 1)], 0, 1) == 2
    diamonds = []  # 60 diamonds in a row: 2**60 paths, far too many to list
    for k in range(60):
        a, b, c, d = 3 * k, 3 * k + 1, 3 * k + 2, 3 * k + 3
        diamonds += [(a, b), (a, c), (b, d), (c, d)]
    assert count_paths(181, diamonds, 0, 180) == 2 ** 60
    assert count_paths(181, diamonds, 0, 180, mod=10**9 + 7) == pow(2, 60, 10**9 + 7)

    rng = random.Random(6)
    for _ in range(300):
        n = rng.randint(1, 8)
        labels = list(range(n))
        rng.shuffle(labels)  # hide the order: labels are not topological
        e = [(labels[i], labels[j], rng.randint(-5, 5))
             for i in range(n) for j in range(i + 1, n) if rng.random() < 0.4]
        s, t = rng.randrange(n), rng.randrange(n)
        paths = list(all_paths(n, e, s))
        best, previous = dag_longest_paths(n, e, s)
        assert best == [max((w for v, w in paths if v == x), default=-inf) for x in range(n)]
        assert count_paths(n, [(u, v) for u, v, _ in e], s, t) == sum(v == t for v, _ in paths)
        weight = {}
        for u, v, w in e:
            weight[(u, v)] = max(weight.get((u, v), -inf), w)
        for x in range(n):
            path = path_to(best, previous, x)
            if path is not None:
                assert path[0] == s and path[-1] == x
                assert sum(weight[p] for p in zip(path, path[1:])) == best[x]


if __name__ == "__main__":
    main()
```

O(V + E) arithmetic operations. Counts grow to hundreds of digits, so problems usually ask for them modulo a prime such as `10**9 + 7`; the `mod` parameter does that.

## 7. Longest increasing path in a matrix: a hidden DAG

Find the longest path in a grid that moves up, down, left or right through **strictly increasing** values.

```text
7 8 9
6 1 2
5 4 3
```

The spiral `1 → 2 → … → 9` has length 9.

**Where is the DAG?** Make each cell a vertex with an edge to each **larger** neighbor. Values strictly increase along every edge, so no path returns to its start: the graph is a DAG, implicit in the grid. A path also never revisits a cell, so no "visited" set is needed. Brute-force DFS over all increasing paths is exponential.

**State.** `length[r][c]` = the number of cells in the longest increasing path **starting** at `(r, c)`:

$$
length[r][c] = 1 + \max\big(0,\ \max_{\text{neighbor } (r', c') \text{ with larger value}} length[r'][c']\big).
$$

The answer is the maximum over all cells. Two orders work:

1. **Memoized DFS.** Quickest to write, but recursion depth can reach `rows × cols` and crash Python on large grids.
2. **Sort by value, largest first.** Every larger neighbor is already finished, so sorting by value *is* a topological order. Equal values are never connected, so ties can come in any order.

**Trace** on `[[5, 4], [1, 2]]` by decreasing value:

| Cell (value) | Larger neighbors | `length` |
|---|---|---|
| (0,0) = 5 | — | 1 |
| (0,1) = 4 | 5 | 1 + 1 = 2 |
| (1,1) = 2 | 4 | 1 + 2 = 3 |
| (1,0) = 1 | 5, 2 | 1 + max(1, 3) = **4** |

The best path is `1 → 2 → 4 → 5`.

```python
import random
from functools import cache


def check(grid: list[list[int]]) -> tuple[int, int]:
    if not grid or not grid[0]:
        return 0, 0
    cols = len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), cols


STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def longest_increasing_path_memo(grid: list[list[int]]) -> int:
    rows, cols = check(grid)

    @cache
    def length(r: int, c: int) -> int:
        best = 0
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] > grid[r][c]:
                best = max(best, length(nr, nc))
        return 1 + best

    return max((length(r, c) for r in range(rows) for c in range(cols)), default=0)


def longest_increasing_path_sorted(grid: list[list[int]]) -> int:
    rows, cols = check(grid)
    length = [[1] * cols for _ in range(rows)]
    cells = sorted(((grid[r][c], r, c) for r in range(rows) for c in range(cols)), reverse=True)
    for value, r, c in cells:  # larger values are finished first
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] > value:
                length[r][c] = max(length[r][c], 1 + length[nr][nc])
    return max((max(row) for row in length), default=0)


def brute_force(grid):
    rows, cols = check(grid)
    best = 0
    stack = [(r, c, 1) for r in range(rows) for c in range(cols)]
    while stack:
        r, c, k = stack.pop()
        best = max(best, k)
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] > grid[r][c]:
                stack.append((nr, nc, k + 1))
    return best


def main():
    spiral = [[7, 8, 9], [6, 1, 2], [5, 4, 3]]
    for solve in (longest_increasing_path_memo, longest_increasing_path_sorted):
        assert solve(spiral) == 9
        assert solve([[5, 4], [1, 2]]) == 4
        assert solve([[1, 1], [1, 1]]) == 1
        assert solve([]) == 0
    # A 200 x 200 snake visits all 40000 cells in increasing order: the bottom-up
    # version handles it, while the recursive one would exceed the recursion limit.
    n = 200
    snake = [[r * n + (c if r % 2 == 0 else n - 1 - c) for c in range(n)] for r in range(n)]
    assert longest_increasing_path_sorted(snake) == n * n

    rng = random.Random(9)
    for _ in range(300):
        rows, cols = rng.randint(1, 4), rng.randint(1, 4)
        grid = [[rng.randint(0, 6) for _ in range(cols)] for _ in range(rows)]
        expected = brute_force(grid)
        assert longest_increasing_path_memo(grid) == expected
        assert longest_increasing_path_sorted(grid) == expected


if __name__ == "__main__":
    main()
```

Memoized DFS: O(rows · cols) time. Sorted: O(rows · cols · log(rows · cols)) for the sort. Both use O(rows · cols) space.

If the problem allowed **non-decreasing** paths, equal neighbors would form cycles, the graph would stop being a DAG, and the memoized version would recurse forever between two equal cells.

## 8. Summary: evaluation order and the rerooting template

Every DP here solves smaller pieces first; what "smaller" means depends on the shape.

| DP family | Smaller subproblem | Evaluation order | Typical mistake |
|---|---|---|---|
| Interval ([chapter 7](07-interval-dp.md)) | Shorter interval | Increasing length | Reading a longer interval before it is filled |
| Tree | Child subtree | Postorder (reversed BFS order) | Combining subtrees that share an edge |
| Rerooting | Down summaries, then up summaries | Postorder pass, then preorder pass | Including the receiving child's own contribution in `up` |
| DAG | Predecessor vertex | Topological order | Treating vertex numbers as a topological order |
| Implicit DAG (grid by value) | Larger-valued neighbor | Decreasing value, or memoized DFS | Allowing equal values, which creates cycles |

**Rerooting template.**

1. **Down pass** (postorder): `down[v]` summarizes `v`'s subtree from its children.
2. **Up pass** (preorder): `up[c]` summarizes everything outside `c`'s subtree from `up[v]` and `c`'s siblings; use prefix/suffix arrays to exclude `c` when the combine has no inverse.
3. **Combine:** the answer at `v` merges `up[v]` with all child contributions.

When unsure about order, draw the dependency arrows of a few states. A tree: leaves first. A DAG: topological order. A cycle: the state is wrong, or the problem is not a plain DP.

## 9. Pitfalls and practice

1. **Recursion depth.** A path-shaped tree or a long increasing chain overflows Python's recursion limit. Use reversed BFS order or sort-by-value when inputs can be large.
2. **Trusting the input to be a tree.** Check `n − 1` edges and connectivity; a hidden cycle silently breaks the independence of subtrees.
3. **Forgetting the parent in an undirected adjacency list.** Skip the parent when walking from `v`, or the "child" loop goes back up.
4. **Reconstruction without the parent's status.** In the independent set, carry "was my parent chosen?" down.
5. **Diameter with one branch only.** The longest path through `v` uses the top **two** depths from **different** children.
6. **Double counting in rerooting.** `up[c]` must exclude `c`'s own contribution.
7. **Numeric order is not topological order.** Compute one unless edges are guaranteed to go from smaller to larger labels.
8. **`-inf` vs 0.** Longest path from a fixed source starts unreachable vertices at `-inf`; counting starts them at 0; "start anywhere" starts everything at 0.
9. **Following predecessor pointers from an unreachable vertex.** Check `best[target]` first.
10. **Non-strict comparisons in implicit DAGs.** A "≤" relation creates cycles among equal values.

Practice: House Robber III, Binary Tree Maximum Path Sum, Diameter of Binary Tree, Diameter of N-Ary Tree, Sum of Distances in Tree, Minimum Height Trees, Count Number of Possible Root Nodes, Maximum Price Difference Between Max and Min Price Sum, Binary Tree Cameras, Distribute Coins in Binary Tree, Longest Increasing Path in a Matrix, Number of Increasing Paths in a Grid, Parallel Courses III, Longest Path With Different Adjacent Characters, All Paths From Source to Target.

Next: [Bitmask DP](09-bitmask-dp.md).
