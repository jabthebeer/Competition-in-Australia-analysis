import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

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

export default defineConfig({
  base: "./",
  plugins: [react(), contentSecurityPolicy()],
  build: { outDir: "dist", sourcemap: false },
  preview: { port: 4173, strictPort: true },
});
