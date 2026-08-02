# MiFID II, WpHG and Related Banking Concepts

## Table of Contents

- [MiFID II](#MiFID%20II)
- [WpHG vs MiFID II](#WpHG%20vs%20MiFID%20II)
- [Main MiFID Business Processes](#Main%20MiFID%20Business%20Processes)
- [Target Market (TaMrA)](#Target%20Market%20(TaMrA))
- [Geeignetheitserklärung (GEE)](#Geeignetheitserklärung%20(GEE))
- [BaFin Registration of Investment Advisors](#BaFin%20Registration%20of%20Investment%20Advisors)
- [Typical End-to-End Advisory Flow](#Typical%20End-to-End%20Advisory%20Flow)
- [Developer Perspective](#Developer%20Perspective)

# MiFID II

**MiFID II is the EU framework that defines how investment services must
be provided to protect investors and ensure fair financial markets.**

It governs: - Securities accounts (Depots) - Stocks, ETFs, bonds -
Derivatives - Investment advice - Portfolio management

Main goals: - Investor protection - Market transparency - Standardised
rules across the EU - Fair competition - Auditability

# WpHG vs MiFID II

**WpHG is not the same as MiFID II.**

Relationship:

``` text
EU
│
├── MiFID II (Directive)
│       │
│       └── Implemented in Germany mainly through:
│             - WpHG
│             - WpDVerOV
│             - Börsengesetz
│             - BaFin regulations
│
└── MiFIR (Regulation)
        └── Directly applicable in all EU countries
```

For a retail bank, most customer-facing MiFID requirements are
implemented through the WpHG.

# Main MiFID Business Processes

Typical advisory flow:

``` text
Customer
    ↓
Identity Check
    ↓
Client Classification
    ↓
Knowledge & Experience
    ↓
Risk Profile
    ↓
Suitability Assessment
    ↓
Target Market Check
    ↓
Recommendation
    ↓
Geeignetheitserklärung (GEE)
    ↓
Order Execution
```

Important concepts:

-   Client Classification
-   Appropriateness Check (Knowledge & Experience)
-   Suitability Check
-   Target Market
-   Best Execution
-   Cost Transparency
-   Audit Logging

# Target Market (TaMrA)

**TaMrA is typically the Target Market Assessment.**

Purpose: Determine whether the recommended product belongs to the
customer's intended target market.

Typical comparison:

  Customer                Product
  ----------------------- --------------------------
  Client category         Intended client category
  Knowledge               Required knowledge
  Risk tolerance          Product risk
  Investment objective    Intended objective
  Investment horizon      Recommended horizon
  Loss-bearing capacity   Required capacity
  ESG preferences         ESG characteristics

Possible outcomes: - Match - Outside positive target market - Negative
target market (normally not distributable)

# Geeignetheitserklärung (GEE)

**The GEE explains why the bank's recommendation is suitable for the
customer.**

Created after the suitability assessment.

Contains: - Recommended product(s) - Investment objectives - Risk
profile - Financial situation - Knowledge & experience - Investment
horizon - Explanation of suitability - Warnings - Advisor information

Typical architecture:

``` text
Customer Profile
      │
Risk Profile
      │
Knowledge & Experience
      │
Target Market
      │
Recommendation Engine
      │
      ▼
GEE Generator
      ▼
PDF
```

# BaFin Registration of Investment Advisors

**Investment advisors are not personally licensed by BaFin. The bank
reports and supervises them.**

Typical process:

``` text
Employee
    ↓
Training
    ↓
Knowledge (Sachkunde)
    ↓
Reliability (Zuverlässigkeit)
    ↓
Bank reports employee to BaFin
(Mitarbeiterregister)
    ↓
Advisor may provide investment advice
```

Typical system checks: - Advisor authorised - Advisory role assigned -
Training valid - Registration maintained

Recorded during advisory: - Advisor ID - Branch - Timestamp - Customer
profile - Recommendation - Generated GEE - Audit trail

# Typical End-to-End Advisory Flow

``` text
Advisor Login
      ↓
Authorisation Check
      ↓
Customer Data
      ↓
Questionnaires
      ↓
Risk Profile
      ↓
Suitability Check
      ↓
Target Market Assessment (TaMrA)
      ↓
Recommendation
      ↓
Generate GEE
      ↓
Customer signs
      ↓
Order execution
```

# Developer Perspective

Common implementation areas: - Validation rules - Workflow engine -
Questionnaires - Target market engine - Recommendation engine - GEE
generation - PDF generation - Audit logging - Advisor authorisation -
Versioned legal documents

For projects like WPFE, common modules include: - Investor Profile -
Sustainability - WpHG Finalisation - Target Market - Recommendation -
Geeignetheitserklärung
