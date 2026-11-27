# Phase 4: counting each rule once, and giving it a regime

*17 November 2026. Draft by Claude Code on the legislation branch, for the owner to check. Phase 4 of the [re-evaluation plan](plan_levers_reevaluation.md) (DECISIONS E-177). The pairs are in [`levers_pairs.csv`](levers_pairs.csv). Regimes are in `regulation-register/regimes/`, and their purposes in `regime-purposes.json`. Drafted by AI-assisted desk research; not yet checked by a person.*

## Summary

| Task | Result |
|---|---|
| Candidate pairs (a requirement that cites an item's Act without naming the item) | 34 checked. None nested; 9 are rules and their changes, staged for the dedicated field |
| Register items without a regime | All 19 now have one: 5 new regimes, and 2 items added to existing ones |
| Requirements shown as their own rows, without a regime | 74 of 84 now have one: 10 in the regimes above (land tax and company reports), 64 in 8 more new regimes. 10 one-off rules are left. 15 requirements inside items also took their item's regime |
| Phase 2 staging | 9 changes now link to a rule the states batches have since drafted |

## 1. Pairs

The plan named 29 candidates; the states batches have since added more, so 34 were checked. Each verdict is in [`levers_pairs.csv`](levers_pairs.csv).

| Verdict | Count | What happens |
|---|---|---|
| A rule and its change | 9 | Not nested. The item is a reform, and the requirement is the standing rule it made or changed. Nesting would hide the rule inside a change, which the impact classes leave out. Each is staged as a rule–change link for the dedicated field (phase 2) |
| Part of an occupational licensing setting | 11 | Builder, plumbing, certifier and engineer licences under each state's occupational licensing item. Nesting them was proposed to the website session (DECISIONS E-171), because the levers page groups the 8 builder licences across states |
| Not the same rule | 14 | They share an Act, for example practitioner registration and pharmacy ownership, or therapeutic goods listing and the vaping item |

**Still counted twice:**

- **Coastal trading.** Both the 2012 reform and the licence it made are ranked as rules until the dedicated field arrives. The reform then becomes the licence's change.
- **Occupational licensing.** The occupational licensing items and the builder licences inside them are both ranked, until the website session decides on the proposal.

## 2. Regimes for the 19 register items

| Regime | New? | Items | Requirements also placed | Purpose |
|---|---|---|---|---|
| Transfer and insurance duty (`state-duties`) | New | The 7 residential transfer duty items and the 7 insurance duty items | 6 transfer duty, 6 insurance duty | Revenue and registration |
| Foreign investment screening (`foreign-investment`) | New | `cth-foreign-investment-screening` | Foreign investment notification | National interest and security (a new purpose) |
| Company reporting and disclosure (`company-reporting`) | New | `cth-sustainability-reporting-2025` | Sustainability reports, modern slavery statements, payment times reports, CATSI reports | Financial stability |
| Postal services (`postal-services`) | New | `cth-australia-post-reserved-services` | Australia Post's reserved services (moved from telecommunications and media, which does not cover postal industries) | Consumer protection |
| Land tax (`land-tax`) | New | None | 7 land tax requirements | Revenue and registration |
| Employment law | Existing | `cth-non-compete-clause-prevalence` | None | Workers' pay and conditions |
| Maritime and ports | Existing | `vic-port-of-melbourne-lease-2016` | None | Health and safety |

## 3. Regimes for the other requirements

84 requirements shown as their own rows had no regime, most from the states and Commonwealth batches. Section 2 placed 10 (7 land tax, 3 company reports); 64 more are now in 8 new regimes.

| Regime | Requirements | Coverage | Purpose |
|---|---|---|---|
| Driving instruction | 8 driving instructor licences | Class 8219 | Health and safety |
| Portable long service leave | 8 construction schemes, 4 cleaning or security schemes | Construction; classes 7311 and 7712 | Workers' pay and conditions |
| Retail leases | 8 retail lease disclosure duties | Class 6712 | Fair dealing between businesses |
| Council permits for public spaces | 20 busking, filming and outdoor dining permits in 7 councils | 8 classes | Land use and amenity |
| Firearms and weapons | 3 dealer licences and permits, 4 paintball venue permits | 2 classes | Health and safety |
| Radiation and nuclear safety | 4 state radiation licences, the Commonwealth nuclear material permit | Every industry | Health and safety |
| Privacy | The Australian Privacy Principles, and their extension to every health service provider | Every industry | Consumer protection |
| Critical infrastructure and cyber security | The critical infrastructure risk program, ransomware payment reports | Every industry | National interest and security |

**Left without a regime (10):** one-off rules that fit no regime yet: the ABS information directions, Australian Industry Participation plans, cultural heritage export permits, defence trade controls permits, gene technology licences, migration agent registration, resale royalty, space launch facility licences, transport safety reporting and NSW scrap metal dealer registration. Each can join a regime when one is added for its area.

## Method

- **Basis.** Each new regime's basis reuses the quotes on its members, which the repository's quote checker has already found word for word in their sources. A web page with no year in its title takes the year it was read.
- **Coverage.** The union of the members' reach: every industry if any member reaches every industry (less government, defence and households, as for payroll tax), otherwise the classes they name.
- **Layers.** Who sets the rules, licenses, approves, inspects or collects, with the bodies the members record. No layer has been checked against an administrative arrangements order.
- **Consistency.** Each state and territory has its own law for the state regimes; the Commonwealth regimes are Commonwealth only.
- **Issues.** None recorded: no review has yet been searched for problems in these regimes.

## Limits

- **Regime boundaries are judgements.** Company reporting groups four reports with different purposes (investors, human rights, payment times, Indigenous corporations); its one purpose, financial stability, fits the first best.
- **Counts on other pages change.** The Industry lens and the regulatory overview now count 74 regimes, not 61, so an industry's count of regimes rises where the new ones reach it.
- **A new purpose.** "National interest and security" is added for foreign investment and critical infrastructure. The other 8 purposes did not fit them.
