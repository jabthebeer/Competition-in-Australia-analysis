import { useId, useState } from "react";
import { PARAMETERS, type Population } from "../../engine/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import { Checkbox, Help, IntegerField, QuantityField, RadioGroup, SelectField, TextField } from "../components/fields";
import { COHORT_LABELS, GROUP_LABELS } from "../format";
import { addOption, addPopulation, populationBlockers, removeOption, removePopulation, setDuration, setProposalType, updateOption, updatePopulation } from "../model";

const BANDS = Object.entries(PARAMETERS.employmentBands) as [Population["employmentBand"] & string, { cohort: string }][];
const BAND_LABELS: Record<string, string> = { nonEmploying: "Non-employing", "1-4": "1–4 employees", "5-19": "5–19 employees", "20-199": "20–199 employees", "200+": "200 or more employees" };

export function ProposalPage({ proposal: p, update, go }: PageProps) {
  const sunset = p.remakesSunsettingInstrument === undefined ? "unsure" : p.remakesSunsettingInstrument ? "yes" : "no";
  return (
    <>
      <PageHeading>Step 1: The proposal</PageHeading>
      <p>Describe the proposal, who it affects, and the options you want to compare. Each option gets its own Regulatory Burden Estimate (RBE) table.</p>

      <section aria-labelledby="about-heading">
        <h2 id="about-heading">About the proposal</h2>
        <TextField label="Title" value={p.title} onChange={(v) => update((q) => ({ ...q, title: v }))} testId="title" />
        <TextField label="Description (optional)" multiline value={p.description ?? ""} onChange={(v) => update((q) => ({ ...q, description: v || undefined }))} />
        <RadioGroup
          label="What kind of proposal is it?"
          value={p.proposalType}
          options={[
            { value: "reform", label: "Reform an existing regulation", help: "Replace it with a less burdensome version, obligation by obligation." },
            { value: "new", label: "New regulation", help: "There is no current regime to compare against." },
            { value: "repeal", label: "Remove a regulation outright" },
          ]}
          onChange={(v) => update((q) => setProposalType(q, v))}
          testId="proposal-type"
        />
        <IntegerField
          label="Analysis period (years)"
          help="The framework uses 10 years by default. Use a shorter period only if the policy ends sooner, e.g. a 3-year programme (RBM p. 6)."
          value={p.durationYears}
          min={1}
          max={PARAMETERS.duration.maxYearsWithoutOverride}
          unit="years"
          onChange={(n) => update((q) => setDuration(q, n))}
          testId="duration"
        />
        {p.durationYears !== 10 && (
          <TextField
            label="Why a different period?"
            value={p.durationOverride?.justification ?? ""}
            onChange={(v) => update((q) => ({ ...q, durationOverride: v ? { justification: v, source: { description: "Recorded by the user" } } : undefined }))}
          />
        )}
        <RadioGroup
          label="Who is making the change?"
          value={p.jurisdiction}
          options={[
            { value: "commonwealthOnly", label: "The Commonwealth only" },
            { value: "interJurisdictional", label: "An inter-jurisdictional reform", help: "e.g. agreed by National Cabinet or a ministerial council. Commonwealth and state or territory changes are netted together (RBM p. 6)." },
          ]}
          onChange={(v) => update((q) => ({ ...q, jurisdiction: v }))}
          testId="jurisdiction"
        />
        <RadioGroup
          label="Will the change be made by remaking a sunsetting legislative instrument?"
          help="If so, the Impact Analysis Framework measures it against no instrument (the instrument sunsetting), not against current settings."
          value={sunset}
          options={[
            { value: "no", label: "No" },
            { value: "yes", label: "Yes" },
            { value: "unsure", label: "Not sure" },
          ]}
          inline
          onChange={(v) =>
            update((q) => {
              const next = { ...q };
              if (v === "unsure") delete next.remakesSunsettingInstrument;
              else next.remakesSunsettingInstrument = v === "yes";
              if (v === "yes") next.baseline = "noInstrument";
              if (v === "no") next.baseline = "statusQuo";
              return next;
            })
          }
        />
        <RadioGroup
          label="Measure the change against"
          value={p.baseline}
          options={[
            { value: "statusQuo", label: "Current settings (default)" },
            { value: "noInstrument", label: "No instrument (a sunsetting instrument being remade)" },
          ]}
          onChange={(v) => update((q) => ({ ...q, baseline: v }))}
          testId="baseline"
        />
      </section>

      <section aria-labelledby="who-heading">
        <h2 id="who-heading">Who is affected</h2>
        <p>Add a group for each set of entities or people that bears different costs, for example small, medium and large businesses (RBM pp. 7–8).</p>
        {p.populations.map((pop, i) => (
          <PopulationEditor key={pop.id} index={i} pop={pop} canRemove={p.populations.length > 1} blockers={populationBlockers(p, pop.id)} update={update} />
        ))}
        <button type="button" onClick={() => update(addPopulation)}>
          Add another affected group
        </button>
      </section>

      <section aria-labelledby="options-heading">
        <h2 id="options-heading">Options to compare</h2>
        <p>The framework needs an RBE table for every viable option. The status quo is always $0.</p>
        {p.options.map((o) => (
          <div className="card" key={o.id}>
            <TextField label={o.isStatusQuo ? "Status quo option name" : "Option name"} value={o.name} onChange={(v) => update((q) => updateOption(q, o.id, (x) => (x.name = v)))} />
            {p.options.length > 1 && (
              <button type="button" className="danger" onClick={() => update((q) => removeOption(q, o.id))}>
                Remove option "{o.name}"
              </button>
            )}
          </div>
        ))}
        <p className="button-row">
          <button type="button" onClick={() => update((q) => addOption(q, `Option ${String.fromCharCode(65 + q.options.filter((o) => !o.isStatusQuo).length)}`))}>
            Add a reform option
          </button>
          <button type="button" onClick={() => update((q) => addOption(q, "Outright repeal", "repeal"))}>
            Add an outright repeal option
          </button>
        </p>
      </section>
      <NextStep go={go} to={p.proposalType === "new" ? "options" : "current"}>
        {p.proposalType === "new" ? "Next: describe the new obligations" : "Next: the current regime"}
      </NextStep>
    </>
  );
}

function PopulationEditor({ pop, index, canRemove, blockers, update }: { pop: Population; index: number; canRemove: boolean; blockers: string[]; update: PageProps["update"] }) {
  const set = (mutate: (x: Population) => void) => update((q) => updatePopulation(q, pop.id, mutate));
  const bands = BANDS.filter(([, b]) => pop.cohort === "all" || b.cohort === pop.cohort);
  return (
    <fieldset className="card" data-testid={`population-${index}`}>
      <legend>Affected group {index + 1}</legend>
      <TextField label="Name" value={pop.label} onChange={(v) => set((x) => (x.label = v))} testId="pop-label" />
      <div className="row">
        <SelectField
          label="Stakeholder group (RBE table column)"
          value={pop.group}
          options={(Object.keys(GROUP_LABELS) as Population["group"][]).map((g) => ({ value: g, label: GROUP_LABELS[g] }))}
          onChange={(v) => set((x) => (x.group = v))}
          testId="pop-group"
        />
        <SelectField
          label="Size"
          value={pop.cohort}
          options={(Object.keys(COHORT_LABELS) as Population["cohort"][]).map((c) => ({ value: c, label: COHORT_LABELS[c] }))}
          onChange={(v) =>
            set((x) => {
              x.cohort = v;
              if (x.employmentBand && v !== "all" && PARAMETERS.employmentBands[x.employmentBand].cohort !== v) delete x.employmentBand;
            })
          }
          testId="pop-cohort"
        />
      </div>
      <QuantityField
        label={`Number of ${pop.group === "individual" ? "individuals" : pop.group === "communityOrg" ? "organisations" : "businesses"}`}
        help="Use the best available data, and record its source. Enter a range if unsure: the midpoint is used."
        value={pop.count}
        min={0}
        onChange={(q) => set((x) => (x.count = q))}
        testId="pop-count"
      />
      <TextField label="Source of this number" value={pop.source?.description ?? ""} onChange={(v) => set((x) => (x.source = v ? { ...(x.source ?? {}), description: v } : undefined))} placeholder="e.g. regulator's register, 2026" />
      <details className="more">
        <summary>More about this group (optional)</summary>
        <SelectField
          label="ABS employment-size band"
          help="Lets results be matched to ABS business counts and entry/exit data."
          value={pop.employmentBand ?? ""}
          options={[{ value: "", label: "Not set" }, ...bands.map(([b]) => ({ value: b, label: BAND_LABELS[b] ?? b }))]}
          onChange={(v) => set((x) => (v ? (x.employmentBand = v as Population["employmentBand"]) : delete x.employmentBand))}
        />
        <AnzsicField value={pop.industry} onChange={(v) => set((x) => (v ? (x.industry = v) : delete x.industry))} />
        <SelectField
          label="Type of entity"
          value={pop.entityType}
          options={[
            { value: "private", label: "Private or community sector" },
            { value: "gbe", label: "Government Business Enterprise" },
            { value: "publicUniversity", label: "Public university" },
            { value: "foreignGovOwnedBusiness", label: "Business owned by a foreign government" },
            { value: "governmentAgency", label: "Government agency (excluded: government-to-government)" },
          ]}
          onChange={(v) => set((x) => (x.entityType = v))}
        />
        {pop.group === "individual" && (
          <Checkbox label="These individuals live outside Australia" help="The $41 non-work rate applies only to Australian residents (RBM p. 13)." checked={pop.nonResident} onChange={(v) => set((x) => (x.nonResident = v))} />
        )}
      </details>
      {canRemove && (
        <>
          <button type="button" className="danger" disabled={blockers.length > 0} onClick={() => update((q) => removePopulation(q, pop.id))} aria-describedby={blockers.length ? `${pop.id}-blockers` : undefined}>
            Remove this group
          </button>
          {blockers.length > 0 && (
            <Help id={`${pop.id}-blockers`}>
              Can't remove yet: {blockers.join(", ")} {blockers.length === 1 ? "applies" : "apply"} only to this group.
            </Help>
          )}
        </>
      )}
    </fieldset>
  );
}

function AnzsicField({ value, onChange }: { value?: string; onChange: (v: string | undefined) => void }) {
  const id = useId();
  const [text, setText] = useState(value ?? "");
  const valid = text === "" || /^([A-S]|\d{2}|\d{3}|\d{4})$/.test(text);
  return (
    <div className="field">
      <label htmlFor={id}>ANZSIC 2006 industry code</label>
      <Help id={`${id}-help`}>A division letter (A–S) or a 2–4 digit code, e.g. "G" for retail trade.</Help>
      <input
        id={id}
        type="text"
        value={text}
        aria-describedby={`${id}-help${valid ? "" : ` ${id}-err`}`}
        aria-invalid={valid ? undefined : true}
        onChange={(e) => {
          const v = e.target.value.trim().toUpperCase();
          setText(v);
          if (v === "") onChange(undefined);
          else if (/^([A-S]|\d{2}|\d{3}|\d{4})$/.test(v)) onChange(v);
        }}
      />
      {!valid && (
        <span className="error" id={`${id}-err`} role="alert">
          Use a letter A–S or a 2–4 digit code
        </span>
      )}
    </div>
  );
}
