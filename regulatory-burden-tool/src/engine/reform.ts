// Current-vs-reformed comparison, obligation by obligation (brief section 6).
// Every proposal type is a comparison: new regulation has no current sides,
// outright repeal has no reformed sides.
import { annualAverage, shiftProfile, timingFactors } from "./annualise";
import { lineCost, point, type ResolvedRate } from "./costing";
import { ONE, ZERO, dec, min, scaleProfile, sum, zeros, type Dec } from "./decimal";
import { tagExclusion, type ExclusionReason } from "./scope";
import type { Line, Obligation, Option, Population, Proposal, Side } from "./schema";
import type { ItemKind, ItemSide } from "./types";

/** Internal per-item calculation, in exact decimals. */
export interface ItemCalc {
  obligation: Obligation;
  kind: ItemKind;
  side: ItemSide;
  sideSpec: Side;
  line: Line;
  population: Population;
  rate?: ResolvedRate;
  formula: string;
  inputs: Record<string, string>;
  effectiveEntities: Dec;
  activeYearCost: Dec;
  factors: Dec[];
  gross: Dec[];
  doAnywayShare: Dec;
  doAnyway: Dec[];
  complianceShare: Dec;
  enforcementExcluded: Dec[];
  subsidy: Dec[];
  subsidyExcess: Dec;
  /** In-scope regime cost (steady state: current unmasked, reformed unshifted). */
  net: Dec[];
  deltaStatusQuo: Dec[];
  deltaNoInstrument: Dec[];
  excluded?: ExclusionReason;
  reformStartYear: number;
  overlapYears: number;
}

/** The share of an obligation counted as compliance under Appendix 3 (R-55 to R-60). */
export function complianceShareOf(obligation: Obligation): Dec {
  const s = obligation.scope;
  if (s.classification === "compliance") return ONE;
  if (s.classification === "enforcement") return ZERO;
  return dec(s.complianceShare ?? 1);
}

function wholeItemExclusion(
  proposal: Proposal,
  obligation: Obligation,
  sideName: ItemSide,
  side: Side,
  line: Line,
  population: Population,
): ExclusionReason | undefined {
  if (sideName === "current" && side.status === "alreadyIncurred") return "sunk";
  const tagged = tagExclusion(obligation.tags, side.costType);
  if (tagged) return tagged;
  if (side.costType === "delay" && line.delay && !line.delay.waitingOnGovernment) return "delayNotWaitingOnGovernment";
  if (population.entityType === "governmentAgency") return "governmentToGovernment";
  if (obligation.jurisdiction === "stateTerritory" && proposal.jurisdiction === "commonwealthOnly") {
    return "stateInCommonwealthOnly";
  }
  return undefined;
}

/** Per-entity average gross cost of an item over the analysis window. */
function perEntityAverage(item: ItemCalc, durationYears: number): Dec {
  if (item.effectiveEntities.isZero()) return ZERO;
  return annualAverage(item.gross, durationYears).dividedBy(item.effectiveEntities);
}

/**
 * Do-anyway adjustment (A-03). Businesses bear only the cost above the do-anyway
 * level = do-anyway share × today's cost per business. The reference version is
 * the current one (or the reformed one for a new obligation). The other version's
 * effective share is min(1, do-anyway level ÷ its own cost per business).
 */
export function doAnywayShares(
  share: Dec,
  reference: ItemCalc | undefined,
  other: ItemCalc | undefined,
  durationYears: number,
): void {
  if (reference) reference.doAnywayShare = share;
  if (!other) return;
  if (!reference) {
    other.doAnywayShare = share;
    return;
  }
  const level = share.times(perEntityAverage(reference, durationYears));
  const own = perEntityAverage(other, durationYears);
  other.doAnywayShare = own.isZero() ? ZERO : min(ONE, level.dividedBy(own));
}

function buildItem(
  proposal: Proposal,
  option: Option,
  obligation: Obligation,
  kind: ItemKind,
  sideName: ItemSide,
  side: Side,
  line: Line,
): ItemCalc {
  const T = proposal.durationYears;
  const population = proposal.populations.find((p) => p.id === line.populationId);
  if (!population) throw new Error(`Unknown population "${line.populationId}"`);
  const cost = lineCost(line, side, population, proposal);
  const factors = timingFactors(side.timing, T);
  const gross = scaleProfile(factors, cost.activeYearCost);
  const item: ItemCalc = {
    obligation,
    kind,
    side: sideName,
    sideSpec: side,
    line,
    population,
    formula: cost.formula,
    inputs: cost.inputs,
    effectiveEntities: cost.effectiveEntities,
    activeYearCost: cost.activeYearCost,
    factors,
    gross,
    doAnywayShare: ZERO,
    doAnyway: zeros(T),
    complianceShare: complianceShareOf(obligation),
    enforcementExcluded: zeros(T),
    subsidy: zeros(T),
    subsidyExcess: ZERO,
    net: zeros(T),
    deltaStatusQuo: zeros(T),
    deltaNoInstrument: zeros(T),
    reformStartYear: obligation.timingOverride?.reformStartYear ?? option.timing.reformStartYear,
    overlapYears: obligation.timingOverride?.overlapYears ?? option.timing.overlapYears,
  };
  if (cost.rate) item.rate = cost.rate;
  const excluded = wholeItemExclusion(proposal, obligation, sideName, side, line, population);
  if (excluded) item.excluded = excluded;
  return item;
}

/** Applies the do-anyway share, enforcement split and subsidy to give the in-scope cost. */
function finaliseItem(item: ItemCalc): void {
  if (item.excluded) return;
  item.doAnyway = scaleProfile(item.gross, item.doAnywayShare);
  const adjusted = item.gross.map((g, i) => g.minus(item.doAnyway[i] ?? ZERO));
  const inScope = scaleProfile(adjusted, item.complianceShare);
  item.enforcementExcluded = adjusted.map((a, i) => a.minus(inScope[i] ?? ZERO));

  const subsidy = item.line.subsidy;
  if (subsidy) {
    const perYear = point(subsidy.perEntityPerActiveYear).times(item.effectiveEntities);
    let applied = scaleProfile(item.factors, perYear);
    const offered = sum(applied);
    const cost = sum(inScope);
    if (offered.greaterThan(cost)) {
      // Cap at the cost it offsets (A-06): the net cost can fall to zero, not below.
      item.subsidyExcess = offered.minus(cost);
      applied = offered.isZero() ? applied : scaleProfile(applied, cost.dividedBy(offered));
    }
    item.subsidy = applied;
  }
  item.net = inScope.map((v, i) => v.minus(item.subsidy[i] ?? ZERO));
}

/**
 * Contribution of an item to the change in burden (A-04, DECISIONS #45).
 * Status quo baseline: Δ_t = reformed_t (shifted to the reform start) − current_t × [current no longer in force].
 * No-instrument baseline (sunsetting remake, N-01): Δ_t = reformed_t; current settings are not the comparison.
 */
function applyMasks(item: ItemCalc, T: number): void {
  if (item.excluded) return;
  if (item.side === "current") {
    const endsAfter = item.reformStartYear + item.overlapYears; // first year without the current obligation
    item.deltaStatusQuo = item.net.map((v, i) => (i + 1 >= endsAfter ? v.negated() : ZERO));
    item.deltaNoInstrument = zeros(T);
  } else {
    const shifted = shiftProfile(item.net, item.reformStartYear);
    item.deltaStatusQuo = shifted;
    item.deltaNoInstrument = shifted;
  }
}

/** Builds and calculates every item (obligation side × population line) in an option. */
export function computeOptionItems(proposal: Proposal, option: Option): ItemCalc[] {
  const T = proposal.durationYears;
  const items: ItemCalc[] = [];
  const groups: { obligation: Obligation; kind: ItemKind }[] = [
    ...option.obligations.map((o) => ({ obligation: o, kind: "obligation" as const })),
    ...option.transitions.map((o) => ({ obligation: o, kind: "transition" as const })),
  ];
  for (const { obligation, kind } of groups) {
    const current = (obligation.current?.lines ?? []).map((line) =>
      buildItem(proposal, option, obligation, kind, "current", obligation.current as Side, line),
    );
    const reformed = (obligation.reformed?.lines ?? []).map((line) =>
      buildItem(proposal, option, obligation, kind, "reformed", obligation.reformed as Side, line),
    );
    const share = point(obligation.doAnywayShare);
    const populationIds = new Set([...current, ...reformed].map((i) => i.population.id));
    for (const pid of populationIds) {
      const cur = current.find((i) => i.population.id === pid && !i.excluded);
      const ref = reformed.find((i) => i.population.id === pid && !i.excluded);
      doAnywayShares(share, cur ?? ref, cur ? ref : undefined, T);
    }
    for (const item of [...current, ...reformed]) {
      finaliseItem(item);
      applyMasks(item, T);
      items.push(item);
    }
  }
  return items;
}

// ---------------------------------------------------------------------------
// "Users only edit what changes" (brief section 6): copy-on-reform and diffs.

/** Returns the obligation with its reformed side set to an exact copy of the current side. */
export function copyCurrentToReformed(obligation: Obligation): Obligation {
  if (!obligation.current) throw new Error(`"${obligation.name}" has no current side to copy`);
  const { status: _status, ...current } = obligation.current;
  return { ...obligation, reformed: structuredClone(current) };
}

export interface FieldChange {
  path: string;
  current: unknown;
  reformed: unknown;
}

function flatten(value: unknown, prefix: string, out: Map<string, unknown>): void {
  if (Array.isArray(value)) {
    value.forEach((v, i) => flatten(v, `${prefix}[${i}]`, out));
  } else if (value !== null && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) flatten(v, prefix ? `${prefix}.${k}` : k, out);
  } else {
    out.set(prefix, value);
  }
}

/**
 * Field-by-field differences between the current and reformed versions of an obligation.
 * Lines are matched by population, so reordering lines is not reported as a change.
 */
export function reformDiff(obligation: Obligation): FieldChange[] {
  const keyed = (side: Side | null) => {
    if (!side) return null;
    const { lines, status: _status, ...rest } = side;
    return { ...rest, lines: Object.fromEntries(lines.map((l) => [l.populationId, l])) };
  };
  const a = new Map<string, unknown>();
  const b = new Map<string, unknown>();
  flatten(keyed(obligation.current), "", a);
  flatten(keyed(obligation.reformed), "", b);
  const paths = [...new Set([...a.keys(), ...b.keys()])].sort();
  return paths
    .filter((p) => JSON.stringify(a.get(p)) !== JSON.stringify(b.get(p)))
    .map((p) => ({ path: p, current: a.get(p), reformed: b.get(p) }));
}
