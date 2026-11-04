# Designing a Recurrence — The Last-Decision Method

## 1. House robber: take it or skip it

A row of houses holds amounts of money `nums[0], nums[1], …`. You may rob any houses except **two adjacent ones**. What is the most money you can take?

For `nums = [2, 7, 9, 3, 1]`, the best is houses 0, 2 and 4: `2 + 9 + 1 = 12`.

**Brute force.** Each house is either robbed or not: `2^n` choices, minus the ones with adjacent robberies. For 40 houses that is about a trillion.

**State, as a sentence.** `best[i]` = the most money obtainable from the **first `i` houses**, `nums[:i]`. Say what the number measures (here a maximum) and exactly which part of the input it covers.

**Last decision.** As with climbing stairs, ask what happened to the last house in range, house `i − 1`. List every possibility:

- **Skip it.** Then the solution is any valid solution for the first `i − 1` houses: `best[i − 1]`.
- **Rob it.** Then house `i − 2` must be skipped, and the rest is any valid solution for the first `i − 2` houses: `best[i − 2] + nums[i − 1]`.

We want the better of the two:

$$
best[i]=\max\big(best[i-1],\ best[i-2]+nums[i-1]\big).
$$

**Base cases.** `best[0] = 0` (no houses, no money). `best[1] = nums[0]` (one house: rob it, assuming amounts are nonnegative).

**Order and answer.** Increasing `i`. The answer is `best[n]`.

**Trace** for `[2, 7, 9, 3, 1]`:

| i | House `i−1` | Skip it: `best[i−1]` | Rob it: `best[i−2] + nums[i−1]` | `best[i]` |
|---:|---:|---:|---:|---:|
| 0 | — | — | — | 0 |
| 1 | 2 | — | — | 2 |
| 2 | 7 | 2 | 0 + 7 = 7 | 7 |
| 3 | 9 | 7 | 2 + 9 = 11 | 11 |
| 4 | 3 | 11 | 7 + 3 = 10 | 11 |
| 5 | 1 | 11 | 11 + 1 = 12 | **12** |

```python
from itertools import product
from random import Random


def rob(nums: list[int]) -> int:
    """Most money from nonadjacent houses; amounts must be nonnegative."""
    if any(x < 0 for x in nums):
        raise ValueError("amounts must be nonnegative")
    n = len(nums)
    best = [0] * (n + 1)
    if n >= 1:
        best[1] = nums[0]
    for i in range(2, n + 1):
        best[i] = max(best[i - 1], best[i - 2] + nums[i - 1])
    return best[n]


def rob_brute(nums: list[int]) -> int:
    best = 0
    for choice in product((False, True), repeat=len(nums)):
        if any(choice[i] and choice[i + 1] for i in range(len(nums) - 1)):
            continue
        best = max(best, sum(x for x, taken in zip(nums, choice) if taken))
    return best


def main():
    assert rob([2, 7, 9, 3, 1]) == 12
    assert rob([1, 2, 3, 1]) == 4
    assert rob([]) == 0
    assert rob([5]) == 5
    rng = Random(1)
    for _ in range(300):
        nums = [rng.randrange(0, 10) for _ in range(rng.randrange(0, 11))]
        assert rob(nums) == rob_brute(nums)


if __name__ == "__main__":
    main()
```

Time O(n), space O(n). Each `best[i]` reads only the two previous entries, so two rolling variables suffice, as in [What DP Is §6](01-what-is-dp.md).

**Why it is correct.** Every valid robbery plan of the first `i` houses either skips house `i − 1` or robs it. If it skips it, what remains is a valid plan for `i − 1` houses. If it robs it, house `i − 2` is untouched and what remains is a valid plan for `i − 2` houses. So every plan is considered, and every plan the recurrence builds is valid.

## 2. Variant: minimum-cost stairs

Each stair `k` costs `cost[k]` when you stand on it. You may start on stair 0 or 1 for free, climb 1 or 2 stairs per move, and must reach the **top**: the position past the last stair. For `cost = [10, 15, 20]`: start on stair 1, pay 15, jump 2 to the top, total 15.

Only the combining rule changes from climbing stairs: `min` over costs instead of `+` over counts. With `pay[k]` = the cheapest total to **stand on** position `k`, not yet paying for `k`:

$$
pay[k]=\min\big(pay[k-1]+cost[k-1],\ pay[k-2]+cost[k-2]\big),\qquad pay[0]=pay[1]=0.
$$

| k | 0 | 1 | 2 | 3 (top) |
|---|---:|---:|---:|---:|
| `pay[k]` | 0 | 0 | min(0 + 15, 0 + 10) = 10 | min(10 + 20, 0 + 15) = **15** |

The definition decides the edge case: with `cost = [5]`, the top is position 1, a free starting position, so the answer is 0, not 5.

## 3. Decode ways: counting with conditions

A message of letters is encoded as digits with `A = 1, B = 2, …, Z = 26`. Given a digit string, how many letter strings could it have come from?

`"226"` can be read as `2 2 6` (BBF), `22 6` (VF) or `2 26` (BZ): 3 ways. `"06"` has 0 ways, because no letter is written `0` or `06`.

**State.** `ways[i]` = the number of ways to decode the **first `i` digits**, `s[:i]`.

**Last decision.** The last letter used either the last **one** digit or the last **two** digits:

- **One digit** `s[i − 1]`: valid only if it is `1`–`9`. Then the rest is any decoding of `s[:i − 1]`.
- **Two digits** `s[i − 2:i]`: valid only if they form `10`–`26`. A leading zero such as `06` is not allowed. Then the rest is any decoding of `s[:i − 2]`.

$$
ways[i]=[\,s_{i-1}\ne 0\,]\cdot ways[i-1]+[\,10\le s_{i-2}s_{i-1}\le 26\,]\cdot ways[i-2],
$$

where `[condition]` is 1 when the condition holds and 0 otherwise. A case that is invalid contributes nothing; it does not make the whole count zero.

**Base case.** `ways[0] = 1`: the empty string has one decoding, the empty message. As with `ways(0)` for stairs, this makes the first real letter count correctly.

**Trace** for `"226"`:

| i | Prefix | One digit | Two digits | `ways[i]` |
|---:|---|---|---|---:|
| 0 | `""` | — | — | 1 |
| 1 | `"2"` | `2` ok → `ways[0]` = 1 | — | 1 |
| 2 | `"22"` | `2` ok → `ways[1]` = 1 | `22` ok → `ways[0]` = 1 | 2 |
| 3 | `"226"` | `6` ok → `ways[2]` = 2 | `26` ok → `ways[1]` = 1 | **3** |

```python
from random import Random


def decode_ways(s: str) -> int:
    if not s.isdigit() and s:
        raise ValueError("digits only")
    n = len(s)
    ways = [0] * (n + 1)
    ways[0] = 1
    for i in range(1, n + 1):
        if s[i - 1] != "0":
            ways[i] += ways[i - 1]
        if i >= 2 and 10 <= int(s[i - 2:i]) <= 26:
            ways[i] += ways[i - 2]
    return ways[n]


def decode_brute(s: str) -> int:
    if not s:
        return 1
    total = 0
    if s[0] != "0":
        total += decode_brute(s[1:])
    if len(s) >= 2 and 10 <= int(s[:2]) <= 26:
        total += decode_brute(s[2:])
    return total


def main():
    assert decode_ways("226") == 3
    assert decode_ways("12") == 2
    assert decode_ways("06") == 0
    assert decode_ways("10") == 1
    assert decode_ways("100") == 0
    assert decode_ways("") == 1
    rng = Random(3)
    for _ in range(500):
        s = "".join(rng.choice("0123456789") for _ in range(rng.randrange(0, 12)))
        assert decode_ways(s) == decode_brute(s)


if __name__ == "__main__":
    main()
```

`decode_brute` is the plain recursion from the front. It is exponential, but trustworthy on short strings. Check `"100"`: the last `0` can only pair with the middle `0` as `00`, which is not a letter, so there are 0 ways.

## 4. Maximum subarray: "ending exactly at i"

Find the largest sum of a **contiguous, nonempty** run of an array. For `[-2, 1, -3, 4, -1, 2, 1, -5, 4]` the answer is 6, from `[4, -1, 2, 1]`.

Try the usual state first: "`best[i]` = the largest subarray sum within the first `i` elements." The last-decision question breaks down. Element `i − 1` might extend a run that ends at `i − 2`, but `best[i − 1]` doesn't say whether its best run ends there or somewhere earlier. The state **forgot something the future needs**.

Fix the state so it remembers it:

**State.** `end[i]` = the largest sum of a subarray that **ends exactly at index `i`**.

**Last decision.** A subarray ending at `i` is either `[a[i]]` alone, or extends a subarray ending at `i − 1`:

$$
end[i]=a[i]+\max\big(0,\ end[i-1]\big).
$$

Extend only if the best run ending at `i − 1` has a positive sum; otherwise start fresh at `i`.

**Answer.** The best subarray ends *somewhere*, so the answer is `max(end[i])` over all `i`, not `end[n − 1]`.

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `a[i]` | −2 | 1 | −3 | 4 | −1 | 2 | 1 | −5 | 4 |
| `end[i]` | −2 | 1 | −2 | 4 | 3 | 5 | **6** | 1 | 5 |

This is **Kadane's algorithm**.

```python
from random import Random


def max_subarray(a: list[int]) -> int:
    if not a:
        raise ValueError("a nonempty subarray needs a nonempty array")
    ending_here = best = a[0]
    for x in a[1:]:
        ending_here = x + max(0, ending_here)
        best = max(best, ending_here)
    return best


def max_subarray_brute(a: list[int]) -> int:
    return max(sum(a[l:r]) for l in range(len(a)) for r in range(l + 1, len(a) + 1))


def main():
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_subarray([-3, -1, -2]) == -1  # nonempty: the best single element
    assert max_subarray([5]) == 5
    rng = Random(4)
    for _ in range(500):
        a = [rng.randrange(-10, 11) for _ in range(rng.randrange(1, 12))]
        assert max_subarray(a) == max_subarray_brute(a)


if __name__ == "__main__":
    main()
```

If the empty subarray (sum 0) were allowed, the answer would be `max(0, max(end))`. Always check whether "nothing" is a legal answer.

## 5. Impossible states are not zero

So far every state could be reached. Many problems have states that **can't be reached at all**, and those must not be confused with states whose answer is 0.

**Example.** Moves are 3 or 5 steps. What is the fewest number of moves to land **exactly** on step `n`? Steps 1, 2, 4 and 7 can't be reached at all.

If unreachable steps stored 0, the recurrence `fewest[n] = 1 + min(fewest[n − 3], fewest[n − 5])` would read `fewest[1] = 0` and claim that step 4 takes one move. Use a value that can never win instead: **positive infinity** for a minimum.

For counting, impossible and zero coincide: "0 ways" really means unreachable. For a minimum they don't. Python's `math.inf` loses every `min`, and `inf + 1` is still `inf`, so an impossible predecessor stays impossible with no special code. For a maximum, use `-inf` the same way.

## 6. Pull and push: two ways to fill the table

The recurrences above **pull**: to compute `dp[i]`, read the states it depends on. You can also **push**: once `dp[j]` is final, send its value forward to every state it leads to.

Push on the 3-or-5 problem, `n = 8`. Each row is one `j` whose value is final; unreachable `j` send nothing:

| `j` | `fewest[j]` | Sends |
|---:|---:|---|
| 0 | 0 | `fewest[3] = 1`, `fewest[5] = 1` |
| 1, 2 | `inf` | nothing |
| 3 | 1 | `fewest[6] = 2`, `fewest[8] = 2` |
| 4 | `inf` | nothing |
| 5 | 1 | `fewest[8] = min(2, 2) = 2` (and 10 is past the end) |
| 6, 7, 8 | 2, `inf`, 2 | every target is past 8 |

Pull computes the same numbers, but at `i = 8` it reads `fewest[5]` and `fewest[3]` itself.

```python
from math import inf
from random import Random


def fewest_moves_pull(n: int, moves=(3, 5)) -> int | None:
    fewest = [inf] * (n + 1)
    fewest[0] = 0
    for i in range(1, n + 1):
        for m in moves:
            if m <= i:
                fewest[i] = min(fewest[i], fewest[i - m] + 1)
    return None if fewest[n] == inf else fewest[n]


def fewest_moves_push(n: int, moves=(3, 5)) -> int | None:
    fewest = [inf] * (n + 1)
    fewest[0] = 0
    for j in range(n + 1):
        if fewest[j] == inf:
            continue  # nothing to send from an unreachable step
        for m in moves:
            if j + m <= n:
                fewest[j + m] = min(fewest[j + m], fewest[j] + 1)
    return None if fewest[n] == inf else fewest[n]


def fewest_moves_brute(n: int) -> int | None:
    options = [a + b for a in range(n // 3 + 1) for b in range(n // 5 + 1)
               if 3 * a + 5 * b == n]
    return min(options) if options else None


def main():
    assert [fewest_moves_pull(n) for n in range(9)] == [0, None, None, 1, None, 1, 2, None, 2]
    for n in range(80):
        expected = fewest_moves_brute(n)
        assert fewest_moves_pull(n) == expected
        assert fewest_moves_push(n) == expected
    rng = Random(5)
    for _ in range(100):
        moves = tuple(sorted(set(rng.randrange(1, 9) for _ in range(rng.randrange(1, 4)))))
        n = rng.randrange(0, 40)
        assert fewest_moves_pull(n, moves) == fewest_moves_push(n, moves)


if __name__ == "__main__":
    main()
```

Both compute the same table. Pull is usually easier to prove correct, because each state's formula is in one place. Push is handy when it is easier to list where a state *leads* than where it *came from*, and it skips unreachable states, as the `continue` does. Either way, a state must be **final** before it is read or pushed: before you push from `j`, every arrow into `j` must already have arrived. Here that holds because every move goes forward.

Pull and push are about the **direction of each update**; top-down and bottom-up ([What DP Is §4–5](01-what-is-dp.md)) are about **who picks the order**. They combine:

| | Pull | Push |
|---|---|---|
| **Bottom-up** (a loop picks the order) | `fewest_moves_pull` | `fewest_moves_push` |
| **Top-down** (recursion picks the order) | The natural form: a call asks for the states it depends on | Rare: a recursive call cannot send a value to a state that has not been asked for yet |

[Choosing the State §4](03-states-and-reconstruction.md#4-top-down-or-bottom-up-and-why-dfs--memo-is-dp) compares the corners on word break, and shows when each one does less work.

## 7. Summary: the last-decision method

1. **Write the state as a sentence**: what the number measures (count, minimum, maximum, true/false) and which part of the input it covers.
2. **Ask what the last decision was**, and list every case. The cases must cover every solution, never count one twice, and each must leave a valid solution of a smaller state.
3. **Write the recurrence**, and give the empty input its value.
4. **Mark impossible states** with a value that can never win.
5. **Pick an order** where every dependency comes first, and say which state holds the answer.
6. **Trace a small example** in a table before writing code, then test against a brute force on tiny inputs, including empty, impossible and all-negative ones.

| Kind of question | Empty / start state | Impossible state | Combine cases with |
|---|---|---|---|
| Can it be done? | `True` | `False` | `or` |
| How many ways? | `1` | `0` | `+` |
| Minimum cost | `0` | `inf` | `min` |
| Maximum value | `0` (if the empty solution is allowed) | `-inf` | `max` |

| State shape | Sentence | Use when | Answer |
|---|---|---|---|
| **Prefix** | "using the first `i` elements" | A solution can skip elements freely (house robber, decode ways) | `dp[n]` |
| **Ending at** | "ending exactly at element `i`" | The solution is contiguous, or the next step must know where the last piece ended (maximum subarray) | `max(dp)` over all `i` |

## 8. Pitfalls and practice

1. Using "first `i`" for a contiguous problem. If the next step needs to know where the last piece ended, use "ending at `i`".
2. Returning `dp[n − 1]` when the answer is `max(dp)`.
3. Treating an invalid case as "the whole count is zero" instead of "this case contributes zero" (decode ways).
4. Storing 0 for an impossible minimum.
5. Assuming the empty answer is allowed, or forbidden, without checking the problem.

Practice: house robber; house robber II (houses in a circle: run the line version twice, once without the first house and once without the last); min cost climbing stairs; decode ways; maximum subarray; maximum product subarray (track both the largest and the smallest product ending at `i`); delete and earn (reduce it to house robber over values); perfect squares.

Next: [Choosing the State and Rebuilding the Answer](03-states-and-reconstruction.md).
