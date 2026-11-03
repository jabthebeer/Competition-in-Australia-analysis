"""Phase P3 of the benchmarking plan: Australia against its peers, by group and measure, and the flag rule.

For each group, measure and window, each year counts when Australia and at least four of the six core peers
(E-103) have a figure. In each counted year the engine takes the core peers' median, mean, standard deviation and
interquartile range (25th to 75th percentile, interpolated between order statistics as R's default type 7 does) and
notes whether Australia is below, within or above that range. Over the window it reports Australia's average, the
peers' average median and range, the gap to the median in points, as a share of the median and in peer standard
deviations, Australia's rank among the seven, and how the gap moved between the two windows.

A gap is flagged (decision D-8) when all of these hold: Australia is on the same side of the peer range in more
than half the counted years, with at least two counted years; that still holds with each core peer left out in
turn (each variant needing three peers a year); Australia's average gap to the median over the window points the
same way (a check that a few extreme years do not hide the opposite); and Australia's figure is rated medium or high
in every counted year. Being outside the range on either side counts; which side is a concern is for the policy
menu (phase P4). A low-rated comparison is shown with its status but never flagged.

Windows: 2015-2019 and 2022-2024 for business demography and productivity (2020 and 2021 are left out, being
distorted by the pandemic and JobKeeper); for regulation, the two latest product market regulation vintages
(2018 and 2023) and 2021-2025 for services trade and FDI restrictiveness. Two further comparisons are reported but
do not enter the flag: the plan's fixed list (Canada, New Zealand, Norway, UK, US) and the median of all OECD
members.

A flag says where to look, not why a gap exists; it is descriptive and identifies no cause.
"""

from __future__ import annotations

import json
import math
from collections import Counter

import pandas as pd

from ..pipeline import store
from . import OUT, peers, prose
from .harmonise import ALL, ALL_GROUPS, DEMOG_GROUPS, LEVELS, MEASURES, _groups

MIN_PEERS = 4
DEMOG_WINDOWS = {"2015-2019": (2015, 2019), "2022-2024": (2022, 2024)}
WINDOWS = {
    **{m: DEMOG_WINDOWS for m in MEASURES},
    "pmr_sector": {"2018-2023": (2018, 2023)},
    "pmr_economy": {"2018-2023": (2018, 2023)},
    "stri_sector": {"2021-2025": (2021, 2025)},
    "fdi_rri": {"2021-2025": (2021, 2025)},
}
EXCLUDE_YEARS = (2020, 2021)  # demography and productivity only


def quantile(xs: list[float], q: float) -> float:
    """The q-quantile by linear interpolation between order statistics (R's type 7, numpy's default)."""
    v = sorted(xs)
    h = (len(v) - 1) * q
    lo = math.floor(h)
    return v[lo] + (h - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo])


def year_stats(au: float, values: list[float]) -> dict:
    q1, med, q3 = quantile(values, 0.25), quantile(values, 0.5), quantile(values, 0.75)
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1)) if len(values) > 1 else float("nan")
    side = "below" if au < q1 else "above" if au > q3 else "within"
    return {"au": au, "median": med, "q1": q1, "q3": q3, "mean": mean, "sd": sd, "n_peers": len(values), "side": side}


def persistent(sides: list[str]) -> str | None:
    """The side Australia is on in more than half the years (at least two), or None."""
    if len(sides) < 2:
        return None
    for s in ("below", "above"):
        if sum(x == s for x in sides) > len(sides) / 2:
            return s
    return None


def _years(df: pd.DataFrame, measure: str, lo: int, hi: int) -> list[int]:
    ys = range(lo, hi + 1)
    if measure not in ("pmr_sector", "pmr_economy", "stri_sector", "fdi_rri"):
        ys = [y for y in ys if y not in EXCLUDE_YEARS]
    return sorted(set(ys) & set(df["year"]))


def evaluate(cell: pd.DataFrame, core: list[str], years: list[int], min_peers: int = MIN_PEERS) -> list[dict]:
    """Per-year statistics for one group, measure and window. ``cell`` has country, year, value."""
    v = cell.set_index(["country", "year"])["value"]
    out = []
    for y in years:
        if ("AUS", y) not in v.index:
            continue
        vals = [v[(c, y)] for c in core if (c, y) in v.index]
        if len(vals) >= min_peers:
            out.append({"year": y, **year_stats(v[("AUS", y)], vals)})
    return out


def leave_one_out(cell: pd.DataFrame, core: list[str], years: list[int], side: str) -> dict[str, bool]:
    """For each core peer left out, whether Australia stays on ``side`` of the range in most years."""
    res = {}
    for c in core:
        rows = evaluate(cell, [p for p in core if p != c], years, MIN_PEERS - 1)
        res[c] = persistent([r["side"] for r in rows]) == side
    return res


def _rank(cell: pd.DataFrame, core: list[str], years: list[int]) -> tuple[int | None, int]:
    w = cell[cell["year"].isin(years) & cell["country"].isin(["AUS", *core])]
    means = w.groupby("country")["value"].mean()
    if "AUS" not in means:
        return None, len(means)
    return int((means > means["AUS"]).sum()) + 1, len(means)


def _comparison(cell: pd.DataFrame, others: list[str], years: list[int]) -> dict:
    """Australia against another peer set (not part of the flag): average median and the side in most years."""
    rows = evaluate(cell, others, years, MIN_PEERS)
    if not rows:
        return {"median": None, "side": None, "years": 0}
    return {
        "median": sum(r["median"] for r in rows) / len(rows),
        "side": persistent([r["side"] for r in rows]) or "within or mixed",
        "years": len(rows),
    }


def benchmark(df: pd.DataFrame, core: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The summary (one row per group, measure and window) and the annual statistics behind it."""
    core = core or list(peers.APPROVED["core"])
    members = sorted(set(df["country"]) - {"AUS"})
    fixed = [c for c in peers.FIXED]
    summary, annual = [], []
    for (g, m), cell in df.groupby(["group", "measure"]):
        if "AUS" not in set(cell["country"]):
            continue
        ratings = cell[cell["country"] == "AUS"].set_index("year")["comparability"]
        prev_gap = None
        for w, (lo, hi) in WINDOWS[m].items():
            years = _years(cell, m, lo, hi)
            rows = evaluate(cell, core, years)
            for r in rows:
                annual.append({"group": g, "measure": m, "window": w, **r})
            n = len(rows)
            counted = [r["year"] for r in rows]
            side = persistent([r["side"] for r in rows])
            loo = leave_one_out(cell, core, counted, side) if side else {}
            rating = min((ratings.get(y, "low") for y in counted), key=LEVELS.index) if counted else None
            gap = sum(r["au"] - r["median"] for r in rows) / n if n else None
            med = sum(r["median"] for r in rows) / n if n else None
            sds = [(r["au"] - r["median"]) / r["sd"] for r in rows if r["sd"] and not math.isnan(r["sd"])]
            rank, of = _rank(cell, core, counted)
            if n < 2:
                status = "too few years"
            elif not side:
                status = "within the range" if all(r["side"] == "within" for r in rows) else "outside, not persistent"
            elif (gap or 0) * (1 if side == "above" else -1) <= 0:
                status = "outside, average on the other side"
            elif not all(loo.values()):
                status = "outside, fails leave-one-out"
            elif LEVELS.index(rating) < LEVELS.index("medium"):
                status = "outside, low comparability"
            else:
                status = "flag"
            summary.append(
                {
                    "group": g,
                    "measure": m,
                    "window": w,
                    "years": n,
                    "first_year": counted[0] if counted else None,
                    "last_year": counted[-1] if counted else None,
                    "australia": sum(r["au"] for r in rows) / n if n else None,
                    "peer_median": med,
                    "peer_mean": sum(r["mean"] for r in rows) / n if n else None,
                    "peer_q1": sum(r["q1"] for r in rows) / n if n else None,
                    "peer_q3": sum(r["q3"] for r in rows) / n if n else None,
                    "gap": gap,
                    "gap_pct_of_median": 100 * gap / abs(med) if n and med else None,
                    "gap_sd": sum(sds) / len(sds) if sds else None,
                    "gap_change": gap - prev_gap if gap is not None and prev_gap is not None else None,
                    "rank": rank,
                    "of": of,
                    "years_below": sum(r["side"] == "below" for r in rows),
                    "years_above": sum(r["side"] == "above" for r in rows),
                    "side": side,
                    "leave_one_out_failed_without": ", ".join(c for c, ok in loo.items() if not ok),
                    "comparability": rating,
                    "status": status,
                    "flag": status == "flag",
                    "fixed_list": _comparison(cell, fixed, counted),
                    "oecd": _comparison(cell, members, counted),
                }
            )
            prev_gap = gap
    s = pd.DataFrame(summary)
    for k in ("fixed_list", "oecd"):
        s[f"{k}_median"] = s[k].map(lambda d: d["median"])
        s[f"{k}_side"] = s[k].map(lambda d: d["side"])
    s = s.drop(columns=["fixed_list", "oecd"])
    return s, pd.DataFrame(annual)


def build(refresh: bool = False) -> pd.DataFrame:
    """Benchmark every group and measure and write benchmarks.parquet, benchmark_years.parquet, the R cross-check
    inputs and docs/international_benchmarks.md."""
    df = pd.read_parquet(OUT / "benchmark_inputs.parquet")
    summary, annual = benchmark(df)
    summary.to_parquet(OUT / "benchmarks.parquet", index=False)
    annual.to_parquet(OUT / "benchmark_years.parquet", index=False)
    write_crosscheck(df, summary, annual)
    (store.ROOT / "docs" / "international_benchmarks.md").write_text(markdown(summary), encoding="utf-8")
    return summary


def write_crosscheck(df: pd.DataFrame, summary: pd.DataFrame, annual: pd.DataFrame) -> None:
    """Inputs and results for analysis/crosscheck_international_benchmarks.R (small CSVs, committed)."""
    d = store.ROOT / "analysis" / "crosscheck"
    d.mkdir(parents=True, exist_ok=True)
    core = list(peers.APPROVED["core"])
    keep = df[df["country"].isin(["AUS", *core])][["country", "group", "measure", "year", "value", "comparability"]]
    keep.to_csv(d / "benchmark_inputs.csv", index=False)
    annual.to_csv(d / "benchmark_years_python.csv", index=False)
    cols = ["group", "measure", "window", "years", "side", "comparability", "status"]
    summary[cols].to_csv(d / "benchmark_summary_python.csv", index=False)
    (d / "benchmark_settings.json").write_text(
        json.dumps(
            {
                "core": core,
                "min_peers": MIN_PEERS,
                "windows": WINDOWS,
                "exclude_years": list(EXCLUDE_YEARS),
                "regulation": ["pmr_sector", "pmr_economy", "stri_sector", "fdi_rri"],
                "levels": list(LEVELS),
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


def _f(v, digits=1) -> str:
    return "–" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{digits}f}"


STATUS_SHORT = {
    "flag": "**FLAG**",
    "outside, low comparability": "outside (low comparability)",
    "outside, fails leave-one-out": "outside (fails leave-one-out)",
    "outside, not persistent": "mixed",
    "outside, average on the other side": "mixed (average on the other side)",
    "within the range": "within",
    "too few years": "too few years",
}


def markdown(s: pd.DataFrame) -> str:
    G = _groups()
    labels = {g: G[g]["label"] for g in G} | {ALL: "Business economy"}
    order = [ALL, *DEMOG_GROUPS, "AGR", "PUB"]
    core = peers.APPROVED["core"]
    names = {r["country"]: r["name"] for r in json.loads((OUT / "peers.json").read_text("utf-8"))["ranking"]}
    counts = Counter(s["status"])
    flags = s[s["flag"]].copy()
    lines = [
        "# How Australia compares: benchmarks against comparable economies",
        "",
        "Generated by `alicia international benchmark` (phase P3 of the "
        "[benchmarking plan](forward_plan_international_benchmarking.md), E-106). Peers: the core group "
        f"({', '.join(names.get(c, c) for c in core)}). Inputs and definitions: "
        "[methods note](methods_international_benchmarks.md). Tables: "
        "`data/processed/international/benchmarks.parquet` (summary) and `benchmark_years.parquet` (each year). "
        "Cross-checked in R: `analysis/crosscheck_international_benchmarks.R`.",
        "",
        "## Rule",
        "",
        prose(__doc__),
        "",
        "## Flags",
        "",
        f"{len(flags)} of {len(s)} comparisons are flagged. Status counts: "
        + "; ".join(f"{STATUS_SHORT.get(k, k)} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        + ".",
        "",
    ]
    if len(flags):
        lines += [
            "| Group | Measure | Window | Australia | Peer median | Peer range (25th-75th) | Gap | Side | Years "
            "| Rank |",
            "|---|---|---|---:|---:|---|---:|---|---:|---:|",
        ]
        flags["o"] = flags["group"].map(lambda g: order.index(g) if g in order else 99)
        for r in flags.sort_values(["measure", "o", "window"]).itertuples():
            lines.append(
                f"| {labels[r.group]} | {MEASURES[r.measure][0]} | {r.window} | {_f(r.australia, 2)} | "
                f"{_f(r.peer_median, 2)} | {_f(r.peer_q1, 2)} to {_f(r.peer_q3, 2)} | {_f(r.gap, 2)} | {r.side} | "
                f"{r.years} | {int(r.rank)} of {int(r.of)} |"
            )
    else:
        lines.append("No comparison meets every condition of the flag rule.")
    lines += [
        "",
        "Gaps are Australia less the peer median, in the measure's unit; the range is the average of each year's "
        "25th to 75th percentile of the core peers. Rank 1 is the highest value among Australia and the peers.",
        "",
        "## By measure",
        "",
        "Status of every comparison: **FLAG**; outside (low comparability): outside the range in most years and "
        "robust, but Australia's figure is rated low, so shown and not flagged; outside (fails leave-one-out); "
        "mixed: outside in some years only; within; too few years: fewer than two years with four peers.",
        "",
    ]
    for m in MEASURES:
        sub = s[s["measure"] == m]
        if sub.empty:
            continue
        label, unit = MEASURES[m]
        wins = list(WINDOWS[m])
        lines += [
            f"### {label}",
            "",
            f"Unit: {unit}. Australia | peer median (range) | status, by window.",
            "",
            "| Group | " + " | ".join(wins) + " |",
            "|---|" + "---|" * len(wins),
        ]
        for g in order:
            cells = []
            for w in wins:
                r = sub[(sub["group"] == g) & (sub["window"] == w)]
                if r.empty:
                    cells.append("")
                    continue
                r = r.iloc[0]
                if not r["years"]:
                    cells.append("no years with enough peers")
                    continue
                cells.append(
                    f"{_f(r['australia'])} \\| {_f(r['peer_median'])} ({_f(r['peer_q1'])} to {_f(r['peer_q3'])}) "
                    f"\\| {STATUS_SHORT.get(r['status'], r['status'])}"
                )
            if any(cells):
                lines.append(f"| {labels[g]} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += [
        "## Limits",
        "",
        "- Six peers make wide ranges: one country can move the median, hence the leave-one-out test.",
        "- The 2022-2024 window is thin for business demography: the peers' data end in 2022 or 2023, and the "
        "UK's in 2018.",
        "- Australia's gross birth, death and churn rates are rated low (E-105, accepted by the owner, who may "
        "revisit it: `GROSS_RATES_RATING` in `international/harmonise.py`), so gaps in them are shown, not flagged.",
        "- Regulation indicators are national; a group's sector indicators cover only part of it. The business "
        f"economy is {', '.join(ALL_GROUPS)}.",
        "- A flag is descriptive: it says where to look, not what causes the gap or whether a policy would close it.",
        "",
    ]
    return "\n".join(lines)
