// ANZSIC 2006 structure needed by the policy brief: which division a code belongs to,
// and whether one code covers another. Subdivision ranges follow the ABS codelist
// CL_ANZSIC_2006 1.1.0 (bundled in alicia/src/alicia/data/anzsic2006.json; a test checks
// this table against it). Whether a code exists is checked against the parameter file in P2.

/** First and last two-digit subdivision of each division. */
export const SUBDIVISION_RANGES = {
  A: [1, 5],
  B: [6, 10],
  C: [11, 25],
  D: [26, 29],
  E: [30, 32],
  F: [33, 38],
  G: [39, 43],
  H: [44, 45],
  I: [46, 53],
  J: [54, 60],
  K: [62, 64],
  L: [66, 67],
  M: [69, 70],
  N: [72, 73],
  O: [75, 77],
  P: [80, 82],
  Q: [84, 87],
  R: [89, 92],
  S: [94, 96],
} as const satisfies Record<string, readonly [number, number]>;

export type Division = keyof typeof SUBDIVISION_RANGES;

/** The division letter above any ANZSIC code (a division returns itself); undefined if outside every range. */
export function divisionOf(code: string): Division | undefined {
  if (/^[A-S]$/.test(code)) return code as Division;
  const sub = Number(code.slice(0, 2));
  for (const [div, [lo, hi]] of Object.entries(SUBDIVISION_RANGES)) {
    if (sub >= lo && sub <= hi) return div as Division;
  }
  return undefined;
}

/** True if `outer` is `inner` or one of its ancestors (e.g. "E" covers "3231", "32" covers "323"). */
export function covers(outer: string, inner: string): boolean {
  if (outer === inner) return true;
  if (/^[A-S]$/.test(outer)) return divisionOf(inner) === outer;
  return /^\d+$/.test(inner) && inner.length > outer.length && inner.startsWith(outer);
}

/** True if either code covers the other. */
export function overlaps(a: string, b: string): boolean {
  return covers(a, b) || covers(b, a);
}
