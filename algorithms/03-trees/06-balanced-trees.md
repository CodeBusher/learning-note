# Balanced Trees — Rotations, Treaps and AVL Trees (Advanced)

## 1. A sorted multiset under any input order

**Problem.** Values arrive and leave one at a time, possibly in sorted order. Between updates, answer "how many values are smaller than `x`?" (the **rank** of `x`) and "what is the `k`-th smallest value?".

**The candidates so far.**

- A sorted list with `bisect` answers both queries in O(log n), but `insort` and deletion shift up to `n` elements: O(n) per update.
- A [binary search tree](03-binary-search-trees.md) with subtree sizes does everything in O(h). Fed sorted input, it becomes a chain with `h = n`.

**The goal.** Keep `h = O(log n)` whatever the order of updates. A tree that guarantees this is **balanced**. Every balanced BST does it with one local repair, the rotation, and differs only in the rule that decides when to rotate.

## 2. Rotations

A **rotation** changes which of two neighboring nodes is the parent, without breaking the BST property. A right rotation at `y`, whose left child is `x`:

```text
          y                      x
         / \                    / \
        x   C       ==>        A   y
       / \                        / \
      A   B                      B   C
```

Here `A`, `B`, `C` are whole subtrees, possibly empty. Inorder before: `A x B y C`. Inorder after: `A x B y C`. The order is the same, so the result is still a BST. Only `B` changes parent: it was right of `x`, and it becomes left of `y`. It belongs there, since every value in `B` is between `x` and `y`. A **left rotation** is the mirror image and undoes a right rotation.

A rotation moves `A` one level up and `C` one level down; that is how it changes height. It rewires three pointers, so it costs O(1). Any stored subtree summary (size, height) must be recomputed for `y` **first**, then for `x`, since `y` is now `x`'s child.

**Smallest example.** Inserting `3, 2, 1` into a plain BST makes a chain leaning left. One right rotation at 3 makes 2 the root, with children 1 and 3: height 3 becomes height 2.

```python
class Node:
    def __init__(self, key, left=None, right=None):
        self.key = key
        self.left = left
        self.right = right


def rotate_right(y):
    x = y.left
    y.left = x.right  # subtree B changes parent
    x.right = y
    return x  # the new root of this subtree


def rotate_left(x):
    y = x.right
    x.right = y.left
    y.left = x
    return y


def inorder(node):
    return [] if node is None else inorder(node.left) + [node.key] + inorder(node.right)


def main():
    chain = Node(3, Node(2, Node(1)))
    root = rotate_right(chain)
    assert root.key == 2 and root.left.key == 1 and root.right.key == 3
    # A rotation keeps the inorder; a left rotation undoes a right one.
    y = Node(20, Node(10, Node(5), Node(15)), Node(30))
    before = inorder(y)
    x = rotate_right(y)
    assert inorder(x) == before and x.key == 10 and x.right.left.key == 15
    assert inorder(rotate_left(x)) == before


if __name__ == "__main__":
    main()
```

## 3. Treaps: balance by random priorities

A **treap** (tree + heap) gives every node a random **priority** at creation. It keeps two rules at once:

- **BST** on the keys: smaller keys left, larger right.
- **Heap** on the priorities: every parent has a larger priority than its children, as in a max-heap ([What a Heap Is](../07-heaps-and-priority-queues/01-what-a-heap-is.md)).

**Why it is balanced.** For distinct keys and priorities, exactly one tree satisfies both rules: the root must be the key with the largest priority, the keys smaller than it form the left subtree by the same rule, and so on. That is also the tree a plain BST builds when the keys are **inserted in decreasing priority order**. The priorities are random, so the treap looks like a BST built from a random insertion order, whatever order the keys really arrived in. Such a tree has expected depth about 2 ln n ≈ 1.39 log₂ n ([§6 of the BST chapter](03-binary-search-trees.md#6-why-height-matters)). An adversary can't produce a bad input, because the shape depends on coins they don't see.

**Insert.** Insert as a leaf, as in a plain BST. That keeps the BST rule but may break the heap rule between the new node and its parent. While the new node's priority beats its parent's, rotate it up; each rotation keeps the BST rule.

Trace: insert the sorted keys `1 2 3 4 5` (a chain for a plain BST), with priorities fixed for the trace at `1:50, 2:80, 3:20, 4:90, 5:40`.

| Insert | Lands as | Rotations | Tree after (`key` with children in parentheses) |
|---|---|---|---|
| 1 (50) | root | — | 1 |
| 2 (80) | right of 1 | 80 > 50: left rotation at 1 | 2(1, ·) |
| 3 (20) | right of 2 | 20 < 80: none | 2(1, 3) |
| 4 (90) | right of 3 | 90 > 20: left at 3; 90 > 80: left at 2 | 4(2(1, 3), ·) |
| 5 (40) | right of 4 | 40 < 90: none | 4(2(1, 3), 5) |

The result is the BST of the keys inserted in priority order `4, 2, 1, 5, 3`, height 3.

**Delete.** Find the node. While it has two children, rotate up the child with the **larger** priority (so the heap rule holds above it); the node to delete moves one level down each time. Once it has at most one child, replace it by that child. Deleting 4 from the tree above:

| Step | Node 4's children | Action | Tree after |
|---|---|---|---|
| 1 | 2 (80), 5 (40) | rotate 2 up (right rotation at 4) | 2(1, 4(3, 5)) |
| 2 | 3 (20), 5 (40) | rotate 5 up (left rotation at 4) | 2(1, 5(4(3, ·), ·)) |
| 3 | 3 only | replace 4 by 3 | 2(1, 5(3, ·)) |

**Order statistics.** Each node stores `count` (copies of its key, so the treap is a multiset) and `size` (copies in its subtree). Rotations recompute both for the two nodes involved. Then `kth` and `rank` descend as in [§4 of the BST chapter](03-binary-search-trees.md#4-order-queries-k-th-smallest-successor-ranges).

The test runs random inserts, deletes, ranks and k-th queries against a sorted list maintained with `bisect`, and inserts 100,000 sorted keys to check the height.

```python
import bisect
import math
import random


class Node:
    def __init__(self, key, prio):
        self.key = key
        self.prio = prio
        self.count = 1  # copies of key
        self.size = 1  # copies in this subtree
        self.left = None
        self.right = None


def size(node):
    return node.size if node else 0


def pull(node):
    node.size = node.count + size(node.left) + size(node.right)


def rotate_right(y):
    x = y.left
    y.left, x.right = x.right, y
    pull(y)  # y is now below x: update it first
    pull(x)
    return x


def rotate_left(x):
    y = x.right
    x.right, y.left = y.left, x
    pull(x)
    pull(y)
    return y


class Treap:
    def __init__(self, seed=0):
        self.root = None
        self.rng = random.Random(seed)

    def __len__(self):
        return size(self.root)

    def insert(self, key, prio=None):
        self.root = self._insert(self.root, key, self.rng.random() if prio is None else prio)

    def _insert(self, node, key, prio):
        if node is None:
            return Node(key, prio)
        if key == node.key:
            node.count += 1
        elif key < node.key:
            node.left = self._insert(node.left, key, prio)
            if node.left.prio > node.prio:
                node = rotate_right(node)
        else:
            node.right = self._insert(node.right, key, prio)
            if node.right.prio > node.prio:
                node = rotate_left(node)
        pull(node)
        return node

    def delete(self, key):
        """Remove one copy; return False if key is absent."""
        if self.count(key) == 0:
            return False
        self.root = self._delete(self.root, key)
        return True

    def _delete(self, node, key):
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        elif node.count > 1:
            node.count -= 1
        elif node.left is None:
            return node.right
        elif node.right is None:
            return node.left
        elif node.left.prio > node.right.prio:  # larger priority moves up
            node = rotate_right(node)
            node.right = self._delete(node.right, key)
        else:
            node = rotate_left(node)
            node.left = self._delete(node.left, key)
        pull(node)
        return node

    def count(self, key):
        node = self.root
        while node and node.key != key:
            node = node.left if key < node.key else node.right
        return node.count if node else 0

    def rank(self, key):
        """How many stored values are < key."""
        node, smaller = self.root, 0
        while node:
            if key <= node.key:
                node = node.left
            else:
                smaller += size(node.left) + node.count
                node = node.right
        return smaller

    def kth(self, k):
        """k-th smallest value, 1-based, counting copies."""
        if not 1 <= k <= len(self):
            raise ValueError("k out of range")
        node = self.root
        while True:
            left = size(node.left)
            if k <= left:
                node = node.left
            elif k <= left + node.count:
                return node.key
            else:
                k -= left + node.count
                node = node.right


def shape(node):
    if node is None:
        return None
    return (node.key, shape(node.left), shape(node.right))


def height(node):
    return 0 if node is None else 1 + max(height(node.left), height(node.right))


def heap_ok(node):
    return node is None or all(
        child is None or (child.prio <= node.prio and heap_ok(child))
        for child in (node.left, node.right))


def main():
    t = Treap()
    for key, prio in [(1, 50), (2, 80), (3, 20), (4, 90), (5, 40)]:
        t.insert(key, prio)
    assert shape(t.root) == (4, (2, (1, None, None), (3, None, None)), (5, None, None))
    assert t.delete(4) and shape(t.root) == (2, (1, None, None), (5, (3, None, None), None))
    assert not t.delete(4) and t.rank(3) == 2 and t.kth(4) == 5

    rng = random.Random(1)
    for trial in range(200):
        t, ref = Treap(seed=trial), []
        for _ in range(80):
            x = rng.randint(-10, 10)
            op = rng.random()
            if op < 0.5:
                t.insert(x)
                bisect.insort(ref, x)
            elif op < 0.8:
                had = x in ref
                assert t.delete(x) == had
                if had:
                    ref.remove(x)
            assert len(t) == len(ref) and heap_ok(t.root)
            assert t.rank(x) == bisect.bisect_left(ref, x)
            assert t.count(x) == ref.count(x)
            if ref:
                k = rng.randint(1, len(ref))
                assert t.kth(k) == ref[k - 1]

    big = Treap(seed=7)
    n = 100_000
    for key in range(n):  # sorted input: a chain for a plain BST
        big.insert(key)
    assert height(big.root) < 3 * math.log2(n)
    assert big.kth(12_345) == 12_344 and big.rank(500) == 500


if __name__ == "__main__":
    main()
```

**Time:** O(log n) expected per operation, for any input order. **Space:** O(n) nodes; O(log n) expected recursion depth.

A second family of treaps uses two operations instead of rotations: `split(t, k)` cuts a treap into keys `< k` and `≥ k`, and `merge(a, b)` joins two treaps whose keys don't overlap. Insert is split + merge + merge, and the same pair supports cutting and joining whole ranges, which makes "implicit treaps" a sequence with O(log n) reversal of any slice.

## 4. AVL trees: balance by a height rule

An **AVL tree** stores each node's height and keeps one deterministic rule:

> At every node, the heights of the two subtrees differ by at most 1.

That is the "balanced" of [Recursion on Trees](02-recursion-on-trees.md#3-bottom-up-with-a-sentinel-is-the-tree-balanced), kept true after every update.

**Why the height is O(log n).** Let `N(h)` be the fewest nodes an AVL tree of height `h` can have. Its root has one subtree of height `h − 1` and, at worst, one of height `h − 2`, so `N(h) = N(h − 1) + N(h − 2) + 1`. That grows like the Fibonacci numbers, about 1.618^h, so `h ≤ 1.44 log₂ n`.

**Repair.** After an insert or delete, walk back up the path. At each node, recompute its height and its **balance factor** `bf = height(left) − height(right)`. If `bf` is +2 or −2, rotate. There are four shapes, two of them mirrors:

| Shape | Meaning | Fix |
|---|---|---|
| LL | `bf = +2`, left child leans left or is even | right rotation at the node |
| LR | `bf = +2`, left child leans right | left rotation at the left child, then right rotation at the node |
| RR | `bf = −2`, right child leans right or is even | left rotation at the node |
| RL | `bf = −2`, right child leans left | right rotation at the right child, then left rotation at the node |

The LR case is the one a single rotation can't fix. Insert `3, 1, 2`:

```text
   3   bf +2            3                    2
  /                    /                    / \
 1     leans right    2       then         1   3
  \                  /        right at 3
   2                1
       left at 1
```

A single right rotation at 3 would give `1(·, 3(2, ·))`, which leans as badly the other way. The first rotation turns the zig-zag into a straight line that the second can fix.

"Left child is even" (both its subtrees the same height) only happens after a delete, and the single rotation is right for it. The code checks `height(left.left) < height(left.right)` to choose LR, so the even case goes to LL.

```python
import math
import random


class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1


def h(node):
    return node.height if node else 0


def fix(node):
    node.height = 1 + max(h(node.left), h(node.right))


def rotate_right(y):
    x = y.left
    y.left, x.right = x.right, y
    fix(y)
    fix(x)
    return x


def rotate_left(x):
    y = x.right
    x.right, y.left = y.left, x
    fix(x)
    fix(y)
    return y


def rebalance(node):
    fix(node)
    bf = h(node.left) - h(node.right)
    if bf > 1:
        if h(node.left.left) < h(node.left.right):  # LR: straighten first
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if bf < -1:
        if h(node.right.right) < h(node.right.left):  # RL
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node


def insert(node, key):
    if node is None:
        return Node(key)
    if key < node.key:
        node.left = insert(node.left, key)
    elif key > node.key:
        node.right = insert(node.right, key)
    return rebalance(node)


def delete(node, key):
    if node is None:
        return None
    if key < node.key:
        node.left = delete(node.left, key)
    elif key > node.key:
        node.right = delete(node.right, key)
    elif node.left is None or node.right is None:
        return node.left or node.right
    else:  # two children: take the successor's key
        succ = node.right
        while succ.left:
            succ = succ.left
        node.key = succ.key
        node.right = delete(node.right, succ.key)
    return rebalance(node)


def check(node):
    """Return the true height; assert AVL rule, stored heights and order."""
    if node is None:
        return 0
    lh, rh = check(node.left), check(node.right)
    assert abs(lh - rh) <= 1 and node.height == 1 + max(lh, rh)
    assert node.left is None or node.left.key < node.key
    assert node.right is None or node.right.key > node.key
    return 1 + max(lh, rh)


def inorder(node):
    return [] if node is None else inorder(node.left) + [node.key] + inorder(node.right)


def main():
    root = None
    for key in (3, 1, 2):  # the LR case
        root = insert(root, key)
    assert (root.key, root.left.key, root.right.key) == (2, 1, 3)

    rng = random.Random(2)
    for _ in range(300):
        root, keys = None, set()
        for _ in range(60):
            x = rng.randint(0, 40)
            if rng.random() < 0.6:
                root = insert(root, x)
                keys.add(x)
            else:
                root = delete(root, x)
                keys.discard(x)
            check(root)
            assert inorder(root) == sorted(keys)

    n = 2 ** 14
    root = None
    for key in range(n):  # sorted input
        root = insert(root, key)
    assert check(root) <= 1.45 * math.log2(n + 2)


if __name__ == "__main__":
    main()
```

**Time:** O(log n) worst case per operation. **Space:** O(n), and O(log n) recursion.

## 5. Red-black trees and what libraries use

Java's `TreeMap` and C++'s `std::map` are **red-black trees**. Each node is colored red or black; no red node has a red child, and every path from a node down to a `None` passes the same number of black nodes. The longest path is then at most twice the shortest, so `h ≤ 2 log₂(n + 1)`. The rule is looser than AVL's, so updates need fewer rotations (at most two for an insert, three for a delete) at the cost of slightly taller trees. The case analysis is long and rarely asked for in full; knowing the guarantee and the trade-off is usually enough.

## 6. Python has no TreeMap

The standard library has no balanced BST. The practical options:

| Need | Tool | Cost |
|---|---|---|
| Sorted container, up to about 10⁵ updates | `list` + `bisect.insort` / `bisect_left` + `del a[i]` | O(log n) search, O(n) update with a fast memory shift |
| Only the minimum or maximum | `heapq` ([Heaps](../07-heaps-and-priority-queues/README.md)) | O(log n) |
| All values known in advance (offline) | coordinate compression + Fenwick tree: rank by prefix sum, k-th by descent ([Fenwick Tree](../04-range-queries/02-fenwick-tree.md)) | O(log n) |
| Online, many updates, rank and k-th | the treap of §3 | O(log n) expected |
| Allowed third-party packages | `sortedcontainers.SortedList` | about O(log n) in practice |

For most interview-size inputs, a sorted list with `bisect` is enough and much shorter. Reach for a treap when updates are both online and numerous, for example 10⁶ inserts into the middle of the order.

## 7. Summary

| Tree | Balance rule | Height | Repair | Notes |
|---|---|---|---|---|
| Plain BST | none | up to `n` | — | sorted input makes a chain |
| Treap | heap on random priorities | ≈ 1.39 log₂ n expected | rotate up on insert, down on delete | shortest code; split/merge variant |
| AVL | subtree heights differ by ≤ 1 | ≤ 1.44 log₂ n | LL, LR, RR, RL rotations on the way up | strictest balance, fastest lookups |
| Red-black | colors, equal black height | ≤ 2 log₂(n + 1) | recolor, ≤ 3 rotations | used by most standard libraries |

All of them rest on the rotation: O(1), keeps the inorder, moves one subtree up and one down. Store subtree sizes to get rank and k-th in O(log n).

## 8. Pitfalls and practice

1. **Updating sizes or heights in the wrong order after a rotation.** The lower node first (§2).
2. **A single rotation for the LR or RL shape.** It mirrors the imbalance instead of fixing it (§4).
3. **Rotating down the lower-priority child on treap delete.** The heap rule breaks (§3).
4. **Deleting a key that isn't there** from a counted multiset (§3).
5. **Writing a balanced tree when `bisect` on a list is fast enough** (§6).

Practice: count of smaller numbers after self; count of range sum; reverse pairs; contains duplicate III; my calendar I and II; sliding window median; data stream as disjoint intervals; the skyline problem (ordered multiset of heights); kth largest element in a stream with deletions.

Next: back to the [Trees README](README.md).
