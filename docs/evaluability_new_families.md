# Evaluability of the new legislation families

**Date:** 18 October 2026. **Covers:** the 102 records added from the [gap scan](legislation_gap_scan.md) (section 7). **Evidence:**
- the menu's evaluability screen (`alicia menu`; rules in `alicia/src/alicia/menu/screen.py`);
- the blinded power study ([`power_study.md`](power_study.md)), which ran 11 of the families through every estimator layer.

No reform's effect was estimated.

## 1. Rating rule

The screen rates timing and structure mechanically. It does not know whether the outcome data measure the change well or how noisy they are. The ratings here add that, family by family.

| Rating | Meaning |
|---|---|
| **High** | A clean comparison: staggered adoption, or states that never adopted. Outcome data already in the pipeline that measure the change directly. A power-study MDE small enough for a plausible effect, with no systematic error at fake dates or placebo states. Dates confirmed |
| **Medium** | Identifiable, but at least one of: only fairly large effects detectable; the outcome only partly covers the change (diluted); a major confounder at the same time; a short post-period that later data releases will lengthen; some dates unconfirmed |
| **Low** | National or simultaneous change with no comparison; the needed data are firm-level, product-level or not public; too recent; infeasible in the power study; or a placebo check shows bias the design cannot remove |
| **Not yet** | Not in force: a candidate for a plan registered before it starts |

"Plausible effect": about 1–3 entries or exits per 100 businesses for business counts (rates average 12–16), and 1–3% for prices.

## 2. Ratings

| Family (records) | Rating | Main outcome | Smallest detectable effect (best layer) | Why |
|---|---|---|---|---|
| **Mandatory fuel price reporting** (6) | **High** | CPI automotive fuel by capital; fuel retailer entry and exit (4000) | Prices: 6.7% against placebo classes; total error 0.7 log points at fake dates (about 2% detectable), no bias. Entry 2.2, exit 2.2 per 100 | Five staggered cohorts 2016–2021 with Victoria (to 2025) and the ACT never treated. Cautions: NSW's reporting start is unconfirmed (registration deadline used); COVID falls in the TAS and SA windows; WA is always treated and left out |
| **Mandatory e-conveyancing** (5) | **Medium** | Legal services entry and exit (6931) | Entry 2.9, exit 1.8 per 100 (saturated); fake dates error 0.2, no bias | Strong design (five cohorts 2018–2023; the ACT, Tasmania and the NT never mandated), but conveyancing is a small part of legal services, so the effect is diluted. PEXA volumes or IPART pricing would measure it directly. Overlaps the uniform law (2015) and automatic mutual recognition (2021) |
| **2022 building code adoption** (8) | **Medium** | House and residential builders' entry and exit (3011, 3019); CPI new dwellings | Entry 2.7, exit 1.6 per 100; prices 6.5% (placebo classes), fake dates error 1.3 | Staggered and partial adoption 2023–2025, but only one post-reform year of business counts until the 2025-26 CABEE release (due December 2026). Building-cost inflation and builder insolvencies overlap |
| **Contestable VET entitlements** (4) | **Medium** | Training provider entry and exit (8101) | Entry 3.6, exit 3.2 per 100 (saturated) | Staggered 2009–2015, and private-provider entry was large, so plausible effects exceed the MDE. But only not-yet-adopting states can be controls (WA, Tasmania, ACT, NT dates unchecked), Victoria has two pre-years, and VET FEE-HELP overlaps. NCVER provider data (not connected) would sharpen it |
| **NDIS Quality and Safeguards Commission** (8) | **Medium** | Other social assistance entry and exit (8790) | Entry 3.1 (synthetic DiD), exit 3.0 per 100 | Staggered 2018–2020, but the NDIS rollout's demand surge and COVID overlap; only not-yet-treated states as controls. NDIS provider registration data (not connected) are the better outcome |
| **Pharmacist UTI prescribing** (8) | **Medium** | CPI medical and hospital services and pharmaceuticals; pharmacy entry and exit (4271) | Prices: total error 0.2–0.7 log points at fake dates (very precise). Pharmacies: entry 2.9, exit 2.1 per 100 | The design is precise, but the outcomes are indirect: pharmacist fees are in no CPI class, and pharmacy numbers are capped by location rules. MBS GP attendances and PBS antibiotics by state (not connected) are the right outcomes. Most states adopted in 2023-24, so the post-period is short; the Queensland and ACT start days are unconfirmed |
| **CTP insurance markets** (3) | **Medium** | CPI insurance by capital | 7.8% against placebo classes; placebo states and fake dates errors 2.2 and 1.9 (synthetic DiD smaller) | The price design is reasonably precise, but whether CTP premiums sit in the CPI Insurance class must be checked first. Insurer entry counts are not meaningful (few insurers; placebo-state errors up to 7 per 100) |
| **National Energy Customer Framework** (5) | **Medium** | CPI electricity by capital | 7.4% against placebo classes; fake dates error 2.8 (bias +1.6) | Business counts infeasible (59 retailers). SA adopted on the day it deregulated prices and NSW and Queensland deregulated a year later, so only the ACT and Tasmania 2012 cohort isolates the framework. Electricity shows pre-reform drift at fake dates |
| Small-bar licences (2) | Low | Pubs and bars entry (4520) | Entry 4.8, exit 3.6 per 100 | Only NSW 2013 is usable (WA's 2007 change predates the data; SA's date is unconfirmed). Small bars are a small part of the class, and Sydney's lockout laws started in the first year. Licence registers by local area would be needed |
| Commercial property duty (3) | Low | Non-residential property operators (6712) | Entry 5.3, exit 2.4 per 100; placebo states error 0.7 | The effect is on property transactions and business moves, not operators' entry. Valuer-General transaction data are needed. The SA three-step phase-out is a good dose-response design once those data are connected |
| Gaming market structure (2) | Low | Pubs and clubs (4520, 4530) | Entry 5.2 (saturated), exit 2.0 per 100 | A single state each (Victoria 2012, Tasmania 2023). The effect falls on machine ownership and venue revenue, which venue-level gaming data would measure (Victoria publishes them; not connected) |
| Liquor licence entry restrictions (2) | Low | Liquor retailing; pubs and bars | NT moratorium infeasible (6 businesses); Victorian freeze lift: entry 6.8 per 100; exits biased −1.6 at fake dates | The Victorian freeze covered four inner-Melbourne councils, too small for state-level counts. Licence registers by local area are needed |
| Next-day fuel price commitment (2) | Low | Fuel prices | — | Too recent (Victoria March 2026, NT April 2026); the quarterly CPI ends 2025-Q3. Becomes medium or high with station-level price data |
| Taxi and booked-hire licensing (2) | Low | Taxi entry (4623); fares | — | Queensland 2017 sits inside the ride-share family's window; SA's December 2025 buyback is too recent |
| National health practitioner registration (8) | Low | Health care | — | Every state started in the same financial year (WA three and a half months later), so annual data cannot separate them |
| Port leases (3) | Low | Port charges and productivity | — | BITRE Waterline and ACCC stevedoring data are not connected; business counts in port operations are too few |
| Electricity full retail contestability (2) | Low | Electricity retailers; prices | — | Queensland 2007 predates the business data; Tasmania 2014 is one small state, two years after its NECF adoption |
| Planning and zoning, NSW (2) | Low | Retail and residential construction by area | — | Single state, recent, and spatial: needs approvals and business counts by small area |
| East-coast gas interventions (1) | Low | CPI gas by capital | 9.6% against placebo classes; fake-date bias +11 | WA and NT gas prices did not track the east coast before 2022, so the comparison fails the fake-date check |
| Small amount credit caps (1) | Low | Non-depository financing (6230) | Not tested | A dose-response design exists (four states had no cap), but the class is broad (most lenders are not payday lenders). Untested in the power study |
| Other national records (23) | Low | — | — | Tax and investment thresholds, insolvency, R&D, open banking, bank levy, super test, Fair Work changes, childcare fee cap, repair information, Sydney slots, 60-day dispensing, vapes, petrol retail 2007, wheat 2008, Sugar Code, card surcharging 2016 and 2026, EPBC: one national date and no state variation. They need firm-level (ATO, BLADE), product-level (APRA) or route-level data, or an exposure design across industries |
| Non-compete ban; National Competition Policy (2) | Not yet | — | — | Not in force: register a plan before commencement (workers either side of the income threshold; states adopting NCP reforms at different times) |

## 3. Ranking for the next evaluations

By evaluability, highest first:

1. **Fuel price reporting:** prices and fuel retailers; ready now.
2. **E-conveyancing:** a strong design on a diluted outcome; ready now.
3. **2022 building code:** stronger after the December 2026 CABEE release.
4. **VET entitlements** and **NDIS Commission:** ready with business counts; better with NCVER or NDIS provider data.
5. **Pharmacist UTI prescribing**, **CTP** and **the energy customer framework:** prices only, each with a check to make first.

## 4. How these ratings differ from the screen

The screen gives some records higher ratings than here, because it does not see data quality:
- VET entitlements (three "high");
- the Victorian gaming change and two port leases ("high");
- the energy customer framework (ACT "high").

It gives fuel price reporting "medium", because of COVID-period overlap. The power study shows the fuel design stays precise.

## 5. Limits

- **Ratings are judgements on the evidence listed.** They rest on draft records not yet checked by a person.
- **Power uses placebos, not the reform.** A design can be precise and still biased. The own-class placebo checks cover some bias, not all.
- **Several families depend on data not yet connected:**
  - MBS and PBS by state;
  - NCVER provider data;
  - NDIS provider data;
  - venue-level gaming;
  - licence registers;
  - Valuer-General transactions;
  - BITRE Waterline.

  Connecting them would raise several ratings.
