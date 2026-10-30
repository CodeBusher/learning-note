# Search

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

### Why DFS space is O(bm), and when it is O(m)

DFS follows one branch at a time, but a stack implementation that generates all children also keeps unexplored siblings. At each of up to `m` levels, as many as `b−1` siblings wait while the search descends. The active path plus those siblings uses at most about `m + m(b−1) = bm` node records.

For branching factor 3 and depth 4, there can be two pending siblings at each level, in addition to the active path. Counting only the four path steps misses those waiting nodes.

Your `O(m)` intuition applies to recursive DFS that generates successors one at a time and stores only constant-size iterator state per level. It also agrees with `O(bm)` when `b` is treated as a fixed constant. A graph-search visited set adds memory: it can require `O(|V|)` records, where `|V|` is the number of reachable states. These bounds assume constant-size state records, not a copied full path in every record. [** Does it depend on the implementation details? If we are using a stack, it will be O(bm), but if we are using a recursion, it will be O(m)?]

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

### Tree search, graph search, and reopening

**Tree search** treats different paths to the same state as different search nodes. An admissible heuristic never overestimates the remaining cost, so a cheaper unfinished solution still has a frontier path with `f` no greater than that solution's cost. With `h(goal)=0`, A* therefore returns an optimal solution when it removes a goal from the priority queue, under the usual completeness assumptions. Testing for a goal when it is merely generated is too early.

**Graph search** merges paths reaching the same state and records the best cost found. A state becomes **closed** after expansion. **Reopening** means putting a closed state back on the frontier after finding a cheaper route to it, so the improvement can reach its descendants.

A consistent heuristic guarantees that the first expansion of a state already uses its optimal path cost; reopening is unnecessary. With an admissible but inconsistent heuristic, a state may be expanded too soon. A* must allow reopening when a better cost is discovered to retain its optimality guarantee. The worked example below shows the failure if it does not. [** Can you show with an example?]

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

## Deeper explanation: designing and evaluating heuristics

**Relax the problem to construct a lower bound.** Suppose a robot moves on a rectangular grid, one unit north/south/east/west per step, but there are walls. Ignore the walls. From (1,2) to (4,6), the relaxed problem needs |4-1|+|6-2|=7 moves. Walls cannot make the real optimal route *shorter*, so Manhattan distance is an admissible heuristic for this movement model.

**Why is it consistent?** A single legal unit step changes Manhattan distance by at most one. Thus h(n)-h(n')≤1=c(n,n'), or h(n)≤c(n,n')+h(n'). The triangle inequality is the mathematical reason, not just a visual analogy.

**Dominance.** If both heuristics are admissible and h₂(n)≥h₁(n) at every node, h₂ is more informed; under standard tree-search assumptions A* with h₂ need not explore as many low-f nodes. It may cost more time to compute, so stronger is not automatically faster overall.

**Greedy best-first vs A*.** Greedy uses priority h(n) only; A* uses g(n)+h(n). A low h does not imply a cheap complete route if reaching that node already cost a lot.

**Challenge:** If diagonal movement becomes legal at unit cost, Manhattan distance from (0,0) to (1,1) equals 2 although the true shortest path costs 1. It is now inadmissible. Revisit heuristic construction whenever actions or costs change.



## Practice examples with worked solutions

These additional teaching examples specify costs, successor order, and stopping rules so you can reproduce every step. Read the solution directly, or cover it to try the problem first.

### 1. Fewest edges versus lowest cost

**Problem.** Directed edges are `S→A:1`, `S→B:2`, `A→G:9`, `B→C:2`, `C→G:2`. Generate successors alphabetically; DFS explores A before B. Test goals when removed from the frontier. Which path does each algorithm return?

**Solution.** DFS follows S→A→G and returns cost `1+9=10`. BFS also returns S→A→G: it has two edges, while S→B→C→G has three. Its removal order is S, A, B, G. BFS minimizes edge count here, not weighted cost.

UCS removes S(0), A(1), B(2), C(4), G(6), where parentheses show `g`. After expanding A, G is waiting with cost 10; expanding C improves it to 6. UCS returns S→B→C→G with cost 6. This is why finding a goal during generation is not enough to stop UCS.

### 2. Why an admissible heuristic may require reopening

**Problem.** Use directed edges `S→A:3`, `S→B:1`, `B→A:1`, `A→G:3`. Set `h(S)=0`, `h(A)=0`, `h(B)=4`, `h(G)=0`. Trace A* with and without reopening.

**Solution.** True remaining costs are 5, 3, 4, and 0 for S, A, B, and G, so the heuristic is admissible. It is inconsistent on B→A because `4 > 1+0`.

| Step | Removed state | Resulting frontier entries (g, f) |
|---|---|---|
| 1 | S | A(3,3), B(1,5) |
| 2 | A | B(1,5), G(6,6) |
| 3 | B | A has a better route with g=2 |

Without reopening, the improved route through A is never expanded; G is returned with cost 6. With reopening, A(2,2) is expanded again, improves G to (5,5), and the returned path S→B→A→G costs 5. Admissibility bounds estimates against true remaining cost; consistency additionally controls estimates across each edge.

### 3. Build a heuristic from the allowed moves

**Problem.** A robot starts at (0,0) and wants to reach (3,2). Each move costs 1. Compare four-way movement with eight-way movement that includes diagonals.

**Solution.** With four-way movement and no walls, three horizontal plus two vertical steps are necessary: Manhattan distance is 5. Walls can only preserve or increase this cost, so 5 remains a lower bound when a route exists.

With unit-cost diagonals, two diagonal steps and one horizontal step reach the goal in 3. Manhattan distance would overestimate. Use `max(|Δx|,|Δy|)=3`, called Chebyshev distance: every move reduces each coordinate gap by at most one, and diagonals reduce both together. It is consistent because one legal move changes this maximum by at most one.

For two robots that can move simultaneously and have individual relaxed distances 3 and 5, the sum 8 can overestimate elapsed time: both may finish in 5 time steps. The maximum 5 is a lower bound for that simultaneous-movement objective.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

- [State Spaces and Search Problems](https://inst.eecs.berkeley.edu/~cs188/textbook/search/state.html)
- [Uninformed Search](https://inst.eecs.berkeley.edu/~cs188/textbook/search/uninformed.html)
- [Informed Search (A*)](https://inst.eecs.berkeley.edu/~cs188/textbook/search/informed.html)

CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
