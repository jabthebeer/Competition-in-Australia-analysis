// Display helpers for the UI (money formats come from the engine's format module).
import { dec } from "../engine/decimal";
import { formatMoney, type Precision } from "../engine/index";

export { formatMoney };

/** A number with thousands separators, trimmed to at most `dp` decimal places. */
export function fmtNum(value: string | number, dp = 2): string {
  const d = dec(value).toDecimalPlaces(dp);
  const [whole = "0", frac] = d.abs().toFixed().split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${d.isNegative() ? "−" : ""}${grouped}${frac ? `.${frac}` : ""}`;
}

export function fmtPct(share: string | number, dp = 1): string {
  return `${fmtNum(dec(share).times(100).toFixed(), dp)}%`;
}

/** Money in running text: "$4.4m" / "($12.7m)" for $ million precision, or dollars. */
export function moneyText(value: string, precision: Precision = 1): string {
  const f = formatMoney(value, precision);
  return precision === "dollars" || f === "$0" ? f : f.replace(/(\d)(\)?)$/, "$1m$2");
}

export const GROUP_LABELS = { business: "Business", communityOrg: "Community organisations", individual: "Individuals" } as const;
export const GROUP_NOUNS = { business: "businesses", communityOrg: "organisations", individual: "individuals" } as const;
export const COHORT_LABELS = { all: "All sizes", small: "Small", medium: "Medium", large: "Large" } as const;
export const CATEGORY_LABELS = { administrative: "Administrative", substantive: "Substantive compliance", delay: "Delay" } as const;
export const TIMING_LABELS: Record<string, string> = {
  oneOff: "One-off",
  ongoing: "Ongoing",
  everyKYears: "Every few years",
  schedule: "Year-by-year schedule",
  transition: "Transition",
};
