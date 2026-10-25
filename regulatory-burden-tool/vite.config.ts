import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";
import { costingParameters } from "./costing-params-plugin";

// Privacy by design (DECISIONS #37): the built app may not contact any server.
// connect-src 'none' blocks fetch, XHR and WebSockets; everything else must come from
// the app's own origin (no CDNs, no third-party fonts or scripts). Applied to the
// production build only, because the dev server needs a WebSocket for hot reload.
export const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'none'",
].join("; ");

function contentSecurityPolicy(): Plugin {
  return {
    name: "content-security-policy",
    apply: "build",
    transformIndexHtml: (html) =>
      html.replace("<head>", `<head>\n    <meta http-equiv="Content-Security-Policy" content="${CONTENT_SECURITY_POLICY}" />`),
  };
}

// ARTIFACT_BUILD=1 produces the hosted test copy (see scripts/build-artifact.mjs): one JavaScript
// file, no CSP meta tag (the host applies its own policy, which also blocks outside requests).
// SITE_BUILD=1 produces the ALICIA website's Policy costing tab (see scripts/build-site.mjs): the same
// app and CSP, with its assets in costing-assets/ so they sit beside the other site pages.
const artifact = process.env.ARTIFACT_BUILD === "1";
const site = process.env.SITE_BUILD === "1";

export default defineConfig({
  base: "./",
  define: site ? { "import.meta.env.VITE_SITE": JSON.stringify("1") } : {},
  plugins: artifact ? [react(), costingParameters()] : [react(), costingParameters(), contentSecurityPolicy()],
  build: artifact
    ? { outDir: "dist-artifact", sourcemap: false, cssCodeSplit: false, rolldownOptions: { output: { inlineDynamicImports: true } } }
    : site
      ? {
          outDir: "dist-site",
          assetsDir: "costing-assets",
          sourcemap: false,
          // No leading underscores in file names (some static hosts hide them); the virtual module's chunk has one.
          rolldownOptions: { output: { chunkFileNames: (c: { name: string }) => `costing-assets/${c.name.replace(/^_+/, "")}-[hash].js` } },
        }
      : { outDir: "dist", sourcemap: false },
  preview: { port: 4173, strictPort: true },
});
