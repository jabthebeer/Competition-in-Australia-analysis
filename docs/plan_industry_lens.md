# Plan: the ALICIA Industry lens page

*Draft for the owner's approval, 6 November 2026. Nothing is built until it is approved. Framework assessments only; no econometrics (E-87, E-113).*

## 1. What the page does

The reader picks an ANZSIC 2006 class (any of the 506, searchable by division → subdivision → group → class, with ABS names) and a state or territory. The page then reads as the first-person view of a business in that class starting up in that state, stage by stage:

**Start** (entry, non-employing) → **1–4** → **5–19** → **20–199** → **200+** → **Exit**

Each stage has two panels:

- **Structural view**: ABS figures for businesses like yours in that stage, in this state, each labelled with the level it is published at (class, subdivision, division; state or Australia) and its year.
- **Legislative view**: what you must do at that stage, what triggers it, who you deal with, how this state's version differs, and the framework assessment of the register item behind it.

Thresholds that don't sit on a band edge (GST turnover, state payroll tax, employee-count tests) appear as **markers** within a stage. Two badges show what cuts across: **Every industry** (a cross-cutting regime) and **Same in every state** or **Differs by state** (with this state's value and the range across states). An **All states** view sets each requirement and threshold side by side for the chosen class, so barriers common to every state stand out.

The first-person text is generated from structured fields (the threshold table, regime descriptions, register summaries) with fixed sentence templates, such as "To start trading you must …". No text is written by hand for individual classes, and nothing is filled in where a field is empty: the page says "not yet sourced" or "not yet assessed".

Deep links: `industry-lens.html#class=4511&state=VIC`. The legislation menu's class view links to the lens. The landing page's card goes live automatically when the build writes the page (`growth.landing`).

## 2. What exists, and what the survey found

| Finding | Consequence for the build |
|---|---|
| The stitched state panel (`data/processed/abs_cabee/`) sums 1–4 and 5–19 into **1–19**. CABEE cube 2 publishes them separately from the Jul 2018–Jun 2022 release on. | A new processed file keeps the five bands apart: 2021-22 to 2024-25 from final vintages. Earlier years show 1–19 and say so. The existing panel is not changed. |
| **11 classes have no current CABEE counts.** 9 are never published: 7711, 7713, 9540, 9551, 9552, 9559, 9601–9603. 6210 Central Banking stops after 2008-09, and 6330 Superannuation Funds is missing from the latest release. Three codes (0310, 0671, 5229) appear only in 2011-12. | These classes still get the legislative view, with a note that the ABS publishes no counts for them. The reason (CABEE's market-sector scope) is to be confirmed in the ABS explanatory notes. |
| The repo doesn't use these ABS cubes yet: **cube 3** (class × state × turnover range), **cubes 4–5** (survival of businesses and of entries, by state × subdivision × employment range) and **cube 1 Tables 14 and 16** (changes in employment range for surviving businesses; survival of entries by range; Australia, all industries). | They are downloaded with manifests and recorded in `data/SOURCES.md`. They give the turnover markers real counts and give survival at each stage at subdivision × state level. |
| **Movement between bands is partly public.** The ABS publishes *net* movement of surviving businesses for each band at class × state × year (already in the panel as `balancing`). It publishes *gross* band-to-band changes only for Australia, all industries combined (Table 14). | The known-limit text (§8) is worded to match: gross moves between bands by industry or state need BLADE. Net movement and the national matrix are shown, clearly labelled. Whether net movement also picks up businesses that change class or state is to be confirmed with the ABS. |
| **Regimes record no triggers or thresholds.** The payroll tax records say "Thresholds and rates change often and are not recorded here". | The stage-and-threshold table (§5) is new. |
| **State versions are uneven.** Payroll tax, planning, WHS, electrical licensing and several more regimes have a register record in every state. Workers' compensation, agvet chemicals, fisheries, native vegetation and 13 others have none. | The state view shows the state's own record where there is one, and its threshold-table entry otherwise. The gaps are listed on the page and in the methods note. |
| **No regime covers several size-triggered or exit obligations**, such as company financial reporting, privacy, modern slavery, gender equality reporting, payment times reporting, and insolvency or closing a business. | Without them, the 200+ and Exit stages would be thin. See Q2. |

## 3. Stages

| Stage | ABS band (CABEE) | Structural figures | Legislative triggers (types; values come from the table) |
|---|---|---|---|
| Start | Non-employing; entries in every band | Businesses, entries, entry rate; turnover ranges (cube 3) | On entry (ABN, licences, premises approval); turnover tests (e.g. GST) |
| 1–4 | 1–4 employees | Businesses, entries, exits, net movement; survival of entries | On first employee (PAYG withholding, super, workers' compensation, awards) |
| 5–19 | 5–19 | As above | Employee-count tests; payroll tax thresholds (where they fall here) |
| 20–199 | 20–199 | As above | Payroll tax (where it falls here); employee-count and turnover tests |
| 200+ | 200+ | As above; concentration and mark-ups (division, Australia; context only) | Revenue, asset and employee tests (reporting obligations, Q2) |
| Exit | Exits by band | Exits, exit rate; survival to 1–3 years | Closing, deregistration, insolvency (Q2) |

**Placing markers.** An employee-count threshold goes in the band that contains it. A payroll or turnover threshold is placed by an indicative headcount, worked out from the ABS figure the marker names (Q3). The marker shows the official value, the conversion and the word *indicative*.

## 4. Structural view: figures and their levels

| Figure | Source | Finest level published | Years |
|---|---|---|---|
| Businesses operating, entries, exits, and entry and exit rates by band | CABEE cube 2 | Class × state | 2007-08 to 2024-25 (1–4 and 5–19 separately from 2021-22) |
| Net movement of surviving businesses by band | CABEE cube 2 | Class × state | 2007-08 to 2024-25 |
| Businesses by turnover range | CABEE cube 3 | Class × state | Latest release (years to confirm) |
| Survival of entries and of businesses by band | CABEE cubes 4–5 | Subdivision × state | Latest release |
| Changes in employment range for surviving businesses (gross) | CABEE cube 1, Table 14 | Australia, all industries | June 2021 to June 2025 |
| Employment, value added, wages and sales by employment range | Australian Industry, 8155.0 Table 5 | Division × Australia (its 0–4 band pools non-employing and 1–4 businesses) | 2022-23 to 2024-25 |
| Businesses hampered by regulation | Business Conditions Survey | Division; by size, Australia | 2024-25 |
| Concentration and mark-ups | RBA, Hambur and Freestone (2025), from BLADE | Division × Australia | End 2019 and 2017 |

Rules:

- Every figure states its level and year.
- Counts are always shown. Rates are left out where fewer than 20 businesses operated at the start of the year (a default you can change), because the ABS perturbs small cells.
- Figures at a coarser level than the class say so on the figure itself, not only in a footnote.

## 5. The stage-and-threshold table (new)

**Where:** `regulation-register/thresholds/<regime>.json`, with a pydantic model in `alicia/src/alicia/register/` and a generated `regulation-register/schema/threshold.schema.json`. `alicia validate` checks it, and a flat copy goes to `data/processed/industry_lens/thresholds.csv` for Cowork.

**One row per requirement × jurisdiction:**

| Field | Content |
|---|---|
| `regime`, `requirement` | Regime id; what the business must do, in plain English |
| `trigger` | `entry`, `first-employee`, `employees`, `payroll`, `turnover`, `revenue`, `assets`, `activity` or `exit` |
| `test`, `value`, `unit` | e.g. `>=`, the value, `AUD per year` or `employees`; null for `entry` and `activity` |
| `jurisdiction` | CTH or a state or territory |
| `same_everywhere` | Derived: one national value, or values that differ |
| `stage` | Derived from the trigger and value (§3) |
| `source` | Publisher, title, URL, locator, verbatim quote, date accessed, and how it was checked |
| `as_at`, `notes` | Date the value applies (Q4); grouping, indexation or exemptions worth knowing |

**Rules:**

- Every value comes from an official source: a legislation register, revenue office, ATO, Fair Work Ombudsman, business.gov.au or the regulator.
- No value is estimated or carried over from memory. If a value can't be sourced, the row says "not yet sourced".
- Sites that block automated requests (NSW and SA, as the fact-check found) are handled as Q5 decides.

**Batches** (each committed separately):

- **A.** The 7 cross-cutting regimes in all 9 jurisdictions (about 60–90 rows). These supply most of the markers.
- **B.** Entry requirements of the 54 sector regimes, in each state where they apply.
- **C.** Upper-stage and exit obligations, after Q2.

## 6. Build steps

1. **Data.**
   - Download cube 2 again, using the URLs and SHA-256 hashes in its manifest, and keep 1–4 and 5–19 apart.
   - Add cube 3, cubes 4–5 and cube 1 Tables 14 and 16.
   - Write everything to `data/processed/industry_lens/`, with manifests and `data/SOURCES.md` rows.
2. **Threshold table.** Write the schema, then batch A, then run `alicia validate`.
3. **Page.**
   - Payload builder in `alicia/src/alicia/menu/lens.py`, template in `templates/industry-lens.html`, called from `build_site`.
   - Charts:
     - businesses per band, with the markers;
     - entry, exit and net movement by band;
     - counts by band over time;
     - turnover ranges.
   - Excel download of the stage table and the threshold rows for the chosen class and state.
   - Added to the site nav after "The state of competition".
4. **Size.** The page is one self-contained file, like the others. If the payload passes about 5 MB, the data moves into one file per division, loaded on demand. Opening from `file://` would then stop working, so I'll tell you before doing that.
5. **Batches B and C.**
6. **Checks** (§7).
7. **Write-up.**
   - A short methods note, `docs/methods_industry_lens.md`: figures, levels and rules, as tables.
   - DECISIONS E-114 (this plan, with your answers) and E-115 (the build).
   - `data/SOURCES.md` and the register README status line.

## 7. Checks before publishing

- **Every number recalculated without the page code.**
  - A standalone script reads the raw ABS workbooks and the threshold files, recomputes every number in the payload and lists any that differ.
  - CLAUDE.md prefers R for this, but R isn't installed in this container. I'll install it if the package mirrors allow; otherwise the script is plain Python that doesn't import `alicia`.
  - The rendered page is then read in a browser (Playwright) for a sample of classes in all states.
- **CABEE consistency.** The five-band file sums to the stitched 1–19 and total bands, within perturbation. The class × state cells add up to the published totals.
- **Thresholds.** Each value is fetched a second time and its quote matched. Values that can't be checked are listed.
- **Tests.**
  - A new `alicia/tests/test_lens.py`.
  - `test_site.py` updated: one "Coming soon" card, not two.
  - Phone width with no sideways scrolling; light and dark themes.

## 8. Limits stated on the page

- **Movement between sizes:** "Public data counts the businesses in each size band, and the net number of surviving businesses moving into or out of it. It doesn't show how many moved up or down. For Australia as a whole, the ABS publishes those moves for all industries combined; by industry or state they need the ABS's confidential firm data (BLADE)."
- **Counts are by main state.** A business that trades in several states is counted once, in its main state.
- **Scope.** CABEE counts actively trading businesses with an ABN. Whether it covers only GST-registered businesses is to be confirmed. If it does, the Start stage undercounts sole traders below the GST threshold.
- **Dates.** Thresholds are as at their `as_at` date, while CABEE runs to 2024-25. Markers placed by conversion are indicative.
- **Regimes** describe a typical business in the class; ABLIS licence counts aren't used. All register content is an AI-assisted draft, not yet checked by a person.

## 9. Questions for you

| # | Question | My recommendation |
|---|---|---|
| Q1 | Show the ABS's net movement by band (class × state) and its national band-to-band table, with the wording in §8? | Yes. It is public and closer to "growth between stages" than counts alone. |
| Q2 | For the 200+ and Exit stages, add two cross-cutting regimes, **Company reporting and disclosure** and **Insolvency and closing a business**? This changes every class's regime count in `class_profiles.csv` and the complexity note. | Yes. Otherwise those stages have little legislative content. |
| Q3 | Place payroll and turnover markers by an indicative headcount? Payroll ÷ ABS average annual earnings (EEH, by division); turnover ÷ sales per person employed (Australian Industry, by subdivision). | Yes, labelled indicative, with the arithmetic shown. |
| Q4 | Which date should threshold values refer to? | Values in force on the date checked (a business starting now). The value in force in 2024-25 is added only where it differs and matters for the CABEE years. |
| Q5 | Where an official site blocks automated checks (NSW, SA): you check those values by hand, or I use another official source (the Act on the state's register, a revenue ruling PDF, budget papers) and flag them? | The second, flagged "checked from <source>", with a list for you to spot-check. |
