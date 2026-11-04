# Stacks and Queues — Last In First Out, First In First Out

## 1. Do the brackets match?

A string of brackets such as `"([]{})"` is **valid** when every opening bracket is closed by the same kind of bracket, in the right order.

| String | Valid? | Why |
|---|---|---|
| `"([]{})"` | yes | `[]` and `{}` sit inside `()` |
| `"([)]"` | no | `[` is still open when `)` arrives |
| `"(("` | no | two brackets are never closed |
| `"())"` | no | the last `)` has nothing to close |
| `""` | yes | nothing is open, nothing is wrong |

**Brute force.** Every valid nonempty string contains an adjacent pair `()`, `[]` or `{}` (its innermost pair), and deleting that pair keeps validity unchanged. So delete adjacent pairs until none are left and check that the string became empty. On `"((((…))))"` that takes `n / 2` rounds of `O(n)` work each: `O(n²)`.

**The key observation.** After reading `(` and `[`, the next closer must close `[`, the **most recently opened** bracket; closing `(` first would cross the pairs, as in `"([)]"`. So a closer is only ever compared with the newest unclosed opener, and the list of open brackets only changes at its newest end.

A container that is changed at one end only, the **top**, is a **stack**. **Push** puts an item on top, **pop** removes and returns the top item, **peek** reads it. The last item pushed is the first popped: **LIFO**, last in first out. In Python a `list` is a stack whose end is the top:

| Operation | Python | Cost |
|---|---|---|
| push `x` | `stack.append(x)` | `O(1)` amortized (§6) |
| pop | `stack.pop()` | `O(1)` |
| peek | `stack[-1]` | `O(1)` |
| empty? | `not stack` | `O(1)` |

`stack.pop()` and `stack[-1]` raise `IndexError` on an empty list, so test `if stack` first.

**Invariant.** The stack holds the opening brackets that are still unclosed, oldest at the bottom.

| Step | Char | Action | Stack after (bottom → top) |
|---:|---|---|---|
| 1 | `(` | push | `(` |
| 2 | `[` | push | `( [` |
| 3 | `]` | top `[` matches: pop | `(` |
| 4 | `{` | push | `( {` |
| 5 | `}` | top `{` matches: pop | `(` |
| 6 | `)` | top `(` matches: pop | empty |

On `"([)]"`, step 3 meets `)` with `[` on top and stops. There are exactly three ways to fail: a closer meets the wrong opener (`"([)]"`), a closer meets an empty stack (`"())"`), or openers remain at the end (`"(("`).

```python
import random

CLOSER_TO_OPENER = {")": "(", "]": "[", "}": "{"}


def is_valid(s: str) -> bool:
    """True when every bracket in s is closed by its partner, in order."""
    stack: list[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in CLOSER_TO_OPENER:
            if not stack or stack[-1] != CLOSER_TO_OPENER[ch]:
                return False
            stack.pop()
        else:
            raise ValueError(f"unexpected character {ch!r}")
    return not stack


def is_valid_brute(s: str) -> bool:
    """Delete adjacent matched pairs until nothing changes."""
    previous = None
    while s != previous:
        previous = s
        s = s.replace("()", "").replace("[]", "").replace("{}", "")
    return s == ""


def random_valid(rng: random.Random, pairs: int) -> str:
    """Build a valid string by wrapping or concatenating smaller ones."""
    if pairs == 0:
        return ""
    inside = rng.randrange(pairs)
    opener, closer = rng.choice(["()", "[]", "{}"])
    return (opener + random_valid(rng, inside) + closer
            + random_valid(rng, pairs - 1 - inside))


def main():
    assert is_valid("([]{})") and is_valid("()") and is_valid("")
    assert not is_valid("([)]")
    assert not is_valid("((")
    assert not is_valid("())")
    try:
        is_valid("(a)")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(1)
    for _ in range(3000):
        s = "".join(rng.choice("()[]{}") for _ in range(rng.randrange(9)))
        assert is_valid(s) == is_valid_brute(s), s
    for _ in range(500):
        s = random_valid(rng, rng.randrange(8))
        assert is_valid(s) and is_valid_brute(s), s


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`, each character is pushed and popped at most once. **Space:** `O(n)`.

**Why it's correct.** If the scan never fails, each closer was paired with the newest unclosed opener of its kind, which pairs the whole string without crossings, and the empty final stack means nothing is left open. If it fails, it found a closer whose only legal partner (the newest unclosed opener) is missing or of the wrong kind, or an opener with no closer; no pairing can fix either.

## 2. Variant: a stack that knows its minimum

**Problem.** Support `push`, `pop`, `top` and `get_min` (the smallest value on the stack), each in `O(1)`.

**Why one variable is not enough.** Keep `smallest` updated on push. Push `5`, then `1`: `smallest = 1`. Pop the `1`. The minimum is now `5`, but the variable has forgotten it.

**The key observation.** While an item `x` sits on the stack, the items below it never change, because a stack only changes at the top. So "the minimum of `x` and everything below it" is fixed from the moment `x` is pushed until it is popped. Compute it once, at push time, and store it next to `x`.

**Invariant.** Each entry is a pair `(value, smallest)`, where `smallest` is the minimum of that entry and every entry below it.

| Operation | Stack after, as `(value, smallest)` | `get_min()` |
|---|---|---:|
| push 5 | `(5,5)` | 5 |
| push 3 | `(5,5) (3,3)` | 3 |
| push 7 | `(5,5) (3,3) (7,3)` | 3 |
| push 3 | `(5,5) (3,3) (7,3) (3,3)` | 3 |
| push 1 | `(5,5) (3,3) (7,3) (3,3) (1,1)` | 1 |
| pop → 1 | `(5,5) (3,3) (7,3) (3,3)` | 3 |
| pop → 3 | `(5,5) (3,3) (7,3)` | 3 |
| pop → 7 | `(5,5) (3,3)` | 3 |
| pop → 3 | `(5,5)` | 5 |

```python
import random


class MinStack:
    """A stack with O(1) push, pop, top and get_min."""

    def __init__(self):
        self._items: list[tuple[int, int]] = []   # (value, min of this and below)

    def push(self, value: int) -> None:
        smallest = min(value, self._items[-1][1]) if self._items else value
        self._items.append((value, smallest))

    def pop(self) -> int:
        if not self._items:
            raise IndexError("pop from empty MinStack")
        return self._items.pop()[0]

    def top(self) -> int:
        if not self._items:
            raise IndexError("top of empty MinStack")
        return self._items[-1][0]

    def get_min(self) -> int:
        if not self._items:
            raise IndexError("get_min of empty MinStack")
        return self._items[-1][1]

    def __len__(self) -> int:
        return len(self._items)


def main():
    s = MinStack()
    for value, expected in [(5, 5), (3, 3), (7, 3), (3, 3), (1, 1)]:
        s.push(value)
        assert s.get_min() == expected
    for popped, expected in [(1, 3), (3, 3), (7, 3), (3, 5)]:
        assert s.pop() == popped
        assert s.get_min() == expected

    rng = random.Random(3)
    for _ in range(300):
        fast, plain = MinStack(), []
        for _ in range(60):
            if plain and rng.random() < 0.4:
                assert fast.pop() == plain.pop()
            else:
                value = rng.randrange(-5, 6)   # small range forces duplicates
                fast.push(value)
                plain.append(value)
            if plain:
                assert fast.top() == plain[-1]
                assert fast.get_min() == min(plain)
            assert len(fast) == len(plain)


if __name__ == "__main__":
    main()
```

Every operation is `O(1)`; space is `O(n)` for `n` items.

**The tie trap in the space-saving version.** A common variant keeps a second stack of minimums only: push `x` onto it when `x <= ` its top, pop it when the popped value equals its top. The test must be `<=`. With `<`, pushing `3, 3` records `3` once; popping one `3` removes the record, and the stack `[3]` reports the wrong minimum.

## 3. Variant: decode string, a stack of unfinished contexts

**Problem.** `k[text]` means `text` repeated `k` times, and groups nest.

| Encoded | Decoded |
|---|---|
| `"3[a]2[bc]"` | `"aaabcbc"` |
| `"3[a2[c]]"` | `"accaccacc"` |
| `"10[x]"` | `"xxxxxxxxxx"` |

**The key observation.** This is §1 with work attached to each bracket. At `[` the scan starts a new inner piece of text, but it must remember the outer text built so far and the repeat count. At `]` the most recently opened group closes. So push the outer context at `[` and pop it at `]`.

**State.** `current` is the text of the innermost open group so far; `number` is the repeat count being read (it may have several digits, as in `10`); the stack holds `(text before this group, repeat count)` for each open group.

| Char | Action | Stack after | `current` | `number` |
|---|---|---|---|---:|
| `3` | read digit | — | `""` | 3 |
| `[` | push `("", 3)`, reset | `("",3)` | `""` | 0 |
| `a` | append | `("",3)` | `"a"` | 0 |
| `2` | read digit | `("",3)` | `"a"` | 2 |
| `[` | push `("a", 2)`, reset | `("",3) ("a",2)` | `""` | 0 |
| `c` | append | `("",3) ("a",2)` | `"c"` | 0 |
| `]` | pop `("a", 2)`: `"a" + "c" * 2` | `("",3)` | `"acc"` | 0 |
| `]` | pop `("", 3)`: `"" + "acc" * 3` | — | `"accaccacc"` | 0 |

```python
import random
import re


def decode_string(s: str) -> str:
    stack: list[tuple[str, int]] = []
    current, number = "", 0
    for ch in s:
        if ch.isdigit():
            number = number * 10 + int(ch)
        elif ch == "[":
            stack.append((current, number))
            current, number = "", 0
        elif ch == "]":
            if not stack:
                raise ValueError("']' without '['")
            before, repeat = stack.pop()
            current = before + current * repeat
        elif ch.isalpha():
            current += ch
        else:
            raise ValueError(f"unexpected character {ch!r}")
    if stack:
        raise ValueError("'[' without ']'")
    return current


GROUP = re.compile(r"(\d+)\[([a-z]*)\]")


def decode_brute(s: str) -> str:
    """Expand innermost groups until none are left."""
    while "[" in s:
        s = GROUP.sub(lambda m: m.group(2) * int(m.group(1)), s)
    return s


def random_encoded(rng: random.Random, depth: int) -> str:
    parts = []
    for _ in range(rng.randrange(1, 4)):
        if depth > 0 and rng.random() < 0.5:
            parts.append(f"{rng.randrange(1, 12)}[{random_encoded(rng, depth - 1)}]")
        else:
            parts.append("".join(rng.choice("abc") for _ in range(rng.randrange(3))))
    return "".join(parts)


def main():
    assert decode_string("3[a]2[bc]") == "aaabcbc"
    assert decode_string("3[a2[c]]") == "accaccacc"
    assert decode_string("2[abc]3[cd]ef") == "abcabccdcdcdef"
    assert decode_string("10[x]") == "x" * 10
    assert decode_string("") == ""
    for bad in ("2[a", "a]", "2[a]]"):
        try:
            decode_string(bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = random.Random(7)
    for _ in range(1000):
        s = random_encoded(rng, 3)
        assert decode_string(s) == decode_brute(s), s


if __name__ == "__main__":
    main()
```

The stack holds one entry per nesting level. Time is dominated by building the output: `O(n + m · d)` for input length `n`, output length `m` and nesting depth `d`, because an inner piece is copied again at each enclosing level.

A recursive decoder that calls itself at `[` and returns at `]` does the same thing: Python's **call stack** holds the unfinished outer calls. The explicit stack has no recursion-depth limit.

## 4. Queues and deques

A **queue** serves items in arrival order: add at the **back** (enqueue), remove from the **front** (dequeue). First in, first out: **FIFO**.

A Python `list` is a poor queue: `list.pop(0)` shifts every remaining element one slot left, `O(n)` per removal, so `n` dequeues cost `O(n²)`. Use `collections.deque` instead. A **deque** ("deck", short for double-ended queue) adds and removes at **both** ends in `O(1)`, so it is a stack and a queue at once:

| Operation | `list` | `collections.deque` |
|---|---|---|
| add / remove at the back | `append(x)`, `pop()`: `O(1)` | `append(x)`, `pop()`: `O(1)` |
| add at the front | `insert(0, x)`: `O(n)` | `appendleft(x)`: `O(1)` |
| remove from the front | `pop(0)`: `O(n)` | `popleft()`: `O(1)` |
| read either end | `a[0]`, `a[-1]`: `O(1)` | `d[0]`, `d[-1]`: `O(1)` |
| read the middle | `a[i]`: `O(1)` | `d[i]`: `O(n)` worst case |

Use a `list` when only one end changes; use a `deque` when items leave from the front, or from both ends as in [Monotonic Deque](04-monotonic-deque.md).

## 5. A queue built from two stacks

**Problem.** Build a FIFO queue whose only storage is two stacks (lists used with `append` and `pop()` only).

**The key observation.** Pouring one stack into another, one pop and push at a time, **reverses** it. The oldest arrival is at the bottom of a stack of arrivals; after pouring, it is on top.

- `inbox`: every push goes here.
- `outbox`: every pop comes from here. Only when it is empty, pour the whole `inbox` into it.

**Invariant.** `outbox` read top to bottom, then `inbox` read bottom to top, lists the queue from front to back.

| Operation | `inbox` (bottom → top) | `outbox` (bottom → top) | Returns |
|---|---|---|---|
| push 1, 2, 3 | `1 2 3` | — | |
| pop | — | pour → `3 2 1`, then `3 2` | 1 |
| push 4 | `4` | `3 2` | |
| pop | `4` | `3` | 2 |
| pop | `4` | — | 3 |
| pop | — | pour → `4`, then empty | 4 |

The third `pop` did not pour although `inbox` held `4`: the `outbox` still had `3`, which is older. Pouring into a nonempty `outbox` would put `4` on top of `3` and serve it first.

```python
import random
from collections import deque


class TwoStackQueue:
    def __init__(self):
        self._inbox: list[int] = []
        self._outbox: list[int] = []
        self.moves = 0      # items ever poured, for the amortized test

    def push(self, value: int) -> None:
        self._inbox.append(value)

    def _refill(self) -> None:
        if not self._outbox:
            while self._inbox:
                self._outbox.append(self._inbox.pop())
                self.moves += 1
        if not self._outbox:
            raise IndexError("queue is empty")

    def pop(self) -> int:
        self._refill()
        return self._outbox.pop()

    def peek(self) -> int:
        self._refill()
        return self._outbox[-1]

    def __len__(self) -> int:
        return len(self._inbox) + len(self._outbox)


def main():
    q = TwoStackQueue()
    for x in (1, 2, 3):
        q.push(x)
    assert q.pop() == 1
    q.push(4)
    assert [q.pop(), q.pop(), q.pop()] == [2, 3, 4]
    try:
        q.pop()
        raise AssertionError("expected IndexError")
    except IndexError:
        pass

    rng = random.Random(5)
    for _ in range(300):
        q, reference, pushes = TwoStackQueue(), deque(), 0
        for step in range(80):
            if reference and rng.random() < 0.45:
                if rng.random() < 0.5:
                    assert q.peek() == reference[0]
                assert q.pop() == reference.popleft()
            else:
                q.push(step)
                reference.append(step)
                pushes += 1
            assert len(q) == len(reference)
        assert q.moves <= pushes          # each item is poured at most once


if __name__ == "__main__":
    main()
```

## 6. Amortized cost: count per item, not per call

One `pop` of the two-stack queue can pour `n` items, so a single call is `O(n)`. Concluding that `m` operations cost `O(mn)` is true but far too pessimistic.

Count per **item** instead. Each item is pushed onto `inbox` once, moved to `outbox` at most once (nothing moves back), and popped from `outbox` once: at most four stack operations in its whole life, however the calls interleave. So any sequence of `m` operations does `O(m)` work in total, which is `O(1)` **amortized** per operation: an average over the worst-case sequence, with no randomness involved. The test above checks it directly with `q.moves <= pushes`. The same argument is why `list.append` is `O(1)` amortized: a rare append copies the list into a bigger block, but the copies over `m` appends add up to `O(m)`.

This is the idea the rest of the folder runs on. A monotonic stack has a `while` loop inside a `for` loop, which looks quadratic; it is linear because every index is pushed once and popped at most once.

## 7. Choosing the container

| The next item to process is… | Container | Python | Examples |
|---|---|---|---|
| the most recent unfinished one | stack (LIFO) | `list` | brackets, min stack, decode string, reverse Polish notation |
| the oldest waiting one | queue (FIFO) | `collections.deque` | two-stack queue, breadth-first search |
| sometimes the newest, sometimes the oldest | deque | `collections.deque` | sliding-window maximum ([Monotonic Deque](04-monotonic-deque.md)) |

**Nesting** (something opened later must close earlier) suggests a stack. **Arrival order** (serve in the order things came) suggests a queue.

## 8. Pitfalls and practice

1. **Reading `[-1]` or calling `pop()` on an empty list.** Test `if stack` first and decide what empty means for the answer.
2. **Skipping the final check.** A bracket scan that never fails still needs an empty stack at the end.
3. **`list.pop(0)` as a queue.** `O(n)` per call; use `deque.popleft()`.
4. **Operands in the wrong order.** In reverse Polish notation (`4 13 5 / +` means `4 + 13 / 5`), the operator applies to the top two values, and the first one popped is the **right** operand.
5. **`<` instead of `<=` in a minimums-only stack.** Equal values each need their own record (§2).
6. **Multi-digit numbers read one digit at a time.** Accumulate `number = number * 10 + digit`.
7. **Pouring into a nonempty `outbox`.** It serves a new item before an old one (§5).
8. **Calling a nested loop quadratic without counting per item.** Amortized counting (§6) often shows it is linear.

Practice: valid parentheses; min stack; evaluate reverse Polish notation; implement queue using stacks; implement stack using queues; decode string; baseball game; backspace string compare; simplify path; asteroid collision; minimum remove to make valid parentheses; longest valid parentheses.

Next: [Monotonic Stack](02-monotonic-stack.md).
