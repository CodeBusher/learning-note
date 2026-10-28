# Lectures 5–7 — Markov Decision Processes

## Decisions under uncertainty
Lecture grid-world has +1 / -1 terminal rewards, step reward -0.04, and noisy actions: moving in the chosen direction with probability 0.8 and sideways with 0.1 each.

An MDP defines states, actions, transition probabilities and rewards. The next-state distribution depends on current state and action (Markov assumption).

## Fixed policy evaluation
For a fixed policy π, undiscounted episodic value is:
`U^π(s)=Σ_{s'} P(s'|s,π(s)) [R(s,π(s),s')+U^π(s')]`.
These are linear equations for the utilities, provided the expected returns are defined.

## Bellman optimality
`U*(s)=max_a Σ_{s'} P(s'|s,a)[R(s,a,s')+U*(s')]`.
The max chooses the best action at each state. This creates coupled nonlinear equations.

## Value iteration
Start with guesses U0(s); iterate:
`U_{k+1}(s)=max_a Σ_{s'} P(s'|s,a)[R(s,a,s')+U_k(s')]`.
Monitor `||U_{k+1}-U_k||∞ = max_s|U_{k+1}(s)-U_k(s)|`.

**Important qualification:** The notes work in an undiscounted setting; convergence requires appropriate termination or other assumptions. In the discounted extension, replace U by γU, 0≤γ<1; then the Bellman operator is a contraction in the infinity norm.

## Lecture 7 coin toss
Fair coin: heads +2, tails +1. Win if score equals 3, lose if over 3.
`U(3)=1`, `U(s>3)=0` and for s<3:
`U(s)=½U(s+1)+½U(s+2)`.
Thus U(2)=1/2, U(1)=3/4, U(0)=5/8.

**Practice:** Derive the grid Bellman equation for a move against a wall; calculate the coin-toss winning probability for target 4.
