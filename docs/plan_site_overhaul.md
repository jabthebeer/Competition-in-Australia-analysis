# Plan: overhaul of the ALICIA website

*14 November 2026. Approved by the owner (DECISIONS E-159). Mock-ups of every page: [ALICIA site overhaul mock-ups](https://claude.ai/artifact/UAGipkw8X1iWrg1Wu9eh91) (private to the owner). Other branches are paused while this work runs.*

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
- **One set of controls for each page:** place, industry and years.
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
| 3. Structural competitive conditions | Scorecard, one control bar, tabs (the tabs component is built here) | Next |
| 4. Legislative levers | Overview tab (drivers, governments, biggest barriers, recommendations); the full list in its own tab | To do |
| 5. Industry lens and Regulatory overview by industry | The lens reordered around the business; the overview page built | To do |
| 6. Framework and Methodology | Framework leads with a worked example; Methodology leads with a reliance table | To do |
| 7. Finish | Phone and accessibility pass; Style Manual pass on all text, including en dashes in financial years and short forms of the states; a check of every headline figure; docs updated | To do |

## Notes for whoever builds a phase

- The house style is in `.claude/skills/alicia-house-style/SKILL.md`.
- The nav, page list and short labels are in `alicia/src/alicia/menu/growth.py` (`PAGES`, `NAV_GROUPS`, `NAV_LABELS`, `nav()`).
- Home is `alicia/src/alicia/menu/home.py`; its tests are `alicia/tests/test_home.py`.
- Shared components are in `alicia/src/alicia/menu/templates/site.css`: `.tiles` and `.tile`, `.btn` and `.btn.primary`, `.site-foot`.
