# What a Heap Is — Always Serve the Most Urgent Task

## 1. Always serve the most urgent ticket

Tickets arrive at a help desk all day, each with a priority number, where **smaller means more urgent**. Whenever an agent is free, they take the most urgent open ticket. Two operations come in any order:

- `push(p)`: a ticket with priority `p` arrives.
- `pop()`: remove and return the smallest priority waiting.

Push `5, 3, 8`, pop (returns 3), push `1`, pop twice (returns 1, then 5). A structure that supports exactly these two operations is a **priority queue**.

**Two lists, each slow at one thing.** An unsorted list pushes in O(1) (append) but pops in O(n) (scan for the minimum). A sorted list pops in O(1) but pushes in O(n) (shift everything after the insertion point). With `n` pushes and `n` pops mixed together, either one costs about `n²` steps: a trillion for a million tickets.

**The idea.** Keep the items only *partly* sorted: enough order that the minimum is always at a known place, not so much that an insert must shift everything. A **binary heap** does both operations in about `log₂ n` steps, about 20 for a million items.

## 2. A complete binary tree stored in a list

A heap is a binary tree (each node has at most two children; vocabulary such as root, leaf and height is in [Trees](../03-trees/README.md)). It is always a **complete** binary tree: levels fill top to bottom, and the last level fills left to right with no gaps. Here is one with 7 nodes, values inside and list index in parentheses:

```text
              2(0)
           /        \
       5(1)          3(2)
      /    \        /    \
   9(3)    6(4)  8(5)    4(6)

index:  0  1  2  3  4  5  6
value: [2, 5, 3, 9, 6, 8, 4]
```

Because there are no gaps, no pointers are needed. Number the nodes level by level, left to right, from 0, and store node `i` at `heap[i]`. The family relations become arithmetic:

$$
\text{left}(i)=2i+1,\qquad \text{right}(i)=2i+2,\qquad \text{parent}(i)=\left\lfloor\frac{i-1}{2}\right\rfloor .
$$

Check: node 1 (value 5) has children at 3 (value 9) and 4 (value 6). Node 5 (value 8) has parent `(5−1)//2 = 2` (value 3).

**Why the formulas work.** Level `d` holds indices `2^d − 1` through `2^{d+1} − 2`. The children of level `d` fill level `d + 1` in the same left-to-right order, two per parent. So node `i`'s children come right after the children of the `i` nodes before it: at `2i + 1` and `2i + 2`.

A complete tree with `n` nodes has height `⌊log₂ n⌋`: 2 for 7 nodes, 19 for a million. Every operation below walks one root-to-leaf path, which is where the `log n` comes from.

## 3. The heap property

A **min-heap** is a complete binary tree where **every parent is less than or equal to each of its children**. A **max-heap** flips the comparison.

The tree in §2 is a min-heap: `2 ≤ 5, 2 ≤ 3`, `5 ≤ 9, 5 ≤ 6`, `3 ≤ 8, 3 ≤ 4`.

Three consequences:

1. **The root is the minimum.** Follow any value upward: each parent is no larger, and every path ends at the root.
2. **Siblings are not ordered.** `5` sits to the left of `3`. The heap promises nothing between siblings or cousins, which is exactly why it is cheaper to maintain than a sorted list.
3. **The list is not sorted.** `[2, 5, 3, 9, 6, 8, 4]` is a valid heap. Reading `heap[1]` does *not* give you the second smallest item.

## 4. Push: sift-up, step by step

To push, put the new value in the only spot that keeps the tree complete: the next free slot, which is the end of the list. That may break the heap property between the new node and its parent. Fix it by **sifting up**: while the new value is smaller than its parent, swap them.

Push `1` into the heap from §2. The path the value climbs is 7 → 3 → 1 → 0:

| Step | `1` is at | Parent (value) | Compare | List afterwards |
|---|---:|---|---|---|
| append | 7 | 3 (9) | 1 < 9: swap | `[2, 5, 3, 9, 6, 8, 4, 1]` |
| 1 | 3 | 1 (5) | 1 < 5: swap | `[2, 5, 3, 1, 6, 8, 4, 9]` |
| 2 | 1 | 0 (2) | 1 < 2: swap | `[2, 1, 3, 5, 6, 8, 4, 9]` |
| 3 | 0 | none | root: stop | `[1, 2, 3, 5, 6, 8, 4, 9]` |

```text
before (1 appended at 7)          after
              2(0)                          1(0)
           /        \                    /        \
       5(1)          3(2)             2(1)          3(2)
      /    \        /    \           /    \        /    \
   9(3)    6(4)  8(5)    4(6)      5(3)    6(4)  8(5)    4(6)
   /                               /
 1(7)                            9(7)
```

Only the path from the new leaf to the root changed; every other node stayed put.

**Why is the result a heap?** Before the push every edge was fine. Say the moving value `x` swaps with its parent `P`, whose other child is `S`. Now `x` sits above `P` and `S`, and `x < P ≤ S`, so both edges below `x` hold. `P` moves into `x`'s old slot, whose children were already below `P` before, so `P` is `≤` them. The only edge that can still be wrong is the one above `x`, and that is exactly what the loop checks next. At most one swap per level: O(log n).

## 5. Pop: sift-down, step by step

The minimum is `heap[0]`. Removing it leaves a hole at the root. The only node we can delete without making a gap is the **last** one, so move the last value into the root and shrink the list by one. Now the root may be too large. Fix it by **sifting down**: while the value is larger than its smaller child, swap it with that smaller child.

Pop from `[1, 2, 3, 5, 6, 8, 4, 9]`: save the answer `1`, move the last value `9` to the root, and sift it down.

| Step | `9` is at | Children (values) | Smaller child | List afterwards |
|---|---:|---|---|---|
| move last to root | 0 | 1 (2), 2 (3) | 2 at index 1: swap | `[2, 9, 3, 5, 6, 8, 4]` |
| 1 | 1 | 3 (5), 4 (6) | 5 at index 3: swap | `[2, 5, 3, 9, 6, 8, 4]` |
| 2 | 3 | 7, 8 (past the end) | none: stop | `[2, 5, 3, 9, 6, 8, 4]` |

The heap is back to the tree of §2, and the pop returns `1`.

**Why the smaller child?** After the swap, the child we chose becomes the parent of the other child. If we had swapped with the larger child (6 in step 1), then 6 would sit above 5, which breaks the property. Swapping with the smaller child makes the new parent `≤` both children by construction.

## 6. A `MinHeap` class from scratch

The trace becomes two helper methods. Everything else is bookkeeping.

```python
import random


class MinHeap:
    """A binary min-heap stored in a Python list."""

    def __init__(self, items=()):
        self._a = list(items)
        # Build in O(n): sift down every internal node, last one first (§7).
        for i in range(len(self._a) // 2 - 1, -1, -1):
            self._sift_down(i)

    def __len__(self):
        return len(self._a)

    def push(self, value):
        self._a.append(value)
        self._sift_up(len(self._a) - 1)

    def peek(self):
        if not self._a:
            raise IndexError("peek from an empty heap")
        return self._a[0]

    def pop(self):
        if not self._a:
            raise IndexError("pop from an empty heap")
        last = self._a.pop()
        if not self._a:
            return last  # The last item was the root.
        top = self._a[0]
        self._a[0] = last
        self._sift_down(0)
        return top

    def _sift_up(self, i):
        a = self._a
        while i > 0:
            parent = (i - 1) // 2
            if a[i] < a[parent]:
                a[i], a[parent] = a[parent], a[i]
                i = parent
            else:
                break

    def _sift_down(self, i):
        a, n = self._a, len(self._a)
        while True:
            smallest = i
            left, right = 2 * i + 1, 2 * i + 2
            if left < n and a[left] < a[smallest]:
                smallest = left
            if right < n and a[right] < a[smallest]:
                smallest = right
            if smallest == i:
                return
            a[i], a[smallest] = a[smallest], a[i]
            i = smallest

    def is_valid(self):
        a = self._a
        return all(a[(i - 1) // 2] <= a[i] for i in range(1, len(a)))


def main():
    # The traces from §4 and §5.
    h = MinHeap()
    h._a = [2, 5, 3, 9, 6, 8, 4]
    h.push(1)
    assert h._a == [1, 2, 3, 5, 6, 8, 4, 9]
    assert h.pop() == 1
    assert h._a == [2, 5, 3, 9, 6, 8, 4]

    # The help desk from §1.
    desk = MinHeap()
    for p in (5, 3, 8):
        desk.push(p)
    assert desk.pop() == 3
    desk.push(1)
    assert [desk.pop(), desk.pop()] == [1, 5]

    # Edge cases.
    empty = MinHeap()
    for bad in (empty.pop, empty.peek):
        try:
            bad()
            raise AssertionError("expected IndexError")
        except IndexError:
            pass
    assert MinHeap([7]).pop() == 7

    # Random mixed operations, checked against a sorted Python list.
    rng = random.Random(1)
    for _ in range(300):
        heap = MinHeap(rng.choices(range(-5, 6), k=rng.randint(0, 8)))
        model = sorted(heap._a)
        for _ in range(60):
            if model and rng.random() < 0.45:
                assert heap.pop() == model.pop(0)
            else:
                v = rng.randint(-10, 10)
                heap.push(v)
                model = sorted(model + [v])
            assert len(heap) == len(model)
            assert heap.is_valid()
            if model:
                assert heap.peek() == model[0]


if __name__ == "__main__":
    main()
```

`push` and `pop` are O(log n) time, `peek` and `len` O(1). The heap uses O(n) space for `n` items and O(1) extra.

The random test compares every operation with a model that is slow but easy to trust: a list re-sorted after each change.

## 7. Building a heap in O(n)

Given `n` items at once, you could push them one by one: O(n log n). There is a faster way, called **heapify** or **build-heap**: treat the list as a complete tree as it stands, then sift down every node that has children, starting from the last one and moving toward the root.

The nodes with children are indices `0` through `n//2 − 1`; everything after that is a leaf. A leaf on its own is already a valid heap of size 1.

Trace on `[9, 4, 7, 1, 8, 2, 3]` (n = 7, so sift down indices 2, 1, 0):

| Step | Node | Value vs. children | Swaps | List afterwards |
|---|---:|---|---|---|
| start | | | | `[9, 4, 7, 1, 8, 2, 3]` |
| 1 | 2 | 7 vs (2, 3): smaller child 2 | 2 ↔ 5 | `[9, 4, 2, 1, 8, 7, 3]` |
| 2 | 1 | 4 vs (1, 8): smaller child 1 | 1 ↔ 3 | `[9, 1, 2, 4, 8, 7, 3]` |
| 3 | 0 | 9 vs (1, 2): smaller child 1 | 0 ↔ 1 | `[1, 9, 2, 4, 8, 7, 3]` |
| 3 cont. | 1 | 9 vs (4, 8): smaller child 4 | 1 ↔ 3 | `[1, 4, 2, 9, 8, 7, 3]` |

**Why go from the bottom up?** When we sift down node `i`, both of its subtrees are already heaps, because their roots have larger indices and were handled first. Sift-down is exactly the repair for "a root sitting on top of two valid heaps".

**Why is it O(n) and not O(n log n)?** A sift-down from a node at height `h` (distance to the deepest leaf below it) costs at most `h` swaps. Most nodes are near the bottom, where `h` is tiny. In a complete tree at most `⌈n / 2^{h+1}⌉` nodes have height `h`. For `n = 15`:

| Height `h` | Nodes at that height | Max swaps each | Max swaps total |
|---:|---:|---:|---:|
| 0 (leaves) | 8 | 0 | 0 |
| 1 | 4 | 1 | 4 |
| 2 | 2 | 2 | 4 |
| 3 (root) | 1 | 3 | 3 |
| | 15 | | **11** |

Pushing one at a time could cost up to 34 swaps here. In general:

$$
\sum_{h\ge 0}\frac{n}{2^{h+1}}\cdot h=\frac{n}{2}\sum_{h\ge0}\frac{h}{2^{h}}=\frac{n}{2}\cdot 2=n .
$$

The series `Σ h/2^h` equals 2, so the total work is at most about `n` swaps. The expensive sift-downs happen at only a handful of nodes near the root.

## 8. Heap sort

A heap can sort a list in place, with no extra list:

1. Build a **max**-heap over the whole list (O(n)). Now the largest value is at index 0.
2. Swap index 0 with the last index of the heap part. The largest value is now in its final sorted place. Shrink the heap part by one and sift down the new root.
3. Repeat until the heap part has one item.

Trace on `[3, 1, 4, 2]`. The bar `|` separates the heap part (left) from the sorted part (right).

| Step | Action | List |
|---|---|---|
| 0 | start | `[3, 1, 4, 2]` |
| 1 | build max-heap: sift down 1 (1 < child 2) | `[3, 2, 4, 1]` |
| 2 | build max-heap: sift down 0 (3 < child 4) | `[4, 2, 3, 1]` |
| 3 | swap 0 ↔ 3 | `[1, 2, 3, \| 4]` |
| 4 | sift down the root in size 3 (children 2, 3; larger 3) | `[3, 2, 1, \| 4]` |
| 5 | swap 0 ↔ 2 | `[1, 2, \| 3, 4]` |
| 6 | sift down the root in size 2 (child 2) | `[2, 1, \| 3, 4]` |
| 7 | swap 0 ↔ 1 | `[1, \| 2, 3, 4]` |

```python
import random


def sift_down_max(a, i, n):
    """Sift a[i] down within the max-heap a[:n]."""
    while True:
        largest = i
        left, right = 2 * i + 1, 2 * i + 2
        if left < n and a[left] > a[largest]:
            largest = left
        if right < n and a[right] > a[largest]:
            largest = right
        if largest == i:
            return
        a[i], a[largest] = a[largest], a[i]
        i = largest


def heap_sort(a):
    """Sort the list a in place, ascending."""
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):
        sift_down_max(a, i, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down_max(a, 0, end)


def main():
    a = [3, 1, 4, 2]
    heap_sort(a)
    assert a == [1, 2, 3, 4]
    for empty_or_one in ([], [5]):
        b = list(empty_or_one)
        heap_sort(b)
        assert b == empty_or_one
    rng = random.Random(2)
    for _ in range(500):
        data = [rng.randint(-20, 20) for _ in range(rng.randint(0, 30))]
        b = data[:]
        heap_sort(b)
        assert b == sorted(data)


if __name__ == "__main__":
    main()
```

Heap sort is O(n log n) time in the worst case and O(1) extra space. It is **not stable**: equal values can change their relative order, because a swap at the root jumps over everything in between. In practice it is slower than Python's built-in `sorted` (Timsort), so its value here is the idea: a heap is a sorting machine you can stop at any point.

## 9. Python's `heapq`

Python ships a min-heap as a set of functions on an ordinary list. The list *is* the heap, in exactly the layout of §2.

| Call | Does | Time |
|---|---|---:|
| `heapq.heappush(h, x)` | push `x` | O(log n) |
| `heapq.heappop(h)` | pop and return the smallest | O(log n) |
| `h[0]` | look at the smallest without removing it | O(1) |
| `heapq.heapify(h)` | turn a list into a heap in place | O(n) |
| `heapq.heapreplace(h, x)` | pop the smallest, *then* push `x` | O(log n) |
| `heapq.heappushpop(h, x)` | push `x`, *then* pop the smallest | O(log n) |
| `heapq.nsmallest(k, it)` / `nlargest(k, it)` | the `k` smallest / largest, sorted | O(n log k) |

Four things to know:

**1. Min-heap only.** For a max-heap of numbers, push `-x` and negate what you pop. (Python 3.14 adds `heappush_max` and friends; negation works on every version.)

**2. Tuples compare left to right.** Push `(priority, item)` to order items by priority. If two priorities tie, Python compares the items next. That fails if the items are not comparable (dictionaries, custom objects), and it silently changes the order if they are. The fix is a **counter** in the middle: `(priority, count, item)`. Counts are unique, so the comparison never reaches `item`, and equal priorities come out in arrival order (first in, first out).

**3. `heapreplace` vs `heappushpop`.** Both do one push and one pop with a single sift. `heapreplace` pops first, so it can return a value larger than `x`; it raises `IndexError` on an empty heap. `heappushpop` pushes first, so if `x` is smaller than everything it returns `x` immediately without touching the heap.

**4. `nsmallest`/`nlargest`** are best when `k` is small compared with `n`. For `k = 1` use `min`/`max`; for `k` close to `n` use `sorted(...)[:k]`.

```python
import heapq
import random


def main():
    h = []
    for x in (5, 3, 8, 1):
        heapq.heappush(h, x)
    assert h[0] == 1
    assert [heapq.heappop(h) for _ in range(4)] == [1, 3, 5, 8]

    data = [9, 4, 7, 1, 8, 2, 3]
    heapq.heapify(data)
    assert data == [1, 4, 2, 9, 8, 7, 3]  # Same as the trace in §7.

    # Max-heap by negation.
    mx = []
    for x in (5, 3, 8, 1):
        heapq.heappush(mx, -x)
    assert -heapq.heappop(mx) == 8

    # Tie-breaking with a counter: equal priorities leave in arrival order,
    # and dicts are never compared.
    tasks, count = [], 0
    for priority, task in [(2, {"name": "b"}), (1, {"name": "a"}), (2, {"name": "c"})]:
        heapq.heappush(tasks, (priority, count, task))
        count += 1
    assert [heapq.heappop(tasks)[2]["name"] for _ in range(3)] == ["a", "b", "c"]
    try:
        heapq.heappush(tasks, (1, {"x": 1}))
        heapq.heappush(tasks, (1, {"y": 2}))  # Tie on 1, then dict < dict.
        raise AssertionError("expected TypeError")
    except TypeError:
        pass

    # heapreplace pops first; heappushpop pushes first.
    h = [2, 4, 6]
    assert heapq.heapreplace(h, 1) == 2 and h[0] == 1
    h = [2, 4, 6]
    assert heapq.heappushpop(h, 1) == 1 and h == [2, 4, 6]

    rng = random.Random(3)
    for _ in range(200):
        xs = [rng.randint(-50, 50) for _ in range(rng.randint(0, 40))]
        k = rng.randint(0, 10)
        assert heapq.nsmallest(k, xs) == sorted(xs)[:k]
        assert heapq.nlargest(k, xs) == sorted(xs, reverse=True)[:k]


if __name__ == "__main__":
    main()
```

Notice that `heapq.heapify` produced exactly the list from the hand trace in §7. It runs the same bottom-up algorithm.

## 10. Summary

| Structure | `push` | `pop` minimum | Look at minimum | Build from `n` items |
|---|---:|---:|---:|---:|
| Unsorted list | O(1) | O(n) | O(n) | O(n) |
| Sorted list | O(n) | O(1) | O(1) | O(n log n) |
| Binary heap | O(log n) | O(log n) | O(1) | O(n) |

- Layout: complete tree in a list; children `2i + 1`, `2i + 2`; parent `(i − 1) // 2`.
- Invariant: every parent `≤` its children, so the root is the minimum and nothing else is promised.
- Push = append + sift-up (compare with the parent). Pop = move the last item to the root + sift-down (swap with the **smaller** child).
- Build-heap = sift-down every internal node from `n//2 − 1` down to 0, O(n).

## 11. Pitfalls and practice

1. Reading `heap[1]` or `heap[-1]` as "second smallest" or "largest". Only `heap[0]` has a guaranteed meaning.
2. Forgetting that `heapq` is a min-heap. A max-heap needs `-x` on the way in **and** on the way out.
3. Pushing `(priority, item)` where items are not comparable, or where tie order matters. Add a counter.
4. Swapping with the larger child in sift-down, which breaks the property between the two children.
5. Modifying an item's priority while it sits in the heap. The heap does not notice, so its order is silently wrong. [Advanced Heaps](04-advanced-heaps.md) shows the safe ways.
6. Pushing `n` items one at a time when they are all available up front. `heapify` is O(n).
7. Calling `heappop` or `heapreplace` on an empty list (`IndexError`). Check `if h:` first.

Practice: implement a max-heap class by flipping the comparisons; last stone weight; sort an array with heap sort; check whether a given list is a valid min-heap; kth largest element in an array (preview of the next chapter). For each heap operation, trace it on paper with both the tree and the list before running code.

Next: [Top-K and Streams](02-top-k-and-streams.md).
