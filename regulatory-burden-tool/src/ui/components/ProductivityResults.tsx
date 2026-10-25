// The productivity and competition results (plan §3.1 step 6): the evidence gate, the long-run GDP effect with its
// range, the threshold 2 check, the time path and present values, effects by channel and industry, the tornado,
// and what is not quantified. Central figures appear only with their ranges (plan §3.2, principle 2), so the
// headline waits for the Monte Carlo, which runs in chunks to keep the page responsive.
import { useEffect, useMemo, useState } from "react";
import { costBrief, evidenceGate, simulateInChunks, tornado, type CostingContext, type CostingResult, type PolicyBrief, type Ranges, type TornadoBar } from "../../productivity/index";
import type { PageProps } from "../App";
import { useCostingContext } from "../costingContext";
import { gdpPct, dollars, millions, range } from "../productivityFormat";
import { ChannelDetail } from "./ChannelDetail";
import { Checkbox, QuantityField, SelectField } from "./fields";
import { PathChart, SignedBars, Tornado } from "./ProductivityCharts";
import { BriefIssues } from "../pages/LeversPage";

const fy = (start: number, year: number) => {
  const y = start + year - 1;
  return `${y}-${String((y + 1) % 100).padStart(2, "0")}`;
};

const GATE_TITLES = {
  full: "Shown in full: material, and resting on evidence graded A or B",
  indicative: "Indicative",
  hidden: "GDP figures hidden by the evidence gate",
} as const;

/** Runs the Monte Carlo and the tornado for a brief, restarting (and cancelling the last run) when it changes. */
export function useRanges(brief: PolicyBrief | null, ctx: CostingContext | null) {
  const [state, setState] = useState<{ brief: PolicyBrief | null; ranges: Ranges | null; tornado: TornadoBar[]; done: number; draws: number }>({ brief: null, ranges: null, tornado: [], done: 0, draws: 0 });
  useEffect(() => {
    if (!brief || !ctx) return;
    const stop = new AbortController();
    const draws = brief.analysis.draws;
    setState({ brief, ranges: null, tornado: [], done: 0, draws });
    const t = window.setTimeout(() => {
      simulateInChunks(brief, ctx, { signal: stop.signal, onProgress: (done) => !stop.signal.aborted && setState((s) => ({ ...s, done })) })
        .then((ranges) => {
          if (!stop.signal.aborted) setState({ brief, ranges, tornado: tornado(brief, ctx), done: draws, draws });
        })
        .catch(() => undefined); // cancelled: a newer run replaces it
    }, 250);
    return () => {
      stop.abort();
      window.clearTimeout(t);
    };
  }, [brief, ctx]);
  return state.brief === brief ? state : { brief, ranges: null, tornado: [], done: 0, draws: brief?.analysis.draws ?? 0 };
}

export function ProductivityResults({ brief, draft, updateDraft }: PageProps) {
  const loaded = useCostingContext();
  const ctx = loaded.status === "ready" ? loaded.ctx : null;
  const parsed = brief.ok ? brief.brief : null;
  const central: CostingResult | null = useMemo(() => (parsed && ctx ? costBrief(parsed, ctx) : null), [parsed, ctx]);
  const { ranges, tornado: bars, done, draws } = useRanges(parsed, ctx);
  const a = draft.analysis;
  const setAnalysis = (patch: Partial<typeof a>) => updateDraft((d) => ({ ...d, analysis: { ...d.analysis, ...patch } }));

  return (
    <section aria-labelledby="productivity-heading" data-testid="productivity-results">
      <h2 id="productivity-heading">Productivity and competition</h2>
      <p>
        The long-run change in the level of real GDP from the productivity levers and the compliance-cost change, with its range, against the baseline. These figures are separate from the Regulatory Burden Estimate, which they never change.
      </p>
      <BriefIssues brief={brief} />
      {loaded.status === "loading" && <p>Loading the bundled data…</p>}
      {loaded.status === "error" && <p className="banner error">{loaded.problem}</p>}

      <details className="card settings">
        <summary>Settings: realisation, discount rate, number of draws</summary>
        <QuantityField
          label="Realisation factor"
          help="Scales every productivity effect: 1 is as estimated. Ex post, the 1990s National Competition Policy reforms delivered less than half the gain projected ex ante (PC 2024, p. 13), so 0.5 is a cautious sensitivity."
          allowRange={false}
          min={0}
          max={2}
          value={a.realisationFactor ?? 1}
          onChange={(q) => setAnalysis({ realisationFactor: q as number })}
          testId="analysis-realisation"
        />
        <QuantityField
          label="Discount rate for present values"
          help="The OIA's cost–benefit guidance uses 7% real, with 3% and 10% as sensitivities."
          allowRange={false}
          scale={100}
          unit="%"
          min={0}
          max={0.2}
          value={a.discountRate ?? 0.07}
          onChange={(q) => setAnalysis({ discountRate: q as number })}
        />
        <SelectField
          label="Monte Carlo draws"
          value={String(a.draws ?? 2000)}
          options={[
            { value: "500", label: "500 (quick)" },
            { value: "2000", label: "2,000 (default)" },
            { value: "5000", label: "5,000 (steadier ranges)" },
          ]}
          onChange={(v) => setAnalysis({ draws: Number(v) })}
        />
        <Checkbox
          label="Show GDP figures the evidence gate would hide"
          help="They are then marked as a draft. Use this to see the arithmetic, not to report it."
          checked={!!a.showUngatedEconomyWide}
          onChange={(on) => setAnalysis({ showUngatedEconomyWide: on })}
          testId="analysis-show-ungated"
        />
      </details>

      {parsed && ctx && central && (ranges ? <Results brief={parsed} ctx={ctx} central={central} ranges={ranges} bars={bars} warnings={brief.ok ? brief.warnings : []} /> : <Progress done={done} draws={draws} />)}
    </section>
  );
}

function Progress({ done, draws }: { done: number; draws: number }) {
  return (
    <div className="summary-box" role="status" data-testid="productivity-running">
      Working out the ranges: {done.toLocaleString("en-AU")} of {draws.toLocaleString("en-AU")} draws.
      <progress max={draws} value={done} aria-label="Monte Carlo progress" />
    </div>
  );
}

function Results({ brief, ctx, central: r, ranges, bars, warnings }: { brief: PolicyBrief; ctx: CostingContext; central: CostingResult; ranges: Ranges; bars: TornadoBar[]; warnings: { code: string; message: string }[] }) {
  const gate = evidenceGate(brief, r, ranges, warnings as never);
  const start = brief.meta.startYear;
  const costed = r.channels.filter((c) => c.gdpPct !== 0);
  const byIndustry = industryRows(r, ctx);
  const t2 = gate.threshold2;
  const [main, ...others] = r.npv;
  const notQuantified = r.channels.flatMap((c) => c.reasons.map((reason) => ({ channel: c.channel, name: c.name, reason })));
  return (
    <>
      <div className={gate.status === "full" ? "summary-box gate" : gate.status === "indicative" ? "banner draft gate" : "banner error gate"} data-testid="gate" data-status={gate.status}>
        <strong>Evidence gate: {GATE_TITLES[gate.status]}.</strong>
        {gate.reasons.length > 0 && (
          <ul>
            {gate.reasons.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        )}
        {gate.watermark && <p className="watermark">Draft: shown although the gate would hide it, or resting on unconfirmed estimates. Not for reporting.</p>}
      </div>

      {gate.showGdp ? (
        <>
          <p className="headline" data-testid="productivity-headline">
            Long-run change in real GDP: <strong>{gdpPct(r.gdpPct)}</strong> (10–90% range {range(ranges.gdpPct, gdpPct)}), about <strong>{millions(r.gdpDollars)} a year</strong> in {r.gdpYear} dollars, or {dollars(r.gdpPerPersonDollars)} a person.
          </p>
          <p data-testid="threshold2">
            Impact Analysis threshold 2 (${gate.thresholdDollars} million a year): the central estimate {t2.centralMeets ? "meets it" : "does not meet it"}, and the low end of the range ({millions(t2.low)}) {t2.lowMeets ? "meets it too" : "does not"}.
            {t2.centralMeets && !t2.lowMeets ? " Treat it as possibly material and say so in the Impact Analysis." : ""}
          </p>
          <div className="table-wrap">
            <table data-testid="productivity-years">
              <caption>Change in real GDP, central estimate and 10–90% range</caption>
              <thead>
                <tr>
                  <th scope="col">When</th>
                  <th scope="col" className="num">GDP</th>
                  <th scope="col">10–90% range</th>
                  <th scope="col" className="num">$ a year</th>
                </tr>
              </thead>
              <tbody>
                {ranges.byYear.map((y) => (
                  <tr key={y.year}>
                    <th scope="row">
                      Year {y.year} ({fy(start, y.year)})
                    </th>
                    <td className="num">{gdpPct(r.path[y.year - 1]!.gdpPct)}</td>
                    <td>{range(y.gdpPct, gdpPct)}</td>
                    <td className="num">{millions(r.path[y.year - 1]!.gdpDollars)}</td>
                  </tr>
                ))}
                <tr>
                  <th scope="row">Long run</th>
                  <td className="num">{gdpPct(r.gdpPct)}</td>
                  <td>{range(ranges.gdpPct, gdpPct)}</td>
                  <td className="num">{millions(r.gdpDollars)}</td>
                </tr>
              </tbody>
            </table>
          </div>
          {main && (
            <p data-testid="npv">
              Present value of the GDP change over {brief.meta.durationYears} years at {Number((main.rate * 100).toFixed(2))}%: <strong>{millions(main.dollars)}</strong> (10–90% range {range(ranges.npv, millions)})
              {others.length > 0 && `; ${others.map((n) => `${millions(n.dollars)} at ${Number((n.rate * 100).toFixed(2))}%`).join(", ")}`}. Dollar figures hold GDP at its {r.gdpYear} level.
            </p>
          )}
          {costed.length > 0 && (
            <SignedBars
              title="By channel"
              caption="Long-run change in real GDP from each channel, per cent, with its 10–90% range."
              rows={costed.map((c) => ({ key: c.channel, label: `${c.channel} ${c.name}`, value: c.gdpPct, range: ranges.byChannel.find((b) => b.channel === c.channel)?.gdpPct }))}
              testId="productivity-channels"
            />
          )}
          <PathChart
            longRun={r.gdpPct}
            points={ranges.path.map((p, i) => ({ year: p.year, label: fy(start, p.year), central: r.path[i]!.gdpPct, low: p.gdpPct.p10, high: p.gdpPct.p90, dollars: r.path[i]!.gdpDollars }))}
          />
          {byIndustry.length > 0 && <SignedBars title="By industry" caption="Long-run change in real GDP coming from each industry (input-output industries), per cent, central estimate. The ten largest are shown." rows={byIndustry} testId="productivity-industries" />}
          {bars.length > 0 && <Tornado central={r.gdpDollars} rows={bars.map((b) => ({ key: b.key, label: b.label, low: b.low, high: b.high, atLow: b.gdpDollarsAtLow, atHigh: b.gdpDollarsAtHigh }))} />}
        </>
      ) : (
        <p data-testid="gdp-hidden">
          The GDP figures are hidden because the evidence behind the largest effect is too weak to report as a number. The direct effects below still show what the policy changes in each industry. To see the arithmetic anyway, tick "Show GDP figures the evidence gate would hide" in the settings above.
        </p>
      )}

      {r.welfareDollars !== 0 && (
        <p data-testid="welfare">
          Efficiency cost of the funding (beside GDP, not in it): <strong>{millions(r.welfareDollars / 1e6)} a year</strong>.
        </p>
      )}

      <h3>Direct effects by channel</h3>
      <p className="help">The calculation behind each channel, industry by industry, with its evidence and grade.</p>
      {r.channels.map((c) => (
        <details key={c.channel} className="card">
          <summary>
            {c.channel} {c.name}
          </summary>
          <ChannelDetail outcome={c} testId={`result-channel-${c.channel}`} />
        </details>
      ))}

      <h3>What is not quantified</h3>
      <ul className="not-costed-list" data-testid="not-quantified">
        {notQuantified.map((n, i) => (
          <li key={i}>
            <strong>
              {n.channel} {n.name}:
            </strong>{" "}
            {n.reason}
          </li>
        ))}
        {r.notModelled.map((n) => (
          <li key={n}>{n}</li>
        ))}
      </ul>
      {warnings.length > 0 && (
        <>
          <h3>Warnings</h3>
          <ul className="warning-list">
            {warnings.map((w, i) => (
              <li key={i}>
                [{w.code}] {w.message}
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

/** The ten input-output industries contributing most to the long-run GDP change, and the rest together. */
function industryRows(r: CostingResult, ctx: CostingContext) {
  const names = new Map(ctx.weights.map((w) => [w.id, w.name]));
  const sums = new Map<string, number>();
  for (const c of r.layerB.contributions) sums.set(c.industry, (sums.get(c.industry) ?? 0) + c.gdpPct * r.realisationFactor);
  const sorted = [...sums].filter(([, v]) => v !== 0).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const top = sorted.slice(0, 10).map(([id, value]) => ({ key: id, label: names.get(id) ?? id, value }));
  const rest = sorted.slice(10).reduce((s, [, v]) => s + v, 0);
  return rest !== 0 ? [...top, { key: "other", label: `All other industries (${sorted.length - 10})`, value: rest }] : top;
}
