"""The website's Framework page (``framework.html``): the productivity impact framework in brief, rendered to
static HTML from ``register/framework.py``, with the register's items counted by main driver and one real
assessment as a worked example."""

from __future__ import annotations

import datetime as dt
from html import escape
from importlib import resources

from ..register import framework as fw
from ..register.schema import ChangeRecord

# The worked example: a reform most readers know, with marks on several drivers.
EXAMPLE_ID = "nsw-rideshare-2015"
MARK_CLS = {2: "m2", 1: "m1", 0: "m0", -1: "mn1", -2: "mn2"}


def _signed(n: int) -> str:
    return f"+{n}" if n > 0 else (f"−{abs(n)}" if n < 0 else "0")


def _cite(keys) -> str:
    return "; ".join(
        f'<a href="{escape(fw.SOURCES[k]["url"])}" target="_blank" rel="noopener">{escape(fw.SOURCES[k]["label"])}</a>'
        for k in keys
    )


def _driver_card(key: str, d: dict, counts: dict) -> str:
    n = counts.get(key, {})
    neg, pos = n.get("neg", 0), n.get("pos", 0)
    marks = "".join(
        f'<tr><td><span class="mk {MARK_CLS[m]}">{_signed(m)}</span></td><td>{escape(t)}</td></tr>'
        for m, t in d["marks"].items()
    )
    look = "".join(f"<li>{escape(x)}</li>" for x in d["look_for"])
    total = neg + pos + n.get("zero", 0)
    in_register = (
        f'<a href="index.html#driver={escape(key)}">{total} items in the register</a> have this as their main driver '
        f"({neg} negative overall, {pos} positive)."
    )
    return f"""<article class="drv-card" id="d-{escape(key)}">
  <h3>{escape(d["label"])}</h3>
  <p class="q">{escape(d["question"])}</p>
  <p>{escape(d["why"])} <span class="cite">{_cite(d["why_sources"])}</span></p>
  <div class="two">
    <div><h4>Look for</h4><ul>{look}</ul></div>
    <div><h4>Marks</h4><table class="mk-table"><tbody>{marks}</tbody></table></div>
  </div>
  <p class="small muted">{in_register} Policy costing channels: {", ".join(d["channels"])}.</p>
</article>"""


def _example(record: ChangeRecord | None) -> str:
    if record is None or record.assessment is None:
        return ""
    a = record.assessment
    rows = []
    for key, d in fw.DRIVERS.items():
        m = a.mark(key)
        reason = next((x.reason for x in a.marks if x.driver == key), "No material effect.")
        main = " · main driver" if key == a.main_driver else ""
        rows.append(
            f'<tr class="{"" if m else "zero"}"><th scope="row">{escape(d["label"])}{main}</th>'
            f'<td><span class="mk {MARK_CLS[m]}">{_signed(m)}</span></td><td>{escape(reason)}</td></tr>'
        )
    label = fw.RATING_LABELS[a.rating]
    reach, conf = fw.REACH[a.reach]["label"].lower(), fw.CONFIDENCE[a.confidence]["label"].lower()
    title = f'<a href="index.html#{escape(record.id)}">{escape(record.title)}</a> ({escape(record.jurisdiction)})'
    total = f'<span class="mk {MARK_CLS[max(-2, min(2, a.total))]}">{_signed(a.total)}</span>'
    return f"""<section class="block" aria-labelledby="h-example">
  <div class="block-head"><h2 id="h-example">A worked example</h2>
  <p>{title}. {escape(a.summary)}</p></div>
  <div class="panel tscroll"><table class="data ex"><thead><tr><th>Driver</th><th>Mark</th><th>Why</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
  <tfoot><tr><th scope="row">Overall</th><td>{total}</td>
  <td>{escape(label)}. Reach: {escape(reach)}; confidence: {escape(conf)}.</td></tr></tfoot>
  </table></div>
</section>"""


def body(records: list[ChangeRecord], generated: dt.date | None = None) -> str:
    counts: dict[str, dict] = {}
    ratings = {k: 0 for _, k, _ in fw.RATINGS}
    for r in records:
        a = r.assessment
        if a is None:
            continue
        c = counts.setdefault(a.main_driver, {"neg": 0, "pos": 0, "zero": 0})
        c["neg" if a.total < 0 else "pos" if a.total > 0 else "zero"] += 1
        ratings[a.rating] += 1
    pillars = []
    for pk, p in fw.PILLARS.items():
        links = "".join(
            f'<li><a href="#d-{escape(k)}">{escape(d["label"])}</a></li>'
            for k, d in fw.DRIVERS.items()
            if d["pillar"] == pk
        )
        pillars.append(
            f'<div class="pillar"><h3>{escape(p["label"])}</h3><p>{escape(p["question"])}</p><ul>{links}</ul></div>'
        )
    cards = []
    for pk, p in fw.PILLARS.items():
        cards.append(f'<h3 class="pillar-h">{escape(p["label"])}</h3>')
        cards += [_driver_card(k, d, counts) for k, d in fw.DRIVERS.items() if d["pillar"] == pk]
    bands = "".join(
        f'<tr><td><span class="mk {cls}">{escape(rng)}</span></td><td>{escape(fw.RATING_LABELS[k])}</td>'
        f'<td class="num">{ratings[k]}</td></tr>'
        for rng, k, cls in (
            ("+3 or more", "strongly-positive", "m2"),
            ("+1 to +2", "positive", "m1"),
            ("0", "neutral", "m0"),
            ("−1 to −2", "negative", "mn1"),
            ("−3 or less", "strongly-negative", "mn2"),
        )
    )

    def table(d: dict) -> str:
        return "".join(
            f"<tr><th scope='row'>{escape(v['label'])}</th><td>{escape(v['help'])}</td></tr>" for v in d.values()
        )

    example = _example(next((r for r in records if r.id == EXAMPLE_ID), None))
    sources = "".join(
        f'<li><a href="{escape(s["url"])}" target="_blank" rel="noopener">{escape(s["label"])}</a></li>'
        for s in fw.SOURCES.values()
    )
    n_assessed = sum(1 for r in records if r.assessment)
    built = (generated or dt.date.today()).isoformat()
    return f"""
  <div class="meta-line"><span>Version {escape(fw.VERSION)}, adopted {escape(fw.ADOPTED)}</span>
  <span>{n_assessed} items marked</span><span>Generated {escape(built)}</span></div>
</header>

<section class="block" aria-labelledby="h-logic">
  <div class="block-head"><h2 id="h-logic">How productivity grows</h2></div>
  <div class="panel stack">
    <ul class="logic">{"".join(f"<li>{escape(x)}</li>" for x in fw.LOGIC)}</ul>
    <p class="source">Sources: {_cite(fw.LOGIC_SOURCES)}.</p>
  </div>
  <div class="pillars">{"".join(pillars)}</div>
</section>

<section class="block" aria-labelledby="h-drivers">
  <div class="block-head"><h2 id="h-drivers">The eight drivers</h2>
  <p>Each driver asks one question. An item gets a mark from −2 (major harm) to +2 (major gain) on each, or 0
  where the effect is small or speculative.</p></div>
  <div class="drv-grid">{"".join(cards)}</div>
</section>

<section class="block" aria-labelledby="h-how">
  <div class="block-head"><h2 id="h-how">How an item is marked</h2></div>
  <div class="split">
    <div class="panel stack">
      <ol class="steps">{"".join(f"<li>{escape(s)}</li>" for s in fw.STEPS)}</ol>
      <p><strong>What a mark compares against.</strong> {escape(fw.COUNTERFACTUAL)}</p>
    </div>
    <div class="panel stack">
      <h3>Overall mark</h3>
      <table class="data"><thead><tr><th>Sum of marks</th><th>Band</th><th>Items</th></tr></thead>
      <tbody>{bands}</tbody></table>
      <h3>Reach</h3><table class="data kvt"><tbody>{table(fw.REACH)}</tbody></table>
      <h3>Confidence</h3><table class="data kvt"><tbody>{table(fw.CONFIDENCE)}</tbody></table>
      <h3>Kinds of item</h3><table class="data kvt"><tbody>{table(fw.KINDS)}</tbody></table>
    </div>
  </div>
</section>

{example}

<section class="block" aria-labelledby="h-overlap">
  <div class="block-head"><h2 id="h-overlap">Avoiding double counting</h2></div>
  <div class="panel"><ul class="plain">{"".join(f"<li>{escape(x)}</li>" for x in fw.OVERLAP_RULES)}</ul></div>
</section>

<section class="block" aria-labelledby="h-limits">
  <div class="block-head"><h2 id="h-limits">Limits</h2></div>
  <div class="panel"><ul class="plain">{"".join(f"<li>{escape(x)}</li>" for x in fw.CAVEATS)}</ul></div>
</section>

<footer class="foot">
  <h2>Sources</h2>
  <ul>{sources}</ul>
  <p>The same framework, as a methods note, is in <code>docs/productivity_framework.md</code> (written by
  <code>alicia framework</code>). The <a href="index.html">legislation menu</a> shows every item's marks; the
  econometric evaluations the site used to show are in the <a href="archive.html">econometric archive</a>.
  Unofficial research, not an Australian Government product.</p>
</footer>"""


def render(records: list[ChangeRecord], nav: str, standalone: bool = True, generated: dt.date | None = None) -> str:
    from .growth import _asset

    template = resources.files("alicia.menu").joinpath("templates/framework.html").read_text("utf-8")
    page = (
        template.replace("/*__SITE_CSS__*/", _asset("site.css"))
        .replace("<!--__NAV__-->", nav)
        .replace("<!--__BODY__-->", body(records, generated))
    )
    if standalone:
        page = (
            '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
        )
    return page
