# PCA T² / SPE Attribution — Two Base Methods

## Table of Contents

- [[#Setup and Symbols|Setup and Symbols]]
- [[#Method 1 — PCA Loading Attribution (T²)|Method 1 — PCA Loading Attribution (T²)]]
- [[#Method 2 — PCA Residual Attribution (SPE)|Method 2 — PCA Residual Attribution (SPE)]]
- [[#Worked Numerical Example (4 variables, 2 components)|Worked Numerical Example (4 variables, 2 components)]]
- [[#Why the Two Methods Give Different Answers|Why the Two Methods Give Different Answers]]

## Setup and Symbols

PCA fit on training data splits every sample into two orthogonal pieces: the part the retained components can explain, and the part they cannot. Both attribution methods score one of these two pieces — never both.

Symbols used throughout:

- $p$ = number of process variables (TEP: 52)
- $c$ = number of retained PCA components (e.g. 10)
- $j$ = index over variables, $j = 1, ..., p$
- $k$ = index over components, $k = 1, ..., c$
- $x \in \mathbb{R}^p$ = one sample (a vector of $p$ variable values)
- $P \in \mathbb{R}^{p \times c}$ = loading matrix. Column $k$ holds the $p$ weights defining component $k$. Row $j$ holds variable $j$'s weight on each of the $c$ components.
- $P^T \in \mathbb{R}^{c \times p}$ = $P$ transposed, used to project $x$ into the $c$-dimensional component space
- $t = P^Tx \in \mathbb{R}^c$ = the sample's scores (coordinates in the $c$-dim PCA space); $t_k$ is a single dot product between row $k$ of $P^T$ (i.e. column $k$ of $P$) and $x$
- $\sigma_k$ = training-data standard deviation of score $k$, computed once from $X_{train}$
- $z_k = t_k / \sigma_k$ = standardized score for component $k$ — how many training-std-devs component $k$ is displaced
- $\hat{x} = Pt \in \mathbb{R}^p$ = reconstruction of $x$ using only the $c$ retained components
- $e_j = x_j - \hat{x}_j$ = residual for variable $j$ — the part of variable $j$ the $c$-component model could not reconstruct
- $\text{Var}_j$ = training-data variance of variable $j$'s residual, computed once from $X_{train}$ before scoring any new sample

The fundamental split:

$$x = \hat{x} + (x - \hat{x})$$

Method 1 scores $\hat{x}$'s side (what the model explains). Method 2 scores $(x-\hat{x})$'s side (what it cannot).

## Method 1 — PCA Loading Attribution (T²)

**What it measures:** how much each variable drove the sample too far along directions the model already knows about.

**Step 1 — scores.** Project $x$ into the $c$-dim space:

$$t_k = \sum_{j=1}^{p} P_{j,k} \, x_j, \qquad k = 1,...,c$$

**Step 2 — standardize.**

$$z_k = \frac{t_k}{\sigma_k}$$

**Step 3 — attribute back to variables.**

$$\text{contrib}_j = \sum_{k=1}^{c} |z_k| \cdot |P_{j,k}|$$

Each term multiplies "how abnormal is component $k$" ($|z_k|$) by "how much does variable $j$ feed component $k$" ($|P_{j,k}|$), summed over all $c$ components. Variables with large loadings on the most-abnormal components get the highest contribution.

**Input:** $x$ (length $p$), $P$, training $\sigma_k$'s.
**Output:** a length-$p$ contribution vector; sort descending to find top drivers.

## Method 2 — PCA Residual Attribution (SPE)

**What it measures:** how much each variable moved in a way the $c$-component model never captured at all.

**Step 1 — reconstruct.**

$$\hat{x}_j = \sum_{k=1}^{c} t_k \cdot P_{j,k}$$

Note: this uses the raw scores $t_k$, not the standardized $z_k$ used in Method 1. Same matrix operation ($P$ times scores), different input, different meaning of output — here $\hat{x}_j$ is a reconstructed *value*, not an abnormality score.

**Step 2 — residual.**

$$e_j = x_j - \hat{x}_j$$

**Step 3 — normalize and score.**

$$\text{contrib}_j = \frac{e_j^2}{\text{Var}_j}$$

Dividing by $\text{Var}_j$ puts all variables on the same scale — otherwise a variable that's naturally noisy under normal operation would dominate every time just from its baseline jitter.

**Input:** $x$ (length $p$), $P$, training $\text{Var}_j$'s.
**Output:** a length-$p$ contribution vector; sort descending to find top drivers.

## Worked Numerical Example (4 variables, 2 components)

Toy setup: $p=4$, $c=2$.

Loading matrix $P$:

| var $j$ | $P_{j,1}$ | $P_{j,2}$ |
|---|---|---|
| 1 | 0.6 | 0.1 |
| 2 | 0.5 | -0.2 |
| 3 | 0.4 | 0.7 |
| 4 | 0.1 | 0.6 |

Training score std: $\sigma_1=1.0$, $\sigma_2=1.2$
Training residual variance: $\text{Var}_1=0.5$, $\text{Var}_2=0.4$, $\text{Var}_3=0.6$, $\text{Var}_4=0.3$

Sample: $x = [3, -2, 1, 4]$

**Scores:**

$$t_1 = 0.6(3)+0.5(-2)+0.4(1)+0.1(4) = 1.6$$
$$t_2 = 0.1(3)+(-0.2)(-2)+0.7(1)+0.6(4) = 3.8$$

**Standardized:** $z_1 = 1.6/1.0 = 1.6$, $z_2 = 3.8/1.2 = 3.17$

**Method 1 output** ($\text{contrib}_j = |z_1||P_{j,1}|+|z_2||P_{j,2}|$):

| var | contrib |
|---|---|
| 1 | 1.6(0.6)+3.17(0.1) = 1.28 |
| 2 | 1.6(0.5)+3.17(0.2) = 1.43 |
| 3 | 1.6(0.4)+3.17(0.7) = **2.86** ← top |
| 4 | 1.6(0.1)+3.17(0.6) = 2.06 |

**Reconstruction** ($\hat{x}_j = t_1 P_{j,1} + t_2 P_{j,2}$):

| var | $\hat{x}_j$ |
|---|---|
| 1 | 1.6(0.6)+3.8(0.1) = 1.34 |
| 2 | 1.6(0.5)+3.8(-0.2) = 0.04 |
| 3 | 1.6(0.4)+3.8(0.7) = 3.30 |
| 4 | 1.6(0.1)+3.8(0.6) = 2.44 |

**Residual** ($e_j = x_j - \hat{x}_j$): $[1.66,\ -2.04,\ -2.30,\ 1.56]$

**Method 2 output** ($\text{contrib}_j = e_j^2/\text{Var}_j$):

| var | contrib |
|---|---|
| 1 | $1.66^2/0.5$ = 5.51 |
| 2 | $2.04^2/0.4$ = **10.40** ← top |
| 3 | $2.30^2/0.6$ = 8.82 |
| 4 | $1.56^2/0.3$ = 8.11 |

## Why the Two Methods Give Different Answers

Same sample, same $P$, same scores $t$ — but Method 1 blames variable 3, Method 2 blames variable 2. This is not a contradiction: they score two disjoint, orthogonal pieces of $x$.

- Method 1 asks: within what the 2-component model explains ($\hat{x}$), which variable pushed hardest along the most-displaced component?
- Method 2 asks: outside what the 2-component model explains ($x-\hat{x}$), which variable has the largest unexplained leftover, relative to its own normal noise level?

A fault can score high on one, low on the other, or high on both — the two contrib vectors are independent diagnostics computed from the identity $x = \hat{x} + (x-\hat{x})$.
