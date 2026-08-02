# Dev - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

## Contents

- `Dev/architecture/` - architecture patterns, spec format, and monolith-to-microservice decomposition research
- `Dev/frontend/` - React, React Native, Skia, Redux, micro-frontends
- `Dev/infra/` - CI, container platforms, log/metric pipelines, certificates and application security
- `Dev/languages/` - language reference notes: Kotlin, Java, JavaScript, Python
- `Dev/practices/` - general engineering practice, independent of any language or framework
- `Dev/LLM/` - **not notes.** A Python/notebook sandbox (`src/`, `*.ipynb`, `requirements.txt`). Never indexed; its math notes moved to `Mathematik/`.

## Dev/architecture/

- Place here: system and software architecture — architectural patterns, deployment topologies, specification formats, and monolith-to-microservice decomposition methods and paper work.
- `Dev/architecture/Monolithic decomposition/` - monolith-to-microservice decomposition research and methods — see `Dev/architecture/Monolithic decomposition/index.md` for its 17 notes
- `Dev/architecture/Mix Architecture patterns - Infra-Deployment strategies.md` - mixing architecture patterns, and the infrastructure/deployment strategies that go with each
- `Dev/architecture/Spec format.md` - a fill-in template for writing an unambiguous feature/system spec: purpose, scope, actors, domain concepts, numbered functional requirements

## Dev/frontend/

- Place here: anything rendered in a browser or a mobile view — React, React Native, Skia canvas graphics, Redux state, micro-frontend integration.
- `Dev/frontend/React JS/` - React fundamentals, DOM handling, ejecting from Create React App
- `Dev/frontend/React-Native/` - React Native development, including iOS and Android specifics
- `Dev/frontend/Skia-React-Native/` - Skia graphics on React Native: components, shapes, animations, shaders — see `Dev/frontend/Skia-React-Native/index.md` for its 16 notes
- `Dev/frontend/Redux_Toolkit_Notes.md` - Redux Toolkit: slices, store setup, async state
- `Dev/frontend/Themenblock.md` - RemoteThemenblock vs a traditional remote JavaScript bundle: who owns rendering, and what the host application must provide

### Dev/frontend/React JS/

- Place here: React on the web — components, hooks, DOM, build tooling.
- `Dev/frontend/React JS/01.md` - React fundamentals
- `Dev/frontend/React JS/dom.md` - working with the DOM from React
- `Dev/frontend/React JS/eject.md` - ejecting from Create React App and what it exposes

### Dev/frontend/React-Native/

- Place here: React Native app development, including platform-specific iOS and Android setup.
- `Dev/frontend/React-Native/react-native-01.md` - React Native basics
- `Dev/frontend/React-Native/react-native-02.md` - React Native, continued
- `Dev/frontend/React-Native/react-native-03.md` - React Native, continued
- `Dev/frontend/React-Native/react-native-android-01.md` - Android-specific React Native setup and build
- `Dev/frontend/React-Native/react-native-ios-01.md` - iOS-specific React Native setup and build

## Dev/infra/

- Place here: everything around running and shipping software — CI servers, container platforms, log and metric pipelines, TLS certificates, and application security configuration.
- `Dev/infra/TeamCity/` - TeamCity CI: connections, Docker, environment variables, git hash logging
- `Dev/infra/elastic stack/` - Elastic stack: Metricbeat, Filebeat, dissect processors, certificate generation
- `Dev/infra/openshift/` - OpenShift topics and build/image management
- `Dev/infra/security/` - Spring Security filter chains and client/server certificate handling

### Dev/infra/TeamCity/

- Place here: TeamCity build server configuration.
- `Dev/infra/TeamCity/connection.md` - TeamCity connection setup
- `Dev/infra/TeamCity/docker_connection.md` - connecting TeamCity to Docker
- `Dev/infra/TeamCity/env.md` - environment variables in TeamCity builds
- `Dev/infra/TeamCity/log git hash.md` - logging the git commit hash from a build

### Dev/infra/elastic stack/

- Place here: Elasticsearch, the Beats agents, and the certificates they need.
- `Dev/infra/elastic stack/Metricbeat.md` - Metricbeat setup and configuration
- `Dev/infra/elastic stack/filebeats.md` - Filebeat setup and configuration
- `Dev/infra/elastic stack/filebeats-dissect.md` - the dissect processor for parsing log lines
- `Dev/infra/elastic stack/generate cert steps.md` - step-by-step certificate generation
- `Dev/infra/elastic stack/needed cert.md` - which certificates the stack actually requires

### Dev/infra/openshift/

- Place here: OpenShift platform notes.
- `Dev/infra/openshift/001 Topics.md` - OpenShift topic breakdown
- `Dev/infra/openshift/008 Build and Image Management.md` - builds and image management on OpenShift

### Dev/infra/security/

- Place here: application and transport security — Spring Security internals, certificates, mutual TLS.
- `Dev/infra/security/client and server certificates.md` - client and server certificate setup
- `Dev/infra/security/security.md` - Spring Security filter chain, `CustomPreAuthenticatedProcessingFilter`, the `Authentication` interface, and how the principal flows through the security context

## Dev/languages/

- Place here: programming language reference notes — syntax, type systems, idioms, and language-specific runtime behaviour.
- `Dev/languages/Kotlin/` - Kotlin language reference following a numbered curriculum — see `Dev/languages/Kotlin/index.md` for its 15 notes
- `Dev/languages/Python/` - Python notes (the folder also holds `.py`/`.ipynb` scratch files, which are not notes)
- `Dev/languages/java-ee-monolith-knowledge-gaps-book.md` - Java EE for Spring Boot developers: servlet request flow and the mental-model gaps that trip up someone arriving from Spring
- `Dev/languages/java-functional-interfaces.md` - Java functional interfaces and how they are used
- `Dev/languages/javascript-loops.md` - JavaScript loop forms and related iteration constructs

### Dev/languages/Python/

- Place here: Python language notes. Scratch scripts and notebooks live here too, but are not notes and are not indexed.
- `Dev/languages/Python/python-01.md` - Python fundamentals reference

## Dev/practices/

- Place here: engineering practice not tied to a language or framework — reading code, reviewing, debugging, working with legacy systems.
- `Dev/practices/How to Read and Understand Code Quickly.md` - twelve techniques for reading unfamiliar code fast, plus a six-step algorithm for opening a new project
  - `## 1. Never Read Top-to-Bottom` - start from the question you want answered
  - `## 2. Think in Layers` - entry point → orchestration → business logic → utilities
  - `## 4. Build a Mental Pipeline` - input → transform → decision → output
  - `## 6. Recognise Patterns` - spotting Factory/Strategy/Observer instead of reading 500 lines
  - `## 7. Follow Data, Not Functions` - trace the object, not the call stack
  - `## 9. Find the Important Nouns` - the few central domain objects everything revolves around
  - `## 12. Accept Partial Understanding` - why insisting on 100% comprehension is a time sink
  - `# My Code Reading Algorithm` - the six-step order for opening an unfamiliar project
