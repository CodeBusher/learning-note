# Digit DP — Counting Numbers Under a Bound

## 1. Numbers up to N with digit sum S

Count the integers `x` with `0 <= x <= N` whose decimal digit sum equals `S`. For `N = 25`, `S = 4` the answer is 3: the numbers 4, 13 and 22.

**Brute force.** Loop over every `x` and add its digits: about `N · L` steps, where `L` is the number of digits of `N`. For `N = 10**18` that is hopeless, yet the answer takes a few thousand steps to compute.

**Key observation.** Counting 4, 13, 22 by hand, we fix the first digit and ask how many ways the rest can finish. Under tens digit 0 or 1, the ones digit may be anything from 0 to 9. Under tens digit 2, it may only go up to 5, because 26 … 29 exceed 25. **Digit DP** builds numbers one digit at a time, left to right, and merges all prefixes that behave the same from now on.

### 1.1 Fixed width and the tight flag

Write every number with as many digits as `N`, padding with zeros: 4 becomes `04`. Each integer in `[0, N]` is now exactly one digit string `<= "25"` of length 2. Padding does not change the digit sum, so here `04` and `4` behave the same (§2 shows properties where it matters).

```text
                         (start)
             ┌──────────────┼──────────────┐
tens:        0              1              2   <- equals N's first digit: still tight
             │              │              │
ones:      0..9           0..9           0..5  <- only 0..5 allowed under tight
          (free)         (free)        (tight)
```

A prefix is **tight** when it equals the bound's prefix of the same length; then the next digit is limited to `0 .. bound digit`. Choosing a digit *smaller* than the bound digit makes the number smaller than `N` whatever follows: the prefix is **free** forever after. Only the single tight path depends on `N`. For `N = 21` instead of 25, the tight branch allows ones digits 0..1, so 22 is lost and the answer is 2; the free branches are unchanged.

### 1.2 State and transition

To count completions we need the position, the digit sum still needed, and whether the prefix is tight. The exact digits so far do not matter: the free prefixes `13` and `40` of a four-digit bound, both with sum 4, have the same completions.

**State.** `count(pos, remaining, tight)` = the number of ways to fill positions `pos .. L-1` so that they add to `remaining`, limited by the bound's digits `d[pos]` only when `tight`.

$$
\text{count}(pos, rem, t) = \sum_{x=0}^{\text{lim}} \text{count}\big(pos+1,\ rem - x,\ t \wedge (x = d[pos])\big),
\qquad \text{lim} = \begin{cases} d[pos] & t \\ 9 & \text{otherwise} \end{cases}
$$

The prefix stays tight only if it was tight **and** we chose exactly the bound digit.

**Base.** At `pos = L`, return 1 if `remaining == 0`, else 0. Return 0 early when `remaining < 0` or `remaining > 9 · (L − pos)` (even all nines cannot reach it). **Answer:** `count(0, S, True)`: the empty prefix equals the bound's empty prefix, so we start tight.

**Trace** for `N = 25`, `S = 4`:

| Call | Allowed digits | Children | Value |
|---|---|---|---|
| `count(1, 4, False)` | 0..9 | only digit 4 reaches `count(2, 0, ·) = 1` | 1 |
| `count(1, 3, False)` | 0..9 | only digit 3 | 1 |
| `count(1, 2, True)` | 0..5 | only digit 2 | 1 |
| `count(0, 4, True)` | 0..2 | `count(1,4,F) + count(1,3,F) + count(1,2,T)` | **3** |

### 1.3 Variant: a range `[lo, hi]`

Count up to `hi` and subtract everything up to `lo − 1`:

$$
\#\{x \in [lo, hi] : P(x)\} = F(hi) - F(lo - 1), \qquad F(-1) = 0.
$$

`F` is a prefix count over the number line, as in [Prefix Sums](../04-range-queries/01-prefix-sums.md). In `[10, 25]` with digit sum 4: `F(25) − F(9) = 3 − 1 = 2` (13 and 22).

```python
import random
from functools import cache


def count_digit_sum_up_to(bound: int, target_sum: int) -> int:
    """Count x in [0, bound] whose decimal digit sum is target_sum."""
    if bound < 0 or target_sum < 0:
        return 0
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, remaining: int, tight: bool) -> int:
        if remaining < 0 or remaining > 9 * (length - pos):
            return 0
        if pos == length:
            return 1  # remaining is 0 here because of the check above
        limit = digits[pos] if tight else 9
        total = 0
        for x in range(min(limit, remaining) + 1):
            total += count(pos + 1, remaining - x, tight and x == digits[pos])
        return total

    return count(0, target_sum, True)


def count_digit_sum_range(lo: int, hi: int, target_sum: int) -> int:
    """Count x in [lo, hi] with digit sum target_sum (see §1.3)."""
    if lo < 0 or lo > hi:
        raise ValueError("require 0 <= lo <= hi")
    return count_digit_sum_up_to(hi, target_sum) - count_digit_sum_up_to(lo - 1, target_sum)


def brute(bound: int, target_sum: int, lo: int = 0) -> int:
    return sum(sum(map(int, str(x))) == target_sum for x in range(lo, bound + 1))


def main():
    assert count_digit_sum_up_to(25, 4) == 3
    assert count_digit_sum_up_to(21, 4) == 2
    assert count_digit_sum_up_to(0, 0) == 1
    assert count_digit_sum_up_to(0, 1) == 0
    assert count_digit_sum_up_to(999, 0) == 1
    assert count_digit_sum_up_to(99, 30) == 0
    assert count_digit_sum_up_to(-1, 0) == 0
    rng = random.Random(10)
    for _ in range(300):
        bound = rng.randrange(0, 3000)
        target = rng.randrange(0, 30)
        assert count_digit_sum_up_to(bound, target) == brute(bound, target)
    assert count_digit_sum_range(10, 25, 4) == 2
    for _ in range(300):
        lo = rng.randrange(0, 500)
        hi = rng.randrange(lo, 1500)
        target = rng.randrange(0, 25)
        assert count_digit_sum_range(lo, hi, target) == brute(hi, target, lo)
    try:
        count_digit_sum_range(5, 4, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    # Large bounds are instant: 10**18 has 19 digits.
    assert count_digit_sum_up_to(10**18, 1) == 19  # 1, 10, 100, ..., 10**18


if __name__ == "__main__":
    main()
```

**Complexity.** At most `L · (S + 1) · 2` states with 10 digits each: O(10·L·S) time, O(L·S) memory. Since `S > 9L` returns 0 at once, the worst case is O(L²): a few thousand steps for `N = 10**18`.

**Why it is correct.** Each integer in `[0, N]` is exactly one fixed-width string `<= N`. The recursion tries, at each position, every digit that keeps the string `<= N`; the tight flag is exactly "the string so far equals `N`'s prefix". Merging states only merges prefixes with identical futures.

**The cache belongs to one bound.** Tight states depend on `N`'s digits, so a global cache keyed by `(pos, remaining, tight)` would mix bounds. The cache above is created per call. Free states do not depend on `N` and may be shared between bounds of the same length, a common speed-up for many queries.

## 2. Leading zeros: no two equal adjacent digits

Count `x` in `[0, N]` with no two equal neighboring digits. For `N = 100` the answer is 91: all ten one-digit numbers and the 81 two-digit numbers other than 11, 22, …, 99 (100 has `00`).

The natural state adds the previous digit: `count(pos, prev, tight)`, skipping `x == prev`. **It is wrong.** With `N = 100` the width is 3, so 5 is built as `005`, and the padding `00` looks like a repeated digit. All ten one-digit numbers are rejected: 81 instead of 91. For `N = 99` only the integer 0 (built as `00`) is lost, an off-by-one that is easy to blame on something else, which is why tests need bounds of several lengths.

**The fix.** Padding zeros and real zeros must be told apart. Add `started`: false while only padding zeros are placed, true from the first nonzero digit. For each allowed digit `x`:

- not started and `x == 0`: another padding zero; stay not started;
- started and `x == prev`: forbidden;
- otherwise place `x`: `started = True`, `prev = x`.

At `pos == L` return 1. The all-padding path stands for the integer 0, which is valid. Every property needs this decision written down: what the all-padding path means, and whether 0 satisfies the property. Test `N = 0` separately.

**Trace** for `N = 100`:

| First digit | State after it | Completions |
|---|---|---|
| 0 (padding) | not started, free | second digit 0 (padding, then 10 choices) + second digit 1..9 (9 choices each) = 10 + 81 = 91 |
| 1 | started, `prev = 1`, tight | second digit limited to 0; third limited to 0 = `prev`: 0 ways |

```python
import random
from functools import cache


def count_no_adjacent_equal(bound: int) -> int:
    """Count x in [0, bound] with no two equal adjacent decimal digits."""
    if bound < 0:
        return 0
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, prev: int, started: bool, tight: bool) -> int:
        if pos == length:
            return 1  # includes the all-padding path, i.e. the integer 0
        limit = digits[pos] if tight else 9
        total = 0
        for x in range(limit + 1):
            next_tight = tight and x == digits[pos]
            if not started and x == 0:
                total += count(pos + 1, -1, False, next_tight)
            elif started and x == prev:
                continue
            else:
                total += count(pos + 1, x, True, next_tight)
        return total

    return count(0, -1, False, True)


def wrong_count_no_adjacent_equal(bound: int) -> int:
    """BUGGY: treats padding zeros as real digits."""
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, prev: int, tight: bool) -> int:
        if pos == length:
            return 1
        limit = digits[pos] if tight else 9
        total = 0
        for x in range(limit + 1):
            if x == prev:
                continue
            total += count(pos + 1, x, tight and x == digits[pos])
        return total

    return count(0, -1, True)  # -1 means "no previous digit"


def brute(bound: int) -> int:
    return sum(
        all(a != b for a, b in zip(str(x), str(x)[1:])) for x in range(bound + 1)
    )


def main():
    assert count_no_adjacent_equal(100) == 91
    assert count_no_adjacent_equal(0) == 1
    assert count_no_adjacent_equal(-1) == 0
    assert wrong_count_no_adjacent_equal(100) == 81  # padding 00 rejects all 10 one-digit numbers
    assert wrong_count_no_adjacent_equal(99) == brute(99) - 1  # only 0 (built as 00) is lost
    for bound in range(0, 2500):
        assert count_no_adjacent_equal(bound) == brute(bound), bound
    rng = random.Random(6)
    for _ in range(30):
        bound = rng.randrange(0, 60000)
        assert count_no_adjacent_equal(bound) == brute(bound)
    # Every 18-digit string with no equal neighbors: 9 * 9**17 of them, plus shorter ones.
    expected = 1 + sum(9 * 9 ** (k - 1) for k in range(1, 19))
    assert count_no_adjacent_equal(10**18 - 1) == expected


if __name__ == "__main__":
    main()
```

**Complexity.** `L · 11 · 2 · 2` states (`prev = -1` is the eleventh value), 10 digits each.

**Why it is correct.** `started` splits each fixed-width string into "padding, then the real number", and the adjacency rule applies only between two real digits, which is the rule on the usual decimal form.

## 3. Remainders: divisible by `m` with a digit-sum condition

Count `x` in `[0, N]` with digit sum exactly `S` **and** `x % m == 0`. For `N = 100`, `S = 9`, `m = 4`: of 9, 18, 27, 36, 45, 54, 63, 72, 81, 90, only 36 and 72 qualify. Answer 2.

The number itself (up to 18 digits) cannot be in the state, but divisibility only needs the remainder. Appending digit `x` to a prefix of value `v` gives `10v + x`, so

$$
r' = (10 r + x) \bmod m.
$$

Leading zeros are harmless: `(10·0 + 0) mod m = 0`.

**State.** `count(pos, remaining, r, tight)`; at `pos == L` return 1 when `remaining == 0` and `r == 0`.

$$
\text{count}(pos, rem, r, t) = \sum_{x=0}^{\text{lim}} \text{count}\big(pos+1,\ rem - x,\ (10r + x) \bmod m,\ t \wedge (x = d[pos])\big).
$$

**Application: numbers divisible by their own digit sum.** The divisor depends on the digit sum, which is not known in advance. Loop over every possible sum `s` from 1 to `9L` and run the DP with `S = s`, `m = s`. Each `x` is counted once, under its own digit sum.

```python
import random
from functools import cache


def count_sum_and_divisible(bound: int, target_sum: int, m: int) -> int:
    """Count x in [0, bound] with digit sum target_sum and x % m == 0."""
    if m <= 0:
        raise ValueError("m must be positive")
    if bound < 0 or target_sum < 0:
        return 0
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, remaining: int, r: int, tight: bool) -> int:
        if remaining < 0 or remaining > 9 * (length - pos):
            return 0
        if pos == length:
            return int(r == 0)
        limit = digits[pos] if tight else 9
        total = 0
        for x in range(min(limit, remaining) + 1):
            total += count(pos + 1, remaining - x, (10 * r + x) % m,
                           tight and x == digits[pos])
        return total

    return count(0, target_sum, 0, True)


def count_divisible_by_digit_sum(bound: int) -> int:
    """Count x in [1, bound] such that x % digit_sum(x) == 0."""
    if bound < 1:
        return 0
    length = len(str(bound))
    return sum(count_sum_and_divisible(bound, s, s) for s in range(1, 9 * length + 1))


def digit_sum(x: int) -> int:
    return sum(map(int, str(x)))


def main():
    assert count_sum_and_divisible(100, 9, 4) == 2  # 36 and 72
    rng = random.Random(7)
    for _ in range(200):
        bound = rng.randrange(0, 5000)
        s = rng.randrange(0, 30)
        m = rng.randrange(1, 15)
        expected = sum(digit_sum(x) == s and x % m == 0 for x in range(bound + 1))
        assert count_sum_and_divisible(bound, s, m) == expected
    for bound in [1, 9, 10, 12, 100, 999, 4321]:
        expected = sum(x % digit_sum(x) == 0 for x in range(1, bound + 1))
        assert count_divisible_by_digit_sum(bound) == expected
    assert count_divisible_by_digit_sum(12) == 11  # 1..10 and 12
    try:
        count_sum_and_divisible(10, 1, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

**Complexity.** One call: O(10·L·S·m). The self-divisor count repeats it for each `s <= 9L` with `m = s`: a few times 10^8 steps for `L = 18`, slow in Python, though the `remaining > 9 · (L − pos)` pruning removes many states.

**Variants.** Divisible by `m` alone: drop `remaining`. "Digit sum divisible by `k`": keep the digit sum modulo `k`. The pattern is the same: replace a large quantity with the small part the final check needs.

## 4. Sets of used digits: unique and repeated digits

Count `x` in `[0, N]` whose digits are all different. For `N = 100`: 10 + 81 = 91 (100 repeats 0). The related "at least one repeated digit in `[1, N]`" is the complement,

$$
\text{repeated}(N) = N - (\text{unique}(N) - 1),
$$

where `− 1` removes the integer 0. For `N = 100`: `100 − 90 = 10` (11, 22, …, 99, 100).

To decide whether the next digit is allowed, we must know **which** digits were used, so keep a 10-bit **mask** (bit `x` set when digit `x` is used; see [Bitmask DP](09-bitmask-dp.md)). State `count(pos, mask, started, tight)`. Padding zeros keep `mask = 0`; without `started`, `007` would put 0 in the mask twice and be rejected, the same bug as §2.

```python
import random
from functools import cache


def count_unique_digits(bound: int) -> int:
    """Count x in [0, bound] whose decimal digits are pairwise distinct."""
    if bound < 0:
        return 0
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, mask: int, started: bool, tight: bool) -> int:
        if pos == length:
            return 1
        limit = digits[pos] if tight else 9
        total = 0
        for x in range(limit + 1):
            next_tight = tight and x == digits[pos]
            if not started and x == 0:
                total += count(pos + 1, 0, False, next_tight)
            elif mask & (1 << x):
                continue
            else:
                total += count(pos + 1, mask | (1 << x), True, next_tight)
        return total

    return count(0, 0, False, True)


def count_repeated_digits(bound: int) -> int:
    """Count x in [1, bound] with at least one repeated decimal digit."""
    if bound < 1:
        return 0
    return bound - (count_unique_digits(bound) - 1)


def unique(x: int) -> bool:
    s = str(x)
    return len(set(s)) == len(s)


def main():
    assert count_unique_digits(100) == 91
    assert count_repeated_digits(100) == 10
    assert count_repeated_digits(20) == 1  # 11
    assert count_repeated_digits(1000) == 262
    assert count_unique_digits(0) == 1
    assert count_repeated_digits(0) == 0
    for bound in range(0, 3000):
        expected = sum(unique(x) for x in range(bound + 1))
        assert count_unique_digits(bound) == expected
    rng = random.Random(8)
    for _ in range(20):
        bound = rng.randrange(1, 200000)
        expected = sum(not unique(x) for x in range(1, bound + 1))
        assert count_repeated_digits(bound) == expected
    # Above 10 digits a repeat is forced, so the unique count stops growing.
    assert count_unique_digits(10**12) == count_unique_digits(9_876_543_210)


if __name__ == "__main__":
    main()
```

**Complexity.** At most `L · 1024 · 2 · 2` states, far fewer reachable (a mask at position `pos` has at most `pos` bits). A closed form with permutations `P(9, k)` also exists; the DP extends without new math to "unique digits **and** divisible by 7".

## 5. The k-th number with a property

Counting also **finds** things. The `k`-th smallest nonnegative integer with digit sum `S` (`k = 1` is the smallest): for `S = 4` the list is 4, 13, 22, 31, 40, 103, 112, …, so the 6th is 103. Walking up from 0 is hopeless for `k` near 10^12.

**Walking down the digit tree.** For a fixed width `L` with leading zeros, string order equals numeric order (`0103 < 0112 < 1003`), so look the answer up like a word in a dictionary:

1. Find the smallest width `L` whose number of matches reaches `k`.
2. At each position, try digits `0, 1, 2, …`. The number of matches starting with the current prefix plus digit `x` is the free count `ways(positions_left, sum_left − x)`.
3. If `k` exceeds it, all those strings come first: subtract it from `k` and try the next digit. Otherwise fix `x` and move on.

Each step skips a whole subtree. **Trace** (`S = 4`, `k = 6`): width 2 has 5 matches < 6, width 3 has 15, so `L = 3`.

| Position | Digit tried | Completions | `k` before → after |
|---|---|---|---|
| 0 | 0 | `ways(2, 4)` = 5 | 6 > 5, skip: `k = 1` |
| 0 | 1 | `ways(2, 3)` = 4 | 1 ≤ 4, take 1 |
| 1 | 0 | `ways(1, 3)` = 1 | take 0 |
| 2 | 0, 1, 2 | `ways(0, ·)` = 0 | skip, nothing subtracted |
| 2 | 3 | `ways(0, 0)` = 1 | take 3 |

Result `103`. The alternative is [binary search on the answer](../01-binary-search/03-search-on-the-answer.md): `F(x)` from §1 is nondecreasing, so the answer is the smallest `x` with `F(x) >= k`, at one full digit DP per probe. The script checks that both agree.

```python
import random
from functools import cache


@cache
def ways(positions: int, total: int) -> int:
    """Number of digit strings of the given length (leading zeros allowed) with this sum."""
    if total < 0 or total > 9 * positions:
        return 0
    if positions == 0:
        return 1
    return sum(ways(positions - 1, total - x) for x in range(10))


def kth_with_digit_sum(k: int, target_sum: int) -> int:
    """Return the k-th smallest nonnegative integer (k >= 1) with this digit sum."""
    if k < 1 or target_sum < 0:
        raise ValueError("require k >= 1 and target_sum >= 0")
    length = 1
    while ways(length, target_sum) < k:
        length += 1
    result = 0
    remaining = target_sum
    for pos in range(length):
        left = length - pos - 1
        for x in range(10):
            branch = ways(left, remaining - x)
            if k <= branch:
                result = result * 10 + x
                remaining -= x
                break
            k -= branch
    return result


def count_up_to(bound: int, target_sum: int) -> int:
    if bound < 0:
        return 0
    digits = [int(c) for c in str(bound)]
    length = len(digits)

    @cache
    def count(pos: int, remaining: int, tight: bool) -> int:
        if remaining < 0 or remaining > 9 * (length - pos):
            return 0
        if pos == length:
            return 1
        limit = digits[pos] if tight else 9
        return sum(count(pos + 1, remaining - x, tight and x == digits[pos])
                   for x in range(min(limit, remaining) + 1))

    return count(0, target_sum, True)


def kth_by_binary_search(k: int, target_sum: int) -> int:
    lo, hi = 0, 1
    while count_up_to(hi, target_sum) < k:
        hi *= 10
    while lo < hi:
        mid = (lo + hi) // 2
        if count_up_to(mid, target_sum) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def main():
    assert kth_with_digit_sum(6, 4) == 103
    assert kth_with_digit_sum(1, 0) == 0
    assert kth_with_digit_sum(1, 20) == 299
    for s in range(1, 20):
        matches = [x for x in range(30000) if sum(map(int, str(x))) == s]
        for k in range(1, min(len(matches), 200) + 1):
            assert kth_with_digit_sum(k, s) == matches[k - 1]
    rng = random.Random(9)
    for _ in range(40):
        s = rng.randrange(10, 60)
        k = rng.randrange(1, 10**9)
        assert kth_with_digit_sum(k, s) == kth_by_binary_search(k, s)
    try:
        kth_with_digit_sum(0, 3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

**Complexity.** `ways` has O(L · 9L) entries; the walk does at most `10L` lookups. O(L²) per query after caching, versus O(L² · log answer) for binary search.

**Variant.** For the `k`-th number inside `[0, N]`, use the tight count: at each position, compute branch counts with the tight flag that branch would have. With `started`, the branch "digit 0 while not started" is the padding branch.

## 6. Long bounds without recursion

A bound given as a 5,000-digit string exceeds Python's recursion limit, and the counts become astronomically large, so such problems ask for the answer modulo a prime like `10**9 + 7`. Rewrite the digit-sum DP as a forward table. At each length, the prefixes that do not exceed the bound's prefix split into **exactly one** tight prefix and the strictly smaller ones. A strictly smaller prefix stays smaller whatever follows, so the smaller ones can be grouped by digit sum alone:

- `free[s]` = how many strictly smaller prefixes have digit sum `s`;
- `tight_sum` = the digit sum of the bound's own prefix.

At bound digit `b`: every free prefix takes any digit (`new_free[s + x] += free[s]`); the tight prefix becomes free with `x < b` (`new_free[tight_sum + x] += 1`); `x = b` keeps it tight (`tight_sum += b`). Sums above `S` never come back down and are dropped. **Answer:** `free[S]`, plus 1 if `tight_sum == S` (the bound itself).

**Trace** for `"25"`, `S = 4`:

| After digit | `free` (nonzero entries) | `tight_sum` |
|---|---|---|
| `2` | `free[0] = 1` (prefix 0), `free[1] = 1` (prefix 1) | 2 |
| `5` | from 0: sums 0..4; from 1: sums 1..4; from tight 2 with `x < 5`: sums 2..4; so `free[4] = 3` | 7 |

Answer `free[4] + (7 == 4) = 3`.

```python
import random


MOD = 10**9 + 7


def count_digit_sum_str(bound: str, target_sum: int, mod: int = MOD) -> int:
    """Count x in [0, int(bound)] with digit sum target_sum, modulo mod. No recursion."""
    if not bound or not bound.isdigit():
        raise ValueError("bound must be a nonempty string of decimal digits")
    if target_sum < 0:
        return 0
    free = [0] * (target_sum + 1)
    tight_sum = 0
    for ch in bound:
        b = ord(ch) - ord("0")
        new_free = [0] * (target_sum + 1)
        for s, ways in enumerate(free):
            if ways:
                for x in range(min(9, target_sum - s) + 1):
                    new_free[s + x] = (new_free[s + x] + ways) % mod
        for x in range(b):
            if tight_sum + x <= target_sum:
                new_free[tight_sum + x] = (new_free[tight_sum + x] + 1) % mod
        free = new_free
        tight_sum += b
    return (free[target_sum] + (tight_sum == target_sum)) % mod


def brute(bound: int, target_sum: int) -> int:
    return sum(sum(map(int, str(x))) == target_sum for x in range(bound + 1))


def main():
    assert count_digit_sum_str("25", 4) == 3
    assert count_digit_sum_str("0", 0) == 1
    assert count_digit_sum_str("007", 7) == 1  # leading zeros in the input are fine
    rng = random.Random(11)
    for _ in range(300):
        bound = rng.randrange(0, 4000)
        s = rng.randrange(0, 30)
        assert count_digit_sum_str(str(bound), s, mod=10**30) == brute(bound, s)
    long_bound = "".join(rng.choice("0123456789") for _ in range(5000))
    answer = count_digit_sum_str(long_bound, 300)
    assert 0 <= answer < MOD
    for bad in ["", "12a", "-5"]:
        try:
            count_digit_sum_str(bad, 1)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

O(10·L·S) time, O(S) memory, no recursion: 1.5·10^7 steps for 5,000 digits and `S = 300`. The same two-part table works for any digit DP: replace "digit sum" with the summary the property needs, and keep `started` inside the summary when leading zeros matter.

## 7. Summary: what goes in the state

Every digit DP is `(pos, summary, tight)`, plus `started` when padding zeros could be mistaken for real ones. The summary is the smallest thing the final check needs:

| Property | Summary | Needs `started`? |
|---|---|---|
| Digit sum equals `S` | remaining sum | no: zeros add nothing |
| No two equal adjacent digits | previous digit | yes: padding `00` is not a repeat |
| Contains digit 0 | seen flag | yes: padding zeros are not real zeros |
| Divisible by `m` | remainder mod `m` | no: `(10·0 + 0) mod m = 0` |
| Exactly `k` nonzero digits | count so far | no |
| All digits distinct | mask of used digits | yes |
| Contains a pattern such as `"13"` | pattern-matching state | often: decide whether matching starts before the first real digit |

Ranges are `F(hi) − F(lo − 1)`; the k-th match is a walk that subtracts branch counts; long string bounds use the free/tight table.

## 8. Pitfalls and practice

1. **Forgetting the tight flag.** The DP then counts everything up to `10**L − 1`, not up to `N`.
2. **Never releasing tight.** Write `tight and x == digits[pos]`, not `tight`.
3. **Sharing a cache across bounds.** Create it per bound, or share only free states.
4. **Padding zeros treated as real digits.** Add `started`, and test bounds of several lengths: the bug in §2 loses only the integer 0 when `N < 100`.
5. **Zero's interpretation.** Decide whether the all-padding path is 0 and whether 0 qualifies; problems over `[1, N]` must subtract it.
6. **Off-by-one in ranges.** `F(hi) − F(lo − 1)` with `F(-1) = 0`.
7. **Storing the number instead of a summary.** Keep a remainder, a capped sum, a mask or a pattern state.
8. **Deep recursion and huge counts.** For string bounds, use the iterative table and reduce modulo the prime.
9. **k-th searches.** Try digits in increasing order, subtract whole branch counts, and fix the width first so string order equals numeric order.

Practice: Count Numbers with Unique Digits, Numbers With Repeated Digits, Number of Digit One, Numbers At Most N Given Digit Set, Non-negative Integers without Consecutive Ones, Count of Integers (digit sum in a range), Rotated Digits, Count Special Integers, Digit Count in Range, Find All Good Strings (digit DP with a pattern automaton).

Next: [Games and Probability](11-games-and-probability.md).
