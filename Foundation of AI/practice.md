# Worked Review — Foundation of AI

These added teaching examples connect the five chapters. Each includes the reasoning and result; you can optionally cover the solution before trying it. Chapter links lead to fuller definitions and derivations.

## 1. Search: trace the frontier and check the guarantee

Use directed edges `S→A:1`, `S→B:2`, `A→G:9`, `B→C:2`, `C→G:2`. Generate successors alphabetically, explore A first in DFS, and test goals when removed from the frontier.

DFS and BFS return S→A→G, cost 10. DFS follows A to the goal; BFS prefers its two edges to the alternative's three. UCS removes S(0), A(1), B(2), C(4), G(6), improving G's tentative cost from 10 to 6 after expanding C. Its solution is S→B→C→G, cost 6. The difference is what each frontier prioritizes: depth, edge count, or accumulated cost.

For A*, a consistent heuristic obeys `h(n)≤c(n,n′)+h(n′)`. Add this along a path to G: intermediate terms cancel, leaving `h(n)≤path cost+h(G)`. With h(G)=0, choosing an optimal path proves admissibility. The reverse implication fails: on A→B→G with costs 2 and 3, h(A)=5 and h(B)=1 are admissible but violate `5≤2+1`.

Admissible graph A* may need reopening; see the full failure trace and the DFS space explanation in [Search](01-search.md).

## 2. Probability: interpret before calculating

A fair die has events A={2,4,6} and B={4,5,6}. The union is {2,4,5,6}, so `P(A∪B)=4/6`. The intersection is {4,6}, so `P(A∩B)=2/6`. Given B, only three equally likely outcomes remain, two in A: `P(A|B)=2/3`.

Independence would require `P(A|B)=P(A)=1/2`, so these events are dependent.

For Bernoulli X with p=0.3, `E[X]=0(0.7)+1(0.3)=0.3`. Since X²=X, `E[X²]=0.3`. Expanding `E[(X−μ)²]` gives `E[X²]−2μE[X]+μ²=E[X²]−μ²`; hence `Var(X)=0.3−0.09=0.21`. See [Probability and Bayesian Networks](02-probability.md).

## 3. Bayesian networks: separate identity from assumption

The chain rule always gives `P(A,B,C)=P(A)P(B|A)P(C|A,B)` wherever the conditioning terms are defined. A chain model A→B→C adds `C ⟂ A | B`, allowing the last term to become P(C|B). Adding A→C generally removes that simplification.

For four binary variables A→B→C→D, P(A) has one independent parameter. Each remaining node has two possible parent values, so its table has two rows and one free probability per row. Total: `1+2+2+2=7`. The unrestricted joint has 16 assignments and one normalization constraint: 15 parameters.

## 4. MDPs: fixed policy versus optimal action

Consider two states, S and terminal T. In S, **Exit** gives reward 2 and reaches T. **Wait** gives reward 0 and returns to S. Set γ=0.9 and U(T)=0; the exit reward is counted on the transition.

Under a policy that always waits, `U^π(S)=0+0.9U^π(S)`, so U^π(S)=0. Under a policy that exits, U^π(S)=2. Bellman optimality gives `U*(S)=max(2,0.9U*(S))`; U*(S)=2 satisfies it and Exit is optimal.

Starting U0(S)=0, value iteration gives U1(S)=max(2,0)=2, then U2(S)=max(2,1.8)=2. In contrast, a γ=1 self-loop with reward −0.001 keeps changing by −0.001 forever, despite small per-step changes. See [Markov Decision Processes](03-mdps.md).

## 5. Coin game: compute backward from termination

A fair coin adds 1 or 2 points. To win by reaching score 4 exactly, set U(4)=1 and U(s>4)=0. For s<4, average the successors: `U(s)=½U(s+1)+½U(s+2)`.

Working backward gives U(3)=1/2, U(2)=3/4, U(1)=5/8, then `U(0)=½(5/8)+½(3/4)=11/16`. Starting from 0, the winning probability is 0.6875. Repeating for target 3 gives 5/8.

## 6. Least squares: differentiate and solve

With `X=[1,2]ᵀ` and `y=[2,3]ᵀ`, the loss is `L(β)=½[(β−2)²+(2β−3)²]`. Differentiate: `L′(β)=(β−2)+2(2β−3)=5β−8`. Set this to zero to get β=8/5.

In matrix form the same equation is `XᵀXβ=Xᵀy`, or 5β=8. The general gradient is `Xᵀ(Xβ−y)`. For any v, `vᵀXᵀXv=||Xv||₂²≥0`, so the Hessian is PSD. Independent columns make this strictly positive for nonzero v, ensuring uniqueness.

For `X=[[1,1],[2,2]]`, the vector v=[1,−1]ᵀ satisfies Xv=0, so β+tv gives the same predictions for every t. This is a flat direction and explains nonuniqueness. See [Linear Algebra and Optimization](04-math-for-ml.md).

## 7. Polynomial regression: identify the unknowns

For `ŷ=β0+β1x+β2x²`, x is the input and β contains the unknown parameters. At x=3, the prediction is `β0+3β1+9β2`, a linear expression in β. Using rows [1,x,x²] in X turns polynomial fitting into ordinary linear least squares. Increasing degree adds flexibility, but performance on held-out data is needed to judge generalization.

## 8. Logistic regression: derive and apply the update

Let p=σ(βᵀx). Differentiating the sigmoid gives `σ′=σ(1−σ)`, so `∇βp=p(1−p)x`. The one-example Bernoulli log-likelihood is `ℓ=y ln p+(1−y)ln(1−p)`. Its gradient is `[y(1−p)−(1−y)p]x=(y−p)x`.

For x=[1,2]ᵀ, y=1, β=[0,0]ᵀ, and α=0.1, p=0.5 and the ascent update is `β_new=β+0.1(0.5)x=[0.05,0.1]ᵀ`. The new score is 0.25 and probability is approximately 0.562. Descent on negative log-likelihood gives the same update. See [Machine Learning and Classification](05-classification.md).

## 9. Learning rate: derive the stability condition

For f(x)=x², descent gives `x_{k+1}=(1−2α)x_k`. After k steps, `x_k=(1−2α)^k x0`. For convergence from every initial value, the multiplier must have magnitude less than 1: `−1<1−2α<1`, or `0<α<1`.

At α=1, the multiplier is −1 and any nonzero start oscillates. At α=0.1 it is 0.8 and the magnitude shrinks each step. A start at zero stays there regardless of α, which is why the condition is stated for every initial value.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).


CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
