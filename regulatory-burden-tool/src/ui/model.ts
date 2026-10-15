// Pure helpers for editing a proposal in the UI. They never mutate their inputs.
//
// The schema stores each option's obligations with both a current and a reformed side.
// The UI presents one shared "current regime", so these helpers keep the current side of
// every obligation identical across options, and let each reformed side follow the current
// one except for the fields the reform deliberately changes ("users only edit what changes").
import {
  PARAMETERS,
  copyCurrentToReformed,
  defaultRateTable,
  reformDiff,
  type CostType,
  type Line,
  type Obligation,
  type Option,
  type Population,
  type Proposal,
  type Side,
} from "../engine/index";

export type ProposalType = Proposal["proposalType"];
export type Category = Obligation["category"];
export type ReformStatus = "keep" | "modify" | "remove";

const clone = <T>(x: T): T => structuredClone(x);

let seq = 0;
/** A short unique id using only characters the schema allows. */
export function newId(prefix: string): string {
  seq += 1;
  return `${prefix}-${Date.now().toString(36)}${seq.toString(36)}${Math.floor(Math.random() * 1e4).toString(36)}`;
}

export function costTypeFor(category: Category): CostType {
  return category === "administrative" ? "labour" : category === "substantive" ? "purchase" : "delay";
}

export function newLine(costType: CostType, population: Population): Line {
  const base = { populationId: population.id, complianceRate: 1 };
  if (costType === "labour") {
    const individual = population.group === "individual";
    return { ...base, labour: { hours: 0, timesPerYear: 1, rateId: individual ? "leisure" : "work", ...(individual ? {} : { staff: 1 }) } };
  }
  if (costType === "purchase") return { ...base, purchase: { unitCost: 0, timesPerYear: 1 } };
  return {
    ...base,
    delay: { unit: "months", applicationDelay: 0, approvalDelay: 0, readyAfter: 0, netIncomePerUnit: 0, extraExpensesPerUnit: 0, waitingOnGovernment: true },
  };
}

export function newSide(costType: CostType, populations: readonly Population[]): Side {
  return { costType, timing: { type: "ongoing", startYear: 1 }, lines: populations.map((p) => newLine(costType, p)) };
}

/** Switches a side to another cost type, keeping who it applies to, entity counts and compliance rates. */
export function changeCostType(side: Side, costType: CostType, populations: readonly Population[]): Side {
  if (side.costType === costType) return side;
  return {
    ...clone(side),
    costType,
    lines: side.lines.map((l) => {
      const pop = populations.find((p) => p.id === l.populationId);
      const fresh = pop ? newLine(costType, pop) : newLine(costType, { id: l.populationId, label: "", group: "business", cohort: "all", count: 0, nonResident: false, entityType: "private" });
      const { labour: _l, purchase: _p, delay: _d, subsidy, ...keep } = l;
      return { ...keep, ...fresh, populationId: l.populationId, complianceRate: l.complianceRate, ...(keep.entities !== undefined ? { entities: keep.entities } : {}), ...(costType !== "delay" && subsidy ? { subsidy } : {}) };
    }),
  };
}

export function newObligation(
  category: Category,
  populations: readonly Population[],
  kind: "current" | "new" | "transition",
  name?: string,
): Obligation {
  const side = newSide(costTypeFor(category), populations.slice(0, 1));
  if (kind === "transition") side.timing = { type: "oneOff", year: 1 };
  const defaultName = kind === "transition" ? "Transition cost" : `${kind === "new" ? "New " : ""}${category === "administrative" ? "administrative" : category === "substantive" ? "substantive compliance" : "delay"} cost`;
  return {
    id: newId(kind === "transition" ? "t" : "ob"),
    name: name ?? defaultName.charAt(0).toUpperCase() + defaultName.slice(1),
    category,
    jurisdiction: "commonwealth",
    scope: { classification: "compliance" },
    doAnywayShare: 0,
    tags: [],
    levers: [],
    current: kind === "current" ? side : null,
    reformed: kind === "current" ? null : side,
  };
}

export function newPopulation(index: number): Population {
  return { id: newId("pop"), label: `Affected group ${index}`, group: "business", cohort: "all", count: 0, nonResident: false, entityType: "private" };
}

export function newOption(name: string, current: readonly Obligation[], template: "keep" | "repeal" = "keep"): Option {
  return {
    id: newId("opt"),
    name,
    isStatusQuo: false,
    timing: { reformStartYear: 1, overlapYears: 0 },
    obligations: current.map((o) => (template === "repeal" ? { ...clone(o), reformed: null, levers: ["removeObligation"] } : keepCopy(o))),
    transitions: [],
  };
}

function statusQuoOption(current: readonly Obligation[] = []): Option {
  return { id: "status-quo", name: "Status quo", isStatusQuo: true, timing: { reformStartYear: 1, overlapYears: 0 }, obligations: current.map(keepCopy), transitions: [] };
}

export function newProposal(type: ProposalType = "reform"): Proposal {
  const options: Option[] =
    type === "new"
      ? [{ ...newOption("Proposed regulation", []), id: "option-a" }]
      : type === "repeal"
        ? [{ ...newOption("Outright repeal", [], "repeal"), id: "repeal" }, statusQuoOption()]
        : [{ ...newOption("Option A: reformed regulation", []), id: "option-a" }, statusQuoOption()];
  return {
    id: newId("proposal"),
    title: "Untitled proposal",
    proposalType: type,
    durationYears: PARAMETERS.duration.defaultYears,
    jurisdiction: "commonwealthOnly",
    baseline: "statusQuo",
    parameterVintage: PARAMETERS.vintage,
    rates: defaultRateTable(),
    populations: [{ id: "pop-1", label: "Affected businesses", group: "business", cohort: "all", count: 0, nonResident: false, entityType: "private" }],
    options,
  };
}

/**
 * Changes the proposal type. While no obligations have been entered, the options are reset to
 * that type's defaults (e.g. "Outright repeal" + status quo); afterwards only the type changes.
 */
export function setProposalType(p: Proposal, type: ProposalType): Proposal {
  const empty = p.options.every((o) => o.obligations.length === 0 && o.transitions.length === 0);
  return empty ? { ...clone(p), proposalType: type, options: newProposal(type).options } : { ...clone(p), proposalType: type };
}

function keepCopy(o: Obligation): Obligation {
  return { ...copyCurrentToReformed(clone(o)), levers: [] };
}

// ---------------------------------------------------------------------------
// The shared current regime

/** The current regime: every obligation with a current side, in order, taken from the first option holding it. */
export function currentObligations(p: Proposal): Obligation[] {
  const seen = new Map<string, Obligation>();
  for (const opt of p.options) for (const o of opt.obligations) if (o.current && !seen.has(o.id)) seen.set(o.id, o);
  return [...seen.values()];
}

/**
 * An option that removes every existing obligation is treated as a repeal: obligations added to
 * the current regime later are removed there too. Otherwise new obligations start as "keep".
 */
function isRepealOption(p: Proposal, opt: Option): boolean {
  if (opt.isStatusQuo) return false;
  const existing = opt.obligations.filter((o) => o.current);
  if (existing.length > 0) return existing.every((o) => !o.reformed);
  return p.proposalType === "repeal";
}

export function addCurrentObligation(p: Proposal, ob: Obligation): Proposal {
  const next = clone(p);
  for (const opt of next.options) {
    const copy = clone(ob);
    opt.obligations.push(isRepealOption(p, opt) ? { ...copy, reformed: null, levers: ["removeObligation"] } : keepCopy(copy));
  }
  return next;
}

export function removeCurrentObligation(p: Proposal, id: string): Proposal {
  const next = clone(p);
  for (const opt of next.options) opt.obligations = opt.obligations.filter((o) => o.id !== id);
  return next;
}

/** Sets a value at a dotted path in a "keyed" side (lines keyed by population id); undefined deletes it. */
function setPath(target: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split(".");
  let node: Record<string, unknown> = target;
  for (const part of parts.slice(0, -1)) {
    if (typeof node[part] !== "object" || node[part] === null) node[part] = {};
    node = node[part] as Record<string, unknown>;
  }
  const last = parts[parts.length - 1]!;
  if (value === undefined) delete node[last];
  else node[last] = clone(value);
}

function prune(value: unknown): unknown {
  if (Array.isArray(value) || value === null || typeof value !== "object") return value;
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(value)) {
    const pv = prune(v);
    if (pv !== null && typeof pv === "object" && !Array.isArray(pv) && Object.keys(pv).length === 0) continue;
    out[k] = pv;
  }
  return out;
}

/**
 * Rebuilds a reformed side after the current side changed: the reformed side follows the new
 * current side, except for the fields the reform had changed. If the reform changed the cost
 * type or the timing pattern, those whole parts stay as the reform set them.
 */
export function rebaseReformed(oldCurrent: Side, oldReformed: Side, newCurrent: Side): Side {
  const changes = reformDiff({ current: oldCurrent, reformed: oldReformed } as Obligation);
  if (changes.some((c) => c.path === "costType")) return clone(oldReformed);
  const { status: _s, lines, ...rest } = clone(newCurrent);
  const keyed: Record<string, unknown> = { ...rest, lines: Object.fromEntries(lines.map((l) => [l.populationId, l])) };
  for (const c of changes) {
    if (c.path.startsWith("timing.")) continue;
    setPath(keyed, c.path, c.reformed);
  }
  if (changes.some((c) => c.path.startsWith("timing."))) keyed.timing = clone(oldReformed.timing);
  const pruned = prune(keyed) as Record<string, unknown> & { lines?: Record<string, Line> };
  const lineMap = pruned.lines ?? {};
  const order = [...lines.map((l) => l.populationId), ...oldReformed.lines.map((l) => l.populationId)];
  const outLines = [...new Set(order)].filter((pid) => lineMap[pid]).map((pid) => lineMap[pid]!);
  return { ...(pruned as unknown as Side), lines: outLines };
}

/**
 * Edits an obligation of the current regime in every option. Shared fields (name, category,
 * tags, do-anyway share, ...) and the current side change everywhere; each reformed side is
 * rebased so it keeps only its deliberate changes.
 */
export function updateCurrentObligation(p: Proposal, id: string, mutate: (o: Obligation) => void): Proposal {
  const next = clone(p);
  for (const opt of next.options) {
    opt.obligations = opt.obligations.map((o) => {
      if (o.id !== id || !o.current) return o;
      const before = clone(o);
      const edited = clone(o);
      mutate(edited);
      if (!edited.current) return edited;
      if (before.reformed) {
        const status = reformStatus(before);
        edited.reformed = status === "keep" ? copyCurrentToReformed(edited).reformed : rebaseReformed(before.current as Side, before.reformed, edited.current);
      } else {
        edited.reformed = null;
      }
      return edited;
    });
  }
  return next;
}

// ---------------------------------------------------------------------------
// Reform options

export function reformStatus(o: Obligation): ReformStatus {
  if (!o.reformed) return "remove";
  const levers = o.levers.filter((l) => l !== "removeObligation");
  return levers.length > 0 || reformDiff(o).length > 0 ? "modify" : "keep";
}

export function setReformStatus(p: Proposal, optionId: string, obligationId: string, status: ReformStatus): Proposal {
  return updateOptionObligation(p, optionId, obligationId, (o) => {
    if (status === "remove") {
      o.reformed = null;
      o.levers = ["removeObligation"];
    } else if (status === "keep") {
      Object.assign(o, keepCopy(o));
    } else {
      if (!o.reformed) o.reformed = copyCurrentToReformed(o).reformed;
      o.levers = o.levers.filter((l) => l !== "removeObligation");
      if (o.levers.length === 0) o.levers = ["other"];
    }
  });
}

/** Edits one obligation (or transition) within one option. */
export function updateOptionObligation(
  p: Proposal,
  optionId: string,
  obligationId: string,
  mutate: (o: Obligation) => void,
  list: "obligations" | "transitions" = "obligations",
): Proposal {
  const next = clone(p);
  const opt = next.options.find((o) => o.id === optionId);
  const ob = opt?.[list].find((o) => o.id === obligationId);
  if (ob) mutate(ob);
  return next;
}

export function addOptionObligation(p: Proposal, optionId: string, ob: Obligation, list: "obligations" | "transitions"): Proposal {
  const next = clone(p);
  next.options.find((o) => o.id === optionId)?.[list].push(clone(ob));
  return next;
}

export function removeOptionObligation(p: Proposal, optionId: string, obligationId: string, list: "obligations" | "transitions"): Proposal {
  const next = clone(p);
  const opt = next.options.find((o) => o.id === optionId);
  if (opt) opt[list] = opt[list].filter((o) => o.id !== obligationId);
  return next;
}

export function addOption(p: Proposal, name: string, template: "keep" | "repeal" = "keep"): Proposal {
  const next = clone(p);
  const opt = newOption(name, currentObligations(p), template);
  const sq = next.options.findIndex((o) => o.isStatusQuo);
  if (sq >= 0) next.options.splice(sq, 0, opt);
  else next.options.push(opt);
  return next;
}

export function removeOption(p: Proposal, optionId: string): Proposal {
  if (p.options.length <= 1) return p;
  const next = clone(p);
  next.options = next.options.filter((o) => o.id !== optionId);
  return next;
}

export function updateOption(p: Proposal, optionId: string, mutate: (o: Option) => void): Proposal {
  const next = clone(p);
  const opt = next.options.find((o) => o.id === optionId);
  if (opt) mutate(opt);
  return next;
}

// ---------------------------------------------------------------------------
// Populations

export function addPopulation(p: Proposal): Proposal {
  const next = clone(p);
  next.populations.push(newPopulation(p.populations.length + 1));
  return next;
}

export function updatePopulation(p: Proposal, id: string, mutate: (pop: Population) => void): Proposal {
  const next = clone(p);
  const pop = next.populations.find((x) => x.id === id);
  if (pop) mutate(pop);
  return next;
}

/** Obligations whose only line is for this population: removing it would leave them applying to no one. */
export function populationBlockers(p: Proposal, id: string): string[] {
  const names = new Set<string>();
  for (const opt of p.options) {
    for (const o of [...opt.obligations, ...opt.transitions]) {
      for (const side of [o.current, o.reformed]) {
        if (side && side.lines.length === 1 && side.lines[0]!.populationId === id) names.add(o.name || "(unnamed obligation)");
      }
    }
  }
  return [...names];
}

export function removePopulation(p: Proposal, id: string): Proposal {
  if (p.populations.length <= 1 || populationBlockers(p, id).length > 0) return p;
  const next = clone(p);
  next.populations = next.populations.filter((x) => x.id !== id);
  for (const opt of next.options) {
    for (const o of [...opt.obligations, ...opt.transitions]) {
      for (const side of [o.current, o.reformed]) if (side) side.lines = side.lines.filter((l) => l.populationId !== id);
    }
  }
  return next;
}

/** Adds or removes the line for a population on a side ("applies to"). Keeps at least one line. */
export function toggleLine(side: Side, population: Population, on: boolean): Side {
  const has = side.lines.some((l) => l.populationId === population.id);
  if (on && !has) return { ...side, lines: [...side.lines, newLine(side.costType, population)] };
  if (!on && has && side.lines.length > 1) return { ...side, lines: side.lines.filter((l) => l.populationId !== population.id) };
  return side;
}

/** Changes the analysis period, resizing any year-by-year schedules to match (extra years get 0). */
export function setDuration(p: Proposal, years: number): Proposal {
  const next = clone(p);
  next.durationYears = years;
  if (years === 10) delete next.durationOverride;
  for (const opt of next.options) {
    for (const o of [...opt.obligations, ...opt.transitions]) {
      for (const side of [o.current, o.reformed]) {
        if (side?.timing.type === "schedule") {
          side.timing.factors = Array.from({ length: years }, (_, i) => side.timing.type === "schedule" ? (side.timing.factors[i] ?? 0) : 0);
        }
      }
    }
  }
  return next;
}

/**
 * Turns a schema issue such as "options.0.obligations.1.reformed.lines.0.labour.hours: ..." into
 * plain language: "Option A › Quarterly report (reformed version) › Small firms: ...".
 */
export function describeIssue(p: Proposal, issue: string): string {
  const [path = "", ...rest] = issue.split(": ");
  const message = rest.join(": ");
  const parts = path.split(".");
  const out: string[] = [];
  let i = 0;
  if (parts[0] === "options" && parts[1] !== undefined) {
    const opt = p.options[Number(parts[1])];
    out.push(opt?.name || `Option ${Number(parts[1]) + 1}`);
    i = 2;
    if ((parts[2] === "obligations" || parts[2] === "transitions") && parts[3] !== undefined) {
      const ob = opt?.[parts[2]][Number(parts[3])];
      const side = parts[4] === "current" ? " (current regime)" : parts[4] === "reformed" ? " (reformed version)" : "";
      out.push(`${ob?.name || "Unnamed obligation"}${side}`);
      i = side ? 5 : 4;
      if (parts[i] === "lines" && parts[i + 1] !== undefined) {
        const sideObj = parts[4] === "current" ? ob?.current : ob?.reformed;
        const line = sideObj?.lines[Number(parts[i + 1])];
        out.push(p.populations.find((x) => x.id === line?.populationId)?.label || "a group");
        i += 2;
      }
    }
  } else if (parts[0] === "populations" && parts[1] !== undefined) {
    out.push(p.populations[Number(parts[1])]?.label || `Affected group ${Number(parts[1]) + 1}`);
    i = 2;
  }
  const field = parts.slice(i).filter((x) => !/^\d+$/.test(x)).join(" ");
  return `${[...out, field].filter(Boolean).join(" › ") || "Proposal"}: ${message || issue}`;
}

