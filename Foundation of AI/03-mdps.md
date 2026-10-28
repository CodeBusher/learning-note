# Markov Decision Processes

*CS 5100 · Lectures 5–7 · Prof. Nadim Saad · Northeastern University (Silicon Valley)*

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

## References

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus, Lectures 5–7 (student-provided lecture notes).

**Supplementary:** UC Berkeley [CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/):
- [Markov Decision Processes](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/markov-decision-processes.html)
- [Value Iteration](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/value-iteration.html)

*CS188 provides additional or alternative explanations; the course lecture material remains the primary source.*

## Deriving value iteration from the Bellman principle

Take a state s and choose action a. We receive immediate reward R(s,a,s') and then continue from the random successor s'. The expected return for that action, given current utility estimate U, is
`Q_U(s,a)=Σ_{s'}P(s'|s,a)[R(s,a,s')+γU(s')]`.
The **Bellman operator** takes the best action:
`(TU)(s)=max_a Q_U(s,a)`.
Repeatedly applying T gives `U_{k+1}=TU_k`. For γ=1 and appropriate finite-horizon/terminating models this matches the lecture update; γ<1 is the standard discounted case.

**Why the discounted iteration converges.** For any two utility vectors U,V and any action, the weighted difference in successor utilities is at most `γ||U-V||∞`. The max over actions cannot increase that bound; hence
`||TU-TV||∞ ≤ γ||U-V||∞`.
When 0≤γ<1, each update shrinks the distance between competing estimates by a uniform factor. The fixed point is unique.

**Concrete action comparison.** A move North reaches states with utilities 0.9,0.2,0.5 with probabilities 0.8,0.1,0.1 and gives fixed immediate reward -0.04. With γ=1, its estimated return is `-0.04+0.8(0.9)+0.1(0.2)+0.1(0.5)=0.75`. Repeat for East, South and West, then choose the maximum.

**Policy evaluation versus improvement.** Evaluation holds the action choice fixed and solves for its utilities; improvement switches to actions maximizing expected return according to those utilities. Repeating these two phases is **policy iteration** (supplementary extension), distinct from applying the max update to every state in value iteration.

**Important boundary issue.** Negative reward cycles can yield undefined infinite undiscounted return. A tiny change `||U_{k+1}-U_k||∞` is a stopping heuristic, not proof of validity in an arbitrary undiscounted model.


## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 — Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. Based on student-provided lecture notes (Lectures 1–12); these are independent study summaries, not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).
- [CS188: markov decision processes](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/markov-decision-processes.html)
- [CS188: value iteration](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/value-iteration.html)

CS188 material is supplementary and is not attributed to the Northeastern course.
