# MYT Decomposition (Mason, Young & Tracy, 1995)

## Table of Contents
- [[#What Problem MYT Solves|What Problem MYT Solves]]
- [[#The Formula|The Formula]]
- [[#Why This Formula, Specifically|Why This Formula, Specifically]]
- [[#Why Divide Instead of Subtract|Why Divide Instead of Subtract]]
- [[#Worked TEP Example|Worked TEP Example]]
- [[#The Core Limitation|The Core Limitation]]
- [[#Summary Table|Summary Table]]

## What Problem MYT Solves

When Hotelling's $T^2$ (the overall multivariate anomaly score, combining all monitored variables into one number) trips an alarm across the 52 TEP process variables, $T^2$ alone doesn't tell you *which* variable(s) caused it. MYT decomposition answers that: it assigns each variable its own "contribution" score, so you can rank variables by how suspicious they look.

## The Formula

$$\text{contrib}_j = \frac{d_j^2}{\sigma_j^2}$$

Where:
- $j$ = index of the variable (1 through 52 for TEP)
- $d_j$ = deviation of variable $j$, defined as $d_j = x_j - \mu_j$, where $x_j$ is the variable's current (possibly faulty) value and $\mu_j$ is its normal average value (learned from NOC — normal operating condition — training data)
- $\sigma_j$ = the normal standard deviation of variable $j$ (how much it naturally fluctuates under normal operation), so $\sigma_j^2$ is its variance

In plain terms: square the deviation, divide by the variable's own normal variance. This is a squared z-score, computed independently for each variable.

## Why This Formula, Specifically

Hotelling's $T^2$ is defined as:

$$T^2 = d^\top \Sigma^{-1} d$$

Where:
- $d$ = the full vector of deviations across all 52 variables
- $\Sigma$ = the covariance matrix (encodes both each variable's variance and the covariance — the tendency to move together — between every pair of variables)
- $\Sigma^{-1}$ = the inverse of that covariance matrix (the precision matrix)

If $\Sigma$ were diagonal (meaning: no variable correlates with any other), $\Sigma^{-1}$ would also be diagonal with entries $1/\sigma_j^2$. In that special case, the matrix multiplication collapses cleanly into a sum:

$$T^2 = \sum_j \frac{d_j^2}{\sigma_j^2}$$

This is not an approximation in that case — it's an exact identity, because a diagonal matrix multiplication has no cross-terms to lose.

**MYT reuses this exact formula even when $\Sigma$ is not diagonal** — i.e., even when the 52 TEP variables genuinely correlate with each other (which they do, heavily, since they're all coupled through the same physical process). MYT simply ignores the off-diagonal terms of $\Sigma^{-1}$ that encode those relationships.

**Consequence:** the MYT contributions, summed across all 52 variables, generally do **not** add up to the true $T^2$ for a faulty sample. The gap between the sum of contributions and the real $T^2$ is exactly the information lost by ignoring cross-covariance.

## Why Divide Instead of Subtract

**Direct interpretation:** dividing by $\sigma_j$ normalizes the deviation to "how many typical wobbles away from normal is this," making variables with different natural scales directly comparable. Subtracting the mean only removes *location* (recentres the variable at zero); it does nothing about *scale* (how spread out the variable naturally is). Dividing by $\sigma_j$ removes scale — a different job, requiring a different operation.

**Example.** Two TEP variables, same event:

| Variable | Deviation $d_j$ | Normal spread $\sigma_j$ |
|---|---|---|
| Reactor Temp | 1.3 | 0.3 |
| CW Outlet Temp | 4.3 | 1.5 |

- Subtraction only (no rescaling): $1.3$ vs $4.3$ → CW Outlet Temp looks 3× more anomalous. **Wrong** — Reactor Temp is the true fault source in this scenario.
- Subtracting $\sigma_j$ instead of dividing: $1.3-0.3=1.0$ vs $4.3-1.5=2.8$ → CW Outlet Temp still ranks higher. **Still wrong.** Subtracting a fixed amount only shifts the number down; it doesn't change the *ratio* between variables, so the wrong variable still dominates.
- Dividing by $\sigma_j$: $1.3/0.3 \approx 4.3$ vs $4.3/1.5 \approx 2.9$ → Reactor Temp now ranks higher. **Correct.**

Division rescales proportionally — it converts raw, differently-scaled units (°C for temperature, psi for pressure, etc.) into a single unitless quantity: "number of standard deviations away from normal." Only that unitless quantity is safe to compare across variables.

## Worked TEP Example

Baseline statistics from NOC training data, and a faulty sample (e.g. a cooling-water-related fault):

| Variable | Normal mean $\mu_j$ | Normal std dev $\sigma_j$ | Faulty value $x_j$ | Deviation $d_j = x_j-\mu_j$ | Contribution $d_j^2/\sigma_j^2$ |
|---|---|---|---|---|---|
| Reactor Temp | 120.4 | 0.3 | 121.7 | 1.3 | 18.8 |
| Reactor Pressure | 2705 | 13 | 2718 | 13 | 1.0 |
| CW Outlet Temp | 94.6 | 1.5 | 98.9 | 4.3 | 8.2 |
| CW Flow | 41.1 | 2.0 | 46.0 | 4.9 | 6.0 |
| Reactor Level | 75.0 | 1.8 | 75.3 | 0.3 | 0.03 |

**Ranking by contribution:** Reactor Temp (18.8) > CW Outlet Temp (8.2) > CW Flow (6.0) > Reactor Pressure (1.0) > Reactor Level (0.03).

**Step-by-step for Reactor Temp** (showing the arithmetic explicitly):
1. $d_j = 121.7 - 120.4 = 1.3$
2. $d_j^2 = 1.3 \times 1.3 = 1.69$
3. $\sigma_j^2 = 0.3 \times 0.3 = 0.09$
4. $1.69 \div 0.09 \approx 18.8$

**Interpretation:** Reactor Pressure had the largest raw deviation (13 units) but scores lowest (1.0), because Pressure naturally swings by about that much anyway — a 13-unit move is unremarkable for it. Reactor Temp's raw deviation (1.3) is tiny in absolute terms, but huge relative to its normally razor-tight fluctuation (σ = 0.3) — so it's flagged as by far the most anomalous variable. This matches the underlying physical fault (a cooling-water problem heating the reactor), which the naive raw-deviation ranking would have missed entirely.

## The Core Limitation

Sum the contributions above: $18.8 + 1.0 + 8.2 + 6.0 + 0.03 \approx 34$. This does **not** equal the true $T^2$ for the sample, because MYT throws away every cross-covariance term in $\Sigma^{-1}$.

Concrete illustration with two correlated variables (correlation strength 0.8, meaning they normally move together): if both deviate by the same amount, $d = (2, 2)$:
- True $T^2 \approx 4.4$ — small, because moving together is *normal* for these two variables.
- MYT contributions: $4$ and $4$, summing to $8$ — nearly double the true value.

**Why:** MYT has no concept of "these two variables usually move together." It scores each deviation in isolation, effectively double-counting one shared, normal movement as two separate anomalies.

## Summary Table

| Question | MYT's answer |
|---|---|
| What does MYT measure? | How anomalous variable $j$ would be *if it lived alone*, with no relationship to the other 51 variables |
| Formula | $\text{contrib}_j = d_j^2/\sigma_j^2$ |
| Why square-and-divide (not subtract)? | Removes both location (via $d_j$) and scale (via dividing by $\sigma_j^2$), producing a unitless, comparable score |
| Does it account for correlation between variables? | No — it assumes $\Sigma$ is diagonal, i.e. no cross-variable relationships |
| Do contributions sum to true $T^2$? | Not in general — only exactly in the special case of zero correlation |
| Main risk | Can double-count or misattribute faults that only show up as a broken *relationship* between correlated variables, rather than an out-of-range single variable |
