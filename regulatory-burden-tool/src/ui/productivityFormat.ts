// Number formats for productivity results: signed percentages of GDP and dollar amounts in words.
import type { Percentiles } from "../productivity/index";

const minus = (x: number) => (x < 0 ? "−" : "+");

/** A signed percentage: three decimals, or two significant figures below 0.01%. */
export function gdpPct(x: number): string {
  if (x === 0) return "0.000%";
  const a = Math.abs(x);
  return `${minus(x)}${a >= 0.01 ? a.toFixed(3) : a.toPrecision(2)}%`;
}

/** $ million as words: "$5.5 billion", "$62 million", "$0.4 million"; signed only when negative. */
export function millions(m: number): string {
  const a = Math.abs(m);
  const s = m < 0 ? "−" : "";
  if (a >= 1000) return `${s}$${(a / 1000).toLocaleString("en-AU", { maximumFractionDigits: 1 })} billion`;
  return `${s}$${a.toLocaleString("en-AU", { maximumFractionDigits: a >= 10 ? 0 : 1 })} million`;
}

/** Whole dollars: "$187". */
export function dollars(x: number): string {
  return `${x < 0 ? "−" : ""}$${Math.abs(x).toLocaleString("en-AU", { maximumFractionDigits: 0 })}`;
}

export function range(p: Percentiles, f: (x: number) => string): string {
  return `${f(p.p10)} to ${f(p.p90)}`;
}
