---
name: alicia-house-style
description: >-
  House style for the ALICIA website: the pages built by `alicia site` from
  alicia/src/alicia/menu/templates/ (landing page, Structural competitive conditions, Legislative
  levers influencing competition, Industry lens, Framework, Methodology). Use it whenever you restyle, reorder, add, archive,
  delete or review an ALICIA page, chart, table, the nav or the landing page, when you write or
  edit any of the site's text (to the Australian Government Style Manual), and before any UX or
  UI change to the site.
---

# ALICIA house style

ALICIA is a public research site full of data, read by people working on policy. A page is good
when a reader can find the figure they came for, understand it, and trace it to its source. It is
not a marketing site: no hero photographs, no animated "moments", no decorative effects.

Some rules below are adapted from tasteSkill (github.com/Leonxlnx/taste-skill, v2.5.1, MIT
licence, copyright 2026 Leonxlnx); they are marked [ts]. Where its rules conflict with this file,
this file wins, above all on captions: ALICIA's charts keep their notes and sources.

## Where things live

- **Templates:** `alicia/src/alicia/menu/templates/`. `site.css` is shared, through the
  `/*__SITE_CSS__*/` placeholder, by every page except `archive.html`, which carries its own
  copy of the tokens.

  | Template | Page |
  |---|---|
  | `home.html` | `index.html`, the landing page |
  | `growth.html` | Structural competitive conditions, with the economic conditions at its end |
  | `explorer.html` | `menu.html`, Legislative levers influencing competition |
  | `industry-lens.html` | Industry lens |
  | `framework.html` | Framework |
  | `methodology.html` | Methodology (text in `menu/methodology.py`) |
  | `archive.html` | The econometric archive and `evaluation-<id>.html` pages: archived, not built for the live site |
- **Nav, page names and landing cards:** `PAGES`, `NAV_GROUPS` and `LANDING` in
  `alicia/src/alicia/menu/growth.py`. The nav groups pages as Top down, Bottom up and About.
  `conditions.html` is only a forward to the economic conditions; nothing links to it.
- **Beta:** every page on the live site ends its h1 with `<!--__BETA__-->` (`growth.beta()`):
  "(beta)" with a work-in-progress tip. A new page gets it too.
- **Archived, not on the live site:** the Policy costing tab (`regulatory-burden-tool/`; built only
  with `--costing`) and the econometric archive (`archive.html`, `evaluation-<id>.html`; built only
  with `--archive`). Don't link to either from any page (DECISIONS E-135, E-136).
- **Build:**

  ```bash
  cd alicia && uv run alicia site -o <scratchpad>/site --dates "$(ls ../regulation-register/reports/effective_dates_*.json | sort | tail -n 1)"
  ```
- **Tests that pin page structure:** `tests/test_site.py`, `test_explorer.py`, `test_lens.py`,
  `test_framework_page.py` and `test_archive.py`. When a change is deliberate, update the test
  and say so in the PR. Never weaken a test only to get it to pass.

## 1. Words

- **Write all text to the Australian Government Style Manual** (stylemanual.gov.au), the
  writing standard for the Australian Public Service.
  - This covers every word on the site and in its downloads: headings, labels, buttons, notes,
    sources, notices and Excel sheets.
  - The rules below add what is specific to ALICIA. Where one of them differs from the Style
    Manual on how to write, follow the Style Manual and tell the owner, so this file can be
    fixed.
- Write in Australian English and plain words, in short sentences, as the site already does.
- **Use sentence case for every heading, nav label and button,** as the Style Manual requires.
  Capitalise only the first word and proper nouns: "Economic conditions", not "Economic
  Conditions".
- **A nav label matches its page's h1,** or is a clear short form of it.
- **Headings name the thing or state the finding** [ts], for example "Fewer new firms start up
  where regulation is heavy". A heading never claims more than its chart shows.
- **Buttons are a verb and an object:** "Clear all filters", "Download as Excel" [ts].
- **Numbers:**
  - put the unit in the label;
  - write financial years with an unspaced en dash, as in 2014–15 (Style Manual). The site
    uses a hyphen (2014-15) on its pages and in its data labels today. That is known drift, to
    fix only when the owner asks;
  - write dates as 11 November 2026 in running text. Where space is tight, as in tables and
    status lines, the site uses 11 Nov 2026;
  - give changes a sign (+1.3);
  - set figures in tabular numerals (`.num`, `.mono`).
- **Never invent, round for looks or "illustrate" a figure.** Every number on a page comes from
  `data/processed/` or a sourced register record (CLAUDE.md). If it can't be traced, take it out
  and say why.

## 2. Every chart and table carries its context

This section overrides tasteSkill's "no caption" rule. Every chart and table has:

1. a title (h2 or h3) and its unit;
2. an "i" button (`.info`) and a `details.more` "About this chart" with what the figures are and
   their limits, as `growth.html` does;
3. a source line (`.source`) naming the publisher and table, with a link, plus an entry in the
   page's "Data sources" section with a link to the methods note;
4. an Excel download when it follows a slider or drop-down (`xlsx.js`), as the existing charts
   do.

Also:

- Keep draft and beta status visible. Register items stay drafts until a person checks them;
  don't remove a `.notice` that says so.
- Colour is never the only signal: positive and negative also show a sign or an arrow.

## 3. One system [ts]

- **Colours come only from the tokens in `site.css` `:root`.** No raw hex in page CSS. Every
  token is defined three times: in `:root`, under `prefers-color-scheme: dark`, and under
  `[data-theme="dark"]`. A new token goes in all three.
- **Chart colours use the existing series tokens:**
  - `--s-<state>` for states;
  - `--c-1` to `--c-5` for series;
  - `--pos` and `--neg` for direction;
  - `--fill-*` for barrier groups;
  - `--t-*` for tiers of government.

  For a palette that doesn't exist yet, use the `dataviz` skill, then add tokens.
- **Type:** three families only.

  | Font | Use |
  |---|---|
  | Literata (`--font-display`) | h1 to h3 |
  | IBM Plex Sans (`--font-body`) | Body text |
  | IBM Plex Mono (`--font-mono`) | Numbers |

  Sizes come from the step scale, `--step--1` to `--step-3`. Sizes such as 0.75rem, 0.78rem,
  11px and 10px are drift: move them onto the scale when you touch that code.
- **Corners:**

  | Radius | Use |
  |---|---|
  | 10px | Panels and cards |
  | 6px | Buttons, selects and inputs |
  | 999px | Chips |
  | 50% | Round icon buttons |

  Other radii are drift.
- **One page width,** the `.wrap` in `site.css` (1240px). Don't give a page its own width
  without the owner's approval.
- **One page header** in the same order everywhere:
  1. nav;
  2. kicker;
  3. h1;
  4. lede (at most 72ch);
  5. a status line (counts, date updated), if any.

  Kickers follow one pattern across pages.
- **Reuse before inventing:**
  - `header.top`, `section.block` and `.block-head`;
  - `.panel` and `.toolbar`;
  - `.chips` with `.chip[aria-pressed]`;
  - `.info` with `details.more`;
  - `.note` and `.notice`;
  - `table.data` inside `.tscroll`;
  - `table.heat`;
  - `.site-nav`.

  A new component needs a reason, given in the PR.
- **At most two boxes deep:** a panel inside a panel, and no deeper [ts]. One style each for
  buttons, chips and links.

## 4. Layout and reading

- **Equal left and right edges:** every block lines up on the `.wrap` edges [ts].
- **What the reader came for comes first.** Methods, caveats and sources go lower or behind
  `details`.
- **A page with more than about five sections gets a row of in-page links** to them under its
  header.
- **Line lengths:** prose at most 72–80ch, notes at most 100ch.
- **A table wider than the screen scrolls inside `.tscroll`,** never the page.
- **Anything shown on hover can also be reached by keyboard focus and by tap,** as `.info`
  already allows.

## 5. Motion: calm

- No fade-in on scroll, parallax, scroll-jacking, carousels or autoplay [ts].
- Transitions only show a change of state (hover, open, close) and last 200ms at most.
- Under `prefers-reduced-motion`, everything rests and nothing stays hidden [ts]. `site.css`
  already does this; a page with its own styles must do it too.

## 6. Access [ts]

- **Controls and headings:**
  - every control has a name (a visible label or `aria-label`);
  - headings go down one level at a time;
  - no `tabindex` above 0;
  - the focus ring stays visible (`:focus-visible`).
- **Controls outside running text are at least 44px tall on phones.**
- **Text contrast** is at least 4.5:1 (3:1 for large text) in both themes. Check every new
  token in light and dark.
- **Nothing scrolls sideways** at 390px and 320px wide.

## 7. Reordering, archiving and deleting pages

- **Reorder** the nav with `PAGES` and `NAV_GROUPS`, and the landing page with `LANDING`, all in
  `growth.py`. They are set separately: when you change one, check the others still make sense.
- **Old URLs keep working.** People link to the site. `home.html` already forwards old
  `index.html#<id>` links to `menu.html`, and a moved page needs the same treatment.
- **Archive** a page by keeping it built and its URL working, with a dated "Archived" notice
  saying why and where the current material lives (as `archive.html` does). Take it out of the
  nav or landing page only when the owner says so.
- **Delete** a page only with the owner's confirmation. Before deleting, search the templates,
  `docs/`, the READMEs and the tests for links to it.
- **Log owner-approved UX decisions** in `alicia/DECISIONS.md` as the next E-number, as E-98,
  E-100 and E-101 did.

## 8. Check before opening a PR

1. In `alicia/`, run `uv run pytest -q`. If the register was touched, also run
   `uv run alicia validate`.
2. Build the site into the scratchpad (see "Where things live").
3. Open every changed page with Playwright (preinstalled; `chromium.launch()` takes no
   options):
   - at 1440x900 and 390x844;
   - with `colorScheme` light and dark.

   On each page, check:
   - that `document.documentElement.scrollWidth` equals the viewport width at 390 and 320;
   - that the console shows no errors.
4. Look at the screenshots yourself. In the PR, describe what changed on each page, before and
   after.
5. Open a PR into `main` for the owner to merge. Never push to `main`.
