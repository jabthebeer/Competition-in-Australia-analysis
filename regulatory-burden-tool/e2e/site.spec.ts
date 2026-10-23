// End-to-end tests of the ALICIA website build (npm run build:site), served on its own port.
// The navigation placeholder is filled by `alicia site` (tested in alicia/tests/test_site.py).
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const SITE = "http://localhost:4174";

test("T-E2E-10 website build: the ALICIA theme, the same privacy policy, the data list, and no WCAG 2.2 A/AA violations", async ({ page }) => {
  const errors: string[] = [];
  const requests: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => requests.push(r.url()));
  await page.goto(`${SITE}/costing.html#about`);
  await page.locator("main h1").waitFor();
  expect(await page.locator("html").getAttribute("data-site")).toBe("alicia");
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--accent").trim())).toBe("#1d5c57");
  expect(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content")).toContain("connect-src 'none'");
  await expect(page.getByRole("heading", { name: "Productivity and competition costing" })).toBeVisible();
  await expect(page.getByText(/Loading the data list/)).toHaveCount(0);
  for (const route of ["proposal", "current", "options", "results", "data", "sources", "about"]) {
    await page.goto(`${SITE}/costing.html#${route}`);
    await page.locator("main h1").waitFor();
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(r.violations.map((v) => `${route}: ${v.id} ×${v.nodes.length}`)).toEqual([]);
  }
  expect(requests.filter((u) => !u.startsWith(SITE))).toEqual([]);
  expect(errors).toEqual([]);
});
