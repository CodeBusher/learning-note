# Synthesis — A Modeling Checklist and the Four Cases Side by Side

## 13. A modeling checklist

Four problems with the same numbers:

| Problem | Answer |
|---|---|
| (a) 6 identical candies to 3 children, each child at most 3 | 10 |
| (b) 6 identical coins into at most 3 piles, each pile at most 3 | 3: $(3,3)$, $(3,2,1)$, $(2,2,2)$ |
| (c) 6 identical coins into at most 3 piles, no two piles the same size | 4: $(6)$, $(5,1)$, $(4,2)$, $(3,2,1)$ |
| (d) 6 students into at most 3 unnamed teams, each team at most 3 | 85 |

They differ only in the answers to these questions:

1. Are the $k$ items **identical** (only quantities matter) or **distinct** (each item has its own identity)?
2. Are the $n$ boxes **identical** (permuting boxes changes nothing) or **labeled** (Box A and Box B differ)?
3. Can a box be **empty**? Must there be **exactly**, **at most**, or **at least** $r$ nonempty boxes?
4. Does each box have a lower or upper **occupancy limit**?
5. Is there a restriction on the **occupancy values themselves**: which sizes may appear, their parity, whether they must be distinct, or how many times a size may repeat?
6. Are we counting arrangements or computing probabilities? For probabilities, different arrangements may have unequal probabilities.

Questions 1–2 choose the **family**; questions 3–5 add **constraints** within it. Children are labeled boxes and piles are identical boxes, so (a) is stars and bars with a cap ([§3](02-labeled-boxes.md#3-capacities-by-inclusionexclusion)) and (b) is a partition in a $3\times3$ rectangle ([§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)). Students are distinct items, so (d) is a restricted set partition ([§12.4](05-set-partitions.md#124-restricted-set-partitions)).

Question 5 sounds like question 4 but is different. In (b), "each pile holds at most 3" limits every box's total. In (c), "no two piles the same size" limits how many boxes share a total: it is a constraint on **part sizes** ([§21](08-part-size-constraints.md#21-distinct-parts-and-gap-restrictions)), not on boxes ([§17](07-box-constraints.md#17-number-of-nonempty-boxes)–[§18](07-box-constraints.md#18-box-capacities-and-occupancy-bounds)).

## 14. The four cases side by side

For $k>0$ and $n>0$:

| Items | Boxes | Empty allowed | **All boxes nonempty** | Where |
|---|---|---|---|---|
| Distinct | Labeled | $n^k$ | $n!\ S(k,n)$ | [§11](05-set-partitions.md#11-distinct-items-labeled-boxes) |
| Identical | Labeled | $\binom{k+n-1}{n-1}$ | $\binom{k-1}{n-1}$ if $k\ge n$, else 0 | [§2](02-labeled-boxes.md#2-the-stick-method-stars-and-bars) |
| Distinct | Identical | $\sum_{r=1}^{\min(k,n)}S(k,r)$ | $S(k,n)$ | [§12](05-set-partitions.md#12-distinct-items-identical-boxes-stirling-and-bell-numbers) |
| Identical | Identical | $p_{\le n}(k)$ | $p_{=n}(k)$ | [§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)–[§10](04-integer-partitions.md#10-counting-partitions-generating-function-and-dp), [§17](07-box-constraints.md#17-number-of-nonempty-boxes) |

What an arrangement *is* in each row (function, composition, set partition, integer partition) is the table of [§1](01-modeling.md#1-the-four-cases-on-one-small-example).

**Moving between rows.** From labeled to identical boxes, divide by $n!$ only when every arrangement has exactly $n!$ labeled versions. That holds for distinct items with all boxes nonempty ([§12.1](05-set-partitions.md#121-from-surjections-to-stirling-numbers)) and fails for identical items ([§8](04-integer-partitions.md#8-why-the-stick-method-fails-for-identical-boxes)).

These four rows are part of the **twelvefold way**, which also covers "at most one item per box" ([§29](10-toolkit.md#29-references)).

## 15. Solution approaches compared

A second method checks the first, and which method generalizes best depends on which constraint you add next.

| Approach | Core idea | Works best for | Weak spot |
|---|---|---|---|
| **Product rule** | Each item independently picks a box | Distinct items, labeled boxes | Breaks as soon as boxes are identical |
| **Stick method** (stars and bars) | Line up the items as stars and separate the boxes with sticks | Identical items, labeled boxes | Overcounts when boxes are identical |
| **Ferrers diagrams and bijections** | Draw the partition as dots, then reshape it: conjugate, shift, peel off a staircase | Identical items, identical boxes; exact-$r$, distinct, and gap variants | Each variant needs its own reshaping trick |
| **Recurrences and DP** | Split on one decision, such as "use size $i$ or not" or "where does the newest item go" | Almost everything; exact values | Loop direction and state size need care |
| **Generating functions** | Encode each independent choice as a factor and multiply | Combining several constraints; deriving the DP | Extracting the coefficient still needs DP or algebra |
| **Inclusion–exclusion** | Count without a limit, then subtract the arrangements that break it | Upper capacities on labeled boxes; "every box nonempty" | Alternating sums; awkward for identical boxes |
| **Symmetry (Burnside)** | Count labeled arrangements, then average over box permutations | Identical boxes; rotations and other symmetry groups | Usually slow to compute directly |
| **Brute-force enumeration** | List every arrangement | Validating the other methods on small inputs | Exponential growth |

Which methods apply to each of the four basic cases:

| Case | Direct counting | Recurrence / DP | Generating function | Other |
|---|---|---|---|---|
| Distinct items, labeled boxes | Product rule: $n^k$ | Place items one by one | EGF $e^{nx}$ ([§11.2](05-set-partitions.md#112-fixed-occupancies-and-capacities)) | Multinomials for fixed occupancies ([§11.2](05-set-partitions.md#112-fixed-occupancies-and-capacities)) |
| Identical items, labeled boxes | Stick method: $\binom{k+n-1}{n-1}$ ([§2](02-labeled-boxes.md#2-the-stick-method-stars-and-bars)) | Add boxes one at a time, prefix sums ([§4](02-labeled-boxes.md#4-dp-over-boxes-prefix-sums-and-sliding-windows)) | $(1-x)^{-n}$ ([§5.2](03-generating-functions.md#52-one-labeled-box-then-n-of-them)) | Inclusion–exclusion for capacities ([§3](02-labeled-boxes.md#3-capacities-by-inclusionexclusion)) |
| Distinct items, identical boxes | — | $S(k,r)=rS(k-1,r)+S(k-1,r-1)$ ([§12.2](05-set-partitions.md#122-the-recurrence)) | EGF $(e^x-1)^r/r!$ | Inclusion–exclusion on surjections ([§12.1](05-set-partitions.md#121-from-surjections-to-stirling-numbers)) |
| Identical items, identical boxes | Ferrers diagrams ([§9](04-integer-partitions.md#9-ferrers-diagrams-and-conjugation)) | Coin-change DP, recurrence on boxes ([§10](04-integer-partitions.md#10-counting-partitions-generating-function-and-dp)) | $\prod_i(1-x^i)^{-1}$ ([§10.1](04-integer-partitions.md#101-the-generating-function)) | Burnside ([§24](09-advanced-topics.md#24-burnsides-lemma-for-identical-boxes)), pentagonal numbers ([§23](09-advanced-topics.md#23-unrestricted-partition-numbers-and-faster-recurrences)) |

## 16. One problem, several approaches

**Problem 1: 5 identical items, 3 labeled boxes: 21.** Stick method $\binom72$ ([§2.1](02-labeled-boxes.md#21-empty-boxes-allowed)), $[x^5](1-x)^{-3}$ ([§5.2](03-generating-functions.md#52-one-labeled-box-then-n-of-them)), and three prefix-sum passes ending in `[1,3,6,10,15,21]` ([§4](02-labeled-boxes.md#4-dp-over-boxes-prefix-sums-and-sliding-windows)) all agree.

**Problem 2: 5 identical items, 3 identical boxes.** Answer: 5.

- **Enumeration with Ferrers diagrams:** $(5)$, $(4,1)$, $(3,2)$, $(3,1,1)$, $(2,2,1)$.
- **Coin-change DP on part sizes:** $[x^5]\prod_{i=1}^{3}(1-x^i)^{-1}=5$ ([§10.2](04-integer-partitions.md#102-the-2d-and-1d-recurrences)).
- **Recurrence on boxes:** $p_{\le3}(5)=p_{\le2}(5)+p_{\le3}(2)=3+2=5$ ([§10.3](04-integer-partitions.md#103-a-second-recurrence-split-on-the-boxes)).
- **Burnside's lemma:** average the number of labeled vectors fixed by each of the $3!=6$ box permutations. The identity fixes all 21. Each of the 3 swaps fixes vectors of the form $(a,a,b)$ with $2a+b=5$, so 3 each. The two 3-cycles need $3a=5$, so they fix none. That gives $(21+3\cdot3+0)/6=5$ ([§24](09-advanced-topics.md#24-burnsides-lemma-for-identical-boxes)).

**Problem 3: 5 distinct items, 3 identical nonempty boxes: $S(5,3)=25$.** Recurrence, inclusion–exclusion and EGF are worked side by side in [§12.3](05-set-partitions.md#123-counts-built-from-skr).

**Takeaway.** Most variations can be solved by identifying (1) which objects are distinguishable, (2) what the exponent tracks, (3) which choices each factor permits, and (4) whether each DP update needs old or newly updated coefficients.

The four answers of §13, by brute force:

```python
from itertools import product


def main():
    vectors = [v for v in product(range(7), repeat=3) if sum(v) == 6]
    piles = {tuple(sorted(v, reverse=True)) for v in vectors}
    teams = set()
    for f in product(range(3), repeat=6):        # student s joins team f[s]
        if all(f.count(t) <= 3 for t in range(3)):
            teams.add(frozenset(frozenset(s for s in range(6) if f[s] == t)
                                for t in range(3) if t in f))
    nonzero = [[x for x in pile if x] for pile in piles]
    assert sum(1 for v in vectors if max(v) <= 3) == 10           # (a)
    assert sum(1 for pile in piles if max(pile) <= 3) == 3        # (b)
    assert sum(1 for q in nonzero if len(set(q)) == len(q)) == 4  # (c)
    assert len(teams) == 85                                       # (d)


if __name__ == "__main__":
    main()
```

## Pitfalls and practice

1. **Answering before fixing distinguishability.** Write down questions 1–2 of §13 before any formula.
2. **Confusing box capacity with multiplicity.** "At most 3 per pile" and "the size 3 at most once" are different factors.
3. **Trusting a single method.** Check one small case by a second method or by brute force ([§1](01-modeling.md#1-the-four-cases-on-one-small-example)).

Practice: classify each of these before solving: coin change II; distribute candies among children; partition a set into $k$ nonempty subsets; count partitions of $k$ into distinct parts; dice-sum counts.

Next: [Constraints on the Boxes](07-box-constraints.md).
