# Choosing the State and Rebuilding the Answer — What to Remember, and How to Get the Solution Back

## 1. What must a state remember?

Take house robber with `nums = [2, 7, 9, 3, 1]` and look at two plans for the first 3 houses:

| Plan | Robbed | Money so far | Robbed house 2? |
|---|---|---:|---|
| A | houses 0, 2 | 11 | yes |
| B | house 1 | 7 | no |

A DP whose state is "the first 3 houses are decided" keeps only the best value, 11, and forgets plan B. But the plans don't have the same future: plan A may not rob house 3, plan B may. A transition that decides house 3 by looking only at the stored best value can't tell whether that is allowed.

A state is a **summary** of a partial solution. DP merges every partial solution with the same summary and keeps only the best one (or the count). That is safe only when the summary holds everything the future depends on:

> **History test.** Two partial solutions that share a state must have exactly the same possible futures, and each future must add the same amount to both.

"First `i` houses decided" fails the test when the next step looks one house ahead. There are two fixes.

- **Change the transition.** [Designing a Recurrence §1](02-designing-a-recurrence.md#1-house-robber-take-it-or-skip-it) jumps two houses back when robbing, so the transition itself guarantees the gap and the state never has to remember it.
- **Add the missing fact to the state.** Keep two numbers per position:
  - `skip[i]` = the most money from the first `i` houses, **with house `i − 1` not robbed**;
  - `took[i]` = the same, **with house `i − 1` robbed**.

$$
skip[i]=\max(skip[i-1],\ took[i-1]),\qquad took[i]=skip[i-1]+nums[i-1].
$$

Now plan A lives in `took[3] = 11` and plan B in `skip[3] = 7`. Within each state every plan has the same options for house 3, so the test passes.

The second fix is the general one: **when the future depends on a fact about the past, put that fact in the state**, and keep it as small as possible, because each extra fact multiplies the number of states. The opposite mistake is remembering **too much**. If the state were the full list of robbed houses, no two partial solutions would ever share a state, nothing would merge, and the DP would be as slow as brute force.

## 2. Word break: one state, three questions

Given a string and a dictionary, split the string into dictionary words. For `s = "catsanddog"` and dictionary `{cat, cats, and, sand, dog}`, there are two splits: `cats and dog` and `cat sand dog`.

**State.** Position `i` in the string, meaning the prefix `s[:i]` has been split completely.

Does it pass the history test? Two different splits of `s[:i]` leave the same suffix `s[i:]` to split, with the same dictionary. Yes: the future doesn't care how the prefix was cut.

**Last decision.** The last word is `s[j:i]` for some `j < i`, and it must be in the dictionary. Removing it leaves a complete split of `s[:j]`.

The same state answers three different questions. Only the combining rule changes:

| Question | Table | Recurrence | Base |
|---|---|---|---|
| Can it be split? | `can[i]` | `can[i] = OR of can[j]` over valid last words | `can[0] = True` |
| In how many ways? | `count[i]` | `count[i] = SUM of count[j]` | `count[0] = 1` |
| Fewest words? | `fewest[i]` | `fewest[i] = 1 + MIN of fewest[j]` | `fewest[0] = 0` |

**Trace** (positions that can be reached):

| i | Prefix | Valid last words `s[j:i]` | `count[i]` | `fewest[i]` |
|---:|---|---|---:|---:|
| 0 | empty | — | 1 | 0 |
| 3 | `cat` | `cat` (j = 0) | 1 | 1 |
| 4 | `cats` | `cats` (j = 0) | 1 | 1 |
| 7 | `catsand` | `sand` (j = 3), `and` (j = 4) | 2 | 2 |
| 10 | `catsanddog` | `dog` (j = 7) | 2 | 3 |

Every other position is unreachable: `count` is 0 and `fewest` is `inf`.

**What if the state isn't enough?** Change the rules and see the history test fail:

- *Each dictionary word may be used at most once.* Two splits of `s[:i]` may have used different words, which changes which words are still allowed. Position alone fails; the state needs the set of used words.
- *Use exactly `k` words.* Position alone doesn't know how many words were used. Add the count: `possible[i][used]`.

## 3. Rebuilding the answer: parent pointers

The table tells you that 3 words suffice, but not which 3. To recover them, store **how** each state got its value. Whenever `fewest[i]` improves, record the position `j` where the last word started: `previous[i] = j`. Then walk backward from the end:

```text
previous[10] = 7  → last word s[7:10] = "dog"
previous[7]  = 3  → word s[3:7] = "sand"      (or 4, "and", if found first)
previous[3]  = 0  → word s[0:3] = "cat"
```

Reverse the list: `cat sand dog`.

```python
from math import inf
from itertools import combinations
from random import Random


def fewest_words(s: str, dictionary: set[str]) -> list[str] | None:
    """A split of s into the fewest dictionary words, or None if impossible."""
    if "" in dictionary:
        raise ValueError("dictionary words must be nonempty")
    words = sorted(dictionary)  # a fixed order makes ties reproducible
    n = len(s)
    fewest = [inf] * (n + 1)
    previous = [None] * (n + 1)
    fewest[0] = 0
    for start in range(n):
        if fewest[start] == inf:
            continue  # unreachable: nothing to push forward
        for word in words:
            end = start + len(word)
            if end <= n and s.startswith(word, start) and fewest[start] + 1 < fewest[end]:
                fewest[end] = fewest[start] + 1
                previous[end] = start
    if fewest[n] == inf:
        return None
    result, end = [], n
    while end > 0:
        start = previous[end]
        result.append(s[start:end])
        end = start
    return result[::-1]


def count_splits(s: str, dictionary: set[str]) -> int:
    n = len(s)
    count = [0] * (n + 1)
    count[0] = 1
    for i in range(1, n + 1):
        for j in range(i):
            if s[j:i] in dictionary:
                count[i] += count[j]
    return count[n]


def all_splits_brute(s: str, dictionary: set[str]) -> list[list[str]]:
    n = len(s)
    splits = []
    for size in range(n):
        for cuts in combinations(range(1, n), size):
            bounds = (0, *cuts, n)
            pieces = [s[a:b] for a, b in zip(bounds, bounds[1:])]
            if all(p in dictionary for p in pieces):
                splits.append(pieces)
    return splits if n else [[]]


def main():
    dictionary = {"cat", "cats", "and", "sand", "dog"}
    answer = fewest_words("catsanddog", dictionary)
    assert answer is not None and len(answer) == 3 and "".join(answer) == "catsanddog"
    assert count_splits("catsanddog", dictionary) == 2
    assert fewest_words("catsandog", dictionary) is None
    assert fewest_words("", dictionary) == []
    assert fewest_words("aaaa", {"a", "aa", "aaaa"}) == ["aaaa"]

    rng = Random(6)
    for _ in range(300):
        dictionary = {"".join(rng.choice("ab") for _ in range(rng.randrange(1, 4)))
                      for _ in range(rng.randrange(1, 5))}
        s = "".join(rng.choice("ab") for _ in range(rng.randrange(0, 9)))
        splits = all_splits_brute(s, dictionary)
        assert count_splits(s, dictionary) == len(splits)
        answer = fewest_words(s, dictionary)
        if splits:
            assert answer is not None and "".join(answer) == s
            assert all(w in dictionary for w in answer)
            assert len(answer) == min(len(p) for p in splits)
        else:
            assert answer is None


if __name__ == "__main__":
    main()
```

Let `n = len(s)`, `d` the number of words and `L` the longest word. There are at most `n·d` word checks of cost O(L) each, so the time is O(n·d·L), and the tables take O(n) space.

**Why one pointer per state is enough.** The question asks for *one* optimal split. A state's best value came from some predecessor; the pointer records one such predecessor. Following pointers back always gives a valid split with exactly the optimal number of words, because each step back removes one word and lands on a state whose own best value is one less.

Other rebuilding questions need more:

| You want… | Store per state |
|---|---|
| One optimal solution | One predecessor, updated only on a strict improvement |
| The number of optimal solutions | The best value and the number of ways achieving it; add counts on ties |
| All optimal solutions | Every tied predecessor. The output itself can be exponentially large |
| A solution after shrinking memory to one row | Not available from the row alone. Keep the full table, or a separate record of decisions |

## 4. Top-down or bottom-up, and why DFS + memo is DP

A common way to write word break is a depth-first search: `dfs(start)` tries every word that matches at `start` and recurses on `start + len(word)`; it returns `True` when `start` reaches the end.

Without a cache this is **backtracking**, and it can be exponential. With `s = "aaaaaaaaaaaaaaaaaaab"` (19 `a`s and a `b`) and words `{a, aa, aaa}`, no split exists, so the search must try every way to cut the `a`s into pieces of length 1, 2 and 3 before giving up. That is over 100,000 calls. Yet there are only 21 different arguments, `start = 0 … 20`. The same overlap as climbing stairs: `dfs(5)` is reached after `a a a a a`, after `aa aaa`, after `aaa aa`, and so on.

Add a cache keyed by `start` and each position is solved once. That makes it DP, and every part of the DP is already in the search:

| DP part | In the DFS |
|---|---|
| **State** | `dfs(start)`: "can the suffix `s[start:]` be split into words?" |
| **Transition** | The loop over words: the **first** word of the suffix, instead of the last word of the prefix |
| **Base case** | `start == len(s)`: the empty suffix splits in one way |
| **Evaluation order** | Whatever order the recursion reaches positions. It is safe because every call goes to a larger `start` (words are nonempty), so there is no cycle |
| **Answer** | `dfs(0)` |

It passes the history test for the same reason as the prefix version: how you reached `start` doesn't change how `s[start:]` can be split. So DFS + memo **is** top-down DP over suffix states. The bottom-up table over prefix states is the same idea with the arrows reversed.

```python
from random import Random


def can_split_dfs(s: str, dictionary: set[str], memo: bool) -> tuple[bool, int]:
    """DFS over start positions. Returns (answer, number of positions solved)."""
    if "" in dictionary:
        raise ValueError("dictionary words must be nonempty")  # "" would be a cycle.
    words = sorted(dictionary)
    known: dict[int, bool] = {}
    solved = 0

    def dfs(start: int) -> bool:
        nonlocal solved
        if memo and start in known:
            return known[start]
        solved += 1
        if start == len(s):
            result = True
        else:
            # any() stops at the first word that leads to a full split.
            result = any(s.startswith(w, start) and dfs(start + len(w)) for w in words)
        known[start] = result
        return result

    return dfs(0), solved


def can_split_bottom_up(s: str, dictionary: set[str]) -> tuple[bool, int]:
    """Pull over prefixes: computes every position, reachable or not."""
    n = len(s)
    can = [False] * (n + 1)
    can[0] = True
    for i in range(1, n + 1):
        can[i] = any(can[j] and s[j:i] in dictionary for j in range(i))
    return can[n], n + 1


def main():
    words = {"a", "aa", "aaa"}
    hard = "a" * 19 + "b"
    found, plain_calls = can_split_dfs(hard, words, memo=False)
    assert not found and plain_calls > 100_000  # Backtracking: exponential.
    found, memo_calls = can_split_dfs(hard, words, memo=True)
    assert not found and memo_calls == 20  # Positions 0..19; 20 is never reached.

    found, solved = can_split_dfs("a" * 30, {"a", "aa"}, memo=True)
    assert found and solved == 31  # Straight down "a", "a", ... and stop.
    found, solved = can_split_dfs("b" + "a" * 30, {"a", "aa"}, memo=True)
    assert not found and solved == 1  # No word starts with "b": stop at once.
    assert can_split_bottom_up("b" + "a" * 30, {"a", "aa"}) == (False, 32)

    rng = Random(7)
    for _ in range(300):
        dictionary = {"".join(rng.choice("ab") for _ in range(rng.randrange(1, 4)))
                      for _ in range(rng.randrange(1, 4))}
        s = "".join(rng.choice("ab") for _ in range(rng.randrange(0, 12)))
        expected = can_split_dfs(s, dictionary, memo=False)[0]  # Brute force.
        assert can_split_dfs(s, dictionary, memo=True)[0] == expected
        assert can_split_bottom_up(s, dictionary)[0] == expected


if __name__ == "__main__":
    main()
```

So which style should you use? They compute the same states with the same recurrence, and the differences are practical:

- **Top-down solves only states reachable from the start.** On `"b" + "a" * 30` it stops after one position, while the bottom-up pull loop computes all 32. The bottom-up *push* loop in §3 also skips unreachable positions with its `continue`, so this is as much about pull vs push ([Designing a Recurrence §6](02-designing-a-recurrence.md#6-pull-and-push-two-ways-to-fill-the-table)) as about top-down vs bottom-up.
- **Top-down can stop early** on a yes/no question: `any(...)` returns at the first word that leads to a full split. Counting and minimizing must look at every split, so for them top-down saves only the unreachable states.
- **The worst case is the same.** If every position is reachable and nothing stops early, both do O(n·d·L) work, and top-down adds function-call overhead.
- **Depth.** The recursion can go `n` levels deep. Python stops at about 1000 by default, so long inputs need the loop.

A good default: write the recurrence top-down when that is the easiest way to get it right, then turn it into a loop when depth or speed matters.

## 5. State machines: stock trading

Some problems have a small set of **modes**, and each step moves between them. Give each mode its own table. The mode is exactly the "missing fact" from §1.

**Problem.** `prices[d]` is a stock's price on day `d`. You may buy and sell many times, holding at most one share at a time, but after selling you must wait one day (a **cooldown**) before buying again. Maximize profit.

For `prices = [1, 2, 3, 0, 2]`: buy at 1, sell at 2, cool down, buy at 0, sell at 2. Profit 3.

**Modes at the end of a day:**

```text
            buy                 sell
   free ───────────► hold ───────────► sold
   ▲  │              ▲  │                │
   └──┘ stay free    └──┘ keep holding   │
   ▲                                     │
   └──────── the cooldown day passes ────┘
```

- `hold[d]`: the best profit at the end of day `d` while **holding** a share.
- `sold[d]`: the best profit at the end of day `d` having **sold today**. Tomorrow is a cooldown.
- `free[d]`: the best profit at the end of day `d`, **not holding, and allowed to buy tomorrow**.

**Transitions** (one per arrow):

$$
\begin{aligned}
hold[d] &= \max(hold[d-1],\ free[d-1]-prices[d]) &&\text{keep holding, or buy today}\\
sold[d] &= hold[d-1]+prices[d] &&\text{sell today}\\
free[d] &= \max(free[d-1],\ sold[d-1]) &&\text{stay free, or finish a cooldown}
\end{aligned}
$$

**Base (before day 0).** `free = 0`, `hold = -inf` (you can't hold a share you never bought), `sold = -inf`.

**Answer.** `max(sold[last], free[last])`. Ending while holding is never better than not having bought.

| Day | Price | `hold` | `sold` | `free` |
|---:|---:|---:|---:|---:|
| start | — | −inf | −inf | 0 |
| 0 | 1 | −1 | −inf | 0 |
| 1 | 2 | −1 | 1 | 0 |
| 2 | 3 | −1 | 2 | 1 |
| 3 | 0 | 1 | −1 | 2 |
| 4 | 2 | 1 | **3** | 2 |

The same picture, with different arrows, solves the whole stock family:

| Variant | Modes | Change |
|---|---|---|
| One transaction only | hold, free | Buying uses profit 0, not the previous free value |
| Unlimited transactions | hold, free | Drop the cooldown mode |
| Transaction fee | hold, free | Subtract the fee when selling |
| At most `k` transactions | hold and free **per number of transactions used** | Add a count to the state: `hold[t]`, `free[t]` |

```python
from itertools import product
from math import inf
from random import Random


def max_profit_cooldown(prices: list[int]) -> int:
    hold, sold, free = -inf, -inf, 0
    for p in prices:
        hold, sold, free = max(hold, free - p), hold + p, max(free, sold)
    return max(sold, free)


def max_profit_k_transactions(prices: list[int], k: int) -> int:
    """At most k buy-sell pairs, at most one share held at a time."""
    if k < 0:
        raise ValueError("k must be nonnegative")
    hold = [-inf] * (k + 1)  # hold[t]: holding, t buys made so far
    free = [0] + [-inf] * k  # free[t]: not holding, t completed transactions
    for p in prices:
        for t in range(k, 0, -1):  # read yesterday's free[t-1]: go downward
            free[t] = max(free[t], hold[t] + p)
            hold[t] = max(hold[t], free[t - 1] - p)
    return max(free)


def brute(prices: list[int], cooldown: bool, k: int | None) -> int:
    """Try every action sequence: 0 = wait, 1 = buy, 2 = sell."""
    best = 0
    for actions in product((0, 1, 2), repeat=len(prices)):
        holding, profit, buys, blocked_until, ok = False, 0, 0, -1, True
        for day, (a, p) in enumerate(zip(actions, prices)):
            if a == 1:
                if holding or day <= blocked_until:
                    ok = False
                    break
                holding, profit, buys = True, profit - p, buys + 1
            elif a == 2:
                if not holding:
                    ok = False
                    break
                holding, profit = False, profit + p
                if cooldown:
                    blocked_until = day + 1
        if ok and not holding and (k is None or buys <= k):
            best = max(best, profit)
    return best


def main():
    assert max_profit_cooldown([1, 2, 3, 0, 2]) == 3
    assert max_profit_cooldown([]) == 0
    assert max_profit_k_transactions([3, 2, 6, 5, 0, 3], 2) == 7
    assert max_profit_k_transactions([1, 5], 0) == 0
    rng = Random(8)
    for _ in range(150):
        prices = [rng.randrange(0, 8) for _ in range(rng.randrange(0, 8))]
        assert max_profit_cooldown(prices) == brute(prices, cooldown=True, k=None)
        k = rng.randrange(0, 4)
        assert max_profit_k_transactions(prices, k) == brute(prices, cooldown=False, k=k)


if __name__ == "__main__":
    main()
```

The tuple assignment `hold, sold, free = ...` computes all three right-hand sides from **yesterday's** values before overwriting any of them. Writing three separate lines would let `sold` read today's `hold`, which corresponds to buying and selling on the same day. The `k`-transaction loop gets the same protection by updating `t` downward, so `free[t − 1]` is still yesterday's value when `hold[t]` reads it. The same "which version of the value am I reading?" question returns in [Knapsack and Coins](04-knapsack-and-coins.md).

## 6. DP is a path problem

Draw each state as a dot and each transition as an arrow from the states it reads to the state it computes. For word break the dots are positions `0 … n`, with an arrow `j → i` whenever `s[j:i]` is a word:

```text
 0 ──cat──► 3 ──sand──► 7 ──dog──► 10
 └──cats──► 4 ──and───┘
```

Then:

| DP question | Graph question |
|---|---|
| Can it be done? | Is there a path from the start to the goal? |
| How many ways? | How many paths are there? |
| Fewest words / minimum cost | Shortest path (each arrow has a length) |
| Maximum value | Longest path |
| Evaluation order | An order where every arrow points forward (a **topological order**) |

This view explains the rules of earlier chapters:

- **Why order matters.** A state is final only after every arrow into it has been processed.
- **Why the arrows must not form a cycle.** If `dp[a]` depends on `dp[b]` and `dp[b]` on `dp[a]`, there is no first one to compute. Memoization loops forever (or hits the recursion limit). Problems with cycles need graph algorithms such as BFS or Dijkstra, covered in [Graphs](../10-graphs/README.md), or an extra state dimension (like a step counter) that makes every arrow go forward.
- **Why DP is efficient.** The graph has one dot per state, and the work is proportional to the number of arrows. Brute force walks every *path*, and there can be exponentially many.

[Tree and DAG DP](08-tree-and-dag-dp.md) runs DP directly on a given graph.

## 7. Summary

**What to add to the state** when it fails the history test:

| The future depends on… | Add to the state | Example |
|---|---|---|
| Whether the previous item was taken | A yes/no flag | House robber (§1), stock trading (§5) |
| How many items were used so far | A count | "Exactly `k` words" (§2) |
| Which items were used | The set, as a bitmask | [Bitmask DP](09-bitmask-dp.md) |
| How much capacity is left | The capacity | [Knapsack and Coins](04-knapsack-and-coins.md) |
| Whether the number built so far still equals a bound | A "tight" flag | [Digit DP](10-digit-dp.md) |

## 8. Pitfalls and practice

1. A state that fails the history test: two partial solutions share it but have different futures.
2. A state that remembers the whole history, so nothing ever merges.
3. Rebuilding from a memory-reduced table whose cells were overwritten.
4. Updating several modes in sequence when each should read yesterday's values.
5. A recurrence with a cycle. Memoization can't fix it.
6. Assuming top-down is always faster. It skips unreachable states and can stop early, but the worst case is the same.

Practice: word break; word break II (return every split, and note the output can be exponential); best time to buy and sell stock I, II, III, IV, with cooldown, and with a fee; paint house (the color of the previous house is the mode); domino and tromino tiling (the shape of the unfinished edge is the mode).

Exercises on the model:

1. Require exactly `k` words in word break. Define `possible[i][used]`, its base case, and its loop order.
2. Give each dictionary word a cost, possibly negative. Explain why the forward loop still works when every word is nonempty.
3. Return the lexicographically smallest optimal split. Explain why sorting the dictionary alone does not guarantee it.

Next: [Knapsack and Coins](04-knapsack-and-coins.md).
