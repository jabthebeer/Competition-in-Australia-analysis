# Forward plan: benchmarking Australia's business dynamism against comparable economies

3 November 2026. Status: **approved** (decisions D-1 to D-8 as recommended, E-102). **P0 done**: the common industry groups and ANZSIC concordance ([note](international_industry_groups.md)) and the peer ranking ([note](international_peers.md)). Core peer group approved (E-103): Canada, the UK, New Zealand, France, Spain and Italy (Italy in place of the ranking's Chile, which has no OECD business demography). Industries classified differently in other countries are flagged on the website (a † with a hover note). **P1 done** (E-104): connectors for every source below, for all 38 members; what each covers for Australia and the peers is in the [coverage note](international_data_coverage.md). The main gaps: the UK's OECD business demography ends in 2018; Canada has no survival or high-growth series; Australia's size structure needs ABS data. **P2 done** (E-105): every measure on common definitions by group for Australia, the OECD members and the US, each rated for comparability ([methods note](methods_international_benchmarks.md)). Australia's gross birth and death rates turn out to be lower bounds of the OECD's (CABEE does not count businesses crossing the one-employee threshold), so they are rated low; the net change in employer businesses is the comparable entry measure (medium). The owner accepted that rating, noting it may be revisited (E-106). **P3 done** (E-106): the benchmark engine and flag rule, cross-checked in R; 23 of 262 comparisons flagged ([benchmarks](international_benchmarks.md)). **Reordered** (E-107): the website comes next (P4, §7.1); validation is P5; the policy menu is paused (P6). **P4 built** (E-107): items 1 to 4 of §7.1 are on the page ([methods](methods_competition_charts.md#similar-economies-international-comparisons)). **Revised** (E-109): Australia's output, jobs and productivity now come from the ABS (STAN labels Australia's financial years by the year they start and its jobs are calendar years on ISIC); the formal tests were re-run (23 flags, 8 changed). **States** (E-110): the comparisons follow the selected state, from the same ABS sources; states are not tested for flags.

## 1. Goal

For each industry statistic on The state of competition in Australia, show:
- Australia's value;
- the average of comparable economies, with their range;
- whether Australia's gap is large and persistent.

Then, for industries where Australia lags, point to a **standardised policy menu**. This is a fixed catalogue of candidate interventions, such as removing restrictive legislation, lowering barriers to entry, or supporting entrants. It is linked to the register items and recommendations that already apply to that industry.

The output is diagnostic. A gap prompts a closer look at an industry; it does not prove that a policy caused it, or that a given intervention would close it.

## 2. What the data allow (checked 3 November 2026)

All of these are on the OECD's SDMX service (`sdmx.oecd.org`), which the project already uses for its product market regulation, services trade and foreign investment connectors. The checks used each dataflow's `availableconstraint` endpoint.

| Measure | International source (dataflow) | Australia in it? | Peers in it | Years |
|---|---|---|---|---|
| Employer business births, deaths, churn | SDBS employer business demography (`OECD.SDD.TPS,DSD_SDBSBD_ISIC4@DF_BD_EMP_B_D`) | **No** | Canada, New Zealand, UK, Norway, Sweden, Denmark, Finland, Netherlands, Ireland, Israel, Korea, Japan; **not the US** | 1989–2024 |
| Employer business survival | SDBS (`DF_BD_EMP_S`) | No | as above | to confirm |
| High-growth enterprises | SDBS (`DF_BD_EMP_HG`) | No | as above, except Japan | 2004–2024 |
| Size structure (enterprises, employment, value added by size class) | SDBS structural business statistics (`DSD_SDBSBSC_ISIC4@DF_SDBS_ISIC4`) | **Only 2007–2010, all sizes together** (corrected in P1: the availability listing names Australia, but its data stop in 2010 and have no size classes) | all core peers; the US only 2010–2015 | 1995–2024 |
| Output, employment, hours (productivity by industry) | STAN 2025 (`OECD.STI.PIE,DSD_STAN@DF_STAN_2025`) | Yes | all | 1949–2025 |
| Product market regulation, economy-wide and by sector | PMR (`OECD.ECO.GCRD,DSD_PMR@DF_PMR`) | Yes | all | 2018, 2023 |
| Services trade restrictiveness, 19 sectors | STRI (`OECD.TAD.TPD,DSD_STRI@DF_STRI_MAIN`) | Yes | all | 2014–2025 |
| Quarterly entries, exits and bankruptcies (trends) | Timely indicators of entrepreneurship (`OECD.SDD.TPS,DSD_TIE@DF_TIE`) | Yes | Canada, New Zealand, US, UK, Nordics, Netherlands | to 2026 |

Australian business entry and exit therefore come from the ABS business register (CABEE, already in the project). The US would come from the Census Bureau's Business Dynamics Statistics; its availability by sector is still to confirm. Neither is on the OECD's definitions, so the comparison needs harmonisation (§4) and carries a comparability rating.

Not available on comparable terms, so **left out of v1**:
- **Concentration and mark-ups by industry across countries.** The OECD's estimates use restricted firm-level data, and the RBA's Australian figures (from BLADE) use different measures.
- **Young-firm employment shares.** Australia's place in the OECD's DynEmp study is not confirmed.
- **Productivity levels across countries.** There are no industry-specific purchasing power parities, so v1 compares growth rates, not levels.

## 3. Comparable economies

The proposal is a **data-driven peer group, fixed for each data vintage and approved by the owner**:
- **Similarity** is ranked across OECD economies on four things: industry structure (each industry's share of output, from STAN), GDP per head, population, and trade openness.
- **A core group** of the 5 to 8 most similar economies is the comparator. The likely candidates are Canada, New Zealand, Norway, the UK, the Netherlands and the Nordics, but the ranking decides.
- **The OECD median** is shown alongside as a second comparator.
- **Robustness:** every result is checked with each peer left out in turn, and against a simple fixed list (Canada, New Zealand, Norway, UK, US).

## 4. Making the statistics comparable

1. **Industries.** ANZSIC 2006 divisions are mapped to ISIC Rev. 4 sections using the ABS concordance, forming about 15 common industry groups. Where the classifications split differently, divisions are merged: for example, ANZSIC D includes waste, which ISIC puts in E. The mapping and every merge are recorded in a JSON file, as `barriers.json` is.
2. **Definitions.** Each Australian series is matched to the OECD definition as closely as the data allow: employer enterprises (at least one employee), births rather than all registrations, and calendar years versus financial years. Each industry × measure comparison is rated high, medium or low comparability, and low-rated comparisons are shown but never flagged. Where an international source includes Australia (STAN, SDBS structural statistics, PMR, STRI), its Australian figure is used rather than the ABS's, so that the comparison is like for like.
3. **Business cycle and COVID.** Comparisons use multi-year averages (for example 2015–2019 and 2022–2024) as well as the latest year.

## 5. The benchmark

For each industry × measure, the benchmark gives:
- Australia's value;
- the peer mean and median, and the 25th to 75th percentile range;
- Australia's rank;
- the gap as a share of the peer median, and in peer standard deviations;
- how the gap has changed over time.

A gap is **flagged** when all of these hold:
- Australia is below (or, for exit and concentration-type measures, above) the peer interquartile range;
- the gap persists in most years of the window;
- it survives leaving each peer out;
- the comparison is rated at least medium.

The thresholds are an owner decision (D-8). With only 5 to 8 peers, the page shows ranges, not significance stars.

## 6. The standardised policy menu

The menu is built on two frameworks:
- **The register's eight-driver productivity framework** (`docs/productivity_framework.md`), so the menu and the legislation menu speak the same language.
- **The OECD Competition Assessment Toolkit's four screening questions.** Does a rule limit the number or range of suppliers, limit their ability to compete, reduce their incentive to compete, or limit consumers' choice and information?

The menu is a fixed catalogue of about 12 to 15 levers, each recording:
- what it addresses;
- the pattern of indicators that points to it;
- the evidence for it, with references compiled and checked in Phase 4 rather than asserted here;
- its risks.

Candidate levers include:
- removing quantity or ownership limits;
- occupational licensing reform and mutual recognition between states;
- lighter start-up administration;
- access regimes for networks;
- merger control and competition enforcement;
- open procurement;
- trade and foreign investment liberalisation;
- insolvency and exit reform;
- support for entrants, such as grants, finance or tax concessions, offered only where there is evidence of a market failure such as credit constraints;
- diffusion and skills.

**A diagnostic tree maps patterns to levers.** For example:
- Low entry combined with restrictive sector regulation (PMR, STRI or register items) points to removing or relaxing those rules.
- Low entry where regulation is light but scale or networks dominate points to access regimes and competition policy, not subsidies.
- Low entry with low survival points to costs, finance and exit rules.

Each flagged industry then lists the levers it triggers, the register items that apply to that industry (existing settings, reforms and recommendations), and a link to the Policy costing tab for estimating effects.

## 7. Phases

| Phase | Work | Output |
|---|---|---|
| P0 | Owner decisions (§8); ANZSIC to ISIC concordance; peer-similarity ranking | Concordance file; peer group for approval |
| P1 | Connectors: SDBS business demography (births, deaths, survival, high growth); SDBS structural statistics; STAN 2025; PMR, STRI and FDI RRI extended to the peers (country list only); timely entrepreneurship indicators; US Business Dynamics Statistics. Each with manifests, `data/SOURCES.md` rows and licences | Processed panels |
| P2 | Harmonise the Australian series to the OECD definitions; rate comparability; methods note | `docs/methods_international_benchmarks.md` |
| P3 | Benchmark engine: peer statistics, gaps, persistence and leave-one-out flags; tests on synthetic data; R cross-check | Benchmark tables |
| P4 | **Website (now the focus, E-107).** International comparisons on The state of competition in Australia, built for people to read: see §7.1 | Page; Excel exports; methods note |
| P5 | Validation against the OECD's own published comparisons for Australia; sensitivity to peer set, years and definitions | Validation note |
| P6 | Policy menu catalogue and diagnostic rules; register links; evidence synthesis (Cowork); owner review. **Paused** at the owner's request (3 November 2026, E-107) | `policy_menu.json`; review sheet |

### 7.1 Phase P4: the website

The comparisons go where readers already look, so the international figures sit beside the Australian ones rather than in a separate tab (D-7). The main focus is the "Industries in each state" section and the selected industry below it.

1. **Industries in each state, heatmap.** A "Similar economies" column after "Aus." gives the core peers' median for the measure shown, where there is a comparable international one (output growth, jobs growth, productivity growth, business entry, exit and net entry, the last three on employer businesses). A marker says whether Australia is below, within or above the peers' middle half, in words and shape as well as colour; hover, focus or tap gives the figures, the peers and the comparability rating.
2. **Industries in each state, new chart: Australia against similar economies, by industry.** One row per industry group: the peers' middle half as a band, their median as a tick, each peer as a small dot (named on hover), and Australia as a large dot, with its position written at the end of the row. A menu picks the measure (growth, productivity, business dynamics, survival, sector regulation and services trade restrictiveness). The years follow the section's slider. Selecting a row opens that industry below.
3. **Selected industry.** The output, jobs and productivity charts gain the peers' median and middle half as a line and band (with a chip to hide them). A new card compares the industry with the peers on every measure, one row each, with the rating and the result of the formal test (P3) for each window.
4. **For every new element:** keyboard and touch access, text equivalents for each row, shapes and words as well as colour, an Excel download with the figures, sources and the definitions, the † notes where the classification differs, and a short "About this chart" with the method and its limits. Australian financial years are shown against the calendar year they end in.

The connectors stay in Python, as the rest of ALICIA does (owner decision, 18 October 2026). The benchmark statistics get an R cross-check.

## 8. Decisions (approved 3 November 2026 as recommended, E-102)

- **D-1 Peer group:** a data-driven similarity ranking with an approved core group (recommended), or a fixed list. If fixed, which countries?
- **D-2 Comparator:** median with the interquartile range, with the mean shown (recommended), or the mean alone ("the average").
- **D-3 Industry detail:** about 15 common ISIC groups in v1 (recommended); finer detail later where the data allow.
- **D-4 Measures in v1:** recommended are entry, exit and churn; survival; firm size structure; labour productivity growth; and regulation (PMR, STRI). High-growth firms would be shown for peers only. Concentration and mark-ups would be left out across countries.
- **D-5 Australian series:** accept the ABS register harmonised to OECD definitions, rated medium comparability (recommended); or first ask the ABS whether it can supply OECD-consistent employer demography.
- **D-6 Policy menu basis:** the eight drivers plus the OECD toolkit's four questions (recommended). Should entrant subsidies be in the menu, and under what conditions?
- **D-7 Website:** overlays on the existing page plus a new "How Australia compares" section (recommended), or a separate tab.
- **D-8 Flag rule:** recommended is outside the peer interquartile range, in most years of the window, surviving leave-one-out, at medium comparability or better.

## 9. Limits

- **Comparability.** Australia and the US are not in the OECD's employer business demography, so their entry and exit rates rest on harmonisation and carry more uncertainty than the European, Canadian and New Zealand figures.
- **Small samples.** With few peers, ranges are wide and a single country can move the average; hence the leave-one-out checks.
- **What is missing.** Regulation indicators (PMR, STRI) are national and only partly sector-specific. Public data do not support cross-country concentration or mark-ups.
- **What a flag means.** A flag says where to look, not why a gap exists. Candidate levers go through the register's review and due-diligence steps before any recommendation.
