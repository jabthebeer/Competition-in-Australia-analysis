// Single source of truth for framework defaults (RBM Appendix 2 and related).
// Updating the labour rates when OIA revises them is a one-file change here.
// All money values are decimal strings so they never pass through floating point.
import { D, dec } from "./decimal";

export const PARAMETERS = {
  vintage: "RBM-2026-07",

  framework: {
    title: "Regulatory Burden Measurement Framework",
    publisher: "Office of Impact Analysis (OIA), Department of the Prime Minister and Cabinet",
    release: "July 2026",
    url: "https://oia.pmc.gov.au/sites/default/files/2026-06/regulatory-burden-measurement-framework.pdf",
    sha256: "646848f921eff3a80f6366f1eb03dec61254a3a6f0190877f19e51f640c74ac8",
  },

  duration: {
    defaultYears: 10, // RBM p. 6
    minYears: 1,
    maxYearsWithoutOverride: 10, // RBM p. 6 only contemplates shorter periods (A-11)
    maxYears: 30,
  },

  rates: {
    work: {
      // RBM p. 12: $52.31 × 1.75 = $91.5425, published as $91.54 (A-02).
      base: "52.31",
      multiplier: "1.75",
      hourly: "91.54",
      ref: "RBM p. 12",
      source:
        "Based on average weekly earnings, adjusted to include income tax. ABS Employee Earnings and Hours, " +
        "released January 2024, Data Cube 6 (full-time non-managerial employees paid at the adult rate); " +
        "ATO Simple Tax Calculator, 2024-25 rates (RBM p. 12, fn 3-4). Multiplier covers on-costs and overheads.",
      nextUpdate: "February 2028 (yet to be confirmed, RBM p. 12, fn 2)",
    },
    leisure: {
      hourly: "41",
      ref: "RBM p. 13",
      source: "Average weekly earnings including overtime, after tax (RBM p. 13).",
      appliesTo: "Individuals residing in Australia (RBM p. 13, fn 5)",
      nextUpdate: "February 2028 (yet to be confirmed, RBM p. 12, fn 2)",
    },
    volunteer: {
      // DECISIONS #43: volunteers' time is non-work time, valued at the RBM non-work rate.
      hourly: "41",
      ref: "RBM pp. 9, 13; DECISIONS #43",
      source: "RBM non-work (leisure) rate applied to volunteer time.",
      nextUpdate: "Follows the non-work rate",
    },
  },

  // Size cohorts (RBM pp. 7-8 name them but do not define them; A-17, DECISIONS #18 and #50).
  // Bands follow ABS Counts of Australian Businesses (release of 18 August 2026).
  cohorts: {
    small: { minEmployees: 0, maxEmployees: 19 },
    medium: { minEmployees: 20, maxEmployees: 199 },
    large: { minEmployees: 200, maxEmployees: null },
  },
  employmentBands: {
    nonEmploying: { cohort: "small", maxEmployees: 0 },
    "1-4": { cohort: "small", maxEmployees: 4 },
    "5-19": { cohort: "small", maxEmployees: 19 },
    "20-199": { cohort: "medium", maxEmployees: 199 },
    "200+": { cohort: "large", maxEmployees: null },
  },

  thresholds: {
    // IA Framework Practical Guide p. 7: IA threshold 1 = change in burden of $20m+ over 10 years.
    iaThreshold1TenYearTotal: "20000000",
    // Net verdicts below this absolute amount are stated in dollars, not $ million (A-08).
    verdictInDollarsBelow: "50000",
  },

  plausibility: {
    maxTimesPerYearPerStaff: 365, // section 7 of the brief
    maxHoursPerOccurrence: 24,
  },
} as const;

export type Parameters = typeof PARAMETERS;
export type CohortName = keyof typeof PARAMETERS.cohorts;
export type EmploymentBand = keyof typeof PARAMETERS.employmentBands;

/** Derives an hourly work rate from a base wage and multiplier, rounded half-up to the cent (A-02). */
export function deriveWorkRate(base: string | number, multiplier: string | number): string {
  return dec(base).times(dec(multiplier)).toDecimalPlaces(2, D.ROUND_HALF_UP).toFixed(2);
}
