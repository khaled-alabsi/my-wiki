# AI - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

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
