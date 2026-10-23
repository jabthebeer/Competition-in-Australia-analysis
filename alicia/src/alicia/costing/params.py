"""``alicia costing-params``: refresh, rebuild and merge the per-source files into ``parameters.json``.

- **merge** (always): every committed per-source file in ``data/processed/costing/sources/`` is merged into
  ``data/processed/costing/parameters.json``. Nothing is downloaded.
- **--rebuild**: before merging, rebuild each source whose raw files (as listed in its per-source file) are
  present in ``data/raw/<source>/``.
- **--refresh**: before merging, ask each source for its latest release. When it differs from (and is not older
  than) the committed release, download only that source's files, build and replace its per-source file. When
  discovery, download or parsing fails, the committed file is kept and the source is marked ``fallback`` in
  ``parameters.json``; a warning is printed and the exit code stays 0 unless ``--strict``.

Only an updated source is downloaded, so the refresh works without ``data/raw/`` (as in CI).
"""

from __future__ import annotations

import importlib
import sys
import traceback
from dataclasses import dataclass

from . import base

# Connectors in priority order (forward plan §7 and the P2 brief).
CONNECTORS = (
    "abs_anzsic",
    "abs_asna",
    "abs_mfp",
    "abs_australian_industry",
)


def _log(msg: str, err: bool = False) -> None:
    print(msg, file=sys.stderr if err else sys.stdout)


def load_connectors(only: list[str] | None = None) -> list:
    names = list(CONNECTORS)
    if only:
        unknown = [n for n in only if n not in names]
        if unknown:
            raise ValueError(f"unknown source(s) {unknown}; known: {', '.join(names)}")
        names = [n for n in names if n in only]
    return [importlib.import_module(f"{__package__}.{n}") for n in names]


def document(conn, release: base.Release) -> dict:
    """The connector's per-source document (its own ``document`` hook, or the standard one)."""
    if hasattr(conn, "document"):
        return conn.document(release)
    return base.source_doc(conn.SOURCE, release, conn.build(release))


@dataclass
class Outcome:
    source: str
    state: str  # "updated", "new", "unchanged", "rebuilt", "skipped", "failed"
    old: str | None = None
    new: str | None = None
    reason: str = ""

    @property
    def failed(self) -> bool:
        return self.state == "failed"


def _release_id(doc: dict | None) -> str | None:
    return doc["release"]["id"] if doc else None


def _short(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}".splitlines()[0][:300]


def refresh_one(conn, log=_log) -> Outcome:
    sid = conn.SOURCE.id
    old = base.read_source_doc(sid)
    try:
        release = conn.discover()
    except Exception as exc:  # noqa: BLE001 - any failure falls back to the committed file
        return Outcome(sid, "failed", _release_id(old), None, f"discovery failed: {_short(exc)}")
    if not base.is_newer(release, old):
        return Outcome(sid, "unchanged", _release_id(old), release.id)
    try:
        conn.fetch(release)
        doc = document(conn, release)
    except Exception as exc:  # noqa: BLE001
        log(traceback.format_exc(), err=True)
        return Outcome(sid, "failed", _release_id(old), release.id, f"download or build failed: {_short(exc)}")
    base.write_json(base.source_path(sid), doc)
    return Outcome(sid, "new" if old is None else "updated", _release_id(old), release.id)


def rebuild_one(conn) -> Outcome:
    sid = conn.SOURCE.id
    old = base.read_source_doc(sid)
    if old is None:
        return Outcome(sid, "skipped", None, None, "no committed per-source file; run with --refresh")
    release = base.Release.from_json(old["release"])
    if not base.have_files(conn.SOURCE, release):
        return Outcome(sid, "skipped", release.id, release.id, "raw files not present locally")
    try:
        doc = document(conn, release)
    except Exception as exc:  # noqa: BLE001
        return Outcome(sid, "failed", release.id, release.id, f"build failed: {_short(exc)}")
    changed = base.dumps(doc) != base.dumps(old)
    base.write_json(base.source_path(sid), doc)
    return Outcome(sid, "rebuilt", release.id, release.id, "changed" if changed else "identical")


def merge(conns: list, fallback: set[str] = frozenset()) -> dict:
    """parameters.json from every per-source file present (sources in priority order, tables by id)."""
    sources, tables = [], {}
    for conn in conns:
        sid = conn.SOURCE.id
        doc = base.read_source_doc(sid)
        if doc is None:
            continue
        rel = doc["release"]
        files = [{"url": f["url"], "sha256": f["sha256"]} for f in doc["files"]]
        files += [{"url": d["from"], "sha256": d["sha256"]} for d in doc.get("derived_from", [])]
        sources.append(
            {
                "id": sid,
                "title": doc["source"]["title"],
                "publisher": doc["source"]["publisher"],
                "licence": doc["source"]["licence"],
                "release": rel["id"],
                "release_date": rel["date"],
                "next_release": rel["next_release"],
                "url": rel["page"],
                "files": files,
                "retrieved": doc["retrieved"],
                "status": "fallback" if sid in fallback else "current",
            }
        )
        for name, t in doc["tables"].items():
            tables[f"{sid}.{name}"] = {
                "source": sid,
                "description": t["description"],
                "columns": t["columns"],
                "rows": t["rows"],
            }
    dates = [s["release_date"] for s in sources if s["release_date"]]
    return {
        "schema": base.PARAMS_SCHEMA,
        "version": base.VERSION,
        "vintage": max(dates) if dates else None,
        "sources": sources,
        "tables": dict(sorted(tables.items())),
    }


def params_path():
    return base.costing_dir() / "parameters.json"


def report_markdown(outcomes: list[Outcome], params: dict, missing: list[str]) -> str:
    size = params_path().stat().st_size if params_path().exists() else 0
    lines = [
        "## Costing parameters",
        "",
        f"`parameters.json`: {len(params['sources'])} sources, {len(params['tables'])} tables, "
        f"{size / 1e6:.2f} MB; vintage {params['vintage']}.",
        "",
    ]
    if outcomes:
        lines += ["| Source | Release | Outcome |", "|---|---|---|"]
        for o in outcomes:
            if o.state in ("updated", "new"):
                release, what = f"{o.old or '(none)'} → {o.new}", o.state
            elif o.state == "failed":
                release, what = o.old or "(none)", f"failed: {o.reason}"
            else:
                release, what = o.old or "(none)", o.state + (f" ({o.reason})" if o.reason else "")
            lines.append(f"| `{o.source}` | {release} | {what.replace('|', '/')} |")
        lines.append("")
    if missing:
        lines += [f"Not built (no per-source file): {', '.join(f'`{m}`' for m in missing)}.", ""]
    return "\n".join(lines)


def run(
    refresh: bool = False,
    rebuild: bool = False,
    strict: bool = False,
    report: str | None = None,
    only: list[str] | None = None,
    conns: list | None = None,
    log=_log,
) -> int:
    """Run the command; returns the exit code. ``conns`` replaces the registered connectors (for tests)."""
    every = conns if conns is not None else load_connectors(None)
    conns = conns if conns is not None else load_connectors(only)
    outcomes: list[Outcome] = []
    if rebuild:
        for conn in conns:
            o = rebuild_one(conn)
            outcomes.append(o)
            log(f"{o.source}: {o.state}" + (f" ({o.reason})" if o.reason else ""))
    if refresh:
        for conn in conns:
            o = refresh_one(conn, log=log)
            outcomes.append(o)
            if o.failed:
                log(f"warning: {o.source}: {o.reason}; keeping the committed file", err=True)
            elif o.state in ("updated", "new"):
                log(f"{o.source}: {o.old or '(none)'} -> {o.new}")
            else:
                log(f"{o.source}: unchanged ({o.old})")
    failed = {o.source for o in outcomes if o.failed}
    params = merge(every, fallback=failed)
    base.write_json(params_path(), params)
    missing = [c.SOURCE.id for c in every if base.read_source_doc(c.SOURCE.id) is None]
    log(f"wrote {params_path()}: {len(params['sources'])} sources, {len(params['tables'])} tables")
    for m in missing:
        log(f"warning: {m}: not built (no per-source file)", err=True)
    if report:
        from pathlib import Path

        Path(report).write_text(report_markdown(outcomes, params, missing), encoding="utf-8")
    return 1 if strict and (failed or missing) else 0
