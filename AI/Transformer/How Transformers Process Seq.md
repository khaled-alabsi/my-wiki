# How Transformers Process Sequences — From Input Vectors to Predictions

## The Core Question

When multiple token vectors are fed into a neural network, what actually happens to them? The classical mental model — “neural networks take 1D input” — leads to the natural assumption that the vectors must be flattened or concatenated into one long vector before processing. For transformers, this assumption is wrong, and unpacking why reveals most of the architecture’s design.

## Tokens as a Matrix, Not a Flattened Vector

A classical MLP expects a 1D vector of fixed size. If we tried to apply that model to a sequence of token embeddings, we would have to flatten them: three vectors of size 4 would become one vector of size 12. This kills variable sequence length and forces position 1 to mean something different from position 2 *in the weights themselves*.

Transformers do not flatten. The input stays as a 2D matrix of shape `(seq_len, d_model)` and keeps this shape throughout the entire stack of layers.

A concrete example with three tokens and `d_model = 4`:

```
Input tokens:  ["the", "cat", "sat"]
Embeddings:    shape (3, 4)
               [[0.1, 0.2, 0.3, 0.4],   "the"
                [0.5, 0.1, 0.9, 0.2],   "cat"
                [0.3, 0.7, 0.1, 0.8]]   "sat"
```

This matrix `X` is what flows through every transformer block. Three tokens go in, three tokens come out — never one flattened vector of size 12.

## The Two Sublayers: Attention vs. FFN

Each transformer block contains two sublayers, and they handle the 2D matrix in different ways.

### Attention operates on the full matrix

Attention is just matrix multiplication. `X @ W_q` where `X` is `(3, 4)` and `W_q` is `(4, 4)` gives `(3, 4)`. The same for `W_k` and `W_v`. Linear algebra handles 2D inputs natively — no flattening required. Attention is also the only sublayer where information moves *across tokens*.

### The FFN is 1D — but applied per token

This is where the “1D input” intuition resurfaces, correctly. The MLP inside a transformer block does expect a 1D vector of size `d_model`. But instead of flattening the whole sequence, the model feeds it **each row separately**, using the **same weights** for every row:

```
Token "the"  → [0.1, 0.2, 0.3, 0.4] → MLP → [..., ..., ..., ...]
Token "cat"  → [0.5, 0.1, 0.9, 0.2] → MLP → [..., ..., ..., ...]
Token "sat"  → [0.3, 0.7, 0.1, 0.8] → MLP → [..., ..., ..., ...]
```

Three independent forward passes through the same MLP, outputs stacked back into a `(3, 4)` matrix. This is sometimes called a **position-wise feed-forward network** for exactly this reason.

The model never sees “3 tokens at once” as a single 12-dim vector. Attention sees the whole sequence as a 2D matrix (which is fine, because matmul); the FFN sees one token at a time (which is fine, because attention already did the cross-token work).

## Every Position Produces an Output

Three input vectors produce three output vectors. Always. No position is ever dropped during the forward pass.

```
Input:   ["the",  "cat",  "sat"]
                  ↓
Output:  [ h_1,    h_2,    h_3 ]    shape (seq_len, d_model)
```

The crucial point: by the time a token reaches the FFN, it is no longer “just itself.” Before attention, the row for `"sat"` is just the embedding of the word “sat.” After attention, that row has absorbed weighted information from `"the"` and `"cat"`. The FFN therefore does not need positional awareness — attention is the communication channel between tokens, and the FFN is just per-token refinement.

Each `h_i` is the model’s contextualized representation of position `i`, used to predict the token that comes *after* position `i`:

```
h_1 (from "the")  → predicts token after "the"   → ideally "cat"
h_2 (from "cat")  → predicts token after "cat"   → ideally "sat"
h_3 (from "sat")  → predicts token after "sat"   → ideally "on"
```

Causal masking exists so that when computing `h_2`, attention is only allowed to look at positions 1 and 2 — not position 3 — otherwise the model would trivially cheat during training.

## Training vs. Inference

The fact that every position produces an output matters very differently in the two phases.

- **Training:** all outputs are used simultaneously. Each `h_i` is scored against the true next-token at position `i+1`. A single forward pass over a 500-token sequence produces 500 prediction errors at once — a much richer training signal than predicting only the last token.
- **Inference (autoregressive generation):** only the last output `h_N` is used to sample the next token. That token is appended to the input, the whole thing runs again, and the new last output is used. Earlier outputs `h_1, ..., h_{N-1}` are computed but discarded for the purpose of generation.

So when a user pastes a 500-token Python file and asks for an explanation, *all 500 tokens* go through attention and the FFN. The model just uses `h_500` to predict token 501.

## The Information Bottleneck Concern

A natural worry arises: if only `h_500` is used to predict the next token, must it not contain everything the model knows about the previous 499 tokens? And if `h_500` is a single vector of, say, 4096 floats, can it really hold that much information without losing some?

This concern is **correct for RNNs and wrong for transformers**, for a specific architectural reason.

### Why RNNs suffer

In an RNN, information flows sequentially through hidden states:

```
h_1 → h_2 → h_3 → ... → h_500
```

For token 1 to influence `h_500`, its information must survive 499 sequential hops. Each hop is a lossy transformation. This is the classical bottleneck that motivated attention in the first place.

### Why transformers escape it

In a transformer, `h_500` is computed by attention as:

```
h_500 = α_1·v_1 + α_2·v_2 + α_3·v_3 + ... + α_500·v_500
```

where `v_i` is the value vector of token `i` and `α_i` is the attention weight. `h_500` looks at **all 500 tokens directly, in parallel, in one step**. The path length from any token to `h_500` is **1**, not 499. There is no sequential squeezing.

## The Order-Invariance Problem

A sharp follow-up: summation is commutative. `4 + 1 + 2 = 1 + 4 + 2`. If `h_500` is just a weighted sum of value vectors, then `"dog bites man"` and `"man bites dog"` would seem to produce identical outputs. Without a fix, transformers would collapse into a **bag-of-words** model.

The fix is not in the operation but in **what gets summed**. Position information is baked into the vectors themselves before attention is applied:

```
v_i = (token_embedding_i + positional_encoding_i) · W_v
```

The same word at different positions produces different `v_i` vectors:

```
"the" at position 1:  embedding("the") + PE(1)
"the" at position 5:  embedding("the") + PE(5)
```

The keys `k_i` work the same way, so the attention weights `α_i = softmax(q · k_i)` are also position-aware.

Swapping `"dog"` and `"man"` in `"dog bites man"` does not just reorder a sum — it changes **what `v_1` and `v_2` actually are**, because the positional encodings stay tied to their slots. Order is preserved not in *how* values are combined, but in *what* is combined.

## The Real Limits: Lossy Compression

Even with positional encodings, the concern about a single vector holding 500 tokens’ worth of information is partially valid. A `d_model`-sized vector has finite capacity. Two things prevent this from being catastrophic in practice.

### h_N does not need to preserve everything

`h_N` is not trying to perfectly reconstruct 500 tokens. It only needs enough information to predict **one next token**. For a prompt like `"The capital of France is"`, the relevant context is mostly `"France"` and `"capital"`. The word `"the"` barely needs to survive. Attention is explicitly trained to discard irrelevant information — that is its job, not a defect.

So “information is lost” is not the same as “useful information is lost.”

### Previous K and V vectors are not discarded

This is the part that fully resolves the concern. When the 500 input tokens are processed, each position produces its own key and value vectors. All of them are kept in memory (the **KV cache**):

```
position 1:    k_1, v_1
position 2:    k_2, v_2
...
position 500:  k_500, v_500
```

When the model predicts token 501 using `h_500`, then needs to predict token 502, it does **not** build further on a lossy `h_500`. The new token runs attention against **all 500 original keys and values directly**. Information at position 1 has a path length of 1 to token 502 — not “through h_500.”

The bottleneck is therefore **per prediction**, not **per conversation**.

### Real-world limits

Per-vector capacity is still finite, and this has observable consequences:

- **“Lost in the middle”** — empirical studies show that models genuinely struggle to retrieve information from the middle of very long contexts.
- Practical context window limits exist for real reasons (compute, memory, and degradation of attention quality).
- Long-context handling is an active research area: longer windows, sparse attention variants, state-space models, and hybrid architectures.

## Summary: RNNs vs. Transformers

|Aspect                     |RNN                               |Transformer                                  |
|---------------------------|----------------------------------|---------------------------------------------|
|Information path length    |O(N) — sequential hops            |O(1) — direct attention                      |
|Cross-token mixing         |Hidden state passed step by step  |Attention reads full sequence in parallel    |
|Order handling             |Implicit in step ordering         |Explicit via positional encodings            |
|Per-token bottleneck       |Severe (forgetting over long seqs)|Limited by `d_model` capacity, not seq length|
|Access to past tokens later|Compressed in current hidden state|Direct via KV cache                          |

The intuition that “stuffing many tokens into one vector seems lossy” is correct and historically important — it is precisely the intuition that drove the move from RNNs to attention-based models. Transformers do not eliminate the bottleneck entirely; they reduce it from a sequential one (forgetting across hops) to a per-vector one (finite capacity per prediction), and they keep the past directly addressable via the KV cache rather than relying on a single compressed state.