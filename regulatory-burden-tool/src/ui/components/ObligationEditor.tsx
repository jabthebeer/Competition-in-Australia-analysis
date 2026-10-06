// Editing an obligation: what it is (shared across options), and one side of it
// (the current regime, or a reformed version), with a live formula preview per group.
import { useId } from "react";
import { dec } from "../../engine/decimal";
import { EXCLUSIONS, type ItemResult, type Line, type Obligation, type OptionResult, type Population, type Proposal, type Side, type Timing } from "../../engine/index";
import { CATEGORY_LABELS, GROUP_NOUNS, TIMING_LABELS, fmtNum, fmtPct, formatMoney } from "../format";
import { SCOPE_TAGS, highlightedFields, type LeverField } from "../levers";
import { changeCostType, costTypeFor, toggleLine, type Category } from "../model";
import { Checkbox, Help, IntegerField, QuantityField, RadioGroup, SelectField, TextField } from "./fields";

export type EditorMode = "current" | "reform" | "new" | "transition";
type Mutate = (mutate: (o: Obligation) => void) => void;

const CATEGORY_OPTIONS = [
  { value: "administrative", label: "Administrative", help: "Demonstrating compliance: records, reports, notifications, tests, applications, and the time spent paying fees." },
  { value: "substantive", label: "Substantive compliance", help: "Delivering the outcome: training, equipment, operating costs, professional services, information for third parties." },
  { value: "delay", label: "Delay", help: "Waiting for a government decision before the entity can start operating. Seek OIA advice on delay costs." },
] as const;

export function ObligationEditor(props: {
  proposal: Proposal;
  obligation: Obligation;
  mode: EditorMode;
  onChange: Mutate;
  result?: OptionResult;
}) {
  const { proposal, obligation, mode, onChange } = props;
  const sideName = mode === "current" ? "current" : "reformed";
  const side = obligation[sideName];
  const compare = mode === "reform" ? (obligation.current ?? undefined) : undefined;
  const highlight = mode === "reform" ? highlightedFields(obligation.levers) : new Set<LeverField>();
  return (
    <div className="obligation-editor">
      {mode !== "reform" && <SharedFields proposal={proposal} obligation={obligation} onChange={onChange} mode={mode} />}
      {side && (
        <SideEditor
          proposal={proposal}
          category={obligation.category}
          side={side}
          sideName={sideName}
          mode={mode}
          compare={compare}
          highlight={highlight}
          onSide={(update) => onChange((o) => (o[sideName] = update(o[sideName] as Side)))}
        />
      )}
      {side && props.result && <Previews result={props.result} obligation={obligation} sideName={sideName} proposal={proposal} />}
    </div>
  );
}

// ---------------------------------------------------------------------------

function SharedFields({ proposal, obligation, onChange, mode }: { proposal: Proposal; obligation: Obligation; onChange: Mutate; mode: EditorMode }) {
  const o = obligation;
  const setCategory = (category: Category) =>
    onChange((ob) => {
      const leavingOrEnteringDelay = (ob.category === "delay") !== (category === "delay");
      ob.category = category;
      for (const s of ["current", "reformed"] as const) {
        const side = ob[s];
        if (side && leavingOrEnteringDelay) ob[s] = changeCostType(side, costTypeFor(category), proposal.populations);
      }
    });
  return (
    <div className="shared-fields">
      <TextField label="Name of the obligation" value={o.name} onChange={(v) => onChange((ob) => (ob.name = v))} placeholder={mode === "transition" ? "e.g. Familiarisation with the new rules" : "e.g. Quarterly report to the regulator"} testId="obligation-name" />
      <RadioGroup label="Type of cost" value={o.category} options={CATEGORY_OPTIONS} onChange={(v) => setCategory(v)} testId="obligation-category" />
      <QuantityField
        label="Do-anyway share"
        help="The share of today's activity that businesses would keep doing even if the rule didn't exist (e.g. records they need anyway). Only the cost above this level counts. Default 0%."
        value={o.doAnywayShare}
        scale={100}
        min={0}
        max={1}
        unit="%"
        onChange={(q) => onChange((ob) => (ob.doAnywayShare = q))}
        testId="do-anyway"
      />
      <details className="more">
        <summary>Scope checks (what counts)</summary>
        <fieldset className="field">
          <legend>Tick any that apply</legend>
          {SCOPE_TAGS.map((t) => (
            <div key={t.tag}>
              <Checkbox
                label={t.label}
                checked={o.tags.includes(t.tag)}
                onChange={(on) => onChange((ob) => (ob.tags = on ? [...ob.tags, t.tag] : ob.tags.filter((x) => x !== t.tag)))}
              />
              {o.tags.includes(t.tag) && <Help>{t.effect}</Help>}
            </div>
          ))}
        </fieldset>
        <SelectField
          label="Compliance or enforcement (Appendix 3)"
          help="Compliance is the default. Enforcement is excluded, but only where it can be clearly demonstrated."
          value={o.scope.classification}
          options={[
            { value: "compliance", label: "Compliance (default)" },
            { value: "enforcement", label: "Enforcement (excluded)" },
            { value: "split", label: "A mix (split)" },
          ]}
          onChange={(v) =>
            onChange((ob) => {
              ob.scope = { ...ob.scope, classification: v, ...(v === "split" ? { complianceShare: ob.scope.complianceShare ?? 1 } : {}) };
              if (v !== "split") delete ob.scope.complianceShare;
            })
          }
        />
        {o.scope.classification === "split" && (
          <QuantityField label="Compliance share" value={o.scope.complianceShare ?? 1} scale={100} unit="%" min={0} max={1} allowRange={false} onChange={(q) => onChange((ob) => (ob.scope.complianceShare = typeof q === "number" ? q : q.low))} />
        )}
        {o.scope.classification !== "compliance" && (
          <TextField
            label="Why this is enforcement"
            multiline
            value={o.scope.override?.justification ?? ""}
            onChange={(v) => onChange((ob) => (ob.scope.override = v ? { justification: v, source: ob.scope.override?.source ?? { description: "Agency assessment" } } : undefined))}
          />
        )}
        {proposal.jurisdiction === "interJurisdictional" && (
          <SelectField
            label="Imposed or removed by"
            value={o.jurisdiction}
            options={[
              { value: "commonwealth", label: "The Commonwealth" },
              { value: "stateTerritory", label: "States and territories" },
            ]}
            onChange={(v) => onChange((ob) => (ob.jurisdiction = v))}
          />
        )}
        <TextField label="Legal reference: Act or instrument (optional)" value={o.legalReference?.instrument ?? ""} onChange={(v) => onChange((ob) => (ob.legalReference = v ? { ...(ob.legalReference ?? {}), instrument: v } : undefined))} />
        {o.legalReference && <TextField label="Provision (optional)" value={o.legalReference.provision ?? ""} onChange={(v) => onChange((ob) => ob.legalReference && (v ? (ob.legalReference.provision = v) : delete ob.legalReference.provision))} />}
      </details>
    </div>
  );
}

// ---------------------------------------------------------------------------

function SideEditor(props: {
  proposal: Proposal;
  category: Category;
  side: Side;
  sideName: "current" | "reformed";
  mode: EditorMode;
  compare?: Side;
  highlight: Set<LeverField>;
  onSide: (update: (s: Side) => Side) => void;
}) {
  const { proposal, side, compare, highlight, onSide, mode } = props;
  const groupsId = useId();
  return (
    <div className="side-editor">
      {props.category !== "delay" && (
        <SelectField
          label="How is the cost incurred?"
          value={side.costType}
          options={[
            { value: "labour", label: "Staff or personal time" },
            { value: "purchase", label: "Buying goods or services (including outsourced services)" },
          ]}
          onChange={(v) => onSide((s) => changeCostType(s, v, proposal.populations))}
          testId="cost-type"
        />
      )}
      <TimingEditor
        timing={side.timing}
        compare={compare?.timing}
        durationYears={proposal.durationYears}
        highlight={highlight.has("timing")}
        relative={mode !== "current"}
        onChange={(t) => onSide((s) => ({ ...s, timing: t }))}
      />
      {props.sideName === "current" && side.timing.type === "oneOff" && (
        <RadioGroup
          label="Has this one-off cost already been incurred?"
          help="Costs already incurred are sunk: removing the obligation can't save them."
          value={side.status ?? "unsure"}
          options={[
            { value: "future", label: "No, it's a future cost (e.g. new entrants, a scheduled upgrade)" },
            { value: "alreadyIncurred", label: "Yes, already incurred (sunk, so not a saving)" },
            { value: "unsure", label: "Not sure yet" },
          ]}
          onChange={(v) =>
            onSide((s) => {
              const next = { ...s };
              if (v === "unsure") delete next.status;
              else next.status = v;
              return next;
            })
          }
        />
      )}
      <fieldset className={`field${highlight.has("appliesTo") ? " highlight" : ""}`} aria-describedby={`${groupsId}-help`}>
        <legend>Who it applies to</legend>
        <Help id={`${groupsId}-help`}>{mode === "reform" ? "Untick a group to exempt it (e.g. a small-business exemption)." : "Tick each affected group. Set up groups in step 1."}</Help>
        {proposal.populations.map((p) => {
          const on = side.lines.some((l) => l.populationId === p.id);
          return <Checkbox key={p.id} label={p.label} checked={on} disabled={on && side.lines.length === 1} onChange={(v) => onSide((s) => toggleLine(s, p, v))} testId={`applies-${p.id}`} />;
        })}
      </fieldset>
      {side.lines.map((line) => {
        const pop = proposal.populations.find((p) => p.id === line.populationId);
        if (!pop) return null;
        return (
          <LineEditor
            key={line.populationId}
            proposal={proposal}
            population={pop}
            line={line}
            costType={side.costType}
            compare={compare?.costType === side.costType ? compare.lines.find((l) => l.populationId === line.populationId) : undefined}
            highlight={highlight}
            onLine={(update) => onSide((s) => ({ ...s, lines: s.lines.map((l) => (l.populationId === line.populationId ? update(l) : l)) }))}
          />
        );
      })}
    </div>
  );
}

function TimingEditor(props: { timing: Timing; compare?: Timing; durationYears: number; highlight: boolean; relative: boolean; onChange: (t: Timing) => void }) {
  const t = props.timing;
  const changed = props.compare !== undefined && JSON.stringify(props.compare) !== JSON.stringify(t);
  const T = props.durationYears;
  const yearHelp = props.relative ? "Years count from when the reform starts." : undefined;
  return (
    <fieldset className={`field timing${props.highlight ? " highlight" : ""}${changed ? " changed" : ""}`}>
      <legend>
        When it happens {changed && <span className="badge changed-badge">Changed</span>}
      </legend>
      <SelectField
        label="Timing"
        value={t.type}
        options={[
          { value: "ongoing", label: "Every year (ongoing)" },
          { value: "oneOff", label: "Once (one-off or start-up)" },
          { value: "everyKYears", label: "Every few years (e.g. renewals)" },
          { value: "schedule", label: "Year by year (enter each year)" },
        ]}
        onChange={(type) =>
          props.onChange(
            type === "oneOff"
              ? { type, year: 1 }
              : type === "ongoing"
                ? { type, startYear: 1 }
                : type === "everyKYears"
                  ? { type, k: 2, firstYear: 1 }
                  : { type, factors: Array.from({ length: T }, () => 1) },
          )
        }
        testId="timing-type"
      />
      {t.type === "oneOff" && <IntegerField label="In year" help={yearHelp} value={t.year} min={1} max={30} onChange={(year) => props.onChange({ ...t, year })} />}
      {t.type === "ongoing" && (
        <div className="row">
          <IntegerField label="From year" help={yearHelp} value={t.startYear} min={1} max={30} onChange={(startYear) => props.onChange({ ...t, startYear })} />
          <IntegerField label="Until year" help={`Default: the end of the ${T}-year period.`} value={t.endYear ?? T} min={1} max={30} onChange={(endYear) => props.onChange(endYear === T ? { type: "ongoing", startYear: t.startYear } : { ...t, endYear })} />
        </div>
      )}
      {t.type === "everyKYears" && (
        <div className="row">
          <IntegerField label="Every (years)" value={t.k} min={1} max={30} onChange={(k) => props.onChange({ ...t, k })} testId="timing-k" />
          <IntegerField label="First occurs in year" help={yearHelp} value={t.firstYear} min={1} max={30} onChange={(firstYear) => props.onChange({ ...t, firstYear })} />
        </div>
      )}
      {t.type === "schedule" && (
        <div className="schedule">
          <Help>Share of the annual cost incurred in each year (1 = the full annual cost, 0.5 = half, 0 = none).</Help>
          {Array.from({ length: T }, (_, i) => (
            <QuantityField
              key={i}
              label={`Year ${i + 1}`}
              value={t.factors[i] ?? 0}
              allowRange={false}
              min={0}
              onChange={(q) => props.onChange({ type: "schedule", factors: Array.from({ length: T }, (_, j) => (j === i ? (typeof q === "number" ? q : q.low) : (t.factors[j] ?? 0))) })}
            />
          ))}
        </div>
      )}
      {changed && props.compare && <p className="was">Current regime: {describeTiming(props.compare)}</p>}
    </fieldset>
  );
}

export function describeTiming(t: Timing): string {
  switch (t.type) {
    case "oneOff":
      return `once, in year ${t.year}`;
    case "ongoing":
      return `every year from year ${t.startYear}${t.endYear ? ` to ${t.endYear}` : ""}`;
    case "everyKYears":
      return `every ${t.k} years from year ${t.firstYear}`;
    case "schedule":
      return "a year-by-year schedule";
  }
}

function LineEditor(props: {
  proposal: Proposal;
  population: Population;
  line: Line;
  costType: Side["costType"];
  compare?: Line;
  highlight: Set<LeverField>;
  onLine: (update: (l: Line) => Line) => void;
}) {
  const { population: pop, line, compare, highlight, onLine, proposal } = props;
  const noun = GROUP_NOUNS[pop.group];
  const individual = pop.group === "individual";
  const set = (patch: Partial<Line>) => onLine((l) => ({ ...l, ...patch }));
  const rates = [
    { value: "work", label: `Work-related ($${proposal.rates.work.hourly}/h, framework default)` },
    { value: "leisure", label: `Non-work time ($${proposal.rates.leisure.hourly}/h, individuals' own time)` },
    { value: "volunteer", label: `Volunteers ($${proposal.rates.volunteer.hourly}/h)` },
    ...proposal.rates.custom.map((r) => ({ value: r.id, label: `${r.label} ($${r.hourly}/h)` })),
  ];
  return (
    <section className="line-editor" aria-label={`Costs for ${pop.label}`} data-testid={`line-${pop.id}`}>
      <h4>{pop.label}</h4>
      <Checkbox
        label={`All of this group (${typeof pop.count === "number" ? fmtNum(pop.count, 0) : `${fmtNum(pop.count.low, 0)}–${fmtNum(pop.count.high, 0)}`} ${noun})`}
        checked={line.entities === undefined}
        onChange={(all) =>
          onLine((l) => {
            const next = { ...l };
            if (all) delete next.entities;
            else next.entities = pop.count;
            return next;
          })
        }
      />
      {line.entities !== undefined && (
        <QuantityField label={`Number of ${noun} affected`} value={line.entities} min={0} current={compare?.entities} highlight={highlight.has("entities")} onChange={(q) => set({ entities: q })} testId="entities" />
      )}
      <QuantityField
        label="Expected compliance rate"
        help="The share expected to comply. Default 100%."
        value={line.complianceRate}
        scale={100}
        unit="%"
        min={0}
        max={1}
        current={compare?.complianceRate}
        onChange={(q) => set({ complianceRate: q })}
        testId="compliance-rate"
      />
      {line.labour && (
        <>
          <QuantityField
            label={individual ? "Hours each time, per person" : "Hours each time, per staff member"}
            value={line.labour.hours}
            min={0}
            unit="h"
            current={compare?.labour?.hours}
            highlight={highlight.has("hours")}
            onChange={(q) => set({ labour: { ...line.labour!, hours: q } })}
            testId="hours"
          />
          <QuantityField
            label={individual ? "Times a year, per person" : "Times a year, per staff member"}
            help="For example, twice a month = 24; quarterly = 4."
            value={line.labour.timesPerYear}
            min={0}
            current={compare?.labour?.timesPerYear}
            highlight={highlight.has("timesPerYear")}
            onChange={(q) => set({ labour: { ...line.labour!, timesPerYear: q } })}
            testId="times"
          />
          {!individual && (
            <QuantityField
              label="Staff per entity who do it"
              value={line.labour.staff ?? 1}
              min={0}
              current={compare?.labour ? (compare.labour.staff ?? 1) : undefined}
              highlight={highlight.has("staff")}
              onChange={(q) => set({ labour: { ...line.labour!, staff: q } })}
              testId="staff"
            />
          )}
          <SelectField label="Labour rate" value={line.labour.rateId} options={rates} onChange={(rateId) => set({ labour: { ...line.labour!, rateId } })} testId="rate" />
          {compare?.labour && compare.labour.rateId !== line.labour.rateId && <p className="warn-inline">The rate differs from the current regime. Keep the same rate unless the change is deliberate and justified.</p>}
        </>
      )}
      {line.purchase && (
        <>
          <QuantityField label="Price each time" prefix="$" value={line.purchase.unitCost} min={0} current={compare?.purchase?.unitCost} highlight={highlight.has("unitCost")} onChange={(q) => set({ purchase: { ...line.purchase!, unitCost: q } })} testId="unit-cost" help="Exclude GST, and exclude fees, levies and taxes paid to government." />
          <QuantityField label="Times a year, per entity" value={line.purchase.timesPerYear} min={0} current={compare?.purchase?.timesPerYear} highlight={highlight.has("timesPerYear")} onChange={(q) => set({ purchase: { ...line.purchase!, timesPerYear: q } })} testId="times" />
        </>
      )}
      {line.delay && <DelayFields line={line} compare={compare} highlight={highlight} set={set} />}
      {line.purchase || line.labour ? (
        <details className="more">
          <summary>Government subsidy towards this cost</summary>
          <Checkbox
            label="Government pays a subsidy towards this cost"
            checked={line.subsidy !== undefined}
            onChange={(on) =>
              onLine((l) => {
                const next = { ...l };
                if (on) next.subsidy = { perEntityPerActiveYear: 0, source: { description: "Source not yet recorded" } };
                else delete next.subsidy;
                return next;
              })
            }
          />
          {line.subsidy && (
            <>
              <QuantityField label="Subsidy per entity, per year it applies" prefix="$" value={line.subsidy.perEntityPerActiveYear} min={0} onChange={(q) => set({ subsidy: { ...line.subsidy!, perEntityPerActiveYear: q } })} />
              <TextField label="Source of the subsidy figure" value={line.subsidy.source.description} onChange={(v) => set({ subsidy: { ...line.subsidy!, source: { ...line.subsidy!.source, description: v || "Source not yet recorded" } } })} />
            </>
          )}
        </details>
      ) : null}
    </section>
  );
}

function DelayFields({ line, compare, highlight, set }: { line: Line; compare?: Line; highlight: Set<LeverField>; set: (patch: Partial<Line>) => void }) {
  const d = line.delay!;
  const c = compare?.delay;
  const upd = (patch: Partial<typeof d>) => set({ delay: { ...d, ...patch } });
  const unit = d.unit;
  return (
    <>
      <Help>Measure every time from when the entity starts its application. Only time spent waiting after it would otherwise be ready to operate counts.</Help>
      <Checkbox label="The entity is waiting on a government decision before it can start operating (or selling a new product)" checked={d.waitingOnGovernment} onChange={(v) => upd({ waitingOnGovernment: v })} />
      <SelectField label="Measure delays in" value={unit} options={[{ value: "days", label: "Days" }, { value: "weeks", label: "Weeks" }, { value: "months", label: "Months" }]} onChange={(u) => upd({ unit: u })} />
      <QuantityField label={`Time to complete the application (${unit})`} value={d.applicationDelay} min={0} current={c?.applicationDelay} onChange={(q) => upd({ applicationDelay: q })} testId="application-delay" />
      <QuantityField label={`Time for the regulator to decide (${unit})`} value={d.approvalDelay} min={0} current={c?.approvalDelay} highlight={highlight.has("approvalDelay")} onChange={(q) => upd({ approvalDelay: q })} testId="approval-delay" />
      <QuantityField label={`When the entity would otherwise be ready to operate (${unit} from the start)`} value={d.readyAfter} min={0} current={c?.readyAfter} onChange={(q) => upd({ readyAfter: q })} testId="ready-after" />
      <QuantityField label={`Net income forgone per ${unit.replace(/s$/, "")}`} prefix="$" value={d.netIncomePerUnit} min={0} current={c?.netIncomePerUnit} onChange={(q) => upd({ netIncomePerUnit: q })} testId="net-income" />
      <QuantityField label={`Extra expenses caused by the delay, per ${unit.replace(/s$/, "")}`} help="Only expenses not already netted out of income (e.g. rent on idle premises). Default $0." prefix="$" value={d.extraExpensesPerUnit} min={0} current={c?.extraExpensesPerUnit} onChange={(q) => upd({ extraExpensesPerUnit: q })} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Live formula preview (brief: "a live formula preview"; RBM pp. 6, 8-10)

function Previews({ result, obligation, sideName, proposal }: { result: OptionResult; obligation: Obligation; sideName: "current" | "reformed"; proposal: Proposal }) {
  const items = result.items.filter((i) => i.obligationId === obligation.id && i.side === sideName);
  if (items.length === 0) return null;
  return (
    <div className="previews" aria-live="polite">
      {items.map((item) => (
        <FormulaPreview key={item.populationId} item={item} proposal={proposal} />
      ))}
    </div>
  );
}

export function FormulaPreview({ item, proposal }: { item: ItemResult; proposal: Proposal }) {
  const pop = proposal.populations.find((p) => p.id === item.populationId);
  const i = item.inputs;
  const noun = pop ? GROUP_NOUNS[pop.group] : "entities";
  const money = (x: string | undefined) => formatMoney(x ?? "0", "dollars");
  const entities = `${fmtNum(i.entities ?? "0")} ${noun}`;
  const compliance = i.complianceRate && i.complianceRate !== "1" ? ` × ${fmtPct(i.complianceRate)} complying` : "";
  let formula = "";
  if (item.costType === "labour") {
    const staff = i.staff && i.staff !== "1" ? ` × ${fmtNum(i.staff)} staff` : "";
    formula = `${fmtNum(i.hours ?? "0")} h × ${money(i.rate)}/h × ${fmtNum(i.timesPerYear ?? "0")} a year × ${entities}${compliance}${staff}`;
  } else if (item.costType === "purchase") {
    formula = `${money(i.unitCost)} × ${fmtNum(i.timesPerYear ?? "0")} a year × ${entities}${compliance}`;
  } else {
    formula = `${entities}${compliance} × ${fmtNum(i.effectiveDelay ?? "0")} ${i.unit} effective delay (${fmtNum(i.applicationDelay ?? "0")} + ${fmtNum(i.approvalDelay ?? "0")} − ${fmtNum(i.readyAfter ?? "0")}, not below 0) × ${money(i.netIncomePerUnit)}${i.extraExpensesPerUnit && i.extraExpensesPerUnit !== "0" ? ` + ${money(i.extraExpensesPerUnit)}` : ""}`;
  }
  const T = item.netByYear.length;
  const average = formatMoney(item.netByYear.reduce((a, b) => a.plus(b), dec(0)).dividedBy(T), "dollars");
  const years = item.grossByYear.map((g, idx) => (g !== "0" ? idx + 1 : 0)).filter(Boolean);
  return (
    <div className="formula" data-testid={`formula-${item.side}-${item.populationId}`}>
      <p>
        <strong>{pop?.label}:</strong> {formula} = <strong data-testid="active-year-cost">{money(item.activeYearCost)}</strong> in each year it applies
        {item.doAnywayShareApplied !== "0" && <>, less a do-anyway share of {fmtPct(item.doAnywayShareApplied)}</>}.
      </p>
      {item.excluded ? (
        <p className="excluded-note">
          Excluded from the RBE: {EXCLUSIONS[item.excluded].label}. {EXCLUSIONS[item.excluded].explanation}
        </p>
      ) : (
        <p>
          Applies in {years.length === 0 ? "no year of the analysis period" : years.length === T ? `every year (1–${T})` : `year${years.length > 1 ? "s" : ""} ${years.join(", ")}`}. Average over {T} years: <strong data-testid="average">{average}</strong> a year ({CATEGORY_LABELS[item.category]}, {TIMING_LABELS[item.timingType]?.toLowerCase()}).
        </p>
      )}
      <details className="profile">
        <summary>Year-by-year profile</summary>
        <table>
          <caption className="visually-hidden">Year-by-year costs for {pop?.label}</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Gross cost</th>
              <th scope="col">Do-anyway</th>
              <th scope="col">Subsidy</th>
              <th scope="col">Counted</th>
            </tr>
          </thead>
          <tbody>
            {item.grossByYear.map((g, idx) => (
              <tr key={idx}>
                <th scope="row">{idx + 1}</th>
                <td>{money(g)}</td>
                <td>{money(item.doAnywayByYear[idx])}</td>
                <td>{money(item.subsidyByYear[idx])}</td>
                <td>{money(item.netByYear[idx])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
