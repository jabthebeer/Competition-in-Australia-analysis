// Public API of the productivity and competition engine (plan: docs/forward_plan_policy_costing.md).
// It sits beside the RBM engine and never changes the RBE (DECISIONS #81).
// P0 holds the input contract; the channel formulas and aggregation arrive in P4.
export * from "./brief";
export { CHANNELS, CHANNEL_IDS, OVERLAP_RULES, SHOCK_TYPES, channelsFor, type Channel, type ChannelId, type InputBlock, type ShockType } from "./channels";
export { SUBDIVISION_RANGES, covers, divisionOf, overlaps, type Division } from "./anzsic";
