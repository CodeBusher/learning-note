# Advanced Heaps — Deleting, Updating, and Merging

## 1. Lazy deletion, in general

**Problem.** Support `push(x)`, `remove(x)` for any value currently stored, `peek()` and `pop()` of the minimum. For example, push `5, 1, 3, 7, 2`, remove `3`, remove `1`, then pop: the answer is **2**.

**Brute force.** `h.remove(x)` on the list followed by `heapify(h)`: O(n) per removal.

**Key observation.** This is the trick from the [sliding window median](02-top-k-and-streams.md#5-sliding-window-median-and-lazy-deletion), made general. A removed value only matters if it reaches the root, because `peek` and `pop` only read the root. So instead of removing it now, record it in a counter `dead` and keep a separate count of live items. Whenever the root is dead, pop it for real. This repair step is called **pruning**.

**Invariant.** The root is always live (or the heap is empty), and `size` counts only live values.

**Trace.** `heapq` turns `5, 1, 3, 7, 2` into the list `[1, 2, 3, 7, 5]`:

```text
             1                 remove 3:  dead = {3: 1}
           /   \               root 1 is live, nothing to prune
          2     3
         / \
        7   5                  list [1, 2, 3, 7, 5], size 4

remove 1:  dead = {3: 1, 1: 1}, size 3, root 1 is dead -> prune
  pop 1  -> list [2, 5, 3, 7], root 2 is live, stop

             2                 pop -> returns 2, size 2
           /   \               list [3, 5, 7]: root 3 is dead -> prune
          5     3              pop 3 -> list [5, 7], root 5 is live
         /
        7
```

The dead `3` cost nothing until it reached the root.

```python
import heapq
import random
from collections import Counter


class RemovableHeap:
    def __init__(self):
        self._h = []
        self._dead = Counter()
        self._live = Counter()  # Needed only to reject removing absent values.
        self._size = 0

    def __len__(self):
        return self._size

    def push(self, x):
        heapq.heappush(self._h, x)
        self._live[x] += 1
        self._size += 1

    def remove(self, x):
        if self._live[x] == 0:
            raise ValueError(f"{x!r} is not in the heap")
        self._live[x] -= 1
        self._dead[x] += 1
        self._size -= 1
        self._prune()

    def _prune(self):
        h, dead = self._h, self._dead
        while h and dead[h[0]]:
            dead[h[0]] -= 1
            heapq.heappop(h)

    def peek(self):
        if not self._size:
            raise IndexError("peek from an empty heap")
        return self._h[0]

    def pop(self):
        x = self.peek()
        heapq.heappop(self._h)
        self._live[x] -= 1
        self._size -= 1
        self._prune()
        return x


def main():
    h = RemovableHeap()
    for x in (5, 1, 3, 7, 2):
        h.push(x)
    h.remove(3)
    h.remove(1)
    assert h.pop() == 2 and h._h == [5, 7] and len(h) == 2
    try:
        h.remove(3)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    rng = random.Random(41)
    for _ in range(300):
        h, model = RemovableHeap(), []
        for _ in range(80):
            r = rng.random()
            if r < 0.45 or not model:
                x = rng.randint(-5, 5)
                h.push(x)
                model.append(x)
            elif r < 0.75:
                x = rng.choice(model)
                h.remove(x)
                model.remove(x)
            else:
                assert h.pop() == min(model)
                model.remove(min(model))
            assert len(h) == len(model)
            if model:
                assert h.peek() == min(model)


if __name__ == "__main__":
    main()
```

Each value is pushed once and popped once, so `n` operations cost O(n log n) in total. The catch is memory: dead values that never reach the root stay in the list. If removals vastly outnumber live items, rebuild the heap from live values whenever dead entries exceed half the list.

## 2. Decrease-key, and why Python's Dijkstra re-inserts

**Decrease-key** lowers the priority of an item already in the heap. In a min-heap a smaller priority can only violate the edge *above* the item, so one sift-up repairs it, in O(log n). The catch: you must know **where** the item sits in the list, and `heapq` does not keep that information.

The main customer is **Dijkstra's algorithm** for shortest paths with nonnegative edge weights ([Graphs](../10-graphs/README.md)). It keeps a tentative distance for every vertex, repeatedly finalizes the unfinalized vertex with the smallest tentative distance, and lowers its neighbors' distances. "Lower a neighbor's distance" is a decrease-key.

**The Python workaround: push a new entry, ignore the old one.** When a distance improves, push `(new_distance, v)` and leave the old entry in the heap. When an entry pops, compare it with `dist[v]`; if it is larger, the entry is **stale**, so skip it. That is §1's lazy deletion with the check built into the pop loop:

```text
while heap:
    d, u = heappop(heap)
    if d > dist[u]:
        continue            # stale: u was finalized with a smaller d
    for v, w in adj[u]:
        if d + w < dist[v]:
            dist[v] = d + w
            heappush(heap, (dist[v], v))
```

The full trace, code and correctness proof are in [Dijkstra](../10-graphs/04-shortest-paths/02-dijkstra.md#4-a-heap-with-lazy-deletion). The cost follows from the heap alone: each edge relaxation pushes at most once, so the heap holds at most `E + 1` entries and the time is O((V + E) log E). Since `E ≤ V²`, `log E ≤ 2 log V`, so this equals O((V + E) log V), the same bound as a true decrease-key. Because `heapq` is written in C, re-insertion is usually as fast as or faster than a hand-written decrease-key in Python. The price is memory (stale entries) and no way to ask "what is `v`'s current priority?" from the heap, which is what §3 fixes.

## 3. An indexed priority queue

Sometimes the stale entries are a real problem: priorities change millions of times, or you need `remove(key)` and "what is the current priority of `key`?". An **indexed priority queue** stores each key once and keeps a map `pos[key]` from key to its index in the heap list. Every swap updates `pos` for both keys.

**Operations.**

- `push(key, p)`: append, record `pos`, sift up.
- `update(key, p)`: change the priority, then sift up (if it decreased) or down (if it increased).
- `remove(key)`: swap the key with the last slot, drop the last slot, then sift the moved key up or down.
- `pop()`: `remove` the root's key and return it with its priority.

**Trace of `update`.** Push `a:5, b:3, c:8, d:6`; the heap list is `[b:3, a:5, c:8, d:6]`. Now `update(d, 1)`:

```text
before                       after swap 3<->1             after swap 1<->0
      b:3                          b:3                          d:1
     /    \                       /    \                       /    \
   a:5    c:8                   d:1    c:8                   b:3    c:8
   /                            /                            /
 d:6 -> d:1                   a:5                          a:5

list [b, a, c, d]            [b, d, c, a]                 [d, b, c, a]
pos  b0 a1 c2 d3             b0 d1 c2 a3                  d0 b1 c2 a3
```

```python
import random


class IndexedMinPQ:
    """Min-priority queue of distinct hashable keys with update and remove."""

    def __init__(self):
        self._keys = []   # Heap-ordered list of keys.
        self._prio = {}   # key -> priority
        self._pos = {}    # key -> index in self._keys

    def __len__(self):
        return len(self._keys)

    def __contains__(self, key):
        return key in self._pos

    def priority(self, key):
        return self._prio[key]

    def push(self, key, p):
        if key in self._pos:
            raise ValueError(f"{key!r} already present; use update")
        self._prio[key] = p
        self._pos[key] = len(self._keys)
        self._keys.append(key)
        self._sift_up(len(self._keys) - 1)

    def update(self, key, p):
        i = self._pos[key]  # KeyError if absent.
        old, self._prio[key] = self._prio[key], p
        if p < old:
            self._sift_up(i)
        else:
            self._sift_down(i)

    def remove(self, key):
        i = self._pos[key]
        last = len(self._keys) - 1
        self._swap(i, last)
        self._keys.pop()
        del self._pos[key]
        p = self._prio.pop(key)
        if i < last:  # The moved key may need to go either way.
            moved = self._keys[i]
            self._sift_up(i)
            self._sift_down(self._pos[moved])
        return p

    def peek(self):
        if not self._keys:
            raise IndexError("peek from an empty queue")
        key = self._keys[0]
        return key, self._prio[key]

    def pop(self):
        key, _ = self.peek()
        return key, self.remove(key)

    def _less(self, i, j):
        return self._prio[self._keys[i]] < self._prio[self._keys[j]]

    def _swap(self, i, j):
        k = self._keys
        k[i], k[j] = k[j], k[i]
        self._pos[k[i]], self._pos[k[j]] = i, j

    def _sift_up(self, i):
        while i > 0 and self._less(i, (i - 1) // 2):
            self._swap(i, (i - 1) // 2)
            i = (i - 1) // 2

    def _sift_down(self, i):
        n = len(self._keys)
        while True:
            best = i
            for c in (2 * i + 1, 2 * i + 2):
                if c < n and self._less(c, best):
                    best = c
            if best == i:
                return
            self._swap(i, best)
            i = best


def main():
    pq = IndexedMinPQ()
    for key, p in (("a", 5), ("b", 3), ("c", 8), ("d", 6)):
        pq.push(key, p)
    assert pq._keys == ["b", "a", "c", "d"]
    pq.update("d", 1)
    assert pq._keys == ["d", "b", "c", "a"]
    assert pq._pos == {"d": 0, "b": 1, "c": 2, "a": 3}
    assert pq.pop() == ("d", 1)

    rng = random.Random(43)
    for _ in range(300):
        pq, model = IndexedMinPQ(), {}
        for _ in range(100):
            r = rng.random()
            key = rng.randrange(12)
            if r < 0.35 and key not in model:
                p = rng.randint(-20, 20)
                pq.push(key, p)
                model[key] = p
            elif r < 0.6 and key in model:
                p = rng.randint(-20, 20)
                pq.update(key, p)
                model[key] = p
            elif r < 0.8 and key in model:
                assert pq.remove(key) == model.pop(key)
            elif model:
                k, p = pq.pop()
                assert p == min(model.values()) and model.pop(k) == p
            assert len(pq) == len(model)
            assert all(pq._keys[pq._pos[k]] == k for k in model)
            assert all(pq._prio[pq._keys[(i - 1) // 2]] <= pq._prio[pq._keys[i]]
                       for i in range(1, len(pq._keys)))


if __name__ == "__main__":
    main()
```

Every operation is O(log n) time; `priority`, `in` and `peek` are O(1). Space is O(n). Keys must be distinct and hashable. With this structure Dijkstra keeps at most `V` entries in the heap and does O(V) pops plus O(E) updates, O((V + E) log V) in total.

**The `remove` subtlety.** The last key moved into slot `i` came from a different branch of the tree, so it can be smaller than the new parent or larger than the new children. Try sifting up; if nothing moved, sift down. The random test exercises both directions.

## 4. d-ary heaps

A **d-ary heap** gives every node `d` children instead of 2. The list layout generalizes directly:

$$
\text{children}(i)=d\,i+1,\;\dots,\;d\,i+d,\qquad \text{parent}(i)=\left\lfloor\frac{i-1}{d}\right\rfloor .
$$

A 3-ary heap of `[1, 4, 2, 6, 9, 5, 7, 3, 8, 10]`:

```text
                          1(0)
            /               |               \
        4(1)              2(2)              6(3)
      /   |   \         /   |   \
   9(4) 5(5) 7(6)    3(7) 8(8) 10(9)
```

Check the formulas: the children of index 2 are `3·2+1 = 7` through `3·2+3 = 9`, and the parent of index 9 is `(9−1)//3 = 2`. Every parent is `≤` each of its children, so this is a valid min-heap even though the leaf 3 is smaller than the internal node 4 in another branch.

The height is `log_d n`, so the trade-off is:

- **Sift-up** (push, decrease-key) compares with one parent per level: about `log_d n` comparisons. Larger `d`, **cheaper**.
- **Sift-down** (pop) finds the smallest of `d` children per level: about `d · log_d n` comparisons. Larger `d`, eventually **costlier**.

For `n = 1,000,000`:

| `d` | Height `log_d n` | Push / decrease-key comparisons | Pop comparisons |
|---:|---:|---:|---:|
| 2 | 19.9 | ≈ 20 | ≈ 40 |
| 4 | 10.0 | ≈ 10 | ≈ 40 |
| 8 | 6.6 | ≈ 7 | ≈ 53 |
| 16 | 5.0 | ≈ 5 | ≈ 80 |

Two practical consequences. First, `d = 4` halves the push cost at no extra pop cost, and the 4 children sit next to each other in memory, which suits CPU caches. Second, in Dijkstra with decrease-key there are up to `E` decrease-keys and only `V` pops, so choosing `d ≈ max(2, E / V)` balances them and gives O(E log_{E/V} V), close to linear for dense graphs.

Only the index arithmetic and the "smallest of the children" step change from the binary `MinHeap` of [chapter 1](01-what-a-heap-is.md#6-a-minheap-class-from-scratch):

```python
import random


def d_push(a, x, d):
    a.append(x)
    i = len(a) - 1
    while i > 0 and a[i] < a[(i - 1) // d]:  # Parent uses d, not 2.
        p = (i - 1) // d
        a[i], a[p] = a[p], a[i]
        i = p


def d_pop(a, d):
    if not a:
        raise IndexError("pop from an empty heap")
    last = a.pop()
    if not a:
        return last
    top, a[0], i = a[0], last, 0
    while d * i + 1 < len(a):
        first = d * i + 1  # Children are d*i+1 .. d*i+d.
        c = min(range(first, min(first + d, len(a))), key=a.__getitem__)
        if a[c] >= a[i]:
            break
        a[i], a[c] = a[c], a[i]
        i = c
    return top


def main():
    h = []
    for x in [1, 4, 2, 6, 9, 5, 7, 3, 8, 10]:
        d_push(h, x, 3)
    assert [d_pop(h, 3) for _ in range(10)] == list(range(1, 11))
    rng = random.Random(44)
    for d in range(2, 7):
        for _ in range(100):
            h, model = [], []
            for _ in range(60):
                if model and rng.random() < 0.4:
                    model.sort()
                    assert d_pop(h, d) == model.pop(0)
                else:
                    x = rng.randint(-10, 10)
                    d_push(h, x, d)
                    model.append(x)
                assert all(h[(i - 1) // d] <= h[i] for i in range(1, len(h)))


if __name__ == "__main__":
    main()
```

Push is O(log_d n), pop is O(d log_d n), space O(n).

## 5. Mergeable heaps: the leftist heap

**Problem.** Combine two heaps of sizes `m` and `n` into one. With list-based heaps the best you can do is concatenate and `heapify`: O(m + n). Some algorithms merge constantly (merging groups in union–find style, some scheduling and graph algorithms), and want O(log n).

The list layout is the obstacle: a complete tree has no room for grafting. So go back to **nodes with pointers**, and give up completeness in exchange for a different shape rule.

**Rank.** The **rank** of a node is the number of nodes on the path from it down its right side to a missing child: `rank(None) = 0`, `rank(x) = 1 + rank(x.right)`.

**Leftist property.** At every node, `rank(left) ≥ rank(right)`. The tree leans left, so the **right spine** (the path from the root always going right) is short: a node of rank `r` has at least `2^r − 1` nodes below and including it, so the right spine has at most `log₂(n + 1)` nodes.

**Merge** walks only right spines:

1. If either heap is empty, return the other.
2. Let `a` be the root with the smaller key (swap if needed). `a` is the new root.
3. Set `a.right = merge(a.right, b)`.
4. If now `rank(a.left) < rank(a.right)`, swap `a`'s children. Set `rank(a) = 1 + rank(a.right)`.

Each recursive call moves one step down a right spine, so merge takes O(log m + log n). `push` merges with a one-node heap; `pop` merges the root's two children.

**Trace.** Merge `A` (root 1, children 3 and 7) with `B` (root 2, left child 5). Ranks in brackets.

```text
A:     1[2]            B:     2[1]
      /    \                  /
    3[1]   7[1]             5[1]

merge(1, 2): 1 < 2, root stays 1; 1.right = merge(7, 2)
  merge(7, 2): 2 < 7, swap so the root is 2; 2.right = merge(None, 7) = 7
    2 now has left 5[1], right 7[1]: ranks are fine, rank(2) = 2
  back at 1: left 3[1], right 2[2]: 1 < 2 breaks the rule -> swap children
  rank(1) = 1 + rank(3) = 2

result:        1[2]
              /    \
           2[2]    3[1]
          /    \
        5[1]   7[1]
```

```python
import random


class Node:
    __slots__ = ("key", "left", "right", "rank")

    def __init__(self, key):
        self.key, self.left, self.right, self.rank = key, None, None, 1


def rank(node):
    return node.rank if node else 0


def merge(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if b.key < a.key:
        a, b = b, a
    a.right = merge(a.right, b)
    if rank(a.left) < rank(a.right):
        a.left, a.right = a.right, a.left
    a.rank = 1 + rank(a.right)
    return a


class LeftistHeap:
    def __init__(self):
        self.root, self.size = None, 0

    def __len__(self):
        return self.size

    def push(self, key):
        self.root = merge(self.root, Node(key))
        self.size += 1

    def peek(self):
        if self.root is None:
            raise IndexError("peek from an empty heap")
        return self.root.key

    def pop(self):
        key = self.peek()
        self.root = merge(self.root.left, self.root.right)
        self.size -= 1
        return key

    def meld(self, other):
        """Move every item of other into self, in O(log n)."""
        self.root = merge(self.root, other.root)
        self.size += other.size
        other.root, other.size = None, 0


def check(node):
    """Return the subtree size; assert heap order, leftist rule, and ranks."""
    if node is None:
        return 0
    for child in (node.left, node.right):
        assert child is None or node.key <= child.key
    assert rank(node.left) >= rank(node.right)
    assert node.rank == 1 + rank(node.right)
    return 1 + check(node.left) + check(node.right)


def main():
    a, b = LeftistHeap(), LeftistHeap()
    for x in (1, 3, 7):
        a.push(x)
    for x in (2, 5):
        b.push(x)
    a.meld(b)
    assert len(b) == 0 and check(a.root) == 5
    assert [a.pop() for _ in range(5)] == [1, 2, 3, 5, 7]

    big = LeftistHeap()
    for x in range(100000, 0, -1):  # Recursion depth stays O(log n).
        big.push(x)
    assert big.pop() == 1

    rng = random.Random(45)
    for _ in range(200):
        heaps = [LeftistHeap() for _ in range(3)]
        models = [[] for _ in range(3)]
        for _ in range(60):
            i = rng.randrange(3)
            r = rng.random()
            if r < 0.5:
                x = rng.randint(-10, 10)
                heaps[i].push(x)
                models[i].append(x)
            elif r < 0.8 and models[i]:
                m = min(models[i])
                assert heaps[i].pop() == m
                models[i].remove(m)
            else:
                j = rng.randrange(3)
                if i != j:
                    heaps[i].meld(heaps[j])
                    models[i] += models[j]
                    models[j] = []
            for h, m in zip(heaps, models):
                assert check(h.root) == len(h) == len(m)


if __name__ == "__main__":
    main()
```

`merge`, `push`, `pop` and `meld` are O(log n) time; `peek` is O(1); space is O(n) nodes. Recursion depth is bounded by the two right spines, under 40 even for a billion items.

**A sibling: the pairing heap.** A pairing heap stores a root with a list of child heaps. `push` and `meld` are O(1): compare two roots and make the larger one a child of the smaller. `pop` removes the root and merges its children in pairs, left to right, then merges the results right to left; this is O(log n) amortized (averaged over a sequence of operations). It is simpler than a leftist heap and fast in practice.

## 6. Fibonacci heaps, in brief

A **Fibonacci heap** is a collection of trees with lazy bookkeeping: inserts and melds only add a tree to a root list, and all the tidying is postponed until a `pop`, which consolidates trees of equal size. Decrease-key cuts the node out and moves it to the root list, and a "mark" bit on each node limits how many cuts a parent can lose before it is cut too. That rule keeps every tree's size exponential in its number of children (by a Fibonacci-number argument, hence the name).

The bounds are **amortized**: averaged over any sequence of operations, not per operation (the full comparison is in §7). With O(1) decrease-key, Dijkstra runs in O(E + V log V), and Prim's minimum spanning tree algorithm likewise. That is the theoretical best for comparison-based priority queues. In practice the constant factors (many pointers per node, poor cache behavior) usually make a binary or 4-ary heap with re-insertion faster in real programs.

## 7. Summary: choosing a heap

| You need | Use | Section |
|---|---|---|
| Push, pop, peek | `heapq` | [Chapter 1](01-what-a-heap-is.md) |
| Occasional removal of arbitrary values | Lazy deletion with a counter | §1 |
| Shortest paths in Python | `heapq` with re-insertion and a stale check | §2 |
| Many priority changes, remove by key, read a key's priority | Indexed priority queue | §3 |
| Many more pushes or decrease-keys than pops | 4-ary or `d`-ary heap | §4 |
| Frequent merging of whole heaps | Leftist or pairing heap | §5 |
| Best asymptotic Dijkstra or Prim | Fibonacci heap (theory) | §6 |

Costs side by side (amortized where marked):

| Operation | Binary heap | Leftist heap | Pairing heap | Fibonacci heap |
|---|---:|---:|---:|---:|
| Push | O(log n) | O(log n) | O(1) | O(1) |
| Find minimum | O(1) | O(1) | O(1) | O(1) |
| Pop minimum | O(log n) | O(log n) | O(log n) amortized | O(log n) amortized |
| Decrease-key | O(log n) with an index | O(log n) | Sub-logarithmic amortized (exact bound is open) | O(1) amortized |
| Meld | O(n) | O(log n) | O(1) | O(1) |
| Build from `n` items | O(n) | O(n) | O(n) | O(n) |

## 8. Pitfalls and practice

1. Lazy deletion with a `set` instead of a counter. Duplicate values then lose track of how many copies are dead.
2. Forgetting to prune after a removal or a pop, which leaves a dead value at the root for the next `peek`.
3. Dijkstra's stale check written as `d != dist[u]` is fine; `d >= dist[u]` is wrong (it skips the valid entry). Use `d > dist[u]`.
4. Dijkstra with negative edges. Neither re-insertion nor decrease-key makes it correct; use Bellman–Ford.
5. Indexed queue: updating `pos` for only one of the two swapped keys, or sifting only up after `remove`.
6. `d`-ary heap: using `2 * i + 1` out of habit. Every index formula must use `d`.
7. Leftist heap: swapping children based on key instead of rank, or forgetting to recompute the rank after a swap.
8. Choosing a Fibonacci heap for speed in Python. Its benefits are asymptotic and rarely show up at practical sizes.

Practice: design a removable priority queue; sliding window median (with your §1 class); network delay time; path with minimum effort; cheapest flights within k stops; implement Prim's algorithm with an indexed priority queue; merge many priority queues in a union–find setting (leftist heap); compare 2-ary and 4-ary heaps on a million random pushes and pops.

Next: back to the [Heaps and Priority Queues overview](README.md).
