# Lectures 10–12 — Polynomial Regression, Classification & Optimization

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
