# Barriers to entry and profitability charts: methods note

25 October 2026. The charts recreate, from public data, the barriers-to-entry and profitability analysis in Grattan Institute's *Competition in Australia: too little of a good thing?* (Minifie, Chisholm and Percival, December 2017). Grattan used IBISWorld industry data and Morningstar firm data, which are proprietary. These charts are on the ALICIA website (`alicia site`):
- **The state of competition in Australia** (formerly State and industry growth) has concentration, business entry and barriers to entry. It reads as a story: each section's heading states what the data show for the settings chosen, and is worked out from the same numbers as the chart.
- **Economic conditions** has profitability and market power.

Each section has its own period slider, spanning only the years its data cover, so a slider never offers years its charts can't show:
- **Concentration:** 2002 to 2019 (the RBA figures).
- **Business entry:** 2007-08 to 2024-25 (ABS business counts).
- **Where the barriers to entry are** and **business entry and returns:** income years 2018-19 to 2022-23, the years the ATO publishes company balance sheets by industry. Business counts, entry rates and company figures are all averaged over the same years.
- **Industries in each state:** 1989-90 on for output and jobs, and 2007-08 on for business rates; changing the measure keeps as much of the chosen period as fits.
- **State economies:** 1989-90 on.

On Economic conditions, commodity prices have their own slider, and a state chart whose figures start after the chosen first year says where they start (wages from 1998). Business rates average the yearly rates of the years chosen, the first year included. Words that need explaining have a plain-English definition on hover, focus or tap, every chart names its source with a link, and each page ends with a list of its data sources and a glossary.

Code:
- `alicia/src/alicia/menu/competition.py` (page data);
- `alicia/src/alicia/barriers.py` and `alicia/src/alicia/data/barriers.json` (classification);
- `alicia/src/alicia/pipeline/ato_company.py` (ATO connector);
- `alicia/src/alicia/menu/templates/` (charts).

Tests: `alicia/tests/test_competition.py`.

## Which Grattan figures, where

| Grattan figure | Chart | Page | Data |
|---|---|---|---|
| 1.1 Value added by barriers group | Where the barriers to entry are: a bar table of each group's share of employing businesses, company income, equity and profit, with the three barrier groups together in the top row | Competition | ABS CABEE; ATO Table 4 |
| 1.2, 3.3, 3.4 Concentration | Concentration by industry: every industry's top-4 (10, 20, top 5%) firms' share of sales in the first and last years of the chosen period, sorted by the change, with one industry over time below; 2002–2019 | Competition | RBA RDP 2025-05 (BLADE) |
| 3.6 Entry, exit, net firms created | Business entry and exit; Net businesses created, by state; extended to **entry and exit rates by barriers group** | Competition | ABS CABEE |
| 4.3 Returns against concentration | Business entry and company returns by sector (entry rate in place of concentration, which is not published by sector) | Competition | CABEE; ATO Table 4 |
| 4.1 Return on equity by group | Return on equity by barriers to entry | Conditions | ATO Table 4 |
| 4.2 Super-normal share of profit | How much profit is above the cost of equity (table) | Conditions | ATO Table 4; RBA F2.1 |
| 4.4, A.7 Profit by sector (width equity, height return) | Profit by sector, one group at a time | Conditions | ATO Table 4; RBA F2.1 |
| 5.1, 5.2 Mark-ups | Mark-ups by sector, with group averages | Conditions | ATO Table 4; RBA F2.1 |
| 3.5 Profitability over time | Has profitability changed? Return on equity by group, 2014-15 to 2022-23 | Conditions | ATO Table 4A |
| (new) | Have mark-ups risen? Price over marginal cost by division, 2004–2017 | Conditions | RBA RDP 2025-05 (BLADE) |

Not recreated, because public data cannot support them:
- **Sector concentration ratios** (Figure 1.3) and **international comparisons** (2.1–2.4, A.1–A.6): these need firm market shares.
- **ASX revenue shares** (3.1, 3.2), **profit persistence** and **market-to-book** (4.5–4.7): these need listed-firm panels.
- **The welfare cost of mark-ups** (5.3): this needs demand elasticities by sector.
- **Margins by firm rank** (5.4, 5.5): these need firm-level data.

## The story on the page

The page runs: concentration; business entry by barrier group and for all industries; whether low entry goes with high returns; then industries in each state, with the selected industry's productivity; and state economies. "Where the barriers to entry are" is shelved (owner's request, 29 October 2026): it is folded away at the end of the page, unchanged. Each chart's description sits behind an "i" beside its title, and its notes and sources in one "About this chart" dropdown. The narrative headings follow the data shown, so they change with the period, state, measure and businesses counted:
- **Concentration**: the all-industries change between the first and last years: risen (+1 point or more), fallen (−1 point or more), or barely changed. The summary names the industries where the share rose and fell most.
- **Business entry**: the barrier group with the lowest average entry rate, against low barriers. Fewer new firms start up there when its rate is below the low-barriers rate; otherwise "Entry is no lower behind barriers to entry". With businesses with employees, heavily regulated industries have a lower entry rate than low-barrier industries in every state and in every period checked (2015-16 to 2024-25, 2008-09 to 2024-25, 2020-21 to 2024-25). Counting all businesses, it is mixed, because of rideshare and delivery sole traders.
- **Where the barriers are**: the barrier groups' share of businesses and of company income. By default (2018-19 to 2022-23): 3.7% of businesses with employees (June 2019 to June 2023, averaged), but 19.6% of company income, 22.2% of company equity and 12.4% of company profit.
- **Entry and returns**: from the weighted line of best fit. If entry explains less than 10% of the differences in returns, the heading says low entry does not go with higher returns; otherwise it gives the direction.

Each barrier group's name shows a plain definition and example industries on hover, keyboard focus or tap, including in chart legends (`definition` and `examples` in `barriers.json`).

**Sectors within each group.** Every group can be broken into its sectors (a sector is a listed ANZSIC class, or otherwise an ANZSIC group; see below):
- **New businesses by barrier group**: "Show" ranks the group's sectors by their yearly average rate for the measure, state and years chosen; clicking one shows it over time against its group.
- **Businesses starting and closing**: "Industries" picks all industries or one group, and "Sector" one of its sectors, for any state.
- **Sectors in each group** (under "Where the barriers to entry are"): for the income years chosen, each sector's share of the group's businesses (average count at the end of each year), company income, equity and profit, with its return on equity and entry rate. Company figures follow the data rules below; a sector's left-out years are listed.

Sectors with few businesses have jumpy rates (a handful of entries can move them by tens of points), and the ABS perturbs small counts; the charts give each sector's size on hover.

## Barriers-to-entry groups

Every ANZSIC 2006 class is put in one of six groups:
- the three barrier groups: natural monopolies, scale economies, heavy regulation;
- low barriers;
- tradeable;
- mostly public.

Where Grattan names a sector (its Figures 1.3, 4.4 and 5.2), the class follows Grattan. Elsewhere, a division default applies:
- A, B and C: tradeable;
- O and P: public;
- the rest: low barriers.

The listed exceptions each carry a reason (for example, water and sewerage go to public as mostly state-owned). Grattan called its own allocation "inherently subjective", and so is this one; `barriers.json` records every choice.

Departures from Grattan:
- **Gas supply** is added to natural monopolies (distribution networks).
- **Other deposit-takers, building societies, credit unions and superannuation funds** are added to heavy regulation. They are APRA-regulated, and the ATO moves companies between the deposit-taking classes from year to year, so banks and other deposit-takers form one sector.
- **Toll roads cannot be shown.** ANZSIC 5299 mixes toll road operation with freight brokerage and many small transport-support firms, and the large operators are mostly trusts. So it stays with low barriers.
- **Airlines** are one class: domestic and international are not separable.
- **Wired and wireless telecommunications** are separate classes, but in ATO data most mobile network operators report as wired network operators.

A sector on the website is a listed class (classes with the same label are merged), or otherwise an ANZSIC group.

## Measures

Company figures come from the ATO's Taxation Statistics, Company Table 4:
- **Table 4B**, by five-digit industry code summed to ANZSIC class, income years 2018-19 to 2022-23;
- **Table 4A**, by ANZSIC group, 2014-15 to 2022-23.

A sector made of whole ANZSIC groups takes Table 4A, because Table 4B leaves some industries out in some years. For example, banking is missing in 2018-19 and 2019-20, and half of gambling in 2018-19. A sector that splits a group sums its classes from Table 4B.

For a chosen span of income years, each sector's figures are yearly averages over the years it is published with positive equity. The definitions:
- **Equity** = total assets − total liabilities (book value, including goodwill).
- **Profit after tax** = total profit or loss (accounting profit before tax) − tax payable.
- **Return on equity** = profit after tax ÷ equity, equity-weighted across sectors.
- **Cost of equity** = the average 10-year Australian Government bond yield over the same income years (RBA F2.1) + a 6 per cent market risk premium, the same for every sector. Grattan used the same premium with sector betas from Morningstar, which are not public. The user can override it on the page.
- **Super-normal profit** = profit after tax − cost of equity × equity. Group totals count each sector's shortfall as zero, as Grattan did.
- **Mark-up** = super-normal profit, grossed up at the 30 per cent company tax rate, ÷ total income. A sector with a shortfall counts as zero (Grattan's definition). This is a price premium over full cost. It is not the RBA's price over marginal cost.

Business entry and exit come from the ABS Counts of Australian Businesses (CABEE), by class and state, 2007-08 to 2024-25:
- **Rate** = entries (or exits) per 100 businesses operating at the start of the year.
- **Default: employing businesses only.** Since about 2016, rideshare drivers and delivery riders registered as sole traders have multiplied the counts in taxis, couriers and other transport support. Counting all businesses, the scale-economies entry rate climbs from 16% in 2015-16 to 38% in 2024-25; counting employing businesses, it stays between 11% and 17%. An "all businesses" option remains.

## Data rules

1. **A sector-year with liabilities above assets is left out** of returns, super-normal profit and mark-ups, and listed on the page. The largest is banking in 2021-22: published liabilities exceed assets by about $600 billion in both ATO tables, which cannot be a real sector balance sheet.
2. **Mixed groups in the time series.** Table 4A is by ANZSIC group, so a group whose classes sit in different barrier groups goes where most of its company income is. There are 13 such groups, listed on the page. For example, liquor retailing counts with low barriers in that chart.
3. **CABEE codes** 0310, 0671 and 5229, which are not ANZSIC 2006 classes, are left out (about 20 cells each).

## What the public data show (default view)

These figures use income years 2018-19 to 2022-23, a cost of equity of 8.0% (bond yield 2.0% + 6%), and employing businesses, with each section's slider at its default. Returns are after tax on book equity.

| Group | Equity, $b a year | Return on equity, % | Super-normal profit, $b a year | Super-normal share of profit, % | Mark-up, % | Grattan (2010-11 to 2015-16): return, mark-up |
|---|---|---|---|---|---|---|
| Natural monopolies | 103 | 0.9 | 0.1 | 7 | 0.2 | 12, >10 |
| Scale economies | 74 | 11.4 | 5.6 | 59 | 3.2 | 12, 3 |
| Heavy regulation | 431 | 7.0 | 8.4 | 22 | 3.1 | nearly 13, 2 |
| Low barriers | 1,266 | 11.7 | 61.2 | 40 | 4.2 | about 10, 1.5 |
| Non-traded private | 1,873 | 10.1 | 75.4 | 37 | 3.8 | about 11, 2 |

- **Grattan's central finding, higher returns behind barriers, does not show up in these data for 2018-19 to 2022-23.** The barrier groups earn 6.5% together, against 11.7% with low barriers. The gap comes from a few large sectors:
  - wired telecommunications networks: −2.4% on $41 billion of equity;
  - electricity distribution: below the cost of equity in four of the five years (−14.6% in 2020-21);
  - life insurance: losses in four of the five years; general insurance earned about 4%;
  - casinos: losses in each of 2020-21 to 2022-23.

  At the same time, the largest low-barrier sector, financial asset investing (15.9% on $394 billion), includes investment and holding companies whose assets are shares in other companies. Its equity and profit partly double count other sectors'.
- **Supermarkets** earn 27.9% on book equity, more than three times the cost of equity, consistent with Grattan's finding of supermarket returns more than double it. Besides supermarkets (4.8%), mark-ups above 4% are found in pipeline transport (a small sector), sports betting, lotteries, pathology and diagnostic imaging, passenger car rental and banks.
- **Super-normal profit behind barriers** is about $14 billion a year, against Grattan's $16 billion or more.
- **Over time** (Table 4A), return on equity moves with the cycle and COVID, with no upward trend in the barrier groups from 2014-15 to 2022-23:
  - natural monopolies: 5.4% to 0.1%;
  - heavy regulation: 11.6% to 10.1%;
  - scale economies: 4.3% to 12.4%;
  - low barriers: 9.9% to 12.1%.
- **Business entry** (employing businesses, average of 2007-08 to 2024-25): heavy regulation 8.7%, tradeable 6.6%, low barriers 11.6%, scale economies 13.2%, natural monopolies 11.9%. The natural-monopoly figure reflects small firms in classes that also hold the network operators (airport support services, telecommunications). The network classes themselves (electricity transmission and distribution, gas supply, rail freight, pipelines, ports) have entry rates of 6–9% a year, pooled over 2007-08 to 2024-25.
- **Entry and returns** (both averaged over 2018-19 to 2022-23): the equity-weighted fit across sectors is +0.53 points of return on equity per point of entry rate, and entry explains 6% of the variation. The barrier groups explain 13% (Grattan: 7%).
- **Concentration and mark-ups (RBA, BLADE):**
  - the all-industry top-4 share was 38.7% in 2002 and 37.9% in 2019, while retail rose from 33.5% to 45.8%;
  - the all-industry harmonic mark-up rose from 1.19 (2004) to 1.26 (2017).

## Limitations

- **Companies only.** Sole traders, partnerships and trusts are out. So are state-owned businesses that pay tax equivalents to their state: several electricity networks, water utilities and ports, which is why electricity transmission and pipelines look small.
- **Industry is self-reported** by the company, and large companies change it, so sector totals jump between years. Averages over several years damp this.
- **Book equity includes goodwill.** Grattan removed it, so returns in sectors built by acquisition read lower here.
- **One beta for every sector.** This overstates super-normal profit in low-risk regulated sectors and understates it in risky ones.
- **Descriptive only.** None of these charts identifies a causal effect of barriers to entry. Public data are too aggregated for firm-level mark-ups or concentration by sector (BLADE is restricted).

## Productivity

- **Output per worker** (Industries in each state): output, adjusted for inflation (State Accounts, chain volume), divided by the number of people employed (Labour Force, Detailed, four surveys averaged over the financial year). Its growth is the average yearly growth between the first and last years chosen; its level is at current prices, in $ thousand a worker. It counts people, not hours, so industries with many part-time workers read lower. Employment in small industries in small states is a survey estimate that jumps around, so their productivity is noisy. All industries includes the rent of owner-occupied homes, which has no workers, so its level reads high.
- **ABS labour productivity**: the ABS's official output per hour worked, by industry, Australia (Estimates of Industry Multifactor Productivity, 5260.0.55.002, hours-worked basis), for the 16 market-sector industries, 2005-06 on; read from the costing parameters. It is not published for public administration, education or health. On the productivity chart it is an index that starts on the Australia output-per-worker line in its first year shown.
- The State Accounts publish output by state only for the 19 industries, so productivity by state cannot go below that.

## Excel export

Every chart that follows a slider or a drop-down list has a **Download Excel** button. The workbook has, for each chart, a sheet with the chart rebuilt as a native Excel chart from the numbers below it (as on the page, unrounded), and an About sheet with the settings in use, each dataset's link, release and licence, the notes and the definitions. Three charts have no exact Excel form:
- **Profit by sector**: every bar has the same width (each sector's equity is in the table);
- **Concentration by industry**: the two years are paired bars rather than dots joined by a line;
- **shaded periods**: drawn as light columns reaching the top of the axis; the table's "Shaded" column only draws them.

Code: `alicia/src/alicia/menu/templates/xlsx.js` (decision E-84). Tests: `alicia/tests/test_xlsx_export.py`.

## Reproduce

```bash
cd alicia
uv run alicia pipeline build ato_company        # ATO Company Table 4, 2014-15 to 2022-23 (nine workbooks)
uv run python -c "from alicia.pipeline import controls; controls.build(['national_month'])"   # RBA I2 and F2.1
uv run alicia site -o ../site                    # the pages
```
