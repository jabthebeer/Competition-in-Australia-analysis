> Research note for [`forward_plan_policy_costing.md`](../../forward_plan_policy_costing.md), compiled on 22 October 2026 by a Claude Code research agent from the sources listed. Figures carry the agent's verification tags where given ([P] primary source read, [A] abstract or official summary, [S] secondary only, UNVERIFIED). Downloaded copies mentioned below were kept in a temporary session folder and are not committed. Nothing here is a default parameter until it passes the P3 evidence-library check.

# Productivity-impact parameters by policy channel, for an Australian policy calculator (verified to 22 Oct 2026)

**Verification tags.** Every figure carries one of these:
- **[P]** I read it in the primary document (full text).
- **[A]** I read it in the abstract or the publisher's or official summary.
- **[S]** Only from secondary coverage or search excerpts. Use with care.
- **UNVERIFIED**: I could not confirm it from any source.

Where I wrote a formula myself rather than taking it from a source, it is labelled **(derived)**.

---

## 0. General frameworks that map policy features to productivity

**OECD reform quantification framework (Égert & Gal 2016, ECO/WKP(2016)78, WP 1354) [P]**
- It is a production-function aggregation, with MFP measured as Harrod-neutral and α = 0.33:
  `Δln(Y/N) = Δln(h) + [α/(1−α)]·Δln(K/Y) + Δln(L/N_wa) + Δln(N_wa/N)`
- Each component is a long-run panel elasticity (dynamic OLS, error-correction speed about −0.03 to −0.05 a year for MFP and K/Y, about −0.2 for employment).
- The effects are linear: doubling the change in the indicator doubles the impact.
- Long-run coefficients (Table 1):
  - MFP on ETCR (energy, transport and communications regulation, scale 0–6): −0.037 to −0.047.
  - K/Y on ETCR: −0.035 / −0.025.
  - K/Y on EPL (employment protection): −0.152.
  - MFP on trade openness: 0.006–0.008.
  - MFP on business R&D: 0.047–0.071.
  - K/Y on corporate tax as % of GDP: −0.024 / −0.026.
  - K/Y on log relative investment prices: −0.377 / −0.608.
- Caveat in the paper itself: overall ETCR "has large standard errors" once year fixed effects are added.
- A preliminary 2018 update (Égert, OECD 2023 slides) [P] gives ETCR→MFP of −0.041 long run and −0.014 short run, and ETCR→K/Y of −0.024.

**Productivity Commission (PC) 2024, *National Competition Policy: modelling proposed reforms* [P]**
- Models: CGE models "PC National" (114 industries) and VURM (Victoria University Regional Model, Centre of Policy Studies, 92 industries), both on 2018-19 databases.
- Three approaches:
  - Scenario or "outer envelope" estimates.
  - An "elasticity approach": an arbitrary 1% or 0.1% productivity shock to the affected sectors, with results "roughly linearly related to the shock".
  - Case studies.
- Headline: 26 reforms raise GDP by **$26–45bn, or 1.0–1.7% of GDP** (2023-24 dollars, long run).
- Largest items:
  - Occupational licensing: +$5.2–10.3bn (+0.19–0.39%).
  - Banking: +$3.5–6.6bn.
  - Tariff removal: +$3.3–6.7bn (+0.13–0.25%).
  - Modern methods of construction: +$2.9–5.7bn.
  - Restraint of trade (non-compete) clauses: +$2.6–5.1bn (+0.10–0.19%).
- Calibration anchor for the calculator: an illustrative **0.1% labour-productivity rise across the economy → +0.10% GDP (+$2,646m)**.
- History quoted in the same report:
  - Industry Commission (1995) projected the Hilmer reforms at +5.5% of GDP.
  - PC (2005) ex post assessment: +2.5%.

**PC 2025 NCP analysis, final report released 19 Dec 2025 [P]**
- Aligning standards with international ones: **$1.1–3bn a year (0.04–0.11% of GDP)**. This replaces the interim estimate of $1.9–3.8bn.
- National licensing for high-risk occupations "may not significantly affect productivity or GDP". A paramedic natural experiment found no significant wage effect.

**Other frameworks**
- PC 2017 *Shifting the Dial* [P]: the package "eventually" yields about $80bn a year; road-network efficiency alone ≈0.7% of GDP (~$20bn).
- IMF (Bouis, Duval & Eugster 2016, WP/16/114) [A]: large cuts to entry barriers in network industries raise output and labour productivity over five years, mainly through TFP. The summary gives no coefficients.
- I found **no published Treasury macro-modelling of the Harper Review**. The Review recommended PC modelling, and I could not locate a separate exercise.

---

## 1. Regulatory burden as a resource cost

**(a) Mechanism.** Labour and capital spent on compliance produce no measured output, so measured MFP falls. Delay costs tie up capital (see channel 10).

**(b) Formula (derived).**
- Treat a change in compliance cost ΔC as a pure input cost.
- Industry value-added MFP: `ΔlnMFP_i ≈ −ΔC_i / GVA_i`.
- Aggregate, using Domar weights: `ΔlnMFP_agg ≈ −ΣΔC_i / GDP`.
- Long-run GDP with K/Y held constant (Harrod-neutral, as in Égert–Gal): `ΔlnY ≈ ΔlnMFP / (1−α)`. With α = 0.41 this is about 1.7× the MFP effect.
- Exclude transfers such as fees, and any part of "substantive compliance" that produces unmeasured benefits.

**(c, d) Estimates**

| Source | Figure | Tag |
|---|---|---|
| PC 2025, *Creating a more dynamic and resilient economy* | Compliance and delay costs of Australian Government regulation **≈$115–160bn a year** | [P] |
| PC 2025 (same report) | Recommended target: **−$10bn a year by 2030**, a 6–9% cut; 2014–16 policy cut costs by about 6% | [P] |
| PC 2025 (same report) | Housing regulation costs **≈$28.6bn a year, "around 1% of total GDP"**; adds $135k–320k per new house and $40k–175k per unit | [P] |
| Deloitte Access Economics 2014, *Get out of your own way* | Total cost of rules **$250bn a year**. Government rules: **$27bn to administer + $67bn to comply**. Self-imposed private rules: **$155bn** ($21bn + $134bn). "1 in 11" employed Australians work in compliance | [S] — primary PDF unreachable; figures from 2014 press coverage (Quarry Magazine, Consultancy.uk); totals reported as $94bn or $95bn |
| IPA | Red tape costs **$176bn a year (11% of GDP)** in forgone output | [S]; method UNVERIFIED |
| European Commission | 25% cut in EU administrative burdens → **+1.4% of EU GDP (~€150bn)** medium term; CPB 2004 estimate 1.6%; base burden €123.8bn | [S] |

Notes on the PC 2025 compliance-cost range:
- The lower bound scales the official 2013 estimate of $65bn by nominal GDP growth.
- The upper bound is Mandala (2025).
- Implied share of GDP is about 4–5.6%, using the GDP figure implied by the PC's own housing estimate (derived).

**(e) Caveats.**
- These are gross costs; benefits are not netted off.
- The PC's range comes from scaling a 2013 estimate, not a new baseline costing.
- The EC's GDP figure implies a multiplier of roughly 5 on direct savings, which comes from CPB's general-equilibrium model. Treat it as an upper bound.

## 2. Capital deepening (user cost of capital)

**(a) Mechanism.** Taxes, depreciation rules, delays and risk raise the required pre-tax return. That shrinks the capital stock and lowers labour productivity.

**(b) Formulas.**
- Hall–Jorgenson user cost (textbook form): `c = q(r + δ − π^e)(1 − τz − k)/(1 − τ)`, where τ = company tax rate, z = PV of depreciation deductions, k = investment credit.
- `ΔlnK ≈ −σ·Δln c` (long run, CES), or apply an investment elasticity.
- `ΔlnLP = ΔlnMFP + α·Δln(K/L)`.

**(c) International parameters**
- Chirinko, Fazzari & Meyer (1999, *J Public Econ* 74:53–80): user-cost elasticity **≈ −0.25** [A].
- Chirinko, Fazzari & Meyer (2011, *JBES*): capital–labour substitution elasticity σ **= 0.40** [A].
- Hassett & Hubbard (2002) consensus range **−0.5 to −1**, as cited by Zwick & Mahon [P].
- Zwick & Mahon (2017, *AER*) [P, NBER version]:
  - Bonus depreciation raised eligible investment by **10.4% (2001–04)** and **16.9% (2008–10)**.
  - Tax-term elasticity **−1.6**; elasticity with respect to (1−τz) **7.2**.
  - Small firms respond 95% more than large firms.

**(d) Australian parameters**
- **Capital share of market-sector factor income ≈ 41%** (peak 44% in 2011-12). Source: Treasury Economic Roundup 2017 (Campbell & Withers), citing ABS 5260.0.55.002 Table 14 [P].
- Treasury WP 2016-02 (Kouparitsas, Prihardini & Beames), company tax cut from 30% to 25%, long run, lump-sum financed [P]:
  - **GDP +1.2%, GNI +0.8%, investment +2.8%, real wages +1.1%, employment +0.4%.**
  - PIT-financed: GDP +1.0%. Spending-financed: GDP +1.1%.
  - 35–50% of the revenue cost is recovered.
  - Labour/non-structures capital elasticity 0.9 (range 0.4–1.4).
- External modelling in Treasury's 2016-17 Budget note [P]: Independent Economics GDP +0.9%; KPMG GDP +0.8%.
- PC 2025, *Resilient economy* [P]:
  - Preferred package (20% rate below $1bn revenue, 28% above, plus a 5% net cash-flow tax): investment +2.2% (~$10bn).
  - GDP: headline "+$13bn (0.5%)"; elsewhere CGETAX +0.7% and VURMTAX +0.4%. The report is internally inconsistent here.
  - Labour productivity +0.4–0.5%.
  - Per ~$7bn a year of revenue, a cut to 25% raises investment by **+2.3%**. A base change roughly doubles that: 33% partial expensing gives investment +4.9% and GDP +1.3%; an ACE gives investment +5% and GDP +1.3%.
  - The PC calls Australian empirical evidence "limited and less conclusive".

**(e) Caveats.**
- Results are long run (Treasury: no explicit timeframe).
- GNI gains are much smaller than GDP gains because foreign owners capture part.
- CGE results depend on the assumed rent share and the capital-mobility assumption.

## 3. Entry, exit and business dynamism

**(a) Mechanism.** Entry costs deter entrants. Weaker entry and exit slows reallocation of resources and slows laggard firms' catch-up to the productivity frontier.

**(b) Formulas.**
- Convergence: `g_i = β1·gap_i + β2·(entry_rate × gap_i)`.
- Changing the entry rate changes productivity growth: `Δg_i = β2·Δentry·ln(LP_frontier/LP_i)`.
- Aggregate reallocation term from Olley–Pakes / FHK decomposition.

**(c) International**
- Djankov et al. (2002, *QJE*), 85 countries [P]:
  - World averages: about 10 procedures, 47 business days, cost **47% of GDP per capita**.
  - **Australia: 2 procedures, 2 days, cost 2.25% of GDP per capita** (3.05% including entrepreneur's time).
- Klapper, Laeven & Rajan (NBER 2004 version of *JFE* 2006) [P]:
  - Moving from Italy's entry cost (20% of GNP per capita) to the Czech Republic's (8%) raises the high-entry-minus-low-entry industry gap in **entry rates by 0.5 pp** (about 10% of the mean gap).
  - It raises the same gap in **value-added-per-worker growth by 0.7 pp**.
- Foster, Haltiwanger & Krizan (2001) [P]: net entry accounts for **25–26% of US manufacturing MFP growth, 1977–87**.
- Branstetter et al. (2014, *EJ* 124:805–832), Portugal "On the Spot Firm": **magnitudes UNVERIFIED**; I could not retrieve them.
- Adalet McGowan, Andrews & Millot (2018, *Econ Policy*) [P]: cutting the share of capital in zombie firms to the sample minimum would raise business MFP by **0.6% on average across 9 countries (range 0.1% France to 1.4% Spain)**.

**(d) Australian**
- Andrews & Hansell (Treasury WP 2019-06; *Econ Record* 2021) [P]:
  - Allocative efficiency puts business-sector labour productivity **≥20% above** a random allocation.
  - Weaker reallocation since 2012 drags labour productivity growth by **≈0.15 percentage points a year by 2016**, about a quarter of the slowdown.
- Andrews, Hambur, Hansell & Wheeler (Treasury WP 2022-01) [P]:
  - Entry-interaction coefficient **0.009** per pp of entry rate (baseline convergence speed 0.415).
  - Moving from the 10th to the 90th percentile of entry rate (8% → 16%) raises convergence speed by 4.8 pp (~10%).
  - Average entry rate fell from **14.5% to 11.5% (2004–16)**. This explains about ¾ of the convergence slowdown; rising mark-ups explain ½–⅔.
- Bakhtiari (2019, *Econ Record*) [A/S]: entry declining and exit risk rising over 2002–15. Qualitative only.

**(e) Caveats.** The Australian results are reduced-form correlations on BLADE microdata, not causal policy elasticities.

## 4. Size-based thresholds and bunching

**(a) Mechanism.** Regulation that switches on at a size threshold acts as an implicit tax on growth. Firms bunch below it and resources are misallocated.

**(b) Heuristic.** Welfare cost ≈ (implicit tax wedge) mapped through structural estimates. Garicano, Lelarge & Van Reenen (GLVR) put a 2.3% labour-tax equivalent at 1.3–3.4% of GDP. Scaling that to Australia would rest on strong assumptions.

**(c) International**
- Garicano, Lelarge & Van Reenen (2016, *AER* 106(11)) [A], France's 50-employee rules:
  - Equivalent to a **2.3% variable tax on labour**.
  - Welfare cost **3.4% of GDP** with French wage rigidity; **1.3%** if wages are fully flexible.
- Gourio & Roys (2014, *QE*) [A]:
  - Cost ≈ a sunk cost of about **1 year of average salary** plus a **0.04% payroll tax**.
  - Removing it raises output per worker by **slightly under 0.3%**, about 10× smaller if entry is elastic.

**(d) Australian**
- e61 Micro Note 23 (Andrews, Buckley & Lee 2024), SA payroll-tax threshold raised to $1.5m [P]:
  - Firms just below the threshold **+21%**, just above **−18%**.
  - The marginal rate jumped from 0 to about 27%.
  - Firms just above cut payrolls by **$5.9m (3.3%)**, more than offsetting a +$3.5m rise at smaller firms.
- Treasury (Ralston 2018) [A]: firms "generally do not bunch" below payroll-tax thresholds (data 2001-02 to 2014-15), with limited exceptions in Victoria and WA.
- I found **no verified bunching studies** for the 15-employee unfair-dismissal threshold, the $75k GST threshold or the $10m small business entity threshold.

## 5. Competition, mark-ups and PMR

**(a) Mechanism.** Mark-ups act as an output tax. Differences in mark-ups across firms misallocate resources. Weak competition also slows adoption of better technology.

**(b) Formulas.**
- `ΔlnMFP_LR = β·ΔETCR` with β = −0.037 to −0.047; the 5-year effect is about one-third of the long run.
- Mark-up channel: `ΔlnTFP ≈ −Δ(misallocation cost)`. Hambur–Freestone imply about **0.2–0.6 pp of TFP per 1% rise in the aggregate mark-up** (derived; non-linear).

**(c) International**
- Edmond, Midrigan & Xu (*JPE* 2023, 131(7); NBER w24800 numbers) [P]:
  - Welfare cost of mark-ups **7.5% of consumption** (benchmark aggregate mark-up 1.15).
  - **18.6%** at a mark-up of 1.25.
  - About ⅔ comes from the aggregate mark-up and ⅓ from misallocation; misallocation TFP loss ≈1.2%.
- Égert–Gal [P]: a typical ETCR reform (−0.31) gives **MFP +0.53%, K/Y +0.07%, employment rate +0.10 pp, and GDP per capita +0.72% at 5 years**.
  - GDP per capita +1.02% at 10 years, **+2.09% in the long run**.
- Bourlès et al. (2013, *REStat*) [A]: anti-competitive upstream regulation curbs downstream MFP growth, more so near the frontier. The often-quoted "1–1.5% a year" is **UNVERIFIED**.
- Aghion et al. (2005) [A]: the competition–innovation relationship is an inverted U (qualitative only).

**(d) Australian**
- Hambur & Freestone (RBA RDP 2025-05) [P], Edmond–Midrigan–Xu (EMX) model calibrated to BLADE:
  - Mark-ups mid-2000s → mid-2010s: harmonic 1.18 → 1.25; cost-weighted 1.25 → 1.33.
  - Value-added misallocation cost rose **1.16–2.52 pp** (harmonic) or **1.54–3.67 pp** (cost-weighted). Headline: productivity would be **1–3% higher** at mid-2000s competition (~$3,000 a person at the top).
  - Including deadweight loss, output would be 32–42% higher and welfare 20–28% higher. The authors flag these as imprecise.
- Hambur (Treasury 2021; *Econ Record* 2023) [A]: mark-ups up **≈5% since the mid-2000s**.
- Australia's PMR score in 2018 was 1.16 vs an OECD average of 1.38 [S]. Check the 2023/24 vintage.

**(e) Caveats.** Mark-ups estimated with the production-function method identify levels poorly. The ETCR covers network sectors only.

## 6. Occupational licensing

**(a) Mechanism.** Licensing restricts labour supply and interstate mobility, and raises prices.

**(b) Formula (derived).** `ΔGDP ≈ Σ_i s_i·Δprod_i × m`, with m ≈ 1 from the PC calibration (0.1% economy-wide labour productivity → 0.10% GDP).

**(c) International**
- Kleiner & Krueger (2013, *JOLE*) [A/S]: 29% of US workers licensed; wage premium ≈18% (14% in working-paper versions).
- Kleiner & Soltas (2023, *REStud*) [A]: welfare loss **12% of occupational surplus**; workers bear 70%, consumers 30%.

**(d) Australian**
- PC (2023 *Advancing Prosperity*, re-run in 2024) [P]: **0.8% productivity rise** in high-licensing industries → **GDP +0.34%** (2023) or **+0.39%** (2024 CGE).
- 24% of Australian workers are in risk-classified licensed occupations [P].
- PC 2014: crossing a state border reduces worker movement by **77%** [P, as cited in PC 2025].
- PC 2009 mutual-recognition modelling: GDP +0.3% under perfect mobility after a resource shock; the national licensing RIS assumed 10% of that [P, as cited].

**(e) Caveat.** Automatic mutual recognition (Queensland does not participate) shrinks remaining gains, and its evaluation is pending.

## 7. Innovation and R&D

**(b) Formulas.**
- `Δln R&D = ε·Δln(user cost of R&D)`, with ε_SR ≈ −0.1 and ε_LR ≈ −1.
- `ΔMFP ≈ ρ_social·Δ(R&D/GDP)`.

**(c) International**
- Bloom, Griffith & Van Reenen (2002, *J Public Econ*) [A]: a 10% fall in R&D cost raises R&D "just over 1%" in the short run and "just under 10%" in the long run.
- Bloom, Schankerman & Van Reenen (2013, *Econometrica*; WP numbers) [P]: social return **55%** vs private **21%**.
- Égert–Gal [P]: business R&D +0.10 pp of GDP → MFP +0.09% at 5 years, GDP per capita **+0.46% long run**.

**(d) Australian**
- Holt, Skali & Thomson (2016) [S, abstract excerpt]: about **$1.90 of extra R&D per $1 of revenue forgone**. The companion Swinburne report recommends a planning range of **0.8–1.9**.
- Thomson (2010) found no significant effect [S].
- 2016 Ferris–Finkel–Fraser review: the R&D Tax Incentive "falls short" on additionality and spillovers [A]. Its quantitative tables are **UNVERIFIED**; the industry.gov.au server was unreachable.

## 8. Trade, tariffs and FDI

**Formulas.** `ΔlnMFP_LR = 0.006–0.008 × Δopenness` (pp of GDP, size-adjusted; Égert–Gal [P]). A +4.01 pp change gives MFP +0.79% at 5 years and GDP per capita +2.40% long run.

**Australian modelling**
- PC 2024 [P]: removing remaining tariffs gives **GDP +0.13–0.25%**.
- PC 2017 *Rising protectionism* [P], all countries raise tariffs by 15 pp:
  - **$0.64 of lost activity per $1 of tariff revenue**.
  - GDP **>1% lower each year**.
  - About 5% of the capital stock mothballed.

**FDI.** Mistura & Roulet (OECD 2019/01) [P]: a **10% cut in the FDI restrictiveness index → +2.1% bilateral FDI stocks**. I found no verified FDI→MFP elasticity.

## 9. Labour-market regulation and non-competes

**Australian modelling and evidence**
- PC 2024, reform L1 [P]:
  - Wages up to **+2.4%** in industries that use non-competes heavily and **+1.4%** in others.
  - **GDP +0.10–0.19%**.
  - One in five workers has a non-compete (ABS 2024).
- Treasury Competition Review (Majeed et al. 2025) [P]: no systematic evidence that workers are compensated for non-competes; non-competes are common in low-productivity firms.
- Treasury also cites an experiment where including a non-compete in a job offer cuts mobility by 30–57%.
- Leigh op-ed, Nov 2025 [A]:
  - Ban from 2027 below the $183,100 high-income threshold, applying to new or varied contracts.
  - Workers with non-competes earn about 4% (~$2,500) less (e61).
- A separate "Treasury 2024 estimate" was not found as distinct from these. **UNVERIFIED.**

**International**
- Johnson, Lavetti & Lipsitz (*JPE* 2025; NBER w31929) [P]:
  - Moving from the 25th to the 75th percentile of enforceability lowers earnings by **1.7%**.
  - A national ban would raise earnings **3.5–13.7%**; this relies on a strong linearity assumption.
- Égert–Gal [P]: a typical EPL reform (−0.30) gives K/Y +0.24%, GDP per capita +0.22% at 5 years and **+1.83% long run**.

## 10. Regulatory delay and uncertainty

**Formula (derived).** A delay of d years raises the effective capital price by about (1+r)^d, so `Δln c ≈ r·d`. Then apply channel 2.

**Australian evidence** (PC 2025, *Investing in cheaper, cleaner energy*, final report) [P]:
- **$20m a year of holding cost on $400m raised**, i.e. r ≈ 5% a year (implied).
- A six-month windfarm delay cost over $25m.
- Environmental (EPBC) approval for a wind project costs about $5m.
- DCCEEW estimate: a **five-month cut in delays saves $3bn a year**.
- Clean-energy approvals can take more than 500 days; NSW windfarm decisions take over 9 years (PC 2025 *Resilient economy*) [P].

**International.** Baker, Bloom & Davis (2016, *QJE*) [P]: an uncertainty shock the size of 2005-06 → 2011-12 "foreshadows" **−6% gross investment, −1.1% industrial production, −0.35% employment**. The authors note this is not necessarily causal.

## 11. Tax efficiency (marginal excess burden, MEB)

Treasury WP 2015-01 (Cao et al.), static CGE model [P]. Welfare cost per $1 of extra revenue:

| Tax | MEB |
|---|---|
| Conveyancing stamp duty | **0.72** |
| Company income tax | **0.50** (sensitivity range 0.20–1.35) |
| Flat labour income tax | **0.21** |
| GST, current base | **0.19** |
| GST, broad base | 0.17 |
| Flat personal income tax | **0.16** |
| Broad land tax | **−0.10** |

KPMG 2010, as reported in Treasury's tables [P]:

| Tax | KPMG 2010 | KPMG 2011 |
|---|---|---|
| Company tax | 0.40 | 0.37 |
| Stamp duty | 0.34 | 0.80 |
| GST | 0.08 | 0.12 |
| Labour income tax | 0.24 | 0.24 |

Caveats:
- The Centre of Policy Studies (Nassios et al. 2019) finds a *negative* company-tax MEB [P, cited by PC 2025].
- PC 2025 says a 20% company rate would bring its MEB to around the GST's.
- **Funding a subsidy (derived):** `net cost = S·(1 + MEB_funding tax) − benefits`.

## 12. Other channels (brief)

- **Agglomeration.** Donovan et al. (Tinbergen DP 2021-026) [P]: elasticity of productivity to city size or density **2.7–6.4%** (6,684 estimates).
- **Public capital.** Bom & Ligthart (2014) [A]: output elasticity **0.083 short run, 0.122 long run**.
- **Human capital.** Égert's 2018 update has a coefficient of 2.359 on a PIAAC/PISA index. **Units unclear; UNVERIFIED for calculator use.**

---

## Parameter table

| Channel | Parameter | Value | Units | Source | Country | Confidence |
|---|---|---|---|---|---|---|
| 0 | GDP response to economy-wide LP shock | 0.1→0.10 | % GDP per % LP | PC 2024 | AU | High [P] |
| 0 | NCP package | 1.0–1.7 | % GDP | PC 2024 | AU | High [P] |
| 0 | Hilmer reforms, ex post | 2.5 | % GDP | PC 2005 via PC 2024 | AU | High [P] |
| 1 | Cth compliance + delay cost | 115–160 | $bn/yr | PC 2025 | AU | High [P] (scaled estimate) |
| 1 | Housing regulation cost | 28.6 (~1%) | $bn/yr (% GDP) | PC 2025 | AU | High [P] |
| 1 | Total rules cost | 250 | $bn/yr | Deloitte 2014 | AU | Low [S] |
| 1 | Red tape cost | 176 (11%) | $bn (% GDP) | IPA | AU | UNVERIFIED |
| 1 | 25% admin-burden cut | +1.4 | % GDP | EC 2007/2012 | EU | Medium [S] |
| 2 | Capital income share | 41 | % factor income | Treasury 2017/ABS | AU | High [P] |
| 2 | Company tax 30%→25% | GDP +1.2, I +2.8 | % long-run level | Treasury WP 2016-02 | AU | High [P] (model) |
| 2 | PC hybrid company tax package | I +2.2, GDP +0.4–0.7, LP +0.4–0.5 | % | PC 2025 | AU | High [P] (model) |
| 2 | User-cost elasticity | −0.25 | elasticity | Chirinko et al. 1999 | US | Medium [A] |
| 2 | User-cost elasticity range | −0.5 to −1 | elasticity | Hassett–Hubbard via ZM | US | Medium |
| 2 | Capital–labour substitution | 0.40 (micro); 0.9 (Treasury model) | σ | CFM 2011; Treasury 2016 | US; AU | Medium/High |
| 2 | Bonus depreciation | +10.4 / +16.9 | % investment | Zwick–Mahon 2017 | US | High [P] |
| 3 | Entry cost | 2.25 | % GDP per capita | Djankov 2002 | AU | High [P] |
| 3 | Entry × convergence | 0.009 | per pp entry rate | Andrews et al. 2022 | AU | High [P] |
| 3 | Reallocation drag | 0.15 | pp LP growth/yr | Andrews–Hansell | AU | High [P] |
| 3 | Zombie capital reduction | 0.6 (0.1–1.4) | % MFP | Adalet McGowan et al. | OECD | High [P] |
| 3 | Net entry share of MFP growth | 25–26 | % | FHK 2001 | US | High [P] |
| 4 | 50-employee rules | 1.3–3.4 | % GDP | GLVR 2016 | FR | Medium [A] |
| 4 | 50-employee rules | <0.3 | % output/worker | Gourio–Roys 2014 | FR | Medium [A] |
| 4 | SA payroll threshold bunching | +21 / −18; −3.3 payroll | % | e61 2024 | AU | High [P] |
| 5 | ETCR→MFP (long run) | −0.037 to −0.047 | log points per index point | Égert–Gal 2016 | OECD | High [P] (weak with year FE) |
| 5 | Typical ETCR reform (−0.31) | +0.72 (5y), +2.09 (LR) | % GDP per capita | Égert–Gal | OECD | High [P] |
| 5 | Mark-up rise cost | 1–3 | % productivity | Hambur–Freestone 2025 | AU | High [P] |
| 5 | Welfare cost of mark-ups | 7.5 (18.6 high case) | % consumption | EMX | US | High [P] (WP version) |
| 5 | Mark-up increase since mid-2000s | ~5 | % | Hambur 2021/23 | AU | Medium [A] |
| 6 | Licensing reform | 0.8 → +0.34–0.39 | % productivity → % GDP | PC 2023/2024 | AU | High [P] |
| 6 | Licensing welfare loss | 12 | % occupational surplus | Kleiner–Soltas 2023 | US | Medium [A] |
| 6 | Interstate border effect on mobility | −77 | % | PC 2014 via PC 2025 | AU | High [P] |
| 7 | R&D tax-price elasticity | −0.1 SR / ≈−1 LR | elasticity | BGVR 2002 | OECD | Medium [A] |
| 7 | R&D additionality | 0.8–1.9 | $ R&D per $ revenue forgone | Holt/Skali/Thomson 2016 | AU | Low–Medium [S] |
| 7 | Social vs private return | 55 vs 21 | % | BSV 2013 | US | High [P] (WP version) |
| 8 | Openness→MFP | 0.006–0.008 | per pp openness | Égert–Gal | OECD | High [P] |
| 8 | Remove tariffs | +0.13–0.25 | % GDP | PC 2024 | AU | High [P] |
| 8 | Global +15pp tariffs | −0.64 per $1; >1% | $ activity per $ revenue; % GDP | PC 2017 | AU | High [P] |
| 8 | FDI restrictiveness −10% | +2.1 | % FDI stocks | Mistura–Roulet 2019 | 60 countries | High [P] |
| 9 | Non-compete reform | +0.10–0.19 | % GDP | PC 2024 | AU | High [P] |
| 9 | National non-compete ban | +3.5–13.7 | % earnings | JLL | US | High [P] (extrapolated) |
| 9 | EPL reform (−0.30) | +1.83 LR | % GDP per capita | Égert–Gal | OECD | High [P] |
| 10 | Delay holding cost | ~5 | %/yr of capital | PC 2025 net zero (QREC) | AU | Medium [P] (anecdote) |
| 10 | Uncertainty shock | −6 | % gross investment | BBD 2016 | US | Medium [P] (non-causal) |
| 11 | MEB: stamp duty / company / labour / GST / PIT / land | 0.72 / 0.50 / 0.21 / 0.19 / 0.16 / −0.10 | $ per $ revenue | Treasury WP 2015-01 | AU | High [P] |
| 12 | Agglomeration elasticity | 2.7–6.4 | % | Donovan et al. | Global | High [P] |
| 12 | Public capital output elasticity | 0.083 / 0.122 | elasticity | Bom–Ligthart 2014 | OECD | Medium [A] |

## Sources
- PC 2025, *Creating a more dynamic and resilient economy*: https://assets.pc.gov.au/2025-12/resilient-economy.pdf
- PC 2025, *Investing in cheaper, cleaner energy* (net zero): https://assets.pc.gov.au/2025-12/net-zero.pdf
- PC 2024, *National Competition Policy: modelling proposed reforms*: https://assets.pc.gov.au/inquiries/completed/competition-analysis/report/competition-analysis.pdf
- PC 2025, *National Competition Policy analysis*: https://assets.pc.gov.au/2025-11/competition-analysis-2025.pdf
- PC 2017, *Rising protectionism*: https://assets.pc.gov.au/research/completed/rising-protectionism/rising-protectionism.pdf
- PC 2017, *Shifting the Dial*: https://assets.pc.gov.au/inquiries/completed/productivity-review/report/productivity-review.pdf
- Treasury WP 2015-01 (Cao et al.): https://treasury.gov.au/sites/default/files/2019-03/TWP2015-01.pdf
- Treasury WP 2016-02 (Kouparitsas, Prihardini & Beames): https://treasury.gov.au/sites/default/files/2019-03/Treasury-Working-Paper-2016-02.pdf
- Treasury 2016-17 Budget economy-wide modelling note: https://treasury.gov.au/sites/default/files/2019-03/160503_Economy-wide-modelling.pdf
- Campbell & Withers 2017, Treasury Economic Roundup: https://treasury.gov.au/sites/default/files/2019-03/p2017-t213722-Roundup_Productivity_trends_and_structural_change.pdf
- Andrews & Hansell, Treasury WP 2019-06: https://treasury.gov.au/sites/default/files/2019-11/p2019-37418-productivity_0.pdf
- Andrews, Hambur, Hansell & Wheeler, Treasury WP 2022-01: https://treasury.gov.au/sites/default/files/2022-02/p2022-243535.pdf
- Hambur 2021, Treasury: https://treasury.gov.au/publication/p2021-177591
- Hambur & Freestone, RBA RDP 2025-05: https://www.rba.gov.au/publications/rdp/2025/pdf/rdp2025-05.pdf
- Treasury Competition Review 2025, non-competes: https://treasury.gov.au/sites/default/files/2025-11/p2025-717176cr.pdf
- Leigh op-ed, Nov 2025: https://ministers.treasury.gov.au/ministers/andrew-leigh-2025/articles/opinion-piece-setting-australian-talent-free
- e61 Micro Note 23 (SA payroll tax): https://e61.in/wp-content/uploads/2024/08/A_Counterproductive_Tax_Cut_.pdf
- Treasury 2018, payroll tax and firm behaviour: https://treasury.gov.au/publication/p2018-t280988
- Égert & Gal, OECD WP 1354: https://www.oecd.org/content/dam/oecd/en/publications/reports/2017/02/the-quantification-of-structural-reforms-in-oecd-countries_b5d58c7d/2d887027-en.pdf
- Égert 2023, OECD PMR slides: https://www.oecd.org/content/dam/oecd/en/events/2023/3/Session%201_Egert_FINAL.pdf
- Edmond, Midrigan & Xu, NBER w24800: https://www.nber.org/papers/w24800
- Djankov et al. 2002: https://web.stanford.edu/~klenow/Regulation%20of%20Entry.pdf
- Klapper, Laeven & Rajan, NBER w10380: https://www.nber.org/system/files/working_papers/w10380/w10380.pdf
- Foster, Haltiwanger & Krizan 2001: https://www.nber.org/system/files/chapters/c10129/c10129.pdf
- Adalet McGowan, Andrews & Millot (zombie firms): https://www.economic-policy.org/wp-content/uploads/2018/05/995_Walking-Dead.pdf
- Garicano, Lelarge & Van Reenen 2016: https://researchonline.lse.ac.uk/id/eprint/66765/
- Gourio & Roys 2014: https://econometricsociety.org/publications/quantitative-economics/2014/07/01/Size-Dependent-Regulations-Firm-Size-Distribution-and-Reallocation
- Kleiner & Soltas: https://www.minneapolisfed.org/research/staff-reports/a-welfare-analysis-of-occupational-licensing-in-us-states
- Kleiner & Krueger: https://www.nber.org/papers/w14979
- Johnson, Lavetti & Lipsitz, NBER w31929: https://www.nber.org/system/files/working_papers/w31929/w31929.pdf
- Bloom, Griffith & Van Reenen 2002: https://researchonline.lse.ac.uk/id/eprint/1353
- Bloom, Schankerman & Van Reenen: https://funginstitute.berkeley.edu/wp-content/uploads/2013/12/Paper_2012_ucb.pdf
- Swinburne R&D additionality report: https://www.swinburne.edu.au/media/swinburneeduau/research/research-centres/cti/reports/The-Additionality-of-R&D-Tax-Policy-in-Australia.pdf
- Zwick & Mahon, NBER w21876: https://www.nber.org/papers/w21876
- Chirinko, Fazzari & Meyer 2011: https://ideas.repec.org/a/taf/jnlbes/v29y2011i4p587-594.html
- Chirinko, Fazzari & Meyer 1999: DOI 10.1016/S0047-2727(99)00024-9
- Mistura & Roulet 2019: http://dx.doi.org/10.1787/641507ce-en
- Baker, Bloom & Davis 2016: https://users.ssc.wisc.edu/~mchinn/bakerbloomdavis_QJE2016.pdf
- Donovan et al.: https://papers.tinbergen.nl/21026.pdf
- Bom & Ligthart 2014: https://ideas.repec.org/a/bla/jecsur/v28y2014i5p889-916.html
- Bouis, Duval & Eugster 2016 (IMF): https://www.imf.org/en/Publications/WP/Issues/2016/12/31/Product-Market-Deregulation-and-Growth-New-Country-Industry-Level-Evidence-43951
- Bourlès et al.: https://www.nber.org/papers/w16520
- Aghion et al.: https://discovery.ucl.ac.uk/id/eprint/2572/
- Deloitte 2014 press coverage: https://www.quarrymagazine.com/2014/07/11/report-finds-compliance-burdens-business/ and https://www.consultancy.uk/news/973/deloitte-compliance-costs-australian-economy-250-billion
- IPA paper (could not open): https://apo.org.au/sites/default/files/resource-files/2017-05/apo-nid76267.pdf
- European Commission, COM(2006)691: https://www.eumonitor.nl/9353000/1/j4nvke1fm2yd1u0_j9vvik7m1c3gyxp/vkcweehseevh/v=s7z/f=/com(2006)691_en.pdf
- Bakhtiari 2019: https://ideas.repec.org/a/bla/ecorec/v95y2019i308p114-140.html

**What I could not check against a primary source:**
- **Deloitte 2014 PDF:** the report itself would not download, so its figures come from 2014 press coverage only.
- **IPA $176bn method:** I found the figure quoted but could not open the IPA paper to see how it was calculated.
- **2016 R&D Tax Incentive review tables:** the industry.gov.au server was unreachable.
- **Branstetter et al. Portugal magnitudes:** I could not retrieve the paper's figures.
- **Bourlès "1–1.5% a year":** the abstract gives no number, so this figure remains unverified.
- **2023/24 PMR score for Australia:** I found only the 2018 value (1.16), from secondary coverage.

The downloaded source texts are in a temporary session folder (not committed).
