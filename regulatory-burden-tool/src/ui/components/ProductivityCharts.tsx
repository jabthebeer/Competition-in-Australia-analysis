// Charts for the productivity costing (plan §3.1 step 6). The job is polarity (a GDP gain or loss), so the same
// diverging blue/red pair as the burden charts, re-validated on this surface (#ffffff: CVD ΔE 21.6, normal-vision
// ΔE 32.3, both ≥ 3:1): blue is a gain, as blue is a saving there. Thin bars (20px) with 4px rounding, 2px lines,
// a 10% wash for the 10–90% band, hairline grid, text in ink tokens, a tooltip, and a table twin for every chart.
// Bar charts are HTML on one explicit scale, so whiskers sit exactly on it and labels wrap at phone width.
import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Percentiles } from "../../productivity/index";
import { gdpPct, millions, range } from "../productivityFormat";

export const GAIN = "#2a78d6";
export const LOSS = "#e34948";
const INK = { secondary: "#52514e", grid: "#e1e0d9", axis: "#c3c2b7" } as const;

function Legend({ items }: { items: { colour: string; label: string; line?: boolean }[] }) {
  return (
    <ul className="chart-legend" aria-label="Legend">
      {items.map((i) => (
        <li key={i.label}>
          <svg width="16" height="12" aria-hidden="true" focusable="false">
            {i.line ? <line x1="0" y1="6" x2="16" y2="6" stroke={i.colour} strokeWidth="2" strokeLinecap="round" /> : <rect width="12" height="12" rx="2" fill={i.colour} />}
          </svg>
          {i.label}
        </li>
      ))}
    </ul>
  );
}

export interface SignedRow {
  key: string;
  label: string;
  /** Long-run change in GDP, per cent. */
  value: number;
  range?: Percentiles;
}

/**
 * Signed horizontal bars of the long-run GDP change, with the 10–90% range as a whisker when given. Drawn in HTML on
 * one scale (zero, the bars and the whiskers), so each label is real text and wraps at phone width.
 */
export function SignedBars({ title, caption, rows, testId }: { title: string; caption: string; rows: SignedRow[]; testId: string }) {
  const values = rows.flatMap((r) => [r.value, ...(r.range ? [r.range.p10, r.range.p90] : [])]).concat(0);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const x = (v: number) => ((v - lo) / span) * 100;
  const signs = new Set(rows.map((r) => r.value < 0));
  const withRange = rows.some((r) => r.range);
  return (
    <figure className="chart" data-testid={testId}>
      <h3>{title}</h3>
      <figcaption className="help">{caption}</figcaption>
      {(signs.size > 1 || withRange) && (
        <Legend
          items={[
            ...(signs.has(false) ? [{ colour: GAIN, label: "Gain" }] : []),
            ...(signs.has(true) ? [{ colour: LOSS, label: "Loss" }] : []),
            ...(withRange ? [{ colour: INK.secondary, label: "10–90% range", line: true }] : []),
          ]}
        />
      )}
      <ol className="hbars">
        {rows.map((r) => {
          const left = Math.min(x(0), x(r.value));
          const tip = `${r.label}: ${gdpPct(r.value)}${r.range ? ` (10–90%: ${range(r.range, gdpPct)})` : ""}`;
          return (
            <li key={r.key} title={tip}>
              <span className="hbar-label">{r.label}</span>
              <span className="hbar-track" aria-hidden="true">
                <span className={`hbar ${r.value < 0 ? "loss" : "gain"}`} style={{ left: `${left}%`, width: `${Math.max(Math.abs(x(r.value) - x(0)), 0.4)}%`, background: r.value < 0 ? LOSS : GAIN }} />
                {r.range && <span className="hbar-whisker" style={{ left: `${x(r.range.p10)}%`, width: `${Math.max(x(r.range.p90) - x(r.range.p10), 0.2)}%` }} />}
                <span className="hbar-zero" style={{ left: `${x(0)}%` }} />
              </span>
              <span className="hbar-value">{gdpPct(r.value)}</span>
            </li>
          );
        })}
      </ol>
      <details className="profile">
        <summary>Show as a table</summary>
        <table>
          <caption className="visually-hidden">{title}</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col" className="num">Long-run GDP</th>
              {withRange && <th scope="col">10–90% range</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <th scope="row">{r.label}</th>
                <td className="num">{gdpPct(r.value)}</td>
                {withRange && <td>{r.range ? range(r.range, gdpPct) : ""}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

export interface PathPoint {
  year: number;
  label: string;
  central: number;
  low: number;
  high: number;
  dollars: number;
}

function PathTooltip({ active, payload }: { active?: boolean; payload?: { payload: PathPoint }[] }) {
  const p = active ? payload?.[0]?.payload : undefined;
  if (!p) return null;
  return (
    <div className="chart-tooltip">
      <strong>{gdpPct(p.central)}</strong>
      <span>
        Year {p.year} ({p.label}): {millions(p.dollars)}
      </span>
      <span className="tooltip-kind">
        10–90%: {gdpPct(p.low)} to {gdpPct(p.high)}
      </span>
    </div>
  );
}

/** The GDP change year by year: the central path as a 2px line over its 10–90% band. */
export function PathChart({ points, longRun }: { points: PathPoint[]; longRun: number }) {
  const colour = longRun < 0 ? LOSS : GAIN;
  const data = points.map((p) => ({ ...p, band: [p.low, p.high] as [number, number] }));
  const last = points.at(-1);
  return (
    <figure className="chart" data-testid="productivity-path">
      <h3>How the effect builds up</h3>
      <figcaption className="help">
        Change in the level of real GDP each year, per cent, with the 10–90% range shaded. The long-run effect is {gdpPct(longRun)}; by year {last?.year ?? ""}, {last ? gdpPct(last.central) : ""} has arrived.
      </figcaption>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 8 }} title="GDP change by year" desc={`Central path and 10–90% band over ${points.length} years`}>
          <CartesianGrid vertical={false} stroke={INK.grid} />
          <XAxis dataKey="label" tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={{ stroke: INK.axis }} interval="preserveStartEnd" minTickGap={16} />
          <YAxis tickFormatter={(v: number) => `${Number(v.toPrecision(2))}%`} tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={false} width={64} />
          <ReferenceLine y={0} stroke={INK.axis} />
          <Tooltip content={<PathTooltip />} cursor={{ stroke: INK.axis, strokeWidth: 1 }} />
          <Area dataKey="band" stroke="none" fill={colour} fillOpacity={0.1} isAnimationActive={false} activeDot={false} />
          <Line dataKey="central" stroke={colour} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" dot={false} activeDot={{ r: 4, stroke: "#ffffff", strokeWidth: 2 }} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
      <details className="profile">
        <summary>Show as a table</summary>
        <table>
          <caption className="visually-hidden">GDP change by year</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col" className="num">GDP</th>
              <th scope="col">10–90% range</th>
              <th scope="col" className="num">$ a year</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={p.year}>
                <th scope="row">
                  {p.year} ({p.label})
                </th>
                <td className="num">{gdpPct(p.central)}</td>
                <td>
                  {gdpPct(p.low)} to {gdpPct(p.high)}
                </td>
                <td className="num">{millions(p.dollars)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

export interface TornadoRow {
  key: string;
  label: string;
  low: number;
  high: number;
  atLow: number;
  atHigh: number;
}

/** One-at-a-time sensitivity: each parameter's bars run from the central estimate to the result at its low and high values. */
export function Tornado({ rows, central }: { rows: TornadoRow[]; central: number }) {
  const values = rows.flatMap((r) => [r.atLow, r.atHigh]).concat(central);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const x = (v: number) => ((v - lo) / span) * 100;
  const seg = (v: number, end: string, at: number) => {
    const left = Math.min(x(v), x(central));
    const width = Math.abs(x(v) - x(central));
    const below = v < central;
    return (
      <span
        className={`tornado-bar ${below ? "below" : "above"}`}
        style={{ left: `${left}%`, width: `${Math.max(width, 0.4)}%`, background: below ? LOSS : GAIN }}
        title={`With this parameter at its ${end} value (${at}): ${millions(v)} a year`}
      />
    );
  };
  return (
    <figure className="chart" data-testid="productivity-tornado">
      <h3>What the result depends on most</h3>
      <figcaption className="help">
        Long-run GDP change, $ a year, with one parameter at a time moved to the low or high end of its range and all others central ({millions(central)}). The longest bars are the parameters worth checking first.
      </figcaption>
      <Legend
        items={[
          { colour: LOSS, label: "Lower than the central estimate" },
          { colour: GAIN, label: "Higher than the central estimate" },
        ]}
      />
      <ol className="tornado">
        {rows.map((r) => (
          <li key={r.key}>
            <span className="tornado-label">{r.label}</span>
            <span className="tornado-track" aria-hidden="true">
              {seg(r.atLow, "low", r.low)}
              {seg(r.atHigh, "high", r.high)}
              <span className="tornado-centre" style={{ left: `${x(central)}%` }} />
            </span>
            <span className="tornado-values">
              {millions(Math.min(r.atLow, r.atHigh))} to {millions(Math.max(r.atLow, r.atHigh))}
            </span>
          </li>
        ))}
      </ol>
      <details className="profile">
        <summary>Show as a table</summary>
        <table>
          <caption className="visually-hidden">Sensitivity of the long-run GDP change</caption>
          <thead>
            <tr>
              <th scope="col">Parameter</th>
              <th scope="col">Low → high</th>
              <th scope="col" className="num">GDP at low</th>
              <th scope="col" className="num">GDP at high</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <th scope="row">{r.label}</th>
                <td>
                  {r.low} → {r.high}
                </td>
                <td className="num">{millions(r.atLow)}</td>
                <td className="num">{millions(r.atHigh)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
