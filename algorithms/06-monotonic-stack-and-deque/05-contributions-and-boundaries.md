# Contributions and Boundaries — How Far Can Each Element Reach?

## 1. Largest rectangle in a histogram

**Problem.** Bars of width 1 stand side by side with heights `h`. Find the largest area of a rectangle that fits entirely under the bars.

```text
heights = [2, 1, 5, 6, 2, 3]

      █
    ▓ ▓
    ▓ ▓
    ▓ ▓   █
█   ▓ ▓ █ █
█ █ ▓ ▓ █ █
0 1 2 3 4 5
```

The shaded rectangle (`▓`) spans bars 2 and 3 at height 5: area `5 × 2 = 10`, the best possible.

**Brute force.** A rectangle over bars `[l..r]` can be as tall as the shortest bar among them. Try every pair `l <= r`, keeping a running minimum as `r` grows: `O(n²)`.

### The key observation: every best rectangle is limited by one bar

Take the best rectangle. Its height equals the height of its shortest covered bar, otherwise it could be taller. Call that bar `i`. The rectangle must also be as wide as possible at that height, otherwise it could be wider. How far can a rectangle of height `h[i]` that contains bar `i` stretch? Left up to, but not including, the nearest bar **strictly shorter** than `h[i]`, and right up to the next strictly shorter bar.

So for each bar `i`, let

- `L[i]` = index of the previous bar with `h < h[i]`, or `−1` if none,
- `R[i]` = index of the next bar with `h < h[i]`, or `n` if none.

The widest rectangle of height `h[i]` around bar `i` covers bars `L[i] + 1 .. R[i] − 1`:

$$
\text{area}_i=h[i]\cdot\big(R[i]-L[i]-1\big).
$$

Both arrays come from the nearest-smaller stacks of [Monotonic Stack §8](02-monotonic-stack.md#8-all-eight-neighbor-queries). The answer is the largest `area_i`. That turns "try every pair" into "try every bar", `n` candidates, each with two boundaries. The sentinels `−1` and `n` make the width right even when no shorter bar exists.

| `i` | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| `h[i]` | 2 | 1 | 5 | 6 | 2 | 3 |
| `L[i]` (previous `<`) | −1 | −1 | 1 | 2 | 1 | 4 |
| `R[i]` (next `<`) | 1 | 6 | 4 | 4 | 6 | 6 |
| width `R − L − 1` | 1 | 6 | 2 | 1 | 4 | 1 |
| area | 2 | 6 | **10** | 6 | 8 | 3 |

Bar 4 (height 2) reaches from bar 2 to bar 5: the bar of height 1 at index 1 stops it on the left, and nothing stops it on the right.

### One pass: a bar's right boundary is the bar that pops it

The two boundary arrays take two stack passes. One pass is enough. Keep a stack of bar indices with **nondecreasing** heights, and pop the top while it is taller than the current bar:

- The current bar `j` is the first bar to the right that is shorter than the popped bar: it is the popped bar's **right boundary**.
- The bar directly below the popped one in the stack is its **left boundary**. Every bar between the two is at least as tall as the popped bar: a shorter one would either still sit between them on the stack, or would have been popped by an even shorter bar, which would have popped this one too. (With equal heights, the bar below may be equally tall; the subsection on equal heights explains why that is harmless.)

After the last bar, a virtual bar of height `−1` at index `n` pops everything that is left.

### Worked trace

`h = [2, 1, 5, 6, 2, 3]`. Stack written bottom to top as `index:height`.

| `j` | `h[j]` | Popped bar | Left boundary (new top) | Width `j − left − 1` | Area | Best | Stack after |
|---:|---:|---|---:|---:|---:|---:|---|
| 0 | 2 | — | | | | 0 | `0:2` |
| 1 | 1 | `0:2` | −1 | 1 | 2 | 2 | `1:1` |
| 2, 3 | 5, 6 | — | | | | 2 | `1:1  2:5  3:6` |
| 4 | 2 | `3:6` | 2 | 1 | 6 | 6 | |
|   |   | `2:5` | 1 | 2 | 10 | 10 | `1:1  4:2` |
| 5 | 3 | — | | | | 10 | `1:1  4:2  5:3` |
| 6 | −1 (virtual) | `5:3` | 4 | 1 | 3 | 10 | |
|   |   | `4:2` | 1 | 4 | 8 | 10 | |
|   |   | `1:1` | −1 | 6 | 6 | 10 | empty |

Every bar is popped exactly once, and the area computed at its pop is exactly its `area_i` from the table above.

The code comes after §2, which reuses it.

### Equal heights

The one-pass loop pops only on `>`, so equal heights stay stacked. Run `[2, 2, 2]`: nothing pops until the virtual bar, which pops index 2 (width 1, left boundary 1), then index 1 (width 2), then index 0 (width 3, area 6). Only the **leftmost** of the equal bars gets the full width; the others get narrower widths.

That is still correct, because the maximum needs only **one** bar to see the full rectangle, and the leftmost equal bar always does. Popping on `>=` would also work, with the **rightmost** equal bar seeing the full width. Extra, too-narrow candidates never exceed a real rectangle, so they cannot spoil a maximum. Section 4 shows that a sum is much less forgiving.

## 2. Maximal rectangle of ones in a binary matrix

**Problem.** Given a grid of `0`s and `1`s, find the area of the largest rectangle containing only `1`s.

```text
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```

The answer is 6: rows 1–2, columns 2–4.

**Brute force.** Try every rectangle (choose two rows and two columns) and check it is all ones. With a 2D prefix sum the check is `O(1)`, so this is `O(R²C²)` for `R` rows and `C` columns.

**The key observation.** Fix the **bottom row** of the rectangle. For each column, count how many consecutive `1`s stand on that row going upward: a **height**. The rectangles with this bottom row are exactly the histogram rectangles of those heights. So run §1 once per row.

The heights are updated row by row: a `1` adds one to the column's height, a `0` resets it to 0.

| Row | Cells | Heights | Largest histogram rectangle |
|---:|---|---|---:|
| 0 | `1 0 1 0 0` | `1 0 1 0 0` | 1 |
| 1 | `1 0 1 1 1` | `2 0 2 1 1` | 3 (height 1, columns 2–4) |
| 2 | `1 1 1 1 1` | `3 1 3 2 2` | **6** (height 2, columns 2–4) |
| 3 | `1 0 0 1 0` | `4 0 0 3 0` | 4 (height 4, column 0) |

### Code for §1 and §2

```python
import random


def largest_rectangle(h: list[int]) -> int:
    """Largest rectangle under a histogram of nonnegative unit-width bars."""
    if any(x < 0 for x in h):
        raise ValueError("heights must be nonnegative")
    n = len(h)
    best = 0
    stack: list[int] = []                     # heights nondecreasing bottom -> top
    for j in range(n + 1):
        current = h[j] if j < n else -1       # virtual bar flushes the stack
        while stack and h[stack[-1]] > current:
            bar = stack.pop()
            left = stack[-1] if stack else -1
            best = max(best, h[bar] * (j - left - 1))
        stack.append(j)
    return best


def largest_rectangle_two_pass(h: list[int]) -> int:
    n = len(h)
    L, R = [-1] * n, [n] * n
    stack: list[int] = []
    for i in range(n):                        # previous strictly smaller
        while stack and h[stack[-1]] >= h[i]:
            stack.pop()
        L[i] = stack[-1] if stack else -1
        stack.append(i)
    stack.clear()
    for i in range(n - 1, -1, -1):            # next strictly smaller
        while stack and h[stack[-1]] >= h[i]:
            stack.pop()
        R[i] = stack[-1] if stack else n
        stack.append(i)
    return max((h[i] * (R[i] - L[i] - 1) for i in range(n)), default=0)


def largest_rectangle_brute(h: list[int]) -> int:
    best = 0
    for l in range(len(h)):
        low = h[l]
        for r in range(l, len(h)):
            low = min(low, h[r])
            best = max(best, low * (r - l + 1))
    return best


def maximal_rectangle(grid: list[list[int]]) -> int:
    if not grid:
        return 0
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("rows must have equal length")
    heights = [0] * width
    best = 0
    for row in grid:
        for c, cell in enumerate(row):
            heights[c] = heights[c] + 1 if cell else 0
        best = max(best, largest_rectangle(heights))
    return best


def maximal_rectangle_brute(grid: list[list[int]]) -> int:
    R = len(grid)
    C = len(grid[0]) if R else 0
    best = 0
    for top in range(R):
        for bottom in range(top, R):
            for left in range(C):
                for right in range(left, C):
                    if all(grid[r][c] for r in range(top, bottom + 1)
                           for c in range(left, right + 1)):
                        best = max(best, (bottom - top + 1) * (right - left + 1))
    return best


def main():
    for f in (largest_rectangle, largest_rectangle_two_pass, largest_rectangle_brute):
        assert f([2, 1, 5, 6, 2, 3]) == 10
        assert f([2, 2, 2]) == 6
        assert f([0, 2, 0]) == 2
        assert f([1, 2, 3, 4]) == 6
        assert f([]) == 0
    rng = random.Random(40)
    for _ in range(3000):
        h = [rng.randrange(4) for _ in range(rng.randrange(12))]
        expected = largest_rectangle_brute(h)
        assert largest_rectangle(h) == expected
        assert largest_rectangle_two_pass(h) == expected

    grid = [[1, 0, 1, 0, 0],
            [1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 0, 0, 1, 0]]
    assert maximal_rectangle(grid) == 6
    assert maximal_rectangle([]) == 0
    assert maximal_rectangle([[0]]) == 0
    assert maximal_rectangle([[1, 1], [1, 1]]) == 4
    for _ in range(800):
        R, C = rng.randrange(1, 5), rng.randrange(1, 6)
        grid = [[int(rng.random() < 0.7) for _ in range(C)] for _ in range(R)]
        assert maximal_rectangle(grid) == maximal_rectangle_brute(grid)


if __name__ == "__main__":
    main()
```

Largest rectangle: each bar is pushed once and popped once, `O(n)` time and stack space. Maximal rectangle: one `O(C)` height update and one `O(C)` histogram per row, `O(R · C)` time and `O(C)` extra space.

## 3. Sum of subarray minimums: count each element's share

**Problem.** Add up the minimum of **every** nonempty subarray.

For `[3, 1, 2, 4]`, there are 10 subarrays:

| Subarray | `[3]` | `[3,1]` | `[3,1,2]` | `[3,1,2,4]` | `[1]` | `[1,2]` | `[1,2,4]` | `[2]` | `[2,4]` | `[4]` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Minimum | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |

The sum is 17.

**Brute force.** For each start, extend the end while keeping a running minimum: `O(n²)` time. With `n = 3 × 10⁴` that is `4.5 × 10⁸` steps, too slow.

### The key observation: swap the order of the loops

The brute force asks "for each subarray, what is its minimum?". Ask the reverse: "for each element, **in how many subarrays is it the minimum**?". Call that count `ways[i]`. Then each subarray is counted once, through its minimum:

$$
\sum_{\text{subarrays } S}\min(S)=\sum_{i}nums[i]\cdot ways[i].
$$

In the table, the `1` at index 1 is the minimum of 6 subarrays, contributing `1 × 6`. Counting `ways[i]` is the histogram question of §1 in disguise: element `i` is the minimum of a subarray exactly when the subarray contains `i` and stays strictly between the nearest smaller elements on each side. If those are at `L[i]` and `R[i]`:

- the start can be any of `L[i] + 1, …, i`: that is `i − L[i]` choices;
- the end can be any of `i, …, R[i] − 1`: that is `R[i] − i` choices;
- the choices are independent, so

$$
ways[i]=(i-L[i])\cdot(R[i]-i).
$$

For index 1 of `[3, 1, 2, 4]`: nothing smaller on either side, so `L = −1`, `R = 4`, and `ways = 2 × 3 = 6`. ✓

There is one catch, and it is the whole difficulty of this problem: what does "smaller" mean when values repeat?

## 4. Ties: every subarray needs exactly one owner

Try `[2, 2]`. Its subarrays are `[2]`, `[2]`, and `[2, 2]`, so the true sum is `2 + 2 + 2 = 6`. The subarray `[2, 2]` has **two** minimum positions. Which index gets credit for it?

| `L[i]` is the previous… | `R[i]` is the next… | `ways` for index 0, 1 | Computed sum | What went wrong |
|---|---|---|---:|---|
| `<` (strictly smaller) | `<` (strictly smaller) | 2, 2 | 8 | both indices claim `[2, 2]` |
| `<=` | `<=` | 1, 1 | 4 | neither claims `[2, 2]` |
| `<` | `<=` | 1, 2 | **6** | index 1 (the rightmost minimum) owns it |
| `<=` | `<` | 2, 1 | **6** | index 0 (the leftmost minimum) owns it |

The fix is to break ties on purpose: **one side strict, the other side not**. With "previous `<`, next `<=`":

- `R[i]` stops at the next element `<= nums[i]`, so a subarray owned by `i` never contains an equal value to the right of `i`;
- `L[i]` stops only at a strictly smaller element, so equal values to the left of `i` are allowed.

So `i` owns exactly the subarrays where it is the **rightmost** position of the minimum. Every subarray has exactly one rightmost minimum position, so every subarray is counted exactly once. The other mixed convention picks the leftmost minimum and is equally correct. Both-strict and both-non-strict are wrong.

### One pass gives exactly the mixed convention

Scan left to right with a stack whose values strictly increase, popping while `nums[top] >= x`:

- The element `j` that pops `i` is the first later element `<= nums[i]`: that is `R[i]` (next `<=`).
- The element below `i` on the stack is strictly smaller than `nums[i]`, and everything between them was popped by values `<=` themselves, so it is the previous strictly smaller element: `L[i]` (previous `<`).

So each pop can add its contribution at once. A virtual `−∞` at index `n` flushes the stack.

### Worked trace

`nums = [3, 1, 2, 4]`. Stack bottom to top as `index:value`.

| `j` | Value | Popped `i` | `L[i]` | `R[i] = j` | `(i − L)(R − i)` | Contribution | Total | Stack after |
|---:|---:|---|---:|---:|---|---:|---:|---|
| 0 | 3 | — | | | | | 0 | `0:3` |
| 1 | 1 | `0:3` | −1 | 1 | 1 × 1 | 3 | 3 | `1:1` |
| 2, 3 | 2, 4 | — | | | | | 3 | `1:1  2:2  3:4` |
| 4 | −∞ | `3:4` | 2 | 4 | 1 × 1 | 4 | 7 | |
|   |    | `2:2` | 1 | 4 | 1 × 2 | 4 | 11 | |
|   |    | `1:1` | −1 | 4 | 2 × 3 | 6 | 17 | empty |

Total 17, matching the table in §3. The ownership counts `1 + 1 + 2 + 6 = 10` add up to the number of subarrays, `4 · 5 / 2`, which is a useful check.

The code follows §5, together with its mirror image for maxima.

**Why it's correct.** Every nonempty subarray has exactly one rightmost position `i` of its minimum. That subarray cannot reach past `L[i]` (a smaller value would become the minimum) or reach `R[i]` (an equal or smaller value to the right of `i` would make `i` not the rightmost minimum). Conversely, any start in `L[i] + 1 .. i` and end in `i .. R[i] − 1` gives a subarray whose rightmost minimum is `i`. So the `ways[i]` sets split all subarrays into disjoint groups, one per owner, with nothing missed.

**Modulus and overflow.** Versions that ask for the answer modulo `10⁹ + 7` apply it to each contribution and the running total. In a fixed-width language `nums[i] · (i − L) · (R − i)` can reach about `10⁹ · 10¹⁰`: multiply in 64 bits and reduce after each multiplication.

## 5. Sum of subarray ranges

**Problem.** The **range** of a subarray is its maximum minus its minimum. Add up the ranges of all subarrays. For `[1, 3, 3]`: the subarrays `[1,3]` and `[1,3,3]` have range 2, the rest have range 0, so the answer is 4.

**Observation.** The sum of differences is a difference of sums:

$$
\sum_S\big(\max(S)-\min(S)\big)=\sum_S\max(S)-\sum_S\min(S).
$$

The sum of maxima is the mirror image of §4: a stack with strictly decreasing values, popping while `nums[top] <= x`, so each maximum is owned by its rightmost position (previous `>`, next `>=`). A shortcut reuses the minimum routine: `max(S) = −min(−S)`, so `sum of maxima = −sum_subarray_mins([−x for x in nums])`.

### Code for §4 and §5

```python
import math
import random


def ownership_counts(nums: list[int]) -> list[int]:
    """ways[i] = number of subarrays whose rightmost minimum is at index i."""
    n = len(nums)
    ways = [0] * n
    stack: list[int] = []                     # values strictly increasing bottom -> top
    for j in range(n + 1):                    # j == n is the virtual -inf that flushes
        while stack and (j == n or nums[stack[-1]] >= nums[j]):
            i = stack.pop()
            left = stack[-1] if stack else -1  # previous strictly smaller
            ways[i] = (i - left) * (j - i)     # j = next smaller-or-equal
        stack.append(j)
    return ways


def sum_subarray_mins(nums: list[int]) -> int:
    """Exact sum of min over all nonempty subarrays."""
    return sum(x * w for x, w in zip(nums, ownership_counts(nums)))


def sum_subarray_maxs(nums: list[int]) -> int:
    """Mirror image: previous strictly greater, next greater-or-equal."""
    total, stack, n = 0, [], len(nums)
    for j in range(n + 1):
        x = nums[j] if j < n else math.inf
        while stack and nums[stack[-1]] <= x:
            i = stack.pop()
            total += nums[i] * (i - (stack[-1] if stack else -1)) * (j - i)
        stack.append(j)
    return total


def sum_subarray_ranges(nums: list[int]) -> int:
    return sum_subarray_maxs(nums) - sum_subarray_mins(nums)


def sum_subarray_ranges_brute(nums: list[int]) -> int:
    total = 0
    for l in range(len(nums)):
        for r in range(l, len(nums)):
            total += max(nums[l:r + 1]) - min(nums[l:r + 1])
    return total


def sum_subarray_mins_brute(nums: list[int]) -> int:
    total = 0
    for l in range(len(nums)):
        low = nums[l]
        for r in range(l, len(nums)):
            low = min(low, nums[r])
            total += low
    return total


def main():
    assert sum_subarray_mins([3, 1, 2, 4]) == 17
    assert sum_subarray_mins([2, 2]) == 6
    assert sum_subarray_mins([11, 81, 94, 43, 3]) == 444
    assert sum_subarray_mins([-1, -2]) == -5
    assert sum_subarray_mins([]) == 0
    assert ownership_counts([3, 1, 2, 4]) == [1, 6, 2, 1]
    assert ownership_counts([2, 2]) == [1, 2]

    rng = random.Random(42)
    for _ in range(3000):
        nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(12))]
        assert sum_subarray_mins(nums) == sum_subarray_mins_brute(nums), nums
        n = len(nums)
        assert sum(ownership_counts(nums)) == n * (n + 1) // 2

    assert sum_subarray_ranges([1, 2, 3]) == 4
    assert sum_subarray_ranges([1, 3, 3]) == 4
    assert sum_subarray_ranges([4, -2, -3, 4, 1]) == 59
    assert sum_subarray_ranges([]) == 0
    for _ in range(3000):
        nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(11))]
        assert sum_subarray_ranges(nums) == sum_subarray_ranges_brute(nums)
        assert sum_subarray_maxs(nums) == -sum_subarray_mins([-x for x in nums])


if __name__ == "__main__":
    main()
```

`O(n)` time and space for each sum, by the push-once, pop-once count. The negation shortcut is exact for Python integers. In a fixed-width language, negating the most negative integer overflows, so write the maximum pass directly as `sum_subarray_maxs` does.

## 6. Two kinds of tie rule

Sections 1 and 4 both use nearest-smaller boundaries, but they treat equal values differently, and copying one rule into the other is a classic bug:

| Task | Combines candidates by | Equal values may… | Tie rule |
|---|---|---|---|
| Largest rectangle (§1) | `max` | produce extra, narrower candidates; harmless | any consistent strictness works |
| Sum of subarray minimums (§4) | `+` | double count or drop subarrays; wrong answer | exactly one side strict |

A quick test for any contribution formula: run it on `[x, x]` and `[x, x, x]`, and check that the ownership counts add up to `n(n + 1) / 2`.

## 7. Pitfalls and practice

1. Using strict comparisons on both sides (or non-strict on both) in a contribution sum. Equal values must have exactly one owner.
2. Mixing up the widths. A rectangle limited by bar `i` covers `L + 1 .. R − 1`, which is `R − L − 1` bars. A subarray count uses `(i − L) · (R − i)`, not the width.
3. Forgetting to flush the stack at the end. Bars or elements that are never popped by a real element still own rectangles or subarrays. A virtual element at index `n` handles it.
4. A flush value that does not pop everything. It must lose every comparison: `−1` for nonnegative heights popped on `>`, `−∞` for contribution sums over values that may be negative. With a virtual `0` and a pop on `>`, zero-height bars stay on the stack. That is harmless for a maximum (their area is 0), but in a contribution sum every element left on the stack loses its share.
5. Indexing with the sentinel `−1`. In Python, `nums[−1]` silently reads the last element.
6. Overflow in fixed-width languages: the product `value · left choices · right choices` needs 64 bits or a modulus applied in the right places.
7. Negating to reuse a minimum routine in a language where the most negative integer has no positive counterpart.

Practice: largest rectangle in histogram; maximal rectangle; count submatrices with all ones; sum of subarray minimums; sum of subarray ranges; sum of total strength of wizards (contributions with prefix sums of prefix sums); maximum subarray min-product (boundaries plus prefix sums); number of subarrays with bounded maximum; count subarrays where the first element is the minimum; minimum cost tree from leaf values (greedy with a monotonic stack).

Back to the folder overview: [Monotonic Stacks and Deques](README.md).
