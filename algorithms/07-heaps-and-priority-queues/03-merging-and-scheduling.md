# Merging and Scheduling — A Heap as the Next-Event Chooser

## 1. Merge k sorted lists

**Problem.** Given `k` sorted lists, produce one sorted list of all their items. For `[[1, 4, 5], [1, 3, 4], [2, 6]]` the answer is `[1, 1, 2, 3, 4, 4, 5, 6]`.

**Brute force.** Concatenate and sort: O(N log N) for `N` items in total. It ignores that each list is already sorted. Merging lists one after another into a growing result is worse: the result is re-copied `k` times, O(N · k).

**Key observation.** The next output item is the smallest of the `k` current fronts. Only `k` values compete at any moment, and after one front is taken, only its successor in the same list joins the competition.

**Invariant.** The heap holds exactly one entry `(value, list index, position)` for each list that is not used up: its current front.

**Trace.** Entries are `(value, list, position)`.

| Pop | Output so far | Push (successor) | Heap afterwards |
|---|---|---|---|
| start | `[]` | | `(1,0,0) (1,1,0) (2,2,0)` |
| `(1,0,0)` | `[1]` | `(4,0,1)` | `(1,1,0) (2,2,0) (4,0,1)` |
| `(1,1,0)` | `[1, 1]` | `(3,1,1)` | `(2,2,0) (3,1,1) (4,0,1)` |
| `(2,2,0)` | `[1, 1, 2]` | `(6,2,1)` | `(3,1,1) (4,0,1) (6,2,1)` |
| … | | | |
| `(6,2,1)` | `[1, 1, 2, 3, 4, 4, 5, 6]` | list 2 done | empty |

The rows in between repeat the same move; when a list runs out, nothing is pushed for it. The list index in each tuple breaks ties between equal values (the two 1s above), so the heap never compares anything else. For **linked lists** the entry is `(value, list index, node)`, so equal values never reach a node comparison; that version is coded and tested in [Linked Lists: merge k sorted lists](../02-linked-lists/04-merging-and-design.md#2-merge-k-sorted-lists). Python's `heapq.merge(*lists)` does the same for any sorted iterables, lazily.

```python
import heapq
import random


def merge_k_arrays(lists):
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    out = []
    while heap:
        value, i, j = heapq.heappop(heap)
        out.append(value)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    return out


def main():
    lists = [[1, 4, 5], [1, 3, 4], [2, 6]]
    assert merge_k_arrays(lists) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_arrays([]) == [] and merge_k_arrays([[], []]) == []
    rng = random.Random(21)
    for _ in range(500):
        lists = [sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 6)))
                 for _ in range(rng.randint(0, 6))]
        expected = sorted(x for lst in lists for x in lst)
        assert merge_k_arrays(lists) == expected
        assert list(heapq.merge(*lists)) == expected  # The standard library version.


if __name__ == "__main__":
    main()
```

O(N log k) time, O(k) extra space besides the output. Merging lists in pairs, like the merge step of merge sort, has the same bound and is the other standard answer.

## 2. The k-th smallest value in a sorted matrix

**Problem.** In an `n × n` matrix whose rows and columns are both sorted ascending, find the `k`-th smallest value (counting duplicates). For

```text
 1   5   9
10  11  13
12  13  15
```

and `k = 8` the sorted values are `1 5 9 10 11 12 13 13 15`, so the answer is **13**.

**Key observation.** Each row is a sorted list, so this is §1 stopped after `k` outputs. Seed the heap with the first column; when `(r, c)` is popped, push its right neighbor `(r, c + 1)`. On the example the pops come out `1, 5, 9, 10, 11, 12, 13` (the trace has the same shape as §1's), and after those `k − 1 = 7` pops the root is the 8th smallest: `(13, 2, 1)`, value 13.

```python
import heapq
import random


def kth_smallest_matrix(matrix, k):
    n = len(matrix)
    if not 1 <= k <= n * n:
        raise ValueError("need 1 <= k <= n*n")
    heap = [(matrix[r][0], r, 0) for r in range(min(n, k))]
    heapq.heapify(heap)
    for _ in range(k - 1):
        _, r, c = heapq.heappop(heap)
        if c + 1 < n:
            heapq.heappush(heap, (matrix[r][c + 1], r, c + 1))
    return heap[0][0]


def random_sorted_matrix(n, rng):
    m = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            up = m[r - 1][c] if r else -5
            left = m[r][c - 1] if c else -5
            m[r][c] = max(up, left) + rng.randint(0, 3)
    return m


def main():
    m = [[1, 5, 9], [10, 11, 13], [12, 13, 15]]
    assert kth_smallest_matrix(m, 8) == 13
    assert kth_smallest_matrix([[-5]], 1) == -5
    rng = random.Random(22)
    for _ in range(500):
        n = rng.randint(1, 6)
        m = random_sorted_matrix(n, rng)
        flat = sorted(x for row in m for x in row)
        k = rng.randint(1, n * n)
        assert kth_smallest_matrix(m, k) == flat[k - 1]


if __name__ == "__main__":
    main()
```

O(n + k log n) time, O(n) space. Only `min(n, k)` rows are ever seeded, because rows below the `k`-th cannot contribute to the first `k` values through their first column. When `k` is near `n²`, **binary search on the answer** is faster: guess a value, count entries `≤` it with a staircase walk in O(n), and narrow the range, for O(n log(max − min)) total ([Binary Search](../01-binary-search/README.md)).

## 3. Smallest range covering k lists

**Problem.** Given `k` sorted lists, find the smallest range `[lo, hi]` (inclusive) that contains at least one value from every list. Smaller means smaller `hi − lo`, and on a tie, smaller `lo`. For `[[1, 5, 8], [4, 12], [7, 8, 10]]` the answer is `[4, 7]`: 4 from list 1, 5 from list 0, 7 from list 2.

**Brute force.** Try every pair of values as `(lo, hi)` and check each list with binary search: O(N² · k log N).

**Key observation.** Pick one value from each list. The range they span is `[min, max]`. To improve it, the only useful move is to raise the **minimum**: lowering the max is impossible without losing a list, and raising anything else only widens the range. So repeatedly replace the current minimum by its successor in the same list, tracking the max as you go. Stop when some list runs out, because its minimum cannot be raised.

**Invariant.** The heap holds one current value per list; `hi` is the max of those values; `[heap[0], hi]` covers every list.

| Step | Heap (current values) | `hi` | Range | Width | Best |
|---:|---|---:|---|---:|---|
| 0 | 1 (L0), 4 (L1), 7 (L2) | 7 | [1, 7] | 6 | [1, 7] |
| 1 | pop 1, push 5 → 4, 5, 7 | 7 | [4, 7] | 3 | **[4, 7]** |
| 2 | pop 4, push 12 → 5, 7, 12 | 12 | [5, 12] | 7 | [4, 7] |
| 3 | pop 5, push 8 → 7, 8, 12 | 12 | [7, 12] | 5 | [4, 7] |
| 4 | pop 7, push 8 → 8, 8, 12 | 12 | [8, 12] | 4 | [4, 7] |
| 5 | pop 8 (L0), L0 is used up | | stop | | [4, 7] |

```python
import heapq
import random
from bisect import bisect_left


def smallest_range(lists):
    if not lists or any(not lst for lst in lists):
        raise ValueError("need at least one list, all nonempty")
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists)]
    heapq.heapify(heap)
    hi = max(lst[0] for lst in lists)
    best = (heap[0][0], hi)
    while True:
        lo, i, j = heapq.heappop(heap)
        if hi - lo < best[1] - best[0]:
            best = (lo, hi)
        if j + 1 == len(lists[i]):
            return list(best)
        nxt = lists[i][j + 1]
        hi = max(hi, nxt)
        heapq.heappush(heap, (nxt, i, j + 1))


def brute(lists):
    values = sorted({x for lst in lists for x in lst})
    best = None
    for lo in values:
        for hi in values:
            if hi < lo:
                continue
            if all(bisect_left(l, lo) < len(l) and l[bisect_left(l, lo)] <= hi for l in lists):
                if best is None or (hi - lo, lo) < (best[1] - best[0], best[0]):
                    best = (lo, hi)
    return list(best)


def main():
    assert smallest_range([[1, 5, 8], [4, 12], [7, 8, 10]]) == [4, 7]
    assert smallest_range([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]) == [20, 24]
    assert smallest_range([[3]]) == [3, 3]
    rng = random.Random(23)
    for _ in range(800):
        lists = [sorted(rng.randint(-8, 8) for _ in range(rng.randint(1, 5)))
                 for _ in range(rng.randint(1, 4))]
        assert smallest_range(lists) == brute(lists), lists


if __name__ == "__main__":
    main()
```

O(N log k) time, O(k) space. The strict `<` keeps the earliest best range, which has the smallest `lo` among ties because popped minimums never decrease.

**Why it's correct.** Let `[a, b]` be an optimal range. Consider the moment the heap's minimum first reaches a value `≥ a`. Each list's current value is then the first one `≥ a` in that list (smaller values were all popped, and nothing `≥ a` was popped yet). The optimal range contains a value of every list in `[a, b]`, so each current value is `≤ b`. The algorithm therefore checks a range at least as good as `[a, b]` at that moment.

## 4. Task scheduler and reorganize string

**Problem (task scheduler).** A CPU runs tasks named by letters, one per time unit. Two runs of the **same** letter must be at least `n` units apart; the CPU may idle. Find the minimum total time. For `AAABBC` and `n = 2`: `A B C A B _ A`, time **7**.

**Greedy.** A **greedy** algorithm takes the best-looking choice at each step and never undoes it; it needs an argument that this is safe (given below). At each time unit, run the available task with the **most remaining copies**. The letter with the most copies is the one most likely to force idles later, so spend it whenever allowed. A max-heap holds counts of tasks that are ready; a queue holds tasks cooling down with the time they become ready.

| Time | Ready heap (counts) | Run | Cooling queue (ready at) |
|---:|---|---|---|
| 1 | A3 B2 C1 | A | A2 (3) |
| 2 | B2 C1 | B | A2 (3), B1 (4) |
| 3 | C1, then A2 returns | C | B1 (4) |
| 4 | A2, then B1 returns | A | A1 (6) |
| 5 | B1 | B | A1 (6) |
| 6 | empty | idle | A1 returns |
| 7 | A1 | A | |

**Counting formula.** Let `m` be the largest count and `t` the number of letters with that count. The most frequent letters need `m − 1` full "frames" of length `n + 1`, plus one final partial frame of `t` slots:

```text
A B C | A B _ | A        frames of n + 1 = 3, then t = 1
```

So the answer is `max(len(tasks), (m − 1)(n + 1) + t)`. The first term wins when there are so many distinct tasks that no idle is ever needed.

**Problem (reorganize string).** Rearrange a string so no two neighbors are equal, or report it impossible. It is the `n = 1` case without idles: `"aab"` → `"aba"`, `"aaab"` → impossible. It is possible exactly when the largest count is at most `⌈len / 2⌉`. The greedy is the same: always take the most frequent letter that differs from the previous one, holding the previous letter out of the heap for one step.

```python
import heapq
import random
from collections import Counter, deque
from functools import cache
from itertools import permutations


def least_interval(tasks, n):
    if n < 0:
        raise ValueError("n must be nonnegative")
    heap = [-c for c in Counter(tasks).values()]
    heapq.heapify(heap)
    cooling = deque()  # (ready_time, negative remaining count)
    time = 0
    while heap or cooling:
        time += 1
        if heap:
            remaining = heapq.heappop(heap) + 1
            if remaining:
                cooling.append((time + n, remaining))
        if cooling and cooling[0][0] == time:
            heapq.heappush(heap, cooling.popleft()[1])
    return time


def least_interval_formula(tasks, n):
    if not tasks:
        return 0
    counts = Counter(tasks).values()
    m = max(counts)
    t = sum(1 for c in counts if c == m)
    return max(len(tasks), (m - 1) * (n + 1) + t)


def least_interval_brute(tasks, n):
    """Exhaustive search over states (remaining count, cooldown) per letter."""
    start = tuple((c, 0) for c in Counter(tasks).values())

    @cache
    def solve(state):
        if all(c == 0 for c, _ in state):
            return 0
        tick = tuple((c, max(0, w - 1)) for c, w in state)
        options = []
        for i, (c, w) in enumerate(state):
            if c and w == 0:
                nxt = list(tick)
                nxt[i] = (c - 1, n)
                options.append(1 + solve(tuple(nxt)))
        if any(w for _, w in state):  # Idling only helps while something cools.
            options.append(1 + solve(tick))
        return min(options)

    return solve(start)


def reorganize(s):
    heap = [(-c, ch) for ch, c in Counter(s).items()]
    heapq.heapify(heap)
    out, held = [], None
    while heap:
        c, ch = heapq.heappop(heap)
        out.append(ch)
        if held:
            heapq.heappush(heap, held)
        held = (c + 1, ch) if c + 1 else None
    return "".join(out) if not held else ""


def main():
    assert least_interval("AAABBC", 2) == least_interval_formula("AAABBC", 2) == 7
    assert least_interval("AAABBB", 0) == 6
    assert least_interval("", 3) == 0
    assert reorganize("aab") == "aba" and reorganize("aaab") == ""
    assert reorganize("") == ""
    rng = random.Random(24)
    for _ in range(300):
        tasks = "".join(rng.choice("ABC") for _ in range(rng.randint(0, 7)))
        n = rng.randint(0, 3)
        expected = least_interval_brute(tasks, n)
        assert least_interval(tasks, n) == expected
        assert least_interval_formula(tasks, n) == expected
    for _ in range(300):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))
        got = reorganize(s)
        possible = any(all(p[i] != p[i + 1] for i in range(len(p) - 1))
                       for p in set(permutations(s)))
        assert (got != "" or s == "") == possible
        if got:
            assert sorted(got) == sorted(s)
            assert all(got[i] != got[i + 1] for i in range(len(got) - 1))


if __name__ == "__main__":
    main()
```

The simulation is O(T log σ) for `T` time units and `σ` distinct letters; the formula is O(len(tasks)). Reorganize is O(len(s) log σ). The brute force is an exhaustive search over every schedule's state, small enough here because there are at most three letters.

**Why the formula is a lower bound.** The `m` copies of a most frequent letter need `n` units between consecutive copies, so the first and last copy are at least `(m − 1)(n + 1)` apart, and each of the `t` letters with count `m` needs its own slot in the last frame. The greedy schedule fills frames left to right and meets this bound, so it is optimal.

## 5. Meeting rooms: a heap of end times

**Problem.** Meetings are half-open intervals `[start, end)`. What is the fewest rooms that hold them all? For `[(0, 30), (5, 10), (15, 20)]` the answer is **2**. A meeting ending at 10 frees its room for one starting at 10.

**Key observation.** Process meetings by start time. The only room worth reusing is the one that frees up **earliest**: if even that room is busy, every room is busy. A min-heap of end times gives that room.

| Meeting | Heap of end times before | Earliest end ≤ start? | Heap after | Rooms |
|---|---|---|---|---:|
| (0, 30) | `[]` | no room | `[30]` | 1 |
| (5, 10) | `[30]` | 30 > 5: new room | `[10, 30]` | 2 |
| (15, 20) | `[10, 30]` | 10 ≤ 15: reuse | `[20, 30]` | 2 |

```python
import heapq
import random


def min_meeting_rooms(meetings):
    for s, e in meetings:
        if s > e:
            raise ValueError("start must not exceed end")
    ends = []
    for s, e in sorted(meetings):
        if ends and ends[0] <= s:
            heapq.heapreplace(ends, e)  # Reuse the room that frees first.
        else:
            heapq.heappush(ends, e)
    return len(ends)


def brute(meetings):
    points = {s for s, _ in meetings}
    return max((sum(1 for s, e in meetings if s <= p < e) for p in points), default=0)


def main():
    assert min_meeting_rooms([(0, 30), (5, 10), (15, 20)]) == 2
    assert min_meeting_rooms([(1, 5), (5, 9)]) == 1
    assert min_meeting_rooms([]) == 0
    rng = random.Random(25)
    for _ in range(1000):
        ms = []
        for _ in range(rng.randint(0, 10)):
            s = rng.randint(0, 15)
            ms.append((s, s + rng.randint(1, 6)))
        assert min_meeting_rooms(ms) == brute(ms)


if __name__ == "__main__":
    main()
```

O(n log n) time, O(n) space. The answer equals the maximum number of meetings in progress at one moment, which is the sweep-line view of the same problem. [Sweep Line](../08-sweep-line/README.md) solves it with sorted start and end events and also assigns a specific room to each meeting.

## 6. IPO: two heaps for "affordable" and "best"

**Problem.** You start with capital `w` and may finish at most `k` projects, one at a time. Project `i` needs `capital[i]` to start (it is not spent) and adds `profit[i]` to your capital when done. Maximize final capital. For `k = 2`, `w = 0`, `profit = [1, 2, 3]`, `capital = [0, 1, 1]`: do project 0 (capital 1), then project 2 (capital 4). Answer **4**.

**Key observation.** Capital only grows, so a project that is affordable now stays affordable forever. At each step, among all affordable projects, take the most profitable: it leaves you with the most capital, which unlocks a superset of what any other choice unlocks.

**Two heaps.** Projects sorted by required capital (a min-heap or a sorted list with a pointer) feed a max-heap of profits as they become affordable.

| Round | Capital | Newly affordable | Profit max-heap | Take | New capital |
|---:|---:|---|---|---:|---:|
| 1 | 0 | project 0 (profit 1) | {1} | 1 | 1 |
| 2 | 1 | projects 1, 2 (profits 2, 3) | {2, 3} | 3 | 4 |

```python
import heapq
import random
from itertools import permutations


def max_capital(k, w, profits, capital):
    if len(profits) != len(capital) or k < 0:
        raise ValueError("bad input")
    projects = sorted(zip(capital, profits))
    best, i = [], 0  # Max-heap of profits (negated) of affordable projects.
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= w:
            heapq.heappush(best, -projects[i][1])
            i += 1
        if not best:
            break  # Nothing affordable now, and capital will not grow.
        w -= heapq.heappop(best)
    return w


def brute(k, w, profits, capital):
    result = w
    n = len(profits)
    for r in range(1, min(k, n) + 1):
        for order in permutations(range(n), r):
            cur = w
            for p in order:
                if capital[p] > cur:
                    break
                cur += profits[p]
            else:
                result = max(result, cur)
    return result


def main():
    assert max_capital(2, 0, [1, 2, 3], [0, 1, 1]) == 4
    assert max_capital(3, 0, [1, 2, 3], [0, 1, 2]) == 6
    assert max_capital(5, 0, [5], [1]) == 0
    rng = random.Random(26)
    for _ in range(500):
        n = rng.randint(0, 6)
        profits = [rng.randint(0, 5) for _ in range(n)]
        capital = [rng.randint(0, 8) for _ in range(n)]
        k, w = rng.randint(0, 4), rng.randint(0, 3)
        assert max_capital(k, w, profits, capital) == brute(k, w, profits, capital)


if __name__ == "__main__":
    main()
```

O(n log n + k log n) time, O(n) space.

## 7. Course schedule III: greedy with an exchange argument

**Problem.** Course `i` takes `duration[i]` days and must finish by day `last[i]`. You take courses one at a time starting on day 0. Maximize how many you finish. For `[(100, 200), (200, 1300), (1000, 1250), (2000, 3200)]` (duration, last day) the answer is **3**.

**Step 1: the order for a fixed set.** If a set of courses can be finished at all, it can be finished in order of deadline. (If two adjacent courses are out of deadline order, swapping them makes the later one finish where the earlier one used to, which is fine because its deadline is even later.)

**Step 2: the greedy.** Go through courses by deadline, adding each to a running total of days. If the total passes the current deadline, drop the **longest** course taken so far (a max-heap of durations).

| Course (d, last) | Push | Total | Over deadline? | Drop | Kept durations |
|---|---|---:|---|---|---|
| (100, 200) | 100 | 100 | no | | {100} |
| (1000, 1250) | 1000 | 1100 | no | | {100, 1000} |
| (200, 1300) | 200 | 1300 | no | | {100, 200, 1000} |
| (2000, 3200) | 2000 | 3300 | yes, > 3200 | 2000 | {100, 200, 1000} |

**Why dropping the longest is safe (exchange argument).** After the drop, the kept set has the same size it would have had without the new course, and the smallest possible total among all sets of that size drawn from the courses seen so far. A smaller total leaves more room for every later course, so any optimal schedule can be exchanged, course by course, into the greedy one without losing a course.

```python
import heapq
import random
from itertools import combinations


def schedule_course(courses):
    taken, total = [], 0  # Max-heap of durations (negated).
    for d, last in sorted(courses, key=lambda c: c[1]):
        if d < 0:
            raise ValueError("duration must be nonnegative")
        heapq.heappush(taken, -d)
        total += d
        if total > last:
            total += heapq.heappop(taken)  # Remove the longest course so far.
    return len(taken)


def brute(courses):
    for r in range(len(courses), -1, -1):
        for subset in combinations(courses, r):
            day = 0
            for d, last in sorted(subset, key=lambda c: c[1]):
                day += d
                if day > last:
                    break
            else:
                return r
    return 0


def main():
    assert schedule_course([(100, 200), (200, 1300), (1000, 1250), (2000, 3200)]) == 3
    assert schedule_course([(3, 2), (4, 3)]) == 0
    assert schedule_course([]) == 0
    rng = random.Random(27)
    for _ in range(800):
        cs = [(rng.randint(1, 6), rng.randint(1, 15)) for _ in range(rng.randint(0, 7))]
        assert schedule_course(cs) == brute(cs), cs


if __name__ == "__main__":
    main()
```

O(n log n) time, O(n) space.

## 8. Connect sticks and Huffman coding

**Problem.** Joining sticks of lengths `x` and `y` costs `x + y` and makes one stick of that length. Join all sticks into one at minimum total cost. For `[2, 4, 3]`: join 2 and 3 (cost 5), then 5 and 4 (cost 9). Total **14**. Joining 4 and 3 first costs 7 + 9 = 16.

**Greedy.** Always join the two shortest sticks. A min-heap gives them in O(log n).

| Heap | Pop two | Cost | Push | Running total |
|---|---|---:|---:|---:|
| {2, 3, 4} | 2, 3 | 5 | 5 | 5 |
| {4, 5} | 4, 5 | 9 | 9 | 14 |
| {9} | done | | | 14 |

**Why it's optimal.** Draw the joins as a binary tree whose leaves are the original sticks. A stick's length is paid once for every join above it, so the total cost is `Σ length × depth`. In an optimal tree, the deepest level holds two sibling leaves; swapping the two shortest sticks into those spots never increases the cost (a shorter length moves deeper, a longer one moves shallower). So some optimal tree joins the two shortest first. After that join they behave as one stick of their combined length, and the same argument applies to the smaller problem.

**Huffman coding** is the same algorithm. Characters with frequencies are the sticks; the join tree is a binary code where left is `0` and right is `1`. No code is a prefix of another (characters are leaves), and the encoded length `Σ frequency × code length` equals the connect-sticks cost, which the argument above minimizes.

```python
import heapq
import random
from functools import cache


def connect_sticks(sticks):
    heap = list(sticks)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        joined = heapq.heappop(heap) + heapq.heappop(heap)
        total += joined
        heapq.heappush(heap, joined)
    return total


def huffman_codes(freq):
    """freq: dict char -> positive count. Returns dict char -> bit string."""
    if not freq:
        return {}
    heap = [(f, i, ch) for i, (ch, f) in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    count = len(heap)
    while len(heap) > 1:
        f1, _, a = heapq.heappop(heap)
        f2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (f1 + f2, count, (a, b)))  # A tuple is an inner node.
        count += 1
    codes = {}

    def walk(node, prefix):
        if isinstance(node, tuple):
            walk(node[0], prefix + "0")
            walk(node[1], prefix + "1")
        else:
            codes[node] = prefix or "0"  # A single symbol still needs one bit.

    walk(heap[0][2], "")
    return codes


@cache
def brute(sticks):
    if len(sticks) <= 1:
        return 0
    best = None
    for i in range(len(sticks)):
        for j in range(i + 1, len(sticks)):
            rest = [s for t, s in enumerate(sticks) if t not in (i, j)]
            joined = sticks[i] + sticks[j]
            cost = joined + brute(tuple(sorted(rest + [joined])))
            best = cost if best is None else min(best, cost)
    return best


def main():
    assert connect_sticks([2, 4, 3]) == 14
    assert connect_sticks([5]) == 0 and connect_sticks([]) == 0
    codes = huffman_codes({"a": 5, "b": 9, "c": 12, "d": 13, "e": 16, "f": 45})
    assert len(codes["f"]) == 1
    rng = random.Random(28)
    for _ in range(300):
        sticks = [rng.randint(1, 9) for _ in range(rng.randint(0, 6))]
        assert connect_sticks(sticks) == brute(tuple(sorted(sticks)))
        freq = {chr(97 + i): s for i, s in enumerate(sticks)}
        codes = huffman_codes(freq)
        words = list(codes.values())
        assert all(not b.startswith(a) for a in words for b in words if a is not b)
        if len(freq) >= 2:
            assert sum(freq[c] * len(codes[c]) for c in freq) == connect_sticks(sticks)


if __name__ == "__main__":
    main()
```

O(n log n) time, O(n) space. The brute force tries every pair to join at every step.

## 9. Summary: what the heap holds

In every section the heap holds the choices **available right now**; each step pops the best one and pushes whatever that choice makes available next.

| Problem | One heap entry | The root is | After a pop, push |
|---|---|---|---|
| Merge k sorted lists | `(value, list, position)` | the smallest current front | that list's next item |
| k-th smallest in a sorted matrix | `(value, row, col)` | the smallest unvisited candidate | the right neighbor |
| Smallest range | one current value per list | the range's left end | that list's next value (stop when a list runs out) |
| Task scheduler | remaining count of a ready task | the task with most copies left | nothing; it returns after cooling |
| Meeting rooms | end time of a busy room | the room that frees first | the new meeting's end |
| IPO | profit of an affordable project | the best affordable project | newly affordable projects |
| Course schedule III | duration of a kept course | the longest kept course | (pop only when over the deadline) |
| Connect sticks / Huffman | a stick length or subtree weight | the shortest stick | the joined stick |

The greedy sections (4, 6, 7, 8) each rest on an exchange argument: take any optimal answer and swap it, one choice at a time, toward the greedy one without making it worse.

## 10. Pitfalls and practice

1. Pushing `(value, node)` for linked lists. Equal values make Python compare nodes, which raises `TypeError`. Put a counter or list index second.
2. Seeding the matrix heap with the whole first row **and** the whole first column, which pushes some cells twice. Seed one side only and move in one direction.
3. In smallest range, stopping when the heap is empty instead of when **one** list runs out.
4. Meeting rooms with closed intervals. Decide whether a meeting ending at 10 frees the room for one starting at 10, and use `<=` or `<` to match.
5. Task scheduler: forgetting that `len(tasks)` can beat the frame formula.
6. IPO: looping `k` times even when nothing is affordable. Break early.
7. Course schedule III: sorting by duration instead of deadline, or dropping the newest course instead of the longest.
8. Huffman with a single symbol: the tree has no edges, so assign it a one-bit code by convention.

Practice: merge k sorted lists; kth smallest element in a sorted matrix; find k pairs with smallest sums; smallest range covering elements from k lists; task scheduler; reorganize string; distant barcodes; meeting rooms II; single-threaded CPU; IPO; course schedule III; minimum cost to connect sticks; minimum cost to hire k workers.

Next: [Advanced Heaps](04-advanced-heaps.md).
