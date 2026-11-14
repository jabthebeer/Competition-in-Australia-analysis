# Plan: overhaul of the ALICIA website

*14 November 2026. Approved by the owner (DECISIONS E-159). What the pages should say, as distinct from how they are laid out, is in [`plan_policy_tool.md`](plan_policy_tool.md) (E-161).*

* Mock-ups of every page: [ALICIA site overhaul mock-ups](https://claude.ai/artifact/UAGipkw8X1iWrg1Wu9eh91) (private to the owner). Other branches are paused while this work runs.*

## Why

The three main pages are too long to read. At desktop width on 14 November 2026:

| Page | Length | Words |
|---|---|---|
| Legislative levers influencing competition | 49 screens | 8,700 |
| Industry lens | 36 screens | 13,400 |
| Structural competitive conditions | 17 screens | 3,900 |

## End goals

**The site:** show where competition is weak in Australia, which laws and barriers hold it back, and what governments could change.

| Page | End goal | Opens with |
|---|---|---|
| Home | Tell a new reader what the site is and get them to the right page in one click | 4 headline figures, then 3 questions to start from |
| Structural competitive conditions | Show the state of competition in Australia | A scorecard: entry, exit, concentration, mark-ups, returns |
| Legislative levers influencing competition | Give an overview of the barriers to competition | How barriers act, who sets them, and the biggest ones ranked |
| Industry lens | Show an industry as a business in one state sees it | One sentence: its market, its legal requirements, who it answers to |
| Regulatory overview by industry | Compare industries by the regulation they face | A table of the 19 industry divisions; each row opens the lens |
| Productivity framework | Explain how items are marked | One worked example of how to read a mark |
| Methodology | Show how far to rely on each part of the site | A table: where each part comes from, how it is checked, its status |

## Design rules

- **Answer first.** Each page opens with the few figures that answer its question.
- **Tabs, not one long scroll.** An Overview tab summarises; the other tabs hold the detail.
- **Controls sit with their charts.** Each tab keeps its own place, industry and years controls. The mock-ups showed one set for each page; that was dropped in phase 3 because the datasets cover different years and places (see "Changes from the mock-ups").
- **Short lists:** the top few, with "see all".
- **One layout on every page:** one width (1240px), a one-line nav, the same header and closing lines.
- **Real figures only.** Every headline figure is worked out from the page data at build time, and a test recomputes it from the source files by a separate route.

## Owner's decisions (14 November 2026)

1. **Industry lens order:** the business's view first (market, requirements, regulators). Pain points come later on the page. This replaces the order set in E-150.
2. **Regulatory overview by industry:** build it as a real page from `data/processed/industry_regulation/`. It takes over the Industries view on the levers page.
3. **Nav labels:** short labels ("Competitive conditions", "Legislative levers", "Regulatory overview") and one Beta badge beside the site's name. Page headings keep their full names and "(beta)".
4. **Tabs** on the long pages.

## Phases

Each phase is a pull request for the owner to merge. The site works after each, and page addresses do not change.

| Phase | Scope | Status |
|---|---|---|
| 1. Foundations | The shared layout: one-line nav with a Menu button on phones, one page width, figure tiles, buttons, closing lines | Done (14 November 2026) |
| 2. Home | Headline figures from the data, 3 questions to start from, an industry and state picker for the lens | Done (14 November 2026) |
| 3. Structural competitive conditions | An Overview tab with a scorecard of 5 figures and 3 findings; 5 tabs for the detail; the sources folded at the foot (the tabs component is built here) | Done (14 November 2026, E-160) |
| 4. Legislative levers | An Overview tab: biggest barriers by impact class with the businesses each reaches, how barriers act, who sets the rules. The register (list, scorecard, timeline, what others recommend, industries) in its own tab | Done (14 November 2026, E-180) |
| 5. Industry lens and Regulatory overview by industry | The lens in 4 tabs, the business's view first (its market, its requirements, who it answers to, pain points). Regulatory overview by industry built: the 19 divisions and 506 detailed industries compared | Done (14 November 2026, E-181) |
| 6. Framework and Methodology | Framework leads with a worked example, and says version 2 is being built; Methodology leads with a table of how far to rely on each part | Done (14 November 2026, E-182) |
| 7. Finish (next) | Phone and accessibility pass; Style Manual pass on all text, including en dashes in financial years and short forms of the states; a check of every headline figure; docs updated | To do |

## Changes from the mock-ups

- **No single control bar on Structural competitive conditions (phase 3).** The mock-up showed one Place, Industry and Years bar for the whole page. The data can't support it:
  - concentration and mark-ups are for Australia only, 2002 to 2019 and 2004 to 2017;
  - company returns cover 2018–19 to 2022–23;
  - business entry covers 2007–08 to 2024–25, by state.

  One bar would offer choices that most charts could not follow. Each tab keeps the controls its data support.
- **The scorecard sits in the Overview tab,** not above the tabs. Placed above, it would repeat on every tab and push each tab's charts down the page.
- **The Overview findings follow the settings chosen in their tabs.** The scorecard does not: it always shows Australia, businesses with employees, and each series' first and last years.

## Notes for whoever builds a phase

- The house style is in `.claude/skills/alicia-house-style/SKILL.md`.
- The nav, page list and short labels are in `alicia/src/alicia/menu/growth.py` (`PAGES`, `NAV_GROUPS`, `NAV_LABELS`, `nav()`).
- Home is `alicia/src/alicia/menu/home.py`; its tests are `alicia/tests/test_home.py`.
- Shared components are in `alicia/src/alicia/menu/templates/site.css`: `.tiles.headline` and `.tile`, `.btn` and `.btn.primary`, `.site-foot`, `.tabs` and `.tab-panel`, `.findings` and `.finding`, `.more-links` and `.more-link`, `.minibars`.
- Tabs: mark up a `.tabs[role="tablist"]` row and `.tab-panel[role="tabpanel"]` panels as `growth.html` does, then call `initTabs()` (in `charts.js`). The address follows the open tab (`growth.html#concentration`), and a link to any id inside a panel opens that panel. Without scripts, every panel shows.
- Exposure (the businesses a rule reaches) and the impact classes are worked out in `alicia/src/alicia/menu/exposure.py` when the site is built, and added to every row of the levers page's data (`exposure`, `standing`, `impactClass`). Tests: `alicia/tests/test_exposure.py`. The rule and its stopgap are in [`plan_policy_tool.md`](plan_policy_tool.md).
- Regulatory overview by industry is `alicia/src/alicia/menu/overview.py` and `templates/regulatory-overview.html`; its tests are `alicia/tests/test_overview.py`.
- A page whose address holds its own state (the Industry lens: `#division=H&class=4511&state=NSW`) calls `initTabs(list, { hash: false })`, so the tabs leave the address alone.
- Headline figures are worked out in `alicia/src/alicia/menu/figures.py` when the site is built. Home and the scorecard both use it. Tests: `alicia/tests/test_home.py` and `alicia/tests/test_scorecard.py`.
