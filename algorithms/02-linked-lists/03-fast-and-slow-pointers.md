# Fast and Slow Pointers — Finding Positions by Moving at Different Speeds

## 1. The middle node

**Problem.** Return the middle node of a list. For `[1] → [2] → [3] → [4] → [5]` it is `[3]`.

**Brute force.** Walk once to count `n`, then walk `n // 2` steps. Two passes, O(1) memory; fine, but the one-pass idea below is the one that later finds cycles.

**Key observation.** Send two pointers from the head: `slow` moves one node per step, `fast` moves two. When `fast` reaches the end, `slow` has gone half as far.

**Invariant:** after `t` steps, `slow` is at position `t` and `fast` at position `2t`.

Trace on five nodes, loop `while fast is not None and fast.next is not None`:

| Step | `slow` | `fast` | Can `fast` move two more? |
|---:|---|---|---|
| 0 | `[1]` (pos 0) | `[1]` (pos 0) | yes |
| 1 | `[2]` (pos 1) | `[3]` (pos 2) | yes |
| 2 | `[3]` (pos 2) | `[5]` (pos 4) | no, `fast.next` is `None` → stop |

### Which middle for even lengths?

`[1] → … → [6]` has two middles, `[3]` and `[4]`, and the loop condition chooses:

| Loop condition (both start at `head`) | Stops `slow` at | Position | `n = 6` | `n = 5` |
|---|---|---|---|---|
| `while fast and fast.next` | the **second** middle | `n // 2` | `[4]` | `[3]` |
| `while fast.next and fast.next.next` | the **first** middle | `(n − 1) // 2` | `[3]` | `[3]` |

On six nodes both loops make the same two steps, reaching `slow = [3]`, `fast = [5]`. Then the first loop sees `fast.next = [6]` and moves once more (`slow = [4]`, `fast = None`), while the second sees `fast.next.next = None` and stops at `[3]`.

**Which to use?** The second middle is the usual answer to "return the middle node". The first middle is for **splitting**: `slow` is then the last node of the first half, and `slow.next = None` cuts cleanly. Merge sort in [chapter 4](04-merging-and-design.md#3-sort-a-list-with-merge-sort) and the palindrome check in [chapter 2](02-reversal.md#8-palindrome-linked-list) split this way. With the second-middle loop, a two-node list would "split" into two nodes and zero, and merge sort would recurse forever.

## 2. The k-th node from the end

**Problem.** Remove the `k`-th node from the end (`k = 1` is the last). `[1] → [2] → [3] → [4] → [5]` with `k = 2` loses `[4]`: `[1] → [2] → [3] → [5]`.

**Brute force.** Count `n`, then delete position `n − k`. Two passes.

**Key observation.** Keep two pointers a fixed **gap** apart. When the front one reaches the end, the back one is the same distance from the end. To delete we need the node **before** the target ([chapter 1, §5](01-nodes-and-pointers.md#5-deleting)), and the target may be the head, so start both at a dummy, move `lead` `k` steps ahead, then move both until `lead` is on the last node.

**Invariant:** after the head start, `lead` is exactly `k` nodes ahead of `trail`.

```text
start          trail = lead = dummy
head start     lead moves 2 steps: lead = [2]
together       ([1],[3])  ([2],[4])  ([3],[5])   lead.next is None → stop
delete         trail.next = trail.next.next      dummy → [1] → [2] → [3] → [5]
```

If `k = n`, the head start puts `lead` on the last node, the loop does not run, `trail` is the dummy, and the head is deleted. The dummy makes that case ordinary.

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


def nodes_of(head, limit=10_000):
    out = []
    while head is not None:
        if len(out) == limit:
            raise ValueError("list too long or has a cycle")
        out.append(head)
        head = head.next
    return out


def second_middle(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
    return slow


def first_middle(head):
    if head is None:
        return None
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    return slow


def remove_kth_from_end(head, k):
    if k < 1:
        raise ValueError("k must be at least 1")
    dummy = ListNode(0, head)
    trail = lead = dummy
    for _ in range(k):
        lead = lead.next
        if lead is None:
            raise ValueError("k is larger than the list length")
    while lead.next is not None:
        trail, lead = trail.next, lead.next
    trail.next = trail.next.next
    return dummy.next


def main():
    assert second_middle(from_list([1, 2, 3, 4, 5, 6])).val == 4
    assert first_middle(from_list([1, 2, 3, 4, 5, 6])).val == 3
    assert second_middle(None) is None and first_middle(None) is None
    assert remove_kth_from_end(from_list([1]), 1) is None
    try:
        remove_kth_from_end(from_list([1, 2]), 3)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(20)
    for _ in range(500):
        n = rng.randint(1, 30)
        values = [rng.randint(0, 9) for _ in range(n)]
        head = from_list(values)
        nodes = nodes_of(head)          # brute force: positions by counting
        assert second_middle(head) is nodes[n // 2]
        assert first_middle(head) is nodes[(n - 1) // 2]
        k = rng.randint(1, n)
        kept = [x.val for x in nodes_of(remove_kth_from_end(head, k))]
        assert kept == values[:n - k] + values[n - k + 1:]


if __name__ == "__main__":
    main()
```

Time: O(n), one pass each. Space: O(1).

## 3. Does the list have a cycle?

**Problem.** A pointer bug, or the problem itself, can make the last node point back to an earlier node instead of `None`. Decide whether such a cycle exists.

```text
[1] → [2] → [3] → [4] → [5] → [6]
             ↑                 │
             └─────────────────┘        the tail points back to [3]
```

**Brute force.** Store every visited node in a set; a repeat means a cycle, `None` means none. O(n) memory.

**Key observation (Floyd's algorithm, "tortoise and hare").** Run `slow` and `fast` from §1. Without a cycle, `fast` reaches `None`. With one, both end up going round it, and the faster catches the slower from behind. **They meet if and only if there is a cycle.**

### Why they must meet (and cannot jump over each other)

The **tail** before the cycle has `a` nodes; the cycle has `L` nodes. In the picture, `a = 2` and `L = 4`.

After `a` steps `slow` enters the cycle; `fast` is already inside. Let `d` be the distance from `fast` forward to `slow` along the cycle, `0 ≤ d < L`. Each step `slow` moves 1 forward (adding 1 to `d`) and `fast` moves 2 (subtracting 2): **`d` drops by exactly 1 per step.** It cannot skip over 0, so after `d` more steps they are on the same node. `fast` never "jumps over" `slow`.

Total steps before meeting: at most `a + L − 1 < n`. Detection is O(n) time, O(1) memory.

| Step | `slow` | `fast` | Note |
|---:|---|---|---|
| 0 | 1 | 1 | start |
| 1 | 2 | 3 | |
| 2 | 3 | 5 | `slow` enters; `d` = distance from 5 forward to 3 = 2 |
| 3 | 4 | 3 | 5 → 6 → 3; `d` = 1 |
| 4 | 5 | 5 | `d` = 0: **meet** |

## 4. Where does the cycle start?

**Problem.** Return the **entry**, the first node of the cycle (`[3]` above), or `None`.

Let `b` be the distance from the entry forward to the meeting point, and `c = L − b` from the meeting point forward back to the entry:

```text
 head                 entry
  ●──────── a ────────►●─────── b ───────┐
                       ▲                 ▼
                       │               meet
                       └─────── c ───────┘
```

When they meet, `slow` has walked `a + b` steps (it meets within its first lap, by §3). `fast` has walked `2(a + b)`, the same path plus `k ≥ 1` whole laps: `2(a + b) = a + b + kL`. So

$$
a+b=kL\quad\Longrightarrow\quad a=kL-b=(k-1)L+c.
$$

Read it as a walking instruction: **`a` steps from the head reach the entry, and `a` steps from the meeting point also reach the entry** (`c` steps to it, then `k − 1` whole laps). Put one pointer at the head, leave the other at the meeting point, move both one step at a time, and they meet at the entry.

Check: they met at `[5]`, so `b = 2`, `c = 2`, `a = 2`. From the head `[1] → [2] → [3]`; from the meeting point `[5] → [6] → [3]`. ✓ (`slow` walked 4 = `a + b`, `fast` 8 = `a + b + 1·L`, so `k = 1`.)

## 5. Cycle length

After the meeting, both pointers are on the cycle. Hold one still and walk the other around, counting: from `[5]` it visits `[6]`, `[3]`, `[4]`, `[5]`, so `L = 4`.

The script tests §3–§5 against a brute force that records the step at which each node is first seen:

```python
import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


def build_with_cycle(values, pos):
    """Build a list; if pos >= 0, the tail points back to the node at position pos."""
    nodes = [ListNode(v) for v in values]
    for x, y in zip(nodes, nodes[1:]):
        x.next = y
    if pos >= 0:
        nodes[-1].next = nodes[pos]
    return (nodes[0] if nodes else None), nodes


def meeting_point(head):
    """Floyd phase 1: the node where slow and fast meet, or None if no cycle."""
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return slow
    return None


def has_cycle(head):
    return meeting_point(head) is not None


def cycle_entry(head):
    meet = meeting_point(head)
    if meet is None:
        return None
    p, q = head, meet
    while p is not q:              # both walk a steps
        p, q = p.next, q.next
    return p


def cycle_length(head):
    meet = meeting_point(head)
    if meet is None:
        return 0
    length, curr = 1, meet.next
    while curr is not meet:
        length += 1
        curr = curr.next
    return length


def brute(head):
    """Return (entry, length) using a dict of first-visit steps; (None, 0) if no cycle."""
    first_seen, step, curr = {}, 0, head
    while curr is not None:
        if curr in first_seen:
            return curr, step - first_seen[curr]
        first_seen[curr] = step
        step, curr = step + 1, curr.next
    return None, 0


def main():
    head, nodes = build_with_cycle([1, 2, 3, 4, 5, 6], 2)
    assert meeting_point(head) is nodes[4]          # they meet at [5]
    assert cycle_entry(head) is nodes[2]            # entry [3]
    assert cycle_length(head) == 4
    assert not has_cycle(None)

    rng = random.Random(22)
    for _ in range(1000):
        n = rng.randint(1, 25)
        pos = rng.randint(-1, n - 1)
        head, nodes = build_with_cycle(list(range(n)), pos)
        entry, length = brute(head)
        assert has_cycle(head) == (pos >= 0)
        assert cycle_entry(head) is entry
        assert cycle_length(head) == length


if __name__ == "__main__":
    main()
```

Time: O(n) each. Space: O(1), versus O(n) for the brute force. Note `slow is fast` compares nodes; `slow.val == fast.val` would report a cycle whenever two different nodes hold equal values.

## 6. Where do two lists meet?

**Problem.** Two lists may merge into a shared tail. Return the first shared **node** (by identity), or `None`.

```text
A:    [4] → [1] ─┐
                 ▼
                [8] → [4] → [5] → None        shared tail
                 ▲
B: [5] → [6] → [1] ─┘
```

**Brute force.** Put A's nodes in a set; walk B and return the first node in the set. O(m) memory.

**Key observation.** If the private parts had equal length, a lockstep walk would hit the shared node together. Make them equal: walk A then B with one pointer, B then A with the other. With `a`, `b` the private lengths and `c` the shared tail (`a = 2`, `b = 3`, `c = 3`):

- `pa` walks `a + c`, then `b`, reaching the shared node after **`a + c + b`** moves (plus one for the `None` step at the switch);
- `pb` walks `b + c`, then `a`: **`b + c + a`**, the same.

So they arrive together. With no shared tail (`c = 0`), both reach `None` at the same moment and the loop returns `None`. The code moves to the other head when the pointer *is* `None`, which makes `None` one step of each walk; that is what lines up the no-intersection case.

| Step | `pa` | `pb` |
|---:|---|---|
| 0 | A:4 | B:5 |
| 3 | shared 4 | shared 8 |
| 5 | `None` | shared 5 |
| 6 | B:5 | `None` |
| 7 | B:6 | A:4 |
| 9 | **shared 8** | **shared 8** |

At step 3, `pb` was on shared `8` while `pa` was not: meeting needs the same node at the same step, which first happens at step 9 = `a + b + c + 1`. That bound is also why the loop cannot run forever.

**Alternative.** Measure both lengths, advance the longer list's pointer by the difference, then walk in lockstep. Same cost, more code.

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


def build_pair(a_vals, b_vals, shared_vals):
    shared = from_list(shared_vals)
    def attach(vals):
        head = from_list(vals)
        if head is None:
            return shared
        tail = head
        while tail.next is not None:
            tail = tail.next
        tail.next = shared
        return head
    return attach(a_vals), attach(b_vals), shared


def intersection(head_a, head_b):
    pa, pb = head_a, head_b
    while pa is not pb:
        pa = pa.next if pa is not None else head_b
        pb = pb.next if pb is not None else head_a
    return pa


def brute(head_a, head_b):
    seen = set()
    while head_a is not None:
        seen.add(head_a)
        head_a = head_a.next
    while head_b is not None:
        if head_b in seen:
            return head_b
        head_b = head_b.next
    return None


def main():
    a, b, shared = build_pair([4, 1], [5, 6, 1], [8, 4, 5])
    assert intersection(a, b) is shared
    a, b, _ = build_pair([1, 2], [1, 2], [])     # equal values, no shared node
    assert intersection(a, b) is None
    assert intersection(None, None) is None

    rng = random.Random(23)
    for _ in range(1000):
        lens = [rng.randint(0, 6) for _ in range(3)]
        a_vals, b_vals, s_vals = ([rng.randint(0, 3) for _ in range(k)] for k in lens)
        a, b, shared = build_pair(a_vals, b_vals, s_vals)
        assert intersection(a, b) is brute(a, b) is shared


if __name__ == "__main__":
    main()
```

Time: O(m + n). Space: O(1).

## 7. Advanced: find the duplicate number as a cycle

**Problem.** An array `nums` has `n + 1` entries, each in `1 … n`, so some value repeats; exactly one value repeats (possibly many times). Find it **without modifying the array** and with O(1) extra memory. For `[1, 3, 4, 2, 2]` the answer is 2.

**Brute force.** A set finds it in O(n) time and O(n) memory; sorting in place modifies the array.

**Key observation.** Treat each index as a node with an arrow `i → nums[i]`. Every value is in `1 … n`, so every arrow lands on a valid index and the walk `0 → nums[0] → nums[nums[0]] → …` never ends. On finitely many nodes an endless walk must repeat: this is a linked list with a cycle, where `next(i) = nums[i]`.

```text
index:   0    1    2    3    4
nums:    1    3    4    2    2

walk:    0 → 1 → 3 → 2 → 4
                     ↑    │
                     └────┘      cycle 2 → 4 → 2, entry 2
```

**Why the entry is the duplicate.** The entry has two incoming arrows: one from the tail and one from the cycle's last node. Two indices `i ≠ j` with `nums[i] = nums[j] = entry` means the entry value is repeated. The tail is not empty, because no value is 0, so index 0 has no incoming arrow and cannot be on the cycle. Only the duplicate value has two incoming arrows, so the entry is exactly the duplicate.

Run §3 and §4 with `slow = nums[slow]` and `fast = nums[nums[fast]]`:

```text
phase 1, from slow = fast = 0
  step 1   slow = 1     fast = nums[nums[0]] = nums[1] = 3
  step 2   slow = 3     fast = nums[nums[3]] = nums[2] = 4
  step 3   slow = 2     fast = nums[nums[4]] = nums[2] = 4
  step 4   slow = 4     fast = nums[nums[4]] = 4       meet at index 4

phase 2, p = 0, q = 4
  step 1   p = 1        q = nums[4] = 2
  step 2   p = 3        q = nums[2] = 4
  step 3   p = 2        q = nums[4] = 2       meet: the duplicate is 2
```

```python
import random
from collections import Counter


def find_duplicate(nums):
    n = len(nums) - 1
    if n < 1 or any(not 1 <= v <= n for v in nums):
        raise ValueError("need n + 1 values, each in 1..n")
    slow = fast = 0
    while True:                     # phase 1: meet inside the cycle
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    p = 0
    while p != slow:                # phase 2: both walk a steps to the entry
        p = nums[p]
        slow = nums[slow]
    return p


def brute(nums):
    return next(v for v, c in Counter(nums).items() if c > 1)


def main():
    assert find_duplicate([1, 3, 4, 2, 2]) == 2
    assert find_duplicate([3, 1, 3, 4, 2]) == 3
    assert find_duplicate([1, 1]) == 1
    assert find_duplicate([2, 2, 2, 2, 2]) == 2
    try:
        find_duplicate([0, 1])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = random.Random(24)
    for _ in range(2000):
        n = rng.randint(1, 12)
        d = rng.randint(1, n)
        nums = list(range(1, n + 1)) + [d]
        for i in range(len(nums)):          # overwrite some values with d
            if rng.random() < 0.3:
                nums[i] = d
        rng.shuffle(nums)
        before = nums[:]
        assert find_duplicate(nums) == brute(nums) == d
        assert nums == before               # the array was not modified


if __name__ == "__main__":
    main()
```

Time: O(n). Space: O(1).

The same problem also falls to binary search on the answer ("how many values are at most `m`?") in O(n log n); see [Binary Search](../01-binary-search/README.md). The cycle view is faster, and shows that "linked list" can mean any function from a finite set to itself. The "happy number" problem is another: repeatedly summing the squares of the digits either reaches 1 or loops, and Floyd detects the loop with no set.

## 8. Summary

| Question | Pointers | Loop | Ends with |
|---|---|---|---|
| Second middle (§1) | `slow` +1, `fast` +2 from `head` | `while fast and fast.next` | `slow` at position `n // 2` |
| First middle, to split (§1) | same | `while fast.next and fast.next.next` | `slow` at `(n − 1) // 2`, the last node of the first half |
| Remove `k`-th from end (§2) | `lead` `k` steps ahead of `trail`, both from a dummy | `while lead.next` | `trail` right before the target |
| Is there a cycle? (§3) | `slow` +1, `fast` +2 | move, then compare `slow is fast` | meet ⇔ cycle |
| Cycle entry (§4) | one at `head`, one at the meeting point, both +1 | `while p is not q` | the entry, because `a = (k − 1)L + c` |
| Cycle length (§5) | one still, one walks around | until back at the meeting point | `L` |
| Intersection (§6) | `pa`, `pb`, switch heads after `None` | `while pa is not pb` | shared node or `None` after `a + b + c + 1` moves |
| Duplicate in `1 … n` (§7) | `i → nums[i]` as `next`, Floyd from index 0 | §3 then §4 | the duplicate value |

The two proofs to remember: in a cycle the gap from `fast` to `slow` shrinks by exactly 1 per step, so they cannot jump over each other; and `a + b = kL` gives `a = (k − 1)L + c`, so `a` steps from the head and from the meeting point both land on the entry.

## 9. Pitfalls and practice

1. **Null checks on `fast`.** `fast.next.next` needs both `fast` and `fast.next` to exist. Check them in that order: `while fast is not None and fast.next is not None`.
2. **Wrong middle.** Splitting with the second-middle loop leaves a two-node list unsplit and makes recursive algorithms loop forever. Use the first-middle loop for splitting.
3. **Starting the meeting check too early.** Both pointers start at `head`, so checking `slow is fast` before the first move reports a cycle in every list. Move first, then compare.
4. **Comparing values instead of nodes.** Use `is` for nodes; equal values do not mean the same node.
5. **Off-by-one in the gap.** For removing the `k`-th from the end, start both pointers at a dummy and give `lead` exactly `k` steps; then stop when `lead.next` is `None`.
6. **Forgetting the `None` step in the switch-heads trick.** Switching to the other head *when the pointer becomes `None`* (not when `next` is `None`) is what makes the no-intersection case terminate.
7. **Find-the-duplicate starting at index 0.** Index 0 is outside the cycle because no value is 0. Starting at another index can begin inside the cycle and return the wrong value.

Practice: middle of the linked list; remove the N-th node from end of list; linked list cycle; linked list cycle II; intersection of two linked lists; find the duplicate number; happy number; delete the middle node of a linked list; circular array loop.

Next: [Merging and Design](04-merging-and-design.md).
