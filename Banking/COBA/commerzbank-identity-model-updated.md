# Commerzbank Customer, Party, Agreement, and Product Identity Model

## Table of Contents

-   [1. Terminology: German, English, and
    Synonyms](#1-terminology-german-english-and-synonyms)
-   [2. Core Identity Model](#2-core-identity-model)
-   [3. Person and BPKENN](#3-person-and-bpkenn)
-   [4. Party-Group and PartyId](#4-party-group-and-partyid)
-   [5. Kundenverbindung and
    Kundennummer](#5-kundenverbindung-and-kundennummer)
-   [6. Long-Term Customer Number](#6-long-term-customer-number)
-   [7. Party--Kundenverbindung
    Relationship](#7-partykundenverbindung-relationship)
-   [8. Roles and Ownership](#8-roles-and-ownership)
-   [9. Online Teilnehmer and
    Teilnehmernummer](#9-online-teilnehmer-and-teilnehmernummer)
-   [10. Products Under a
    Kundenverbindung](#10-products-under-a-kundenverbindung)
-   [11. Account and Product
    Identifiers](#11-account-and-product-identifiers)
-   [12. IBAN and Check Digits](#12-iban-and-check-digits)
-   [13. Java Domain Model](#13-java-domain-model)
-   [14. Common Lookup Flows](#14-common-lookup-flows)
-   [15. Identifier Cheat Sheet](#15-identifier-cheat-sheet)
-   [16. Open Questions and Uncertain
    Points](#16-open-questions-and-uncertain-points)

## 1. Terminology: German, English, and Synonyms

The same business concept appears under different German, English, API,
and legacy-system names.

> \[!NOTE\] `*` marks a mapping or interpretation that is not fully
> verified. See [Open Questions and Uncertain
> Points](#16-open-questions-and-uncertain-points).

  -------------------------------------------------------------------------------------------------
  German / business     English meaning      Synonyms / code names seen  Current interpretation
  term                                                                   
  --------------------- -------------------- --------------------------- --------------------------
  Person                Person / legal       `Person`, `BPKENN`          Natural or legal person
                        entity                                           

  Beteiligung           Participation /      `AgreementRole`,            Person/party ↔
                        relationship         `PartyAgreementRole`        Kundenverbindung
                                                                         relationship carrying a
                                                                         role

  Rolle                 Role                 `role`, `roleLabel`         E.g. Inhaber,
                                                                         Bevollmächtigter,
                                                                         gesetzlicher Vertreter

  Gemeinschaft /        Party group / shared `PartyId`\*, `PGBPKENN`     Group/party layer,
  Party-Group           party                                            relevant for shared
                                                                         relationships

  Kundenverbindung      Customer             `CustomerAgreement`,        Business relationship
                        relationship /       Agreement                   identified by KDNR
                        customer agreement                               

  Kundennummer          Customer number      `KDNR`, `customerId`,       10-digit identifier of a
                                             `customerNumber`,           Kundenverbindung in this
                                             `internalCustomerNumber`,   system
                                             `AgreementID`               

  langfristige          Long-term customer   `longTermCustomerId`,       Different from 10-digit
  Kundennummer\*        number               `longTermCustomerNumber`,   KDNR; exact semantics open
                                             `VEKNKDNR`\*                

  Teilnehmer            Online participant   participant                 Online-banking
                                                                         participation/access
                                                                         entity

  Teilnehmernummer      Participant number / Banking-ID                  Current public Commerzbank
                        login identifier                                 login identifier: 10
                                                                         digits

  Teilnehmerkennung\*   Internal participant `TNVEKENN`                  ERD shows 16; relation to
                        identifier                                       10-digit Teilnehmernummer
                                                                         unresolved

  Zugriff               Access               opt-in / opt-out            Online participant access
                                                                         to
                                                                         Kundenverbindung/product

  Inhaber               Owner / account      owner role                  Business role on an
                        holder                                           agreement

  Bevollmächtigter      Authorized           proxy / authorized person   Authority without
                        representative                                   necessarily being owner

  gesetzlicher          Legal representative representative              Legal representation role
  Vertreter                                                              

  Produkt               Product              account, depot, etc.        Product underneath a
                                                                         Kundenverbindung

  Konto                 Account              account                     Banking account

  Depot                 Securities/custody   securities depot            Holds securities
                        account                                          

  Kontonummer           Account number       account number              Account identifier

  Depotnummer           Depot number         securities-account          Depot identifier
                                             identifier                  

  technische            Technical product    technical product no.       ERD shows length 12
  Produktnummer\*       number                                           

  IBAN                  International Bank   IBAN                        Payment-account identifier
                        Account Number                                   
  -------------------------------------------------------------------------------------------------

``` mermaid
flowchart LR
    K["Kundennummer / KDNR<br/>10 digits"]
    C1["customerId"]
    C2["customerNumber"]
    C3["internalCustomerNumber"]
    C4["AgreementID"]
    A["Kundenverbindung / CustomerAgreement"]

    C1 --> K
    C2 --> K
    C3 --> K
    C4 --> K
    K -->|"identifies"| A
```

## 2. Core Identity Model

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

## 3. Person and BPKENN

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

## 4. Party-Group and PartyId

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

## 5. Kundenverbindung and Kundennummer

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

## 6. Long-Term Customer Number

`longTermCustomerNumber` / `longTermCustomerId` is different from the
10-digit KDNR.

An internal example supplied during analysis was alphanumeric rather
than a 10-digit number.

The technical term encountered was:

``` text
VEKNKDNR
```

Current understanding:

  ----------------------------------------------------------------------------
  Identifier                            Same as KDNR? Format
  -------------------------- ------------------------ ------------------------
  `customerId`                                    Yes 10-digit numeric

  `customerNumber`                                Yes 10-digit numeric

  `internalCustomerNumber`                        Yes 10-digit numeric

  `longTermCustomerId`                             No Different/alphanumeric

  `VEKNKDNR`                          Associated with Different/alphanumeric
                                   long-term customer 
                                           identifier 
  ----------------------------------------------------------------------------

The precise semantics and lifecycle of `VEKNKDNR` should be verified
against the owning internal system.

## 7. Party--Kundenverbindung Relationship

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

## 8. Roles and Ownership

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

## 9. Online Teilnehmer and Teilnehmernummer

The **Teilnehmer** belongs to the online-banking/authentication layer.
It must be separated from Person/Party identity and from the
Kundenverbindung.

### Customer-facing Teilnehmernummer

Current public Commerzbank information describes the **Teilnehmernummer
as a 10-digit Digital Banking login identifier**. It is separate from
the account number and from the Kundennummer/KDNR.

The conceptual distinction is:

-   **Teilnehmernummer:** Who is logging in?
-   **KDNR / Kundennummer / AgreementID:** Which Kundenverbindung is
    being operated on?
-   **BPKENN / Party identity:** Which person/party exists in the bank's
    identity model?
-   **Product identifier:** Which concrete account/depot/product?

A KDNR is not a unique login identity because one Kundenverbindung can
involve multiple persons with different roles.

``` mermaid
flowchart LR
    L["Login<br/>Teilnehmernummer"]
    T["Authenticated Teilnehmer"]
    A["Accessible Kundenverbindungen"]
    K1["KDNR A"]
    K2["KDNR B"]
    S["Select AgreementID / KDNR"]
    D["Open new product<br/>e.g. Depot"]

    L --> T --> A
    A --> K1
    A --> K2
    K1 --> S
    K2 --> S
    S --> D
```

This explains a product-opening flow: authenticate first, determine
accessible Kundenverbindungen, select the target KDNR, then add the new
product under that agreement.

### `TNVEKENN (16)` vs. Teilnehmernummer (10) \*

The supplied internal ERD says `Teilnehmer (online) → TNVEKENN (16)`,
while current public Commerzbank information says the customer-facing
Teilnehmernummer is **10 digits**.

  ------------------------------------------------------------------------
  Identifier                         Observed length Context
  --------------------- ---------------------------- ---------------------
  Teilnehmernummer                         10 digits Current public
                                                     Commerzbank Digital
                                                     Banking/login

  `TNVEKENN`                                      16 Supplied internal ERD
  ------------------------------------------------------------------------

**Open question \***: the exact relationship is not proven. Possible
explanations are:

1.  `TNVEKENN` is an internal 16-character identifier while
    Teilnehmernummer is a separate 10-digit login identifier.
2.  `TNVEKENN` reflects an older/legacy representation.
3.  Another internal mapping exists between the two.

The first explanation currently fits the domain separation best, but it
is still a working hypothesis.

### Authentication vs. authorization vs. business role

``` mermaid
flowchart LR
    T["Teilnehmer<br/>authentication"]
    Z["Zugriff<br/>authorization"]
    K["Kundenverbindung<br/>KDNR"]
    R["Beteiligung / Rolle<br/>Inhaber, Bevollmächtigter, ..."]
    P["Person / Party"]

    T --> Z --> K
    P --> R --> K
```

-   **Authentication:** Who logged in?
-   **Authorization/Zugriff:** Which agreements/products may the
    participant access?
-   **Business role:** What is the person's role on the
    Kundenverbindung?

## 10. Products Under a Kundenverbindung

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

## 11. Account and Product Identifiers

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

## 12. IBAN and Check Digits

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

## 13. Java Domain Model

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

## 14. Common Lookup Flows

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

## 15. Identifier Cheat Sheet

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

## 16. Open Questions and Uncertain Points

An asterisk `*` marks information that is plausible or observed in one
source/model but is not yet sufficiently verified to be treated as a
stable business rule.

### Q1. `TNVEKENN (16)` vs. 10-digit Teilnehmernummer \*

**Known:** the internal ERD shows `TNVEKENN (16)` for the online
Teilnehmer; current public Commerzbank information describes the Digital
Banking Teilnehmernummer as 10 digits; and the login identity is
conceptually different from KDNR/Kundennummer.

**Unknown:** whether both identifiers coexist for the same Teilnehmer,
whether the 16-character form is legacy, and whether a deterministic
mapping exists.

**Working hypothesis:** `TNVEKENN` is an internal Teilnehmer identifier
and the 10-digit Teilnehmernummer is the customer-facing login
identifier. Not confirmed.

### Q2. Exact `partyId` ↔ `BPKENN` / `PGBPKENN` mapping \*

The ERD distinguishes Person → `BPKENN` and Party-Group → `PGBPKENN`.
Internal information also described `PartyId` as the BPKENN of a
*Gemeinschaft*. Verify the exact API mapping before assuming either
`partyId == BPKENN(Person)` or `partyId == PGBPKENN(Party-Group)`.

### Q3. Exact meaning of `VEKNKDNR` / long-term customer identifier \*

`longTermCustomerId` / `longTermCustomerNumber` differs from the
10-digit KDNR and can be alphanumeric. Its source system, lifecycle,
business purpose, and mapping to KDNR remain open.

### Q4. Meaning of owner-role codes `EI`, `MI`, and `GF` \*

The application treats all three as owner roles:

``` java
OWNER_ROLES = {"EI", "MI", "GF"}
```

Their exact German business expansions and semantics should be confirmed
from role master data.

### Q5. Party → Kundenverbindung minimum cardinality \*

For the discussed flow, a PartyId is understood to have at least one
Kundennummer/AgreementID, and each Kundennummer can have multiple
products. It remains open whether this is a universal master-data rule
or only guaranteed in the current application/domain.

### Q6. Technical product number format \*

The ERD shows a technical product number of length 12. Its exact
composition, whether it is strictly numeric, and how it maps to
Kontonummer/Depotnummer remain to be verified.

> \[!IMPORTANT\] When an open question is resolved, remove its `*`
> marker from the relevant sections and move the confirmed rule into the
> main terminology/identity tables. Do not silently convert a working
> hypothesis into a business rule.
