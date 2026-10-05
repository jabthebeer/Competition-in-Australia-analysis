# Model summary: Hambur & Freestone (2025) / Edmond, Midrigan & Xu (2023)

Sources read so far:

- **H&F**: Hambur, J. and Freestone, O. (2025), RBA RDP 2025-05, read in full (`literature/rdp2025-05.pdf`, 33 pp., including Appendices A and B). Page numbers below are the paper's printed page numbers.
- **EMX**: Edmond, C., Midrigan, V. and Xu, D.Y. (2023), *JPE* 131(7). **Not yet read.** The paper, online appendix and replication package could not be downloaded because the session's network policy blocks the hosts (see `../data/raw/SOURCES.md`).

Anything tagged **[EMX: verify]** below is my reconstruction of EMX. It is not stated in H&F, and it must be checked against the EMX paper or code before it is used in any result. Everything else is either quoted from H&F (equation and table numbers given) or derived algebraically from H&F's equations, with the derivation shown.

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

## 4. What I still need from EMX before implementing

1. The full model appendix: the Kimball constraint with inactive firms, the choke cut-off vs the Pareto lower bound, how the planner treats the active set, and the definition of the loss metric.
2. The GE block: the entry-cost units, the normalisations of $\varphi$ and $\kappa$, the welfare metric, and how the uniform subsidy is implemented.
3. The oligopoly simulation design: the distribution of $n$, the number of sectors, the seed and draw scheme, the labour-share–HHI regression in the model, and the moment weighting.
4. The replication code. If H&F's adapted code is in the RBA's RDP 2025-05 replication files (an RBA "read me" page for this RDP turned up in a web search but could not be opened), it should be the primary reference.
