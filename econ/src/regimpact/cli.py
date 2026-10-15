"""Command line: ``regimpact <command>``.

regimpact validate                      check every register record
regimpact menu [filters]                list candidate changes, with an evaluability screen
regimpact show <id>                     one record in full
regimpact families                      reforms adopted by several jurisdictions, in date order
regimpact dates <id>... | --all         gather effective dates and check them against registers
regimpact explorer [-o file.html]       build the interactive menu explorer (one HTML file)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from . import anzsic, cpi
from .register.catalogue import families, filter_records, load_records
from .register.schema import CHANNEL_LABELS, JURISDICTIONS, ChangeRecord


def _load(args) -> list[ChangeRecord]:
    result = load_records(Path(args.records) if args.records else None)
    if result.problems:
        print(f"{len(result.problems)} problem(s) in the register; run 'regimpact validate'.", file=sys.stderr)
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
    for p in problems:
        print(p)
    for w in warnings:
        print(f"warning: {w}")
    drafts = sum(r.review.status == "draft" for r in result.records)
    print(
        f"{len(result.records)} record(s) loaded; {len(problems)} problem(s); {len(warnings)} warning(s); "
        f"{drafts} awaiting review."
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
    build_explorer(_load(args), out, dates_report=report, standalone=args.standalone)
    print(f"Wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="regimpact", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--records", help="folder of register records (default: regulation-register/records)")
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
    e.add_argument("--dates", help="a report from 'regimpact dates --all --json', to show register checks")
    e.add_argument("--standalone", action="store_true", help="wrap in a full HTML document for local viewing")
    e.set_defaults(func=cmd_explorer)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
