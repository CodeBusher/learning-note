# Identical Boxes: Integer Partitions — Ferrers Diagrams and Coin-Change DP

## 8. Why the stick method fails for identical boxes

Put $k=5$ identical items into $n=3$ identical boxes. Stars and bars counts *ordered* vectors. With identical boxes, $(2,1,2)$, $(1,2,2)$ and $(2,2,1)$ are the same arrangement. You can't fix this by dividing by $n!$, because different arrangements have different numbers of orderings: $(5,0,0)$ has 3, while $(4,1,0)$ has 6. For $k=5,n=3$ there are 21 vectors but only 5 arrangements, and $21/3!$ is not even an integer.

The fix is to pick one **canonical representative** for each arrangement. Sort the occupancies in decreasing order:

$$
\lambda_1\ge\lambda_2\ge\cdots\ge\lambda_n\ge0,
\qquad
\lambda_1+\cdots+\lambda_n=k.
$$

Drop the zeros and what remains is an **integer partition** of $k$: an unordered sum of positive integers, called its **parts**. Each nonempty box is one part, and the empty boxes are padding.

For $k=5$ identical items in $n=3$ identical boxes:

$$
(5,0,0),\ (4,1,0),\ (3,2,0),\ (3,1,1),\ (2,2,1)\quad\Rightarrow\quad 5.
$$

**Notation.** Write $p_{\le n}(k)$ for the number of partitions of $k$ into *at most $n$* positive parts, which is the number of ways to place $k$ identical items in $n$ identical boxes. Write $p_{=n}(k)$ when exactly $n$ boxes must be nonempty, and $p(k)$ when there is no limit on the number of boxes. Above, $p_{\le3}(5)=5$.

**Boundary values.** Read each one as a statement about boxes:

- $p_{\le n}(0)=1$ for any $n\ge0$. There is exactly one way to place zero items: leave every box empty. This is the *empty partition*, with no parts.
- $p_{\le0}(k)=0$ for $k>0$. With no boxes, a positive number of items can't be placed.
- $p_{\le n}(k)=0$ for $k<0$. This lets recurrences that subtract from $k$ run past zero safely.

## 9. Ferrers diagrams and conjugation

Draw a partition as rows of dots, one row per part, longest first. The partition $(4,2,1)$ of $7$:

```text
● ● ● ●
● ●
●
```

Read the **column heights** instead of the row lengths: $(3,2,1,1)$. This is the **conjugate** partition. The transformation is reversible: conjugating twice gives back the original.

- The number of rows in the original diagram becomes the largest row in the conjugate.
- The largest original row becomes the number of rows in the conjugate.
- The number of dots $k$ stays unchanged.

Therefore:

$$
\boxed{\#\{\text{partitions of }k\text{ into }\le n\text{ parts}\}
=\#\{\text{partitions of }k\text{ with parts }\le n\}.}
$$

**Why bother?** The box question limits the **number of parts**, one part per nonempty box. Generating functions ([§6](03-generating-functions.md#6-products-of-different-factors)) are easiest to build by limiting the **allowed part sizes**, with one factor per size. Conjugation proves the two counts are equal, so we may count the second.

**Warning:** this swaps one restriction for the other, and nothing more. If the boxes also have capacity $L$, we must enforce *both* "at most $n$ parts" and "largest part ≤ $L$". That is a partition inside an $n\times L$ rectangle ([§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)). Allowing only sizes $1,\ldots,n$ does not enforce the capacity.

## 10. Counting partitions: generating function and DP

### 10.1 The generating function

After conjugation, we count partitions whose parts are all in $\{1,\ldots,n\}$. Each size $i$ may occur $0,1,2,\ldots$ times, contributing the factor $\frac1{1-x^i}$ from [§6](03-generating-functions.md#6-products-of-different-factors):

$$
\boxed{F_n(x)=\prod_{i=1}^n\frac1{1-x^i}},
\qquad
\boxed{p_{\le n}(k)=[x^k]F_n(x)}.
$$

This is the coin product from [§6](03-generating-functions.md#6-products-of-different-factors): **identical items in $n$ identical boxes is the same as making change with coins $1,\ldots,n$**. So the hand expansion there already gives $p_{\le3}(5)=5$ and $p_{\le3}(6)=7$.

Each factor stands for **a part size** after conjugation, **not one of the original boxes**. Compare [§5.2](03-generating-functions.md#52-one-labeled-box-then-n-of-them), where there was one factor per labeled box.

### 10.2 The 2D and 1D recurrences

Let $P(i,j)$ count partitions of total $j$ using only part sizes $1,\ldots,i$.

Split into mutually exclusive cases:

1. Use **zero** parts of size $i$ → $P(i-1,j)$.
2. Use **at least one** part of size $i$ → remove one $i$, leaving $P(i,j-i)$; $i$ remains available.

$$
\boxed{P(i,j)=P(i-1,j)+P(i,j-i)}.
$$

Base conditions: $P(i,0)=1$, $P(0,j>0)=0$, and a negative total contributes zero.

**Compressing to one array.** Process $i$ in increasing order, then $j$ in increasing order. Before `dp[j]` is changed it still holds $P(i-1,j)$, and `dp[j-i]` has already become $P(i,j-i)$. This is the forward row of the table in [§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates), applied once per factor $\frac1{1-x^i}$.

Trace for $k=6,n=3$, coefficients indexed by $j=0,1,\ldots,6$:

| Processed sizes | `dp[0..6]` | Example update |
|---|---|---|
| None | `[1,0,0,0,0,0,0]` | |
| $1$ | `[1,1,1,1,1,1,1]` | `dp[j] += dp[j-1]`: one way, all 1s |
| $1,2$ | `[1,1,2,2,3,3,4]` | `dp[4] = 1 + dp[2] = 1 + 2`: $(1,1,1,1)$, $(2,1,1)$, $(2,2)$ |
| $1,2,3$ | `[1,1,2,3,4,5,7]` | `dp[6] = 4 + dp[3] = 4 + 3` |

The rows are the partial products $1$, $\frac1{1-x}$, $D(x)$ and $F_3(x)$ from [§6.1](03-generating-functions.md#61-expand-by-hand). In the last row, `dp[3]` was already updated to 3 when `dp[6]` read it, so the 3 counts partitions of 3 that may themselves use a 3: $(3)$, $(2,1)$, $(1,1,1)$, each with one more 3 added.

```python
import random


def partitions_2d(k: int, n: int) -> int:
    """P(i, j) table: totals j using part sizes 1..i."""
    if k < 0 or n < 0:
        raise ValueError("k and n must be nonnegative")
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            dp[i][j] = dp[i - 1][j]          # no part of size i
            if j >= i:
                dp[i][j] += dp[i][j - i]     # at least one part of size i
    return dp[n][k]


def partitions_at_most_boxes(k: int, n: int) -> int:
    """k identical items into n identical boxes, empties allowed."""
    if k < 0 or n < 0:
        raise ValueError("k and n must be nonnegative")
    dp = [1] + [0] * k
    for i in range(1, min(n, k) + 1):        # sizes above k never fit
        for j in range(i, k + 1):            # increasing: current row
            dp[j] += dp[j - i]
    return dp[k]


def by_boxes(k: int, n: int, memo=None) -> int:
    """Section 10.3: p(k, <=n) = p(k, <=n-1) + p(k-n, <=n)."""
    memo = {} if memo is None else memo
    if k == 0:
        return 1
    if k < 0 or n == 0:
        return 0
    if (k, n) not in memo:
        memo[k, n] = by_boxes(k, n - 1, memo) + by_boxes(k - n, n, memo)
    return memo[k, n]


def brute(k: int, n: int) -> int:
    """List nonincreasing sequences of at most n positive parts."""
    def go(remaining: int, slots: int, largest: int) -> int:
        if remaining == 0:
            return 1
        if slots == 0:
            return 0
        return sum(go(remaining - part, slots - 1, part)
                   for part in range(1, min(remaining, largest) + 1))
    return go(k, n, k)


def main():
    assert partitions_at_most_boxes(5, 3) == 5
    assert partitions_at_most_boxes(6, 3) == 7
    assert partitions_at_most_boxes(0, 0) == 1
    assert partitions_at_most_boxes(4, 0) == 0
    assert partitions_at_most_boxes(10, 10) == 42   # p(10)
    rng = random.Random(4)
    for _ in range(300):
        k, n = rng.randint(0, 14), rng.randint(0, 8)
        expected = brute(k, n)
        assert partitions_2d(k, n) == expected
        assert partitions_at_most_boxes(k, n) == expected
        assert by_boxes(k, n) == expected


if __name__ == "__main__":
    main()
```

The 2D table takes $O(nk)$ time and space; the 1D version takes $O(k\min(n,k))$ time and $O(k)$ space. The catalog version is `count_partitions` ([§26](10-toolkit.md#26-code-catalog-and-tests)).

### 10.3 A second recurrence: split on the boxes

Instead of splitting on part sizes, split on the boxes directly. Either some box is empty, so at most $n-1$ boxes are used, or all $n$ boxes are nonempty. In the second case, remove one item from each box (the shift from [§2.2](02-labeled-boxes.md#22-every-box-nonempty-and-lower-bounds)), which leaves a partition of $k-n$ into at most $n$ parts:

$$
\boxed{p_{\le n}(k)=p_{\le n-1}(k)+p_{\le n}(k-n)}.
$$

So $p_{\le3}(5)=p_{\le2}(5)+p_{\le3}(2)=3+2=5$.

This is the conjugate of [§10.2](#102-the-2d-and-1d-recurrences). "Some box is empty" in the box picture is "no part of size $n$" in the part-size picture, and removing one item from each of $n$ boxes is removing one part of size $n$.

For large $k$ with no limit on boxes, a faster recurrence exists ([§23](09-advanced-topics.md#23-unrestricted-partition-numbers-and-faster-recurrences)). [§24](09-advanced-topics.md#24-burnsides-lemma-for-identical-boxes) derives $p_{\le n}(k)$ a third way, by averaging labeled arrangements over box permutations.

## Pitfalls and practice

1. **Dividing labeled counts by $n!$.** Arrangements have different numbers of orderings ([§8](#8-why-the-stick-method-fails-for-identical-boxes)).
2. **One factor per box, or looping $j$ outside $i$.** With the total in the outer loop, the DP counts ordered sums (compositions), not partitions. Factors are per part *size* (§10.1).
3. **Conjugation swaps one bound, not both** (§9).
4. **$p_{\le n}(0)=1$.** The empty partition counts once, even with $n=0$.

Practice: coin change II; count partitions of $k$ into at most $n$ parts; the number of ways to write $k$ as a sum of positive integers (unordered).

Next: [Distinct Items: Set Partitions](05-set-partitions.md).
