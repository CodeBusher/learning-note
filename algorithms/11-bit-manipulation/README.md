# Bit Manipulation — Binary, Tricks, XOR, and Masks

Every integer is a row of bits, and many problems get shorter, faster, or possible at all once you work on those bits directly: one-line tricks for the lowest set bit, popcount and powers of two; XOR, whose cancelling pairs lead to prefix XOR, binary tries and the XOR linear basis; and bitmasks, which turn sets into integers and give submask enumeration, Gosper's hack, Gray codes, bitsets and meet in the middle.

> **Learning path:** [Binary Numbers](01-binary-numbers.md) → [Everyday Bit Tricks](02-everyday-tricks.md) → [XOR](03-xor.md) → [Masks and Subsets](04-masks-and-subsets.md)

## Chapters

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Binary Numbers](01-binary-numbers.md) | Place values, converting both ways, `& \| ^ ~ << >>`, shifts as floor division, two's complement, Python's unbounded ints and 32-bit masking, precedence | Add binary strings, number complement, reverse integer (overflow) |
| 2 | [Everyday Bit Tricks](02-everyday-tricks.md) | Test/set/clear/toggle, `x & -x`, `x & (x - 1)`, popcount three ways, counting bits DP, reverse bits, adding without `+`, XOR swap and branch-free abs | Number of 1 bits, counting bits, power of two, reverse bits, Hamming distance, sum of two integers |
| 3 | [XOR](03-xor.md) | Pairs cancel, single number I/II/III, missing and duplicate numbers, XOR of `0..n` in O(1), prefix XOR, binary trie for maximum XOR, XOR basis (advanced) | Single number, missing number, XOR queries of a subarray, maximum XOR of two numbers, maximum subset XOR |
| 4 | [Masks and Subsets](04-masks-and-subsets.md) | Sets as masks, all subsets, submasks and the 3^n bound, Gosper's hack, Gray codes, Python ints as bitsets, meet in the middle | Subsets, Gray code, partition equal subset sum, closest subsequence sum |

Chapter 1 starts from zero; chapter 2 builds on it. Chapters 3 and 4 use `x & -x` and the 32-bit masking from chapters 1–2 and are otherwise independent of each other. Each chapter ends with a summary table and its pitfalls.

## Recognizing the pattern

| If the problem says or implies… | Reach for | Chapter |
|---|---|---|
| "every element appears twice except one" | XOR everything | [3 §1](03-xor.md#1-the-number-without-a-partner) |
| "…appears three times except one" | Bit counts mod 3, or the `ones`/`twos` machine | [3 §2](03-xor.md#2-single-number-ii-every-other-value-appears-three-times) |
| "two elements appear once" | XOR, then split by the lowest differing bit | [3 §3](03-xor.md#3-single-number-iii-two-lonely-values) |
| A missing value from `0..n` with O(1) space | XOR indices with values | [3 §4](03-xor.md#4-missing-and-duplicated-numbers) |
| XOR of a subarray, many queries | Prefix XOR | [3 §6](03-xor.md#6-prefix-xor-subarray-queries) |
| "maximum XOR of two numbers / with a prefix" | Binary trie, greedy from the high bit | [3 §7](03-xor.md#7-maximum-xor-of-two-numbers) |
| "maximum XOR of any subset", "how many distinct XORs" | XOR linear basis | [3 §8](03-xor.md#8-advanced-the-xor-basis-maximum-subset-xor) |
| "is it a power of two", "count 1 bits", "lowest 1 bit" | `x & (x - 1)`, `bit_count`, `x & -x` | [2 §2–4](02-everyday-tricks.md#2-the-lowest-set-bit-x---x) |
| "without using `+`", "32-bit signed integer", overflow | Masking with `0xFFFFFFFF`, convert back to signed | [1 §6](01-binary-numbers.md#6-pythons-integers-have-no-fixed-width), [2 §8](02-everyday-tricks.md#6-adding-two-integers-without-) |
| Set union/intersection/subset tests on small sets | Bitmask operators | [4 §1](04-masks-and-subsets.md#1-sets-as-integers) |
| `n ≤ 20` and "choose a subset" | Enumerate masks `0 … 2^n − 1` | [4 §2](04-masks-and-subsets.md#2-enumerating-all-subsets) |
| DP over subsets that splits a set into parts | Submask loop, O(3^n) | [4 §3](04-masks-and-subsets.md#3-all-submasks-of-a-mask) |
| "subsets of exactly `k` items" | Gosper's hack | [4 §4](04-masks-and-subsets.md#4-subsets-of-size-k-gospers-hack) |
| "consecutive codes differ by one bit" | Gray code `i ^ (i >> 1)` | [4 §5](04-masks-and-subsets.md#5-gray-codes) |
| Subset-sum reachability with sums up to ~10^6 | Python int as a bitset: `reach \| (reach << a)` | [4 §6](04-masks-and-subsets.md#6-bitsets-a-python-integer-as-a-boolean-array) |
| `n ≈ 40` and "choose a subset" | Meet in the middle | [4 §7](04-masks-and-subsets.md#7-meet-in-the-middle-subset-sum-closest-to-a-target) |

## Conventions

- **Bit `i`** is the bit worth `2^i`; bit 0 is the lowest. Diagrams print the highest bit on the left and group bits in fours (`1011 0110`).
- **Masks:** a set of items `0 … n − 1` is the integer whose bit `i` is 1 when item `i` is in the set; `full = (1 << n) - 1`.
- **Width:** Python integers are unbounded and act like two's complement with infinitely many sign bits. When a problem assumes 32-bit integers, code masks with `& 0xFFFFFFFF` and converts back with `u - (1 << 32)` when bit 31 is set.
- **Precedence:** the code parenthesizes bitwise subexpressions even where Python would not need it, because C, Java and JavaScript bind `==` tighter than `&`.
- Zero-based indexing and half-open slices `a[l:r]`, as in the rest of the guide.
- Every solution block is a runnable script with asserts and a fixed-seed brute-force comparison.

## Connections

- [Trees](../03-trees/README.md): the binary trie for maximum XOR is a trie over the alphabet `{0, 1}`.
- [Range Queries](../04-range-queries/README.md): the Fenwick tree is built on `x & -x`; prefix XOR is prefix sums with XOR as the operation.
- [Dynamic Programming](../09-dynamic-programming/README.md): bitmask DP stores `dp[mask]` over subsets, and the counting-bits table is a one-line DP. Chapter 4's submask loop and Gosper's hack are its toolkit; the bitset trick speeds up subset-sum and 0/1 knapsack reachability.
- [Binary Search](../01-binary-search/README.md): meet in the middle binary searches one half's sorted sums. The greedy "decide the highest bit first" in maximum XOR is the same idea as binary search on the answer, one bit at a time.
- [Graphs](../10-graphs/README.md): masks represent visited sets in traveling-salesman style searches and BFS over states.
- [Sweep Line](../08-sweep-line/README.md): offline maximum-XOR queries sort the queries and insert into a trie as a sweep.
- [Math and Geometry](../12-math-and-geometry/README.md): the XOR basis is Gaussian elimination over GF(2); Gray codes and subset counts tie into combinatorics.

## Practice order

1. Number of 1 bits; power of two; counting bits; Hamming distance (chapter 2).
2. Reverse bits; add binary; number complement (chapters 1–2).
3. Single number; missing number; set mismatch (chapter 3).
4. Single number III; single number II (chapter 3).
5. Sum of two integers (chapter 2: the 32-bit masking).
6. XOR queries of a subarray; count triplets that can form two arrays of equal XOR (chapter 3).
7. Subsets; letter case permutation; Gray code (chapter 4).
8. Maximum product of word lengths; total Hamming distance (chapters 2 and 4).
9. Maximum XOR of two numbers in an array; maximum XOR with an element from array (chapter 3).
10. Partition equal subset sum and last stone weight II with a bitset (chapter 4).
11. Number of valid words for each puzzle (submasks); smallest sufficient team (bitmask DP) (chapter 4 and [DP](../09-dynamic-programming/README.md)).
12. Closest subsequence sum; partition array into two arrays to minimize sum difference (meet in the middle, chapter 4).
13. Maximum subset XOR with a linear basis (chapter 3, advanced).
