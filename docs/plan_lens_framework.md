# Plan: framework version 2 on the Industry lens

*15 November 2026. Written by the legislation branch (`claude/admiring-archimedes-q8usns`) at the owner's request. The page code is the website session's (see "Before you push" in [`notes_for_other_branches.md`](notes_for_other_branches.md)), so each phase says who does it.*

## Where things stand

Framework version 2 ([methods note](productivity_framework.md), DECISIONS E-184 and E-185) asks 3 questions about each rule:

1. Does it weigh on productivity? The 8-driver marks answer this, as a judgement.
2. How hard does it bite on each business it binds? Severity answers this, scored from coded facts: kind, when it bites and whom it binds.
3. How many businesses does it bind? Exposure answers this, counted from the ABS business counts.

Severity and exposure give each rule an impact class: Severe; Major, wide; Major, narrow; or Minor.

Legislative levers and Register data already show version 2. The Industry lens still shows version 1 only:

- the effect table adds up the marks in each market-position column;
- each row's tag shows the total of its marks;
- rows sort by that total;
- the lens colours come from the marks.

Version 2 no longer ranks on the total.

The data for version 2 is ready for every requirement. Severity is worked out from fields each requirement already has, and the 102 register items that apply today are coded in `rule-coding.json`. Since 15 November 2026 (E-162), the state drafts take their kind, trigger and reach from their own law, not from the NSW draft, because these now set severity.

## The goal

For a chosen industry and state, the lens answers the 3 questions for each law that binds the business, and shows the evidence behind each answer:

- the law named;
- the law quoted, with a link to the provision;
- coded;
- counted.

## Phases

| Phase | What | Who | Depends on |
|---|---|---|---|
| 0 | Check the coding the lens will rely on | Legislation branch | — |
| 1 | Severity and impact class on every row | Website session | 0 |
| 2 | Business view: severity in the summary and the journey | Website session | 1 |
| 3 | Source hover and links to the provision | Both | — |
| 4 | Pain points ranked on version 2 | Website session | 1, 3 |
| 5 | The same rule across states | Both | 1; owner to unshelve (E-161) |
| 6 | Fees, waiting times, renewal and penalties | Both | ABLIS |

### Phase 0: check the coding (legislation branch)

- **Audit triggers.** Find each requirement coded `entry` that does not have to be met before trading starts. Heritage works and the NSW child employment authority were fixed on 15 November 2026. Candidates still to check include employer duties and duties tied to one activity.
- **Audit reach.** Find each reach part with no `condition` or `activities` where the law binds only businesses doing something. These overstate "every business".
- **Record thresholds** with value, unit and date wherever the law states them (17 do so far).
- **List kinds the schema cannot express.** Requirements have no kind for a cap or an ownership limit, though register items do (5 points). The NT pharmacy ownership limit is coded as a licence for now. This is asked of the website session.
- **Output:** a short audit list in `docs/plan_legislation_links.md`, with the fixes made in the requirement files.

### Phase 1: severity and impact class on every row (website session)

- In "Its requirements", each law shows:
  - its severity band and score, with its 3 parts (kind, when, whom);
  - its impact class;
  - its evidence steps.

  Use the same functions as the levers page (`register/severity.py`, `menu/exposure.py`), so the two pages can't disagree.
- Sort rows by class, then severity, then businesses reached, as the levers page does. Drop the sort on the total of marks.
- Keep the effect table's columns of marks by market position, labelled as the judgement layer. The 8-driver profile opens on request.
- Tests: recompute each row's score and class from the requirement file, as `tests/test_registerdata.py` does.

### Phase 2: the business's view (website session)

- **Summary at the top:** how many laws bind every business in the industry in that state, and how many of them score high. Add how many must be met before trading starts (the "before you can open" count).
- **Exposure within the industry.** Where a law binds only businesses doing an activity, say so ("only those that tow vehicles"), and don't count it as binding every business.
- **The journey view** (start up, first employee, grow, operate) is coloured by severity, not by the marks.
- Tests: recompute the summary counts for a few industries and states.

### Phase 3: source hover and links to the provision (both)

The lens links "the record" to the requirement's JSON file on GitHub. The register is stored as one JSON file per item, and no page shows a single item. Register data now shows every item as a row, so the lens can link there instead.

Each requirement already holds, for every claim, the law's address, the provision (such as s 15), the exact words quoted, the version and how it was checked (3,133 quotes; all 686 main sources are quoted). That is enough for a hover card and a link to the provision.

- **Legislation branch:** add a script that writes `data/processed/legislation/source_links.csv`, one link per source. The link type depends on the register:
  - **Section anchors**, checked on 15 November 2026:
    - Queensland: `#sec.52`, 47 main sources;
    - Tasmania: `#GS6@EN`, or `#GS6@Gs1@EN` for a subsection, 44 main sources.

    NSW's register uses the same system but refuses automated requests, so check its `#sec.15` form in a browser (55 main sources).
  - **Text fragments** (`#:~:text=`) for other web pages: Commonwealth legislation (196), modern awards (122) and ABLIS (16). Current Chrome, Edge, Safari and Firefox scroll to and highlight the quoted words. The Federal Register of Legislation builds its pages in the browser, so test that a fragment lands.
  - **Page numbers** (`#page=N`) for PDFs:
    - ACT and NT, 78 main sources; the page number is read from the saved text;
    - Victoria (32) only once each source records the authorised PDF's address (it now cites the in-force page).
  - **No link to the provision** for WA (Word documents, 44) and SA (RTF documents, 41). Link to the law's register page; the hover still shows the quote.
- **Website session:** a hover card (and a tap card on a phone) on each law and each claim. It shows the quote, the provision, the version, how it was checked and "Open at s 15". Point "the record" link at the row on Register data.
- Tests: every link in `source_links.csv` belongs to its source's law, and each anchor matches the provision.

### Phase 4: pain points on version 2 (website session)

- Rank pain points by impact class and severity, then by overlap between bodies (methods rule 13). This follows the owner's decision that the register is the source of truth once the data is in; reviews support a point and don't rank it.
- Each pain card quotes and links the law through the Phase 3 hover. This meets the owner's item "register sources on the pain-point cards".

### Phase 5: the same rule across states (both; shelved)

Comparisons between states are shelved (E-161). When the owner unshelves them, the D-4c data supports them directly. For example, conveyancers are licensed in WA, Tasmania and the NT, registered in SA (lower severity), and have no scheme in Queensland or the ACT.

- **Legislation branch:** fill the to-draft and blocked gaps first (12 and 24 after D-4c), so a missing state means "no such law" rather than "not yet searched".
- **Website session:** show each family's severity by state on the Across states panel, with the gap status where there is no requirement.

### Phase 6: fees, waiting times, renewal and penalties (both; with ABLIS)

These are in the plan for version 2 but wait on the ABLIS key. The legislation branch codes penalties from the quoted provisions where the text states them (some quotes already include the maximum penalty). The website session adds them to severity once the owner settles their weights.

## Wording on the page

Follow the version 2 vocabulary:

- "Rule" and "Change", never "layer";
- the 4 class names;
- "the marks" for the judgement layer.

Website text follows the house-style skill.
