# MonoEmbed vs MicroDec — Step-by-Step Comparison

Both are LLM-based decomposition methods. Neither uses a Genetic Algorithm.
The core idea in both: use an LLM to understand code meaning, turn each class
into a vector, then cluster similar vectors into microservices.

The fundamental difference: **how they feed information to the LLM.**

- MonoEmbed feeds raw source code text to the LLM
- MicroDec feeds graph-walk sequences (structural paths through the call graph) to the LLM

-----

## Step 0: What is an Embedding Vector?

Before diving in, you need to understand what an embedding is — both methods produce them.

An embedding vector is a list of numbers that represents the *meaning* of something.
The LLM reads a class and converts it into a vector like:

```
OrderService  → [0.82, 0.14, 0.91, 0.03, ...]   (hundreds of numbers)
PaymentService → [0.79, 0.11, 0.88, 0.05, ...]
FraudService   → [0.12, 0.95, 0.07, 0.61, ...]
```

Classes that are semantically similar end up with vectors that are numerically close.
Classes that are unrelated end up with vectors far apart.

```
OrderService ←— close —→ PaymentService   (both about transactions)
OrderService ←— far   —→ FraudService    (different domains)
```

This is the key capability neither pure GA method has — the LLM encodes *meaning*,
not just call counts.

-----

## Step 1: Input — What do you feed it?

Both use static analysis on source code. No need to run the application.

### MonoEmbed

Extracts raw source code fragments — the actual text of each class:

```
OrderService source fragment:
  "class OrderService {
     void placeOrder(Order o) {
       validateOrder(o);
       inventory.reserve(o.items);
       payment.charge(o.total);
     }
   }"
```

This text is what gets fed directly to the LLM.

-----

### MicroDec

Extracts the call graph — classes as nodes, method calls as edges:

```
Nodes: OrderService, PaymentService, InventoryService, FraudService
Edges:
  OrderService → PaymentService
  OrderService → InventoryService
  PaymentService → FraudService
```

MicroDec does NOT feed source code text to the LLM.
It feeds graph structure instead.

-----

## Step 2: Creating the Input for the LLM

This is the biggest difference between the two methods.

### MonoEmbed — Feed Source Code Directly

Each class’s source code is passed to the LLM as text.
The LLM reads it like a human would read code and produces an embedding vector.

```
Input to LLM:
  "class OrderService { void placeOrder... payment.charge... inventory.reserve... }"

Output from LLM:
  OrderService → [0.82, 0.14, 0.91, 0.03, ...]
```

The LLM understands words like “payment”, “charge”, “order” and encodes their
meaning into the vector. Two classes that deal with similar concepts get
numerically similar vectors even if they never call each other.

-----

### MicroDec — Random Walks on the Call Graph First

MicroDec does not feed source code to the LLM.
Instead it runs **random walks** on the call graph to generate sequences of classes,
then feeds those sequences to the LLM.

**What is a random walk?**

Starting from a class, you randomly follow edges to neighboring classes,
then follow edges from there, and so on — like a random stroll through the graph.
You record the sequence of classes visited.

```
Call graph:
  OrderService → PaymentService → FraudService
  OrderService → InventoryService

Random walks starting from OrderService (3 walks of length 4):
  Walk 1: OrderService → PaymentService → FraudService → PaymentService
  Walk 2: OrderService → InventoryService → OrderService → PaymentService
  Walk 3: OrderService → PaymentService → FraudService → FraudService
```

You run many walks from every node in the graph.
Each class ends up with a collection of sequences describing its neighborhood context.

**Why random walks and not just the direct call list?**

Direct calls only show immediate neighbors (1 hop away).
Random walks capture indirect relationships — classes that are 2, 3, or 4 hops away
but frequently co-appear in the same execution path.

```
OrderService directly calls: PaymentService, InventoryService
Random walks reveal: OrderService frequently co-appears with FraudService too
  (because OrderService → PaymentService → FraudService is a common path)
```

These sequences are then fed to the LLM, which converts each class’s
collection of walk sequences into an embedding vector:

```
Input to LLM for OrderService:
  Sequences: ["OrderService PaymentService FraudService", 
              "OrderService InventoryService OrderService",
              ...]

Output from LLM:
  OrderService → [0.76, 0.21, 0.84, 0.09, ...]
```

The LLM encodes not just what the class does, but how it is structurally
connected to other classes in the call graph.

-----

## Step 3: Fine-tuning the LLM (MonoEmbed only)

MicroDec uses a pre-trained LLM as-is and skips this step.

MonoEmbed adds a crucial extra step — it fine-tunes the LLM specifically
for the microservice decomposition task using **Contrastive Learning**.

**The problem with a generic pre-trained LLM:**

A generic LLM produces embeddings optimized for general language understanding.
But classes that belong to the same microservice might use very different vocabulary.
The generic LLM might put them far apart in vector space even though they belong together.

**What Contrastive Learning does:**

It trains the LLM with pairs of examples:

- “These two classes belong to the same microservice” → pull their vectors closer
- “These two classes belong to different microservices” → push their vectors further apart

```
Before fine-tuning:
  OrderService  → [0.82, 0.14, 0.91]
  InventoryService → [0.61, 0.33, 0.72]   ← somewhat close but not enough
  FraudService  → [0.79, 0.18, 0.88]      ← incorrectly close to OrderService

After fine-tuning with contrastive learning:
  OrderService  → [0.90, 0.10, 0.95]
  InventoryService → [0.88, 0.12, 0.93]   ← pulled much closer (same microservice)
  FraudService  → [0.10, 0.90, 0.15]      ← pushed much further away
```

MonoEmbed also uses **LoRA** (Low Rank Adaptation) to make this fine-tuning
computationally efficient — it only adjusts a small subset of the LLM’s parameters
rather than retraining the whole model.

This fine-tuning is what makes MonoEmbed’s embeddings specifically optimized
for decomposition rather than general code understanding.

-----

## Step 4: Clustering — Group Vectors into Microservices

Both methods do the same thing here — run a clustering algorithm on the embedding vectors.

Classes with similar vectors end up in the same cluster.
Each cluster becomes a microservice candidate.

### MonoEmbed

Uses standard clustering algorithms (e.g. K-Means, hierarchical clustering):

```
Embedding space after fine-tuning:

  [OrderService, InventoryService]     ← cluster 1 → Microservice 1
  [PaymentService, FraudService]       ← cluster 2 → Microservice 2
  [ProductService, CategoryService]    ← cluster 3 → Microservice 3
```

### MicroDec

Uses K-Means clustering on the random-walk LLM embeddings:

```
Embedding space after random-walk encoding:

  [OrderService, InventoryService]     ← cluster 1 → Service Candidate 1
  [PaymentService, FraudService]       ← cluster 2 → Service Candidate 2
  [ProductService, CategoryService]    ← cluster 3 → Service Candidate 3
```

Both produce the same type of output — class-to-cluster assignments.

-----

## Step 5: Output

Both output a **single decomposition** — one assignment of classes to microservices.

```
Microservice 1: OrderService, InventoryService
Microservice 2: PaymentService, FraudService
Microservice 3: ProductService, CategoryService
```

There is no Pareto front. There is no set of trade-off options.
There is one answer, produced in one shot.

This is the key limitation both share compared to GA methods —
and the reason they are called **single-shot clustering** approaches.

-----

## Summary Table

|Aspect                      |MonoEmbed                        |MicroDec                             |
|----------------------------|---------------------------------|-------------------------------------|
|Input to LLM                |Raw source code text             |Random walk sequences from call graph|
|LLM fine-tuned?             |Yes — Contrastive Learning + LoRA|No — pre-trained as-is               |
|What LLM encodes            |Semantic meaning of code         |Structural neighborhood in call graph|
|Clustering algorithm        |K-Means / hierarchical           |K-Means                              |
|Output                      |Single decomposition             |Single decomposition                 |
|Multi-objective optimization|No                               |No                                   |
|Pareto front                |No                               |No                                   |
|Needs running app           |No                               |No                                   |

-----

## The Core Tradeoff Between the Two

**MonoEmbed’s strength:**
It understands what code *means* through text.
Two classes that never call each other but both deal with “payment processing”
will get close vectors because the LLM reads the words.
Fine-tuning makes those vectors specifically sharp for decomposition.

**MonoEmbed’s weakness:**
It ignores graph structure. It does not know that OrderService is always
3 hops away from FraudService in every execution path.

**MicroDec’s strength:**
It captures structural relationships through random walks.
Classes that are structurally close in the call graph — even indirectly —
end up with similar vectors. It sees the graph topology.

**MicroDec’s weakness:**
It ignores source code meaning. Two classes with identical names and purposes
but no call relationship will get distant vectors.
Also the LLM is not fine-tuned for decomposition — it uses generic embeddings.

-----

## Why Both Were Still Not Enough (→ leading to SEMA-GA)

Both produce rich semantic embeddings that GA methods like FoSCI and MSExtractor
cannot — they understand meaning, not just call counts.

But they both share two fatal limitations:

**1. Single-shot — no optimization**
They cluster once and output one answer.
There is no iterative refinement, no feedback loop, no chance to fix bad groupings.
If the clustering puts two unrelated classes together, nobody catches it.

**2. No multi-objective trade-off**
They produce one decomposition with no sense of trade-offs.
You cannot ask “give me the version that is more cohesive but accepts higher coupling”
— you just get whatever the clustering algorithm decided.

SEMA-GA combines the best of both worlds:

- LLM semantic understanding (from the LLM-based camp)
- Iterative multi-objective optimization with trade-off preservation (from the GA camp)
- Plus LLM-as-critic to catch what numbers cannot measure