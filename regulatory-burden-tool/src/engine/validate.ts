// Non-blocking warnings (brief section 7) and the assumptions register.
// Structural errors are caught earlier by the schema; nothing here stops a calculation.
import { point, resolveRate } from "./costing";
import { dec, str } from "./decimal";
import { findCliffs } from "./aggregate";
import { PARAMETERS, deriveWorkRate } from "./parameters";
import type { ItemCalc } from "./reform";
import type { Obligation, Option, Proposal, Side, Timing } from "./schema";
import type { AssumptionRow, Warning, WarningCode } from "./types";

export const WARNING_CATALOGUE: Record<WarningCode, { title: string; ref: string }> = {
  "W-01": { title: "Fee, levy, charge or tax entered as a purchase cost", ref: "RBM pp. 2, 4" },
  "W-02": { title: "Outsourced professional service entered as labour", ref: "RBM p. 12" },
  "W-03": { title: "Delay cost where the entity isn't waiting on government", ref: "RBM p. 10" },
  "W-04": { title: "Leisure rate applied to non-resident individuals", ref: "RBM p. 13, fn 5" },
  "W-05": { title: "Default rate overridden without a justification", ref: "RBM p. 12" },
  "W-06": { title: "Labour rate differs between current and reformed versions", ref: "RBM p. 6; DECISIONS #3" },
  "W-07": { title: "Do-anyway share of 0% on common industry practice", ref: "RBM pp. 3, 6" },
  "W-08": { title: "Start-up cost on the current regime: check whether it is sunk", ref: "DECISIONS #6" },
  "W-09": { title: "Reform with no transition costs", ref: "RBM p. 8" },
  "W-10": { title: "Exemption threshold creates a cliff effect", ref: "RBM pp. 7-8" },
  "W-11": { title: "Implausible input", ref: "RBM p. 7" },
  "W-12": { title: "Subsidy larger than the cost it offsets", ref: "RBM p. 3" },
  "W-13": { title: "Government-to-government obligation", ref: "RBM pp. 4-5" },
  "W-14": { title: "Compliance or enforcement classification needs attention", ref: "RBM pp. 14-15" },
  "W-15": { title: "State or territory cost in a Commonwealth-only proposal", ref: "RBM p. 6" },
  "W-16": { title: "Duration differs from the 10-year default without a justification", ref: "RBM p. 6" },
  "W-17": { title: "Delay costs: seek OIA advice", ref: "RBM p. 10" },
  "W-18": { title: "Proposal saved with a different parameter vintage", ref: "RBM p. 12, fn 2" },
  "W-19": { title: "Expected compliance rate differs between versions", ref: "RBM pp. 8-9" },
  "W-20": { title: "Timing falls outside the analysis period", ref: "RBM p. 6" },
  "W-21": { title: "Baseline doesn't match how the change will be made", ref: "IA Framework Practical Guide pp. 21-22" },
};

interface Ctx {
  option?: Option;
  obligation?: Obligation;
  populationId?: string;
}

function warn(code: WarningCode, message: string, ctx: Ctx = {}, severity: Warning["severity"] = "warning"): Warning {
  const w: Warning = { code, severity, message, ref: WARNING_CATALOGUE[code].ref };
  if (ctx.option) w.optionId = ctx.option.id;
  if (ctx.obligation) w.obligationId = ctx.obligation.id;
  if (ctx.populationId) w.populationId = ctx.populationId;
  return w;
}

function timingStart(t: Timing): number {
  switch (t.type) {
    case "oneOff":
      return t.year;
    case "ongoing":
      return t.startYear;
    case "everyKYears":
      return t.firstYear;
    case "schedule":
      return 1;
  }
}

function sides(o: Obligation): [("current" | "reformed"), Side][] {
  const out: [("current" | "reformed"), Side][] = [];
  if (o.current) out.push(["current", o.current]);
  if (o.reformed) out.push(["reformed", o.reformed]);
  return out;
}

function rateWarnings(p: Proposal): Warning[] {
  const out: Warning[] = [];
  const d = PARAMETERS.rates;
  const r = p.rates;
  const workDefault =
    dec(r.work.hourly).equals(d.work.hourly) && dec(r.work.base).equals(d.work.base) && dec(r.work.multiplier).equals(d.work.multiplier);
  if (!workDefault && !r.work.override) {
    out.push(warn("W-05", `The work-related rate ($${r.work.hourly}/h) differs from the default ($${d.work.hourly}/h). Record a justification and source.`));
  }
  const derived = deriveWorkRate(r.work.base, r.work.multiplier);
  if (!dec(derived).equals(r.work.hourly)) {
    out.push(warn("W-05", `The work-related rate ($${r.work.hourly}/h) doesn't equal base × multiplier ($${r.work.base} × ${r.work.multiplier} = $${derived}/h).`));
  }
  if (!dec(r.leisure.hourly).equals(d.leisure.hourly) && !r.leisure.override) {
    out.push(warn("W-05", `The non-work rate ($${r.leisure.hourly}/h) differs from the default ($${d.leisure.hourly}/h). Record a justification and source; OIA asks to be consulted on different leisure rates (RBM p. 13).`));
  }
  if (!dec(r.volunteer.hourly).equals(d.volunteer.hourly) && !r.volunteer.override) {
    out.push(warn("W-05", `The volunteer rate ($${r.volunteer.hourly}/h) differs from the default ($${d.volunteer.hourly}/h). Record a justification and source.`));
  }
  return out;
}

function obligationWarnings(p: Proposal, option: Option, o: Obligation, isTransition: boolean): Warning[] {
  const out: Warning[] = [];
  const ctx = { option, obligation: o };
  const T = p.durationYears;
  const pop = (id: string) => p.populations.find((x) => x.id === id);

  for (const [sideName, side] of sides(o)) {
    if (side.costType === "purchase" && (o.tags.includes("governmentFee") || o.tags.includes("tax"))) {
      out.push(warn("W-01", `"${o.name}" is a fee, levy, charge or tax paid to government. The amount is excluded from the RBE. The time spent paying it is an administrative cost: enter that as labour.`, ctx));
    }
    if (side.costType === "labour" && o.tags.includes("outsourcedService")) {
      out.push(warn("W-02", `"${o.name}" is tagged as an outsourced service but entered as labour. Outsourced services (e.g. accountants, lawyers) are purchase costs.`, ctx));
    }
    if (sideName === "current" && side.timing.type === "oneOff") {
      if (side.status === "alreadyIncurred") {
        out.push(warn("W-08", `"${o.name}" (current regime) is marked as already incurred, so it is sunk and excluded: removing it can't save anything.`, ctx, "info"));
      } else if (side.status === undefined) {
        out.push(warn("W-08", `"${o.name}" has a one-off cost on the current regime. If it has already been incurred it is sunk and isn't a saving: mark it as already incurred. Future one-off costs (e.g. new entrants, scheduled replacements) are avoidable.`, ctx));
      }
    }
    if (timingStart(side.timing) > T) {
      out.push(warn("W-20", `"${o.name}" (${sideName}) starts after year ${T}, so it falls outside the analysis period and isn't counted.`, ctx, "info"));
    }
    for (const line of side.lines) {
      const population = pop(line.populationId);
      if (!population) continue;
      const lctx = { ...ctx, populationId: population.id };
      if (line.delay) {
        if (!line.delay.waitingOnGovernment) {
          out.push(warn("W-03", `"${o.name}": delay costs count only while the entity is waiting on government action to commence operating. This line is excluded.`, lctx));
        } else {
          out.push(warn("W-17", `"${o.name}" includes delay costs. The framework asks agencies to contact OIA for guidance on delay costs.`, lctx, "info"));
        }
      }
      if (line.labour) {
        const rate = resolveRate(line.labour.rateId, p.rates);
        if (population.nonResident && (rate.kind === "leisure" || rate.kind === "volunteer")) {
          out.push(warn("W-04", `"${o.name}": the $${p.rates.leisure.hourly}/h non-work rate applies only to individuals residing in Australia. Use a rate based on the country where "${population.label}" live.`, lctx));
        }
        if (point(line.labour.timesPerYear).greaterThan(PARAMETERS.plausibility.maxTimesPerYearPerStaff)) {
          out.push(warn("W-11", `"${o.name}": performed more than ${PARAMETERS.plausibility.maxTimesPerYearPerStaff} times a year per staff member. Check that times performed is per staff member, not per business.`, lctx));
        }
        if (point(line.labour.hours).greaterThan(PARAMETERS.plausibility.maxHoursPerOccurrence)) {
          out.push(warn("W-11", `"${o.name}": more than ${PARAMETERS.plausibility.maxHoursPerOccurrence} hours per occurrence per staff member. Check the time required.`, lctx));
        }
        if (population.group === "individual" && line.labour.staff !== undefined && !point(line.labour.staff).equals(1)) {
          out.push(warn("W-11", `"${o.name}": the individuals formula has no staff factor (RBM p. 9), so the staff value is ignored.`, lctx));
        }
        if (population.group !== "individual" && population.cohort !== "all" && line.labour.staff !== undefined) {
          const maxStaff = PARAMETERS.cohorts[population.cohort].maxEmployees;
          if (maxStaff !== null && point(line.labour.staff).greaterThan(maxStaff)) {
            out.push(warn("W-11", `"${o.name}": ${str(point(line.labour.staff))} staff per entity is more than a ${population.cohort} entity can have (up to ${maxStaff} employees).`, lctx));
          }
        }
      }
      if (population.entityType === "governmentAgency") {
        out.push(warn("W-13", `"${o.name}" falls on a government agency ("${population.label}"). Government-to-government policy is excluded unless the entity is a GBE, a public university or a foreign-government-owned business.`, lctx));
      }
    }
  }

  if (o.jurisdiction === "stateTerritory" && p.jurisdiction === "commonwealthOnly") {
    out.push(warn("W-15", `"${o.name}" is a state or territory cost, but the proposal is Commonwealth-only, so it is excluded. Mark the proposal as inter-jurisdictional if it is a National Cabinet or ministerial council reform.`, ctx));
  }
  if (o.tags.includes("commonIndustryPractice") && point(o.doAnywayShare).isZero()) {
    out.push(warn("W-07", `"${o.name}" is tagged as common industry practice but its do-anyway share is 0%. Only the cost above what businesses would do anyway should count.`, ctx));
  }
  if (o.scope.classification !== "compliance" && !o.scope.override) {
    out.push(warn("W-14", `"${o.name}" is classified as ${o.scope.classification === "split" ? "partly " : ""}enforcement. Agencies must clearly demonstrate this to depart from the default (compliance): record a justification.`, ctx));
  }
  if (o.tags.includes("enforcementActivity") && o.scope.classification === "compliance") {
    out.push(warn("W-14", `"${o.name}" is tagged as an enforcement activity but classified as compliance, so it is counted in the RBE. Reclassify it if it is enforcement.`, ctx));
  }
  if (o.current && o.reformed && !isTransition) {
    for (const cl of o.current.lines) {
      const rl = o.reformed.lines.find((l) => l.populationId === cl.populationId);
      if (!rl) continue;
      if (cl.labour && rl.labour) {
        const a = resolveRate(cl.labour.rateId, p.rates).hourly;
        const b = resolveRate(rl.labour.rateId, p.rates).hourly;
        if (!a.equals(b) && !o.rateChangeJustification) {
          out.push(warn("W-06", `"${o.name}": the labour rate changes from $${str(a)}/h to $${str(b)}/h between versions. Use the same rate unless the change is deliberate and justified, or the reform will look cheaper only because the rate changed.`, { ...ctx, populationId: cl.populationId }));
        }
      }
      if (!point(cl.complianceRate).equals(point(rl.complianceRate))) {
        out.push(warn("W-19", `"${o.name}": the expected compliance rate differs between versions. Check this is intended.`, { ...ctx, populationId: cl.populationId }, "info"));
      }
    }
  }
  return out;
}

/** Collects every warning for a calculated proposal. */
export function collectWarnings(p: Proposal, computed: { option: Option; items: ItemCalc[] }[]): Warning[] {
  const out: Warning[] = [...rateWarnings(p)];
  if (p.durationYears !== PARAMETERS.duration.defaultYears && !p.durationOverride) {
    out.push(warn("W-16", `The duration is ${p.durationYears} years. The default is 10 years; a shorter period suits a policy that ends sooner (RBM p. 6). Record a justification.`));
  }
  if (p.parameterVintage !== PARAMETERS.vintage) {
    out.push(warn("W-18", `This proposal was saved with parameters "${p.parameterVintage}"; the tool now uses "${PARAMETERS.vintage}". Check the labour rates.`));
  }
  if (p.remakesSunsettingInstrument === true && p.baseline !== "noInstrument") {
    out.push(warn("W-21", "Remaking a sunsetting instrument is assessed against no instrument, not current settings. Switch the baseline to \"no instrument\"."));
  }
  if (p.remakesSunsettingInstrument === false && p.baseline === "noInstrument") {
    out.push(warn("W-21", "The baseline is \"no instrument\", but the change isn't a remake of a sunsetting instrument. Compare against current settings unless OIA advises otherwise."));
  }
  for (const { option, items } of computed) {
    for (const o of option.obligations) out.push(...obligationWarnings(p, option, o, false));
    for (const o of option.transitions) out.push(...obligationWarnings(p, option, o, true));
    if (!option.isStatusQuo && option.transitions.length === 0 && option.obligations.some((o) => o.current)) {
      out.push(warn("W-09", `Option "${option.name}" changes existing obligations but has no transition costs. Will entities need time to learn the new rules, update systems or retrain staff?`, { option }));
    }
    for (const item of items) {
      if (item.subsidyExcess.greaterThan(0)) {
        const T = p.durationYears;
        out.push(warn("W-12", `"${item.obligation.name}": the subsidy is larger than the cost it offsets. It is capped at the cost; the excess ($${str(item.subsidyExcess.dividedBy(T))} a year) is a transfer outside the framework.`, { option, obligation: item.obligation, populationId: item.population.id }));
      }
    }
    for (const c of findCliffs(p, items)) {
      const ob = [...option.obligations].find((o) => o.id === c.obligationId);
      const label = p.populations.find((x) => x.id === c.populationId)?.label ?? c.populationId;
      out.push(warn("W-10", `"${ob?.name ?? c.obligationId}": a smaller cohort is exempted but "${label}" gets no relief, creating a cliff at the threshold that may discourage growth.`, { option, ...(ob ? { obligation: ob } : {}), populationId: c.populationId }));
    }
  }
  return out;
}

/** Every assumption that departs from a default, or that needs a source, with its justification. */
export function assumptionsRegister(p: Proposal): AssumptionRow[] {
  const rows: AssumptionRow[] = [];
  const d = PARAMETERS.rates;
  const src = (s?: { description: string; url?: string | undefined }) => (s ? [s.description, s.url].filter(Boolean).join(" — ") : undefined);
  const row = (r: AssumptionRow) => rows.push(Object.fromEntries(Object.entries(r).filter(([, v]) => v !== undefined)) as unknown as AssumptionRow);

  row({ item: "Duration", value: `${p.durationYears} years`, defaultValue: "10 years", justification: p.durationOverride?.justification, source: src(p.durationOverride?.source), ref: "RBM p. 6" });
  row({ item: "Baseline", value: p.baseline === "statusQuo" ? "Current settings" : "No instrument (sunsetting remake)", defaultValue: "Current settings", ref: "IA Framework Practical Guide pp. 21-22" });
  row({ item: "Work-related labour rate", value: `$${p.rates.work.hourly}/h ($${p.rates.work.base} × ${p.rates.work.multiplier})`, defaultValue: `$${d.work.hourly}/h ($${d.work.base} × ${d.work.multiplier})`, justification: p.rates.work.override?.justification, source: src(p.rates.work.override?.source) ?? d.work.source, ref: d.work.ref });
  row({ item: "Non-work (leisure) rate", value: `$${p.rates.leisure.hourly}/h`, defaultValue: `$${d.leisure.hourly}/h`, justification: p.rates.leisure.override?.justification, source: src(p.rates.leisure.override?.source) ?? d.leisure.source, ref: d.leisure.ref });
  row({ item: "Volunteer rate", value: `$${p.rates.volunteer.hourly}/h`, defaultValue: `$${d.volunteer.hourly}/h`, justification: p.rates.volunteer.override?.justification, source: src(p.rates.volunteer.override?.source) ?? d.volunteer.source, ref: d.volunteer.ref });
  for (const r of p.rates.custom) {
    row({ item: `Custom rate: ${r.label}`, value: `$${r.hourly}/h (${r.kind})`, justification: r.override.justification, source: src(r.override.source), ref: "RBM p. 12" });
  }
  for (const pop of p.populations) {
    const count = typeof pop.count === "number" ? String(pop.count) : `${pop.count.low}–${pop.count.high} (midpoint ${str(point(pop.count))})`;
    row({ item: `Number affected: ${pop.label}`, value: count, source: src(pop.source), ref: "RBM pp. 8-9" });
  }
  for (const option of p.options) {
    if (option.timing.reformStartYear !== 1 || option.timing.overlapYears !== 0) {
      row({ item: `Timing: ${option.name}`, value: `Reform starts in year ${option.timing.reformStartYear}; ${option.timing.overlapYears} year(s) of dual running`, defaultValue: "Starts in year 1; no dual running" });
    }
    for (const o of [...option.obligations, ...option.transitions]) {
      const share = point(o.doAnywayShare);
      if (!share.isZero()) {
        row({ item: `Do-anyway share: ${o.name}`, value: `${str(share.times(100))}%`, defaultValue: "0%", source: src(o.doAnywaySource), ref: "RBM pp. 3, 6" });
      }
      if (o.scope.classification !== "compliance") {
        row({ item: `Compliance/enforcement: ${o.name}`, value: o.scope.classification === "split" ? `${(o.scope.complianceShare ?? 1) * 100}% compliance` : "Enforcement (excluded)", defaultValue: "Compliance", justification: o.scope.override?.justification, source: src(o.scope.override?.source), ref: "RBM pp. 14-15" });
      }
      if (o.rateChangeJustification) {
        row({ item: `Rate change between versions: ${o.name}`, value: "Different labour rate in reformed version", justification: o.rateChangeJustification.justification, source: src(o.rateChangeJustification.source) });
      }
      if (o.timingOverride) {
        row({ item: `Timing override: ${o.name}`, value: JSON.stringify(o.timingOverride) });
      }
      for (const [, side] of sides(o)) {
        for (const line of side.lines) {
          if (line.subsidy) {
            row({ item: `Subsidy: ${o.name}`, value: `$${str(point(line.subsidy.perEntityPerActiveYear))} per entity per year`, source: src(line.subsidy.source), ref: "RBM p. 3" });
          }
        }
      }
    }
  }
  return rows;
}

