# Probability and Bayesian Networks

*CS 5100 · Lectures 3–4 · Prof. Nadim Saad · Northeastern University (Silicon Valley)*

## Foundations
`P(A∪B)=P(A)+P(B)-P(A∩B)`.
`P(A|B)=P(A∩B)/P(B)` (for P(B)>0).
Independence: `P(A∩B)=P(A)P(B)`.

Bernoulli variable X ∈ {0,1}, success probability p:
`P(X=x)=p^x(1-p)^(1-x)`.

## Expectation and variance
`E[X]=Σ_x xP(X=x)`.
`Var(X)=E[(X-E[X])²]=E[X²]-(E[X])²`.

Derive variance by expanding the square and using E[X]=μ. Squaring prevents positive/negative deviations from cancelling.

Lecture example: equally likely {50,60} and {30,80} both have mean 55, but variance 25 vs 625.

## Chain rule versus Bayesian-network assumption
Always:
`P(X1,X2,X3)=P(X1)P(X2|X1)P(X3|X1,X2)`.

For graph `X1→X2→X3`, conditional independence `X3 ⟂ X1 | X2` allows:
`P(X1,X2,X3)=P(X1)P(X2|X1)P(X3|X2)`.

General Bayes-network factorization: `P(X1,…,Xn)=∏ P(Xi | Parents(Xi))`.

## Number of parameters
For a node with k outcomes and q distinct parent configurations, the conditional table requires `q(k-1)` independent numbers.

For a 3-node chain with domain sizes k1,k2,k3:
`(k1-1)+k1(k2-1)+k2(k3-1)`.
Compare to a fully unrestricted joint distribution, which needs `k1*k2*k3-1`.

**Practice:** Explain why X3|X1,X2 simplifies to X3|X2 only with conditional independence; count parameters for four binary variables in a chain.

## References

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus, Lectures 3–4 (student-provided lecture notes).

**Supplementary:** UC Berkeley [CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/):
- [Probability Rundown](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/probability.html)
- [Bayesian Network Representation](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/representation.html)
- [Structure of Bayes Nets](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/structure.html)

*CS188 provides additional or alternative explanations; the course lecture material remains the primary source.*

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. Based on student-provided lecture notes (Lectures 1–12); these are independent study summaries, not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).
- [CS188: probability](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/probability.html)
- [CS188: representation](https://inst.eecs.berkeley.edu/~cs188/textbook/bayes-nets/representation.html)

CS188 material is supplementary and is not attributed to the Northeastern course.
