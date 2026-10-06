// Aggregation into the RBE table, net verdict, breakdowns, context, waterfall
// and per-entity results (brief sections 5-6; RBM pp. 5-6, 11).
import { annualAverage } from "./annualise";
import { point } from "./costing";
import { ZERO, dec, str, sum, type Dec } from "./decimal";
import { PARAMETERS } from "./parameters";
import type { ItemCalc } from "./reform";
import { EXCLUSIONS, type ExclusionReason } from "./scope";
import type { Group, Option, Proposal } from "./schema";
import type { ExcludedItem, ItemResult, OptionResult, PerEntityResult, RbeRow } from "./types";

const GROUPS: Group[] = ["business", "communityOrg", "individual"];
const COHORT_ORDER = ["small", "medium", "large"] as const;

type Baseline = "statusQuo" | "noInstrument";

function delta(item: ItemCalc, baseline: Baseline): Dec[] {
  return baseline === "statusQuo" ? item.deltaStatusQuo : item.deltaNoInstrument;
}

function totalOf(items: readonly ItemCalc[], baseline: Baseline): Dec {
  return sum(items.map((i) => sum(delta(i, baseline))));
}

function byYear(items: readonly ItemCalc[], baseline: Baseline, T: number): Dec[] {
  return Array.from({ length: T }, (_, t) => sum(items.map((i) => delta(i, baseline)[t] ?? ZERO)));
}

function rbeRow(items: readonly ItemCalc[], baseline: Baseline, T: number): RbeRow {
  const g = (group: Group) => totalOf(items.filter((i) => i.population.group === group), baseline).dividedBy(T);
  return {
    business: str(g("business")),
    communityOrg: str(g("communityOrg")),
    individual: str(g("individual")),
    total: str(totalOf(items, baseline).dividedBy(T)),
  };
}

function breakdown(items: readonly ItemCalc[], baseline: Baseline, T: number, key: (i: ItemCalc) => string) {
  const out: Record<string, Dec> = {};
  for (const item of items) {
    const k = key(item);
    out[k] = (out[k] ?? ZERO).plus(sum(delta(item, baseline)));
  }
  return Object.fromEntries(Object.entries(out).map(([k, v]) => [k, str(v.dividedBy(T))]));
}

/** Cohort pairs where a lower cohort is exempted but the next cohort gets no relief (brief section 6). */
export function findCliffs(proposal: Proposal, items: readonly ItemCalc[]): { obligationId: string; populationId: string }[] {
  const T = proposal.durationYears;
  const cliffs: { obligationId: string; populationId: string }[] = [];
  const obligations = new Map<string, ItemCalc[]>();
  for (const i of items.filter((x) => x.kind === "obligation" && !x.excluded)) {
    obligations.set(i.obligation.id, [...(obligations.get(i.obligation.id) ?? []), i]);
  }
  for (const [obligationId, its] of obligations) {
    const ob = its[0]?.obligation;
    if (!ob || !ob.current || !ob.reformed) continue; // a threshold is a modification, not a repeal
    const perEntity = (side: "current" | "reformed", pid: string) => {
      const it = its.find((i) => i.side === side && i.population.id === pid);
      if (!it || it.effectiveEntities.isZero()) return ZERO;
      return annualAverage(it.net, T).dividedBy(it.effectiveEntities);
    };
    const pops = proposal.populations.filter((p) => its.some((i) => i.population.id === p.id && i.side === "current"));
    for (const lower of pops) {
      const idx = COHORT_ORDER.indexOf(lower.cohort as (typeof COHORT_ORDER)[number]);
      if (idx < 0 || idx === COHORT_ORDER.length - 1) continue;
      const cur = its.find((i) => i.side === "current" && i.population.id === lower.id);
      const ref = its.find((i) => i.side === "reformed" && i.population.id === lower.id);
      const exempt = cur && sum(cur.net).greaterThan(0) && (!ref || sum(ref.net).isZero());
      if (!exempt) continue;
      const nextCohort = COHORT_ORDER[idx + 1];
      for (const upper of pops.filter(
        (p) => p.group === lower.group && p.cohort === nextCohort && (p.industry ?? "") === (lower.industry ?? ""),
      )) {
        const before = perEntity("current", upper.id);
        const after = perEntity("reformed", upper.id);
        if (before.greaterThan(0) && after.greaterThanOrEqualTo(before)) cliffs.push({ obligationId, populationId: upper.id });
      }
    }
  }
  return cliffs;
}

function excludedItems(option: Option, items: readonly ItemCalc[], T: number): ExcludedItem[] {
  const out: ExcludedItem[] = [];
  const add = (item: ItemCalc, reason: ExclusionReason, total: Dec) => {
    if (total.isZero()) return;
    const ex = EXCLUSIONS[reason];
    out.push({
      optionId: option.id,
      obligationId: item.obligation.id,
      obligationName: item.obligation.name,
      side: item.side,
      populationId: item.population.id,
      reason,
      label: ex.label,
      explanation: ex.explanation,
      ref: ex.ref,
      annualAmount: str(total.dividedBy(T)),
    });
  };
  for (const item of items) {
    if (item.excluded) add(item, item.excluded, sum(item.gross));
    else {
      add(item, "enforcement", sum(item.enforcementExcluded));
      add(item, "subsidyExcess", item.subsidyExcess);
    }
  }
  return out;
}

function toItemResult(option: Option, item: ItemCalc, baseline: Baseline, T: number): ItemResult {
  const alt: Baseline = baseline === "statusQuo" ? "noInstrument" : "statusQuo";
  const s = (xs: Dec[]) => xs.map(str);
  const r: ItemResult = {
    optionId: option.id,
    obligationId: item.obligation.id,
    obligationName: item.obligation.name,
    kind: item.kind,
    side: item.side,
    populationId: item.population.id,
    group: item.population.group,
    cohort: item.population.cohort,
    entityType: item.population.entityType,
    category: item.obligation.category,
    costType: item.sideSpec.costType,
    timingType: item.kind === "transition" ? "transition" : item.sideSpec.timing.type,
    jurisdiction: item.obligation.jurisdiction,
    formula: item.formula,
    inputs: item.inputs,
    effectiveEntities: str(item.effectiveEntities),
    activeYearCost: str(item.activeYearCost),
    doAnywayShareApplied: str(item.doAnywayShare),
    grossByYear: s(item.gross),
    doAnywayByYear: s(item.doAnyway),
    enforcementExcludedByYear: s(item.enforcementExcluded),
    subsidyByYear: s(item.subsidy),
    netByYear: s(item.net),
    deltaByYear: s(delta(item, baseline)),
    deltaByYearAlternative: s(delta(item, alt)),
    deltaAnnual: str(sum(delta(item, baseline)).dividedBy(T)),
  };
  if (item.population.employmentBand) r.employmentBand = item.population.employmentBand;
  if (item.population.industry) r.industry = item.population.industry;
  if (item.obligation.legalReference) {
    r.legalInstrument = item.obligation.legalReference.instrument;
    if (item.obligation.legalReference.provision) r.legalProvision = item.obligation.legalReference.provision;
  }
  if (item.excluded) r.excluded = item.excluded;
  return r;
}

export function aggregateOption(proposal: Proposal, option: Option, items: ItemCalc[]): OptionResult {
  const T = proposal.durationYears;
  const baseline: Baseline = proposal.baseline;
  const alt: Baseline = baseline === "statusQuo" ? "noInstrument" : "statusQuo";

  const totalDec = totalOf(items, baseline);
  const annual = totalDec.dividedBy(T);

  // Gross increases and reductions at obligation × population level (DECISIONS #48).
  const pairs = new Map<string, Dec>();
  for (const i of items) {
    const k = `${i.kind}|${i.obligation.id}|${i.population.id}`;
    pairs.set(k, (pairs.get(k) ?? ZERO).plus(sum(delta(i, baseline))));
  }
  const pairValues = [...pairs.values()];
  const increases = sum(pairValues.filter((v) => v.greaterThan(0))).dividedBy(T);
  const reductions = sum(pairValues.filter((v) => v.lessThan(0))).dividedBy(T);

  // Context: steady-state regime costs (DECISIONS #49). Labelled "context, not RBE" in outputs.
  const live = items.filter((i) => !i.excluded);
  const netAnnual = (xs: ItemCalc[]) => sum(xs.map((i) => sum(i.net))).dividedBy(T);
  const currentAnnual = netAnnual(live.filter((i) => i.kind === "obligation" && i.side === "current"));
  const reformedAnnual = netAnnual(live.filter((i) => i.kind === "obligation" && i.side === "reformed"));
  const transitions = items.filter((i) => i.kind === "transition");
  const transitionAnnual = totalOf(transitions, baseline).dividedBy(T);
  const share = (x: Dec) => (currentAnnual.greaterThan(0) ? str(x.dividedBy(currentAnnual)) : null);

  // Waterfall: current regime → removed → reduced → increased → new → transition (status quo comparison).
  const steps = { removed: ZERO, reduced: ZERO, increased: ZERO, newObligations: ZERO };
  for (const ob of option.obligations) {
    const v = totalOf(items.filter((i) => i.kind === "obligation" && i.obligation.id === ob.id), "statusQuo").dividedBy(T);
    if (ob.current && !ob.reformed) steps.removed = steps.removed.plus(v);
    else if (!ob.current && ob.reformed) steps.newObligations = steps.newObligations.plus(v);
    else if (v.lessThan(0)) steps.reduced = steps.reduced.plus(v);
    else steps.increased = steps.increased.plus(v);
  }
  const transitionStatusQuo = totalOf(transitions, "statusQuo").dividedBy(T);
  const end = currentAnnual.plus(steps.removed).plus(steps.reduced).plus(steps.increased).plus(steps.newObligations).plus(transitionStatusQuo);

  // Per-entity results by population (cohort), with threshold cliff flags.
  const cliffs = findCliffs(proposal, items);
  const perEntity: PerEntityResult[] = proposal.populations
    .filter((p) => items.some((i) => i.population.id === p.id))
    .map((p) => {
      const its = items.filter((i) => i.population.id === p.id);
      const count = point(p.count);
      const per = (x: Dec) => (count.isZero() ? ZERO : x.dividedBy(count));
      const its2 = its.filter((i) => !i.excluded && i.kind === "obligation");
      return {
        populationId: p.id,
        label: p.label,
        group: p.group,
        cohort: p.cohort,
        count: str(count),
        currentAnnualPerEntity: str(per(netAnnual(its2.filter((i) => i.side === "current")))),
        reformedAnnualPerEntity: str(per(netAnnual(its2.filter((i) => i.side === "reformed")))),
        changePerEntity: str(per(totalOf(its, baseline).dividedBy(T))),
        cliffFlag: cliffs.some((c) => c.populationId === p.id),
      };
    });

  const tenYearTotal = totalDec;
  const threshold = dec(PARAMETERS.thresholds.iaThreshold1TenYearTotal);
  const altTotal = totalOf(items, alt);

  return {
    optionId: option.id,
    optionName: option.name,
    isStatusQuo: option.isStatusQuo,
    baseline,
    rbe: rbeRow(items, baseline, T),
    tenYearTotal: str(tenYearTotal),
    deltaByYear: byYear(items, baseline, T).map(str),
    alternativeBaseline: {
      baseline: alt,
      rbe: rbeRow(items, alt, T),
      tenYearTotal: str(altTotal),
      deltaByYear: byYear(items, alt, T).map(str),
    },
    verdict: {
      kind: annual.isZero() ? "none" : annual.greaterThan(0) ? "increase" : "reduction",
      amount: str(annual.abs()),
    },
    gross: { increases: str(increases), reductions: str(reductions) },
    context: {
      currentAnnual: str(currentAnnual),
      reformedAnnual: str(reformedAnnual),
      transitionAnnual: str(transitionAnnual),
      shareRemoved: share(currentAnnual.minus(reformedAnnual)),
      shareRemovedNetOfTransition: share(currentAnnual.minus(reformedAnnual).minus(transitionAnnual)),
    },
    waterfall: [
      { step: "current", label: "Current regime (annual cost)", value: str(currentAnnual) },
      { step: "removed", label: "Obligations removed", value: str(steps.removed) },
      { step: "reduced", label: "Obligations reduced", value: str(steps.reduced) },
      { step: "increased", label: "Obligations increased", value: str(steps.increased) },
      { step: "new", label: "New replacement obligations", value: str(steps.newObligations) },
      { step: "transition", label: "Transition costs", value: str(transitionStatusQuo) },
      { step: "end", label: "Current regime + net change", value: str(end) },
    ],
    breakdowns: {
      group: breakdown(items, baseline, T, (i) => i.population.group),
      category: breakdown(items, baseline, T, (i) => i.obligation.category),
      cohort: breakdown(items, baseline, T, (i) => i.population.cohort),
      timing: breakdown(items, baseline, T, (i) => (i.kind === "transition" ? "transition" : i.sideSpec.timing.type)),
      jurisdiction: breakdown(items, baseline, T, (i) => i.obligation.jurisdiction),
      obligation: breakdown(items, baseline, T, (i) => i.obligation.id),
    },
    jurisdictionSplit: {
      commonwealth: str(totalOf(items.filter((i) => i.obligation.jurisdiction === "commonwealth"), baseline).dividedBy(T)),
      stateTerritory: str(totalOf(items.filter((i) => i.obligation.jurisdiction === "stateTerritory"), baseline).dividedBy(T)),
    },
    perEntity,
    iaThreshold1: {
      tenYearTotal: str(tenYearTotal),
      threshold: str(threshold),
      likelyMet: tenYearTotal.abs().greaterThanOrEqualTo(threshold),
      note: "IA threshold 1 is a change in regulatory burden of $20 million or more over 10 years (IA Framework Practical Guide p. 7). Indicative only: confirm with OIA.",
    },
    items: items.map((i) => toItemResult(option, i, baseline, T)),
    excluded: excludedItems(option, items, T),
  };
}

export { GROUPS };
