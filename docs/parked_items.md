# Parked items

Work the owner has deliberately set aside, with when to raise it again. Claude Code checks this list when a phase in the current plan closes and reminds the owner of any item whose trigger has been reached.

| # | Parked on | Item | Why parked | Raise again when | Status |
|---|---|---|---|---|---|
| P-1 | 22 Oct 2026 | **Literature review for each register record.** For every law in `regulation-register/records/`, review the published evidence for and against the hypothesised effect on competition and productivity (the record's `direction`, `direction_rationale` and `channels`), and record the verdict and sources against the record | The owner paused the retrospective analysis: each law would need its own identification strategy. A literature review is the cheaper way to test the hypotheses | **When the policy-costing plan closes** ([`forward_plan_policy_costing.md`](forward_plan_policy_costing.md), after Phase P7), or earlier if the owner asks | Parked |
| P-2 | 29 Oct 2026 | **Recommendations section.** For register items, and for the drivers that weigh most on productivity, set out reform recommendations based on best practice in the Australian and international literature (for example Productivity Commission, Competition Review and OECD work, and evaluations of comparable reforms abroad), each tied to the items and responsible departments it concerns | The owner wants it after the responsibility and timeline work (E-94) is done | **When the owner asks**: after the responsibility tags and timelines (E-94) are reviewed | Parked |

## Notes for P-1, when it is picked up

- **Who:** Cowork does the literature synthesis (CLAUDE.md division of labour). Claude Code supplies:
  - one review sheet per record, from the register;
  - a schema field for the verdict and sources;
  - the validation.
- **Output:** each review should say whether the evidence supports, contradicts or is silent on the hypothesised direction, citing studies with exact quotes. Nothing is to be fabricated.
- **Retrospective work it would feed:**
  - the 12 provisional evaluations ([`due_diligence.md`](due_diligence.md));
  - the "similar past changes" panel in the policy-costing tab (§6.9 of the plan).

## Notes for P-2, when it is picked up

- **Who:** Cowork synthesises the literature and drafts the recommendations (CLAUDE.md division of labour). Claude Code supplies:
  - a schema for recommendations: the items, drivers and responsible bodies each one concerns, with sources;
  - validation;
  - a section on the menu (or its own page) that links each recommendation to its items.
- **Builds on:**
  - the framework marks (which drivers weigh most);
  - the `responsible` tags (who would act);
  - the timelines (what has already been tried and reversed, such as the lockout laws).
- **Nothing to be fabricated:** every recommendation cites the studies or reviews it rests on, with exact quotes.
