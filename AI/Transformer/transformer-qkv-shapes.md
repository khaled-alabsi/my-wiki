# Transformer Q, K, V Shapes

## Table of Contents

- [[#Core Symbols|Core Symbols]]
- [[#Single Token Shapes|Single Token Shapes]]
- [[#Projection Matrices|Projection Matrices]]
- [[#Why Q and K Have the Same Shape|Why Q and K Have the Same Shape]]
- [[#Full Sequence Shapes|Full Sequence Shapes]]
- [[#Attention Score Matrix|Attention Score Matrix]]
- [[#Attention Output|Attention Output]]
- [[#Multi-Head Attention|Multi-Head Attention]]
- [[#Shape Summary|Shape Summary]]

## Core Symbols

![[Pasted image 20260620165643.png]]

In the original Transformer paper, *Attention Is All You Need*, the model uses these dimensions:

$$
d_{\text{model}} = 512
$$

$$
d_k = 64
$$

$$
d_v = 64
$$

Here:

- $d_{\text{model}}$ is the size of the main token embedding.
- $d_k$ is the size of the query and key vectors.
- $d_v$ is the size of the value vectors.

The table in the image describes the shapes of objects for one attention head.

## Single Token Shapes

For a single token at position $i$, the token representation is:

$$
x_i \in \mathbb{R}^{d_{\text{model}}}
$$

In the original Transformer:

$$
x_i \in \mathbb{R}^{512}
$$

So each token starts as a vector of length $512$.

The attention mechanism does not use $x_i$ directly. Instead, it creates three different vectors from it:

$$
q_i = x_i W^{(Q)}
$$

$$
k_i = x_i W^{(K)}
$$

$$
v_i = x_i W^{(V)}
$$

These are:

- $q_i$: the query vector.
- $k_i$: the key vector.
- $v_i$: the value vector.

The table says:

$$
q_i, k_i \in \mathbb{R}^{d_k}
$$

$$
v_i \in \mathbb{R}^{d_v}
$$

With the original Transformer dimensions:

$$
q_i, k_i \in \mathbb{R}^{64}
$$

$$
v_i \in \mathbb{R}^{64}
$$

So, for one token:

$$
x_i: 512
$$

$$
q_i: 64
$$

$$
k_i: 64
$$

$$
v_i: 64
$$

## Projection Matrices

The projection matrices transform the token vector from the model space into query, key, and value spaces.

The table says:

$$
W^{(Q)}, W^{(K)} \in \mathbb{R}^{d_{\text{model}} \times d_k}
$$

and:

$$
W^{(V)} \in \mathbb{R}^{d_{\text{model}} \times d_v}
$$

Using the original Transformer dimensions:

$$
W^{(Q)} \in \mathbb{R}^{512 \times 64}
$$

$$
W^{(K)} \in \mathbb{R}^{512 \times 64}
$$

$$
W^{(V)} \in \mathbb{R}^{512 \times 64}
$$

The multiplication works like this:

$$
q_i = x_i W^{(Q)}
$$

Shape-wise:

$$
(1 \times 512)(512 \times 64) = (1 \times 64)
$$

So:

$$
q_i \in \mathbb{R}^{64}
$$

Similarly:

$$
k_i = x_i W^{(K)}
$$

$$
(1 \times 512)(512 \times 64) = (1 \times 64)
$$

So:

$$
k_i \in \mathbb{R}^{64}
$$

And:

$$
v_i = x_i W^{(V)}
$$

$$
(1 \times 512)(512 \times 64) = (1 \times 64)
$$

So:

$$
v_i \in \mathbb{R}^{64}
$$

## Why Q and K Have the Same Shape

The query vector $q_i$ and key vector $k_j$ must have the same dimension because attention compares them using a dot product:

$$
q_i \cdot k_j
$$

A dot product requires both vectors to have the same length.

If:

$$
q_i \in \mathbb{R}^{64}
$$

and:

$$
k_j \in \mathbb{R}^{64}
$$

then:

$$
q_i \cdot k_j \rightarrow \text{scalar}
$$

That scalar is the attention score between token $i$ and token $j$.

The value vector $v_j$ does not need to be compared with the query. It is the information retrieved after the attention weights are computed. Therefore, $d_v$ does not theoretically need to equal $d_k$, although in the original Transformer both are $64$.

## Full Sequence Shapes

Now assume the sequence has length $n$.

Instead of one token vector $x_i$, we have a matrix of all token vectors:

$$
X \in \mathbb{R}^{n \times d_{\text{model}}}
$$

In the original Transformer:

$$
X \in \mathbb{R}^{n \times 512}
$$

Each row of $X$ is one token representation:

$$
X =
\begin{bmatrix}
--- x_1 --- \\
--- x_2 --- \\
\vdots \\
--- x_n ---
\end{bmatrix}
$$

Then the model computes:

$$
Q = XW^{(Q)}
$$

$$
K = XW^{(K)}
$$

$$
V = XW^{(V)}
$$

Shape-wise:

$$
XW^{(Q)} = (n \times 512)(512 \times 64) = n \times 64
$$

Therefore:

$$
Q \in \mathbb{R}^{n \times 64}
$$

Similarly:

$$
K \in \mathbb{R}^{n \times 64}
$$

$$
V \in \mathbb{R}^{n \times 64}
$$

More generally:

$$
Q \in \mathbb{R}^{n \times d_k}
$$

$$
K \in \mathbb{R}^{n \times d_k}
$$

$$
V \in \mathbb{R}^{n \times d_v}
$$

## Attention Score Matrix

Attention compares every query against every key.

The score matrix is computed as:

$$
QK^T
$$

The shapes are:

$$
Q \in \mathbb{R}^{n \times 64}
$$

$$
K^T \in \mathbb{R}^{64 \times n}
$$

Therefore:

$$
QK^T \in \mathbb{R}^{n \times n}
$$

So:

$$
(n \times 64)(64 \times n) = n \times n
$$

The result is an attention-score matrix:

$$
QK^T =
\begin{bmatrix}
q_1 \cdot k_1 & q_1 \cdot k_2 & \cdots & q_1 \cdot k_n \\
q_2 \cdot k_1 & q_2 \cdot k_2 & \cdots & q_2 \cdot k_n \\
\vdots & \vdots & \ddots & \vdots \\
q_n \cdot k_1 & q_n \cdot k_2 & \cdots & q_n \cdot k_n
\end{bmatrix}
$$

Each row corresponds to one query token.

Each column corresponds to one key token.

The entry at row $i$, column $j$ is:

$$
q_i \cdot k_j
$$

This means:

> How much should token $i$ attend to token $j$?

The scaled dot-product attention formula is:

$$
\operatorname{Attention}(Q, K, V)
=
\operatorname{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

The division by $\sqrt{d_k}$ stabilizes the dot-product magnitudes.

With $d_k = 64$:

$$
\sqrt{d_k} = \sqrt{64} = 8
$$

So the score matrix is scaled by $8$:

$$
\frac{QK^T}{8}
$$

## Attention Output

After computing the attention scores, the model applies softmax:

$$
A = \operatorname{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)
$$

The shape remains:

$$
A \in \mathbb{R}^{n \times n}
$$

Then the model multiplies the attention weights by the value matrix:

$$
AV
$$

Shape-wise:

$$
A \in \mathbb{R}^{n \times n}
$$

$$
V \in \mathbb{R}^{n \times 64}
$$

Therefore:

$$
AV \in \mathbb{R}^{n \times 64}
$$

So:

$$
(n \times n)(n \times 64) = n \times 64
$$

The output of one attention head is:

$$
\operatorname{head} \in \mathbb{R}^{n \times d_v}
$$

In the original Transformer:

$$
\operatorname{head} \in \mathbb{R}^{n \times 64}
$$

## Multi-Head Attention

The original Transformer uses $8$ attention heads.

Each head has:

$$
d_k = 64
$$

$$
d_v = 64
$$

Each head outputs:

$$
n \times 64
$$

With $8$ heads, we concatenate the outputs:

$$
\operatorname{Concat}(\text{head}_1, \ldots, \text{head}_8)
$$

Shape-wise:

$$
(n \times 64) \times 8 = n \times 512
$$

Because:

$$
8 \cdot 64 = 512
$$

So after concatenating all heads:

$$
\operatorname{Concat}(\text{heads}) \in \mathbb{R}^{n \times 512}
$$

Then the Transformer applies a final output projection:

$$
W^{(O)} \in \mathbb{R}^{512 \times 512}
$$

So:

$$
(n \times 512)(512 \times 512) = n \times 512
$$

The final multi-head attention output has the same shape as the original input:

$$
n \times d_{\text{model}}
$$

In the original Transformer:

$$
n \times 512
$$

This is important because the output can be added back to the original input through a residual connection.

## Shape Summary

For one token:

| Object | Shape | Original Transformer |
|---|---:|---:|
| $x_i$ | $d_{\text{model}}$ | $512$ |
| $q_i$ | $d_k$ | $64$ |
| $k_i$ | $d_k$ | $64$ |
| $v_i$ | $d_v$ | $64$ |
| $W^{(Q)}$ | $d_{\text{model}} \times d_k$ | $512 \times 64$ |
| $W^{(K)}$ | $d_{\text{model}} \times d_k$ | $512 \times 64$ |
| $W^{(V)}$ | $d_{\text{model}} \times d_v$ | $512 \times 64$ |

For a sequence of length $n$:

| Object | Shape | Original Transformer |
|---|---:|---:|
| $X$ | $n \times d_{\text{model}}$ | $n \times 512$ |
| $Q$ | $n \times d_k$ | $n \times 64$ |
| $K$ | $n \times d_k$ | $n \times 64$ |
| $V$ | $n \times d_v$ | $n \times 64$ |
| $QK^T$ | $n \times n$ | $n \times n$ |
| $\operatorname{softmax}(QK^T / \sqrt{d_k})$ | $n \times n$ | $n \times n$ |
| One head output | $n \times d_v$ | $n \times 64$ |
| $8$ concatenated heads | $n \times (8 \cdot 64)$ | $n \times 512$ |
| Final MHA output | $n \times d_{\text{model}}$ | $n \times 512$ |

The key idea is:

$$
X: n \times 512
$$

projects into:

$$
Q, K, V: n \times 64
$$

for each head.

Then:

$$
QK^T: n \times n
$$

creates the attention weights, and:

$$
\operatorname{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V: n \times 64
$$

creates the output of one head.

With $8$ heads:

$$
8 \cdot 64 = 512
$$

so the concatenated result returns to the model dimension:

$$
n \times 512
$$

## Question: Why does attention output a matrix instead of one scalar score?

I expected the output of the query-key comparison to be a **scalar** similarity score.

For one query vector and one key vector, this is true:

$q_i \cdot k_j = \text{one scalar similarity score}$

This scalar tells us how similar one query is to one key:

$q_i \cdot k_j = \text{similarity between token } i \text{ and token } j$

So why does the Transformer compute:

$QK^T$

and get a matrix of shape:

$T \times T$

instead of one scalar?

## Answer

The key point is that **one query compared with one key gives one scalar**, but the Transformer does this comparison for **all query-key pairs at once**.

For one pair:

$q_i \cdot k_j = \text{scalar}$

But for a sequence of length $T$, we have $T$ query vectors and $T$ key vectors:

$Q \in \mathbb{R}^{T \times d_k}$

$K \in \mathbb{R}^{T \times d_k}$

Each row of $Q$ is one query vector:

$q_1, q_2, \dots, q_T$

Each row of $K$ is one key vector:

$k_1, k_2, \dots, k_T$

The Transformer wants to compute every possible query-key similarity:

$q_1 \cdot k_1,\ q_1 \cdot k_2,\ \dots,\ q_1 \cdot k_T$

$q_2 \cdot k_1,\ q_2 \cdot k_2,\ \dots,\ q_2 \cdot k_T$

$\dots$

$q_T \cdot k_1,\ q_T \cdot k_2,\ \dots,\ q_T \cdot k_T$

All of these are scalar scores, but they are arranged into a matrix:

$$
QK^T =
\begin{bmatrix}
q_1 \cdot k_1 & q_1 \cdot k_2 & \cdots & q_1 \cdot k_T \\
q_2 \cdot k_1 & q_2 \cdot k_2 & \cdots & q_2 \cdot k_T \\
\vdots & \vdots & \ddots & \vdots \\
q_T \cdot k_1 & q_T \cdot k_2 & \cdots & q_T \cdot k_T
\end{bmatrix}
$$

So:

$QK^T \in \mathbb{R}^{T \times T}$

Each cell is still a scalar similarity score.

The matrix is not one score. It is a table of all pairwise scalar scores.

Rows represent query tokens.

Columns represent key tokens.

So entry $(i, j)$ means:

$\text{How much should token } i \text{ attend to token } j?$

Then softmax is applied row by row:

$$
\text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)
$$

Each row becomes a normalized distribution over all tokens.

For example, if one row before softmax is:

$[2.0,\ 1.0,\ 0.1]$

Then after softmax it may become approximately:

$[0.66,\ 0.24,\ 0.10]$

Meaning:

$\text{this token attends } 66\% \text{ to token 1, } 24\% \text{ to token 2, and } 10\% \text{ to token 3}$

So the correct mental model is:

$q_i \cdot k_j \rightarrow \text{one scalar similarity score}$

but:

$QK^T \rightarrow \text{a matrix containing all scalar similarity scores}$

The Transformer uses the matrix because every token needs to decide how much to attend to every other token.