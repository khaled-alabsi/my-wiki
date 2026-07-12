# Transformer Matrix Shapes From Input Text to Output

## Table of Contents

- [[#Starting Example|Starting Example]]
- [[#Core Idea|Core Idea]]
- [[#Step 0 Text and Tokens|Step 0 Text and Tokens]]
- [[#Step 1 Token IDs|Step 1 Token IDs]]
- [[#Step 2 Embedding Lookup|Step 2 Embedding Lookup]]
- [[#Step 3 The Input Matrix Before the Neural Network|Step 3 The Input Matrix Before the Neural Network]]
- [[#Step 4 How a Neural Network Layer Receives the Matrix|Step 4 How a Neural Network Layer Receives the Matrix]]
- [[#Step 5 Transformer Block Overview|Step 5 Transformer Block Overview]]
- [[#Step 6 Attention Creates Q K V|Step 6 Attention Creates Q K V]]
- [[#Step 7 Attention Scores|Step 7 Attention Scores]]
- [[#Step 8 Attention Weights Multiply V|Step 8 Attention Weights Multiply V]]
- [[#Step 9 MLP Feed Forward Network|Step 9 MLP Feed Forward Network]]
- [[#Step 10 Final Output Logits|Step 10 Final Output Logits]]
- [[#Full Shape Summary|Full Shape Summary]]
- [[#Key Takeaways|Key Takeaways]]

---

## Starting Example

Use this sentence:

```text
"I hate apple"
```

Assume the tokenizer splits it into three tokens:

```text
["I", "hate", "apple"]
```

So the sequence has three tokens:

```text
T = 3
```

For a tiny example, assume each token embedding has four numbers:

```text
d_model = 4
```

In real models, `d_model` is much larger, for example 768, 2048, 4096, or more.

---

## Core Idea

A Transformer does not process raw words directly.

It first converts tokens into vectors.

For one sequence, the main input matrix has this shape:

```text
X: [T x d_model]
```

Meaning:

```text
T       = number of tokens
d_model = number of numbers per token vector
```

For the example:

```text
X: [3 x 4]
```

Because:

```text
3 tokens
4 numbers per token
```

The matrix looks like this:

```text
X = one sequence after embedding

          d1    d2    d3    d4
        ┌                         ┐
I       │ 0.2   0.1  -0.4   0.7   │
hate    │ 0.0  -0.3   0.8   0.1   │
apple   │ 0.5   0.2   0.1  -0.6   │
        └                         ┘

Shape: [3 x 4]
```

Important:

```text
Each row = one token vector
Each column = one coordinate inside the token vector
```

The columns are not usually human-interpretable tabular features. The full row is the meaningful token representation.

---

## Step 0 Text and Tokens

Start with text:

```text
"I hate apple"
```

Tokenizer output:

```text
["I", "hate", "apple"]
```

This is one sequence.

```text
Sequence = ordered list of tokens
```

So:

```text
T = 3
```

The sequence is not one token.

The sequence is the full ordered list:

```text
["I", "hate", "apple"]
```

The tokens are the individual items:

```text
Token 1 = "I"
Token 2 = "hate"
Token 3 = "apple"
```

---

## Step 1 Token IDs

The tokenizer maps each token to an integer ID.

Example:

```text
"I"     -> 40
"hate"  -> 9182
"apple" -> 12345
```

So the token ID input is:

```text
[40, 9182, 12345]
```

Shape:

```text
[3]
```

Because there are three tokens.

With batch size included, the shape would be:

```text
[B, T]
```

For one sentence:

```text
B = 1
T = 3
```

So:

```text
[1, 3]
```

But to keep the explanation simple, we ignore batch for now.

---

## Step 2 Embedding Lookup

The embedding table is part of the model.

It contains one learned vector for each token in the vocabulary.

Example:

```text
vocab_size = 50000
d_model    = 4
```

Embedding table shape:

```text
[vocab_size x d_model] = [50000 x 4]
```

The token IDs select rows from this embedding table.

```text
ID 40     -> [0.2,  0.1, -0.4,  0.7]
ID 9182   -> [0.0, -0.3,  0.8,  0.1]
ID 12345  -> [0.5,  0.2,  0.1, -0.6]
```

Stacked together:

```text
X

          d1    d2    d3    d4
        ┌                         ┐
I       │ 0.2   0.1  -0.4   0.7   │
hate    │ 0.0  -0.3   0.8   0.1   │
apple   │ 0.5   0.2   0.1  -0.6   │
        └                         ┘

Shape: [3 x 4]
```

So:

```text
Token IDs: [3]
Embedding output: [3 x 4]
```

General form:

```text
[T] -> [T x d_model]
```

---

## Step 3 The Input Matrix Before the Neural Network

Before entering a Transformer block, the model has a matrix:

```text
X: [T x d_model]
```

In the example:

```text
X: [3 x 4]
```

ASCII view:

```text
          token vector size = 4
        ┌─────────────────────┐
I       │ 0.2  0.1 -0.4  0.7  │
hate    │ 0.0 -0.3  0.8  0.1  │
apple   │ 0.5  0.2  0.1 -0.6  │
        └─────────────────────┘

Shape: [3 x 4]
```

This means:

```text
3 token vectors
each vector has 4 numbers
```

---

## Step 4 How a Neural Network Layer Receives the Matrix

A basic neural network layer conceptually receives one 1D vector at a time.

So for this matrix:

```text
X: [3 x 4]
```

The layer conceptually processes each row:

```text
I row     [0.2,  0.1, -0.4,  0.7]  -> NN layer
hate row  [0.0, -0.3,  0.8,  0.1]  -> same NN layer
apple row [0.5,  0.2,  0.1, -0.6]  -> same NN layer
```

ASCII diagram:

```text
Input matrix X

          4 numbers per token
        ┌─────────────────────┐
I       │ 0.2  0.1 -0.4  0.7  │  ──┐
hate    │ 0.0 -0.3  0.8  0.1  │  ──┼── fed row-by-row to the SAME layer
apple   │ 0.5  0.2  0.1 -0.6  │  ──┘
        └─────────────────────┘
```

If the layer maps from 4 numbers to 6 numbers:

```text
input_dim = 4
output_dim = 6
```

Then:

```text
I     [1 x 4] -> NN layer -> [1 x 6]
hate  [1 x 4] -> NN layer -> [1 x 6]
apple [1 x 4] -> NN layer -> [1 x 6]
```

Matrix shorthand:

```text
X [3 x 4]  x  W [4 x 6]  =  Y [3 x 6]
```

This is vectorized processing.

It does not mean the NN treats the whole matrix as one flat input.

It means:

```text
same layer
applied to each token row
all rows processed in parallel
```

---

## Step 5 Transformer Block Overview

A Transformer block mostly keeps the same outer shape:

```text
[T x d_model] -> [T x d_model]
```

For the example:

```text
[3 x 4] -> [3 x 4]
```

Inside the block, there are two main parts:

```text
1. Self-attention
2. MLP / feed-forward network
```

Block overview:

```text
X [3 x 4]
  |
  v
Self-attention
  |
  v
[3 x 4]
  |
  v
MLP / feed-forward
  |
  v
[3 x 4]
```

The Transformer block changes the values, but usually preserves the shape.

---

## Step 6 Attention Creates Q K V

Self-attention creates three matrices from X:

```text
Q = query
K = key
V = value
```

They are created using learned weight matrices:

```text
Q = X W_Q
K = X W_K
V = X W_V
```

Input:

```text
X: [3 x 4]
```

Weights:

```text
W_Q: [4 x 4]
W_K: [4 x 4]
W_V: [4 x 4]
```

Outputs:

```text
Q: [3 x 4]
K: [3 x 4]
V: [3 x 4]
```

Shape calculation:

```text
X [3 x 4] x W_Q [4 x 4] = Q [3 x 4]
X [3 x 4] x W_K [4 x 4] = K [3 x 4]
X [3 x 4] x W_V [4 x 4] = V [3 x 4]
```

Conceptually:

```text
Each token row gets transformed into:
- a query vector
- a key vector
- a value vector
```

So:

```text
I     row -> q_I, k_I, v_I
hate  row -> q_hate, k_hate, v_hate
apple row -> q_apple, k_apple, v_apple
```

---

## Step 7 Attention Scores

Attention asks:

```text
How much should each token look at each other token?
```

This is done by multiplying Q with K transposed.

```text
Q:   [3 x 4]
K^T: [4 x 3]

QK^T: [3 x 3]
```

Shape:

```text
[3 x 4] x [4 x 3] = [3 x 3]
```

The result is an attention score matrix:

```text
Attention scores

             I     hate   apple
          ┌                      ┐
I         │  s11   s12    s13    │
hate      │  s21   s22    s23    │
apple     │  s31   s32    s33    │
          └                      ┘

Shape: [3 x 3]
```

Rows mean:

```text
Which token is looking?
```

Columns mean:

```text
Which token is being looked at?
```

Example:

```text
row "hate", column "apple"
```

means:

```text
How much "hate" attends to "apple"
```

In decoder-only models, a causal mask is applied so future tokens cannot be seen.

For the sequence:

```text
[I, hate, apple]
```

causal attention allows:

```text
I     can see: I
hate  can see: I, hate
apple can see: I, hate, apple
```

The masked score matrix still has shape:

```text
[3 x 3]
```

---

## Step 8 Attention Weights Multiply V

After the score matrix, softmax is applied.

```text
scores [3 x 3] -> attention weights [3 x 3]
```

Then the attention weights multiply V:

```text
attention weights: [3 x 3]
V:                 [3 x 4]

output:            [3 x 4]
```

Shape calculation:

```text
[3 x 3] x [3 x 4] = [3 x 4]
```

This gives one new vector per token.

```text
Attention output

          d1    d2    d3    d4
        ┌                         ┐
I       │ ...   ...   ...   ...   │
hate    │ ...   ...   ...   ...   │
apple   │ ...   ...   ...   ...   │
        └                         ┘

Shape: [3 x 4]
```

This is the first important row-mixing step.

Before attention, each row is transformed separately by linear layers.

During attention, rows can mix information from other rows.

---

## Step 9 MLP Feed Forward Network

After attention, the Transformer applies an MLP to each row.

Input:

```text
[3 x 4]
```

Usually the MLP expands the vector size, then contracts it back.

For this tiny example:

```text
d_model = 4
d_ff = 16
```

The MLP has two main weight matrices:

```text
W_1: [4 x 16]
W_2: [16 x 4]
```

Flow:

```text
X [3 x 4]
  |
  | x W_1 [4 x 16]
  v
[3 x 16]
  |
  | activation
  v
[3 x 16]
  |
  | x W_2 [16 x 4]
  v
[3 x 4]
```

So:

```text
[3 x 4] -> [3 x 16] -> [3 x 4]
```

The MLP is also applied row-by-row.

ASCII:

```text
I     [4 numbers] -> MLP -> [4 numbers]
hate  [4 numbers] -> MLP -> [4 numbers]
apple [4 numbers] -> MLP -> [4 numbers]
```

But internally:

```text
[4] -> [16] -> [4]
```

The Transformer uses matrix multiplication to process all rows at once:

```text
[3 x 4] -> [3 x 16] -> [3 x 4]
```

---

## Step 10 Final Output Logits

After many Transformer blocks, the model still has:

```text
[3 x 4]
```

In real models:

```text
[T x d_model]
```

Then the model projects each token vector to vocabulary size.

Assume:

```text
vocab_size = 50000
d_model = 4
```

Output projection weight:

```text
W_vocab: [4 x 50000]
```

Final logits:

```text
X [3 x 4] x W_vocab [4 x 50000] = logits [3 x 50000]
```

So each token position gets a score for every token in the vocabulary.

```text
logits: [T x vocab_size]
```

For the example:

```text
logits: [3 x 50000]
```

Meaning:

```text
Position 1 -> scores for all possible next tokens
Position 2 -> scores for all possible next tokens
Position 3 -> scores for all possible next tokens
```

For next-token prediction, usually the final row is used to predict the next token after the input.

For:

```text
"I hate apple"
```

the last row predicts what comes after `"apple"`.

---

## Full Shape Summary

Using:

```text
Sentence: "I hate apple"
T = 3
d_model = 4
d_ff = 16
vocab_size = 50000
```

The shape flow is:

```text
1. Text
   "I hate apple"

2. Tokens
   ["I", "hate", "apple"]

3. Token IDs
   [3]

4. Embedding lookup
   [3] -> [3 x 4]

5. Add positional embedding
   [3 x 4] -> [3 x 4]

6. Create Q, K, V
   X [3 x 4]

   W_Q [4 x 4] -> Q [3 x 4]
   W_K [4 x 4] -> K [3 x 4]
   W_V [4 x 4] -> V [3 x 4]

7. Attention scores
   Q [3 x 4] x K^T [4 x 3] = [3 x 3]

8. Softmax
   [3 x 3] -> [3 x 3]

9. Weighted sum of V
   [3 x 3] x [3 x 4] = [3 x 4]

10. Output projection
   [3 x 4] -> [3 x 4]

11. MLP
   [3 x 4] -> [3 x 16] -> [3 x 4]

12. Transformer block output
   [3 x 4]

13. Repeat many blocks
   [3 x 4] -> [3 x 4] -> [3 x 4]

14. Vocabulary projection
   [3 x 4] -> [3 x 50000]
```

General version:

```text
Token IDs:
[T]

Embeddings:
[T x d_model]

Each Transformer block:
[T x d_model] -> [T x d_model]

Final logits:
[T x vocab_size]
```

With batch:

```text
Token IDs:
[B x T]

Embeddings:
[B x T x d_model]

Each Transformer block:
[B x T x d_model] -> [B x T x d_model]

Final logits:
[B x T x vocab_size]
```

---

## Key Takeaways

```text
X is data.
W matrices are the model.
```

The input matrix:

```text
X: [T x d_model]
```

means:

```text
T rows = token vectors
d_model = vector size of each token
```

A normal NN layer conceptually takes one row at a time:

```text
one token vector -> layer -> one output vector
```

Matrix multiplication processes all rows in parallel:

```text
X [T x d_model] x W [d_model x d_out] = Y [T x d_out]
```

Attention is special because it mixes rows:

```text
QK^T -> [T x T]
```

That matrix tells how tokens relate to other tokens.

The Transformer block usually preserves the main shape:

```text
[T x d_model] -> [T x d_model]
```

The final output changes to vocabulary size:

```text
[T x d_model] -> [T x vocab_size]
```
