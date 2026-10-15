// Tidy, analysis-ready export (DECISIONS #44): one row per option × obligation side ×
// population × year, with identifiers that merge with ABS business data
// (ANZSIC 2006 industry codes and ABS employment-size bands). Intended for
// econometric work in Stata, R or Python; the tool itself does no econometrics.
import { dec, str } from "./decimal";
import type { ProposalResult } from "./types";

export interface TidyColumn {
  name: string;
  type: "string" | "integer" | "decimal" | "boolean";
  description: string;
}

/** Data dictionary for the tidy export. Column order is stable across versions; new columns are only appended. */
export const TIDY_COLUMNS: readonly TidyColumn[] = [
  { name: "proposal_id", type: "string", description: "Proposal identifier" },
  { name: "option_id", type: "string", description: "Option identifier" },
  { name: "option_name", type: "string", description: "Option name" },
  { name: "baseline", type: "string", description: "Baseline for delta_contribution: statusQuo (current settings) or noInstrument (sunsetting remake)" },
  { name: "obligation_id", type: "string", description: "Obligation identifier" },
  { name: "obligation_name", type: "string", description: "Obligation name" },
  { name: "item_kind", type: "string", description: "obligation, or transition (one-off switching cost)" },
  { name: "side", type: "string", description: "current (existing regime) or reformed (proposed regime)" },
  { name: "legal_instrument", type: "string", description: "Act or instrument, e.g. 'CCA Sch 2 (ACL)' (optional)" },
  { name: "legal_provision", type: "string", description: "Provision, e.g. 's 131' (optional)" },
  { name: "population_id", type: "string", description: "Affected population identifier" },
  { name: "stakeholder_group", type: "string", description: "business, communityOrg or individual (RBE table columns)" },
  { name: "cohort", type: "string", description: "small, medium, large or all" },
  { name: "employment_band", type: "string", description: "ABS employment-size band: nonEmploying, 1-4, 5-19, 20-199, 200+ (optional)" },
  { name: "industry_anzsic", type: "string", description: "ANZSIC 2006 division letter or 2-4 digit code (optional)" },
  { name: "entity_type", type: "string", description: "private, gbe, publicUniversity, foreignGovOwnedBusiness or governmentAgency" },
  { name: "category", type: "string", description: "administrative, substantive or delay (RBM pp. 1-3)" },
  { name: "cost_type", type: "string", description: "labour, purchase or delay" },
  { name: "timing_type", type: "string", description: "oneOff, ongoing, everyKYears, schedule or transition" },
  { name: "jurisdiction", type: "string", description: "commonwealth or stateTerritory" },
  { name: "year", type: "integer", description: "Year of the analysis window (1 = first year)" },
  { name: "entities", type: "decimal", description: "Entities incurring the cost (count × expected compliance rate)" },
  { name: "gross_cost", type: "decimal", description: "Gross cost in the year, $ (real terms, undiscounted)" },
  { name: "do_anyway_adjustment", type: "decimal", description: "Business-as-usual portion removed, $" },
  { name: "enforcement_excluded", type: "decimal", description: "Enforcement share removed (Appendix 3), $" },
  { name: "subsidy_applied", type: "decimal", description: "Government subsidy subtracted, $" },
  { name: "net_cost", type: "decimal", description: "In-scope regime cost in the year, $ (steady state: current unmasked, reformed unshifted)" },
  { name: "net_cost_per_entity", type: "decimal", description: "net_cost ÷ entities, $ (blank when entities is 0)" },
  { name: "delta_contribution", type: "decimal", description: "Contribution to the change in regulatory burden in the year, $ (sums to the RBE × duration)" },
  { name: "excluded_reason", type: "string", description: "Why the item is outside the RBE, if it is (blank otherwise)" },
  { name: "parameter_vintage", type: "string", description: "Default-parameter vintage, e.g. RBM-2026-07" },
  { name: "engine_version", type: "string", description: "Engine version that produced the row" },
];

export type TidyRow = Record<string, string | number>;

export function toTidyRows(result: ProposalResult): TidyRow[] {
  const rows: TidyRow[] = [];
  for (const option of result.options) {
    for (const item of option.items) {
      const entities = dec(item.effectiveEntities);
      for (let t = 0; t < result.durationYears; t++) {
        const net = dec(item.netByYear[t] ?? "0");
        rows.push({
          proposal_id: result.proposalId,
          option_id: option.optionId,
          option_name: option.optionName,
          baseline: option.baseline,
          obligation_id: item.obligationId,
          obligation_name: item.obligationName,
          item_kind: item.kind,
          side: item.side,
          legal_instrument: item.legalInstrument ?? "",
          legal_provision: item.legalProvision ?? "",
          population_id: item.populationId,
          stakeholder_group: item.group,
          cohort: item.cohort,
          employment_band: item.employmentBand ?? "",
          industry_anzsic: item.industry ?? "",
          entity_type: item.entityType,
          category: item.category,
          cost_type: item.costType,
          timing_type: item.timingType,
          jurisdiction: item.jurisdiction,
          year: t + 1,
          entities: item.effectiveEntities,
          gross_cost: item.grossByYear[t] ?? "0",
          do_anyway_adjustment: item.doAnywayByYear[t] ?? "0",
          enforcement_excluded: item.enforcementExcludedByYear[t] ?? "0",
          subsidy_applied: item.subsidyByYear[t] ?? "0",
          net_cost: str(net),
          net_cost_per_entity: entities.isZero() ? "" : str(net.dividedBy(entities)),
          delta_contribution: item.deltaByYear[t] ?? "0",
          excluded_reason: item.excluded ?? "",
          parameter_vintage: result.parameterVintage,
          engine_version: result.engineVersion,
        });
      }
    }
  }
  return rows;
}

function csvCell(value: string | number): string {
  const s = String(value);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** RFC 4180 CSV with a header row, in data-dictionary column order. */
export function tidyCsv(rows: readonly TidyRow[]): string {
  const header = TIDY_COLUMNS.map((c) => c.name);
  const lines = [header.join(",")];
  for (const row of rows) lines.push(header.map((h) => csvCell(row[h] ?? "")).join(","));
  return `${lines.join("\r\n")}\r\n`;
}

/** The data dictionary as CSV, to ship alongside the data. */
export function tidyDictionaryCsv(): string {
  const lines = ["name,type,description", ...TIDY_COLUMNS.map((c) => [c.name, c.type, c.description].map(csvCell).join(","))];
  return `${lines.join("\r\n")}\r\n`;
}
