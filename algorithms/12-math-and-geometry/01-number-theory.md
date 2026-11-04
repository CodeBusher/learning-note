# Number Theory — Remainders, GCD, Primes, and Modular Arithmetic

## 1. Remainders: what time is it?

It is 9 o'clock. What time will it be in 100 hours? A clock wraps around every 12 hours, so only the **remainder** of `9 + 100` after removing whole 12-hour turns matters:

```text
9 + 100 = 109 = 9 · 12 + 1    →    1 o'clock
```

Two numbers come out of every division of an integer `a` by a positive integer `m`:

$$
a = q\cdot m + r,\qquad 0 \le r < m.
$$

`q` is the **quotient** and `r` the **remainder**. We say `m` **divides** `a`, written `m | a`, when the remainder is 0. For example `4 | 12` but `4` does not divide `10`.

### Negative numbers: Python and C disagree

What time was it 100 hours *before* 9 o'clock? `9 − 100 = −91`. Mathematically the remainder must be in `0..11`, and `−91 = −8 · 12 + 5`, so the answer is 5 o'clock. Python agrees; C, C++ and Java do not:

| Expression | Python | C / C++ / Java |
|---|---:|---:|
| `-91 // 12` (quotient) | −8 (rounds down) | −7 (rounds toward zero) |
| `-91 % 12` (remainder) | 5 | −7 |

Python rounds the quotient **down** (toward minus infinity), so with a positive modulus the remainder is always in `0..m−1`. C rounds **toward zero**, so the remainder takes the sign of `a`. Both languages keep `a == (a // m) * m + a % m` true; they only choose a different `q`.

When you port code to C-like languages, write `((a % m) + m) % m` to get the mathematical remainder. In Python, `a % m` is already correct for `m > 0`.

## 2. Greatest common divisor: Euclid's algorithm

**Problem.** You have a 1071 × 462 rectangle and want to tile it with equal squares, as large as possible. The square's side must divide both 1071 and 462, so you want their **greatest common divisor**, `gcd(1071, 462)`. (The answer is 21.)

**Brute force.** Try every `d` from `min(a, b)` down to 1 and stop at the first one that divides both. That is up to `min(a, b)` divisions: a billion for numbers near `10^9`.

**Key observation.** If `d` divides `a` and `b`, it divides `a − b`, and so it divides `a − q·b = a mod b` for any `q`. The reverse also holds: a divisor of `b` and `a mod b` divides `a = q·b + (a mod b)`. So the pairs `(a, b)` and `(b, a mod b)` have **exactly the same common divisors**, and therefore the same gcd:

$$
\gcd(a, b) = \gcd(b,\ a \bmod b),\qquad \gcd(a, 0) = a.
$$

The base case says every number divides 0, so the common divisors of `a` and 0 are the divisors of `a`, the largest being `a` itself.

**Trace** on `(1071, 462)`. Each row replaces `(a, b)` with `(b, a mod b)`:

| Step | a | b | a = q·b + r | r = a mod b |
|---:|---:|---:|---|---:|
| 1 | 1071 | 462 | 1071 = 2·462 + 147 | 147 |
| 2 | 462 | 147 | 462 = 3·147 + 21 | 21 |
| 3 | 147 | 21 | 147 = 7·21 + 0 | 0 |
| 4 | 21 | 0 | stop | |

Three divisions instead of hundreds. In the rectangle, step 1 cuts two 462 × 462 squares off the 1071 × 462 rectangle, leaving 147 × 462; step 2 cuts three 147-squares, leaving 147 × 21; step 3 cuts seven 21-squares and nothing is left.

### Why it finishes fast

Look at two consecutive steps, `(a, b) → (b, r) → (r, r')`. Claim: `r < a / 2`. Two cases:

- If `b ≤ a/2`, then `r < b ≤ a/2`.
- If `b > a/2`, then `a` contains `b` only once, so `r = a − b < a/2`.

So every two steps the first number at least halves. Starting from `a`, there are at most about `2·log₂(a)` steps: around 60 for 32-bit numbers, 128 for 64-bit numbers. The worst case is consecutive Fibonacci numbers (Lamé's theorem), where every quotient is 1.

Time O(log min(a, b)) division steps; space O(1). The code, tested against a brute force, is with extended Euclid in §3; Python's `math.gcd` and `math.lcm` do the same job.

### Variant: least common multiple

Two buses leave together; one returns every 4 minutes, the other every 6. They meet again after `lcm(4, 6) = 12` minutes, the smallest positive number both divide. In prime factorizations (§4), `gcd` takes the **smaller** power of each prime and `lcm` the **larger**, and `min + max` of two exponents is their sum, so

$$
\gcd(a, b)\cdot \operatorname{lcm}(a, b) = a\cdot b.
$$

Compute it as `a // gcd(a, b) * b`: divide **before** multiplying. In C++ or Java, `a * b` can overflow 64 bits even when the lcm fits.

## 3. Extended Euclid: writing the gcd as a combination

**Problem.** Find integers `x, y` with `240x + 46y = gcd(240, 46) = 2`. Such `x, y` always exist (this is **Bézout's identity**), and they are the key to modular inverses (§9) and the Chinese remainder theorem (§10).

**Key observation.** Suppose the recursive call on `(b, a mod b)` already found `x₁, y₁` with

$$
b\,x_1 + (a \bmod b)\,y_1 = g.
$$

Substitute `a mod b = a − q·b`, where `q = a // b`:

$$
b\,x_1 + (a - q b)\,y_1 = a\,y_1 + b\,(x_1 - q\,y_1) = g.
$$

So for `(a, b)` take `x = y₁` and `y = x₁ − q·y₁`. At the base case `(g, 0)`, take `x = 1, y = 0`, since `g·1 + 0·0 = g`.

**Trace.** Go down the Euclid chain, then **back-substitute** on the way up:

| Call | q = a // b | Coefficients from the call below (x₁, y₁) | x = y₁ | y = x₁ − q·y₁ | Check a·x + b·y |
|---|---:|---|---:|---:|---|
| (2, 0) | — | base case | 1 | 0 | 2·1 = 2 |
| (4, 2) | 2 | (1, 0) | 0 | 1 − 2·0 = 1 | 4·0 + 2·1 = 2 |
| (6, 4) | 1 | (0, 1) | 1 | 0 − 1·1 = −1 | 6 − 4 = 2 |
| (10, 6) | 1 | (1, −1) | −1 | 1 − 1·(−1) = 2 | −10 + 12 = 2 |
| (46, 10) | 4 | (−1, 2) | 2 | −1 − 4·2 = −9 | 92 − 90 = 2 |
| (240, 46) | 5 | (2, −9) | −9 | 2 − 5·(−9) = 47 | −2160 + 2162 = 2 |

Read the calls bottom-up, the answers top-down. Result: `240·(−9) + 46·47 = 2`.

Solutions are not unique: if `(x, y)` works, so does `(x + k·b/g, y − k·a/g)` for every integer `k`. The algorithm returns a small one, with `|x| ≤ b/g` and `|y| ≤ a/g`.

The iterative version below avoids recursion by keeping `old_r = a·old_x + b·old_y` and `r = a·x + b·y` true at every step.

```python
import math
import random


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else abs(a // gcd(a, b) * b)


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) with a*x + b*y == g == gcd(a, b) >= 0."""
    old_r, r, old_x, x, old_y, y = a, b, 1, 0, 0, 1
    while r:  # Invariant: old_r == a*old_x + b*old_y and r == a*x + b*y.
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_x, x = x, old_x - q * x
        old_y, y = y, old_y - q * y
    if old_r < 0:
        old_r, old_x, old_y = -old_r, -old_x, -old_y
    return old_r, old_x, old_y


def extended_gcd_recursive(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0) if a >= 0 else (-a, -1, 0)
    g, x1, y1 = extended_gcd_recursive(b, a % b)
    return g, y1, x1 - (a // b) * y1


def euclid_steps(a: int, b: int) -> int:
    steps = 0
    while b:
        a, b, steps = b, a % b, steps + 1
    return steps


def gcd_brute(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    if a == 0 or b == 0:
        return a + b
    return max(d for d in range(1, min(a, b) + 1) if a % d == 0 and b % d == 0)


def main():
    assert gcd(1071, 462) == 21 and euclid_steps(1071, 462) == 3
    assert gcd(0, 0) == 0 and gcd(-12, 18) == 6 and lcm(-4, 6) == 12 and lcm(0, 5) == 0
    assert extended_gcd(240, 46) == extended_gcd_recursive(240, 46) == (2, -9, 47)
    rng = random.Random(1)
    for _ in range(2000):
        a, b = rng.randint(-200, 200), rng.randint(-200, 200)
        assert gcd(a, b) == gcd_brute(a, b) == math.gcd(a, b)
        assert lcm(a, b) == math.lcm(a, b)
        a, b = rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6)
        for f in (extended_gcd, extended_gcd_recursive):
            g, x, y = f(a, b)
            assert g == math.gcd(a, b) and a * x + b * y == g
    fib = [1, 1]
    while len(fib) < 90:
        fib.append(fib[-1] + fib[-2])
    assert euclid_steps(fib[-1], fib[-2]) == 88  # Fibonacci: the worst case
    for _ in range(1000):
        assert euclid_steps(rng.randint(1, 2**64), rng.randint(1, 2**64)) <= 2 * 64 + 2


if __name__ == "__main__":
    main()
```

Time O(log min(|a|, |b|)); space O(1) iterative, O(log) recursive.

## 4. Primes by trial division

A **prime** is an integer `p ≥ 2` whose only positive divisors are 1 and `p`. Every other integer `n ≥ 2` is **composite**: `n = a·b` with `1 < a ≤ b < n`.

**Key observation.** In `n = a·b` with `a ≤ b`, the smaller factor satisfies `a·a ≤ a·b = n`, so `a ≤ √n`. A composite number always has a divisor in `2..√n`. Testing only that far is enough:

```text
n = 91:   d = 2 .. 6 fail, d = 7 divides: 91 = 7 · 13          → composite
n = 97:   d = 2 .. 9 fail, and 10 · 10 = 100 > 97, so stop     → prime
```

The same loop **factorizes** `n`: divide out each `d` as long as it divides, and whatever remains above 1 at the end is a prime larger than `√(original n)`.

Both appear in the combined script in §6. Trial division costs O(√n) per number: fine for one number up to `10^12`, too slow for a million numbers.

## 5. Sieve of Eratosthenes

**Problem.** List every prime up to `n = 30`. Testing each number separately costs O(n√n). The sieve does it in O(n log log n), which is close to linear.

**Key observation.** Instead of asking "is `k` prime?" for every `k`, let each prime `p` **cross out its multiples**. Anything never crossed out has no smaller prime factor, so it is prime. Two refinements:

- Start crossing out at `p·p`. Any smaller multiple `p·j` with `j < p` has the prime factor of `j`, which is smaller than `p`, so it was already crossed out.
- Stop once `p·p > n`. By §4, every composite `≤ n` has a prime factor `≤ √n`.

**Trace** on 1..30 (`.` means crossed out or not prime):

```text
after p = 2 (from 4)               after p = 3 (from 9) and p = 5 (from 25)
 .  2  3  .  5  .  7  .  9  .       .  2  3  .  5  .  7  .  .  .
11  . 13  . 15  . 17  . 19  .      11  . 13  .  .  . 17  . 19  .
21  . 23  . 25  . 27  . 29  .       .  . 23  .  .  .  .  . 29  .
```

`p = 3` crosses out 9, 15, 21, 27 (12, 18, 24, 30 were already gone). `p = 5` adds only 25. Next is `p = 7`, but `7·7 = 49 > 30`, so we stop. The survivors are the 10 primes `2, 3, 5, 7, 11, 13, 17, 19, 23, 29`.

**Why O(n log log n)?** Prime `p` crosses out about `n/p` numbers. The sum `n·(1/2 + 1/3 + 1/5 + …)` over primes up to `n` grows like `n·ln ln n`, which is below `4n` for any `n` you will meet.

## 6. Linear sieve, smallest prime factors, and factorization

The plain sieve crosses some numbers out more than once (30 is hit by 2, 3 and 5). A **linear sieve** crosses out every composite exactly once and records its **smallest prime factor** `spf[k]` along the way. With `spf`, factorizing any `k ≤ n` takes only O(log k) steps: divide by `spf[k]`, repeat.

**Key observation.** Write each composite as `c = p·i`, where `p = spf[c]`. Then `i = c / p` has no prime factor smaller than `p`, so `p ≤ spf[i]`. So: for each `i`, multiply by each prime `p` **up to** `spf[i]`, and mark `spf[p·i] = p`. Each composite is produced once, from its unique pair `(p, i)`.

**Trace** for `n = 30`. `primes` grows as we go; we stop the inner loop when `p > spf[i]` or `p·i > 30`:

| i | spf[i] | primes so far | marks spf[p·i] = p |
|---:|---:|---|---|
| 2 | 2 (new prime) | 2 | 4←2 |
| 3 | 3 (new prime) | 2, 3 | 6←2, 9←3 |
| 4 | 2 | 2, 3 | 8←2, then stop: 3 > spf[4] |
| 5 | 5 (new prime) | 2, 3, 5 | 10←2, 15←3, 25←5 |
| 7 | 7 (new prime) | 2, 3, 5, 7 | 14←2, 21←3, then stop: 5·7 > 30 |
| 9 | 3 | | 18←2, 27←3 |
| 15 | 3 | | 30←2, then stop: 3·15 > 30 |

Every even `i` marks only `2i` (because `spf[i] = 2`), and once `i > 15` even `2i > 30`, so nothing more is marked; 11, 13, 17, 19, 23, 29 join `primes`. Each of the 19 composites up to 30 was marked once.

Factorizing `360` with `spf`: `360 → 2 → 180 → 2 → 90 → 2 → 45 → 3 → 15 → 3 → 5 → 5 → 1`, so `360 = 2³ · 3² · 5`.

### Counting divisors

A divisor of `n = p₁^e₁ · p₂^e₂ ⋯` picks, independently for each prime, an exponent from `0..eᵢ`. That is `eᵢ + 1` choices per prime, so by the product rule:

$$
d(n) = \prod_i (e_i + 1),\qquad d(360) = (3+1)(2+1)(1+1) = 24.
$$

The sum of divisors works the same way: `σ(n) = ∏ (1 + pᵢ + pᵢ² + ⋯ + pᵢ^eᵢ)`.

```python
import math
import random
from collections import Counter


def factorize_trial(n: int) -> Counter:
    if n < 1:
        raise ValueError("n must be positive")
    factors = Counter()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] += 1
            n //= d
        d += 1
    if n > 1:
        factors[n] += 1
    return factors


def sieve(n: int) -> list[bool]:
    """is_prime[k] for 0 <= k <= n."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    is_prime = [True] * (n + 1)
    is_prime[0] = False
    if n >= 1:
        is_prime[1] = False
    p = 2
    while p * p <= n:
        if is_prime[p]:
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
        p += 1
    return is_prime


def linear_sieve(n: int) -> tuple[list[int], list[int]]:
    """Return (spf, primes); spf[k] is the smallest prime factor of k >= 2."""
    spf = [0] * (n + 1)
    primes = []
    for i in range(2, n + 1):
        if spf[i] == 0:
            spf[i] = i
            primes.append(i)
        for p in primes:
            if p > spf[i] or p * i > n:
                break
            spf[p * i] = p
    return spf, primes


def factorize_spf(k: int, spf: list[int]) -> Counter:
    if k < 1 or k >= len(spf):
        raise ValueError("k out of range of the sieve")
    factors = Counter()
    while k > 1:
        factors[spf[k]] += 1
        k //= spf[k]
    return factors


def count_divisors(factors: Counter) -> int:
    result = 1
    for e in factors.values():
        result *= e + 1
    return result


def main():
    flags = sieve(30)
    assert [k for k in range(31) if flags[k]] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert sieve(0) == [False] and sieve(1) == [False, False]
    n = 5000
    flags = sieve(n)
    spf, primes = linear_sieve(n)
    assert primes == [k for k in range(n + 1) if flags[k]]
    assert factorize_spf(360, spf) == Counter({2: 3, 3: 2, 5: 1})
    assert count_divisors(factorize_spf(360, spf)) == 24
    assert factorize_trial(2 * 97) == Counter({2: 1, 97: 1})  # the leftover prime
    assert factorize_trial(10**12 + 39) == Counter({10**12 + 39: 1})  # a prime
    for k in range(1, n + 1):
        f = factorize_trial(k)
        assert flags[k] == (k > 1 and f == Counter({k: 1}))  # sieve vs trial division
        assert factorize_spf(k, spf) == f and (k == 1 or spf[k] == min(f))
        assert math.prod(p**e for p, e in f.items()) == k
    rng = random.Random(3)
    for k in rng.sample(range(1, n + 1), 300):
        assert count_divisors(factorize_trial(k)) == sum(1 for d in range(1, k + 1) if k % d == 0)


if __name__ == "__main__":
    main()
```

## 7. Modular arithmetic

Many counting answers are astronomically large, so problems ask for them **modulo** a number `m`, usually the prime `10^9 + 7` or `998244353`. We write `a ≡ b (mod m)`, read "a is congruent to b mod m", when `m | (a − b)`: `a` and `b` leave the same remainder.

**Addition, subtraction and multiplication** respect remainders. You may reduce at any moment:

$$
(a + b) \bmod m = ((a \bmod m) + (b \bmod m)) \bmod m,\qquad (a\cdot b) \bmod m = ((a \bmod m)(b \bmod m)) \bmod m.
$$

Why: write `a = q₁m + r₁` and `b = q₂m + r₂`. Then `a·b = (stuff)·m + r₁r₂`, and the multiples of `m` vanish in the remainder. Check: `17 · 23 = 391 ≡ 1 (mod 5)`, and `2 · 3 = 6 ≡ 1`. ✓

**Division does not.** `6 ≡ 2 (mod 4)`, but `6/2 = 3` and `2/2 = 1` are not congruent mod 4. Division by `a` is allowed only as multiplication by a **modular inverse** `a⁻¹`, a number with `a·a⁻¹ ≡ 1 (mod m)`, and that exists exactly when `gcd(a, m) = 1` (§9).

In C++ or Java, reduce after **every** multiplication: two numbers below `10^9 + 7` multiply to about `10^18`, which fits in a signed 64-bit integer (limit about `9.2·10^18`), but three do not.

## 8. Fast exponentiation by squaring

**Problem.** Compute `3^13 mod 1000`. Multiplying 3 by itself 12 times is fine here, but `a^(10^18)` would take `10^18` steps.

**Key observation.** Write the exponent in binary: `13 = 1101₂ = 8 + 4 + 1`, so `3^13 = 3^8 · 3^4 · 3^1`. The powers `3^1, 3^2, 3^4, 3^8, …` come from repeated squaring. Walk the bits from the lowest: square the base every step, and multiply it into the result when the bit is 1.

**Invariant:** `result · base^e ≡ 3^13 (mod 1000)` at the start of every step.

**Trace** (`e` shown in binary, all values mod 1000):

| Step | e | lowest bit | base before | result after | base after squaring |
|---:|---|---:|---:|---:|---:|
| 1 | 1101 | 1 | 3 (= 3¹) | 1 · 3 = 3 | 9 (= 3²) |
| 2 | 110 | 0 | 9 | 3 | 81 (= 3⁴) |
| 3 | 11 | 1 | 81 | 3 · 81 = 243 | 6561 mod 1000 = 561 (= 3⁸) |
| 4 | 1 | 1 | 561 | 243 · 561 = 136323 → 323 | 721 |

`e` becomes 0 and the answer is `323`. Check: `3^13 = 1594323`. ✓ The loop runs once per bit: O(log e) multiplications.

The same loop works for anything you can multiply associatively: matrices (Fibonacci in O(log n), see [Faster Transitions](../09-dynamic-programming/12-faster-transitions.md)), permutations, or polynomials. Python's built-in `pow(a, e, m)` does exactly this.

```python
import random


def power_mod(base: int, exp: int, mod: int) -> int:
    if exp < 0:
        raise ValueError("exp must be nonnegative")
    if mod < 1:
        raise ValueError("mod must be positive")
    result = 1 % mod
    base %= mod
    while exp:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result


def main():
    assert power_mod(3, 13, 1000) == 323
    assert power_mod(5, 0, 1) == 0 and power_mod(5, 0, 7) == 1
    assert power_mod(-2, 3, 7) == (-8) % 7
    rng = random.Random(4)
    for _ in range(2000):
        b = rng.randint(-1000, 1000)
        e = rng.randint(0, 60)
        m = rng.randint(1, 10**9)
        assert power_mod(b, e, m) == pow(b, e, m) == (b ** e) % m
    assert power_mod(2, 10**18, 10**9 + 7) == pow(2, 10**18, 10**9 + 7)


if __name__ == "__main__":
    main()
```

Time O(log exp) multiplications; space O(1).

## 9. Modular inverse: two ways

**Problem.** Solve `3x ≡ 1 (mod 11)`. Brute force tries `x = 1..10`: `3·4 = 12 ≡ 1`, so `x = 4`. That is O(m) per inverse; we want O(log m).

**When does an inverse exist?** If `g = gcd(a, m) > 1`, then `a·x − 1` would have to be a multiple of `m`, hence of `g`; but `g` divides `a·x`, so it would divide 1. Impossible. So `a` is invertible mod `m` **exactly when** `gcd(a, m) = 1`.

**Way 1: extended Euclid (any modulus).** Find `x, y` with `a·x + m·y = 1`. Reduce mod `m`: `a·x ≡ 1`. For `(3, 11)`: `11 = 3·3 + 2`, `3 = 1·2 + 1`; back-substituting gives `3·4 + 11·(−1) = 1`, so the inverse is 4.

**Way 2: Fermat's little theorem (prime modulus).** If `p` is prime and `p` does not divide `a`, then `a^(p−1) ≡ 1 (mod p)`. Split off one factor: `a · a^(p−2) ≡ 1`, so

$$
a^{-1} \equiv a^{p-2} \pmod p.
$$

For `(3, 11)`: `3^9 = 19683 = 1789·11 + 4`. ✓

Extended Euclid works for any modulus; Fermat needs a prime and returns a wrong number, not an error, for a composite one. Both, and the linear recurrence below, are tested in the script at the end of §10.

Python 3.8+ also offers `pow(a, -1, m)`, which raises `ValueError` when no inverse exists.

For **many** inverses mod a prime, there is a linear-time recurrence: `inv[1] = 1`, and `inv[i] = −(p // i) · inv[p mod i] mod p`. It comes from `p = (p // i)·i + (p mod i)` reduced mod `p`. [Combinatorics](02-combinatorics.md) uses a different trick, inverse factorials, for the same purpose.


## 10. Chinese remainder theorem for two moduli

**Problem.** A number leaves remainder 2 when divided by 3 and remainder 3 when divided by 5. What is it? Brute force walks `2, 5, 8, …` (the numbers `≡ 2 mod 3`) and finds `8 ≡ 3 (mod 5)`. Every `8 + 15k` also works, so the answer is `x ≡ 8 (mod 15)`.

**Key observation.** Every solution of the first congruence has the form `x = a₁ + m₁·t`. Plug it into the second:

$$
m_1 t \equiv a_2 - a_1 \pmod{m_2}.
$$

This is one linear congruence in `t`. Let `g = gcd(m₁, m₂)`:

- If `g` does not divide `a₂ − a₁`, there is **no** solution (both congruences fix `x mod g`, and they disagree).
- Otherwise divide everything by `g` and multiply by the inverse of `m₁/g` modulo `m₂/g`: `t ≡ ((a₂ − a₁)/g) · (m₁/g)⁻¹ (mod m₂/g)`.

The answer is `x = a₁ + m₁·t`, unique modulo `lcm(m₁, m₂)`.

**Trace.** `x ≡ 2 (mod 3)`, `x ≡ 3 (mod 5)`. `g = 1`; solve `3t ≡ 1 (mod 5)`; inverse of 3 mod 5 is 2, so `t = 2` and `x = 2 + 3·2 = 8 (mod 15)`.

**Variant: moduli not coprime.** `x ≡ 2 (mod 4)`, `x ≡ 4 (mod 6)`. `g = 2` divides `4 − 2 = 2`. Reduced: `2t ≡ 1 (mod 3)`, inverse of 2 mod 3 is 2, so `t = 2`, `x = 2 + 4·2 = 10 (mod 12)`. Check: `10 mod 4 = 2`, `10 mod 6 = 4`. ✓

**Variant: no solution.** `x ≡ 1 (mod 4)`, `x ≡ 2 (mod 6)`. The first says `x` is odd, the second says even. `g = 2` does not divide `1`.

More than two congruences: fold them one at a time, replacing the pair with the combined `x mod lcm`.

```python
import math
import random


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    old_r, r, old_x, x, old_y, y = a, b, 1, 0, 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_x, x = x, old_x - q * x
        old_y, y = y, old_y - q * y
    return old_r, old_x, old_y


def inverse_euclid(a: int, m: int) -> int:
    if m < 1:
        raise ValueError("modulus must be positive")
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f"{a} has no inverse modulo {m}")
    return x % m


def inverse_fermat(a: int, p: int) -> int:
    """Only valid when p is prime and p does not divide a."""
    if a % p == 0:
        raise ValueError("0 has no inverse")
    return pow(a, p - 2, p)


def inverses_up_to(n: int, p: int) -> list[int]:
    inv = [0, 1] + [0] * max(0, n - 1)
    for i in range(2, n + 1):
        inv[i] = (-(p // i) * inv[p % i]) % p
    return inv[: n + 1]


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> tuple[int, int] | None:
    """Solve x = a1 (mod m1), x = a2 (mod m2). Return (x, lcm) or None."""
    if m1 < 1 or m2 < 1:
        raise ValueError("moduli must be positive")
    g, p, _ = extended_gcd(m1, m2)  # m1*p + m2*q = g, so p is (m1/g)^-1 mod m2/g
    diff = a2 - a1
    if diff % g:
        return None
    t = (diff // g) * p % (m2 // g)
    lcm = m1 // g * m2
    return (a1 + m1 * t) % lcm, lcm


def crt_many(pairs: list[tuple[int, int]]) -> tuple[int, int] | None:
    x, m = 0, 1
    for a, mod in pairs:
        combined = crt_pair(x, m, a, mod)
        if combined is None:
            return None
        x, m = combined
    return x, m


def main():
    assert inverse_euclid(3, 11) == 4 == inverse_fermat(3, 11)
    try:
        inverse_euclid(6, 9)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    assert 3 * inverse_fermat(3, 10) % 10 != 1  # Fermat is silently wrong for composite m
    rng = random.Random(5)
    for _ in range(2000):
        m, a = rng.randint(2, 500), rng.randint(-1000, 1000)
        brute = [x for x in range(m) if a * x % m == 1]
        if math.gcd(a, m) == 1:
            assert inverse_euclid(a, m) == brute[0] == pow(a, -1, m)
        else:
            assert brute == []
    p = 10**9 + 7
    for a in (1, 2, 12345, p - 1):
        assert inverse_fermat(a, p) == inverse_euclid(a, p)
    inv = inverses_up_to(1000, 1009)
    assert all(i * inv[i] % 1009 == 1 for i in range(1, 1001))

    assert crt_pair(2, 3, 3, 5) == (8, 15)
    assert crt_pair(2, 4, 4, 6) == (10, 12)
    assert crt_pair(1, 4, 2, 6) is None
    assert crt_many([(2, 3), (3, 5), (2, 7)]) == (23, 105)
    for _ in range(3000):
        m1, m2 = rng.randint(1, 30), rng.randint(1, 30)
        a1, a2 = rng.randint(-50, 50), rng.randint(-50, 50)
        lcm = math.lcm(m1, m2)
        brute = [x for x in range(lcm) if (x - a1) % m1 == 0 and (x - a2) % m2 == 0]
        assert crt_pair(a1, m1, a2, m2) == ((brute[0], lcm) if brute else None)
        assert len(brute) <= 1


if __name__ == "__main__":
    main()
```

Time O(log max(m₁, m₂)). Watch overflow in C++: `m1 * t` can reach `lcm`, which may exceed 64 bits for large moduli.

## 11. Advanced: Miller–Rabin primality test

Trial division needs `√n` steps: `4·10^9` for a 64-bit `n`. Miller–Rabin decides primality of any 64-bit number with about a dozen fast powers.

**Key observation 1.** By Fermat, a prime `n` satisfies `a^(n−1) ≡ 1` for every `a` not divisible by `n`. If some `a` breaks that, `n` is certainly composite. But some composites (Carmichael numbers, the smallest is 561) satisfy it for every coprime `a`, so Fermat alone is not enough.

**Key observation 2.** Modulo a prime, the only square roots of 1 are `1` and `−1` (because `x² − 1 = (x − 1)(x + 1)`, and a prime dividing a product divides a factor). So write `n − 1 = d·2^s` with `d` odd, and look at the sequence

$$
a^d,\ a^{2d},\ a^{4d},\ \dots,\ a^{2^s d} = a^{n-1} \pmod n,
$$

where each term is the square of the one before. For a prime `n`, this sequence either starts at 1, or hits `n − 1` somewhere before the end. Anything else proves `n` composite, and `a` is called a **witness**.

**Trace** with `n = 561 = 3·11·17`, `a = 2`. `560 = 35·2⁴`, so `d = 35`, `s = 4`, and the sequence is

```text
2^35, 2^70, 2^140, 2^280, 2^560  ≡  263, 166, 67, 1, 1   (mod 561)
```

Fermat's check (`2^560 ≡ 1`) passes, but `67² ≡ 1` while `67 ≢ ±1`: a square root of 1 that a prime could never have. So 561 is composite.

**Deterministic bases.** For a random composite, at most 1/4 of the bases fail to expose it. Better, it has been verified that the first twelve primes `2, 3, 5, …, 37` as bases correctly classify **every** `n < 3.1·10^23`, which covers all 64-bit integers (`2^64 ≈ 1.8·10^19`). (Seven special bases also suffice for 64-bit; the twelve primes are easier to remember.)

```python
import random

BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime_mr(n: int) -> bool:
    """Deterministic for n < 3.1e23, which covers every 64-bit integer."""
    if n < 2:
        return False
    for p in BASES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in BASES:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False  # a is a witness: n is composite
    return True


def is_prime_trial(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def main():
    assert [pow(2, 35 * 2**i, 561) for i in range(5)] == [263, 166, 67, 1, 1]  # the trace
    for n in range(20000):
        assert is_prime_mr(n) == is_prime_trial(n)
    rng = random.Random(7)
    for _ in range(300):
        n = rng.randint(10**9, 10**10)
        assert is_prime_mr(n) == is_prime_trial(n)
    carmichael = [561, 1105, 1729, 2465, 2821, 6601, 8911]
    assert not any(is_prime_mr(c) for c in carmichael)
    assert all(pow(2, c - 1, c) == 1 for c in carmichael)  # Fermat is fooled
    assert not is_prime_mr(3215031751)  # strong pseudoprime to bases 2, 3, 5, 7
    assert is_prime_mr(2**61 - 1)
    assert is_prime_mr(18446744073709551557)  # largest prime below 2**64
    assert not is_prime_mr(2**64 - 1)
    assert not is_prime_mr(4294967291 * 4294967279)  # two large primes


if __name__ == "__main__":
    main()
```

Time O(k log n) multiplications with `k = 12` bases; in C++ the `x * x % n` step needs 128-bit multiplication for 64-bit `n`.

To **factorize** a 64-bit number, Miller–Rabin is paired with Pollard's rho, which finds a factor in about `n^(1/4)` steps.

## 12. Summary

| Question | Tool | Cost | Section |
|---|---|---|---|
| Common divisor, reduce a ratio | Euclid: `gcd(a, b) = gcd(b, a mod b)` | O(log min(a, b)) | §2 |
| Common multiple | `a // gcd(a, b) * b` | same | §2 |
| Solve `ax + by = gcd(a, b)` | Extended Euclid, back-substitution | O(log min(a, b)) | §3 |
| Is one `n` prime, or factor it | Trial division up to `√n` | O(√n) | §4 |
| All primes up to `n` | Sieve of Eratosthenes | O(n log log n) build, O(n) memory | §5 |
| Factor many numbers up to `n` | Linear sieve with `spf` | O(n) build, O(log k) per number | §6 |
| Number of divisors | `∏ (eᵢ + 1)` from the factorization | after factoring | §6 |
| `a^e mod m` | Square and multiply over the bits of `e` | O(log e) | §8 |
| `a⁻¹ mod m`, any `m` | Extended Euclid; exists iff `gcd(a, m) = 1` | O(log m) | §9 |
| `a⁻¹ mod p`, prime `p` | Fermat: `a^(p−2)` | O(log p) | §9 |
| Inverses of `1..n` mod `p` | `inv[i] = −(p // i) · inv[p mod i]` | O(n) | §9 |
| Several remainder conditions | CRT, folding pairs; solvable iff `gcd(m₁, m₂)` divides `a₂ − a₁` | O(log m) per pair | §10 |
| Is a 64-bit `n` prime | Miller–Rabin with the first 12 primes as bases | O(12 log n) | §11 |

**Modular rules.** Reduce after every `+`, `−` and `×`. Never divide: multiply by an inverse, and check that it exists.

## 13. Pitfalls and practice

1. Assuming `%` has the same sign rules in every language. With a negative left side, C, C++ and Java return a negative remainder (§1).
2. Computing `a * b // gcd(a, b)` in fixed-width languages. Divide first: `a / gcd(a, b) * b` (§2).
3. Starting the sieve's inner loop at `2p` instead of `p·p` (correct but slower), or stopping the outer loop at `p < √n` instead of `p·p ≤ n` (misses squares of primes such as 25).
4. Treating 1 as prime, or 0 and 1 as composite and factorizable. Handle `n < 2` explicitly.
5. Forgetting the leftover prime after trial-division factorization (`factorize(2·97)` must report 97).
6. Using Fermat's inverse with a composite modulus. It silently returns a wrong number (§9).
7. Dividing modular values directly. `(a / b) mod m` must become `a · b⁻¹ mod m`, and `b⁻¹` must exist (§7). In C++/Java, also reduce after each multiplication to stay within 64 bits.
8. Assuming the CRT moduli are coprime. Check `(a₂ − a₁) mod gcd(m₁, m₂)` first (§10).
9. Trusting a Fermat test alone. Carmichael numbers fool it for every coprime base (§11).

Practice: greatest common divisor of strings; water and jug problem (Bézout); count primes below `n`; ugly number II; four divisors; closest prime numbers in a range; super pow; pow(x, n); count good numbers (fast power mod `10^9 + 7`); a system of remainders such as the classic "find the smallest number with given remainders" exercise; Project Euler problem 3 (largest prime factor).

Next: [Combinatorics](02-combinatorics.md).
