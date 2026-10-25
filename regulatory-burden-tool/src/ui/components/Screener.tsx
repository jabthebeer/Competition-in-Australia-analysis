// The scope screener (burden tool Phase 3; RBM pp. 2–4, 10, 14–15): plain-language questions that say whether a
// cost belongs in the Regulatory Burden Estimate, with the framework page for each answer. A helper: the answers
// are not saved, and nothing is changed until the user acts on them.
import { useState } from "react";
import { SCREENER, screen } from "../../engine/index";
import { RadioGroup } from "./fields";

type Answer = "yes" | "no" | "unsure";

const SCOPE_LABELS = { in: "Cost it", out: "Leave it out", partly: "Cost part of it" } as const;

export function Screener() {
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const outcomes = screen(Object.fromEntries(Object.entries(answers).filter(([, a]) => a !== "unsure").map(([id, a]) => [id, a === "yes"])));
  return (
    <details className="card screener" data-testid="screener">
      <summary>Is a cost in scope? Check it with the screener</summary>
      <p className="help">Answer for one cost at a time. Each answer says whether the cost belongs in the RBE, and where the framework says so. Your answers are not saved.</p>
      {SCREENER.map((q) => (
        <RadioGroup
          key={q.id}
          label={q.question}
          value={answers[q.id] ?? "unsure"}
          inline
          options={[
            { value: "yes", label: "Yes" },
            { value: "no", label: "No" },
            { value: "unsure", label: "Not sure" },
          ]}
          onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
          testId={`screener-${q.id}`}
        />
      ))}
      <div aria-live="polite">
        {outcomes.length > 0 && (
          <ul className="screener-outcomes" data-testid="screener-outcomes">
            {outcomes.map((o) => (
              <li key={o.questionId} className={`scope-${o.scope}`}>
                <strong>{SCOPE_LABELS[o.scope]}.</strong> {o.explanation} ({o.ref})
              </li>
            ))}
          </ul>
        )}
        {outcomes.length > 0 && <button type="button" className="link" onClick={() => setAnswers({})}>Clear the answers</button>}
      </div>
    </details>
  );
}
