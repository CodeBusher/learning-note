# Constraints on Part Sizes — Allowed Sizes, Multiplicity Caps, Distinct Parts

## 19. Allowed, forbidden, parity, and colored parts

Items and boxes are still identical, but now the restriction is on which part sizes appear and how often. Coin change with coins $S$ is exactly this: partitions whose parts lie in $S$.

| Constraint | Generating function |
|---|---|
| Only sizes in $S$, unlimited | $\prod_{i\in S}(1-x^i)^{-1}$ |
| Only sizes in $S$, at most once | $\prod_{i\in S}(1+x^i)$ |
| All parts odd | $\prod_{i\ge1}(1-x^{2i-1})^{-1}$ |
| All parts even | $\prod_{i\ge1}(1-x^{2i})^{-1}$ |
| Parts between $a$ and $b$ | $\prod_{i=a}^{b}(1-x^i)^{-1}$ |
| Forbid sizes in $T$ | $\prod_{i\ge1,\ i\notin T}(1-x^i)^{-1}$ |
| Each size $i$ has $c_i$ distinguishable colors | $\prod_i(1-x^i)^{-c_i}$ |

Only sizes $i\le k$ matter for extracting $[x^k]$.

**Even parts:** if $k$ is odd the answer is zero; if $k=2t$ the unrestricted count is $p(t)$ (divide every part by 2).

**Euler's identity.** Partitions of $k$ into distinct parts are as many as partitions into odd parts. For $k=5$: $(5),(4,1),(3,2)$ and $(5),(3,1,1),(1,1,1,1,1)$.

$$
\prod_{i\ge1}(1+x^i)
=\prod_{i\ge1}\frac{1-x^{2i}}{1-x^i}
=\prod_{i\ge1,\ i\ \mathrm{odd}}\frac1{1-x^i}.
$$

Every even factor $1-x^{2i}$ in the numerator cancels against the same factor in the denominator. With a finite cutoff ("parts at most $n$") the cancellation is incomplete and the identity fails.

A congruence condition $i\equiv a\pmod b$ is the allowed-set row with $S=\lbrace i>0:i\equiv a\pmod b\rbrace$. Colors give $(1-x^i)^{-c_i}$ because each of the $c_i$ distinguishable types of size $i$ is its own unlimited choice.

## 20. Multiplicity caps and the two-pass DP

Now part size $i$ may occur at most $m$ times: a limit on how many boxes share the same total, not on how full a box is ([§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)). Its factor is:

$$
1+x^i+x^{2i}+\cdots+x^{mi}
=\boxed{\frac{1-x^{(m+1)i}}{1-x^i}}.
$$

### 20.1 Direct recurrence

Let $Q(i,j)$ count ways using allowed sizes up to $i$, with at most $m$ copies of each size:

$$
Q(i,j)=\sum_{r=0}^{\min(m,\lfloor j/i\rfloor)}Q(i-1,j-ri).
$$

Evaluated directly this costs $O(nkm)$ time.

### 20.2 Sliding-sum derivation

Write the same equation for $j-i$:

$$
Q(i,j-i)=\sum_{r=1}^{m+1}Q(i-1,j-ri).
$$

Subtract to cancel the overlapping terms:

$$
\boxed{
Q(i,j)=Q(i-1,j)+Q(i,j-i)-Q(i-1,j-(m+1)i).
}
$$

A 2D DP now takes $O(nk)$ time.

### 20.3 Two in-place passes

The generating-function view gives the same $O(nk)$ without the 2D table. Multiply by $\frac{1-x^{(m+1)i}}{1-x^i}$ as two separate passes:

- **Pass A, multiply by $1-x^{(m+1)i}$:** `dp[j] -= dp[j-(m+1)i]` needs the old value, so sweep **backward**.
- **Pass B, divide by $1-x^i$:** `dp[j] += dp[j-i]` needs the new value, so sweep **forward**.

Pass B alone would allow any number of copies; pass A planted negative copies that cancel every count above $m$. For $i=3,m=2$: $(1-x^9)(1+x^3+x^6+x^9+\cdots)=1+x^3+x^6$.

Trace for $k=5$, size 1 capped at 2 copies, then size 2 capped at 1:

| Step | `dp[0..5]` |
|---|---|
| Start | `[1,0,0,0,0,0]` |
| Size 1, pass A (shift 3) | `[1,0,0,-1,0,0]` |
| Size 1, pass B | `[1,1,1,0,0,0]` |
| Size 2, pass A (shift 4) | `[1,1,1,0,-1,-1]` |
| Size 2, pass B | `[1,1,2,1,1,0]` |

The negative entries are intermediate coefficients of a polynomial, not counts. The final row says total 4 has one partition, $(2,1,1)$, and total 5 has none: it would need a third 1 or a second 2.

```python
from itertools import product
import random


def bounded_multiplicities(k: int, caps: dict[int, int]) -> int:
    """Partitions of k where size i appears at most caps[i] times."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    dp = [1] + [0] * k
    for size, cap in sorted(caps.items()):
        if size <= 0 or cap < 0:
            raise ValueError("sizes must be positive and caps nonnegative")
        shift = (cap + 1) * size
        for j in range(k, shift - 1, -1):   # pass A: OLD values, backward
            dp[j] -= dp[j - shift]
        for j in range(size, k + 1):        # pass B: NEW values, forward
            dp[j] += dp[j - size]
    return dp[k]


def sliding_2d(k: int, n: int, m: int) -> int:
    """Q(i,j) = Q(i-1,j) + Q(i,j-i) - Q(i-1,j-(m+1)i), sizes 1..n."""
    Q = [[0] * (k + 1) for _ in range(n + 1)]
    Q[0][0] = 1
    for i in range(1, n + 1):
        for j in range(k + 1):
            Q[i][j] = Q[i - 1][j]
            if j >= i:
                Q[i][j] += Q[i][j - i]
            if j >= (m + 1) * i:
                Q[i][j] -= Q[i - 1][j - (m + 1) * i]
    return Q[n][k]


def brute(k: int, caps: dict[int, int]) -> int:
    sizes = list(caps)
    return sum(1 for counts in product(*(range(caps[s] + 1) for s in sizes))
               if sum(c * s for c, s in zip(counts, sizes)) == k)


def main():
    assert bounded_multiplicities(4, {1: 2, 2: 1}) == 1
    assert bounded_multiplicities(5, {1: 2, 2: 1}) == 0
    assert bounded_multiplicities(5, {1: 2, 2: 1, 3: 2}) == 2  # 3+2, 3+1+1
    assert bounded_multiplicities(6, {3: 0}) == 0              # cap 0 forbids 3
    rng = random.Random(8)
    for _ in range(300):
        k, n, m = rng.randint(0, 12), rng.randint(1, 5), rng.randint(0, 3)
        expected = brute(k, {i: m for i in range(1, n + 1)})
        assert bounded_multiplicities(k, {i: m for i in range(1, n + 1)}) == expected
        assert sliding_2d(k, n, m) == expected
        caps = {rng.randint(1, 6): rng.randint(0, 3) for _ in range(3)}
        assert bounded_multiplicities(k, caps) == brute(k, caps)


if __name__ == "__main__":
    main()
```

Time $O(sk)$ for $s$ capped sizes, space $O(k)$. The two passes may run in either order, since multiplication commutes; the direction **within** each pass may not change. The same code covers a separate cap $m_i$ per size, which is `count_bounded_multiplicities` in [§26](10-toolkit.md#26-code-catalog-and-tests):

$$
F(x)=\prod_{i\in S}\frac{1-x^{(m_i+1)i}}{1-x^i}.
$$

## 21. Distinct parts and gap restrictions

### 21.1 Each part size can be used at most once

The factor is $1+x^i$, and for allowed sizes $S$:

$$
\boxed{F(x)=\prod_{i\in S}(1+x^i)}.
$$

This is the backward 0/1 update of [§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates), once per allowed size: `count_distinct_parts` in [§26](10-toolkit.md#26-code-catalog-and-tests).

$\prod_{i=1}^n(1+x^i)$ bounds the **largest part** by $n$. It does **not** mean "at most $n$ distinct parts of any size"; that count comes next.

### 21.2 Exactly $r$ distinct positive parts

Take $(4,1)$, a partition of 5 into 2 distinct parts. Subtract the staircase $(1,0)$ to get $(3,1)$: now parts may be equal. In general, strictly decreasing $\lambda_1>\cdots>\lambda_r\ge1$ minus $(r-1,\ldots,1,0)$ is a weakly decreasing partition into exactly $r$ positive parts, and the step reverses. Subtracting one more from each part ([§17.1](07-box-constraints.md#171-exactly-r-nonempty-boxes)) removes $r(r+1)/2$ in total:

$$
\boxed{D_{=r}(k)=p_{\le r}\left(k-\frac{r(r+1)}2\right)}.
$$

Equivalently,

$$
\sum_{k\ge0}D_{=r}(k)x^k
=\frac{x^{r(r+1)/2}}{\prod_{i=1}^r(1-x^i)}.
$$

Example $k=5,r=2$: $(4,1)$ and $(3,2)$, so 2.

At most $r$ distinct parts: sum $D_{=t}(k)$ for $0\le t\le r$.

If all parts must be ≤ $L$ as well, the GF is

$$
x^{r(r+1)/2}{L\brack r}_x.
$$

### 21.3 Consecutive parts differ by at least $d$

For exactly $r$ positive parts with

$$
\lambda_1-\lambda_2\ge d,\ldots,\lambda_{r-1}-\lambda_r\ge d,
$$

subtract the staircase $(d(r-1),d(r-2),\ldots,0)$. Each gap shrinks by exactly $d$, so the result is an ordinary partition into exactly $r$ positive parts, and adding the staircase back reverses it:

$$
\boxed{\text{answer}
=p_{=r}\left(k-d\frac{r(r-1)}2\right)}.
$$

$d=1$ recovers distinct parts, since $p_{=r}(k-\tfrac{r(r-1)}2)=p_{\le r}(k-\tfrac{r(r+1)}2)$.

## 22. Multiplicity sets and two-variable generating functions

### 22.1 Allowed multiplicity sets

Every multiplicity rule so far is one factor per size: list the allowed copy counts $M_i$ of size $i$ and add one term per count.

$$
\boxed{H_i(x)=\sum_{r_i\in M_i}x^{r_ii}},
\qquad
\boxed{F(x)=\prod_iH_i(x)},
$$

where $M_i$ is the allowed set of nonnegative multiplicities.

Examples:

- **At least $\ell_i$ copies:** $x^{\ell_i i}/(1-x^i)$.
- **Exactly $t_i$ copies:** $x^{t_i i}$.
- **Between $\ell_i$ and $u_i$ copies:** $x^{\ell_i i}(1-x^{(u_i-\ell_i+1)i})/(1-x^i)$.
- **Only an even number of copies:** $1/(1-x^{2i})$.
- **Only an odd number of copies:** $x^i/(1-x^{2i})$.
- **At most $m_i$ copies:** $(1-x^{(m_i+1)i})/(1-x^i)$.

### 22.2 Exactly $t$ boxes with occupancy $s$

"Exactly $t$ boxes hold $s$ items" says the part $s$ has multiplicity exactly $t$: its factor is $x^{ts}$, and no other factor may produce $s$. Adding a limit on the number of boxes as well needs the second variable of [§22.3](#223-track-a-second-statistic).

### 22.3 Track a second statistic

To track **both** the total $k$ and the number $r$ of positive parts (occupied original boxes), use an auxiliary variable $y$:

$$
\boxed{
F(x,y)=\prod_{i\ge1}\frac1{1-yx^i}
}.
$$

Then $[x^ky^r]F(x,y)$ counts partitions of $k$ into exactly $r$ positive parts. Each copy of size $i$ contributes $x^iy$, which increases the item total by $i$ and the occupied-box count by 1.

If size $i$ has a multiplicity limit $m_i$, replace its factor with $\sum_{t=0}^{m_i}y^t x^{ti}$.

To track **exactly $r$ distinct sizes used** (rather than number of parts), use a different meaning for $y$:

$$
\boxed{
\prod_{i\ge1}\left(1+y(x^i+x^{2i}+\cdots)\right)
=\prod_{i\ge1}\left(1+\frac{yx^i}{1-x^i}\right).
}
$$

Here one $y$ is contributed when a size is used at least once, no matter how many copies.

In code, a second variable is a second DP index, as `dp[b][t]` in [§18.1](07-box-constraints.md#181-every-box-has-capacity-at-most-l).

## Pitfalls and practice

1. **Cap on copies vs cap on a box.** "Size 2 at most once" is $1+x^2$; "each box at most 2" is the rectangle of [§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds).
2. **Swapping a pass direction in the two-pass DP.** Pass A backward, pass B forward; otherwise the cancellation fails.
3. **Treating negative intermediate values as a bug.** They are coefficients of $1-x^{(m+1)i}$ times the old polynomial; the final values are counts.
4. **Euler's identity with a cutoff.** Distinct parts $\le n$ and odd parts $\le n$ are not equinumerous.
5. **$\prod_{i\le n}(1+x^i)$ read as "at most $n$ parts".** It bounds the largest part.

Practice: coin change with limited coins of each type; partitions into distinct parts; partitions into odd parts; Rogers–Ramanujan-type counts (parts differing by at least 2); count subsets with a given sum.

Next: [Advanced Topics](09-advanced-topics.md).
