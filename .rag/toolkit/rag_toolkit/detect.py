"""Host and corpus detection.

Standard library only, by design: this module runs *before* ``.rag/.venv`` exists,
via a bare ``python3 detect.py`` bootstrap. It never imports a third-party package
at module level, and every optional probe is wrapped.

Run directly for a JSON report::

    python3 detect.py --path /some/corpus
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_SKIP_DIRS = {
    ".git", ".hg", ".svn", ".rag", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", "out", "target", "bin", "obj", ".next", ".nuxt", ".svelte-kit",
    ".gradle", ".idea", ".vscode", ".cache", ".terraform", "vendor", "Pods",
    "site-packages", ".ipynb_checkpoints", ".DS_Store", "coverage", ".parcel-cache",
}


def is_private_name(name: str) -> bool:
    """True for names that are private by convention and must never be indexed.

    A leading ``.`` or ``_`` marks editor state, caches, tooling internals, scratch
    folders, and work-in-progress material. The rule is applied to directories and to
    files, here and in ``discover.py``, so the survey counts match what actually gets
    ingested.
    """
    return name.startswith((".", "_"))

CODE_EXT = {
    ".py", ".java", ".kt", ".cs", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".rb",
    ".php", ".c", ".h", ".cpp", ".hpp", ".scala", ".swift", ".m", ".sh", ".sql",
    ".vue", ".svelte", ".gradle", ".tf",
}
DOC_EXT = {".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls", ".epub", ".rtf", ".odt"}
NOTE_EXT = {".md", ".markdown", ".mdx", ".org", ".rst", ".txt"}
DATA_EXT = {".json", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml", ".ini", ".ipynb"}
WEB_EXT = {".html", ".htm"}

# Path fragments that mean "this is inside a file-sync container". Order matters:
# CloudStorage is checked before the bare vendor names because macOS mounts OneDrive,
# Google Drive, Dropbox and Box underneath it with decorated folder names.
SYNC_CONTAINERS: tuple[tuple[str, str, str], ...] = (
    ("/Library/Mobile Documents/", "icloud", "iCloud Drive"),
    ("/Library/CloudStorage/", "cloudstorage", "macOS CloudStorage"),
    ("/Dropbox/", "dropbox", "Dropbox"),
    ("/OneDrive", "onedrive", "OneDrive"),
    ("/Google Drive", "gdrive", "Google Drive"),
    ("/pCloud Drive/", "pcloud", "pCloud"),
    ("/Nextcloud/", "nextcloud", "Nextcloud"),
    ("/Sync.com/", "synccom", "Sync.com"),
)

# Which CloudStorage vendor, once we know we are under that mount point.
_CLOUDSTORAGE_VENDORS: tuple[tuple[str, str, str], ...] = (
    ("onedrive", "onedrive", "OneDrive"),
    ("googledrive", "gdrive", "Google Drive"),
    ("dropbox", "dropbox", "Dropbox"),
    ("box", "box", "Box"),
    ("egnyte", "egnyte", "Egnyte"),
)

# How many note files to sample for the language guess. Higher than the old 25
# because the verdict is now per-file: a single minority-language file matters.
LANGUAGE_SAMPLES = 60

STOPWORDS = {
    "en": {"the", "and", "that", "with", "this", "from", "have", "which", "are", "for"},
    "de": {"der", "die", "das", "und", "nicht", "mit", "eine", "auch", "wird", "werden"},
    "fr": {"les", "des", "une", "que", "pour", "dans", "est", "pas", "sur", "avec"},
    "es": {"que", "los", "las", "una", "por", "para", "con", "del", "como", "más"},
    "it": {"che", "per", "con", "del", "una", "sono", "come", "nella", "alla", "più"},
    "nl": {"het", "een", "van", "niet", "voor", "met", "zijn", "worden", "aan", "door"},
}


# --------------------------------------------------------------------------- host


def total_ram_gb() -> float:
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
            return round(int(out.stdout.strip()) / 1024**3, 1)
        if system == "Linux":
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    return round(int(line.split()[1]) / 1024**2, 1)
        if system == "Windows":
            class _Status(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            status = _Status()
            status.dwLength = ctypes.sizeof(_Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))  # type: ignore[attr-defined]
            return round(status.ullTotalPhys / 1024**3, 1)
    except Exception:
        pass
    return 0.0


def nvidia_gpus() -> list[dict[str, Any]]:
    if not shutil.which("nvidia-smi"):
        return []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return []
    gpus = []
    for line in out.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2 and parts[1].isdigit():
            gpus.append({"name": parts[0], "vram_gb": round(int(parts[1]) / 1024, 1)})
    return gpus


def accelerator() -> dict[str, Any]:
    """Pick the best available device without requiring torch to be installed."""
    system, machine = platform.system(), platform.machine()
    gpus = nvidia_gpus()
    torch_mps = torch_cuda = None
    try:  # authoritative when torch is already present; absent is not an error
        import torch  # type: ignore

        torch_mps = bool(torch.backends.mps.is_available())
        torch_cuda = bool(torch.cuda.is_available())
    except Exception:
        pass

    if gpus and torch_cuda is not False:
        return {"device": "cuda", "vram_gb": max(g["vram_gb"] for g in gpus), "gpus": gpus,
                "confirmed_by_torch": bool(torch_cuda)}
    if system == "Darwin" and machine == "arm64" and torch_mps is not False:
        return {"device": "mps", "vram_gb": 0.0, "gpus": [], "confirmed_by_torch": bool(torch_mps)}
    return {"device": "cpu", "vram_gb": 0.0, "gpus": gpus, "confirmed_by_torch": False}


def onnx_providers() -> list[str]:
    try:
        import onnxruntime  # type: ignore

        return list(onnxruntime.get_available_providers())
    except Exception:
        return []


# The newest CPython minor the torch / sentence-transformers stack is known to have
# wheels for. A just-released CPython is the usual reason a `torch` tier install dies
# minutes in, so detection names a safer interpreter rather than leaving it to chance.
NEWEST_TESTED_MINOR = 13
OLDEST_SUPPORTED_MINOR = 11  # tomllib


def interpreters() -> dict[str, Any]:
    """Available CPython interpreters, with a recommendation for the heavy tiers.

    ``install.py`` builds the venv from whichever interpreter runs it — normally the
    newest ``python3`` on PATH, which is exactly the one most likely to have no wheels
    yet for torch and its dependencies.
    """
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in ("python3.14", "python3.13", "python3.12", "python3.11", "python3"):
        path = shutil.which(name)
        if not path:
            continue
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        try:
            out = subprocess.run(
                [path, "-c", "import sys;print('%d.%d.%d' % sys.version_info[:3])"],
                capture_output=True, text=True, timeout=10,
            )
            version = out.stdout.strip()
            minor = int(version.split(".")[1])
        except Exception:
            continue
        if not version:
            continue
        found.append({
            "path": path, "version": version,
            "usable": minor >= OLDEST_SUPPORTED_MINOR,
            "safe_for_torch": OLDEST_SUPPORTED_MINOR <= minor <= NEWEST_TESTED_MINOR,
        })

    safe = [i for i in found if i["safe_for_torch"]]
    usable = [i for i in found if i["usable"]]
    recommended, reason = "", ""
    if safe:
        recommended = max(safe, key=lambda i: i["version"])["path"]
        newest = max(usable, key=lambda i: i["version"]) if usable else None
        if newest and not newest["safe_for_torch"]:
            reason = (f"{newest['version']} is newer than the torch stack is known to support; "
                      f"build the venv from {recommended} on the torch tiers")
        else:
            reason = "newest interpreter is also the safest"
    elif usable:
        recommended = max(usable, key=lambda i: i["version"])["path"]
        reason = "no interpreter within the tested range — expect wheel gaps on the torch tiers"
    return {"available": found, "recommended": recommended, "reason": reason}


def host() -> dict[str, Any]:
    accel = accelerator()
    return {
        "interpreters": interpreters(),
        "os": platform.system().lower(),
        "os_release": platform.release(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count() or 1,
        "ram_gb": total_ram_gb(),
        "accelerator": accel,
        "onnx_providers": onnx_providers(),
        "has_uv": bool(shutil.which("uv")),
        "has_git": bool(shutil.which("git")),
    }


# --------------------------------------------------------------------------- corpus


def sync_container(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Report the file-sync container *path* sits inside, if any.

    This is not a curiosity. A ``.rag`` workspace accumulates gigabytes of
    rebuildable data — model weights, a virtualenv, a vector store — none of which
    should ever sync, and two concrete failures follow from letting it:

    * macOS flags files under a dot-directory in an iCloud container ``UF_HIDDEN``,
      and CPython 3.13+ skips hidden ``.pth`` files, leaving the toolkit importable
      only through an explicit ``PYTHONPATH``.
    * ``state/manifest.sqlite`` syncing while ``db/`` stays machine-local gives a
      second machine a manifest claiming everything is indexed against an empty
      store. ``update`` then skips every file and reports success on an empty index.

    Returns ``kind``/``label``/``root``, with ``kind`` None when the path is not in
    a known container.
    """
    resolved = str(Path(path).expanduser().resolve())
    probe = resolved if resolved.endswith(os.sep) else resolved + os.sep
    for marker, kind, label in SYNC_CONTAINERS:
        index = probe.find(marker)
        if index == -1:
            continue
        root = probe[: index + len(marker)].rstrip(os.sep)
        if kind == "cloudstorage":
            # e.g. .../CloudStorage/OneDrive-Personal/... — name the real vendor.
            # Compare case-insensitively but keep the on-disk spelling in `root`.
            leaf = probe[index + len(marker):].split(os.sep, 1)[0]
            for needle, vendor_kind, vendor_label in _CLOUDSTORAGE_VENDORS:
                if needle in leaf.lower():
                    return {"kind": vendor_kind, "label": vendor_label,
                            "root": f"{root}{os.sep}{leaf}"}
        return {"kind": kind, "label": label, "root": root}
    return {"kind": None, "label": "", "root": ""}


def _family(ext: str) -> str:
    if ext in CODE_EXT:
        return "code"
    if ext in DOC_EXT:
        return "documents"
    if ext in NOTE_EXT:
        return "notes"
    if ext in DATA_EXT:
        return "data"
    if ext in WEB_EXT:
        return "web"
    return "other"


def _score_one(text: str) -> str:
    """Best-guess language for a single sample, or "" when there is too little signal."""
    words = [w.strip(".,;:!?()[]\"'") for w in text.lower().split()]
    if len(words) < 40:
        return ""
    scores = {lang: sum(1 for w in words if w in bag) for lang, bag in STOPWORDS.items()}
    best = max(scores, key=lambda k: scores[k])
    if scores[best] < 5:
        return ""
    others = sum(v for k, v in scores.items() if k != best)
    return best if scores[best] > others * 2 else ""


def _sample_language(samples: list[str]) -> str:
    """Language verdict across the sampled files: a language name, "mixed", or "unknown".

    Scored **per file**, never on the concatenation. Pooling first made a minority
    language arithmetically invisible: one long German note among 144 English ones
    cannot beat ``others * 2`` on a merged blob, so the corpus reported ``en`` and a
    non-``large`` tier would have picked an English-only model. That failure is silent
    — retrieval still returns results, just quietly worse ones.

    A single confidently non-dominant file is enough to say "mixed". Multilingual
    models cost a little more and getting this wrong cannot be noticed from the output.
    """
    verdicts = [lang for lang in (_score_one(s) for s in samples) if lang]
    if not verdicts:
        return "unknown"
    counts: dict[str, int] = {}
    for lang in verdicts:
        counts[lang] = counts.get(lang, 0) + 1
    dominant = max(counts, key=lambda k: counts[k])
    return dominant if len(counts) == 1 else "mixed"


def survey(root: Path, max_files: int = 400_000) -> dict[str, Any]:
    """Walk *root* and describe what is in it. Read-only, no third-party imports."""
    exts: dict[str, int] = {}
    families: dict[str, int] = {}
    total_bytes = 0
    family_bytes: dict[str, int] = {}
    count = 0
    max_depth = 0
    depth_sum = 0
    samples: list[str] = []
    markers: set[str] = set()
    seen_notes = 0
    sampler = random.Random(0)  # deterministic: the same corpus reports the same guess
    truncated = False

    root = root.resolve()
    marker_names = (".git", ".obsidian", "package.json", "pom.xml", "build.gradle",
                    "pyproject.toml", "Cargo.toml", "go.mod", "requirements.txt")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in DEFAULT_SKIP_DIRS and not is_private_name(d)]
        rel_depth = len(Path(dirpath).relative_to(root).parts)
        if rel_depth <= 1:  # markers only matter near the top; stat'ing every dir is too slow
            for marker in marker_names:
                if (Path(dirpath) / marker).exists():
                    markers.add(marker)
        for name in filenames:
            if is_private_name(name):
                continue
            path = Path(dirpath) / name
            ext = path.suffix.lower()
            try:
                size = path.stat().st_size
            except OSError:
                continue
            count += 1
            depth_sum += rel_depth
            max_depth = max(max_depth, rel_depth)
            total_bytes += size
            exts[ext or "<none>"] = exts.get(ext or "<none>", 0) + 1
            fam = _family(ext)
            families[fam] = families.get(fam, 0) + 1
            family_bytes[fam] = family_bytes.get(fam, 0) + size
            # Reservoir sampling, so the sample is spread across the whole corpus.
            # Taking the first N in walk order meant a minority-language note living
            # late in the tree was never looked at, and the language guess could not
            # see it even in principle.
            if ext in NOTE_EXT and 200 < size < 200_000:
                seen_notes += 1
                slot = -1
                if len(samples) < LANGUAGE_SAMPLES:
                    slot = len(samples)
                    samples.append("")
                elif sampler.random() < LANGUAGE_SAMPLES / seen_notes:
                    slot = sampler.randrange(LANGUAGE_SAMPLES)
                if slot >= 0:
                    try:
                        samples[slot] = path.read_text(encoding="utf-8", errors="ignore")[:4000]
                    except OSError:
                        samples[slot] = ""
            if count >= max_files:
                truncated = True
                break
        if truncated:
            break

    top_exts = dict(sorted(exts.items(), key=lambda kv: kv[1], reverse=True)[:25])
    return {
        "path": str(root),
        "file_count": count,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / 1024**2, 1),
        "truncated": truncated,
        "max_depth": max_depth,
        "mean_depth": round(depth_sum / count, 1) if count else 0.0,
        "extensions": top_exts,
        "families": families,
        "family_bytes": family_bytes,
        "markers": sorted(markers),
        "language_guess": _sample_language(samples),
        "sync_container": sync_container(root),
    }


def profile_for(corpus: dict[str, Any]) -> str:
    """Map a survey onto one of the bundled corpus profiles."""
    count = corpus.get("file_count", 0)
    families = corpus.get("families", {})
    fam_bytes = corpus.get("family_bytes", {})
    total_bytes = max(corpus.get("total_bytes", 0), 1)
    distinct = sum(1 for fam, n in families.items() if fam != "other" and n > count * 0.05)

    if count > 2000 or distinct >= 3 or corpus.get("max_depth", 0) > 5:
        return "mixed"
    if fam_bytes.get("documents", 0) / total_bytes > 0.30:
        return "documents"
    if ".git" in corpus.get("markers", []) and families.get("code", 0) > count * 0.35:
        return "code"
    if families.get("notes", 0) > count * 0.70:
        return "notes"
    return "generic"


def report(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    corpus = survey(Path(path)) if path else None
    data: dict[str, Any] = {"host": host(), "corpus": corpus}
    if corpus:
        data["suggested_profile"] = profile_for(corpus)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect host capabilities and survey a corpus.")
    parser.add_argument("--path", help="corpus directory to survey")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args(argv)
    print(json.dumps(report(args.path), indent=args.indent, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
