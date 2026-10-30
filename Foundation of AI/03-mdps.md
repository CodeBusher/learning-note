# Markov Decision Processes

## Decisions under uncertainty

A **Markov decision process (MDP)** models repeated choices whose outcomes can be random. A search problem asks for a path; an MDP asks what action to take in each state, including states reached unexpectedly.

| Symbol | Meaning |
|---|---|
| s, s′ | Current state and next state |
| a | Action available in the current state |
| P(s′\|s,a) | Probability of reaching s′ after choosing a in s |
| R(s,a,s′) | Immediate reward for that transition |
| π(s) | Action prescribed in s by a deterministic policy π |
| U^π(s) | Expected total return starting in s and following π |
| γ | Discount factor controlling the weight of later rewards |

A **policy** is a rule for choosing actions. A stochastic policy can assign probabilities to actions; the formulas below use deterministic policies. The **Markov assumption** says that, given the current state and action, earlier history does not change the next-state distribution. A useful state description must contain the information needed for that assumption.

The existing course notes use a grid world with terminal outcomes +1 and −1, step reward −0.04, and noisy moves: intended direction with probability 0.8 and each sideways direction with probability 0.1. Transition probabilities for a state/action pair sum to 1.

### Reward and terminal-state conventions

Two equivalent bookkeeping choices are common. One gives the terminal payoff on the transition into a terminal state and then sets that state's continuation utility to zero. Another assigns a boundary utility to the terminal state and omits that payoff from the incoming reward. Never include the same terminal payoff in both places.

Below, ordinary Bellman equations use transition rewards and zero continuation after termination. The coin game explicitly uses success probabilities as boundary values instead.

## Fixed-policy evaluation: why the Bellman equation works

A **return** is the sum of rewards along a trajectory. With discounting it is `R0+γR1+γ²R2+…`. The next reward counts fully; later rewards are scaled by successive powers of γ.

Following a fixed policy gives:

`U^π(s)=Σ_{s′} P(s′|s,π(s))[R(s,π(s),s′)+γU^π(s′)]`.

Choose the action specified by π. For each possible successor, add the immediate reward to the discounted expected future return. Multiply by that successor's probability and sum. This is an expectation over the next state.

For a finite MDP, π fixes all coefficients, so these are simultaneous linear equations in the unknown utilities. The undiscounted episodic form sets γ=1 and requires well-defined expected total returns.

## Optimal actions and value iteration

`U*(s)` means the highest achievable expected return. Instead of following a fixed action, compare all available actions:

`U*(s)=max_a Σ_{s′} P(s′|s,a)[R(s,a,s′)+γU*(s′)]`.

The **maximum** chooses the best expected return, not the best possible random outcome. The equations are coupled because each state's value uses successor values; the maximum makes them generally nonlinear.

**Value iteration** starts with estimates U0, often zero, and repeatedly updates:

`U_{k+1}(s)=max_a Σ_{s′} P(s′|s,a)[R(s,a,s′)+γU_k(s′)]`.

In a synchronous update, every state uses the previous vector U_k. With zero initialization and zero terminal continuation, successive updates can be interpreted as optimal returns for successively longer finite horizons. To extract a policy, choose an action attaining the maximum using the current utility estimates.

### Worked action comparison

Suppose North reaches nonterminal successors with estimated utilities 0.9, 0.2, and 0.5 with probabilities 0.8, 0.1, and 0.1. With immediate reward −0.04 and γ=1:

`Q(North)=−0.04+0.8(0.9)+0.1(0.2)+0.1(0.5)=0.75`.

Here Q is the estimated return for a particular action. If East instead reaches utilities 0.7, 0.6, and 0.4 with the same probabilities, `Q(East)=−0.04+0.56+0.06+0.04=0.62`. Between these two actions, choose North. Check the other available actions before declaring it best overall.

### Worked move against a wall

Suppose North is blocked, so its 0.8 probability keeps the agent in s. The sideways outcomes reach W and E with probabilities 0.1 each, and all three transitions give reward −0.04. Under a policy that chooses North at s:

`U(s)=−0.04+γ[0.8U(s)+0.1U(W)+0.1U(E)]`.

With γ=1 and boundary values U(W)=1 and U(E)=0, this becomes `0.2U(s)=0.06`, so U(s)=0.3. The self-transition appears in the equation because hitting a wall still consumes a step. These boundary values use the second reward convention described above.

## When value iteration converges

A common change measure is the **infinity norm**:

`||U_{k+1}−U_k||∞ = max_s |U_{k+1}(s)−U_k(s)|`.

It reports the largest change at any state. A small change alone is not a convergence guarantee for an arbitrary undiscounted problem. For example, a one-state self-loop with reward −0.001 and γ=1 changes the estimate by just −0.001 every iteration but tends to −∞; it has no finite utility.

**CS188 extension: discounted convergence.** For a finite MDP with bounded rewards and `0≤γ<1`, define T as one Bellman optimality update. For each action, the difference in expected successor values is bounded by `γ||U−V||∞`; taking the maximum over actions preserves this bound. Therefore:

`||TU−TV||∞ ≤ γ||U−V||∞`.

This makes T a **contraction**: it shrinks distances by a factor smaller than one. It has a unique fixed point and value iteration converges to it. For γ=1, that contraction argument no longer applies. Finite-horizon problems use backward induction; infinite-horizon undiscounted problems need suitable termination and return assumptions.

**CS188 extension: policy iteration.** Evaluate a fixed policy, then improve it by choosing actions with the largest expected return according to those values. Repeat. Value iteration instead directly applies the maximum update, without fully evaluating a fixed policy each time.

## Worked coin game: recursion from boundary values

A fair coin adds 2 points on heads and 1 on tails. You win by reaching the target exactly and lose by exceeding it. Define U(s) as the probability of eventually winning from score s. There are no decisions here; this is a Markov reward-process calculation using terminal success values.

For target 3, `U(3)=1` and `U(s>3)=0`. For smaller scores, average the two equally likely outcomes:

`U(s)=½U(s+1)+½U(s+2)`.

Work backward: `U(2)=½(1)+½(0)=1/2`; `U(1)=½(1/2)+½(1)=3/4`; `U(0)=½(3/4)+½(1/2)=5/8`.

For target 4, set `U(4)=1`, `U(s>4)=0`. Then `U(3)=1/2`, `U(2)=3/4`, `U(1)=5/8`, and `U(0)=½(5/8)+½(3/4)=11/16`. The boundary conditions change; the averaging rule stays the same.

## Sources and references

**Primary:** Prof. Nadim Saad, *CS 5100 Foundations of Artificial Intelligence*, Northeastern University, Silicon Valley Campus. These independent study summaries are based on student-provided lecture notes; they are not official course publications.

**Supplementary:** [UC Berkeley CS188 Online Textbook](https://inst.eecs.berkeley.edu/~cs188/textbook/).

- [Markov Decision Processes](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/markov-decision-processes.html)
- [Value Iteration](https://inst.eecs.berkeley.edu/~cs188/textbook/mdp/value-iteration.html)

CS188 extensions and added teaching examples are supplementary explanations, not claims about what was taught in the Northeastern lectures.
