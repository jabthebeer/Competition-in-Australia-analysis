# Phase 6: the rules that score highest but were missing

*17 November 2026. Draft by Claude Code on the legislation branch, for the owner to check. Phase 6 of the [re-evaluation plan](plan_levers_reevaluation.md), batch 1 (DECISIONS E-179). The screen is `alicia/scripts/levers_gap_screen.py`, and its shortlist is `data/processed/legislation/levers_gap_screen.csv`. Drafted by AI-assisted desk research; not yet checked by a person.*

## Why

The ranking can rank only the rules in the register, and the register has followed what reviews wrote about. Before this batch it coded only 18 caps (with exclusive rights, bans and ownership limits) and 8 price controls: the kinds that score highest. Owner decision 5 (15 November 2026): fill gaps in the highest-scoring kinds first.

## The screen

`levers_gap_screen.py` reads the full text of every law in the Open Australian Legal Corpus (Commonwealth, NSW, Queensland, SA, Tasmania and WA, as scraped from September 2024 to March 2025; Victoria, the ACT and the NT are not in it) and looks for wording that signals the five kinds. It skips laws the register already cites.

| Signal | Laws (first run) |
|---|---|
| A cap on numbers ("moratorium", "maximum number of licences", "no further licences may be granted") | 135 |
| An exclusive right ("exclusive licence", "exclusivity period") | 159 |
| An ownership limit ("unacceptable shareholding situation", "more than 20% of the voting shares") | 71 |
| A price control ("maximum fares … determined", "price determination", "minimum price") | 107 |
| A ban on a business ("must not carry on a business of") | 19 |
| **Laws with any signal** (a law can have several) | **474 before batch 1; 469 after** |

The shortlist is noisy: intellectual property laws grant "exclusive rights", amending Acts repeat their principal Act, and burial rights are exclusive. It is a list for reading, not a finding. Each candidate is checked against the current law before anything is drafted.

## Batch 1

A requirement can only be a licence, registration, standard and so on; a cap, an exclusive right or an ownership limit scores as one only when a register item is coded as a cap. So each rule below is a new register item (an existing setting), with a requirement quoting its law inside it.

| Item | Law | What it does | Requirement inside |
|---|---|---|---|
| `nsw-casino-licence-cap` | Casino Control Act 1992 (NSW) s 6(1) | No more than 2 casino licences | `nsw-casino-licence` (existing) |
| `nsw-lottery-exclusivity` | Public Lotteries Act 1996 (NSW) s 18 | An operator licence may be exclusive; no other may be granted during its exclusivity period | `nsw-exclusive-lottery-licence` (new) |
| `nsw-totalizator-exclusivity` | Totalizator Act 1997 (NSW) s 14 | Only the TAB may hold the off-course totalizator licence during the exclusivity period | `nsw-exclusive-totalizator-licence` (new) |
| `qld-wagering-exclusivity` | Wagering Act 1998 (Qld) ss 4, 22 | Only UBET may be granted race and sports wagering licences, until 30 June 2044 | `qld-exclusive-wagering-licence` (new) |
| `qld-lottery-exclusivity` | Lotteries Act 1997 (Qld) s 237 | The corporation's lottery licence may be exclusive for a set term | `qld-exclusive-lottery-licence` (new) |
| `qld-gaming-machine-numbers-cap` | Gaming Machine Act 1991 (Qld) s 55(4) | No more machines in a venue than the maximum prescribed for its category | `qld-gaming-machine-cap` (new) |
| `cth-qantas-ownership-limits` | Qantas Sale Act 1992 s 7(1)(a) | Foreign ownership of Qantas capped at 49% | `cth-qantas-foreign-ownership-limit` (new) |
| `cth-media-ownership-limits` | Broadcasting Services Act 1992 ss 53, 54 | No more than 1 commercial TV, or 2 commercial radio, licences in a licence area | `cth-media-control-limits` (new) |
| `cth-airport-ownership-restrictions` | Airports Act 1996 | Limits on airline ownership of airport operators, and on cross-ownership | `cth-airport-ownership-limits` (existing) |
| `cth-financial-sector-ownership-limit` | Financial Sector (Shareholdings) Act 1998 s 11 | No stake above 20% in a bank or insurer without the Treasurer's approval | `cth-financial-sector-shareholding-limit` (existing) |

All 26 quotes in the 7 new requirements were found word for word in their sources. Each item is placed in its regime (gambling, aviation, telecommunications and media, financial services), and each new state family has its other jurisdictions logged as not yet searched.

**Marks.** Each item is marked against the framework. The exclusive licences and the casino cap mark −2 on entry and exit and −1 on competition. The airport and media limits mark +1 on competition and −1 on capital, so they total zero and are not classed: they keep owners from concentrating a market, as well as limiting investment.

**Not yet classed by severity.** Until the website session codes them, the new items take their class from their marks. The proposed coding is below.

## Proposed coding for the website session

For `rule-coding.json` (owner decision 4: the file is the website session's).

| Item | Kind | When | Bound | Note |
|---|---|---|---|---|
| `nsw-casino-licence-cap` | cap | entry | all | No more than 2 casino licences (s 6(1)) |
| `nsw-lottery-exclusivity` | cap | entry | all | An exclusive operator licence bars others during its exclusivity period (s 18) |
| `nsw-totalizator-exclusivity` | cap | entry | some | Only the TAB may run an off-course totalizator during the exclusivity period (s 14); bookmakers are not bound |
| `qld-wagering-exclusivity` | cap | entry | some | Only UBET may be granted race and sports wagering licences until 2044 (ss 4, 22) |
| `qld-lottery-exclusivity` | cap | entry | all | The corporation's lottery licence may be exclusive (s 237) |
| `qld-gaming-machine-numbers-cap` | cap | entry | some | Machines in a venue capped at the prescribed maximum (s 55(4)); binds venues with gaming machines |
| `cth-qantas-ownership-limits` | cap | operating | some | Foreign ownership of one company capped at 49% (s 7(1)(a)) |
| `cth-financial-sector-ownership-limit` | cap | operating | some | Stakes above 20% need the Treasurer's approval (s 11) |
| `cth-airport-ownership-restrictions` | cap | operating | some | Ownership limits on airport operators (marks total zero) |
| `cth-media-ownership-limits` | cap | operating | some | Control of licences in a licence area capped (ss 53, 54; marks total zero) |

## Limits

- **NSW quotes** are from the corpus copy of January 2023, which is not itself official; a later change would not show.
- **Exclusivity in force.** The NSW and Queensland lottery Acts allow an exclusive licence; whether the current licence is exclusive, and to when, is in the licence, which is not quoted.
- **Not screened:** Victoria, the ACT and the NT, which are not in the corpus. Their exclusive gambling licences, casino caps and gaming machine caps are the next batch, through their registers.
- **Next batch:** the same families in the other states; price controls (regulated energy tariffs in Queensland, WA and Tasmania; taxi fares); limited-entry fisheries.
