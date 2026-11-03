"""Which OECD economies are most like Australia: a similarity ranking that proposes a peer group (decision D-1).

Four distances from Australia, each averaged over a window of years:

- **Industry structure**: the dissimilarity index of value-added shares across the common industry groups
  (half the sum of absolute differences in shares, from 0 for identical structures to 1 for no overlap).
  Shares exclude the imputed rent of owner-occupied dwellings, which has no businesses or workers.
- **Income**: the gap in log GDP per head at purchasing power parity.
- **Size**: the gap in log population.
- **Openness**: the gap in log trade (exports plus imports) as a share of GDP.

Each distance is divided by its typical size between two OECD economies (the root mean square over all
pairs of members), so the four are in the same units, and the score is their weighted sum: industry
structure 1/2 and the other three 1/6 each, because structure matters most for comparing industry
statistics. Lower is more similar. Variants change the weights, drop one distance at a time and move the
window, to show how stable the ranking is; the proposed core group is the six most similar economies, which
the owner approves before any benchmark is computed.

Shares are averaged over the window's years in which every group is available. Where fewer than three such
years exist (mostly because the country does not split out imputed rent, which real estate needs), real
estate is left out of that country's comparison and the shares of both countries are taken over the other
groups. Where a country does not split out rental and leasing, it stays with professional and administrative
services. The ranking describes similarity only; it says nothing about which economy performs better.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from itertools import combinations

from ..pipeline import store
from . import OECD, OUT, prose, stan, wdi
from .concordance import groups

HOME = "AUS"
CORE = 6
WINDOW = (2015, 2019)  # before COVID, and the latest years every economy has in full
WEIGHTS = {"structure": 1 / 2, "income": 1 / 6, "size": 1 / 6, "openness": 1 / 6}
FIXED = ("CAN", "NZL", "NOR", "GBR", "USA")  # the simple fixed list the plan checks results against
MIN_YEARS = 3
# National sources of employer business demography for members outside the OECD's (to confirm in P1)
NATIONAL_DEMOGRAPHY = {"USA": "the Census Bureau's Business Dynamics Statistics"}
DROPPABLE = "RES"
RENTAL = "N77"

DEMOGRAPHY_SOURCE = "oecd_sdbs"
DEMOGRAPHY_URL = (
    "https://sdmx.oecd.org/public/rest/availableconstraint/"
    "OECD.SDD.TPS,DSD_SDBSBD_ISIC4@DF_BD_EMP_B_D,1.0/A..ENT.....B./all?mode=available"
)

VARIANTS = {
    "baseline": ("Baseline: structure 1/2, the others 1/6 each, 2015-2019", WEIGHTS, WINDOW),
    "equal": ("Equal weights, 1/4 each", dict.fromkeys(WEIGHTS, 1 / 4), WINDOW),
    "structure_only": ("Industry structure only", {"structure": 1.0}, WINDOW),
    "no_income": ("Without income", {"structure": 3 / 5, "size": 1 / 5, "openness": 1 / 5}, WINDOW),
    "no_size": ("Without size", {"structure": 3 / 5, "income": 1 / 5, "openness": 1 / 5}, WINDOW),
    "no_openness": ("Without openness", {"structure": 3 / 5, "income": 1 / 5, "size": 1 / 5}, WINDOW),
    "recent": ("Baseline weights, 2019-2023", WEIGHTS, (2019, 2023)),
    "earlier": ("Baseline weights, 2010-2014", WEIGHTS, (2010, 2014)),
}


def group_values(rows: list[dict]) -> dict[tuple[str, int], dict[str, float]]:
    """Value added in each common group, by (country, year), from STAN activities. A group is left out of a
    year when any activity in its formula is missing, except rental and leasing (N77): where a country does
    not split it out, it stays in professional and administrative services (see ``unsplit_rental``)."""
    acts: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for r in rows:
        acts[(r["country"], r["year"])][r["activity"]] = r["value_added_mn"]
    out = {}
    for key, a in acts.items():
        a = {RENTAL: 0.0, **a}
        vals = {}
        for g in groups()["groups"]:
            if all(code in a for code, _ in g["stan"]):
                vals[g["id"]] = sum(sign * a[code] for code, sign in g["stan"])
        out[key] = vals
    return out


def unsplit_rental(rows: list[dict]) -> set[tuple[str, int]]:
    """Country-years without rental and leasing (N77) split out of administrative services."""
    have = {(r["country"], r["year"]) for r in rows if r["activity"] == RENTAL}
    return {(r["country"], r["year"]) for r in rows} - have


def structure(
    values: dict[tuple[str, int], dict[str, float]], window: tuple[int, int], unsplit: set | frozenset = frozenset()
) -> dict[str, dict]:
    """Average value-added shares over the window for each country: over all groups if at least MIN_YEARS
    years have them all, else without real estate. ``unsplit`` (country-years without rental and leasing
    split out) is used to flag the countries affected."""
    ids = [g["id"] for g in groups()["groups"]]
    years = range(window[0], window[1] + 1)
    out = {}
    for c in sorted({k[0] for k in values}):
        for use in (ids, [g for g in ids if g != DROPPABLE]):
            yrs = [y for y in years if all(g in values.get((c, y), {}) for g in use)]
            if len(yrs) >= MIN_YEARS:
                break
        else:
            continue
        shares = defaultdict(float)
        for y in yrs:
            v = values[(c, y)]
            tot = sum(v[g] for g in use)
            for g in use:
                shares[g] += v[g] / tot / len(yrs)
        out[c] = {
            "shares": dict(shares),
            "years": yrs,
            "groups": use,
            "rental_not_split": any((c, y) in unsplit for y in yrs),
        }
    return out


def dissimilarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Half the sum of absolute share differences over the groups both have, after rescaling each to 1."""
    common = sorted(set(a) & set(b))
    sa, sb = sum(a[g] for g in common), sum(b[g] for g in common)
    return 0.5 * sum(abs(a[g] / sa - b[g] / sb) for g in common)


def scalars(rows: list[dict], window: tuple[int, int]) -> dict[str, dict[str, float]]:
    """Window averages of log GDP per head, log population and log trade share, by country."""
    acc: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        if window[0] <= r["year"] <= window[1] and r["value"] > 0:
            acc[(r["country"], r["indicator"])].append(math.log(r["value"]))
    names = {"gdp_per_head_ppp": "income", "population": "size", "trade_share_gdp": "openness"}
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for (c, ind), v in acc.items():
        out[c][names[ind]] = sum(v) / len(v)
    return dict(out)


def _rms(xs: list[float]) -> float:
    return math.sqrt(sum(x * x for x in xs) / len(xs))


def rank(stan_rows: list[dict], wdi_rows: list[dict], weights: dict[str, float], window: tuple[int, int]) -> dict:
    """Score every OECD economy against Australia. Returns the ranking (most similar first) and the scales."""
    struct = structure(group_values(stan_rows), window, unsplit_rental(stan_rows))
    scal = scalars(wdi_rows, window)
    countries = [c for c in OECD if c in struct and all(k in scal.get(c, {}) for k in ("income", "size", "openness"))]
    if HOME not in countries:
        raise ValueError(f"{HOME} lacks data for {window}")
    pairs = list(combinations(countries, 2))
    scale = {"structure": _rms([dissimilarity(struct[a]["shares"], struct[b]["shares"]) for a, b in pairs])}
    for k in ("income", "size", "openness"):
        scale[k] = _rms([scal[a][k] - scal[b][k] for a, b in pairs])
    home = struct[HOME]["shares"]
    ranking = []
    for c in countries:
        if c == HOME:
            continue
        d = {"structure": dissimilarity(home, struct[c]["shares"])}
        for k in ("income", "size", "openness"):
            d[k] = abs(scal[c][k] - scal[HOME][k])
        std = {k: d[k] / scale[k] if scale[k] else 0.0 for k in d}  # a scale of 0: every economy is alike
        score = sum(w * std[k] for k, w in weights.items())
        ranking.append(
            {
                "country": c,
                "score": round(score, 4),
                "distance": {k: round(v, 4) for k, v in d.items()},
                "standardised": {k: round(v, 3) for k, v in std.items()},
                "years": struct[c]["years"],
                "real_estate_left_out": DROPPABLE not in struct[c]["groups"],
                "rental_not_split": struct[c]["rental_not_split"],
            }
        )
    ranking.sort(key=lambda r: r["score"])
    for i, r in enumerate(ranking, 1):
        r["rank"] = i
    return {
        "ranking": ranking,
        "scale": {k: round(v, 4) for k, v in scale.items()},
        "structure": struct,
        "scalars": scal,
    }


def demography_countries(refresh: bool = False) -> list[str]:
    """Economies with employer business births in the OECD's business demography (SDBS), from the dataflow's
    availability response."""
    path = store.download(
        DEMOGRAPHY_SOURCE, DEMOGRAPHY_URL, "bd_emp_births_availability.xml", stan.LICENCE, refresh=refresh
    )
    xml = path.read_text("utf-8")
    m = re.search(r'<common:KeyValue id="REF_AREA">(.*?)</common:KeyValue>', xml, re.S)
    if not m:
        raise ValueError("no REF_AREA in the business demography availability response")
    return sorted(re.findall(r"<common:Value>([^<]+)</common:Value>", m.group(1)))


def build(refresh: bool = False) -> dict:
    """Rank the OECD economies, run the variants and write data/processed/international/peers.json and
    docs/international_peers.md."""
    stan_rows, wdi_rows = stan.read(), wdi.read()
    names = {r["country"]: r["country_name"] for r in stan_rows}
    demog = set(demography_countries(refresh))
    runs = {k: rank(stan_rows, wdi_rows, w, win) for k, (_, w, win) in VARIANTS.items()}
    base = runs["baseline"]
    ranks = {k: {r["country"]: r["rank"] for r in run["ranking"]} for k, run in runs.items()}
    ranking = []
    for r in base["ranking"]:
        c = r["country"]
        var = {k: ranks[k].get(c) for k in VARIANTS if k != "baseline"}
        ranking.append(
            {
                **r,
                "name": names.get(c, c),
                "in_business_demography": c in demog,
                "variants": var,
                "top_core_in": sum(1 for k in VARIANTS if (ranks[k].get(c) or 99) <= CORE),
            }
        )
    struct, scal = base["structure"], base["scalars"]
    out = {
        "title": "Economies most similar to Australia (OECD members)",
        "status": "proposed core group, awaiting owner approval (decision D-1)",
        "method": prose(__doc__),
        "window": list(WINDOW),
        "weights": WEIGHTS,
        "scale": base["scale"],
        "variants": {k: v[0] for k, v in VARIANTS.items()},
        "australia": {
            "shares": {g: round(s, 4) for g, s in struct[HOME]["shares"].items()},
            "years": struct[HOME]["years"],
            "gdp_per_head_ppp": round(math.exp(scal[HOME]["income"])),
            "population_m": round(math.exp(scal[HOME]["size"]) / 1e6, 1),
            "trade_share_gdp": round(math.exp(scal[HOME]["openness"]), 1),
        },
        "levels": {
            c: {
                "gdp_per_head_ppp": round(math.exp(v["income"])),
                "population_m": round(math.exp(v["size"]) / 1e6, 1),
                "trade_share_gdp": round(math.exp(v["openness"]), 1),
            }
            for c, v in sorted(scal.items())
            if c in OECD
        },
        "shares": {c: {g: round(s, 4) for g, s in v["shares"].items()} for c, v in sorted(struct.items())},
        "ranking": ranking,
        "proposed_core": [r["country"] for r in ranking[:CORE]],
        "fixed_list": list(FIXED),
        "checks": {"stan_groups_vs_total_max_gap": round(stan.additivity(stan_rows), 4)},
        "business_demography": sorted(demog & set(OECD)),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "peers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (store.ROOT / "docs" / "international_peers.md").write_text(markdown(out), encoding="utf-8")
    return out


def _pct(x: float) -> str:
    return f"{100 * x:.1f}"


def markdown(out: dict) -> str:
    """The ranking as a short note for the owner to approve the peer group."""
    gl = {g["id"]: g["label"] for g in groups()["groups"]}
    au = out["australia"]
    rk = out["ranking"]
    core = out["proposed_core"]
    names = {r["country"]: r["name"] for r in rk}
    var_keys = [k for k in out["variants"] if k != "baseline"]
    lines = [
        "# Economies most similar to Australia: proposed peer group",
        "",
        f"Generated by `alicia international peers` from OECD STAN 2025 and World Bank WDI data. Status: "
        f"**{out['status']}**.",
        "",
        "## Proposal",
        "",
        f"Core peer group ({len(core)} economies): **{', '.join(names[c] for c in core)}**. The OECD median is "
        "shown alongside as a second comparator, and results are checked against the fixed list "
        f"({', '.join(names.get(c, c) for c in out['fixed_list'])}) and with each peer left out.",
        "",
        "Peers without OECD employer business demography, and where their entry and exit rates would come from: "
        + (
            "; ".join(
                f"{names[c]} ({NATIONAL_DEMOGRAPHY.get(c, 'no national source identified yet')})"
                for c in core
                if not next(r for r in rk if r["country"] == c)["in_business_demography"]
            )
            or "none"
        )
        + ". Such comparisons need harmonising to the OECD definitions and carry a lower comparability rating.",
        "",
        "## Method",
        "",
        out["method"],
        "",
        f"Typical distances between two OECD economies (the scales): structure {out['scale']['structure']:.3f}, "
        f"log income {out['scale']['income']:.3f}, log population {out['scale']['size']:.3f}, log trade share "
        f"{out['scale']['openness']:.3f}.",
        "",
        "## Ranking",
        "",
        "Score: weighted sum of the four standardised distances (lower is more similar). Columns 'Structure' to "
        "'Openness' are each distance divided by its scale. 'Demography': in the OECD's employer business "
        "demography (births). 'In top 6': how many of the eight runs (baseline and seven variants) put the economy "
        "among the six most similar.",
        "",
        "| Rank | Economy | Score | Structure | Income | Size | Openness | GDP per head (PPP $) | Population (m) | "
        "Trade (% GDP) | Demography | In top 6 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        f"| | **Australia** | | | | | | {au['gdp_per_head_ppp']:,} | {au['population_m']} | {au['trade_share_gdp']} "
        "| no | |",
    ]
    for r in rk:
        lv = out["levels"][r["country"]]
        s = r["standardised"]
        flag = " (no real estate)" if r["real_estate_left_out"] else ""
        flag += " (rental not split)" if r["rental_not_split"] else ""
        lines.append(
            f"| {r['rank']} | {r['name']}{flag} | {r['score']:.2f} | {s['structure']:.2f} | {s['income']:.2f} | "
            f"{s['size']:.2f} | {s['openness']:.2f} | {lv['gdp_per_head_ppp']:,} | {lv['population_m']} | "
            f"{lv['trade_share_gdp']} | {'yes' if r['in_business_demography'] else 'no'} | {r['top_core_in']} of 8 |"
        )
    lines += [
        "",
        "## Stability",
        "",
        "Rank of the 12 most similar economies in each variant:",
        "",
        "| Economy | Baseline | " + " | ".join(out["variants"][k] for k in var_keys) + " |",
        "|---|---:|" + "---:|" * len(var_keys),
    ]
    for r in rk[:12]:
        lines.append(f"| {r['name']} | {r['rank']} | " + " | ".join(str(r["variants"][k]) for k in var_keys) + " |")
    top = {k: sorted((r for r in rk), key=lambda r: r["variants"].get(k) or 99)[:CORE] for k in var_keys}
    lines += ["", "Six most similar in each variant:", ""]
    for k in var_keys:
        lines.append(f"- {out['variants'][k]}: {', '.join(r['name'] for r in top[k])}")
    lines += [
        "",
        "## Industry structure",
        "",
        "Value-added shares, %, average of "
        f"{out['window'][0]}-{out['window'][1]}, excluding imputed rent of owner-occupied dwellings:",
        "",
        "| Group | Australia | " + " | ".join(names[c] for c in core) + " | OECD median |",
        "|---|---:|" + "---:|" * (len(core) + 1),
    ]
    for gid, label in gl.items():
        vals = sorted(v[gid] for c, v in out["shares"].items() if gid in v and c != "AUS")
        med = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
        cells = [_pct(out["shares"][c][gid]) if gid in out["shares"][c] else "" for c in core]
        lines.append(
            f"| {label} | {_pct(au['shares'].get(gid, float('nan')))} | " + " | ".join(cells) + f" | {_pct(med)} |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "- Similarity is measured on economy-wide features. Two economies can be alike overall and differ within "
        "an industry (for example, the kind of mining).",
        "- GDP per head for Ireland and Luxembourg is inflated by multinational profits and cross-border workers, "
        "so their income distance overstates how different living standards are.",
        "- Value-added shares at current prices move with commodity prices, which matters for Australia, Norway, "
        "Canada and Chile; the earlier and recent windows show how much.",
        "- The weights are a judgement. The variants show which economies are close on any reasonable choice.",
        "",
    ]
    return "\n".join(lines)
