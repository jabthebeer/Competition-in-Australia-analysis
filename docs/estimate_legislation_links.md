# Estimate for phases C to G, and the D5 choice

*Phase B wrap-up, 6 November 2026 (DECISIONS E-121). The numbers come from `alicia/scripts/legislation_estimate.py`, which writes [`estimate_legislation_links.csv`](estimate_legislation_links.csv) and [`estimate_legislation_links_cost.csv`](estimate_legislation_links_cost.csv). They were recalculated independently, with separate code, before publishing. They are ranges for planning, not forecasts.*

## What the calibration measured

Times are active session time between each batch's commits, with gaps of more than five minutes capped so the owner's absences don't count. They cover everything in the batch: research, fetching, debugging, writing the records and notes, checks and commits. The source is [`calibration_session_usage.csv`](calibration_session_usage.csv), taken from the session's own log.

| Batch | Requirements | Active minutes | Minutes a requirement | Output tokens a requirement |
|---|---|---|---|---|
| 1. Commonwealth, every business | 11 | 25.2 | 2.29 (includes building the register readers) | 10,328 |
| 2. States, every business | 24 | 31.4 | 1.31 (includes building the PDF, Word and RTF readers) | 8,383 |
| 3. Commonwealth, industry-specific | 20 | 21.7 | 1.09 | 5,342 |
| 4. States, industry-specific | 42 | 29.5 | 0.70 | 4,239 |
| 5. Capital-city councils | 20 | 16.5 | 0.83 | 4,343 |
| 4f. More state families (mostly drafted from ABLIS listings) | 42 | 23.9 | 0.57 | 1,398 |
| **Steady state (3 to 4f)** | **124** | **91.6** | **0.74** | **3,471** |

## Three gaps, measured in the wrap-up

The batches drafted requirements already known to exist, for the 19 calibration classes only. Three steps of the full method were not measured, so the wrap-up tested each with a small sample.

**Screening a register.**
- **Sample:** 100 laws drawn at random from the corpus after a title triage, 50 Commonwealth and 50 from the five states the corpus covers (NSW, Qld, WA, SA, Tas). The triage drops amending Acts, appropriations, airworthiness directives, tariff concession orders, appointments and similar series.
- **How:** each law was judged from its title, long title and obligation wording, in about one second a law.
- **Results:** in [`screening_sample.csv`](../data/processed/legislation/screening_sample.csv), with the call and reason for each law. The calls are Y (creates a requirement), L (only supports an existing one), P (a planning instrument, for phase E) or N (no obligation on businesses).

| Sample | Laws | Y | Requirements per Y law | L | P |
|---|---|---|---|---|---|
| Commonwealth Acts | 25 | 12% (95% interval 4–30%) | 1.7 | 4% | 0% |
| Commonwealth instruments | 25 | 8% (2–25%) | 1.0 | 24% | 0% |
| State Acts | 25 | 20% (9–39%) | 2.0 | 0% | 0% |
| State instruments | 25 | 12% (4–30%) | 1.0 | 36% | 12% |

**Full reach.** Four families were coded across all 506 classes, from a keyword shortlist of ABS class names, definitions and primary activities ([`reach_test.csv`](../data/processed/legislation/reach_test.csv); a first pass, not yet coded as records). The results:

| Family | Classes reached |
|---|---|
| Liquor licensing | 17 |
| Security licensing | 4 |
| Food business registration | 47 |
| Working with children checks | 30 |

That is about 15 seconds a family. These four average about 25 classes, against 1.2 per industry-specific requirement in the calibration, which coded only the calibration classes. So for broad families like these, the link table will grow about twentyfold.

**What ABLIS's 30,663 services are.** A random sample of 60 public service pages ([`ablis_sample.csv`](../data/processed/legislation/ablis_sample.csv); fields only, no ABLIS text) found:
- 57 licences, 2 codes of practice and 1 advisory listing;
- 50 administered by a council (83%, 72–91%), of which 17 name a council local law (28%, 19–41%);
- every page names an Act.

So most of ABLIS is the same kind of council permit, issued under a state Act and repeated for each council. Under methods rule 7, each such permit becomes one state requirement, not 540. True council requirements, under a local law, come to about 16 a council.

## Scale

| | Central | Range |
|---|---|---|
| Laws to screen, Commonwealth | 10,773 | |
| Laws to screen, states (8/5 of the five corpus states) | 10,874 | |
| Requirements, phase C (Commonwealth) | 1,017 | 300–3,012 |
| Requirements, phase D (states) | 3,021 | 1,284–6,218 |
| Requirements, phase E (21 sample councils, D4) | 337 | 220–485 |
| **Requirements, C to E** | **4,375** | **1,805–9,716** |
| Further local-law requirements if every council is covered (needs the ABLIS key; not in the totals) | 8,688 | 5,675–12,501 |

**Cross-checks.** ABLIS lists 775 Australian Government services, against about 1,000 Commonwealth requirements here; ours also include standards and duties that ABLIS doesn't list as services. About 15% of ABLIS's pages are state-administered (about 4,600), against about 3,000 state requirements here; ABLIS also lists services for individuals.

## Time, in session

| Phase | Central hours | Range |
|---|---|---|
| C. Commonwealth | 28.5 | 11.5–127.2 |
| D. States and territories | 55.9 | 22.8–189.1 |
| E. Councils (planning terms; 21 sample councils) | 14.7 | 4.9–30.8 |
| F. Completeness check (waits for the ABLIS key) | 13.5 | 6.8–20.2 |
| G. Assemble and check | 6.7 | 3.3–10.0 |
| **Total** | **119.3** | **49.3–377.3** |

About 66 of the 119 central hours come from measured rates. The other 53 rest on assumed rates: building the catalogues, attaching supporting instruments, planning terms, and phases F and G. The CSV marks each component `measured` or `assumed`. At today's pace (about 4 active hours across the day), 119 hours would take about 30 working days.

## D5: keep the bulk work in session, or use the Claude API?

| | In session | Claude API, batch runs |
|---|---|---|
| **Extra cost** | None beyond the owner's plan, but the work counts against its usage limits. At this session's rate the remaining work would re-read about 7 billion tokens of context | Drafting about 4,400 requirements: $220–440 if code finds the provisions and one call drafts each (Batch API); $1,100–2,200 for a multi-step agent. Screening every law: $8–325. For drafting, the low end is the Sonnet family and the high end Opus; for screening, Haiku to Opus. Allow about 30% more for retries and a pilot |
| **Session time** | About 120 hours (49–377) | About 40 hours (catalogues, planning terms, phases F and G, reviewing the pilot), plus building the pipeline (assumed 6–10 hours) |
| **Elapsed time** | About 30 working days at today's pace | Most batches return within an hour, all within 24 hours; days rather than weeks |
| **Quality** | Judgement with the full methods and context; every quote re-found in its source | The same validation and quote check apply. Reach judgement depends on the prompt, so a pilot comparison is needed |
| **Needs** | Nothing new | An Anthropic API key, saved as a secret on this environment through the secure form (never pasted in chat), and a pipeline |

Prices are the current Opus, Sonnet and Haiku models' per-token prices on the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) (read 6 November 2026), with the Batch API's 50% discount where batch runs are assumed. Token use per call is assumed (see the script), not measured.

**Recommendation.**
1. Run phase C in session. The Commonwealth comes to about 1,000 requirements and about 29 hours, and it settles the patterns: full reach, attaching supporting instruments, the screening record.
2. In parallel, pilot the API on about 100 requirements from one state whose register serves plain text, for example Queensland. The pilot would cost about $5–50.
3. Compare the pilot with in-session drafts of the same laws.
4. Decide how to run phase D (about 3,000 requirements, about 56 hours in session) on the pilot's error rate and real cost.

Either way, run each batch in a fresh session with a short brief. This long session re-read about 1.6 million tokens of context per requirement.

## Limits

- **Small samples.** Each sample stratum has 25 laws, hence the wide intervals; requirement counts could be half or double the central case.
- **The corpus.** It is as at March 2025 and covers five states. Victoria, the ACT and the NT are assumed to have the five-state average number of laws, though the ACT and NT statute books are smaller and Victoria's larger.
- **The screening calls.** I made them in about a second a law, and two are flagged as needing a check. A full screen meets more borderline laws, so the high case allows five seconds a law.
- **The calibration rate.** The batches drafted requirements already known to exist. A full sweep meets harder laws, so the high case uses batch 2's first-of-its-kind rate.
- **What the hours cover.** They are AI session time only. The owner's review and spot-checks are not included.
- **ABLIS beyond the sample councils.** The public site is not for bulk reading. Covering every council needs the API key.
