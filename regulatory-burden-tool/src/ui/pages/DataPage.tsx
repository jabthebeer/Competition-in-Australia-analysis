import { useId, useRef, useState } from "react";
import { importDraft, toProposalFile, type Proposal } from "../../engine/index";
import { PageHeading, type PageProps } from "../App";
import { ConfirmButton } from "../components/ConfirmButton";
import { Checkbox, Help, SelectField } from "../components/fields";
import { HOSTED } from "../env";
import { exampleProposal } from "../example";
import { newProposal, type ProposalType } from "../model";
import { clearAllData, downloadProposal, fileNameFor, type Settings } from "../persistence";

export function DataPage(props: PageProps & { settings: Settings; setSettings: (s: Settings) => void; replace: (p: Proposal) => void }) {
  const { proposal, settings, setSettings, replace, go } = props;
  const [issues, setIssues] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [paste, setPaste] = useState("");
  const [copyText, setCopyText] = useState<string | null>(null);
  const [newType, setNewType] = useState<ProposalType>("reform");
  const copyRef = useRef<HTMLTextAreaElement>(null);
  const pasteId = useId();
  const fileId = useId();
  const copyId = useId();

  const load = (text: string, what: string) => {
    const r = importDraft(text);
    if (r.ok) {
      replace(r.file.proposal);
      setIssues([]);
      setMessage(`Loaded ${what}: "${r.file.proposal.title || "Untitled proposal"}".`);
    } else {
      setIssues(r.issues);
      setMessage("");
    }
  };

  const copyAsText = async () => {
    const text = JSON.stringify(toProposalFile(proposal), null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setCopyText(null);
      setMessage("Copied. Paste it into a document or email to keep it, and paste it back here to load it again.");
    } catch {
      // Clipboard refused (some browsers and embedded viewers): show the text, selected, to copy by hand.
      setCopyText(text);
      setMessage("");
      setTimeout(() => copyRef.current?.select(), 0);
    }
  };

  return (
    <>
      <PageHeading>Save and load</PageHeading>
      <p>Nothing you enter is sent anywhere. Your proposal stays in this browser, and in any file or text you choose to keep.</p>
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
        <ConfirmButton
          label="Delete everything stored in this browser"
          question="Delete everything this tool has stored in this browser, and start a new proposal?"
          confirmLabel="Yes, delete it"
          className="danger"
          onConfirm={() => {
            clearAllData();
            setSettings({ autosave: settings.autosave });
            replace(newProposal("reform"));
            setMessage("Everything stored in this browser has been deleted.");
          }}
        />
      </section>

      <section>
        <h2>Keep a copy</h2>
        <p className="button-row">
          {!HOSTED && (
            <button type="button" className="primary" onClick={() => downloadProposal(proposal)} data-testid="download">
              Download this proposal ({fileNameFor(proposal)})
            </button>
          )}
          <button type="button" className={HOSTED ? "primary" : undefined} onClick={copyAsText} data-testid="copy-text">
            Copy this proposal as text
          </button>
        </p>
        <Help>
          {HOSTED
            ? "This hosted copy can't download files. Copy the proposal as text and keep it in a document; paste it back below to load it again."
            : "If downloading isn't allowed where you're using the tool, copy the proposal as text instead and keep it in a document."}
        </Help>
        {copyText !== null && (
          <div className="field">
            <label htmlFor={copyId}>Proposal as text: select all and copy</label>
            <textarea id={copyId} ref={copyRef} rows={8} readOnly value={copyText} />
          </div>
        )}
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
            Paste a proposal you copied as text, or a draft produced by an AI tool your agency has approved. It is checked against the framework's rules before it loads. Values the AI estimated stay marked as unconfirmed until you replace or source them.
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
        <div className="button-row">
          <ConfirmButton
            label="Start a new proposal"
            question="Start a new proposal? Keep a copy of this one first if you want it."
            confirmLabel="Yes, start a new one"
            testId="start-new"
            onConfirm={() => {
              replace(newProposal(newType));
              go("proposal");
            }}
          />
          <ConfirmButton
            label="Load the illustrative example (synthetic data)"
            question="Replace the current proposal with the illustrative example? Keep a copy of this one first if you want it."
            confirmLabel="Yes, load the example"
            testId="load-example"
            onConfirm={() => {
              replace(exampleProposal());
              setIssues([]);
              setMessage("Loaded the illustrative example.");
            }}
          />
        </div>
      </section>
    </>
  );
}
