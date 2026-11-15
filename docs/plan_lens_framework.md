# Plan: framework version 2 on the Industry lens

*15 November 2026. Written at the owner's request. The owner decides who builds each phase.*

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

| Phase | What | Status | Depends on |
|---|---|---|---|
| 0 | Check the coding the lens will rely on | Under way in another session | — |
| 1 | Severity and impact class on every row | To do | 0 |
| 2 | Business view: severity in the summary and the journey | To do | 1 |
| 3 | Source hover and links to the provision | Built 15 November 2026 (E-163) | — |
| 4 | Pain points ranked on version 2 | To do | 1, 3 |
| 5 | The same rule across states | Shelved (E-161) | 1; owner to unshelve |
| 6 | Fees, waiting times, renewal and penalties | Waits on ABLIS | ABLIS |

### Phase 0: check the coding

- **Audit triggers.** Find each requirement coded `entry` that does not have to be met before trading starts. Heritage works and the NSW child employment authority were fixed on 15 November 2026. Candidates still to check include employer duties and duties tied to one activity.
- **Audit reach.** Find each reach part with no `condition` or `activities` where the law binds only businesses doing something. These overstate "every business".
- **Record thresholds** with value, unit and date wherever the law states them (17 do so far).
- **List kinds the schema cannot express.** Requirements have no kind for a cap or an ownership limit, though register items do (5 points). The NT pharmacy ownership limit is coded as a licence for now.
- **Output:** a short audit list, with the fixes made in the requirement files.

### Phase 1: severity and impact class on every row

- In "Its requirements", each law shows:
  - its severity band and score, with its 3 parts (kind, when, whom);
  - its impact class;
  - its evidence steps.

  Use the same functions as the levers page (`register/severity.py`, `menu/exposure.py`), so the two pages can't disagree.
- Sort rows by class, then severity, then businesses reached, as the levers page does. Drop the sort on the total of marks.
- Keep the effect table's columns of marks by market position, labelled as the judgement layer. The 8-driver profile opens on request.
- Tests: recompute each row's score and class from the requirement file, as `tests/test_registerdata.py` does.

### Phase 2: the business's view

- **Summary at the top:** how many laws bind every business in the industry in that state, and how many of them score high. Add how many must be met before trading starts (the "before you can open" count).
- **Exposure within the industry.** Where a law binds only businesses doing an activity, say so ("only those that tow vehicles"), and don't count it as binding every business.
- **The journey view** (start up, first employee, grow, operate) is coloured by severity, not by the marks.
- Tests: recompute the summary counts for a few industries and states.

### Phase 3: source hover and links to the provision

Built on 15 November 2026 (E-163). A law's name opens the law at the provision quoted and, on hover or keyboard focus, shows a preview of the words quoted. A "What the law says" button opens a card with every quoted source, for touch and keyboard. "How it is coded" opens the item's row on Register data instead of its JSON file. The link rules, and which were tested in a browser, are in the [Industry lens methods note](industry_lens.md).

### Phase 4: pain points on version 2

- Rank pain points by impact class and severity, then by overlap between bodies (methods rule 13). This follows the owner's decision that the register is the source of truth once the data is in; reviews support a point and don't rank it.
- Each pain card quotes and links the law through the Phase 3 hover. This meets the owner's item "register sources on the pain-point cards".

### Phase 5: the same rule across states

Comparisons between states are shelved (E-161). When the owner unshelves them, the D-4c data supports them directly. For example, conveyancers are licensed in WA, Tasmania and the NT, registered in SA (lower severity), and have no scheme in Queensland or the ACT.

- Fill the to-draft and blocked gaps first (12 and 24 after D-4c), so a missing state means "no such law" rather than "not yet searched".
- Show each family's severity by state on the Across states panel, with the gap status where there is no requirement.

### Phase 6: fees, waiting times, renewal and penalties

These are in the plan for version 2 but wait on the ABLIS key. Penalties can be coded from the quoted provisions where the text states them (some quotes already include the maximum penalty), and added to severity once the owner settles their weights.

## Wording on the page

Follow the version 2 vocabulary:

- "Rule" and "Change", never "layer";
- the 4 class names;
- "the marks" for the judgement layer.

Website text follows the house-style skill.
