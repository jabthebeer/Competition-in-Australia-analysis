import { useEffect, useState } from "react";
import { ENGINE_VERSION, PARAMETERS } from "../../engine/index";
import { PageHeading } from "../App";
import { loadCostingParameters, type CostingLoad } from "../costingData";
import { HOSTED } from "../env";

/** The publishers' releases bundled into this build for the productivity and competition costing. */
function DataInThisBuild() {
  const [load, setLoad] = useState<CostingLoad | null>(null);
  useEffect(() => {
    let live = true;
    loadCostingParameters()
      .then((l) => live && setLoad(l))
      .catch((e: unknown) => live && setLoad({ ok: false, problem: String(e) }));
    return () => {
      live = false;
    };
  }, []);
  if (!load) return <p>Loading the data list…</p>;
  if (!load.ok) return <p>The bundled data file could not be read ({load.problem}).</p>;
  const { sources, vintage } = load.parameters;
  if (sources.length === 0) return <p>No published data is bundled in this build yet.</p>;
  return (
    <div className="table-wrap">
      <table data-testid="data-vintages">
        <caption>
          Published data in this build{vintage ? ` (latest release ${vintage})` : ""}. On the ALICIA website these are checked against the publishers every day and refreshed when a new release appears.
        </caption>
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">Publisher</th>
            <th scope="col">Release</th>
            <th scope="col">Released</th>
            <th scope="col">Next release</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.id}>
              <th scope="row">
                <a href={s.url} rel="noreferrer">
                  {s.title}
                </a>
              </th>
              <td>{s.publisher}</td>
              <td>{s.release}</td>
              <td>{s.release_date ?? "–"}</td>
              <td>{s.next_release ?? "–"}</td>
              <td>{s.status === "fallback" ? "Previous release kept (the latest check failed)" : "Current"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AboutPage() {
  const r = PARAMETERS.rates;
  return (
    <>
      <PageHeading>About this tool</PageHeading>
      <section className="disclaimer" aria-labelledby="disclaimer-heading">
        <h2 id="disclaimer-heading">Disclaimer</h2>
        <p>
          This is an <strong>unofficial</strong> aid. It is not an Australian Government tool and isn't endorsed by the Department of the Prime Minister and Cabinet or the Office of Impact Analysis (OIA). You remain responsible for your estimates. For formal advice, contact OIA at helpdesk-OIA@pmc.gov.au or 02 6271 6270 (as listed in the framework, p. 10).
        </p>
      </section>
      <section aria-labelledby="framework-heading">
        <h2 id="framework-heading">The framework</h2>
        <p>
          The tool applies the <cite>Regulatory Burden Measurement Framework</cite> ({PARAMETERS.framework.release}). It estimates the <strong>average annual change in regulatory costs</strong> for businesses, community organisations and individuals, measured against business as usual, and presents it in the framework's Regulatory Burden Estimate (RBE) table.
        </p>
        <ul>
          <li>
            <strong>What counts:</strong> administrative costs (demonstrating compliance), substantive compliance costs (delivering the outcome) and delay costs (waiting on government before operating). Subsidies are subtracted.
          </li>
          <li>
            <strong>What doesn't:</strong> business-as-usual costs, fees, levies and taxes (the time to pay them counts), fines and enforcement, indirect and competition effects, court administration, international-market obligations, government-to-government policy (with exceptions), and benefits.
          </li>
          <li>
            <strong>Timing:</strong> 10 years by default, in real terms, with no inflation and no discounting. One-off costs are spread over the period.
          </li>
          <li>
            <strong>Labour rates:</strong> ${r.work.hourly}/hour work-related (${r.work.base} × {r.work.multiplier}); ${r.leisure.hourly}/hour for individuals' own time (Australian residents); ${r.volunteer.hourly}/hour for volunteers. Next update: {r.work.nextUpdate}.
          </li>
          <li>
            <strong>Reforms</strong> are costed obligation by obligation: the reformed version's cost, minus the current version's, plus one-off transition costs. Sunk costs are never savings, and only activity businesses wouldn't do anyway counts.
          </li>
        </ul>
        <p>
          Forgone benefits of a lighter regulation (such as safety or consumer protection) are outside the framework. Discuss them in the Impact Analysis.
        </p>
      </section>
      <section aria-labelledby="costing-heading">
        <h2 id="costing-heading">Productivity and competition costing</h2>
        <p>
          A second part, in development, turns a policy brief into estimated effects on productivity and competition, by channel and industry, with ranges, sources and an evidence grade. It sits outside the framework: the RBM excludes "changes to market structure and competition impacts" (p. 4), so it never changes the regulatory burden estimate.
        </p>
        <DataInThisBuild />
      </section>
      <section aria-labelledby="privacy-heading">
        <h2 id="privacy-heading">Your data</h2>
        <p>
          The tool runs entirely in your browser. It has no server, no analytics and makes no network requests{HOSTED ? ". This test copy is hosted in a viewer, so use illustrative or public information only" : ": its security policy blocks them"}. Your proposal is stored only in this browser (if auto-save is on) and in files or text you choose to keep. Proposals may be Cabinet-in-confidence: follow your agency's rules about where such material may be handled.
        </p>
      </section>
      <section aria-labelledby="version-heading">
        <h2 id="version-heading">Version</h2>
        <p>
          Engine {ENGINE_VERSION} · Parameters {PARAMETERS.vintage}
        </p>
      </section>
    </>
  );
}
