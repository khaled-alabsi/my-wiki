Here are a mix of architecture patterns, runtime infrastructure, deployment strategies, and reliability practices. Use them as decision tools, not a checklist. The current baseline is that containerized cloud-native systems are mainstream: CNCF’s 2026-published annual survey says 82% of container users run Kubernetes in production, which explains why many of these patterns now show up as Kubernetes, service mesh, gateway, and observability features rather than hand-written code.  


![[Pasted image 20260513110430.jpg]]

1. API Gateway

An API Gateway is the external entry point into a group of backend services. It normally handles L7 routing, TLS termination, authentication, authorization, rate limiting, request transformation, response aggregation, caching, API versioning, logging, tracing, and sometimes protocol translation. Microsoft describes it as a service between client apps and microservices that acts as a reverse proxy and can centralize cross-cutting concerns such as auth, SSL, caching, retries, throttling, tracing, and request transformation.  

Example: a mobile shopping app calls GET /home-screen. The gateway validates the JWT, rate-limits the user, calls catalog-service, pricing-service, inventory-service, and recommendation-service, then returns one compact mobile-optimized DTO.

Pros: it hides internal service topology, reduces client chattiness, centralizes edge security, gives a stable API surface, simplifies client development, and allows internal services to evolve without exposing every internal endpoint.

Cons: it can become a bottleneck, a single point of failure, or a “new ESB” if business orchestration and domain logic accumulate there. It also adds an extra network hop and creates coupling between gateway deployment and backend service contracts. Microsoft explicitly warns that a single custom gateway can become bloated and should often be split by client type or business boundary.  

Common use cases: public APIs, mobile backends, partner APIs, API monetization, auth enforcement, request aggregation, edge caching, protocol translation from HTTP to gRPC/AMQP, and legacy modernization where the gateway hides whether a route is served by the monolith or a new service.

Alternatives: direct client-to-service calls for small/internal systems, Backend for Frontend, GraphQL federation, gRPC gateway, service mesh for east-west traffic, ingress controller only, API composition service, or a modular monolith with one API.

Tools: Kong, Apigee, AWS API Gateway, Azure API Management, NGINX, Envoy Gateway, Traefik, Tyk, KrakenD, Spring Cloud Gateway, Ocelot, YARP, GraphQL Apollo Router.

Implementation advice: keep it thin. The gateway should route, protect, transform, and aggregate. It should not own core business workflows. Add correlation IDs, propagate trace context, set strict timeouts, and make gateway fan-out calls parallel and bounded. For large systems, split gateways by consumer type or domain.

Popularity: very high for external-facing microservice systems. Almost every production microservice platform has some gateway, ingress, or API management layer.

2. Service Discovery

Service Discovery solves this question: “Where is the service instance I should call right now?” In dynamic environments, service instances appear and disappear due to autoscaling, deployments, failures, rescheduling, and node replacement. A service registry stores service names, instances, locations, and often health status. Clients or routers query it to find available instances. Microservices.io describes the registry as a database of services, instances, and locations, with startup registration, shutdown deregistration, and optional health checks.  

Example: orders-service calls payment-service. In Kubernetes, it may call payment.default.svc.cluster.local, which resolves to the service’s cluster IP or, for a headless service, to the backing pod IPs. Kubernetes DNS creates A/AAAA and SRV records for services.  

Pros: removes hardcoded IPs, supports autoscaling, enables rolling deployments, improves failover, and lets services move across nodes or zones without client changes.

Cons: the registry or DNS layer becomes critical infrastructure. Stale records, wrong TTLs, bad health checks, split-brain registries, and client-side caching can route traffic to dead instances. If service discovery is implemented outside the platform, it adds operational burden.

Common use cases: Kubernetes services, VM-based microservices with Consul or Eureka, multi-region discovery, service registration in hybrid cloud, and dynamic discovery for gRPC clients.

Alternatives: static config for tiny systems, DNS-only discovery, cloud load balancer target groups, Kubernetes Services, AWS Cloud Map, service mesh xDS discovery, or serverless endpoints where discovery is abstracted away.

Tools: Kubernetes Service, EndpointSlice, CoreDNS, Consul, Eureka, etcd, ZooKeeper, AWS Cloud Map, Nacos, Envoy xDS, Istio, Linkerd, Consul Connect.

Implementation advice: health checks must reflect readiness, not just process liveness. Cache discovery results, but respect TTLs. Separate liveness from readiness. Use stable logical names, not pod names. For gRPC and long-lived connections, watch connection balancing carefully because DNS resolution alone may not rebalance already-open connections.

Popularity: very high, but often invisible because Kubernetes, service meshes, and cloud platforms provide it by default.

3. Load Balancing

Load Balancing chooses which healthy backend instance receives a request. Service discovery tells you where instances exist; load balancing decides where this request goes.

It can operate at L4, L7, global DNS, client-side, server-side, ingress, east-west, or mesh level. AWS Elastic Load Balancing distributes traffic across targets such as EC2 instances, containers, and IP addresses, monitors target health, and routes only to healthy targets.  

Example: an Application Load Balancer receives HTTPS traffic for api.company.com, terminates TLS, checks path /orders, and routes to the healthy orders-service pods or ECS tasks.

Pros: horizontal scalability, high availability, zero-downtime deployments, health-based routing, traffic splitting, zone failover, and better resource utilization.

Cons: sticky sessions can create imbalance; retries at the load balancer can amplify traffic; bad health checks can remove healthy nodes or keep broken nodes alive; L7 load balancers can become bottlenecks; gRPC, WebSockets, and long-lived HTTP/2 connections need special tuning.

Common algorithms: round robin, weighted round robin, least connections, least request, random, IP hash, consistent hash, locality-aware routing, latency-aware routing, and priority failover. NGINX supports methods such as round robin, least connections, IP hash, generic hash, least time, and random; Envoy supports weighted least request behavior.  

Common use cases: public ingress, service-to-service traffic, canary release, blue-green deployment, multi-AZ failover, tenant isolation, and routing based on path, host, headers, or weights.

Alternatives: DNS load balancing, client-side load balancing, queue-based load leveling, consistent hashing at the application layer, event-driven async processing, or service mesh traffic routing.

Tools: AWS ALB/NLB/GWLB, Azure Load Balancer/Application Gateway/Front Door, GCP Load Balancer, NGINX, HAProxy, Envoy, Traefik, Kubernetes Service, Ingress, Gateway API, Istio, Linkerd, Cilium, F5, Cloudflare, Akamai.

Implementation advice: use health checks that test real dependency readiness for critical paths. Set connection draining for deploys. Configure request, idle, and upstream timeouts. Avoid unlimited retries. For stateful sessions, prefer external session storage over sticky sessions.

Popularity: universal in production. You rarely operate a microservice system without multiple load-balancing layers.

4. Circuit Breaker

A Circuit Breaker prevents repeated calls to a failing or overloaded dependency. It has three classic states: closed, open, and half-open. In closed state, calls pass. If failures or slow calls exceed a threshold, the breaker opens and fails fast. After a wait period, half-open allows a small number of trial calls. If they succeed, the breaker closes; if not, it opens again.

Azure’s architecture guide frames it as a way to temporarily block access to faulty services, prevent repeated unsuccessful attempts, and avoid cascading failures. It also stresses that a circuit breaker is different from retry: retry assumes eventual success, while circuit breaker prevents work that is likely to fail.  

Example: checkout-service calls recommendation-service. Recommendation starts timing out. Without a breaker, checkout threads pile up and the whole checkout path fails. With a breaker, recommendation calls fail fast and checkout returns the page without recommendations.

Pros: protects threads, connection pools, and CPU; prevents cascading failure; gives faster responses under failure; supports graceful degradation; improves resilience to slow dependencies.

Cons: incorrect thresholds can trip too aggressively or too late. Bad fallbacks can hide outages. Breaker state is usually local per process, so different replicas may behave differently. It does not replace timeouts, bulkheads, retries, or proper capacity planning.

Common use cases: synchronous HTTP/gRPC calls, third-party APIs, payment providers, recommendation services, search dependencies, slow databases, cache fallback, and noncritical enrichment calls.

Alternatives and companions: timeouts, retries with exponential backoff and jitter, rate limiting, bulkheads, load shedding, backpressure, queue-based async processing, cached fallback, failover routing, adaptive concurrency limits.

Tools: Resilience4j, Spring Cloud CircuitBreaker, Polly for .NET, Envoy outlier detection, Istio DestinationRule traffic policies, Sentinel, Akka, Opossum for Node.js. Hystrix exists historically but is generally legacy.

Implementation advice: always set a timeout before a circuit breaker. A breaker around a call with a 60-second timeout still lets threads burn for 60 seconds. Track failure rate and slow-call rate. Do not retry blindly inside an open breaker. Emit metrics for open/half-open/closed transitions. Design fallbacks explicitly: cached response, default response, partial response, or user-visible degradation.

Popularity: high in mature systems with synchronous service-to-service dependencies. Less central in fully async flows, but still relevant at edges and third-party integrations.

5. Event-Driven Architecture

Event-driven architecture uses events as the communication primitive. A producer publishes a fact: “OrderCreated,” “PaymentAuthorized,” “CustomerAddressChanged.” Consumers subscribe and react independently. This decouples producers from consumers in time, location, and deployment lifecycle.

Kafka defines event streaming as capturing real-time data as streams of events, storing them durably, processing them in real time or retrospectively, and routing them to destinations. Kafka’s docs also describe producers and consumers as decoupled and topics as multi-producer/multi-subscriber.   AWS EventBridge similarly positions an event bus as a foundation for event-driven architecture that decouples producers from consumers and centralizes routing logic.  

Example: order-service emits OrderCreated. inventory-service reserves stock, payment-service starts payment authorization, email-service sends confirmation, and analytics-service updates dashboards. order-service does not need to know those consumers exist.

Pros: loose coupling, high scalability, fan-out, resilience to consumer downtime, easier integration with analytics, better audit trail, replay capability if using a durable log, and natural fit for long-running workflows.

Cons: eventual consistency, duplicate messages, out-of-order delivery, poison messages, schema evolution, harder debugging, replay hazards, and dual-write problems if database updates and event publishing are not atomic.

Common use cases: order lifecycle, payment processing, notifications, audit logs, integration between bounded contexts, IoT telemetry, fraud detection, analytics pipelines, ML feature pipelines, cache invalidation, search index updates, and CDC-driven projections.

Alternatives: synchronous REST/gRPC, orchestration through workflow engines, batch jobs, polling APIs, shared database integration, direct RPC, GraphQL subscriptions, database triggers, CDC without domain events.

Tools: Kafka, Confluent Platform, Redpanda, RabbitMQ, NATS JetStream, Apache Pulsar, Redis Streams, AWS EventBridge, SNS, SQS, Kinesis, Azure Event Grid, Azure Service Bus, Azure Event Hubs, Google Pub/Sub, Debezium, Kafka Streams, Flink, Spark Structured Streaming, CloudEvents, AsyncAPI, Schema Registry. CloudEvents is useful for standardizing common event metadata and became a CNCF graduated project in 2024.  

Implementation advice: distinguish events from commands. An event is a fact that already happened; a command asks someone to do something. Use the transactional outbox pattern to avoid database-event dual writes. Make consumers idempotent. Version schemas. Use dead-letter queues. Partition by aggregate ID when ordering matters. Avoid “event soup”: define ownership and semantics clearly.

Popularity: very high for integration, streaming data, decoupled workflows, and modern data platforms. It is not a replacement for every synchronous call.

6. CQRS

CQRS means Command Query Responsibility Segregation. It separates the write model from the read model. Commands change state; queries read state and should not mutate it. In simple CQRS, this separation is just in code. In advanced CQRS, the write side and read side have separate databases, with projections updated through events.

Azure defines CQRS as separating read and write operations into separate data models so each model can be optimized independently for performance, scalability, and security.   Martin Fowler’s caution is important: CQRS can be valuable in some situations, but for most systems it adds risky complexity.  

Example: a banking system writes to a strict ledger model optimized for consistency and invariants. The read side projects account summaries, monthly statements, merchant analytics, and fraud dashboards into separate optimized query stores.

Pros: independent read/write scaling, optimized query models, better separation of domain logic from presentation queries, easier handling of complex read views, stronger security boundaries, and good fit with event sourcing.

Cons: more moving parts, duplicated data, eventual consistency, projection lag, rebuild complexity, harder testing, more operational monitoring, and overengineering for basic CRUD systems.

Common use cases: high read/write asymmetry, complex domains with strict write invariants, read-heavy dashboards, search views, reporting, audit systems, event-sourced systems, multi-model persistence, and task-based UIs.

Alternatives: normal CRUD, read replicas, materialized views, reporting database, caching, API composition, search index, denormalized tables, database views, GraphQL resolvers, or a modular monolith.

Tools: Axon Framework, Eventuate, EventStoreDB, Kafka Streams, Flink, Materialize, Debezium, Elasticsearch/OpenSearch, Redis, MongoDB projections, DynamoDB streams, MediatR for .NET, NestJS CQRS, Spring Boot with domain events. Axon explicitly targets event-driven systems based on DDD, CQRS, and Event Sourcing, with components like command buses, event stores, query buses, and sagas.  

Implementation advice: do not start with CQRS everywhere. Apply it per bounded context or per hot path. Define projection ownership. Track projection version and lag. For “read your writes,” use session state, query-side version checks, polling, or command result DTOs. Never assume the read model is instantly consistent unless you designed it that way.

Popularity: medium. Common in complex enterprise domains and event-sourced systems, but often misused in simple CRUD applications.

7. Saga

A Saga manages a business transaction that spans multiple services without using a single distributed database transaction. It breaks the transaction into local transactions. Each service commits its own database change and triggers the next step through messages or events. If a later step fails, compensating actions undo prior completed steps.

Azure describes a saga as a sequence of local transactions where each service performs its operation and initiates the next step through events or messages; if a step fails, compensating transactions undo completed steps.   AWS notes that sagas help maintain consistency across microservices without tight coupling, support long-lived transactions, and enable rollback when an operation fails. AWS also warns that sagas are difficult to debug and become more complex as the number of microservices grows.  

Example: order placement requires reserving inventory, authorizing payment, creating shipment, and confirming the order. If shipment creation fails, the saga releases inventory and voids payment authorization.

Two main styles: choreography and orchestration. In choreography, each service reacts to events and emits new events. In orchestration, a central workflow coordinator tells each participant what to do. Choreography is simpler for small workflows but can become hard to reason about. Orchestration gives visibility and control but introduces a coordinator.

Pros: avoids distributed locks and 2PC, fits database-per-service, supports long-running workflows, improves service autonomy, and models real business compensation.

Cons: compensation is not always a true undo. No global isolation. Race conditions and inconsistent intermediate states are normal. Debugging is hard. Idempotency is mandatory. Choreography can create cyclic dependencies. Orchestration can become a central workflow dependency.

Common use cases: order management, payment and inventory, travel booking, subscription provisioning, KYC onboarding, loan approval, insurance claims, refund workflows, fulfillment, and multi-step partner integrations.

Alternatives: keep the transaction inside one service, modular monolith, database transaction, two-phase commit/XA for tightly controlled environments, reservation/escrow model, eventual reconciliation, manual workflow, or redesigning bounded contexts to avoid cross-service transactions.

Tools: Temporal, Cadence, AWS Step Functions, Camunda, Zeebe, Netflix Conductor, Azure Durable Functions, Dapr Workflow, Axon Saga, Eventuate Tram Sagas, Kafka, RabbitMQ, NATS, BPMN engines.

Implementation advice: design every step with idempotency keys. Persist saga state. Define compensating actions before implementation. Use timeouts and retries. Make the pivot transaction explicit: before the pivot, compensate; after the pivot, retry until success or escalate. Emit trace IDs across the entire saga.

Popularity: medium to high in serious microservice systems. If you use database-per-service and have cross-service business workflows, sagas become difficult to avoid.

8. Service Mesh

A Service Mesh is a dedicated infrastructure layer for service-to-service communication. It usually consists of a control plane and a data plane. The data plane is often Envoy sidecars or a newer sidecarless/ambient model. It handles cross-cutting network concerns without requiring each application team to implement them.

Microsoft defines service mesh as an infrastructure layer that transparently adds observability, traffic management, and security without adding that code to services. It can cover discovery, load balancing, failure recovery, metrics, monitoring, A/B testing, canary deployments, rate limiting, access control, encryption, and end-to-end authentication.   Istio also generates telemetry for service communications, including metrics, distributed traces, and access logs.  

Example: all calls between orders-service and payments-service use mutual TLS. Traffic to payments-v2 is shifted from 1% to 10% to 50%. Retries, timeouts, and telemetry are enforced consistently through mesh policy.

Pros: uniform mTLS, service identity, policy enforcement, traffic splitting, retries, timeouts, circuit breaking, observability, and consistent behavior across polyglot services.

Cons: significant operational complexity, extra latency and resource cost, proxy debugging, control-plane upgrades, sidecar lifecycle issues, and a need for specialized platform knowledge. CNCF’s 2024 survey reported service mesh production use in roughly 42% of respondent organizations, down from 50% in 2023, citing complexity, cost, performance, and operational overhead as likely factors.  

Common use cases: zero-trust internal networking, regulated environments, large polyglot Kubernetes fleets, canary releases, service-level authorization, mTLS, traffic mirroring, and platform-level observability.

Alternatives: application libraries, API gateway only, Kubernetes NetworkPolicy plus ingress, Cilium/eBPF-based networking, Envoy without full mesh, cloud-native load balancers, SPIFFE/SPIRE with app-level mTLS, or simply using platform defaults for small systems.

Tools: Istio, Linkerd, Consul Connect, Cilium Service Mesh, Kuma, Envoy, SPIFFE, SPIRE, cert-manager, cloud service mesh offerings from major cloud providers.

Implementation advice: do not add a service mesh just because you use microservices. Add it when the pain is real: mTLS at scale, policy, traffic shaping, or uniform telemetry. Start with a few namespaces. Standardize timeouts and retries carefully; mesh-level retries can amplify failures if application retries already exist.

Popularity: selective. Common in larger Kubernetes platforms, less common in small teams because the operational cost is real.

9. Distributed Tracing

Distributed tracing follows a single request or business operation across multiple services, queues, databases, and external calls. A trace is made of spans. Each span represents one unit of work: an HTTP handler, DB query, queue publish, queue consume, RPC call, or internal operation.

OpenTelemetry defines a span as a unit of work and the building block of traces, with fields like name, parent span ID, timestamps, span context, attributes, events, links, and status. It also explains that context propagation lets traces build causal information across services and process boundaries.   W3C Trace Context standardizes headers such as traceparent and tracestate so trace identity can propagate across vendors and platforms.  

Example: a single checkout request creates spans for API gateway, auth, cart, pricing, payment, fraud check, inventory reservation, DB writes, and Kafka event publish. The trace shows that fraud-service added 700 ms and caused timeout retries.

Pros: root-cause analysis, latency breakdown, dependency mapping, incident debugging, SLO analysis, async workflow visibility, and correlation between logs, metrics, and traces.

Cons: sampling can miss rare failures, trace volume can be expensive, high-cardinality attributes can explode cost, async context propagation is easy to break, PII can leak into spans, and instrumentation quality varies.

Common use cases: microservice latency debugging, production incident response, saga debugging, dependency mapping, external API performance, queue lag analysis, and bottleneck discovery.

Alternatives and companions: structured logs with correlation IDs, metrics using RED/USE methods, profiling, synthetic monitoring, RUM, audit logs, APM agents, service mesh telemetry.

Tools: OpenTelemetry SDKs and Collector, Jaeger, Zipkin, Grafana Tempo, Honeycomb, Datadog, New Relic, Dynatrace, Elastic APM, AWS X-Ray, Google Cloud Trace, Azure Application Insights. Jaeger is a CNCF graduated distributed tracing platform used to monitor workflows, identify bottlenecks, find root causes, and analyze dependencies.  

Implementation advice: standardize on OpenTelemetry. Instrument service entry/exit, HTTP clients, gRPC clients, DB clients, messaging producers/consumers, and workflow engines. Propagate context through queues using message headers. Use span links for async fan-out where parent-child does not fit. Add business attributes sparingly: order.id may be useful; raw user PII is not.

Popularity: high in nontrivial microservice systems. Without tracing, debugging becomes guesswork once requests cross several services.

10. Containerization

Containerization packages an application and its dependencies into an image that runs as an isolated process. Docker defines a container as a standard unit of software that packages code and dependencies so the application runs reliably across environments; Docker’s docs also describe containers as self-contained, isolated, independent, and portable.  

Example: a Spring Boot service is built into an OCI image, scanned, pushed to a registry, and deployed as six Kubernetes pods behind a service.

Pros: consistent runtime, portable deployment, immutable releases, fast startup compared with VMs, efficient resource usage, dependency isolation, and strong fit with CI/CD.

Cons: image vulnerabilities, base image maintenance, orchestration complexity, storage and networking complexity, secrets management, cold image pulls, container escape risks, and stateful workload difficulty.

Common use cases: stateless APIs, workers, batch jobs, ML inference services, sidecars, local development environments, CI builds, and platform standardization.

Alternatives: VMs, PaaS, serverless functions, bare-metal processes, systemd services, buildpacks without explicit Dockerfiles, WebAssembly workloads, or modular monolith deployments.

Tools: Docker, Podman, Buildah, BuildKit, Kaniko, containerd, CRI-O, runc, Kubernetes, Helm, Kustomize, Skaffold, Tilt, Docker Compose, ECR, ACR, GAR, Harbor, Trivy, Grype, Syft, Cosign, SLSA tooling.

Implementation advice: use small base images, pin dependencies, run as non-root, set CPU/memory limits, implement graceful shutdown, add readiness/liveness probes, generate SBOMs, scan images, sign images, avoid baking secrets into images, and use multi-stage builds.

Popularity: very high. Containerization is now the default packaging model for many cloud-native systems, especially Kubernetes-based platforms.

11. Database per Service

Database per Service means each service owns its data. Other services do not directly read or write its tables. They access its data through APIs, events, or replicated read models. The physical implementation can be a separate database server, separate database, separate schema, or separate collection, but the ownership boundary must be real.

AWS describes this pattern as loose coupling: each microservice stores and retrieves information from its own data store, other microservices cannot directly access that store, and persistent data is accessed only through APIs. AWS also notes that it allows different services to choose different data stores but makes cross-service queries and transactions harder.  

Example: orders-service uses PostgreSQL, catalog-service uses MongoDB, payments-service uses a ledger database, and search-service owns an OpenSearch projection built from events.

Pros: service autonomy, independent schema evolution, independent scaling, better encapsulation, polyglot persistence, failure isolation, and clearer bounded contexts.

Cons: cross-service joins are hard, distributed transactions require sagas, data duplication increases, eventual consistency appears, reporting becomes harder, and operational cost rises because multiple databases must be managed.

Common use cases: independently owned domains, teams deploying independently, different compliance requirements, different data models, scaling hot services separately, and reducing shared database coupling.

Alternatives: shared database, schema-per-service inside one database engine, modular monolith, data warehouse/lake for reporting, CQRS projections, API composition, event sourcing, CDC replication.

Tools: PostgreSQL, MySQL, MongoDB, Cassandra, DynamoDB, Redis, Elasticsearch/OpenSearch, Kafka, Debezium, Flyway, Liquibase, Schema Registry, outbox pattern libraries, CDC pipelines, API composition layers.

Implementation advice: do not allow “just this one direct query” from another service. That is how the boundary dies. Use domain events for replication. Use API composition or CQRS for cross-service reads. Use sagas for cross-service writes. For analytics, export to a warehouse rather than letting BI tools query production service databases.

Popularity: high as an architectural principle, but difficult in practice. Many organizations start with shared databases and gradually move toward stronger ownership as service boundaries mature.

12. Bulkhead

Bulkhead isolates resources so one failing part of the system does not sink everything else. The name comes from ship compartments: if one compartment floods, the ship can still survive.

Azure defines the Bulkhead pattern as isolating application elements into pools so that if one fails, others continue to function. It gives examples such as separate connection pools per service and isolated service instances per client.  

Example: checkout-service has separate thread pools and connection pools for payment-service, inventory-service, and recommendation-service. If recommendations hang, only the recommendation pool is exhausted. Payments still work.

Pros: failure containment, better resilience, predictable degradation, tenant isolation, critical-path protection, and reduced cascading failures.

Cons: capacity fragmentation, more tuning, idle reserved resources, configuration complexity, and possible underutilization if partitions are too strict.

Common use cases: third-party calls, critical vs noncritical features, tenant isolation, priority traffic, connection pools, thread pools, queues, Kubernetes namespaces, node pools, and regional isolation.

Alternatives and companions: circuit breaker, rate limiter, backpressure, load shedding, priority queues, autoscaling, queue-based load leveling, timeout policies, resource quotas.

Tools: Resilience4j Bulkhead, Polly Bulkhead, Envoy/Istio connection pool limits, Kubernetes ResourceQuota, LimitRange, namespaces, node pools, PodDisruptionBudgets, separate deployments, Akka dispatchers, executor pools, DB pool configuration.

Implementation advice: isolate by dependency, tenant, priority, and failure domain. Protect the critical path first. Combine bulkheads with timeouts and circuit breakers. A bulkhead without timeouts still fills up eventually.

Popularity: medium-high. Mature systems use it, but it is often implicit in thread pools, connection pools, Kubernetes quotas, and deployment topology rather than named explicitly.

13. BFF — Backend for Frontend

A BFF is a specialized backend for a specific frontend or client type. Instead of one general API gateway trying to serve web, mobile, TV, partner, and admin clients equally, each client gets a tailored backend.

Microsoft notes that the API Gateway pattern is sometimes called Backend for Frontend and recommends splitting gateways per client app form factor when different clients have different needs.  

Example: mobile-bff returns compact payloads, uses mobile-friendly pagination, hides fields not needed on small screens, and aggregates calls to reduce round trips. web-bff returns richer data and admin links. tv-bff optimizes for remote-control navigation and low interaction complexity.

Pros: optimized UX contracts, fewer client round trips, independent frontend team velocity, reduced client complexity, better API evolution per channel, and cleaner separation than one bloated gateway.

Cons: duplicate logic across BFFs, inconsistent behavior between clients, too many BFFs, increased maintenance, auth/session complexity, and risk that BFFs become mini-monoliths.

Common use cases: mobile apps, SPAs, TV apps, partner portals, admin portals, multi-brand frontends, legacy clients, and frontend teams with independent release cycles.

Alternatives: single API gateway, GraphQL federation, direct service APIs, generated SDKs, API composition service, edge functions, HATEOAS-style APIs, or a frontend using multiple backend APIs directly.

Tools: Node.js, NestJS, Express, Fastify, Spring Boot/WebFlux, ASP.NET Core, YARP, Ocelot, Next.js API routes, Apollo GraphQL, GraphQL Mesh, AWS Lambda/API Gateway, Azure Functions, Cloudflare Workers.

Implementation advice: put client-specific composition in the BFF, not domain rules. Shared business rules belong in domain services. Use contract tests between BFF and backend services. Keep auth standards consistent across BFFs. Track per-client latency and payload size.

Popularity: high when there are multiple serious client channels, especially mobile plus web. Less useful for internal systems with one UI.

14. Blue-Green Deployment

Blue-green deployment uses two production-like environments. Blue is the current live version. Green is the new version. You deploy and validate green, then shift traffic from blue to green. If something breaks, shift back.

AWS describes blue-green deployment as a release methodology that reduces downtime and risk by running two identical production environments, validating the new revision before directing production traffic to it, and allowing quick rollback. AWS also notes that both environments may run simultaneously, which can double resource usage during deployment.  

Example: orders-v1 is blue and receives 100% traffic. You deploy orders-v2 to green, run smoke tests and synthetic traffic, then flip the load balancer to green. Blue stays warm during bake time. If metrics degrade, flip back.

Pros: fast rollback, low downtime, production-like validation, clear release boundary, simpler mental model than complex rolling behavior, and useful for high-risk releases.

Cons: double infrastructure cost during deployment, database migration complexity, cache warming, session compatibility, background jobs duplication, event consumer duplication, and environment drift.

Common use cases: critical APIs, high-traffic web apps, regulated releases, risky upgrades, platform migrations, and deployments where rollback speed matters.

Alternatives: rolling deployment, canary release, feature flags, shadow traffic, A/B testing, recreate deployment, progressive delivery, traffic mirroring, dark launch.

Tools: Kubernetes Services/Ingress, Argo Rollouts, Flagger, Spinnaker, Harness, AWS CodeDeploy, ECS blue-green, Elastic Beanstalk swap, Azure App Service deployment slots, Cloud Foundry blue-green, NGINX, Envoy, Istio, Linkerd.

Implementation advice: the hard part is the database. Use expand-contract migrations: add backward-compatible schema first, deploy new app, migrate data, then remove old schema later. Avoid destructive migrations during cutover. Externalize sessions. Ensure only one environment runs singleton jobs unless intentionally duplicated.

Popularity: high as a deployment strategy, especially where rollback needs to be fast and downtime is unacceptable. Canary and progressive delivery are often preferred when gradual risk exposure is needed.

15. Strangler Fig

Strangler Fig is a modernization pattern for gradually replacing a legacy system. You place a façade or proxy in front of the old system. New functionality is built outside the legacy system. The façade routes migrated functionality to new services and unmigrated functionality to the legacy system. Over time, the new system replaces the old one.

Azure describes it as incrementally migrating a legacy system by gradually replacing specific pieces of functionality with new applications and services, with a façade intercepting requests and routing them either to the legacy application or new services.  

Example: a monolith serves /catalog, /checkout, /billing, and /profile. First, route /catalog to a new catalog service. Then extract checkout. Billing remains in the monolith until its data and workflows are understood. Eventually the monolith has no routes left and is retired.

Pros: avoids big-bang rewrite, reduces migration risk, delivers value incrementally, allows production learning, preserves existing clients, and supports phased team ownership.

Cons: temporary complexity, duplicated logic, data synchronization problems, routing complexity, long-lived hybrid architecture, hidden coupling to legacy data, and risk that the migration stalls halfway.

Common use cases: monolith decomposition, legacy API replacement, platform migration, cloud migration, replacing vendor systems, rewriting high-change modules first, and isolating risky legacy components.

Alternatives: big-bang rewrite, modularizing the monolith first, branch by abstraction, replatforming, rehosting, buy/replace with SaaS, extracting only one service, or keeping the monolith if it is stable and cheap to maintain.

Tools: API gateways, NGINX, Envoy, Kong, Apigee, feature flags, CDC with Debezium, outbox pattern, anti-corruption layers, contract testing with Pact, OpenRewrite, telemetry dashboards, traffic shadowing.

Implementation advice: start with seams: routes, modules, tables, or workflows that can be isolated. Build an anti-corruption layer so legacy models do not infect the new domain. Avoid uncontrolled dual writes. Use CDC or explicit events where possible. Track migration progress by routes, data ownership, and business capabilities, not by number of extracted services.

Popularity: high in enterprise modernization. It is one of the safer ways to move from monolith to services.

How these patterns combine in real systems

A sane production baseline often looks like this: containerized services on Kubernetes; service discovery and load balancing from the platform; an API Gateway or BFF at the edge; database ownership per bounded context; timeouts, retries, circuit breakers, and bulkheads for synchronous calls; event-driven messaging plus outbox for decoupling; sagas for real cross-service business transactions; OpenTelemetry tracing everywhere; blue-green or canary for deployment; and strangler fig for legacy migration.

The dangerous version is cargo-cult microservices: every service has its own DB before boundaries are understood, every query becomes CQRS, every workflow becomes a saga, every cluster gets a service mesh, and every deployment pipeline adds blue-green without solving database compatibility. That produces distributed pain, not architecture.

A practical adoption order is usually: first get boundaries right, then containerize and automate deployments, then add observability, then add resilience patterns, then introduce async events where coupling hurts, then use sagas/CQRS/service mesh only where the complexity is justified.