# Nodes and Pointers — Building, Walking, and Editing a Linked List

## 1. Adding to the front

You keep recent messages newest first, so every new message goes to the **front**. With a Python list that is `messages.insert(0, m)`, and with a million messages it is slow. A Python list is one block of consecutive slots, so putting `5` at index 0 shifts every value one slot right:

```text
before:  [ 7 ][ 3 ][ 9 ][ 4 ][   ]
shift:   [   ][ 7 ][ 3 ][ 9 ][ 4 ]    ← n values moved
write:   [ 5 ][ 7 ][ 3 ][ 9 ][ 4 ]
```

A **linked list** stores each value in its own box, called a **node**. A node holds the value and a **pointer** (a reference) to the next node. The last node points to `None`. A variable `head` points to the first node.

```text
  head
   │
   ▼
 ┌───┬───┐    ┌───┬───┐    ┌───┬───┐    ┌───┬───┐
 │ 7 │ ●─┼───►│ 3 │ ●─┼───►│ 9 │ ●─┼───►│ 4 │ ╳ │
 └───┴───┘    └───┴───┘    └───┴───┘    └───┴───┘
  val next     val next     val next     val next = None
```

The boxes can be anywhere in memory; only the arrows define the order. To add `5` at the front, make a new node pointing at the old first node and move `head` to it: two steps, however long the list is.

The price: there are no indices. To reach the fourth value you start at `head` and follow three arrows, where a Python list jumps to `a[3]` in one step. [§9](#9-summary-costs-and-moves) compares every cost.

From here on, diagrams write `[7] → [3] → None`: each `[ ]` is a node and each `→` is a `next` pointer.

## 2. The node class and test helpers

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def from_list(values):
    """Build a linked list holding values in order; return its head (None if empty)."""
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head, limit=100_000):
    """Return the values of the list starting at head."""
    out = []
    while head is not None:
        if len(out) >= limit:
            raise ValueError("list is too long or contains a cycle")
        out.append(head.val)
        head = head.next
    return out
```

Every test in this folder has one shape: build with `from_list`, run the pointer code, read back with `to_list`, and compare with the same operation done on a plain Python list (the **brute force**, short code we already trust). `to_list` stops after a step limit, because one pointer mistake can create a loop and a plain walk over a loop never ends. Each later script copies these helpers so that it runs on its own.

## 3. Walking a list

Every linked-list algorithm walks with a pointer, usually called `curr` (current):

```text
curr = head
while curr is not None:
    ... use curr.val ...
    curr = curr.next
```

Trace `length` on `[7] → [3] → [9] → None`:

| Step | `curr` points to | `count` after the step |
|---:|---|---:|
| start | `[7]` | 0 |
| 1 | `[3]` | 1 |
| 2 | `[9]` | 2 |
| 3 | `None` | 3 |

**Why `while curr is not None` and not `while curr.next is not None`?** The second form stops *on* the last node. That is what you want when you need the last node itself (to append after it), but it crashes on an empty list, because `None.next` does not exist. Choose the condition by asking: "where must `curr` be when the loop ends?"

Reading position `i` follows `i` arrows, O(i); `length` is O(n). A node does not know where it sits, so there is no shortcut.

## 4. Inserting

**At the head:** `head = ListNode(5, head)`. The function must **return the new head**, because the caller's `head` variable still points at the old first node. Forgetting to use the returned head is a classic bug: the new node exists but nobody can reach it.

**In the middle.** Insert `6` after the node holding `3`. Walk a pointer `prev` to `[3]`, then:

```text
start   head → [7] → [3] → [9] → None
                      ↑
                     prev

step 1  node = ListNode(6)
        node.next = prev.next          (the new node points at [9])

step 2  prev.next = node               ([3] now points at the new node)

        head → [7] → [3] → [6] → [9] → None
```

**Why this order?** The other way round:

```text
wrong step 1  prev.next = node         [7] → [3] → [6]      [9] → None  ← nobody points here
wrong step 2  node.next = prev.next    prev.next is [6] itself: [6] points to itself, [9] is lost
```

The rule: **connect the new node to the rest first, then connect the rest to the new node.** Never overwrite a `next` pointer while it is the only way to reach the nodes after it.

**At the tail:** walk until `curr.next is None` (stop *on* the last node), then `curr.next = node`. That walk is O(n); keep a separate `tail` pointer and appending is O(1), as `from_list` does.

## 5. Deleting

Deleting a node means making the arrow that points *to* it skip over it. That arrow belongs to the node **before** it. Delete `[3]`: walk `prev` to `[7]`, then:

```text
before   head → [7] → [3] → [9] → None
                 ↑
                prev

step 1   prev.next = prev.next.next

after    head → [7] ───────→ [9] → None
                     [3] ─┘          (still points at [9], but unreachable)
```

Python's garbage collector frees the unreachable node. Deleting the tail is the same with `prev` on the second-to-last node. Finding `prev` is O(n), because a singly linked list cannot step backwards.

The head has no node before it, so deleting it is a different line, `head = head.next`. Delete-at-position written without tricks:

```python
def delete_at(head, i):
    """Delete the node at zero-based position i. Return the new head."""
    if head is None or i < 0:
        raise ValueError("position out of range")
    if i == 0:                      # special case: position 0 has no node before it
        return head.next
    prev = head
    for _ in range(i - 1):          # stop on the node before position i
        prev = prev.next
        if prev is None:
            raise ValueError("position out of range")
    if prev.next is None:
        raise ValueError("position out of range")
    prev.next = prev.next.next
    return head
```

Insert-at-position needs the same `if i == 0` branch, and so does every function that might change the first node. Forgetting it is one of the most common linked-list bugs.

## 6. The dummy head: make the first node ordinary

A **dummy node** (also called a **sentinel**) is a fake node placed in front of the real list. Its value is never read. It exists so that every real node, including the first, has a node before it.

```text
dummy → [?] → [7] → [3] → [9] → None
                ↑
        the real head is dummy.next
```

"The node before position `i`" is now `i` steps from `dummy`, for every `i` including 0. At the end, return `dummy.next`, which is the real head even if the first node was deleted or replaced.

**Problem: remove every node with a given value.** `[6] → [6] → [1] → [6] → [2]` with `val = 6` gives `[1] → [2]`. Without a dummy you need one loop to skip matches at the front (changing `head`) and another for the rest. With a dummy, one loop does both.

**Invariant:** every node from `dummy` through `prev` has been checked and kept; `prev.next` is the next node to examine.

| Step | `prev` | `prev.next` | Action | List after |
|---:|---|---|---|---|
| 1 | dummy | `[6]` | delete, `prev` stays | `dummy → [6] → [1] → [6] → [2]` |
| 2 | dummy | `[6]` | delete, `prev` stays | `dummy → [1] → [6] → [2]` |
| 3 | dummy | `[1]` | keep, `prev = [1]` | unchanged |
| 4 | `[1]` | `[6]` | delete, `prev` stays | `dummy → [1] → [2]` |
| 5 | `[1]` | `[2]` | keep, `prev = [2]` | unchanged |
| 6 | `[2]` | `None` | stop, return `dummy.next` | `[1] → [2]` |

`prev` **does not move after a deletion**: the node that slid into `prev.next` has not been checked yet. Moving `prev` would skip it, which breaks on two matches in a row (steps 1 and 2).

The script rewrites insert and delete with a dummy (no `i == 0` branch), adds `remove_value`, `length` and `get`, and tests them and the helpers against Python lists:

```python
import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def from_list(values):
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head, limit=100_000):
    out = []
    while head is not None:
        if len(out) >= limit:
            raise ValueError("list is too long or contains a cycle")
        out.append(head.val)
        head = head.next
    return out


def length(head):
    count, curr = 0, head
    while curr is not None:
        count += 1
        curr = curr.next
    return count


def get(head, i):
    """Value at zero-based position i: follow i arrows."""
    if i < 0:
        raise ValueError("position must be nonnegative")
    curr = head
    for _ in range(i):
        if curr is None:
            break
        curr = curr.next
    if curr is None:
        raise ValueError("position out of range")
    return curr.val


def node_before(dummy, i):
    """Walk i steps from dummy: the node before position i, or None."""
    if i < 0:
        raise ValueError("position must be nonnegative")
    prev = dummy
    for _ in range(i):
        prev = prev.next
        if prev is None:
            return None
    return prev


def insert_at(head, i, val):
    dummy = ListNode(0, head)
    prev = node_before(dummy, i)
    if prev is None:
        raise ValueError("position out of range")
    prev.next = ListNode(val, prev.next)
    return dummy.next


def delete_at(head, i):
    dummy = ListNode(0, head)
    prev = node_before(dummy, i)
    if prev is None or prev.next is None:
        raise ValueError("position out of range")
    prev.next = prev.next.next
    return dummy.next


def remove_value(head, val):
    dummy = ListNode(0, head)
    prev = dummy
    while prev.next is not None:
        if prev.next.val == val:
            prev.next = prev.next.next   # delete; prev stays
        else:
            prev = prev.next             # keep; move on
    return dummy.next


def main():
    assert from_list([]) is None and to_list(None) == []
    loop = from_list([1, 2])
    loop.next.next = loop                # 1 → 2 → 1 → ...
    try:
        to_list(loop, limit=10)
        raise AssertionError("cycle not detected")
    except ValueError:
        pass

    assert to_list(remove_value(from_list([6, 6, 1, 6, 2]), 6)) == [1, 2]
    assert remove_value(from_list([6, 6]), 6) is None
    for bad in (-1, 3):
        try:
            get(from_list([7, 3, 9]), bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = random.Random(4)
    for _ in range(400):
        values = [rng.randint(0, 3) for _ in range(rng.randint(0, 10))]
        assert to_list(from_list(values)) == values
        val = rng.randint(0, 3)
        assert to_list(remove_value(from_list(values), val)) == [v for v in values if v != val]
        head = from_list(values)
        assert length(head) == len(values)
        assert all(get(head, i) == v for i, v in enumerate(values))

        for _ in range(8):
            if values and rng.random() < 0.5:
                i = rng.randrange(len(values))
                del values[i]
                head = delete_at(head, i)
            else:
                i, v = rng.randint(0, len(values)), rng.randint(0, 9)
                values.insert(i, v)
                head = insert_at(head, i, v)
            assert to_list(head) == values


if __name__ == "__main__":
    main()
```

Time: O(n) for `remove_value`, O(i) for insert or delete at `i`. Space: O(1), one extra node.

**When to reach for a dummy:** whenever the head might be deleted, replaced, or not yet exist (building a new list).

## 7. Removing duplicates from a sorted list

**Problem.** In a sorted list, keep one copy of each value: `[1] → [1] → [2] → [3] → [3]` becomes `[1] → [2] → [3]`.

**Key observation.** In a sorted list a duplicate sits right after its twin, so compare each node with its successor. If equal, unlink the successor and stay (the next successor may be another copy); otherwise move on.

**Invariant:** the nodes from `head` through `curr` are distinct, and `curr` holds the largest value seen so far.

| Step | `curr` | `curr.next` | Action | List after |
|---:|---|---|---|---|
| 1 | first `[1]` | `[1]` | equal: unlink, stay | `[1] → [2] → [3] → [3]` |
| 2 | `[1]` | `[2]` | move | unchanged |
| 3 | `[2]` | `[3]` | move | unchanged |
| 4 | `[3]` | `[3]` | equal: unlink, stay | `[1] → [2] → [3]` |
| 5 | `[3]` | `None` | stop | |

The first copy always stays, so the head never changes and no dummy is needed.

**Variant: delete every value that appears more than once.** `[1] → [1] → [2] → [3] → [3]` becomes `[2]`. Now the head *can* be deleted, so use a dummy. Walk `run_end` to the last node of the run of equal values starting at `prev.next`. A run of one node is kept (`prev` advances); a longer run is cut out whole with `prev.next = run_end.next`, and `prev` stays, because the node after the run has not been examined.

```python
import random
from collections import Counter


class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


def from_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head):
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def dedupe_sorted(head):
    """Keep one copy of each value. The list must be sorted."""
    curr = head
    while curr is not None and curr.next is not None:
        if curr.next.val == curr.val:
            curr.next = curr.next.next
        else:
            curr = curr.next
    return head


def drop_repeated_sorted(head):
    """Delete every value that occurs more than once. The list must be sorted."""
    dummy = ListNode(0, head)
    prev = dummy
    while prev.next is not None:
        run_end = prev.next
        while run_end.next is not None and run_end.next.val == run_end.val:
            run_end = run_end.next
        if run_end is prev.next:      # run of length 1: keep it
            prev = prev.next
        else:                         # run of length >= 2: cut it all out
            prev.next = run_end.next
    return dummy.next


def main():
    assert to_list(dedupe_sorted(from_list([1, 1, 2, 3, 3]))) == [1, 2, 3]
    assert to_list(drop_repeated_sorted(from_list([1, 1, 2, 3, 3]))) == [2]
    assert dedupe_sorted(None) is None
    assert drop_repeated_sorted(from_list([4, 4, 4])) is None

    rng = random.Random(5)
    for _ in range(400):
        values = sorted(rng.randint(-3, 3) for _ in range(rng.randint(0, 12)))
        assert to_list(dedupe_sorted(from_list(values))) == sorted(set(values))
        counts = Counter(values)
        expected = [v for v in values if counts[v] == 1]
        assert to_list(drop_repeated_sorted(from_list(values))) == expected


if __name__ == "__main__":
    main()
```

Time: O(n) for both. Space: O(1).

## 8. Doubly linked lists

A singly linked node can only move forward, so deleting a node needs the node before it. A **doubly linked list** gives each node two pointers, `prev` and `next`, so holding any node you can remove it in O(1).

Doubly linked lists almost always use **two sentinels**, a fake `head` and a fake `tail`. Real nodes live between them, so every real node has a real `prev` and a real `next`, and there are no `None` checks at all:

```text
empty:      head ⇄ tail
with data:  head ⇄ [7] ⇄ [3] ⇄ [9] ⇄ tail
```

**Remove a node `x`.** One pointer change per neighbor:

```text
before        head ⇄ [7] ⇄ [3] ⇄ [9] ⇄ tail          x = [3]

step 1   x.prev.next = x.next          [7] now points forward to [9]
step 2   x.next.prev = x.prev          [9] now points back to [7]
```

**Insert node `x` after node `p`.** Four changes. As in §4, set the new node's own pointers first, while `p.next` still leads to the rest:

```text
before        head ⇄ [7] ⇄ [9] ⇄ tail          insert x = [3] after p = [7]

step 1   x.prev = p                     [3] points back to [7]
step 2   x.next = p.next                [3] points forward to [9]
step 3   p.next.prev = x                [9] points back to [3]
step 4   p.next = x                     [7] points forward to [3]
```

Steps 3 and 4 must stay in this order: step 4 overwrites `p.next`, and step 3 still needs the old `p.next` (which is `[9]`).

A small deque built this way, tested against `collections.deque`:

```python
import random
from collections import deque


class DNode:
    def __init__(self, val=0):
        self.val = val
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = DNode()          # sentinel before the first real node
        self.tail = DNode()          # sentinel after the last real node
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def insert_after(self, p, x):
        x.prev = p
        x.next = p.next
        p.next.prev = x
        p.next = x
        self.size += 1
        return x

    def remove(self, x):
        if x is self.head or x is self.tail:
            raise ValueError("cannot remove a sentinel")
        x.prev.next = x.next
        x.next.prev = x.prev
        x.prev = x.next = None       # detach, so stale use fails loudly
        self.size -= 1
        return x

    def push_front(self, val):
        return self.insert_after(self.head, DNode(val))

    def push_back(self, val):
        return self.insert_after(self.tail.prev, DNode(val))

    def pop_front(self):
        if self.size == 0:
            raise ValueError("pop from empty list")
        return self.remove(self.head.next).val

    def pop_back(self):
        if self.size == 0:
            raise ValueError("pop from empty list")
        return self.remove(self.tail.prev).val

    def to_list(self):
        out, curr = [], self.head.next
        while curr is not self.tail:
            out.append(curr.val)
            curr = curr.next
        return out

    def to_list_backward(self):
        out, curr = [], self.tail.prev
        while curr is not self.head:
            out.append(curr.val)
            curr = curr.prev
        return out


def main():
    dll = DoublyLinkedList()
    mid = dll.push_back(3)
    dll.push_front(7)
    dll.push_back(9)
    assert dll.to_list() == [7, 3, 9]
    dll.remove(mid)                   # O(1) removal by node
    assert dll.to_list() == [7, 9] and dll.size == 2
    try:
        DoublyLinkedList().pop_front()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(6)
    dll, ref = DoublyLinkedList(), deque()
    for _ in range(3000):
        op = rng.randrange(4)
        if op == 0:
            v = rng.randint(0, 99)
            dll.push_front(v)
            ref.appendleft(v)
        elif op == 1:
            v = rng.randint(0, 99)
            dll.push_back(v)
            ref.append(v)
        elif op == 2 and ref:
            assert dll.pop_front() == ref.popleft()
        elif op == 3 and ref:
            assert dll.pop_back() == ref.pop()
        assert dll.size == len(ref)
    assert dll.to_list() == list(ref)
    assert dll.to_list_backward() == list(reversed(ref))


if __name__ == "__main__":
    main()
```

Time: every operation is O(1); `to_list` is O(n). Space: two pointers per node plus two sentinels.

Python's `collections.deque` links blocks of 64 slots rather than single values and gives the same O(1) costs at both ends. What it cannot do is remove an element you are holding in O(1). That ability is the reason to write a doubly linked list yourself.

## 9. Summary: costs and moves

`n` is the length, `i` the position.

| Operation | Python list (array) | Linked list (singly, unless noted) |
|---|---|---|
| Read position `i` | O(1) | O(i), walk from head |
| Insert / delete at the front | O(n), shifts everything | O(1) |
| Insert / delete at the back | O(1) amortized | O(1) insert with a tail pointer; O(n) delete (need the node before) |
| Insert / delete after a node you already hold | O(n), shifts the rest | O(1) |
| Delete a node you hold | O(n) | O(1) doubly linked; O(n) singly (find the node before) |
| Search for a value | O(n) | O(n) |
| Extra memory per value | small | one node object and one or two pointers |
| Cache friendliness | high, values are adjacent | low, nodes are scattered |

"Amortized" means averaged over many operations: a Python list occasionally reallocates and copies, but the average append is constant.

In Python, a plain `list` or `collections.deque` usually wins for ordinary sequences. Linked lists earn their place when you hold a node and want O(1) removal or insertion there (the LRU cache in [chapter 4](04-merging-and-design.md#8-design-an-lru-cache)), when you splice whole chains without copying, and in interviews, which test whether you can move pointers without losing anything.

| Move | Code | Rule |
|---|---|---|
| Walk to the end | `while curr is not None` | Ask where `curr` must be when the loop ends |
| Walk to the last node | `while curr.next is not None` | Needs a non-empty list |
| Insert after `prev` | `node.next = prev.next; prev.next = node` | New node to the rest first |
| Delete after `prev` | `prev.next = prev.next.next` | Do not advance `prev` after a deletion |
| Head might change | `dummy = ListNode(0, head)` … `return dummy.next` | Caller writes `head = f(head)` |
| Doubly linked remove | `x.prev.next = x.next; x.next.prev = x.prev` | Two sentinels, no `None` checks |
| Doubly linked insert after `p` | `x.prev, x.next = p, p.next; p.next.prev = x; p.next = x` | Overwrite `p.next` last |

## 10. Pitfalls and practice

1. **Losing the rest of the list.** Overwriting `prev.next` before saving where it pointed. Connect the new node to the rest first (§4).
2. **Dropping the returned head.** Any function that can change the first node must return the head, and the caller must write `head = f(head)`.
3. **`None` checks.** `curr.next.val` crashes when `curr.next` is `None`. Before touching `x.next`, make sure `x` is not `None`; before touching `x.next.val`, make sure `x.next` is not `None`.
4. **Advancing after a deletion.** In `remove_value`, moving `prev` after deleting skips the node that slid into place.
5. **Special-casing the head by hand.** Use a dummy node instead whenever the head can change.
6. **Accidental cycles.** One wrong assignment can make a node point back into the list. Test helpers that stop after a step limit turn an infinite loop into a clear error.
7. **Doubly linked pointer order.** In insert-after, set the new node's pointers first and overwrite `p.next` last.

Practice: design a linked list (get, add at head, add at tail, add at index, delete at index); remove linked list elements; remove duplicates from sorted list; remove duplicates from sorted list II; delete a node when you are given only that node (copy the next value forward); design a browser history with back and forward (doubly linked list).

Next: [Reversal](02-reversal.md).
