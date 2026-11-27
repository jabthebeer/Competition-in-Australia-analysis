# Plan: ingesting National Construction Code data into ALICIA

Plan for the owner. First written 26 November 2026; **revised 27 November 2026** after the owner's answers (DECISIONS E-500). Phases N0, N1, N4 and the regulatory map data are built; the register phases (N2, N3) are next. Results: [`ncc_variability.md`](ncc_variability.md).

**Purpose (owner, 27 November 2026).** Show how unevenly the National Construction Code (NCC) is adopted, so state-based differences come first. Find a middle ground on scope between one item for the whole code and one for each standard. Use the NCC as the first example of a regulatory map: a main law linked to the instruments that sit within it.

## 1. How the NCC appeared in ALICIA before this work

| Where | What | Gap |
|---|---|---|
| `regulation-register/records/*-ncc-2022-*.json` (8 records, family `ncc-2022-adoption`) | One reform per state: adoption of the NCC 2022 energy efficiency (7-star) and livable housing provisions | Generic instruments with no register id (except NSW); one commencement each; Queensland's livable housing date unconfirmed; no `history` |
| `families.json`, `rule-coding.json`, `regimes/building-licensing-and-approvals.json`, `recommendations/building-code-net-benefit-test.json` | Family name, coding, the regime's "state variations" layer, the PC 2025 net-benefit recommendation | NCC 2022 only; the regime's variations layer names no source |
| `regulation-register/requirements/` | Licences, warranty insurance, contracts, pool barriers | **No requirement to build to the code** |

## 2. What the ABCB publishes (checked 27 November 2026)

| Item | Finding | Used |
|---|---|---|
| **Structured data** | The ABCB publishes the NCC as XML on data.gov.au: [NCC 2025 v1.2](https://data.gov.au/data/dataset/national-construction-code-2025-version-1-2) (June 2026, one file per volume, with an XML schema) and [NCC 2022](https://data.gov.au/data/dataset/national-construction-code-ncc-2022) (11,331 fragment files). Every state and territory variation is tagged with its jurisdiction and type (insert, replace, delete) | NCC 2025 in full; NCC 2022 later (N4b) |
| **Licence** | CC BY 4.0, except third-party material, trade marks, images and photographs. NCC 2022 Amendment 1 changed NCC 2022 from CC BY-ND to CC BY. Required attribution: "The National Construction Code 2025 was provided by the Australian Building Codes Board under the CC BY 4.0 licence." | Recorded in `data/SOURCES.md` and `sources.json` |
| **Volumes** | Volume One (Class 2 to 9 buildings), Volume Two (Class 1 and 10) with the ABCB Housing Provisions, Volume Three (the Plumbing Code of Australia), the Livable Housing Design Standard | All read |
| **Adoption history** | Each volume's preface has a "History of adoption" table: every edition since BCA 96, by jurisdiction | `adoption_history.csv` |
| **Adoption pages** | [NCC 2022 adoption dates](https://www.abcb.gov.au/ncc-2022-state-and-territory-adoption-dates) by provision area (as at 22 September 2023); [NCC 2025 adoption information](https://ncc.abcb.gov.au/ncc-2025/ncc-2025-state-and-territory-adoption-information) with transition periods | `adoption_2022.csv`, `adoption_2025.csv` |
| **State appendices** | Each state's schedule names the laws that give the code effect, lists "other legislation affecting buildings" with the administering agency, and lists the state's referenced documents | `other_legislation.csv`, the map |
| **Referenced documents** | Schedule 2 lists 173 standards with the clauses that cite them | `referenced_documents.csv`, the map |
| **Impact analyses** | Regulation impact statements are listed on `ncc.abcb.gov.au/resources`; the NCC 2022 energy efficiency Decision RIS is also on the OIA site | N5 |

Two corrections to the first version of this plan: there is a structured dataset (the first version said none was found), and the ACT publishes its variations in the ACT Appendix on the ACT Legislation Register, not in the NCC text.

## 3. Scope: the middle ground

One item for the whole code hides the state differences; one item per standard would mean hundreds of files. The middle ground has 3 layers:

| Layer | Grain | Where it lives | Count |
|---|---|---|---|
| **Requirement** | One per jurisdiction per code: building to Volume One (Class 2 to 9), building to Volume Two and the Housing Provisions (houses), plumbing to Volume Three | `regulation-register/requirements/<state>/`, families `building-code-class-2-9`, `building-code-housing`, `plumbing-code` | Up to 24 |
| **Technical area** | One per section of each volume (for example Volume One J Energy efficiency, Volume Two H8 Livable housing design) | `variation_counts.csv` and map nodes; each requirement's description names the areas its state varies most | About 40 areas |
| **Provision** | Each varied clause | `variations.csv` and the map, not the register | 1,305 tagged changes |

So the register gains a small number of items a business deals with, and the standards are still accounted for, as sourced data under each item.

## 4. Phases

| Phase | What | Status |
|---|---|---|
| **N0. Access and licence** | Hosts reachable; licence read; `alicia/scripts/ncc_data.py --download` caches the inputs in `data/raw/ncc/` (not committed); `sources.json` records URL, date and SHA-256; `data/SOURCES.md` entry | **Done** |
| **N1. Adoption tables** | `adoption_history.csv`, `adoption_2022.csv`, `adoption_2025.csv` | **Done** |
| **N4a. Variations, NCC 2025** | `variations.csv`, `variation_counts.csv`, method in [`ncc_variability.md`](ncc_variability.md) | **Done** |
| **Map data (beta)** | `regulatory_map.json` (section 7) | **Done**; page to be built by a website-side thread |
| **N2. Register records** | (a) Revise the 8 `ncc-2022-adoption` records: provision-level commencements from `adoption_2022.csv`, real instruments (the adopting laws in the map, with register ids), Queensland's dates from the Queensland source the ABCB cites. (b) New family `ncc-2025-adoption`: one reform per jurisdiction from `adoption_2025.csv`, including the Northern Territory's non-adoption and the one-year delays. (c) `history` event for the August 2025 pause on residential changes. (d) Family summaries cite the variation counts | Next |
| **N3. Requirements** | The 3 families in section 3, quoting each state's adopting provision (for example Building Act 1975 (Qld) section 37, named in the Queensland appendix). Reach: 3019 and 3020 for Volume One, 3011 for Volume Two, 3231 for Volume Three. `records` link to the adoption reforms | Next |
| **N4b. Variations, NCC 2022** | Parse the 2022 fragment files the same way, so the counts can be compared across editions | Later |
| **N5. Cost inputs** | RIS figures (section 5) | Later |
| **N6. Checks** | `alicia validate`, quote checks, links table, tests; Industry lens for 3011 by state | With N2 and N3 |

## 5. Where the NCC feeds the compliance cost figure

The compliance cost plan ([thread](https://claude.ai/code/artifact/0ab7b54b-625e-4708-bde3-c43ba1d30489)) costs paperwork time only. The NCC is where the cost of meeting a standard is largest, and where official estimates exist:

1. **Substantive compliance cost per new dwelling** from the NCC 2022 energy efficiency Decision RIS and the livable housing RIS, with locators (N5). The OIA framework counts substantive compliance costs as well as administrative ones (to verify against the RBM text cached in `regulatory-burden-tool/data/`).
2. **Volume and timing:** new dwellings by state (ABS *Building Activity*, cat. 8752.0, not yet in the repo), from each state's adoption date in `adoption_2022.csv`. A state that did not adopt a provision bears no cost for it.
3. **Administrative part:** the energy rating certificate (NatHERS or BASIX) fits the paperwork formula directly.
4. **Kept apart:** substantive costs as a separate line, labelled as the RIS's own ex ante estimate.

The N3 requirements are the rows the cost figure would attach to.

## 6. Decisions

| # | Question | Answer |
|---|---|---|
| 1 | Network access | Owner opened all networks (27 November 2026) |
| 2 | Scope | Middle ground (owner); the 3 layers in section 3 (this revision) |
| 3 | NCC 2019 and earlier | Adoption dates only (in `adoption_history.csv`), no register records |
| 4 | Decision numbers | This work uses E-500 onwards (noted in `notes_for_other_branches.md`); E-600 onwards is the regulatory map page's and E-700 onwards the compliance cost work's |
| 5 | Regulatory map | Owner asked for it, with the NCC as the first example; the coordinator will start a website-side thread for the page once this data is in place |

## 7. Regulatory map: data shape and beta view

**Purpose.** Show a main law and the instruments that sit within it, and let a reader move from a state's building law to the code, to that state's variations, to the standards the code calls up, and to the other laws a builder must also meet. The view is a force-directed node-and-link graph, like Obsidian's graph view.

**File.** `data/processed/ncc/regulatory_map.json`, written by `alicia/scripts/ncc_data.py`. Later regulatory maps (for example work health and safety, food) should use the same shape, one file per map, so the page can load any of them.

```json
{
  "note": "...", "built_on": "2026-11-27",
  "node_types": ["adoption", "area", "code", "edition", "law", "other-law", "standard", "variation-set", "volume"],
  "relations": ["adopted-as", "consolidated-into", "contains", "edition", "gives-effect-to", "read-with", "references", "varies", "varies-area"],
  "nodes": [{"id": "law-qld-building-act-1975", "type": "law", "label": "Building Act 1975", "jurisdiction": "QLD", "register_id": "act-1975-011", "url": "...", "matched": "title"}],
  "links": [{"source": "law-qld-building-act-1975", "target": "ncc-2025-qld", "relation": "gives-effect-to", "jurisdiction": "QLD",
             "basis": {"source": "...", "locator": "Volume One, Queensland schedule, 'QLD Introduction'", "quote": "Section 37 of the Building Act 1975 continues to apply ..."}}]
}
```

**Nodes.** Every node has a stable `id`, a `type`, a `label` and a `jurisdiction` (`national` or a state code). Optional fields: `url`, `register_id` (the state register's id, joined from `data/processed/legislation/<state>_catalogue.csv`; ids repeat between states, so join on `jurisdiction` and `register_id` together), `matched` (how the join was made), `register_records` (ALICIA register items), `source`, and counts on variation sets.

| Type | Example | Count |
|---|---|---|
| `code` | National Construction Code | 1 |
| `edition` | NCC 2022, NCC 2025 | 2 |
| `volume` | NCC 2025 Volume One | 5 |
| `area` | Volume One, J Energy efficiency | 46 |
| `adoption` | NCC 2025 in Queensland (date, transition) | 16 |
| `law` | Building Act 1975 (Qld) | 19 |
| `variation-set` | NSW variations: Energy efficiency (Volume One), 30 provisions | 169 |
| `other-law` | Food Regulation 2025 (NSW), with agency and topic | 251 |
| `standard` | AS 3600 (2018) | 170 |

**Links** run from parent to child and are typed: `edition` (code to edition), `contains` (edition to volume, volume to area), `adopted-as` (edition to a state's adoption), `gives-effect-to` (state law to its adoption, quoting the state appendix), `consolidated-into` (a law whose rules were moved into the state appendix), `varies` (adoption to variation set, weight = provisions varied), `varies-area` (variation set to the national area it changes), `read-with` (adoption to other legislation the state lists) and `references` (area to standard, weight = citing clauses). 1,161 links in all.

**Beta view (for the website-side thread).**

- Force-directed graph; node size by degree or weight, colour by type, state filter that hides other jurisdictions' adoptions, variation sets and laws.
- Start collapsed at the code, editions and the 8 adoptions; expand a node to show its children. Standards and other laws start hidden behind a toggle (421 nodes).
- Selecting a node shows its label, jurisdiction, counts, the quoted basis and links to the register record or requirement where one exists.
- No schema change is needed for the beta, because the map is a separate file. A later field on register items (for example `parent_instrument`) should be the website session's change.

**Limits.** The map shows the structure the NCC itself describes. It does not show councils, the full ACT Appendix, or rules a state sets outside the code (the Queensland Development Code, BASIX), except where a state appendix names them. Laws not found in a state catalogue (61 of 251) have no register id yet.
