"""Register data (``register-data.html``): how every rule is coded, in one plain table.

Owner decision, 14 November 2026 (DECISIONS E-161): an advanced back end that records, for each law, requirement
and barrier, how it is coded, which sources are used, which industries it reaches and the other information held
about it. It is a working table, not a showpiece: one row for each item, every coded field a column, with a search
and a download.

The rows are the levers page's own rows (``explorer.build_payload``), flattened, so the two can't disagree. A
requirement shown inside a register item on the levers page has its own row here.
"""

from __future__ import annotations

from ..register import severity as S
from .growth import STATE_SHORT

TYPE_LABELS = {
    "requirement": "Requirement",
    "reform": "Reform",
    "setting": "Law or policy in place",
    "barrier": "Non-legislative barrier",
}
CHECKED_LABELS = {
    "register-text": "official register text",
    "document": "official document",
    "web-page": "web page",
    "corpus-copy": "corpus copy of the official text",
}
NOTE = (
    "One row for each item in the register: the requirements laws place on businesses, and the register's laws, "
    "policies and barriers. Marks are draft judgements against the productivity framework. Impact class and "
    "businesses reached are worked out from the marks and the ABS business counts. "
)


def _set_by(r: dict) -> str:
    j = "Cth" if r["jurisdiction"] == "CTH" else STATE_SHORT.get(r["jurisdiction"], r["jurisdiction"])
    return f"{r['council']} ({j})" if r.get("council") else j


def _row(r: dict, menu: dict, inside: str | None = None) -> dict:
    is_req = r["type"] == "requirement"
    a = r.get("assessment") or {}
    marks = {m["driver"]: m["mark"] for m in a.get("marks", [])}
    e = r.get("exposure") or {}
    bodies = menu["bodies"]
    if is_req:
        laws = [(x["title"], x.get("registerId"), x.get("provisions")) for x in r["laws"]]
        sources = r["sources"]
        checked = sorted({CHECKED_LABELS.get(s.get("checked"), s.get("checked") or "not stated") for s in sources})
        urls = sorted({s["url"] for s in sources if s.get("url")})
        sev = r.get("severity") or {}
        file = r["file"]
        industries = "All" if r["allIndustries"] else " ".join(r["industryCodes"])
    else:
        laws = [(x["title"], x.get("register_id"), x.get("provisions")) for x in r["instruments"]]
        urls = sorted({str(u) for u in (r.get("direction_sources") or [])} | {str(u) for u in a.get("evidence", [])})
        checked = ["dates checked against official sources"] if (r.get("verified") or {}).get("dates") else []
        sev = {}
        file = f"regulation-register/records/{r['id']}.json"
        industries = " ".join(i["anzsic"] for i in r["industries"]) or "All"
    return {
        "id": r["id"],
        "title": r["title"],
        "setBy": _set_by(r),
        "type": TYPE_LABELS["requirement" if is_req else r["kind"]],
        "kind": r.get("obligation") if is_req else "",
        "when": S.WHEN_LABELS[sev["when"]] if sev else "",
        "bound": S.BOUND_LABELS[sev["bound"]] if sev else "",
        "severity": sev.get("score"),
        "severityBand": S.BAND_LABELS[sev["band"]] if sev else "",
        "thresholds": sev.get("thresholds") if sev else None,
        "marks": [marks.get(d, 0) for d in menu["framework"]["drivers"]],
        "total": a.get("total"),
        "mainDriver": a.get("main_driver") or "",
        "impactClass": r.get("impactClass") or "",
        "standing": bool(r.get("standing")),
        "businesses": e.get("businesses"),
        "upTo": bool(e.get("partial")),
        "share": e.get("share"),
        "classes": "All" if e.get("allIndustries") else e.get("classes"),
        "industries": industries,
        "laws": "; ".join(f"{t}{f' ({i})' if i else ''}{f', {p}' if p else ''}" for t, i, p in laws),
        "sources": len(urls),
        "sourceUrls": urls,
        "checked": "; ".join(checked),
        "bodies": "; ".join((bodies.get(x["body"]) or {}).get("name", x["body"]) for x in r.get("responsible", [])),
        "family": (r.get("family") or "").removeprefix("req-"),
        "regimes": " ".join(r.get("regimes", [])),
        "confidence": (r.get("reachConfidence") if is_req else a.get("confidence")) or "",
        "review": (r.get("review") or {}).get("status", ""),
        "effective": r.get("effective") or "",
        "ended": bool(r.get("ended")),
        "inside": inside or "",
        "file": file,
    }


def payload(menu: dict) -> dict:
    rows = []
    for r in menu["records"]:
        rows.append(_row(r, menu))
        rows += [_row(q, menu, inside=r["id"]) for q in r.get("requirements", [])]
    # A requirement that sits inside two items is one row.
    seen, out = set(), []
    for x in rows:
        if x["id"] not in seen:
            seen.add(x["id"])
            out.append(x)
    return {
        "rows": out,
        "drivers": [
            {"id": k, "short": v["short"], "label": v["label"]} for k, v in menu["framework"]["drivers"].items()
        ],
        "classes": {c["id"]: c["label"] for c in menu.get("impactClasses", [])},
        "types": list(TYPE_LABELS.values()),
        "note": NOTE + (menu.get("exposureNote") or "") + " " + S.NOTE,
        "exposureYear": menu.get("exposureYear"),
        "generated": menu.get("generated"),
        "repo": None,
    }
