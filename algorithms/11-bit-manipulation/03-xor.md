# XOR — Cancelling Pairs, Prefix XOR, Tries, and Linear Bases

## 1. The number without a partner

**Problem.** Every value in a list appears exactly twice, except one value that appears once. Find it. For `[4, 1, 2, 1, 2]` the answer is `4`.

**Brute force.** A dictionary of counts takes O(n) extra space; sorting and scanning neighbours takes O(n log n) time. We want O(n) time *and* O(1) space.

**The key observation: pairs cancel.** XOR every number together, and look at one bit column at a time:

```text
          bit:  2 1 0
  4   =         1 0 0
  1   =         0 0 1
  2   =         0 1 0
  1   =         0 0 1
  2   =         0 1 0
  count of 1s:  1 2 2
  XOR (parity): 1 0 0   = 4
```

XOR of a column is the **parity** of its count of 1s: 1 if odd, 0 if even. A value that appears twice adds an even count to every column, so it vanishes; only the lonely value is left. The code is one loop, `acc = 0; for x in nums: acc ^= x`, tested with §3's code below.

In algebra, XOR (written `⊕` in formulas) has four rules: `a ^ 0 = a` (identity), `a ^ a = 0` (self-inverse), and order and grouping don't matter (commutative, associative). So `4 ⊕ 1 ⊕ 2 ⊕ 1 ⊕ 2 = 4 ⊕ (1 ⊕ 1) ⊕ (2 ⊕ 2) = 4`.

One consequence is used in every section below, the **undo rule**: if `a ^ b = c`, then `a = c ^ b`. XOR both sides with `b` and the two `b`s cancel.

Negative numbers need no masking: in Python's infinite two's complement ([Binary Numbers §6](01-binary-numbers.md#6-pythons-integers-have-no-fixed-width)) the infinite sign columns cancel in pairs too.

## 2. Single number II: every other value appears three times

**Problem.** Every value appears exactly **three** times except one, which appears once. For `[2, 2, 3, 2]` the answer is `3`. XOR fails: three copies leave one behind.

### Method 1: count each bit column mod 3

Redo §1's column picture: in each column the tripled values contribute a multiple of 3 ones, so `count mod 3` is the lonely value's bit. For `[2, 2, 3, 2]` = `10, 10, 11, 10`, bit 1 has 4 ones and bit 0 has 1; mod 3 that is `1 1` = 3.

For 32-bit inputs, count all 32 columns, rebuild the pattern, and convert back to signed (bit 31 set means negative). O(32 · n) time, O(1) space, and it generalizes to "every value appears `k` times" with `count % k`.

### Method 2: a two-variable state machine

Each column only needs its count mod 3, which fits in two bits. Keep two integers, `ones` and `twos`; in each column, `(twos, ones)` is the count:

```text
   count 0        count 1        count 2
     0 0  --1-->    0 1  --1-->    1 0  --1--> back to 0 0
```

A 0 bit of `x` leaves its column alone. Two lines update every column at once:

```text
ones = (ones ^ x) & ~twos     # flip "ones" on a 1 bit, unless the count was already 2
twos = (twos ^ x) & ~ones     # flip "twos" on a 1 bit, unless "ones" became 1 on this step
```

Check one column: from `(0,0)` a 1 bit gives `ones = 1`, `twos = 1 & ~1 = 0` → `(0,1)`. From `(0,1)`: `ones = 0`, `twos = 1` → `(1,0)`. From `(1,0)`: `ones = 1 & ~1 = 0`, `twos = 0` → `(0,0)`.

Trace on `[2, 2, 3, 2]`:

| Step | `x` | `ones` | `twos` | column 1 count | column 0 count |
|---:|---|---|---|---:|---:|
| 1 | `10` | `10` | `00` | 1 | 0 |
| 2 | `10` | `00` | `10` | 2 | 0 |
| 3 | `11` | `01` | `00` | 3 ≡ 0 | 1 |
| 4 | `10` | `11` | `00` | 1 | 1 |

Every column ends at count 0 or 1, so `ones` is the answer, `3`. The update is purely bitwise, so negatives need no masking.

```python
import random
from collections import Counter


def single_number_ii_count(nums: list[int]) -> int:
    """Count each of 32 bit columns mod 3 (inputs are 32-bit signed)."""
    result = 0
    for i in range(32):
        count = sum((x >> i) & 1 for x in nums)
        if count % 3:
            result |= 1 << i
    return result - (1 << 32) if result >> 31 else result


def single_number_ii(nums: list[int]) -> int:
    ones = twos = 0
    for x in nums:
        ones = (ones ^ x) & ~twos
        twos = (twos ^ x) & ~ones
    return ones


def brute(nums: list[int]) -> int:
    return next(v for v, c in Counter(nums).items() if c == 1)


def main():
    assert single_number_ii([2, 2, 3, 2]) == single_number_ii_count([2, 2, 3, 2]) == 3
    assert single_number_ii([0, 1, 0, 1, 0, 1, 99]) == 99
    assert single_number_ii([-2, -2, 1, 1, -3, 1, -2]) == -3
    assert single_number_ii_count([-2, -2, 1, 1, -3, 1, -2]) == -3
    rng = random.Random(11)
    for _ in range(500):
        values = rng.sample(range(-(1 << 31), 1 << 31), rng.randrange(1, 12))
        nums = values + values[1:] * 2
        rng.shuffle(nums)
        assert single_number_ii(nums) == single_number_ii_count(nums) == brute(nums) == values[0]


if __name__ == "__main__":
    main()
```

Both are O(n) time and O(1) space.

## 3. Single number III: two lonely values

**Problem.** Every value appears twice except **two** values `a` and `b`, which appear once. Return both. For `[1, 2, 1, 3, 2, 5]` the answer is `{3, 5}`.

XOR of everything gives `a ^ b`, not the two values. **The key observation:** `a ≠ b`, so `a ^ b` has a 1 bit, and any 1 bit of `a ^ b` is a position where `a` and `b` differ. Take the lowest, `d = (a ^ b) & -(a ^ b)` ([lowbit](02-everyday-tricks.md#2-the-lowest-set-bit-x---x)), and split the list by that bit. `a` and `b` land in different groups; both copies of a paired value land in the same group. Each group is now §1's problem:

```text
XOR of all      = 1^2^1^3^2^5 = 3^5 = 011 ^ 101 = 110   (6)
d = 6 & -6      = 010                                    (bit 1)

bit 1 set:   2 (010), 3 (011), 2 (010)   ->  2^3^2 = 3
bit 1 clear: 1 (001), 1 (001), 5 (101)   ->  1^1^5 = 5
```

Only one group needs a pass: once `a` is known, `b = (a ^ b) ^ a` by the undo rule.

```python
import random
from collections import Counter


def single_number(nums: list[int]) -> int:
    if not nums:
        raise ValueError("nums must be nonempty")
    acc = 0
    for x in nums:
        acc ^= x
    return acc


def single_number_iii(nums: list[int]) -> tuple[int, int]:
    both = 0
    for x in nums:
        both ^= x
    if both == 0:
        raise ValueError("need exactly two values that appear once")
    d = both & -both
    a = 0
    for x in nums:
        if x & d:
            a ^= x
    b = both ^ a                # undo: a ^ b ^ a = b
    return (a, b) if a < b else (b, a)


def once(nums: list[int]) -> list[int]:
    return sorted(v for v, c in Counter(nums).items() if c == 1)


def main():
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([7]) == 7 and single_number([-3, 5, 5]) == -3
    assert single_number_iii([1, 2, 1, 3, 2, 5]) == (3, 5)
    assert single_number_iii([-1, 0]) == (-1, 0)
    rng = random.Random(12)
    for _ in range(500):
        values = rng.sample(range(-500, 500), rng.randrange(2, 15))
        nums = values + values[1:]                     # values[0] appears once
        rng.shuffle(nums)
        assert [single_number(nums)] == once(nums)
        nums = values + values[2:]                     # values[0], values[1] once
        rng.shuffle(nums)
        assert list(single_number_iii(nums)) == once(nums)


if __name__ == "__main__":
    main()
```

Both are O(n) time, O(1) space.

## 4. Missing and duplicated numbers

**Missing number.** A list holds `n` distinct numbers from `0..n`; one is missing. For `[3, 0, 1]` the answer is `2`. XOR all indices `0..n` with all values: each present number appears twice and cancels, the missing one appears once:

```text
(0 ^ 1 ^ 2 ^ 3) ^ (3 ^ 0 ^ 1) = (0^0) ^ (1^1) ^ (3^3) ^ 2 = 2
```

The sum formula `n(n+1)/2 − sum(nums)` also works, but can overflow in fixed-width languages; XOR cannot.

**Duplicate and missing.** A list should hold `1..n`, but one value `dup` appears twice and `miss` is absent. For `[1, 2, 2, 4]`: `dup = 2`, `miss = 3`. XOR all values with `1..n`: correct numbers cancel, `dup` appears three times (one copy left) and `miss` once, so the result is `dup ^ miss`. §3's split separates them:

```text
(1^2^2^4) ^ (1^2^3^4) = 2 ^ 3 = 001     -> d = bit 0

bit 0 set:   values 1        and numbers 1, 3   ->  1^1^3     = 3
bit 0 clear: values 2, 2, 4  and numbers 2, 4   ->  2^2^4^2^4 = 2
```

The split gives `{2, 3}` but not which is which. One more pass decides it: the candidate that occurs in the list is `dup`.

```python
import random


def missing_number(nums: list[int]) -> int:
    acc = len(nums)                     # the index n has no slot in range(len)
    for i, x in enumerate(nums):
        acc ^= i ^ x
    return acc


def find_error_nums(nums: list[int]) -> tuple[int, int]:
    """Return (dup, miss) for a list meant to hold 1..n."""
    both = 0
    for i, x in enumerate(nums, 1):
        both ^= i ^ x
    if both == 0:
        raise ValueError("no duplicate found")
    d = both & -both
    x1 = 0
    for i, x in enumerate(nums, 1):
        if i & d:
            x1 ^= i
        if x & d:
            x1 ^= x
    x2 = both ^ x1
    return (x1, x2) if x1 in nums else (x2, x1)


def main():
    assert missing_number([3, 0, 1]) == 2
    assert missing_number([0]) == 1 and missing_number([]) == 0
    assert find_error_nums([1, 2, 2, 4]) == (2, 3)
    assert find_error_nums([1, 1]) == (1, 2)
    rng = random.Random(13)
    for _ in range(500):
        n = rng.randrange(1, 40)
        miss = rng.randrange(0, n + 1)
        nums = [v for v in range(n + 1) if v != miss]
        rng.shuffle(nums)
        assert missing_number(nums) == miss
    for _ in range(500):
        n = rng.randrange(2, 40)
        dup, miss = rng.sample(range(1, n + 1), 2)
        nums = [dup if v == miss else v for v in range(1, n + 1)]
        rng.shuffle(nums)
        assert find_error_nums(nums) == (dup, miss)


if __name__ == "__main__":
    main()
```

O(n) time and O(1) extra space each.

## 5. XOR of a range in O(1)

**Problem.** Compute `f(n) = 0 ^ 1 ^ 2 ^ … ^ n` without a loop.

| `n` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `f(n)` | 0 | 1 | 3 | 0 | 4 | 1 | 7 | 0 | 8 | 1 | 11 | 0 |

The pattern repeats every 4: `f(n)` is `n`, `1`, `n + 1`, `0` for `n % 4 = 0, 1, 2, 3`.

**Why.** In a block `4k, 4k+1, 4k+2, 4k+3`, the bits above bit 1 are the same four times and cancel, and the low two bits `00, 01, 10, 11` XOR to `00`. So every complete block is 0, and `f(n)` is the XOR of what follows the last complete block: `4k` → `n`; `4k ^ (4k+1)` → `1`; `1 ^ (4k+2)` → `4k+3 = n + 1`; a complete block → `0`.

**Any range.** By the undo rule, `l ^ … ^ r = f(r) ^ f(l − 1)`: the numbers below `l` appear in both and cancel. With `f(−1) = 0` it works for `l = 0`.

```python
import random
from functools import reduce
from operator import xor


def xor_upto(n: int) -> int:
    """0 ^ 1 ^ ... ^ n; f(-1) = 0 (the empty XOR)."""
    if n < -1:
        raise ValueError("n must be at least -1")
    if n == -1:
        return 0
    return [n, 1, n + 1, 0][n % 4]


def xor_range(l: int, r: int) -> int:
    if not 0 <= l <= r + 1:
        raise ValueError("need 0 <= l <= r + 1")
    return xor_upto(r) ^ xor_upto(l - 1)


def main():
    assert [xor_upto(n) for n in range(12)] == [0, 1, 3, 0, 4, 1, 7, 0, 8, 1, 11, 0]
    assert xor_range(5, 4) == 0                       # empty range
    rng = random.Random(14)
    for _ in range(2000):
        l = rng.randrange(0, 300)
        r = rng.randrange(l - 1, 400)
        assert xor_range(l, r) == reduce(xor, range(l, r + 1), 0)
    assert xor_upto(10**18) == 10**18                 # 10**18 % 4 == 0


if __name__ == "__main__":
    main()
```

O(1) time and space.

## 6. Prefix XOR: subarray queries

XOR is its own inverse, so it behaves like addition with a built-in subtraction, and the [prefix-sum](../04-range-queries/01-prefix-sums.md) idea carries over. `P[i]` is the XOR of the prefix `a[:i]`, with `P[0] = 0`. The XOR of the half-open slice `a[l:r]` is `P[r] ^ P[l]`, because the shared prefix `a[:l]` appears in both and cancels.

For `a = [4, 2, 2, 6, 4]`, `P = [0, 4, 6, 4, 2, 6]`. Query `a[1:4] = [2, 2, 6]`: `P[4] ^ P[1] = 2 ^ 4 = 6`, and indeed `2 ^ 2 ^ 6 = 6`.

### Counting subarrays with XOR equal to `k`

**Problem.** Count the slices `a[l:r]` whose XOR is `k`, i.e. pairs `l < r` with `P[r] ^ P[l] == k`. By the undo rule this is `P[l] == P[r] ^ k`. Sweep `r` left to right with a dictionary counting the prefix values seen so far, and at each `r` add the count of `P[r] ^ k`: the same pattern as "count subarrays with sum `k`".

Trace for the same `a`, `k = 6`:

| `r` | `P[r]` | look up `P[r] ^ 6` | found | total | seen after |
|---:|---:|---:|---:|---:|---|
| 0 | 0 | 6 | 0 | 0 | `{0:1}` |
| 1 | 4 | 2 | 0 | 0 | `{0:1, 4:1}` |
| 2 | 6 | 0 | 1 | 1 | `{0:1, 4:1, 6:1}` |
| 3 | 4 | 2 | 0 | 1 | `{0:1, 4:2, 6:1}` |
| 4 | 2 | 4 | 2 | 3 | `{0:1, 4:2, 6:1, 2:1}` |
| 5 | 6 | 0 | 1 | 4 | `{0:1, 4:2, 6:2, 2:1}` |

The four slices are `a[0:2]`, `a[1:4]`, `a[3:4]` and `a[0:5]`. Seeding the dictionary with `{0: 1}` is what counts the slices that start at index 0.

```python
import random
from collections import defaultdict


def prefix_xor(a: list[int]) -> list[int]:
    p = [0] * (len(a) + 1)
    for i, x in enumerate(a):
        p[i + 1] = p[i] ^ x
    return p


def range_xor(p: list[int], l: int, r: int) -> int:
    """XOR of a[l:r] (half-open)."""
    if not 0 <= l <= r < len(p):
        raise ValueError("need 0 <= l <= r <= len(a)")
    return p[r] ^ p[l]


def count_subarrays_xor(a: list[int], k: int) -> int:
    seen = defaultdict(int)
    seen[0] = 1
    cur = total = 0
    for x in a:
        cur ^= x
        total += seen[cur ^ k]
        seen[cur] += 1
    return total


def count_brute(a: list[int], k: int) -> int:
    total = 0
    for l in range(len(a)):
        acc = 0
        for r in range(l, len(a)):
            acc ^= a[r]
            total += acc == k
    return total


def main():
    p = prefix_xor([4, 2, 2, 6, 4])
    assert p == [0, 4, 6, 4, 2, 6]
    assert range_xor(p, 1, 4) == 6 and range_xor(p, 2, 2) == 0
    assert count_subarrays_xor([4, 2, 2, 6, 4], 6) == 4
    assert count_subarrays_xor([], 0) == 0
    rng = random.Random(15)
    for _ in range(500):
        a = [rng.randrange(0, 16) for _ in range(rng.randrange(0, 25))]
        p = prefix_xor(a)
        l = rng.randrange(0, len(a) + 1)
        r = rng.randrange(l, len(a) + 1)
        acc = 0
        for x in a[l:r]:
            acc ^= x
        assert range_xor(p, l, r) == acc
        k = rng.randrange(0, 16)
        assert count_subarrays_xor(a, k) == count_brute(a, k)


if __name__ == "__main__":
    main()
```

Building `P` is O(n); each range query is O(1). Counting is O(n) expected time and O(n) space for the dictionary.

## 7. Maximum XOR of two numbers

**Problem.** Given a list of nonnegative integers, find the largest `a ^ b` over all pairs. For `[3, 10, 5, 8]` the answer is `5 ^ 10 = 15`.

All pairs cost O(n²), too slow for `n = 10^5`.

**The key observation: greedy from the highest bit.** A 1 in bit `b` is worth more than all lower bits together (`2^b > 2^b − 1`). So the answer takes a 1 in the highest bit if *any* pair allows it, then a 1 in the next bit if any pair *that keeps the first choice* allows it, and so on. No better answer is ever thrown away: any answer with a 0 where we chose 1, and the same higher bits, is smaller. We need a structure that answers "is there a number whose bit here is the opposite of mine, among those matching my choices so far?"

### Method 1: a binary trie

A **binary trie** is a [trie](../03-trees/05-tries.md) whose alphabet is `{0, 1}`: each number is a path from the root, one level per bit, highest bit first, every number padded to the same width. Going left means bit 0, right means bit 1. For `[3, 10, 5, 8]` in 4 bits (`0011`, `1010`, `0101`, `1000`):

```text
                     root
               0 /          \ 1            bit 3
                •             •
             0 / \ 1        0 |            bit 2
              •   •           •
            1 |   | 0       0 / \ 1        bit 1
              •   •          •   •
            1 |   | 1      0 |   | 0       bit 0
              3   5          8   10
```

To find the best partner for `x`, walk down from the root. At each bit, prefer the child with the **opposite** bit (that makes the XOR bit 1); if it is missing, take the same bit (XOR bit 0). Query `x = 5 = 0101`:

| Bit | `x`'s bit | want | available? | go | XOR bit | partial answer |
|---:|---:|---:|---|---:|---:|---|
| 3 | 0 | 1 | yes | 1 | 1 | `1` |
| 2 | 1 | 0 | yes | 0 | 1 | `11` |
| 1 | 0 | 1 | yes (10) | 1 | 1 | `111` |
| 0 | 1 | 0 | yes | 0 | 1 | `1111` = 15 |

Insert numbers one by one and query each before inserting it; the best over all queries is the answer.

### Method 2: the greedy prefix-set method

The same greedy, without a trie. Decide the answer one bit at a time from the top. Suppose the bits above `b` are fixed as `ans`. Try `candidate = ans | (1 << b)`. Take the set of every number's **prefix** (its bits from the top down to `b`, the rest zeroed). A pair reaches `candidate` exactly when two prefixes XOR to it, i.e. when `p ^ candidate` is also in the set (undo rule again).

Trace for `[3, 10, 5, 8]`:

| Bit | prefixes (bits ≥ b) | candidate | `p` with `p ^ candidate` in set | `ans` |
|---:|---|---|---|---|
| 3 | `{0000, 1000}` | `1000` | `0000 ^ 1000 = 1000` ✓ | `1000` |
| 2 | `{0000, 1000, 0100}` | `1100` | `1000 ^ 1100 = 0100` ✓ | `1100` |
| 1 | `{0010, 1010, 0100, 1000}` | `1110` | `1010 ^ 1110 = 0100` ✓ | `1110` |
| 0 | `{0011, 1010, 0101, 1000}` | `1111` | `1010 ^ 1111 = 0101` ✓ | `1111` |

```python
import random


class XorTrie:
    def __init__(self, bits: int):
        if bits <= 0:
            raise ValueError("bits must be positive")
        self.bits = bits
        self.children = [[-1, -1]]          # node 0 is the root

    def insert(self, x: int) -> None:
        if not 0 <= x < (1 << self.bits):
            raise ValueError("x out of range")
        node = 0
        for b in range(self.bits - 1, -1, -1):
            bit = (x >> b) & 1
            if self.children[node][bit] == -1:
                self.children[node][bit] = len(self.children)
                self.children.append([-1, -1])
            node = self.children[node][bit]

    def best_xor(self, x: int) -> int:
        """Largest x ^ y over inserted y (the trie must be nonempty)."""
        node, result = 0, 0
        for b in range(self.bits - 1, -1, -1):
            bit = (x >> b) & 1
            want = bit ^ 1
            if self.children[node][want] != -1:
                result |= 1 << b
                node = self.children[node][want]
            else:
                node = self.children[node][bit]
        return result


def max_xor_trie(nums: list[int]) -> int:
    if not nums:
        raise ValueError("nums must be nonempty")
    trie = XorTrie(max(max(nums).bit_length(), 1))
    best = 0
    for x in nums:
        trie.insert(x)                       # insert first so a single number gives x ^ x = 0
        best = max(best, trie.best_xor(x))
    return best


def max_xor_prefix(nums: list[int]) -> int:
    if not nums:
        raise ValueError("nums must be nonempty")
    ans = 0
    for b in range(max(nums).bit_length() - 1, -1, -1):
        prefixes = {x >> b for x in nums}    # bits >= b, shifted down
        candidate = (ans << 1) | 1           # ans is also kept shifted down
        ans = candidate if any(p ^ candidate in prefixes for p in prefixes) else ans << 1
    return ans


def max_xor_brute(nums: list[int]) -> int:
    return max(a ^ b for a in nums for b in nums)


def main():
    assert max_xor_trie([3, 10, 5, 8]) == max_xor_prefix([3, 10, 5, 8]) == 15
    assert max_xor_trie([3, 10, 5, 25, 2, 8]) == 28
    assert max_xor_trie([0]) == max_xor_prefix([0]) == 0
    assert max_xor_prefix([7, 7]) == 0
    rng = random.Random(16)
    for _ in range(400):
        nums = [rng.randrange(0, 1 << rng.randrange(1, 12)) for _ in range(rng.randrange(1, 30))]
        expected = max_xor_brute(nums)
        assert max_xor_trie(nums) == max_xor_prefix(nums) == expected


if __name__ == "__main__":
    main()
```

The code keeps `ans` and the prefixes shifted down by `b` (the table with the low zeros removed). Both methods cost O(n · B) time for `B`-bit numbers. The trie uses O(n · B) nodes; the prefix sets use O(n) at a time.

**Variants.** "Maximum XOR with an element from the array, where the element is at most `m`": sort queries by `m` and insert numbers into the trie as `m` grows (an offline sweep, as in [Sweep Line](../08-sweep-line/README.md)). "Maximum XOR of a subarray": insert prefix XORs `P[i]` and query each one; a subarray XOR is `P[r] ^ P[l]` (§6).

## 8. Advanced: the XOR basis (maximum subset XOR)

**Problem.** Choose any subset of a list (possibly empty) and XOR its elements. What is the largest possible result? For `[9, 8, 5]` the eight subsets give `0, 9, 8, 5, 9^8 = 1, 9^5 = 12, 8^5 = 13, 9^8^5 = 4`. The answer, 13, is bigger than every element. Trying all `2^n` subsets is hopeless for `n = 10^5`.

**The key observation: XOR is vector addition.** Treat each number as a vector of bits. XOR adds two vectors bit by bit, modulo 2. The set of values reachable as subset XORs is exactly the **span** of the numbers: everything you can build by adding some of them. In linear algebra over the two-element field GF(2) (arithmetic mod 2), a span is described by a **basis**: a small set of independent vectors that builds the same span.

We keep a basis in a special shape: `basis[b]` is either empty or a vector whose **highest set bit is `b`**. Distinct leading bits make the vectors independent, like rows of a matrix in echelon form.

**Insert `x`.** Scan from the highest bit down. If bit `b` of `x` is set and `basis[b]` exists, XOR it into `x`, which clears bit `b`. If `basis[b]` is empty, store `x` there and stop. If `x` becomes 0, it was already in the span (it adds nothing new).

**Query the maximum.** Start with `res = 0`. For `b` from high to low, if `res ^ basis[b] > res`, take it. Since `basis[b]` is the only vector with leading bit `b`, the decision at `b` is made by bit `b` alone, which is the same greedy argument as §7.

**Trace** for `[9, 8, 5]` (4 bits):

| Insert | Steps | Basis after |
|---|---|---|
| 9 = `1001` | bit 3 free → store | `b3: 1001` |
| 8 = `1000` | bit 3 taken → `1000 ^ 1001 = 0001`; bit 0 free → store | `b3: 1001`, `b0: 0001` |
| 5 = `0101` | bit 2 free → store | `b3: 1001`, `b2: 0101`, `b0: 0001` |

| Bit | `basis[b]` | `res ^ basis[b]` | bigger? | `res` |
|---:|---|---|---|---|
| 3 | `1001` | `1001` | yes | `1001` (9) |
| 2 | `0101` | `1100` | yes | `1100` (12) |
| 1 | — | | | `1100` |
| 0 | `0001` | `1101` | yes | `1101` (13) |

The basis has **rank** 3, so exactly `2^3 = 8` distinct values are reachable, matching the eight different values listed above.

```python
import random


class XorBasis:
    def __init__(self, bits: int = 64):
        if bits <= 0:
            raise ValueError("bits must be positive")
        self.basis = [0] * bits             # 0 means "empty"

    def insert(self, x: int) -> bool:
        """Add x to the span. Return False if x was already reachable."""
        if not 0 <= x < (1 << len(self.basis)):
            raise ValueError("x out of range")
        for b in range(len(self.basis) - 1, -1, -1):
            if not (x >> b) & 1:
                continue
            if self.basis[b] == 0:
                self.basis[b] = x
                return True
            x ^= self.basis[b]
        return False

    def max_xor(self) -> int:
        res = 0
        for b in range(len(self.basis) - 1, -1, -1):
            if res ^ self.basis[b] > res:
                res ^= self.basis[b]
        return res

    def can_make(self, x: int) -> bool:
        for b in range(len(self.basis) - 1, -1, -1):
            if (x >> b) & 1 and self.basis[b]:
                x ^= self.basis[b]
        return x == 0

    def rank(self) -> int:
        return sum(1 for v in self.basis if v)


def all_subset_xors(nums: list[int]) -> set[int]:
    reach = {0}
    for x in nums:
        reach |= {r ^ x for r in reach}
    return reach


def main():
    xb = XorBasis(4)
    for x in [9, 8, 5]:
        xb.insert(x)
    assert xb.basis == [1, 0, 5, 9] and xb.max_xor() == 13 and xb.rank() == 3
    assert XorBasis(8).max_xor() == 0                # empty subset
    rng = random.Random(17)
    for _ in range(300):
        nums = [rng.randrange(0, 1 << 10) for _ in range(rng.randrange(0, 14))]
        xb = XorBasis(10)
        for x in nums:
            xb.insert(x)
        reach = all_subset_xors(nums)
        assert xb.max_xor() == max(reach)
        assert len(reach) == 1 << xb.rank()
        for q in range(1 << 10):
            assert xb.can_make(q) == (q in reach)


if __name__ == "__main__":
    main()
```

Insert, query and membership each cost O(B) for `B`-bit numbers, so a list of `n` numbers costs O(n · B) to build. The basis holds at most `B` vectors, however long the list is.

**Why the maximum query is correct.** Every reachable value is a XOR of some basis vectors. The decision for `basis[b]` changes bit `b` and lower bits only, and no later vector can touch bit `b`. So taking it exactly when it turns bit `b` on is optimal, by the same "higher bit beats all lower bits" argument as §7.

**Where it goes next.** The same basis answers "the `k`-th smallest subset XOR" (reduce the basis fully, then read `k` in binary), "can `x` be made?" (`can_make`), and merges with prefix structures for "maximum subset XOR inside `a[l:r]`".

## 9. Summary

The facts behind every method: pairs cancel (`a ^ a = 0`), XOR undoes itself (`a ^ b = c` ⇒ `a = c ^ b`), any 1 bit of `a ^ b` separates `a` from `b`, and bit `b` outweighs all lower bits together, which makes "greedy from the top bit" correct.

| Problem | Method | Time | Extra space |
|---|---|---:|---:|
| One value appears once, others twice | XOR all | O(n) | O(1) |
| One value once, others three times | `ones`/`twos` | O(n) | O(1) |
| Two values once, others twice | XOR, split by `d = s & -s` | O(n) | O(1) |
| Missing from `0..n` | XOR indices and values | O(n) | O(1) |
| `l ^ … ^ r` | `f(r) ^ f(l − 1)` | O(1) | O(1) |
| Many subarray XORs | prefix XOR | O(n) + O(1) per query | O(n) |
| Maximum XOR of a pair | binary trie or prefix sets | O(n · B) | O(n · B) / O(n) |
| Maximum XOR of a subset | XOR basis | O(n · B) | O(B) |

## 10. Pitfalls and practice

1. **XOR does not cancel triples.** Three copies leave one; use bit counting mod 3 or the `ones`/`twos` machine.
2. **Forgetting the lowest-bit split needs `a ^ b ≠ 0`.** It holds whenever the two lonely values differ; validate it.
3. **Off-by-one in range XOR.** `l ^ … ^ r = f(r) ^ f(l − 1)`, and `f(−1) = 0`.
4. **Prefix XOR indexing.** `P` has `n + 1` entries; seed the dictionary with `{0: 1}` so subarrays starting at index 0 count.
5. **Trie width.** Every number must use the same number of levels, including leading zeros, or the walk compares the wrong bits.
6. **Negative numbers in a trie or basis.** Both assume nonnegative fixed-width numbers. Map 32-bit inputs with `x & 0xFFFFFFFF` first.
7. **Precedence.** `p ^ candidate in prefixes` is `(p ^ candidate) in prefixes` in Python, because `in` is a comparison. In C-family languages, parenthesize `(a ^ b) == c`.

Practice: single number I, II and III; missing number; set mismatch; find the duplicate number (XOR fails when a value repeats more than twice: know why); XOR operation in an array; XOR queries of a subarray; count triplets that can form two arrays of equal XOR; maximum XOR of two numbers in an array; maximum XOR with an element from array; decode XORed permutation; maximum subset XOR (linear basis).

Next: [Masks and Subsets](04-masks-and-subsets.md).
