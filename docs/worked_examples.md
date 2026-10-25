# Worked examples: five real policies costed end to end

Plan P6, §8. Each example is a policy brief in `regulatory-burden-tool/examples/`. `npm run make:examples` writes the briefs from the published figures, with each value's page in the brief's provenance. `npm run worked:examples` costs them and writes the results section below. Test T-WEX-01 freezes the outputs and T-WEX-02 checks what each source says the result should show. Sources and hashes are in `regulatory-burden-tool/data/SOURCES.md`.

Results are the tool's: unofficial and indicative. Every GDP figure is a change in the level of real GDP, with Layer B's closure (fixed employment, no terms-of-trade effects).

## 1. Banning non-compete clauses (2025-26 Budget)

**Policy and source.** The 2025-26 Budget measure: ban non-compete clauses for employees earning below the Fair Work Act's high-income threshold. It is Option 2 of Treasury's Impact Analysis (OIA, 21 September 2026), which applies prospectively from 2027. This is also the bundled costing example.

**Inputs:**
- **Scope:** all 19 divisions at full exposure. C8 leaves agriculture out, as the PC's simulation does.
- **Burden:** the IA's Options 2 and 3, each a one-off familiarisation cost. They are rebuilt from Table 6 (the share of businesses using non-competes, by size) and Table 5 (who reads the reforms, for 90 or 30 minutes, at Glassdoor rates). The rates are multiplied by the RBM's 1.75 on-cost multiplier, which the IA's small-business figure implies. The IA's 73,403 medium and large businesses are split by CABEE.
- **Lever:** coverage change −0.2 to −0.18. Treasury expects Option 2 to deliver at least 90% of a full ban's mobility gain (p. 41).
- **Timing:** a phase-in of 7 years, the midpoint of the IA's 5–10 years for contracts to turn over (p. 50).

**How the tool costs it.** C8 rebuilds the PC's L1 chain: 10% of the US wage effect becomes labour productivity. C1 costs the familiarisation burden.

**Against the source:**
- **GDP:** the central estimate is close to Treasury's $5.1 billion, because both are the PC's chain. That $5.1 billion is the top of the PC's pass-through range (10%; 5% in its lower case), so the central value sits above the 90th percentile and the median is lower. The Government's "$5 billion" is the upper case.
- **RBE:** Option 3 reproduces Treasury's $16.3 million. Option 2 comes to $48.9 million against Treasury's $46.4 million. Treasury's medium- and large-business figures for Option 2 ($7.5m, $0.7m) are not three times its Option 3 figures ($3.3m, $0.3m), although Option 2's time is three times as long. The stated inputs give three times.

**Limitations:**
- The tool does not separate Option 2 from a full ban except through the 90% bound.
- High-income employees keep non-competes for up to 6 months; the coverage of high earners is not published.

## 2. Automatic mutual recognition of occupational registrations (2021)

**Policy and source.** A worker registered in one state or territory may work in another without registering again (Mutual Recognition Act 1992, Part 3A, from 1 July 2021).

**Inputs:**
- The PC's estimate (2015, p. 171, citing NOLA 2014) of the annual cost of holding a licence in a second jurisdiction: $2.7m for electrical, $1.4m for plumbing and gasfitting, $2.3m for property occupations.
- The licensing lever, with mutual recognition ticked and no change in stringency.

**How the tool costs it.** It costs nothing:
- **Fees:** the second registrations' fees are paid to government, so they are outside the RBE (RBM pp. 2, 4). They are also a transfer, not a resource cost. The source does not estimate the time spent applying.
- **Mobility:** the C8 elasticity comes from the PC's licensing simulation, which leaves mutual recognition out of scope (PC 2024, p. 128). No evidence entry gives its effect on mobility or productivity (A-P35). The tool records mutual recognition and says so.

**Against the source.** The Government's estimate of "$2.4 billion over ten years" is reported in secondary sources, among them the OECD's *Competition and Regulation in Professions and Occupations* (2024, p. 34). Its method, the 2020 Decision RIS, could not be retrieved: the PM&C page now redirects, and archived copies are blocked. The tool cannot check it. A user with a sourced estimate enters it as a custom shock, graded D unless the source is graded.

**Limitation.** This is a gap, not a result. The PC recommended an evaluation of the scheme, which is the evidence C8 would need.

## 3. Mandatory climate-related financial disclosure (2024)

**Policy and source.** Large entities report climate-related risks, phased in by size:
- Group 1 from 2024-25;
- Group 2 from 2026-27;
- Group 3 from 2027-28.

The source is Treasury's Policy Impact Analysis (September 2023).

**Inputs:**
- **Burden:** Treasury's per-entity costs (Tables 7, 10 and 13) and counts (pp. 20, 26), with its discounts (Group 2's transition cost by 20%, NGER reporters' costs by 30%). The status quo of voluntary TCFD reporting is Table 3's $249.99m a year. Options 1, 1a and 1b are all entered; 1b, the recommended option, is first.
- **Thresholds:** the three groups' employee tests (500, 250, 100), with the ongoing cost per entity above each.

**How the tool costs it.** C1 turns the RBE into a fall in multifactor productivity in proportion to value added. The populations have no industry, so the cost is spread over the divisions by value added. The C5 screen counts the businesses near each threshold.

**Against the source:**
- **RBE:** the burden proposal reproduces Treasury's Table 14 to $0.1 million for all three options ($1,150.2m, $1,386.7m, $1,207.3m).
- **GDP:** the cost is about twice the RBE. Layer B lets capital fall with the productivity loss (1/(1 − α)), and the multiplier on an economy-wide MFP shock is 1.91, against 1.60 in the PC's runs ([validation](costing_validation.md), B7tar). So the GDP figure may be about 19% too large.
- **Benefits:** Treasury does not quantify them (a lower cost of capital, better pricing of climate risk), and the tool counts none (s = 0, A-P31).

**Limitations:**
- Each group's test is two of three (revenue, assets, employees); the screen uses the employee test only.
- The ABS size bands put 250 and 500 employees in the same band (200+).
- Group 3's 228 entities follow Table 12; the text says 278.

## 4. EPBC Act reform: the Streamlined Assessment Pathway (2025)

**Policy and source.** The Environment Protection Reform Bill 2025 shortens the statutory assessment and approval period for controlled actions by at least 20 days. DCCEEW's addendum (24 September 2025) gives three scenarios: 20 days (low), 141 days (medium) and 288 days (high), the last two if other reforms cut requests for more information.

**Inputs:**
- **Lever:** the investment approval delay changes by −20 days (−0.6575 months). The 141- and 288-day runs are variants.
- **Exposure:** the share of investment that passes through the assessment pathways, the same in every market-sector division (A–N, R, S). It is DCCEEW's implied value of the projects assessed each year, its business saving ÷ (7% × 20/365) = $115 billion, over market-sector gross fixed capital formation in 2025-26 (ASNA).

**How the tool costs it.** C2: a delay of d years raises the user cost of the investment it applies to by about r·d. Capital responds with σ = 0.4, and value added rises by α·Δln K.

**Against the source:**
- **Long run:** the tool's effect is close to DCCEEW's reduction in delay costs in all three scenarios. That is expected: the exposure is built from DCCEEW's implied project value, so the comparison checks consistency, not independence. The tool's effect is proportional to the days saved. DCCEEW's is not quite: its medium and high scenarios are 6.8 and 15.5 times its low one, against 7.05 and 14.4 times the days, because they compare with different pathways' median timeframes.
- **Timing:** the two differ in time. DCCEEW's saving accrues at once, while the tool's effect comes through capital deepening at Égert and Gal's capital-output speed (2.4% a year). Only about a fifth of the long-run effect arrives within ten years, so the tool's present value is much smaller than ten years of DCCEEW's saving.

**Limitations:**
- DCCEEW's implied project value is 27% of market-sector investment. If it is a project's total capital spending rather than a year's, the exposure is overstated.
- The commencement date is assumed to be 2026-27.
- The sectors' values are not published, so the exposure is uniform across industries.

## 5. Victoria's payroll tax-free threshold: $700,000 to $1 million (2023-24 Budget)

**Policy and source.** The tax-free threshold rose to $900,000 on 1 July 2024 and to $1 million on 1 July 2025. It is phased out for wages above $3 million (by $1 for every $2) and is nil above $5 million. The rate is 4.85%. The sources are Victorian Budget 2023-24, BP3 p. 114 and Table 1.27, and BP5 chapter 4.

**Inputs:**
- **Thresholds:** two, both on payroll. The move from $700,000 to $1 million costs a business above the threshold $0 to $14,550 a year (4.85% of the first $300,000 above it). The phase-out from $3 million costs up to $48,500 a year at $5 million.
- **Exposure:** each division's exposure is Victoria's share of its employing businesses (CABEE by state, June 2025).

**How the tool costs it:**
- **C5:** the screen counts businesses and employment near each threshold, converting payroll to employees with wages per person employed (A-P34). It has no GDP effect in v1 (A-P05).
- **No fiscal lever:** the Budget's net revenue effect (−$38.7 million in 2026-27) combines a lower average rate for small employers with a higher marginal rate between $3 million and $5 million. It is not a change in the marginal rate of one tax, so C11's marginal excess burden would misstate its efficiency effect. Entered as revenue given up through labour income tax (MEB 0.21), C11 would show a gain of about $8 million a year, an upper bound that ignores the phase-out.

**Against the source.** The Budget counts 6,000 businesses that stop paying and more than 26,000 that benefit. The screen's counts are larger because the ABS bands (5–19, 20–199) are much wider than ±10% of the threshold.

**Limitations:**
- Finance and insurance (K) is not screened: Australian Industry has no wages for it.
- Payroll tax is assessed on grouped, Australia-wide wages; the screen uses businesses, not groups.

## Results

<!-- worked-results:start -->
Generated by `npm run worked:examples`. Parameters: vintage 2026-10-23, sources fingerprint 97e8dcdd61a44d9f; 2,000 Monte Carlo draws, seed 1. Long-run change in the level of real GDP; dollars a year in 2025-26 prices.

| Example | Gate | GDP, central | 10–90% range | $ a year | PV at 7% (10 years) | RBE a year (first option) | Published |
|---|---|---:|---|---:|---:|---:|---|
| Banning non-compete clauses for low- and middle-income workers (2025-26 Budget) | indicative | +0.178% | +0.104% to +0.166% | +$5,242m | +$6,569m | +$5m | GDP +$5.1 billion a year (the PC's 2024 modelling, cited in the IA); one-off familiarisation cost $46.4 million (Option 2) and $16.3 million (Option 3) |
| Automatic mutual recognition of occupational registrations (2021) | indicative | 0 | 0 to 0 | $0m | $0m | $0m | "$2.4 billion over ten years" (Australian Government, as reported; method not retrieved); multiple licences cost $6.4 million a year (PC 2015) |
| Mandatory climate-related financial disclosure (2024) | full | −0.083% | −0.088% to −0.061% | −$2,431m | −$7,903m | +$1,150m | RBE +$1,150.2 million a year (Option 1b; Option 1 $1,386.7m, Option 1a $1,207.3m); benefits not quantified |
| EPBC Act reform: the Streamlined Assessment Pathway (2025) | full | +0.016% | +0.0084% to +0.019% | +$456m | +$356m | – | Delay costs −$445 million a year at 20 days (−$3,045m at 141 days, −$6,914m at 288 days) |
| EPBC Act reform: the Streamlined Assessment Pathway (2025): 141 days (DCCEEW's medium scenario) | full | +0.109% | +0.059% to +0.137% | +$3,214m | +$2,509m | – |  |
| EPBC Act reform: the Streamlined Assessment Pathway (2025): 288 days (DCCEEW's high scenario) | full | +0.223% | +0.121% to +0.281% | +$6,565m | +$5,124m | – |  |
| Victoria's payroll tax-free threshold: $700,000 to $1 million (2023-24 Budget) | indicative | 0 | 0 to 0 | $0m | $0m | – | Revenue +$20.3m (2024-25), −$43.6m (2025-26), −$38.7m (2026-27), net of the phase-out; about 6,000 businesses stop paying, 26,000 benefit |

**By channel** (long-run GDP, per cent; grade):

- Banning non-compete clauses for low- and middle-income workers (2025-26 Budget): C1 −0.00035% (A); C8 +0.179% (C).
- Automatic mutual recognition of occupational registrations (2021): C1 not quantified; C8 0 (C).
- Mandatory climate-related financial disclosure (2024): C1 −0.083% (A); C5 0 (B).
- EPBC Act reform: the Streamlined Assessment Pathway (2025): C2 +0.016% (B).
- Victoria's payroll tax-free threshold: $700,000 to $1 million (2023-24 Budget): C5 0 (B).

**RBE by option** (average a year over ten years):

- Banning non-compete clauses for low- and middle-income workers (2025-26 Budget): option-2-partial-ban +$5m; option-3-full-ban +$2m.
- Automatic mutual recognition of occupational registrations (2021): amr $0m.
- Mandatory climate-related financial disclosure (2024): option-1b +$1,150m; option-1 +$1,387m; option-1a +$1,207m.

**C5 screens:**

- Mandatory climate-related financial disclosure (2024):
  - Threshold "group-1" at 500 employees: businesses in the size bands that overlap 450–550 employees (200+; CABEE 2024-25): 5,324 businesses
  - Threshold "group-1" at 500 employees: employment in those bands (Australian Industry 2024-25): 4,781.1 thousand persons
  - Threshold "group-1": cost a year above the threshold as a share of an average wage bill in the 200+ band, against the French rules' 2.3% labour-tax equivalent: 0.84 % of wages
  - Threshold "group-2" at 250 employees: businesses in the size bands that overlap 225–275 employees (200+; CABEE 2024-25): 5,324 businesses
  - Threshold "group-2" at 250 employees: employment in those bands (Australian Industry 2024-25): 4,781.1 thousand persons
  - Threshold "group-2": cost a year above the threshold as a share of an average wage bill in the 200+ band, against the French rules' 2.3% labour-tax equivalent: 0.84 % of wages
  - Threshold "group-3" at 100 employees: businesses in the size bands that overlap 90–110 employees (20-199; CABEE 2024-25): 67,876 businesses
  - Threshold "group-3" at 100 employees: employment in those bands (Australian Industry 2024-25): 3,424.5 thousand persons
  - Threshold "group-3": cost a year above the threshold as a share of an average wage bill in the 20-199 band, against the French rules' 2.3% labour-tax equivalent: 0.93 % of wages
- Victoria's payroll tax-free threshold: $700,000 to $1 million (2023-24 Budget):
  - Threshold "tax-free-threshold" at $1,000,000 of payroll: businesses in the size bands that overlap ±10% of its employee equivalent (5-19, 20-199; CABEE 2024-25): 44,207.6 businesses
  - Threshold "tax-free-threshold" at $1,000,000 of payroll: employment in those bands (Australian Industry 2024-25): 584.68 thousand persons
  - Threshold "tax-free-threshold": cost a year above the threshold as a share of an average wage bill in the 5-19 or 20-199 band, against the French rules' 2.3% labour-tax equivalent: 0.87 % of wages
  - Threshold "tax-free-threshold" at $700,000 of payroll: businesses in the size bands that overlap ±10% of its employee equivalent (0-4, 5-19, 20-199; CABEE 2024-25): 59,718.4 businesses
  - Threshold "tax-free-threshold" at $700,000 of payroll: employment in those bands (Australian Industry 2024-25): 651.23 thousand persons
  - Threshold "tax-free-threshold": cost a year above the threshold as a share of an average wage bill in the 0-4 or 5-19 or 20-199 band, against the French rules' 2.3% labour-tax equivalent: 1.04 % of wages
  - Threshold "threshold-phase-out" at $3,000,000 of payroll: businesses in the size bands that overlap ±10% of its employee equivalent (5-19, 20-199; CABEE 2024-25): 17,100.5 businesses
  - Threshold "threshold-phase-out" at $3,000,000 of payroll: employment in those bands (Australian Industry 2024-25): 873.78 thousand persons
  - Threshold "threshold-phase-out": cost a year above the threshold as a share of an average wage bill in the 5-19 or 20-199 band, against the French rules' 2.3% labour-tax equivalent: 0.63 % of wages
<!-- worked-results:end -->
