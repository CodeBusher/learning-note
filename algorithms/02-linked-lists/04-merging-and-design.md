# Merging and Design — Splicing Lists and Building an LRU Cache

## 1. Merge two sorted lists

**Problem.** Given two sorted lists, return one sorted list made of their nodes. `[1] → [3] → [5]` and `[2] → [3] → [4]` give `[1] → [2] → [3] → [3] → [4] → [5]`.

**Brute force.** `sorted(a + b)` on the values, then build new nodes: O((m + n) log(m + n)) time and new memory.

**Key observation.** The smallest remaining value is always at the front of one of the two lists. Compare the fronts, unlink the smaller node, append it to the result. No new nodes: only `next` pointers are rewired. The result starts empty, so use a dummy head ([chapter 1, §6](01-nodes-and-pointers.md#6-the-dummy-head-make-the-first-node-ordinary)) and a `tail` pointer to its last node.

**Invariant:** the result from `dummy.next` to `tail` holds the smallest nodes seen so far, in sorted order; `a` and `b` point at the fronts of what remains.

```text
start     a: [1] → [3] → [5]      b: [2] → [3] → [4]      result: dummy

step 1    1 <= 2: take a's [1]    result: dummy → [1]
step 2    3 >  2: take b's [2]    result: dummy → [1] → [2]
step 3    3 <= 3: take a's [3]    result: ... → [2] → [3]a
step 4    5 >  3: take b's [3]    result: ... → [3]a → [3]b
step 5    5 >  4: take b's [4]    result: ... → [3]b → [4]
step 6    b is empty: attach the rest of a in one move
          result: dummy → [1] → [2] → [3]a → [3]b → [4] → [5]
```

On a tie (step 3), take from `a`, so equal values keep their original order (`[3]a` before `[3]b`). A merge with this property is **stable**, which matters when nodes carry more than a value. Step 6 is why merging is fast: the leftover is already sorted and linked, so one assignment attaches all of it.

Time: O(m + n). Space: O(1); the result reuses the input nodes. The code is `merge_two` in the script of §2.

## 2. Merge k sorted lists

**Problem.** Merge `k` sorted lists with `N` nodes in total. `[1, 4, 5]`, `[1, 3, 4]`, `[2, 6]` give `[1, 1, 2, 3, 4, 4, 5, 6]`.

**Brute force.** Merge the lists one at a time into a growing result. The result is re-walked on every merge: up to O(kN).

**Key observation.** As in §1, the next node is the smallest of the `k` fronts. Repeatedly finding the smallest of `k` values is what a **min-heap** does: it returns its smallest item and accepts a new one in O(log k) ([Heaps and Priority Queues](../07-heaps-and-priority-queues/README.md)). Put each front in the heap; pop the smallest, append it, push its successor.

Python's `heapq` compares tuples item by item, and nodes cannot be compared with `<`. Store `(value, list_index, node)`: on equal values the list index breaks the tie and the node is never compared.

Trace (heap shown sorted, `Lᵢ` names the list):

| Step | Pop | Push | Heap after the step | Result |
|---:|---|---|---|---|
| 0 | | fronts | `(1,L0) (1,L1) (2,L2)` | |
| 1 | `(1,L0)` | `(4,L0)` | `(1,L1) (2,L2) (4,L0)` | 1 |
| 2 | `(1,L1)` | `(3,L1)` | `(2,L2) (3,L1) (4,L0)` | 1 1 |
| 3 | `(2,L2)` | `(6,L2)` | `(3,L1) (4,L0) (6,L2)` | 1 1 2 |
| 4 | `(3,L1)` | `(4,L1)` | `(4,L0) (4,L1) (6,L2)` | 1 1 2 3 |
| 5 | `(4,L0)` | `(5,L0)` | `(4,L1) (5,L0) (6,L2)` | … 4 |
| 6–8 | `(4,L1)`, `(5,L0)`, `(6,L2)` | none | empty | … 4 5 6 |

**Without a heap: merge in pairs.** Merge lists 0+1, 2+3, …, then merge the results in pairs again. Each round touches every node once and halves the number of lists, so about `log₂ k` rounds: O(N log k), the same as the heap.

```python
import heapq
import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


def from_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head, limit=100_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def merge_two(a, b):
    dummy = tail = ListNode()
    while a is not None and b is not None:
        if a.val <= b.val:              # <= keeps the merge stable
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a is not None else b
    return dummy.next


def merge_k_heap(lists):
    heap = [(node.val, i, node) for i, node in enumerate(lists) if node is not None]
    heapq.heapify(heap)
    dummy = tail = ListNode()
    while heap:
        _, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, i, node.next))
    tail.next = None
    return dummy.next


def merge_k_pairs(lists):
    lists = [h for h in lists if h is not None]
    if not lists:
        return None
    while len(lists) > 1:
        merged = [merge_two(lists[i], lists[i + 1]) for i in range(0, len(lists) - 1, 2)]
        if len(lists) % 2:
            merged.append(lists[-1])
        lists = merged
    return lists[0]


def main():
    assert to_list(merge_two(from_list([1, 3, 5]), from_list([2, 3, 4]))) == [1, 2, 3, 3, 4, 5]
    assert merge_two(None, None) is None
    a3 = from_list([3])
    assert merge_two(a3, from_list([3])) is a3          # tie: a's node first
    example = [[1, 4, 5], [1, 3, 4], [2, 6]]
    for merge in (merge_k_heap, merge_k_pairs):
        assert to_list(merge([from_list(x) for x in example])) == [1, 1, 2, 3, 4, 4, 5, 6]
        assert merge([]) is None and merge([None, None]) is None

    rng = random.Random(31)
    for _ in range(500):
        groups = [sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 8)))
                  for _ in range(rng.randint(0, 7))]
        expected = sorted(v for g in groups for v in g)
        for merge in (merge_k_heap, merge_k_pairs):
            assert to_list(merge([from_list(g) for g in groups])) == expected
        if len(groups) >= 2:
            a, b = groups[0], groups[1]
            assert to_list(merge_two(from_list(a), from_list(b))) == sorted(a + b)


if __name__ == "__main__":
    main()
```

Time: O(N log k) for both k-way merges. Space: O(k) for the heap or the list of heads.

## 3. Sort a list with merge sort

**Problem.** Sort a linked list: `[4] → [2] → [1] → [3]` becomes `[1] → [2] → [3] → [4]`.

**Why merge sort?** Quicksort and heapsort jump to arbitrary positions, which a list cannot do cheaply. Merge sort needs only three things lists do well: find the middle ([chapter 3, §1](03-fast-and-slow-pointers.md#1-the-middle-node)), cut, and merge (§1). And merging lists needs no extra array.

### Top-down

1. A list of 0 or 1 nodes is sorted.
2. Find the **first** middle `mid`; let `right = mid.next`, then **cut**: `mid.next = None`.
3. Sort both halves recursively and merge them.

```text
              [4] → [2] → [1] → [3]
          [4] → [2]              [1] → [3]          split at the first middle [2]
        [4]      [2]           [1]      [3]
          [2] → [4]              [1] → [3]          merge
              [1] → [2] → [3] → [4]                 merge
```

Without the cut, the left half still runs into the right half, the recursion sorts overlapping lists, and the result has cycles or lost nodes. The first middle matters too: on two nodes the second-middle loop returns the second node, the "left half" keeps both, and the recursion never shrinks. The recursion is `log₂ n` deep: O(log n) stack.

### Bottom-up: O(1) extra space

Skip the recursion. Merge runs of size 1 into sorted runs of size 2, then 2 into 4, and so on. Each pass walks the list with a `tail` pointer from a dummy. A helper `split(head, size)` cuts after `size` nodes and returns the rest. One step of a pass: cut off `left`, cut off `right`, merge them, attach to `tail`, move `tail` to the end of the merged run.

```text
size 1   [4] [2] [1] [3] [5]   →   [2,4] [1,3] [5]
size 2   [2,4] [1,3] [5]       →   [1,2,3,4] [5]
size 4   [1,2,3,4] [5]         →   [1,2,3,4,5]
size 8   size >= n: stop
```

```python
import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


def from_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head, limit=100_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def merge_two(a, b):
    dummy = tail = ListNode()
    while a is not None and b is not None:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a is not None else b
    return dummy.next


def sort_top_down(head):
    if head is None or head.next is None:
        return head
    slow, fast = head, head
    while fast.next is not None and fast.next.next is not None:   # first middle
        slow, fast = slow.next, fast.next.next
    right = slow.next
    slow.next = None                                             # cut
    return merge_two(sort_top_down(head), sort_top_down(right))


def split(head, size):
    """Cut after the first `size` nodes; return the head of the rest."""
    for _ in range(size - 1):
        if head is None:
            return None
        head = head.next
    if head is None:
        return None
    rest = head.next
    head.next = None
    return rest


def sort_bottom_up(head):
    n, curr = 0, head
    while curr is not None:
        n, curr = n + 1, curr.next
    dummy = ListNode(0, head)
    size = 1
    while size < n:
        tail, curr = dummy, dummy.next
        while curr is not None:
            left = curr
            right = split(left, size)
            curr = split(right, size)
            tail.next = merge_two(left, right)
            while tail.next is not None:        # move tail to the end of the merged run
                tail = tail.next
        size *= 2
    return dummy.next


def main():
    for sort in (sort_top_down, sort_bottom_up):
        assert to_list(sort(from_list([4, 2, 1, 3]))) == [1, 2, 3, 4]
        assert sort(None) is None
        assert to_list(sort(from_list([7]))) == [7]

    rng = random.Random(32)
    for _ in range(400):
        values = [rng.randint(-9, 9) for _ in range(rng.randint(0, 40))]
        for sort in (sort_top_down, sort_bottom_up):
            assert to_list(sort(from_list(values))) == sorted(values)
    big = [rng.randint(0, 10**6) for _ in range(20_000)]
    assert to_list(sort_bottom_up(from_list(big))) == sorted(big)


if __name__ == "__main__":
    main()
```

Time: O(n log n) for both: `log₂ n` levels or passes of O(n) each (walking `tail` along each merged run adds only O(n) per pass). Space: O(log n) stack top-down, O(1) bottom-up.

## 4. Partition around a value

**Problem.** Put every node with value `< x` before every node with value `≥ x`, keeping the original order inside each group. `[1, 4, 3, 2, 5, 2]` with `x = 3` gives `[1, 2, 2, 4, 3, 5]`.

**Key observation.** Build two lists as you walk, "small" and "large", each with its own dummy and tail, and append each node to one of them. At the end, attach large after small.

```text
[1] <3    small: [1]
[4] ≥3                          large: [4]
[3] ≥3                          large: [4] → [3]
[2] <3    small: [1] → [2]
[5] ≥3                          large: [4] → [3] → [5]
[2] <3    small: [1] → [2] → [2]

finish    large_tail.next = None          ← cut!
          small_tail.next = large_dummy.next
          [1] → [2] → [2] → [4] → [3] → [5] → None
```

**Why the cut?** Appending a node does not change its own `next`. `[5]` still points to the last `[2]`, its successor in the original list; without the cut the result is `… → [5] → [2] → [4] → …`, a cycle. Whenever you redistribute nodes into new lists, end each new list with an explicit `None`.

## 5. Add two numbers

**Problem.** Two non-negative integers are stored as digit lists, **least significant digit first**. Return their sum in the same form. `342 + 465 = 807`: `[2, 4, 3] + [5, 6, 4] = [7, 0, 8]`.

**Brute force.** Convert to Python integers, add, convert back. It works in Python (unbounded integers), but a 100-digit number overflows in fixed-width languages, and the problem asks for digit-by-digit addition.

**Key observation.** Least-significant-first is the order of grade-school addition. Walk both lists together; write `total % 10` and carry `total // 10`; a missing digit counts as 0; a leftover carry becomes one more digit.

| Step | Digit of a | Digit of b | Carry in | Total | Write | Carry out |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 5 | 0 | 7 | 7 | 0 |
| 2 | 4 | 6 | 0 | 10 | 0 | 1 |
| 3 | 3 | 4 | 1 | 8 | 8 | 0 |

With `[9, 9] + [1]` the steps write 0, 0 and leave carry 1, which adds a final `[1]`: `[0, 0, 1]` = 100.

**Variant: most significant digit first.** Reverse both lists ([chapter 2](02-reversal.md)), add, reverse the result; or push digits onto two stacks and build the answer by inserting at the head.

## 6. Reorder a list

**Problem.** Rearrange `L0 → L1 → … → Ln−1` into `L0 → Ln−1 → L1 → Ln−2 → …`. `[1, 2, 3, 4, 5]` becomes `[1, 5, 2, 4, 3]`.

**Brute force.** Put the nodes in a Python list and relink by index from both ends: O(n) memory.

**Key observation.** The order alternates between the front of the first half and the *back* of the second half. Reversing the second half turns "from the back" into "from the front". So: split at the first middle, reverse the second half, weave.

```text
split     first:  [1] → [2] → [3]       second: [4] → [5]     (cut after [3])
reverse   second: [5] → [4]
weave     p = [1], q = [5]:  save p_next = [2], q_next = [4];  p.next = q;  q.next = p_next
          p = [2], q = [4]:  same
          result: [1] → [5] → [2] → [4] → [3] → None
```

One script tests §4–§6 against Python-list versions:

```python
import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


def from_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head, limit=100_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def partition(head, x):
    small = small_tail = ListNode()
    large = large_tail = ListNode()
    while head is not None:
        if head.val < x:
            small_tail.next = head
            small_tail = head
        else:
            large_tail.next = head
            large_tail = head
        head = head.next
    large_tail.next = None              # cut, or the old next makes a cycle
    small_tail.next = large.next
    return small.next


def add_two_numbers(a, b):
    dummy = tail = ListNode()
    carry = 0
    while a is not None or b is not None or carry:
        total = carry
        if a is not None:
            total, a = total + a.val, a.next
        if b is not None:
            total, b = total + b.val, b.next
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    return dummy.next


def reverse(head):
    prev, curr = None, head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    return prev


def reorder(head):
    if head is None or head.next is None:
        return head
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow, fast = slow.next, fast.next.next
    second = reverse(slow.next)
    slow.next = None                       # cut the first half
    p, q = head, second
    while q is not None:                   # second half is never longer
        p_next, q_next = p.next, q.next
        p.next = q
        q.next = p_next
        p, q = p_next, q_next
    return head


def to_digits(number):
    return [int(c) for c in reversed(str(number))]


def brute_reorder(values):
    out, i, j = [], 0, len(values) - 1
    while i <= j:
        out.append(values[i])
        if i != j:
            out.append(values[j])
        i, j = i + 1, j - 1
    return out


def main():
    assert to_list(partition(from_list([1, 4, 3, 2, 5, 2]), 3)) == [1, 2, 2, 4, 3, 5]
    assert partition(None, 0) is None
    assert to_list(add_two_numbers(from_list([2, 4, 3]), from_list([5, 6, 4]))) == [7, 0, 8]
    assert to_list(add_two_numbers(from_list([9, 9]), from_list([1]))) == [0, 0, 1]
    assert to_list(reorder(from_list([1, 2, 3, 4, 5]))) == [1, 5, 2, 4, 3]
    assert reorder(None) is None

    rng = random.Random(33)
    for _ in range(500):
        values = [rng.randint(0, 6) for _ in range(rng.randint(0, 12))]
        x = rng.randint(0, 7)
        expected = [v for v in values if v < x] + [v for v in values if v >= x]
        assert to_list(partition(from_list(values), x)) == expected
        assert to_list(reorder(from_list(values))) == brute_reorder(values)

        p, q = rng.randint(0, 10**rng.randint(1, 12)), rng.randint(0, 10**rng.randint(1, 12))
        got = to_list(add_two_numbers(from_list(to_digits(p)), from_list(to_digits(q))))
        assert got == to_digits(p + q)


if __name__ == "__main__":
    main()
```

Time: O(n) for partition and reorder, O(max(m, n)) for addition. Space: O(1) extra (the sum's own nodes aside).

## 7. Copy a list with random pointers

**Problem.** Each node has `next` and a second pointer `random`, to any node in the list or `None`. Make a **deep copy**: new nodes with the same values, whose `next` and `random` point to the corresponding *new* nodes.

```text
original:   A(7) → B(13) → C(11) → None
random:     A → None,   B → A,   C → C
```

**Why one pass is not enough.** A random pointer can point *forward*, to a node not yet copied. We need "the copy of node X" for any X.

**With a hash map.** Pass 1 creates every copy and records `copy_of[old] = new`. Pass 2 sets `copy_of[X].next = copy_of[X.next]` and `copy_of[X].random = copy_of[X.random]`, with `None` mapping to `None`. O(n) time and O(n) memory for the map.

**O(1) extra space: interleave.** Store the mapping *inside the list*: put each copy right after its original, so "the copy of X" is `X.next`.

```text
step 1  weave copies in:       A → A' → B → B' → C → C' → None
step 2  random pointers:       X.next.random = X.random.next   (None stays None)
        A'.random = None,  B'.random = A.next = A',  C'.random = C.next = C'
step 3  unweave:               A → B → C → None   and   A' → B' → C' → None
```

Step 2 must finish for every node before step 3 starts: a random pointer may refer to a node that step 3 has already unwoven.

```python
import random


class Node:
    def __init__(self, val, next=None, rand=None):
        self.val, self.next, self.random = val, next, rand


def build(values, rand_idx):
    """rand_idx[i] is the position node i's random points to, or None."""
    nodes = [Node(v) for v in values]
    for i, node in enumerate(nodes):
        node.next = nodes[i + 1] if i + 1 < len(nodes) else None
        node.random = nodes[rand_idx[i]] if rand_idx[i] is not None else None
    return nodes[0] if nodes else None


def describe(head):
    """(values, random positions, node ids) of a list, for comparing structures."""
    nodes = []
    while head is not None:
        nodes.append(head)
        head = head.next
    pos = {id(n): i for i, n in enumerate(nodes)}
    rand = [pos[id(n.random)] if n.random is not None else None for n in nodes]
    return [n.val for n in nodes], rand, {id(n) for n in nodes}


def copy_with_map(head):
    copy_of = {None: None}
    curr = head
    while curr is not None:
        copy_of[curr] = Node(curr.val)
        curr = curr.next
    curr = head
    while curr is not None:
        copy_of[curr].next = copy_of[curr.next]
        copy_of[curr].random = copy_of[curr.random]
        curr = curr.next
    return copy_of[head]


def copy_interleave(head):
    if head is None:
        return None
    curr = head
    while curr is not None:                         # 1. weave: X → X' → next
        curr.next = Node(curr.val, curr.next)
        curr = curr.next.next
    curr = head
    while curr is not None:                         # 2. random pointers
        curr.next.random = curr.random.next if curr.random is not None else None
        curr = curr.next.next
    new_head, curr = head.next, head
    while curr is not None:                         # 3. unweave
        copy = curr.next
        curr.next = copy.next
        copy.next = copy.next.next if copy.next is not None else None
        curr = curr.next
    return new_head


def main():
    rng = random.Random(34)
    for copy in (copy_with_map, copy_interleave):
        assert copy(None) is None
        vals, rand, _ = describe(copy(build([7, 13, 11], [None, 0, 2])))
        assert vals == [7, 13, 11] and rand == [None, 0, 2]

        for _ in range(300):
            n = rng.randint(1, 10)
            values = [rng.randint(0, 5) for _ in range(n)]
            rand_idx = [rng.choice([None] + list(range(n))) for _ in range(n)]
            head = build(values, rand_idx)
            before = describe(head)
            c_vals, c_rand, c_ids = describe(copy(head))
            assert (c_vals, c_rand) == (values, rand_idx)
            assert describe(head) == before             # original restored
            assert not (c_ids & before[2])              # no shared nodes


if __name__ == "__main__":
    main()
```

Time: O(n) for both. Space: O(n) for the map versus O(1) extra (besides the copy) for interleaving.

## 8. Design: an LRU cache

**Problem.** Build a cache with a fixed `capacity`:

- `get(key)`: return the value, or `-1` if absent. Counts as a use.
- `put(key, value)`: insert or update. Counts as a use. If the cache now holds more than `capacity` keys, evict the **least recently used** (LRU) key.

Both in O(1) time.

**Brute force.** A Python list of keys ordered by last use; each use removes the key and appends it. `list.remove` is O(capacity): correct, too slow, and a good test oracle.

**Key observation.** Two abilities are needed at once:

1. Find a key's entry fast: a **dict**.
2. Keep entries in order of use, and move any entry to the front or remove the oldest in O(1): a **doubly linked list** with two sentinels ([chapter 1, §8](01-nodes-and-pointers.md#8-doubly-linked-lists)). Holding a node, unlinking it is O(1).

The dict maps each key to its node. The list runs from most recent (after the `head` sentinel) to least recent (before the `tail` sentinel). Each node also stores its key, so that evicting `tail.prev` can delete the key from the dict.

```text
dict:  { 1: ●, 2: ● }            each ● is a pointer to a node below
list:  head ⇄ [2:2] ⇄ [1:1] ⇄ tail
              newest        oldest
```

Trace with `capacity = 2`:

| Operation | Returns | List after (newest → oldest) | Note |
|---|---|---|---|
| `put(1, 1)`, `put(2, 2)` | | `[2:2] [1:1]` | each new node goes after `head` |
| `get(1)` | 1 | `[1:1] [2:2]` | unlink 1, relink after `head` |
| `put(3, 3)` | | `[3:3] [1:1]` | size 3 > 2: evict `tail.prev` = key 2 |
| `get(2)` | -1 | `[3:3] [1:1]` | not in dict |
| `put(1, 10)` | | `[1:10] [3:3]` | update value, move to front, no eviction |
| `put(4, 4)` | | `[4:4] [1:10]` | evict key 3 |

```python
import random


class DNode:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key=None, val=None):
        self.key, self.val = key, val
        self.prev = self.next = None


class LRUCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.nodes = {}                       # key -> DNode
        self.head, self.tail = DNode(), DNode()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            return -1
        self._unlink(node)
        self._push_front(node)
        return node.val

    def put(self, key, val):
        node = self.nodes.get(key)
        if node is not None:
            node.val = val
            self._unlink(node)
        else:
            node = DNode(key, val)
            self.nodes[key] = node
        self._push_front(node)
        if len(self.nodes) > self.capacity:
            oldest = self.tail.prev
            self._unlink(oldest)
            del self.nodes[oldest.key]       # why each node stores its key

    def keys_newest_first(self):
        out, curr = [], self.head.next
        while curr is not self.tail:
            out.append(curr.key)
            curr = curr.next
        return out


class BruteLRU:
    def __init__(self, capacity):
        self.capacity, self.order, self.data = capacity, [], {}

    def get(self, key):
        if key not in self.data:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.data[key]

    def put(self, key, val):
        if key in self.data:
            self.order.remove(key)
        self.order.append(key)
        self.data[key] = val
        if len(self.order) > self.capacity:
            del self.data[self.order.pop(0)]


def main():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    c.put(1, 10)
    c.put(4, 4)
    assert c.get(3) == -1 and c.get(4) == 4 and c.get(1) == 10
    assert c.keys_newest_first() == [1, 4]

    rng = random.Random(36)
    for _ in range(200):
        cap = rng.randint(1, 4)
        fast, slow = LRUCache(cap), BruteLRU(cap)
        for _ in range(60):
            key = rng.randint(0, 6)
            if rng.random() < 0.5:
                assert fast.get(key) == slow.get(key)
            else:
                val = rng.randint(0, 99)
                fast.put(key, val)
                slow.put(key, val)
            assert fast.keys_newest_first() == slow.order[::-1]


if __name__ == "__main__":
    main()
```

Time: O(1) per `get` and `put`. Space: O(capacity).

**Why it is correct.** Invariant: the list holds exactly the dict's keys, ordered by last use, newest first. Each use moves its key to the front and keeps the others' order, so `tail.prev` is always the least recently used key.

**In practice.** `collections.OrderedDict` is itself a dict plus a doubly linked list (`move_to_end`, `popitem(last=False)`), and `functools.lru_cache` uses the same design for memoization ([Dynamic Programming](../09-dynamic-programming/README.md)).

## 9. Advanced: an LFU cache

An **LFU** (least frequently used) cache evicts the key with the **fewest uses**; among keys tied on frequency, the least recently used. Still O(1) per operation.

Extend the LRU idea with one recency list **per frequency**:

- `entry`: `key → [value, freq]`.
- `buckets`: `freq → keys used exactly freq times`, oldest first. Each bucket is a small LRU list; `OrderedDict` plays the doubly linked list (`popitem(last=False)` removes the oldest).
- `min_freq`: the smallest frequency with any key. Eviction removes the oldest key of `buckets[min_freq]`.

Two rules keep `min_freq` correct without searching. A use moves a key from bucket `f` to `f + 1`; if bucket `f` empties and `f` was `min_freq`, then `min_freq = f + 1` (the moved key is there). A new key has frequency 1, so after inserting one, `min_freq = 1`.

Trace with `capacity = 2`:

| Operation | Buckets after (oldest first) | `min_freq` | Note |
|---|---|---:|---|
| `put(1, 1)`, `put(2, 2)` | f1: 1, 2 | 1 | |
| `get(1)` → 1 | f1: 2 · f2: 1 | 1 | 1 moves to bucket 2 |
| `put(3, 3)` | f1: 3 · f2: 1 | 1 | full: evict oldest of f1, key 2 |
| `get(3)` → 3 | f2: 1, 3 | 2 | bucket 1 emptied and was `min_freq` |
| `put(4, 4)` | f1: 4 · f2: 3 | 1 | full: evict oldest of f2, key 1 (tied with 3, older) |

The brute force stores `(value, freq, last_use_time)` per key and evicts the smallest `(freq, last_use_time)` by scanning.

```python
import random
from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.entry = {}                                  # key -> [value, freq]
        self.buckets = defaultdict(OrderedDict)          # freq -> keys, oldest first
        self.min_freq = 0

    def _touch(self, key):
        """Count one use of an existing key: move it from bucket f to f + 1."""
        f = self.entry[key][1]
        del self.buckets[f][key]
        if not self.buckets[f]:
            del self.buckets[f]
            if self.min_freq == f:
                self.min_freq = f + 1                    # the moved key lives there
        self.entry[key][1] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key):
        if key not in self.entry:
            return -1
        self._touch(key)
        return self.entry[key][0]

    def put(self, key, val):
        if key in self.entry:
            self.entry[key][0] = val
            self._touch(key)
            return
        if len(self.entry) == self.capacity:
            old, _ = self.buckets[self.min_freq].popitem(last=False)
            if not self.buckets[self.min_freq]:
                del self.buckets[self.min_freq]
            del self.entry[old]
        self.entry[key] = [val, 1]
        self.buckets[1][key] = None
        self.min_freq = 1                                # a new key has frequency 1


class BruteLFU:
    def __init__(self, capacity):
        self.capacity, self.data, self.clock = capacity, {}, 0

    def _use(self, key):
        self.clock += 1
        val, freq, _ = self.data[key]
        self.data[key] = (val, freq + 1, self.clock)

    def get(self, key):
        if key not in self.data:
            return -1
        self._use(key)
        return self.data[key][0]

    def put(self, key, val):
        if key in self.data:
            _, freq, t = self.data[key]
            self.data[key] = (val, freq, t)
            self._use(key)
            return
        if len(self.data) == self.capacity:
            victim = min(self.data, key=lambda k: self.data[k][1:])
            del self.data[victim]
        self.clock += 1
        self.data[key] = (val, 1, self.clock)


def main():
    c = LFUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)                      # evicts 2
    assert c.get(2) == -1
    assert c.get(3) == 3 and c.min_freq == 2
    c.put(4, 4)                      # evicts 1 (tied with 3 on freq 2, older)
    assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4

    rng = random.Random(37)
    for _ in range(300):
        cap = rng.randint(1, 4)
        fast, slow = LFUCache(cap), BruteLFU(cap)
        for _ in range(80):
            key = rng.randint(0, 6)
            if rng.random() < 0.5:
                assert fast.get(key) == slow.get(key)
            else:
                val = rng.randint(0, 99)
                fast.put(key, val)
                slow.put(key, val)
            assert set(fast.entry) == set(slow.data)


if __name__ == "__main__":
    main()
```

Time: O(1) per `get` and `put`. Space: O(capacity).

## 10. Summary

| Problem | Structure | Key step | Time | Extra space |
|---|---|---|---|---|
| Merge two sorted (§1) | dummy + `tail` | take the smaller front, `<=` for stability; attach the leftover in one move | O(m + n) | O(1) |
| Merge `k` sorted (§2) | heap of `(val, i, node)`, or merge in pairs | pop the smallest, push its successor | O(N log k) | O(k) |
| Sort (§3) | first middle, cut, merge | top-down recursion or bottom-up runs of 1, 2, 4, … | O(n log n) | O(log n) / O(1) |
| Partition (§4) | two dummies + two tails | cut the large list's tail, then join | O(n) | O(1) |
| Add two numbers (§5) | dummy + `tail` | `carry, digit = divmod(total, 10)`; loop while a list or the carry remains | O(max(m, n)) | O(1) besides the output |
| Reorder (§6) | split, reverse, weave | save both `next`s before relinking | O(n) | O(1) |
| Copy with random (§7) | map old → new, or weave `X → X'` | `X.next.random = X.random.next`; unweave last | O(n) | O(n) / O(1) |
| LRU cache (§8) | dict key → node + doubly linked list | move to front on use; evict `tail.prev` | O(1) per op | O(capacity) |
| LFU cache (§9) | dict + one recency list per frequency + `min_freq` | move to bucket `f + 1`; evict oldest in `min_freq` | O(1) per op | O(capacity) |

Every splice that redistributes nodes ends the same way: the last node of each new list gets `next = None`.

## 11. Pitfalls and practice

1. **Forgetting to cut.** Partition, merge-sort splitting, and reorder all redistribute nodes; the last node of each new list must get `next = None`, or an old pointer creates a cycle.
2. **Comparing nodes in a heap.** Push `(val, index, node)`, never `(val, node)`: on equal values Python would compare nodes and raise `TypeError`.
3. **Wrong middle in merge sort.** Use the first-middle loop, or two-node lists never shrink.
4. **Leftover carry.** In add-two-numbers, loop while either list *or the carry* remains.
5. **Unweaving too early.** In the interleaved copy, set every random pointer before unweaving anything.
6. **LRU node without its key.** Eviction finds the node at `tail.prev`; without `node.key` you cannot delete it from the dict.
7. **Updating an existing LRU key.** `put` on an existing key must update the value *and* move it to the front, without evicting anything.
8. **LFU `min_freq`.** Reset it to 1 after every insertion of a new key, and raise it only when its bucket empties during a use.

Practice: merge two sorted lists; merge k sorted lists; sort list; insertion sort list; partition list; add two numbers; add two numbers II; reorder list; copy list with random pointer; odd even linked list; LRU cache; LFU cache; design a browser history; all O(1) data structure.

Next: [Trees](../03-trees/README.md). A binary tree node is a list node with two `next` pointers (`left` and `right`); walking, the dummy, and "save before you overwrite" carry over unchanged. Back to the [Linked Lists overview](README.md).
