# Binary Numbers — Bits, Operators, and Negative Numbers

## 1. What the bits `1011 0110` mean

A computer stores every integer as a row of **bits**, digits that are 0 or 1. Which number is the byte `1011 0110`? (The space only groups the bits in fours for reading.)

Decimal digits have place values 1, 10, 100, …: `407 = 4·100 + 0·10 + 7·1`. Binary works the same way with base 2. Number the positions from the right, starting at 0; position `i` is worth `2^i`:

| Position `i` | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Value `2^i` | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
| Bit of `1011 0110` | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0 |

Add the values of the positions that hold a 1: `128 + 32 + 16 + 4 + 2 = 182`.

Words used in every chapter of this folder:

- **Bit `i`** is the bit worth `2^i`. Bit 0 is the **lowest bit** (least significant); the highest position is the **highest bit** (most significant).
- With `w` bits there are `2^w` patterns, so the unsigned values `0 … 2^w − 1`. Eight bits are a **byte**: `0 … 255`.
- Bit 0 is the only odd place value, so **bit 0 says whether the number is odd**.
- A single 1 followed by zeros (`1`, `10`, `100`, `1000`) is a **power of two** (1, 2, 4, 8).

## 2. Decimal to binary, and Python's tools

Going the other way, divide by 2 repeatedly. Each remainder is the next bit **from the right**; stop when the quotient is 0. For 182:

| Step | Number | ÷ 2 | Remainder = next bit | Bits so far |
|---:|---:|---:|---:|---|
| 1 | 182 | 91 | 0 | `0` |
| 2 | 91 | 45 | 1 | `10` |
| 3 | 45 | 22 | 1 | `110` |
| 4 | 22 | 11 | 0 | `0110` |
| 5 | 11 | 5 | 1 | `1 0110` |
| 6 | 5 | 2 | 1 | `11 0110` |
| 7 | 2 | 1 | 0 | `011 0110` |
| 8 | 1 | 0 | 1 | `1011 0110` |

**Why it works.** Every position except bit 0 is worth an even amount, so `n % 2` is bit 0. Dropping the remainder (`n // 2`) slides every bit one place right, so the next bit becomes bit 0.

Reading a binary string left to right is the reverse: each new bit doubles the value so far and adds itself (`1 → 2 → 5 → 11 → 22 → 45 → 91 → 182`).

| You want | Write | Result |
|---|---|---|
| Binary string | `bin(182)` / `format(182, "b")` | `'0b10110110'` / `'10110110'` |
| Fixed width, zero padded | `format(5, "08b")` or `f"{5:08b}"` | `'00000101'` |
| Parse a binary string | `int("10110110", 2)` | `182` |
| Binary literal | `0b1011_0110` | `182` (underscores are ignored) |
| Number of bits needed | `(182).bit_length()` | `8` (and `(0).bit_length() == 0`) |

```python
import random


def to_binary(n: int) -> str:
    """Repeated division by 2."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n == 0:
        return "0"
    bits = []
    while n > 0:
        bits.append(str(n % 2))  # the lowest bit
        n //= 2                  # slide the remaining bits right
    return "".join(reversed(bits))


def from_binary(s: str) -> int:
    """Each new bit doubles what came before and adds itself."""
    if not s or any(c not in "01" for c in s):
        raise ValueError("s must be a nonempty string of 0s and 1s")
    value = 0
    for c in s:
        value = value * 2 + int(c)
    return value


def main():
    assert to_binary(182) == "10110110" and from_binary("10110110") == 182
    assert to_binary(0) == "0" and from_binary("0") == 0
    assert from_binary("0001") == 1          # leading zeros do not change the value
    assert format(5, "08b") == "00000101"
    assert (182).bit_length() == 8 and (0).bit_length() == 0
    rng = random.Random(1)
    for _ in range(1000):
        n = rng.randrange(0, 10**12)
        assert to_binary(n) == bin(n)[2:] == format(n, "b")
        assert from_binary(to_binary(n)) == n == int(to_binary(n), 2)
    for bad in ["", "12", "-1"]:
        try:
            from_binary(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

`to_binary` takes O(log n) steps, one per bit; `from_binary` takes O(len(s)).

## 3. The bitwise operators

A **bitwise operator** works on each position separately: bit `i` of the result depends only on bit `i` of the inputs. There is no carry between positions, unlike `+`.

| `a` | `b` | `a & b` (AND) | `a \| b` (OR) | `a ^ b` (XOR) |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 1 | 1 |
| 1 | 0 | 0 | 1 | 1 |
| 1 | 1 | 1 | 1 | 0 |

- **AND** is 1 only when both bits are 1: use it to *keep* chosen bits and erase the rest.
- **OR** is 1 when at least one bit is 1: use it to *turn bits on*.
- **XOR** (exclusive or) is 1 when the bits *differ*: use it to *flip* bits or detect a difference. [XOR](03-xor.md) is a whole chapter.
- **NOT**, `~a`, flips every bit. It takes one input.

With `a = 202` and `b = 166`, apply the table column by column:

```text
a       = 1100 1010   (202)
b       = 1010 0110   (166)
a & b   = 1000 0010   (130)   1 only where both have 1
a | b   = 1110 1110   (238)   1 where either has 1
a ^ b   = 0110 1100   (108)   1 where they differ
~a      = 0011 0101   ( 53)   every bit of a flipped, in 8 bits
```

The `~a` line is true only on an 8-bit machine. Python prints `~202` as `-203`; §5 and §6 explain why.

**Masks.** A **mask** is a number whose 1 bits mark the positions you care about. AND with a mask keeps those positions and zeroes the rest:

```text
x        = 1011 0110
mask     = 0000 1111   (keep the low four bits)
x & mask = 0000 0110
```

Hexadecimal (`0x…`, base 16) is convenient for masks because each hex digit is exactly four bits: `0xF = 1111`, `0xFF` is eight 1s, `0xFFFFFFFF` is thirty-two 1s. `x & 1` keeps only bit 0, the odd/even test.

## 4. Shifts: multiplying and dividing by powers of two

`x << k` (**left shift**) slides every bit `k` places left and fills with zeros. `x >> k` (**right shift**) slides every bit `k` places right; bits that fall off the right end are lost.

```text
13       =    0000 1101
13 << 2  =    0011 0100   (52)
13 >> 2  =    0000 0011   ( 3)   the two low bits 01 fell off
```

Moving a bit up one position doubles its value, so

$$
x \ll k = x\cdot 2^k, \qquad x \gg k = \left\lfloor \frac{x}{2^k} \right\rfloor .
$$

The right shift **rounds down** (toward minus infinity), because the bits that fall off are exactly the remainder. For negative numbers this is not C's division:

| Expression | Python result | Why |
|---|---:|---|
| `-13 >> 1` | `-7` | shift = floor division |
| `-13 // 2` | `-7` | floor division |
| `int(-13 / 2)` | `-6` | rounds toward zero, like C's `-13 / 2` |

In C and Java, `>>` on a negative `int` is also a floor (an **arithmetic** shift, which copies the sign bit in from the left), but `/` truncates toward zero. Java's `>>>` and C's shift of an `unsigned` value fill with zeros instead (a **logical** shift).

**Fixed width drops bits on the left, too.** In 8 bits, `200 << 1` is `1 1001 0000` with the ninth bit thrown away: `1001 0000 = 144 = 400 mod 256`. In general a `w`-bit machine computes `x · 2^k mod 2^w`. Python never drops bits, so `200 << 1 == 400`; to imitate 8 bits, mask: `(200 << 1) & 0xFF == 144`.

## 5. Negative numbers: two's complement

An 8-bit machine has 256 patterns. To store negative numbers, almost every computer uses **two's complement**: the highest bit gets a **negative** place value.

| Position | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unsigned value | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
| Signed value | **−128** | 64 | 32 | 16 | 8 | 4 | 2 | 1 |

`1111 1011` read unsigned is `251`; read signed it is `−128 + 64 + 32 + 16 + 8 + 2 + 1 = −5`. The two readings differ by exactly `256 = 2^8` whenever the top bit is 1. That top bit is the **sign bit**: 1 means negative. Signed 8-bit values run from `−128` to `127`.

Put the 256 patterns on a wheel; adding 1 steps clockwise:

```text
             0000 0000 (0)
   1111 1111 (-1)    0000 0001 (1)
        ...                ...
   1000 0000 (-128)  0111 1111 (127)
         ^---- 127 + 1 wraps ----^
```

- **`−1` is all ones** in every width: it is one step back from `0000 0000`.
- **Overflow wraps silently.** `127 + 1` lands on `1000 0000 = −128`. The hardware raises no error.

**Negating: flip every bit, then add 1.** `x` and `~x` have opposite bits everywhere, so their sum is all ones, which is `−1`:

```text
x        = 0000 0101   (5)
~x       = 1111 1010
x + ~x   = 1111 1111   (-1)
```

So `~x = −x − 1`, or `−x = ~x + 1`. Check: `~5 + 1 = 1111 1011 = −5`. The same identity explains Python's `~202 == −203`.

**The one number without a partner.** `−(−128)` in 8 bits is `~1000 0000 + 1 = 0111 1111 + 1 = 1000 0000 = −128` again. In 32 bits the same happens to `−2^31`, which is why `abs(INT_MIN)` overflows in C and Java.

**Why machines use it.** Addition needs no sign logic. The adder adds the patterns as unsigned numbers and drops the carry out of the top; read as signed, the answer is right:

```text
  1111 1011   (-5, or 251 unsigned)
+ 0000 0111   ( 7)
1 0000 0010   drop the 9th bit -> 0000 0010 = 2
```

## 6. Python's integers have no fixed width

A Python `int` grows as large as it needs to: nothing wraps, `2**100` is fine, and `200 << 1` is `400`. For bitwise operators Python acts as if every integer were two's complement with **infinitely many** bits: nonnegative numbers have infinitely many 0s on the left, negative numbers infinitely many 1s.

```text
 5  = ...0000 0000 0101
-5  = ...1111 1111 1011
-1  = ...1111 1111 1111
```

So `&`, `|`, `^`, `~` and `>>` give sensible answers on negatives: `-5 & 0xFF == 251` (the low 8 bits of `...1011`), and `-1 >> 10 == -1`. Two surprises remain:

1. `bin(-5)` is `'-0b101'`: sign and magnitude, **not** the two's complement bits. To see the bits, mask first: `format(-5 & 0xFF, "08b") == '11111011'`.
2. `while x: x >>= 1` never ends for negative `x`: shifting right stops at `-1`, never 0.

**Simulating 32-bit integers.** Interview problems often assume 32-bit signed integers. Two conversions are all you need:

- **To the pattern:** `u = x & 0xFFFFFFFF`, a number in `[0, 2^32)` with the low 32 bits of `x`.
- **Back to signed:** if bit 31 of `u` is set, the value is `u − 2^32`; otherwise it is `u`.

For `x = −5`: `u = 1111 … 1111 1011 = 4294967291`; bit 31 is set, so `4294967291 − 4294967296 = −5`.

The script wraps these for any width `w` and checks them against "walk around the wheel by whole turns":

```python
import random


def to_unsigned(x: int, w: int = 32) -> int:
    """The w-bit pattern of x, read as an unsigned number in [0, 2^w)."""
    if w <= 0:
        raise ValueError("width must be positive")
    return x & ((1 << w) - 1)


def to_signed(u: int, w: int = 32) -> int:
    """Read a w-bit pattern as a two's complement number in [-2^(w-1), 2^(w-1))."""
    if w <= 0:
        raise ValueError("width must be positive")
    u &= (1 << w) - 1
    return u - (1 << w) if (u >> (w - 1)) & 1 else u


def wrap_add(a: int, b: int, w: int = 32) -> int:
    """a + b as a w-bit signed machine computes it."""
    return to_signed(a + b, w)


def wrap_brute(value: int, w: int) -> int:
    """Push value into [-2^(w-1), 2^(w-1)) by whole turns of the wheel."""
    half, full = 1 << (w - 1), 1 << w
    while value >= half:
        value -= full
    while value < -half:
        value += full
    return value


def main():
    assert to_unsigned(-5, 8) == 251 and format(to_unsigned(-5, 8), "08b") == "11111011"
    assert to_signed(251, 8) == -5
    assert to_unsigned(-1) == 0xFFFFFFFF and to_signed(0xFFFFFFFF) == -1
    assert wrap_add(127, 1, 8) == -128                # the wheel wraps
    assert wrap_add(2**31 - 1, 1) == -2**31           # INT_MAX + 1
    assert to_signed(128, 8) == -128                  # -(-128) has no 8-bit partner
    assert ~202 == -203 and ~202 & 0xFF == 53
    assert -13 >> 1 == -7 == -13 // 2 and int(-13 / 2) == -6
    assert (200 << 1) & 0xFF == 144
    assert bin(-5) == "-0b101"
    rng = random.Random(6)
    for _ in range(2000):
        w = rng.choice([4, 8, 16, 32])
        x = rng.randrange(-(1 << (w + 3)), 1 << (w + 3))
        assert to_signed(to_unsigned(x, w), w) == wrap_brute(x, w)
        assert 0 <= to_unsigned(x, w) < (1 << w)
        k = rng.randrange(0, 10)
        assert x >> k == x // (1 << k)                # shifts are floor division
        assert x << k == x * (1 << k)
        assert -x == ~x + 1                           # negation identity
    try:
        to_signed(5, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    main()
```

Each helper is O(1) for fixed `w` (Python's big-integer operations cost O(w / 64) machine words).

## 7. Operator precedence

The smallest failing example: `x & 1 == 0` means `(x & 1) == 0` in Python, but `x & (1 == 0)` in C, C++, Java and JavaScript, where `==` binds tighter than `&`. A second one, in every language: `1 << k - 1` is `1 << (k - 1)`, not `(1 << k) - 1`.

Python's order, tightest first: `**`; unary `-x ~x`; `* / // %`; `+ -`; `<< >>`; `&`; `^`; `|`; then comparisons (`==`, `<`, `in`), `not`, `and`, `or`.

**The rule:** parenthesize every bitwise subexpression that is mixed with another operator. The code in this folder does so even where Python would not need it.

```python
def main():
    x, k = 6, 3
    assert (x & 1 == 0) == ((x & 1) == 0)         # Python: comparisons bind loosest
    assert 1 << k - 1 == 4 and (1 << k) - 1 == 7  # not the same thing
    assert 1 | 2 ^ 3 == 1 and (1 | 2) ^ 3 == 0    # ^ binds tighter than |


if __name__ == "__main__":
    main()
```

## 8. Summary

| Operation | Code | Fixed width `w` | Python |
|---|---|---|---|
| Keep bits | `x & mask` | | |
| Turn bits on | `x \| mask` | | |
| Flip bits | `x ^ mask` | | |
| Flip all | `~x` | `(2^w − 1) − x` | `−x − 1`; use `~x & ((1 << w) - 1)` for `w` bits |
| Multiply by `2^k` | `x << k` | `x · 2^k mod 2^w` | exact, never overflows |
| Divide by `2^k` | `x >> k` | floor (arithmetic shift) | floor, `x // 2**k` |
| Negate | `~x + 1` | `−2^(w−1)` maps to itself | exact |
| To `w`-bit pattern | `x & ((1 << w) - 1)` | | |
| Pattern back to signed | `u - (1 << w)` if bit `w−1` set | | |

Identities worth remembering: `x + ~x = −1`; `−x = ~x + 1`; `x >> k == x // 2**k`; `x & 1` is `x % 2`.

## 9. Pitfalls and practice

1. **Reading `bin()` of a negative number as its bits.** `bin(-5)` is `'-0b101'`. Mask with `& ((1 << w) - 1)` before formatting.
2. **Assuming `~x` is small.** In Python `~x == -x - 1`; in `w` bits get `~x & ((1 << w) - 1)`.
3. **Assuming `x >> 1` truncates.** It floors: `-13 >> 1 == -7`, while C's `-13 / 2` is `-6`.
4. **Forgetting wraparound when porting.** Code that relies on overflow in C (hashes, `x << 31`) gives different numbers in Python unless you mask after each step.
5. **Shifting a negative number right until it is zero.** It stops at `-1` forever. Convert to the unsigned pattern first.
6. **Precedence.** `x & 1 == 0` is wrong in C-family languages; `1 << k - 1` is `1 << (k - 1)` everywhere (§7).
7. **Shifting by the width or more in C/Java.** `1 << 32` on a 32-bit `int` is undefined in C and becomes `1 << 0` in Java. Python has no such limit.

Practice: convert 37, 100, 255 and 256 by hand both ways; add binary strings; convert a number to hexadecimal and to base −2 by hand; write the 8-bit patterns of −1, −100 and −128; reverse integer with 32-bit overflow detection; number complement (flip the bits below the highest set bit).

Next: [Everyday Bit Tricks](02-everyday-tricks.md).
