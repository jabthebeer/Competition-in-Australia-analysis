"""The website's Framework page (``framework.html``): the productivity impact framework as pictures, tables and a
rubric, rendered to static HTML from ``register/framework.py``.

The page shows how the ideas fit together, a table of key ideas in plain words, the signs that competition has
weakened, the rubric (eight drivers by five marks, with the register's items counted in each cell), how an item is
marked, one real assessment on the rubric, the double-counting rules, regulatory complexity (how duplication,
differences between states and complex rules are recorded, DECISIONS E-96) and the limits. Hovering over, focusing or
tapping a component shows more detail; the details are also in the page, linked by ``aria-describedby``, for screen
readers. The evidence and full marking guide for each driver sit in a collapsible section under the rubric."""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter
from html import escape
from importlib import resources

from ..register import framework as fw
from ..register.regimes import ISSUE_HELP, ISSUE_LABELS, TIER_LABELS, Regime, industry_profiles, load_regimes
from ..register.regimes import regimes_by_record as _regimes_by_record
from ..register.schema import ChangeRecord
from .archive import FAMILY_LABELS

# The worked example: a reform most readers know, with marks on several drivers.
EXAMPLE_ID = "nsw-rideshare-2015"
MARK_CLS = {2: "m2", 1: "m1", 0: "m0", -1: "mn1", -2: "mn2"}
MARK_ORDER = (-2, -1, 0, 1, 2)
MARK_HELP = {
    2: "A large, direct improvement on this driver, such as removing a ban or a cap.",
    1: "A modest improvement.",
    0: "No material effect: small or speculative effects are left at 0.",
    -1: "A modest harm.",
    -2: "A large, direct harm on this driver, such as a ban, a cap or a large distorting tax.",
}

# Line icons on a 24-unit grid, drawn with the current text colour (see .ic in the template).
ICONS = {
    "entry-exit": '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/><path d="M3 12h11"/><path d="M10 8l4 4-4 4"/>',
    "competition": (
        '<path d="M8 4h8v6a4 4 0 0 1-8 0z"/><path d="M8 6H5v1a3 3 0 0 0 3 3"/><path d="M16 6h3v1a3 3 0 0 1-3 3"/>'
        '<path d="M12 14v4"/><path d="M8 20h8"/>'
    ),
    "market-integration": (
        '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
        '<path d="M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>'
    ),
    "capital": '<path d="M3 20V10l5 3v-3l5 3v-3l5 3V4h3v16z"/><path d="M2 20h20"/>',
    "labour": (
        '<circle cx="9" cy="7" r="3.5"/><path d="M3 20v-1.5A5.5 5.5 0 0 1 8.5 13h1a5.5 5.5 0 0 1 5.5 5.5V20"/>'
        '<path d="M16 9h6"/><path d="M19 6l3 3-3 3"/>'
    ),
    "burden": (
        '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/>'
        '<path d="M8.5 9.5h7M8.5 13h7M8.5 16.5h4"/>'
    ),
    "innovation": (
        '<path d="M9 18h6M10 21h4"/>'
        '<path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2v.5h5V16c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>'
    ),
    "prices-taxes": '<path d="M3 4v7l10 10 8-8L11 3H4a1 1 0 0 0-1 1z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "dynamism": '<path d="M13 3L5 13h6l-1 8 8-10h-6z"/>',
    "inputs": '<path d="M12 4l9 5-9 5-9-5z"/><path d="M3 14l9 5 9-5"/>',
    "efficiency": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l3.5-5"/><circle cx="12" cy="17" r="1"/>',
    "productivity": '<path d="M3 20h18"/><path d="M6 16v-3M10 16v-6M14 16V8M18 16V5"/>',
    "mfp": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 16v4M17 18h4"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
    "cycle": (
        '<path d="M20 11a8 8 0 0 0-14.3-4.3L4 9"/><path d="M4 4v5h5"/>'
        '<path d="M4 13a8 8 0 0 0 14.3 4.3L20 15"/><path d="M20 20v-5h-5"/>'
    ),
    "describe": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 16h6"/>',
    "mark": (
        '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/>'
        '<circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>'
    ),
    "add": '<path d="M18 5H6l6 7-6 7h12"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "reach": '<circle cx="12" cy="12" r="2"/><circle cx="12" cy="12" r="5.5"/><circle cx="12" cy="12" r="9"/>',
    "reform": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13 7l4 4"/>',
    "setting": '<path d="M3 9l9-5 9 5"/><path d="M5 9v9M9.5 9v9M14.5 9v9M19 9v9"/><path d="M3 20h18"/>',
    "barrier": (
        '<rect x="3" y="6" width="18" height="12" rx="1"/><path d="M3 12h18M9 6v6M15 6v6M6 12v6M12 12v6M18 12v6"/>'
    ),
    "compare": (
        '<rect x="3" y="6" width="7" height="12" rx="1"/><rect x="14" y="6" width="7" height="12" rx="1"/>'
        '<path d="M10 12h4"/>'
    ),
    "scales": '<path d="M12 4v16M7 20h10M4 8h16"/><path d="M6 8l-3 6a3 3 0 0 0 6 0zM18 8l-3 6a3 3 0 0 0 6 0z"/>',
    "approx": '<path d="M4 10c2-2 4-2 6 0s4 2 6 0 3-1.5 4-1.5M4 16c2-2 4-2 6 0s4 2 6 0 3-1.5 4-1.5"/>',
    "review": '<circle cx="9" cy="8" r="3.5"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 11l2 2 4-4"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
    "arrow": '<path d="M4 12h15"/><path d="M14 7l5 5-5 5"/>',
}
PILLAR_ICONS = {"dynamism": "dynamism", "inputs": "inputs", "efficiency": "efficiency"}
CONCEPT_ICONS = {
    "productivity": "productivity",
    "capital-deepening": "capital",
    "mfp": "mfp",
    "dynamic": "innovation",
    "productive": "efficiency",
    "allocative": "target",
    "competition": "competition",
    "dynamism": "cycle",
    "markup": "prices-taxes",
}
SIGN_ICONS = {"entry": "entry-exit", "jobs": "labour", "markups": "prices-taxes", "investment": "capital"}
STEP_ICONS = ("describe", "mark", "add", "star", "reach")
LIMIT_ICONS = ("scales", "approx", "review", "reach")
BANDS = (
    ("−3 or less", "strongly-negative", "mn2"),
    ("−1 to −2", "negative", "mn1"),
    ("0", "neutral", "m0"),
    ("+1 to +2", "positive", "m1"),
    ("+3 or more", "strongly-positive", "m2"),
)


def icon(name: str, cls: str = "ic") -> str:
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


def _signed(n: int) -> str:
    return f"+{n}" if n > 0 else (f"−{abs(n)}" if n < 0 else "0")


def _items(n: int) -> str:
    return f"{n} item" if n == 1 else f"{n} items"


def _cite(keys) -> str:
    return "; ".join(
        f'<a href="{escape(fw.SOURCES[k]["url"])}" target="_blank" rel="noopener">{escape(fw.SOURCES[k]["label"])}</a>'
        for k in keys
    )


def _short(label: str) -> str:
    """'Andrews and Hansell (2019), Productivity-enhancing ...' -> 'Andrews and Hansell (2019)'."""
    m = re.match(r"^(.*?\(\d{4}\))", label)
    return m.group(1) if m else label


def _cite_short(keys) -> str:
    """Short author-year links, with the full reference as the link's title."""
    return "; ".join(
        f'<a href="{escape(fw.SOURCES[k]["url"])}" title="{escape(fw.SOURCES[k]["label"])}" target="_blank" '
        f'rel="noopener">{escape(_short(fw.SOURCES[k]["label"]))}</a>'
        for k in keys
    )


def _cite_text(keys) -> str:
    """Short author-year references as plain text, for hover details (which cannot hold links)."""
    return "; ".join(escape(_short(fw.SOURCES[k]["label"])) for k in keys)


class _Tips:
    """Collects the hover details: each component gets ``data-tip`` pointing at a hidden element with its detail,
    which the page script shows on hover, focus or tap, and which screen readers read as the description."""

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def __call__(self, html: str, wide: bool = False, focusable: bool = False) -> str:
        tid = f"tip-{len(self.items) + 1}"
        self.items.append((tid, html))
        attrs = f' data-tip="{tid}" aria-describedby="{tid}"'
        if wide:
            attrs += ' data-wide="1"'
        if focusable:
            attrs += ' tabindex="0"'
        return attrs

    def html(self) -> str:
        return '<div class="tip-srcs" hidden>' + "".join(f'<div id="{i}">{h}</div>' for i, h in self.items) + "</div>"


def _tip(title: str, *paras: str, extra: str = "") -> str:
    body = "".join(f"<p>{p}</p>" for p in paras if p)
    return f"<strong>{escape(title)}</strong>{body}{extra}"


def _driver_chip(key: str, tips: _Tips) -> str:
    d = fw.DRIVERS[key]
    tip = _tip(d["label"], escape(d["plain"]), '<span class="tip-ex">Select to see its row in the rubric.</span>')
    return f'<a class="dchip" href="#r-{escape(key)}"{tips(tip)}>{icon(key)}<span>{escape(d["short"])}</span></a>'


def _flow(tips: _Tips) -> str:
    """How the ideas fit together: competition and dynamism push firms to invest, use people well and work
    efficiently, which lifts productivity. Each box lists its drivers."""

    def node(pk: str, logic: str) -> str:
        p = fw.PILLARS[pk]
        chips = "".join(_driver_chip(k, tips) for k, d in fw.DRIVERS.items() if d["pillar"] == pk)
        tip = _tip(p["label"], escape(p["question"]), escape(logic))
        return (
            f'<div class="fnode" {tips(tip, wide=True, focusable=True)}>'
            f'<div class="fhead"><span class="badge">{icon(PILLAR_ICONS[pk])}</span><h3>{escape(p["label"])}</h3></div>'
            f'<p>{escape(p["question"])}</p><div class="chips">{chips}</div></div>'
        )

    goal_tip = _tip("Higher productivity", escape(fw.LOGIC[0]))
    arrow = f'<div class="farrow" aria-hidden="true">{icon("arrow")}</div>'
    inputs = (
        "Workers get more and better capital to work with (capital deepening), and people move to the jobs where "
        "they are most productive."
    )
    return f"""<div class="flow" role="group" aria-label="How the drivers lift productivity">
  {node("dynamism", fw.LOGIC[2])}
  {arrow}
  <div class="fmid">
    {node("inputs", inputs)}
    {node("efficiency", fw.LOGIC[1])}
  </div>
  {arrow}
  <div class="fnode goal" {tips(goal_tip, wide=True, focusable=True)}>
    <div class="fhead"><span class="badge">{icon("productivity")}</span><h3>Higher productivity</h3></div>
    <p>More output for every hour worked, through more capital per worker and better use of every input.</p>
  </div>
</div>"""


def _concepts(tips: _Tips) -> str:
    rows = []
    for c in fw.CONCEPTS:
        tip = _tip(c["label"], escape(c["detail"]))
        rows.append(
            f'<tr {tips(tip, focusable=True)}><th scope="row"><span class="cl"><span class="badge sm">'
            f"{icon(CONCEPT_ICONS[c['key']])}</span><span>{escape(c['label'])}</span></span></th>"
            f"<td>{escape(c['plain'])}</td>"
            f'<td class="info">{icon("info")}</td></tr>'
        )
    return (
        '<div class="panel tight"><table class="concepts"><thead><tr><th scope="col">Idea</th>'
        '<th scope="col">In plain words</th><th scope="col"><span class="sr-only">More</span></th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _signs(tips: _Tips) -> str:
    tiles = []
    for s in fw.SIGNS:
        tip = _tip(s["label"], escape(s["detail"]), extra=f'<p class="tip-ex">Source: {_cite_text(s["sources"])}</p>')
        tiles.append(
            f'<div class="sign" {tips(tip, focusable=True)}><div class="fhead"><span class="badge neg">'
            f"{icon(SIGN_ICONS[s['key']])}</span><h3>{escape(s['label'])}</h3></div>"
            f'<p class="fig">{escape(s["figure"])}</p><p class="small muted">{escape(s["plain"])}</p></div>'
        )
    return f'<div class="signs">{"".join(tiles)}</div>'


def _cell_examples(records: list[ChangeRecord], driver: str, mark: int) -> tuple[int, list[str]]:
    """How many items have this mark on this driver, and up to three examples (a family counted once)."""
    hits = [r for r in records if r.assessment and r.assessment.mark(driver) == mark]
    groups: dict[str, list[ChangeRecord]] = {}
    for r in hits:
        groups.setdefault(r.family or r.id, []).append(r)
    order = sorted(
        groups.values(),
        key=lambda g: (g[0].assessment.main_driver != driver, -len(g), -abs(g[0].assessment.total), g[0].title),
    )
    names = [
        f"{FAMILY_LABELS.get(g[0].family, g[0].title)} ({len(g)} items)" if len(g) > 1 else g[0].title
        for g in order[:3]
    ]
    return len(hits), names


def _main_counts(records: list[ChangeRecord]) -> dict[str, dict]:
    counts: dict[str, dict] = {}
    for r in records:
        a = r.assessment
        if a is None:
            continue
        c = counts.setdefault(a.main_driver, {"neg": 0, "pos": 0, "zero": 0})
        c["neg" if a.total < 0 else "pos" if a.total > 0 else "zero"] += 1
    return counts


def _rubric(records: list[ChangeRecord], tips: _Tips) -> str:
    counts = _main_counts(records)
    head = ['<th scope="col" class="dcol">Driver</th>']
    for m in MARK_ORDER:
        tip = _tip(f"{_signed(m)}: {fw.MARK_LABELS[m]}", escape(MARK_HELP[m]))
        head.append(
            f'<th scope="col" class="mcol{" zcol" if m == 0 else ""}" {tips(tip, focusable=True)}>'
            f'<span class="mk {MARK_CLS[m]}">{_signed(m)}</span>'
            f'<span class="ml">{escape(fw.MARK_LABELS[m])}</span></th>'
        )
    body = []
    for pk, p in fw.PILLARS.items():
        body.append(
            f'<tr class="prow"><th colspan="6" scope="colgroup"><span class="badge sm">{icon(PILLAR_ICONS[pk])}'
            f'</span><span class="pl">{escape(p["label"])}</span>'
            f'<span class="pq">{escape(p["question"])}</span></th></tr>'
        )
        for k, d in fw.DRIVERS.items():
            if d["pillar"] != pk:
                continue
            c = counts.get(k, {"neg": 0, "pos": 0, "zero": 0})
            n_main = c["neg"] + c["pos"] + c["zero"]
            look = "".join(f"<li>{escape(x)}</li>" for x in d["look_for"])
            dtip = _tip(
                d["label"],
                f"<em>{escape(d['question'])}</em>",
                escape(d["why"]),
                extra=f"<p><b>Look for</b></p><ul>{look}</ul>"
                f'<p class="tip-ex">{_items(n_main)} have this as their main driver ({c["neg"]} negative overall, '
                f"{c['pos']} positive). Sources: {_cite_text(d['why_sources'])}.</p>",
            )
            cells = [
                f'<th scope="row" class="drv" {tips(dtip, wide=True)}><div class="dwrap"><span class="badge">'
                f'{icon(k)}</span><div><a class="dname" href="#d-{escape(k)}">{escape(d["label"])}</a>'
                f'<span class="dplain">{escape(d["plain"])}</span></div></div></th>'
            ]
            for m in MARK_ORDER:
                label = f"{_signed(m)} {fw.MARK_LABELS[m]}"
                if m == 0:
                    tip = _tip(f"0 on {d['short'].lower()}", escape(MARK_HELP[0]))
                    cells.append(f'<td class="c c0" data-label="{escape(label)}" {tips(tip, focusable=True)}>—</td>')
                    continue
                n, ex = _cell_examples(records, k, m)
                found = (
                    f"In the register: {_items(n)}." + (f" Examples: {escape('; '.join(ex))}." if ex else "")
                    if n
                    else "No item in the register has this mark yet."
                )
                tip = _tip(f"{label}: {d['label']}", escape(d["marks"][m]), extra=f'<p class="tip-ex">{found}</p>')
                cells.append(
                    f'<td class="c c{MARK_CLS[m]}{"" if n else " empty"}" data-label="{escape(label)}" '
                    f"{tips(tip, focusable=True)}>"
                    f'<span class="ct">{escape(d["marks_short"][m])}</span>'
                    f'<span class="n">{_items(n) if n else "none yet"}</span></td>'
                )
            body.append(f'<tr id="r-{escape(k)}">{"".join(cells)}</tr>')
    return f"""<div class="rubric-wrap"><table class="rubric">
  <caption class="sr-only">The rubric: each driver of productivity, and what each mark from −2 to +2 means for it,
  with the number of register items given that mark.</caption>
  <thead><tr>{"".join(head)}</tr></thead>
  <tbody>{"".join(body)}</tbody>
</table></div>"""


def _driver_details(records: list[ChangeRecord]) -> str:
    counts = _main_counts(records)
    out = []
    for k, d in fw.DRIVERS.items():
        c = counts.get(k, {"neg": 0, "pos": 0, "zero": 0})
        total = c["neg"] + c["pos"] + c["zero"]
        marks = "".join(
            f'<tr><td><span class="mk {MARK_CLS[m]}">{_signed(m)}</span></td><td>{escape(t)}</td></tr>'
            for m, t in d["marks"].items()
        )
        look = "".join(f"<li>{escape(x)}</li>" for x in d["look_for"])
        out.append(f"""<details class="ddet" id="d-{escape(k)}">
  <summary><span class="badge sm">{icon(k)}</span><span class="dl">{escape(d["label"])}</span>
  <span class="dq">{escape(d["question"])}</span></summary>
  <div class="ddet-body">
    <p>{escape(d["why"])} <span class="cite">{_cite(d["why_sources"])}</span></p>
    <div class="two">
      <div><h4>Look for</h4><ul>{look}</ul></div>
      <div><h4>Full marking guide</h4><table class="mk-table"><tbody>{marks}</tbody></table></div>
    </div>
    <p class="small muted"><a href="index.html#driver={escape(k)}">{_items(total)} in the register</a> have this as
    their main driver ({c["neg"]} negative overall, {c["pos"]} positive). Policy costing channels:
    {", ".join(d["channels"])}.</p>
  </div>
</details>""")
    return "".join(out)


def _rings(level: int) -> str:
    """Reach as rings: one ring filled per level, from narrow (1) to economy-wide (4)."""
    rings = "".join(
        f'<circle cx="12" cy="12" r="{r}" class="{"on" if i <= level else "off"}"/>'
        for i, r in reversed(list(enumerate((3, 6, 8.5, 11), 1)))
    )
    return f'<svg class="rings" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{rings}</svg>'


def _bars(level: int) -> str:
    """Confidence as signal bars: three filled for high, one for low."""
    bars = "".join(
        f'<rect x="{3 + i * 7}" y="{20 - h}" width="4.5" height="{h}" rx="1" class="{"on" if i < level else "off"}"/>'
        for i, h in enumerate((7, 12, 17))
    )
    return f'<svg class="bars" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{bars}</svg>'


def _marking(records: list[ChangeRecord], tips: _Tips) -> str:
    assessed = [r for r in records if r.assessment]
    steps = []
    for i, ((title, short), full) in enumerate(zip(fw.STEP_TITLES, fw.STEPS, strict=True), 1):
        steps.append(
            f'<li class="step" {tips(_tip(f"Step {i}: {title}", escape(full)), focusable=True)}>'
            f'<span class="num">{i}</span><span class="badge">{icon(STEP_ICONS[i - 1])}</span>'
            f'<strong>{escape(title)}</strong><span class="small muted">{escape(short)}</span></li>'
        )
    bands = []
    for rng, key, cls in BANDS:
        n = sum(1 for r in assessed if r.assessment.rating == key)
        tip = _tip(
            fw.RATING_LABELS[key],
            f"Overall mark {escape(rng)}.",
            extra=f'<p class="tip-ex">{_items(n)} in the register.</p>',
        )
        bands.append(
            f'<div class="band {cls}" {tips(tip, focusable=True)}><span class="br">{escape(rng)}</span>'
            f'<span class="bl">{escape(fw.RATING_LABELS[key])}</span><span class="bn">{_items(n)}</span></div>'
        )
    reach = []
    for i, (k, v) in enumerate(fw.REACH.items(), 1):
        n = sum(1 for r in assessed if r.assessment.reach == k)
        tip = _tip(v["label"], escape(v["help"]), extra=f'<p class="tip-ex">{_items(n)} in the register.</p>')
        reach.append(
            f"<li {tips(tip, focusable=True)}>{_rings(i)}<span><strong>{escape(v['label'])}</strong>"
            f'<span class="small muted">{escape(v["help"])}</span></span><span class="cnt">{n}</span></li>'
        )
    conf = []
    for i, (k, v) in enumerate(fw.CONFIDENCE.items()):
        n = sum(1 for r in assessed if r.assessment.confidence == k)
        tip = _tip(
            f"{v['label']} confidence", escape(v["help"]), extra=f'<p class="tip-ex">{_items(n)} in the register.</p>'
        )
        conf.append(
            f"<li {tips(tip, focusable=True)}>{_bars(3 - i)}<span><strong>{escape(v['label'])}</strong>"
            f'<span class="small muted">{escape(v["help"])}</span></span><span class="cnt">{n}</span></li>'
        )
    kinds = []
    for k, v in fw.KINDS.items():
        n = sum(1 for r in assessed if r.kind == k)
        kinds.append(
            f'<li><span class="badge">{icon(k)}</span><span><strong>{escape(v["label"])}</strong>'
            f'<span class="small muted">{escape(v["help"])}</span></span><span class="cnt">{n}</span></li>'
        )
    return f"""<ol class="steps-strip">{"".join(steps)}</ol>
<div class="compare">
  <div class="cmp"><span class="badge">{icon("reform")}</span><div><strong>A reform</strong>
  <span class="small muted">is marked against the settings it replaced or would replace: before against
  after.</span></div></div>
  <div class="cmp"><span class="badge">{icon("compare")}</span><div><strong>A setting or barrier</strong>
  <span class="small muted">is marked against the same market without it: with against without.</span></div></div>
</div>
<h3 class="sub">The overall mark: add the eight marks, then read the band</h3>
<div class="bands" role="group" aria-label="Overall mark bands">{"".join(bands)}</div>
<p class="small muted">An item with both positive and negative marks is flagged as mixed.</p>
<div class="scales3">
  <div class="panel"><h3 class="sub">Reach: how much of the economy it touches</h3>
  <ul class="levels">{"".join(reach)}</ul></div>
  <div class="panel"><h3 class="sub">Confidence: how strong the evidence is</h3>
  <ul class="levels">{"".join(conf)}</ul></div>
  <div class="panel"><h3 class="sub">Kind of item</h3><ul class="levels">{"".join(kinds)}</ul></div>
</div>"""


def _example(record: ChangeRecord | None, tips: _Tips) -> str:
    if record is None or record.assessment is None:
        return ""
    a = record.assessment
    rows = []
    for key, d in fw.DRIVERS.items():
        m = a.mark(key)
        reason = next((x.reason for x in a.marks if x.driver == key), "No material effect.")
        strip = "".join(
            f'<i class="{MARK_CLS[v] if v == m else ""}">{_signed(v) if v == m else ""}</i>' for v in MARK_ORDER
        )
        main = '<span class="tag">main driver</span>' if key == a.main_driver else ""
        rows.append(
            f'<tr class="{"" if m else "zero"}"><th scope="row"><span class="badge sm">{icon(key)}</span>'
            f"<span>{escape(d['short'])}</span>{main}</th>"
            f'<td><span class="strip" role="img" aria-label="Mark {_signed(m)}">{strip}</span></td>'
            f"<td>{escape(reason)}</td></tr>"
        )
    label = fw.RATING_LABELS[a.rating]
    reach, conf = fw.REACH[a.reach]["label"].lower(), fw.CONFIDENCE[a.confidence]["label"].lower()
    where = "" if f"({record.jurisdiction})" in record.title else f" ({escape(record.jurisdiction)})"
    title = f'<a href="index.html#{escape(record.id)}">{escape(record.title)}</a>{where}'
    total = f'<span class="mk {MARK_CLS[max(-2, min(2, a.total))]}">{_signed(a.total)}</span>'
    scale = "".join(f"<span>{_signed(v)}</span>" for v in MARK_ORDER)
    return f"""<section class="block" aria-labelledby="h-example">
  <div class="block-head"><h2 id="h-example">A worked example on the rubric</h2>
  <p>{title}. {escape(a.summary)}</p></div>
  <div class="panel tscroll"><table class="data ex">
  <thead><tr><th scope="col">Driver</th><th scope="col"><span class="strip-scale">{scale}</span></th>
  <th scope="col">Why</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
  <tfoot><tr><th scope="row">Overall</th><td>{total}</td>
  <td>{escape(label)}. Reach: {escape(reach)}; confidence: {escape(conf)}.</td></tr></tfoot>
  </table></div>
</section>"""


def _overlap(tips: _Tips) -> str:
    rows = []
    for i, o in enumerate(fw.OVERLAP_TABLE):
        # A heavier rule between rows that belong to different rules.
        cls = ' class="grp"' if i and o["group"] != fw.OVERLAP_TABLE[i - 1]["group"] else ""
        chips = "".join(_driver_chip(k, tips) for k in o["under"])
        note = f'<span class="small muted">{escape(o["note"])}</span>' if o["note"] else ""
        rows.append(f'<tr{cls}><td>{escape(o["case"])}</td><td><div class="chips">{chips}</div>{note}</td></tr>')
    return (
        '<div class="panel tscroll"><table class="data overlap"><thead><tr><th scope="col">When an item involves…</th>'
        f'<th scope="col">Mark it under</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


# The regime shown as a worked diagram, and the Productivity Commission's words on why fragmentation matters.
COMPLEXITY_EXAMPLE = "food-safety"
COMPLEXITY_QUOTE = (
    "Businesses would wait shorter periods of time for regulatory decisions. They would not need to provide the same "
    "information to multiple regulators. And they would no longer need to wade through the confusing and "
    "contradictory requirements of different regulators in the same space."
)
FUNCTION_SHORT = {
    "sets-rules": "Sets rules",
    "licenses": "Licenses",
    "approves": "Approves",
    "inspects": "Inspects",
    "collects": "Collects",
    "funds": "Funds",
}


def venn_regions(reg: Regime) -> dict[str, list[dict]]:
    """The regime's functions placed by the tiers that perform them, for ``vennSvg`` in charts.js."""
    out: dict[str, list[dict]] = {}
    for f, label in FUNCTION_SHORT.items():
        layers = [x for x in reg.layers if x.function == f]
        if not layers:
            continue
        tiers = [t for t in TIER_LABELS if any(x.tier == t for x in layers)]
        who = "\n".join(f"{TIER_LABELS[x.tier]}: {x.who}" for x in layers)
        out.setdefault("+".join(tiers), []).append({"label": label, "title": f"{label}\n{who}", "hot": len(tiers) > 1})
    return out


def _complexity(records: list[ChangeRecord], regimes: list[Regime]) -> str:
    if not regimes:
        return ""
    issues = [i for r in regimes for i in r.issues if i.status != "addressed"]
    counts = Counter(i.tag for i in issues)
    by_record = _regimes_by_record(regimes)
    items = Counter(
        t
        for r in records
        for t in {i.tag for g in by_record.get(r.id, []) for i in g.issues if i.status != "addressed"}
    )
    rows = "".join(
        f'<tr><td><a href="index.html#complexity={t}">{escape(label)}</a>'
        f'<span class="cx-help">{escape(ISSUE_HELP[t])}</span></td>'
        f'<td class="num">{counts[t]}</td><td class="num">{items[t]}</td></tr>'
        for t, label in ISSUE_LABELS.items()
    )
    profiles = industry_profiles(regimes)
    top = sorted(profiles, key=lambda p: (-p["sector_touchpoints"], -p["sector_regimes"], p["anzsic"]))[:8]
    top_rows = "".join(
        f'<tr><td><a href="index.html#class={p["anzsic"]}"><span class="mono">{p["anzsic"]}</span> '
        f'{escape(p["name"])}</a></td><td class="num">{p["sector_regimes"]}</td>'
        f'<td class="num">{p["sector_touchpoints"]}</td><td class="num">{p["sector_varying"]}</td></tr>'
        for p in top
    )
    ex = next((r for r in regimes if r.id == COMPLEXITY_EXAMPLE), regimes[0])
    venn = escape(
        json.dumps(
            {
                "regions": venn_regions(ex),
                "names": TIER_LABELS,
                "label": f"{ex.name}: which tiers of government do what",
            }
        ),
        quote=True,
    )
    sector = sum(r.scope == "sector" for r in regimes)
    linked = sum(1 for r in records if r.id in by_record)
    src = fw.SOURCES["pc2025"]
    return f"""
<section class="block" aria-labelledby="h-complexity">
  <div class="block-head"><h2 id="h-complexity">Regulatory complexity</h2>
  <p>A rule can be light on its own and still costly when a business must deal with several agencies or tiers of
  government for one activity, meet different rules in each state, or follow guidance that is vague or keeps
  changing. The framework counts these costs under <strong>regulatory burden</strong>, whose checklist already looks
  for &ldquo;the same thing regulated by several governments&rdquo; and &ldquo;complexity, and frequent changes to the
  rules&rdquo;. The menu now shows where they arise, industry by industry.</p></div>
  <div class="cx-grid">
    <figure class="panel cx-quote"><blockquote>{escape(COMPLEXITY_QUOTE)}</blockquote>
    <figcaption>What success would look like: <a href="{escape(src["url"])}" target="_blank"
    rel="noopener">{escape(src["label"])}</a>, p. 37.</figcaption></figure>
    <div class="panel"><h3 class="sub">How it is recorded</h3><ol class="cx-steps">
      <li><strong>Regimes.</strong> {len(regimes)} bodies of regulation a business deals with as one task
      ({len(regimes) - sector} that apply across industries, such as payroll tax; {sector} industry-specific, such as
      food safety). Each records which tier of government sets the rules, licenses, approves, inspects or collects,
      and whether the rules are national, a model law adopted with variations, or different in each state.</li>
      <li><strong>Industries.</strong> Every detailed industry in the ABS classification (all
      {len(profiles)} ANZSIC classes) is mapped to the regimes it faces, giving the number of government parties it
      deals with, where tiers overlap and where rules differ by state.</li>
      <li><strong>Evidence.</strong> Where a review or regulator reports a problem, the regime is tagged, with the
      source quoted word for word: {len(issues)} issues so far. {linked} of the {len(records)} register items belong to
      a regime and carry its tags.</li></ol></div>
  </div>
  <div class="cx-grid">
    <div class="panel"><h3 class="sub">Reading the diagram: {escape(ex.name.lower())}</h3>
      <div class="venn-wrap" data-venn="{venn}"></div>
      <p class="small muted">Each circle is a tier of government; each label is something it does. A label in an overlap
      is done by more than one tier (shown in bold): here councils and state agencies both license and inspect food
      businesses. Every item in the <a href="index.html">menu</a> shows this diagram for its regimes, and each industry
      shows one for all of its regimes together.</p></div>
    <div class="panel tscroll"><h3 class="sub">The tags</h3>
      <table class="data cx-tags"><thead><tr><th scope="col">Tag and meaning</th><th scope="col">Issues</th>
      <th scope="col">Menu items</th></tr></thead><tbody>{rows}</tbody></table>
      <p class="small muted">Click a tag to see the items that carry it. No tag means no evidence was found in the
      sources searched, not that there is no problem; counts also reflect where reviews have looked.</p></div>
  </div>
  <div class="cx-grid">
    <div class="panel"><h3 class="sub">How it relates to the marks</h3>
      <p class="small">The tags do not change any mark by themselves: each effect is marked once (see above), and
      complexity is marked under regulatory burden. An item that adds a second approval for the same activity, or
      that departs from a national model, is marked down on burden; one that removes a duplicate approval, joins a
      national scheme or recognises other states' licences is marked up. The tags show the assessor, and the reader,
      where the evidence is. Marks under framework version {escape(fw.VERSION)} are unchanged.</p></div>
    <div class="panel tscroll"><h3 class="sub">Industries dealing with the most government parties</h3>
      <table class="data"><thead><tr><th scope="col">Industry</th><th scope="col">Regimes</th>
      <th scope="col">Parties</th><th scope="col">Differ by state</th></tr></thead><tbody>{top_rows}</tbody></table>
      <p class="small muted">Industry-specific regimes only; every industry also deals with about
      {len(regimes) - sector} that apply across industries. The <a href="index.html#industries">Industries view</a>
      lists all {len(profiles)}. Method and limits: <code>docs/industry_regulation.md</code>.</p></div>
  </div>
</section>"""


def _limits() -> str:
    cards = "".join(
        f'<div class="limit"><span class="badge">{icon(ic)}</span><div><strong>{escape(t)}</strong>'
        f"<p>{escape(c)}</p></div></div>"
        for ic, t, c in zip(LIMIT_ICONS, fw.CAVEAT_TITLES, fw.CAVEATS, strict=True)
    )
    return f'<div class="limits">{cards}</div>'


def body(records: list[ChangeRecord], generated: dt.date | None = None, regimes: list[Regime] | None = None) -> str:
    """``regimes`` defaults to the committed regulatory regimes (``load_regimes``)."""
    regimes = load_regimes().regimes if regimes is None else regimes
    tips = _Tips()
    flow = _flow(tips)
    concepts = _concepts(tips)
    signs = _signs(tips)
    rubric = _rubric(records, tips)
    marking = _marking(records, tips)
    example = _example(next((r for r in records if r.id == EXAMPLE_ID), None), tips)
    overlap = _overlap(tips)
    sources = "".join(
        f'<li><a href="{escape(s["url"])}" target="_blank" rel="noopener">{escape(s["label"])}</a></li>'
        for s in fw.SOURCES.values()
    )
    idea_sources = sorted(
        set(fw.LOGIC_SOURCES) | {k for s in fw.SIGNS for k in s["sources"]}, key=list(fw.SOURCES).index
    )
    n_assessed = sum(1 for r in records if r.assessment)
    built = (generated or dt.date.today()).isoformat()
    return f"""
  <div class="meta-line"><span>Version {escape(fw.VERSION)}, adopted {escape(fw.ADOPTED)}</span>
  <span>{n_assessed} items marked</span><span>Generated {escape(built)}</span></div>
  <p class="hint">{icon("info")} Hover over, or tap, any box, row or cell for more detail.</p>
</header>

<section class="block" aria-labelledby="h-fit">
  <div class="block-head"><h2 id="h-fit">The idea in one picture</h2>
  <p>Eight drivers, in three groups. Competition and dynamism push firms to invest, to use people well and to work
  efficiently, and that is what lifts productivity.</p></div>
  {flow}
</section>

<section class="block" aria-labelledby="h-ideas">
  <div class="block-head"><h2 id="h-ideas">Key ideas in plain words</h2></div>
  <div class="ideas">
    {concepts}
    <div class="stack">
      <h3 class="sub">Warning signs in Australia</h3>
      {signs}
      <p class="source">Sources: {_cite_short(idea_sources)}. Full references are at the foot of the page.</p>
    </div>
  </div>
</section>

<section class="block" aria-labelledby="h-rubric">
  <div class="block-head"><h2 id="h-rubric">The rubric</h2>
  <p>Every item gets a mark from −2 to +2 on each driver. Each cell says what that mark means, and how many items in
  the register have it.</p></div>
  {rubric}
  <details class="more-drivers"><summary>Evidence, checklists and the full marking guide for each driver</summary>
  <div class="ddets">{_driver_details(records)}</div></details>
</section>

<section class="block" aria-labelledby="h-how">
  <div class="block-head"><h2 id="h-how">How an item is marked</h2></div>
  {marking}
</section>

{example}

<section class="block" aria-labelledby="h-overlap">
  <div class="block-head"><h2 id="h-overlap">Avoiding double counting</h2>
  <p>Each effect is marked once, under the driver it acts through.</p></div>
  {overlap}
</section>
{_complexity(records, regimes)}

<section class="block" aria-labelledby="h-limits">
  <div class="block-head"><h2 id="h-limits">Limits</h2></div>
  {_limits()}
</section>

<footer class="foot">
  <h2>Sources</h2>
  <ul>{sources}</ul>
  <p>The same framework, as a methods note, is in <code>docs/productivity_framework.md</code> (written by
  <code>alicia framework</code>). The <a href="index.html">legislation menu</a> shows every item's marks; the
  econometric evaluations the site used to show are in the <a href="archive.html">econometric archive</a>.
  Unofficial research, not an Australian Government product.</p>
</footer>
{tips.html()}"""


def render(
    records: list[ChangeRecord],
    nav: str,
    standalone: bool = True,
    generated: dt.date | None = None,
    regimes: list[Regime] | None = None,
) -> str:
    from .growth import _asset

    template = resources.files("alicia.menu").joinpath("templates/framework.html").read_text("utf-8")
    page = (
        template.replace("/*__SITE_CSS__*/", _asset("site.css"))
        .replace("/*__CHARTS_JS__*/", _asset("charts.js"))
        .replace("<!--__NAV__-->", nav)
        .replace("<!--__BODY__-->", body(records, generated, regimes))
    )
    if standalone:
        page = (
            '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
        )
    return page
