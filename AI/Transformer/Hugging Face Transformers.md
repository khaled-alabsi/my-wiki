# Hugging Face Transformers — A Self-Contained Tutorial

This tutorial assumes nothing about your knowledge of the Hugging Face ecosystem and aims to leave you, by the end, able to load any model from the Hub, run inference for any task, fine-tune on your own data, and reason about what is happening at every step. Everything you need is in this document — concepts are defined inline, every shortcut is explained, and every code pattern is paired with input/output examples and a description of what is happening underneath.

The library this tutorial is about is the Python package `transformers` published by the company Hugging Face. The same company also publishes a website called the Hugging Face Hub (`huggingface.co`) that hosts model weights, datasets, and demos. The two are deeply intertwined: the `transformers` library is essentially a uniform Python interface to “any model on the Hub” plus the training and inference machinery to use them.

-----

## 1. The Mental Model: What This Library Actually Is

A transformer model — the neural network architecture introduced by Vaswani et al. in 2017 — is, mechanically, a stack of layers that turn a sequence of token IDs into a sequence of vectors (or further into logits over a vocabulary, or class scores, or whatever the task head produces). To run such a model you need three things in lockstep:

1. **A configuration**: hyperparameters describing the architecture (number of layers, hidden size, number of attention heads, vocabulary size, dropout rates, position-embedding type, and so on). Without this, the framework doesn’t know what shape of weights to allocate.
2. **A tokenizer**: the deterministic procedure that turns raw text into the integer token IDs the model expects, plus the inverse procedure to turn IDs back into text. Different models were pretrained with different tokenizers and you cannot mix them — using BERT’s tokenizer with GPT-2’s weights produces garbage.
3. **The model itself**: the weights organized into the architecture described by the configuration.

The Hugging Face `transformers` library is, fundamentally, a single coherent abstraction over these three things, for hundreds of model families, with one consistent API. The library’s biggest design decision is what they call the **AutoClass** system: instead of importing `BertModel`, `GPT2Model`, `LlamaModel` separately and remembering which kind of weights are in a given checkpoint, you import `AutoModel` and call `AutoModel.from_pretrained("some/checkpoint")` — and the library reads the config file at that checkpoint, figures out it is a Llama model, and gives you back the right class instantiated with the right weights.

A **checkpoint** in this world is just a folder (local or on the Hub) containing at minimum a `config.json`, a weights file (`pytorch_model.bin`, `model.safetensors`, or sharded variants), and the tokenizer files. The string you pass to `from_pretrained` — for example `"distilbert-base-uncased"` or `"meta-llama/Llama-3.2-1B"` — is the path to such a folder, either locally or as a repository ID on the Hub. The library downloads it on first use and caches it under `~/.cache/huggingface/hub` (or wherever the environment variable `HF_HOME` points).

Internally the flow when you call `AutoModel.from_pretrained("some-repo/some-model")` is:

The library downloads `config.json` (if not cached) and inspects the field `model_type`, which is a short string like `"bert"`, `"llama"`, `"qwen3"`. It looks this string up in a registry that maps `model_type` to a concrete config class and a concrete model class. It instantiates the config from the JSON, then instantiates the model architecture using that config (this allocates the weight tensors with random initial values), then downloads the weights file and copies them into the right places in the model. The end result is an ordinary PyTorch `nn.Module` (or TensorFlow / Flax equivalent), which you can call with input tensors as usual.

This three-step pattern — config → architecture → weights — is repeated for tokenizers (`AutoTokenizer`), image processors (`AutoImageProcessor`), feature extractors (`AutoFeatureExtractor`), and the multi-modal `AutoProcessor`. Once you have internalized this, the entire library makes sense as variations on the same theme.

-----

## 2. Installation and Environment

The library is `pip install transformers`. By itself it has no deep-learning backend — you must additionally install PyTorch, TensorFlow, or JAX/Flax. In practice almost everyone uses PyTorch today and that is what this tutorial assumes:

```
pip install "transformers[torch]"
pip install datasets accelerate evaluate
```

The three companion libraries that almost always come along:

- **`datasets`**: a fast, Arrow-backed library for loading and processing datasets, with the same `load_dataset("repo_id")` pattern that mirrors `from_pretrained`.
- **`accelerate`**: an abstraction layer that handles device placement, mixed precision, and multi-GPU / multi-node training so you don’t have to write `.to(device)` and `DistributedDataParallel` boilerplate.
- **`evaluate`**: the metrics library (accuracy, F1, BLEU, ROUGE, perplexity, and so on) used during training and evaluation.

Optional but very common: `peft` (parameter-efficient fine-tuning — LoRA and friends), `bitsandbytes` (4-bit and 8-bit quantization on NVIDIA GPUs), `trl` (RLHF and DPO trainers), `sentencepiece` and `tiktoken` (specific tokenizer backends required by some models), `safetensors` (a safer weights format than pickle; the modern default).

The library reads several environment variables that are worth knowing about because they will save you hours of confusion later. `HF_HOME` controls the cache root. `HF_TOKEN` provides authentication for private/gated models without an interactive login. `TRANSFORMERS_OFFLINE=1` forces the library to use only what is already in the cache (useful on air-gapped machines or to prevent silent re-downloads). `HF_HUB_DISABLE_TELEMETRY=1` silences anonymous usage reporting.

A common gotcha: many Llama-family and gated models require you to accept a license on the Hub web page before `from_pretrained` will work. The error message in this case is misleading (“repository not found”); the real cause is that you haven’t logged in (`huggingface-cli login`) or haven’t accepted the gate.

-----

## 3. The Pipeline API — Easy Mode

The fastest path from zero to a working model is the `pipeline` function. A pipeline is a thin wrapper that bundles together a tokenizer (or image processor), a model, and the pre/post-processing code specific to one task. You give it raw inputs of the right kind (strings, images, audio) and it gives you back human-readable outputs (labels, generated text, bounding boxes).

```python
from transformers import pipeline

classifier = pipeline("sentiment-analysis")
classifier("I really enjoyed this movie, the acting was superb.")
```

The output is:

```python
[{'label': 'POSITIVE', 'score': 0.9998}]
```

Under the hood the pipeline did roughly the following: because no `model=` was passed, it looked up a default model for the task `"sentiment-analysis"` (which is currently `distilbert-base-uncased-finetuned-sst-2-english`), downloaded that checkpoint and its tokenizer if not cached, ran `tokenizer(text, return_tensors="pt", truncation=True, padding=True)` to get a dict of input tensors, called `model(**inputs)` to get logits of shape `(1, 2)`, applied softmax to convert them to probabilities, picked the argmax index, looked up the corresponding string label in `model.config.id2label`, and packaged it as a list of dicts.

You can — and almost always should — specify the model explicitly rather than rely on the task default, both because the default may change over time and because the right model depends on your domain:

```python
classifier = pipeline(
    task="sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=0,           # 0 = first GPU; -1 = CPU; "cuda", "mps", "cpu" also work
    torch_dtype="auto", # let the library pick bf16/fp16 if available
)
```

The `device` argument tells the pipeline where to put the model. `device=0` means CUDA device 0; on Apple Silicon use `"mps"`; on CPU use `-1` or `"cpu"`. The `torch_dtype="auto"` instructs the library to use the precision specified in the model’s config (most modern checkpoints declare `bfloat16`, which roughly halves memory versus `float32` at a tiny accuracy cost).

Pipelines accept either a single input or a list. Passing a list is more efficient because the inputs get batched. You can also control batch size explicitly with `batch_size=`:

```python
texts = ["Great product!", "Worst purchase ever.", "It was okay."]
results = classifier(texts, batch_size=8)
# [{'label': 'positive', 'score': 0.98},
#  {'label': 'negative', 'score': 0.97},
#  {'label': 'neutral',  'score': 0.71}]
```

Tasks supported by `pipeline()` include `text-classification` (a.k.a. `sentiment-analysis`), `token-classification` (a.k.a. `ner`), `question-answering`, `fill-mask`, `summarization`, `translation`, `text-generation`, `text2text-generation`, `zero-shot-classification`, `feature-extraction` (just returns the last hidden state), `image-classification`, `object-detection`, `image-segmentation`, `depth-estimation`, `automatic-speech-recognition`, `audio-classification`, `text-to-audio`, `image-to-text`, and `visual-question-answering`. Each accepts the appropriate input type and returns task-appropriate output dicts.

Here is what each looks like at the input/output level so you have a concrete picture:

For **`text-generation`**, you pass a prompt string and get back continuation text:

```python
gen = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B", device=0)
gen("The capital of France is", max_new_tokens=20, do_sample=False)
# [{'generated_text': 'The capital of France is Paris. Paris is also the largest city in France...'}]
```

For **`ner`** (named-entity recognition, technically token-classification), you get back a list of detected spans with their entity types:

```python
ner = pipeline("ner", aggregation_strategy="simple")
ner("Khaled works at Commonwealth Bank in Sydney.")
# [{'entity_group': 'PER', 'score': 0.99, 'word': 'Khaled', 'start': 0,  'end': 6},
#  {'entity_group': 'ORG', 'score': 0.97, 'word': 'Commonwealth Bank', 'start': 16, 'end': 33},
#  {'entity_group': 'LOC', 'score': 0.99, 'word': 'Sydney', 'start': 37, 'end': 43}]
```

The `aggregation_strategy="simple"` argument is essential: without it you get back one entry per *sub-word token* rather than per word, which is almost never what you want. The strategy merges adjacent sub-word tokens that share an entity type back into whole-word spans.

For **`question-answering`**, you pass a dict with `question` and `context`:

```python
qa = pipeline("question-answering")
qa({"question": "What language is HF Transformers written in?",
    "context": "Hugging Face Transformers is a Python library that supports PyTorch, TensorFlow, and JAX."})
# {'score': 0.94, 'start': 33, 'end': 39, 'answer': 'Python'}
```

For **`zero-shot-classification`**, you pass text plus a list of candidate labels and the pipeline returns a ranked list:

```python
zsc = pipeline("zero-shot-classification")
zsc("I need to refund this purchase",
    candidate_labels=["billing", "shipping", "technical support", "compliment"])
# {'sequence': 'I need to refund...', 
#  'labels': ['billing', 'shipping', 'technical support', 'compliment'],
#  'scores': [0.87, 0.07, 0.04, 0.02]}
```

The pipeline API is intentionally lossy — it hides intermediate tensors. That is exactly the right tool when you want to ship a quick demo or a one-off inference script. As soon as you need batched throughput at scale, custom preprocessing, or fine-tuning, you graduate to the lower-level Auto classes described next.

-----

## 4. Tokenizers in Depth

A tokenizer is a deterministic function that maps a string to a list of integer IDs (and back). Different models use different tokenizers — BERT uses WordPiece, GPT-2 uses byte-pair encoding (BPE), T5 and Llama use SentencePiece variants. You should never mix tokenizers across models; always load the one that ships with the checkpoint.

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("bert-base-uncased")
```

The library detects the tokenizer type from `tokenizer_config.json` and `tokenizer.json` in the checkpoint, and returns the appropriate class. There are two implementations behind the scenes: a pure-Python `PreTrainedTokenizer` (slow but easy to extend) and a Rust-backed `PreTrainedTokenizerFast` (an order of magnitude faster, returns extra information like character-to-token offsets). `AutoTokenizer` prefers the fast version when available, falling back to the slow version otherwise. You can force the choice with `use_fast=True/False`.

Calling the tokenizer on a string returns a `BatchEncoding`, which is a dict-like object:

```python
out = tok("Hello, world!", return_tensors="pt")
# {'input_ids':      tensor([[ 101, 7592, 1010, 2088, 999,  102]]),
#  'token_type_ids': tensor([[   0,    0,    0,    0,   0,    0]]),
#  'attention_mask': tensor([[   1,    1,    1,    1,   1,    1]])}
```

Three things just happened. First, the text was split into sub-word tokens — `["[CLS]", "hello", ",", "world", "!", "[SEP]"]`. Note the `[CLS]` and `[SEP]` special tokens that BERT-style models prepend and append; the tokenizer adds them automatically because they are declared in the tokenizer’s config as the model’s required special tokens. Second, each sub-word string was mapped to its integer ID via the tokenizer’s vocabulary. Third, the IDs were wrapped in a PyTorch tensor because we requested `return_tensors="pt"` (the alternatives are `"tf"` for TensorFlow, `"np"` for NumPy, or omitting the argument to get plain Python lists).

The keys of the returned dict are exactly the keyword arguments the model’s `forward` method accepts. This is not a coincidence — the tokenizer’s job is to produce model-ready inputs. The `attention_mask` is `1` for real tokens and `0` for padding tokens (we’ll see padding shortly). The `token_type_ids` distinguishes the first and second sentences in tasks like question answering; for single-sentence input it’s all zeros.

The `[CLS]` token at the start is a learned summary token that BERT-style classification heads read for sentence-level decisions. The `[SEP]` token marks sentence boundaries. Different model families use different special tokens — Llama uses a `<s>` BOS (beginning-of-sequence) token; T5 uses no BOS and an `</s>` EOS; GPT-2 uses neither by default and just BPE-encodes the text directly. The point is that the tokenizer handles this for you — you pass plain text, you get model-correct IDs.

When you have multiple inputs of different lengths you need to pad them to a common length so they can stack into a single tensor:

```python
batch = tok(
    ["Hello, world!", "This is a much longer sentence with more tokens."],
    padding=True,         # pad shorter sequences to the longest in the batch
    truncation=True,      # truncate sequences longer than max_length
    max_length=512,       # the cap (defaults to model's max position embeddings)
    return_tensors="pt",
)
batch["input_ids"].shape   # torch.Size([2, 12])
batch["attention_mask"]    # tensor([[1,1,1,1,1,1,0,0,0,0,0,0],
                           #         [1,1,1,1,1,1,1,1,1,1,1,1]])
```

The shorter sentence was padded with `[PAD]` tokens at the end and its attention mask is zero there. The model will see the padding tokens but the attention mask tells the attention layers to ignore them, so the result is the same as if the shorter sentence had been processed alone.

`padding` accepts three useful values. `True` or `"longest"` pads to the longest sequence in the batch (the most common choice). `"max_length"` pads to the value of `max_length` regardless of batch contents (useful when you want consistent shapes across batches, for example with `torch.compile`). `False` or `"do_not_pad"` returns variable-length sequences and is what you want when using a `DataCollator` to batch later.

To go the other direction, from IDs back to text:

```python
tok.decode([101, 7592, 1010, 2088, 999, 102])
# '[CLS] hello, world! [SEP]'

tok.decode([101, 7592, 1010, 2088, 999, 102], skip_special_tokens=True)
# 'hello, world!'

tok.batch_decode(generated_ids, skip_special_tokens=True)
# list of strings, one per row
```

A common operation when generating text is to find the index of the EOS (end-of-sequence) token to know where to stop reading. The tokenizer exposes useful identifiers: `tok.pad_token_id`, `tok.eos_token_id`, `tok.bos_token_id`, `tok.unk_token_id`, `tok.cls_token_id`, `tok.sep_token_id`, `tok.mask_token_id`. Not all of these are defined for every model.

A pitfall worth flagging: GPT-2’s tokenizer has no pad token by default. If you try to batch-pad GPT-2 inputs the tokenizer will error. The standard workaround is `tok.pad_token = tok.eos_token` — reuse EOS as PAD. This works because you’ll set the attention mask anyway, so the model ignores the padded positions regardless of which token sits there.

For tokenizer-fast users, the encoding also carries character offsets and word IDs, which are invaluable for token-classification post-processing:

```python
enc = tok("Hello, world!", return_offsets_mapping=True)
enc["offset_mapping"]
# [(0,0), (0,5), (5,6), (7,12), (12,13), (0,0)]
# Each tuple is (char_start, char_end) in the original string for that token.
# (0,0) is used for special tokens that don't correspond to input characters.
```

This is how the `ner` pipeline maps model predictions back to character spans in your original text.

-----

## 5. Models in Depth

Just like `AutoTokenizer`, there is a family of `AutoModel...` classes. The base `AutoModel` returns the bare transformer — input tokens go in, last-layer hidden states come out, with no task-specific head on top. This is what you want for feature extraction, custom downstream heads, or sentence embeddings. The task-specific variants add a randomly-initialized (or pretrained, if the checkpoint has it) head on top:

|Class                               |Head added                             |Use case                                     |
|------------------------------------|---------------------------------------|---------------------------------------------|
|`AutoModel`                         |none — returns hidden states           |embeddings, custom heads                     |
|`AutoModelForSequenceClassification`|linear classifier over `[CLS]`         |sentiment, topic, intent                     |
|`AutoModelForTokenClassification`   |per-token linear classifier            |NER, POS tagging                             |
|`AutoModelForQuestionAnswering`     |two linear heads (span start/end)      |extractive QA                                |
|`AutoModelForMaskedLM`              |LM head over vocab for masked positions|BERT-style fill-in-the-blank, MLM pretraining|
|`AutoModelForCausalLM`              |LM head over vocab for next token      |GPT-style generation, all modern LLMs        |
|`AutoModelForSeq2SeqLM`             |encoder-decoder with LM head           |T5, BART, mT5 — translation, summarization   |
|`AutoModelForImageClassification`   |classifier head                        |ViT, DINOv2 with labels                      |
|`AutoModelForObjectDetection`       |detection head                         |DETR, YOLOS                                  |
|`AutoModelForVision2Seq`            |vision encoder + text decoder          |image captioning, VLMs                       |

There is one core consistency rule: whichever class you instantiate must match the checkpoint’s purpose. If the checkpoint is `distilbert-base-uncased-finetuned-sst-2-english` (a sentiment classifier), loading it with `AutoModelForSequenceClassification` recovers the trained classification head; loading it with `AutoModel` discards that head and gives you just the encoder. Loading it with `AutoModelForTokenClassification` would warn that the classification head’s weights don’t match and randomly initialize a new head. You can do that intentionally when fine-tuning the base encoder for a different task — see the fine-tuning section.

A complete inference example using the low-level Auto API:

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

name = "distilbert-base-uncased-finetuned-sst-2-english"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForSequenceClassification.from_pretrained(name).eval().to("cuda")

inputs = tok(
    ["I love this!", "I hate this."],
    return_tensors="pt", padding=True, truncation=True,
).to("cuda")

with torch.no_grad():
    outputs = model(**inputs)

logits = outputs.logits           # tensor of shape (2, 2)
probs  = logits.softmax(dim=-1)   # rowwise softmax
labels = probs.argmax(dim=-1)     # most-likely class index per row

# Convert indices to human labels using model.config.id2label:
[model.config.id2label[i.item()] for i in labels]   # ['POSITIVE', 'NEGATIVE']
```

A few things are worth dwelling on here. The model returned by `from_pretrained` is in **training mode** by default (dropout active, batch-norm tracking running stats). You call `.eval()` to switch to **inference mode**. Forgetting this is a classic source of non-deterministic inference results when the model contains dropout. The `torch.no_grad()` context manager tells PyTorch not to build the autograd graph during the forward pass, which saves significant memory; for inference you always want this (or its equivalent `torch.inference_mode()`).

The `outputs` object is a dataclass-like container called a `ModelOutput`. You access fields by attribute (`outputs.logits`) or by string key (`outputs["logits"]`). Standard fields across model types include `loss` (when you pass `labels=`), `logits` (raw pre-softmax scores), `hidden_states` (tuple of per-layer hidden state tensors, available if `output_hidden_states=True` was passed), `attentions` (tuple of per-layer attention weights, available if `output_attentions=True`). The base `AutoModel` returns a different shape: `last_hidden_state` of shape `(batch, seq, hidden)` plus optional `pooler_output` (for BERT-family models, the `[CLS]` representation passed through one tanh layer — present mostly for legacy reasons; people usually mean-pool `last_hidden_state` instead).

Two `from_pretrained` arguments deserve a special call-out because they have changed the way modern models are loaded:

`dtype="auto"` (formerly `torch_dtype="auto"`) tells the library to honor whatever precision is declared in the checkpoint config. For most modern releases this is `bfloat16`, which uses 2 bytes per weight (instead of 4 for float32) and runs faster on Ampere+ GPUs. The accuracy hit is essentially zero for inference. Without this argument, the model defaults to `float32` and a 7B-parameter model occupies 28 GB instead of 14 GB.

`device_map="auto"` triggers the `accelerate` library to inspect your hardware (GPUs and their VRAM, plus system RAM) and place the model’s layers across devices. For a single-GPU machine this is equivalent to `.to("cuda")`. For a machine with multiple GPUs it distributes layers in order across them. If the model doesn’t fit even across all GPUs it spills to CPU RAM (and, in extreme cases, disk), which is slow but enables you to at least run a model larger than your VRAM. For training you typically use `device_map="auto"` with `accelerate` configured appropriately, or omit it and use the `Trainer`’s built-in distribution.

```python
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    dtype="auto",
    device_map="auto",
)
```

This single line loads a 1B-parameter Llama model in bfloat16 onto the right device(s) for your machine. That’s the modern incantation.

-----

## 6. The Generate API — How Autoregressive Models Produce Text

Encoder-only models like BERT produce fixed-size outputs and a single `forward()` call is all the inference you ever need. Decoder-only models like GPT, Llama, Qwen, and Mistral, and encoder-decoder models like T5 and BART, are **autoregressive**: they produce one token at a time, and you must call them in a loop, feeding back each generated token as the next input. The library hides this loop behind the `model.generate()` method.

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B")
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B", dtype="auto", device_map="auto"
)

prompt = "The three laws of thermodynamics are:"
inputs = tok(prompt, return_tensors="pt").to(model.device)

out_ids = model.generate(
    **inputs,
    max_new_tokens=128,     # cap on tokens to produce (not counting the prompt)
    do_sample=True,         # if False -> greedy decoding (deterministic)
    temperature=0.7,        # softens/sharpens the distribution before sampling
    top_p=0.9,              # nucleus sampling: keep smallest set of tokens whose
                            # cumulative probability >= top_p, renormalize, sample
    top_k=50,               # also keep only top_k highest-probability tokens
    repetition_penalty=1.1, # >1 penalizes already-generated tokens
    pad_token_id=tok.eos_token_id,
)

print(tok.decode(out_ids[0], skip_special_tokens=True))
```

Several distinct decoding strategies hide inside this one call. **Greedy** decoding (`do_sample=False`, no beam search) picks the argmax at every step — fully deterministic, often dull and repetitive. **Beam search** (`num_beams=N`) maintains `N` partial hypotheses at each step and keeps the top-`N` continuations; better for tasks with a “right answer” like translation, but it tends to produce bland text for open-ended generation. **Sampling** (`do_sample=True`) samples from the predicted distribution at each step; `temperature`, `top_k`, and `top_p` shape that distribution before sampling. **Contrastive search** and **assisted/speculative decoding** are more recent additions for quality or speed.

The temperature parameter divides the logits before applying softmax: a temperature of 1.0 leaves them unchanged, less than 1.0 sharpens the distribution (more confident, more greedy-like), and greater than 1.0 flattens it (more random). A temperature of 0 is undefined mathematically but the library treats it as a special case equivalent to greedy. Typical values for open-ended creative generation are 0.7–1.0; for factual completion, 0.0–0.3.

`top_k=50` means: at each step, restrict the candidate set to the 50 tokens with highest probability, renormalize their probabilities, and sample from that. `top_p=0.9` means: at each step, find the smallest set of top-ranked tokens whose probabilities sum to at least 0.9, renormalize, and sample from that. The two are typically combined — top_k as a safety floor against the very long tail, top_p as the main filter. Setting `top_p=1.0` and `top_k=0` disables them entirely.

`repetition_penalty` divides the logit of any token that has already appeared by the given factor (the formulation is slightly more nuanced for negative logits but that’s the intuition). Values in `[1.05, 1.2]` are common; too high and the model avoids natural repetition like the words “the” and “a”.

**Chat templates** are the modern way to format input for instruction-tuned models. Every chat model on the Hub now ships with a Jinja template that knows how to wrap a conversation into the exact special-token format the model was trained on. You should never hand-construct these strings — use `tokenizer.apply_chat_template`:

```python
messages = [
    {"role": "system", "content": "You are a concise assistant."},
    {"role": "user",   "content": "What is the boiling point of water at sea level?"},
]
inputs = tok.apply_chat_template(
    messages,
    add_generation_prompt=True,   # appends the assistant-turn-start marker
    return_tensors="pt",
).to(model.device)

out = model.generate(inputs, max_new_tokens=64, do_sample=False)
# Slice off the prompt portion to get just the new tokens:
new_tokens = out[0, inputs.shape[-1]:]
print(tok.decode(new_tokens, skip_special_tokens=True))
```

`add_generation_prompt=True` is the crucial flag — without it the template produces a string ending with the user’s turn, and the model will try to continue the user’s turn rather than reply as the assistant. Always pass `True` for inference; for training you pass `False` so that the assistant’s reply is included in the sequence (and labels can be set accordingly).

A subtle but important detail: `model.generate` returns the **entire** token sequence including the prompt. To get just the new tokens you slice off `inputs.shape[-1]` from the front, as shown above. Forgetting this is a common bug (“the model keeps repeating my prompt back at me”).

-----

## 7. The Datasets Library — Loading and Processing Data

The `datasets` library is the standard way to get tabular, text, image, and audio data into a form the Trainer can consume. Its API mirrors `transformers`: `load_dataset("repo_id")` downloads and caches a dataset from the Hub, returning a `DatasetDict` (with `"train"`, `"validation"`, `"test"` splits) or a single `Dataset` if there is only one split.

```python
from datasets import load_dataset

ds = load_dataset("imdb")
ds
# DatasetDict({
#     train:      Dataset({features: ['text', 'label'], num_rows: 25000})
#     test:       Dataset({features: ['text', 'label'], num_rows: 25000})
#     unsupervised: Dataset({features: ['text', 'label'], num_rows: 50000})
# })

ds["train"][0]
# {'text': 'I rented I AM CURIOUS-YELLOW...', 'label': 0}
```

`Dataset` objects are backed by Apache Arrow files on disk, so they are memory-mapped — even a 1-TB dataset doesn’t load into RAM. You index them like Python lists and iterate over them, and they integrate directly with PyTorch DataLoader.

The core operation is `.map()`, which applies a function to every example (or batch of examples) and produces a new column. To tokenize a text dataset:

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tok(batch["text"], truncation=True, max_length=256)

ds_tok = ds.map(tokenize, batched=True, remove_columns=["text"])
# Now each example has 'input_ids', 'attention_mask', 'label' — and no 'text'.
```

`batched=True` is important for speed: the function receives a dict of lists (one list per column, length up to ~1000 by default) instead of one example at a time, and `tok` happily accepts a list and tokenizes everything in one Rust call. The speedup is typically 100×. `remove_columns=["text"]` drops the raw text — the model’s `forward` method only accepts `input_ids` and `attention_mask`, and the Trainer (helpfully) raises if you leave extra columns on the dataset.

Two other operations to know:

`.filter()` keeps only examples matching a predicate. `.train_test_split(test_size=0.1)` creates a held-out split when the dataset doesn’t ship with one. Cached results live alongside the original dataset under `~/.cache/huggingface/datasets`, so re-running the same `.map` call returns instantly.

You can also build a `Dataset` from a Python dict, a list, a pandas DataFrame, a CSV/JSON file, or a directory of Parquet files — `Dataset.from_dict`, `Dataset.from_list`, `Dataset.from_pandas`, `load_dataset("csv", data_files=...)`. This is how you bring your own data.

The matching piece on the Trainer side is a **data collator**: a function that takes a list of dicts (the dataset items) and stacks them into a batched tensor dict, applying padding on the fly. The default collators for common tasks are:

`DataCollatorWithPadding(tokenizer)` is the workhorse for classification. It dynamically pads each batch to its own longest example — far more efficient than padding everything to a global maximum during tokenization.

`DataCollatorForLanguageModeling(tokenizer, mlm=True)` is for masked-language-model pretraining; it randomly masks 15% of tokens in each batch.

`DataCollatorForLanguageModeling(tokenizer, mlm=False)` is for causal LM fine-tuning; it copies `input_ids` to `labels` and shifts internally (the model handles the shift).

`DataCollatorForSeq2Seq(tokenizer, model=model)` handles encoder-decoder padding for the encoder side and shifted-right decoder labels for the decoder side.

```python
from transformers import DataCollatorWithPadding
collator = DataCollatorWithPadding(tokenizer=tok)
# Now pass collator=collator to the Trainer.
```

-----

## 8. Fine-Tuning with the Trainer API

The `Trainer` class wraps an entire training loop — forward, loss, backward, optimizer step, gradient accumulation, mixed precision, distributed training, evaluation, checkpointing, logging — behind one object. For 95% of supervised fine-tuning workloads this is what you should use. Writing your own loop is reasonable only when you need something the Trainer can’t express (very custom losses, complex curriculum schedules, RL).

The basic shape:

```python
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, DataCollatorWithPadding,
)
from datasets import load_dataset
import evaluate
import numpy as np

# 1) Data
ds = load_dataset("imdb")
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=256),
            batched=True, remove_columns=["text"])
small_train = ds["train"].shuffle(seed=42).select(range(2000))
small_eval  = ds["test"].shuffle(seed=42).select(range(500))

# 2) Model — note num_labels matches the task
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2,
    id2label={0: "neg", 1: "pos"},
    label2id={"neg": 0, "pos": 1},
)

# 3) Metric
acc = evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return acc.compute(predictions=preds, references=labels)

# 4) TrainingArguments — every knob the Trainer exposes
args = TrainingArguments(
    output_dir="distilbert-imdb",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    learning_rate=5e-5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    gradient_accumulation_steps=1,
    gradient_checkpointing=False,
    bf16=True,                       # mixed precision on Ampere+
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    logging_steps=50,
    report_to="none",                # "wandb", "tensorboard", etc.
    seed=42,
)

# 5) Wire it up
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=small_train,
    eval_dataset=small_eval,
    processing_class=tok,            # newer arg name; replaces tokenizer=
    data_collator=DataCollatorWithPadding(tok),
    compute_metrics=compute_metrics,
)

trainer.train()
trainer.evaluate()
trainer.save_model("distilbert-imdb/final")
```

Let me walk through what each piece is doing.

The `output_dir` is the only required argument — checkpoints, logs, and the optimizer state all go there. `num_train_epochs` and `per_device_train_batch_size` set total training compute. The effective batch size is `per_device_train_batch_size * gradient_accumulation_steps * num_gpus`; `gradient_accumulation_steps` runs the forward and backward `N` times before stepping the optimizer, so you can simulate a large batch on small VRAM at the cost of `N` times the wall-clock per optimizer step. `gradient_checkpointing=True` trades compute for memory by recomputing activations during the backward pass instead of storing them — turn this on when you can’t fit the batch size you want.

`learning_rate=5e-5` is the modal value for fine-tuning encoder models on classification; for full fine-tuning of LLMs typical values are `1e-5` to `2e-5`; for LoRA they can go an order of magnitude higher (`1e-4` to `3e-4`). `warmup_ratio=0.1` means the LR ramps linearly from zero to `learning_rate` over the first 10% of steps, then decays according to `lr_scheduler_type`. `weight_decay=0.01` is standard AdamW weight decay; the Trainer uses AdamW by default (`optim="adamw_torch"`) and you can swap to memory-cheaper optimizers like `"adamw_8bit"` (requires `bitsandbytes`) or `"adafactor"`.

`bf16=True` enables bfloat16 mixed precision, which is the right default on Ampere (A100), Hopper (H100), and consumer RTX 30/40 series. Use `fp16=True` on older cards (V100, T4) that don’t support bf16. `tf32=True` is also worth knowing — it accelerates matmuls on Ampere+ at almost no accuracy cost and is on by default in recent versions.

`eval_strategy="epoch"` runs evaluation at the end of every epoch; alternatives are `"steps"` (with `eval_steps=N`) or `"no"`. `save_strategy` must match `eval_strategy` if you want `load_best_model_at_end=True`. `save_total_limit=2` keeps only the last two checkpoints, deleting older ones to save disk.

`load_best_model_at_end=True` rewinds to the best checkpoint by `metric_for_best_model` after training finishes, so when you `save_model` you save the best, not the last. Without this, early-stopping is also impossible.

The `processing_class=tok` argument is the **modern** way (Transformers 4.46+); older code uses `tokenizer=tok`. Both still work but the new name accommodates models whose preprocessing is an image processor or audio feature extractor — the same Trainer handles all modalities.

`compute_metrics` is a function that receives `(predictions, labels)` from the eval loop and returns a dict. The `evaluate` library hosts standard metrics; for custom metrics you compute them in pure Python and return your own dict.

Once `trainer.train()` runs, you’ll see a live table of training loss, eval loss, eval accuracy, and learning rate. Checkpoints land in `output_dir/checkpoint-NNN/`. After `trainer.save_model("distilbert-imdb/final")` the folder contains everything needed to reload with `AutoModelForSequenceClassification.from_pretrained("distilbert-imdb/final")` and the matching tokenizer.

To push the result to the Hub:

```python
trainer.push_to_hub("your-username/distilbert-imdb")
# or set hub_model_id in TrainingArguments and push_to_hub=True for auto-push
```

-----

## 9. Callbacks, Early Stopping, and Hooks

The Trainer fires events at well-defined points: `on_train_begin`, `on_epoch_begin`, `on_step_begin`, `on_step_end`, `on_evaluate`, `on_save`, `on_log`, `on_train_end`. You can hook into them by subclassing `TrainerCallback` and registering instances via `Trainer(..., callbacks=[MyCallback()])`. The most commonly used built-in callback:

```python
from transformers import EarlyStoppingCallback

trainer = Trainer(
    ...,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
)
```

This stops training when `metric_for_best_model` fails to improve for `patience` consecutive evaluations. It only works when `eval_strategy` is not `"no"` and `load_best_model_at_end=True`.

A custom callback example — log the GPU memory after every step:

```python
from transformers import TrainerCallback
import torch

class GpuMemoryCallback(TrainerCallback):
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step % 50 == 0 and torch.cuda.is_available():
            mem_gb = torch.cuda.max_memory_allocated() / 1e9
            print(f"step {state.global_step}: peak GPU mem = {mem_gb:.2f} GB")
```

For more invasive customization — for example, a non-standard loss — you subclass `Trainer` and override `compute_loss`:

```python
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        # custom class-weighted cross-entropy
        weights = torch.tensor([1.0, 3.0], device=logits.device)
        loss = torch.nn.functional.cross_entropy(logits, labels, weight=weights)
        return (loss, outputs) if return_outputs else loss
```

-----

## 10. The Manual Training Loop — When the Trainer Isn’t Enough

Sometimes you want full control. Here is the same fine-tune written by hand, which is also the best way to understand exactly what the Trainer does:

```python
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    DataCollatorWithPadding, get_linear_schedule_with_warmup,
)
from datasets import load_dataset

tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=2
).to("cuda")

ds = load_dataset("imdb")
ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=256),
            batched=True, remove_columns=["text"])
ds = ds.rename_column("label", "labels")  # the model expects 'labels'
ds.set_format("torch")                    # so DataLoader gives torch tensors

train_loader = DataLoader(
    ds["train"].select(range(2000)), batch_size=16, shuffle=True,
    collate_fn=DataCollatorWithPadding(tok),
)

optim = AdamW(model.parameters(), lr=5e-5, weight_decay=0.01)
num_steps = len(train_loader) * 3
sched = get_linear_schedule_with_warmup(optim, num_warmup_steps=num_steps // 10,
                                        num_training_steps=num_steps)

model.train()
for epoch in range(3):
    for batch in train_loader:
        batch = {k: v.to("cuda") for k, v in batch.items()}
        out = model(**batch)
        out.loss.backward()
        optim.step()
        sched.step()
        optim.zero_grad()
```

That is the entire fine-tuning loop. The Trainer adds, on top of this: mixed precision (`autocast` context), gradient accumulation, distributed sampler swapping for multi-GPU, checkpoint saving and resuming, evaluation, metric tracking, callbacks, logging integrations, and early stopping. None of those are conceptually deep — they are just bookkeeping. The Trainer is just very thorough bookkeeping.

`accelerate` is the middle ground between writing the manual loop and using the Trainer. You write the loop yourself, but wrap a few objects with `accelerator.prepare(...)` and the library handles device placement and distributed coordination:

```python
from accelerate import Accelerator
acc = Accelerator(mixed_precision="bf16")
model, optim, train_loader, sched = acc.prepare(model, optim, train_loader, sched)
for batch in train_loader:
    out = model(**batch)
    acc.backward(out.loss)     # replaces out.loss.backward()
    optim.step(); sched.step(); optim.zero_grad()
```

This same code now runs unchanged on one GPU, multiple GPUs, multiple nodes, or TPUs, controlled by `accelerate config` / `accelerate launch`.

-----

## 11. Saving, Loading, Pushing to the Hub

Three save methods, three slightly different things:

`model.save_pretrained("./mymodel")` writes `config.json` and weight files (typically `model.safetensors`). It does **not** save the tokenizer.

`tokenizer.save_pretrained("./mymodel")` writes the tokenizer files (`tokenizer.json`, `vocab.txt` or equivalent, `tokenizer_config.json`, `special_tokens_map.json`).

`trainer.save_model("./mymodel")` saves both the model and the tokenizer (assuming you passed `processing_class=tok` to the Trainer). This is the one you want for a complete artifact.

Loading is symmetric:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
tok = AutoTokenizer.from_pretrained("./mymodel")
model = AutoModelForSequenceClassification.from_pretrained("./mymodel")
```

Pushing to the Hub requires being logged in (`huggingface-cli login` or `HF_TOKEN`), then any saved checkpoint has a `push_to_hub` method:

```python
model.push_to_hub("your-username/my-classifier")
tok.push_to_hub("your-username/my-classifier")
# Or, from a Trainer:
trainer.push_to_hub("your-username/my-classifier", commit_message="v1")
```

The Trainer also accepts `push_to_hub=True` in `TrainingArguments`, in which case checkpoints are pushed continuously during training, ending with a final clean version. This is convenient and slightly dangerous — public by default unless you set `hub_private_repo=True`.

-----

## 12. Inference at Scale — The Optimization Quick Tour

For production inference the considerations shift from training: latency and throughput dominate. The library and its ecosystem give you several knobs.

**Precision.** Run inference in bf16 or fp16 unless your hardware doesn’t support them; this halves memory and roughly doubles throughput at no quality cost on most modern models. Set `dtype="bfloat16"` (or `"float16"`) at load time.

**Quantization** further reduces precision below the floating-point baseline. Common options:

`bitsandbytes` 8-bit and 4-bit quantize linear layers post-hoc with the LLM.int8() and QLoRA algorithms respectively. Enable at load time with `load_in_8bit=True` or by constructing a `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")` and passing it as `quantization_config=`. 4-bit roughly quarters memory; a 7B model fits in ~5 GB. Inference is slightly slower than bf16 but training (via LoRA) is enabled on consumer GPUs.

GPTQ and AWQ are post-training quantization schemes that produce checkpoint files quantized in advance (so loading is fast and inference is fast). Many popular models have prebuilt `-GPTQ` and `-AWQ` variants on the Hub. Load them with the same `from_pretrained` call — the library detects the quantization config in the checkpoint.

**Flash Attention.** Modern attention kernels (`flash_attention_2`, `sdpa`) compute attention with far less memory and at higher speed. Recent versions of the library default to `sdpa` (the PyTorch built-in) automatically; you can force flash-attention-2 by passing `attn_implementation="flash_attention_2"` to `from_pretrained` (requires the `flash-attn` package).

**KV caching** is on by default for generation: during autoregressive decoding, the key/value tensors for previously-generated tokens are cached so each new token requires only one forward pass over one new position rather than over the entire prefix. You don’t need to do anything — it just happens — but be aware that the cache occupies VRAM proportional to sequence length, so long contexts can OOM even when the model weights fit fine.

**`torch.compile`** wraps the model in a graph-compiled version for further speed. The library is largely compatible: `model = torch.compile(model)` after loading typically yields 20–40% throughput gains for batched inference at the cost of an initial compile delay.

**Dedicated serving frameworks.** When throughput matters more than flexibility, leave `transformers` at the model-loading layer and serve with `vllm` or Hugging Face’s own `text-generation-inference` (TGI). These implement continuous batching, paged attention, and aggressive scheduling that single-process Python inference can’t match.

-----

## 13. Parameter-Efficient Fine-Tuning (LoRA in 50 lines)

Full fine-tuning of a 7B model needs roughly `model_size * 16` bytes of memory because of the optimizer state and gradients (`AdamW` keeps two moments per parameter, plus the gradient itself, plus the master fp32 weights when using mixed precision). LoRA — Low-Rank Adaptation — sidesteps this by freezing the base model and training small low-rank “adapter” matrices added beside selected linear layers. A 7B Llama then needs ~14 GB for weights plus a few hundred MB for the adapter and its optimizer state, fitting on a 16-GB consumer GPU.

The `peft` library provides this on top of `transformers`:

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

base = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    quantization_config=bnb,
    device_map="auto",
)

lora_cfg = LoraConfig(
    r=16,                         # rank of the adapter matrices
    lora_alpha=32,                # scaling factor (effective LR multiplier)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(base, lora_cfg)
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 1,239,814,144 || trainable%: 0.34
```

The `get_peft_model` call freezes every parameter in `base` and injects small `lora_A` and `lora_B` matrices next to each module listed in `target_modules`. The forward pass becomes `output = base_linear(x) + (lora_B @ lora_A) @ x * (alpha / r)`. Only the adapter matrices receive gradients. You then plug this `model` into the Trainer exactly as before; it behaves identically except gradients are computed only for the trainable tenth of a percent.

After training, `model.save_pretrained` writes only the adapter (a few megabytes). At inference you reload it as `PeftModel.from_pretrained(base, "path/to/adapter")`. Or you can permanently merge: `model = model.merge_and_unload()` returns a normal `transformers` model with the LoRA delta folded into the base weights.

-----

## 14. Common Pitfalls and Gotchas

The model and tokenizer must match. Loading a tokenizer from checkpoint A with a model from checkpoint B produces logits that are statistically random. If you change tokenizers you must retrain.

The Trainer expects the label column to be named `"labels"`, not `"label"`. The `datasets` library typically yields `"label"`. Use `ds = ds.rename_column("label", "labels")` or rely on the data collator to do this for you.

`model.eval()` matters. Dropout and BatchNorm misbehave in training mode during inference, producing non-deterministic outputs.

`with torch.no_grad():` matters for inference memory. Without it, the autograd graph silently consumes VRAM proportional to model depth.

Padding direction matters for autoregressive models. Encoder models like BERT can be padded on either side; decoder models like Llama must be padded on the **left** because attention is causal and right-padding shifts the meaningful tokens out of the model’s “view” at the EOS position. `tokenizer.padding_side = "left"` is required when batching prompts for generation. Forgetting this produces garbled outputs.

The pipeline’s `device` argument is an integer (`0` = first GPU), but the model’s `.to()` and the model’s `device_map` use strings (`"cuda"`, `"cuda:0"`). They mean the same things; the inconsistency is historical.

`generate()` returns prompt+continuation; slice the prompt off if you want only the new tokens.

Mixed precision training (`bf16=True`) on a CPU-only environment silently does nothing useful and can be slower. Check `torch.cuda.is_available()` and pick precision accordingly.

`gradient_accumulation_steps` does not save VRAM during the forward pass — it saves you the optimizer step. Memory is still proportional to per-device batch size. To save forward-pass memory use `gradient_checkpointing=True` and a smaller per-device batch.

The default Adam-family optimizers (`adamw_torch`) keep two fp32 momentum tensors per parameter, doubling the memory needed beyond the weights themselves. Use `optim="adamw_8bit"` or `optim="adafactor"` to cut this.

When fine-tuning on a domain very different from the pretraining corpus (medical, legal, code), the tokenizer may produce many `[UNK]` tokens or split common words badly, hurting quality. Inspect with `tokenizer.tokenize(text)` before launching long training runs.

The Hub gates some models (Llama, Mistral instruction variants). The first `from_pretrained` call on a gated model fails with a permission error if you haven’t accepted the license in your browser and aren’t logged in.

-----

## 15. A Complete End-to-End Example

To consolidate, here is a fully runnable end-to-end pipeline: fine-tune a small encoder on a binary text-classification task and serve the result through a pipeline.

```python
import numpy as np
import torch
import evaluate
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, DataCollatorWithPadding,
    EarlyStoppingCallback, pipeline,
)

MODEL = "distilbert-base-uncased"
OUT   = "./distilbert-imdb-finetuned"

# 1. Load and split the dataset
raw = load_dataset("imdb")
raw["train"] = raw["train"].shuffle(seed=42).select(range(5000))
raw["test"]  = raw["test"].shuffle(seed=42).select(range(1000))

# 2. Tokenize
tok = AutoTokenizer.from_pretrained(MODEL)
def preprocess(batch):
    return tok(batch["text"], truncation=True, max_length=256)
ds = raw.map(preprocess, batched=True, remove_columns=["text"])
ds = ds.rename_column("label", "labels")

# 3. Model
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL, num_labels=2,
    id2label={0: "negative", 1: "positive"},
    label2id={"negative": 0, "positive": 1},
)

# 4. Metric
acc = evaluate.load("accuracy")
f1  = evaluate.load("f1")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        **acc.compute(predictions=preds, references=labels),
        **f1.compute(predictions=preds, references=labels, average="binary"),
    }

# 5. Training arguments
args = TrainingArguments(
    output_dir=OUT,
    num_train_epochs=3,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=64,
    learning_rate=5e-5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    bf16=torch.cuda.is_available(),
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    logging_steps=25,
    report_to="none",
    seed=42,
)

# 6. Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds["train"],
    eval_dataset=ds["test"],
    processing_class=tok,
    data_collator=DataCollatorWithPadding(tok),
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=1)],
)

# 7. Train & save
trainer.train()
metrics = trainer.evaluate()
print(metrics)
trainer.save_model(OUT)

# 8. Reload & serve via pipeline
clf = pipeline(
    "text-classification",
    model=OUT,
    tokenizer=OUT,
    device=0 if torch.cuda.is_available() else -1,
)
print(clf([
    "This movie was an absolute masterpiece, easily my favorite of the year.",
    "I want my two hours back. Avoid at all costs.",
]))
# [{'label': 'positive', 'score': 0.9994}, {'label': 'negative', 'score': 0.9982}]
```

Every concept in this tutorial appears here in production form. Reading this script top to bottom and being able to articulate why each line is there is a reasonable benchmark for fluency in the library.

-----

## 16. Beyond — What Else Lives in the Ecosystem

A short reference of adjacent libraries you will inevitably need:

`trl` (Transformers Reinforcement Learning) provides `SFTTrainer` for supervised fine-tuning with simpler defaults than `Trainer`, plus `DPOTrainer`, `PPOTrainer`, `GRPOTrainer` for preference-based and RL fine-tuning. Builds on `transformers` and `peft`.

`sentence-transformers` is a separate library specialized for producing sentence-level embeddings (semantic search, clustering). It builds on `transformers` but its models output a single vector per input rather than a sequence.

`diffusers` is the sister library for diffusion models (Stable Diffusion, FLUX). Same `from_pretrained` pattern, different pipelines (e.g. `StableDiffusionPipeline`).

`optimum` adds hardware-specific backends — ONNX Runtime, Intel OpenVINO, AWS Neuron, NVIDIA TensorRT — for inference acceleration without rewriting your code.

`tokenizers` (lowercase) is the Rust library that backs `PreTrainedTokenizerFast`. You only deal with it directly when training a new tokenizer from a corpus.

The Hub itself supports much more than weight downloads: dataset hosting, Spaces (Gradio/Streamlit demos), model cards (the `README.md` of a checkpoint, which the library will read for default values like `pipeline_tag`), and Inference Endpoints (managed serverless inference).

-----

## 17. Closing — A Mental Cheat Sheet

If you remember nothing else, remember this:

A checkpoint is a folder. `from_pretrained("name")` downloads it and instantiates the appropriate class. There are three classes per checkpoint that travel together: a config, a tokenizer (or processor), and a model. `AutoClass` abstracts over model families so you don’t have to know which one a checkpoint belongs to. `pipeline` bundles them with task-specific pre/post-processing for one-line inference. The `Trainer` bundles them with a training loop for fine-tuning. The `datasets` library produces inputs the Trainer can consume. The `accelerate` library handles devices. The `peft` library makes fine-tuning fit on small GPUs. Everything else is a parameter.

You now have the full surface area of the library in your head. The rest is practice and reading specific model cards for their quirks.