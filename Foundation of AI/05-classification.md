# Machine Learning and Classification

*CS 5100 · Lectures 10–12 · Prof. Nadim Saad · Northeastern University (Silicon Valley)*

## Polynomial regression
`yhat=β0+β1*x+β2*x²+⋯+βd*x^d = φ(x)ᵀβ`, with `φ(x)=[1,x,…,x^d]ᵀ`.
The function is nonlinear in the input x but linear in coefficients β. Thus polynomial least squares is still convex in β.

High-degree models can overfit; the lecture covers training/test split, underfitting, overfitting and the bias–variance tradeoff.

## Binary classification
Sigmoid `σ(z)=1/(1+exp(-z))` maps to (0,1) and has derivative `σ'(z)=σ(z)(1-σ(z))`.
With a feature vector that includes an intercept: `pi=σ(βᵀxi)`. The lecture example classifies spam using number of typos.

## Likelihood and log-likelihood
Assuming training examples are conditionally independent given features and β, each binary label yi has Bernoulli likelihood:
`L(β)=∏_i pi^(yi) (1-pi)^(1-yi)`.
Taking logarithms:
`ℓ(β)=Σ_i [yi ln(pi)+(1-yi) ln(1-pi)]`.
Because log is strictly increasing, maximizing log-likelihood is equivalent to maximizing likelihood.

## Derive logistic gradient (Lecture 12)
`∇ ln(pi)=(1-pi)xi`
and `∇ ln(1-pi)=-pi xi`.
Therefore:
`∇ℓ(β)=Σ_i(yi-pi)xi=Xᵀ(y-p)`.

Gradient ascent: `β_{k+1}=β_k+α∇ℓ(β_k)`.
Equivalently, gradient descent minimizes negative log-likelihood using minus its gradient.

Lecture 11 example: for f(x)=x², x0=-2 and α=1, descent oscillates between -2 and 2. With α=0.1, updates converge toward zero.

**Practice:** Derive sigmoid derivative, likelihood and logistic gradient from first principles; prove the scalar quadratic descent stability condition `0<α<1`.

## References

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus, Lectures 10–12 (student-provided lecture notes).

**Supplementary:** UC Berkeley [CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/):
- [Machine Learning](https://inst.eecs.berkeley.edu/~cs188/textbook/ml.html)
- [Linear Regression](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/linear-regression.html)
- [Optimization](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/optimization.html)
- [Logistic Regression](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/logistic.html)

*CS188 provides additional or alternative explanations; the course lecture material remains the primary source.*

## Detailed logistic regression derivation

Let `zᵢ=βᵀxᵢ`, `pᵢ=σ(zᵢ)=1/(1+e^{-zᵢ})`, and binary label `yᵢ∈{0,1}`. Under independent conditional Bernoulli observations,
`L(β)=∏ pᵢ^{yᵢ}(1-pᵢ)^{1-yᵢ}`.

Because the logarithm is strictly increasing, maximizing L is equivalent to maximizing
`ℓ(β)=Σ[yᵢ log pᵢ+(1-yᵢ)log(1-pᵢ)]`.
Turning products into sums also avoids multiplying many tiny probabilities.

Use `∇β pᵢ=pᵢ(1-pᵢ)xᵢ` from the sigmoid derivative and chain rule. Thus
`∇β log pᵢ=(1-pᵢ)xᵢ`
and
`∇β log(1-pᵢ)=-pᵢxᵢ`.
Combining terms:
`∇βℓ=Σ[yᵢ(1-pᵢ)-(1-yᵢ)pᵢ]xᵢ=Σ(yᵢ-pᵢ)xᵢ=Xᵀ(y-p)`.

**One-sample intuition:** If a positive example has label y=1 but predicted probability p=0.2, the gradient contribution is `0.8x` and ascent pushes the score upward along x. If label y=0 and p=0.8, the contribution is `-0.8x` and ascent pushes the score downward.

**Relationship to loss functions.** Binary cross-entropy is the *negative* log-likelihood. Minimizing cross-entropy by gradient **descent** and maximizing log-likelihood by gradient **ascent** lead to equivalent parameter updates.

**Curvature (supplementary extension):** For this model, `∇²ℓ=-XᵀWX`, with diagonal `Wᵢᵢ=pᵢ(1-pᵢ)≥0`. So ℓ is concave. In perfectly separable unregularized data, however, the finite maximum-likelihood parameter vector may not exist.

**Practice:** Differentiate the Bernoulli log-likelihood on paper, then verify the sign of the update when y=0,p=0.9 and x>0.


## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. Based on student-provided lecture notes (Lectures 1–12); these are independent study summaries, not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).
- [CS188: optimization](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/optimization.html)
- [CS188: logistic](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/logistic.html)

CS188 material is supplementary and is not attributed to the Northeastern course.
