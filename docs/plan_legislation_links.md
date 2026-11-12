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
| **G. Assemble and check** | One link table across tiers. Counts recalculated independently; every requirement, call and link checked by the AI checking process the owner is setting up in a separate thread (E-145), with the error rate reported. A person cannot check a register of this size | Final link table; checks; methods note; `data/SOURCES.md` and DECISIONS entries |

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
| C. Commonwealth | **Started 7 November 2026.** Catalogue from the Federal Register API (`alicia/scripts/frl_catalogue.py`, `data/processed/legislation/cth_catalogue.csv`): 1,263 principal Acts and 23,586 principal instruments in force; after title triage, 1,212 Acts and 6,849 instruments to screen. Batch 1: 20 industry-specific requirements from 18 Acts (licences, authorisations and registrations in pharmacy, therapeutic goods, credit, banking, insurance, superannuation, telecommunications, broadcasting, aviation, tax agents, excise, education, industrial chemicals, aged care, appliances and greenhouse reporting), each quoted from the latest compilation, reached across all 506 classes and marked against the productivity framework (E-124). 18 Acts called Y in the catalogue; the rest still to screen. **Reach recoded 10 Nov 2026** (E-127): the 123 requirements drafted during calibration now reach every class their law covers, not only the 19 calibration classes. **Batch 2 (10 Nov 2026, E-130):** VET training organisation registration, agricultural and veterinary chemical registration, domestic commercial vessel certificates and AML/CTF enrolment, and fuel quality standards (E-131); 23 Acts now called Y. **Batch 3 (11 Nov 2026, E-132):** the catalogue reconciled with requirements drafted before screening (17 Acts); the 115 unscreened Acts with the strongest obligation signals screened (39 Y, 2 L, 67 N, 7 already Y); 10 requirements drafted; 29 Y calls are marked 'to draft' in the catalogue. Calls so far: 77 Y, 4 L, 67 N of 1,212 Acts. **Batch 4 (11 Nov 2026, E-133):** 22 of batch 3's 29 'to draft' calls drafted; 7 remain. **Left on the Commonwealth side:** 1,067 Acts to screen (87 with entry signals, 165 with levy signals, 822 with neither) and 6,843 instruments. **Batch 5 (11 Nov 2026, E-134):** the 165 Acts with levy or charge signals screened (30 Y, 67 L, 68 N); 9 levy and tax requirements drafted. Calls so far: 105 Y, 72 L, 136 N; 902 Acts left to screen. **Batch 6 (11 Nov 2026, E-138, E-139):** 13 of the 26 'to draft' calls drafted after a manual read; the remaining 902 Acts screened (51 Y, 112 L, 739 N), with 5 new requirements drafted. **Every Commonwealth Act is now screened:** 149 Y, 188 L, 878 N. **Batch 7 (11 Nov 2026, E-140):** 44 more requirements drafted from 45 of the 58 'to draft' calls; 5 calls corrected; 8 still to draft. **Instruments batch 1 (11 Nov 2026, E-141):** 5,438 instruments screened by parent Act and series (82 Y, 2152 L, 3207 N so far); 10 requirements drafted, including six industry codes and the Water Market Rules; 1405 instruments left, mostly ASIC and CASA instruments. **Instruments batch 2 (11 Nov 2026, E-142):** the ASIC, CASA and other series screened; 9 requirements drafted (the Australian Consumer Law duties on safety standards, bans and information standards; the Dairy, Unit Pricing and Electricity Retail codes; the road transport and platform deactivation codes; the financial sector shareholding limit). Instrument calls: 38 Y, 2586 L, 4137 N; 85 left to screen; 23 Y to draft. **Final Commonwealth batch (12 Nov 2026, E-143):** every Commonwealth Act and instrument screened (Acts 146 Y, 186 L, 880 N; instruments 28 Y, 2641 L, 4177 N); 14 more requirements drafted; 3 Y calls to draft. **Quality check (12 Nov 2026, E-144,** [`qa_legislation_register_2026-11-12.md`](qa_legislation_register_2026-11-12.md)**):** automated checks, a sample of 30 requirements and 40 N calls, and a re-scan of every N Act. 3 Acts recalled Y and drafted (Sex Discrimination, Marriage, Child Support), 1 recalled Y to draft (Movable Cultural Heritage), 1 recalled L (Disability Discrimination) and 6 instruments recalled L. Calls now: Acts 150 Y, 187 L, 875 N; instruments 28 Y, 2,647 L, 4,171 N; 329 requirements. **Last Y calls drafted (12 Nov 2026, E-146):** the ASIC continuing credit order, the public transport disability standards and the cultural heritage export permit; no Commonwealth Y call is left to draft; 332 requirements (197 Commonwealth) |
| D. States and territories | **Plan drafted 12 Nov 2026:** [`plan_states.md`](plan_states.md) (batches D-1 to D-11, decisions S1 to S4). **Started 10 Nov 2026** (E-129), on the calibration families: 24 of the 40 ABLIS-first drafts now quote the law (E-129, E-131); 7 missing states drafted from the law; the other 22 gaps logged in `regulation-register/requirement-gaps.json` (rule 12). Full register screening not started (D2 settled: the corpus indexes NSW and SA, E-118) |
| E. Councils | Not started |
| F. Completeness check | Waiting for the ABLIS key |
| G. Assemble and check | Not started. A first quality check by the drafting process was done on 12 Nov 2026 (E-144). The full check will be an AI checking process run from a separate thread (E-145) |

## Open items (checklist)

*Started 10 November 2026 (E-131). Tick items off here as they are done.*

**Commonwealth: to return to** (owner, 12 Nov 2026: the Commonwealth phase's core is done; these are listed to come back to while the states proceed)

*Quotes to complete*

- [ ] **Who is covered is not yet quoted** for 30 Commonwealth requirements: the duty is quoted, but the definitions, thresholds or rules that say which businesses it reaches are not. They include payment times reporting (reporting entities), sustainability reporting (the size tests in s 292A(3) to (6)), ransomware reporting (the turnover threshold in the rules), the CSLR levy, the Financial Accountability Regime, critical infrastructure, the cash acceptance code, foreign investment thresholds, the unmanned aircraft levy and primary industries levies. Each record's confidence note names what is missing.
- [ ] **Commonwealth requirements quoting a simplified outline** (medium confidence until the operative section is quoted): aged care, paid parental leave, ozone and SGG licences, coastal trading. The food and grocery code also quotes its outline.
- [ ] **Single provisions still to quote:** the National Health Security Act's duty to register (the last of the 8 Acts left after batch 7; event reporting is drafted from the Regulations, s 20, and the SSBA Standards Determination 2023 supports it); the 20% shareholding limit (Financial Sector (Shareholdings) Act, s 10 and the Schedule); who is liable for the ASIC annual review fee (s 7).
- [ ] **Import entry rests on the ABF's guidance** (medium), because s 68(2) of the Customs Act says the owner "may enter" goods.
- [ ] **Quoted from the corpus copy (March 2025 or earlier):** the bulk wheat code, the coal long service payroll levy, the news media bargaining charge, the seafarers compensation levy and the Water Market Rules (a 2013 compilation). Re-quote from the current register text.
- [ ] **Section numbers not yet checked or recorded:** the ASIC binary options and short term credit orders, and the space launch facility licence.
- [ ] **Weak quotes from the calibration:** the superannuation guarantee (s 17A(1) only says when the Subdivision applies) and privacy for health service providers.
- [ ] **21 Commonwealth requirements are medium confidence with no note saying why.** Add the reason, or raise them to high once checked.
- [ ] **Come back to (owner, 11 Nov 2026): aged care.** It keeps the Act's simplified outline as the source. Registration is a condition of funding in the Aged Care Act 2024, not an offence, so there is no operative offence to quote. Revisit if a later batch finds the registration duty in the Rules or another Act.

*Coverage*

- [ ] **Other AML/CTF designated services** (bullion and precious stones dealers, property developers selling real estate). Not yet coded.
- [ ] **The 3 public sector awards** (Local Government Industry, State Government Agencies, Australian Government Industry): which governments are in the national system differs by state and is not yet coded (E-147).
- [ ] **Refresh the Commonwealth catalogue.** It was read from the Federal Register API on 7 Nov 2026; laws made since then are not screened. Re-run `alicia/scripts/frl_catalogue.py` (it keeps the calls already made) and screen the new rows. Deferred (owner, 12 Nov 2026): major new legislation since 7 November is unlikely.

*Regulator and regime links*

- [ ] **Left from the regulator links:** 19 Commonwealth requirements fit none of the 61 regimes (privacy, foreign investment, modern slavery, sustainability reporting, critical infrastructure, space and others); 14 roles had no source naming the body (mostly levies collected under separate collection Acts, and some DCCEEW licences); 2 requirements have no administration yet.

*For the AI checking process (E-145)*

- [ ] **Sample the title-only screening calls.** In batch 6, 739 Acts were called N from their titles (and long titles where the corpus has them). A first sample of 20 N Acts (12 Nov 2026, E-144) found 1 miss (the Sex Discrimination Act), which led to 4 more under the same heading; every N Act was then re-scanned for duty wording and no other miss found. The AI checking process (E-145) should re-check them, for duties worded another way.
- [ ] **Sample the rule-based instrument calls.** Instruments batch 1 called 5,359 instruments N or L by parent Act and series rules. A first sample of 20 N calls (E-144) found none wrong, but 6 instruments under recalled Acts changed with them. The AI checking process (E-145) should re-check them, especially L calls made only because of the parent Act.
- [ ] **Titles set aside by triage:** 16,733 instruments (mostly airworthiness directives and tariff concession orders) and 51 Acts were never screened, by rule 10's title triage. A sample would confirm none oblige businesses directly.

*Done*

- [x] **Commonwealth Y calls not yet drafted.** The last 4 were drafted on 12 Nov 2026 (E-146): ASIC's continuing credit contracts order (with its extension), the Disability Standards for Accessible Public Transport, and the Movable Cultural Heritage Act's export permit. No Commonwealth Y call is left to draft.
- [x] **Modern awards.** All 122 on the Fair Work Ombudsman's list are drafted (E-147; 13 in calibration, 109 on 12 Nov 2026), from the Fair Work Commission's award text. Still open: which governments are in the national system, for the 3 public sector awards.
- [x] **Commonwealth requirements linked to their regulators and regimes** (E-148): 304 of 306 have sourced `administration` entries, with overlaps recorded (methods rule 13); 287 have a regime.
- [x] **Life insurance registration** (come back to, owner 11 Nov 2026). Resolved the same day: the ban is in s 17(1) of the Life Insurance Act 1995, worded "must not intentionally issue a life policy"; drafted in batch 3 (E-132).

**States, councils and general: sources**

- [ ] **Medium confidence until the local law is quoted:** the Brisbane outdoor dining permit (quoted from ABLIS and the council's page; E-144).
- [ ] **ACT workers' compensation quotes the default notice**, not the duty to insure (a weak quote from the calibration).
- [ ] **Victoria: 16 requirements and gaps do not quote the Victorian Act** (15 Acts). The Victorian register asks automated tools not to fetch its documents, and several regulators' sites refuse automated requests. The owner has saved these Acts (11 Nov 2026) and will upload them in the state phase (D).
- [ ] **16 requirements still rest on an ABLIS listing alone** (rule 5a). Most of the duties are likely in regulations; phase D's screening of each register, regulations included, should reach them.
- [ ] **Partial ABLIS reach** (owner, 10 Nov 2026: come back to these). The Queensland livestock duty is the Act's, but which entities must register comes from ABLIS. The same applies to the ACT cleaning and security scheme's coverage and the two Victorian long service schemes (administrators' pages).
- [ ] **NSW and SA quotes come from the corpus copy as at 10 March 2025.** Re-check them against the current text once a source for later NSW changes is found (D2).
- [ ] **NT locators use section headings**, because the NT register's PDFs lose section numbers when read as text. Recover the numbers.
- [ ] **Nothing has been through the AI checking process yet** (E-145). The owner is setting it up in a separate thread; phase G covers this.

**States and councils: coverage**

- [ ] **State and council requirements' regulators** (phase D): only 25 of 135 name a body, so the agencies-per-class counts are mostly Commonwealth for now.
- [ ] **22 state gaps** in `regulation-register/requirement-gaps.json`: 10 to draft, 7 not found, 3 blocked (Victoria), 2 not searched.
- [ ] **Construction long service levies**, a separate obligation on the person for whom building work is done (e.g. NSW s 34). To be recorded as their own family.

**Industry lens (owner's list, 10 Nov 2026)**

- [ ] Regulators' market studies (ACCC, PC) as a cross-check of the market figures (option 4).
- [ ] A structural economic conditions chart for council areas and regions (when the owner asks).
- [ ] Council-level features on the map (when the owner asks).
- [ ] ABLIS API key (owner), then phase F.
