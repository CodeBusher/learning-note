# Advanced Window Patterns — When the Simple Proof Bends or Breaks

## 1. Longest repeating character replacement

You get a string of uppercase letters and a budget `k`. You may change at most `k` letters into any other letters. Find the longest substring that can be made into one repeated letter.

```text
index    0  1  2  3  4  5  6
text     A  A  B  A  B  B  A      k = 1
```

The answer is 4: `AABA` at `[0, 3]` becomes `AAAA` by changing its one `B`. Also `BABB` at `[2, 5]` becomes `BBBB`.

**Brute force.** Check all `O(n²)` windows. For each, count its letters.

**The key observation.** In a window of length `L`, the cheapest plan keeps the most frequent letter and changes everything else:

$$
\text{changes needed} = L - \max_c \text{count}[c].
$$

The window is valid when this is at most `k`. Is validity monotone? Pick any one letter `c`. Extending the window adds one letter, which is either `c` (its mismatch count stays the same) or not (it grows by one). So the number of non-`c` letters never falls as the window grows, for every `c`. The smallest of them, which is the number of changes needed, cannot fall either. An invalid window stays invalid when extended, and the longest-window template applies.

**State:** `counts`, the 26 letter counts of `[left, right]`.

```text
index      0  1  2  3  4  5  6
text       A  A  B  A  B  B  A      k = 1

right=0-2 [A  A  B] A  B  B  A     A=2 B=1   needs 3-2 = 1              len 3  best 3
right=3   [A  A  B  A] B  B  A     A=3 B=1   needs 4-3 = 1              len 4  best 4
right=4    A  A [B  A  B] B  A     add B: needs 5-3 = 2 > 1
                                   remove A, A: A=1 B=2, needs 3-2 = 1  len 3  best 4
right=5    A  A [B  A  B  B] A     A=1 B=3   needs 4-3 = 1              len 4  best 4
right=6    A  A  B  A [B  B  A]    add A: needs 5-3 = 2 > 1
                                   remove B, A: A=1 B=2, needs 3-2 = 1  len 3  best 4
```

The exact code, `longest_replacement` below, is the longest-window template with `while right - left + 1 - max(counts) > k`. Each `max(counts)` scans 26 numbers, so it costs `O(26 · n)`; with a large alphabet that scan costs one step per distinct letter, which motivates the shortcut.

### The famous shortcut: a maximum that never decreases

Many solutions replace `max(counts)` with a variable `max_freq` that only ever **grows**: when a letter enters, `max_freq = max(max_freq, counts[letter])`. When letters leave, `max_freq` is not lowered, even if it is now too large. They also use `if` instead of `while`, so the window never shrinks; it either grows by one or slides by one.

This looks like a bug. Here is the same input with the shortcut:

```text
index      0  1  2  3  4  5  6
text       A  A  B  A  B  B  A      k = 1

right=3   [A  A  B  A] B  B  A     max_freq 3             len 4
right=4    A [A  B  A  B] B  A     max_freq 3; slide by one;  window ABAB really needs 2 changes
right=5    A  A [B  A  B  B] A     max_freq 3; slide by one;  window BABB needs 1 change
right=6    A  A  B [A  B  B  A]    max_freq 3; slide by one;  window ABBA needs 2 changes
```

At `right = 4` the window `ABAB` is **not** valid: it needs two changes, and `k = 1`. The true maximum count in it is 2, but `max_freq` still says 3. Yet the final answer, the window length 4, is correct. Why?

**Why `max_freq` need not decrease.** Two facts make it work.

1. **The length never claims more than is achievable.** Each step adds one letter and removes at most one, so the window length never goes down. It grows from `L` to `L + 1` only when `(L + 1) - max_freq <= k`. The value `max_freq` is a real letter count: some window `W` seen so far, no longer than `L + 1`, held `max_freq` copies of one letter. Stretch `W` to any window of length `L + 1` that contains it (possible, since the text has at least `L + 1` letters). That window still has at least `max_freq` copies of the letter, so it needs at most `(L + 1) - max_freq <= k` changes. A valid window of length `L + 1` exists.
2. **The length reaches the optimum.** First, `max_freq` is never smaller than the true largest count in the current window: since a letter's last copy entered, its count has only gone down, and `max_freq` was updated at that moment. So whenever the window after adding `text[right]` is truly valid, the shortcut's test passes and nothing is removed. Now claim: after step `e`, the length is at least `ℓ`, the length of the longest valid window ending at `e`. The window `[e - ℓ + 1, e - 1]` is valid (a shorter part of a valid window is valid) and ends at `e - 1`, so before step `e` the length is at least `ℓ - 1`. If it is already `ℓ` or more, it stays that way. If it is exactly `ℓ - 1`, then after adding `text[e]` the window is exactly `[e - ℓ + 1, e]`, which is valid, so it grows to `ℓ`. Applying the claim at the end of the best window shows the final length reaches the best length.

The price: the final window may be **invalid**, as at `right = 4` above. Use the shortcut for the **length** only. If you need to return an actual valid substring, use the exact version.

```python
from random import Random


def longest_replacement(text: str, k: int) -> int:
    """Uppercase A-Z, k >= 0. Longest window fixable with <= k changes."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    if any(not "A" <= char <= "Z" for char in text):
        raise ValueError("text must contain only A-Z")
    counts = [0] * 26
    left = best = 0
    for right, char in enumerate(text):
        counts[ord(char) - 65] += 1
        while right - left + 1 - max(counts) > k:
            counts[ord(text[left]) - 65] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


def longest_replacement_lazy(text: str, k: int) -> int:
    """Any alphabet. Length only: the final window itself may be invalid."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    counts = {}
    left = max_freq = 0
    for right, char in enumerate(text):
        counts[char] = counts.get(char, 0) + 1
        max_freq = max(max_freq, counts[char])
        if right - left + 1 - max_freq > k:
            counts[text[left]] -= 1
            left += 1
    return len(text) - left


def longest_replacement_brute(text, k):
    return max((r - l + 1 for l in range(len(text)) for r in range(l, len(text))
                if r - l + 1 - max(map(text[l:r + 1].count, text[l:r + 1])) <= k),
               default=0)


def main():
    assert longest_replacement("AABABBA", 1) == 4
    assert longest_replacement("ABAB", 2) == 4
    assert longest_replacement("ABC", 0) == 1
    assert longest_replacement("", 0) == 0
    assert longest_replacement_lazy("AABABBA", 1) == 4
    assert longest_replacement_lazy("ABBBCCA", 1) == 4
    assert longest_replacement_lazy("", 2) == 0

    rng = Random(31)
    for _ in range(2000):
        text = "".join(rng.choice("ABCD") for _ in range(rng.randrange(11)))
        k = rng.randrange(0, 4)
        expected = longest_replacement_brute(text, k)
        assert longest_replacement(text, k) == longest_replacement_lazy(text, k) == expected


if __name__ == "__main__":
    main()
```

**Time:** `O(26 · n)` for the exact version; `O(n)` expected for the lazy one, for any alphabet. **Space:** `O(1)` and `O(d)` for `d` distinct letters. The lazy window never shrinks, so its final length `len(text) - left` is the answer.

## 2. Exact sums with negative values: prefix sums and a map

Count the windows whose sum is exactly `target`. Values may be negative.

With nonnegative values, [two "at most" counts](03-counting-and-frequency-windows.md#2-exactly-k-subtract-two-at-most-counts) solve this. With negatives, no sum window works. Every window proof for sums needs "adding a value never lowers the sum, removing one never raises it", and a negative value breaks both: in `[1, -1, 5]` with target 5 the shortest-window scan [shrinks to `[-1, 5]` and stops](02-fixed-and-variable-windows.md#why-negative-numbers-break-this), although removing `-1` would reach `[5]`. No `while` condition fixes this; the window has no rule for when to stop. So drop the moving left end and look the right starts up directly, with [prefix sums](../04-range-queries/01-prefix-sums.md).

```text
index    0   1   2   3   4
nums     1   2  -1   2   1      target = 3
```

The answer is 3: `[1, 2]` at `[0, 1]`, `[2, -1, 2]` at `[1, 3]`, and `[2, 1]` at `[3, 4]`.

**Brute force.** Sum every window: `O(n²)` with running sums.

**The key observation.** Let `P[j]` be the sum of the first `j` values, so `P[0] = 0` and `P[j + 1] = P[j] + nums[j]`. A **prefix sum** turns a window sum into a difference of two numbers:

$$
\text{sum of nums}[i..j-1] = P[j] - P[i].
$$

So the window `nums[i:j]` has sum `target` exactly when `P[i] = P[j] - target` for some earlier `i < j`. Walk `j` forward, and keep a hash map `seen` that counts how often each prefix value has appeared so far. At each `j`, the number of windows ending at `j - 1` with the right sum is `seen[P[j] - target]`.

**State:** `seen[s]` = how many of `P[0], …, P[j - 1]` equal `s`.

```text
index      0   1   2   3   4
nums       1   2  -1   2   1      target = 3
P      0   1   3   2   4   5
```

| `j` | `P[j]` | Look up `P[j] - 3` | `seen` before inserting `P[j]` | Found | Total | Window found |
|---:|---:|---:|---|---:|---:|---|
| 0 | 0 | — | `{}` | — | 0 | (`P[0]` is inserted first) |
| 1 | 1 | -2 | `{0:1}` | 0 | 0 | |
| 2 | 3 | 0 | `{0:1, 1:1}` | 1 | 1 | `P[2] - P[0]`: `[0, 1]` |
| 3 | 2 | -1 | `{0:1, 1:1, 3:1}` | 0 | 1 | |
| 4 | 4 | 1 | `{0:1, 1:1, 3:1, 2:1}` | 1 | 2 | `P[4] - P[1]`: `[1, 3]` |
| 5 | 5 | 2 | `{0:1, 1:1, 3:1, 2:1, 4:1}` | 1 | 3 | `P[5] - P[3]`: `[3, 4]` |

```python
from random import Random


def count_exact_sum(nums: list[int], target: int) -> int:
    """Count nonempty windows with sum == target. Any signs allowed."""
    seen = {0: 1}                # P[0] = 0
    prefix = total = 0
    for value in nums:
        prefix += value
        total += seen.get(prefix - target, 0)    # look up before inserting
        seen[prefix] = seen.get(prefix, 0) + 1
    return total


def longest_exact_sum(nums: list[int], target: int) -> int:
    """Length of the longest window with sum == target, or 0 if none."""
    first = {0: 0}               # earliest j with each prefix value
    prefix = best = 0
    for j, value in enumerate(nums, start=1):
        prefix += value
        if prefix - target in first:
            best = max(best, j - first[prefix - target])
        first.setdefault(prefix, j)
    return best


def main():
    assert count_exact_sum([1, 2, -1, 2, 1], 3) == 3
    assert count_exact_sum([1, -1, 1], 1) == 3
    assert count_exact_sum([0, 0, 0], 0) == 6
    assert count_exact_sum([], 0) == 0
    assert longest_exact_sum([1, -1, 5, -2, 3], 3) == 4

    rng = Random(32)
    for _ in range(1000):
        nums = [rng.randrange(-4, 5) for _ in range(rng.randrange(9))]
        target = rng.randrange(-5, 6)
        sums = [(sum(nums[l:r + 1]), r - l + 1)
                for l in range(len(nums)) for r in range(l, len(nums))]
        assert count_exact_sum(nums, target) == sum(s == target for s, _ in sums)
        assert longest_exact_sum(nums, target) == \
            max((n for s, n in sums if s == target), default=0)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` expected. **Space:** `O(n)` for the map.

**Why look up before inserting?** The lookup must see only earlier prefixes `i < j`. Inserting `P[j]` first would pair it with itself, which is an empty window, and for `target = 0` it would be counted.

**Why it's correct.** Every window `[i, j - 1]` corresponds to exactly one pair `i < j` of prefix positions. At step `j`, `seen` holds exactly the earlier prefixes, so each window is counted once, at its right end.

**Variant: longest instead of count.** To find the longest window with sum `target`, store the **earliest** position of each prefix value instead of a count (`longest_exact_sum`). The earliest start gives the longest window for each end, so later copies of the same prefix value are never needed.

## 3. Shortest window with sum at least `k`, negatives allowed

Find the length of the shortest window with sum at least `k`, where values may be negative. Return 0 if there is none.

```text
index       0   1   2   3   4
nums        3  -4   2   3   3      k = 6
```

The answer is 2: `[3, 3]` at `[3, 4]`. The [shortest-window template](02-fixed-and-variable-windows.md#4-the-shortest-window-that-reaches-a-total) returns 5 here: it reaches sum 7 at `right = 4`, records length 5, removes the 3 to get sum 4, and stops. It never tries removing the `-4`.

**Brute force.** Check all `O(n²)` windows using prefix sums.

**The key observation.** With prefix sums, we want the pair `i < j` with `P[j] - P[i] >= k` and the smallest `j - i`. As `j` moves forward, keep a list of **candidate starts** `i`. Two rules remove candidates that can never win:

1. **Front rule: a start that has already succeeded is finished.** If `P[j] - P[i] >= k`, record `j - i`. Any later `j' > j` would make a longer window with the same `i`, so `i` can be dropped for good.
2. **Back rule: a newer, lower prefix beats an older, higher one.** If `i < j` and `P[i] >= P[j]`, then for every future end `j'`, `P[j'] - P[j] >= P[j'] - P[i]`, and `j` gives a shorter window. Start `i` can never be better than `j`, so drop `i`.

After the back rule, the candidates have **strictly increasing** prefix values from front to back. That is exactly what makes the front rule correct to apply only at the front: the front has the smallest prefix, so if it does not succeed, no candidate does. A list with removals at both ends is a **deque** (double-ended queue), and a deque whose values stay sorted is a **monotonic deque**.

```text
index        0   1   2   3   4
nums         3  -4   2   3   3      k = 6
P        0   3  -1   1   4   7
```

| `j` | `P[j]` | Front rule (`P[j] - P[front] >= 6`?) | Back rule (`P[back] >= P[j]`?) | Deque after (index:prefix) | Best |
|---:|---:|---|---|---|---:|
| 0 | 0 | — | — | `0:0` | — |
| 1 | 3 | `3 - 0 = 3`: no | no | `0:0, 1:3` | — |
| 2 | -1 | `-1 - 0`: no | drop `1:3`, drop `0:0` | `2:-1` | — |
| 3 | 1 | `1 - (-1) = 2`: no | no | `2:-1, 3:1` | — |
| 4 | 4 | `4 - (-1) = 5`: no | no | `2:-1, 3:1, 4:4` | — |
| 5 | 7 | `7 - (-1) = 8`: yes, length 3, drop 2; `7 - 1 = 6`: yes, length 2, drop 3; `7 - 4 = 3`: no | no | `4:4, 5:7` | 2 |

At `j = 2`, the prefix fell to -1. Every earlier start had a higher prefix, so starting after the `-4` is always better: those starts are gone.

```python
from collections import deque
from random import Random


def shortest_sum_at_least(nums: list[int], k: int) -> int:
    """Shortest nonempty window with sum >= k; any signs. 0 if none."""
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    best = len(nums) + 1
    starts: deque[int] = deque()     # indices with strictly increasing prefix
    for j, p in enumerate(prefix):
        while starts and p - prefix[starts[0]] >= k:
            best = min(best, j - starts.popleft())
        while starts and prefix[starts[-1]] >= p:
            starts.pop()
        starts.append(j)
    return 0 if best > len(nums) else best


def shortest_brute(nums, k):
    lengths = [r - l + 1 for l in range(len(nums)) for r in range(l, len(nums))
               if sum(nums[l:r + 1]) >= k]
    return min(lengths, default=0)


def main():
    assert shortest_sum_at_least([3, -4, 2, 3, 3], 6) == 2
    assert shortest_sum_at_least([1, -1, 5], 5) == 1
    assert shortest_sum_at_least([2, -1, 2], 3) == 3
    assert shortest_sum_at_least([1, 2], 4) == 0
    assert shortest_sum_at_least([], 1) == 0
    assert shortest_sum_at_least([-5], -6) == 1

    rng = Random(33)
    for _ in range(2000):
        nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(9))]
        k = rng.randrange(-4, 10)
        assert shortest_sum_at_least(nums, k) == shortest_brute(nums, k)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`: each prefix index enters the deque once and leaves at most once. **Space:** `O(n)`.

**Why the front rule runs first.** Both rules compare against the new `P[j]`. A start removed by the back rule has `P[i] >= P[j]`, so its window sum `P[j] - P[i]` is at most 0. For a positive `k` it could never pass the front rule, and the order would not matter. For `k <= 0` it could, so the front rule must record it before the back rule throws it away. Running the front rule first is correct for every `k`. The [monotonic deque chapter](../06-monotonic-stack-and-deque/README.md) studies this structure in depth.

## 4. Sliding window maximum: when the state is not one number

For each window of exactly `k` neighbors, report its largest value.

```text
index     0   1   2   3   4   5   6   7
nums      1   3  -1  -3   5   3   6   7      k = 3
```

The answer is `[3, 3, 5, 5, 6, 7]`.

**Brute force.** Take `max` of each window: `O(n · k)`.

### Why a single number is not enough

A running sum works because subtraction undoes addition. A maximum cannot be undone. If the window `[3, -1, -3]` loses its 3, the number 3 says nothing about the next largest value. We need to remember more, but not everything.

**The key observation.** A value is **useless** once a larger (or equal) value arrives **after** it: the newer value stays in the window at least as long and is at least as large. So keep a deque of indices whose values are **decreasing** from front to back:

- **Back:** before adding `nums[right]`, pop every index whose value is `<=` it. They can never be the maximum again.
- **Front:** if the front index has left the window (`front <= right - k`), pop it.
- The front is the maximum of the current window.

| `right` | Value | Pops from back | Expire front | Deque after (index:value) | Window max |
|---:|---:|---|---|---|---:|
| 0 | 1 | — | — | `0:1` | — |
| 1 | 3 | `0:1` | — | `1:3` | — |
| 2 | -1 | — | — | `1:3, 2:-1` | 3 |
| 3 | -3 | — | — | `1:3, 2:-1, 3:-3` | 3 |
| 4 | 5 | `3:-3`, `2:-1`, `1:3` | — | `4:5` | 5 |
| 5 | 3 | — | — | `4:5, 5:3` | 5 |
| 6 | 6 | `5:3`, `4:5` | — | `6:6` | 6 |
| 7 | 7 | `6:6` | — | `7:7` | 7 |

In this input, every large value was pushed out from the back before it could expire. With `nums = [5, 1, 1, 1]` and `k = 2`, the 5 leaves through the front at `right = 2`.

```python
from collections import deque
from random import Random


def window_maxima(nums: list[int], k: int) -> list[int]:
    """Maximum of every window of exactly k elements."""
    if not 1 <= k <= len(nums):
        raise ValueError("k must be between 1 and len(nums)")
    candidates: deque[int] = deque()    # indices, values decreasing
    result = []
    for right, value in enumerate(nums):
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(right)
        if candidates[0] <= right - k:
            candidates.popleft()
        if right >= k - 1:
            result.append(nums[candidates[0]])
    return result


def main():
    assert window_maxima([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert window_maxima([5, 1, 1, 1], 2) == [5, 1, 1]
    assert window_maxima([4], 1) == [4]
    assert window_maxima([2, 2, 2], 2) == [2, 2]

    rng = Random(34)
    for _ in range(1000):
        nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(1, 10))]
        k = rng.randrange(1, len(nums) + 1)
        assert window_maxima(nums, k) == \
            [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`: each index is pushed once and popped at most once. **Space:** `O(k)`. One `if` suffices for expiry, because the window moves by one and at most one index can expire per step. For the minimum, flip the comparison. [Monotonic Stacks and Deques](../06-monotonic-stack-and-deque/README.md) covers the deque's invariant and its equal-value rule in depth.

## 5. Combining both: longest window with `max - min <= limit`

Find the longest window whose largest and smallest values differ by at most `limit`.

```text
index    0  1  2  3
nums     8  2  4  7      limit = 4
```

The answer is 2: `[2, 4]` (difference 2) or `[4, 7]` (difference 3).

The condition is monotone: extending a window can only raise its maximum and lower its minimum. So the longest-window template applies, and two deques from §4 supply the maximum and minimum in `O(1)`. The window decides how the ends move; the deques answer "what is the max and min right now".

| `right` | Value | Max deque (index:value) | Min deque | Shrink | Window | Length | Best |
|---:|---:|---|---|---|---|---:|---:|
| 0 | 8 | `0:8` | `0:8` | — | `[8]` | 1 | 1 |
| 1 | 2 | `0:8, 1:2` | `1:2` | `8 - 2 = 6 > 4`: left → 1, expire `0:8` | `[2]` | 1 | 1 |
| 2 | 4 | `2:4` | `1:2, 2:4` | `4 - 2 = 2`: no | `[2, 4]` | 2 | 2 |
| 3 | 7 | `3:7` | `1:2, 2:4, 3:7` | `7 - 2 = 5 > 4`: left → 2, expire `1:2` | `[4, 7]` | 2 | 2 |

```python
from collections import deque
from random import Random


def longest_bounded_range(nums: list[int], limit: int) -> int:
    """Longest window with max - min <= limit (limit >= 0)."""
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    high: deque[int] = deque()      # indices, values decreasing (front = max)
    low: deque[int] = deque()       # indices, values increasing (front = min)
    left = best = 0
    for right, value in enumerate(nums):
        while high and nums[high[-1]] <= value:
            high.pop()
        high.append(right)
        while low and nums[low[-1]] >= value:
            low.pop()
        low.append(right)
        while nums[high[0]] - nums[low[0]] > limit:
            left += 1
            if high[0] < left:
                high.popleft()
            if low[0] < left:
                low.popleft()
        best = max(best, right - left + 1)
    return best


def longest_bounded_brute(nums, limit):
    return max((r - l + 1 for l in range(len(nums)) for r in range(l, len(nums))
                if max(nums[l:r + 1]) - min(nums[l:r + 1]) <= limit), default=0)


def main():
    assert longest_bounded_range([8, 2, 4, 7], 4) == 2
    assert longest_bounded_range([10, 1, 2, 4, 7, 2], 5) == 4
    assert longest_bounded_range([4, 2, 2, 2, 4, 4, 2, 2], 0) == 3
    assert longest_bounded_range([], 3) == 0

    rng = Random(35)
    for _ in range(1000):
        nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(10))]
        limit = rng.randrange(0, 6)
        assert longest_bounded_range(nums, limit) == longest_bounded_brute(nums, limit)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`. **Space:** `O(n)` in the worst case for the deques.

## 6. Choosing a method: derive a window, or decide not to

Pointer moves in this folder were justified by sorted order, an area formula, monotone validity, counting identities and dominance in a deque. Whether a window survives negative values depends on whether its pointer moves depend on the values' signs:

| Question | Values | Method |
|---|---|---|
| Best sum of exactly `k` neighbors | Any signs | Fixed window (size, not sum, moves the pointers) |
| Distinct counts, letter frequencies, coverage | Any signs | Window (signs do not matter) |
| Shortest window with sum at least target | Nonnegative | [Window](02-fixed-and-variable-windows.md#4-the-shortest-window-that-reaches-a-total) |
| Count windows with sum exactly target | Any signs | Prefix sums and a hash map (§2) |
| Shortest window with sum at least target | Any signs | Prefix sums and a monotonic deque (§3) |
| Largest sum of any window | Any signs | Kadane's algorithm, a one-line [dynamic programming](../09-dynamic-programming/README.md) recurrence |

For an unfamiliar problem, fill in these sentences before writing code:

1. "My state describes exactly the window `[left, right]` and is ___."
2. "Adding `a[right]` changes ___; removing `a[left]` undoes it by ___."
3. "I can drop this left end forever because ___." (Monotone validity, a finished shortest window, or dominance.)
4. "For this `right`, the windows my state stands for are ___." (One longest window, or a whole block of `right - left + 1` starts.)
5. "Each element enters ___ times and leaves ___ times." (Usually once each, giving `O(n)`.)

If sentence 3 cannot be proved, a window is the wrong tool. The usual replacements are:

| Symptom | Try instead |
|---|---|
| Sum conditions with negative values | Prefix sums with a hash map (§2) or a monotonic deque (§3) |
| "Exactly" a count | Subtract two "at most" counts ([Counting and Frequency Windows](03-counting-and-frequency-windows.md#2-exactly-k-subtract-two-at-most-counts)) |
| The window needs a maximum, minimum, or median | Monotonic deques (§4), or two heaps for medians ([Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md)) |
| The answer is a length, and a fixed-length check is easy | Binary search on the length ([Search on the Answer](../01-binary-search/03-search-on-the-answer.md)) |
| Choices interact beyond one contiguous stretch | [Dynamic programming](../09-dynamic-programming/README.md) |

## 7. Pitfalls and practice

1. **Running a sum window with negative values.** Check monotone validity first. The `[1, -1, 5]` example breaks it.
2. **Returning the window from the lazy `max_freq` version.** Its length is right; the window itself may be invalid.
3. **Inserting the current prefix before the lookup** in the prefix-sum count. That counts empty windows when the target is 0.
4. **Forgetting `P[0] = 0`.** Without it, windows starting at index 0 are missed.
5. **Storing values instead of indices in a deque.** Expiry needs positions; equal values make values ambiguous.
6. **Wrong comparison in the window-maximum deque.** Popping `<=` keeps the deque strictly decreasing; popping only `<` keeps duplicates, which also works but stores more.
7. **Applying the deque's back rule before the front rule** in §3. For `k <= 0` this drops starts before their success is recorded.

Practice: Longest Repeating Character Replacement; Subarray Sum Equals K; Continuous Subarray Sum (prefix sums modulo k); Maximum Size Subarray Sum Equals k; Shortest Subarray with Sum at Least K; Sliding Window Maximum; Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit; Constrained Subsequence Sum (a deque inside a DP); Minimum Number of K Consecutive Bit Flips; Sliding Window Median.

Back to [Two Pointers and Sliding Window](README.md).
