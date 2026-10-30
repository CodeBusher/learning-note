# Counting Distributions, Integer Partitions, Generating Functions, and Knapsack DP

> Comprehensive algorithm study guide | Mathematics, derivations, Python implementations, worked examples, and problem variants
>
> **Core problem:** Distribute `k` items into `n` boxes, possibly leaving boxes empty. The answer depends first on which objects are distinguishable, then on constraints (capacities, nonempty boxes, multiplicities, parity, order, and more).

**Scope.** There is no finite catalog of *every* conceivable research variant: new constraints define new counting problems. This guide covers the main classical families and a reusable framework to solve many additional variations. In particular, *bounded occurrences of a part size* and *bounded capacity of each original box* are different restrictions. Keep their meanings separate.

## Contents

1. [Model the problem before counting](#1-model-the-problem-before-counting)
2. [Four balls-and-boxes cases](#2-four-balls-and-boxes-cases)
3. [Integer partitions and conjugation](#3-integer-partitions-and-conjugation)
4. [Generating functions from first principles](#4-generating-functions-from-first-principles)
5. [Expand a generating function by hand](#5-expand-a-generating-function-by-hand)
6. [Derive 2D and 1D partition DP](#6-derive-2d-and-1d-partition-dp)
7. [Derive iteration directions algebraically](#7-derive-iteration-directions-algebraically)
8. [Bounded multiplicities: two-pass in-place DP](#8-bounded-multiplicities-two-pass-in-place-dp)
9. [Original-box constraints: exact boxes and capacities](#9-original-box-constraints-exact-boxes-and-capacities)
10. [Distinct parts and gap restrictions](#10-distinct-parts-and-gap-restrictions)
11. [Odd, even, permitted, forbidden, and colored parts](#11-odd-even-permitted-forbidden-and-colored-parts)
12. [Multiplicity, minimum counts, and two-variable functions](#12-multiplicity-minimum-counts-and-two-variable-functions)
13. [Ordered distributions and compositions](#13-ordered-distributions-and-compositions)
14. [Distinct items: Stirling and Bell numbers](#14-distinct-items-stirling-and-bell-numbers)
15. [Distinct items with labeled-box capacities](#15-distinct-items-with-labeled-box-capacities)
16. [Burnside's lemma for identical boxes](#16-burnsides-lemma-for-identical-boxes)
17. [Unrestricted partition numbers and faster recurrences](#17-unrestricted-partition-numbers-and-faster-recurrences)
18. [Additional advanced partition families](#18-additional-advanced-partition-families)
19. [Algorithm catalog and tested Python code](#19-algorithm-catalog-and-tested-python-code)
20. [Examples, edge cases, and interview checklist](#20-examples-edge-cases-and-interview-checklist)
21. [References](#21-references)

---

## 1. Model the problem before counting

Ask these questions **before** writing any formula:

1. Are the `k` items **identical** (only quantities matter) or **distinct** (each item has its own identity)?
2. Are the `n` boxes **identical** (permuting boxes changes nothing) or **labeled** (Box A and Box B differ)?
3. Can a box be **empty**?
4. Are there **exactly `r` nonempty boxes**, **at most `r`**, or **at least `r`**?
5. Does each box have a lower/upper **occupancy limit**?
6. Are restrictions about each **box's total occupancy** or about the **number of parts of a given size**? These are *not* equivalent.
7. Does order matter? Are there restrictions on sizes, parity, distinctness, gaps, or color?
8. Are we counting combinations or probabilities? For probabilities, different arrangements may have unequal probabilities.

For an identical-item/identical-box problem, represent the occupancies canonically as

$$
\lambda_1\ge\lambda_2\ge\cdots\ge\lambda_n\ge0,
\qquad
\lambda_1+\cdots+\lambda_n=k.
$$

These `\lambda_i` form an **integer partition** padded with zeros. Write `p_{\le n}(k)` for the number of partitions of `k` into *at most `n` positive parts*.

Conventions:

- `p_{\le n}(0)=1` for any `n\ge0`: one empty arrangement.
- `p_{\le0}(k)=0` for `k>0`.
- `p_{\le n}(k)=0` for `k<0`.
- Unless noted, `k,n` and capacities are nonnegative integers.

## 2. Four balls-and-boxes cases

For `k>0` and `n>0` (with normal boundary conventions):

| Items | Boxes | Empty allowed | **All boxes required nonempty** |
|---|---|---|---|
| Distinct | Labeled | `n^k` | `n!\,S(k,n)` |
| Identical | Labeled | `\binom{k+n-1}{n-1}` | `\binom{k-1}{n-1}` if `k\ge n`, else 0 |
| Distinct | Identical | `\sum_{r=1}^{\min(k,n)}S(k,r)` | `S(k,n)` |
| Identical | Identical | `p_{\le n}(k)` | `p_{=n}(k)` |

Here `S(k,r)` is a **Stirling number of the second kind**: the number of ways to partition a set of `k` distinct items into exactly `r` nonempty, unlabeled groups.

**Why the formulas differ**

- **Distinct items/labeled boxes:** each item independently selects one of `n` boxes, giving `n^k`.
- **Identical items/labeled boxes:** solve `x_1+\cdots+x_n=k` with `x_i\ge0` via **stars and bars**; the solution vector's order matters.
- **Distinct items/identical boxes:** a grouping is a set partition, counted by Stirling numbers.
- **Identical items/identical boxes:** an occupancy multiset is an integer partition.

Example: `k=5` identical items, `n=3` identical boxes:

`(5,0,0), (4,1,0), (3,2,0), (3,1,1), (2,2,1)`.

Answer: `p_{\le3}(5)=5`.

**Corner case:** If `k=0`, there is one empty arrangement even with zero boxes. If `n=0<k` there are no valid arrangements. Apply these boundaries explicitly rather than using factorial formulas outside their domain.

## 3. Integer partitions and conjugation

A partition is an unordered sum of positive integers. The partition `(4,2,1)` corresponds to seven dots:

```text
● ● ● ●
● ●
●
```

Read the **column heights** instead of the row lengths: `(3,2,1,1)`. This is the **conjugate** partition. The transformation is reversible.

- The number of rows in the original diagram becomes the largest row in the conjugate.
- The largest original row becomes the number of rows in the conjugate.
- The number of dots `k` stays unchanged.

Therefore:

$$
\boxed{\#\{\text{partitions of }k\text{ into }\le n\text{ parts}\}
=\#\{\text{partitions of }k\text{ with parts }\le n\}.}
$$

**Why bother?** Our original identical-box question limits **number of boxes**. Generating functions are easier to build by limiting the **allowed part sizes**. Conjugation proves that these two counts coincide.

**Warning:** The transformation works with the unrestricted partition set. If the original boxes must have capacity `L`, we must enforce *both* number of parts ≤ `n` and largest part ≤ `L` (a partition inside an `n\times L` rectangle). We cannot simply say "only allow sizes `1,\ldots,n`" and forget the capacity.

## 4. Generating functions from first principles

A generating function encodes a set of objects as a formal power series:

$$
F(x)=\sum_{k\ge0}a_kx^k.
$$

- `x` is a **formal bookkeeping variable**; it need not have a numerical value.
- The exponent `k` records the **total size/value**.
- The coefficient `a_k` records the **number of ways** to obtain total `k`.
- `[x^k]F(x)` means "extract the coefficient of `x^k`."

**Why add?** Alternative possibilities are summed. If two different choices both give size 4, `x^4+x^4=2x^4`.

**Why multiply?** Independent choices combine. Selecting size 2 and size 3 gives `x^2x^3=x^5`. Distributivity enumerates every pair of choices.

If part size `i` may occur 0, 1, 2, ... times, its generating factor is

$$
1+x^i+x^{2i}+\cdots=\frac1{1-x^i}.
$$

As a formal power series this identity works by coefficient algebra; for numerical `x` it also converges when `|x|<1`.

So partitions using sizes `1,\ldots,n` have

$$
\boxed{F_n(x)=\prod_{i=1}^n\frac1{1-x^i}},
\qquad
\boxed{p_{\le n}(k)=[x^k]F_n(x)}.
$$

Each factor means **a part size** after conjugation, **not one of the original boxes**.

## 5. Expand a generating function by hand

For `n=3`,

$$
F_3(x)=\underbrace{(1+x+x^2+\cdots)}_{\text{number of 1s}}\;
\underbrace{(1+x^2+x^4+\cdots)}_{\text{number of 2s}}\;
\underbrace{(1+x^3+x^6+\cdots)}_{\text{number of 3s}}.
$$

First multiply the 1s and 2s:

$$
D(x)=\frac1{(1-x)(1-x^2)}
=1+x+2x^2+2x^3+3x^4+3x^5+4x^6+\cdots.
$$

There are three contributions to `x^4`: `x^4\cdot1`, `x^2\cdot x^2`, and `1\cdot x^4`. In general

$$
[x^k]D(x)=\left\lfloor\frac k2\right\rfloor+1,
$$

because 2 may be used `0,\ldots,\lfloor k/2\rfloor` times, with 1s filling the remainder.

Now multiply by `1+x^3+x^6+\cdots`:

$$
\begin{aligned}
[x^6]F_3(x)
&=[x^6]D+[x^3]D+[x^0]D\\
&=4+2+1=\boxed7.
\end{aligned}
$$

And

$$
F_3(x)=1+x+2x^2+3x^3+4x^4+5x^5+7x^6+\cdots.
$$

For `k=5`, the desired coefficient is 5. **We do not need to expand forever:** discard all terms of degree greater than `k`.

## 6. Derive 2D and 1D partition DP

Let `P(i,j)` count partitions of total `j` using only part sizes `1,\ldots,i`.

Split into mutually exclusive cases:

1. Use **zero** parts of size `i` → `P(i-1,j)`.
2. Use **at least one** part of size `i` → remove one `i`, leaving `P(i,j-i)`; `i` remains available.

$$
\boxed{P(i,j)=P(i-1,j)+P(i,j-i)}.
$$

Base conditions: `P(i,0)=1`, `P(0,j>0)=0`, and a negative sum contributes zero.

The 2D version:

```python
def partitions_2d(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            dp[i][j] = dp[i - 1][j]
            if j >= i:
                dp[i][j] += dp[i][j - i]
    return dp[n][k]
```

To compress into one array, process `i` in increasing order, then `j` in increasing order. Before `dp[j]` is changed it still holds `P(i-1,j)`; `dp[j-i]` has already become `P(i,j-i)`.

```python
def partitions_at_most_boxes(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    dp = [1] + [0] * k

    for i in range(1, min(n, k) + 1):
        for j in range(i, k + 1):  # increasing: current row
            dp[j] += dp[j - i]

    return dp[k]
```

Time `O(k\min(n,k))` and space `O(k)`.

Walkthrough for `k=6,n=3`, coefficients indexed by `j=0,1,\ldots,6`:

| Processed sizes | `dp[0..6]` |
|---|---|
| None | `[1,0,0,0,0,0,0]` |
| `1` | `[1,1,1,1,1,1,1]` |
| `1,2` | `[1,1,2,2,3,3,4]` |
| `1,2,3` | `[1,1,2,3,4,5,7]` |

This is **unbounded coin change / complete knapsack counting**, where part sizes `1,\ldots,n` are coin denominations, each usable arbitrarily many times.

## 7. Derive iteration directions algebraically

Let `A(x)=\sum_j a_jx^j` be the old generating function and `B(x)=\sum_j b_jx^j` the desired result.

| Operation on generating function | Coefficient relation | In-place update | Direction |
|---|---|---|---|
| Multiply by `1+x^d` | `b_j=a_j+a_{j-d}` | `dp[j] += dp[j-d]` | **Backward** |
| Multiply by `1-x^d` | `b_j=a_j-a_{j-d}` | `dp[j] -= dp[j-d]` | **Backward** |
| Multiply by `1/(1-x^d)` | `b_j=a_j+b_{j-d}` | `dp[j] += dp[j-d]` | **Forward** |
| Multiply by `1/(1+x^d)` | `b_j=a_j-b_{j-d}` | `dp[j] -= dp[j-d]` | **Forward** |

Take `a_t=0` when `t<0`.

The rule comes from **old vs. updated coefficients**, not from memorizing "knapsack direction":

- Multiplication by `1\pm x^d` requires the old `a_{j-d}`. Sweep **down** so it hasn't been overwritten.
- Division by `1\mp x^d` requires the new `b_{j-d}`. Sweep **up** so it has been computed.

For example, multiplying by `1+x^2`:

$$
b_4=a_4+a_2.
$$

If we sweep upward, we instead compute `b_4=a_4+b_2`, accidentally allowing another size-2 part. Sweeping downward avoids this.

A backward in-place `dp[j]+=dp[j-i]` realizes **0/1 subset sum counting**, not unbounded coin change.

**Important:** If you change the direction, you generally change the generating function being computed.

## 8. Bounded multiplicities: two-pass in-place DP

This section is about a limit on **how many times a particular part size may occur**. It is not, by itself, a restriction on the capacity of the original identical boxes.

Suppose part size `i` can occur at most `m` times. Its factor is:

$$
1+x^i+x^{2i}+\cdots+x^{mi}
=\boxed{\frac{1-x^{(m+1)i}}{1-x^i}}.
$$

### Direct recurrence

Let `Q(i,j)` count ways using allowed sizes up to `i`, with at most `m` copies of each size:

$$
Q(i,j)=\sum_{r=0}^{\min(m,\lfloor j/i\rfloor)}Q(i-1,j-ri).
$$

Naively: `O(nkm)` time and `O(nk)` space.

### Sliding-sum derivation

Write the same equation for `j-i`:

$$
Q(i,j-i)=\sum_{r=1}^{m+1}Q(i-1,j-ri).
$$

Subtract to cancel the overlapping terms:

$$
\boxed{
Q(i,j)=Q(i-1,j)+Q(i,j-i)-Q(i-1,j-(m+1)i).
}
$$

A 2D DP now takes `O(nk)` time.

### Generating-function two-pass optimization

For each `i`, the target multiplication is

$$
A(x)\;\frac{1-x^{(m+1)i}}{1-x^i}.
$$

We implement it as two separate in-place operations:

**Pass A: Multiply by `1-x^{(m+1)i}`.** This inserts negative shifted copies of the old coefficients. Sweep **backward** so the subtracted values are old.

**Pass B: Multiply by `1/(1-x^i)`.** This permits unlimited repeated `i` parts. Sweep **forward** so the added values already include the current size.

After both operations, illegal counts `m+1,m+2,\ldots` cancel.

For `i=3,m=2`,

$$
(1-x^9)(1+x^3+x^6+x^9+x^{12}+\cdots)
=1+x^3+x^6.
$$

All terms for three or more 3s vanish.

```python
def bounded_part_size(k: int, n: int, m: int) -> int:
    """Use sizes 1..n; each size may occur at most m times."""
    if min(k, n, m) < 0:
        return 0
    dp = [1] + [0] * k

    for i in range(1, min(n, k) + 1):
        shift = (m + 1) * i

        # Multiply by (1 - x^shift):
        # use OLD dp[j-shift], so sweep backward.
        for j in range(k, shift - 1, -1):
            dp[j] -= dp[j - shift]

        # Multiply by 1/(1-x^i):
        # use UPDATED dp[j-i], so sweep forward.
        # The prior subtraction cancels occurrences above m.
        for j in range(i, k + 1):
            dp[j] += dp[j - i]

    return dp[k]
```

Time `O(nk)`, space `O(k)` (or `O(k\min(n,k))` if skipping sizes above `k`).

**The full-pass order can be swapped**, because polynomial multiplication is commutative. However, the **direction within each pass must not be swapped**.

Intermediate DP coefficients during the subtraction pass may be negative. That is valid algebra; the final product has nonnegative counting coefficients.

### Separate limit for each size

If size `i` has cap `m_i`:

$$
F(x)=\prod_{i\in S}\frac{1-x^{(m_i+1)i}}{1-x^i}.
$$

Use the same two passes with `shift=(m_i+1)i`. See `count_bounded_multiplicities` in the code catalog.

## 9. Original-box constraints: exact boxes and capacities

For this section, the boxes are identical and the items are identical.

### 9.1 Exactly `r` nonempty boxes

Each positive occupancy is ≥1. Remove one item from each of the `r` occupied boxes:

$$
\boxed{p_{=r}(k)=p_{\le r}(k-r)\quad(k\ge r)}.
$$

Also `p_{=r}(k)=p_{\le r}(k)-p_{\le r-1}(k)`.

Generating function:

$$
\boxed{\sum_{k\ge0}p_{=r}(k)x^k=\frac{x^r}{\prod_{i=1}^r(1-x^i)}}.
$$

Return 0 when `k<r`. For `r=0` the count is 1 only if `k=0`.

### 9.2 At least `r` nonempty boxes

If there are at most `n` available boxes, sum the exact-count variants:

$$
\sum_{t=r}^{\min(n,k)}p_{=t}(k).
$$

For `k=0`, only `t=0` is possible.

### 9.3 Every original box has capacity ≤ `L`

Now we require

$$
\lambda_1\ge\cdots\ge\lambda_n\ge0,\quad
\lambda_1\le L,\quad
\sum\lambda_i=k.
$$

In Ferrers-diagram language, the partition fits in an **`n\times L` rectangle**. Its generating function is the **Gaussian binomial coefficient**:

$$
\boxed{
\sum_{k\ge0}R_{n,L}(k)x^k
={n+L\brack n}_x
=\prod_{j=1}^{n}\frac{1-x^{L+j}}{1-x^j}.
}
$$

Here `{a\brack b}_x` is a polynomial, **not** an ordinary binomial coefficient. Only coefficients through total degree `nL` can be nonzero.

Example: `k=4,n=3,L=2`: `(2,2,0)` and `(2,1,1)`, so answer 2.

A general direct DP tracks both number of positive parts and total. For each allowed **occupancy size** `i=1,\ldots,L`, repeatedly choose size `i` while tracking how many boxes are used. Code below (`count_rectangle`).

Time `O(Lnk)`, space `O(nk)`; more specialized Gaussian-binomial recurrences can avoid this cost.

The polynomial recursion from splitting on whether a part of size `L` is used is

$$
\boxed{G_{n,L}(x)=G_{n,L-1}(x)+x^L G_{n-1,L}(x)}
$$

with `G_{0,L}=G_{n,0}=1`. Extract `[x^k]` as required.

### 9.4 Exactly `r` occupied boxes, occupancy in `[a,b]`

Assume `1\le a\le b`. Subtract `a` from every one of the `r` positive occupancies. The remainder is a partition inside an `r\times (b-a)` rectangle:

$$
\boxed{\text{answer}=R_{r,b-a}(k-ar)}.
$$

For example `k=5,r=3,[a,b]=[1,3]`: `(3,1,1)` and `(2,2,1)`, answer 2.

If **at most `n`** occupied boxes with `[a,b]` bounds, sum the last expression over `r=0,\ldots,n`. If zero-occupancy boxes are permitted, they do not count as occupied.

### 9.5 Exactly one box has a given size, or exactly `t` boxes have size `s`

This is a multiplicity restriction **in the original partition**: the occupancy value `s` must appear exactly `t` times. The corresponding factor is `x^{ts}`, and the `s` factor must be excluded from all remaining choices. To impose both a limit on the number of boxes and this exact multiplicity, use a **two-variable** generating function tracking total items and occupied boxes (see `12).

## 10. Distinct parts and gap restrictions

### 10.1 Each part size can be used at most once

The factor is `1+x^i`, and for allowed sizes `S`:

$$
\boxed{F(x)=\prod_{i\in S}(1+x^i)}.
$$

Code: **backward** 0/1 DP.

```python
def count_distinct_allowed_sizes(k: int, sizes) -> int:
    dp = [1] + [0] * k
    for i in sorted(set(sizes)):
        if i <= 0:
            raise ValueError("Part sizes must be positive")
        for j in range(k, i - 1, -1):
            dp[j] += dp[j - i]
    return dp[k]
```

**Careful:** `\prod_{i=1}^n(1+x^i)` restricts the **largest part to `n`** and makes parts distinct. It does **not** mean "at most `n` distinct parts, with no bound on part size." For the latter, use the formulas next.

### 10.2 Exactly `r` distinct positive parts

Start with strictly decreasing `\lambda_1>\cdots>\lambda_r\ge1`. Subtract the staircase `(r-1,r-2,\ldots,0)` to obtain an ordinary partition with exactly `r` positive parts; then subtract one more from each part.

This gives

$$
\boxed{D_{=r}(k)=p_{\le r}\left(k-\frac{r(r+1)}2\right)}.
$$

Equivalently,

$$
\sum_{k\ge0}D_{=r}(k)x^k
=\frac{x^{r(r+1)/2}}{\prod_{i=1}^r(1-x^i)}.
$$

Example `k=5,r=2`: `(4,1)` and `(3,2)`, so 2.

At most `r` distinct parts: sum `D_{=t}(k)` for `0\le t\le r`.

If all parts must be ≤ `L` as well, the GF is

$$
x^{r(r+1)/2}{L\brack r}_x.
$$

### 10.3 Consecutive parts differ by at least `d`

For exactly `r` positive parts with

$$
\lambda_1-\lambda_2\ge d,\ldots,\lambda_{r-1}-\lambda_r\ge d,
$$

subtract the staircase `(d(r-1),d(r-2),\ldots,0)`. We obtain an ordinary partition into exactly `r` positive parts:

$$
\boxed{\text{answer}
=p_{=r}\left(k-d\frac{r(r-1)}2\right)}.
$$

The `d=1` case recovers distinct parts. This counts gaps between consecutive sorted parts; it does not independently prohibit every specific part size.

## 11. Odd, even, permitted, forbidden, and colored parts

These examples often start as "coin change" questions but are also restricted integer partitions.

| Constraint | Generating function |
|---|---|
| Only sizes in `S`, unlimited | `\prod_{i\in S}(1-x^i)^{-1}` |
| Only sizes in `S`, at most once | `\prod_{i\in S}(1+x^i)` |
| All parts odd | `\prod_{i\ge1}(1-x^{2i-1})^{-1}` |
| All parts even | `\prod_{i\ge1}(1-x^{2i})^{-1}` |
| Parts between `a` and `b` | `\prod_{i=a}^{b}(1-x^i)^{-1}` |
| Forbid sizes in `T` | `\prod_{i\ge1,\;i\notin T}(1-x^i)^{-1}` |
| Each size `i` has `c_i` distinguishable colors | `\prod_i(1-x^i)^{-c_i}` |

Only sizes `i\le k` matter for extracting `[x^k]`.

**Even parts:** if `k` is odd the answer is zero; if `k=2t` the unrestricted count is `p(t)` (divide every part by 2).

**Euler's identity:** the number of partitions into distinct parts equals the number of partitions into odd parts (when unrestricted in part size):

$$
\prod_{i\ge1}(1+x^i)
=\prod_{i\ge1}\frac{1-x^{2i}}{1-x^i}
=\prod_{i\ge1,\ i\ \mathrm{odd}}\frac1{1-x^i}.
$$

This works because the even factors cancel. The identity **does not automatically hold with the same finite cutoff** in the two products.

**Congruence restriction:** To allow sizes `i\equiv a\pmod b`, let `S=\{i>0:i\equiv a\pmod b\}` and use the generic allowed-set product.

**Colors:** If each coin/part size has `c_i` distinguishable types, selecting how many of *each type* gives `(1-x^i)^{-c_i}`. This assumes those types are genuinely distinguishable; if colors are ignored, don't introduce extra factors.

## 12. Multiplicity, minimum counts, and two-variable functions

For each allowed size `i`, decide exactly how many copies `r_i` may occur.

A universal factor is

$$
\boxed{H_i(x)=\sum_{r_i\in M_i}x^{r_ii}},
\qquad
\boxed{F(x)=\prod_iH_i(x)},
$$

where `M_i` is the allowed set of nonnegative multiplicities.

Examples:

- **At least `\ell_i` copies:** `x^{\ell_i i}/(1-x^i)`.
- **Exactly `t_i` copies:** `x^{t_i i}`.
- **Between `\ell_i` and `u_i` copies:** `x^{\ell_i i}(1-x^{(u_i-\ell_i+1)i})/(1-x^i)`.
- **Only an even number of copies:** `1/(1-x^{2i})`.
- **Only an odd number of copies:** `x^i/(1-x^{2i})`.
- **At most `m_i` copies:** `(1-x^{(m_i+1)i})/(1-x^i)`.

To track **both** the total `k` and the number `r` of positive parts (occupied original boxes), use an auxiliary variable `y`:

$$
\boxed{
F(x,y)=\prod_{i\ge1}\frac1{1-yx^i}
}.
$$

Then `[x^ky^r]F(x,y)` counts partitions of `k` into exactly `r` positive parts. Each copy of size `i` contributes `x^iy`, which increases the item total by `i` and the occupied-box count by 1.

If size `i` has a multiplicity limit `m_i`, replace its factor with `\sum_{t=0}^{m_i}y^t x^{ti}`.

To track **exactly `r` distinct sizes used** (rather than number of parts), use a different meaning for `y`:

$$
\boxed{
\prod_{i\ge1}\left(1+y(x^i+x^{2i}+\cdots)\right)
=\prod_{i\ge1}\left(1+\frac{yx^i}{1-x^i}\right).
}
$$

Here one `y` is contributed when a size is used at least once, no matter how many copies.

These multivariate generating functions handle joint constraints that a simple 1D DP cannot encode.

## 13. Ordered distributions and compositions

A **composition** of `k` is an ordered sequence of positive integers summing to `k`.

If the boxes are **labeled**, assignments of identical items are compositions with zero parts allowed:

- Exactly `n` labeled boxes, zeros allowed: `\binom{k+n-1}{n-1}`.
- Exactly `n` labeled boxes, all positive: `\binom{k-1}{n-1}`, for `k\ge n`.
- Exactly `r` positive labeled boxes with fixed positions: `\binom{k-1}{r-1}`.
- Exactly `r` nonempty among `n` labeled boxes: `\binom nr\binom{k-1}{r-1}`.
- All compositions of `k>0` with any positive number of parts: `2^{k-1}`, by choosing breaks among `k-1` gaps.

If each labeled box has capacity ≤ `L`, the generating function is

$$
\boxed{(1+x+\cdots+x^L)^n}
$$

and stars-and-bars with inclusion-exclusion gives

$$
\boxed{
\sum_{t=0}^{\lfloor k/(L+1)\rfloor}
(-1)^t\binom nt
\binom{k-t(L+1)+n-1}{n-1}
}
$$

for `n\ge1`. A binomial coefficient is interpreted as 0 when its top index is too small. This counts **labeled boxes**, not identical ones.

If all labeled boxes must contain between `a` and `b` items, subtract `a` from each and apply the capped formula with target `k-an` and cap `b-a`.

**Key distinction:** "Ordered sum" (compositions) and "unordered sum" (partitions) are different problems.

## 14. Distinct items: Stirling and Bell numbers

If the `k` items are distinct but the boxes are identical, we're partitioning a set into unlabeled groups.

Let `S(k,r)` count partitions into exactly `r` **nonempty** groups.

Place the newest item either:

1. In one of the `r` existing groups (in `rS(k-1,r)` ways); or
2. Alone in a newly formed group (in `S(k-1,r-1)` ways).

$$
\boxed{S(k,r)=rS(k-1,r)+S(k-1,r-1)}.
$$

Base: `S(0,0)=1`, `S(k,0)=0` for `k>0`.

- Exactly `n` nonempty identical boxes: `S(k,n)`.
- At most `n` nonempty identical boxes (empty allowed): `\sum_{r=0}^{\min(k,n)}S(k,r)`.
- Unlimited identical boxes: **Bell number** `B_k=\sum_{r=0}^kS(k,r)`.
- `n` labeled boxes, each nonempty: `n!\,S(k,n)`.

A useful exponential generating function is

$$
\boxed{\sum_{k\ge0}S(k,r)\frac{x^k}{k!}=\frac{(e^x-1)^r}{r!}}.
$$

**Why exponential?** The items have identities, and `k!` accounts for labelings. Ordinary generating functions generally suit identical items; exponential generating functions often suit labeled combinatorial objects.

## 15. Distinct items with labeled-box capacities

If the items are distinct and boxes labeled, the number of arrangements with precise occupancies `(a_1,\ldots,a_n)` is

$$
\boxed{\frac{k!}{a_1!\cdots a_n!}},
\qquad a_i\ge0,\quad\sum a_i=k.
$$

To enforce each box capacity ≤ `L`, sum over allowable occupancy vectors. This is succinctly expressed by an **exponential generating function**:

$$
\boxed{
k!\,[x^k]\left(\sum_{j=0}^{L}\frac{x^j}{j!}\right)^n.
}
$$

If each box must contain between `a` and `b` distinct items, use

$$
\boxed{
k!\,[x^k]\left(\sum_{j=a}^{b}\frac{x^j}{j!}\right)^n.
}
$$

For nonempty boxes and no capacity, substitute `(e^x-1)^n`: this gives `n!\,S(k,n)`.

For **distinct items/identical boxes** with block sizes ≤ `L` and at most `n` nonempty boxes, the corresponding EGF is

$$
\sum_{r=0}^{n}\frac1{r!}\left(\sum_{j=1}^{L}\frac{x^j}{j!}\right)^r.
$$

Extract `k![x^k]`. The factor `1/r!` removes the order of the unlabeled groups. The problem is now a **restricted set partition**, not an integer partition.

## 16. Burnside's lemma for identical boxes

Here is a second, more advanced way to derive the identical-item/identical-box answer.

Start with labeled-box occupancy vectors `(a_1,\ldots,a_n)` summing to `k`. The symmetric group `S_n` acts by permuting the boxes. We want the number of distinct orbits under this action.

By **Burnside's lemma**,

$$
\#\text{orbits}
=\frac1{n!}\sum_{\sigma\in S_n}\#\{\text{vectors fixed by }\sigma\}.
$$

If permutation `\sigma` has cycles of lengths `\ell_1,\ldots,\ell_t`, a vector fixed by `\sigma` must have the same occupancy within each cycle. Its fixed-vector generating function is

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

This is a principled **symmetry/orbit counting** interpretation of identical boxes. It is usually not the fastest way to compute the answer, but is valuable when more complicated symmetry actions arise.

## 17. Unrestricted partition numbers and faster recurrences

When `n\ge k`, the number-of-boxes constraint is irrelevant:

$$
p_{\le n}(k)=p(k).
$$

The unrestricted generating function is

$$
\boxed{\sum_{k\ge0}p(k)x^k=\prod_{i\ge1}(1-x^i)^{-1}}.
$$

### Euler's pentagonal-number recurrence

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

with `p(0)=1` and `p(t)=0` for `t<0`.

This gives a practical `O(k\sqrt{k})`-time, `O(k)`-space algorithm to calculate **all** `p(0),\ldots,p(k)`, instead of the naive `O(k^2)` coin-change method when `n\ge k`.

### Asymptotic formulas (not exact)

Hardy–Ramanujan, as `k\to\infty`:

$$
\boxed{p(k)\sim\frac{1}{4k\sqrt3}
\exp\left(\pi\sqrt{\frac{2k}{3}}\right)}.
$$

If the number of boxes `n` is **fixed** and `k\to\infty`:

$$
\boxed{p_{\le n}(k)\sim\frac{k^{n-1}}{n!(n-1)!}}.
$$

These estimates describe growth. They must not replace exact DP when the problem asks for an exact integer.

## 18. Additional advanced partition families

Useful names to recognize when a problem introduces more structure:

| Family | What changes | Typical technique |
|---|---|---|
| **Partitions into exactly `r` parts** | Fixed number of nonempty boxes | Shift by 1 per part; `p_{\le r}(k-r)` |
| **Restricted largest part** | Per-box maximum for a single partition | Allowed part sizes and/or rectangle DP |
| **Partitions in a rectangle** | Both max part and number of parts bounded | Gaussian/binomial-in-`q` GF |
| **Strict partitions** | Parts are pairwise distinct | Staircase shift; 0/1 DP |
| **Gap-restricted partitions** | Adjacent sorted parts differ by ≥`d` | Staircase shift |
| **Odd/distinct partitions** | Allowed sizes or repeats restricted | Euler products and bijections |
| **Self-conjugate partitions** | Ferrers diagram equals its transpose | Bijection with distinct odd parts |
| **Colored partitions** | Parts have different labels/colors | Powers of Euler product factors |
| **Multivariate partitions** | Track total, number of parts, or other statistics | Two-/multi-variable GFs |
| **Vector partitions** | Parts have vector weights (multiple resource dimensions) | Multidimensional coefficient DP |
| **Plane partitions** | Two-dimensional weakly decreasing arrays, not just rows | MacMahon-type products under box bounds |
| **Set partitions** | Items are distinct, groups unlabeled | Stirling/Bell numbers, EGF |
| **Cyclic/rotation-equivalent allocations** | Different symmetry group on boxes | Burnside/Pólya enumeration |
| **Restricted compositions** | Order of occupancies matters | Stars and bars, ordinary GF, inclusion-exclusion |
| **Weighted partitions** | Each occurrence contributes a weight or probability | Weighted generating functions / semirings |

### Self-conjugate ↔ distinct odd parts

Each self-conjugate Ferrers diagram can be decomposed into diagonal hooks. These hook lengths are **distinct odd integers**, so the number of self-conjugate partitions of `k` equals the number of partitions of `k` into distinct odd parts:

$$
\prod_{i\ge1}(1+x^{2i-1}).
$$

### Plane partitions (a different dimension)

An ordinary partition is one nonincreasing list. A **plane partition** is a two-dimensional array of nonnegative entries that are weakly decreasing along rows and columns. It is *not* the same as moving identical balls among ordinary boxes. If the array has at most `a` rows, `b` columns, and entry height at most `c`, MacMahon's boxed plane-partition formula counts all such arrays:

$$
\prod_{i=1}^{a}\prod_{j=1}^{b}\prod_{h=1}^{c}
\frac{i+j+h-1}{i+j+h-2}.
$$

This is a neighboring topic, not a variant that can be solved by blindly applying the original 1D partition DP.

## 19. Algorithm catalog and tested Python code

The following implementations address the major cases. Python integers grow automatically, so exact counts are supported, although results can become very large.

```python
from math import comb, factorial


# A. Original problem: identical items, identical boxes, empties allowed.
def count_partitions(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    dp = [1] + [0] * k
    for size in range(1, min(n, k) + 1):
        for total in range(size, k + 1):
            dp[total] += dp[total - size]
    return dp[k]


# B. Exactly r positive identical boxes.
def count_exact_boxes(k: int, r: int) -> int:
    if k < 0 or r < 0 or k < r:
        return 0
    return count_partitions(k - r, r)


# C. Part sizes restricted to a set S; unlimited copies of each.
def count_allowed_parts(k: int, sizes) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size in sorted(set(sizes)):
        if size <= 0:
            raise ValueError("Part sizes must be positive")
        for total in range(size, k + 1):
            dp[total] += dp[total - size]
    return dp[k]


# D. At most one copy of each allowed part size.
def count_distinct_parts(k: int, sizes) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size in sorted(set(sizes)):
        if size <= 0:
            raise ValueError("Part sizes must be positive")
        for total in range(k, size - 1, -1):
            dp[total] += dp[total - size]
    return dp[k]


# E. Size-specific multiplicity caps, e.g. {1: 2, 2: 1, 3: 2}.
# Keys are allowed part sizes, values are maximum copy counts.
def count_bounded_multiplicities(k: int, caps: dict[int, int]) -> int:
    if k < 0:
        return 0
    dp = [1] + [0] * k
    for size, max_copies in sorted(caps.items()):
        if size <= 0 or max_copies < 0:
            raise ValueError("Require positive size and nonnegative cap")

        shift = (max_copies + 1) * size

        # Multiply old polynomial by (1 - x^shift).
        # Backward iteration preserves OLD coefficients.
        for total in range(k, shift - 1, -1):
            dp[total] -= dp[total - shift]

        # Divide by (1 - x^size); forward iteration
        # reuses NEW coefficients. The two passes together
        # allow exactly 0..max_copies copies of this size.
        for total in range(size, k + 1):
            dp[total] += dp[total - size]

    return dp[k]


# F. Identical boxes, each containing at most L identical items.
# Counts partitions of k into <= n parts, each <= L.
def count_rectangle(k: int, n: int, L: int) -> int:
    if min(k, n, L) < 0 or k > n * L:
        return 0

    # dp[used_boxes][total] for processed occupancy sizes.
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 1

    for size in range(1, min(L, k) + 1):
        # Increasing used_boxes allows multiple copies of
        # this occupancy size in different identical boxes.
        for used_boxes in range(1, n + 1):
            for total in range(size, k + 1):
                dp[used_boxes][total] += dp[used_boxes - 1][total - size]

    return sum(dp[used_boxes][k] for used_boxes in range(n + 1))


# G. Exactly r occupied identical boxes, each occupancy in [a,b].
def count_exact_boxes_with_bounds(k: int, r: int, a: int, b: int) -> int:
    if k < 0 or r < 0 or a < 1 or b < a:
        return 0
    return count_rectangle(k - r * a, r, b - a)


# H. Exactly r DISTINCT positive parts, no size bound.
def count_exact_distinct_parts(k: int, r: int) -> int:
    if k < 0 or r < 0:
        return 0
    return count_partitions(k - r * (r + 1) // 2, r)


# I. Exactly r positive parts, adjacent gap >= d.
def count_exact_parts_with_gap(k: int, r: int, d: int) -> int:
    if k < 0 or r < 0 or d < 0:
        return 0
    return count_exact_boxes(k - d * r * (r - 1) // 2, r)


# J. Stirling numbers of second kind: distinct items, identical nonempty boxes.
def stirling2(k: int, r: int) -> int:
    if min(k, r) < 0:
        return 0
    dp = [0] * (r + 1)
    dp[0] = 1
    for total_items in range(1, k + 1):
        for groups in range(min(total_items, r), 0, -1):
            dp[groups] = groups * dp[groups] + dp[groups - 1]
        dp[0] = 0
    return dp[r]


# K. Labeled boxes, identical items: stars and bars.
def identical_items_labeled_boxes(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    if n == 0:
        return int(k == 0)
    return comb(k + n - 1, n - 1)


# L. Labeled boxes, identical items, all boxes nonempty.
def labeled_boxes_nonempty(k: int, n: int) -> int:
    if k < 0 or n < 0:
        return 0
    if n == 0:
        return int(k == 0)
    return comb(k - 1, n - 1) if k >= n else 0


# M. Labeled boxes, identical items, each capacity <= L.
def labeled_boxes_capacity(k: int, n: int, L: int) -> int:
    if min(k, n, L) < 0 or k > n * L:
        return 0
    if n == 0:
        return int(k == 0)
    ways = 0
    for t in range(min(n, k // (L + 1)) + 1):
        remainder = k - t * (L + 1)
        ways += (-1) ** t * comb(n, t) * comb(remainder + n - 1, n - 1)
    return ways


# N. Unrestricted partition numbers, via pentagonal recurrence.
def unrestricted_partition_numbers(k: int) -> list[int]:
    if k < 0:
        return []
    p = [0] * (k + 1)
    p[0] = 1

    for target in range(1, k + 1):
        m = 1
        while m * (3 * m - 1) // 2 <= target:
            left = m * (3 * m - 1) // 2
            right = m * (3 * m + 1) // 2
            sign = 1 if m % 2 else -1
            p[target] += sign * p[target - left]
            if right <= target:
                p[target] += sign * p[target - right]
            m += 1

    return p


# O. Enumerate actual partitions, rather than just count them.
# Careful: output size grows quickly.
def enumerate_partitions(k: int, max_parts: int):
    def dfs(remaining: int, slots: int, largest: int, path: list[int]):
        if remaining == 0:
            yield tuple(path)
            return
        if slots == 0:
            return
        for current in range(min(remaining, largest), 0, -1):
            path.append(current)
            yield from dfs(remaining - current, slots - 1, current, path)
            path.pop()

    if k < 0 or max_parts < 0:
        return
    yield from dfs(k, max_parts, k, [])
```

### Quick usage examples

```python
assert count_partitions(5, 3) == 5
assert count_partitions(6, 3) == 7
assert count_exact_boxes(5, 3) == 2  # (3,1,1), (2,2,1)
assert count_rectangle(4, 3, 2) == 2
assert count_exact_boxes_with_bounds(5, 3, 1, 3) == 2
assert count_distinct_parts(5, range(1, 4)) == 1  # 3+2
assert count_exact_distinct_parts(5, 2) == 2  # 4+1, 3+2
assert count_bounded_multiplicities(5, {1: 2, 2: 1, 3: 2}) == 2
assert stirling2(5, 3) == 25
assert identical_items_labeled_boxes(5, 3) == 21
assert labeled_boxes_capacity(4, 3, 2) == 6
assert unrestricted_partition_numbers(6)[6] == 11
assert list(enumerate_partitions(5, 3)) == [
    (5,), (4, 1), (3, 2), (3, 1, 1), (2, 2, 1)
]
```

### Complexity snapshot

| Problem / implementation | Time | Extra space |
|---|---|---|
| `count_partitions` | `O(k\min(n,k))` | `O(k)` |
| `count_allowed_parts`, `s` allowed sizes | `O(sk)` | `O(k)` |
| `count_distinct_parts`, `s` sizes | `O(sk)` | `O(k)` |
| `count_bounded_multiplicities`, `s` sizes | `O(sk)` | `O(k)` |
| `count_rectangle` | `O(Lnk)` | `O(nk)` |
| `stirling2(k,r)` | `O(kr)` | `O(r)` |
| `unrestricted_partition_numbers(k)` | `O(k\sqrt{k})` | `O(k)` |
| `enumerate_partitions` | output-dependent; potentially very large | `O(k)` recursion, excluding output |

Use limits only as large as needed: part sizes larger than `k` contribute no positive-degree terms up to `x^k`.

### Validation strategy

For small `k`, brute-force enumerate all nonincreasing occupancy sequences and compare counts to optimized DPs. Cross-check especially:

- `k=0`, `n=0`, capacity 0, `n>k`, and impossible capacities (`k>nL`).
- A size with multiplicity cap 0.
- Exactly `r=0` occupied boxes.
- Forward-vs-backward loop changes.
- The distinction between capacity limits (on original boxes) and multiplicity limits (on sizes).

## 20. Examples, edge cases, and interview checklist

### Example A: five identical items, three identical boxes

- Model: unordered occupancy vector.
- Answer: `p_{\le3}(5)=5`.
- Generating function: `[x^5]1/((1-x)(1-x^2)(1-x^3))`.
- DP: unlimited sizes `1,2,3`; iterate target forward.

### Example B: no box can hold more than 2

For `k=5,n=3,L=2`, the only partition is `(2,2,1)`. Answer: 1.

Do **not** use `\prod_{i=1}^3(1+x^i+x^{2i})`: that limits **copies of each part size** after conjugation, not the size of each original box.

### Example C: each *part size* can occur at most twice

For `k=5` and allowed sizes `1,2,3`, permitted partitions are:

`(3,2)` and `(3,1,1)` and `(2,2,1)`? The last uses 2 twice (allowed). Thus **3**, not 2.

In contrast, if the cap for size 2 is *one* (e.g. `{1:2,2:1,3:2}`), only `(3,2)` and `(3,1,1)` remain, giving **2**.

This example demonstrates why it matters to state *which* multiplicity caps apply.

### Example D: three labeled boxes, identical items, capacity 2

For `k=4`, occupancy triples with entries in `{0,1,2}` summing to 4:

- The three permutations of `(2,2,0)`.
- The three permutations of `(2,1,1)`.

Answer: **6**. Identical boxes would give **2**.

### Example E: interview derivation template

1. **Restate distinguishability:** Are items and boxes labeled?
2. **Write a canonical state:** For identical boxes, sorted nonnegative occupancy vectors.
3. **List small examples:** `k=3,4,5` and edge cases.
4. **Find the mathematical family:** stars and bars, integer partitions, compositions, Stirling/Bell, or inclusion-exclusion.
5. **Write the generating function:** What does each factor count? Which exponent is the total? Is the factor `1+x^i`, `1/(1-x^i)`, or bounded?
6. **Derive DP by cases:** zero vs one-or-more, or exact number of copies.
7. **Compress safely:** Verify whether the dependency uses **old** or **new** coefficients. Descend for old; ascend for new.
8. **Explain complexity** and whether you need an exact value, a value modulo `M`, or an approximation.
9. **Test special cases:** empty, impossible, distinct vs identical boxes, zero limits, max occupancy, and performance.

### Mental summary

- `n^k`: distinct items, labeled boxes, empty allowed.
- `\binom{k+n-1}{n-1}`: identical items, labeled boxes, empty allowed.
- `\sum_{r\le n}S(k,r)`: distinct items, identical boxes.
- `p_{\le n}(k)`: identical items, identical boxes.
- **Generating functions:** addition collects alternatives; multiplication combines choices; `x^k` tracks size; coefficient counts ways.
- **0/1 usage:** `1+x^i` → backward addition.
- **Unlimited usage:** `1/(1-x^i)` → forward addition.
- **At most `m` copies:** `(1-x^{(m+1)i})/(1-x^i)` → backward subtraction + forward addition.
- **Original-box capacity ≤ `L`:** both length and largest part bounded → partition in an `n\times L` rectangle.
- **More conditions:** introduce additional DP dimensions or auxiliary generating-function variables.

## 21. References

These references provide standard terminology, proofs, and deeper extensions.

1. **NIST Digital Library of Mathematical Functions**, [`26.9: Integer Partitions — Restricted Number and Part Size](https://dlmf.nist.gov/26.9). Gaussian binomial coefficients, exact-size restrictions, and generating functions.
2. **NIST Digital Library of Mathematical Functions**, [`26.10: Other Restrictions](https://dlmf.nist.gov/26.10). Distinct parts, odd parts, difference restrictions, and identities.
3. **Applied Combinatorics**, [Partitions of an Integer](https://appliedcombinatorics.org/book/s_genfunction_partitions-integer.html). A friendly treatment of generating functions and Euler's odd/distinct identity.
4. **NIST DLMF**, [`26.4: Integer Partitions — General Properties](https://dlmf.nist.gov/26.4). Classical partition identities and enumerative tools.

---

**Study progression:** Derive the 4 basic cases → Ferrers conjugation → generating factors → 2D recurrence → 1D loop direction → bounded multiplicities → rectangle/capacity DP → exact counts/sets/parity/distinctness → Stirling/Bell and advanced GF families.

**Takeaway:** Most variations can be solved by identifying (1) which objects are distinguishable, (2) what the exponent tracks, (3) which choices each factor permits, and (4) which coefficient dependencies are old vs. newly updated. You do not need to memorize a separate algorithm for every variation.
