# Lectures 7–9 — Linear Algebra, Derivatives & Least Squares

## Vector fundamentals
`||v||1=Σ|vi|`, `||v||2=sqrt(Σvi²)`, `||v||∞=max|vi|`.
The gradient of a scalar-valued function is conventionally a column vector, while its Jacobian is one row.

## Linear regression
Prediction `yhat=Xβ`; for n samples and p features, X is n×p, β p×1, and y n×1.
Squared loss: `L(β)=½||Xβ-y||₂²`.

## Derive the normal equations
Expand:
`L(β)=½βᵀXᵀXβ - βᵀXᵀy + ½yᵀy`.
Since XᵀX is symmetric:
`∇L(β)=XᵀXβ-Xᵀy`.
Setting gradient to zero yields `XᵀXβ=Xᵀy`.

## Hessian and positive semidefiniteness
`∇²L=XᵀX`. For any vector v:
`vᵀXᵀXv=(Xv)ᵀ(Xv)=||Xv||₂²≥0`.
Hence the Hessian is PSD and loss convex.

If X has full column rank, Xv≠0 for all v≠0, making XᵀX positive definite; the loss is strictly convex with a unique minimizer.

The formula `β=(XᵀX)⁻¹Xᵀy` is mathematically valid when X has full column rank, but QR/SVD solvers are usually numerically preferable to explicit inversion.

**Practice:** Derive the gradient from coordinate sums and matrix expansion; prove full column rank implies unique least-squares minimizer; give a rank-deficient example and a flat parameter direction.
