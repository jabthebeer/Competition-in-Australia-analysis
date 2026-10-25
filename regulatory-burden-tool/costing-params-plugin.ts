// Bundles the ALICIA costing parameters (data/processed/costing/parameters.json, written by
// `alicia costing-params`) into the app as the virtual module "virtual:costing-parameters", and the
// register export (register.json, written by `alicia costing-register`) as "virtual:costing-register".
// The built page makes no network requests (DECISIONS #37), so the data travels inside the bundle:
// rebuilding the site after `alicia costing-params --refresh` is what brings in a new release.
// COSTING_PARAMS and COSTING_REGISTER override the paths; without a file a module holds an empty set.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Plugin } from "vite";

export const DEFAULT_PARAMS_PATH = resolve(import.meta.dirname, "..", "data", "processed", "costing", "parameters.json");
export const DEFAULT_REGISTER_PATH = resolve(import.meta.dirname, "..", "data", "processed", "costing", "register.json");
export const EMPTY_PARAMETERS = { schema: "alicia-costing-parameters", version: 1, vintage: null, sources: [], tables: {} };
export const EMPTY_REGISTER = { schema: "alicia-costing-register", version: 1, channels: {}, records: [] };

export function costingParameters(
  path: string = process.env.COSTING_PARAMS ?? DEFAULT_PARAMS_PATH,
  registerPath: string = process.env.COSTING_REGISTER ?? DEFAULT_REGISTER_PATH,
): Plugin {
  const modules: Record<string, { path: string; empty: unknown }> = {
    "virtual:costing-parameters": { path, empty: EMPTY_PARAMETERS },
    "virtual:costing-register": { path: registerPath, empty: EMPTY_REGISTER },
  };
  return {
    name: "costing-parameters",
    resolveId: (id) => (id in modules ? `\0${id}` : undefined),
    load(id) {
      const m = id.startsWith("\0") ? modules[id.slice(1)] : undefined;
      if (!m) return undefined;
      const found = existsSync(m.path);
      if (found) this.addWatchFile(m.path);
      const json = found ? readFileSync(m.path, "utf8") : JSON.stringify(m.empty);
      // JSON.parse of a string literal is faster to start up than an object literal of the same size.
      return `export default JSON.parse(${JSON.stringify(json)});`;
    },
  };
}
