# Industry lens (beta): methods

*6 November 2026 (DECISIONS E-122). Code: `alicia/src/alicia/register/competition.py` (the coding) and `alicia/src/alicia/menu/lens.py` (the page's data); template `menu/templates/industry-lens.html`; map `alicia/src/alicia/pipeline/boundaries.py`. Tests: `alicia/tests/test_lens.py`.*

## What the page shows

The user picks an ANZSIC class and a state or territory. The page lists:

- **Requirements** (`regulation-register/requirements/`) whose reach covers the class and that apply in the state: Commonwealth ones (unless limited to other states), the state's own, and its capital city council's, where recorded;
- **Register items** (`regulation-register/records/`) about the class, at the Commonwealth or in that state, except those repealed or replaced. Items about a division, subdivision or group reach every class in it; economy-wide items with no industries reach every class.

Each row is coded for three market positions, in the page's columns. A requirement that takes its coding from a register *setting* stands for that setting, so the setting is not listed twice. Rows with no coded effect are hidden unless the user asks for them.

## The three positions

| Column | Question | Register channels that act through it |
|---|---|---|
| Entrants into the market | Does it make starting up in this market easier or harder? | Barriers to entry or exit; number or types of businesses that can operate |
| Small and medium competitors | Does it change smaller businesses' ability or incentive to compete and grow, or customers' ability to switch to them? | Ability or incentives to compete; consumer choice and information |
| Monopoly and oligopoly players | Does it constrain or shelter the market power of the largest players? | Prices or market share; number or types of businesses that can operate (limits on who may operate shelter those already in) |

The channels are the register's five, which are the Office of Impact Analysis competition checklist's categories.

## How each row is coded

An effect is **positive** (more competition), **negative** (less), **mixed** or **unclear**. It describes the effect on competition only. A licence can protect consumers and still be a barrier to entry; the page does not weigh the two.

Three sources, in order of precedence:

1. **Assessed on the requirement.** A `competition` block written by hand on the requirement, with a reason for each position (format in [`regulation-register/requirements/README.md`](../regulation-register/requirements/README.md)).
2. **Assessed in the register.** A register item's direction becomes the effect (enhancing is positive, weakening negative, mixed is mixed, unclear is unclear). Its channels give the positions, as in the table above, and its direction rationale is the reason. A requirement that names a *setting* record (the same law in force, such as payroll tax or occupational licensing) takes that record's coding. Reform records are not used this way, because they assess a change, not the duty itself.
3. **Coded by rule.** Requirements without either are coded from their kind and triggers:

| Rule | Condition | Coding |
|---|---|---|
| Entry gate | A licence or approval needed before trading or before an activity, for listed industries | Entrants: negative, **strong** |
| Light entry gate | A registration, notification or insurance needed in the same way | Entrants: negative, **minor** |
| Size threshold | A threshold on turnover, payroll, revenue, employees or assets | Entrants: positive, minor (businesses below it are exempt). Small and medium: negative, minor (a step in cost when a business grows past it) |
| Tiny threshold | A money threshold under $50,000 | Not coded: it applies to practically every business that trades or employs |
| Large threshold | $50 million or more, or 200 employees or more | Entrants positive only: it is no step for small and medium businesses |
| Any business, any market | A requirement on every class, triggered by an activity (such as an environmental approval) | Not coded: it falls alike on firms in every market |
| Everything else | Duties every business or employer meets alike (employment standards, records, work health and safety) | Not coded |

The cut-offs ($50,000; $50 million or 200 employees) are judgement, chosen to separate thresholds that bite on almost everyone, on growing small and medium firms, and on the largest firms only. The 200-employee line matches the ABS's large-business band.

**Strength.** Register items and hand-coded effects are shown as strong unless coded otherwise; rule codings are strong only for licences and approvals. The page shows minor effects in a lighter tone.

## Limits

- **Coverage is thin and uneven.**
  - Laws on every business are recorded for every industry.
  - Industry-specific requirements exist only for the 19 calibration classes, plus a few families with wider reach.
  - Councils are the capital cities only.

  A blank cell or a short list means *not yet recorded*, not *no regulation*. The page says when no industry-specific requirement has been recorded for the chosen industry.
- **Drafts.** Every requirement, register item and coding is a draft drafted by AI-assisted desk research and not yet checked by a person.
- **The rules are crude.**
  - Every licence counts as a strong barrier, however easy it is to get.
  - Every size threshold counts as both an exemption and a step.
  - Fixed compliance costs, which weigh more on small firms, are not coded.

  Hand-coded assessments (source 1) are the way to refine them, one requirement at a time.
- **The channel mapping is mechanical.** A register item's one direction is applied to every position its channels reach. Where an item helps one group and hurts another, it should be coded `mixed` or given its own assessment.
- **The columns are market positions, not firm sizes.** "Monopoly and oligopoly players" means market power. Public data cannot show which firms in a class hold it (class-level concentration is not published; firm-level data such as BLADE are restricted).
- **Indirect effects.** Register items marked as affecting an industry indirectly are included by default; the page can hide them.

## Later features (owner, 6 November 2026)

To be built only when the owner asks:

- **A structural economic conditions chart for council areas and regions.**
- **Council-level features on the map.** `pipeline/boundaries.py` already reads the ABS's generalised council (LGA) boundaries, `build("LGA")`, so the map can gain council areas without a new data source.

## Adding to it

New requirements and register items appear on the page at the next site build, with no code change. The workflow is in [`regulation-register/requirements/README.md`](../regulation-register/requirements/README.md).
