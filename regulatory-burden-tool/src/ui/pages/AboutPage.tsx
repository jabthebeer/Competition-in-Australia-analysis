import { ENGINE_VERSION, PARAMETERS } from "../../engine/index";
import { PageHeading } from "../App";
import { HOSTED } from "../env";

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
