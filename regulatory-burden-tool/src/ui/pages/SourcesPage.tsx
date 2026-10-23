// "Sources and parameters" (plan §6.7): the evidence library, grouped by channel, with each parameter's value and
// range, grade, verification tag, citation, locator and quote. Read-only; the library is bundled at build time,
// so the page makes no network requests (links open the sources only when the user follows them).
import {
  EVIDENCE,
  EVIDENCE_GRADE_LABELS,
  VERIFICATION_TAG_LABELS,
  citationText,
  evidenceByChannel,
  type EvidenceChannel,
  type EvidenceEntry,
} from "../../productivity/evidence";
import { PageHeading } from "../App";

const METHOD_LABELS: Record<EvidenceEntry["method"], string> = {
  causal: "Causal estimate",
  structural: "Structural estimate",
  correlational: "Correlation",
  model: "Model result",
  assumption: "Assumption",
  data: "Measured statistic",
  rule: "Official rule",
};

const RANGE_LABELS: Record<EvidenceEntry["rangeBasis"], string> = {
  source: "from the source",
  plusMinus50: "the tool's ±50% rule: the source gives no range",
  sensitivity: "sensitivity cases, reported side by side",
  fixed: "no range",
};

/** Up to four significant figures, with a true minus sign. */
export function formatEvidenceNumber(n: number): string {
  return Number(n.toPrecision(4)).toString().replace("-", "−");
}

function channelLabel(channel: EvidenceChannel): string {
  return channel === "layerB" ? "Layer B" : channel === "general" ? "General" : channel;
}

function EvidenceCard({ entry: e }: { entry: EvidenceEntry }) {
  const headingId = `evidence-${e.id.replace(/\./g, "-")}`;
  const n = formatEvidenceNumber;
  return (
    <article className="card evidence-card" aria-labelledby={headingId} data-testid="evidence-entry" data-evidence-id={e.id}>
      <div className="card-header">
        <h3 id={headingId}>{e.label}</h3>
        <p className="evidence-badges">
          <span className={`badge ${e.isDefault ? "evidence-default" : "evidence-alternative"}`}>{e.isDefault ? "Default" : "Alternative"}</span>
          <span className="badge evidence-grade">Grade {e.grade}</span>
          <span className="badge evidence-tag">[{e.tag}]</span>
          {e.review.status === "draft" ? <span className="badge evidence-draft">Not yet checked</span> : <span className="badge evidence-checked">Checked</span>}
        </p>
      </div>
      <dl className="evidence-facts">
        <div>
          <dt>Value</dt>
          <dd>
            <strong>{n(e.value)}</strong> {e.units}
          </dd>
        </div>
        <div>
          <dt>Range</dt>
          <dd>{e.rangeBasis === "fixed" ? RANGE_LABELS.fixed : `${n(e.low)} to ${n(e.high)} (${RANGE_LABELS[e.rangeBasis]})`}</dd>
        </div>
        <div>
          <dt>Used in</dt>
          <dd>
            {[e.formula, ...(e.alsoUsedBy ?? [])].map((f, i) => (
              <span key={f}>
                {i > 0 && ", "}
                <code>{f}</code>
              </span>
            ))}{" "}
            · parameter <code>{e.parameter}</code>
          </dd>
        </div>
        <div>
          <dt>Evidence</dt>
          <dd>
            Grade {e.grade}: {EVIDENCE_GRADE_LABELS[e.grade]}. [{e.tag}] {VERIFICATION_TAG_LABELS[e.tag]}. {METHOD_LABELS[e.method]}; {e.country}.
          </dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>
            <a href={e.citation.url} rel="noreferrer">
              {citationText(e.citation)}
            </a>
            {e.citation.locator && <> {e.citation.locator}.</>}
          </dd>
        </div>
      </dl>
      {e.quote && (
        <figure className="evidence-quote">
          <blockquote cite={e.citation.url}>
            <p>{e.quote}</p>
          </blockquote>
          <figcaption>Exact text from the source{e.citation.locator ? ` (${e.citation.locator})` : ""}.</figcaption>
        </figure>
      )}
      <details className="more">
        <summary>How the value is derived{e.notes ? ", and notes" : ""}</summary>
        <p>{e.derivation}</p>
        {e.notes && <p>{e.notes}</p>}
      </details>
    </article>
  );
}

export function SourcesPage() {
  const groups = evidenceByChannel();
  const defaults = EVIDENCE.filter((e) => e.isDefault).length;
  const checked = EVIDENCE.filter((e) => e.review.status === "checked").length;
  return (
    <>
      <PageHeading>Sources and parameters</PageHeading>
      <p>
        Every number the productivity and competition costing uses comes from this library: its value and range, the source with a page or table, an exact quote, and how strong the evidence is. Where a value is the tool's own assumption, it says so.
      </p>
      <p className="context-note" data-testid="evidence-summary">
        {EVIDENCE.length} entries, {defaults} of them defaults; {checked} checked against their source.
      </p>
      {checked < EVIDENCE.length && (
        <div className="banner draft evidence-banner" role="note">
          <strong>Draft library.</strong> Entries marked "Not yet checked" were read against their sources when the library was compiled, but have not yet had an independent review. Treat their values as provisional.
        </div>
      )}
      <section aria-labelledby="evidence-key-heading">
        <h2 id="evidence-key-heading">How to read an entry</h2>
        <dl className="evidence-key">
          {Object.entries(EVIDENCE_GRADE_LABELS).map(([grade, label]) => (
            <div key={grade}>
              <dt>Grade {grade}</dt>
              <dd>{label}</dd>
            </div>
          ))}
          {Object.entries(VERIFICATION_TAG_LABELS).map(([tag, label]) => (
            <div key={tag}>
              <dt>[{tag}]</dt>
              <dd>{label}</dd>
            </div>
          ))}
          <div>
            <dt>Default</dt>
            <dd>The value the costing uses unless you change it. Alternatives are shown for comparison and sensitivity.</dd>
          </div>
        </dl>
      </section>
      {groups.map((g) => (
        <section key={g.channel} aria-labelledby={`evidence-group-${g.channel}`} className="evidence-group">
          <h2 id={`evidence-group-${g.channel}`}>
            {channelLabel(g.channel)}: {g.name}
          </h2>
          <ul className="evidence-list">
            {g.entries.map((e) => (
              <li key={e.id}>
                <EvidenceCard entry={e} />
              </li>
            ))}
          </ul>
        </section>
      ))}
    </>
  );
}
