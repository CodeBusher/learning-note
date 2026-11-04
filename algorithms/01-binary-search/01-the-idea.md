# The Idea of Binary Search — Throw Away Half, Keep the Range Honest

## 1. Find a value in a sorted array

Return an index `i` with `a[i] == target`, or `-1` if `target` is not in the sorted list `a`.

```text
index:   0   1   2   3   4   5   6   7   8   9
a    : [ 2,  5,  8, 12, 16, 23, 38, 56, 72, 91]
```

For `target = 12` the answer is 3; for `target = 13` it is −1. Scanning left to right works, but it costs `n` comparisons and ignores the one thing we know: the list is sorted.

**The idea.** Compare `target` with the middle element `a[mid]`.

- `a[mid] < target`: every element at or left of `mid` is `≤ a[mid]`, so it is too small. Throw that whole left part away.
- `a[mid] > target`: every element at or right of `mid` is too big. Throw the right part away.
- `a[mid] == target`: done.

Each comparison removes about half of what is left. This array runs on through the whole chapter.

## 2. Keeping track of what is left

We need two numbers that describe the candidates still alive. This guide uses a **half-open range**: `lo` is the first live index and `hi` is **one past** the last one, so the live candidates are exactly the slice `a[lo:hi]`, written `[lo, hi)`.

```text
index:   0   1   2   3   4   5   6   7   8   9
a    : [ 2,  5,  8, 12, 16, 23, 38, 56, 72, 91]
         ^                   ^                   ^
         lo = 0              mid = 5             hi = 10 (not a candidate)
```

The search for 12:

| Step | `lo` | `hi` | Live `a[lo:hi]` | `mid` | `a[mid]` | Action |
|---:|---:|---:|---|---:|---:|---|
| 1 | 0 | 10 | `2 5 8 12 16 23 38 56 72 91` | 5 | 23 | 23 > 12: `hi = 5` |
| 2 | 0 | 5 | `2 5 8 12 16` | 2 | 8 | 8 < 12: `lo = 3` |
| 3 | 3 | 5 | `12 16` | 4 | 16 | 16 > 12: `hi = 4` |
| 4 | 3 | 4 | `12` | 3 | 12 | found: return 3 |

Two updates in this table deserve a closer look.

**`lo = mid + 1`, not `lo = mid`.** At step 2, `a[2] = 8` is too small, so index 2 itself is dead. The new first live index is `mid + 1`.

**`hi = mid`, not `hi = mid − 1`.** At step 1, `a[5] = 23` is too big, so index 5 is dead. Because `hi` already points *past* the last live index, `hi = 5` removes index 5 and keeps index 4. Writing `hi = mid − 1` would also throw away index 4, which could be the answer. This is the most common bug in half-open binary search.

## 3. Variant: the target is missing

Search for 13. Every comparison goes the same way as for 12, until step 4:

| Step | `lo` | `hi` | Live | `mid` | `a[mid]` | Action |
|---:|---:|---:|---|---:|---:|---|
| 4 | 3 | 4 | `12` | 3 | 12 | 12 < 13: `lo = 4` |
| 5 | 4 | 4 | (empty) | — | — | stop: return −1 |

When `lo == hi` the slice `a[lo:hi]` is empty: no candidate is left, so 13 is not in the list. That is the whole stopping rule: **loop while `lo < hi`**.

Why is it safe to conclude "not there"? Because one sentence stays true before every step:

> **Invariant:** if `target` is in `a`, it is in `a[lo:hi]`.

It holds at the start, when `a[lo:hi]` is the whole list. Each update only removes indexes we proved dead in §2. So when the range is empty, the target can't be anywhere.

**Why the loop always ends.** The midpoint `mid = lo + (hi − lo) // 2` satisfies `lo ≤ mid < hi`. So `lo = mid + 1` strictly raises `lo`, and `hi = mid` strictly lowers `hi`. The range shrinks every step.

## 4. Variant: the edges

The same loop handles every edge case without special code. It's worth checking each once, because these are where hand-written searches fail:

| Input | What happens |
|---|---|
| `a = []` | `lo = hi = 0`, the loop never runs, return −1. |
| `a = [5]`, `target = 5` | `mid = 0`, found. |
| `target = 2` (first element) | `hi` keeps shrinking to the left until `mid = 0`. |
| `target = 91` (last element) | `lo` keeps moving right; `mid` reaches 9 because `mid < hi = 10` always. |
| `target = 1` or `100` (outside the values) | The range empties at the left end or the right end, return −1. |

## 5. Variant: duplicates

```text
index:  0  1  2  3  4
a    : [1, 2, 2, 2, 3]
```

Search for 2: the first `mid` is 2, and `a[2] == 2`, so the search returns 2, not the first copy at index 1. With duplicates this search returns **some** matching index. "Where is the first 2?" and "how many 2s?" are different questions with their own searches in [Boundaries](02-boundaries.md).

Here is the search, tested against a linear scan on random sorted lists (duplicates included). The fixed seed makes every run test the same lists, so a failure can be reproduced.

```python
import random


def binary_search(a: list[int], target: int) -> int:
    """Return an index i with a[i] == target, or -1. The list must be sorted."""
    lo, hi = 0, len(a)  # Invariant: if target is in a, it is in a[lo:hi].
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] == target:
            return mid
        if a[mid] < target:
            lo = mid + 1  # a[lo..mid] are all too small.
        else:
            hi = mid  # a[mid..hi-1] are all too big.
    return -1


def main():
    a = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
    assert binary_search(a, 12) == 3
    assert binary_search(a, 13) == -1
    assert binary_search(a, 2) == 0
    assert binary_search(a, 91) == 9
    assert binary_search(a, 1) == -1 and binary_search(a, 100) == -1
    assert binary_search([], 5) == -1
    assert binary_search([5], 5) == 0
    assert binary_search([1, 2, 2, 2, 3], 2) == 2  # Some copy, not the first.

    rng = random.Random(1)
    for _ in range(3000):
        a = sorted(rng.randint(-10, 10) for _ in range(rng.randint(0, 12)))
        target = rng.randint(-12, 12)
        i = binary_search(a, target)
        if target in a:
            assert 0 <= i < len(a) and a[i] == target
        else:
            assert i == -1


if __name__ == "__main__":
    main()
```

**Time:** O(log n) comparisons. **Space:** O(1).

## 6. Variant: the closed range `[lo, hi]`

Many textbooks keep both ends live: the candidates are `a[lo..hi]`, both included. Only three lines change, and each change follows from "`hi` is now a live index":

```python
def binary_search_closed(a: list[int], target: int) -> int:
    lo, hi = 0, len(a) - 1  # hi is the last live index.
    while lo <= hi:  # lo == hi is one live candidate, not an empty range.
        mid = lo + (hi - lo) // 2
        if a[mid] == target:
            return mid
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1  # hi is live, so step past the dead mid.
    return -1


def main():
    a = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
    for i, value in enumerate(a):
        assert binary_search_closed(a, value) == i
    assert binary_search_closed(a, 13) == -1
    assert binary_search_closed([], 5) == -1


if __name__ == "__main__":
    main()
```

Both styles are correct on their own. Bugs come from mixing them, for example `while lo <= hi` with `hi = mid`: once `lo == hi == mid` and `a[mid] > target`, nothing changes and the loop never ends. This guide uses half-open ranges everywhere, because they match Python slices and `range`, and because the boundary searches of the next chapter end at a single answer, `lo == hi`.

## 7. Variant: change one line and it breaks

Two one-line changes that look harmless are behind most real binary-search bugs.

**`(lo + hi) // 2` overflows in fixed-width languages.** In Python the two midpoint formulas are equal. In Java, C, C++ or Go, a 32-bit `int` stops at 2,147,483,647. With `lo = 1,500,000,000` and `hi = 2,000,000,000` (common when [searching on the answer](03-search-on-the-answer.md)), `lo + hi` wraps around to a negative number and `mid` becomes a negative index. `lo + (hi − lo) // 2` never builds a value larger than `hi`, so it is always safe. This bug sat in Java's own `Arrays.binarySearch` until 2006.

**`lo = mid` can loop forever.** Suppose you want the last index with `a[i] ≤ 4` in `[1, 3, 5]` and write `if a[mid] <= 4: lo = mid` on a closed range. At `lo = 1, hi = 2`, the rounded-down midpoint is `mid = 1 = lo`, so `lo = mid` changes nothing, every step. The rule: a branch that sets `lo = mid` needs a midpoint that rounds **up**. The simpler fix, used in the next chapter, is to never write `lo = mid`: search for the first index with `a[i] > 4` and subtract 1.

```python
def to_int32(value: int) -> int:
    """Wrap an exact integer the way a 32-bit int does."""
    return (value + 2**31) % 2**32 - 2**31


def last_at_most(a: list[int], x: int, max_steps: int = 50) -> int:
    """The broken version: lo = mid with a rounded-down midpoint."""
    lo, hi = 0, len(a) - 1
    for _ in range(max_steps):
        if lo >= hi:
            return lo
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid
        else:
            hi = mid - 1
    raise RuntimeError("stuck: lo = mid did not move")


def main():
    lo, hi = 1_500_000_000, 2_000_000_000
    assert to_int32(lo + hi) // 2 < 0  # Overflow: a negative index.
    assert lo + to_int32(hi - lo) // 2 == 1_750_000_000

    try:
        last_at_most([1, 3, 5], 4)
        raise AssertionError("expected the search to get stuck")
    except RuntimeError:
        pass


if __name__ == "__main__":
    main()
```

## 8. Summary

**The template** (half-open):

```text
lo, hi = 0, len(a)              # live candidates: a[lo:hi]
while lo < hi:                  # stop when the range is empty
    mid = lo + (hi - lo) // 2   # lo <= mid < hi, no overflow
    if a[mid] is the answer: return mid
    if mid and everything left of it is dead:  lo = mid + 1
    else (mid and everything right is dead):   hi = mid
```

**The invariant** that justifies every line: *if the answer exists, it is in `a[lo:hi]`*. Write it down before writing the loop.

**Half-open vs closed:**

| | Half-open `[lo, hi)` | Closed `[lo, hi]` |
|---|---|---|
| Start | `hi = n` | `hi = n − 1` |
| Loop while | `lo < hi` | `lo <= hi` |
| Drop the right part | `hi = mid` | `hi = mid − 1` |
| Drop the left part | `lo = mid + 1` | `lo = mid + 1` |
| Empty range | `lo == hi` | `lo == hi + 1` |

**How many steps.** Each step at least halves the live range, so a list of `n` elements takes at most ⌊log₂ n⌋ + 1 steps: 10 for a thousand elements, 20 for a million, 30 for a billion.

## 9. Pitfalls and practice

1. **The list isn't sorted.** Binary search returns wrong answers silently.
2. **`hi = mid − 1` in a half-open search.** It discards a live candidate (§2).
3. **Mixing closed and half-open lines.** Keep the start, the condition and both updates from one column of the table (§6).
4. **`(lo + hi) / 2` in a fixed-width language.** Overflow for large ranges (§7).
5. **`lo = mid` with a rounded-down midpoint.** An infinite loop when `hi = lo + 1` (§7).
6. **Expecting the first copy.** With duplicates, the plain search returns any matching index (§5).

Practice: binary search on a sorted array; guess number higher or lower; first bad version; search insert position; sqrt(x). Write the invariant sentence before each loop.

Next: [Boundaries](02-boundaries.md).
