// Saving in this browser only (localStorage) and to files the user explicitly exports.
// Nothing is ever sent anywhere. Every storage access is guarded: storage can be
// unavailable (private windows, blocked site data) and the app must still work.
import { importDraft, toProposalFile, type Proposal } from "../engine/index";

const PROPOSAL_KEY = "regulatory-burden-tool:v1:proposal";
const SETTINGS_KEY = "regulatory-burden-tool:v1:settings";

export interface Settings {
  autosave: boolean;
}

const DEFAULT_SETTINGS: Settings = { autosave: true };

export function loadSettings(): Settings {
  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY);
    return raw ? { ...DEFAULT_SETTINGS, ...(JSON.parse(raw) as Partial<Settings>) } : DEFAULT_SETTINGS;
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: Settings): void {
  try {
    window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    /* storage unavailable: settings last for this visit only */
  }
}

/** The proposal saved in this browser, if there is a valid one. */
export function loadSavedProposal(): Proposal | null {
  try {
    const raw = window.localStorage.getItem(PROPOSAL_KEY);
    if (!raw) return null;
    const r = importDraft(raw);
    return r.ok ? r.file.proposal : null;
  } catch {
    return null;
  }
}

export function saveProposal(p: Proposal): boolean {
  try {
    window.localStorage.setItem(PROPOSAL_KEY, JSON.stringify(toProposalFile(p)));
    return true;
  } catch {
    return false;
  }
}

/** Removes everything this tool has stored in this browser. */
export function clearAllData(): void {
  try {
    window.localStorage.removeItem(PROPOSAL_KEY);
    window.localStorage.removeItem(SETTINGS_KEY);
  } catch {
    /* nothing stored */
  }
}

export function fileNameFor(p: Proposal): string {
  const slug = p.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "proposal";
  return `${slug}.rbm.json`;
}

/** Downloads the proposal as a versioned JSON file, entirely in the browser. */
export function downloadProposal(p: Proposal): void {
  const blob = new Blob([JSON.stringify(toProposalFile(p, new Date().toISOString()), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileNameFor(p);
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
