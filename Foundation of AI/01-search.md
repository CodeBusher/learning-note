# Search

*CS 5100 · Lectures 1–2 · Prof. Nadim Saad · Northeastern University (Silicon Valley)*

*CS 5100 · Lectures 1–2*

## Search problem fundamentals

A search problem specifies an initial state, available actions, successor states, a goal test, and transition costs. A **frontier** contains generated states/paths awaiting expansion; an **explored/closed** set records expanded states in graph search.

## Algorithm comparison

Let `b` be branching factor, `d` depth of the shallowest goal, `m` maximum search depth, `C*` optimal solution cost, and `ε>0` a lower bound on step cost when relevant.

| Algorithm | Frontier / selection | Complete? | Optimal? | Time (common tree bound) | Space (common tree bound) |
|---|---|---|---|---|---|
| DFS | Stack (LIFO), deepest first | No in infinite-depth search (yes in finite graph with appropriate visited handling) | No | O(b^m) | O(bm) for depth-first tree search |
| BFS | Queue (FIFO), shallowest first | Yes for finite branching | Yes with uniform step costs | O(b^(d+1)) | O(b^(d+1)) |
| UCS | Priority queue, minimum g(n) | Yes when step costs ≥ ε and finite branching | Yes with nonnegative edges and appropriate best-cost updates | Exponential worst case; often written O(b^(1+⌊C*/ε⌋)) | Exponential worst case |
| A* | Priority queue, minimum f(n)=g(n)+h(n) | Under standard finite branching, positive-cost, and heuristic assumptions | Tree search: admissible h; graph search without reopening: consistent h | Exponential worst case; heavily dependent on heuristic | Exponential worst case |

These are illustrative **tree-search** bounds, not universal bounds for graph implementations. With `h=0`, A* reduces to UCS; with equal unit step costs, UCS expands in the same cost layers as BFS.

### What is guaranteed?
- **Complete**: will find a solution if one exists (under stated conditions).
- **Optimal**: returns a minimum-total-cost solution.
- DFS saves memory, while BFS can be expensive due to its breadth.
- UCS considers cost incurred; A* also estimates cost remaining.

## A* in detail

For each node `n`:

- `g(n)`: *known* cost of the discovered path from start to n.
- `h(n)`: estimated cheapest remaining cost from n to the goal.
- `h*(n)`: *actual* cheapest remaining cost.
- `f(n)=g(n)+h(n)`: estimated total cost of a solution that goes through n.

A* repeatedly removes from its priority queue the node with smallest `f`. In graph search, if it discovers a lower-cost route to a state, it updates that state's best `g`; whether closed nodes may be reopened affects guarantees when h is inconsistent.

### Admissibility vs. consistency

**Admissible** (optimistic):
`h(n) ≤ h*(n)` for all n, and typically `h(goal)=0`.

**Consistent** (edge-wise triangle inequality):
`h(n) ≤ c(n,n') + h(n')` for every edge n→n'; assume `h(goal)=0`.

A heuristic can satisfy **both**. In standard settings, consistency implies admissibility, but admissibility alone does not imply consistency.

**Why consistency gives monotone f:**
```text
f(n') = g(n') + h(n')
      = g(n) + c(n,n') + h(n')
     >= g(n) + h(n)
      = f(n)
```
The equality for `g(n')` holds for the specific path just extended; it need not hold for a state's previously known best path. Along an extended path, the f estimate cannot decrease.

**Consistency implies admissibility:** Add inequalities along any path n→n1→…→G. Intermediate h terms cancel, giving h(n) ≤ path cost + h(G) = path cost. This is true for every path; choose the cheapest.

### Worked example: A* vs. UCS

Directed edges with nonnegative costs:

```text
       2         2
   S ------> A ------> G
    \                       (goal)
     \ 1         5
      ------> B ------> G
```

There are two candidate paths:
- S→A→G: cost 2+2=**4** (optimal).
- S→B→G: cost 1+5=**6**.

Choose a heuristic:
`h(S)=4, h(A)=2, h(B)=5, h(G)=0`.
Here each h is the exact remaining cost, so it is admissible and consistent.

| Expansion / candidate | g | h | f=g+h |
|---|---:|---:|---:|
| Start S | 0 | 4 | 4 |
| Generate A from S | 2 | 2 | 4 |
| Generate B from S | 1 | 5 | 6 |
| Expand A; generate G | 4 | 0 | 4 |

A* pops S, then A (f=4 rather than B's 6), then G. It returns cost **4**.

**UCS comparison:** UCS first pops S, then B (g=1), then A (g=2), then G (g=4). UCS also finds the optimal cost but expands an extra node B because it has no estimate of remaining cost.

**Check consistency on every edge:**
- S→A: 4 ≤ 2+2 ✓
- S→B: 4 ≤ 1+5 ✓
- A→G: 2 ≤ 2+0 ✓
- B→G: 5 ≤ 5+0 ✓

### Admissible but inconsistent example

Edges: A→B cost 2, B→G cost 3. Actual remaining distances: h*(A)=5, h*(B)=3, h*(G)=0.
Choose `h(A)=5, h(B)=1, h(G)=0`.

It is **admissible** (5≤5 and 1≤3), but fails **consistency** on A→B: `5 ≤ 2+1` is false.

Why care? With inconsistent heuristics, graph A* may need to **reopen** previously closed states when it discovers a cheaper path. You should not intentionally seek inconsistency; consistency is a useful stronger guarantee.

### Constructing heuristics

A good heuristic should be cheap to calculate, informative, and provably non-overestimating when optimality is required.

- Grid with unit-cost four-way movement: Manhattan distance `|x-x_goal|+|y-y_goal|` is a lower bound.
- With an allowed diagonal move, plain Manhattan distance may overestimate; reconsider the movement model.
- Straight-line Euclidean distance can be admissible for routes whose actual cost is at least Euclidean distance in matching units.
- The zero heuristic `h(n)=0` is consistent (for nonnegative edges) but provides no informed guidance.

## Practice

1. In the worked graph, set h=0. Record UCS/A* node expansion order and cost.
2. Replace h(B)=5 with h(B)=0. Does this preserve admissibility? Consistency? Explain edge by edge.
3. Prove consistency implies admissibility via a path to G.
4. Design a grid heuristic when multiple cars move **simultaneously**; why might summing each car's Manhattan distance overestimate number of time steps?
5. Explain why admissibility alone may be insufficient for graph A* that never reopens closed nodes.

*Based on Lecture 1 search comparisons and Lecture 2 A*, heuristic-consistency diagrams, and the multi-car heuristic exercise; numeric graph in this chapter is an additional worked teaching example.*

## References

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus, Lectures 1–2 (student-provided lecture notes).

**Supplementary:** UC Berkeley [CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/):
- [State Spaces and Search Problems](https://inst.eecs.berkeley.edu/~cs188/textbook/search/state.html)
- [Uninformed Search](https://inst.eecs.berkeley.edu/~cs188/textbook/search/uninformed.html)
- [Informed Search (A*)](https://inst.eecs.berkeley.edu/~cs188/textbook/search/informed.html)

*CS188 provides additional or alternative explanations; the course lecture material remains the primary source.*

## Deeper explanation: designing and evaluating heuristics

**Relax the problem to construct a lower bound.** Suppose a robot moves on a rectangular grid, one unit north/south/east/west per step, but there are walls. Ignore the walls. From (1,2) to (4,6), the relaxed problem needs |4-1|+|6-2|=7 moves. Walls cannot make the real optimal route *shorter*, so Manhattan distance is an admissible heuristic for this movement model.

**Why is it consistent?** A single legal unit step changes Manhattan distance by at most one. Thus h(n)-h(n')≤1=c(n,n'), or h(n)≤c(n,n')+h(n'). The triangle inequality is the mathematical reason, not just a visual analogy.

**Dominance.** If both heuristics are admissible and h₂(n)≥h₁(n) at every node, h₂ is more informed; under standard tree-search assumptions A* with h₂ need not explore as many low-f nodes. It may cost more time to compute, so stronger is not automatically faster overall.

**Greedy best-first vs A*.** Greedy uses priority h(n) only; A* uses g(n)+h(n). A low h does not imply a cheap complete route if reaching that node already cost a lot.

**Worked choice:** S→A costs 2, A→G costs 2, S→B costs 1, B→G costs 5. Let h(A)=2, h(B)=5, h(G)=0, h(S)=4. After expanding S, A has f=2+2=4 while B has f=1+5=6; A* expands A and finds the path costing 4. Greedy also chooses A in this case, but that is not a general optimality guarantee.

**Challenge:** If diagonal movement becomes legal at unit cost, Manhattan distance from (0,0) to (1,1) equals 2 although the true shortest path costs 1. It is now inadmissible. Revisit heuristic construction whenever actions or costs change.


## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. Based on student-provided lecture notes (Lectures 1–12); these are independent study summaries, not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).
- [CS188: state](https://inst.eecs.berkeley.edu/~cs188/textbook/search/state.html)
- [CS188: uninformed](https://inst.eecs.berkeley.edu/~cs188/textbook/search/uninformed.html)
- [CS188: informed](https://inst.eecs.berkeley.edu/~cs188/textbook/search/informed.html)

CS188 material is supplementary and is not attributed to the Northeastern course.
