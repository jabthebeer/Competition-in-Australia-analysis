// Exact decimal arithmetic for all money calculations (DECISIONS #33).
// Values never pass through binary floating point: inputs are converted from
// their shortest decimal string, and outputs are exact decimal strings.
import Decimal from "decimal.js";

export const D = Decimal.clone({
  precision: 40,
  rounding: Decimal.ROUND_HALF_EVEN,
  toExpNeg: -60,
  toExpPos: 60,
});

export type Dec = Decimal;

export const ZERO: Dec = new D(0);
export const ONE: Dec = new D(1);

/** Converts a JSON number (or decimal string) to an exact Decimal. */
export function dec(value: number | string | Dec): Dec {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new RangeError(`Not a finite number: ${value}`);
    return new D(String(value));
  }
  return new D(value);
}

export function sum(values: readonly Dec[]): Dec {
  let total = ZERO;
  for (const v of values) total = total.plus(v);
  return total;
}

export function max(a: Dec, b: Dec): Dec {
  return a.greaterThanOrEqualTo(b) ? a : b;
}

export function min(a: Dec, b: Dec): Dec {
  return a.lessThanOrEqualTo(b) ? a : b;
}

/** Exact decimal string, never in exponent notation. */
export function str(value: Dec): string {
  return value.toFixed();
}

export function zeros(length: number): Dec[] {
  return Array.from({ length }, () => ZERO);
}

export function addProfiles(a: readonly Dec[], b: readonly Dec[]): Dec[] {
  return a.map((v, i) => v.plus(b[i] ?? ZERO));
}

export function scaleProfile(profile: readonly Dec[], factor: Dec): Dec[] {
  return profile.map((v) => v.times(factor));
}
