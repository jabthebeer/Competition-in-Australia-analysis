// The productivity and competition channels (plan §6.2), the shock types Layer A produces,
// which brief inputs feed which channel, and the overlap rules (plan §6.5).
// Formulas and parameters arrive in P4; this file fixes the vocabulary they share.

export const CHANNEL_IDS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"] as const;
export type ChannelId = (typeof CHANNEL_IDS)[number];

/** Where a channel's inputs come from in the brief: the RBM proposal, or a lever block. */
export type InputBlock = "burden" | "entry" | "thresholds" | "capital" | "conduct.markup" | "conduct.pmr" | "labour" | "innovation" | "trade" | "fiscal" | "custom";

export interface Channel {
  id: ChannelId;
  name: string;
  /** Brief blocks that feed it. Every channel can also take a custom shock. */
  inputs: readonly InputBlock[];
  /** Shock types its Layer A produces. */
  shocks: readonly ShockType[];
  /** Plan section with the method. */
  ref: string;
}

export const SHOCK_TYPES = {
  mfp: { label: "Value-added multifactor productivity (Hicks-neutral)", unit: "% change" },
  labourProductivity: { label: "Labour-augmenting productivity", unit: "% change" },
  userCost: { label: "User cost of capital", unit: "% change" },
  entryRate: { label: "Business entry rate", unit: "percentage points" },
  markup: { label: "Price–cost mark-up", unit: "% change" },
  price: { label: "Output price (reported, not a GDP gain)", unit: "% change" },
  rent: { label: "Economic rent removed (a transfer, not a GDP gain)", unit: "$ a year" },
} as const;
export type ShockType = keyof typeof SHOCK_TYPES;
export const SHOCK_TYPE_IDS = Object.keys(SHOCK_TYPES) as [ShockType, ...ShockType[]];

export const CHANNELS: Readonly<Record<ChannelId, Channel>> = {
  C1: { id: "C1", name: "Resource cost of compliance", inputs: ["burden"], shocks: ["mfp"], ref: "§6.2 C1" },
  C2: { id: "C2", name: "Delay and approval time", inputs: ["burden", "entry", "capital"], shocks: ["userCost"], ref: "§6.2 C2" },
  C3: { id: "C3", name: "Capital deepening (user cost of capital)", inputs: ["capital"], shocks: ["userCost"], ref: "§6.2 C3" },
  C4: { id: "C4", name: "Entry and exit barriers", inputs: ["entry"], shocks: ["entryRate", "mfp"], ref: "§6.2 C4" },
  C5: { id: "C5", name: "Size thresholds", inputs: ["thresholds"], shocks: ["mfp"], ref: "§6.2 C5" },
  C6: { id: "C6", name: "Competition intensity and mark-ups", inputs: ["conduct.markup"], shocks: ["markup", "mfp"], ref: "§6.2 C6" },
  C7: { id: "C7", name: "Product market regulation indicator", inputs: ["conduct.pmr"], shocks: ["mfp", "userCost"], ref: "§6.2 C7" },
  C8: { id: "C8", name: "Labour mobility (licensing, non-competes)", inputs: ["labour"], shocks: ["labourProductivity"], ref: "§6.2 C8" },
  C9: { id: "C9", name: "Innovation and R&D", inputs: ["innovation"], shocks: ["mfp"], ref: "§6.2 C9" },
  C10: { id: "C10", name: "Trade and foreign investment", inputs: ["trade"], shocks: ["mfp", "userCost"], ref: "§6.2 C10" },
  C11: { id: "C11", name: "Efficiency cost of funding", inputs: ["fiscal"], shocks: [], ref: "§6.2 C11" },
  C12: { id: "C12", name: "Other (user-entered shocks only in v1)", inputs: ["custom"], shocks: ["mfp", "labourProductivity", "userCost", "price", "rent"], ref: "§6.2 C12" },
};

/** Channels fed by each lever block (the reverse of `Channel.inputs`, custom shocks aside). */
export function channelsFor(block: InputBlock): ChannelId[] {
  return CHANNEL_IDS.filter((id) => CHANNELS[id].inputs.includes(block) && block !== "custom");
}

/** Overlap rules (plan §6.5). The engine applies them in P4; the brief schema enforces the ones it can see. */
export const OVERLAP_RULES = [
  { id: "O-1", channels: ["C1", "C4"], rule: "C1 counts the resource cost to incumbents; C4 only the change in entry. Entrants' compliance cost is taken out of C1 before the two are added." },
  { id: "O-2", channels: ["C2", "C3"], rule: "Delay costs already in the RBE are left out of the user-cost shock." },
  { id: "O-3", channels: ["C6", "C7"], rule: "Alternative routes to the same effect: one per policy (the brief's conduct lever takes one route)." },
  { id: "O-4", channels: ["C8", "C4"], rule: "A licensing change is costed in C8; its entry-cost part is not costed again in C4." },
  { id: "O-5", channels: ["C3", "C11"], rule: "A tax change's investment effect is in C3 and its funding cost in C11; the tax cut cannot also be the funding tax." },
  { id: "O-6", channels: ["custom", "any"], rule: "A custom shock on an industry and channel that a lever already covers must say whether it replaces or adds to it." },
] as const;
