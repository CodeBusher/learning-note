# Maximum Flow and Bipartite Matching — Augmenting Paths (Advanced)

## 1. Water through pipes

A pumping station `s` (vertex 0) sends water to a reservoir `t` (vertex 5). Each one-way pipe has a **capacity**, the most liters per second it can carry:

```text
0 → 1 (10)    0 → 2 (10)
1 → 2 (2)     1 → 3 (4)     1 → 4 (8)
2 → 4 (9)
4 → 3 (6)
3 → 5 (10)    4 → 5 (10)
```

A **flow** assigns an amount to every pipe so that

- **capacity:** no pipe carries more than its capacity, and nothing negative;
- **conservation:** at every vertex other than `s` and `t`, water in equals water out.

The **value** of the flow is the total leaving `s` (equal to the total arriving at `t`). **Problem:** find the maximum value. The answer for this network is **19**.

## 2. Greedy paths are not enough

Flows are real-valued, so there is no finite list to brute-force. The natural greedy: find any route from `s` to `t` with spare capacity, push as much as it allows, repeat. It fails on a tiny network where every pipe has capacity 1:

```text
        a
      ↗ │ ↘
     s  │  t        s→a, s→b, a→b, a→t, b→t, all capacity 1
      ↘ ↓ ↗
        b
```

The maximum is 2 (`s→a→t` and `s→b→t`). But suppose the first route chosen is `s → a → b → t`. Push 1. Now `s→a`, `a→b` and `b→t` are full. The only spare pipes are `s→b` and `a→t`, and no route of spare pipes joins `s` to `t`. Greedy stops at 1.

The first route made a bad choice (`a→b`) that a later route would like to **take back**.

## 3. The residual graph: room to add, room to undo

The fix is to allow sending flow **backward** along a pipe that already carries flow, which means cancelling some of it. For the current flow `f`, build the **residual graph**:

- for each pipe `u → v`, a forward residual edge with capacity `cap(u, v) − f(u, v)` (room left);
- and a **reverse** residual edge `v → u` with capacity `f(u, v)` (amount that could be cancelled).

An **augmenting path** is a route from `s` to `t` in the residual graph using only edges with positive residual capacity. Pushing `b` units along it means: on forward edges, add `b` flow; on reverse edges, cancel `b` flow of the original pipe.

Back to the tiny network after the bad first route `s → a → b → t`:

| Residual edge | Capacity | Why |
|---|---:|---|
| `s → b` | 1 | unused |
| `b → a` | 1 | **reverse** of `a → b`, which carries 1 |
| `a → t` | 1 | unused |
| others | 0 | full, or nothing to cancel |

Augmenting path `s → b → a → t`. Pushing 1 along it adds flow on `s→b` and `a→t`, and **cancels** the flow on `a→b`. The result: `s→a→t` and `s→b→t`, each carrying 1. Value 2, the maximum. The reverse edge let the second route reroute the first.

## 4. Ford–Fulkerson and Edmonds–Karp

**Ford–Fulkerson method:** start with zero flow; while the residual graph has an augmenting path, push its **bottleneck** (smallest residual capacity on the path) along it.

**Edmonds–Karp** is the version that always picks a **shortest** augmenting path (fewest edges), found by BFS. That choice guarantees termination in O(V · E) augmentations, so **O(V · E²)** time in total, whatever the capacities.

### Trace on the pipe network

| Round | Shortest augmenting path (BFS) | Bottleneck | Total flow |
|---:|---|---:|---:|
| 1 | `0 → 1 → 3 → 5` | min(10, 4, 10) = 4 | 4 |
| 2 | `0 → 1 → 4 → 5` | min(10 − 4, 8, 10) = 6 | 10 |
| 3 | `0 → 2 → 4 → 5` | min(10, 9, 10 − 6) = 4 | 14 |
| 4 | `0 → 2 → 4 → 3 → 5` | min(10 − 4, 9 − 4, 6, 10 − 4) = 5 | 19 |
| 5 | none: BFS from 0 reaches only {0, 2} | — | 19 |

After round 4, pipe `0→1` has 0 spare (10 used), and from 2 the only pipe `2→4` has 0 spare (9 used). The search is stuck at `{0, 2}`.

## 5. The min-cut certificate

A **cut** splits the vertices into a side `S` containing `s` and a side `T` containing `t`. Its **capacity** is the total capacity of pipes going from `S` to `T` (pipes going back from `T` to `S` do not count).

Every unit of flow must cross from `S` to `T` at some point, so **any flow value ≤ any cut capacity.**

When Edmonds–Karp stops, let `S` be the vertices reachable from `s` in the residual graph. Here `S = {0, 2}` and `T = {1, 3, 4, 5}`. Pipes from `S` to `T`: `0→1` (10) and `2→4` (9), capacity **19**, equal to the flow. Since no flow can exceed this cut, 19 is optimal.

This is the **max-flow min-cut theorem**: the maximum flow value equals the minimum cut capacity. Proof sketch: at termination, every pipe from `S` to `T` is full (otherwise its head would be reachable), and every pipe from `T` to `S` is empty (otherwise its reverse edge would make its tail reachable). So the flow across the cut equals the cut's capacity exactly.

The min cut answers questions of its own: "the cheapest set of links to destroy so that `s` cannot reach `t`" is exactly a min cut.

```python
import random
from collections import deque
from itertools import combinations


class FlowNetwork:
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]
        self.to, self.cap = [], []

    def add_edge(self, u, v, capacity):
        """Edge i and its reverse i ^ 1 are stored next to each other."""
        if capacity < 0:
            raise ValueError("capacity must be nonnegative")
        self.adj[u].append(len(self.to))
        self.to.append(v)
        self.cap.append(capacity)
        self.adj[v].append(len(self.to))
        self.to.append(u)
        self.cap.append(0)

    def max_flow(self, s, t):
        """Edmonds-Karp. Returns (value, source side of a minimum cut)."""
        if s == t:
            raise ValueError("source and sink must differ")
        value = 0
        while True:
            via = [-1] * self.n  # edge index used to reach each vertex
            seen = [False] * self.n
            seen[s] = True
            queue = deque([s])
            while queue and not seen[t]:
                u = queue.popleft()
                for e in self.adj[u]:
                    v = self.to[e]
                    if self.cap[e] > 0 and not seen[v]:
                        seen[v] = True
                        via[v] = e
                        queue.append(v)
            if not seen[t]:
                return value, {v for v in range(self.n) if seen[v]}
            bottleneck = float("inf")
            v = t
            while v != s:
                e = via[v]
                bottleneck = min(bottleneck, self.cap[e])
                v = self.to[e ^ 1]
            v = t
            while v != s:
                e = via[v]
                self.cap[e] -= bottleneck
                self.cap[e ^ 1] += bottleneck
                v = self.to[e ^ 1]
            value += bottleneck


def min_cut_brute(n, edges, s, t):
    """Try every side S that contains s and not t."""
    others = [v for v in range(n) if v not in (s, t)]
    best = float("inf")
    for size in range(len(others) + 1):
        for extra in combinations(others, size):
            side = {s, *extra}
            best = min(best, sum(c for u, v, c in edges if u in side and v not in side))
    return best


def solve(n, edges, s, t):
    net = FlowNetwork(n)
    for u, v, c in edges:
        net.add_edge(u, v, c)
    return net.max_flow(s, t)


def main():
    pipes = [(0, 1, 10), (0, 2, 10), (1, 2, 2), (1, 3, 4), (1, 4, 8),
             (2, 4, 9), (3, 5, 10), (4, 3, 6), (4, 5, 10)]
    value, side = solve(6, pipes, 0, 5)
    assert value == 19 and side == {0, 2}
    assert sum(c for u, v, c in pipes if u in side and v not in side) == 19

    diamond = [(0, 1, 1), (0, 2, 1), (1, 2, 1), (1, 3, 1), (2, 3, 1)]
    assert solve(4, diamond, 0, 3)[0] == 2
    assert solve(3, [(0, 1, 5)], 0, 2) == (0, {0, 1})        # sink unreachable
    assert solve(2, [(0, 1, 3), (0, 1, 4), (1, 0, 9)], 0, 1)[0] == 7  # parallel edges

    rng = random.Random(29)
    for _ in range(400):
        n = rng.randint(2, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(0, 6))
                 for _ in range(rng.randint(0, 12))]
        edges = [(u, v, c) for u, v, c in edges if u != v]
        s, t = rng.sample(range(n), 2)
        value, side = solve(n, edges, s, t)
        assert value == min_cut_brute(n, edges, s, t)
        assert s in side and t not in side
        assert value == sum(c for u, v, c in edges if u in side and v not in side)


if __name__ == "__main__":
    main()
```

Time **O(V · E²)** for Edmonds–Karp; space O(V + E). With integer capacities, every flow value found is an integer, and so is every pipe's flow (the **integrality** property), which is what makes the matching reduction below work.

**Faster algorithms (advanced).** **Dinic's algorithm** runs BFS once to label vertices by distance, then pushes as much flow as possible along shortest paths at once with DFS (a *blocking flow*), and repeats. It runs in O(V² E) in general and O(E √V) on unit-capacity bipartite graphs, and is the usual contest choice. Push-relabel methods are another family. For **costs** on edges ("cheapest way to send `k` units"), use **min-cost flow**: repeatedly augment along a *cheapest* residual path (Bellman–Ford, or Dijkstra with potentials as in Johnson's algorithm).

## 6. Bipartite matching

Four workers and four jobs. Each worker is qualified for some jobs:

```text
worker 0: jobs 0, 1
worker 1: job 0
worker 2: jobs 1, 2
worker 3: jobs 2, 3
```

A **matching** pairs workers with jobs they are qualified for, each worker and each job used at most once. **Problem:** find a matching of maximum size. The graph is **bipartite**: vertices split into two sides (workers, jobs), and every edge joins the two sides.

**Brute force.** Try every subset of edges and keep the largest that uses no vertex twice: `2^E` subsets.

**Greedy fails.** Give each worker the first free job on their list: worker 0 takes job 0, worker 1 finds job 0 taken and gets nothing. But the matching `0→1, 1→0, 2→2, 3→3` has size 4.

### Augmenting paths in a matching

The same idea as flow. An **alternating path** starts at an unmatched worker, follows an edge to a job, then the matched edge from that job back to its current worker, then another edge to a job, and so on. If it ends at an **unmatched** job, it is an **augmenting path**: flip every edge on it (matched ↔ unmatched) and the matching grows by one.

> **Berge's theorem:** a matching is maximum exactly when it has no augmenting path.

**Kuhn's algorithm** tries each worker in turn and searches for an augmenting path from it with a DFS: "try each job on my list; if the job is free, take it; if it is held by someone, ask that person to move to another job, recursively". A job already visited during the current search is not tried again.

Trace (`match[job] = worker`):

| Worker | Search | `match[0..3]` after |
|---|---|---|
| 0 | job 0 free → take it | `0 · · ·` |
| 1 | job 0 held by 0 → can 0 move? 0 tries job 1: free → 0 moves to job 1, 1 takes job 0 | `1 0 · ·` |
| 2 | job 1 held by 0 → 0 tries job 0: held by 1 → 1 has no other job → fail; 2 tries job 2: free → take it | `1 0 2 ·` |
| 3 | job 2 held by 2 → 2 tries job 1: held by 0 → 0 tries job 0 (held by 1, no alternative) → fail; 2 fails; 3 tries job 3: free | `1 0 2 3` |

Size 4. Worker 1's search is the augmenting path `worker 1 → job 0 → worker 0 → job 1`, and flipping it is exactly "worker 0 moves over".

### As a flow problem

Add a source `s` with a capacity-1 pipe to every worker, a capacity-1 pipe from each worker to each job they are qualified for, and a capacity-1 pipe from every job to a sink `t`. By integrality, a maximum flow uses each pipe 0 or 1 times; the worker–job pipes carrying 1 form a maximum matching. Kuhn's algorithm is this flow computation, specialized.

### Hopcroft–Karp (outline)

Kuhn's algorithm runs one DFS per worker: **O(V · E)**. **Hopcroft–Karp** speeds this up the way Dinic speeds up Edmonds–Karp:

1. BFS from **all** free workers at once, labeling every vertex with its distance along alternating paths, until free jobs are found.
2. DFS from each free worker, following only edges that go one layer deeper, to find a maximal set of vertex-disjoint **shortest** augmenting paths; flip them all.
3. Repeat. There are only O(√V) phases, so the total time is **O(E √V)**.

```python
import random
from collections import deque
from itertools import combinations


def kuhn(n_left, n_right, adj):
    """adj[w] lists the right vertices worker w may take. Returns (size, match_right)."""
    match = [-1] * n_right

    def try_worker(w, visited):
        for job in adj[w]:
            if not visited[job]:
                visited[job] = True
                if match[job] == -1 or try_worker(match[job], visited):
                    match[job] = w
                    return True
        return False

    size = 0
    for w in range(n_left):
        if try_worker(w, [False] * n_right):
            size += 1
    return size, match


def hopcroft_karp(n_left, n_right, adj):
    match_l, match_r = [-1] * n_left, [-1] * n_right
    INF = float("inf")

    def bfs():
        dist = [INF] * n_left
        queue = deque()
        for w in range(n_left):
            if match_l[w] == -1:
                dist[w] = 0
                queue.append(w)
        found = False
        while queue:
            w = queue.popleft()
            for job in adj[w]:
                other = match_r[job]
                if other == -1:
                    found = True
                elif dist[other] == INF:
                    dist[other] = dist[w] + 1
                    queue.append(other)
        return found, dist

    def dfs(w, dist):
        for job in adj[w]:
            other = match_r[job]
            if other == -1 or (dist[other] == dist[w] + 1 and dfs(other, dist)):
                match_l[w], match_r[job] = job, w
                return True
        dist[w] = INF  # dead end for this phase
        return False

    size = 0
    while True:
        found, dist = bfs()
        if not found:
            return size
        for w in range(n_left):
            if match_l[w] == -1 and dfs(w, dist):
                size += 1


def matching_brute(n_left, n_right, adj):
    edges = [(w, j) for w in range(n_left) for j in set(adj[w])]
    for size in range(min(n_left, n_right), 0, -1):
        for chosen in combinations(edges, size):
            if len({w for w, _ in chosen}) == size == len({j for _, j in chosen}):
                return size
    return 0


def main():
    adj = [[0, 1], [0], [1, 2], [2, 3]]
    size, match = kuhn(4, 4, adj)
    assert size == 4 and match == [1, 0, 2, 3]
    assert hopcroft_karp(4, 4, adj) == 4
    assert kuhn(2, 1, [[0], [0]])[0] == 1
    assert hopcroft_karp(0, 0, []) == 0

    rng = random.Random(30)
    for _ in range(300):
        n_left, n_right = rng.randint(0, 5), rng.randint(0, 5)
        adj = [[j for j in range(n_right) if rng.random() < 0.4] for _ in range(n_left)]
        expected = matching_brute(n_left, n_right, adj)
        size, match = kuhn(n_left, n_right, adj)
        assert size == expected == hopcroft_karp(n_left, n_right, adj)
        assert all(j in adj[w] for j, w in enumerate(match) if w != -1)
        assert len({w for w in match if w != -1}) == size


if __name__ == "__main__":
    main()
```

The DFS here is recursive, with depth at most twice the matching size; for very large inputs, raise the recursion limit or rewrite it with an explicit stack.

**Related facts.** In a bipartite graph, the size of a maximum matching equals the size of a minimum **vertex cover** (fewest vertices touching every edge), by **König's theorem**; the cover can be read off the final BFS like a min cut. Matchings with **weights** (maximize total value of the pairs) need the Hungarian algorithm or min-cost flow. Matching in **non-bipartite** graphs needs Edmonds' blossom algorithm.

## 7. Summary

| Problem | Model | Algorithm | Time |
|---|---|---|---:|
| Most flow from `s` to `t` | Residual graph, augment shortest paths | Edmonds–Karp | O(V E²) |
| Cheapest set of links separating `s` and `t` | Min cut = vertices reachable from `s` at the end | Same run | — |
| Pair workers with jobs | Augmenting alternating paths | Kuhn / Hopcroft–Karp | O(V E) / O(E √V) |
| Vertex capacity | Split `v` into `v_in → v_out` | any max flow | — |
| Edge-disjoint paths | All capacities 1 | any max flow | — |

A flow is maximum exactly when no augmenting path exists, and then the reachable set is a minimum cut; a matching is maximum exactly when no augmenting path exists (Berge).

## 8. Pitfalls and practice

1. Forgetting reverse residual edges. Without them, the algorithm is the greedy of §2 and can stop early.
2. Updating only the forward edge after an augmentation. Both `cap[e]` and `cap[e ^ 1]` must change.
3. Using DFS (any augmenting path) with large capacities. Plain Ford–Fulkerson can need as many rounds as the flow value, O(E · F) time for maximum flow `F`; with irrational capacities a bad path choice may never terminate. BFS (Edmonds–Karp) bounds the rounds by O(V E) regardless.
4. Modeling a vertex capacity ("at most 3 units through this city") directly. Split the vertex into `v_in → v_out` with that capacity.
5. Modeling an undirected pipe with one directed edge. Use two directed edges, each with the full capacity.
6. Confusing a **maximal** matching (cannot add an edge) with a **maximum** one (largest size). Greedy gives maximal.

Practice: maximum flow in a small network by hand, then confirm the min cut; maximum bipartite matching (job assignment); minimum number of links to cut to disconnect two nodes; maximum number of edge-disjoint paths (all capacities 1); maximum students taking exam (matching on a grid); assign tasks with costs (min-cost flow, advanced).

Next: [Euler Paths and Further Topics](04-euler-paths-and-roadmap.md).
