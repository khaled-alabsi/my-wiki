# Banking Product Information and Suitability in Germany

## Table of Contents
- [1. Product information documents](#1-product-information-documents)
- [2. How the names relate](#2-how-the-names-relate)
- [3. Suitability and recommendation](#3-suitability-and-recommendation)
- [4. What happens when the customer changes the recommendation](#4-what-happens-when-the-customer-changes-the-recommendation)
- [5. Context: the new Altersvorsorgedepot](#5-context-the-new-altersvorsorgedepot)
- [6. Practical system view](#6-practical-system-view)
- [7. Short terminology map](#7-short-terminology-map)
- [8. Sources](#8-sources)

## 1. Product information documents

German banking and investment processes often use short, standardized documents to explain a financial product before the customer buys it. The purpose is to make the product understandable and comparable.

Common terms:

- **PIB** = Produktinformationsblatt
- **BIB** = Basisinformationsblatt
- **KID** = Key Information Document
- **KIID** = Key Investor Information Document

These are not all the same thing. Some are older German terms, some are EU terms, and some apply only to specific product types.

## 2. How the names relate

### PIB
The **Produktinformationsblatt (PIB)** is an older German product information sheet. In the German retirement-product area, BMF documentation still refers to PIB under the old certification framework.  

### BIB / KID
The **Basisinformationsblatt (BIB)** is the German term for the EU **Key Information Document (KID)** under the PRIIPs regime. It is the standardized pre-contractual document for many packaged retail and insurance-based investment products.

### KIID
The **Wesentliche Anlegerinformationen (KIID)** is a different document used for UCITS funds under older fund rules. It has the same general purpose, but it is not identical to the PRIIPs KID/BIB.

### Practical rule
- **BIB = KID** in practice.
- **KIID** is a different, fund-specific document.
- **PIB** is another, older product information form used in some contexts.

## 3. Suitability and recommendation

In advice processes, the bank or advisor performs a **suitability assessment**. In German this is the **Geeignetheitsprüfung**. The result of that process is the recommendation.

The advice flow usually looks like this:

```text
Customer profile collected
    ↓
Suitability assessment
    ↓
Recommended product or portfolio
    ↓
Customer receives explanation / documentation
    ↓
Customer decides whether to continue
```

The customer is not forced to buy the recommended product. The customer can still stop, compare, or request changes.

## 4. What happens when the customer changes the recommendation

If the customer changes the recommended configuration, the original recommendation may no longer match the assessed suitability.

There are two main cases:

### Case 1: the change is still suitable
The customer modifies something, but the result remains consistent with the customer profile.

Example:
- one ETF is replaced by another similar ETF
- the allocation changes only slightly
- the portfolio remains within the target risk profile

In that case, the bank should re-evaluate the recommendation and regenerate the documentation so that the final recommendation and the explanation stay aligned.

### Case 2: the change is no longer suitable
The customer changes the product or allocation in a way that conflicts with the suitability result.

Example:
- a conservative customer moves into a very high-risk portfolio
- the equity share becomes much higher than the assessed risk profile allows

Then the bank must not simply continue as if the old recommendation still applies. The system must re-check suitability, and depending on the business design it may:
- block the change,
- warn the customer,
- require a new recommendation,
- or move the customer into a different process that is not advice-based.

## 5. Context: the new Altersvorsorgedepot

For the new tax-favored private pension framework, the same basic logic matters during the life of the contract, not only at the start.

The BMF FAQ says the new products are meant to be more flexible and that product information should be standardized and made available so that people can compare offers. The current public FAQ also describes the new **Altersvorsorgedepot** as part of the reformed product world.

The practical implication is:

- when the customer selects or changes a pension investment,
- the bank must check whether the final configuration is still suitable,
- and the documentation must match the final advised configuration.

That means a later change can require a new recommendation and a new suitability explanation.

## 6. Practical system view

A typical implementation in a bank may look like this:

```text
Advisor recommendation
      ↓
Suitability result stored
      ↓
Geeignetheitserklärung generated
      ↓
Customer clicks "reconfigure"
      ↓
Portfolio changes
      ↓
Suitability engine runs again
      ↓
New recommendation and new documentation
      ↓
Customer can continue
```

If the new portfolio is not suitable, the process should not continue as an advised recommendation without a fresh assessment.

## 7. Short terminology map

- **Produktinformationsblatt / PIB**: older German product information sheet
- **Basisinformationsblatt / BIB**: PRIIPs product information sheet in German
- **Key Information Document / KID**: English term for BIB under PRIIPs
- **Wesentliche Anlegerinformationen / KIID**: older fund disclosure document for UCITS
- **Geeignetheitsprüfung**: suitability assessment
- **Geeignetheitserklärung**: written suitability explanation
- **Altersvorsorgedepot**: tax-favored private pension investment account in the reform context

## 8. Sources

1. **WpHG § 64** — official German law text for investment advice information duties and suitability-related reporting.
2. **EU PRIIPs Regulation (EU) No 1286/2014** — official EU rule for Key Information Documents.
3. **BaFin PRIIPs information** — confirms the PRIIPs BIB/KID framework in Germany.
4. **BMF FAQ on the reform of private pension provision** — official current policy context for the new Altersvorsorgedepot and flexible product world.
5. **BMF historical PIB/AltvPIBV notices** — confirm that PIB is an older German product information document in the pension-product area.
