# Lectures 1–2 — Search

**Core algorithms:** DFS (stack / depth-first), BFS (queue / breadth-first), UCS (priority by path cost g), A* (priority by f=g+h).

A search problem specifies starting state, legal actions, successors, goal test and edge costs. Completeness and optimality depend on assumptions:
- BFS is optimal for uniform step costs, with finite branching.
- UCS is optimal with sufficiently positive step costs under standard graph-search handling.
- DFS can fail to terminate on infinite paths and is not cost-optimal.
- A* tree search can use an admissible heuristic; graph search that never reopens closed nodes generally needs consistency for the standard optimality guarantee.

## A* heuristics
Actual path cost: `g(n)`; heuristic remaining estimate: `h(n)`; true optimal remaining cost: `h*(n)`.

Admissible: `h(n) ≤ h*(n)`.
Consistent: `h(n) ≤ c(n,n')+h(n')` for every edge (with h(goal)=0).

**Proof of nondecreasing f along a path:**
`f(n')=g(n')+h(n')=g(n)+c(n,n')+h(n') ≥ g(n)+h(n)=f(n)`.

**Proof consistency ⇒ admissibility:** apply the consistency inequality along a path to the goal. The intermediate h terms cancel; taking the cheapest path establishes h(n)≤h*(n).

**Counterexample:** A→B has cost 2, B→G cost 3; h(A)=5,h(B)=1,h(G)=0. All estimates are admissible, but `5≤2+1` is false.

**Practice:** Trace a weighted graph with a cycle using all four algorithms, recording frontier and visited states; construct your own admissible-but-inconsistent heuristic.
