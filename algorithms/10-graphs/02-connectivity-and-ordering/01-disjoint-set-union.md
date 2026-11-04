# Disjoint Set Union — Merging Groups as Edges Arrive

## 1. A problem that keeps changing

Six people, numbered 0 to 5, start as strangers. Events arrive one at a time. "Join" means two people become friends; friends of friends are in the same group. "Ask" means: are these two in the same group right now?

| # | Event | Groups after the event | Answer |
|---:|---|---|---|
| 1 | join 0, 1 | {0,1} {2} {3} {4} {5} | |
| 2 | join 2, 3 | {0,1} {2,3} {4} {5} | |
| 3 | ask 0, 3 | | no |
| 4 | join 0, 2 | {0,1,2,3} {4} {5} | |
| 5 | ask 1, 3 | | yes |
| 6 | join 4, 5 | {0,1,2,3} {4,5} | |
| 7 | join 3, 5 | {0,1,2,3,4,5} | |
| 8 | join 1, 4 | no change: already together | |

**Brute force.** Keep the edges and answer each "ask" with a [BFS or DFS](../01-search-and-traversal/README.md): O(V + q) per ask for `V` people and `q` events, O(q · (V + q)) in total, around 10¹⁰ steps for 100,000 of each.

A search rebuilds the whole group every time, yet groups only ever **merge**. So keep the groups themselves. They never overlap and cover everyone: a **partition** into **disjoint** sets. A **disjoint set union** (DSU, or **union–find**) stores a partition with two operations:

- `find(x)`: return a **representative** of `x`'s set, one fixed member that stands for the whole set. Two people are in the same set exactly when `find` gives the same representative.
- `union(a, b)`: merge the sets of `a` and `b`.

## 2. First try: a label per person

Store `label[x]`, the representative of `x`'s set. Then `find(x)` is one array read. To `union(a, b)`, relabel every person whose label equals `label[b]` to `label[a]`.

Trace the events (asks are only comparisons):

| Event | `label` for 0..5 | People relabeled |
|---|---|---:|
| start | 0 1 2 3 4 5 | |
| join 0, 1 | 0 0 2 3 4 5 | 1 |
| join 2, 3 | 0 0 2 2 4 5 | 1 |
| join 0, 2 | 0 0 0 0 4 5 | 2 |
| join 4, 5 | 0 0 0 0 4 4 | 1 |
| join 3, 5 | 0 0 0 0 0 0 | 2 |

Finding is instant, but every union scans the whole array to find who to relabel: O(V) per union. Building one group of V people takes V − 1 unions, so O(V²) in total. This is known as **quick-find**.

## 3. Second try: a forest of parent pointers

Instead of everyone pointing at the representative directly, let each person point at **some** member of their set, called their **parent**. Follow parents up until you reach someone who is their own parent: that is the **root**, and the root is the representative. Each set is then a tree, and the whole structure is a **forest**. The trees are bookkeeping only: a parent link does not have to be a friendship from the input.

- `find(x)`: walk up from `x` until `parent[r] == r`; return `r`.
- `union(a, b)`: find both roots; if they differ, make one root the parent of the other. Only one array entry changes.

Trace, always making `b`'s root a child of `a`'s root:

| Event | Roots found | Change | `parent` for 0..5 |
|---|---|---|---|
| start | | | 0 1 2 3 4 5 |
| join 0, 1 | 0, 1 | parent[1] = 0 | 0 0 2 3 4 5 |
| join 2, 3 | 2, 3 | parent[3] = 2 | 0 0 2 2 4 5 |
| join 0, 2 | 0, 2 | parent[2] = 0 | 0 0 0 2 4 5 |
| join 4, 5 | 4, 5 | parent[5] = 4 | 0 0 0 2 4 4 |
| join 3, 5 | 3 → 2 → 0; 5 → 4 | parent[4] = 0 | 0 0 0 2 0 4 |

```text
after the last join:        0
                          / | \
                         1  2  4
                            |  |
                            3  5
```

Union is now cheap, but `find` costs the **depth** of the vertex, the number of steps up to the root. Nothing stops the trees from getting tall. The sequence `join 1, 0`, `join 2, 1`, `join 3, 2`, … each time hangs the old root below the new person:

```text
join 1,0      join 2,1      join 3,2
   1             2             3
   |             |             |
   0             1             2
                 |             |
                 0             1
                               |
                               0
```

After V − 1 such joins, the tree is a chain, and `find(0)` takes V − 1 steps. This is **quick-union**, and its worst case is no better than quick-find.

## 4. Union by size: the smaller tree goes under

The chain happened because a big tree was hung below a single vertex. Fix that: keep `size[r]` for every root `r`, the number of people in its tree, and always hang the **smaller** tree's root below the **larger** tree's root. On a tie, either way works.

On the §1 events, every join but the last is a tie between equal sizes, and the last hangs root 4 (size 2) under root 0 (size 4): the same tree as in §3. And the chain-making sequence `join 1,0`, `join 2,1`, … now gives a star: each new single person is the smaller tree and goes under the existing root.

**Why the trees stay short.** Watch one vertex `x`. Its depth grows by one only when its root is hung below another root, and that happens only when `x`'s tree is the smaller one. Then the merged tree has at least **twice** as many people as `x`'s old tree. Starting from 1, the size of `x`'s tree can double at most log₂ V times before it exceeds V. So every depth is at most log₂ V, and `find` costs O(log V).

A common alternative, **union by rank**, keeps an upper bound on each tree's height instead of its size and hangs the lower-rank root below the higher. It gives the same O(log V) bound. Size is often more useful because problems frequently ask for group sizes anyway (§10).

## 5. Path compression: flatten while you walk

`find(x)` walks a path from `x` to the root. Every vertex on that path has the same root. Once we know it, we might as well point them all **directly** at the root, so the next `find` on any of them takes one step. This is **path compression**.

Start from the chain `parent = [0, 0, 1, 2, 3]` (4 → 3 → 2 → 1 → 0) and call `find(4)`.

**Full compression** (two passes): walk up once to find the root 0, then walk again and set each visited vertex's parent to 0.

```text
before: 4 → 3 → 2 → 1 → 0        parent = [0, 0, 1, 2, 3]
after:  4, 3, 2, 1 all → 0       parent = [0, 0, 0, 0, 0]
```

**Path halving** (one pass): while walking, point each visited vertex at its **grandparent**, then jump there.

| `x` | `parent[x]` becomes `parent[parent[x]]` | Jump to | `parent` |
|---:|---|---:|---|
| 4 | parent[4] = parent[3] = 2 | 2 | [0, 0, 1, 2, 2] |
| 2 | parent[2] = parent[1] = 0 | 0 | [0, 0, 0, 2, 2] |
| 0 | root | | |

Halving roughly halves the path each time, with no second pass and no extra memory.

**How fast is it?** With union by size and either form of compression, any sequence of `m` operations on `V` elements takes O(m · α(V)) time, where α is the **inverse Ackermann function**. It grows so slowly that α(V) ≤ 4 for any V that fits in the universe. The bound is **amortized**: a single `find` can still take several steps, but the total over the whole sequence is that small. The proof is long (Tarjan, 1975) and not needed to use the structure; the intuition is that compression and size balancing make paths collapse faster than unions can build them.

## 6. The complete structure

Put §4 and §5 together in a class `DSU(n)`: arrays `parent` and `size`, a `components` counter, `find(x)` with full path compression (walk up to the root, then walk again pointing each vertex at it), and `union(a, b)` that hangs the smaller root under the larger and returns `False` when `a` and `b` were already together. The class is in the script at the end of §8, next to the two problems that use it; its tests compare every answer with BFS on random operation sequences, and check that equal-size merges of 4096 elements, the fastest way union by size can grow depth, reach depth exactly log₂ 4096 = 12.

| Operation | Time | Space |
|---|---:|---:|
| Create `DSU(n)` | O(n) | O(n) |
| `find`, `union`, `connected`, `set_size` | O(α(n)) amortized | O(1) extra |
| `m` operations in total | O(n + m α(n)) | O(n) |

**Why it's correct.** The invariant is: *two elements have the same root if and only if they are in the same set*. It holds at the start, when everyone is their own root. `union` changes one root's parent to another root, so it merges exactly those two sets and leaves the others untouched. `find` with compression changes parents only to the root they already lead to, so no element changes set.

## 7. Number of provinces

**Problem.** `n` cities are given as an `n × n` matrix where `m[i][j] = 1` means cities `i` and `j` are directly connected. A **province** is a group of cities connected directly or indirectly. Count the provinces.

```text
      0 1 2
  0 [ 1 1 0 ]
  1 [ 1 1 0 ]        provinces: {0, 1} and {2}  →  2
  2 [ 0 0 1 ]
```

This is "count connected components", which DFS also solves. With a DSU: start with `n` components and union every connected pair; each successful union removes one. `find_circle_num` in the script of §8 does this in O(n² α(n)) time and O(n) space.

## 8. Redundant connection: the edge that closes a cycle

**Problem.** A tree on vertices `1..n` had one extra edge added, giving `n` edges. Return an edge whose removal leaves a tree; if several work, return the one that appears **last** in the input.

```text
edges: [1,2], [1,3], [2,3]        1
                                 / \
                                2 — 3        answer: [2, 3]
```

**Brute force.** Try removing each edge, from the last one backwards, and check whether the rest is a tree (connected with `n − 1` edges). That is `n` checks of O(n) each: O(n²).

**Key observation.** Add the edges one by one to a DSU. An edge whose two endpoints are **already connected** closes a cycle. A tree plus one edge has exactly one cycle, so exactly one edge fails to union, and it is the cycle's last edge in input order. Removing any cycle edge leaves a tree, so that last one is the answer.

| Edge | `find` of endpoints | Result |
|---|---|---|
| [1, 2] | 1, 2 | union |
| [1, 3] | 1, 3 | union |
| [2, 3] | 1, 1 | **already connected**: answer |

`find_redundant_connection` below takes O(n α(n)) time and O(n) space. The script holds the full `DSU` of §6, the one-pass `find_halving` of §5, both problems, and tests against BFS and against removing each edge in turn.

```python
import random
from collections import deque


class DSU:
    """Disjoint set union with union by size and full path compression."""

    def __init__(self, n):
        if n < 0:
            raise ValueError("n must be nonnegative")
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x):
        if not 0 <= x < len(self.parent):
            raise IndexError("element out of range")
        root = x
        while self.parent[root] != root:  # pass 1: find the root
            root = self.parent[root]
        while self.parent[x] != root:     # pass 2: point the path at it
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        """Merge the sets of a and b. Return False if they were already together."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)

    def set_size(self, x):
        return self.size[self.find(x)]


def find_halving(parent, x):
    """One-pass alternative: point each visited node at its grandparent."""
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def find_circle_num(m):
    """Number of provinces in an adjacency matrix (section 7)."""
    d = DSU(len(m))
    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            if m[i][j]:
                d.union(i, j)
    return d.components


def find_redundant_connection(edges):
    """Tree on 1..n plus one edge: the edge that closes the cycle (section 8)."""
    d = DSU(len(edges) + 1)  # vertices are 1..n; index 0 unused
    for u, v in edges:
        if not d.union(u, v):
            return [u, v]
    raise ValueError("no redundant edge: input is not a tree plus one edge")


def redundant_brute(edges):
    """Remove each edge, last first, until the rest is connected (n - 1 edges: a tree)."""
    n = len(edges)
    for i in range(n - 1, -1, -1):
        rest = edges[:i] + edges[i + 1:]
        if all(connected_by_bfs(n + 1, rest, 1, v) for v in range(2, n + 1)):
            return edges[i]
    raise ValueError("no answer")


def connected_by_bfs(n, edges, a, b):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    seen = {a}
    queue = deque([a])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return b in seen


def main():
    d = DSU(6)
    assert d.union(0, 1) and d.union(2, 3)
    assert not d.connected(0, 3)
    assert d.union(0, 2) and d.connected(1, 3)
    assert d.union(4, 5) and d.union(3, 5)
    assert not d.union(1, 4)  # already together
    assert d.components == 1 and d.set_size(5) == 6
    assert not d.union(2, 2)
    assert DSU(0).components == 0

    chain = [0, 0, 1, 2, 3]
    assert find_halving(chain, 4) == 0 and chain == [0, 0, 0, 2, 2]

    rng = random.Random(21)
    for _ in range(200):
        n = rng.randint(1, 10)
        d, edges = DSU(n), []
        for _ in range(rng.randint(0, 25)):
            a, b = rng.randrange(n), rng.randrange(n)
            if rng.random() < 0.5:
                was = connected_by_bfs(n, edges, a, b)
                assert d.union(a, b) == (not was)
                edges.append((a, b))
            else:
                assert d.connected(a, b) == connected_by_bfs(n, edges, a, b)
        roots = {d.find(x) for x in range(n)}
        assert d.components == len(roots)
        assert sum(d.size[r] for r in roots) == n

    assert find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]) == 2
    assert find_circle_num([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 3
    assert find_circle_num([]) == 0
    for _ in range(200):  # provinces against BFS from every city
        n = rng.randint(1, 8)
        m = [[int(i == j) for j in range(n)] for i in range(n)]
        for _ in range(rng.randint(0, n)):
            i, j = rng.randrange(n), rng.randrange(n)
            m[i][j] = m[j][i] = 1
        edges = [(i, j) for i in range(n) for j in range(n) if m[i][j]]
        groups = {frozenset(b for b in range(n) if connected_by_bfs(n, edges, a, b)) for a in range(n)}
        assert find_circle_num(m) == len(groups)

    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4]
    for _ in range(200):  # random tree plus one new edge, shuffled
        n = rng.randint(3, 9)
        edges = [[rng.randint(1, v - 1), v] for v in range(2, n + 1)]
        while True:
            u, v = sorted(rng.sample(range(1, n + 1), 2))
            if [u, v] not in edges and [v, u] not in edges:
                break
        edges.append([u, v])
        rng.shuffle(edges)
        assert find_redundant_connection(edges) == redundant_brute(edges)

    # Union by size alone keeps depth <= log2(n): check on a worst-case style sequence.
    n = 1 << 12
    parent, size = list(range(n)), [1] * n
    def root_depth(x):
        depth = 0
        while parent[x] != x:
            x, depth = parent[x], depth + 1
        return x, depth
    step = 1
    while step < n:  # merge equal-size pairs, which is where depth grows the most
        for i in range(0, n, 2 * step):
            ra, rb = root_depth(i)[0], root_depth(i + step)[0]
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]
        step *= 2
    assert max(root_depth(x)[1] for x in range(n)) == 12


if __name__ == "__main__":
    main()
```


The same "union fails" test detects a cycle in any undirected edge list, which is how Kruskal's algorithm skips edges in [Minimum Spanning Trees](../03-minimum-spanning-trees/README.md). A **directed** version of this problem (one vertex may end up with two parents) needs extra case analysis and is not solved by the plain test.

## 9. Accounts merge: union by shared keys

**Problem.** Each account is a name followed by email addresses. Two accounts belong to the same person if they share **any** email (sharing is transitive). Merge them and output each person's name with their sorted emails.

```text
["John", "a@x", "b@x"]
["John", "c@x"]                     →  ["John", "a@x", "b@x", "d@x"]
["John", "b@x", "d@x"]                 ["John", "c@x"]
["Mary", "m@x"]                        ["Mary", "m@x"]
```

Note that names alone mean nothing: two different Johns stay separate unless they share an email.

**Key observation.** Union the **accounts**, not the emails. Keep a dictionary `owner[email]` holding the first account seen with that email. Each later account containing the same email is unioned with that owner.

| Account | Emails | Action |
|---:|---|---|
| 0 | a, b | owner[a] = 0, owner[b] = 0 |
| 1 | c | owner[c] = 1 |
| 2 | b, d | b owned by 0: union(2, 0); owner[d] = 2 |
| 3 | m | owner[m] = 3 |

Roots at the end: {0, 2}, {1}, {3}. Collect each root's emails, sort them, and attach the name.

```python
import random
from collections import defaultdict


def accounts_merge(accounts):
    parent = list(range(len(accounts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for i, (_, *emails) in enumerate(accounts):
        for email in emails:
            if email in owner:
                parent[find(i)] = find(owner[email])
            else:
                owner[email] = i
    groups = defaultdict(set)
    for email, i in owner.items():
        groups[find(i)].add(email)
    return sorted([accounts[root][0]] + sorted(emails) for root, emails in groups.items())


def accounts_brute(accounts):
    """Graph of accounts joined by a shared email; DFS each component."""
    n = len(accounts)
    adj = [[j for j in range(n) if j != i and set(accounts[i][1:]) & set(accounts[j][1:])] for i in range(n)]
    seen, result = set(), []
    for s in range(n):
        if s in seen or len(accounts[s]) == 1:
            continue
        seen.add(s)
        stack, emails = [s], set()
        while stack:
            u = stack.pop()
            emails.update(accounts[u][1:])
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        result.append([accounts[s][0]] + sorted(emails))
    return sorted(result)


def main():
    accounts = [["John", "a@x", "b@x"], ["John", "c@x"], ["John", "b@x", "d@x"], ["Mary", "m@x"]]
    assert accounts_merge(accounts) == [["John", "a@x", "b@x", "d@x"], ["John", "c@x"], ["Mary", "m@x"]]
    assert accounts_merge([]) == []
    rng = random.Random(24)
    for _ in range(300):
        accounts = []
        for _ in range(rng.randint(1, 7)):
            emails = rng.sample([f"e{k}" for k in range(10)], rng.randint(1, 3))
            accounts.append(["P"] + emails)  # one name, so merged groups share it
        assert accounts_merge(accounts) == accounts_brute(accounts)


if __name__ == "__main__":
    main()
```

O(N α(N) + N log N) time for `N` total emails (the log comes from sorting the output), O(N) space. The same pattern, "first owner of each key, union later holders with it", solves similar-string grouping, merging intervals of shared IDs, and grouping by any shared attribute.

## 10. DSU with extra data

A root can carry information about its whole set. The rule is: **store set data only at roots, and combine it inside `union`**.

### 10.1 Sizes and the largest group

`size[root]` is already maintained. After each union, `size[new_root]` is the new set's size, so the **largest group so far** is a running maximum. Other per-set data works the same way: the minimum or maximum element, the sum of values, the number of edges inside the set (add one per edge, add both counts on a merge).

### 10.2 Parity: is the graph still two-colorable?

**Problem.** Edges arrive one by one. After each, report whether the graph can still be two-colored ([bipartite](../01-search-and-traversal/03-bfs.md#8-two-coloring-is-the-graph-bipartite)), and find the first edge that makes it impossible. Re-running BFS after every edge costs O(E · (V + E)).

**Key observation.** Within one set, the colors are fixed up to swapping. So store, for each element, one bit `parity[x]`: 0 if `x` has the same color as its parent, 1 if different. The color of `x` relative to its root is the XOR (sum mod 2) of the bits along the path. Path compression must keep this right: when `x` is re-pointed directly at the root, its new bit is the XOR of the whole old path.

An edge `a – b` demands `color(a) ≠ color(b)`, which is "parity of a XOR parity of b equals 1".

- Different roots: attach root `rb` under root `ra` with `parity[rb] = pa ⊕ pb ⊕ 1`, where `pa`, `pb` are the parities of `a`, `b` to their roots. Then `a` and `b` end up with different colors.
- Same root: the colors are already decided. If `pa ⊕ pb = 1`, fine. If 0, the edge joins two same-colored vertices: an odd cycle.

Trace on the triangle edges `0–1`, `1–2`, `2–0`:

| Edge | Roots, parities | Action | `parent`, `parity` (0..2) |
|---|---|---|---|
| start | | | [0,1,2], [0,0,0] |
| 0–1 | 0 (p 0), 1 (p 0) | attach 1 under 0, parity 0⊕0⊕1 = 1 | [0,0,2], [0,1,0] |
| 1–2 | 0 (p 1), 2 (p 0) | attach 2 under 0, parity 1⊕0⊕1 = 0 | [0,0,0], [0,1,0] |
| 2–0 | 0 (p 0), 0 (p 0) | same root, 0⊕0 = 0: **conflict** | |

Vertex 2 ended up with the same color as 0, and the edge 2–0 demands they differ.

### 10.3 Weighted DSU: ratios

**Problem (evaluate division).** Given facts like `a / b = 2` and `b / c = 3`, answer queries like `a / c` (6) or `c / a` (1/6), or report that a query can't be answered.

Store `weight[x]` meaning `x = weight[x] × parent[x]`. Along a path to the root, multiply. Then `x = w(x) × root`, where `w(x)` is the product. A query `a / b` with a common root is `w(a) / w(b)`. To record `a / b = k` with different roots `ra`, `rb`: from `a = w(a)·ra` and `b = w(b)·rb` and `a = k·b`, get `ra = (k · w(b) / w(a)) · rb`, so hang `ra` under `rb` with that weight. Parity in §10.2 is the same idea with XOR in place of multiplication.

```python
import random
from collections import deque
from fractions import Fraction


class ParityDSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.parity = [0] * n  # color relative to parent
        self.size = [1] * n

    def find(self, x):
        """Return (root, parity of x relative to root), compressing the path."""
        path = []
        while self.parent[x] != x:
            path.append(x)
            x = self.parent[x]
        root = x
        for node in reversed(path):  # nearest the root first
            p = self.parent[node]
            if p != root:
                self.parity[node] ^= self.parity[p]  # parity[p] is already relative to root
            self.parent[node] = root
        return root, (self.parity[path[0]] if path else 0)

    def add_edge(self, a, b):
        """Require different colors. Return False if this creates an odd cycle."""
        (ra, pa), (rb, pb) = self.find(a), self.find(b)
        if ra == rb:
            return pa != pb
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.parity[rb] = pa ^ pb ^ 1
        self.size[ra] += self.size[rb]
        return True


class RatioDSU:
    def __init__(self):
        self.parent, self.weight = {}, {}

    def find(self, x):
        """Return (root, w) with x = w * root."""
        path = []
        while self.parent[x] != x:
            path.append(x)
            x = self.parent[x]
        root = x
        for node in reversed(path):
            p = self.parent[node]
            if p != root:
                self.weight[node] *= self.weight[p]
            self.parent[node] = root
        return root, (self.weight[path[0]] if path else Fraction(1))

    def add(self, a, b, k):
        """Record a / b = k."""
        for x in (a, b):
            if x not in self.parent:
                self.parent[x], self.weight[x] = x, Fraction(1)
        (ra, wa), (rb, wb) = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb
            self.weight[ra] = k * wb / wa

    def query(self, a, b):
        if a not in self.parent or b not in self.parent:
            return None
        (ra, wa), (rb, wb) = self.find(a), self.find(b)
        return wa / wb if ra == rb else None


def bipartite_brute(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    color = [-1] * n
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return False
    return True


def ratio_brute(facts, a, b):
    adj = {}
    for x, y, k in facts:
        adj.setdefault(x, []).append((y, k))
        adj.setdefault(y, []).append((x, 1 / k))
    if a not in adj or b not in adj:
        return None
    value = {a: Fraction(1)}  # value[v] = a / v
    queue = deque([a])
    while queue:
        u = queue.popleft()
        for v, k in adj[u]:  # u / v = k
            if v not in value:
                value[v] = value[u] * k
                queue.append(v)
    return value.get(b)


def main():
    d = ParityDSU(3)
    assert d.add_edge(0, 1) and d.add_edge(1, 2)
    assert d.parent == [0, 0, 0] and d.parity == [0, 1, 0]
    assert not d.add_edge(2, 0)
    assert not ParityDSU(1).add_edge(0, 0)  # a self-loop is an odd cycle

    rng = random.Random(25)
    for _ in range(300):
        n = rng.randint(1, 8)
        d, edges = ParityDSU(n), []
        for _ in range(rng.randint(0, 12)):
            u, v = rng.randrange(n), rng.randrange(n)
            edges.append((u, v))
            ok = d.add_edge(u, v)
            assert ok == bipartite_brute(n, edges)
            if not ok:
                break  # after the first conflict the structure stops being meaningful

    r = RatioDSU()
    r.add("a", "b", Fraction(2))
    r.add("b", "c", Fraction(3))
    assert r.query("a", "c") == 6 and r.query("c", "a") == Fraction(1, 6)
    assert r.query("a", "a") == 1 and r.query("a", "x") is None
    for _ in range(300):
        names = [chr(ord("a") + i) for i in range(6)]
        value = {x: Fraction(rng.randint(1, 9)) for x in names}  # hidden consistent values
        r, facts = RatioDSU(), []
        for _ in range(rng.randint(0, 6)):
            x, y = rng.choice(names), rng.choice(names)
            facts.append((x, y, value[x] / value[y]))
            r.add(*facts[-1])
        x, y = rng.choice(names), rng.choice(names)
        assert r.query(x, y) == ratio_brute(facts, x, y)


if __name__ == "__main__":
    main()
```

Both run in O(α(n)) amortized per operation when union by size is used (`ParityDSU`), or O(log n) amortized with compression alone (`RatioDSU`). The tests use `Fraction` so that ratios compare exactly; with floats, compare with a tolerance.

## 11. Where DSU fits, and where it doesn't

DSU shines whenever groups only merge:

- **Kruskal's minimum spanning tree**: accept edges in increasing weight when their endpoints are in different sets ([Minimum Spanning Trees](../03-minimum-spanning-trees/README.md)).
- **Offline threshold queries**: "are `a` and `b` connected using only edges of weight ≤ `t`?" Sort edges and queries by weight; add edges up to each query's threshold, then answer.
- **Grids that fill in over time** (number of islands II): when a cell becomes land, add it as a new set and union it with land neighbors. Keep a separate count of land sets, since the DSU also holds water cells.
- **Deletions answered backwards**: if edges are only removed, process events in reverse, so removals become additions.

It cannot do everything:

- It does not **split** sets. Deleting edges online needs other tools; offline, a DSU **with rollback** (union by size, no path compression, and a stack of changes to undo) handles some insert-and-delete workloads.
- It knows **who** is together, not **how**: no paths, no distances.
- It is for **undirected** connectivity. Directed reachability and strongly connected components need DFS ([Topological Sort and SCCs](02-topological-sort-and-scc.md)).

## 12. Pitfalls and practice

1. Reading `size[x]` or other set data at a non-root. Always go through `find(x)` first.
2. Linking `parent[a] = b` instead of `parent[find(a)] = find(b)`. Linking non-roots silently splits trees and loses members.
3. Forgetting that a failed `union` (same root) must not change counts or sizes.
4. Recursive `find` on a deep tree before compression has had a chance to work. Use the iterative form.
5. Caching a root and using it after later unions: roots change. Call `find` again.
6. In parity or weighted DSU, compressing the path without updating the stored parity or weight.
7. One-based input with a 0-based array of size `n`: vertex `n` is out of range.
8. Using DSU for directed graphs. "Same set" ignores direction.

Practice: number of provinces; redundant connection; graph valid tree; number of connected components in an undirected graph; accounts merge; satisfiability of equality equations; smallest string with swaps; most stones removed with same row or column; number of islands II; evaluate division; is graph bipartite (with parity DSU); largest component size by common factor.

Next: [Topological Sort and Strongly Connected Components](02-topological-sort-and-scc.md).
