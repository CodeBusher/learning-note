# Machine Learning and Classification

## Polynomial regression and generalization

**Supervised learning** uses examples with known targets to learn a prediction rule. Regression predicts a number; classification predicts a category or its probability.

Polynomial regression uses powers of an input as features:

`ŷ=β0+β1*x+β2*x²+⋯+βd*x^d = φ(x)ᵀβ`, where `φ(x)=[1,x,…,x^d]ᵀ`.

This can curve as x changes, but it is still linear in the unknown coefficients β: the coefficients are neither squared nor multiplied together. For example, x=2 gives `ŷ=β0+2β1+4β2`. The least-squares derivation in [Linear Algebra and Optimization](04-math-for-ml.md) applies after placing these feature vectors into X.

**Underfitting** occurs when a model cannot capture the relevant pattern. **Overfitting** occurs when it fits training-specific noise or details that do not generalize. A high polynomial degree increases flexibility and can increase overfitting; it does not guarantee better predictions on new data.

The **bias–variance tradeoff** describes systematic error from restrictive assumptions versus sensitivity to the particular training sample. Under the usual squared-error decomposition, expected prediction error combines squared bias, variance, and irreducible noise. Use training data to fit parameters, validation data to choose model settings, and held-out test data to assess final generalization.

## Binary classification and the sigmoid

A binary label y is either 0 or 1. Logistic regression models `p=P(y=1|x,β)` from a feature vector x, normally including a constant 1 for the intercept:

`z=βᵀx`, then `p=σ(z)=1/(1+exp(−z))`.

The **score** z may be any real number; the **sigmoid** maps it into (0,1). A score of zero gives p=0.5, a positive score gives p>0.5, and a negative score gives p<0.5. A threshold such as 0.5 converts probabilities into labels; other thresholds may fit different error costs.

For a spam classifier with feature “number of typos,” take `x=[1,3]ᵀ` and `β=[−2,1]ᵀ`. The score is −2+3=1, so the spam probability is approximately 0.731. The coefficient values here are an added numerical example.

### Deriving the sigmoid derivative

```text
σ(z)  = (1+e^(−z))^(−1)
σ′(z) = e^(−z)/(1+e^(−z))²
      = [1/(1+e^(−z))][e^(−z)/(1+e^(−z))]
      = σ(z)(1−σ(z)).
```

The derivative is largest at p=0.5 and small near 0 or 1. Because `∇β z=x`, the chain rule gives `∇β p=p(1−p)x`.

## Likelihood: probability of the observed labels

A **likelihood** treats the observed data as fixed and varies β to ask which parameters make those observations most probable. Given features and β, assume labels from different training examples are independent. Each yi is Bernoulli with probability pi:

`L(β)=∏_i pi^(yi)(1−pi)^(1−yi)`.

For yi=1 the factor is pi; for yi=0 it is 1−pi. With two labels y1=1 and y2=0 and predicted probabilities 0.8 and 0.3, the likelihood is `0.8(1−0.3)=0.56`.

The **log-likelihood** is:

`ℓ(β)=Σ_i[yi ln(pi)+(1−yi)ln(1−pi)]`.

The logarithm turns products into sums. Since it is strictly increasing, it preserves which β maximizes the likelihood. Summing log-probabilities also avoids multiplying a large number of tiny probabilities; practical implementations use stable log-sigmoid calculations for extreme scores.

## Deriving the logistic gradient

Use the chain rule and the sigmoid derivative:

```text
∇β ln(pi)     = (1/pi)pi(1−pi)xi = (1−pi)xi
∇β ln(1−pi)   = −[1/(1−pi)]pi(1−pi)xi = −pi xi
∇β ℓ         = Σ_i[yi(1−pi)−(1−yi)pi]xi
             = Σ_i(yi−pi)xi
             = Xᵀ(y−p).
```

Here X stores xiᵀ as row i, and y and p are columns of observed labels and predicted probabilities. Each example contributes its prediction error `yi−pi` multiplied by its feature vector.

**Gradient ascent** increases log-likelihood:

`β_{k+1}=β_k+α∇ℓ(β_k)`, where α>0 is the learning rate.

**Binary cross-entropy loss** is the negative log-likelihood, `J=−ℓ`. Its gradient is `Xᵀ(p−y)`. Gradient descent subtracts this gradient, giving the same update as ascent on ℓ. If the loss is averaged over n examples, its gradient also has a factor 1/n; account for that scaling when choosing α.

### Worked update, including the sign

For one example `x=[1,2]ᵀ`, y=1, and initial `β=[0,0]ᵀ`, the score is 0 and p=0.5. The gradient is `(1−0.5)[1,2]ᵀ=[0.5,1]ᵀ`. With α=0.1, ascent gives `β_new=[0.05,0.1]ᵀ`. The new score is 0.25, so p rises to about 0.562, making the positive observation more likely.

If y=0 but p=0.9, the contribution is `−0.9x`. The update decreases the score for that example by `0.9α||x||₂²`, so its predicted positive probability falls. This sign check explains what the gradient does.

## Learning rate: why a large step can fail

For `f(x)=x²`, the gradient is 2x. Descent gives:

`x_{k+1}=x_k−α(2x_k)=(1−2α)x_k`, hence `x_k=(1−2α)^k x0`.

To converge to zero from any starting point, require `|1−2α|<1`, which simplifies to `0<α<1`.

- α=0.1 gives multiplier 0.8: starting from −2 gives −1.6, −1.28, and so on.
- α=0.5 reaches zero in one step.
- α=1 gives multiplier −1: a nonzero start oscillates, such as −2, 2, −2.
- α>1 has multiplier magnitude greater than 1, so a nonzero start diverges.

This interval is specific to f(x)=x², not a universal learning-rate range. Other objectives have different curvature.

## Curvature and separability: supplementary extension

For logistic regression, `∇²ℓ=−XᵀWX`, where W is diagonal with entries `Wi,i=pi(1−pi)≥0`. For any v, `vᵀ∇²ℓv=−Σ_i pi(1−pi)(xiᵀv)²≤0`, so log-likelihood is concave and negative log-likelihood is convex.

Convexity does not ensure a finite optimum exists. With perfectly separable unregularized data, increasing coefficient magnitudes can drive correct-class probabilities toward 1 without reaching them at finite β. A penalty such as a positive squared norm on all coefficients prevents unlimited growth and changes the optimization objective.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

- [Machine Learning](https://inst.eecs.berkeley.edu/~cs188/textbook/ml.html)
- [Linear Regression](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/linear-regression.html)
- [Optimization](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/optimization.html)
- [Logistic Regression](https://inst.eecs.berkeley.edu/~cs188/textbook/ml/logistic.html)

CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
