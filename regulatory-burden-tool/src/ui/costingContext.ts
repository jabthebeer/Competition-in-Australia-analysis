// The costing context (input-output weights, GDP, entry rates, …) and the register, loaded once from the bundled
// data when a page first needs them. Both sit in their own chunks, so the burden pages stay small.
import { useEffect, useState } from "react";
import { buildContext, type CostingContext, type ParameterFile } from "../productivity/index";
import { loadCostingParameters, loadCostingRegister, type CostingParameters, type CostingRegister } from "./costingData";

export type Loaded<T> = { status: "loading" } | ({ status: "ready" } & T) | { status: "error"; problem: string };

let contextPromise: Promise<Loaded<{ ctx: CostingContext; parameters: CostingParameters }>> | null = null;
let registerPromise: Promise<Loaded<{ register: CostingRegister }>> | null = null;

export function loadContext() {
  contextPromise ??= loadCostingParameters()
    .then((r): Loaded<{ ctx: CostingContext; parameters: CostingParameters }> => {
      if (!r.ok) return { status: "error", problem: `The costing parameters in this build are unreadable (${r.problem}).` };
      try {
        return { status: "ready", ctx: buildContext(r.parameters as unknown as ParameterFile), parameters: r.parameters };
      } catch (e) {
        return { status: "error", problem: `This build has no usable costing parameters: ${e instanceof Error ? e.message : String(e)}.` };
      }
    })
    .catch((e: unknown) => ({ status: "error", problem: `The costing parameters couldn't be loaded: ${String(e)}.` }));
  return contextPromise;
}

export function loadRegister() {
  registerPromise ??= loadCostingRegister()
    .then((r): Loaded<{ register: CostingRegister }> => (r.ok ? { status: "ready", register: r.register } : { status: "error", problem: `The register in this build is unreadable (${r.problem}).` }))
    .catch((e: unknown) => ({ status: "error", problem: `The register couldn't be loaded: ${String(e)}.` }));
  return registerPromise;
}

function useLoaded<T>(load: () => Promise<Loaded<T>>): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ status: "loading" });
  useEffect(() => {
    let live = true;
    void load().then((s) => live && setState(s));
    return () => {
      live = false;
    };
  }, [load]);
  return state;
}

export const useCostingContext = () => useLoaded(loadContext);
export const useRegister = () => useLoaded(loadRegister);
