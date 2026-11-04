# Reversal — Turning Arrows Around Without Losing the List

## 1. Reverse a list

Turn `[1] → [2] → [3] → [4] → None` into `[4] → [3] → [2] → [1] → None` and return the new head.

**Brute force.** Copy the values into a Python list, reverse it, and write them back: O(n) extra memory, and some problems forbid changing values, only links.

**Key observation.** The nodes do not move. Only the arrows change direction:

```text
before   [1] → [2] → [3] → [4] → None
after    None ← [1] ← [2] ← [3] ← [4]
                                   ↑ new head
```

Flipping one arrow means `curr.next = prev`. But `curr.next` was the only way to reach the rest of the list; overwrite it and `[2] → [3] → [4]` is gone. So save it first in a third variable, `nxt` (the "connect before you overwrite" rule of [Nodes and Pointers](01-nodes-and-pointers.md#4-inserting)).

## 2. Iterative reversal, one arrow per step

**State.** `prev` is the head of the **reversed part** (nodes already flipped); `curr` is the head of the **rest** (nodes not yet touched).

**Invariant:** the reversed part holds the nodes before `curr`, in reverse order; the rest is unchanged.

Each step moves one node from the front of the rest to the front of the reversed part:

```text
nxt = curr.next      save the rest
curr.next = prev     flip the arrow
prev = curr          the reversed part grows by one
curr = nxt           the rest shrinks by one
```

Trace on `[1] → [2] → [3] → [4]`:

| Step | `nxt` | Arrow flipped | Reversed part (`prev`) | Rest (`curr`) |
|---:|---|---|---|---|
| start | | | `None` | `[1] → [2] → [3] → [4]` |
| 1 | `[2]` | `[1] → None` | `[1]` | `[2] → [3] → [4]` |
| 2 | `[3]` | `[2] → [1]` | `[2] → [1]` | `[3] → [4]` |
| 3 | `[4]` | `[3] → [2]` | `[3] → [2] → [1]` | `[4]` |
| 4 | `None` | `[4] → [3]` | `[4] → [3] → [2] → [1]` | `None`: stop, return `prev` |

**Why it is correct.** At the end the rest is empty, so by the invariant the reversed part holds every node in reverse order.

**Without `nxt`**, step 1 sets `[1].next = None`, nothing points to `[2]` any more, `curr = [1].next = None`, and the loop stops with a one-node list. **Return `prev`, not `curr`:** at the end `curr` is `None`, and the old tail, the new head, is in `prev`.

## 3. Recursive reversal

Reverse everything after the head, then attach the head at the end. The trick is finding "the end": after the recursive call reverses `[2] → [3]`, node `[2]` is the tail of the reversed part, and `head.next` still points to it. So `head.next.next = head` hangs `[1]` after `[2]`, and `head.next = None` makes `[1]` the new tail.

```text
reverse([1] → [2] → [3])
  reverse([2] → [3])
    reverse([3])           one node: return [3]
  head = [2]:  [2].next.next = [2]  gives [3] → [2];  [2].next = None    return [3]
head = [1]:    [1].next.next = [1]  gives [2] → [1];  [1].next = None    return [3]
result: [3] → [2] → [1] → None
```

Every level returns the same `new_head`, the old tail found at the bottom. The recursion is `n` levels deep: O(n) stack, and Python raises `RecursionError` beyond roughly 1000 levels. Prefer the iterative loop; the recursive one is worth knowing because "fix up after the call returns" is the shape of most [tree](../03-trees/README.md) recursions.

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


def nodes_of(head, limit=100_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head)
        head = head.next
    return out


def reverse_iterative(head):
    prev, curr = None, head
    while curr is not None:
        nxt = curr.next      # save the rest
        curr.next = prev     # flip one arrow
        prev = curr
        curr = nxt
    return prev


def reverse_recursive(head):
    if head is None or head.next is None:
        return head
    new_head = reverse_recursive(head.next)
    head.next.next = head    # hang head after its old successor
    head.next = None         # head is now the tail
    return new_head


def main():
    assert reverse_iterative(None) is None
    rng = random.Random(10)
    for _ in range(300):
        values = [rng.randint(0, 9) for _ in range(rng.randint(0, 15))]
        for reverse in (reverse_iterative, reverse_recursive):
            head = from_list(values)
            original = nodes_of(head)
            # In place: the same node objects, only relinked.
            assert nodes_of(reverse(head)) == original[::-1]
    assert len(nodes_of(reverse_iterative(from_list(list(range(5000)))))) == 5000


if __name__ == "__main__":
    main()
```

Time: O(n) for both. Space: O(1) iterative, O(n) call stack recursive.

## 4. Reverse a range of positions

**Problem.** Reverse the nodes at zero-based positions `left` through `right` (inclusive). With `[1] → [2] → [3] → [4] → [5]`, `left = 1`, `right = 3`: `[1] → [4] → [3] → [2] → [5]`. (The well-known version counts from 1; subtract one.)

**Key observation.** Run the §2 loop for exactly `right − left + 1` nodes, then repair two **seams**. Remember:

- `before`: the node right before the range. It does not exist when `left = 0`, so start from a dummy.
- `first`: the first node of the range. After reversal it is the **last**, and must point to whatever followed the range.

```text
start          dummy → [1] → [2] → [3] → [4] → [5] → None
                        ↑     ↑
                     before  first

after loop     prev = [4] (new front of the range), curr = [5] (node after the range)
               range is [4] → [3] → [2] → None;  [1] still points at [2]

seam 1         before.next = prev        [1] → [4]
seam 2         first.next = curr         [2] → [5]

result         dummy → [1] → [4] → [3] → [2] → [5] → None
```

## 5. Reverse in groups of k

**Problem.** Reverse every consecutive block of `k` nodes; a final block shorter than `k` stays as it is. `[1] → [2] → [3] → [4] → [5]` with `k = 2` gives `[2] → [1] → [4] → [3] → [5]`.

**Key observation.** Each group is a §4 range. Before reversing it, walk `k` steps from `group_prev` (the node right before the group, initially the dummy) to a scout `kth`; if the walk falls off the end, stop.

One change removes a seam: start `prev` at `kth.next`, the first node **after** the group, instead of `None`. The group's new tail then already points to the next group, and only the front needs `group_prev.next = kth`.

```text
group 1   group_prev = dummy, kth = [2], first = [1], prev starts at [3]
          after the loop: [2] → [1] → [3];  dummy.next = [2];  group_prev = [1]
          dummy → [2] → [1] → [3] → [4] → [5]

group 2   kth = [4], first = [3], prev starts at [5]
          [4] → [3] → [5];  [1].next = [4];  group_prev = [3]
          dummy → [2] → [1] → [4] → [3] → [5]

group 3   from [3]: [5], then None → fewer than k nodes, stop
```

## 6. Swap nodes in pairs

**Problem.** Swap every two adjacent nodes (the nodes, not the values): `[1] → [2] → [3] → [4]` becomes `[2] → [1] → [4] → [3]`.

This is `k = 2`, but three assignments per pair do it directly. With `prev` before the pair `a`, `b`:

```text
before    prev → [a] → [b] → [rest...]

step 1    a.next = b.next          [a] → [rest...]      (saves the rest first)
step 2    b.next = a               [b] → [a]
step 3    prev.next = b            prev → [b]

after     prev → [b] → [a] → [rest...];  then prev = a
```

One script tests §4–§6 against Python-list slicing:

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


def to_list(head, limit=10_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def reverse_between(head, left, right):
    """Reverse zero-based positions left..right inclusive. Return the new head."""
    if left < 0 or right < left:
        raise ValueError("need 0 <= left <= right")
    dummy = ListNode(0, head)
    before = dummy
    for _ in range(left):
        before = before.next
        if before is None:
            raise ValueError("left is past the end")
    first = before.next
    prev, curr = None, first
    for _ in range(right - left + 1):
        if curr is None:
            raise ValueError("right is past the end")
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    before.next = prev    # front seam
    first.next = curr     # back seam
    return dummy.next


def reverse_k_group(head, k):
    if k < 1:
        raise ValueError("k must be positive")
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next
            if kth is None:
                return dummy.next          # fewer than k nodes remain
        first = group_prev.next
        prev, curr = kth.next, first       # reversed tail will point past the group
        for _ in range(k):
            nxt = curr.next
            curr.next = prev
            prev, curr = curr, nxt
        group_prev.next = kth              # kth is the group's new front
        group_prev = first                 # first is the group's new back


def swap_pairs(head):
    dummy = ListNode(0, head)
    prev = dummy
    while prev.next is not None and prev.next.next is not None:
        a, b = prev.next, prev.next.next
        a.next = b.next
        b.next = a
        prev.next = b
        prev = a
    return dummy.next


def brute_k_group(values, k):
    out = []
    for i in range(0, len(values), k):
        block = values[i:i + k]
        out += block[::-1] if len(block) == k else block
    return out


def main():
    assert to_list(reverse_between(from_list([1, 2, 3, 4, 5]), 1, 3)) == [1, 4, 3, 2, 5]
    assert to_list(reverse_k_group(from_list([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert to_list(swap_pairs(from_list([1, 2, 3, 4]))) == [2, 1, 4, 3]
    assert swap_pairs(None) is None
    for bad in ((2, 1), (0, 3), (-1, 0)):
        try:
            reverse_between(from_list([1, 2, 3]), *bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    rng = random.Random(11)
    for _ in range(500):
        values = [rng.randint(0, 9) for _ in range(rng.randint(0, 14))]
        k = rng.randint(1, 6)
        assert to_list(reverse_k_group(from_list(values), k)) == brute_k_group(values, k)
        assert to_list(swap_pairs(from_list(values))) == brute_k_group(values, 2)
        if values:
            left = rng.randrange(len(values))
            right = rng.randrange(left, len(values))
            expected = values[:left] + values[left:right + 1][::-1] + values[right + 1:]
            assert to_list(reverse_between(from_list(values), left, right)) == expected


if __name__ == "__main__":
    main()
```

Time: O(n) for each (`reverse_k_group` walks each node twice: once with the scout, once reversing). Space: O(1). A recursive k-group (reverse the first `k`, recurse on the rest) is shorter but uses O(n / k) stack frames.

## 7. Rotate a list

**Problem.** Rotate right by `k` places: the last `k` nodes move to the front. `[1] → [2] → [3] → [4] → [5]` with `k = 2` gives `[4] → [5] → [1] → [2] → [3]`. Rotating by `n` gives the same list back, so only `k mod n` matters, and `k` can be huge.

**Key observation.** Rotation reverses nothing: it cuts the list at one point and swaps the two pieces. Join the tail to the head to make a ring, then cut the ring after the new tail, at position `n − k − 1`.

```text
step 1   walk to the tail and count:   n = 5, tail = [5]
step 2   tail.next = head              ring: [1] → [2] → [3] → [4] → [5] → back to [1]
step 3   walk n − k − 1 = 2 steps from head: new_tail = [3], new_head = [4]
step 4   new_tail.next = None          [4] → [5] → [1] → [2] → [3] → None
```

Skip step 4 and the list stays a ring: every later walk never ends.

## 8. Palindrome linked list

**Problem.** Does the list read the same forwards and backwards? `[1] → [2] → [3] → [2] → [1]` yes; `[1] → [2] → [2] → [3]` no.

**Brute force.** Compare the values with their reverse: O(n) extra memory.

**Key observation.** A singly linked list cannot walk backwards, but we can **reverse the second half** and walk both halves forward. Afterwards, reverse it back: leaving the caller's input damaged is a bug even when the answer is right.

1. Find the last node of the first half, `slow`, with the first-middle loop of [Fast and Slow Pointers](03-fast-and-slow-pointers.md#1-the-middle-node) (`slow` +1, `fast` +2, `while fast.next and fast.next.next`). For odd length the middle node counts as the first half.
2. `second = reverse(slow.next)`.
3. Compare from `head` and from `second` until `second`'s side runs out (it is never longer).
4. `slow.next = reverse(second)` to restore.

```text
step 1   slow stops on [3]:   first half [1] → [2] → [3],  second half [2] → [1]
step 2   second = [1] → [2] → None      ([3] still points at the old 4th node, now a tail)
step 3   1 = 1, 2 = 2, second side ends → palindrome
step 4   reverse back, slow.next = [2] → [1]:  [1] → [2] → [3] → [2] → [1]
```

For even `[1] → [2] → [2] → [1]`, `slow` stops on the first `[2]` and the halves are `[1] → [2]` and `[2] → [1]`.

One script tests §7 and §8:

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


def to_list(head, limit=10_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def reverse(head):
    prev, curr = None, head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    return prev


def rotate_right(head, k):
    if k < 0:
        raise ValueError("k must be nonnegative")
    if head is None:
        return None
    n, tail = 1, head
    while tail.next is not None:
        tail = tail.next
        n += 1
    k %= n
    if k == 0:
        return head
    tail.next = head                  # make a ring
    new_tail = head
    for _ in range(n - k - 1):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None              # cut the ring
    return new_head


def is_palindrome(head):
    if head is None or head.next is None:
        return True
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = reverse(slow.next)          # slow is the last node of the first half
    p1, p2, answer = head, second, True
    while p2 is not None:
        if p1.val != p2.val:
            answer = False
            break
        p1, p2 = p1.next, p2.next
    slow.next = reverse(second)          # restore the input
    return answer


def main():
    assert to_list(rotate_right(from_list([1, 2, 3, 4, 5]), 2)) == [4, 5, 1, 2, 3]
    assert to_list(rotate_right(from_list([0, 1, 2]), 4)) == [2, 0, 1]
    assert rotate_right(None, 3) is None
    assert is_palindrome(from_list([1, 2, 3, 2, 1]))
    assert not is_palindrome(from_list([1, 2, 2, 3]))
    assert is_palindrome(None) and is_palindrome(from_list([5]))

    rng = random.Random(13)
    for _ in range(1000):
        n = rng.randint(0, 9)
        values = [rng.randint(0, 2) for _ in range(n)]
        if rng.random() < 0.5:           # force some palindromes
            values = values[: (n + 1) // 2] + values[: n // 2][::-1]
        head = from_list(values)
        assert is_palindrome(head) == (values == values[::-1])
        assert to_list(head) == values   # the list is restored
        if values:
            k = rng.randint(0, 25)
            r = k % len(values)
            expected = values[-r:] + values[:-r] if r else values
            assert to_list(rotate_right(from_list(values), k)) == expected


if __name__ == "__main__":
    main()
```

Time: O(n) for both. Space: O(1).

**Variant: maximum twin sum.** In a list of even length `n`, nodes `i` and `n − 1 − i` are "twins". Steps 1 to 3 with a running maximum of `p1.val + p2.val` find the largest twin sum.

## 9. Summary

Every operation here is the four-line loop plus some seams to reconnect:

```text
nxt = curr.next      # save the rest
curr.next = prev     # flip one arrow
prev = curr          # reversed part grows
curr = nxt           # rest shrinks
```

| Operation | `prev` starts at | Loop runs | Seams to reconnect afterwards |
|---|---|---|---|
| Whole list (§2) | `None` | until `curr is None` | none; return `prev` |
| Range `left..right` (§4) | `None` | `right − left + 1` times | `before.next = prev`, `first.next = curr` |
| Group of `k` (§5) | `kth.next` | `k` times | `group_prev.next = kth` only |
| Pair (§6) | — | three assignments | `a.next = b.next`, `b.next = a`, `prev.next = b` |
| Rotate (§7) | — | no reversal | ring `tail.next = head`, cut `new_tail.next = None` |
| Palindrome (§8) | `None`, from the second half | until `None` | reverse back and set `slow.next` |

Recursive reversal (§3) costs O(n) stack; everything else is O(1) extra space.

## 10. Pitfalls and practice

1. **Losing the next pointer.** Always `nxt = curr.next` before `curr.next = prev`. Writing the four reversal lines in any other order breaks the list.
2. **Returning `curr` instead of `prev`** after a full reversal. `curr` is `None` at the end.
3. **Forgetting a seam.** A reversed range has two (`before.next` and `first.next`); fixing only one leaves either a lost tail or a cycle.
4. **Forgetting to cut.** Rotation builds a ring on purpose. If the cut is missed, every later walk loops forever. Test helpers with a step limit catch this.
5. **Off-by-one in counts.** `reverse_between` reverses `right − left + 1` nodes; rotation walks `n − k − 1` steps. Check both on a list of length 1 and on `k = 0`, `k = n`, `k > n`.
6. **Leaving the input modified.** After using a reversed half for a check, reverse it back.
7. **Recursion depth.** Recursive reversal fails on long lists in Python; the iterative loop does not.

Practice: reverse linked list; reverse linked list II; reverse nodes in k-group; swap nodes in pairs; rotate list; palindrome linked list; maximum twin sum of a linked list; reverse nodes in even-length groups.

Next: [Fast and Slow Pointers](03-fast-and-slow-pointers.md).
