# Industry lens (beta): methods

*6–10 November 2026 (DECISIONS E-122, E-123, E-126 to E-128). Code: `alicia/src/alicia/register/competition.py` (placing marks in columns) and `alicia/src/alicia/menu/lens.py` (the page's data); template `menu/templates/industry-lens.html`; map `alicia/src/alicia/pipeline/boundaries.py`. Tests: `alicia/tests/test_lens.py`.*

## What the page shows

The user picks an ANZSIC **division**, then, optionally, one of its **classes**, and a state or territory (10 November 2026, E-126).

- **Division only:** every law that applies to any class in the division. Each is tagged with the classes it applies to; a tag is a button that opens that class alone. A law that reaches every class in the division, or every industry, says so instead of listing them. The market figures are for the whole division in the state (CABEE summed over its classes).
- **Division and class:** the class's own view, with no tags.

The address keeps the choice (`#division=H&class=4511&state=NSW`); older `#class=` links still work. For the chosen classes, the page lists:

- **Requirements** (`regulation-register/requirements/`) whose reach covers the class and that apply in the state: Commonwealth ones (unless limited to other states), the state's own, and its capital city council's, where recorded;
- **Register items** (`regulation-register/records/`) about the class, at the Commonwealth or in that state, except those repealed or replaced. Items about a division, subdivision or group reach every class in it; economy-wide items with no industries reach every class.

A register item whose framework assessment rates its reach **economy-wide** appears for every industry: directly where it names the industry, and as an indirect effect elsewhere (shown as "Economy-wide, indirect", and hidden with the other indirect items when the user asks). Examples are insurance duty, planning and zoning, and insolvency reforms (10 November 2026, E-127).

**Reading the table** (10 November 2026, E-128). The laws are one list, not grouped under Commonwealth, state and council headings. Each law starts with a tag for its level of government: *Commonwealth*, the state or territory's name, or *Council* and the council's name. Above the table:

- **Level of government** chips show or hide Commonwealth, state or territory, and council laws; at least one stays on. The tallies follow the filter.
- **Sort by:** level of government (Commonwealth, then state, then council; the default), most negative first or most positive first (by the framework total), or title.

A requirement that names a register *setting* about the same law (payroll tax, occupational licensing, Australia Post's reserved service) stands for it, so the setting is not listed twice. Laws with no material effect are hidden unless the user asks for them.

## Every law is marked against the productivity framework

The marks come from the ALICIA productivity impact framework (v1.0, [`productivity_framework.md`](productivity_framework.md)): eight drivers, each marked from −2 (major harm) to +2 (major gain) with a reason, against the same market without the law.

- **Register items** carry their existing framework assessments.
- **Requirements** were marked against the framework on 7 November 2026, all 159 of them (`assessment` on each file):
  - Where the register already assesses the same law, the requirement uses its marks and evidence, so the two agree. This applies to payroll tax and Australia Post's reserved letter service; the security licence takes the occupational licensing setting's labour mark.
  - The rest follow the marking guide. Examples:
    - a licence or registration needed before trading: entry and exit −1;
    - a licence that narrows who may do the work: labour and skills −1;
    - ongoing paperwork, inspections and fees: regulatory burden −1;
    - portable long service leave: labour and skills +1 (entitlements move with the worker) against regulatory burden −1;
    - trading-hours and licence conditions on liquor: competition −1;
    - working with children checks that are not valid across states: market integration −1.
  - Four small obligations have **no material effect** (the framework's mark 0): business name registration, keeping employee records, Single Touch Payroll and the spam consent rules. Their summary says why.
  - All requirement marks are drafts at low confidence (reasoning and desk research), unless they come from a register assessment with higher confidence.

## Placing marks in the three columns

Each mark goes in the column of the market players it acts through:

| Column | Question | Drivers placed there |
|---|---|---|
| Entrants into the market | Does it change how easily new businesses can start up, or enter from other states and countries? | Entry, exit and scale-up; Trade and market integration |
| Small and medium competitors | Does it change smaller businesses' costs, or their ability and incentive to compete, invest and grow? | Competitive pressure; Regulatory burden; Labour mobility and skills; Capital deepening; Innovation; Price and tax signals |
| Monopoly and oligopoly players | Does it shelter the largest players from rivals, or expose them to more competition? | Competitive pressure; and entry marks of ±2 |

Three refinements:

- **Bans, caps and exclusive rights.** An entry-exit mark of −2 or +2 is a ban, cap or exclusive right on entry, or its removal (the framework's marking guide). It shelters or exposes the incumbents, so it also lands with the largest players. An example is Australia Post's reserved letter service.
- **A mark can name its column** (`positions` on the mark) where the usual place would mislead:
  - the entry-exit marks about growing past a payroll or GST threshold go to small and medium competitors (14 register marks and the requirements that mirror them);
  - a cost only the largest firms bear, such as the $100 million modern slavery threshold, goes to the largest players.
- **A cell adds up its marks.** It is positive or negative by the total, and mixed when marks of both signs meet. It is shown darker when any mark is ±2, and lists each mark with its driver and reason. The overall framework mark (the sum of all marks), its band and the main driver are shown with the law.

The columns describe market positions, not firm sizes: "monopoly and oligopoly players" means market power. Public data cannot show which firms in a class hold it (class-level concentration is not published; firm-level data such as BLADE are restricted).

## Market structure (7 November 2026, E-125)

Above the laws, a **Structural market conditions** section, and figures at the top of each column's tile. Each figure carries its level, year and source, because no public source gives market shares for one class in one state ([feasibility note](market_structure_feasibility.md)).

| Column | Figure | Level | Source |
|---|---|---|---|
| Entrants | Entries in the latest financial year as a share of businesses operating at its start; closures likewise | Class × state | ABS CABEE |
| Small and medium competitors | Businesses with 1–199 employees, and with none, at the end of the latest year | Class × state | ABS CABEE |
| | Share of sales and service income earned by businesses with fewer than 200 employees | Division, Australia | ABS *Australian Industry* (8155.0), Table 5 |
| Monopoly and oligopoly players | Businesses with 200 or more employees, and their share of sales | Class × state; division, Australia | ABS CABEE; ABS 8155.0 Table 5 |
| | The four largest firms' share of sales in the division's industries (sales-weighted mean), latest year | Division | RBA RDP 2025-05 (Hambur and Freestone), from BLADE |

The charts:

- **Businesses and sales by size.** Two bars, cut into fewer than 20 employees (including none), 20–199 employees, and 200 or more. One bar is the share of businesses (class × state); the other is the share of sales (division, Australia).
- **Entry and exit rates.** Each year from 2007-08 (class × state).
- **The division's four-firm share.** 2002 to 2019, the sales-weighted mean and the median industry.

The page builds these from `data/processed/abs_cabee/class_state_fy.parquet` and the ingested 8155.0 and RBA files (`lens.market()`). `test_lens.py` recomputes them from the same files by a separate route.

**Limits of these figures.**

- Counts of businesses are not market shares.
- Sales by size and concentration describe the whole division across Australia, not the class in the state.
- Firms with 200 or more employees are the largest firms, not necessarily an oligopoly.
- The RBA series stops at 2019.
- Finance and insurance is not in the ABS size table.
- The ABS perturbs small counts, so rates for small industries are noisy.
- CABEE counts each business once, in one state, so a firm trading in several states appears in only one.

Regulators' published market shares (ACCC inquiries, PC reports) are to be added later as a cross-check of these figures (owner, 7 November 2026).

## Limits

- **Coverage is thin and uneven.**
  - Laws on every business are recorded for every industry.
  - Industry-specific requirements cover the families drafted so far (the calibration's and phase C batch 1). Each reaches every class its law covers (E-127), but many industries have no industry-specific law recorded yet.
  - Councils are the capital cities only.

  A short list means *not yet recorded*, not *no regulation*. The page says when no industry-specific requirement has been recorded for the chosen industry.
- **Drafts.** Every requirement, register item and mark was drafted by AI-assisted desk research and is not yet checked by a person.
- **The framework weighs productivity and competition only.** It does not count a law's benefits to safety, consumers or the environment. A red cell says a law adds cost or shelters incumbents, not that it should go.
- **Placing marks is mechanical.** The driver-to-column table is a convention. A mark that acts through more than one group needs its own `positions`.
- **Requirement marks are rough.** Most requirements carry one or two −1 marks (an entry condition, compliance burden). Differences in how hard a licence is to get, or how large the burden is, are not yet captured.
- **Indirect effects.** Register items marked as affecting an industry indirectly are included by default; the page can hide them.

## Later features (owner, 6 November 2026)

To be built only when the owner asks:

- **A structural economic conditions chart for council areas and regions.**
- **Council-level features on the map.** `pipeline/boundaries.py` already reads the ABS's generalised council (LGA) boundaries, `build("LGA")`.

## Adding to it

New requirements and register items appear on the page at the next site build, with no code change. A requirement must carry a framework assessment, which `alicia validate` checks. The workflow is in [`regulation-register/requirements/README.md`](../regulation-register/requirements/README.md).
