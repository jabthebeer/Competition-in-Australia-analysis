"""Phase C, step 1: the catalogue of Commonwealth laws in force, from the Federal Register of Legislation API.

Lists every principal Act and legislative instrument in force (``isInForce eq true``, keeping ``isPrincipal``), with
its register ID, name, year and making date, and applies the title triage of methods rule 10: series that never
oblige businesses directly (appropriations, airworthiness directives, tariff concession orders, appointments and the
like) are set aside with the reason. The rest are left for screening: each gets a call (Y creates a requirement,
L supports one, P planning, N no business obligation) as phase C works through it. Calls already made are kept
when the catalogue is rebuilt.

Writes data/processed/legislation/cth_catalogue.csv (metadata only, no law texts) and records the query in
data/manifests/frl_catalogue.json.

Usage (in alicia/):  uv run python scripts/frl_catalogue.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.prod.legislation.gov.au/v1"
HEADERS = {"User-Agent": "alicia-research/0.1 (non-commercial research)"}
OUT = ROOT / "data" / "processed" / "legislation" / "cth_catalogue.csv"
MANIFEST = ROOT / "data" / "manifests" / "frl_catalogue.json"
PAGE, PAUSE = 500, 5.0  # the API caps $top at 500
FIELDS = ["register_id", "name", "collection", "year", "number", "making_date", "triage", "call", "requirements", "reason"]
# Title triage (methods rule 10): series that set nothing for businesses to do, or one-off decisions about named
# parties. Anything not matched goes to screening.
TRIAGE = [
    (r"\bAppropriation\b", "appropriation"),
    (r"^AD/|Airworthiness Directive", "airworthiness directive (aircraft-specific technical order)"),
    (r"Tariff Concession Order", "tariff concession order (one product)"),
    (r"Appointment|Delegation|Authorisation of (an )?officer", "appointment or delegation"),
    (r"Statement of Principles", "veterans' statement of principles"),
    (r"Determination of (an )?Australian Standard|Declaration of (a )?(Defence|Prohibited) Area", "declaration about a place"),
    (r"Defence (Determination|\(Defence Area)|Defence Force", "defence personnel or areas"),
    (r"Superannuation \((CSS|PSS)|Commonwealth Superannuation|Military Superannuation", "government superannuation"),
    (r"Remuneration Tribunal|Parliamentary (Entitlements|Business Resources)", "public office pay and entitlements"),
    (r"Exemption \(.*\) (No\.|Instrument)|\bEX\d+", "exemption for named parties"),
    (r"Licence Area Plan", "spectrum planning"),
    (r"Seat of Government|Acceptance Act", "territory or constitutional machinery"),
]


def fetch(collection: str) -> list[dict]:
    rows, skip = [], 0
    # The API fails when isInForce and isPrincipal are combined in one filter, so principal titles are kept here.
    flt = f"collection eq '{collection}' and isInForce eq true"
    while True:
        params = {"$filter": flt, "$select": "id,name,collection,year,number,makingDate,isPrincipal", "$orderby": "id", "$top": PAGE, "$skip": skip, "$count": "true"}
        time.sleep(PAUSE)
        r = httpx.get(f"{API}/Titles", params=params, headers=HEADERS, timeout=120)
        r.raise_for_status()
        data = r.json()
        rows += [t for t in data["value"] if t.get("isPrincipal")]
        seen = skip + len(data["value"])
        print(f"  {collection}: {seen:,} of {data.get('@odata.count', 0):,} read, {len(rows):,} principal", flush=True)
        # Page by the reported total: a page can come back one short of PAGE.
        total = data.get("@odata.count", 0)
        if not data["value"] or seen >= total:
            return rows
        skip = seen


def triage(name: str) -> str:
    return next((why for pat, why in TRIAGE if re.search(pat, name)), "")


def main() -> None:
    kept = {}
    if OUT.exists():
        with OUT.open(encoding="utf-8", newline="") as fh:
            kept = {r["register_id"]: r for r in csv.DictReader(fh) if r.get("call")}
    rows, seen = [], set()
    for collection in ("Act", "LegislativeInstrument"):
        for t in fetch(collection):
            if t["id"] in seen:  # pages can overlap by a row
                continue
            seen.add(t["id"])
            old = kept.get(t["id"], {})
            rows.append(
                {
                    "register_id": t["id"],
                    "name": t["name"],
                    "collection": t["collection"],
                    "year": t.get("year") or "",
                    "number": t.get("number") or "",
                    "making_date": (t.get("makingDate") or "")[:10],
                    "triage": triage(t["name"]),
                    "call": old.get("call", ""),
                    "requirements": old.get("requirements", ""),
                    "reason": old.get("reason", ""),
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["collection"], r["name"])))
    counts = {c: sum(1 for r in rows if r["collection"] == c) for c in ("Act", "LegislativeInstrument")}
    screen = {c: sum(1 for r in rows if r["collection"] == c and not r["triage"]) for c in counts}
    MANIFEST.write_text(
        json.dumps(
            {
                "source": "Federal Register of Legislation API (Office of Parliamentary Counsel)",
                "url": f"{API}/Titles?$filter=collection eq '<Act|LegislativeInstrument>' and isInForce eq true (principal kept)",
                "retrieved": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                "licence": "CC BY 4.0 (Federal Register of Legislation content)",
                "in_force_principal": counts,
                "to_screen_after_triage": screen,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT.relative_to(ROOT)}: {counts}; to screen after title triage: {screen}")


if __name__ == "__main__":
    main()
