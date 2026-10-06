# Model summary: Hambur & Freestone (2025) / Edmond, Midrigan & Xu (2023)

Sources read so far:

- **H&F**: Hambur, J. and Freestone, O. (2025), RBA RDP 2025-05, read in full (`literature/rdp2025-05.pdf`, 33 pp., including Appendices A and B). Page numbers below are the paper's printed page numbers.
- **EMX**: Edmond, C., Midrigan, V. and Xu, D.Y. (2023), *JPE* 131(7). The model (Section II), efficient allocation (III), calibration (IV.A) and oligopoly set-up (VI) were read on 2026-10-05 (`literature/emx2023_jpe.pdf`, git-ignored).
- **H&F replication code**: the RBA supplementary-information zip, which contains H&F's edited copy of the EMX MATLAB code and their input moments (`data/raw/hf2025_supplementary/`). Read on 2026-10-05.

Items tagged **[EMX: verify]** below were open when this note was first written. **§4 now records how each was resolved**, with the source file. Everything else is either quoted from H&F (equation and table numbers given) or derived algebraically from H&F's equations, with the derivation shown.

---

## 1. Model structure (H&F Section 3)

### 1.1 Household (eqs 1–4)

- Preferences: $\sum_t \beta^t\left(\log C_t - \varphi \frac{L_t^{1+\nu}}{1+\nu}\right)$.
- Budget constraint: $C_t + I_t = W_t L_t + R_t K_t + \Pi_t$.
- Capital accumulation: $K_{t+1} = (1-\delta)K_t + I_t$.
- Labour supply: $\varphi C_t L_t^{\nu} = W_t$.
- The final good is the numeraire.
- Steady state:
  - the Euler equation gives $R = 1/\beta - 1 + \delta$;
  - profits $\Pi$ are rebated to the household.
- H&F call $\nu$ "the elasticity of labour supply" (p. 5) and set it to 1 (Table 3). With this utility function the Frisch elasticity is $1/\nu$. The two readings coincide at 1, but they matter for the Phase 2 sensitivity (see DECISIONS.md, D-007).

### 1.2 Intermediate-goods firms (eqs 5–8)

- Gross-output production function (nested CES, elasticity $\theta$ between value added $v$ and materials $x$):
  $y_i = z_i\left[\phi^{1/\theta} v_i^{(\theta-1)/\theta} + (1-\phi)^{1/\theta} x_i^{(\theta-1)/\theta}\right]^{\theta/(\theta-1)}$.
- Value added is Cobb–Douglas: $v_i = k_i^{\alpha} l_i^{1-\alpha}$, with $1-\alpha = 2/3$.
- Materials are the final good ("roundabout" input–output structure; p. 7).
- Every firm faces the same input prices. So the unit cost of the input bundle, $c$, is common, and firm $i$'s marginal cost is $c/z_i$.
- Entry: pay fixed cost $\kappa$, then draw $z \sim G(z)$, which is Pareto with tail $\xi$ (p. 6).
- Exit: exogenous, at rate 0.04 (Table 3). Footnote 9 notes this is an employment-weighted exit concept, consistent with EMX.
- Sector output aggregates firms with a Kimball aggregator: $\int_0^{n(s)} \Upsilon\left(y_i(s)/y(s)\right) di = 1$ (eq. 7).

### 1.3 Klenow–Willis Kimball demand (eq. 8 and Appendix A.3)

- Inverse demand (A1), with relative quantity $q = y_i/y$:
  $\Upsilon'(q) = \frac{\bar\sigma-1}{\bar\sigma}\exp\left(\frac{1-q^{\varepsilon/\bar\sigma}}{\varepsilon}\right)$, with $\bar\sigma>1$.

Derived from (A1); I checked each by differentiation:

- **Demand elasticity:** $\sigma(q) = -\Upsilon'/(\Upsilon'' q) = \bar\sigma\, q^{-\varepsilon/\bar\sigma}$.
- **Markup:** $\mu(q) = \sigma(q)/(\sigma(q)-1) = \bar\sigma/(\bar\sigma - q^{\varepsilon/\bar\sigma})$.
  - It is finite only for $q < \bar\sigma^{\bar\sigma/\varepsilon}$.
  - $\mu \to 1$ as $q \to 0$.
- **Level of the aggregator** (needed for the constraint in eq. 7):
  $\Upsilon(q) = 1 + (\bar\sigma-1)e^{1/\varepsilon}\varepsilon^{\bar\sigma/\varepsilon-1}\left[\Gamma\left(\tfrac{\bar\sigma}{\varepsilon},\tfrac{1}{\varepsilon}\right) - \Gamma\left(\tfrac{\bar\sigma}{\varepsilon},\tfrac{q^{\varepsilon/\bar\sigma}}{\varepsilon}\right)\right]$.
  - $\Gamma$ is the upper incomplete gamma function.
  - Differentiating gives (A1) back, and $\Upsilon(1)=1$.
- **Choke price:** $\Upsilon'(0) = \frac{\bar\sigma-1}{\bar\sigma}e^{1/\varepsilon}$ is finite. So low-productivity firms may choose not to produce, which gives an endogenous productivity cut-off. **[EMX: verify]** whether EMX's Pareto lower bound or this choke cut-off is the binding lower limit of active firms. Related question: how inactive entrants enter the Kimball constraint, given that $\Upsilon(0)\neq 0$ in this normalisation.
- **Superelasticity mapping (A2–A3):**
  - Sales share: $\omega \propto \Upsilon'(q)q$.
  - Then $F(\mu) \equiv 1/\mu + \ln(1-1/\mu) = a + \frac{\varepsilon}{\bar\sigma}\ln\omega$ holds exactly, with $a = 1 - 1/\bar\sigma - \ln\bar\sigma$ plus the share normalisation (I re-derived this).
  - So the slope of the within-firm regression is the superelasticity $\varepsilon/\bar\sigma$, which equals 0.13 in the baseline.
  - CES is the special case $\varepsilon = 0$.

### 1.4 Firm optimisation and the market allocation

- **Firm first-order condition.** Firms choose $q$ to maximise profit, which gives price = $\mu(q)\times$ marginal cost:
  $\Upsilon'(q_i)\,D = \mu(q_i)\,c/z_i$, where $D$ is a sector demand index.
- **Monotonicity.** The left side falls in $q$ and the right side rises. So $q$, sales share and markup all increase with $z$.
- **Scale invariance.** Write $x = z/z^\ast$, where $z^\ast$ is the lowest active productivity. Then $q$ depends only on $x$ and $(\bar\sigma,\varepsilon)$. If $G$ is Pareto above $z^\ast$, then $x$ is Pareto($\xi$) on $[1,\infty)$ whatever the mass of entrants. Every *relative* object (shares, markups, top-5% share, misallocation) is then a function of $(\xi,\bar\sigma,\varepsilon)$ only, and the mass of firms $N$ is pinned down by the Kimball constraint. **[EMX: verify]** This is the property that lets the static calibration be separated from the general-equilibrium block.

### 1.5 Aggregation (eqs 9–15)

- **Final good** (eq. 9): CES across sectors, $Y = \left(\int_0^1 y(s)^{(\eta-1)/\eta} ds\right)^{\eta/(\eta-1)}$.
  - In the baseline, sectors are ex ante identical (one representative Pareto/Kimball structure), so $\eta$ does not affect any baseline result.
  - $\eta$ matters for the division-level model and the oligopoly model.
- **Aggregate TFP** is a sales-weighted harmonic mean (eq. 10):
  - $z(s) = \left(\int q_i(s)/z_i(s)\,di\right)^{-1}$
  - $Z = \left(\int q(s)/z(s)\,ds\right)^{-1}$
  - Equivalently, $Z = Y/X$, where $X = \int y_i/z_i$ is total use of the input bundle. Unit test 3 checks this.
- **Markups** are harmonic sales-weighted (eqs 11–12). For sectors, $\mu(s) = \left(\int \omega_i/\mu_i\right)^{-1}$, and $M$ aggregates sectors the same way.
  - In the model, the cost-weighted arithmetic mean of firm markups equals the harmonic sales-weighted mean: both are total sales / total variable cost.
  - So the model has a **single** aggregate markup $M$.
  - H&F's "harmonic" and "cost-weighted" columns are therefore **two separate calibrations** of the same model, to two data targets ($M$ = 1.18/1.25 vs 1.25/1.33). Footnote 8 says this; see D-005.
- **Sector shares and aggregate TFP** with markup dispersion (eqs 13–14):
  - $q(s) = \left(\frac{\mu(s)}{M}\frac{Z}{z(s)}\right)^{-\eta}$
  - $Z = \left(\int (\mu(s)/M)^{-\eta} z(s)^{\eta-1} ds\right)^{1/(\eta-1)}$
- **Value-added productivity** (eq. 15, transcribed as printed):
  $Z_{va} = \phi^{1/(\theta-1)}\frac{1-(1-\phi)Z^{\theta-1}M^{-\theta}}{\left[1-(1-\phi)Z^{\theta-1}M^{1-\theta}\right]^{\theta/(\theta-1)}}Z$
  - The level of $M$ distorts the choice of materials relative to value added ("input misallocation").
  - "Value added (no input)", which EMX call "Value added, $\mu=1$", sets $M=1$ in this mapping, so it captures only misallocation across firms through $Z$. **[EMX: verify]** the exact definition.
  - $\phi$ is set to match a materials share of gross output of 0.47 (Table 3). **[EMX: verify]** whether this share is measured in costs or in revenue.

### 1.6 Static misallocation cost (Section 5.1; Table 4)

- **Static planner.** Holding total inputs (and the set of firms) fixed, the planner equalises marginal products: $\Upsilon'(q_i)\propto 1/z_i$. This is the market first-order condition with $\mu(\cdot)\equiv 1$.
- **The three reported losses**, as a percentage of planner productivity:
  - gross output: from $Z$;
  - value added: from $Z_{va}$, using the market $M$;
  - value added (no input): from $Z_{va}$ with $M = 1$.
- Table 4 note: "percentage loss in productivity relative to the efficient static planner's problem allocation".
  - **[EMX: verify]** whether the loss is $1 - Z/Z^\ast$ or $Z^\ast/Z - 1$. The two differ by about 0.01 ppt at the 1% level, but by a lot for the large division-level numbers, e.g. Mining VA at 64.61%.
  - **[EMX: verify]** whether the planner also re-optimises the active set of firms (the choke cut-off).

### 1.7 Full steady state (Section 7; Tables 11 and B9)

- **Market steady state.** The decentralised equilibrium contains:
  - aggregate markup $M$;
  - misallocation through $Z$;
  - free entry, where the expected present value of profits, discounted at $\beta(1-\text{exit})$, equals $\kappa$;
  - capital and labour first-order conditions under the markup wedge.
- **First best.** The planner removes all markup distortions (level and dispersion) and chooses entry efficiently.
- **Uniform subsidy (Table B9).** A uniform production subsidy offsets the *level* of markups (the deadweight-loss channel) but leaves dispersion and entry distortions in place.
- **Reported numbers** are percentage gains in output, consumption, hours and welfare between steady states, ignoring transitions.
  - **[EMX: verify]** the welfare metric. It is presumably the consumption-equivalent variation between steady states.
  - **[EMX: verify]** the normalisation of $\varphi$ and $\kappa$, and whether the entry cost is paid in final goods or in labour.
- Arithmetic check: the "mid-2000s relative to mid-2010s" rows of Table 11 equal $(1+g_{10})/(1+g_{00})-1$ to rounding. For example, output: $2.41/1.82 - 1 = 32\%$.

### 1.8 Oligopoly variant (Section 6; eqs 16–21; Tables 8–10)

- **Market structure:**
  - each sector has $n$ firms, with CES within the sector (elasticity $\gamma$) and CES across sectors (elasticity $\eta$), $\gamma > \eta > 1$;
  - Cournot competition;
  - Pareto productivity.
- **Firm demand elasticity** (eq. 19): $\sigma_i = \left[\omega_i/\eta + (1-\omega_i)/\gamma\right]^{-1}$.
- **Markup** (eq. 20): $1/\mu_i = (1-1/\gamma) - (1/\eta - 1/\gamma)\omega_i$, where $\omega_i$ is the firm's sales share within its sector.
- **Sector markup** (eq. 21): $1/\mu(s) = (1-1/\gamma) - (1/\eta-1/\gamma)\,\mathrm{HHI}(s)$. This is why the industry labour share is linear in HHI.
- **Calibration:** $(\xi,\eta,\gamma)$ to four moments (Table 8):
  - harmonic markup;
  - top-4 share;
  - top-20 share (unweighted averages across industries);
  - slope of the regression of industry labour share on HHI, which is −0.15 (EMX use −0.21).
- **Fixed inputs:** the number of firms per industry is set from data (3,440 and 3,884). Calibrated values are in Table 9.
- **[EMX: verify]**
  - whether $n$ is fixed or drawn from a distribution with that mean (H&F say "average number of firms");
  - the number of simulated sectors and the random-number scheme;
  - the exact regression specification in the model (levels, value-added vs gross-output labour share, any controls);
  - how the over-identified system (four moments, three parameters) is weighted.

---

## 2. Calibration algorithm (baseline monopolistic-competition model)

Fixed parameters (Table 3):

| Parameter | Value |
|---|---|
| β | 0.96 |
| δ | 0.06 |
| exit rate | 0.04 |
| 1−α (labour share of value added) | 2/3 |
| labour supply elasticity | 1 |
| θ | 0.5 |
| materials share of gross output | 0.47 |
| superelasticity ε/σ̄ | 0.13 (Table 1, both periods) |

For each period (mid-2000s, mid-2010s) and each markup target (harmonic, cost-weighted):

1. Fix $\varepsilon/\bar\sigma = 0.13$.
2. Choose the Pareto tail $\xi$ and the average elasticity $\bar\sigma$ to hit two moments exactly:
   - the aggregate markup $M$: 1.18 / 1.25 harmonic, or 1.25 / 1.33 cost-weighted;
   - the top-5% sales share: 0.68 / 0.70.
   
   The top-5% share is the share of sales of the top 5% of active firms in a sector. In the data, it is the unweighted mean across 4-digit ANZSIC industries.
   
   Expected solutions (Table 2), as ($\xi$, $\bar\sigma$):

   | | Harmonic | Cost-weighted |
   |---|---|---|
   | Mid-2000s | (5.59, 9.45) | (4.00, 7.26) |
   | Mid-2010s | (4.04, 7.02) | (3.05, 6.03) |
3. Set $\phi$ to match the 0.47 materials share, given $M$ and $Z$.
4. Static block: compute market and planner $Z$, then the GO, VA and VA($\mu$=1) losses (Table 4), and markup percentiles (Table 5).
   - **[EMX: verify]** the weighting of the percentiles in Table 5. The model's 25th percentile of 1.18 exceeds $\bar\sigma/(\bar\sigma-1)=1.16$, which is the markup of a firm at $q=1$. With Pareto-distributed productivity, most firms by count are small, so unweighted percentiles would sit closer to 1. The percentiles are therefore probably sales- or cost-weighted.
5. GE block: solve the market steady state, the first-best steady state and the uniform-subsidy steady state (Tables 11 and B9).

Variants, each a re-run of steps 1–5 with different inputs:

- **B.1 smaller sample:** different markup targets (Table B1).
- **B.2 time-varying superelasticity:** 0.11 and 0.09 (Table B4).
- **B.3 division level:** division-specific superelasticity, markup, top-5% share and materials share (Table 6).
  - Divisions with |superelasticity| < 0.05 are dropped, as is Accommodation & Food Services.
  - Value-added shares come from the ABS *Estimates of Industry Multifactor Productivity* (footnote 11).

---

## 3. Internal inconsistencies found in the paper

I checked all of these arithmetically against the text extracted from the PDF (`pdftotext`) and confirmed them against the rendered pages. The Phase 1 replication will report what the model implies for each.

| # | Location | Issue | Likely explanation |
|---|---|---|---|
| 1 | Table 10, VA (no input) | Levels 3.67 → 3.31 imply −0.36 ppt, but the reported change is **+1.18**. | 3.31 is exactly Table 4's harmonic mid-2010s VA (no input) cell, so it looks like a copy-paste error. If the +1.18 change is right, the mid-2010s level would be about 4.85. To be settled by the replication. |
| 2 | Table B3, harmonic, VA and VA (no input) | Levels 12.17 → 17.93 and 5.73 → 7.90 imply **+5.76** and **+2.17**, but the reported changes are +2.72 and +0.51. | 2.72 and 0.51 are exactly Table B6's *cost-weighted* VA and VA (no input) changes, so this also looks like a copy-paste error. |
| 3 | Tables B1 / B4, markup targets | Mid-2000s 1.37 / 1.59 are **above** mid-2010s 1.25 / 1.46, so markups would *fall*. Yet the B2 elasticities fall (5.49 → 4.88), costs rise (B3), and the text says the smaller sample gives higher markups. | The B1 rows look swapped. Table B4 repeats B1's markups, but the B5 parameters (5.64 / 8.91) are close to the baseline Table 2 values (5.59 / 9.45). That suggests B4 actually used the baseline markups (1.18 / 1.25 and 1.25 / 1.33) and the target rows were copied from B1. To be tested. |
| 4 | p. 10 text vs Table 4 | Text says the harmonic VA (no input) cost rose by "around **1.12**". The table says **1.16** (2.15 → 3.31). | Minor; text typo. |
| 5 | p. 10 text | "mid-2000s and **late**-2010s" vs "mid-2010s" everywhere else; p. 2 says estimates end in 2017. | The exact years in each window are **not stated** in H&F. They will need to be taken from Hambur (2023) to align the Phase 3 bridging windows. |

All other change rows checked out: Table 4, Table B6, Table B8 vs Table 7, and Table 11's relative rows, to within ±0.01 ppt or ±1 pt of rounding.

---

## 4. Resolved from the H&F code and the EMX paper (2026-10-05)

`hf/` below refers to `Model/Tables/Benchmark/` inside `data/raw/hf2025_supplementary/rdp-2025-05-supplementary-information.zip`.

| Open item | Resolution | Source |
|---|---|---|
| Productivity distribution | $\log z \sim$ Exponential($\xi$), i.e. $z\sim$ Pareto($\xi$) on $[1,\infty)$. Discretised with 5,000 Gauss–Legendre nodes on $[0, -\ln(10^{-22})/\xi]$, with weights renormalised. | `hf/objective.m`, `hf/start_aggr.m` |
| Choke cut-off vs Pareto lower bound | Both exist. Firms with $z < \frac{\bar\sigma}{\bar\sigma-1}e^{-1/\varepsilon}D$ are inactive ($q=0$), and the Kimball constraint $N\sum w\,\Upsilon(q)=1$ includes their $\Upsilon(0)$. **At all four Table 2 parameter sets the cut-off is below 1 (0.46–0.57), so it does not bind: every firm is active.** | `hf/findequilibrium.m`; Octave check |
| Normalisations | $Y=1$ and $N=1$ in the calibrated steady state. The entry cost $\kappa$ (`p.F`, in **labour** units) and the disutility weight $\psi$ are backed out from these. | `hf/objective.m`; EMX §IV.A |
| $\nu$ | **Inverse** Frisch elasticity ("We set the inverse of the Frisch elasticity of labor supply to $\nu=1$"). H&F Table 3's "elasticity of labour supply = 1" is this parameter. | EMX p. 1638; code comment `p.nu` |
| Materials share | 0.47 = intermediates' share of **sales** ($B/Y$). Matched exactly by resetting $\phi = 1 - m\,\Omega^{1-\theta}M$. | `hf/objective.m` |
| Calibration algorithm | Nelder–Mead (`fminsearchbnd`) over $(\xi,\bar\sigma)\in[2,20]\times[4,20]$, starting at (3, 8.0084), with TolX $10^{-5}$ and MaxFunEvals 200. It minimises the RMS of percentage deviations of ($M$, $B/Y$, top-5% share) from the data. The superelasticity is **imposed** ($\varepsilon = 0.13\,\bar\sigma$), not targeted. | `hf/start_calibration_main.m`, `hf/objective.m` |
| Top-5% share | Share of sales of firms above the 95th percentile of the productivity distribution. The calibration counts all entrants; the reporting script counts active firms only. These are identical when the cut-off does not bind (see above). | `hf/objective.m` vs `hf/start_aggr.m` |
| Static misallocation loss (Table 4) | **$(1 - Z/Z^\ast)\times 100$**, likewise for value added (`GDP/GDPp`) and value added with $M=1$ (`GDP1/GDPp`), holding $K$ and $L_p$ fixed. Note that `objective.m` prints $\log(Z^\ast/Z)$, but the tables use $1-Z/Z^\ast$. | `hf/start_aggr.m` (report `T3`) |
| Planner's static allocation | $q^\ast = \left(1-\min\{\varepsilon\ln(\tfrac{\bar\sigma}{\bar\sigma-1}D^\ast/z),1\}\right)^{\bar\sigma/\varepsilon}$. The planner also has a choke, so the active set is re-optimised. | `hf/findequilibrium.m` (`planner`) |
| Table 5 percentile weights | Labour-weighted (`w.*l`), which equals cost-weighted because input proportions are common across firms. | `hf/start_aggr.m` |
| Steady-state welfare (Table 11) | Consumption-equivalent between steady states: $dW = \left(\exp[(1-\beta)(W_{new}-W_{old})]-1\right)\times 100$, where $W = \frac{1}{1-\beta}\left(\log C - \frac{\psi}{1+\nu}L^{1+\nu}\right)$ and $L = L_p + \kappa\cdot\text{exit}\cdot N$. Transitions are ignored. | `hf/start_planner.m` |
| First best | `findequilibrium(…,'planner','new')` solves for $(D, Y, N)$ jointly with the planner's entry condition. | `hf/start_planner.m` |
| Uniform subsidy (Table B9) | `start_aggr.m` calls `start_subsidy`, but **no `start_subsidy.m` exists in the H&F Benchmark folder**. The EMX Dataverse package has only an autosave, `Benchmark/start_subsidy.asv`, plus `Cournot/start_subsidy.m`. **Open: Phase 1 must establish which file H&F ran.** | package listings |
| Oligopoly design | EMX: Poisson entry per sector, so $n(s)$ is random with mean $N$; Cournot; indirect inference on the labour-share–HHI slope (EMX use long differences; H&F's preferred annual specification gives −0.15). H&F inputs: firms per sector 3,439.8 / 3,884.0, top-4 0.394 / 0.412, top-20 0.593 / 0.633. **Simulation details (number of sectors, seeds, weighting) are still to be read from `Cournot/start_calibration_agg.m` and `start_olig.m` in Phase 1.** | EMX §VI; `Inputs for model.xlsx` |

### 4.1 New findings from the H&F input file and an Octave smoke test

1. **Unrounded targets** (`Inputs for model.xlsx`, sheets `Pre_main` / `Post_main`):

   | Target | Mid-2000s | Mid-2010s |
   |---|---|---|
   | Harmonic markup | 1.181255 | 1.249878 |
   | Cost-weighted markup | 1.252905 | 1.330354 |
   | Top-5% share | 0.682845 | 0.695717 |

   Specification 1 is cost-weighted and 2 is harmonic. Specifications 3–8 are unreported variants (median superelasticity, sales-weighted concentration).
2. **Table B1 is garbled, not just swapped.** The input file's smaller-sample markups are:

   | | Harmonic | Cost-weighted |
   |---|---|---|
   | Mid-2000s | 1.372 | 1.473 |
   | Mid-2010s | 1.459 | 1.587 |

   The paper prints 1.37 / 1.59 and 1.25 / 1.46. This supersedes the "rows swapped" hypothesis in §3, item 3.
3. **Table B4 used the baseline markups** (1.18 / 1.25 and 1.25 / 1.33), with superelasticities 0.107 (mid-2000s) and 0.088 (mid-2010s). The printed B4 target rows were copied from B1. This confirms the hypothesis in §3, item 3.
4. **Table B2's cost-weighted mid-2010s value of $\xi = 2.000$ sits exactly on the calibration's lower bound** ($\xi \ge 2$), so it is a corner solution, not an interior fit. The mid-2000s value of 2.121 is close to the bound as well.
5. **Smoke test** (Octave 8.4; the only change is that the `fsolve` calls are wrapped for Octave's syntax). One `objective()` call takes about 0.7 s. At the published Table 2 parameters:

   | Calibration | ($\xi$, $\bar\sigma$) | Model markup | Target markup | Model top-5% | Target top-5% | Result |
   |---|---|---|---|---|---|---|
   | Mid-2000s harmonic | (5.59, 9.45) | 1.1813 | 1.1813 | 0.6833 | 0.6828 | Matches |
   | Mid-2000s cost-weighted | (4.00, 7.26) | 1.2526 | 1.2529 | 0.6822 | 0.6828 | Matches |
   | Mid-2010s cost-weighted | (3.05, 6.03) | 1.3299 | 1.3304 | 0.6954 | 0.6957 | Matches |
   | **Mid-2010s harmonic** | **(4.04, 7.02)** | 1.2518 | 1.2499 | **0.6380** | **0.6957** | **Misses by 5.8 ppt** |

   So either Table 2's mid-2010s harmonic parameters are mis-printed, or H&F's Nelder–Mead stopped before converging (MaxFunEvals = 200). Phase 1 will re-run the calibration to tell which. If it is the latter, the Table 4 mid-2010s harmonic costs would also be affected.
