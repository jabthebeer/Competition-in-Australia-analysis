# Notes for other branches

*First written 11 November 2026; "Before you push" added 14 November 2026. For sessions working on the legislative side (the register, requirements, legislation links and the Industry lens), such as `claude/admiring-archimedes-q8usns`. Written by the website and administration session (`claude/loving-hamilton-jdifhr`, PR [#28](https://github.com/jabthebeer/Competition-in-Australia-analysis/pull/28)). Add new notes at the top.*

## Before you push (every session adding legislation)

*14 November 2026. From the website session (`claude/loving-hamilton-jdifhr`). The owner has asked for these steps so that legislation work and the website work merge cleanly (DECISIONS E-161).*

The website and the framework are being rebuilt while you add legislation. The two kinds of work touch different files, with a few shared ones. Follow these steps and your branch will merge.

### 1. Start from, and return to, `main`

```bash
git fetch origin main
```

```bash
git merge origin/main
```

Merge `main` into your branch before each push, not only at the start. Don't rebase a branch that is already pushed.

### 2. What is yours, and what to leave alone

| Yours to change | Leave alone (the website session's) |
|---|---|
| `regulation-register/requirements/`, `records/`, `regimes/`, `requirement-gaps.json`, `families.json`, `bodies.json` | `alicia/src/alicia/menu/` (every page, template, `site.css`, `charts.js`) |
| `data/processed/legislation/` | `alicia/src/alicia/register/framework.py` and `docs/productivity_framework.md` |
| `docs/plan_legislation_links.md`, `docs/plan_states.md`, `docs/methods_legislation_links.md` | `regulation-register/schema/` and the models in `alicia/src/alicia/register/` |
| Your own row in `alicia/DECISIONS.md` | `docs/plan_site_overhaul.md`, `docs/plan_policy_tool.md`, `.claude/skills/` |

If you need a change on the right-hand side (a new field, a new kind of requirement, a fix to a page), don't make it. Write what you need at the top of this file and tell the owner.

### 3. Keep to the current schema

- Draft requirements and register items exactly as now. Framework version 2 ([plan](plan_policy_tool.md)) will add optional fields (fee, waiting time, renewal, purpose). It will not rename or remove a field you use.
- Don't add fields the schema does not have. `uv run alicia validate` rejects them.
- Keep marking each item on the 8 drivers as now. The marks stay, as the judgement layer.
- Wherever the law states them, record thresholds with their value, unit and date, and the trigger (before trading starts, first employee, a size threshold). Version 2 scores rules from these.

### 4. Generated files: rebuild, never merge by hand

These files are written by scripts. If `git merge` reports a conflict in one, take either side and rebuild it. Never edit it by hand.

| File | Rebuild with (from `alicia/`) |
|---|---|
| `data/processed/legislation/links.csv.gz`, `links_summary.csv` | `uv run python scripts/requirement_links.py` |
| `data/processed/legislation/agencies_by_class.csv`, `requirement_agencies.csv` | `uv run python scripts/agency_overlap.py` |
| `data/processed/legislation/*_catalogue.csv`, `state_catalogue_estimate.csv` | the script that wrote them (`state_catalogues.py`, `frl_catalogue.py`, `legislation_estimate.py`) |
| `data/processed/industry_regulation/` and `docs/industry_regulation.md` | `uv run python scripts/industry_regulation.py` |
| `docs/productivity_framework.md` | `uv run alicia framework -o ../docs/productivity_framework.md` (website session only) |

Check each script's own header for its arguments before you run it. `links.csv.gz` is a compressed file, so git cannot merge it: after any merge that touches requirements, rebuild it and commit the result.

### 5. `alicia/DECISIONS.md`

- Rows are added at the end, so two branches always conflict there. Keep both sets of rows, in number order.
- **E-161 is taken. Use E-162 to E-179.** The website session uses **E-180 onwards** (E-180 to E-183 are taken), so the numbers can't collide.
- One row for each batch, as now.

### 6. Check before you push

From `alicia/`:

```bash
uv run alicia validate
```

```bash
uv run pytest -q
```

```bash
uv run ruff check src tests
```

All 3 must pass after the merge from `main`, not only before it. If a website test fails because of your data (for example, a test that recomputes a page's figure), don't change the test: tell the owner, and note it at the top of this file.

### 7. Open a pull request for the owner

Never push to `main`. Say in the pull request which batch it is, how many requirements it adds, and that the 3 checks pass.

### What the website shows from your data, with no code change

New requirements and register items appear on Legislative levers and the Industry lens as soon as they are merged (and on Register data, once it is built). The headline counts, the impact classes and the exposure figures are worked out when the site is built.

## Website overhaul in progress (DECISIONS E-159)

*14 November 2026. From the website session (`claude/loving-hamilton-jdifhr`). The owner has paused other branches while it runs.*

- **Plan:** [`plan_site_overhaul.md`](plan_site_overhaul.md) has each page's end goal, the design rules and the phases.
- **Decision numbers:** see "Before you push" above: use **E-162 to E-179**.
- **Nav:** one line, with short labels set in `NAV_LABELS` in `alicia/src/alicia/menu/growth.py` and one Beta badge beside the site's name. Links no longer carry "(beta)"; page headings still do.
- **Width:** every page is 1240px wide. Don't set `max-width` on `.wrap` in a page template; a test fails if one does.
- **Home** is built by `alicia/src/alicia/menu/home.py`. `growth.landing()` and `LANDING` are gone.
- **Structural competitive conditions is in tabs (E-160).** Section ids are unchanged, and a link to any of them opens the right tab (`growth.html#economic-conditions` still works). In `site.css`, `.tabs` now means a row of tabs (`initTabs()` in `charts.js`). Headline figures come from `alicia/src/alicia/menu/figures.py`.
- **Levers and lens are in tabs (E-180, E-181).** The lens leads with the business's view (its market, its requirements, who it answers to); pain points are the last tab (this replaces the order in E-150). Their page data is as it was, with 3 fields added to each row of the levers data (`exposure`, `standing`, `impactClass`), so new requirements and register items keep appearing with no code change.
- **Regulatory overview by industry** is now a page (`regulatory-overview.html`), built from the regimes, the requirements and the ABS counts.

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

## Requirements on Legislative levers influencing competition (DECISIONS E-137)

*11 November 2026. From the branch `claude/sharp-bell-4dsvcz`, in a pull request for the owner to merge.*

### Decision numbers

- **E-137 is taken** by this change. Use **E-138 onwards** for your next entries.
- If your branch has already used E-137, renumber your entry when you merge, and keep the rows in number order.

### What changed for legislative-side work

- **Requirements now appear on the levers page too** (`menu.html`), read from `regulation-register/requirements/` at each build. A new requirement needs no code change.
  - A requirement whose `records` names a register item (the same law in force) is shown **inside that item**, not as a row of its own.
  - The others are rows, grouped by `family` into one expandable row when two or more places have the same requirement.
- **One vocabulary for both pages** (`alicia/src/alicia/register/competition.py`):
  - the market positions are **Entrants**, **Existing competitors**, and **Monopolies and oligopolies**;
  - `EFFECT_PHRASES` words each position's effect, such as "Harder to start up or enter";
  - `most_affected()` gives the position whose marks weigh most.

  Use these names in site text and methods notes, not "small and medium competitors" or "the largest players".
- **Types of item** (`INFLUENCE_TAGS` and `INFLUENCE_GROUPS` in `register/framework.py`):
  - reforms, existing settings and requirements are all **legislative influences**;
  - a non-legislative barrier keeps its own tag;
  - the Industry lens no longer shows "Reform" or "Existing setting" tags.
- **Tests:** `tests/test_explorer.py` checks that every requirement is a row or sits inside its item, never both, and that neither page uses the old labels.
