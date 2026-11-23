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
- **D-4c done 14 Nov 2026 (E-162):** the 29 NSW D-4 families searched in the other seven jurisdictions. 92 requirements drafted (Queensland 15, WA 17, SA 14, Tasmania 16, the ACT 14, the NT 15, Victoria 1); 111 cells logged: 75 not found, 24 blocked (Victorian Acts not uploaded) and 12 to draft. The register now holds 629 requirements. Follow-ups (15 Nov 2026, E-164): SA pipelines (Energy Resources Act 2000 ss 10(1)(g), 11) and Victorian building surveyors (Building Act 1993 s 169D(1)) drafted from their to-draft gaps; 631 requirements.
- **D-4e done 16 Nov 2026 (E-166):** 8 more NSW requirements from the screening calls: gaming machine authorisations, wholesale supply of medicines and poisons, pesticide work, building in a mine subsidence district, a club's approved secretary, firearms dealers, weapons dealers and water access licences. 639 requirements. The 8 families are logged as not searched in the other states.
- **D-4f done 16 Nov 2026 (E-167):** 3 NSW Acts read by hand: the casino licence (a cap of 2, s 6(1)), property agents (s 8(1)) and radiation management licences (s 6(2)). 642 requirements.
- **D-4g done 16 Nov 2026 (E-168):** the 11 D-4e and D-4f families searched in the other seven jurisdictions: 16 requirements drafted, 31 to draft, 21 not found, 9 blocked (Victoria). 658 requirements. Follow-ups (E-169): 7 to-draft cells drafted (SA casino; SA and ACT radiation; Qld, WA and NT water; ACT gaming machines); 665 requirements. Second round (E-300, 17 Nov 2026): 12 more drafted; 12 D-4g cells remain to draft.
- **D-4j done 17 Nov 2026 (E-301):** 35 high-signal NSW Acts screened; 5 requirements drafted (non-government schools, gas reticulation, land surveyors, offshore minerals, racecourses); 14 more called Y to draft, 4 L and 13 N. 725 requirements.
- **D-4k done 17 Nov 2026 (E-302):** 6 more NSW requirements: legal practice, architects, explosives, gaming machine tax, community services portable long service leave and onshore petroleum titles. 731 requirements.
- **D-4l done 18 Nov 2026 (E-303):** the 11 D-4j and D-4k families searched in the other seven jurisdictions: 48 requirements drafted (Queensland 11, WA 8, SA 8, the ACT 8, Tasmania 7, the NT 5, Victoria 1); 29 cells logged: 12 not found, 9 blocked (Victorian Acts not uploaded) and 8 to draft. 779 requirements.
- **D-4m done 18 Nov 2026 (E-304):** 5 NSW requirements from Acts called Y but not drafted: point of consumption tax on wagering (Betting Tax Act 2001 s 13C, above $1 million of net NSW wagering revenue), depositing rental bonds (Residential Tenancies Act 2010 s 162(1)), notifying a land lease community (s 16) and its disclosure statement (s 21), and retirement village inquiry and disclosure documents (Retirement Villages Act 1999 s 18). The public lotteries licence and electronic lodgment network operators are noted as worth looking at again. 784 requirements.
- **D-4n done 18 Nov 2026 (E-305):** 6 NSW requirements: the heavy vehicle chain of responsibility primary duty (Heavy Vehicle National Law s 26C(1)), combat sport promoters (s 20(2)), water bore drillers (Water Act 1912 s 118A(1)), licensed premises for anatomical examination (s 14), registration with AEMO to generate or run networks in the national electricity market (National Electricity Law s 11(1), (2)) and energy retailer authorisation (National Energy Retail Law s 88(1)). The 72 high-signal NSW Acts not yet called were screened: 6 called Y, 66 N. Vehicle registration and motor vehicle tax are noted as worth looking at again. 790 requirements.
- **D-4o done 18 Nov 2026 (E-306):** the 73 high-signal NSW regulations not yet called were screened (7 Y, 44 L, 22 N), and 10 NSW requirements drafted from them or their Acts: food safety scheme licences (Food Regulation 2015 cl 41), food safety supervisors (Food Act 2003 s 106C(1)), licences for vehicles carrying dangerous goods in bulk (s 220(1)), the waste levy (Protection of the Environment Operations Act 1997 s 88(2)), cemetery operator licences (s 4B(3)), complying mortuaries (s 76(1)), cooling water system risk assessments (ss 12(3), 13(2)), animal display establishment licences (Exhibited Animals Protection Act 1986 s 12(1)), annual fire safety statements (s 89(1)) and licensed specialist work at coal mines (s 154(1)). The 35 high-signal council local environmental plans are left to the council phase. 800 requirements.
- **D-4p done 18 Nov 2026 (E-307):** the 11 D-4m and D-4n families searched in the other seven jurisdictions: 45 requirements drafted (Queensland 9, SA 8, WA 8, Tasmania 8, the ACT 7, the NT 5); 32 cells logged: 19 not found, 11 blocked (Victorian Acts not uploaded) and 2 to draft. Tasmania and the ACT apply the Heavy Vehicle National Law, the National Electricity Law and the National Energy Retail Law from another state's text, so those requirements quote the host text and cite the application law, as the rail requirements do. 845 requirements.
- **D-4q done 18 Nov 2026 (E-308):** the 10 D-4o families searched in the other seven jurisdictions: 26 requirements drafted (Queensland 6, Tasmania 6, SA 4, the ACT 3, Victoria 3, WA 2, the NT 2); 44 cells logged: 34 not found, 6 blocked (Victorian laws not uploaded) and 4 to draft. 871 requirements.
- **D-4r done 18 Nov 2026 (E-309):** the 37 cells of 8 older families still logged as not searched: 3 drafted (SA refund-marked drink containers, s 69B(2); WA's fixed daily fuel price, reg 3; Tasmania's information duty for short stays, s 6(1)), 33 logged not found and 1 to draft (NSW short-term rental registration, in the Fair Trading Regulation 2019). No state has a moratorium on takeaway liquor licences, but several restrict where packaged liquor licences may be granted (noted as worth looking at again). No cell is now logged as not searched. 874 requirements.
- **D-4s done 18 Nov 2026 (E-310):** the NSW medium band: 425 medium-signal NSW laws not yet called were screened (20 Y, 59 L, 346 N); the 146 medium-signal council local environmental plans are left to the council phase. 18 NSW requirements drafted: pawnbroker and second-hand dealer licences, animal research accreditation, approval of declared electrical articles, boarding house notification, funeral contribution funds, fundraising authorities, qualified hairdressers, the parking space levy, the emergency services insurance contribution, tobacco retailer notification, contaminated land notification, the ethanol mandate, pool barriers, unclaimed money returns, apprenticeship registration, health record retention and poppy licences. 892 requirements.
- **D-4t done 18 Nov 2026 (E-311):** the 18 D-4s families searched in the other seven jurisdictions: 41 requirements drafted (Tasmania 9, SA 8, WA 8, Queensland 6, the ACT 5, the NT 4, Victoria 1); 85 cells logged: 56 not found, 14 blocked (Victorian Acts not uploaded) and 15 to draft. 933 requirements.
- **D-4u done 18 Nov 2026 (E-312): NSW screening complete.** The 733 low-signal NSW laws not yet called (other than council plans) were screened: 46 had a licensing-style offence, most in public-body Acts; 5 called Y, 7 L, 721 N. 3 NSW requirements drafted: supporting statements with head contractors' payment claims (Building and Construction Industry Security of Payment Act 1999 s 13(7)), notice before workplace surveillance (Workplace Surveillance Act 2005 s 10) and licensed motor vehicle racing grounds (Motor Vehicle Sports (Public Safety) Act 1985 s 8(1)). Every NSW law in the catalogue now has a call, except the 195 council and planning instruments left to the council phase and the 606 set aside by triage. 936 requirements.
- **Responsible parties and traceability done 18 Nov 2026 (E-313).** Every state, territory and Commonwealth requirement now names who administers it (933 of 936; 3 NSW laws name no body), each body quoted from the requirement's own law. Every source has a locator, and every source on a legislation register names the version it quotes. `scripts/check_traceability.py` keeps it so.
- **D-5a done 18 Nov 2026 (E-314): Queensland's high band called; 6 Queensland requirements.** The 12 Queensland cells logged 'to draft' were read by hand: 6 drafted (pawnbroker and second-hand dealer licences, Second-hand Dealers and Pawnbrokers Act 2003 s 6; registration of electrical equipment suppliers, Electrical Safety Regulation 2013 ss 143, 144; charitable appeals, Collections Act 1966 s 10(1); unclaimed money, Public Trustee Act 1978 ss 100, 102; supply of medicines and poisons, Medicines and Poisons Act 2019 s 35(1)), 2 logged as not found, 1 blocked and 3 left to draft. The 170 high-signal Queensland laws not yet called are called (28 Y, 52 L, 87 N, plus 3 drafted). 19 Y calls are to draft in D-5b, including two families missing from the whole register: electrical licences and labour hire licences. 942 requirements.
- **D-5b and D-5c done 18 Nov 2026 (E-315, E-316): 16 Queensland requirements.** Drafted first for Queensland, from D-5a's 'to draft' calls: electrical contractor licences and licensed electrical workers (Electrical Safety Act 2002 ss 56(1), 55(1)); labour hire licences (Labour Hire Licensing Act 2017 s 10(1)); introduction agents (Introduction Agents Act 2001 s 18); inbound tour operators (Tourism Services Act 2003 s 12(1)); drinking water quality management plans (Water Supply (Safety and Reliability) Act 2008 s 92); project trust accounts (Building Industry Fairness (Security of Payment) Act 2017 s 18); casino employee licences (Casino Control Act 1982 s 34(1)); registered agricultural chemicals only (Chemical Usage (Agricultural and Veterinary) Control Act 1988 s 13A(1)); dog breeder registration (Animal Management (Cats and Dogs) Act 2008 s 43E(2)); regional interests development approvals (Regional Planning Interests Act 2014 s 19(1)); commercial activity permits in recreation areas (Recreation Areas Management Act 2006 s 111(1)); stock route travel permits (Stock Route Management Act 2002 s 132); biodiscovery collection authorities (Biodiscovery Act 2004 s 50(1)); and the cultural heritage duty of care (both 2003 cultural heritage Acts, s 23(1)). Queensland's racing bookmaker licence joins the bookmaker family (Racing Integrity Act 2016 s 70). The 15 new families are logged as not searched in the other seven jurisdictions. 958 requirements.
- **D-5d done 18 Nov 2026 (E-317): 18 new families searched in the other jurisdictions; 33 requirements.** Electrical contractor licences (SA s 6(1), WA reg 33(1), Tasmania s 21, the ACT s 82(1), the NT s 66(1)) and licensed electrical workers (NSW s 14(1), SA s 13, Tasmania s 22(1), the ACT s 84(1), the NT s 65(1)); labour hire licences (SA s 11(1), ACT s 23); drinking water quality programs (NSW s 25(1), SA ss 5, 12); retention money trust accounts (WA s 74); casino employee licences (NSW s 44, Tasmania s 50(1), ACT s 41(1)); registered agricultural chemicals only (NSW s 13(1), SA s 6(1), Tasmania s 18(1), and label use in the NT s 22(1)); dog and cat breeders (SA s 69(1), ACT s 72(1)); business licences in Tasmanian reserves (s 38(1)); stock on public roads (NSW s 73); bioprospecting permits (NT s 38(1)); Aboriginal heritage protection (NSW s 86(2), WA s 17, SA s 23(1), Tasmania s 9(1), NT sacred sites s 34(1)); and workplace surveillance notices (ACT s 13(1)). 93 cells logged. 991 requirements.
- **D-5e and D-5f done 18 Nov 2026 (E-318, E-319): Queensland's medium band called; 11 requirements.** 266 medium-signal laws called: 19 Y, 92 L, 155 N. Drafted first for Queensland: aerial chemical distribution under licence (Agricultural Chemicals Distribution Control Act 1966 s 39(1)); generation and transmission authorities (Electricity Act 1994 ss 87(1), 88(1)); farm debt mediation before enforcing a farm mortgage (Farm Business Debt Mediation Act 2017 s 12(1)); marine park authorities (Marine Parks Act 2004 s 44(1)); trust accounts for trust money (Trust Accounts Act 1973 s 7(1)); valuer registration (Valuers Registration Act 1992 s 63(1)); land sales disclosure (Land Sales Act 1984 s 10(1)); resource financial provisioning (Mineral and Energy Resources (Financial Provisioning) Act 2018 s 47(1)); recreational water safety (Safety in Recreational Water Activities Act 2011 s 16(1)); funeral price display (Fair Trading (Funeral Pricing) Regulation 2022 s 4(1)); and the employment agents' code (Private Employment Agents (Code of Conduct) Regulation 2015 s 4(1)). 1,002 requirements.
- **D-5g done 18 Nov 2026 (E-320): Queensland's low band called; 3 requirements.** 436 low-signal laws called: 4 Y, 81 L, 351 N. Every Queensland law in the catalogue now has a call except the 55 set aside by triage. Drafted first for Queensland: the fitness industry code of practice (Fair Trading (Code of Practice—Fitness Industry) Regulation 2003 s 5(1)); accommodation for resident pastoral workers (Pastoral Workers' Accommodation Act 1980 s 8(1)); and fuel price reporting (Fair Trading (Fuel Price Reporting) Regulation 2018 s 6(1)). 1,005 requirements.
- **D-5h done 18 Nov 2026 (E-321): the 14 D-5f and D-5g families searched in the other jurisdictions; 31 requirements.** Drafted: aerial spraying (WA, Tas, NT); generation and transmission licences (NSW, WA, SA, Tas, ACT, NT); farm debt mediation (NSW, SA, Tas); SA marine park zone limits; valuers (WA, SA, Tas); off-the-plan and strata disclosure (NSW, WA); mine rehabilitation funds (WA, SA, NT); funeral price display (NSW, WA); fitness codes (WA, SA); fuel price reporting (NSW, SA, Tas); employment agent licences (WA, SA, a new family); and WA business on CALM land (correcting D-5d). 76 cells logged (69 not found, 7 blocked). 1,036 requirements.
- **D-5i done 18 Nov 2026 (E-322): 2 Queensland requirements.** The site senior executive's safety and health management system for coal mines and other mines and quarries (one family, two Acts), and accommodation for resident workers (Workers' Accommodation Act 1952 s 12(1)). 1,038 requirements.
- **D-5j done 18 Nov 2026 (E-323): mine safety management systems in the other states; 4 requirements.** NSW (cl 18(1)), WA (reg 621(1)), SA (reg 621(1)) and Tasmania (s 20(1)); Victoria blocked; the ACT and the NT not found. 1,042 requirements.
- **D-5k done 18 Nov 2026 (E-324): commercial fishing and aquaculture; 10 requirements.** Commercial fishing licences for Queensland (s 82 and the regulation's sch 1), Tasmania (s 60(1)) and the NT (s 10), replacing D-4's 'not found' cells; a new family, aquaculture authorities, in every jurisdiction but Victoria (blocked). 1,052 requirements.
- **D-6a done 18 Nov 2026 (E-325): WA's 'to draft' cells; 10 requirements.** Environment protection, radiation, tobacco retail and wholesale, electrical work, casino employees, firearms dealing, charitable collections, unclaimed money, medicines and poisons, and rail accreditation. Bookmakers and dangerous goods vehicles are still to draft. 1,062 requirements.
- **D-6b done 18 Nov 2026 (E-326): WA's high band called; 6 requirements.** Cat breeders, veterinary premises and licensed racecourses (earlier 'not found' cells), and three WA-first families: public aquatic facility permits, lobbyist registration and the construction industry training levy. 1,068 requirements.
- **D-6c done 18 Nov 2026 (E-327): WA's medium band called; 5 requirements.** Abattoir approval and licensed crematoria (earlier 'not found' cells), and three WA-first families: auctioneer licences, pearling and hatchery licences, and industrial hemp licences. 1,073 requirements.
- **D-6d done 18 Nov 2026 (E-328): WA's low band called; WA fully called; 1 requirement.** 763 low-signal laws called; dangerous goods vehicle licences drafted (reg 215(2)). Every WA law now has a call except those set aside by triage. Bookmaker licences remain to draft. 1,074 requirements.
- **D-6e done 19 Nov 2026 (E-329): the six WA-first families in the other jurisdictions; 14 requirements.** Public pools (NSW, SA), lobbyists (Qld), construction training levies (SA, Tas, ACT), auctioneers (NSW, Qld, Tas, ACT, NT) and industrial hemp (NSW, SA, Tas). 28 cells logged (21 not found, 4 to draft, 3 blocked). 1,088 requirements.
- **D-7a done 19 Nov 2026 (E-330): SA's 'to draft' cells and high band; 7 requirements.** Cemeteries and crematoria, dangerous goods vehicles and apprentice employers (SA cells), and four SA-first families: declared air route licences, hydroponic equipment dealers, petroleum products licences and dangerous substances storage licences. 129 high-signal laws called. 1,095 requirements.
- **D-7b and D-7c done 19 Nov 2026 (E-331): SA's medium (280) and low (519) bands called; SA fully called.** No new requirement; the medium band's licensing duties support requirements already recorded. 1,095 requirements.
- **D-7d done 20 Nov 2026 (E-332): the four SA-first families in the other jurisdictions; 1 requirement.** NSW intrastate air passenger licences (s 3(1)). 27 cells logged (23 not found, 2 to draft, 2 blocked). 1,096 requirements.
- **D-8a done 20 Nov 2026 (E-333): Tasmania's 'to draft' cells; 8 requirements.** Public health risk activities, education and care services, gaming machines, wholesale poisons, water licences, explosives permits, onshore petroleum production and poppy grower's licences. 1,104 requirements.
- **D-8b done 20 Nov 2026 (E-334): Tasmania's high band called; 5 requirements.** Cat breeders (an earlier 'not found' cell) and four Tasmania-first families: child care licences, licences to trade in protected wildlife, deer farm licences and GMO-free area permits. Second laws on the fishing and explosives requirements. 71 high-signal laws called. 1,109 requirements.
- **D-8e done 20 Nov 2026 (E-335): the four Tasmania-first families in the other jurisdictions; 10 requirements.** Child care licences (NSW, Qld, WA, ACT), protected wildlife trade (NSW, WA, SA, ACT) and GM crop bans (SA, ACT). 18 cells logged (12 not found, 2 to draft, 4 blocked). 1,119 requirements.
- **D-8c done 20 Nov 2026 (E-336): Tasmania's medium band called; 3 requirements.** 246 laws called (7 Y, 36 L, 203 N); three Tasmania-first families: written residential building contracts, certified forest practices plans and non-emergency patient transport licences. 1,122 requirements.
- **D-8f done 20 Nov 2026 (E-337): the D-8c families in the other jurisdictions; 6 requirements.** Written building contracts (NSW, Qld, WA, SA) and patient transport licences (SA, ACT). 15 cells logged (10 not found, 2 to draft, 3 blocked). 1,128 requirements.
- **TD-1 done 20 Nov 2026 (E-338): two older 'to draft' cells; 2 requirements.** SA explosives (Explosives Act 1936 ss 12(1), 23(1); the 2024 Act has not come into operation) and NSW private native forestry plans (s 60ZW(1)). 1,130 requirements.
- **D-8d done 20 Nov 2026 (E-339): Tasmania's low band called; Tasmania fully called.** 810 laws called; no new requirement. Every Tasmanian law now has a call except those set aside by triage. 1,130 requirements.
- **D-9a done 23 Nov 2026 (E-340): the ACT's 'to draft' cells; 8 requirements.** Pool barriers, licensable public health risk activities, education and care services, firearms dealers, conveyance duty, explosives licences, dangerous goods vehicles and home warranty cover. 1,138 requirements.
- **TD-2 done 23 Nov 2026 (E-341): two older 'to draft' cells; 2 requirements.** WA dangerous goods site licences (reg 25(1)) and SA residential park particulars (s 135(2)). 1,140 requirements.
- **D-9b and D-9c done 23 Nov 2026 (E-342): two ACT-first families; 2 requirements.** The short-term rental accommodation levy and the utilities network facilities tax; searched elsewhere by title (13 not found, Victoria blocked). 1,142 requirements.
- **D-9d and D-9e done 23 Nov 2026 (E-343, E-344): from the ACT's low band; 4 requirements.** ACT controlled sports registration (an earlier 'not found'), two ACT-first families (property developer licences, energy savings obligations) and SA's Retailer Energy Productivity Scheme; clinical waste transport as a second law. 1,146 requirements.
- **D-9f and D-9g done 23 Nov 2026 (E-345, E-346): gas appliance approval; 6 requirements.** An ACT-first family, drafted also for NSW, Qld, WA, SA and Tasmania; the property developer licence gains its development application rule. 1,152 requirements.
- **D-9h done 23 Nov 2026 (E-347): the ACT fully called.** 440 laws called (17 Y, 105 L, 318 N). Every ACT law now has a call except the 55 set aside by triage. 1,152 requirements.

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
