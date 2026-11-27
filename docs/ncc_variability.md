# How the National Construction Code varies across states and territories

Methods note, 27 November 2026, for the owner and Cowork. Built by `alicia/scripts/ncc_data.py` (plan: [`plan_ncc_ingestion.md`](plan_ncc_ingestion.md)). All figures are counts from official Australian Building Codes Board (ABCB) data. No figure here has been checked by a person.

> **Attribution.** The National Construction Code 2025 was provided by the Australian Building Codes Board under the CC BY 4.0 licence. The NCC 2022 dataset carries the same licence: NCC 2022 Amendment 1 changed it from CC BY-ND to CC BY (data.gov.au read-me, read 27 November 2026).

## Summary

- **One code, adopted 8 ways.** The National Construction Code (NCC) is a single national code, but each state and territory gives it legal effect through its own law and writes its own variations into it.
- **States vary hundreds of provisions.** In NCC 2025, Tasmania varies 274 provisions and New South Wales 272. South Australia varies 149, the Northern Territory 135, Victoria 72, Western Australia 56 and Queensland 30. The ACT's count is 0 because it publishes its variations separately, not because it has none.
- **Adoption dates moved together until NCC 2025, but key provisions did not.** From 2002 to NCC 2022, every jurisdiction adopted each edition on the national date, except the ACT's month-late start for NCC 2019. NCC 2025 broke the pattern: New South Wales, Queensland and South Australia (for building) adopt it a year late, on 1 May 2027, and the Northern Territory has not adopted it.
- **The 2022 energy and accessibility changes split 8 ways.** States brought in the NCC 2022 energy efficiency, condensation and livable housing provisions on 5 different dates between October 2023 and May 2025 (Queensland's 2 dates, from the Queensland Building and Construction Commission, are among them). New South Wales and Western Australia did not adopt livable housing, Tasmania did not adopt housing energy efficiency, and the Northern Territory kept housing at 5 stars.

## Sources and method

| Table (`data/processed/ncc/`) | Source | What it holds |
|---|---|---|
| `adoption_history.csv` | NCC 2025 dataset v1.2 ([data.gov.au](https://data.gov.au/data/dataset/national-construction-code-2025-version-1-2)), each volume's "History of adoption" table | 711 rows: every edition and amendment of Volumes One, Two and Three since BCA 96, by jurisdiction, with the gap in days from the Commonwealth date |
| `adoption_2022.csv` | ABCB, [NCC 2022 state and territory adoption dates](https://www.abcb.gov.au/ncc-2022-state-and-territory-adoption-dates) (correct as at 22 September 2023) | 40 rows: 8 jurisdictions × 5 provision areas, with the ABCB's wording and the matching register record |
| `adoption_2025.csv` | ABCB, [NCC 2025 state and territory adoption information](https://ncc.abcb.gov.au/ncc-2025/ncc-2025-state-and-territory-adoption-information) | 9 rows: adoption date and transition period (South Australia has separate dates for the building and plumbing codes) |
| `variations.csv` | NCC 2025 dataset v1.2, XML | 1,305 rows: every element the ABCB tags as a state or territory variation, with its type (insert, replace, delete), clause code and technical area |
| `variation_counts.csv` | From `variations.csv` | Provisions varied by volume, jurisdiction and technical area |
| `other_legislation.csv` | Each state's appendix, "Other legislation affecting buildings" | 362 laws by topic, with the administering agency, as each state lists them |
| `referenced_documents.csv` | Schedule 2, "Referenced documents" | 173 standards and other documents the NCC calls up, with the clauses that cite them |
| `regulatory_map.json` | All of the above | Nodes and typed links for the regulatory map (spec in the plan, section 7) |

**Unit of count.** A "provision varied" is a distinct clause code (or table, figure or part) that a jurisdiction inserts, replaces or deletes. Definitions in Schedule 1 are counted separately, because Schedule 1 is repeated in every volume. A clause with several tagged sub-clause changes counts once. The technical area comes from the clause code: the section letter in Volumes One and Three, the H part in Volume Two, and the part number in the Housing Provisions.

## Variations in NCC 2025

**Table 1: provisions varied, by volume and jurisdiction (NCC 2025, excluding definitions)**

| Volume | ACT | NSW | NT | QLD | SA | TAS | VIC | WA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Volume One (Class 2 to 9 buildings) | 0 | 188 | 47 | 12 | 82 | 159 | 26 | 13 |
| Volume Two (Class 1 and 10 buildings) | 0 | 26 | 15 | 9 | 28 | 11 | 5 | 16 |
| Housing Provisions | 0 | 27 | 68 | 3 | 21 | 17 | 1 | 21 |
| Volume Three (plumbing) | 0 | 31 | 5 | 6 | 18 | 87 | 40 | 6 |
| **All volumes** | **0** | **272** | **135** | **30** | **149** | **274** | **72** | **56** |
| Definitions (Schedule 1) | 0 | 30 | 0 | 1 | 11 | 8 | 9 | 4 |

Part A (governing requirements) is shared by the 3 volumes, so its variations are counted in each volume's row.

**How states vary the code differs too.** New South Wales and Tasmania mostly replace national wording (217 and 198 of their tagged changes). The Northern Territory mostly inserts its own provisions (95 of 148), many in energy efficiency and health and amenity for housing. Western Australia never deletes a national provision; the Northern Territory deletes 28.

**Table 2: provisions varied, by technical area (NCC 2025; · means none)**

| Volume | Area | ACT | NSW | NT | QLD | SA | TAS | VIC | WA | States varying |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Volume One | A Governing requirements | · | 4 | · | · | 1 | 3 | 2 | · | 4 |
| Volume One | B Structure | · | 4 | 1 | 3 | 2 | · | 1 | · | 5 |
| Volume One | C Fire resistance | · | 4 | · | · | 5 | · | 1 | · | 3 |
| Volume One | D Access and egress | · | 15 | · | · | 4 | 4 | 4 | · | 4 |
| Volume One | E Services and equipment | · | 10 | 1 | · | 3 | 3 | 1 | · | 5 |
| Volume One | F Health and amenity | · | 6 | 15 | · | 15 | 4 | 10 | 3 | 6 |
| Volume One | G Ancillary provisions | · | 18 | 4 | 4 | 21 | 6 | · | 1 | 6 |
| Volume One | I Special use buildings | · | 91 | · | · | 28 | 136 | 4 | 8 | 5 |
| Volume One | J Energy efficiency | · | 30 | 18 | 4 | · | 2 | · | · | 4 |
| Volume Two | H1 Structure | · | 5 | · | 5 | 2 | · | 1 | · | 4 |
| Volume Two | H2 Damp and weatherproofing | · | 4 | 1 | · | 2 | · | 1 | · | 4 |
| Volume Two | H3 Fire safety | · | 2 | · | · | 1 | · | · | 1 | 3 |
| Volume Two | H4 Health and amenity | · | 1 | 2 | · | 1 | 1 | · | · | 4 |
| Volume Two | H5 Safe movement and access | · | · | · | · | 5 | · | · | · | 1 |
| Volume Two | H6 Energy efficiency | · | 2 | 9 | · | · | 2 | · | · | 3 |
| Volume Two | H7 Ancillary provisions | · | 5 | 2 | 3 | 3 | 4 | · | 1 | 6 |
| Volume Two | H8 Livable housing design | · | 2 | · | · | 1 | · | · | · | 2 |
| Volume Two | H9 Water use | · | · | · | · | · | · | · | 10 | 1 |
| Volume Two | H10 Changes to AS/NZS 3500.3:2021 | · | · | · | · | 8 | · | · | 3 | 2 |
| Housing Provisions | 9 Fire safety | · | 6 | · | · | 10 | · | · | 13 | 3 |
| Housing Provisions | 10 Health and amenity | · | 2 | 27 | · | 5 | 2 | · | · | 4 |
| Housing Provisions | 13 Energy efficiency | · | 14 | 38 | · | 1 | 14 | · | 3 | 5 |
| Volume Three | B Water services | · | 21 | · | 5 | 6 | 13 | 7 | 3 | 6 |
| Volume Three | C Sanitary plumbing and drainage | · | 5 | 2 | · | 8 | 41 | 5 | 2 | 6 |
| Volume Three | E Facilities and ancillary additions | · | · | · | · | · | 29 | 25 | · | 2 |

Housing Provisions parts with 3 or fewer variations in total, and Volume Three Parts A and D, are in `variation_counts.csv`. Section I (special use buildings) holds most of the New South Wales and Tasmanian variations. New South Wales's are mostly about stages, auditorium seating and other entertainment venues; Tasmania's are mostly about food, meat and other premises it regulates in its own way (titles in `variations.csv`).

## Adoption timing

**Edition dates.** The "History of adoption" tables show that adoption dates moved together for 2 decades. Late adoptions are concentrated in BCA 96 and its first 9 amendments, 1997 to 2001 (in Volume One: ACT 6, South Australia 5, New South Wales 3, Northern Territory 3, Victoria 2). From BCA 96 Amendment 10 (2002) to NCC 2022, every jurisdiction adopted on the national date, except the ACT's NCC 2019, a month late, and Tasmania's Amendment 13, shown as 'To Be advised'. The plumbing code (Volume Three, from NCC 2011) had more gaps: Western Australia did not adopt the 2011 to 2014 editions, New South Wales and the Northern Territory not 2011, and the ACT not 2012.

**NCC 2025.** The national date was 1 May 2026.

| Jurisdiction | NCC 2025 (ABCB adoption page) | Transition |
|---|---|---|
| ACT | 1 May 2026 | 12 months |
| New South Wales | 1 May 2027 | None |
| Northern Territory | Not adopted | None |
| Queensland | 1 May 2027 | None |
| South Australia | Building code 1 May 2027; plumbing code 1 May 2026 | None |
| Tasmania | 1 May 2027 (temporarily adopted 1 May to 4 June 2026) | 5 June 2026 to 1 May 2027 |
| Victoria | 1 May 2026 | None |
| Western Australia | 1 May 2026 | 12 months |

**Tasmania applied NCC 2025 for 5 weeks, then went back to NCC 2022.** The Building Act 2016 (Tas) defined the code as the ABCB's series 'as amended or substituted from time to time', so NCC 2025 applied from its publication on 1 May 2026. The [Building Amendment Act 2026](https://www.legislation.tas.gov.au/view/whole/html/asmade/act-2026-006) (Tas), in force from its assent on 5 June 2026, redefined the code as NCC 2022 (as amended to 29 July 2025) until 30 April 2027 and the latest edition from 1 May 2027 (s 5). This explains why the two ABCB sources differ: the adoption page gives 1 May 2027 with the temporary adoption, while the history tables in the NCC 2025 dataset (version 1.2, June 2026) still give 1 May 2026. The tables keep both as published; the register record `tas-ncc-2025-2027` follows the Act.

**NCC 2022 provisions.** The edition date was 1 May 2023 everywhere, but the energy efficiency, condensation and livable housing provisions had their own transitions:

| Provision area | ACT | NSW | NT | QLD | SA | TAS | VIC | WA |
|---|---|---|---|---|---|---|---|---|
| Housing energy efficiency | 15 Jan 2024 | Enhanced BASIX, 1 Oct 2023 | 5-star only, 1 Oct 2023 | See Queensland site | 1 Oct 2024 | Not adopted | 1 May 2024 | 1 May 2025 |
| Apartment energy efficiency | 15 Jan 2024 | Enhanced BASIX, 1 Oct 2023 | Not adopted | See Queensland site | 1 Oct 2024 | Not adopted | 1 May 2024 | 1 May 2025 |
| Commercial energy efficiency | 15 Jan 2024 | 1 Oct 2023 | NCC 2019 Section J, 1 Oct 2023 | See Queensland site | 1 Oct 2024 | 1 Oct 2023 | 1 May 2024 | 1 May 2025 |
| Condensation management | 15 Jan 2024 | 1 Oct 2023 | 1 Oct 2023 | See Queensland site | 1 Oct 2024 | 1 Oct 2023 | 1 May 2024 | 1 May 2025 |
| Livable housing design | 15 Jan 2024 | Not adopted | 1 Oct 2023 | See Queensland site | 1 Oct 2024 | 1 Oct 2024 | 1 May 2024 | Not adopted |

Source: ABCB, correct as at 22 September 2023, shortened. The ABCB's own wording is in `adoption_2022.csv`. The ABCB page refers to the Queensland Modern Homes website for Queensland's dates; that site refuses automated requests. The [Queensland Building and Construction Commission](https://qbcc.qld.gov.au/news/ncc-2022-update) gives them instead: livable housing (accessibility), condensation management and the provisions for future solar, battery and electric vehicle charging equipment from 1 October 2023, and energy efficiency from 1 May 2024, for houses through the Queensland Development Code. The register record `qld-ncc-2022-2024` uses these dates.

## What the counts do not show

- **Rules outside the code.** The counts cover variations written into the NCC. Some states set building rules in their own instruments instead: the Queensland Development Code, the New South Wales BASIX scheme, and the ACT Appendix, which is notified on the ACT Legislation Register. Queensland's low count and the ACT's zero understate how far those jurisdictions depart from the national text.
- **Size of each variation.** A replaced clause may change one word or a whole method of compliance. The counts measure how often states depart from the national text, not by how much, or at what cost.
- **Councils.** Local planning rules that add to the code are not counted.
- **NCC 2022 variations.** The NCC 2022 dataset is published as 11,331 separate XML files in a different format, so this note counts NCC 2025 only. NCC 2022 is still in force in New South Wales, Queensland, South Australia (building), Tasmania and the Northern Territory until each adopts NCC 2025. Counting it is a later step (plan, phase N4b).
- **Effects.** Nothing here estimates an effect on building costs, competition or productivity. A link from variation counts to outcomes would need state-level outcome data and a design that separates the code from everything else that differs between states.

## How this feeds the register

- The register's 8 `ncc-2022-adoption` records can now cite provision-level dates from `adoption_2022.csv` (plan, phase N2).
- A new family for NCC 2025 adoption can be drafted from `adoption_2025.csv`.
- The variation counts give a sourced basis for the market-integration mark that every NCC record carries ("Adopting only part of the national code, or a local version, leaves builders working across states with different rules").
- `regulatory_map.json` joins the laws to the register's catalogues by register id: 190 of the 251 other laws, and all 19 adopting laws, matched a catalogue title.
