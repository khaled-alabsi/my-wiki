So4MoD stands for Security-Optimized approach for Microservice-Oriented Decomposition. It is essentially NSGA-II with one major new idea — security is added as an explicit objective alongside the usual coupling and cohesion.

Step 1: Static Analysis of Source Code
Same as MSExtractor — reads source code without running the app. Extracts the call graph and class relationships.
But So4MoD does one extra thing here: it identifies sensitive data in the codebase. It looks for classes and fields that handle things like:

UserCredentials    → sensitive (passwords, tokens)
PaymentDetails     → sensitive (card numbers, bank accounts)
OrderHistory       → less sensitive (public data)
ProductCatalogue   → not sensitive (public data)


This sensitivity classification is what makes So4MoD different — it knows which data is dangerous to expose.

Step 2: Score Every Solution — 3 Objective Categories
So4MoD optimizes both security and modularity simultaneously using five adapted security metrics alongside standard modularity metrics. ￼
Modularity objectives (same as what you already know):

Coupling     → cross-boundary calls → lower better
Cohesion     → internal calls → higher better


Security objective — this is the new addition:
The core idea is: sensitive data classes should not be grouped together with non-sensitive classes in the same service.
Why? Because if UserCredentials and ProductCatalogue live in the same service, any attacker who breaches the product catalogue endpoint potentially gains access to user credentials too. Sensitive data should be isolated in its own tightly controlled service.
So4MoD measures security of a decomposition by checking how well sensitive classes are isolated:

Solution 1:
  Bucket-1: UserCredentials, PaymentDetails   → both sensitive → isolated ✅
  Bucket-2: OrderService, ProductCatalogue    → both non-sensitive → isolated ✅
  Security score = HIGH

Solution 2:
  Bucket-1: UserCredentials, ProductCatalogue → mixed! sensitive + non-sensitive ❌
  Bucket-2: PaymentDetails, OrderService      → mixed! sensitive + non-sensitive ❌
  Security score = LOW


Final score vector per solution:

[coupling=2, cohesion=0.6, security=0.85]


Step 3: Run Modified NSGA-II
So4MoD uses a multi-objective optimization algorithm based on NSGA-II to search for microservices with optimized security and modularity together. ￼
Exactly the NSGA-II you already know — Pareto fronts, crowding distance, tournament selection, crossover, mutation — but now with 3 objectives instead of 2. The security score participates in dominance comparisons just like coupling and cohesion.

S1 [coupling=2, cohesion=0.6, security=0.85]
S2 [coupling=1, cohesion=0.7, security=0.40]

  S1 better at security
  S2 better at coupling and cohesion
  → neither dominates → both survive


This means the algorithm now preserves trade-offs across three dimensions — you might get a very secure decomposition that is slightly less cohesive, or a very cohesive one that is slightly less secure. The human picks at the end.

Step 4: Output
Same as NSGA-II — Front 1 of the final generation, a set of trade-off decompositions.

How So4MoD differs from FoSCI and MSExtractor



|                  |FoSCI           |MSExtractor        |So4MoD            |
|------------------|----------------|-------------------|------------------|
|Input             |Runtime traces  |Source code        |Source code       |
|Needs running app |Yes             |No                 |No                |
|Algorithm         |Modified NSGA-II|IBEA               |NSGA-II           |
|Security objective|No              |No                 |Yes               |
|Key innovation    |Dynamic traces  |Semantic similarity|Security isolation|

Why So4MoD was still not enough
It adds security as a number — how isolated are the sensitive classes. But it still cannot reason about meaning. It does not understand that a class called AuditLogger is security-related even if it never touches a field labelled sensitive. It only knows what it can count or classify from surface-level code analysis. That limitation is shared by all three prior GA methods.​​​​​​​​​​​​​​​​