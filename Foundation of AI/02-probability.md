# Lectures 3–4 — Probability & Bayesian Networks

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
