# Plan: making ALICIA a tool that informs competition policy

*14 November 2026. Agreed with the owner (DECISIONS E-161), after a review of the framework, the register, the data and the site. Figures marked "review" were computed from the repository on 14 November 2026. Sources marked "checked" were opened on that date.*

## 1. The short answer

**Does the site inform competition policy well? Not yet.** It is a careful catalogue with honest limits. It is not yet a tool that tells a government where to act first, or why.

| A policy maker asks | Today | Gap |
|---|---|---|
| Where is competition weak? | National figures for entry, concentration and mark-ups | Concentration ends in 2019 and mark-ups in 2017. Both are another paper's results |
| What holds it back there? | 255 register items and 537 requirements, each marked | The marks barely rank anything. The list follows what reviews have written about |
| What could change? | 65 recommendations | All 65 are drawn from published reviews |
| How much does it matter? | Not answered | No measure of the businesses, jobs or output behind a rule |

**The asset no one else has** is the link from quoted law to each of the 506 detailed industries in each state, joined to 18 years of business counts for the same industries. The plan is to make that link do the work.

## 2. What the review found

| # | Finding | Evidence (review) |
|---|---|---|
| 1 | The site's findings lean on other people's work | Concentration and mark-ups are the RBA's. "Fewer new firms start up where regulation is heavy" uses Grattan's 2017 industry groups, not the register. Of 140 evidence links on assessments, 117 go to the Productivity Commission or the Treasury |
| 2 | The confidence scale rewards literature | "High" needs a published evaluation or official finding. A rule read word for word from the Act can only rate "low" |
| 3 | The marks do not rank | Requirements: 677 of 728 non-zero marks are −1. Register items: 419 of 487 are +1 or −1 |
| 4 | Reforms and standing rules share one scale | 193 of 255 register items are reforms, marked against what they replaced. Standing settings are marked against no rule at all |
| 5 | Counts of rules do not separate industries | 123 requirements reach every industry. In NSW an industry faces 63 to 79, with a median of 65 |
| 6 | Coverage is uneven | Commonwealth 306 requirements, NSW 56, every other state 21 to 28. The project's estimate is about 2,240 state requirements; 211 are recorded |
| 7 | Nothing weighs economic size | Reach is a 4-step label, though the site holds business counts for every industry and state |
| 8 | Ingested data sit unused | Monthly ABN and ASIC counts, business counts by small area, and the catalogues of every Act and instrument |

## 3. Principles

1. **Own evidence first.** Every headline finding is computed from law or data the tool ingests. What reviews found and recommend sits in a separate panel, labelled "What others found".
2. **Rules and changes are different things, shown simply.** A standing rule is what applies today. A reform is a change to a rule. The site shows one list of rules; a rule's changes hang under it. Readers never have to learn a model to use the page.
3. **Coded facts before judgement.** A rule is scored from things anyone can check in its text: its kind, when it bites, who it covers, its fee, its threshold.
4. **Three plain classes.** Each rule is **Major, narrow** (a large effect on a small set of industries), **Major, wide** (a small effect on a large set of industries) or **Minor** (a small effect on a small set). The class comes from the coded severity and from measured exposure. The figures behind it are shown.
5. **Join the law to the data.** A rule shows the industries it reaches and their size. An industry shows its rules.
6. **Describe; do not estimate.** No econometric studies and no comparisons between states at this stage. State economies differ too much for a simple comparison to be fair. This is shelved, not ruled out.
7. **Declare coverage.** Each finding says how much of the law has been screened. No ranking of states until coverage is even.
8. **The law speaks for itself.** Each rule links to its text. Its purpose is recorded as a secondary field, not a headline. Readers weigh the rule's benefits themselves.
9. **Open workings.** A plain table shows how every rule is coded, which sources are used and which industries it reaches.
10. **Small scope.** A new input is added only with a named use on a page. One at a time.
11. **Current and reproducible.** Prefer sources that update each year or month. Every figure is rebuilt from raw data and recomputed in a test.

## 4. Framework version 2

### What changes

| Version 1.0 | Version 2 |
|---|---|
| Eight marks added into one total | The total is no longer used to rank. The profile across the 8 drivers stays, as the judgement layer |
| Marks from −2 to +2 | A **severity score** from coded attributes (below) |
| Reach as a label | **Exposure**, measured: businesses, and jobs and output where the data allow |
| Bands (strongly negative to strongly positive) | **Impact class:** Major, narrow; Major, wide; Minor |
| Reforms and settings in one list, one scale | Rules, with their changes under them |
| Confidence follows the literature | **Evidence:** quoted from the law; coded; described in the tool's data. Reviews are listed beside it |
| Benefits out of scope | A secondary **purpose** field. Not used in any ranking |

### Severity: coded attributes (draft, to settle when built)

| Attribute | Coded as | Scores higher when |
|---|---|---|
| Kind | Cap or exclusive right; licence; approval; registration; standard; tax or levy; insurance; reporting; notification | It limits who may operate at all |
| When it bites | Before trading starts; at the first employee; at a size threshold; while operating; at exit | It bites before trading starts, or as a business grows |
| Who is bound | Every business in the industry; only some activities | It binds every business in the industry |
| Fee and waiting time | Dollars; days (from ABLIS, when it arrives) | They are higher |
| Renewal | Period | It is shorter |
| Threshold | Value and unit | It is lower |
| Penalty | Maximum, where the provision states it | It is higher |

Until the attributes are coded, severity is taken from the marks already drafted: a rule with a total of −2 or lower counts as a large effect. This is a stopgap, and the site says so.

**First step, built on 14 November 2026 (E-184).** `alicia/src/alicia/register/severity.py` scores each requirement from 3 attributes it already records. The weights are a draft for the owner to settle.

| Attribute | Points |
|---|---|
| Kind | Licence or approval 4; registration, insurance, tax or levy, or standard 2; reporting, notification, record-keeping or other 1 |
| When it bites | Before trading starts 2; at the first employee or a size threshold 1; while operating or on an activity 0 |
| Who is bound | Every business in its industries 1; only those doing a named activity 0 |

The score runs from 1 to 7: 5 or more is high, 3 or 4 medium, and less is low. Across the 537 requirements it takes every value from 1 to 7, where the marks take 4 values and 336 requirements share one of them. Of the 120 requirements that score high, 96 also have marks that add to −2 or lower. Fees, waiting times, renewal and penalties are not yet coded and add nothing. The score is shown on Register data beside the marks; the impact classes still come from the marks until the weights are settled.

### Exposure and the three classes

For each rule the tool computes, from its own data:

- the detailed industries it reaches, and their share of all businesses in its jurisdiction (ABS business counts, latest year);
- the number of businesses, and how many have employees;
- jobs and output in the divisions it touches (state accounts and labour force), marked as an upper bound when the rule covers only part of a division.

| | Small set of industries | Large set of industries |
|---|---|---|
| **Large effect on each business** | Major, narrow | Major, wide (listed first) |
| **Small effect on each business** | Minor | Major, wide |

"Large set" is a share of the businesses in the rule's own jurisdiction, so a state rule is judged within its state. The cut-off is set from the data when the class is built, and published.

### Keeping it usable

- One list. Each row is a rule with its class, its exposure figures and a link to the law.
- A rule's reforms show under it as a dated history, as the timeline does today.
- The site never uses the word "layer". The labels are "Rule" and "Change".
- The 8-driver profile opens on request.

### Binding words, with care

Counting words of obligation in the text ("must", "must not", "is required to", "it is an offence") gives a measure that needs no judgement. Mercatus published one for Australia in 2019 (RegData: Australia). It is used here only with these limits:

- **Count who is bound.** Many "musts" bind the minister or the regulator, not a business. Count an obligation only where its subject is a person, licensee, employer or operator.
- **Scale by length:** obligations for every 1,000 words.
- **Compare an Act with itself over time,** or with others in the same jurisdiction. Drafting styles differ between states and eras.
- **Use it to screen,** to find Acts worth reading, and as one attribute among several. It is never the severity score on its own.
- **Only where the full text is held** (the Open Australian Legal Corpus, part-ingested).

## 5. Inputs

### Agreed, in order of work

| # | Input | Checked on 14 November 2026 | Use |
|---|---|---|---|
| 1 | **ABS input–output tables** | 2023–24, released 25 March 2026; yearly. Has an industry-by-industry flow table, direct and total requirement coefficients, imports by product, and employment by industry. National only | See 5.1 |
| 2 | **ABS job mobility** | February 2026, released 31 July 2026; yearly. Separations and engagements by industry (tables 4 and 5) | See 5.3 |
| 3 | **ABS Labour Account** (hours, jobs, vacancies) | Quarterly. Division in the spreadsheets; subdivision through Data Explorer. Some industry series are under ABS review from June 2026 and may be missing | See 5.3 |
| 4 | **APRA monthly bank statistics** | Bank by bank, monthly, XLSX, March 2019 to September 2026, with an earlier series back to 2002. Creative Commons Attribution 4.0. Variables to confirm from the glossary | Current concentration in deposits and lending. APRA's insurance and superannuation files are not yet checked |
| 5 | **Occupation by industry** | Labour Force table EQ09 exists (division by major occupation group), but the ABS has paused some industry data. Fine detail needs the Census (TableBuilder, free registration): not yet checked | See 5.2 |
| 6 | **ACCC acquisitions register** | Public. Each entry has the parties, status, phase, dates and ANZSIC codes. No download seen; terms of use to check | Mergers notified, by industry |
| 7 | **Binding words** | RegData: Australia (Mercatus, 2019) confirmed. Corpus part-ingested | Section 4 |
| 8 | **Fees and waiting times** | ABLIS, when the owner's access arrives | Severity attributes |
| 9 | **Even coverage of state law** | Catalogues ingested; drafting continues on other branches | Removes the bar on state comparisons, if wanted later |

Not checked: the AER's retail energy figures (the site refused the connection from this environment).

### Dropped or shelved

- Commonwealth contracts (AusTender): dropped for now; too much scope.
- Comparing states, and state rankings: shelved.
- Econometric studies: shelved.

### 5.1 The case for input–output tables

The tables show what each industry buys from every other. They answer 4 questions the site cannot answer today.

1. **Who pays for a rule on someone else?** A rule on ports, road freight, electricity or insurance is narrow by a count of businesses. Every industry that buys from them carries its cost. With the direct and total requirement coefficients, the tool can state, for each industry, the share of its inputs bought from industries under a Major rule. This is what moves a rule from "Major, narrow" to "Major, wide" on evidence.
2. **Does concentration matter here?** Imports as a share of supply show which industries face foreign rivals. A concentrated industry open to imports is a smaller worry than one that is not. This replaces Grattan's judged "tradeable" group with a computed one.
3. **Who are the customers?** The share sold to households, to other businesses and to government shows who bears a rule's cost. The Industry lens can say what share of an industry's output goes to households.
4. **How large is it, in dollars?** Value added, wages, profits and employment for the input–output industry groups (more than 100; the count is to confirm), against 19 divisions today. That makes exposure figures finer. Profit as a share of output gives a yearly check on mark-ups to 2023–24, where the RBA series ends in 2017.

Limits: national only; the industries are input–output groups, so a concordance to ANZSIC is needed; 2 years' lag; cost shares show exposure, not a price effect. Work: one workbook and a parser.

### 5.2 Uses for occupation by industry

1. **Licensed workers in each industry.** Map the register's occupational licences to occupations, and state the share of an industry's workers who need one.
2. **Carry a licence to where it bites.** An electrician's licence affects mining and manufacturing, not only electrical services. Today a licence is linked only to the industry named for the trade.
3. **Class labour rules by workers,** not by businesses.
4. **Workers affected by recognition between states,** for the automatic mutual recognition items.

Limits: the Census is every 5 years; the Labour Force table is too coarse (19 divisions by 8 occupation groups).

### 5.3 Uses for job mobility and hours worked

Job mobility:

1. **A second measure of dynamism** on Structural competitive conditions: the share of workers who changed employer in the year, by industry, beside business entry. Falling mobility is the labour side of falling entry.
2. **On the Industry lens:** the industry's mobility against all industries; how many left and joined.
3. **Beside labour rules:** industries with many licensed workers, shown with their mobility. Described, not estimated.

Hours and jobs (Labour Account):

1. **Output per hour,** not per worker. The site's productivity figures read low for industries with many part-time workers; this fixes the cause.
2. **Finer industries:** 86 subdivisions nationally, against 19 divisions.
3. **Vacancies by industry,** as context for labour rules.
4. **Exposure in jobs and hours** for the impact class.

Limits: both are national by industry; state by industry is not published in the tables.

## 6. What the site gains

1. **Biggest barriers, on evidence.** On Legislative levers: standing rules by impact class, with the businesses each reaches. Built in overhaul phase 4 with the stopgap severity; rebuilt on coded severity under version 2.
2. **Register data** (the advanced back end). A plain table of every rule: how it is coded, its marks, its class and exposure figures, the sources used and how each was checked, the industries it reaches, its regulator, family and regime. It downloads as a file. It does not need to be pretty.
3. **What others found.** Review findings and the 65 recommendations move to a labelled panel.
4. **Findings computed by the tool,** each with its coverage stated.
5. **Knock-on exposure** from the input–output tables.
6. **Labour dynamism** and output per hour.
7. **Current concentration** in banking, then other APRA sectors.
8. **Mergers notified,** by industry.

## 7. Order of work

| # | Work | Status |
|---|---|---|
| 1 | Site overhaul phases 4 to 7 ([plan](plan_site_overhaul.md)), with biggest barriers and exposure in phase 4 | Done (14 November 2026, E-180 to E-183) |
| 2 | Framework version 2: schema, coded attributes, impact class, evidence, purpose; the Framework page; Register data | Started (E-184): Register data is built, with a draft severity score for requirements from the attributes already coded. Still to do: settle the weights with the owner; move the impact classes from the marks to the score; code the standing rules among the register items; add the evidence and purpose fields; rewrite the Framework page |
| 3 | "What others found" panel | With 2 |
| 4 | Inputs 1 to 7 in section 5, one at a time | After 2 |
| 5 | Fees and waiting times | When ABLIS arrives |
| 6 | Even coverage of state law | Other branches, alongside |

Each piece ends in a pull request, tests that recompute its figures, and a short methods note.

## 8. For sessions adding legislation

Keep drafting requirements under the current schema. Version 2 adds optional fields; it does not change or remove the ones in use. See "Before you push" in [`notes_for_other_branches.md`](notes_for_other_branches.md).
