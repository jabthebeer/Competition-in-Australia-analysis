import { useMemo, type ReactNode } from "react";
import { CHANNELS, CHANNEL_IDS, SHOCK_TYPES, costBrief, type ChannelId, type ChannelOutcome, type CostingResult, type ShockType } from "../../productivity/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import type { BriefDraft, LeversDraft } from "../briefModel";
import { useCostingContext, useRegister } from "../costingContext";
import { ChannelDetail } from "../components/ChannelDetail";
import { Checkbox, Help, QuantityField, RadioGroup, SelectField, TextField } from "../components/fields";
import { SimilarChanges } from "../components/SimilarChanges";

type Q = number | { low: number; high: number };
type Levers = LeversDraft;

interface NumberProps {
  label: string;
  help?: ReactNode;
  unit?: string;
  prefix?: string;
  scale?: number;
  min?: number;
  max?: number;
  testId?: string;
}

/** A quantity the lever may leave out: an "Add" button until the user gives it a value. */
function OptionalQuantity(props: NumberProps & { value: Q | undefined; onChange: (q: Q | undefined) => void }) {
  const { value, onChange, ...rest } = props;
  if (value === undefined) {
    return (
      <p className="optional-add">
        <button type="button" className="link" onClick={() => onChange(0)} data-testid={props.testId ? `${props.testId}-add` : undefined}>
          Add: {props.label.toLowerCase()}
        </button>
      </p>
    );
  }
  return (
    <div className="optional-field">
      <QuantityField {...rest} value={value} onChange={onChange} />
      <button type="button" className="link" onClick={() => onChange(undefined)}>
        Remove: {props.label.toLowerCase()}
      </button>
    </div>
  );
}

/** Which scope industries a lever applies to; all ticked means the whole scope (the lever names none of its own). */
function LeverIndustries({ draft, value, onChange }: { draft: BriefDraft; value: string[] | undefined; onChange: (v: string[] | undefined) => void }) {
  const codes = draft.scope.industries.map((i) => i.anzsic);
  if (codes.length < 2) return null;
  const chosen = new Set(value ?? codes);
  return (
    <fieldset className="field checkbox-group compact">
      <legend>Industries this lever applies to</legend>
      {codes.map((c) => (
        <Checkbox
          key={c}
          label={c}
          checked={chosen.has(c)}
          onChange={(on) => {
            const next = new Set(chosen);
            if (on) next.add(c);
            else next.delete(c);
            const list = codes.filter((x) => next.has(x));
            onChange(list.length === codes.length ? undefined : list);
          }}
        />
      ))}
    </fieldset>
  );
}

function LeverCard(props: {
  id: string;
  title: string;
  intro: ReactNode;
  enabled: boolean;
  toggleLabel: string;
  onToggle: (on: boolean) => void;
  channels: ChannelId[];
  outcomes: Map<ChannelId, ChannelOutcome>;
  children?: ReactNode;
}) {
  const shown = props.channels.map((c) => props.outcomes.get(c)).filter((o): o is ChannelOutcome => !!o);
  return (
    <section className={`card lever-card${props.enabled ? " on" : ""}`} aria-labelledby={`${props.id}-heading`} data-testid={`lever-${props.id}`}>
      <h2 id={`${props.id}-heading`}>{props.title}</h2>
      <Help>{props.intro}</Help>
      <Checkbox label={props.toggleLabel} checked={props.enabled} onChange={props.onToggle} testId={`lever-${props.id}-toggle`} />
      {props.enabled && <div className="lever-fields">{props.children}</div>}
      {props.enabled && shown.length > 0 && (
        <div className="lever-result">
          <h3>What the tool calculates</h3>
          {shown.map((o) => (
            <ChannelDetail key={o.channel} outcome={o} />
          ))}
        </div>
      )}
    </section>
  );
}

const PMR_INDICATORS = [
  { value: "energy", label: "Energy (ETCR): costed" },
  { value: "transport", label: "Transport (ETCR): costed" },
  { value: "communications", label: "Communications (ETCR): costed" },
  { value: "economyWide", label: "Economy-wide PMR: reported only" },
  { value: "adminRegulatoryBurden", label: "Administrative and regulatory burden: reported only" },
  { value: "barriersToEntry", label: "Barriers to entry: reported only" },
  { value: "barriersServiceSectors", label: "Barriers in service sectors: reported only" },
  { value: "lawyers", label: "Lawyers: reported only" },
  { value: "retailMedicines", label: "Retail sale of medicines: reported only" },
  { value: "other", label: "Other: reported only" },
] as const;

const RESTRICTIONS = [
  { value: "priceControl", label: "Price controls" },
  { value: "quantityControl", label: "Quantity controls" },
  { value: "advertising", label: "Advertising limits" },
  { value: "standards", label: "Standards" },
  { value: "tradingHours", label: "Trading-hours rules" },
  { value: "exclusivity", label: "Exclusive rights" },
  { value: "information", label: "Information requirements" },
  { value: "other", label: "Other" },
] as const;

const FUNDING_TAXES = [
  { value: "labourIncome", label: "Labour income tax" },
  { value: "personalIncome", label: "Personal income tax" },
  { value: "companyIncome", label: "Company income tax" },
  { value: "gstCurrentBase", label: "GST (current base)" },
  { value: "gstBroadBase", label: "GST (broader base)" },
  { value: "conveyancingDuty", label: "Conveyancing (stamp) duty" },
  { value: "landTax", label: "Land tax" },
  { value: "other", label: "Other (not costed)" },
] as const;

export function LeversPage({ draft, updateDraft, brief, proposal, go }: PageProps) {
  const loaded = useCostingContext();
  const register = useRegister();
  const result: CostingResult | null = useMemo(() => (brief.ok && loaded.status === "ready" ? costBrief(brief.brief, loaded.ctx) : null), [brief, loaded]);
  const outcomes = useMemo(() => new Map((result?.channels ?? []).map((c) => [c.channel, c as ChannelOutcome])), [result]);
  const l = draft.levers;
  const set = (fn: (l: Levers) => Levers) => updateDraft((d) => ({ ...d, levers: fn(d.levers) }));
  const c1 = outcomes.get("C1");

  return (
    <>
      <PageHeading>Step 5: Productivity levers</PageHeading>
      <p>
        Each card is a way the policy can change productivity. Switch on only the ones that apply. Under each card, the tool shows its calculation for each industry, the evidence it uses and that evidence's grade. GDP effects, with their ranges, are on the Results page.
      </p>
      {draft.scope.industries.length === 0 && (
        <p className="banner draft">
          The levers apply to the industries in scope. <a href="#scope">Add at least one industry on the Scope page</a> first.
        </p>
      )}
      <BriefIssues brief={brief} />
      {loaded.status === "loading" && <p>Loading the bundled data…</p>}
      {loaded.status === "error" && <p className="banner error">{loaded.problem}</p>}

      <section className="card lever-card on" aria-labelledby="c1-heading" data-testid="lever-burden">
        <h2 id="c1-heading">Compliance costs (from the burden pages)</h2>
        <Help>
          The burden proposal's change in compliance and delay costs (the RBE) is a change in the resources businesses spend on regulation. The tool turns it into a change in measured productivity in each industry. Individuals' costs are left out: they are not in GDP.
        </Help>
        {brief.withBurden ? c1 ? <ChannelDetail outcome={c1} /> : <p>Calculating…</p> : <p>No burden costing yet: add obligations on the Current regime and Reform options pages to include compliance costs.</p>}
      </section>

      <EntryCard draft={draft} set={set} outcomes={outcomes} proposalPopulations={proposal.populations.map((p) => ({ id: p.id, label: p.label || p.id }))} />
      <ThresholdsCard draft={draft} set={set} outcomes={outcomes} />

      <LeverCard
        id="capital"
        title="Investment: tax, depreciation, risk and approvals"
        intro="Changes to the cost of capital: the company tax rate, depreciation deductions, the risk premium investors require, or how long investment approvals take. The tool works out the change in the user cost of capital and how much capital industries add or shed."
        enabled={!!l.capital}
        toggleLabel="The policy changes the cost of investing"
        onToggle={(on) => set((x) => ({ ...x, capital: on ? { companyTaxRate: { from: 0.3, to: 0.3 } } : undefined }))}
        channels={["C3", "C2"]}
        outcomes={outcomes}
      >
        {l.capital && (
          <>
            {l.capital.companyTaxRate ? (
              <div className="optional-field">
                <div className="field-pair">
                  <QuantityField label="Company tax rate now" scale={100} unit="%" min={0} max={1} value={l.capital.companyTaxRate.from} onChange={(q) => set((x) => ({ ...x, capital: { ...x.capital!, companyTaxRate: { ...x.capital!.companyTaxRate!, from: q } } }))} />
                  <QuantityField label="Company tax rate after" scale={100} unit="%" min={0} max={1} value={l.capital.companyTaxRate.to} onChange={(q) => set((x) => ({ ...x, capital: { ...x.capital!, companyTaxRate: { ...x.capital!.companyTaxRate!, to: q } } }))} testId="lever-tax-to" />
                </div>
                <button type="button" className="link" onClick={() => set((x) => ({ ...x, capital: { ...x.capital!, companyTaxRate: undefined } }))}>
                  Remove: company tax rate
                </button>
              </div>
            ) : (
              <p className="optional-add">
                <button type="button" className="link" onClick={() => set((x) => ({ ...x, capital: { ...x.capital!, companyTaxRate: { from: 0.3, to: 0.3 } } }))}>
                  Add: company tax rate
                </button>
              </p>
            )}
            <OptionalQuantity
              label="Change in the present value of depreciation deductions"
              help="Per dollar invested, e.g. 0.05 for five cents more. Needs the company tax rate."
              value={l.capital.depreciationPvChange}
              min={-1}
              max={1}
              onChange={(q) => set((x) => ({ ...x, capital: { ...x.capital!, depreciationPvChange: q } }))}
            />
            <OptionalQuantity label="Change in the risk premium" unit="pp" min={-20} max={20} value={l.capital.riskPremiumChangePp} onChange={(q) => set((x) => ({ ...x, capital: { ...x.capital!, riskPremiumChangePp: q } }))} />
            <OptionalQuantity
              label="Change in investment approval time"
              help="Negative for faster approvals. Set each industry's exposure to the share of its investment that needs the approval."
              unit="months"
              min={-120}
              max={120}
              value={l.capital.investmentApprovalDelayChangeMonths}
              onChange={(q) => set((x) => ({ ...x, capital: { ...x.capital!, investmentApprovalDelayChangeMonths: q } }))}
            />
            <LeverIndustries draft={draft} value={l.capital.industries} onChange={(v) => set((x) => ({ ...x, capital: { ...x.capital!, industries: v } }))} />
          </>
        )}
      </LeverCard>

      <ConductCard draft={draft} set={set} outcomes={outcomes} />
      <LabourCard draft={draft} set={set} outcomes={outcomes} />

      <LeverCard
        id="innovation"
        title="Innovation: R&D and product approvals"
        intro="Changes to the cost of doing research and development (for example the R&D tax incentive), or to how long new products take to be approved."
        enabled={!!l.innovation}
        toggleLabel="The policy changes the cost of R&D or product approval times"
        onToggle={(on) => set((x) => ({ ...x, innovation: on ? { rdUserCostChangePct: 0 } : undefined }))}
        channels={["C9"]}
        outcomes={outcomes}
      >
        {l.innovation && (
          <>
            <OptionalQuantity label="Change in the cost of R&D (user cost)" help="Negative for a cheaper R&D, e.g. −10 for a 10% cut." unit="%" min={-99} max={500} value={l.innovation.rdUserCostChangePct} onChange={(q) => set((x) => ({ ...x, innovation: { ...x.innovation!, rdUserCostChangePct: q } }))} />
            <OptionalQuantity label="Change in product approval time" unit="days" min={-3650} max={3650} value={l.innovation.productApprovalTimeChangeDays} onChange={(q) => set((x) => ({ ...x, innovation: { ...x.innovation!, productApprovalTimeChangeDays: q } }))} />
            <LeverIndustries draft={draft} value={l.innovation.industries} onChange={(v) => set((x) => ({ ...x, innovation: { ...x.innovation!, industries: v } }))} />
          </>
        )}
      </LeverCard>

      <LeverCard
        id="trade"
        title="Trade and foreign investment"
        intro="Changes to tariffs, to how open the economy is to trade, or to restrictions on foreign direct investment."
        enabled={!!l.trade}
        toggleLabel="The policy changes trade or foreign investment rules"
        onToggle={(on) => set((x) => ({ ...x, trade: on ? { opennessChangePp: 0 } : undefined }))}
        channels={["C10"]}
        outcomes={outcomes}
      >
        {l.trade && (
          <>
            <OptionalQuantity label="Change in trade openness" help="Exports plus imports as a share of GDP, in percentage points." unit="pp of GDP" min={-50} max={50} value={l.trade.opennessChangePp} onChange={(q) => set((x) => ({ ...x, trade: { ...x.trade!, opennessChangePp: q } }))} />
            <OptionalQuantity label="Change in the average tariff" unit="pp" min={-100} max={100} value={l.trade.tariffChangePp} onChange={(q) => set((x) => ({ ...x, trade: { ...x.trade!, tariffChangePp: q } }))} />
            <OptionalQuantity label="Change in the OECD FDI restrictiveness index" unit="%" min={-100} max={500} value={l.trade.fdiRestrictivenessChangePct} onChange={(q) => set((x) => ({ ...x, trade: { ...x.trade!, fdiRestrictivenessChangePct: q } }))} />
          </>
        )}
      </LeverCard>

      <LeverCard
        id="fiscal"
        title="Funding: the cost of raising revenue"
        intro="When a policy raises or gives up revenue, the tax that funds it has an efficiency cost. The tool reports it beside GDP, not in it."
        enabled={!!l.fiscal}
        toggleLabel="The policy raises or gives up revenue"
        onToggle={(on) => set((x) => ({ ...x, fiscal: on ? { revenueChangeDollarsPerYear: 0, fundingTax: "labourIncome" } : undefined }))}
        channels={["C11"]}
        outcomes={outcomes}
      >
        {l.fiscal && (
          <>
            <QuantityField label="Revenue a year" help="Positive if the policy raises revenue through the funding tax; negative if it gives revenue up." prefix="$" min={-1e12} max={1e12} value={l.fiscal.revenueChangeDollarsPerYear} onChange={(q) => set((x) => ({ ...x, fiscal: { ...x.fiscal!, revenueChangeDollarsPerYear: q } }))} />
            <SelectField label="The tax that funds it" value={l.fiscal.fundingTax} options={FUNDING_TAXES} onChange={(v) => set((x) => ({ ...x, fiscal: { ...x.fiscal!, fundingTax: v } }))} />
          </>
        )}
      </LeverCard>

      <CustomCard draft={draft} set={set} outcomes={outcomes} />

      {register.status === "ready" && <SimilarChanges draft={draft} records={register.register.records} />}

      <NextStep go={go} to="competition">
        Next: the competition screen
      </NextStep>
    </>
  );
}

/** What stops the brief being costed, in plain words. */
export function BriefIssues({ brief }: { brief: PageProps["brief"] }) {
  if (brief.ok) return null;
  return (
    <div className="banner error" role="alert" data-testid="brief-issues">
      <strong>Some productivity inputs need fixing before they can be costed:</strong>
      <ul>
        {brief.issues.slice(0, 8).map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </div>
  );
}

type CardProps = { draft: BriefDraft; set: (fn: (l: Levers) => Levers) => void; outcomes: Map<ChannelId, ChannelOutcome> };

function EntryCard({ draft, set, outcomes, proposalPopulations }: CardProps & { proposalPopulations: { id: string; label: string }[] }) {
  const e = draft.levers.entry;
  const put = (patch: Partial<NonNullable<Levers["entry"]>>) => set((x) => ({ ...x, entry: { ...x.entry!, ...patch } }));
  return (
    <LeverCard
      id="entry"
      title="Entry and exit"
      intro="Changes to what it costs, or how long it takes, to start a business; caps on the number of businesses; and the cost of closing one. The tool works out the change in each industry's entry rate, and, if you know how far the industry is from the global productivity frontier, the productivity gain from faster catch-up."
      enabled={!!e}
      toggleLabel="The policy changes the cost of entering or leaving an industry"
      onToggle={(on) => set((x) => ({ ...x, entry: on ? { costPerEntrantChangeDollars: 0 } : undefined }))}
      channels={["C4"]}
      outcomes={outcomes}
    >
      {e && (
        <>
          <OptionalQuantity label="Change in the one-off cost per new business" help="Negative for a saving, e.g. −400." prefix="$" min={-1e9} max={1e9} value={e.costPerEntrantChangeDollars} onChange={(q) => put({ costPerEntrantChangeDollars: q })} testId="lever-entry-cost" />
          <OptionalQuantity
            label="Cost per new business before the change"
            help="The industries' own entry cost, if known. Otherwise the tool uses Djankov et al.'s 2.25% of GDP per head (Australia, 1999)."
            prefix="$"
            min={0}
            max={1e9}
            value={e.baselineCostPerEntrantDollars}
            onChange={(q) => put({ baselineCostPerEntrantDollars: q })}
          />
          {e.numberCap ? (
            <div className="optional-field">
              <SelectField
                label="Cap on the number of businesses"
                value={e.numberCap.change}
                options={[
                  { value: "introduce", label: "Introduce a cap" },
                  { value: "tighten", label: "Tighten a cap" },
                  { value: "loosen", label: "Loosen a cap" },
                  { value: "remove", label: "Remove a cap" },
                ]}
                onChange={(v) => put({ numberCap: { ...e.numberCap!, change: v } })}
              />
              <QuantityField
                label={e.numberCap.change === "introduce" || e.numberCap.change === "tighten" ? "Share of would-be entrants it keeps out" : "Share of would-be entrants it lets in"}
                scale={100}
                unit="%"
                min={0}
                max={1}
                value={e.numberCap.excludedEntrantShare}
                onChange={(q) => put({ numberCap: { ...e.numberCap!, excludedEntrantShare: q } })}
              />
              <button type="button" className="link" onClick={() => put({ numberCap: undefined })}>
                Remove: cap on numbers
              </button>
            </div>
          ) : (
            <p className="optional-add">
              <button type="button" className="link" onClick={() => put({ numberCap: { change: "introduce", excludedEntrantShare: 0 } })}>
                Add: a cap on the number of businesses
              </button>
            </p>
          )}
          <OptionalQuantity label="Change in approval time for a new business" help="Reported, not costed: enter its cost to an entrant above to cost it." unit="days" min={-3650} max={3650} value={e.approvalTimeChangeDays} onChange={(q) => put({ approvalTimeChangeDays: q })} />
          <OptionalQuantity label="Change in the one-off cost of closing a business" help="Reported, not costed (no verified evidence)." prefix="$" min={-1e9} max={1e9} value={e.exitCostChangeDollars} onChange={(q) => put({ exitCostChangeDollars: q })} />
          <OptionalQuantity
            label="Distance from the global productivity frontier"
            help="ln(frontier labour productivity ÷ the industry's), e.g. 0.6. No public source publishes it, so it is your estimate and graded D. Without it, the tool reports the faster convergence but no productivity gain."
            unit="log points"
            min={0}
            max={5}
            value={e.frontierGapLogPoints}
            onChange={(q) => put({ frontierGapLogPoints: q })}
          />
          {proposalPopulations.length > 0 && (
            <fieldset className="field checkbox-group compact">
              <legend>Burden groups that are new entrants</legend>
              <Help>Their compliance costs are counted here, as an entry cost, and left out of the compliance-cost calculation, so they are not counted twice.</Help>
              {proposalPopulations.map((p) => (
                <Checkbox
                  key={p.id}
                  label={p.label}
                  checked={(e.entrantPopulationIds ?? []).includes(p.id)}
                  onChange={(on) => {
                    const ids = new Set(e.entrantPopulationIds ?? []);
                    if (on) ids.add(p.id);
                    else ids.delete(p.id);
                    put({ entrantPopulationIds: ids.size ? proposalPopulations.map((x) => x.id).filter((x) => ids.has(x)) : undefined });
                  }}
                />
              ))}
            </fieldset>
          )}
          <LeverIndustries draft={draft} value={e.industries} onChange={(v) => put({ industries: v })} />
        </>
      )}
    </LeverCard>
  );
}

function ThresholdsCard({ draft, set, outcomes }: CardProps) {
  const list = draft.levers.thresholds ?? [];
  const put = (i: number, patch: Partial<(typeof list)[number]>) => set((x) => ({ ...x, thresholds: (x.thresholds ?? []).map((t, j) => (j === i ? { ...t, ...patch } : t)) }));
  return (
    <LeverCard
      id="thresholds"
      title="Size thresholds"
      intro="Rules that start to apply once a business passes a size, such as 20 employees or $10 million turnover. The tool screens how many businesses and workers sit near the threshold and how large its cost is against wages; it does not cost a GDP effect, because the published estimates cannot be scaled to Australian thresholds."
      enabled={list.length > 0}
      toggleLabel="The policy introduces, moves or removes a size threshold"
      onToggle={(on) => set((x) => ({ ...x, thresholds: on ? [{ id: "threshold-1", metric: "employees", change: "introduce", value: 20, costAbovePerYearDollars: 0 }] : [] }))}
      channels={["C5"]}
      outcomes={outcomes}
    >
      {list.map((t, i) => (
        <div className="sub-card" key={i}>
          <SelectField
            label="Measured by"
            value={t.metric}
            options={[
              { value: "employees", label: "Employees" },
              { value: "turnover", label: "Turnover ($)" },
              { value: "payroll", label: "Payroll ($)" },
              { value: "assets", label: "Assets ($)" },
            ]}
            onChange={(v) => put(i, { metric: v })}
          />
          <SelectField
            label="Change"
            value={t.change}
            options={[
              { value: "introduce", label: "Introduce" },
              { value: "move", label: "Move" },
              { value: "remove", label: "Remove" },
            ]}
            onChange={(v) => put(i, { change: v, previousValue: v === "move" ? (t.previousValue ?? t.value) : undefined })}
          />
          <QuantityField label={t.change === "remove" ? "Threshold being removed" : "Threshold after the change"} allowRange={false} min={0} value={t.value} onChange={(q) => put(i, { value: q as number })} />
          {t.change === "move" && <QuantityField label="Threshold before the change" allowRange={false} min={0} value={t.previousValue ?? t.value} onChange={(q) => put(i, { previousValue: q as number })} />}
          <QuantityField label="Cost a year for a business above it" prefix="$" min={0} max={1e12} value={t.costAbovePerYearDollars} onChange={(q) => put(i, { costAbovePerYearDollars: q })} />
          <button type="button" className="danger" onClick={() => set((x) => ({ ...x, thresholds: (x.thresholds ?? []).filter((_, j) => j !== i) }))}>
            Remove this threshold
          </button>
        </div>
      ))}
      {list.length > 0 && (
        <button
          type="button"
          onClick={() => set((x) => ({ ...x, thresholds: [...(x.thresholds ?? []), { id: `threshold-${(x.thresholds ?? []).length + 1}`, metric: "employees", change: "introduce", value: 20, costAbovePerYearDollars: 0 }] }))}
        >
          Add another threshold
        </button>
      )}
    </LeverCard>
  );
}

function ConductCard({ draft, set, outcomes }: CardProps) {
  const c = draft.levers.conduct;
  const restrictions = (c?.restrictions ?? []) as string[];
  return (
    <LeverCard
      id="conduct"
      title="Competition: mark-ups and market regulation"
      intro="Two alternative routes to the same effect; use one. Either the change in price–cost mark-ups the policy brings, or a change in an OECD product market regulation (PMR) indicator. Only the network-sector (ETCR) indicators have a verified productivity estimate."
      enabled={!!c}
      toggleLabel="The policy changes how intensely businesses compete"
      onToggle={(on) => set((x) => ({ ...x, conduct: on ? { route: "markup", markupChangePct: 0 } : undefined }))}
      channels={["C6", "C7"]}
      outcomes={outcomes}
    >
      {c && (
        <>
          <RadioGroup
            label="Route"
            value={c.route}
            options={[
              { value: "markup", label: "A change in mark-ups" },
              { value: "pmr", label: "A change in an OECD PMR indicator" },
            ]}
            onChange={(v) =>
              set((x) => {
                const base = { restrictions: x.conduct?.restrictions, industries: x.conduct?.industries, description: x.conduct?.description };
                return { ...x, conduct: v === "markup" ? { route: "markup", markupChangePct: 0, ...base } : { route: "pmr", indicator: "energy", from: 1, to: 1, ...base } };
              })
            }
          />
          {c.route === "markup" ? (
            <QuantityField label="Change in the average mark-up of the industries reached" help="Negative for lower mark-ups, e.g. −2 for 2% lower." unit="%" min={-100} max={100} value={c.markupChangePct} onChange={(q) => set((x) => ({ ...x, conduct: { ...(x.conduct as typeof c), markupChangePct: q } }))} />
          ) : (
            <>
              <SelectField label="Indicator" value={c.indicator} options={PMR_INDICATORS} onChange={(v) => set((x) => ({ ...x, conduct: { ...(x.conduct as typeof c), indicator: v } }))} />
              <div className="field-pair">
                <QuantityField label="Indicator now (0–6)" allowRange={false} min={0} max={6} value={c.from} onChange={(q) => set((x) => ({ ...x, conduct: { ...(x.conduct as typeof c), from: q as number } }))} />
                <QuantityField label="Indicator after (0–6)" allowRange={false} min={0} max={6} value={c.to} onChange={(q) => set((x) => ({ ...x, conduct: { ...(x.conduct as typeof c), to: q as number } }))} />
              </div>
            </>
          )}
          <fieldset className="field checkbox-group compact">
            <legend>Kinds of rule it changes</legend>
            <Help>Used for the competition screen and to find similar past changes.</Help>
            {RESTRICTIONS.map((r) => (
              <Checkbox
                key={r.value}
                label={r.label}
                checked={restrictions.includes(r.value)}
                onChange={(on) =>
                  set((x) => {
                    const s = new Set((x.conduct?.restrictions ?? []) as string[]);
                    if (on) s.add(r.value);
                    else s.delete(r.value);
                    return { ...x, conduct: { ...x.conduct!, restrictions: RESTRICTIONS.map((y) => y.value).filter((y) => s.has(y)) } };
                  })
                }
              />
            ))}
          </fieldset>
          <LeverIndustries draft={draft} value={c.industries} onChange={(v) => set((x) => ({ ...x, conduct: { ...x.conduct!, industries: v } }))} />
        </>
      )}
    </LeverCard>
  );
}

function LabourCard({ draft, set, outcomes }: CardProps) {
  const lab = draft.levers.labour;
  const put = (patch: Partial<NonNullable<Levers["labour"]>>) =>
    set((x) => {
      const next = { ...x.labour, ...patch };
      return { ...x, labour: next.licensing || next.nonCompetes ? next : undefined };
    });
  return (
    <LeverCard
      id="labour"
      title="Workers: occupational licensing and non-compete clauses"
      intro="Changes to how hard it is to enter a licensed occupation, and to how many workers are bound by non-compete clauses. The tool follows the Productivity Commission's 2024 modelling."
      enabled={!!lab}
      toggleLabel="The policy changes licensing or non-compete clauses"
      onToggle={(on) => set((x) => ({ ...x, labour: on ? { nonCompetes: { coveredShareChange: 0 } } : undefined }))}
      channels={["C8"]}
      outcomes={outcomes}
    >
      {lab && (
        <>
          <Checkbox
            label="Occupational licensing"
            checked={!!lab.licensing}
            onChange={(on) => put({ licensing: on ? { occupations: ["000000"], stringencyChange: 0 } : undefined })}
            testId="lever-licensing-toggle"
          />
          {lab.licensing && (
            <div className="sub-card">
              <TextField
                label="Occupations (OSCA 2024 codes)"
                help="Six-digit codes, separated by commas, e.g. 381231 for electricians."
                value={lab.licensing.occupations.join(", ")}
                onChange={(v) => put({ licensing: { ...lab.licensing!, occupations: v.split(/[,\s]+/).filter(Boolean) } })}
              />
              <QuantityField
                label="Change in occupational entry regulation stringency"
                help="OECD index points; negative for less stringent. The PC modelled a cut of 0.5."
                unit="index points"
                min={-6}
                max={6}
                value={lab.licensing.stringencyChange}
                onChange={(q) => put({ licensing: { ...lab.licensing!, stringencyChange: q } })}
                testId="lever-stringency"
              />
              <Checkbox label="Through mutual recognition of licences" checked={!!lab.licensing.mutualRecognition} onChange={(on) => put({ licensing: { ...lab.licensing!, mutualRecognition: on } })} />
              <LeverIndustries draft={draft} value={lab.licensing.industries} onChange={(v) => put({ licensing: { ...lab.licensing!, industries: v } })} />
            </div>
          )}
          <Checkbox label="Non-compete clauses" checked={!!lab.nonCompetes} onChange={(on) => put({ nonCompetes: on ? { coveredShareChange: 0 } : undefined })} testId="lever-noncompetes-toggle" />
          {lab.nonCompetes && (
            <div className="sub-card">
              <QuantityField
                label="Change in the share of workers bound"
                help="In percentage points of all workers; one in five are bound now, so a ban is −20."
                scale={100}
                unit="pp"
                min={-1}
                max={1}
                value={lab.nonCompetes.coveredShareChange}
                onChange={(q) => put({ nonCompetes: { ...lab.nonCompetes!, coveredShareChange: q } })}
                testId="lever-noncompete-share"
              />
              <LeverIndustries draft={draft} value={lab.nonCompetes.industries} onChange={(v) => put({ nonCompetes: { ...lab.nonCompetes!, industries: v } })} />
            </div>
          )}
        </>
      )}
    </LeverCard>
  );
}

const CUSTOM_TYPES: ShockType[] = ["mfp", "labourProductivity", "price", "rent"];

function CustomCard({ draft, set, outcomes }: CardProps) {
  const list = draft.levers.custom ?? [];
  const put = (i: number, patch: Partial<(typeof list)[number]>) => set((x) => ({ ...x, custom: (x.custom ?? []).map((s, j) => (j === i ? { ...s, ...patch } : s)) }));
  const channels = [...new Set(list.map((s) => s.channel))] as ChannelId[];
  const first = draft.scope.industries[0]?.anzsic ?? "A";
  return (
    <LeverCard
      id="custom"
      title="Your own estimates"
      intro="An effect the levers don't cover, from your own analysis or a study. It is graded D unless you cite a source (then C). Only productivity effects reach GDP; prices and rents are reported beside it."
      enabled={list.length > 0}
      toggleLabel="Add an effect of my own"
      onToggle={(on) => set((x) => ({ ...x, custom: on ? [{ id: "custom-1", channel: "C12", industry: first, type: "mfp", size: 0, justification: "" }] : [] }))}
      channels={channels}
      outcomes={outcomes}
    >
      {list.map((s, i) => (
        <div className="sub-card" key={i}>
          <SelectField label="Channel" value={s.channel} options={CHANNEL_IDS.map((c) => ({ value: c, label: `${c} ${CHANNELS[c].name}` }))} onChange={(v) => put(i, { channel: v })} />
          <SelectField label="Industry" value={s.industry} options={draft.scope.industries.map((x) => ({ value: x.anzsic, label: x.anzsic }))} onChange={(v) => put(i, { industry: v })} />
          <SelectField label="Kind of effect" value={s.type} options={CUSTOM_TYPES.map((t) => ({ value: t, label: SHOCK_TYPES[t].label }))} onChange={(v) => put(i, { type: v })} />
          <QuantityField label={`Size (${SHOCK_TYPES[s.type].unit})`} min={-1e12} max={1e12} value={s.size} onChange={(q) => put(i, { size: q })} />
          <SelectField
            label="If a lever already feeds this channel and industry"
            value={s.relation ?? "adds"}
            options={[
              { value: "adds", label: "Add it to the lever's effect" },
              { value: "replaces", label: "Replace the lever's effect" },
            ]}
            onChange={(v) => put(i, { relation: v })}
          />
          <TextField label="Why (required)" multiline value={s.justification} onChange={(v) => put(i, { justification: v })} />
          <TextField label="Source (optional)" help="A citation lifts the grade from D to C." value={s.source?.description ?? ""} onChange={(v) => put(i, { source: v ? { description: v } : undefined })} />
          <button type="button" className="danger" onClick={() => set((x) => ({ ...x, custom: (x.custom ?? []).filter((_, j) => j !== i) }))}>
            Remove this estimate
          </button>
        </div>
      ))}
      {list.length > 0 && (
        <button type="button" onClick={() => set((x) => ({ ...x, custom: [...(x.custom ?? []), { id: `custom-${(x.custom ?? []).length + 1}`, channel: "C12", industry: first, type: "mfp", size: 0, justification: "" }] }))}>
          Add another estimate
        </button>
      )}
    </LeverCard>
  );
}

