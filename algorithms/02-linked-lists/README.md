# Linked Lists — Pointers, Dummy Nodes, Fast/Slow, Reversal

A linked list stores a sequence as separate nodes, each holding a value and a pointer to the next node. It gives up instant indexing in exchange for O(1) insertion and removal anywhere you already hold a node. Almost every linked-list problem is solved with a handful of moves: walk with a pointer, save `next` before overwriting it, put a dummy node in front, reverse a run of arrows, and send two pointers at different speeds. The folder starts from what a node is and ends with Floyd's cycle proof, merge sort on lists, and O(1) LRU and LFU caches.

> **Learning path:** [Nodes and Pointers](01-nodes-and-pointers.md) → [Reversal](02-reversal.md) → [Fast and Slow Pointers](03-fast-and-slow-pointers.md) → [Merging and Design](04-merging-and-design.md)

## Chapters

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Nodes and Pointers](01-nodes-and-pointers.md) | Memory picture versus Python lists; `ListNode` and test helpers; traversal; insert and delete at head, middle, tail; the dummy head; sorted-list deduplication; doubly linked lists with sentinels; cost table | Design linked list; remove linked list elements; remove duplicates from sorted list I and II |
| 2 | [Reversal](02-reversal.md) | The `prev`/`curr`/`nxt` loop traced step by step; recursive reversal; reversing a range, groups of `k`, pairs; rotation by ring-and-cut; palindrome check that restores the list | Reverse linked list I and II; reverse nodes in k-group; swap nodes in pairs; rotate list; palindrome linked list |
| 3 | [Fast and Slow Pointers](03-fast-and-slow-pointers.md) | First versus second middle; fixed-gap pointers; Floyd's cycle detection with proof; cycle entry by the distance argument; cycle length; switch-heads intersection; an array as a linked list | Middle of the linked list; remove N-th node from end; linked list cycle I and II; intersection of two linked lists; find the duplicate number |
| 4 | [Merging and Design](04-merging-and-design.md) | Stable merge with dummy and tail; k-way merge with a heap or in pairs; top-down and bottom-up merge sort; partition; digit addition with carry; reorder; deep copy with random pointers (map and interleaving); LRU cache; LFU cache | Merge two / k sorted lists; sort list; partition list; add two numbers; copy list with random pointer; reorder list; LRU cache; LFU cache |

## Recognizing the pattern

| The problem says or implies | Reach for | Chapter |
|---|---|---|
| The head might be deleted, replaced, or the result list starts empty | Dummy head, return `dummy.next` | 1 |
| Remove a node you are holding, in O(1), from the middle of an ordering | Doubly linked list with two sentinels | 1, 4 |
| Reverse all or part of the list, or process it "from the back" | `prev`/`curr`/`nxt` reversal | 2 |
| Rotate, or cut the list at a computed position | Count length, make a ring, cut | 2 |
| Middle of the list, or split into halves | Slow 1 step, fast 2 steps; first middle to split | 3 |
| "k-th from the end" in one pass | Two pointers with a gap of `k` | 3 |
| Does it loop? Where does the loop start? | Floyd: meet, then restart one pointer at the head | 3 |
| Two lists may share a tail | Switch heads; both walk `a + b + c` | 3 |
| Values in `1 … n` used as indices, O(1) memory, array must stay unchanged | `i → nums[i]` is a linked list; find the cycle entry | 3 |
| Combine sorted lists | Merge with dummy and tail; heap for `k` lists | 4 |
| Sort a linked list | Merge sort (first middle, cut, merge); bottom-up for O(1) space | 4 |
| Rearrange into groups keeping order | One dummy and tail per group, then cut and join | 4 |
| Deep copy of a node graph | Map old → new, or interleave copies | 4 |
| O(1) cache with recency eviction | Dict of key → node plus doubly linked list | 4 |

## Conventions

- Nodes are `ListNode(val, next)`. [Chapter 1, §2](01-nodes-and-pointers.md#2-the-node-class-and-test-helpers) defines it with two helpers used by every test: `from_list(values)` builds a list and returns its head, and `to_list(head)` returns the values (stopping with an error if the list is too long or cyclic).
- Diagrams write a node as `[v]` and a `next` pointer as `→`; doubly linked pointers are `⇄`.
- Positions are zero-based. Ranges such as `reverse_between(head, left, right)` are inclusive and say so; well-known problem versions that count from 1 are noted.
- Functions that can change the first node **return the new head**; callers write `head = f(head)`.
- Node identity is compared with `is`, never by value.
- Every Python block is a complete script with a `main()` of assertions. Solutions are checked against a Python-list brute force with a fixed-seed `random.Random`, and run with `python3 -I`.

## Connections

- [Trees](../03-trees/README.md), the next folder: a binary tree node is a list node with two `next` pointers (`left`, `right`). Walking, recursion that fixes things up after the call returns (recursive reversal), and the first-middle split (building a balanced tree from a sorted list) carry over directly.
- [Binary Search](../01-binary-search/README.md): "find the duplicate number" also falls to binary search on the answer; compare with the cycle method in chapter 3.
- [Sliding Window](../05-sliding-window/README.md): the gap-of-`k` pointers in chapter 3 are the linked-list form of two pointers moving in the same direction.
- [Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md): the heap behind merging `k` sorted lists in chapter 4.
- [Dynamic Programming](../09-dynamic-programming/README.md): `functools.lru_cache` is the LRU cache of chapter 4 wrapped around a function.
- [Graphs](../10-graphs/README.md): a linked list is a graph where every node has at most one outgoing edge. Floyd's algorithm finds cycles in any such "functional graph", and copying a list with random pointers is a small case of cloning a graph.

## Practice order

1. Design linked list → remove linked list elements → remove duplicates from sorted list I and II.
2. Reverse linked list (iterative, then recursive) → reverse linked list II → swap nodes in pairs → reverse nodes in k-group → rotate list.
3. Middle of the linked list → remove N-th node from end → linked list cycle → linked list cycle II → intersection of two linked lists → palindrome linked list.
4. Merge two sorted lists → partition list → add two numbers → reorder list → sort list → merge k sorted lists.
5. Copy list with random pointer → find the duplicate number → LRU cache → LFU cache.

At each step, draw the pointers before and after on paper first, and name which `next` you must save before you overwrite it.
