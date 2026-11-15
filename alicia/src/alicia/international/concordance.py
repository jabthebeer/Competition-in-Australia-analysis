"""ANZSIC 2006 to ISIC Rev. 4, and the common industry groups used to compare Australia with other economies.

The ABS publishes the correspondence both ways as HTML tables, one per division: each ANZSIC class with the
ISIC classes it matches, and each ISIC class with the ANZSIC classes it matches. "p" after a code marks a
partial match (only part of that class corresponds). Both pages are downloaded and parsed, and their pairs
are checked against each other and against the ANZSIC codelist.

The groups themselves (``alicia/data/industry_groups.json``) are defined by ISIC divisions, the
classification the international sources use. Each ANZSIC class goes to the group holding most of its ISIC
matches: each match counts equally, since the ABS gives no weights. Data published only by ANZSIC division
use the division assignment in the groups file, and the fit of each group's divisions is measured with the
number of employing businesses in each class (ABS business register), so a mismatch that affects few
businesses counts for little.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from functools import cache
from html.parser import HTMLParser
from importlib import resources

from .. import anzsic
from ..pipeline import store
from . import OUT, prose

SOURCE = "abs_isic"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
BASE = (
    "https://www.abs.gov.au/statistics/classifications/"
    "australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0/correspondences"
)
PAGES = {
    "anzsic_to_isic": f"{BASE}/anzsic-2006-isic-rev-4",
    "isic_to_anzsic": f"{BASE}/isic-rev-4-anzsic-2006",
}
EMPLOYING = ("1-19 employees", "20-199 employees", "200+ employees")
CLASS = re.compile(r"\d{4}")


@cache
def groups() -> dict:
    """The common industry groups (alicia/data/industry_groups.json)."""
    return json.loads(resources.files("alicia.data").joinpath("industry_groups.json").read_text("utf-8"))


def isic_group(code: str) -> str | None:
    """The group an ISIC Rev. 4 class or division belongs to (None for division 99, which no group holds)."""
    div = code[:2]
    for g in groups()["groups"]:
        if div in g["isic"]:
            return g["id"]
    return None


class _Tables(HTMLParser):
    """Every table row on a page, as lists of cell text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth += 1
        elif tag == "tr" and self._depth:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).replace("\xa0", " ").split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
        elif tag == "table" and self._depth:
            self._depth -= 1

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse(page: str) -> list[tuple[str, str, bool]]:
    """(class, matching class, partial) for every pair on a correspondence page.

    A class row has five cells: blank, the class code, its title, the first match and that match's title.
    Each further match of the same class is a row with the first three cells blank. Division, subdivision and
    group headings (a code of one to three characters in the first cell) end the class above them."""
    p = _Tables()
    p.feed(page)
    pairs, current = [], None
    for cells in p.rows:
        if len(cells) == 5 and CLASS.fullmatch(cells[1]):
            current, match = cells[1], cells[3]
        elif len(cells) == 5 and not any(cells[:3]) and cells[3] and current:
            match = cells[3]
        else:
            if cells and cells[0]:
                current = None
            continue
        code = match.rstrip("p")
        if not CLASS.fullmatch(code):
            raise ValueError(f"{current}: unexpected match code {match!r}")
        pairs.append((current, code, match.endswith("p")))
    return pairs


def check(forward: list[tuple[str, str, bool]], reverse: list[tuple[str, str, bool]]) -> dict:
    """Compare the two directions of the correspondence and the ANZSIC side with the codelist."""
    f = {(a, i) for a, i, _ in forward}
    r = {(a, i) for i, a, _ in reverse}
    classes = {c for c in anzsic._codes() if len(c) == 4}
    seen = {a for a, _ in f}
    return {
        "pairs_anzsic_to_isic": len(f),
        "pairs_isic_to_anzsic": len(r),
        "only_in_anzsic_to_isic": sorted(map(list, f - r)),
        "only_in_isic_to_anzsic": sorted(map(list, r - f)),
        "anzsic_classes": len(seen),
        "isic_classes": len({i for _, i in f | r}),
        "anzsic_classes_not_in_codelist": sorted(seen - classes),
        "codelist_classes_without_a_match": sorted(classes - seen),
    }


def assign(pairs: list[tuple[str, str, bool]]) -> dict[str, dict]:
    """Each ANZSIC class's group: the group holding most of its ISIC matches, each match counted equally.
    A tie goes to the group of the class's ANZSIC division (from the groups file), then alphabetically. A class
    that matches only ISIC division 99 stays with its ANZSIC division's group, with share 0."""
    by_class: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for a, i, partial in pairs:
        by_class[a].append((i, partial))
    div_group = {d: g["id"] for g in groups()["groups"] for d in g["anzsic_divisions"]}
    out = {}
    for a, matches in sorted(by_class.items()):
        votes = Counter(isic_group(i) for i, _ in matches)
        votes.pop(None, None)
        home = div_group.get(anzsic.division(a) or "")
        if not votes:  # only ISIC division 99 (extraterritorial organisations): keep the ANZSIC division's group
            if home is None:
                raise ValueError(f"{a}: no ISIC match falls in a group, and its division has none")
            out[a] = {"group": home, "share": 0.0, "isic": [i + ("p" if p else "") for i, p in matches]}
            out[a]["note"] = "matches only ISIC division 99, which no group holds; kept with its ANZSIC division"
            continue
        top = max(votes.values())
        tied = sorted(g for g, v in votes.items() if v == top)
        group = home if home in tied else tied[0]
        out[a] = {
            "group": group,
            "share": round(votes[group] / len(matches), 4),
            "isic": [i + ("p" if partial else "") for i, partial in matches],
        }
        if len(votes) > 1:
            out[a]["other_groups"] = sorted(g for g in votes if g != group)
    return out


def employing_businesses() -> dict[str, float]:
    """Employing businesses in each ANZSIC class at the end of the latest financial year, all states (ABS
    business register). Empty if the processed panel is not built."""
    try:
        df = store.read_panel("abs_cabee", "class_state_fy")
    except FileNotFoundError:
        return {}
    df = df[(df["measure"] == "businesses_end") & df["breakdown"].isin(EMPLOYING) & (df["industry_level"] == "class")]
    if df.empty:
        return {}
    df = df[df["period"] == df["period"].max()]
    return df.groupby("industry_code")["value"].sum().to_dict()


def division_fit(assigned: dict[str, dict], weights: dict[str, float]) -> dict[str, dict]:
    """How well each group's ANZSIC divisions match the group defined by ISIC.

    ``in_group``: of the businesses in the group's divisions, the share in classes assigned to the group.
    ``covered``: of the businesses in classes assigned to the group, the share in the group's divisions.
    ``classes_elsewhere`` and ``classes_from_elsewhere`` list the classes behind each gap, largest first.
    Both are 1 for an exact match. Weighted by employing businesses where given, else each class counts once."""
    div_group = {d: g["id"] for g in groups()["groups"] for d in g["anzsic_divisions"]}
    tot_div, tot_grp, both = Counter(), Counter(), Counter()
    leaks: dict[str, Counter] = defaultdict(Counter)
    arrivals: dict[str, Counter] = defaultdict(Counter)
    for a, info in assigned.items():
        w = weights.get(a, 0.0) if weights else 1.0
        by_div = div_group.get(anzsic.division(a) or "")
        tot_div[by_div] += w
        tot_grp[info["group"]] += w
        if by_div == info["group"]:
            both[by_div] += w
        else:
            leaks[by_div][a] += w
            arrivals[info["group"]][a] += w
    out = {}
    for g in groups()["groups"]:
        gid = g["id"]
        out[gid] = {
            "in_group": round(both[gid] / tot_div[gid], 4) if tot_div[gid] else None,
            "covered": round(both[gid] / tot_grp[gid], 4) if tot_grp[gid] else None,
            "classes_elsewhere": [
                {"anzsic": a, "name": anzsic.name(a), "group": assigned[a]["group"], "weight": w}
                for a, w in leaks[gid].most_common()
            ],
            "classes_from_elsewhere": [
                {"anzsic": a, "name": anzsic.name(a), "division": anzsic.division(a), "weight": w}
                for a, w in arrivals[gid].most_common()
            ],
        }
    return out


FLAG = 0.05  # a division is flagged when at least 5% of the businesses on either side are mismatched


def _sentence(name: str) -> str:
    """An ABS title in sentence case ("Computer System Design" -> "Computer system design")."""
    return name[:1] + name[1:].lower()


def by_division(assigned: dict[str, dict], weights: dict[str, float]) -> dict[str, dict]:
    """For each ANZSIC division, how far it differs from its group as other countries define it (ISIC).

    ``out_share``: of the division's businesses, the share in classes that ISIC puts in another group.
    ``in_share``: of the businesses in the division's group (classes assigned to it), the share in classes that
    ANZSIC puts in other divisions. A division is flagged when either is at least ``FLAG``; the note says what
    differs in plain language, for the website's hover text. Classes split between groups count wholly in their
    main group, as for data published by class."""
    div_group = {d: g["id"] for g in groups()["groups"] for d in g["anzsic_divisions"]}
    label = {g["id"]: g["label"] for g in groups()["groups"]}
    tot, grp_tot = Counter(), Counter()
    out_c: dict[str, Counter] = defaultdict(Counter)
    in_c: dict[str, Counter] = defaultdict(Counter)
    for a, info in assigned.items():
        d = anzsic.division(a) or ""
        w = weights.get(a, 0.0) if weights else 1.0
        tot[d] += w
        grp_tot[info["group"]] += w
        if info["group"] != div_group.get(d):
            out_c[d][a] += w
            in_c[info["group"]][a] += w
    res = {}
    for d in sorted(tot):
        g = div_group[d]
        o = sum(out_c[d].values()) / tot[d] if tot[d] else 0.0
        i = sum(in_c[g].values()) / grp_tot[g] if grp_tot[g] else 0.0
        info = {
            "group": g,
            "merged_with": [
                x for grp in groups()["groups"] if grp["id"] == g for x in grp["anzsic_divisions"] if x != d
            ],
            "out_share": round(o, 4),
            "out": [
                {"anzsic": a, "name": anzsic.name(a), "group": assigned[a]["group"], "weight": w}
                for a, w in out_c[d].most_common(3)
            ],
            "in_share": round(i, 4),
            "in": [
                {"anzsic": a, "name": anzsic.name(a), "division": anzsic.division(a), "weight": w}
                for a, w in in_c[g].most_common(3)
                if anzsic.division(a) != d
            ],
            "flag": o >= FLAG or i >= FLAG,
        }
        parts = []
        if o >= FLAG:
            top = info["out"][0]
            parts.append(
                f"About {_share(o)} of its employing businesses do work that other countries count in another "
                f"industry, mainly ‘{_sentence(top['name']).lower()}’ (counted in {label[top['group']].lower()})."
            )
        if i >= FLAG and info["in"]:
            top = info["in"][0]
            here = _sentence(anzsic.name(top["division"]) or "").lower()
            parts.append(
                "Other countries' version also takes in work that Australia counts elsewhere, mainly "
                f"‘{_sentence(top['name']).lower()}’ (here in {here}). That work is about {_share(i)} of the "
                "industry's employing businesses as other countries define it."
            )
        if parts and info["merged_with"]:
            others = " and ".join(_sentence(anzsic.name(x) or x).lower() for x in info["merged_with"])
            parts.append(f"They also combine it with {others}.")
        if parts:
            parts.append("Comparisons with other countries are approximate.")
        info["note"] = " ".join(parts)
        res[d] = info
    return res


NOTE_TITLE = "Classified differently in other countries"


def division_notes() -> dict[str, str]:
    """The hover note for each flagged ANZSIC division, from the built concordance (empty if not built)."""
    path = OUT / "anzsic_isic4.json"
    if not path.exists():
        return {}
    divs = json.loads(path.read_text("utf-8")).get("divisions", {})
    return {d: v["note"] for d, v in divs.items() if v.get("flag") and v.get("note")}


def _manifest() -> list[dict]:
    path = store.MANIFESTS / f"{SOURCE}.json"
    return json.loads(path.read_text("utf-8"))["files"] if path.exists() else []


def build(refresh: bool = False) -> dict:
    """Download both correspondence pages, check them, assign classes to groups and write
    data/processed/international/anzsic_isic4.json."""
    pages = {
        name: store.download(SOURCE, url, f"{name}.html", LICENCE, refresh=refresh).read_text("utf-8")
        for name, url in PAGES.items()
    }
    forward, reverse = parse(pages["anzsic_to_isic"]), parse(pages["isic_to_anzsic"])
    checks = check(forward, reverse)
    if checks["anzsic_classes_not_in_codelist"] or checks["codelist_classes_without_a_match"]:
        raise ValueError(f"the correspondence does not cover the ANZSIC classes exactly: {checks}")
    assigned = assign(forward)
    # The groups that would change if the ISIC to ANZSIC table were used instead
    alt = assign([(a, i, p) for i, a, p in reverse])
    checks["groups_that_differ_with_the_other_table"] = sorted(
        a for a in assigned if alt[a]["group"] != assigned[a]["group"]
    )
    weights = employing_businesses()
    fit = division_fit(assigned, weights)
    g = groups()
    out = {
        "title": "ANZSIC 2006 classes in the common industry groups (ISIC Rev. 4)",
        "method": prose(__doc__),
        "sources": [
            {"page": url, **{k: f[k] for k in ("retrieved", "sha256") if k in f}}
            for url in PAGES.values()
            for f in _manifest()
            if f["url"] == url
        ],
        "licence": LICENCE,
        "weights": "employing businesses at the end of the latest financial year (ABS CABEE)"
        if weights
        else "none (each class counts once; the business register panel was not built)",
        "checks": checks,
        "groups": [
            {
                **{k: grp[k] for k in ("id", "label", "isic", "anzsic_divisions", "stan")},
                "classes": sum(1 for a in assigned.values() if a["group"] == grp["id"]),
                **fit[grp["id"]],
            }
            for grp in g["groups"]
        ],
        "divisions": by_division(assigned, weights),
        "classes": assigned,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "anzsic_isic4.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (store.ROOT / "docs" / "international_industry_groups.md").write_text(markdown(out), encoding="utf-8")
    return out


def _share(x: float | None) -> str:
    return "" if x is None else f"{100 * x:.0f}%"


def markdown(out: dict) -> str:
    """The groups, how well ANZSIC divisions fit them, and the checks, as a short note."""
    c = out["checks"]
    notes = {g["id"]: g.get("note", "") for g in groups()["groups"]}
    lines = [
        "# Common industry groups: ANZSIC 2006 and ISIC Rev. 4",
        "",
        "Generated by `alicia international concordance` from the ABS correspondence tables "
        f"({' and '.join('<' + src['page'] + '>' for src in out['sources'])}). Groups are defined in "
        "`alicia/src/alicia/data/industry_groups.json`; every class's group is in "
        "`data/processed/international/anzsic_isic4.json`.",
        "",
        "## Method",
        "",
        out["method"],
        "",
        "## Groups",
        "",
        "'In group': of the employing businesses in the ANZSIC divisions used for the group, the share in classes "
        "assigned to it. 'Covered': of the employing businesses in classes assigned to the group, the share in those "
        f"divisions. Weights: {out['weights']}.",
        "",
        "| Group | ISIC Rev. 4 divisions | ANZSIC divisions | STAN | Classes | In group | Largest class going "
        "elsewhere | Covered | Largest class coming in |",
        "|---|---|---|---|---:|---:|---|---:|---|",
    ]
    for g in out["groups"]:
        divs = g["isic"]
        isic = (
            f"{divs[0]}-{divs[-1]}"
            if len(divs) > 2 and int(divs[-1]) - int(divs[0]) == len(divs) - 1
            else ", ".join(divs)
        )
        stan_ = " ".join(("+" if sign > 0 else "-") + code for code, sign in g["stan"]).lstrip("+")
        away = g["classes_elsewhere"][0] if g["classes_elsewhere"] else None
        come = g["classes_from_elsewhere"][0] if g["classes_from_elsewhere"] else None
        away_s = f"{away['anzsic']} {away['name']} (to {away['group']})" if away else ""
        come_s = f"{come['anzsic']} {come['name']} (from {come['division']})" if come else ""
        lines.append(
            f"| {g['label']} ({g['id']}) | {isic} | {', '.join(g['anzsic_divisions'])} | {stan_} | {g['classes']} | "
            f"{_share(g['in_group'])} | {away_s} | {_share(g['covered'])} | {come_s} |"
        )
    lines += ["", "Notes on the groups:", ""]
    lines += [f"- **{gid}**: {n}" for gid, n in notes.items() if n]
    lines += [
        "",
        "## By ANZSIC division",
        "",
        f"Divisions are flagged on the website (a † with a hover note) when at least {_share(FLAG)} of the employing "
        "businesses on either side are mismatched: 'Out' is the share of the division's businesses in classes ISIC "
        "puts in another group; 'In' is the share of its group's businesses in classes ANZSIC puts in other "
        "divisions.",
        "",
        "| Division | Group | Out | In | Flagged | Hover note |",
        "|---|---|---:|---:|---|---|",
    ]
    for d, v in out.get("divisions", {}).items():
        lines.append(
            f"| {d} {anzsic.name(d)} | {v['group']} | {_share(v['out_share'])} | {_share(v['in_share'])} | "
            f"{'yes' if v['flag'] else ''} | {v['note']} |"
        )
    split = {a: v for a, v in out["classes"].items() if v["share"] < 1}
    lines += [
        "",
        "## Classes that span groups",
        "",
        f"{len(split)} of {len(out['classes'])} ANZSIC classes have ISIC matches in more than one group (or, for "
        "7552, only in division 99). Each goes to the group with most of its matches:",
        "",
        "| Class | Group | Share of matches | Other groups |",
        "|---|---|---:|---|",
    ]
    for a, v in split.items():
        lines.append(
            f"| {a} {anzsic.name(a)} | {v['group']} | {_share(v['share'])} | {', '.join(v.get('other_groups', []))} |"
        )
    lines += [
        "",
        "## Checks",
        "",
        f"- Pairs: {c['pairs_anzsic_to_isic']} from ANZSIC to ISIC and {c['pairs_isic_to_anzsic']} from ISIC to "
        f"ANZSIC; {c['anzsic_classes']} ANZSIC classes (every class in the codelist) and {c['isic_classes']} ISIC "
        "classes.",
        "- In one direction only: "
        + (
            "; ".join(f"{a} to {i} (ANZSIC to ISIC table)" for a, i in c["only_in_anzsic_to_isic"])
            + "".join(f"; {a} to {i} (ISIC to ANZSIC table)" for a, i in c["only_in_isic_to_anzsic"])
            or "none"
        )
        + ".",
        "- Classes whose group would differ if assigned from the ISIC to ANZSIC table instead: "
        + (", ".join(c["groups_that_differ_with_the_other_table"]) or "none")
        + ".",
        "",
    ]
    return "\n".join(lines)
