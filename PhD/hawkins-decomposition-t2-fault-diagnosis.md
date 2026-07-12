# Hawkins' Whitened T² Decomposition for Fault Diagnosis

## Table of Contents

- [[#Overview|Overview]]
- [[#Symbols and Definitions|Symbols and Definitions]]
- [[#The T² Decomposition Family|The T² Decomposition Family]]
- [[#Hawkins Decomposition — Derivation|Hawkins Decomposition — Derivation]]
- [[#Why Squares and Not Absolute Values|Why Squares and Not Absolute Values]]
- [[#Worked Example — Four Process Variables|Worked Example — Four Process Variables]]
- [[#From Raw Measurements to Contributions — Step by Step|From Raw Measurements to Contributions — Step by Step]]
- [[#Interpretation of the Example|Interpretation of the Example]]
- [[#Punchline|Punchline]]

## Overview

Hotelling's $T^2$ statistic answers a single yes/no question: *is this observation abnormal, given how the process variables normally vary and co-vary?* It collapses all variables into one alarm number. The moment $T^2$ crosses its control limit, a second question arises that $T^2$ itself cannot answer: *which variable(s) actually drove the abnormality?*

Hawkins' whitened decomposition (Hawkins, 1993) answers that second question by splitting the single $T^2$ number into one non-negative piece per variable, such that the pieces sum back to $T^2$ exactly, while correctly accounting for the fact that process variables are correlated — two variables that move together should not both get blamed independently for the same shift.

## Symbols and Definitions

Every symbol used below is defined here before use.

- $x_i \in \mathbb{R}^p$ — the vector of measured values at time point $i$, one entry per process variable (e.g. temperature, pressure, flow, level). $p$ is the number of variables monitored ($p=4$ in the worked example).
- $\mu \in \mathbb{R}^p$ — the in-control (healthy/reference) mean vector. Each variable has **its own** mean, estimated from normal operating data — there is no single overall mean shared across variables.
- $d = x_i - \mu$ — the deviation vector at time point $i$. Each entry $d_j$ is that variable's own value minus that variable's own in-control mean.
- $\Sigma$ — the in-control covariance matrix of the $p$ variables (a correlation matrix if variables are standardized to unit variance, as in the worked example). $\Sigma_{jk}$ captures how variable $j$ and variable $k$ move together.
- $\Sigma^{-1}$ — the inverse covariance matrix, sometimes called the precision matrix.
- $T^2 = d^\top \Sigma^{-1} d$ — Hotelling's $T^2$ statistic: a single scalar alarm score for the whole observation, accounting for correlations between variables.
- $L$ — the lower-triangular Cholesky factor of $\Sigma^{-1}$, satisfying $LL^\top = \Sigma^{-1}$. $L$ acts as an "un-mixing" matrix that removes the correlation structure encoded in $\Sigma^{-1}$.
- $z = L^\top d$ — the **whitened deviation vector**. It is not a raw measurement of any variable; it is $d$ rotated and rescaled into a coordinate system where the components no longer share correlation information with each other. $z_j$ is the part of variable $j$'s deviation that is *not already explained* by its correlation with the other variables.
- $\text{contrib}_j = z_j^2$ (or $\mathbb{E}[z_j^2]$ when averaged over many samples of the same fault type) — variable $j$'s contribution to $T^2$.

## The T² Decomposition Family

Three classical methods split $T^2$ across the original variables. They differ only in how they handle the correlation structure:

- **MYT decomposition** (Mason, Young & Tracy, 1995) computes an *unconditional* contribution, $\mathbb{E}[d_j^2]/\sigma_j^2$ — each variable's deviation normalized only by its own variance, ignoring cross-covariance entirely.
- **Hawkins' whitened decomposition** (Hawkins, 1993) whitens $d$ with the Cholesky factor of $\Sigma^{-1}$ before squaring — this *does* account for cross-covariance, and the pieces sum to $T^2$ exactly.
- **Runger, Alt & Montgomery's variable contribution plots** (1996) use the same whitening idea as Hawkins but with the symmetric inverse square root $\Sigma^{-1/2}$ (obtained via eigendecomposition) instead of the asymmetric Cholesky factor.

The rest of this note focuses on the Hawkins method.

## Hawkins Decomposition — Derivation

Start from the definition of $T^2$ and substitute the Cholesky factorization of $\Sigma^{-1}$:

$$T^2 = d^\top \Sigma^{-1} d = d^\top (LL^\top) d$$

Regroup the product, using $d^\top L = (L^\top d)^\top$:

$$T^2 = (L^\top d)^\top (L^\top d)$$

Substitute $z = L^\top d$:

$$T^2 = z^\top z = \sum_{j=1}^{p} z_j^2$$

This is an exact algebraic identity, not an approximation. It is the same relationship as the Pythagorean theorem: once $d$ has been whitened into $z$, the components of $z$ are uncorrelated, so the squared length of $z$ splits additively across its axes — exactly as $\|(a,b)\|^2 = a^2 + b^2$ does for perpendicular axes in a right triangle.

$$\boxed{\text{contrib}_j = z_j^2, \qquad \sum_j \text{contrib}_j = T^2}$$

## Why Squares and Not Absolute Values

Squaring is not an arbitrary choice to remove negative signs — it is the specific operation for which the identity above holds. Absolute value has no equivalent identity: $\sum_j |z_j| \neq z^\top z$ in general. Using absolute values would break the exact reconstruction of $T^2$ and destroy the property that contributions sum to 100% of the alarm score.

## Worked Example — Four Process Variables

Four standardized process variables are monitored:

- $T$ — Reactor Temperature
- $P$ — Reactor Pressure
- $F$ — Feed Flow
- $L$ — Tank Level

Their in-control correlation matrix reflects realistic physical coupling — temperature and pressure move together tightly, feed flow and level move together moderately:

$$\Sigma = \begin{pmatrix}1.0&0.8&0.3&0.1\\0.8&1.0&0.2&0.1\\0.3&0.2&1.0&0.6\\0.1&0.1&0.6&1.0\end{pmatrix}$$

At time point 5, a fault occurs. The deviation vector (each variable's value minus that variable's own in-control mean, in standard-deviation units) is:

$$d = (d_T, d_P, d_F, d_L) = (0.5,\ 0.5,\ 3.0,\ 2.5)$$

Computing $\Sigma^{-1}$ and its Cholesky factor $L$ gives:

$$\Sigma^{-1} = \begin{pmatrix}3.002&-2.308&-0.621&0.303\\-2.308&2.817&0.249&-0.201\\-0.621&0.249&1.741&-1.007\\0.303&-0.201&-1.007&1.594\end{pmatrix}, \qquad L^\top = \begin{pmatrix}1.733&-1.332&-0.358&0.175\\0&1.021&-0.223&0.032\\0&0&1.250&-0.750\\0&0&0&1.000\end{pmatrix}$$

## From Raw Measurements to Contributions — Step by Step

1. **Total alarm score:** $T^2 = d^\top \Sigma^{-1} d = 9.963$.
2. **Whiten:** $z = L^\top d = (-0.437,\ -0.080,\ 1.875,\ 2.500)$.
3. **Square each entry:** $z^2 = (0.191,\ 0.006,\ 3.516,\ 6.250)$.
4. **Verify the sum:** $\sum_j z_j^2 = 9.963 = T^2$ ✓ — exact, no leftover.
5. **Convert to percentage contribution:** divide each $z_j^2$ by $T^2$.

| Variable | Raw deviation $d_j$ (σ) | Whitened $z_j$ | Contribution $z_j^2$ | % of $T^2$ |
|---|---|---|---|---|
| $T$ | 0.5 | −0.437 | 0.191 | 1.9% |
| $P$ | 0.5 | −0.080 | 0.006 | 0.1% |
| $F$ | 3.0 | 1.875 | 3.516 | 35.3% |
| $L$ | 2.5 | 2.500 | 6.250 | 62.7% |

## Interpretation of the Example

Looking only at the raw deviations $d$, $F$ (3.0σ) looks like the worst offender and $L$ (2.5σ) second. After whitening, the ranking flips: $L$ is responsible for 62.7% of the total anomaly, while $F$ drops to 35.3%. This happens because $F$ and $L$ are correlated (0.6) in normal operation — part of $F$'s deviation is already "explained" by its expected co-movement with $L$, so only the unexplained remainder counts against it. $T$ and $P$, despite deviating by 0.5σ each, contribute almost nothing (2% combined) because that small joint shift is fully consistent with their normal 0.8 correlation — it is not anomalous at all once correlation is accounted for.

## Punchline

A naive per-variable check (raw deviation, or MYT's unconditional $d_j^2/\sigma_j^2$) would flag $F$ as the dominant fault driver and treat $T$/$P$ as equally suspicious as $F$/$L$. Hawkins' whitening exposes the opposite picture — $L$ is the true driver, $F$'s apparent shift is partly borrowed from its correlation with $L$, and $T$/$P$ are innocent bystanders — while guaranteeing the contributions add up exactly to the original $T^2$ alarm score.
