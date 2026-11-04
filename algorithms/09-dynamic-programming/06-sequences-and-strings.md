# Sequences and Strings — Prefixes, Endings, and Matches

## 1. Longest increasing subsequence, the quadratic DP

**Problem.** Given `a`, find the length of the longest **strictly increasing** subsequence (LIS). For `a = [5, 2, 8, 6, 3, 6, 9, 7]` the answer is 4, for example `2, 3, 6, 9`.

A **subsequence** keeps some positions in their original order and may skip others; a **substring** (for arrays, a **subarray**) is one unbroken block `s[l:r]`; a **prefix** is a substring starting at index 0, and the prefix of length `i` is `s[:i]`. On `s = "dynamo"`:

```text
index:        0  1  2  3  4  5
s:            d  y  n  a  m  o
substring     .  y  n  a  .  .      "yna"   one contiguous block
subsequence   d  .  n  .  m  o      "dnmo"  keep order, gaps allowed
prefix        d  y  n  .  .  .      "dyn"   = s[:3]
```

The difference must show in the state. A string of length `n` has `n(n+1)/2` nonempty substrings but `2^n` subsequences (465 versus about a billion for `n = 30`), and "increasing subsequence ending at `i`" may jump back to *any* earlier `j`, while "increasing subarray ending at `i`" may only extend `i − 1`.

**Brute force.** Try all `2^n` subsets of positions; hopeless for `n = 60`.

**State.** Let `end[i]` be the length of the longest strictly increasing subsequence whose last element is `a[i]`. Fixing the last element is what makes the transition easy: we know exactly which value the previous element must be smaller than.

**Transition.** Ask what came right before `a[i]` in the subsequence.

- Nothing: the subsequence is `a[i]` alone, length 1.
- Some earlier `a[j]` with `j < i` and `a[j] < a[i]`: take the best subsequence ending at `j` and append `a[i]`.

$$
end[i] = 1 + \max\bigl(\{0\} \cup \{\, end[j] : 0 \le j < i,\ a[j] < a[i] \,\}\bigr)
$$

**Base case and answer.** No separate base case: the `{0}` handles "nothing before". The answer is `max(end)`, or 0 for an empty list, because the LIS may end anywhere.

**Order.** `end[i]` reads only smaller indices, so a left-to-right loop works.

**Trace.** `prev[i]` stores the maximizing `j` (or `-1`), for reconstruction.

| i | a[i] | earlier smaller values (end) | end[i] | prev[i] |
|---|---|---|---|---|
| 0 | 5 | none | 1 | -1 |
| 1 | 2 | none | 1 | -1 |
| 2 | 8 | 5 (1), 2 (1) | 2 | 0 |
| 3 | 6 | 5 (1), 2 (1) | 2 | 0 |
| 4 | 3 | 2 (1) | 2 | 1 |
| 5 | 6 | 5 (1), 2 (1), 3 (2) | 3 | 4 |
| 6 | 9 | all earlier; best is 6 at i=5 (3) | 4 | 5 |
| 7 | 7 | 5, 2, 6, 3, 6 ; best 6 at i=5 (3) | 4 | 5 |

The maximum is 4 at `i = 6`. Following `prev` gives `6 → 5 → 4 → 1`, values `9, 6, 3, 2`, reversed: `2, 3, 6, 9`.

The code for both LIS methods, tested together against a brute force, follows §2. Time O(n²), space O(n).

**Why it is correct.** Every increasing subsequence ending at `a[i]` either has length 1 or has a well-defined previous element `a[j]` with `j < i` and `a[j] < a[i]`. Removing `a[i]` leaves an increasing subsequence ending at `j`, so its length is at most `end[j]`. Conversely, appending `a[i]` to the best one ending at `j` is valid. The cases are exhaustive and each builds a valid subsequence.

**Strict versus nondecreasing.** The only change is `<` versus `<=`. The input `[2, 2, 2]` tells them apart: strict LIS is 1, nondecreasing is 3. Always test that input.

## 2. LIS in O(n log n): the tails array

The quadratic loop asks, for each `i`, "which earlier subsequences can I extend?" Many of them are redundant. Suppose two increasing subsequences both have length 2, one ending in 8 and one ending in 3. Any future value that extends the "…8" one (anything above 8) also extends the "…3" one. So for each length we only need to remember the **smallest possible last value**.

**Invariant.** After processing a prefix, `tails[k]` is the smallest last value of any strictly increasing subsequence of length `k + 1` in that prefix.

`tails` is always strictly increasing. (If a length-3 subsequence ends in `v`, dropping its last element gives a length-2 one ending in something smaller than `v`.) So binary search works. For a new value `x`:

- Find the first position `k` with `tails[k] >= x` (`bisect_left`).
- If no such position exists, `x` extends the longest subsequence: append it.
- Otherwise `x` extends the length-`k` subsequence (ending in `tails[k-1] < x`) and gives a length-`k+1` subsequence ending in `x <= tails[k]`. Replace `tails[k]` with `x`.

**Trace** on `[5, 2, 8, 6, 3, 6, 9, 7]`:

| x | position k | action | tails after |
|---|---|---|---|
| 5 | 0 | append | `[5]` |
| 2 | 0 | replace 5 | `[2]` |
| 8 | 1 | append | `[2, 8]` |
| 6 | 1 | replace 8 | `[2, 6]` |
| 3 | 1 | replace 6 | `[2, 3]` |
| 6 | 2 | append | `[2, 3, 6]` |
| 9 | 3 | append | `[2, 3, 6, 9]` |
| 7 | 3 | replace 9 | `[2, 3, 6, 7]` |

The final length is 4. Notice that `tails` itself need not be a real subsequence. Try `[3, 4, 1]`: tails ends as `[1, 4]`, but 1 comes after 4. So for reconstruction we store, for each input index, the index that ended the previous length at the moment it was processed.

For a **nondecreasing** subsequence, equal values may extend each other, so search for the first tail strictly greater than `x` with `bisect_right`.

```python
import random
from bisect import bisect_left, bisect_right
from itertools import combinations


def lis_indices(nums: list[int], strict: bool = True) -> list[int]:
    """Indices of one longest increasing subsequence."""
    search = bisect_left if strict else bisect_right
    tails = []          # tails[k] = smallest last value for length k+1
    tail_index = []     # index in nums where that value sits
    previous = [-1] * len(nums)
    for i, x in enumerate(nums):
        k = search(tails, x)
        if k > 0:
            previous[i] = tail_index[k - 1]
        if k == len(tails):
            tails.append(x)
            tail_index.append(i)
        else:
            tails[k] = x
            tail_index[k] = i
    out = []
    i = tail_index[-1] if tail_index else -1
    while i != -1:
        out.append(i)
        i = previous[i]
    return out[::-1]


def lis_quadratic(a: list[int], strict: bool = True) -> list[int]:
    """Return one longest increasing subsequence (values)."""
    n = len(a)
    if n == 0:
        return []
    end = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            fits = a[j] < a[i] if strict else a[j] <= a[i]
            if fits and end[j] + 1 > end[i]:
                end[i] = end[j] + 1
                prev[i] = j
    i = max(range(n), key=end.__getitem__)
    out = []
    while i != -1:
        out.append(a[i])
        i = prev[i]
    return out[::-1]


def brute_lis_length(a: list[int], strict: bool = True) -> int:
    for size in range(len(a), 0, -1):
        for idx in combinations(range(len(a)), size):
            vals = [a[k] for k in idx]
            pairs = zip(vals, vals[1:])
            if all(x < y if strict else x <= y for x, y in pairs):
                return size
    return 0


def main():
    nums = [5, 2, 8, 6, 3, 6, 9, 7]
    idx = lis_indices(nums)
    assert [nums[i] for i in idx] == [2, 3, 6, 7]
    assert lis_indices([3, 4, 1]) == [0, 1]
    assert lis_indices([]) == []
    assert len(lis_indices([2, 2, 2])) == 1
    assert len(lis_indices([2, 2, 2], strict=False)) == 3
    assert lis_quadratic(nums) == [2, 3, 6, 9]
    assert lis_quadratic([2, 2, 2]) == [2]
    assert lis_quadratic([2, 2, 2], strict=False) == [2, 2, 2]
    rng = random.Random(7)
    for _ in range(300):
        a = [rng.randint(-3, 3) for _ in range(rng.randint(0, 10))]
        for strict in (True, False):
            idx = lis_indices(a, strict)
            assert idx == sorted(set(idx))
            vals = [a[i] for i in idx]
            assert all(x < y if strict else x <= y for x, y in zip(vals, vals[1:]))
            best = brute_lis_length(a, strict)
            assert len(idx) == best
            got = lis_quadratic(a, strict)
            assert len(got) == best
            assert all(x < y if strict else x <= y for x, y in zip(got, got[1:]))


if __name__ == "__main__":
    main()
```

`lis_indices` takes O(n log n) time and O(n) space.

**Why it is correct.** The invariant holds after each step: appending creates the only subsequence of a new length, and replacing lowers a tail only when a valid smaller-ending subsequence of that length was built. No other tail can improve, because `x` can only extend lengths whose tail is below `x`, and the largest such length is `k`. Since `tails` grows by one exactly when a longer subsequence appears, its final length is the LIS length.

## 3. Counting the longest increasing subsequences

**Problem.** Return how many strictly increasing subsequences have the maximum length. Count by index sets: equal values at different positions are different subsequences. For `[1, 3, 5, 4, 7]` the answer is 2 (`1,3,5,7` and `1,3,4,7`).

The tails trick throws away the information we need, so return to the quadratic DP and carry a pair per index:

- `length[i]`: the LIS length ending at `i` (as before).
- `count[i]`: how many subsequences ending at `i` have that length.

For each `j < i` with `a[j] < a[i]`, the candidate length is `length[j] + 1`:

- longer than the current `length[i]`: replace, and set `count[i] = count[j]`;
- equal: add, `count[i] += count[j]`;
- shorter: ignore.

$$
count[i] = \sum_{\substack{j<i,\ a[j]<a[i] \\ length[j]+1 = length[i]}} count[j], \qquad \text{or } 1 \text{ if no such } j.
$$

**Trace** on `[5, 2, 8, 6, 3, 6, 9, 7]`, as `(length, count)`:

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| a[i] | 5 | 2 | 8 | 6 | 3 | 6 | 9 | 7 |
| pair | (1,1) | (1,1) | (2,2) | (2,2) | (2,1) | (3,1) | (4,1) | (4,1) |

At `i = 2` both `5` and `2` give length 2, so the counts add to 2. The maximum length 4 appears at `i = 6` and `i = 7`; the answer is `1 + 1 = 2`. Note the final step: sum counts over **all** indices whose length equals the global maximum, not only one.

```python
import random
from itertools import combinations


def count_lis(a: list[int]) -> tuple[int, int]:
    """Return (LIS length, number of LIS) for strictly increasing."""
    n = len(a)
    if n == 0:
        return 0, 0
    length = [1] * n
    count = [1] * n
    for i in range(n):
        for j in range(i):
            if a[j] < a[i]:
                if length[j] + 1 > length[i]:
                    length[i] = length[j] + 1
                    count[i] = count[j]
                elif length[j] + 1 == length[i]:
                    count[i] += count[j]
    best = max(length)
    return best, sum(c for l, c in zip(length, count) if l == best)


def brute_count_lis(a: list[int]) -> tuple[int, int]:
    for size in range(len(a), 0, -1):
        ways = 0
        for idx in combinations(range(len(a)), size):
            if all(a[x] < a[y] for x, y in zip(idx, idx[1:])):
                ways += 1
        if ways:
            return size, ways
    return 0, 0


def main():
    assert count_lis([1, 3, 5, 4, 7]) == (4, 2)
    assert count_lis([5, 2, 8, 6, 3, 6, 9, 7]) == (4, 2)
    assert count_lis([2, 2, 2, 2]) == (1, 4)
    assert count_lis([]) == (0, 0)
    rng = random.Random(4)
    for _ in range(300):
        a = [rng.randint(0, 4) for _ in range(rng.randint(0, 10))]
        assert count_lis(a) == brute_count_lis(a)


if __name__ == "__main__":
    main()
```

Time O(n²), space O(n). To reach O(n log n), compress values to ranks and keep a [Fenwick Tree](../04-range-queries/02-fenwick-tree.md) or [Segment Tree](../04-range-queries/03-segment-tree.md) whose "sum" operation combines `(length, count)` pairs: keep the larger length, add counts on ties. A prefix query over ranks below `a[i]` replaces the inner loop.

## 4. Longest common subsequence

**Problem.** Given strings `a` and `b`, find a longest string that is a subsequence of both (LCS). For `a = "abcbd"`, `b = "bdcb"`, one answer is `"bcb"`, length 3.

**Brute force.** List all `2^n` subsequences of `a` and test each against `b` in O(m). Exponential.

**State.** `dp[i][j]` = the LCS length of the prefixes `a[:i]` and `b[:j]`. Using prefixes (not "ending at") is natural here, because an LCS need not use the last character of either string.

**Transition.** Look at the last characters `a[i-1]` and `b[j-1]`.

- They are equal: an optimal LCS may use them as its final matched pair, leaving the LCS of `a[:i-1]` and `b[:j-1]`.
- They differ: no common subsequence can end with both. At least one of them goes unused, so drop it.

$$
dp[i][j] =
\begin{cases}
dp[i-1][j-1] + 1, & a[i-1] = b[j-1],\\
\max\bigl(dp[i-1][j],\ dp[i][j-1]\bigr), & \text{otherwise.}
\end{cases}
$$

**Base cases.** `dp[0][j] = dp[i][0] = 0`: an empty prefix shares only the empty subsequence.

**Order.** Each cell reads up, left, and up-left. Row by row, left to right, works.

**Trace** (rows are `a`, columns are `b`):

| | "" | b | d | c | b |
|---|---|---|---|---|---|
| "" | 0 | 0 | 0 | 0 | 0 |
| a | 0 | 0 | 0 | 0 | 0 |
| b | 0 | **1** | 1 | 1 | **1** |
| c | 0 | 1 | 1 | **2** | 2 |
| b | 0 | **1** | 1 | 2 | **3** |
| d | 0 | 1 | **2** | 2 | 3 |

Bold cells are matches (up-left plus one). Reconstruction walks back from the bottom-right: at a match take the character and go diagonally; otherwise move toward the larger neighbor. From `(5,4)`: `d ≠ b`, up is 3, go up to `(4,4)`; `b = b`, take `b`, go to `(3,3)`; `c = c`, take `c`, go to `(2,2)`; `b ≠ d`, up is 0, left is 1, go left to `(2,1)`; `b = b`, take `b`. Reversed: `"bcb"`.

The diagonal move at a match is safe: if `a[i-1] = b[j-1]`, then `dp[i][j] = dp[i-1][j-1] + 1`, which is never less than either other neighbor.

```python
import random
from itertools import combinations


def lcs(a: str, b: str) -> str:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    out = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i, j = i - 1, j - 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))


def is_subsequence(small: str, big: str) -> bool:
    it = iter(big)
    return all(ch in it for ch in small)


def brute_lcs_length(a: str, b: str) -> int:
    for size in range(len(a), 0, -1):
        for idx in combinations(range(len(a)), size):
            if is_subsequence("".join(a[k] for k in idx), b):
                return size
    return 0


def main():
    assert lcs("abcbd", "bdcb") == "bcb"
    assert lcs("abcde", "ace") == "ace"
    assert lcs("", "abc") == "" and lcs("abc", "xyz") == ""
    rng = random.Random(5)
    for _ in range(300):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 8)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 8)))
        got = lcs(a, b)
        assert is_subsequence(got, a) and is_subsequence(got, b)
        assert len(got) == brute_lcs_length(a, b)


if __name__ == "__main__":
    main()
```

Time O(nm), space O(nm) for the table. Reconstruction adds O(n + m). If only the length is needed, keep two rows and use O(min(n, m)) space; but then the path is gone. Rebuilding an LCS in linear space needs a divide-and-conquer method (Hirschberg's algorithm).

**Longest common substring is a different recurrence.** Its state is "ending at": `end[i][j]` = the length of the longest common block ending exactly at `a[i-1]` and `b[j-1]`. On a match it is `end[i-1][j-1] + 1`; on a mismatch it **resets to 0**, because a block cannot skip characters. The answer is the maximum over all cells. Copying the LCS `max(up, left)` rule here would silently allow gaps; `"abcde"` and `"ace"` give 3 for LCS but 1 for substring.

## 5. Edit distance and the operation script

**Problem.** Convert `source` into `target` with the fewest single-character operations: insert, delete, or substitute. For `"horse" → "ros"` the answer is 3 (substitute `h→r`, delete `r`, delete `e`). Transposing two adjacent characters is **not** an operation here, so `"ab" → "ba"` costs 2.

**State.** `dp[i][j]` = the minimum cost to turn `source[:i]` into `target[:j]`.

**Transition.** Think about what happens to the last characters in an optimal edit.

- `source[i-1]` is deleted: cost `dp[i-1][j] + 1`.
- `target[j-1]` is inserted at the end: cost `dp[i][j-1] + 1`.
- `source[i-1]` becomes `target[j-1]`: free if they are equal, otherwise one substitution: `dp[i-1][j-1] + [source[i-1] ≠ target[j-1]]`.

$$
dp[i][j] = \min\bigl(dp[i-1][j] + 1,\ dp[i][j-1] + 1,\ dp[i-1][j-1] + [s_{i-1} \ne t_{j-1}]\bigr)
$$

**Base cases.** `dp[i][0] = i` (delete everything) and `dp[0][j] = j` (insert everything). These are **not** zero; an all-zero first row is the classic bug, and an empty source catches it.

**Trace** for `"horse" → "ros"`:

| | "" | r | o | s |
|---|---|---|---|---|
| "" | 0 | 1 | 2 | 3 |
| h | 1 | 1 | 2 | 3 |
| o | 2 | 2 | 1 | 2 |
| r | 3 | 2 | 2 | 2 |
| s | 4 | 3 | 3 | 2 |
| e | 5 | 4 | 4 | 3 |

**Rebuilding the script.** Walk back from `(5, 3)`. At each cell, find which of the three cases produced its value, record the operation, and step to that neighbor. Here: `(5,3)=3` came from up `(4,3)=2` plus a deletion of `e`; `(4,3)=2` came diagonally from `(3,2)=2` with `s = s` (keep); `(3,2)=2` came from up `(2,2)=1`, delete `r`; `(2,2)=1` came diagonally from `(1,1)=1`, keep `o`; `(1,1)=1` came diagonally from `(0,0)`, substitute `h→r`. Reversed, the script is: substitute, keep, delete, keep, delete.

When the script is written as positions, be careful: after an insertion or deletion, later positions in the edited string shift. The code below avoids that by recording each step relative to the original strings and then testing the script by applying it.

```python
import random
from collections import deque


def edit_script(source: str, target: str) -> list[tuple[str, str, str]]:
    """List of (op, from_char, to_char) left to right; op in keep/sub/del/ins."""
    n, m = len(source), len(target)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1,
                           dp[i - 1][j - 1] + (source[i - 1] != target[j - 1]))
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (source[i - 1] != target[j - 1]):
            op = "keep" if source[i - 1] == target[j - 1] else "sub"
            ops.append((op, source[i - 1], target[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("del", source[i - 1], ""))
            i -= 1
        else:
            ops.append(("ins", "", target[j - 1]))
            j -= 1
    return ops[::-1]


def apply_script(source: str, ops) -> str:
    out, i = [], 0
    for op, frm, to in ops:
        if op in ("keep", "sub", "del"):
            assert source[i] == frm
            i += 1
        if op != "del":
            out.append(to)
    assert i == len(source)
    return "".join(out)


def brute_distance(source: str, target: str, alphabet: str) -> int:
    """BFS over strings; only for tiny inputs."""
    limit = max(len(source), len(target)) + 1
    seen, queue = {source: 0}, deque([source])
    while queue:
        s = queue.popleft()
        if s == target:
            return seen[s]
        nexts = [s[:k] + s[k + 1:] for k in range(len(s))]
        nexts += [s[:k] + c + s[k + 1:] for k in range(len(s)) for c in alphabet]
        if len(s) < limit:
            nexts += [s[:k] + c + s[k:] for k in range(len(s) + 1) for c in alphabet]
        for t in nexts:
            if t not in seen:
                seen[t] = seen[s] + 1
                queue.append(t)
    raise AssertionError("unreachable")


def main():
    def edit_distance(s, t):
        return sum(op != "keep" for op, _, _ in edit_script(s, t))

    assert edit_distance("horse", "ros") == 3
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("", "abc") == 3 and edit_distance("abc", "") == 3
    assert edit_distance("ab", "ba") == 2      # no transposition
    ops = edit_script("horse", "ros")
    assert [op for op, _, _ in ops] == ["sub", "keep", "del", "keep", "del"]
    rng = random.Random(8)
    for _ in range(200):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 5)))
        t = "".join(rng.choice("ab") for _ in range(rng.randint(0, 5)))
        ops = edit_script(s, t)
        assert apply_script(s, ops) == t
        assert sum(op != "keep" for op, _, _ in ops) == brute_distance(s, t, "ab")


if __name__ == "__main__":
    main()
```

Time and space O(nm). If only the distance is needed, each row reads only the previous one, so two rows suffice; swapping the strings so the shorter one indexes the row gives O(min(n, m)) space. That swap is safe only because insertion and deletion cost the same.

## 6. Palindromes: subsequences and substrings

A **palindrome** reads the same forwards and backwards. Here the natural state is an interval `s[l:r]`, a preview of [Interval DP](07-interval-dp.md).

### 7.1 Longest palindromic subsequence

**Problem.** For `s = "bbabcb"`, the longest palindromic subsequence is `"bbabb"` (indices 0, 1, 2, 3, 5), length 5.

**State.** `L[l][r]` = the length of the longest palindromic subsequence of `s[l:r]`.

**Transition** on the two end characters `s[l]` and `s[r-1]`:

- Equal: use both as the outer pair, `L[l+1][r-1] + 2`.
- Different: they cannot both be the outer pair, so drop one, `max(L[l+1][r], L[l][r-1])`.

**Base cases.** Empty interval: `L[l][l] = 0`. One character: `L[l][l+1] = 1`. These differ, and both are needed: when `r - l = 2` with equal characters, the inner interval is empty.

**Order.** Each interval reads strictly shorter intervals, so fill by increasing length. A neat check: the LPS of `s` equals the LCS of `s` and `reversed(s)`.

### 7.2 Palindromic substrings: count them, find the longest

**Problem.** Count the palindromic substrings of `"aaba"` (by position): `a, a, b, a, aa, aba` gives 6. The longest is `"aba"`.

**DP table.** `pal[l][r]` is true if `s[l:r]` is a palindrome: `s[l] == s[r-1]` and the inside `s[l+1:r-1]` is a palindrome (intervals of length 0 or 1 are palindromes). Fill by length. O(n²) time and O(n²) space.

**Expand around center.** Every palindrome has a center: a character (odd length) or a gap between two characters (even length). There are `2n - 1` centers. From each center, grow outwards while both ends match; every successful step is one more palindrome. O(n²) time in the worst case (`"aaaa…"`), but **O(1)** extra space and usually faster in practice, because it stops at the first mismatch.

| | DP table | Expand around center |
|---|---|---|
| Time | O(n²) always | O(n²) worst, often much less |
| Space | O(n²) | O(1) |
| Bonus | answers "is `s[l:r]` a palindrome?" for any later query | none |

Use the table when another DP needs palindrome queries (palindrome partitioning in [Interval DP](07-interval-dp.md)). Use expansion for one-shot counting. Manacher's algorithm does it in O(n).

```python
import random


def longest_pal_subseq(s: str) -> int:
    n = len(s)
    L = [[0] * (n + 1) for _ in range(n + 1)]
    for l in range(n):
        L[l][l + 1] = 1
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            if s[l] == s[r - 1]:
                L[l][r] = L[l + 1][r - 1] + 2
            else:
                L[l][r] = max(L[l + 1][r], L[l][r - 1])
    return L[0][n]


def pal_table(s: str) -> list[list[bool]]:
    n = len(s)
    pal = [[True] * (n + 1) for _ in range(n + 1)]  # length 0 and 1 are True
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length
            pal[l][r] = s[l] == s[r - 1] and pal[l + 1][r - 1]
    return pal


def count_pal_substrings_dp(s: str) -> int:
    pal, n = pal_table(s), len(s)
    return sum(pal[l][r] for l in range(n) for r in range(l + 1, n + 1))


def expand_all(s: str) -> tuple[int, str]:
    """Return (count of palindromic substrings, one longest)."""
    count, best = 0, (0, 0)
    for center in range(2 * len(s) - 1):
        l, r = center // 2, center // 2 + center % 2
        while l >= 0 and r < len(s) and s[l] == s[r]:
            count += 1
            if r + 1 - l > best[1] - best[0]:
                best = (l, r + 1)
            l, r = l - 1, r + 1
    return count, s[best[0]:best[1]]


def brute(s: str):
    subs = [s[l:r] for l in range(len(s)) for r in range(l + 1, len(s) + 1)]
    pals = [t for t in subs if t == t[::-1]]
    best_sub = max(map(len, pals), default=0)
    best_seq = 0
    for mask in range(1 << len(s)):
        t = "".join(s[k] for k in range(len(s)) if mask >> k & 1)
        if t == t[::-1]:
            best_seq = max(best_seq, len(t))
    return len(pals), best_sub, best_seq


def main():
    assert longest_pal_subseq("bbabcb") == 5
    assert longest_pal_subseq("") == 0 and longest_pal_subseq("ab") == 1
    assert count_pal_substrings_dp("aaba") == 6
    assert expand_all("aaba") == (6, "aba")
    assert expand_all("") == (0, "")
    rng = random.Random(9)
    for _ in range(300):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 10)))
        count, best_sub, best_seq = brute(s)
        assert longest_pal_subseq(s) == best_seq
        assert count_pal_substrings_dp(s) == count
        c, longest = expand_all(s)
        assert c == count and len(longest) == best_sub
        assert longest == longest[::-1] and longest in s


if __name__ == "__main__":
    main()
```

## 7. Distinct subsequences: counting embeddings

**Problem.** Count the number of ways to pick positions in `s` that spell `t` as a subsequence. For `s = "babgbag"`, `t = "bag"` the answer is 5.

**Brute force.** Try all `C(len(s), len(t))` position sets. Fine for testing, exponential in general.

**State.** `dp[i][j]` = the number of ways `t[:j]` appears as a subsequence of `s[:i]`.

**Transition.** Decide about the last character `s[i-1]`.

- Do not use it: `dp[i-1][j]` ways.
- Use it as the final character of `t[:j]`: only allowed if `s[i-1] == t[j-1]`, giving `dp[i-1][j-1]` ways.

The two cases are disjoint (the last position is used or not), so the counts add:

$$
dp[i][j] = dp[i-1][j] + [s_{i-1} = t_{j-1}] \cdot dp[i-1][j-1]
$$

**Base cases.** `dp[i][0] = 1`: the empty target is matched in exactly one way, by choosing nothing. `dp[0][j] = 0` for `j > 0`. The empty construction counts once, as in [What DP Is](01-what-is-dp.md).

**Trace** (rows `s`, columns `t`):

| | "" | b | a | g |
|---|---|---|---|---|
| "" | 1 | 0 | 0 | 0 |
| b | 1 | 1 | 0 | 0 |
| a | 1 | 1 | 1 | 0 |
| b | 1 | 2 | 1 | 0 |
| g | 1 | 2 | 1 | 1 |
| b | 1 | 3 | 1 | 1 |
| a | 1 | 3 | 4 | 1 |
| g | 1 | 3 | 4 | 5 |

Each row depends only on the previous row. Iterating `j` **downwards** lets one array hold both, exactly like the 0/1 knapsack in [Knapsack and Coins](04-knapsack-and-coins.md): when we update `dp[j]`, `dp[j-1]` still holds the previous row's value.

```python
import random
from itertools import combinations


def num_distinct(s: str, t: str) -> int:
    dp = [1] + [0] * len(t)
    for ch in s:
        for j in range(len(t), 0, -1):   # downward: dp[j-1] is still old
            if ch == t[j - 1]:
                dp[j] += dp[j - 1]
    return dp[len(t)]


def brute(s: str, t: str) -> int:
    return sum(1 for idx in combinations(range(len(s)), len(t))
               if all(s[k] == c for k, c in zip(idx, t)))


def main():
    assert num_distinct("babgbag", "bag") == 5
    assert num_distinct("rabbbit", "rabbit") == 3
    assert num_distinct("abc", "") == 1
    assert num_distinct("", "a") == 0
    rng = random.Random(10)
    for _ in range(300):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 10)))
        t = "".join(rng.choice("ab") for _ in range(rng.randint(0, 4)))
        assert num_distinct(s, t) == brute(s, t)


if __name__ == "__main__":
    main()
```

Time O(nm), space O(m). The counts can grow exponentially; Python integers handle that, but other languages often ask for the answer modulo a prime.

## 8. Pattern matching: wildcards and regular expressions

Both problems ask whether a pattern `p` matches **all** of a string `s`. Both use `dp[i][j]` = "does `s[:i]` match `p[:j]`?" The interesting parts are the star and the first row.

### 9.1 Wildcard matching (`?` and `*`)

`?` matches exactly one character. `*` matches any sequence, including the empty one. Example: `"adceb"` matches `"*a*b"`; `"acdcb"` does not match `"a*c?b"`.

Transition on the last pattern character `p[j-1]`:

- An ordinary letter or `?`: it must match `s[i-1]`, and `dp[i][j] = dp[i-1][j-1]`.
- `*`: either it matches nothing (`dp[i][j-1]`), or it absorbs `s[i-1]` and may continue absorbing (`dp[i-1][j]`, same `j` because the star is still available).

$$
dp[i][j] =
\begin{cases}
dp[i][j-1] \lor dp[i-1][j], & p_{j-1} = \texttt{*},\\
dp[i-1][j-1] \land (p_{j-1} = \texttt{?} \lor p_{j-1} = s_{i-1}), & \text{otherwise.}
\end{cases}
$$

**Base row, carefully.** `dp[0][0] = True`. For the empty string, `dp[0][j]` is true only while every pattern character so far is `*`: `dp[0][j] = dp[0][j-1] and p[j-1] == '*'`. So `"**a*"` gives `T, T, T, F, F`. `dp[i][0] = False` for `i > 0`: an empty pattern matches only an empty string.

### 9.2 Regular-expression matching (`.` and `*`)

Here `.` matches one character, and `*` means "zero or more copies of **the preceding element**." So `"a*"` is a single unit: it never makes sense to read `*` on its own. Example: `"aab"` matches `"c*a*b"` (`c*` takes zero copies).

Transition on `p[j-1]`:

- Ordinary letter or `.`: `dp[i][j] = dp[i-1][j-1]` if it matches `s[i-1]`.
- `*` (with `x = p[j-2]`): two cases.
  - Zero copies of `x`: drop the pair, `dp[i][j-2]`.
  - One more copy: if `x` matches `s[i-1]`, absorb it and keep the pair, `dp[i-1][j]`.

$$
dp[i][j] = dp[i][j-2] \;\lor\; \bigl(\mathrm{match}(p_{j-2}, s_{i-1}) \land dp[i-1][j]\bigr) \quad \text{when } p_{j-1} = \texttt{*}.
$$

**Base row, carefully.** `dp[0][j]` is true when `p[:j]` can match the empty string, which is when it is made only of `x*` units: `dp[0][j] = p[j-1] == '*' and dp[0][j-2]`. For `"a*b*c"` the row is `T, F, T, F, T, F`. The common mistake is reusing the wildcard rule ("all stars so far"), which wrongly rejects the empty string for `"a*"`, or indexing `p[j-2]` when `j = 1`. We reject patterns that start with `*` or contain `**`.

We test against Python's own `fnmatch.fnmatchcase` and `re.fullmatch`, restricted to safe alphabets.

```python
import fnmatch
import random
import re


def wildcard_match(s: str, p: str) -> bool:
    n, m = len(s), len(p)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] and p[j - 1] == "*"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if p[j - 1] == "*":
                dp[i][j] = dp[i][j - 1] or dp[i - 1][j]
            else:
                dp[i][j] = dp[i - 1][j - 1] and p[j - 1] in ("?", s[i - 1])
    return dp[n][m]


def regex_match(s: str, p: str) -> bool:
    if p.startswith("*") or "**" in p:
        raise ValueError("'*' must follow a letter or '.'")
    n, m = len(s), len(p)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for j in range(2, m + 1):
        dp[0][j] = p[j - 1] == "*" and dp[0][j - 2]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if p[j - 1] == "*":
                x = p[j - 2]
                dp[i][j] = dp[i][j - 2] or (x in (".", s[i - 1]) and dp[i - 1][j])
            else:
                dp[i][j] = dp[i - 1][j - 1] and p[j - 1] in (".", s[i - 1])
    return dp[n][m]


def main():
    assert wildcard_match("adceb", "*a*b")
    assert not wildcard_match("acdcb", "a*c?b")
    assert wildcard_match("", "***") and not wildcard_match("", "?")
    assert regex_match("aab", "c*a*b")
    assert regex_match("", "a*b*") and not regex_match("", "a*b")
    assert regex_match("ab", ".*") and not regex_match("aa", "a")
    try:
        regex_match("a", "*a")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    rng = random.Random(11)
    for _ in range(2000):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 6)))
        p = "".join(rng.choice("ab?*") for _ in range(rng.randint(0, 6)))
        assert wildcard_match(s, p) == fnmatch.fnmatchcase(s, p), (s, p)
        units = [rng.choice("ab.") + rng.choice(["", "*"]) for _ in range(rng.randint(0, 4))]
        q = "".join(units)
        assert regex_match(s, q) == (re.fullmatch(q, s) is not None), (s, q)


if __name__ == "__main__":
    main()
```

Both run in O(nm) time and space; each row reads only the current and previous row, so O(m) space is possible. A greedy two-pointer method with backtracking to the last star also solves wildcard matching, but the DP is easier to prove.

## 9. Summary

| Problem | State | Last-decision cases | Base | Answer |
|---|---|---|---|---|
| LIS | `end[i]`: ending at `i` | Previous element `j < i` with `a[j] < a[i]`, or none | — | `max(end)` |
| LCS | `dp[i][j]`: prefixes `a[:i]`, `b[:j]` | Last characters match, or drop one | Row and column 0 are 0 | `dp[n][m]` |
| Common substring | `end[i][j]`: ending at both | Match extends, mismatch resets to 0 | 0 | `max` over cells |
| Edit distance | `dp[i][j]`: prefixes | Delete, insert, substitute/keep | `dp[i][0] = i`, `dp[0][j] = j` | `dp[n][m]` |
| Palindromic subsequence | `L[l][r]`: interval | Ends match, or drop one end | Empty 0, single 1 | `L[0][n]` |
| Distinct subsequences | `dp[i][j]`: prefixes | Use `s[i-1]` or not | `dp[i][0] = 1` | `dp[n][m]` |
| Wildcard / regex | `dp[i][j]`: does `s[:i]` match `p[:j]` | Last pattern character (or `x*` unit) | `dp[0][0] = True`, careful row 0 | `dp[n][m]` |

## 10. Pitfalls and practice

1. **Subsequence versus substring.** `"abcde"` and `"ace"` have LCS 3 but longest common substring 1. A substring recurrence must reset on a mismatch.
2. **Strict versus nondecreasing LIS.** `[2, 2, 2]` gives 1 or 3. Use `bisect_left` for strict, `bisect_right` for nondecreasing.
3. **The tails array is not an answer.** `[3, 4, 1]` ends with tails `[1, 4]`, which is not a subsequence. Reconstruct with predecessor indices.
4. **Counting LIS: sum over all endings** that reach the maximum length, not only the first one found.
5. **Edit-distance base cases are `i` and `j`, not 0.** An empty source exposes the bug. Also, adjacent swaps are not an operation.
6. **Edit scripts and shifting positions.** Record operations relative to the original strings, then verify by applying the script.
7. **Two different empty bases in interval palindromes.** `L[l][l] = 0` and `L[l][l+1] = 1`; the even-length case reads the empty interval.
8. **Empty target counts as one** in distinct subsequences; forgetting it makes every answer 0.
9. **Rolling one array needs the right direction.** Distinct subsequences iterates `j` downwards, so `dp[j-1]` is still the previous row.
10. **Pattern base rows.** Wildcard: all stars so far. Regex: `x*` units only, reading `dp[0][j-2]`. Reject a leading `*` in a regex.
11. **Repeated characters test reconstruction.** Inputs like `"aaaa"` and `"aa"` check that ties do not skip valid matches.

Practice: Longest Increasing Subsequence, Number of Longest Increasing Subsequence, Russian Doll Envelopes, Longest Common Subsequence, Maximum Length of Repeated Subarray, Edit Distance, Delete Operation for Two Strings, Longest Palindromic Subsequence, Palindromic Substrings, Longest Palindromic Substring, Distinct Subsequences, Wildcard Matching, Regular Expression Matching, Interleaving String, Shortest Common Supersequence.

Next: [Interval DP](07-interval-dp.md).
