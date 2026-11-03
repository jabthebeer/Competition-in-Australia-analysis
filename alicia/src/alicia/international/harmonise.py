"""Phase P2 of the benchmarking plan: the same measures, on the same definitions, for Australia and the OECD
economies, by common industry group, each rated for how comparable Australia's figure is.

The benchmark definitions are the OECD's employer business demography (Eurostat-OECD Manual on Business
Demography Statistics), as Eurostat's metadata states them, read 3 November 2026 at
<https://ec.europa.eu/eurostat/cache/metadata/en/bd_sims.htm>: an employer enterprise birth is a new enterprise with
at least one employee in its birth year, or an existing enterprise that takes on its first employee; an employer
death is a death of an enterprise with employees, or an enterprise that drops to no employees; deaths count only
if the enterprise is not reactivated within two years; rates are per active employer enterprise. Peers' figures are
summed from ISIC sections to the common groups (the European members publish no all-industries total).

Australia (ABS business register, CABEE, employing businesses) comes closest as follows. Births are entries with
employees, deaths exits with employees, and active businesses those at the start of the year plus entries.
CABEE does not count businesses that take on their first employee as entries, or those that stop employing as
exits, so its gross birth and death rates are lower bounds of the OECD's. Across all industries the net movement
across the one-employee threshold is known (CABEE's balancing item), and was out of employing, about 1 to 3% of
active businesses a year outside 2020-21 (JobKeeper moved many businesses into employing that year). The net
change in employer businesses includes those movements, as the OECD's births less deaths do, so it is the
comparable measure; within an industry group it also includes businesses reclassified between industries.
Financial years are labelled by the calendar year they end in.

Three-year survival compares the OECD's survivors in year t of the enterprises born in t-3 with CABEE's employing
entries of a financial year still trading two Junes after it ends: both about two and a half years after an
average birth. CABEE survival is published by subdivision, so groups are built from subdivisions. Size structure
compares enterprises with 20 or more persons employed (OECD) with businesses with 20 or more employees (CABEE),
each as a share of all businesses. Labour productivity growth uses STAN for every country, Australia included:
value added at previous year's prices over the year before at current prices (chain-linking the group), less the
growth of hours worked (or persons employed). A year's growth per hour is dropped where hours and persons employed
grow more than 10 log points apart, a sign of a break in the hours series (STAN's Australian manufacturing hours fall
22% in 2018 while persons employed rise 4%); the test also drops genuine swings when job-retention schemes cut hours
in 2020-2022, mostly outside the windows, and a group with breaks in two or more years is rated one level lower
per hour. STAN's Australian hours, though, disagree with the ABS's official industry productivity estimates
(5260.0.55.002): over 2015-2019 per-hour growth differs by more than a point a year in most divisions where both
exist, while STAN's Australian employment matches the Labour Force survey's calendar-year averages. So Australia's
per-hour growth is the ABS's official series for the groups that are one division (rated medium: financial years
against the peers' calendar years), and STAN's for the rest, rated low; growth per person stays on STAN. Regulation
indicators (PMR, STRI, FDI RRI) are the OECD's own, by
the sector indicators that apply to each group. The US (Census BDS) is mapped from NAICS sectors.

Each country, group and measure gets a rating. It starts from the source: high for the OECD's own data, medium
for Australia's net change in employer businesses and for the US BDS, low for Australia's gross birth and death
rates, survival and size shares. It drops one level where the classification does not line up enough to move a
rate: for Australian data built from classes or subdivisions, when at least 15% of the group's businesses are in
units whose ISIC matches lie in other groups (each split unit counted by the share of its matches elsewhere); for
Australian STAN figures, which come from national accounts by ANZSIC division, when at least 15% of the group's
businesses fall on the other side of the division boundary; for a peer that does not split out rental and leasing;
for US NAICS sectors that differ from ISIC. Rates are less sensitive to misclassification than levels, hence a
higher threshold than the 5% at which the website notes a difference. Low-rated comparisons are shown but never
flagged (decision D-8).

The business economy total sums the same groups for every country: the demography groups less utilities and
finance, which several peers do not publish (Canada has no electricity births; France, Italy, Spain and the UK no
finance). Where STAN does not split out rental and leasing or households as employers, they stay in their parent
groups for value added and hours alike, and the rating drops one level.
"""

from __future__ import annotations

import json
from collections import defaultdict

import pandas as pd

from ..pipeline import store
from . import OECD, OUT, bds, cabee_survival, oecd, peers, prose, stan
from .concordance import groups

EMPLOYING = ("1-19 employees", "20-199 employees", "200+ employees")
DEMOG_GROUPS = ("MIN", "MAN", "UTL", "CON", "TRD", "TRN", "ACC", "ICT", "FIN", "RES", "PRO", "EDU", "HLT", "OTH")
# The business economy, summed the same way for every country: the demography groups less utilities and finance,
# which several peers do not publish (Canada has no electricity; France, Italy, Spain and the UK no finance)
ALL = "ALL"
ALL_GROUPS = tuple(g for g in DEMOG_GROUPS if g not in ("UTL", "FIN"))
SPLIT = 0.15  # a group's rating drops when this share of its businesses is in units split between groups
BREAK = 0.10  # per-hour growth is dropped when hours and persons employed grow this far apart (log points)
BREAKS: list[dict] = []  # the group-years dropped by that test, for the record
LEVELS = ("low", "medium", "high")
COVID = (2020, 2021)
MEASURES = {
    "birth_rate": ("Employer business birth rate", "% of active employer businesses"),
    "death_rate": ("Employer business death rate", "% of active employer businesses"),
    "churn": ("Churn (births plus deaths)", "% of active employer businesses"),
    "net_entry_rate": ("Net change in employer businesses", "% of active employer businesses"),
    "survival_3y": ("Three-year survival of new employer businesses", "% of births"),
    "size_20plus": ("Businesses with 20 or more people", "% of all businesses"),
    "lp_growth_hour": ("Labour productivity growth per hour worked", "% a year"),
    "lp_growth_person": ("Labour productivity growth per person employed", "% a year"),
    "va_growth": ("Output growth (value added, volume)", "% a year"),
    "emp_growth": ("Jobs growth (persons employed)", "% a year"),
    "pmr_sector": ("Product market regulation, the group's sector indicators", "0 to 6"),
    "pmr_economy": ("Product market regulation, economy-wide", "0 to 6"),
    "stri_sector": ("Services trade restrictiveness, the group's sectors", "0 to 1"),
    "fdi_rri": ("FDI regulatory restrictiveness, all sectors", "0 to 1"),
}


def _groups() -> dict[str, dict]:
    return {g["id"]: g for g in groups()["groups"]}


def _rows(country, group, measure, year, value, source, note=""):
    return {
        "country": country,
        "group": group,
        "measure": measure,
        "year": int(year),
        "value": float(value),
        "source": source,
        "note": note,
    }


def _rates(out: list, country: str, group: str, year: int, births, deaths, active, source: str, note: str = ""):
    if not active or pd.isna(active) or active <= 0:
        return
    if pd.notna(births):
        out.append(_rows(country, group, "birth_rate", year, 100 * births / active, source, note))
    if pd.notna(deaths):
        out.append(_rows(country, group, "death_rate", year, 100 * deaths / active, source, note))
    if pd.notna(births) and pd.notna(deaths):
        out.append(_rows(country, group, "churn", year, 100 * (births + deaths) / active, source, note))
        out.append(_rows(country, group, "net_entry_rate", year, 100 * (births - deaths) / active, source, note))


# ---- OECD members -----------------------------------------------------------------------------------------


def _section_sum(vals: dict[str, float], formula: list) -> tuple[float | None, bool]:
    """A group's value from section values with signs. Missing rental and leasing (N77) counts as zero and is
    reported; any other missing section makes the group missing."""
    total, unsplit = 0.0, False
    for code, sign in formula:
        if code not in vals or pd.isna(vals[code]):
            if code == "N77":
                unsplit = True
                continue
            return None, False
        total += sign * vals[code]
    return total, unsplit


def oecd_demography(bd: pd.DataFrame) -> list[dict]:
    d = bd[(bd["measure"] == "ENT") & (bd["unit_measure"] == "ENT_EM") & (bd["size_class"] == "_T")]
    stage = {("ACTIVE", "_T"): "active", ("B", "Y_LT1"): "births", ("D", "_T"): "deaths"}
    d = d.assign(kind=[stage.get((s, a)) for s, a in zip(d["business_stage"], d["age"], strict=True)]).dropna(
        subset=["kind"]
    )
    cells = d.groupby(["country", "period", "kind", "activity"])["value"].sum()
    out = []
    G = _groups()
    for (c, p), sub in cells.groupby(level=["country", "period"]):
        kinds = {k: v.droplevel(["country", "period", "kind"]).to_dict() for k, v in sub.groupby(level="kind")}
        tot = defaultdict(float)
        complete = True
        for gid in DEMOG_GROUPS:
            vals = {}
            unsplit = False
            for k in ("active", "births", "deaths"):
                v, u = _section_sum(kinds.get(k, {}), G[gid]["sdbs"])
                vals[k], unsplit = v, unsplit or u
            if vals["active"] is None:
                complete = complete and gid not in ALL_GROUPS
                continue
            for k in vals if gid in ALL_GROUPS else ():
                tot[k] = tot[k] + vals[k] if vals[k] is not None else float("nan")
            note = "rental and leasing not split out" if unsplit and gid in ("RES", "PRO") else ""
            _rates(out, c, gid, int(p), vals["births"], vals["deaths"], vals["active"], "OECD SDBS", note)
        if complete:
            _rates(out, c, ALL, int(p), tot["births"], tot["deaths"], tot["active"], "OECD SDBS")
    return out


def oecd_survival(bd: pd.DataFrame, sv: pd.DataFrame) -> list[dict]:
    births = bd[(bd["measure"] == "ENT") & (bd["unit_measure"] == "ENT_EM") & (bd["size_class"] == "_T")]
    births = births[(births["business_stage"] == "B") & (births["age"] == "Y_LT1")]
    b = (
        births.assign(year=births["period"].astype(int))
        .set_index(["country", "year", "activity"])["value"]
        .sort_index()
    )
    s = sv[(sv["age"] == "Y3") & (sv["unit_measure"] == "ENT_EM") & (sv["size_class"] == "_T")]
    s = s.assign(year=s["period"].astype(int)).set_index(["country", "year", "activity"])["value"]
    out = []
    G = _groups()
    for (c, y), sub in s.groupby(level=["country", "year"]):
        surv = sub.droplevel(["country", "year"]).to_dict()
        born = b.loc[(c, y - 3)].to_dict() if (c, y - 3) in b.index.droplevel("activity") else {}
        num_all = den_all = 0.0
        complete = True
        for gid in DEMOG_GROUPS:
            n, _ = _section_sum(surv, G[gid]["sdbs"])
            dn, _ = _section_sum(born, G[gid]["sdbs"])
            if n is None or not dn:
                complete = complete and gid not in ALL_GROUPS
                continue
            out.append(_rows(c, gid, "survival_3y", y, 100 * n / dn, "OECD SDBS"))
            if gid in ALL_GROUPS:
                num_all, den_all = num_all + n, den_all + dn
        if complete and den_all:
            out.append(_rows(c, ALL, "survival_3y", y, 100 * num_all / den_all, "OECD SDBS"))
    return out


def oecd_size(sz: pd.DataFrame) -> list[dict]:
    d = sz[(sz["measure"] == "ENTR") & sz["size_class"].isin(["_T", "S_GE20"])]
    cells = d.groupby(["country", "period", "size_class", "activity"])["value"].sum()
    out = []
    G = _groups()
    for (c, p), sub in cells.groupby(level=["country", "period"]):
        by = {k: v.droplevel(["country", "period", "size_class"]).to_dict() for k, v in sub.groupby(level="size_class")}
        num_all = den_all = 0.0
        complete = True
        for gid in DEMOG_GROUPS:
            n, _ = _section_sum(by.get("S_GE20", {}), G[gid]["sdbs"])
            dn, _ = _section_sum(by.get("_T", {}), G[gid]["sdbs"])
            if n is None or not dn:
                complete = complete and gid not in ALL_GROUPS
                continue
            out.append(_rows(c, gid, "size_20plus", int(p), 100 * n / dn, "OECD SDBS"))
            if gid in ALL_GROUPS:
                num_all, den_all = num_all + n, den_all + dn
        if complete and den_all:
            out.append(_rows(c, ALL, "size_20plus", int(p), 100 * num_all / den_all, "OECD SDBS"))
    return out


OPTIONAL = ("N77", "T")  # rental and leasing, and households as employers: left in their parents if not split out


def _formula(series: list[dict], c: str, y: int, formula: list) -> tuple[list, list[str]]:
    """The group's STAN formula for a country-year, without the optional activities that any of the series it needs
    (each a dict and the year it is read for) does not split out, so value added and employment cover the same
    activities."""
    missing = [code for code, _ in formula if code in OPTIONAL and any((c, yr, code) not in src for src, yr in series)]
    return [(code, sign) for code, sign in formula if code not in missing], missing


def _grp(src: dict, c: str, year: int, formula: list, zero_rent: bool = False) -> float | None:
    """A group's value from STAN activities with signs; None if any is missing (imputed rent counts as zero for
    hours and persons, which it has none of)."""
    total = 0.0
    for code, sign in formula:
        v = src.get((c, year, code))
        if v is None:
            if zero_rent and code == "L68A":
                continue
            return None
        total += sign * v
    return total


def _gaps(got: dict) -> dict:
    (h1, h0), (n1, n0) = got["lp_growth_hour"], got["lp_growth_person"]
    return {"hours_growth": round(100 * (h1 / h0 - 1), 1), "persons_growth": round(100 * (n1 / n0 - 1), 1)}


def _broken(got: dict) -> bool:
    """Hours and persons employed growing more than BREAK log points apart: a break in the hours series (STAN's
    Australian manufacturing hours fall 22% in 2018 while persons employed rise 4%)."""
    import math

    (h1, h0), (n1, n0) = got["lp_growth_hour"], got["lp_growth_person"]
    return abs(math.log(h1 / h0) - math.log(n1 / n0)) > BREAK


def stan_productivity(vh: pd.DataFrame, va: list[dict]) -> list[dict]:
    """Labour productivity growth by group and year, per hour worked and per person employed, for every country
    with STAN data (Australia included), and for the business economy (ALL_GROUPS chain-linked together)."""
    scaled = vh.assign(v=vh["value"] * 10.0 ** vh["unit_mult"].astype(float), year=vh["period"].astype(int))
    prev = scaled[(scaled["measure"] == "B1G") & (scaled["price_base"] == "Y")]
    hours = scaled[(scaled["measure"] == "EMP") & (scaled["unit_measure"] == "H")]
    persons = scaled[(scaled["measure"] == "EMP") & (scaled["unit_measure"] == "PS")]
    cur = pd.DataFrame(va).assign(v=lambda x: x["value_added_mn"] * 1e6)
    idx = lambda df: df.set_index(["country", "year", "activity"])["v"].to_dict()  # noqa: E731
    P, V, H, N = idx(prev), idx(cur), idx(hours), idx(persons)
    out = []
    G = _groups()
    for c, y in sorted({(c, y) for c, y, _ in P}):
        found: dict[str, dict] = {}  # group -> measure -> (vy, v0, e1, e0, note)
        for gid, g in G.items():
            found[gid] = {}
            for measure, src in (("lp_growth_hour", H), ("lp_growth_person", N)):
                f, missing = _formula([(P, y), (V, y - 1), (src, y), (src, y - 1)], c, y, g["stan"])
                vy, v0 = _grp(P, c, y, f), _grp(V, c, y - 1, f)
                e1, e0 = _grp(src, c, y, f, True), _grp(src, c, y - 1, f, True)
                if vy is None or not v0 or not e1 or not e0:
                    continue
                note = f"{' and '.join(missing)} not split out of value added" if missing else ""
                found[gid][measure] = (vy, v0, e1, e0, note)
            m = found[gid]
            if len(m) == 2 and _broken({k: (v[2], v[3]) for k, v in m.items()}):
                BREAKS.append({"country": c, "group": gid, "year": y, **_gaps({k: (v[2], v[3]) for k, v in m.items()})})
                m["broken"] = True
            for measure in ("lp_growth_hour", "lp_growth_person"):
                if measure in m and not (measure == "lp_growth_hour" and m.get("broken")):
                    vy, v0, e1, e0, note = m[measure]
                    out.append(_rows(c, gid, measure, y, 100 * ((vy / v0) / (e1 / e0) - 1), "OECD STAN", note))
            if "lp_growth_person" in m:  # context for the website: output and jobs growth on the same basis
                vy, v0, e1, e0, note = m["lp_growth_person"]
                out.append(_rows(c, gid, "va_growth", y, 100 * (vy / v0 - 1), "OECD STAN", note))
                out.append(_rows(c, gid, "emp_growth", y, 100 * (e1 / e0 - 1), "OECD STAN", note))
        for measure in ("lp_growth_hour", "lp_growth_person"):
            parts = [found[g].get(measure) for g in ALL_GROUPS]
            if any(p is None for p in parts):
                continue
            if measure == "lp_growth_hour" and any(found[g].get("broken") for g in ALL_GROUPS):
                BREAKS.append({"country": c, "group": ALL, "year": y, "hours_growth": None, "persons_growth": None})
                continue  # a component group's hours series breaks this year
            vy, v0, e1, e0 = (sum(p[k] for p in parts) for k in range(4))
            out.append(_rows(c, ALL, measure, y, 100 * ((vy / v0) / (e1 / e0) - 1), "OECD STAN"))
            if measure == "lp_growth_person":
                out.append(_rows(c, ALL, "va_growth", y, 100 * (vy / v0 - 1), "OECD STAN"))
                out.append(_rows(c, ALL, "emp_growth", y, 100 * (e1 / e0 - 1), "OECD STAN"))
    return out


def regulation(pmr: pd.DataFrame, stri: pd.DataFrame, fdi: pd.DataFrame) -> list[dict]:
    out = []
    G = _groups()
    pm = pmr.assign(year=pmr["period"].astype(int))
    st = stri.assign(year=stri["period"].astype(int))
    for (c, y), sub in pm.groupby(["country", "year"]):
        v = sub.set_index("measure")["value"]
        if "PMR" in v:  # economy-wide: one row, under the business-economy total
            out.append(_rows(c, ALL, "pmr_economy", y, v["PMR"], "OECD PMR"))
        for gid, g in G.items():
            codes = [m for m in g["pmr"] if m in v]
            if codes:
                out.append(_rows(c, gid, "pmr_sector", y, v[codes].mean(), "OECD PMR", "mean of " + ", ".join(codes)))
    for (c, y), sub in st.groupby(["country", "year"]):
        v = sub.set_index("activity")["value"]
        for gid, g in G.items():
            codes = [a for a in g["stri"] if a in v]
            if codes:
                out.append(_rows(c, gid, "stri_sector", y, v[codes].mean(), "OECD STRI", "mean of " + ", ".join(codes)))
    tot = fdi[(fdi["activity"] == "_T") & (fdi["pol_cat"] == "_T")]
    for _, r in tot.iterrows():
        out.append(_rows(r["country"], ALL, "fdi_rri", int(r["period"]), r["value"], "OECD FDI RRI"))
    return out


# ---- Australia ---------------------------------------------------------------------------------------------


def _class_groups() -> dict[str, str]:
    con = json.loads((OUT / "anzsic_isic4.json").read_text("utf-8"))
    return {a: v["group"] for a, v in con["classes"].items()}


def subdivision_groups(weights: dict[str, float]) -> dict[str, tuple[str, float]]:
    """Each ANZSIC subdivision's group (the one holding most of its employing businesses, by class) and the share of
    its businesses in classes assigned elsewhere."""
    cg = _class_groups()
    by: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for a, g in cg.items():
        by[a[:2]][g] += weights.get(a, 0.0) or 1e-9
    out = {}
    for sub, gs in by.items():
        g = max(gs, key=gs.get)
        tot = sum(gs.values())
        out[sub] = (g, 1 - gs[g] / tot if tot else 0.0)
    return out


def au_demography(panel: pd.DataFrame) -> list[dict]:
    cg = _class_groups()
    p = panel[panel["industry_level"] == "class"]
    emp = p[p["breakdown"].isin(EMPLOYING)]
    emp = emp.assign(year=emp["period"].dt.year + 1, group=emp["industry_code"].map(cg))
    t = emp.groupby(["group", "year", "measure"])["value"].sum().unstack("measure")
    out = []
    note = "lower bound: excludes businesses crossing the one-employee threshold"
    for (gid, y), r in t.iterrows():
        if gid not in DEMOG_GROUPS:
            continue
        active = r["businesses_start"] + r["entries"]
        _rates(out, "AUS", gid, y, r["entries"], r["exits"], active, "ABS CABEE", note)
    allg = t[t.index.get_level_values("group").isin(ALL_GROUPS)].groupby(level="year").sum()
    for y, r in allg.iterrows():
        active = r["businesses_start"] + r["entries"]
        _rates(out, "AUS", ALL, y, r["entries"], r["exits"], active, "ABS CABEE", note)
    # net change in employer businesses: the stock change, which includes threshold crossings (as the OECD's does)
    out = [o for o in out if o["measure"] != "net_entry_rate"]
    for (gid, y), r in pd.concat([t, pd.concat({ALL: allg}, names=["group"])]).iterrows():
        if gid in (*DEMOG_GROUPS, ALL):
            active = r["businesses_start"] + r["entries"]
            if active > 0:
                v = 100 * (r["businesses_end"] - r["businesses_start"]) / active
                n = "covid: JobKeeper moved businesses into employing" if y in COVID else ""
                out.append(_rows("AUS", gid, "net_entry_rate", y, v, "ABS CABEE", n))
    return out


def au_threshold_bounds(panel: pd.DataFrame) -> pd.DataFrame:
    """All industries: CABEE's net movement across the one-employee threshold (its balancing item for employing
    businesses), and the birth and death rates with it added where it adds (still lower bounds)."""
    cg = _class_groups()
    p = panel[(panel["industry_level"] == "class") & panel["breakdown"].isin(EMPLOYING)]
    p = p[p["industry_code"].map(cg).isin(ALL_GROUPS)]
    t = p.assign(year=p["period"].dt.year + 1).groupby(["year", "measure"])["value"].sum().unstack("measure")
    active = t["businesses_start"] + t["entries"]
    bal = t["businesses_end"] - t["businesses_start"] - t["entries"] + t["exits"]
    return pd.DataFrame(
        {
            "active": active,
            "net_threshold_crossing_pct": 100 * bal / active,
            "birth_rate_cabee": 100 * t["entries"] / active,
            "death_rate_cabee": 100 * t["exits"] / active,
            "birth_rate_with_net_crossing": 100 * (t["entries"] + bal.clip(lower=0)) / active,
            "death_rate_with_net_crossing": 100 * (t["exits"] + (-bal).clip(lower=0)) / active,
        }
    ).round(2)


def au_survival(sv: pd.DataFrame, weights: dict[str, float]) -> tuple[list[dict], dict[str, float]]:
    sg = subdivision_groups(weights)
    e = sv[sv["size"].isin(EMPLOYING)]
    e = e.assign(group=e["subdivision"].map(lambda s: sg.get(s, (None, 0))[0]))
    t = e.groupby(["group", "cohort", "june"])["count"].sum().unstack("june")
    out = []
    note = "employing entries still trading two Junes after the entry year"
    for (gid, cohort), r in t.iterrows():
        if gid in DEMOG_GROUPS and r.get(0):
            out.append(_rows("AUS", gid, "survival_3y", cohort + 2, 100 * r[2] / r[0], "ABS CABEE", note))
    allg = t[t.index.get_level_values("group").isin(ALL_GROUPS)].groupby(level="cohort").sum()
    for cohort, r in allg.iterrows():
        out.append(_rows("AUS", ALL, "survival_3y", cohort + 2, 100 * r[2] / r[0], "ABS CABEE", note))
    # share of each group's businesses in subdivisions that span groups (for the rating)
    tot, split = defaultdict(float), defaultdict(float)
    for a, w in weights.items():
        g, s = sg.get(a[:2], (None, 0.0))
        if g:
            tot[g] += w
            split[g] += w * s
    return out, {g: split[g] / tot[g] for g in tot if tot[g]}


def au_size(panel: pd.DataFrame) -> list[dict]:
    cg = _class_groups()
    p = panel[(panel["industry_level"] == "class") & (panel["measure"] == "businesses_end")]
    p = p.assign(year=p["period"].dt.year + 1, group=p["industry_code"].map(cg))
    big = p[p["breakdown"].isin(("20-199 employees", "200+ employees"))].groupby(["group", "year"])["value"].sum()
    tot = p[p["breakdown"] == ""].groupby(["group", "year"])["value"].sum()
    out = []
    for (gid, y), v in big.items():
        if gid in DEMOG_GROUPS and tot.get((gid, y)):
            out.append(
                _rows("AUS", gid, "size_20plus", y, 100 * v / tot[(gid, y)], "ABS CABEE", "employees, not persons")
            )
    b_all = big[big.index.get_level_values(0).isin(ALL_GROUPS)].groupby(level=1).sum()
    t_all = tot[tot.index.get_level_values(0).isin(ALL_GROUPS)].groupby(level=1).sum()
    for y, v in b_all.items():
        out.append(_rows("AUS", ALL, "size_20plus", y, 100 * v / t_all[y], "ABS CABEE", "employees, not persons"))
    return out


# ---- United States -----------------------------------------------------------------------------------------


def us_demography(b: pd.DataFrame) -> list[dict]:
    sec = b[b["table"] == "sec"].pivot_table(index=["sector", "year"], columns="measure", values="value")
    born = b[(b["table"] == "sec_fa") & (b["fage"] == "a) 0") & (b["measure"] == "firms")]
    born = born.set_index(["sector", "year"])["value"]
    G = _groups()
    out = []
    years = sorted({y for _, y in sec.index})
    for y in years:
        tot = defaultdict(float)
        complete = True
        for gid in DEMOG_GROUPS:
            secs = G[gid]["naics"]
            try:
                firms = sum(sec.loc[(s, y), "firms"] for s in secs)
                deaths = sum(sec.loc[(s, y), "firmdeath_firms"] for s in secs)
                births = sum(born.loc[(s, y)] for s in secs)
            except KeyError:
                complete = complete and gid not in ALL_GROUPS
                continue
            note = G[gid].get("naics_note", "")
            _rates(out, "USA", gid, y, births, deaths, firms, "US Census BDS", note)
            if gid in ALL_GROUPS:
                tot["births"] += births
                tot["deaths"] += deaths
                tot["firms"] += firms
        if complete:
            _rates(out, "USA", ALL, y, tot["births"], tot["deaths"], tot["firms"], "US Census BDS")
    return out


# ---- Australia's official productivity --------------------------------------------------------------------

# Groups that are one ANZSIC division with an ABS hours-based labour productivity series (5260.0.55.002)
ABS_LP_GROUPS = {"A": "AGR", "B": "MIN", "C": "MAN", "D": "UTL", "E": "CON", "H": "ACC", "I": "TRN", "J": "ICT"}
ABS_LP_GROUPS |= {"K": "FIN", "L": "RES"}
STAN_CHECK: dict = {}  # STAN's Australian per-hour growth against the ABS's, 2015-2019, for the record


def au_productivity_abs() -> list[dict]:
    """Australia's labour productivity growth per hour worked from the ABS's official industry estimates, for the
    groups that are one division. Financial years are labelled by the year they end in (the ABS series by the year
    they start)."""
    from ..menu.growth import abs_productivity

    p = abs_productivity()
    out = []
    for div, gid in ABS_LP_GROUPS.items():
        s = pd.Series(p["lp"].get(div) or [], index=p["years"][: len(p["lp"].get(div) or [])], dtype=float)
        g = 100 * (s / s.shift(1) - 1)
        for start, v in g.dropna().items():
            out.append(
                _rows("AUS", gid, "lp_growth_hour", int(start) + 1, v, "ABS 5260", "ABS official, financial years")
            )
    return out


def check_stan_australia(rows: list[dict], lo: int = 2015, hi: int = 2019) -> dict:
    """STAN's Australian per-hour growth against the ABS's official series, by group, averaged over a window."""
    df = pd.DataFrame(rows)
    a = df[(df["country"] == "AUS") & (df["measure"] == "lp_growth_hour") & df["year"].between(lo, hi)]
    by = a.groupby(["group", "source"])["value"].mean().unstack("source")
    if not {"OECD STAN", "ABS 5260"} <= set(by.columns):
        return {"window": f"{lo}-{hi}", "groups": {}, "differ": 0, "compared": 0}
    by = by.dropna(subset=["OECD STAN", "ABS 5260"])
    diff = (by["OECD STAN"] - by["ABS 5260"]).round(2)
    return {
        "window": f"{lo}-{hi}",
        "groups": {
            g: {"stan": round(by.loc[g, "OECD STAN"], 2), "abs": round(by.loc[g, "ABS 5260"], 2)} for g in by.index
        },
        "differ": int((diff.abs() > 1).sum()),
        "compared": int(len(diff)),
    }


# ---- comparability -----------------------------------------------------------------------------------------

# Australia's gross birth, death and churn rates: low, not D-5's medium, because CABEE does not count businesses
# crossing the one-employee threshold (E-105). The owner accepted this on 3 November 2026 and may revisit it
# (E-106): setting this to "medium" restores D-5 as first approved, and lets gaps in those rates be flagged.
GROSS_RATES_RATING = "low"

BASE_RATING = {
    ("ABS CABEE", "birth_rate"): (GROSS_RATES_RATING, "gross births exclude businesses taking on their first employee"),
    ("ABS CABEE", "death_rate"): (GROSS_RATES_RATING, "gross deaths exclude businesses that stop employing"),
    ("ABS CABEE", "churn"): (GROSS_RATES_RATING, "gross flows exclude businesses crossing the one-employee threshold"),
    ("ABS CABEE", "net_entry_rate"): ("medium", "stock change includes threshold crossings, as the OECD's does"),
    ("ABS CABEE", "survival_3y"): ("low", "CABEE survivors include businesses that stopped employing"),
    ("ABS CABEE", "size_20plus"): ("low", "employees (CABEE) against persons employed (OECD)"),
    ("US Census BDS", None): ("medium", "national source on NAICS sectors"),
    ("ABS 5260", "lp_growth_hour"): (
        "medium",
        "the ABS's official labour productivity, by financial year, against the peers' STAN calendar years",
    ),
}


def _down(level: str) -> str:
    return LEVELS[max(0, LEVELS.index(level) - 1)]


def rate(df: pd.DataFrame, class_split: dict[str, float], sub_split: dict[str, float]) -> pd.DataFrame:
    """Add a comparability rating and its reasons to each row."""
    con = json.loads((OUT / "anzsic_isic4.json").read_text("utf-8"))
    # division-level mismatch of each group (for Australian national accounts, published by ANZSIC division)
    division_gap = {
        g["id"]: 1
        - min(g["in_group"] if g["in_group"] is not None else 1, g["covered"] if g["covered"] is not None else 1)
        for g in con["groups"]
    }
    division_gap[ALL] = 0.0
    stan_unreliable = STAN_CHECK.get("compared", 0) and STAN_CHECK["differ"] * 2 >= STAN_CHECK["compared"]
    repeated_breaks: dict[tuple[str, str], int] = defaultdict(int)
    for b in BREAKS:
        repeated_breaks[(b["country"], b["group"])] += 1
    ratings, reasons = [], []
    for r in df.itertuples(index=False):
        base = BASE_RATING.get((r.source, r.measure)) or BASE_RATING.get((r.source, None))
        level, why = base if base else ("high", "the OECD's own data")
        why = [why]
        if r.country == "AUS" and r.source == "ABS CABEE":
            split = (sub_split if r.measure == "survival_3y" else class_split).get(r.group, 0.0)
            if split >= SPLIT:
                level = _down(level)
                why.append(f"{100 * split:.0f}% of the group's businesses are in units split between groups")
        if r.country == "AUS" and r.source == "OECD STAN" and r.measure == "lp_growth_hour" and stan_unreliable:
            level = "low"
            why.append(
                "STAN's Australian hours disagree with the ABS: per-hour growth differs by more than a point a "
                f"year in {STAN_CHECK['differ']} of the {STAN_CHECK['compared']} groups where both exist "
                f"({STAN_CHECK['window']})"
            )
        if r.country == "AUS" and r.source in ("OECD STAN", "ABS 5260") and division_gap.get(r.group, 0.0) >= SPLIT:
            level = _down(level)
            why.append(
                f"Australian national accounts are by ANZSIC division; {100 * division_gap[r.group]:.0f}% of the "
                "group's businesses differ from ISIC"
            )
        if r.measure == "lp_growth_hour" and repeated_breaks.get((r.country, r.group), 0) >= 2:
            level = _down(level)
            why.append(
                f"its hours series breaks in {repeated_breaks[(r.country, r.group)]} years (those years dropped)"
            )
        if r.note == "rental and leasing not split out" or "not split out of value added" in r.note:
            level = _down(level)
            why.append(r.note)
        if r.source == "US Census BDS" and r.note:
            level = _down(level)
            why.append(r.note)
        if r.country == "AUS" and r.year in COVID and r.source == "ABS CABEE":
            why.append("2020 and 2021 are distorted by JobKeeper")
        ratings.append(level)
        reasons.append("; ".join(why))
    return df.assign(comparability=ratings, reasons=reasons)


# ---- build -------------------------------------------------------------------------------------------------


def build(refresh: bool = False) -> pd.DataFrame:
    """Harmonise every measure, rate it, and write data/processed/international/benchmark_inputs.parquet,
    comparability.json and docs/methods_international_benchmarks.md."""
    from .concordance import employing_businesses

    if refresh or not (OUT / "au_cabee_survival.parquet").exists():
        cabee_survival.build(refresh)
    weights = employing_businesses()
    panel = store.read_panel("abs_cabee", "class_state_fy")
    rows = []
    bd = oecd.read("sdbs_births_deaths")
    rows += oecd_demography(bd)
    rows += oecd_survival(bd, oecd.read("sdbs_survival"))
    rows += oecd_size(oecd.read("sdbs_size"))
    BREAKS.clear()
    rows += stan_productivity(oecd.read("stan_volumes_hours"), stan.read())
    # Australia per hour: the ABS's official series where a group is one division (STAN's Australian hours are
    # checked against it and, where they disagree, the remaining STAN groups are rated low)
    abs_rows = au_productivity_abs()
    STAN_CHECK.clear()
    STAN_CHECK.update(check_stan_australia(rows + abs_rows))
    replaced = {r["group"] for r in abs_rows}
    rows = [
        r for r in rows if not (r["country"] == "AUS" and r["measure"] == "lp_growth_hour" and r["group"] in replaced)
    ] + abs_rows
    rows += regulation(oecd.read("pmr"), oecd.read("stri"), oecd.read("fdi_rri"))
    rows += au_demography(panel)
    surv, sub_split = au_survival(cabee_survival.read(), weights)
    rows += surv
    rows += au_size(panel)
    rows += us_demography(bds.read())
    df = pd.DataFrame(rows)
    df = df[df["country"].isin(OECD)]
    con = json.loads((OUT / "anzsic_isic4.json").read_text("utf-8"))
    class_split = class_split_shares(con, weights)
    df = rate(df, class_split, sub_split).sort_values(["measure", "group", "country", "year"]).reset_index(drop=True)
    df.to_parquet(OUT / "benchmark_inputs.parquet", index=False)
    bounds = au_threshold_bounds(panel)
    summary = au_ratings(df)
    (OUT / "comparability.json").write_text(
        json.dumps(
            {
                "title": "Comparability of Australia's figures with the OECD's, by group and measure",
                "levels": list(LEVELS),
                "australia": summary,
                "threshold_bounds": {int(y): r.to_dict() for y, r in bounds.iterrows()},
                "class_split": {g: round(v, 4) for g, v in class_split.items()},
                "subdivision_split": {g: round(v, 4) for g, v in sub_split.items()},
                "hours_breaks": BREAKS,
                "stan_australia_vs_abs": STAN_CHECK,
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    (store.ROOT / "docs" / "methods_international_benchmarks.md").write_text(markdown(df, summary, bounds), "utf-8")
    return df


def class_split_shares(con: dict, weights: dict[str, float]) -> dict[str, float]:
    """For each group, the share of its employing businesses (weighted by how much of each class's ISIC matches
    lie in other groups) in ANZSIC classes split between groups."""
    tot, split = defaultdict(float), defaultdict(float)
    for a, v in con["classes"].items():
        w = weights.get(a, 0.0)
        tot[v["group"]] += w
        split[v["group"]] += w * (1 - v["share"])
    return {g: split[g] / tot[g] for g in tot if tot[g]}


def au_ratings(df: pd.DataFrame) -> dict[str, dict[str, dict]]:
    """Australia's rating for each group and measure (the most common one across years, with its reasons)."""
    a = df[(df["country"] == "AUS") & ~df["year"].isin(COVID)]
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for (g, m), sub in a.groupby(["group", "measure"]):
        level = sub["comparability"].mode().iloc[0]
        why = sub.loc[sub["comparability"] == level, "reasons"].iloc[-1]
        out[g][m] = {"rating": level, "reasons": why, "years": f"{sub['year'].min()}-{sub['year'].max()}"}
    return dict(out)


def _median(xs: list[float]) -> float | None:
    xs = sorted(x for x in xs if pd.notna(x))
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def markdown(df: pd.DataFrame, summary: dict, bounds: pd.DataFrame) -> str:
    G = _groups()
    labels = {g: G[g]["label"] for g in G} | {ALL: "Business economy (the groups above except utilities and finance)"}
    core = peers.APPROVED["core"]
    lines = [
        "# Methods: international benchmarks (harmonisation and comparability)",
        "",
        "Generated by `alicia international harmonise` (phase P2 of the "
        "[benchmarking plan](forward_plan_international_benchmarking.md); decisions E-102 to E-105). Inputs: "
        "`data/processed/international/benchmark_inputs.parquet` (one row per country, group, measure and year, "
        "with its source, comparability rating and reasons) and `comparability.json`.",
        "",
        "## Method",
        "",
        prose(__doc__),
        "",
        "## Measures",
        "",
        "| Measure | Unit | Australia's source | Peers' source |",
        "|---|---|---|---|",
    ]
    for m, (label, unit) in MEASURES.items():
        sub = df[df["measure"] == m]
        au = sub.loc[sub["country"] == "AUS", "source"]
        peer = sub.loc[sub["country"] != "AUS", "source"]
        lines.append(
            f"| {label} (`{m}`) | {unit} | {au.mode().iloc[0] if len(au) else '–'} | "
            f"{', '.join(sorted(peer.unique())) or '–'} |"
        )
    lines += [
        "",
        "## Australia's ratings by group",
        "",
        "Comparability of Australia's figure with the peers', by group and measure (H high, M medium, L low; a dash: "
        "no Australian series). Regulation indicators are the OECD's own and rated high throughout.",
        "",
    ]
    ms = ["birth_rate", "death_rate", "churn", "net_entry_rate", "survival_3y", "size_20plus", "lp_growth_hour"]
    lines += ["| Group | " + " | ".join(MEASURES[m][0] for m in ms) + " |", "|---|" + "---|" * len(ms)]
    for g in [*DEMOG_GROUPS, "AGR", "PUB", ALL]:
        cells = [(summary.get(g, {}).get(m, {}).get("rating", "–") or "–")[0].upper().replace("–", "–") for m in ms]
        lines.append(f"| {labels[g]} ({g}) | " + " | ".join(cells) + " |")
    reasons = sorted(
        {
            v["reasons"]
            for g in summary.values()
            for v in g.values()
            if "split" in v["reasons"] or "ANZSIC division" in v["reasons"]
        }
    )
    if reasons:
        lines += ["", "Reasons for the downgrades:", ""]
        lines += [f"- {r}" for r in reasons]
    lines += [
        "",
        "## The one-employee threshold (Australia, all industries)",
        "",
        "CABEE's net movement of employing businesses across the threshold, and Australia's birth and death rates "
        "with it added where it adds. Both rates stay lower bounds: only the net movement is published, not the "
        "flows each way.",
        "",
        "| Year | Net crossing, % of active | Birth rate, CABEE | Death rate, CABEE | Birth rate with net crossing | "
        "Death rate with net crossing |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for y, r in bounds.iterrows():
        lines.append(
            f"| {y} | {r['net_threshold_crossing_pct']:+.1f} | {r['birth_rate_cabee']:.1f} | "
            f"{r['death_rate_cabee']:.1f} | {r['birth_rate_with_net_crossing']:.1f} | "
            f"{r['death_rate_with_net_crossing']:.1f} |"
        )
    lines += [
        "",
        "## Scale check",
        "",
        "Australia against the median of the six core peers, business economy, averaged over the plan's two windows "
        "(2020 and 2021 are left out). This checks that the harmonised series are on comparable scales; it is not "
        "the benchmark, which phase P3 computes with ranges, persistence and leave-one-out checks.",
        "",
        "| Measure | Australia, 2015-19 | Peer median, 2015-19 | Australia, 2022-24 | Peer median, 2022-24 | "
        "Australia's rating |",
        "|---|---:|---:|---:|---:|---|",
    ]
    fmt = lambda v: "–" if v is None or pd.isna(v) else f"{v:.1f}"  # noqa: E731
    for m in (
        "birth_rate",
        "death_rate",
        "churn",
        "net_entry_rate",
        "survival_3y",
        "size_20plus",
        "lp_growth_hour",
        "lp_growth_person",
    ):
        cells = []
        for lo, hi in ((2015, 2019), (2022, 2024)):
            w = df[(df["year"] >= lo) & (df["year"] <= hi) & (df["group"] == ALL) & (df["measure"] == m)]
            sub = w.groupby("country")["value"].mean()
            med = _median([sub.get(c) for c in core if c in sub.index])
            n = sum(1 for c in core if c in sub.index)
            cells += [fmt(sub.get("AUS")), f"{fmt(med)} ({n})"]
        rating = summary.get(ALL, {}).get(m, {}).get("rating", "–")
        lines.append(f"| {MEASURES[m][0]} | " + " | ".join(cells) + f" | {rating} |")
    lines += ["", "In brackets: the number of core peers with data in the window.", ""]
    lines += [
        "",
        "## Limits",
        "",
        "- Australia's gross birth and death rates are lower bounds of the OECD's definitions by an amount that "
        "public data cannot fix: the ABS publishes the net movement across the one-employee threshold, not the "
        "flows each way. A gap in them is never flagged (rated low); the net change in employer businesses is.",
        "- CABEE counts businesses by ABN-based units, the OECD enterprises; CABEE exits are not held back for two "
        "years to exclude reactivations. Financial years are compared with calendar years half a year apart.",
        "- The recent window is thin: the peers' business demography ends in 2022 or 2023, and deaths, which wait two "
        "years to rule out reactivation, end earlier. The UK's ends in 2018, so it has no figures for 2022-2024.",
        "- STAN's hours for Australia break in several groups (mining, ICT, finance, utilities); per-person growth is "
        "the steadier comparison there.",
        "- Regulation indicators are national; a group's sector indicators cover only part of it.",
        "",
    ]
    return "\n".join(lines)
