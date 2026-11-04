# Two Pointers — Discard Candidates Without Checking Them

## 1. Two values that add up to a target

You get a list of integers sorted from smallest to largest, and a target. Find two different positions whose values add up to the target.

```text
index    0   1   2   3   4   5
nums     1   3   4   6   8  11      target = 10
```

The answer is positions 2 and 3, because `4 + 6 = 10`.

**Brute force.** Try every pair `(i, j)` with `i < j`. With `n` values there are `n(n − 1) / 2` pairs: 15 here, about 500,000 for `n = 1,000`, and about 5 billion for `n = 100,000`. The brute force never uses the fact that the list is **sorted**.

**The key observation.** Put one index, called a **pointer**, `left` on the smallest value and another, `right`, on the largest. Look at their sum.

- **Too small:** `nums[left]` plus *any* value at or before `right` is also too small, because `nums[right]` is the largest value still in play. So `nums[left]` belongs to no possible answer. Throw it away: `left += 1`.
- **Too large:** `nums[right]` plus any value at or after `left` is also too large, because `nums[left]` is the smallest value still in play. Throw it away: `right -= 1`.
- **Equal:** stop.

Each step discards one value **together with every pair it belongs to**, after checking only one of those pairs.

**Invariant:** if an answer pair exists, both of its positions lie in `[left, right]`.

`L` marks `left` and `R` marks `right`:

```text
index     0   1   2   3   4   5
nums      1   3   4   6   8  11      target = 10

step 1    L                   R      1 + 11 = 12  too large  -> right -= 1
step 2    L               R          1 +  8 =  9  too small  -> left  += 1
step 3        L           R          3 +  8 = 11  too large  -> right -= 1
step 4        L       R              3 +  6 =  9  too small  -> left  += 1
step 5            L   R              4 +  6 = 10  found (2, 3)
```

Five sums instead of fifteen; the pointers meet after at most `n − 1` steps.

### What was skipped

Draw every pair as a cell, with `i` down the side and `j` across the top. A number is the step that checked that pair; a dot is a pair never checked:

```text
            j=1   j=2   j=3   j=4   j=5
   i=0       .     .     .     2     1
   i=1             .     4     3     .
   i=2                   5     .     .
   i=3                         .     .
   i=4                               .
```

Moving `R` removes a column; moving `L` removes a row. Every dot sits in a row or column that was proved useless before the dot was reached. That is the whole safety argument.

```python
from random import Random


def pair_sum_sorted(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return positions (i, j), i < j, with nums[i] + nums[j] == target.

    nums must be sorted in nondecreasing order. Return None if no pair exists.
    """
    if any(nums[i] > nums[i + 1] for i in range(len(nums) - 1)):
        raise ValueError("nums must be sorted")
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return left, right
        if total < target:
            left += 1
        else:
            right -= 1
    return None


def count_pairs_below(nums: list[int], target: int) -> int:
    """Count pairs i < j with nums[i] + nums[j] < target. nums is sorted."""
    left, right = 0, len(nums) - 1
    count = 0
    while left < right:
        if nums[left] + nums[right] < target:
            count += right - left      # nums[left] pairs with all of (left, right]
            left += 1
        else:
            right -= 1
    return count


def has_pair_brute(nums, target):
    return any(nums[i] + nums[j] == target
               for i in range(len(nums)) for j in range(i + 1, len(nums)))


def count_pairs_below_brute(nums, target):
    return sum(nums[i] + nums[j] < target
               for i in range(len(nums)) for j in range(i + 1, len(nums)))


def main():
    assert pair_sum_sorted([1, 3, 4, 6, 8, 11], 10) == (2, 3)
    assert pair_sum_sorted([2, 2], 4) == (0, 1)            # duplicates
    assert pair_sum_sorted([-3, -1, 0, 5], -4) == (0, 1)   # negatives
    assert pair_sum_sorted([5], 10) is None                # one element
    assert pair_sum_sorted([], 0) is None                  # empty
    assert pair_sum_sorted([1, 2, 3], 100) is None         # impossible
    assert count_pairs_below([1, 3, 4, 6, 8, 11], 10) == 6
    try:
        pair_sum_sorted([3, 1], 4)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    rng = Random(1)
    for _ in range(500):
        nums = sorted(rng.randrange(-8, 9) for _ in range(rng.randrange(8)))
        target = rng.randrange(-12, 13)
        found = pair_sum_sorted(nums, target)
        if found is None:
            assert not has_pair_brute(nums, target)
        else:
            i, j = found
            assert i < j and nums[i] + nums[j] == target
        assert count_pairs_below(nums, target) == count_pairs_below_brute(nums, target)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)` for `n` values; the sortedness check is also `O(n)`. If the input is not sorted, sort it first for `O(n log n)`, and keep the original indices if the problem asks for positions. **Space:** `O(1)`.

**Why it's correct.** A value is removed only after every pair it could still form was shown to have the wrong sum, so the invariant holds. If the loop ends with `left >= right`, no pair of positions is left, so no answer exists.

**Variant: counting instead of finding.** `count_pairs_below` counts pairs with sum `< target`. When `nums[left] + nums[right]` is small enough, `nums[left]` plus anything in `(left, right]` is small enough too, so all `right − left` of those pairs count in one step. Counting a whole block at once returns in [Counting and Frequency Windows](03-counting-and-frequency-windows.md).

## 2. Container with most water

You get a list of wall heights; wall `i` stands at position `i`. Two walls and the floor hold water up to the **shorter** wall:

$$
\text{area}(i,j)=(j-i)\cdot\min(h_i,h_j).
$$

Find the largest area.

```text
heights   1  8  6  2  5  4  8  3  7
index     0  1  2  3  4  5  6  7  8
```

The best pair is walls 1 and 8: width 7, height `min(8, 7) = 7`, area 49. Trying all pairs costs `O(n²)`.

**The key observation.** Start with the widest pair, `left = 0` and `right = n − 1`. Suppose `h[left] <= h[right]`, so the left wall is the shorter one. Every other pair that uses the left wall, `(left, j)` with `j < right`, is

- **narrower**: `j − left < right − left`, and
- **no taller**: `min(h[left], h[j]) <= h[left]`, the current height.

So no remaining pair with the left wall beats the current pair. Record the current area, then move the shorter wall inward. Moving the taller wall instead would be a mistake: the shorter wall still caps the height while the width shrinks. On a tie, the argument applies to either wall.

This list is **not** sorted. The reason to discard comes from the area formula, not from order. Two pointers need a reason to discard, and sortedness is only one possible reason.

```text
heights   1   8   6   2   5   4   8   3   7
index     0   1   2   3   4   5   6   7   8

step 1    L                               R   width 8, min(1,7)=1 ->  8   best  8   move L
step 2        L                           R   width 7, min(8,7)=7 -> 49   best 49   move R
```

Steps 3–8 all move `R`: the left wall, height 8, is never the shorter one again. Their areas are 18, 40 (a tie, `min(8, 8)`), 16, 15, 4 and 6, so the best stays 49. Eight areas instead of thirty-six.

```python
from random import Random


def max_area(heights: list[int]) -> int:
    """Largest (j - i) * min(heights[i], heights[j]); 0 if fewer than 2 walls."""
    if any(h < 0 for h in heights):
        raise ValueError("heights must be nonnegative")
    left, right = 0, len(heights) - 1
    best = 0
    while left < right:
        best = max(best, (right - left) * min(heights[left], heights[right]))
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best


def max_area_brute(heights):
    return max(((j - i) * min(heights[i], heights[j])
                for i in range(len(heights)) for j in range(i + 1, len(heights))),
               default=0)


def main():
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    assert max_area([4, 3, 2, 1, 4]) == 16
    assert max_area([5]) == 0
    assert max_area([]) == 0
    assert max_area([0, 0, 0]) == 0

    rng = Random(2)
    for _ in range(500):
        heights = [rng.randrange(10) for _ in range(rng.randrange(9))]
        assert max_area(heights) == max_area_brute(heights)


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`. **Space:** `O(1)`.

**Why it's correct.** Each move discards the shorter wall after showing that every pair it can still form is no larger than the area recorded at that step. So the best pair is either recorded or tied with a recorded area.

## 3. Three values that sum to zero

Find every **distinct** triple of values from three different positions with sum 0. Report each triple of values once, however many position sets build it.

For `nums = [-1, 0, 1, 2, -1, -4]` the answer is `[-1, -1, 2]` and `[-1, 0, 1]`. The triple `[-1, 0, 1]` can use either `-1`, but it appears once. Trying all triples costs `O(n³)`.

**The key observation.** Sort the list. Fix the first value `nums[i]`; the other two must sum to `−nums[i]` and come from positions after `i`. That is §1 on `nums[i+1:]`, which costs `O(n)`, so all `i` together cost `O(n²)`.

The real difficulty is **duplicates**. Sorting puts equal values next to each other, so two skips remove them:

- If `nums[i] == nums[i − 1]`, every triple starting with this value was found in the previous round. Skip this `i`.
- After a match, move `left` past every copy of `nums[left]` and `right` past every copy of `nums[right]`. Otherwise the next step finds the same triple again.

Sorted: `[-4, -1, -1, 0, 1, 2]`.

```text
index      0   1   2   3   4   5
nums      -4  -1  -1   0   1   2

i = 0  need 4    every pair sum is < 4: L walks right until it meets R

i = 1  need 1
               i   L           R      -1 + 2 =  1  found [-1, -1, 2]; move both
               i       L   R           0 + 1 =  1  found [-1,  0, 1]; move both, meet

i = 2  nums[2] == nums[1]: skip

i = 3  need 0
                       i   L   R       1 + 2 =  3 > 0  -> R; meet
```

```python
from itertools import combinations
from random import Random


def three_sum_zero(nums: list[int]) -> list[list[int]]:
    """All distinct value triples summing to 0, each sorted, in sorted order."""
    nums = sorted(nums)
    n = len(nums)
    triples = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue                      # same first value as the last round
        if nums[i] > 0:
            break                         # three positive values cannot sum to 0
        need = -nums[i]
        left, right = i + 1, n - 1
        while left < right:
            total = nums[left] + nums[right]
            if total < need:
                left += 1
            elif total > need:
                right -= 1
            else:
                triples.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
    return triples


def three_sum_brute(nums):
    found = {tuple(sorted(t)) for t in combinations(nums, 3) if sum(t) == 0}
    return [list(t) for t in sorted(found)]


def main():
    assert three_sum_zero([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]
    assert three_sum_zero([0, 0, 0, 0]) == [[0, 0, 0]]
    assert three_sum_zero([0, 1, 1]) == []
    assert three_sum_zero([]) == []
    assert three_sum_zero([-2, 1, 1, 1]) == [[-2, 1, 1]]

    rng = Random(3)
    for _ in range(500):
        nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(9))]
        assert three_sum_zero(nums) == three_sum_brute(nums)


if __name__ == "__main__":
    main()
```

**Time:** `O(n log n)` to sort plus `O(n²)` for the loops. **Space:** `O(n)` for the sorted copy, plus the output.

**Why it's correct.** Write a distinct triple in sorted order `a <= b <= c`. The round for the **first** `i` with `nums[i] == a` is never skipped, and inside it the pair search of §1 finds every distinct pair summing to `−a` among later positions. Skipping copies after a match only skips pairs with the same values as the triple found at that step. So each distinct triple is reported exactly once.

**Variants.** 3Sum Closest keeps the loops and records the total closest to the target. 4Sum fixes two values and runs the pair search inside: `O(n³)`. k-Sum recurses down to the pair search.

## 4. Reader and writer: remove duplicates in place

Here both pointers move **in the same direction**, at different speeds. You get a sorted list. Move each distinct value once to the front, in order, and return how many there are. Use no second list.

```text
input    [0, 0, 1, 1, 1, 2, 2, 3]
output   4, and the list starts with [0, 1, 2, 3]
```

What comes after the first four places does not matter. A second list costs `O(n)` space; `list.pop(i)` costs `O(n²)` in total.

### The key observation

- `read` visits every value once.
- `write` marks where the next kept value goes.

**Invariant:** `nums[:write]` holds the distinct values of `nums[:read]`, in order.

Because the list is sorted, a value is new exactly when it differs from the last kept value `nums[write − 1]`. When it is new, copy it to `nums[write]` and advance `write`. The writer never passes the reader, so no value is overwritten before it is read.

The bar `|` sits at `write`; left of it is the kept prefix.

```text
start        [0 | 0, 1, 1, 1, 2, 2, 3]   write = 1 (the first value is always kept)
read = 1     0 == last kept 0  -> skip
read = 2     1 is new          -> nums[1] = 1    [0, 1 | 1, 1, 1, 2, 2, 3]
read = 3, 4  1 == 1            -> skip
read = 5     2 is new          -> nums[2] = 2    [0, 1, 2 | 1, 1, 2, 2, 3]
read = 6     2 == 2            -> skip
read = 7     3 is new          -> nums[3] = 3    [0, 1, 2, 3 | 1, 2, 2, 3]
```

The answer is `write = 4`.

### Variant: keep at most `k` copies

A value may be written when it differs from `nums[write − k]`, the value `k` places back in the kept prefix. If it is equal, the sorted prefix already ends with `k` copies of it. With `k = 1` this is the problem above.

```python
from random import Random


def keep_at_most(nums: list[int], k: int) -> int:
    """Keep at most k copies of each value at the front of sorted nums.

    Return the new length. Modify nums in place.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    write = 0
    for read in range(len(nums)):
        if write < k or nums[read] != nums[write - k]:
            nums[write] = nums[read]
            write += 1
    return write


def remove_duplicates(nums: list[int]) -> int:
    return keep_at_most(nums, 1)


def keep_at_most_brute(nums, k):
    return [v for i, v in enumerate(nums) if nums[:i].count(v) < k]


def main():
    nums = [0, 0, 1, 1, 1, 2, 2, 3]
    assert remove_duplicates(nums) == 4 and nums[:4] == [0, 1, 2, 3]
    nums = [1, 1, 1, 2, 2, 3]
    assert keep_at_most(nums, 2) == 5 and nums[:5] == [1, 1, 2, 2, 3]
    assert remove_duplicates([]) == 0
    assert remove_duplicates([7]) == 1

    rng = Random(4)
    for _ in range(500):
        nums = sorted(rng.randrange(-3, 4) for _ in range(rng.randrange(10)))
        k = rng.randrange(1, 4)
        expected = keep_at_most_brute(nums, k)
        length = keep_at_most(nums, k)
        assert nums[:length] == expected


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`. **Space:** `O(1)`.

**Why check `write < k` first.** While fewer than `k` values are kept, `nums[write − k]` is a negative index, which Python silently reads from the end of the list. The check keeps the first `k` values unconditionally.

The same reader/writer pattern solves "move all zeros to the end" (write every nonzero, then fill zeros) and "remove every copy of a value" (write everything else).

## 5. The Dutch national flag: three pointers

You get a list of only `0`, `1` and `2`. Sort it in one pass, in place, without counting. (The name comes from the flag's three stripes.)

```text
input    [2, 0, 2, 1, 1, 0]
output   [0, 0, 1, 1, 2, 2]
```

Counting takes two passes. The one-pass version matters because the same idea **partitions** a list around a pivot in quicksort.

### The state

Three pointers split the list into four regions:

```text
 [ 0 0 0 | 1 1 1 | ? ? ? ? | 2 2 2 ]
          low     mid     high

 nums[:low]          all 0
 nums[low:mid]       all 1
 nums[mid:high+1]    not looked at yet
 nums[high+1:]       all 2
```

Look at `nums[mid]`, the first unknown value:

- `0`: swap it with `nums[low]` (a `1`, or `mid` itself). Advance `low` and `mid`.
- `1`: already in place. Advance `mid`.
- `2`: swap it with `nums[high]` and shrink `high`. Do **not** advance `mid`: the value that arrived from `high` is still unknown.

Stop when the unknown region is empty, `mid > high`.

```text
                     index:  0  1  2  3  4  5
start                       [2, 0, 2, 1, 1, 0]   low=0 mid=0 high=5
nums[0]=2  swap 0<->5       [0, 0, 2, 1, 1, 2]   low=0 mid=0 high=4
nums[0]=0  swap 0<->0       [0, 0, 2, 1, 1, 2]   low=1 mid=1 high=4
nums[1]=0  swap 1<->1       [0, 0, 2, 1, 1, 2]   low=2 mid=2 high=4
nums[2]=2  swap 2<->4       [0, 0, 1, 1, 2, 2]   low=2 mid=2 high=3
nums[2]=1                   [0, 0, 1, 1, 2, 2]   low=2 mid=3 high=3
nums[3]=1                   [0, 0, 1, 1, 2, 2]   low=2 mid=4 high=3   stop
```

In step 1, the `0` that came from position 5 was examined in step 2. That is why `mid` stays put after a swap with `high`.

```python
from random import Random


def sort_colors(nums: list[int]) -> None:
    """Sort a list of 0s, 1s, and 2s in place in one pass."""
    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        value = nums[mid]
        if value == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif value == 1:
            mid += 1
        elif value == 2:
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1
        else:
            raise ValueError("values must be 0, 1, or 2")


def main():
    nums = [2, 0, 2, 1, 1, 0]
    sort_colors(nums)
    assert nums == [0, 0, 1, 1, 2, 2]
    for case in ([], [1], [2, 2], [2, 1, 0]):
        copy = list(case)
        sort_colors(copy)
        assert copy == sorted(case)

    rng = Random(5)
    for _ in range(500):
        nums = [rng.randrange(3) for _ in range(rng.randrange(12))]
        expected = sorted(nums)
        sort_colors(nums)
        assert nums == expected


if __name__ == "__main__":
    main()
```

**Time:** `O(n)`: each step advances `mid` or shrinks `high`, so the unknown region loses one place per step. **Space:** `O(1)`.

**Why it's correct.** The four-region picture holds at the start (everything is unknown), and each case keeps it. In the `0` case, the value swapped out of `nums[low]` is a `1` when `low < mid`, so the `1` region shifts right by one and stays all 1s. When the unknown region is empty, the list reads 0s, then 1s, then 2s.

## 6. What these problems share

Every solution above moves a pointer only after proving that the candidates it discards cannot be the answer. So no pointer moves back, the total number of moves is a few times `n`, and the algorithm is linear after any sorting.

| Pattern | Pointers move | Why a move is safe | Examples |
|---|---|---|---|
| Opposite ends | Toward each other | The discarded value's remaining pairs are all too small, too large, or no better | Pair sum, container with most water, 3Sum |
| Reader and writer | Same direction, writer behind | The written prefix holds exactly the accepted values read so far | Remove duplicates, move zeros |
| Partition | `low`/`mid` forward, `high` backward | Each region's content is fixed by the invariant | Dutch national flag, quicksort partition |
| Sliding window | Same direction; the stretch between them matters | A discarded left end cannot start any future answer | [Fixed and Variable Windows](02-fixed-and-variable-windows.md) onward |

Fast and slow pointers on a [linked list](../02-linked-lists/README.md) (cycle detection, the middle node) and merging two sorted lists follow the same rule: find a reason to discard, then move only forward.

## 7. Pitfalls and practice

1. **Forgetting the sorted precondition.** Opposite-end pair sum is wrong on unsorted input. Sort first, and keep original indices if they are part of the answer.
2. **Moving the taller wall** in container with most water. Only the shorter wall has been proved useless.
3. **Duplicate triples** in 3Sum. Skip equal first values, and skip copies on both sides after a match.
4. **Advancing `mid` after a swap with `high`.** The value that came from `high` is still unknown.
5. **Negative indices in Python.** `nums[write − k]` with `write < k` reads from the end of the list instead of raising an error.
6. **`left <= right` versus `left < right`.** Pair problems need two different positions, so they loop while `left < right`. The Dutch flag loops while `mid <= high`, because one unknown value is still work.

Practice: Two Sum II (sorted input); Valid Palindrome; Container With Most Water; 3Sum; 3Sum Closest; 4Sum; Remove Duplicates from Sorted Array (I and II); Move Zeroes; Sort Colors; Squares of a Sorted Array; Trapping Rain Water (two-pointer version).

Next: [Fixed and Variable Windows](02-fixed-and-variable-windows.md).
