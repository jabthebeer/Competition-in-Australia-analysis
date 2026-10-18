"""Event-study figure for the trading-hours case, drawn from estimate.json as a static SVG.

Two panels on one scale: entries and exits per 100 businesses, WA's general retail relative to
the comparison states and net of the placebo-industry mean, with the 90% placebo band.

Run: uv run python analyses/wa_trading_hours/figure.py
Writes: docs/figures/wa_trading_hours_event_study.svg
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "docs" / "figures" / "wa_trading_hours_event_study.svg"

W, H = 760, 350
PANEL_W, TOP, BOTTOM = 310, 72, 280  # plot area per panel; y pixels of the data range
LEFT = (56, 56 + PANEL_W + 56)
Y_MIN, Y_MAX = -13.0, 7.0
Y_TICKS = (-10, -5, 0, 5)
KS = list(range(-3, 8))
FY = {k: f"{2006 + k + 4}-{str(2007 + k + 4)[2:]}" for k in KS}  # k = 0 is 2010-11

STYLE = """
  .s { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#8a8984; --grid:#e8e7e2;
       --series:#2a78d6; --band:#cde2fb; --marker:#d0cfc8; }
  @media (prefers-color-scheme: dark) {
    .s { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#8f8e86; --grid:#2e2e2c;
         --series:#3987e5; --band:#1c3a63; --marker:#4a4a46; }
  }
  .bg { fill: var(--surface); }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .zero { stroke: var(--muted); stroke-width: 1; }
  .reform { stroke: var(--marker); stroke-width: 1.5; stroke-dasharray: 4 3; }
  .band { fill: var(--band); }
  .line { fill: none; stroke: var(--series); stroke-width: 2; stroke-linejoin: round; }
  .dot { fill: var(--series); stroke: var(--surface); stroke-width: 2; }
  text { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: var(--ink2); font-size: 11px; }
  .title { fill: var(--ink); font-size: 13px; font-weight: 600; }
  .note { fill: var(--muted); font-size: 10.5px; }
  .value { fill: var(--ink); font-size: 11px; font-variant-numeric: tabular-nums; }
"""


def y(v: float) -> float:
    return TOP + (Y_MAX - v) / (Y_MAX - Y_MIN) * (BOTTOM - TOP)


def x(left: int, k: int) -> float:
    return left + 10 + (k - KS[0]) / (KS[-1] - KS[0]) * (PANEL_W - 20)


def panel(left: int, title: str, net: dict, band: dict, delta: float, interval: list[float]) -> list[str]:
    pts = {k: (0.0 if k == -1 else net[str(k)]) for k in KS}
    bands = {k: ((0.0, 0.0) if k == -1 else tuple(band[str(k)])) for k in KS}
    out = [f'<text class="title" x="{left}" y="24">{title}</text>']
    out.append(
        f'<text class="note" x="{left}" y="40">Net effect {delta:+.1f} per 100 '
        f"(90% interval {interval[0]:+.1f} to {interval[1]:+.1f})</text>"
    )
    for t in Y_TICKS:
        cls = "zero" if t == 0 else "grid"
        out.append(f'<line class="{cls}" x1="{left}" x2="{left + PANEL_W}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>')
        if left == LEFT[0]:
            out.append(f'<text x="{left - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{t:+d}</text>'.replace("+0", "0"))
    upper = " ".join(f"{x(left, k):.1f},{y(bands[k][1]):.1f}" for k in KS)
    lower = " ".join(f"{x(left, k):.1f},{y(bands[k][0]):.1f}" for k in reversed(KS))
    out.append(f'<polygon class="band" points="{upper} {lower}"/>')
    # Reform markers: weeknights and precincts from 2010-11 (k = 0); Sundays from 2012-13 (k = 2).
    xr = (x(left, -1) + x(left, 0)) / 2
    out.append(f'<line class="reform" x1="{xr:.1f}" x2="{xr:.1f}" y1="{TOP}" y2="{BOTTOM}"/>')
    out.append(f'<text class="note" x="{xr + 4:.1f}" y="{TOP - 6}">Weeknights</text>')
    xs = x(left, 2)
    out.append(f'<line class="reform" x1="{xs:.1f}" x2="{xs:.1f}" y1="{TOP}" y2="{BOTTOM}"/>')
    out.append(f'<text class="note" x="{xs + 4:.1f}" y="{TOP - 6}">Sundays</text>')
    out.append(f'<polyline class="line" points="{" ".join(f"{x(left, k):.1f},{y(pts[k]):.1f}" for k in KS)}"/>')
    for k in KS:
        out.append(
            f'<circle class="dot" cx="{x(left, k):.1f}" cy="{y(pts[k]):.1f}" r="4">'
            f"<title>{FY[k]}: {pts[k]:+.1f} per 100 (90% band {bands[k][0]:+.1f} to {bands[k][1]:+.1f})</title>"
            "</circle>"
        )
    for k in KS[::2]:
        out.append(f'<text x="{x(left, k):.1f}" y="{BOTTOM + 18}" text-anchor="middle">{FY[k]}</text>')
    return out


def main() -> None:
    r = json.loads((HERE / "estimate.json").read_text(encoding="utf-8"))
    body = []
    for left, m, title in ((LEFT[0], "entries", "Business entries"), (LEFT[1], "exits", "Business exits")):
        ev, p = r[m]["event_study"], r[m]["primary"]
        body += panel(left, title, ev["net"], ev["net_band_90"], p["delta"], p["interval_90"])
    body.append(
        f'<text class="note" x="{LEFT[0]}" y="{H - 30}">Per 100 businesses at the start of the year: '
        "WA general retail vs other states, net of the placebo industry groups (472 and 451).</text>"
    )
    body.append(
        f'<text class="note" x="{LEFT[0]}" y="{H - 14}">Reference year 2009-10. Shaded: 90% placebo band. '
        "Dashed: 9pm weeknight trading (1 Nov 2010) and Sunday trading (26 Aug 2012).</text>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        'aria-labelledby="t d" class="s">\n'
        '<title id="t">Perth trading-hours deregulation: event study for retail entry and exit</title>\n'
        '<desc id="d">Annual effects relative to 2009-10, net of the placebo-industry mean, with 90% placebo bands. '
        "All post-reform years lie inside the bands for both entries and exits.</desc>\n"
        f"<style>{STYLE}</style>\n"
        f'<rect class="bg" width="{W}" height="{H}" rx="6"/>\n' + "\n".join(body) + "\n</svg>\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
