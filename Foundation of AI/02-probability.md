# Probability and Bayesian Networks

## Events and probability notation

An **event** is a set of possible outcomes. `P(A)` is the probability that event A occurs, a number between 0 and 1. For a fair six-sided die, let A mean “the result is even” (`{2,4,6}`) and B mean “the result is greater than 3” (`{4,5,6}`).

| Notation | Meaning | Die example |
|---|---|---|
| `A∪B` | A or B occurs, including both | `{2,4,5,6}` |
| `A∩B` | Both A and B occur | `{4,6}` |
| `P(A∪B)` | Probability of at least one of A and B | `4/6` |
| `P(A∩B)` | Probability of both events | `2/6` |
| `P(A\|B)` | Probability of A given that B occurred | `2/3` |

### Why the union formula subtracts the intersection

`P(A∪B)=P(A)+P(B)−P(A∩B)`.

Adding P(A) and P(B) counts their shared outcomes twice. Subtract the intersection once to count each outcome once. For the die, `3/6+3/6−2/6=4/6`.

### Conditional probability

`P(A|B)=P(A∩B)/P(B)`, provided `P(B)>0`.

The vertical bar means “given.” Knowing B occurred restricts attention to outcomes in B; dividing by P(B) rescales that restricted space to total probability 1. In the example, B leaves `{4,5,6}` possible and two are even, so `P(A|B)=(2/6)/(3/6)=2/3`. This differs from `P(A)=1/2` because the information changes the probability.

### Independence

Events A and B are **independent** when learning that one occurred does not change the probability of the other. Algebraically, `P(A∩B)=P(A)P(B)`; when `P(B)>0`, this is equivalent to `P(A|B)=P(A)`.

The die events above are not independent: `2/6 ≠ (3/6)(3/6)`. In contrast, heads on the first and second tosses of independent fair coins have intersection probability `1/4=(1/2)(1/2)`. Independence does not mean the events cannot happen together. Mutually exclusive events with positive probabilities are dependent: learning one happened rules out the other.

## Random variables and the Bernoulli distribution

A **random variable** assigns a number to each outcome. A **Bernoulli variable** represents one binary result: X=1 for success and X=0 for failure. “Success” is simply the outcome we choose to label 1.

If success probability is p, `P(X=x)` means the probability that X takes the particular value x. Its probability mass function is:

```text
P(X=1)=p
P(X=0)=1−p
P(X=x)=p^x(1−p)^(1−x), for x∈{0,1} and 0<p<1.
```

Substituting x=1 selects p; substituting x=0 selects 1−p. At p=0 or p=1, use the first two equations directly to avoid ambiguous powers such as 0^0. For example, if a device works with probability 0.8, X=1 means “works,” with `P(X=1)=0.8` and `P(X=0)=0.2`.

## Expectation and variance

**Expectation** is the probability-weighted average value of a random variable. For discrete X,

`E[X]=Σ_x xP(X=x)`.

The sum runs over its possible values. It describes a long-run average, not necessarily a possible individual outcome. For Bernoulli X, `E[X]=0(1−p)+1p=p`.

**Variance**, written `Var(X)`, measures spread around the mean `μ=E[X]`:

`Var(X)=E[(X−μ)²]`.

For each outcome, subtract the mean to get its deviation, square the deviation, and average using its probability. Without squaring, positive and negative deviations cancel: `E[X−μ]=0` even for widely spread values. Squaring gives nonnegative contributions and more weight to larger deviations. Variance has squared units; the standard deviation `sqrt(Var(X))` has the same units as X.

### Deriving the computational formula

Treat μ as a constant and use linearity of expectation:

```text
Var(X) = E[X²−2μX+μ²]
       = E[X²]−2μE[X]+μ²
       = E[X²]−2μ²+μ²
       = E[X²]−(E[X])².
```

For Bernoulli X, `X²=X`, because both 0²=0 and 1²=1. Therefore `Var(X)=p−p²=p(1−p)`. With p=0.8, the variance is 0.16. These formulas assume the relevant moments are finite.

## Why the probability chain rule works

`P(X1,X2,X3)` is shorthand for a joint probability at particular values, such as `P(X1=x1,X2=x2,X3=x3)`. It asks for all three assignments at once.

Rearranging conditional probability gives `P(A,B)=P(A)P(B|A)`. Apply it twice:

```text
P(X1,X2,X3) = P(X1,X2)P(X3|X1,X2)
            = P(X1)P(X2|X1)P(X3|X1,X2).
```

This is the **chain rule**. It requires no independence assumption. Conditional probabilities must be defined on the conditioning events used; zero-probability prefixes contribute zero joint probability.

## Bayesian networks: what the graph adds

A **Bayesian network** is a directed acyclic graph plus a probability table for each node conditioned on its parents. A parent is a node with an arrow directly into the current node. “Acyclic” means arrows cannot be followed around a directed cycle.

For the chain `X1→X2→X3`, the model assumes `X3 ⟂ X1 | X2`, read “X3 is conditionally independent of X1 given X2.” Once X2 is known, learning X1 provides no additional information about X3:

`P(X3|X1,X2)=P(X3|X2)`.

That assumption simplifies the chain rule to:

`P(X1,X2,X3)=P(X1)P(X2|X1)P(X3|X2)`.

For an added teaching example, let R=rain, W=wet pavement, and S=slipping, with model `R→W→S`. Suppose `P(R=1)=0.2`, `P(W=1|R=1)=0.9`, and `P(S=1|W=1)=0.3`. Then the probability of rain, wet pavement, and slipping together is `0.2×0.9×0.3=0.054`. The model assumes rain does not further affect slipping once pavement wetness is known; that is a modeling choice, not a universal fact.

If the graph also includes R→S, the final factor is generally `P(S|R,W)`. We cannot remove R unless an additional conditional-independence assumption justifies it.

### General factorization

`P(X1,…,Xn)=∏_i P(Xi | Parents(Xi))`.

The product symbol `∏` means multiply one factor for every node. A root has no parents, so its factor is simply P(Xi). Order nodes so parents precede children, apply the chain rule, then use the network's assumptions to replace conditioning on all preceding variables with conditioning on just the parents. This is why a Bayesian network can represent a joint distribution using smaller local tables.

## Counting independent parameters: worked solutions

A probability row with k outcomes needs only `k−1` freely chosen numbers: probabilities sum to 1, so the last is `1−(sum of the others)`. If there are q possible combinations of parent values, there are q rows, requiring `q(k−1)` independent numbers for an ordinary unrestricted conditional table.

For a chain with domain sizes k1, k2, and k3:

| Factor | Parent configurations | Independent parameters |
|---|---:|---:|
| P(X1) | 1 | k1−1 |
| P(X2\|X1) | k1 | k1(k2−1) |
| P(X3\|X2) | k2 | k2(k3−1) |

Adding the rows gives `(k1−1)+k1(k2−1)+k2(k3−1)`. An unrestricted joint table instead has `k1*k2*k3` entries and needs `k1*k2*k3−1` independent numbers.

### Four binary variables in a chain

For `A→B→C→D`, each variable has two outcomes. P(A) needs one number, such as P(A=1); its complement is fixed. P(B|A) has two rows, one for A=0 and one for A=1, each requiring one number. The same reasoning applies to C given B and D given C. Total: `1+2+2+2=7`.

Without the chain's independence assumptions there are `2⁴=16` assignments, requiring 15 independent probabilities. The reduction from 15 to 7 comes from the model's constraints, not from discarding entries arbitrarily.

## Chain, fork, and collider: CS188 extension

For these isolated three-node graphs, the path rules are:

- **Chain A→B→C:** conditioning on B blocks the path between A and C.
- **Fork A←B→C:** conditioning on the common cause B blocks the path.
- **Collider A→B←C:** the path is blocked until B or a descendant of B is observed; that evidence may make A and C dependent.

For example, two independent causes of an alarm can become dependent after observing the alarm: evidence for one cause may reduce the inferred need for the other. This is called *explaining away*. In a larger network, other unblocked paths must also be considered.

In a chain, `A ⟂ C | B` does not imply `A ⟂ C`. Before B is known, information can still pass along the chain. Conditional independence and unconditional independence are different claims.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

- [Probability Rundown](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/probability.html)
- [Bayesian Network Representation](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/representation.html)
- [Structure of Bayes Nets](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/structure.html)

CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
