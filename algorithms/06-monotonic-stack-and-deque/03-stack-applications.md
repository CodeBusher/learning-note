# Stack Applications — Greedy Removal, Trapped Water, Patterns, Fleets

## 1. Remove k digits: the smallest number left

**Problem.** Given a number as a string of digits and an integer `k`, delete exactly `k` digits so that the remaining number is as small as possible. Drop leading zeros, and return `"0"` if nothing is left.

| `num` | `k` | Answer | Why |
|---|---:|---|---|
| `"1432219"` | 3 | `"1219"` | delete 4, 3, and one 2 |
| `"10200"` | 1 | `"200"` | delete 1; `"0200"` loses its leading zero |
| `"10"` | 2 | `"0"` | nothing is left |

**Brute force.** Try every way to keep `n − k` of the `n` digits, in order, and take the smallest. All candidates have the same length, so the smallest string is also the smallest number. There are `C(n, k)` candidates, which is about `1.8 × 10²⁸` for `n = 100, k = 50`.

### The key observation: a bigger digit before a smaller one should go

Numbers of equal length compare at their **first differing digit**, so the leftmost digits matter most. In `"1432219"`, deleting the `4` moves the `3` into its place: `"132219"` beats `"142219"` at the second digit, whatever happens later. In general:

> While deletions remain, a digit that is **larger than the digit after it** should be deleted.

Keep the digits chosen so far on a stack. When a new digit `d` arrives and the top is larger, pop the top (spending one deletion) and check again. While deletions remain the stack stays **nondecreasing**, so deletions left over at the end are spent on the tail, where the largest digits are (`"12345"`, `k = 2` gives `"123"`).

### Worked trace

`num = "1432219"`, `k = 3`:

| Digit | Pops (deletions left after) | Stack after |
|---|---|---|
| `1`, `4` | — (3) | `1 4` |
| `3` | `4` (2) | `1 3` |
| `2` | `3` (1) | `1 2` |
| `2` | — (1); equal is not larger | `1 2 2` |
| `1` | `2` (0) | `1 2 1` |
| `9` | — (0); no deletions left | `1 2 1 9` |

Result `"1219"`. When the second `1` arrived, the top `2` was larger, but only one deletion was left, so only one `2` could go.

The code comes after §2, which changes one rule.

**Why it's correct.** The first digit of the answer must come from the first `k + 1` digits, because at most `k` digits can be deleted in front of it. The best choice is the smallest of those, at its earliest position, and the stack finds exactly that: every larger digit before it was popped, and nothing after it is reachable. Once the first digit is fixed, the same argument repeats on the rest of the string with the deletions that are left. The brute-force test checks this on all small cases with repeated digits.

## 2. Smallest subsequence with each letter once

**Problem.** Given a string, delete letters so that every distinct letter appears **exactly once**, and the result is the lexicographically smallest possible (dictionary order). The letters keep their original order.

| `s` | Answer |
|---|---|
| `"bcabc"` | `"abc"` |
| `"cbacdcbc"` | `"acdb"` |
| `"abacb"` | `"abc"` |

### The key observation: pop a bigger letter only if it comes back later

This is remove-`k`-digits with a different budget. A bigger letter before a smaller one should go, but now a letter may be deleted **only if another copy of it appears later**; otherwise it would be lost. So precompute `last[c]`, the last index of each letter, and pop the top only while:

- the top is larger than the current letter, and
- the top appears again later: `last[top] > i`.

One more rule: if the current letter is **already on the stack**, skip it. The copy on the stack is already in a position at least as good. (Why: let `y` be the letter right above that copy. When `y` arrived, it did not pop the copy, even though the copy appears again later, namely now. So the copy is smaller than `y`. Moving the copy to the current position would put the larger `y` in its place and make the string bigger.)

### Worked trace

`s = "cbacdcbc"`. Last positions: `a → 2`, `b → 6`, `c → 7`, `d → 4`.

| `i` | Letter | Action | Stack after |
|---:|---|---|---|
| 0 | `c` | push | `c` |
| 1 | `b` | `c > b` and `c` returns at 7: pop `c`; push | `b` |
| 2 | `a` | `b > a` and `b` returns at 6: pop `b`; push | `a` |
| 3, 4 | `c`, `d` | push | `a c d` |
| 5 | `c` | already on the stack: skip | `a c d` |
| 6 | `b` | `d > b` but `d` never returns (last 4): stop; push | `a c d b` |
| 7 | `c` | already on the stack: skip | `a c d b` |

Result `"acdb"`. At `i = 6` the `d` would have been worth popping, but it was the last `d`, so it had to stay.

### Code for §1 and §2

```python
import random
from itertools import combinations


def remove_k_digits(num: str, k: int) -> str:
    if not 0 <= k <= len(num) or not num.isdigit() and num:
        raise ValueError("need a digit string and 0 <= k <= len(num)")
    stack: list[str] = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    if k:
        del stack[-k:]                      # leftover deletions: cut the largest tail
    return "".join(stack).lstrip("0") or "0"


def remove_k_digits_brute(num: str, k: int) -> str:
    keep = len(num) - k
    best = min("".join(num[i] for i in idx) for idx in combinations(range(len(num)), keep))
    return best.lstrip("0") or "0"


def smallest_distinct_subsequence(s: str) -> str:
    last = {c: i for i, c in enumerate(s)}
    stack: list[str] = []
    on_stack: set[str] = set()
    for i, c in enumerate(s):
        if c in on_stack:
            continue
        while stack and stack[-1] > c and last[stack[-1]] > i:
            on_stack.remove(stack.pop())
        stack.append(c)
        on_stack.add(c)
    return "".join(stack)


def smallest_distinct_subsequence_brute(s: str) -> str:
    letters = set(s)
    best = None
    for idx in combinations(range(len(s)), len(letters)):
        candidate = "".join(s[i] for i in idx)
        if set(candidate) == letters and (best is None or candidate < best):
            best = candidate
    return best if best is not None else ""


def main():
    assert remove_k_digits("1432219", 3) == "1219"
    assert remove_k_digits("10200", 1) == "200"
    assert remove_k_digits("10", 2) == "0"
    assert remove_k_digits("12345", 2) == "123"
    assert remove_k_digits("9", 0) == "9"
    try:
        remove_k_digits("12", 3)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(20)
    for _ in range(2000):
        num = "".join(rng.choice("01239") for _ in range(rng.randrange(1, 9)))
        k = rng.randrange(len(num) + 1)
        assert remove_k_digits(num, k) == remove_k_digits_brute(num, k), (num, k)

    assert smallest_distinct_subsequence("bcabc") == "abc"
    assert smallest_distinct_subsequence("cbacdcbc") == "acdb"
    assert smallest_distinct_subsequence("abacb") == "abc"
    assert smallest_distinct_subsequence("") == ""
    assert smallest_distinct_subsequence("aaaa") == "a"
    for _ in range(2000):
        s = "".join(rng.choice("abcd") for _ in range(rng.randrange(11)))
        assert smallest_distinct_subsequence(s) == smallest_distinct_subsequence_brute(s), s


if __name__ == "__main__":
    main()
```

Both are `O(n)` time: each character is pushed once and popped at most once. Remove `k` digits uses `O(n)` space; the distinct-letters version uses `O(σ)` for the stack, set and `last`, where `σ` is the alphabet size.

## 3. Trapping rain water: three ways

**Problem.** Bars of width 1 have heights `h[0..n−1]`. After rain, water collects between taller bars. How many units of water are trapped?

```text
heights = [4, 2, 0, 3, 2, 5]

          █
█ ~ ~ ~ ~ █
█ ~ ~ █ ~ █
█ █ ~ █ █ █
█ █ ~ █ █ █
4 2 0 3 2 5      water per column: 0 2 4 1 2 0, total 9
```

### Brute force: one column at a time

Water stands on column `i` up to the lower of the two highest walls around it, the tallest bar on its left (including itself) and the tallest on its right (including itself):

$$
\text{water}[i]=\min\Big(\max_{j\le i}h[j],\ \max_{j\ge i}h[j]\Big)-h[i].
$$

Computing both maxima from scratch for every column is `O(n²)`. Storing them in two arrays, `left_max` from a left-to-right pass and `right_max` from a right-to-left pass, makes it `O(n)` time and `O(n)` space. That is the prefix-maximum version.

### The stack view: fill water in horizontal layers

The stack method counts water differently: in **horizontal layers**, the way a bathtub between two walls fills.

Keep a stack of bar indices whose heights are decreasing from bottom to top: bars still waiting for a taller right wall. When a bar `j` arrives that is taller than the top:

1. Pop the top. It is the **floor** of a pool.
2. The new top (if any) is the **left wall**; bar `j` is the **right wall**.
3. The pool between them has width `j − left − 1` and its water rises from the floor to the lower wall: depth `min(h[left], h[j]) − h[floor]`. Add `width × depth`.
4. Repeat while bar `j` is still taller than the top.

If the stack becomes empty after popping a floor, there is no left wall, and water would run off the left side.

Trace for `[4, 2, 0, 3, 2, 5]`, stack as `index:height`:

| `j` | `h[j]` | Floor popped | Left wall | Width | Depth | Added | Total | Stack after |
|---:|---:|---|---|---:|---:|---:|---:|---|
| 0–2 | 4, 2, 0 | — | | | | | 0 | `0:4  1:2  2:0` |
| 3 | 3 | `2:0` | `1:2` | 1 | 2 − 0 = 2 | 2 | 2 | |
|   |   | `1:2` | `0:4` | 2 | 3 − 2 = 1 | 2 | 4 | `0:4  3:3` |
| 4 | 2 | — | | | | | 4 | `0:4  3:3  4:2` |
| 5 | 5 | `4:2` | `3:3` | 1 | 3 − 2 = 1 | 1 | 5 | |
|   |   | `3:3` | `0:4` | 4 | 4 − 3 = 1 | 4 | 9 | |
|   |   | `0:4` | none | | | | 9 | `5:5` |

The layer added at `j = 5` with width 4 is the band between heights 3 and 4 spanning columns 1 to 4: one row of the picture.

### Two pointers: constant extra space

The column formula needs, for each column, the smaller of its two side maxima. We do not always need to know both exactly. Walk inward from both ends, keeping `left_max` (the tallest bar seen from the left) and `right_max` (the tallest seen from the right):

- If `left_max <= right_max`, process the left column `l`. Its true left maximum is `max(left_max, h[l])`, known exactly. Its true right maximum is at least `right_max`, which is at least `left_max`. So the smaller side is the left one, and the water is `max(left_max, h[l]) − h[l]`. Move `l` right.
- Otherwise process the right column `r` symmetrically.

Trace for `[4, 2, 0, 3, 2, 5]`:

| `l` | `r` | `left_max` | `right_max` | Side processed | Added | Total |
|---:|---:|---:|---:|---|---:|---:|
| 0 | 5 | 0 | 0 | left, `h[0] = 4`: `left_max` → 4 | 0 | 0 |
| 1 | 5 | 4 | 0 | right, `h[5] = 5`: `right_max` → 5 | 0 | 0 |

From here `left_max = 4 <= right_max = 5` for every remaining column, so `l` walks right through columns 1 to 4, adding `4 − 2, 4 − 0, 4 − 3, 4 − 2 = 2, 4, 1, 2`. The loop stops when `l > r`. Total 9 again.

```python
import random


def trap_brute(h: list[int]) -> int:
    return sum(min(max(h[:i + 1]), max(h[i:])) - h[i] for i in range(len(h)))


def trap_prefix(h: list[int]) -> int:
    n = len(h)
    left_max, right_max = [0] * n, [0] * n
    for i in range(n):
        left_max[i] = max(h[i], left_max[i - 1] if i else 0)
    for i in range(n - 1, -1, -1):
        right_max[i] = max(h[i], right_max[i + 1] if i + 1 < n else 0)
    return sum(min(left_max[i], right_max[i]) - h[i] for i in range(n))


def trap_stack(h: list[int]) -> int:
    water = 0
    stack: list[int] = []                  # heights nonincreasing bottom -> top
    for j, height in enumerate(h):
        while stack and h[stack[-1]] < height:
            floor = stack.pop()
            if not stack:
                break                      # no left wall: water runs off
            left = stack[-1]
            width = j - left - 1
            depth = min(h[left], height) - h[floor]
            water += width * depth
        stack.append(j)
    return water


def trap_two_pointers(h: list[int]) -> int:
    l, r = 0, len(h) - 1
    left_max = right_max = water = 0
    while l <= r:
        if left_max <= right_max:
            left_max = max(left_max, h[l])
            water += left_max - h[l]
            l += 1
        else:
            right_max = max(right_max, h[r])
            water += right_max - h[r]
            r -= 1
    return water


def main():
    for f in (trap_brute, trap_prefix, trap_stack, trap_two_pointers):
        assert f([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
        assert f([4, 2, 0, 3, 2, 5]) == 9
        assert f([]) == 0
        assert f([3]) == 0
        assert f([3, 3, 3]) == 0
        assert f([2, 0, 2]) == 2
    rng = random.Random(22)
    for _ in range(3000):
        h = [rng.randrange(5) for _ in range(rng.randrange(12))]
        expected = trap_brute(h)
        assert trap_prefix(h) == trap_stack(h) == trap_two_pointers(h) == expected, h


if __name__ == "__main__":
    main()
```

All three fast methods are `O(n)` time. Two pointers needs `O(1)` extra space, the other two `O(n)`. The stack method is still worth knowing: it only looks left, so it works when bars arrive one at a time, and its "floor, left wall, right wall" step is the shape of the histogram rectangle in [Contributions and Boundaries](05-contributions-and-boundaries.md). Equal heights are harmless: a floor with an equal left wall has depth 0.

## 4. The 132 pattern

**Problem.** Is there a triple of indices `i < j < k` with `nums[i] < nums[k] < nums[j]`? Read the values as "1", "3", "2": the first is the smallest, the middle is the largest, the last is in between.

| `nums` | Answer | Witness |
|---|---|---|
| `[1, 2, 3, 4]` | no | |
| `[3, 1, 4, 2]` | yes | `1, 4, 2` |
| `[-1, 3, 2, 0]` | yes | `-1, 3, 2` (also `-1, 3, 0` and `-1, 2, 0`) |

**Brute force.** Three nested loops, `O(n³)`; the prefix minimum as the best "1" for each `j` gives `O(n²)`.

### The key observation: scan from the right, keep the best "2"

Scan right to left. At each position, ask: "could this element be the '1'?" It can if some pair `j < k` to its right forms a "32" (that is, `nums[j] > nums[k]`) with `nums[k]` larger than it. Among all such "2" values, only the **largest** matters: call it `third`. The test is then `nums[i] < third`.

How do we keep `third` up to date? Keep a stack of elements seen so far (to the right) that could still serve as a "3". When a new element `x` arrives, every stacked value smaller than `x` has `x` to its left and bigger: `x` is a "3" for it, so it becomes a candidate "2". Pop it and set `third` to it. Popping in order from the top (smallest first), the last value popped is the largest, so `third` takes the best value. The popped values are not needed as "3" anymore: `x` is larger and further left, so it dominates them.

The stack ends up nonincreasing from bottom to top, and every stacked value is larger than `third`.

### Worked trace

`nums = [-1, 3, 2, 0]`, right to left:

| `i` | `x` | `x < third`? | Pops (new `third`) | Stack after (bottom → top) |
|---:|---:|---|---|---|
| 3 | 0 | no (`third = −∞`) | — | `0` |
| 2 | 2 | no | `0` (`third = 0`) | `2` |
| 1 | 3 | no | `2` (`third = 2`) | `3` |
| 0 | −1 | **yes**: `−1 < 2` | | found |

The pattern found is `-1, 3, 2`: the `3` that popped the `2` is the "3".

```python
import math
import random


def has_132(nums: list[int]) -> bool:
    third = -math.inf          # largest value with a bigger value somewhere to its left (in the suffix)
    stack: list[int] = []      # nonincreasing bottom -> top, all > third
    for x in reversed(nums):
        if x < third:
            return True
        while stack and stack[-1] < x:
            third = stack.pop()
        stack.append(x)
    return False


def has_132_brute(nums: list[int]) -> bool:
    n = len(nums)
    return any(nums[i] < nums[k] < nums[j]
               for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n))


def main():
    assert not has_132([1, 2, 3, 4])
    assert has_132([3, 1, 4, 2])
    assert has_132([-1, 3, 2, 0])
    assert not has_132([])
    assert not has_132([1, 1, 1])
    assert not has_132([1, 2, 2])         # needs nums[k] < nums[j] strictly
    rng = random.Random(23)
    for _ in range(4000):
        nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(9))]
        assert has_132(nums) == has_132_brute(nums), nums


if __name__ == "__main__":
    main()
```

`O(n)` time and `O(n)` space. The strict pop `stack[-1] < x` matters: with `<=`, an equal pair would make `third` equal to a "3", and `[1, 2, 2]` would wrongly look like it has a strict "2" below its "3". Note also that `third` only grows: every value still on the stack is above it, so every later pop gives a larger value.

## 5. Car fleet: a stack of arrival times

**Problem.** Cars drive along a one-lane road toward a `target`. Car `i` starts at `position[i]` (all different) with constant `speed[i]`. A car cannot pass the car ahead: when it catches up, it slows down and they drive together as one **fleet**. A car that catches a fleet exactly at the target also joins it. How many fleets arrive?

`target = 12`, positions `[10, 8, 0, 5, 3]`, speeds `[2, 4, 1, 1, 3]`. The time each car would need **alone** is `(target − position) / speed`, shown in the trace below. The answer is 3: `{10, 8}` arrive together at time 1, `{5, 3}` at time 7, and `{0}` at time 12.

**Brute force.** Simulate with exact fractions: find the earliest moment some group catches the one directly ahead at or before the target, move everyone to that moment, merge, and repeat. That is up to `n` rounds of `O(n)` work.

### The key observation: only the fleet directly ahead matters

Process cars from the one **closest to the target** backward. A car can never arrive earlier than the fleet directly ahead of it, because it cannot pass. So:

- If its time alone is **at most** the arrival time of the fleet ahead, it catches that fleet at or before the target and joins it. It then arrives at the fleet's time.
- Otherwise it never catches up and leads a new, slower fleet.

Keep the fleets' arrival times on a stack. A new fleet is pushed only when its time is larger than the top, so times strictly increase from bottom to top, and the answer is the stack size.

| Car (position) | Time alone | Compared with top | Stack of fleet times after |
|---:|---:|---|---|
| 10 | 1 | empty: new fleet | `1` |
| 8 | 1 | `1 <= 1`: joins | `1` |
| 5 | 7 | `7 > 1`: new fleet | `1 7` |
| 3 | 3 | `3 <= 7`: joins | `1 7` |
| 0 | 12 | `12 > 7`: new fleet | `1 7 12` |

The car at 3 (time 3) catches the car at 5 and is slowed to time 7.

```python
import random
from fractions import Fraction


def car_fleet(target: int, position: list[int], speed: list[int]) -> int:
    if len(position) != len(speed) or len(set(position)) != len(position):
        raise ValueError("need distinct positions, one speed each")
    fleets: list[Fraction] = []                    # arrival times, strictly increasing
    for p, s in sorted(zip(position, speed), reverse=True):
        time = Fraction(target - p, s)             # exact: no float ties
        if not fleets or time > fleets[-1]:
            fleets.append(time)
    return len(fleets)


def car_fleet_simulate(target: int, position: list[int], speed: list[int]) -> int:
    """Exact event simulation: jump to the earliest catch-up at or before the target, merge."""
    groups = [[Fraction(p), v] for p, v in sorted(zip(position, speed), reverse=True)]
    while True:
        times = [(pa - pb) / (vb - va)                       # a ahead, b behind
                 for (pa, va), (pb, vb) in zip(groups, groups[1:])
                 if vb > va and pa + va * (pa - pb) / (vb - va) <= target]
        if not times:
            return len(groups)
        dt = min(times)
        for g in groups:
            g[0] += g[1] * dt
        merged = [groups[0]]
        for g in groups[1:]:
            if g[0] != merged[-1][0] or g[0] > target:       # same spot before the end: joins
                merged.append(g)
        groups = merged


def main():
    assert car_fleet(12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]) == 3
    assert car_fleet(10, [3], [3]) == 1
    assert car_fleet(100, [0, 2, 4], [4, 2, 1]) == 1
    assert car_fleet(10, [], []) == 0
    assert car_fleet(10, [0, 4], [2, 1]) == 1        # meet exactly at the target
    rng = random.Random(24)
    for _ in range(1500):
        target = rng.randrange(1, 20)
        n = rng.randrange(min(target, 7) + 1)
        position = rng.sample(range(target), n)
        speed = [rng.randrange(1, 6) for _ in range(n)]
        assert car_fleet(target, position, speed) == car_fleet_simulate(target, position, speed)


if __name__ == "__main__":
    main()
```

Sorting costs `O(n log n)`; the scan is `O(n)`; space `O(n)`. Only the top is ever read, so one variable holding the last fleet time would do; the stack keeps every fleet's time, which variants such as "when does each car arrive?" need.

**Exact times.** Equal times decide whether two cars form one fleet, so compare them exactly. A plain `(target − p) / s` happens to be safe for small integers (equal fractions such as `1/3` and `2/6` round to the same float), but `(target − p) * (1 / s)` or integers above `2**53` break it. `Fraction`, or cross-multiplying `(target − p1) · s2` against `(target − p2) · s1`, avoids the question.

## 6. Summary

Five problems, one loop. What differs is what the stack holds and what a pop proves:

| Problem | Scan | Stack holds | Pop when | A pop means |
|---|---|---|---|---|
| Remove `k` digits | left → right | digits kept so far | top `>` new digit and budget left | deleting the top makes the number smaller |
| Distinct letters | left → right | letters kept so far | top `>` new letter and top appears later | the top can be placed better later |
| Trapping water | left → right | bars without a taller right wall | top `<` new bar | the top is the floor of a pool, now closed |
| 132 pattern | right → left | candidate "3" values | top `<` new value | the top becomes a candidate "2" |
| Car fleet | nearest the target first | fleet arrival times | (never; join or push) | — |

## 7. Pitfalls and practice

1. `del stack[-k:]` or `stack[:-k]` with `k = 0`. The first deletes everything, the second keeps nothing. Guard with `if k`.
2. Forgetting to strip leading zeros, or returning `""` instead of `"0"`.
3. In the distinct-letters problem, popping a letter that never appears again, or forgetting to skip letters already on the stack.
4. In the stack water method, adding water when the stack is empty after popping the floor. There is no left wall.
5. In the two-pointer water method, comparing `h[l]` with `h[r]` but then using the wrong side's maximum. The rule "process the side with the smaller running maximum" is the one the proof supports.
6. Using `<=` in the 132 pop, which lets an equal value act as a strictly smaller "2".
7. Comparing car arrival times with rounded arithmetic. Equal times decide fleets, so compare them exactly.

Practice: remove k digits; remove duplicate letters; smallest subsequence of distinct characters; create maximum number; trapping rain water; 132 pattern; car fleet; car fleet II (collision times, scanning from the front with a stack); asteroid collision; make the string great; minimum add to make parentheses valid; score of parentheses.

Next: [Monotonic Deque](04-monotonic-deque.md).
