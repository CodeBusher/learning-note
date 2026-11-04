# Binary Trees and Traversals — Building a Tree and Visiting Every Node

## 1. A tree given as a list

Tree problems usually hand you a tree as a list such as `[8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13]`. It describes this tree, which runs through the whole folder:

```text
              8
            /   \
           3     10
          / \      \
         1   6      14
            / \     /
           4   7   13
```

- A **binary tree** is made of **nodes**. Each node holds a value and two pointers, `left` and `right`, to its **children**; a missing child is `None`. The class is `ListNode` from [Nodes and Pointers](../02-linked-lists/01-nodes-and-pointers.md) with two pointers instead of one.
- The **root** (8) is the top node. Every other node has one **parent**. A **leaf** has no children (1, 4, 7, 13).
- The **subtree** of a node is the node and everything below it: the subtree of 6 is `{6, 4, 7}`.
- The **depth** of a node counts edges from the root (8 has depth 0, 4 has depth 3). Nodes of equal depth form a **level**.
- The **height** of a tree, in this folder, counts the nodes on the longest root-to-leaf path: 4 here, 1 for one node, 0 for the empty tree. Some books count edges, one less.

### Reading the list

The list is the tree read level by level, left to right. The rule that trips people: **a `None` gets no children of its own in the list.** After the two `None`s of node 1, the next two values belong to 6, not to the missing left child of 10.

So the builder keeps a queue of nodes waiting for children: take the front node, give it the next two values, and put each real child at the back.

| Node taken | Next two values | Queue after |
|---:|---|---|
| 8 | 3, 10 | 3, 10 |
| 3 | 1, 6 | 10, 1, 6 |
| 10 | None, 14 | 1, 6, 14 |
| 1 | None, None | 6, 14 |
| 6 | 4, 7 | 14, 4, 7 |
| 14 | 13, (end) | 4, 7, 13 |

The list ran out, so 4, 7 and 13 stay leaves. This is **not** the heap layout, where index `i` has children `2i + 1` and `2i + 2` ([What a Heap Is](../07-heaps-and-priority-queues/01-what-a-heap-is.md)): that layout reserves slots for missing nodes, so a long chain would need an exponentially long list.

`to_level_list` reverses the process; building and writing back must give the same list on random trees. `random_tree` hangs each new node on a random free slot. Later scripts repeat these helpers so each runs on its own.

```python
import random
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build(values):
    """Build a tree from a level-order list with None for missing children."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        for side in ("left", "right"):
            if i < len(values) and values[i] is not None:
                child = TreeNode(values[i])
                setattr(node, side, child)
                queue.append(child)
            i += 1
    return root


def to_level_list(root):
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        out.append(None if node is None else node.val)
        if node is not None:
            queue += [node.left, node.right]
    while out and out[-1] is None:
        out.pop()
    return out


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


def main():
    example = [8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13]
    root = build(example)
    assert root.right.left is None and root.right.right.left.val == 13
    assert root.left.right.left.val == 4
    assert to_level_list(root) == example
    assert build([]) is None and to_level_list(None) == []
    assert to_level_list(build([1, None, 2, None, 3])) == [1, None, 2, None, 3]

    rng = random.Random(1)
    for _ in range(500):
        values = to_level_list(random_tree(rng, rng.randint(0, 15)))
        assert to_level_list(build(values)) == values


if __name__ == "__main__":
    main()
```

**Time:** O(n) for `n` nodes. **Space:** O(w), the widest level, for the queue.

## 2. Depth-first orders: where the visit goes

To **traverse** a tree is to visit every node once. A depth-first traversal goes down one side as far as it can before backing up. Recursively it is three lines: recurse left, recurse right, and visit the node. The only choice is where the visit goes:

| Order | Visit the node | Example tree |
|---|---|---|
| **Preorder** | before both subtrees | 8 3 1 6 4 7 10 14 13 |
| **Inorder** | between the subtrees | 1 3 4 6 7 8 10 13 14 |
| **Postorder** | after both subtrees | 1 4 7 6 3 13 14 10 8 |

One walk produces all three. Trace the outline of the tree with a pencil, starting above the root, keeping the tree on your right. You pass each node three times: going down (pass 1), back up from its left subtree (pass 2), back up from its right subtree (pass 3). That is exactly the recursive call: the call, the return from `left`, the return from `right`.

```text
node:   8  3  1  1  1  3  6  4  4  4  6  7  7  7  6  3  8 10 10 14 13 13 13 14 14 10  8
pass:   1  1  1  2  3  2  1  1  2  3  2  1  2  3  3  3  2  1  2  1  1  2  3  2  3  3  3
```

Keep the pass-1 entries: preorder. Pass 2: inorder. Pass 3: postorder. What each order is for follows from what has been seen at visit time:

- **Preorder** reaches a parent before its descendants: copy or serialize a tree, pass values down from the root.
- **Inorder** puts the left subtree before the node and the right subtree after. In a binary search tree that is sorted order; the example is one ([Binary Search Trees](03-binary-search-trees.md)).
- **Postorder** reaches a node after both subtrees: anything computed from the children's answers, such as height or size ([Recursion on Trees](02-recursion-on-trees.md)).

## 3. The same orders with an explicit stack

Python stops at about 1000 nested calls, and a chain of 5000 nodes is 5000 deep. Our own stack (a list with `append` and `pop`) has no limit.

**Preorder.** Pop a node, visit it, push its children. The stack returns the last thing pushed, so push **right before left**: popping 8 pushes 10 then 3, and 3 comes out next.

**Inorder** is where iterative code goes wrong, because a node can't be visited when first reached. The stack holds the nodes whose left side is in progress:

1. From `curr`, walk left as far as possible, pushing every node.
2. Pop the top; its left subtree is done, so visit it.
3. Set `curr` to its right child. Loop while the stack is non-empty **or** `curr` is not `None`.

| Pushed going left | Pop, visit | `curr` becomes | Stack after (top right) |
|---|---:|---|---|
| 8, 3, 1 | 1 | `None` | 8 3 |
| — | 3 | 6 | 8 |
| 6, 4 | 4 | `None` | 8 6 |
| — | 6 | 7 | 8 |
| 7 | 7 | `None` | 8 |
| — | 8 | 10 | (empty) |
| 10 | 10 | 14 | (empty) |
| 14, 13 | 13 | `None` | 14 |
| — | 14 | `None` | (empty) |

After visiting 8 the stack is empty but `curr` is 10. A loop testing only the stack stops there and loses the right half of the tree.

**Postorder, and one template for all three.** A node must wait for both subtrees. Push pairs `(node, ready)`: `ready = False` means "expand", `True` means "visit now". To expand, push the three parts in the **reverse** of the order you want them handled. Postorder wants left, right, node, so push `(node, True)`, then right, then left. On the subtree of 3:

| Pop | Stack after (top right) | Output |
|---|---|---|
| (3,F): expand | (3,T) (6,F) (1,F) | |
| (1,F) expand, (1,T) visit | (3,T) (6,F) | 1 |
| (6,F): expand | (3,T) (6,T) (7,F) (4,F) | 1 |
| (4,F), (4,T), (7,F), (7,T) | (3,T) (6,T) | 1 4 7 |
| (6,T), (3,T) | (empty) | 1 4 7 6 3 |

Inorder pushes `right, (node, True), left`; preorder pushes `right, left, (node, True)`. A second postorder trick: preorder with the children swapped gives *node, right, left*; reversed, that is *left, right, node*.

## 4. Advanced: Morris inorder in O(1) extra space

The stack exists to get back to a node after its left subtree. The node visited right before `curr` in inorder is its **predecessor**, the rightmost node of `curr`'s left subtree, and that node's `right` is `None`. Point it at `curr` for a while (a **thread**) and the walk can return without a stack.

At each `curr`: with no left child, visit and go right (possibly along a thread). Otherwise find the predecessor `p`, walking right while `p.right` is neither `None` nor `curr`. If `p.right is None`, this is the first arrival: set the thread and go left. If `p.right is curr`, the left subtree is done: remove the thread, visit, go right. On the subtree of 3:

| `curr` | Predecessor `p` | Action | Output |
|---:|---|---|---|
| 3 | 1, right is `None` | thread 1 → 3, go left | |
| 1 | — (no left child) | visit, follow thread to 3 | 1 |
| 3 | 1, right is 3 | remove thread, visit, go right | 1 3 |
| 6 | 4, right is `None` | thread 4 → 6, go left | 1 3 |
| 4 | — | visit, follow thread to 6 | 1 3 4 |
| 6 | 4, right is 6 | remove thread, visit, go right | 1 3 4 6 |
| 7 | — | visit, go right | 1 3 4 6 7 |

Each edge is walked a constant number of times by predecessor searches, so the total stays O(n). The tree is modified during the walk, so nothing else may read it, and stopping early leaves threads behind.

The script checks every iterative version against the recursive ones on random trees and a 100,000-deep chain, and checks that Morris leaves the tree unchanged.

```python
import random
from collections import deque


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


def shape(root):
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        out.append(None if node is None else node.val)
        if node is not None:
            queue += [node.left, node.right]
    return out


def recursive(root, order):
    out = []

    def go(node):
        if node is None:
            return
        if order == "pre":
            out.append(node.val)
        go(node.left)
        if order == "in":
            out.append(node.val)
        go(node.right)
        if order == "post":
            out.append(node.val)

    go(root)
    return out


def preorder_iter(root):
    out, stack = [], [root] if root else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right:
            stack.append(node.right)  # pushed first, popped last
        if node.left:
            stack.append(node.left)
    return out


def inorder_iter(root):
    out, stack, curr = [], [], root
    while stack or curr:
        while curr:  # go left as far as possible
            stack.append(curr)
            curr = curr.left
        node = stack.pop()  # its left subtree is done
        out.append(node.val)
        curr = node.right
    return out


def traverse(root, order):
    """Pre/in/postorder with (node, ready) stack entries."""
    if order not in ("pre", "in", "post"):
        raise ValueError(f"unknown order {order!r}")
    out, stack = [], [(root, False)]
    while stack:
        node, ready = stack.pop()
        if node is None:
            continue
        if ready:
            out.append(node.val)
        elif order == "pre":  # want node, left, right: push reversed
            stack += [(node.right, False), (node.left, False), (node, True)]
        elif order == "in":
            stack += [(node.right, False), (node, True), (node.left, False)]
        else:
            stack += [(node, True), (node.right, False), (node.left, False)]
    return out


def morris_inorder(root):
    out, curr = [], root
    while curr:
        if curr.left is None:
            out.append(curr.val)
            curr = curr.right  # real child or thread
            continue
        p = curr.left
        while p.right is not None and p.right is not curr:
            p = p.right
        if p.right is None:  # first arrival: thread back to curr
            p.right = curr
            curr = curr.left
        else:  # returned along the thread
            p.right = None
            out.append(curr.val)
            curr = curr.right
    return out


def main():
    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert recursive(root, "pre") == preorder_iter(root) == [8, 3, 1, 6, 4, 7, 10, 14, 13]
    assert recursive(root, "in") == inorder_iter(root) == [1, 3, 4, 6, 7, 8, 10, 13, 14]
    assert traverse(root, "post") == [1, 4, 7, 6, 3, 13, 14, 10, 8]
    assert morris_inorder(root) == [1, 3, 4, 6, 7, 8, 10, 13, 14]
    try:
        traverse(root, "level")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    deep = None
    for v in range(100_000):  # a left chain, far past the recursion limit
        deep = TreeNode(v, deep)
    assert inorder_iter(deep) == list(range(100_000))
    assert traverse(deep, "post") == list(range(100_000))

    rng = random.Random(2)
    for _ in range(500):
        tree = random_tree(rng, rng.randint(0, 20))
        for order in ("pre", "in", "post"):
            assert traverse(tree, order) == recursive(tree, order)
        assert preorder_iter(tree) == recursive(tree, "pre")
        assert inorder_iter(tree) == recursive(tree, "in")
        before = shape(tree)
        assert morris_inorder(tree) == recursive(tree, "in")
        assert shape(tree) == before  # every thread removed


if __name__ == "__main__":
    main()
```

**Time:** O(n) for every version. **Space:** O(h) for the stacks, where `h` is the height (O(log n) bushy, O(n) for a chain); O(1) for Morris.

## 5. Level order: a queue instead of a stack

Questions about levels (values per level, rightmost node per level, averages) need a **breadth-first** traversal: all of depth 0, then depth 1, and so on. Replace the stack with a **queue**: take from the front, add children at the back. Children wait behind everything already queued, which is the rest of the current level. Use `collections.deque`; `list.pop(0)` shifts every element.

To group by level: when a level starts, the queue holds exactly that level, so record `len(queue)` and take that many.

| Queue at level start | Take | Children added | Row |
|---|---:|---|---|
| 8 | 1 | 3, 10 | `[8]` |
| 3 10 | 2 | 1, 6, 14 | `[3, 10]` |
| 1 6 14 | 3 | 4, 7, 13 | `[1, 6, 14]` |
| 4 7 13 | 3 | — | `[4, 7, 13]` |

Variants change only what is done with each row. **Zigzag** reverses every second row, `[8], [10, 3], [1, 6, 14], [13, 7, 4]`; reverse the finished row rather than reordering the queue, which would scramble the next level. **Averages** are `8, 6.5, 7, 8`. The **right side view** is the last value of each row, `8, 10, 14, 13`.

The brute force records each node's depth during a preorder walk; preorder meets each level left to right, so the rows match.

```python
import random
from collections import deque


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


def level_order(root):
    rows, queue = [], deque([root] if root else [])
    while queue:
        row = []
        for _ in range(len(queue)):  # exactly the current level
            node = queue.popleft()
            row.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        rows.append(row)
    return rows


def zigzag(root):
    return [row[::-1] if d % 2 else row for d, row in enumerate(level_order(root))]


def levels_brute(root):
    rows = []

    def go(node, depth):
        if node is None:
            return
        if depth == len(rows):
            rows.append([])
        rows[depth].append(node.val)
        go(node.left, depth + 1)
        go(node.right, depth + 1)

    go(root, 0)
    return rows


def main():
    T = TreeNode
    root = T(8, T(3, T(1), T(6, T(4), T(7))), T(10, None, T(14, T(13))))
    assert level_order(root) == [[8], [3, 10], [1, 6, 14], [4, 7, 13]]
    assert zigzag(root) == [[8], [10, 3], [1, 6, 14], [13, 7, 4]]
    assert [sum(r) / len(r) for r in level_order(root)] == [8, 6.5, 7, 8]
    assert [r[-1] for r in level_order(root)] == [8, 10, 14, 13]
    assert level_order(None) == []

    rng = random.Random(3)
    for _ in range(500):
        tree = random_tree(rng, rng.randint(0, 20))
        assert level_order(tree) == levels_brute(tree)


if __name__ == "__main__":
    main()
```

**Time:** O(n). **Space:** O(w), up to about n/2 for a complete tree.

## 6. Summary

| Order | Visit when | Iterative tool | Typical use |
|---|---|---|---|
| Preorder | before children | stack, push right then left | copy, serialize, pass values down |
| Inorder | between children | stack plus `curr`, go left first | sorted order of a BST |
| Postorder | after children | marked stack, or reversed mirrored preorder | heights, sizes, answers built from children |
| Level order | by depth | `deque`, take `len(queue)` per level | rows, side views, nearest leaf |
| Morris inorder | between children | threads in `None` pointers | inorder with O(1) extra space |

```text
stack = [(root, False)]                 # marked-stack template, any DFS order
while stack:
    node, ready = stack.pop()
    if node is None: continue
    if ready: visit(node)
    else: push (node, True), (node.left, False), (node.right, False)
          in the REVERSE of the order you want them handled
```

## 7. Pitfalls and practice

1. **Giving `None` children in a level-order list.** Missing nodes have no slots (§1).
2. **Pushing left before right in iterative preorder.** The stack reverses the order (§3).
3. **`while stack:` in iterative inorder.** The stack can be empty while `curr` still points at a right subtree (§3).
4. **Deep recursion.** Python fails near 1000 levels; one chain-shaped input is enough (§3).
5. **`list.pop(0)` as a queue, or reordering the queue for zigzag** (§5).
6. **Stopping Morris early.** It leaves threads in the tree (§4).

Practice: binary tree preorder, inorder and postorder traversal (recursive and iterative); binary tree level order traversal I and II; zigzag level order traversal; average of levels in binary tree; minimum depth of binary tree; N-ary tree level order traversal; recover binary search tree (Morris for O(1) space).

Next: [Recursion on Trees](02-recursion-on-trees.md).
