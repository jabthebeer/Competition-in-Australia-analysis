# CLAUDE.md

## Project context
Research project on weak competition and constrained business dynamism in Australia: literature review + econometric analysis of public data, aiming at policy reform recommendations to lift productivity. See `README.md`.

## Division of labour
- The owner uses **Claude Cowork** for writing, literature synthesis and project management.
- **Claude Code's role here:** (1) support data collection, and (2) help develop interesting, novel econometric analysis. Don't draft long-form prose deliverables here; produce tables, figures, and short methods notes in `docs/` for Cowork to use.

## Conventions
- Use **R** as the default language (tidyverse, fixest, plm, did, modelsummary, ggplot2, readabs, OECD/WDI API packages). Use `renv` for package management. Python only if a method or data tool clearly needs it, and flag it first.
- Prefer Quarto (`.qmd`) or plain `.R` scripts in `analysis/`; keep scripts runnable top to bottom.
- Never edit files in `data/raw/`. Cleaning goes in scripts that write to `data/processed/`. Every analysis must be reproducible from raw data via scripts.
- Record every dataset in `data/SOURCES.md`: publisher, URL, date accessed, licence/access limits, coverage, variables of interest.
- Do not fabricate data, citations, or statistics. If a source can't be reached or a figure can't be verified, say so.
- State identification assumptions, sample, and limitations for every estimate; flag when public data is too aggregated to support a claim (e.g. firm-level markups).
- Large or restricted data (e.g. BLADE) must not be committed.
- Develop on the designated feature branch; commit with clear messages.
