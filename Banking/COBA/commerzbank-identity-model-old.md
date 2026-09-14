# Commerzbank Customer, Party, Agreement, and Product Identity Model

## Table of Contents

-   [1. Core Identity Model](#1-core-identity-model)
-   [2. Person and BPKENN](#2-person-and-bpkenn)
-   [3. Party-Group and PartyId](#3-party-group-and-partyid)
-   [4. Kundenverbindung and
    Kundennummer](#4-kundenverbindung-and-kundennummer)
-   [5. Long-Term Customer Number](#5-long-term-customer-number)
-   [6. Party--Kundenverbindung
    Relationship](#6-partykundenverbindung-relationship)
-   [7. Roles and Ownership](#7-roles-and-ownership)
-   [8. Online Teilnehmer and
    Teilnehmernummer](#8-online-teilnehmer-and-teilnehmernummer)
-   [9. Products Under a
    Kundenverbindung](#9-products-under-a-kundenverbindung)
-   [10. Account and Product
    Identifiers](#10-account-and-product-identifiers)
-   [11. IBAN and Check Digits](#11-iban-and-check-digits)
-   [12. Java Domain Model](#12-java-domain-model)
-   [13. Common Lookup Flows](#13-common-lookup-flows)
-   [14. Identifier Cheat Sheet](#14-identifier-cheat-sheet)
-   [15. Open Points / Terminology to
    Verify](#15-open-points--terminology-to-verify)

## 1. Core Identity Model

The banking model separates **person identity**, **party/group
identity**, **customer agreement**, **online participation**, and
**products**. These identifiers must not be treated as synonyms.

``` mermaid
flowchart LR
    P["Person<br/>BPKENN (16)"]
    PG["Party-Group<br/>PGBPKENN (16)"]
    KA["Kundenverbindung<br/>KDNR (10)"]
    PR["Product<br/>Technical Product No. (12)"]
    T["Online Teilnehmer<br/>TNVEKENN (16)"]

    P --> PG
    P -->|"Beteiligung + Rolle"| KA
    PG --> KA
    KA -->|"1 : n"| PR
    T -->|"Zugriff"| KA
    T -->|"sieht"| PR
```

The main questions are:

  Question                                 Concept
  ---------------------------------------- ----------------------------------
  Which natural/legal person?              `BPKENN`
  Which party/group?                       `PGBPKENN` / PartyId
  Which customer agreement/relationship?   `KDNR` / Kundennummer
  Which online participant?                Teilnehmernummer / `TNVEKENN`
  Which concrete banking product?          Product/account/depot identifier

## 2. Person and BPKENN

A `Person` represents a natural person (*natürliche Person*) or legal
person (*juristische Person*).

The ERD associates the Person entity with:

-   `BPKENN`
-   length: 16
-   person master data

A person is not identical to a Kundenverbindung. The same person can
participate in multiple customer agreements and can have a different
role in each.

``` mermaid
flowchart LR
    P["Person<br/>BPKENN"]
    K1["KDNR 1"]
    K2["KDNR 2"]
    K3["KDNR 3"]

    P -->|"Inhaber"| K1
    P -->|"Bevollmächtigter"| K2
    P -->|"other role"| K3
```

## 3. Party-Group and PartyId

The ERD contains a separate `Party-Group` entity identified by
`PGBPKENN (16)`.

This is important for shared/group relationships. A Party-Group is
distinct from an individual Person.

``` mermaid
flowchart LR
    P1["Person A<br/>BPKENN A"]
    P2["Person B<br/>BPKENN B"]
    PG["Party-Group / Gemeinschaft<br/>PGBPKENN"]
    K["Kundenverbindung<br/>KDNR"]

    P1 --> PG
    P2 --> PG
    PG --> K
```

Internal information described `PartyId` as the BPKENN of a
*Gemeinschaft*. Based on the ERD, this should be understood more
precisely as the identifier associated with the Party/Party-Group layer,
potentially `PGBPKENN`.

Do not automatically assume:

``` text
partyId == person's BPKENN
```

The exact mapping depends on the API/object being used.

## 4. Kundenverbindung and Kundennummer

A **Kundennummer (`KDNR`) identifies a Kundenverbindung**.

In the discussed system, the following field names are reported to mean
the same 10-digit identifier:

-   `customerNumber`
-   `internalCustomerNumber`
-   `customerId`
-   `KDNR`
-   Kundennummer

Example format:

``` text
5004002275
```

The conceptual mapping is:

``` mermaid
flowchart LR
    K["Kundennummer / KDNR<br/>10 digits"]
    A["Kundenverbindung<br/>CustomerAgreement"]

    K -->|"identifies"| A
```

One Kundennummer belongs to one Kundenverbindung in this model.

A Kundenverbindung can have:

-   multiple related persons/parties,
-   different roles for those persons/parties,
-   multiple products.

Therefore, a Kundennummer does **not** identify an individual person.

## 5. Long-Term Customer Number

`longTermCustomerNumber` / `longTermCustomerId` is different from the
10-digit KDNR.

An internal example supplied during analysis was alphanumeric rather
than a 10-digit number.

The technical term encountered was:

``` text
VEKNKDNR
```

Current understanding:

  --------------------------------------------------------------------------------
  Identifier                                Same as KDNR? Format
  -------------------------- ---------------------------- ------------------------
  `customerId`                                        Yes 10-digit numeric

  `customerNumber`                                    Yes 10-digit numeric

  `internalCustomerNumber`                            Yes 10-digit numeric

  `longTermCustomerId`                                 No Different/alphanumeric

  `VEKNKDNR`                    Associated with long-term Different/alphanumeric
                                      customer identifier 
  --------------------------------------------------------------------------------

The precise semantics and lifecycle of `VEKNKDNR` should be verified
against the owning internal system.

## 6. Party--Kundenverbindung Relationship

The relationship between a party/person and a Kundenverbindung is not
merely a foreign key. It carries business information such as the
**role**.

Conceptually:

``` mermaid
erDiagram
    PERSON ||--o{ AGREEMENT_ROLE : has
    CUSTOMER_AGREEMENT ||--o{ AGREEMENT_ROLE : has

    PERSON {
        string partyId
    }

    CUSTOMER_AGREEMENT {
        string customerId
        string longTermCustomerId
    }

    AGREEMENT_ROLE {
        string customerId
        string partyId
        string role
        string roleLabel
        string addressId
    }
```

This is an association/junction model:

``` text
Party/Person ↔ AgreementRole ↔ CustomerAgreement
```

A Party can be associated with multiple Kundennummern. In the discussed
business context, a PartyId has at least one Kundennummer/AgreementID,
and each Kundennummer can contain many products.

``` mermaid
flowchart LR
    PA["PartyId"]
    A1["KDNR / Agreement 1"]
    A2["KDNR / Agreement 2"]
    P11["Product"]
    P12["Product"]
    P21["Product"]

    PA --> A1
    PA --> A2
    A1 --> P11
    A1 --> P12
    A2 --> P21
```

Whether every Party in every upstream system must always have at least
one KDNR remains a system-specific cardinality rule.

## 7. Roles and Ownership

A person's identity does not by itself determine what the person may do
within a Kundenverbindung. The **relationship carries the role**.

Examples seen in the conceptual model include:

-   Inhaber
-   gesetzlicher Vertreter
-   Bevollmächtigter

In the Java implementation, the configured owner roles are:

``` java
private static final Set<String> OWNER_ROLES =
        Collections.unmodifiableSet(
                new HashSet<>(Arrays.asList(
                        "EI",
                        "MI",
                        "GF"
                ))
        );
```

The existing ownership check is:

``` java
private boolean isOwner(
        final String internalCustomerNumber,
        final Person person) {

    return person
            .getAgreementRoles()
            .stream()
            .filter(role -> OWNER_ROLES.contains(role.getRole()))
            .anyMatch(role ->
                    internalCustomerNumber.equals(role.getCustomerId()));
}
```

This answers:

> Does this Person have an owner role for this particular Kundennummer?

The logic is:

``` mermaid
flowchart LR
    P["Person"]
    AR["Agreement Roles"]
    R{"role ∈<br/>{EI, MI, GF}?"}
    K{"customerId ==<br/>requested KDNR?"}
    O["Person is an owner"]

    P --> AR --> R
    R -->|"yes"| K
    K -->|"yes"| O
```

### Finding owners from the agreement side

`CustomerAgreement` already contains `agreementRoles`. Therefore, given
a KDNR, the natural lookup is:

``` java
List<AgreementRole> ownerRoles = customerAgreement
        .getAgreementRoles()
        .stream()
        .filter(agreementRole ->
                OWNER_ROLES.contains(agreementRole.getRole()))
        .toList();
```

Each matching `AgreementRole` contains the corresponding `partyId`.

``` mermaid
flowchart LR
    K["KDNR"]
    CA["CustomerAgreement"]
    AR["agreementRoles[]"]
    F["role ∈ {EI, MI, GF}"]
    PI["Owner PartyId(s)"]

    K --> CA --> AR --> F --> PI
```

Ownership therefore belongs to the **Party ↔ Agreement relationship**,
not to the KDNR itself.

## 8. Online Teilnehmer and Teilnehmernummer

There are two identifiers that must not be confused.

### Customer-facing Teilnehmernummer

Public Commerzbank Digital Banking documentation describes the
**Teilnehmernummer as a 10-digit identification/login number**. It is
separate from the account number.

### Internal TNVEKENN

The supplied ERD models:

``` text
Teilnehmer (online)
TNVEKENN (16)
```

Therefore:

  ------------------------------------------------------------------------
  Identifier                                  Length Purpose
  --------------------- ---------------------------- ---------------------
  Teilnehmernummer                         10 digits Customer-facing
                                                     Digital Banking
                                                     participant/login
                                                     identifier

  `TNVEKENN`                                      16 Internal identifier
                                                     of the Teilnehmer
                                                     entity
  ------------------------------------------------------------------------

They are not the same identifier.

The ERD additionally separates online access from the person's
business/legal role:

``` mermaid
flowchart LR
    P["Person<br/>BPKENN"]
    B["Beteiligung<br/>business/legal role"]
    K["Kundenverbindung<br/>KDNR"]
    T["Teilnehmer<br/>TNVEKENN"]
    Z["Zugriff<br/>opt-in / opt-out"]

    P --> B --> K
    T --> Z --> K
```

This distinction answers two separate questions:

-   **Beteiligung/Rolle:** What is the person's business/legal
    relationship?
-   **Zugriff:** What may the online participant access?

The ERD also contains a `sieht` relationship from Teilnehmer to Product,
indicating product visibility/access as a separate concern.

## 9. Products Under a Kundenverbindung

A Kundenverbindung can contain multiple products.

``` mermaid
flowchart LR
    K["Kundenverbindung<br/>KDNR"]
    G["Girokonto"]
    D["Depot"]
    V["Verrechnungskonto"]
    O["Other Product"]

    K --> G
    K --> D
    K --> V
    K --> O
```

The ERD describes the product level using:

-   technical product number `(12)`
-   product type

The whiteboard additionally referenced product-specific identifiers such
as Kontonummer and Depotnummer.

The hierarchy to remember is:

``` mermaid
flowchart LR
    PA["Party"]
    A["Kundennummer / AgreementID"]
    P["Products"]

    PA -->|"1..n in discussed context"| A
    A -->|"1..n"| P
```

## 10. Account and Product Identifiers

Different identifiers answer different questions.

### Kontonummer

Identifies an account within the banking/account domain.

### IBAN

Identifies a payment account in the standardized payment domain. A
German IBAN has 22 characters:

``` text
DEkk BBBBBBBB CCCCCCCCCC
```

where:

-   `DE` = country code
-   `kk` = check digits
-   `BBBBBBBB` = Bankleitzahl
-   `CCCCCCCCCC` = 10-digit account-number field

### Depotnummer

Identifies a securities depot. A depot is not itself a payment account
and therefore does not require an IBAN.

### Technical product/account identifier

Backend systems can use technical identifiers independently of
customer-facing account identifiers. The ERD explicitly shows a
12-character technical product number.

Do not treat these as interchangeable:

``` text
KDNR ≠ Kontonummer ≠ Depotnummer ≠ IBAN ≠ technical product number
```

## 11. IBAN and Check Digits

Check digits (*Prüfziffern*) provide mathematical redundancy for
detecting input/transmission errors.

For IBAN, validation uses **MOD-97**.

For a German IBAN such as:

``` text
DE89 3704 0044 0532 0130 00
```

move the first four characters to the end:

``` text
370400440532013000DE89
```

Convert letters using:

$$
A=10,\;B=11,\;\ldots,\;Z=35
$$

Thus:

$$
D=13,\qquad E=14
$$

giving:

$$
N=370400440532013000131489
$$

A valid IBAN satisfies:

$$
N \bmod 97 = 1
$$

or equivalently:

$$
N \equiv 1 \pmod{97}
$$

### Generating check digits

Replace the check digits with `00`, transform the IBAN, and calculate:

$$
r=N_0\bmod97
$$

Then:

$$
\text{check digits}=98-r
$$

For the example, the result is `89`.

A valid checksum proves that the identifier is structurally consistent;
it does **not** prove that the account exists or belongs to a particular
customer.

## 12. Java Domain Model

### Person

The supplied `Person` model contains:

``` java
private Person(
        final String partyId,
        final String partyType,
        final String tenant,
        final String countryOfForeignTradeRegulations,
        final String countryOfTaxLiability,
        final List<ShipmentAddress> shipmentAddresses,
        final List<PartyAgreementRole> agreementRoles,
        final String lastName,
        final String firstName,
        final LocalDate dateOfBirth,
        final String placeOfBirth,
        final String birthCountryCode,
        final List<String> nationalities,
        final String email,
        final String phoneNumber,
        final String individualSalutation,
        final String salutation,
        final String title,
        final String titleOfNobility,
        final String salutationExtension,
        final String titleExtension) {
    // ...
}
```

The relevant identity/relationship fields are:

``` text
partyId
agreementRoles[]
```

### PartyAgreementRole

The supplied persistence entity contains:

``` java
class PartyAgreementRole {

    private Long id;
    private String customerId;
    private String partyId;
    private String addressId;
    private String role;
    private String roleLabel;
}
```

This exposes agreement relationships from the Person/Party side.

### CustomerAgreement

The supplied object contains:

``` java
public class CustomerAgreement {

    private String customerId;
    private String longTermCustomerId;
    private String typeOfCustomer;
    private String typeOfAgreement;
    private String customerTypology;
    private String tenant;
    private String status;

    private List<AgreementRole> agreementRoles;
    private List<ShipmentAddress> shipmentAddresses;
}
```

Here:

``` text
customerId = KDNR / Kundennummer
```

while `longTermCustomerId` is a different identifier.

### AgreementRole

The supplied object contains:

``` java
public class AgreementRole {

    private String customerId;
    private String partyId;
    private String firstName;
    private String lastName;
    private String legalName;
    private String role;
    private String roleLabel;
    private String addressId;
}
```

This gives the same fundamental relationship from the agreement side:

``` mermaid
flowchart LR
    P["Person"]
    PAR["PartyAgreementRole"]
    R["Party ↔ Agreement<br/>customerId + partyId + role"]
    AR["AgreementRole"]
    CA["CustomerAgreement"]

    P --> PAR --> R
    CA --> AR --> R
```

`PartyAgreementRole` and `AgreementRole` are therefore two domain/API
representations of essentially the same conceptual relationship viewed
from different directions.

## 13. Common Lookup Flows

### Kundennummer → CustomerAgreement

The code retrieves an agreement using the 10-digit
`internalCustomerNumber`:

``` java
CustomerAgreement customerAgreement =
        customerAgreementMnC.retrieveCustomerAgreement(
                request.getInternalCustomerNumber(),
                technicalUserCore,
                ApplicationContextProvider.getLocale(),
                ApplicationContextProvider.getChannel().asString(),
                ApplicationContextProvider.getRequestId());
```

The identifying input is:

``` text
request.getInternalCustomerNumber()
        ↓
KDNR / Kundennummer
        ↓
CustomerAgreement
```

The remaining parameters are technical/request context rather than
agreement identifiers.

### Kundennummer → Owner PartyId(s)

``` mermaid
flowchart LR
    K["KDNR"]
    CA["retrieveCustomerAgreement()"]
    AR["agreementRoles"]
    OR["Filter owner roles<br/>EI / MI / GF"]
    PI["partyId(s)"]

    K --> CA --> AR --> OR --> PI
```

### PartyId → Agreements

From the Person/Party side:

``` mermaid
flowchart LR
    P["PartyId"]
    AR["agreementRoles"]
    K1["customerId / KDNR 1"]
    K2["customerId / KDNR 2"]

    P --> AR
    AR --> K1
    AR --> K2
```

### Kundennummer → Products

``` mermaid
flowchart LR
    K["KDNR / CustomerAgreement"]
    P1["Product 1"]
    P2["Product 2"]
    PN["Product n"]

    K --> P1
    K --> P2
    K --> PN
```

## 14. Identifier Cheat Sheet

  ------------------------------------------------------------------------------------------
  Identifier / field         Length / format          Identifies          Notes
  -------------------------- ------------------------ ------------------- ------------------
  `BPKENN`                   16                       Natural/legal       Person-level
                                                      Person              internal
                                                                          identifier

  `PGBPKENN`                 16                       Party-Group /       Distinct from
                                                      Gemeinschaft        individual BPKENN

  `partyId`                  Context-dependent        Party/Party-Group   Exact mapping
                                                                          depends on API;
                                                                          internal
                                                                          information links
                                                                          it to Gemeinschaft

  `KDNR`                     10 digits                Kundenverbindung    Kundennummer

  `customerId`               10 digits                Kundenverbindung    Same KDNR in
                                                                          discussed model

  `customerNumber`           10 digits                Kundenverbindung    Same KDNR

  `internalCustomerNumber`   10 digits                Kundenverbindung    Same KDNR; despite
                                                                          the name, not a
                                                                          separate ID here

  `longTermCustomerId`       Alphanumeric/different   Long-term customer  Not the KDNR
                                                      identifier          

  `VEKNKDNR`                 Alphanumeric/different   Long-term customer  Precise semantics
                                                      identifier          still to verify

  Teilnehmernummer           10 digits                Online-banking      Customer-facing
                                                      participant/login   

  `TNVEKENN`                 16                       Teilnehmer entity   Internal
                                                                          identifier; not
                                                                          Teilnehmernummer

  Kontonummer                Product-specific         Account             Account-domain
                                                                          identifier

  IBAN                       22 chars in Germany      Payment account     Includes country,
                                                                          check digits, BLZ
                                                                          and account-number
                                                                          field

  Depotnummer                Product-specific         Securities depot    No IBAN required
                                                                          for the depot
                                                                          itself

  Technical product no.      12 in supplied ERD       Product             Internal product
                                                                          identifier
  ------------------------------------------------------------------------------------------

## 15. Open Points / Terminology to Verify

The following should remain explicitly marked as system-specific until
confirmed from authoritative internal documentation:

1.  Exact expansion and semantics of `BPKENN`.
2.  Exact expansion and semantics of `PGBPKENN`.
3.  Whether every `partyId` in every API always represents a Party-Group
    identifier or whether its semantics vary by endpoint/model.
4.  Exact semantics, source system, and lifecycle of `VEKNKDNR` /
    `longTermCustomerId`.
5.  Business meanings of owner-role codes `EI`, `MI`, and `GF`.
6.  Exact cardinality rules for Party → Kundenverbindung outside the
    currently discussed application context.
7.  Exact relationship between the customer-facing 10-digit
    Teilnehmernummer and internal 16-character `TNVEKENN`.

> \[!IMPORTANT\] Do not infer identifier equivalence merely from similar
> names. In this domain, `Kundennummer`, `Teilnehmernummer`, `BPKENN`,
> `PGBPKENN`, `TNVEKENN`, product numbers, and IBANs belong to different
> identity layers.
