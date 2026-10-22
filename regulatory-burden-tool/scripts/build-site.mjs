// Turns the SITE_BUILD output into the ALICIA website's Policy costing tab:
// dist-site/index.html becomes dist-site/costing.html, marked data-site="alicia" so the site theme applies.
// `alicia site --costing dist-site` then copies it into the site and fills the <!--__NAV__--> placeholder.
// Usage: npm run build:site
import { readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dir = join(import.meta.dirname, "..", "dist-site");
const html = readFileSync(join(dir, "index.html"), "utf8");
for (const [what, needle] of [
  ["navigation placeholder", "<!--__NAV__-->"],
  ["Content-Security-Policy", "connect-src 'none'"],
]) {
  if (!html.includes(needle)) throw new Error(`dist-site/index.html has no ${what}`);
}
writeFileSync(join(dir, "index.html"), html.replace('<html lang="en-AU">', '<html lang="en-AU" data-site="alicia">'));
renameSync(join(dir, "index.html"), join(dir, "costing.html"));
console.log(`Wrote ${join(dir, "costing.html")}`);
