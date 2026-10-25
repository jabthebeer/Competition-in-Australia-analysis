// A channel's Layer A arithmetic (plan §3.1 step 4): its effects by industry with the chain of factors behind
// each, other effects reported beside GDP, what it could not cost and why, and the evidence it rests on with
// grades. No GDP figure here: GDP comes with its range on the Results page (plan §3.2, principle 2).
import { EVIDENCE, EVIDENCE_GRADE_LABELS, type ChannelOutcome, type Factor } from "../../productivity/index";

const ENTRY = new Map(EVIDENCE.map((e) => [e.id, e]));

/** A value for display: up to four significant figures, with thousands separators for large numbers. */
export function figure(x: number): string {
  if (!Number.isFinite(x)) return "—";
  if (Math.abs(x) >= 1000) return x.toLocaleString("en-AU", { maximumFractionDigits: 0 });
  return Number(x.toPrecision(4)).toLocaleString("en-AU", { maximumFractionDigits: 6 });
}

function Chain({ chain }: { chain: Factor[] }) {
  return (
    <ol className="chain">
      {chain.map((f, i) => (
        <li key={i}>
          {f.label}: <strong>{figure(f.value)}</strong> {f.unit}
          {f.evidence && (
            <>
              {" "}
              <a href="#sources" className="evidence-ref">
                [{f.evidence}]
              </a>
            </>
          )}
        </li>
      ))}
    </ol>
  );
}

export function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span className="badge">No evidence grade</span>;
  return (
    <span className={`badge grade grade-${grade.toLowerCase()}`} title={EVIDENCE_GRADE_LABELS[grade as keyof typeof EVIDENCE_GRADE_LABELS]}>
      Evidence grade {grade}
    </span>
  );
}

export function ChannelDetail({ outcome: o, testId }: { outcome: ChannelOutcome; testId?: string }) {
  return (
    <div className="channel-detail" data-testid={testId ?? `channel-${o.channel}`}>
      <p className="channel-heading">
        <strong>
          {o.channel} {o.name}
        </strong>{" "}
        <span className={`badge ${o.status === "costed" ? "costed" : "not-costed"}`}>{o.status === "costed" ? "Costed" : "Not quantified"}</span> <GradeBadge grade={o.grade} />
      </p>
      {o.effects.length > 0 && (
        <div className="table-wrap">
          <table className="effects">
            <caption className="visually-hidden">Direct effects of {o.name} by industry</caption>
            <thead>
              <tr>
                <th scope="col">Industry</th>
                <th scope="col">Effect</th>
                <th scope="col" className="num">Size</th>
              </tr>
            </thead>
            <tbody>
              {o.effects.map((e, i) => (
                <tr key={i}>
                  <th scope="row">{e.anzsic === "TOT" ? "Whole economy" : e.anzsic}</th>
                  <td>
                    {e.measure}
                    <details>
                      <summary>How it is calculated</summary>
                      <Chain chain={e.chain} />
                    </details>
                  </td>
                  <td className="num">
                    {e.value >= 0 ? "+" : "−"}
                    {figure(Math.abs(e.value))} {e.unit === "% change" ? "%" : e.unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {o.other.length > 0 && (
        <ul className="other-effects">
          {o.other.map((x, i) => (
            <li key={i}>
              {x.label}: <strong>{figure(x.value)}</strong> {x.unit}
              {x.chain.length > 0 && (
                <details>
                  <summary>How it is calculated</summary>
                  <Chain chain={x.chain} />
                </details>
              )}
            </li>
          ))}
        </ul>
      )}
      {o.reasons.length > 0 && (
        <ul className="not-costed-list">
          {o.reasons.map((r, i) => (
            <li key={i}>
              <strong>Not costed:</strong> {r}
            </li>
          ))}
        </ul>
      )}
      {o.notes.map((n, i) => (
        <p key={i} className="help">
          {n}
        </p>
      ))}
      {o.evidence.length > 0 && (
        <details className="evidence-used">
          <summary>Evidence used ({o.evidence.length})</summary>
          <ul>
            {o.evidence.map((id) => {
              const e = ENTRY.get(id);
              return (
                <li key={id}>
                  <a href="#sources">{id}</a>: {e?.label}. {e ? `${e.citation.authors} (${e.citation.year}), grade ${e.grade}, [${e.tag}]` : ""}
                  {o.assumptions.includes(id) && " · the tool's own assumption: it sets the range, not the grade"}
                </li>
              );
            })}
          </ul>
        </details>
      )}
    </div>
  );
}
