# Combinatorics — Counting Without Listing

## 1. Counting rules: PIN codes

**Problem.** How many 4-digit PIN codes (`0000` to `9999`) have at least one repeated digit? The answer is 4960.

**Brute force.** List all `10^4` codes and test each. Fine for 4 digits, hopeless for 20. We want to count without listing, and three rules do most of the work.

**Product rule.** If a choice is made in steps, with `a` options at the first step and `b` at the second whatever the first choice was, there are `a · b` results. All PINs: `10 · 10 · 10 · 10 = 10000`. PINs with four different digits: `10 · 9 · 8 · 7 = 5040`. The second step has 9 options whichever digit came first; *which* 9 changes, but the count doesn't, and the count is all the rule needs.

**Complement rule.** Count what you don't want and subtract from the total: `10000 − 5040 = 4960`. "At least one repeat" splits into many cases (one pair, two pairs, a triple, …); "no repeat" is one product. Reach for the complement whenever a problem says "at least one".

**Sum rule.** If the things you count split into groups that **do not overlap**, add the group sizes. Variant: how many PINs start with 0 **or** end with 0? Each group has 1000 codes, but `1000 + 1000 = 2000` is wrong: the 100 codes `0__0` are in both groups and were counted twice. The answer is `2000 − 100 = 1900`. Fixing overlaps in general is inclusion–exclusion (§8). The formulas of §1, §2 and §6 are checked by brute force in one script in §10.

## 2. Permutations and combinations

The running example: four runners A, B, C, D.

**In how many orders can they finish?** First place has 4 choices, second 3, third 2, fourth 1: `4 · 3 · 2 · 1 = 24`. This is `4!`, read "4 factorial", and an ordering of all items is a **permutation**:

$$
n! = n\cdot(n-1)\cdots 2\cdot 1,\qquad 0! = 1.
$$

Why `0! = 1`? There is exactly one way to arrange nothing: the empty arrangement.

**Variant: only the podium.** Gold and silver among 4 runners: stop after 2 places, `4 · 3 = 12`. Ordered selections of `k` out of `n`:

$$
P(n, k) = n\cdot(n-1)\cdots(n-k+1) = \frac{n!}{(n-k)!}.
$$

**Variant: order doesn't matter.** Pick a team of 2. `{A, B}` and `{B, A}` are the same team, and each team appears `2! = 2` times among the 12 ordered pairs:

```text
ordered pairs:  AB BA   AC CA   AD DA   BC CB   BD DB   CD DC
teams:          {A,B}   {A,C}   {A,D}   {B,C}   {B,D}   {C,D}     → 12 / 2 = 6
```

Each unordered choice of `k` items appears `k!` times among the ordered ones, so the number of **combinations** is

$$
\binom{n}{k} = \frac{P(n,k)}{k!} = \frac{n!}{k!\,(n-k)!},
$$

read "n choose k", also written `C(n, k)` or `nCr`. It is 0 when `k < 0` or `k > n`. Two facts follow from the meaning, without algebra:

- **Symmetry:** `C(n, k) = C(n, n − k)`. Choosing the `k` runners on the team is the same as choosing the `n − k` left out.
- **Row sum:** `C(n, 0) + C(n, 1) + ⋯ + C(n, n) = 2^n`. Each runner is either in or out of a subset.

**Variant: repeated items.** How many different strings use the letters of `AAB`? With labels, `A₁A₂B` has `3! = 6` orders, and each real string appears `2!` times (swap the two A's), so there are `6 / 2 = 3`: `AAB, ABA, BAA`. With counts `c₁, c₂, …` summing to `n`, the number of distinct arrangements is the **multinomial** `n! / (c₁! c₂! ⋯)`.

## 3. Pascal's triangle: binomials by DP

**Problem.** Compute `C(n, k)` for all `n, k ≤ 1000` modulo `m`, where `m` might not be prime. Factorial formulas need division, which is not allowed modulo a general `m` (see [Number Theory §7](01-number-theory.md#7-modular-arithmetic)). We want a method with only additions.

**Key observation.** Look at one particular person, say the last one. A `k`-subset of `n` people either **excludes** that person (then pick all `k` from the other `n − 1`) or **includes** them (then pick `k − 1` more from the other `n − 1`). The two cases don't overlap, so by the sum rule:

$$
\binom{n}{k} = \binom{n-1}{k} + \binom{n-1}{k-1},\qquad \binom{n}{0} = \binom{n}{n} = 1.
$$

**State:** `C[n][k]` is the number of `k`-element subsets of an `n`-element set.

**Trace.** Each entry is the sum of the two entries above it:

```text
n = 0:                1
n = 1:              1   1
n = 2:            1   2   1
n = 3:          1   3   3   1
n = 4:        1   4   6   4   1
n = 5:      1   5  10  10   5   1
n = 6:    1   6  15  20  15   6   1
```

For example `C(6, 2) = C(5, 1) + C(5, 2) = 5 + 10 = 15`, and the team count from §2 is `C(4, 2) = 6`.

Time and space O(n_max²). Keep only one row (updating `k` from high to low) if you need a single `n`. The code for §3–§5 is one script at the end of §5.

## 4. `nCr` modulo a prime with factorials

**Problem.** Answer `q = 10^5` queries `C(n, k) mod p` with `n ≤ 10^6` and `p = 10^9 + 7`. Pascal's table would have `10^12` cells.

**Key observation.** Since `p` is a prime larger than `n`, none of `1..n` is divisible by `p`, so every factorial up to `n!` has an inverse mod `p`. Precompute

- `fact[i] = i! mod p`, forward: `fact[i] = fact[i−1] · i`,
- `inv_fact[i] = (i!)⁻¹ mod p`, **backward**: one Fermat inverse for `inv_fact[n]`, then `inv_fact[i−1] = inv_fact[i] · i`, because `1/(i−1)! = i / i!`.

Then each query is two multiplications:

$$
\binom{n}{k} \equiv \text{fact}[n]\cdot \text{inv\_fact}[k]\cdot \text{inv\_fact}[n-k] \pmod p.
$$

**Trace** with `p = 13`, `n = 6`:

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `fact[i]` | 1 | 1 | 2 | 6 | 24 → 11 | 55 → 3 | 18 → 5 |
| `inv_fact[i]` (filled right to left) | 1·1 = 1 | 7·2 = 14 → 1 | 11·3 = 33 → 7 | 6·4 = 24 → 11 | 9·5 = 45 → 6 | 8·6 = 48 → 9 | 5¹¹ mod 13 = 8 |

Check a pair: `fact[4] · inv_fact[4] = 11 · 6 = 66 = 5·13 + 1`. ✓ Then `C(6, 2) ≡ 5 · 7 · 6 = 210 ≡ 2 (mod 13)`, and indeed `15 = 13 + 2`. ✓

Precomputation O(n_max + log p); each query O(1); space O(n_max).

## 5. Lucas's theorem: when the prime is small

**Problem.** Compute `C(12, 5) mod 5`. The factorial method breaks: `12!` contains the factors 5 and 10, so `fact[12] ≡ 0` and `5!` has no inverse.

**Lucas's theorem.** Write `n` and `k` in base `p`, digit by digit: `n = (n_r … n_1 n_0)_p`, `k = (k_r … k_1 k_0)_p`. Then

$$
\binom{n}{k} \equiv \prod_i \binom{n_i}{k_i} \pmod p,
$$

where `C(nᵢ, kᵢ) = 0` whenever `kᵢ > nᵢ`. Each factor has `nᵢ, kᵢ < p`, so the factorial method from §4 handles it.

**Why it holds, in one line.** Mod a prime, `(1 + x)^p ≡ 1 + x^p`, because every middle coefficient `C(p, j)` has a factor `p` in the numerator and none in the denominator. So `(1 + x)^n = ∏ (1 + x^(p^i))^(nᵢ)`, and the coefficient of `x^k` can only come from picking `x^(kᵢ·p^i)` in each factor, which happens in `C(nᵢ, kᵢ)` ways.

**Trace** for `C(12, 5) mod 5`:

```text
n = 12 = 2·5 + 2  →  digits (2, 2)
k =  5 = 1·5 + 0  →  digits (1, 0)
C(2, 1) · C(2, 0) = 2 · 1 = 2
```

Check: `C(12, 5) = 792 = 158·5 + 2`. ✓ A digit with `kᵢ > nᵢ` makes the whole product 0: `C(7, 3) mod 5`, digits `(1, 2)` and `(0, 3)`, gives `C(2, 3) = 0`; indeed `C(7, 3) = 35`.

A neat special case, `p = 2`: `C(n, k)` is odd exactly when every 1-bit of `k` is also a 1-bit of `n`, that is when `k & n == k` (see [Bit Manipulation](../11-bit-manipulation/README.md)).

```python
import math
import random


def pascal(n_max: int, mod: int | None = None) -> list[list[int]]:
    """C[n][k] for 0 <= k <= n <= n_max, optionally reduced mod `mod` (any modulus)."""
    if n_max < 0:
        raise ValueError("n_max must be nonnegative")
    C = [[0] * (n_max + 1) for _ in range(n_max + 1)]
    for n in range(n_max + 1):
        C[n][0] = 1 if mod is None else 1 % mod
        for k in range(1, n + 1):
            value = C[n - 1][k - 1] + C[n - 1][k]
            C[n][k] = value if mod is None else value % mod
    return C


class Binomial:
    """C(n, k) mod a prime p, for n < p and n <= n_max."""

    def __init__(self, n_max: int, p: int = 10**9 + 7):
        if n_max >= p:
            raise ValueError("n_max must be below p; use Lucas's theorem instead")
        self.p = p
        self.fact = [1] * (n_max + 1)
        for i in range(1, n_max + 1):
            self.fact[i] = self.fact[i - 1] * i % p
        self.inv_fact = [1] * (n_max + 1)
        self.inv_fact[n_max] = pow(self.fact[n_max], p - 2, p)  # the only pow
        for i in range(n_max, 0, -1):
            self.inv_fact[i - 1] = self.inv_fact[i] * i % p

    def comb(self, n: int, k: int) -> int:
        if k < 0 or k > n or n < 0:
            return 0
        if n >= len(self.fact):
            raise ValueError("n exceeds n_max")
        return self.fact[n] * self.inv_fact[k] % self.p * self.inv_fact[n - k] % self.p


def lucas(n: int, k: int, p: int) -> int:
    """C(n, k) mod a prime p, for any size of n."""
    if k < 0 or k > n:
        return 0
    small = Binomial(p - 1, p)
    result = 1
    while n or k:
        ni, ki = n % p, k % p  # one base-p digit of each
        if ki > ni:
            return 0
        result = result * small.comb(ni, ki) % p
        n, k = n // p, k // p
    return result


def main():
    C = pascal(60)
    assert C[6][:7] == [1, 6, 15, 20, 15, 6, 1]
    assert all(C[n][k] == math.comb(n, k) for n in range(61) for k in range(n + 1))
    C12 = pascal(200, 12)  # 12 is not prime: Pascal needs no inverses
    assert all(C12[n][k] == math.comb(n, k) % 12 for n in range(201) for k in range(n + 1))

    small = Binomial(6, 13)
    assert small.fact == [1, 1, 2, 6, 11, 3, 5] and small.inv_fact == [1, 1, 7, 11, 6, 9, 8]
    assert small.comb(6, 2) == 2
    p = 10**9 + 7
    B = Binomial(2000, p)
    rng = random.Random(8)
    for _ in range(3000):
        n = rng.randint(0, 2000)
        k = rng.randint(-3, n + 3)
        assert B.comb(n, k) == (math.comb(n, k) % p if 0 <= k <= n else 0)
    try:
        Binomial(20, 13)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    assert lucas(12, 5, 5) == 2 == 792 % 5 and lucas(7, 3, 5) == 0
    for q in (2, 3, 5, 7, 13):
        for _ in range(500):
            n = rng.randint(0, 300)
            k = rng.randint(-2, n + 2)
            assert lucas(n, k, q) == (math.comb(n, k) % q if 0 <= k <= n else 0)
    assert all((math.comb(n, k) % 2 == 1) == (k & n == k) for n in range(64) for k in range(n + 1))
    assert 0 <= lucas(10**18, 10**9, 7) < 7  # 22 base-7 digits: fast


if __name__ == "__main__":
    main()
```

Lucas costs O(p) to build the factorial tables up to `p`, then O(1) per base-`p` digit: use it when `p` is small enough to tabulate.

## 6. Stars and bars, briefly

**Problem.** In how many ways can you put 5 identical candies into 3 labeled jars (jars may stay empty)?

Draw the candies as stars and separate the jars with 2 bars. Every arrangement of 5 stars and 2 bars in a row is one distribution, and every distribution is one arrangement:

```text
★★|★|★★     →  jars (2, 1, 2)
|★★★★★|     →  jars (0, 5, 0)
★★★★★||     →  jars (5, 0, 0)
```

There are 7 positions, and we choose which 2 hold bars: `C(7, 2) = 21`. In general, `k` identical items into `n` labeled boxes:

$$
\binom{k+n-1}{n-1}.
$$

**Variant: every jar nonempty.** Put one candy in each jar first and distribute the remaining `k − n` freely: `C(k − n + n − 1, n − 1) = C(k − 1, n − 1)`. For 5 candies in 3 jars, `C(4, 2) = 6`.

That is the start of a big family. What if the jars are identical? What if each jar has a capacity, or the candies are all different? [Counting Distributions](04-counting-distributions/README.md) works through every one of those cases, with integer partitions, Stirling numbers and generating functions.

## 7. Catalan numbers

**Problem.** How many strings of `n` pairs of parentheses are **balanced**, meaning every `(` is closed by a later `)`? For `n = 3`, list them:

```text
((()))   (()())   (())()   ()(())   ()()()        → 5
```

**Brute force.** Generate all `2^(2n)` strings and check each. Already a million strings for `n = 10`.

**Key observation: split at the partner of the first `(`.** A nonempty balanced string starts with `(`. Find the `)` that closes it. Everything between them is balanced (`i` pairs), and everything after is balanced (`n − 1 − i` pairs):

```text
( inside ) rest        inside has i pairs, rest has n − 1 − i pairs
```

The split is unique, and `i` ranges over `0..n−1`. By the product rule within a split and the sum rule across splits:

$$
\text{Cat}_n = \sum_{i=0}^{n-1} \text{Cat}_i\cdot \text{Cat}_{n-1-i},\qquad \text{Cat}_0 = 1.
$$

**Trace:**

| n | sum of products | Catₙ |
|---:|---|---:|
| 0 | base case (the empty string) | 1 |
| 1 | 1·1 | 1 |
| 2 | 1·1 + 1·1 | 2 |
| 3 | 1·2 + 1·1 + 2·1 | 5 |
| 4 | 1·5 + 1·2 + 2·1 + 5·1 | 14 |

The sequence continues 42, 132, 429, …

The recurrence costs O(n²). There is also a **closed form**:

$$
\text{Cat}_n = \binom{2n}{n} - \binom{2n}{n+1} = \frac{1}{n+1}\binom{2n}{n}.
$$

**Why (the reflection argument).** Read `(` as a step up and `)` as a step down. Any string with `n` of each is a path from height 0 back to 0: `C(2n, n)` paths. A string is **bad** when the path dips to height −1. Take a bad path and flip every step after the first time it reaches −1. The flipped path ends at −2, so it has `n − 1` ups and `n + 1` downs. Flipping is reversible (flip back after the first −1), so bad paths match paths ending at −2 one to one, and there are `C(2n, n + 1)` of those.

The same numbers count many other structures, each splitting the same way into "a first piece and the rest": binary trees with `n` nodes (left subtree and right subtree), triangulations of a convex polygon with `n + 2` sides, monotone lattice paths that stay below the diagonal, and valid push/pop sequences of a stack.

```python
import math
from itertools import product


def is_balanced(s: str) -> bool:
    depth = 0
    for ch in s:
        depth += 1 if ch == "(" else -1
        if depth < 0:
            return False
    return depth == 0


def catalan_brute(n: int) -> int:
    return sum(1 for chars in product("()", repeat=2 * n) if is_balanced(chars))


def catalan_dp(n_max: int) -> list[int]:
    cat = [0] * (n_max + 1)
    cat[0] = 1
    for n in range(1, n_max + 1):
        cat[n] = sum(cat[i] * cat[n - 1 - i] for i in range(n))
    return cat


def main():
    cat = catalan_dp(30)
    assert cat[:7] == [1, 1, 2, 5, 14, 42, 132]
    for n in range(9):
        assert catalan_brute(n) == cat[n] == math.comb(2 * n, n) // (n + 1)
    for n in range(31):
        assert cat[n] == math.comb(2 * n, n) - math.comb(2 * n, n + 1)


if __name__ == "__main__":
    main()
```

## 8. Inclusion–exclusion

**Problem.** How many integers in `1..30` are divisible by 2, 3 or 5?

Adding the three counts double-counts: `15 + 10 + 6 = 31`, more than 30 numbers. A number like 6 is counted by both 2 and 3. **Inclusion–exclusion** fixes this: add single sets, subtract pairwise overlaps, add back triple overlaps, and so on.

$$
|A\cup B\cup C| = |A|+|B|+|C| - |A\cap B| - |A\cap C| - |B\cap C| + |A\cap B\cap C|.
$$

Numbers divisible by both 2 and 3 are the multiples of `lcm(2, 3) = 6`, so each overlap is one floor division:

| Subset of {2, 3, 5} | lcm | ⌊30 / lcm⌋ | sign |
|---|---:|---:|:---:|
| {2} | 2 | 15 | + |
| {3} | 3 | 10 | + |
| {5} | 5 | 6 | + |
| {2, 3} | 6 | 5 | − |
| {2, 5} | 10 | 3 | − |
| {3, 5} | 15 | 2 | − |
| {2, 3, 5} | 30 | 1 | + |

Total: `15 + 10 + 6 − 5 − 3 − 2 + 1 = 22`. (The 8 numbers left over are 1 and the primes 7, 11, 13, 17, 19, 23, 29.)

**Why every number is counted exactly once.** Suppose `x` is divisible by exactly `t ≥ 1` of the given numbers. It appears in `C(t, 1)` single terms, `C(t, 2)` pairs, and so on, so its total weight is `C(t,1) − C(t,2) + C(t,3) − ⋯ = 1 − (1 − 1)^t = 1`.

With `s` numbers there are `2^s − 1` nonempty subsets, so this works for `s` up to about 20. Iterating subsets with a bitmask is covered in [Bit Manipulation](../11-bit-manipulation/README.md).

### Variant: derangements

**Problem.** `n` people throw their hats in a pile and each grabs one at random. In how many of the `n!` outcomes does **nobody** get their own hat? Such a permutation is a **derangement**.

Let `Aᵢ` be the permutations where person `i` gets their own hat. Fixing any `j` specific people leaves `(n − j)!` permutations of the rest, and there are `C(n, j)` ways to choose those people. By the complement rule and inclusion–exclusion:

$$
D_n = \sum_{j=0}^{n} (-1)^j \binom{n}{j}(n-j)! = n!\sum_{j=0}^{n}\frac{(-1)^j}{j!}.
$$

The sum is the start of the series for `e^(−1)`, so about `n!/e`, or 36.8% of all permutations, are derangements.

There is also a recurrence: `D_n = (n − 1)(D_{n−1} + D_{n−2})`, with `D_0 = 1, D_1 = 0`. Person 1's hat goes to someone else, say person `k` (`n − 1` choices). Then two cases:

- `k` takes hat 1. Persons 1 and `k` have swapped, and the other `n − 2` people derange: `D_{n−2}`.
- `k` does not take hat 1. Pretend hat 1 is `k`'s own hat. Now the `n − 1` people other than person 1 must each avoid "their own" hat: `D_{n−1}`.

| n | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `D_n` | 1 | 0 | 1 | 2 | 9 | 44 | 265 |

```python
import math
import random
from itertools import permutations


def count_divisible_by_any(n: int, divisors: list[int]) -> int:
    if any(d <= 0 for d in divisors):
        raise ValueError("divisors must be positive")
    total = 0
    s = len(divisors)
    for mask in range(1, 1 << s):
        l = 1
        for i in range(s):
            if mask >> i & 1:
                l = math.lcm(l, divisors[i])
        sign = 1 if bin(mask).count("1") % 2 else -1
        total += sign * (n // l)
    return total


def derangements_formula(n: int) -> int:
    return sum((-1) ** j * math.comb(n, j) * math.factorial(n - j) for j in range(n + 1))


def derangements_recurrence(n_max: int) -> list[int]:
    d = [1, 0] + [0] * max(0, n_max - 1)
    for n in range(2, n_max + 1):
        d[n] = (n - 1) * (d[n - 1] + d[n - 2])
    return d[: n_max + 1]


def main():
    assert count_divisible_by_any(30, [2, 3, 5]) == 22
    rng = random.Random(10)
    for _ in range(300):
        n = rng.randint(0, 500)
        divs = [rng.randint(1, 40) for _ in range(rng.randint(0, 5))]
        brute = sum(1 for x in range(1, n + 1) if any(x % d == 0 for d in divs))
        assert count_divisible_by_any(n, divs) == brute

    d = derangements_recurrence(20)
    assert d[:7] == [1, 0, 1, 2, 9, 44, 265]
    for n in range(8):
        brute = sum(1 for p in permutations(range(n)) if all(p[i] != i for i in range(n)))
        assert brute == d[n] == derangements_formula(n)
    for n in range(1, 16):  # floats stay exact enough up to here
        assert d[n] == round(math.factorial(n) / math.e)


if __name__ == "__main__":
    main()
```

Inclusion–exclusion over `s` sets costs O(2^s · s) here; derangements O(n).

## 9. The pigeonhole principle

If you put `n + 1` pigeons into `n` holes, some hole holds at least two pigeons. It sounds too plain to be useful, but it **guarantees that something exists**, and the proof often tells you how to find it.

**Problem.** Given `n` integers, show that some nonempty contiguous subarray has a sum divisible by `n`, and find one.

**Key observation.** Look at the `n + 1` prefix sums `S_0 = 0, S_1, …, S_n`, where `S_i` is the sum of `a[:i]`, and their remainders mod `n`. There are only `n` possible remainders, so two prefixes `i < j` share one. Then `S_j − S_i`, the sum of `a[i:j]`, is divisible by `n`.

**Trace** with `a = [3, 1, 4, 1, 5]`, `n = 5`:

| i | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| `S_i` | 0 | 3 | 4 | 8 | 9 | 14 |
| `S_i mod 5` | 0 | 3 | 4 | **3** | 4 | 4 |
| action | store 0→0 | store 3→1 | store 4→2 | 3 seen at 1: stop | | |

The remainder 3 repeats at prefixes 1 and 3, so `a[1:3] = [1, 4]` has sum 5. ✓ The scan stops at the first repeat: O(n) time with a dictionary from remainder to first index. The prefix-sum idea comes from [Prefix Sums](../04-range-queries/01-prefix-sums.md).

Other pigeonhole facts you will meet: among any `n + 1` numbers from `1..2n`, two are consecutive (pair the holes `{1,2}, {3,4}, …`); and in "find the duplicate number" (`n + 1` values in `1..n`), a duplicate must exist before any algorithm starts.

```python
import random


def subarray_divisible_by_n(a: list[int]) -> tuple[int, int]:
    """Return (i, j) with i < j and sum(a[i:j]) % len(a) == 0."""
    n = len(a)
    if n == 0:
        raise ValueError("need at least one number")
    first = {0: 0}
    prefix = 0
    for j in range(1, n + 1):
        prefix += a[j - 1]
        r = prefix % n
        if r in first:
            return first[r], j
        first[r] = j
    raise AssertionError("unreachable by the pigeonhole principle")


def main():
    assert subarray_divisible_by_n([3, 1, 4, 1, 5]) == (1, 3)
    assert subarray_divisible_by_n([7]) == (0, 1)
    rng = random.Random(11)
    for _ in range(3000):
        n = rng.randint(1, 12)
        a = [rng.randint(-50, 50) for _ in range(n)]
        i, j = subarray_divisible_by_n(a)
        assert 0 <= i < j <= n and sum(a[i:j]) % n == 0


if __name__ == "__main__":
    main()
```

## 10. Summary

| Situation | Count | Section |
|---|---|---|
| Steps with `a`, then `b` options | `a · b` | §1 |
| "At least one" | total − "none" | §1 |
| Arrange `n` distinct items | `n!` | §2 |
| Ordered choice of `k` from `n` | `P(n, k) = n! / (n − k)!` | §2 |
| Unordered choice of `k` from `n` | `C(n, k) = n! / (k! (n − k)!)` | §2 |
| Arrange with repeated items | `n! / (c₁! c₂! ⋯)` | §2 |
| `k` identical items into `n` labeled boxes | `C(k + n − 1, n − 1)`; nonempty: `C(k − 1, n − 1)` | §6 |
| Balanced brackets, binary trees, triangulations | `Catₙ = C(2n, n) / (n + 1)` | §7 |
| Union of overlapping sets | Inclusion–exclusion: odd subsets add, even subtract | §8 |
| Nobody in their own place | `D_n = (n − 1)(D_{n−1} + D_{n−2})` ≈ `n!/e` | §8 |
| "Some pair must exist" | Pigeonhole on remainders | §9 |

Which way to compute `C(n, k)` in a program:

| Situation | Method | Cost |
|---|---|---|
| Any modulus (even composite), `n` up to a few thousand | Pascal's triangle | O(n²) once |
| Prime `p > n`, many queries | Factorials and inverse factorials | O(n) once, O(1) per query |
| Small prime `p ≤ n` | Lucas's theorem | O(p + log_p n) per query |
| Exact value, no modulus | `math.comb` | big integers |

Every closed formula above, checked against brute-force listing:

```python
import math
from itertools import combinations, permutations, product


def multinomial(counts: list[int]) -> int:
    return math.factorial(sum(counts)) // math.prod(math.factorial(c) for c in counts)


def stars_and_bars(k: int, n: int, nonempty: bool = False) -> int:
    """Ways to put k identical items into n labeled boxes."""
    if k < 0 or n < 0:
        raise ValueError("k and n must be nonnegative")
    if n == 0:
        return 1 if k == 0 else 0
    if nonempty:
        return math.comb(k - 1, n - 1) if k >= n else 0
    return math.comb(k + n - 1, n - 1)


def main():
    pins = list(product(range(10), repeat=4))  # §1
    assert sum(1 for pin in pins if len(set(pin)) == 4) == 10 * 9 * 8 * 7
    assert sum(1 for pin in pins if len(set(pin)) < 4) == 10**4 - 5040 == 4960
    assert sum(1 for pin in pins if pin[0] == 0 or pin[3] == 0) == 1000 + 1000 - 100
    for n in range(7):  # §2
        assert len(list(permutations(range(n)))) == math.factorial(n)
        assert sum(math.comb(n, k) for k in range(n + 1)) == 2**n
        for k in range(n + 1):
            assert len(list(permutations(range(n), k))) == math.perm(n, k)
            assert len(list(combinations(range(n), k))) == math.comb(n, k) == math.comb(n, n - k)
    for word in ("", "A", "AAB", "LETTER", "BANANA", "AABBCC"):
        counts = [word.count(ch) for ch in set(word)]
        assert len(set(permutations(word))) == multinomial(counts)
    assert stars_and_bars(5, 3) == 21 and stars_and_bars(5, 3, nonempty=True) == 6  # §6
    for n in range(5):
        for k in range(7):
            fills = [f for f in product(range(k + 1), repeat=n) if sum(f) == k]
            assert stars_and_bars(k, n) == len(fills)
            assert stars_and_bars(k, n, True) == sum(1 for f in fills if min(f, default=1) >= 1)


if __name__ == "__main__":
    main()
```

## 11. Pitfalls and practice

1. Mixing up ordered and unordered counts. Ask "would swapping two chosen items give a different answer?" Yes means permutations, no means combinations.
2. Adding overlapping cases. The sum rule needs disjoint groups; otherwise use inclusion–exclusion.
3. Forgetting `C(n, k) = 0` for `k < 0` or `k > n`. Formulas with negative factorial indices crash or return garbage.
4. Using factorials and inverses when `n ≥ p`. Then `n! ≡ 0 (mod p)`; use Lucas's theorem.
5. Using factorial inverses with a composite modulus. Use Pascal's triangle, or factor the modulus and combine with the Chinese remainder theorem.
6. Overflow in C++ when multiplying three residues: reduce after each product.
7. Wrong signs in inclusion–exclusion: odd-sized subsets add, even-sized subtract.
8. Using a product of divisors instead of their lcm for the overlaps (`{4, 6}` overlap at multiples of 12, not 24).
9. Off-by-one in stars and bars: `k` items in `n` boxes need `n − 1` bars, not `n`.

Practice: unique paths in a grid (`C(m + n − 2, m − 1)`); Pascal's triangle; generate parentheses; unique binary search trees; count sorted vowel strings (stars and bars); number of ways to reach a position after exactly `k` steps; count anagrams (multinomials mod a prime); count all valid pickup and delivery options; the derangement problem ("find the derangement of an array"); make sum divisible by `P` (prefix remainders); find the duplicate number (pigeonhole).

Next: [Geometry](03-geometry.md).
