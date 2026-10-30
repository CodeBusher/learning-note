# Study Progress — Foundation of AI

Check a box when you can explain the concept in your own words and solve a fresh variation. Reading a worked solution is preparation; reproducing the reasoning demonstrates mastery. Use the [worked review](practice.md) to revisit gaps.

## Search

- [ ] Define states, actions, frontier, goal test, and path cost.
- [ ] Trace DFS, BFS, UCS, and A* with an explicit successor order and stopping rule.
- [ ] Explain when DFS space is O(bm), when O(m) applies, and how a visited set changes memory use.
- [ ] Distinguish completeness from optimality and state their assumptions.
- [ ] Define admissibility and consistency, prove consistency implies admissibility, and explain reopening.
- [ ] Construct a heuristic appropriate for four-way, diagonal, or simultaneous movement.

## Probability and Bayesian networks

- [ ] Explain union, intersection, conditional probability, and independence before using their formulas.
- [ ] Define a Bernoulli variable and interpret P(X=x).
- [ ] Explain expectation and variance; derive Var(X)=E[X²]−(E[X])².
- [ ] Derive the chain rule from conditional probability.
- [ ] Explain why Bayesian-network factorization requires conditional-independence assumptions.
- [ ] Count conditional-table parameters and explain the four-binary-chain result of 7 versus 15.
- [ ] Distinguish chain, fork, and collider behavior (supplementary extension).

## Markov decision processes

- [ ] Define transition probabilities, rewards, policies, returns, and the Markov assumption.
- [ ] Explain each term in fixed-policy and optimal Bellman equations.
- [ ] Calculate an action's expected return, including wall self-transitions and terminal conventions.
- [ ] Perform value-iteration updates and explain the conditions behind convergence.
- [ ] Derive the coin-game recurrence and solve targets 3 and 4 from boundary values.

## Linear algebra and optimization

- [ ] Interpret norms, dot products, gradients, Jacobians, and Hessians.
- [ ] Check dimensions in Xβ and explain squared-error loss.
- [ ] Derive the least-squares gradient and normal equations from both coordinate sums and matrix expansion.
- [ ] Explain PSD, PD, convexity, and the role of full column rank in uniqueness.
- [ ] Exhibit a flat direction in a rank-deficient example and explain residual orthogonality.
- [ ] Explain why QR or SVD can be preferable to explicit inversion (supplementary explanation).

## Machine learning and classification

- [ ] Explain why polynomial regression is linear in its parameters.
- [ ] Distinguish underfitting, overfitting, bias, variance, and train/validation/test roles.
- [ ] Interpret a sigmoid output and derive its derivative.
- [ ] Define likelihood and log-likelihood, including the conditional-independence assumption.
- [ ] Derive the logistic gradient and carry out one numerical update with the correct sign.
- [ ] Relate ascent on log-likelihood to descent on cross-entropy.
- [ ] Derive the learning-rate condition for f(x)=x² and explain its limits.

## Learning log

| Date | Topic | What I can explain or solve | Errors / questions to revisit |
|---|---|---|---|
| | | | |

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).


CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
