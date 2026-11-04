# Counting and Frequency Windows — Count Every Window, Track Every Letter

## 1. Counting windows: subarrays with product less than `k`

You get a list of positive integers and a number `k`. Count the windows (nonempty runs of consecutive elements) whose product is less than `k`.

```text
index     0   1   2   3
nums     10   5   2   6      k = 100
```

The answer is 8. The windows are `[10]`, `[5]`, `[2]`, `[6]`, `[10, 5]`, `[5, 2]`, `[2, 6]`, and `[5, 2, 6]`. The window `[10, 5, 2]` has product exactly 100, which is not less than 100.

**Brute force.** For each `left`, multiply forward while the product stays below `k`: `O(n²)` in the worst case, for example when every value is 1.

### The key observation: count every start at once

All values are at least 1, so validity is monotone in the "longest" direction of [Fixed and Variable Windows](02-fixed-and-variable-windows.md#5-the-two-templates-side-by-side): extending a window cannot lower its product, and shortening it cannot raise it. Run the longest-window template. After the `while` loop, `[left, right]` is the longest valid window ending at `right`.

Now look at the shorter windows that end at the same `right`:

```text
[left, right], [left + 1, right], ..., [right, right]
```

Each one is a part of the valid window `[left, right]`, so each is valid too. Every window that starts before `left` was removed because it was invalid. So **exactly `right - left + 1` valid windows end at `right`**. Adding that number for each `right` counts every valid window exactly once, since every window has exactly one right end.

**State:** `product` is the product of `nums[left..right]`.

```text
index       0   1   2   3
nums       10   5   2   6      k = 100

right=0   [10]  5   2   6     multiply 10: product  10           +1   total 1
right=1   [10   5]  2   6     multiply  5: product  50           +2   total 3
right=2    10 [ 5   2]  6     multiply  2: product 100 >= 100;
                              divide by 10: product 10           +2   total 5
right=3    10 [ 5   2   6]    multiply  6: product  60           +3   total 8
```

At `right = 3`, the three windows ending at 3 are `[6]`, `[2, 6]`, and `[5, 2, 6]`.

```python
from math import prod
from random import Random


def count_product_below(nums: list[int], k: int) -> int:
    """Count nonempty windows whose product is < k. nums are positive ints."""
    if any(value < 1 for value in nums):
        raise ValueError("nums must be positive integers")
    if k <= 1:
        return 0                     # every product is at least 1
    left = 0
    product = 1
    count = 0
    for right, value in enumerate(nums):
        product *= value
        while product >= k:
            product //= nums[left]   # exact: nums[left] divides the product
            left += 1
        count += right - left + 1
    return count


def count_product_below_brute(nums, k):
    return sum(prod(nums[l:r + 1]) < k
               for l in range(len(nums)) for r in range(l, len(nums)))


def main():
    assert count_product_below([10, 5, 2, 6], 100) == 8
    assert count_product_below([1, 2, 3], 0) == 0
    assert count_product_below([1, 1, 1], 2) == 6
    assert count_product_below([], 5) == 0
    assert count_product_below([7], 7) == 0

    rng = Random(20)
    for _ in range(1000):
        nums = [rng.randrange(1, 6) for _ in range(rng.randrange(9))]
        k = rng.randrange(0, 40)
        assert count_product_below(nums, k) == count_product_below_brute(nums, k)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` multiplications and divisions. **Space:** `O(1)`.

**Why `k <= 1` returns early.** Every product is at least 1, so no window has a product below 1. Without the check, the `while` loop would divide `product` down to 1 and then keep moving `left` past `right`, because `1 >= k` is still true.

**Large products.** The loop shrinks as soon as the product reaches `k`, so it stays below `k · max(nums)`. Python cannot overflow anyway, but in fixed-width languages that bound keeps the arithmetic safe. Summing logarithms instead avoids overflow but brings floating-point rounding at the boundary.

## 2. Exactly `k`: subtract two "at most" counts

Count the windows with **exactly** `k` distinct values.

```text
index    0  1  2  3  4
nums     1  2  1  2  3      k = 2
```

The answer is 7: `[1,2]`, `[2,1]`, `[1,2]`, `[2,3]`, `[1,2,1]`, `[2,1,2]`, and `[1,2,1,2]`.

### Why a single window fails

The trick in §1 needed the valid windows ending at `right` to form one block that reaches all the way to `right`. For "exactly 2 distinct", they do not. At `right = 3`:

| Start | Window | Distinct | Exactly 2? |
|---:|---|---:|---|
| 0 | `1 2 1 2` | 2 | yes |
| 1 | `2 1 2` | 2 | yes |
| 2 | `1 2` | 2 | yes |
| 3 | `2` | 1 | no |

Starts 0 to 2 are valid, but the shortest window `[3, 3]` is not. Shrinking can make an "exactly 2" window **invalid** by dropping below 2. The condition is not monotone, so there is no single `left` to maintain.

**The observation.** "At most `k` distinct" **is** monotone, and §1 already counts it. Every window with at most `k` distinct values has either at most `k - 1`, or exactly `k`. These two groups do not overlap. So

$$
\#\{\text{exactly }k\} \;=\; \#\{\text{at most }k\} \;-\; \#\{\text{at most }k-1\}.
$$

For each `right`, the table shows how many windows ending at `right` have at most 2 and at most 1 distinct values:

```text
index        0  1  2  3  4
nums         1  2  1  2  3

at most 2   [1] .  .  .  .     left=0  ->  1 window
            [1  2] .  .  .     left=0  ->  2
            [1  2  1] .  .     left=0  ->  3
            [1  2  1  2] .     left=0  ->  4
             1  2  1 [2  3]    left=3  ->  2           total 12

at most 1   each window is one element: left = right, 1 per step     total 5
```

Dots mark positions the scan has not reached yet. Exactly 2 distinct: `12 - 5 = 7`.

The same subtraction counts windows whose **sum is exactly** a target when the values are nonnegative integers: windows with sum at most `target`, minus those with sum at most `target - 1`. With zeros present, many windows can share the same sum, which is why a single "find one window" scan cannot count them.

```python
from random import Random


def count_at_most_distinct(nums, k: int) -> int:
    """Count nonempty windows with at most k distinct values."""
    if k < 0:
        return 0
    counts = {}
    left = total = 0
    for right, value in enumerate(nums):
        counts[value] = counts.get(value, 0) + 1
        while len(counts) > k:
            outgoing = nums[left]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                del counts[outgoing]
            left += 1
        total += right - left + 1
    return total


def count_exactly_distinct(nums, k: int) -> int:
    """Count nonempty windows with exactly k distinct values."""
    if k <= 0:
        return 0                     # every nonempty window has >= 1 value
    return count_at_most_distinct(nums, k) - count_at_most_distinct(nums, k - 1)


def count_exact_sum_nonnegative(nums: list[int], target: int) -> int:
    """Count nonempty windows with sum == target. nums are nonnegative ints."""
    if any(value < 0 for value in nums):
        raise ValueError("nums must be nonnegative")

    def at_most(limit: int) -> int:
        if limit < 0:
            return 0
        left = running = total = 0
        for right, value in enumerate(nums):
            running += value
            while running > limit:
                running -= nums[left]
                left += 1
            total += right - left + 1
        return total

    return at_most(target) - at_most(target - 1)


def windows(nums):
    for left in range(len(nums)):
        for right in range(left, len(nums)):
            yield nums[left:right + 1]


def main():
    assert count_at_most_distinct([1, 2, 1, 2, 3], 2) == 12
    assert count_at_most_distinct([1, 2, 1, 2, 3], 1) == 5
    assert count_exactly_distinct([1, 2, 1, 2, 3], 2) == 7
    assert count_exactly_distinct([1, 1, 1], 1) == 6
    assert count_exactly_distinct([], 1) == 0
    assert count_exactly_distinct([1], 0) == 0
    assert count_exact_sum_nonnegative([1, 0, 1, 0, 1], 2) == 4
    assert count_exact_sum_nonnegative([0, 0, 0], 0) == 6
    assert count_exact_sum_nonnegative([1], -1) == 0

    rng = Random(21)
    for _ in range(1000):
        nums = [rng.randrange(4) for _ in range(rng.randrange(9))]
        k = rng.randrange(-1, 5)
        assert count_exactly_distinct(nums, k) == \
            sum(len(set(w)) == k for w in windows(nums))
        target = rng.randrange(-1, 8)
        assert count_exact_sum_nonnegative(nums, target) == \
            sum(sum(w) == target for w in windows(nums))


if __name__ == "__main__":
    main()
```

**Time:** two linear scans, `O(n)` expected. **Space:** `O(k)` for the distinct counts, `O(1)` for the sums.

**The subtraction is a counting identity, not a window trick.** It works for any whole-number measure (distinct values, sum of nonnegative integers, number of odd values, number of vowels) whenever "at most" can be counted. It does **not** make a non-monotone condition monotone. With negative numbers, "sum at most `g`" is not monotone, and [Advanced Window Patterns](04-advanced-patterns.md) counts exact sums with prefix sums instead.

## 3. Find all anagrams: a fixed window of letter counts

An **anagram** of a word is a rearrangement of its letters: `bca` and `cab` are anagrams of `abc`. Given `text` and `pattern`, list every start position in `text` where an anagram of `pattern` begins. (Checking whether at least one exists is the "permutation in string" problem.)

```text
index    0  1  2  3  4  5  6  7  8  9
text     c  b  a  e  b  a  b  a  c  d      pattern = abc
```

The answer is `[0, 6]`: `cba` at 0 and `bac` at 6.

**Brute force.** For each of the `n - m + 1` starts, sort the window and compare it with the sorted pattern, where `m` is the pattern length: `O(n · m log m)`. Building a letter count for each window instead costs `O(n · m)`.

**The key observation.** An anagram has the same length as the pattern, so this is a **fixed-size** window of width `m`, as in [the fixed-size window](02-fixed-and-variable-windows.md#1-a-fixed-size-window-the-largest-sum-of-k-neighbors). Its state is a table of letter counts instead of a sum. Moving the window changes only two counts: one for the letter entering and one for the letter leaving.

Comparing two whole count tables after each move costs one step per distinct letter of the alphabet. A single number makes each step `O(1)`:

**State:** `have[c]` counts each pattern letter `c` inside the window, and

$$
\text{missing}=\sum_{c}\max\bigl(\text{need}[c]-\text{have}[c],\,0\bigr),
$$

the number of pattern letters (with repeats) that the window still lacks.

- When a letter enters and its count was **below** what the pattern needs, it fills a gap: `missing -= 1`. An extra copy beyond the need changes nothing.
- When a letter leaves and its count drops **below** the need, it opens a gap: `missing += 1`.

A window of exactly `m` letters with `missing == 0` contains every needed letter at least as often as needed. Those needed letters already add up to `m`, so there is no room for anything else: the window is an anagram.

```text
index      0  1  2  3  4  5  6  7  8  9
text       c  b  a  e  b  a  b  a  c  d      pattern = abc, m = 3

right=0-1 [c  b] a  e  b  a  b  a  c  d     add c, b                 missing 1
right=2   [c  b  a] e  b  a  b  a  c  d     add a                    missing 0   anagram at 0
right=3    c [b  a  e] b  a  b  a  c  d     add e, drop c            missing 1
right=4-5  e stays inside; each step adds and drops the same letter   missing 1
right=6    c  b  a  e [b  a  b] a  c  d     add b (extra), drop e    missing 1
right=7    c  b  a  e  b [a  b  a] c  d     add a (extra), drop b    missing 1
right=8    c  b  a  e  b  a [b  a  c] d     add c, drop a            missing 0   anagram at 6
right=9    c  b  a  e  b  a  b [a  c  d]    add d, drop b            missing 1
```

At `right = 6` the window `bab` has two `b`s. The second `b` was extra, so `missing` stayed at 1 (the `c` is still absent). At `right = 8`, the `a` at position 5 leaves, but the `a` at position 7 is still inside, so the drop opens no gap.

```python
from collections import Counter
from random import Random


def anagram_starts(text: str, pattern: str) -> list[int]:
    """Start positions of anagrams of pattern in text. Empty pattern -> []."""
    width = len(pattern)
    if width == 0 or width > len(text):
        return []
    need = Counter(pattern)
    have = dict.fromkeys(need, 0)
    missing = width
    starts = []
    for right, char in enumerate(text):
        if char in need:
            if have[char] < need[char]:
                missing -= 1
            have[char] += 1
        if right >= width:                        # one letter leaves
            outgoing = text[right - width]
            if outgoing in need:
                have[outgoing] -= 1
                if have[outgoing] < need[outgoing]:
                    missing += 1
        if right >= width - 1 and missing == 0:
            starts.append(right - width + 1)
    return starts


def contains_permutation(text: str, pattern: str) -> bool:
    return bool(anagram_starts(text, pattern))


def anagram_starts_brute(text, pattern):
    width = len(pattern)
    if width == 0:
        return []
    target = sorted(pattern)
    return [start for start in range(len(text) - width + 1)
            if sorted(text[start:start + width]) == target]


def main():
    assert anagram_starts("cbaebabacd", "abc") == [0, 6]
    assert anagram_starts("abab", "ab") == [0, 1, 2]
    assert anagram_starts("baa", "aa") == [1]
    assert anagram_starts("abc", "") == []
    assert anagram_starts("a", "aa") == []
    assert contains_permutation("eidbaooo", "ab")
    assert not contains_permutation("eidboaoo", "ab")

    rng = Random(22)
    for _ in range(1000):
        text = "".join(rng.choice("abc") for _ in range(rng.randrange(10)))
        pattern = "".join(rng.choice("abc") for _ in range(rng.randrange(4)))
        assert anagram_starts(text, pattern) == anagram_starts_brute(text, pattern)


if __name__ == "__main__":
    main()
```

**Time:** `O(n + m)` expected for text length `n` and pattern length `m`. **Space:** `O(d)` for the `d` distinct pattern letters, plus the output.

## 4. Minimum window substring: the shortest cover

Given `text` and `pattern`, find the shortest substring of `text` that contains every letter of `pattern`, **with repeats**: for pattern `AABC`, the substring needs at least two `A`s. Letters not in the pattern are allowed. If several shortest substrings exist, return the leftmost; if none exists, return `""`.

For `text = "ADOBECODEBANC"` and `pattern = "ABC"`, the answer is `"BANC"`.

**Brute force.** Check every one of the `O(n²)` windows for coverage.

**The key observation.** Call a window **covering** if `missing == 0`. Coverage is monotone in the "shortest" direction of [the shortest-window template](02-fixed-and-variable-windows.md#4-the-shortest-window-that-reaches-a-total): adding letters cannot lose coverage, and removing letters cannot create it. So use the shortest-window template: extend `right`; while the window covers, record it and remove `text[left]`. The `missing` counter from §3 makes the coverage test `O(1)`.

Steps that only grow the window are grouped; every shrink is shown.

```text
index      0   1   2   3   4   5   6   7   8   9  10  11  12
text       A   D   O   B   E   C   O   D   E   B   A   N   C      pattern = ABC

right=0-4  add A D O B E: A and B fill gaps                           missing 1
right=5   [A   D   O   B   E   C]  O   D   E   B   A   N   C         missing 0
           record ADOBEC (6), best 6; drop A -> missing 1, stop
right=6-9  add O D E B: the second B is extra                         missing 1
right=10   A  [D   O   B   E   C   O   D   E   B   A]  N   C         missing 0
           record 10, drop D; record 9, drop O
           record 8, drop B: another B is inside, missing stays 0
           record 7, drop E; record CODEBA (6), not shorter
           drop C -> missing 1, stop
right=11   add N                                                      missing 1
right=12   A   D   O   B   E   C  [O   D   E   B   A   N   C]         missing 0
           record 7, drop O; record 6, drop D
           record EBANC (5), best 5, drop E
           record BANC (4), best 4, drop B -> missing 1, stop
```

Final answer: `"BANC"`.

### Repeated letters in the pattern

For `pattern = "AABC"` and `text = "ABAACBAB"`, `missing` starts at 4:

| `right` | Letter | `have` (A, B, C) | `missing` | Note |
|---:|---|---|---:|---|
| 0 | A | 1, 0, 0 | 3 | first A fills a gap |
| 1 | B | 1, 1, 0 | 2 | |
| 2 | A | 2, 1, 0 | 1 | second A fills the second A gap |
| 3 | A | 3, 1, 0 | 1 | third A is extra: no change |
| 4 | C | 3, 1, 1 | 0 | covers `ABAAC`; record 5 |
| | drop A | 2, 1, 1 | 0 | two As are still enough; record `BAAC` (4) |
| | drop B | 2, 0, 1 | 1 | B gap opens; stop shrinking |

Using a **set** of pattern letters would lose the "two As" requirement. That is why `need` is a `Counter`.

**Variant: counting covers.** To count substrings that contain every needed letter, count the **left ends that still cover**. After the `while` loop ends at a given `right`, every start in `0 .. left - 1` gave a covering window `[start, right]` (each was recorded and dropped while covering, and covering windows stay covering when extended right). So `left` windows ending at `right` cover. Adding `left` for each `right` counts them all; this solves "number of substrings containing all three characters".

```python
from collections import Counter
from random import Random


def minimum_cover(text: str, pattern: str) -> str:
    """Shortest substring of text containing pattern's letters with repeats.

    Earliest start wins ties. Empty pattern or no cover returns "".
    """
    if not pattern:
        return ""
    need = Counter(pattern)
    have = dict.fromkeys(need, 0)
    missing = len(pattern)
    left = 0
    best_left, best_length = 0, len(text) + 1
    for right, char in enumerate(text):
        if char in need:
            if have[char] < need[char]:
                missing -= 1
            have[char] += 1
        while missing == 0:
            if right - left + 1 < best_length:
                best_left, best_length = left, right - left + 1
            outgoing = text[left]
            if outgoing in need:
                have[outgoing] -= 1
                if have[outgoing] < need[outgoing]:
                    missing += 1
            left += 1
    if best_length > len(text):
        return ""
    return text[best_left:best_left + best_length]


def count_covering(text: str, pattern: str) -> int:
    """Count substrings of text that contain pattern's letters with repeats."""
    if not pattern:
        raise ValueError("pattern must be nonempty")
    need = Counter(pattern)
    have = dict.fromkeys(need, 0)
    missing = len(pattern)
    left = total = 0
    for right, char in enumerate(text):
        if char in need:
            if have[char] < need[char]:
                missing -= 1
            have[char] += 1
        while missing == 0:
            outgoing = text[left]
            if outgoing in need:
                have[outgoing] -= 1
                if have[outgoing] < need[outgoing]:
                    missing += 1
            left += 1
        total += left          # starts 0 .. left-1 all cover with this right
    return total


def covers_brute(text, pattern):
    """All covering substrings, shortest first, then leftmost."""
    need = Counter(pattern)
    return [text[s:s + n] for n in range(1, len(text) + 1)
            for s in range(len(text) - n + 1) if Counter(text[s:s + n]) >= need]


def main():
    assert minimum_cover("ADOBECODEBANC", "ABC") == "BANC"
    assert minimum_cover("ABAACBAB", "AABC") == "BAAC"
    assert minimum_cover("a", "aa") == ""
    assert minimum_cover("anything", "") == ""
    assert minimum_cover("", "A") == ""
    assert count_covering("abcabc", "abc") == 10
    assert count_covering("aaacb", "abc") == 3
    assert count_covering("abc", "aa") == 0

    rng = Random(23)
    for _ in range(1000):
        text = "".join(rng.choice("abcd") for _ in range(rng.randrange(10)))
        pattern = "".join(rng.choice("abc") for _ in range(rng.randrange(4)))
        covers = covers_brute(text, pattern) if pattern else []
        assert minimum_cover(text, pattern) == (covers[0] if covers else "")
        if pattern:
            assert count_covering(text, pattern) == len(covers)


if __name__ == "__main__":
    main()
```

**Time:** `O(n + m)` expected for both functions. **Space:** `O(d)` for the distinct pattern letters, plus the returned substring. Letters outside the pattern never enter `have`, so the dictionary stays small even when the text uses many other characters.

### Why it's correct

`missing` always equals the formula above, so `missing == 0` means the window covers the pattern. While the window covers, the code records it before dropping `text[left]`; every later covering window with the same `left` is longer, so that start is finished. When the window stops covering, every shorter window ending at `right` also fails to cover, so the only useful move is to extend `right`. Every start is dropped only after its shortest cover has been recorded.

## 5. Pitfalls and practice

1. **Zero counts left in the dictionary** when `len(counts)` is used as the number of distinct values.
2. **Treating "exactly `k`" as a window condition.** It is not monotone; subtract two "at most" counts.
3. **Using a set for the pattern.** Repeated letters in the pattern need a count, not membership.
4. **Updating `missing` on every letter.** Only letters that fill or open a gap change it; extra copies do not.
5. **Forgetting `k <= 1`** in the product count, which makes `left` run past `right`.
6. **Empty pattern contracts.** The code above returns `""` for the minimum cover and `[]` for the anagram starts. State your contract.
7. **Counter width.** The number of windows grows like `n² / 2`; use 64-bit integers outside Python.

Practice: Subarray Product Less Than K; Subarrays with K Different Integers; Binary Subarrays With Sum; Count Number of Nice Subarrays; Count Vowel Substrings of a String; Number of Substrings Containing All Three Characters; Find All Anagrams in a String; Permutation in String; Minimum Window Substring; Substring with Concatenation of All Words (a frequency window over words).

Next: [Advanced Window Patterns](04-advanced-patterns.md).
