# Plan: linking Commonwealth, state and council legislation to ANZSIC classes

*Approved 6 November 2026 (DECISIONS E-115, E-116). Phase 2 of the [Industry lens plan](plan_industry_lens.md).*

## Goal

For every ANZSIC class (all 506) in every state and territory, build a sourced list of the laws a business in that class must deal with, at each tier: Commonwealth, state or territory, and council. Each link says:

- **why the law applies**: to the whole class, to some of the ABS's primary activities in it, or through an activity that crosses classes;
- **the evidence**: an official source with a quote;
- **how sure we are**: a confidence rating.

The links feed the Industry lens page, including its stage-and-threshold markers.

## What we start from

A first look at the repository; phase A is the full review.

| Asset | What it holds | Tiers | Use in this work |
|---|---|---|---|
| Register records (`regulation-register/records/`, 255) | Reforms, settings and barriers. Their 278 instruments (115 with a register ID or link) are coded mostly at class level, with framework marks and responsible bodies | Commonwealth 66, states and territories 189, councils 0 | Seed instruments; framework marks for the page |
| Regimes (`regulation-register/regimes/`, 61) | Bodies of regulation a business deals with as one task (such as food safety), each mapped to classes, with layers by tier and 55 evidenced issues | 68 Commonwealth, 104 state and 14 council layers; councils appear in 11 regimes, as one party each | The grouping a business sees; their class maps become hypotheses to test |
| Bodies (`bodies.json`, 115) | Departments, agencies and regulators | Commonwealth 28, states and territories 81, national schemes 6, councils none | Administering bodies for each law |
| Register adapters (`alicia/src/alicia/legislation/`) | Read dates for a named law from the Federal Register of Legislation (public API) and six state and territory registers. NSW and SA block automated requests | Commonwealth, six states and territories | Extend from "dates for one law" to "list every law in force" |
| ANZSIC classes (`data/processed/anzsic/`) | 506 classes, their definitions, 4,440 primary activities and their exclusions | n/a | The join key |
| ABS LGAs (`data/processed/geo/`) | 548 council-area codes (ASGS 2021) | Councils | Council geography |
| Notes in `docs/` | Regulatory complexity method, responsibility and history, the legislation gap scan, the register review, recommendations | All | Methods and known gaps |

**Gaps:**

- No list of all laws in force at any tier.
- No council laws or planning terms.
- No licence lists: the ABLIS API, the government's business licence finder, needs registration.
- Most instruments have no register ID.
- Some regime class maps cover too much. For example, pharmacy rules are mapped to all of class 4271, which also covers cosmetics retailers.

## How the data will be shaped

Three linked tables, so a law that applies to every business is recorded once, not 506 times:

1. **Law.** One Act, regulation, legislative instrument, code, planning scheme or local law. It records the jurisdiction, tier, title, official register ID and link, whether it is in force, and the administering body.
2. **Requirement.** What the law asks of a business: register, hold a licence, get an approval, pay, report or meet a standard. It also records the trigger (entry, first employee, a size threshold, an activity, exit) and the value in each jurisdiction. This absorbs the stage-and-threshold table from the first lens plan.
3. **Link.** A requirement's reach, in one of four forms:
   - every class, with any exclusions;
   - listed classes;
   - listed classes, limited to named ABS primary activities;
   - an activity trigger across classes.

   Each link also records its basis (the law's own definitions, regulator guidance or ABLIS), a quote, a confidence rating and whether it has been checked.

Each requirement belongs to a regime. Classes that are mainly government or households are kept and marked. The proposed rule:

- the 11 classes the ABS publishes no business counts for;
- the government administration and defence classes in Division O, judged by their ABS definitions.

## Phases

| Phase | What | Main outputs |
|---|---|---|
| **A. Review** | Review the repository's existing research on each tier: what it covers, how it is coded, how well sourced it is, and what can be reused as it is. Mark the government and household classes | `docs/legislation_inventory.md`; the marked class list |
| **B. Design and calibration** | Write the schema and coding rules: what counts as "applies to a business" (direct obligations only, with economy-wide laws listed once); whole class versus activities; quotes; confidence levels. Then run the full method on one class per division (19) across all tiers, to test the rules and time the work. This is a method test before running all 506, not a cut in scope | Schema checked by `alicia validate`; `docs/methods_legislation_links.md`; a timing estimate for C to F |
| **C. Commonwealth** | List every principal Act and legislative instrument in force from the Federal Register. Screen out laws that don't oblige businesses, split economy-wide from industry-specific, and link to classes | `data/processed/legislation/` catalogue (metadata only, no law texts); Commonwealth links in `regulation-register/links/` |
| **D. States and territories** | The same for each of the eight registers, including each state's version of national model laws. Done state by state, with NSW and SA handled as D2 decides | State catalogues and links; differences between states recorded per requirement |
| **E. Councils** | (1) Classify each class in each state's planning-scheme land-use terms (each state's standard definitions; which ones, to be confirmed). (2) Flag state laws that councils administer (food business registration, public health permits) in phase D. (3) Collect local laws for a sample of councils in each state, measure how much they vary, then decide whether to cover all of them (D4) | Class × state × land-use term table; local-law sample and a summary of the variation |
| **F. Completeness check** | Compare the links for each class and state with what ABLIS and business.gov.au's industry guides list, and fix what is missing | Coverage report by class and state |
| **G. Assemble and check** | One link table across tiers. Counts recalculated independently; a random sample of links re-verified, with the error rate reported; a spot-check list for the owner | Final link table; checks; methods note; `data/SOURCES.md` and DECISIONS entries |

**Order.** The Commonwealth comes first: it has one register with an API, and its economy-wide laws apply to every class. States follow, with eight registers, two of which block automated requests. Councils come last: they are the least standardised, and their planning work depends on each state's planning framework.

**Scale.** How many laws there are is not yet known. Phases C and D measure it; the Federal Register API's in-force filter returned errors on 6 November, which phase C resolves.

**Managing the scale:**

- Work is committed in batches, by jurisdiction and division, each validated before the next starts.
- A progress table is kept in this plan.
- As with the register, links are drafted by AI-assisted desk research from the sources they cite. Nothing is invented, and each link quotes its basis.

## Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| D1 | Run the method end to end on one class per division (19) before scaling to all 506? | Yes. It tests the rules and gives a time estimate |
| D2 | The NSW and SA registers block automated access. Use AustLII (free, but not an official source) only as an index of titles, and cite and link each law's official register page, with a sample checked by hand? | Yes, if AustLII is reachable from here; otherwise you download the NSW and SA lists |
| D3 | Register for an ABLIS API key (your action; stored as a secret on this environment) before phase F? | Yes |
| D4 | Councils: start with a sample of three per state (capital city, a regional city, a rural council) and decide on all ~540 after measuring the variation? | Yes |
| D5 | Bulk work: in-session AI-assisted research (no extra cost, slower), or batch runs through the Claude API (faster, needs an API key and costs money)? | Start in-session; decide after D1's timing |

**Answers (6 November 2026):** D1, D4 and D5 approved as recommended. D3: the owner will apply for an ABLIS key, which may take time ([brief](ablis_brief.md)); phase F waits for it. D2 is open. AustLII refused this environment (Cloudflare block), and the owner will revisit with a preference for little work by hand. Options found the same day:

- the Open Australian Legal Corpus (CC BY 4.0), covering in-force Commonwealth, NSW, Qld, WA, SA and Tas law as at 10 March 2025, with official register links;
- SA's official XML update packages, published fortnightly on data.sa.gov.au;
- NSW changes since March 2025, which have no open source found yet.

**D5, revisited after calibration (6 November 2026):** about 120 hours in session (49–377) for phases C to G, or about 40 hours plus a pipeline with the Claude API. Recommendation: phase C in session, while a pilot of about 100 API-drafted requirements from one state is compared with in-session drafts; decide phase D on the pilot ([estimate](estimate_legislation_links.md)).

**D5 answered (10 November 2026):** in-session work. The owner may later hand some of it to other models; that is for later (E-129).

## Progress

| Phase | Status |
|---|---|
| A. Review | **Done 6 November 2026**: [`legislation_inventory.md`](legislation_inventory.md); 16 classes marked (`data/processed/anzsic/class_marks.csv`) |
| B. Design and calibration | **Done 6 November 2026.** Estimate for phases C to G and the D5 options: [`estimate_legislation_links.md`](estimate_legislation_links.md); rules revised (methods 4, 7, 10–12; 5a added). Design done 6 Nov 2026 ([`methods_legislation_links.md`](methods_legislation_links.md), E-119). Calibration: batch 1 (Commonwealth, every business) done, 11 requirements; batch 2 (states and territories, every business) done, 24 requirements: payroll tax, workers' compensation insurance and the WHS primary duty in all eight; batch 3 (industry-specific Commonwealth) done, 20 requirements: 13 modern awards and 7 Acts or instruments; batch 4 (industry-specific states) done for six families, 42 requirements: food business registration, builder licensing, security, liquor and health practitioner registration in all eight, exploration in two. batch 5 (capital-city councils) done, 20 requirements: outdoor dining, busking and filming permits in the seven capital cities, from ABLIS's public listings (four council sites refuse automated requests) and, where readable, the councils' own documents. Batch 4f (more state families) done, 42 requirements: livestock property identification (7), waste transport (5), construction long service leave (8), cleaning and security long service leave (3), skin penetration (3), driving instructors (7), working with children checks (7), most drafted from ABLIS listings (methods rule 5a, law text still to quote), and home warranty insurance (NSW, SA) from the law. 376 of 376 quotes checked. Class link table: `data/processed/legislation/links.csv.gz` (19,389 links) |
| C. Commonwealth | **Started 7 November 2026.** Catalogue from the Federal Register API (`alicia/scripts/frl_catalogue.py`, `data/processed/legislation/cth_catalogue.csv`): 1,263 principal Acts and 23,586 principal instruments in force; after title triage, 1,212 Acts and 6,849 instruments to screen. Batch 1: 20 industry-specific requirements from 18 Acts (licences, authorisations and registrations in pharmacy, therapeutic goods, credit, banking, insurance, superannuation, telecommunications, broadcasting, aviation, tax agents, excise, education, industrial chemicals, aged care, appliances and greenhouse reporting), each quoted from the latest compilation, reached across all 506 classes and marked against the productivity framework (E-124). 18 Acts called Y in the catalogue; the rest still to screen. **Reach recoded 10 Nov 2026** (E-127): the 123 requirements drafted during calibration now reach every class their law covers, not only the 19 calibration classes. **Batch 2 (10 Nov 2026, E-130):** VET training organisation registration, agricultural and veterinary chemical registration, domestic commercial vessel certificates and AML/CTF enrolment, and fuel quality standards (E-131); 23 Acts now called Y. **Batch 3 (11 Nov 2026, E-132):** the catalogue reconciled with requirements drafted before screening (17 Acts); the 115 unscreened Acts with the strongest obligation signals screened (39 Y, 2 L, 67 N, 7 already Y); 10 requirements drafted; 29 Y calls are marked 'to draft' in the catalogue. Calls so far: 77 Y, 4 L, 67 N of 1,212 Acts. **Batch 4 (11 Nov 2026, E-133):** 22 of batch 3's 29 'to draft' calls drafted; 7 remain. **Left on the Commonwealth side:** 1,067 Acts to screen (87 with entry signals, 165 with levy signals, 822 with neither) and 6,843 instruments. **Batch 5 (11 Nov 2026, E-134):** the 165 Acts with levy or charge signals screened (30 Y, 67 L, 68 N); 9 levy and tax requirements drafted. Calls so far: 105 Y, 72 L, 136 N; 902 Acts left to screen. **Batch 6 (11 Nov 2026, E-138, E-139):** 13 of the 26 'to draft' calls drafted after a manual read; the remaining 902 Acts screened (51 Y, 112 L, 739 N), with 5 new requirements drafted. **Every Commonwealth Act is now screened:** 149 Y, 188 L, 878 N. **Batch 7 (11 Nov 2026, E-140):** 44 more requirements drafted from 45 of the 58 'to draft' calls; 5 calls corrected; 8 still to draft. **Instruments batch 1 (11 Nov 2026, E-141):** 5,438 instruments screened by parent Act and series (82 Y, 2152 L, 3207 N so far); 10 requirements drafted, including six industry codes and the Water Market Rules; 1405 instruments left, mostly ASIC and CASA instruments |
| D. States and territories | **Started 10 Nov 2026** (E-129), on the calibration families: 24 of the 40 ABLIS-first drafts now quote the law (E-129, E-131); 7 missing states drafted from the law; the other 22 gaps logged in `regulation-register/requirement-gaps.json` (rule 12). Full register screening not started (D2 settled: the corpus indexes NSW and SA, E-118) |
| E. Councils | Not started |
| F. Completeness check | Waiting for the ABLIS key |
| G. Assemble and check | Not started |

## Open items (checklist)

*Started 10 November 2026 (E-131). Tick items off here as they are done.*

**Sources**

- [ ] **Victoria: 16 requirements and gaps do not quote the Victorian Act** (15 Acts). The Victorian register asks automated tools not to fetch its documents, and several regulators' sites refuse automated requests. The owner has saved these Acts (11 Nov 2026) and will upload them in the state phase (D).
- [ ] **16 requirements still rest on an ABLIS listing alone** (rule 5a). Most of the duties are likely in regulations; phase D's screening of each register, regulations included, should reach them.
- [ ] **Commonwealth requirements quoting a simplified outline** (medium confidence until the operative section is quoted): aged care, paid parental leave, ozone and SGG licences, coastal trading.
- [ ] **Partial ABLIS reach** (owner, 10 Nov 2026: come back to these). The Queensland livestock duty is the Act's, but which entities must register comes from ABLIS. The same applies to the ACT cleaning and security scheme's coverage and the two Victorian long service schemes (administrators' pages).
- [ ] **NSW and SA quotes come from the corpus copy as at 10 March 2025.** Re-check them against the current text once a source for later NSW changes is found (D2).
- [ ] **NT locators use section headings**, because the NT register's PDFs lose section numbers when read as text. Recover the numbers.
- [ ] **Nothing has been checked by a person.** Phase G's spot-check list covers this.

**Coverage**

- [ ] **The 8 Commonwealth Acts left to draft after batch 7** (owner, 11 Nov 2026: look for them in the instruments, and if they are not there, check elsewhere). Status after instruments batch 1:
    - [x] Water Act 2007: drafted from the Water Market Rules 2009 (r 6).
    - [x] Payment Times Reporting Act 2020: drafted from the Act (s 12(1)); the Payment Times Reporting Rules 2024 support it.
    - [x] Civil Aviation (Unmanned Aircraft Levy) Act 2020: drafted from the Act (s 5) and the 2021 Regulations (s 5, $40 for aircraft over 500 g).
    - [ ] Sea Installations Act 1987: the Sea Installations Regulations 2018 exist; the permit duty is still to locate in the Act (s 6 is a definition). Next: read the Act's Part on permits.
    - [ ] National Health Security Act 2007: the SSBA Standards Determination 2023 exists; the duty to register is still to locate. Next: Part 3 of the Act (sections 36 to 38).
    - [ ] Financial Sector (Shareholdings) Act 1998: a 2019 determination exists; the 20% limit is still to quote. Next: the Act's sections after s 10.
    - [ ] Customs Act 1901: about 45 customs instruments support it; the duty to enter imported goods is still to quote. Next: s 68 and the import declaration sections (71A onwards).
    - [ ] Aircraft Noise Levy Act 1995: no instrument names a leviable airport. Next: check whether any airport is still prescribed (the Collection Act and the Department's notices); if none, recall it as N.

- [ ] **Sample the title-only screening calls.** In batch 6, 739 Acts were called N from their titles (and long titles where the corpus has them). Phase G should re-check a random sample of them.

- [ ] **Commonwealth instruments called Y but not yet drafted** (72 after instruments batch 1: industry codes such as Dairy, Unit Pricing and Electricity Retail; product safety and information standards; the Fair Work termination and deactivation codes) Act 2020; Customs Act 1901; Financial Sector (Shareholdings) Act 1998; National Health Security Act 2007; Payment Times Reporting Act 2020; Sea Installations Act 1987; Water Act 2007), listed in `data/processed/legislation/cth_catalogue.csv` with 'to draft' reasons.

- [ ] **22 state gaps** in `regulation-register/requirement-gaps.json`: 10 to draft, 7 not found, 3 blocked (Victoria), 2 not searched.
- [ ] **Construction long service levies**, a separate obligation on the person for whom building work is done (e.g. NSW s 34). To be recorded as their own family.
- [x] **Life insurance registration** (come back to, owner 11 Nov 2026). Resolved the same day: the ban is in s 17(1) of the Life Insurance Act 1995, worded "must not intentionally issue a life policy"; drafted in batch 3 (E-132).
- [ ] **Other AML/CTF designated services** (bullion and precious stones dealers, property developers selling real estate). Not yet coded.
- [ ] **Come back to (owner, 11 Nov 2026): aged care.** It keeps the Act's simplified outline as the source. Registration is a condition of funding in the Aged Care Act 2024, not an offence, so there is no operative offence to quote. Revisit if a later batch finds the registration duty in the Rules or another Act.

**Industry lens (owner's list, 10 Nov 2026)**

- [ ] Regulators' market studies (ACCC, PC) as a cross-check of the market figures (option 4).
- [ ] A structural economic conditions chart for council areas and regions (when the owner asks).
- [ ] Council-level features on the map (when the owner asks).
- [ ] ABLIS API key (owner), then phase F.
