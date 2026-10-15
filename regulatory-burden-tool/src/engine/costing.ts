// Costing formulas (RBM pp. 8-10). Each function returns the gross cost in a
// year in which the activity occurs, before the do-anyway adjustment, the
// compliance/enforcement split and subsidies.
import { ONE, ZERO, dec, max, str, type Dec } from "./decimal";
import type { Line, Population, Proposal, Quantity, Side } from "./schema";

/** Point estimate of a quantity: the value, or the midpoint of a range (A-07). */
export function point(q: Quantity): Dec {
  return typeof q === "number" ? dec(q) : dec(q.low).plus(dec(q.high)).dividedBy(2);
}

export interface ResolvedRate {
  id: string;
  kind: "work" | "leisure" | "volunteer";
  hourly: Dec;
  label: string;
}

export function resolveRate(rateId: string, rates: Proposal["rates"]): ResolvedRate {
  if (rateId === "work") return { id: rateId, kind: "work", hourly: dec(rates.work.hourly), label: "Work-related" };
  if (rateId === "leisure") return { id: rateId, kind: "leisure", hourly: dec(rates.leisure.hourly), label: "Non-work (leisure)" };
  if (rateId === "volunteer") return { id: rateId, kind: "volunteer", hourly: dec(rates.volunteer.hourly), label: "Volunteer" };
  const custom = rates.custom.find((r) => r.id === rateId);
  if (!custom) throw new Error(`Unknown labour rate "${rateId}"`);
  return { id: rateId, kind: custom.kind, hourly: dec(custom.hourly), label: custom.label };
}

/**
 * Labour cost (RBM pp. 8-9):
 * businesses and community organisations = (time × rate) × (times performed × entities × staff);
 * individuals = (time × rate) × (times performed × individuals).
 */
export function labourCost(args: { hours: Dec; rate: Dec; timesPerYear: Dec; entities: Dec; staff: Dec }): Dec {
  return args.hours.times(args.rate).times(args.timesPerYear.times(args.entities).times(args.staff));
}

/** Purchase cost (RBM p. 9) = price × (times performed × entities). */
export function purchaseCost(args: { unitCost: Dec; timesPerYear: Dec; entities: Dec }): Dec {
  return args.unitCost.times(args.timesPerYear.times(args.entities));
}

/**
 * Effective delay (A-01): all times are measured from when the entity starts its
 * application. Only time spent waiting beyond the point the entity would otherwise
 * be ready to operate counts. RBM p. 10: approval 6 months, ready at 4 → 2 months.
 */
export function effectiveDelay(applicationDelay: Dec, approvalDelay: Dec, readyAfter: Dec): Dec {
  return max(ZERO, applicationDelay.plus(approvalDelay).minus(readyAfter));
}

/** Delay cost (RBM pp. 2-3, 10; A-01) = entities × effective delay × (net income forgone + extra expenses) per unit of time. */
export function delayCost(args: { entities: Dec; effectiveDelay: Dec; netIncomePerUnit: Dec; extraExpensesPerUnit: Dec }): Dec {
  return args.entities.times(args.effectiveDelay).times(args.netIncomePerUnit.plus(args.extraExpensesPerUnit));
}

export interface LineCost {
  /** Gross cost in a year in which the activity occurs. */
  activeYearCost: Dec;
  /** Entities incurring the cost: entities × expected compliance rate. */
  effectiveEntities: Dec;
  formula: string;
  inputs: Record<string, string>;
  /** Labour rate used (labour lines only). */
  rate?: ResolvedRate;
}

/** Entities affected on a line: the line's count (default: population count) × expected compliance rate (R-39, X-07). */
export function effectiveEntities(line: Line, population: Population): Dec {
  return point(line.entities ?? population.count).times(point(line.complianceRate));
}

export function lineCost(line: Line, side: Side, population: Population, proposal: Proposal): LineCost {
  const entities = effectiveEntities(line, population);
  const base = {
    entities: str(point(line.entities ?? population.count)),
    complianceRate: str(point(line.complianceRate)),
  };
  if (side.costType === "labour" && line.labour) {
    const rate = resolveRate(line.labour.rateId, proposal.rates);
    const isIndividual = population.group === "individual";
    const staff = isIndividual ? ONE : point(line.labour.staff ?? 1);
    const hours = point(line.labour.hours);
    const times = point(line.labour.timesPerYear);
    return {
      activeYearCost: labourCost({ hours, rate: rate.hourly, timesPerYear: times, entities, staff }),
      effectiveEntities: entities,
      rate,
      formula: isIndividual
        ? "(time × rate) × (times performed × individuals × compliance rate)"
        : "(time × rate) × (times performed × entities × compliance rate × staff)",
      inputs: { ...base, hours: str(hours), rate: str(rate.hourly), rateId: rate.id, timesPerYear: str(times), staff: str(staff) },
    };
  }
  if (side.costType === "purchase" && line.purchase) {
    const unitCost = point(line.purchase.unitCost);
    const times = point(line.purchase.timesPerYear);
    return {
      activeYearCost: purchaseCost({ unitCost, timesPerYear: times, entities }),
      effectiveEntities: entities,
      formula: "price × (times performed × entities × compliance rate)",
      inputs: { ...base, unitCost: str(unitCost), timesPerYear: str(times) },
    };
  }
  if (side.costType === "delay" && line.delay) {
    const d = line.delay;
    const eff = effectiveDelay(point(d.applicationDelay), point(d.approvalDelay), point(d.readyAfter));
    const income = point(d.netIncomePerUnit);
    const extra = point(d.extraExpensesPerUnit);
    return {
      activeYearCost: delayCost({ entities, effectiveDelay: eff, netIncomePerUnit: income, extraExpensesPerUnit: extra }),
      effectiveEntities: entities,
      formula: `entities × compliance rate × max(0, application + approval − ready) × (net income forgone + extra expenses) per ${d.unit.replace(/s$/, "")}`,
      inputs: {
        ...base,
        unit: d.unit,
        applicationDelay: str(point(d.applicationDelay)),
        approvalDelay: str(point(d.approvalDelay)),
        readyAfter: str(point(d.readyAfter)),
        effectiveDelay: str(eff),
        netIncomePerUnit: str(income),
        extraExpensesPerUnit: str(extra),
      },
    };
  }
  throw new Error(`Line for population "${line.populationId}" has no ${side.costType} block`);
}
