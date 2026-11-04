# Trees — Traversals, Tree Recursion, BSTs, Tries, Balanced Trees

A binary tree is a linked structure where each node has up to two children. Every tree problem rests on two moves: visiting the nodes in a chosen order, and a recursion that states what each call returns for its subtree. Binary search trees add an ordering rule that makes search, insert, delete and order queries cost O(height); tries key a tree by letters; balanced trees keep the height at O(log n) whatever the input order. The folder ends with treaps and AVL trees, with rank and k-th queries.

> **Learning path:** Foundations [1](01-binary-trees-and-traversals.md) → [2](02-recursion-on-trees.md) · Ordered trees [3](03-binary-search-trees.md) → [4](04-construction-paths-and-lca.md) · Other trees [5](05-tries.md) · Advanced [6](06-balanced-trees.md)

## Chapters

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Binary Trees and Traversals](01-binary-trees-and-traversals.md) | `TreeNode`; building from a level-order list with `None`; preorder, inorder, postorder as one outline walk; iterative versions with a stack and one marked-stack template; level order with `deque`; Morris inorder in O(1) space | Binary tree inorder / preorder / postorder traversal; level order traversal; zigzag level order; average of levels |
| 2 | [Recursion on Trees](02-recursion-on-trees.md) | The "`f(node)` returns …" sentence; top-down vs bottom-up; sentinel returns; return one value and record another; negative branches; recursion depth and the iterative fallback | Maximum depth; path sum; symmetric tree; balanced binary tree; diameter of binary tree; binary tree maximum path sum |
| 3 | [Binary Search Trees](03-binary-search-trees.md) | BST property; search and insert; delete in all three cases; the validate trap and two correct checks; k-th smallest with subtree sizes; successor, floor, ceiling; range pruning; balanced build from sorted values; why height matters | Delete node in a BST; validate BST; kth smallest in a BST; inorder successor; range sum of BST; convert sorted array to BST |
| 4 | [Construction, Paths and LCA](04-construction-paths-and-lca.md) | Rebuilding from preorder + inorder in O(n), why preorder + postorder is ambiguous; serialize with `None` markers; LCA in a binary tree and in a BST; downward path sums with root-path prefix sums; right side view; vertical order | Construct from preorder and inorder; serialize and deserialize; lowest common ancestor; path sum III; right side view; vertical order traversal |
| 5 | [Tries](05-tries.md) | Prefix trees; search vs starts-with; prefix counts; delete with pruning; wildcard search; word search on a grid with one trie walk; binary and compressed tries | Implement trie I and II; add and search words; word search II; replace words; search suggestions |
| 6 | [Balanced Trees](06-balanced-trees.md) (advanced) | Rotations; treaps with insert, delete, rank and k-th; AVL trees and the four rotation cases; red-black guarantees; Python's options without a TreeMap | Count of smaller numbers after self; contains duplicate III; sliding window median; my calendar |

## Recognizing the pattern

| The problem says or implies | Reach for | Chapter |
|---|---|---|
| Tree given as `[3, 9, 20, None, None, 15, 7]` | Queue-based build; `None` gets no children | 1 |
| Values level by level, per-level answers, nearest leaf | Level order with `deque` and `len(queue)` | 1 |
| Deep or chain-shaped input in Python | Explicit stack, marked entries | 1, 2 |
| Answer at a node depends on its children | Bottom-up recursion, postorder | 2 |
| Condition along the root-to-node path | Top-down recursion with an argument | 2 |
| Best path that may bend anywhere | Return the one-sided value, record the bent one | 2 |
| Sorted order, k-th smallest, next larger value | BST inorder, successor walk | 3 |
| "Is this a valid BST?" | Bounds passed down, or strictly increasing inorder | 3 |
| Two traversals given, rebuild the tree | Preorder (or postorder) + inorder with an index map | 4 |
| Lowest common manager / ancestor | LCA recursion; value walk in a BST | 4 |
| Count downward paths with a given sum | Prefix-sum counter on the root path, remove on exit | 4 |
| Prefixes, autocomplete, many words at once | Trie | 5 |
| Maximum XOR of a pair | Binary trie | 5 |
| Rank / k-th under online inserts and deletes | Treap with sizes, or `bisect` if small | 6 |

## Conventions

- Nodes are `TreeNode(val, left, right)`. Each script repeats the helpers it needs so that it runs on its own; `build` and `to_level_list` convert to and from level-order lists.
- The running example is the BST `[8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13]`, used in chapters 1 to 4.
- **Height** counts nodes on the longest root-to-leaf path (0 for the empty tree). **Depth** counts edges from the root. **Diameter** counts edges.
- BSTs hold distinct keys unless a chapter says otherwise; the treap of chapter 6 is a multiset. `k` in k-th queries is 1-based.
- Functions that can change the root return the new root; callers write `root = insert(root, key)`.
- Every Python block is a complete script with a `main()` of assertions, tested against a brute force on random trees with a fixed-seed `random.Random`, and run with `python3 -I`.

## Connections

- [Linked Lists](../02-linked-lists/README.md): a tree node is a list node with two pointers; "return the new head" becomes "return the new root".
- [Range Queries](../04-range-queries/README.md): a segment tree is a binary tree over index ranges; root-path prefix sums in chapter 4 are prefix sums on a path; a Fenwick tree replaces a balanced BST when values are known in advance.
- [Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md): a heap is a complete binary tree stored in an array; a treap is a BST and a heap at once.
- [Dynamic Programming](../09-dynamic-programming/08-tree-and-dag-dp.md): tree DP is the bottom-up recursion of chapter 2 with richer states (house robber III, rerooting).
- [Graphs](../10-graphs/05-trees-and-advanced/README.md): trees given as edge lists, rooting, binary-lifting LCA for many queries, and the diameter of general trees.
- [Bit Manipulation](../11-bit-manipulation/03-xor.md): the binary trie for maximum XOR.

## Practice order

1. Traversals: binary tree inorder / preorder / postorder traversal (recursive, then iterative); level order traversal; zigzag level order; minimum depth.
2. Recursion: maximum depth; same tree; symmetric tree; invert binary tree; path sum I and II; balanced binary tree; diameter of binary tree; binary tree maximum path sum.
3. BSTs: search and insert in a BST; validate BST; kth smallest in a BST; delete node in a BST; inorder successor; range sum of BST; convert sorted array to BST; BST iterator.
4. Construction and paths: construct from preorder and inorder; serialize and deserialize; lowest common ancestor (BST, then binary tree); path sum III; right side view; vertical order traversal; all nodes distance K.
5. Tries: implement trie; add and search words; replace words; search suggestions; word search II; maximum XOR of two numbers.
6. Balanced trees: count of smaller numbers after self; contains duplicate III; sliding window median; my calendar II.

For every recursive solution, write the sentence "`f(node)` returns … for the subtree of `node`" before the code.
