import { useId, useMemo, useState } from "react";
import { covers } from "../../productivity/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import type { BriefDraft, ScopeIndustryDraft, SizeBand } from "../briefModel";
import { JURISDICTIONS } from "../briefModel";
import { useCostingContext } from "../costingContext";
import { Checkbox, Help, QuantityField, SelectField, TextField } from "../components/fields";
import { fmtNum } from "../format";
import { anzsicCodes, industryFacts, type AnzsicCode } from "../scopeData";

const BANDS: { value: SizeBand; label: string }[] = [
  { value: "nonEmploying", label: "Non-employing" },
  { value: "1-4", label: "1–4 employees" },
  { value: "5-19", label: "5–19 employees" },
  { value: "20-199", label: "20–199 employees" },
  { value: "200+", label: "200 or more employees" },
];

type Industry = ScopeIndustryDraft;

export function ScopePage({ proposal, draft, updateDraft, go }: PageProps) {
  const loaded = useCostingContext();
  const names = useMemo(() => (loaded.status === "ready" ? anzsicCodes(loaded.parameters) : new Map<string, AnzsicCode>()), [loaded]);
  const industries = draft.scope.industries;
  const setIndustries = (fn: (list: Industry[]) => Industry[]) => updateDraft((d) => ({ ...d, scope: { ...d.scope, industries: fn(d.scope.industries) } }));
  const fromBurden = [...new Set(proposal.populations.map((p) => p.industry).filter((c): c is string => !!c))].filter((c) => !industries.some((i) => covers(i.anzsic, c)));
  const states = JURISDICTIONS.filter((j) => j.value !== "CTH");

  return (
    <>
      <PageHeading>Step 2: Scope</PageHeading>
      <p>
        List the industries the policy reaches, at any ANZSIC 2006 level from a division (a letter) to a class (four digits). Exposure is the share of an industry's activity the policy reaches. The productivity levers apply to these industries unless a lever names its own.
      </p>

      <section aria-labelledby="industries-heading">
        <h2 id="industries-heading">Industries</h2>
        {industries.length === 0 && <p data-testid="scope-empty">No industries yet. The productivity costing needs at least one.</p>}
        {industries.map((ind, i) => (
          <IndustryEditor
            key={i}
            index={i}
            industry={ind}
            name={names.get(ind.anzsic)}
            known={names.size > 0}
            update={(next) => setIndustries((list) => list.map((x, j) => (j === i ? next : x)))}
            remove={() => setIndustries((list) => list.filter((_, j) => j !== i))}
          />
        ))}
        <AddIndustry names={names} onAdd={(code) => setIndustries((list) => [...list, { anzsic: code, exposure: 1, role: "direct" }])} />
        {fromBurden.length > 0 && (
          <p>
            <button type="button" onClick={() => setIndustries((list) => [...list, ...fromBurden.map((anzsic) => ({ anzsic, exposure: 1, role: "direct" as const }))])} data-testid="scope-from-burden">
              Add the burden proposal's industries ({fromBurden.join(", ")})
            </button>
          </p>
        )}
      </section>

      <section aria-labelledby="who-scope-heading">
        <h2 id="who-scope-heading">Business sizes and places</h2>
        <fieldset className="field checkbox-group">
          <legend>Business sizes affected</legend>
          {BANDS.map((b) => (
            <Checkbox
              key={b.value}
              label={b.label}
              checked={(draft.scope.sizeBands ?? BANDS.map((x) => x.value)).includes(b.value)}
              onChange={(on) =>
                updateDraft((d) => {
                  const set = new Set(d.scope.sizeBands ?? BANDS.map((x) => x.value));
                  if (on) set.add(b.value);
                  else set.delete(b.value);
                  return { ...d, scope: { ...d.scope, sizeBands: BANDS.map((x) => x.value).filter((x) => set.has(x)) } };
                })
              }
            />
          ))}
        </fieldset>
        <fieldset className="field checkbox-group">
          <legend>States and territories affected</legend>
          <Help>Leave all unticked if the policy applies everywhere within its jurisdictions.</Help>
          {states.map((s) => (
            <Checkbox
              key={s.value}
              label={s.label}
              checked={(draft.scope.states ?? []).includes(s.value as never)}
              onChange={(on) =>
                updateDraft((d) => {
                  const set = new Set(d.scope.states ?? []);
                  if (on) set.add(s.value as never);
                  else set.delete(s.value as never);
                  const list = states.map((x) => x.value).filter((x) => set.has(x as never)) as BriefDraft["scope"]["states"];
                  const { states: _drop, ...rest } = d.scope;
                  return { ...d, scope: list && list.length ? { ...rest, states: list } : rest };
                })
              }
            />
          ))}
        </fieldset>
      </section>

      <section aria-labelledby="facts-heading">
        <h2 id="facts-heading">What the data says about these industries</h2>
        {loaded.status === "loading" && <p>Loading the bundled data…</p>}
        {loaded.status === "error" && <p className="banner error">{loaded.problem}</p>}
        {loaded.status === "ready" && industries.length > 0 && (
          <div className="table-wrap">
            <table data-testid="scope-facts">
              <caption>
                Businesses and entry and exit rates: ABS Counts of Australian Businesses ({loaded.ctx.sizeYear}). Value added: ABS input-output tables ({loaded.ctx.ioYear}), compensation of employees plus gross operating surplus and mixed income, rescaled to {loaded.ctx.gdpYear} GDP. Employment: ABS Australian Industry ({loaded.ctx.industryByBandYear}), divisions only.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Industry</th>
                  <th scope="col" className="num">Businesses</th>
                  <th scope="col" className="num">Entry rate</th>
                  <th scope="col" className="num">Exit rate</th>
                  <th scope="col" className="num">Value added ($m)</th>
                  <th scope="col" className="num">Employment (000)</th>
                </tr>
              </thead>
              <tbody>
                {industries.map((ind, i) => {
                  const f = industryFacts(ind.anzsic, loaded.ctx, loaded.parameters, names);
                  return (
                    <tr key={i}>
                      <th scope="row">
                        {ind.anzsic} {f.name ?? ""}
                      </th>
                      <td className="num">{f.businesses !== undefined ? fmtNum(f.businesses) : "—"}</td>
                      <td className="num">{f.entryRatePct !== undefined ? `${f.entryRatePct.toFixed(1)}%` : "—"}</td>
                      <td className="num">{f.exitRatePct !== undefined ? `${f.exitRatePct.toFixed(1)}%` : "—"}</td>
                      <td className="num">{f.valueAdded > 0 ? fmtNum(Math.round(f.valueAdded)) : "—"}</td>
                      <td className="num">{f.employment !== undefined ? fmtNum(Math.round(f.employment * 10) / 10) : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <Help>CABEE counts businesses registered for GST with an ABN; groups (three-digit codes) are not published, so they show a dash.</Help>
      </section>

      <NextStep go={go} to={proposal.proposalType === "new" ? "options" : "current"}>
        {proposal.proposalType === "new" ? "Next: describe the new obligations" : "Next: the current regime"}
      </NextStep>
    </>
  );
}

function IndustryEditor(props: { index: number; industry: Industry; name?: AnzsicCode; known: boolean; update: (i: Industry) => void; remove: () => void }) {
  const { industry: ind, update } = props;
  const label = props.name ? `${ind.anzsic} ${props.name.name} (${props.name.level})` : ind.anzsic;
  return (
    <div className="card" data-testid={`scope-industry-${props.index}`}>
      <div className="card-header">
        <h3>{label}</h3>
        <button type="button" className="danger" onClick={props.remove}>
          Remove {ind.anzsic}
        </button>
      </div>
      {props.known && !props.name && <p className="error">{ind.anzsic} is not an ANZSIC 2006 code.</p>}
      <QuantityField
        label="Exposure"
        help="The share of the industry's activity the policy reaches: 100% if it applies to every business in the industry."
        value={ind.exposure ?? 1}
        scale={100}
        min={0}
        max={1}
        unit="%"
        onChange={(q) => update({ ...ind, exposure: q })}
      />
      <SelectField
        label="How the policy reaches it"
        value={ind.role ?? "direct"}
        options={[
          { value: "direct", label: "Directly (the rules apply to it)" },
          { value: "indirect", label: "Indirectly (through suppliers or customers)" },
        ]}
        onChange={(v) => update({ ...ind, role: v })}
      />
      <TextField label="Note (optional)" value={ind.note ?? ""} onChange={(v) => update({ ...ind, note: v || undefined })} />
    </div>
  );
}

function AddIndustry({ names, onAdd }: { names: Map<string, AnzsicCode>; onAdd: (code: string) => void }) {
  const [text, setText] = useState("");
  const id = useId();
  const listId = `${id}-codes`;
  const code = text.trim().split(/\s/)[0]?.toUpperCase() ?? "";
  const valid = /^([A-S]|\d{2}|\d{3}|\d{4})$/.test(code) && (names.size === 0 || names.has(code));
  return (
    <div className="field add-industry">
      <label htmlFor={id}>Add an industry (ANZSIC code or name)</label>
      <Help id={`${id}-help`}>Type a code such as E, 32 or 3232, or start typing a name and choose from the list.</Help>
      <span className="inline-form">
        <input
          id={id}
          type="text"
          list={listId}
          value={text}
          aria-describedby={`${id}-help`}
          data-testid="scope-add-code"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && valid) {
              onAdd(code);
              setText("");
            }
          }}
        />
        <button
          type="button"
          disabled={!valid}
          data-testid="scope-add"
          onClick={() => {
            onAdd(code);
            setText("");
          }}
        >
          Add
        </button>
      </span>
      <datalist id={listId}>
        {[...names.values()].map((c) => (
          <option key={c.code} value={`${c.code} ${c.name}`} />
        ))}
      </datalist>
    </div>
  );
}
