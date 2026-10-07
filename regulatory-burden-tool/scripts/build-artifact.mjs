// Turns the ARTIFACT_BUILD output into a single page fragment for a hosted test copy:
// the host wraps it in its own <!doctype>/<head>/<body>, so this emits only a <title>,
// the inlined stylesheet, the root element and the inlined module script.
// Usage: npm run build:artifact  ->  dist-artifact/regulatory-burden-calculator.html
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dir = join(import.meta.dirname, "..", "dist-artifact");
const html = readFileSync(join(dir, "index.html"), "utf8");
const css = [...html.matchAll(/<link rel="stylesheet"[^>]*href="\.\/([^"]+)"[^>]*>/g)].map((m) => readFileSync(join(dir, m[1]), "utf8"));
const js = [...html.matchAll(/<script type="module"[^>]*src="\.\/([^"]+)"[^>]*><\/script>/g)].map((m) => readFileSync(join(dir, m[1]), "utf8"));
if (js.length !== 1) throw new Error(`Expected one script, found ${js.length}`);
const title = /<title>([^<]*)<\/title>/.exec(html)?.[1] ?? "Regulatory Burden Calculator";
const page = [
  `<title>${title}</title>`,
  `<style>\n${css.join("\n")}\n</style>`,
  `<div id="root"></div>`,
  `<script type="module">\n${js[0].replace(/<\/script/gi, "<\\/script")}\n</script>`,
  "",
].join("\n");
const out = join(dir, "regulatory-burden-calculator.html");
writeFileSync(out, page);
console.log(`Wrote ${out} (${(page.length / 1024).toFixed(0)} KB)`);
