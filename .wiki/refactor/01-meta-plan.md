# 01 — Meta-plan (scope: `Dev/`)

Three units. Registered before any sub-plan is written.

| Order | Unit | Kind | Artifact |
|---|---|---|---|
| 1 | `dev-old-layout` | territorial | `02-plan-dev-old-layout.md` |
| 2 | `dev-grouped-layout` | territorial | `02-plan-dev-grouped-layout.md` |
| 3 | `dev-index` | cross-cutting | `02-plan-dev-index.md` |

## 1. `dev-old-layout`
- **Scope**: the 18 pre-refactor folders directly under `Dev/` — `Architect/`, `Dev tools/`, `JS/`,
  `Java/`, `Kotlin/`, `Microfrontend/`, `Monolithic decomposition/`, `Python/`, `React JS/`,
  `React-Native/`, `Read/`, `Skia-React-Native/`, `Spec/`, `TeamCity/`, `elastic stack/`,
  `openshift/`, `redux/`, `wk/`.
- **Findings owned**: F1, F2.
- **May not decide**: anything inside the grouped layout (unit 2 owns it); index wording (unit 3).
- **Depends on**: nothing. It is the unit that frees the ground.

## 2. `dev-grouped-layout`
- **Scope**: `Dev/architecture/`, `Dev/frontend/`, `Dev/infra/`, `Dev/languages/`, `Dev/practices/`.
- **Findings owned**: F5.
- **May not decide**: the fate of any old-layout file (unit 1); where unit 1's two orphans land —
  it only states whether a destination inside the grouped layout exists for them.
- **Depends on**: unit 1, for whether the two orphaned files arrive.

## 3. `dev-index`
- **Scope**: `Dev/index.md` and the `Dev/` entries in the root `index.md`. Finding type: index drift.
- **Findings owned**: F4.
- **May not decide**: any move, rename or trash. It records wherever units 1 and 2 leave things.
- **Depends on**: units 1 and 2.

## Out of scope, carried to the report as open decisions
- F3 — the third copy of the code-reading note at the vault root. Outside `Dev/`.
- F6 — tracked `.DS_Store` files. Already reported; the owner's call.
