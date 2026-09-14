# NSGA-II vs MSExtractor — Step-by-Step Comparison

-----

## Step 0: Input — What do you feed it?

|        |NSGA-II (pure)          |MSExtractor                        |
|--------|------------------------|-----------------------------------|
|Input   |Source code             |Source code                        |
|Analysis|Static (call graph only)|Static (call graph + semantic text)|

**NSGA-II** scans the source code and builds a call graph — who calls whom. That is the only input.

**MSExtractor** does the same call graph, but also reads class names, method names, and comments as text — extracting *semantic meaning* on top of structural calls.

```
NSGA-II sees:
  OrderService → PaymentService  (a call exists)

MSExtractor sees:
  OrderService → PaymentService  (a call exists)
  OrderService is about: "order", "purchase", "checkout"
  PaymentService is about: "payment", "charge", "transaction"
```

MSExtractor builds a similarity matrix from both sources combined:

```
                OrderService  PaymentService  InventoryService
OrderService         1.0           0.6              0.7
PaymentService       0.6           1.0              0.1
InventoryService     0.7           0.1              1.0
```

NSGA-II has no such matrix — it works purely from the call graph.

-----

## Step 1: Initialize Population

Both start the same way — randomly assign classes to buckets to create N candidate solutions.

```
Solution 1:
  Bucket-1: OrderService, InventoryService
  Bucket-2: PaymentService
  Bucket-3: FraudService

Solution 2:
  Bucket-1: OrderService, PaymentService
  Bucket-2: InventoryService, FraudService
  ...
```

Bucket labels mean nothing — just random groupings. Both algorithms start completely blind and improve over generations.

**No difference here between the two.**

-----

## Step 2: Score Every Solution — Objectives

This is where they diverge significantly.

### NSGA-II (pure)

Optimizes 2 objectives:

**Coupling — lower is better**
Count method calls crossing bucket boundaries using the call graph:

```
OrderService(B1) → PaymentService(B2)   → different → +1
OrderService(B1) → InventoryService(B1) → same      → +0
coupling = 1
```

**Cohesion — higher is better**
Count internal calls within each bucket:

```
Bucket-1: OrderService ↔ InventoryService → 1 internal call out of 2 possible
cohesion = 0.5
```

Final vector: `[coupling=1, cohesion=0.5]`

-----

### MSExtractor

Optimizes 3 objectives using BOTH structural calls AND semantic similarity:

**Coupling — lower is better**
Same as NSGA-II — count cross-boundary calls:

```
OrderService(B1) → PaymentService(B2) → +1
coupling = 1
```

**Cohesion — higher is better**
Uses the similarity matrix, not just raw call counts.
Instead of counting calls, it measures how similar classes are overall:

```
Bucket-1: OrderService + InventoryService
  similarity score from matrix = 0.7
  cohesion = 0.7
```

This is richer than NSGA-II’s cohesion — two classes that never call each other
but share the same domain vocabulary (both about “orders”) still get
a high cohesion score in MSExtractor. NSGA-II would score them 0.

**Granularity — middle is better**
A third objective NSGA-II does not have.
Penalizes decompositions that produce too few or too many services:

```
Too few (serviceCount=1): penalty → bad score
Too many (serviceCount=20): penalty → bad score
Ideal middle range: good score
```

This prevents the algorithm from collapsing everything into one bucket
or exploding into dozens of single-class services.

Final vector: `[coupling=1, cohesion=0.7, granularity=0.8]`

-----

## Step 3: Ranking Solutions

Both algorithms rank solutions by comparing their score vectors.
But they use different ranking mechanisms.

### NSGA-II

Uses **non-dominated sorting** — assigns solutions to Pareto fronts:

```
Compare Solution 1 [coupling=1, cohesion=0.5]
     vs Solution 2 [coupling=2, cohesion=0.8]

  S1 better at coupling, S2 better at cohesion → neither dominates
  → both go to Front 1
```

Solutions nobody dominates → Front 1 (best)
Solutions dominated by Front 1 → Front 2
And so on.

Within same front → use crowding distance (how isolated/unique the solution is).

-----

### MSExtractor (IBEA)

Uses a completely different approach — **no Pareto fronts**.

Instead, each solution gets a single numeric score based on how much
the overall population would suffer if that solution were removed.

A solution that covers a unique region of the trade-off space gets a HIGH score
— removing it would leave a gap nobody else covers.

A solution that has many similar neighbors gets a LOW score
— removing it loses nothing because neighbors already cover that trade-off.

```
Solution 1 [coupling=1, cohesion=0.7, granularity=0.8]
  → unique in this region → high IBEA score → keep

Solution 2 [coupling=1, cohesion=0.71, granularity=0.79]
  → nearly identical to Solution 1 → low IBEA score → likely dropped
```

**Key difference:**

- NSGA-II preserves a whole SET of trade-off solutions (the Pareto front)
- IBEA converges toward ONE best solution — the highest scoring one

-----

## Step 4: Selection — Pick Parents

### NSGA-II

Random 1v1 tournaments:

- Pick 2 random solutions
- Lower front number wins
- Tie → higher crowding distance wins
- Winner becomes parent

This keeps diversity — weaker solutions occasionally survive and breed,
preventing premature convergence to similar solutions.

### MSExtractor (IBEA)

Also uses tournament selection, but compares by IBEA score directly:

- Pick 2 random solutions
- Higher IBEA score wins
- Winner becomes parent

Solutions with unique trade-offs (high score) are more likely selected.
Redundant solutions (low score) are more likely dropped.

-----

## Step 5: Crossover — Combine Parents into Child

Both do the same thing here — random split point, take left side from
one parent and right side from the other:

```
Parent1: [OrderService→B1, PaymentService→B1, | InventoryService→B2, FraudService→B2]
Parent2: [OrderService→B1, PaymentService→B2, | InventoryService→B2, FraudService→B3]

Child:   [OrderService→B1, PaymentService→B1,   InventoryService→B2, FraudService→B3]
          ←————— from P1 ——————→                 ←————— from P2 ——————→
```

**No meaningful difference here between the two.**

-----

## Step 6: Mutation — Randomly Tweak Child

Both fire mutation with small probability (1–5%).
Randomly move one class to a different bucket:

```
Before: OrderService→B1, PaymentService→B1, InventoryService→B2, FraudService→B3
After:  OrderService→B1, PaymentService→B2, InventoryService→B2, FraudService→B3
```

**No meaningful difference here between the two.**

-----

## Step 7: Merge + Trim

### NSGA-II

Merge parents (N) + children (N) = pool of 2N.
Re-rank everything into Pareto fronts.
Fill next generation greedily from Front 1, then Front 2, etc.
If a front is too large → sort by crowding distance, keep most isolated.

Result: next generation preserves diversity across the full trade-off space.

### MSExtractor (IBEA)

Merge parents (N) + children (N) = pool of 2N.
Recalculate IBEA score for all 2N solutions.
Repeatedly remove the solution with the LOWEST IBEA score until back to N.

Result: next generation converges toward the highest quality region,
dropping redundant solutions aggressively.

-----

## Step 8: Stopping Condition

Both stop at a pre-defined max number of generations (e.g. 200).
Both also stop early if the population stops changing between generations.

**No difference here.**

-----

## Final Output

### NSGA-II

Outputs Front 1 of the final population — a SET of solutions:

```
Option 1: [coupling=1, cohesion=0.80, serviceCount=5]
Option 2: [coupling=2, cohesion=0.90, serviceCount=3]
Option 3: [coupling=0, cohesion=0.60, serviceCount=8]
```

Human architect picks one based on their priorities.

### MSExtractor

Outputs ONE recommended decomposition — the solution with the highest IBEA score:

```
Best: [coupling=1, cohesion=0.85, granularity=0.80]
  Bucket-1: OrderService, InventoryService
  Bucket-2: PaymentService, FraudService
  Bucket-3: NotificationService
```

No human choice needed — the algorithm already decided the best trade-off.

-----

## Summary Table

|Aspect             |NSGA-II (pure)                   |MSExtractor                    |
|-------------------|---------------------------------|-------------------------------|
|Input              |Call graph only                  |Call graph + semantic text     |
|Objectives         |2 (coupling, cohesion)           |3 (+ granularity)              |
|Cohesion scoring   |Raw call counts                  |Similarity matrix (richer)     |
|Ranking mechanism  |Pareto fronts + crowding distance|Single IBEA score per solution |
|Output             |Set of trade-off solutions       |One best solution              |
|Needs running app  |No                               |No                             |
|Understands meaning|No                               |Partially (via text similarity)|

-----

## Why Neither Was Enough (→ leading to SEMA-GA)

Both algorithms work purely with numbers — call counts, similarity scores, granularity ratios.
Neither can answer questions like:

- “Does this grouping represent a coherent business domain?”
- “Does this decomposition respect layering discipline?”
- “Would a senior architect agree this is a good boundary?”

These qualities exist but cannot be expressed as a formula.
That gap is exactly what SEMA-GA fills by embedding an LLM inside the evolutionary loop
to score and reason about things numbers cannot capture.