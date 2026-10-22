// Bundles the ALICIA costing parameters (data/processed/costing/parameters.json, written by
// `alicia costing-params`) into the app as the virtual module "virtual:costing-parameters".
// The built page makes no network requests (DECISIONS #37), so the data travels inside the bundle:
// rebuilding the site after `alicia costing-params --refresh` is what brings in a new release.
// COSTING_PARAMS overrides the path; without a file the module holds an empty parameter set.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Plugin } from "vite";

export const DEFAULT_PARAMS_PATH = resolve(import.meta.dirname, "..", "data", "processed", "costing", "parameters.json");
export const EMPTY_PARAMETERS = { schema: "alicia-costing-parameters", version: 1, vintage: null, sources: [], tables: {} };

const ID = "virtual:costing-parameters";
const RESOLVED = `\0${ID}`;

export function costingParameters(path: string = process.env.COSTING_PARAMS ?? DEFAULT_PARAMS_PATH): Plugin {
  return {
    name: "costing-parameters",
    resolveId: (id) => (id === ID ? RESOLVED : undefined),
    load(id) {
      if (id !== RESOLVED) return undefined;
      const found = existsSync(path);
      if (found) this.addWatchFile(path);
      const json = found ? readFileSync(path, "utf8") : JSON.stringify(EMPTY_PARAMETERS);
      // JSON.parse of a string literal is faster to start up than an object literal of the same size.
      return `export default JSON.parse(${JSON.stringify(json)});`;
    },
  };
}
