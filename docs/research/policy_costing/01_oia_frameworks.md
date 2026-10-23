> Research note for [`forward_plan_policy_costing.md`](../../forward_plan_policy_costing.md), compiled on 22 October 2026 by a Claude Code research agent from the sources listed. Figures carry the agent's verification tags where given ([P] primary source read, [A] abstract or official summary, [S] secondary only, UNVERIFIED). Downloaded copies mentioned below were kept in a temporary session folder and are not committed. Nothing here is a default parameter until it passes the P3 evidence-library check.

# Australian regulatory impact analysis: verified facts for the costing tool (checked 22 Oct 2026)

I read every primary document below in full text (PDF, DOCX or XLSX) unless I say otherwise. The downloaded copies are in a temporary session folder (not committed) (subfolders oia2026, oia2026b, pc2025, budget2026, uk, eu, us, nz, states).

## 1. OIA Impact Analysis Framework

**Name, date and URL:** *Australian Government Impact Analysis Framework*, dated July 2026. The foreword by Assistant Minister Patrick Gorman is dated June 2026. https://oia.pmc.gov.au/resources/australian-government-impact-analysis-framework. It comes with the *Practical Guide for Agencies* (June 2026). The OIA states: "The new framework commenced on 1 July 2026." It was announced on 17 June 2026.

**Scope.** An IA is only required for "regulatory policy proposals, or proposals with material competition impacts." A competition impact covers "barriers to set-up (or exit) for businesses, organisations or workers", "the ability or incentives for businesses to compete" and "changes to the choices, information, goods or services available to consumers." The practical guide adds that impacts should "consider changes in dynamism (that is, the entry and exit of businesses or organisations) over time."

**Thresholds.** An in-scope proposal that meets any one of these needs an IA:
- "IA threshold 1 (regulatory burden): proposals likely to change regulatory burden by $20 million or more in total (over 10 years)." This confirms your threshold 1 flag.
- "IA threshold 2 (material impacts): proposals likely to have indicative impacts of $200 million or more annually on the economic and social outcomes…" The guide says this explicitly covers "economic growth, household income, investment, innovation and productivity." For the preliminary test, no discounting is applied. A worked example uses a value of statistical life of "$5.87 million per life saved."
- "IA threshold 3 (distributional impacts): proposals likely to disproportionately and significantly impact a cohort, including small businesses, where no other impact assessment applies."

**Formats and sign-off.**
- The Dashboard IA is the default and "should be around 3 pages."
- A Detailed IA is needed only if the Prime Minister or Cabinet "call in" the proposal, or it would set a mandatory standard that deviates from international standards.
- A Statement of Sufficiency must be endorsed by a Deputy Secretary (SES Band 3) or higher.

**The 7 IA questions:**
1. Policy problem
2. Policy objective
3. Policy options (status quo plus at least one non-regulatory option)
4. Net benefit
5. Consultation
6. Implementation
7. Evaluation

Question 4 requires: "Where significant, assess the economic, competition, social, environmental or other impacts…"; "Assess the regulatory burden impacts… using the Regulatory Burden Measurement Framework"; and "Provide analysis of impacts based on cost-benefit analysis and other analysis to quantify impacts where possible."

**How competition and productivity are assessed.** The main source is the supplementary guidance *How to consider competition in impact analysis* (July 2026), https://oia.pmc.gov.au/sites/default/files/2026-06/competition-guidance.pdf.
- **Two tests.** "the benefits of the change to competition to the community as a whole outweigh the costs; and" the objectives "cannot be achieved by another approach that… does not restrict competition… and has net community benefits that are at least as high."
- **A checklist, not a model.** Its categories are "broadly based on the… OECD Competition Assessment Toolkit."
- **Qualitative is acceptable.** "many of the costs of restrictions on competition… may need to be described in qualitative terms."
- **Limits of cost-benefit analysis.** It flags that a CBA treats pass-through "as a transfer and will be ignored," and that a CBA "does not typically consider impacts on secondary markets."
- **Productivity.** "Consider whether the proposal is likely to improve productivity… identify the direction and channels of impact… Where aggregate (economy-wide) effects are claimed, these should be presented only if they are material and supported by robust evidence."
- **Dashboard template.** Economic impacts include "productivity (for example, efficiency and innovation), and competition impacts such as changes in market functioning and market power."
- **Discounting for CBA.** OIA's CBA note (July 2023, still listed with a "no longer current" banner and marked "under review") says: "OIA requires the calculation of net present values at an annual real discount rate of 7 per cent." Sensitivity tests at 3% and 10% are also required.

## 2. Regulatory Burden Measurement Framework (RBMF), July 2026

PDF: https://oia.pmc.gov.au/sites/default/files/2026-06/regulatory-burden-measurement-framework.pdf (resource page dated 1 July 2026).

**Your rates are confirmed, quoted exactly:**
- Work time: "This provides an economy-wide value for employees of $52.31 per hour… scaled up using a multiplier of 1.75 to account for the non-wage labour on-costs (for example, payroll tax and superannuation) and overhead costs… This results in a scaled up rate of $91.54 per hour ($52.31 multiplied by 1.75)."
- Leisure time: "the default value that should be used for an individual's leisure time is based on average weekly earnings and has been estimated at $41 per hour." It applies only to individuals living in Australia. For people not in the labour force, "discuss this with OIA."
- OIA's Regulatory Burden Estimate calculator (xlsx, 1 July 2026) has 91.54 and 41 hard-coded.

**Correction to your notes on the source data.** The rate is not built from AWOTE (average weekly ordinary time earnings). Footnote 4 says it is based on ABS *Employee Earnings and Hours*, "Data Cube 6 - Full-time non-managerial employees paid at the adult rate. Calculated using the ATO's online Simple Tax Calculator, 2024-25 tax rates."
- The same footnote also says "released January 2024", which may be stale. I could not verify whether the January 2026 ABS release was used.
- The main text says "average weekly earnings, but adjusted to include income tax." Whether the base is pre-tax or after-tax is ambiguous; the leisure rate is explicitly after tax.
- "The next update is scheduled for February 2028… yet to be confirmed."
- The previous version (February 2024) used $48.67 × 1.75 = $85.17 and a $37 leisure rate. That is useful if your tool needs versioning.

**Cost categories:**
- Compliance costs: administrative costs ("primarily to demonstrate compliance… usually record keeping and reporting") and substantive compliance costs ("to deliver the outcomes being sought").
- Delay costs: application delay and approval delay.
- Excluded: opportunity costs (unless delay-related), business-as-usual costs, enforcement and non-compliance costs, fees, levies and taxes, and "Indirect costs… including changes to market structure and competition impacts." So competition effects belong in IA question 4 or threshold 2, not in the regulatory burden estimate.

**Annualisation.** "You should cost your proposal over a 10-year default duration"; costs are "in real terms… Discount rates are not to be applied." One-off and start-up costs are "divided by the duration of the proposal." The result is a single point estimate; OIA uses the midpoint of any range.

**Who bears costs.** The regulatory burden estimate table is split into Business, Community organisations and Individuals, and is required "for every viable option." The framework suggests splitting into small, medium and large cohorts where effects vary. Government subsidies are subtracted.

**Offsets.** The July 2026 RBMF, framework and guide contain no offset requirement; a search of the text for "offset" found nothing.

**Inconsistency to handle in the tool.** The RBMF and practical guide require an "average annual change… over 10 years (without discounting)". But the Dashboard template asks for "[X$ over 10 years]", and the calculator labels its outputs "10 Year Total (For Dashboard, $M)" and "Annual Average over 10 years (For Preliminary Analysis, $M)". Report both figures. Threshold 1 is a 10-year total, which equals $2m a year on average.

## 3. Productivity agenda, 2025–26

- **Economic Reform Roundtable, Treasurer's closing press conference, 21 Aug 2025.** One of 10 reform directions was "better regulation and how we cut the clutter." He added: "The Productivity Commission is going to give us some options on the best way to measure progress on better regulation…" and "We are going to expand National Competition Policy."
- **Media release, 5 Sep 2025.** Letters from "38 Commonwealth regulators containing more than 400 ideas" were released, and the government committed to "Alter statements of expectations for Commonwealth regulators to emphasise the reduction of red tape and a better balance between outcomes and risk."
- **PC final report, *Creating a more dynamic and resilient economy* (No. 109).** Handed to government 10 Dec 2025, released 19 Dec 2025, tabled 29 Jan 2026.
  - Recommendation 2.2: "set a target to reduce the compliance and delay costs of its regulation by $10 billion by 2030," plus an annual Regulation Review.
  - Recommendation 2.3: "appoint an independent statutory commissioner to oversee the Office of Impact Analysis"; mandatory post-implementation review where impacts are "highly uncertain".
  - Recommendation 2.4: deliver "growth, competition and innovation."
  - The overview says portfolios "should operate under 'regulatory burden offsetting'."
- **Government response.**
  - Budget media release (12 May 2026): "reduce regulatory costs by $10.2 billion each year."
  - Budget fact sheet: this is a "gross reduction in regulatory burden." It also says "A new productivity policy objective for Ministerial Statements of Expectations has been set for all Commonwealth regulators", and that the IA framework would be improved from 1 July 2026.
  - 17 June 2026 release: "The Productivity Commission recommended that the Framework be administered by an independent statutory body. These changes will improve the impact analysis framework without adding the additional regulatory burden of a new statutory body." That is, the statutory recommendation was not adopted.
- **No separate "productivity test" found.** I found no standalone productivity test or regulatory budget for new policy proposals. The closest equivalents are the 2026 "material competition impacts" scope trigger and threshold 2. Whether a regulatory offset rule has been adopted is UNVERIFIED; I found no evidence that it has.

## 4. International comparators

- **OECD Competition Assessment Toolkit (v4.0, 2019).** It screens whether a regulation "A. Limits the number or range of suppliers; B. Limits the ability of suppliers to compete; C. Reduces the incentive of suppliers to compete; D. Limits the choices and information available to customers." This wording is quoted from the APEC–OECD Framework (2017) that reproduces it; oecd.org returned 403 to every request. It is mainly a qualitative screening checklist. The detail of Volume 2's quantification guidance is UNVERIFIED. The CMA describes the OECD manual as "updated to include more detailed guidance on methodologies."
- **UK Better Regulation Framework (2023 version; page updated 5 Sep 2025).**
  - Full scrutiny applies above "±£10m EANDCB" (equivalent annual net direct cost to business), which is annualised using the Green Book 3.5% discount rate. Australia's estimate, by contrast, is undiscounted.
  - A small and micro business assessment (SaMBA) is "mandatory" above £10m.
  - Competition: departments "should consider completing the… CMA's 'competition assessment checklist'… encouraged and may be expected for measures with a high impact."
  - The CMA guidelines (updated 28 Jul 2023) now have 5 questions, including one on new technologies and business models. For significant issues "quantitative analysis is preferred," but "will often have to be buttressed by qualitative evidence."
  - Current target: cut administrative burden by 25% this Parliament, which is £5.6bn of a £22.4bn baseline (2024 prices).
  - Whether a statutory Business Impact Target exists for this Parliament is UNVERIFIED.
- **New Zealand.** From 1 July 2026, under Cabinet circular CO (26) 2, a Regulatory Analysis Summary (no more than 20 pages) replaced the Regulatory Impact Statement. Its cost-benefit section was "strengthened to encourage monetisation," and a deregulatory option is required where regulation already exists. The template is tied to the principles in the Regulatory Standards Act 2025. Market power appears only as a market-failure prompt; there is no dedicated competition test (from searching the template text).
- **EU Better Regulation Toolbox (Dec 2025).**
  - Tool #21, Competitiveness check (Annex 5), covers cost and price, innovation, international and SME competitiveness. If impacts are significant, "strive to include quantitative elements."
  - Tool #23, the SME test, has four steps; "Since May 2025" an "SME Check" annex is mandatory for relevant initiatives.
  - Tool #24, Competition, covers market definition and market power.
- **US Circular A-4 (Nov 2023).**
  - Default real discount rate of about "2.0 percent".
  - Says analysis "generally should examine the benefits and costs" of substantial changes in market power.
  - Distributional weights are optional.
  - Executive Order 14192 (31 Jan 2025) directs OMB to "revoke OMB Circular No. A-4 of November 9, 2023… and… reinstate the prior version… issued on September 17, 2003". The formal revocation step is UNVERIFIED; secondary sources say it happened in February 2025.
  - OMB memo M-25-20 (26 Mar 2025) uses "a 7 percent end-of-period discount rate" for this order's accounting.
  - The 2003 version's 3%/7% rates were not re-checked in this session.

## 5. State equivalents

- **NSW: TPP19-01 *Guide to Better Regulation* (Jan 2019).** A Better Regulation Statement is required if a proposal would "impose a material restriction on competition." The competition test says regulation should not restrict competition unless "the benefits… outweigh the costs" and the objectives "can only be achieved by restricting competition." It gives six indicators of restriction. It is a qualitative checklist and is proportionate to impact.
- **Victoria: 2024 *Victorian Guide to Regulation* (published 28 Jun 2024; files updated Dec 2025).** The indicative trigger is burden "greater than $2 million per year." The summary includes "competition effects (for all proposals)." A small business assessment is mandatory for legislative impact assessments (LIAs). The Commissioner for Better Regulation assesses adequacy. The PC notes Better Regulation Victoria is overseen by a "non-statutory Commissioner for Economic Growth and Better Regulation."

## Sources

| Title | Publisher | Date | URL |
|---|---|---|---|
| Australian Government Impact Analysis Framework | PM&C / OIA | Jul 2026 | https://oia.pmc.gov.au/sites/default/files/resource/download/impact-analysis-framework.pdf |
| IA Framework Practical Guide for Agencies | OIA | Jun 2026 | https://oia.pmc.gov.au/sites/default/files/2026-06/impact-analysis-practical-guide.pdf |
| Regulatory Burden Measurement Framework | OIA | Jul 2026 | https://oia.pmc.gov.au/sites/default/files/2026-06/regulatory-burden-measurement-framework.pdf |
| RBMF (previous version) | OIA | Feb 2024 | https://oia.pmc.gov.au/sites/default/files/2024-02/regulatory-burden-measurement-framework.pdf |
| How to consider competition in impact analysis | OIA | Jul 2026 | https://oia.pmc.gov.au/sites/default/files/2026-06/competition-guidance.pdf |
| Dashboard IA template; Preliminary Analysis checklist; RBE calculator | OIA | Jun–Jul 2026 | https://oia.pmc.gov.au/resources/dashboard-impact-analysis-template ; https://oia.pmc.gov.au/resources/preliminary-analysis-checklist ; https://oia.pmc.gov.au/resources/regulatory-burden-estimate-calculator |
| Cost Benefit Analysis guidance note | OIA | Jul 2023 | https://oia.pmc.gov.au/sites/default/files/2023-08/cost-benefit-analysis.pdf |
| Strengthening the Impact Analysis Framework | Asst Minister Gorman | 17 Jun 2026 | https://ministers.pmc.gov.au/gorman/strengthening-impact-analysis-framework |
| Press conference, Canberra | Treasurer | 21 Aug 2025 | https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/transcripts/press-conference-canberra-26 |
| Regulatory reform to reduce red tape… | Treasurer / Finance Minister | 5 Sep 2025 | https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/media-releases/regulatory-reform-reduce-red-tape-and-ease-burden |
| Creating a more dynamic and resilient economy, Inquiry report No. 109 | Productivity Commission | 10/19 Dec 2025 | https://assets.pc.gov.au/2025-12/resilient-economy.pdf |
| Budget to boost productivity and cut regulatory costs by $10 billion | Treasurer | 12 May 2026 | https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/media-releases/budget-boost-productivity-and-cut-regulatory-costs-10 |
| Whole-of-Government Regulatory Reform Agenda fact sheet | Budget 2026–27 | May 2026 | https://budget.gov.au/content/factsheets/download/factsheet-regulatory-reform.pdf |
| Better Regulation Framework guidance | UK DBT | 2023 (page updated 5 Sep 2025) | https://www.gov.uk/government/publications/better-regulation-framework |
| Technical annex: 25% administrative burden reduction | UK Government | c. Jul 2026 | https://assets.publishing.service.gov.uk/media/6a4d0039c5aa1b17abab415c/technical_annex_administrative_burden_reduction.pdf |
| Competition assessment: guidelines for policymakers (Parts 1–2) | CMA | 28 Jul 2023 | https://www.gov.uk/government/publications/competition-impact-assessment-guidelines-for-policymakers |
| APEC–OECD Framework on Competition Assessment | APEC | 2017 | https://mddb.apec.org/Documents/2017/SOM/SOM3/17_som3_025anx1.pdf |
| Better Regulation Toolbox | European Commission | Dec 2025 | https://commission.europa.eu/document/download/9c8d2189-8abd-4f29-84e9-abc843cc68e0_en?filename=BR+toolbox+-+December+2025.pdf |
| Circular A-4 | US OMB | 9 Nov 2023 | https://bidenwhitehouse.archives.gov/wp-content/uploads/2023/11/CircularA-4.pdf |
| EO 14192, Unleashing Prosperity Through Deregulation | US President | 31 Jan 2025 | https://www.govinfo.gov/content/pkg/FR-2025-02-06/html/2025-02345.htm |
| M-25-20 | OMB / OIRA | 26 Mar 2025 | https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-20-Guidance-Implementing-Section-3-of-Executive-Order-14192-Titled-Unleashing-Prosperity-Through-Deregulation.pdf |
| RIA requirements page; Key changes PDF; RAS template | NZ Ministry for Regulation | Jun–Aug 2026 | https://www.regulation.govt.nz/our-work/meeting-regulatory-impact-analysis-ria-requirements/ |
| TPP19-01 Guide to Better Regulation | NSW Government | Jan 2019 | https://www.productivity.nsw.gov.au/sites/default/files/2022-05/TPP19-01_Guide-to-Better-Regulation.pdf |
| 2024 Victorian Guide to Regulation | Better Regulation Victoria | Jun 2024 (files Dec 2025) | https://www.vic.gov.au/victorian-guide-to-regulation |
