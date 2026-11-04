# Prefix Sums and Difference Arrays — Answer Range Questions with One Subtraction

## 1. The problem and the brute force

A small shop records its sales for seven days:

| Day `i` | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sales `a[i]` | 3 | 1 | 4 | 1 | 5 | 9 | 2 |

The manager asks many questions of the form "what were the total sales from day `l` through day `r`?". Both ends are included, so the range is **inclusive** `[l, r]`; every range API in this folder works this way ([conventions](README.md#conventions)). Days 2 through 5 give `4 + 1 + 5 + 9 = 19`; days 0 through 3 give `3 + 1 + 4 + 1 = 9`.

**Brute force.** Add the elements of the range one by one. One question costs up to `n` additions, so `q` questions cost up to `n · q`: ten billion for `n = q = 100,000`. The array **never changes** between questions, so the brute force keeps re-adding the same numbers. That repeated work is what we remove.

## 2. The observation: every range is a difference of two running totals

Write down the **running total** before each day: the total of everything that came earlier.

```text
day i          0    1    2    3    4    5    6
a[i]           3    1    4    1    5    9    2
running     0    3    4    8    9   14   23   25
            ↑    ↑    ↑    ↑    ↑    ↑    ↑    ↑
           P[0] P[1] P[2] P[3] P[4] P[5] P[6] P[7]
```

Each running total sits on the boundary *between* two days. `P[k]` is the total of the first `k` days, that is, of `a[0], …, a[k − 1]` (the prefix `a[:k]`). This array is called the **prefix-sum array**. It has `n + 1` entries, one for each boundary, including the boundary before day 0.

Now look at the question "days 2 through 5":

```text
day i          0    1    2    3    4    5    6
a[i]           3    1  [ 4    1    5    9 ]  2
            |---- P[2] = 4 ----|
            |---------------- P[6] = 23 ---------------|
```

`P[6]` adds days 0 to 5. `P[2]` adds days 0 to 1. Subtract, and days 0 and 1 cancel, leaving days 2 to 5:

$$
\operatorname{sum}(l, r) = P[r+1] - P[l].
$$

For days 2 through 5: `P[6] − P[2] = 23 − 4 = 19`. ✓
For days 0 through 3: `P[4] − P[0] = 9 − 0 = 9`. ✓

**Invariant.** `P[k]` is the sum of the first `k` elements; in symbols,

$$
P[0] = 0, \qquad P[k] = a[0] + a[1] + \dots + a[k-1].
$$

**Why does `P` start with 0?** `P[0]` is the total of zero days, the **empty prefix**, and that total is 0. It makes the formula work when `l = 0`: `sum(0, 3) = P[4] − P[0]`. Without it, ranges that start at day 0 would need a special case.

**Why `r + 1` and not `r`?** `P[k]` covers `k` elements, so to include day `r` we need the first `r + 1` days. The `+ 1` is where most off-by-one bugs live; draw the boundary picture above when in doubt.

**Building `P`** is one pass, `P[k + 1] = P[k] + a[k]`: the `running` row in the first picture. Two edge questions check the formula: `[4, 4]` is `P[5] − P[4] = 14 − 9 = 5`, a single day, and `[0, 6]` is `P[7] − P[0] = 25`, the whole week.

**Why it's correct.** Write the subtraction out for `l = 2`, `r = 5`:

```text
P[6] = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
P[2] = a[0] + a[1]
--------------------------------------------------
P[6] − P[2] =           a[2] + a[3] + a[4] + a[5]
```

Every element before `l` appears once in each total and cancels; every element from `l` to `r` appears only in `P[r + 1]`; nothing after `r` appears in either. Seen one element at a time, the same fact reads `a[i] = P[i + 1] − P[i]`: `a` is the step-by-step **change** of `P`, and `P` is the **accumulation** of `a`. §5 uses this in the other direction. Subtraction is what makes the trick work; §9 shows what goes wrong for minimum, which cannot be undone.

## 3. Code: `StaticRangeSum`

"Static" means the array never changes. The test compares the class with the brute force on random arrays with negatives, single elements and repeats.

```python
from random import Random


class StaticRangeSum:
    """Inclusive range sums over an array that never changes."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.prefix = [0] * (self.n + 1)  # prefix[k] = sum(nums[:k])
        for i, num in enumerate(nums):
            self.prefix[i + 1] = self.prefix[i] + num

    def query(self, l: int, r: int) -> int:
        """Sum of nums[l..r], both ends included, 0-based."""
        if not 0 <= l <= r < self.n:
            raise ValueError(f"bad range [{l}, {r}] for length {self.n}")
        return self.prefix[r + 1] - self.prefix[l]


def range_sum_brute(a: list[int], l: int, r: int) -> int:
    return sum(a[l:r + 1])


def main():
    rs = StaticRangeSum([3, 1, 4, 1, 5, 9, 2])
    assert rs.prefix == [0, 3, 4, 8, 9, 14, 23, 25]
    assert rs.query(2, 5) == 19
    assert rs.query(0, 3) == 9
    assert rs.query(4, 4) == 5
    assert rs.query(0, 6) == 25

    single = StaticRangeSum([-7])
    assert single.query(0, 0) == -7

    assert StaticRangeSum([]).prefix == [0]
    for bad in [(2, 1), (-1, 3), (0, 7)]:
        try:
            rs.query(*bad)
            raise AssertionError(f"expected ValueError for {bad}")
        except ValueError:
            pass

    rng = Random(1)
    for _ in range(300):
        n = rng.randint(1, 12)
        a = [rng.randint(-5, 5) for _ in range(n)]
        rs = StaticRangeSum(a)
        for _ in range(10):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            assert rs.query(l, r) == range_sum_brute(a, l, r)


if __name__ == "__main__":
    main()
```

Build O(n) time and space; each `query` is **O(1)**, so `q` questions cost O(n + q). Changing one `a[i]` costs O(n), because every `prefix[k]` with `k > i` shifts. That weakness motivates the [Fenwick Tree](02-fenwick-tree.md).

## 4. Counting with prefix sums

Many questions are not "what is the sum?" but "**how many** positions in `[l, r]` satisfy a condition?". Turn each position into 1 if it satisfies the condition and 0 otherwise. The count is then the sum of those 0/1 values, and `StaticRangeSum` answers it unchanged.

For `a = [4, 7, 2, 9, 6]` and the condition "is even":

```text
i              0   1   2   3   4
a[i]           4   7   2   9   6
is even        1   0   1   0   1
prefix      0   1   1   2   2   3
```

Even values in `[1, 4]`: `prefix[5] − prefix[1] = 3 − 1 = 2` (the values 2 and 6).

The same 0/1 trick counts vowels in a substring, zeros in a range, or values below a threshold. A count over **time** works the same way: put the number of events at each time `t` in an array, and a range sum counts the events in a time window. Each counter costs O(n) to build and O(1) per question, with no new code. The condition must be fixed when building: "how many values below `x` in `[l, r]`" with a different `x` each time needs sorting plus a [Fenwick tree](02-fenwick-tree.md) (offline) or a merge-sort tree.

## 5. Difference arrays: many range updates, one final read

### The problem

Now reverse the roles. A teacher has six students' scores:

```text
student i      0   1   2   3   4   5
score          1   2   3   4   5   6
```

Then many adjustments arrive, each of the form "add `delta` to every student from `l` through `r`":

1. `add(1, 3, +2)`
2. `add(2, 5, +3)`
3. `add(0, 1, −1)`

Only after **all** adjustments is the final list needed. The expected result is `[0, 3, 8, 9, 8, 9]`.

**Brute force.** Loop over the range for every adjustment: up to `n` writes each, O(n · q) in total.

### The observation: a range update changes only two neighbor differences

Look at the **gaps** between neighbors, `a[i] − a[i − 1]`, before and after one range update. Take `+2` on `[1, 3]`:

```text
i                0    1    2    3    4    5
before           1    2    3    4    5    6
after            1    4    5    6    5    6
gap before       1    1    1    1    1    1
gap after        1    3    1    1   −1    1
gap changed?          +2              −2
```

Inside the range every element rose by the same amount, so the gap between two neighbors **inside** the range did not move. The gap changed only at the two edges:

- At `l = 1`, the value jumps up by `delta` relative to its left neighbor.
- At `r + 1 = 4`, the extra `delta` stops, so the value drops by `delta` relative to its left neighbor.

So instead of writing `delta` into every position, record the change in the gaps. Call the array of recorded gap changes `d`:

$$
d[l] \mathrel{+}= \Delta, \qquad d[r+1] \mathrel{-}= \Delta.
$$

The total change at position `i` is then the running total `d[0] + d[1] + … + d[i]`, which is a prefix sum of `d`. Check that it gives the right change in every region:

| Position `i` | Which of `d[l]`, `d[r + 1]` are included in `d[0] + … + d[i]` | Total change at `i` |
|---|---|---:|
| `i < l` | neither | 0 |
| `l ≤ i ≤ r` | `d[l] = +Δ` only | `+Δ` |
| `i ≥ r + 1` | both, `+Δ − Δ` | 0 |

Two writes describe an update to any number of elements. This is the reverse of §2: prefix sums turn values into totals, and a **difference array** stores the changes whose prefix sums are the values.

**Invariant.** After any sequence of updates, `d[0] + … + d[i]` equals the total amount added to position `i` so far.

### Trace

`d` has one extra slot, `d[n]`, so that `d[r + 1] −= delta` is a valid write even when `r = n − 1`. The final read never looks at it.

| Update | Writes | `d[0..6]` after |
|---|---|---|
| start | — | `[ 0, 0, 0, 0,  0, 0,  0]` |
| `add(1, 3, +2)` | `d[1] += 2`, `d[4] −= 2` | `[ 0, 2, 0, 0, −2, 0,  0]` |
| `add(2, 5, +3)` | `d[2] += 3`, `d[6] −= 3` | `[ 0, 2, 3, 0, −2, 0, −3]` |
| `add(0, 1, −1)` | `d[0] −= 1`, `d[2] += 1` | `[−1, 2, 4, 0, −2, 0, −3]` |

Now compute the final array in one pass. `running` is the prefix sum of `d`, the total change at `i`:

| `i` | `d[i]` | `running` | original | final = original + running |
|---:|---:|---:|---:|---:|
| 0 | −1 | −1 | 1 | 0 |
| 1 | 2 | 1 | 2 | 3 |
| 2 | 4 | 5 | 3 | 8 |
| 3 | 0 | 5 | 4 | 9 |
| 4 | −2 | 3 | 5 | 8 |
| 5 | 0 | 3 | 6 | 9 |

The result `[0, 3, 8, 9, 8, 9]` is the expected one. `d[6] = −3` was never read.

### Code: `BatchRangeAdd`

```python
from random import Random


class BatchRangeAdd:
    """Collect many range additions, then build the final array once."""

    def __init__(self, nums: list[int]):
        self.nums = list(nums)
        # d[i] = change in the gap a[i] - a[i-1]; d[n] absorbs r + 1 == n.
        self.d = [0] * (len(nums) + 1)

    def add(self, l: int, r: int, delta: int) -> None:
        """Add delta to every element of [l, r], both ends included."""
        if not 0 <= l <= r < len(self.nums):
            raise ValueError(f"bad range [{l}, {r}]")
        self.d[l] += delta
        self.d[r + 1] -= delta

    def final_array(self) -> list[int]:
        """Apply every recorded addition and return the resulting array."""
        result = []
        running = 0  # total change at position i
        for i, num in enumerate(self.nums):
            running += self.d[i]
            result.append(num + running)
        return result


def brute(nums, updates):
    a = list(nums)
    for l, r, delta in updates:
        for i in range(l, r + 1):
            a[i] += delta
    return a


def main():
    batch = BatchRangeAdd([1, 2, 3, 4, 5, 6])
    batch.add(1, 3, 2)
    batch.add(2, 5, 3)
    batch.add(0, 1, -1)
    assert batch.d == [-1, 2, 4, 0, -2, 0, -3]
    assert batch.final_array() == [0, 3, 8, 9, 8, 9]

    whole = BatchRangeAdd([5, 5, 5])
    whole.add(0, 2, 10)              # r + 1 == n lands in the extra slot
    assert whole.final_array() == [15, 15, 15]

    assert BatchRangeAdd([]).final_array() == []

    try:
        BatchRangeAdd([1, 2]).add(1, 0, 5)
    except ValueError:
        pass
    else:
        raise AssertionError("reversed range accepted")

    rng = Random(3)
    for _ in range(300):
        n = rng.randint(1, 10)
        nums = [rng.randint(-5, 5) for _ in range(n)]
        updates = []
        batch = BatchRangeAdd(nums)
        for _ in range(rng.randint(0, 8)):
            l = rng.randrange(n)
            r = rng.randrange(l, n)
            delta = rng.randint(-4, 4)
            updates.append((l, r, delta))
            batch.add(l, r, delta)
        assert batch.final_array() == brute(nums, updates)


if __name__ == "__main__":
    main()
```

Each `add` is **O(1)**; `final_array()` is O(n); `q` updates followed by one read cost **O(n + q)** time and O(n) space.

### Why a difference array is not enough when reads and updates mix

Reading one current value means summing `d[0..i]`, which is O(n). If updates and reads alternate ("add to `[2, 5]`, what is `a[3]` now?, add to `[0, 1]`, what is `a[1]` now?"), each read costs O(n) again. A prefix-sum table over `d` would make reads O(1), but every update would then shift O(n) table entries.

This gap is exactly what the [Fenwick Tree](02-fenwick-tree.md) closes: it keeps prefix sums of `d` that survive updates, with O(log n) for both operations.

## 6. Two-dimensional prefix sums

### The problem

A grid of numbers with `R` rows and `C` columns. Many questions ask for the sum of a rectangle, given by its top-left cell `(r1, c1)` and bottom-right cell `(r2, c2)`, both included.

```text
          col 0  col 1  col 2  col 3
row 0       1      2      3      4
row 1       5      6      7      8
row 2       9      1      2      3
```

The rectangle from `(1, 1)` to `(2, 2)` is `6 + 7 + 1 + 2 = 16`. The brute force adds every cell in the rectangle, up to `R · C` per question.

### The observation: a rectangle is a difference of four corner rectangles

Define `S[r][c]` as the sum of the **top-left block** with `r` rows and `c` columns: rows `0..r − 1`, columns `0..c − 1`. As in 1D, `S` has an extra zero row and column for the empty block.

To get the target rectangle `T`, start from the big block that ends at its bottom-right corner, then remove what is above it and what is left of it:

```text
            c1        c2
      ┌─────┬──────────┐
      │  D  │    B     │          D = top-left corner block, S[r1][c1]
  r1  ├─────┼──────────┤          B = strip above T
      │     │          │          L = strip left of T
      │  L  │    T     │          T = the target rectangle
      │     │          │
  r2  └─────┴──────────┘

  S[r2+1][c2+1] = D + B + L + T     (everything)
  S[r1][c2+1]   = D + B             (the top band)
  S[r2+1][c1]   = D + L             (the left band)
  S[r1][c1]     = D                 (the corner)
```

Subtract the top band and the left band from everything. The corner `D` lies in both bands, so it was removed twice; add it back once:

$$
T = S[r_2+1][c_2+1] - S[r_1][c_2+1] - S[r_2+1][c_1] + S[r_1][c_1].
$$

This add-back-the-overlap rule is called **inclusion–exclusion**.

Building `S` uses the same picture with `T` shrunk to one cell: the block ending at `(r, c)` is the cell, plus the block above, plus the block to the left, minus their shared corner, which was counted twice:

$$
S[r+1][c+1] = grid[r][c] + S[r][c+1] + S[r+1][c] - S[r][c].
$$

### Trace

Fill `S` row by row. Row 0 and column 0 of `S` stay zero.

```text
S          c=0   c=1   c=2   c=3   c=4
r=0          0     0     0     0     0
r=1          0     1     3     6    10
r=2          0     6    14    24    36
r=3          0    15    24    36    51
```

For example `S[2][2] = 6 + 3 + 6 − 1 = 14` (cell, above, left, minus corner).

Rectangle `(1, 1)` to `(2, 2)`: `S[3][3] − S[1][3] − S[3][1] + S[1][1] = 36 − 6 − 15 + 1 = 16`. ✓

### Code: `StaticRangeSum2D`

```python
from random import Random


class StaticRangeSum2D:
    """Inclusive rectangle sums over a grid that never changes."""

    def __init__(self, grid: list[list[int]]):
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        if any(len(row) != self.cols for row in grid):
            raise ValueError("grid rows must have equal length")
        s = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for r in range(self.rows):
            for c in range(self.cols):
                s[r + 1][c + 1] = grid[r][c] + s[r][c + 1] + s[r + 1][c] - s[r][c]
        self.s = s

    def query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Sum of the rectangle with corners (r1, c1) and (r2, c2), included."""
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise ValueError("bad rectangle")
        s = self.s
        return s[r2 + 1][c2 + 1] - s[r1][c2 + 1] - s[r2 + 1][c1] + s[r1][c1]


def brute(grid, r1, c1, r2, c2):
    return sum(grid[r][c] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))


def main():
    grid = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 1, 2, 3]]
    ps = StaticRangeSum2D(grid)
    assert ps.s[3] == [0, 15, 24, 36, 51]
    assert ps.query(1, 1, 2, 2) == 16      # the traced rectangle
    assert ps.query(0, 0, 2, 3) == 51      # whole grid
    assert ps.query(2, 3, 2, 3) == 3       # one cell, bottom-right corner
    assert StaticRangeSum2D([]).s == [[0]]
    for bad in [(1, 0, 0, 0), (0, 0, 3, 0), (0, -1, 0, 0)]:
        try:
            ps.query(*bad)
            raise AssertionError(bad)
        except ValueError:
            pass

    rng = Random(4)
    for _ in range(200):
        rows, cols = rng.randint(1, 5), rng.randint(1, 5)
        g = [[rng.randint(-5, 5) for _ in range(cols)] for _ in range(rows)]
        ps = StaticRangeSum2D(g)
        for _ in range(10):
            r1 = rng.randrange(rows)
            r2 = rng.randrange(r1, rows)
            c1 = rng.randrange(cols)
            c2 = rng.randrange(c1, cols)
            assert ps.query(r1, c1, r2, c2) == brute(g, r1, c1, r2, c2)


if __name__ == "__main__":
    main()
```

Build O(R · C) time and space; each `query` is **O(1)**. Negative values cause no trouble.

## 7. Two-dimensional difference arrays

The 2D version of §5: many "add `delta` to every cell of this rectangle" updates, then one final read of the whole grid.

**Observation.** In 1D, a mark `+Δ` at `l` affects every position to its right, and a `−Δ` at `r + 1` cancels it. In 2D, a mark at `(r, c)` affects every cell **below and to the right** of it, because the final read is a 2D prefix sum. To confine the effect to rows `r1..r2` and columns `c1..c2`, place four marks:

```text
               c1            c2+1
        r1    +Δ ............ −Δ
               .   affected   .
               .   rectangle  .
        r2+1  −Δ ............ +Δ
```

- `+Δ` at `(r1, c1)` covers everything below-right of the top-left corner.
- `−Δ` at `(r1, c2 + 1)` removes the part to the right of the rectangle.
- `−Δ` at `(r2 + 1, c1)` removes the part below it.
- The region below-right of `(r2 + 1, c2 + 1)` was removed twice, so `+Δ` there adds it back once. Inclusion–exclusion again.

**Trace.** A 3 × 4 grid of zeros, one update `+5` on rows `0..1`, columns `1..2`. The mark grid `d` has one extra row and column:

```text
marks d                    after row-wise prefix sums     after column-wise prefix sums
   0   5   0  −5   0          0   5   5   0   0              0   5   5   0   0
   0   0   0   0   0          0   0   0   0   0              0   5   5   0   0
   0  −5   0   5   0          0  −5  −5   0   0              0   0   0   0   0
   0   0   0   0   0          0   0   0   0   0              0   0   0   0   0
```

The top-left 3 × 4 part of the last grid is the answer: `5` exactly on rows 0–1, columns 1–2. Prefix sums along rows, then along columns, give the same result as the 2D prefix formula from §6.

```python
from random import Random


class BatchRangeAdd2D:
    """Collect rectangle additions, then build the final grid once."""

    def __init__(self, rows: int, cols: int):
        if rows < 0 or cols < 0:
            raise ValueError("negative size")
        self.rows, self.cols = rows, cols
        self.d = [[0] * (cols + 1) for _ in range(rows + 1)]

    def add(self, r1: int, c1: int, r2: int, c2: int, delta: int) -> None:
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise ValueError("bad rectangle")
        d = self.d
        d[r1][c1] += delta
        d[r1][c2 + 1] -= delta
        d[r2 + 1][c1] -= delta
        d[r2 + 1][c2 + 1] += delta

    def final_grid(self) -> list[list[int]]:
        g = [row[:self.cols] for row in self.d[:self.rows]]
        for r in range(self.rows):          # prefix sums along each row
            for c in range(1, self.cols):
                g[r][c] += g[r][c - 1]
        for r in range(1, self.rows):       # then along each column
            for c in range(self.cols):
                g[r][c] += g[r - 1][c]
        return g


def main():
    paint = BatchRangeAdd2D(3, 4)
    paint.add(0, 1, 1, 2, 5)
    assert paint.d[0] == [0, 5, 0, -5, 0]
    assert paint.final_grid() == [[0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0]]
    paint.add(1, 0, 2, 3, -1)               # touches the last row and column
    assert paint.final_grid() == [[0, 5, 5, 0], [-1, 4, 4, -1], [-1, -1, -1, -1]]
    assert BatchRangeAdd2D(0, 0).final_grid() == []

    rng = Random(5)
    for _ in range(200):
        rows, cols = rng.randint(1, 5), rng.randint(1, 5)
        paint = BatchRangeAdd2D(rows, cols)
        expected = [[0] * cols for _ in range(rows)]
        for _ in range(rng.randint(0, 6)):
            r1 = rng.randrange(rows)
            r2 = rng.randrange(r1, rows)
            c1 = rng.randrange(cols)
            c2 = rng.randrange(c1, cols)
            delta = rng.randint(-3, 3)
            paint.add(r1, c1, r2, c2, delta)
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    expected[r][c] += delta
        assert paint.final_grid() == expected


if __name__ == "__main__":
    main()
```

Each `add` is O(1). `final_grid` is O(R · C). For `q` updates the total is O(R · C + q) instead of O(q · R · C).

## 8. Counting subarrays with sum `k`: prefix sums plus a hash map

### The problem

Given an array that may contain negative numbers and a target `k`, count the **subarrays** (contiguous, nonempty runs of elements) whose sum is exactly `k`.

Example: `nums = [1, 2, −1, 2, 1]`, `k = 3`. The subarrays with sum 3 are `[1, 2]` (indices 0–1), `[2, −1, 2]` (indices 1–3), and `[2, 1]` (indices 3–4). Answer: 3.

**Brute force.** Try every start `i` and extend the end `j`, keeping a running sum. That is `n(n + 1)/2` subarrays, O(n²). For `n = 100,000` that is about 5 billion sums.

**Why not a sliding window?** A window that grows to the right only works when growing can never make the sum smaller, which needs nonnegative values. With `−1` in the array, extending can lower the sum, so the usual "shrink while too big" rule throws away answers. [Sliding Window](../05-sliding-window/README.md) covers this limit.

### The observation: a subarray sum is a difference of two prefix sums

With `P` as before, the subarray from index `i` to index `j − 1` has sum `P[j] − P[i]`. So:

$$
P[j] - P[i] = k \quad\Longleftrightarrow\quad P[i] = P[j] - k.
$$

For each end boundary `j`, the number of good subarrays ending right before `j` equals the number of **earlier** boundaries `i < j` whose prefix sum is exactly `P[j] − k`. Scan left to right and keep a dictionary `freq` that counts how many times each prefix value has appeared so far.

**State.** Before processing element `j − 1`, `freq[v]` is the number of boundaries `i < j` with `P[i] = v`. The empty prefix `P[0] = 0` is one of them, so `freq` starts as `{0: 1}`.

### Trace

Prefix sums of `[1, 2, −1, 2, 1]` are `0, 1, 3, 2, 4, 5`.

| Step | `num` | `running` = `P[j]` | look up `running − k` | `freq[...]` found | `answer` | `freq` after adding `running` |
|---:|---:|---:|---:|---:|---:|---|
| start | — | 0 | — | — | 0 | `{0: 1}` |
| 1 | 1 | 1 | −2 | 0 | 0 | `{0: 1, 1: 1}` |
| 2 | 2 | 3 | 0 | 1 | 1 | `{0: 1, 1: 1, 3: 1}` |
| 3 | −1 | 2 | −1 | 0 | 1 | `{0: 1, 1: 1, 3: 1, 2: 1}` |
| 4 | 2 | 4 | 1 | 1 | 2 | `… 4: 1` |
| 5 | 1 | 5 | 2 | 1 | 3 | `… 5: 1` |

Step 2 found `P[0] = 0`: the subarray `[1, 2]`. Step 4 found `P[1] = 1`: the subarray `[2, −1, 2]`. Step 5 found `P[3] = 2`: the subarray `[2, 1]`.

**Why look up before recording the current prefix?** If `running` were added first, then for `k = 0` the boundary would match itself, counting an empty subarray. Looking up first means only boundaries strictly to the left are counted.

### Code

```python
from collections import defaultdict
from random import Random


def count_subarrays_sum_k(nums: list[int], k: int) -> int:
    freq = defaultdict(int)
    freq[0] = 1          # the empty prefix
    running = 0
    answer = 0
    for num in nums:
        running += num
        answer += freq[running - k]   # earlier boundaries that pair with this one
        freq[running] += 1
    return answer


def brute(nums, k):
    n = len(nums)
    return sum(sum(nums[i:j]) == k for i in range(n) for j in range(i + 1, n + 1))


def main():
    assert count_subarrays_sum_k([1, 2, -1, 2, 1], 3) == 3
    assert count_subarrays_sum_k([1, 1, 1], 2) == 2
    assert count_subarrays_sum_k([1, -1, 0], 0) == 3
    assert count_subarrays_sum_k([0, 0, 0], 0) == 6   # every subarray
    assert count_subarrays_sum_k([], 0) == 0          # no nonempty subarray
    assert count_subarrays_sum_k([5], 5) == 1
    assert count_subarrays_sum_k([5], 4) == 0

    rng = Random(6)
    for _ in range(500):
        nums = [rng.randint(-3, 3) for _ in range(rng.randint(0, 10))]
        k = rng.randint(-4, 4)
        assert count_subarrays_sum_k(nums, k) == brute(nums, k)


if __name__ == "__main__":
    main()
```

Time O(n) expected (each dictionary operation is O(1) on average). Space O(n) for up to `n + 1` distinct prefix values.

**Why it's correct.** Every nonempty subarray is `nums[i..j − 1]` for exactly one pair of boundaries `0 ≤ i < j ≤ n`, and its sum is `P[j] − P[i]`. The scan visits each `j` once. At that moment `freq` holds exactly the boundaries `0, …, j − 1`, so it adds the number of `i < j` with `P[i] = P[j] − k`. Summed over all `j`, that is the number of pairs with `P[j] − P[i] = k`, which is the number of subarrays with sum `k`. No pair is counted twice, because each pair is counted only at its right boundary `j`.

### Variants on the same idea

All of these keep "something about earlier prefixes" in a dictionary:

| Question | Store per prefix value | Key fact |
|---|---|---|
| Count subarrays with sum `k` | how many times it appeared | `P[i] = P[j] − k` |
| Longest subarray with sum `k` | the **earliest** boundary where it appeared | earliest start gives the longest run |
| Longest run with equal 0s and 1s | earliest boundary, after mapping 0 → −1 | equal counts ⇔ sum 0 |
| Count subarrays with sum divisible by `m` | how many times each **remainder** `P mod m` appeared | `P[j] − P[i]` divisible by `m` ⇔ equal remainders |
| Count subarrays with XOR equal to `x` | how many times each prefix XOR appeared | `PX[j] ^ PX[i] = x` ⇔ `PX[i] = PX[j] ^ x` |

```python
from random import Random


def longest_sum_k(nums: list[int], k: int) -> int:
    first_seen = {0: 0}       # prefix value -> earliest boundary index
    running = best = 0
    for j, num in enumerate(nums, start=1):
        running += num
        if running - k in first_seen:
            best = max(best, j - first_seen[running - k])
        first_seen.setdefault(running, j)   # keep the earliest only
    return best


def longest_balanced_01(bits: list[int]) -> int:
    return longest_sum_k([1 if b else -1 for b in bits], 0)


def count_divisible(nums: list[int], m: int) -> int:
    if m == 0:
        raise ValueError("m must be nonzero")
    freq = {0: 1}
    running = answer = 0
    for num in nums:
        running = (running + num) % m   # Python's % is never negative for m > 0
        answer += freq.get(running, 0)
        freq[running] = freq.get(running, 0) + 1
    return answer


def count_xor(nums: list[int], x: int) -> int:
    freq = {0: 1}
    running = answer = 0
    for num in nums:
        running ^= num
        answer += freq.get(running ^ x, 0)
        freq[running] = freq.get(running, 0) + 1
    return answer


def subarrays(nums):
    n = len(nums)
    return [nums[i:j] for i in range(n) for j in range(i + 1, n + 1)]


def xor_all(seq):
    out = 0
    for v in seq:
        out ^= v
    return out


def main():
    assert longest_sum_k([1, -1, 5, -2, 3], 3) == 4      # [1, -1, 5, -2]
    assert longest_sum_k([2, 2], 1) == 0
    assert longest_balanced_01([0, 1, 1, 0, 1, 1, 1, 0]) == 4
    assert count_divisible([4, 5, 0, -2, -3, 1], 5) == 7
    assert count_xor([4, 2, 2, 6, 4], 6) == 4

    rng = Random(7)
    for _ in range(300):
        nums = [rng.randint(-4, 4) for _ in range(rng.randint(0, 9))]
        k = rng.randint(-4, 4)
        subs = subarrays(nums)
        assert longest_sum_k(nums, k) == max(
            (len(s) for s in subs if sum(s) == k), default=0)
        m = rng.randint(1, 5)
        assert count_divisible(nums, m) == sum(sum(s) % m == 0 for s in subs)
        bits = [abs(v) % 2 for v in nums]
        assert longest_balanced_01(bits) == max(
            (len(s) for s in subarrays(bits) if s.count(0) == s.count(1)), default=0)
        xs = [abs(v) for v in nums]
        assert count_xor(xs, 3) == sum(xor_all(s) == 3 for s in subarrays(xs))


if __name__ == "__main__":
    main()
```

Each variant is one O(n) pass with O(n) extra space. In languages where `%` can return a negative number for a negative operand (C++, Java), normalize the remainder with `((x % m) + m) % m` before using it as a key.

## 9. What prefix sums cannot do

The range formula needs to **undo** the part of the prefix before `l`. Sums can be undone by subtraction, XOR by XOR again, and counts by subtraction. A **minimum** cannot be undone.

Example: the arrays `[1, 5, 6]` and `[1, 2, 6]` have the same prefix minima, `[1, 1, 1]`, yet their minimum over `[1, 2]` is 5 in one and 2 in the other. No formula using only prefix minima can tell them apart.

| Operation | Can be undone? | Static range query | With changes |
|---|---|---|---|
| Sum, count | yes (subtract) | this chapter, O(1) | [Fenwick Tree](02-fenwick-tree.md) |
| XOR | yes (XOR again) | this chapter, O(1) | [Fenwick Tree](02-fenwick-tree.md) |
| Product | only without zeros, and with exact division | risky | [Segment Tree](03-segment-tree.md) |
| Min, max, GCD | no | [Sparse Table](04-sparse-table-and-sqrt.md), O(1) | [Segment Tree](03-segment-tree.md) |

## 10. Summary

| Tool | Build | Answer | Formula |
|---|---|---|---|
| Prefix sums | `P[0] = 0`, `P[k + 1] = P[k] + a[k]` | sum of `a[l..r]` in O(1) | `P[r + 1] − P[l]` |
| 0/1 prefix counts | prefix sums of `[cond(x) for x in a]` | count in `[l, r]` in O(1) | `P[r + 1] − P[l]` |
| Difference array | `d[l] += Δ`, `d[r + 1] −= Δ` per update | final array in O(n) | `a[i] += d[0] + … + d[i]` |
| 2D prefix sums | `S[r+1][c+1] = g[r][c] + S[r][c+1] + S[r+1][c] − S[r][c]` | rectangle sum in O(1) | `S[r2+1][c2+1] − S[r1][c2+1] − S[r2+1][c1] + S[r1][c1]` |
| 2D difference array | `+Δ, −Δ, −Δ, +Δ` at the four corners | final grid in O(R · C) | row prefix sums, then column prefix sums |
| Prefix sums + hash map | `freq = {0: 1}`, look up, then record | subarray counts in O(n) | `P[i] = P[j] − k` |

Two questions decide when these tools stop working: if the array changes between reads, move to the [Fenwick Tree](02-fenwick-tree.md); if the summary cannot be undone by subtraction (§9), move to the [Segment Tree](03-segment-tree.md) or the [Sparse Table](04-sparse-table-and-sqrt.md).

## 11. Pitfalls and practice

1. Using `P[r] − P[l]` for an inclusive range. That drops `a[r]`. The inclusive formula is `P[r + 1] − P[l]`.
2. Forgetting `P[0] = 0`, or starting the hash map without `{0: 1}`. Both lose every range that starts at index 0.
3. Recording the current prefix in the hash map before looking it up, which counts empty subarrays.
4. Forgetting `d[r + 1] −= delta` in a difference array, which leaks the update to the end of the array.
5. Forgetting the add-back corner in 2D, or using `+` where inclusion–exclusion needs `−`.
6. Expecting a prefix-sum table to handle changes. One point change costs O(n); use a [Fenwick Tree](02-fenwick-tree.md).
7. Using a sliding window for sums with negative values. Use prefix sums plus a hash map.
8. Overflow. Python integers grow without limit; in C++ or Java, a sum of 10⁵ values of size 10⁹ needs 64-bit integers.

Practice: range sum query on an immutable array; range sum query on an immutable 2D matrix; subarray sum equals k; contiguous array (equal 0s and 1s); continuous subarray sum (multiple of k, length at least 2); subarray sums divisible by K; range addition (difference array); corporate flight bookings; car pooling; stamping the grid (2D prefix sums plus 2D difference array); count triplets that can form two arrays of equal XOR.

Next: [Fenwick Tree](02-fenwick-tree.md).
