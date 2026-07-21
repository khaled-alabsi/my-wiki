# Noise Handling in Statistical Process Monitoring (SPM) and Multivariate Statistical Process Control (MSPC): A Literature Review

## TL;DR

- **The state of the art splits into two paradigms.** *Noise isolation/characterization* uses latent-variable projection (PCA, PLS, ICA, factor analysis, probabilistic PCA), multiscale wavelet decomposition, and robust statistics to separate a “noise subspace” from a “signal subspace”; *noise reduction/filtering* uses classical smoothing (moving average, median, Savitzky–Golay), model-based filters (Kalman, particle), transform-domain denoising (wavelet, Fourier, EMD/SSA), and modern deep denoising (denoising/variational autoencoders, diffusion models). Most methods still implicitly *assume* noise is zero-mean white Gaussian; factor analysis and ICA are the main methods that *explicitly model* heteroscedastic and non-Gaussian noise respectively.
- **The dominant, unresolved tension is anomaly preservation vs. smoothing.** Aggressive denoising lowers false alarms but delays or erases small/incipient faults because they occupy the same amplitude/frequency band as noise; the literature quantifies this trade-off inconsistently, usually reporting fault-detection rate (FDR) alone rather than FDR, false-alarm rate (FAR), and detection delay jointly.
- **The Tennessee Eastman Process (TEP) is the field’s dominant benchmark and defines how noise is studied.** Its measured variables carry white Gaussian measurement noise (present whenever “random variation” disturbances are off),  while the random-variation disturbance class IDV(8)–IDV(12) injects stochastic *process* noise — making TEP a natural testbed for separating measurement noise, process noise, and faults.

## Key Findings

1. **“Noise” in MSPC is defined operationally, not physically.** In PCA the data matrix is decomposed X = TP^T + E, and the residual matrix E is treated as “statistical noise” — the variation left unexplained by retained components. The same physical signal can therefore be “noise” in one model and fault-carrying “signal” in another; this model-relativity is the root cause of most methodological difficulty in the field.
1. **Explicit noise modeling is the exception.** Factor Analysis (FA) explicitly models heteroscedastic (per-variable) noise; Probabilistic PCA (PPCA) models isotropic (equal-variance) noise; ICA and its noisy/robust variants model non-Gaussian noise. The overwhelming majority of PCA/PLS/control-chart methods simply *assume* white Gaussian noise and discard it via low-variance components.
1. **Multiscale wavelet methods are the classical bridge between isolation and reduction.** Bakshi’s Multiscale PCA (MSPCA, AIChE Journal 1998) simultaneously denoises and monitors by combining PCA’s cross-correlation decorrelation with wavelets’ separation of deterministic features from stochastic noise and approximate decorrelation of autocorrelated measurements.
1. **Autocorrelation and closed-loop control break standard assumptions.** Shewhart/EWMA/CUSUM and static PCA assume independent samples; autocorrelation severely distorts average run length (ARL) and inflates false alarms. Dynamic PCA (DPCA) and especially DPCA with Decorrelated Residuals (DPCA-DR, Rato & Reis 2013) were developed specifically to produce white residuals valid for monitoring.
1. **Deep denoising (2021–2026) is displacing linear MSPC for nonlinear, non-Gaussian, noisy data**, but at the cost of interpretability, data hunger, online latency, and the risk of learning to reconstruct faults (over-smoothing anomalies).
1. **Evaluation practice is a recurring weakness.** FDR-only reporting is common and misleading; the field increasingly recognizes that FDR/FAR trade-offs and detection delay must be reported together, and that the lack of a standardized TEP data split impedes fair comparison.

## Details

### 1. Taxonomy of Noise in MSPC

**Definitional status.** MSPC inherits its noise concept from latent-variable modeling: PCA decomposes X = TP^T + E where E (residuals) is treated as statistical noise — an operational, model-relative definition, not a physical one.

**Types of noise:**

- **Measurement/sensor noise** — additive, typically zero-mean white Gaussian (transducers, ADC quantization). In TEP this is explicitly white Gaussian noise on measured variables.
- **Process/stochastic noise** — random fluctuations in the process itself (e.g., feed composition, cooling-water temperature), often colored/autocorrelated and shaped by process dynamics; modeled in TEP via the “random variation” disturbances.
- **Environmental/common-cause noise** — ambient temperature, vibration, drift.
- **Colored/autocorrelated noise** — violates independence assumptions of Shewhart/PCA charts; inflates false alarms.
- **Heteroscedastic noise** — variance differs across sensors (motivates FA over PPCA).
- **Non-Gaussian/heavy-tailed noise** — outliers, spikes, multimodal noise (motivates ICA and robust methods).
- **Cross-correlated noise** — noise correlated across sensors.

**Noise vs. common-cause variation vs. anomaly.** SPC distinguishes common-cause variation (in-control, includes noise) from special-cause/assignable variation (out-of-control faults). Incipient faults are small and slow, occupying the same amplitude/frequency band as noise, so denoising can erase them. Wavelet multiscale methods exploit the fact that deterministic fault features concentrate at coarse scales while noise spreads across fine scales.

### 2. Phase 1 — Noise Isolation / Characterization Methods

**2.1 PCA and the residual (SPE/Q) subspace.** Project correlated variables onto a low-dimensional principal subspace (scores → Hotelling’s T²) and a residual subspace (SPE/Q). X = TP^T + E; T² is a Mahalanobis distance in score space, SPE = ||x − x̂||² is reconstruction-error (noise) energy. *Assumptions:* linearity, Gaussian scores, stationarity, independent samples; discarded components “generally represent random noise.” *Complexity:* ~O(m²n) offline eigendecomposition, O(mA) online per sample. *Strengths:* simple, decorrelates variables, handles high dimensionality and low SNR. *Weaknesses:* crude noise definition, not robust to outliers, poor under autocorrelation/non-Gaussianity. *Applications:* chemical, semiconductor, autobody assembly, wastewater.

**2.2 Factor Analysis (FA) and Probabilistic PCA (PPCA).** Generative model x = Bz + ε, z ~ N(0,I); ε ~ N(0,σ²I) for PPCA (isotropic noise) or ε ~ N(0,Ψ), Ψ diagonal, for FA (heteroscedastic noise). Induces Gaussian covariance BB^T + Ψ estimated by EM. This is the clearest family that *explicitly models* noise. FA is preferred when sensor noise levels differ. *Weaknesses:* linear, Gaussian, offline EM cost; standard SPE/T² discard residual/factor variance (uncertainty information lost). *Applications:* wastewater, multimode processes (mixture PPCA), soft sensing.

**2.3 Independent Component Analysis (ICA).** Decompose X = AS into statistically independent non-Gaussian components; monitor I², I_e², SPE using higher-order statistics PCA ignores. *Weaknesses:* IC ordering ambiguous; FastICA sensitive to outliers (motivating RobustICA); control limits require kernel density estimation since ICs aren’t Gaussian; noisy-ICA variants needed when measurement noise is significant. *Applications:* non-Gaussian chemical processes, CSTR, TEP.

**2.4 Multiscale PCA (MSPCA) — wavelet + PCA (Bakshi, AIChE Journal 44(7):1596–1610, 1998).** Per the abstract, “MSPCA combines the ability of PCA to decorrelate the variables by extracting a linear relationship with that of wavelet analysis to extract deterministic features and approximately decorrelate autocorrelated measurements.” It computes PCA of wavelet coefficients at each scale and recombines only scales with significant events — equivalent to adaptively filtering scores/residuals and adjusting detection limits. *Strengths:* handles autocorrelated and multiscale data, simultaneous denoising + monitoring, near-normal coefficients per scale. *Weaknesses:* manual basis/threshold selection; online boundary distortion and latency. *Applications:* batch/continuous chemical processes, sequencing batch reactors.

**2.5 Robust statistics / Robust PCA.** Separate gross outliers/sparse corruption from low-rank signal: ROBPCA (Hubert et al., *Technometrics* 2005) uses robust scatter + projection pursuit; Principal Component Pursuit / Stable PCP decomposes X = L (low-rank) + S (sparse) + noise via convex optimization; robust covariance (MCD) resists contamination. *Weaknesses:* expensive convex solvers; PCP’s “sparse” matrix often not truly sparse (motivating moment-based RPCA). *Applications:* monitoring with contaminated training data, structural health monitoring.

**2.6 Validating that isolated components are “truly noise.”** Whiteness/autocorrelation tests on residuals (a Kalman innovation should be white under no-fault), normality/goodness-of-fit tests on wavelet coefficients, cross-validation for component selection (NIPALS), variance-explained thresholds, and physical interpretation via contribution plots. DPCA-DR explicitly targets decorrelated (white) residuals so the monitoring statistic is valid. 

### 3. Phase 2 — Noise Reduction / Filtering Methods

**3.1 Classical smoothing filters.**

- *Moving Average (MA):* low-pass averaging of adjacent samples; simple, online, but blurs steps and lags; underlies EWMA/CUSUM.
- *Median filter:* nonlinear, robust to impulsive spikes, preserves edges; poor for Gaussian noise.
- *Savitzky–Golay (SG):* local least-squares polynomial fit in a sliding window; preserves peak shape and higher moments better than MA and yields derivatives; ubiquitous in chemometrics/spectroscopy. *Weaknesses:* sensitive to window/order, poor high-frequency suppression, boundary artifacts.
- *EWMA/CUSUM as filters:* EWMA is an exponential low-pass filter with memory, excellent for small shifts and can be made robust to non-normality; CUSUM accumulates deviations. Both degrade badly under autocorrelation (ARL heavily affected).

**3.2 Model-based filters.**

- *Kalman filter (KF):* optimal linear estimator for Gaussian noise; the innovation/residual is zero-mean white under no-fault and non-white/biased under fault, giving a residual-based fault detector with GLR/chi-square tests. Online, recursive. *Weaknesses:* needs a state-space model, Gaussian assumption, degrades under model mismatch; EKF/UKF for nonlinearity.
- *Particle filter:* sequential Monte Carlo for nonlinear/non-Gaussian, heavy-tailed state estimation. *Weaknesses:* high cost, particle degeneracy.

**3.3 Transform-domain denoising.**

- *Wavelet denoising:* threshold wavelet coefficients (hard/soft, VisuShrink/Minimax), retaining coarse deterministic features and removing fine-scale noise; multivariate extension combines wavelets + PCA (Aminghafari et al., *Computational Statistics & Data Analysis* 2006); online moving-window variants address border distortion and pseudo-Gibbs effects.
- *Fourier filtering:* low-pass in frequency; good for stationary periodic signals, poor for transients.
- *EMD/EEMD/SSA:* data-adaptive decomposition into intrinsic mode functions (EMD) or trajectory-matrix eigen-components (SSA); reconstruct excluding noise-dominated modes. Good for nonlinear/nonstationary signals; EEMD adds white noise to mitigate mode mixing.  Applied to chemical process monitoring (SSA+EMD+PCA). *Weaknesses:* mode mixing, cost, mode-selection heuristics.

**3.4 Dimensionality reduction as inherent denoising.** PCA/PLS/regularized PCA/kernel PCA inherently denoise by discarding low-variance directions. DPCA (Ku et al. 1995) augments lagged variables to model autocorrelation;  DPCA-DR (Rato & Reis 2013) generates decorrelated residuals for valid monitoring;  recursive/moving-window PCA adapt to nonstationarity.

**3.5 Deep-learning denoising.**

- *Denoising autoencoders (DAE):* reconstruct clean input from artificially corrupted (Gaussian/dropout) input, learning a robust nonlinear normal-operation manifold; reconstruction error is the monitoring statistic. DAE + elastic net (Yan et al., *IEEE TNNLS* 2019) adds sparse variable selection; stacked/sparse DAEs deepen features. *Weakness:* artificial injected noise may not match the real noise distribution.
- *Adaptive/diffusion denoising (ADAE):* Li & Zhao (*Chemical Engineering Science* 298:120368, 2024) replace hand-injected noise with diffusion-model-generated noise. Per the paper, ADAE “designs a diffusion model to generate noise with varying degrees of similarity to the original data. The noise is then separately introduced into chained DAEs. So ADAE can effectively eliminate noise closely resembling the distribution of real data,” using a chain-like structure with a noise-prediction network replacing manually injected noise; it is validated on TEP against PCA/SPCA/LRMD and a standard DAE. (Exact per-fault FDR figures are in the paper’s TEP case study; the reported qualitative claim is superior noise suppression and detection versus a standard DAE.)
- *Variational autoencoders (VAE):* probabilistic latent model monitored in probability space; LSTM/GRU-VAE capture temporal dependence. OSAVA (Bi & Zhao, *Process Safety and Environmental Protection* 156:581–597, 2021) adds orthogonal self-attention and reports an **average FDR of 94.7% and an average detection delay of 24.2 minutes on TEP**.
- *Causal/graph-based denoising:* causality-weighted stacked DAE (CSDAE) incorporates causal relations between variables and reconstruction errors with dynamic thresholds for closed-loop monitoring.
- *Suitability:* powerful for nonlinear/non-Gaussian data, but data-hungry, opaque, hard to certify, at risk of reconstructing faults, and costly online.

### 4. Comparison Tables

**Table 1 — Method characteristics**

|Method              |Isolation/Reduction|Stat/ML/Hybrid|Sup/Unsup |Online|Real-time|Distribution assumptions     |Multivariate |Correlated vars|Robust to outliers|Preserves anomalies      |Complexity |Typical applications   |
|--------------------|-------------------|--------------|----------|------|---------|-----------------------------|-------------|---------------|------------------|-------------------------|-----------|-----------------------|
|PCA (T²/SPE)        |Isolation          |Stat          |Unsup     |Yes   |Yes      |Gaussian                     |Yes          |Yes            |No                |Medium                   |Low online |Chemical, semiconductor|
|PPCA/FA             |Isolation          |Stat          |Unsup     |Yes   |Yes      |Gaussian (FA: heterosced.)   |Yes          |Yes            |No                |Medium                   |Medium (EM)|WWTP, soft sensing     |
|ICA / RobustICA     |Isolation          |Stat/ML       |Unsup     |Yes   |Yes      |Non-Gaussian                 |Yes          |Yes            |No / Yes          |Medium                   |Medium     |Non-Gaussian chemical  |
|MSPCA (wavelet+PCA) |Both               |Hybrid        |Unsup     |Semi  |Semi     |Approx. Gaussian per scale   |Yes          |Yes (autocorr) |Partial           |High                     |Medium     |Batch/continuous       |
|Robust PCA/PCP      |Isolation          |Stat          |Unsup     |Semi  |No       |Low-rank + sparse            |Yes          |Yes            |Yes               |Medium                   |High       |Contaminated training  |
|Moving Average      |Reduction          |Stat          |Unsup     |Yes   |Yes      |None                         |Per-var      |No             |No                |Low (lags shifts)        |Low        |Univariate SPC         |
|Median filter       |Reduction          |Stat          |Unsup     |Yes   |Yes      |None                         |Per-var      |No             |Yes               |High (edges)             |Low        |Spike removal          |
|Savitzky–Golay      |Reduction          |Stat          |Unsup     |Yes   |Yes      |Local polynomial             |Per-var      |No             |No                |Medium-High              |Low        |Spectroscopy           |
|EWMA/CUSUM          |Reduction          |Stat          |Unsup     |Yes   |Yes      |Gaussian (autocorr-sensitive)|MEWMA: yes   |Weak           |No                |Medium (small shifts)    |Low        |Control charts         |
|Kalman filter       |Reduction          |Model         |Unsup     |Yes   |Yes      |Gaussian, linear model       |Yes          |Yes            |No                |High (residual)          |Low-Med    |State-estimation FDI   |
|Particle filter     |Reduction          |Model         |Unsup     |Yes   |Semi     |Non-Gaussian/nonlinear       |Yes          |Yes            |Yes               |High                     |High       |Nonlinear FDI          |
|Wavelet denoising   |Reduction          |Stat          |Unsup     |Semi  |Semi     |Sparse in wavelet domain     |Multivar ext.|Yes            |Partial           |Medium-High              |Medium     |Multiscale monitoring  |
|EMD/SSA             |Reduction          |Stat          |Unsup     |Semi  |No       |Nonstationary/nonlinear      |Semi         |Yes            |Partial           |Medium                   |High       |Nonstationary signals  |
|DAE                 |Reduction          |ML            |Unsup/Semi|Yes   |Semi     |Learned/none                 |Yes          |Yes            |Partial           |Medium (over-smooth risk)|High train |Nonlinear processes    |
|VAE (LSTM/GRU/OSAVA)|Both               |ML            |Unsup/Semi|Yes   |Semi     |Learned probabilistic        |Yes          |Yes            |Partial           |Medium                   |High       |Dynamic nonlinear      |
|Diffusion/ADAE      |Reduction          |ML            |Unsup/Semi|Semi  |No       |Learned                      |Yes          |Yes            |Yes               |Medium                   |Very high  |Robust FDD (recent)    |

**Table 2 — Noise-type coverage**

|Noise type                |Best-suited methods                                   |Poorly handled by       |
|--------------------------|------------------------------------------------------|------------------------|
|White Gaussian measurement|PCA, PPCA, MA, SG, KF                                 |—                       |
|Heteroscedastic           |FA, weighted methods                                  |PPCA, plain PCA         |
|Colored/autocorrelated    |DPCA, DPCA-DR, MSPCA, wavelet, time-series charts     |Shewhart, plain PCA/EWMA|
|Non-Gaussian/heavy-tailed |ICA/RobustICA, robust PCA, particle filter, KDE limits|PCA, PPCA, T²           |
|Impulsive/spikes          |Median filter, robust PCA                             |MA, SG, PCA             |
|Nonstationary             |EMD/SSA, recursive/MW-PCA, LSTM-VAE                   |static PCA              |

### 5. Timeline of Major Developments

- **1930s–1950s:** Shewhart charts; Page CUSUM (1954); Roberts EWMA (1959).
- **1960s:** Kalman filter (1960); Savitzky–Golay (1964).
- **Late 1980s–1990s:** MSPC via PCA/PLS (MacGregor, Kourti, Wise); Multiway PCA/PLS for batch (Nomikos & MacGregor); DPCA (Ku et al. 1995); Downs & Vogel TEP (1993).
- **1998:** Bakshi Multiscale PCA (AIChE Journal) — landmark wavelet + PCA.
- **2000s:** ICA-based non-Gaussian monitoring; PPCA (Kim & Lee 2003); kernel PCA; ROBPCA (2005); multivariate wavelet denoising (Aminghafari et al. 2006); Chiang/Russell/Braatz texts.
- **2010s:** Qin survey (2012); DPCA-DR (Rato & Reis 2013); Stable PCP for MSPC; deep learning enters (DAE, VAE); TEP revision and extended simulator (Bathelt et al. 2015; revised TEP as SPC/DoE testbed).
- **2021–2026:** Denoising sparse autoencoders; attention/transformer FDD; diffusion-based ADAE (Li & Zhao 2024); VAE comparative studies; causal/graph-based residual monitoring; open-source tooling (BibMon).

### 6. Research Trends (2021–2026)

- **Deep denoising dominance:** DAE/VAE/diffusion increasingly replace linear MSPC for nonlinear, non-Gaussian, noisy data; ADAE (Li & Zhao 2024) uses diffusion-generated noise matching the real data distribution.
- **Attention & VAE:** OSAVA (Bi & Zhao 2021) reports FDR 94.7% / detection delay 24.2 min on TEP; LSTM/GRU-VAE recommended for dynamic monitoring.
- **Causal/graph methods:** causal structure embedded into residual monitoring and denoising (CSDAE).
- **Open-source tooling:** BibMon (Petrobras, 2024) — SPE control charts, benchmarking, Optuna hyperparameter tuning, and a TEP loader; pyPhi (García-Muñoz) — PCA/PLS variants and batch multi-way models; scikit-learn robust covariance (MinCovDet); the `mspca` GitHub package implements Bakshi-style MSPCA.
- **Benchmarks:** TEP dominant — it defines **41 measured variables (XMEAS) and 12 manipulated variables (XMV)** with **20 preset disturbances (IDV)** at 3/6/15-min sampling; the extended TEP (Bathelt/Reinartz 2015 onward) adds scalable disturbances and repeat simulations, and the revised TEP serves as an SPC/DoE testbed. Others: CSTR, wastewater, semiconductor.
- **Evaluation metrics:** FDR, FAR, detection delay, ARL, SNR, RMSE — with growing recognition that FDR alone is misleading and FDR/FAR/delay must be reported jointly.

### 7. Gap Analysis

1. **Non-Gaussian, heteroscedastic, colored noise remains hard.** Most methods assume Gaussian white noise; FA and ICA each address one dimension, but *combined* heteroscedastic + colored + non-Gaussian noise is underserved.
1. **Noise vs. incipient-fault separation.** Small/slow faults share the noise band; denoising risks erasing them. Anomaly-preserving denoising is underdeveloped and rarely quantified (e.g., minimum detectable fault magnitude vs. denoising strength).
1. **Online/real-time denoising.** Wavelet/EMD/diffusion methods carry latency and boundary problems; certifiable real-time deep denoising is open.
1. **Uncertainty propagation.** PPCA/FA discard residual/factor variance in SPE/T²; principled uncertainty-aware statistics are underused.
1. **Closed-loop control effects.** Control loops mask faults and color noise (TEP demonstrates this via IDV(8)–IDV(12)); statistics assuming independence fail.
1. **Evaluation inconsistency.** No standardized reference dataset/protocol; FDR-only reporting; the extended TEP’s lack of a standard split impedes fair comparison.
1. **Underexplored combinations:** robust + probabilistic + multiscale hybrids; diffusion denoising + causal graphs; physics-informed denoising; noise-model-aware deep monitoring.
1. **Poorly supported industrial scenarios:** multimode/transition operation, non-stationary drift, high missing-data rates, heavy sensor contamination, small-sample regimes.

## Recommendations

**Staged, concrete next steps for the PhD program:**

1. **Immediately (foundation-building):** Establish a reproducible TEP experimental harness that reports **FDR, FAR, and detection delay jointly** for every method, on a fixed extended-TEP split, with published code (build on BibMon’s TEP loader and SPE charting). *Benchmark to change the plan:* if baseline PCA/DPCA already achieve near-ceiling FDR at acceptable FAR on your fault set, pivot toward the harder incipient/random-variation faults (IDV(8)–IDV(12)) and the classically “unobservable” faults (IDV(3), IDV(9), IDV(15)).
1. **Near-term (characterize the noise before denoising it):** Empirically characterize TEP’s noise — verify Gaussianity/whiteness of measurement noise with random-variation disturbances off, then quantify how IDV(8)–IDV(12) inject colored process noise. Use this to build a *noise taxonomy per variable* that later methods can condition on. *Threshold:* if residuals fail whiteness/normality tests, prioritize DPCA-DR-style decorrelation and FA (heteroscedastic) over plain PCA/PPCA.
1. **Core contribution (address the central gap):** Develop an **anomaly-preserving, noise-model-aware denoiser** — e.g., condition a denoising/diffusion autoencoder on estimated per-variable, colored noise statistics rather than generic Gaussian corruption — and explicitly measure incipient-fault attenuation (minimum detectable fault magnitude as a function of denoising strength). This directly targets Gaps 1–2 and differentiates from the many “add generic Gaussian noise” DAE papers.
1. **Hybridization (breadth):** Test underexplored combinations — robust FA on wavelet coefficients (robust + probabilistic + multiscale), and diffusion denoising fused with causal/graph residual monitoring — to handle contaminated, autocorrelated, heteroscedastic data simultaneously. *Benchmark:* adopt a hybrid only if it beats the best single-paradigm method on the joint FDR/FAR/delay criterion under realistic contamination.
1. **Deployment realism:** Report **computational cost and online latency** alongside accuracy, and evaluate explicitly under closed-loop control and across TEP operating modes/transitions. *Threshold:* methods that cannot meet the 3-min TEP sampling cadence online should be flagged as offline-only.
1. **Uncertainty-aware statistics:** Where PPCA/FA are used, derive monitoring statistics that retain residual/factor variances (Bayesian PPCA/FA) rather than discarding them.

## Caveats

- **“Noise” is defined inconsistently across the literature** — usually operationally (residual variation) rather than physically — so cross-paper comparisons of “denoising performance” must be read carefully.
- **Some quantitative figures could not be verified verbatim from primary full text.** The ADAE (Li & Zhao 2024) per-fault FDR numbers are in the paywalled TEP case study and were not extracted here; only the method description and qualitative superiority claim are confirmed. The OSAVA figures (FDR 94.7%, delay 24.2 min) are as reported by the authors and a secondary survey summary, not independently reproduced.
- **Vendor/industry web sources** (e.g., MSPC software marketing pages) were used only for background framing, not for technical claims; all method-level claims rest on peer-reviewed venues (AIChE Journal, IEEE Transactions, Journal of Process Control, Chemometrics and Intelligent Laboratory Systems, Ind. Eng. Chem. Res., Technometrics, Chemical Engineering Science, Process Safety and Environmental Protection) and reputable preprints.
- **Deep-learning results on TEP can be optimistic:** many report FDR without matched FAR/detection-delay, use non-standard splits, or evaluate on easy faults; treat single-number superiority claims skeptically.
- **The TEP measurement-noise model is idealized** (white Gaussian); real plants exhibit colored, heteroscedastic, non-stationary, and contaminated noise that TEP only partially represents (mainly through the random-variation disturbances), so TEP performance is an upper bound on real-world robustness.

### Selected References (seminal and recent)

- Downs, J.J. & Vogel, E.F. (1993). A plant-wide industrial process control problem. *Computers & Chemical Engineering* 17(3):245–255.
- Bakshi, B.R. (1998). Multiscale PCA with application to multivariate statistical process monitoring. *AIChE Journal* 44(7):1596–1610.
- Ku, W., Storer, R.H., Georgakis, C. (1995). Disturbance detection and isolation by dynamic PCA. *Chemometrics and Intelligent Laboratory Systems* 30:179–196.
- Chiang, L.H., Russell, E.L., Braatz, R.D. (2001). *Fault Detection and Diagnosis in Industrial Systems.* Springer.
- Russell, E.L., Chiang, L.H., Braatz, R.D. (2000). *Data-driven Methods for Fault Detection and Diagnosis in Chemical Processes.* Springer.
- Chiang, L.H., Russell, E.L., Braatz, R.D. (2000). Fault diagnosis using FDA, DPLS, and PCA. *Chemometrics and Intelligent Laboratory Systems* 50:243–252.
- Qin, S.J. (2012). Survey on data-driven industrial process monitoring and diagnosis. *Annual Reviews in Control* 36(2):220–234.
- Kim, D. & Lee, I.-B. (2003). Process monitoring based on probabilistic PCA. *Chemometrics and Intelligent Laboratory Systems* 67:109–123.
- Rato, T.J. & Reis, M.S. (2013). Fault detection in the TEP using DPCA based on decorrelated residuals (DPCA-DR). *Chemometrics and Intelligent Laboratory Systems* 125:101–108.
- Rato, T.J. & Reis, M.S. (2013). Advantage of using decorrelated residuals in DPCA. *Ind. Eng. Chem. Res.* 52(38):13685–13698.
- Rato, T.J., Reis, M.S. et al. (2016). A systematic comparison of PCA-based SPM methods. *AIChE Journal*.
- Aminghafari, M., Cheze, N., Poggi, J.-M. (2006). Multivariate denoising using wavelets and PCA. *Computational Statistics & Data Analysis*.
- Ganesan, R., Das, T.K., Venkataraman, V. (2004). Wavelet-based multiscale statistical process monitoring: a review. *IIE Transactions* 36(9).
- Cohen, A. & Atoui, M.A. (2022). On wavelet-based statistical process monitoring. *Transactions of the Institute of Measurement and Control* 44(3):525–.
- Hubert, M., Rousseeuw, P.J., Vanden Branden, K. (2005). ROBPCA: a new approach to robust PCA. *Technometrics*.
- Yan, W. et al. (2019). Robust monitoring and fault isolation using denoising autoencoder and elastic net. *IEEE Transactions on Neural Networks and Learning Systems.*
- Li, Z. & Zhao, H. (2024). Adaptive denoising autoencoder based on the diffusion model for robust fault detection. *Chemical Engineering Science* 298:120368.
- Bi, X. & Zhao, J. (2021). Orthogonal self-attentive VAE (OSAVA) for interpretable chemical process fault detection and identification. *Process Safety and Environmental Protection* 156:581–597.
- Spina, D.E. et al. (2024). Comparison of autoencoder architectures for fault detection in industrial processes. *Digital Chemical Engineering*.
- Melo, A. et al. (2024). BibMon: an open-source Python package for process monitoring, soft sensing, and fault diagnosis. *Digital Chemical Engineering*.
- Capaci, F., Vanhatalo, E., Palazoglu, A., Bergquist, B., Kulahci, M. (2018). The revised Tennessee Eastman process simulator as testbed for SPC and DoE methods. *Quality Engineering* 30(2).
- Bathelt, A., Ricker, N.L., Jelali, M. (2015). Revision of the Tennessee Eastman process model. *IFAC-PapersOnLine* 48(8):309–314.
- Sheriff, M.Z., Mansouri, M., Karim, M.N., Nounou, H., Nounou, M. (2017). Fault detection using multiscale PCA-based moving window GLRT. *Journal of Process Control* 54:47–64.