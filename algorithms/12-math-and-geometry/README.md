# Math and Geometry — Number Theory, Counting, and Computational Geometry

Some problems are not about a data structure at all. The hard part is a fact about numbers (which values divide which, what a huge power is modulo a prime), a count that would take forever to list (arrangements, paths, bracket strings), or a picture that has to become arithmetic (which way a path turns, whether a point is inside a fence). Chapter 1 starts from remainders, chapter 2 from the product rule, chapter 3 from "left or right turn?"; each ends with an advanced section (Miller–Rabin; Lucas's theorem and Catalan numbers; rotating calipers). Chapter 2 uses the modular inverses of chapter 1, and chapter 4 goes deep on the distribution problems that chapter 2 introduces with stars and bars.

> **Learning path:** [Number Theory](01-number-theory.md) → [Combinatorics](02-combinatorics.md) → [Geometry](03-geometry.md) → [Counting Distributions](04-counting-distributions/README.md)

| # | Chapter | What you'll learn | Representative problems |
|---|---|---|---|
| 1 | [Number Theory](01-number-theory.md) | Remainders (Python vs C), Euclid's gcd and why it is fast, lcm, extended Euclid, trial division, the sieve of Eratosthenes, the linear sieve with smallest prime factors, divisor counts, modular arithmetic, fast exponentiation, modular inverses (Fermat and Euclid), the Chinese remainder theorem, Miller–Rabin | Count primes; four divisors; pow(x, n); super pow; water and jug; GCD of strings |
| 2 | [Combinatorics](02-combinatorics.md) | Product, complement and sum rules; permutations, combinations and multinomials; Pascal's triangle; `nCr` mod a prime with inverse factorials; Lucas's theorem; stars and bars; Catalan numbers; inclusion–exclusion and derangements; the pigeonhole principle | Unique paths; generate parentheses; unique BSTs; count sorted vowel strings; find the derangement; make sum divisible by P |
| 3 | [Geometry](03-geometry.md) | Vectors, dot and cross products, the orientation test, point-to-segment distance, segment intersection with collinear cases, shoelace area, point in polygon (ray casting and winding), Andrew's monotone chain hull, rotating calipers, precision | Valid boomerang; largest triangle area; erect the fence; convex polygon; max points on a line; farthest pair |
| 4 | [Counting Distributions](04-counting-distributions/README.md) | Balls into boxes, integer partitions, set partitions, generating functions: all four cases of identical or distinct items and boxes, with capacities and part-size constraints | Coin change II; count partitions; distribute candies; Stirling and Bell numbers |

## Recognizing the pattern

| The problem says or implies… | Reach for | Where |
|---|---|---|
| "Return the answer modulo `10^9 + 7`" | Reduce after every `+` and `×`; replace division by a modular inverse | [1 §7](01-number-theory.md#7-modular-arithmetic), [1 §9](01-number-theory.md#9-modular-inverse-two-ways) |
| A power with an exponent up to `10^18` | Fast exponentiation by squaring (or matrix power for a linear recurrence) | [1 §8](01-number-theory.md#8-fast-exponentiation-by-squaring) |
| Largest common size, a repeating period, reducing a ratio or a direction | `gcd`, `lcm` | [1 §2](01-number-theory.md#2-greatest-common-divisor-euclids-algorithm) |
| "Is `ax + by = c` solvable?", jugs, steps of two sizes | Bézout and extended Euclid | [1 §3](01-number-theory.md#3-extended-euclid-writing-the-gcd-as-a-combination) |
| Many primality or factorization queries up to `10^6`–`10^7` | Sieve; smallest prime factors | [1 §5](01-number-theory.md#5-sieve-of-eratosthenes), [1 §6](01-number-theory.md#6-linear-sieve-smallest-prime-factors-and-factorization) |
| Primality of a single number up to `2^64` | Miller–Rabin with fixed bases | [1 §11](01-number-theory.md#11-advanced-millerrabin-primality-test) |
| Several remainder conditions at once | Chinese remainder theorem | [1 §10](01-number-theory.md#10-chinese-remainder-theorem-for-two-moduli) |
| Choose `k` of `n`, grid paths, arrangements with repeats | Binomials, multinomials; factorial tables mod `p` | [2 §2](02-combinatorics.md#2-permutations-and-combinations), [2 §4](02-combinatorics.md#4-ncr-modulo-a-prime-with-factorials) |
| Binomials modulo a small prime, or a non-prime modulus | Lucas's theorem; Pascal's triangle | [2 §5](02-combinatorics.md#5-lucass-theorem-when-the-prime-is-small), [2 §3](02-combinatorics.md#3-pascals-triangle-binomials-by-dp) |
| Balanced brackets, binary tree shapes, polygon triangulations | Catalan numbers | [2 §7](02-combinatorics.md#7-catalan-numbers) |
| "Divisible by at least one of…", "nobody gets their own…" | Inclusion–exclusion; derangements | [2 §8](02-combinatorics.md#8-inclusionexclusion) |
| "Prove that some pair / some subarray must exist" | Pigeonhole on prefix remainders | [2 §9](02-combinatorics.md#9-the-pigeonhole-principle) |
| Identical items into boxes, partitions of an integer | Stars and bars; partition DP; generating functions | [2 §6](02-combinatorics.md#6-stars-and-bars-briefly), [chapter 4](04-counting-distributions/README.md) |
| Left or right turn, collinear points, which side of a line | Cross product, orientation | [3 §3](03-geometry.md#3-the-orientation-test) |
| Do two segments touch or cross? | Four orientations plus bounding boxes | [3 §5](03-geometry.md#5-do-two-segments-intersect) |
| Area of a polygon, its orientation, lattice points inside | Shoelace formula; Pick's theorem | [3 §6](03-geometry.md#6-polygon-area-the-shoelace-formula) |
| Is a point inside a polygon? | Ray casting or winding number, boundary first | [3 §7](03-geometry.md#7-is-a-point-inside-a-polygon) |
| Smallest fence, outermost points | Convex hull (monotone chain) | [3 §8](03-geometry.md#8-convex-hull-andrews-monotone-chain) |
| Farthest pair, width of a point set | Rotating calipers on the hull | [3 §9](03-geometry.md#9-rotating-calipers-the-farthest-pair) |

## Conventions

- Python 3.10+, standard library only. Every complete code block is a runnable script with assertions and, where a brute force is feasible, a comparison against it with a fixed-seed `random.Random`.
- `%` means Python's remainder, which is always in `0..m−1` for `m > 0`. Each chapter notes where C, C++ or Java differ.
- `p` denotes a prime modulus; the default is `10^9 + 7`. Functions that require a prime say so, and inverse functions raise `ValueError` when no inverse exists.
- `C(n, k)`, `nCr` and `\binom{n}{k}` all mean "n choose k", and equal 0 when `k < 0` or `k > n`.
- Geometry uses integer coordinates and exact arithmetic unless a section says otherwise. `orient(a, b, c) > 0` means counterclockwise (a left turn). Polygons are listed counterclockwise; hulls exclude collinear boundary points unless stated.
- Indexing is zero-based, and `a[i:j]` is the half-open range `[i, j)`.

## Connections

- [Faster Transitions](../09-dynamic-programming/12-faster-transitions.md): matrix exponentiation is the fast-power loop of [1 §8](01-number-theory.md#8-fast-exponentiation-by-squaring) applied to matrices, which computes linear recurrences such as Fibonacci in O(log n).
- [Dynamic Programming](../09-dynamic-programming/README.md): Pascal's triangle, Catalan numbers and derangements are DP recurrences; many counting DPs end with an answer modulo a prime.
- [Bit Manipulation](../11-bit-manipulation/README.md): fast exponentiation walks the bits of the exponent; inclusion–exclusion iterates over subsets as bitmasks; `C(n, k)` is odd exactly when `k & n == k`.
- [Sweep Line](../08-sweep-line/README.md): sweep-based geometry, including the closest pair of points, detecting segment intersections, rectangle union area, the skyline and angular sweeps.
- [Prefix Sums](../04-range-queries/01-prefix-sums.md): the pigeonhole argument on prefix remainders is a prefix-sum technique.
- [Binary Search](../01-binary-search/README.md): point location in a convex polygon in O(log n), and binary search on the answer for geometric optimization.

## Suggested practice order

1. Remainders and gcd: GCD of strings, water and jug, fraction addition and subtraction (reduce with `gcd`).
2. Primes: count primes (sieve), closest prime numbers in a range, four divisors, ugly number II.
3. Modular arithmetic: pow(x, n), super pow, count good numbers; then modular inverse and a two-congruence CRT exercise.
4. Counting basics: unique paths, Pascal's triangle, count sorted vowel strings, number of ways to reach a position after exactly `k` steps.
5. Binomials mod a prime: count anagrams, count all valid pickup and delivery options; then a Lucas exercise with a small prime.
6. Catalan and inclusion–exclusion: generate parentheses, unique binary search trees, the derangement problem, numbers divisible by any of a set.
7. Pigeonhole: make sum divisible by P, find the duplicate number.
8. Geometry basics: valid boomerang, check if it is a straight line, largest triangle area, rectangle overlap.
9. Geometry structures: max points on a line, convex polygon, erect the fence, point in polygon, farthest pair with rotating calipers.
10. Counting distributions: work through [chapter 4](04-counting-distributions/README.md) from its first note.

For every problem, write the smallest example by hand first and check your formula or invariant on it before writing code.
