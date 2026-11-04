# Construction, Paths and LCA — Rebuilding Trees and Asking About Paths

## 1. Rebuild a tree from two traversals

**Problem.** You are given the preorder and the inorder of a tree with distinct values. Rebuild it. For the running tree from [Binary Trees and Traversals](01-binary-trees-and-traversals.md):

```text
preorder: 8 3 1 6 4 7 10 14 13
inorder : 1 3 4 6 7 8 10 13 14

              8
            /   \
           3     10
          / \      \
         1   6      14
            / \     /
           4   7   13
```

**The key observation.** Preorder starts with the root. Inorder puts the root **between** its left and right subtrees. So the root's position in the inorder tells the size of each subtree:

- `preorder[0] = 8` is the root. 8 sits at index 5 of the inorder.
- So `inorder[0:5] = 1 3 4 6 7` is the left subtree, and `inorder[6:9] = 10 13 14` is the right.
- In preorder, the root is followed by the whole left subtree, then the whole right subtree. Recurse on each.

Slicing lists costs O(n) per call. Two changes make the whole build O(n): a dictionary from value to inorder index, and a single pointer `i` that walks through the preorder. Each call takes `preorder[i]` as its root, builds the left subtree (which consumes exactly the left part of the preorder), then the right.

| `preorder[i]` | Inorder range `[lo, hi)` | Root's inorder index | Left range | Right range |
|---:|---|---:|---|---|
| 8 | [0, 9) | 5 | [0, 5) | [6, 9) |
| 3 | [0, 5) | 1 | [0, 1) | [2, 5) |
| 1 | [0, 1) | 0 | empty | empty |
| 6 | [2, 5) | 3 | [2, 3) | [4, 5) |
| 4, 7 | one value each | — | empty | empty |
| 10 | [6, 9) | 6 | empty | [7, 9) |
| 14 | [7, 9) | 8 | [7, 8) | empty |
| 13 | [7, 8) | 7 | empty | empty |

An empty range returns `None` without consuming a preorder value. That is how 10 gets no left child.

**Postorder + inorder.** Postorder ends with the root. Walk the postorder **backwards** and build the **right** subtree before the left, since reversed postorder is *root, right, left*.

**Preorder + postorder is not enough.** Both trees below have preorder `1 2` and postorder `2 1`: the two orders can't tell whether 2 is a left or a right child. Only inorder separates the sides. (If every node has 0 or 2 children, preorder and postorder do determine the tree.)

```text
  1        1
 /          \
2            2
```

**Duplicates break it too.** With inorder `1 1`, the root 1 could sit at either index.

## 2. Serialize and deserialize

**Problem.** Turn a tree into a string and back, for any values, duplicates included.

Two traversals were needed above because a plain preorder doesn't say where a subtree ends. Fix that by writing a marker `#` for every `None`. Then preorder alone is enough:

```text
8,3,1,#,#,6,4,#,#,7,#,#,10,#,14,13,#,#,#
```

Reading it back is the same recursion as writing: take the next token; `#` means `None`; otherwise make a node, read its left subtree, then its right. The markers tell each call exactly where its subtree stops, so no sizes or searches are needed. A tree with `n` nodes writes `n` values and `n + 1` markers (every node has two child slots, and `n − 1` of them are filled).

The level-order list of [chapter 1](01-binary-trees-and-traversals.md#1-a-tree-given-as-a-list) is another valid format, and it has no recursion depth problem. Any format works as long as it records the empty slots.

```python
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, values):
    """A random shape holding the given values (one node each)."""
    if not values:
        return None
    nodes = [TreeNode(values[0])]
    for v in values[1:]:
        while True:
            parent, side = rng.choice(nodes), rng.choice(("left", "right"))
            if getattr(parent, side) is None:
                setattr(parent, side, TreeNode(v))
                nodes.append(getattr(parent, side))
                break
    return nodes[0]


def order(node, kind):
    if node is None:
        return []
    left, right = order(node.left, kind), order(node.right, kind)
    return {"pre": [node.val] + left + right, "in": left + [node.val] + right,
            "post": left + right + [node.val]}[kind]


def from_pre_in(preorder, inorder):
    if sorted(preorder) != sorted(inorder) or len(set(inorder)) != len(inorder):
        raise ValueError("need two orders of the same distinct values")
    where = {v: k for k, v in enumerate(inorder)}
    i = 0

    def build(lo, hi):  # the subtree whose inorder is inorder[lo:hi]
        nonlocal i
        if lo >= hi:
            return None
        root = TreeNode(preorder[i])
        i += 1
        mid = where[root.val]
        root.left = build(lo, mid)  # consumes the left part of preorder
        root.right = build(mid + 1, hi)
        return root

    return build(0, len(inorder))


def from_post_in(postorder, inorder):
    where = {v: k for k, v in enumerate(inorder)}
    i = len(postorder) - 1

    def build(lo, hi):
        nonlocal i
        if lo >= hi:
            return None
        root = TreeNode(postorder[i])
        i -= 1
        mid = where[root.val]
        root.right = build(mid + 1, hi)  # reversed postorder: root, right, left
        root.left = build(lo, mid)
        return root

    return build(0, len(inorder))


def serialize(root):
    out = []

    def go(node):
        if node is None:
            out.append("#")
            return
        out.append(str(node.val))
        go(node.left)
        go(node.right)

    go(root)
    return ",".join(out)


def deserialize(text):
    tokens = iter(text.split(","))

    def go():
        token = next(tokens)
        if token == "#":
            return None
        node = TreeNode(int(token))
        node.left = go()
        node.right = go()
        return node

    return go()


def main():
    pre = [8, 3, 1, 6, 4, 7, 10, 14, 13]
    ino = [1, 3, 4, 6, 7, 8, 10, 13, 14]
    root = from_pre_in(pre, ino)
    text = serialize(root)
    assert text == "8,3,1,#,#,6,4,#,#,7,#,#,10,#,14,13,#,#,#"
    assert serialize(from_post_in(order(root, "post"), ino)) == text
    assert serialize(deserialize(text)) == text and deserialize("#") is None
    a, b = TreeNode(1, TreeNode(2)), TreeNode(1, None, TreeNode(2))
    assert order(a, "pre") == order(b, "pre") and order(a, "post") == order(b, "post")
    try:
        from_pre_in([1, 1], [1, 1])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(1)
    for _ in range(500):
        values = rng.sample(range(100), rng.randint(0, 15))
        tree = random_tree(rng, values)
        text = serialize(tree)
        assert serialize(from_pre_in(order(tree, "pre"), order(tree, "in"))) == text
        assert serialize(from_post_in(order(tree, "post"), order(tree, "in"))) == text
        dup = random_tree(rng, [rng.randint(-3, 3) for _ in values])  # duplicates
        assert serialize(deserialize(serialize(dup))) == serialize(dup)


if __name__ == "__main__":
    main()
```

**Time:** O(n) for each function. **Space:** O(n) for the dictionary and the string, O(h) for the recursion.

## 3. Lowest common ancestor

**Problem.** The **lowest common ancestor** (LCA) of nodes `p` and `q` is the deepest node that has both in its subtree. A node is in its own subtree, so it can be its own ancestor. In the running tree, `LCA(4, 7) = 6`, `LCA(4, 13) = 8`, and `LCA(6, 4) = 6`.

**Brute force.** Record each node's parent with one traversal. Collect all ancestors of `p` in a set, then climb from `q` until reaching one of them. O(n) per query, plus O(n) memory.

**One bottom-up pass.** Let `f(node)` return:

- `None` if neither `p` nor `q` is in the subtree of `node`;
- `node` itself if `node` is `p` or `q`;
- otherwise, whatever the children report, combined like this: if **both** children return something, `p` and `q` are on different sides and `node` is the LCA; if only one does, pass that one up.

The middle rule stops the search early: if `node` is `p`, either `q` is below it (and then `p` is the LCA) or `q` is elsewhere (and then some ancestor will see `p` from one side and `q` from the other).

| Query | Node | Left returns | Right returns | Returns |
|---|---:|---|---|---|
| (4, 13) | 6 | 4 | `None` | 4 |
| | 3 | `None` (from 1) | 4 | 4 |
| | 14 | 13 | `None` | 13 |
| | 10 | `None` | 13 | 13 |
| | 8 | 4 | 13 | **8**, both sides |
| (6, 4) | 6 | — | — | **6**, without looking below |

**The assumption.** The function assumes both nodes are in the tree. If `q` is missing, `LCA(6, q)` still returns 6. When nodes may be absent, count how many of `p` and `q` were seen during the same pass (do not stop early at `p`), and return `None` unless the count is 2.

**In a BST**, values point the way. Start at the root: if both values are smaller, go left; if both are larger, go right; otherwise they split here (or one of them is here), so this node is the LCA. For (4, 7): 8, both smaller, go left; 3, both larger, go right; 6 splits them. O(h) and no recursion.

For thousands of LCA queries on a large tree, binary lifting answers each in O(log n) after O(n log n) preprocessing: [Rooting a Tree and LCA](../10-graphs/05-trees-and-advanced/01-rooting-and-lca.md).

```python
import random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, n):
    nodes = [TreeNode(0)]
    while len(nodes) < n:
        parent, side = rng.choice(nodes), rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            setattr(parent, side, TreeNode(len(nodes)))
            nodes.append(getattr(parent, side))
    return nodes[0], nodes


def lca(node, p, q):
    if node is None or node is p or node is q:
        return node
    left, right = lca(node.left, p, q), lca(node.right, p, q)
    if left and right:
        return node  # p and q on different sides
    return left or right


def lca_bst(root, a, b):
    node = root
    while node:
        if a < node.val and b < node.val:
            node = node.left
        elif a > node.val and b > node.val:
            node = node.right
        else:
            return node
    raise ValueError("values not in the tree")


def lca_brute(root, p, q):
    parent, stack = {root: None}, [root]
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child:
                parent[child] = node
                stack.append(child)
    ancestors = set()
    while p:
        ancestors.add(p)
        p = parent[p]
    while q not in ancestors:
        q = parent[q]
    return q


def bst_insert(node, key):
    if node is None:
        return TreeNode(key)
    if key < node.val:
        node.left = bst_insert(node.left, key)
    else:
        node.right = bst_insert(node.right, key)
    return node


def find(node, val):
    while node.val != val:
        node = node.left if val < node.val else node.right
    return node


def main():
    root = None
    for v in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
        root = bst_insert(root, v)
    n4, n7, n13, n6 = (find(root, v) for v in (4, 7, 13, 6))
    assert lca(root, n4, n7).val == 6 and lca(root, n4, n13).val == 8
    assert lca(root, n6, n4).val == 6
    assert lca_bst(root, 4, 7).val == 6 and lca_bst(root, 13, 4).val == 8
    assert lca_bst(root, 6, 4).val == 6

    rng = random.Random(2)
    for _ in range(300):
        tree, nodes = random_tree(rng, rng.randint(1, 20))
        for _ in range(10):
            p, q = rng.choice(nodes), rng.choice(nodes)
            assert lca(tree, p, q) is lca_brute(tree, p, q)
        keys = rng.sample(range(50), rng.randint(1, 15))
        bst = None
        for k in keys:
            bst = bst_insert(bst, k)
        a, b = rng.choice(keys), rng.choice(keys)
        assert lca_bst(bst, a, b) is lca_brute(bst, find(bst, a), find(bst, b))


if __name__ == "__main__":
    main()
```

**Time:** O(n) for `lca`, O(h) for `lca_bst`. **Space:** O(h).

## 4. Counting downward paths with a given sum

**Problem.** Count the paths that go **downward** (from a node to one of its descendants, any start, any end) whose values sum to `target`. In the running tree with `target = 13` there are three: 3 + 6 + 4, 6 + 7, and 13 alone.

**Brute force.** From every node, walk down every path and count the sums that hit `target`. Each node starts walks that reach its whole subtree: O(n·h), O(n²) on a chain.

**The key observation.** This is [prefix sums](../04-range-queries/01-prefix-sums.md) on the path from the root. Let `P(v)` be the sum from the root down to `v`. A downward path that starts right below an ancestor `a` to `v` sums to `P(v) − P(a)`. So the number of good paths ending at `v` is the number of ancestors `a` (or the empty prefix, value 0) with `P(a) = P(v) − target`.

Keep a counter of the prefix sums **on the current root path**. Entering `v`: count `P(v) − target` in it, then add `P(v)`. Leaving `v`: remove `P(v)`. The counter starts as `{0: 1}` so that paths starting at the root count.

| Node | `P(v)` | Look for `P(v) − 13` | Found | Counter after adding `P(v)` |
|---:|---:|---:|---:|---|
| 8 | 8 | −5 | 0 | 0, 8 |
| 3 | 11 | −2 | 0 | 0, 8, 11 |
| 1 | 12 | −1 | 0 | (12 added, removed on leaving) |
| 6 | 17 | 4 | 0 | 0, 8, 11, 17 |
| 4 | 21 | 8 | 1 (3 + 6 + 4) | … |
| 7 | 24 | 11 | 1 (6 + 7) | … |
| 10 | 18 | 5 | 0 | 0, 8, 18 |
| 14 | 32 | 19 | 0 | 0, 8, 18, 32 |
| 13 | 45 | 32 | 1 (13) | … |

**The trap: forgetting to remove.** Without the removal, prefix sums from a finished subtree stay in the counter and pair with nodes in a **sibling** subtree, which is not a downward path. The smallest failing case: root 1 with children 2 and 3, `target = 1`. The answer is 1 (the root alone). At node 3, `P = 4` and `4 − 1 = 3` is the prefix of the sibling 2, so the buggy version answers 2.

## 5. Views: what you see from the side and from below

**Right side view.** Looking at the tree from the right, you see the last node of each level: `8, 10, 14, 13`. The level order of chapter 1 gives it. A depth-first version visits the **right** child first and records a node when its depth equals the number of values recorded so far; that node is the first one reached at its depth.

**Vertical order.** Give the root column 0; a left child has its parent's column − 1, a right child + 1. List the columns left to right, each from top to bottom; nodes in the same column **and** row are sorted by value.

```text
column:   -2   -1    0    1    2
row 0                8
row 1          3          10
row 2     1          6          14
row 3          4          7
                          13          (13 is also row 3, column 1)
```

Result: `[1], [3, 4], [8, 6], [10, 7, 13], [14]`. The tie is in column 1, row 3: 7 (from 6, a right step) and 13 (from 14, a left step) share a cell, so value order decides. A plain BFS order would also give 7 before 13 here, but it breaks ties by position, not by value; collect `(column, row, value)` triples and sort them.

```python
import random
from collections import Counter, defaultdict


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def random_tree(rng, n, lo=-5, hi=5):
    if n == 0:
        return None
    nodes = [TreeNode(rng.randint(lo, hi))]
    while len(nodes) < n:
        parent, side = rng.choice(nodes), rng.choice(("left", "right"))
        if getattr(parent, side) is None:
            setattr(parent, side, TreeNode(rng.randint(lo, hi)))
            nodes.append(getattr(parent, side))
    return nodes[0]


def path_sum_count(root, target, remove=True):
    seen = Counter({0: 1})  # prefix sums on the current root path
    count = 0

    def go(node, prefix):
        nonlocal count
        if node is None:
            return
        prefix += node.val
        count += seen[prefix - target]
        seen[prefix] += 1
        go(node.left, prefix)
        go(node.right, prefix)
        if remove:
            seen[prefix] -= 1  # leaving: no longer on the path

    go(root, 0)
    return count


def path_sum_brute(root, target):
    def down(node, need):  # paths starting at node
        if node is None:
            return 0
        need -= node.val
        return (need == 0) + down(node.left, need) + down(node.right, need)

    def every(node):
        if node is None:
            return 0
        return down(node, target) + every(node.left) + every(node.right)

    return every(root)


def right_view(root):
    out = []

    def go(node, depth):
        if node is None:
            return
        if depth == len(out):
            out.append(node.val)  # first node reached at this depth
        go(node.right, depth + 1)
        go(node.left, depth + 1)

    go(root, 0)
    return out


def right_view_brute(root):
    rows = []

    def go(node, depth):
        if node:
            if depth == len(rows):
                rows.append([])
            rows[depth].append(node.val)
            go(node.left, depth + 1)
            go(node.right, depth + 1)

    go(root, 0)
    return [row[-1] for row in rows]


def vertical_order(root):
    cells = []

    def go(node, row, col):
        if node:
            cells.append((col, row, node.val))
            go(node.left, row + 1, col - 1)
            go(node.right, row + 1, col + 1)

    go(root, 0, 0)
    columns = defaultdict(list)
    for col, row, val in sorted(cells):
        columns[col].append(val)
    return [columns[c] for c in sorted(columns)]


def main():
    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert path_sum_count(root, 13) == path_sum_brute(root, 13) == 3
    small = T(1, T(2), T(3))
    assert path_sum_count(small, 1) == 1
    assert path_sum_count(small, 1, remove=False) == 2  # the sibling bug
    assert right_view(root) == [8, 10, 14, 13]
    assert vertical_order(root) == [[1], [3, 4], [8, 6], [10, 7, 13], [14]]
    assert vertical_order(T(1, T(2, None, T(9)), T(3, T(5)))) == [[2], [1, 5, 9], [3]]

    rng = random.Random(3)
    for _ in range(500):
        tree = random_tree(rng, rng.randint(0, 15))
        for target in range(-6, 7):
            assert path_sum_count(tree, target) == path_sum_brute(tree, target)
        assert right_view(tree) == right_view_brute(tree)


if __name__ == "__main__":
    main()
```

**Time:** O(n) for path counting and the right view; O(n log n) for vertical order (the sort). **Space:** O(n).

## 6. Summary

| Problem | Key fact | Cost |
|---|---|---|
| Build from preorder + inorder | preorder gives the root, inorder splits the sides | O(n) with an index map and one pointer |
| Build from postorder + inorder | walk postorder backwards, right before left | O(n) |
| Preorder + postorder | ambiguous for one-child nodes | — |
| Serialize | preorder with a marker per `None` | O(n) |
| LCA, binary tree | return `p`/`q`/`None`; both sides non-empty means here | O(n), assumes both present |
| LCA, BST | walk down while both are on one side | O(h) |
| Downward paths summing to `k` | prefix sums on the root path, counter, remove on exit | O(n) |
| Right side view | first node per depth, right child first | O(n) |
| Vertical order | sort `(column, row, value)` | O(n log n) |

## 7. Pitfalls and practice

1. **Slicing in the rebuild.** O(n²) on a chain; use an index map and a pointer (§1).
2. **Building left before right from postorder** (§1).
3. **Rebuilding with duplicate values** from two traversals: ambiguous (§1).
4. **Calling LCA when a node may be missing** (§3).
5. **Not removing the prefix sum on exit** (§4).
6. **Breaking vertical-order ties by position instead of value** (§5).

Practice: construct binary tree from preorder and inorder traversal; construct from inorder and postorder; construct from preorder and postorder; construct BST from preorder traversal; serialize and deserialize binary tree; serialize and deserialize BST; lowest common ancestor of a binary tree (I to III); LCA of a BST; path sum III; binary tree right side view; vertical order traversal of a binary tree; all nodes distance K in binary tree.

Next: [Tries](05-tries.md).
