# Costing cards

One file per requirement, or per family of requirements, whose compliance cost comes from a source rather than from
the hours assumed for its kind (`../compliance-cost-assumptions.json`). DECISIONS E-701 and E-702; method in
`docs/compliance_costs.md`. `alicia/scripts/compliance_costs.py` reads every card here.

| Field | Meaning |
|---|---|
| `applies_to` | `{"requirement": "<id>"}`, or `{"family": "<family>"}` for every requirement of a family that has no card of its own |
| `evidence` | `sourced` (the law's own impact analysis or a regulator's figure) or `analogue` (a similar regime's) |
| `task` | What a business does, in plain words |
| `basis` | What was taken from the source and what was assumed |
| `source_cost` | A source in dollars: `cost_a_year` for `entities` entities, in `price_year` prices, `indexed` (true once indexed to today), `start_share` (the share of the cost paid once, when a business starts; 0 when the source averages upfront costs in), `range` (low and high as multiples of the central figure) |
| `start_hours`, `yearly_hours` | A source in hours, `{"low", "central", "high"}`, in place of `source_cost` |
| `entities` | Optional: the entities bound, from a regulator, in place of the ABS counts. `groups` of `{"name", "count", "classes", "states"?}`; `states` limits a group to some jurisdictions (for family cards) |
| `sources` | Each source's `title`, `publisher`, `url`, `locator`, `quote` and `accessed` date |
| `review` | `draft` until a person checks the card |

Dollars become hours at the work rate ($91.54, from the burden calculator), so that each requirement's working reads
the same way on the site.
