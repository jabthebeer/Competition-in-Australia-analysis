# Barriers to entry and profitability charts: methods note

25 October 2026. The charts recreate, from public data, the barriers-to-entry and profitability analysis in Grattan Institute's *Competition in Australia: too little of a good thing?* (Minifie, Chisholm and Percival, December 2017). Grattan used IBISWorld industry data and Morningstar firm data, which are proprietary. These charts are on the ALICIA website (`alicia site`):
- **State and industry growth** has barriers to entry and business dynamism.
- **Economic conditions** has profitability and market power.

Both pages now pick their time span with a slider instead of a drop-down list. Words that need explaining have a plain-English definition on hover, focus or tap, every chart names its source with a link, and each page ends with a list of its data sources and a glossary.

Code:
- `alicia/src/alicia/menu/competition.py` (page data);
- `alicia/src/alicia/barriers.py` and `alicia/src/alicia/data/barriers.json` (classification);
- `alicia/src/alicia/pipeline/ato_company.py` (ATO connector);
- `alicia/src/alicia/menu/templates/` (charts).

Tests: `alicia/tests/test_competition.py`.

## Which Grattan figures, where

| Grattan figure | Chart | Page | Data |
|---|---|---|---|
| 1.1 Value added by barriers group | Where the barriers to entry are: each group's share of employing businesses, company income, equity and profit | Growth | ABS CABEE; ATO Table 4 |
| 1.2, 3.3, 3.4 Concentration | Has concentration risen? Every industry's top-4 (10, 20, top 5%) firms' share of sales in the first and last years of the chosen period, sorted by the change, with one industry over time below; 2002–2019 | Growth | RBA RDP 2025-05 (BLADE) |
| 3.6 Entry, exit, net firms created | Business entry and exit; Net businesses created, by state; extended to **entry and exit rates by barriers group** | Growth | ABS CABEE |
| 4.3 Returns against concentration | Business entry and company returns by sector (entry rate in place of concentration, which is not published by sector) | Growth | CABEE; ATO Table 4 |
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

These figures use income years 2018-19 to 2022-23, a cost of equity of 8.0% (bond yield 2.0% + 6%), and employing businesses with the slider at 2014-15 to 2024-25. Returns are after tax on book equity.

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
- **Business entry** (employing businesses, average of 2015-16 to 2024-25): heavy regulation 8.0%, tradeable 6.6%, low barriers 11.7%, scale economies 13.1%, natural monopolies 12.7%. The natural-monopoly figure reflects small firms in classes that also hold the network operators (airport support services, telecommunications). The network classes themselves (electricity transmission and distribution, gas supply, rail freight, pipelines, ports) have entry rates of 6–9% a year, pooled over 2007-08 to 2024-25.
- **Entry and returns:** the equity-weighted fit across sectors is +0.36 points of return on equity per point of entry rate, and entry explains 3% of the variation. The barrier groups explain 13% (Grattan: 7%).
- **Concentration and mark-ups (RBA, BLADE):**
  - the all-industry top-4 share was 38.7% in 2002 and 37.9% in 2019, while retail rose from 33.5% to 45.8%;
  - the all-industry harmonic mark-up rose from 1.19 (2004) to 1.26 (2017).

## Limitations

- **Companies only.** Sole traders, partnerships and trusts are out. So are state-owned businesses that pay tax equivalents to their state: several electricity networks, water utilities and ports, which is why electricity transmission and pipelines look small.
- **Industry is self-reported** by the company, and large companies change it, so sector totals jump between years. Averages over several years damp this.
- **Book equity includes goodwill.** Grattan removed it, so returns in sectors built by acquisition read lower here.
- **One beta for every sector.** This overstates super-normal profit in low-risk regulated sectors and understates it in risky ones.
- **Descriptive only.** None of these charts identifies a causal effect of barriers to entry. Public data are too aggregated for firm-level mark-ups or concentration by sector (BLADE is restricted).

## Reproduce

```bash
cd alicia
uv run alicia pipeline build ato_company        # ATO Company Table 4, 2014-15 to 2022-23 (nine workbooks)
uv run python -c "from alicia.pipeline import controls; controls.build(['national_month'])"   # RBA I2 and F2.1
uv run alicia site -o ../site                    # the pages
```
