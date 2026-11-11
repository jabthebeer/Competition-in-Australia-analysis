# Notes for other branches

*11 November 2026. For sessions working on the legislative side (the register, requirements, legislation links and the Industry lens), such as `claude/admiring-archimedes-q8usns`. Written by the website and administration session (`claude/loving-hamilton-jdifhr`, PR [#28](https://github.com/jabthebeer/Competition-in-Australia-analysis/pull/28)). Add new notes at the top.*

## Website restructure (PR #28, DECISIONS E-135 and E-136)

These changes reach `main` when the owner merges PR #28.

### Decision numbers

- **E-134 is yours** (Phase C batch 5). The website changes are **E-135** (restructure) and **E-136** (econometric archive off the site).
- **Use E-137 onwards** for your next entries, even before PR #28 is merged, so the numbers don't collide.

### Merging

- A trial merge of `claude/admiring-archimedes-q8usns` (at "Phase C batch 5") into PR #28 conflicts **only in `alicia/DECISIONS.md`**, because both branches add rows at its end.
- To resolve it, keep both sets of rows, in number order: E-134, then E-135 and E-136.
- On the combined code, all tests pass and `alicia validate` finds no problems (232 requirements).

### What changed on the site

- **New page names.** The addresses are unchanged, so existing links still work.
  - The legislation menu is now **Legislative levers influencing competition** (`menu.html`).
  - The state of competition in Australia is now **Structural competitive conditions** (`growth.html`).

  Use the new names in site text and methods notes.
- **The nav is grouped:**
  - **Top down:** Structural competitive conditions, Legislative levers influencing competition;
  - **Bottom up:** Industry lens, Regulatory overview by industry (coming soon);
  - **About:** Framework, Methodology.

  The groups are set in `NAV_GROUPS` in `alicia/src/alicia/menu/growth.py`.
- **"(beta)" on every page.** Each page heading ends with the `<!--__BETA__-->` placeholder, which the build fills with "(beta)" and a work-in-progress tip. The nav and landing cards add "(beta)" themselves, so `LENS_PAGE` is now just `("industry-lens.html", "Industry lens")`.
- **Economic conditions** is now the end of `growth.html`. The `conditions.html` template is deleted; the built `conditions.html` only forwards to `growth.html#economic-conditions`.
- **Taken off the site:** the Policy costing tab and the econometric archive (`archive.html`, `evaluation-<id>.html`). Their code stays. `alicia site --costing <build>` and `alicia site --archive` still build them, but the live site does not.
- **New Methodology page** (`methodology.html`, text in `alicia/src/alicia/menu/methodology.py`).

### What this means for legislative-side work

- **Industry lens template** (`industry-lens.html`):
  - Keep `<h1>Industry lens <!--__BETA__--></h1>`.
  - The old "Beta" pill and its `h1 .beta` style are gone, and `.beta` is now the shared marker's class, so don't reintroduce them.
  - Nav links now carry a `title` attribute. `tests/test_lens.py` matches the new markup.
- **No links to archived pages.** Don't link `archive.html`, `evaluation-<id>.html`, `costing.html` or `conditions.html` from any page; `tests/test_site.py` fails if a page does.
- **Methodology page counts** (register items, requirements, recommendations, regimes, bodies) are read from the register at build time. Adding requirements needs no edit there.
- **Methodology page wording is written by hand.** Its statements about your methods are text in `methodology.py`:
  - the Open Australian Legal Corpus copy last updated in March 2025;
  - ABLIS-first drafts;
  - councils limited to capital cities;
  - the high, medium and low confidence rules.

  If any of these changes, update that text.
- **Unchanged for you:** the register and requirement schemas, `alicia validate`, the requirement files and the daily refresh of `data/processed/costing/` (the Industry lens still reads it).

### Writing standard

- Methods notes in `docs/` follow the Australian Government Style Manual (`CLAUDE.md`).
- Website text follows the house-style skill in `.claude/skills/alicia-house-style/`, which loads for any website change.
