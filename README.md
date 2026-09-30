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
analysis/         Scripts and notebooks (econometrics)
docs/             Methods notes, outputs handed to Cowork
```

See [`CLAUDE.md`](CLAUDE.md) for working conventions.
