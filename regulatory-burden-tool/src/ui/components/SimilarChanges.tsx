// Similar past changes from the register (plan §6.9): context, not parameters. Directions are hypotheses and
// evaluation verdicts provisional; an evaluation links to its page on the ALICIA website.
import { useMemo } from "react";
import type { BriefDraft } from "../briefModel";
import type { RegisterRecord } from "../costingData";
import { SITE } from "../env";
import { directionCheck, similarChanges } from "../similar";

const DIRECTION_LABELS: Record<string, string> = {
  enhancing: "expected to enhance competition",
  weakening: "expected to weaken competition",
  mixed: "mixed expected effects",
  unclear: "direction unclear",
};

export function SimilarChanges({ draft, records, limit = 5 }: { draft: BriefDraft; records: readonly RegisterRecord[]; limit?: number }) {
  const similar = useMemo(() => similarChanges(draft, records, limit), [draft, records, limit]);
  const check = directionCheck(draft, similar);
  return (
    <section aria-labelledby="similar-heading" data-testid="similar-changes">
      <h2 id="similar-heading">Similar past changes</h2>
      <p className="help">
        Australian regulatory changes from the ALICIA register that touch the same competition categories, industries or level of government. Their directions are hypotheses, not findings, and evaluation verdicts are provisional. They are context: none is used as a parameter.
      </p>
      {check && (
        <p className="banner draft" data-testid="direction-check">
          {check}
        </p>
      )}
      {similar.length === 0 ? (
        <p>No similar changes yet: they appear once the scope has industries or a lever touches a competition category.</p>
      ) : (
        <ol className="similar-list">
          {similar.map(({ record: r, sharedCategories, sharedIndustries, alsoIn }) => (
            <li key={r.id}>
              <strong>{r.title}</strong> ({r.jurisdiction}
              {r.commencement ? `, from ${r.commencement}` : ""}): {DIRECTION_LABELS[r.direction] ?? r.direction}.
              {r.direction_rationale && <span className="help"> {r.direction_rationale}</span>}
              {alsoIn.length > 0 && <span className="similar-why"> Also made in {alsoIn.join(", ")}.</span>}
              <span className="similar-why">
                {" "}
                Shares {[sharedCategories.length ? `categories: ${sharedCategories.join(", ")}` : "", sharedIndustries.length ? `industries: ${sharedIndustries.join(", ")}` : ""].filter(Boolean).join("; ")}.
              </span>
              {r.evaluation && (
                <span>
                  {" "}
                  Evaluation (provisional): {r.evaluation.finding ?? r.evaluation.verdict}
                  {SITE && r.evaluation.page ? (
                    <>
                      {" "}
                      <a href={r.evaluation.page}>read the evaluation</a>
                    </>
                  ) : null}
                  .
                </span>
              )}
              {r.direction_sources.length > 0 && (
                <span className="similar-sources">
                  {" "}
                  Sources:{" "}
                  {r.direction_sources.map((u, i) => (
                    <span key={u}>
                      {i > 0 ? ", " : ""}
                      <a href={u} rel="noreferrer noopener" target="_blank">
                        {new URL(u).hostname}
                      </a>
                    </span>
                  ))}
                </span>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
