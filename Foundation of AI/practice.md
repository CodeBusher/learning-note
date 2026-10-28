# Practice Set — Lectures 1–12

Try every exercise without reading the module proof first.

1. **Search:** Prove heuristic consistency implies admissibility when h(goal)=0.
2. **Search:** Construct an admissible-but-inconsistent heuristic and identify the violating edge.
3. **Probability:** Derive `Var(X)=E[X²]-(E[X])²`.
4. **Bayes networks:** Explain whether `P(X3|X1,X2)` can be replaced by `P(X3|X2)` in a chain and in a graph with direct X1→X3 edge.
5. **Bayes networks:** Count independent probability parameters for a four-binary-node chain vs unrestricted joint table.
6. **MDPs:** Write Bellman equations for a fixed policy and optimal actions in a two-state example.
7. **MDPs:** Solve the exact-score coin game for target N=4 (fair coin, +1/+2).
8. **MDPs:** Explain why small successive value-iteration changes do not alone prove convergence in arbitrary undiscounted models.
9. **Least squares:** Derive `∇β(½||Xβ-y||²)=Xᵀ(Xβ-y)` and the normal equations.
10. **Convexity:** Prove `XᵀX` PSD and full-column-rank ⇒ PD.
11. **Regression:** Explain why `β0+β1x+β2x²` is nonlinear in x but linear in β.
12. **Classification:** Derive sigmoid derivative and Bernoulli log-likelihood.
13. **Optimization:** Derive `∇ℓ=Σ(yi-pi)xi`; distinguish gradient ascent from descent.
14. **Learning rate:** For f(x)=x², derive `x_{k+1}=(1-2α)x_k` and when it converges.

## Selected checks
- Four binary chain independent parameter count: 1+2+2+2=7 vs unrestricted 15.
- Target score 3 coin game: U(0)=5/8.
- Scalar quadratic descent converges from any x0 for 0<α<1.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. Based on student-provided lecture notes (Lectures 1–12); these are independent study summaries, not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

CS188 material is supplementary and is not attributed to the Northeastern course.
