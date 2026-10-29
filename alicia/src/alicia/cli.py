"""Command line: ``alicia <command>``.

alicia validate                      check every register record (assessment, responsible bodies, history), evaluation
alicia menu [filters]                list register items with their framework marks
alicia recommendations [filters]     what government could do about register items, with their sources
alicia industries [--class] [--division]   regulatory regimes and complexity measures for each ANZSIC class
alicia show <id>                     one record in full
alicia families                      reforms adopted by several jurisdictions, in date order
alicia dates <id>... | --all         gather effective dates and check them against registers
alicia explorer [-o file.html]       build the legislation menu (one HTML file)
alicia site [-o dir]                 build the website: the menu, framework, archive, growth and conditions pages
alicia framework [-o file.md]        the productivity impact framework as a methods note
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
from .register.bodies import check_records, department_of, load_bodies
from .register.catalogue import families, filter_records, load_records
from .register.evaluation import load_evaluations
from .register.families import check_families, load_families
from .register.framework import DRIVERS, KINDS
from .register.recommendations import check_coverage, check_recommendations, load_gaps, load_recommendations
from .register.regimes import check_regimes, load_regimes
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
    problems.extend(
        f"{r.id}.json: assessment: every item needs a framework assessment"
        for r in result.records
        if r.assessment is None
    )
    evals = load_evaluations(result.records, Path(args.evaluations) if args.evaluations else None)
    problems.extend(evals.problems)
    bodies, body_problems = load_bodies()
    problems.extend(body_problems)
    problems.extend(check_records(result.records, bodies))
    recs = load_recommendations()
    problems.extend(recs.problems)
    problems.extend(check_recommendations(recs.recommendations, result.records, bodies))
    warnings.extend(check_coverage(recs.recommendations, result.records, load_gaps()))
    regimes = load_regimes()
    problems.extend(regimes.problems)
    problems.extend(check_regimes(regimes.regimes, result.records, bodies))
    families, family_problems = load_families()
    problems.extend(family_problems)
    problems.extend(check_families(families, result.records))
    ids = {r.id for r in result.records}
    problems.extend(
        f"{r.id}.json: history: unknown record '{h.record}'"
        for r in result.records
        for h in r.history
        if h.record and h.record not in ids
    )
    for p in problems:
        print(p)
    for w in warnings:
        print(f"warning: {w}")
    drafts = sum(r.review.status == "draft" for r in result.records)
    print(
        f"{len(result.records)} record(s), {len(evals.evaluations)} evaluation(s), "
        f"{len(recs.recommendations)} recommendation(s) and {len(regimes.regimes)} regime(s) loaded; {len(problems)} "
        f"problem(s); {len(warnings)} warning(s); {drafts} record(s) awaiting review."
    )
    return 1 if problems else 0


def _dept_short(body: str, bodies: dict) -> str:
    """The short name of the department a body sits in (or of the body, if it has none)."""
    b = bodies.get(body)
    if b is None:
        return body
    d = department_of(b, bodies)
    return (d or b).short


def cmd_menu(args) -> int:
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
    bodies = load_bodies()[0]
    if args.body and args.body not in bodies:
        print(f"Unknown body '{args.body}'; ids are in regulation-register/bodies.json.", file=sys.stderr)
        return 2
    rows = []
    for r in sorted(
        records,
        key=lambda r: (
            r.effective_commencement is None,
            r.effective_commencement.date if r.effective_commencement else None,
        ),
    ):
        a = r.assessment
        if args.driver and not (a and a.main_driver == args.driver):
            continue
        if args.kind and r.kind != args.kind:
            continue
        if args.body and not any(
            x.body == args.body or (x.body in bodies and bodies[x.body].parent == args.body) for x in r.responsible
        ):
            continue
        eff = r.effective_commencement
        rows.append(
            {
                "id": r.id,
                "kind": r.kind,
                "jurisdiction": r.jurisdiction,
                "effective": eff.date.isoformat() if eff else "",
                "main_driver": a.main_driver if a else "",
                "mark": f"{a.total:+d}" if a else "",
                "rating": a.rating if a else "",
                "industries": " ".join(i.anzsic for i in r.industries),
                "responsible": " ".join(dict.fromkeys(_dept_short(x.body, bodies) for x in r.responsible)),
                "ended": r.ended.date.isoformat() if r.ended else "",
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
            f"{row['effective'] or '-':10}  {row['jurisdiction']:3}  {row['mark']:>3}  {row['main_driver']:18}  "
            f"{row['id']:42}  {row['title']}"
        )
    print(f"\n{len(rows)} item(s).")
    return 0


def cmd_recommendations(args) -> int:
    from .register.recommendations import KIND_LABELS, actors_of

    records = {r.id: r for r in _load(args)}
    recs = load_recommendations().recommendations
    bodies = load_bodies()[0]
    rows = []
    for rec in recs:
        actors = actors_of(rec, records)
        if args.record and args.record not in rec.applies_to:
            continue
        if args.kind and rec.kind != args.kind:
            continue
        if args.body and not any(a == args.body or (a in bodies and bodies[a].parent == args.body) for a in actors):
            continue
        rows.append(
            {
                "id": rec.id,
                "kind": rec.kind,
                "items": len(rec.applies_to),
                "confidence": rec.confidence,
                "actors": " ".join(dict.fromkeys(_dept_short(a, bodies) for a in actors)),
                "sources": len(rec.evidence),
                "title": rec.title,
            }
        )
    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else ["id"])
        w.writeheader()
        w.writerows(rows)
        return 0
    for row in rows:
        print(f"{KIND_LABELS[row['kind']][:26]:26}  {row['items']:>3} item(s)  {row['id']:48}  {row['title']}")
    print(f"\n{len(rows)} recommendation(s).")
    return 0


def cmd_industries(args) -> int:
    from .register.regimes import CONSISTENCY_LABELS, ISSUE_LABELS, industry_profiles, regimes_by_class

    regimes = load_regimes().regimes
    if args.anzsic:
        regs = regimes_by_class(regimes).get(args.anzsic)
        if regs is None:
            print(f"No ANZSIC class '{args.anzsic}'.", file=sys.stderr)
            return 2
        print(f"{args.anzsic} {anzsic.name(args.anzsic)}: {len(regs)} regime(s)")
        for r in sorted(regs, key=lambda r: (r.scope != "sector", r.name)):
            tags = ", ".join(dict.fromkeys(ISSUE_LABELS[i.tag] for i in r.issues if i.status != "addressed"))
            print(f"  {r.name:60} {CONSISTENCY_LABELS[r.consistency][:38]:38}  {', '.join(r.tiers):16}  {tags}")
        return 0
    rows = [p for p in industry_profiles(regimes) if not args.division or p["division"] == args.division.upper()]
    rows.sort(key=lambda p: (-p["sector_touchpoints"], -p["issues"], p["anzsic"]))
    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else ["anzsic"])
        w.writeheader()
        w.writerows(rows)
        return 0
    print(
        f"{'class':5}  {'regimes':>7}  {'touch':>5}  {'vary':>4}  {'overlap':>7}  {'issues':>6}  "
        "name (industry-specific counts)"
    )
    for p in rows:
        print(
            f"{p['anzsic']:5}  {p['sector_regimes']:>7}  {p['sector_touchpoints']:>5}  {p['sector_varying']:>4}  "
            f"{p['sector_overlapping']:>7}  {p['issues']:>6}  {p['name']}"
        )
    print(f"\n{len(rows)} class(es).")
    return 0


def cmd_show(args) -> int:
    from .menu.screen import screen_all

    records = _load(args)
    by_id = {r.id: r for r in records}
    rec = by_id.get(args.id)
    if rec is None:
        print(f"No record '{args.id}'.", file=sys.stderr)
        return 1
    out = rec.model_dump(mode="json")
    if rec.assessment:
        out["assessment"] |= {"total": rec.assessment.total, "rating": rec.assessment.rating}
    if rec.kind == "reform":
        out["evaluability"] = screen_all([r for r in records if r.kind == "reform"])[rec.id].as_dict()
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
    build_explorer(records, out, dates_report=report, standalone=args.standalone, evaluations=evals.evaluations)
    print(f"Wrote {out}")
    return 0


def cmd_framework(args) -> int:
    from .register.framework import markdown

    text = markdown()
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
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

    m = sub.add_parser("menu", help="list register items with their framework marks")
    m.add_argument("--jurisdiction", choices=[j.lower() for j in JURISDICTIONS] + list(JURISDICTIONS))
    m.add_argument("--direction", choices=["enhancing", "weakening", "mixed", "unclear"])
    m.add_argument("--channel", choices=list(CHANNEL_LABELS))
    m.add_argument("--industry", help="ANZSIC code or prefix, e.g. 4623 or 46")
    m.add_argument("--family")
    m.add_argument("--driver", choices=list(DRIVERS), help="main driver of productivity impact")
    m.add_argument("--kind", choices=list(KINDS), help="reform, existing setting or non-legislative barrier")
    m.add_argument(
        "--body", help="department or agency id (regulation-register/bodies.json); a department includes its agencies"
    )
    m.add_argument("--text", help="search titles and summaries")
    m.add_argument("--csv", action="store_true", help="CSV output")
    m.set_defaults(func=cmd_menu)

    rc = sub.add_parser("recommendations", help="what government could do about register items, with sources")
    rc.add_argument("--record", help="only recommendations that apply to this record id")
    rc.add_argument("--body", help="department or agency id that would act (a department includes its agencies)")
    rc.add_argument("--kind", choices=["remove", "reform", "replace", "extend", "harmonise", "review", "keep"])
    rc.add_argument("--csv", action="store_true", help="CSV output")
    rc.set_defaults(func=cmd_recommendations)

    ind = sub.add_parser("industries", help="regulatory regimes and complexity measures for each ANZSIC class")
    ind.add_argument("--class", dest="anzsic", help="one ANZSIC class (4 digits): list its regimes")
    ind.add_argument("--division", help="ANZSIC division letter")
    ind.add_argument("--csv", action="store_true", help="CSV output")
    ind.set_defaults(func=cmd_industries)

    s = sub.add_parser("show", help="one record in full, with its assessment (and, for reforms, evaluability screen)")
    s.add_argument("id")
    s.set_defaults(func=cmd_show)

    sub.add_parser("families", help="multi-jurisdiction reforms in date order").set_defaults(func=cmd_families)

    d = sub.add_parser("dates", help="gather effective dates and check them against registers")
    d.add_argument("ids", nargs="*")
    d.add_argument("--all", action="store_true")
    d.add_argument("--offline", action="store_true", help="don't contact registers; use sourced dates only")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_dates)

    e = sub.add_parser("explorer", help="build the legislation menu (one HTML file)")
    e.add_argument("-o", "--output", default="regulation-menu.html")
    e.add_argument("--dates", help="a report from 'alicia dates --all --json', to show register checks")
    e.add_argument("--standalone", action="store_true", help="wrap in a full HTML document for local viewing")
    e.set_defaults(func=cmd_explorer)

    fr = sub.add_parser("framework", help="the productivity impact framework as a methods note (Markdown)")
    fr.add_argument("-o", "--output", help="file to write (default: print)")
    fr.set_defaults(func=cmd_framework)

    si = sub.add_parser("site", help="build the website: legislation menu, framework, archive, growth and conditions")
    si.add_argument(
        "-o",
        "--output",
        default="site",
        help="directory to write index.html, framework.html, archive.html, growth.html, conditions.html",
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
