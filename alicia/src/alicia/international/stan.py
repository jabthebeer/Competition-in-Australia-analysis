"""Value added by industry for the OECD economies, from the OECD STAN database (2025 edition).

Gross value added at current prices in national currency (measure B1G, price base V, unit XDC), for the STAN
activities the common industry groups are built from (``stan`` in alicia/data/industry_groups.json) and the
total. Current prices in each country's own currency are enough for industry shares, which is what the peer
ranking uses; levels are not compared across countries.
"""

from __future__ import annotations

import csv
import io

from ..pipeline import store
from . import OECD, OUT
from .concordance import groups

SOURCE = "oecd_stan"
SDMX = "https://sdmx.oecd.org/public/rest"
FLOW = "OECD.STI.PIE,DSD_STAN@DF_STAN_2025,1.0"
# Not verified on oecd.org, which refuses automated requests (HTTP 403), as for the costing connectors.
LICENCE = (
    "OECD terms and conditions; CC BY 4.0 is the OECD default for data published from 1 July 2024 "
    "(open-by-default policy, seen in search results only; oecd.org refused direct requests)"
)
START = 2010
TOTAL = "_T"


def activities() -> list[str]:
    acts = {a for g in groups()["groups"] for a, _ in g["stan"]}
    return sorted(acts) + [TOTAL]


def url(countries: list[str] | None = None) -> str:
    key = f"A.{'+'.join(countries or OECD)}.{'+'.join(activities())}.B1G.V.XDC"
    return f"{SDMX}/data/{FLOW}/{key}?startPeriod={START}&format=csvfilewithlabels"


def parse(text: str) -> list[dict]:
    """(country, activity, year, value in millions of national currency) from the SDMX-CSV response."""
    if not text.startswith("STRUCTURE"):
        raise ValueError(f"STAN: the response is not SDMX-CSV ({text[:60]!r})")
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        if (r["MEASURE"], r["PRICE_BASE"], r["UNIT_MEASURE"]) != ("B1G", "V", "XDC"):
            raise ValueError(f"STAN: unexpected series {r['MEASURE']}/{r['PRICE_BASE']}/{r['UNIT_MEASURE']}")
        if not r["OBS_VALUE"]:
            continue
        value = float(r["OBS_VALUE"]) * 10 ** (int(r["UNIT_MULT"] or 0) - 6)
        out.append(
            {
                "country": r["REF_AREA"],
                "country_name": r["Reference area"],
                "activity": r["ACTIVITY"],
                "year": int(r["TIME_PERIOD"]),
                "value_added_mn": value,
                "status": r["OBS_STATUS"],
            }
        )
    return sorted(out, key=lambda r: (r["country"], r["activity"], r["year"]))


def additivity(rows: list[dict]) -> float:
    """Largest relative gap, over country-years with every activity, between the total and the sum of the
    common groups plus imputed rent (which the groups leave out). Near zero if the formulas cover the economy
    once; STAN totals can differ slightly from the sum of industries."""
    from .peers import group_values

    total = {(r["country"], r["year"]): r["value_added_mn"] for r in rows if r["activity"] == TOTAL}
    rent = {(r["country"], r["year"]): r["value_added_mn"] for r in rows if r["activity"] == "L68A"}
    n = len(groups()["groups"])
    gaps = [
        abs((sum(v.values()) + rent[k]) / total[k] - 1)
        for k, v in group_values(rows).items()
        if len(v) == n and k in rent and total.get(k)
    ]
    return max(gaps) if gaps else float("nan")


def build(refresh: bool = False) -> list[dict]:
    """Download STAN value added and write data/processed/international/stan_value_added.csv."""
    path = store.download(SOURCE, url(), "stan2025_b1g_current_prices.csv", LICENCE, refresh=refresh)
    rows = parse(path.read_text("utf-8-sig"))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "stan_value_added.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def read() -> list[dict]:
    with (OUT / "stan_value_added.csv").open(encoding="utf-8") as f:
        return [{**r, "year": int(r["year"]), "value_added_mn": float(r["value_added_mn"])} for r in csv.DictReader(f)]
