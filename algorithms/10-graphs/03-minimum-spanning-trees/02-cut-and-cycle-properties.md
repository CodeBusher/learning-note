# The Cut and Cycle Properties — Which Edges Are Safe

## 1. A question about one edge

The office graph from [Spanning Trees](01-spanning-trees.md):

```text
        4
   0 ------- 1
   |       / |
 1 |    2 /  | 5
   |     /   |
   2 ------- 3
        8
```

Edges: `0–1=4`, `0–2=1`, `1–2=2`, `1–3=5`, `2–3=8`. The MST is `{0–2, 1–2, 1–3}` with cost 8.

**Without listing any trees, can you prove that `0–2` belongs to the MST?**

Office 0 must be linked to *something*, so every spanning tree contains `0–1` (cost 4) or `0–2` (cost 1). If a tree used `0–1` instead of `0–2`, swapping them gives another spanning tree (checked in §3) that is cheaper by 3. So the cheapest tree uses `0–2`.

The argument used only "vertex 0 has to be linked to the rest". The cut property is the same argument with vertex 0 replaced by any group of vertices.

## 2. Cuts

A **cut** splits the vertices into two nonempty groups, `S` and the rest, `V − S`. An edge **crosses** the cut if one endpoint is in `S` and the other is not.

Here are three cuts of the office graph:

```text
Cut A:  S = {0}          V − S = {1, 2, 3}
        crossing: 0–1 (4), 0–2 (1)                    lightest: 0–2 (1)

Cut B:  S = {0, 2}       V − S = {1, 3}
        crossing: 0–1 (4), 1–2 (2), 2–3 (8)           lightest: 1–2 (2)

Cut C:  S = {0, 1, 2}    V − S = {3}
        crossing: 1–3 (5), 2–3 (8)                    lightest: 1–3 (5)
```

Drawn for cut B, with `S` on the left. The edges inside each box stay on their own side; the three edges between the boxes cross:

```text
     S = {0, 2}                V − S = {1, 3}
   ┌──────────┐              ┌──────────┐
   │  0       │ ─── 4 ────── │  1       │    0–1 crosses, weight 4
   │  │ 1     │ ─── 2 ────── │  │ 5     │    2–1 crosses, weight 2
   │  2       │ ─── 8 ────── │  3       │    2–3 crosses, weight 8
   └──────────┘              └──────────┘
   inside: 0–2 (1)           inside: 1–3 (5)
```

Every spanning tree must contain **at least one** crossing edge of every cut. Otherwise nothing links `S` to the rest.

The lightest crossing edges of cuts A, B and C are `0–2`, `1–2` and `1–3`. Those three edges are exactly the MST. That is the cut property at work.

## 3. The cut property

> **Cut property.** For any cut, a lightest edge crossing it belongs to some MST. If it is the *only* lightest crossing edge, it belongs to every MST.

### The exchange, on the example

Take a spanning tree that does **not** contain `0–2`, for example `T = {0–1, 1–2, 1–3}` with cost 11. Use cut A, `S = {0}`, whose lightest crossing edge is `0–2`.

1. Add `0–2` to `T`. By tree fact 3 from chapter 1, this creates exactly one cycle: `0 → 2 → 1 → 0`.
2. That cycle starts in `S` (at 0), leaves `S` along `0–2`, and must come back to 0. So it crosses the cut a second time. Here the second crossing is `0–1`.
3. Remove `0–1`. Removing an edge from a cycle keeps everything connected, and the count is back to `V − 1 = 3` edges, so the result is again a spanning tree: `{0–2, 1–2, 1–3}`.
4. Cost changes by `+1 − 4 = −3`, from 11 to 8.

```text
before  T = {0–1, 1–2, 1–3}   cost 11
add 0–2     cycle 0–2–1–0 crosses cut A twice: 0–2 and 0–1
remove 0–1
after   T' = {0–2, 1–2, 1–3}  cost 8
```

### The general proof

Let `e` be a lightest edge crossing a cut, and let `T` be any MST.

- If `T` contains `e`, done.
- Otherwise, add `e` to `T`. This closes one cycle. The cycle crosses the cut along `e`, and since it returns to where it started, it crosses the cut again along some other edge `f` in `T`.
- `T − f + e` is a spanning tree: removing `f` from the cycle keeps everything connected, and the edge count stays `V − 1`.
- `e` is a lightest crossing edge and `f` also crosses, so `w(e) ≤ w(f)`. Hence `T − f + e` costs no more than `T`. Since `T` was minimum, so is `T − f + e`, and it contains `e`.

If `e` is the *strictly* lightest crossing edge, `w(e) < w(f)`, so `T − f + e` would be strictly cheaper than `T`. That is impossible for a minimum `T`, so every MST must already contain `e`.

### The version algorithms use

Algorithms build the tree edge by edge. Call the edges picked so far `A`, and suppose `A` is part of some MST. We want to add one more edge without losing that.

> **Safe-edge rule.** If no edge of `A` crosses the cut, a lightest crossing edge `e` can be added: `A ∪ {e}` is still part of some MST.

The proof is the same exchange. Start from an MST `T` that contains `A`. The edge `f` removed in the exchange crosses the cut, and no edge of `A` crosses the cut, so `f` is not in `A`. The new tree `T − f + e` still contains all of `A`, plus `e`.

The phrase "no edge of `A` crosses the cut" matters. Kruskal's algorithm uses the cut "one current component versus everything else", and Prim's uses "the vertices reached so far versus the rest". Neither cut is crossed by an already chosen edge.

## 4. The cycle property

Now the opposite question: which edges can we throw away?

> **Cycle property.** If an edge is the strictly heaviest edge on some cycle, it belongs to no MST.

On the office graph:

| Cycle | Edges and weights | Strictly heaviest | Conclusion |
|---|---|---|---|
| `0–1–2` | `0–1=4`, `1–2=2`, `0–2=1` | `0–1` | `0–1` is in no MST |
| `1–2–3` | `1–2=2`, `2–3=8`, `1–3=5` | `2–3` | `2–3` is in no MST |

Deleting `0–1` and `2–3` leaves three edges, which must then be the MST. We reach the answer from the other side.

**Proof.** Let `e = u–v` be strictly heaviest on a cycle `C`, and suppose some MST `T` contains `e`. Remove `e` from `T`. By tree fact 3, `T` splits into two pieces, one holding `u`, one holding `v`. The rest of the cycle, `C − e`, is a route from `u` to `v`, so some edge `f` on it joins the two pieces. `T − e + f` is a spanning tree, and `w(f) < w(e)` because `e` is strictly heaviest on `C`. That tree is cheaper than `T`, a contradiction.

If the heaviest weight on the cycle is tied, the same swap gives a tree of *equal* cost without `e`. So a tied heaviest edge can appear in some MSTs but is never required.

## 5. Ties and uniqueness

Take a square whose four sides all cost 1:

```text
  0 ──1── 1
  │       │
  1       1
  │       │
  3 ──1── 2
```

Any three sides form a spanning tree of cost 3, so there are **four** different MSTs. With ties, "the MST" is ambiguous; "the MST cost" is not.

> **If all edge weights are different, the MST is unique.**

Why: take any edge `e` of an MST `T`. Removing `e` splits `T` into two pieces, which form a cut. If some other edge crossing that cut were lighter, the exchange would give a cheaper tree, so `e` is a lightest crossing edge. With distinct weights it is the *strictly* lightest, so by the cut property every MST contains `e`. Every MST therefore contains all of `T`'s `V − 1` edges, and since every MST has exactly `V − 1` edges, every MST equals `T`.

## 6. Classifying every edge

The two properties combine into an exact test for each edge `e = u–v` with weight `w`:

| Question about `e` | Answer is yes exactly when… |
|---|---|
| Is `e` in **some** MST? | `u` and `v` are **not** connected using only edges lighter than `w` |
| Is `e` in **every** MST? | `u` and `v` are **not** connected using the *other* edges of weight `≤ w` |

**Why the first test works.** If `u` and `v` are connected by strictly lighter edges, those edges plus `e` form a cycle on which `e` is strictly heaviest, so the cycle property excludes `e`. If they are not, let `S` be the set of vertices reachable from `u` using lighter edges. Any edge leaving `S` has weight at least `w` (a lighter one would have extended `S`), and `e` leaves `S` because `v` is outside. So `e` is a lightest edge crossing the cut `S`, and the cut property puts it in some MST.

**Why the second test works.** If another route of weight-`≤ w` edges joins `u` and `v`, take an MST `T` containing `e` and remove `e`. Some edge `f` on that route joins the two pieces, `w(f) ≤ w`, so `T − e + f` is a spanning tree that costs no more and avoids `e`. If no such route exists, define `S` the same way using the other edges of weight `≤ w`. Then `e` is the strictly lightest edge crossing `S`, so the cut property puts it in every MST.

Edges in every MST are called **critical**. Edges in some but not all MSTs are sometimes called **pseudo-critical**.

## 7. Testing the properties against brute force

The script checks every claim of this chapter against the brute force from chapter 1. Weights drawn from `1..3` make ties common, which exercises the "some" and "every" tests hard.

```python
import random
from itertools import combinations


def connected(n, edges, u, v):
    """Can u reach v using the undirected edges (a, b, w) in `edges`?"""
    adj = [[] for _ in range(n)]
    for a, b, _ in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen = {u}
    stack = [u]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return v in seen


def minimum_trees(n, edges):
    """(best cost, list of index sets of every MST) by brute force."""
    best, trees = None, []
    for chosen in combinations(range(len(edges)), n - 1):
        picked = [edges[i] for i in chosen]
        if all(connected(n, picked, 0, x) for x in range(n)):
            cost = sum(w for _, _, w in picked)
            if best is None or cost < best:
                best, trees = cost, [set(chosen)]
            elif cost == best:
                trees.append(set(chosen))
    return best, trees


def in_some_mst(n, edges, i):
    u, v, w = edges[i]
    lighter = [e for e in edges if e[2] < w]
    return not connected(n, lighter, u, v)


def in_every_mst(n, edges, i):
    u, v, w = edges[i]
    others = [e for j, e in enumerate(edges) if j != i and e[2] <= w]
    return not connected(n, others, u, v)


def lightest_crossing(edges, side):
    crossing = [e for e in edges if (e[0] in side) != (e[1] in side)]
    return min(crossing, key=lambda e: e[2]) if crossing else None


def random_connected_graph(rng, n, extra, weights):
    edges = []
    for v in range(1, n):  # a random tree keeps the graph connected
        edges.append((rng.randrange(v), v, rng.choice(weights)))
    for _ in range(extra):
        u, v = rng.randrange(n), rng.randrange(n)
        edges.append((u, v, rng.choice(weights)))  # may be a loop or parallel
    return edges


def main():
    offices = [(0, 1, 4), (0, 2, 1), (1, 2, 2), (1, 3, 5), (2, 3, 8)]
    best, trees = minimum_trees(4, offices)
    assert best == 8 and trees == [{1, 2, 3}]
    for side, expected in (({0}, (0, 2, 1)), ({0, 2}, (1, 2, 2)), ({0, 1, 2}, (1, 3, 5))):
        assert lightest_crossing(offices, side) == expected
    assert [in_some_mst(4, offices, i) for i in range(5)] == [False, True, True, True, False]

    square = [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, 1)]
    best, trees = minimum_trees(4, square)
    assert best == 3 and len(trees) == 4
    assert all(in_some_mst(4, square, i) and not in_every_mst(4, square, i) for i in range(4))

    rng = random.Random(2)
    for _ in range(400):
        n = rng.randint(2, 5)
        edges = random_connected_graph(rng, n, rng.randint(0, 4), [1, 2, 3])
        best, trees = minimum_trees(n, edges)
        for i in range(len(edges)):
            assert in_some_mst(n, edges, i) == any(i in t for t in trees)
            assert in_every_mst(n, edges, i) == all(i in t for t in trees)

    # Distinct weights: the MST is unique, and every cut's lightest edge is in it.
    for _ in range(200):
        n = rng.randint(2, 6)
        edges = random_connected_graph(rng, n, rng.randint(0, 5), [0])
        edges = [(u, v, k) for k, (u, v, _) in enumerate(edges)]
        rng.shuffle(edges)
        best, trees = minimum_trees(n, edges)
        assert len(trees) == 1
        tree = {edges[i] for i in trees[0]}
        for size in range(1, n):
            for side in combinations(range(n), size):
                assert lightest_crossing(edges, set(side)) in tree


if __name__ == "__main__":
    main()
```

The classification tests each take O(V + E) per edge with a fresh search; the brute force is only for checking.

## 8. Summary

| Fact | Statement | Proof idea |
|---|---|---|
| Cut property | A lightest edge across any cut is in some MST; a strictly lightest one is in every MST | Add it, remove the other crossing edge on the cycle it closes |
| Safe-edge rule | If no chosen edge crosses the cut, adding a lightest crossing edge keeps "part of some MST" | Same exchange; the removed edge is not a chosen one |
| Cycle property | A strictly heaviest edge on a cycle is in no MST | Remove it, reconnect with a lighter cycle edge |
| Uniqueness | Distinct weights ⇒ one MST | Every tree edge is strictly lightest across its own cut |
| In some MST | Endpoints not joined by strictly lighter edges | Cycle property / cut property |
| In every MST | Endpoints not joined by the *other* edges of weight `≤ w` | Same, with ties |

## 9. Pitfalls and practice

1. Applying the cut property to a cut that an already chosen edge crosses. The exchange might then remove a chosen edge. Algorithms always pick cuts that their chosen edges do not cross.
2. Forgetting "strictly" in the cycle property. A tied heaviest edge can still be in an MST.
3. Claiming the MST is unique when weights repeat. Only the cost is guaranteed unique.
4. Treating a self-loop as a candidate. It never crosses any cut and is always the only edge of its own cycle, so it is in no MST.
5. Thinking the lightest edge at each *vertex* gives the whole MST. Those edges are all safe (cut `{v}`), but together they can leave the graph in several pieces; you still need more cuts.

Practice: find all critical and pseudo-critical edges in a minimum spanning tree; prove by hand that the globally lightest edge is in some MST; find a graph with two MSTs that share no edge (hint: a triangle with equal weights does not work).

Next: [Kruskal's Algorithm](03-kruskal.md).
