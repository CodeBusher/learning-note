# Beyond Sorted Arrays — Rotations, Peaks, Matrices and Medians

## 1. Rotated sorted arrays

### 1.1 Finding the minimum

**Problem.** A sorted array of distinct values was **rotated**: a prefix was cut off and moved to the end, so `[0, 1, 2, 4, 5, 6, 7]` might become `[4, 5, 6, 7, 0, 1, 2]`. Find the smallest value (0, at index 4). Scanning is O(n).

**The key observation.** Compare each element with the **last** one, `a[-1] = 2`:

```text
index      :  0  1  2  3  4  5  6
a          :  4  5  6  7  0  1  2
a[i] <= 2 ?:  F  F  F  F  T  T  T
```

The elements before the minimum came from the end of the original list, so all are larger than `a[-1]`; the elements from the minimum on are its start, so all are `≤ a[-1]`. So "`a[i] ≤ a[-1]`" is monotone and its first `True` is the minimum. An unrotated array is all `True`, and the answer 0 is still right.

**Trace** with `first_true(0, 7, lambda i: a[i] <= a[-1])`:

| Step | `lo` | `hi` | `mid` | `a[mid]` | `a[mid] ≤ 2`? | Action |
|---:|---:|---:|---:|---:|---|---|
| 1 | 0 | 7 | 3 | 7 | F | `lo = 4` |
| 2 | 4 | 7 | 5 | 1 | T | `hi = 5` |
| 3 | 4 | 5 | 4 | 0 | T | `hi = 4` → minimum at index 4 |

### 1.2 Searching for a target

**Problem.** Return the index of `target` in the rotated array, or −1.

**Two steps.** Find the rotation point `p` as above. `a[:p]` and `a[p:]` are each sorted, and `a[0]` tells you which one can hold `target`; run a lower bound there.

**One pass.** Around any `mid`, at least one side is sorted. If `a[lo] ≤ a[mid]`, the left part `a[lo..mid]` contains no drop, so it is sorted and its two ends tell you whether `target` is inside it. Otherwise the right part `a[mid..hi−1]` is sorted. For `target = 0`:

| Step | `lo` | `hi` | `mid` | `a[mid]` | Sorted part | 0 inside it? | Action |
|---:|---:|---:|---:|---:|---|---|---|
| 1 | 0 | 7 | 3 | 7 | left `4..7` | no | `lo = 4` |
| 2 | 4 | 7 | 5 | 1 | left `0..1` | yes | `hi = 5` |
| 3 | 4 | 5 | 4 | 0 | — | found | return 4 |

### 1.3 With duplicates

Duplicates break the predicate. In `[2, 2, 2, 0, 2]` every element is `≤ a[-1]`, yet the minimum is at index 3. `[2, 0, 2, 2, 2]` has the same ends and the same middle, with the minimum on the other side: when `a[mid]` equals the value it is compared with, the side of the drop is unknowable.

The fix compares `a[mid]` with `a[hi]` in a **closed** range `[lo, hi]` (it needs the actual right-end element) and shrinks by one on a tie:

- `a[mid] > a[hi]`: the drop is right of `mid`: `lo = mid + 1`.
- `a[mid] < a[hi]`: `a[mid..hi]` is sorted, so the minimum is at `mid` or left of it: `hi = mid`.
- `a[mid] == a[hi]`: `hi -= 1`. Safe, because `a[mid]` has the same value and stays in range.

| Step | `lo` | `hi` | `mid` | `a[mid]` vs `a[hi]` | Action |
|---:|---:|---:|---:|---|---|
| 1 | 0 | 4 | 2 | 2 = 2 | `hi = 3` |
| 2 | 0 | 3 | 1 | 2 > 0 | `lo = 2` |
| 3 | 2 | 3 | 2 | 2 > 0 | `lo = 3` → minimum `a[3] = 0` |

The price is O(n) in the worst case, as on `[1, 1, …, 1, 0, 1]`. No algorithm does better: an all-ones array with one hidden 0 needs every position checked. The one-pass target search survives duplicates with the same fix: shrink both ends when `a[lo] == a[mid] == a[hi]`.

**Time:** O(log n) for distinct values; O(n) worst case with duplicates. **Space:** O(1). The code is in the script after §2.

## 2. Finding a peak

**Problem.** A **peak** is an element larger than both neighbors, with positions outside the array counting as −∞. Adjacent elements differ. Return any peak. In `a = [1, 2, 1, 3, 5, 6, 4]`, indexes 1 and 5 are peaks. Checking every index is O(n).

**The key observation.** Look at "does the array go down right after `i`?", `a[i] > a[i + 1]`, for `i` in `[0, n − 1)`:

```text
index          :  0  1  2  3  4  5  6
a              :  1  2  1  3  5  6  4
a[i] > a[i+1] ?:  F  T  F  F  F  T  (index 6 counts as T: a[7] is -inf)
```

`F T F F F T` is **not** monotone, yet binary search still works. The `first_true` loop keeps this invariant for **any** predicate:

> `lo` is the start, or `ok(lo − 1)` is false; and `hi` is the end, or `ok(hi)` is true.

Each step only moves `lo` past a `False` or `hi` onto a `True`. So the loop ends on an index `i` where the array does not go down at `i − 1` but goes down at `i`: `a[i − 1] < a[i] > a[i + 1]`, a peak. For a monotone predicate this boundary is the unique first `True`; otherwise it is *some* `F → T` boundary, and here every such boundary is a peak.

**Trace** with `first_true(0, 6, lambda i: a[i] > a[i + 1])`:

| Step | `lo` | `hi` | `mid` | `a[mid]`, `a[mid+1]` | Down? | Action |
|---:|---:|---:|---:|---|---|---|
| 1 | 0 | 6 | 3 | 3, 5 | F | `lo = 4` |
| 2 | 4 | 6 | 5 | 6, 4 | T | `hi = 5` |
| 3 | 4 | 5 | 4 | 5, 6 | F | `lo = 5` → peak at 5 |

Step 1 discards the left half, which holds a peak. That's fine: the climb from index 3 to 4 guarantees a peak to the right, and one is enough.

Code for §1 and §2, against brute force on random rotated arrays:

```python
import random


def first_true(lo: int, hi: int, ok) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def rotation_point(a: list[int]) -> int:
    """Index of the minimum of a rotated sorted array of distinct values."""
    if not a:
        raise ValueError("empty array")
    return first_true(0, len(a), lambda i: a[i] <= a[-1])


def search_one_pass(a: list[int], target: int) -> int:
    lo, hi = 0, len(a)  # Half-open; a[hi - 1] is the last candidate.
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] == target:
            return mid
        if a[lo] <= a[mid]:  # a[lo..mid] is sorted.
            if a[lo] <= target < a[mid]:
                hi = mid
            else:
                lo = mid + 1
        else:  # a[mid..hi-1] is sorted.
            if a[mid] < target <= a[hi - 1]:
                lo = mid + 1
            else:
                hi = mid
    return -1


def min_with_duplicates(a: list[int]) -> int:
    if not a:
        raise ValueError("empty array")
    lo, hi = 0, len(a) - 1  # Closed: the minimum is in a[lo..hi].
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] > a[hi]:
            lo = mid + 1
        elif a[mid] < a[hi]:
            hi = mid
        else:
            hi -= 1
    return a[lo]


def contains_with_duplicates(a: list[int], target: int) -> bool:
    lo, hi = 0, len(a) - 1  # Closed range.
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if a[mid] == target:
            return True
        if a[lo] == a[mid] == a[hi]:
            lo += 1
            hi -= 1
        elif a[lo] <= a[mid]:  # Left part is sorted.
            if a[lo] <= target < a[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:  # Right part is sorted.
            if a[mid] < target <= a[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return False


def find_peak(a: list[int]) -> int:
    if not a:
        raise ValueError("empty array")
    return first_true(0, len(a) - 1, lambda i: a[i] > a[i + 1])


def is_peak(a: list[int], i: int) -> bool:
    left = a[i - 1] if i > 0 else float("-inf")
    right = a[i + 1] if i + 1 < len(a) else float("-inf")
    return left < a[i] > right


def main():
    a = [4, 5, 6, 7, 0, 1, 2]
    assert rotation_point(a) == 4
    assert search_one_pass(a, 0) == 4 and search_one_pass(a, 3) == -1
    assert min_with_duplicates([2, 2, 2, 0, 2]) == 0
    assert contains_with_duplicates([2, 5, 6, 0, 0, 1, 2], 0)

    rng = random.Random(14)
    for _ in range(3000):
        n, k = rng.randint(1, 10), rng.randint(0, 9)
        b = sorted(rng.sample(range(-20, 20), n))
        distinct = b[k % n:] + b[:k % n]
        target = rng.randint(-22, 22)
        assert rotation_point(distinct) == distinct.index(min(distinct))
        expected = distinct.index(target) if target in distinct else -1
        assert search_one_pass(distinct, target) == expected

        b = sorted(rng.randint(0, 4) for _ in range(n))
        dups = b[k % n:] + b[:k % n]
        assert min_with_duplicates(dups) == min(dups)
        assert contains_with_duplicates(dups, target % 6) == (target % 6 in dups)

    assert find_peak([1, 2, 1, 3, 5, 6, 4]) == 5
    assert find_peak([7]) == 0 and find_peak([1, 2, 3]) == 2 and find_peak([3, 2, 1]) == 0

    for _ in range(3000):
        a = [rng.randint(0, 6)]
        for _ in range(rng.randint(0, 12)):
            a.append(rng.choice([v for v in range(7) if v != a[-1]]))  # Neighbors differ.
        assert is_peak(a, find_peak(a))


if __name__ == "__main__":
    main()
```

**Time:** O(log n). **Space:** O(1).

With equal neighbors the guarantee breaks: on a flat stretch like `[1, 1, 1, 2, 1, 1]` a step can't tell where the peak is, and the worst case is O(n). The same idea finds a local minimum, and a peak in a 2D grid (binary search on columns, taking each column's maximum).

## 3. Searching a sorted matrix

Two different matrices are called "sorted", and they need different methods.

**Rows chained together.** Each row is sorted and starts after the previous row ends, so read row by row it is one sorted list:

```text
[ 1,  3,  5,  7]
[10, 11, 16, 20]      flattened: 1 3 5 7 10 11 16 20 23 30 34 60
[23, 30, 34, 60]      index k  ->  row k // 4, column k % 4
```

Run an ordinary lower bound over the virtual indexes `0 … R·C − 1`, reading index `k` as `matrix[k // C][k % C]`. Nothing is copied, and the trace is the lower-bound trace of [Boundaries](02-boundaries.md). O(log(R·C)).

**Rows and columns sorted separately.** Every row increases left to right and every column top to bottom, but a row may start below the previous row's end:

```text
[ 1,  4,  7, 11, 15]
[ 2,  5,  8, 12, 19]
[ 3,  6,  9, 16, 22]
[10, 13, 14, 17, 24]
[18, 21, 23, 26, 30]
```

Flattening no longer gives a sorted list. Start at the **top-right** corner instead: the largest cell of its row and the smallest of its column.

- Bigger than `target`: everything below it in this column is bigger still. Discard the column: move left.
- Smaller than `target`: everything left of it in this row is smaller still. Discard the row: move down.

Each step discards a row or a column, so at most `R + C` steps. For `target = 5`:

| Step | (row, col) | Value | vs 5 | Move |
|---:|---|---:|---|---|
| 1 | (0, 4) | 15 | bigger | left |
| 2 | (0, 3) | 11 | bigger | left |
| 3 | (0, 2) | 7 | bigger | left |
| 4 | (0, 1) | 4 | smaller | down |
| 5 | (1, 1) | 5 | equal | found |

This **staircase** walk is not a halving search. Binary searching each row is O(R log C), better when the matrix is very wide and short.

```python
import random


def search_chained(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    lo, hi = 0, rows * cols
    while lo < hi:  # Lower bound over the virtual flattened list.
        mid = lo + (hi - lo) // 2
        r, c = divmod(mid, cols)
        if matrix[r][c] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo < rows * cols and matrix[lo // cols][lo % cols] == target


def search_staircase(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    r, c = 0, len(matrix[0]) - 1
    while r < len(matrix) and c >= 0:
        value = matrix[r][c]
        if value == target:
            return True
        if value > target:
            c -= 1  # Whole column below is too big.
        else:
            r += 1  # Whole row to the left is too small.
    return False


def main():
    chained = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_chained(chained, 3) and not search_chained(chained, 13)
    grid = [[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22],
            [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]]
    assert search_staircase(grid, 5) and not search_staircase(grid, 20)
    assert not search_chained([], 1) and not search_staircase([[]], 1)

    rng = random.Random(16)
    for _ in range(2000):
        rows, cols = rng.randint(1, 5), rng.randint(1, 5)
        flat = sorted(rng.sample(range(60), rows * cols))
        m = [flat[r * cols:(r + 1) * cols] for r in range(rows)]
        t = rng.randint(-1, 61)
        assert search_chained(m, t) == (t in flat)

        g = [[0] * cols for _ in range(rows)]  # Random rows-and-columns-sorted grid.
        for r in range(rows):
            for c in range(cols):
                g[r][c] = max(g[r - 1][c] if r else 0, g[r][c - 1] if c else 0) + rng.randint(0, 3)
        t = rng.randint(-1, 25)
        assert search_staircase(g, t) == any(t in row for row in g)


if __name__ == "__main__":
    main()
```

**Time:** O(log(RC)) chained; O(R + C) staircase. **Space:** O(1).

## 4. Advanced: the median of two sorted arrays

**Problem.** Given sorted arrays `A` and `B` with `m` and `n` elements, find the median of all of them together in O(log(min(m, n))). The **median** of `t` sorted values is the middle one if `t` is odd, and the average of the two middle ones if `t` is even. For `A = [1, 3, 8, 9, 15]`, `B = [7, 11, 18, 19, 21, 25]`, the merged list is `1 3 7 8 9 11 15 18 19 21 25` and the median is 11. Merging is O(m + n).

**The key observation: cut both arrays.** The median splits the merged list into a left and a right half. The left half is some prefix `A[:i]` plus some prefix `B[:j]`. Fix its size to `half = (m + n + 1) // 2`; then `j = half − i`, and the only unknown is `i`, with `0 ≤ i ≤ m`.

```text
A:  1  3  8  9 | 15                 i = 4  (A[:4] on the left)
B:  7 11 | 18 19 21 25              j = 2  (B[:2] on the left)

left  = {1, 3, 8, 9, 7, 11}   max = 11
right = {15, 18, 19, 21, 25}  min = 15
```

A cut is **correct** when every left element is `≤` every right element. Each array is sorted, so only the cross pairs need checking:

$$
A[i-1]\le B[j]\qquad\text{and}\qquad B[j-1]\le A[i].
$$

Missing elements count as −∞ on the left and +∞ on the right. With a correct cut, the median is the left maximum (odd total), or the average of the left maximum and the right minimum (even total).

**The monotone predicate.** Let `ok(i)` be "`B[j − 1] ≤ A[i]`" (true if `i = m` or `j = 0`). As `i` grows, `A[i]` grows and `B[j − 1] = B[half − i − 1]` shrinks, so `ok` is `F … F T … T`. At its **first** `True`, `ok(i)` is the second condition, and `ok(i − 1)` being false (or `i = 0`) says `A[i − 1] < B[j]`, the first. So the first `True` is exactly the correct cut. Search `i` in `[0, m)`; if nothing is true, `first_true` returns `m`, which is then the cut. Searching over the **shorter** array keeps `j` inside `[0, n]` and gives the O(log(min(m, n))) bound.

**Trace**: `m = 5`, `n = 6`, `half = 6`.

| Step | `lo` | `hi` | `i` | `j` | `A[i]` | `B[j−1]` | `B[j−1] ≤ A[i]`? | Action |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 0 | 5 | 2 | 4 | 8 | 19 | F | `lo = 3` |
| 2 | 3 | 5 | 4 | 2 | 15 | 11 | T | `hi = 4` |
| 3 | 3 | 4 | 3 | 3 | 9 | 18 | F | `lo = 4` → `i = 4`, `j = 2` |

Check: `A[3] = 9 ≤ B[2] = 18` and `B[1] = 11 ≤ A[4] = 15`. The total is odd, so the median is the left maximum, `max(9, 11) = 11`.

**Even total.** For `A = [1, 2]`, `B = [3, 4]`, `half = 2`: at `i = 1`, `B[0] = 3 ≤ A[1] = 2` is false, so the cut is `i = 2`, `j = 0`, and the median is `(2 + 3) / 2 = 2.5`.

```python
import math
import random


def first_true(lo: int, hi: int, ok) -> int:
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def median_two_sorted(a: list[int], b: list[int]) -> float:
    if len(a) > len(b):
        a, b = b, a  # Search over the shorter array.
    m, n = len(a), len(b)
    if m + n == 0:
        raise ValueError("both arrays are empty")
    half = (m + n + 1) // 2

    def ok(i: int) -> bool:
        j = half - i
        return i == m or j == 0 or b[j - 1] <= a[i]

    i = first_true(0, m, ok)
    j = half - i
    left_max = max(a[i - 1] if i > 0 else -math.inf, b[j - 1] if j > 0 else -math.inf)
    if (m + n) % 2 == 1:
        return left_max
    right_min = min(a[i] if i < m else math.inf, b[j] if j < n else math.inf)
    return (left_max + right_min) / 2


def median_brute(a: list[int], b: list[int]) -> float:
    merged = sorted(a + b)
    t = len(merged)
    return merged[t // 2] if t % 2 else (merged[t // 2 - 1] + merged[t // 2]) / 2


def main():
    assert median_two_sorted([1, 3, 8, 9, 15], [7, 11, 18, 19, 21, 25]) == 11
    assert median_two_sorted([1, 2], [3, 4]) == 2.5
    assert median_two_sorted([], [5]) == 5
    assert median_two_sorted([2, 2], [2]) == 2

    rng = random.Random(17)
    for _ in range(5000):
        a = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 7)))
        b = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 7)))
        if a or b:
            assert median_two_sorted(a, b) == median_brute(a, b)


if __name__ == "__main__":
    main()
```

**Time:** O(log(min(m, n))). **Space:** O(1).

**Variant.** The same cut finds the **k-th smallest** of the union: use `half = k`, with `i` restricted so that `0 ≤ j ≤ n`.

## 5. Summary

Binary search needs less than a sorted array: only a test at `mid` that says for certain which half can't hold an answer. The `first_true` loop always ends on *some* `F → T` boundary, monotone predicate or not, so it applies whenever any such boundary is a valid answer.

| Problem | Test at `mid` | Range | Time |
|---|---|---|---|
| Minimum of a rotated array | `a[mid] ≤ a[-1]` (first `True`) | half-open | O(log n) |
| Target in a rotated array | which side is sorted, is the target inside it | half-open | O(log n) |
| Rotated array with duplicates | `a[mid]` vs `a[hi]`, `hi -= 1` on a tie | closed | O(n) worst |
| Any peak, neighbors differ | `a[mid] > a[mid + 1]` (any `F → T`) | half-open | O(log n) |
| Matrix, rows chained | lower bound on the flattened index | half-open | O(log(RC)) |
| Matrix, rows and columns sorted | staircase from the top-right corner | — | O(R + C) |
| Median of two sorted arrays | `B[j − 1] ≤ A[i]`, `j = half − i` | half-open, shorter array | O(log min(m, n)) |

## 6. Pitfalls and practice

1. **Using `a[i] ≤ a[-1]` on a rotated array with duplicates.** It is no longer monotone. Use the shrink-by-one version and accept O(n) worst case.
2. **Mixing closed and half-open ranges.** The duplicate-tolerant rotated searches compare against `a[hi]`, so they use a closed range; the others are half-open. Keep each function consistent.
3. **Equal neighbors in peak finding.** The argument needs strict inequalities.
4. **Mixing up the two matrix shapes.** Flattening works only when each row starts after the previous row ends.
5. **Searching the longer array in the median problem.** `j = half − i` can go negative or past `n`.
6. **Forgetting the empty sides of a cut.** A cut at `i = 0` or `i = m` has an empty part; missing elements are −∞ on the left and +∞ on the right.

Practice: find minimum in rotated sorted array (I and II); search in rotated sorted array (I and II); find peak element; peak index in a mountain array; find a peak element II (2D); search a 2D matrix (I and II); kth smallest element in a sorted matrix; median of two sorted arrays; k-th element of two sorted arrays.

Next: [Real Numbers and Unbounded Ranges](05-reals-ternary-and-unbounded.md).
