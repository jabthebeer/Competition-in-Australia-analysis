// End-to-end tests of the productivity and competition costing against the production build. All briefs are
// ILLUSTRATIVE (synthetic): the bundled costing example (lighter licensing for electricians) and briefs built here.
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

async function loadCostingExample(page: Page) {
  await page.goto("/#data");
  await page.getByTestId("load-brief-example").click();
  await page.getByTestId("load-brief-example-confirm").click();
  await expect(page.locator(".success")).toContainText("costing example");
}

async function goTo(page: Page, name: RegExp) {
  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name }).click();
}

test("T-E2E-11 the costing example: scope data, the levers' chains, results with ranges and the gate, the competition screen, CSV", async ({ page }) => {
  const errors = watchErrors(page);
  await loadCostingExample(page);

  await goTo(page, /Scope/);
  await expect(page.getByTestId("scope-industry-0")).toContainText("3232 Electrical Services");
  await expect(page.getByTestId("scope-facts")).toContainText("48,274");

  await goTo(page, /Productivity levers/);
  const c8 = page.getByTestId("lever-labour").getByTestId("channel-C8");
  await expect(c8).toContainText("Evidence grade C");
  await expect(c8).toContainText("+0.8 %");
  await expect(page.getByTestId("lever-burden").getByTestId("channel-C1")).toContainText("Evidence grade A");
  await expect(page.getByTestId("similar-changes")).toContainText("Automatic mutual recognition");

  await goTo(page, /Results/);
  await expect(page.getByTestId("rbe-three-yearly")).toBeVisible(); // the burden results stay first
  const gate = page.getByTestId("gate");
  await expect(gate).toHaveAttribute("data-status", "indicative", { timeout: 30_000 });
  await expect(gate).toContainText("below the $200m threshold");
  await expect(page.getByTestId("productivity-headline")).toContainText("10–90% range");
  await expect(page.getByTestId("threshold2")).toContainText("does not meet it");
  await expect(page.getByTestId("productivity-years").locator("tbody tr")).toHaveCount(4);
  await expect(page.getByTestId("productivity-channels")).toContainText("C8 Labour mobility");
  await expect(page.getByTestId("productivity-path")).toBeVisible();
  await expect(page.getByTestId("productivity-tornado")).toContainText("occupational entry regulation");
  await expect(page.getByTestId("not-quantified")).toContainText("terms of trade");
  const download = page.waitForEvent("download");
  await page.getByTestId("download-csv").click();
  const csv = await download;
  expect(csv.suggestedFilename()).toBe("illustrative-licensing-productivity.csv");

  await goTo(page, /Competition screen/);
  await expect(page.getByTestId("category-barriers")).toBeChecked();
  await expect(page.getByTestId("category-number-or-type")).toBeChecked();
  await expect(page.getByTestId("share-affected")).toContainText("20.7%");
  await expect(page.getByTestId("bcs-barrier")).toContainText("20.2%");
  await expect(page.getByTestId("competition-gdp")).toContainText("indicative", { timeout: 30_000 });
  // Unticking a suggestion is kept.
  await page.getByTestId("category-number-or-type").uncheck();
  await expect(page.getByTestId("competition-verdict")).toContainText("1 of the five");
  expect(errors).toEqual([]);
});

test("T-E2E-12 a costing from scratch: an industry, a non-compete ban, then results; an incomplete lever is reported", async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto("/");
  await page.getByTestId("title").fill("E2E: ban non-competes (illustrative)");
  await page.getByRole("button", { name: "Next: the industries affected" }).click();
  await page.getByTestId("scope-add-code").fill("M");
  await page.getByTestId("scope-add").click();
  await expect(page.getByTestId("scope-industry-0")).toContainText("Professional, Scientific and Technical Services");

  await goTo(page, /Productivity levers/);
  await page.getByTestId("lever-labour-toggle").check();
  await page.getByTestId("lever-noncompete-share-input").fill("-20");
  await expect(page.getByTestId("lever-labour").getByTestId("channel-C8")).toContainText("+0.19 %");

  // A custom estimate without a reason stops the costing, and says why.
  await page.getByTestId("lever-custom-toggle").check();
  await expect(page.getByTestId("brief-issues")).toContainText("justification");
  await page.getByTestId("lever-custom-toggle").uncheck();
  await expect(page.getByTestId("brief-issues")).toHaveCount(0);

  await goTo(page, /Results/);
  await expect(page.getByTestId("no-burden")).toBeVisible();
  await expect(page.getByTestId("gate")).toHaveAttribute("data-status", "indicative", { timeout: 30_000 });
  await expect(page.getByTestId("productivity-headline")).toContainText("million a year");
  // The PC's 10% pass-through is the top of its range, so the central estimate sits above most draws, and says so.
  await expect(page.getByTestId("central-outside")).toContainText("median");
  // The realisation factor scales the effect: at 0 there is nothing to show but the gate.
  await page.getByText("Settings: realisation, discount rate, number of draws").click();
  await page.getByTestId("analysis-realisation-input").fill("0");
  await expect(page.getByTestId("gate")).toContainText("No channel changes GDP", { timeout: 30_000 });
  expect(errors).toEqual([]);
});

test("T-E2E-13 the productivity pages pass axe with a costing loaded and fit a phone screen", async ({ page }) => {
  await loadCostingExample(page);
  for (const route of ["scope", "levers", "competition", "results"]) {
    await page.goto(`/#${route}`);
    await page.locator("main h1").waitFor();
    if (route === "results" || route === "competition") await page.getByTestId(route === "results" ? "gate" : "competition-gdp").waitFor({ timeout: 30_000 });
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(r.violations.map((v) => `${route}: ${v.id} (${v.impact}) ×${v.nodes.length}: ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of ["scope", "levers", "competition", "results"]) {
    await page.goto(`/#${route}`);
    await page.locator("main h1").waitFor();
    if (route === "results") await page.getByTestId("gate").waitFor({ timeout: 30_000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, route).toBeLessThanOrEqual(0);
  }
});

test("T-E2E-14 the whole costing saves to a file and loads back", async ({ page }) => {
  await loadCostingExample(page);
  await page.goto("/#data");
  const download = page.waitForEvent("download");
  await page.getByTestId("download-brief").click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/\.brief\.json$/);
  const path = await file.path();
  await page.getByTestId("start-new").click();
  await page.getByTestId("start-new-confirm").click();
  await page.goto("/#data");
  await page.getByTestId("open-file").setInputFiles(path);
  await expect(page.locator(".success")).toContainText("with its productivity levers");
  await goTo(page, /Productivity levers/);
  await expect(page.getByTestId("lever-labour").getByTestId("channel-C8")).toContainText("+0.8 %");
});

test("T-E2E-15 the scope screener answers whether a cost is in the RBE, with the framework's page", async ({ page }) => {
  await page.goto("/#current");
  await page.getByText("Is a cost in scope? Check it with the screener").click();
  await page.getByTestId("screener-feeToGovernment").getByRole("radio", { name: "Yes", exact: true }).check();
  await page.getByTestId("screener-waitingOnGovernment").getByRole("radio", { name: "No", exact: true }).check();
  const out = page.getByTestId("screener-outcomes");
  await expect(out).toContainText("Cost part of it. The amount paid is out of scope");
  await expect(out).toContainText("Leave it out. Delay costs only count while waiting on government action");
  await expect(out).toContainText("RBM p. 10");
});
