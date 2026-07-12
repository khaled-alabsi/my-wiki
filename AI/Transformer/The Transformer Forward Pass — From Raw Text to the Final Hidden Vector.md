# The Transformer Forward Pass — From Raw Text to the Final Hidden Vector

This note walks through every stage that transforms a string of text into the contextualized hidden vector `h_N`, the single object the model uses to predict the next token. It is meant to be read as a standalone explanation: each step builds on the previous one, every concept has a concrete numerical example, and every piece of jargon is defined the first time it appears.

The journey has six stages, and the central thing to keep in mind is that there is one fixed “width” — called `d_model` — that information travels along throughout the entire network. Tokens enter as `d_model`-wide vectors, they stay `d_model`-wide through every layer, and they exit `d_model`-wide. Only the *contents* of those vectors change; the *shape* does not. Think of `d_model` as a pipe diameter that is chosen once when the model is designed and held fixed forever after. In small research models it might be 512, in modern production models it is typically 4096, 8192, or even 12288.

## Step 1: Tokenization

The model cannot read text directly. Neural networks operate on numbers, so the first thing that must happen is converting the raw string into a sequence of integers. This step is called tokenization.

Tokenization is not the same as splitting on spaces. Splitting by word gives you a vocabulary that is far too large (every conjugation, plural, and typo becomes its own token), and splitting by character gives you sequences that are absurdly long. Modern transformers use a middle ground called **subword tokenization**, with algorithms like Byte-Pair Encoding (BPE), WordPiece, or SentencePiece. These algorithms learn, from a huge text corpus, which sequences of characters appear together often enough to deserve their own token. Common words like `the` or `cat` end up as single tokens. Rare or compound words get split into pieces. For example, the word `unbelievable` might be tokenized as `["un", "believ", "able"]`, three tokens, because those subword pieces are reusable across many other words (`unhappy`, `believing`, `capable`).

The output of tokenization is a list of integer IDs, one per token. Each ID is just an index into the model’s vocabulary, which typically contains around 30,000 to 100,000 entries. If our toy sentence is `"the cat sat"`, tokenization might produce something like `[1043, 27, 9981]`. Three tokens, three integers, and at this stage they have no meaning yet — they are just labels pointing into a table.

A useful analogy is that tokenization is like splitting a sentence into LEGO bricks of standard shapes. You do not invent a custom brick for every sentence; you reuse a fixed inventory of pieces. The vocabulary is the set of available bricks, and tokenization is the act of identifying which bricks make up your input.

## Step 2: Token Embedding

The integers from step one carry no semantic information. The number 1043 does not mean anything; it is just an address. To give the model something to work with, each integer is looked up in a giant table called the **embedding matrix**, which has shape `(vocab_size, d_model)`. Every row of this table is a learned vector representing one token in the vocabulary.

If `d_model = 8` and the vocabulary has 50,000 entries, the embedding matrix has shape `(50000, 8)`. Looking up token ID 1043 means grabbing row 1043 of this matrix, which is a vector of 8 floating-point numbers. After looking up all three of our tokens, the data looks like this:

```
                  ←———— d_model = 8 ————→

token "the"  →   [ 0.1, -0.3,  0.7,  0.2, -0.5,  0.9,  0.1,  0.4 ]
token "cat"  →   [ 0.5,  0.2, -0.1,  0.8,  0.3, -0.6,  0.2,  0.7 ]
token "sat"  →   [ 0.3,  0.7,  0.1,  0.8, -0.2,  0.4,  0.6, -0.1 ]

  ↑
  N = 3 tokens
```

Three integer IDs became a matrix of shape `(N, d_model)` which here is `(3, 8)`. Each row is one token, each row has exactly `d_model` numbers, and every downstream layer in the transformer expects exactly this format. This is the moment when `d_model` first appears, and it stays the width of the data from here all the way to the end.

The values inside these vectors are not random. They are **learned** during training. Over many training steps, the model adjusts these numbers so that tokens with similar meanings end up with similar vectors. The vector for `cat` will end up close (in cosine-distance terms) to the vector for `dog`, and far from the vector for `democracy`. Nobody designs these similarities by hand; they emerge from the training data.

A good analogy here is that the embedding matrix is a giant dictionary, and the embedding step is a dictionary lookup. The integer ID is the dictionary key, and the `d_model`-long vector is the definition. The definitions were written collaboratively by the training data over millions of examples, and they encode whatever the model found useful about each token.

## Step 3: Positional Encoding

There is a serious problem lurking in what we have built so far. The attention mechanism that comes next is, at its core, a weighted sum of value vectors. And summation is commutative: `4 + 1 + 2` equals `1 + 4 + 2`. If we feed our three embeddings into attention as they are, the model has no way to distinguish `"the cat sat"` from `"sat cat the"` or `"cat the sat"`. The order of words would be invisible. Without a fix, the entire transformer would collapse into a bag-of-words model that ignores syntax entirely.

The fix is to inject position information directly into each token’s vector **before** anything else happens. This is called **positional encoding**. For every position `i` in the sequence, we compute a position-specific vector of length `d_model` and add it to the token embedding at that position.

After this addition, the same word appearing at different positions produces different vectors. Conceptually, position 1 has its own characteristic fingerprint, position 2 has another, and so on. When attention later does its weighted sum, it is summing vectors that already carry their position with them, so reordering the inputs really does change the result.

There are three common ways to compute positional encodings, and they all share the goal of giving each position a unique, recognizable signature. The original 2017 transformer used **sinusoidal encodings**, where each dimension of the position vector is a sine or cosine wave of a different frequency. The clever trick is that this lets the model easily learn relative offsets, because shifting position by a fixed amount corresponds to a simple rotation in this representation. Later models use **learned positional embeddings**, where the position vector for each slot is just another set of trainable parameters. Modern models like Llama and GPT-4 use **Rotary Positional Embedding (RoPE)**, which encodes position by rotating the query and key vectors inside attention rather than by adding a vector up front — the effect is similar, but RoPE generalizes better to longer sequences than the model was trained on.

For our purposes, the mechanism does not matter. What matters is that after step three, the data still has shape `(N, d_model)`, but each row now encodes both *what* the token is and *where* it sits in the sequence.

The analogy here is name tags at a conference. The embedding vector tells you who a person is. The positional encoding tells you where they are standing in line. Without name tags showing position, you cannot tell apart two attendees with the same name standing in different spots.

## Step 4: The Stack of Transformer Blocks

This is the heart of the model. The data, now shaped `(N, d_model)` and carrying both token identity and position, flows through a stack of identical transformer blocks. A small model might have 12 blocks; Llama 3 70B has 80. Each block has the same internal structure and takes `(N, d_model)` in and produces `(N, d_model)` out. The blocks do not share weights; each one learns its own transformation.

Inside one block, four operations happen in sequence: multi-head self-attention, a residual connection with layer normalization, a position-wise feed-forward network, and another residual connection with layer normalization. Each of these deserves its own explanation.

### Multi-head self-attention

This is the only operation in the entire transformer where information moves **between tokens**. Every other operation processes tokens independently. So attention is the model’s communication channel.

The mechanism is this: each token row generates three projections of itself called the **query**, **key**, and **value**, all computed by multiplying the token’s vector with learned weight matrices. The query represents what the token is looking for; the key represents what each token offers; the value represents the information each token will share if attended to. For every pair of tokens, the model computes a similarity score between one token’s query and another token’s key. These scores are normalized into attention weights via softmax, and the output for each token is a weighted sum of all the value vectors in the sequence.

Concretely, when we compute the output for the position of `sat`, the model asks: “given what `sat` is looking for, how much should it pay attention to `the`, to `cat`, and to itself?” The weights might come out as 0.1, 0.6, and 0.3, meaning `sat`’s output absorbs a little from `the`, a lot from `cat`, and a moderate amount from itself.

The word **multi-head** means this entire process is done several times in parallel, with different sets of weight matrices, and the results are concatenated and projected back to `d_model`. Each “head” can learn to focus on a different kind of relationship. One head might learn syntactic dependencies (verbs attending to their subjects), another might track long-range references (pronouns attending to the nouns they refer to), another might focus on positional patterns. Multi-head attention gives the model parallel specialists, each looking at the sequence from a different angle.

There is one more crucial detail for language models: the **causal mask**. During training, the model is shown the entire sequence at once and asked to predict each next token in parallel. To prevent it from cheating by looking ahead, attention is masked so that position `i` can only attend to positions `1` through `i`, never to positions `i+1` onward. The mask is implemented by setting the attention scores for forbidden positions to negative infinity before the softmax, which makes their weights effectively zero.

A good analogy is that attention is like a meeting where each token gets to ask every other token a question and weigh the answers. Multi-head attention is several such meetings happening in parallel, each focused on a different topic. The causal mask is the rule that you can only consult colleagues who arrived before you, not after.

### Residual connection and layer normalization

After attention produces its output, the model does something that looks almost trivial but is actually one of the most important architectural tricks in deep learning. It adds the *input* of the attention layer back to its *output*. This is called a **residual connection** or **skip connection**.

The reason this matters is that it gives every layer a direct shortcut to bypass itself. If a particular attention layer happens to be unhelpful for a given token, the residual lets the original information pass through unchanged, rather than being mangled by the layer. During training, this also makes gradients flow much more cleanly back through deep stacks of layers, which is what allows transformers to have dozens or hundreds of blocks without degrading.

Right after the residual sum, **layer normalization** is applied. This rescales each token’s vector so that its values have mean zero and standard deviation one across the `d_model` dimension, then applies a learned scale and shift. The point is to keep the magnitudes of activations stable as data flows through many layers, preventing the numbers from drifting toward zero or exploding. Without it, training deep transformers is unstable.

An analogy: the residual connection is like keeping a photocopy of your original notes before sending them off to be edited, so that if the editor returns garbage, you can still see what you started with. Layer normalization is like a sound engineer normalizing volume levels between tracks, so that no single voice drowns out the others as the song progresses.

### Position-wise feed-forward network

After attention has done the cross-token mixing, each token’s row is passed through a small two-layer neural network called the **feed-forward network** or FFN. The critical point — and this is where the “1D input” intuition from classical MLPs lives — is that this FFN is applied to **each token’s row independently**, with the **same weights shared across all positions**. It is not given access to other tokens. By the time data reaches the FFN, attention has already mixed in whatever cross-token information is needed, and now the FFN does private per-token refinement.

The FFN typically expands the dimension internally before contracting back. A common pattern is `d_model → 4 × d_model → d_model`, with a nonlinearity (GELU or SwiGLU in modern models) in the middle. So a token vector of width 4096 might be expanded to 16384, transformed nonlinearly, then projected back to 4096. The internal expansion is where most of the model’s parameters actually live, and it is where the FFN does the heavy lifting of transforming token representations.

After the FFN, another residual connection and layer normalization are applied, just like after attention.

The analogy: if attention was a meeting where tokens exchanged information, the FFN is private reflection time afterward, where each token sits alone and processes what it just heard, using the same thinking method (shared weights) as every other token.

### What the block accomplishes

After one full block, every token’s vector has been updated to incorporate information from other tokens in the sequence (via attention) and then refined individually (via FFN). The shape is still `(N, d_model)`. The values inside have changed.

Then the same thing happens again in the next block, and the next, for however many blocks the model has. Each block builds on the previous one, producing progressively more refined representations. Early blocks tend to capture surface patterns (which token is next to which); middle blocks capture syntactic relationships; later blocks capture abstract semantic content. This emergent specialization is not designed in — it arises from training.

## Step 5: Final Layer Normalization

After the last transformer block, one final layer normalization is applied to the output. This is mostly a stability detail: it ensures that the activations entering the next stage (the projection to vocabulary logits) have well-behaved magnitudes. The shape is still `(N, d_model)`.

There is not much more to say about this step. It is a tidying-up operation. The interesting work has already happened in the blocks.

## Step 6: Take the Last Row, h_N

The output of step five is a matrix of shape `(N, d_model)` containing one contextualized vector per input position. Each row represents the model’s full understanding of that position given everything before it. During training, every row matters because each one is used to predict the token that follows it. During inference, when the model is generating the next token, only the last row is used.

That last row is what we have been calling `h_N`. It is the **contextualized hidden state of the final position**. The terms used for it in the literature vary: hidden state, contextualized embedding, contextual representation, final representation, output embedding. The user’s instinct to call it a “latent vector” is also defensible — it is a learned compressed representation of meaning, which is roughly what “latent” implies in machine learning. The most technically standard name in transformer-specific literature is **last-position hidden state** or just **hidden state at position N**.

`h_N` is a vector of length `d_model`. To predict the next token, the model multiplies `h_N` by another learned matrix of shape `(d_model, vocab_size)`, producing a vector of length `vocab_size` called the **logits**. Applying softmax to the logits gives a probability distribution over the entire vocabulary, and the model either picks the most probable token (greedy decoding) or samples from the distribution (with strategies like top-k, top-p, or temperature). That token becomes token `N+1`. To generate token `N+2`, the whole pipeline runs again with the new token appended.

This is the moment where everything comes together. Tokenization gave the model a list of integers to work with. Embedding turned each integer into a meaningful learned vector. Positional encoding injected order. The stack of blocks let tokens exchange information via attention and refine themselves via the FFN, with residuals and normalization keeping everything stable. The final layer norm tidied up. And taking the last row gave us the single vector — `h_N` — that contains everything the model needs to know about what should come next.

## Summary: The Pipeline at a Glance

The forward pass starts with a string of text and ends with a single `d_model`-wide vector that summarizes everything relevant for predicting the next token. Stage one converts the text into integer token IDs using subword tokenization. Stage two looks each integer up in a learned embedding table, producing a matrix of shape `(N, d_model)`. Stage three adds positional information to that matrix so that order is preserved through the subsequent operations. Stage four sends the matrix through a stack of transformer blocks, each of which performs multi-head self-attention to mix information across tokens, then a position-wise feed-forward network to refine each token individually, with residual connections and layer normalization wrapped around both sublayers. Stage five applies a final layer normalization to the output. Stage six picks the last row of that output as the hidden vector `h_N`, which is then projected into vocabulary logits and turned into the next token.

The shape `(N, d_model)` is the invariant of the entire process. From the moment tokens are embedded until the very last block produces its output, every operation preserves this shape. The contents change at every step, but the width — `d_model` — never does. That single number is the highway along which all information in the transformer travels, and understanding that one fact unlocks most of the architecture’s design.