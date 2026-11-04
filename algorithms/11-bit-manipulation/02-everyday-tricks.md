# Everyday Bit Tricks — Single Bits, Lowest Bits, and Counting

## 1. Reading and changing one bit

Eight on/off flags, numbered 0 to 7, fit in one integer `x`: bit `i` is 1 when flag `i` is on. Flags 3, 4 and 6 are on:

```text
bit:    7 6 5 4 3 2 1 0
x   =   0 1 0 1 1 0 0 0    (88)
```

Four jobs: is flag `i` on? turn it on, turn it off, flip it.

**The key observation.** `1 << i` has a single 1, at position `i`. Combine it with the operator whose truth table does the job ([Binary Numbers §3](01-binary-numbers.md#3-the-bitwise-operators)):

| Job | Code | Why it works |
|---|---|---|
| Test bit `i` | `(x >> i) & 1` | shift bit `i` down to position 0, keep only it |
| Set bit `i` | `x \| (1 << i)` | OR with 1 forces a 1; OR with 0 changes nothing |
| Clear bit `i` | `x & ~(1 << i)` | `~(1 << i)` is all 1s except at `i`; AND with 0 forces a 0 |
| Toggle bit `i` | `x ^ (1 << i)` | XOR with 1 flips; XOR with 0 changes nothing |

Trace from `x = 0101 1000`:

| Step | Operation | Mask | Result | Bits on |
|---:|---|---|---|---|
| 1 | test bit 4 | `0001 0000` | `x & mask = 0001 0000` → on | 3, 4, 6 |
| 3 | set bit 2 | `0000 0100` | `0101 1100` | 2, 3, 4, 6 |
| 4 | clear bit 6 | `~0100 0000 = 1011 1111` | `0001 1100` | 2, 3, 4 |
| 5 | toggle bit 3 | `0000 1000` | `0001 0100` | 2, 4 |

Toggling twice undoes itself; setting a set bit or clearing a clear one changes nothing (**idempotent**). The test replays random operations on a list of booleans and on `x` side by side:

```python
import random


def test_bit(x: int, i: int) -> bool:
    return (x >> i) & 1 == 1


def set_bit(x: int, i: int) -> int:
    return x | (1 << i)


def clear_bit(x: int, i: int) -> int:
    return x & ~(1 << i)


def toggle_bit(x: int, i: int) -> int:
    return x ^ (1 << i)


def main():
    x = 0b0101_1000
    assert test_bit(x, 4) and not test_bit(x, 2)
    x = set_bit(x, 2)
    assert x == 0b0101_1100
    x = clear_bit(x, 6)
    assert x == 0b0001_1100
    x = toggle_bit(x, 3)
    assert x == 0b0001_0100
    assert toggle_bit(x, 3) == 0b0001_1100
    assert clear_bit(x, 7) == x and set_bit(x, 2) == x   # idempotent

    rng = random.Random(2)
    n = 20
    for _ in range(200):
        flags = [False] * n
        x = 0
        for _ in range(50):
            i = rng.randrange(n)
            op = rng.choice(["set", "clear", "toggle"])
            if op == "set":
                flags[i], x = True, set_bit(x, i)
            elif op == "clear":
                flags[i], x = False, clear_bit(x, i)
            else:
                flags[i], x = not flags[i], toggle_bit(x, i)
            assert [test_bit(x, j) for j in range(n)] == flags


if __name__ == "__main__":
    main()
```

Each operation is O(1) on a machine word. Treating the integer as a whole set of flags, with union and intersection in one operator, is the subject of [Masks and Subsets](04-masks-and-subsets.md).

## 2. The lowest set bit: `x & -x`

**Problem.** Given `x > 0`, find the value of its lowest 1 bit, called the **lowest set bit** or **lowbit**. For `x = 88 = 0101 1000` it is `8 = 0000 1000`. The [Fenwick tree](../04-range-queries/02-fenwick-tree.md) is built on it.

**Brute force.** Test bits 0, 1, 2, … until one is set: up to `w` steps for a `w`-bit number.

**The key observation.** `−x = ~x + 1` ([Binary Numbers §5](01-binary-numbers.md#5-negative-numbers-twos-complement)). Watch what that does to `x`:

```text
x        = 0101 1000
~x       = 1010 0111     the trailing zeros of x became trailing ones
~x + 1   = 1010 1000     the +1 carries through them and stops at the old lowest 1
x & -x   = 0000 1000
```

Write `x` as `[high bits] 1 [k zeros]`. Then `−x` is `[flipped high bits] 1 [k zeros]`. AND keeps only the middle 1: the high bits are opposite, the low bits are zero in both. Python's integers act like infinite two's complement for `&`, so `x & -x` needs no masking.

## 3. Removing the lowest set bit: `x & (x - 1)`

Subtracting 1 borrows through the trailing zeros and turns the lowest 1 into 0:

```text
x         = 0101 1000
x - 1     = 0101 0111     lowest 1 became 0; the zeros below it became 1s
x & (x-1) = 0101 0000     the lowest 1 is gone; everything above is unchanged
```

**Power-of-two test.** A power of two has exactly one 1 bit, so removing it leaves 0:

$$
x \text{ is a power of two} \iff x > 0 \text{ and } x \mathbin{\&} (x-1) = 0 .
$$

The `x > 0` part matters: `0 & -1 == 0`, but 0 is not a power of two.

**Visiting every set bit.** Read the lowest bit, remove it, repeat. Each round handles one 1 bit, so the loop runs `popcount(x)` times, not once per position:

| Round | `x` | `low = x & -x` | index `low.bit_length() - 1` | `x & (x - 1)` |
|---:|---|---|---:|---|
| 1 | `0101 1000` | `0000 1000` | 3 | `0101 0000` |
| 2 | `0101 0000` | `0001 0000` | 4 | `0100 0000` |
| 3 | `0100 0000` | `0100 0000` | 6 | `0000 0000` |

```python
import random


def lowbit(x: int) -> int:
    if x <= 0:
        raise ValueError("x must be positive")
    return x & -x


def lowbit_brute(x: int) -> int:
    i = 0
    while not (x >> i) & 1:
        i += 1
    return 1 << i


def is_power_of_two(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0


def set_bit_indices(x: int) -> list[int]:
    if x < 0:
        raise ValueError("x must be nonnegative")
    out = []
    while x:
        out.append((x & -x).bit_length() - 1)
        x &= x - 1
    return out


def main():
    assert lowbit(0b0101_1000) == 0b1000
    assert set_bit_indices(0b0101_1000) == [3, 4, 6]
    assert set_bit_indices(0) == []
    assert [x for x in range(-4, 70) if is_power_of_two(x)] == [1, 2, 4, 8, 16, 32, 64]
    powers = {1 << k for k in range(200)}
    rng = random.Random(3)
    for _ in range(3000):
        x = rng.randrange(1, 1 << rng.randrange(1, 100))
        assert lowbit(x) == lowbit_brute(x)
        assert x & (x - 1) == x - lowbit_brute(x)
        assert is_power_of_two(x) == (x in powers)
        assert set_bit_indices(x) == [i for i in range(x.bit_length()) if (x >> i) & 1]
    try:
        lowbit(0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

`lowbit` and the power test are O(1) on machine words; `set_bit_indices` runs O(popcount(x)) rounds.

## 4. Counting 1 bits (popcount)

**Problem.** Count the 1 bits of `x`, its **popcount** or **Hamming weight**. `popcount(0101 1000) = 3`.

Three ways: add `x & 1` and shift right until 0, one round per position; **Kernighan's method**, removing the lowest set bit until 0 (§3), one round per 1 bit; or the built-in `x.bit_count()` (Python 3.10+).

**Negative inputs.** `(-3).bit_count()` is `2`: it counts the bits of `abs(x)`. A loop on `-3` never ends. For "number of 1 bits of a 32-bit int", mask first: `(-3 & 0xFFFFFFFF).bit_count() == 31`.

### Counting bits for every number from 0 to n

**Problem.** Return `bits[i] = popcount(i)` for `i = 0 … n`.

Calling popcount `n + 1` times costs O(n · w). **The key observation:** `i >> 1` is `i` without its lowest bit, and it is smaller than `i`, so its answer is already in the table:

$$
bits[i] = bits[i \gg 1] + (i \mathbin{\&} 1), \qquad bits[0] = 0 .
$$

| `i` | binary | `i >> 1` | `bits[i >> 1]` | `i & 1` | `bits[i]` |
|---:|---|---:|---:|---:|---:|
| 1 | `0001` | 0 | 0 | 1 | 1 |
| 2 | `0010` | 1 | 1 | 0 | 1 |
| 3 | `0011` | 1 | 1 | 1 | 2 |
| 6 | `0110` | 3 | 2 | 0 | 2 |
| 7 | `0111` | 3 | 2 | 1 | 3 |

`bits[i] = bits[i & (i - 1)] + 1` works too: removing the lowest set bit leaves a smaller number with one fewer 1. Either way it is a one-dimensional DP ([What DP Is](../09-dynamic-programming/01-what-is-dp.md)): each state depends on one smaller state.

### Hamming distance

The **Hamming distance** of two numbers is the number of positions where their bits differ. XOR marks exactly those positions, so it is `popcount(a ^ b)`: for `1 = 0001` and `4 = 0100`, `a ^ b = 0101` gives 2.

**Total over all pairs.** Count per bit position instead of per pair: if `c` of the `n` numbers have bit `i` set, that position differs in exactly `c · (n − c)` pairs. That is O(n · w) instead of O(n² · w). For `[4, 14, 2] = [0100, 1110, 0010]`: bit 1 has `c = 2` (contributes 2), bit 2 has `c = 2` (2), bit 3 has `c = 1` (2), total 6.

```python
import random
from itertools import combinations


def popcount_loop(x: int) -> int:
    if x < 0:
        raise ValueError("mask negative numbers to a fixed width first")
    count = 0
    while x:
        count += x & 1
        x >>= 1
    return count


def popcount_kernighan(x: int) -> int:
    if x < 0:
        raise ValueError("mask negative numbers to a fixed width first")
    count = 0
    while x:
        x &= x - 1
        count += 1
    return count


def count_bits(n: int) -> list[int]:
    if n < 0:
        raise ValueError("n must be nonnegative")
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + (i & 1)
    return bits


def hamming_weight_32(x: int) -> int:
    """Number of 1 bits in the 32-bit two's complement pattern of x."""
    return (x & 0xFFFFFFFF).bit_count()


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def total_hamming_distance(nums: list[int], width: int = 32) -> int:
    n = len(nums)
    total = 0
    for i in range(width):
        c = sum((x >> i) & 1 for x in nums)
        total += c * (n - c)
    return total


def main():
    assert popcount_loop(0b0101_1000) == popcount_kernighan(0b0101_1000) == 3
    assert count_bits(8) == [0, 1, 1, 2, 1, 2, 2, 3, 1]
    assert count_bits(0) == [0]
    assert hamming_weight_32(-3) == 31 and (-3).bit_count() == 2
    assert hamming_weight_32(-1) == 32
    assert hamming_distance(1, 4) == 2
    assert total_hamming_distance([4, 14, 2]) == 6
    assert total_hamming_distance([]) == 0
    rng = random.Random(4)
    for _ in range(2000):
        x = rng.randrange(0, 1 << 64)
        expected = bin(x).count("1")
        assert popcount_loop(x) == popcount_kernighan(x) == x.bit_count() == expected
    table = count_bits(5000)
    assert all(table[i] == bin(i).count("1") for i in range(5001))
    for _ in range(100):
        nums = [rng.randrange(0, 1 << 10) for _ in range(rng.randrange(0, 12))]
        brute = sum(hamming_distance(a, b) for a, b in combinations(nums, 2))
        assert total_hamming_distance(nums, 10) == brute


if __name__ == "__main__":
    main()
```

Per number: the loop is O(w), Kernighan O(popcount), `bit_count` O(w / 64) in C. `count_bits(n)` is O(n) time and space; `total_hamming_distance` is O(n · w).

## 5. Reversing bits

**Problem.** Reverse the 32-bit pattern of an unsigned integer: bit 0 swaps with bit 31, bit 1 with bit 30, and so on. In 8 bits, `1101 0010` becomes `0100 1011`.

`int(format(x, "032b")[::-1], 2)` works and serves as the brute force.

**Bit by bit.** Pop the lowest bit of `x` and push it onto the right end of `res`. The first bit popped (bit 0) gets shifted `w − 1` times and ends at the top. 8-bit trace for `x = 1101 0010`:

| Round | bit `x & 1` | `res = (res << 1) \| bit` | `x >>= 1` |
|---:|---:|---|---|
| 1 | 0 | `0000 0000` | `0110 1001` |
| 2 | 1 | `0000 0001` | `0011 0100` |
| 3 | 0 | `0000 0010` | `0001 1010` |
| 4 | 0 | `0000 0100` | `0000 1101` |
| 5 | 1 | `0000 1001` | `0000 0110` |
| 6 | 0 | `0001 0010` | `0000 0011` |
| 7 | 1 | `0010 0101` | `0000 0001` |
| 8 | 1 | `0100 1011` | `0000 0000` |

**Divide and conquer.** Reversing a block = swapping its two halves, then reversing each half. For 32 bits: swap the 16-bit halves, then the bytes inside each half, then the 4-bit groups, the pairs, and finally neighbouring bits. Each level is one line, with a mask that picks the low half of every block:

```text
swap halves of 32:   (x >> 16) | (x << 16)
swap halves of 16:   mask 0x00FF00FF
swap halves of 8:    mask 0x0F0F0F0F
swap halves of 4:    mask 0x33333333  (0011 repeated)
swap halves of 2:    mask 0x55555555  (0101 repeated)
```

In Python, mask to 32 bits after a left shift, because `x << 16` keeps the high bits.

```python
import random

MASK32 = 0xFFFFFFFF


def reverse_bits_loop(x: int, w: int = 32) -> int:
    if not 0 <= x < (1 << w):
        raise ValueError("x must be an unsigned w-bit number")
    res = 0
    for _ in range(w):
        res = (res << 1) | (x & 1)
        x >>= 1
    return res


def reverse_bits_32(x: int) -> int:
    if not 0 <= x <= MASK32:
        raise ValueError("x must be an unsigned 32-bit number")
    x = ((x >> 16) | (x << 16)) & MASK32
    x = ((x >> 8) & 0x00FF00FF) | ((x & 0x00FF00FF) << 8)
    x = ((x >> 4) & 0x0F0F0F0F) | ((x & 0x0F0F0F0F) << 4)
    x = ((x >> 2) & 0x33333333) | ((x & 0x33333333) << 2)
    x = ((x >> 1) & 0x55555555) | ((x & 0x55555555) << 1)
    return x


def reverse_bits_brute(x: int, w: int = 32) -> int:
    return int(format(x, f"0{w}b")[::-1], 2)


def main():
    assert reverse_bits_loop(0b1101_0010, 8) == 0b0100_1011
    assert reverse_bits_32(0b00000010100101000001111010011100) == 964176192
    assert reverse_bits_32(0) == 0 and reverse_bits_32(MASK32) == MASK32
    assert reverse_bits_32(1) == 1 << 31
    rng = random.Random(5)
    for _ in range(3000):
        x = rng.randrange(0, 1 << 32)
        expected = reverse_bits_brute(x)
        assert reverse_bits_loop(x) == reverse_bits_32(x) == expected
        assert reverse_bits_32(reverse_bits_32(x)) == x
    try:
        reverse_bits_32(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

The loop is O(w); the divide-and-conquer version is O(log w) mask operations. The same mask ladder, with additions instead of swaps, is the branch-free popcount used in C.

## 6. Adding two integers without `+`

**Problem.** Compute `a + b` using only bitwise operators. This is how hardware adds.

**The key observation.** Adding two bits gives a sum bit and a carry bit:

| `a` | `b` | sum bit | carry |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

The sum column is XOR; the carry column is AND. So `a ^ b` is the sum **ignoring carries**, and `(a & b) << 1` is the carries moved to where they land. Their sum is still `a + b`, so repeat on these two numbers until the carry is 0.

**Invariant:** `a + b` is the same after every round; only the split between "partial sum" and "carry" changes.

Trace `13 + 11`:

| Round | `a` | `b` | new `a = a ^ b` | new `b = (a & b) << 1` |
|---:|---|---|---|---|
| 1 | `01101` (13) | `01011` (11) | `00110` (6) | `10010` (18) |
| 2 | `00110` (6) | `10010` (18) | `10100` (20) | `00100` (4) |
| 3 | `10100` (20) | `00100` (4) | `10000` (16) | `01000` (8) |
| 4 | `10000` (16) | `01000` (8) | `11000` (24) | `00000` (0) |

The carry is 0, so the answer is 24. **Why it ends:** the carry's lowest set bit moves at least one place left each round, so with `w`-bit numbers the loop stops within `w + 1` rounds.

**Why Python needs masking.** Try `-1 + 1`. In Python `-1` is `...1111`, and the carry walks left through the infinite 1s forever (`b = 10, 100, 1000, …`). On a 32-bit machine it falls off at bit 31. **Fix:** keep both numbers as 32-bit patterns (`& 0xFFFFFFFF`) every round, then convert the final pattern back to signed. `~(a ^ MASK32)` equals `a − 2^32`: XOR with all ones flips the low 32 bits, and `~` flips them back while turning the leading 0s into 1s.

```python
import random

MASK32 = 0xFFFFFFFF
INT_MIN, INT_MAX = -(1 << 31), (1 << 31) - 1


def get_sum(a: int, b: int) -> int:
    """a + b with bitwise operators only, as 32-bit signed integers."""
    a &= MASK32
    b &= MASK32
    while b:
        a, b = (a ^ b) & MASK32, ((a & b) << 1) & MASK32
    return a if a <= INT_MAX else ~(a ^ MASK32)


def subtract(a: int, b: int) -> int:
    """a - b = a + (~b + 1), still without + or - on the operands."""
    return get_sum(a, get_sum(~b, 1))


def wrap32(x: int) -> int:
    x &= MASK32
    return x - (1 << 32) if x > INT_MAX else x


def main():
    assert get_sum(13, 11) == 24
    assert get_sum(-1, 1) == 0
    assert get_sum(-5, -7) == -12
    assert get_sum(INT_MAX, 1) == INT_MIN          # wraps like a real int
    assert subtract(5, 9) == -4
    rng = random.Random(8)
    for _ in range(5000):
        a = rng.randrange(INT_MIN, INT_MAX + 1)
        b = rng.randrange(INT_MIN, INT_MAX + 1)
        assert get_sum(a, b) == wrap32(a + b)
        assert subtract(a, b) == wrap32(a - b)
    for _ in range(500):                            # small values never wrap
        a, b = rng.randrange(-1000, 1001), rng.randrange(-1000, 1001)
        assert get_sum(a, b) == a + b


if __name__ == "__main__":
    main()
```

At most 33 rounds of O(1) work for 32-bit inputs: O(w) time, O(1) space.

## 7. Tricks you will read in C code

Three branch-free idioms show up in C and Java code. Know what they do; in Python, `a, b = b, a`, `abs`, `min` and `if` are clearer and as fast.

**XOR swap.** `a ^= b; b ^= a; a ^= b` swaps two variables, because `B ^ (A ^ B) = A` and `(A ^ B) ^ A = B`. The smallest failing example: swap `arr[i]` and `arr[j]` with `i == j`. Step 1 sets the slot to `A ^ A = 0`, and the value is lost. Rule: never XOR-swap two references that may alias.

**Sign mask and abs.** In 32 bits, `m = x >> 31` is 0 when `x ≥ 0` and −1 (all ones) when `x < 0`, because the arithmetic shift copies the sign bit everywhere. Then `abs(x) = (x ^ m) - m`: with `m = −1` this is `~x + 1 = −x`. The trap is `x = INT_MIN = −2^31`: `−x` does not fit, and the result is `INT_MIN` again.

**Branch-free min.** `y ^ ((x ^ y) & -(x < y))`: if `x < y`, `-(1)` is all ones and the result is `y ^ x ^ y = x`; otherwise the mask is 0 and the result is `y`.

```python
import random

MASK32 = 0xFFFFFFFF


def to_signed32(u: int) -> int:
    u &= MASK32
    return u - (1 << 32) if u >> 31 else u


def abs32(x: int) -> int:
    """Branch-free abs as a 32-bit machine computes it (wraps at INT_MIN)."""
    if not -(1 << 31) <= x < (1 << 31):
        raise ValueError("x must fit in a signed 32-bit integer")
    m = x >> 31                      # 0 or -1; Python's >> is arithmetic
    return to_signed32((x ^ m) - m)


def min_branchless(x: int, y: int) -> int:
    return y ^ ((x ^ y) & -(x < y))


def xor_swap(arr: list[int], i: int, j: int) -> None:
    arr[i] ^= arr[j]
    arr[j] ^= arr[i]
    arr[i] ^= arr[j]


def main():
    arr = [5, 9]
    xor_swap(arr, 0, 1)
    assert arr == [9, 5]
    arr = [7]
    xor_swap(arr, 0, 0)                          # same slot: the value is destroyed
    assert arr == [0]
    assert abs32(-6) == 6 and abs32(6) == 6 and abs32(0) == 0
    assert abs32(-(1 << 31)) == -(1 << 31)       # INT_MIN has no positive partner
    rng = random.Random(7)
    for _ in range(3000):
        x = rng.randrange(-(1 << 31) + 1, 1 << 31)
        y = rng.randrange(-(1 << 31), 1 << 31)
        assert abs32(x) == abs(x)
        assert min_branchless(x, y) == min(x, y)
        assert (x >> 31) == (-1 if x < 0 else 0)


if __name__ == "__main__":
    main()
```

## 8. Summary

| Expression | Meaning | `x = 0101 1000` |
|---|---|---|
| `(x >> i) & 1` | bit `i` | `i = 4` → 1 |
| `x \| (1 << i)`, `x & ~(1 << i)`, `x ^ (1 << i)` | set, clear, toggle bit `i` | |
| `x & -x` | lowest set bit | `0000 1000` |
| `x & (x - 1)` | remove the lowest set bit | `0101 0000` |
| `(x & -x).bit_length() - 1` | index of the lowest set bit (trailing zeros) | 3 |
| `x.bit_length() - 1` | index of the highest set bit | 6 |
| `1 << (x.bit_length() - 1)` | highest set bit | `0100 0000` |
| `x > 0 and (x & (x - 1)) == 0` | power of two? | no |
| `x.bit_count()` | popcount | 3 |
| `(a ^ b).bit_count()` | Hamming distance | |
| `a ^ b`, `(a & b) << 1` | sum without carries, carries | |
| `x & 0xFFFFFFFF`, then `u - 2**32` if bit 31 | 32-bit pattern and back | |

## 9. Pitfalls and practice

1. **`x & -x` or `x & (x - 1)` on `x = 0`.** Both give 0. The power-of-two test needs `x > 0`; a lowbit loop must stop at 0.
2. **Counting bits of a negative number.** Python's loop never ends, and `bit_count` counts `abs(x)`. Mask to the problem's width first.
3. **Precedence.** `x & 1 << i` is `x & (1 << i)`, which is fine; `x & 1 == 0` is safe only in Python. In C, Java and JavaScript write `(x & 1) == 0`.
4. **Not masking after a left shift.** Bit reversal and bitwise addition must mask to 32 bits after each step in Python, or high bits pile up.
5. **Converting back to signed.** A 32-bit pattern above `2^31 − 1` is negative: return `u − 2^32` (or `~(u ^ MASK32)`), not `u`.
6. **XOR swap of aliased slots** zeroes the value (§7).
7. **`abs(INT_MIN)`** overflows in fixed width; the branch-free version returns `INT_MIN` (§7).

Practice: number of 1 bits; counting bits; power of two; power of four (one set bit at an even position: `x & 0x55555555`); reverse bits; Hamming distance; total Hamming distance; sum of two integers; minimum flips to make `a OR b` equal to `c`; binary watch; bitwise AND of numbers range (the common high prefix of `left` and `right`).

Next: [XOR](03-xor.md).
