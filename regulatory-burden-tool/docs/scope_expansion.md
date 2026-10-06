# Scope expansion: Competition and Consumer Act (CCA) stocktake, cost–benefit analysis, business dynamism

**Status:** Planning note for discussion (6 October 2026). Nothing here is approved or built.

## The request

Add three capabilities on top of the regulatory burden calculator:

1. regulatory costings for all existing consumer legislation in the CCA;
2. ultimately, a possible cost–benefit analysis for each provision of the CCA;
3. estimated effects on business entry and exit rates, and on competition overall.

## Short answer

All three can be built on the same engine, which was designed for add-on modules that read its output without changing the RBE. Each module is a research project in its own right, and the binding constraint is **evidence, not code**. I recommend:

- finishing the core tool (Phases 1–5) first;
- then running a **pilot on 3–5 provisions** before committing to the whole Act.

Two small schema fields should be added now so the expansion needs no migration later: `legalReference` on obligations and `industry` on populations (DECISIONS #42).

## Open scope question: which part of the CCA?

| Option | What it covers | Relative size |
|---|---|---|
| **A. The Australian Consumer Law (ACL) only** | CCA Schedule 2: general protections, specific protections, consumer guarantees, product safety, information standards, lay-by, unsolicited consumer agreements | Moderate |
| **B. A + consumer instruments made under it** | Option A, plus the Competition and Consumer Regulations, mandatory safety and information standards (e.g. button batteries, quad bikes), and consumer-facing mandatory industry codes (e.g. unit pricing) | Larger. This is where most *prescriptive* obligations sit. |
| **C. The whole CCA** | Option B, plus Part IV competition law (cartels, misuse of market power, the merger regime), all Part IVB industry codes (franchising, food and grocery, …), the Consumer Data Right, the Scams Prevention Framework, and telecommunications and energy access regimes | Very large. Several regimes are sector-specific and have their own existing Impact Analyses. |

**Recommendation:** start with **B**. It is what "consumer legislation" most naturally means, and it contains the obligations the RBM can actually cost.

**Unit of analysis.** Use the **obligation** (a duty to do something), not the section. Many sections are definitions, remedies or enforcement provisions, which have no RBM cost.

## Stage S1: stocktake of existing obligations (RBM costing)

### Method

- Each provision group becomes a proposal file in the engine.
- The "current" side is the existing obligation; the option is **outright repeal** (reformed = none). The RBE then equals the provision's burden relative to its absence.
- This reuses the core tool unchanged, and every parameter carries a source.

### What the RBM will and won't show

- **Prohibitions show little or no RBM cost.** Most of the ACL consists of *prohibitions*: misleading or deceptive conduct (s 18), false or misleading representations (s 29), unconscionable conduct, unfair contract terms. A normally efficient business doesn't mislead consumers anyway, so the RBM cost is mostly BAU and close to zero (RBM p. 3). Legal review and compliance programmes are partly in scope.
- **Prescriptive obligations hold the measurable costs.** Examples: consumer guarantee remedy processes, the prescribed warranty-against-defects text, mandatory injury reporting (s 131), recalls, safety and information standards, lay-by and unsolicited-agreement formalities, proof of transaction and itemised bills (ss 100–101), single-price display (s 48).
- **Risk:** a stocktake that reads as "the ACL costs almost nothing" because the RBM excludes BAU, enforcement and indirect effects. Results must be presented with that caveat, and alongside S2/S3.

### Structural issue: the ACL is a national scheme

- The ACL is applied as Commonwealth law *and* as state and territory law, through each jurisdiction's application Act under an intergovernmental agreement.
- Removing a CCA provision alone wouldn't remove the obligation, so costings of ACL changes are inherently inter-jurisdictional (RBM p. 6, R-33/R-34). The engine handles this, but the counterfactual must be stated clearly.

### Data

- **Entity counts:** ABS *Counts of Australian Businesses*, by industry and size.
- **Activity frequencies:** partly ACCC data (e.g. recalls, mandatory injury reports).
- **Time and cost per task:** usually unavailable, so assumptions, consultation or previous Impact Analyses are needed.
- **Previous Impact Analyses:** OIA has published dozens on CCA and ACL topics (found via its sitemap, 6 Oct 2026). They include consumer guarantees, unfair contract terms (several), the consumer product safety system, quad bike and button battery standards, unit pricing, unfair trading practices, scams, franchising, the Food and Grocery Code, the Consumer Data Right and merger reform. These are the richest source of sourced parameters. I haven't yet checked which have line-item detail.

## Stage S2: cost–benefit module

### Method

- **Discounting:** follow OIA's *Cost–benefit analysis* guidance (August 2023; still listed by OIA, with a note that references to the previous IA framework are out of date). That means NPV at a **7% real** discount rate, with **3% and 10%** sensitivity.
- **A wider cost base than the RBE,** kept as separate lines:
  - government administration and enforcement costs;
  - non-compliance costs;
  - indirect effects.

  Fees and levies are transfers, not economic costs. This module reads the RBE output; it never writes to the RBE table.
- **Benefits only where sourced.** Many consumer-law benefits (less detriment, more trust, lower search costs, deterrence) have no credible provision-level estimates. Where none exist, use **break-even analysis**: "the provision is justified if it avoids at least $X a year of consumer detriment". This respects the no-fabrication rule and is an accepted CBA technique.

### Risk

Spurious precision. Per-provision CBA of a framework law is rarely possible with confidence, so the output should be a ranked evidence table (cost, quantified benefit or break-even, evidence quality), not a single league table of net benefits.

## Stage S3: business dynamism and competition module

### Data

- **ABS *Counts of Australian Businesses, including Entries and Exits*.** Latest release 18 August 2026, covering July 2022 to June 2026. In 2025–26 the entry rate was 16.9% and the exit rate 13.8%. Available by ANZSIC industry and employment and turnover size. Public.
- **BLADE (firm-level).** Available through ABS DataLab with project approval, which takes time and needs an organisational sponsor.

### The hard part: attribution

- The ACL has applied uniformly nationwide since 2011, so there is little variation to identify the effect of a single provision.
- Credible designs exploit **industry-level exposure × timing of specific changes**, for example:
  - the extension of unfair contract terms protection to small business contracts;
  - the later introduction of UCT penalties;
  - individual mandatory safety standards that hit specific product categories.

### Proposed approach

Keep causal estimation **outside** the tool, in this repository's econometric programme. The tool then applies the estimates transparently:

1. Per-entity compliance cost by size cohort (already produced by the engine) ÷ typical revenue for that cohort = a cost share.
2. Cost share × an entry/exit elasticity (from your estimates or the literature, with a range) = an indicative change in entry and exit rates by industry and size.
3. A qualitative **OECD Competition Assessment Toolkit** checklist (already on the roadmap) for competition effects that can't be quantified.

This is where the calculator and the wider competition research programme connect.

## Sequencing proposal

| Stage | Content | Depends on |
|---|---|---|
| Phases 1–5 | Core RBM calculator (unchanged) | — |
| S0 (now, cheap) | Schema fields `legalReference`, `industry` | Phase 1 |
| S1 pilot | Obligation inventory for the chosen scope; cost 3–5 prescriptive provisions from published Impact Analyses | Phase 3 engine |
| S1 full | Remaining provisions, if the pilot shows the data supports it | S1 pilot review |
| S2 | CBA module (separate, discounted, break-even) | S1 pilot |
| S3 | Dynamism and competition module, fed by the repo's econometric estimates | S1 pilot; econometric work |

## Decisions needed

1. Scope A, B or C (recommendation: B).
2. Whether the stocktake is a *research output* (published reports and data in this repo) or a *feature of the tool* (a library of pre-built provision costings users can start from). These lead to different designs.
3. Whether S3 elasticities come from your own econometric work (preferred) or the literature.
