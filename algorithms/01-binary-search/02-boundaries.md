# Boundaries — Lower Bound, Upper Bound, and the First True

## 1. The first copy of `x`

```text
index:  0  1  2  3  4  5
a    : [1, 2, 2, 2, 5, 7]
```

Return the index of the **first** 2 (answer: 1). The search from [The Idea of Binary Search](01-the-idea.md) checks `mid = 3` first, sees a 2, and returns 3. Scanning from the left finds 1, but costs O(n) per question.

**The key observation.** Stop asking "is `a[mid]` equal to `x`?" and ask "is `a[mid] ≥ x`?". Because the list is sorted, the answers form one block of "no" followed by one block of "yes":

```text
a    : [1, | 2, 2, 2, 5, 7]
        < 2 |  >= 2
            ^
       the cut, at index 1
```

The first copy of `x`, if there is one, sits right at that cut. The position of the cut is called the **lower bound** of `x`: the smallest index `i` with `a[i] ≥ x`, or `len(a)` if every element is smaller.

**The invariant.** We don't know where the cut is, but we keep two indexes that bracket it:

> Everything in `a[:lo]` is `< x`, and everything in `a[hi:]` is `≥ x`.

At the start, `lo = 0` and `hi = len(a)`, so both slices are empty and the sentence holds. Each step looks at `a[mid]`:

- `a[mid] < x`: `mid` and everything left of it is `< x`. Set `lo = mid + 1`.
- `a[mid] ≥ x`: `mid` and everything right of it is `≥ x`. Set `hi = mid`.

There is no "equal, return" branch. A copy of `x` is one more element `≥ x`, and an earlier copy may exist, so the search keeps going left. When `lo == hi`, the unknown region `a[lo:hi]` is empty and the cut is at `lo`.

**Trace** for `x = 2`:

| Step | `lo` | `hi` | `mid` | `a[mid]` | `a[mid] < 2`? | Action | Known `< 2` | Known `≥ 2` |
|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 0 | 6 | 3 | 2 | no | `hi = 3` | — | `a[3:]` |
| 2 | 0 | 3 | 1 | 2 | no | `hi = 1` | — | `a[1:]` |
| 3 | 0 | 1 | 0 | 1 | yes | `lo = 1` | `a[:1]` | `a[1:]` |
| 4 | 1 | 1 | — | — | — | stop: 1 | `a[:1]` | `a[1:]` |

Step 1 found a 2 at index 3; the invariant forced the search to keep looking left of it.

**Why it's correct.** The invariant holds at the start and each step keeps it, by sortedness. The range shrinks every step, because `lo ≤ mid < hi`. At the end `lo == hi`, so every element before `lo` is `< x` and every element from `lo` on is `≥ x`: `lo` is the cut.

### Variant: `x` is missing

For `x = 3` the cut still exists; it is where 3 would be inserted:

| Step | `lo` | `hi` | `mid` | `a[mid]` | `a[mid] < 3`? | Action |
|---:|---:|---:|---:|---:|---|---|
| 1 | 0 | 6 | 3 | 2 | yes | `lo = 4` |
| 2 | 4 | 6 | 5 | 7 | no | `hi = 5` |
| 3 | 4 | 5 | 4 | 5 | no | `hi = 4` |
| 4 | 4 | 4 | — | — | — | stop: 4 |

So the lower bound alone does not say whether `x` is present. Check `L < len(a) and a[L] == x`, in that order: `L` can be `len(a)`.

### Variant: `x` outside the values

| `x` | What happens | Lower bound |
|---:|---|---:|
| 0 | Every `a[mid] ≥ 0`, so only `hi` moves | 0 |
| 9 | Every `a[mid] < 9`, so only `lo` moves | 6 = `len(a)` |
| any, `a = []` | The loop never runs | 0 |

## 2. Variant: the last copy, with no `lo = mid`

The last 2 is at index 3. The tempting loop moves `lo = mid` whenever `a[mid] ≤ x`, and [chapter 1](01-the-idea.md#7-variant-change-one-line-and-it-breaks) showed that it can loop forever. The fix is to search for a *first* position instead:

> The last index with `a[i] ≤ x` is the first index with `a[i] > x`, minus 1.

The first index with `a[i] > x` is the **upper bound** of `x`. It is the lower-bound loop with one comparison changed: copies of `x` now go to the left part.

```text
a    : [1, 2, 2, 2, | 5, 7]
         <= 2       |  > 2
                    ^
               upper bound = 4, last 2 = 4 - 1 = 3
```

**Invariant:** everything in `a[:lo]` is `≤ x`, and everything in `a[hi:]` is `> x`.

**Trace.** On integers, `a[i] > 2` is the same test as `a[i] ≥ 3`, so `upper_bound(a, 2)` makes exactly the comparisons of the `x = 3` table above and stops at 4.

The question chapter 1 got stuck on, "the last index with `a[i] ≤ 4`", becomes `upper_bound(a, 4) − 1 = 4 − 1 = 3`.

## 3. Variant: counting and inserting

Write `L = lower_bound(a, x)` and `U = upper_bound(a, x)`. The copies of `x` occupy exactly `a[L:U]`:

```text
index:  0  1  2  3  4  5
a    : [1, 2, 2, 2, 5, 7]
           ^        ^
           L = 1    U = 4        a[L:U] = [2, 2, 2]
```

- **Count of `x`:** `U − L`. No presence check is needed: when `x` is absent, `L == U` and the count is 0.
- **Count of values in `[low, high]`:** `upper_bound(high) − lower_bound(low)`.
- **Insert position:** `L` puts a new `x` before the existing copies, `U` after them. Both keep the list sorted.

## 4. One search: the first true of a monotone predicate

Lower bound never used the values themselves, only one yes/no answer per index:

```text
index        :  0      1     2     3     4     5
a            :  1      2     2     2     5     7
a[i] >= 2 ?  :  False  True  True  True  True  True
```

A **predicate** is a function that returns `True` or `False`. A predicate over positions is **monotone** if, once it becomes `True`, it stays `True`: some `False`s, then some `True`s (either part may be empty). Lower bound finds the first `True` of "`a[i] ≥ x`"; upper bound, of "`a[i] > x`". So there is really one binary search:

> Given a monotone predicate `ok` on `[lo, hi)`, find the smallest `i` in `[lo, hi)` with `ok(i)`, or `hi` if there is none.

**Invariant:** every index `< lo` has `ok` false, and every index `≥ hi` has `ok` true (counting the original `hi` as true).

For the opposite pattern, `True … True, False … False`, the **last** `True` sits right before the first `False`: negate the predicate and subtract 1. That is the trick of §2 in general form.

The predicate need not look at an array. In *first bad version*, versions `1 … n` are good up to some point and bad from then on; "is version `v` bad?" is monotone in `v`, and the first bad version is its first `True`. Spotting a hidden `False … True` pattern is most of the skill, and [Search on the Answer](03-search-on-the-answer.md) is built on it.

## 5. Python's `bisect` module

The standard `bisect` module implements both bounds in C, so it is faster than a hand-written loop.

| Function | Same as |
|---|---|
| `bisect_left(a, x, lo=0, hi=len(a))` | lower bound |
| `bisect_right(a, x, lo=0, hi=len(a))`, alias `bisect` | upper bound |
| `insort_left(a, x)` | `a.insert(bisect_left(a, x), x)` |
| `insort_right(a, x)`, alias `insort` | `a.insert(bisect_right(a, x), x)` |

The details that cause bugs:

- **`lo` and `hi`** restrict the search to `a[lo:hi]` without copying. The result is still an index into the whole list.
- **`key=`** (Python 3.10+) is applied to each **element**, but **not** to `x`: pass `x` already in key form. `insort(a, item, key=f)` is the exception; it applies `f` to `item` itself, because it needs the whole item to insert it.
- **Only `<` is used**, so strings, tuples and dates work.
- **`insort` is O(n).** Finding the spot is O(log n), but `list.insert` shifts the elements after it.
- **Nothing checks that `a` is sorted.** An unsorted list gives a meaningless index, not an error.

Everything from §1–§5 in one script: the hand-written bounds, the answers built on them, `first_true`, and `bisect`, all checked against linear scans.

```python
import random
from bisect import bisect_left, bisect_right, insort


def lower_bound(a: list[int], x: int) -> int:
    """Smallest i with a[i] >= x, or len(a). Invariant: a[:lo] < x <= a[hi:]."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(a: list[int], x: int) -> int:
    """Smallest i with a[i] > x, or len(a). Invariant: a[:lo] <= x < a[hi:]."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def first_occurrence(a: list[int], x: int) -> int:
    i = lower_bound(a, x)
    return i if i < len(a) and a[i] == x else -1


def last_occurrence(a: list[int], x: int) -> int:
    i = upper_bound(a, x) - 1
    return i if i >= 0 and a[i] == x else -1


def count_between(a: list[int], low: int, high: int) -> int:
    """How many values v satisfy low <= v <= high."""
    return upper_bound(a, high) - lower_bound(a, low) if low <= high else 0


def first_true(lo: int, hi: int, ok) -> int:
    """Smallest i in [lo, hi) with ok(i), or hi. ok must be F..F T..T on [lo, hi)."""
    if lo > hi:
        raise ValueError("empty or reversed range")
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if ok(mid):
            hi = mid  # The first True is at mid or to its left.
        else:
            lo = mid + 1  # The first True is to the right of mid.
    return lo


def last_true(lo: int, hi: int, ok) -> int:
    """Largest i in [lo, hi) with ok(i), or lo - 1. ok must be T..T F..F."""
    return first_true(lo, hi, lambda i: not ok(i)) - 1


def main():
    a = [1, 2, 2, 2, 5, 7]
    assert [lower_bound(a, x) for x in range(9)] == [0, 0, 1, 4, 4, 4, 5, 5, 6]
    assert [upper_bound(a, x) for x in range(9)] == [0, 1, 4, 4, 4, 5, 5, 6, 6]
    assert first_occurrence(a, 2) == 1 and last_occurrence(a, 2) == 3
    assert first_occurrence(a, 3) == -1 and last_occurrence(a, 3) == -1
    assert upper_bound(a, 4) - 1 == 3  # Last index with a[i] <= 4.
    assert count_between(a, 2, 5) == 4
    assert last_true(0, 6, lambda i: a[i] < 1) == -1
    assert first_true(1, 101, lambda v: v >= 37) == 37  # First bad version.

    # bisect: lo/hi search a[2:5] but return indexes into a.
    assert bisect_left(a, 2, 2, 5) == 2 and bisect_left(a, 9, 2, 5) == 5
    # key= applies to elements only; x must already be a key.
    people = [("ann", 19), ("bob", 25), ("cy", 25), ("dee", 40)]  # Sorted by age.
    age = lambda p: p[1]
    assert bisect_left(people, 25, key=age) == 1
    assert bisect_right(people, 25, key=age) == 3
    try:
        bisect_left(people, ("zed", 25), key=age)  # Wrong: compares tuple < int.
        raise AssertionError("expected TypeError")
    except TypeError:
        pass
    insort(people, ("eve", 25), key=age)  # insort applies key to the item itself.
    assert people[3] == ("eve", 25)  # After the existing 25s.

    rng = random.Random(4)
    for _ in range(3000):
        a = sorted(rng.randint(-4, 4) for _ in range(rng.randint(0, 12)))
        n, x = len(a), rng.randint(-6, 6)
        lb = next((i for i, v in enumerate(a) if v >= x), n)
        ub = next((i for i, v in enumerate(a) if v > x), n)
        assert lower_bound(a, x) == bisect_left(a, x) == lb
        assert upper_bound(a, x) == bisect_right(a, x) == ub
        assert first_true(0, n, lambda i: a[i] >= x) == lb
        assert last_true(0, n, lambda i: a[i] <= x) == ub - 1
        hits = [i for i, v in enumerate(a) if v == x]
        assert first_occurrence(a, x) == (hits[0] if hits else -1)
        assert last_occurrence(a, x) == (hits[-1] if hits else -1)
        assert ub - lb == a.count(x)
        low, high = sorted((rng.randint(-6, 6), rng.randint(-6, 6)))
        assert count_between(a, low, high) == sum(low <= v <= high for v in a)


if __name__ == "__main__":
    main()
```

**Time:** O(log n) per query; `first_true` makes O(log(hi − lo)) calls to `ok`. **Space:** O(1).

## 6. Variant: records sorted by one field

### A time-based key–value store

**Problem.** Support `set(key, value, timestamp)` and `get(key, timestamp)`. `get` returns the value set for `key` at the **largest timestamp `≤` the given one**, or `""` if there is none. For each key, timestamps arrive in increasing order.

Example for key `"foo"`: `set("foo", "bar", 1)`, `set("foo", "baz", 4)`. Then `get("foo", 3)` is `"bar"`, `get("foo", 4)` is `"baz"`, and `get("foo", 0)` is `""`.

**Brute force.** Scan every entry for the key: O(entries) per `get`.

**Key observation.** Each key's list of `(timestamp, value)` pairs is sorted by timestamp for free. "The last entry with time `≤ t`" is the upper bound of `t`, minus 1 (§2), searched on the first field with `key=`.

**Trace** on `[(1, "bar"), (4, "baz")]`. For `get("foo", 3)`, the predicate "time > 3" is `F, T`; the upper bound is 1, so the answer is entry 0, `"bar"`. For `get("foo", 0)` it is `T, T`; the upper bound is 0, entry −1 means none, so `""`.

```python
import random
from bisect import bisect_right


class TimeMap:
    def __init__(self):
        self.history: dict[str, list[tuple[int, str]]] = {}

    def set(self, key: str, value: str, timestamp: int) -> None:
        entries = self.history.setdefault(key, [])
        if entries and timestamp <= entries[-1][0]:
            raise ValueError("timestamps for a key must increase")
        entries.append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        entries = self.history.get(key, [])
        i = bisect_right(entries, timestamp, key=lambda e: e[0]) - 1
        return entries[i][1] if i >= 0 else ""


def brute_get(log: list[tuple[str, str, int]], key: str, timestamp: int) -> str:
    best_time, best_value = None, ""
    for k, value, t in log:
        if k == key and t <= timestamp and (best_time is None or t > best_time):
            best_time, best_value = t, value
    return best_value


def main():
    store = TimeMap()
    store.set("foo", "bar", 1)
    store.set("foo", "baz", 4)
    assert store.get("foo", 3) == "bar"
    assert store.get("foo", 4) == "baz"
    assert store.get("foo", 5) == "baz"
    assert store.get("foo", 0) == ""
    assert store.get("nope", 9) == ""

    rng = random.Random(7)
    for _ in range(300):
        store, log = TimeMap(), []
        clock = {"a": 0, "b": 0}
        for _ in range(rng.randint(0, 20)):
            key = rng.choice("ab")
            clock[key] += rng.randint(1, 3)
            value = str(rng.randint(0, 99))
            store.set(key, value, clock[key])
            log.append((key, value, clock[key]))
        for _ in range(20):
            key, t = rng.choice("abc"), rng.randint(0, 50)
            assert store.get(key, t) == brute_get(log, key, t)


if __name__ == "__main__":
    main()
```

**Time:** O(1) amortized per `set`, O(log m) per `get`, where `m` is the number of entries for that key. **Space:** O(total entries).

**Without `key=`.** A shorter tuple that matches a prefix is smaller, `(4,) < (4, "baz")`, so `bisect_left(entries, (t,))` is the first entry with time `≥ t`. "First time `> t`" would need a sentinel second field; prefer `key=`.

### Descending lists

`bisect` assumes ascending order. On a list sorted from largest to smallest, "`a[i] ≤ x`" is monotone (`F … T`), so call `first_true(0, n, lambda i: a[i] <= x)` directly, or search with negated keys: `bisect_left(a, -x, key=lambda v: -v)`.

## 7. Advanced: longest increasing subsequence in O(n log n)

The **longest increasing subsequence** (LIS) is the longest list of elements, taken in order but not necessarily adjacent, that strictly increases. For `[3, 1, 4, 1, 5, 9, 2, 6]` one answer is `1, 4, 5, 9`, length 4. The usual dynamic-programming solution is O(n²) ([Dynamic Programming](../09-dynamic-programming/README.md)); lower bound makes it O(n log n).

**The state.** Keep a list `tails`, where `tails[k]` is the **smallest possible last element** of an increasing subsequence of length `k + 1` seen so far. A smaller tail is always better: it leaves more room for later elements.

`tails` is strictly increasing, because a length-3 subsequence contains a length-2 one that ends earlier at a smaller value. So for each new value `v`, binary search where it fits:

- `i = lower_bound(tails, v)`, the first tail `≥ v`.
- `i == len(tails)`: `v` is bigger than every tail and extends the longest subsequence. Append it.
- Otherwise `v` ends a length-`i + 1` subsequence with a smaller tail than before. Set `tails[i] = v`.

**Trace** on `[3, 1, 4, 1, 5, 9, 2, 6]`:

| Value | `lower_bound(tails, v)` | Action | `tails` after |
|---:|---:|---|---|
| 3 | 0 (empty list) | append | `[3]` |
| 1 | 0 | replace `tails[0]` | `[1]` |
| 4 | 1 | append | `[1, 4]` |
| 1 | 0 | replace `tails[0]` (same value) | `[1, 4]` |
| 5 | 2 | append | `[1, 4, 5]` |
| 9 | 3 | append | `[1, 4, 5, 9]` |
| 2 | 1 | replace `tails[1]` | `[1, 2, 5, 9]` |
| 6 | 3 | replace `tails[3]` | `[1, 2, 5, 6]` |

The answer is `len(tails) = 4`. `tails` itself (`1, 2, 5, 6`) is **not** a subsequence of the input: 2 comes after 5 there. Only its length means something.

For **non-decreasing** subsequences (equal values allowed), use upper bound, so an equal value extends instead of replacing.

```python
import random
from bisect import bisect_left, bisect_right


def lis_length(a: list[int], strict: bool = True) -> int:
    tails: list[int] = []
    find = bisect_left if strict else bisect_right
    for v in a:
        i = find(tails, v)
        if i == len(tails):
            tails.append(v)
        else:
            tails[i] = v
    return len(tails)


def lis_quadratic(a: list[int], strict: bool = True) -> int:
    """O(n^2) DP: best[i] = longest valid subsequence ending at a[i]."""
    best = []
    for i, v in enumerate(a):
        fits = [best[j] for j in range(i) if (a[j] < v if strict else a[j] <= v)]
        best.append(1 + max(fits, default=0))
    return max(best, default=0)


def main():
    assert lis_length([3, 1, 4, 1, 5, 9, 2, 6]) == 4
    assert lis_length([]) == 0
    assert lis_length([5, 5, 5]) == 1
    assert lis_length([5, 5, 5], strict=False) == 3

    rng = random.Random(8)
    for _ in range(2000):
        a = [rng.randint(-5, 5) for _ in range(rng.randint(0, 12))]
        assert lis_length(a) == lis_quadratic(a)
        assert lis_length(a, strict=False) == lis_quadratic(a, strict=False)


if __name__ == "__main__":
    main()
```

**Time:** O(n log n). **Space:** O(n) for `tails`.

**Why it's correct.** By induction over the input, `tails[k]` stays the smallest tail of any increasing subsequence of length `k + 1` in the prefix read so far. A new value `v` can extend only subsequences whose tail is `< v`; the longest of those has length `i`, the lower bound, so `v` creates a length-`i + 1` subsequence ending in `v`. Since `tails[i] ≥ v`, the replacement can only lower that tail, and no other entry can improve.

## 8. Summary

**Every question about `x` from two bounds.** `L = lower_bound(a, x)`, `U = upper_bound(a, x)`, on `a = [1, 2, 2, 2, 5, 7]`:

| Question | Formula | `x = 2` | `x = 3` |
|---|---|---:|---:|
| Is `x` present? | `L < len(a) and a[L] == x` | yes | no |
| First occurrence | `L` if present, else −1 | 1 | −1 |
| Last occurrence | `U − 1` if present, else −1 | 3 | −1 |
| Count of `x` | `U − L` | 3 | 0 |
| Insert before / after equal copies | `L` / `U` | 1 / 4 | 4 / 4 |
| Count of values `< x` / `≤ x` | `L` / `U` | 1 / 4 | 4 / 4 |
| Last index with `a[i] < x` / `≤ x` | `L − 1` / `U − 1` (−1 if none) | 0 / 3 | 3 / 3 |
| Count of values in `[low, high]` | `upper_bound(high) − lower_bound(low)` | | |

**As predicates:**

| You want | Pattern | Call | `bisect` |
|---|---|---|---|
| First index with `a[i] ≥ x` | `F F T T` | `first_true(0, n, lambda i: a[i] >= x)` | `bisect_left` |
| First index with `a[i] > x` | `F F T T` | `first_true(0, n, lambda i: a[i] > x)` | `bisect_right` |
| Last index with `a[i] ≤ x` | `T T F F` | `last_true(0, n, lambda i: a[i] <= x)` | `bisect_right − 1` |
| Last index with `a[i] < x` | `T T F F` | `last_true(0, n, lambda i: a[i] < x)` | `bisect_left − 1` |

Every later search in this folder is `first_true` with a different `ok`.

## 9. Pitfalls and practice

1. **Returning early on equality.** A boundary search must keep going after it finds `x`, or it returns an arbitrary copy (§1).
2. **Using the result without a check.** `bisect_left(a, x)` may be `len(a)`, so `a[i]` crashes, or it may point at a different value.
3. **Mixing up left and right.** "First `≥`" is `bisect_left`; "first `>`" is `bisect_right`. Write the predicate down before choosing.
4. **Writing `lo = mid` for "last".** The last index with a property is the first index without it, minus 1 (§2). Handle the −1 result.
5. **Passing a whole record as `x` with `key=`.** `bisect` applies `key` to the elements only (§5).
6. **`insort` in a hot loop on a big list.** Each insertion is O(n).
7. **A predicate that isn't monotone.** `first_true` then returns some position, but usually not a meaningful one. Print the `F … T` pattern on small cases.

Practice: find first and last position of element in sorted array; search insert position; first bad version; count occurrences of a number in a sorted array; time-based key–value store; longest increasing subsequence; Russian doll envelopes (sort widths up, heights down, then LIS); count of smaller numbers in a sorted list for each query.

Next: [Search on the Answer](03-search-on-the-answer.md).
