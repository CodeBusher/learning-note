# Advanced Topics — Pentagonal Numbers, Burnside's Lemma, Other Partition Families

## 23. Unrestricted partition numbers and faster recurrences

Computing $p(0),\ldots,p(k)$ with the coin-change DP of [§10.2](04-integer-partitions.md#102-the-2d-and-1d-recurrences) costs $O(k^2)$, since every size up to $k$ gets a pass. When $n\ge k$ the number of boxes no longer matters:

$$
p_{\le n}(k)=p(k).
$$

The unrestricted generating function is

$$
\boxed{\sum_{k\ge0}p(k)x^k=\prod_{i\ge1}(1-x^i)^{-1}}.
$$

### 23.1 Euler's pentagonal-number recurrence

Define generalized pentagonal numbers

$$
g_m^-=\frac{m(3m-1)}2,\qquad
g_m^+=\frac{m(3m+1)}2.
$$

Then

$$
\boxed{
p(k)=\sum_{m\ge1}(-1)^{m-1}
\left(p(k-g_m^-)+p(k-g_m^+)\right),
}
$$

with $p(0)=1$ and $p(t)=0$ for $t<0$. The pentagonal numbers are $1,2,5,7,12,15,\ldots$, so

$$
p(6)=p(5)+p(4)-p(1)-p(-1)=7+5-1-0=11.
$$

**Why.** Euler's pentagonal number theorem says $\prod_{i\ge1}(1-x^i)=1+\sum_{m\ge1}(-1)^m\left(x^{g_m^-}+x^{g_m^+}\right)$: almost everything cancels. Multiply it by $\sum p(k)x^k=\prod(1-x^i)^{-1}$; the product is 1, so for $k>0$ the coefficient of $x^k$ is 0, and solving for $p(k)$ gives the recurrence. Only $O(\sqrt k)$ pentagonal numbers are $\le k$, so all of $p(0),\ldots,p(k)$ take $O(k\sqrt k)$ time and $O(k)$ space (`unrestricted_partition_numbers` in [§26](10-toolkit.md#26-code-catalog-and-tests)).

### 23.2 Asymptotic formulas (not exact)

Hardy–Ramanujan, as $k\to\infty$:

$$
\boxed{p(k)\sim\frac{1}{4k\sqrt3}
\exp\left(\pi\sqrt{\frac{2k}{3}}\right)}.
$$

If the number of boxes $n$ is **fixed** and $k\to\infty$:

$$
\boxed{p_{\le n}(k)\sim\frac{k^{n-1}}{n!(n-1)!}}.
$$

They describe growth only; an exact answer still needs the DP. ($p(100)=190{,}569{,}292$, while the first formula gives about $1.99\times10^8$.)

## 24. Burnside's lemma for identical boxes

Identical boxes mean: two labeled vectors $(a_1,\ldots,a_n)$ are the same arrangement if some permutation of the boxes turns one into the other. The set of all vectors reachable from one vector by permuting is its **orbit**; we want the number of orbits. [§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes) showed that orbits have different sizes, which is why dividing by $n!$ fails. Burnside's lemma fixes the division by counting, for each permutation, the vectors it leaves unchanged.

By **Burnside's lemma**,

$$
\#\text{orbits}
=\frac1{n!}\sum_{\sigma\in S_n}\#\{\text{vectors fixed by }\sigma\}.
$$

If permutation $\sigma$ has cycles of lengths $\ell_1,\ldots,\ell_t$, a vector fixed by $\sigma$ must have the same occupancy within each cycle. Its fixed-vector generating function is

$$
\prod_{h=1}^{t}\frac1{1-x^{\ell_h}}.
$$

Hence

$$
\boxed{
p_{\le n}(k)
=\frac1{n!}\sum_{\sigma\in S_n}
[x^k]\prod_{\ell\in\operatorname{cycles}(\sigma)}
\frac1{1-x^\ell}.
}
$$

[§16](06-synthesis.md#16-one-problem-several-approaches) works $p_{\le3}(5)=(21+3\cdot3+0)/6=5$ by hand. Burnside is slower than the coin-change DP for all permutations, but it is the method that still works when the boxes are equivalent only under rotation (sum over the $n$ rotations instead) or another symmetry group.

```python
from itertools import permutations
from math import factorial
import random


def cycle_lengths(perm: tuple[int, ...]) -> list[int]:
    seen, lengths = set(), []
    for start in range(len(perm)):
        if start not in seen:
            length, i = 0, start
            while i not in seen:
                seen.add(i)
                i = perm[i]
                length += 1
            lengths.append(length)
    return lengths


def burnside(k: int, n: int) -> int:
    total = 0
    for perm in permutations(range(n)):
        fixed = [1] + [0] * k               # [x^j] of prod 1/(1 - x^len)
        for length in cycle_lengths(perm):
            for j in range(length, k + 1):
                fixed[j] += fixed[j - length]
        total += fixed[k]
    assert total % factorial(n) == 0
    return total // factorial(n)


def coin_change(k: int, n: int) -> int:
    dp = [1] + [0] * k
    for size in range(1, n + 1):
        for j in range(size, k + 1):
            dp[j] += dp[j - size]
    return dp[k]


def main():
    assert burnside(5, 3) == 5
    rng = random.Random(9)
    for _ in range(60):
        k, n = rng.randint(0, 15), rng.randint(0, 5)
        assert burnside(k, n) == coin_change(k, n)


if __name__ == "__main__":
    main()
```

Time $O(n!\,nk)$: fine for checking, useless for large $n$.

## 25. Other partition families

Exactly $r$ parts ([§17](07-box-constraints.md#17-number-of-nonempty-boxes)), rectangles ([§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)), odd, colored, strict and gap-restricted parts ([§19](08-part-size-constraints.md#19-allowed-forbidden-parity-and-colored-parts)–[§21](08-part-size-constraints.md#21-distinct-parts-and-gap-restrictions)) and set partitions ([§12](05-set-partitions.md#12-distinct-items-identical-boxes-stirling-and-bell-numbers)) are covered earlier. Families beyond them:

| Family | What changes | Typical technique |
|---|---|---|
| **Self-conjugate partitions** | Ferrers diagram equals its transpose | Bijection with distinct odd parts (§25.1) |
| **Vector partitions** | Parts have vector weights (several resources) | DP over a multidimensional coefficient array |
| **Plane partitions** | Two-dimensional weakly decreasing arrays | MacMahon's product (§25.2) |
| **Rotation-equivalent allocations** | A different symmetry group on the boxes | Burnside / Pólya ([§24](#24-burnsides-lemma-for-identical-boxes)) |
| **Weighted partitions** | Each part carries a weight or probability | Weighted generating functions |

### 25.1 Self-conjugate ↔ distinct odd parts

Peel a self-conjugate Ferrers diagram into diagonal hooks: the first row plus the first column, then the same for what remains. Because the diagram is symmetric, each hook has equal arms, so its length is odd, and each hook is shorter than the one outside it. The hook lengths are **distinct odd integers**, and they determine the diagram, so the number of self-conjugate partitions of $k$ equals the number of partitions of $k$ into distinct odd parts:

$$
\prod_{i\ge1}(1+x^{2i-1}).
$$

### 25.2 Plane partitions (a different dimension)

An ordinary partition is one nonincreasing list. A **plane partition** is a two-dimensional array of nonnegative entries that are weakly decreasing along rows and columns. It is *not* the same as moving identical balls among ordinary boxes. If the array has at most $a$ rows, $b$ columns, and entry height at most $c$, MacMahon's boxed plane-partition formula counts all such arrays:

$$
\prod_{i=1}^{a}\prod_{j=1}^{b}\prod_{h=1}^{c}
\frac{i+j+h-1}{i+j+h-2}.
$$

The 1D partition DP does not apply to it.

## Pitfalls and practice

1. **Pentagonal signs.** The pattern is $+,+,-,-,+,+,\ldots$: both pentagonal numbers of index $m$ share the sign $(-1)^{m-1}$.
2. **Using an asymptotic formula for an exact count.** Hardy–Ramanujan is off by about 5% at $k=100$.
3. **Dividing by the group size instead of averaging fixed points.** Burnside needs the fixed-point sum.
4. **Treating a plane partition as a partition with more boxes.** It is a two-dimensional object with its own formulas.

Practice: partition numbers modulo a prime for $k$ up to $10^5$; necklaces of $n$ beads in $c$ colors under rotation (Burnside); count self-conjugate partitions.

Next: [Toolkit](10-toolkit.md).
