"""Command line interface.

    rag init [PATH ...]      create .rag, detect the host and corpus, write config.toml
    rag plan                 dry run: what would be indexed, and a chunk estimate
    rag index [--full]       build the index      (heavy — embeds the corpus)
    rag update               incremental refresh  (heavy in proportion to what changed)
    rag search QUERY         hybrid search with citations
    rag status               index size, staleness, drift
    rag doctor [--models]    diagnose environment, dependencies, models, store
    rag config show|get|set  read and edit config.toml
    rag serve --mcp|--web    expose the index to an agent or a browser
    rag watch                re-index on file change

Every command accepts ``--json`` for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__
from . import config as config_mod
from . import detect, discover, models


def _resolve_rag_dir(args: argparse.Namespace, must_exist: bool = True) -> Path:
    if getattr(args, "rag_dir", ""):
        return Path(args.rag_dir).resolve()
    found = config_mod.find_rag_dir()
    if found is None:
        if must_exist:
            raise SystemExit("no .rag workspace found here or above. Run 'rag init' first.")
        return config_mod.rag_dir_for(Path.cwd())
    return found


def _emit(payload: dict[str, Any], as_json: bool, lines: list[str] | None = None) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    elif lines:
        print("\n".join(lines))


# --------------------------------------------------------------------------- init


def _default_store(project_root: Path) -> Path:
    """Where relocated heavy data goes when the project is in a sync container."""
    base = Path(os.environ.get("XDG_DATA_HOME", "")).expanduser() if os.environ.get("XDG_DATA_HOME") \
        else Path.home() / ".local" / "share"
    return base / "rag" / project_root.name


def _make_store(rag_dir: Path, store: Path, venv: Path, project_root: Path,
                in_sync_container: bool) -> list[str]:
    """Create the external store directories, and link to them only where that is safe.

    **Never create a symlink inside a file-sync container.** iCloud Drive cannot sync
    symlinks: it replaces each one with an empty directory named ``cache 2``, ``db 2``,
    ``.venv 2`` and so on, which reappear after every deletion. Dropbox and OneDrive
    mangle them in their own ways.

    Nothing needs the links. ``config.layout()`` reads ``project.store`` and
    ``project.venv`` and uses the real paths, and the launchers embed the resolved
    interpreter path at write time. The links were only ever there so that listing
    ``.rag/`` showed where the data went — which ``config.toml`` already says, without
    generating conflict garbage.

    Outside a sync container they are harmless and mildly useful, so they are still made.
    """
    notes: list[str] = []
    for name in ("db", "state", "cache"):
        (store / name).mkdir(parents=True, exist_ok=True)
    venv.parent.mkdir(parents=True, exist_ok=True)

    if in_sync_container:
        notes.append("no symlinks created inside the sync container — it cannot sync them; "
                     "config.toml records the real locations")
        return notes

    for name in ("db", "state", "cache"):
        link = rag_dir / name
        if link.is_symlink() or not link.exists():
            try:
                if link.is_symlink():
                    link.unlink()
                link.symlink_to(store / name)
            except OSError:
                notes.append(f"could not link .rag/{name} (the real path is still used)")
    root_link = project_root / ".venv"
    if venv != root_link and (root_link.is_symlink() or not root_link.exists()):
        try:
            if root_link.is_symlink():
                root_link.unlink()
            root_link.symlink_to(venv)
        except OSError:
            notes.append(f"could not link {root_link}")
    return notes


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root or Path.cwd()).resolve()
    rag_dir = Path(args.rag_dir).resolve() if args.rag_dir else config_mod.rag_dir_for(project_root)
    paths = config_mod.layout(rag_dir)

    if paths["config"].is_file() and not args.force:
        raise SystemExit(f"{paths['config']} already exists. Use --force to overwrite it.")

    raw_sources = args.sources or [str(project_root)]
    sources = []
    for entry in raw_sources:
        path = Path(entry).expanduser().resolve()
        if not path.is_dir():
            raise SystemExit(f"source is not a directory: {path}")
        sources.append({"name": args.name or path.name, "path": str(path),
                        "include": [], "exclude": []})

    host = detect.host()
    primary = detect.survey(Path(sources[0]["path"]))
    profile = detect.profile_for(primary)

    cfg = config_mod.default_config(project_root, __version__)
    cfg["sources"] = sources
    cfg["corpus"]["profile"] = args.profile or profile

    # A project inside a file-sync container must not hold the heavy, rebuildable
    # data: gigabytes of model weights and a virtualenv would sync, sync eviction
    # breaks the install, and a synced manifest paired with a machine-local store
    # yields an empty index that reports success. Relocate by default; --no-relocate
    # keeps everything inside .rag/ for anyone who has a reason to.
    container = detect.sync_container(project_root)
    relocate_notes: list[str] = []
    if args.store:
        cfg["project"]["store"] = str(Path(args.store).expanduser().resolve())
    elif container["kind"] and not args.no_relocate:
        cfg["project"]["store"] = str(_default_store(project_root))
    if args.venv:
        cfg["project"]["venv"] = str(Path(args.venv).expanduser().resolve())
    elif cfg["project"]["store"]:
        # The venv is the other multi-GB directory, so it moves too. It lives beside
        # the rest of the store; a symlink at <project>/.venv points editors at it.
        cfg["project"]["venv"] = str(Path(cfg["project"]["store"]) / "venv")

    paths = config_mod.layout(rag_dir, cfg)  # re-derive: store/venv may have moved

    # Estimate the chunk count before choosing a tier: a corpus large enough to make a
    # heavy model's run time dominate should step the tier down.
    try:
        estimate = int(discover.plan(cfg, rag_dir)["estimated_chunks"])
    except Exception:
        estimate = 0

    selection = models.select(
        host, primary, tier=args.tier, language=args.language, estimated_chunks=estimate
    )
    cfg["corpus"]["language"] = selection["language"]
    cfg["embedding"].update(selection["embedding"])
    cfg["embedding"]["device"] = host["accelerator"]["device"]
    cfg["retrieval"].update(selection["retrieval"])

    for key in ("docs", "state", "db", "cache", "notebooks", "bin"):
        paths[key].mkdir(parents=True, exist_ok=True)
    if cfg["project"]["store"]:
        relocate_notes = _make_store(
            rag_dir, Path(cfg["project"]["store"]), paths["venv"], project_root,
            in_sync_container=bool(container["kind"]),
        )
    config_mod.save(cfg, rag_dir)
    paths["version"].write_text(f"{__version__}\n", encoding="utf-8")

    payload = {
        "rag_dir": str(rag_dir), "project_root": str(project_root), "sources": sources,
        "host": host, "corpus": primary, "profile": cfg["corpus"]["profile"],
        "selection": selection, "estimated_chunks": estimate,
        "sync_container": container,
        "store": cfg["project"]["store"], "venv": cfg["project"]["venv"],
        "extras": models.extras_for(
            cfg["embedding"]["backend"], cfg["retrieval"]["rerank_backend"]
        ),
    }
    lines = [
        f"created     {rag_dir}",
        f"sources     " + ", ".join(f"{s['name']} -> {s['path']}" for s in sources),
        f"corpus      {primary['file_count']} files, {primary['total_mb']} MB, "
        f"profile '{cfg['corpus']['profile']}', language '{selection['language']}'",
        f"host        {host['os']}/{host['arch']}, {host['ram_gb']} GB RAM, "
        f"device '{host['accelerator']['device']}'",
        f"tier        {selection['tier']} — " + "; ".join(selection["notes"]),
        f"embedding   {cfg['embedding']['model']} via {cfg['embedding']['backend']}",
        f"reranker    {cfg['retrieval']['rerank_model'] or 'none'}",
        f"disk        ~{selection['disk_mb']} MB of model weights on first run",
    ]
    if container["kind"]:
        lines.append(f"sync        inside {container['label']} — {container['root']}")
    if cfg["project"]["store"]:
        lines += [
            f"store       {cfg['project']['store']}",
            f"venv        {cfg['project']['venv']}",
            "            db, state, cache and the venv were placed OUTSIDE the sync",
            "            container: they are rebuildable, and a synced manifest over a",
            "            local store silently produces an empty index. No symlinks were",
            "            left behind — the container cannot sync them.",
        ]
        lines += [f"            note: {n}" for n in relocate_notes]
    elif container["kind"]:
        lines.append("            --no-relocate given: heavy data stays inside the container")
    # install.py builds the venv from whichever interpreter runs it. On the torch tiers
    # that must not be a CPython newer than the stack has wheels for, so name the safe
    # one explicitly rather than letting `python3` decide.
    interp = host.get("interpreters", {})
    installer_python = interp.get("recommended") or sys.executable
    needs_torch = cfg["embedding"]["backend"] == "sentence-transformers"
    if needs_torch and interp.get("reason") and installer_python != sys.executable:
        lines.append(f"python      {interp['reason']}")
    lines += [
        "",
        "Next, install dependencies (this downloads packages — run it yourself):",
        f"  {installer_python} {rag_dir / 'toolkit' / 'rag_toolkit' / 'install.py'}",
    ]
    _emit(payload, args.json, lines)
    return 0


# --------------------------------------------------------------------------- plan / index


def cmd_plan(args: argparse.Namespace) -> int:
    rag_dir = _resolve_rag_dir(args)
    cfg = config_mod.load(rag_dir)
    result = discover.plan(cfg, rag_dir)
    lines = [
        f"indexable   {result['files']} files, {result['total_mb']} MB on disk",
        f"text        ~{result['estimated_text_mb']} MB after extraction",
        f"chunks      ~{result['estimated_chunks']} estimated",
        "",
        "by extension:",
        *[f"  {ext:<12} {count}" for ext, count in list(result["by_extension"].items())[:15]],
    ]
    if result["skipped"]:
        lines += ["", "skipped:", *[f"  {reason:<45} {count}"
                                    for reason, count in result["skipped"].items()]]
    _emit(result, args.json, lines)
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    from .index import iter_progress_lines, run_index

    rag_dir = _resolve_rag_dir(args)
    verbose = not args.json and not args.quiet

    def progress(event: str, data: dict[str, Any]) -> None:
        if not verbose:
            return
        if event == "indexed":
            print(f"  + {data['path']} ({data['chunks']} chunks)", flush=True)
        elif event == "failed":
            print(f"  ! {data['path']}: {data['error']}", file=sys.stderr, flush=True)
        elif event == "dimension_corrected":
            print(f"  config dimension {data['was']} corrected to {data['now']}", flush=True)

    stats = run_index(rag_dir, full=args.full, limit=args.limit, on_progress=progress)
    payload = stats.as_dict()
    lines = ["", *iter_progress_lines(stats)]
    if stats.failures:
        lines += ["", "first failures:"]
        lines += [f"  {f['path']}: {f['error']}" for f in stats.failures[:10]]
    _emit(payload, args.json, lines)
    return 1 if stats.failed and not stats.indexed else 0


def cmd_update(args: argparse.Namespace) -> int:
    args.full = False
    args.limit = 0
    return cmd_index(args)


# --------------------------------------------------------------------------- search


def cmd_search(args: argparse.Namespace) -> int:
    from .api import Index
    from .retrieve import to_dict

    rag_dir = _resolve_rag_dir(args)
    with Index(rag_dir) as index:
        report = index.search_report(
            args.query, k=args.k, path=args.path, ext=args.ext, source=args.source,
            since=args.since, rerank_results=None if not args.no_rerank else False,
            hybrid=False if args.no_hybrid else None,
        )
        hits = [to_dict(hit, max_chars=args.max_chars) for hit in report.hits]

    payload = {
        "query": args.query, "hits": hits, "dense": report.dense_count,
        "text": report.text_count, "fused": report.fused_count,
        "reranked": report.reranked, "notes": report.notes,
    }
    lines: list[str] = []
    if not hits:
        lines.append(f"no matches for: {args.query}")
    for number, hit in enumerate(hits, start=1):
        lines.append(f"\n[{number}] {hit['citation']}")
        lines.append(f"    score {hit['score']}  ({hit['matched_by']})")
        body = "\n".join(f"    {ln}" for ln in hit["text"].splitlines()[: args.lines])
        lines.append(body)
    for note in report.notes:
        lines.append(f"\nnote: {note}")
    _emit(payload, args.json, lines)
    return 0


# --------------------------------------------------------------------------- status / config


def cmd_status(args: argparse.Namespace) -> int:
    from .api import Index

    rag_dir = _resolve_rag_dir(args)
    status = Index(rag_dir).status()
    lines = [
        f"workspace   {status['rag_dir']}",
        f"sources     " + ", ".join(f"{s['name']} -> {s['path']}" for s in status["sources"]),
        f"embedding   {status['embedding'].get('model', '?')} "
        f"({status['embedding'].get('backend', '?')}, dim {status['embedding'].get('dimension', '?')})",
        f"store       {status['store'].get('kind', '?')}",
        f"indexed     {status.get('files', 0)} files, {status.get('chunks', 0)} chunks",
    ]
    if status.get("by_status"):
        lines.append("            " + ", ".join(f"{k}: {v}" for k, v in status["by_status"].items()))
    last = status.get("last_run") or {}
    if last:
        lines.append(f"last run    {last.get('kind', '?')}, "
                     f"{last.get('stats', {}).get('indexed', 0)} indexed, "
                     f"{last.get('stats', {}).get('seconds', 0)}s")
    if status.get("warning"):
        lines += ["", f"WARNING: {status['warning']}"]
    if status.get("message"):
        lines += ["", status["message"]]
    _emit(status, args.json, lines)
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    rag_dir = _resolve_rag_dir(args)
    cfg = config_mod.load(rag_dir)
    if args.action == "show":
        _emit(cfg, args.json, [config_mod.dumps_toml(cfg)])
    elif args.action == "get":
        value = config_mod.get(cfg, args.key)
        _emit({args.key: value}, args.json, [str(value)])
    elif args.action == "set":
        config_mod.set_(cfg, args.key, args.value)
        config_mod.save(cfg, rag_dir)
        new = config_mod.get(cfg, args.key)
        _emit({args.key: new}, args.json, [f"{args.key} = {new!r}"])
        if args.key.startswith("embedding.") or args.key.startswith("chunking."):
            print("\nThis changes how content is encoded. Re-run 'rag index --full' "
                  "before trusting search results.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- serve / watch


def cmd_serve(args: argparse.Namespace) -> int:
    rag_dir = _resolve_rag_dir(args)
    if args.mcp:
        from .mcp_server import serve

        return serve(rag_dir)
    from .webui import serve_web

    cfg = config_mod.load(rag_dir)
    return serve_web(
        rag_dir,
        host=args.host or cfg["server"]["web_host"],
        port=args.port or int(cfg["server"]["web_port"]),
    )


def cmd_watch(args: argparse.Namespace) -> int:
    from .watch import watch

    return watch(_resolve_rag_dir(args), debounce=args.debounce)


def cmd_doctor(args: argparse.Namespace) -> int:
    from .doctor import run_doctor

    return run_doctor(_resolve_rag_dir(args, must_exist=False), args)


# --------------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag", description=__doc__.split("\n")[0])
    parser.add_argument("--rag-dir", default="", help="path to the .rag workspace")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--version", action="version", version=f"rag_toolkit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create .rag and write a detected config")
    init.add_argument("sources", nargs="*", help="folders to index (default: the project root)")
    init.add_argument("--project-root", default="", help="where .rag is created")
    init.add_argument("--name", default="", help="name for the first source")
    init.add_argument("--profile", default="", help="generic|mixed|code|notes|documents")
    init.add_argument("--tier", default="auto", help="auto|large|balanced|light|api")
    init.add_argument("--language", default="auto", help="auto|en|multi")
    init.add_argument("--force", action="store_true", help="overwrite an existing config.toml")
    init.add_argument("--store", default="",
                      help="where db/state/cache live (default: inside .rag, or outside a sync container)")
    init.add_argument("--venv", default="", help="where the virtualenv lives (default: .rag/.venv)")
    init.add_argument("--no-relocate", action="store_true",
                      help="keep heavy data inside .rag even in a sync container")
    init.set_defaults(func=cmd_init)

    plan = sub.add_parser("plan", help="dry run: what would be indexed")
    plan.set_defaults(func=cmd_plan)

    index = sub.add_parser("index", help="build the index (heavy)")
    index.add_argument("--full", action="store_true", help="rebuild every file from scratch")
    index.add_argument("--limit", type=int, default=0, help="stop after N files (for a trial run)")
    index.add_argument("--quiet", action="store_true")
    index.set_defaults(func=cmd_index)

    update = sub.add_parser("update", help="index only what changed")
    update.add_argument("--quiet", action="store_true")
    update.set_defaults(func=cmd_update)

    search = sub.add_parser("search", help="hybrid search with citations")
    search.add_argument("query")
    search.add_argument("-k", type=int, default=0, help="how many hits (default: config top_k)")
    search.add_argument("--path", default="", help="glob against the path relative to its source")
    search.add_argument("--ext", default="", help="comma-separated extensions, e.g. .md,.pdf")
    search.add_argument("--source", default="", help="restrict to one configured source")
    search.add_argument("--since", default="", help="ISO date; only files modified since")
    search.add_argument("--no-rerank", action="store_true")
    search.add_argument("--no-hybrid", action="store_true", help="dense retrieval only")
    search.add_argument("--max-chars", type=int, default=700, help="truncate each hit's text")
    search.add_argument("--lines", type=int, default=8, help="text lines to print per hit")
    search.set_defaults(func=cmd_search)

    status = sub.add_parser("status", help="index size, staleness, drift")
    status.set_defaults(func=cmd_status)

    doctor = sub.add_parser("doctor", help="diagnose environment, deps, models, store")
    doctor.add_argument("--models", action="store_true", help="actually load the models (downloads)")
    doctor.add_argument("--extract", action="store_true", help="sample-extract real files")
    doctor.add_argument("--sample", type=int, default=12, help="files to sample for --extract")
    doctor.set_defaults(func=cmd_doctor)

    config_cmd = sub.add_parser("config", help="read and edit config.toml")
    config_cmd.add_argument("action", choices=["show", "get", "set"])
    config_cmd.add_argument("key", nargs="?", default="", help="dotted key, e.g. retrieval.top_k")
    config_cmd.add_argument("value", nargs="?", default="", help="new value, for 'set'")
    config_cmd.set_defaults(func=cmd_config)

    serve = sub.add_parser("serve", help="expose the index over MCP or a local web page")
    serve.add_argument("--mcp", action="store_true", help="MCP stdio server for agents")
    serve.add_argument("--web", action="store_true", help="local search page (the default)")
    serve.add_argument("--host", default="")
    serve.add_argument("--port", type=int, default=0)
    serve.set_defaults(func=cmd_serve)

    watch_cmd = sub.add_parser("watch", help="re-index on file change")
    watch_cmd.add_argument("--debounce", type=float, default=3.0, help="seconds to batch changes")
    watch_cmd.set_defaults(func=cmd_watch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("\ninterrupted — progress is saved; re-run the same command to resume.",
              file=sys.stderr)
        return 130
    except (SystemExit, BrokenPipeError):
        raise
    except Exception as exc:
        if getattr(args, "json", False):
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
