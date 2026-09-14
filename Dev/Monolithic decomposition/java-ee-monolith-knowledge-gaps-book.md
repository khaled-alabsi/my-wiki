# Java EE Monolith Knowledge Gaps for Spring Boot Developers

## Table of Contents

- [[#How to Use This Book|How to Use This Book]]
- [[#Mental Model First|Mental Model First]]
- [[#Part 1 Closest to Spring Boot|Part 1: Closest to Spring Boot]]
  - [[#1 Servlet Request Flow|1. Servlet Request Flow]]
  - [[#2 Filters and Listeners|2. Filters and Listeners]]
  - [[#3 JSP and Server-Side Rendering|3. JSP and Server-Side Rendering]]
  - [[#4 JPA in Java EE|4. JPA in Java EE]]
  - [[#5 Logging and Runtime Diagnostics|5. Logging and Runtime Diagnostics]]
- [[#Part 2 Similar Concepts Different Configuration|Part 2: Similar Concepts, Different Configuration]]
  - [[#6 webxml Configuration|6. web.xml Configuration]]
  - [[#7 persistencexml|7. persistence.xml]]
  - [[#8 Server-Managed DataSources|8. Server-Managed DataSources]]
  - [[#9 Java EE Security Model|9. Java EE Security Model]]
  - [[#10 JMS Queues and Topics|10. JMS Queues and Topics]]
- [[#Part 3 Java EE Container Concepts|Part 3: Java EE Container Concepts]]
  - [[#11 Application Server Mindset|11. Application Server Mindset]]
  - [[#12 Container-Managed Lifecycle|12. Container-Managed Lifecycle]]
  - [[#13 Container-Managed EntityManager|13. Container-Managed EntityManager]]
  - [[#14 Container-Managed Transactions|14. Container-Managed Transactions]]
  - [[#15 JTA Transaction Model|15. JTA Transaction Model]]
- [[#Part 4 Packaging and Deployment|Part 4: Packaging and Deployment]]
  - [[#16 WAR and EAR Packaging|16. WAR and EAR Packaging]]
  - [[#17 Deployment Descriptors|17. Deployment Descriptors]]
  - [[#18 Vendor-Specific Descriptors|18. Vendor-Specific Descriptors]]
  - [[#19 Server Configuration|19. Server Configuration]]
  - [[#20 Running Legacy Benchmark Monoliths|20. Running Legacy Benchmark Monoliths]]
- [[#Part 5 More Java EE-Specific Less Spring-Like|Part 5: More Java EE-Specific, Less Spring-Like]]
  - [[#21 JNDI Resource Lookup|21. JNDI Resource Lookup]]
  - [[#22 EJB Basics|22. EJB Basics]]
  - [[#23 Stateless Session Beans|23. Stateless Session Beans]]
  - [[#24 Stateful Session Beans|24. Stateful Session Beans]]
  - [[#25 Singleton Beans|25. Singleton Beans]]
  - [[#26 Message-Driven Beans|26. Message-Driven Beans]]
- [[#Part 6 Hardest Most Legacy-Painful|Part 6: Hardest / Most Legacy-Painful]]
  - [[#27 Application Server Classloading|27. Application Server Classloading]]
  - [[#28 Dependency Conflicts|28. Dependency Conflicts]]
  - [[#29 Java EE Version Differences|29. Java EE Version Differences]]
  - [[#30 javax vs jakarta|30. javax vs jakarta]]
- [[#Practical Study Plan|Practical Study Plan]]
- [[#Benchmark Monolith Reading Checklist|Benchmark Monolith Reading Checklist]]
- [[#Resource Index|Resource Index]]

## How to Use This Book

This guide is written for someone who already knows Java and Spring Boot, but now needs to read, run, debug, or modify older Java EE monoliths such as benchmark systems like JPetStore-style applications, DayTrader-style applications, Plants-style applications, or AcmeAir-style applications.

The goal is not to teach Java from zero. The goal is to identify the exact missing layer between a modern Spring Boot mental model and a traditional Java EE monolith mental model.

The shortest summary is this:

Spring Boot usually feels application-owned. The application starts, creates the Spring context, configures many components from local configuration files, starts an embedded server, and exposes endpoints.

Java EE usually feels server-owned. The application server is already running. Your application is deployed into it. The server creates components, injects resources, manages transactions, enforces security, controls classloading, exposes server-managed resources, and decides how modules interact.

So your knowledge gap is not “Java.” It is “server-managed enterprise Java.”

The learning order in this book goes from familiar to unfamiliar. Start with web request flow and persistence because they resemble Spring Boot ideas. Then move toward deployment, EJBs, JNDI, transactions, application server behavior, classloading, and version migration.

Recommended official references:

- Jakarta EE Tutorial: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/index.html
- Jakarta EE specifications: https://jakarta.ee/specifications/
- Open Liberty Jakarta EE overview: https://openliberty.io/docs/latest/jakarta-ee.html
- WildFly documentation: https://docs.wildfly.org/
- IBM Liberty EJB documentation: https://www.ibm.com/docs/en/was-liberty/base?topic=environment-developing-ejb-applications-liberty
- Spring Boot Reference Documentation: https://docs.spring.io/spring-boot/

## Mental Model First

Before going through the individual sections, fix this model in your head:

Java is the language and runtime.

Spring Boot is a framework that builds applications around the Spring container. It usually embeds the HTTP server inside the application.

Java EE, now Jakarta EE, is a platform specification for enterprise applications. It expects a compliant application server to provide services such as HTTP handling, dependency injection, persistence integration, transaction management, security, messaging, resource lookup, and deployment lifecycle.

In Spring Boot, you often ask: “How is this bean configured in the application?”

In Java EE, you often ask: “Which container is responsible for this, and where is the server-side configuration?”

In Spring Boot, you often debug by looking at application properties, auto-configuration, bean definitions, and dependencies.

In Java EE, you often debug by looking at deployment descriptors, server resources, JNDI bindings, data source definitions, security realms, transaction configuration, application server logs, and classloading behavior.

The biggest trap for Spring Boot developers is assuming that everything important is inside the application repository. In old Java EE monoliths, that is frequently false. Some critical runtime information may live in the application server configuration, not in the app.

---

# Part 1: Closest to Spring Boot

This group contains concepts that should feel familiar because Spring Boot still uses or builds on many of them. Spring MVC itself runs on the Servlet API in typical blocking web applications. JPA is also familiar if you have used Spring Data JPA or Hibernate. Logging and diagnostics are conceptually the same, although the sources of logs and errors differ.

## 1. Servlet Request Flow

### What it is

The Servlet API is the classic Java web foundation. A servlet receives HTTP requests and produces HTTP responses. It is lower-level than a Spring MVC controller.

In a Spring Boot web application, you normally write controllers and let Spring MVC handle the servlet details. But underneath, a servlet container such as Tomcat, Jetty, or Undertow receives the request. The Spring DispatcherServlet then routes the request to controllers.

In Java EE monoliths, you may see the servlet layer more directly. The application might define servlets explicitly. Requests might be mapped to servlets through XML configuration or annotations. Some business logic might even live directly inside servlets in older applications.

### Why it matters for monoliths

When you open an old Java EE application, the first task is often to answer:

Where does this URL go?

In Spring Boot, you usually search for controller mappings. In Java EE, you may need to inspect servlet mappings, web.xml, filters, JSP forwards, request dispatchers, and sometimes framework-specific front controllers.

A benchmark monolith may have request paths that do not map neatly to annotation-based controllers. Instead, a request may flow through:

Browser or load test client → application server HTTP connector → servlet container → filter chain → servlet → business component → persistence layer → JSP or response writer.

Understanding servlet flow lets you find the real entry point.

### Spring Boot comparison

Spring Boot with Spring MVC usually hides raw servlet work behind controllers. But the underlying request path still includes the servlet container, filters, and DispatcherServlet.

Java EE monoliths often expose more of that machinery. You may need to read configuration files instead of relying on annotations.

### What to learn

Learn the request and response objects conceptually. Learn servlet lifecycle. Learn URL mapping. Learn how sessions work. Learn request attributes versus session attributes. Learn forwarding versus redirecting. Learn how filters wrap request processing.

You do not need to become a servlet specialist first. You need enough knowledge to trace a request from URL to business logic.

### What to inspect in a monolith

Look for web.xml. Look for classes whose names include Servlet. Look for URL pattern mappings. Look for JSP files that are forwarded to. Look for filters that intercept all requests. Look for custom front controllers.

### Common bugs

A servlet mapping catches more URLs than expected.

A filter changes the request or session before the servlet sees it.

A redirect loses request attributes because it starts a new request.

A forward keeps request attributes but changes which server-side resource handles rendering.

A session object is assumed to exist but was not created.

Load tests behave strangely because session state is mixed with request routing.

### Resources

- Jakarta Servlet specification: https://jakarta.ee/specifications/servlet/
- Jakarta EE Tutorial, Web Tier: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/index.html
- Tomcat Servlet documentation: https://tomcat.apache.org/tomcat-10.1-doc/servletapi/
- Spring Boot reference, web applications: https://docs.spring.io/spring-boot/reference/web/index.html

## 2. Filters and Listeners

### What they are

A filter is a component that intercepts requests before and after the main servlet or resource. It can inspect, modify, block, wrap, log, authenticate, authorize, compress, or transform request and response handling.

A listener observes lifecycle events. It can react when the web application starts, when it shuts down, when a session is created, when a session is destroyed, or when request lifecycle events happen.

### Why they matter for monoliths

Old Java EE monoliths often use filters for cross-cutting behavior. Authentication, logging, encoding, session checks, request timing, tenant resolution, and transaction-like patterns may live in filters.

Listeners may initialize application resources at startup. In a legacy app, some global state or cache may be created by a listener before any servlet handles requests.

If you only search for servlets or business classes, you may miss important behavior happening before the request reaches them.

### Spring Boot comparison

Spring Boot also has filters, interceptors, servlet context initializers, and application events. The difference is that in Spring Boot, these are often configured as Spring beans. In older Java EE apps, filters and listeners may be declared in web.xml or through servlet annotations.

A Spring MVC HandlerInterceptor is not the same as a servlet filter. A filter sits at the servlet container level. A HandlerInterceptor sits inside Spring MVC after the request has entered the Spring dispatcher.

In Java EE monoliths, the filter layer can be the main cross-cutting layer.

### What to learn

Learn filter chain ordering. Learn the difference between pre-processing and post-processing. Learn how a filter can stop a request from continuing. Learn listener types. Learn how startup listeners initialize state.

### What to inspect in a monolith

Look in web.xml for filter and listener declarations. Check URL patterns. Check ordering. Search for classes ending with Filter or Listener. Inspect whether filters wrap requests or responses. Inspect whether listeners create global resources.

### Common bugs

Filter ordering is wrong.

A filter blocks requests because of stale session assumptions.

A listener fails during application startup, preventing deployment.

A filter consumes the request body, so downstream code cannot read it.

Character encoding is set too late.

A filter assumes a specific URL shape that changes under a reverse proxy or benchmark driver.

### Resources

- Jakarta Servlet specification: https://jakarta.ee/specifications/servlet/
- Jakarta EE Tutorial, Web Applications: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/index.html
- Open Liberty Servlet feature docs: https://openliberty.io/docs/latest/reference/feature/servlet.html
- Spring Framework filter reference: https://docs.spring.io/spring-framework/reference/web/webmvc/filters.html

## 3. JSP and Server-Side Rendering

### What it is

JSP means JavaServer Pages. It is a server-side view technology. A JSP page is processed on the server and produces HTML or other text output.

In older Java EE applications, JSPs are commonly used for user interfaces. A servlet may prepare data, put it into request or session attributes, and forward to a JSP for rendering.

### Why it matters for monoliths

Many benchmark or legacy monoliths predate modern SPA frontends and REST-first design. Their UI may be generated by JSPs. Even when the benchmark focuses on backend performance, JSPs may still exist as part of the application.

Understanding JSP matters because business logic sometimes leaks into JSPs. You may find database access, formatting logic, conditional behavior, or session manipulation directly in view files. This is not ideal architecture, but it is common in older code.

### Spring Boot comparison

In Spring Boot, you may have used Thymeleaf, Freemarker, Mustache, or REST APIs returning JSON. JSP is conceptually similar to server-side templates, but older and more tightly linked to the servlet container.

JSPs are compiled into servlets by the container. That means JSP errors can show up as generated servlet compilation errors, which can be confusing if you do not expect it.

### What to learn

Learn the role of JSP as a view. Learn request attributes and session attributes. Learn JSP expression language. Learn tag libraries. Learn the difference between rendering HTML and redirecting to another request.

You do not need to master old scriptlet style, but you should recognize it. Scriptlets are Java fragments inside JSP files and are a sign of older style code.

### What to inspect in a monolith

Look for .jsp files. Look for WEB-INF views. Look for tag library declarations. Look for request.setAttribute-like behavior in servlets. Look for forwards to JSP paths. Look for session usage.

### Common bugs

A JSP expects a request attribute that was never set.

A redirect is used instead of forward, losing request attributes.

A JSP contains logic that should have been in a service, making behavior hard to find.

A tag library is missing from the runtime.

JSP compilation fails because of old Java or app server compatibility.

### Resources

- Jakarta Server Pages specification: https://jakarta.ee/specifications/pages/
- Jakarta Standard Tag Library specification: https://jakarta.ee/specifications/tags/
- Jakarta EE Tutorial, Web Tier: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/index.html
- Apache Tomcat JSP support: https://tomcat.apache.org/tomcat-10.1-doc/jasper-howto.html

## 4. JPA in Java EE

### What it is

JPA is the Java Persistence API, now Jakarta Persistence. It defines a standard object-relational mapping model for Java. You map Java classes to database tables, query them, persist them, update them, and remove them through an EntityManager.

If you know Spring Data JPA or Hibernate, you already know many JPA concepts: entities, relationships, lazy loading, transactions, persistence context, dirty checking, JPQL, criteria queries, and entity lifecycle.

### Why it matters for monoliths

Many Java EE monoliths use JPA for database access. Some older ones use direct JDBC. Some have mixed persistence layers.

The key difference from Spring Boot is not JPA itself. The key difference is how the EntityManager is created, injected, scoped, and connected to transactions.

In Java EE, the application server may provide a container-managed EntityManager. That EntityManager is bound to a persistence unit and participates in container-managed transactions.

### Spring Boot comparison

Spring Boot often uses Spring Data repositories, Hibernate auto-configuration, application properties, and a Spring transaction manager.

Java EE often uses persistence.xml, JNDI data sources, container-managed EntityManager injection, and JTA transactions.

Spring Boot makes repository creation feel central. Java EE often makes the EntityManager itself more visible.

### What to learn

Learn EntityManager. Learn persistence context. Learn transaction-scoped persistence. Learn JTA versus resource-local persistence units. Learn persistence.xml. Learn how the data source is referenced. Learn lazy loading and transaction boundaries.

### What to inspect in a monolith

Look for persistence.xml. Look for entity classes. Look for named queries. Look for direct EntityManager usage. Look for DAOs. Look for whether the app uses JPA, JDBC, or both. Look for whether the persistence unit says JTA or resource-local.

### Common bugs

Lazy loading fails outside a transaction or persistence context.

The wrong persistence unit is used.

The JNDI data source name does not match the server configuration.

Transactions are missing, so writes fail or do not commit.

Entity changes are not flushed when expected.

The benchmark database schema does not match entity mappings.

### Resources

- Jakarta Persistence specification: https://jakarta.ee/specifications/persistence/
- Jakarta EE Tutorial, Persistence: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/persist/index.html
- Hibernate ORM documentation: https://docs.jboss.org/hibernate/orm/
- Spring Data JPA reference: https://docs.spring.io/spring-data/jpa/reference/

## 5. Logging and Runtime Diagnostics

### What it is

Logging and diagnostics are the practices of understanding what the application and server are doing at runtime. In Java EE monoliths, this includes both application logs and application server logs.

### Why it matters for monoliths

A Java EE deployment can fail before your application logic ever runs. The failure may be in classloading, descriptor parsing, resource binding, JNDI lookup, data source connection, security realm configuration, EJB initialization, transaction manager setup, or JMS resource creation.

Spring Boot developers often expect errors in application logs. In Java EE, you must also read server logs carefully. Sometimes the application deploys partially. Sometimes one module inside an EAR fails while another starts. Sometimes the server masks the root cause behind a deployment exception.

### Spring Boot comparison

Spring Boot centralizes much of the startup story in the application process. Java EE splits the story between the deployed application and the server runtime.

In Spring Boot, “application failed to start” often points to a bean creation or auto-configuration error.

In Java EE, “deployment failed” may mean a descriptor is invalid, a JNDI resource is missing, a data source cannot connect, an EJB cannot be initialized, or a class cannot be resolved by the deployment module.

### What to learn

Learn where server logs live. Learn how deployment messages are structured. Learn how to identify the first cause, not the last wrapper exception. Learn how to increase logging categories. Learn how to distinguish application exceptions from server configuration exceptions.

### What to inspect in a monolith

Check application logs. Check server logs. Check deployment logs. Check database logs when needed. Check server admin console. Check startup order. Check whether modules inside an EAR are all deployed.

### Common bugs

The top-level exception hides the real root cause.

The app logs nothing because deployment failed before app initialization.

The application server uses a different logging framework or bridge than expected.

Logs go to server-specific files, not stdout.

Benchmark scripts assume a log location that differs from your server setup.

### Resources

- Open Liberty logging and trace: https://openliberty.io/docs/latest/log-trace-configuration.html
- WildFly logging subsystem: https://docs.wildfly.org/
- Payara documentation: https://docs.payara.fish/
- Spring Boot logging reference: https://docs.spring.io/spring-boot/reference/features/logging.html

---

# Part 2: Similar Concepts, Different Configuration

This group contains ideas you likely understand conceptually from Spring Boot, but Java EE configures them differently. The main shift is that XML descriptors and server-managed resources become more important.

## 6. web.xml Configuration

### What it is

web.xml is the standard deployment descriptor for a Java web application. It lives inside the web application structure and tells the servlet container how to configure the web module.

It can define servlets, servlet mappings, filters, filter mappings, listeners, session settings, error pages, welcome pages, MIME mappings, context parameters, and security constraints.

### Why it matters for monoliths

Old Java EE monoliths often rely heavily on web.xml. If you skip it, you may miss the real routing table of the application.

Modern Java often uses annotations and conventions. Older Java EE apps use descriptors because annotations were not always available or were not the dominant style.

web.xml is often the first file to read when tracing an HTTP path.

### Spring Boot comparison

In Spring Boot, equivalent configuration may be spread across annotations, Java configuration classes, application properties, and auto-configuration.

In Java EE, web.xml may directly define what handles each URL and which filters apply.

Spring Boot says: “the framework discovers and wires components.”

Java EE legacy apps often say: “the descriptor declares components and wiring.”

### What to learn

Learn servlet declarations. Learn URL patterns. Learn filter ordering. Learn context parameters. Learn session timeout. Learn welcome files. Learn error pages. Learn security constraints.

### What to inspect in a monolith

Open web.xml early. Identify all servlet mappings. Identify filters that apply to all paths. Identify listeners. Identify security constraints. Identify welcome files. Identify context parameters used elsewhere.

### Common bugs

The URL you are testing is mapped differently than expected.

Two mappings overlap and one wins due to mapping rules.

A filter applies globally and changes behavior.

A context parameter differs between environments.

Security constraints block a path before application code runs.

### Resources

- Jakarta Servlet specification: https://jakarta.ee/specifications/servlet/
- Jakarta EE Tutorial, Web Applications: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/web/index.html
- Tomcat deployment descriptor reference: https://tomcat.apache.org/tomcat-10.1-doc/servletapi/
- Open Liberty web application docs: https://openliberty.io/docs/latest/deploying-applications.html

## 7. persistence.xml

### What it is

persistence.xml defines JPA persistence units. A persistence unit describes how a group of entities connects to a database and how persistence should behave.

It can define the persistence provider, transaction type, JTA data source, non-JTA data source, entity classes, mapping files, and provider-specific properties.

### Why it matters for monoliths

In Spring Boot, much JPA configuration lives in application.properties or application.yaml. In Java EE, persistence.xml is often the central file.

If a Java EE app cannot find a persistence unit, cannot find a data source, or uses the wrong transaction type, persistence.xml is usually involved.

### Spring Boot comparison

Spring Boot auto-configures an EntityManagerFactory based on dependencies and configuration. Java EE usually expects persistence.xml to describe the persistence unit. The application server then wires the persistence unit to server resources and JTA.

### What to learn

Learn persistence unit names. Learn JTA versus resource-local transaction type. Learn jta-data-source. Learn provider properties. Learn entity scanning behavior. Learn how the EntityManager refers to the persistence unit.

### What to inspect in a monolith

Open persistence.xml. Identify the persistence unit name. Identify whether it uses JTA. Identify the data source name. Identify provider-specific settings. Identify whether entities are listed explicitly or discovered.

### Common bugs

The persistence unit name in the code does not match persistence.xml.

The JNDI data source name does not exist on the server.

The app expects JTA but is configured resource-local, or the reverse.

Hibernate or EclipseLink provider properties are wrong for the server.

An entity is not discovered because module boundaries or scanning behavior differ.

### Resources

- Jakarta Persistence specification: https://jakarta.ee/specifications/persistence/
- Jakarta EE Tutorial, Persistence Units: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/persist/index.html
- Hibernate persistence unit documentation: https://docs.jboss.org/hibernate/orm/
- EclipseLink documentation: https://www.eclipse.org/eclipselink/documentation/

## 8. Server-Managed DataSources

### What it is

A DataSource represents a configured database connection pool. In Java EE, the application server often owns the DataSource. The application refers to it by a logical name, usually through JNDI.

The server configuration contains the actual JDBC driver, database URL, credentials, pool settings, timeout settings, validation query, transaction integration, and sometimes security credentials.

### Why it matters for monoliths

Database configuration may not be in the application repository. It may be in the application server. If the app fails to connect to the database, changing application code may not help. You may need to configure the server.

This is a major shift from Spring Boot, where database config is commonly inside application.yaml, environment variables, or config server.

### Spring Boot comparison

Spring Boot commonly builds the DataSource from application config and dependencies.

Java EE commonly says: “the server has a DataSource named X; the application asks for X.”

This makes deployment more environment-dependent. The same application artifact can be deployed to different environments with different server-side DataSources.

### What to learn

Learn JNDI names for data sources. Learn connection pool configuration. Learn JDBC driver installation in the server. Learn test connection behavior. Learn transaction-aware data sources. Learn how the persistence unit references the DataSource.

### What to inspect in a monolith

Find the JNDI data source name. Check persistence.xml. Check server config. Check server admin console. Check benchmark scripts. Check whether the database schema must be created manually.

### Common bugs

The DataSource name differs between application and server.

The JDBC driver is missing from the server.

The server uses a stale database URL.

The pool is exhausted during load tests.

Connection validation is disabled and stale connections survive.

JTA integration is missing for a transaction-managed app.

### Resources

- Open Liberty DataSource configuration: https://openliberty.io/docs/latest/reference/config/dataSource.html
- WildFly data source subsystem docs: https://docs.wildfly.org/
- Payara JDBC connection pools: https://docs.payara.fish/
- Jakarta Persistence specification: https://jakarta.ee/specifications/persistence/

## 9. Java EE Security Model

### What it is

Java EE security can be container-managed. The application declares roles and access rules. The application server authenticates users and maps users or groups to roles.

Security can be configured through web.xml, annotations, server-specific descriptors, and server security realms.

### Why it matters for monoliths

In a Spring Boot app, security logic often lives in Spring Security configuration. In Java EE, some security behavior may live outside the application in server configuration.

This means an endpoint may be blocked or allowed because of server-level role mapping, not because of application code.

### Spring Boot comparison

Spring Security is application-framework-centric. Java EE security is platform/container-centric.

Spring Security usually defines filters and authentication providers inside the app.

Java EE may define a realm in the server, declare roles in the app, and bind users or groups to those roles in vendor-specific configuration.

### What to learn

Learn authentication mechanisms. Learn security roles. Learn role mapping. Learn declarative URL constraints. Learn method-level security. Learn programmatic checks. Learn server realms.

### What to inspect in a monolith

Check web.xml security constraints. Check EJB security annotations or descriptors. Check vendor-specific role binding files. Check server security realm configuration. Check whether benchmark workloads bypass authentication or require seeded users.

### Common bugs

User authenticates but has no mapped role.

A security constraint blocks static resources.

The same role name exists in the app but is not mapped in the server.

Authentication works locally but not in another server profile.

A benchmark driver fails because login/session handling differs.

### Resources

- Jakarta Security specification: https://jakarta.ee/specifications/security/
- Jakarta Authorization specification: https://jakarta.ee/specifications/authorization/
- Open Liberty security docs: https://openliberty.io/docs/latest/security.html
- WildFly security documentation: https://docs.wildfly.org/
- Spring Security reference, for comparison: https://docs.spring.io/spring-security/reference/

## 10. JMS Queues and Topics

### What it is

JMS means Java Message Service, now Jakarta Messaging. It is the standard Java API for messaging. Applications use queues and topics to send and receive messages asynchronously.

A queue is usually point-to-point: one message is consumed by one consumer.

A topic is publish-subscribe: a message can be delivered to multiple subscribers.

### Why it matters for monoliths

Enterprise monoliths often use messaging for asynchronous work, order processing, notifications, audit events, integration with external systems, or benchmark transaction paths.

DayTrader-style systems may include messaging paths because enterprise benchmarks often test database transactions, messaging, and container behavior together.

### Spring Boot comparison

In Spring Boot you may use Spring JMS, RabbitMQ, Kafka, or cloud messaging libraries. In Java EE, JMS resources are often configured in the application server. The app uses connection factories and destinations provided by the server.

### What to learn

Learn queues, topics, connection factories, producers, consumers, durable subscriptions, acknowledgement, redelivery, dead-letter handling, and transactional messaging.

Learn message-driven beans because they are the classic Java EE way to consume JMS messages.

### What to inspect in a monolith

Look for JMS resource names. Look for message-driven beans. Look for queue or topic declarations. Check server messaging configuration. Check whether transactions span database writes and message sends.

### Common bugs

Queue name mismatch.

Connection factory missing.

Message listener not deployed.

Messages redeliver repeatedly because processing fails.

Database transaction commits but message transaction rolls back, or the reverse.

Load tests overload the message broker or connection pool.

### Resources

- Jakarta Messaging specification: https://jakarta.ee/specifications/messaging/
- Jakarta EE Tutorial, Messaging: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/messaging/index.html
- Open Liberty messaging docs: https://openliberty.io/docs/latest/messaging.html
- WildFly messaging documentation: https://docs.wildfly.org/

---

# Part 3: Java EE Container Concepts

This is where Java EE starts to feel less like Spring Boot. The term “container” here does not mean Docker. It means the managed runtime inside the application server that executes your application components and provides enterprise services.

## 11. Application Server Mindset

### What it is

An application server is not just a web server. It is a managed runtime for enterprise Java applications. It provides servlet execution, EJB management, dependency injection, transactions, persistence integration, security, messaging, naming, resource pooling, and deployment services.

Examples include WebSphere, WebLogic, WildFly, GlassFish, Payara, and Open Liberty.

### Why it matters for monoliths

The application server may be part of the application architecture. It is not just infrastructure. It can define how the app starts, how resources are provided, how transactions behave, how classes are loaded, and how security is enforced.

In older monoliths, the application and the server are often tightly coupled.

### Spring Boot comparison

Spring Boot made many applications easier to run by packaging a lot of runtime behavior inside the application.

Java EE says: “deploy the app to a compliant server.”

That server can be configured independently of the app. This has advantages and disadvantages.

The advantage: the same app artifact can be deployed with different resources in different environments.

The disadvantage: understanding the app requires understanding server configuration.

### What to learn

Learn what your target application server provides. Learn its directory structure. Learn how deployments work. Learn where logs live. Learn how resources are configured. Learn how server profiles are defined. Learn how to deploy and undeploy applications.

### What to inspect in a monolith

Identify the expected server. Identify expected Java version. Identify Java EE or Jakarta EE version. Identify server-specific files. Identify scripts that install resources. Identify Dockerfiles or benchmark automation.

### Common bugs

The app expects one server but is deployed to another.

The server supports a different Java EE version than the application expects.

Server resources are missing.

Classloading differs between servers.

Vendor-specific descriptors are ignored by the wrong server.

### Resources

- Jakarta EE platform specification: https://jakarta.ee/specifications/platform/
- Open Liberty Jakarta EE overview: https://openliberty.io/docs/latest/jakarta-ee.html
- WildFly documentation: https://docs.wildfly.org/
- Payara documentation: https://docs.payara.fish/

## 12. Container-Managed Lifecycle

### What it is

Container-managed lifecycle means the application server creates, initializes, injects, pools, activates, passivates, and destroys components.

Your code does not fully own object creation. The container does.

This applies to servlets, EJBs, CDI beans, message-driven beans, and other managed components.

### Why it matters for monoliths

If you manually instantiate a class that expects container injection, lifecycle callbacks, transactions, or security, it may not work. The object must be created by the container to receive container services.

This is similar to Spring beans: if you create a Spring-managed service manually, dependencies and proxies may be missing. Java EE has the same idea, but the responsible container may be the web container, EJB container, CDI container, or persistence provider integrated with the server.

### Spring Boot comparison

In Spring Boot, the Spring ApplicationContext manages beans.

In Java EE, the application server manages components through multiple containers. The web container manages servlets. The EJB container manages EJBs. The CDI container manages CDI beans. The persistence provider manages entity state in cooperation with transactions.

### What to learn

Learn component lifecycle callbacks. Learn managed versus unmanaged objects. Learn injection timing. Learn pooling. Learn stateful activation/passivation at a conceptual level. Learn why direct construction can bypass container behavior.

### What to inspect in a monolith

Find managed components. Identify whether dependencies are injected by the container. Identify lifecycle callback methods. Check whether utility classes are manually created. Check whether business services are EJBs or plain objects.

### Common bugs

An object is constructed manually and injection is null.

A lifecycle callback depends on a resource that is not available yet.

A pooled component stores unsafe mutable state.

A stateful component is passivated and cannot serialize its state.

A singleton component has concurrency assumptions.

### Resources

- Jakarta EE Tutorial: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/index.html
- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta Contexts and Dependency Injection specification: https://jakarta.ee/specifications/cdi/
- IBM Liberty EJB docs: https://www.ibm.com/docs/en/was-liberty/base?topic=environment-developing-ejb-applications-liberty

## 13. Container-Managed EntityManager

### What it is

A container-managed EntityManager is provided by the Java EE container. It is associated with a persistence unit and often participates automatically in the current JTA transaction.

The application does not create it manually. The container injects it or otherwise provides it.

### Why it matters for monoliths

A lot of Java EE persistence behavior depends on this concept. The EntityManager may be scoped to a transaction. When an EJB method starts a transaction, the EntityManager joins it automatically.

This is where Spring Boot developers can get confused. In Spring Boot, the EntityManager is also often managed, but Spring is the manager. In Java EE, the application server and JPA provider cooperate under the Java EE model.

### Spring Boot comparison

Spring Boot often exposes repositories and hides the EntityManager. Java EE code may use the EntityManager directly.

Spring transaction management and Java EE JTA transaction management have similar goals but different control points.

### What to learn

Learn transaction-scoped persistence contexts. Learn extended persistence contexts at a high level. Learn when the EntityManager is valid. Learn what it means for an entity to be managed or detached. Learn how the EntityManager joins a transaction.

### What to inspect in a monolith

Find EntityManager usage. Find persistence context injection. Check the persistence unit name. Check transaction boundaries around methods that use persistence. Check whether the app uses extended persistence context, which is more common with stateful beans.

### Common bugs

EntityManager is used outside an active transaction for writes.

Entities become detached and updates are not persisted.

Lazy loading happens after the persistence context closes.

The wrong persistence unit is injected.

Extended persistence context keeps too much state.

### Resources

- Jakarta Persistence specification: https://jakarta.ee/specifications/persistence/
- Jakarta EE Tutorial, Persistence: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/persist/index.html
- Hibernate ORM documentation: https://docs.jboss.org/hibernate/orm/

## 14. Container-Managed Transactions

### What it is

Container-managed transactions mean the application server controls transaction boundaries for managed components, especially EJBs.

A method can run inside a transaction without manually beginning or committing it. The container starts, joins, commits, suspends, or rolls back transactions depending on configuration and method attributes.

### Why it matters for monoliths

This is central to Java EE. Many business methods rely on the server to manage transactions. If you do not know where transactions begin and end, you cannot safely modify persistence, messaging, or service calls.

In a Java EE monolith, a method call may be more than a normal Java call. If it crosses an EJB boundary, the container may apply transactions, security, pooling, interceptors, and remoting semantics.

### Spring Boot comparison

Spring Boot developers know transactional services. The Java EE equivalent is usually EJB transaction management with JTA.

The Spring Boot mental model is: a proxied Spring bean method gets transactional behavior.

The Java EE mental model is: a container-managed component method gets transactional behavior from the EJB container or transaction integration.

Both have proxy/boundary issues. Self-invocation can matter in Spring. In Java EE, calling a method internally may bypass container interceptors depending on structure.

### What to learn

Learn transaction attributes conceptually: required, requires new, mandatory, supports, not supported, never.

Learn rollback rules. Learn checked versus unchecked exception behavior. Learn database and JMS transaction participation. Learn where the transaction boundary begins.

### What to inspect in a monolith

Find transactional annotations or descriptors. Identify which service methods are EJB methods. Identify whether database and messaging operations occur inside the same transaction. Identify exception handling that may accidentally prevent rollback.

### Common bugs

A method catches an exception and prevents rollback.

A method assumes a transaction exists but does not have one.

A nested call starts a new transaction unexpectedly.

A transaction stays open too long under load.

A message is sent but database commit fails, or vice versa.

### Resources

- Jakarta Transactions specification: https://jakarta.ee/specifications/transactions/
- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta EE Tutorial, Transactions: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/supporttechs/transactions.html
- Open Liberty transaction docs: https://openliberty.io/docs/latest/transaction-manager.html

## 15. JTA Transaction Model

### What it is

JTA means Java Transaction API, now Jakarta Transactions. It is the standard transaction model used by Java EE application servers.

JTA can coordinate transactions across multiple transactional resources, such as a relational database and a JMS provider. This is why it matters in enterprise applications.

### Why it matters for monoliths

In benchmark monoliths, transaction behavior is often part of what is being measured. DayTrader-style applications are especially transaction-heavy.

If a request updates a database and sends a message, JTA may coordinate both. If the transaction rolls back, both resource operations may roll back.

### Spring Boot comparison

Spring Boot can use local transactions or JTA. Many Spring Boot apps use a single database transaction manager. Java EE apps are more likely to assume a server-managed JTA transaction manager.

The conceptual gap is distributed coordination. You need to know when the server is doing more than a simple database commit.

### What to learn

Learn local transaction versus global transaction. Learn transaction manager. Learn resource manager. Learn XA at a high level. Learn two-phase commit at a high level. Learn transaction propagation. Learn rollback-only state.

### What to inspect in a monolith

Check whether the app uses JTA data sources. Check whether JMS participates in transactions. Check server transaction logs. Check timeout settings. Check whether the benchmark expects XA or non-XA resources.

### Common bugs

Transaction timeout under load.

XA driver not configured correctly.

One resource is JTA-aware and another is not.

Rollback-only state appears after an exception, but code still tries to continue.

Two-phase commit adds overhead that surprises benchmark results.

### Resources

- Jakarta Transactions specification: https://jakarta.ee/specifications/transactions/
- Open Liberty transaction manager docs: https://openliberty.io/docs/latest/transaction-manager.html
- WildFly transaction subsystem docs: https://docs.wildfly.org/

---

# Part 4: Packaging and Deployment

This group is where the application becomes a deployable enterprise artifact. Spring Boot developers often think in executable JARs and containers. Java EE monoliths often think in WARs, EARs, server profiles, deployment descriptors, and server-specific binding files.

## 16. WAR and EAR Packaging

### What it is

A WAR is a Web Application Archive. It packages a web module: servlets, JSPs, web resources, libraries, and web descriptors.

An EAR is an Enterprise Application Archive. It can contain multiple modules, including WAR modules, EJB JAR modules, shared libraries, resource adapter archives, and deployment descriptors.

### Why it matters for monoliths

Large Java EE monoliths often use EAR packaging. The web layer may be in one module. EJB business logic may be in another. Shared model classes may be in a library module.

If you do not understand the packaging, you cannot understand module boundaries, class visibility, deployment order, or configuration.

### Spring Boot comparison

Spring Boot typically packages one executable application artifact. Java EE may package a multi-module enterprise archive deployed into an external server.

Spring Boot asks: “what is inside the fat JAR?”

Java EE asks: “what modules are inside the EAR, and what does the server provide?”

### What to learn

Learn WAR structure. Learn EAR structure. Learn EJB JAR. Learn library placement. Learn application.xml. Learn module dependencies. Learn where descriptors live.

### What to inspect in a monolith

Check Maven or Gradle modules. Check packaging types. Check generated target artifacts. Check whether there is an EAR module. Check application.xml. Check server-specific deployment descriptors.

### Common bugs

A class is visible in one module but not another.

A library is packaged twice.

An EJB module deploys but the web module cannot find it.

The EAR structure expected by the server differs from the build output.

A benchmark script deploys the wrong artifact.

### Resources

- Jakarta EE Tutorial, Packaging: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/overview/index.html
- Jakarta EE platform specification: https://jakarta.ee/specifications/platform/
- IBM Liberty EJB packaging docs: https://www.ibm.com/docs/en/was-liberty/base?topic=environment-developing-ejb-applications-liberty
- Maven WAR plugin: https://maven.apache.org/plugins/maven-war-plugin/
- Maven EAR plugin: https://maven.apache.org/plugins/maven-ear-plugin/

## 17. Deployment Descriptors

### What it is

Deployment descriptors are XML files that describe application components and deployment behavior. Standard descriptors include web.xml, ejb-jar.xml, persistence.xml, and application.xml.

They can define components, mappings, dependencies, persistence units, security, roles, environment entries, resource references, and module structure.

### Why it matters for monoliths

Legacy Java EE applications often rely on descriptors more than annotations. The descriptor may override or supplement annotations.

If behavior seems invisible in code, check descriptors.

### Spring Boot comparison

Spring Boot configuration is usually annotation and property driven. Java EE legacy configuration is often descriptor driven.

### What to learn

Learn the purpose of each standard descriptor. Learn where each descriptor lives. Learn whether it is standard or vendor-specific. Learn whether descriptors override annotations.

### What to inspect in a monolith

Search for XML files under web, META-INF, WEB-INF, and deployment directories. Identify which are standard Java EE descriptors and which are vendor-specific.

### Common bugs

Descriptor references a class that was renamed.

Descriptor URL pattern differs from expected route.

Descriptor role name differs from server role mapping.

Descriptor says one persistence unit name while code expects another.

Descriptor version does not match server support.

### Resources

- Jakarta EE Tutorial: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/index.html
- Jakarta Servlet specification: https://jakarta.ee/specifications/servlet/
- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta Persistence specification: https://jakarta.ee/specifications/persistence/

## 18. Vendor-Specific Descriptors

### What it is

Vendor-specific descriptors are server-specific configuration files. They are not portable Java EE standard files. They tell a particular application server how to bind, tune, secure, or load the application.

Examples include files for WebSphere, WebLogic, JBoss/WildFly, GlassFish/Payara, and Liberty.

They often handle JNDI bindings, role mappings, classloader behavior, context roots, EJB bindings, resource references, and deployment tuning.

### Why it matters for monoliths

A Java EE app may be “standard” in theory but server-specific in practice. Vendor descriptors can be the reason it works on one server and fails on another.

Benchmark monoliths often have variants for different servers. Each variant may include server-specific deployment files.

### Spring Boot comparison

Spring Boot is usually less dependent on a specific application server. Java EE monoliths may encode server assumptions in descriptors.

### What to learn

Learn to identify vendor descriptors. Learn what server they target. Learn whether they are mandatory. Learn how they bind standard resource references to actual server resources.

### What to inspect in a monolith

Look for names containing ibm, weblogic, jboss, glassfish, payara, liberty, sun, was, or deployment-structure. Inspect files under WEB-INF and META-INF. Check benchmark documentation for server-specific deployment steps.

### Common bugs

The descriptor is ignored because the app runs on the wrong server.

A server-specific JNDI binding is missing.

Classloader isolation is configured incorrectly.

Security roles are declared but not bound.

A context root differs from the benchmark URL.

### Resources

- WildFly developer guide: https://docs.wildfly.org/
- Open Liberty deployment docs: https://openliberty.io/docs/latest/deploying-applications.html
- WebLogic deployment descriptor docs: https://docs.oracle.com/en/middleware/
- IBM WebSphere Liberty docs: https://www.ibm.com/docs/en/was-liberty/

## 19. Server Configuration

### What it is

Server configuration defines the runtime environment outside the application artifact. It includes ports, data sources, JDBC drivers, JMS resources, security realms, transaction manager settings, thread pools, classloading behavior, logging, and deployed applications.

### Why it matters for monoliths

In Java EE, running the app correctly often requires reproducing the expected server configuration. The app artifact alone may not be enough.

### Spring Boot comparison

Spring Boot apps often externalize config, but the app still tends to own much of the runtime wiring. Java EE apps often depend on server-level resources that must exist before deployment succeeds.

### What to learn

Learn the configuration model of the target server. For Liberty, learn server.xml. For WildFly, learn standalone.xml or domain configuration. For WebLogic and WebSphere, learn admin console concepts and deployment descriptors.

### What to inspect in a monolith

Check Dockerfiles, scripts, README files, benchmark harness files, server profiles, resource setup scripts, and environment variables. Identify what the app expects the server to provide.

### Common bugs

Wrong server profile.

Missing JDBC driver.

Wrong port.

Wrong context root.

Wrong database credentials.

Missing JMS destination.

Transaction timeout too low.

Thread pool too small for benchmark workload.

### Resources

- Open Liberty server configuration: https://openliberty.io/docs/latest/server-configuration-overview.html
- WildFly documentation: https://docs.wildfly.org/
- Payara administration docs: https://docs.payara.fish/
- IBM WebSphere Liberty docs: https://www.ibm.com/docs/en/was-liberty/

## 20. Running Legacy Benchmark Monoliths

### What it is

Running a legacy benchmark monolith means reproducing the expected combination of application code, build system, Java version, application server version, database, schema, data seed, server config, benchmark driver, and workload.

### Why it matters for monoliths

Benchmark applications are often less forgiving than normal apps. They may be old, pinned to specific versions, or designed to measure particular runtime behavior. If one component differs, results may be invalid or the app may not run.

### Spring Boot comparison

Spring Boot apps are usually easier to run locally. Benchmark Java EE monoliths may require old JDKs, specific server distributions, vendor resource configs, and carefully seeded databases.

### What to learn

Learn to identify the expected stack. Learn to run the build. Learn to deploy to the correct server. Learn to initialize the database. Learn to validate one transaction path before running a load test. Learn to separate app failure from benchmark harness failure.

### What to inspect in a monolith

README files. Build files. Dockerfiles. Deployment scripts. Database scripts. Server config files. Workload driver configuration. Expected URLs. Health or verification endpoints.

### Common bugs

Using the wrong Java version.

Using a Jakarta EE server for a javax-based Java EE app without migration.

Database schema missing.

Benchmark data not seeded.

App deployed but wrong context root used.

Benchmark driver sends requests before app is fully initialized.

### Resources

- Jakarta EE Tutorial: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/index.html
- Open Liberty guides: https://openliberty.io/guides/
- WildFly quickstarts: https://github.com/wildfly/quickstart
- Eclipse Cargo, for deployment automation: https://codehaus-cargo.github.io/cargo/

---

# Part 5: More Java EE-Specific, Less Spring-Like

This group contains concepts that are more characteristic of traditional Java EE. Some have analogies in Spring, but the Java EE versions are more tightly tied to the application server.

## 21. JNDI Resource Lookup

### What it is

JNDI means Java Naming and Directory Interface. It is a naming system used to look up resources by name.

In Java EE, JNDI is used for data sources, EJBs, JMS connection factories, queues, topics, mail sessions, environment entries, and other server-managed resources.

### Why it matters for monoliths

JNDI is one of the main ways an application connects to resources configured in the server. If a resource name is wrong or missing, deployment or runtime lookup fails.

### Spring Boot comparison

Spring Boot usually wires resources through configuration properties, beans, and dependency injection.

Java EE often wires resources through names. The server has a resource named something. The application references that name.

### What to learn

Learn global names, application names, module names, and environment naming context at a conceptual level. Learn resource-ref. Learn how descriptors bind logical names to physical server resources.

### What to inspect in a monolith

Search for JNDI names. Check web.xml, ejb-jar.xml, persistence.xml, and vendor descriptors. Check server resource configuration. Check application server logs for lookup failures.

### Common bugs

Name mismatch.

Resource exists globally but not under the expected application environment name.

Vendor-specific binding missing.

Different servers use different naming conventions.

A resource is available in one module but not another.

### Resources

- Jakarta EE Tutorial, Resources: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/supporttechs/resources.html
- Open Liberty JNDI docs: https://openliberty.io/docs/latest/reference/config/jndiEntry.html
- WildFly naming subsystem docs: https://docs.wildfly.org/

## 22. EJB Basics

### What it is

EJB means Enterprise JavaBeans, now Jakarta Enterprise Beans. EJBs are container-managed business components.

EJBs can provide transaction management, security, pooling, concurrency control, remote access, asynchronous execution, scheduling, and messaging integration.

### Why it matters for monoliths

EJBs are often the business layer in old Java EE monoliths. If you only know Spring services, EJBs are the nearest Java EE equivalent, but they come with stronger server-managed semantics.

### Spring Boot comparison

A stateless EJB may feel like a Spring service. But unlike a plain service, an EJB is managed by the EJB container. Calls to it may trigger transactions, security checks, interceptors, pooling, and remote invocation behavior.

### What to learn

Learn session beans, message-driven beans, local versus remote interfaces, transaction attributes, security annotations, lifecycle callbacks, and container injection.

### What to inspect in a monolith

Search for EJBs, business interfaces, local or remote interfaces, EJB descriptors, and injection points. Identify whether business logic sits in EJBs, servlets, or plain classes.

### Common bugs

Calling an EJB incorrectly bypasses container behavior.

Remote interface serialization fails.

Transaction attributes are misunderstood.

State is stored in a stateless bean.

EJB lookup name is wrong.

### Resources

- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta EE Tutorial, Enterprise Beans: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/ejb/index.html
- IBM Liberty EJB docs: https://www.ibm.com/docs/en/was-liberty/base?topic=environment-developing-ejb-applications-liberty
- Open Liberty Enterprise Beans feature docs: https://openliberty.io/docs/latest/reference/feature/enterpriseBeans.html

## 23. Stateless Session Beans

### What they are

A stateless session bean is an EJB designed for business operations that do not keep conversational state for a specific client between calls.

The container may pool stateless bean instances. Any instance can serve any compatible request.

### Why they matter for monoliths

Stateless session beans are common in Java EE business layers. They often contain transaction boundaries around business operations.

They are usually the easiest EJB type to understand if you know Spring services.

### Spring Boot comparison

A stateless session bean is roughly comparable to a singleton Spring service with transactional and security behavior applied by the container. But the container may pool instances, and the lifecycle model is not identical.

### What to learn

Learn that instance fields should not store request-specific or user-specific state. Learn transaction attributes. Learn local versus remote business interfaces. Learn pooling implications.

### What to inspect in a monolith

Find stateless beans. Identify public business methods. Identify transaction attributes. Identify injected EntityManagers and resources. Identify whether fields are safe.

### Common bugs

Mutable instance fields used as request state.

Transaction boundary assumed at the wrong method.

Bean called internally rather than through container-managed reference.

Remote call overhead ignored in benchmark paths.

### Resources

- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta EE Tutorial, Session Beans: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/ejb/session-beans.html
- IBM Liberty EJB docs: https://www.ibm.com/docs/en/was-liberty/base?topic=environment-developing-ejb-applications-liberty

## 24. Stateful Session Beans

### What they are

A stateful session bean keeps conversational state for a specific client across multiple method calls.

The container associates a bean instance with a client conversation. It may passivate and later activate the bean to conserve resources.

### Why they matter for monoliths

Stateful beans appear in older enterprise applications that model sessions, shopping carts, workflows, or multi-step interactions.

They are less common in modern Spring Boot applications, where state is often stored in databases, caches, tokens, or external session stores.

### Spring Boot comparison

A stateful session bean is not like a normal singleton Spring service. It is closer to a server-managed conversation object.

Spring has scopes, including session scope, but stateful EJBs have their own lifecycle, passivation, and container semantics.

### What to learn

Learn conversational state. Learn passivation and activation. Learn serialization requirements at a conceptual level. Learn removal. Learn extended persistence contexts because they may appear with stateful beans.

### What to inspect in a monolith

Find stateful beans. Identify what state they store. Identify lifecycle methods. Check whether state is serializable. Check whether the benchmark workload creates many concurrent sessions.

### Common bugs

Stateful bean holds non-serializable resources.

State grows too large under load.

Client conversation is not ended, causing resource retention.

Stateful behavior breaks when load balancing is introduced.

### Resources

- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta EE Tutorial, Stateful Session Beans: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/ejb/session-beans.html
- Open Liberty Enterprise Beans docs: https://openliberty.io/docs/latest/reference/feature/enterpriseBeans.html

## 25. Singleton Beans

### What they are

A singleton session bean has one shared instance per application. The container manages its lifecycle and concurrency.

Singleton beans are often used for shared state, startup initialization, caches, schedulers, or coordination tasks.

### Why they matter for monoliths

Singletons can influence global behavior. A singleton bean may initialize benchmark data, manage caches, or hold application-wide settings.

Because it is shared, concurrency behavior matters.

### Spring Boot comparison

A singleton EJB is closer to a normal singleton Spring bean, but with EJB container lifecycle and concurrency rules.

Spring singleton beans are also shared, but Java EE singleton beans have defined container-managed concurrency options.

### What to learn

Learn startup initialization. Learn concurrency management. Learn read/write locks conceptually. Learn lifecycle callbacks. Learn why mutable shared state is dangerous.

### What to inspect in a monolith

Find singleton beans. Identify startup behavior. Check shared state. Check concurrency settings. Check initialization order.

### Common bugs

Shared mutable state is not protected.

Startup logic depends on unavailable resources.

Cache is not invalidated.

Singleton becomes a bottleneck under load.

### Resources

- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta EE Tutorial, Singleton Session Beans: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/ejb/session-beans.html

## 26. Message-Driven Beans

### What they are

A message-driven bean is an EJB that asynchronously receives messages, usually from JMS queues or topics.

The container manages the listener lifecycle, concurrency, transactions, and message delivery integration.

### Why they matter for monoliths

Message-driven beans are the classic Java EE mechanism for background message processing. If a monolith uses JMS, it may use MDBs as consumers.

### Spring Boot comparison

A message-driven bean is comparable to a Spring message listener method, but managed by the EJB container and connected to server-provided JMS resources.

### What to learn

Learn how MDBs subscribe to destinations. Learn transaction behavior. Learn redelivery. Learn concurrency. Learn poison message behavior. Learn dead-letter queues.

### What to inspect in a monolith

Find message-driven beans. Identify destination names. Check activation configuration. Check JMS resources in server config. Check transaction behavior.

### Common bugs

Destination does not exist.

MDB deploys but does not receive messages.

Message processing fails and redelivers endlessly.

Concurrency causes database contention.

Transaction rollback causes message redelivery loops.

### Resources

- Jakarta Enterprise Beans specification: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta Messaging specification: https://jakarta.ee/specifications/messaging/
- Jakarta EE Tutorial, Message-Driven Beans: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/ejb/message-driven-beans.html

---

# Part 6: Hardest / Most Legacy-Painful

This group is where time disappears. The concepts are not always hard in theory, but they are painful in practice because they are environment-specific, version-specific, or failure-prone.

## 27. Application Server Classloading

### What it is

Classloading decides which class version is loaded at runtime and from where.

In Java EE, the application server has its own libraries and modules. Your application has its own libraries. EAR modules may have their own libraries. Servers may use parent-first, parent-last, module isolation, or explicit module dependency rules.

### Why it matters for monoliths

Classloading errors are common in legacy Java EE. The application might package a library version that conflicts with the server’s built-in version. Or the app may assume a class is available from the server but it is not.

### Spring Boot comparison

Spring Boot fat JARs have dependency issues too, but the application usually controls most library versions. Java EE servers provide many APIs and sometimes implementations. That creates more ambiguity.

### What to learn

Learn server-provided APIs. Learn application-packaged libraries. Learn module isolation. Learn parent-first versus parent-last. Learn shared libraries. Learn how your target server resolves classes.

### What to inspect in a monolith

Inspect packaged JARs. Inspect server modules. Check whether Java EE API JARs are wrongly bundled. Check vendor-specific classloading descriptors. Check NoClassDefFoundError, ClassNotFoundException, LinkageError, and ClassCastException carefully.

### Common bugs

Two versions of the same library exist.

The app bundles an API that should be provided by the server.

The server provides an older implementation than the app expects.

A class is loaded twice by different classloaders, causing ClassCastException.

EAR submodules cannot see each other.

### Resources

- WildFly classloading documentation: https://docs.wildfly.org/
- Open Liberty class loader configuration: https://openliberty.io/docs/latest/class-loader-library-config.html
- IBM WebSphere class loading docs: https://www.ibm.com/docs/en/was-liberty/
- Maven dependency plugin: https://maven.apache.org/plugins/maven-dependency-plugin/

## 28. Dependency Conflicts

### What it is

Dependency conflicts happen when the application, server, or modules require incompatible versions of libraries.

In Java EE, dependency conflicts are tightly connected to classloading.

### Why it matters for monoliths

Legacy benchmark apps often use old dependencies. Modern build tools may resolve newer versions accidentally. Newer servers may include different implementations. Java version changes may break old libraries.

### Spring Boot comparison

Spring Boot gives dependency management through BOMs and starters. Java EE monoliths may rely on older Maven configurations, manually included JARs, or server-provided libraries.

### What to learn

Learn Maven dependency trees. Learn transitive dependencies. Learn provided scope. Learn optional dependencies. Learn exclusions. Learn server API boundaries. Learn why javax or jakarta API JARs should often be provided by the server in traditional deployments.

### What to inspect in a monolith

Run dependency tree. Check scopes. Check packaged artifact contents. Check server-provided libraries. Check for duplicate logging frameworks, persistence providers, XML parsers, JSON libraries, and Java EE API JARs.

### Common bugs

Compile succeeds but deployment fails.

Runtime uses a different version than build-time.

A dependency should be provided but is packaged.

A dependency should be packaged but is missing.

Logging conflicts hide useful errors.

### Resources

- Maven dependency mechanism: https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html
- Maven dependency plugin: https://maven.apache.org/plugins/maven-dependency-plugin/
- WildFly classloading documentation: https://docs.wildfly.org/
- Open Liberty class loader docs: https://openliberty.io/docs/latest/class-loader-library-config.html

## 29. Java EE Version Differences

### What it is

Java EE changed significantly across versions. Older applications may use J2EE 1.4 or Java EE 5 style. Newer ones may use Java EE 6, 7, or 8. Jakarta EE continues the evolution after the move to the Eclipse Foundation.

The differences affect APIs, annotations, EJB style, CDI availability, JPA versions, servlet versions, server support, and deployment behavior.

### Why it matters for monoliths

A monolith built for an old Java EE version may not run unchanged on a newer Jakarta EE server. Even if it compiles, behavior may differ.

### Spring Boot comparison

Spring Boot version upgrades can also be painful, but Java EE version differences are often tied to application server compatibility and package names.

### What to learn

Learn the approximate eras:

J2EE 1.4 era: heavier XML, older EJB 2.x style, more boilerplate.

Java EE 5 era: annotations and EJB 3 introduced a simpler model.

Java EE 6 era: CDI became important, more modern platform.

Java EE 7 and 8 era: more mature APIs, improved concurrency, batch, JSON, WebSocket, JAX-RS improvements.

Jakarta EE 8: essentially Java EE 8 under Eclipse Foundation branding, still mostly javax package names.

Jakarta EE 9 and later: namespace change from javax to jakarta.

### What to inspect in a monolith

Check imports. Check descriptor versions. Check build dependencies. Check target server. Check Java version. Check EJB style. Check whether CDI is used. Check whether the app uses javax or jakarta packages.

### Common bugs

Running old javax app on jakarta-only runtime.

Using app server that supports the wrong platform version.

Descriptor schema mismatch.

Old EJB 2.x patterns not supported as expected.

Java version too new for old libraries or too old for server.

### Resources

- Jakarta EE specifications: https://jakarta.ee/specifications/
- Jakarta EE release plan and platform specs: https://jakarta.ee/specifications/platform/
- Eclipse Jakarta EE: https://jakarta.ee/
- Open Liberty supported Java EE and Jakarta EE platforms: https://openliberty.io/docs/latest/reference/platform/JakartaEE.html

## 30. javax vs jakarta

### What it is

The Java EE APIs historically used package names beginning with javax. After Java EE moved to the Eclipse Foundation and became Jakarta EE, newer Jakarta EE versions changed many package names from javax to jakarta.

This is not just naming trivia. It affects source code, dependencies, application servers, libraries, and binary compatibility.

### Why it matters for monoliths

Most older benchmark monoliths use javax packages. Modern Jakarta EE 9+ servers expect jakarta packages for many APIs.

A javax application usually cannot simply run on a jakarta-only server without transformation, migration, or compatibility support.

### Spring Boot comparison

Spring Boot 2.x was largely aligned with javax-era APIs. Spring Boot 3.x moved to Jakarta EE 9+ baseline and uses jakarta packages.

So if you know Spring Boot 3, you may already have seen the migration pain. If your monolith is older, it may still be javax-based.

### What to learn

Learn which ecosystem your app belongs to. Learn whether the target server is Java EE, Jakarta EE 8, or Jakarta EE 9+. Learn migration tools conceptually. Learn that dependencies must align with the namespace.

### What to inspect in a monolith

Search imports for javax and jakarta. Check Maven dependencies. Check app server version. Check Spring version if the app mixes Spring with Java EE. Check whether bytecode transformation is part of the build or deployment.

### Common bugs

Compiling javax code against jakarta APIs.

Deploying javax WAR to jakarta-only server.

Mixing javax persistence annotations with jakarta persistence provider expectations.

Using Spring Boot 3 dependencies with old javax application code.

Transforming app classes but not third-party libraries.

### Resources

- Jakarta EE namespace change FAQ: https://jakarta.ee/about/faq/
- Jakarta EE specifications: https://jakarta.ee/specifications/
- Spring Boot 3 migration guide: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide
- Eclipse Transformer project: https://projects.eclipse.org/projects/technology.transformer

---

# Practical Study Plan

## Phase 1: Map Requests

Learn servlet flow, filters, listeners, JSP, and web.xml.

Goal: Given a URL, you can find what code handles it and what runs before and after it.

Practice by taking one endpoint and tracing it from URL to servlet/filter/JSP/service/persistence.

## Phase 2: Map Persistence

Learn JPA in Java EE, persistence.xml, EntityManager, and server-managed DataSources.

Goal: Given a database operation, you can identify the persistence unit, data source, transaction boundary, and database schema.

Practice by tracing one read and one write path.

## Phase 3: Map Container Behavior

Learn application server mindset, container-managed lifecycle, container-managed transactions, and JTA.

Goal: Given a business method, you can explain what the server does around it.

Practice by identifying which calls are plain Java calls and which calls cross managed component boundaries.

## Phase 4: Map Deployment

Learn WAR, EAR, deployment descriptors, vendor descriptors, and server configuration.

Goal: Given a built artifact, you can explain where it is deployed, what modules it contains, and what resources it expects.

Practice by opening the built WAR or EAR and matching it to server configuration.

## Phase 5: Map Enterprise-Specific Features

Learn JNDI, EJBs, stateless/stateful/singleton beans, and message-driven beans.

Goal: Given an injected resource or EJB call, you can explain where it comes from and what container behavior applies.

Practice by finding all EJBs and classifying them.

## Phase 6: Fight Legacy Problems

Learn classloading, dependency conflicts, Java EE version differences, and javax versus jakarta.

Goal: Given a deployment failure, you can separate app bug, dependency bug, server resource bug, and platform mismatch.

Practice by reading the first root cause in server logs and mapping it to one of those categories.

---

# Benchmark Monolith Reading Checklist

Use this checklist when opening one of the benchmark monoliths.

## Initial Identification

What Java version does it expect?

What Java EE or Jakarta EE version does it expect?

Which application server does it target?

Does it use javax or jakarta imports?

Is it built with Maven, Gradle, Ant, or custom scripts?

Is it packaged as JAR, WAR, EAR, or multiple artifacts?

## Web Layer

Where is web.xml?

What are the servlet mappings?

What filters apply globally?

What listeners run at startup?

Are JSPs used?

Are URLs generated dynamically?

Does the benchmark driver hit servlet paths, REST paths, or rendered pages?

## Business Layer

Where is business logic located?

Are there EJBs?

Are there plain Java services?

Are there DAOs?

Are business methods local, remote, or both?

Are there stateful components?

## Persistence Layer

Does it use JPA, JDBC, or both?

Where is persistence.xml?

What is the persistence unit name?

What DataSource does it reference?

Where is the schema created?

Where is seed data loaded?

Which operations are read-only and which are transactional writes?

## Transactions

Where do transactions begin?

Are transactions container-managed?

Are there JTA resources?

Does JMS participate in the same transaction as the database?

What exceptions trigger rollback?

Are transaction timeouts configured?

## Messaging

Does the app use JMS?

Which queues or topics exist?

Which connection factory is used?

Are message-driven beans deployed?

What happens on redelivery?

## Security

Is container-managed security used?

Are roles declared?

Where are roles mapped?

Does the benchmark path require login?

Does the app use session-based authentication?

## Deployment

What server resources must exist before deployment?

Which vendor descriptors are present?

What context root is expected?

What modules are inside the EAR?

Do all modules deploy successfully?

## Runtime

Where are logs?

What is the first deployment error, not the last wrapper error?

Are database connections successful?

Are pools sized for the workload?

Are there classloading warnings?

Are there transaction timeout warnings?

## Version and Migration

Is the app javax-based?

Is the server javax-compatible or jakarta-only?

Are dependencies old?

Are Java EE API JARs packaged when they should be provided?

Does the app rely on deprecated EJB or descriptor style?

---

# Resource Index

## Official Jakarta EE

- Jakarta EE homepage: https://jakarta.ee/
- Jakarta EE Tutorial: https://jakarta.ee/learn/docs/jakartaee-tutorial/current/index.html
- Jakarta EE specifications: https://jakarta.ee/specifications/
- Jakarta EE platform specification: https://jakarta.ee/specifications/platform/
- Jakarta Servlet: https://jakarta.ee/specifications/servlet/
- Jakarta Server Pages: https://jakarta.ee/specifications/pages/
- Jakarta Persistence: https://jakarta.ee/specifications/persistence/
- Jakarta Transactions: https://jakarta.ee/specifications/transactions/
- Jakarta Messaging: https://jakarta.ee/specifications/messaging/
- Jakarta Enterprise Beans: https://jakarta.ee/specifications/enterprise-beans/
- Jakarta Security: https://jakarta.ee/specifications/security/
- Jakarta Contexts and Dependency Injection: https://jakarta.ee/specifications/cdi/

## Application Servers

- Open Liberty documentation: https://openliberty.io/docs/latest/
- Open Liberty Jakarta EE overview: https://openliberty.io/docs/latest/jakarta-ee.html
- Open Liberty guides: https://openliberty.io/guides/
- WildFly documentation: https://docs.wildfly.org/
- WildFly quickstarts: https://github.com/wildfly/quickstart
- Payara documentation: https://docs.payara.fish/
- IBM WebSphere Liberty documentation: https://www.ibm.com/docs/en/was-liberty/
- Oracle WebLogic documentation: https://docs.oracle.com/en/middleware/

## Spring Boot Comparison Resources

- Spring Boot reference: https://docs.spring.io/spring-boot/
- Spring Framework reference: https://docs.spring.io/spring-framework/reference/
- Spring Security reference: https://docs.spring.io/spring-security/reference/
- Spring Data JPA reference: https://docs.spring.io/spring-data/jpa/reference/
- Spring Boot 3 migration guide: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide

## Persistence and Build Tools

- Hibernate ORM documentation: https://docs.jboss.org/hibernate/orm/
- EclipseLink documentation: https://www.eclipse.org/eclipselink/documentation/
- Maven dependency mechanism: https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html
- Maven WAR plugin: https://maven.apache.org/plugins/maven-war-plugin/
- Maven EAR plugin: https://maven.apache.org/plugins/maven-ear-plugin/
- Maven dependency plugin: https://maven.apache.org/plugins/maven-dependency-plugin/

## Final Compression

For your specific learning gap, remember this stack:

Java is the language.

Spring Boot is the framework you already know.

Java EE is the server-managed enterprise platform you need to understand.

The practical gap is not syntax. It is runtime ownership.

Spring Boot asks you to understand the application context.

Java EE asks you to understand the application server container.

Spring Boot problems often center around beans, auto-configuration, starters, properties, and embedded server behavior.

Java EE monolith problems often center around deployment descriptors, server resources, JNDI names, DataSources, EJBs, JTA transactions, classloading, and server-specific configuration.

If you master those differences, the benchmark monoliths stop looking mysterious. They become old but understandable server-managed Java systems.
