# COBA Technical Patterns — Locale, Exception Handling & CORE API Comsidl

## Source

Screenshot of a chat conversation (Friday 09:07) with Tobias Koltsch (extern).

---

## Locale handling

Use `ApplicationContextProvider.getLocale()` for the Locale. The language is only needed when creating an address salutation (e.g., "Frau" vs. "Mrs."), so it's not critical here — but using the real Locale is still better.

> Original: _"Nimm als 'Locale' besser diesen hier: ApplicationContextProvider.getLocale() Die Sprache wird nur benötigt wenn die Anrede erstellt wird (z.B. 'Frau' vs. 'Mrs.'). Die ist also hier nicht so wichtig. Es ist aber dennoch besser wenn das echte 'Locale' verwendet wird."_

---

## Exception handling pattern

If there is no general error handling later that catches `IllegalStateException`, use this pattern instead:

```java
orElseThrow(() -> BusinessExceptionCollector.createAndLogCancellingException())
```

> Original: _"Gibt es später noch ein allgemeines Fehlerhandling, welches die IllegalStateException wieder fängt? Falls nicht dann nimm hier besser folgende Exception: orElseThrow(() -> BusinessExceptionCollector.createAndLogCancellingException()_"

---

## CORE API — Comsidl requirements

### personMnC → /natural-persons (NaturalPersonApiClientV3)

The `personMnC` calls the CORE API `/natural-persons` (`NaturalPersonApiClientV3`). This API **does not actually require a Comsidl**.

However, other CORE APIs **do** require Comsidl — for example `/customer-agreements` (`CustomerAgreementApiClientV3`).

### AbstractCOREKBApiRequest

The Request object being created is the same for all CORE calls (`AbstractCOREKBApiRequest`), and it **does need a Comsidl**. If you leave Comsidl empty, the `/natural-persons` API will still work.

But it's better to set the Comsidl so the data is complete. The code location you selected is exactly right.

### Online channels vs. other channels

- **Online channels:** No Comsidl in context — a special technical user for CORE is used instead.
- **Other channels:** The Comsidl can simply be read from the context.

> Original: _"Aber setze die Comsidl besser, dann sind die Daten vollständig. Die Code-Stelle die du rausgesucht hast ist genau die richtige. In den Online-Kanälen gibt es keine Comsidl im Context und wir nehmen einen speziellen technischen Nutzer für CORE. In den anderen Kanälen kann die Comsidl einfach aus dem Conext gelesen werden."_

---

## Summary

| Topic | Guidance |
|-------|----------|
| **Locale** | Use `ApplicationContextProvider.getLocale()` — real Locale is preferred even if not critical |
| **Exception handling** | Prefer `BusinessExceptionCollector.createAndLogCancellingException()` over `IllegalStateException` unless a general handler catches it later |
| **CORE API Comsidl** | `/natural-persons` works without it, but other APIs (e.g. `/customer-agreements`) require it; set it for complete data |
| **Online channels** | No Comsidl in context — special technical user for CORE is used |
| **Other channels** | Read Comsidl from the context |
