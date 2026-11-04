# What Dynamic Programming Is — From Recursion to a Table

## 1. Climbing stairs

A staircase has `n` steps. Each move climbs **1 or 2 steps**. How many different sequences of moves land exactly on step `n`?

| n | Move sequences | Count |
|---:|---|---:|
| 1 | `1` | 1 |
| 2 | `1+1`, `2` | 2 |
| 3 | `1+1+1`, `1+2`, `2+1` | 3 |
| 4 | `1+1+1+1`, `1+1+2`, `1+2+1`, `2+1+1`, `2+2` | 5 |

Order matters: `1+2` and `2+1` are different sequences. For `n = 50` there are over 20 billion sequences, so we need to count them without listing them.

## 2. The recurrence: look at the last move

Every sequence that lands on step `n` has a **last move**, and it was either 1 step or 2 steps:

- Last move 1 step: the moves before it landed on `n − 1`. Any sequence for `n − 1` works.
- Last move 2 steps: the moves before it landed on `n − 2`. Any sequence for `n − 2` works.

Write `ways(n)` for the number of sequences that land on step `n`. A sequence has only one last move, so the two cases never overlap, and together they cover every sequence:

$$
ways(n)=ways(n-1)+ways(n-2)\qquad (n\ge2).
$$

Check: `ways(4) = ways(3) + ways(2) = 3 + 2 = 5`.

**Base cases.** The rule reads two smaller answers, so the two smallest are answered directly: `ways(1) = 1`, and `ways(0) = 1`.

Why is `ways(0)` 1 and not 0? Standing at the bottom, there is exactly one way to "be on step 0": make no moves. The recurrence needs it: `ways(2) = ways(1) + ways(0)` must be 2 (`1+1` and `2`). With `ways(0) = 0`, the sequence `2` would never be counted. **The empty sequence counts as one way** in nearly every counting DP.

## 3. Plain recursion, and why it is slow

The recurrence translates directly into code, and the code is correct. But `ways(40)` takes a long time. Here is every call that `ways(5)` makes:

```text
                         ways(5)
                ┌───────────┴───────────┐
             ways(4)                 ways(3)
           ┌────┴────┐             ┌────┴────┐
        ways(3)    ways(2)      ways(2)    ways(1)
        ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
    ways(2) ways(1) w(1) w(0)   w(1) w(0)
     ┌──┴──┐
   w(1)  w(0)
```

`ways(3)` is computed twice and `ways(2)` three times, each time from scratch. The waste grows fast:

| n | Calls made by plain recursion | Different questions |
|---:|---:|---:|
| 5 | 15 | 6 |
| 10 | 177 | 11 |
| 20 | 21,891 | 21 |
| 30 | 2,692,537 | 31 |
| 50 | about 40,000,000,000 | 51 |

There are only `n + 1` different questions, `ways(0)` to `ways(n)`, but the recursion asks them billions of times. The call count multiplies by about 1.6 each time `n` grows by 1: **exponential** growth. The subproblems **overlap**: the same smaller question appears in many branches. That is what DP fixes.

```python
def ways(n: int) -> int:
    """Plain recursion: correct, but exponential."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n <= 1:
        return 1
    return ways(n - 1) + ways(n - 2)


def count_calls(n: int) -> int:
    """How many calls the plain recursion makes for ways(n)."""
    if n <= 1:
        return 1
    return 1 + count_calls(n - 1) + count_calls(n - 2)


def main():
    assert [ways(n) for n in range(8)] == [1, 1, 2, 3, 5, 8, 13, 21]
    assert count_calls(5) == 15
    assert count_calls(10) == 177
    assert count_calls(20) == 21891


if __name__ == "__main__":
    main()
```

## 4. Fix 1: remember every answer (memoization, top-down)

Keep the recursion, but before computing `ways(k)`, look it up in a dictionary. If it is there, return it; otherwise compute it once and store it. This is **memoization** (from "memo", a note to yourself).

The tree for `ways(5)` collapses. Each question is computed the first time it is asked and looked up every later time:

```text
ways(5)
├── ways(4)
│   ├── ways(3)
│   │   ├── ways(2)
│   │   │   ├── ways(1)   base case
│   │   │   └── ways(0)   base case
│   │   └── ways(1)       base case
│   └── ways(2)           found in memo
└── ways(3)               found in memo
```

Each `ways(k)` is computed once with two lookups, so the total work is proportional to `n`: **linear** instead of exponential. `ways(50)` takes about 100 steps instead of 40 billion. Python's `functools.cache` does the dictionary bookkeeping for you; both forms are below.

```python
from functools import cache


def ways_memo(n: int) -> tuple[int, int]:
    """Return (ways(n), how many times a value was actually computed)."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    memo = {}

    def ways(k: int) -> int:
        if k <= 1:
            return 1
        if k not in memo:
            memo[k] = ways(k - 1) + ways(k - 2)
        return memo[k]

    return ways(n), len(memo)


@cache
def ways_cached(k: int) -> int:
    if k <= 1:
        return 1
    return ways_cached(k - 1) + ways_cached(k - 2)


def ways_plain(k: int) -> int:
    return 1 if k <= 1 else ways_plain(k - 1) + ways_plain(k - 2)


def main():
    for n in range(20):
        assert ways_memo(n)[0] == ways_cached(n) == ways_plain(n)
    assert ways_memo(50) == (20365011074, 49)  # ways(2)..ways(50), once each.
    assert ways_cached(50) == 20365011074


if __name__ == "__main__":
    main()
```

Memoization is called **top-down DP**: you start from the question you want, `ways(n)`, and the recursion reaches down to the smaller questions it needs, in whatever order it meets them. Any recursive search, DFS included, becomes DP the moment it caches answers to repeated subproblems. [Choosing the State §4](03-states-and-reconstruction.md#4-top-down-or-bottom-up-and-why-dfs--memo-is-dp) shows this on word break.

## 5. Fix 2: fill a table in dependency order (tabulation, bottom-up)

Memoization still recurses. Python raises `RecursionError` at a depth of about 1000, so `ways_memo(5000)` fails.

Look at the dependencies instead. `ways(k)` reads only `ways(k − 1)` and `ways(k − 2)`, which are smaller. If we compute answers in increasing `k`, everything a step reads is already done. Store them in a list, `dp[k] = ways(k)`:

| k | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dp[k]` | 1 | 1 | 1+1 = 2 | 2+1 = 3 | 3+2 = 5 | 5+3 = 8 | 8+5 = 13 |

This is **tabulation**, or **bottom-up DP**: start from the base cases and build upward. It computes the same states with the same recurrence as memoization. The only difference is who chooses the order: the recursion discovers it on demand, while the loop states it up front. No recursion means no depth limit.

## 6. Keep only what you still need

`dp[k]` looks back only two cells, so everything older is never read again. Keep two variables and slide them forward:

| After `j` loop steps | `older` | `newer` |
|---:|---:|---:|
| 0 | `ways(0)` = 1 | `ways(1)` = 1 |
| 1 | `ways(1)` = 1 | `ways(2)` = 2 |
| 2 | `ways(2)` = 2 | `ways(3)` = 3 |

This is a **space optimization**: same recurrence, same order, less memory. Get the full table right first. Shrinking memory before the recurrence is correct makes bugs much harder to find.

Both versions below are tested against a brute force that lists every move sequence, which is the definition of the problem.

```python
from itertools import product


def ways_brute(n: int) -> int:
    """Count sequences of 1s and 2s that sum to n by listing them all."""
    return sum(
        1
        for length in range(n + 1)
        for moves in product((1, 2), repeat=length)
        if sum(moves) == n
    )


def ways_table(n: int) -> int:
    if n < 0:
        raise ValueError("n must be nonnegative")
    dp = [1] * (n + 1)  # dp[0] = dp[1] = 1
    for k in range(2, n + 1):
        dp[k] = dp[k - 1] + dp[k - 2]
    return dp[n]


def ways_rolling(n: int) -> int:
    if n < 0:
        raise ValueError("n must be nonnegative")
    older, newer = 1, 1  # ways(0), ways(1)
    for _ in range(n - 1):
        older, newer = newer, older + newer
    return newer


def main():
    for n in range(13):
        assert ways_table(n) == ways_rolling(n) == ways_brute(n)
    assert ways_rolling(50) == 20365011074
    assert ways_table(5000) == ways_rolling(5000)  # No recursion limit here.


if __name__ == "__main__":
    main()
```

Time O(n) for both; space O(n) for the table and O(1) variables for the rolling version. The numbers themselves grow: `ways(5000)` has over a thousand digits. Python integers grow automatically, so "O(1)" here means a constant number of variables, not of bits.

## 7. Variant: same steps, different question

The recurrence came from asking "what was the last move?". Variations change only how the cases are combined:

| Question | Combine the cases with | Value at step 0 | Impossible state |
|---|---|---|---|
| How many sequences reach step `n`? | `+` | 1 (the empty sequence) | 0 |
| Can you reach step `n` at all? | `or` | `True` | `False` |
| Landing on step `k` costs `cost[k]`; cheapest way up? | `min`, then add the landing cost | 0 | `inf` |

Different allowed moves change only the list of last moves. With moves of 1, 3 or 5 steps:

$$
ways(n)=ways(n-1)+ways(n-3)+ways(n-5),
$$

where `ways` of a negative number is 0: you can't overshoot and come back.

## 8. When does DP apply?

Two things must hold:

1. **The answer is built from answers to smaller versions of the same question.** For optimization problems this is called *optimal substructure*: a best solution is made of best solutions to subproblems.
2. **The smaller questions overlap.** Many branches ask the same question, so remembering answers saves work.

With only the first, you have **divide and conquer**. Merge sort splits an array into halves that share no elements, so no question repeats and a cache would never be hit.

## 9. Summary

| Version | Time | Extra memory | Notes |
|---|---:|---:|---|
| Plain recursion | Exponential | O(n) call stack | Recomputes the same questions |
| Memoization (top-down) | O(n) | O(n) memo + O(n) stack | Order found by the recursion; depth limit applies |
| Table (bottom-up) | O(n) | O(n) list | You choose an order where dependencies come first |
| Rolling variables | O(n) | O(1) variables | Only because each step looks back a fixed distance |

Every DP in these notes is described with the same five words:

| Word | Meaning | Climbing stairs |
|---|---|---|
| **State** | One smaller question, named by a few parameters | `ways(k)`: sequences landing on step `k` |
| **Transition** | How a state's answer is built from other states | `ways(k) = ways(k−1) + ways(k−2)`, from the last move |
| **Base case** | States answered directly | `ways(0) = 1`, `ways(1) = 1` |
| **Evaluation order** | An order in which every state's dependencies are ready | Increasing `k` |
| **Answer** | Which state answers the original question | `ways(n)` |

Write the state as a sentence. "`dp[k]` is the number of move sequences that land exactly on step `k`" is a definition you can check every other line against. "`dp[k]` is the stairs thing" is not.

## 10. Pitfalls and practice

1. **`ways(0) = 0`.** The empty sequence is one way; without it, every sequence whose last move starts at the bottom is lost.
2. **A missing base case**, so the recursion calls `ways(−1)` or never stops.
3. **Deep memoization in Python.** Switch to a table when the depth can exceed about 1000.
4. **Shrinking memory first.** Get the full table right before rolling it (§6).
5. **DP without overlap.** It still works, but the bookkeeping buys nothing.

Practice: climbing stairs; Fibonacci number; N-th Tribonacci number; climbing stairs with moves `{1, 3, 5}`; count the tilings of a `2 × n` board with `2 × 1` dominoes. Write the state sentence before any code.

Next: [Designing a Recurrence](02-designing-a-recurrence.md).
