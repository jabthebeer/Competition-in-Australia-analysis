import { useState } from "react";
import { dec } from "../../engine/decimal";
import type { Obligation, OptionResult } from "../../engine/index";
import { NextStep, PageHeading, type PageProps } from "../App";
import { ObligationEditor } from "../components/ObligationEditor";
import { CATEGORY_LABELS, formatMoney, moneyText } from "../format";
import { addCurrentObligation, currentObligations, newObligation, removeCurrentObligation, updateCurrentObligation, type Category } from "../model";

/** Average annual in-scope cost of one side of an obligation (context, not RBE). */
export function sideAnnual(result: OptionResult | undefined, obligationId: string, side: "current" | "reformed"): string {
  if (!result) return "0";
  const items = result.items.filter((i) => i.obligationId === obligationId && i.side === side && !i.excluded);
  const total = items.reduce((a, i) => a.plus(i.netByYear.reduce((x, y) => x.plus(y), dec(0))), dec(0));
  const T = items[0]?.netByYear.length ?? 1;
  return total.dividedBy(T).toFixed();
}

const ADD_BUTTONS: { category: Category; label: string }[] = [
  { category: "administrative", label: "Add an administrative cost (e.g. reporting, record keeping)" },
  { category: "substantive", label: "Add a substantive compliance cost (e.g. equipment, training, advice)" },
  { category: "delay", label: "Add a delay cost (waiting for a government decision)" },
];

export function CurrentRegimePage({ proposal, update, computed, go }: PageProps) {
  const obligations = currentObligations(proposal);
  const [open, setOpen] = useState<Set<string>>(() => new Set(obligations.length === 1 ? [obligations[0]!.id] : []));
  const result = computed.ok ? computed.result.options[0] : undefined;
  const toggle = (id: string) => setOpen((s) => (s.has(id) ? new Set([...s].filter((x) => x !== id)) : new Set([...s, id])));

  const add = (category: Category) => {
    const ob = newObligation(category, proposal.populations, "current");
    update((p) => addCurrentObligation(p, ob));
    setOpen((s) => new Set([...s, ob.id]));
  };

  return (
    <>
      <PageHeading>Step 2: The current regime</PageHeading>
      {proposal.proposalType === "new" ? (
        <p className="summary-box">
          A new regulation has no current regime. You can skip this step and describe the new obligations under <button type="button" className="link" onClick={() => go("options")}>reform options</button>.
        </p>
      ) : (
        <p>
          List the obligations as they are today: what entities must do, how long it takes or what it costs, and how often. Each option in step 3 starts from this list, and you change only what the reform changes.
        </p>
      )}
      {result && obligations.length > 0 && (
        <p className="summary-box" data-testid="current-total">
          Current regime cost (context, not an RBE figure): <strong>{moneyText(result.context.currentAnnual)}</strong> a year ({formatMoney(result.context.currentAnnual, "dollars")}).
        </p>
      )}
      {obligations.map((o: Obligation) => {
        const expanded = open.has(o.id);
        const panelId = `panel-${o.id}`;
        return (
          <section className="card" key={o.id} aria-labelledby={`h-${o.id}`} data-testid={`current-obligation-${o.name || o.id}`}>
            <div className="card-header">
              <div>
                <h3 id={`h-${o.id}`}>{o.name || "Unnamed obligation"}</h3>
                <span className="card-meta">
                  {CATEGORY_LABELS[o.category]} · {formatMoney(sideAnnual(result, o.id, "current"), "dollars")} a year on average
                </span>
              </div>
              <div className="button-row">
                <button type="button" aria-expanded={expanded} aria-controls={panelId} onClick={() => toggle(o.id)}>
                  {expanded ? "Close" : "Edit"}
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={() => {
                    if (window.confirm(`Remove "${o.name || "this obligation"}" from the current regime and every option?`)) update((p) => removeCurrentObligation(p, o.id));
                  }}
                >
                  Remove
                </button>
              </div>
            </div>
            {expanded && (
              <div id={panelId}>
                <ObligationEditor proposal={proposal} obligation={o} mode="current" result={result} onChange={(mutate) => update((p) => updateCurrentObligation(p, o.id, mutate))} />
              </div>
            )}
          </section>
        );
      })}
      <div className="button-row">
        {ADD_BUTTONS.map((b) => (
          <button key={b.category} type="button" onClick={() => add(b.category)}>
            {b.label}
          </button>
        ))}
      </div>
      <NextStep go={go} to="options">
        Next: design the reform options
      </NextStep>
    </>
  );
}
