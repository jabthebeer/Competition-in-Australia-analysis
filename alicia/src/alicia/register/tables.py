"""Regression tables (``Evaluation.tables``) as Markdown and LaTeX, in the usual academic layout.

Each coefficient takes three lines: the estimate with significance stars (and a dagger when it is the registered
estimator), its spread in parentheses and its p-value in brackets. Text rows (sample sizes, fixed effects, tests)
follow each panel; footer rows apply to every panel.

    uv run alicia tables -o ../docs/econometric_tables.md --latex ../docs/econometric_tables.tex
"""

from __future__ import annotations

import re
from itertools import groupby

from .evaluation import Evaluation, ResultsTable, TableCoef, archived, recency, stars

DAGGER = "†"


def num(v: float | None, digits: int = 2) -> str:
    return "" if v is None else f"{v:.{digits}f}".replace("-", "−")


def pval(p: float | None) -> str:
    return "" if p is None else ("< 0.001" if p < 0.001 else f"{p:.3f}")


def coef_lines(c: TableCoef | None) -> tuple[str, str, str]:
    """(estimate with stars and dagger, spread in parentheses, p-value in brackets)."""
    if c is None:
        return "", "", ""
    mark = stars(c.p_value) + (DAGGER if c.registered else "")
    return (
        num(c.estimate) + mark,
        f"({num(c.spread)})" if c.spread is not None else "",
        f"[{pval(c.p_value)}]" if c.p_value is not None else "",
    )


def legend(t: ResultsTable, compact: bool = False) -> str:
    """The standard last note: what the parentheses, brackets, stars and dagger mean."""
    where = "stars from two-sided p-values" if compact else "two-sided p-values in brackets"
    return (
        f"{t.spread_label} in parentheses; {where}. * p < 0.10, ** p < 0.05, "
        f"*** p < 0.01. {DAGGER} The registered (pre-specified) estimator for that outcome."
    )


COMPACT_ROWS = 6  # LaTeX: tables with more coefficient rows put the estimate and spread on one line


# ---- Markdown -------------------------------------------------------------------------------------------------


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def table_markdown(t: ResultsTable, number: int | None = None) -> str:
    n = len(t.columns)
    head = "| | " + " | ".join(f"({i})<br>{_md_cell(c.label)}" for i, c in enumerate(t.columns, 1)) + " |"
    lines = [f"**Table{f' {number}' if number else ''}. {t.title}**", "", head, "|---|" + "---:|" * n]
    groups = [(g, len(list(cols))) for g, cols in groupby(c.group for c in t.columns)]
    if any(g for g, _ in groups):
        spans = " | ".join(" | ".join([f"*{g or ''}*"] + [""] * (k - 1)) for g, k in groups)
        lines.append(f"| | {spans} |")

    def row(label: str, cells: list[str]) -> str:
        return f"| {_md_cell(label)} | " + " | ".join(_md_cell(c) for c in cells) + " |"

    for p in t.panels:
        lines.append(row(f"***{p.title}***", [""] * n))
        for r in p.rows:
            if r.coefficients:
                parts = [coef_lines(c) for c in r.coefficients]
                lines.append(row(r.label, [x[0].replace("*", "\\*") for x in parts]))
                lines.append(row("", [x[1] for x in parts]))
                lines.append(row("", [x[2] for x in parts]))
            else:
                lines.append(row(r.label, [v or "" for v in r.values]))
    if t.footer:
        lines.append(row("***Specification***", [""] * n))
    for r in t.footer:
        lines.append(row(r.label, [v or "" for v in r.values]))
    notes = [*t.notes, legend(t)]
    lines += ["", "*Notes:* " + " ".join(notes), ""]
    return "\n".join(lines)


# ---- LaTeX ------------------------------------------------------------------------------------------------------

_TEX = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "<": r"$<$",
    ">": r"$>$",
    "^": r"\textasciicircum{}",
    "×": r"$\times$",
    "−": "$-$",
    "–": "--",
    "—": "---",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "†": r"$^{\dagger}$",
    "‡": r"$^{\ddagger}$",
    "β": r"$\beta$",
    "’": "'",
    "Σ": r"$\Sigma$",
    "ω": r"$\omega$",
    "²": r"$^{2}$",
    "\ue000": r"$\bar{M}$",
    "‘": "`",
}


def tex(text: str) -> str:
    text = text.replace("M\u0304", "\ue000")  # M-bar (combining macron) as one symbol
    return "".join(_TEX.get(ch, ch) for ch in text)


def _tex_head(label: str, width: int = 10) -> str:
    """A column heading, wrapped onto lines of about ``width`` characters."""
    lines: list[str] = []
    for word in label.split():
        if lines and len(lines[-1]) + 1 + len(word) <= width:
            lines[-1] += " " + word
        else:
            lines.append(word)
    if len(lines) == 1:
        return tex(label)
    return r"\shortstack{" + r"\\".join(tex(x) for x in lines) + "}"


def _tex_panel(title: str, width: int = 70) -> str:
    """A panel title; a long one breaks before its parenthesis so it does not widen the table."""
    cut = title.rfind(" (")
    if len(title) <= width or cut < 0:
        return tex(title)
    return rf"\shortstack[l]{{{tex(title[:cut])}\\{tex(title[cut + 1 :])}}}"


def _tex_num(text: str) -> str:
    """A formatted number with stars and dagger as LaTeX math."""
    if not text:
        return ""
    m = re.fullmatch(r"([−\-]?[\d.,]+)(\**)(†?)", text)
    if not m:
        return tex(text)
    val, st, dag = m.groups()
    sup = st + (r"\dagger" if dag else "")
    return f"${val.replace('−', '-')}" + (f"^{{{sup}}}" if sup else "") + "$"


def table_latex(t: ResultsTable) -> str:
    n = len(t.columns)
    compact = sum(1 for p in t.panels for r in p.rows if r.coefficients) > COMPACT_ROWS
    wide = n > 7  # set sideways (rotating package)
    out = [
        r"\begin{sidewaystable}\centering" if wide else r"\begin{table}[htbp]\centering",
        r"\footnotesize\setlength{\tabcolsep}{2.5pt}",
        rf"\caption{{{tex(t.title)}}}\label{{tab:{t.id}}}",
        r"\begin{threeparttable}",
        rf"\begin{{tabular}}{{l*{{{n}}}{{c}}}}",
        r"\toprule",
    ]
    groups = [(g, len(list(cols))) for g, cols in groupby(c.group for c in t.columns)]
    if any(g for g, _ in groups):
        cells, rules, col = [], [], 2
        for g, k in groups:
            cells.append(rf"\multicolumn{{{k}}}{{c}}{{{tex(g or '')}}}")
            if g:
                rules.append(rf"\cmidrule(lr){{{col}-{col + k - 1}}}")
            col += k
        out += [" & " + " & ".join(cells) + r" \\", " ".join(rules)]
    out.append(" & " + " & ".join(f"({i})" for i in range(1, n + 1)) + r" \\")
    out.append(" & " + " & ".join(_tex_head(c.label) for c in t.columns) + r" \\")
    out.append(r"\midrule")
    for i, p in enumerate(t.panels):
        if i:
            out.append(r"\addlinespace[1pt]" if compact else r"\addlinespace[2pt]")
        out.append(rf"\multicolumn{{{n + 1}}}{{l}}{{\textit{{{_tex_panel(p.title)}}}}} \\")
        for r in p.rows:
            if r.coefficients:
                parts = [coef_lines(c) for c in r.coefficients]
                if compact:
                    cells = [f"{_tex_num(x[0])} {tex(x[1])}".strip() for x in parts]
                    out.append(tex(r.label) + " & " + " & ".join(cells) + r" \\")
                    continue
                out.append(tex(r.label) + " & " + " & ".join(_tex_num(x[0]) for x in parts) + r" \\")
                out.append(" & " + " & ".join(tex(x[1]) for x in parts) + r" \\")
                out.append(" & " + " & ".join(tex(x[2]) for x in parts) + r" \\")
            else:
                out.append(tex(r.label) + " & " + " & ".join(tex(v or "") for v in r.values) + r" \\")
    if t.footer:
        out.append(r"\midrule")
        for r in t.footer:
            out.append(tex(r.label) + " & " + " & ".join(tex(v or "") for v in r.values) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\begin{tablenotes}\scriptsize"]
    out.append(r"\item \textit{Notes:} " + tex(" ".join([*t.notes, legend(t, compact)])))
    out += [r"\end{tablenotes}", r"\end{threeparttable}", r"\end{sidewaystable}" if wide else r"\end{table}", ""]
    return "\n".join(out)


# ---- documents ----------------------------------------------------------------------------------------------------


def _ordered(evaluations: list[Evaluation]) -> list[Evaluation]:
    """Current evaluations newest first, then archived ones; only those with tables."""
    gone = archived(evaluations)
    by_title = sorted((e for e in evaluations if e.tables), key=lambda e: e.title)
    newest = sorted(by_title, key=recency, reverse=True)  # stable: same-time evaluations stay in title order
    return [e for e in newest if e.id not in gone] + [e for e in newest if e.id in gone]


def tables_markdown(evaluations: list[Evaluation]) -> str:
    gone = archived(evaluations)
    lines = [
        "# Econometric results tables",
        "",
        "Generated from `regulation-register/evaluations/` by `alicia tables`. Do not edit by hand: change the "
        "analysis's builder script and regenerate. The same tables, in LaTeX (booktabs and threeparttable), are in "
        "`econometric_tables.tex`.",
        "",
        "One table per evaluation, newest first. Columns are estimators or registered specifications; each panel "
        "is one outcome. Every number comes from the analysis's registered outputs.",
        "",
    ]
    k = 0
    for ev in _ordered(evaluations):
        status = f" · archived, superseded by `{gone[ev.id]}`" if ev.id in gone else ""
        lines += [f"## {ev.title}", "", f"`{ev.id}` · evaluated {ev.evaluated_on:%d %B %Y}{status}", ""]
        for t in ev.tables:
            k += 1
            lines += [table_markdown(t, k), ""]
    return "\n".join(lines).rstrip() + "\n"


def tables_latex(evaluations: list[Evaluation]) -> str:
    head = [
        "% Econometric results tables, generated by `alicia tables` from regulation-register/evaluations/.",
        "% Do not edit by hand. Needs \\usepackage{booktabs,threeparttable,rotating}; tables wider than seven",
        "% columns are set sideways.",
        "",
    ]
    body = [table_latex(t) for ev in _ordered(evaluations) for t in ev.tables]
    return "\n".join(head + body)
