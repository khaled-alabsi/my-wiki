# AI - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

## Business Glossary

> `AI/`-local vocabulary, additional to the root `index.md` glossary — not a copy of it.
> Every definition comes from a note in this folder.

- **AdamW** — the optimizer used throughout these tutorials, motivated by Loshchilov and Hutter's decoupled weight-decay formulation. → `AI/Transformer/PyTorch-gpt.md`
- **AutoClass** — Hugging Face's system for loading a model and its matching tokenizer by name without naming the concrete class. → `AI/Transformer/Hugging Face Transformers.md`
- **DoRA** — LoRA variant that decomposes the weight update into magnitude and direction. → `AI/Transformer/PyTorch-llm-tutorial.md`
- **FSDP** — Fully Sharded Data Parallel. Shards parameters, gradients and optimizer states across GPUs and gathers them on demand; what you use when the model does not fit on one GPU. → `AI/Transformer/PyTorch-llm-tutorial.md`
- **KV cache** — stores each layer's key and value tensors per step so generation only computes K and V for the new token, turning it from O(T²) to O(T) per token. → `AI/Transformer/PyTorch-llm-tutorial.md`
- **LoRA** — Low-Rank Adaptation (Hu et al., 2021). Freezes the base model and trains two low-rank matrices A and B per linear layer, so the forward pass becomes `Wx + BAx`. → `AI/Transformer/LoRa.md`
- **MHA** — multi-head attention. Heads split the model dimension, attend separately, then concatenate and project. → `AI/Transformer/transformer-qkv-shapes.md`
- **PEFT** — Parameter-Efficient Fine-Tuning. The family of methods that fine-tune a small set of new or selected parameters and freeze the rest; LoRA is one branch. → `AI/Transformer/LoRa.md`
- **Pre-LN / Post-LN** — where layer norm sits in a transformer block. Pre-LN gives better-behaved gradients at initialisation and less warm-up sensitivity, so it is the default here. → `AI/Transformer/PyTorch-gpt.md`
- **QLoRA** — LoRA on top of a 4-bit quantized frozen base (Dettmers et al., 2023). → `AI/Transformer/LoRa.md`
- **Q / K / V** — Query, Key and Value: the three projections attention is built from, explained through a YouTube-search analogy. → `AI/Transformer/transformer_qkv_notes.md`
- **RMSNorm** — Root Mean Square Normalization. One of the structural enhancements a production-grade LLM relies on for training stability. → `AI/Transformer/PyTorch.md`
- **RoPE** — Rotary Positional Embeddings. Rotates the Query and Key representations in the complex plane before the attention dot product, encoding relative position dynamically instead of adding absolute position vectors. → `AI/Transformer/PyTorch.md`

## Contents

- `AI/Transformer/` - transformer architecture deep-dives, PyTorch, Hugging Face, fine-tuning, tokenizers

## AI/Transformer/

- Place here: transformer architecture internals, PyTorch (framework mechanics and LLM training), Hugging Face Transformers, parameter-efficient fine-tuning (LoRA/QLoRA), tokenizers, seq2seq, and tensor-shape walkthroughs.
- `AI/Transformer/How Transformers Process Seq.md` - how transformers process sequences from input vectors through to predictions
- `AI/Transformer/Hugging Face Transformers.md` - self-contained tutorial on the `transformers` library: the AutoClass system, model loading, tokenizers, inference, fine-tuning
- `AI/Transformer/LLM-Fine-Tuning.md` - fine-tuning small models locally and across AWS, GCP and Azure
- `AI/Transformer/LoRa.md` - LoRA and QLoRA: PhD-level tutorial on parameter-efficient fine-tuning
- `AI/Transformer/lora-input-output-clarified.md` - what "input" and "output" actually mean inside a LoRA layer
- `AI/Transformer/nn-layer-example.md` - deep learning mechanics end to end: `nn.Linear` layers and attention projections worked through
- `AI/Transformer/PyTorch.md` - exhaustive PyTorch reference: tensors, autograd, `nn.Module`, memory management, distributed training, deployment
- `AI/Transformer/PyTorch-gpt.md` - building and training a demo large language model in PyTorch
- `AI/Transformer/PyTorch-llm-tutorial.md` - comprehensive PyTorch tutorial for building and training LLMs end to end
- `AI/Transformer/The Transformer Forward Pass — From Raw Text to the Final Hidden Vector.md` - the forward pass step by step, from raw text to the final hidden vector
- `AI/Transformer/Tokenizer seq2seq.md` - sequence-to-sequence translation, tokenizers, embeddings, and extending vocabularies
- `AI/Transformer/transformer-matrix-shapes.md` - every matrix shape from input text to output, tracked through the architecture
  - `## Step 0 Text and Tokens` - tokenization and what comes out of it
  - `## Step 2 Embedding Lookup` - turning token IDs into vectors
  - `## Step 5 Transformer Block Overview` - the block's internal structure
  - `## Step 6 Attention Creates Q K V` - where Q, K and V come from
- `AI/Transformer/transformer-qkv-shapes.md` - Q, K, V tensor shapes at every stage: single token, full sequence, multi-head attention
  - `## Single Token Shapes` - shapes for one token
  - `## Projection Matrices` - the weight matrices that produce Q, K, V
  - `## Full Sequence Shapes` - shapes once a whole sequence is in play
  - `## Multi-Head Attention` - how heads split and recombine
- `AI/Transformer/transformer_qkv_notes.md` - conceptual guide to Query, Key and Value: the YouTube-search analogy, how they are built and used, scaling and softmax
