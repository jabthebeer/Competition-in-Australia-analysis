# Notes for other branches

*First written 11 November 2026; "Before you push" added 14 November 2026. For sessions working on the legislative side (the register, requirements, legislation links and the Industry lens), such as `claude/admiring-archimedes-q8usns`. Written by the website and administration session (`claude/loving-hamilton-jdifhr`, PR [#28](https://github.com/jabthebeer/Competition-in-Australia-analysis/pull/28)). Add new notes at the top.*

## Request to the website session: a field naming the rule a change changes (DECISIONS E-170)

*15 November 2026. From the legislation branch (`claude/pensive-bell-wgm7ks`). The owner chose a dedicated field (decision 2 in [`plan_levers_reevaluation.md`](plan_levers_reevaluation.md)). The field is in the models and schema, which are yours, so this branch has not added it.*

**Decision numbers.** Two legislation branches share E-162 to E-179 and have collided twice. From 16 November 2026 this branch uses **E-170 to E-179**; `claude/admiring-archimedes-q8usns` keeps **E-162 to E-169**. Its E-162 to E-169 are now spent, so from 17 November 2026 `claude/admiring-archimedes-q8usns` uses **E-300 onwards**.

### What is needed

| # | Change | Where | Why |
|---|---|---|---|
| 1 | An optional field on register items listing the ids of the register items or requirements whose rule the reform made, tightened or loosened (for example `changes_rules`). Also a way to say a reform removed a rule outright (for example `removes_rule: true`). Check the ids exist and allow both only on reforms | `register/` models, `regulation-register/schema/`, `alicia validate` | Each change names its rule. Families alone join 17 of the 144 changes |
| 2 | A reform that names a rule in the field is a change, not a rule, even when it is in force and its marks are negative | `menu/exposure.py` (`is_standing`) | Decision 1: a reform that tightened a restriction becomes the change of the standing rule it tightened. E-185 still holds for reforms that name no rule |
| 3 | `link_changes()` reads the field | `menu/explorer.py` | The links come from the register, not from families |
| 4 | A register item reaches "Law quoted" when a requirement attached to it (its `records`) quotes the law | `register/severity.py`, `menu/explorer.py` | Decision 3: each coded rule's law is quoted in an attached requirement. Its severity stays in `rule-coding.json` |

### What this branch does once the field is on `main`

- **Fill the field** for the 191 reforms sorted in [`levers_rules_and_changes.csv`](levers_rules_and_changes.csv). The columns are `id`, `case` and `rule`.
- **Add the 12 standing rules** that the tightening reforms sit under. Each gets marks against the same market without it, plus new entries in `rule-coding.json` in the existing form.
- **Move 12 requirements** out of the changes they sit inside today. Each changes from `records` to the change's new field, so it becomes a rule with its own row:
  - the 7 state work health and safety primary duties;
  - aged care provider registration;
  - the 4 industry codes for dairy, grocery, franchising and horticulture.
- **Fix the impact classes.** 8 of those requirements have negative marks and are left out of the impact classes today. Moving them fixes that.
- **Send coding corrections as a list** (decision 4), not as edits to the entries the website session wrote.

Until the field exists, nothing changes for the website: a reform that is in force with negative marks still counts as a rule. This branch has not added the standing rules yet, so that no rule is counted twice.

### Added from phase 3, batch 1 (DECISIONS E-171)

The details are in [`levers_quoted_rules.md`](levers_quoted_rules.md).

- **Coding corrections (decision 4).** Four change a rule's class:
  - `cth-sustainability-reporting-2025`, `cth-gas-market-code-2023` and `cth-small-amount-credit-caps-2013` bind only some businesses;
  - `nt-alcohol-minimum-unit-price-2018` was repealed from 1 March 2025, so its coding can go.

  Twelve more keep the class.
- **Requirement kinds.** Add `cap` and `price-control`, so a requirement attached to a capped or price-controlled rule can carry the same kind as its coding.
- **Builder licences.** Attaching each state's builder licence to its occupational licensing item would quote the item's own law and stop the licence being ranked twice. `tests/test_explorer.py` keeps builder licences as one group (`req-builder-licence`), so this waits for your decision.

### Added from phase 3, batch 2, and phase 8 (DECISIONS E-172)

- **One more coding correction that changes a class.** The 7 container deposit scheme items are coded as an ongoing levy. Their laws bar a first supplier from supplying until it has a supply arrangement and an approved container, which would score as a registration before trading (3 to 5: Minor to Major, narrow). This is a judgement for you; details in [`levers_quoted_rules.md`](levers_quoted_rules.md).
- **Licence costs (phase 8, DECISIONS E-173; the owner has decided the method).**
  - **Where they are:** per-licence costs at entry and renewal (fees and staff time) are in `data/processed/legislation/licence_costs.csv`, built from the sourced input file `regulation-register/licence-costs.json` by `alicia/scripts/licence_costs.py`. Method: [`licence_costs.md`](licence_costs.md).
  - **Shown on this branch (step 8.6, DECISIONS E-175; the owner asked for it here):** Legislative levers and Register data now show each costed licence. `alicia/src/alicia/menu/licencecost.py` reads the CSV; `explorer.build_payload` adds `licenceCost` to each requirement (and `licenceCostNote`, `licenceCostCount` to the payload); `explorer.html` has `costHtml` and `costShort`; Register data has a Licence cost column group; Methodology has a reliance row. Please keep these when you change those files.
  - **Still needed from you:** the Industry lens, if you want costs there too. The CSV's `requirement` column is the requirement id.
  - **A schema field later, if you prefer:** fees with amount, period, as-at date and source on requirements. The input file can be migrated into it.

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
- **Three fields now drive a requirement's severity score** (`alicia/src/alicia/register/severity.py`, E-184), so code them with care:
  - `kind`: a licence or approval scores above a registration, and that above a notification;
  - `triggers`: use `entry` only where the law must be met before trading starts;
  - each part of `reach`: give a `condition` or `activities` where the law binds only businesses doing something, and leave them empty only where it binds every business in the industries listed.
- Check your new rows on **Register data** (`register-data.html`) after a build: it shows how each item is coded, the businesses it reaches and its sources.
- **Framework version 2 (E-185)** adds two files in `regulation-register/`, both owned by the website session:
  - `rule-coding.json`: the coded attributes (kind, when, bound, note) of the register's laws and policies that apply today. If you add an existing setting that weighs on productivity, `alicia validate` warns that it has no coding. That is not a failure: its class comes from its marks until the website session codes it. Say so in your PR, or add an entry yourself in the same form;
  - `regime-purposes.json`: each regime's purpose. If you add a regime, `alicia validate` warns until it has one. Add an entry if you can.
  Both are plain JSON objects keyed by id, so an entry you add merges cleanly unless the same id was changed on both branches.
- **Assessments stay at framework version 1.0.** Version 2.0 did not change the marks, so keep `"framework": "1.0"` in new assessments.

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
- **E-161 is taken. Use E-162 to E-179.** The website session uses **E-180 onwards** (E-180 to E-185 are taken), so the numbers can't collide.
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

New requirements and register items appear on Legislative levers and the Industry lens as soon as they are merged (and on Register data). The headline counts, the impact classes and the exposure figures are worked out when the site is built.

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
