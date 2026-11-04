# Recursion on Trees — Decide What Each Call Returns

## 1. How deep is the tree?

The running tree from [Binary Trees and Traversals](01-binary-trees-and-traversals.md):

```text
              8
            /   \
           3     10
          / \      \
         1   6      14
            / \     /
           4   7   13
```

Its height is 4: the path 8 → 3 → 6 → 4 has four nodes. How does code find that?

Write down, in one sentence, what a call returns: **`height(node)` is the number of nodes on the longest downward path starting at `node`, and 0 for `None`.** Then the body follows from the sentence. A path down from `node` is `node` plus a path down from one child, so

$$\text{height}(v) = 1 + \max(\text{height}(v.\text{left}), \text{height}(v.\text{right})).$$

While writing the body, **trust the sentence for the children** instead of tracing into them. Each call only has to be right for its own node, given right answers from below. That is induction on the subtree size: true for `None`, and true for a node whenever it is true for its smaller subtrees.

The calls return in postorder, children first:

| Node | `height(left)` | `height(right)` | Returns |
|---:|---:|---:|---:|
| 1, 4, 7, 13 (leaves) | 0 | 0 | 1 |
| 6 | 1 | 1 | 2 |
| 3 | 1 | 2 | 3 |
| 14 | 1 | 0 | 2 |
| 10 | 0 | 2 | 3 |
| 8 | 3 | 3 | 4 |

Two families of tree recursion grow from here. **Bottom-up** calls return information up from the children, like `height`. **Top-down** calls pass information down as arguments, from the root toward the leaves. Many problems use both.

## 2. Top-down: carrying the path

**Problem.** Is there a root-to-leaf path whose values add up to `target`? In the example, `target = 21` is reached by 8 + 3 + 6 + 4. `target = 11` is not: 8 + 3 = 11, but 3 is not a leaf.

The question at a leaf depends on everything above it, so pass it down: **`has_path(node, remaining)` says whether some path from `node` down to a leaf sums to `remaining`.** Each call subtracts its own value and asks its children for the rest.

| Call | `remaining` on entry | After subtracting | Result |
|---|---:|---:|---|
| 8 | 21 | 13 | asks 3, then 10 |
| 3 | 13 | 10 | asks 1, then 6 |
| 1 (leaf) | 10 | 9 | not 0: false |
| 6 | 10 | 4 | asks 4 |
| 4 (leaf) | 4 | 0 | true; `or` stops the search |

The check happens **only at leaves**; checking `remaining == 0` at every node would accept 11. And a node with one child is not a leaf: for the tree `1 → 2` (only a left child), `target = 1` is false, because the only root-to-leaf path is 1 + 2.

Other top-down problems carry a different value down the same way. **Good nodes** (a node is good if no value above it on its path is larger) carry the path maximum. Top-down **max depth** carries the current depth and records the largest one seen at a leaf.

**Two trees at once.** The same shape works on pairs. `same(a, b)`: both `None`, or both present with equal values and `same(a.left, b.left)` and `same(a.right, b.right)`. A tree is **symmetric** when its left subtree mirrors its right one: `mirror(a, b)` compares `a.left` with `b.right` and `a.right` with `b.left`.

## 3. Bottom-up with a sentinel: is the tree balanced?

**Problem.** A tree is **height-balanced** when, at every node, the heights of the two subtrees differ by at most 1. Is the running tree balanced?

**Brute force.** At each node, call `height` on both children and compare, then recurse into both children. Each node's height is recomputed once per ancestor: O(n²) on a chain, O(n log n) on a bushy tree.

**The observation.** The postorder walk of §1 already computes every height once. Let one call return both answers, encoded in one number: **`check(node)` returns the height if the subtree is balanced, and −1 if it is not.** No real height is negative, so −1 can't be confused with an answer. Once a child returns −1, pass −1 up without more work.

| Node | Left returns | Right returns | Returns |
|---:|---:|---:|---|
| 1, 4, 7, 13 | 0 | 0 | 1 |
| 6 | 1 | 1 | 2 |
| 3 | 1 | 2 | 3 |
| 14 | 1 | 0 | 2 |
| 10 | 0 | 2 | differ by 2: −1 |
| 8 | 3 | −1 | −1 |

The running tree is **not** balanced: node 10 has an empty left side and a right side of height 2. Every subtree of 3 is fine.

```python
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, n, lo=-9, hi=9):
    if n == 0:
        return None
    nodes = [TreeNode(rng.randint(lo, hi))]
    while len(nodes) < n:
        parent, side = rng.choice(nodes), rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            setattr(parent, side, TreeNode(rng.randint(lo, hi)))
            nodes.append(getattr(parent, side))
    return nodes[0]


def height(node):
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def has_path(node, remaining):
    if node is None:
        return False
    remaining -= node.val
    if node.left is None and node.right is None:  # check only at a leaf
        return remaining == 0
    return has_path(node.left, remaining) or has_path(node.right, remaining)


def path_sums_brute(node, acc=0):
    """Every root-to-leaf sum."""
    if node is None:
        return []
    acc += node.val
    if node.left is None and node.right is None:
        return [acc]
    return path_sums_brute(node.left, acc) + path_sums_brute(node.right, acc)


def same(a, b):
    if a is None or b is None:
        return a is b
    return a.val == b.val and same(a.left, b.left) and same(a.right, b.right)


def symmetric(root):
    def mirror(a, b):
        if a is None or b is None:
            return a is b
        return a.val == b.val and mirror(a.left, b.right) and mirror(a.right, b.left)

    return root is None or mirror(root.left, root.right)


def is_balanced(root):
    def check(node):
        if node is None:
            return 0
        left = check(node.left)
        if left < 0:
            return -1
        right = check(node.right)
        if right < 0 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return check(root) >= 0


def mirror_copy(node):
    if node is None:
        return None
    return TreeNode(node.val, mirror_copy(node.right), mirror_copy(node.left))


def is_balanced_brute(node):
    if node is None:
        return True
    return (abs(height(node.left) - height(node.right)) <= 1
            and is_balanced_brute(node.left) and is_balanced_brute(node.right))


def main():
    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert height(root) == 4 and height(None) == 0
    assert has_path(root, 21) and has_path(root, 45)  # 8+3+6+4, 8+10+14+13
    assert not has_path(root, 11)  # 8 + 3 stops at a non-leaf
    assert not has_path(T(1, T(2)), 1) and not has_path(None, 0)
    assert not is_balanced(root) and is_balanced(root.left)
    assert same(root, T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13)))))
    assert symmetric(T(1, T(2, T(3)), T(2, None, T(3))))
    assert not symmetric(T(1, T(2, T(3)), T(2, T(3))))

    rng = random.Random(1)
    for _ in range(1000):
        tree = random_tree(rng, rng.randint(0, 14))
        sums = path_sums_brute(tree)
        for target in range(-20, 21):
            assert has_path(tree, target) == (target in sums)
        assert is_balanced(tree) == is_balanced_brute(tree)
        assert same(tree, tree) and symmetric(tree) == same(tree, mirror_copy(tree))


if __name__ == "__main__":
    main()
```

**Time:** O(n) for each function. **Space:** O(h) for the recursion.

## 4. Return one thing, record another: the diameter

**Problem.** The **diameter** of a tree is the number of edges on its longest path between any two nodes. The path may bend at a node and need not pass through the root. In the running tree it is 6: 4 – 6 – 3 – 8 – 10 – 14 – 13.

**The observation.** Every path has one highest node, where it bends. A path bending at `v` goes down the left side as far as it can and down the right side as far as it can, so its length is `height(v.left) + height(v.right)` edges (each height counts nodes, and each node below `v` adds one edge). The diameter is the largest of these over all `v`.

**The trap.** The function wants to return the diameter, but the parent can't use a child's diameter: a parent can extend only a path that **ends** at the child, not one that bends there. So the recursion **returns** the height (what the parent can extend) and **records** the bent path in a separate variable `best` (what the problem asks for). Mixing the two is the usual bug.

| Node | Left height | Right height | Bent path `l + r` | `best` | Returns `1 + max` |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 1 |
| 4, 7 | 0 | 0 | 0 | 0 | 1 |
| 6 | 1 | 1 | 2 | 2 | 2 |
| 3 | 1 | 2 | 3 | 3 | 3 |
| 13 | 0 | 0 | 0 | 3 | 1 |
| 14 | 1 | 0 | 1 | 3 | 2 |
| 10 | 0 | 2 | 2 | 3 | 3 |
| 8 | 3 | 3 | **6** | 6 | 4 |

`best` can live in a `nonlocal` variable of an enclosing function, or each call can return the pair `(height, best inside this subtree)` and combine `best = max(left_best, right_best, l + r)`. The pair keeps the function pure and testable on its own; the `nonlocal` version is shorter. The script has both.

## 5. Variant: maximum path sum, where branches can hurt

**Problem.** Values may be negative. Find the largest sum of values on any path (at least one node). For

```text
       -10
       /  \
      9    20
          /  \
         15   7
```

the answer is 42, the path 15 – 20 – 7, which avoids the root.

Same split as the diameter: **return** the best sum of a path that starts at `v` and goes **down one side** (the parent can extend it), **record** the best path that bends at `v`. Two changes:

1. **A negative branch is dropped.** If the best downward path from a child sums to −5, the path is better off stopping at `v`. Use `max(0, gain(child))`.
2. **`best` starts at `−∞`, not 0.** The path must contain a node. For the one-node tree `[-3]` the answer is −3; starting at 0 reports a path that doesn't exist.

| Node | Left gain (clamped) | Right gain (clamped) | Bent path | `best` | Returns `v + max(l, r)` |
|---:|---:|---:|---:|---:|---:|
| 9 | 0 | 0 | 9 | 9 | 9 |
| 15 | 0 | 0 | 15 | 15 | 15 |
| 7 | 0 | 0 | 7 | 15 | 7 |
| 20 | 15 | 7 | 42 | 42 | 35 |
| −10 | 9 | 35 | 34 | 42 | 25 |

The root returns 25, which is not the answer; the answer is `best`. For the tree `2` with left child `−1`, the gain from −1 is clamped to 0 and the answer is 2.

The brute force in the script tries every pair of nodes `(u, v)`, walks the unique path between them using parent pointers, and takes the largest sum and the longest length.

```python
import math
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, n, lo=-9, hi=9):
    if n == 0:
        return None
    nodes = [TreeNode(rng.randint(lo, hi))]
    while len(nodes) < n:
        parent, side = rng.choice(nodes), rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            setattr(parent, side, TreeNode(rng.randint(lo, hi)))
            nodes.append(getattr(parent, side))
    return nodes[0]


def diameter(root):
    best = 0

    def height(node):
        nonlocal best
        if node is None:
            return 0
        l, r = height(node.left), height(node.right)
        best = max(best, l + r)  # record: the path bending here
        return 1 + max(l, r)  # return: what the parent can extend

    height(root)
    return best


def diameter_pair(root):
    def go(node):  # (height, best path length inside this subtree)
        if node is None:
            return 0, 0
        lh, lb = go(node.left)
        rh, rb = go(node.right)
        return 1 + max(lh, rh), max(lb, rb, lh + rh)

    return go(root)[1]


def max_path_sum(root):
    if root is None:
        raise ValueError("a path needs at least one node")
    best = -math.inf

    def gain(node):
        nonlocal best
        if node is None:
            return 0
        l = max(0, gain(node.left))  # drop a branch that hurts
        r = max(0, gain(node.right))
        best = max(best, node.val + l + r)
        return node.val + max(l, r)

    gain(root)
    return best


def paths_brute(root):
    """(largest path sum, most edges) over all pairs of nodes."""
    parent, depth, nodes = {root: None}, {root: 0}, [root]
    for node in nodes:  # grows while we iterate: a BFS
        for child in (node.left, node.right):
            if child:
                parent[child], depth[child] = node, depth[node] + 1
                nodes.append(child)
    best_sum, best_len = -math.inf, 0
    for u in nodes:
        for v in nodes:
            a, b, total, length = u, v, 0, 0
            while a is not b:
                if depth[a] < depth[b]:
                    a, b = b, a
                total += a.val
                a, length = parent[a], length + 1
            total += a.val  # the bend node
            best_sum, best_len = max(best_sum, total), max(best_len, length)
    return best_sum, best_len


def main():
    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert diameter(root) == diameter_pair(root) == 6
    assert diameter(None) == 0 and diameter(T(1)) == 0
    assert max_path_sum(T(-10, T(9), T(20, T(15), T(7)))) == 42
    assert max_path_sum(T(-3)) == -3
    assert max_path_sum(T(2, T(-1))) == 2
    assert max_path_sum(T(-2, T(-1))) == -1

    rng = random.Random(2)
    for _ in range(500):
        tree = random_tree(rng, rng.randint(1, 12))
        best_sum, best_len = paths_brute(tree)
        assert max_path_sum(tree) == best_sum
        assert diameter(tree) == diameter_pair(tree) == best_len


if __name__ == "__main__":
    main()
```

**Time:** O(n). **Space:** O(h).

The same "return one, record another" split solves longest univalue path, binary tree cameras and house robber III; the last is worked in [Tree and DAG DP](../09-dynamic-programming/08-tree-and-dag-dp.md). For a tree given as an edge list with no root, see [Tree Diameter and Centers](../10-graphs/05-trees-and-advanced/02-tree-diameter.md).

## 6. Variant: when the recursion is too deep

The smallest failing example: a chain of 5000 nodes, each the left child of the next. `height` on it raises `RecursionError`, because CPython's default limit is 1000 frames.

**The rule.** Recursion depth equals tree height, and input trees can be chains. `sys.setrecursionlimit` raises the limit but not the real C stack, so very deep inputs can still crash the interpreter.

**The fix.** Get a postorder with an explicit stack ([§3 of the traversal chapter](01-binary-trees-and-traversals.md#3-the-same-orders-with-an-explicit-stack)) and store each node's return value in a dictionary. When a node is handled, its children's values are already there.

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def height_recursive(node):
    return 0 if node is None else 1 + max(height_recursive(node.left), height_recursive(node.right))


def diameter_iterative(root):
    """Diameter in edges, with no recursion at all."""
    h = {None: 0}  # node -> height
    best = 0
    stack = [(root, False)]
    while stack:
        node, ready = stack.pop()
        if node is None:
            continue
        if not ready:
            stack += [(node, True), (node.right, False), (node.left, False)]
            continue
        l, r = h[node.left], h[node.right]  # children are done
        best = max(best, l + r)
        h[node] = 1 + max(l, r)
    return best


def main():
    deep = None
    for v in range(5000):
        deep = TreeNode(v, deep)
    try:
        height_recursive(deep)
        raise AssertionError("expected RecursionError")
    except RecursionError:
        pass
    assert diameter_iterative(deep) == 4999

    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert diameter_iterative(root) == 6
    assert diameter_iterative(None) == 0


if __name__ == "__main__":
    main()
```

## 7. Summary

| Kind | Information flows | Signature | Examples |
|---|---|---|---|
| Top-down | root → leaves, as arguments | `go(node, state_from_above)` | path sum, good nodes, top-down depth |
| Bottom-up | leaves → root, as return values | `go(node) -> summary of subtree` | height, size, balanced, LCA |
| Return + record | up, plus a global best | returns what the parent can extend, records what the problem asks | diameter, max path sum, longest univalue path |
| Two trees | in lockstep | `go(a, b)` | same tree, symmetric, subtree of another |

Before writing any tree recursion, write the sentence "**`f(node)` returns … for the subtree of `node`, and … for `None`**". Then check:

1. Can the parent build its answer from the children's answers? If not, return more (a pair, a sentinel).
2. Is the returned value the same as the asked value? If not, record the asked value separately.
3. Can the tree be a chain of thousands of nodes? If so, use an explicit stack.

## 8. Pitfalls and practice

1. **Checking a path condition at a non-leaf**, or treating a one-child node as a leaf (§2).
2. **Recomputing heights inside the recursion.** O(n²) on a chain; return both answers in one pass (§3).
3. **Returning the bent path to the parent.** The parent can only extend a one-sided path (§4).
4. **`best = 0` with negative values**, and forgetting to clamp negative gains (§5).
5. **Deep recursion on chain-shaped input** (§6).

Practice: maximum depth of binary tree; path sum I and II; count good nodes in binary tree; same tree; symmetric tree; invert binary tree; subtree of another tree; balanced binary tree; diameter of binary tree; binary tree maximum path sum; longest univalue path; sum root to leaf numbers.

Next: [Binary Search Trees](03-binary-search-trees.md).
