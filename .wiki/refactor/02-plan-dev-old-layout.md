# 02 — `dev-old-layout`

Owns F1 and F2. 18 folders, 84 files.

## Read for this plan
All 18 folders compared file-by-file against the grouped layout by content hash; the 6 divergent
filename pairs opened; `Dev/Dev tools/Vs code configs.md` and `Dev/Read/Untitled.md` read in full.

## Operations

### OP-1 — Trash 16 folders whose every file is byte-identical to a grouped counterpart
Each moves whole to `.wiki/.trash/<original path>`.

`Dev/Architect/` · `Dev/JS/` · `Dev/Java/` · `Dev/Kotlin/` · `Dev/Microfrontend/` ·
`Dev/Monolithic decomposition/` · `Dev/Python/` · `Dev/React JS/` · `Dev/React-Native/` ·
`Dev/Skia-React-Native/` · `Dev/Spec/` · `Dev/TeamCity/` · `Dev/elastic stack/` · `Dev/openshift/` ·
`Dev/redux/` · `Dev/wk/`

Precondition, re-verified at execution time: for every file in the folder, an identical-hash file
exists under `Dev/architecture|frontend|infra|languages|practices/`. A folder failing the check is
skipped and reported, never trashed.

Not destroyed: the 6 pre-normalization filenames (`000 Techincal.md`, `filbeats.md`,
`docker_connetion.md`, `generte cert steps.md`, `needen cert.md`, `exmaple.md`), the extensionless
`013 Skia with react-native-gesture-handler and react-native-reanimated`, and the second copies of
`key.txt`, the Python scratch files, the TeamCity images and the `Pasted image 20260513110430.jpg`.
All go to trash with their folder and are restorable.

### OP-2 — `Dev/Dev tools/Vs code configs.md` → move out, then trash the empty folder
**Open decision D1.** Recommended: move to `Quick note/VS Code macOS local network access.md` —
the profile routes macOS configuration to `Quick note/`, and one note does not earn a new
`Dev/tools/`. Alternative: `Dev/practices/` , or a new `Dev/tools/`.
Then trash `Dev/Dev tools/` (empty).

### OP-3 — `Dev/Read/Untitled.md`
**Open decision D2.** It is not a duplicate: 28 of its sentences are absent from
`Dev/practices/How to Read and Understand Code Quickly.md`.
Recommended: append those 28 lines verbatim to the shaped note under a new
`## Original capture — lines not carried over` section, verify the target holds them, then trash
`Dev/Read/`. Lossless, one note, reversible.
Alternatives: keep it as `Dev/practices/How to Read and Understand Code Quickly — capture.md`; or
trash it outright, accepting the loss.

## Result
`Dev/` keeps `architecture/ frontend/ infra/ languages/ practices/ LLM/ index.md` and nothing else.
