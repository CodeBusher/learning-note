# Depth-First Search — Go Deep, Then Back Up

## 1. Reach everything in one pass

Which vertices can be reached from vertex 0?

```text
    0 ─── 1 ─── 3            adj[0] = [1, 2]
    │     │                  adj[1] = [0, 3, 4]
    │     │                  adj[2] = [0, 4]
    2 ─── 4      5 ─── 6     adj[3] = [1]
                             adj[4] = [1, 2]
                             adj[5] = [6]
                             adj[6] = [5]
```

The scanning method of [What a Graph Is](01-what-a-graph-is.md#6-a-slow-but-honest-answer-to-what-can-i-reach) answers this in O(V · E) because it re-reads edges whose work is done. A vertex's edges only matter once, right after the vertex is first reached.

**Depth-first search (DFS)** acts on that. Mark the start. From the current vertex, take any edge to an **unmarked** vertex, mark it, and continue from there. When every neighbor of the current vertex is marked, the vertex is **finished**: step back to the vertex you came from and continue its list. The chain of vertices from the start to the current one is the **path**; stepping back pops its last vertex.

Trace from 0, neighbors tried in list order:

| Step | At | Look at neighbor | Action | Path | Visited |
|---:|---:|---|---|---|---|
| 1 | 0 | | enter 0 | 0 | {0} |
| 2 | 0 | 1 (new) | go to 1 | 0 1 | {0,1} |
| 3 | 1 | 0 (seen) | skip | 0 1 | {0,1} |
| 4 | 1 | 3 (new) | go to 3 | 0 1 3 | {0,1,3} |
| 5 | 3 | 1 (seen) | 3 finished, back up | 0 1 | {0,1,3} |
| 6 | 1 | 4 (new) | go to 4 | 0 1 4 | {0,1,3,4} |
| 7 | 4 | 1 (seen) | skip | 0 1 4 | {0,1,3,4} |
| 8 | 4 | 2 (new) | go to 2 | 0 1 4 2 | {0,1,2,3,4} |
| 9 | 2 | 0, 4 (seen) | 2 finished, back up | 0 1 4 | |
| 10 | 4 | none left | 4 finished, back up | 0 1 | |
| 11 | 1 | none left | 1 finished, back up | 0 | |
| 12 | 0 | 2 (seen) | 0 finished | (empty) | {0,1,2,3,4} |

DFS **entered** vertices in the order `0, 1, 3, 4, 2` and **finished** them in the order `3, 2, 4, 1, 0`. Vertices 5 and 6 were never reached. At step 8 DFS reached 2 by the route `0, 1, 4, 2` although the edge `0 – 2` exists: DFS finds *a* path, not the shortest one. That is [Breadth-First Search](03-bfs.md)'s job.

Each vertex is entered once (it is marked) and each adjacency list is read once, so DFS costs O(V + E).

On a **tree** there are no cycles, so DFS needs no visited set beyond "don't go back to the parent", and entry and finish order are the preorder and postorder of [tree traversal](../../03-trees/01-binary-trees-and-traversals.md). On a general graph, the visited marks are what keep DFS from walking around a cycle forever.

## 2. Three ways to write it

### 2.1 Recursive

Entering a vertex is a function call; backing up is a return (`dfs_recursive` in the script below). The catch is depth. Python stops at about 1000 nested calls with `RecursionError`, and a chain `0 – 1 – … – 4999` needs 5000. Raising the limit with `sys.setrecursionlimit` can crash the interpreter instead. So this folder uses recursion only when the depth is known to be small.

### 2.2 Explicit stack, marking when pushed

Replace the call stack with a list: mark `start` and push it; pop a vertex `u`; mark and push each unmarked neighbor; repeat until the stack is empty.

| Step | Pop | Pushed (and marked) | Stack after (top right) |
|---:|---:|---|---|
| 0 | | start | [0] |
| 1 | 0 | 1, 2 | [1, 2] |
| 2 | 2 | 4 | [1, 4] |
| 3 | 4 | none | [1] |
| 4 | 1 | 3 | [3] |
| 5 | 3 | none | [] |

The visit order is `0, 2, 4, 1, 3`, not the recursive `0, 1, 3, 4, 2`, but the reached set is the same, and marking on push keeps each vertex on the stack at most once. For **reachability** this is all you need. It is not a faithful DFS, though: vertex 4 was claimed by 2 rather than by 1, and no vertex ever "finishes". Anything that needs finishing order (topological sort, strongly connected components, bridges) can't use it.

### 2.3 Explicit stack of frames: an exact copy of the recursion

A recursive call remembers two things: its vertex and how far it has got through that vertex's neighbor list. A Python iterator over `adj[u]` remembers its position, so store the **frame** `(u, iter(adj[u]))`.

1. Mark `start`, record it as entered, push `(start, iter(adj[start]))`.
2. Ask the top frame's iterator for its next neighbor `v`.
   - `v` unmarked: mark it, record it as entered, push `(v, iter(adj[v]))`. (A call.)
   - `v` marked: do nothing; the loop returns to the same frame.
   - no neighbors left: `u` is finished; pop the frame. (A return.)

This performs exactly the steps of the §1 table, with no depth limit. Every DFS in this folder that needs finishing order uses it. The script also records each vertex's `parent` and its entry and finish times `tin`/`tout`, used in §5 and §8.

```python
import random
import sys


def dfs_recursive(adj, start):
    visited = [False] * len(adj)
    order = []

    def go(u):
        visited[u] = True
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                go(v)

    go(start)
    return order


def dfs_stack(adj, start):
    """Reachability with a plain stack; marks on push. Visit order differs from recursion."""
    if not 0 <= start < len(adj):
        raise ValueError("start out of range")
    visited = [False] * len(adj)
    visited[start] = True
    stack, order = [start], []
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                stack.append(v)
    return order


def dfs_frames(adj, start):
    """Exact recursive DFS without recursion.

    Returns (enter order, finish order, parent, tin, tout); tin/tout use one shared clock
    and are -1 for vertices that were not reached.
    """
    n = len(adj)
    if not 0 <= start < n:
        raise ValueError("start out of range")
    parent, tin, tout = [-1] * n, [-1] * n, [-1] * n
    enter, finish = [start], []
    tin[start], clock = 0, 1
    frames = [(start, iter(adj[start]))]
    while frames:
        u, neighbors = frames[-1]
        v = next(neighbors, None)  # None when the list is used up
        if v is None:  # u finishes: a return
            frames.pop()
            finish.append(u)
            tout[u], clock = clock, clock + 1
        elif tin[v] == -1:  # unvisited: a call
            parent[v] = u
            enter.append(v)
            tin[v], clock = clock, clock + 1
            frames.append((v, iter(adj[v])))
    return enter, finish, parent, tin, tout


def path_to(parent, tin, start, target):
    """Follow parents back from target; [] if target was not reached."""
    if tin[target] == -1:
        return []
    path = [target]
    while path[-1] != start:
        path.append(parent[path[-1]])
    return path[::-1]


def reachable_by_scanning(n, edges, source):
    """The brute force from What a Graph Is, undirected."""
    reached, changed = {source}, True
    while changed:
        changed = False
        for u, v in edges:
            if (u in reached) != (v in reached):
                reached.update((u, v))
                changed = True
    return reached


def build(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def main():
    adj = [[1, 2], [0, 3, 4], [0, 4], [1], [1, 2], [6], [5]]
    enter, finish, parent, tin, tout = dfs_frames(adj, 0)
    assert dfs_recursive(adj, 0) == enter == [0, 1, 3, 4, 2]
    assert finish == [3, 2, 4, 1, 0]
    assert dfs_stack(adj, 0) == [0, 2, 4, 1, 3]
    assert path_to(parent, tin, 0, 2) == [0, 1, 4, 2]  # valid, not the shortest
    assert path_to(parent, tin, 0, 6) == []
    assert tin == [0, 1, 5, 2, 4, -1, -1] and tout == [9, 8, 6, 3, 7, -1, -1]
    assert dfs_frames([[]], 0)[:2] == ([0], [0])

    rng = random.Random(1)
    for _ in range(300):
        n = rng.randint(1, 9)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 12))]
        adj = build(n, edges)
        s = rng.randrange(n)
        expected = reachable_by_scanning(n, edges, s)
        enter, finish, parent, tin, tout = dfs_frames(adj, s)
        assert set(dfs_stack(adj, s)) == set(finish) == expected
        assert enter == dfs_recursive(adj, s)
        for t in range(n):
            path = path_to(parent, tin, s, t)
            assert bool(path) == (t in expected)
            assert len(set(path)) == len(path)  # simple
            assert all(b in adj[a] for a, b in zip(path, path[1:]))
        for a in expected:  # parenthesis property: nested or disjoint, never crossing
            for b in expected:
                if tin[a] < tin[b]:
                    assert tout[b] < tout[a] or tout[a] < tin[b]

    # A 5000-vertex chain: recursion fails, the explicit stacks do not.
    chain = build(5000, [(i, i + 1) for i in range(4999)])
    assert len(dfs_frames(chain, 0)[0]) == len(dfs_stack(chain, 0)) == 5000
    if sys.getrecursionlimit() < 5000:
        try:
            dfs_recursive(chain, 0)
        except RecursionError:
            pass
        else:
            raise AssertionError("expected RecursionError")


if __name__ == "__main__":
    main()
```

**Time** O(V + E); **space** O(V) for the marks and the stack (at most V frames or vertices).

**Why it's correct.** A vertex is marked only when reached by an edge from a marked vertex, so nothing unreachable is marked. Conversely, suppose a reachable `w` stays unmarked. On a path from `start` to `w`, let `y` be the first unmarked vertex and `x` the marked one before it. Every marked vertex has its whole list examined, so `y` was found from `x` and marked: a contradiction.

## 3. Variant: connected components

**Problem.** Split an undirected graph into connected components. For the §1 graph: `{0, 1, 2, 3, 4}` and `{5, 6}`.

One DFS from `s` marks exactly the component of `s`. Loop over all vertices; each one still unmarked starts a new DFS with a new id. Marks are never cleared, so each vertex and edge is handled once in total.

| Outer loop at | Labeled? | Action | `comp` for 0..6 |
|---:|---|---|---|
| 0 | no | DFS with id 0 marks 0, 1, 2, 3, 4 | 0 0 0 0 0 −1 −1 |
| 1–4 | yes | skip | |
| 5 | no | DFS with id 1 marks 5, 6 | 0 0 0 0 0 1 1 |


O(V + E) time, O(V) extra space; `component_labels` is in the script of §4.

On a **directed** graph this loop gives a DFS forest, not components: 0 reaching 1 says nothing about 1 reaching 0. Mutually reachable groups are **strongly connected components**, in [Topological Sort and SCCs](../02-connectivity-and-ordering/02-topological-sort-and-scc.md).

## 4. Variant: flood fill and number of islands

**Problem.** A grid of `1` (land) and `0` (water). An **island** is a group of land cells joined through shared sides, not corners. Count the islands.

```text
      c0 c1 c2 c3
r0  [  1  1  0  0 ]
r1  [  1  0  0  1 ]
r2  [  0  0  1  1 ]
r3  [  1  0  0  0 ]
```

The answer is 3: `(0,0) (0,1) (1,0)`; `(1,3) (2,3) (2,2)` (2,2 touches 1,3 only diagonally but is joined through 2,3); and `(3,0)`. This is §3 on the implicit grid graph of [What a Graph Is](01-what-a-graph-is.md#5-grids-are-graphs-you-never-build). The DFS that marks one island is a **flood fill**, after the paint-bucket tool.

| Scan reaches | Land and unseen? | Flood fill marks | Islands |
|---|---|---|---:|
| (0,0) | yes | (0,0), (0,1), (1,0) | 1 |
| (1,3) | yes | (1,3), (2,3), (2,2) | 2 |
| (3,0) | yes | (3,0) | 3 |

```python
import random

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def component_labels(adj):
    """comp[v] = id of v's component, ids 0, 1, ... in order of first vertex."""
    n = len(adj)
    comp = [-1] * n
    count = 0
    for s in range(n):
        if comp[s] != -1:
            continue
        comp[s] = count
        stack = [s]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if comp[v] == -1:
                    comp[v] = count
                    stack.append(v)
        count += 1
    return comp, count


def count_islands(grid):
    """Rectangular 0/1 grid, 4-neighbor connectivity. The input is not modified."""
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")
    seen = [[False] * cols for _ in range(rows)]
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 1 or seen[r][c]:
                continue
            islands += 1
            seen[r][c] = True
            stack = [(r, c)]
            while stack:
                x, y = stack.pop()
                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < rows and 0 <= ny < cols
                            and grid[nx][ny] == 1 and not seen[nx][ny]):
                        seen[nx][ny] = True
                        stack.append((nx, ny))
    return islands


def islands_by_relabeling(grid):
    """Brute force: every land cell starts with its own label; repeatedly take the
    smallest label among land neighbors until nothing changes."""
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    label = {(r, c): r * cols + c for r in range(rows) for c in range(cols) if grid[r][c] == 1}
    changed = True
    while changed:
        changed = False
        for (r, c), value in list(label.items()):
            for dr, dc in DIRS:
                other = label.get((r + dr, c + dc))
                if other is not None and other < label[(r, c)]:
                    label[(r, c)] = other
                    changed = True
    return len(set(label.values()))


def main():
    grid = [[1, 1, 0, 0],
            [1, 0, 0, 1],
            [0, 0, 1, 1],
            [1, 0, 0, 0]]
    assert count_islands(grid) == 3
    assert count_islands([[1, 0], [0, 1]]) == 2  # corners do not join
    assert count_islands([]) == 0
    assert count_islands([[]]) == 0
    assert count_islands([[0, 0]]) == 0

    rng = random.Random(3)
    for _ in range(300):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        g = [[int(rng.random() < 0.5) for _ in range(cols)] for _ in range(rows)]
        assert count_islands(g) == islands_by_relabeling(g)

    adj = [[1, 2], [0, 3, 4], [0, 4], [1], [1, 2], [6], [5]]
    assert component_labels(adj) == ([0, 0, 0, 0, 0, 1, 1], 2)
    assert component_labels([]) == ([], 0)
    assert component_labels([[], [], []]) == ([0, 1, 2], 3)
    for _ in range(300):  # components against min-label relaxation over the edges
        n = rng.randint(1, 9)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 10))]
        adj = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        label = list(range(n))
        for _ in range(n):
            for u, v in edges:
                label[u] = label[v] = min(label[u], label[v])
        comp, count = component_labels(adj)
        assert count == len(set(label))
        assert all((comp[a] == comp[b]) == (label[a] == label[b]) for a in range(n) for b in range(n))

    big = [[1] * 300 for _ in range(300)]  # 90,000 cells in one island: no recursion
    assert count_islands(big) == 1


if __name__ == "__main__":
    main()
```

O(RC) time and space for an `R × C` grid. Overwriting visited land with `0` instead of keeping `seen` saves memory but destroys the caller's grid. A recursive flood fill on the 300 × 300 test would nest up to 90,000 calls.

Variants: largest island **area** (count cells per fill); recolor one region; **8-direction** islands (eight offsets); **closed islands** and **enclaves** (first flood-fill everything touching the border, then count what remains).

## 5. Variant: recovering the path

To report *how* to reach `t`, record `parent[v] = u` when DFS first reaches `v` from `u`. Follow parents from `t` back to the start and reverse. From the §1 trace, `parent[1] = 0`, `parent[3] = 1`, `parent[4] = 1`, `parent[2] = 4`:

```text
2 → 4 → 1 → 0 (start)      reversed: [0, 1, 4, 2]
```

The parent links form the **DFS tree** rooted at the start. Each vertex has one parent, so the path is **simple** (no repeated vertex), but not the shortest: three edges where one would do. `path_to` in the §2.3 script does this and is tested on random graphs. To stop early, end the loop as soon as the target is marked; the worst case stays O(V + E).

## 6. Cycles in an undirected graph

**Problem.** Does an undirected graph contain a cycle, and where? The §1 graph does: `0, 1, 4, 2, 0`.

**Brute force.** A graph with no cycle is a **forest** (a collection of trees), and a tree on `k` vertices has `k − 1` edges. So a cycle exists exactly when `E > V − C`, with `C` components. That detects a cycle but doesn't locate it.

**Key observation.** Run the frame DFS. An edge `u – v` to an already-visited `v` is either the edge we arrived on, seen from the other end, or an extra edge that closes a cycle.

On the §1 graph, every visited neighbor met at steps 3, 5 and 7 of the trace is the vertex we arrived from, over the edge we arrived on: ignore. The first exception is at 2, whose neighbor 0 is visited and is **not** the arrival edge (that was `4 – 2`): a cycle. Walk parents from 2 up to 0: `2, 4, 1, 0`.

The visited vertex is always an **ancestor** (still on the path), so walking parents reaches it. Why? If `v` were already finished, its whole list, including `u`, was examined while `v` was active, so `u` would have been entered below `v`, making `v` an ancestor of `u` after all. In undirected DFS every non-tree edge joins a vertex to an ancestor.

**Parallel edges.** With two edges between 0 and 1, the second one is a real cycle of length 2, but "ignore the parent **vertex**" skips it. Give each edge an id and ignore only the **edge** we arrived on. A self-loop `u – u` then shows up as an edge to a visited vertex with a different id: a cycle of length 1.

```python
import random


def find_undirected_cycle(n, edges):
    """Return the vertices of some cycle (in order), or None. Allows parallel edges and self-loops."""
    adj = [[] for _ in range(n)]
    for eid, (u, v) in enumerate(edges):
        adj[u].append((v, eid))
        if u != v:
            adj[v].append((u, eid))
    parent = [-1] * n
    parent_edge = [-1] * n
    visited = [False] * n
    for root in range(n):
        if visited[root]:
            continue
        visited[root] = True
        frames = [(root, iter(adj[root]))]
        while frames:
            u, neighbors = frames[-1]
            item = next(neighbors, None)
            if item is None:
                frames.pop()
                continue
            v, eid = item
            if eid == parent_edge[u]:
                continue  # the edge we arrived on
            if visited[v]:  # v is an ancestor of u (or u itself)
                cycle = [u]
                while cycle[-1] != v:
                    cycle.append(parent[cycle[-1]])
                return cycle
            visited[v] = True
            parent[v], parent_edge[v] = u, eid
            frames.append((v, iter(adj[v])))
    return None


def is_valid_cycle(cycle, edges):
    if len(cycle) == 1:
        return (cycle[0], cycle[0]) in edges
    if len(set(cycle)) != len(cycle):
        return False
    counts = {}
    for u, v in edges:
        key = (min(u, v), max(u, v))
        counts[key] = counts.get(key, 0) + 1
    needed = {}
    for a, b in zip(cycle, cycle[1:] + cycle[:1]):
        key = (min(a, b), max(a, b))
        needed[key] = needed.get(key, 0) + 1
    return all(counts.get(k, 0) >= c for k, c in needed.items())


def has_cycle_by_counting(n, edges):
    """Brute force: a forest has exactly V - C edges."""
    comp = list(range(n))
    changed = True
    while changed:  # label every vertex with the smallest vertex in its component
        changed = False
        for u, v in edges:
            low = min(comp[u], comp[v])
            if comp[u] != low or comp[v] != low:
                comp[u] = comp[v] = low
                changed = True
    return len(edges) > n - len(set(comp))


def main():
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (5, 6)]
    assert find_undirected_cycle(7, edges) == [2, 4, 1, 0]
    assert find_undirected_cycle(4, [(0, 1), (1, 2), (1, 3)]) is None
    assert find_undirected_cycle(2, [(0, 1), (0, 1)]) == [1, 0]  # parallel edges
    assert find_undirected_cycle(1, [(0, 0)]) == [0]  # self-loop
    assert find_undirected_cycle(0, []) is None

    rng = random.Random(5)
    for _ in range(500):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 8))]
        cycle = find_undirected_cycle(n, edges)
        assert (cycle is not None) == has_cycle_by_counting(n, edges)
        if cycle is not None:
            assert is_valid_cycle(cycle, edges)


if __name__ == "__main__":
    main()
```

O(V + E) time and space; it stops at the first cycle.

## 7. Cycles in a directed graph

**Problem.** Does a directed graph have a directed cycle? A prerequisite list "A needs B, B needs C, C needs A" can never be satisfied.

"Visited and not the arrival edge" fails here. In the diamond below, DFS from 0 visits 1, 3, backs up, visits 2, and from 2 sees the visited 3, yet both arrows point down into 3 and there is no cycle.

```text
      0
     ↙ ↘
    1   2
     ↘ ↙
      3
```

**Key observation.** Split "visited" into three colors:

- **white**: not entered yet;
- **gray**: entered, not finished, so on the current path;
- **black**: finished; everything reachable from it is explored.

An arrow `u → v` into a **gray** `v` closes a cycle: the path runs from `v` down to `u`. An arrow into a **black** `v` cannot: if `v` could reach `u`, DFS would have entered `u` while `v` was gray, and `u` would have finished first; but `u` is still active while `v` is done. So **a directed graph has a cycle if and only if DFS finds an arrow to a gray vertex.**

Trace on the diamond plus the arrow `3 → 1` (`0: [1, 2]`, `1: [3]`, `2: [3]`, `3: [1]`):

| Step | Action | Gray path | Colors 0 1 2 3 |
|---:|---|---|---|
| 1 | enter 0 | 0 | G W W W |
| 2 | 0 → 1 white: enter | 0 1 | G G W W |
| 3 | 1 → 3 white: enter | 0 1 3 | G G W G |
| 4 | 3 → 1 **gray** | 0 1 3 | cycle 1, 3 |

Without `3 → 1`, step 4 finishes 3 and then 1 (black); 0 → 2 enters 2, and 2 → 3 meets a **black** vertex, correctly ignored.

```python
import random


def find_directed_cycle(adj):
    """Return the vertices of a directed cycle in order, or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    n = len(adj)
    color = [WHITE] * n
    parent = [-1] * n
    for root in range(n):
        if color[root] != WHITE:
            continue
        color[root] = GRAY
        frames = [(root, iter(adj[root]))]
        while frames:
            u, neighbors = frames[-1]
            v = next(neighbors, None)
            if v is None:
                color[u] = BLACK
                frames.pop()
            elif color[v] == GRAY:  # arrow back onto the current path
                cycle = [u]
                while cycle[-1] != v:
                    cycle.append(parent[cycle[-1]])
                return cycle[::-1]
            elif color[v] == WHITE:
                color[v] = GRAY
                parent[v] = u
                frames.append((v, iter(adj[v])))
    return None


def has_cycle_brute(adj):
    """Some arrow u -> v where u is reachable from v (by repeated scanning)."""
    n = len(adj)
    arrows = [(u, v) for u in range(n) for v in adj[u]]
    for u, v in arrows:
        reached, changed = {v}, True
        while changed:
            changed = False
            for a, b in arrows:
                if a in reached and b not in reached:
                    reached.add(b)
                    changed = True
        if u in reached:
            return True
    return False


def main():
    diamond = [[1, 2], [3], [3], []]
    assert find_directed_cycle(diamond) is None
    assert find_directed_cycle([[1, 2], [3], [3], [1]]) == [1, 3]
    assert find_directed_cycle([[0]]) == [0]  # self-loop
    assert find_directed_cycle([]) is None
    assert find_directed_cycle([[1], [2], [0]]) == [0, 1, 2]

    rng = random.Random(6)
    for _ in range(500):
        n = rng.randint(1, 7)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 10)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        cycle = find_directed_cycle(adj)
        assert (cycle is not None) == has_cycle_brute(adj)
        if cycle is not None:
            assert len(set(cycle)) == len(cycle)
            for a, b in zip(cycle, cycle[1:] + cycle[:1]):
                assert b in adj[a]


if __name__ == "__main__":
    main()
```

O(V + E) time, O(V) extra space.

**Why every cycle is found.** Let `v` be the first vertex of a cycle that DFS enters. The rest of the cycle is white then, and while `v` stays gray DFS enters every white vertex reachable from `v`, including the cycle vertex `u` with the arrow `u → v`. When `u` examines that arrow, `v` is still gray.

## 8. Entry and exit times

The frame DFS of §2.3 stamps each vertex with a shared clock when it is entered (`tin`) and when it finishes (`tout`). On the §1 graph:

| Vertex | 0 | 1 | 3 | 4 | 2 |
|---|---:|---:|---:|---:|---:|
| `tin` | 0 | 1 | 2 | 4 | 5 |
| `tout` | 9 | 8 | 3 | 7 | 6 |

As brackets on a timeline they nest like parentheses:

```text
time:  0  1  2  3  4  5  6  7  8  9
       (0 (1 (3 3) (4 (2 2) 4) 1) 0)
```

**Parenthesis property:** two intervals `[tin, tout]` are either nested (one vertex is an ancestor of the other in the DFS tree) or disjoint; the §2.3 script checks it on random graphs. Three later algorithms rest on it:

- **Topological sort** lists vertices by decreasing `tout` ([Topological Sort and SCCs](../02-connectivity-and-ordering/02-topological-sort-and-scc.md#3-topological-order-from-dfs-finishing-times)).
- **Bridges and articulation points** compare `tin` values to ask whether a subtree has another way up ([Bridges and Articulation Points](../02-connectivity-and-ordering/03-bridges-and-articulation.md)).
- **Subtree queries** turn "the subtree of `v`" into the `tin` range from `tin[v]` to `tout[v]` ([Rooting a Tree and LCA](../05-trees-and-advanced/01-rooting-and-lca.md)).

## 9. Summary

| Need | DFS form | Key detail |
|---|---|---|
| Reachability, components, flood fill | Plain stack (§2.2) | Mark on push; loop over every unmarked start |
| Some path to `t` | Frames + `parent` (§5) | Simple, not shortest |
| Undirected cycle | Frames + edge ids (§6) | Skip only the arrival **edge** |
| Directed cycle | Frames + three colors (§7) | Arrow to **gray** = cycle; black is harmless |
| Finishing order, `tin`/`tout` | Frames (§2.3, §8) | Intervals nest like parentheses |

All run in O(V + E) time and O(V) extra space.

## 10. Pitfalls and practice

1. Marking when popped instead of when pushed in the plain stack. A vertex can then sit on the stack many times, up to O(E) entries.
2. Recursion on inputs deeper than about 1000: a long path or a big grid region. Use frames.
3. Expecting DFS to find shortest paths. It finds *a* path.
4. Detecting directed cycles with one visited flag. The diamond revisits 3 with no cycle.
5. "Visited and not the parent vertex" for undirected cycles when parallel edges are possible. Compare edge ids.
6. Starting from one vertex when the question is about the whole graph. Loop over every unvisited vertex.
7. The plain stack (§2.2) where finishing order matters. It has no finishing moment.

Practice: number of islands; max area of island; flood fill; number of connected components in an undirected graph; graph valid tree; find if path exists in graph; surrounded regions; number of closed islands; keys and rooms; course schedule (three colors).

Next: [Breadth-First Search](03-bfs.md).
