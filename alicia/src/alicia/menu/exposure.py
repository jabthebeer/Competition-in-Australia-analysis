"""Exposure: how many businesses a rule reaches, and the impact class that follows from it.

Owner decision, 14 November 2026 (DECISIONS E-161; plan in ``docs/plan_policy_tool.md``). A rule's importance is
read from two things: how large its effect is on each business it binds, and how many businesses it binds. The
second is measured here from the ABS business counts (CABEE, by detailed industry and state, latest June), for the
industries and states the rule reaches. The first is, for now, the framework marks already drafted: a rule whose
marks add to −2 or lower counts as a large effect. Framework version 2 replaces that stopgap with a severity score
from coded attributes.

Three classes (the owner's):

- **Major, wide:** it reaches a large share of the businesses in its jurisdiction, whatever the size of its effect
  on each. A rule that binds only the businesses doing some activity (its reach carries a condition or lists
  activities) is never wide, however many industries it could reach: the count is then an upper bound;
- **Major, narrow:** a large effect on a small set of industries;
- **Minor:** a small effect on a small set of industries.

A state's rule is judged within its state, and a council's within its state too (business counts by council are not
in the panel), so a council rule's figures are an upper bound and it is never classed as wide.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .. import anzsic
from ..pipeline import schema, store
from ..register.requirements import Requirement, reach_classes
from ..register.schema import ChangeRecord

# A rule is wide when it reaches at least this share of the businesses in its jurisdiction.
WIDE_SHARE = 25.0
# A rule has a large effect when its framework marks add to this or lower (the stopgap for version 2's severity).
DEEP_TOTAL = -2

CLASSES = {
    "major-wide": "Major, wide",
    "major-narrow": "Major, narrow",
    "minor": "Minor",
}
CLASS_HELP = {
    "major-wide": f"Reaches at least {WIDE_SHARE:.0f}% of the businesses in its jurisdiction.",
    "major-narrow": "A large effect on a small set of industries.",
    "minor": "A small effect on a small set of industries.",
}
NOTE = (
    "Businesses are counted from the ABS Counts of Australian Businesses, by detailed industry and state, for the "
    "industries and states each rule reaches. For a register item, these are the industries it names as directly "
    "affected. A rule that binds only some businesses in an industry (those above a threshold, or doing one "
    "activity) is counted as reaching the whole industry, so its figure is an upper bound, shown as 'up to'; a rule "
    "that follows an activity is never classed as wide. Where a rule binds some whole industries and, elsewhere, "
    "only businesses doing an activity, the whole industries are counted. "
    f"A rule is wide when it reaches at least {WIDE_SHARE:.0f}% of the businesses in its jurisdiction; a state's "
    "rule is judged within its state. The size of a rule's effect is, for now, read from its framework marks: marks "
    f"that add to {DEEP_TOTAL} or lower count as a large effect. The marks are drafts and are being replaced by a "
    "score from coded attributes."
)


@dataclass(frozen=True)
class Counts:
    """Businesses operating at the end of the latest financial year, by class and state."""

    all: dict[tuple[str, str], float]
    employing: dict[tuple[str, str], float]
    year: int  # the June the counts are for

    @property
    def classes(self) -> tuple[str, ...]:
        return tuple(sorted({c for c, _ in self.all}))

    def total(self, states, employing: bool = False) -> float:
        src = self.employing if employing else self.all
        states = set(states)
        return sum(v for (_, s), v in src.items() if s in states)


def counts_from(df) -> Counts | None:
    """Counts from the CABEE class-by-state panel (``data/processed/abs_cabee/class_state_fy.parquet``)."""
    df = df[(df["measure"] == "businesses_end") & df["geo_code"].isin(schema.STATES)]
    df = df[df["industry_code"].str.fullmatch(r"\d{4}")]
    if df.empty:
        return None
    last = df["period"].max()
    df = df[df["period"] == last]
    bands = df[df["breakdown"] != ""]  # the size bands; the blank breakdown is their total
    emp = bands[bands["breakdown"] != "non-employing"]

    def table(x) -> dict:
        return {k: float(v) for k, v in x.groupby(["industry_code", "geo_code"])["value"].sum().items()}

    employing = table(emp)
    everyone = table(bands)
    if not everyone:
        return None
    return Counts(everyone, employing, int(last.year) + 1)


@lru_cache(maxsize=1)
def load_counts() -> Counts | None:
    """None when the business counts have not been built (the page then shows no exposure)."""
    import pandas as pd

    path = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
    if not path.exists():
        return None
    cols = ["measure", "industry_code", "geo_code", "breakdown", "period", "value"]
    return counts_from(pd.read_parquet(path, columns=cols))


@lru_cache(maxsize=1)
def _all_classes() -> tuple[str, ...]:
    return tuple(sorted(c for c in anzsic._codes() if len(c) == 4))


def _under(cls: str, code: str) -> bool:
    return anzsic.division(cls) == code if len(code) == 1 else cls.startswith(code)


def _firm(q: Requirement) -> list:
    """The parts of a requirement's reach that bind every business in their industries: those with no condition and
    no list of activities. Empty when every part follows an activity."""
    return [r for r in q.reach if not (r.condition or r.activities)]


def beyond(q: Requirement) -> bool:
    """Whether the requirement also binds some businesses outside the industries counted: it has parts that bind
    whole industries and parts that follow an activity."""
    return bool(_firm(q)) and len(_firm(q)) < len(q.reach)


def requirement_pairs(q: Requirement) -> set[tuple[str, str]]:
    """Every (class, state) a requirement reaches. A Commonwealth requirement reaches every state unless its reach
    names some; a state's or a council's reaches its own state. Where some parts of its reach bind whole industries
    and others follow an activity (an award that covers one industry, and anyone else who employs that occupation),
    only the whole industries are counted; where every part follows an activity, all are counted, as an upper
    bound (``conditional``)."""
    home = schema.STATES if q.jurisdiction == "CTH" else (q.jurisdiction,)
    pairs = set()
    for r in _firm(q) or q.reach:
        states = [s for s in (r.in_states or home) if s in schema.STATES]
        pairs.update((c, s) for c in reach_classes(r) for s in states)
    return pairs


def record_pairs(r: ChangeRecord) -> set[tuple[str, str]]:
    """Every (class, state) a register item reaches: the classes under the industries it names as directly affected
    (all it names, if none is marked direct; every class, if it names none), in every state for a Commonwealth item
    and in its own state otherwise."""
    codes = [i.anzsic for i in r.industries if i.exposure == "direct"] or [i.anzsic for i in r.industries]
    classes = [c for c in _all_classes() if any(_under(c, code) for code in codes)] if codes else _all_classes()
    states = schema.STATES if r.jurisdiction == "CTH" else (r.jurisdiction,)
    return {(c, s) for c in classes for s in states if s in schema.STATES}


def conditional(q: Requirement) -> bool:
    """Whether a requirement binds only the businesses doing some activity: every part of its reach carries a
    condition or lists activities."""
    return bool(q.reach) and not _firm(q)


def measure(
    pairs: set[tuple[str, str]], jurisdiction: str, counts: Counts | None, council: bool = False, partial: bool = False
) -> dict:
    """The exposure figures for a rule: the industries it reaches, the businesses in them, and their share of the
    businesses in the rule's jurisdiction and in Australia. ``None`` figures when the counts are not built."""
    classes = {c for c, _ in pairs}
    out = {
        "classes": len(classes),
        "allIndustries": len(classes) >= len(_all_classes()),
        "states": sorted({s for _, s in pairs}, key=schema.STATES.index),
        "council": council,
        "partial": partial or council,
        "businesses": None,
        "employing": None,
        "share": None,
        "shareAus": None,
        "year": counts.year if counts else None,
    }
    if not counts or not pairs:
        return out
    n = sum(counts.all.get(p, 0.0) for p in pairs)
    emp = sum(counts.employing.get(p, 0.0) for p in pairs)
    home = schema.STATES if jurisdiction == "CTH" else (jurisdiction,)
    base, aus = counts.total(home), counts.total(schema.STATES)
    out.update(
        businesses=round(n),
        employing=round(emp),
        share=round(100 * n / base, 1) if base else None,
        shareAus=round(100 * n / aus, 1) if aus else None,
    )
    return out


def impact_class(total: int | None, exposure: dict) -> str | None:
    """The impact class of a standing rule with a negative overall mark; ``None`` for anything else, or when the
    businesses it reaches can't be counted."""
    if total is None or total >= 0 or exposure.get("share") is None:
        return None
    if exposure["share"] >= WIDE_SHARE and not exposure.get("partial"):
        return "major-wide"
    return "major-narrow" if total <= DEEP_TOTAL else "minor"


def is_standing(kind: str, total: int | None, ended: bool, in_force: bool) -> bool:
    """Whether an item is a rule that applies today. Requirements, existing settings and non-legislative barriers
    are. A reform is a change, not a rule, with one exception kept until version 2 separates the two: a reform now
    in force whose marks are negative has added a restriction that stands."""
    if ended:
        return False
    if kind in ("requirement", "setting", "barrier"):
        return True
    return kind == "reform" and in_force and total is not None and total < 0
