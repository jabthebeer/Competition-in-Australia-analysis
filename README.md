# Competition-in-Australia-analysis
A series of econometric analyses for competition in Australia, aiming to ultimately assess where business dynamism is constrained and what policy drivers can be used to lift productivity through higher competition. 

## Browse the ALICIA legislation menu

The legislation menu is a register of what shapes competition and productivity in Australia: reforms (passed or proposed), existing regulatory settings and non-legislative barriers. Every item is marked against the [ALICIA productivity framework](docs/productivity_framework.md) on eight drivers of productivity, and shown with summary statistics for the industries it affects. Filter by **main driver** to see what weighs on productivity.

- **On GitHub Pages:** <https://jabthebeer.github.io/Competition-in-Australia-analysis/> (the menu, the Framework page, The state of competition in Australia and Economic conditions pages, the Policy costing tab, and the econometric archive)
  - It is published by `.github/workflows/menu-explorer-pages.yml` on every push to `main`.
  - One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
- **Locally:** `cd alicia && uv run alicia explorer --standalone -o menu.html`, then open `menu.html` in a browser; `uv run alicia site -o ../site` builds every page.

## Current priority (28 October 2026)

**A productivity framework applied to legislation, settings and barriers** (owner decision, `alicia/DECISIONS.md` E-87 to E-90 and E-92):

1. **Framework** (done): eight drivers of productivity, each marked from −2 to +2 ([methods note](docs/productivity_framework.md); the website's Framework page).
2. **Assessment of the register** (done): all records assessed; the menu's econometric sections are replaced by the assessments and industry statistics. The econometric evaluations are archived on the site, unchanged.
3. **Review of the register** (done): [`docs/register_review_framework.md`](docs/register_review_framework.md). The reforms were chosen for evaluability and are a skewed sample.
4. **Additions** (two tranches done, 63 items: stamp duty, payroll tax, trade and foreign investment settings and concentrated markets, then planning and zoning, occupational licensing, pharmacy ownership and location rules, mandatory standards, insurance duty and other settings); the review lists the remaining candidates.

Every assessment is a draft until checked by a person: the review sheet is [`docs/review/framework_assessments_review.csv`](docs/review/framework_assessments_review.csv). The Policy costing tab ([plan](docs/forward_plan_policy_costing.md)) quantifies what the framework marks. The retrospective evaluations were paused on 22 October 2026 (E-75); parked items are in [`docs/parked_items.md`](docs/parked_items.md).

## Projects

- [`regulatory-burden-tool/`](regulatory-burden-tool/): an unofficial calculator for regulatory burden under the OIA Regulatory Burden Measurement framework, with reform (remove-and-replace) comparisons and analysis-ready exports for competition and business-dynamism research.
- [`alicia/`](alicia/): **ALICIA**, Australian Legislation Impact on Competition Industry Analysis: a public-data toolkit for assessing how legislation, regulatory settings and other barriers affect productivity and competition. It holds the productivity framework, the register and its validation, an effective-date gatherer that checks the legislation registers, the website (legislation menu, framework, growth and conditions pages, econometric archive) and the archived econometric analyses.
- [`regulation-register/`](regulation-register/): the register itself, with one record per reform, setting or barrier per jurisdiction, each with its framework assessment, and dated reports from the date checks.
- **Barriers to entry and profitability** (on the ALICIA website's The state of competition in Australia and Economic conditions pages): Grattan Institute's 2017 *Competition in Australia* charts recreated from public data (ABS business counts, ATO company tax statistics, RBA). Each chart downloads as an Excel workbook with the chart, its numbers and its sources. Methods and results: [`docs/methods_competition_charts.md`](docs/methods_competition_charts.md).

## Planning

- [`docs/productivity_framework.md`](docs/productivity_framework.md): the productivity impact framework (version 1.0, 28 October 2026), written by `alicia framework` from the same definition the website uses.
- [`docs/register_review_framework.md`](docs/register_review_framework.md): the register reviewed under the framework, the items added, and candidates to add next (28 October 2026).

Archived econometric work (paused 22 October 2026; the results stay published in the site's econometric archive):

- [`docs/econometric_foundation_scoping.md`](docs/econometric_foundation_scoping.md): scoping note (14 October 2026) for an econometric foundation that links regulatory changes and their compliance costs to competition, business dynamism and innovation outcomes. Decisions taken 14 October 2026 (`alicia/DECISIONS.md`, E-01 to E-07).
- [`docs/impact_evaluation_design.md`](docs/impact_evaluation_design.md): how each change will be evaluated against entry and exit, productivity, real prices and wages (draft, 15 October 2026).
- [`docs/robustness_review_wa_trading_hours.md`](docs/robustness_review_wa_trading_hours.md): blinded design-stage robustness review of the first case, Perth trading-hours deregulation (2010, 2012), with its pre-analysis plan [`docs/pap_wa_trading_hours.md`](docs/pap_wa_trading_hours.md) and results [`docs/results_wa_trading_hours.md`](docs/results_wa_trading_hours.md) (15 October 2026): no detectable effect on retail entry or exit, grade Moderate.
- [`docs/results_high_evaluability.md`](docs/results_high_evaluability.md): the other high-evaluability reforms (seven reforms, 16 records) under one plan, [`docs/pap_high_evaluability.md`](docs/pap_high_evaluability.md): no detectable effect on entry or exit; three not identified.
# Competition in Australia Analysis

A research project to understand **weak competition and constrained business dynamism in Australia**, using literature review and econometric analysis of publicly available data, and ultimately to identify **policy reforms** that could lift productivity through stronger competition.

## Aims

1. **Diagnose** – build a clear, evidence-based picture of where and how competition is weak in Australia (market concentration, markups, entry/exit rates, job reallocation, barriers to entry, regulatory burden).
2. **Explain** – identify the drivers (e.g. regulation, licensing, merger settings, common ownership, labour-market frictions such as non-competes, digital and network effects).
3. **Quantify** – link weak competition to outcomes (productivity, investment, wages, prices, innovation) with credible, novel econometric methods.
4. **Reform** – translate findings into policy analysis and recommendations.

## Workstreams and roles

| Workstream | Where | Lead |
|---|---|---|
| Writing, literature synthesis, project management | Claude Cowork | Project owner |
| Data collection, cleaning, econometric analysis (this repo) | Claude Code | Project owner + Claude Code |

This repo holds the **data and code**. Prose outputs and project management live in Cowork; results are exported here (tables, figures, short methods notes) for it to draw on.

## Candidate public data sources

- **ABS**: Australian Industry; Counts of Australian Businesses (entries/exits); Business Longitudinal Analysis Data Environment (BLADE, restricted access); National Accounts; Labour Account; Business Indicators.
- **ATO**: Corporate tax transparency data; taxation statistics.
- **Productivity Commission**: Productivity data, inquiry reports and datasets (e.g. *Advancing Prosperity*, competition and dynamism work).
- **Treasury / RBA**: Competition reviews, RBA research discussion papers and business dynamism work.
- **ACCC / AER**: Market inquiries, merger data, regulatory determinations.
- **Melbourne Institute (HILDA)**, **OECD** (Product Market Regulation, STRI, Business Dynamics), **World Bank**, **Penn World Table**, **EU KLEMS/GGDC** for international benchmarks.

Sources and access status are tracked in [`data/SOURCES.md`](data/SOURCES.md).

## Candidate analytical themes

- Market concentration trends (HHI, CR4) by industry, and their reliability given limited public data
- Markup estimation (production-function approach, De Loecker–Eeckhout style) using firm-level and aggregate data
- Business entry/exit and job reallocation, and the decline of dynamism
- Productivity dispersion and the frontier–laggard gap
- Regulatory and licensing barriers vs entry (industry-level panels, difference-in-differences around reforms)
- Labour-market competition (monopsony, non-competes, wage-setting power)
- Merger and enforcement effects; event studies of policy changes
- International comparison using OECD indicators

## Repo structure

```
data/raw/         Unmodified downloads (large files git-ignored; document in SOURCES.md)
data/processed/   Cleaned, analysis-ready datasets
literature/       Reading notes, bibliography, review summaries
analysis/         R scripts and Quarto documents (econometrics)
docs/             Methods notes, outputs handed to Cowork
```

See [`CLAUDE.md`](CLAUDE.md) for working conventions.
