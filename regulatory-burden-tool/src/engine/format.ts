// Presentation of results in the framework's RBE table format (RBM pp. 5, 11; A-08).
// Rounding happens only here, never in the calculation.
import { D, dec, type Dec } from "./decimal";
import { PARAMETERS } from "./parameters";
import type { OptionResult, RbeRow } from "./types";

export type Precision = 1 | 2 | 3 | "dollars";

export const RBE_CAPTION = "Average annual regulatory costs (from business as usual)";
export const RBE_ROW_LABEL = "Total, by sector";

export function rbeHeaders(precision: Precision = 1): string[] {
  return [
    precision === "dollars" ? "Change in costs ($)" : "Change in costs ($ million)",
    "Business",
    "Community organisations",
    "Individuals",
    "Total change in costs",
  ];
}

function groupThousands(digits: string): string {
  const [whole = "0", frac] = digits.split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return frac === undefined ? grouped : `${grouped}.${frac}`;
}

function roundHalfAwayFromZero(value: Dec, dp: number): Dec {
  // decimal.js ROUND_HALF_UP rounds ties away from zero.
  return value.toDecimalPlaces(dp, D.ROUND_HALF_UP);
}

/** Formats a dollar amount: $ million to 1–3 decimal places, or exact dollars. Negatives in brackets; exact zero as "$0". */
export function formatMoney(value: string | Dec, precision: Precision = 1): string {
  const v = typeof value === "string" ? dec(value) : value;
  if (v.isZero()) return "$0";
  let body: string;
  if (precision === "dollars") {
    const cents = roundHalfAwayFromZero(v.abs(), 2);
    body = cents.isInteger() ? groupThousands(cents.toFixed(0)) : groupThousands(cents.toFixed(2));
  } else {
    body = groupThousands(roundHalfAwayFromZero(v.abs().dividedBy(1_000_000), precision).toFixed(precision));
  }
  return v.isNegative() ? `($${body})` : `$${body}`;
}

/** Formats a share (e.g. "0.875") as a percentage. */
export function formatShare(value: string | null, dp = 1): string {
  if (value === null) return "n/a";
  return `${roundHalfAwayFromZero(dec(value).times(100), dp).toFixed(dp)}%`;
}

export interface RbeTableView {
  caption: string;
  headers: string[];
  cells: string[];
  notes: string[];
}

/** The RBE table exactly in the framework's layout, with rounding notes where needed. */
export function rbeTable(rbe: RbeRow, precision: Precision = 1): RbeTableView {
  const values = [rbe.business, rbe.communityOrg, rbe.individual].map((x) => dec(x));
  const total = dec(rbe.total);
  const notes: string[] = [];
  if (precision !== "dollars") {
    const round = (x: Dec) => roundHalfAwayFromZero(x.dividedBy(1_000_000), precision);
    const sumOfRounded = values.map(round).reduce((a, b) => a.plus(b), dec(0));
    if (!sumOfRounded.equals(round(total))) notes.push("Columns may not add to the total due to rounding.");
    if ([...values, total].some((x) => !x.isZero() && round(x).isZero())) {
      const limit = formatMoney(dec(1_000_000).times(dec(10).pow(-precision)).dividedBy(2), "dollars");
      notes.push(`$0.${"0".repeat(precision)} means a change of less than ${limit} a year.`);
    }
  }
  return {
    caption: RBE_CAPTION,
    headers: rbeHeaders(precision),
    cells: [RBE_ROW_LABEL, ...values.map((v) => formatMoney(v, precision)), formatMoney(total, precision)],
    notes,
  };
}

/** Plain-language net verdict (brief section 5). */
export function verdictText(verdict: OptionResult["verdict"]): string {
  if (verdict.kind === "none") return "No net change";
  const amount = dec(verdict.amount);
  const shown = amount.lessThan(PARAMETERS.thresholds.verdictInDollarsBelow)
    ? formatMoney(amount, "dollars")
    : `${formatMoney(amount, 1)} million`;
  return verdict.kind === "increase"
    ? `Net increase in regulatory burden of ${shown} a year`
    : `Net reduction of ${shown} a year`;
}

/** The RBE table as Markdown (for the CLI and quick pasting). */
export function rbeTableMarkdown(rbe: RbeRow, precision: Precision = 1): string {
  const t = rbeTable(rbe, precision);
  const lines = [
    `**${t.caption}**`,
    "",
    `| ${t.headers.join(" | ")} |`,
    `|${t.headers.map(() => "---").join("|")}|`,
    `| ${t.cells.join(" | ")} |`,
  ];
  if (t.notes.length) lines.push("", ...t.notes.map((n) => `_${n}_`));
  return lines.join("\n");
}
