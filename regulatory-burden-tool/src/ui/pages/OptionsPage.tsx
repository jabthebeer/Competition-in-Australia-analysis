import { useState } from "react";
import { reformDiff, verdictText, type Obligation, type OptionResult, type Proposal } from "../../engine/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import { ObligationEditor, describeTiming } from "../components/ObligationEditor";
import { Checkbox, Help, IntegerField, RadioGroup, formatQuantity } from "../components/fields";
import { CATEGORY_LABELS, formatMoney, moneyText } from "../format";
import { LEVERS } from "../levers";
import {
  addOptionObligation,
  newObligation,
  reformStatus,
  removeOptionObligation,
  setReformStatus,
  updateOption,
  updateOptionObligation,
  type Category,
  type ReformStatus,
} from "../model";
import { sideAnnual } from "./CurrentRegimePage";

const TRANSITION_PRESETS: { label: string; category: Category; name: string }[] = [
  { label: "Familiarisation with the new rules", category: "administrative", name: "Familiarisation with the new rules" },
  { label: "Updating systems and processes", category: "substantive", name: "Updating systems and processes" },
  { label: "Retraining staff", category: "administrative", name: "Retraining staff" },
  { label: "Professional advice", category: "substantive", name: "Professional advice on the changes" },
];

export function OptionsPage({ proposal, update, computed, go }: PageProps) {
  const editable = proposal.options.filter((o) => !o.isStatusQuo);
  const [selected, setSelected] = useState<string>(editable[0]?.id ?? proposal.options[0]!.id);
  const option = proposal.options.find((o) => o.id === selected) ?? proposal.options[0]!;
  const index = proposal.options.indexOf(option);
  const result = computed.ok ? computed.result.options[index] : undefined;

  return (
    <>
      <PageHeading>Step 3: Reform options</PageHeading>
      <p>For each option, say what happens to each existing obligation, then add any new replacement obligations and the one-off costs of switching over.</p>
      <nav className="option-tabs" aria-label="Options">
        {proposal.options.map((o) => (
          <button key={o.id} type="button" aria-pressed={o.id === option.id} onClick={() => setSelected(o.id)} data-testid={`option-tab-${o.id}`}>
            {o.name}
          </button>
        ))}
      </nav>
      {option.isStatusQuo ? (
        <p className="summary-box">The status quo keeps every obligation as it is today, so its change in regulatory burden is $0. It is shown alongside the other options in the results.</p>
      ) : (
        <OptionEditor proposal={proposal} optionId={option.id} update={update} result={result} />
      )}
      <NextStep go={go} to="results">
        Next: results
      </NextStep>
    </>
  );
}

function OptionEditor({ proposal, optionId, update, result }: { proposal: Proposal; optionId: string; update: PageProps["update"]; result?: OptionResult }) {
  const option = proposal.options.find((o) => o.id === optionId)!;
  const existing = option.obligations.filter((o) => o.current);
  const added = option.obligations.filter((o) => !o.current);
  const T = proposal.durationYears;
  return (
    <>
      <section aria-labelledby="opt-heading">
        <h2 id="opt-heading">{option.name}</h2>
        {result && (
          <div className="summary-box" aria-live="polite" data-testid="option-summary">
            <strong>{verdictText(result.verdict)}</strong> (RBE total {moneyText(result.rbe.total)}). See the results page for the full RBE table.
          </div>
        )}
        <div className="row">
          <IntegerField
            label="Reform starts in year"
            help="Use a later year for deferred commencement: nothing changes until then."
            value={option.timing.reformStartYear}
            min={1}
            max={T}
            onChange={(n) => update((p) => updateOption(p, optionId, (o) => (o.timing.reformStartYear = n)))}
            testId="reform-start"
          />
          <IntegerField
            label="Years of dual running"
            help="Current obligations continue alongside the new ones for this many years, so savings start later."
            value={option.timing.overlapYears}
            min={0}
            max={T}
            onChange={(n) => update((p) => updateOption(p, optionId, (o) => (o.timing.overlapYears = n)))}
            testId="overlap"
          />
        </div>
      </section>

      {existing.length > 0 && (
        <section aria-labelledby="existing-heading">
          <h2 id="existing-heading">Existing obligations</h2>
          {existing.map((o) => (
            <ExistingObligation key={o.id} proposal={proposal} optionId={optionId} obligation={o} update={update} result={result} />
          ))}
        </section>
      )}

      <section aria-labelledby="new-heading">
        <h2 id="new-heading">{proposal.proposalType === "new" ? "Obligations of the new regulation" : "New replacement obligations"}</h2>
        {proposal.proposalType !== "new" && <p>Obligations the reform introduces, for example a self-declaration that replaces an audit.</p>}
        {added.map((o) => (
          <OptionObligation key={o.id} proposal={proposal} optionId={optionId} obligation={o} list="obligations" update={update} result={result} />
        ))}
        <div className="button-row">
          {(["administrative", "substantive", "delay"] as const).map((c) => (
            <button key={c} type="button" onClick={() => update((p) => addOptionObligation(p, optionId, newObligation(c, proposal.populations, "new"), "obligations"))}>
              Add a new {CATEGORY_LABELS[c].toLowerCase()} cost
            </button>
          ))}
        </div>
      </section>

      <section aria-labelledby="transition-heading">
        <h2 id="transition-heading">Transition costs</h2>
        <p>One-off costs of switching over, spread across the analysis period. They usually fall in the year the reform starts.</p>
        {option.transitions.map((o) => (
          <OptionObligation key={o.id} proposal={proposal} optionId={optionId} obligation={o} list="transitions" update={update} result={result} />
        ))}
        <div className="button-row">
          {TRANSITION_PRESETS.map((t) => (
            <button key={t.label} type="button" onClick={() => update((p) => addOptionObligation(p, optionId, newObligation(t.category, proposal.populations, "transition", t.name), "transitions"))}>
              Add: {t.label}
            </button>
          ))}
        </div>
      </section>
    </>
  );
}

function ExistingObligation({ proposal, optionId, obligation: o, update, result }: { proposal: Proposal; optionId: string; obligation: Obligation; update: PageProps["update"]; result?: OptionResult }) {
  const status = reformStatus(o);
  const change = result ? result.breakdowns.obligation[o.id] ?? "0" : "0";
  return (
    <div className="card" data-testid={`reform-obligation-${o.name || o.id}`}>
      <div className="card-header">
        <div>
          <h3>{o.name || "Unnamed obligation"}</h3>
          <span className="card-meta">
            Today: {formatMoney(sideAnnual(result, o.id, "current"), "dollars")} a year · Change under this option: <strong>{formatMoney(change, "dollars")}</strong> a year
          </span>
        </div>
      </div>
      <RadioGroup
        label="Under this option"
        value={status}
        inline
        options={[
          { value: "keep", label: "Keep as is" },
          { value: "modify", label: "Modify" },
          { value: "remove", label: "Remove" },
        ]}
        onChange={(v: ReformStatus) => update((p) => setReformStatus(p, optionId, o.id, v))}
        testId="reform-status"
      />
      {status === "remove" && (
        <Help>
          Only future costs are saved. If businesses would keep doing some of this anyway, set the do-anyway share for this obligation in step 2 (now {formatQuantity(o.doAnywayShare, 100, "%")}).
        </Help>
      )}
      {status === "modify" && (
        <>
          <fieldset className="field">
            <legend>Reform levers</legend>
            <Help>Tick what the reform does. The inputs each lever usually changes are highlighted below.</Help>
            {LEVERS.map((l) => (
              <Checkbox
                key={l.id}
                label={l.label}
                help={o.levers.includes(l.id) ? l.help : undefined}
                checked={o.levers.includes(l.id)}
                onChange={(on) =>
                  update((p) =>
                    updateOptionObligation(p, optionId, o.id, (ob) => {
                      ob.levers = on ? [...ob.levers.filter((x) => x !== "removeObligation"), l.id] : ob.levers.filter((x) => x !== l.id);
                    }),
                  )
                }
                testId={`lever-${l.id}`}
              />
            ))}
          </fieldset>
          <ObligationEditor proposal={proposal} obligation={o} mode="reform" result={result} onChange={(mutate) => update((p) => updateOptionObligation(p, optionId, o.id, mutate))} />
          <DiffSummary proposal={proposal} obligation={o} />
        </>
      )}
    </div>
  );
}

function OptionObligation({ proposal, optionId, obligation: o, list, update, result }: { proposal: Proposal; optionId: string; obligation: Obligation; list: "obligations" | "transitions"; update: PageProps["update"]; result?: OptionResult }) {
  const [open, setOpen] = useState(true);
  const change = result ? result.breakdowns.obligation[o.id] ?? "0" : "0";
  return (
    <div className="card" data-testid={`${list === "transitions" ? "transition" : "new-obligation"}-${o.name || o.id}`}>
      <div className="card-header">
        <div>
          <h3>{o.name || "Unnamed obligation"}</h3>
          <span className="card-meta">
            {CATEGORY_LABELS[o.category]} · {o.reformed ? describeTiming(o.reformed.timing) : ""} · Adds <strong>{formatMoney(change, "dollars")}</strong> a year on average
          </span>
        </div>
        <div className="button-row">
          <button type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
            {open ? "Close" : "Edit"}
          </button>
          <button type="button" className="danger" onClick={() => update((p) => removeOptionObligation(p, optionId, o.id, list))}>
            Remove
          </button>
        </div>
      </div>
      {open && <ObligationEditor proposal={proposal} obligation={o} mode={list === "transitions" ? "transition" : "new"} result={result} onChange={(mutate) => update((p) => updateOptionObligation(p, optionId, o.id, mutate, list))} />}
    </div>
  );
}

const FIELD_LABELS: Record<string, string> = {
  hours: "hours each time",
  timesPerYear: "times a year",
  staff: "staff per entity",
  rateId: "labour rate",
  unitCost: "price each time",
  approvalDelay: "time for the regulator to decide",
  applicationDelay: "time to complete the application",
  readyAfter: "ready to operate after",
  netIncomePerUnit: "net income forgone",
  extraExpensesPerUnit: "extra expenses",
  entities: "number affected",
  complianceRate: "expected compliance rate",
  perEntityPerActiveYear: "subsidy",
  unit: "delay unit",
  waitingOnGovernment: "waiting on government",
};

function DiffSummary({ proposal, obligation }: { proposal: Proposal; obligation: Obligation }) {
  const diff = reformDiff(obligation);
  const label = (path: string) => {
    const parts = path.split(".");
    if (parts[0] === "lines") {
      const pop = proposal.populations.find((p) => p.id === parts[1])?.label ?? parts[1];
      const field = parts.filter((x) => !["lines", parts[1], "labour", "purchase", "delay", "subsidy", "source", "low", "high"].includes(x)).pop() ?? "";
      const bound = parts.includes("low") ? " (low)" : parts.includes("high") ? " (high)" : "";
      return `${pop}: ${FIELD_LABELS[field] ?? field}${bound}`;
    }
    if (parts[0] === "timing") return "Timing";
    if (parts[0] === "costType") return "How the cost is incurred";
    return path;
  };
  const show = (v: unknown) => (v === undefined ? "—" : typeof v === "number" ? String(v) : typeof v === "boolean" ? (v ? "yes" : "no") : String(v));
  const rows = diff.filter((d) => !d.path.endsWith("populationId"));
  const added = diff.filter((d) => d.path.endsWith("populationId") && d.current === undefined).map((d) => proposal.populations.find((p) => p.id === d.reformed)?.label ?? String(d.reformed));
  const exempted = diff.filter((d) => d.path.endsWith("populationId") && d.reformed === undefined).map((d) => proposal.populations.find((p) => p.id === d.current)?.label ?? String(d.current));
  const timingChanged = rows.some((r) => r.path.startsWith("timing"));
  const fieldRows = rows.filter((r) => !r.path.startsWith("timing") && !(exempted.length && exempted.some((e) => label(r.path).startsWith(`${e}:`))) && !(added.length && added.some((a) => label(r.path).startsWith(`${a}:`))));
  return (
    <div className="diff" aria-live="polite" data-testid="diff-summary">
      <h4>What this option changes</h4>
      {diff.length === 0 ? (
        <p>Nothing yet: the reformed version is the same as today. Change the highlighted inputs above.</p>
      ) : (
        <ul>
          {timingChanged && obligation.current && obligation.reformed && (
            <li>
              Timing: {describeTiming(obligation.current.timing)} → {describeTiming(obligation.reformed.timing)}
            </li>
          )}
          {exempted.map((e) => (
            <li key={`ex-${e}`}>Exempts: {e}</li>
          ))}
          {added.map((a) => (
            <li key={`add-${a}`}>Now also applies to: {a}</li>
          ))}
          {fieldRows.map((d) => (
            <li key={d.path}>
              {label(d.path)}: {show(d.current)} → {show(d.reformed)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

