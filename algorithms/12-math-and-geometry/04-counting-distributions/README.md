# Counting Distributions — Balls into Boxes, Partitions, Generating Functions

Count the ways to put $k$ items into $n$ boxes. The answer depends first on whether the items and the boxes can be told apart (four cases: compositions, integer partitions, set partitions, functions), then on the constraints: nonempty boxes, capacities, which part sizes may appear and how often. Generating functions tie the cases together and turn every constraint into a DP pass with a provable loop direction. The core is identical items in identical boxes, the integer partitions; most of the constraint chapters work there.

> **Learning path:** [Four ways](01-modeling.md) → [Labeled boxes](02-labeled-boxes.md) → [Generating functions](03-generating-functions.md) → [Integer partitions](04-integer-partitions.md) → [Set partitions](05-set-partitions.md) → [Synthesis](06-synthesis.md) → [Box constraints](07-box-constraints.md) → [Part-size constraints](08-part-size-constraints.md) → [Advanced topics](09-advanced-topics.md) → [Toolkit](10-toolkit.md)

## Chapters

| # | Chapter | Sections | You will learn | Problems |
|---|---|---|---|---|
| 1 | [Four Ways to Put 4 Balls in 2 Boxes](01-modeling.md) | §1 | The four cases by hand (16, 8, 5, 3); why dividing by $n!$ usually fails | Distinguishability warm-ups |
| 2 | [Labeled Boxes, Identical Items](02-labeled-boxes.md) | §2–§4 | Stars and bars, compositions, capacities by inclusion–exclusion, prefix-sum and sliding-window DP | Distribute candies, bounded integer solutions, dice sums |
| 3 | [Generating Functions](03-generating-functions.md) | §5–§7 | What the exponent and coefficient mean, products of different factors, loop direction from old vs new coefficients | Coin change II, subset-sum counting |
| 4 | [Identical Boxes: Integer Partitions](04-integer-partitions.md) | §8–§10 | Why sticks fail, Ferrers diagrams and conjugation, coin-change DP, the recurrence on boxes | Count partitions, partitions into at most $n$ parts |
| 5 | [Distinct Items: Set Partitions](05-set-partitions.md) | §11–§12 | Surjections, multinomials, exponential generating functions, Stirling and Bell numbers | Onto functions, partition a set into $k$ subsets |
| 6 | [Synthesis](06-synthesis.md) | §13–§16 | A modeling checklist, the four cases side by side, methods compared, one problem several ways | Classifying problems |
| 7 | [Constraints on the Boxes](07-box-constraints.md) | §17–§18 | Exactly or at least $r$ nonempty boxes, capacities, partitions in a rectangle | Partitions into exactly $r$ parts, bounded piles |
| 8 | [Constraints on Part Sizes](08-part-size-constraints.md) | §19–§22 | Allowed, parity and colored parts; multiplicity caps (two-pass DP); distinct parts and gaps; two-variable generating functions | Limited coins, distinct parts, odd parts |
| 9 | [Advanced Topics](09-advanced-topics.md) | §23–§25 | Pentagonal recurrence and asymptotics, Burnside's lemma, other partition families | Partition numbers mod $p$, necklaces |
| 10 | [Toolkit](10-toolkit.md) | §26–§29 | Tested code catalog, capacity vs multiplicity traps, cheat sheet, references | All of the above |

Chapters 1–5 go from the easiest case to the hardest; each answers a question the previous one raises (stars and bars fail for identical boxes; the coin-change product counts partitions; dividing by $r!$ works for distinct items). Chapter 6 reviews all four cases at once. Chapters 7–8 add constraints to identical items in identical boxes. Chapters 9–10 are advanced material and reference.

## Recognizing the pattern

| If your problem is… | Go to |
|---|---|
| Identical items, labeled boxes (ordered occupancies) | [§2](02-labeled-boxes.md#2-the-stick-method-stars-and-bars)–[§4](02-labeled-boxes.md#4-dp-over-boxes-prefix-sums-and-sliding-windows) |
| Identical items and identical boxes, no other constraint | [§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)–[§10](04-integer-partitions.md#10-counting-partitions-generating-function-and-dp) |
| Distinct items | [§11](05-set-partitions.md#11-distinct-items-labeled-boxes)–[§12](05-set-partitions.md#12-distinct-items-identical-boxes-stirling-and-bell-numbers) |
| Comparing methods, or checking an answer a second way | [§15](06-synthesis.md#15-solution-approaches-compared)–[§16](06-synthesis.md#16-one-problem-several-approaches) |
| A DP loop direction you're unsure of | [§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates) |
| Exactly, or at least, $r$ nonempty identical boxes | [§17](07-box-constraints.md#17-number-of-nonempty-boxes) |
| Each identical box holds at most $L$, or between $a$ and $b$ | [§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds) |
| Only certain part sizes, odd/even parts, colored parts | [§19](08-part-size-constraints.md#19-allowed-forbidden-parity-and-colored-parts) |
| Each part size used at most $m$ times | [§20](08-part-size-constraints.md#20-multiplicity-caps-and-the-two-pass-dp) |
| All parts distinct, or adjacent parts differ by at least $d$ | [§21](08-part-size-constraints.md#21-distinct-parts-and-gap-restrictions) |
| Exact or minimum multiplicities, or tracking total and number of parts together | [§22](08-part-size-constraints.md#22-multiplicity-sets-and-two-variable-generating-functions) |
| Large $k$ with no limit on the number of boxes | [§23](09-advanced-topics.md#23-unrestricted-partition-numbers-and-faster-recurrences) |
| Boxes equivalent under rotation or another symmetry | [§24](09-advanced-topics.md#24-burnsides-lemma-for-identical-boxes), [§25](09-advanced-topics.md#25-other-partition-families) |

Two restrictions are easy to confuse: a cap on **each box** ([§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)) bounds the largest part, while a cap on **how often a part size repeats** ([§20](08-part-size-constraints.md#20-multiplicity-caps-and-the-two-pass-dp)) bounds multiplicities.

## Conventions

- Section numbers §1–§29 run across the whole folder, so §20 means the same section in every chapter. Each chapter ends with an unnumbered "Pitfalls and practice" section.
- $k$ items, $n$ boxes; all are nonnegative integers. $p_{\le n}(k)$ counts partitions of $k$ into at most $n$ parts, $p_{=n}(k)$ into exactly $n$, $p(k)$ with no limit. $S(k,r)$ is a Stirling number of the second kind. $[x^k]F$ is the coefficient of $x^k$ in $F$.
- Every Python block is a runnable script that checks itself against a brute force.

## Connections

- [Combinatorics](../02-combinatorics.md): binomial coefficients, inclusion–exclusion and stars and bars in brief.
- [Knapsack and coins](../../09-dynamic-programming/04-knapsack-and-coins.md): the same DPs seen as knapsack; [§7](03-generating-functions.md#7-from-factors-to-in-place-dp-updates) explains their loop directions algebraically.

## Practice order

1. Distribute candies (labeled, with and without limits) — chapter 2.
2. Coin change II, then count subsets with a sum — chapter 3.
3. Count partitions of $k$ into at most $n$ parts — chapter 4.
4. Partition a set into $k$ nonempty subsets; Bell numbers — chapter 5.
5. Partitions into exactly $r$ parts; partitions in an $n\times L$ box — chapter 7.
6. Limited coins; distinct parts; odd parts — chapter 8.
7. Partition numbers modulo a prime for large $k$; necklaces under rotation — chapter 9.
