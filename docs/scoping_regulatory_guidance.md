# Scoping: unclear or overlapping regulatory guidance in the legislation menu

*29 October 2026. Scoping only: nothing has been built. Owner request: "scope out the possibility of including unclear
or overlapping regulatory guidance into this menu … workshop a process and do some research". Drafted by Claude Code
for the owner and Cowork. Quotes were checked against the downloaded text unless marked "search results".*

## 1. The question

The menu records laws, settings and barriers, and (since E-96) problems in the regimes they belong to. Much of what
businesses experience as burden comes from guidance instead: regulator guides, codes of practice, interpretive
statements and the way inspectors apply them. The question is whether, and how, to record guidance that is unclear,
inconsistent or overlapping, and to mark it against the framework.

**The evidence that it matters is strong and Australian:**

- **Productivity Commission, *Regulator Engagement with Small Business* (2013):**
  - "How small businesses 'experience' regulation has as much to do with the engagement approaches of regulators as it does with the regulations." (Overview, key points)
  - "Unnecessary burdens can be created by a regulator's engagement approach through, for example, inconsistent advice, excessive reporting requirements or unnecessary delays in processing licences and permits." (Ch. 1, key points, p. 27)
  - Businesses cited "lack of guidance or inconsistent advice about what constitutes adequate compliance". (Ch. 1, p. 37)
- **Productivity Commission, *Creating a more dynamic and resilient economy* (2025):**
  - Participants named "regulatory fragmentation and overlap, including where multiple regulators have overlapping responsibilities, and jurisdictional differences in regulatory approaches". (Appendix C, p. 168)
  - The Commission lists "cumulative burden of multiple overlapping or conflicting regulations" among the most common and impactful burdens. (Box 2.1, p. 36)
- **Productivity Commission, *The Role of Local Government as Regulator* (2012):** recorded "inconsistent processes within and across councils, including differences in interpretation of similar requirements". (Box 6.1, p. 214)

## 2. What counts as a guidance problem: a typology

| Type | What it looks like | Australian example in the sources |
|---|---|---|
| **Unclear** | Guidance is vague or missing, so businesses cannot tell what compliance requires | Privacy: "It is possible that businesses would benefit from further regulatory guidance or legal precedent to help them understand their regulatory obligations" (PC 2025, *Harnessing data and digital technology*, p. 73) |
| **Inconsistent interpretation** | Inspectors, councils or offices read the same rule differently | Food safety: "inconsistent interpretation and implementation of food laws by environmental health and similarly authorised officers" (PC 2009 food safety benchmarking, ch. 7; already a menu issue) |
| **Overlapping or conflicting** | Two or more regulators issue guidance on the same obligation, or tiers' guidance differs | WHS: a model code has legal effect only once each jurisdiction approves it, and Victoria uses its own compliance codes (Safe Work Australia, search results; Victoria's separate OHS law is item `vic-ohs-not-harmonised`) |
| **De facto rules** | Guidance framed as advice but enforced as if it were law | Council design guidelines: "builders require permits. This means satisfying local governments by complying with regulations, regardless of how they are framed" (PC 2025, *Housing construction productivity*, p. 52) |
| **Churn** | Guidance changes often or without notice | EPBC assessments: "complex and duplicative requests for additional information and shifting requirements" (PC 2025, *net zero* inquiry, Box 2.4; already a menu issue) |

**Good guidance should be recorded too, not only bad guidance.** Binding rulings, safe harbours and single points of
advice reduce burden and uncertainty, and should be marked up just as poor guidance is marked down. The UK's Primary
Authority scheme is an example (see section 6).

## 3. What the menu does today

- **Tags.** The regimes (`regulation-register/regimes/`) already have a "Vague or inconsistent guidance" tag
  (`unclear-guidance`). Only 3 of the 55 issues use it, because the Phase 2 sources were mostly about laws, not
  regulator practice.
- **No guidance records.** Nothing records the guidance documents themselves (who issues what, on which obligation).
- **No way to show overlap.** Nothing shows where several bodies guide on the same thing.

## 4. Options for the menu

| Option | What it adds | For | Against |
|---|---|---|---|
| **A. Issues on regimes** (extend Phase 2) | More `unclear-guidance` issues, plus new tags: `overlapping-guidance`, `guidance-as-rule`, `guidance-churn`, and a positive tag such as `assured-advice` | No schema change; shows in the existing tags, filter and regime cards | Stays at regime level; no per-document detail |
| **B. Guidance as register items** (a new kind, `guidance`, next to reform, setting and barrier) | A record per significant guidance instrument (e.g. a code of practice, a regulatory guide), assessed with the framework and grouped like other families | Lets important guidance be marked, filtered and recommended on, like laws | Needs evidence of effect for each; risk of many low-value records |
| **C. Guidance layer in regimes** | For each regime, the bodies that issue guidance at each tier, added to the Venn diagram as a seventh job ("guides") | Makes overlap visible: two tiers both guiding on the same obligation shows in the overlap | Needs a careful map of who guides on what; another job in the diagram |
| **D. Indicators** | Per regime or industry: count of guidance documents, length, readability, update frequency, number of bodies guiding | Reproducible and comparable | Volume is not burden; needs scraping where licences allow; only some libraries are reachable |

**Recommendation: A and C first, B only for a few high-impact cases, D as an experiment on one or two regimes.**
- A and C reuse what exists and keep the "quote every claim" standard.
- B should wait until A shows which guidance matters most.
- D is useful as a cross-check, not as a measure of burden.

## 5. Proposed process (to workshop)

1. **Agree scope and tags** (owner).
   - Confirm the typology in section 2 and the new tags, including a positive one.
   - Decide whether guidance can be marked up as well as down. Recommendation: yes.
2. **Choose pilot regimes** (owner, with Claude Code). Four candidates, each with known evidence:
   - work health and safety (model codes against Victorian codes; codes approved differently by jurisdiction);
   - food safety (inspector interpretation);
   - planning and building (council guidelines enforced as rules);
   - privacy (missing guidance).
3. **Map the guidance** (Claude Code).
   - For each pilot regime, list the guidance instruments and their issuers by tier, with links.
   - Note which are registered law (codes approved by notice) and which are informal.
   - Record the result as a guidance layer (option C).
4. **Gather evidence of problems** (Claude Code, Cowork for synthesis). Sources, in order of weight:
   - reviews and inquiries (Productivity Commission, ANAO, state productivity and better-regulation commissions);
   - ombudsman and small business commissioner reports;
   - parliamentary committee reports;
   - courts and tribunals, where guidance was found inconsistent with the law;
   - regulators' own consultation summaries.

   Every issue quotes its source, as in Phase 2.
5. **Mark against the framework** (Claude Code drafts, owner reviews).
   - Mark only the incremental effect of the guidance, not the law it explains, to avoid double counting.
   - Most effects go under regulatory burden. Use capital deepening where uncertainty deters investment, and innovation where guidance locks in one technology.
6. **Show it on the menu** (Claude Code).
   - Add the new tags to the complexity filter, and the guidance layer to the regime diagram.
   - Add a "Guidance" fold in each item's panel listing the guidance on its regime and any issues.
7. **Review** (owner and Cowork).
   - Use a review sheet like the existing ones.
   - All entries stay drafts until a person has checked them.

## 6. International precedents

- **UK Regulators' Code and Primary Authority.**
  - The Code requires regulators to make clear guidance available.
  - Primary Authority (since 2009) gives a business trading across council boundaries one council whose "assured advice" other councils must respect, aimed at inconsistent interpretation between councils.
  - Its evaluation is weak: a government peer review noted it relied on self-reported data (search results).
  - It is a model for the food safety and council issues already in the menu.
- **United States: OMB *Final Bulletin for Agency Good Guidance Practices* (2007).** Agencies had to:
  - list their significant guidance documents online;
  - accept comments;
  - put economically significant guidance out for public comment (search results; whether it is still in force was not checked).

  It suggests a "significant guidance" register as a benchmark for Australian regulators.
- **OECD Best Practice Principles for Regulatory Enforcement and Inspections (2014).**
  - Calls for compliance to be promoted "through the use of appropriate instruments such as guidance, toolkits and checklists".
  - Calls for inspectors to be "trained and managed to ensure professionalism, integrity, consistency and transparency" (search results).
  - The OECD toolkit turns these into a 12-point checklist that could rate regulators.
- **Australia's own frameworks.**
  - The Office of Impact Analysis treats quasi-regulation, "a rule not in legislation but expected to change behaviour", as within scope for impact analysis (OIA checklist, search results).
  - The Regulator Performance Guide (2021) sets principles that Commonwealth regulators report against in corporate plans and annual reports (search results).
  - Both could anchor the "de facto rules" and "regulator practice" tags.

## 7. Data: what is reachable from this environment

| Source | Content | Reachable here | Notes |
|---|---|---|---|
| Federal Register of Legislation API | Codes and guidelines made as legislative or notifiable instruments | Yes | 34 in-force titles containing "Code of Practice" (mostly Commonwealth WHS codes) and 111 containing "Guidelines" (search of 29 Oct 2026); informal guidance is not registered |
| FSANZ, *Safe Food Australia* and standard guides | National food safety guidance | Yes | |
| OAIC privacy guidance; ASIC regulatory guides | Large national guidance libraries | Pages load, but lists are built by script or search | Listing needs their search interfaces; check licence terms before bulk download |
| Safe Work Australia model codes; ATO, ACCC, Fair Work | Model codes; rulings and guidance | No (blocked or refused) | Would need manual collection or a different environment |
| State WHS regulators | Codes approved in each state | Mixed (Victoria redirects; Queensland refuses) | Code-by-code approval status needs each regulator's site |
| Downloaded library | PC 2013 small business report (new), plus PC benchmarking and 2025 inquiries already used | Yes | The PC 2013 report's survey of regulators (appendix B) is a precedent for collecting comparable data |

## 8. Limits and risks

- **Volume is not burden.** Long, detailed guidance can reduce uncertainty. Indicators need judgement and evidence beside them.
- **Evidence is uneven.** Much of it is business submissions, which are claims, not findings, so confidence will often be low.
- **Selection bias.** Pilots chosen because problems are known will overstate how common problems are.
- **Licensing and access.** Several libraries refuse automated access, and bulk reuse may be restricted.
- **Moving target.** Guidance changes often, so each entry should carry the date it was checked.

## 9. Decisions for the owner

1. **Approach:** options A and C, with B for high-impact cases only?
2. **Tags:** new tags, including a positive one for good guidance?
3. **Pilots:** WHS, food safety, planning and building, and privacy?
4. **Indicators:** try them (option D) on one regime, or defer?

## Sources

- Productivity Commission (2013), *Regulator Engagement with Small Business*, research report: <https://assets.pc.gov.au/inquiries/completed/small-business/report/small-business.pdf>
- Productivity Commission (2025), *Creating a more dynamic and resilient economy*: <https://assets.pc.gov.au/2025-12/resilient-economy.pdf>
- Productivity Commission (2025), *Harnessing data and digital technology*: <https://assets.pc.gov.au/2025-12/data-digital.pdf>
- Productivity Commission (2025), *Housing construction productivity: Can we fix it?*: <https://assets.pc.gov.au/research/completed/housing-construction/housing-construction.pdf>
- Productivity Commission (2025), *Investing in cheaper, cleaner energy and the net zero transformation*: <https://assets.pc.gov.au/2025-12/net-zero.pdf>
- Productivity Commission (2012), *The Role of Local Government as Regulator*: <https://assets.pc.gov.au/inquiries/completed/regulation-benchmarking-local-government/report/local-government-volume1.pdf>
- Productivity Commission (2009), *Performance Benchmarking of Australian and New Zealand Business Regulation: Food Safety*: <https://assets.pc.gov.au/inquiries/completed/regulation-benchmarking-food-safety/report/food-safety-report.pdf>
- Safe Work Australia, model WHS laws and codes (search results): <https://www.safeworkaustralia.gov.au/law-and-regulation/legislation>
- Office of Impact Analysis, impact analysis framework and checklist (search results): <https://oia.pmc.gov.au/resources/australian-government-impact-analysis-framework/step-1-preliminary-analysis>
- Department of Finance, Regulator Performance (RMG 128) (search results): <https://finance.gov.au/government/managing-commonwealth-resources/regulator-performance-rmg-128>
- UK Government, Primary Authority guidance and 2015 evaluation peer review (search results): <https://www.gov.uk/guidance/local-regulation-primary-authority>, <https://assets.publishing.service.gov.uk/media/5a82c7d0e5274a2e87dc2f29/2015-pa-evaluation-summary-and-peer-review.pdf>
- US Office of Management and Budget (2007), *Final Bulletin for Agency Good Guidance Practices* (search results): <https://www.whitehouse.gov/wp-content/uploads/legacy_drupal_files/omb/federal_register/FR2007/012507_good_guidance.pdf>
- OECD (2014), *Regulatory Enforcement and Inspections*, OECD Best Practice Principles for Regulatory Policy (search results): <https://doi.org/10.1787/9789264208117-en>
