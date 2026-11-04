# Bitmask DP — When the State Is a Set

## 1. The assignment problem

`n` workers and `n` jobs; `cost[w][j]` is the cost for worker `w` to do job `j`. Give each worker exactly one job and each job exactly one worker, minimizing the total.

```text
           job 0  job 1  job 2
worker 0     9      2      7
worker 1     6      4      3
worker 2     5      8      1
```

The answer is 9: worker 0 → job 1 (2), worker 1 → job 0 (6), worker 2 → job 2 (1).

**Brute force.** Try all `n!` permutations: fine for `n = 8`, impossible for `n = 16` (`2 × 10^13`).

**Key observation.** Assign workers in a fixed order, 0 first. After some steps, the future depends only on **which jobs are taken**, not on who took them or in what order. Many permutations share the same set of taken jobs, and only the cheapest of them matters. A count is not enough ("3 jobs taken" does not say which 3), so the state must be the set itself.

### 1.1 A set as the bits of an integer

With few objects (about 20 or fewer), store the set in one integer: bit `i` is 1 when object `i` is in the set. `{job 0, job 2}` is `0b101 = 5`. Binary is read **right to left**, so the rightmost digit is bit 0. The `2^n` masks `0 … (1 << n) - 1` are exactly the `2^n` subsets; `full = (1 << n) - 1` is the whole set. [Masks and Subsets](../11-bit-manipulation/04-masks-and-subsets.md) teaches these operations from scratch; DP uses these:

| Set operation | Expression | Example with `mask = 0b0101` = {0, 2} |
|---|---|---|
| Is `i` in the set? | `mask >> i & 1` | `i = 2`: 1 |
| Add `i` | `mask \| (1 << i)` | add 1: `7` |
| Remove `i` (any case) | `mask & ~(1 << i)` | remove 2: `1` |
| Remove `i` known to be present | `mask ^ (1 << i)` | remove 0: `4` |
| Size | `mask.bit_count()` | `2` |
| Lowest member as a bit | `mask & -mask` | `1` |
| Complement within `n` bits | `full ^ mask` | `0b1010` |

XOR **toggles**: on an absent bit it adds the element instead of removing it. `mask & -mask` works because `-mask` in two's complement flips every bit above the lowest set bit.

### 1.2 State and transition

The number of workers assigned so far equals the number of taken jobs, so the next worker's index is `mask.bit_count()` and needs no dimension of its own.

- `dp[mask]` = the minimum cost of assigning workers `0 … k−1` to exactly the jobs in `mask`, where `k = mask.bit_count()`.

The last decision: worker `k − 1` took some job `j` in `mask`.

$$
dp[mask] = \min_{j \in mask}\Big(dp[mask \setminus \{j\}] + cost[k-1][j]\Big),
\qquad dp[0] = 0.
$$

The answer is `dp[full]`. Removing a bit makes the number smaller, so **increasing numeric order** has every dependency ready.

**Trace** (masks written with job 2 on the left):

| Mask | Worker `k−1` | Options | `dp` |
|---|---|---|---|
| `001`, `010`, `100` | 0 | row 0 of `cost` | 9, 2, 7 |
| `011` | 1 | job 0: dp[`010`] + 6 = 8; job 1: dp[`001`] + 4 = 13 | 8 |
| `101` | 1 | job 0: dp[`100`] + 6 = 13; job 2: dp[`001`] + 3 = 12 | 12 |
| `110` | 1 | job 1: dp[`100`] + 4 = 11; job 2: dp[`010`] + 3 = 5 | 5 |
| `111` | 2 | job 0: 5 + 5 = 10; job 1: 12 + 8 = 20; job 2: 8 + 1 = **9** | 9 |

```python
import random
from itertools import permutations
from math import inf


def assignment(cost: list[list[int]]) -> tuple[int, list[int]]:
    """Return (minimum cost, job_of[worker])."""
    n = len(cost)
    if any(len(row) != n for row in cost):
        raise ValueError("cost matrix must be square")
    dp = [inf] * (1 << n)
    choice = [-1] * (1 << n)  # the job given to the last worker
    dp[0] = 0
    for mask in range(1, 1 << n):
        worker = mask.bit_count() - 1
        for j in range(n):
            if mask >> j & 1:
                candidate = dp[mask ^ (1 << j)] + cost[worker][j]
                if candidate < dp[mask]:
                    dp[mask], choice[mask] = candidate, j
    full = (1 << n) - 1
    job_of = [0] * n
    mask = full
    while mask:  # walk back: the last worker's job, then the one before
        job_of[mask.bit_count() - 1] = choice[mask]
        mask ^= 1 << choice[mask]
    return dp[full], job_of


def brute_force(cost):
    n = len(cost)
    return min(sum(cost[w][p[w]] for w in range(n)) for p in permutations(range(n)))


def main():
    cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]
    assert assignment(cost) == (9, [1, 0, 2])
    assert assignment([]) == (0, [])
    assert assignment([[5]]) == (5, [0])
    rng = random.Random(1)
    for _ in range(200):
        n = rng.randint(1, 7)
        c = [[rng.randint(-5, 20) for _ in range(n)] for _ in range(n)]
        value, job_of = assignment(c)
        assert value == brute_force(c)
        assert sorted(job_of) == list(range(n))
        assert sum(c[w][job_of[w]] for w in range(n)) == value


if __name__ == "__main__":
    main()
```

Time O(2^n · n), space O(2^n). The Hungarian algorithm solves plain assignment in O(n³); the bitmask version matters because it adapts to side constraints the Hungarian algorithm cannot handle, and its trick (an index recovered from the popcount) recurs often.

**Why it is correct.** Any assignment of the first `k` workers to `mask` gives worker `k − 1` some `j ∈ mask`, and the rest is an assignment of the first `k − 1` workers to `mask \ {j}`, which costs at least `dp[mask \ {j}]`.

## 2. Traveling salesperson: the set and the last city

`cost[a][b]` is the cost from city `a` to city `b` (`inf` if no road). Start at 0, visit every city exactly once, return to 0, minimizing the total.

```text
      0   1   2   3
0  [  0, 10, 15, 20 ]
1  [ 10,  0, 35, 25 ]
2  [ 15, 35,  0, 30 ]
3  [ 20, 25, 30,  0 ]
```

The best tour is `0 → 1 → 3 → 2 → 0`, cost `10 + 25 + 30 + 15 = 80`.

**What changes from assignment.** The cost of the next step depends on **where we are now**. The set alone forgets the current city; the city alone forgets which cities are still legal. Keep both:

- `dp[mask][last]` = the minimum cost of a path that starts at 0, visits exactly `mask`, and ends at `last`.

Two paths with the same `(mask, last)` have identical futures, so only the cheaper one matters. Push forward to an unvisited `nxt`:

$$
dp[mask \cup \{nxt\}][nxt] \leftarrow \min\Big(dp[mask \cup \{nxt\}][nxt],\ dp[mask][last] + cost[last][nxt]\Big).
$$

Base `dp[{0}][0] = dp[1][0] = 0`; masks without city 0 stay `inf` (so only odd masks are processed). Answer: `min over last of dp[full][last] + cost[last][0]`.

**Trace** of the states on the best tour and its closest rival:

| State `(mask, last)` | How it is reached | Value |
|---|---|---|
| `({0,1}, 1)` | `({0}, 0)` + 10 | 10 |
| `({0,3}, 3)` | `({0}, 0)` + 20 | 20 |
| `({0,1,3}, 3)` | `({0,1}, 1)` + 25 | 35 |
| `({0,1,3}, 1)` | `({0,3}, 3)` + 25 | 45 |
| `({0,1,2,3}, 2)` | `({0,1,3}, 3)` + 30 = 65, or `({0,1,3}, 1)` + 35 = 80 | 65 |
| close the tour at 2 | 65 + 15 | **80** |

Reconstruction stores the previous city per state and walks back, removing the current city from the mask at each step.

### 2.1 Variant: counting Hamiltonian paths

A **Hamiltonian path** visits every vertex exactly once. To count them in a directed graph (any start, any end), keep the same state with **counting** instead of minimizing. Each path has exactly one previous vertex, so the cases are disjoint and add:

$$
ways[mask][v] = \sum_{u \in mask \setminus \{v\},\ adj[u][v]} ways[mask \setminus \{v\}][u],
\qquad ways[\{v\}][v] = 1.
$$

The answer is `sum(ways[full])`. On the undirected 4-cycle `0 — 1 — 2 — 3 — 0` (edges both ways), each of 4 starts goes around in 2 directions: 8 sequences, or 4 if a path and its reverse count once. Fixed start: seed only `ways[{s}][s]`. Hamiltonian **cycles**: fix the start at 0 and close with an edge back to 0.

```python
import random
from itertools import permutations
from math import inf


def traveling_salesperson(cost: list[list[int | float]]) -> tuple[int | float, list[int]] | None:
    """Integer edge costs or inf; start/end at 0, visit each other vertex once."""
    n = len(cost)
    if any(len(row) != n for row in cost):
        raise ValueError("cost matrix must be square")
    if any(value != inf and not isinstance(value, int) for row in cost for value in row):
        raise ValueError("costs must be integers or positive infinity")
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0]  # empty movement; no self-loop is required
    full = (1 << n) - 1
    dp = [[inf] * n for _ in range(1 << n)]
    previous = [[-1] * n for _ in range(1 << n)]
    dp[1][0] = 0
    for mask in range(1, 1 << n, 2):  # odd masks: those containing city 0
        for last in range(n):
            if dp[mask][last] == inf:
                continue
            for nxt in range(1, n):
                if mask >> nxt & 1:
                    continue
                new_mask = mask | (1 << nxt)
                candidate = dp[mask][last] + cost[last][nxt]
                if candidate < dp[new_mask][nxt]:
                    dp[new_mask][nxt] = candidate
                    previous[new_mask][nxt] = last

    best, end = inf, -1
    for last in range(1, n):
        candidate = dp[full][last] + cost[last][0]
        if candidate < best:
            best, end = candidate, last
    if end == -1:
        return None
    reverse_path = []
    mask, vertex = full, end
    while vertex != -1:
        reverse_path.append(vertex)
        predecessor = previous[mask][vertex]
        mask ^= 1 << vertex
        vertex = predecessor
    return best, list(reversed(reverse_path)) + [0]


def count_hamiltonian_paths(adj: list[list[int]]) -> int:
    n = len(adj)
    if any(len(row) != n for row in adj):
        raise ValueError("adjacency matrix must be square")
    if n == 0:
        return 0
    ways = [[0] * n for _ in range(1 << n)]
    for v in range(n):
        ways[1 << v][v] = 1
    for mask in range(1, 1 << n):
        for last in range(n):
            count = ways[mask][last]
            if count == 0:
                continue
            for nxt in range(n):
                if not (mask >> nxt & 1) and adj[last][nxt]:
                    ways[mask | (1 << nxt)][nxt] += count
    return sum(ways[(1 << n) - 1])


def brute_force(cost):
    n = len(cost)
    best = inf
    for order in permutations(range(1, n)):
        route = (0,) + order + (0,)
        best = min(best, sum(cost[a][b] for a, b in zip(route, route[1:])))
    return best


def brute_count(adj):
    n = len(adj)
    return sum(all(adj[a][b] for a, b in zip(p, p[1:])) for p in permutations(range(n)))


def main():
    cost = [[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]
    value, route = traveling_salesperson(cost)
    assert value == 80
    assert route[0] == route[-1] == 0 and sorted(route[:-1]) == [0, 1, 2, 3]
    assert sum(cost[a][b] for a, b in zip(route, route[1:])) == value
    assert traveling_salesperson([[0, 2], [inf, 0]]) is None
    assert traveling_salesperson([[0, -4], [1, 0]]) == (-3, [0, 1, 0])
    assert traveling_salesperson([[inf]]) == (0, [0])
    assert traveling_salesperson([]) == (0, [])

    cycle = [[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 0]]
    assert count_hamiltonian_paths(cycle) == 8  # 4 undirected paths, each in 2 directions
    complete = [[int(a != b) for b in range(6)] for a in range(6)]
    assert count_hamiltonian_paths(complete) == 720  # every order works
    assert count_hamiltonian_paths([[0]]) == 1
    assert count_hamiltonian_paths([[0, 0], [0, 0]]) == 0

    rng = random.Random(2)
    for _ in range(200):
        n = rng.randint(2, 7)
        c = [[inf if rng.random() < 0.2 else rng.randint(-3, 20) for _ in range(n)]
             for _ in range(n)]
        answer = traveling_salesperson(c)
        expected = brute_force(c)
        if expected == inf:
            assert answer is None
        else:
            value, route = answer
            assert value == expected
            assert sum(c[a][b] for a, b in zip(route, route[1:])) == value
        adj = [[int(a != b and rng.random() < 0.5) for b in range(n)] for a in range(n)]
        assert count_hamiltonian_paths(adj) == brute_count(adj)


if __name__ == "__main__":
    main()
```

Both are O(2^n · n²) time and O(2^n · n) space. Negative edges are fine: no city repeats, so no cycle can be repeated.

**Why it is correct.** A path covering `mask ∪ {nxt}` and ending at `nxt` has a previous city `last`; the part before the final edge covers `mask` and ends at `last`. Replacing it with the cheapest such part, `dp[mask][last]`, never hurts, because the final edge and everything after do not care how the prefix was ordered.

## 3. Splitting items into groups: submask enumeration

`n` tasks with durations; sessions of length at most `cap`. Each task goes into exactly one session. Minimize the number of sessions. For `[2, 3, 3, 4]`, `cap = 6`: `{2, 4}` and `{3, 3}`, so 2.

- `dp[mask]` = the minimum number of groups covering exactly `mask`.

The last decision is a whole group: some nonempty `sub ⊆ mask` whose total fits.

$$
dp[mask] = 1 + \min_{\substack{sub \subseteq mask,\ sub \ne \emptyset \\ total(sub) \le cap}} dp[mask \setminus sub],
\qquad dp[\emptyset] = 0.
$$

Precompute `total[mask]` in O(2^n): `total[mask] = total[mask without its lowest bit] + that item's duration`.

**Enumerating submasks.** Start with `sub = mask` and repeat `sub = (sub - 1) & mask` until 0. Subtracting 1 clears the lowest set bit of `sub` and sets every bit below it; `& mask` keeps only allowed bits. The result is the next smaller subset: for `mask = 1011`, `1011, 1010, 1001, 1000, 0011, 0010, 0001, 0000`. A `while sub:` loop skips the empty set; handle it separately when it matters.

**Why the cost is 3^n, not 4^n.** Count pairs `(mask, sub)` with `sub ⊆ mask` item by item: each item is not in `mask`, in `sub`, or in `mask` but not `sub`. Three choices per item: exactly `3^n` pairs. For `n = 12` that is 531,441 instead of 16.7 million; `3^16` is 43 million, slow in Python, so keep `3^n` methods to about `n ≤ 14`.

**The lowest-bit rule.** Groups are unordered: `{2, 4}` then `{3, 3}` is the same split as the reverse. The recurrence still finds the right minimum, but explores each split once per ordering of its groups. Require the chosen group to **contain the lowest item of `mask`**. That item must be in some group, so nothing is lost, and each split is now built in one order only. For minimizing this is a speedup (about `3^n / 2` pairs); for **counting** splits it is required, or a split with `k` groups is counted `k!` times (the script asserts exactly that).

**Trace** (tasks `a=2, b=3, c=3, d=4` are bits 0–3):

| `mask` | Groups containing its lowest item that fit (≤ 6) | `dp` |
|---|---|---|
| {b,c} | {b,c} = 6 | 1 |
| {c,d} | {c}, then {d}; {c,d} = 7 is too big | 2 |
| {a,b,c,d} | {a,d} + dp[{b,c}] = 2; {a,b} + dp[{c,d}] = 3; {a} + dp[{b,c,d}] = 3; … | **2** |

### 3.1 Variant: `k` groups with equal sums in O(2^n · n)

"Partition into `k` subsets with equal sums" works with the `3^n` method and `total[sub] == target`, but a smaller state exists. Fill the groups **one at a time**. All earlier groups are exactly full, so the current group's fill is forced: `total[mask] % target`. So `dp[mask]` = "can the used items form full groups plus a partial current group?", and item `i` may be added when `fill + value[i] ≤ target`. For `[5, 1, 4, 2, 3, 3]`, `k = 3`, target 6: `{5, 1}`, `{4, 2}`, `{3, 3}`, so yes.

This works because filling groups in order makes the partial group's content irrelevant beyond its sum, which the mask already determines. When a group's validity is not a running total (for example, "members are pairwise compatible"), fall back to `3^n`.

```python
import random
from math import inf


def subset_totals(values: list[int]) -> list[int]:
    total = [0] * (1 << len(values))
    for mask in range(1, 1 << len(values)):
        low = mask & -mask
        total[mask] = total[mask ^ low] + values[low.bit_length() - 1]
    return total


def min_groups(durations: list[int], cap: int) -> int:
    if any(d < 0 for d in durations) or cap < 0:
        raise ValueError("durations and cap must be nonnegative")
    if any(d > cap for d in durations):
        raise ValueError("a task longer than cap fits in no group")
    n = len(durations)
    total = subset_totals(durations)
    dp = [inf] * (1 << n)
    dp[0] = 0
    for mask in range(1, 1 << n):
        low = mask & -mask
        rest = mask ^ low  # the group = low + any subset of rest
        sub = rest
        while True:
            group = sub | low
            if total[group] <= cap:
                dp[mask] = min(dp[mask], 1 + dp[mask ^ group])
            if sub == 0:
                break
            sub = (sub - 1) & rest
    return dp[(1 << n) - 1]


def count_splits(durations: list[int], cap: int, lowest_bit: bool = True) -> int:
    """Number of ways to split all items into groups with total <= cap."""
    n = len(durations)
    total = subset_totals(durations)
    ways = [0] * (1 << n)
    ways[0] = 1
    for mask in range(1, 1 << n):
        low = mask & -mask
        sub = mask
        while sub:
            if (not lowest_bit or sub & low) and total[sub] <= cap:
                ways[mask] += ways[mask ^ sub]
            sub = (sub - 1) & mask
    return ways[(1 << n) - 1]


def can_partition_k(values: list[int], k: int) -> bool:
    if k <= 0 or any(v <= 0 for v in values):
        raise ValueError("k and values must be positive")
    total = sum(values)
    if total % k:
        return False
    target = total // k
    if any(v > target for v in values):
        return False
    n = len(values)
    fill = [-1] * (1 << n)  # -1: unreachable; otherwise total(mask) % target
    fill[0] = 0
    for mask in range(1 << n):
        if fill[mask] < 0:
            continue
        for i in range(n):
            if not (mask >> i & 1) and fill[mask] + values[i] <= target:
                fill[mask | (1 << i)] = (fill[mask] + values[i]) % target
    return fill[(1 << n) - 1] == 0


def all_set_partitions(items: list[int]):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for partition in all_set_partitions(rest):
        yield [[first]] + partition
        for i in range(len(partition)):
            yield partition[:i] + [[first] + partition[i]] + partition[i + 1:]


def main():
    assert min_groups([2, 3, 3, 4], 6) == 2
    assert min_groups([], 5) == 0
    assert min_groups([5, 5, 5], 5) == 3
    assert min_groups([1, 2, 3, 4, 5], 15) == 1
    assert count_splits([1, 1, 1], 3) == 5  # the 5 set partitions of 3 items
    assert can_partition_k([5, 1, 4, 2, 3, 3], 3)
    assert not can_partition_k([1, 2, 3, 4], 3) and can_partition_k([2, 2, 2, 2], 4)

    rng = random.Random(4)
    for _ in range(200):
        n = rng.randint(0, 7)
        durations = [rng.randint(1, 6) for _ in range(n)]
        cap = rng.randint(6, 12)
        fitting = [p for p in all_set_partitions(list(range(n)))
                   if all(sum(durations[i] for i in g) <= cap for g in p)]
        assert min_groups(durations, cap) == min(len(p) for p in fitting)
        assert count_splits(durations, cap) == len(fitting)
        # Without the lowest-bit rule, a split with k groups is counted k! times.
        factorial = [1, 1, 2, 6, 24, 120, 720, 5040]
        assert count_splits(durations, cap, lowest_bit=False) == sum(factorial[len(p)] for p in fitting)
        k = rng.randint(1, 3)
        if n:  # k groups, all with the same sum
            assert can_partition_k(durations, k) == any(
                len(p) == k and len({sum(durations[i] for i in g) for g in p}) == 1
                for p in all_set_partitions(list(range(n))))


if __name__ == "__main__":
    main()
```

`min_groups` and `count_splits` are O(3^n) time; `can_partition_k` is O(2^n · n). All use O(2^n) space.

## 4. SOS DP: sum over subsets

Given a value `a[sub]` for every mask of `n` bits, compute for **every** mask

$$
F[mask] = \sum_{sub \subseteq mask} a[sub].
$$

Typical use: `a[x]` = how many numbers in a list equal `x`. Then `F[mask]` counts the numbers whose bits all lie inside `mask`, and "how many `x` satisfy `x & y == 0`?" is `F[full ^ y]`.

**Brute force** enumerates submasks of every mask: `3^n`, 3.5 billion at `n = 20`. SOS DP takes `n · 2^n`, about 21 million.

**Key observation.** A mask is a point in an `n`-dimensional grid with side 2, and `sub ⊆ mask` means every coordinate of `sub` is ≤ that of `mask`. So `F` is an `n`-dimensional **prefix sum** ([Prefix Sums](../04-range-queries/01-prefix-sums.md)). A 2D prefix sum can be built one axis at a time; do the same, one bit at a time:

```text
for each bit i:
    for each mask that has bit i:
        F[mask] += F[mask without bit i]
```

**Invariant.** After processing bits `0 … i−1`, `F[mask]` sums `a[sub]` over the `sub` that **agree with `mask` on bits `i` and up** and are **⊆ `mask` on bits below `i`**. Processing bit `i`: if `mask` has it, its submasks may have bit `i` set (already in `F[mask]`) or cleared (exactly `F[mask ^ (1 << i)]`). After all bits, `F[mask]` covers every subset, each once.

**Trace** (`n = 2`, `a = [1, 2, 3, 4]` for masks `00, 01, 10, 11`):

| Step | `F[00]` | `F[01]` | `F[10]` | `F[11]` |
|---|---|---|---|---|
| start (`F = a`) | 1 | 2 | 3 | 4 |
| bit 0: `F[01] += F[00]`, `F[11] += F[10]` | 1 | 3 | 3 | 7 |
| bit 1: `F[10] += F[00]`, `F[11] += F[01]` | 1 | 3 | 4 | **10** |

```python
import random


def sum_over_subsets(a: list[int]) -> list[int]:
    size = len(a)
    if size & (size - 1) or size == 0:
        raise ValueError("length must be a power of two")
    n = size.bit_length() - 1
    f = a.copy()
    for i in range(n):
        bit = 1 << i
        for mask in range(size):
            if mask & bit:
                f[mask] += f[mask ^ bit]
    return f


def sum_over_supersets(a: list[int]) -> list[int]:
    f = a.copy()
    n = len(a).bit_length() - 1
    for i in range(n):
        bit = 1 << i
        for mask in range(len(a)):
            if not mask & bit:
                f[mask] += f[mask | bit]
    return f


def undo_subset_sums(f: list[int]) -> list[int]:
    """Inverse of sum_over_subsets (the Mobius transform): recover a from F."""
    a = f.copy()
    n = len(f).bit_length() - 1
    for i in range(n):
        bit = 1 << i
        for mask in range(len(f)):
            if mask & bit:
                a[mask] -= a[mask ^ bit]
    return a


def count_disjoint_partners(numbers: list[int], n: int) -> list[int]:
    """For each y, how many x in numbers have x & y == 0 (x may be y itself)."""
    count = [0] * (1 << n)
    for x in numbers:
        count[x] += 1
    within = sum_over_subsets(count)
    full = (1 << n) - 1
    return [within[full ^ y] for y in numbers]


def main():
    assert sum_over_subsets([1, 2, 3, 4]) == [1, 3, 4, 10]
    assert sum_over_supersets([1, 2, 3, 4]) == [10, 6, 7, 4]
    assert count_disjoint_partners([0b01, 0b10, 0b11, 0b00], 2) == [2, 2, 1, 4]

    rng = random.Random(6)
    for _ in range(100):
        n = rng.randint(0, 7)
        a = [rng.randint(-5, 9) for _ in range(1 << n)]
        f = sum_over_subsets(a)
        g = sum_over_supersets(a)
        for mask in range(1 << n):
            assert f[mask] == sum(a[s] for s in range(1 << n) if s & mask == s)
            assert g[mask] == sum(a[s] for s in range(1 << n) if s & mask == mask)
        assert undo_subset_sums(f) == a
        numbers = [rng.randrange(1 << n) for _ in range(rng.randint(1, 15))]
        assert count_disjoint_partners(numbers, n) == [
            sum(1 for x in numbers if x & y == 0) for y in numbers]


if __name__ == "__main__":
    main()
```

Time O(n · 2^n), space O(2^n), in place. The bit loop must be the **outer** loop; swapping the loops counts some subsets more than once.

**Variants.** Replace `+=` with `max=` for the maximum over subsets. Superset sums iterate the other way. `undo_subset_sums` (the Möbius transform) recovers `a` from `F`; subset convolution and inclusion–exclusion over masks are built from this pair.

## 5. Summary: when bitmask DP fits, and what it costs

Many "use each item once" problems look like they need every **order** (`n!`). Bitmask DP notices that the future depends only on **which** items are used, sometimes plus the last one, and merges all orders with the same state.

| `n` | Orders `n!` | States `2^n · n` | Work `2^n · n²` |
|---|---|---|---|
| 10 | 3,628,800 | 10,240 | 102,400 |
| 16 | 20,922,789,888,000 | 1,048,576 | 16,777,216 |
| 20 | about 2.4 × 10^18 | 20,971,520 | 419,430,400 |

**Signal:** `n ≤ 20` and a rule like "each item used exactly once" or "each item in exactly one group."

| State | Transition | Cost | Example |
|---|---|---|---|
| `dp[mask]` | Add one item; position = popcount | O(2^n · n) | Assignment |
| `dp[mask][last]` | Add one item after `last` | O(2^n · n²) | TSP, Hamiltonian paths |
| `dp[mask]` over submasks | Add a whole group | O(3^n) | Work sessions, set partitions |
| `dp[mask]` with forced partial group | Add one item to the current group | O(2^n · n) | `k` equal-sum groups |
| `F[mask]` by bits | Prefix sum, one bit at a time | O(n · 2^n) | Sum over subsets |

Other states with the same shape: shortest superstring and Steiner tree (`dp[mask][v]`), profile DP for tilings (the mask is the boundary of a partly filled column), and game states such as `win[mask]` ([Games and Probability](11-games-and-probability.md)).

**Speed and memory in Python.** Plain Python runs roughly 10–50 million simple loop steps per second: `2^16 · 16²` takes seconds, `2^20 · 20²` takes minutes. Memory often runs out first. A list stores an 8-byte pointer per slot, and each integer outside −5 … 256 is a separate object of about 28–32 bytes, so a nested `dp[1 << 20][20]` of big integers approaches 1 GB. Remedies: one flat list indexed `mask * n + last`, or `array('q')`, which stores 64-bit integers inline; drop recoverable dimensions (the worker index in §1); skip unreachable states (odd masks only in TSP); keep two popcount layers when the recurrence allows; or split the items in half (meet in the middle).

## 6. Pitfalls and practice

1. **Reading binary backwards.** Bit 0 is the **rightmost** digit. `0b0101` is {0, 2}, not {1, 3}.
2. **Precedence and `~`.** `1 << i - 1` is `1 << (i - 1)`; add parentheses. Python's `~mask` is negative; use `full ^ mask` for the complement.
3. **Removing with XOR when the bit may be absent.** XOR adds it instead; use `mask & ~(1 << i)`.
4. **Forgetting the last vertex.** In TSP and Hamiltonian paths the set alone is not enough.
5. **Evaluation order.** Plain increasing numeric order of `mask`, as the outer loop, serves transitions that add bits and those that remove them.
6. **Counting groups in every order.** For unordered partitions, force the next group to contain the lowest remaining item.
7. **Skipping the empty submask.** `while sub:` never visits `sub = 0`.
8. **`3^n` with too large `n`.** Keep it to about `n ≤ 14` in Python, or find an `O(2^n · n)` state.
9. **Memory blow-up.** Flatten, use `array`, or shrink the state.
10. **SOS loop order.** Bits outside, masks inside.

Practice: Find the Shortest Superstring, Shortest Path Visiting All Nodes, Minimum Cost to Connect Two Groups of Points, Maximum Compatibility Score Sum, Partition to K Equal Sum Subsets, Matchsticks to Square, Minimum Number of Work Sessions to Finish the Tasks, Fair Distribution of Cookies, Parallel Courses II, Number of Ways to Wear Different Hats to Each Other, Smallest Sufficient Team, Count the Number of Square-Free Subsets, Beautiful Arrangement, Maximum AND Sum of Array.

Next: [Digit DP](10-digit-dp.md).
