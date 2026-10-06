import { useId, useState } from "react";
import { importDraft, type Proposal } from "../../engine/index";
import example from "../../../examples/illustrative-reform.json";
import { PageHeading, type PageProps } from "../App";
import { Checkbox, Help, SelectField } from "../components/fields";
import { newProposal, type ProposalType } from "../model";
import { clearAllData, downloadProposal, fileNameFor, type Settings } from "../persistence";

export function DataPage(props: PageProps & { settings: Settings; setSettings: (s: Settings) => void; replace: (p: Proposal) => void }) {
  const { proposal, settings, setSettings, replace, go } = props;
  const [issues, setIssues] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [paste, setPaste] = useState("");
  const [newType, setNewType] = useState<ProposalType>("reform");
  const pasteId = useId();
  const fileId = useId();

  const load = (text: string, what: string) => {
    const r = importDraft(text);
    if (r.ok) {
      replace(r.file.proposal);
      setIssues([]);
      setMessage(`Loaded ${what}: "${r.file.proposal.title}".`);
    } else {
      setIssues(r.issues);
      setMessage("");
    }
  };

  return (
    <>
      <PageHeading>Save and load</PageHeading>
      <p>Nothing you enter is sent anywhere. Your proposal stays in this browser, and in any file you choose to download.</p>
      <div aria-live="polite" className="live">
        {message && <p className="success">{message}</p>}
      </div>
      {issues.length > 0 && (
        <div className="banner error" role="alert" data-testid="import-issues">
          <strong>That couldn't be loaded:</strong>
          <ul>
            {issues.slice(0, 12).map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </div>
      )}

      <section>
        <h2>In this browser</h2>
        <Checkbox
          label="Save my work automatically in this browser"
          help="Saved only on this device, in this browser's local storage. Turn this off on a shared computer."
          checked={settings.autosave}
          onChange={(autosave) => setSettings({ ...settings, autosave })}
          testId="autosave"
        />
        <button
          type="button"
          className="danger"
          onClick={() => {
            if (window.confirm("Delete everything this tool has stored in this browser, and start a new proposal?")) {
              clearAllData();
              setSettings({ autosave: settings.autosave });
              replace(newProposal("reform"));
              setMessage("Everything stored in this browser has been deleted.");
            }
          }}
        >
          Delete everything stored in this browser
        </button>
      </section>

      <section>
        <h2>Files</h2>
        <p>
          <button type="button" className="primary" onClick={() => downloadProposal(proposal)} data-testid="download">
            Download this proposal ({fileNameFor(proposal)})
          </button>
        </p>
        <div className="field">
          <label htmlFor={fileId}>Open a saved proposal file</label>
          <input
            id={fileId}
            type="file"
            accept=".json,application/json"
            data-testid="open-file"
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (f) load(await f.text(), "file");
              e.target.value = "";
            }}
          />
        </div>
      </section>

      <section>
        <h2>Paste a proposal or a draft</h2>
        <div className="field">
          <label htmlFor={pasteId}>Proposal text</label>
          <Help id={`${pasteId}-help`}>
            Paste a saved proposal, or a draft produced by an AI tool your agency has approved. It is checked against the framework's rules before it loads. Values the AI estimated stay marked as unconfirmed until you replace or source them.
          </Help>
          <textarea id={pasteId} aria-describedby={`${pasteId}-help`} rows={8} value={paste} onChange={(e) => setPaste(e.target.value)} data-testid="paste" />
        </div>
        <button type="button" onClick={() => load(paste, "pasted proposal")} disabled={!paste.trim()} data-testid="load-paste">
          Check and load
        </button>
      </section>

      <section>
        <h2>Start again</h2>
        <SelectField
          label="Type of proposal"
          value={newType}
          options={[
            { value: "reform", label: "Reform an existing regulation" },
            { value: "new", label: "New regulation" },
            { value: "repeal", label: "Remove a regulation outright" },
          ]}
          onChange={setNewType}
        />
        <p className="button-row">
          <button
            type="button"
            onClick={() => {
              if (window.confirm("Start a new proposal? Download this one first if you want to keep it.")) {
                replace(newProposal(newType));
                go("proposal");
              }
            }}
          >
            Start a new proposal
          </button>
          <button
            type="button"
            onClick={() => {
              if (window.confirm("Replace the current proposal with the illustrative example? Download this one first if you want to keep it.")) {
                load(JSON.stringify(example), "the illustrative example");
              }
            }}
            data-testid="load-example"
          >
            Load the illustrative example (synthetic data)
          </button>
        </p>
      </section>
    </>
  );
}
