// Builders for concise test proposals. All figures built with these helpers are
// ILLUSTRATIVE (synthetic) unless a test says it reproduces a framework or OIA example.
import { computeProposal, rbeTable, type Precision, type ProposalResult } from "../../src/engine/index";

type Obj = object;

export const pop = (id: string, count: unknown, extra: Obj = {}) => ({ id, label: id, group: "business", count, ...extra });

export const labour = (populationId: string, hours: unknown, timesPerYear: unknown, opts: { staff?: unknown; rateId?: string; line?: Obj } = {}) => ({
  populationId,
  labour: {
    hours,
    timesPerYear,
    ...(opts.staff !== undefined ? { staff: opts.staff } : {}),
    ...(opts.rateId ? { rateId: opts.rateId } : {}),
  },
  ...(opts.line ?? {}),
});

export const purchase = (populationId: string, unitCost: unknown, timesPerYear: unknown, line: Obj = {}) => ({
  populationId,
  purchase: { unitCost, timesPerYear },
  ...line,
});

export const delayLine = (populationId: string, delay: Obj, line: Obj = {}) => ({
  populationId,
  delay: { unit: "months", waitingOnGovernment: true, ...delay },
  ...line,
});

export const side = (costType: "labour" | "purchase" | "delay", lines: unknown[], timing: Obj = { type: "ongoing" }, extra: Obj = {}) => ({
  costType,
  timing,
  lines,
  ...extra,
});

export const ob = (id: string, category: "administrative" | "substantive" | "delay", current: unknown, reformed: unknown, extra: Obj = {}) => ({
  id,
  name: id,
  category,
  current,
  reformed,
  ...extra,
});

export const option = (id: string, obligations: unknown[], extra: Obj = {}) => ({ id, name: id, obligations, ...extra });

export const proposal = (populations: unknown[], options: unknown[], extra: Obj = {}) => ({
  id: "test",
  title: "Test proposal (illustrative, synthetic data)",
  populations,
  options,
  ...extra,
});

export const run = (p: unknown): ProposalResult => computeProposal(p);

/** Formatted RBE cells: Business, Community organisations, Individuals, Total. */
export const cells = (r: ProposalResult, optionIndex = 0, precision: Precision = 1): string[] =>
  rbeTable(r.options[optionIndex]!.rbe, precision).cells.slice(1);

export const codes = (r: ProposalResult): string[] => r.warnings.map((w) => w.code);

export const opt = (r: ProposalResult, i = 0) => r.options[i]!;

/** The illustrative reform from the brief (synthetic): quarterly 4 h report → annual 2 h; 1 h familiarisation; 10,000 businesses. */
export function illustrativeReform(extra: Obj = {}, optionExtra: Obj = {}) {
  return proposal(
    [pop("biz", 10000)],
    [
      option(
        "annual",
        [ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), side("labour", [labour("biz", 2, 1)]))],
        {
          transitions: [ob("familiarise", "administrative", null, side("labour", [labour("biz", 1, 1)], { type: "oneOff", year: 1 }))],
          ...optionExtra,
        },
      ),
    ],
    extra,
  );
}

export const WORK_RATE = 91.54;
