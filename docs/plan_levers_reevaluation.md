# Plan: re-evaluating Legislative levers under framework version 2.0

*15 November 2026. Drafted by Claude Code on the legislation branch (`claude/pensive-bell-wgm7ks`) for the owner. Nothing in this plan has been built. Figures were computed on 15 November 2026 from `main` at PR [#33](https://github.com/jabthebeer/Competition-in-Australia-analysis/pull/33), using the levers page's own data (`build_payload` in `alicia/src/alicia/menu/explorer.py`).*

## 1. What version 2.0 already did

The website session adopted framework version 2.0 on 14 November 2026 (DECISIONS E-184, E-185; [plan](plan_policy_tool.md)).

- **Severity:** each rule is scored from its coded kind, when it bites and whom it binds.
- **Exposure:** the businesses each rule reaches, counted from ABS data.
- **Impact classes:** 4 of them.
- **Evidence steps:** law named, law quoted, coded, counted.
- **Rules and changes:** each item is a rule or a change.
- **Purpose:** each regime has one.

It coded the 102 laws and policies that apply today and weigh on productivity in `regulation-register/rule-coding.json`. The marks are unchanged and stay at version 1.0.

So the levers page already ranks rules under version 2.0. Re-evaluating them means checking and completing what that first pass drafted, not starting again.

## 2. Where the register items stand

| Measure | Count | Gap |
|---|---|---|
| Register items | 255 | |
| Rules: existing settings | 55 | |
| Rules: reforms in force that added a restriction | 47 | Marked against what they replaced, not against no rule (the version 1.0 counterfactual), so some marks may capture only the increase |
| Rules: non-legislative barriers | 7 | No law to code; classed from their marks |
| Changes (reforms not counted as rules) | 144 | **127 link to no rule**, so they cannot sit under one |
| No longer in force | 2 | |
| Rules coded | 102 of 102 laws | Coded from each item's own summary, not from quoted law; not yet checked |
| Rules with the "law quoted" step | 0 of 109 | The page sets it to false for every register item: items hold no quote of their obligation |
| Laws with a link to the official register | 97 of 248 | **151 laws have none** (79 of them rules), most of them state laws |
| Rules with no regime, so no purpose | 19 | 7 state transfer duties, 7 insurance duties, foreign investment screening, Australia Post's reserved services, sustainability reporting, the Port of Melbourne lease, non-compete clauses |
| Rules naming industries only by division, or none | 16 and 12 | Exposure is coarse or economy-wide by default |
| Rules counted as an upper bound ("up to") | 28 | They bind only businesses doing an activity |
| Requirements citing the same Act as an item they don't name | 29 | Some are probably the same rule listed twice among the biggest barriers |
| Impact classes of register-item rules | 1 Severe, 10 Major (wide), 50 Major (narrow), 48 Minor | Of the 61 Severe or Major, the marks' confidence is high for 8, medium for 41, low for 12 |

Requirements (537) are in better shape. All are coded in their own files and 398 are quoted word for word. 49 are not classed because their marks add to zero.

## 3. Phases

Each phase ends in a pull request, with `alicia validate`, `pytest` and `ruff` passing after a merge from `main` ([before you push](notes_for_other_branches.md)). Decision rows take E-162 to E-179.

### Who does what

| Party | Work |
|---|---|
| This branch | Records, requirements, families, regimes and bodies |
| Website session | Schema, `severity.py`, the pages and the format of `rule-coding.json` |
| Owner | The decisions in section 4 |

| # | Phase | Who | Scope | Depends on |
|---|---|---|---|---|
| 1 | Settle the method | Owner | The 5 decisions in section 4 | |
| 2 | Put every change under its rule | This branch; one field from the website session | 144 changes, 47 reform rules | 1 |
| 3 | Quote and check each rule's coding | This branch; one change from the website session | 102 coded rules; 151 law links | 1 |
| 4 | Count each rule once, and give it a regime | This branch | 29 candidate pairs; 19 rules | Alongside 2 and 3 |
| 5 | Sharpen exposure | This branch | 28 coarse rules; 28 upper bounds | 3 |
| 6 | Fill gaps where version 2 scores highest | This branch, with the state branches | Caps, exclusive rights, bans, ownership limits, price controls | 3 |
| 7 | Re-mark, review and publish | This branch; owner's spot check | Only what phases 2 to 6 changed | Each phase |

### Phase 2. Put every change under its rule

**Sort each of the 144 changes into one of 3 cases:**

1. It changed a rule already in the register (a setting, a requirement or a reform rule). Link it.
2. It changed a rule that applies today but is not in the register. Add that rule as an existing setting if it weighs on productivity, with marks against the same market without it. Otherwise record why not.
3. It removed a rule outright. It has no rule to sit under, so it stays in the history as a rule removed.

**Sort each of the 47 reforms counted as rules:**

- **It created the restriction.** Its marks are already against no rule, so they stand.
- **It tightened a restriction that was already there.** Its marks capture only the increase, and decision 1 applies.

Check these first, without assuming the answer:

- the 7 adoptions of the 2022 building code;
- the 8 transfers to the NDIS Commission;
- coastal trading (2012);
- the pharmacy location rules (2018);
- Queensland pharmacy ownership (2025);
- the vaping reforms (2024).

**Output and check:**

- **Output:** each change linked to its rule, or marked as removing one.
- **Check:** a test that every change does one or the other.
- **Today's links:** only families and a requirement's `records`. They join 17 changes.

### Phase 3. Quote and check each rule's coding

For each of the 102 coded rules:

- find its operating provision in the official register and quote it word for word, with a pinpoint;
- check its kind, when it bites and whom it binds against that quote;
- record any threshold with its value, unit, date and trigger;
- record the maximum penalty where the provision states it, ready for when the schema scores penalties.

Severe and Major rules come first (56), then Minor (46).

**Where the quote goes (decision 3).** The recommended vehicle is a requirement file nested in the item (`records: [item id]`). It already carries quoted sources, kind, triggers and reach, so it needs no schema change. The website session then lets an item reach "law quoted", and read its severity, through that nested requirement.

**Law links.** At the same time, add official-register links to the 151 laws without one, rules first.

| Source | How |
|---|---|
| Commonwealth | The Federal Register of Legislation API |
| Qld, Tas, ACT, WA, NT and Vic | The toolkit's state adapters |
| NSW and SA | Search results, marked unverified, because their sites refused connections from this environment |

**Coding corrections.** Corrections to entries in `rule-coding.json` follow decision 4.

### Phase 4. Count each rule once, and give it a regime

**Pairs.** Confirm each of the 29 requirements that cite an item's Act without naming the item.

- **Probably the same rule listed twice:** the coastal trading licence and the 2012 coastal trading reform; foreign investment notification and screening; customs duty and import tariffs; the state builder licences and each state's occupational licensing setting.
- **Probably not:** some only share an umbrella Act, such as the industry codes under the Competition and Consumer Act.

Nest the true pairs through `records`, so each rule is ranked once.

**Regimes.** Give the 19 rules that lack one a regime: state transfer and insurance duties, foreign investment, postal services and sustainability reporting. Each regime needs a quoted basis, and an entry in `regime-purposes.json`.

### Phase 5. Sharpen exposure

| Rule | Fix |
|---|---|
| The 16 rules that name only a division, and the 12 that name no industry | Narrow each to the classes its law names, using the phase 3 quote |
| The 28 upper bounds | Check that each states its condition or activity |
| Rules near the 25% line between wide and narrow | Recheck them |

Knock-on exposure from the input–output tables, and licensed workers from occupation by industry, stay with the website session (inputs 1 and 5 in the [policy-tool plan](plan_policy_tool.md)).

### Phase 6. Fill gaps where version 2 scores highest

The ranking can only rank the rules in the register, and the register follows what reviews have written about (policy-tool plan, findings 1 and 6). Screen the catalogues already ingested (every Commonwealth Act and instrument, and the state catalogues) for the kinds that score most:

- caps on numbers;
- exclusive rights;
- bans;
- ownership limits;
- price controls.

Draft those found as quoted requirements. Check [`plan_states.md`](plan_states.md) and the state branches first, so nothing is drafted twice.

Guidance that is enforced as if it were law ([scoping note](scoping_regulatory_guidance.md), P-4) could later be coded as a standard here. It is not in this phase.

### Phase 7. Re-mark, review and publish

- **Re-mark only what phases 2 to 6 changed:** new settings, and reform rules re-based under decision 1. Assessments keep `"framework": "1.0"`.
- **Zero totals:** confirm that the 49 requirements whose marks add to zero are neutral.
- **Rebuild and check:** rebuild the generated files, and check the new rows on Register data.
- **Write up:** a short methods note and one decision row for each phase.
- **Owner's spot check:** a sample of about 20 rules, Severe and Major first. The register is checked by an AI process, not a person.

## 4. Decisions for the owner

| # | Question | Recommended |
|---|---|---|
| 1 | A reform that tightened an existing restriction: add the standing rule as a setting and make the reform its change, or re-mark the reform against no rule? | Add the standing rule. It keeps one counterfactual for each kind of item |
| 2 | How a change names its rule: an explicit field from the website session, or reuse families for now? | An explicit field. Families mean one policy across governments, and using them for links would blur that |
| 3 | Where a register item's quoted obligation lives: in a nested requirement, or in new fields in `rule-coding.json`? | A nested requirement. It needs no schema change |
| 4 | May this branch correct existing entries in `rule-coding.json`, or should it send the corrections to the website session? | Send a list, unless the owner says otherwise. The file is the website session's |
| 5 | Phase 6 scope: only the highest-scoring kinds, or every kind? | The highest-scoring kinds. They decide the top of the ranking |

## 5. Limits

- **Coded, not verified.** Severity and the classes rest on coding drafted by AI-assisted desk research. Phase 3 checks it against the law, but no person has reviewed it.
- **Not scored yet.** Fees, waiting times and renewal periods wait on ABLIS. Penalties can be recorded from the text now, but score nothing until the schema takes them.
- **No comparing states.** State coverage is uneven: 306 Commonwealth requirements against 21 to 56 per state. States are not compared or ranked until it is even (E-161).
- **Not an estimate.** An impact class describes a rule's kind and reach. It does not estimate its effect.
