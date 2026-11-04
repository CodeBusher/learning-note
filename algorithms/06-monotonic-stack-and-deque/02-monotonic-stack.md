# Monotonic Stack — The Nearest Greater or Smaller Neighbor

## 1. How many days until a warmer day?

For each day, how many days do you wait until a **strictly warmer** day? If none comes, the answer is `0`.

```text
day          0   1   2   3   4   5   6   7
temperature 73  74  75  71  69  72  76  73
answer       1   1   4   2   1   1   0   0
```

Day 2 (75) waits through 71, 69, 72 until day 6 (76): `6 − 2 = 4`. This array runs through the whole chapter.

**Brute force.** For each day, scan right until a warmer day appears. On a falling sequence `90, 89, 88, …` no scan ever stops early: `n(n − 1) / 2` comparisons, about 5 billion for `n = 10⁵`.

## 2. The key observation: the waiting days are sorted

Scan left to right. At any moment some earlier days are still **waiting**: no warmer day has appeared for them yet. After day 4 they are

```text
waiting:  day 2 (75)   day 3 (71)   day 4 (69)
```

The temperatures 75, 71, 69 never go up, and that is forced. If a waiting day `d` were colder than a later waiting day `e`, then `e` would have answered `d` when it arrived, and `d` would not be waiting.

Now day 5 (72) arrives. It answers the waiting days colder than 72, and because the list is sorted they are all at the **newest end**: 69, then 71. Then comes 75, which is not colder, and everything older than 75 is at least 75, so the search stops.

So the waiting days change only at their newest end: answered days leave there and the new day joins there. That is a stack (from [Stacks and Queues](01-stacks-and-queues.md)), and because its values stay sorted it is called a **monotonic stack**. "Monotonic" means moving in one direction only.

> **Invariant.** The stack holds the indices of the days that have no warmer day yet, oldest at the bottom; their temperatures are nonincreasing from bottom to top.

Store **indices**, not temperatures: the answer is a distance `j − i`, and the index gives both the position and, through `temps[i]`, the value.

## 3. Worked trace

The stack is written bottom to top as `index:temperature`.

| Day `j` | Temp | Pops (answer = `j − i`) | Stack after |
|---:|---:|---|---|
| 0 | 73 | — | `0:73` |
| 1 | 74 | `0:73` → answer[0] = 1 | `1:74` |
| 2 | 75 | `1:74` → answer[1] = 1 | `2:75` |
| 3 | 71 | — (75 is not colder) | `2:75  3:71` |
| 4 | 69 | — | `2:75  3:71  4:69` |
| 5 | 72 | `4:69` → answer[4] = 1, `3:71` → answer[3] = 2; stop at 75 | `2:75  5:72` |
| 6 | 76 | `5:72` → answer[5] = 1, `2:75` → answer[2] = 4 | `6:76` |
| 7 | 73 | — | `6:76  7:73` |

Days 6 and 7 are still waiting at the end, so their answers stay 0.

```python
import random


def daily_temperatures(temps: list[int]) -> list[int]:
    """answer[i] = days until a strictly warmer day, or 0 if none."""
    answer = [0] * len(temps)
    waiting: list[int] = []            # indices; temps nonincreasing bottom -> top
    for j, t in enumerate(temps):
        while waiting and temps[waiting[-1]] < t:
            i = waiting.pop()
            answer[i] = j - i
        waiting.append(j)
    return answer


def daily_temperatures_brute(temps: list[int]) -> list[int]:
    n = len(temps)
    answer = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if temps[j] > temps[i]:
                answer[i] = j - i
                break
    return answer


def count_comparisons(temps: list[int]) -> int:
    """Same loop as daily_temperatures, counting value comparisons."""
    waiting, comparisons = [], 0
    for j, t in enumerate(temps):
        while waiting:
            comparisons += 1
            if temps[waiting[-1]] >= t:
                break
            waiting.pop()
        waiting.append(j)
    return comparisons


def main():
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [
        1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([]) == []
    assert daily_temperatures([50]) == [0]
    assert daily_temperatures([70, 70, 71]) == [2, 1, 0]    # equal is not warmer
    assert daily_temperatures([3, 2, 1]) == [0, 0, 0]

    rng = random.Random(10)
    for _ in range(2000):
        temps = [rng.randrange(5) for _ in range(rng.randrange(12))]  # many ties
        assert daily_temperatures(temps) == daily_temperatures_brute(temps)
        assert count_comparisons(temps) <= 2 * len(temps)

    falling = list(range(1000, 0, -1))
    assert count_comparisons(falling) == 999          # brute force: 499,500


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`. **Space:** `O(n)` for the stack (a falling sequence keeps every day waiting).

**Why it is linear.** One iteration can pop many indices, so count per index, as in [Stacks and Queues §6](01-stacks-and-queues.md#6-amortized-cost-count-per-item-not-per-call): every index is pushed exactly once and popped at most once. Each `while` test either pops (at most `n` times in total) or fails and ends the loop (once per day). That is at most `2n` comparisons, which `count_comparisons` checks.

**Why it is correct.** Say day `j` pops day `i`, so `temps[j] > temps[i]`. Could a warmer day `k` lie between them? When `k` arrived, `i` was waiting, and every day above `i` on the stack was at most `temps[i] < temps[k]`, so `k` would have popped all of them and then `i`. But `i` was still there when `j` arrived. So `j` is the **nearest** warmer day. A day never popped has no warmer day after it, and 0 is right.

## 4. Variant: look left (previous greater) and dominance

Turn the question around: for each day, find the nearest **earlier** day that was strictly warmer, or `−1`.

Now the question is asked about the **current** day, so the stack should hold earlier days that could still be the answer for some later day. The key observation is **dominance**:

> When day `j` arrives, every earlier day `i` with `temps[i] <= temps[j]` is beaten. It can never again be the answer for anyone to the right.

Suppose a later day `x` would pick `i`, so `temps[i] > temps[x]`. Then `temps[j] >= temps[i] > temps[x]`, so `j` also qualifies, and `j` is closer to `x`. We say `j` **dominates** `i`: at least as good in value, and closer. So: pop every dominated day, read the top (if any) as `j`'s answer, push `j`.

Run it on the running array and the stack after each day is **exactly** the stack column of §3: the same days are popped by the same days. The answers are `[-1, -1, -1, 2, 3, 2, -1, 6]`; for example day 5 (72) pops 69 and 71 and then reads day 2 (75) on top. The loop is the same; only the meaning of a pop and the place the answer is written differ:

| Scanning left to right | A pop means | Answer written into |
|---|---|---|
| next greater (§3) | the current day **answers** the popped one | `answer[popped]` |
| previous greater (§4) | the current day **dominates** the popped one | `answer[current]`, after popping |

The two stacks differ only on equal values: §3 pops on `<`, this one on `<=` (§7).

**Stock span.** The span of a day is the number of consecutive days ending today whose value is at most today's. If the previous strictly greater day is `p` (or `−1`), the span is `today − p`. On the running array: `1, 2, 3, 1, 1, 3, 7, 1`. The code for both comes with the online version below.

## 5. Variant: online stock span

Now the values arrive **one at a time**, and each span must be returned before the next value is known: an **online** problem. The previous-greater stack only looks backward, so it already works online; it needs no index if it stores `(value, span)` pairs. When a pair is popped, its whole span belongs to the new day too: every day inside it was at most the popped value, which is at most today's.

| Value | Pops, adding their spans | Span | Stack after |
|---:|---|---:|---|
| 73 | — | 1 | `(73,1)` |
| 74 | `(73,1)`: 1 + 1 | 2 | `(74,2)` |
| 75 | `(74,2)`: 1 + 2 | 3 | `(75,3)` |
| 71 | — | 1 | `(75,3) (71,1)` |
| 69 | — | 1 | `(75,3) (71,1) (69,1)` |
| 72 | `(69,1)`, `(71,1)`: 1 + 1 + 1 | 3 | `(75,3) (72,3)` |
| 76 | `(72,3)`, `(75,3)`: 1 + 3 + 3 | 7 | `(76,7)` |
| 73 | — | 1 | `(76,7) (73,1)` |

```python
import random


class StockSpanner:
    def __init__(self):
        self._stack: list[tuple[int, int]] = []   # (value, span); values strictly decreasing

    def next(self, price: int) -> int:
        span = 1
        while self._stack and self._stack[-1][0] <= price:
            span += self._stack.pop()[1]
        self._stack.append((price, span))
        return span


def previous_greater(nums: list[int]) -> list[int]:
    """Nearest index to the left with a strictly greater value, or -1."""
    answer = [-1] * len(nums)
    stack: list[int] = []
    for j, x in enumerate(nums):
        while stack and nums[stack[-1]] <= x:     # dominated by j
            stack.pop()
        if stack:
            answer[j] = stack[-1]
        stack.append(j)
    return answer


def stock_spans(prices: list[int]) -> list[int]:
    """Offline spans: today minus the previous strictly greater day."""
    return [day - p for day, p in enumerate(previous_greater(prices))]


def spans_brute(prices: list[int]) -> list[int]:
    result = []
    for day, price in enumerate(prices):
        span = 1
        while day - span >= 0 and prices[day - span] <= price:
            span += 1
        result.append(span)
    return result


def main():
    temps = [73, 74, 75, 71, 69, 72, 76, 73]
    assert previous_greater(temps) == [-1, -1, -1, 2, 3, 2, -1, 6]
    spanner = StockSpanner()
    assert [spanner.next(p) for p in temps] == [1, 2, 3, 1, 1, 3, 7, 1]
    assert stock_spans([5, 5, 5]) == [1, 2, 3] and stock_spans([]) == []
    rng = random.Random(13)
    for _ in range(1000):
        prices = [rng.randrange(1, 6) for _ in range(rng.randrange(15))]
        spanner = StockSpanner()
        online = [spanner.next(p) for p in prices]
        assert online == stock_spans(prices) == spans_brute(prices)


if __name__ == "__main__":
    main()
```

`previous_greater` is `O(n)` time and space by the same push-once, pop-once count; each `next` call is `O(1)` amortized.

## 6. Variant: circular arrays

In a **circular** array the element after the last is the first, so "next greater" may wrap: in `[1, 2, 1]` the last `1` finds the `2` at index 1.

**Idea.** Walk `2n` steps with `current = step % n`. Push indices only during the first pass; during the second pass only **answer** waiting indices. Every index then sees all `n − 1` other positions after it.

| Step | Index | Value | Pops | Push? | Stack after |
|---:|---:|---:|---|---|---|
| 0 | 0 | 1 | — | yes | `0:1` |
| 1 | 1 | 2 | `0:1` → answer[0] = 2 | yes | `1:2` |
| 2 | 2 | 1 | — | yes | `1:2  2:1` |
| 3 | 0 | 1 | — (1 is not greater than 1) | no | `1:2  2:1` |
| 4 | 1 | 2 | `2:1` → answer[2] = 2 | no | `1:2` |
| 5 | 2 | 1 | — | no | `1:2` |

Index 1 holds the maximum and is never answered: `[2, -1, 2]`.

```python
import random


def next_greater_circular(nums: list[int]) -> list[int]:
    """Value of the first strictly greater element going around; -1 if none."""
    n = len(nums)
    answer = [-1] * n
    waiting: list[int] = []
    for step in range(2 * n):
        current = step % n
        while waiting and nums[waiting[-1]] < nums[current]:
            answer[waiting.pop()] = nums[current]
        if step < n:
            waiting.append(current)
    return answer


def next_greater_circular_brute(nums: list[int]) -> list[int]:
    n = len(nums)
    return [next((nums[(i + d) % n] for d in range(1, n) if nums[(i + d) % n] > nums[i]), -1)
            for i in range(n)]


def main():
    assert next_greater_circular([1, 2, 1]) == [2, -1, 2]
    assert next_greater_circular([3, 1, 2]) == [-1, 2, 3]
    assert next_greater_circular([2, 2]) == [-1, -1]
    assert next_greater_circular([]) == []
    rng = random.Random(14)
    for _ in range(2000):
        nums = [rng.randrange(4) for _ in range(rng.randrange(10))]
        assert next_greater_circular(nums) == next_greater_circular_brute(nums)


if __name__ == "__main__":
    main()
```

The strict `<` matters: on the second pass an index meets **itself** (step 3), and an element is not greater than itself. With `<=`, `[2, 2]` would answer each `2` with the other `2`. `O(n)` time and space.

## 7. Variant: ties, strict or not

Equal values are where these stacks go wrong. Two versions of "next greater" on `[70, 70, 71]`:

| Version | Pop while | Stack after day 1 | Answers |
|---|---|---|---|
| next strictly greater | `temps[top] < t` | `0:70  1:70` (both wait) | `[2, 1, 0]` |
| next greater or equal | `temps[top] <= t` | `1:70` (day 1 answered day 0) | `[1, 1, 0]` |

With the strict version equal values pile up and the stack is **nonincreasing**; with the non-strict version a new equal value pops the old one and the stack is **strictly decreasing**. Neither is "the right one": "warmer" means strictly greater, "at least as warm" means greater or equal. Say the relation out loud before writing the comparison, and always test a run of equal values such as `[5, 5, 5]`.

## 8. All eight neighbor queries

Four relations (`>`, `>=`, `<`, `<=`) and two sides give eight questions, such as "nearest index to the right with a value `<=` mine". The dominance reading of §4 handles all of them with one loop:

> Scan so that the side being asked about is already seen: left to right for "previous", right to left for "next". Before reading the top, pop every candidate that **fails the relation against the current element**. The current element dominates it: it is closer to every future query and passes whenever the popped one would.

Check for `>=`: a candidate fails when `candidate < x`. If it would pass for a future `y` (`candidate >= y`), then `x > candidate >= y`, so `x` passes too.

```python
import operator
import random

RELATIONS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}


def nearest(nums: list[int], relation: str, side: str) -> list[int]:
    """For each i, nearest index j on `side` with nums[j] <relation> nums[i].

    side is "left" (missing -> -1) or "right" (missing -> len(nums)).
    """
    if relation not in RELATIONS or side not in ("left", "right"):
        raise ValueError("bad relation or side")
    passes = RELATIONS[relation]
    n = len(nums)
    order = range(n) if side == "left" else range(n - 1, -1, -1)
    missing = -1 if side == "left" else n
    answer = [missing] * n
    stack: list[int] = []
    for i in order:
        while stack and not passes(nums[stack[-1]], nums[i]):
            stack.pop()                     # dominated by i
        if stack:
            answer[i] = stack[-1]
        stack.append(i)
    return answer


def next_by_resolving(nums: list[int], relation: str) -> list[int]:
    """Next-neighbor version scanning left to right, answering popped indices (§3)."""
    passes = RELATIONS[relation]
    answer = [len(nums)] * len(nums)
    waiting: list[int] = []
    for j, x in enumerate(nums):
        while waiting and passes(x, nums[waiting[-1]]):
            answer[waiting.pop()] = j
        waiting.append(j)
    return answer


def nearest_brute(nums: list[int], relation: str, side: str) -> list[int]:
    passes = RELATIONS[relation]
    n = len(nums)
    answer = []
    for i in range(n):
        if side == "left":
            js, missing = range(i - 1, -1, -1), -1
        else:
            js, missing = range(i + 1, n), n
        answer.append(next((j for j in js if passes(nums[j], nums[i])), missing))
    return answer


def main():
    nums = [2, 2, 1, 3]
    assert nearest(nums, ">", "right") == [3, 3, 3, 4]
    assert nearest(nums, ">=", "right") == [1, 3, 3, 4]
    assert nearest(nums, "<", "left") == [-1, -1, -1, 2]
    assert nearest(nums, "<=", "left") == [-1, 0, -1, 2]
    try:
        nearest(nums, "!=", "left")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(12)
    for _ in range(1500):
        nums = [rng.randrange(-2, 3) for _ in range(rng.randrange(11))]
        for relation in RELATIONS:
            for side in ("left", "right"):
                assert nearest(nums, relation, side) == nearest_brute(nums, relation, side)
            assert next_by_resolving(nums, relation) == nearest(nums, relation, "right")


if __name__ == "__main__":
    main()
```

Each query is `O(n)` time and space. The test also confirms that the left-to-right "answers" loop of §3 (`next_by_resolving`) gives the same next-neighbor results as the right-to-left dominance loop.

## 9. Summary

| Nearest neighbor wanted | Scan order | Pop the top while | Missing answer | Stack values, bottom → top |
|---|---|---|---:|---|
| previous `>` | left → right | `nums[top] <= x` | `-1` | strictly decreasing |
| previous `>=` | left → right | `nums[top] < x` | `-1` | nonincreasing |
| previous `<` | left → right | `nums[top] >= x` | `-1` | strictly increasing |
| previous `<=` | left → right | `nums[top] > x` | `-1` | nondecreasing |
| next `>` | right → left | `nums[top] <= x` | `n` | strictly decreasing |
| next `>=` | right → left | `nums[top] < x` | `n` | nonincreasing |
| next `<` | right → left | `nums[top] >= x` | `n` | strictly increasing |
| next `<=` | right → left | `nums[top] > x` | `n` | nondecreasing |

The missing answers `-1` and `n` are **sentinels**, positions immediately outside the array. They make widths come out right later (`R − L − 1` in [Contributions and Boundaries](05-contributions-and-boundaries.md)).

**What a stack cannot do.** A monotonic stack answers *nearest* questions because a beaten candidate is never needed again, and beaten candidates are always the newest ones. It does not answer the maximum of an arbitrary range `[l, r]` (use a sparse table or a [segment tree](../04-range-queries/03-segment-tree.md)), the maximum of the last `k` elements when old ones **expire** (use the deque of [Monotonic Deque](04-monotonic-deque.md)), or the `k`-th largest so far (use a [heap](../07-heaps-and-priority-queues/README.md)). If a candidate can become useless *because it is too old*, a stack alone is not enough.

## 10. Pitfalls and practice

1. **Storing values instead of indices.** Distances, widths and equal values at different positions all need the index.
2. **Choosing `<` or `<=` without saying the relation.** Test `[5, 5, 5]` and `[70, 70, 71]` (§7).
3. **Writing the answer in the wrong place.** Into the popped index for "next" read as answering, into the current index for "previous" read as dominance (§4).
4. **Indexing `nums[-1]` with a sentinel.** In Python it reads the last element instead of failing. Check for the sentinel first.
5. **Pushing again on the second circular pass, or popping on `<=` there.** An element then answers itself (§6).
6. **Believing the loop is quadratic, or that each step pops a constant number.** The true statement is at most `n` pops in total.
7. **Using a stack when candidates expire by age.** That needs a deque.

Practice: daily temperatures; next greater element I (answers looked up in a second array); next greater element II (circular); online stock span; final prices with a special discount; next greater node in a linked list; number of visible people in a queue; buildings with an ocean view; beautiful towers (previous smaller with sums).

Next: [Stack Applications](03-stack-applications.md).
