import { useMemo } from "react";
import { rbeTable, type OptionResult } from "../../engine/index";
import { OIA_CATEGORIES, costBrief, divisionOf, evidenceGate, type OiaCategory } from "../../productivity/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import { useCostingContext, useRegister } from "../costingContext";
import { categoryReasons, cohortBurden, regulationBarrier, shareAffected, smallToLarge, type CohortBurden } from "../competition";
import { Checkbox, Help, TextField } from "../components/fields";
import { useRanges } from "../components/ProductivityResults";
import { isUntouched } from "../example";
import { fmtNum, moneyText } from "../format";
import { gdpPct, millions, range } from "../productivityFormat";

const CATEGORY_LABELS: Record<OiaCategory, string> = {
  barriers: "Barriers to entry, growth or exit",
  "number-or-type": "Number or types of businesses that can operate",
  "ability-incentive": "Ability or incentives to compete",
  "prices-market-share": "Conditions that influence prices or market share",
  "consumer-choice": "Choices, information, goods or services available to consumers",
};

const SIZE_LABELS = { small: "Small (under 20)", medium: "Medium (20–199)", large: "Large (200 or more)", unknown: "All sizes, or not given" } as const;

const share = (x: number | undefined, dp = 2) => (x === undefined ? "—" : `${(x * 100).toFixed(dp)}%`);

export function CompetitionPage(props: PageProps) {
  const { proposal, computed, draft, updateDraft, brief, go } = props;
  const loaded = useCostingContext();
  const register = useRegister();
  const ctx = loaded.status === "ready" ? loaded.ctx : null;
  const records = register.status === "ready" ? register.register.records : [];
  const reasons = useMemo(() => categoryReasons(draft, records), [draft, records]);
  const answers = draft.competition?.categories ?? {};
  const setCompetition = (patch: NonNullable<typeof draft.competition>) => updateDraft((d) => ({ ...d, competition: { ...d.competition, ...patch } }));
  const options = computed.ok && !isUntouched(proposal) ? computed.result.options.filter((o) => !o.isStatusQuo) : [];
  const ticked = OIA_CATEGORIES.filter((c) => answers[c] ?? reasons.has(c));
  const divisions = [...new Set(draft.scope.industries.map((i) => divisionOf(i.anzsic)).filter((d): d is NonNullable<typeof d> => !!d))];
  const central = useMemo(() => (brief.ok && ctx ? costBrief(brief.brief, ctx) : null), [brief, ctx]);
  const { ranges } = useRanges(brief.ok ? brief.brief : null, ctx);
  const c5 = central?.channels.find((c) => c.channel === "C5");

  return (
    <>
      <PageHeading>Step 6: Competition screen</PageHeading>
      <p>
        The Office of Impact Analysis asks three questions of a regulatory proposal: does it impact competition; are there less restrictive ways to meet the objective; and do the benefits outweigh the costs. This page gathers what the tool can say about each. The answers are yours.
      </p>

      <section aria-labelledby="step1-heading" data-testid="competition-step1">
        <h2 id="step1-heading">1. Does it impact competition?</h2>
        <p>Tick each category the proposal could affect. The tool suggests categories from your levers and from similar past changes; your ticks replace its suggestions.</p>
        {OIA_CATEGORIES.map((c) => {
          const why = reasons.get(c) ?? [];
          return (
            <div key={c} className="category">
              <Checkbox
                label={CATEGORY_LABELS[c]}
                checked={answers[c] ?? why.length > 0}
                onChange={(on) => setCompetition({ categories: { ...answers, [c]: on } })}
                testId={`category-${c}`}
                help={
                  why.length > 0
                    ? `${answers[c] === false ? "You have unticked this suggestion. " : "Suggested: "}${[...new Set(why)].slice(0, 3).join("; ")}.`
                    : answers[c]
                      ? "Ticked by you."
                      : undefined
                }
              />
            </div>
          );
        })}
        <p data-testid="competition-verdict">
          {ticked.length === 0
            ? "On these answers the proposal does not appear to affect competition. Record why in the Impact Analysis."
            : `On these answers the proposal may affect competition in ${ticked.length} of the five categories: assess it further (Steps 2 and 3).`}
        </p>

        <h3>Who bears the compliance cost</h3>
        {options.length === 0 && <p>No burden costing yet: add obligations on the burden pages to compare costs by business size.</p>}
        {ctx &&
          options.map((o) => {
            const rows = cohortBurden(o, proposal, ctx);
            return <CohortTable key={o.optionId} option={o} rows={rows} ratio={smallToLarge(rows)} year={ctx.industryByBandYear} />;
          })}
        {ctx &&
          (() => {
            const s = shareAffected(proposal, draft, ctx);
            return s ? (
              <p data-testid="share-affected">
                The burden proposal counts {fmtNum(s.affected)} businesses: {share(s.affected / s.inScope, 1)} of the {fmtNum(s.inScope)} businesses in the scope industries (CABEE, {ctx.sizeYear}).
              </p>
            ) : null;
          })()}
        {c5 && c5.other.length > 0 && (
          <div data-testid="threshold-screen">
            <h3>Businesses near a size threshold</h3>
            <ul>
              {c5.other.map((x, i) => (
                <li key={i}>
                  {x.label}: <strong>{fmtNum(Math.round(x.value * 100) / 100)}</strong> {x.unit}
                </li>
              ))}
            </ul>
          </div>
        )}
        {loaded.status === "ready" && (
          <>
            <h3>How often businesses report regulation as a barrier</h3>
            <Help>
              Share of businesses reporting "government regulations and/or compliance" as a barrier to their activities or performance, ABS Business Characteristics Survey 2024-25. A measured incidence, not an assumed one: compliance cost does not always fall hardest on the smallest firms.
            </Help>
            <div className="table-wrap">
              <table data-testid="bcs-barrier">
                <caption className="visually-hidden">Businesses reporting regulation as a barrier</caption>
                <thead>
                  <tr>
                    <th scope="col">Businesses</th>
                    <th scope="col" className="num">Report regulation as a barrier</th>
                  </tr>
                </thead>
                <tbody>
                  {regulationBarrier(loaded.parameters, divisions).map((r) => (
                    <tr key={r.label}>
                      <th scope="row">{r.label}</th>
                      <td className="num">{r.pct.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section aria-labelledby="step2-heading" data-testid="competition-step2">
        <h2 id="step2-heading">2. Are there less restrictive alternatives?</h2>
        <p>The burden proposal's options side by side, on the same measures. Add an option on the Proposal page to compare another way of meeting the objective.</p>
        {ctx && options.length > 0 && (
          <div className="table-wrap">
            <table data-testid="competition-options">
              <caption className="visually-hidden">Options compared on competition measures</caption>
              <thead>
                <tr>
                  <th scope="col">Option</th>
                  <th scope="col" className="num">RBE, business ($m a year)</th>
                  <th scope="col" className="num">Small-to-large cost ratio</th>
                  <th scope="col">Threshold cliffs</th>
                </tr>
              </thead>
              <tbody>
                {options.map((o) => {
                  const rows = cohortBurden(o, proposal, ctx);
                  const ratio = smallToLarge(rows);
                  return (
                    <tr key={o.optionId}>
                      <th scope="row">{o.optionName}</th>
                      <td className="num">{rbeTable(o.rbe, 1).cells[1]}</td>
                      <td className="num">{ratio === undefined ? "—" : `${ratio.toFixed(2)}×`}</td>
                      <td>{rows.some((r) => r.cliff) ? "Yes" : "None found"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <TextField
          label="Alternatives considered and why they were not preferred"
          multiline
          value={draft.competition?.alternatives ?? ""}
          onChange={(v) => setCompetition({ alternatives: v || undefined })}
          testId="competition-alternatives"
        />
      </section>

      <section aria-labelledby="step3-heading" data-testid="competition-step3">
        <h2 id="step3-heading">3. Do the benefits outweigh the costs?</h2>
        <p>The costs and gains the tool can quantify, beside each other. Benefits the regulation protects (safety, consumer protection) are outside both; record them below.</p>
        <ul>
          {options.map((o) => (
            <li key={o.optionId}>
              Regulatory burden, {o.optionName}: <strong>{moneyText(o.rbe.total)}</strong> a year (the RBE; a negative figure is a saving).
            </li>
          ))}
          {central && ranges && ctx && brief.ok && (
            <ProductivityLine central={central} ranges={ranges} gate={evidenceGate(brief.brief, central, ranges, brief.warnings)} />
          )}
          {central && !ranges && <li>Productivity: working out the ranges…</li>}
          {!brief.ok && <li>Productivity: the levers need fixing before they can be costed (see the Productivity levers page).</li>}
        </ul>
        <TextField
          label="Benefits not quantified here"
          multiline
          help="For example, safety, health or consumer protection the regulation provides, and who receives them."
          value={draft.competition?.benefits ?? ""}
          onChange={(v) => setCompetition({ benefits: v || undefined })}
          testId="competition-benefits"
        />
      </section>

      <NextStep go={go} to="results">
        Next: results
      </NextStep>
    </>
  );
}

function ProductivityLine({ central, ranges, gate }: { central: ReturnType<typeof costBrief>; ranges: NonNullable<ReturnType<typeof useRanges>["ranges"]>; gate: ReturnType<typeof evidenceGate> }) {
  if (!gate.showGdp) return <li data-testid="competition-gdp">Productivity: the GDP effect is hidden by the evidence gate (see Results); the direct effects by industry are on the Productivity levers page.</li>;
  return (
    <li data-testid="competition-gdp">
      Productivity: long-run change in real GDP <strong>{gdpPct(central.gdpPct)}</strong> (10–90% range {range(ranges.gdpPct, gdpPct)}), about {millions(central.gdpDollars)} a year
      {gate.status === "indicative" ? ", indicative" : ""}.{central.welfareDollars !== 0 && ` Efficiency cost of the funding: ${millions(central.welfareDollars / 1e6)} a year.`}
    </li>
  );
}

function CohortTable({ option, rows, ratio, year }: { option: OptionResult; rows: CohortBurden[]; ratio: number | undefined; year: string }) {
  return (
    <div data-testid={`cohort-${option.optionId}`}>
      <div className="table-wrap">
        <table>
          <caption>
            {option.optionName}: compliance cost per business against average revenue for businesses that size in the same division (Australian Industry, {year})
          </caption>
          <thead>
            <tr>
              <th scope="col">Group</th>
              <th scope="col">Size</th>
              <th scope="col" className="num">Cost a year, each</th>
              <th scope="col" className="num">Change a year, each</th>
              <th scope="col" className="num">Average revenue</th>
              <th scope="col" className="num">Cost ÷ revenue</th>
              <th scope="col" className="num">Change ÷ revenue</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.populationId}>
                <th scope="row">
                  {r.label}
                  {r.cliff ? " (threshold cliff)" : ""}
                </th>
                <td>{SIZE_LABELS[r.size]}</td>
                <td className="num">${fmtNum(Math.round(r.costPerEntity))}</td>
                <td className="num">{r.changePerEntity < 0 ? "−" : ""}${fmtNum(Math.abs(Math.round(r.changePerEntity)))}</td>
                <td className="num">{r.revenue === undefined ? "—" : `$${fmtNum(Math.round(r.revenue))}`}</td>
                <td className="num">{share(r.costShare, 3)}</td>
                <td className="num">{share(r.changeShare, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="help" data-testid={`ratio-${option.optionId}`}>
        {ratio === undefined
          ? "Small-to-large ratio: needs both a small and a large business group with an industry (set each group's industry and size on the Proposal page)."
          : `Small-to-large ratio: small businesses' cost is ${ratio.toFixed(2)} times large businesses' as a share of revenue${ratio > 1 ? ", so the cost falls harder on small businesses (Impact Analysis threshold 3 asks whether any cohort is disproportionately affected)" : ""}.`}
      </p>
    </div>
  );
}
