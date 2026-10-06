import { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ProposalValidationError, computeProposal, type Proposal, type ProposalResult } from "../engine/index";
import { describeIssue, newProposal } from "./model";
import { AboutPage } from "./pages/AboutPage";
import { CurrentRegimePage } from "./pages/CurrentRegimePage";
import { DataPage } from "./pages/DataPage";
import { OptionsPage } from "./pages/OptionsPage";
import { ProposalPage } from "./pages/ProposalPage";
import { loadSavedProposal, loadSettings, saveProposal, saveSettings, type Settings } from "./persistence";

// The results page carries the charting library, so it loads only when first opened.
const ResultsPage = lazy(() => import("./pages/ResultsPage").then((m) => ({ default: m.ResultsPage })));

export type Computed = { ok: true; result: ProposalResult } | { ok: false; issues: string[] };
export type Update = (fn: (p: Proposal) => Proposal) => void;

export interface PageProps {
  proposal: Proposal;
  update: Update;
  computed: Computed;
  go: (route: Route) => void;
}

const STEPS = [
  { path: "proposal", label: "Proposal" },
  { path: "current", label: "Current regime" },
  { path: "options", label: "Reform options" },
  { path: "results", label: "Results" },
] as const;
const OTHER = [
  { path: "data", label: "Save and load" },
  { path: "about", label: "About" },
] as const;
export type Route = (typeof STEPS)[number]["path"] | (typeof OTHER)[number]["path"];
const ROUTES = new Set<string>([...STEPS, ...OTHER].map((r) => r.path));

function readRoute(): Route {
  const r = window.location.hash.replace(/^#\/?/, "");
  return (ROUTES.has(r) ? r : "proposal") as Route;
}

export function App() {
  const [route, setRoute] = useState<Route>(readRoute);
  const [settings, setSettingsState] = useState<Settings>(loadSettings);
  const [proposal, setProposal] = useState<Proposal>(() => loadSavedProposal() ?? newProposal("reform"));
  const [saved, setSaved] = useState<"saved" | "off" | "failed">(settings.autosave ? "saved" : "off");
  const mainRef = useRef<HTMLElement>(null);
  const firstRender = useRef(true);

  useEffect(() => {
    const onHash = () => setRoute(readRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Move focus to the page heading on navigation, so screen-reader users hear the new page.
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    mainRef.current?.querySelector<HTMLElement>("h1")?.focus();
  }, [route]);

  const update: Update = useCallback((fn) => setProposal((prev) => fn(prev)), []);
  const go = useCallback((r: Route) => {
    window.location.hash = `/${r}`;
  }, []);

  const computed = useMemo<Computed>(() => {
    try {
      return { ok: true, result: computeProposal(proposal) };
    } catch (e) {
      return { ok: false, issues: e instanceof ProposalValidationError ? e.issues : [String(e)] };
    }
  }, [proposal]);

  useEffect(() => {
    if (!settings.autosave) {
      setSaved("off");
      return;
    }
    const t = window.setTimeout(() => setSaved(saveProposal(proposal) ? "saved" : "failed"), 250);
    return () => window.clearTimeout(t);
  }, [proposal, settings.autosave]);

  const setSettings = (s: Settings) => {
    setSettingsState(s);
    saveSettings(s);
  };

  const pageProps: PageProps = { proposal, update, computed, go };
  const estimates = computed.ok ? computed.result.unconfirmedEstimates.length : 0;

  return (
    <>
      <a
        className="skip-link"
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          mainRef.current?.focus();
        }}
      >
        Skip to main content
      </a>
      <header className="site-header">
        <div className="brand">
          <span className="site-title">Regulatory Burden Calculator</span>
          <span className="tag">Unofficial aid</span>
        </div>
        <nav aria-label="Main">
          <ol className="steps">
            {STEPS.map((s, i) => (
              <li key={s.path}>
                <a href={`#/${s.path}`} aria-current={route === s.path ? "page" : undefined}>
                  <span className="step-number">{i + 1}</span> {s.label}
                </a>
              </li>
            ))}
          </ol>
          <ul className="secondary-nav">
            {OTHER.map((s) => (
              <li key={s.path}>
                <a href={`#/${s.path}`} aria-current={route === s.path ? "page" : undefined}>
                  {s.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <div className="status-bar">
        <span className="proposal-title">{proposal.title || "Untitled proposal"}</span>
        <span className="save-status" data-testid="save-status">
          {saved === "saved" ? "Saved in this browser only" : saved === "off" ? "Auto-save is off: download a file to keep your work" : "Couldn't save in this browser: download a file to keep your work"}
        </span>
      </div>
      {!computed.ok && (
        <div className="banner error" role="alert" data-testid="validation-banner">
          <strong>Some inputs need fixing before results can be calculated:</strong>
          <ul>
            {computed.issues.slice(0, 8).map((i) => (
              <li key={i}>{describeIssue(proposal, i)}</li>
            ))}
          </ul>
        </div>
      )}
      {estimates > 0 && (
        <div className="banner draft" data-testid="draft-banner">
          <strong>Draft:</strong> {estimates} input{estimates > 1 ? "s are" : " is"} unconfirmed model estimate{estimates > 1 ? "s" : ""}. Replace or confirm {estimates > 1 ? "them" : "it"} with a source before relying on the results.
        </div>
      )}
      <main id="main" ref={mainRef} tabIndex={-1}>
        {route === "proposal" && <ProposalPage {...pageProps} />}
        {route === "current" && <CurrentRegimePage {...pageProps} />}
        {route === "options" && <OptionsPage {...pageProps} />}
        {route === "results" && (
          <Suspense fallback={<p>Loading results…</p>}>
            <ResultsPage {...pageProps} />
          </Suspense>
        )}
        {route === "data" && <DataPage {...pageProps} settings={settings} setSettings={setSettings} replace={setProposal} />}
        {route === "about" && <AboutPage />}
      </main>
      <footer className="site-footer">
        <p>
          This is an unofficial aid, not an Australian Government tool. You remain responsible for your estimates; contact the Office of Impact Analysis for formal advice. Everything you enter stays in this browser unless you download it.
        </p>
      </footer>
    </>
  );
}

/** Page heading that receives focus on navigation. */
export function PageHeading({ children }: { children: React.ReactNode }) {
  return <h1 tabIndex={-1}>{children}</h1>;
}

/** Link-style button to another step. */
export function NextStep({ go, to, children }: { go: (r: Route) => void; to: Route; children: React.ReactNode }) {
  return (
    <p className="next-step">
      <button type="button" className="primary" onClick={() => go(to)}>
        {children}
      </button>
    </p>
  );
}
