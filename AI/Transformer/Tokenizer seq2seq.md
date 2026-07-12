# Seq2Seq Translation, Tokenizers, Embeddings, and Extending Vocabularies

## Core Mental Model

A seq2seq translation model has two different systems that are often confused:

```text
Raw text
→ tokenizer
→ token IDs
→ embedding layer
→ vectors
→ Transformer model
→ output token IDs
→ tokenizer decode
→ translated text
```

The tokenizer does **not** create vectors.

The tokenizer does:

```text
text → tokens → token IDs
```

The model’s embedding layer does:

```text
token IDs → vectors
```

The Transformer does:

```text
source-side vectors → target-side token predictions
```

For example:

```text
"I love you"
→ tokenizer
→ [45, 812, 91]
→ embedding layer
→ vectors
→ Transformer
→ [77, 1302, 508]
→ tokenizer decode
→ "Ich liebe dich"
```

The tokenizer does not translate.  
The embedding layer does not translate by itself.  
The Transformer learns the translation.

---

## Seq2Seq Translation Model Structure

In a seq2seq Transformer translation model, there are two main sides:

```text
Encoder: reads the source sentence
Decoder: generates the target sentence
```

Example: English → German

```text
English sentence → encoder
decoder → German sentence
```

For a training example:

```text
Source: "I love you"
Target: "Ich liebe dich"
```

The tokenizer converts both into IDs:

```text
"I love you"     → [10, 25, 90]
"Ich liebe dich" → [300, 411, 502]
```

The model learns:

```text
[10, 25, 90] → [300, 411, 502]
```

That means:

```text
"I love you" → "Ich liebe dich"
```

The source IDs go to the encoder.  
The target IDs are used as the correct answer for the decoder.

---

## What a Tokenizer Actually Is

A tokenizer is a mapping system between text and integer IDs.

It usually has:

```text
token string → token ID
token ID → token string
```

Example vocabulary:

```text
0   → <pad>
1   → <unk>
2   → <s>
3   → </s>
122 → love
300 → Ich
411 → liebe
502 → dich
```

So if the vocabulary says:

```text
love → 122
```

then every time the tokenizer sees the token `love`, it maps it to:

```text
love → 122
```

And decoding can map it back:

```text
122 → love
```

Important: the vocabulary contains **tokens**, not always full words.

A word may be one token:

```text
love → [122]
```

Or multiple subword tokens:

```text
loving → ["lov", "ing"] → [810, 55]
```

So this is correct:

```text
A trained tokenizer has IDs for all tokens in its vocabulary.
```

But this is not always correct:

```text
Every word has exactly one ID.
```

Many modern tokenizers use subwords, so words can be split into smaller pieces.

---

## Word Tokens vs Subword Tokens

Modern tokenizers usually do not rely only on full words.

For example:

```text
translation
translator
translated
translating
```

A subword tokenizer may learn pieces like:

```text
translat
ion
or
ed
ing
```

Then it can represent:

```text
translation → ["translat", "ion"]
translator  → ["translat", "or"]
translated  → ["translat", "ed"]
translating → ["translat", "ing"]
```

This helps with rare words, new forms, typos, and morphologically rich languages.

For example, if the user writes a typo:

```text
lovk
```

The tokenizer does not automatically correct it to `love`.

Instead, it tries to represent it using known pieces:

```text
lovk → ["lov", "k"]
```

or:

```text
lovk → ["l", "o", "v", "k"]
```

The tokenizer handles the typo mechanically.

The model may infer from context that:

```text
I lovk you
```

probably means:

```text
I love you
```

But that inference happens inside the Transformer, not inside the tokenizer.

---

## Training a Tokenizer

People often just **use** tokenizers from pretrained models, but tokenizers can also be trained.

Tokenizer training means:

```text
large text corpus
→ learn useful text pieces
→ build vocabulary
→ assign IDs
```

It does not mean neural network training in the same way as Transformer training.

For example, suppose the tokenizer training corpus contains:

```text
I love cats
I love dogs
The cat is sleeping
The dog is running
Translation is useful
```

The tokenizer may learn pieces like:

```text
I
love
cat
dog
s
ing
translation
is
useful
the
```

Then it builds a vocabulary:

```text
0 → <pad>
1 → <unk>
2 → I
3 → love
4 → cat
5 → dog
6 → s
7 → ing
8 → translation
```

After this, the tokenizer is considered trained.

Using the tokenizer later means:

```text
"I love dogs"
→ ["I", "love", "dog", "s"]
→ [2, 3, 5, 6]
```

So there are two phases:

```text
Tokenizer training:
text corpus → vocabulary + splitting rules

Tokenizer usage:
new sentence → token IDs
```

---

## Tokenizer vs Embedding Layer

The tokenizer has no embedding vectors.

The tokenizer owns this:

```text
"love" → 122
```

The model owns this:

```text
122 → [0.21, -0.44, 0.09, ...]
```

So:

```text
Tokenizer:
text ↔ IDs

Embedding layer:
IDs → vectors
```

If the tokenizer has 32,000 tokens, the model usually needs an embedding matrix with 32,000 rows.

Example:

```text
tokenizer vocabulary size = 32,000
hidden size = 512

embedding matrix shape = 32,000 × 512
```

That means:

```text
token ID 0     → vector of size 512
token ID 1     → vector of size 512
token ID 122   → vector of size 512
...
```

The ID is fixed by the tokenizer.  
The vector is learned by the model during training.

Important distinction:

```text
Tokenizer training:
decides that "love" is ID 122

Model training:
learns what vector ID 122 should have
```

The tokenizer does not understand the meaning of `love`.

The model learns a useful vector for ID `122` from data and gradients.

---

## One Tokenizer or Two Tokenizers for Translation?

For a seq2seq translation model, there are two possible designs.

### Design 1: One Shared Tokenizer

You train one tokenizer on both languages.

For English → German:

```text
English text + German text
→ one shared tokenizer
```

The shared vocabulary may contain:

```text
10  → I
25  → love
90  → you
300 → Ich
411 → liebe
502 → dich
```

Then:

```text
English input → same tokenizer → encoder
German output → same tokenizer → decoder
```

Example:

```text
"I love you"     → [10, 25, 90]
"Ich liebe dich" → [300, 411, 502]
```

This is common and simple, especially with subword tokenizers.

### Design 2: Separate Source and Target Tokenizers

You can also train one tokenizer for the source language and another for the target language.

Example:

```text
English tokenizer:
10 → I
25 → love
90 → you

German tokenizer:
10 → Ich
25 → liebe
90 → dich
```

The same ID can mean different things depending on the tokenizer.

That is not automatically wrong, but it means the system must keep the source and target vocabularies separate.

Pipeline:

```text
English text
→ English tokenizer
→ English IDs
→ encoder

German text
→ German tokenizer
→ German IDs
→ decoder
```

This can work, but for many modern Transformer translation setups, one shared subword tokenizer is easier and often preferred.

Practical rule:

```text
Training from scratch:
usually train one tokenizer on all involved languages.

Fine-tuning a pretrained model:
use the tokenizer that belongs to that pretrained model.
```

---

## Hugging Face Names

In Hugging Face Transformers, the tokenizer is usually loaded with:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("model-name")
```

For seq2seq translation models:

```python
from transformers import AutoModelForSeq2SeqLM

model = AutoModelForSeq2SeqLM.from_pretrained("model-name")
```

For example:

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "Helsinki-NLP/opus-mt-en-de"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
```

The tokenizer does:

```python
inputs = tokenizer("I love you", return_tensors="pt")
print(inputs["input_ids"])
```

The model’s embedding layer can be accessed with:

```python
embedding_layer = model.get_input_embeddings()
```

The embedding layer converts token IDs into vectors:

```python
vectors = embedding_layer(inputs["input_ids"])
print(vectors.shape)
```

Mapping:

```text
AutoTokenizer
= text → token IDs

AutoModelForSeq2SeqLM
= encoder-decoder translation model

model.get_input_embeddings()
= embedding layer inside the model

model.resize_token_embeddings(len(tokenizer))
= resize model embedding table after tokenizer vocabulary changes
```

---

## Training a Seq2Seq Translator From Scratch

Training a translator from scratch requires:

```text
1. Parallel translation data
2. Tokenizer training
3. Model configuration
4. Dataset tokenization
5. Model training
6. Inference
```

Example data:

```text
source,target
I love you,Ich liebe dich
The house is big,Das Haus ist groß
I am learning,Ich lerne
```

Each example has:

```text
source = sentence in the input language
target = correct translation in the output language
```

For English → German:

```text
source = English
target = German
```

The training example:

```python
{
    "source": "I love you",
    "target": "Ich liebe dich"
}
```

becomes:

```text
source IDs = [10, 25, 90]
target IDs = [300, 411, 502]
```

The model learns:

```text
[10, 25, 90] → [300, 411, 502]
```

---

## Training a Tokenizer for Translation

For training from scratch, train the tokenizer on both source and target text.

Example corpus:

```text
I love you
The house is big
I am learning
Ich liebe dich
Das Haus ist groß
Ich lerne
```

A simple Hugging Face tokenizer training example:

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace
from transformers import PreTrainedTokenizerFast

# Create a BPE tokenizer.
raw_tokenizer = Tokenizer(BPE(unk_token="<unk>"))

# This pre-tokenizer first splits roughly on whitespace.
# BPE then learns subword pieces inside those chunks.
raw_tokenizer.pre_tokenizer = Whitespace()

# Special tokens used by many seq2seq models.
special_tokens = ["<pad>", "<unk>", "<s>", "</s>"]

# vocab_size controls how many token pieces the tokenizer should learn.
trainer = BpeTrainer(
    vocab_size=32000,
    special_tokens=special_tokens,
)

# tokenizer_corpus.txt should contain BOTH source and target language text.
raw_tokenizer.train(
    files=["tokenizer_corpus.txt"],
    trainer=trainer,
)

# Wrap the raw tokenizer so it can be used by Hugging Face Transformers.
tokenizer = PreTrainedTokenizerFast(
    tokenizer_object=raw_tokenizer,
    unk_token="<unk>",
    pad_token="<pad>",
    bos_token="<s>",
    eos_token="</s>",
)

# Save tokenizer files.
tokenizer.save_pretrained("./my_translation_tokenizer")
```

After training:

```python
tokens = tokenizer("I love you")
print(tokens["input_ids"])
```

Possible output:

```text
[4, 5, 6]
```

And:

```python
tokens = tokenizer("Ich liebe dich")
print(tokens["input_ids"])
```

Possible output:

```text
[7, 8, 9]
```

---

## Creating a Seq2Seq Transformer Model From Scratch

The model must know the tokenizer vocabulary size.

If the tokenizer has 32,000 tokens, the model needs embeddings for 32,000 token IDs.

Example using a BART-style architecture:

```python
from transformers import BartConfig, BartForConditionalGeneration

config = BartConfig(
    vocab_size=len(tokenizer),

    # Hidden vector size.
    # Every token embedding will have this many dimensions.
    d_model=512,

    # Number of Transformer layers in encoder and decoder.
    encoder_layers=6,
    decoder_layers=6,

    # Number of attention heads.
    encoder_attention_heads=8,
    decoder_attention_heads=8,

    # Feed-forward network size inside each Transformer layer.
    encoder_ffn_dim=2048,
    decoder_ffn_dim=2048,

    # Maximum sequence length supported by learned position embeddings.
    max_position_embeddings=512,

    # Special token IDs from the tokenizer.
    pad_token_id=tokenizer.pad_token_id,
    bos_token_id=tokenizer.bos_token_id,
    eos_token_id=tokenizer.eos_token_id,

    # First token used to start decoder generation.
    decoder_start_token_id=tokenizer.bos_token_id,
)

model = BartForConditionalGeneration(config)
```

If:

```text
len(tokenizer) = 32000
d_model = 512
```

then the model embedding table has shape:

```text
32000 × 512
```

---

## What `labels` Means in Hugging Face Seq2Seq Training

In Hugging Face seq2seq training, `labels` means:

```text
the correct target output token IDs that the model should learn to generate
```

For translation:

```text
source = input sentence
target = correct translated sentence
```

Example:

```text
source: "أنا أقرأ كتابًا."
target: "Ich lese ein Buch."
```

After tokenization:

```text
input_ids = token IDs of the source sentence
labels    = token IDs of the target sentence
```

So:

```text
input_ids = what the encoder reads
labels    = what the decoder should generate
```

During training, the model compares:

```text
predicted target tokens
vs
labels
```

Then it calculates loss and updates the model weights.

This line:

```python
model_inputs["labels"] = target_tokens["input_ids"]
```

means:

```text
Store the tokenized target translation as the correct answer.
```

Without `labels`, the model has input but no supervised answer to compare against.

Minimal example:

```python
source = "أنا أقرأ كتابًا."
target = "Ich lese ein Buch."

model_inputs = tokenizer(source)
target_tokens = tokenizer(text_target=target)

model_inputs["labels"] = target_tokens["input_ids"]
```

Conceptually:

```text
input_ids = tokenizer("أنا أقرأ كتابًا.")
labels    = tokenizer("Ich lese ein Buch.")
```

When you call the model during training:

```text
model(input_ids=input_ids, labels=labels)
```

the model internally computes a loss:

```text
loss = difference between predicted output tokens and labels
```

---

## Full Commented Seq2Seq Fine-Tuning Example

This example fine-tunes a multilingual seq2seq model for Arabic → German.

For a whole new language, start from a multilingual model when possible. Adding a whole language to an English-German model by manually adding words is usually a weak approach.

```python
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

# ============================================================
# 1. Load tokenizer and model
# ============================================================
# Use a multilingual seq2seq model because the source language is Arabic.
#
# The tokenizer converts text <-> token IDs.
# The model learns source token IDs -> target token IDs.
# ============================================================

model_name = "facebook/nllb-200-distilled-600M"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


# ============================================================
# 2. Create parallel translation data
# ============================================================
# Each example has:
#
# source = input sentence, the language we translate FROM
# target = expected output sentence, the language we translate TO
#
# During training:
# - source becomes model input
# - target becomes labels
#
# "labels" are the correct answer token IDs.
# The model predicts output IDs and compares them against labels.
# ============================================================

train_examples = [
    {
        "source": "أنا أقرأ كتابًا.",
        "target": "Ich lese ein Buch.",
    },
    {
        "source": "المدرسة كبيرة.",
        "target": "Die Schule ist groß.",
    },
    {
        "source": "أنا أتعلم اللغة الألمانية.",
        "target": "Ich lerne die deutsche Sprache.",
    },
    {
        "source": "هذا كتاب جديد.",
        "target": "Das ist ein neues Buch.",
    },
    {
        "source": "الطالب يذهب إلى المدرسة.",
        "target": "Der Schüler geht zur Schule.",
    },
]

dataset = Dataset.from_list(train_examples)


# ============================================================
# 3. Optional: add NEW tokens
# ============================================================
# Add tokens only when you have special tokens that the tokenizer
# currently splits badly, for example:
#
# - company-specific terms
# - product names
# - domain-specific identifiers
# - special markup tokens
#
# Do NOT add a whole language word-by-word if the base tokenizer
# already supports that language.
#
# tokenizer.add_tokens(...) changes the tokenizer vocabulary.
# model.resize_token_embeddings(...) extends the model embedding table.
#
# The new embedding rows are random at first.
# They become meaningful only during trainer.train().
# ============================================================

new_tokens = [
    "SenacorGPT",
    "QdrantHybridRetriever",
]

num_added = tokenizer.add_tokens(new_tokens)

if num_added > 0:
    # The tokenizer vocabulary is now bigger.
    # The model embedding matrix must be resized to the same size.
    #
    # Before:
    # model embedding rows = old tokenizer vocab size
    #
    # After:
    # model embedding rows = new tokenizer vocab size
    #
    # Old token vectors are kept.
    # New token vectors are initialized randomly.
    model.resize_token_embeddings(len(tokenizer))


# ============================================================
# 4. Tokenize source and target sentences
# ============================================================
# The model cannot train on raw strings.
# It needs integer token IDs.
#
# Example:
#
# source:
# "أنا أقرأ كتابًا."
#
# becomes:
# input_ids = [123, 456, 789, ...]
#
# target:
# "Ich lese ein Buch."
#
# becomes:
# labels = [321, 654, 987, ...]
#
# input_ids:
#   What the encoder reads.
#
# labels:
#   What the decoder is supposed to generate.
#
# During training, Hugging Face automatically uses labels to compute loss.
# The model tries to predict the next target token and compares prediction
# with labels.
# ============================================================

max_source_length = 128
max_target_length = 128


def preprocess(batch):
    # ------------------------------------------------------------
    # Tokenize the SOURCE sentences.
    #
    # batch["source"] contains the input language sentences.
    #
    # The tokenizer returns:
    # - input_ids: integer IDs for the source text
    # - attention_mask: 1 for real tokens, 0 for padding tokens
    #
    # These are used by the encoder.
    # ------------------------------------------------------------

    model_inputs = tokenizer(
        batch["source"],
        max_length=max_source_length,
        truncation=True,
    )

    # ------------------------------------------------------------
    # Tokenize the TARGET sentences.
    #
    # batch["target"] contains the correct translation.
    #
    # These token IDs are NOT normal input to the encoder.
    # They are the expected output.
    #
    # Hugging Face calls them "labels".
    #
    # labels = correct target token IDs
    #
    # The model uses them to calculate training loss:
    #
    # predicted output tokens vs labels
    # ------------------------------------------------------------

    target_tokens = tokenizer(
        text_target=batch["target"],
        max_length=max_target_length,
        truncation=True,
    )

    # ------------------------------------------------------------
    # Store target token IDs under the key "labels".
    #
    # Seq2SeqTrainer expects this exact key.
    #
    # Without labels:
    # source sentence -> model has input
    # but no correct answer to compare against.
    #
    # With labels:
    # source sentence -> model predicts translation
    # labels -> correct translation
    # loss -> difference between prediction and correct answer
    # ------------------------------------------------------------

    model_inputs["labels"] = target_tokens["input_ids"]

    return model_inputs


tokenized_dataset = dataset.map(
    preprocess,
    batched=True,
    remove_columns=dataset.column_names,
)


# ============================================================
# 5. Create data collator
# ============================================================
# Training uses batches.
#
# Sentences have different lengths:
#
# "I read."              -> short
# "I read a large book." -> longer
#
# A batch needs tensors of equal length.
#
# The data collator pads examples inside a batch.
#
# It pads:
# - input_ids
# - attention_mask
# - labels
#
# For labels, padding tokens are usually replaced with -100.
#
# Why -100?
# Because PyTorch loss ignores label positions with value -100.
# This prevents the model from being punished for padding tokens.
# ============================================================

data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
)


# ============================================================
# 6. Define training settings
# ============================================================
# These control how training runs.
#
# learning_rate:
#   How large each weight update is.
#
# per_device_train_batch_size:
#   Number of examples processed at once per device.
#
# num_train_epochs:
#   How many times the model sees the full dataset.
#
# predict_with_generate:
#   Lets Trainer use model.generate() for seq2seq evaluation.
# ============================================================

training_args = Seq2SeqTrainingArguments(
    output_dir="./ar_de_translator",
    learning_rate=3e-5,
    per_device_train_batch_size=4,
    num_train_epochs=10,
    logging_steps=10,
    save_strategy="epoch",
    predict_with_generate=True,
    fp16=False,
)


# ============================================================
# 7. Create Trainer
# ============================================================
# Trainer connects everything:
#
# model:
#   The seq2seq Transformer being trained.
#
# args:
#   Training settings.
#
# train_dataset:
#   Tokenized examples containing input_ids and labels.
#
# tokenizer:
#   Needed for padding, saving, decoding, etc.
#
# data_collator:
#   Pads batches correctly.
# ============================================================

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)


# ============================================================
# 8. Train
# ============================================================
# This is where learning happens.
#
# For every batch:
#
# 1. Encoder reads source input_ids.
# 2. Decoder tries to generate target tokens.
# 3. Model predictions are compared with labels.
# 4. Loss is calculated.
# 5. Backpropagation updates model weights.
#
# This updates:
# - old embeddings if they are used
# - new embeddings if new tokens appear in the data
# - encoder weights
# - decoder weights
# - attention weights
# - output projection weights
#
# If your new tokens never appear in the training data,
# their embedding rows will not meaningfully learn.
# ============================================================

trainer.train()


# ============================================================
# 9. Save model and tokenizer together
# ============================================================
# Always save both.
#
# The model weights depend on the tokenizer IDs.
# If you load the wrong tokenizer later, IDs can mismatch.
# ============================================================

trainer.save_model("./ar_de_translator")
tokenizer.save_pretrained("./ar_de_translator")
```

---

## Inference After Training

After training, load the saved model and tokenizer together:

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("./ar_de_translator")
model = AutoModelForSeq2SeqLM.from_pretrained("./ar_de_translator")

text = "أنا أقرأ كتابًا."

inputs = tokenizer(
    text,
    return_tensors="pt",
)

generated_ids = model.generate(
    **inputs,
    max_length=64,
    num_beams=4,
)

translation = tokenizer.decode(
    generated_ids[0],
    skip_special_tokens=True,
)

print(translation)
```

Pipeline:

```text
"أنا أقرأ كتابًا."
→ tokenizer.encode()
→ input IDs
→ model.generate()
→ output IDs
→ tokenizer.decode()
→ German translation
```

---

## Extending a Tokenizer

You can extend a tokenizer by adding tokens:

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "Helsinki-NLP/opus-mt-en-de"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

new_tokens = [
    "SenacorGPT",
    "QdrantHybridRetriever",
]

num_added = tokenizer.add_tokens(new_tokens)

if num_added > 0:
    model.resize_token_embeddings(len(tokenizer))

tokenizer.save_pretrained("./extended_translation_model")
model.save_pretrained("./extended_translation_model")
```

The important line:

```python
model.resize_token_embeddings(len(tokenizer))
```

This resizes the embedding matrix so the model has a vector row for each tokenizer ID.

Before adding tokens:

```text
tokenizer size = 58101
embedding matrix = 58101 × hidden_size
```

After adding 2 tokens:

```text
tokenizer size = 58103
embedding matrix = 58103 × hidden_size
```

The old rows keep their learned vectors.

The new rows are initialized randomly.

Example:

```text
old token "love"  → trained vector remains
old token "Haus"  → trained vector remains

new token "SenacorGPT"          → random vector
new token "QdrantHybridRetriever" → random vector
```

So after only resizing:

```text
new token ID = valid ID
new embedding vector = random / untrained vector
meaning = none yet
```

The vector is not empty. It exists, but it is untrained.

---

## Why Extending Embeddings Does Not Teach Meaning

This is the key point.

After:

```python
tokenizer.add_tokens(["كتاب"])
model.resize_token_embeddings(len(tokenizer))
```

you get:

```text
"كتاب" → new token ID
new token ID → new embedding vector
```

But the vector is randomly initialized.

Example:

```text
كتاب → ID 58101
embedding[58101] → [0.013, -0.021, 0.044, ...]
```

At this point the model does **not** know what `كتاب` means.

It only knows:

```text
There is now a token with ID 58101.
It has some vector.
```

The model learns meaning only when the token appears in training data and gradients update its vector.

Training examples:

```text
أنا أقرأ كتابًا.      → Ich lese ein Buch.
هذا كتاب جديد.        → Das ist ein neues Buch.
الكتاب على الطاولة.   → Das Buch ist auf dem Tisch.
```

During training:

```text
"كتاب" appears in source input
target contains "Buch"
loss is calculated
backpropagation updates embedding vector for "كتاب"
```

Without data:

```text
no examples
→ no loss involving the token
→ no gradient
→ no learning
→ random vector stays useless
```

So:

```text
New token + no training data = useless token
New token + training examples = learnable token
New language + no corpus = impossible
```

---

## When Should You Add Tokens?

Adding tokens is useful for:

```text
domain-specific terms
company/product names
special symbols
rare technical identifiers
markup tokens
```

Examples:

```text
SenacorGPT
QdrantHybridRetriever
<CUSTOMER_ID>
<TOOL_CALL>
```

Adding tokens is usually **not** the right method for adding a whole language.

For a whole language, the model needs much more than token IDs and random vectors. It needs:

```text
grammar
word order
morphology
syntax
translation patterns
attention behavior
generation behavior
```

Better options for a new language:

```text
Option 1:
Use a multilingual model that already supports the language.

Option 2:
Train a tokenizer on all target languages from the beginning, then train the model from scratch.

Option 3:
Continue fine-tuning a multilingual model on enough parallel data.
```

Bad path:

```text
English-German model
+ add Arabic tokens
+ little data
= weak Arabic understanding
```

Better path:

```text
multilingual model that already knows Arabic
+ Arabic-German parallel data
= much better
```

---

## What Happens Before and After Fine-Tuning New Tokens

Before fine-tuning:

```text
"كتاب" → ID 58101
embedding[58101] → random vector
meaning → none
```

After fine-tuning on enough examples:

```text
"كتاب" → ID 58101
embedding[58101] → trained vector
meaning → learned through context and translation objective
```

The embedding row becomes useful because the model saw the token in examples and adjusted it to reduce loss.

---

## Fine-Tuning vs Training From Scratch

### Training From Scratch

Use this when you are building a model from zero.

Flow:

```text
1. Collect large parallel dataset.
2. Train tokenizer on all source + target language text.
3. Create model config with vocab_size = len(tokenizer).
4. Train model on source-target pairs.
5. Save model and tokenizer together.
```

This needs a lot of data.

A useful translation model often requires:

```text
hundreds of thousands to millions of sentence pairs
```

Small data will mostly produce memorization.

### Fine-Tuning Existing Model

Use this when a pretrained model already supports your language pair or languages.

Flow:

```text
1. Load pretrained model and tokenizer.
2. Keep its tokenizer.
3. Prepare your domain-specific translation pairs.
4. Fine-tune the model.
5. Save model and tokenizer together.
```

This is usually the practical path.

Important:

```text
Do not replace the tokenizer of a pretrained model casually.
```

Reason:

```text
The model’s embedding matrix is aligned with the tokenizer IDs.
```

If the old tokenizer had:

```text
love → 122
```

then the model learned:

```text
embedding row 122 ≈ useful vector for "love"
```

If a new tokenizer changes:

```text
love → 918
```

then the old model’s learned embedding alignment is broken.

---

## Checkpoints

In this context, a checkpoint usually means a saved snapshot of model training.

A checkpoint may contain:

```text
model weights
optimizer state
scheduler state
training step
tokenizer files
configuration files
```

Example:

```text
checkpoint-10000
checkpoint-20000
checkpoint-30000
```

A checkpoint lets you:

```text
resume training
evaluate a previous model state
compare different training stages
recover after interruption
```

The tokenizer should be saved with the model because token IDs must match the model’s embedding rows.

---

## Compact Summary

The practical rules:

```text
Tokenizer = text ↔ token IDs
Embedding layer = token IDs → vectors
Seq2seq Transformer = source vectors → target token predictions
```

A trained tokenizer has IDs for every token in its vocabulary.

The tokenizer does not contain vectors.

The model contains vectors in its embedding matrix.

Extending a tokenizer creates new token IDs.

Resizing embeddings creates new vector rows for those IDs.

The new vectors are random/untrained.

The model learns their meaning only from training data containing those tokens.

`labels` in seq2seq training are the correct target output token IDs.

For translation:

```text
input_ids = source sentence token IDs
labels    = target sentence token IDs
```

During training:

```text
model predicts target tokens
labels provide the correct answer
loss compares prediction vs labels
backpropagation updates the model
```

For a new language, do not just add words manually unless you have a narrow special-token/domain-token reason.

For a whole language:

```text
use a multilingual model
or train tokenizer + model from scratch with that language included
or fine-tune a multilingual model on parallel translation data
```

Final core idea:

```text
Adding tokens gives the model a place to store meaning.
Training gives that place actual meaning.
