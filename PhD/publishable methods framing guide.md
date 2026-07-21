# Publishable Methods from the TEP Catalog
## Academic Positioning: Related Work, Prior Art, Novelty Deltas, and Claim Framing

**Scope.** This document treats each of the five publication candidates as a paper-in-preparation. For every candidate it provides: (i) a technical summary; (ii) a structured relation-to-prior-work analysis (identical work, closely related work, bordering work from other fields); (iii) an explicit statement of what is already done and by whom, versus what remains claimable as new (the "delta"); (iv) a readiness assessment; and (v) recommended claim language. Numbered citations refer to the consolidated reference list in Section 7.

**General principle.** None of the five candidates supports the claim "we introduce a completely new state-of-the-art method." In statistical process monitoring, virtually every algorithmic primitive here (CUSUM, regression residuals, discriminant projections, dependency matrices, conformal p-values) has a 20–70 year history. The defensible contribution types are: a *surprising empirical result with an ablation-based explanation* (CGRM), a *repurposing of an established quantity for a new task* (CGCI_MON), a *theoretical bridge between two known constructions* (FDP_CUSUM), a *named phenomenon plus a fix* (dependency-structure bundle), and a *transferred statistical guarantee* (CAR). Reviewers in Technometrics, Journal of Quality Technology, Journal of Process Control, Computers & Chemical Engineering, and Chemometrics and Intelligent Laboratory Systems reward precise deltas and punish inflated ones.

---

# 1. CGRM — Localized Regression-Residual CUSUM for Incipient Faults

## 1.1 Method summary
For each of five temperature variables, a Ridge regression (α = 1) predicts the target from its ten most-correlated covariates; the standardized prediction residual drives a two-sided CUSUM with allowance k = 0.25; the five channel alarms are OR-combined. Reported performance: F1 ≈ 0.90 on TEP fault 3 (FPR 0.017, ARL1 ≈ 94), against a literature in which fault 3 is conventionally treated as undetectable.

## 1.2 Relation to prior work

**Identical work (the algorithmic ancestor).** The core construction — monitor the residual of a variable regressed on other in-control variables, and place a CUSUM on that residual — is *exactly* the regression-adjusted variables framework of Hawkins [1], extended in [2], with roots in Mandel's regression control chart [3] and Zhang's cause-selecting charts [4]. Hawkins [1] explicitly proposed CUSUM charts on regression-adjusted variables; Hawkins & Olwell [9] give the standard treatment of CUSUM design (choice of allowance k, two-sided schemes). A paper that presents CGRM as a new *method* will be desk-rejected by any reviewer who knows [1].

**Closely related work.** Hauck, Runger & Montgomery [5] extended regression adjustment to *grouped* variables — selecting subsets of covariates per target — which is structurally the closest published relative of CGRM's per-target correlated-predictor sets. Ridge (rather than OLS) regression adjustment and correlation-ranked predictor selection are implementation-level variations, not conceptual ones. On the benchmark side, Russell, Chiang & Braatz [11] and the companion monograph [12] established the canonical TEP results in which PCA, DPCA, and CVA exhibit missed-detection rates near 99% on faults 3, 9, and 15; this is the literature CGRM's empirical claim is measured against. Pilario & Cao's canonical variate dissimilarity analysis (CVDA) [15], with kernel extensions [16], is the landmark "incipient faults are detectable after all" line of work and the mandatory head-to-head baseline.

**Bordering work.** Deep-learning TEP papers occasionally report high average detection on incipient-fault groups; such figures are usually averages over several faults or are accompanied by uncontrolled false-alarm rates. Any comparison must be per-fault and must pair every detection rate with its false-alarm rate on matched data splits and control-limit conventions (see the caveats in [11], [12], and the dataset documentation of Rieth et al. [17]).

**What is already done, and by whom.**
- Residual monitoring of regressed variables + CUSUM: Hawkins [1], [2]; Mandel [3].
- Cause-selecting philosophy (monitor an output adjusted for its inputs): Zhang [4].
- Grouped/subset covariate selection for regression adjustment: Hauck, Runger & Montgomery [5].
- CUSUM design theory (k, h, ARL): Page [8]; Hawkins & Olwell [9]; Crosier [6]; Healy [7].
- TEP hard-fault benchmark context: Russell, Chiang & Braatz [11]; Chiang, Russell & Braatz [12]; CVDA [15].

**What remains new (the delta).**
1. The *empirical finding* that a small-allowance (k = 0.25) two-sided CUSUM on localized ridge residuals detects TEP fault 3 at F1 ≈ 0.90 with low FPR — if it replicates on the standard splits, this exceeds every credible published single-fault-3 result.
2. The *explanation*: an ablation isolating which ingredient (localized predictor sets vs. full-covariate adjustment; k = 0.25 vs. 0.5; ridge vs. OLS; two-sided vs. one-sided) produces the effect, plus a process-level account of why the fault-3 signature is linearly recoverable at the raw-variable level while remaining invisible to PCA-subspace statistics.
3. Secondary: a systematic comparison of regression-adjustment charts against modern deep baselines on the incipient-fault subset — a benchmark contribution.

## 1.3 Readiness assessment
Not submission-ready. Required: (a) replication on the canonical Downs & Vogel splits [10] and the Rieth et al. extended dataset [17] with FAR reported next to every detection figure; (b) the ablation in §1.2; (c) head-to-head against CVDA [15] and against plain Hawkins adjustment; (d) removal or explicit defense of the word "causal" — the graph is correlation-derived, and causal-inference reviewers will object (rename, e.g., "localized regression-residual CUSUM").

## 1.4 Recommended framing
Genre: *surprising result + explanation*. Claim skeleton:

> "We revisit regression-adjusted monitoring (Hawkins, 1991) with localized predictor sets and a small-allowance two-sided CUSUM, and show that this classical construction detects Tennessee Eastman fault 3 — long treated as undetectable (Russell et al., 2000) — with F1 ≈ 0.90 at a false-alarm rate of X%, exceeding published single-fault results including recent deep-learning detectors and CVDA (Pilario & Cao, 2018). An ablation attributes the effect to [ingredient], and we explain why the fault-3 signature survives at the raw-variable level but not in reduced subspaces."

Do **not** claim a new method; claim a result, an ablation, and an explanation. Cite [1]–[5] in the second paragraph of the introduction, before any reviewer can cite them at you.

---

# 2. CGCI_MON — Causality-Structure Drift as a Detection Statistic

## 2.1 Method summary
In sliding 100-sample windows over 8 variables, the conditional Granger causality index (CGCI) is re-estimated for every ordered pair (lag-2 VAR; log-ratio of restricted vs. full residual sums of squares); the Frobenius distance between the windowed CGCI matrix and its in-control baseline drives a one-sided CUSUM. Reported: hard-fault recall 0.419 (second-best in the catalog), overall FPR 0.399 (disqualifying as-is).

## 2.2 Relation to prior work

**Identical work.** None found for the specific construction (online sequential *detection* via CUSUM on CGCI-matrix drift).

**Closely related work.** Granger causality [18] is heavily used in process monitoring — but almost exclusively for *root-cause diagnosis after an alarm*: Yuan & Qin [19] locate the source of plant-wide oscillations via time- and frequency-domain Granger causality; Lindner et al. [20] compare Granger causality and transfer entropy for oscillation diagnosis; Duan et al. [21] use transfer entropy for direct-causality mapping; a substantial recent literature (graph attention networks with Granger maps, error-correction-model Granger diagnosis, hierarchical Granger frameworks) continues this diagnosis-oriented use on TEP. Closest in spirit is an IEEE conference framework that compares causality intensity before and after a fault to refine propagation paths — but that comparison is performed *offline, post-detection, for diagnosis*, not as a sequential detection chart. This paper must be cited and differentiated explicitly.

**Bordering work.** Offline change-point estimation in dependency structures: Gaussian graphical-model / Markov-random-field change-point estimation (Roy, Atchadé & Michailidis [28]) solves the retrospective version of the problem in high dimensions. Network-monitoring SPC (charts on network summary statistics) is a related but distinct thread. The distinction to draw: offline single-change-point estimation with asymptotic theory (their contribution) versus online sequential detection with ARL calibration (yours).

**What is already done, and by whom.**
- Granger/transfer-entropy causal maps for TEP root-cause diagnosis: [19], [20], [21] and successors.
- Before/after causality-intensity comparison (offline, diagnostic): IEEE 2020 conference framework noted above.
- Offline structural change-point estimation: [28].

**What remains new (the delta).**
1. Inverting the standard pipeline: the causality structure is monitored *continuously as the first-line detection statistic*, on the hypothesis that incipient, PID-masked faults rewire dependency structure before they move variable levels.
2. The accompanying evidence: top-tier recall on TEP faults 3/9/15, which value-based charts miss.
3. The methodological work that makes it usable: variance control of windowed CGCI estimation (regularized VAR fits, longer overlapping windows, or a self-normalized drift statistic) and calibration of the null distribution of the Frobenius drift so the threshold carries a stated in-control ARL. Solving the FPR problem *is* the paper's technical contribution; without it there is no publishable chart.

## 2.3 Readiness assessment
Requires substantial work: (a) FPR 0.399 must be reduced by an order of magnitude via the variance-control machinery above; (b) null calibration (analytic or Monte Carlo) of the drift statistic under stationary in-control dynamics; (c) either scale beyond 8 variables or justify the restriction with a computational analysis and a principled variable-selection step; (d) detection-delay comparison against CVDA [15] and against the diagnosis-oriented Granger literature repurposed naively.

## 2.4 Recommended framing
Genre: *repurposing an established quantity* ("X has been used for A; we show it serves as B"). Claim skeleton:

> "Granger-causal maps are established tools for root-cause diagnosis in industrial processes, applied after an alarm from a separate detection chart (Yuan & Qin, 2014; Lindner et al., 2019). We invert this pipeline: the conditional Granger causality structure is itself monitored sequentially as a first-line detection statistic. We show that incipient valve faults in the Tennessee Eastman Process, which barely perturb variable levels under closed-loop compensation, measurably alter the process's dependency structure well before conventional charts respond. We address the estimation-variance problem inherent to windowed causality estimation via [fix], yielding a chart with calibrated in-control run length."

---

# 3. FDP_CUSUM — Directed CUSUM from Synthetic Contrasts

## 3.1 Method summary
A synthetic "shifted" class is created by adding +0.3σ to ten temperature variables of the normal training data; the Fisher discriminant direction between normal and shifted classes is computed; monitoring is a two-sided CUSUM on the one-dimensional projection. Reported: overall F1 0.759, FPR 0.087, hard-fault F1 0.421, with a distinctive fault-15 profile (slow, ARL1 ≈ 412, but precision 0.862).

## 3.2 Relation to prior work

**Identical work.** None found for the exact construction; however, the two constituent halves are both classical, and one very close relative exists (next paragraph).

**Closely related work — this delta is narrower than it first appears.** Hwang, Runger & Tuv [22] ("Multivariate statistical process control with artificial contrasts") and Hu, Runger & Tuv [23] ("Tuned artificial contrasts to detect signals") already proposed *simulating out-of-control observations representing postulated shifts and converting monitoring into supervised learning*, with the control region learned by a classifier. This is the same core trick — synthetic fault data standing in for unavailable real fault data. FDP_CUSUM differs in that it extracts a *closed-form linear direction* (Fisher discriminant) and monitors it with a *sequential CUSUM* rather than learning a nonparametric classifier boundary; but the artificial-contrast lineage must be acknowledged as the conceptual precedent, not discovered by reviewers. On the second half: Healy [7] showed that the optimal multivariate CUSUM for a *known* shift δ reduces to a univariate CUSUM on the projection Σ⁻¹δ — and the Fisher direction between a distribution and its mean-shifted copy is exactly w ∝ Σ⁻¹δ. Fisher discriminant analysis for fault detection/diagnosis (with real fault data) is standard: Chiang, Russell & Braatz [24].

**Bordering work.** One-class classification with synthetic outliers, and contrastive/negative-sampling approaches in machine-learning anomaly detection, use the same generate-a-contrast device in a nonsequential setting.

**What is already done, and by whom.**
- Optimal directed CUSUM for a known shift (projection Σ⁻¹δ): Healy [7].
- Synthetic/artificial out-of-control data to design monitors without fault data: Hwang, Runger & Tuv [22]; Hu, Runger & Tuv [23].
- FDA-based fault detection with real fault data: Chiang, Russell & Braatz [24].

**What remains new (the delta).**
1. The *bridge theorem*: making explicit that the Fisher direction extracted from a synthetic mean-shift contrast coincides with Healy's optimal CUSUM direction for that postulated shift — turning "pick a synthetic shift" into an interpretable, theory-backed design parameter (which fault family the chart is optimized for), with the full sequential ARL machinery of the CUSUM attached.
2. A robustness analysis over the synthetic-shift specification (magnitude, sign, variable subset), absent from [22], [23], which tuned to specific postulated faults.
3. A principled multi-direction extension (a small bank of contrast directions covering plausible shift subspaces) with multiplicity-corrected calibration.

## 3.3 Readiness assessment
Moderate work required: (a) state and prove the equivalence w ∝ Σ⁻¹δ and its consequence for ARL optimality under the postulated shift; (b) sensitivity study over the contrast specification; (c) explain the fault-15 asymmetry (slow but precise) — a shift-direction-misalignment analysis would do this naturally; (d) cite and differentiate [22], [23] prominently.

## 3.4 Recommended framing
Genre: *design-method contribution grounded in a known optimality result*. Claim skeleton:

> "Directed multivariate CUSUMs are ARL-optimal when the fault direction is known (Healy, 1987), but no fault data exist at commissioning time. Building on the artificial-contrast idea of Hwang, Runger & Tuv (2007), we derive directed sequential monitors without fault data: perturbing normal operating data along physically plausible axes and extracting the Fisher discriminant direction, which we show coincides with the optimal CUSUM direction for the postulated shift. Fault-direction specification thereby becomes an interpretable design parameter with explicit run-length guarantees, requiring no classifier training and no fault records."

---

# 4. The Dependency-Structure Bundle — PCOR_CUSUM, SYMRANK_MON, SPECTRAL_CUSUM

## 4.1 Method summary
Three monitors share one skeleton: re-estimate a structural summary in a sliding window — the partial-correlation matrix (PCOR_CUSUM), the Spearman rank-correlation matrix (SYMRANK_MON), or the Bartlett power spectral density (SPECTRAL_CUSUM) — measure its Frobenius (or normalized L2) distance to an in-control baseline, and CUSUM the distance. Empirically all three attain top-tier hard-fault recall (0.40–0.42) and all three fail on FPR (0.37–0.40) for the same reason: windowed matrix-estimation variance dominates the chart.

## 4.2 Relation to prior work

**Identical work.** None found for the unified online-CUSUM-on-structure-drift formulation across these three statistics on TEP; each individual thread has neighbors below.

**Closely related work.**
- *Covariance/correlation structure monitoring* is an established SPC subfield (charts for the covariance matrix, |S| charts, eigenvalue-based dispersion charts); PCOR_CUSUM's specific target — the *partial*-correlation (precision-derived) matrix — connects to Gaussian graphical models, where offline change-point estimation is developed (Roy, Atchadé & Michailidis [28]) and regularized estimation is standard (graphical lasso, Friedman, Hastie & Tibshirani [39]; shrinkage, Ledoit & Wolf [38]).
- *Rank-based multivariate SPC* exists in strong form: Qiu & Hawkins [25], [26] built rank-based multivariate CUSUMs — but those monitor *location* using ranks, not drift of the rank-*correlation matrix*; the distinction (robust location monitoring vs. dependence-structure monitoring) is the differentiator SYMRANK_MON must state.
- *Frequency-domain process monitoring*: Thornhill's spectral methods for detecting and diagnosing plant-wide oscillations [27] are the canonical relative of SPECTRAL_CUSUM; again the prior use is oscillation detection/diagnosis, not a calibrated sequential PSD-drift chart.

**Bordering work.** High-dimensional two-sample tests for covariance/precision matrices; dynamic-network change detection in statistics and neuroscience (time-varying functional connectivity), where windowed correlation drift is routinely monitored but without SPC-style run-length calibration.

**What is already done, and by whom.**
- Covariance and dispersion charts; eigenstructure monitoring: classical SPC literature.
- Rank-based multivariate CUSUM (location): Qiu & Hawkins [25], [26].
- Spectral detection of oscillations: Thornhill et al. [27].
- Offline graphical-model change points and regularized precision estimation: [28], [38], [39].

**What remains new (the delta).**
1. The *unified formulation*: window → structural summary → matrix drift distance → CUSUM, instantiated with parametric (partial correlation), nonparametric (rank correlation), and frequency-domain (PSD) summaries, evaluated on a common benchmark.
2. The *named finding*: structure-drift statistics achieve the best incipient-fault (TEP 3/9/15) recall in a 200+-method catalog, and their failure mode is uniformly estimation variance, not insensitivity — i.e., the binding constraint is statistical, not informational. A paper that names and demonstrates a shared failure mode across a family is a citable contribution.
3. The *fix*: shrinkage/graphical-lasso estimation [38], [39], longer overlapping windows, or self-normalized drift statistics, shown to reduce FPR into an operational range while preserving recall for at least one family member. Without the fix, the paper is a negative-result study (publishable in a benchmark-oriented venue, but materially weaker).

## 4.3 Readiness assessment
Publishable only as one unified paper, not three: (a) implement at least one variance-reduction fix end-to-end; (b) provide null calibration for the drift statistics (in-control ARL); (c) differentiate explicitly from [25]–[28]; (d) include detection-delay and FAR trade-off curves per fault.

## 4.4 Recommended framing
Genre: *phenomenon + diagnosis + fix*. Claim skeleton:

> "We study a family of structure-drift monitors — partial-correlation, rank-correlation, and spectral-density charts — for incipient fault detection. On the Tennessee Eastman benchmark, all three detect the canonically hard faults 3, 9, and 15 with recall far above value-based charts, and all three fail identically on false alarms: the sampling variance of windowed matrix estimates, not fault insensitivity, is the binding constraint. Regularized estimation [and/or self-normalization] closes this gap, yielding an operationally viable dependence-drift chart with calibrated in-control run length."

---

# 5. CAR — Conformal Ensemble Monitoring with Distribution-Free Guarantees

## 5.1 Method summary
Five heterogeneous anomaly scores (Mahalanobis, kNN distance, PCA reconstruction error, Isolation Forest, subset Mahalanobis) are each converted to a conformal p-value by rank against a calibration set, combined by Fisher's method, EWMA-smoothed, and thresholded. Reported: F1 0.982, FPR 0.003 — strong but not distinguishable, empirically, from other well-tuned ensembles.

## 5.2 Relation to prior work

**Identical work (component-wise).** Every ingredient exists: conformal p-values and their theory (Vovk, Gammerman & Shafer [29]); conformal anomaly detection, including sequential/inductive variants (Laxhammar & Falkman [30]); the rigorous multiple-testing treatment of conformal p-values for outlier detection (Bates, Candès, Lei, Romano & Sesia [31], Ann. Statist. 2023); Fisher's combination method [32]; score-ensemble outlier detection (feature bagging, Lazarevic & Kumar [40]). Sequential change detection with exchangeability-based guarantees also exists: conformal (inductive) martingales (Volkhonskiy et al. [33]).

**Closely related work.** The combination "several heterogeneous detectors → conformal p-values → p-value combination" appears in the conformal literature with attention to the dependence between p-values (positive dependence and FDR control in [31]); ensemble/aggregated conformal predictors are an active thread.

**What is already done, and by whom.**
- Conformal p-values, guarantees, martingale-based sequential testing: [29], [31], [33].
- Conformal anomaly detection for streaming data: [30].
- Detector ensembles: [40].

**What remains new (the delta).** Only a *guarantee-transfer* contribution survives: an SPC chart on an ensemble of arbitrary detectors whose in-control false-alarm rate (or ARL) is guaranteed distribution-free — no Gaussian assumption — with the guarantee proved, not asserted. Two technical obstacles define the actual work: (i) the current EWMA smoothing destroys the exchangeability on which conformal validity rests — replace it with a conformal-martingale construction [33] or remove it and prove validity of the resulting scheme; (ii) serial dependence of process data violates exchangeability per se and must be addressed (block-based calibration or explicit assumptions). If neither obstacle is resolved theoretically, the paper has no contribution beyond its numbers, and its numbers do not distinguish it.

## 5.3 Readiness assessment
Highest theoretical burden of the five; lowest priority. Pursue only as a theory-forward paper for a statistics-adjacent venue.

## 5.4 Recommended framing
Genre: *transferred guarantee*. Claim skeleton:

> "We construct a multivariate control chart from an ensemble of heterogeneous anomaly detectors whose in-control behavior is guaranteed distribution-free: detector scores are calibrated to conformal p-values (Vovk et al., 2005; Bates et al., 2023), combined by Fisher's method, and monitored via a conformal-martingale scheme (Volkhonskiy et al., 2017) that preserves validity under sequential testing. We characterize the guarantee under serial dependence and validate it on the Tennessee Eastman Process."

---

# 6. Cross-Method Publication Strategy

1. **Order of effort.** (1) CGRM validation and ablation — fastest path, largest payoff; (2) CGCI_MON — deepest novelty, most methodological work; (3) FDP_CUSUM — compact, could be a second contribution inside the CGCI paper or a short standalone; (4) the dependency bundle — one unified paper; (5) CAR — only with the theory.
2. **Non-negotiables for every submission.** Per-fault results with FAR/ARL0 adjacent to every detection number; matched dataset splits ([10], [17]) and control-limit conventions; preemptive citation of the ancestors listed per method; honest naming (no "causal" without causal identification; no reuse of colliding names — KL-CPD [35] and JMIM [36] are established methods with different content, and CWT_KDE / RLS_FF must be renamed to match their actual algorithms even in comparison tables).
3. **Venue guidance.** Result-driven CGRM: Journal of Process Control, Computers & Chemical Engineering, or Chemometrics and Intelligent Laboratory Systems. Methodological CGCI_MON / FDP_CUSUM / bundle: same venues, or Journal of Quality Technology / Quality Engineering for the SPC-theoretic angle. CAR: a statistics-adjacent venue only with the martingale theory complete.

---

# 7. References

[1] Hawkins, D. M. (1991). Multivariate quality control based on regression-adjusted variables. *Technometrics*, 33(1), 61–75.
[2] Hawkins, D. M. (1993). Regression adjustment for variables in multivariate quality control. *Journal of Quality Technology*, 25(3), 170–182.
[3] Mandel, B. J. (1969). The regression control chart. *Journal of Quality Technology*, 1(1), 1–9.
[4] Zhang, G. X. (1984). A new type of control charts and a theory of diagnosis with control charts. *World Quality Congress Transactions*, ASQC, 175–185.
[5] Hauck, D. J., Runger, G. C., & Montgomery, D. C. (1999). Multivariate statistical process monitoring and diagnosis with grouped regression-adjusted variables. *Communications in Statistics — Simulation and Computation*, 28(2), 309–328.
[6] Crosier, R. B. (1988). Multivariate generalizations of cumulative sum quality-control schemes. *Technometrics*, 30(3), 291–303.
[7] Healy, J. D. (1987). A note on multivariate CUSUM procedures. *Technometrics*, 29(4), 409–412.
[8] Page, E. S. (1954). Continuous inspection schemes. *Biometrika*, 41(1/2), 100–115.
[9] Hawkins, D. M., & Olwell, D. H. (1998). *Cumulative Sum Charts and Charting for Quality Improvement*. Springer, New York.
[10] Downs, J. J., & Vogel, E. F. (1993). A plant-wide industrial process control problem. *Computers & Chemical Engineering*, 17(3), 245–255.
[11] Russell, E. L., Chiang, L. H., & Braatz, R. D. (2000). Fault detection in industrial processes using canonical variate analysis and dynamic principal component analysis. *Chemometrics and Intelligent Laboratory Systems*, 51(1), 81–93.
[12] Chiang, L. H., Russell, E. L., & Braatz, R. D. (2001). *Fault Detection and Diagnosis in Industrial Systems*. Springer, London.
[13] Ku, W., Storer, R. H., & Georgakis, C. (1995). Disturbance detection and isolation by dynamic principal component analysis. *Chemometrics and Intelligent Laboratory Systems*, 30(1), 179–196.
[14] Yue, H. H., & Qin, S. J. (2001). Reconstruction-based fault identification using a combined index. *Industrial & Engineering Chemistry Research*, 40(20), 4403–4414.
[15] Pilario, K. E. S., & Cao, Y. (2018). Canonical variate dissimilarity analysis for process incipient fault detection. *IEEE Transactions on Industrial Informatics*, 14(12), 5308–5315.
[16] Pilario, K. E. S., Cao, Y., & Shafiee, M. (2019). Mixed kernel canonical variate dissimilarity analysis for incipient fault monitoring in nonlinear dynamic processes. *Computers & Chemical Engineering*, 123, 143–154.
[17] Rieth, C. A., Amsel, B. D., Tran, R., & Cook, M. B. (2017). *Additional Tennessee Eastman Process simulation data for anomaly detection evaluation*. Harvard Dataverse.
[18] Granger, C. W. J. (1969). Investigating causal relations by econometric models and cross-spectral methods. *Econometrica*, 37(3), 424–438.
[19] Yuan, T., & Qin, S. J. (2014). Root cause diagnosis of plant-wide oscillations using Granger causality. *Journal of Process Control*, 24(2), 450–459.
[20] Lindner, B., Auret, L., Bauer, M., & Groenewald, J. W. D. (2019). Comparative analysis of Granger causality and transfer entropy to present a decision flow for the application of oscillation diagnosis. *Journal of Process Control*, 79, 72–84.
[21] Duan, P., Yang, F., Chen, T., & Shah, S. L. (2013). Direct causality detection via the transfer entropy approach. *IEEE Transactions on Control Systems Technology*, 21(6), 2052–2066.
[22] Hwang, W., Runger, G., & Tuv, E. (2007). Multivariate statistical process control with artificial contrasts. *IIE Transactions*, 39(6), 659–669.
[23] Hu, J., Runger, G., & Tuv, E. (2007). Tuned artificial contrasts to detect signals. *International Journal of Production Research*, 45(23), 5527–5534.
[24] Chiang, L. H., Russell, E. L., & Braatz, R. D. (2000). Fault diagnosis in chemical processes using Fisher discriminant analysis, discriminant partial least squares, and principal component analysis. *Chemometrics and Intelligent Laboratory Systems*, 50(2), 243–252.
[25] Qiu, P., & Hawkins, D. M. (2001). A rank-based multivariate CUSUM procedure. *Technometrics*, 43(2), 120–132.
[26] Qiu, P., & Hawkins, D. M. (2003). A nonparametric multivariate cumulative sum procedure for detecting shifts in all directions. *Journal of the Royal Statistical Society: Series D (The Statistician)*, 52(2), 151–164.
[27] Thornhill, N. F., Huang, B., & Zhang, H. (2003). Detection of multiple oscillations in control loops. *Journal of Process Control*, 13(1), 91–100.
[28] Roy, S., Atchadé, Y., & Michailidis, G. (2017). Change point estimation in high dimensional Markov random-field models. *Journal of the Royal Statistical Society: Series B*, 79(4), 1187–1206.
[29] Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer, New York.
[30] Laxhammar, R., & Falkman, G. (2015). Inductive conformal anomaly detection for sequential detection of anomalous sub-trajectories. *Annals of Mathematics and Artificial Intelligence*, 74(1–2), 67–94.
[31] Bates, S., Candès, E., Lei, L., Romano, Y., & Sesia, M. (2023). Testing for outliers with conformal p-values. *Annals of Statistics*, 51(1), 149–178.
[32] Fisher, R. A. (1932). *Statistical Methods for Research Workers* (4th ed.). Oliver & Boyd, Edinburgh.
[33] Volkhonskiy, D., Burnaev, E., Nouretdinov, I., Gammerman, A., & Vovk, V. (2017). Inductive conformal martingales for change-point detection. *Proceedings of Machine Learning Research (COPA)*, 60, 132–153.
[34] Adams, R. P., & MacKay, D. J. C. (2007). Bayesian online changepoint detection. *arXiv:0710.3742*.
[35] Chang, W.-C., Li, C.-L., Yang, Y., & Póczos, B. (2019). Kernel change-point detection with auxiliary deep generative models. *International Conference on Learning Representations (ICLR)*; arXiv:1901.06077.
[36] Bennasar, M., Hicks, Y., & Setchi, R. (2015). Feature selection using Joint Mutual Information Maximisation. *Expert Systems with Applications*, 42(22), 8520–8532.
[37] Bakshi, B. R. (1998). Multiscale PCA with application to multivariate statistical process monitoring. *AIChE Journal*, 44(7), 1596–1610.
[38] Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of Multivariate Analysis*, 88(2), 365–411.
[39] Friedman, J., Hastie, T., & Tibshirani, R. (2008). Sparse inverse covariance estimation with the graphical lasso. *Biostatistics*, 9(3), 432–441.
[40] Lazarevic, A., & Kumar, V. (2005). Feature bagging for outlier detection. *Proceedings of the 11th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 157–166.

---

*Note on citation hygiene: entries [3], [4], [20], and [33] were verified against secondary sources; confirm page ranges against the original publications before inclusion in a manuscript. All detection-rate comparisons across papers are approximate unless dataset version (Downs & Vogel vs. Rieth et al.), split, and control-limit convention are matched.*
