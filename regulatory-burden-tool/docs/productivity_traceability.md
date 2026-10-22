# Productivity and competition costing: traceability

**Status:** P0 of [`docs/forward_plan_policy_costing.md`](../../docs/forward_plan_policy_costing.md) (22 October 2026).

What P0 covers:
- The input contract (the policy brief) is implemented and tested.
- The formulas are specified with their sources; they will be implemented in P4. Rows marked **P4** or **P5** have no code yet.

Column key:
- **Code** points to `src/productivity/` (or `src/engine/` for the RBM rules this module relies on).
- **Test** gives test IDs, which appear in the test titles under `tests/productivity/`, `tests/engine/` and `e2e/`.
- `npm run trace` checks this document as it does `framework_traceability.md`: every cited test ID and code reference must exist.

Companion documents: [`framework_traceability.md`](framework_traceability.md) (the RBM rules, unchanged) and the research notes in [`docs/research/policy_costing/`](../../docs/research/policy_costing/).

## 1. Source documents

| Short name | Document | Version and identity |
|---|---|---|
| **RBM** | OIA, *Regulatory Burden Measurement Framework* | July 2026; SHA-256 `646848f9…0c74ac8` (see `data/SOURCES.md`) |
| **IAF-PG** | OIA, *Australian Government Impact Analysis Framework: Practical Guide for Agencies* | 1 July 2026; SHA-256 `7b3f3801…dddef67e` |
| **OIA-COMP** | OIA, *Supplementary guidance: How to consider competition in impact analysis* | July 2026, 13 pp.; SHA-256 `8408469f…5888678` |
| **OIA-CBA** | OIA, *Cost Benefit Analysis* guidance note | 2023, listed as under review |
| **PC2024** | Productivity Commission, *National Competition Policy: modelling proposed reforms*, and the PC National results workbook | Released 29 Nov 2024; workbook SHA-256 `0a0e3058…f8d94e6`; CC BY 4.0 (PC copyright statement, checked 22 Oct 2026) |
| **PC2025-RE** | Productivity Commission, *Creating a more dynamic and resilient economy* (Inquiry Report 109) | Released 19 Dec 2025 |
| **PC2025-NZ** | Productivity Commission, *Investing in cheaper, cleaner energy and the net zero transformation* | Dec 2025 |
| **EG2016** | Égert & Gal, *The quantification of structural reforms in OECD countries*, OECD Economics Department WP 1354 | 2016 |
| **AHHW2022** | Andrews, Hambur, Hansell & Wheeler, *Reaching for the stars*, Treasury WP 2022-01 | 2022 |
| **KLR** | Klapper, Laeven & Rajan, *Entry regulation as a barrier to entrepreneurship*, NBER w10380 (JFE 2006) | 2004 version read |
| **DJ2002** | Djankov, La Porta, Lopez-de-Silanes & Shleifer, *The regulation of entry*, QJE | 2002 |
| **GLVR2016** | Garicano, Lelarge & Van Reenen, AER 106(11) | 2016 |
| **GR2014** | Gourio & Roys, Quantitative Economics | 2014 |
| **E61-2024** | e61 Institute, Micro Note 23 (SA payroll tax threshold) | Aug 2024 |
| **HF2025** | Hambur & Freestone, *How costly are mark-ups in Australia?*, RBA RDP 2025-05, and supplementary data | Aug 2025 |
| **CFM2011** | Chirinko, Fazzari & Meyer, JBES 29(4) | 2011 |
| **KPB2016** | Kouparitsas, Prihardini & Beames, Treasury WP 2016-02 | 2016 |
| **BGVR2002** | Bloom, Griffith & Van Reenen, J Public Econ | 2002 |
| **JLL** | Johnson, Lavetti & Lipsitz, NBER w31929 | 2023 working paper |
| **MR2019** | Mistura & Roulet, OECD Working Papers on International Investment 2019/01 | 2019 |
| **CAO2015** | Cao et al., Treasury WP 2015-01 | 2015 |
| **ABS-MFP** | ABS, *Estimates of Industry Multifactor Productivity* (5260.0.55.002) | 2024-25, released 6 Feb 2026 |
| **ABS-IO** | ABS, *Australian National Accounts: Input-Output Tables* (5209.0.55.001) | 2023-24, released 25 Mar 2026 |
| **ABS-OSCA** | ABS, *OSCA 2024 Version 1.0*, Category descriptions (Table 1: 1,156 occupations, six-digit identifiers, "Registration or Licensing" column) | Checked 22 Oct 2026 |
| **ABS-ANZSIC** | ABS codelist `CL_ANZSIC_2006` 1.1.0 (bundled in `alicia/src/alicia/data/anzsic2006.json`) | Retrieved 14 Oct 2026 |

**Evidence grades** (plan §6.2):
- **A:** Australian causal or structural estimate.
- **B:** international causal estimate.
- **C:** cross-country correlation, or a model result used as a rule of thumb.
- **D:** the tool's assumption, or a user entry.

**Verification tags:**
- **[P]:** read in the primary source.
- **[A]:** read in the abstract or official summary.
- **[S]:** from secondary coverage only, and never a default.

## 2. Rules and formulas

### 2.1 Separation from the RBE, and the OIA framework

| ID | Rule | Source | Code | Test |
|---|---|---|---|---|
| PR-01 | The productivity engine never changes the RBE: it reads frozen copies of the proposal and results | RBM p. 4; DECISIONS #44, #81 | `src/engine/extensions.ts#runExtensions` | T-EXT-01, T-BRF-12 |
| PR-02 | Competition and other indirect impacts are excluded from the RBE ("Indirect costs … including changes to market structure and competition impacts") and reported separately | RBM p. 4 | `src/engine/scope.ts#EXCLUSIONS` | T-SCOPE-01 |
| PR-03 | IA threshold 2: "indicative impacts of $200 million or more a year on economic and social outcomes", undiscounted in the preliminary test. Results compare the central and low annual GDP effect with $200m | IAF-PG p. 8 | P4 | P4 |
| PR-04 | IA threshold 3: a cohort, including small businesses, disproportionately and significantly affected. Reported as cost-to-revenue by size cohort and the small-to-large cost ratio | IAF-PG p. 9 | P5 | P5 |
| PR-05 | Economy-wide effects are presented "only if they are material and supported by robust evidence" (the evidence gate, plan §6.6) | OIA-COMP | P4 | P4 |
| PR-06 | Productivity NPVs at a 7% real discount rate, with 3% and 10% sensitivity. The RBE stays undiscounted (RBM p. 6) | OIA-CBA | `src/productivity/brief.ts#AnalysisSchema` (defaults); NPV in P4 | T-BRF-01; P4 |
| PR-07 | The competition screen follows the three competition tests: (1) does it impact competition, (2) less restrictive alternatives, (3) net benefit | OIA-COMP (the three steps) | P5 | P5 |
| PR-08 | Step 1 uses the five OIA categories, which are the register's channels (`barriers`, `number-or-type`, `ability-incentive`, `prices-market-share`, `consumer-choice`) | OIA-COMP, Step 1; `alicia/src/alicia/register/schema.py` | P5 | P5 |
| PR-09 | A 10-year default duration; a longer one needs a recorded justification | RBM p. 6 | `src/productivity/brief.ts#BriefMetaSchema` | T-BRF-11 |

### 2.2 The policy brief (implemented in P0)

| ID | Rule | Source | Code | Test |
|---|---|---|---|---|
| BR-01 | Every lever is a signed change from the baseline; a range's midpoint is its central value | Plan §5.1; RBM convention A-07 | `src/productivity/brief.ts#SignedQuantitySchema`, `src/productivity/brief.ts#central` | T-BRF-03 |
| BR-02 | Strict objects: unknown keys are rejected, so nothing unplanned reaches the engine | DECISIONS #34 (same rule as the RBM schema) | `src/productivity/brief.ts#PolicyBriefSchema` | T-BRF-02 |
| BR-03 | Scope industries are listed once, and no code may sit inside another (it would be counted twice) | Plan §6.5 | `src/productivity/anzsic.ts#overlaps` | T-BRF-04 |
| BR-04 | ANZSIC 2006 division structure follows the ABS codelist | ABS-ANZSIC | `src/productivity/anzsic.ts#SUBDIVISION_RANGES`, `src/productivity/anzsic.ts#divisionOf` | T-BRF-14 |
| BR-05 | A lever's industries default to the scope and must lie within it | Plan §5.1 | `src/productivity/brief.ts#leverReach` | T-BRF-05 |
| BR-06 | The conduct lever takes one route: mark-up (C6) or PMR indicator (C7) (overlap rule O-3) | Plan §6.5 | `src/productivity/brief.ts#ConductLeverSchema` | T-BRF-06 |
| BR-07 | A moved threshold needs its previous value; threshold ids are unique | Plan §5.1 | `src/productivity/brief.ts#ThresholdLeverSchema` | T-BRF-07 |
| BR-08 | Every lever block changes at least one thing | Plan §5.1 | `src/productivity/brief.ts#EntryLeverSchema` (and the other lever schemas) | T-BRF-08 |
| BR-09 | A company tax change cannot also be its own funding tax (overlap rule O-5) | Plan §6.5 | `src/productivity/brief.ts#PolicyBriefSchema` | T-BRF-09 |
| BR-10 | Custom shocks: within scope, of a type their channel produces, and explicit ("adds" or "replaces") where a lever already feeds that channel and industry (overlap rule O-6) | Plan §6.5 | `src/productivity/brief.ts#CustomShockSchema` | T-BRF-10 |
| BR-11 | Phase-in no longer than the duration; jurisdictions listed once; states within the jurisdictions | Plan §5.1 | `src/productivity/brief.ts#PolicyBriefSchema` | T-BRF-11 |
| BR-12 | The burden block is the RBM proposal, parsed by the RBM schema with its defaults. It gives the same RBE as on its own, and must run for the brief's duration | DECISIONS #81 | `src/engine/schema.ts#ProposalSchema` | T-BRF-12 |
| BR-13 | Warnings PB-01 to PB-04 (nothing to cost; burden population outside the scope; unsourced custom shock; unconfirmed language-model estimate) flag problems without blocking | Plan §5.3; DECISIONS #59 | `src/productivity/brief.ts#briefWarnings` | T-BRF-13 |
| BR-14 | Licensed occupations use six-digit OSCA 2024 codes | ABS-OSCA | `src/productivity/brief.ts#LabourLeverSchema` | T-BRF-16 |
| BR-15 | One vocabulary of channels, shock types and overlap rules, shared by the brief and the engine | Plan §6.2, §6.5 | `src/productivity/channels.ts#CHANNELS`, `src/productivity/channels.ts#OVERLAP_RULES` | T-BRF-15 |
| BR-16 | Briefs may be confidential: saved briefs (`*.brief.json`) are gitignored, except the illustrative examples; the built page makes no network requests | DECISIONS #37 | `.gitignore`; Vite CSP | T-E2E-07, T-BRF-16 |

### 2.3 Layer A: direct effects by channel (P4)

The formulas below are specified now and implemented in P4. "Derived" marks a mapping this tool makes, rather than one taken from the source; each derived mapping has an interpretation in section 3.

| ID | Formula | Parameters (grade, tag) | Source | Phase |
|---|---|---|---|---|
| F-C1-01 | Δln MFP_i = −ΔC_i / GVA_i, where ΔC_i is the RBE's average annual change in compliance cost for populations in industry i (fees and taxes are already outside the RBE). **Derived** (A-P01) | GVA by industry (ABS ASNA, Australian Industry) | RBM (input); plan §6.2 | P4 |
| F-C1-02 | ΔC_i × (1 − s), s = share of substantive compliance producing unmeasured benefits | s: user-set, default 0 (D) | Plan §6.2 | P4 |
| F-C1-03 | When C4 is active, entrants' compliance cost is taken out of C1 before adding (O-1) | — | Plan §6.5 | P4 |
| F-C2-01 | Δln c ≈ r·d for a delay of d years, then applied through C3. **Derived** (A-P02) | r: 7% real (OIA-CBA, D as a delay cost of capital); holding cost about 5% a year as sensitivity (PC2025-NZ, C, [P]) | Plan §6.2 | P4 |
| F-C2-02 | Delay costs already in the RBE are left out of the user-cost shock (O-2) | — | Plan §6.5 | P4 |
| F-C3-01 | User cost c = q(r + δ)(1 − τz)/(1 − τ) | τ, z from the brief; δ by asset type (ABS ASNA) | Hall–Jorgenson (textbook); KPB2016 | P4 |
| F-C3-02 | Δln K = −σ·Δln c | σ = 0.40 (CFM2011, B, [A]); range 0.4–1.4 (KPB2016, C, [P]) | CFM2011; KPB2016 | P4 |
| F-C3-03 | Δln LP = α_i·Δln(K/L), α_i = industry capital share | α_i (ABS-MFP Table 14) | ABS-MFP | P4 |
| F-C4-01 | Δentry_i = ε·Δ(entry cost_i / GDP per capita), with ε = 0.5 pp per 12 pp (cutting entry cost from 20% to 8% of GNP per capita), applied only to naturally high-entry industries. **Derived** (A-P03) | ε (KLR, B, [P]); Australian entry cost 2.25% of GDP per capita for scale (DJ2002, [P]) | KLR | P4 |
| F-C4-02 | A number cap: Δentry_i = −(excluded share) × baseline entry rate_i. **Derived** | Baseline entry rates (ABS CABEE) | Plan §6.2 | P4 |
| F-C4-03 | Δg_i = β₂·Δentry_i·gap_i, β₂ = 0.009 per pp of entry rate | β₂ (AHHW2022, A, [P]); gap_i: paper's sample mean until a public measure exists (A-P04) | AHHW2022 | P4 |
| F-C4-04 | Exit costs: no verified elasticity; reported, not quantified, in v1 | — | Plan §6.2 | P4 |
| F-C5-01 | Screen: businesses and employment within ±10% of the threshold (CABEE size bands; ATO turnover bands) | — | Plan §6.2 | P4 |
| F-C5-02 | Bounded growth-tax cost, scaled by the share of employment near the threshold: between Gourio & Roys (under 0.3% of output per worker) and Garicano, Lelarge & Van Reenen (a 2.3% labour-tax equivalent costs 1.3–3.4% of GDP). **Derived** (A-P05) | GR2014 (B, [A]); GLVR2016 (B, [A]); Australian check E61-2024 (A, [P]) | GLVR2016; GR2014 | P4 |
| F-C6-01 | Misallocation loss interpolated within Hambur & Freestone: an aggregate mark-up rise from 1.18 to 1.25 (harmonic) raised the value-added misallocation cost by 1.16–2.52 pp. Linear inside that interval; no extrapolation. **Derived** (A-P06) | HF2025 (A, [P]) | HF2025 | P4 |
| F-C7-01 | Δln MFP_LR = β·ΔETCR, β ∈ [−0.047, −0.037] per index point; the 5-year effect is about one-third of the long run | EG2016 Table 1 (C, [P]); the paper notes large standard errors with year effects | EG2016 | P4 |
| F-C7-02 | Δln(K/Y) = −0.035 or −0.025 × ΔETCR | EG2016 (C, [P]) | EG2016 | P4 |
| F-C7-03 | Other PMR indicators are costed only where the evidence library holds an elasticity; otherwise the lever is reported, not quantified (A-P07) | — | Plan §6.7 | P3–P4 |
| F-C8-01 | Licensing: Δ LP_i = 1.6% per unit cut in stringency, weighted by the employment share of the licensed occupations in industry i. **Derived** weighting (A-P08) | OECD elasticity as used in PC2024 (C, [P]); employment by occupation (ABS-OSCA with LFS EQ08) | PC2024 | P4 |
| F-C8-02 | Non-competes: Δ LP = 10% pass-through of JLL wage effects (2.4% in heavy-use service industries, 1.4% elsewhere), scaled by the change in coverage. **Derived** scaling (A-P09) | PC2024 L1 (C, [P]); JLL ([P]) | PC2024 | P4 |
| F-C9-01 | Δln R&D = ε·Δln(R&D user cost); ε ≈ −0.1 short run, ≈ −1 long run | BGVR2002 (B, [A]) | BGVR2002 | P4 |
| F-C9-02 | GDP per capita in the long run: +0.46% per +0.10 pp of business R&D in GDP | EG2016 (C, [P]) | EG2016 | P4 |
| F-C10-01 | Δln MFP = (0.006 to 0.008) × Δopenness (pp of GDP) | EG2016 (C, [P]) | EG2016 | P4 |
| F-C10-02 | Tariff removal checked against PC2024: GDP +0.13 to +0.25% | PC2024 (A, [P]) | PC2024 | P6 |
| F-C10-03 | FDI restrictiveness: a 10% cut → +2.1% bilateral FDI stocks; reported as investment, with no MFP effect (no verified elasticity) | MR2019 (C, [P]) | MR2019 | P4 |
| F-C11-01 | Excess burden = revenue × MEB of the funding tax: company 0.50 (0.20–1.35), labour income 0.21, GST (current base) 0.19, personal income 0.16, conveyancing duty 0.72, land −0.10 | CAO2015 (A, [P]); KPMG 2010/2011 as sensitivity (C, [P]) | CAO2015 | P4 |

### 2.4 Layer B: economy-wide effects (P4)

| ID | Formula | Source | Phase |
|---|---|---|---|
| F-B-01 | Labour-augmenting shocks: Δln Y ≈ Σ_i (W_i/W)·x_i, with W_i the industry wage bill. Check: an economy-wide 0.1% labour productivity rise gives +0.10% GDP. **Derived** (A-P10) | ABS-IO Table 17 or ASNA Table 46 (weights); PC2024 (check, [P]) | P4 |
| F-B-02 | Hicks-neutral value-added MFP shocks: Δln Y ≈ Σ_i (GVA_i/GDP)·z_i/(1 − α). **Derived** | EG2016 (production-function aggregation) | P4 |
| F-B-03 | Long-run closure: fixed aggregate employment and a fixed rate of return (capital adjusts) | PC2024 Appendix C ([P]) | P4 |
| F-B-04 | Time path: shocks phase in over `phaseInYears`; MFP and K/Y adjust at error-correction speeds of about −0.03 to −0.05 a year; results at years 1, 5 and 10 and the long run | EG2016 ([P]) | P4 |
| F-B-05 | Back-test against every PC National simulation (27 plus lower bounds and linearity tests). Target within ±15% of real GDP for pure productivity shocks; rent and tariff simulations reported, not targeted | PC2024 workbook | P4 |
| F-B-06 | GNI, terms of trade, CPI and state GSP are not modelled in v1; every result says so | Plan §6.3 | P4 |

### 2.5 Uncertainty, overlaps and the gate (P4)

| ID | Rule | Source | Code | Test |
|---|---|---|---|---|
| F-U-01 | Monte Carlo: seeded and deterministic; 2,000 draws by default; triangular distributions on low, central and high; reports the 10th, 50th and 90th percentiles and a tornado chart of the top ten parameters | Plan §6.4 | `src/productivity/brief.ts#AnalysisSchema` (settings); sampler in P4 | T-BRF-01; P4 |
| F-U-02 | A parameter with no published range gets ±50%, graded D | Plan §6.4 | P4 | P4 |
| F-U-03 | A realisation factor (default 1, 0–2) scales every productivity effect | Plan §6.4 | `src/productivity/brief.ts#AnalysisSchema` | T-BRF-01 |
| F-O-01 | Overlap rules O-3, O-5 and O-6 are enforced when the brief is read; O-1, O-2 and O-4 when the engine runs | Plan §6.5 | `src/productivity/channels.ts#OVERLAP_RULES` | T-BRF-06, T-BRF-09, T-BRF-10; P4 |
| F-G-01 | The evidence gate (plan §6.6):<br>• central effect ≥ $200m a year and largest channel graded A or B → shown in full;<br>• below $200m, or graded C → "indicative";<br>• graded D, or with unconfirmed estimates → GDP hidden unless `showUngatedEconomyWide` | OIA-COMP; IAF-PG p. 8 | `src/productivity/brief.ts#AnalysisSchema` (the opt-in); gate in P4 | T-BRF-01; P4 |

## 3. Interpretations and assumptions

Each was made by this tool, not taken from a source. Each one is proposed in P0 and is checked again when its channel is implemented.

| ID | Interpretation | Why | Check in |
|---|---|---|---|
| A-P01 | Compliance work produces no measured output, so a change in compliance cost is a change in measured MFP of the same share of GVA | National accounts count the inputs but not the "output" of compliance. It is an upper bound if some compliance produces unmeasured benefits (F-C1-02) | P4 |
| A-P02 | A delay of d years raises the user cost of capital by about r·d | First-order approximation of (1 + r)^d − 1 for small r·d | P4 |
| A-P03 | KLR's cross-industry estimate (entry cost relative to GNP per capita) can be applied to a change in one industry's entry cost relative to GDP per capita, in naturally high-entry industries only | KLR identify the effect from industries with naturally high entry; applying it elsewhere would extrapolate | P3–P4 |
| A-P04 | Until a public measure of each industry's distance to the productivity frontier exists (it needs BLADE), AHHW2022's sample means are used, labelled | The interaction needs a gap; using the paper's own means keeps the estimate within its sample | P3–P4 |
| A-P05 | Size-threshold costs are bounded between two published structural estimates, scaled by the share of employment near the threshold | No Australian structural estimate exists; the e61 bunching evidence is used as a check | P4 |
| A-P06 | Hambur & Freestone's change in misallocation cost can be interpolated linearly inside their mark-up interval, never beyond it | Their model is non-linear; interpolation inside a computed interval is the least extrapolation | P4 |
| A-P07 | Only the ETCR has a verified MFP elasticity (EG2016); other PMR indicators need an evidence-library entry before they are costed | Avoids applying a network-sector elasticity to other sectors | P3 |
| A-P08 | Licensing effects are weighted by the employment share of the affected licensed occupations in each industry | The PC applied a uniform shock to whole industries; occupation weights make it specific to the policy | P4 |
| A-P09 | The non-compete effect scales with the change in the share of workers covered | The PC modelled a ban (coverage to zero); partial changes scale linearly, following the PC's linearity finding | P4 |
| A-P10 | Labour-augmenting shocks aggregate with wage-bill weights. A scratch check of PC2024 L2 (+0.8% labour productivity in 15 industries with 34.4% of GSP gives +0.387% real GDP) implies 1.41 with GVA weights, so GVA weights would be wrong | To be confirmed by the F-B-05 back-test | P4 |
