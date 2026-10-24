// The time path of a long-run effect (F-B-04) and its present value (PR-06). A shock is phased in over the policy's
// `phaseInYears`; each annual step then builds up towards its long-run effect at a speed that depends on how it works:
//  - productivity shocks follow Égert & Gal's 5- and 10-year shares of the long run (A-P26);
//  - capital deepening (C2, C3) follows their capital-output error-correction speed;
//  - a compliance cost change (C1) lowers measured MFP at once, while the capital that responds to it builds up at the
//    capital-output speed (A-P26);
//  - faster catch-up to the frontier (C4) arrives at the convergence speed λ: 1 − (1 − λ)^τ (A-P30).
import type { ParamSource } from "./layerA";

export type Response = "productivity" | "capital" | "directThenCapital" | "convergence";

export interface PathParams {
  /** Share of the long-run effect reached after 5 and 10 years (productivity shocks). */
  fiveYearShare: number;
  tenYearShare: number;
  /** Error-correction speed of the capital-output ratio, a year (negative). */
  ecmSpeedKY: number;
  /** Capital share: the part of an MFP shock's long-run effect that comes through capital. */
  alpha: number;
  /** Speed of convergence to the frontier, a year (C4). */
  convergenceSpeed: number;
}

export function pathParams(params: ParamSource, alpha: number): PathParams {
  return {
    fiveYearShare: params.get("F-B-04", "fiveYearShare"),
    tenYearShare: params.get("F-B-04", "tenYearShare"),
    ecmSpeedKY: params.get("F-B-04", "ecmSpeedKY"),
    alpha,
    convergenceSpeed: params.get("F-C4-03", "lambda0"),
  };
}

/**
 * The curve s(τ) = 1 − c·e^(−bτ) through the 5- and 10-year shares: b = ln((1 − s₅)/(1 − s₁₀))/5 and
 * c = (1 − s₅)·e^(5b). With Égert & Gal's ETCR shares (0.344, 0.488), b ≈ 0.050 a year, close to their MFP
 * error-correction speed (−0.052).
 */
export function productivityCurve(fiveYearShare: number, tenYearShare: number): { b: number; c: number } {
  const b = Math.log((1 - fiveYearShare) / (1 - tenYearShare)) / 5;
  if (!(fiveYearShare > 0 && tenYearShare < 1 && b > 0)) {
    throw new Error(`The 5- and 10-year shares (${fiveYearShare}, ${tenYearShare}) must rise towards 1`);
  }
  return { b, c: (1 - fiveYearShare) * Math.exp(5 * b) };
}

/** Share of the long-run effect reached in the τ-th year of a shock (τ = 1 in its first year). */
export function responseShare(kind: Response, tau: number, p: PathParams): number {
  if (tau <= 0) return 0;
  const capital = 1 - (1 + p.ecmSpeedKY) ** tau;
  if (kind === "capital") return capital;
  if (kind === "directThenCapital") return 1 - p.alpha + p.alpha * capital;
  if (kind === "convergence") return 1 - (1 - p.convergenceSpeed) ** tau;
  const { b, c } = productivityCurve(p.fiveYearShare, p.tenYearShare);
  return Math.min(1, Math.max(0, 1 - c * Math.exp(-b * tau)));
}

/**
 * Share of the long-run effect in year t of the policy (t = 1 is `startYear`). The shock arrives in equal steps over
 * years 1 to phaseInYears + 1, so it is in full from year phaseInYears + 1; each step builds up on its own.
 */
export function pathShare(kind: Response, t: number, phaseInYears: number, p: PathParams): number {
  const steps = phaseInYears + 1;
  let s = 0;
  for (let k = 1; k <= Math.min(t, steps); k++) s += responseShare(kind, t - k + 1, p) / steps;
  return s;
}

/** Present value of flows in years 1, 2, …, each discounted to the start of year 1 (end-of-year flows). */
export function presentValue(flows: readonly number[], rate: number): number {
  return flows.reduce((s, x, i) => s + x / (1 + rate) ** (i + 1), 0);
}
