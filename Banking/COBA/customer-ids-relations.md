**one Kundennummer (`KDNR`) identifies exactly one `Kundenverbindung` (customer agreement/relationship).**

So:

```text
Kundenverbindung / Agreement
          │
          └── KDNR = Kundennummer (10 digits)
```

Multiple persons can participate in that same Kundenverbindung with different roles:

```text
             KDNR 5004002275
             Kundenverbindung
                    │
       ┌────────────┼────────────┐
       │            │            │
    Person A     Person B     Person C
    Inhaber      Inhaber      Bevollm.
```

And that Kundenverbindung can contain multiple products:

```text
KDNR 5004002275
      │
      ├── Girokonto
      ├── Depot
      └── Verrechnungskonto
```

Therefore:

**1 KDNR → 1 Kundenverbindung → potentially multiple persons + multiple products.**

A person, on the other hand, can participate in multiple Kundenverbindungen and therefore be associated with multiple KDNRs.


Eine PartyId hat am Ende mindestens eine Kundennummer (AgreementID) und unter der Kundennummer kann es viele Produkte geben. 