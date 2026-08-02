# AI - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

## Contents

- `AI/Transformer/` - transformer architecture deep-dives: forward pass, QKV shapes, matrix shapes, tokenizers, seq2seq
- `AI/tourch/` - PyTorch deep learning mechanics and nn-layer examples

## AI/Transformer/

- Place here: transformer architecture internals, PyTorch LLM tutorials, Hugging Face Transformers library, fine-tuning (LoRA/QLoRA), tokenizers, seq2seq models.
- `AI/Transformer/How Transformers Process Seq.md` - how transformers process sequences from input vectors to predictions; forward pass mechanics
- `AI/Transformer/Hugging Face Transformers.md` - self-contained tutorial on the Hugging Face `transformers` library: AutoClass system, model loading, tokenizers, inference, fine-tuning
- `AI/Transformer/LLM-Fine-Tuning.md.md` - fine-tuning small models locally and across cloud providers (AWS, GCP, Azure)
- `AI/Transformer/LoRa.md` - LoRA and QLoRA tutorial: parameter-efficient fine-tuning of large language models at PhD level
- `AI/Transformer/PyTorch-llm-tutorial.md` - comprehensive PyTorch tutorial for building and training LLMs end-to-end
- `AI/Transformer/PyTorch.md` - exhaustive PyTorch tutorial covering tensors, autograd, nn.Module, memory management, distributed training, and LLM deployment
- `AI/Transformer/PyTorsh-gpt.md` - building and training a demo large language model in PyTorch
- `AI/Transformer/The Transformer Forward Pass — From Raw Text to the Final Hidden Vector.md` - step-by-step transformer forward pass from raw text input through to final hidden vector output
- `AI/Transformer/Tokenizer seq2seq.md` - sequence-to-sequence translation, tokenizers, embeddings, and extending vocabularies
- `AI/Transformer/lora-input-output-clarified.md` - clarifying what "input" and "output" actually mean inside a LoRA layer
- `AI/Transformer/transformer-matrix-shapes.md` - transformer matrix shapes from input text to output; dimension tracking through the architecture
- `AI/Transformer/transformer-qkv-shapes.md` - Q, K, V tensor shapes at every stage: single token, full sequence, multi-head attention
- `AI/Transformer/transformer_qkv_notes.md` - comprehensive guide to understanding Query, Key, Value in transformers

## AI/tourch/

- Place here: PyTorch deep learning mechanics, nn.Linear usage, and attention projection examples.
- `AI/tourch/nn-layer-exmple.md` - complete reference on deep learning mechanics, nn.Linear layers, and attention projections
