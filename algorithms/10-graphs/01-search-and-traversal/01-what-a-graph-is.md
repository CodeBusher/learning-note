# What a Graph Is — Vertices, Edges, and How to Store Them

## 1. Can you fly there?

An airline flies these routes, each in both directions:

```text
Boston – Chicago      Chicago – Denver      Boston – Miami
Denver – Seattle      Austin – Phoenix
```

Can you fly from Boston to Seattle, changing planes as often as you like? From Boston to Phoenix? Draw a dot per city and a line per route:

```text
   Miami        Austin
     |            |
   Boston       Phoenix
     |
   Chicago
     |
   Denver
     |
   Seattle
```

Boston → Chicago → Denver → Seattle works, so the first answer is **yes**. No line leaves the group {Miami, Boston, Chicago, Denver, Seattle}, and Phoenix is outside it, so the second answer is **no**. Positions and line lengths in the drawing don't matter; only **which dots are joined** does. That is what a graph records.

## 2. The vocabulary

A **graph** is a set of **vertices** (the dots, also called nodes) and a set of **edges** (the lines), each edge joining two vertices. `V` is the number of vertices and `E` the number of edges; in code, vertices are numbered `0, 1, …, V − 1`.

| Situation | Vertex | Edge | Kind |
|---|---|---|---|
| Friendships | a person | "A and B are friends" | **undirected**: works both ways |
| Following on a social app | an account | "A follows B" | **directed**: A → B says nothing about B → A |
| Road map with distances | a town | a road with its length | **weighted**: each edge carries a number |
| One-way streets with travel times | an intersection | a street with minutes | directed and weighted |

A directed edge `u → v` can be travelled from `u` to `v` only. An undirected edge `u – v` is stored in code as the two arrows `u → v` and `v → u`.

- Two vertices joined by an edge are **adjacent**; each is a **neighbor** of the other.
- The **degree** of a vertex is the number of edges touching it. In a directed graph, **out-degree** counts arrows leaving it and **in-degree** counts arrows arriving.
- A **path** is a sequence of vertices in which consecutive ones are joined by an edge, such as `Boston, Chicago, Denver`. Its **length** is its number of edges, here 2.
- `v` is **reachable** from `u` if some path goes from `u` to `v`. Every vertex reaches itself by a path of length 0.
- A **cycle** is a path of at least one edge that returns to its start without reusing an edge, such as `A, B, C, A`.
- A **self-loop** joins a vertex to itself. **Parallel edges** are two or more edges joining the same pair. Most problems promise neither; the code in this folder says what it does when they appear.
- In an undirected graph, a **connected component** is a largest group of vertices that all reach each other. The flight graph has two: {Miami, Boston, Chicago, Denver, Seattle} and {Austin, Phoenix}.

## 3. Three ways to store a graph

Number the cities: Boston 0, Chicago 1, Denver 2, Miami 3, Seattle 4, Austin 5, Phoenix 6.

**Edge list**: one pair per edge.

```text
[(0, 1), (1, 2), (0, 3), (2, 4), (5, 6)]
```

**Adjacency matrix**: a `V × V` table with `matrix[u][v] = 1` when there is an edge `u → v`. Undirected graphs give a symmetric table.

```text
        0  1  2  3  4  5  6
    0 [ 0  1  0  1  0  0  0 ]
    1 [ 1  0  1  0  0  0  0 ]
    2 [ 0  1  0  0  1  0  0 ]
    3 [ 1  0  0  0  0  0  0 ]
    4 [ 0  0  1  0  0  0  0 ]
    5 [ 0  0  0  0  0  0  1 ]
    6 [ 0  0  0  0  0  1  0 ]
```

**Adjacency list**: `adj[u]` lists every `v` with an edge `u → v`.

```text
adj[0] = [1, 3]      adj[4] = [2]
adj[1] = [0, 2]      adj[5] = [6]
adj[2] = [1, 4]      adj[6] = [5]
adj[3] = [0]
```

| Question | Edge list | Adjacency matrix | Adjacency list |
|---|---|---|---|
| Memory | O(E) | O(V²) | O(V + E) |
| "Is there an edge `u → v`?" | O(E) scan | O(1) | O(deg(u)) scan |
| "List the neighbors of `u`" | O(E) scan | O(V) row scan | O(deg(u)) |
| Visit every edge once | O(E) | O(V²) | O(V + E) |

A search visits every vertex and asks for its neighbors, so the **adjacency list** is the default here, and a whole search costs O(V + E). The `V` term is real: a vertex with no edges still owns an empty list that the search must look at. The matrix pays off only for dense graphs (E near V²) or constant-time edge lookups. The edge list is the usual input format, and [Kruskal's algorithm](../03-minimum-spanning-trees/03-kruskal.md) wants nothing else.

## 4. Building a graph from real input

- **One-based vertices.** Many problems number vertices `1..n`. Subtract 1 from every endpoint, or allocate `n + 1` lists and leave index 0 unused. Pick one and say so in a comment.
- **Weighted edges.** Store `(neighbor, weight)` pairs. Weighted searches live in [Shortest Paths](../04-shortest-paths/README.md); building the lists looks the same.
- **Named vertices.** When vertices are strings (cities, emails), give each new name the next free number as you meet it.

```python
def to_adjacency_list(n, edges, directed=False):
    """Build adj[u] = list of v with an edge u -> v."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    adj = [[] for _ in range(n)]
    for u, v in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"edge ({u}, {v}) has a vertex outside 0..{n - 1}")
        adj[u].append(v)
        if not directed:
            adj[v].append(u)
    return adj


def to_matrix(n, edges, directed=False):
    """matrix[u][v] = number of edges u -> v (1 for a simple graph)."""
    matrix = [[0] * n for _ in range(n)]
    for u, v in edges:
        matrix[u][v] += 1
        if not directed and u != v:
            matrix[v][u] += 1
    return matrix


def build_named_graph(pairs):
    """Map names to ids 0, 1, ... in first-seen order; return (ids, names, adj)."""
    ids = {}
    names = []
    adj = []

    def vertex(name):
        if name not in ids:
            ids[name] = len(names)
            names.append(name)
            adj.append([])
        return ids[name]

    for a, b in pairs:
        u, v = vertex(a), vertex(b)
        adj[u].append(v)
        adj[v].append(u)
    return ids, names, adj


def build_weighted(n, triples, one_based=False):
    """triples are (u, v, w); returns adj[u] = [(v, w), ...] for an undirected graph."""
    shift = 1 if one_based else 0
    adj = [[] for _ in range(n)]
    for u, v, w in triples:
        u, v = u - shift, v - shift
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("vertex out of range")
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj


def main():
    edges = [(0, 1), (1, 2), (0, 3), (2, 4), (5, 6)]
    adj = to_adjacency_list(7, edges)
    assert adj == [[1, 3], [0, 2], [1, 4], [0], [2], [6], [5]]
    matrix = to_matrix(7, edges)
    for u in range(7):
        for v in range(7):
            assert matrix[u][v] == adj[u].count(v)
            assert matrix[u][v] == matrix[v][u]  # undirected: symmetric

    # Directed: the reverse arrow is not added.
    assert to_adjacency_list(3, [(0, 1), (1, 2)], directed=True) == [[1], [2], []]
    # Handshake lemma: the degrees add up to twice the number of edges.
    assert sum(len(neighbors) for neighbors in adj) == 2 * len(edges)
    # Empty graph and isolated vertices.
    assert to_adjacency_list(0, []) == []
    assert to_adjacency_list(2, []) == [[], []]
    try:
        to_adjacency_list(2, [(0, 2)])
    except ValueError:
        pass
    else:
        raise AssertionError("bad vertex was accepted")

    routes = [("Boston", "Chicago"), ("Chicago", "Denver"), ("Boston", "Miami"),
              ("Denver", "Seattle"), ("Austin", "Phoenix")]
    ids, names, adj = build_named_graph(routes)
    assert names == ["Boston", "Chicago", "Denver", "Miami", "Seattle", "Austin", "Phoenix"]
    assert ids["Seattle"] == 4
    assert sorted(names[v] for v in adj[ids["Boston"]]) == ["Chicago", "Miami"]

    adj_w = build_weighted(3, [(1, 2, 5), (2, 3, 7)], one_based=True)
    assert adj_w == [[(1, 5)], [(0, 5), (2, 7)], [(1, 7)]]
    assert build_named_graph([]) == ({}, [], [])


if __name__ == "__main__":
    main()
```

The handshake check in `main` holds because each undirected edge adds one entry to two lists, so the lists together hold exactly `2E` entries.

## 5. Grids are graphs you never build

A maze of open cells `.` and walls `#` is a graph: each open cell is a vertex, and two open cells sharing a side are joined.

```text
   col 0 1 2
row 0   . . #
row 1   # . .
row 2   . . .
```

Cell `(0, 0)` has one neighbor, `(0, 1)`; cell `(1, 1)` has three: `(0, 1)`, `(1, 2)` and `(2, 1)`. There is no need to number cells and build lists: add each of the four direction offsets to `(r, c)` and keep the results that are inside the grid and open. A graph whose edges are computed by a rule instead of stored is an **implicit graph**.

```python
DIRECTIONS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRECTIONS_8 = DIRECTIONS_4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def grid_neighbors(grid, r, c, directions=DIRECTIONS_4):
    """Yield open cells next to (r, c). grid is a list of equal-length strings."""
    rows, cols = len(grid), len(grid[0])
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != "#":
            yield nr, nc


def main():
    maze = ["..#",
            "#..",
            "..."]
    assert list(grid_neighbors(maze, 0, 0)) == [(0, 1)]
    assert sorted(grid_neighbors(maze, 1, 1)) == [(0, 1), (1, 2), (2, 1)]
    assert sorted(grid_neighbors(maze, 2, 0)) == [(2, 1)]
    # With diagonal moves, (1, 1) also touches (0, 0), (2, 0), and (2, 2).
    assert len(list(grid_neighbors(maze, 1, 1, DIRECTIONS_8))) == 6

    # An R x C grid with no walls has R(C-1) + C(R-1) four-direction edges.
    open_grid = ["." * 5] * 4
    degree_sum = sum(len(list(grid_neighbors(open_grid, r, c)))
                     for r in range(4) for c in range(5))
    assert degree_sum == 2 * (4 * 4 + 5 * 3)


if __name__ == "__main__":
    main()
```

An `R × C` grid has `V = RC` vertices and fewer than `2RC` four-direction edges, so a search over it costs O(RC).

Other implicit graphs: words joined when they differ in one letter; board positions joined by one legal move; maze cells **plus the keys you hold**, because the same cell with different keys has different futures. Choosing what a vertex must remember is the subject of [State-Space Search](04-state-space-search.md).

## 6. A slow but honest answer to "what can I reach?"

Which vertices can be reached from `s`? Keep a set `reached = {s}`. Scan the whole edge list; whenever an edge has one end inside `reached` and the other outside, add the outside end. Repeat full scans until one adds nothing.

Trace from Boston (0), scanning the edge list `(0,1), (1,2), (0,3), (2,4), (5,6)` **backwards** to show the worst behavior:

| Scan | Edges that add a vertex | `reached` after the scan |
|---:|---|---|
| start | | {0} |
| 1 | `(0,3)` adds 3; `(0,1)` adds 1 | {0, 1, 3} |
| 2 | `(1,2)` adds 2 | {0, 1, 2, 3} |
| 3 | `(2,4)` adds 4 | {0, 1, 2, 3, 4} |
| 4 | nothing | stop |

**Why it's correct.** Nothing joins `reached` unless it is joined to something already reachable, so every member is reachable. Conversely, along any path `s = p0, p1, …, pk`, scan `i` at the latest adds `p_i`, so every reachable vertex is eventually added.

**Why it's slow.** Each scan costs O(E), and a bad edge order can make a scan add only one vertex, so up to V scans: O(V · E). Scan 3 re-examined `(0,1)`, `(0,3)` and `(1,2)`, whose work was already done. A vertex's edges matter only once, right after the vertex joins `reached`. Keeping a to-do list of newly reached vertices and looking at each one's edges once brings the cost down to O(V + E); that to-do list is depth-first and breadth-first search, the next two chapters.

The slow method stays useful as a **brute force**: short enough to trust, it is the reference answer later code is tested against on small random graphs.

```python
def reachable_by_scanning(n, edges, source, directed=False):
    """Return the set of vertices reachable from source. O(V * E) worst case."""
    if not 0 <= source < n:
        raise ValueError("source out of range")
    reached = {source}
    changed = True
    while changed:
        changed = False
        for u, v in edges:
            if u in reached and v not in reached:
                reached.add(v)
                changed = True
            if not directed and v in reached and u not in reached:
                reached.add(u)
                changed = True
    return reached


def main():
    edges = [(0, 1), (1, 2), (0, 3), (2, 4), (5, 6)]
    assert reachable_by_scanning(7, edges, 0) == {0, 1, 2, 3, 4}
    assert reachable_by_scanning(7, edges, 6) == {5, 6}
    # Directed: following arrows only.
    assert reachable_by_scanning(3, [(0, 1), (2, 1)], 0, directed=True) == {0, 1}
    assert reachable_by_scanning(3, [(0, 1), (2, 1)], 1, directed=True) == {1}
    assert reachable_by_scanning(1, [], 0) == {0}


if __name__ == "__main__":
    main()
```

## 7. Summary: model before you search

1. **What is a vertex?** A city, a cell, a word, or a whole state such as "cell plus keys held".
2. **What is an edge?** Directed or not? Weighted? Weights decide whether BFS is enough ([Breadth-First Search](03-bfs.md)) or a weighted method is needed ([Shortest Paths](../04-shortest-paths/README.md)).
3. **How big is it?** A search costs O(V + E). If a vertex is a board arrangement, V may be astronomically large.
4. **Given or implicit?** Implicit graphs compute neighbors on demand and store no lists.
5. **What can go wrong in the input?** One-based numbering, isolated vertices, self-loops, parallel edges, several components.

## 8. Pitfalls and practice

1. Forgetting the reverse arrow for an undirected edge. The graph then behaves as directed, and searches miss vertices.
2. Off-by-one vertex numbers. Input numbered `1..n` in a list of size `n` crashes on vertex `n`, or silently drops vertex 0.
3. An adjacency matrix for a large sparse graph. With V = 100,000 it has 10¹⁰ cells.
4. Forgetting isolated vertices. They appear in no edge, own empty lists, and are components of their own.
5. Reading `grid[r][c]` before checking `0 <= r < rows` and `0 <= c < cols`. A negative index wraps around silently in Python.

Practice: find if path exists in graph; find center of star graph; find the town judge (in-degree and out-degree); count the edges of a grid; build adjacency lists for a graph whose vertices are strings.

Next: [Depth-First Search](02-dfs.md).
