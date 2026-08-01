Here is the corrected, fully reconstructed business analysis of `Track 7.md`, updated to explicitly capture data acquisition workflows, conditional lookups, and state-dependent dependencies as required by the revised system prompt.

---

### 1. Executive Summary
The transcript captures a sprint refinement session for a **Wealth Management & Investment Advisory Platform**. The team is prioritizing and clarifying backlog items related to the lifecycle of retirement savings products (`AVD`), regulatory document delivery, metadata management, content integration, caching configuration, and client eligibility gating. The core business objective is to enable compliant product configuration, generate and archive mandatory disclosure documents, deliver finalized metadata to core banking systems, and enforce strict access controls based on account type.

### 2. Business Context
The domain is **Retail/Institutional Investment Advisory**, specifically focused on **retirement savings products** (Altersvorsorge). The platform supports financial advisors in configuring investment products for clients, generating regulatory disclosure documents, archiving them according to compliance standards, and delivering metadata to downstream depot systems. The business operates in a regulated environment requiring strict document lifecycle management, data privacy, and access control.

### 3. Key Concepts
| Business Concept | Description |
|------------------|-------------|
| **AVD (Altersvorsorge Depot)** | Retirement savings account. A specific product type with regulatory restrictions. |
| **TIP-Dokument** | Product Information Plan (PRIIPs/KID equivalent). Mandatory pre-contractual disclosure. |
| **GE-Dokument** | Fee Overview (Gebührenübersicht). Regulatory disclosure of costs. |
| **Ex-Anton** | Exposé/Prospectus. Detailed product offering document. |
| **Metadata & Archiving** | Business linkage mechanism associating generated documents with a specific client depot for long-term storage and retrieval. |
| **Contentful Integration** | External Content Management System used to serve product marketing/content information to advisors/clients. |
| **Caching Layer** | Business performance mechanism for storing frequently accessed, pseudonymized data to reduce system load. |
| **Eligibility Gate** | Business rule restricting product configuration/access based on account type and status. |

### 4. Business Process
**AVD Product Advisory & Document Lifecycle:**
1. **Product Configuration:** Advisor selects/configures an AVD product for a client.
2. **Document Generation:** System automatically generates TIP, GE, Suitability, and Ex-Anton documents upon configuration completion.
3. **Archiving:** Documents are immediately archived in the document management system (`DocFamily`).
4. **Metadata Update:** System updates archive metadata to link documents to the specific depot/reference level.
5. **Downstream Delivery:** Latest version of the TIP document is delivered to the downstream system (`WBF-E-SAU`).
6. **Content Display:** Frontend retrieves product-specific content from `Contentful` and displays it in a dedicated information layer.
7. **Eligibility Gate:** System validates client account status before allowing product configuration/access.

**Data Acquisition Workflow (Customer Identity & Birthdate):**
1. **Frontend Selection:** Advisor selects a client from a dropdown list of available Customer IDs.
2. **Identity Resolution:** System resolves the selected Customer ID to the `Inhaber` (account owner) using `Acting Person ID` or `Party ID`.
3. **API Lookup:** System calls the `Natural Person API Client` to retrieve detailed person data.
4. **Data Extraction:** System maps and extracts the `Birthdate` for compliance/advisory requirements.
5. **Validation:** System verifies the retrieved data matches the AVD eligibility rules (natural person, active account).

### 5. Business Rules
- **Rule 1 (Document Priority):** Only the **latest version** of the TIP document shall be delivered to the downstream system.
- **Rule 2 (Lifecycle Order):** Documents must be successfully archived **before** metadata can be updated or delivered.
- **Rule 3 (Account Type Restriction):** Only clients with an active **AVD depot** are eligible to configure/access specific retirement products.
- **Rule 4 (Entity Restriction):** AVD accounts can **only be held by natural persons** (not legal entities).
- **Rule 5 (Data Requirement):** Customer birthdate is required for advisory compliance and must be retrieved from the Natural Person data source.
- **Rule 6 (Content Delivery):** Product information layer content is dynamically fetched from an external CMS (`Contentful`) based on the selected product.
- **Rule 7 (Eligibility Gate):** Product configuration is explicitly denied if the client lacks an active AVD depot.

### 6. Decision Logic
```text
IF Customer has valid AVD Depot:
  → ALLOW product configuration & document generation
  → ENABLE metadata update & downstream delivery
ELSE:
  → DENY product access
  → Block configuration workflow

IF Documents successfully archived:
  → Trigger metadata update to link to depot
  → Deliver latest TIP to downstream system
ELSE:
  → Block metadata update & delivery

IF Product ID is available in context:
  → Query Contentful for product content
  → Render content layer in frontend
ELSE:
  → Wait until product selection is confirmed

IF Frontend selects Customer ID:
  → Resolve to Party/Acting Person ID
  → Call Natural Person API → Extract Birthdate
  → Validate against compliance & eligibility rules
```

### 7. Actors
| Role | Business Responsibility |
|------|-------------------------|
| **Client/Investor** | Natural person opening or holding an AVD account. |
| **Financial Advisor** | Configures products, reviews documents, initiates advisory workflow. |
| **System (AM Platform)** | Automates document generation, metadata management, and eligibility checks. |
| **System (SAO)** | Sales/Advisory Operations system triggering product configuration. |
| **System (WBF-E-SAU)** | Core depot/banking system receiving finalized document metadata. |
| **External Service (DocFamily)** | Secure document archiving & retrieval system. |
| **External Service (Contentful)** | CMS providing dynamic product content. |

### 8. Important Objects
- `Customer / Natural Person` (Attributes: ID, Birthdate, Account Status, Party/Acting ID)
- `AVD Depot` (State: Active/Inactive, Type: Retirement)
- `Product` (Attributes: Product-ID, Risk Class, Fee Structure)
- `Advisory Documents` (TIP, GE, Suitability, Ex-Anton)
- `Archive Metadata` (Linkage: Document ↔ Depot, Versioning, Timestamp)
- `Cache Entry` (Pseudonymized ID, Expiration, Access Frequency)

### 9. Inputs / Outputs
| Category | Details |
|----------|---------|
| **Inputs** | Customer/Advisor IDs, Product ID, AVD account status, Configuration completion event, Frontend selection |
| **Outputs** | Archived documents, Updated archive metadata, Latest TIP delivery payload, CMS product content, Cache records |
| **Documents** | TIP, GE, Suitability, Ex-Anton, Metadata records, Cache logs |
| **Events** | Product configuration completed, Document archived, Metadata updated, Content requested, Identity resolved |

### 10. Dependencies
- **Upstream:** SAO process (triggers configuration), Customer Master Data (provides IDs & birthdate)
- **Downstream:** WBF-E-SAU (receives latest TIP), Core Banking/Depot System (relies on metadata linkage)
- **External:** DocFamily (archiving), Contentful (CMS), Shared Services (pseudonymization library)
- **Internal:** AM Platform (document generation), Frontend (content display), Backend (API routing, cache config)

### 11. Regulatory Aspects
- **PRIIPs/KID:** `TIP-Dokument` fulfills pre-contractual product disclosure requirements.
- **MiFID II:** `Suitability` and `GE (Gebührenübersicht)` ensure transparency of costs and product-client fit.
- **Archiving Obligations:** Documents must be securely stored with traceable metadata linked to the depot.
- **Data Privacy (GDPR):** Pseudonymization cache and birthdate handling imply strict access controls and data minimization requirements.
- **Eligibility Rules:** Restricting AVD to natural persons aligns with retirement savings regulatory frameworks.

### 12. Assumptions
| Assumption | Basis | Confidence |
|------------|-------|------------|
| `AVD` = Altersvorsorge (Retirement Savings) | Contextual German financial terminology | High |
| `AM` = Advisory Management / Account Management | Platform handling document generation & metadata | High |
| `SAO` = Sales/Advisory Operations | Triggers product configuration workflow | Medium |
| `WBF-E-SAU` = Core Depot/Banking System | Downstream recipient of finalized metadata | Medium |
| `Ex-Anton` = Exposé/Prospectus | German financial documentation convention | High |
| Team is in Sprint Refinement/Planning | Scrum Poker, story prioritization, backlog movement | High |

### 13. Missing Information
- Exact data model schemas for `TIP`, `GE`, and metadata linkage.
- Current implementation status of Shared Services (pseudonymization library).
- Full API contract between Frontend, Backend, and Contentful.
- Detailed error handling & retry logic for document archiving failures.
- Complete list of products covered by the AVD eligibility rule.

### 14. Risks
- **Testing Complexity:** Requires specific test customer profiles (with/without AVD depot), increasing validation effort.
- **Dependency Delays:** Reliance on external/Shared services (Redis, Contentful, Pseudonymization) may block delivery.
- **Lifecycle Misalignment:** Story prioritization currently out of sequence with actual document generation & archiving capabilities.
- **Data Mapping Gaps:** Uncertainty around whether birthdate is fully mapped in the Natural Person API client.

### 15. Open Questions
1. What is the exact source and timing of the `Product-ID` in the workflow?
2. How is the `Frontend vs. Backend` responsibility split for the Contentful integration?
3. What is the current status of the Shared Services merge for pseudonymization?
4. How are failed archiving attempts handled (retry, alert, rollback)?
5. What specific metadata fields must be updated when linking documents to a depot?

### 16. Suggested Next Investigation Areas
- **Data Model Review:** Map `Customer`, `Natural Person`, `AVD Depot`, and `Product` relationships.
- **Document Lifecycle Validation:** Trace full path from configuration → generation → archiving → metadata update → delivery.
- **API Contract Definition:** Formalize contracts for Natural Person service, Contentful integration, and Metadata endpoint.
- **Test Data Strategy:** Define test customer profiles and AVD account states for eligibility validation.
- **Dependency Audit:** Verify status of Redis caching, Shared pseudonymization, and Contentful integration readiness.

### 17. Overall Big Picture
This domain represents a **regulated Wealth Management Advisory Platform** enabling financial advisors to configure retirement savings products, generate mandatory disclosure documents, and manage their secure lifecycle. The business prioritizes **compliance** (PRIIPs, MiFID II, archiving), **data integrity** (metadata linkage, version control), **performance** (caching strategy), and **access control** (AVD eligibility gating). The platform acts as an orchestrator between advisory workflows, document management, core banking systems, and external content delivery, ensuring that regulatory obligations are met while maintaining system responsiveness and advisor efficiency.

---
**Confidence Level:** High for business concepts & rules. Medium for system acronyms & exact data flows.  
**Classification:** Business Architecture / Domain Extraction  
**Next Step:** Validate assumptions with product owners & system architects; draft capability map & process sequence diagram.