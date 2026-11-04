# Four Ways to Put 4 Balls in 2 Boxes — Distinct or Identical, Labeled or Not

## 1. The four cases on one small example

Put $k=4$ items into $n=2$ boxes, empty boxes allowed. How many ways are there? The answer is 16, 8, 5 or 3, depending only on whether the items and the boxes can be told apart. Unless noted, $k$, $n$ and capacities in these notes are nonnegative integers.

**Distinct items $a,b,c,d$; labeled boxes A, B.** Each item independently picks a box, so there are $2\cdot2\cdot2\cdot2=16$ arrangements. In general:

$$
\boxed{n^k}\qquad\text{(product rule)}.
$$

**Identical items; labeled boxes.** Only the occupancy vector $(x_A,x_B)$ matters:

$$
(4,0),\ (3,1),\ (2,2),\ (1,3),\ (0,4)\quad\Rightarrow\quad 5.
$$

**Distinct items; identical boxes.** Only the *grouping* matters, not which box holds which group:

$$
\{abcd\},\ \{abc\mid d\},\ \{abd\mid c\},\ \{acd\mid b\},\ \{bcd\mid a\},\ \{ab\mid cd\},\ \{ac\mid bd\},\ \{ad\mid bc\}\quad\Rightarrow\quad 8.
$$

**Identical items; identical boxes.** Only the multiset of occupancies matters, so sort it in decreasing order:

$$
(4,0),\ (3,1),\ (2,2)\quad\Rightarrow\quad 3.
$$

| Items | Labeled boxes | Identical boxes |
|---|---|---|
| Distinct | 16 | 8 |
| Identical | 5 | 3 |

**Forgetting information shrinks the count, but not by a simple factor.** For distinct items, going from labeled to identical boxes halves the count, $16/2!=8$, because every grouping appears in exactly two labeled versions. For identical items, $5/2!$ is not even an integer. Here $(3,1)$ and $(1,3)$ merge, but $(2,2)$ has only one labeled version. Dividing by $n!$ is safe only when every arrangement has the same number of labeled versions. [§12](05-set-partitions.md#12-distinct-items-identical-boxes-stirling-and-bell-numbers) shows when that holds.

**Each case has its own mathematics.**

| Case | An arrangement is… | Counted by |
|---|---|---|
| Identical items, labeled boxes | an ordered vector: a *composition* | stars and bars ([labeled boxes](02-labeled-boxes.md)) |
| Identical items, identical boxes | a multiset of occupancies: an *integer partition* | coin-change DP ([integer partitions](04-integer-partitions.md)) |
| Distinct items, identical boxes | a grouping: a *set partition* | Stirling numbers ([set partitions](05-set-partitions.md)) |
| Distinct items, labeled boxes | a function from items to boxes | product rule, inclusion–exclusion ([§11](05-set-partitions.md#11-distinct-items-labeled-boxes)) |

[Generating functions](03-generating-functions.md) and DP connect them all. Labeled boxes come first, because the reason the stick method fails for identical boxes is exactly what makes partitions necessary.

**Corner cases.** With $k=0$ there is exactly one arrangement (everything empty), even when $n=0$. With $n=0<k$ there is none. Apply these boundaries explicitly instead of using factorial formulas outside their domain.

The four counts can be checked by listing every labeled arrangement and then merging the ones that look the same once labels are forgotten:

```python
from itertools import product


def four_counts(k: int, n: int) -> dict[str, int]:
    """Brute force: list labeled arrangements, then forget labels."""
    if k < 0 or n < 0:
        raise ValueError("k and n must be nonnegative")
    # Distinct items, labeled boxes: item i goes to box f[i].
    functions = list(product(range(n), repeat=k))
    # Identical items: keep only the occupancy vector.
    vectors = {tuple(f.count(b) for b in range(n)) for f in functions}
    # Identical boxes: keep only the set of nonempty groups.
    groupings = {
        frozenset(frozenset(i for i in range(k) if f[i] == b)
                  for b in range(n) if b in f)
        for f in functions
    }
    multisets = {tuple(sorted(v, reverse=True)) for v in vectors}
    return {
        "distinct/labeled": len(functions),
        "identical/labeled": len(vectors),
        "distinct/identical": len(groupings),
        "identical/identical": len(multisets),
    }


def main():
    assert four_counts(4, 2) == {
        "distinct/labeled": 16,
        "identical/labeled": 5,
        "distinct/identical": 8,
        "identical/identical": 3,
    }
    assert four_counts(0, 0) == {key: 1 for key in four_counts(0, 0)}
    assert all(v == 0 for v in four_counts(3, 0).values())
    assert list(four_counts(3, 3).values()) == [27, 10, 5, 3]
    assert four_counts(5, 3)["identical/identical"] == 5


if __name__ == "__main__":
    main()
```

Exponential time; it exists only to check the formulas of later chapters on small inputs.

## Pitfalls and practice

1. **Dividing by $n!$ to make boxes identical.** Correct for distinct items in nonempty boxes, wrong for identical items: $5/2$ is not a count.
2. **Not deciding distinguishability first.** "Distribute 4 candies to 2 children" (labeled boxes) and "split 4 candies into 2 piles" (identical boxes) differ: 5 vs 3.
3. **Factorial formulas at $k=0$ or $n=0$.** Handle the boundary cases explicitly.

Practice: redo the table for $k=3$, $n=3$ by hand (27, 10, 5, 3), then confirm with `four_counts`.

Next: [Labeled Boxes, Identical Items](02-labeled-boxes.md).
