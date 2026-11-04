# Bridges and Articulation Points — Single Points of Failure

## 1. Which cable must not break?

Eight servers are joined by cables (undirected edges), each with an id:

```text
        0                      e0: 0–1   e4: 3–4
       / \                     e1: 1–2   e5: 4–5
      1 ─ 2                    e2: 2–0   e6: 5–6
      |                        e3: 1–3   e7: 6–4
      3
      |
      4
     / \
    5 ─ 6
```

If a single cable fails, does the network split? Cable `1–3` is critical: without it, `{0, 1, 2}` cannot talk to `{3, 4, 5, 6}`. So is `3–4`. But any cable inside the triangle `0, 1, 2` can fail safely, because the other two edges of the triangle still connect its ends, and likewise for the triangle `4, 5, 6`.

An edge whose removal increases the number of connected components is a **bridge**. A vertex whose removal (together with its edges) increases the number of components is an **articulation point** (or **cut vertex**). Here the bridges are `1–3` and `3–4`, and the articulation points are 1, 3, and 4. Removing 1 cuts off `{0, 2}`; removing 3 separates the two halves; removing 4 cuts off `{5, 6}`.

**Brute force.** For each edge, delete it, count components with a DFS, and put it back. That is `E` searches of O(V + E) each: O(E · (V + E)). Articulation points the same way: O(V · (V + E)). With 10⁵ edges, that is around 10¹⁰ steps.

| Edge removed | e0 | e1 | e2 | e3 | e4 | e5 | e6 | e7 |
|---|---|---|---|---|---|---|---|---|
| Components after | 1 | 1 | 1 | **2** | **2** | 1 | 1 | 1 |

## 2. The key observation: look at the DFS tree

Run DFS from vertex 0. The edges it walks along to discover new vertices form the **DFS tree**; the others are **non-tree edges**. [Depth-First Search §6](../01-search-and-traversal/02-dfs.md#6-cycles-in-an-undirected-graph) showed that in an undirected graph every non-tree edge joins a vertex to one of its **ancestors** in the DFS tree. We call those **back edges**. There are no edges "sideways" between separate branches.

For the example (neighbors tried in the order the edges are listed), DFS walks `0 → 1 → 2`, backs up to 1, then walks `1 → 3 → 4 → 5 → 6`:

```text
    DFS tree              back edges
       0
       |
       1
      / \
     2   3                2 ⇢ 0
         |
         4
         |
         5
         |
         6                6 ⇢ 4
```

Now ask when a tree edge `p – v` (with `p` the parent) can be a bridge. Delete it. The subtree below `v` is still attached to the rest **only** through back edges, and every back edge from inside that subtree goes to an ancestor of its endpoint. So:

> The tree edge `p – v` is a bridge **exactly when no back edge goes from `v`'s subtree to `p` or anything above `p`.**

Non-tree edges are never bridges: each one lies on a cycle (itself plus the tree path between its ends).

In the example, the subtree of 2 is `{2}`, and its back edge `2 ⇢ 0` jumps above 1, so `1 – 2` is not a bridge. The subtree of 3 is `{3, 4, 5, 6}`; its only back edge `6 ⇢ 4` stays inside, so `1 – 3` is a bridge.

## 3. Measuring "how high can a subtree reach"

Give every vertex its DFS entry time `tin[v]` ([entry and exit times](../01-search-and-traversal/02-dfs.md#8-entry-and-exit-times)): 0 for the first vertex entered, 1 for the next, and so on. Ancestors always have smaller `tin` than their descendants. Then define

$$
\text{low}[v] = \min\Big(\text{tin}[v],\ \min \{\text{tin}[a] : \text{a back edge goes from } v\text{'s subtree to } a\}\Big).
$$

In words: the earliest-entered vertex that `v`'s subtree can reach using any number of tree edges downward and then **one** back edge. It is computed during the DFS with three rules:

- On entering `v`: `low[v] = tin[v]`.
- Back edge `v ⇢ a` (a visited neighbor, not through the edge we arrived on): `low[v] = min(low[v], tin[a])`.
- When a tree child `c` of `v` finishes: `low[v] = min(low[v], low[c])`. The child's subtree is part of `v`'s subtree.

Trace on the example, showing only steps that change `low` or test an edge (each vertex also skips the edge it arrived on):

| Step | Event | `low` change | Test when the child finishes |
|---:|---|---|---|
| 1 | enter 0, 1, 2 (tin 0, 1, 2) | | |
| 2 | at 2: back edge e2 to 0 | low[2] = min(2, 0) = **0** | |
| 3 | 2 finishes | low[1] = min(1, 0) = **0** | low[2] = 0 > tin[1] = 1? no: `1–2` not a bridge |
| 4 | enter 3, 4, 5, 6 (tin 3, 4, 5, 6) | | |
| 5 | at 6: back edge e7 to 4 | low[6] = min(6, 4) = **4** | |
| 6 | 6 finishes | low[5] = 4 | low[6] = 4 > tin[5] = 5? no |
| 7 | 5 finishes | low[4] = min(4, 4) = 4 | low[5] = 4 > tin[4] = 4? no |
| 8 | at 4: e7 down to 6, already visited | low[4] = min(4, tin 6) = 4, no change | |
| 9 | 4 finishes | low[3] = min(3, 4) = 3 | low[4] = 4 > tin[3] = 3? **yes: `3–4` is a bridge** |
| 10 | 3 finishes | low[1] = min(0, 3) = 0 | low[3] = 3 > tin[1] = 1? **yes: `1–3` is a bridge** |
| 11 | 1 finishes | low[0] = 0 | low[1] = 0 > tin[0] = 0? no |

Final table:

| v | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tin` | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| `low` | 0 | 0 | 0 | 3 | 4 | 4 | 4 |

Step 8 looks at an edge to a **descendant** (from 4 down to 6). It is the same edge as the back edge `6 ⇢ 4`, seen from the top. Using `tin[6]` there never lowers `low[4]`, because a descendant's `tin` is larger, so it does no harm.

The order matters: `low[v]` is only final after **all** of `v`'s children have finished. That is why the code uses the stack of frames from [Depth-First Search §2.3](../01-search-and-traversal/02-dfs.md#23-explicit-stack-of-frames-an-exact-copy-of-the-recursion), which has a real "finish" moment.

## 4. The bridge rule

For a tree edge `p – v`, with `p` the parent:

$$
p\text{–}v \text{ is a bridge} \iff \text{low}[v] > \text{tin}[p].
$$

**Why.** `low[v] > tin[p]` says that the highest vertex `v`'s subtree can reach by a back edge was entered **after** `p`. Every ancestor of `p`, and `p` itself, was entered at or before `tin[p]`. So no back edge leaves the subtree toward `p` or above, and by §2 the edge is a bridge. Conversely, if `low[v] ≤ tin[p]`, some back edge from the subtree lands on `p` or an ancestor of `p`, giving a second route around the edge.

Why strict `>`? Equality, `low[v] = tin[p]`, means a back edge from the subtree lands **on `p` itself**. Then the subtree has two separate connections to `p` (the tree edge and the back edge), so the tree edge is safe. In the example, DFS walked `0 → 1 → 2` and found the back edge `2 ⇢ 0`, so `low[1] = 0 = tin[0]` for the tree edge `0 – 1`. That edge is correctly not a bridge (the route `0, 2, 1` replaces it). Using `≥` would wrongly call it one.

## 5. The articulation point rules

**A non-root vertex `p`** is an articulation point if it has **some** tree child `v` with

$$
\text{low}[v] \ge \text{tin}[p].
$$

Deleting `p` removes `p` itself, so a back edge that lands exactly on `p` no longer helps. The subtree of `v` must reach **strictly above** `p` to stay attached. Hence `≥` here, versus `>` for bridges. In the example: vertex 4 has child 5 with `low[5] = 4 ≥ tin[4] = 4`, so 4 is an articulation point even though no edge at 4 is a bridge: removing 4 leaves `5 – 6` stranded with only edges back to 4.

**The root** has no vertex above it, so the rule above would always fire. Instead: **the root is an articulation point exactly when it has two or more tree children.** Different children of the root are in separate branches, and undirected DFS has no edges between separate branches; so with two children, removing the root separates them. With one child, everything else hangs below that child and stays connected.

```text
root 0 with two children          root 0 with one child
      0                                 0
     / \       removing 0              /         removing 0 leaves
    1   2      splits {1} and {2}     1 ─ 2      1 – 2 connected
```

In the example, root 0 has one tree child (1), so it is not an articulation point. Vertex 1 has child 3 with `low[3] = 3 ≥ tin[1] = 1`, and vertex 3 has child 4 with `low[4] = 4 ≥ tin[3] = 3`: both are articulation points.

## 6. Parallel edges and self-loops

If two cables both join `u` and `v`, neither is a bridge: each is a backup for the other. The common shortcut "skip the neighbor that is my parent **vertex**" would skip **both** copies, missing the backup, and report a bridge that isn't one.

The fix is to give each edge an id, and when standing at `v`, skip only the **specific edge** we arrived on (`parent_edge[v]`). The second copy is then treated as a back edge to the parent, which sets `low[v] ≤ tin[p]` and correctly cancels the bridge.

A self-loop `u – u` never connects anything new, so it is never a bridge and never matters for articulation. With edge ids it shows up as an edge to the visited vertex `u` itself; `min(low[u], tin[u])` changes nothing. It is harmless.

## 7. The code

```python
import random


def bridges_and_articulation_points(n, edges):
    """Undirected edges as (u, v) pairs. Return (set of bridge edge ids, set of articulation vertices).

    Parallel edges, self-loops, isolated vertices, and several components are allowed.
    """
    adj = [[] for _ in range(n)]
    for eid, (u, v) in enumerate(edges):
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("vertex out of range")
        adj[u].append((v, eid))
        adj[v].append((u, eid))
    tin, low = [-1] * n, [0] * n
    parent, parent_edge, children = [-1] * n, [-1] * n, [0] * n
    timer = 0
    bridges, cut_vertices = set(), set()

    for root in range(n):
        if tin[root] != -1:
            continue
        tin[root] = low[root] = timer
        timer += 1
        frames = [(root, iter(adj[root]))]
        while frames:
            v, neighbors = frames[-1]
            item = next(neighbors, None)
            if item is None:  # v finishes: report to its parent
                frames.pop()
                p = parent[v]
                if p == -1:
                    if children[v] >= 2:
                        cut_vertices.add(v)
                else:
                    low[p] = min(low[p], low[v])
                    if low[v] > tin[p]:
                        bridges.add(parent_edge[v])
                    if parent[p] != -1 and low[v] >= tin[p]:
                        cut_vertices.add(p)
                continue
            w, eid = item
            if eid == parent_edge[v]:
                continue  # the edge we arrived on
            if tin[w] == -1:  # tree edge
                parent[w], parent_edge[w] = v, eid
                children[v] += 1
                tin[w] = low[w] = timer
                timer += 1
                frames.append((w, iter(adj[w])))
            else:  # back edge (or the same back edge seen from the ancestor's side)
                low[v] = min(low[v], tin[w])
    return bridges, cut_vertices


def bridge_tree(n, edges):
    """Return (group id per vertex, list of tree edges between group ids)."""
    bridges, _ = bridges_and_articulation_points(n, edges)
    adj = [[] for _ in range(n)]
    for eid, (u, v) in enumerate(edges):
        if eid not in bridges:
            adj[u].append(v)
            adj[v].append(u)
    group, count = [-1] * n, 0
    for s in range(n):
        if group[s] != -1:
            continue
        group[s] = count
        stack = [s]
        while stack:
            for v in adj[stack.pop()]:
                if group[v] == -1:
                    group[v] = count
                    stack.append(v)
        count += 1
    tree = sorted((min(group[u], group[v]), max(group[u], group[v]))
                  for eid, (u, v) in enumerate(edges) if eid in bridges)
    return group, tree


def connected(n, edges, a, b):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    seen, stack = {a}, [a]
    while stack:
        for v in adj[stack.pop()]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return b in seen


def count_components(n, edges, removed_vertex=None):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    alive = n - (removed_vertex is not None)
    for u, v in edges:
        if removed_vertex in (u, v):
            continue
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            alive -= 1
    return alive


def brute_force(n, edges):
    base = count_components(n, edges)
    bridges = {i for i in range(len(edges))
               if count_components(n, edges[:i] + edges[i + 1:]) > base}
    base_without = lambda x: base - 1 if not any(x in e for e in edges) else base
    cut = {x for x in range(n) if count_components(n, edges, removed_vertex=x) > base_without(x)}
    return bridges, cut


def main():
    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 5), (5, 6), (6, 4)]
    assert bridges_and_articulation_points(7, edges) == ({3, 4}, {1, 3, 4})
    assert bridges_and_articulation_points(2, [(0, 1), (0, 1)]) == (set(), set())  # parallel
    assert bridges_and_articulation_points(3, [(0, 1), (0, 2)]) == ({0, 1}, {0})  # root, 2 children
    assert bridges_and_articulation_points(3, [(0, 1), (1, 2), (2, 0)]) == (set(), set())
    assert bridges_and_articulation_points(1, [(0, 0)]) == (set(), set())  # self-loop
    assert bridges_and_articulation_points(0, []) == (set(), set())

    rng = random.Random(41)
    for _ in range(600):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 11))]
        assert bridges_and_articulation_points(n, edges) == brute_force(n, edges)

    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 5), (5, 6), (6, 4)]
    group, tree = bridge_tree(7, edges)
    assert group == [0, 0, 0, 1, 2, 2, 2] and tree == [(0, 1), (1, 2)]

    rng = random.Random(42)
    for _ in range(300):
        n = rng.randint(1, 7)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 10))]
        group, tree = bridge_tree(n, edges)
        assert len(set(tree)) == len(tree)  # at most one bridge between two groups
        for a in range(n):
            for b in range(a + 1, n):
                same = connected(n, edges, a, b) and all(
                    connected(n, edges[:i] + edges[i + 1:], a, b) for i in range(len(edges)))
                assert (group[a] == group[b]) == same

    path = [(i, i + 1) for i in range(19999)]  # 20,000-deep DFS, no recursion
    bridges, cut = bridges_and_articulation_points(20000, path)
    assert len(bridges) == 19999 and len(cut) == 19998


if __name__ == "__main__":
    main()
```

In the brute force, removing an isolated vertex lowers the component count by one, so the comparison uses the count that removal "should" give. Isolated vertices are never articulation points.

**Cost.** One DFS: each vertex is entered once and each edge is examined twice (once from each end). O(V + E) time; O(V + E) space for the adjacency list, and O(V) for the arrays and frames.

## 8. Two-edge-connected components and the bridge tree

Delete every bridge. What remains falls apart into groups called **2-edge-connected components**: inside one group, any single edge can fail and the group stays connected. In the example, the groups are `{0, 1, 2}`, `{3}`, and `{4, 5, 6}`.

Squash each group into one vertex and keep the bridges between them. The result has no cycles, because any cycle would contain no bridge, so it is a forest, called the **bridge tree**:

```text
   {0,1,2} ── e3 ── {3} ── e4 ── {4,5,6}
```

Questions like "how many cables must fail before `a` and `b` lose contact, if one is not enough?" or "which edges lie on every route from `a` to `b`?" become questions about paths in this tree: the bridges on the tree path between their groups.

**Brute-force check.** Two vertices are in the same 2-edge-connected component exactly when they stay connected after removing **any one** edge. (By Menger's theorem, that is the same as having two edge-disjoint paths.)

`bridge_tree` is in the §7 script: one bridge search plus one DFS over the non-bridge edges, O(V + E) time and space, tested against this check on random graphs.

## 9. Advanced: biconnected components

The vertex version of §8 groups **edges** rather than vertices. A **biconnected component** (or **block**) is a largest set of edges in which any two edges lie on a common simple cycle; a bridge forms a block by itself. Articulation points are exactly the vertices that belong to more than one block. In the example the blocks are the triangle `{e0, e1, e2}`, the bridge `{e3}`, the bridge `{e4}`, and the triangle `{e5, e6, e7}`; vertex 1 sits in two blocks, 3 in two, and 4 in two.

Blocks fall out of the same DFS with one extra stack, of **edges**:

- Push each tree edge when walking down it, and each back edge when it is first seen from the lower end (`tin[w] < tin[v]`).
- When a child `c` of `p` finishes with `low[c] ≥ tin[p]` (the articulation test, now applied to the root too), pop edges down to and including the tree edge `p – c`. Those edges are one block.

Why does this work? `low[c] ≥ tin[p]` says that the subtree of `c` hangs on `p` alone. The edges pushed since the tree edge `p – c`, minus blocks already removed deeper down, are exactly the edges of that hanging piece together with `p`.

**Brute-force check** (simple graphs): list every simple cycle, merge the edges of each cycle into one group, and leave every other edge alone.

```python
import random


def biconnected_components(n, edges):
    """Blocks of a graph without self-loops, as sorted lists of edge ids."""
    adj = [[] for _ in range(n)]
    for eid, (u, v) in enumerate(edges):
        if u == v:
            raise ValueError("self-loops are not supported")
        adj[u].append((v, eid))
        adj[v].append((u, eid))
    tin, low = [-1] * n, [0] * n
    parent, parent_edge = [-1] * n, [-1] * n
    timer, edge_stack, blocks = 0, [], []
    for root in range(n):
        if tin[root] != -1:
            continue
        tin[root] = low[root] = timer
        timer += 1
        frames = [(root, iter(adj[root]))]
        while frames:
            v, neighbors = frames[-1]
            item = next(neighbors, None)
            if item is None:
                frames.pop()
                p = parent[v]
                if p != -1:
                    low[p] = min(low[p], low[v])
                    if low[v] >= tin[p]:  # v's subtree hangs on p: pop one block
                        block = []
                        while True:
                            eid = edge_stack.pop()
                            block.append(eid)
                            if eid == parent_edge[v]:
                                break
                        blocks.append(sorted(block))
                continue
            w, eid = item
            if eid == parent_edge[v]:
                continue
            if tin[w] == -1:
                parent[w], parent_edge[w] = v, eid
                tin[w] = low[w] = timer
                timer += 1
                edge_stack.append(eid)
                frames.append((w, iter(adj[w])))
            elif tin[w] < tin[v]:  # back edge seen from below: push it once
                edge_stack.append(eid)
                low[v] = min(low[v], tin[w])
    return sorted(blocks)


def blocks_brute(n, edges):
    group = list(range(len(edges)))

    def find(x):
        while group[x] != x:
            x = group[x]
        return x

    adj = [[] for _ in range(n)]
    for eid, (u, v) in enumerate(edges):
        adj[u].append((v, eid))
        adj[v].append((u, eid))
    for s in range(n):  # cycles whose smallest vertex is s
        path_edges, on_path = [], {s}

        def walk(u):
            for w, eid in adj[u]:
                if w == s and len(path_edges) >= 2 and eid != path_edges[0]:
                    for other in path_edges:  # merge the whole cycle
                        group[find(other)] = find(eid)
                elif w > s and w not in on_path:
                    on_path.add(w)
                    path_edges.append(eid)
                    walk(w)
                    path_edges.pop()
                    on_path.remove(w)

        walk(s)
    result = {}
    for eid in range(len(edges)):
        result.setdefault(find(eid), []).append(eid)
    return sorted(result.values())


def main():
    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 5), (5, 6), (6, 4)]
    assert biconnected_components(7, edges) == [[0, 1, 2], [3], [4], [5, 6, 7]]
    assert biconnected_components(3, [(0, 1), (0, 2)]) == [[0], [1]]
    assert biconnected_components(2, []) == []

    rng = random.Random(43)
    for _ in range(300):
        n = rng.randint(2, 6)
        pairs = {tuple(sorted(rng.sample(range(n), 2))) for _ in range(rng.randint(0, 9))}
        edges = sorted(pairs)
        rng.shuffle(edges)
        assert biconnected_components(n, edges) == blocks_brute(n, edges)


if __name__ == "__main__":
    main()
```

O(V + E) time and space. Every edge is pushed once and popped once. The brute force is exponential in general (it lists all simple cycles) and only meant for graphs of a handful of vertices.

## 10. Summary

One DFS with `tin` and `low`, skipping only the edge we arrived on, answers all of these in O(V + E):

| Question | Test, for tree edge `p – v` (`p` the parent) | Why |
|---|---|---|
| Is `p – v` a bridge? | `low[v] > tin[p]` | A back edge landing on `p` is a detour around the edge |
| Is non-root `p` a cut vertex? | some child `v` with `low[v] ≥ tin[p]` | A back edge landing on `p` is lost when `p` is deleted |
| Is the root a cut vertex? | two or more tree children | Separate branches have no edges between them |
| 2-edge-connected components | components after deleting bridges | Contract them: the bridge tree |
| Blocks (biconnected components) | pop the edge stack when `low[v] ≥ tin[p]` | Includes the root |

`low[v]` is final only when all of `v`'s children have finished, which is why the code uses the frame DFS.

## 11. Pitfalls and practice

1. Using `≥` in the bridge test. Equality means a back edge lands on the parent itself, which is a valid detour.
2. Using `>` in the articulation test. For a vertex, a back edge that lands on it does not help once it is deleted.
3. Applying the non-root articulation rule to the DFS root. The root needs two or more tree children.
4. Skipping "the parent vertex" instead of "the parent edge". With parallel edges, the second copy is a real detour.
5. Updating `low[parent]` before the child's whole subtree is done. Propagate only when the child finishes.
6. Forgetting disconnected graphs. Start a DFS from every unvisited vertex; each start is its own root.
7. Recursion on large inputs. A path of 10⁵ vertices is a DFS 10⁵ deep; use frames.
8. Applying these rules to directed graphs. Bridges and cut vertices in directed graphs (with respect to strong connectivity) need different methods.

Practice: critical connections in a network; articulation points (cut vertices) of an undirected graph; minimum number of days to disconnect an island (the answer is 0, 1, or 2; a cut vertex means 1); find edges in every minimum spanning tree (bridges in a threshold graph); count bridges after adding edges online (bridge tree plus DSU); biconnected components.

Back to the [Connectivity and Ordering overview](README.md).
