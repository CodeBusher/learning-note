# Dynamic Programming — From Zero to Advanced

Dynamic programming (DP) solves a problem by answering smaller versions of it once each, storing those answers, and building the full answer from them. Chapter 1 starts from a plain recursive function; chapter 12 ends with transitions sped up by deques, Fenwick trees, divide and conquer, Knuth's bound, convex hulls and matrix powers.

> **Learning path:** Foundations [1](01-what-is-dp.md) → [2](02-designing-a-recurrence.md) → [3](03-states-and-reconstruction.md) · Core families [4](04-knapsack-and-coins.md) → [5](05-grid-dp.md) → [6](06-sequences-and-strings.md) → [7](07-interval-dp.md) → [8](08-tree-and-dag-dp.md) · Advanced [9](09-bitmask-dp.md) → [10](10-digit-dp.md) → [11](11-games-and-probability.md) → [12](12-faster-transitions.md)

## Roadmap

### Foundations: read these first, in order

| # | Chapter | You will learn | Problems |
|---|---|---|---|
| 1 | [What Dynamic Programming Is](01-what-is-dp.md) | Why plain recursion is slow, memoization, tables, rolling variables, the five words: state, transition, base case, order, answer | Climbing stairs |
| 2 | [Designing a Recurrence](02-designing-a-recurrence.md) | The last-decision method, `min`/`max`/count/feasibility, "first `i`" vs "ending at `i`", impossible vs zero, pull vs push | House robber, min-cost stairs, decode ways, maximum subarray |
| 3 | [Choosing the State and Rebuilding the Answer](03-states-and-reconstruction.md) | The history test, adding a dimension, parent pointers, top-down vs bottom-up, state machines, DP as paths in a graph | Word break, stock trading with cooldown and `k` transactions |

### Core families: each chapter is one problem shape

| # | Chapter | State shape | Problems |
|---|---|---|---|
| 4 | [Knapsack and Coins](04-knapsack-and-coins.md) | `dp[items][capacity]` | 0/1, unbounded and bounded knapsack; subset sum; coin change; combinations vs sequences |
| 5 | [Grid DP](05-grid-dp.md) | `dp[row][col]` | Unique paths, minimum path sum, maximal square, dungeon (backward DP), two walkers |
| 6 | [Sequences and Strings](06-sequences-and-strings.md) | `dp[i]` ending at `i`, or `dp[i][j]` over two prefixes | LIS, LCS, edit distance, palindromes, distinct subsequences, wildcard and regex matching |
| 7 | [Interval DP](07-interval-dp.md) | `dp[l][r]` by increasing length | Matrix chain, burst balloons, merging stones (`K` piles), palindrome partitioning, optimal BST |
| 8 | [Tree and DAG DP](08-tree-and-dag-dp.md) | `dp[vertex][condition]` | Tree independent set, diameter, rerooting (sum of distances, heights), DAG longest paths and path counts, longest increasing path in a grid |

### Advanced: extra history in the state, and faster transitions

| # | Chapter | Idea | Problems |
|---|---|---|---|
| 9 | [Bitmask DP](09-bitmask-dp.md) | A small set of used items becomes the state | Assignment, traveling salesperson, Hamiltonian paths, set partitions (`3^n`), `k` equal-sum groups, sum over subsets |
| 10 | [Digit DP](10-digit-dp.md) | Build numbers digit by digit under a bound (the tight flag) | Digit sums, adjacent-digit rules, divisibility, unique digits, k-th number, 5,000-digit bounds |
| 11 | [Games and Probability](11-games-and-probability.md) | The state is a game position or a random process | Win/lose games, minimax, Sprague–Grundy, expected dice rolls, knight probability |
| 12 | [Faster Transitions](12-faster-transitions.md) | Same recurrence, cheaper way to find the best predecessor | Monotonic deque, prefix sums, Fenwick tree, divide and conquer, Knuth, Li Chao tree, matrix power |

## Recognizing the state shape

| The problem looks like… | Likely state | Evaluation order | Typical cost | Chapter |
|---|---|---|---:|---|
| A row of items, each taken or skipped | `dp[i]` over the first `i` items | Increasing `i` | O(n) × choices | [2](02-designing-a-recurrence.md) |
| A contiguous piece that must end somewhere | `dp[i]` ending exactly at `i` | Increasing `i`; answer is `max(dp)` | O(n) | [2](02-designing-a-recurrence.md) |
| A few modes that switch over time | One table per mode | Increasing time | O(n × modes) | [3](03-states-and-reconstruction.md) |
| Items and a limited budget | `dp[i][capacity]` | Item by item; loop direction matters | O(nW) | [4](04-knapsack-and-coins.md) |
| Moves on a grid that only go right/down | `dp[r][c]` | Row by row | O(RC) | [5](05-grid-dp.md) |
| Two sequences compared | `dp[i][j]` over two prefixes | Increasing `i`, then `j` | O(nm) | [6](06-sequences-and-strings.md) |
| Split or merge a contiguous range | `dp[l][r]` | Increasing length | Often O(n³) | [7](07-interval-dp.md) |
| Combine independent subtrees | `dp[v][condition]` | Children before parents | O(V) | [8](08-tree-and-dag-dp.md) |
| Any acyclic dependency graph | `dp[v]` | Topological order | O(V + E) | [8](08-tree-and-dag-dp.md) |
| Which of ≤ 20 items are used | `dp[mask][last]` | Increasing mask | O(2ⁿ n²) | [9](09-bitmask-dp.md) |
| Count numbers ≤ a huge bound | `dp[position][tight][summary]` | Digit by digit | Digits × summary size | [10](10-digit-dp.md) |
| Two players taking turns | `dp[position]` for the player to move | Smaller games first | Positions × moves | [11](11-games-and-probability.md) |
| A random process, expected cost | `E[state]` | From the end | States × outcomes | [11](11-games-and-probability.md) |
| Correct recurrence, slow inner `min`/`sum` | Same state | Same order | Drops a factor of n | [12](12-faster-transitions.md) |

An O(nW) knapsack depends on the **numeric value** of the capacity W, not on how many digits W has. This is called *pseudopolynomial* time. An O(2ⁿn²) bitmask DP becomes impractical quickly, even though the recurrence is short.

## Conventions

- Zero-based indexing. The prefix of length `i` is `a[:i]`. Intervals are half-open `[l, r)` unless a chapter says otherwise, which differs from the inclusive query API in [Range Queries](../04-range-queries/README.md).
- Every Python block is a complete runnable script using only the standard library, with its own assertions. Most compare the DP against a brute force on small random inputs.
- Impossible states use `0` (counts), `False` (feasibility), `inf` (minimum) or `-inf` (maximum), never a value that could win. Each problem states whether the empty solution is allowed.
- Counts are exact Python integers unless a modulus is part of the problem.

## Practice order

1. Chapters 1–3 in order: everything later uses their vocabulary (state, transition, base case, order, answer).
2. Chapters 4–8 in any order. For each problem, write the state sentence and the last-decision cases before reading the code, trace the small table by hand, then run the script and break it on purpose (flip a loop direction, change a base case) to see which assertion fails.
3. Chapters 9–11 assume the core families; chapter 12 assumes 6–8 and [Range Queries](../04-range-queries/README.md).

## Connections to other topics

- [Counting and Distributions](../12-math-and-geometry/04-counting-distributions/README.md): generating functions explain knapsack and coin DPs algebraically, including why loop direction matters.
- [Range Queries](../04-range-queries/README.md): prefix sums, Fenwick trees and segment trees speed up DP transitions ([Faster Transitions](12-faster-transitions.md)).
- [Monotonic Stacks and Deques](../06-monotonic-stack-and-deque/README.md): sliding-window minimum transitions.
- [Trees](../03-trees/01-binary-trees-and-traversals.md): the tree vocabulary that chapter 8 builds on.
- [Graphs](../10-graphs/README.md): an acyclic DP is a computation on a dependency graph. Problems with cycles need BFS or shortest-path algorithms instead.
