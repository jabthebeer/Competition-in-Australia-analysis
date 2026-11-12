# Plan: the ALICIA Industry lens page

*Prototype built 6 November 2026 (DECISIONS E-122): the owner chose to prototype the page from the register as it stands and widen the legislation later. The page's design changed from the stages below to three market positions (entrants, small and medium competitors, monopoly and oligopoly players), each law coded positive or negative for competition; see [`industry_lens.md`](industry_lens.md). The stage-and-threshold idea survives in the rules for size thresholds.*

*Replanned 6 November 2026 at the owner's request: legislation first. The ABS data side is parked (§6). Framework assessments only, no econometrics (E-87, E-113). Nothing beyond phase 1 is started until the owner confirms.*

## 1. Aim

Pick an Australian industry and a state. See, in the first person, what a business in that industry faces as it enters the market and grows, stage by stage, and which barriers are the same in every state. The first version of the page is scoped from **legislation**: what applies to the business, which tier of government sets it (Commonwealth, state or territory, council), and at which stage it bites.

## 2. Phases

| Phase | What | Status |
|---|---|---|
| 1 | Choose the ABS classification level that legislation is collected against, and list its categories | **Done; confirmed 6 Nov 2026** (§3, list in [`anzsic_classes.md`](anzsic_classes.md); E-114, E-115) |
| 2 | Plan how to ingest all the legislation that applies to these businesses: Commonwealth, states and territories, councils | **Plan proposed, awaiting approval**: [`plan_legislation_links.md`](plan_legislation_links.md) |
| 3 | Ingest, as phase 2 decides | Not started |
| 4 | Page design from the legislative view: stages, threshold markers, state switch, cross-cutting badges | Not started |
| 5 | Add the structural (ABS data) view | Parked (§6) |

## 3. Phase 1: the classification level

**Recommendation: the ANZSIC 2006 class.** Collect legislation against the 506 classes, using the codes and titles exactly as the ABS publishes them. Revision 2.0 (26 June 2013) is the current release, and the ABS lists the next release as "Unknown". Then add three refinements, each taken from ABS or official categories, not invented:

1. **Primary activities as qualifiers.** Where a law covers only part of a class, name the part using the ABS's own primary activities for that class, quoted word for word. The ABS lists 4,440 primary activities under the 506 classes. They are not a coded level: the ABS assigns a business to a class, never to an activity.
2. **Activity triggers across classes.** Some laws follow an activity that businesses in many classes carry out, such as selling alcohol, handling food, using hazardous chemicals or running heavy vehicles. These are recorded on the law itself, because ANZSIC codes a business by its main activity only.
3. **Keys other than industry.** Some laws turn on something other than industry:
   - legal form: the ABS's Type of Legal Organisation (SESCA 2008), e.g. company, trust, partnership or sole proprietor;
   - size: employees, payroll or turnover, handled later as threshold markers;
   - location: the state, and the council by ABS Local Government Area (548 LGA codes, including 6 unincorporated areas, in the ASGS 2021 postcode correspondence the repo holds).

### Why the class, and not a coarser level

The ABS assigns each business to one category at each level, by its predominant activity, and codes it at the finest level: *"The ABS and Statistics NZ classify each unit at the finest level of the classification"* ([ABS, Methods of classification](https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0/methods-classification)). So the class is the lowest level at which a business has an official ABS category.

Coarser levels mix businesses that face different laws. I tested this on the register's own mapping of 54 industry-specific regimes to classes (`regulation-register/regimes/`, a draft not yet checked). The table counts how often a regime would cover only part of a unit at each level:

| Level | Units | Regime–unit pairs where the regime covers only part of the unit | Regimes affected (of 54) |
|---|---|---|---|
| Division | 19 | 104 of 116 (90%) | 51 |
| Subdivision | 86 | 91 of 206 (44%) | 43 |
| Group | 214 | 44 of 400 (11%) | 27 |
| **Class** | **506** | finest level | n/a |

For example, group 693 *Legal and Accounting Services* holds 6931 *Legal Services* (legal profession regime) and 6932 *Accounting Services* (tax and BAS agents regime). Collected at group level, each would wrongly get the other's regime.

Other evidence:

- The register already works at this level: 469 of the 560 industry codes on its records are classes, and regimes use 99 class codes plus 12 class exclusions.
- 26 of the 54 industry-specific regimes span two or more divisions (hazardous chemicals spans 7, food safety 5, liquor licensing 5). Those regimes follow an activity rather than an industry, which is why refinement 2 is needed.
- The ABS publishes business counts at class level (CABEE), so the parked data view will join without re-coding.

### Why not go below the class

Below the class there is no ABS code to collect against, only the descriptive list of primary activities. Treating each activity as a category would mean inventing a classification, which the brief rules out. Used as qualifiers, the activities keep the ABS's wording and stay inside its classes. Two examples from the ABS's own lists:

- **Part of a class.** 4271 *Pharmaceutical, Cosmetic and Toiletry Goods Retailing* lists both "Pharmacy, retail, operation" and "Cosmetic retailing". The register's pharmacy regime (ownership, premises and PBS approval) is mapped to the whole class today, so it also lands on cosmetics and perfume retailers. With a qualifier, it is recorded against 4271 for "Pharmacy, retail, operation" and "Prescription, medicine, dispensing" only.
- **An activity across classes.** A café that also serves alcohol stays in 4511 *Cafes and Restaurants* while that is its main activity. The ABS sends units "selling alcoholic beverages both for consumption on and off the premises" to 4520 *Pubs, Taverns and Bars*. Liquor licensing is mapped to all of 4511 today, but it reaches a café through the activity, not the class. That is what an activity trigger records.

## 4. Questions for you (phase 1), answered 6 November 2026

Answers: Q1 yes; Q2 no, occupational licences stay with the classes whose businesses employ the people (may be revisited); Q3 keep all 506 and mark them.

| # | Question | My recommendation |
|---|---|---|
| Q1 | Confirm the class as the unit, with ABS primary activities as qualifiers and activity triggers recorded on the law? | Yes |
| Q2 | Occupational licences (electricians, plumbers, builders, real estate agents) license people, not businesses, and one class employs many occupations. Should they also be recorded against the ABS's occupation classification, linked to the classes that use them? The current one is OSCA 2024, already in the repo (`abs_osca`). It flags 187 occupations as requiring registration or licensing and 196 as possibly requiring it. | Yes, as a second key, planned in phase 2 |
| Q3 | Some classes are mainly government or households (e.g. 7520 *State Government Administration*, 9601–9603 private households). Keep all 506 as you decided, and mark these? | Keep, and mark them |

## 5. Phase 2: what it will plan (not started)

*Superseded on 6 November 2026 by [`plan_legislation_links.md`](plan_legislation_links.md), which covers each of these headings.*

These are the headings for the next conversation, not decisions:

- **Sources by tier:**
  - Commonwealth: the Federal Register of Legislation;
  - states and territories: each one's legislation register;
  - councils: local laws and planning schemes;
  - cross-checks: business.gov.au and ABLIS (whose API needs registration).
- **The council problem.** Councils regulate land use and activities through each state's planning scheme terms, such as "food and drink premises" or "shop", not through ANZSIC. A crosswalk from classes to each state's land-use terms will be needed, and about 540 councils won't all publish in the same way.
- **What a record holds:** regime → instrument → requirement → trigger → jurisdiction, with an official source for each. The stage-and-threshold table from the first draft of this plan becomes part of this.
- **Coverage and completeness:** how we'll know nothing major is missing for a class in a state.
- **Open questions from the first draft:** add regimes for company reporting and for insolvency or closing a business; the date threshold values refer to; sites that block automated checks (NSW, SA).

## 6. Parked: the data side

Kept so the work isn't lost, not to be built now:

- **Bands.** The state CABEE panel merges 1–4 and 5–19 into 1–19. The ABS publishes them separately from 2021-22 (cube 2).
- **Missing classes.** 11 classes have no current CABEE counts.
- **Unused tables.** The repo doesn't use cube 3 (class × state × turnover range), cubes 4–5 (survival by state × subdivision × size) or cube 1 Table 14 (moves between size ranges, Australia, all industries).
- **Movement between bands.** Net movement between size bands is published by class × state. Gross moves are published only nationally; by industry or state they need BLADE.
- **No R here.** R isn't installed in this container, so independent recalculations will need it installed or a standalone script.

## 7. Earlier decisions that still stand

- Industries: ANZSIC 2006 classes, all 506, ABS conventions.
- Stages: CABEE employment bands (Start, 1–4, 5–19, 20–199, 200+, Exit), with thresholds as markers within a stage.
- A state switch showing each state's version of each regime; barriers common to all states pointed out.
- An official source for every threshold; nothing fabricated; framework assessments only.
- The landing page's Industry lens card links to `industry-lens.html` once the build writes it.
