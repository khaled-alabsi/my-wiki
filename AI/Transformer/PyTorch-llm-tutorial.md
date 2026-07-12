# PyTorch for Large Language Models: A Comprehensive Tutorial

This tutorial walks through PyTorch end-to-end with the specific goal of building, training, and fine-tuning a large language model. It covers PyTorch’s core abstractions, the transformer architecture implemented from scratch, training infrastructure, and modern fine-tuning techniques such as LoRA. The examples are concrete and include input/output traces wherever a behaviour might be surprising.

-----

## Part 1: What PyTorch Actually Is

PyTorch is a Python library that does three things. First, it provides an N-dimensional array called a `Tensor` that runs on CPU or GPU. Second, it tracks operations on those tensors so it can automatically compute gradients (this is called autograd, and it is the entire reason deep learning frameworks exist). Third, it provides building blocks — layers, optimizers, data loaders — to assemble these tensors into neural networks and train them.

Everything you do in PyTorch is one of these three things in some combination. When you write a transformer, you are composing tensor operations into a function. When you call `loss.backward()`, you are asking autograd to compute the gradient of that function. When you call `optimizer.step()`, you are nudging the parameters in the direction the gradient suggests. The rest is plumbing.

A useful mental model is that PyTorch is a thin Python wrapper around a large C++/CUDA computation engine called ATen and a gradient engine called Autograd. When you write `a + b` in Python where `a` and `b` are tensors, Python doesn’t add them. Python calls into C++, C++ launches a CUDA kernel on the GPU if the tensors are on GPU, and the kernel performs the addition in parallel across thousands of GPU threads. Python’s job is just to describe the computation; the heavy lifting happens elsewhere. This is why Python’s speed is mostly irrelevant for training.

```python
import torch
print(torch.__version__)
# 2.x.x
print(torch.cuda.is_available())
# True if you have an NVIDIA GPU with CUDA, False otherwise
```

-----

## Part 2: Tensors

A tensor is a multidimensional array with a data type (`dtype`), a shape, and a device (CPU or GPU). Almost everything you do in PyTorch involves creating, transforming, or destroying tensors. Understanding the tensor API deeply is the single highest-leverage skill in PyTorch, because the transformer is just a clever arrangement of tensor operations.

### Creating Tensors

There are several ways to create a tensor, and each is used in different situations. You can create one from a Python list, from a NumPy array, or from a factory function that produces a specific pattern of values.

```python
import torch

# From a Python list. Useful for tiny test cases.
x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
print(x)
# tensor([[1., 2.],
#         [3., 4.]])
print(x.shape, x.dtype, x.device)
# torch.Size([2, 2]) torch.float32 cpu

# Factory functions. Useful for initializing model weights or buffers.
zeros = torch.zeros(3, 4)               # all zeros, shape (3, 4)
ones = torch.ones(2, 3)                 # all ones
randn = torch.randn(2, 3)               # standard normal: mean 0, std 1
rand = torch.rand(2, 3)                 # uniform in [0, 1)
arange = torch.arange(0, 10, 2)         # [0, 2, 4, 6, 8]
eye = torch.eye(3)                      # 3x3 identity matrix

# Empty does NOT initialize values — it just allocates memory.
# Use it when you will immediately overwrite the contents.
buf = torch.empty(1000, 1000)
```

The `dtype` argument controls precision. For LLMs you will encounter `torch.float32` (the default, 32 bits per number), `torch.float16` and `torch.bfloat16` (16 bits, used during mixed-precision training), and `torch.int64` (used for token IDs and indices). bfloat16 is particularly important because it has the same exponent range as float32 but fewer mantissa bits, which makes it numerically stable for training large models while halving memory usage.

```python
weights = torch.randn(1024, 1024, dtype=torch.bfloat16)
tokens = torch.tensor([101, 7592, 102], dtype=torch.long)  # long == int64
```

### Shape, View, Reshape, and the Memory Layout

A tensor has a `shape` (the size of each dimension) and a `stride` (how many elements you skip in memory to move one step along each dimension). Most tensors are contiguous in memory, meaning the elements are laid out in row-major order with no gaps. Some operations produce non-contiguous views, and this matters because some other operations (notably `view`) require contiguity.

```python
x = torch.arange(12)
print(x.shape)
# torch.Size([12])

# view returns a tensor that shares memory with x but has a new shape.
# This is free — no data is copied.
y = x.view(3, 4)
print(y)
# tensor([[ 0,  1,  2,  3],
#         [ 4,  5,  6,  7],
#         [ 8,  9, 10, 11]])

# reshape is more forgiving: it returns a view if possible, otherwise a copy.
z = x.reshape(3, 4)

# Using -1 lets PyTorch infer one dimension from the others.
y = x.view(3, -1)        # PyTorch infers the second dim is 4

# transpose swaps two dimensions. The result is a non-contiguous view.
y = torch.randn(2, 3, 4)
yt = y.transpose(1, 2)   # shape (2, 4, 3), shares memory with y
print(yt.is_contiguous())
# False

# If you need contiguity (for example, before calling .view), call .contiguous()
yt_contig = yt.contiguous()
```

The reason `view` requires contiguity is mechanical: it just reinterprets the same memory under a new shape, and that only works if the new shape’s stride pattern is compatible with the existing memory layout. A transposed tensor has a stride pattern that interleaves memory accesses, so reinterpreting it as a flat 1D array would scramble the values. `reshape` checks for this and silently copies when needed.

### Indexing and Slicing

PyTorch supports NumPy-style indexing with some extensions. The crucial mental model is that basic slicing returns a view (shares memory) while fancy indexing (with a tensor of indices or a boolean mask) returns a copy.

```python
x = torch.arange(24).view(2, 3, 4)

# Basic slicing — returns a view.
a = x[0]              # shape (3, 4)
b = x[:, 1, :]        # shape (2, 4)
c = x[..., 2]         # shape (2, 3), ... means "all remaining dims"

# Fancy indexing with a tensor of indices — returns a copy.
idx = torch.tensor([0, 2])
d = x[:, idx, :]      # shape (2, 2, 4)

# Boolean masking.
mask = x > 10
e = x[mask]           # 1D tensor of values where mask is True
```

For LLMs you will use indexing constantly: to look up token embeddings, to gather attention scores, to mask out padded positions, and to select the top-k predictions during generation.

### Broadcasting

Broadcasting is the rule that lets you add a tensor of shape `(3, 1)` to a tensor of shape `(1, 4)` and get a tensor of shape `(3, 4)` without writing an explicit loop. The rule is: align shapes from the right, and any dimension of size 1 is stretched to match the other tensor’s size in that dimension. Missing dimensions on the left are treated as size 1.

```python
a = torch.arange(3).view(3, 1)    # shape (3, 1):  [[0], [1], [2]]
b = torch.arange(4).view(1, 4)    # shape (1, 4):  [[0, 1, 2, 3]]
c = a + b                          # shape (3, 4)
print(c)
# tensor([[0, 1, 2, 3],
#         [1, 2, 3, 4],
#         [2, 3, 4, 5]])
```

In transformer code you will see broadcasting used for adding positional encodings (one position vector broadcasted across the batch), applying attention masks (one mask broadcasted across heads), and scaling (one scalar broadcasted across an entire tensor).

### Matrix Multiplication and Einsum

Matrix multiplication is the single most important operation in an LLM. PyTorch provides several ways to do it, each with slightly different semantics.

```python
a = torch.randn(3, 4)
b = torch.randn(4, 5)

# Standard 2D matrix multiply.
c = a @ b              # shape (3, 5)
c = torch.matmul(a, b) # same thing

# Batched matmul: the last two dims are the matrix, earlier dims are batch.
a = torch.randn(8, 3, 4)
b = torch.randn(8, 4, 5)
c = a @ b              # shape (8, 3, 5)
# This is what happens inside attention: a batch of QK^T multiplications.

# Einsum is a flexible way to express any contraction of tensor axes.
# The notation reads: "for each output index, sum over the indices not in the output"
a = torch.randn(2, 3, 4)
b = torch.randn(2, 4, 5)
c = torch.einsum('bij,bjk->bik', a, b)  # same as a @ b, shape (2, 3, 5)
```

Einsum is verbose but unambiguous, which makes it valuable for attention code where the index gymnastics get hairy. You will see both styles in real LLM codebases.

### Device Placement

A tensor lives on a specific device. To move it, use `.to()` or `.cuda()`. Operations between tensors require them to be on the same device.

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

x = torch.randn(1000, 1000)
x = x.to(device)
# or:
x = x.cuda()  # specifically for GPU; .to() is more general

# Once on GPU, operations run on GPU and produce GPU tensors.
y = x @ x.T
print(y.device)
# cuda:0
```

The first time you move data to the GPU there is a noticeable delay because CUDA initializes its context. Subsequent transfers are fast. A common bug is forgetting to move either the model or the input to the GPU, which gives a `RuntimeError: Expected all tensors to be on the same device` message.

-----

## Part 3: Autograd

Autograd is the system that makes deep learning possible. When you create a tensor with `requires_grad=True`, PyTorch starts recording every operation performed on it into a directed graph called the computation graph. When you later call `.backward()` on a scalar derived from that tensor, PyTorch walks the graph in reverse and uses the chain rule to compute gradients with respect to every leaf tensor that had `requires_grad=True`.

```python
import torch

# A leaf tensor with requires_grad=True is a tensor whose gradient we want.
x = torch.tensor([2.0, 3.0], requires_grad=True)

# Any operation on x produces a tensor that is also part of the graph.
y = x ** 2              # y = [4.0, 9.0]
z = y.sum()             # z = 13.0, a scalar

# .backward() computes dz/dx for every leaf tensor with requires_grad=True.
z.backward()
print(x.grad)
# tensor([4., 6.])
# Because dz/dx_i = d(x_i^2)/dx_i = 2*x_i = [4.0, 6.0]
```

Several details matter in practice. First, gradients accumulate by default. If you call `.backward()` twice without zeroing gradients, the second call adds to the first. This is why training loops always start with `optimizer.zero_grad()`. Second, you can only call `.backward()` on a scalar; if your output is not a scalar, you have to either sum or mean it, or pass a gradient tensor of the same shape. Third, intermediate tensors (not leaf tensors) do not retain their gradients by default — call `.retain_grad()` on them if you need them.

```python
# Demonstrating gradient accumulation.
x = torch.tensor([2.0], requires_grad=True)
y = x ** 2
y.backward()
print(x.grad)   # tensor([4.])
y = x ** 2      # recompute
y.backward()
print(x.grad)   # tensor([8.])  — accumulated, not reset
x.grad.zero_()  # reset to zero in-place
```

Sometimes you want to disable autograd, for instance during inference or when manually updating parameters. Use `torch.no_grad()` as a context manager, or `tensor.detach()` to break a tensor out of the graph.

```python
with torch.no_grad():
    predictions = model(inputs)
    # No graph is built; saves memory and time. Use during evaluation.

# detach returns a tensor that shares data but has no autograd history.
frozen_features = encoder(inputs).detach()
```

Conceptually, autograd is doing reverse-mode automatic differentiation. Every operation in PyTorch is registered with a forward function and a backward function. During the forward pass, PyTorch stores enough information (typically the inputs and outputs) to compute the local Jacobian-vector product in the backward pass. During the backward pass, it walks the graph from the output back to the inputs, multiplying these local Jacobians together via the chain rule. The “magic” is that this happens automatically because every tensor knows which operation produced it.

-----

## Part 4: nn.Module — Building Layers

`torch.nn.Module` is the base class for every layer, model, or composite component in PyTorch. It does two things: it registers parameters (tensors that should be trained) and submodules (other Modules), and it defines a `forward` method that describes the computation.

```python
import torch
import torch.nn as nn

class MyLinear(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        # nn.Parameter is a Tensor that is automatically registered
        # as a parameter of this module.
        self.weight = nn.Parameter(torch.randn(out_features, in_features) * 0.01)
        self.bias = nn.Parameter(torch.zeros(out_features))

    def forward(self, x):
        # x has shape (..., in_features)
        # @ is matmul; we transpose weight to align dimensions.
        return x @ self.weight.T + self.bias

layer = MyLinear(3, 4)
x = torch.randn(2, 3)
y = layer(x)            # Equivalent to layer.forward(x), but also invokes hooks
print(y.shape)
# torch.Size([2, 4])
```

When you call `layer(x)` rather than `layer.forward(x)`, PyTorch invokes the `__call__` method, which runs registered hooks, handles things like training/eval mode, and then calls `forward`. Always use the call syntax in user code.

A module composed of submodules automatically tracks all of their parameters. This recursion is what makes it possible to write `model.parameters()` and get back every weight in the entire network.

```python
class TwoLayerMLP(nn.Module):
    def __init__(self, d_in, d_hidden, d_out):
        super().__init__()
        self.fc1 = nn.Linear(d_in, d_hidden)
        self.fc2 = nn.Linear(d_hidden, d_out)
        # nn.Linear is PyTorch's built-in linear layer.

    def forward(self, x):
        x = self.fc1(x)
        x = torch.relu(x)
        x = self.fc2(x)
        return x

model = TwoLayerMLP(10, 32, 5)
# Iterating model.parameters() yields fc1.weight, fc1.bias, fc2.weight, fc2.bias.
for name, p in model.named_parameters():
    print(name, p.shape)
# fc1.weight torch.Size([32, 10])
# fc1.bias torch.Size([32])
# fc2.weight torch.Size([5, 32])
# fc2.bias torch.Size([5])
```

PyTorch provides a large library of pre-built modules in `torch.nn`. The ones most relevant to LLMs are `nn.Linear` (fully connected layer), `nn.Embedding` (lookup table mapping integer IDs to dense vectors), `nn.LayerNorm` (normalization across the last dimension), `nn.Dropout` (randomly zeros activations during training), and `nn.ModuleList` / `nn.ModuleDict` (containers for collections of submodules).

The training/evaluation mode distinction is important. Some modules — Dropout and BatchNorm in particular — behave differently in training versus inference. Call `model.train()` before training and `model.eval()` before evaluation. Forgetting this is a classic source of mysterious performance bugs.

```python
model.train()    # Dropout active, BatchNorm uses batch statistics
model.eval()     # Dropout inactive, BatchNorm uses running statistics
```

-----

## Part 5: Optimizers and Loss Functions

A loss function is just a tensor operation that takes predictions and targets and returns a scalar. PyTorch provides standard losses in `torch.nn`. For language modeling, the loss is almost always cross-entropy over the vocabulary at each position.

```python
import torch.nn.functional as F

logits = torch.randn(8, 50)          # batch of 8, vocab size 50
targets = torch.randint(0, 50, (8,)) # 8 target token IDs
loss = F.cross_entropy(logits, targets)
print(loss)
# tensor(3.91...)
# Cross-entropy expects raw logits (not probabilities) and integer targets.
# Internally it applies log_softmax and then negative log likelihood.
```

An optimizer is an object that holds references to the parameters you want to train and knows how to update them given their gradients. The standard optimizer for LLMs is AdamW, which is Adam with proper weight decay.

```python
from torch.optim import AdamW

optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)

# The training step pattern:
optimizer.zero_grad()    # clear gradients from the last step
loss = compute_loss(...) # forward pass
loss.backward()          # backward pass: populates .grad on every parameter
optimizer.step()         # use .grad to update each parameter
```

Under the hood, AdamW maintains two running averages per parameter: the first moment (mean of recent gradients) and the second moment (mean of recent squared gradients). The update rule divides the first moment by the square root of the second moment, which adapts the learning rate per parameter based on how noisy each gradient has been. Weight decay is applied as a direct shrinkage of the parameter rather than as a term added to the gradient, which is the “W” in AdamW and matters more than people initially think for large models.

Learning rate schedules are usually applied on top of the optimizer. The standard schedule for LLM pretraining is a linear warmup followed by cosine decay.

```python
from torch.optim.lr_scheduler import LambdaLR
import math

def lr_lambda(step):
    warmup_steps = 1000
    total_steps = 100000
    if step < warmup_steps:
        return step / warmup_steps
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return 0.5 * (1.0 + math.cos(math.pi * progress))

scheduler = LambdaLR(optimizer, lr_lambda)

# In the training loop:
optimizer.step()
scheduler.step()   # advance the schedule by one step
```

-----

## Part 6: Datasets and DataLoaders

PyTorch separates the concepts of a dataset (something you can index into to get one example) from a dataloader (something that batches, shuffles, and parallelizes loading). You implement a dataset by subclassing `torch.utils.data.Dataset` and providing `__len__` and `__getitem__`.

```python
from torch.utils.data import Dataset, DataLoader

class TextDataset(Dataset):
    def __init__(self, token_ids, block_size):
        # token_ids: a long 1D tensor of all tokens in the corpus
        # block_size: how many tokens each training example contains
        self.token_ids = token_ids
        self.block_size = block_size

    def __len__(self):
        # Number of possible starting positions for a block of block_size tokens.
        return len(self.token_ids) - self.block_size

    def __getitem__(self, idx):
        # Input is tokens [idx : idx + block_size]
        # Target is tokens [idx + 1 : idx + block_size + 1]
        # This is the classic "predict the next token at every position" setup.
        x = self.token_ids[idx : idx + self.block_size]
        y = self.token_ids[idx + 1 : idx + self.block_size + 1]
        return x, y

# Suppose we have a tokenized corpus.
corpus_tokens = torch.randint(0, 50000, (1_000_000,))  # 1M tokens, vocab 50k
dataset = TextDataset(corpus_tokens, block_size=512)

loader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4,     # parallel data loading processes
    pin_memory=True,   # speeds up CPU→GPU transfer
    drop_last=True,    # drop the last incomplete batch
)

for x, y in loader:
    # x: shape (32, 512), y: shape (32, 512)
    break
```

`num_workers` launches background processes that prefetch data, which matters when your dataset involves disk I/O or expensive preprocessing. `pin_memory=True` allocates the batches in special memory that can be transferred to GPU asynchronously, which overlaps data loading with compute.

For LLM training at scale you will outgrow this simple pattern and need streaming datasets (HuggingFace’s `datasets` library with `IterableDataset` is the de facto standard). The principle is the same: produce batches of `(input_ids, target_ids)` tensors as fast as the GPU can consume them.

-----

## Part 7: The Transformer From Scratch

Now we have enough PyTorch to build an LLM. The architecture is a decoder-only transformer, which is what GPT, Llama, and most modern LLMs use. The model consists of token embeddings, a stack of transformer blocks, a final layer norm, and an output projection back to vocabulary logits. Each transformer block contains a multi-head self-attention layer and a feed-forward network, each with a residual connection and pre-layer-norm.

### Token and Positional Embeddings

The first layer maps integer token IDs to dense vectors. Since attention is permutation-invariant, we also need to inject information about position. The simplest approach is a learned positional embedding table, although modern models use rotary embeddings (RoPE) instead. We will start with learned positional embeddings for clarity.

```python
import torch
import torch.nn as nn

class Embeddings(nn.Module):
    def __init__(self, vocab_size, d_model, max_seq_len):
        super().__init__()
        # Token embedding: a lookup table of shape (vocab_size, d_model).
        # Looking up token ID i returns row i of this table.
        self.token_emb = nn.Embedding(vocab_size, d_model)
        # Positional embedding: a lookup table for positions 0..max_seq_len-1.
        self.pos_emb = nn.Embedding(max_seq_len, d_model)

    def forward(self, input_ids):
        # input_ids: shape (batch, seq_len), dtype long
        batch, seq_len = input_ids.shape
        # Build a positions tensor: [0, 1, 2, ..., seq_len-1] for each batch.
        positions = torch.arange(seq_len, device=input_ids.device)
        # Token and position embeddings are added; broadcasting handles batch dim.
        return self.token_emb(input_ids) + self.pos_emb(positions)
```

Input/output trace: if `input_ids` has shape `(2, 5)` and `d_model=64`, the output has shape `(2, 5, 64)`. Each of the 10 token positions becomes a 64-dimensional vector that encodes both *what* the token is and *where* it sits in the sequence.

### Multi-Head Self-Attention

Attention is the operation that lets each token “look at” every other token (or only the previous tokens, in the causal/decoder case) and aggregate information from them. Multi-head attention runs several attention operations in parallel with different learned projections, then concatenates the results. The intuition is that different heads can specialize in different relationships — one might track syntactic dependencies, another might track entity coreference, and so on.

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        # One big linear that produces Q, K, V for all heads at once.
        # Output dim is 3 * d_model because we are concatenating Q, K, V.
        self.qkv_proj = nn.Linear(d_model, 3 * d_model, bias=False)
        # Final output projection that mixes information across heads.
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, causal_mask=None):
        # x: shape (batch, seq_len, d_model)
        B, T, C = x.shape

        # Project to Q, K, V all at once, then split.
        qkv = self.qkv_proj(x)                       # (B, T, 3*C)
        q, k, v = qkv.chunk(3, dim=-1)               # each (B, T, C)

        # Reshape to separate heads: (B, T, n_heads, d_head),
        # then transpose to (B, n_heads, T, d_head) so the matmul works.
        q = q.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        k = k.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.d_head).transpose(1, 2)

        # Compute attention scores: Q @ K^T, scaled by sqrt(d_head).
        # scores has shape (B, n_heads, T, T): for each head, a TxT matrix
        # where entry (i, j) is the unnormalized attention from token i to token j.
        scores = (q @ k.transpose(-2, -1)) / (self.d_head ** 0.5)

        # Apply the causal mask: token i can only attend to tokens j <= i.
        # We fill the masked positions with -inf so they become 0 after softmax.
        if causal_mask is not None:
            scores = scores.masked_fill(causal_mask, float('-inf'))

        # Softmax over the last dimension turns scores into a probability distribution.
        attn = torch.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        # Use the attention weights to compute a weighted sum of value vectors.
        # out shape: (B, n_heads, T, d_head)
        out = attn @ v

        # Merge heads back together: (B, T, n_heads, d_head) → (B, T, d_model)
        out = out.transpose(1, 2).contiguous().view(B, T, C)

        # Final output projection.
        return self.out_proj(out)
```

The shape gymnastics here are worth tracing carefully. We start with a `(B, T, C)` tensor where `C = n_heads * d_head`. We project it to three tensors of the same shape (Q, K, V), then reshape and transpose each one into `(B, n_heads, T, d_head)`. The transpose is what makes the batched matrix multiplication compute one attention operation per head in parallel: the last two dimensions are `(T, d_head)`, and the first two are batch dimensions. After the attention computation we transpose and reshape back, then project.

The causal mask is a boolean tensor of shape `(T, T)` where entry `(i, j)` is `True` if token `i` should NOT attend to token `j` (which is the case when `j > i`). It is broadcastable across batch and head dimensions.

```python
def make_causal_mask(seq_len, device):
    # True above the diagonal: position i cannot see positions j > i.
    return torch.triu(torch.ones(seq_len, seq_len, dtype=torch.bool, device=device),
                      diagonal=1)
```

A note on efficiency: this implementation is for clarity. In production you should use `torch.nn.functional.scaled_dot_product_attention`, which dispatches to a fused kernel (FlashAttention on supported hardware) that is much faster and uses much less memory. We will use it in the final model.

### Feed-Forward Network

The feed-forward network in a transformer is a two-layer MLP applied independently to each position. The standard width is `4 * d_model` in the hidden layer.

```python
class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff=None, dropout=0.0):
        super().__init__()
        d_ff = d_ff or 4 * d_model
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # GELU is the standard activation in modern transformers.
        # It's like ReLU but smooth, which helps gradient flow.
        x = self.fc1(x)
        x = nn.functional.gelu(x)
        x = self.fc2(x)
        return self.dropout(x)
```

Modern models often use a “gated” variant called SwiGLU, which has three linear layers instead of two and an element-wise multiplication that acts as a gate. SwiGLU performs slightly better but is mechanically the same idea.

### Transformer Block

Each transformer block applies attention, then feed-forward, each wrapped in a residual connection and pre-layer-norm. Pre-LN (norm before the sublayer) is more stable than post-LN (norm after) and is what every recent model uses.

```python
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff=None, dropout=0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_heads, dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = FeedForward(d_model, d_ff, dropout)

    def forward(self, x, causal_mask=None):
        # Pre-norm: normalize, apply sublayer, then add the residual.
        # This is the "Pre-LN" arrangement.
        x = x + self.attn(self.norm1(x), causal_mask)
        x = x + self.ff(self.norm2(x))
        return x
```

The residual connection (`x + ...`) is what allows information and gradients to flow unimpeded through deep networks. Without it, training a transformer with dozens of layers would be nearly impossible because gradients would vanish or explode.

### The Full Model

Now we assemble everything.

```python
class GPT(nn.Module):
    def __init__(self, vocab_size, d_model=512, n_layers=6, n_heads=8,
                 max_seq_len=512, dropout=0.0):
        super().__init__()
        self.max_seq_len = max_seq_len
        self.embeddings = Embeddings(vocab_size, d_model, max_seq_len)
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, dropout=dropout)
            for _ in range(n_layers)
        ])
        self.norm_f = nn.LayerNorm(d_model)
        # Output projection back to vocab. We tie this weight to the input
        # embedding weight, which is a standard trick that saves parameters
        # and often improves performance.
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        self.lm_head.weight = self.embeddings.token_emb.weight  # weight tying

        # Initialize weights with the GPT-2 scheme: small Gaussian for linear
        # layers, slightly different for embeddings.
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids, targets=None):
        # input_ids: (B, T)
        B, T = input_ids.shape
        assert T <= self.max_seq_len

        # Build causal mask once per forward pass.
        causal_mask = torch.triu(
            torch.ones(T, T, dtype=torch.bool, device=input_ids.device),
            diagonal=1
        )

        x = self.embeddings(input_ids)         # (B, T, d_model)
        for block in self.blocks:
            x = block(x, causal_mask)
        x = self.norm_f(x)
        logits = self.lm_head(x)                # (B, T, vocab_size)

        if targets is None:
            return logits, None

        # Compute loss: cross-entropy at every position.
        # We flatten (B, T) into one big batch dimension for cross_entropy.
        loss = nn.functional.cross_entropy(
            logits.view(B * T, -1),
            targets.view(B * T),
        )
        return logits, loss
```

This is roughly the architecture of nanoGPT, which is a clean reference implementation worth reading. A real production LLM has additional refinements: rotary positional embeddings instead of learned, SwiGLU instead of GELU, RMSNorm instead of LayerNorm, grouped-query attention, and fused kernels. But the bones are exactly what we built.

-----

## Part 8: Training the Model

A training loop is just a `for` loop that batches data, runs the forward pass, computes the loss, backpropagates, and steps the optimizer.

```python
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

# Setup.
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = GPT(vocab_size=50257, d_model=512, n_layers=8, n_heads=8,
            max_seq_len=512).to(device)

optimizer = AdamW(model.parameters(), lr=3e-4, weight_decay=0.1,
                  betas=(0.9, 0.95))

# Suppose `loader` yields (input_ids, targets) batches.
model.train()
for step, (input_ids, targets) in enumerate(loader):
    input_ids = input_ids.to(device, non_blocking=True)
    targets = targets.to(device, non_blocking=True)

    optimizer.zero_grad(set_to_none=True)
    logits, loss = model(input_ids, targets)
    loss.backward()

    # Gradient clipping: prevents the rare exploding-gradient catastrophe.
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

    optimizer.step()

    if step % 100 == 0:
        print(f"step {step}, loss {loss.item():.4f}")
```

A few details that matter at scale. `optimizer.zero_grad(set_to_none=True)` is slightly faster than the default because it deallocates the gradient tensors instead of filling them with zeros. `non_blocking=True` in the `.to()` call allows the transfer to overlap with computation when `pin_memory=True` in the DataLoader. Gradient clipping is essentially free insurance against the occasional huge gradient that would otherwise blow up training.

### Mixed Precision Training

Training in pure float32 wastes memory and compute. Mixed precision uses float16 or bfloat16 for most operations while keeping a float32 master copy of the weights for numerically stable updates. PyTorch’s `torch.amp` makes this nearly automatic.

```python
from torch.amp import autocast, GradScaler

# GradScaler is only needed for float16; bfloat16 doesn't need it.
scaler = GradScaler('cuda')

for input_ids, targets in loader:
    input_ids = input_ids.to(device, non_blocking=True)
    targets = targets.to(device, non_blocking=True)

    optimizer.zero_grad(set_to_none=True)

    # autocast wraps the forward pass: operations inside automatically
    # use float16 where it's safe, float32 where it isn't.
    with autocast(device_type='cuda', dtype=torch.float16):
        logits, loss = model(input_ids, targets)

    # GradScaler scales the loss up before backward to keep small gradients
    # from underflowing in float16. It unscales them before the optimizer step.
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)
    scaler.update()
```

If you use bfloat16 (which is preferred on Ampere GPUs and newer because it has the same exponent range as float32), you can skip the GradScaler:

```python
with autocast(device_type='cuda', dtype=torch.bfloat16):
    logits, loss = model(input_ids, targets)
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
optimizer.step()
```

### Gradient Accumulation

Sometimes the batch size you want exceeds GPU memory. Gradient accumulation simulates a large batch by running several small batches and summing their gradients before stepping.

```python
accum_steps = 4   # effective batch size is batch_size * accum_steps

optimizer.zero_grad(set_to_none=True)
for step, (input_ids, targets) in enumerate(loader):
    input_ids = input_ids.to(device)
    targets = targets.to(device)

    with autocast(device_type='cuda', dtype=torch.bfloat16):
        _, loss = model(input_ids, targets)
        loss = loss / accum_steps  # scale because we sum accum_steps losses

    loss.backward()  # gradients accumulate

    if (step + 1) % accum_steps == 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
```

### Checkpointing

Saving and loading model state is done through state dictionaries, which are ordered dictionaries mapping parameter names to tensors.

```python
# Save.
torch.save({
    'step': step,
    'model_state': model.state_dict(),
    'optimizer_state': optimizer.state_dict(),
    'scheduler_state': scheduler.state_dict(),
}, 'checkpoint.pt')

# Load.
ckpt = torch.load('checkpoint.pt', map_location=device)
model.load_state_dict(ckpt['model_state'])
optimizer.load_state_dict(ckpt['optimizer_state'])
scheduler.load_state_dict(ckpt['scheduler_state'])
start_step = ckpt['step']
```

Always save the optimizer state too: AdamW’s running moments are large and important. Resuming training without them effectively restarts the optimizer, which can destabilize training.

### Activation Checkpointing

For large models, the activations stored for the backward pass can exceed GPU memory. Activation checkpointing trades compute for memory by discarding activations during the forward pass and recomputing them during the backward pass.

```python
from torch.utils.checkpoint import checkpoint

# In your TransformerBlock or model forward:
def forward(self, x, causal_mask=None):
    x = x + checkpoint(self.attn, self.norm1(x), causal_mask, use_reentrant=False)
    x = x + checkpoint(self.ff, self.norm2(x), use_reentrant=False)
    return x
```

This roughly halves activation memory at the cost of an extra forward pass per backward step. For models that don’t fit in memory otherwise, it is a lifesaver.

-----

## Part 9: Inference and Text Generation

Generating text from a trained LLM is autoregressive: feed in a prompt, sample one token from the output distribution, append it, and repeat. The simplest version is greedy decoding (always pick the highest-probability token), but in practice you want temperature, top-k, or top-p (nucleus) sampling.

```python
@torch.no_grad()
def generate(model, input_ids, max_new_tokens, temperature=1.0, top_k=None):
    """
    input_ids: (B, T) starting prompt, on the same device as the model
    Returns:   (B, T + max_new_tokens)
    """
    model.eval()
    for _ in range(max_new_tokens):
        # Crop to max context length so positional embeddings don't break.
        ids_cond = input_ids[:, -model.max_seq_len:]

        logits, _ = model(ids_cond)
        # Take logits at the last position only.
        logits = logits[:, -1, :] / temperature        # (B, vocab_size)

        if top_k is not None:
            # Keep only the top-k logits, set the rest to -inf.
            v, _ = torch.topk(logits, top_k)
            logits[logits < v[:, [-1]]] = float('-inf')

        probs = torch.softmax(logits, dim=-1)
        # Sample one token per batch element.
        next_id = torch.multinomial(probs, num_samples=1)  # (B, 1)
        input_ids = torch.cat([input_ids, next_id], dim=1)

    return input_ids
```

Temperature is a knob on the softmax: low temperature (close to 0) sharpens the distribution toward the most likely token, high temperature (above 1) flattens it and introduces more randomness. Top-k truncates the distribution to the k most likely tokens. Top-p (nucleus) keeps the smallest set of tokens whose cumulative probability exceeds p. These are not in the loss function, just in the sampling procedure.

A serious inefficiency in the code above is that we recompute attention for the entire context at every step. Real inference uses a **KV cache**: store the key and value tensors from each layer at each step so that on the next step you only need to compute K and V for the new token. This turns generation from O(T²) to O(T) per token. Implementing it cleanly requires threading a cache object through every attention layer.

-----

## Part 10: Fine-Tuning

Once a base model is pretrained on a large corpus, fine-tuning adapts it to a specific task or style. There are several flavors of fine-tuning.

### Full Fine-Tuning

Full fine-tuning updates every parameter in the model. The training loop is identical to pretraining, except the dataset is task-specific (typically instruction-response pairs) and the learning rate is much lower (often 10× to 100× smaller than pretraining LR).

```python
# Load the pretrained checkpoint.
ckpt = torch.load('pretrained.pt', map_location=device)
model.load_state_dict(ckpt['model_state'])

# Fresh optimizer with a lower learning rate.
optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

# Otherwise the training loop is identical.
```

For instruction tuning, the dataset usually has the format `<prompt> <response>`, and you typically mask the loss on the prompt tokens so the model is only trained to predict the response. You do this by setting target IDs to a special ignore index (default `-100`) for prompt positions.

```python
# Suppose prompt is the first 30 tokens of a 128-token sequence.
targets = input_ids.clone()
targets[:, :30] = -100   # cross_entropy ignores positions with target == -100
_, loss = model(input_ids[:, :-1], targets[:, 1:])
```

### Parameter-Efficient Fine-Tuning: LoRA

Full fine-tuning of a 70B-parameter model is impractical for most people. LoRA (Low-Rank Adaptation) freezes the base model and trains a tiny number of additional parameters: for each linear layer of interest, two low-rank matrices `A` and `B` of shape `(r, d)` and `(d, r)` are added, and the forward pass becomes `Wx + BAx` where `W` is frozen. With `r = 8`, you might train 0.1% as many parameters as the full model and recover most of the performance.

```python
class LoRALinear(nn.Module):
    def __init__(self, base_linear: nn.Linear, rank: int, alpha: float = 16.0):
        super().__init__()
        self.base = base_linear
        # Freeze the base weights.
        for p in self.base.parameters():
            p.requires_grad = False

        in_features = base_linear.in_features
        out_features = base_linear.out_features

        # A is initialized with Kaiming, B is initialized to zero.
        # This means the LoRA contribution starts at exactly zero, so the
        # model behaves identically to the base at the start of training.
        self.lora_A = nn.Parameter(torch.empty(rank, in_features))
        nn.init.kaiming_uniform_(self.lora_A, a=5**0.5)
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        # Scaling: alpha/rank is the standard convention.
        self.scale = alpha / rank

    def forward(self, x):
        # x @ W.T is the frozen base computation.
        # x @ A.T @ B.T is the low-rank adaptation.
        base_out = self.base(x)
        lora_out = (x @ self.lora_A.T) @ self.lora_B.T * self.scale
        return base_out + lora_out


def apply_lora(model, rank=8, target_modules=('qkv_proj', 'out_proj')):
    """Replace target Linear layers with LoRALinear in-place."""
    for name, module in model.named_modules():
        for child_name, child in list(module.named_children()):
            if isinstance(child, nn.Linear) and child_name in target_modules:
                setattr(module, child_name, LoRALinear(child, rank=rank))
    return model
```

When you train this, only `lora_A` and `lora_B` have `requires_grad=True`, so the optimizer only sees a fraction of the parameters and the optimizer state shrinks accordingly. After training, you can either keep the LoRA modules as a separate adapter or merge `BA` back into `W` to recover a plain linear layer with no inference overhead.

```python
# Filter to trainable params only.
trainable = [p for p in model.parameters() if p.requires_grad]
optimizer = AdamW(trainable, lr=1e-4)

print(f"Trainable: {sum(p.numel() for p in trainable):,}")
print(f"Total:     {sum(p.numel() for p in model.parameters()):,}")
```

LoRA is the most popular fine-tuning method today because it makes single-GPU fine-tuning of large models tractable. Variants include QLoRA (LoRA on top of a 4-bit quantized base model) and DoRA (decomposes the weight update into magnitude and direction).

-----

## Part 11: Distributed Training (Conceptual Overview)

Single-GPU training caps out at a few hundred million parameters. Beyond that you need to spread the work across multiple GPUs, and there are several strategies.

**Data Parallel (DDP)** replicates the entire model on each GPU and splits the batch across them. Each GPU computes gradients on its slice, and the gradients are averaged across GPUs after the backward pass (via an all-reduce operation). This is the simplest and most common strategy and works as long as the model fits on a single GPU.

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group(backend='nccl')
torch.cuda.set_device(local_rank)

model = GPT(...).to(local_rank)
model = DDP(model, device_ids=[local_rank])

# The rest of the training loop is unchanged. DDP intercepts the backward
# pass to all-reduce gradients across GPUs.
```

**Fully Sharded Data Parallel (FSDP)** is what you use when the model doesn’t fit on one GPU. It shards the parameters, gradients, and optimizer states across GPUs and gathers them on-demand during the forward and backward passes. PyTorch’s `FullyShardedDataParallel` makes this almost as simple as DDP, although it has more knobs to tune.

**Tensor parallelism** splits individual layers across GPUs (for example, splitting a linear layer’s weight matrix into column chunks, each on a different GPU). This is necessary for very large models where even a single layer doesn’t fit. Megatron-LM popularized this approach; PyTorch now has native support via `torch.distributed.tensor.parallel`.

**Pipeline parallelism** splits the layers across GPUs so different stages of the model run on different devices. It’s typically combined with the other strategies for the largest training runs (“3D parallelism” = data + tensor + pipeline).

You will rarely write the distributed code from scratch. Most people use higher-level libraries like HuggingFace Accelerate, DeepSpeed, or PyTorch Lightning that abstract these patterns into a few lines of configuration.

-----

## Part 12: Profiling and Debugging

When training is slower than you expect, the answer is almost always: profile, don’t guess. PyTorch has a built-in profiler.

```python
from torch.profiler import profile, ProfilerActivity

with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
             record_shapes=True) as prof:
    for _ in range(5):
        logits, loss = model(input_ids, targets)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
```

This produces a table of operations sorted by GPU time, which immediately tells you whether you are bottlenecked by matmul, attention, dataloading, or something else. The most common surprises are: GPU idle time waiting on the dataloader (fix: more workers, prefetching), excessive `.item()` or `.cpu()` calls that force CPU-GPU sync (fix: avoid them in the hot path), and unfused operations that should be fused (fix: `torch.compile`).

`torch.compile` is PyTorch’s JIT compiler. Wrapping your model in it can produce significant speedups by fusing operations:

```python
model = torch.compile(model)
# The first call is slow (compilation), subsequent calls are faster.
```

It works on most models without any code changes, although it occasionally fails on unusual control flow and you have to work around it.

-----

## Part 13: Putting It All Together

Here is the skeleton of a complete training script that combines everything we have built. This is the kind of file you would actually run.

```python
import torch
import torch.nn as nn
from torch.amp import autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader
import math

# 1. Config
CONFIG = dict(
    vocab_size=50257,
    d_model=768,
    n_layers=12,
    n_heads=12,
    max_seq_len=1024,
    batch_size=12,
    accum_steps=8,
    lr=6e-4,
    weight_decay=0.1,
    warmup_steps=2000,
    total_steps=600_000,
    grad_clip=1.0,
)

# 2. Model
device = torch.device('cuda')
model = GPT(
    vocab_size=CONFIG['vocab_size'],
    d_model=CONFIG['d_model'],
    n_layers=CONFIG['n_layers'],
    n_heads=CONFIG['n_heads'],
    max_seq_len=CONFIG['max_seq_len'],
).to(device)

# 3. Optimizer with weight decay only on 2D parameters (matrices, not biases/norms)
decay_params = [p for p in model.parameters() if p.dim() >= 2]
no_decay_params = [p for p in model.parameters() if p.dim() < 2]
optimizer = AdamW([
    {'params': decay_params, 'weight_decay': CONFIG['weight_decay']},
    {'params': no_decay_params, 'weight_decay': 0.0},
], lr=CONFIG['lr'], betas=(0.9, 0.95))

# 4. Learning rate schedule
def lr_lambda(step):
    if step < CONFIG['warmup_steps']:
        return step / CONFIG['warmup_steps']
    progress = (step - CONFIG['warmup_steps']) / \
               (CONFIG['total_steps'] - CONFIG['warmup_steps'])
    return max(0.1, 0.5 * (1.0 + math.cos(math.pi * progress)))
scheduler = LambdaLR(optimizer, lr_lambda)

# 5. Compile for speed
model = torch.compile(model)

# 6. Training loop
model.train()
optimizer.zero_grad(set_to_none=True)
step = 0
while step < CONFIG['total_steps']:
    for micro_step, (x, y) in enumerate(loader):
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with autocast(device_type='cuda', dtype=torch.bfloat16):
            _, loss = model(x, y)
            loss = loss / CONFIG['accum_steps']
        loss.backward()
        if (micro_step + 1) % CONFIG['accum_steps'] == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), CONFIG['grad_clip'])
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            if step % 100 == 0:
                print(f"step {step} loss {loss.item()*CONFIG['accum_steps']:.4f} "
                      f"lr {scheduler.get_last_lr()[0]:.2e}")
            if step % 5000 == 0:
                torch.save({'model': model.state_dict(), 'step': step},
                           f'ckpt_{step}.pt')
```

This script trains a 124M-parameter GPT-2-sized model. The same code with bigger numbers in `CONFIG` and FSDP wrapping is what trains a 7B-parameter model.

-----

## Part 14: What to Read Next

This tutorial gives you a complete grounding, but several topics are worth deeper study. Andrej Karpathy’s nanoGPT and the accompanying YouTube series are the cleanest reference implementation of everything in Part 7. The HuggingFace Transformers library is the de facto standard for working with pretrained models — reading its `modeling_llama.py` is enlightening. For inference optimization, vLLM and the PagedAttention paper are essential. For training infrastructure, the DeepSpeed and Megatron-LM papers explain the algorithms behind FSDP and tensor parallelism. For fine-tuning, the QLoRA paper is the right entry point.

The most important meta-skill is reading other people’s PyTorch code. The library is small enough that any well-written model file should be readable end-to-end, and patterns repeat across codebases. Once you can read a transformer implementation in any framework and immediately recognize what each part is doing, you have arrived.