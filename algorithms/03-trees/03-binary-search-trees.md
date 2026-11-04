# Binary Search Trees — Sorted Order You Can Insert Into

## 1. A sorted set that accepts inserts

Keep a set of numbers under three operations: search, insert, delete, plus questions like "what is the next value above 7?" A sorted Python list answers searches in O(log n) with binary search, but inserting or deleting shifts up to `n` elements.

A **binary search tree** (BST) keeps the order in the shape instead of in positions. It is a binary tree with one rule:

> **BST property:** for every node, every value in its left subtree is smaller, and every value in its right subtree is larger.

The running tree is a BST:

```text
              8
            /   \
           3     10
          / \      \
         1   6      14
            / \     /
           4   7   13
```

**Search** compares with the current node and discards one side, like [binary search](../01-binary-search/01-the-idea.md): smaller goes left, larger goes right, until the value is found or the walk falls off at `None`.

| Search 7 | Search 5 |
|---|---|
| 8: 7 < 8, go left | 8: go left |
| 3: 7 > 3, go right | 3: go right |
| 6: 7 > 6, go right | 6: 5 < 6, go left |
| 7: found | 4: 5 > 4, go right → `None`: missing |

**Insert** walks exactly like a search for the new value and hangs a new leaf where the search fell off. Inserting 5 makes it the right child of 4. The tree stays a BST because every comparison on the way put 5 on the correct side of that ancestor.

Both cost O(h), where `h` is the height. That is fast only if the tree is bushy (§6).

## 2. Delete: three cases

Deleting a node must keep the BST property and keep every other value. The recursive form returns **the new root of the subtree**, so the parent writes `node.left = delete(node.left, key)`, as list code writes `head = f(head)` in [Nodes and Pointers](../02-linked-lists/01-nodes-and-pointers.md).

**No children (delete 7).** Return `None`; 6 loses its right child.

**One child (delete 14).** Return the child: 10's right pointer now goes to 13. Everything under 14 was already in the right place relative to 10.

**Two children (delete 3).** This is the hard case. Node 3 has two subtrees and its parent has one pointer to give. Some value must take 3's place, and it must be larger than everything left of it and smaller than everything right of it. The **inorder successor** works: the smallest value in the right subtree, found by going right once and then left until there is no left child. For 3, that is 4.

```text
before                 copy 4 into the node      remove the old 4 from the right subtree
       3                      4                          4
      / \                    / \                        / \
     1   6                  1   6                      1   6
        / \                    / \                          \
       4   7                  4   7                          7
```

Why it is correct:

- **The order holds.** 4 is larger than all of the left subtree (it came from the right of 3) and smaller than everything left in the right subtree (it was the smallest there).
- **The second delete is easy.** The successor has **no left child**, otherwise that child would be smaller and would be the successor. So removing it is case 1 or case 2, never case 2-children again.

Deleting the root 8 works the same way: the successor is 10 (go right to 10, which has no left child). 10 is copied into the root, and the old 10 is replaced by its right child 14.

The **inorder predecessor** (the largest value on the left) works equally well. Always picking the successor tends to make long-lived trees lean left; some libraries alternate.

The script runs thousands of random inserts and deletes against a Python `set`, checking after each step that the inorder walk is the sorted set.

```python
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def search(node, key):
    while node is not None and node.val != key:
        node = node.left if key < node.val else node.right
    return node


def insert(node, key):
    """Insert key (ignored if present); return the subtree's root."""
    if node is None:
        return TreeNode(key)
    if key < node.val:
        node.left = insert(node.left, key)
    elif key > node.val:
        node.right = insert(node.right, key)
    return node


def delete(node, key):
    """Delete key if present; return the subtree's new root."""
    if node is None:
        return None
    if key < node.val:
        node.left = delete(node.left, key)
    elif key > node.val:
        node.right = delete(node.right, key)
    elif node.left is None:  # zero children or only a right child
        return node.right
    elif node.right is None:  # only a left child
        return node.left
    else:  # two children: copy the successor, then delete it on the right
        succ = node.right
        while succ.left is not None:
            succ = succ.left
        node.val = succ.val
        node.right = delete(node.right, succ.val)
    return node


def inorder(node):
    return [] if node is None else inorder(node.left) + [node.val] + inorder(node.right)


def main():
    root = None
    for v in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
        root = insert(root, v)
    assert search(root, 7).val == 7 and search(root, 5) is None
    root = delete(root, 3)
    assert root.left.val == 4 and root.left.right.left is None
    root = delete(root, 8)
    assert root.val == 10 and root.right.val == 14
    root = delete(root, 14)
    assert root.right.val == 13
    assert inorder(root) == [1, 4, 6, 7, 10, 13]
    assert delete(None, 5) is None and delete(TreeNode(5), 5) is None

    rng = random.Random(1)
    for _ in range(300):
        root, present = None, set()
        for _ in range(60):
            key = rng.randint(0, 30)
            if rng.random() < 0.6:
                root = insert(root, key)
                present.add(key)
            else:
                root = delete(root, key)
                present.discard(key)
            assert inorder(root) == sorted(present)
            assert (search(root, key) is not None) == (key in present)


if __name__ == "__main__":
    main()
```

**Time:** O(h) per operation. **Space:** O(h) for the recursion.

## 3. Validate a BST: the classic wrong check

**Problem.** Is a given binary tree a BST?

**The wrong check.** "At each node, the left child is smaller and the right child is larger." It accepts this tree:

```text
        8
       / \
      3   10
       \
        9
```

Every parent-child pair is fine (3 < 8, 10 > 8, 9 > 3), but 9 sits in the **left** subtree of 8 and is larger than 8. The property is about whole subtrees, not children.

**The fix: pass bounds down.** Each node must lie in an open interval `(low, high)` set by its ancestors. Going left, the current value becomes the new `high`; going right, it becomes the new `low`. This is the top-down pattern of [Recursion on Trees](02-recursion-on-trees.md#2-top-down-carrying-the-path).

| Node | Allowed `(low, high)` | OK? |
|---:|---|---|
| 8 | (−∞, ∞) | yes |
| 3 | (−∞, 8) | yes |
| 9 | (3, 8) | **no**: 9 ≥ 8 |
| 10 | (8, ∞) | yes |

**A second fix: inorder must increase strictly.** The inorder walk here is `3 9 8 10`: 9 then 8 goes down. Keep the previous value while walking; the iterative inorder can stop at the first descent.

Two details:

- **Duplicates.** This guide's BSTs hold distinct values, so the check is strict (`low < v < high`). If a problem allows duplicates on one side, change exactly one comparison to `≤` and say which side.
- **Bounds.** Use `-math.inf` and `math.inf`, not the smallest and largest integer of a fixed-width type; a node holding that exact value would be rejected.

The brute force compares each node with every value in its subtrees.

```python
import math
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, n, lo, hi):
    if n == 0:
        return None
    nodes = [TreeNode(rng.randint(lo, hi))]
    while len(nodes) < n:
        parent, side = rng.choice(nodes), rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            setattr(parent, side, TreeNode(rng.randint(lo, hi)))
            nodes.append(getattr(parent, side))
    return nodes[0]


def children_only_check(node):  # WRONG: compares with children only
    if node is None:
        return True
    if node.left and node.left.val >= node.val:
        return False
    if node.right and node.right.val <= node.val:
        return False
    return children_only_check(node.left) and children_only_check(node.right)


def is_bst(node, low=-math.inf, high=math.inf):
    if node is None:
        return True
    if not low < node.val < high:
        return False
    return is_bst(node.left, low, node.val) and is_bst(node.right, node.val, high)


def is_bst_inorder(root):
    prev, stack, curr = -math.inf, [], root
    while stack or curr:
        while curr:
            stack.append(curr)
            curr = curr.left
        node = stack.pop()
        if node.val <= prev:
            return False  # first descent
        prev, curr = node.val, node.right
    return True


def values(node):
    return [] if node is None else values(node.left) + [node.val] + values(node.right)


def is_bst_brute(node):
    if node is None:
        return True
    return (all(v < node.val for v in values(node.left))
            and all(v > node.val for v in values(node.right))
            and is_bst_brute(node.left) and is_bst_brute(node.right))


def main():
    T = TreeNode
    trap = T(8, T(3, None, T(9)), T(10))
    assert children_only_check(trap) and not is_bst(trap) and not is_bst_inorder(trap)
    good = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert is_bst(good) and is_bst_inorder(good)
    assert not is_bst(T(2, T(2))) and is_bst(None)

    rng = random.Random(2)
    found = 0
    for _ in range(3000):
        tree = random_tree(rng, rng.randint(0, 6), 0, 6)
        expected = is_bst_brute(tree)
        found += expected
        assert is_bst(tree) == is_bst_inorder(tree) == expected
    assert found > 100  # enough positive cases were tested


if __name__ == "__main__":
    main()
```

**Time:** O(n). **Space:** O(h).

## 4. Order queries: k-th smallest, successor, ranges

**Inorder is sorted.** By induction on the subtree: inorder lists the left subtree (sorted, all smaller), then the node, then the right subtree (sorted, all larger). The running tree gives `1 3 4 6 7 8 10 13 14`.

**k-th smallest (1-based).** Run the iterative inorder and stop at the `k`-th pop: O(h + k). If many queries arrive, store in each node the **size** of its subtree, and descend in O(h): with `L` the size of the left subtree, the answer is on the left if `k ≤ L`, is the node if `k = L + 1`, and is otherwise the `(k − L − 1)`-th of the right subtree. For `k = 7`: at 8, `L = 5`, so `k` becomes 7 − 6 = 1 and we go right; at 10, `L = 0` and `k = 1 = L + 1`, so the answer is 10. Sizes must be updated on every insert and delete; [Balanced Trees](06-balanced-trees.md) does that.

**Successor of `x`** (the smallest value greater than `x`, whether or not `x` is in the tree). Walk from the root. When `node.val > x`, the node is a candidate, and anything better is smaller, so remember it and go left. Otherwise go right. The last candidate is the answer.

| Successor of 7 | Successor of 14 |
|---|---|
| 8 > 7: candidate 8, go left | 8: go right |
| 3 ≤ 7: go right | 10: go right |
| 6 ≤ 7: go right | 14 ≤ 14: go right |
| 7 ≤ 7: go right → `None`; answer **8** | 13 is not visited; `None`: no successor |

The **predecessor** swaps the roles: candidate when `node.val < x`, then go right. **Ceiling** (smallest `≥ x`) and **floor** (largest `≤ x`) change `>` to `≥` or `<` to `≤`; these are `bisect_left`/`bisect_right` from [Boundaries](../01-binary-search/02-boundaries.md) on a tree.

**Range sum.** Sum the values in `[lo, hi]`. If `node.val < lo`, the whole left subtree is smaller too: skip it. If `node.val > hi`, skip the right subtree. For `[5, 12]`: 8 is in, search both sides; 3 is below, so only its right; 6 is in; 4 is below, and its right is empty; 7 is in; 10 is in; 14 is above, so only its left; 13 is above. Sum 6 + 7 + 8 + 10 = 31. Listing the `k` values in range costs O(h + k).

## 5. Building a balanced BST from sorted values

Given sorted values, make the middle one the root, then build the left half and the right half the same way. Each subtree gets half the values, so the height is ⌈log₂(n + 1)⌉: 4 for the nine values of the running tree.

```text
sorted: 1 3 4 6 [7] 8 10 13 14       root 7
left  : 1 [3] 4 6    right: 8 [10] 13 14      (middle = index len // 2)
```

## 6. Why height matters

Every operation costs O(h). Insert `1, 2, 3, …, n` in that order and each new value goes right of all the others: the tree is a chain, `h = n`, and the BST is a slow linked list. Sorted input is common in practice (timestamps, ids).

Inserting in **random** order gives an expected depth of about 2 ln n ≈ 1.39 log₂ n; the script measures it. But the input order is not ours to choose. [Balanced Trees](06-balanced-trees.md) keeps `h = O(log n)` whatever the order.

The script tests k-th, successor, predecessor, range sum and the balanced build against a sorted list with `bisect`, and measures heights.

```python
import bisect
import math
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None, size=1):
        self.val = val
        self.left = left
        self.right = right
        self.size = size  # nodes in this subtree


def size(node):
    return node.size if node else 0


def insert(node, key):
    """Iterative insert of a new distinct key; keeps sizes; returns the root."""
    new = TreeNode(key)
    if node is None:
        return new
    root, parent = node, None
    while node is not None:
        node.size += 1
        parent, node = node, (node.left if key < node.val else node.right)
    if key < parent.val:
        parent.left = new
    else:
        parent.right = new
    return root


def kth(node, k):
    """k-th smallest, 1-based."""
    if not 1 <= k <= size(node):
        raise ValueError("k out of range")
    while True:
        left = size(node.left)
        if k <= left:
            node = node.left
        elif k == left + 1:
            return node.val
        else:
            k -= left + 1
            node = node.right


def successor(node, x):
    best = None
    while node:
        if node.val > x:
            best, node = node.val, node.left
        else:
            node = node.right
    return best


def predecessor(node, x):
    best = None
    while node:
        if node.val < x:
            best, node = node.val, node.right
        else:
            node = node.left
    return best


def range_sum(node, lo, hi):
    if node is None:
        return 0
    if node.val < lo:
        return range_sum(node.right, lo, hi)
    if node.val > hi:
        return range_sum(node.left, lo, hi)
    return node.val + range_sum(node.left, lo, hi) + range_sum(node.right, lo, hi)


def from_sorted(values, lo=0, hi=None):
    """Balanced BST from values[lo:hi]."""
    if hi is None:
        hi = len(values)
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    left, right = from_sorted(values, lo, mid), from_sorted(values, mid + 1, hi)
    return TreeNode(values[mid], left, right, hi - lo)


def height(node):
    return 0 if node is None else 1 + max(height(node.left), height(node.right))


def inorder(node):
    return [] if node is None else inorder(node.left) + [node.val] + inorder(node.right)


def main():
    root = None
    for v in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
        root = insert(root, v)
    assert [kth(root, k) for k in range(1, 10)] == [1, 3, 4, 6, 7, 8, 10, 13, 14]
    assert successor(root, 7) == 8 and successor(root, 14) is None
    assert predecessor(root, 8) == 7 and predecessor(root, 1) is None
    assert range_sum(root, 5, 12) == 31
    balanced = from_sorted([1, 3, 4, 6, 7, 8, 10, 13, 14])
    assert balanced.val == 7 and height(balanced) == 4 and kth(balanced, 7) == 10

    rng = random.Random(3)
    for _ in range(300):
        keys = rng.sample(range(-20, 21), rng.randint(1, 15))
        root = None
        for key in keys:
            root = insert(root, key)
        s = sorted(keys)
        assert inorder(root) == s and size(root) == len(s)
        assert [kth(root, k) for k in range(1, len(s) + 1)] == s
        for x in range(-22, 23):
            i, j = bisect.bisect_right(s, x), bisect.bisect_left(s, x)
            assert successor(root, x) == (s[i] if i < len(s) else None)
            assert predecessor(root, x) == (s[j - 1] if j > 0 else None)
            lo, hi = sorted((x, rng.randint(-22, 22)))
            assert range_sum(root, lo, hi) == sum(v for v in s if lo <= v <= hi)
        b = from_sorted(s)
        assert inorder(b) == s and height(b) == math.ceil(math.log2(len(s) + 1))

    chain = None
    for v in range(500):
        chain = insert(chain, v)
    assert height(chain) == 500  # sorted inserts: a chain
    n = 2000
    keys = list(range(n))
    random.Random(4).shuffle(keys)
    shuffled = None
    for v in keys:
        shuffled = insert(shuffled, v)
    assert height(shuffled) < 4 * math.log2(n)  # random order: about log n


if __name__ == "__main__":
    main()
```

**Time:** O(h) for `kth`, `successor`, `predecessor`; O(h + k) for a range touching `k` values; O(n) for `from_sorted`. **Space:** O(1) for the loops, O(h) for the recursive ones.

## 7. Summary

| Operation | How | Cost |
|---|---|---|
| Search, insert | compare, go one side | O(h) |
| Delete, 0 or 1 child | return the child | O(h) |
| Delete, 2 children | copy the inorder successor, delete it from the right subtree | O(h) |
| Validate | bounds `(low, high)` passed down, or strictly increasing inorder | O(n) |
| Sorted output | inorder | O(n) |
| k-th smallest | inorder and stop, or subtree sizes | O(h + k), or O(h) |
| Successor, floor, ceiling | walk down, remember the last candidate | O(h) |
| Range `[lo, hi]` | skip subtrees entirely out of range | O(h + k) |
| From sorted values | middle as root, recurse | O(n), height ⌈log₂(n + 1)⌉ |

`h` is between log₂ n and n. A plain BST has no control over it; that is the job of [Balanced Trees](06-balanced-trees.md).

## 8. Pitfalls and practice

1. **Forgetting to use the returned root** after insert or delete (`node.left = delete(node.left, key)`) (§2).
2. **Deleting a two-child node by attaching one subtree under the other.** Correct but it can double the height; use the successor (§2).
3. **Validating with children only** (§3).
4. **Integer sentinels as bounds**, or `≤` vs `<` mixed up with duplicates (§3).
5. **Assuming O(log n).** Sorted inserts make a chain (§6).

Practice: search in a binary search tree; insert into a BST; delete node in a BST; validate binary search tree; kth smallest element in a BST; inorder successor in BST; range sum of BST; convert sorted array to binary search tree; convert sorted list to BST; two sum IV (input is a BST); minimum absolute difference in BST; trim a BST; BST iterator.

Next: [Construction, Paths and LCA](04-construction-paths-and-lca.md).
