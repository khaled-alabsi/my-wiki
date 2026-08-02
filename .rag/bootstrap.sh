#!/usr/bin/env bash
# bootstrap.sh — rebuild the machine-local half of this project's RAG index.
#
#
# Why this exists: the project lives in a file-sync container, so the heavy and fully
# rebuildable parts are kept outside it, at $STORE:
#
#     $STORE/venv     the Python environment
#     $STORE/cache    downloaded model weights
#     $STORE/db       the vector store
#     $STORE/state    manifest.sqlite, the resume record
#
# Those paths are recorded in .rag/config.toml as project.store and project.venv, and
# the toolkit reads them directly. There are NO symlinks pointing at them from inside
# the project — a sync container cannot sync a symlink and turns each one into an empty
# "name 2" folder that reappears no matter how often you delete it.
#
# db and state ALWAYS move together. A synced manifest describing a store that is
# not there makes `update` skip every file and report success on an empty index.
#
# Idempotent: existing pieces are left alone, missing ones are rebuilt.
#
#     bash .rag/bootstrap.sh
#     STORE=/some/other/path bash .rag/bootstrap.sh
#     PYTHON=/opt/homebrew/bin/python3.13 bash .rag/bootstrap.sh
#
# It does NOT build the index. That step is slow and downloads gigabytes of model
# weights, so it is printed at the end for you to run.

set -euo pipefail

RAG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$RAG_DIR/.." && pwd)"
STORE="${STORE:-/Users/Khaled.Alabsi/.local/share/rag/my-wiki}"

# Any CPython >= 3.11 works (the toolkit needs tomllib). Override with PYTHON=...
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for candidate in /opt/homebrew/bin/python3.13 python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$(command -v "$candidate")"; break; fi
  done
fi
if [ -z "$PYTHON" ]; then
  echo "error: no python3 found. Install CPython 3.11+, or set PYTHON=/path/to/python3" >&2
  exit 1
fi

echo "project $PROJECT"
echo "store   $STORE"
echo "python  $PYTHON ($("$PYTHON" -V 2>&1))"
echo

# --- 1. external store ------------------------------------------------------
# NO SYMLINKS ARE CREATED INSIDE THE PROJECT. A file-sync container cannot sync a
# symlink: iCloud Drive replaces each one with an empty directory called "cache 2",
# "db 2", ".venv 2", and they come back after every deletion. Nothing needs them —
# config.toml records the real locations and the launchers embed the resolved
# interpreter path. Clean up any that a previous version left behind.
mkdir -p "$STORE"
for name in cache db state venv; do
  mkdir -p "$STORE/$name"
done
echo "ok      store ready at $STORE"

removed=0
for stale in "$RAG_DIR/cache" "$RAG_DIR/db" "$RAG_DIR/state" "$RAG_DIR/.venv" "$PROJECT/.venv"; do
  if [ -L "$stale" ]; then rm -f "$stale"; removed=$((removed + 1)); fi
done
# ...and the empty conflict copies the sync client made from them.
find "$RAG_DIR" "$PROJECT" -maxdepth 1 -type d -name "* 2" -empty -print0 2>/dev/null \
  | xargs -0 -r rmdir 2>/dev/null || true
[ "$removed" -gt 0 ] && echo "removed $removed symlink(s) from inside the sync container"
echo

# --- 2. virtualenv ----------------------------------------------------------
VENV_PY="$STORE/venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
  echo "creating virtualenv…"
  rm -rf "$STORE/venv"
  "$PYTHON" -m venv "$STORE/venv"
else
  echo "ok      virtualenv already present ($("$VENV_PY" -V 2>&1))"
fi

echo "installing dependencies from requirements.txt…"
"$VENV_PY" -m pip install --upgrade pip --quiet
"$VENV_PY" -m pip install -r "$RAG_DIR/requirements.txt" --quiet
echo "ok      dependencies installed"

# --- 3. vendored toolkit on the venv path -----------------------------------
SITE_PACKAGES="$("$VENV_PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
printf '%s\n' "$RAG_DIR/toolkit" > "$SITE_PACKAGES/rag_toolkit.pth"

# macOS marks files under a dot-directory in a sync container UF_HIDDEN, and CPython
# 3.13+ SKIPS hidden .pth files — the file is then valid but never read, and every
# launcher call dies with ModuleNotFoundError. `mv` preserves the flag, so it can
# even survive a relocation. Clear it defensively.
command -v chflags >/dev/null 2>&1 && chflags nohidden "$SITE_PACKAGES/rag_toolkit.pth" 2>/dev/null || true
echo "ok      rag_toolkit.pth written to $SITE_PACKAGES"

# --- 4. launchers -----------------------------------------------------------
"$VENV_PY" - <<PY
import sys
from pathlib import Path
sys.path.insert(0, "$RAG_DIR/toolkit")
from rag_toolkit import install
for p in install.write_launchers(Path("$RAG_DIR")):
    print("ok      launcher", p.name)
PY

# --- 5. Jupyter kernel ------------------------------------------------------
# Without this the notebook falls back to whatever kernel the editor offers —
# usually a system python with no torch. rag_toolkit still imports there (it is
# pure Python), so the failure surfaces late and confusingly inside a search.
if "$VENV_PY" -c "import ipykernel" >/dev/null 2>&1; then
  "$VENV_PY" -m ipykernel install --user \
      --name my-wiki-rag --display-name "my-wiki RAG (.venv)" >/dev/null 2>&1 \
    && echo "ok      Jupyter kernel 'my-wiki RAG (.venv)' registered" \
    || echo "WARN    could not register the Jupyter kernel" >&2
else
  echo "note    ipykernel not installed — notebook kernel not registered"
fi

# --- 6. verify --------------------------------------------------------------
echo
echo "verifying…"
"$RAG_DIR/bin/rag" doctor || true

echo
echo "------------------------------------------------------------------------------"
if "$RAG_DIR/bin/rag" status 2>/dev/null | grep -qE '^indexed +[1-9]'; then
  echo "Environment is ready and the index is already populated — nothing else to do."
  echo
  echo "    .rag/bin/rag search \"your question\""
  echo "    .rag/bin/rag update              # after editing content"
else
  echo "Environment is ready. The index itself is NOT built yet."
  echo
  echo "Next, from the project root:"
  echo
  echo "    .rag/bin/rag doctor --models    # downloads the model weights, once"
  echo "    .rag/bin/rag index              # ~285s for 144 notes"
  echo "    .rag/bin/rag status             # confirm: files > 0 and chunks > 0"
  echo
  echo "Run those one at a time — never two index or model jobs at once."
fi
echo "------------------------------------------------------------------------------"
