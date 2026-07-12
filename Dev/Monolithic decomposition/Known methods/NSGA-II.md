# Full NSGA-II — Every Step With Full Detail

-----

## Phase 0: Static Analysis (happens once before algorithm starts)

A tool like JavaParser scans every Java file and records every method call:

```java
class OrderService {
    void placeOrder() {
        paymentService.charge();     // → recorded
        inventoryService.reserve();  // → recorded
    }
}
class PaymentService {
    void charge() {
        fraudService.check();        // → recorded
    }
}
```

Produces this **call graph:**

```
OrderService   → PaymentService
OrderService   → InventoryService
PaymentService → FraudService
```

This never changes. Every step queries it.

-----

## Step 1: Initialize Population

Randomly throw classes into numbered buckets (N solutions total, e.g. N=4).

Bucket numbers mean nothing — they are just labels for groupings. The algorithm has no idea yet which classes belong together. It starts completely random and improves over generations.

```
Solution 1:
  Bucket-1: OrderService, InventoryService
  Bucket-2: PaymentService
  Bucket-3: FraudService

Solution 2:
  Bucket-1: OrderService, PaymentService
  Bucket-2: InventoryService, FraudService

Solution 3:
  Bucket-1: OrderService
  Bucket-2: PaymentService, InventoryService
  Bucket-3: FraudService

Solution 4:
  Bucket-1: OrderService, FraudService
  Bucket-2: PaymentService, InventoryService
```

-----

## Step 2: Score Every Solution

For each solution run 3 formulas. Each formula measures a different quality of the decomposition.

-----

### Coupling — lower is better

**Meaning:** how many times do classes in different buckets call each other?

Low coupling means services are independent — they do not constantly reach into each other to get work done. A good microservice should be able to operate without constantly calling other services. If OrderService needs to call PaymentService every time it does anything, they are too tightly connected — splitting them into separate services gains you nothing.

```
Solution 1:
  OrderService(B1) → PaymentService(B2)    → different buckets → +1
  OrderService(B1) → InventoryService(B1)  → same bucket      → +0
  PaymentService(B2) → FraudService(B3)    → different buckets → +1
  coupling = 2
```

-----

### Cohesion — higher is better

**Meaning:** how much do classes inside the same bucket call each other?

High cohesion means the classes inside a bucket are naturally related and depend on each other — they work together to fulfill one clear responsibility, so they belong together. Low cohesion means unrelated classes were randomly dumped into the same bucket with nothing in common — like putting OrderService and FraudService together even though they never interact. That bucket has no clear purpose and makes a terrible microservice.

```
Solution 1:
  Bucket-1 contains OrderService and InventoryService:
    OrderService → InventoryService: YES (placeOrder calls reserve) → 1 internal call
    InventoryService → OrderService: NO → 0
    internal calls = 1 out of 2 possible directions
    Bucket-1 cohesion = 1/2 = 0.50

  Bucket-2 contains only PaymentService:
    Only one class → no internal calls possible
    Bucket-2 cohesion = 0.0

  Bucket-3 contains only FraudService:
    Only one class → no internal calls possible
    Bucket-3 cohesion = 0.0

  avg cohesion = (0.50 + 0.0 + 0.0) / 3 = 0.17
```

-----

### Service Count — middle is better

**Meaning:** how many buckets exist?

Too few means you barely decomposed the monolith — you just renamed it. Too many means you exploded it into dozens of tiny meaningless services that constantly call each other. The ideal is somewhere in the middle — enough services to have clear separation, few enough to stay manageable.

```
Solution 1: 3 buckets → serviceCount = 3
```

-----

### Final score vectors for all solutions:

```
Solution 1: [coupling=2, cohesion=0.17, serviceCount=3]
Solution 2: [coupling=3, cohesion=0.50, serviceCount=2]
Solution 3: [coupling=2, cohesion=0.25, serviceCount=3]
Solution 4: [coupling=3, cohesion=0.40, serviceCount=2]
```

-----

## Step 3: Non-Dominated Sorting → Assign Fronts

Every pair of solutions gets compared. The rule is:

**Solution X dominates Solution Y if X is better or equal in ALL objectives and strictly better in at least one.**

“X” and “Y” here are just placeholders meaning “any two solutions being compared” — not fixed labels.

Objectives direction:

- coupling → lower is better
- cohesion → higher is better
- serviceCount → middle is better (3 is ideal here)

```
S1 [2, 0.17, 3] vs S2 [3, 0.50, 2]

  Does S1 dominate S2?
    coupling:     S1=2 vs S2=3 → S1 better ✅
    cohesion:     S1=0.17 vs S2=0.50 → S1 worse ❌
    → S1 fails → S1 does NOT dominate S2

  Does S2 dominate S1?
    coupling:     S2=3 vs S1=2 → S2 worse ❌
    → S2 fails → S2 does NOT dominate S1

  → Neither dominates the other
```

Why do both survive if neither dominates? Because they are **differently good**, not both bad:

- S1 is better at coupling — more independent services
- S2 is better at cohesion — classes inside each service are more related

They represent different trade-offs. Throwing away either one would mean the algorithm is deciding which trade-off matters more — a decision that belongs to the human architect at the end. So both are kept.

```
S1 [2, 0.17, 3] vs S3 [2, 0.25, 3]
  coupling:     equal
  cohesion:     S3 better (0.25 > 0.17) ✅
  serviceCount: equal
  → S3 dominates S1 (never worse, strictly better in cohesion)

S1 [2, 0.17, 3] vs S4 [3, 0.40, 2]
  coupling:     S1 better ✅
  cohesion:     S4 better ❌
  → neither dominates

S2 [3, 0.50, 2] vs S3 [2, 0.25, 3]
  coupling:     S3 better ❌ for S2
  cohesion:     S2 better ❌ for S3
  → neither dominates

S2 [3, 0.50, 2] vs S4 [3, 0.40, 2]
  coupling:     equal
  cohesion:     S2 better (0.50 > 0.40) ✅
  serviceCount: equal
  → S2 dominates S4

S3 [2, 0.25, 3] vs S4 [3, 0.40, 2]
  coupling:     S3 better ✅
  cohesion:     S4 better ❌
  → neither dominates
```

Count how many solutions dominate each:

```
S1 → dominated by S3 → count = 1
S2 → dominated by nobody → count = 0
S3 → dominated by nobody → count = 0
S4 → dominated by S2 → count = 1
```

Assign fronts:

```
Front 1 (dominated by nobody): S2, S3
Front 2 (dominated by at least one): S1, S4
```

Front 1 is called the **Pareto front** — the set of solutions where you cannot improve one objective without making another worse. These are the best trade-offs found so far.

-----

## Step 4: Crowding Distance

Within each front all solutions have equal rank. We need a tiebreaker when a front is too large to fully fit into the next generation.

The goal is to keep the most **variety** of trade-offs — not keep solutions that are nearly identical to each other.

Imagine Front 1 has 5 solutions and you can only keep 3. Plot them on a line by coupling score:

```
A          B    C  D        E
|__________|____|__|________|
low coupling              high coupling
```

- A and E are boundaries → always kept → infinite distance
- B has large gap on both sides → unique trade-off → high distance → keep
- C and D are crammed together → nearly identical → one gets dropped

Crowding distance is just measuring those gaps. The solution with the smallest gap to its neighbors gets dropped because its neighbor already represents a very similar trade-off — keeping both adds no value.

**Why measure gaps on each objective separately then add them?**

Because you have 3 objectives not 1. A solution might be unique in coupling but have identical cohesion to its neighbor. You measure the gap along each objective axis and sum them to get the total uniqueness of that solution across all dimensions:

```
crowding distance =
  gap to neighbors along coupling axis
+ gap to neighbors along cohesion axis
+ gap to neighbors along serviceCount axis
```

Boundary solutions along any axis always get infinite distance and are always kept — they represent the extremes of the trade-off space and must be preserved.

-----

## Step 5: Selection — Pick Parents

You do NOT compare all solutions against each other. Instead you run many small random 1v1 tournaments:

1. Pick 2 solutions randomly from the pool
2. Compare them: lower front wins — if same front → higher crowding distance wins
3. Winner becomes a parent
4. Repeat until you have enough parents for the next generation

**Why random 1v1 instead of just always taking the top solutions?**

If you always pick the absolute best, the population becomes clones of the same few solutions within a few generations. Diversity collapses and the algorithm gets stuck. Random tournaments keep slightly weaker solutions alive occasionally, which preserves variety and allows the algorithm to keep exploring.

```
Pool: S1(Front2, dist=∞), S2(Front1, dist=∞), S3(Front1, dist=∞), S4(Front2, dist=∞)

Tournament 1: randomly pick S1 vs S2
  S1 is Front2, S2 is Front1 → S2 wins → S2 selected as Parent1

Tournament 2: randomly pick S3 vs S4
  S3 is Front1, S4 is Front2 → S3 wins → S3 selected as Parent2

Parents: S2 and S3
```

-----

## Step 6: Crossover — Combine Parents into Child

A random split point is chosen — say after position 2 out of 4 classes. Everything before the split comes from one parent, everything after comes from the other. The split point is random every generation — this ensures the algorithm explores different combinations rather than always mixing the same halves.

```
S2: [OrderService→B1, PaymentService→B1, | InventoryService→B2, FraudService→B2]
S3: [OrderService→B1, PaymentService→B2, | InventoryService→B2, FraudService→B3]

Child: [OrderService→B1, PaymentService→B1, InventoryService→B2, FraudService→B3]
        ←————— from S2 ——————→               ←————— from S3 ——————→
```

**What do the bucket labels actually mean in the child?**

The bucket labels from each parent mean nothing in isolation. What matters is which classes end up grouped together:

```
Child result:
  B1 group: OrderService, PaymentService   ← came from S2's B1
  B2 group: InventoryService               ← came from S3's B2
  B3 group: FraudService                   ← came from S3's B3
```

The algorithm immediately re-labels them 1, 2, 3 just for bookkeeping. The grouping is what matters, not the label.

-----

## Step 7: Mutation — Randomly Tweak Child

Mutation does not happen to every child — it fires with a small probability (typically 1–5%). This is intentional.

- If you mutate everything → you destroy the good patterns inherited from parents → child becomes random again
- If you never mutate → algorithm can only explore combinations of patterns already in the population → gets stuck

The small probability means occasionally one class gets moved to a different bucket:

```
Before: OrderService→B1, PaymentService→B1, InventoryService→B2, FraudService→B3

Mutation fires on PaymentService (random pick):
  Current bucket: B1
  Move to: B2 (random pick from remaining buckets)

After: OrderService→B1, PaymentService→B2, InventoryService→B2, FraudService→B3
```

Sometimes mutation makes things worse — that is fine. The scoring and selection in the next generation will filter it out. Occasionally mutation discovers a grouping no crossover combination could have reached.

-----

## Step 8: Merge

After producing N children, merge them with the N parents into a pool of 2N.

**Why not just throw away the parents and keep only the children?**

Because a child might be worse than its parent. Discarding the parent permanently loses a good solution. By merging both into 2N and re-ranking everything together, the best N solutions always survive — whether they are parents or children.

```
Parents (N=4): S1, S2, S3, S4
Children (N=4): C1, C2, C3, C4
Merged pool (2N=8): S1, S2, S3, S4, C1, C2, C3, C4
```

All 8 now get scored and sorted into fronts from scratch.

-----

## Step 9: Trim Back to N=4

Fill next generation greedily starting from the best fronts:

```
Merged pool fronts after re-ranking:
  Front 1: S2, S3, C1, C2       (4 solutions)
  Front 2: S1, S4, C3, C4       (4 solutions)

Take all of Front 1 → 4 solutions → 4/4 slots filled → done
Front 2 is completely dropped
```

**What if a front is too large to fully fit?**

```
Front 1: S2, S3, C1, C2, C3, C4   (6 solutions, only 4 slots available)

Sort Front 1 by crowding distance:
  S2:  dist = ∞    (boundary — always kept)
  C4:  dist = ∞    (boundary — always kept)
  C1:  dist = 0.8
  S3:  dist = 0.6
  C2:  dist = 0.3  ← crowded, neighbors cover similar trade-off
  C3:  dist = 0.2  ← most crowded, dropped first

Keep top 4: S2, C4, C1, S3
Drop: C2, C3  ← redundant, their neighbors already represent similar trade-offs
```

-----

## Step 10: Repeat

Go back to Step 2 with the new population of 4. Run for however many generations are defined (e.g. 200).

Each generation the population shifts — solutions that score badly get replaced by better children. The Pareto front slowly moves toward genuinely good decompositions:

```
Generation 1 (random start):
  Best coupling seen: 8    Best cohesion seen: 0.20

Generation 50:
  Best coupling seen: 4    Best cohesion seen: 0.55

Generation 200:
  Best coupling seen: 1    Best cohesion seen: 0.85
```

The algorithm stops when either:

- You hit the max generation limit (e.g. 200)
- The Pareto front stops changing between generations — no child is beating any parent anymore

-----

## Final Output

After 200 generations, Front 1 of the final population is your answer — a set of decompositions each representing a different valid trade-off:

```
Option 1: [coupling=1, cohesion=0.80, serviceCount=5]
  → very independent services, highly cohesive, but more services to manage

Option 2: [coupling=2, cohesion=0.90, serviceCount=3]
  → fewer services, even more cohesive, slightly more cross-service calls

Option 3: [coupling=0, cohesion=0.60, serviceCount=8]
  → zero cross-calls but many small services with moderate cohesion
```

None of these is the single correct answer. A human architect picks whichever trade-off fits their system priorities — team size, deployment constraints, performance requirements.