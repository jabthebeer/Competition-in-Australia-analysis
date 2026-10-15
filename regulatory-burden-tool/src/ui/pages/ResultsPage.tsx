import { useState } from "react";
import { rbeTable, verdictText, type OptionResult, type Precision, type Proposal, type ProposalResult, type Warning } from "../../engine/index";
import { PageHeading, type PageProps } from "../App";
import { BreakdownChart, WaterfallChart } from "../components/Charts";
import { RadioGroup } from "../components/fields";
import { CATEGORY_LABELS, COHORT_LABELS, GROUP_LABELS, TIMING_LABELS, fmtNum, fmtPct, formatMoney, moneyText } from "../format";

const PRECISIONS: { value: string; label: string }[] = [
  { value: "1", label: "$ million, 1 decimal place" },
  { value: "2", label: "2 decimal places" },
  { value: "3", label: "3 decimal places" },
  { value: "dollars", label: "Exact dollars" },
];

export function ResultsPage({ proposal, computed }: PageProps) {
  const [precisionKey, setPrecisionKey] = useState("1");
  const precision: Precision = precisionKey === "dollars" ? "dollars" : (Number(precisionKey) as 1 | 2 | 3);
  if (!computed.ok) {
    return (
      <>
        <PageHeading>Results</PageHeading>
        <p>Results will appear once the inputs listed at the top of the page are fixed.</p>
      </>
    );
  }
  const r = computed.result;
  return (
    <>
      <PageHeading>Results</PageHeading>
      <p>
        Average annual change in regulatory costs from business as usual, over {r.durationYears} years, in real terms and without discounting. Measured against{" "}
        {r.baseline === "statusQuo" ? "current settings" : "no instrument (a sunsetting instrument being remade)"}.
      </p>
      <RadioGroup label="Show figures as" value={precisionKey} options={PRECISIONS} inline onChange={setPrecisionKey} testId="precision" />
      {r.options.length > 1 && <Comparison result={r} precision={precision} />}
      {r.options.map((o) => (
        <OptionResults key={o.optionId} proposal={proposal} result={r} option={o} precision={precision} />
      ))}
      <Warnings warnings={r.warnings.filter((w) => !w.optionId)} title="Warnings for the whole proposal" />
      <Assumptions result={r} />
      <p className="context-note">
        Forgone benefits of a lighter regulation (such as safety or consumer protection) are outside the Regulatory Burden Measurement framework. Discuss them in the Impact Analysis.
      </p>
    </>
  );
}

export function RbeTable({ option, precision, testId }: { option: OptionResult; precision: Precision; testId?: string }) {
  const t = rbeTable(option.rbe, precision);
  return (
    <div className="table-wrap">
      <table className="rbe-table" data-testid={testId}>
        <caption>{t.caption}</caption>
        <thead>
          <tr>
            {t.headers.map((h, i) => (
              <th key={h} scope="col" className={i > 0 ? "num" : undefined}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">{t.cells[0]}</th>
            {t.cells.slice(1).map((c, i) => (
              <td key={i} className="num">
                {c}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
      {t.notes.map((n) => (
        <p key={n} className="context-note">
          {n}
        </p>
      ))}
    </div>
  );
}

function Comparison({ result, precision }: { result: ProposalResult; precision: Precision }) {
  return (
    <section aria-labelledby="comparison-heading">
      <h2 id="comparison-heading">Options side by side</h2>
      <div className="table-wrap">
        <table data-testid="comparison">
          <caption className="visually-hidden">Average annual change in regulatory costs by option</caption>
          <thead>
            <tr>
              <th scope="col">Option</th>
              <th scope="col" className="num">Business</th>
              <th scope="col" className="num">Community organisations</th>
              <th scope="col" className="num">Individuals</th>
              <th scope="col" className="num">Total change a year</th>
              <th scope="col" className="num">Over {result.durationYears} years</th>
            </tr>
          </thead>
          <tbody>
            {result.options.map((o) => (
              <tr key={o.optionId}>
                <th scope="row">{o.optionName}</th>
                <td className="num">{formatMoney(o.rbe.business, precision)}</td>
                <td className="num">{formatMoney(o.rbe.communityOrg, precision)}</td>
                <td className="num">{formatMoney(o.rbe.individual, precision)}</td>
                <td className="num">{formatMoney(o.rbe.total, precision)}</td>
                <td className="num">{formatMoney(o.tenYearTotal, precision)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {precision !== "dollars" && <p className="context-note">$ million.</p>}
    </section>
  );
}

function OptionResults({ proposal, result, option: o, precision }: { proposal: Proposal; result: ProposalResult; option: OptionResult; precision: Precision }) {
  const T = result.durationYears;
  const altLabel = o.alternativeBaseline.baseline === "statusQuo" ? "current settings" : "no instrument";
  const hasCurrent = o.context.currentAnnual !== "0";
  const obligationName = (id: string) => {
    for (const opt of proposal.options) for (const ob of [...opt.obligations, ...opt.transitions]) if (ob.id === id) return ob.name || "Unnamed obligation";
    return id;
  };
  const optWarnings = result.warnings.filter((w) => w.optionId === o.optionId);
  return (
    <section className="card" aria-labelledby={`res-${o.optionId}`} data-testid={`results-${o.optionId}`}>
      <h2 id={`res-${o.optionId}`}>{o.optionName}</h2>
      <RbeTable option={o} precision={precision} testId={`rbe-${o.optionId}`} />
      <p className={`verdict ${o.verdict.kind}`} aria-live="polite" data-testid={`verdict-${o.optionId}`}>
        {verdictText(o.verdict)}
      </p>
      <div className="stat-row">
        <div className="stat">
          <span className="stat-label">Gross increases</span>
          <span className="stat-value">{moneyText(o.gross.increases, precision)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Gross reductions</span>
          <span className="stat-value">{moneyText(o.gross.reductions, precision)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Total over {T} years (Dashboard IA)</span>
          <span className="stat-value" data-testid={`total-${o.optionId}`}>{moneyText(o.tenYearTotal, precision)}</span>
          {o.iaThreshold1.likelyMet && <span className="threshold-badge">Likely meets IA threshold 1 ($20m over 10 years): confirm with OIA</span>}
        </div>
        <div className="stat">
          <span className="stat-label">Against {altLabel} instead (context)</span>
          <span className="stat-value">{moneyText(o.alternativeBaseline.rbe.total, precision)} a year</span>
        </div>
      </div>
      {!o.isStatusQuo && hasCurrent && (
        <p className="context-note" data-testid={`context-${o.optionId}`}>
          <strong>Context, not RBE figures:</strong> the current regime costs {moneyText(o.context.currentAnnual, precision)} a year and the reformed regime {moneyText(o.context.reformedAnnual, precision)} a year, with transition costs of {moneyText(o.context.transitionAnnual, precision)} a year on average. The option removes {fmtPct(o.context.shareRemoved ?? "0")} of the current regime's burden ({fmtPct(o.context.shareRemovedNetOfTransition ?? "0")} after transition costs).
        </p>
      )}
      {!o.isStatusQuo && hasCurrent && <WaterfallChart option={o} />}
      {!o.isStatusQuo && <BreakdownChart title="Change by obligation" data={o.breakdowns.obligation} labels={obligationName} />}
      {!o.isStatusQuo && (
        <details className="more">
          <summary>More breakdowns</summary>
          <Breakdown title="By type of cost" data={o.breakdowns.category} labels={(k) => CATEGORY_LABELS[k as keyof typeof CATEGORY_LABELS] ?? k} />
          <Breakdown title="By stakeholder group" data={o.breakdowns.group} labels={(k) => GROUP_LABELS[k as keyof typeof GROUP_LABELS] ?? k} />
          <Breakdown title="By size" data={o.breakdowns.cohort} labels={(k) => COHORT_LABELS[k as keyof typeof COHORT_LABELS] ?? k} />
          <Breakdown title="By timing" data={o.breakdowns.timing} labels={(k) => TIMING_LABELS[k] ?? k} />
          {proposal.jurisdiction === "interJurisdictional" && <Breakdown title="By jurisdiction" data={o.breakdowns.jurisdiction} labels={(k) => (k === "commonwealth" ? "Commonwealth" : "States and territories")} />}
        </details>
      )}
      {!o.isStatusQuo && <PerEntity option={o} />}
      {o.excluded.length > 0 && (
        <div>
          <h3>Kept out of the RBE</h3>
          <ul>
            {o.excluded.map((e, i) => (
              <li key={i}>
                {e.obligationName} ({e.side === "current" ? "current regime" : "reformed regime"}): {e.label}, {formatMoney(e.annualAmount, "dollars")} a year. <span className="context-note">{e.explanation} ({e.ref})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <Warnings warnings={optWarnings} title="Warnings for this option" level={3} />
    </section>
  );
}

function Breakdown({ title, data, labels }: { title: string; data: Record<string, string>; labels: (k: string) => string }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;
  return (
    <table>
      <caption>{title}</caption>
      <tbody>
        {entries.map(([k, v]) => (
          <tr key={k}>
            <th scope="row">{labels(k)}</th>
            <td className="num">{formatMoney(v, "dollars")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PerEntity({ option }: { option: OptionResult }) {
  if (option.perEntity.length === 0) return null;
  return (
    <div className="table-wrap">
      <table data-testid={`per-entity-${option.optionId}`}>
        <caption>Change per affected entity, per year</caption>
        <thead>
          <tr>
            <th scope="col">Group</th>
            <th scope="col" className="num">Number</th>
            <th scope="col" className="num">Today, each</th>
            <th scope="col" className="num">Reformed, each</th>
            <th scope="col" className="num">Change, each</th>
          </tr>
        </thead>
        <tbody>
          {option.perEntity.map((p) => (
            <tr key={p.populationId}>
              <th scope="row">
                {p.label}
                {p.cliffFlag && <span className="badge changed-badge">Cliff: no relief above the threshold</span>}
              </th>
              <td className="num">{fmtNum(p.count, 0)}</td>
              <td className="num">{formatMoney(p.currentAnnualPerEntity, "dollars")}</td>
              <td className="num">{formatMoney(p.reformedAnnualPerEntity, "dollars")}</td>
              <td className="num">{formatMoney(p.changePerEntity, "dollars")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Warnings({ warnings, title, level = 2 }: { warnings: Warning[]; title: string; level?: 2 | 3 }) {
  if (warnings.length === 0) return null;
  const H = level === 2 ? "h2" : "h3";
  return (
    <section>
      <H>{title}</H>
      <ul className="warning-list" data-testid="warnings">
        {warnings.map((w, i) => (
          <li key={i}>
            <span className="sev">{w.severity === "info" ? "Note" : "Check"} ({w.code}):</span>
            {w.message} <span className="context-note">({w.ref})</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Assumptions({ result }: { result: ProposalResult }) {
  return (
    <section aria-labelledby="assumptions-heading">
      <h2 id="assumptions-heading">Assumptions register</h2>
      <div className="table-wrap">
        <table>
          <caption className="visually-hidden">Assumptions and their sources</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">Value</th>
              <th scope="col">Default</th>
              <th scope="col">Justification and source</th>
            </tr>
          </thead>
          <tbody>
            {result.assumptions.map((a, i) => (
              <tr key={i}>
                <th scope="row">{a.item}</th>
                <td>{a.value}</td>
                <td>{a.defaultValue ?? "—"}</td>
                <td>{[a.justification, a.source, a.ref].filter(Boolean).join(" · ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
