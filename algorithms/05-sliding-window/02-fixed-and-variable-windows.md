# Fixed and Variable Windows — Why the Left End Never Moves Back

## 1. A fixed-size window: the largest sum of `k` neighbors

A **window** is a stretch of consecutive positions, written `[left, right]` with both ends included; its length is `right - left + 1`. You get a list of numbers and a length `k`. Find the largest sum among all windows of exactly `k` numbers.

```text
index    0  1  2  3  4  5
nums     2  1  5  1  3  2      k = 3
```

The four windows of length 3 have sums 8, 7, 9 and 6, so the answer is 9, from `[2, 4]`. As a Python slice that window is `nums[2:5]`, because a slice leaves out its end.

**Brute force.** Add up each of the `n - k + 1` windows from scratch, `k` additions each: about 2.5 billion additions for `n = 100,000` and `k = 50,000`.

**The key observation.** Two neighboring windows share all but two elements:

```text
index    0  1  2  3  4  5
nums     2  1  5  1  3  2
        [2  1  5]              sum 8
            [1  5  1]          shares 1 and 5; loses 2, gains 1
```

So the next sum is the old sum, minus the element that leaves on the left, plus the element that enters on the right:

$$
\text{sum}[left+1,\ right+1]=\text{sum}[left,\ right]-nums[left]+nums[right+1].
$$

That is two operations per step instead of `k`.

**State:** `running` is the sum of the current window.

The brackets show the window over the array:

```text
index      0  1  2  3  4  5
nums       2  1  5  1  3  2

start     [2  1  5] 1  3  2     sum 8                 best 8
right=3    2 [1  5  1] 3  2     +1 -2  ->  sum 7      best 8
right=4    2  1 [5  1  3] 2     +3 -1  ->  sum 9      best 9
right=5    2  1  5 [1  3  2]    +2 -5  ->  sum 6      best 9
```

```python
from random import Random


def max_sum_fixed(nums: list[int], k: int) -> tuple[int, int, int]:
    """Return (best_sum, left, right) over windows of exactly k elements.

    Require 1 <= k <= len(nums). Endpoints are inclusive; the earliest
    window wins ties.
    """
    if not 1 <= k <= len(nums):
        raise ValueError("k must be between 1 and len(nums)")
    running = sum(nums[index] for index in range(k))
    best_sum, best_left = running, 0
    for right in range(k, len(nums)):
        running += nums[right] - nums[right - k]
        if running > best_sum:
            best_sum, best_left = running, right - k + 1
    return best_sum, best_left, best_left + k - 1


def max_sum_fixed_brute(nums, k):
    total, neg_left = max((sum(nums[i:i + k]), -i) for i in range(len(nums) - k + 1))
    return total, -neg_left, -neg_left + k - 1      # earliest window on ties


def main():
    assert max_sum_fixed([2, 1, 5, 1, 3, 2], 3) == (9, 2, 4)
    assert max_sum_fixed([-4, -2, -7], 2) == (-6, 0, 1)   # all negative
    assert max_sum_fixed([5, 5], 1) == (5, 0, 0)          # tie: earliest
    assert max_sum_fixed([3], 1) == (3, 0, 0)             # one element
    for bad in ([], 0), ([1, 2], 3):
        try:
            max_sum_fixed(*bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = Random(10)
    for _ in range(500):
        nums = [rng.randrange(-9, 10) for _ in range(rng.randrange(1, 10))]
        k = rng.randrange(1, len(nums) + 1)
        assert max_sum_fixed(nums, k) == max_sum_fixed_brute(nums, k)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` for `n` elements. **Space:** `O(1)`.

**Why it's correct.** Before the loop, `running` is the sum of the first window. Each step removes the one element that leaves and adds the one that enters, so `running` is always the sum of the current window. Every window of length `k` is visited exactly once, and `best_sum` keeps the largest.

Negative numbers cause no trouble here. The window length alone decides which element leaves; the values never influence how the pointers move. That will not be true for the variable-size windows below.

**Variants.** The largest *average* of `k` neighbors is the largest sum divided by `k`, since every window has the same length. Counting windows whose average is at least a threshold uses the same `running` sum. A fixed window can also carry a frequency table instead of a sum; [Counting and Frequency Windows](03-counting-and-frequency-windows.md#3-find-all-anagrams-a-fixed-window-of-letter-counts) uses that to find anagrams.

## 2. A variable-size window: the longest substring without repeats

Now the window length is not given. Find the length of the longest substring of `text` in which no character appears twice.

```text
index    0  1  2  3  4  5  6  7
text     a  b  c  a  b  c  b  b
```

The answer is 3, for example `"abc"` at `[0, 2]`. No substring of length 4 works.

**Brute force.** For each `left`, grow the window one character at a time and stop at the first repeat: `O(n²)`, about 5 billion steps for `n = 100,000`.

### The key observation: validity is monotone

Call a window **valid** if it has no repeated character. Draw every window in a grid, with `left` down the side and `right` across the top. `V` means valid and `x` means invalid:

```text
                 right   0  1  2  3  4  5  6  7
left 0   (a)             V  V  V  x  x  x  x  x
left 1   (b)                V  V  V  x  x  x  x
left 2   (c)                   V  V  V  x  x  x
left 3   (a)                      V  V  V  x  x
left 4   (b)                         V  V  x  x
left 5   (c)                            V  V  x
left 6   (b)                               V  x
left 7   (b)                                  V
```

Two facts explain the shape of this grid:

1. **Making an invalid window longer keeps it invalid.** If `[left, right]` has a repeated character, then `[left, right + 1]` contains the same repeat. So in each row, once an `x` appears, every cell to its right is `x`.
2. **Making a valid window shorter keeps it valid.** Removing characters cannot create a repeat. So in each column, once a `V` appears, every cell below it is `V`.

This is **monotone validity**: as the window grows, validity can only switch from valid to invalid, never back. So the first `V` in each column, the smallest valid `left` for that `right`, never moves up as `right` grows: rows 0, 0, 0, 1, 2, 3, 5, 7. One forward scan of `left`, never moving back, finds the best window for every `right`.

**State:** `counts` holds how many times each character occurs in the current window `[left, right]`, and the window is valid between steps.

At each step:

1. Add `text[right]` to `counts`. Only this character can now be repeated.
2. While it is repeated, remove `text[left]` and advance `left`.
3. The window is valid again. Record its length.

```text
index      0  1  2  3  4  5  6  7
text       a  b  c  a  b  c  b  b

right=0   [a] b  c  a  b  c  b  b     add a; nothing to remove          len 1   best 1
right=1   [a  b] c  a  b  c  b  b     add b                             len 2   best 2
right=2   [a  b  c] a  b  c  b  b     add c                             len 3   best 3
right=3    a [b  c  a] b  c  b  b     add a; a repeats; remove a        len 3   best 3
right=4    a  b [c  a  b] c  b  b     add b; b repeats; remove b        len 3   best 3
right=5    a  b  c [a  b  c] b  b     add c; c repeats; remove c        len 3   best 3
right=6    a  b  c  a  b [c  b] b     add b; b repeats; remove a, b     len 2   best 3
right=7    a  b  c  a  b  c  b [b]    add b; b repeats; remove c, b     len 1   best 3
```

At `right = 6`, removing one character was not enough. The first removal took away `a`, but the repeated `b` was still inside. That is why step 2 is a `while` loop and not an `if`.

```python
from random import Random


def longest_unique(text: str) -> tuple[int, tuple[int, int] | None]:
    """Return (length, (left, right)) of the longest window with no repeat.

    Endpoints are inclusive; the earliest window wins ties.
    Empty text returns (0, None).
    """
    counts: dict[str, int] = {}
    left = 0
    best_length, best_range = 0, None
    for right, char in enumerate(text):
        counts[char] = counts.get(char, 0) + 1
        while counts[char] > 1:
            counts[text[left]] -= 1
            left += 1
        if right - left + 1 > best_length:
            best_length, best_range = right - left + 1, (left, right)
    return best_length, best_range


def longest_unique_jump(text: str) -> int:
    """Same length, moving left directly past the previous copy."""
    last_seen: dict[str, int] = {}
    left = best = 0
    for right, char in enumerate(text):
        if last_seen.get(char, -1) >= left:
            left = last_seen[char] + 1
        last_seen[char] = right
        best = max(best, right - left + 1)
    return best


def longest_unique_brute(text):
    return max((r - l + 1 for l in range(len(text)) for r in range(l, len(text))
                if len(set(text[l:r + 1])) == r - l + 1), default=0)


def main():
    assert longest_unique("abcabcbb") == (3, (0, 2))
    assert longest_unique("abba") == (2, (0, 1))
    assert longest_unique("aaaa") == (1, (0, 0))
    assert longest_unique("") == (0, None)
    assert longest_unique_jump("abba") == 2

    rng = Random(11)
    for _ in range(1000):
        text = "".join(rng.choice("abcd") for _ in range(rng.randrange(10)))
        length, span = longest_unique(text)
        assert length == longest_unique_brute(text) == longest_unique_jump(text)
        if span is not None:
            window = text[span[0]:span[1] + 1]
            assert len(window) == length == len(set(window))


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` expected, counting dictionary operations as `O(1)`. **Space:** `O(d)` for `d` distinct characters in the text.

**Is the `while` inside the `for` loop `O(n²)`?** No. Count pointer moves, not loop nesting. `right` moves `n` times. `left` only increases and never passes `right + 1`, so it also moves at most `n` times **in total**, across all iterations. So there are at most `n` additions and `n` removals: `O(n)` work.

**Why it's correct.** For each `right`, the loop finds the longest valid window ending at `right`. The removed starting points were removed because they made a window with a repeat. By fact 1, those starting points stay invalid for every larger `right`, so they can never start an answer again. Every window that the scan never looks at is either invalid or shorter than the one recorded for its `right`. The best window overall ends at some `right`, so it is recorded.

**Variant: jump instead of crawl.** `longest_unique_jump` stores the last position of each character. When `text[right]` was last seen inside the window, `left` jumps straight past it. The check `last_seen[char] >= left` matters: in `"abba"`, the final `a` was last seen at 0, which is already outside the window `[2, 3]`, so `left` must not jump back to 1. Without the check, `left` would move backward.

## 3. Same template, new state: at most `k` distinct characters

Find the longest substring that contains **at most `k` different characters**.

```text
index    0  1  2  3  4
text     e  c  e  b  a      k = 2
```

The answer is 3, from `"ece"`: it uses only `e` and `c`.

**The observation.** Validity is monotone again: a longer window never has fewer distinct characters. So the template from §2 applies with a different state:

**State:** `counts` maps each character in the window to its number of copies, and holds **only characters with a positive count**. Then `len(counts)` is the number of distinct characters.

```text
index      0  1  2  3  4
text       e  c  e  b  a

right=0-2 [e  c  e] b  a     add e, c, e           {e:2, c:1}   len 3   best 3
right=3    e  c [e  b] a     add b: 3 kinds;       {e:1, b:1}   len 2   best 3
                             remove e, then c
right=4    e  c  e [b  a]    add a: 3 kinds;       {b:1, a:1}   len 2   best 3
                             remove e
```

At `right = 3`, removing the first `e` leaves three kinds. Removing `c` brings its count to 0, and that key must be **deleted**; with a zero count left in, `len(counts)` would still say 3.

```python
from random import Random


def longest_at_most_k_distinct(items, k: int) -> int:
    """Length of the longest window with at most k distinct values."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    counts = {}
    left = best = 0
    for right, item in enumerate(items):
        counts[item] = counts.get(item, 0) + 1
        while len(counts) > k:
            outgoing = items[left]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                del counts[outgoing]
            left += 1
        best = max(best, right - left + 1)
    return best


def longest_ones_with_flips(bits: list[int], k: int) -> int:
    """Longest window of 1s after turning at most k zeros into ones."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    left = zeros = best = 0
    for right, bit in enumerate(bits):
        zeros += bit == 0
        while zeros > k:
            zeros -= bits[left] == 0
            left += 1
        best = max(best, right - left + 1)
    return best


def longest_brute(items, is_valid):
    return max((r - l + 1 for l in range(len(items)) for r in range(l, len(items))
                if is_valid(items[l:r + 1])), default=0)


def main():
    assert longest_at_most_k_distinct("eceba", 2) == 3
    assert longest_at_most_k_distinct("aa", 1) == 2
    assert longest_at_most_k_distinct("abc", 0) == 0
    assert longest_at_most_k_distinct("", 3) == 0
    assert longest_at_most_k_distinct([1, 2, 1, 2, 3], 2) == 4  # fruit baskets
    assert longest_ones_with_flips([1, 1, 0, 0, 1, 1, 1, 0, 1], 1) == 5

    rng = Random(12)
    for _ in range(1000):
        text = "".join(rng.choice("abcd") for _ in range(rng.randrange(10)))
        k = rng.randrange(0, 5)
        assert longest_at_most_k_distinct(text, k) == \
            longest_brute(text, lambda w: len(set(w)) <= k)
        bits = [rng.randrange(2) for _ in range(rng.randrange(10))]
        assert longest_ones_with_flips(bits, k) == \
            longest_brute(bits, lambda w: w.count(0) <= k)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` expected. **Space:** `O(k)`: the dictionary holds at most `k + 1` keys at any moment.

`longest_ones_with_flips` is the same template with a simpler state: the number of zeros in the window. "At most `k` zeros" is monotone for the same reason. The "fruit into baskets" problem is `k = 2`.

## 4. The shortest window that reaches a total

Now the goal flips: find the **shortest** window whose sum is at least `target`. All numbers are **positive or zero**. Return 0 if no window reaches the target.

```text
index    0  1  2  3  4  5
nums     2  3  1  2  4  3      target = 7
```

The answer is 2, from `[4, 3]` at positions 4 and 5.

**Brute force.** For each `left`, extend `right` until the sum reaches 7: `O(n²)`.

**The key observation.** Here the useful facts point the other way:

1. **Making a valid window longer keeps it valid.** All numbers are nonnegative, so adding one cannot lower the sum.
2. **Making an invalid window shorter keeps it invalid.** Removing a nonnegative number cannot raise the sum.

So once `[left, right]` reaches the target, every longer window with the same `left` is valid but also longer: it can never beat the current one. Record the current length, then remove `nums[left]` and see whether the window is **still** valid. Keep shrinking while it is. When the sum drops below the target, removing more cannot help (fact 2), so extend `right` instead.

So the shortest template records and shrinks **while valid**, where the longest template shrank **while invalid**, then recorded.

```text
index      0  1  2  3  4  5
nums       2  3  1  2  4  3      target = 7

right=0-2 [2  3  1] 2  4  3      add 2, 3, 1: sum 6 < 7
right=3   [2  3  1  2] 4  3      add 2: sum  8 >= 7   record 4, best 4; remove 2 -> sum 6
right=4    2 [3  1  2  4] 3      add 4: sum 10 >= 7   record 4, best 4; remove 3 -> sum 7
           2  3 [1  2  4] 3             sum  7 >= 7   record 3, best 3; remove 1 -> sum 6
right=5    2  3  1 [2  4  3]     add 3: sum  9 >= 7   record 3, best 3; remove 2 -> sum 7
           2  3  1  2 [4  3]            sum  7 >= 7   record 2, best 2; remove 4 -> sum 3
```

Final answer: 2.

```python
from random import Random


def min_length_sum_at_least(nums: list[int], target: int) -> int:
    """Shortest window with sum >= target. nums nonnegative, target positive.

    Return 0 if no window reaches the target.
    """
    if target <= 0:
        raise ValueError("target must be positive")
    if any(value < 0 for value in nums):
        raise ValueError("nums must be nonnegative")
    left = running = 0
    best = len(nums) + 1
    for right, value in enumerate(nums):
        running += value
        while running >= target:
            best = min(best, right - left + 1)
            running -= nums[left]
            left += 1
    return 0 if best > len(nums) else best


def min_length_brute(nums, target):
    return min((r - l + 1 for l in range(len(nums)) for r in range(l, len(nums))
                if sum(nums[l:r + 1]) >= target), default=0)


def main():
    assert min_length_sum_at_least([2, 3, 1, 2, 4, 3], 7) == 2
    assert min_length_sum_at_least([0, 0, 7], 7) == 1
    assert min_length_sum_at_least([1, 1], 3) == 0      # impossible
    assert min_length_sum_at_least([], 1) == 0          # empty
    for bad in ([1, -1], 1), ([1], 0):
        try:
            min_length_sum_at_least(*bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = Random(13)
    for _ in range(1000):
        nums = [rng.randrange(0, 6) for _ in range(rng.randrange(10))]
        target = rng.randrange(1, 15)
        assert min_length_sum_at_least(nums, target) == min_length_brute(nums, target)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`, including the input check. **Space:** `O(1)`.

**Why it's correct.** When the window `[left, right]` is valid, the code records it before removing `nums[left]`. Any later valid window starting at the same `left` ends further right, so it is longer. That starting point has already given its best length and can be dropped. When the window is invalid, every shorter window ending at `right` is also invalid, so moving `right` forward is the only useful move. No candidate that could beat the recorded best is ever skipped.

### Why negative numbers break this

Both facts used the assumption that numbers are nonnegative. With `nums = [1, -1, 5]` and `target = 5`:

```text
index       0   1   2
nums        1  -1   5

right=2   [ 1  -1   5]     sum 5 >= 5   record 3; remove 1 -> sum 4
            1 [-1   5]     sum 4 <  5   stop shrinking
```

The loop stops, but removing `-1` would raise the sum back to 5 and give the window `[5]` of length 1. An invalid window **can** become valid by shrinking when values may be negative. The validity is no longer monotone, so no window algorithm can know when to stop. [Advanced Window Patterns](04-advanced-patterns.md) solves this case with prefix sums and a deque.

## 5. The two templates side by side

| Goal | Validity must be monotone in this direction | Shrink while | Record when |
|---|---|---|---|
| Longest valid window | Extending an invalid window keeps it invalid | Invalid | After the loop restores validity |
| Shortest valid window | Extending a valid window keeps it valid | Valid | Before each removal |

```text
longest:                              shortest:
for right in range(n):                for right in range(n):
    add(items[right])                     add(items[right])
    while not valid():                    while valid():
        remove(items[left]); left += 1        record(right - left + 1)
    record(right - left + 1)                  remove(items[left]); left += 1
```

Keep a state whose validity check is `O(1)`: a count, a sum, or a dictionary's size.

Before writing a window, answer three questions:

1. **What is the state**, and how does it change when one item enters or leaves?
2. **Which direction is validity monotone in?** If you cannot prove one of the two rows of the table, a sliding window is the wrong tool.
3. **When is the answer recorded?** After restoring validity, or before each removal.

Every template is linear for the reason given in §2: each pointer moves forward at most `n` times in total, and each move does `O(1)` work on the state.

| Algorithm | Time | Extra space |
|---|---:|---:|
| Fixed-size sum | `O(n)` | `O(1)` |
| Longest without repeats | `O(n)` expected | `O(d)`, `d` distinct characters |
| Longest with at most `k` distinct | `O(n)` expected | `O(k)` |
| Shortest with sum at least target (nonnegative) | `O(n)` | `O(1)` |

## 6. Pitfalls and practice

1. **Starting a maximum at 0.** All window sums may be negative. Start from the first full window.
2. **`if` instead of `while` when shrinking.** One removal may not restore the condition (see `right = 6` in §2).
3. **Recording at the wrong moment.** A longest window is recorded after it is valid again; a shortest window before its left element is removed.
4. **Keeping zero counts in the dictionary** when `len(counts)` means "number of distinct values".
5. **Jumping `left` backward** in the last-seen variant. Only jump when the previous copy is inside the window.
6. **Using a variable window when values can be negative.** Check monotone validity first; negative values break sum conditions.
7. **Sorting the input.** Sorting changes which elements are neighbors. A window must use the original order.
8. **Copying slices inside the loop.** Store endpoints and slice once at the end; slicing every step adds `O(n)` per step.

Practice: Maximum Average Subarray I; Longest Substring Without Repeating Characters; Longest Substring with At Most K Distinct Characters; Fruit Into Baskets; Max Consecutive Ones III; Minimum Size Subarray Sum; Maximum Points You Can Obtain from Cards (a fixed window on the complement); Grumpy Bookstore Owner.

Next: [Counting and Frequency Windows](03-counting-and-frequency-windows.md).
