"""Markdown tables for docs/power_study.md, read from power.json and power_prices.json (no numbers typed by hand).

uv run python analyses/power_study/tables.py > /tmp/power_tables.md
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYERS = ("twoway", "state_year", "saturated", "controls", "imputation", "sdid", "gsynth")
HEAD = ("Two-way", "+ state × year", "Saturated", "Controls", "Imputation", "Synthetic DiD", "Gen. synth.")
FAMILIES = (("industries", "Placebo industries"), ("states", "Placebo states"), ("dates", "Fake dates"))
MIN_DRAWS = 5  # fewer draws: the spread is not reported


def _fmt(x) -> str:
    return "—" if x is None else f"{x:.1f}"


def _row(layers: dict, extra: list[str]) -> str:
    vals = {k: layers[k]["mde"] for k in LAYERS}
    best = min((v for v in vals.values() if v is not None), default=None)
    cells = [f"**{_fmt(v)}**" if v is not None and v == best else _fmt(v) for v in vals.values()]
    return "| " + " | ".join(extra + cells) + " |"


def mde_table(reforms: list[dict], measure: str, registered: bool) -> list[str]:
    cols = ["Reform", "Mean rate", "Registered design", *HEAD] if registered else ["Reform", "Mean rate", *HEAD]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in reforms:
        o = r["outcomes"].get(measure)
        if not o:
            continue
        extra = [r["title"], f"{o['mean_rate']:.1f}"]
        if registered:
            reg = (r.get("registered_design") or {}).get(measure)
            extra.append(_fmt(reg["mde"]) if reg else "—")
        out.append(_row(o["layers"], extra))
    return out


def _err(layer: dict) -> str:
    """Mean (systematic error) / root mean square (total error) of the placebo estimates."""
    if layer["mean"] is None:
        return "—"
    return f"{layer['mean']:+.1f} / {layer['rms']:.1f}"


ERR_LAYERS = ("twoway", "saturated", "imputation", "sdid")


def _family_rows(fams: dict, lead: list[str], labels) -> list[str]:
    rows, first = [], True
    for fam, label in labels:
        f = fams.get(fam)
        if not f or f["draws"] < MIN_DRAWS:
            continue
        lay = f["layers"]
        ok = {k: v["rms"] for k, v in lay.items() if v["rms"] is not None}
        best = min(ok, key=ok.get) if ok else None
        cells = [*(lead if first else [""] * len(lead)), label, str(f["draws"])]
        cells += [_err(lay[k]) for k in ERR_LAYERS] + [HEAD[LAYERS.index(best)] if best else "—"]
        rows.append("| " + " | ".join(cells) + " |")
        first = False
    return rows


def family_table(reforms: list[dict], measure: str) -> list[str]:
    """Each placebo family: mean / RMS of placebo estimates for four layers, and the layer with the smallest RMS."""
    cols = ["Reform", "Family", "Draws", "Two-way", "Saturated", "Imputation", "Synthetic DiD", "Smallest RMS"]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in reforms:
        o = r["outcomes"].get(measure)
        if not o:
            continue
        fams = {"industries": {"draws": len(o["placebo_estimates"]), "layers": o["layers"]}, **o.get("families", {})}
        out += _family_rows(fams, [r["title"]], FAMILIES)
    return out


def price_table(reforms: list[dict]) -> list[str]:
    cols = ["Reform", "CPI class", "Registered design", *HEAD]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in reforms:
        for o in r["outcomes"].values():
            reg = o.get("registered_design")
            out.append(_row(o["layers"], [r["title"], o["name"], _fmt(reg["mde"]) if reg else "—"]))
    return out


def price_family_table(reforms: list[dict]) -> list[str]:
    cols = ["Reform", "CPI class", "Family", "Draws", *(HEAD[LAYERS.index(k)] for k in ERR_LAYERS), "Smallest RMS"]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    labels = (("industries", "Placebo classes"), *FAMILIES[1:])
    for r in reforms:
        for o in r["outcomes"].values():
            fams = {"industries": {"draws": len(o["placebo_estimates"]), "layers": o["layers"]}, **o["families"]}
            out += _family_rows(fams, [r["title"], o["name"]], labels)
    return out


def main() -> None:
    cabee = json.loads((HERE / "power.json").read_text("utf-8"))["reforms"]
    old = [r for r in cabee if not any("New family" in n for n in r["notes"])]
    new = [r for r in cabee if any("New family" in n for n in r["notes"])]
    lines: list[str] = []
    for measure in ("entries", "exits"):
        lines += [f"### Business {measure}: evaluated reforms", "", *mde_table(old, measure, True), ""]
        lines += [f"### Business {measure}: new families", "", *mde_table(new, measure, False), ""]
        lines += [f"### Business {measure}: placebo families", "", *family_table(cabee, measure), ""]
    infeasible = [(r["title"], "; ".join(r["feasible"]["reasons"])) for r in cabee if not r["feasible"]["ok"]]
    lines += ["### Not feasible with CABEE classes", "", "| Reform | Reason |", "|---|---|"]
    lines += [f"| {t} | {why} |" for t, why in infeasible] + [""]
    p = HERE / "power_prices.json"
    if p.exists():
        prices = json.loads(p.read_text("utf-8"))["reforms"]
        lines += ["### Prices", "", *price_table(prices), "", "### Prices: placebo families", ""]
        lines += [*price_family_table(prices), ""]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
