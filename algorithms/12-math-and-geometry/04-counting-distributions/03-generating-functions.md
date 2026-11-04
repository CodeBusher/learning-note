# Generating Functions — Choices as Factors, Factors as DP Passes

## 5. What a generating function encodes

### 5.1 The bookkeeping rules

The stick count $\binom{k+n-1}{n-1}$ answers one question. Change one box's rule and you need a new formula. A **generating function** stores the whole answer table, one coefficient per total, in a form where each independent choice is one factor:

$$
F(x)=\sum_{k\ge0}a_kx^k.
$$

- $x$ is a **formal bookkeeping variable**. It need not have a numerical value.
- The exponent $k$ records the **total size**: here, the number of items.
- The coefficient $a_k$ records the **number of ways** to obtain total $k$.
- $[x^k]F(x)$ means "extract the coefficient of $x^k$."

**Why add?** Alternatives are summed. If two different choices both give size 4, $x^4+x^4=2x^4$.

**Why multiply?** Independent choices combine. Choosing size 2 in one place and size 3 in another gives $x^2x^3=x^5$. Expanding a product with the distributive law lists every combination of choices exactly once.

### 5.2 One labeled box, then $n$ of them

A single box may hold $0,1,2,\ldots$ items, one way each:

$$
1+x+x^2+\cdots=\frac1{1-x}.
$$

As a formal power series this identity holds by coefficient algebra: multiply both sides by $1-x$ and everything except $1$ cancels. For numerical $x$ it also converges when $|x|<1$.

The $n$ labeled boxes are chosen independently, so multiply $n$ copies:

$$
\boxed{\#\{x_1+\cdots+x_n=k,\ x_i\ge0\}=[x^k]\,\frac1{(1-x)^n}=\binom{k+n-1}{n-1}}.
$$

The coefficient is the stars-and-bars count from [§2.1](02-labeled-boxes.md#21-empty-boxes-allowed). Change what one box may hold, and you change only its factor:

| Each labeled box holds… | Factor per box | Whole generating function |
|---|---|---|
| Any number | $\dfrac1{1-x}$ | $(1-x)^{-n}$ |
| At least 1 | $x+x^2+\cdots=\dfrac{x}{1-x}$ | $x^n(1-x)^{-n}$ |
| At most $L$ | $1+x+\cdots+x^L=\dfrac{1-x^{L+1}}{1-x}$ | $\left(\dfrac{1-x^{L+1}}{1-x}\right)^n$ |
| Between $a$ and $b$ | $x^a+\cdots+x^b$ | $(x^a+\cdots+x^b)^n$ |

Expanding $(1-x^{L+1})^n$ with the binomial theorem and multiplying by $(1-x)^{-n}$ reproduces the inclusion–exclusion formula of [§3](02-labeled-boxes.md#3-capacities-by-inclusionexclusion) term by term. The $t$-th term of $(1-x^{L+1})^n$ is $(-1)^t\binom nt x^{t(L+1)}$.

### 5.3 The DP of §4 is polynomial multiplication

In [§4](02-labeled-boxes.md#4-dp-over-boxes-prefix-sums-and-sliding-windows), adding a box replaced `ways` with its prefix sums. That is exactly multiplication by $\frac1{1-x}$: if $B(x)=A(x)/(1-x)$, then $B(x)(1-x)=A(x)$, so

$$
b_j=a_j+b_{j-1}.
$$

Each new coefficient is the old one plus the *previous new* one, which is a running prefix sum. A capped box multiplies by $1+x+\cdots+x^L$ instead, and that is the sliding window. **A DP step is a multiplication by one factor.** [§7](#7-from-factors-to-in-place-dp-updates) turns this into a general rule.

## 6. Products of different factors

When factors differ, each one stands for a *different* independent choice.

**Example: making change.** Count the ways to pay total $k$ with coins of value 1, 2 and 3, where only the number of each coin matters, not the order. The choices are "how many 1s", "how many 2s" and "how many 3s":

$$
F_3(x)=\underbrace{(1+x+x^2+\cdots)}_{\text{number of 1s}}\;
\underbrace{(1+x^2+x^4+\cdots)}_{\text{number of 2s}}\;
\underbrace{(1+x^3+x^6+\cdots)}_{\text{number of 3s}}
=\prod_{i=1}^{3}\frac1{1-x^i}.
$$

Using $c$ coins of value $i$ contributes $x^{ci}$, so the factor for value $i$ is $1+x^i+x^{2i}+\cdots=\frac1{1-x^i}$.

### 6.1 Expand by hand

First multiply the 1s and 2s:

$$
D(x)=\frac1{(1-x)(1-x^2)}
=1+x+2x^2+2x^3+3x^4+3x^5+4x^6+\cdots.
$$

There are three contributions to $x^4$: $x^4\cdot1$, $x^2\cdot x^2$, and $1\cdot x^4$. In general

$$
[x^k]D(x)=\left\lfloor\frac k2\right\rfloor+1,
$$

because 2 may be used $0,\ldots,\lfloor k/2\rfloor$ times, with 1s filling the remainder.

Now multiply by $1+x^3+x^6+\cdots$. A $3^c$ term picks out $[x^{6-3c}]D$:

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

To find $[x^k]$, discard all terms of degree greater than $k$; they never affect it. [§10.1](04-integer-partitions.md#101-the-generating-function) shows that this same product counts identical items in identical boxes.

## 7. From factors to in-place DP updates

Store the coefficients $a_0,\ldots,a_k$ in an array `dp`. Multiplying by a factor updates `dp` in place, and the only subtle part is the **loop direction**.

Let $A(x)=\sum_j a_jx^j$ be the old generating function and $B(x)=\sum_j b_jx^j$ the desired result.

| Operation on generating function | Coefficient relation | In-place update | Direction |
|---|---|---|---|
| Multiply by $1+x^d$ | $b_j=a_j+a_{j-d}$ | `dp[j] += dp[j-d]` | **Backward** |
| Multiply by $1-x^d$ | $b_j=a_j-a_{j-d}$ | `dp[j] -= dp[j-d]` | **Backward** |
| Multiply by $1/(1-x^d)$ | $b_j=a_j+b_{j-d}$ | `dp[j] += dp[j-d]` | **Forward** |
| Multiply by $1/(1+x^d)$ | $b_j=a_j-b_{j-d}$ | `dp[j] -= dp[j-d]` | **Forward** |

Take $a_t=0$ when $t<0$.

The rule comes from **old vs. updated coefficients**, not from a "knapsack direction" to memorize:

- Multiplication by $1\pm x^d$ needs the old $a_{j-d}$. Sweep **down** so it hasn't been overwritten yet.
- Division by $1\mp x^d$ needs the new $b_{j-d}$. Sweep **up** so it has already been computed.

For example, multiplying by $1+x^2$ (use a 2 at most once):

$$
b_4=a_4+a_2.
$$

If we sweep upward, we instead compute $b_4=a_4+b_2$, which accidentally allows a second 2. Sweeping downward avoids this.

So the same line `dp[j] += dp[j-i]` is **unbounded coin change** (forward, factor $1/(1-x^i)$) or **0/1 subset-sum counting** (backward, factor $1+x^i$): changing the direction changes the generating function. The prefix-sum step of [§5.3](#53-the-dp-of-4-is-polynomial-multiplication) is the forward row with $d=1$.

The script checks each row of the table against an explicit polynomial product on random arrays, and shows the wrong direction failing:

```python
import random


def multiply(a: list[int], b: list[int]) -> list[int]:
    """Truncated product: keep degrees < len(a)."""
    out = [0] * len(a)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            if i + j < len(a):
                out[i + j] += ai * bj
    return out


def times_one_plus(dp: list[int], d: int, sign: int) -> None:
    """dp *= (1 + sign * x^d): needs OLD dp[j-d], so sweep down."""
    for j in range(len(dp) - 1, d - 1, -1):
        dp[j] += sign * dp[j - d]


def divide_one_minus(dp: list[int], d: int, sign: int) -> None:
    """dp /= (1 - sign * x^d): needs NEW dp[j-d], so sweep up."""
    for j in range(d, len(dp)):
        dp[j] += sign * dp[j - d]


def series(d: int, sign: int, size: int) -> list[int]:
    """Coefficients of 1 / (1 - sign * x^d) below degree size."""
    out = [0] * size
    for t in range(0, size, d):
        out[t] = sign ** (t // d)
    return out


def main():
    rng = random.Random(3)
    for _ in range(200):
        size, d = rng.randint(1, 12), rng.randint(1, 4)
        a = [rng.randint(-5, 5) for _ in range(size)]
        for sign in (1, -1):
            factor = [int(t == 0) + sign * int(t == d) for t in range(size)]
            dp = a[:]
            times_one_plus(dp, d, sign)
            assert dp == multiply(a, factor)
            dp = a[:]
            divide_one_minus(dp, d, sign)
            assert dp == multiply(a, series(d, sign, size))

    # Sweeping UP for 1 + x^2 silently allows a second 2.
    dp = [1, 0, 0, 0, 0]
    for j in range(2, 5):
        dp[j] += dp[j - 2]
    assert dp == [1, 0, 1, 0, 1]  # that is 1/(1 - x^2), not 1 + x^2


if __name__ == "__main__":
    main()
```

Each pass costs $O(k)$ for $k+1$ stored coefficients.

## Pitfalls and practice

1. **Choosing the loop direction by habit.** Ask whether the update needs the old or the new `dp[j-d]` (§7).
2. **One factor per box vs. one factor per value.** Labeled boxes give one factor per box ([§5.2](#52-one-labeled-box-then-n-of-them)); coin change gives one factor per coin value ([§6](#6-products-of-different-factors)). Mixing the two counts something else.
3. **Treating $x$ as a number.** The identities are coefficient algebra; convergence never matters for counting.
4. **Expanding too far.** Truncate at degree $k$.

Practice: coin change II (number of combinations); combination sum IV (ordered, so *not* this product: compare); count subsets with a given sum; dice-roll sums as $(x+\cdots+x^6)^n$.

Next: [Identical Boxes: Integer Partitions](04-integer-partitions.md).
