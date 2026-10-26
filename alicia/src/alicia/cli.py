"""Command line: ``alicia <command>``.

alicia validate                      check every register record and evaluation
alicia menu [filters]                list candidate changes, with an evaluability screen
alicia show <id>                     one record in full
alicia families                      reforms adopted by several jurisdictions, in date order
alicia dates <id>... | --all         gather effective dates and check them against registers
alicia explorer [-o file.html]       build the interactive menu explorer (one HTML file)
alicia site [-o dir]                 build the website: the menu plus the growth and conditions pages
alicia methods [-o file.md]          key insights and econometric methods of every evaluation, as Markdown
alicia tables [-o file.md] [--latex file.tex]   every evaluation's regression tables, as Markdown and LaTeX
alicia pipeline build <source>...    build outcome panels in data/processed (see alicia.pipeline.sources)
alicia pipeline catalogue            summarise every processed panel for coverage matching
alicia data <id>                     which data panels can measure a change, at what industry and area level
alicia spec list | show <id>         evaluation specifications (alicia/specs)
alicia spec run <id> [--stage ...]   run a specification's stages and check outputs reproduce byte for byte
alicia costing-params [--refresh] [--rebuild] [--strict] [--report file.md]   policy-costing parameters.json
alicia costing-register [-o file.json]   the register as the Policy costing tab's reference class
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from . import anzsic, cpi
from .register.catalogue import families, filter_records, load_records
from .register.evaluation import load_evaluations
from .register.schema import CHANNEL_LABELS, JURISDICTIONS, ChangeRecord


def _load(args) -> list[ChangeRecord]:
    result = load_records(Path(args.records) if args.records else None)
    if result.problems:
        print(f"{len(result.problems)} problem(s) in the register; run 'alicia validate'.", file=sys.stderr)
    return result.records


def cmd_validate(args) -> int:
    result = load_records(Path(args.records) if args.records else None)
    problems = list(result.problems)
    for r in result.records:
        for ind in r.industries:
            problems.extend(f"{r.id}.json: industries: {p}" for p in anzsic.check(ind.anzsic, ind.name))
    warnings = [
        f"{r.id}.json: price_series names no CPI expenditure class, group or subgroup: '{r.price_series}'"
        for r in result.records
        if r.price_series and not (cpi.matched_classes(r.price_series) or cpi.matched_aggregates(r.price_series))
    ]
    evals = load_evaluations(result.records, Path(args.evaluations) if args.evaluations else None)
    problems.extend(evals.problems)
    for p in problems:
        print(p)
    for w in warnings:
        print(f"warning: {w}")
    drafts = sum(r.review.status == "draft" for r in result.records)
    print(
        f"{len(result.records)} record(s) and {len(evals.evaluations)} evaluation(s) loaded; {len(problems)} "
        f"problem(s); {len(warnings)} warning(s); {drafts} record(s) awaiting review."
    )
    return 1 if problems else 0


def cmd_menu(args) -> int:
    from .menu.screen import screen_all

    all_records = _load(args)
    records = list(
        filter_records(
            all_records,
            jurisdiction=args.jurisdiction,
            direction=args.direction,
            channel=args.channel,
            industry=args.industry,
            family=args.family,
            text=args.text,
        )
    )
    screens = screen_all(all_records)
    rows = []
    for r in sorted(
        records,
        key=lambda r: (
            r.effective_commencement is None,
            r.effective_commencement.date if r.effective_commencement else None,
        ),
    ):
        s = screens[r.id]
        if args.rating and s.rating != args.rating:
            continue
        eff = r.effective_commencement
        rows.append(
            {
                "id": r.id,
                "jurisdiction": r.jurisdiction,
                "effective": eff.date.isoformat() if eff else "",
                "direction": r.direction,
                "industries": " ".join(i.anzsic for i in r.industries),
                "rating": s.rating,
                "title": r.title,
            }
        )
    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else ["id"])
        w.writeheader()
        w.writerows(rows)
        return 0
    for row in rows:
        print(
            f"{row['effective'] or 'not yet':10}  {row['jurisdiction']:3}  {row['direction']:9}  "
            f"{row['rating']:8}  {row['id']:38}  {row['title']}"
        )
    print(f"\n{len(rows)} change(s).")
    return 0


def cmd_show(args) -> int:
    from .menu.screen import screen_all

    records = _load(args)
    by_id = {r.id: r for r in records}
    rec = by_id.get(args.id)
    if rec is None:
        print(f"No record '{args.id}'.", file=sys.stderr)
        return 1
    s = screen_all(records)[rec.id]
    out = rec.model_dump(mode="json")
    out["evaluability"] = s.as_dict()
    out["channels_explained"] = [CHANNEL_LABELS[c] for c in rec.channels]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_families(args) -> int:
    for fam, members in families(_load(args)).items():
        print(fam)
        for r in members:
            eff = r.effective_commencement
            print(f"  {r.jurisdiction:3}  {eff.date.isoformat() if eff else 'not commenced':13}  {r.id}")
        missing = [j for j in JURISDICTIONS[1:] if j not in {r.jurisdiction for r in members}]
        if missing and all(r.jurisdiction != "CTH" for r in members):
            print(f"  (no record for: {', '.join(missing)})")
    return 0


def cmd_dates(args) -> int:
    from .legislation.adapters import adapter_for
    from .legislation.base import make_client
    from .legislation.gather import STATUS_HELP, gather

    records = _load(args)
    by_id = {r.id: r for r in records}
    chosen = records if args.all else [by_id[i] for i in args.ids if i in by_id]
    unknown = [i for i in args.ids if i not in by_id]
    if unknown:
        print(f"Unknown id(s): {', '.join(unknown)}", file=sys.stderr)
    client = None if args.offline else make_client()
    try:
        results = [gather(r, client, adapter_for) for r in chosen]
    finally:
        if client is not None:
            client.close()
    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2, ensure_ascii=False))
        return 0
    for res in results:
        t = res.timing.as_dict() if res.timing else {}
        print(f"{res.record_id}  [{res.status}: {STATUS_HELP[res.status]}]")
        print(
            f"  effective {t.get('effective_date', 'n/a')}  first exposed FY {t.get('first_exposed_fy', 'n/a')}"
            f" ({t.get('exposure_share_first_fy', '')} of the year)  first full FY {t.get('first_full_fy', 'n/a')}"
            f"  first full quarter {t.get('first_full_quarter', 'n/a')}"
        )
        for issue in res.issues:
            print(f"  ! {issue}")
    return 0


def cmd_explorer(args) -> int:
    from .menu.explorer import build_explorer

    out = Path(args.output)
    report = Path(args.dates) if args.dates else None
    records = _load(args)
    evals = load_evaluations(records, Path(args.evaluations) if args.evaluations else None)
    if evals.problems:
        print(f"{len(evals.problems)} problem(s) in the evaluations; run 'alicia validate'.", file=sys.stderr)
    build_explorer(
        records,
        out,
        dates_report=report,
        standalone=args.standalone,
        evaluations=evals.evaluations,
        repo_base=args.repo_base,
    )
    print(f"Wrote {out}")
    return 0


def cmd_methods(args) -> int:
    from .register.evaluation import methods_markdown

    records = _load(args)
    evals = load_evaluations(records, Path(args.evaluations) if args.evaluations else None)
    text = methods_markdown(evals.evaluations)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


def cmd_tables(args) -> int:
    from .register.tables import tables_latex, tables_markdown

    records = _load(args)
    evals = load_evaluations(records, Path(args.evaluations) if args.evaluations else None).evaluations
    text = tables_markdown(evals)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    if args.latex:
        Path(args.latex).write_text(tables_latex(evals), encoding="utf-8")
        print(f"Wrote {args.latex}")
    return 0


def cmd_site(args) -> int:
    from .menu.growth import build_site

    records = _load(args)
    evals = load_evaluations(records, Path(args.evaluations) if args.evaluations else None)
    if evals.problems:
        print(f"{len(evals.problems)} problem(s) in the evaluations; run 'alicia validate'.", file=sys.stderr)
    paths = build_site(
        Path(args.output),
        records,
        evals.evaluations,
        dates_report=Path(args.dates) if args.dates else None,
        standalone=not args.fragment,
        repo_base=args.repo_base,
        costing_dist=Path(args.costing) if args.costing else None,
    )
    for p in paths:
        print(f"Wrote {p}")
    return 0


BUILDERS = {
    "abs_cabee": "alicia.pipeline.abs_cabee",
    "abs_cabee_local": "alicia.pipeline.abs_cabee_local",
    "abs_retail": "alicia.pipeline.abs_retail",
    "abs_lfs": "alicia.pipeline.abs_lfs",
    "abs_regional": "alicia.pipeline.abs_regional",
    "abs_asgs": "alicia.pipeline.geo",
    "abr_abn": "alicia.pipeline.abr_abn",
    "asic": "alicia.pipeline.asic",
    "clue_melbourne": "alicia.pipeline.clue",
    "jsa_ivi": "alicia.pipeline.jsa_ivi",  # needs workbooks saved by hand in data/raw/jsa_ivi/
    "abs_state_accounts": "alicia.pipeline.abs_state_accounts",
    "ato_company": "alicia.pipeline.ato_company",
    "controls": "alicia.pipeline.controls",  # macroeconomic controls, written to data/processed/controls/
}


def cmd_pipeline(args) -> int:
    import importlib

    from .pipeline import coverage

    if args.action == "build":
        names = args.sources or list(BUILDERS)
        for name in names:
            if name not in BUILDERS:
                print(f"unknown source '{name}'; known: {', '.join(BUILDERS)}", file=sys.stderr)
                return 2
            panel = importlib.import_module(BUILDERS[name]).build()
            rows = sum(map(len, panel.values())) if isinstance(panel, dict) else len(panel)
            print(f"{name}: {rows:,} rows")
    entries = coverage.build_catalogue()
    print(f"catalogue: {len(entries)} measure(s) across {len({(e['source'], e['table']) for e in entries})} panel(s)")
    return 0


def cmd_data(args) -> int:
    from .pipeline.coverage import coverage

    records = {r.id: r for r in _load(args)}
    rec = records.get(args.id)
    if rec is None:
        print(f"no record '{args.id}'", file=sys.stderr)
        return 2
    matches = coverage(rec)
    if not matches:
        print("No processed panel covers this change's industries. Run 'alicia pipeline build'.")
        return 0
    print(f"{rec.id} ({rec.jurisdiction}): {', '.join(i.anzsic for i in rec.industries)}")
    for m in matches:
        where = "state" if m.state else "not by state"
        local = f"; local: {', '.join(m.local_levels)}" if m.local_levels else ""
        code = f" {m.matched_code}" if m.matched_code else ""
        print(
            f"  {m.industry}: {m.source}/{m.measure} at {m.matched_level}{code}, {where}{local}, "
            f"{m.period_type} {m.first} to {m.last}"
        )
    return 0


def cmd_spec(args) -> int:
    from .register.evaluation import default_evaluations_dir
    from .runner import run as runner
    from .runner.spec import load, load_all

    if args.action == "list":
        specs, problems = load_all()
        for s in specs:
            stages = ", ".join(st.name for st in s.stages)
            print(f"{s.id:45} {s.analysis:20} {len(s.evaluations)} evaluation(s); stages: {stages}")
        for msg in problems:
            print(f"PROBLEM {msg}", file=sys.stderr)
        return 1 if problems else 0
    if not args.id:
        print("give a specification id", file=sys.stderr)
        return 2
    spec = load(args.id)
    if args.action == "show":
        print(json.dumps(spec.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0
    if args.action == "check":
        records = {r.id for r in _load(args)}
        missing = [r for r in spec.records if r not in records]
        evals = default_evaluations_dir()
        absent = [e for e in spec.evaluations if not (evals / f"{e}.json").exists()]
        for msg in [f"record {r} not in the register" for r in missing] + [f"evaluation {e} not found" for e in absent]:
            print(msg)
        return 1 if missing or absent else 0
    try:
        results = runner.run(spec, args.stage or None, allow_uncommitted_design=args.allow_uncommitted_design)
    except (PermissionError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    ok = all(r.reproduced for r in results)
    changed = [o.path for r in results for o in r.outputs if o.status != "identical"]
    if ok:
        print("REPRODUCED: every output byte-identical")
    else:
        print(f"NOT REPRODUCED: {', '.join(changed) or 'a stage failed'}")
    return 0 if ok else 1


def cmd_costing_params(args) -> int:
    from .costing import params

    return params.run(
        refresh=args.refresh, rebuild=args.rebuild, strict=args.strict, report=args.report, only=args.source or None
    )


def cmd_costing_register(args) -> int:
    from .costing import register

    records = _load(args)
    evals = load_evaluations(records, Path(args.evaluations) if args.evaluations else None)
    if evals.problems:
        print(f"{len(evals.problems)} problem(s) in the evaluations; run 'alicia validate'.", file=sys.stderr)
    path = register.write(records, evals.evaluations, Path(args.output) if args.output else None)
    print(f"Wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="alicia", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--records", help="folder of register records (default: regulation-register/records)")
    p.add_argument("--evaluations", help="folder of evaluation results (default: regulation-register/evaluations)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="check every register record").set_defaults(func=cmd_validate)

    m = sub.add_parser("menu", help="list candidate changes with an evaluability screen")
    m.add_argument("--jurisdiction", choices=[j.lower() for j in JURISDICTIONS] + list(JURISDICTIONS))
    m.add_argument("--direction", choices=["enhancing", "weakening", "mixed", "unclear"])
    m.add_argument("--channel", choices=list(CHANNEL_LABELS))
    m.add_argument("--industry", help="ANZSIC code or prefix, e.g. 4623 or 46")
    m.add_argument("--family")
    m.add_argument("--rating", choices=["high", "medium", "low", "not-yet"])
    m.add_argument("--text", help="search titles and summaries")
    m.add_argument("--csv", action="store_true", help="CSV output")
    m.set_defaults(func=cmd_menu)

    s = sub.add_parser("show", help="one record in full, with its evaluability screen")
    s.add_argument("id")
    s.set_defaults(func=cmd_show)

    sub.add_parser("families", help="multi-jurisdiction reforms in date order").set_defaults(func=cmd_families)

    d = sub.add_parser("dates", help="gather effective dates and check them against registers")
    d.add_argument("ids", nargs="*")
    d.add_argument("--all", action="store_true")
    d.add_argument("--offline", action="store_true", help="don't contact registers; use sourced dates only")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_dates)

    e = sub.add_parser("explorer", help="build the interactive menu explorer (one HTML file)")
    e.add_argument("-o", "--output", default="regulation-menu.html")
    e.add_argument("--dates", help="a report from 'alicia dates --all --json', to show register checks")
    e.add_argument("--standalone", action="store_true", help="wrap in a full HTML document for local viewing")
    e.add_argument("--repo-base", default=None, help="URL that evaluation document paths are linked under")
    e.set_defaults(func=cmd_explorer)

    si = sub.add_parser("site", help="build the website: legislation menu, growth and conditions pages")
    si.add_argument(
        "-o", "--output", default="site", help="directory to write index.html, growth.html, conditions.html"
    )
    si.add_argument("--dates", help="a report from 'alicia dates --all --json', to show register checks")
    si.add_argument("--fragment", action="store_true", help="write page fragments instead of full HTML documents")
    si.add_argument("--repo-base", default=None, help="URL that repository paths are linked under")
    si.add_argument(
        "--costing",
        default=None,
        help="the Policy costing build to add (regulatory-burden-tool/dist-site, from 'npm run build:site')",
    )
    si.set_defaults(func=cmd_site)

    me = sub.add_parser("methods", help="key insights and methods of every evaluation, as Markdown")
    me.add_argument("-o", "--output", help="file to write (default: print)")
    me.set_defaults(func=cmd_methods)

    ta = sub.add_parser("tables", help="every evaluation's regression tables, as Markdown (and LaTeX)")
    ta.add_argument("-o", "--output", help="Markdown file to write (default: print)")
    ta.add_argument("--latex", help="also write the tables as LaTeX to this file")
    ta.set_defaults(func=cmd_tables)

    pl = sub.add_parser("pipeline", help="build outcome panels and the coverage catalogue")
    pl.add_argument("action", choices=["build", "catalogue"])
    pl.add_argument("sources", nargs="*")
    pl.set_defaults(func=cmd_pipeline)

    dt_ = sub.add_parser("data", help="which data panels can measure a change")
    dt_.add_argument("id")
    dt_.set_defaults(func=cmd_data)

    sp = sub.add_parser("spec", help="evaluation specifications and the runner")
    sp.add_argument("action", choices=["list", "show", "check", "run"])
    sp.add_argument("id", nargs="?")
    sp.add_argument("--stage", action="append", help="run only this stage (repeatable)")
    sp.add_argument(
        "--allow-uncommitted-design",
        action="store_true",
        help="run the registered estimate even if design outputs are not committed (for checks only)",
    )
    sp.set_defaults(func=cmd_spec)

    cp = sub.add_parser("costing-params", help="merge (and refresh) the policy-costing parameters.json")
    cp.add_argument("--refresh", action="store_true", help="download and rebuild sources with a newer release")
    cp.add_argument("--rebuild", action="store_true", help="rebuild sources whose raw files are present locally")
    cp.add_argument("--strict", action="store_true", help="exit non-zero if any source fails or is missing")
    cp.add_argument("--report", help="write a Markdown summary of the run to this file")
    cp.add_argument("--source", action="append", help="limit the refresh or rebuild to this source (repeatable)")
    cp.set_defaults(func=cmd_costing_params)

    cr = sub.add_parser("costing-register", help="export the register for the Policy costing tab")
    cr.add_argument("-o", "--output", help="file to write (default: data/processed/costing/register.json)")
    cr.set_defaults(func=cmd_costing_register)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
