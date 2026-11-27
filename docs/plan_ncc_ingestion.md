# Plan: ingesting National Construction Code data into ALICIA

Plan for the owner, 26 November 2026. **Status: draft, for approval.** Nothing is built yet. Written by Claude Code on branch `claude/project-thread-pg3toc`; it touches no register file, so it cannot clash with PR [#41](https://github.com/jabthebeer/Competition-in-Australia-analysis/pull/41).

> **Source check.** The cloud environment's network policy blocks `abcb.gov.au`, `ncc.abcb.gov.au`, `oia.pmc.gov.au` and `data.gov.au`, so no Australian Building Codes Board (ABCB) page was read directly for this plan. What section 2 says about the code comes from web search results that quote those pages, plus state government pages. Each fact is marked **(to verify)** until phase N0 reads the page itself. No figure in this plan should be quoted until then.

## 1. How the NCC appears in ALICIA now

| Where | What | Gap |
|---|---|---|
| `regulation-register/records/*-ncc-2022-*.json` (8 records, family `ncc-2022-adoption`) | One reform per state: adoption of the NCC 2022 residential energy efficiency (7-star) and livable housing provisions, with its primary commencement, marks (burden −1, market integration −1) and the bodies responsible | Instruments are generic ("NCC 2022 … as adopted in Victoria") with no register id or URL, except NSW (BASIX SEPP, dates not checked). Queensland's livable housing date is "not confirmed". Only one commencement each; condensation, commercial energy efficiency and the transition periods are not recorded. No `history` |
| `families.json` | "Inconsistent adoption of the 2022 building code standards" | Covers NCC 2022 only |
| `rule-coding.json` | All 8 coded `standard`, `operating`, `all` | None |
| `regimes/building-licensing-and-approvals.json` | ABCB sets rules; states vary the code; consistency `harmonised` | The "state variations" layer names no bodies and no source for how much states vary the code |
| `recommendations/building-code-net-benefit-test.json` | Independent review of building regulation; net-benefit test for code changes (PC 2025); progress notes the August 2025 pause on residential changes to mid-2029 | The pause is not a register event |
| `regulation-register/requirements/` | Builder, plumbing and electrical licences, home warranty insurance, building contracts, pool barriers, fire safety statements | **No requirement to build to the code.** The core obligation is absent from the Industry lens |
| `data/SOURCES.md` | No ABCB entry | Licence and access not recorded |

So the register holds one change (NCC 2022) and none of the standing obligation, the earlier or later editions, or the state variations.

## 2. What the ABCB publishes (to verify)

| Item | What the search results show | Use in ALICIA |
|---|---|---|
| **Volumes** | Volume One: Class 2 to 9 buildings (apartments, commercial, public). Volume Two: Class 1 and 10 (houses, sheds), with the ABCB Housing Provisions Standard from 2022. Volume Three: the Plumbing Code of Australia | Each volume maps to different ANZSIC classes (section 4, N3) |
| **Editions** | NCC 2016, 2019 (with Amendment 1), 2022 and 2025 online at `ncc.abcb.gov.au/editions/...`; 2022 PDFs at `abcb.gov.au/system/files/ncc/ncc2022-volume-one-20230501b.pdf` and similar | Edition-by-edition adoption table (N1) |
| **Adoption dates** | Page "NCC 2022 state and territory adoption dates", a table by state and provision (energy efficiency, condensation, livable housing), "correct as at 22 September 2023". National adoption 1 May 2023 with transitions. Each edition also has a "History of adoption" table, for which jurisdictions supplied NCC 2025 dates by 31 March 2026 (Treasury FOI 4242) | Main source for N1 and the records' commencements |
| **NCC 2025** | Preview 1 February 2026, final 1 May 2026; states may adopt from 1 May 2026. Reported: NSW, Queensland and SA from 1 May 2027; ACT from 1 May 2026 with a 6-month transition; Tasmania paused some measures; NT gazetted that NCC 2025 does not apply. Building ministers paused residential changes (except safety and quality) to mid-2029 | A new family `ncc-2025-adoption` and a `history` event for the pause |
| **State variations** | Each volume has a schedule of state and territory variations and additions (for example Queensland's in Schedule 7, carried into NCC 2025) | Variation counts by state and edition (N4) |
| **Impact analyses** | Decision RIS, NCC 2022 residential energy efficiency (September 2022; CIE cost-benefit analysis; also on the OIA site); RISs for livable housing and other changes listed under "Regulation impact statements" on `ncc.abcb.gov.au/resources` | Substantive compliance cost per dwelling for the costing work (section 5) |
| **Structured data** | None found: no API, CSV or dataset. The code is HTML and PDF; the adoption tables are HTML | ALICIA builds its own tables, each row quoting its page |
| **Licence** | ABCB FAQ: NCC 2022 "is now available under the Creative Commons Attribution 4.0 International Licence" and most ABCB material is CC BY 4.0. NCC 2022 was first CC BY-ND, later changed; NCC 2016 was CC BY-NC-ND 4.0. Logos and third-party material are excluded. Suggested attribution: "The National Construction Code 2022 was provided by the Australian Building Codes Board under the CC BY licence." | Quoting and deriving tables is allowed for 2022 and 2025 if confirmed. Record each edition's notice in `SOURCES.md`; treat 2016 (and 2019 until checked) as no-derivatives: quote only, no restructured text |

## 3. Principles

- Fit the current schema and folders exactly (`notes_for_other_branches.md`, "Keep to the current schema"). No new fields, no model changes. If a field is needed, write the request at the top of that file instead.
- Every date and quote is read from the official page (ABCB first, then the state's own adoption instrument or regulator), with a locator. Secondary sources (HIA, MBA) are leads only, as coding protocol rule 2 says.
- PDFs are cached under `data/raw/abcb/` but **not committed** (the volumes are tens of megabytes). A manifest with URL, date and SHA-256 is committed.
- The scripts are Python in `alicia/scripts/`, under the ALICIA exception in `CLAUDE.md`.
- Draft status throughout; nothing is marked reviewed.

## 4. Phases

| Phase | What | Files | Size |
|---|---|---|---|
| **N0. Access and licence** | Allow the hosts (section 6, question 1). Read the copyright notice of each edition and the ABCB copyright page; add an ABCB entry to `data/SOURCES.md`. Write `alicia/scripts/abcb_fetch.py` to cache the adoption pages, schedules and RIS PDFs with a manifest. Confirm or correct every "(to verify)" fact in section 2 | `data/SOURCES.md`, `data/raw/abcb/manifest.json`, script | Small |
| **N1. Adoption table** | One row per edition × jurisdiction × provision area (residential energy efficiency, condensation, livable housing, commercial energy efficiency, other) with: date applied, status (adopted, adopted with variation, deferred, not adopted), the instrument, the ABCB source and the state source, each with a quote | `data/processed/ncc/adoption.csv` | NCC 2019, 2022, 2025 × 9 jurisdictions |
| **N2. Register records** | (a) Fix the 8 `ncc-2022-adoption` records: real instruments with register ids (for example Queensland Development Code MP 4.1, the Victorian Building Regulations, the NSW BASIX SEPP), one commencement per provision with the competition-relevant one `primary`, Queensland's livable housing date confirmed or removed, `alicia dates` run. (b) Add family `ncc-2025-adoption`: one reform per jurisdiction, including deferrals and the NT's non-application (no commencement where not in force). (c) Add a `history` event "announced" for the 2025 pause on residential changes, linked from the recommendation's `progress`. (d) Update `families.json` summaries | `records/`, `families.json`, `rule-coding.json` entries for any new standing item | ~9 new, 8 edited |
| **N3. Requirements** | Add the missing standing obligation. Family `building-code-compliance`: one requirement per state, kind `standard`, "build to the NCC as adopted, with this state's variations", quoting the state law that adopts the code. Reach by volume: Volume Two to 3011; Volume One to 3019 and 3020; Volume Three to a separate family `plumbing-code-compliance` (3231). Consider `energy-rating-assessment` (NatHERS or BASIX certificate before approval) as a third family, trigger `entry` for each building. Link `records` to the adoption reforms so the lens does not list them twice. Marks reuse the existing records' marks. Log any state with no separate adopting provision in `requirement-gaps.json` | `requirements/<state>/`, `requirement-gaps.json`; rebuild `links.csv.gz` | 16 to 27 files |
| **N4. Variations measure** | From each edition's schedules, count each state's variations and additions by volume and part, and classify them (stricter, looser, administrative). This gives a measure of how far each state departs from the national code over time, a public-data indicator of the market-integration mark. It supports the family summaries, the regime's `consistency_note` and a chart | `data/processed/ncc/variations.csv`, a short methods note in `docs/` | Counts are mechanical; the classification needs care |
| **N5. Cost inputs** | Extract the RIS figures (section 5) into a quoted table | `data/processed/costing/ncc_ris.csv` | A few RISs |
| **N6. Checks and PR** | `uv run alicia validate`, `check_requirement_quotes.py`, `requirement_links.py`, `pytest -q`; site build and look at the Industry lens for 3011 in each state. One DECISIONS row per phase in a range the owner assigns | | |

Order: N0, then N1 and N2 together (N2 reads N1), then N3, N4 and N5 in any order. N2 and N3 touch the same folders as PR #41, so start them after #41 merges and merge `main` first.

## 5. Where the NCC feeds the compliance cost figure

The compliance cost plan ([thread](https://claude.ai/code/artifact/0ab7b54b-625e-4708-bde3-c43ba1d30489)) costs paperwork time only: hours × $91.54 × frequency × businesses bound. It says the cost of meeting a standard is not counted. The NCC is the clearest case where that cost dominates, and it is the one where official estimates exist:

1. **Substantive compliance cost per new dwelling.** The OIA framework counts substantive compliance costs as well as administrative ones (to verify against the RBM text already cached in `regulatory-burden-tool/data/`). The NCC 2022 energy efficiency Decision RIS and the livable housing RIS estimate the added construction cost per dwelling, by state and dwelling type. N5 extracts those with locators.
2. **Volume.** Multiply by new dwellings commenced by state (ABS *Building Activity*, cat. 8752.0, or *Building Approvals*, cat. 8731.0, via `readabs`; not yet in the repo, so add to `SOURCES.md`), for each state from the date it adopted (N1). The adoption dates also give the counterfactual: states that deferred or did not adopt bear no cost for that provision.
3. **Administrative part.** The energy-rating certificate (NatHERS or BASIX) is a paperwork cost per building that fits the other thread's formula directly, with its fee from the assessor market, if a public source exists.
4. **Keep the two apart.** Show substantive costs as a separate line, labelled as the RIS's own estimate (ex ante, not measured), so the paperwork figure keeps its meaning. RIS figures are national averages for some provisions; say where a state figure is not available.

The building requirement in N3 is the row the cost figure would attach to. Tell the compliance cost thread when N3 and N5 land.

## 6. Questions for the owner

1. **Network.** Allow `abcb.gov.au`, `ncc.abcb.gov.au`, `consultation.abcb.gov.au` and `oia.pmc.gov.au` in the legislation environment (Project settings, Cloud environment). Nothing in N0 to N5 can start without it.
2. **Scope of the code.** Recommended: one standing requirement per state for the whole code, plus reform records only for the changes the register is about (energy, livable housing, and later editions). The alternative, a requirement per NCC part (fire, structure, energy, access), would add about 100 files and duplicate a standard most builders meet through a certifier.
3. **NCC 2019 and earlier.** Recommended: adoption rows in N1 only, no register records, because the register's reforms start from changes with competition relevance and public data.
4. **Decision numbers.** This work needs a DECISIONS range (for example E-450 onwards).
