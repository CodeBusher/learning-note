# Constraints on the Boxes — Nonempty Counts and Capacities

## 17. Number of nonempty boxes

Back to identical items in identical boxes ([§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)). A restriction on the boxes bounds the number of parts (nonempty boxes) or the largest part (the fullest box).

### 17.1 Exactly $r$ nonempty boxes

Five items in exactly three nonempty boxes: $(3,1,1)$ and $(2,2,1)$. Each positive occupancy is ≥1, so remove one item from each of the $r$ occupied boxes; what is left is $(2,0,0)$ and $(1,1,0)$, the partitions of $k-r=2$ into at most 3 parts:

$$
\boxed{p_{=r}(k)=p_{\le r}(k-r)\quad(k\ge r)}.
$$

Also $p_{=r}(k)=p_{\le r}(k)-p_{\le r-1}(k)$, and the generating function is the shifted product:

$$
\boxed{\sum_{k\ge0}p_{=r}(k)x^k=\frac{x^r}{\prod_{i=1}^r(1-x^i)}}.
$$

### 17.2 At least $r$ nonempty boxes

If there are at most $n$ available boxes, sum the exact-count variants:

$$
\sum_{t=r}^{\min(n,k)}p_{=t}(k).
$$

For $k=0$, only $t=0$ is possible.

## 18. Box capacities and occupancy bounds

### 18.1 Every box has capacity at most $L$

Now we require

$$
\lambda_1\ge\cdots\ge\lambda_n\ge0,\quad
\lambda_1\le L,\quad
\sum\lambda_i=k.
$$

In Ferrers-diagram language, the partition fits in an **$n\times L$ rectangle**. Its generating function is the **Gaussian binomial coefficient**:

$$
\boxed{
\sum_{k\ge0}R_{n,L}(k)x^k
={n+L\brack n}_x
=\prod_{j=1}^{n}\frac{1-x^{L+j}}{1-x^j}.
}
$$

Here ${a\brack b}_x$ is a polynomial, **not** an ordinary binomial coefficient. Only coefficients through total degree $nL$ can be nonzero.

Example: $k=4,n=3,L=2$: $(2,2,0)$ and $(2,1,1)$, so answer 2.

**A DP with two counters.** Let `dp[b][t]` count partitions of total $t$ into exactly $b$ parts, using the sizes processed so far. For each **size** $i=1,\ldots,L$, sweep $b$ upward and add `dp[b-1][t-i]`: the read entry is already updated, so size $i$ may be used several times (the forward rule of [§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates), now on the box counter). For $k=4,n=3,L=2$, rows $b=0..3$, columns $t=0..4$:

| After size | `dp[0]` | `dp[1]` | `dp[2]` | `dp[3]` |
|---|---|---|---|---|
| 1 | `1 0 0 0 0` | `0 1 0 0 0` | `0 0 1 0 0` | `0 0 0 1 0` |
| 2 | `1 0 0 0 0` | `0 1 1 0 0` | `0 0 1 1 1` | `0 0 0 1 1` |

Column $t=4$ sums to $0+0+1+1=2$: $(2,2)$ in `dp[2]`, $(2,1,1)$ in `dp[3]`. Code: `count_rectangle` in [§26](10-toolkit.md#26-code-catalog-and-tests), time $O(Lnk)$, space $O(nk)$.

**A recursion without the box counter.** Split on whether a part of size $L$ is used:

$$
\boxed{G_{n,L}(x)=G_{n,L-1}(x)+x^L G_{n-1,L}(x)}
$$

with $G_{0,L}=G_{n,0}=1$: either no part equals $L$, or remove one part $L$ (and its row). Extract $[x^k]$; computing coefficient arrays this way costs $O(nLk)$ too, but needs no second counter.

### 18.2 Exactly $r$ occupied boxes, occupancy in $[a,b]$

Assume $1\le a\le b$. Subtract $a$ from every one of the $r$ positive occupancies. The remainder is a partition inside an $r\times (b-a)$ rectangle:

$$
\boxed{\text{answer}=R_{r,b-a}(k-ar)}.
$$

For example $k=5,r=3,[a,b]=[1,3]$: $(3,1,1)$ and $(2,2,1)$, answer 2.

If **at most $n$** occupied boxes with $[a,b]$ bounds, sum the last expression over $r=0,\ldots,n$. If zero-occupancy boxes are permitted, they do not count as occupied.

## Pitfalls and practice

1. **$p_{=r}(k)$ with $k<r$.** It is 0; with $r=0$ it is 1 only for $k=0$.
2. **Capping part sizes instead of box totals.** $\prod_{i\le n}(1+x^i+x^{2i})$ caps how often a size repeats, not how full a box is ([§27](10-toolkit.md#27-worked-examples-and-interview-checklist), example A).
3. **Shifting by $a$ when zero is allowed.** Only occupied boxes take the shift; empty boxes are not "occupied with fewer than $a$".
4. **Forgetting both bounds after conjugation.** Capacity $L$ and $n$ boxes need the rectangle, not one bound.

Practice: partitions of $k$ into exactly $r$ parts; partitions fitting in an $n\times L$ box; split $k$ identical tasks among at most $n$ identical machines, each taking between $a$ and $b$.

Next: [Constraints on Part Sizes](08-part-size-constraints.md).
