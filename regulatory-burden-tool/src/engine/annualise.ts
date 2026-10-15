// Year-by-year profiles and annualisation (RBM pp. 6, 8).
// Real terms only: there is no inflation, wage growth or discounting anywhere.
import { ONE, ZERO, dec, sum, type Dec } from "./decimal";
import type { Timing } from "./schema";

/**
 * The share of an activity's annual cost incurred in each year 1..T (index 0 = year 1).
 * One-off: 1 in its year. Ongoing: 1 from start to end. Every k years: 1 in each
 * occurrence year from firstYear (A-10). Schedule: as entered. Years beyond T are dropped.
 */
export function timingFactors(timing: Timing, durationYears: number): Dec[] {
  const T = durationYears;
  const factors: Dec[] = Array.from({ length: T }, () => ZERO);
  switch (timing.type) {
    case "oneOff":
      if (timing.year <= T) factors[timing.year - 1] = ONE;
      break;
    case "ongoing": {
      const end = Math.min(timing.endYear ?? T, T);
      for (let y = timing.startYear; y <= end; y++) factors[y - 1] = ONE;
      break;
    }
    case "everyKYears":
      for (let y = timing.firstYear; y <= T; y += timing.k) factors[y - 1] = ONE;
      break;
    case "schedule":
      timing.factors.slice(0, T).forEach((f, i) => (factors[i] = dec(f)));
      break;
  }
  return factors;
}

/**
 * Moves a profile so that its year 1 falls in `startYear` of the analysis window.
 * Used for reformed-side and transition costs, whose timing counts from the
 * reformed regime's start (DECISIONS #45). Values pushed past year T are dropped.
 */
export function shiftProfile(profile: readonly Dec[], startYear: number): Dec[] {
  const offset = startYear - 1;
  return profile.map((_, i) => (i - offset >= 0 ? (profile[i - offset] ?? ZERO) : ZERO));
}

/** Average annual value: total over the duration ÷ duration (RBM p. 6). */
export function annualAverage(profile: readonly Dec[], durationYears: number): Dec {
  return sum(profile).dividedBy(durationYears);
}

/** Years in which a timing pattern is active, for display ("years 1, 4, 7, 10"). */
export function activeYears(timing: Timing, durationYears: number): number[] {
  return timingFactors(timing, durationYears)
    .map((f, i) => (f.isZero() ? 0 : i + 1))
    .filter((y) => y > 0);
}
