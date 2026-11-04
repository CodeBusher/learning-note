# Distinct Items: Set Partitions — Surjections, Exponential Generating Functions, Stirling Numbers

## 11. Distinct items, labeled boxes

### 11.1 Every box nonempty: surjections

Now the items have identities. With no constraint, each of the $k$ items picks one of $n$ boxes: $n^k$ arrangements. Requiring every box to be nonempty means counting **surjections** (onto maps) from items to boxes.

Use inclusion–exclusion as in [§3](02-labeled-boxes.md#3-capacities-by-inclusionexclusion). Let $A_i$ be the arrangements where box $i$ stays empty. If $j$ chosen boxes must all stay empty, the items choose among the other $n-j$ boxes, giving $(n-j)^k$. So

$$
\boxed{\#\text{surjections}=\sum_{j=0}^{n}(-1)^j\binom nj(n-j)^k}.
$$

For $k=4,n=2$: $2^4-2\cdot1^4+0=14$. Of the 16 arrangements in [§1](01-modeling.md#1-the-four-cases-on-one-small-example), only "all in A" and "all in B" leave a box empty.

### 11.2 Fixed occupancies and capacities

If the occupancies are fixed at $(a_1,\ldots,a_n)$, choose which items go to box 1, then box 2, and so on. This gives the **multinomial coefficient**:

$$
\boxed{\frac{k!}{a_1!\cdots a_n!}},
\qquad a_i\ge0,\quad\sum a_i=k.
$$

To enforce each box capacity ≤ $L$, sum this over all allowed occupancy vectors. An **exponential generating function** (EGF) does that sum automatically:

$$
\boxed{
k!\,[x^k]\left(\sum_{j=0}^{L}\frac{x^j}{j!}\right)^n.
}
$$

**Why exponential?** Write each box's options as $\sum_j \frac{x^j}{j!}$. When the $n$ factors are multiplied, the coefficient of $x^k$ is $\sum\frac1{a_1!\cdots a_n!}$ over occupancy vectors summing to $k$. Multiplying by $k!$ turns each term into exactly the multinomial above. The $1/j!$ in each factor takes care of choosing *which* items land in each box. Ordinary generating functions ([§5](03-generating-functions.md#5-what-a-generating-function-encodes)) suit identical items, and exponential ones suit distinct, labeled items.

The same pattern handles other per-box rules:

| Each labeled box holds… | EGF factor per box | Count |
|---|---|---|
| Any number | $\sum_{j\ge0}\frac{x^j}{j!}=e^x$ | $k![x^k]e^{nx}=n^k$ |
| At least 1 | $e^x-1$ | $k![x^k](e^x-1)^n$, the surjections of §11.1 |
| At most $L$ | $\sum_{j=0}^{L}\frac{x^j}{j!}$ | formula above |
| Between $a$ and $b$ | $\sum_{j=a}^{b}\frac{x^j}{j!}$ | $k![x^k]\left(\sum_{j=a}^{b}\frac{x^j}{j!}\right)^n$ |

Compare the table in [§5.2](03-generating-functions.md#52-one-labeled-box-then-n-of-them). It has the same rows, with $x^j$ replaced by $x^j/j!$.

## 12. Distinct items, identical boxes: Stirling and Bell numbers

If the $k$ items are distinct but the boxes are identical, we're splitting a set into unlabeled groups. This is a **set partition**.

### 12.1 From surjections to Stirling numbers

Let $S(k,r)$, a **Stirling number of the second kind**, count the ways to split $k$ distinct items into exactly $r$ **nonempty** unlabeled groups.

Take any surjection onto $r$ labeled boxes and forget the labels. Every box is nonempty and the items are distinct, so no two boxes have the same contents. Each set partition therefore corresponds to exactly $r!$ labeled versions, and

$$
\boxed{S(k,r)=\frac1{r!}\sum_{j=0}^{r}(-1)^j\binom rj(r-j)^k}.
$$

This is the case [§1](01-modeling.md#1-the-four-cases-on-one-small-example) promised, where dividing by $r!$ **is** safe. It failed for identical items ([§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)) because two boxes could hold equal amounts. Distinct items in nonempty boxes rule that out.

### 12.2 The recurrence

Place the newest item either:

1. In one of the $r$ existing groups (in $rS(k-1,r)$ ways); or
2. Alone in a newly formed group (in $S(k-1,r-1)$ ways).

$$
\boxed{S(k,r)=rS(k-1,r)+S(k-1,r-1)}.
$$

Base: $S(0,0)=1$, $S(k,0)=0$ for $k>0$.

Small values:

| $k\backslash r$ | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 1 | | | |
| 2 | 1 | 1 | | |
| 3 | 1 | 3 | 1 | |
| 4 | 1 | 7 | 6 | 1 |
| 5 | 1 | 15 | 25 | 10 |

### 12.3 Counts built from $S(k,r)$

- Exactly $n$ nonempty identical boxes: $S(k,n)$.
- At most $n$ nonempty identical boxes (empty allowed): $\sum_{r=0}^{\min(k,n)}S(k,r)$. For $k=4,n=2$: $1+7=8$, as enumerated in [§1](01-modeling.md#1-the-four-cases-on-one-small-example).
- Unlimited identical boxes: **Bell number** $B_k=\sum_{r=0}^kS(k,r)$.
- $n$ labeled boxes, each nonempty: $n!\ S(k,n)$, the surjections of [§11.1](#111-every-box-nonempty-surjections).

The EGF divides the labeled version by $r!$:

$$
\boxed{\sum_{k\ge0}S(k,r)\frac{x^k}{k!}=\frac{(e^x-1)^r}{r!}}.
$$

**Example: $S(5,3)=25$, three ways.**

- **Recurrence:** $S(5,3)=3S(4,3)+S(4,2)=3\cdot6+7=25$.
- **Inclusion–exclusion:** $\frac1{3!}(243-3\cdot32+3\cdot1-0)=\frac{150}{6}=25$.
- **EGF:** $5![x^5]\frac{(e^x-1)^3}{3!}=25$.

### 12.4 Restricted set partitions

For distinct items in identical boxes with every group size ≤ $L$ and at most $n$ nonempty boxes, the EGF is

$$
\sum_{r=0}^{n}\frac1{r!}\left(\sum_{j=1}^{L}\frac{x^j}{j!}\right)^r.
$$

Extract $k![x^k]$. The factor $1/r!$ removes the order of the $r$ unlabeled groups, which is safe for the reason in [§12.1](#121-from-surjections-to-stirling-numbers). This is a **restricted set partition**, not an integer partition.

### 12.5 Checking every formula

The script computes each count of this chapter two ways and compares both with a brute force that labels every item with a box:

```python
from fractions import Fraction
from itertools import product
from math import comb, factorial
import random


def surjections(k: int, n: int) -> int:
    return sum((-1) ** j * comb(n, j) * (n - j) ** k for j in range(n + 1))


def stirling2_table(k: int) -> list[list[int]]:
    """S[a][r] for 0 <= r <= a <= k, by S(a,r) = r S(a-1,r) + S(a-1,r-1)."""
    S = [[0] * (k + 1) for _ in range(k + 1)]
    S[0][0] = 1
    for a in range(1, k + 1):
        for r in range(1, a + 1):
            S[a][r] = r * S[a - 1][r] + S[a - 1][r - 1]
    return S


def egf_count(k: int, n: int, lo: int, hi: int) -> int:
    """k! [x^k] (sum_{j=lo..hi} x^j / j!)^n with exact fractions."""
    box = [Fraction(1, factorial(j)) if lo <= j <= hi else Fraction(0)
           for j in range(k + 1)]
    poly = [Fraction(1)] + [Fraction(0)] * k
    for _ in range(n):
        poly = [sum(poly[i] * box[t - i] for i in range(t + 1))
                for t in range(k + 1)]
    return int(poly[k] * factorial(k))


def brute(k: int, n: int, lo: int, hi: int) -> tuple[int, int]:
    """(labeled count, identical-box count) with every box size in [lo, hi]."""
    labeled, groupings = 0, set()
    for f in product(range(n), repeat=k):
        if all(lo <= f.count(b) <= hi for b in range(n)):
            labeled += 1
            groupings.add(frozenset(
                frozenset(i for i in range(k) if f[i] == b) for b in range(n)))
    return labeled, len(groupings)


def main():
    S = stirling2_table(6)
    assert S[5][3] == 25 and S[4][2] == 7
    assert surjections(4, 2) == 14
    assert surjections(5, 3) == 3 * 2 * 1 * S[5][3] == 150
    assert sum(S[4]) == 15  # Bell number B_4
    rng = random.Random(5)
    for _ in range(150):
        k, n = rng.randint(0, 6), rng.randint(0, 4)
        lo = rng.randint(0, 2)
        hi = rng.randint(lo, 4)
        labeled, unlabeled = brute(k, n, lo, hi)
        assert egf_count(k, n, lo, hi) == labeled
        if lo >= 1:  # nonempty boxes: each grouping has n! labelings
            assert labeled == factorial(n) * unlabeled
        labeled_onto, unlabeled_onto = brute(k, n, 1, k)
        assert surjections(k, n) == labeled_onto
        assert (S[k][n] if n <= k else 0) == unlabeled_onto


if __name__ == "__main__":
    main()
```

The Stirling table costs $O(k^2)$ time and space; `egf_count` costs $O(nk^2)$ fraction operations.

## Pitfalls and practice

1. **Dividing by $n!$ when boxes may be empty.** Two empty boxes have equal contents, so the labeled versions are fewer than $n!$. Sum $S(k,r)$ over $r$ instead.
2. **Forgetting $k!$ when reading an EGF.** The count is $k![x^k]$, not $[x^k]$.
3. **Ordinary GF for distinct items.** $(1+x+\cdots)^n$ counts occupancy vectors, not which item went where.
4. **$S(0,0)=1$ but $S(k,0)=0$ for $k>0$.** Start the recurrence from these.

Practice: number of onto functions; partition a set into $k$ nonempty subsets; Bell numbers; assign $k$ distinct tasks to $n$ workers with each worker getting at most $L$ tasks.

Next: [Synthesis](06-synthesis.md).
