# Masks and Subsets — Sets as Integers, Submasks, Gray Codes, Bitsets

## 1. Sets as integers

A set drawn from items `0 … n − 1` fits in one integer: bit `i` is 1 when item `i` is in the set. That integer is a **bitmask**. Take `n = 4`, `A = {0, 2, 3}` and `B = {1, 2}`:

```text
item:   3 2 1 0
A   =   1 1 0 1    {0, 2, 3}  = 13
B   =   0 1 1 0    {1, 2}     =  6
```

Each set operation is one operator, because each item is one bit column and the operators work column by column ([Binary Numbers §3](01-binary-numbers.md#3-the-bitwise-operators)):

| Set operation | Mask code | Result | As a set |
|---|---|---|---|
| Union `A ∪ B` | `A \| B` | `1111` | `{0, 1, 2, 3}` |
| Intersection `A ∩ B` | `A & B` | `0100` | `{2}` |
| Difference `A − B` | `A & ~B` | `1001` | `{0, 3}` |
| Symmetric difference | `A ^ B` | `1011` | `{0, 1, 3}` |
| Complement of `A` (within `n` items) | `A ^ full` where `full = (1 << n) - 1` | `0010` | `{1}` |
| Is item `i` in `A`? | `(A >> i) & 1` | `i = 2` → 1 | yes |
| Size `\|A\|` | `A.bit_count()` | 3 | |
| Is `B ⊆ A`? | `(B & ~A) == 0`, or `(B & A) == B` | `0010 ≠ 0` | no |
| Empty set / full set | `0` / `(1 << n) - 1` | `0000` / `1111` | |

Every operation is O(1) on a machine word, against O(n) for Python `set` objects. Masks are plain integers, so they work as dictionary keys and list indices: `dp[mask]` is the state of bitmask DP in [Dynamic Programming](../09-dynamic-programming/README.md), and the loops in this chapter are its toolkit.

The subset test is the one people get wrong: `B ⊆ A` means "no item of `B` is missing from `A`", i.e. `B & ~A == 0`. Here `B & ~A = 0010` (item 1), so `B ⊄ A`.

## 2. Enumerating all subsets

**Problem.** List every subset of `items = [3, 5, 2]`, with its sum.

The subsets of `n` items are exactly the masks `0 … 2^n − 1`, so counting up visits each one once:

| `mask` | binary (item 2, 1, 0) | subset | sum |
|---:|---|---|---:|
| 0 | `000` | `{}` | 0 |
| 1 | `001` | `{3}` | 3 |
| 2 | `010` | `{5}` | 5 |
| 3 | `011` | `{3, 5}` | 8 |
| 4 | `100` | `{2}` | 2 |
| 5 | `101` | `{3, 2}` | 5 |
| 6 | `110` | `{5, 2}` | 7 |
| 7 | `111` | `{3, 5, 2}` | 10 |

**Every subset sum in O(2^n), not O(n · 2^n).** Decoding a mask costs O(n). Instead, a mask's sum is the sum of the mask without its lowest set bit, already computed, plus that one item. Row 6: `6 & 5 = 4`, so `sum[6] = sum[4] + items[1] = 2 + 5 = 7`.

$$
sum[mask] = sum[mask \mathbin{\&} (mask - 1)] + items[\text{index of lowbit}(mask)] .
$$

```python
import random
from itertools import combinations


def all_subsets(items: list) -> list[list]:
    n = len(items)
    return [[items[i] for i in range(n) if (mask >> i) & 1] for mask in range(1 << n)]


def subset_sums(items: list[int]) -> list[int]:
    """sums[mask] = sum of the items whose bits are set in mask."""
    sums = [0] * (1 << len(items))
    for mask in range(1, len(sums)):
        low = mask & -mask
        sums[mask] = sums[mask ^ low] + items[low.bit_length() - 1]
    return sums


def main():
    assert all_subsets([3, 5, 2])[5] == [3, 2]
    assert len(all_subsets([])) == 1                     # only the empty set
    assert subset_sums([3, 5, 2]) == [0, 3, 5, 8, 2, 5, 7, 10]
    rng = random.Random(20)
    for _ in range(100):
        items = [rng.randrange(-50, 50) for _ in range(rng.randrange(0, 10))]
        n = len(items)
        expected = sorted(tuple(c) for k in range(n + 1) for c in combinations(items, k))
        assert sorted(tuple(s) for s in all_subsets(items)) == expected
        sums = subset_sums(items)
        for mask in range(1 << n):
            assert sums[mask] == sum(items[i] for i in range(n) if mask >> i & 1)


if __name__ == "__main__":
    main()
```

`all_subsets` is O(n · 2^n); `subset_sums` is O(2^n) time and space. At `n = 20` that is about a million entries, which Python handles in well under a second; at `n = 30` it is a billion, which it does not.

## 3. All submasks of a mask

**Problem.** Given a mask, visit every **submask**: every mask whose 1 bits are a subset of its 1 bits. For `mask = 1011` the submasks are the 8 combinations of bits 0, 1 and 3.

**Brute force.** Loop over all `2^n` masks and keep those with `sub & mask == sub`. When this runs inside another loop over all masks, the total is `4^n`.

**The key observation.** Pretend the 0 bits of `mask` don't exist. Then the submasks are a plain binary counter on the remaining positions, and we want to count it **down**. Subtracting 1 from `sub` turns its lowest 1 into 0 and every bit below it into 1. Some of those new 1s fall on positions outside `mask`; `& mask` erases them. What is left is exactly "the compressed counter minus 1".

```text
sub = mask
loop:
    use sub
    if sub == 0: stop
    sub = (sub - 1) & mask
```

**Trace** for `mask = 1011`:

| Step | `sub` | `sub - 1` | `(sub - 1) & 1011` | compressed (bits 3,1,0) |
|---:|---|---|---|---|
| 1 | `1011` | `1010` | `1010` | `111` |
| 2 | `1010` | `1001` | `1001` | `110` |
| 3 | `1001` | `1000` | `1000` | `101` |
| 4 | `1000` | `0111` | `0011` | `100` |
| 5 | `0011` | `0010` | `0010` | `011` |
| 6 | `0010` | `0001` | `0001` | `010` |
| 7 | `0001` | `0000` | `0000` | `001` |
| 8 | `0000` | stop | | `000` |

Step 4 is the interesting one: `1000 − 1 = 0111` turns on bit 2, which is not in the mask, and `& 1011` removes it. The submasks come out in decreasing order, and the empty submask is last. A plain `while sub:` loop would skip it; that is the classic bug.

### Why all submasks of all masks cost 3^n, not 4^n

Bitmask DP often has the loop "for every mask, for every submask of it". Count the pairs `(mask, sub)` with `sub ⊆ mask`. For each of the `n` items, there are exactly three choices: not in `mask`; in `mask` but not in `sub`; in both. So the total is

$$
\sum_{mask} 2^{|mask|} = 3^n .
$$

For `n = 15`, `3^15 ≈ 1.4 \times 10^7`, versus `4^15 ≈ 10^9`.

```python
import random


def submasks(mask: int) -> list[int]:
    if mask < 0:
        raise ValueError("mask must be nonnegative")
    out = []
    sub = mask
    while True:
        out.append(sub)
        if sub == 0:
            break
        sub = (sub - 1) & mask
    return out


def submasks_brute(mask: int) -> list[int]:
    return [s for s in range(mask, -1, -1) if s & mask == s]


def count_all_pairs(n: int) -> int:
    return sum(len(submasks(mask)) for mask in range(1 << n))


def main():
    assert submasks(0b1011) == [0b1011, 0b1010, 0b1001, 0b1000, 0b0011, 0b0010, 0b0001, 0]
    assert submasks(0) == [0]
    for n in range(9):
        assert count_all_pairs(n) == 3 ** n
    rng = random.Random(21)
    for _ in range(300):
        mask = rng.randrange(0, 1 << 12)
        subs = submasks(mask)
        assert subs == submasks_brute(mask)
        assert len(subs) == 1 << mask.bit_count()


if __name__ == "__main__":
    main()
```

Listing the submasks of one mask costs O(2^popcount(mask)). The double loop over all masks costs O(3^n).

A related loop visits the **supermasks** of `mask` within `n` bits: `sup = (sup + 1) | mask` starting from `mask`, stopping after `full`.

## 4. Subsets of size k: Gosper's hack

**Problem.** Visit every `n`-bit mask with exactly `k` ones, in increasing order. For `n = 5, k = 3` there are `C(5, 3) = 10` of them.

**Brute force.** Loop over all `2^n` masks and keep those with `bit_count() == k`. Wasteful when `C(n, k)` is much smaller than `2^n`.

**The key observation.** The next larger number with the same popcount is found by:

1. Find the **rightmost block of consecutive 1s**. Its lowest bit is `c = x & -x`.
2. Add `c`: `r = x + c`. The carry turns the whole block to 0s and sets the 0 directly above it. `r` now has the right high part but has lost some 1s.
3. Put the lost 1s back at the very bottom (smallest possible). `r ^ x` marks the changed bits: the old block plus the new bit. Shifting right by 2 and dividing by `c` slides the right number of 1s to position 0.

$$
next = \left(\frac{(r \oplus x) \gg 2}{c}\right) \mathbin{|} r, \qquad c = x \mathbin{\&} {-x},\quad r = x + c .
$$

Trace one step, from `x = 00111`:

```text
x          = 00111
c = x & -x = 00001
r = x + c  = 01000     block 111 cleared, bit 3 set
r ^ x      = 01111     the old block plus the new bit: k + 1 = 4 ones, starting at c
>> 2       = 00011     drop two ones: k - 1 = 2 remain
// c       = 00011     dividing by c slides them down to bit 0 (c = 1 here, so no move)
| r        = 01011     the k - 1 low ones plus r's new bit: k = 3 ones in all
```

The full sequence for `n = 5, k = 3`:

```text
00111 → 01011 → 01101 → 01110 → 10011 → 10101 → 10110 → 11001 → 11010 → 11100
```

Start at `(1 << k) - 1` and stop once the mask reaches `1 << n`.

```python
import random
from itertools import combinations


def masks_of_size(n: int, k: int) -> list[int]:
    if not 0 <= k <= n:
        raise ValueError("need 0 <= k <= n")
    if k == 0:
        return [0]                          # Gosper's step needs at least one 1 bit
    out = []
    x = (1 << k) - 1
    while x < (1 << n):
        out.append(x)
        c = x & -x
        r = x + c
        x = (((r ^ x) >> 2) // c) | r
    return out


def masks_of_size_brute(n: int, k: int) -> list[int]:
    return sorted(sum(1 << i for i in combo) for combo in combinations(range(n), k))


def main():
    got = [format(m, "05b") for m in masks_of_size(5, 3)]
    assert got == ["00111", "01011", "01101", "01110", "10011",
                   "10101", "10110", "11001", "11010", "11100"]
    assert masks_of_size(4, 0) == [0] and masks_of_size(3, 3) == [7]
    for n in range(0, 13):
        for k in range(0, n + 1):
            assert masks_of_size(n, k) == masks_of_size_brute(n, k)
    rng = random.Random(22)
    n = 40
    k = rng.randrange(1, 4)
    assert len(masks_of_size(n, k)) == len(list(combinations(range(n), k)))


if __name__ == "__main__":
    main()
```

O(1) per mask, so O(C(n, k)) in total. The division by `c` is exact, because `(r ^ x) >> 2` is a block of 1s starting at least as high as `c`.

## 5. Gray codes

**Problem.** List all `2^n` masks so that **consecutive masks differ in exactly one bit**. For `n = 3` one answer is `000, 001, 011, 010, 110, 111, 101, 100`. This is a **Gray code**. It is used where a counter changes physically (rotary encoders), and in algorithms that walk all subsets while changing one item per step.

**The formula.** The `i`-th Gray code is

$$
g(i) = i \oplus (i \gg 1) .
$$

| `i` | `i` (binary) | `i >> 1` | `g(i)` | bit changed from previous |
|---:|---|---|---|---:|
| 0 | `000` | `000` | `000` | |
| 1 | `001` | `000` | `001` | 0 |
| 2 | `010` | `001` | `011` | 1 |
| 3 | `011` | `001` | `010` | 0 |
| 4 | `100` | `010` | `110` | 2 |
| 5 | `101` | `010` | `111` | 0 |
| 6 | `110` | `011` | `101` | 1 |
| 7 | `111` | `011` | `100` | 0 |

**Why consecutive codes differ by one bit.** Going from `i` to `i + 1` flips the trailing 1s of `i` and the 0 above them:

```text
i      = ... 0 1 1 1     (t = 3 trailing ones)
i + 1  = ... 1 0 0 0
d = i ^ (i+1) = 0 1 1 1 1     (t + 1 ones at the bottom)
```

Since `g` is built from XOR and shift, `g(i) ^ g(i+1) = d ^ (d >> 1) = 01111 ^ 00111 = 01000`: a single bit, at position `t`. So step `i → i + 1` flips bit `t`, the number of trailing 1s of `i`, which is the "bit changed" column in the table.

**The mirror picture.** The `n`-bit Gray code is the `(n−1)`-bit code, followed by the same list reversed with the top bit set:

```text
n = 2:   00 01 11 10
n = 3:   000 001 011 010 | 110 111 101 100
         (n=2 list, 0 on top) (n=2 list reversed, 1 on top)
```

The seam in the middle changes only the new top bit, and the reversed half is still one-bit steps. This is why it is also called the *reflected* binary code.

**Inverse.** To get `i` back from `g`, undo the XOR: `i = g ^ (g >> 1) ^ (g >> 2) ^ …`.

```python
import random


def gray(i: int) -> int:
    return i ^ (i >> 1)


def gray_inverse(g: int) -> int:
    i = 0
    while g:
        i ^= g
        g >>= 1
    return i


def gray_reflect(n: int) -> list[int]:
    codes = [0]
    for b in range(n):
        codes += [c | (1 << b) for c in reversed(codes)]
    return codes


def subset_sums_gray(items: list[int]) -> list[int]:
    """Visit every subset, adding or removing one item per step. Returns sums in Gray order."""
    n = len(items)
    total, prev, out = 0, 0, [0]
    for i in range(1, 1 << n):
        g = gray(i)
        changed = g ^ prev
        j = changed.bit_length() - 1
        total += items[j] if g & changed else -items[j]
        out.append(total)
        prev = g
    return out


def main():
    assert [format(gray(i), "03b") for i in range(8)] == \
        ["000", "001", "011", "010", "110", "111", "101", "100"]
    for n in range(11):
        codes = [gray(i) for i in range(1 << n)]
        assert codes == gray_reflect(n)
        assert sorted(codes) == list(range(1 << n))               # every mask once
        assert all((codes[i] ^ codes[i + 1]).bit_count() == 1 for i in range(len(codes) - 1))
        assert all(gray_inverse(codes[i]) == i for i in range(len(codes)))
    rng = random.Random(23)
    for _ in range(50):
        items = [rng.randrange(-20, 20) for _ in range(rng.randrange(0, 10))]
        sums = subset_sums_gray(items)
        for i, s in enumerate(sums):
            g = gray(i)
            assert s == sum(items[j] for j in range(len(items)) if g >> j & 1)


if __name__ == "__main__":
    main()
```

`gray` is O(1); `gray_inverse` is O(B) for `B`-bit codes. `subset_sums_gray` visits all `2^n` subsets with O(1) work per step and O(1) state, which is useful when you can't store a table of `2^n` sums.

## 6. Bitsets: a Python integer as a boolean array

**Problem.** Given positive integers `nums` and a `target`, can some subset sum to exactly `target`? For `[3, 5, 2]` and `target = 7`: yes, `5 + 2`.

**The list DP.** `reach[s]` is `True` when some subset of the items so far sums to `s`; start with `reach[0] = True`. Each item `a` makes `s + a` reachable for every reachable `s`, looping `s` downward so the item is used once (the 0/1 knapsack rule from [Dynamic Programming](../09-dynamic-programming/README.md)). That is O(n · S) Python-level steps for target `S`.

**The bitset idea.** Store all of `reach` in **one integer**: bit `s` is 1 when sum `s` is reachable. Then "every reachable `s` makes `s + a` reachable" is a single shift and OR:

$$
reach \leftarrow reach \mathbin{|} (reach \ll a) .
$$

Shifting moves every reachable sum up by `a` at once. Trace for `[3, 5, 2]` (bit positions 10 … 0):

```text
position:          10 9 8 7 6 5 4 3 2 1 0
start              0  0 0 0 0 0 0 0 0 0 1    {0}
item 3: reach<<3   0  0 0 0 0 0 0 1 0 0 0
        OR         0  0 0 0 0 0 0 1 0 0 1    {0, 3}
item 5: reach<<5   0  0 1 0 0 1 0 0 0 0 0
        OR         0  0 1 0 0 1 0 1 0 0 1    {0, 3, 5, 8}
item 2: reach<<2   1  0 0 1 0 1 0 0 1 0 0
        OR         1  0 1 1 0 1 0 1 1 0 1    {0, 2, 3, 5, 7, 8, 10}
```

Bit 7 is set, so the answer is yes.

**Why it is faster.** The shift and the OR run in C on 64-bit words: each item costs about `S / 64` word operations instead of `S` interpreted steps. The bound is still O(n · S) bit operations, but with `n = 150` and `S ≈ 11,000` the list DP takes about 0.07 s and the bitset about 0.0001 s, and the gap grows with `S`. To keep the integer from growing past the target, mask it: `reach &= (1 << (target + 1)) - 1`.

The same integer answers more questions: `reach.bit_count()` is the number of distinct reachable sums, and the highest set bit at most `total // 2` gives the best split for "partition into two subsets with minimum difference".

```python
import random


def can_sum_list(nums: list[int], target: int) -> bool:
    if target < 0 or any(a <= 0 for a in nums):
        raise ValueError("need positive items and a nonnegative target")
    reach = [False] * (target + 1)
    reach[0] = True
    for a in nums:
        for s in range(target, a - 1, -1):     # downward: each item used once
            if reach[s - a]:
                reach[s] = True
    return reach[target]


def can_sum_bitset(nums: list[int], target: int) -> bool:
    if target < 0 or any(a <= 0 for a in nums):
        raise ValueError("need positive items and a nonnegative target")
    limit = (1 << (target + 1)) - 1
    reach = 1                                   # bit 0: the empty subset
    for a in nums:
        reach = (reach | (reach << a)) & limit
    return (reach >> target) & 1 == 1


def reachable_sums(nums: list[int]) -> int:
    reach = 1
    for a in nums:
        reach |= reach << a
    return reach


def brute(nums: list[int], target: int) -> bool:
    n = len(nums)
    return any(sum(nums[i] for i in range(n) if m >> i & 1) == target for m in range(1 << n))


def main():
    assert can_sum_bitset([3, 5, 2], 7) and can_sum_list([3, 5, 2], 7)
    assert reachable_sums([3, 5, 2]) == 0b101_1010_1101
    assert not can_sum_bitset([3, 5, 2], 6)
    assert can_sum_bitset([], 0) and not can_sum_bitset([], 1)
    rng = random.Random(24)
    for _ in range(300):
        nums = [rng.randrange(1, 20) for _ in range(rng.randrange(0, 11))]
        target = rng.randrange(0, 80)
        expected = brute(nums, target)
        assert can_sum_list(nums, target) == can_sum_bitset(nums, target) == expected
    nums = [rng.randrange(1, 300) for _ in range(150)]
    assert can_sum_list(nums, sum(nums) // 2) == can_sum_bitset(nums, sum(nums) // 2)


if __name__ == "__main__":
    main()
```

List DP: O(n · S) time, O(S) list slots. Bitset: O(n · S / 64) word operations in C, O(S) bits.

## 7. Meet in the middle: subset sum closest to a target

**Problem.** Given up to `n = 40` integers (possibly negative) and a `goal`, choose a subset whose sum is as close to `goal` as possible, and return `|sum − goal|`. For `[5, −7, 3, 5]` and `goal = 6`, the subset `{5, −7, 3, 5}` sums to 6, so the answer is 0.

**Brute force.** `2^40 ≈ 10^{12}` subsets is far too many. The bitset does not help: values up to `10^7` make `S` huge, and negatives complicate it.

**The key observation.** Split the list into halves `L` and `R` of 20 items. Every subset of the whole list is a subset of `L` plus a subset of `R`, and each half has only `2^20 ≈ 10^6` subset sums (§2). Now pick one sum `x` from `L` and one `y` from `R` with `x + y` closest to `goal`: sort `R`'s sums, and for each `x` [binary search](../01-binary-search/02-boundaries.md) for the `y` nearest `goal − x`. `2^40` work becomes `2 · 2^20` sums, a sort and `2^20` searches: O(2^{n/2} · n).

**Trace** for `[5, −7, 3, 5]`, `goal = 6`:

```text
L = [5, -7]  sums: {} 0, {5} 5, {-7} -7, {5,-7} -2        -> [0, 5, -7, -2]
R = [3, 5]   sums: {} 0, {3} 3, {5} 5, {3,5} 8           -> sorted [0, 3, 5, 8]
```

| `x` from `L` | need `goal − x` | nearest `y` in `[0, 3, 5, 8]` | `x + y` | `\|x + y − 6\|` | best so far |
|---:|---:|---:|---:|---:|---:|
| 0 | 6 | 5 or 8 → 5 | 5 | 1 | 1 |
| 5 | 1 | 0 or 3 → 0 | 5 | 1 | 1 |
| −7 | 13 | 8 | 1 | 5 | 1 |
| −2 | 8 | 8 | 6 | 0 | 0 |

At each `x`, `bisect_left` finds the first `y ≥ goal − x`; the nearest is that `y` or the one right before it.

```python
import random
from bisect import bisect_left


def half_sums(items: list[int]) -> list[int]:
    sums = [0] * (1 << len(items))
    for mask in range(1, len(sums)):
        low = mask & -mask
        sums[mask] = sums[mask ^ low] + items[low.bit_length() - 1]
    return sums


def min_abs_difference(nums: list[int], goal: int) -> int:
    mid = len(nums) // 2
    left = half_sums(nums[:mid])
    right = sorted(half_sums(nums[mid:]))
    best = abs(goal)                            # the empty subset
    for x in left:
        need = goal - x
        j = bisect_left(right, need)
        if j < len(right):
            best = min(best, right[j] - need)
        if j > 0:
            best = min(best, need - right[j - 1])
        if best == 0:
            break
    return best


def brute(nums: list[int], goal: int) -> int:
    return min(abs(s - goal) for s in half_sums(nums))


def main():
    assert min_abs_difference([5, -7, 3, 5], 6) == 0
    assert min_abs_difference([7, -9, 15, -2], -5) == 1
    assert min_abs_difference([1, 2, 3], -7) == 7
    assert min_abs_difference([], 4) == 4
    rng = random.Random(25)
    for _ in range(300):
        nums = [rng.randrange(-100, 100) for _ in range(rng.randrange(0, 13))]
        goal = rng.randrange(-400, 400)
        assert min_abs_difference(nums, goal) == brute(nums, goal)


if __name__ == "__main__":
    main()
```

Time O(2^{n/2} · n) for the sort and the searches; space O(2^{n/2}). For `n = 40`, a second or two in Python instead of `10^{12}` steps.

**Why it is correct.** Every subset of the full list splits uniquely into a subset of `L` and a subset of `R`, so every candidate total `x + y` is considered. For a fixed `x`, the `y` closest to `goal − x` is one of the two neighbours of the insertion point in the sorted list.

**Variants.** Two sorted lists can also be scanned with two pointers instead of binary search (one ascending, one descending). "Count subsets with sum at most `T`" uses the same split with counting instead of nearest. Partition `2n` numbers into two groups of `n` with minimum difference uses the split with a sorted list **per subset size**.

## 8. Summary

| Task | Code | Cost |
|---|---|---:|
| Union, intersection, difference, symmetric difference | `A \| B`, `A & B`, `A & ~B`, `A ^ B` | O(1) |
| Complement within `n` items | `A ^ full`, `full = (1 << n) - 1` | O(1) |
| Subset test `B ⊆ A` | `(B & ~A) == 0` | O(1) |
| All subsets of `n` items | `for mask in range(1 << n)` | O(2^n) |
| Sum (or any additive value) of every subset | `s[m] = s[m & (m - 1)] + item[lowbit index]` | O(2^n) |
| Submasks of `mask`, including 0 | `sub = (sub - 1) & mask` until after 0 | O(2^popcount) |
| Submasks of every mask | the line above inside `for mask` | O(3^n) |
| Masks with exactly `k` ones, increasing | Gosper: `c = x & -x; r = x + c; x = (((r ^ x) >> 2) // c) \| r` | O(C(n, k)) |
| One-bit-change order of all masks | `g = i ^ (i >> 1)` | O(2^n) |
| Reachable subset sums up to `S` | `reach \|= reach << a` | O(n · S / 64) words |
| Subset choice with `n ≈ 40` | meet in the middle | O(2^{n/2} · n) |

How big can `n` be? In Python, "all subsets" is fine up to about 20, "all submasks of all masks" up to about 15, meet in the middle up to about 40, and a bitset handles sums into the millions.

## 9. Pitfalls and practice

1. **Precedence in subset tests.** In Python `sub & mask == sub` means `(sub & mask) == sub`, which is right. In C, Java and JavaScript it means `sub & (mask == sub)`. Parenthesize everywhere.
2. **Skipping the empty submask.** `while sub:` exits before visiting 0. Use the loop in §3, or handle 0 separately.
3. **Complement without a width.** `~A` in Python is negative (`−A − 1`). Within `n` items, write `A ^ full` or `full & ~A` with `full = (1 << n) - 1`.
4. **Gosper's hack with `k = 0`.** `x = 0` makes `c = 0` and the division fails. Special-case it.
5. **Bitset growth.** `reach << a` grows without limit in Python. Mask to `target + 1` bits when only small sums matter.
6. **Masks for large `n`.** Past the limits in §8, enumerating subsets is hopeless; look for DP over values instead.
7. **Fixed-width languages.** `1 << n` for `n ≥ 31` overflows a 32-bit `int`; use `1L << n` or `1ULL << n`.

Practice: subsets; subsets II (with duplicates: skip by sorted position); letter case permutation; Gray code; maximum product of word lengths (mask of letters per word); partition to K equal sum subsets (bitmask DP); smallest sufficient team; partition equal subset sum (bitset); last stone weight II (bitset); closest subsequence sum (meet in the middle); partition array into two arrays to minimize sum difference (meet in the middle by size); number of valid words for each puzzle (submask enumeration).

Back to the folder overview: [Bit Manipulation](README.md).
