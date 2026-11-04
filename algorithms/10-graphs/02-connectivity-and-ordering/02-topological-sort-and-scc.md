# Topological Sort and Strongly Connected Components — Order and Cycles in Directed Graphs

## 1. Putting tasks in order

Six courses, numbered 0 to 5. An arrow `a → b` means course `a` must be taken before course `b`.

```text
   0       1                 arrows:
    ↘    ↙  ↘                 0 → 2,  1 → 2,  1 → 3
      2      3                2 → 4,  3 → 4,  4 → 5
       ↘    ↙
         4
         ↓
         5
```

Find an order in which to take all six. By hand: `0, 1, 2, 3, 4, 5` works, and so does `1, 3, 0, 2, 4, 5`. An order that lists every vertex so that every arrow points **forward** (from earlier to later) is called a **topological order**. Usually many exist.

If the arrows form a cycle, such as `3 → 4 → 5 → 3`, no order exists: 3 must come before 4, 4 before 5, and 5 before 3. A directed graph with no directed cycle is called a **DAG** (directed acyclic graph). A topological order exists **exactly** for DAGs; §2 proves the "if" direction by constructing one.

**Brute force.** Try every ordering and check each arrow. There are `n!` orderings: 720 for 6 courses, about 2.4 × 10¹⁸ for 20.

## 2. Kahn's algorithm: repeatedly take something with no prerequisites

**Key observation.** In a DAG, some vertex has no incoming arrows. (If every vertex had one, you could walk backwards along incoming arrows forever; with finitely many vertices you would revisit one, which means a cycle.) Such a vertex can safely go first. Remove it and its outgoing arrows; what remains is still a DAG, so repeat.

The number of arrows coming into `v` is its **in-degree**. "Remove a vertex" is done by lowering the in-degree of each of its out-neighbors; a vertex whose in-degree reaches 0 is ready.

1. Compute every in-degree. Put every vertex with in-degree 0 in a queue.
2. Remove a vertex `u` from the queue and append it to the order. For each arrow `u → v`, lower `indeg[v]` by 1; if it becomes 0, add `v` to the queue.
3. When the queue is empty: if the order has every vertex, it is a topological order. Otherwise a cycle exists.

Trace on the course graph:

| Step | Remove | Arrows processed | `indeg` for 0..5 after | Queue after | Order |
|---:|---:|---|---|---|---|
| 0 | | compute in-degrees | 0 0 2 1 2 1 | [0, 1] | |
| 1 | 0 | 0→2 | 0 0 **1** 1 2 1 | [1] | 0 |
| 2 | 1 | 1→2, 1→3 | 0 0 **0** **0** 2 1 | [2, 3] | 0 1 |
| 3 | 2 | 2→4 | 0 0 0 0 **1** 1 | [3] | 0 1 2 |
| 4 | 3 | 3→4 | 0 0 0 0 **0** 1 | [4] | 0 1 2 3 |
| 5 | 4 | 4→5 | 0 0 0 0 0 **0** | [5] | 0 1 2 3 4 |
| 6 | 5 | none | | [] | 0 1 2 3 4 5 |

Now add the arrow `5 → 3`. In-degrees start `0 0 2 2 2 1`. Steps 1–2 remove 0 and 1 and make 2 ready (3 drops only to 1); step 3 removes 2 and lowers 4 to 1. The queue is empty, yet 3, 4, 5 remain, each with in-degree 1. They are stuck on each other: the cycle `3 → 4 → 5 → 3`.

**Variant: course schedule as interview problems state it.** `n` courses and a list of pairs `[a, b]` meaning "to take `a` you must first take `b`". Can you finish all courses? **Course Schedule II.** Return one valid order, or an empty list.

The only trap is direction. `[a, b]` means `b` before `a`, so the arrow is `b → a`. Getting it backwards produces the reversed order, which is wrong whenever any prerequisite exists.

Sometimes the order must be the **lexicographically smallest** one (smallest available course first at every step). Replace the queue with a min-heap; time becomes O(V log V + E). Both are `find_order` below; the tests compare the heap version with the smallest of all valid permutations.

```python
import heapq
import itertools
import random
from collections import deque


def topological_order(adj, smallest_first=False):
    """Kahn's algorithm. Return an order, or None if the graph has a directed cycle.

    smallest_first uses a min-heap, giving the lexicographically smallest order.
    """
    n = len(adj)
    indeg = [0] * n
    for u in range(n):
        for v in adj[u]:
            indeg[v] += 1
    ready = [u for u in range(n) if indeg[u] == 0]
    if smallest_first:
        heapq.heapify(ready)
        pop, push = (lambda: heapq.heappop(ready)), (lambda v: heapq.heappush(ready, v))
    else:
        ready = deque(ready)
        pop, push = ready.popleft, ready.append
    order = []
    while ready:
        u = pop()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                push(v)
    return order if len(order) == n else None


def find_order(num_courses, prerequisites, smallest_first=False):
    """Course Schedule II: [a, b] means b before a, so the arrow is b -> a. [] if impossible."""
    adj = [[] for _ in range(num_courses)]
    for course, before in prerequisites:
        adj[before].append(course)
    return topological_order(adj, smallest_first) or []


def is_topological(adj, order):
    position = {u: i for i, u in enumerate(order)}
    return len(order) == len(adj) and len(position) == len(adj) and all(
        position[u] < position[v] for u in range(len(adj)) for v in adj[u])


def main():
    courses = [[2], [2, 3], [4], [4], [5], []]
    assert topological_order(courses) == [0, 1, 2, 3, 4, 5]
    courses[5].append(3)
    assert topological_order(courses) is None
    assert topological_order([]) == []
    assert topological_order([[0]]) is None  # a self-loop is a cycle
    assert topological_order([[1, 1], []]) == [0, 1]  # parallel arrows are fine
    assert find_order(2, [[1, 0]]) == [0, 1]
    assert find_order(2, [[1, 0], [0, 1]]) == []
    assert find_order(4, [[1, 3], [2, 3]], smallest_first=True) == [0, 3, 1, 2]

    rng = random.Random(31)
    for _ in range(400):
        n = rng.randint(1, 6)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 9)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        valid = [list(p) for p in itertools.permutations(range(n)) if is_topological(adj, p)]
        order = topological_order(adj)
        assert (order is not None) == bool(valid)
        if order is not None:
            assert is_topological(adj, order)
            assert topological_order(adj, smallest_first=True) == min(valid)


if __name__ == "__main__":
    main()
```

O(V + E) time: every vertex enters the queue once and every arrow is processed once. O(V) extra space.

**Why it's correct.** A vertex enters the queue only when all its incoming arrows have been processed, which means all its predecessors are already in the order; so every arrow points forward. If the queue empties early, every leftover vertex has an incoming arrow from another leftover vertex; walking backwards along those arrows inside the leftover set must eventually repeat a vertex, so there is a cycle. Note that the leftover set can contain more than the cycle: vertices **downstream** of a cycle get stuck too (above, nothing was downstream, but an arrow `5 → 6` would strand 6 as well).

Parallel arrows are fine as long as each copy is counted in `indeg` and each copy decrements it once, which the code does.

## 3. Topological order from DFS finishing times

There is a second way, built on DFS. Run the three-color DFS from [Chapter 2 of Search and Traversal](../01-search-and-traversal/02-dfs.md#7-cycles-in-a-directed-graph) from every unvisited vertex, and record each vertex when it **finishes**. Then **reverse** that list.

**Why it works.** Take any arrow `u → v` in a DAG and look at the moment DFS examines it, while `u` is gray:

- `v` is white: DFS enters `v` now, and `v` finishes before `u` does.
- `v` is black: `v` has already finished.
- `v` is gray: impossible, that would be a cycle.

In every possible case `v` finishes before `u`. So in **decreasing** finishing order, `u` comes before `v`, for every arrow. Reversing the finish list gives exactly that.

Trace on the course graph (`adj`: `0: [2]`, `1: [2, 3]`, `2: [4]`, `3: [4]`, `4: [5]`):

| Step | Event | Gray path | Finish list |
|---:|---|---|---|
| 1 | enter 0 | 0 | |
| 2 | 0 → 2: enter 2 | 0 2 | |
| 3 | 2 → 4: enter 4 | 0 2 4 | |
| 4 | 4 → 5: enter 5; 5 has no arrows, finish | 0 2 4 | 5 |
| 5 | 4 done, finish; 2 done, finish; 0 done, finish | | 5 4 2 0 |
| 6 | enter 1 (next unvisited root) | 1 | 5 4 2 0 |
| 7 | 1 → 2: black, skip | 1 | |
| 8 | 1 → 3: enter 3; 3 → 4 black; finish 3 | 1 | 5 4 2 0 3 |
| 9 | 1 done, finish | | 5 4 2 0 3 1 |

Reversed: `1, 3, 0, 2, 4, 5`. Check every arrow: 0→2, 1→2, 1→3, 2→4, 3→4, 4→5 all point forward.

The same pass detects cycles for free: an arrow into a gray vertex means there is no topological order.

```python
import itertools
import random


def topological_order_dfs(adj):
    """Reverse finishing order of DFS. Return None if there is a directed cycle."""
    WHITE, GRAY, BLACK = 0, 1, 2
    n = len(adj)
    color = [WHITE] * n
    finished = []
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
                finished.append(u)
                frames.pop()
            elif color[v] == GRAY:
                return None
            elif color[v] == WHITE:
                color[v] = GRAY
                frames.append((v, iter(adj[v])))
    return finished[::-1]


def main():
    courses = [[2], [2, 3], [4], [4], [5], []]
    assert topological_order_dfs(courses) == [1, 3, 0, 2, 4, 5]
    assert topological_order_dfs([[1], [0]]) is None
    assert topological_order_dfs([]) == []

    rng = random.Random(33)
    for _ in range(400):
        n = rng.randint(1, 6)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 9)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        order = topological_order_dfs(adj)
        valid = [p for p in itertools.permutations(range(n))
                 if all(p.index(u) < p.index(v) for u in range(n) for v in adj[u])]
        assert (order is not None) == bool(valid)
        if order is not None:
            assert tuple(order) in valid

    chain = [[i + 1] for i in range(9999)] + [[]]  # deep graph: no recursion limit
    assert topological_order_dfs(chain) == list(range(10000))


if __name__ == "__main__":
    main()
```

O(V + E) time and O(V) extra space, like Kahn's algorithm.

## 4. Preview: longest path in a DAG

Once vertices are in topological order, every arrow into `v` comes from a vertex already processed. So any quantity of the form "best over predecessors" can be computed in one pass. This is dynamic programming on a DAG ([Dynamic Programming](../../09-dynamic-programming/README.md)).

**Problem (parallel courses).** Each semester you may take any number of courses whose prerequisites are done. What is the minimum number of semesters? For the course graph, it is 4: `{0, 1}`, then `{2, 3}`, then `{4}`, then `{5}`.

The answer is the number of vertices on the **longest path**: courses on a chain of prerequisites must go in different semesters, and taking every course as early as possible achieves that bound. With

$$
\text{sem}[v] = 1 + \max_{u \to v} \text{sem}[u] \qquad (\text{or } 1 \text{ if } v \text{ has no prerequisites}),
$$

computed in topological order, the answer is `max(sem)`.

| v (in order) | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| predecessors | | | 0, 1 | 1 | 2, 3 | 4 |
| `sem[v]` | 1 | 1 | 2 | 2 | 3 | 4 |

The same pass with different combining rules gives other classic answers: weighted longest path (`max` of `best[u] + w(u, v)`), shortest path in a DAG with any weights, including negative ones (`min`), and the number of paths (`+`). For a path from a **fixed** source, start that source at 0 and every other vertex at `-inf` (for `max`) so that unreachable vertices never win. Shortest paths in DAGs are developed in [Shortest Paths](../04-shortest-paths/README.md).

```python
import random
from collections import deque


def min_semesters(n, arrows):
    """Return the number of vertices on the longest path, or -1 if there is a cycle."""
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v in arrows:
        adj[u].append(v)
        indeg[v] += 1
    sem = [1] * n
    queue = deque(u for u in range(n) if indeg[u] == 0)
    done = 0
    while queue:
        u = queue.popleft()
        done += 1
        for v in adj[u]:
            sem[v] = max(sem[v], sem[u] + 1)  # u is final when it leaves the queue
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if done < n:
        return -1
    return max(sem, default=0)


def longest_path_brute(n, arrows):
    """Enumerate every path in a DAG by DFS from each vertex."""
    adj = [[] for _ in range(n)]
    for u, v in arrows:
        adj[u].append(v)
    best = 0

    def walk(u, length):
        nonlocal best
        best = max(best, length)
        for v in adj[u]:
            walk(v, length + 1)

    for s in range(n):
        walk(s, 1)
    return best


def main():
    arrows = [(0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (4, 5)]
    assert min_semesters(6, arrows) == 4
    assert min_semesters(2, [(0, 1), (1, 0)]) == -1
    assert min_semesters(0, []) == 0
    assert min_semesters(3, []) == 1

    rng = random.Random(34)
    for _ in range(300):
        n = rng.randint(1, 7)
        rank = rng.sample(range(n), n)  # arrows go from lower rank to higher: a DAG
        arrows = []
        for _ in range(rng.randint(0, 10)):
            u, v = rng.randrange(n), rng.randrange(n)
            if rank[u] < rank[v]:
                arrows.append((u, v))
        assert min_semesters(n, arrows) == longest_path_brute(n, arrows)


if __name__ == "__main__":
    main()
```

O(V + E) time, O(V + E) space for the adjacency lists.

## 5. When cycles are the point: strongly connected components

**Problem.** A town has one-way streets. Which intersections can you drive between **in both directions**? Vertices `u` and `v` are **strongly connected** if `u` can reach `v` and `v` can reach `u`. This relation splits the vertices into groups called **strongly connected components** (SCCs). Every vertex is in exactly one SCC, possibly alone.

```text
     0 → 1                     arrows:
     ↑   ↓                     0→1, 1→2, 2→0,
     └── 2 → 3 → 4             2→3, 3→4, 4→5, 5→3,
             ↑   ↓             6→5, 6→7, 7→6
             └── 5 ← 6 ⇄ 7
```

The SCCs are `{0, 1, 2}`, `{3, 4, 5}`, and `{6, 7}`. From `{0, 1, 2}` you can drive into `{3, 4, 5}` but never back.

Squash each SCC into a single vertex and keep one arrow between two components whenever some original arrow crosses between them. The result is the **condensation**:

```text
   A = {0,1,2}  →  B = {3,4,5}  ←  C = {6,7}
```

The condensation is always a **DAG**. If it had a cycle through components X and Y, every vertex of X could reach every vertex of Y and back, so X and Y would be one SCC, not two. This is the main reason SCCs matter: they turn any directed graph into a DAG of cycle-blobs, and then everything from §1–§4 applies.

**Brute force.** Compute the set of vertices reachable from each vertex (one BFS each), then put `u` and `v` together when each is in the other's set. O(V · (V + E)) time and O(V²) space.

Two linear-time algorithms follow. Both are O(V + E).

## 6. Kosaraju's algorithm: two passes

**Key observation.** Run DFS on the whole graph and record finishing order, as in §3. Consider the vertex that finishes **last**. Its SCC is a **source** of the condensation: no arrow from another component enters it. (§3's argument, applied to components: if component X has an arrow into component Y, the latest finish in X is later than every finish in Y.)

Now **reverse every arrow**. Reversal does not change SCCs (mutual reachability is symmetric), but it turns that source component into a **sink**: no arrow leaves it. A DFS from the last-finishing vertex in the reversed graph can therefore visit exactly its own SCC and nothing else. Remove that SCC, take the next vertex in decreasing finish order that is not yet assigned, and repeat.

1. DFS the original graph; record vertices as they finish.
2. Build the reversed graph.
3. Go through vertices in **decreasing** finish order. Each unassigned vertex starts a DFS in the reversed graph that collects one SCC, skipping assigned vertices.

**Pass 1** on the example (neighbors in the listed order):

| Event | Finish list so far |
|---|---|
| enter 0 → 1 → 2; 2 → 0 is gray, skip; 2 → 3 → 4 → 5; 5 → 3 gray | |
| finish 5, 4, 3 | 5 4 3 |
| finish 2, 1, 0 | 5 4 3 2 1 0 |
| enter 6; 6 → 5 black; 6 → 7; 7 → 6 gray; finish 7, 6 | 5 4 3 2 1 0 7 6 |

Decreasing finish order: `6, 7, 0, 1, 2, 3, 4, 5`.

**Pass 2** on the reversed arrows (`1→0, 2→1, 0→2, 3→2, 4→3, 5→4, 3→5, 5→6, 7→6, 6→7`):

| Start | Reversed-graph DFS visits | SCC |
|---:|---|---|
| 6 | 6 → 7; 7 → 6 already | {6, 7} |
| 7 | already assigned | |
| 0 | 0 → 2 → 1; 1 → 0 already | {0, 1, 2} |
| 3 | 3 → 2 assigned, 3 → 5 → 4; 5 → 6 assigned | {3, 4, 5} |

In pass 2, the search from 3 tried to leave through `3 → 2` and `5 → 6` (reversed arrows), but those vertices were already in finished components. That is exactly why the order matters: the components it could leak into were removed first.

Pass 1 must record **true** finishing order. The plain stack from [Depth-First Search §2.2](../01-search-and-traversal/02-dfs.md#22-explicit-stack-marking-when-pushed) has no finishing moment; using its pop order breaks the algorithm. The stack of frames reproduces recursion exactly.

## 7. Tarjan's algorithm: one pass with low-links

Tarjan's algorithm finds SCCs during a single DFS. Each vertex gets a discovery time `tin[v]` (0, 1, 2, … in order of entry). Vertices are also pushed onto a separate **SCC stack** when entered, and stay there until their whole SCC is identified.

`low[v]` is the smallest `tin` of any vertex **still on the SCC stack** that `v`'s DFS subtree can reach with arrows, using tree arrows downward and then at most one other arrow. Rules:

- On entering `v`: `low[v] = tin[v]`; push `v` on the SCC stack.
- Arrow `v → w` with `w` unvisited: explore `w`; when it finishes, `low[v] = min(low[v], low[w])`.
- Arrow `v → w` with `w` **on the SCC stack**: `low[v] = min(low[v], tin[w])`.
- Arrow `v → w` with `w` visited but **not** on the stack: ignore. `w`'s SCC is complete and cannot include `v`.
- When `v` finishes and `low[v] == tin[v]`: `v` is the **root** (first-entered vertex) of its SCC. Pop the SCC stack down to and including `v`; those vertices are one SCC.

Trace on the example:

| Event | `tin` / `low` changes | SCC stack | SCC found |
|---|---|---|---|
| enter 0, 1, 2 | tin 0, 1, 2 | 0 1 2 | |
| 2 → 0, on stack | low[2] = 0 | 0 1 2 | |
| enter 3, 4, 5 | tin 3, 4, 5 | 0 1 2 3 4 5 | |
| 5 → 3, on stack | low[5] = 3 | | |
| finish 5, then 4 | low[4] = min(4, 3) = 3 | | |
| finish 3: low[3] = 3 = tin[3] | | pop 5, 4, 3 → 0 1 2 | **{3, 4, 5}** |
| finish 2 (low 0), then 1 | low[1] = 0 | | |
| finish 0: low[0] = 0 = tin[0] | | pop 2, 1, 0 → empty | **{0, 1, 2}** |
| enter 6 (tin 6); 6 → 5: visited, **not on stack**, ignore | | 6 | |
| enter 7 (tin 7); 7 → 6 on stack | low[7] = 6 | 6 7 | |
| finish 7; finish 6: low[6] = 6 = tin[6] | | pop 7, 6 | **{6, 7}** |

The arrow `6 → 5` shows why the "not on the stack" rule exists. If it lowered `low[6]` to `tin[5] = 5`, vertex 6 would never satisfy `low == tin`, and `{6, 7}` would never be reported.

SCCs come out of Tarjan's algorithm in **reverse topological order** of the condensation: sinks first (`{3,4,5}` before `{0,1,2}`).

Both algorithms are in the script at the end of §8.

**Why Tarjan is correct, in brief.** The first vertex DFS enters in an SCC, its root `r`, reaches every other vertex of the SCC while it is gray, so they all become its descendants and sit above it on the SCC stack. No vertex of the SCC can reach a vertex on the stack with a smaller `tin` than `r`'s without that vertex being in the same SCC, so `low[r] = tin[r]`. Every other vertex `v` of the SCC can reach `r` (still on the stack), so `low[v] < tin[v]` and it is not mistaken for a root. Popping at `r` removes exactly the SCC, because SCCs finished earlier inside `r`'s subtree have already been popped.

## 8. Using the condensation

Build the condensation by mapping each arrow `u → v` to `comp[u] → comp[v]` and dropping arrows inside one component. Many problems become easy on that DAG.

**Problem.** What is the minimum number of arrows to add so the whole graph becomes strongly connected?

On the condensation, count **sources** (no incoming arrows) and **sinks** (no outgoing arrows). Every source needs at least one new incoming arrow, and every sink at least one new outgoing arrow, and one new arrow serves one of each. So at least `max(sources, sinks)` arrows are needed, and a known construction always achieves it. A graph that is already one SCC needs 0 (it is both a source and a sink, a special case).

In the example, the condensation `A → B ← C` has sources A, C and one sink B: answer `max(2, 1) = 2`, for instance `5 → 0` and `5 → 6`.

The script below has Kosaraju, Tarjan, `condensation` and `arrows_to_strongly_connect`, tested against reach-set SCCs and against trying every set of added arrows on tiny graphs.

```python
import itertools
import random
from collections import deque


def kosaraju(adj):
    n = len(adj)
    seen, finish = [False] * n, []
    for root in range(n):
        if seen[root]:
            continue
        seen[root] = True
        frames = [(root, iter(adj[root]))]
        while frames:
            u, neighbors = frames[-1]
            v = next(neighbors, None)
            if v is None:
                finish.append(u)
                frames.pop()
            elif not seen[v]:
                seen[v] = True
                frames.append((v, iter(adj[v])))
    reverse = [[] for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            reverse[v].append(u)
    comp, groups = [-1] * n, []
    for start in reversed(finish):
        if comp[start] != -1:
            continue
        cid = len(groups)
        comp[start] = cid
        group, stack = [], [start]
        while stack:  # any traversal works here; only membership matters
            u = stack.pop()
            group.append(u)
            for v in reverse[u]:
                if comp[v] == -1:
                    comp[v] = cid
                    stack.append(v)
        groups.append(group)
    return comp, groups


def tarjan(adj):
    n = len(adj)
    tin, low = [-1] * n, [0] * n
    on_stack, stack = [False] * n, []
    comp, groups = [-1] * n, []
    timer = 0
    for root in range(n):
        if tin[root] != -1:
            continue
        tin[root] = low[root] = timer
        timer += 1
        stack.append(root)
        on_stack[root] = True
        frames = [(root, iter(adj[root]))]
        while frames:
            u, neighbors = frames[-1]
            v = next(neighbors, None)
            if v is None:
                frames.pop()
                if low[u] == tin[u]:  # u is the root of an SCC
                    group = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        comp[w] = len(groups)
                        group.append(w)
                        if w == u:
                            break
                    groups.append(group)
                if frames:
                    parent = frames[-1][0]
                    low[parent] = min(low[parent], low[u])
            elif tin[v] == -1:
                tin[v] = low[v] = timer
                timer += 1
                stack.append(v)
                on_stack[v] = True
                frames.append((v, iter(adj[v])))
            elif on_stack[v]:
                low[u] = min(low[u], tin[v])
    return comp, groups


def scc_brute(adj):
    n = len(adj)
    reach = []
    for s in range(n):
        seen = {s}
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        reach.append(seen)
    return {frozenset(v for v in range(n) if v in reach[u] and u in reach[v]) for u in range(n)}


def condensation(adj):
    comp, groups = tarjan(adj)
    count = len(groups)
    dag = [set() for _ in range(count)]
    for u in range(len(adj)):
        for v in adj[u]:
            if comp[u] != comp[v]:
                dag[comp[u]].add(comp[v])
    return comp, [sorted(s) for s in dag]


def arrows_to_strongly_connect(adj):
    comp, dag = condensation(adj)
    if len(dag) <= 1:
        return 0
    has_in = [False] * len(dag)
    for outs in dag:
        for c in outs:
            has_in[c] = True
    sources = sum(not x for x in has_in)
    sinks = sum(not outs for outs in dag)
    return max(sources, sinks)


def strongly_connected(adj):
    n = len(adj)
    for s in range(n):
        seen, stack = {s}, [s]
        while stack:
            for v in adj[stack.pop()]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        if len(seen) != n:
            return False
    return True


def brute_force(adj):
    n = len(adj)
    candidates = [(u, v) for u in range(n) for v in range(n) if u != v]
    for k in range(n + 1):
        for extra in itertools.combinations(candidates, k):
            new = [list(a) for a in adj]
            for u, v in extra:
                new[u].append(v)
            if strongly_connected(new):
                return k
    raise AssertionError("unreachable")


def main():
    adj = [[1], [2], [0, 3], [4], [5], [3], [5, 7], [6]]
    expected = {frozenset({0, 1, 2}), frozenset({3, 4, 5}), frozenset({6, 7})}
    assert {frozenset(g) for g in kosaraju(adj)[1]} == expected
    _, groups = tarjan(adj)
    assert groups == [[5, 4, 3], [2, 1, 0], [7, 6]]  # sinks first
    assert kosaraju([]) == ([], []) and tarjan([]) == ([], [])
    assert tarjan([[0]]) == ([0], [[0]])

    rng = random.Random(35)
    for _ in range(500):
        n = rng.randint(1, 9)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 16)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        brute = scc_brute(adj)
        for algorithm in (kosaraju, tarjan):
            comp, groups = algorithm(adj)
            assert {frozenset(g) for g in groups} == brute
            assert all(comp[v] == i for i, g in enumerate(groups) for v in g)

    adj = [[1], [2], [0, 3], [4], [5], [3], [5, 7], [6]]
    comp, dag = condensation(adj)
    a, b, c = comp[0], comp[3], comp[6]
    assert dag[a] == [b] and dag[c] == [b] and dag[b] == []
    assert arrows_to_strongly_connect(adj) == 2
    assert arrows_to_strongly_connect([[]]) == 0
    assert arrows_to_strongly_connect([[], []]) == 2

    rng = random.Random(36)
    for _ in range(150):
        n = rng.randint(1, 4)
        adj = [[] for _ in range(n)]
        for _ in range(rng.randint(0, 6)):
            adj[rng.randrange(n)].append(rng.randrange(n))
        assert arrows_to_strongly_connect(adj) == brute_force(adj)

    chain = [[i + 1] for i in range(9999)] + [[0]]  # one big cycle, 10,000 deep
    assert len(kosaraju(chain)[1]) == 1 and len(tarjan(chain)[1]) == 1


if __name__ == "__main__":
    main()
```

O(V + E) time and space for each algorithm.

Further uses of the condensation:

- **Reachability between components** is a question about a DAG, so DP in topological order applies (count reachable components, longest path through components, sum of values collected along a route where a whole SCC can be collected at once).
- **2-SAT** (advanced). A formula of clauses `(x or y)` is turned into implication arrows `not x → y` and `not y → x`. The formula is satisfiable exactly when no variable shares an SCC with its own negation. An assignment is read from the component order: set `x` true when `comp[x]` comes after `comp[not x]` in topological order, which with Tarjan's numbering (sinks first) means `comp[x] < comp[not x]`.
- **Eventual safe states**: vertices from which every path ends at a dead end are exactly those that cannot reach any cycle. Kahn's algorithm on the reversed graph finds them.

## 9. Summary

**Topological order** exists exactly for DAGs; both methods run in O(V + E).

| | Kahn (in-degrees) | DFS (finishing order) |
|---|---|---|
| Idea | Remove sources repeatedly | Reverse postorder |
| Cycle signal | Order shorter than V | Arrow into a gray vertex |
| Smallest-first order | Easy with a heap | Not natural |
| Layers ("how many rounds?") | Natural: process the queue layer by layer | Needs extra work |
| Reused later by | Scheduling, DAG DP | Kosaraju's SCC algorithm (§6) |

**Strongly connected components** turn any directed graph into the condensation DAG.

| Algorithm | Time | Extra space | Notes |
|---|---:|---:|---|
| Brute force (reach sets) | O(V(V + E)) | O(V²) | Fine for V ≤ a few hundred |
| Kosaraju | O(V + E) | O(V + E) | Two passes; needs the reversed graph |
| Tarjan | O(V + E) | O(V) | One pass; components come out sinks first |

**DAG DP** (§4): process vertices in topological order and combine over predecessors with `max` (longest path), `min` (shortest path, negative weights allowed) or `+` (path counts).

## 10. Pitfalls and practice

1. Getting prerequisite direction backwards. `[a, b]` meaning "b before a" is the arrow `b → a`.
2. Reporting the leftover vertices of Kahn's algorithm as "the cycle". They include everything downstream of a cycle too.
3. Using discovery order (or a plain stack's pop order) instead of finishing order in DFS topological sort or Kosaraju's first pass.
4. Forgetting to reverse the finish list, or reversing the graph in the wrong pass.
5. In Tarjan's algorithm, lowering `low` through an arrow to a vertex that is visited but no longer on the stack.
6. Running DFS from vertex 0 only. Every unvisited vertex must start its own search.
7. Assuming component numbers from one SCC algorithm follow the same topological direction as another's. Kosaraju numbers sources first; Tarjan numbers sinks first.
8. Recursive DFS on a 10⁵-vertex chain. Use frames, as all code here does.

Practice: course schedule; course schedule II; alien dictionary; parallel courses; minimum height trees (peeling leaves, a Kahn-like idea on undirected trees); find eventual safe states; sequence reconstruction; longest increasing path in a matrix (a DAG on cells); strongly connected components (Kosaraju or Tarjan); count of minimum arrows to make a graph strongly connected; 2-SAT problems.

Next: [Bridges and Articulation Points](03-bridges-and-articulation.md).
