"""Configuration for a .rag workspace.

The config is a plain nested dict persisted as TOML at ``.rag/config.toml``. Every
auto-detected choice is written out as an explicit value, so a user can read and
override any decision the toolkit made.
"""

from __future__ import annotations

import copy
import datetime as _dt
import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - guarded by install.py/doctor
    raise RuntimeError("rag_toolkit requires Python 3.11 or newer (tomllib)") from exc

CONFIG_NAME = "config.toml"
RAG_DIR_NAME = ".rag"

DEFAULTS: dict[str, Any] = {
    "project": {
        "root": "",
        "created": "",
        "toolkit_version": "",
    },
    "sources": [],
    "corpus": {
        "profile": "generic",
        "language": "auto",
        "max_file_mb": 25.0,
        "follow_symlinks": False,
        "use_gitignore": True,
        "ocr": False,
    },
    "chunking": {
        "strategy": "auto",
        "target_chars": 1800,
        "overlap_chars": 220,
        "min_chars": 120,
        "prefix_context": True,
    },
    "embedding": {
        "tier": "balanced",
        "backend": "fastembed",
        "model": "",
        "dimension": 0,
        "batch_size": 32,
        "device": "cpu",
        "query_prefix": "",
        "document_prefix": "",
        "normalize": True,
        "trust_remote_code": False,
    },
    "store": {
        "kind": "lancedb",
        "table": "chunks",
    },
    "retrieval": {
        "top_k": 10,
        "candidates": 60,
        "hybrid": True,
        "rrf_k": 60,
        "rerank": True,
        "rerank_backend": "none",
        "rerank_model": "",
        "rerank_candidates": 40,
    },
    "server": {
        "web_host": "127.0.0.1",
        "web_port": 8765,
    },
}


# --------------------------------------------------------------------------- paths


def find_rag_dir(start: str | os.PathLike[str] | None = None) -> Path | None:
    """Walk upward from *start* looking for an existing ``.rag`` directory."""
    here = Path(start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        rag = candidate / RAG_DIR_NAME
        if (rag / CONFIG_NAME).is_file():
            return rag
    return None


def rag_dir_for(project_root: str | os.PathLike[str]) -> Path:
    return Path(project_root).resolve() / RAG_DIR_NAME


def layout(rag_dir: Path) -> dict[str, Path]:
    """Canonical subpaths of a ``.rag`` workspace."""
    return {
        "root": rag_dir,
        "config": rag_dir / CONFIG_NAME,
        "ragignore": rag_dir / ".ragignore",
        "version": rag_dir / "VERSION",
        "docs": rag_dir / "docs",
        "toolkit": rag_dir / "toolkit",
        "venv": rag_dir / ".venv",
        "db": rag_dir / "db",
        "state": rag_dir / "state",
        "manifest": rag_dir / "state" / "manifest.sqlite",
        "progress": rag_dir / "state" / "progress.json",
        "log": rag_dir / "state" / "index.log",
        "lock": rag_dir / "state" / "index.lock",
        "cache": rag_dir / "cache" / "models",
        "notebooks": rag_dir / "notebooks",
        "bin": rag_dir / "bin",
    }


# --------------------------------------------------------------------------- load / save


def default_config(project_root: str | os.PathLike[str], version: str) -> dict[str, Any]:
    cfg = copy.deepcopy(DEFAULTS)
    cfg["project"]["root"] = str(Path(project_root).resolve())
    cfg["project"]["created"] = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    cfg["project"]["toolkit_version"] = version
    return cfg


def deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load(rag_dir: Path) -> dict[str, Any]:
    path = layout(rag_dir)["config"]
    if not path.is_file():
        raise FileNotFoundError(f"no config at {path} — run 'rag init' first")
    with path.open("rb") as handle:
        stored = tomllib.load(handle)
    return deep_merge(DEFAULTS, stored)


def save(cfg: dict[str, Any], rag_dir: Path) -> Path:
    """Write the config atomically. The file is always valid TOML after this call."""
    path = layout(rag_dir)["config"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".toml.tmp")
    tmp.write_text(dumps_toml(cfg), encoding="utf-8")
    tmp.replace(path)
    return path


# --------------------------------------------------------------------------- dotted access


def get(cfg: dict[str, Any], dotted: str, default: Any = None) -> Any:
    node: Any = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_(cfg: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            raise TypeError(f"{dotted}: '{part}' is not a table")
    node[parts[-1]] = coerce(value, node.get(parts[-1]))


def coerce(value: Any, like: Any) -> Any:
    """Coerce a CLI string to the type of the existing value it replaces."""
    if not isinstance(value, str) or like is None:
        return value
    if isinstance(like, bool):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(like, int):
        return int(value)
    if isinstance(like, float):
        return float(value)
    if isinstance(like, list):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


# --------------------------------------------------------------------------- TOML output


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_fmt(item) for item in value) + "]"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _emit(node: dict[str, Any], prefix: str, out: list[str]) -> None:
    scalars = {k: v for k, v in node.items() if not isinstance(v, dict) and not _is_table_array(v)}
    if scalars or prefix:
        if prefix:
            out.append(f"[{prefix}]")
        for key, value in scalars.items():
            out.append(f"{key} = {_fmt(value)}")
        out.append("")
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            _emit(value, path, out)
        elif _is_table_array(value):
            for entry in value:
                out.append(f"[[{path}]]")
                for sub_key, sub_value in entry.items():
                    out.append(f"{sub_key} = {_fmt(sub_value)}")
                out.append("")


def _is_table_array(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(i, dict) for i in value)


def dumps_toml(cfg: dict[str, Any]) -> str:
    out: list[str] = ["# .rag configuration — edit freely, then re-run 'rag doctor'.", ""]
    _emit(cfg, "", out)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"
