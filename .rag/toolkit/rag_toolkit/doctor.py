"""Diagnostics: find out why an index is missing, broken, or returning bad results.

Checks are ordered so the first failure is usually the root cause. Each one reports a
status, what was actually observed, and the concrete command that fixes it. Nothing here
guesses: a check that cannot run says so rather than reporting a pass.

``--models`` and ``--extract`` are opt-in because they are the expensive checks —
``--models`` downloads and loads real models.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import __version__
from . import config as config_mod
from . import detect, discover, extract

OK, WARN, FAIL, SKIP = "ok", "warn", "fail", "skip"

OPTIONAL_PACKAGES = {
    "lancedb": "core store — without it the numpy fallback is used",
    "pathspec": "correct .gitignore/.ragignore matching",
    "numpy": "required by both stores",
    "fastembed": "ONNX embedding backend",
    "sentence_transformers": "torch embedding backend and cross-encoder reranking",
    "pymupdf": "PDF extraction",
    "docx": "Word extraction",
    "pptx": "PowerPoint extraction",
    "openpyxl": "Excel extraction",
    "selectolax": "clean HTML and EPUB extraction",
    "mcp": "MCP server (rag serve --mcp)",
    "watchdog": "file watching (rag watch)",
}


class Report:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(self, name: str, status: str, detail: str, fix: str = "") -> None:
        self.checks.append({"check": name, "status": status, "detail": detail, "fix": fix})

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c["status"] == FAIL)

    @property
    def warned(self) -> int:
        return sum(1 for c in self.checks if c["status"] == WARN)

    def as_dict(self) -> dict[str, Any]:
        return {"checks": self.checks, "failed": self.failed, "warned": self.warned}

    def lines(self) -> list[str]:
        marks = {OK: "ok  ", WARN: "warn", FAIL: "FAIL", SKIP: "skip"}
        out: list[str] = []
        for check in self.checks:
            out.append(f"[{marks[check['status']]}] {check['check']}: {check['detail']}")
            if check["fix"] and check["status"] in {WARN, FAIL}:
                out.append(f"         fix: {check['fix']}")
        out.append("")
        out.append(f"{self.failed} failed, {self.warned} warnings, {len(self.checks)} checks")
        return out


def run_doctor(rag_dir: Path, args: argparse.Namespace) -> int:
    report = Report()
    # Load the config before deriving paths: project.store and project.venv relocate
    # db, state, cache and the venv, and every later check needs the real locations.
    try:
        preload = config_mod.load(rag_dir)
    except Exception:
        preload = {}
    paths = config_mod.layout(rag_dir, preload)

    _check_workspace(report, rag_dir, paths)
    cfg = _check_config(report, rag_dir, paths)
    _check_runtime(report)
    _check_import(report, rag_dir, paths)
    _check_packages(report, cfg, rag_dir)
    _check_sources(report, cfg, rag_dir)
    _check_store_roundtrip(report, cfg)
    _check_index(report, cfg, rag_dir, paths)

    if args.extract:
        _check_extraction(report, cfg, rag_dir, args.sample)
    else:
        report.add("extraction", SKIP, "not sampled", "run 'rag doctor --extract'")

    if args.models:
        _check_models(report, cfg, paths)
    else:
        report.add("models", SKIP, "not loaded (this downloads them)",
                   "run 'rag doctor --models' when you are ready to fetch them")

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, default=str))
    else:
        print("\n".join(report.lines()))
    return 1 if report.failed else 0


# --------------------------------------------------------------------------- checks


def _check_workspace(report: Report, rag_dir: Path, paths: dict[str, Path]) -> None:
    if not rag_dir.is_dir():
        report.add("workspace", FAIL, f"{rag_dir} does not exist", "run 'rag init'")
        return
    missing = [name for name in ("docs", "state", "db") if not paths[name].exists()]
    if missing:
        report.add("workspace", WARN, f"{rag_dir} exists, missing {', '.join(missing)}",
                   "run 'rag init --force' to rebuild the layout")
    else:
        report.add("workspace", OK, str(rag_dir))

    stored = paths["version"].read_text(encoding="utf-8").strip() if paths["version"].is_file() else ""
    if stored and stored != __version__:
        report.add("toolkit version", WARN,
                   f"vendored copy is {stored}, this code is {__version__}",
                   "re-vendor the toolkit from the skill, then run 'rag index --full' "
                   "if the chunking or model defaults changed")
    elif stored:
        report.add("toolkit version", OK, stored)


def _check_config(report: Report, rag_dir: Path, paths: dict[str, Path]) -> dict[str, Any]:
    try:
        cfg = config_mod.load(rag_dir)
    except FileNotFoundError:
        report.add("config", FAIL, f"no {paths['config']}", "run 'rag init'")
        return {}
    except Exception as exc:
        report.add("config", FAIL, f"{paths['config']} is not valid TOML: {exc}",
                   "fix the syntax, or delete it and run 'rag init'")
        return {}

    if not cfg.get("sources"):
        report.add("config", FAIL, "no sources configured", "run 'rag init PATH'")
    elif not cfg.get("embedding", {}).get("model"):
        report.add("config", FAIL, "embedding.model is empty", "run 'rag init --force'")
    else:
        report.add("config", OK,
                   f"{len(cfg['sources'])} source(s), model '{cfg['embedding']['model']}'")
    return cfg


def _check_runtime(report: Report) -> None:
    if sys.version_info < (3, 11):
        report.add("python", FAIL, f"{sys.version.split()[0]} at {sys.executable}",
                   "rebuild the venv with Python 3.11 or newer (tomllib is required)")
    else:
        report.add("python", OK, f"{sys.version.split()[0]} at {sys.executable}")

    host = detect.host()
    accel = host["accelerator"]
    detail = f"{host['os']}/{host['arch']}, {host['ram_gb']} GB RAM, device '{accel['device']}'"
    if accel["device"] != "cpu" and not accel["confirmed_by_torch"]:
        report.add("hardware", WARN, detail + " (not confirmed — torch is not importable here)",
                   "install the 'torch' extra, or set embedding.device = 'cpu'")
    else:
        report.add("hardware", OK, detail)


def _check_import(report: Report, rag_dir: Path, paths: dict[str, Path]) -> None:
    """Can the venv interpreter import ``rag_toolkit`` on its own?

    Every other check can pass while the answer is no. The launchers export
    ``PYTHONPATH``, so they work regardless; anything else — a notebook kernel, a
    plain ``python -c``, an MCP host — depends on ``rag_toolkit.pth`` being read.

    On macOS a ``.rag`` inside a file-sync container gets ``UF_HIDDEN`` on its files,
    and CPython 3.13+ skips hidden ``.pth`` files. The file is then byte-correct and
    never read. That is reported explicitly here, because nothing about the symptom
    points at it.
    """
    python = paths["venv"] / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        report.add("import", SKIP, f"no interpreter at {python}", "run install.py")
        return

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    try:
        proc = subprocess.run(
            [str(python), "-c", "import rag_toolkit; print(rag_toolkit.__version__)"],
            capture_output=True, text=True, timeout=60, env=env,
        )
    except Exception as exc:
        report.add("import", WARN, f"could not run the venv interpreter: {exc}", "")
        return

    if proc.returncode == 0:
        report.add("import", OK, f"'import rag_toolkit' works without PYTHONPATH "
                                 f"(version {proc.stdout.strip()})")
        return

    hint = "re-run install.py to rewrite rag_toolkit.pth"
    pth = next(iter(paths["venv"].glob("lib/python*/site-packages/rag_toolkit.pth")), None) \
        or next(iter(paths["venv"].glob("Lib/site-packages/rag_toolkit.pth")), None)
    detail = "the venv cannot import rag_toolkit without PYTHONPATH"
    if pth is None:
        detail += " — rag_toolkit.pth is missing"
    elif hasattr(os, "chflags"):
        try:
            if os.lstat(pth).st_flags & stat.UF_HIDDEN:
                detail += f" — {pth.name} is flagged UF_HIDDEN, and CPython 3.13+ skips hidden .pth files"
                hint = f"chflags nohidden '{pth}'"
        except OSError:
            pass
    report.add("import", WARN, detail, hint)


def _check_packages(report: Report, cfg: dict[str, Any], rag_dir: Path) -> None:
    needed = {
        cfg.get("embedding", {}).get("backend", ""): "the configured embedding backend",
        cfg.get("retrieval", {}).get("rerank_backend", ""): "the configured reranker",
        cfg.get("store", {}).get("kind", ""): "the configured store",
    }
    aliases = {"sentence-transformers": "sentence_transformers", "fastembed": "fastembed",
               "lancedb": "lancedb", "numpy": "numpy"}
    required = {aliases[k] for k in needed if k in aliases}

    present, absent = [], []
    for module, why in OPTIONAL_PACKAGES.items():
        try:
            importlib.import_module(module)
            present.append(module)
        except Exception:
            absent.append((module, why))

    for module, why in absent:
        if module in required:
            report.add(f"package {module}", FAIL, f"missing — {why}",
                       "re-run install.py, or change the backend in config.toml")

    # Split "missing and this corpus needs it" from "missing and irrelevant here".
    # Listing every extractor as `optional missing` reads as a deficiency even when
    # the corpus has no PDF, Office or HTML file for any of them to open.
    extractor_modules = {"pymupdf": "documents", "docx": "documents", "pptx": "documents",
                         "openpyxl": "documents", "selectolax": "web"}
    try:
        wanted_extras = extract.extras_for_extensions(discover.plan(cfg, rag_dir)["by_extension"])
    except Exception:
        wanted_extras = {"documents", "web"}  # cannot tell; assume they matter

    absent_modules = [m for m, _ in absent if m not in required]
    relevant = [m for m in absent_modules
                if extractor_modules.get(m, "core") in wanted_extras or m not in extractor_modules]
    irrelevant = [m for m in absent_modules if m not in relevant]

    parts = [f"{len(present)} present"]
    if relevant:
        parts.append(f"missing: {', '.join(relevant)}")
    if irrelevant:
        parts.append(f"not needed for this corpus: {', '.join(irrelevant)}")
    report.add("packages",
               OK if not [m for m, _ in absent if m in required] else WARN,
               ", ".join(parts),
               "install.py --extras documents,web,mcp,watch,notebook adds the optional ones")


def _check_sources(report: Report, cfg: dict[str, Any], rag_dir: Path) -> None:
    if not cfg.get("sources"):
        return
    for source in cfg["sources"]:
        path = Path(source.get("path", ""))
        if not path.is_dir():
            report.add(f"source '{source.get('name')}'", FAIL, f"{path} is not a directory",
                       "fix the path in config.toml, or re-run 'rag init'")
    try:
        result = discover.plan(cfg, rag_dir)
    except Exception as exc:
        report.add("discovery", FAIL, f"{type(exc).__name__}: {exc}")
        return
    if result["files"] == 0:
        top = ", ".join(f"{k} ({v})" for k, v in list(result["skipped"].items())[:3])
        report.add("discovery", FAIL, f"0 indexable files. Top skip reasons: {top or 'none'}",
                   "loosen .ragignore, raise corpus.max_file_mb, or check the source path")
    else:
        report.add("discovery", OK,
                   f"{result['files']} indexable files, ~{result['estimated_chunks']} chunks")


def _check_store_roundtrip(report: Report, cfg: dict[str, Any]) -> None:
    """Exercise the configured store in a scratch directory before a long run depends on it.

    This is the check that catches a vector-store API mismatch in two seconds instead of
    two hours into an index run: create, upsert, vector search, full-text search, delete.
    """
    import tempfile

    from . import store as store_mod

    kind = cfg.get("store", {}).get("kind", "lancedb")
    probe = dict(cfg)
    probe["store"] = {"kind": kind, "table": "doctor_probe"}

    with tempfile.TemporaryDirectory(prefix="rag-doctor-") as tmp:
        try:
            store = store_mod.build(probe, Path(tmp), dimension=4, create=True)
        except Exception as exc:
            report.add("store", FAIL, f"cannot open a '{kind}' store: {type(exc).__name__}: {exc}",
                       "install the missing package, or set store.kind = 'numpy' in config.toml")
            return

        if store.kind != kind:
            report.add("store", WARN,
                       f"config asks for '{kind}' but '{store.kind}' is in use "
                       f"(the package is not importable)",
                       "install lancedb, or set store.kind = 'numpy' to make the fallback explicit")

        try:
            rows = [
                store_mod.Record(chunk_id="probe-a", path="/probe/a.md", rel_path="a.md",
                                 source="probe", title="A", ordinal=0,
                                 text="alpha bravo charlie", ext=".md",
                                 vector=[1.0, 0.0, 0.0, 0.0]),
                store_mod.Record(chunk_id="probe-b", path="/probe/b.md", rel_path="b.md",
                                 source="probe", title="B", ordinal=0,
                                 text="delta echo foxtrot", ext=".md",
                                 vector=[0.0, 1.0, 0.0, 0.0]),
            ]
            store.upsert(rows)
            hits = store.search_vector([1.0, 0.0, 0.0, 0.0], k=2)
            if not hits or hits[0].record.chunk_id != "probe-a":
                report.add("store", FAIL,
                           f"'{store.kind}' returned the wrong nearest neighbour for a probe vector",
                           "set store.kind = 'numpy' and re-run 'rag index --full'")
                return

            fts = getattr(store, "ensure_fts", None)
            fts_built = bool(fts()) if callable(fts) else False
            text_hits = store.search_text("bravo", k=2) if fts_built else []

            store.delete(["probe-a"])
            remaining = store.count()
            store.close()
        except Exception as exc:
            report.add("store", FAIL,
                       f"'{store.kind}' round-trip failed: {type(exc).__name__}: {exc}",
                       "this is usually a version mismatch — reinstall, or set store.kind = 'numpy'")
            return

    detail = f"'{store.kind}' round-trip ok (upsert, search, delete; {remaining} row left)"
    if store.kind == "lancedb" and not fts_built:
        # Report the real exception. Saying only "check the lancedb version" once meant
        # the actual cause — "Native FTS indexes can only be created on a single field
        # at a time" — had to be reproduced by hand before it could be fixed.
        why = getattr(store, "last_fts_error", "") or "no reason reported by the store"
        report.add("store", WARN, detail + f", but the full-text index could not be built: {why}",
                   "hybrid search will be dense-only until this is fixed")
    elif store.kind == "lancedb" and not text_hits:
        report.add("store", WARN, detail + ", but full-text search returned nothing for a known term",
                   "hybrid search may be degraded; check the lancedb version")
    else:
        report.add("store", OK, detail)


def _check_index(report: Report, cfg: dict[str, Any], rag_dir: Path, paths: dict[str, Path]) -> None:
    if not paths["manifest"].is_file():
        report.add("index", WARN, "nothing indexed yet", "run 'rag index'")
        return
    from .manifest import Manifest

    with Manifest(paths["manifest"]) as manifest:
        stats = manifest.stats()
        built_with = manifest.get_meta("embedding") or {}
        store_meta = manifest.get_meta("store") or {}

    if not stats["chunks"]:
        report.add("index", FAIL, "manifest exists but holds 0 chunks",
                   "run 'rag index --full'")
        return
    report.add("index", OK, f"{stats['files']} files, {stats['chunks']} chunks "
                            f"({store_meta.get('kind', '?')} store)")

    configured = cfg.get("embedding", {}).get("model", "")
    if built_with.get("model") and configured and built_with["model"] != configured:
        report.add("model drift", FAIL,
                   f"index built with '{built_with['model']}', config says '{configured}'",
                   "run 'rag index --full' to rebuild, or restore the old model in config.toml")
    elif built_with.get("model"):
        report.add("model drift", OK, f"index and config agree on '{configured}'")

    failed = stats["by_status"].get("failed", 0)
    empty = stats["by_status"].get("empty", 0)
    if failed:
        report.add("extraction failures", WARN, f"{failed} files failed to extract",
                   "run 'rag doctor --extract' to see why")
    if empty and stats["files"] and empty / stats["files"] > 0.25:
        report.add("empty documents", WARN,
                   f"{empty} of {stats['files']} files produced no text",
                   "if these are scanned PDFs, set corpus.ocr = true and install the 'ocr' extra")

    lock = paths["lock"]
    if lock.is_file():
        report.add("lock", WARN, f"{lock} exists — an index run may still be going",
                   "wait for it, or delete the lock file if you are certain it died")


def _check_extraction(report: Report, cfg: dict[str, Any], rag_dir: Path, sample: int) -> None:
    candidates: list[Any] = []
    seen_ext: set[str] = set()
    for candidate in discover.iter_files(cfg, rag_dir):
        if candidate.ext in seen_ext and len(candidates) >= sample // 2:
            continue
        seen_ext.add(candidate.ext)
        candidates.append(candidate)
        if len(candidates) >= sample:
            break

    if not candidates:
        report.add("extraction", FAIL, "no files to sample", "check discovery above")
        return

    ok_count = 0
    problems: list[str] = []
    for candidate in candidates:
        doc = extract.extract(candidate.path, ocr=bool(cfg.get("corpus", {}).get("ocr")))
        if doc.error and doc.is_empty:
            problems.append(f"{candidate.rel_path}: {doc.error}")
        elif doc.is_empty:
            problems.append(f"{candidate.rel_path}: extracted 0 characters")
        else:
            ok_count += 1

    status = OK if not problems else (WARN if ok_count else FAIL)
    detail = f"{ok_count}/{len(candidates)} sampled files extracted text"
    if problems:
        detail += " — " + "; ".join(problems[:4])
    report.add("extraction", status, detail,
               "install the matching extra, enable corpus.ocr for scanned PDFs, "
               "or exclude these files in .ragignore")


def _check_models(report: Report, cfg: dict[str, Any], paths: dict[str, Path]) -> None:
    from . import embed, rerank

    try:
        embedder = embed.build(cfg, cache_dir=str(paths["cache"]))
    except Exception as exc:
        report.add("embedding model", FAIL, f"{type(exc).__name__}: {exc}",
                   "check embedding.model and embedding.backend, and that the extra is installed")
        return

    dimension = embedder.dimension
    recorded = int(cfg.get("embedding", {}).get("dimension", 0))
    if recorded and recorded != dimension:
        report.add("embedding model", WARN,
                   f"loaded '{embedder.model_id}' with dimension {dimension}, "
                   f"config recorded {recorded}",
                   "run 'rag index --full' — the recorded dimension is corrected automatically")
    else:
        report.add("embedding model", OK, f"'{embedder.model_id}' loaded, dimension {dimension}")

    import time

    started = time.time()
    embedder.embed_query("a short throughput probe")
    report.add("embedding speed", OK, f"{(time.time() - started) * 1000:.0f} ms for one query")

    reranker = rerank.build(cfg, cache_dir=str(paths["cache"]))
    if reranker.name == "none" and reranker.reason:
        status = WARN if cfg.get("retrieval", {}).get("rerank") else OK
        report.add("reranker", status, reranker.reason,
                   "install the matching extra, or set retrieval.rerank = false")
    else:
        report.add("reranker", OK, f"'{reranker.model_id}' via {reranker.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose a .rag workspace")
    parser.add_argument("--rag-dir", default="")
    parser.add_argument("--models", action="store_true")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--sample", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    found = Path(args.rag_dir).resolve() if args.rag_dir else config_mod.find_rag_dir()
    if found is None:
        print("no .rag workspace found. Run 'rag init' first.", file=sys.stderr)
        return 2
    return run_doctor(Path(found), args)


if __name__ == "__main__":
    raise SystemExit(main())
