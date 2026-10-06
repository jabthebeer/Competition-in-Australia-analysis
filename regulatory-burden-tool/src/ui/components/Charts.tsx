// Charts follow the dataviz method: the job is polarity (reduction vs increase), so a
// diverging blue/red pair with a neutral for regime totals, validated with the palette
// validator (light surface #ffffff: CVD ΔE ≥ 10.4, normal-vision ΔE ≥ 26.6, all ≥ 3:1).
// Thin bars (≤ 24px) with a 4px rounded data end, hairline grid, text in ink tokens, a
// legend, a tooltip, and a table twin for every chart.
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dec } from "../../engine/decimal";
import type { OptionResult } from "../../engine/index";
import { formatMoney, moneyText } from "../format";

const COLOURS = { reduction: "#2a78d6", increase: "#e34948", total: "#52514e" } as const;
const INK = { secondary: "#52514e", grid: "#e1e0d9", axis: "#c3c2b7" } as const;
type Kind = keyof typeof COLOURS;
const KIND_LABELS: Record<Kind, string> = { reduction: "Reduction", increase: "Increase", total: "Regime cost (context)" };

const toMillions = (v: string) => dec(v).dividedBy(1_000_000).toNumber(); // display only
const tickMillions = (v: number) => `${v < 0 ? "−" : ""}$${Math.abs(v).toLocaleString("en-AU", { maximumFractionDigits: 1 })}m`;

/** A rect path with 4px rounding on the given end only (the data end), square at the baseline. */
function roundedPath(x: number, y: number, w: number, h: number, end: "top" | "bottom" | "left" | "right"): string {
  const r = Math.min(4, Math.abs(w) / 2, Math.abs(h) / 2);
  const x0 = Math.min(x, x + w);
  const y0 = Math.min(y, y + h);
  const W = Math.abs(w);
  const H = Math.abs(h);
  if (W === 0 || H === 0) return "";
  switch (end) {
    case "top":
      return `M${x0},${y0 + H} V${y0 + r} Q${x0},${y0} ${x0 + r},${y0} H${x0 + W - r} Q${x0 + W},${y0} ${x0 + W},${y0 + r} V${y0 + H} Z`;
    case "bottom":
      return `M${x0},${y0} H${x0 + W} V${y0 + H - r} Q${x0 + W},${y0 + H} ${x0 + W - r},${y0 + H} H${x0 + r} Q${x0},${y0 + H} ${x0},${y0 + H - r} Z`;
    case "right":
      return `M${x0},${y0} H${x0 + W - r} Q${x0 + W},${y0} ${x0 + W},${y0 + r} V${y0 + H - r} Q${x0 + W},${y0 + H} ${x0 + W - r},${y0 + H} H${x0} Z`;
    case "left":
      return `M${x0 + W},${y0} H${x0 + r} Q${x0},${y0} ${x0},${y0 + r} V${y0 + H - r} Q${x0},${y0 + H} ${x0 + r},${y0 + H} H${x0 + W} Z`;
  }
}

interface ShapeProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: { kind: Kind; value: number };
}

function Legend({ kinds }: { kinds: Kind[] }) {
  return (
    <ul className="chart-legend" aria-label="Legend">
      {kinds.map((k) => (
        <li key={k}>
          <svg width="12" height="12" aria-hidden="true" focusable="false">
            <rect width="12" height="12" rx="2" fill={COLOURS[k]} />
          </svg>
          {KIND_LABELS[k]}
        </li>
      ))}
    </ul>
  );
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: { label: string; display: string; kind: Kind } }[] }) {
  const row = active ? payload?.[0]?.payload : undefined;
  if (!row) return null;
  return (
    <div className="chart-tooltip">
      <strong>{row.display}</strong>
      <span>{row.label}</span>
      <span className="tooltip-kind">{KIND_LABELS[row.kind]}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------

/** Waterfall: current regime → removed → reduced → increased → new → transition → current + net change. */
export function WaterfallChart({ option }: { option: OptionResult }) {
  let running = 0;
  const rows = option.waterfall
    .filter((s) => s.step === "current" || s.step === "end" || s.value !== "0")
    .map((s) => {
      const v = toMillions(s.value);
      if (s.step === "current" || s.step === "end") {
        running = v;
        return { label: s.label, range: [0, v] as [number, number], kind: "total" as Kind, value: v, display: moneyText(s.value), raw: s.value };
      }
      const start = running;
      running += v;
      return { label: s.label, range: [Math.min(start, running), Math.max(start, running)] as [number, number], kind: (v < 0 ? "reduction" : "increase") as Kind, value: v, display: moneyText(s.value), raw: s.value };
    });
  const net = dec(option.waterfall.filter((s) => s.step !== "current" && s.step !== "end").reduce((a, s) => a.plus(s.value), dec(0))).toFixed();
  const shape = (p: ShapeProps) => {
    const kind = p.payload?.kind ?? "total";
    const end = kind === "reduction" ? "bottom" : "top";
    return <path d={roundedPath(p.x ?? 0, p.y ?? 0, p.width ?? 0, p.height ?? 0, end)} fill={COLOURS[kind]} />;
  };
  return (
    <figure className="chart" data-testid="waterfall">
      <h3>From the current regime to the reformed regime</h3>
      <figcaption className="help">
        Average annual cost, $ million. Net change: <strong>{moneyText(net)}</strong> a year (the RBE total). Regime costs are context, not RBE figures.
      </figcaption>
      <Legend kinds={["total", "reduction", "increase"]} />
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={rows} margin={{ top: 24, right: 16, bottom: 8, left: 8 }} title="Waterfall of annual regulatory cost" desc={`From the current regime to the reformed regime; net change ${moneyText(net)} a year`}>
          <CartesianGrid vertical={false} stroke={INK.grid} />
          <XAxis dataKey="label" tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={{ stroke: INK.axis }} interval={0} height={48} />
          <YAxis tickFormatter={tickMillions} tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={false} width={64} />
          <ReferenceLine y={0} stroke={INK.axis} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(11,11,11,0.04)" }} />
          <Bar dataKey="range" barSize={24} shape={shape} isAnimationActive={false}>
            {rows.map((r) => (
              <Cell key={r.label} fill={COLOURS[r.kind]} />
            ))}
            <LabelList dataKey="display" position="top" fill={INK.secondary} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <details className="profile">
        <summary>Show as a table</summary>
        <table>
          <caption className="visually-hidden">Waterfall values</caption>
          <thead>
            <tr>
              <th scope="col">Step</th>
              <th scope="col" className="num">Average annual amount</th>
            </tr>
          </thead>
          <tbody>
            {option.waterfall.map((s) => (
              <tr key={s.step}>
                <th scope="row">{s.label}</th>
                <td className="num">{formatMoney(s.value, "dollars")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/** Signed horizontal bars: the change in burden by a breakdown (obligation, category, cohort...). */
export function BreakdownChart({ title, data, labels }: { title: string; data: Record<string, string>; labels: (key: string) => string }) {
  const rows = Object.entries(data)
    .filter(([, v]) => v !== "0")
    .map(([k, v]) => ({ key: k, label: labels(k), value: toMillions(v), kind: (dec(v).isNegative() ? "reduction" : "increase") as Kind, display: moneyText(v), raw: v }))
    .sort((a, b) => a.value - b.value);
  if (rows.length === 0) return null;
  const shape = (p: ShapeProps) => {
    const kind = p.payload?.kind ?? "increase";
    return <path d={roundedPath(p.x ?? 0, p.y ?? 0, p.width ?? 0, p.height ?? 0, kind === "reduction" ? "left" : "right")} fill={COLOURS[kind]} />;
  };
  const kinds = [...new Set(rows.map((r) => r.kind))];
  return (
    <figure className="chart" data-testid={`breakdown-${title}`}>
      <h3>{title}</h3>
      <figcaption className="help">Change in average annual cost, $ million.</figcaption>
      {kinds.length > 1 && <Legend kinds={kinds} />}
      <ResponsiveContainer width="100%" height={rows.length * 40 + 56}>
        <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 72, bottom: 8, left: 8 }} title={title} desc={`${rows.length} bars`}>
          <CartesianGrid horizontal={false} stroke={INK.grid} />
          <XAxis type="number" tickFormatter={tickMillions} tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={{ stroke: INK.axis }} />
          <YAxis type="category" dataKey="label" width={180} tick={{ fill: INK.secondary, fontSize: 12 }} tickLine={false} axisLine={false} />
          <ReferenceLine x={0} stroke={INK.axis} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(11,11,11,0.04)" }} />
          <Bar dataKey="value" barSize={20} shape={shape} isAnimationActive={false}>
            {rows.map((r) => (
              <Cell key={r.key} fill={COLOURS[r.kind]} />
            ))}
            <LabelList dataKey="display" position="right" fill={INK.secondary} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <details className="profile">
        <summary>Show as a table</summary>
        <table>
          <caption className="visually-hidden">{title}</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col" className="num">Change a year</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <th scope="row">{r.label}</th>
                <td className="num">{formatMoney(r.raw, "dollars")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
