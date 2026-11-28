# Plan for councils (phase E)

*Part of the [legislation-links plan](plan_legislation_links.md), phase E. Drafted 25 November 2026, after the state phase (D-1 to D-12). Approved by the owner on 26 November 2026 (E-360). Victoria's councils wait until the Victorian state batch.*

## Goal

Record the requirements that councils place on businesses, and show how much they differ from one council to the next. The plan has 3 strands, as set in the legislation-links plan:

1. **Planning land-use terms.** For each state, match each of the 506 industry classes to the land-use terms in the state's planning scheme, such as "shop", "light industry" or "food and drink premises". These terms decide where a business may set up and what approval it needs.
2. **State permits that councils issue.** Mark every state requirement that councils administer, such as food business registration and skin penetration premises.
3. **Councils' own local laws.** Collect the local laws and by-laws for a sample of councils, measure how much they vary, then decide whether to cover all of them (decision D4).

A permit that every council issues under a state Act stays one state requirement, marked as council-administered. It is not counted once for each council (methods rule 7). Only requirements made by a council, under a local law, a by-law or a planning scheme the council makes, are filed as council requirements.

## Where we start

- **20 council requirements:** outdoor dining, busking and filming permits in the 7 capital cities, filed under `regulation-register/requirements/local/<ABS LGA code>/` (calibration batch 5). Brisbane's outdoor dining permit is still at medium confidence until its local law is quoted.
- **8 state requirements marked as council-administered**, of 1,200. ABLIS's sample found that 83% of its services were council-administered (see the [estimate](estimate_legislation_links.md)), so this flag is probably under-recorded.
- **Council instruments set aside in the state phase:**
  - NSW: 179 local environmental plans in the NSW catalogue, of 195 council and planning instruments left uncalled;
  - NT: 40 council by-laws on the NT register, such as the Alice Springs (Management of Public Places) By-laws 2009;
  - the other states' registers hold almost no council local laws.
- **Regimes:** 14 council layers in the 61 regimes. Local government counts as one party per regime.
- **Phase B's estimate** for planning terms and 21 sample councils: about 337 requirements (range 220 to 485) and about 15 hours in session (5 to 31). Covering every council would add about 8,700 local-law requirements (5,700 to 12,500), which is feasible only with the ABLIS API key.

## Where the law comes from

| State | Planning scheme and land-use terms | Councils' local laws | Can we reach it now? |
|---|---|---|---|
| NSW | The Standard Instrument local environmental plan's dictionary, and each council's local environmental plan | NSW councils approve activities under s 68 of the Local Government Act 1993 and their local approvals policies, not local laws | LEPs: corpus copy (as at 10 March 2025). The NSW register and the planning portal are not reachable |
| Queensland | Planning Regulation 2017, schedule 3 (regulated definitions), and each council's planning scheme | Each council's local laws, on its own website | The register is reachable. Council websites are not |
| WA | Planning and Development (Local Planning Schemes) Regulations 2015 (model provisions), and each council's local planning scheme | Local laws are published in the Government Gazette | The register and the Gazette are reachable |
| SA | One planning code for the whole state (the Planning and Design Code) | Each council's by-laws | PlanSA and council websites are not reachable |
| Tasmania | One set of planning provisions for the whole state, with a local provisions schedule for each council | Each council's by-laws | The Gazette, the planning site and council websites are not reachable |
| NT | One planning scheme for the whole territory | Council by-laws, many on the NT register | Register: reachable |
| ACT | The Territory Plan (there are no councils) | None | ACT register: reachable |
| Victoria | One set of planning provisions for the whole state, with each council's planning scheme | Each council's local laws | Waits for the Victorian batch |

For every council, ABLIS's public pages give each permit's legal basis, including the local law. The site is not built for bulk reading, so we read only the pages we need, and its copyright allows only unaltered, non-commercial reproduction.

The ABLIS API key would allow every council to be covered. Whether the API carries council services is the first thing to test when the key arrives ([ABLIS brief](ablis_brief.md)).

**To verify in batch E-1:** each state's planning terms instrument named above, and where each sample council publishes its local laws. These are listed from what earlier phases found, not yet checked against the instruments.

## The sample (decision D4)

There are 3 councils in each state: the capital city, a regional city and a rural council. That makes 21 councils, or 18 without Victoria. The 7 capital cities are already chosen (ABS LGA codes 17200, 24600, 31000, 40070, 57080, 62810, 71000).

Rule for the other 2 in each state, so the choice can be repeated:
- **Regional city:** the council with the most businesses outside the state's greater capital city area and outside the ABS major cities class, from ABS counts of businesses by local government area. The major cities test was added in E-1 (E-361), because without it the rule picked Newcastle and the Gold Coast.
- **Rural council:** in each state, the council with the median number of businesses among those in outer regional, remote or very remote areas.

All codes are checked against ASGS 2021.

## Method

The Commonwealth and state rules apply (methods rules 1 to 13), with these changes:

1. **Council requirements** are tier `local` and filed under the ABS LGA code. Each one quotes the local law, by-law or planning provision and gives its official link. An ABLIS listing alone gives medium confidence (rule 5a) until the law itself is quoted.
2. **Families across councils.** A requirement found in one sample council is searched for in the other 20. Each result is either drafted or logged in `requirement-gaps.json`, with the council as the cell.
3. **Land-use terms** go in one table, `data/processed/legislation/land_use_terms.csv`, with columns for the state, the ANZSIC class, the term, the instrument and its locator, and a confidence level. A class can match more than one term. Each match quotes the term's definition. Where a scheme names a use the class covers, the match is direct. Otherwise it is judged from the definition, and the confidence level shows this.
4. **Council-administered flag.** The 1,200 state requirements are swept again, and `administered_by_councils` is set wherever the law or the state's guidance names councils as issuing or enforcing it. Each change is quoted.
5. **Variation measure.** For each family across the sample councils, the note records:
   - how many councils have the requirement;
   - whether its trigger and fee differ;
   - whether the same activity needs a different approval in different councils.

   This feeds decision D4 on covering every council.
6. **Checks** in every batch: `alicia validate`, every quote re-found in its source, the tests, the link and agency tables rebuilt. Everything stays a draft for the AI checking process (E-145).

## Batches

| Batch | What | Needs |
|---|---|---|
| **E-1** | Check what each source holds. Choose the 14 non-capital sample councils by the rule above (12 without Victoria). Ask for the network hosts the batches need | ABS business counts by local government area |
| **E-2** | The council-administered flag across the 1,200 state requirements (strand 2) | Nothing new: the state law texts are already cached |
| **E-3** | Land-use terms in the states whose instruments we can reach now: Queensland, WA, NT, ACT and NSW (corpus copy) | Reachable now |
| **E-4** | Land-use terms for SA and Tasmania | PlanSA and Tasmania's planning hosts allowed, or the owner saves the documents |
| **E-5** | Local laws for the capital cities: quote the local law behind each of the 20 existing requirements, then extend to each capital city's other local laws that apply to businesses | Council hosts allowed, or the owner saves the local laws (4 capital-city sites refuse automated requests) |
| **E-6** | Local laws for the 12 regional and rural councils, family by family across all 18 councils | As for E-5 |
| **E-7** | Quality check, variation note and the D4 decision on covering every council | Results of E-5 and E-6 |
| **Later** | Victoria's 3 councils and its planning provisions, with the Victorian state batch. All other councils, if D4 says yes | Victorian uploads. ABLIS API key |

E-2 and E-3 can start straight away. E-5 and E-6 depend on reaching council websites.

## Outputs

- Council requirements in `regulation-register/requirements/local/<LGA code>/`, linked to classes in `links.csv.gz`.
- `data/processed/legislation/land_use_terms.csv` (class by state by land-use term), with its entry in `data/SOURCES.md`.
- A short variation note in `docs/` for the D4 decision.
- Council layers updated in the regimes, and councils added to the agency counts.

## Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| E1 | Use the 3 strands and the batch order above, with E-2 and E-3 first? | Yes |
| E2 | Choose the regional and rural councils by the rule above, rather than naming them by hand? | Yes, so the sample can be repeated and defended |
| E3 | Council websites and planning portals are blocked in the cloud. Allow each sample council's host when E-1 lists them (about 20 hosts), or save the local laws yourself? | Allow the hosts. Saving the files by hand is the fallback for sites that refuse automated requests |
| E4 | Leave Victoria's councils until the Victorian state batch? | Yes, as you asked on 25 November 2026 |
| E5 | Decision numbers for this phase: continue the states range from E-360? | Yes, so the states range E-300 to E-399 stays with one thread |

**Answers (owner, 26 November 2026):** E1 to E5 accepted as recommended. The owner asked for all council hosts to be allowed rather than saving files, and for E-1 and E-2 to start (E-360).

## Progress

- **E-1 done 26 Nov 2026 (E-361).** The sample was chosen by `alicia/scripts/council_sample.py` from ABS counts of businesses at 30 June 2025 and the ASGS 2021 allocation files. It is saved in `data/processed/legislation/council_sample.csv`.

  | State | Capital | Regional | Rural |
  |---|---|---|---|
  | NSW | Sydney (17200) | Shoalhaven (16950) | Temora (17350) |
  | Queensland | Brisbane (31000) | Toowoomba (36910) | Winton (37400) |
  | SA | Adelaide (40070) | Alexandrina (40220) | Mount Remarkable (44830) |
  | WA | Perth (57080) | Busselton (51260) | Victoria Plains (58540) |
  | Tasmania | Hobart (62810) | Launceston (64010) | Break O'Day (60210) |
  | NT | Darwin (71000) | Alice Springs (70200) | Victoria Daly (74550) |
  | Victoria (later) | Melbourne (24600) | Ballarat (20570) | Gannawarra (22250) |

  The owner allowed the hosts of these councils and of the planning sites and gazettes on 26 Nov 2026. A check on that day found 3 kinds of site:
  - **Readable:** Sydney, Brisbane, Darwin, Shoalhaven, Temora, Toowoomba, Winton, Busselton, Victoria Plains, Launceston, Hobart, Break O'Day and Victoria Daly; the WA Gazette (on the WA register), wa.gov.au (WA scheme texts) and the ABS;
  - **Refused by the site's bot protection, even when allowed:** Perth, Adelaide, Alexandrina, Mount Remarkable, PlanSA and the Planning and Design Code, Tasmania's planning site and Gazette, the SA Government Gazette and Tasmania's council by-laws directory. For these, the fallback is ABLIS's listing (which names each permit's local law) and the councils' documents where a search finds a direct link;
  - **Redirected to a host not yet allowed:** Alice Springs (www.alicesprings.nt.gov.au) and the NSW planning portal (www2.planning.nsw.gov.au). These go in the next host request.

  So SA is the hardest state: all 3 SA councils, PlanSA and the SA Gazette refuse automated requests.
- **E-2 done 26 Nov 2026 (E-362).** The 834 state requirements outside Victoria were searched for laws that make councils an issuing, registering or enforcing body. 26 more requirements are now marked as council-administered (34 in all, of 1,200): 23 that already quoted the law naming councils, and 3 with a new quote (NSW food safety supervisors, Food Act 2003 s 111(4); WA development approval, Planning and Development Act 2005 s 4; Tasmanian cooling water systems, Public Health Act 1997 s 114(1)). Definitions alone, such as "local authority" in the WHS Acts, did not count.

- **E-3 done 26 Nov 2026 (E-363).** `alicia/scripts/land_use_terms.py` reads the standard land-use definitions of Queensland (Planning Regulation 2017, schedules 3 and 24: 91 use terms), WA (model provisions, schedule 1 cl 38: 77 terms), NSW (the Standard Instrument definitions in the Shoalhaven LEP 2014 dictionary: 190 terms) and the ACT (Territory Plan 2023, Part G, Table 1: 131 terms). Every quote is checked word for word against its source. Each of the 506 classes is matched to the terms through about 100 use types, in `data/processed/legislation/land_use_terms.csv` (2,673 rows: 985 high, 833 medium and 750 low confidence, and 105 with no premises use or no standard term). Definitions are in `land_use_definitions.csv`.
  - **Not covered:** the NT, whose planning scheme site (nt.gov.au) refuses automated requests even when allowed, and SA and Tasmania (batch E-4), for the same reason. Victoria waits for its batch.
  - **Limits:** the match says which term a class most likely falls under, not whether the use is allowed in a zone. Queensland's industry terms (low, medium, high impact) depend on thresholds each council sets, so those matches are low confidence. Mining is not a Queensland planning use.

- **E-5 done 27 Nov 2026 (E-364).** Capital-city local laws outside Victoria.
  - **Quoted:** the local law behind 7 of the 13 existing permits. Darwin outdoor dining (by-law 96), Brisbane busking, outdoor dining and filming (Public Land and Council Assets Local Law 2014; Footpath Dining Local Law 2011), Sydney filming (Local Government Act 1993 ss 114 and 115), and Perth busking and outdoor dining (from the Government Gazette). 4 are now high confidence. Brisbane filming stays medium because the local law does not name filming. Perth stays medium because only the law as made could be read.
  - **New:** 5 requirements. Darwin street food (by-law 106) and market licence (by-law 108), Brisbane street trading (s 23, sch 2) and advertising signs (Advertising Devices Local Law 2021 s 40), and Perth street trading (Public Trading Local Law 2005 cll 3.1 and 3.2). The register now holds 25 local requirements.
  - **Not done:** Adelaide (its website and the SA Gazette refuse automated requests) and Hobart (its Public Spaces By-law is a scanned image with no text layer). Perth filming has no matching provision in the Local Government Property Local Law 2005. Sydney's other approvals (goods on footways, mobile food vending) are made under s 68 of the state Act, so by methods rule 7 they belong with the NSW state requirements, not here.

- **E-6 done 27 Nov 2026 (E-365).** Local laws of the regional and rural sample councils. 11 requirements are new, and the register now holds 36 local requirements.
  - **Winton (Qld):** 4 approvals under the model Local Law No. 1 (Administration) 2011 and the council's 2024 subordinate local law. They cover trading on council land or roads, advertising signs, caravan parks, and temporary entertainment events of 250 people or more.
  - **Toowoomba (Qld):** approval to trade on council land, from its Subordinate Local Law No. 1.2 (2020). Trading on a council road next to the business's own premises needs no approval if it meets set standards, including $10 million of public liability insurance. This is medium confidence because the authorising local law could not be found online.
  - **Busselton (WA):** 4 permits under its 2026 trading local law. They cover advertising signs on roads, stalls and trading, busking, and outdoor dining.
  - **Victoria Plains (WA):** 2 licences, one to trade on council property and one for temporary signs and trade displays. Two small signs need no licence.
  - **Not done:**
    - Launceston and Alice Springs publish their by-laws as scanned images with no text layer. Reading them would need a text-recognition tool, which this environment does not have.
    - Break O'Day's site did not respond (502).
    - Alexandrina and Mount Remarkable refuse automated requests.
    - Victoria Daly publishes no by-laws.
    - Shoalhaven and Temora approve these activities under s 68 of the state Act, so by methods rule 7 they belong with the NSW state requirements.

## Limits

- A sample of 21 councils, from about 540 in total, shows how much councils vary. It cannot give a complete count for every council.
- Planning terms decide where a use is allowed, not whether a given site is approved. Zoning maps and approval outcomes are out of scope.
- The NSW local environmental plans are corpus copies as at 10 March 2025.
- Council fees change every year. Fees are recorded with their date, as values, not as requirements.
