# Competition-in-Australia-analysis
A series of econometric analyses for competition in Australia, aiming to ultimately assess where business dynamism is constrained and what policy drivers can be used to lift productivity through higher competition. 

## Browse the ALICIA legislation menu

The menu explorer is one HTML page built from the register. Use it to search the 69 changes, filter for **Evaluated** ones and open the **Results** tab for each evaluation's estimated effects and charts.

- **On GitHub Pages:** <https://jabthebeer.github.io/Competition-in-Australia-analysis/>
  - It is published by `.github/workflows/menu-explorer-pages.yml` on every push to `main`.
  - One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
- **Locally:** `cd alicia && uv run alicia explorer --standalone -o menu.html`, then open `menu.html` in a browser.

## Current priority (22 October 2026)

Forward-looking costing of prospective policies: a new interactive **Policy costing** tab on the ALICIA website, with a regulatory burden costing (OIA *Regulatory Burden Measurement Framework*) and a productivity and competition costing. Plan: [`docs/forward_plan_policy_costing.md`](docs/forward_plan_policy_costing.md). The retrospective evaluations are paused (`alicia/DECISIONS.md` E-75); parked items are in [`docs/parked_items.md`](docs/parked_items.md).

## Projects

- [`regulatory-burden-tool/`](regulatory-burden-tool/): an unofficial calculator for regulatory burden under the OIA Regulatory Burden Measurement framework, with reform (remove-and-replace) comparisons and analysis-ready exports for competition and business-dynamism research.
- [`alicia/`](alicia/): **ALICIA**, Australian Legislation Impact on Competition Industry Analysis: a public-data toolkit for evaluating how legislation affects competition. It has a register of changes, an effective-date gatherer that checks the legislation registers, an evaluability screen, a menu explorer that shows evaluated changes and their results, and the analyses behind those results.
- [`regulation-register/`](regulation-register/): the register itself, with one record per regulatory change per jurisdiction, and dated reports from the date checks.
- **Barriers to entry and profitability** (on the ALICIA website's State and industry growth and Economic conditions pages): Grattan Institute's 2017 *Competition in Australia* charts recreated from public data (ABS business counts, ATO company tax statistics, RBA). Methods and results: [`docs/methods_competition_charts.md`](docs/methods_competition_charts.md).

## Planning

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
