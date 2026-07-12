# What “Input” and “Output” Actually Mean Inside a LoRA Layer

*A clarification note. The confusion this note resolves: when we say “$A$ is on the input side” and “$B$ is on the output side” of a LoRA module, we are not talking about the user’s prompt going into the LLM or the LLM’s generated text coming out. We are talking about something much more local.*

-----

## The misleading words

In a sentence like *”$A$ reads the input and $B$ writes the output,”* the words “input” and “output” sound like they refer to the model as a whole — the prompt you type and the answer the model generates. They do not. That is the input and output of the *entire model*, and it has nothing to do with the matrices $A$ and $B$.

LoRA does not operate at the level of the whole model. It operates inside one specific linear layer, somewhere deep in the network — for example, the query projection $W_q$ inside the third transformer block, or the up-projection in the seventh MLP. Every linear layer has its own *local* input and output, which are nothing more than the activation vectors flowing through that one point in the network. When this note (and the earlier discussion) uses the words “input” and “output,” that is what is meant.

## What flows in and out of one linear layer

Pick any one linear layer in the network. By itself, it is just a matrix-vector multiplication:
$$h = W , x.$$
The vector $x$ is whatever the previous layer handed to this one. The vector $h$ is whatever this layer hands to the next one. Both are intermediate activations, internal to the network, invisible from outside the model.

To make this very concrete, take the query projection $W_q$ in one attention block of a hidden-size-4096 transformer. For a single token at this point in the forward pass, a vector $x \in \mathbb{R}^{4096}$ arrives. That $x$ is the token’s hidden state at this depth in the network — a contextualized internal representation, *not* the user’s prompt. The matrix $W_q$ has shape $4096 \times 4096$, so multiplying gives $h = W_q x \in \mathbb{R}^{4096}$, the token’s query vector, which then feeds into the attention computation downstream. The vector $x$ is what is meant by “input of this layer,” and $h$ is what is meant by “output of this layer.” Both are local activations.

LoRA wraps such a layer. If 32 layers of a transformer get LoRA-wrapped, there are 32 independent matrix pairs $(A^{(1)}, B^{(1)}), \ldots, (A^{(32)}, B^{(32)})$, and each pair’s local $x$ is just whatever activation arrives at *that* specific layer in the architecture. The “input” the LoRA module sees has already passed through everything that comes before it in the network.

## Tracing one token through one LoRA-wrapped layer

Working this out on tiny shapes makes the picture concrete. Take a layer with $k = 4$ input dimensions, $d = 4$ output dimensions, and LoRA rank $r = 2$. Suppose the previous layer hands us
$$x = \begin{pmatrix} 1 \ 2 \ -1 \ 0 \end{pmatrix} \in \mathbb{R}^4.$$
This $x$ is the *local input* of this layer. The forward pass through the LoRA-wrapped layer is
$$h = W_0 , x ;+; B , (A , x),$$
where $W_0$ is the frozen pretrained weight, $A \in \mathbb{R}^{2 \times 4}$, and $B \in \mathbb{R}^{4 \times 2}$. The expression is best read right-to-left.

### Step 1: $A$ reads the input

With
$$A = \begin{pmatrix} 0.10 & -0.05 & 0.07 & -0.02 \ -0.04 & 0.06 & 0.03 & 0.08 \end{pmatrix},$$
the product $Ax$ is
$$A x = \begin{pmatrix} 0.10 \cdot 1 - 0.05 \cdot 2 + 0.07 \cdot (-1) - 0.02 \cdot 0 \ -0.04 \cdot 1 + 0.06 \cdot 2 + 0.03 \cdot (-1) + 0.08 \cdot 0 \end{pmatrix} = \begin{pmatrix} -0.07 \ 0.05 \end{pmatrix}.$$
Watch what this multiplication actually does. Each *row* of $A$ takes an inner product with $x$. Row 1 of $A$ asks “how much does $x$ resemble the pattern $(0.10, -0.05, 0.07, -0.02)$?” and the answer is $-0.07$. Row 2 asks a different question of $x$ and the answer is $0.05$. The result is a 2-dimensional summary of the 4-dimensional input. This is what is meant by saying *$A$ reads the input*: its rows are small detectors that scan the local input vector $x$ and produce scalar summaries.

### Step 2: $B$ writes to the output

With
$$B = \begin{pmatrix} 0.02 & -0.01 \ -0.03 & 0.04 \ 0.05 & 0.02 \ 0.01 & -0.03 \end{pmatrix},$$
the product $B(Ax)$ is
$$B (Ax) = \begin{pmatrix} 0.02 \cdot (-0.07) + (-0.01) \cdot 0.05 \ -0.03 \cdot (-0.07) + 0.04 \cdot 0.05 \ 0.05 \cdot (-0.07) + 0.02 \cdot 0.05 \ 0.01 \cdot (-0.07) + (-0.03) \cdot 0.05 \end{pmatrix} = \begin{pmatrix} -0.0019 \ 0.0041 \ -0.0025 \ -0.0022 \end{pmatrix}.$$
Now each *row* of $B$ takes the same 2-dim summary $(-0.07, 0.05)$ and forms its own weighted combination of those two numbers. The first output coordinate uses weights $(0.02, -0.01)$; the second uses $(-0.03, 0.04)$; and so on for all four. So $B$ takes the 2-dimensional summary that $A$ produced and “writes” it back into a 4-dimensional contribution, where each output coordinate is allowed its own mixture of the summary. This is what is meant by *$B$ writes to the output*.

### Step 3: Add to the base

We compute $W_0 x$ — the contribution the frozen pretrained model would have produced on its own — and add the LoRA contribution on top. The resulting vector $h$ becomes the *local input* of whatever layer comes next in the architecture.

## The precise translation

Whenever a LoRA explanation says *”$A$ is on the input side”*, the precise meaning is that $A$ is the matrix that first touches the local activation $x$ entering this specific layer. Whenever it says *”$B$ is on the output side”*, the precise meaning is that $B$ is the matrix that produces the LoRA branch’s contribution to the local activation $h$ leaving this specific layer. The $r$-dimensional vector that sits between them is a private internal summary that exists only inside this one LoRA module, between these two matrices, for a brief moment during the forward pass. It is never seen by any other layer and never appears anywhere else in the network.

This local picture is also what makes statements like *“information in $x$ orthogonal to all rows of $A$ is invisible to the LoRA update”* precise. If some direction in the 4-dim input has zero inner product with every row of $A$, then $Ax$ produces the same summary regardless of whether that direction was present, and from that point on the LoRA branch cannot tell. Symmetrically, output directions outside the column span of $B$ are “unreachable”: $B(Ax)$ is always some weighted combination of $B$‘s columns, so any direction in $\mathbb{R}^4$ that no column of $B$ points along will receive zero LoRA contribution. Both statements are about the local layer’s input space and output space — not about the model’s prompt or its generated text.

## The clean mental model

At every linear layer LoRA wraps, the local activation $x$ comes in, $A$ reads it down to an $r$-dimensional summary, $B$ writes that summary back up into the local output space, and the result is added on top of what the frozen $W_0$ produced. “Input” and “output” in that sentence always mean the local activations of *this* layer — never the model’s prompt or its response.

Why this confusion arises in the first place is worth naming. In everyday programming and machine-learning conversation, “input” and “output” almost always refer to the boundaries of a system: what the user supplies and what the system returns. That is the right reading at the level of the whole model. But once one zooms inside the network, every layer is itself a tiny system with its own input boundary (whatever the previous layer just produced) and its own output boundary (whatever this layer is about to produce). The vocabulary recurses. The price of that recursion is that any phrase like “input side” or “output side” has to be anchored to which system one is talking about. For LoRA, the answer is always: *the one specific linear layer that this particular LoRA module wraps.*