# LoRA and QLoRA: A Self-Contained PhD-Level Tutorial on Parameter-Efficient Fine-Tuning of Large Language Models

*A graduate-textbook chapter. Last revised May 2026.*

-----

## Table of Contents

1. Background and Motivation
2. Linear Algebra Primer
3. LoRA: The Core Idea
4. A Worked Numerical Example for LoRA
5. Why LoRA Works: Theory and Evidence
6. Quantization Primer
7. QLoRA: The Full Technique
8. Worked Example for Quantization and QLoRA
9. PyTorch Code Implementation
10. Practical Considerations
11. Recent Alternatives and Extensions (2024–2025)
12. Connecting to Broader Themes

-----

## 1. Background and Motivation

### 1.1 Pretraining versus Fine-Tuning

Modern large language models (LLMs) are produced in two stages. In **pretraining**, a model with billions of parameters is trained from scratch on a massive corpus (trillions of tokens of web text, code, books) using a self-supervised objective — most commonly next-token prediction. Pretraining produces a *generalist* model that has absorbed an enormous amount of linguistic and world knowledge, but it is rarely the right tool for any specific task: it does not yet know that it should answer questions politely, follow JSON schemas, write Python in your house style, or diagnose dermatological photographs.

In **fine-tuning**, the pretrained weights are updated on a much smaller, task-specific dataset (typically thousands to millions of examples) so that the model specializes. This is an instance of the broader paradigm of **transfer learning**: features learned on a large, generic problem are reused as initialization for many smaller problems. The fundamental empirical regularity that makes transfer learning work in deep learning is that **most of what a neural network needs to know about language (or images, or proteins) is universal across tasks**; the task-specific increment is small.

That last sentence is the philosophical seed of LoRA. If the *delta* between the pretrained model and the fine-tuned model is small, perhaps we can represent and learn that delta in a much more compact way than re-learning all of the parameters.

### 1.2 The Cost Structure of Full Fine-Tuning

Let me be quantitative. Consider a 7-billion-parameter transformer (e.g., Llama-2-7B) and a standard fine-tuning recipe using the AdamW optimizer with mixed-precision (BF16) training. During training the GPU must hold four classes of tensors simultaneously:

1. **Model parameters** $W$. At 2 bytes each (BF16 or FP16), this is $7 \times 10^9 \times 2 = 14$ GB.
2. **Gradients** $\nabla_W \mathcal{L}$. Same shape as the parameters; another **14 GB** in BF16.
3. **Optimizer states**. AdamW maintains two FP32 moments per parameter  (the exponential moving averages $m$ and $v$). Mixed-precision training also keeps an FP32 *master copy* of the weights.  The Chronicals fine-tuning-framework paper (Nair, arXiv:2601.02609) quantifies this exactly: *“Fine-tuning a 7-billion parameter language model requires 84GB of memory: 14GB for weights, 14GB for gradients, and 56GB for optimizer states in FP32.”*  If $m, v$ are kept in BF16 (8-bit Adam variants do even better), the optimizer cost drops to $\approx 28$ GB, but full FP32 Adam is the academic default.
4. **Activations** saved for the backward pass. These scale with batch size, sequence length, and depth. For Llama-7B with sequence length 2048 and modest batch size, activations are commonly 5–15 GB even with gradient checkpointing.

This 84 GB total — *before* activations — is why fine-tuning a 7B model in BF16 with AdamW typically requires a single A100-80GB or H100, and a 65B model requires multiple high-end GPUs with model parallelism. The QLoRA paper (Dettmers et al., 2023) confirms this: *“regular 16-bit finetuning of a LLaMA 65B parameter model requires more than 780 GB of GPU memory.”*

### 1.3 The Storage and Deployment Disaster

Even if you can afford to fine-tune, full fine-tuning produces a problem at deployment. Each fine-tuned model is a fresh copy of all 7B parameters — about **14 GB per task** in BF16. If your company has 200 customers and each wants a slightly personalized variant, that is 2.8 TB of model weights. If you want to A/B test 5 variants per customer, multiply by 5. Loading any of these into GPU memory is slow; cold-starting requires reading tens of gigabytes from disk; multi-tenant serving is impossible because no GPU can hold even a few full copies. The LoRA paper (Hu et al., 2021) names this directly: *“Using GPT-3 175B as an example — deploying independent instances of fine-tuned models, each with 175B parameters, is prohibitively expensive,”* with each checkpoint requiring ~350 GB of storage.

### 1.4 The PEFT Family

**Parameter-Efficient Fine-Tuning (PEFT)** is the response: a family of methods that fine-tune only a small set of new or selected parameters, freezing the rest. The major branches are:

- **Adapters** (Houlsby et al., 2019): insert small bottleneck MLP modules between transformer sub-layers; train only those. Add inference latency.
- **Prefix Tuning** (Li & Liang, 2021) and **Prompt Tuning** (Lester et al., 2021): prepend learned continuous “soft prompt” vectors to the input or to each layer’s keys/values. No weight modifications, but consume sequence length and underperform on harder tasks.
- **BitFit** (Ben Zaken et al., 2021): train only the bias terms. Extremely cheap; works poorly on harder tasks.
- **IA³** (Liu et al., 2022): learn three small vectors per transformer block that elementwise rescale keys, values, and FFN activations.
- **LoRA** (Hu et al., 2021): inject low-rank update matrices into linear layers; train only those.
- **QLoRA** (Dettmers et al., 2023): LoRA on top of a 4-bit-quantized frozen base.

LoRA and QLoRA have, by 2024–2025, become the dominant choices for two reasons. First, they *match* full fine-tuning quality on a wide range of tasks while training under 1% of parameters. Second, unlike adapters, the learned update can be **mathematically merged into the base weights at inference time**, leaving zero latency overhead. The rest of this chapter is the careful unpacking of how and why.

-----

## 2. Linear Algebra Primer

LoRA’s central object is a *low-rank matrix*. Three concepts make that meaningful: rank, the singular value decomposition, and the Eckart–Young theorem.

### 2.1 Matrix Rank

For a matrix $A \in \mathbb{R}^{m \times n}$, the **rank** $r = \mathrm{rank}(A)$ is the dimension of the column space of $A$ (equivalently, the dimension of the row space; these are always equal). Geometrically:

- A linear map $x \mapsto Ax$ sends $\mathbb{R}^n$ into $\mathbb{R}^m$, but the image is a linear subspace of dimension $r$.
- $r$ is the number of independent directions $A$ “produces” — independent column or row vectors.
- $r \le \min(m, n)$. The matrix is **full rank** if $r = \min(m,n)$, and **rank-deficient** otherwise.

A useful mental picture: if $r$ is small, $A$ is a *flat pancake* embedded in a high-dimensional space. Almost all directions in $\mathbb{R}^m$ are unreachable by $Ax$; the map collapses everything onto a thin $r$-dimensional plane through the origin.

**Outer-product factorization.** Any rank-$r$ matrix can be written as a sum of $r$ outer products:
$$A = \sum_{i=1}^{r} u_i v_i^\top = U V^\top$$
where $U \in \mathbb{R}^{m \times r}$ has the $u_i$ as columns and $V \in \mathbb{R}^{n \times r}$ has the $v_i$ as columns. The total parameter count drops from $mn$ to $r(m+n)$, which is much smaller when $r \ll \min(m,n)$. **This is exactly LoRA’s parameterization**, up to notation.

### 2.2 Singular Value Decomposition

The SVD theorem states that every $A \in \mathbb{R}^{m\times n}$ admits a decomposition
$$A = U \Sigma V^\top$$
where $U \in \mathbb{R}^{m \times m}$ and $V \in \mathbb{R}^{n \times n}$ are orthogonal (their columns are orthonormal) and $\Sigma \in \mathbb{R}^{m\times n}$ is diagonal with non-negative entries $\sigma_1 \ge \sigma_2 \ge \ldots \ge \sigma_{\min(m,n)} \ge 0$ called the **singular values**.

Geometric interpretation: any linear map factors into (i) a rotation/reflection $V^\top$ in the input space, (ii) an axis-aligned stretching $\Sigma$, and (iii) a rotation/reflection $U$ in the output space. The singular values quantify how much each independent direction is stretched. Directions corresponding to $\sigma_i = 0$ are *annihilated*. The rank of $A$ equals the number of non-zero singular values.

### 2.3 Eckart–Young Theorem (Best Low-Rank Approximation)

The **Eckart–Young–Mirsky theorem** states that the optimal rank-$k$ approximation of $A$ in either the Frobenius or the spectral norm is obtained by truncating the SVD:
$$A_k = \sum_{i=1}^{k} \sigma_i u_i v_i^\top, \quad |A - A_k|*F = \sqrt{\sum*{i=k+1}^{\min(m,n)} \sigma_i^2}.$$
That is, the best you can do with rank $k$ is to keep the $k$ largest singular triplets. If the spectrum decays quickly — most “energy” is in the top few singular values — then a low-rank approximation is extremely good. Many real-world matrices (covariance matrices, transformer weight updates, image-pixel matrices, recommender system matrices) have rapidly-decaying spectra. This is the empirical fact that LoRA exploits.

### 2.4 Intrinsic Dimension

The **intrinsic dimension** of an optimization problem (Li et al., 2018; Aghajanyan, Zettlemoyer, Gupta, 2020, arXiv:2012.13255) is the smallest dimension $d$ such that optimizing in a random $d$-dimensional subspace of the full parameter space reaches a satisfactory solution.  Aghajanyan et al. famously showed that **for RoBERTa-base, optimizing only 200 randomly-projected parameters reaches 90% of the full fine-tuning accuracy on the MRPC task**. The verbatim claim from their abstract: *“by optimizing only 200 trainable parameters randomly projected back into the full space, we can tune a RoBERTa model to achieve 90% of the full parameter performance levels on MRPC.”*  They also showed *larger* pretrained models tend to have *lower* intrinsic dimension  — a counterintuitive finding that suggests scale makes adaptation easier, not harder. This empirical phenomenon is the direct intellectual ancestor of LoRA.

-----

## 3. LoRA: The Core Idea

### 3.1 Statement of the Method

LoRA (Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang & Chen, 2021, arXiv:2106.09685, ICLR 2022) takes seriously the hypothesis: **“the change in weights during model adaptation also has a low ‘intrinsic rank’”**  (verbatim from §1 of the paper). Let $W_0 \in \mathbb{R}^{d \times k}$ be a frozen pretrained weight matrix (for example, the query projection in some attention head). Full fine-tuning would learn an additive update $\Delta W$ of the same shape, giving $W = W_0 + \Delta W$.

LoRA constrains $\Delta W$ to be at most rank $r$ by writing
$$\Delta W = B A, \quad B \in \mathbb{R}^{d \times r}, \quad A \in \mathbb{R}^{r \times k}, \quad r \ll \min(d,k).$$
Only $A$ and $B$ are trained; $W_0$ is frozen.   The forward pass becomes
$$h = W_0 x + \Delta W \cdot x = W_0 x + B(Ax).$$
The computation $Ax$ first projects the $k$-dimensional input down to $r$ dimensions; $B$ then projects back up to $d$ dimensions. Because $r$ is tiny (typically 4, 8, 16, 32, 64), $A$ and $B$ together have only $r(d + k)$ parameters — a dramatic reduction.

**Parameter count comparison.** For a typical transformer attention projection with $d = k = 4096$ and rank $r = 8$:

- Full fine-tuning: $4096 \times 4096 = 16{,}777{,}216$ trainable parameters per matrix.
- LoRA: $2 \times 4096 \times 8 = 65{,}536$ parameters per matrix.
- Reduction factor: $16{,}777{,}216 / 65{,}536 = 256\times$.

For all of GPT-3 175B, the LoRA paper reports an overall **10,000× reduction in trainable parameters and a 3× reduction in GPU memory requirements compared to full Adam fine-tuning**.

### 3.2 The Asymmetric Initialization

A and B are *not* initialized symmetrically. The original LoRA recipe is:

- $A$ initialized with Kaiming-uniform (or zero-mean Gaussian) noise: $A_0 \sim \mathcal{N}(0, \sigma^2)$.
- $B$ initialized to **zero**: $B_0 = 0$.

The asymmetry matters. At initialization, $\Delta W = B_0 A_0 = 0 \cdot A_0 = 0$, so the forward pass is *exactly* the pretrained model’s forward pass. Training begins from the unperturbed pretrained behaviour and gradually moves away from it. If we instead set both $A_0$ and $B_0$ to zero, *no gradients would flow* — $\partial \mathcal{L}/\partial A \propto B^\top$ and $\partial \mathcal{L}/\partial B \propto A^\top$, so both would be stuck at zero. If both were nonzero, the model would start with random noise injected into its predictions, destabilising training.

(There is a recent literature, including PiSSA and LoRA-One, that argues this “noise & zero” initialization is suboptimal and proposes initializing $A$ and $B$ from a singular-value decomposition of $W_0$ or of the one-step full-fine-tuning gradient. We cover these in §11.)

### 3.3 The Scaling Factor $\alpha/r$

LoRA’s effective update is not $BA$ but $(\alpha/r) BA$:
$$h = W_0 x + \frac{\alpha}{r} B A x.$$
The hyperparameter $\alpha$ is conventionally a constant of the same order as $r$ (frequently $\alpha = 2r$, sometimes $\alpha = r$). The purpose is to *decouple* the choice of rank from the effective learning rate of the update. When you double $r$, you simultaneously double the number of singular components $BA$ can represent; without the $1/r$ scaling, doubling $r$ would also roughly double the magnitude of $BA$ and force you to retune the learning rate. With the scaling, “increasing $r$” can be interpreted as increasing capacity, with the magnitude roughly preserved.

In the Hu et al. paper, the scaling is described as similar in spirit to the way attention is divided by $\sqrt{d_k}$. In practice, many practitioners treat $\alpha$ and learning rate as somewhat redundant — adjusting one is essentially equivalent to adjusting the other.

**Important caveat (rsLoRA).** Kalajdzievski (2023, arXiv:2312.03732) proved that the $\alpha/r$ scaling  is mathematically suboptimal for high ranks: it suppresses the effective gradient magnitude as $r$ grows, so increasing the rank does not actually buy you more capacity. The fix is to scale by $\alpha/\sqrt{r}$ instead.  This **rsLoRA** correction makes higher ranks (64–2048) actually beneficial.  We discuss it in §11.

### 3.4 Which Layers to Apply LoRA To

The original LoRA paper limited adapters to the query and value projections ($W_q$ and $W_v$) in self-attention. In §6.1 of that paper they conducted ablations on GPT-3 175B with a fixed parameter budget of 18M, corresponding to $r=8$ for one type of attention weight or $r=4$ for two types across all 96 layers. They found that *“adapting both $W_q$ and $W_v$ yields the best results”*, while putting the whole budget into $\Delta W_q$ or $\Delta W_k$ alone *“results in significantly lower performance”*.

Subsequent practice has expanded the target set substantially. The QLoRA paper (Dettmers et al., 2023) found that targeting all linear layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`  in Llama-style models) is necessary to fully recover 16-bit fine-tuning performance. The Biderman et al. (2024) study “LoRA Learns Less and Forgets Less” (TMLR; arXiv:2405.09673) finds that **attention-only LoRA underperforms; targeting MLP layers (or all linear layers) is essential**. Quoting their §4.7: *“targeting just ‘Attention’ underperforms both ‘MLP’ and ‘All’, where … most gains are interestingly driven by the ‘MLP’ modules.”*  In 2025, the prevailing default is **target all linear layers**, sometimes called the `"all-linear"` preset.

### 3.5 Degrees of Freedom versus Positions Affected

A subtle but important conceptual trap lurks in the parameter-count argument above. The naive intuition — *“fewer trainable parameters must mean fewer weights get updated”* — is wrong, and it leads to a wrong mental model of what LoRA does at the layer level. LoRA does not select a subset of weights to train and freeze the rest. The product $BA$ is a dense matrix of shape $d \times k$, and in general every one of its $d \cdot k$ entries is nonzero. **Every weight position in $W_0$ can, and typically does, receive a nonzero update.** The reduction is not in *which* positions change, but in how those changes are *related to each other*.

To make this visible, drop $r$ to its smallest meaningful value and work the arithmetic explicitly. Take $W_0 \in \mathbb{R}^{4 \times 4}$ and $r = 1$. Then $B$ is a single column of 4 numbers and $A$ is a single row of 4 numbers — eight trainable parameters in total, against the sixteen of a full $\Delta W$. Pick concrete values:
$$B = \begin{pmatrix} 1 \ 2 \ 3 \ 4 \end{pmatrix}, \qquad A = \begin{pmatrix} 10 & 20 & 30 & 40 \end{pmatrix}.$$
The update $\Delta W = BA$ is then
$$\Delta W ;=; \begin{pmatrix}
1 \cdot 10 & 1 \cdot 20 & 1 \cdot 30 & 1 \cdot 40 \
2 \cdot 10 & 2 \cdot 20 & 2 \cdot 30 & 2 \cdot 40 \
3 \cdot 10 & 3 \cdot 20 & 3 \cdot 30 & 3 \cdot 40 \
4 \cdot 10 & 4 \cdot 20 & 4 \cdot 30 & 4 \cdot 40
\end{pmatrix} ;=; \begin{pmatrix}
10 & 20 & 30 & 40 \
20 & 40 & 60 & 80 \
30 & 60 & 90 & 120 \
40 & 80 & 120 & 160
\end{pmatrix}.$$
All sixteen entries are nonzero. Every weight position is updated. So the “subset of weights” picture is wrong; the right picture is *the whole matrix moves, but the way it moves is constrained.*

Now look at the constraint. Row 2 is exactly twice row 1; row 3 is exactly three times row 1; row 4 is four times. Equivalently, every row of $\Delta W$ is a scalar multiple of the single row vector $A$, and every column is a scalar multiple of the single column vector $B$. If gradient descent were to decide that row 2’s optimal update was, say, $(5, 5, 5, 5)$ while row 1’s was $(10, 20, 30, 40)$, rank-1 LoRA simply *cannot represent that*. The rows are mathematically locked into proportionality, because they are all generated by multiplying the single column $B$ against the single row $A$. This is what “8 trainable numbers” buys you: a full-size update matrix whose rows are forced to live on a single line through the origin in $\mathbb{R}^4$.

Increasing the rank relaxes this constraint, one degree of freedom at a time. At $r = 2$, the update becomes $\Delta W = b_1 a_1^\top + b_2 a_2^\top$ — the sum of two rank-1 patterns. Each row of $\Delta W$ can now be written as $\beta_{i,1} a_1 + \beta_{i,2} a_2$, where $\beta_{i,1}$ and $\beta_{i,2}$ are this row’s coordinates inside the 2-dimensional subspace spanned by $a_1$ and $a_2$. Row 2 no longer has to be proportional to row 1; it can pick its own mixture of the two patterns. The geometric content of “rank at most $r$” is precisely this: every row of $\Delta W$ lies inside the same $r$-dimensional subspace of $\mathbb{R}^k$, and symmetrically every column lies inside the same $r$-dimensional subspace of $\mathbb{R}^d$. For the production setting $d = k = 4096$, $r = 8$ means all 16.8 million entries of $\Delta W$ are free to be nonzero, but every row of $\Delta W$ must lie inside one shared 8-dimensional subspace of $\mathbb{R}^{4096}$. That is the entire content of the rank constraint.

This reframing exposes why two common questions about LoRA do not have clean answers. People new to the method often ask “*which* weights get changed and which stay fixed?” or, in a layer-graph mental picture, “which *neurons* does LoRA pick?” Neither matches the geometry. LoRA does not pick weights and it does not pick neurons. A better question is: *what kinds of input-to-output transformations can $\Delta W$ express?* Writing the forward pass as $\Delta W , x = B (A x)$ makes the answer transparent. The update first squeezes the $k$-dimensional input through $A$ down to an $r$-dimensional summary, then expands that summary through $B$ back up to $d$ dimensions. Any information in $x$ that lies in the null space of $A$ is invisible to $\Delta W$, and any output direction outside the column space of $B$ is unreachable by $\Delta W$. So $\Delta W$ is constrained to be a transformation that *factors through an $r$-dimensional intermediate space.* That is the operational meaning of low rank, and it is a constraint on transformations, not on which entries are allowed to move.

The punchline against full fine-tuning sharpens accordingly. Full fine-tuning offers $d \cdot k$ independent dials and can express any $\Delta W$. LoRA at rank $r$ still touches all $d \cdot k$ entries of $W_0$, but those entries are not separately tunable — they are generated by $r \cdot (d + k)$ underlying dials, with the resulting $\Delta W$ forced to factor through an $r$-dimensional bottleneck. The empirical bet of the entire LoRA literature, supported by the intrinsic-dimension findings of §2.4 and the spectral evidence to be presented in §5.2, is that task adaptation typically *does* require only a low-rank update, so this constraint is almost free in practice. The naïve intuition “fewer parameters means fewer weights touched” overestimates the cost of LoRA and misdescribes its mechanism. The accurate statement is this: *LoRA leaves the set of affected weight positions essentially unchanged from full fine-tuning, but constrains the number of independent degrees of freedom available to generate those changes.*

A small sanity check: at $d = k = 4$ and $r = 2$, the parameter count $r(d+k) = 16$ equals the count of a full $\Delta W$, and indeed any $4 \times 4$ matrix of rank at most 2 is reachable. Savings emerge only once $r \ll \min(d, k)$ — which is the regime the rest of this chapter actually cares about.

### 3.6 Merging Back at Inference

Because $\Delta W = (\alpha/r) BA$ is a matrix of the same shape as $W_0$, one can compute
$$W_{\text{merged}} = W_0 + \tfrac{\alpha}{r} BA$$
once, after training, and replace the original weight matrix with the merged one. The LoRA branch is then *gone* — inference cost is identical to the base model. This is the property that makes LoRA dominate over adapter-bottleneck methods: adapter methods cannot be merged in this way and add ~5–30% inference latency. Quoting Hu et al.: *“When deployed in production, we can explicitly compute and store $W = W_0 + BA$ and perform inference as usual. … This guarantees that we introduce no additional latency during inference compared to a fine-tuned model by construction.”*

-----

## 4. A Worked Numerical Example for LoRA

I will work a small example by hand so you can verify every arithmetic step. Take $d = k = 4$, $r = 2$, $\alpha = 2$ (so the scaling factor $\alpha/r = 1$).

### 4.1 The Matrices

Let the pretrained weight be
$$W_0 = \begin{pmatrix} 0.5 & -0.2 & 0.1 & 0.3 \ 0.0 & 0.4 & -0.3 & 0.2 \ 0.2 & 0.1 & 0.5 & -0.4 \ -0.1 & 0.3 & 0.0 & 0.6 \end{pmatrix}.$$

Initialise $A \in \mathbb{R}^{2 \times 4}$ with small Gaussian noise (I am choosing convenient values for pedagogy):
$$A_0 = \begin{pmatrix} 0.10 & -0.05 & 0.07 & -0.02 \ -0.04 & 0.06 & 0.03 & 0.08 \end{pmatrix},$$
and $B_0 = \mathbf{0} \in \mathbb{R}^{4 \times 2}$ (the zero matrix).

### 4.2 Forward Pass at Initialization

Take input $x = (1, 2, -1, 0)^\top$.

Step 1: $A_0 x$.
$$A_0 x = \begin{pmatrix} 0.10\cdot 1 + (-0.05)\cdot 2 + 0.07\cdot (-1) + (-0.02)\cdot 0 \ -0.04\cdot 1 + 0.06 \cdot 2 + 0.03\cdot(-1) + 0.08\cdot 0 \end{pmatrix} = \begin{pmatrix} -0.07 \ 0.05 \end{pmatrix}.$$

Step 2: $B_0 (A_0 x) = \mathbf{0} \cdot (-0.07, 0.05)^\top = (0,0,0,0)^\top$.

Step 3: $W_0 x$.

- Row 1: $0.5 \cdot 1 + (-0.2)\cdot 2 + 0.1\cdot(-1) + 0.3\cdot 0 = 0.5 - 0.4 - 0.1 + 0 = 0.0$.
- Row 2: $0.0 + 0.8 + 0.3 + 0 = 1.1$.
- Row 3: $0.2 + 0.2 - 0.5 + 0 = -0.1$.
- Row 4: $-0.1 + 0.6 + 0.0 + 0 = 0.5$.

So $h_0 = W_0 x + B_0 A_0 x = (0.0, 1.1, -0.1, 0.5)^\top + 0 = (0.0, 1.1, -0.1, 0.5)^\top$. **The LoRA branch contributes exactly zero, so the model output equals the pretrained model output.** This is the asymmetric-initialization payoff.

### 4.3 After One Gradient Step

Suppose after one optimisation step the matrices have become
$$A_1 = \begin{pmatrix} 0.10 & -0.05 & 0.07 & -0.02 \ -0.04 & 0.06 & 0.03 & 0.08 \end{pmatrix}, \quad B_1 = \begin{pmatrix} 0.02 & -0.01 \ -0.03 & 0.04 \ 0.05 & 0.02 \ 0.01 & -0.03 \end{pmatrix}.$$

The new effective update is $\Delta W_1 = B_1 A_1$. Each entry $(\Delta W_1)*{ij} = \sum*{p=1}^{r=2} B_{ip} A_{pj}$. For example:

- $(\Delta W_1)_{11} = 0.02\cdot 0.10 + (-0.01)\cdot(-0.04) = 0.0020 + 0.0004 = 0.0024$.
- $(\Delta W_1)_{12} = 0.02\cdot(-0.05) + (-0.01)\cdot 0.06 = -0.0010 - 0.0006 = -0.0016$.
- $(\Delta W_1)_{13} = 0.02\cdot 0.07 + (-0.01)\cdot 0.03 = 0.0014 - 0.0003 = 0.0011$.
- $(\Delta W_1)_{14} = 0.02\cdot(-0.02) + (-0.01)\cdot 0.08 = -0.0004 - 0.0008 = -0.0012$.

Completing the matrix you obtain a $4\times 4$ matrix that has rank exactly 2 (by construction, since it is the product of a $4\times 2$ and a $2\times 4$ matrix; no rank-2 product can exceed rank 2). The original $W_0$ had full rank 4. So $\Delta W_1$ lives on a 2-dimensional “subspace” of the 16-dimensional weight matrix space.

### 4.4 Gradient Flow

During backpropagation, only $A$ and $B$ receive gradients. Let $\mathcal{L}$ be the loss and let the upstream gradient flowing back into $h$ be $g = \partial \mathcal{L}/\partial h \in \mathbb{R}^4$. The chain rule gives:
$$\frac{\partial \mathcal{L}}{\partial B} = g , (Ax)^\top \in \mathbb{R}^{d \times r}, \qquad \frac{\partial \mathcal{L}}{\partial A} = (B^\top g) , x^\top \in \mathbb{R}^{r \times k}.$$
Both gradients are *outer products* of small vectors — very cheap to compute. The pretrained weight $W_0$ has `requires_grad=False`, so PyTorch (or any framework) silently skips computing its gradient, saving the largest single block of memory.

### 4.5 Parameter Count Savings

For this toy example: full fine-tuning would have $4 \times 4 = 16$ trainable parameters per layer; LoRA has $2 \times 4 + 4 \times 2 = 16$ parameters. So at $r = 2$ with $d = k = 4$ there is no saving — the saving kicks in once $r \ll \min(d,k)$. In a realistic transformer with $d = 4096$ and $r = 8$, full fine-tuning is $16.78\text{M}$ parameters per matrix, LoRA is $65,536$ — a 256× reduction.

-----

## 5. Why LoRA Works: Theory and Evidence

### 5.1 Intrinsic Dimension Revisited

Aghajanyan et al.’s (2020) finding — that 200 randomly-projected parameters can fine-tune RoBERTa-base to within 10% of full performance — is essentially a statement that the *fine-tuning loss landscape* has a *very low effective dimension*. LoRA differs from random projection in that the projection (parameterized by $A$ and $B$) is itself *learned*. Intuitively, a learned low-dimensional subspace should require *even fewer* dimensions than a random one.

### 5.2 Empirical Spectral Evidence

In §7.2 of the LoRA paper, Hu et al. compute the singular values of the learned $\Delta W$ from full fine-tuning and observe that the spectrum decays sharply — most of the Frobenius norm is in the top few singular triplets. This means **the fine-tuning update is approximately low-rank already**, even when nothing constrains it to be. LoRA simply makes this implicit fact explicit and exploits it.

### 5.3 Connection to Truncated SVD

If $\Delta W^*$ denotes the optimal full-rank fine-tuning update, the best rank-$r$ approximation in Frobenius norm is the truncated SVD $\Delta W^*_r = U_r \Sigma_r V_r^\top$. LoRA’s $BA$ can absorb such a decomposition by setting $B = U_r \Sigma_r^{1/2}$, $A = \Sigma_r^{1/2} V_r^\top$. Gradient descent on $A, B$ does not necessarily *find* the SVD-optimal update, but it operates over the same expressive class, and Zhang, Liu, Chen (2025, arXiv:2502.01235, “LoRA-One”) show that under one-step gradient descent, LoRA adapters align with the dominant singular subspaces of the full one-step gradient. So LoRA is, both in expressive class and in practice, an approximate truncated-SVD method.

### 5.4 What Ranks Actually Work?

The original paper’s surprising empirical claim was that **very low ranks suffice**. Table 6 of Hu et al. showed that $r=1$ or $r=2$ for adapting GPT-3 attention to several GLUE-style tasks was competitive with full fine-tuning. The 2024 Biderman et al. study qualifies this: for *easy* tasks (chat, classification, instruction-following on diverse data), $r=8$ to $r=16$ is plenty. For *hard* tasks — particularly **code generation and continued pretraining on math/code corpora** — much higher ranks are required, $r=256$ being competitive only at the very top. The key empirical finding from Biderman et al. is verbatim from their abstract: *“full finetuning learns perturbations with a rank that is 10–100× greater than typical LoRA configurations, possibly explaining some of the reported gaps.”*  In concrete numbers, on Magicoder-110K code instruction tuning of Llama-2-7B, full fine-tuning reaches HumanEval=0.497 at epoch 8, while LoRA reaches 0.358 at $r=16$, 0.417 at $r=64$, and 0.498 at $r=256$ (epoch 4).

-----

## 6. Quantization Primer

To understand QLoRA we need the basics of numerical quantization.

### 6.1 Why Quantize?

A 65B-parameter model in FP16 is $130$ GB. No single consumer GPU has that much memory. The bandwidth between GPU memory (HBM) and compute (the matrix-multiply units) is also a major bottleneck: in many inference workloads the GPU is *memory-bandwidth bound*, meaning it spends most of its time *waiting* for weights to arrive from HBM. If we encode each weight in 4 bits rather than 16, we shrink memory by 4× *and* feed weights to the compute units 4× faster.

### 6.2 Floating-Point Formats

A floating-point number is encoded as `sign · mantissa · 2^exponent`. The trade-off between range and precision depends on how many bits are spent on the exponent vs the mantissa:

- **FP32** (IEEE single): 1 sign, 8 exponent, 23 mantissa. Range $\approx 10^{\pm 38}$, ~7 decimal digits of precision.
- **FP16** (IEEE half): 1 sign, 5 exponent, 10 mantissa. Range $\approx 10^{\pm 5}$, ~3 decimal digits. *Limited range often causes overflow for large activations.*
- **BF16** (bfloat16, Google Brain): 1 sign, 8 exponent, 7 mantissa. **Same range as FP32** but only ~2.5 decimal digits of precision. Widely preferred over FP16 for training because the larger exponent range avoids overflow/underflow.

In QLoRA, computations always happen in BF16, *never* in FP16.

### 6.3 Integer Quantization

Integer quantization maps a continuous range $[a, b]$ to $2^k$ discrete bins. The simplest form, **symmetric, per-tensor, absmax quantization** for INT8, works as follows. Given a weight tensor $W$:

1. Compute the absolute maximum: $s = \max_{ij} |W_{ij}|$.
2. Compute the quantization scale: $\Delta = s / 127$ (so that values are mapped to integers in $[-127, 127]$).
3. Quantize: $\hat{W} = \mathrm{round}(W / \Delta) \in {-127, \ldots, 127}^{m \times n}$.
4. Dequantize for compute: $\tilde{W} = \hat{W} \cdot \Delta \approx W$.

The roundtrip error $\tilde{W} - W$ is at most $\Delta / 2$ per entry. **Asymmetric quantization** instead maps $[w_{\min}, w_{\max}]$ to $[0, 2^k - 1]$ with both a scale and a *zero point*; it is preferred when the data is not centred at zero (e.g., activations after ReLU).

**Granularity**: the scale $\Delta$ can be computed per tensor (one $\Delta$ for the whole matrix), per channel/row (one $\Delta$ per output channel), or **block-wise**: split the flattened weight into blocks of, say, 64 consecutive elements and use a separate $\Delta$ for each block. Block-wise quantization is much more robust to outliers and is what QLoRA uses.

### 6.4 Quantization Error and Its Distribution-Sensitivity

For weights that are roughly normally distributed (which transformer weights empirically are), most values are near zero and a few outliers extend far into the tails. Uniform bins (as in plain INT4) waste resolution on the tails and starve the centre. For 4 bits — only 16 buckets — this is catastrophic.

### 6.5 NF4: 4-bit NormalFloat

The QLoRA paper proposes **4-bit NormalFloat (NF4)**, a non-uniform 4-bit codebook whose bin boundaries are chosen so that *each bin under a standard normal distribution* $\mathcal{N}(0,1)$ *contains approximately equal probability mass*.  They call this **quantile quantization**: it is information-theoretically optimal under the assumption that the input data is normally distributed.

The construction (Dettmers et al. 2023, Appendix E):

1. Compute the quantile function $\Phi^{-1}$ of $\mathcal{N}(0,1)$ at $2^k = 16$ approximately-equiprobable points.
2. Adjust endpoints so that $-1$ and $+1$ are exactly representable  (one bin centred at zero, asymmetric to fit the 16 codes).
3. Normalise so that the codebook spans $[-1, +1]$.

The resulting codebook (verbatim from the QLoRA paper Appendix E, as recovered by John D. Cook 2026):
$${-1.0,; -0.6962,; -0.5251,; -0.3949,; -0.2844,; -0.1848,; -0.0911,; 0.0,$$
$$0.0796,; 0.1609,; 0.2461,; 0.3379,; 0.4407,; 0.5626,; 0.7230,; 1.0}.$$
Note the *non-uniform spacing*: bins are dense near zero and sparse near $\pm 1$, matching the density of a normal distribution. Crucially, **zero is exactly representable**  — this matters for sparse activations.

A weight tensor is then quantised in **blocks of 64**, where each block is:

1. Divided by its block-wise absmax $s_{\text{block}}$ (so values lie in $[-1, 1]$).
2. Each value mapped to the nearest of the 16 NF4 codes (stored as a 4-bit index).

The block scale $s_{\text{block}}$ is stored separately, typically in FP32.  The original QLoRA paper notes that *“NF4 is superior to FP4 in terms of quantization precision”* and that *“NF4 with double quantization fully recovers the 16-bit LoRA MMLU performance.”*

### 6.6 Double Quantization

Storing one FP32 block-scale per 64 weights adds $32/64 = 0.5$ bits per weight of overhead. To reduce this, QLoRA introduces **double quantization**: the FP32 block-scales themselves are quantised to FP8 in blocks of 256, with a tiny FP32 second-level scale per super-block. Subtracting the mean before quantizing the scales makes the distribution symmetric and amenable to symmetric quantization.

Dettmers et al. compute the savings exactly: *“On average, for a blocksize of 64, this quantization reduces the memory footprint per parameter from 32/64 = 0.5 bits, to 8/64 + 32/(64·256) = 0.127 bits, a reduction of 0.373 bits per parameter.”* For a 65B model, that is $65\text{B} \times 0.373 \text{ bits} / 8 \approx 3$ GB saved.

-----

## 7. QLoRA: The Full Technique

### 7.1 The Three Innovations

QLoRA (Dettmers, Pagnoni, Holtzman, Zettlemoyer, May 2023, arXiv:2305.14314, NeurIPS 2023) is a system, not just an algorithm, built from three innovations:

1. **4-bit NormalFloat (NF4)** quantization of the frozen base model weights.
2. **Double quantization** of the per-block scales.
3. **Paged optimizers**: uses NVIDIA unified memory to page Adam optimizer states between GPU and CPU when GPU memory spikes (e.g., during long-sequence attention).

The key conceptual trick is to *combine* heavy weight quantization with LoRA: the base model weights are stored in NF4 (4 bits each), the LoRA adapters $A$ and $B$ in BF16. During each forward pass, each NF4 block is **just-in-time dequantized to BF16**, multiplied by the input, and added to the BF16 LoRA branch’s output. During backprop, gradients flow only to $A$ and $B$.

### 7.2 The Forward Pass

For a single quantized linear layer:
$$h = \underbrace{\mathrm{dequant}*{\text{NF4} \to \text{BF16}}(W_0^{\text{NF4}}) \cdot x}*{\text{frozen base}} + \underbrace{\tfrac{\alpha}{r} B (A x)}_{\text{LoRA in BF16}}.$$
The dequantization step is fused into the matmul kernel so the BF16 weights never have to be materialized in HBM — they exist only transiently in registers/SRAM. The base model lives in 4-bit storage at rest; this is the source of the memory savings.

### 7.3 Why Accuracy Is Preserved

A naive 4-bit quantized model loses accuracy. So why does QLoRA recover full 16-bit fine-tuning performance? Two reasons:

1. **The quantization error from NF4 is small** — Table 3 of the QLoRA paper shows that NF4 alone (no fine-tuning) yields perplexity within ~0.1 of 16-bit on LLaMA, much better than FP4 or naive INT4.
2. **The LoRA adapters absorb residual quantization error during fine-tuning.** Even if NF4 perturbs $W_0$ to $\tilde{W}_0 = W_0 + E$ where $E$ is small quantization noise, the LoRA branch can learn $\Delta W$ that compensates for the low-rank component of $-E$ that matters for the task. Empirically the result is verbatim from §5 of the paper: *“NF4 with double quantization fully recovers the 16-bit LoRA MMLU performance.”*

The LoftQ extension (Li et al., ICLR 2024, arXiv:2310.08659) makes this absorption explicit: they jointly choose the quantization *and* the LoRA initialization to minimise the quantization-induced perturbation.  See §11.

### 7.4 The Memory Math

Let’s redo the memory budget for fine-tuning a 65B model with QLoRA versus full BF16 fine-tuning:

|Component                             |Full BF16 FT                          |QLoRA                                                                                   |
|--------------------------------------|--------------------------------------|----------------------------------------------------------------------------------------|
|Base weights                          |$65\text{B} \times 2\text{B} = 130$ GB|$65\text{B} \times 0.5\text{B} \text{ (NF4)} + 0.127\text{ bits overhead} \approx 33$ GB|
|Gradients                             |130 GB                                |$\approx 0$ for base; only LoRA gradients (~100 MB)                                     |
|Adam states (FP32 $m,v$ + master copy)|$65\text{B}\times 12\text{B} = 780$ GB|Only for LoRA params (~MBs)                                                             |
|Activations                           |5–30 GB                               |5–30 GB (similar; this is unchanged)                                                    |
|**Total (typical)**                   |**>780 GB**                           |**<48 GB**                                                                              |

The published QLoRA abstract is verbatim: *“QLoRA reduces the average memory requirements of finetuning a 65B parameter model from >780GB of GPU memory to <48GB without degrading the runtime or predictive performance compared to a 16-bit fully finetuned baseline.”* This is what enabled the Guanaco-65B model to be fine-tuned on a single 48-GB A6000 GPU, reaching, in the paper’s own words, *“99.3% of the performance level of ChatGPT while only requiring 24 hours of finetuning on a single GPU”*  (on the Vicuna benchmark, as evaluated by GPT-4 — a noisy metric, but the result is striking).

For a 7B model, QLoRA reduces the memory budget so much that you can fine-tune Llama-7B on a **single 24-GB consumer GPU** (RTX 3090 or 4090). The breakdown (Llama-2-7B, batch size 1, sequence length 2048, rank 16 on all linear layers): ~3.5 GB for the NF4 base, ~0.5 GB for activations with gradient checkpointing, ~0.2 GB for the LoRA parameters and their Adam states, ~5 GB for activation memory at the LoRA layers — total around 10 GB, with headroom.

### 7.5 Paged Optimizers

Even with 4-bit quantization, attention activations can momentarily spike (e.g., the $\mathcal{O}(L^2)$ attention matrices for long sequences $L$). QLoRA uses **NVIDIA’s unified memory feature**  to automatically page rarely-used optimizer state from GPU to CPU when memory pressure peaks, and back when needed. This avoids out-of-memory crashes during sporadic spikes without requiring you to manually shard or offload.

-----

## 8. Worked Example for Quantization and QLoRA

### 8.1 A Tiny Block, Quantized

Take a single block of $b = 8$ weights (in real QLoRA, $b = 64$):
$$w = (0.31,; -0.84,; 0.05,; 0.62,; -0.11,; 0.78,; -0.27,; 0.09).$$

**Step 1 — block absmax**: $s = \max |w_i| = 0.84$.

**Step 2 — normalise**: divide each by $s$ to get $\tilde w \in [-1, 1]$:
$$\tilde w \approx (0.369,; -1.000,; 0.060,; 0.738,; -0.131,; 0.929,; -0.321,; 0.107).$$

**Step 3 — map each to the nearest NF4 code.** Recall the NF4 codebook
$${-1.0,; -0.6962,; -0.5251,; -0.3949,; -0.2844,; -0.1848,; -0.0911,; 0.0,$$
$$0.0796,; 0.1609,; 0.2461,; 0.3379,; 0.4407,; 0.5626,; 0.7230,; 1.0}.$$

Nearest assignments (verify by inspection):

|$\tilde w$|nearest NF4 code|NF4 index (4-bit)|
|----------|----------------|-----------------|
|$0.369$   |$0.3379$        |$11$             |
|$-1.000$  |$-1.0$          |$0$              |
|$0.060$   |$0.0796$        |$8$              |
|$0.738$   |$0.7230$        |$14$             |
|$-0.131$  |$-0.0911$       |$6$              |
|$0.929$   |$1.0$           |$15$             |
|$-0.321$  |$-0.2844$       |$4$              |
|$0.107$   |$0.0796$        |$8$              |

So we store the block as **eight 4-bit indices (4 bytes total) plus one FP32 scale $s = 0.84$** (which in turn would be jointly quantized with 255 other block scales under double quantization).

**Step 4 — dequantize for compute**: $\tilde w^{\text{rec}} = s \cdot \mathrm{NF4}[\text{idx}_i]$.
$$\tilde w^{\text{rec}} = (0.84 \cdot 0.3379, \ldots) = (0.2838,; -0.84,; 0.0669,; 0.6073,; -0.0765,; 0.84,; -0.2389,; 0.0669).$$

Per-element quantization error $w_i - \tilde w_i^{\text{rec}}$:
$$(0.026,; 0.000,; -0.017,; 0.013,; -0.034,; -0.060,; -0.031,; 0.023).$$
RMS error $\approx 0.030$, about $3.6%$ of $s$. With 64-element blocks and well-behaved transformer weights, the error is typically <2%.

### 8.2 NF4 Bucketing Visualised

If you plot the 16 NF4 codes on a number line you see they cluster near zero: 7 codes lie in $[-0.18, 0.18]$, only 2 codes ($-1.0, 1.0$) lie at the extremes. Under a standard normal, ~68% of mass is within one standard deviation — and NF4 spends ~14 of its 16 codes covering that region. By contrast, uniform INT4 would waste 8 of its 16 codes on the tails where almost no data lives.

### 8.3 A QLoRA Forward Pass End to End

Imagine the linear layer has stored weight $W_0^{\text{NF4}}$ (the 4-bit indices and scales described above), LoRA matrices $A \in \mathbb{R}^{r \times k}$ (BF16) and $B \in \mathbb{R}^{d \times r}$ (BF16), and BF16 input $x$. The computation:

1. CUDA kernel reads NF4 block; looks up code values; multiplies by block scale; gets BF16 weight tile $\tilde W_0$ (in registers).
2. Computes $\tilde W_0 \cdot x$ tile by tile, accumulating in BF16 (or FP32 for numerical stability of the sum).
3. Computes $u = A x$, $v = B u$, scales by $\alpha/r$.
4. Returns $\tilde W_0 \cdot x + (\alpha/r) v$.

The base weights never persist in HBM as BF16; they exist only transiently. This is what makes the memory savings real even during the forward pass, not just at rest.

-----

## 9. PyTorch Code Implementation

The point of this section is *not* to ship production code; the canonical production library is HuggingFace `peft`. The goal here is to show you what `peft` does under the hood, so that when it breaks (and it will), you can debug it.

### 9.1 A LoRALinear Module from Scratch

```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class LoRALinear(nn.Module):
    """
    A drop-in replacement for nn.Linear that adds a LoRA branch.

    The base nn.Linear weights are FROZEN (requires_grad=False).
    Only the LoRA matrices A and B (and optional bias) are trainable.
    """
    def __init__(self, in_features: int, out_features: int, r: int = 8,
                 alpha: float = 16.0, dropout: float = 0.0, bias: bool = False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.r = r
        self.alpha = alpha
        self.scaling = alpha / r  # the alpha/r scaling factor

        # The frozen pretrained linear layer. nn.Linear stores W of shape
        # (out_features, in_features); the forward is x @ W.T + b.
        self.base = nn.Linear(in_features, out_features, bias=bias)
        for p in self.base.parameters():
            p.requires_grad_(False)  # FREEZE the base weights

        # LoRA matrices.
        # We follow the convention from the original LoRA paper:
        #   A : (r, in_features)  -- "projection-down", Gaussian init
        #   B : (out_features, r) -- "projection-up", zero init
        # so that BA = 0 at initialization and the model output is unchanged.
        self.lora_A = nn.Parameter(torch.empty(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

        # Optional dropout applied to the LoRA branch input.
        self.lora_dropout = nn.Dropout(p=dropout) if dropout > 0 else nn.Identity()

        self._merged = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.base(x)
        if self._merged:
            return base_out

        # LoRA path:  x -> A x -> B (A x) -> scale by alpha/r
        x_drop = self.lora_dropout(x)
        lora_out = F.linear(x_drop, self.lora_A)        # (..., r)
        lora_out = F.linear(lora_out, self.lora_B)      # (..., out_features)
        return base_out + self.scaling * lora_out

    @torch.no_grad()
    def merge(self) -> None:
        """Fold (alpha/r) * B A into the base weight for zero-overhead inference."""
        if self._merged:
            return
        delta_W = self.scaling * (self.lora_B @ self.lora_A)
        self.base.weight.add_(delta_W)
        self._merged = True

    @torch.no_grad()
    def unmerge(self) -> None:
        if not self._merged:
            return
        delta_W = self.scaling * (self.lora_B @ self.lora_A)
        self.base.weight.sub_(delta_W)
        self._merged = False
```

Three subtleties:

1. We initialise `lora_A` with Kaiming-uniform (PyTorch’s `nn.Linear` default) and `lora_B` with zeros, so that the LoRA term is exactly zero at the start.
2. We freeze the base weights with `requires_grad_(False)` — autograd will then *not* build the graph for them, saving memory.
3. After training, `merge()` folds the LoRA delta into the base weight, so deployment costs zero extra latency. `unmerge()` is the inverse for swapping adapters.

### 9.2 Monkey-Patching an Existing Model

```python
def replace_linear_with_lora(module: nn.Module, r: int = 8, alpha: float = 16.0,
                             target_substrings=("q_proj", "v_proj")):
    """
    Walk a model, replacing every nn.Linear whose qualified name contains one of
    the target substrings with a LoRALinear that wraps its frozen weights.
    """
    for name, child in module.named_children():
        if isinstance(child, nn.Linear) and any(s in name for s in target_substrings):
            lora_layer = LoRALinear(child.in_features, child.out_features,
                                    r=r, alpha=alpha,
                                    bias=(child.bias is not None))
            with torch.no_grad():
                lora_layer.base.weight.copy_(child.weight)
                if child.bias is not None:
                    lora_layer.base.bias.copy_(child.bias)
            for p in lora_layer.base.parameters():
                p.requires_grad_(False)
            setattr(module, name, lora_layer)
        else:
            replace_linear_with_lora(child, r=r, alpha=alpha,
                                     target_substrings=target_substrings)
```

### 9.3 The Training Loop

```python
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=2e-4, weight_decay=0.0
)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"trainable: {trainable:,} / total: {total:,}  ({100*trainable/total:.4f}%)")

model.train()
for batch in dataloader:
    optimizer.zero_grad()
    loss = model(**batch).loss
    loss.backward()
    optimizer.step()
```

Two key points:

1. We pass *only the parameters with `requires_grad=True`* to AdamW. If you pass `model.parameters()` and some are frozen, AdamW will still happily allocate FP32 $m,v$ buffers for them (~12 bytes per frozen parameter) and waste memory. Filter explicitly.
2. The base model should be in `train()` mode only if it has trainable layers; if you have frozen everything except adapters, set `model.eval()` then `model.lora_A.requires_grad_(True)` etc. to keep BatchNorm/Dropout in inference mode. For transformer-based LLMs without batchnorm this is less critical, but for vision models it matters.

### 9.4 Saving and Loading Just the Adapter

```python
adapter_state = {n: p for n, p in model.state_dict().items()
                 if "lora_A" in n or "lora_B" in n}
torch.save(adapter_state, "my_adapter.pt")   # a few tens of MB

# Later: load the same base model, recreate LoRA wrappers, then:
model.load_state_dict(adapter_state, strict=False)
```

A typical LoRA adapter for a 7B model with rank 16 on all linear layers weighs **20–80 MB** — versus 14 GB for a full BF16 fine-tuned model. This is the property that makes serving thousands of specialised LoRAs on the same base model (S-LoRA, Punica, multi-tenant systems) practical.

### 9.5 The Canonical Modern Approach (HuggingFace PEFT + bitsandbytes for QLoRA)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model_id = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# QLoRA: load the base model in 4-bit NF4, compute in BF16.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",          # NormalFloat4
    bnb_4bit_use_double_quant=True,     # the second quantization (FP8 scales)
    bnb_4bit_compute_dtype=torch.bfloat16,  # BF16 matmul
)
base = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
)
base = prepare_model_for_kbit_training(base)  # casts norms to FP32, etc.

lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,                        # the alpha = 2r convention
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(base, lora_cfg)
model.print_trainable_parameters()
# e.g. "trainable params: 39,976,960 || all params: 6,778,499,072 || trainable%: 0.5897"
```

`prepare_model_for_kbit_training` performs three small but important operations:

- Casts the *layer norms* to FP32 (LayerNorm’s tiny FP32 parameters add no memory but greatly improve numerical stability).
- Casts the *language-modelling head* to FP32 for the same reason.
- Enables gradient checkpointing in a way compatible with frozen weights.

After training:

```python
model.save_pretrained("my-qlora-llama")
# Saves only the LoRA adapter (~80 MB).

# Merging back into a 16-bit base (you cannot merge into a 4-bit base):
from peft import PeftModel
base_fp16 = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16)
merged = PeftModel.from_pretrained(base_fp16, "my-qlora-llama").merge_and_unload()
merged.save_pretrained("my-llama-merged")
```

-----

## 10. Practical Considerations

### 10.1 Hyperparameter Defaults That Actually Work

Based on the QLoRA paper, the Unsloth defaults guide, and Biderman et al. (2024), here is a tuned starting point for 2025 fine-tuning of a 7B Llama-style model on a small task (≤100K examples):

|Hyperparameter  |Default                     |Notes                                                    |
|----------------|----------------------------|---------------------------------------------------------|
|`r` (rank)      |16                          |8 if memory-tight; 32–64 if task is hard (code, math).   |
|`lora_alpha`    |32 (= 2r)                   |Or set $\alpha = r$ if using rsLoRA scaling.             |
|`lora_dropout`  |0.05 (7B/13B) or 0.1 (small)|The QLoRA paper used 0.1 for 7B/13B and 0.05 for 33B/65B.|
|`target_modules`|all linear                  |$q,k,v,o,$gate,up,down. The big lesson of Biderman et al.|
|Learning rate   |2e-4 to 3e-4                |Higher than full FT (which uses 1e-5–5e-5).              |
|Optimizer       |AdamW (paged for QLoRA)     |`paged_adamw_8bit` for QLoRA.                            |
|LR schedule     |cosine, 3% warmup           |Standard.                                                |
|Weight decay    |0.0 on LoRA params          |0.1 hurts; LoRA is already strongly regularised.         |
|Batch size      |as large as fits            |Effective batch via grad accumulation: 64–256 sequences. |
|Epochs          |2–4 (IFT), 1 (CPT)          |More epochs help LoRA more than FT (Biderman et al.).    |

### 10.2 Module Targeting Decision Tree

- **Lightweight task (style transfer, classification):** attention only (`q_proj`, `v_proj`) at $r=8$ is fine.
- **Instruction tuning, chat:** all linear at $r=16$. This is the modern default.
- **Continued pretraining, code, math:** all linear at $r \ge 64$, with rsLoRA scaling ($\alpha/\sqrt{r}$), 2–6 epochs. Even then, expect a small gap to full fine-tuning.

### 10.3 Common Pitfalls

1. **Forgetting to filter `requires_grad`** when constructing the optimiser. You will allocate Adam state for frozen weights and OOM unnecessarily.
2. **Using FP16 instead of BF16** for the compute dtype in QLoRA. The original Llama-style models have activations whose dynamic range overflows FP16; BF16 has the same exponent range as FP32 and avoids this. The QLoRA paper recommends BF16 explicitly.
3. **Too low a rank for a hard task.** If your task needs ~rank-200 worth of structural change (Biderman et al.’s code-CPT finding), $r=8$ will leave a large gap.
4. **Setting the learning rate too low.** LoRA’s effective learning rate is multiplied by $\alpha/r$; if you reuse a full-fine-tuning learning rate of 1e-5 you will see no learning. 2e-4 is a far better starting point.
5. **Forgetting `model.eval()` at inference.** Adapters with dropout enabled will randomly zero out the LoRA contribution at inference time, hurting accuracy.
6. **Saving the merged model and the adapter both as your “final checkpoint.”** Decide which you want: an adapter for multi-tenancy and storage, or a merged model for single-tenant serving.

### 10.4 LoRA vs Full FT: When Does the Gap Open?

The cleanest published study is Biderman, Portes, Gonzalez Ortiz et al., *“LoRA Learns Less and Forgets Less”* (TMLR Aug 2024, arXiv:2405.09673). Quoting their headline result: *“in the standard low-rank settings, LoRA substantially underperforms full finetuning”*   on code and math continued pretraining; but *“LoRA better maintains the base model’s performance on tasks outside the target domain.”*   Concretely:

- **Code IFT (Magicoder-110K), Llama-2-7B**: full FT HumanEval=0.497 (epoch 8); LoRA $r=16$ → 0.358, $r=64$ → 0.417, $r=256$ → 0.498 (epoch 4).  High-rank LoRA matches full FT; low-rank does not.
- **Code CPT (StarCoder-Python, 20B tokens)**: full FT HumanEval=0.263; best LoRA ($r=256$) HumanEval=0.224.  **Gap persists even at high rank** in continued pretraining.
- **Math IFT (MetaMathQA)**: $r=64$ suffices to approach full FT (GSM8K=0.624 vs 0.642).
- **Forgetting (HellaSwag/ARC/WinoGrande mean)**: LoRA degrades less than full FT, especially as training proceeds.

The paper also reports that *“LoRA is very sensitive to hyperparameters, including learning rates, choice of target modules, ranks, and scaling factors; setting these properly is a prerequisite to approach full finetuning performance.”*

The practical takeaway: if you are doing **light task adaptation**, LoRA $r=16$ on all linear layers is essentially free relative to full FT. If you are doing **heavy domain shift** (continued pretraining on a new programming language), expect a measurable quality gap unless you use very high ranks and accept the corresponding compute.

-----

## 11. Recent Alternatives and Extensions (2024–2025)

The PEFT landscape has exploded since QLoRA. Here are the methods that matter, with enough detail to use them.

### 11.1 DoRA — Weight-Decomposed Low-Rank Adaptation

(Liu, Wang, Yin, Molchanov, Wang, Cheng, Chen, 2024, arXiv:2402.09353, ICML 2024 Oral; NVIDIA)

DoRA observes that the weight matrix can be written as a *magnitude* (per-column norm $m \in \mathbb{R}^k$) times a *direction* (column-normalised matrix $V \in \mathbb{R}^{d \times k}$):
$$W = m \cdot \frac{V}{|V|_c}$$
where $|V|_c$ denotes the column-wise norm. DoRA fine-tunes the magnitude  $m$ as a small trainable vector *and* applies a standard LoRA $\Delta V = BA$ to the direction. The DoRA paper reports consistent improvements over LoRA *“on fine-tuning LLaMA, LLaVA, and VL-BART on various downstream tasks, such as commonsense reasoning, visual instruction tuning, and image/video-text understanding,”* with no additional inference cost (everything still merges back into $W$). DoRA is supported by HuggingFace PEFT via `LoraConfig(use_dora=True)`.

### 11.2 LoRA+ — Different Learning Rates for $A$ and $B$

(Hayou, Ghosh, Yu, 2024, arXiv:2402.12354, ICML 2024)

Hayou et al. prove that  in the infinite-width limit, LoRA’s choice to update $A$ and $B$ with the *same* learning rate is sub-optimal: the optimal ratio $\eta_B / \eta_A$ grows with width. Their fix — using a higher learning rate for $B$ than for $A$ (typically 16× larger) — yields, verbatim from the abstract, *“performance (1-2 % improvements) and finetuning speed (up to ∼ 2X SpeedUp), at the same computational cost as LoRA.”*  Trivial to implement: two parameter groups in your optimiser.

### 11.3 LoftQ — LoRA-Fine-Tuning-Aware Quantization

(Li et al., 2023, arXiv:2310.08659, ICLR 2024; Microsoft Research)

In QLoRA, the base is quantised first and the LoRA adapter is initialised to zero — so at initialisation the model is the *quantized* base, which has noticeable error in the low-bit regime.  LoftQ instead alternates a few steps between quantising $W_0$ and using SVD of $(W_0 - \hat W_0)$ to pick a non-zero LoRA initialisation that *compensates* for the quantization error. Result: better initial perplexity and consistently better downstream performance, especially at 2- and 3-bit precision where QLoRA degrades sharply. Supported by HuggingFace PEFT.

### 11.4 VeRA — Vector-Based Random Matrix Adaptation

(Kopiczko, Blankevoort, Asano, 2024, arXiv:2310.11454, ICLR 2024)

VeRA freezes a *single pair* of random low-rank matrices $A, B$ shared across all layers and learns only two small *scaling vectors* $b \in \mathbb{R}^d$ and $d \in \mathbb{R}^r$ per layer that elementwise modulate them:
$$\Delta W_\ell = \Lambda_b^{(\ell)} B \Lambda_d^{(\ell)} A.$$
Because $A, B$ are frozen and shared, you only store the per-layer vectors plus a single random seed. On GLUE and E2E, parameter count drops 10× below LoRA while matching its performance.  On LLaMA-13B MT-Bench instruction-following (Table 4 of the paper) the savings are even more extreme: *“VeRA closely matches the performance of LoRA on the instruction-following task, with 100× reduction in trainable parameters.”* This makes VeRA extremely attractive when you want to serve thousands of specialised models.

### 11.5 AdaLoRA — Adaptive Rank Allocation

(Zhang et al., 2023, arXiv:2303.10512)

AdaLoRA parameterises $\Delta W = P \Lambda Q$ as an SVD-like factorisation (with $P, Q$ orthogonality-regularised and $\Lambda$ diagonal), then *prunes the smallest singular values* during training based on an importance score, effectively reallocating rank from less-important layers (early layers, attention) to more-important ones (later layers, FFN). The result is a non-uniform per-layer rank distribution at the same total parameter budget. Their Figure 3 (DeBERTa-v3-base on MNLI) shows AdaLoRA preferring to allocate more rank to top-layer FFNs.

### 11.6 LoRA-FA — Frozen $A$

(Zhang et al., 2023, arXiv:2308.03303)

Insight: $A$ is essentially a random projection-down; you can freeze it and only train  $B$, halving the trainable parameter count and — more importantly — reducing the *activation memory* (since you only need to store the $r$-dimensional output of $Ax$ for backprop, not the full $x$). Reported memory savings of $\sim 1.4\times$ on top of LoRA,  with similar quality.

### 11.7 rsLoRA — Rank-Stabilized Scaling

(Kalajdzievski, 2023, arXiv:2312.03732)

As mentioned in §3.3: replace $\alpha/r$ scaling with $\alpha/\sqrt{r}$. The paper proves that this is the unique scaling that keeps activations and gradients $O(1)$ as $r \to \infty$. Consequence: ranks of 64, 128, 256, even 2048 actually help, instead of saturating. Enable via `use_rslora=True`  in `LoraConfig`.

### 11.8 PiSSA — Principal Singular Values and Vectors Adaptation

(Meng, Wang, Zhang, 2024, arXiv:2404.02948, NeurIPS 2024 Spotlight)

PiSSA changes only the *initialisation*: factor $W_0 = U \Sigma V^\top$ via SVD, then set
$$A_0 = \Sigma_r^{1/2} V_r^\top,\quad B_0 = U_r \Sigma_r^{1/2},\quad W_0^{\text{res}} = W_0 - B_0 A_0.$$
Train $A, B$ as in LoRA, but $W^{\text{res}}$ (frozen) is the *small singular values* of $W_0$. Intuition: instead of training the “noise” while freezing the signal (as standard LoRA does, by freezing $W_0$ and initialising $BA = 0$), PiSSA trains the *principal components* and freezes the noise. Verbatim from the abstract: *“On GSM8K, Mistral-7B fine-tuned with PiSSA achieves an accuracy of 72.86%, outperforming LoRA’s 67.7% by 5.16%.”* The same paper reports that PiSSA *“reduces the 4-bit quantization error in LLaMA 2-7B by 18.97%, resulting in a substantial improvement in fine-tuning performance.”*

### 11.9 GaLore — Gradient Low-Rank Projection

(Zhao, Zhang, Chen, Wang, Anandkumar, Tian, 2024, arXiv:2403.03507, ICML 2024)

GaLore is *not* a PEFT method — it trains all parameters — but uses the same low-rank intuition for the *gradients*. At each step, project the full gradient $G$ into a low-rank subspace, run Adam in that subspace, and project back. Quoting the abstract: *“Our approach reduces memory usage by up to 65.5% in optimizer states while maintaining both efficiency and performance for pre-training on LLaMA 1B and 7B architectures … Our 8-bit GaLore further reduces optimizer memory by up to 82.5% and total training memory by 63.3%, compared to a BF16 baseline. Notably, we demonstrate, for the first time, the feasibility of pre-training a 7B model on consumer GPUs with 24GB memory (e.g., NVIDIA RTX 4090) without model parallel, checkpointing, or offloading strategies.”* Useful when you want full-parameter training but on a budget.

### 11.10 Benchmarks and SOTA, mid-2025

The empirical picture has stabilised. On standard instruction-tuning benchmarks (MT-Bench, MMLU, GSM8K) the rough pecking order, for 7B–13B models, is:

1. **Full fine-tuning** (gold standard, but ~10× the memory).
2. **DoRA** or **LoRA at high rank with all-linear targeting** and rsLoRA scaling (typically within 1–2 points of full FT).
3. **PiSSA** (similar to high-rank LoRA, faster convergence).
4. **Standard LoRA** at $r=16$ on attention-only (~3–10 points behind FT on hard tasks; comparable on easy ones).
5. **VeRA** (slightly behind LoRA but with 10–100× fewer parameters; great for multi-tenant serving).

Nothing in 2024–2025 has dethroned the LoRA-family for parameter-efficient fine-tuning. The exciting directions are *initialization* (PiSSA, LoRA-One, EVA) and *combination with quantization* (QLoRA, LoftQ, QDoRA). Note that **QDoRA**, combining DoRA with 4-bit quantization, is supported in Answer.AI’s FSDP-QDoRA recipe (Turgutlu, Whitaker, Howard, 2024) and is rapidly becoming the modern QLoRA replacement.

-----

## 12. Connecting to Broader Themes

### 12.1 LoRA as Compression

LoRA is, fundamentally, a compression statement about *the difference between pretraining and a task*. The pretrained model is large because language is large; the task-specific delta is small because the task is small. Once you accept this view, many extensions become natural: quantise the (large, frozen) base aggressively, compress the (small, trained) delta only mildly. QLoRA is just this principle pushed to 4 bits.

This pattern is repeating in adjacent fields. Diffusion models, vision transformers, and speech models all have the same fine-tuning cost problem, and all have adopted LoRA-style adapters. Simo Ryu’s `cloneofsimo/lora` repository (December 2022) was the first to apply LoRA to Stable Diffusion’s cross-attention layers. The HuggingFace `diffusers` blog post (Cuenca & Paul, 26 January 2023) describes the integration verbatim: *“In the case of Stable Diffusion fine-tuning, LoRA can be applied to the cross-attention layers that relate the image representations with the prompts that describe them.”* The same post quantifies the storage gains: *“we can save the weights for the new layers as a single file that weighs in at ~3 MB in size. This is about one thousand times smaller than the original size of the UNet model.”* In community practice, ranks of 4–32 are typical, with file sizes ranging from ~3 MB (UNet only, low rank) to ~200 MB (UNet + text encoder, rank 32).

### 12.2 Democratisation

QLoRA’s signal contribution is sociological as much as technical. Before mid-2023, fine-tuning a 30B+ model required institutional GPU access. After QLoRA, hobbyists with a single consumer RTX 3090 or 4090 (24 GB) can fine-tune 33B models in their bedroom. The cultural consequence is visible at scale: in 2025, the RunPod × Civitai industrial case study quotes a Civitai engineer reporting *“Last month alone, we trained 868,069 unique LoRAs on your platform,”* alongside 50 million monthly image generations on Civitai. This is several orders of magnitude more fine-tuning runs per month than the entire pre-LoRA research community had ever produced. Two and a half years later this has produced an entire ecosystem: HuggingFace’s PEFT and TRL libraries, Unsloth (which JIT-compiles LoRA kernels for ~2× speedup), Axolotl (a fine-tuning recipe wrapper), and dozens of community models in the 7–13B range. The marginal cost of a domain-specific LLM is now closer to the cost of curating the dataset than the cost of compute.

### 12.3 Multi-Tenant Serving: S-LoRA

(Sheng et al., 2023, arXiv:2311.03285)

Once you have a base model and many small LoRA adapters, the natural serving question is: can a single GPU serve many customers, each with their own adapter, in batches? S-LoRA shows the answer is yes. They use a **unified paged memory pool** (similar to vLLM’s paged KV cache) to manage adapter weights of different ranks alongside the KV cache, custom CUDA kernels (the heterogeneous batched grouped matrix-vector multiply, or **HBGMV**) for the LoRA branch, and adapter clustering to maximise batching. Verbatim from the S-LoRA abstract: *“Compared to state-of-the-art libraries such as HuggingFace PEFT and vLLM (with naive support of LoRA serving), S-LoRA can improve the throughput by up to 4 times and increase the number of served adapters by several orders of magnitude.”* In their experiments, throughput is roughly constant once the served adapter count exceeds ~100, whereas baseline systems run out of memory above a handful of adapters.

This is what makes “your own GPT” plausible at scale: ChatGPT-style personalisation can be implemented as one base model plus a per-user 80 MB LoRA. Punica (Chen et al., 2023) and CaraServe make similar points with similar mechanisms.

### 12.4 LoRA in Non-NLP Contexts

- **Diffusion models**: ubiquitous. Both Stable Diffusion (UNet cross-attention) and DiT-style models (transformer all-attention) use LoRA, often with very low rank ($r=4$ to $r=32$). The HF `diffusers` library supports adapter loading via `pipe.load_lora_weights("path-or-hub-id")`.
- **Vision Transformers**: ViT-LoRA and similar variants apply LoRA to ViT attention; useful for low-data fine-tuning of CLIP, SAM, and similar.
- **Speech**: Whisper-LoRA is widely used for speech-to-text domain adaptation.
- **Multimodal**: VL-BART, LLaVA, and similar models use LoRA on top of frozen vision encoders for parameter-efficient multimodal fine-tuning. The DoRA paper specifically evaluates on visual instruction tuning (LLaVA) and image/video-text understanding (VL-BART).

### 12.5 Final Synthesis

LoRA and QLoRA represent the empirical fact that **almost all of a neural network is general, and adaptation is local**. This fact — and the linear-algebraic tools that make it operational — has reshaped how we train and serve LLMs. As models grow, the *ratio* of adaptation cost to pretraining cost will continue to shrink, and PEFT methods will become more rather than less essential. The next frontier, visible in 2025, is the combination of LoRA-style adapters with *quantization-aware training* (LoftQ, QDoRA) and with *serving systems* (S-LoRA, Punica), so that the entire stack — train, store, deploy — is sub-percent of the cost of full fine-tuning while sacrificing essentially none of the accuracy. For a graduate student entering the field, LoRA and QLoRA are no longer optional knowledge: they are the basic alphabet in which modern LLM customisation is written.

-----

*End of chapter.*