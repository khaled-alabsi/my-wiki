"""Dependency installer for a .rag workspace.

Standard library only — it runs with the system interpreter, before ``.rag/.venv`` exists::

    python3 .rag/toolkit/rag_toolkit/install.py            # install what detection chose
    python3 .rag/toolkit/rag_toolkit/install.py --dry-run  # print the commands, change nothing

It prefers ``uv`` when present (much faster, and it resolves torch's platform wheels
correctly) and falls back to ``venv`` + ``pip``. On Windows without CUDA it installs the
CPU torch wheel index rather than dragging down a multi-gigabyte GPU build.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# Extras map to concrete requirement lists. Keep every pin loose: this is a tool a user
# installs into their own project, not a library other packages resolve against.
EXTRAS: dict[str, list[str]] = {
    "core": ["lancedb>=0.13", "pyarrow>=15", "pathspec>=0.12", "numpy>=1.24"],
    "onnx": ["fastembed>=0.4"],
    "torch": ["sentence-transformers>=3.0"],
    "documents": ["pymupdf>=1.24", "python-docx>=1.1", "python-pptx>=1.0", "openpyxl>=3.1"],
    "web": ["selectolax>=0.3"],
    "api": ["httpx>=0.27"],
    # 2.0 removed mcp.server.fastmcp, which mcp_server.py is built on. Pin to 1.x
    # until the server is ported; an unpinned install silently yields a broken
    # `rag serve --mcp` that blames a missing extra.
    "mcp": ["mcp>=1.2,<2"],
    "watch": ["watchdog>=4.0"],
    # ipykernel is what makes the venv selectable as a Jupyter/VS Code kernel;
    # without it the shipped notebook cannot run at all. ipywidgets is deliberately
    # absent: VS Code caches widget state per notebook path and stale registrations
    # make outputs render several times.
    "notebook": ["ipykernel>=6.29", "nbformat>=5.10", "nbclient>=0.10"],
    "ocr": ["rapidocr-onnxruntime>=1.3"],
}

# Torch wheel indexes. CPU is the right default anywhere without a working CUDA runtime.
TORCH_INDEX_CPU = "https://download.pytorch.org/whl/cpu"


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_dir(rag_dir: Path) -> Path:
    """Where the virtualenv lives — ``project.venv`` when set, else ``.rag/.venv``.

    Read straight from the TOML rather than through ``config.load``: this module is
    stdlib-only and runs before the venv (and therefore the package) exists.
    """
    config = rag_dir / "config.toml"
    if config.is_file():
        try:
            import tomllib

            with config.open("rb") as handle:
                configured = tomllib.load(handle).get("project", {}).get("venv", "")
            if configured:
                return Path(configured).expanduser()
        except Exception:
            pass
    return rag_dir / ".venv"


def choose_extras(rag_dir: Path, explicit: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Return ``(extras, reasons)`` from config when present, else from live detection."""
    if explicit:
        return sorted({"core", *explicit}), ["chosen explicitly on the command line"]

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from rag_toolkit import config as config_mod  # noqa: E402
    from rag_toolkit import models  # noqa: E402

    reasons: list[str] = []
    extras = {"core"}
    try:
        cfg = config_mod.load(rag_dir)
        backend = cfg.get("embedding", {}).get("backend", "fastembed")
        rerank_backend = cfg.get("retrieval", {}).get("rerank_backend", "none")
        extras.update(models.extras_for(backend, rerank_backend))
        reasons.append(f"config.toml selects the '{backend}' embedding backend")

        # Extraction extras come from what the corpus actually holds, never from a
        # default set: installing PDF and Office support for a corpus with neither
        # is a wasted multi-package download, and it used to happen every time.
        from rag_toolkit import discover, extract  # noqa: E402

        try:
            found = discover.plan(cfg, rag_dir)["by_extension"]
            wanted = extract.extras_for_extensions(found)
            extras.update(wanted)
            if wanted:
                reasons.append(
                    "corpus contains " + ", ".join(sorted(found)[:6]) + f" -> {', '.join(sorted(wanted))}"
                )
            else:
                reasons.append("no PDF/Office/HTML files found — skipping 'documents' and 'web'")
        except Exception as exc:  # a corpus we cannot walk should not block installing
            extras.update({"documents", "web"})
            reasons.append(f"could not scan the corpus ({exc}) — including all extractors")

        if cfg.get("corpus", {}).get("ocr"):
            extras.add("ocr")
            reasons.append("corpus.ocr is enabled")
    except FileNotFoundError:
        from rag_toolkit import detect  # noqa: E402

        host = detect.host()
        tier, reason = models.pick_tier(host)
        selection = models.select(host, None, tier=tier)
        extras.update(models.extras_for(
            selection["embedding"]["backend"], selection["retrieval"]["rerank_backend"]
        ))
        # No config means no source list to scan, so the corpus contents are unknown.
        # Err toward installing every extractor here: a wasted download is recoverable,
        # a file type that silently fails to extract is not.
        extras.update({"documents", "web"})
        reasons.append(f"no config.toml yet — detection says: {reason}")
        reasons.append("corpus unknown without a config — including all extractors")
    return sorted(extras), reasons


def requirements(extras: list[str]) -> list[str]:
    out: list[str] = []
    for extra in extras:
        for requirement in EXTRAS.get(extra, []):
            if requirement not in out:
                out.append(requirement)
    return out


def torch_step(python: Path, use_uv: bool) -> list[str] | None:
    """Install torch on its own when the CPU wheel index is needed.

    ``--extra-index-url`` only *adds* a source, so it cannot stop pip from resolving the
    multi-gigabyte CUDA build from PyPI. Forcing the CPU index with ``--index-url`` is
    correct here but must not apply to the other packages, so torch gets its own step.
    macOS wheels are universal and a machine with nvidia-smi wants the default index.
    """
    if platform.system() == "Darwin" or shutil.which("nvidia-smi"):
        return None
    base = (["uv", "pip", "install", "--python", str(python)] if use_uv
            else [str(python), "-m", "pip", "install"])
    return [*base, "--index-url", TORCH_INDEX_CPU, "torch"]


def interpreter_warning(extras: list[str]) -> str:
    """Warn when the venv would be built from a CPython the torch stack may not support.

    The venv inherits ``sys.executable``, which is normally the newest python on PATH —
    and a just-released CPython is the usual reason a torch install fails several
    minutes in, with a wheel-resolution error that does not mention the version.
    """
    if "torch" not in extras:
        return ""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from rag_toolkit import detect  # noqa: E402

        if sys.version_info[:2] <= (3, detect.NEWEST_TESTED_MINOR):
            return ""
        info = detect.interpreters()
        safe = info.get("recommended", "")
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        if safe and Path(safe).resolve() != Path(sys.executable).resolve():
            return (f"this is Python {current}, newer than the torch stack is known to "
                    f"support. Re-run with:\n       {safe} {Path(__file__)}")
        return (f"this is Python {current}, newer than the torch stack is known to "
                f"support, and no older interpreter was found. Expect wheel gaps.")
    except Exception:
        return ""


def build_commands(rag_dir: Path, extras: list[str], use_uv: bool) -> list[list[str]]:
    venv = venv_dir(rag_dir)
    python = venv_python(venv)
    reqs = requirements(extras)
    commands: list[list[str]] = []

    if use_uv:
        commands.append(["uv", "venv", "--python", sys.executable, str(venv)])
    else:
        commands.append([sys.executable, "-m", "venv", str(venv)])
        commands.append([str(python), "-m", "pip", "install", "--upgrade", "pip", "--quiet"])

    if "torch" in extras:
        step = torch_step(python, use_uv)
        if step:
            commands.append(step)

    if use_uv:
        commands.append(["uv", "pip", "install", "--python", str(python), *reqs])
    else:
        commands.append([str(python), "-m", "pip", "install", *reqs])
    return commands


def write_launchers(rag_dir: Path) -> list[Path]:
    """Small wrappers so every documented command is interpreter-qualified.

    The interpreter path is resolved at write time from ``project.venv``, because a
    shell script cannot read TOML. That makes the launchers machine-specific, which is
    fine: they are regenerated by ``install.py`` and by the generated ``bootstrap.sh``
    on any machine that needs them, and they are not portable data.
    """
    bin_dir = rag_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    venv = venv_dir(rag_dir)
    written: list[Path] = []

    # Relative to .rag when the venv sits inside it, so a moved project still works.
    try:
        posix_python = '"$here/' + str(venv.relative_to(rag_dir)) + '/bin/python"'
    except ValueError:
        posix_python = '"' + str(venv / "bin" / "python") + '"'

    posix = bin_dir / "rag"
    posix.write_text(
        '#!/usr/bin/env bash\n'
        '# Launcher: always runs the toolkit with the workspace venv.\n'
        'set -euo pipefail\n'
        'here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
        '# PYTHONPATH rather than trusting rag_toolkit.pth: on macOS a .rag inside an\n'
        '# iCloud container is flagged UF_HIDDEN, and CPython 3.13+ skips hidden .pth\n'
        '# files, so the toolkit would be present but unimportable.\n'
        'export PYTHONPATH="$here/toolkit${PYTHONPATH:+:$PYTHONPATH}"\n'
        f'exec {posix_python} -m rag_toolkit.cli --rag-dir "$here" "$@"\n',
        encoding="utf-8",
    )
    posix.chmod(0o755)
    written.append(posix)

    try:
        win_python = '"%HERE%\\' + str(venv.relative_to(rag_dir)) + '\\Scripts\\python.exe"'
    except ValueError:
        win_python = '"' + str(venv / "Scripts" / "python.exe") + '"'

    windows = bin_dir / "rag.cmd"
    windows.write_text(
        "@echo off\r\n"
        "setlocal\r\n"
        'set "HERE=%~dp0.."\r\n'
        'set "PYTHONPATH=%HERE%\\toolkit;%PYTHONPATH%"\r\n'
        f'{win_python} -m rag_toolkit.cli --rag-dir "%HERE%" %*\r\n',
        encoding="utf-8",
    )
    written.append(windows)
    return written


def unhide(path: Path) -> None:
    """Clear macOS ``UF_HIDDEN`` so CPython will process this file.

    A ``.rag`` workspace inside an iCloud container — an Obsidian vault, typically —
    gets ``UF_HIDDEN`` set on files beneath its dot-directory. Since 3.13,
    ``site.addpackage`` skips hidden ``.pth`` files, which leaves ``rag_toolkit``
    silently unimportable: the file is present and correct, and simply never read.
    """
    if not hasattr(os, "chflags"):  # not macOS/BSD
        return
    try:
        flags = os.lstat(path).st_flags
    except (OSError, AttributeError):
        return
    if flags & stat.UF_HIDDEN:
        try:
            os.chflags(path, flags & ~stat.UF_HIDDEN)
        except OSError:
            pass  # the launcher sets PYTHONPATH too, so this is not fatal


def write_pth(rag_dir: Path) -> Path | None:
    """Put ``.rag/toolkit`` on the venv's path so ``import rag_toolkit`` just works."""
    venv = venv_dir(rag_dir)
    candidates = list(venv.glob("lib/python*/site-packages")) + list(venv.glob("Lib/site-packages"))
    if not candidates:
        return None
    target = candidates[0] / "rag_toolkit.pth"
    target.write_text(str((rag_dir / "toolkit").resolve()) + "\n", encoding="utf-8")
    unhide(target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install .rag dependencies into .rag/.venv")
    parser.add_argument("--rag-dir", default="", help="path to the .rag directory")
    parser.add_argument("--extras", default="", help="comma-separated extras to force")
    parser.add_argument("--dry-run", action="store_true", help="print commands, change nothing")
    parser.add_argument("--no-uv", action="store_true", help="use venv + pip even if uv exists")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if sys.version_info < (3, 11):
        print(
            f"error: rag_toolkit needs Python 3.11 or newer (tomllib); this is "
            f"{platform.python_version()} at {sys.executable}.\n"
            f"       Re-run install.py with a newer interpreter — the venv is built from it.",
            file=sys.stderr,
        )
        return 2

    rag_dir = Path(args.rag_dir).resolve() if args.rag_dir else Path(__file__).resolve().parents[2]
    if rag_dir.name != ".rag":
        print(f"error: {rag_dir} is not a .rag directory — pass --rag-dir", file=sys.stderr)
        return 2

    explicit = [e.strip() for e in args.extras.split(",") if e.strip()]
    extras, reasons = choose_extras(rag_dir, explicit)
    use_uv = bool(shutil.which("uv")) and not args.no_uv
    commands = build_commands(rag_dir, extras, use_uv)

    if args.json:
        print(json.dumps({
            "rag_dir": str(rag_dir), "extras": extras, "reasons": reasons,
            "installer": "uv" if use_uv else "venv+pip",
            "commands": [" ".join(c) for c in commands],
            "requirements": requirements(extras),
        }, indent=2))
        if args.dry_run:
            return 0

    if not args.json:
        print(f"workspace   {rag_dir}")
        print(f"installer   {'uv' if use_uv else 'venv + pip'}")
        print(f"extras      {', '.join(extras)}")
        warning = interpreter_warning(extras)
        if warning:
            print(f"WARNING     {warning}")
        for reason in reasons:
            print(f"            - {reason}")
        print()
        for command in commands:
            print("  " + " ".join(command))
        print()

    if args.dry_run:
        print("dry run — nothing was installed.")
        return 0

    for command in commands:
        print(f"$ {' '.join(command)}", flush=True)
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"\nfailed: {' '.join(command)}", file=sys.stderr)
            return result.returncode

    write_pth(rag_dir)
    for launcher in write_launchers(rag_dir):
        print(f"wrote {launcher}")

    python = venv_python(venv_dir(rag_dir))
    print("\ninstalled. Next:")
    print(f"  {python} -m rag_toolkit.cli --rag-dir {rag_dir} doctor --models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
