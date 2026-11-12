# Methods: linking legislation to ANZSIC classes

*Phase B of the [legislation-links plan](plan_legislation_links.md) (DECISIONS E-116, E-119). The model is `alicia/src/alicia/register/requirements.py`; its JSON schema is `regulation-register/schema/requirement.schema.json`; `uv run alicia validate` checks every file. Draft rules, to be revised after calibration.*

## What is recorded

**Requirements.** One per requirement per jurisdiction, in `regulation-register/requirements/<jurisdiction>/` (`cth`, `nsw`, ..., `local/<ABS LGA code>/`). Each requirement records:

| Part | What it holds |
|---|---|
| Laws | Each Act, regulation, instrument, code, planning scheme or local law behind it, with an official register ID or link and the provision |
| Kind and what | Register, licence, approval, notification, tax or levy, insurance, reporting, record-keeping, standard; plain English |
| Triggers | Entry, first employee, a threshold in employees, payroll, turnover, revenue or assets (value, test, unit, date and source), an activity, while operating, exit |
| Reach | Every class, listed classes, listed classes limited to ABS primary activities, or listed classes with a condition; optionally some legal forms only |
| Sources | The obligation, the reach and any threshold, each quoted word for word |
| Confidence | High, medium or low (below) |
| Links | The regime it belongs to, the administering bodies (`bodies.json`), register items about it, ABLIS service IDs once checked |

**The link table.** `links()` expands requirements into one row per class and requirement. That is the table joining each legislative level to the ANZSIC classes. A requirement that reaches every business is stored once and expanded only there.

## Rules

1. **What counts.** A requirement is something a law obliges a business to do or have in order to start, run, grow or close it:
   - register, hold a licence or permit, get an approval, notify, pay a tax, levy or fee, report, keep records, insure, or meet a standard specific to the activity.

   General laws that bind everyone alike are left out, such as criminal law or road rules for private driving. Things a business may choose to do (an ABN, which is voluntary) are recorded only where a requirement depends on them; GST registration, for example, depends on an ABN.
2. **Once per jurisdiction.** A Commonwealth requirement is recorded once and applies in every state. Each state's version of a national model law is its own requirement. All versions share a `family`, which drives the state switch and the "same in every state" badge.
3. **Economy-wide requirements are stored once.** A requirement on every business, every employer or every company is recorded with an `all` reach. Its triggers and legal forms say which businesses it reaches (e.g. "first employee", "company").
4. **Reach at the class level.**
   - **Whole class:** when the law's scope, read against the ABS class definition, covers every business mainly engaged in the class.
   - **Primary activities:** when it covers only some of the class. The ABS primary activities are quoted exactly as the ABS lists them, and `alicia validate` checks the wording.
   - **Condition:** when it follows an activity that crosses classes, such as selling alcohol. It is linked to the classes whose ABS definition or primary activities include the activity, or that official guidance names.
   - **Once per family, across all 506 classes** (revised after phase B). The reach is coded for the whole family from a keyword shortlist of ABS class names, definitions and primary activities. Each state's version is then checked for a narrower or wider scope. The calibration coded only its 19 classes; on 10 November 2026 every calibration requirement was recoded across all 506 (E-127), and from phase C every requirement is coded that way from the start.
5. **Sources.**
   - Every requirement quotes the obligation from the law, read from the official register.
   - For NSW and SA, the quote may be read from the Open Australian Legal Corpus's copy of the official text (`checked: corpus-copy`, with the corpus document ID), cited by its official register link.
   - The reach quotes the law's scope or definitions, or official guidance (the regulator, business.gov.au, ABLIS) naming the industry.
   - Thresholds quote the official value, with the date it applied.

   **5a. ABLIS-first drafts.** Where the law's text is slow to reach (registers that refuse automated requests, obligations spread across definitions), a requirement may be drafted from its official ABLIS service page before the law is quoted. Such a draft:
   - quotes the first sentence of the ABLIS description, unaltered and attributed (ABLIS's copyright allows nothing more);
   - names the Act or Acts the listing gives, linked through the ABLIS page and with no register ID yet;
   - records the ABLIS service ID (`ablis`);
   - is rated **medium** at most, with a `confidence_note` saying the law's own text is not yet quoted.

   Phase D replaces the ABLIS link with the register ID and a quote from the law, and raises the confidence where the law's words support it. The ABLIS listing stays as a reach source.
6. **Confidence.**
   - **High:** the law's own words name the activity, or its scope clearly covers every business in the class.
   - **Medium:** official guidance names the industry.
   - **Low:** inferred from the ABS class definition, with no source naming the industry.
7. **Tiers.**
   - Council-made instruments (local laws, and planning schemes a council makes) are tier `local`, filed under the ABS LGA code. The code is checked against ASGS 2021 and its state.
   - State laws that councils administer, such as food business registration, are tier `state` with `administered_by_councils`. A permit that every council issues under a state Act is one state requirement, not one per council (revised after phase B: 83% of a random sample of ABLIS services were council-administered, most under state Acts). Fees or conditions that differ by council are recorded as values.
   - Classifying classes in each state's planning land-use terms is phase E.
8. **Dates.** Values are those in force on the date checked (`as_at`). A law repealed since is not recorded.
9. **Drafts.** Everything is drafted by AI-assisted desk research from the sources cited, and stays `draft` until a person has checked it.
10. **Screening a register** (added after phase B). Every law in a register's list is screened, and the call is recorded in the catalogue so it can be audited and sampled:
    - **Y:** it creates one or more requirements;
    - **L:** it only supports an existing requirement (a standard, rate or form under it); the law is added to that requirement's `laws`;
    - **P:** a planning instrument, handled in phase E;
    - **N:** no obligation on businesses, with a one-line reason.

    Instruments are screened by parent Act (added 11 Nov 2026, E-141). An instrument made under an Act called N is called N. An instrument under an Act that creates requirements is called L to them, unless it is administrative (an appointment, delegation, exemption or amendment), when it is N, or it creates a new obligation of its own (an industry code, a product safety or information standard), when it is Y. Instruments with no parent Act in their name are screened by series (accounting standards, Australian Design Rules, Marine Orders and so on) or one by one.

    A title triage first sets aside amending Acts, appropriations, airworthiness directives, tariff concession orders, appointments and similar series; the triage patterns are kept with the catalogue.
11. **Thresholds in subordinate instruments** (added after phase B). Before a threshold is recorded as not yet quoted, the regulations, determinations and orders made under the law are searched for it. The calibration found the GST threshold in the regulations and the ACT payroll tax threshold in a determination, not in the Acts.
12. **Gaps are logged** (added after phase B; built 10 November 2026, E-129). A state family with no requirement in a state or territory is logged in `regulation-register/requirement-gaps.json`, saying what was searched, rather than left blank. `alicia validate` fails if a state family has neither a requirement nor a gap in any of the eight. Each gap has a status:
    - **not found:** the sources searched show no such requirement;
    - **to draft:** the law is identified (named in `law`) but the requirement is not yet drafted;
    - **not applicable:** a quoted source shows the family cannot apply there;
    - **blocked:** the sources could not be read (a register or regulator refusing automated requests);
    - **not searched:** not yet looked for, with the reason.

    A gap records a search, not that no law exists, unless its sources say so.
13. **Every requirement is marked against the productivity framework** (added 7 November 2026, DECISIONS E-123). Each requirement carries an `assessment` like a register item's: the eight drivers marked from −2 to +2 against the same market without it, a main driver, reach and confidence. Where the register assesses the same law, the requirement uses its marks. A small obligation may have no material effect. The Industry lens reads these marks ([`industry_lens.md`](industry_lens.md)).

13. **Who administers a requirement, and where administration overlaps** (added 12 November 2026, E-148). Each requirement records every body with a part in it, in `administration`. Each entry gives:
    - the body's function, in the regime model's terms: sets the rules, licenses, approves, inspects and enforces, collects, or funds;
    - the body (from `bodies.json`), or a class of bodies such as "state and territory consumer protection agencies";
    - the tier and any states it acts in;
    - a quoted source.

    The sources are:
    - **the law's own words** naming the body and its part (for example, "ASIC must grant an applicant an Australian financial services licence"), or the law's definition of the body it names;
    - **the Administrative Arrangements Order** for the department that administers the Act. The Order's entry for the Act is quoted. Where it splits an Act between departments ("except to the extent administered by…"), each department is recorded;
    - **official guidance** where the law does not name a body, such as the ACCC's advice that state agencies also enforce the Australian Consumer Law.

    `administered_by` lists the same bodies, and `alicia validate` checks that they match. A role whose source could not be found is left out rather than guessed.

    Two measures of complexity follow (`scripts/agency_overlap.py`):
    - **an overlap:** two or more bodies doing the same business-facing function for one requirement (licensing, approving, inspecting and enforcing, collecting or funding). An example is the ACL, which the ACCC and the state agencies both enforce. Rules set by more than one body (a department and a regulator, or two departments) are counted separately;
    - **agencies per class:** the distinct bodies behind the requirements that reach each class and state (`data/processed/legislation/agencies_by_class.csv`), with how many of those requirements involve several bodies, overlap, or span the Commonwealth and the states.

    **Limits.** The counts cover bodies the register names, not every agency a business may meet. So far they are almost all Commonwealth: state and council requirements are linked to their regulators in phase D.

## Calibration (phase B)

**Classes:** the class with the most businesses in each division (ABS CABEE, June 2025, Australia), leaving out the marked classes:

| Division | Class | Division | Class |
|---|---|---|---|
| A | 0142 Beef Cattle Farming (Specialised) | K | 6240 Financial Asset Investing |
| B | 1012 Mineral Exploration | L | 6712 Non-Residential Property Operators |
| C | 1174 Bakery Product Manufacturing (Non-factory based) | M | 6962 Management Advice and Related Consulting Services |
| D | 2911 Solid Waste Collection Services | N | 7311 Building and Other Industrial Cleaning Services |
| E | 3011 House Construction | O | 7712 Investigation and Security Services |
| F | 3800 Commission-Based Wholesaling | P | 8219 Adult, Community and Other Education n.e.c. |
| G | 4310 Non-Store Retailing | Q | 8511 General Practice Medical Services |
| H | 4511 Cafes and Restaurants | R | 9002 Creative Artists, Musicians, Writers and Performers |
| I | 5102 Courier Pick-up and Delivery Services | S | 9511 Hairdressing and Beauty Services |
| J | 5511 Motion Picture and Video Production | | |

**Tiers:** the Commonwealth, all eight states and territories, and each capital city's council. The ABS LGA codes are Sydney 17200, Melbourne 24600, Brisbane 31000, Perth 57080, Adelaide 40070, Hobart 62810 and Darwin 71000; the ACT has no councils.

**Batches:**

1. Commonwealth requirements on every business;
2. state requirements on every business;
3. industry-specific Commonwealth requirements;
4. industry-specific state requirements;
5. councils.

The time taken, the sources fetched and the sources refused are logged for each requirement (`docs/calibration_legislation_links.csv`). Those logs give the estimate for phases C to F.

**Results.** 159 requirements across all tiers; 376 quotes, all re-found in their sources. Steady-state time was 0.74 active minutes a requirement. Three steps the batches did not exercise were measured in small samples: screening a register, coding reach across all 506 classes, and the mix of ABLIS services. The estimate for phases C to G, and the options for D5, are in [`estimate_legislation_links.md`](estimate_legislation_links.md). The rules revised as a result are 4, 7 and 10 to 12; rule 5a was added during batch 4f. From phase C, each batch runs in a fresh session with a short brief: re-reading a long conversation's context was most of the calibration's token use.
