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
5. **Sources.**
   - Every requirement quotes the obligation from the law, read from the official register.
   - For NSW and SA, the quote may be read from the Open Australian Legal Corpus's copy of the official text (`checked: corpus-copy`, with the corpus document ID), cited by its official register link.
   - The reach quotes the law's scope or definitions, or official guidance (the regulator, business.gov.au, ABLIS) naming the industry.
   - Thresholds quote the official value, with the date it applied.
6. **Confidence.**
   - **High:** the law's own words name the activity, or its scope clearly covers every business in the class.
   - **Medium:** official guidance names the industry.
   - **Low:** inferred from the ABS class definition, with no source naming the industry.
7. **Tiers.**
   - Council-made instruments (local laws, and planning schemes a council makes) are tier `local`, filed under the ABS LGA code. The code is checked against ASGS 2021 and its state.
   - State laws that councils administer, such as food business registration, are tier `state` with `administered_by_councils`.
   - Classifying classes in each state's planning land-use terms is phase E.
8. **Dates.** Values are those in force on the date checked (`as_at`). A law repealed since is not recorded.
9. **Drafts.** Everything is drafted by AI-assisted desk research from the sources cited, and stays `draft` until a person has checked it.

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
