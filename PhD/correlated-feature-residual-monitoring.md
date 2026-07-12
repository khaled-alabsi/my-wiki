# Correlated-Feature Residual Distribution Monitoring

## Table of Contents

- [[#Core Idea|Core Idea]]
- [[#Short Positioning Statement|Short Positioning Statement]]
- [[#Mathematical Formulation|Mathematical Formulation]]
- [[#What Is Already Covered in Existing Literature|What Is Already Covered in Existing Literature]]
- [[#Where Novelty Could Still Exist|Where Novelty Could Still Exist]]
- [[#1. Correlated Feature Group Selection|1. Correlated Feature Group Selection]]
- [[#2. Residual Distribution Testing|2. Residual Distribution Testing]]
- [[#3. Fault Localization Across Multiple Residuals|3. Fault Localization Across Multiple Residuals]]
- [[#4. Nonlinear or Time-Varying Correlations|4. Nonlinear or Time-Varying Correlations]]
- [[#5. Multiple-Testing and False-Alarm Control|5. Multiple-Testing and False-Alarm Control]]
- [[#6. Streaming Monitoring and Concept Drift|6. Streaming Monitoring and Concept Drift]]
- [[#7. Interpretability for Industrial Operators|7. Interpretability for Industrial Operators]]
- [[#Additional Research Angles|Additional Research Angles]]
- [[#Candidate Method Name|Candidate Method Name]]
- [[#Possible Paper Abstract|Possible Paper Abstract]]
- [[#References and Related Search Directions|References and Related Search Directions]]

---

## Core Idea

The proposed idea is a **correlated-feature residual distribution monitoring** method for multivariable process monitoring.

The process has several measured features:

$$
X_1, X_2, \dots, X_p
$$

Some features are correlated because they describe the same physical phenomenon, the same subsystem, or coupled process behavior. Instead of monitoring each raw feature independently, the method constructs a **residual** or **contrast residual** between correlated variables or correlated groups of variables.

The central rule is:

> If the residual distribution remains equal to the expected in-control residual distribution, the process is considered in control. If the residual distribution changes, the process is considered out of control.

The important object is therefore not a prediction error in the machine-learning sense. The important object is the **distribution of the residual itself**.

---

## Short Positioning Statement

A concise formulation is:

> The method monitors process stability by constructing residual distributions from correlated feature pairs or correlated feature groups. Each residual measures how far one feature deviates from the shared behavior of its correlated companions. The process is considered in control when these residuals follow their learned in-control distributions, and out of control when one or more residual distributions shift.

A more research-style formulation is:

> We propose an interpretable pairwise and groupwise contrast-residual monitoring framework for multivariable process control. For each correlated feature pair or group, the method constructs residuals around the local shared behavior of the variables and monitors the empirical residual distribution against an in-control reference distribution.

---

## Mathematical Formulation

### Pairwise case

Assume two correlated process variables:

$$
X_i, X_j
$$

At time $t$, define their local shared level as the mean:

$$
m_{ij,t} = \frac{X_{i,t} + X_{j,t}}{2}
$$

Then define the residual of $X_i$ around the pair mean:

$$
r_{i|j,t} = X_{i,t} - m_{ij,t}
$$

Substituting the mean gives:

$$
r_{i|j,t}
=
X_{i,t} - \frac{X_{i,t}+X_{j,t}}{2}
=
\frac{X_{i,t}-X_{j,t}}{2}
$$

Similarly:

$$
r_{j|i,t}
=
X_{j,t} - \frac{X_{i,t}+X_{j,t}}{2}
=
\frac{X_{j,t}-X_{i,t}}{2}
=
-r_{i|j,t}
$$

So, for two variables, monitoring one residual is equivalent to monitoring the signed difference:

$$
d_{ij,t} = X_{i,t} - X_{j,t}
$$

or the scaled contrast:

$$
r_{ij,t} = \frac{X_{i,t}-X_{j,t}}{2}
$$

The in-control residual distribution is estimated from historical normal data:

$$
r_{ij,t} \sim F_{ij}^{IC}
$$

During monitoring, a new window of residuals is collected:

$$
\mathcal{R}_{ij}^{new}
=
\{r_{ij,t-w+1}, \dots, r_{ij,t}\}
$$

The process is in control if:

$$
\mathcal{R}_{ij}^{new} \approx F_{ij}^{IC}
$$

and out of control if:

$$
\mathcal{R}_{ij}^{new} \not\approx F_{ij}^{IC}
$$

The comparison can be based on normality, mean shift, variance shift, quantile shift, tail behavior, or a full nonparametric distribution-distance test.

---

### Groupwise case

Assume a correlated feature group:

$$
G = \{X_1, X_2, \dots, X_k\}
$$

Define the group mean at time $t$:

$$
m_{G,t} = \frac{1}{k}\sum_{\ell=1}^{k} X_{\ell,t}
$$

The residual for variable $X_i$ inside group $G$ is:

$$
r_{i,G,t} = X_{i,t} - m_{G,t}
$$

This residual measures whether $X_i$ still behaves consistently with its correlated group.

For example, with three correlated variables:

$$
m_{G,t} = \frac{X_{1,t}+X_{2,t}+X_{3,t}}{3}
$$

$$
r_{1,G,t}
=
X_{1,t}
-
\frac{X_{1,t}+X_{2,t}+X_{3,t}}{3}
$$

$$
r_{1,G,t}
=
\frac{2}{3}X_{1,t}
-
\frac{1}{3}X_{2,t}
-
\frac{1}{3}X_{3,t}
$$

This is a **contrast**, because the coefficients sum to zero:

$$
\frac{2}{3} - \frac{1}{3} - \frac{1}{3} = 0
$$

So the method can be described as **contrast-residual monitoring**.

---

### Weighted groupwise residual

If the variables have different variances or different importance, the group mean can be weighted:

$$
m_{G,t}^{(w)} = \sum_{\ell \in G} w_{\ell} X_{\ell,t}
$$

with:

$$
\sum_{\ell \in G} w_{\ell} = 1
$$

Then:

$$
r_{i,G,t}^{(w)} = X_{i,t} - m_{G,t}^{(w)}
$$

The weights may be chosen using inverse variance, process knowledge, correlation strength, or robust estimates.

---

### Robust residual

If the variables are noisy or heavy-tailed, the group center may be robust:

$$
m_{G,t}^{robust} = \operatorname{median}\{X_{\ell,t}: X_{\ell} \in G\}
$$

Then:

$$
r_{i,G,t}^{robust} = X_{i,t} - m_{G,t}^{robust}
$$

This makes the residual less sensitive to a single extreme feature.

---

## What Is Already Covered in Existing Literature

The broad principle is already covered in several neighboring fields.

First, **residual control charts** already monitor residuals instead of raw variables. Their central idea is that the residuals should follow a stable in-control distribution if the process is stable.

Second, **profile monitoring** monitors whether a relationship among variables remains stable over time. In many profile-monitoring methods, residuals from the relationship are charted to detect changes.

Third, **auxiliary-information-based control charts** use one or more correlated auxiliary variables to improve the monitoring of a main variable. Some use difference-type, ratio-type, regression-type, or memory-type statistics.

Fourth, **multivariate statistical process control** monitors multiple correlated variables jointly, often using Hotelling's $T^2$, MEWMA, MCUSUM, PCA/SPE, or covariance-monitoring charts. These methods already recognize that a process can go out of control through changes in the mean, variance, or correlation structure.

So the base idea:

> correlated variables create residuals, and residuals are monitored for stability

is not new.

However, the specific design can still be novel if it focuses on an interpretable, local, pairwise or groupwise residual-distribution framework.

---

## Where Novelty Could Still Exist

The method becomes more interesting if the contribution is not simply:

> We monitor residuals.

That is too broad and already covered.

A stronger contribution would be:

> We define an interpretable local residual-distribution monitoring framework for correlated feature groups, where the groups are automatically selected, the residual distributions are monitored nonparametrically, and fault localization is performed through the residual-dependency graph.

The seven strongest novelty dimensions are:

1. how correlated feature groups are selected;
2. how the residual distribution is tested;
3. how the responsible feature is localized;
4. how nonlinear or time-varying correlations are handled;
5. how false alarms are controlled when many residuals are monitored;
6. how the method works in streaming data with concept drift;
7. how the method remains interpretable for industrial operators.

Each of these points is detailed below.

---

## 1. Correlated Feature Group Selection

### Problem

The first design question is:

$$
\text{Which variables should be compared with which other variables?}
$$

If every variable is compared with every other variable, the number of residual charts grows quickly:

$$
\binom{p}{2} = \frac{p(p-1)}{2}
$$

For $p=100$ variables, that gives:

$$
\binom{100}{2} = 4950
$$

residual pairs.

That is too many for practical monitoring and will create many false alarms.

---

### How existing methods usually handle this

Classical multivariate SPC methods usually avoid explicit pair selection. They treat the whole vector as one multivariate object:

$$
\mathbf{X}_t =
(X_{1,t}, X_{2,t}, \dots, X_{p,t})^\top
$$

Then they use a global statistic such as Hotelling's $T^2$:

$$
T_t^2 =
(\mathbf{X}_t - \boldsymbol{\mu})^\top
\Sigma^{-1}
(\mathbf{X}_t - \boldsymbol{\mu})
$$

This handles correlation globally, but it does not naturally give a simple local statement like:

> Feature $X_i$ is no longer consistent with feature $X_j$.

PCA-based process monitoring handles correlation by learning latent variables. The residual space is monitored through SPE/Q-statistics:

$$
Q_t = \mathbf{e}_t^\top \mathbf{e}_t
$$

where $\mathbf{e}_t$ is the reconstruction residual.

This is powerful, but the resulting residual is global and latent-space-based, not directly pairwise or operator-friendly.

Auxiliary-information charts often assume the auxiliary variable is already known. They usually do not focus on automatic discovery of correlated feature groups.

Profile monitoring usually assumes the relationship structure is known in advance, such as a response variable and explanatory variables.

---

### Possible contribution

A useful contribution would be automatic correlated-group selection.

Examples:

#### Correlation-threshold graph

Build a graph:

$$
\mathcal{G} = (\mathcal{V}, \mathcal{E})
$$

where each feature is a node:

$$
\mathcal{V} = \{X_1, \dots, X_p\}
$$

and an edge exists if:

$$
|\rho_{ij}| \geq \tau
$$

Then residuals are only constructed for connected pairs.

Example:

$$
\rho_{12}=0.92,\quad \rho_{13}=0.15,\quad \rho_{23}=0.18
$$

Then monitor only:

$$
r_{12,t} = \frac{X_{1,t}-X_{2,t}}{2}
$$

because $X_1$ and $X_2$ are strongly correlated.

#### Top-$k$ correlated neighbors

For each feature $X_i$, choose only the top $k$ most correlated features:

$$
N_k(i) = \operatorname{TopK}_{j \neq i} |\rho_{ij}|
$$

Then construct:

$$
r_{i,N_k(i),t}
=
X_{i,t}
-
\frac{1}{k}\sum_{j \in N_k(i)}X_{j,t}
$$

This creates one residual distribution per feature instead of thousands of pairwise residuals.

#### Graphical-model selection

Instead of using marginal correlation, use conditional dependence. Estimate a sparse precision matrix:

$$
\Omega = \Sigma^{-1}
$$

If:

$$
\Omega_{ij} \neq 0
$$

then $X_i$ and $X_j$ are conditionally connected.

This avoids spurious correlation. For example, if $X_1$ and $X_2$ are correlated only because both depend on $X_3$, a simple correlation graph may connect them, but a conditional-dependence graph may not.

---

### What may be less used

What seems less common, and potentially more novel, is:

> selecting local correlated feature groups specifically for residual-distribution monitoring, then using that same graph both for detection and diagnosis.

Many existing methods either:
- monitor everything globally;
- assume the auxiliary variable is known;
- use PCA/latent residuals;
- or monitor covariance matrices directly.

A graph-selected local residual system would be more interpretable.

---

## 2. Residual Distribution Testing

### Problem

Once residuals are constructed, the next question is:

$$
\text{How do we decide whether the residual distribution has changed?}
$$

The simplest approach is to monitor only the mean:

$$
\mathbb{E}[r_t]
$$

But this misses cases where the mean stays stable while the variance, skewness, tails, or shape changes.

Example:

In control:

$$
r_t \sim \mathcal{N}(0,1)
$$

Out of control:

$$
r_t \sim \mathcal{N}(0,2^2)
$$

The mean is still zero, but the residual distribution changed.

Another example:

In control:

$$
r_t \sim \mathcal{N}(0,1)
$$

Out of control:

$$
r_t \sim t_3
$$

The mean may remain zero, but the tails become heavier.

---

### How existing methods usually handle this

Classical Shewhart charts monitor individual points using limits:

$$
\operatorname{UCL} = \mu_r + 3\sigma_r
$$

$$
\operatorname{LCL} = \mu_r - 3\sigma_r
$$

EWMA charts monitor smoothed residuals:

$$
z_t = \lambda r_t + (1-\lambda)z_{t-1}
$$

CUSUM charts accumulate persistent deviations:

$$
C_t^+ = \max(0, C_{t-1}^+ + r_t - k)
$$

$$
C_t^- = \min(0, C_{t-1}^- + r_t + k)
$$

These are good for mean shifts, especially small persistent shifts, but they may not fully test the residual distribution.

Covariance-monitoring charts focus on variance/covariance changes, but often as global multivariate statistics.

Profile monitoring may chart residual mean, variance, or model parameters, depending on the method.

---

### Possible contribution

Your method can be framed as **full residual-distribution monitoring**, not just residual mean monitoring.

Possible tests:

#### Kolmogorov-Smirnov statistic

Compare the empirical distribution of new residuals with the in-control distribution:

$$
D =
\sup_x
\left|
\hat{F}_{new}(x) - \hat{F}_{IC}(x)
\right|
$$

This detects general distribution changes.

#### Anderson-Darling statistic

More sensitive to tail changes:

$$
A^2 =
n
\int_{-\infty}^{\infty}
\frac{
\left(\hat{F}_{new}(x)-F_{IC}(x)\right)^2
}{
F_{IC}(x)(1-F_{IC}(x))
}
dF_{IC}(x)
$$

This is useful when out-of-control behavior appears in extreme residuals.

#### Wasserstein distance

Measure how much one distribution must be moved to become another:

$$
W_1(F_{IC}, F_{new})
=
\int_0^1
\left|
F_{IC}^{-1}(u) - F_{new}^{-1}(u)
\right|
du
$$

This is interpretable because it has the same unit as the residual.

#### Maximum Mean Discrepancy

Kernel-based distribution shift:

$$
\operatorname{MMD}^2(P,Q)
=
\mathbb{E}_{x,x' \sim P}[k(x,x')]
+
\mathbb{E}_{y,y' \sim Q}[k(y,y')]
-
2\mathbb{E}_{x \sim P, y \sim Q}[k(x,y)]
$$

This can detect nonlinear differences in distribution shape.

#### Quantile monitoring

Monitor residual quantiles:

$$
q_{\alpha}^{IC}
\quad \text{versus} \quad
q_{\alpha}^{new}
$$

For example:

$$
q_{0.95}^{new} > q_{0.95}^{IC} + \delta
$$

This is useful for tail-risk monitoring.

---

### What may be less used

The less-used angle is not simply “test residuals.” The stronger angle is:

> monitor the complete residual distribution of local correlated-feature contrasts using nonparametric two-sample or window-vs-reference tests.

This differs from many classical charts that reduce the residual sequence to one statistic such as mean shift, EWMA, CUSUM, or variance.

---

## 3. Fault Localization Across Multiple Residuals

### Problem

If one residual distribution changes, the pair or group involved is suspicious.

But if many residual distributions change at once, we need to infer:

$$
\text{Which original feature is most likely responsible?}
$$

Example:

Suppose we monitor three residual pairs:

$$
r_{12,t}, \quad r_{13,t}, \quad r_{23,t}
$$

If these two shift:

$$
r_{12,t}, \quad r_{13,t}
$$

but this one does not:

$$
r_{23,t}
$$

then the likely root cause is:

$$
X_1
$$

because $X_1$ appears in both abnormal residuals.

---

### How existing methods usually handle this

Hotelling's $T^2$ detects a multivariate deviation, but interpretation requires extra decomposition.

Common interpretation tools include:
- contribution plots;
- variable-wise decomposition;
- principal-component loadings;
- univariate follow-up charts;
- diagnostic rules after the multivariate chart signals.

PCA monitoring often uses contribution plots to identify which variables contribute most to the SPE or $T^2$ signal.

Covariance-monitoring methods may detect that the covariance matrix changed, but identifying the exact local relationship that changed can be difficult.

Auxiliary-information charts may localize to the main variable and auxiliary variable, but they are often not designed as a full graph of pairwise residual relationships.

---

### Possible contribution

Represent residual alarms as a graph.

Let:

$$
A_{ij,t} =
\begin{cases}
1, & \text{if residual } r_{ij} \text{ is abnormal at time } t \\
0, & \text{otherwise}
\end{cases}
$$

Define a feature-level abnormality score:

$$
S_i(t) = \sum_{j: (i,j)\in \mathcal{E}} A_{ij,t}
$$

A feature with a large score is involved in many abnormal residuals.

Weighted version:

$$
S_i(t) =
\sum_{j: (i,j)\in \mathcal{E}}
w_{ij}
D_{ij,t}
$$

where $D_{ij,t}$ is a distribution-distance statistic such as KS, Wasserstein, or MMD.

Example:

| Residual pair | Abnormality distance |
|---|---:|
| $r_{12}$ | 0.80 |
| $r_{13}$ | 0.75 |
| $r_{23}$ | 0.05 |

Then:

$$
S_1 = 0.80 + 0.75 = 1.55
$$

$$
S_2 = 0.80 + 0.05 = 0.85
$$

$$
S_3 = 0.75 + 0.05 = 0.80
$$

So $X_1$ is the most likely source.

---

### What may be less used

The possible novelty is:

> using the residual alarm graph itself as a diagnostic object.

This is stronger than simply saying “the chart signals.” It gives:
- local residual alarms;
- feature-level aggregation;
- graph-based root-cause scoring;
- interpretable explanation.

---

## 4. Nonlinear or Time-Varying Correlations

### Problem

Correlation may not be linear or stable.

Example of nonlinear relation:

$$
X_2 \approx X_1^2
$$

If we use only:

$$
r_{12,t} = X_{1,t} - X_{2,t}
$$

the residual may look strange even when the process is normal.

Example of time-varying relation:

$$
\rho_{12}(t)
$$

may change between operating regimes.

A compressor, turbine, chemical reactor, or production line may behave differently depending on load, recipe, temperature, or speed.

---

### How existing methods usually handle this

Linear SPC methods often assume stable mean and covariance.

PCA captures linear correlation structure. Kernel PCA and autoencoders capture nonlinear structure, but the residuals become less directly interpretable.

Profile monitoring handles functional relationships, including nonlinear profiles, but it usually assumes a defined response-explanatory structure.

State-space and dynamic models handle autocorrelation and time-varying behavior, but they can become model-heavy.

---

### Possible contribution

Instead of using one global residual definition, define residuals conditionally by regime.

Let $C_t$ be a context variable such as operating mode, load, recipe, or speed.

Then estimate an in-control residual distribution conditional on context:

$$
r_{ij,t} \sim F_{ij}^{IC}(\cdot \mid C_t)
$$

The monitoring rule becomes:

$$
\mathcal{R}_{ij}^{new}(C_t)
\approx
F_{ij}^{IC}(\cdot \mid C_t)
$$

For nonlinear relations, use local or rank-based residuals.

#### Rank residual

Instead of comparing raw values, compare normalized ranks:

$$
u_{i,t} = \hat{F}_i(X_{i,t})
$$

$$
u_{j,t} = \hat{F}_j(X_{j,t})
$$

Then monitor:

$$
r_{ij,t}^{rank} = u_{i,t} - u_{j,t}
$$

This captures whether the two variables remain aligned in distribution, even if their units differ.

#### Copula residual

Model the dependence structure separately from marginal distributions.

Let:

$$
U_i = F_i(X_i), \quad U_j = F_j(X_j)
$$

Then monitor whether the joint behavior:

$$
C_{ij}(U_i,U_j)
$$

remains stable.

This is closer to monitoring dependence, not just mean difference.

#### Local residual by operating region

For a context bin $b$:

$$
r_{ij,t}^{(b)}
=
X_{i,t} - m_{ij,t}^{(b)}
$$

where:

$$
C_t \in b
$$

The in-control reference distribution is then:

$$
F_{ij,b}^{IC}
$$

not one global distribution.

---

### What may be less used

A possible research gap is:

> interpretable local residual distributions that are conditioned on operating regime, without moving fully into black-box autoencoder or kernel-PCA monitoring.

That could be practically valuable.

---

## 5. Multiple-Testing and False-Alarm Control

### Problem

If many residual distributions are monitored, false alarms become serious.

If each residual chart has false-alarm probability $\alpha$, and there are $M$ residual charts, then the probability of at least one false alarm is approximately:

$$
1 - (1-\alpha)^M
$$

For example, if:

$$
\alpha = 0.01
$$

and:

$$
M = 100
$$

then:

$$
1-(1-0.01)^{100}
\approx
0.634
$$

So even if every residual is normal, there is a high chance of at least one false alarm.

---

### How existing methods usually handle this

Classical multivariate charts avoid this by using a single global statistic.

For example:

$$
T_t^2
$$

or:

$$
Q_t
$$

or:

$$
\operatorname{MEWMA}_t
$$

This controls the alarm rate globally, but loses local interpretability.

Univariate chart systems sometimes use Bonferroni correction:

$$
\alpha_{local} = \frac{\alpha_{global}}{M}
$$

But Bonferroni can be too conservative.

False discovery rate methods, such as Benjamini-Hochberg, control the expected proportion of false discoveries among alarms.

---

### Possible contribution

Use a two-stage monitoring rule.

#### Stage 1: global residual-network alarm

Aggregate all residual distances:

$$
G_t = \max_{(i,j)\in \mathcal{E}} D_{ij,t}
$$

or:

$$
G_t = \sum_{(i,j)\in \mathcal{E}} D_{ij,t}
$$

or:

$$
G_t = \sum_{(i,j)\in \mathcal{E}} \mathbb{I}(D_{ij,t} > h_{ij})
$$

Signal only if:

$$
G_t > H
$$

#### Stage 2: local diagnosis

After global alarm, inspect individual residuals:

$$
D_{ij,t}
$$

and feature scores:

$$
S_i(t)
$$

This reduces false alarms while preserving interpretability.

---

### What may be less used

A strong novelty angle is:

> combining residual-distribution monitoring with structured false-alarm control over a correlation graph.

This is especially useful when many correlated feature pairs exist.

---

## 6. Streaming Monitoring and Concept Drift

### Problem

In real industrial systems, the in-control distribution may slowly change because of:
- sensor aging;
- equipment wear;
- seasonal effects;
- raw-material variation;
- maintenance;
- operating-mode changes.

This creates concept drift.

If the reference distribution is fixed forever:

$$
F_{ij}^{IC}
$$

then the method may produce false alarms as the process naturally evolves.

But if the reference distribution updates too aggressively, the method may absorb real faults and stop detecting them.

---

### How existing methods usually handle this

EWMA and CUSUM handle gradual shifts by using memory.

EWMA:

$$
z_t = \lambda r_t + (1-\lambda)z_{t-1}
$$

with smaller $\lambda$ giving longer memory.

Adaptive charts update parameters over time, but they must avoid learning from out-of-control data.

Some machine-learning monitoring methods use sliding windows, but they may not distinguish between acceptable drift and faults.

---

### Possible contribution

Use a protected update rule.

Maintain a reference window:

$$
\mathcal{R}_{ij}^{ref}
$$

and a monitoring window:

$$
\mathcal{R}_{ij}^{new}
$$

Update the reference only if the residual passes the in-control test:

$$
D(\mathcal{R}_{ij}^{new}, \mathcal{R}_{ij}^{ref}) \leq h
$$

Then:

$$
\mathcal{R}_{ij}^{ref}
\leftarrow
(1-\eta)\mathcal{R}_{ij}^{ref}
+
\eta \mathcal{R}_{ij}^{new}
$$

Conceptually:

> update only when the process appears normal.

Another option is to maintain two references:

$$
F_{ij}^{short}
$$

and:

$$
F_{ij}^{long}
$$

A sudden difference between short-term and long-term distributions signals a fault. A slow consistent difference may indicate drift.

---

### What may be less used

A useful contribution is:

> residual-distribution monitoring with safe adaptation, where the in-control residual reference is updated only under statistical evidence of stability.

This is practically important and not always handled cleanly in classical SPC.

---

## 7. Interpretability for Industrial Operators

### Problem

Many multivariate methods detect anomalies but are difficult to explain.

A global statistic such as:

$$
T^2 = 37.4
$$

or:

$$
Q = 12.8
$$

may be statistically meaningful, but an operator wants to know:

> Which variables stopped agreeing with each other?

Your residual method can answer this directly.

---

### How existing methods usually handle this

Hotelling's $T^2$ gives a global alarm. Extra decomposition is needed.

PCA/SPE gives latent residual alarms. Contribution plots help, but operators may not understand latent components.

Autoencoder methods give reconstruction errors. They are often powerful but can be black-box.

Covariance charts signal correlation or covariance changes, but local explanation may require extra work.

---

### Possible contribution

The residual system can produce human-readable explanations.

Example:

> The process is out of control because the residual distribution between inlet temperature and outlet temperature shifted. Historically, their residual was centered near zero with standard deviation $0.4$. In the last 30 samples, the residual median shifted to $1.2$, and the upper tail became wider.

A diagnostic table could show:

| Residual | Change type | Severity | Interpretation |
|---|---:|---:|---|
| $r_{\text{temp,in},\text{temp,out}}$ | median shift | high | temperature relation changed |
| $r_{\text{pressure},\text{flow}}$ | variance increase | medium | flow-pressure coupling unstable |
| $r_{\text{speed},\text{vibration}}$ | tail increase | high | abnormal vibration at normal speed |

The method can report:
- which residual distribution changed;
- whether the change is mean, variance, skew, or tail;
- which original feature appears in many abnormal residuals;
- whether the fault is local or system-wide.

---

### What may be less used

The possible novelty is:

> operator-facing residual-distribution explanations instead of latent-space anomaly scores.

This is not just cosmetic. In industrial monitoring, interpretability affects whether alarms are trusted and acted upon.

---

## Additional Research Angles

### 8. Residual normalization

Raw residuals may not be comparable across feature pairs.

For pair $(i,j)$, define:

$$
z_{ij,t}
=
\frac{r_{ij,t} - \mu_{ij}^{IC}}{\sigma_{ij}^{IC}}
$$

Then all residuals are on a comparable scale.

Robust version:

$$
z_{ij,t}^{robust}
=
\frac{r_{ij,t} - \operatorname{median}(r_{ij}^{IC})}
{\operatorname{MAD}(r_{ij}^{IC})}
$$

where:

$$
\operatorname{MAD}(r)
=
\operatorname{median}(|r - \operatorname{median}(r)|)
$$

This helps compare alarms across variables with different units.

---

### 9. Directional residual interpretation

For pairwise residual:

$$
r_{ij,t} = \frac{X_{i,t}-X_{j,t}}{2}
$$

a positive shift means:

$$
X_i > X_j
$$

relative to normal behavior.

A negative shift means:

$$
X_i < X_j
$$

relative to normal behavior.

This is useful for diagnosis.

---

### 10. Residual-shape classification

The residual distribution can change in different ways.

Mean shift:

$$
\mathbb{E}[r] \text{ changes}
$$

Variance shift:

$$
\operatorname{Var}(r) \text{ changes}
$$

Tail shift:

$$
P(|r| > c) \text{ increases}
$$

Skewness shift:

$$
\mathbb{E}\left[\left(\frac{r-\mu}{\sigma}\right)^3\right] \text{ changes}
$$

A practical method could classify alarms into:
- location change;
- spread change;
- tail change;
- asymmetry change;
- multimodality change.

This gives richer diagnostic information than a binary alarm.

---

### 11. Difference between raw-feature monitoring and residual monitoring

Raw-feature monitoring may miss relationship faults.

Example:

In control:

$$
X_1 \sim \mathcal{N}(10,1)
$$

$$
X_2 \sim \mathcal{N}(10,1)
$$

and:

$$
X_1 - X_2 \sim \mathcal{N}(0,0.2^2)
$$

Suppose out of control:

$$
X_1 \sim \mathcal{N}(10.3,1)
$$

$$
X_2 \sim \mathcal{N}(9.7,1)
$$

Each raw variable may still look acceptable. But:

$$
X_1 - X_2 \sim \mathcal{N}(0.6,0.2^2)
$$

The residual clearly shifted.

This is the central value of the method:

> It detects when correlated variables stop agreeing, even if each variable alone still looks normal.

---

## Candidate Method Name

Possible names:

1. **Correlated-Feature Residual Distribution Monitoring**
2. **Pairwise Residual Distribution Monitoring**
3. **Contrast-Residual Monitoring for Multivariable Processes**
4. **Graph-Based Residual Distribution Monitoring**
5. **Local Correlation Residual Monitoring**
6. **Interpretable Residual Distribution Monitoring for Correlated Features**

The most accurate name is probably:

> **Graph-Based Contrast-Residual Distribution Monitoring**

This name captures:
- local correlated feature groups;
- residuals as contrasts;
- distribution-level monitoring;
- graph-based detection and diagnosis.

---

## Possible Paper Abstract

Multivariable process monitoring commonly relies on global statistics such as Hotelling's $T^2$, MEWMA, PCA/SPE, or covariance-monitoring charts. Although these methods are effective for detecting multivariate changes, their diagnostic interpretation can be difficult for process operators. This work proposes a graph-based contrast-residual distribution monitoring framework for correlated process features. In Phase I, correlated feature pairs or groups are selected using correlation, conditional dependence, or domain constraints. For each selected pair or group, a contrast residual is constructed by comparing each feature with the local shared behavior of its correlated companions. The in-control distribution of each residual is then estimated nonparametrically. In Phase II, sliding windows of residuals are compared against the corresponding in-control residual distributions using distribution-distance tests. Out-of-control behavior is signaled when one or more residual distributions deviate significantly from their reference distributions. A residual alarm graph is used for fault localization by identifying features involved in multiple abnormal residuals. The proposed framework provides local, interpretable alarms that indicate which process relationships changed and how their residual distributions changed. This makes the method especially suitable for industrial processes where correlated features must remain mutually consistent and where operator-facing explanations are required.

---

## References and Related Search Directions

The following references and literature areas are relevant for positioning the idea.

### Residual control charts

Residual control charts monitor residuals instead of raw process variables. They are relevant because the core proposed statistic is the residual distribution.

Search terms:

```text
residual control chart correlated variables
residual-based control chart multivariate process monitoring
Pearson residual control chart correlated variables
deviance residual control chart process monitoring
```

Relevant example:

- Pearson and deviance residual-based control charts have been used for monitoring complex processes with correlated variables, including cases with multicollinearity.

### Profile monitoring

Profile monitoring treats process quality as the stability of a relationship among variables. This is close because the residual distribution represents whether the relationship among correlated features remains stable.

Search terms:

```text
profile monitoring residual control chart
residual profile monitoring process control
nonparametric profile monitoring residuals
```

Relevant point:

- Profile monitoring is commonly described as monitoring a relationship between a response variable and one or more explanatory variables over time.

### Auxiliary-information-based charts

Auxiliary-information-based charts use correlated auxiliary variables to improve monitoring of a target variable. This is related when one variable is monitored relative to another correlated variable.

Search terms:

```text
auxiliary information based control chart correlated auxiliary variable
difference type estimator control chart auxiliary information
EWMA auxiliary information correlated variable
```

Relevant point:

- Many auxiliary-information methods use correlated variables to construct more sensitive monitoring statistics, including difference-type and memory-type charts.

### Multivariate SPC and covariance/correlation monitoring

Multivariate SPC directly addresses correlated quality characteristics. Covariance/correlation monitoring is relevant because the proposed residual distributions are sensitive to changes in the relationship among variables.

Search terms:

```text
multivariate statistical process control covariance matrix monitoring
monitoring correlation structure multivariate process
Hotelling T2 covariance shift correlation structure
MEWMA covariance monitoring multivariate process
```

Relevant point:

- Multivariate processes can go out of control through mean shifts, variance shifts, or changes in correlation structure.

### PCA/SPE residual monitoring

PCA/SPE methods monitor residual variation after removing latent correlated structure.

Search terms:

```text
PCA SPE residual monitoring multivariate statistical process control
Q statistic residual space process monitoring
latent variable residual process monitoring
```

Relevant point:

- PCA/SPE is powerful for high-dimensional correlated systems, but the residuals are latent/global rather than simple pairwise or groupwise residual distributions.

---

## Final Evaluation

The base idea is not fully new because residual monitoring, profile monitoring, auxiliary-information charts, and covariance-monitoring methods already cover related principles.

The potentially publishable angle is not:

> monitor residuals of correlated variables.

The stronger angle is:

> construct interpretable pairwise or groupwise contrast residuals from automatically selected correlated feature groups, monitor the full residual distributions using nonparametric tests, control false alarms across the residual graph, and use the abnormal residual graph for fault localization.

That version has a clearer methodological contribution.
