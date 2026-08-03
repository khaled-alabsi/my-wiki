# Test Data Mocking — SEC Account, Owner & Depot Numbers

## Sources

- Screenshot of a chat conversation (Friday 11:05–11:12) with Tobias Koltsch (extern).
- Screenshot of a chat conversation (19.03.) with Kazim Güvenc (extern).

---

## How to mock technical SEC account number and owner number for a test user

### OwnerGroupId

In the investor profile at `/wpfe/reg/wphgoverview?pk` you can find the **owner BPKenns** of all communities. Use one of those as `OwnerGroupId`.

> Original: _"Im Anlegerprofil `/wpfe/reg/wphgoverview?pk` findest du die Inhaber-BPKenns aller Gemeinschaften. Nimm einfach eine von denen als OwnerGroupId."_

### Depot number construction

Based on the customer numbers (Kundennummern) listed under that profile, you can build your own depot number by appending two digits to the customer number.

**Example:**
- Customer number: `7073201118`
- Possible depot numbers: `707320111804`, `707320111805`, `707320111806`, etc.

> Original: _"Anhand der Kundennummern die darunter stehen, kannst du dir selber eine Depotnummer bauen. Also zum Beispiel ist die Kundennummer '7073201118' dann wären dies mögliche Depotnummern: 707320111804, 707320111805, 707320111806 usw. Also einfach zwei Zahlen hinten anhängen."_

---

## Customer numbers and person roles in COBA

### Owner (EI) vs. Authorized Representative (VB)

When two people share the same customer number (Kundennummer):
- **Top entry = EI (Eigentümer)** — the owner of that customer number.
- **Bottom entry = VB (Bevollmächtigter)** — the authorized representative for that customer number.

**Example:** Helene is Hedwig's friend. The customer number belongs to Hedwig (owner = EI), but Helene has power of attorney (VB) and can also view and modify it.

> Original: _"Der obere ist (EI) = Eigentümer, der untere ist (VB) = Bevollmächtigter für diese Kundennummer. z.B. Helene ist Freundin von Hedwig. Und diese Kundennummer ist von Hedwig (Eigentümer=EI) aber Helene hat Vollmacht für diese Kundennummer und kann auch sehen und ändern"_

### Person identification — which number is unique to one person?

There is **no single number that maps 1:1 to a person** in COBA, except:
- **BPkenn / PartyID**

However, BPkenn is tenant-specific. A person has one BPkenn in Germany but could have a different BPkenn in France.

There is also **GPKENN (Global Kennung)** which is safe for uniquely identifying one person, but it's more complicated to work with.

> Original: _"Das gibt es nicht. Also außer bpkkenn/partyid. Aber auch diese ist pro Tenant anders. Also ein Mensch hat eine bpkkenn in Deutschland. Aber könnte noch eine Bpkenn in frankreich haben. Dann gibtes aber noch GPKENN (global kennung) diese ist nur für einen Menschen safe aber das ist kompliziert bissichen"_

---

## Summary

| Field / Concept | How to obtain / construct |
|-----------------|--------------------------|
| `OwnerGroupId` | Pick a BPKenn from `/wpfe/reg/wphgoverview?pk` (investor profile) |
| Depot number | Take a Kundennummer and append two digits of your choice |
| Owner vs. VB (same Kundennummer) | Top entry = EI (Eigentümer/owner); bottom entry = VB (Bevollmächtigter/authorized representative) |
| Unique person identifier | BPkenn / PartyID — but tenant-specific; GPKENN is globally unique but more complicated |
