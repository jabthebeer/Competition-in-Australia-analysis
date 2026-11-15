# Plan for the states and territories (phase D)

*Part of the [legislation-links plan](plan_legislation_links.md), phase D. Drafted 12 November 2026, after the Commonwealth phase (E-143 to E-148). For the owner's approval before the first batch.*

## Goal

For each of the eight states and territories, record every requirement its laws place on businesses:
- Acts and their regulations, rules and orders;
- each state's version of the national model laws, such as work health and safety;
- state laws that councils administer, such as food business registration.

Each requirement gets what the Commonwealth ones have:
- the law's words quoted;
- its reach across the 506 industry classes;
- its triggers and thresholds;
- framework marks;
- the bodies that administer it, with any overlaps.

Councils' own local laws are phase E.

## Where we start

- **115 state requirements in 17 families.** Twelve families are in all eight jurisdictions, including payroll tax, workers' compensation, the WHS primary duty, food, liquor, builders, security and health practitioners. Five are partial.
- **20 council requirements:** outdoor dining, busking and filming permits in the capital cities.
- **22 logged gaps:**
  - 10 to draft;
  - 7 not found;
  - 3 blocked in Victoria;
  - 2 not searched.
- **Few regulator links:** only 25 of the 135 state and council requirements name a regulator.
- **Phase B's estimate:** about 3,000 state requirements (range 1,300 to 6,200) and about 56 hours in session (23 to 189). We will re-estimate once the catalogues measure the real scale.

## Where the law comes from

| Jurisdiction | List of laws in force | Law text | Limits |
|---|---|---|---|
| NSW | Legal corpus: 1,418 Acts, 798 instruments | Corpus copy | The register refuses automated requests. The text is as at 10 March 2025, and no open source for later changes has been found |
| Victoria | Register sitemap and in-force pages (allowed, with a 2-second delay) | The Acts the owner saved | The register's document server disallows automated fetching |
| Queensland | Corpus: 573 Acts, 427 instruments (the register's lists load by script, so they could not be read) | Register (current text) | The list is as at the corpus's scrape |
| WA | Corpus: 816 Acts, 748 instruments | Register Word documents (current) | None found |
| SA | Corpus: 572 Acts, 495 instruments | Corpus copy, updated from SA's fortnightly XML packages where they cover a law | The register refuses automated requests |
| Tasmania | Corpus: 862 Acts, 1,690 instruments | Register (current), corpus as fallback | None found |
| ACT | The register's in-force lists, saved from a browser by the owner (12 Nov 2026), because they are under `/results`, which robots.txt disallows | Register PDFs | The lists cannot be fetched automatically; a later refresh needs the owner to save them again |
| NT | Register lists | Register PDFs | Section numbers are lost when the PDFs are read as text, so locators use section headings |

The legal corpus is the Open Australian Legal Corpus (CC BY 4.0). Every quote cites the official register link, whatever copy it was read from.

## Method

The Commonwealth rules apply (methods rules 1 to 13). The changes for the states:

1. **A catalogue per jurisdiction.** Each lists every law in force, with the same columns as the Commonwealth catalogue: ID, name, year, triage, call, requirements and reason. Files: `data/processed/legislation/<state>_catalogue.csv`, metadata only.
2. **Title triage, then screening.**
   - Triage sets aside series that never oblige businesses directly, such as appropriations, commencement orders, land grants and naming orders.
   - Each remaining law gets a call: Y (creates a requirement), L (supports one) or N (no business obligation), each with a reason.
   - Laws with the strongest signals (licences, registrations, levies, duties) are screened first.
   - Calls are made from the law's text, not its title alone. The Commonwealth check found that title-only calls miss duties (E-144).
3. **Families before single states.** A requirement found in one state is looked for in all eight, so each family is complete or its gaps are logged (rule 12). Differences between states are recorded in each state's requirement.
4. **Who administers it, from the start.** Every new state requirement gets `administration` entries (rule 13):
   - the state regulator and department, quoted from the law and from the state's own administrative arrangements;
   - councils, where they administer it.

   Overlaps with the Commonwealth are recorded where they exist, such as WHS (Comcare and the state regulators), health practitioners (Ahpra and the national boards with state bodies) and food (FSANZ's standards, enforced by state food authorities and councils).
5. **Council-administered state permits count once.** A permit issued under a state Act counts as one state requirement, marked as council-administered, not one per council (rule 7).
6. **Checks in every batch:**
   - `alicia validate`;
   - every quote re-found in its source;
   - the tests;
   - the link and agency tables rebuilt;
   - a quality-check sample at the end of the phase, as in E-144.

   Everything stays a draft for the AI checking process (E-145).

## Batches

| Batch | What | Why first |
|---|---|---|
| **D-1** | Finish the 17 existing families. Draft the 10 to-draft gaps and search the 2 not yet searched. Link every existing state and council requirement to its regulator and department, with sources and overlaps | Quick, and it makes the agency counts reflect state agencies, not only Commonwealth ones |
| **D-2** | Build the eight catalogues, triage them, score them for signals, and re-estimate the scale | Measures the work before the bulk of it |
| **D-3** | Economy-wide state laws across all eight. Candidates for screening include long service leave, land tax, high-risk work and asbestos licences, dangerous goods storage, environment protection licences, retail leases and trading hours | Every class carries these; doing them family by family keeps states consistent |
| **D-4 to D-10** | Industry-specific laws, state by state, by division: NSW, then Queensland, WA, SA, Tasmania, the ACT and the NT. Victoria runs when the saved Acts are uploaded | NSW is the largest economy and its corpus copy is ready |
| **D-11** | Quality check of the state phase, gap log review, and an updated plan and estimate | As for the Commonwealth (E-144) |

## Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| S1 | The batch order above, starting with D-1? | Yes |
| S2 | Victoria: when can the saved Acts be uploaded, and where? | To `data/raw/vic_legislation/`, which is not committed. Until then, the Victorian catalogue is built from the register's listing pages, and Victorian drafts wait |
| S3 | NSW text is the corpus copy as at 10 March 2025. Accept it, flagged, and check key figures (such as payroll tax thresholds) against the regulator's current guidance? | Yes, until an open source for later NSW changes is found |
| S4 | Include regulations, rules and orders, not only Acts? | Yes: many duties sit in regulations, as the calibration found |

**Answers (owner, 12 November 2026):** S1 to S4 accepted as recommended. Victoria's saved Acts will be uploaded when they are requested for the Victorian batch (E-149).

## Progress

- **D-1, done 12 Nov 2026 (E-149):** 5 family gaps drafted, 6 searched again, 2 moved to D-2; 138 of 140 state and council requirements linked to their regulator or council, with 3 new overlaps recorded.
- **D-2, catalogues built 12 Nov 2026 (E-151):** all eight, the ACT's from the lists the owner saved. State departments are still to do. Details below.
- **D-3 done 12 Nov 2026 (E-152 to E-154):** 59 requirements in eight families, each quoted from the law of each jurisdiction:

  | Family | Drafted | Not drafted |
  |---|---|---|
  | Long service leave | all eight | |
  | Land tax | NSW, Vic, Qld, WA, SA, Tas, ACT (residential land only) | NT (no land tax Act) |
  | High-risk work licences (the business sees the worker's licence; in Victoria, the employer) | all eight | |
  | Hazardous chemicals above manifest quantities (notify the regulator; WA licenses the site; Victoria uses notifiable quantities) | NSW, Vic, Qld, WA, Tas, ACT, NT | SA (its r 348 was deleted) |
  | Asbestos removal licences | all eight | |
  | Environment protection licences for listed activities | NSW, Victoria, Qld, SA, Tas, ACT, NT | WA (to draft: the operating offence not yet located) |
  | Retail lease disclosure statements (landlords) | all eight | |
  | Retail trading hours | NSW, Vic, Qld, WA, SA, Tas | the ACT and NT have no such law |

  Victoria's eight are quoted from the authorised versions the owner saved and uploaded on 12 Nov 2026 (`data/raw/vic_legislation/`).
- **D-4 started 12 Nov 2026 (E-156).** NSW's 157 high-signal Acts were scanned for business licensing offences ("a person must not carry on … unless licensed"); 50 have one. 13 NSW requirements are drafted (D-4a): conveyancers, motor dealers, motor vehicle repairers, tow truck operators, scrap metal dealers, tattooists, private health facilities, plumbers, taxi and booking services, bus operators, commercial fishers, veterinary hospitals and education and care services. 38 more Acts have screening calls in the NSW catalogue (35 Y to draft, 1 L, 2 N). Each new family is logged as not yet searched in the other seven jurisdictions. The 107 high-signal Acts with no business licensing offence, and the medium and low bands, are still to screen.
- **D-4b done 12 Nov 2026 (E-157):** 16 more NSW requirements from the screening calls: ART providers, building certifiers, employing children, professional engineers, electricity accredited service providers, commercial agents, greyhound racing participants, pharmacy premises, works to State heritage items, paintball venues, petroleum in NSW coastal waters, pipelines, rail operators (national law, ONRSR), bookmakers, employing accredited teachers and private water infrastructure. NSW now has 29 industry-specific requirements from D-4.

### D-2: the catalogues and the new estimate

All eight catalogues are built (`data/processed/legislation/<state>_catalogue.csv`, by `alicia/scripts/state_catalogues.py`):

| | Listed | Set aside by title triage | To screen | High signal | Source of the list |
|---|---:|---:|---:|---:|---|
| NSW | 2,217 | 606 | 1,611 | 285 | Corpus (March 2025) |
| Victoria | 1,297 | 97 | 1,200 | 22 | Register sitemap and pages |
| Queensland | 1,000 | 55 | 945 | 234 | Corpus |
| WA | 1,565 | 85 | 1,480 | 202 | Corpus |
| SA | 1,068 | 57 | 1,011 | 189 | Corpus |
| Tasmania | 2,385 | 1,175 | 1,210 | 121 | Corpus |
| ACT | 561 | 55 | 506 | 4 | Register lists saved by the owner |
| NT | 691 | 30 | 661 | 7 | Register lists |
| **All** | **10,784** | **2,160** | **8,624** | **1,064** | |

- **Triage** sets aside 2,160 of 10,784 laws: appropriations, amending and commencement laws (most of Tasmania's set-asides are proclamations and amending Acts), appointments, naming, validations, parliamentary and judicial office, public sector superannuation, private Acts about named property or churches, old Acts cited by regnal year (such as Magna Carta in the ACT), and Commonwealth Acts the ACT register lists. The rules were checked against every high-signal law they set aside, which found and fixed three wrong ones (NSW's Electricity Supply and Gas Supply Acts had been caught as appropriations, and WA's Health (Miscellaneous Provisions) Act as an amending law). The 10 high-signal laws still set aside are 5 Electoral Acts (the Commonwealth Electoral Act was called N: its duties fall on political participants), 2 parliamentary bodies, 1 amending Act and 2 public sector superannuation schemes.
- **The signal score works as a guide.** For the five corpus states it reads each law's text for licensing offences, licences, registration, levies and duties, penalties and business words. The high band is 16% of the laws to screen but holds 84% (68 of 81) of the laws the register's requirements already cite; the low band is 53% of laws and holds 1 of 81. For Victoria, the ACT and the NT the score reads the title only, so it is weaker.
- **Victoria's titles** were all read from the register's pages (1,296, at the 2-second delay). The 470 statutory rules use their page address as their ID, because the number was not captured (the pages word it "Statutory rule number"; the script now reads it).

**The new estimate** (`data/processed/legislation/state_catalogue_estimate.csv`):

| Basis | New state requirements | Hours in session |
|---|---:|---:|
| Commonwealth outcome (low) | 594 | 11 |
| **Planning** | **950** | **20** |
| Phase B's sample, upper bound (high) | 4,711 | 134 |

- Phase B estimated about 3,000 state requirements (1,300 to 6,200) and 56 hours (23 to 189).
- The Commonwealth phase showed why to revise it. Phase B's sample rate for Acts was close: it implied about 145 Y Acts, and 150 were found. Its rate for instruments was about 20 times too high (27 of 6,846 Commonwealth instruments were Y; 39% were L), and each Y law gave 1.04 requirements, not 2.
- The planning basis takes Acts at the state sample's Y rate (20%; state Acts license more than Commonwealth ones), with the Commonwealth's yield per Y law and its instrument rate.
- Hours are on phase B's terms (screening a few seconds a law, drafting at the calibration's minutes a requirement), so they compare with phase B, not with elapsed time.

## What this plan does not cover

- Councils' own local laws and planning schemes (phase E).
- The ABLIS cross-check (phase F), which waits for the ABLIS key.
- The Commonwealth items left to return to, which are listed in the plan's [open items](plan_legislation_links.md#open-items-checklist).
