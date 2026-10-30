# Linear Algebra and Optimization

## Vectors, norms, and derivatives

A **vector** is an ordered list of numbers. For `v=[v1,…,vp]ᵀ`, the superscript ᵀ means transpose: a row becomes a column or vice versa. The dot product `uᵀv=Σ_i ui*vi` multiplies matching entries and adds them.

A **norm** measures vector size:

| Norm | Formula | For v=[3,−4]ᵀ |
|---|---|---:|
| L1 | `\|\|v\|\|₁=Σ_i \|vi\|` | 7 |
| L2 (Euclidean) | `\|\|v\|\|₂=sqrt(Σ_i vi²)` | 5 |
| Infinity | `\|\|v\|\|∞=max_i \|vi\|` | 4 |

The **gradient** of a scalar function is the column vector of its partial derivatives. Each entry measures how the function changes when one coordinate changes. The **Jacobian** is a matrix of first derivatives; for a scalar-valued function it is conventionally the gradient transposed into one row. The **Hessian** is the matrix of second derivatives and describes curvature.

For a constant vector a, `∇β(aᵀβ)=a`. For a constant matrix A, `∇β(βᵀAβ)=(A+Aᵀ)β`; if A is symmetric this is `2Aβ`. The two terms arise because each coordinate of β can occur on either side of A.

## Linear regression: what is being fitted?

**Linear regression** predicts a numerical target from a weighted sum of features. For n examples and p features, the **design matrix** X has one example per row and one feature per column:

- X has shape n×p.
- β is a p×1 column of model coefficients.
- y is an n×1 column of observed targets.
- `ŷ=Xβ` is the n×1 column of predictions.

An intercept can be represented by a column of ones in X. The error vector `Xβ−y` measures prediction minus observation. The squared-error objective is

`L(β)=½||Xβ−y||₂² = ½Σ_i(Σ_j Xijβj−yi)²`.

Squaring prevents errors from cancelling and penalizes larger errors more. The factor ½ cancels the 2 produced by differentiation; it does not change the minimizer.

## Deriving the gradient and normal equations

Differentiate one coordinate βj. The chain rule gives:

`∂L/∂βj=Σ_i Xij(Σ_k Xikβk−yi)`.

Collecting these partial derivatives into a vector yields `∇L=Xᵀ(Xβ−y)`. You can obtain the same result by matrix expansion:

```text
L(β) = ½(Xβ−y)ᵀ(Xβ−y)
     = ½βᵀXᵀXβ−βᵀXᵀy+½yᵀy
∇L   = XᵀXβ−Xᵀy.
```

The two cross terms in the expansion are equal scalars, so they combine. XᵀX is symmetric, which explains why the quadratic derivative simplifies. Setting the gradient to zero gives the **normal equations**:

`XᵀXβ=Xᵀy`.

These are the conditions for a least-squares optimum. The convexity argument below explains why a stationary point is a global minimum.

### Worked fit with one feature

Take `X=[1,2]ᵀ` and `y=[2,3]ᵀ`, with no intercept. Then `XᵀX=1²+2²=5` and `Xᵀy=1(2)+2(3)=8`, so `5β=8` and β=1.6.

Predictions are `[1.6,3.2]ᵀ`, errors are `[−0.4,0.2]ᵀ`, and the loss is `½(0.16+0.04)=0.1`. The gradient is `1(−0.4)+2(0.2)=0`, confirming the normal equation.

## Hessians, convexity, and uniqueness

A function is **convex** when the line segment connecting two points on its graph lies on or above the graph. For a differentiable convex function, a zero gradient identifies a global minimum.

A symmetric matrix H is **positive semidefinite (PSD)** if `vᵀHv≥0` for every v. It is **positive definite (PD)** if the inequality is strict for every nonzero v. The quantity `vᵀHv` is a quadratic form; for a Hessian it measures curvature in direction v.

For squared loss, `∇²L=XᵀX`. For any v,

`vᵀXᵀXv=(Xv)ᵀ(Xv)=||Xv||₂²≥0`.

The Hessian is PSD, so the loss is convex. If X has **full column rank**, its columns are linearly independent: no nonzero coefficient vector v makes Xv=0. Then the displayed expression is strictly positive for nonzero v, the loss is strictly convex, and its minimizer is unique.

### Worked rank-deficient example

Let `X=[[1,1],[2,2]]`. Its columns are identical, so it is **rank deficient**. Matrix multiplication gives `XᵀX=[[5,5],[5,5]]`. Choose `v=[1,−1]ᵀ`; then Xv=0.

For any scalar t, `X(β+tv)=Xβ+tXv=Xβ`, so moving along v leaves predictions and loss unchanged. If `y=[3,6]ᵀ`, every β satisfying `β1+β2=3` fits perfectly: [3,0], [1,2], and [0,3] all give loss zero. Convexity alone does not guarantee uniqueness.

## Geometry and numerical computation

The **column space** of X is the set of vectors Xβ that the model can predict. Least squares finds the vector in that space closest to y. At the optimum, the residual `r=y−Xβ` is perpendicular to every column of X; otherwise moving along a column could reduce the squared distance. Thus `Xᵀr=0`, which rearranges to the normal equations.

**Supplementary numerical explanation.** With full column rank, `β=(XᵀX)⁻¹Xᵀy` is mathematically valid. Explicit inversion is usually unnecessary. A reduced QR factorization writes `X=QR`, where Q has orthonormal columns and R is triangular, and solves `Rβ=Qᵀy`. Singular value decomposition (SVD) also exposes rank deficiency and can select a minimum-norm solution using a pseudoinverse.

The **condition number** measures sensitivity to input perturbations. For full-column-rank X, forming XᵀX squares its spectral condition number, which can amplify numerical error. This is why the normal equations are valuable for derivation while QR or SVD are often preferable for computation.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

- [Linear Regression](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/linear-regression.html)
- [Optimization](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/optimization.html)

CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
