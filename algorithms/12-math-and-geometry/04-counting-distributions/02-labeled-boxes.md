# Labeled Boxes, Identical Items — Stars and Bars, Capacities, Prefix-Sum DP

## 2. The stick method (stars and bars)

### 2.1 Empty boxes allowed

The items are identical, so only the number in each box matters; the boxes are labeled, so the order of those numbers matters. An arrangement is a vector $(x_1,\ldots,x_n)$ with $x_i\ge0$ and $x_1+\cdots+x_n=k$.

Write the $k$ identical items as stars and place $n-1$ sticks between them to mark where one labeled box ends and the next begins. With $k=5$ and $n=4$:

```text
★ ★ | ★ | | ★ ★      →  boxes (2, 1, 0, 2)
| ★ ★ ★ ★ ★ | |      →  boxes (0, 5, 0, 0)
```

Every row of $k$ stars and $n-1$ sticks gives exactly one occupancy vector $(x_1,\ldots,x_n)$, and every vector gives exactly one row. So counting vectors is the same as choosing which of the $k+n-1$ positions hold sticks:

$$
\boxed{\#\{x_1+\cdots+x_n=k,\ x_i\ge0\}=\binom{k+n-1}{n-1}}.
$$

Check against [§1](01-modeling.md#1-the-four-cases-on-one-small-example): $k=4,n=2$ gives $\binom51=5$.

### 2.2 Every box nonempty, and lower bounds

Now two sticks can't touch, and no stick can sit at either end. Lay out the $k$ stars first. There are $k-1$ gaps between them, and we choose $n-1$ of those gaps for sticks:

```text
★ ★ ★ ★ ★
 ^ ^ ^ ^          k - 1 = 4 gaps, pick n - 1 of them
★ ★ | ★ | ★ ★     →  (2, 1, 2)
```

$$
\boxed{\#\{x_1+\cdots+x_n=k,\ x_i\ge1\}=\binom{k-1}{n-1}}\qquad(k\ge n,\ \text{else }0).
$$

The two answers are linked by a **shift**. Give every box one item up front, then distribute the remaining $k-n$ freely: $\binom{(k-n)+n-1}{n-1}=\binom{k-1}{n-1}$. The same shift handles any lower bound $x_i\ge a$: distribute $k-an$ items freely. The shift comes back for identical boxes ([§10.3](04-integer-partitions.md#103-a-second-recurrence-split-on-the-boxes), [§17](07-box-constraints.md#17-number-of-nonempty-boxes)).

### 2.3 Compositions

A **composition** of $k$ is an ordered sequence of positive integers summing to $k$. Labeled-box arrangements are compositions, with zero parts allowed when boxes may be empty:

- Exactly $n$ labeled boxes, zeros allowed: $\binom{k+n-1}{n-1}$.
- Exactly $n$ labeled boxes, all positive: $\binom{k-1}{n-1}$, for $k\ge n$.
- Exactly $r$ nonempty among $n$ labeled boxes: choose which boxes, then fill them, giving $\binom nr\binom{k-1}{r-1}$.
- All compositions of $k>0$ with any positive number of parts: $2^{k-1}$. Each of the $k-1$ gaps either holds a break or does not.

**Key distinction:** a composition is an *ordered* sum, while a partition ([§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)) is an *unordered* sum. $2+1+2$, $1+2+2$ and $2+2+1$ are three compositions but one partition.

## 3. Capacities by inclusion–exclusion

Now each labeled box holds **at most $L$** items. Sticks alone can't stop a box from getting too many stars, so count everything and subtract the bad arrangements.

Let $A_i$ be the set of arrangements in which box $i$ gets at least $L+1$ items. For any $t$ chosen boxes, the arrangements in all of their $A_i$ are counted by preloading $L+1$ items into each of them and distributing the remaining $k-t(L+1)$ freely:

$$
\left|A_{i_1}\cap\cdots\cap A_{i_t}\right|=\binom{k-t(L+1)+n-1}{n-1}.
$$

Inclusion–exclusion alternates over the number $t$ of overfull boxes:

$$
\boxed{
\sum_{t=0}^{\lfloor k/(L+1)\rfloor}
(-1)^t\binom nt
\binom{k-t(L+1)+n-1}{n-1}
}
$$

for $n\ge1$. A binomial coefficient is interpreted as 0 when its top index is too small.

**Example:** $k=4$, $n=3$, $L=2$.

- $t=0$: $\binom62=15$ arrangements in total.
- $t=1$: $\binom31\binom32=9$ arrangements with some box holding $\ge3$.
- $t=2$: two boxes holding $\ge3$ need 6 items, more than 4, so this term is 0.

Answer: $15-9=6$. These are the three orderings of $(2,2,0)$ and the three of $(2,1,1)$.

**Lower and upper bounds together.** If every labeled box must hold between $a$ and $b$ items, subtract $a$ from each (the shift from [§2.2](#22-every-box-nonempty-and-lower-bounds)) and apply the capped formula with target $k-an$ and cap $b-a$.

## 4. DP over boxes: prefix sums and sliding windows

Formulas get messy as constraints pile up; a DP extends more easily. Let `ways[j]` be the number of ways to put $j$ items into the boxes processed so far. Adding one more box that takes $t$ items gives

$$
\text{new}[j]=\sum_{t=0}^{j}\text{ways}[j-t],
$$

which is a **prefix sum**. For $k=5$, $n=3$:

| Boxes processed | `ways[0..5]` |
|---|---|
| 0 | `[1,0,0,0,0,0]` |
| 1 | `[1,1,1,1,1,1]` |
| 2 | `[1,2,3,4,5,6]` |
| 3 | `[1,3,6,10,15,21]` |

The last entry matches $\binom{5+2}{2}=21$.

A capacity $L$ limits the prefix sum to the last $L+1$ terms ($t\le L$), which is a **sliding window**: add the entry entering on the right, drop `ways[j-L-1]` leaving on the left. The example of [§3](#3-capacities-by-inclusionexclusion), $k=4$, $n=3$, $L=2$:

| Boxes processed | `ways[0..4]` | How `new[4]` is formed |
|---|---|---|
| 0 | `[1,0,0,0,0]` | |
| 1 | `[1,1,1,0,0]` | `ways[2]+ways[3]+ways[4]` = 0 (window of 3) |
| 2 | `[1,2,3,2,1]` | `1+0+0` = 1 |
| 3 | `[1,3,6,7,6]` | `3+2+1` = 6 |

The answer 6 matches inclusion–exclusion.

```python
from itertools import product
from math import comb
import random


def labeled_boxes_dp(k: int, n: int, L: int | None = None) -> int:
    """Identical items into n labeled boxes, each holding at most L (None = no cap)."""
    if k < 0 or n < 0 or (L is not None and L < 0):
        raise ValueError("k, n and L must be nonnegative")
    cap = k if L is None else min(L, k)
    ways = [1] + [0] * k  # zero boxes: only total 0 is reachable

    for _ in range(n):
        new = [0] * (k + 1)
        window = 0
        for j in range(k + 1):
            window += ways[j]
            if j - cap - 1 >= 0:
                window -= ways[j - cap - 1]  # drop t > cap
            new[j] = window
        ways = new

    return ways[k]


def labeled_boxes_formula(k: int, n: int, L: int) -> int:
    """Inclusion-exclusion over the number t of overfull boxes (section 3)."""
    if n == 0:
        return int(k == 0)
    return sum(
        (-1) ** t * comb(n, t) * comb(k - t * (L + 1) + n - 1, n - 1)
        for t in range(min(n, k // (L + 1)) + 1)
    )


def brute(k: int, n: int, L: int) -> int:
    return sum(1 for v in product(range(L + 1), repeat=n) if sum(v) == k)


def main():
    assert labeled_boxes_dp(5, 3) == comb(7, 2) == 21
    assert labeled_boxes_dp(4, 3, 2) == labeled_boxes_formula(4, 3, 2) == 6
    assert labeled_boxes_dp(0, 0) == 1 and labeled_boxes_dp(3, 0) == 0
    assert labeled_boxes_dp(7, 3, 2) == 0  # more than n * L items
    rng = random.Random(2)
    for _ in range(300):
        k, n, L = rng.randint(0, 8), rng.randint(0, 4), rng.randint(0, 4)
        expected = brute(k, n, L)
        assert labeled_boxes_dp(k, n, L) == expected
        assert labeled_boxes_formula(k, n, L) == expected
        if L >= k:
            assert labeled_boxes_dp(k, n) == expected


if __name__ == "__main__":
    main()
```

Time $O(nk)$, space $O(k)$.

**Why this leads to generating functions.** Each box applied the *same* transformation to the `ways` array. [§5.3](03-generating-functions.md#53-the-dp-of-4-is-polynomial-multiplication) shows that this transformation is multiplication by one polynomial factor, and that every DP in this guide is a product of such factors.

**Where this method stops working.** Stars and bars counts *ordered* vectors. If the boxes become identical, $(2,1,2)$, $(1,2,2)$ and $(2,2,1)$ should count once. [§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes) shows why no simple correction fixes this.

## Pitfalls and practice

1. **$n-1$ sticks, not $n$.** $n$ boxes need $n-1$ separators: $\binom{k+n-1}{n-1}$, not $\binom{k+n}{n}$.
2. **Nonempty boxes with $k<n$.** $\binom{k-1}{n-1}$ must be 0, and $n=0$ needs the $k=0$ special case.
3. **Stopping inclusion–exclusion too early.** Keep every $t$ with $t(L+1)\le k$; the terms alternate in sign.
4. **Applying stars and bars to identical boxes.** It counts ordered vectors and overcounts ([§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)).

Practice: distribute candies among children (with and without a per-child limit); count solutions of $x_1+x_2+x_3=k$ with bounds; number of compositions of $k$; dice-sum counts ($n$ dice, faces $1..6$, as a box with bounds $[1,6]$).

Next: [Generating Functions](03-generating-functions.md).
