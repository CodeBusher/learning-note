# Top-K and Streams — Keep Only What Can Still Win

## 1. The k-th largest element

**Problem.** Given a list `nums` and an integer `k` with `1 ≤ k ≤ len(nums)`, return the `k`-th largest value, counting duplicates. For `nums = [3, 2, 1, 5, 6, 4]` and `k = 2`, the sorted order is `[1, 2, 3, 4, 5, 6]`; the largest is 6 and the 2nd largest is **5**.

**Brute force.** `sorted(nums)[-k]`. It costs O(n log n) and needs the whole list in memory. If `nums` is a stream of a billion numbers and `k = 10`, we sort a billion items to look at ten.

**Key observation.** At any moment, only the `k` largest values seen so far can still be the answer. Everything smaller than all of them is dead forever: `k` larger values already exist, so it can never rise to rank `k`.

**Invariant.** After reading each value, `heap` is a min-heap (Python's `heapq`, from [What a Heap Is](01-what-a-heap-is.md#9-pythons-heapq)) holding the `k` largest values seen so far. Its root `heap[0]` is the *smallest* of those `k`, which is the `k`-th largest overall.

**Why a min-heap and not a max-heap?** The question at each new value is "does it beat the weakest of my top `k`?". The weakest member is the one to evict, so we need fast access to the minimum of the kept set. A max-heap would put the strongest member at the root, which is the one we never evict.

**Trace** with `nums = [3, 2, 1, 5, 6, 4]`, `k = 2`:

| Read | Heap before | Rule | Heap after (as a list) | `heap[0]` |
|---:|---|---|---|---:|
| 3 | `[]` | fewer than k: push | `[3]` | 3 |
| 2 | `[3]` | fewer than k: push | `[2, 3]` | 2 |
| 1 | `[2, 3]` | 1 ≤ 2: dead, skip | `[2, 3]` | 2 |
| 5 | `[2, 3]` | 5 > 2: replace root | `[3, 5]` | 3 |
| 6 | `[3, 5]` | 6 > 3: replace root | `[5, 6]` | 5 |
| 4 | `[5, 6]` | 4 ≤ 5: dead, skip | `[5, 6]` | 5 |

The answer is `heap[0] = 5`. ✓

### Quickselect, the in-memory alternative

When the whole list is in memory and can be modified, **quickselect** finds the `k`-th largest in average O(n). It is quicksort that recurses into only one side. Pick a random **pivot** value, split the list into values greater than, equal to and less than the pivot, then look only in the part that contains rank `k`:

```text
nums = [3, 2, 1, 5, 6, 4], k = 2, pivot = 4
greater = [5, 6]   equal = [4]   less = [3, 2, 1]
len(greater) = 2 >= k = 2  ->  the answer is the 2nd largest of [5, 6]
pivot = 5: greater = [6], equal = [5]
len(greater) = 1 < 2 <= 1 + 1  ->  the answer is the pivot, 5
```

Each round keeps on average a constant fraction of the list, so the work is about `n + n/2 + n/4 + … ≈ 2n`. A random pivot makes the O(n²) worst case (always picking the extreme value) extremely unlikely.

```python
import heapq
import random


def kth_largest_heap(nums, k):
    if not 1 <= k <= len(nums):
        raise ValueError("need 1 <= k <= len(nums)")
    heap = []
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)  # Evict the weakest, insert x.
    return heap[0]


def kth_largest_quickselect(nums, k, rng=random.Random(0)):
    if not 1 <= k <= len(nums):
        raise ValueError("need 1 <= k <= len(nums)")
    items = list(nums)
    while True:
        pivot = rng.choice(items)
        greater = [x for x in items if x > pivot]
        equal_count = sum(1 for x in items if x == pivot)
        if k <= len(greater):
            items = greater
        elif k <= len(greater) + equal_count:
            return pivot
        else:
            k -= len(greater) + equal_count
            items = [x for x in items if x < pivot]


def main():
    assert kth_largest_heap([3, 2, 1, 5, 6, 4], 2) == 5
    assert kth_largest_heap([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert kth_largest_quickselect([3, 2, 1, 5, 6, 4], 2) == 5
    assert kth_largest_heap([7], 1) == 7
    for bad_k in (0, 2):
        try:
            kth_largest_heap([1], bad_k)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
    rng = random.Random(11)
    for _ in range(1000):
        nums = [rng.randint(-10, 10) for _ in range(rng.randint(1, 25))]
        k = rng.randint(1, len(nums))
        expected = sorted(nums)[-k]
        assert kth_largest_heap(nums, k) == expected
        assert kth_largest_quickselect(nums, k) == expected


if __name__ == "__main__":
    main()
```

The heap version is O(n log k) time and O(k) space, and it reads the input once, so it works on streams. Quickselect is O(n) average time, O(n) worst-case extra space as written (the in-place partition version uses O(1)), and needs all values at once.

**Why the heap version is correct.** By induction on the values read. If the heap holds the top `k` of the first `i` values, then the top `k` of the first `i + 1` values are either the same set (the new value is no larger than the weakest member) or the same set with the weakest member swapped for the new value. Those are exactly the two branches.

## 2. Variants: a different key, the opposite direction

The size-`k` heap from §1 changes in only two ways across the "top k" family: **what is compared** and **which end is evicted**.

**Top k frequent elements.** Return the `k` values that appear most often. For `nums = [1, 1, 1, 2, 2, 3]` and `k = 2` the counts are `{1: 3, 2: 2, 3: 1}`, so the answer is `[1, 2]`. Count with `collections.Counter`, then run §1 on pairs `(count, value)`: the pair `(1, 3)` arrives when the heap holds `(2, 2), (3, 1)`, loses to the root `(2, 2)`, and is skipped.

A count lies between 1 and `n`, so there is also a comparison-free **bucket** method: put each value in bucket `count`, then walk buckets from `n` down to 1 until `k` values are collected. That is O(n).

**K closest points to the origin.** For `[(1, 3), (-2, 2), (2, -1)]` and `k = 2` the squared distances are `10, 8, 5`, so the answer is `(2, -1)` and `(-2, 2)`. Two changes from §1:

- Compare **squared** distances `x² + y²`. A square root does not change the order and adds floating-point error.
- This is "k smallest", so the weakest kept candidate is the **farthest** one: the heap must expose its maximum. Push `(-d, index)`. The index breaks ties without comparing point tuples. When `(2, -1)` arrives (`d = 5`), the root is `(-10, 0)`; `5 < 10`, so `(1, 3)` is evicted.

```python
import heapq
import random
from collections import Counter


def top_k_frequent_heap(nums, k):
    counts = Counter(nums)
    if not 0 <= k <= len(counts):
        raise ValueError("need 0 <= k <= number of distinct values")
    if k == 0:
        return []
    heap = []
    for value, c in counts.items():
        if len(heap) < k:
            heapq.heappush(heap, (c, value))
        elif c > heap[0][0]:
            heapq.heapreplace(heap, (c, value))
    return [value for _, value in heap]


def top_k_frequent_buckets(nums, k):
    counts = Counter(nums)
    if not 0 <= k <= len(counts):
        raise ValueError("need 0 <= k <= number of distinct values")
    buckets = [[] for _ in range(len(nums) + 1)]
    for value, c in counts.items():
        buckets[c].append(value)
    result = []
    for c in range(len(nums), 0, -1):
        for value in buckets[c]:
            if len(result) == k:
                return result
            result.append(value)
    return result


def k_closest(points, k):
    if not 0 <= k <= len(points):
        raise ValueError("need 0 <= k <= len(points)")
    if k == 0:
        return []
    heap = []  # (-squared distance, index): a max-heap on distance.
    for i, (x, y) in enumerate(points):
        d = x * x + y * y
        if len(heap) < k:
            heapq.heappush(heap, (-d, i))
        elif d < -heap[0][0]:
            heapq.heapreplace(heap, (-d, i))
    return [points[i] for _, i in heap]


def check_frequent(nums, k, answer):
    counts = Counter(nums)
    assert len(set(answer)) == len(answer) == k
    best = sorted(counts.values(), reverse=True)[:k]
    assert sorted((counts[v] for v in answer), reverse=True) == best


def main():
    assert sorted(top_k_frequent_heap([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent_buckets([1, 1, 1, 2, 2, 3], 2) == [1, 2]
    assert top_k_frequent_heap([], 0) == []
    assert sorted(k_closest([(1, 3), (-2, 2), (2, -1)], 2)) == [(-2, 2), (2, -1)]
    assert k_closest([(0, 0)], 0) == []
    rng = random.Random(12)
    for _ in range(1000):
        nums = [rng.randint(-4, 4) for _ in range(rng.randint(0, 30))]
        k = rng.randint(0, len(set(nums)))
        check_frequent(nums, k, top_k_frequent_heap(nums, k))
        check_frequent(nums, k, top_k_frequent_buckets(nums, k))

        pts = [(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(rng.randint(0, 15))]
        k = rng.randint(0, len(pts))
        got = sorted(x * x + y * y for x, y in k_closest(pts, k))
        assert got == sorted(x * x + y * y for x, y in pts)[:k]


if __name__ == "__main__":
    main()
```

With `n` values and `u` distinct ones, top-k frequent by heap is O(n + u log k) time and O(u) space; buckets are O(n). K closest is O(n log k) time and O(k) space. When counts or distances tie at the boundary, several answers are correct, so the tests compare the multiset of counts or distances, not one fixed list.

## 3. Sorting a nearly sorted array

**Problem.** Every element of `a` is at most `k` positions away from where it belongs in sorted order. Sort it. For `a = [6, 5, 3, 2, 8, 10, 9]` and `k = 3`, the answer is `[2, 3, 5, 6, 8, 9, 10]`.

**Brute force.** `sorted(a)`: O(n log n), ignoring the promise.

**Key observation.** The element that belongs at position 0 is somewhere in `a[0 : k + 1]`. After placing it, the element for position 1 is somewhere in `a[0 : k + 2]` minus what we placed. In general, the next smallest is always among the next `k + 1` unplaced elements in reading order.

**Invariant.** Before writing output position `i`, the heap holds exactly the unplaced elements among `a[0 : i + k + 1]`.

| Output pos | Push | Heap contents (sorted for reading) | Pop |
|---:|---|---|---:|
| setup | 6, 5, 3, 2 | {2, 3, 5, 6} | |
| 0 | 8 | {2, 3, 5, 6, 8} | 2 |
| 1 | 10 | {3, 5, 6, 8, 10} | 3 |
| 2 | 9 | {5, 6, 8, 9, 10} | 5 |
| 3 | — | {6, 8, 9, 10} | 6 |
| 4–6 | — | drain | 8, 9, 10 |

Here `heappushpop` does "push the next element, pop the smallest" in one sift.

```python
import heapq
import random


def sort_k_sorted(a, k):
    if k < 0:
        raise ValueError("k must be nonnegative")
    heap = list(a[: k + 1])
    heapq.heapify(heap)
    out = []
    for x in a[k + 1 :]:
        out.append(heapq.heappushpop(heap, x))
    while heap:
        out.append(heapq.heappop(heap))
    return out


def make_k_sorted(n, k, rng):
    """A list whose elements are each at most k places from sorted order."""
    values = sorted(rng.randint(-20, 20) for _ in range(n))
    order = sorted(range(n), key=lambda i: i + rng.uniform(0, k))
    return [values[i] for i in order]


def main():
    assert sort_k_sorted([6, 5, 3, 2, 8, 10, 9], 3) == [2, 3, 5, 6, 8, 9, 10]
    assert sort_k_sorted([], 2) == []
    assert sort_k_sorted([1, 2, 3], 0) == [1, 2, 3]
    rng = random.Random(14)
    for _ in range(1000):
        n, k = rng.randint(0, 25), rng.randint(0, 6)
        a = make_k_sorted(n, k, rng)
        assert sort_k_sorted(a, k) == sorted(a)


if __name__ == "__main__":
    main()
```

O(n log k) time, O(k) extra space. With `k = 0` the heap has one element and the method degenerates to copying the list.

## 4. Median of a data stream

**Problem.** Numbers arrive one at a time. After each, report the **median**: the middle value in sorted order, or the average of the two middle values when the count is even. After `5, 15, 1, 3` the sorted values are `[1, 3, 5, 15]` and the median is `(3 + 5) / 2 = 4`.

**Brute force.** Keep a sorted list and insert with `bisect.insort`: O(n) per insert because of shifting, O(n²) for the stream.

**Key observation.** The median depends only on the boundary between the smaller half and the larger half. We need the largest of the smaller half and the smallest of the larger half, nothing else. That is one max-heap and one min-heap.

**Invariant.**

- `low` is a max-heap (stored negated) holding the smaller half; `high` is a min-heap holding the larger half.
- Every value in `low` is `≤` every value in `high`.
- `len(low) == len(high)` or `len(low) == len(high) + 1`.

Then the median is `top(low)` when the count is odd, and `(top(low) + top(high)) / 2` when it is even.

**Insert recipe.** Push `x` into `low`. Move the largest of `low` to `high` (this restores the ordering, whatever `x` was). If `high` is now bigger than `low`, move its smallest back to `low`.

**Trace** for the stream `5, 15, 1, 3, 8, 7`. Heaps are shown as sets with their top marked by `*`.

| Insert | After push to `low` | After moving `low`'s max | After rebalancing | Median |
|---:|---|---|---|---:|
| 5 | low {5*} | low {}, high {5*} | low {5*}, high {} | 5 |
| 15 | low {5, 15*} | low {5*}, high {15*} | (sizes 1, 1) | (5 + 15)/2 = 10 |
| 1 | low {1, 5*} | low {1*}, high {5*, 15} | low {1, 5*}, high {15*} | 5 |
| 3 | low {1, 3, 5*} | low {1, 3*}, high {5*, 15} | (sizes 2, 2) | (3 + 5)/2 = 4 |
| 8 | low {1, 3, 8*} | low {1, 3*}, high {5*, 8, 15} | low {1, 3, 5*}, high {8*, 15} | 5 |
| 7 | low {1, 3, 5, 7*} | low {1, 3, 5*}, high {7*, 8, 15} | (sizes 3, 3) | (5 + 7)/2 = 6 |

Check the last row: sorted `[1, 3, 5, 7, 8, 15]`, middle two 5 and 7, median 6. ✓

```python
import heapq
import random


class MedianFinder:
    def __init__(self):
        self.low = []   # Max-heap of the smaller half, values negated.
        self.high = []  # Min-heap of the larger half.

    def add(self, x):
        heapq.heappush(self.low, -x)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if not self.low:
            raise ValueError("median of an empty stream")
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2


def brute_median(values):
    s = sorted(values)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def main():
    mf = MedianFinder()
    seen = []
    for x in (5, 15, 1, 3, 8, 7):
        mf.add(x)
        seen.append(mf.median())
    assert seen == [5, 10, 5, 4, 5, 6]
    try:
        MedianFinder().median()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    rng = random.Random(15)
    for _ in range(300):
        mf, values = MedianFinder(), []
        for _ in range(rng.randint(1, 40)):
            x = rng.randint(-10, 10)
            mf.add(x)
            values.append(x)
            assert mf.median() == brute_median(values)
            assert len(mf.low) - len(mf.high) in (0, 1)


if __name__ == "__main__":
    main()
```

Each `add` is O(log n) (at most three pushes and two pops), `median` is O(1), and space is O(n).

**Why the invariant survives `add`.** Let `b` be the value moved from `low` to `high`: the maximum of the old `low` plus `x`.

- *Order.* `b` is `≥` everything left in `low`, so it may join `high`. Everything left in `low` is `≤` every old member of `high`: old `low` values already were, and if `x` stayed in `low` then `x ≤ b`, where `b` is an old `low` value.
- *Sizes.* `(m, m)` becomes `(m, m + 1)`, and the final step moves `high`'s minimum back, giving `(m + 1, m)`. `(m + 1, m)` becomes `(m + 1, m + 1)`. Moving `high`'s minimum into `low` keeps the order, because it is `≤` the rest of `high` and `≥` all of `low`.

## 5. Sliding window median and lazy deletion

**Problem.** Given `nums` and a window size `k`, report the median of every window `nums[i : i + k]`. For `nums = [1, 3, -1, -3, 5, 3, 6, 7]` and `k = 3` the answer is `[1, -1, -1, 3, 5, 6]`.

**Brute force.** Sort each window: O(n · k log k).

**The obstacle.** §4 handles insertions. A sliding window also *removes* the value leaving on the left, which may sit anywhere inside a heap, and `heapq` can only remove the root.

**Key idea: lazy deletion.** Don't remove it now. Write it in a `delayed` counter ("one copy of `-1` is dead") and fix the **sizes** we track by hand. Only when a dead value reaches the top of a heap, where it could affect an answer, pop it for real. This is called **pruning**.

**Invariant.**

- `small_size` and `large_size` count only **live** values in each heap; the lists may also hold dead ones.
- The top of each heap is always live (we prune after every change that could expose a dead top).
- Live values satisfy the §4 invariant: `small_size == large_size` or `small_size == large_size + 1`.

**Trace** for `[1, 3, -1, -3, 5, 3, 6, 7]`, `k = 3`. Each slide inserts the entering value, then erases the leaving one; rows that repeat an earlier pattern are merged. Heaps are shown as sorted sets with the top marked `*`; a dead entry still sitting in a list is written with `~`. Sizes are the live counts `(small_size, large_size)`.

| Steps | Action | `small` (max-heap) | `large` (min-heap) | Sizes | Median |
|---|---|---|---|---|---:|
| 1–3 | insert 1, 3, −1 (3 > 1 goes to `large`) | {−1, 1*} | {3*} | (2, 1) | **1** |
| 4 | insert −3 → sizes (3, 1): **rebalance**, move 1 to `large` | {−3, −1*} | {1*, 3} | (2, 2) | |
| 5 | erase 1: it is `large`'s top, so **prune** it at once | {−3, −1*} | {3*} | (2, 1) | **−1** |
| 6–7 | insert 5, erase 3: same pattern as 4–5 | {−3, −1*} | {5*} | (2, 1) | **−1** |
| 8–9 | insert 3 (to `large`), erase −1: `small`'s top, prune → (1, 2), move 3 to `small` | {−3, 3*} | {5*} | (2, 1) | **3** |
| 10–11 | insert 6, erase −3: **inside** `small`, only marked dead → (1, 2), move 5 to `small` | {~−3, 3, 5*} | {6*} | (2, 1) | **5** |
| 12–13 | insert 7, erase 5: `small`'s top, prune → (1, 2), move 6 to `small` | {~−3, 3, 6*} | {7*} | (2, 1) | **6** |

From step 11 on, the dead `−3` stays in the list with no harm: it is not at a top, and `small_size` says `small` has one live value fewer than its length. If it ever rises to the top, the next prune removes it.

```python
import heapq
import random
from collections import Counter


class SlidingMedian:
    def __init__(self):
        self.small, self.large = [], []  # Max-heap (negated), min-heap.
        self.delayed = Counter()
        self.small_size = self.large_size = 0

    def _prune(self, heap, sign):
        while heap and self.delayed[sign * heap[0]]:
            self.delayed[sign * heap[0]] -= 1
            heapq.heappop(heap)

    def _balance(self):
        if self.small_size > self.large_size + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
            self.small_size -= 1
            self.large_size += 1
            self._prune(self.small, -1)
        elif self.small_size < self.large_size:
            heapq.heappush(self.small, -heapq.heappop(self.large))
            self.small_size += 1
            self.large_size -= 1
            self._prune(self.large, 1)

    def insert(self, x):
        if not self.small or x <= -self.small[0]:
            heapq.heappush(self.small, -x)
            self.small_size += 1
        else:
            heapq.heappush(self.large, x)
            self.large_size += 1
        self._balance()

    def erase(self, x):
        self.delayed[x] += 1
        if x <= -self.small[0]:
            self.small_size -= 1
            if x == -self.small[0]:
                self._prune(self.small, -1)
        else:
            self.large_size -= 1
            if x == self.large[0]:
                self._prune(self.large, 1)
        self._balance()

    def median(self):
        if self.small_size > self.large_size:
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2


def sliding_median(nums, k):
    if not 1 <= k <= len(nums):
        raise ValueError("need 1 <= k <= len(nums)")
    sm = SlidingMedian()
    for x in nums[:k]:
        sm.insert(x)
    out = [sm.median()]
    for i in range(k, len(nums)):
        sm.insert(nums[i])
        sm.erase(nums[i - k])
        out.append(sm.median())
    return out


def brute(nums, k):
    out = []
    for i in range(len(nums) - k + 1):
        s = sorted(nums[i : i + k])
        out.append(s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2)
    return out


def main():
    assert sliding_median([1, 3, -1, -3, 5, 3, 6, 7], 3) == [1, -1, -1, 3, 5, 6]
    assert sliding_median([2, 2, 2, 2], 2) == [2, 2, 2]
    assert sliding_median([4], 1) == [4]
    rng = random.Random(16)
    for _ in range(1500):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(1, 30))]
        k = rng.randint(1, len(nums))
        assert sliding_median(nums, k) == brute(nums, k)


if __name__ == "__main__":
    main()
```

O(n log n) time: each value is pushed once and popped at most once (by a move or a prune), and a heap never holds more than O(n) entries. Space is O(n) in the worst case, because dead values can pile up below the tops. A balanced ordered container (a sorted list with O(log k) updates) gives O(n log k); Python's standard library has none, so the lazy two-heap version is the usual answer. The fixed-size window itself is the pattern from [Sliding Window](../05-sliding-window/README.md).

**Why does `erase` choose the side with `x <= -small[0]`?** Every live value in `small` is `≤` its top, and every live value in `large` is `≥` that top. If `x` equals the top it may sit in either heap, but equal values are interchangeable, so charging the removal to `small` is safe.

## 6. Summary: choosing a method

| Situation | Method | Time | Extra space |
|---|---|---:|---:|
| `k`-th largest, input is a stream or too big for memory | Size-`k` min-heap | O(n log k) | O(k) |
| `k`-th largest, all in memory, one query | Quickselect | O(n) average | O(1) in place |
| `k` largest, sorted output, `k` close to `n` | `sorted` | O(n log n) | O(n) |
| Top `k` by frequency | Counter + size-`k` heap, or buckets | O(n + u log k) or O(n) | O(u) or O(n) |
| Sort when each element is ≤ `k` from home | Heap of `k + 1` | O(n log k) | O(k) |
| Median after every insert | Two heaps | O(log n) per insert | O(n) |
| Median of every window | Two heaps + lazy deletion | O(n log n) | O(n) |

The common thread: **the heap holds the candidates that can still win, and its root is the one closest to losing.**

## 7. Pitfalls and practice

1. Using a max-heap for "k largest". The root must be the weakest kept candidate, so "k largest" needs a min-heap and "k smallest" a max-heap.
2. Pushing every value and popping when the size exceeds `k` is correct but does an extra push per value. Compare with `heap[0]` first and use `heapreplace`.
3. Taking square roots for distances. Compare squared integers.
4. Returning `heap` and assuming it is sorted. If order matters, sort the `k` results at the end.
5. In two-heap medians, forgetting the negation on one of the reads, or letting the size difference drift to 2.
6. In lazy deletion, using `len(heap)` as the live size. Track live sizes separately and prune after every move.
7. Integer division in medians. `(a + b) / 2` gives a float; if the problem wants exact output, use `fractions.Fraction` or keep the doubled value `a + b`.

Practice: kth largest element in an array; kth largest element in a stream; top k frequent elements; top k frequent words (ties by alphabetical order); k closest points to origin; find k closest elements; sort a nearly sorted (k-sorted) array; find median from data stream; sliding window median; last stone weight.

Next: [Merging and Scheduling](03-merging-and-scheduling.md).
