# How council requirements vary: the 18 sample councils

*Methods note for batch E-7 of [`plan_councils.md`](plan_councils.md) (DECISIONS E-366), 28 November 2026. Draft: compiled by AI-assisted desk research; not yet checked.*

This note shows how the requirements that councils make for businesses differ between councils. It covers the 18 sample councils outside Victoria (3 in each state and the NT). It is the evidence for decision D4, on whether to cover every council.

## What the register holds

The register holds 43 council requirements in 8 families for 11 of the 18 councils. Each family was searched for in all 18 councils. The register also holds 3 City of Melbourne permits, which wait for the Victorian batch and are not counted here.

The table is `data/processed/legislation/council_variation.csv`, with one row for each family and council. A summary for each family is in `council_variation_summary.csv`. Both are written by `alicia/scripts/council_variation.py`, which also checks that the families are drafted consistently.

| Family | Councils with it | Covered by another requirement | Under a state Act | Laws read, none found | Not yet checked | Laws could not be read |
|---|---|---|---|---|---|---|
| Busking | 8 | 0 | 2 | 1 | 2 | 5 |
| Filming | 5 | 0 | 2 | 4 | 1 | 6 |
| Outdoor dining | 8 | 2 | 2 | 0 | 1 | 5 |
| Street trading and stalls | 8 | 0 | 3 | 0 | 0 | 7 |
| Markets | 2 | 1 | 0 | 0 | 8 | 7 |
| Advertising signs | 6 | 0 | 0 | 0 | 5 | 7 |
| Temporary events | 4 | 0 | 0 | 1 | 6 | 7 |
| Caravan parks | 2 | 0 | 6 | 2 | 1 | 7 |

"Laws could not be read" covers 7 councils:
- Adelaide, Alexandrina and Mount Remarkable: their websites refuse automated requests.
- Hobart and Launceston: their by-laws are scanned images with no text.
- Break O'Day: its website was down.
- Victoria Daly: it publishes no by-laws.

Adelaide and Hobart still have 5 requirements between them, taken from ABLIS listings.

## How councils differ

**The same activity needs a different approval in different councils.**
- **Footpath dining** has its own permit in Brisbane, Perth, Busselton, Darwin and Alice Springs. In Winton and Toowoomba it falls under a general approval for commercial use of council land and roads. In Toowoomba, trading on a council road next to the business's own premises needs no approval at all, if it meets set standards. These include public liability insurance of at least $10 million and set clearances for pedestrians.
- **Caravan parks** need an approval in Winton, and the council must find the operator suitable. In Toowoomba, a park that meets minimum standards needs no approval; one of the standards is that at least 10% of the park is recreation area. In NSW and WA, caravan parks are approved under state Acts.
- **Markets** need a council licence in Darwin and a permit in Alice Springs. In Darwin only a body corporate set up to manage a market can hold the licence. In Winton a single-day market stall is a "public place activity" and needs no separate licence.

**Triggers differ widely for the same family.**
- **Temporary events.** Victoria Plains needs a licence for any function on council property. Toowoomba needs approval for events of 50 people or more on council land, or more than 200 if the event meets set standards. Winton's threshold is 250 people. Brisbane's is 1,000 people where the event has risks such as amplified music, late hours or alcohol, and 2,000 people otherwise. Firearms and motorsport events in Brisbane need a permit at any size.
- **Advertising signs.** Brisbane and Winton need approval for any sign visible from a road or public place, unless it is a permitted type. Busselton needs a permit for any sign on or over a road or footpath. Victoria Plains allows 2 small signs (up to 1 square metre each) without a licence. Alice Springs needs a permit for signs on private premises in view of a public place only if they are larger than 0.5 square metres.

**Some families are much more common than others.** Busking, outdoor dining and street trading need an approval in most councils whose laws could be read, under either a council law or a state Act. Filming permits are found in only 5 of the 18 councils. Councils in Queensland and WA are more alike within their state, because many use the state's model local laws. Winton follows Queensland's model Local Law No. 1. Perth and Busselton use the same wording for stallholder and trader permits.

**Fees were not collected.** The plan records fees as dated values, not as requirements, and no fee schedules were read in this phase.

## Quality check

- **Quotes:** every one of the 192 quotes in the council requirements was found word for word in its source (28 November 2026).
  - 37 of the 43 requirements quote the law itself.
  - 6 rest on ABLIS listings alone, and stay at medium confidence: 3 in Adelaide, 2 in Hobart, and Perth's filming permit.
- **Administration:** every requirement names the council as the body that issues the approval. The script also checks that no requirement is high confidence without a quote from the law.
- **Medium confidence:** 18 of the 43 requirements are medium confidence. The 6 ABLIS-only requirements are among them. The other 12 are medium for these reasons:
  - Toowoomba (3): its authorising Local Law No. 1 (Administration) 2020 was not found online.
  - Perth (3): its laws are quoted as made, from the Gazette.
  - Alice Springs (5): the register copy is as in force at 5 August 2010, and a 2012 amendment was not read.
  - Brisbane filming: its local law covers commercial activity in parks but does not name filming.
- **A methods inconsistency to fix.** Sydney's busking, filming and outdoor dining permits are filed as council requirements. They are approvals under state Acts: busking under the Local Government Act 1993 s 68, filming under ch 7 pt 1 div 4 of the same Act, and outdoor dining under the Roads Act 1993 s 125. By methods rule 7 they should each be one NSW state requirement marked as council-administered, as Shoalhaven and Temora are treated here.
- **Regimes:** the busking, filming and outdoor dining families belong to the "Council permits for public spaces" regime. Street trading, markets, signs, events and caravan parks have no regime yet.
- **Kinds:** street trading, signs and events are recorded as approvals in Queensland and as licences or permits in WA and the NT. This follows the words each law uses.

## What this means for decision D4

Councils differ in whether a requirement exists, in what approval it needs, and in its trigger. A sample can show this. It cannot count how many businesses face each version.

Covering every council would add about 8,700 requirements (range 5,700 to 12,500), from the phase B estimate. Reading each council's laws one by one is slow, and 7 of the 18 sample councils could not be read at all.

The ABLIS API key would list each council's permits with their legal basis. It is the practical route to full coverage.

## Limits

- 18 councils of about 470 outside Victoria. The sample shows the kinds of variation, not their frequency.
- "Not found" means the laws named in the table were read and hold no such provision. A council may still regulate the activity under another law, a policy or its planning scheme.
- Planning-scheme controls on signs and events are out of scope. Land-use terms are covered by batch E-3.
