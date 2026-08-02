#!/usr/bin/env bash
# bootstrap.sh — rebuild the machine-local half of this vault's RAG index.
#
# The vault syncs through iCloud, but the heavy parts are deliberately NOT in it:
# they are large, machine-specific, and fully rebuildable. They live outside the
# iCloud container and are reached through symlinks.
#
#     <vault>/.venv -> $STORE/venv    the Python environment   (~1.5 GB)
#     .rag/cache    -> $STORE/cache   downloaded model weights (~6.4 GB)
#     .rag/db       -> $STORE/db      the LanceDB vector store
#     .rag/state    -> $STORE/state   manifest.sqlite, the resume record
#
# The virtualenv lives at the VAULT ROOT (<vault>/.venv), not inside .rag/, so
# editors pick it up as the project interpreter. The launchers know this.
#
# Run this on a new machine, or any time those symlinks are broken. It is
# idempotent: existing pieces are left alone, missing ones are rebuilt.
#
#     bash .rag/bootstrap.sh                 # default store location
#     STORE=/some/other/path bash .rag/bootstrap.sh
#     PYTHON=/opt/homebrew/bin/python3.13 bash .rag/bootstrap.sh
#
# It does NOT build the index — that is the last step and it is printed at the end,
# because it takes minutes and downloads several GB of model weights on first run.

set -euo pipefail

RAG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="$(cd "$RAG_DIR/.." && pwd)"
STORE="${STORE:-$HOME/.local/share/rag/my-wiki}"

# Any CPython >= 3.11 works (the toolkit needs tomllib). 3.13 is what this was built
# with; 3.14 was avoided as a base for the torch stack. Override with PYTHON=...
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$(command -v "$candidate")"; break; fi
  done
fi
if [ -z "$PYTHON" ]; then
  echo "error: no python3 found. Install CPython 3.11+, or set PYTHON=/path/to/python3" >&2
  exit 1
fi

echo "vault   $VAULT"
echo "store   $STORE"
echo "python  $PYTHON ($("$PYTHON" -V 2>&1))"
echo

# --- 1. the external store and its symlinks ---------------------------------
mkdir -p "$STORE"

# cache / db / state hang off .rag/
for name in cache db state; do
  mkdir -p "$STORE/$name"
  target="$RAG_DIR/$name"
  if [ -L "$target" ]; then
    echo "ok      .rag/$name -> $(readlink "$target")"
  elif [ -e "$target" ]; then
    echo "WARN    .rag/$name exists and is not a symlink — leaving it alone" >&2
  else
    ln -s "$STORE/$name" "$target"
    echo "linked  .rag/$name -> $STORE/$name"
  fi
done

# the venv hangs off the VAULT ROOT
mkdir -p "$STORE/venv"
if [ -e "$VAULT/.venv" ] && [ ! -L "$VAULT/.venv" ]; then
  echo "WARN    <vault>/.venv exists and is not a symlink — leaving it alone" >&2
else
  ln -sfn "$STORE/venv" "$VAULT/.venv"
  echo "linked  <vault>/.venv -> $STORE/venv"
fi

# a stale .rag/.venv from an older layout would shadow nothing, but it confuses
if [ -L "$RAG_DIR/.venv" ]; then
  rm -f "$RAG_DIR/.venv"
  echo "removed .rag/.venv (superseded by <vault>/.venv)"
fi
echo

# --- 2. the virtualenv ------------------------------------------------------
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

# --- 3. put the vendored toolkit on the venv's path -------------------------
SITE_PACKAGES="$("$VENV_PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
printf '%s\n' "$RAG_DIR/toolkit" > "$SITE_PACKAGES/rag_toolkit.pth"

# macOS marks files under a dot-directory in an iCloud container UF_HIDDEN, and
# CPython 3.13+ SKIPS hidden .pth files — the file is then valid but never read,
# and every launcher call dies with ModuleNotFoundError. Clear it defensively;
# `mv` preserves the flag, so it can even survive a relocation.
if command -v chflags >/dev/null 2>&1; then
  chflags nohidden "$SITE_PACKAGES/rag_toolkit.pth" 2>/dev/null || true
fi
echo "ok      rag_toolkit.pth written to $SITE_PACKAGES"

# --- 4. launchers -----------------------------------------------------------
# Written here rather than by install.py, because the stock toolkit expects the
# venv at .rag/.venv and this workspace keeps it at the vault root instead.
mkdir -p "$RAG_DIR/bin"
cat > "$RAG_DIR/bin/rag" <<'LAUNCHER'
#!/usr/bin/env bash
# Launcher: runs the toolkit with the project-root venv (<vault>/.venv).
# The venv itself lives outside iCloud; <vault>/.venv is a symlink to it.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> <vault>/.rag
root="$(cd "$here/.." && pwd)"                            # -> <vault>
# PYTHONPATH rather than trusting rag_toolkit.pth: on macOS a .rag inside an iCloud
# container is flagged UF_HIDDEN, and CPython 3.13+ skips hidden .pth files.
export PYTHONPATH="$here/toolkit${PYTHONPATH:+:$PYTHONPATH}"
exec "$root/.venv/bin/python" -m rag_toolkit.cli --rag-dir "$here" "$@"
LAUNCHER
chmod 755 "$RAG_DIR/bin/rag"

cat > "$RAG_DIR/bin/rag.cmd" <<'LAUNCHER'
@echo off
setlocal
set "HERE=%~dp0.."
set "ROOT=%HERE%\.."
set "PYTHONPATH=%HERE%\toolkit;%PYTHONPATH%"
"%ROOT%\.venv\Scripts\python.exe" -m rag_toolkit.cli --rag-dir "%HERE%" %*
LAUNCHER
echo "ok      launchers written to .rag/bin/"

# --- 4b. Jupyter kernel -----------------------------------------------------
# Without this the notebook falls back to whatever kernel the editor offers —
# usually a system python with no torch — and fails on `import
# sentence_transformers` deep inside a call rather than at startup.
if "$VENV_PY" -c "import ipykernel" >/dev/null 2>&1; then
  "$VENV_PY" -m ipykernel install --user \
      --name my-wiki-rag --display-name "my-wiki RAG (.venv)" >/dev/null 2>&1 \
    && echo "ok      Jupyter kernel 'my-wiki RAG (.venv)' registered" \
    || echo "WARN    could not register the Jupyter kernel" >&2
else
  echo "note    ipykernel not installed — notebook kernel not registered"
fi

# --- 5. verify --------------------------------------------------------------
echo
echo "verifying…"
"$RAG_DIR/bin/rag" doctor || true

echo
echo "------------------------------------------------------------------------------"
if "$RAG_DIR/bin/rag" status 2>/dev/null | grep -qE '^indexed +[1-9]'; then
  echo "Environment is ready and the index is already populated — nothing else to do."
  echo
  echo "    .rag/bin/rag search \"your question\""
  echo "    .rag/bin/rag update              # after editing notes"
else
  echo "Environment is ready. The index itself is NOT built yet."
  echo
  echo "Next, from the vault root:"
  echo
  echo "    .rag/bin/rag doctor --models    # downloads ~6.4 GB of model weights, once"
  echo "    .rag/bin/rag index              # builds the index (~285s for 144 notes)"
  echo "    .rag/bin/rag status             # confirm: files > 0 and chunks > 0"
  echo
  echo "Run those one at a time — never two index or model jobs at once."
fi
echo "------------------------------------------------------------------------------"
