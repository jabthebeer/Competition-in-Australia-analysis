// End-to-end tests against the production build. All data is ILLUSTRATIVE (synthetic),
// apart from the framework's own worked examples (RBM pp. 6, 8, 11).
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

/** Console errors and page errors (CSP violations are reported as console errors). */
function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

async function rbeCells(page: Page, optionId: string): Promise<string[]> {
  const cells = page.getByTestId(`rbe-${optionId}`).locator("tbody td");
  await expect(cells).toHaveCount(4);
  return cells.allTextContents();
}

async function fill(scope: Locator | Page, testId: string, value: string) {
  await scope.getByTestId(`${testId}-input`).fill(value);
}

async function loadExample(page: Page) {
  await page.goto("/#data");
  await page.getByTestId("load-example").click();
  await page.getByTestId("load-example-confirm").click();
}

async function goTo(page: Page, name: RegExp) {
  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name }).click();
}

test.beforeEach(async ({ page }) => {
  page.on("dialog", (d) => d.accept());
});

test("T-E2E-01 build a current regime, reform it, and get the illustrative RBE table ($12.7)", async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto("/");
  await page.getByTestId("title").fill("E2E: quarterly to annual (illustrative)");
  await fill(page, "pop-count", "10000");
  await page.getByRole("button", { name: "Next: the current regime" }).click();

  // Current regime: a quarterly 4-hour report for 10,000 businesses.
  await page.getByRole("button", { name: /Add an administrative cost/ }).click();
  const current = page.getByTestId(/^current-obligation-/).first();
  await current.getByTestId("obligation-name").fill("Quarterly report");
  await fill(current, "hours", "4");
  await fill(current, "times", "4");
  await expect(current.getByTestId("active-year-cost")).toHaveText("$14,646,400");
  await expect(page.getByTestId("current-total")).toContainText("$14.6m");

  // Reform it: annual, 2 hours, plus 1 hour of familiarisation.
  await page.getByRole("button", { name: "Next: design the reform options" }).click();
  const ob = page.getByTestId("reform-obligation-Quarterly report");
  await ob.getByRole("radio", { name: "Modify" }).check();
  await ob.getByTestId("lever-lessFrequent").check();
  await ob.getByTestId("lever-simplerForm").check();
  await fill(ob, "hours", "2");
  await fill(ob, "times", "1");
  await expect(ob.getByTestId("diff-summary")).toContainText("hours each time: 4 → 2");
  await expect(ob.getByTestId("diff-summary")).toContainText("times a year: 4 → 1");
  await page.getByRole("button", { name: "Add: Familiarisation with the new rules" }).click();
  await fill(page.getByTestId("transition-Familiarisation with the new rules"), "hours", "1");
  await expect(page.getByTestId("option-summary")).toContainText("Net reduction of $12.7 million a year");

  // Results: the framework's RBE table.
  await page.getByRole("button", { name: "Next: results" }).click();
  const table = page.getByTestId("rbe-option-a");
  await expect(table.locator("caption")).toHaveText("Average annual regulatory costs (from business as usual)");
  await expect(table.locator("thead th")).toHaveText(["Change in costs ($ million)", "Business", "Community organisations", "Individuals", "Total change in costs"]);
  await expect(table.locator("tbody th")).toHaveText("Total, by sector");
  expect(await rbeCells(page, "option-a")).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);
  await expect(page.getByTestId("verdict-option-a")).toHaveText("Net reduction of $12.7 million a year");
  expect(await rbeCells(page, "status-quo")).toEqual(["$0", "$0", "$0", "$0"]);
  await expect(page.getByTestId("context-option-a")).toContainText("87.5%");
  await expect(page.getByTestId("waterfall")).toBeVisible();
  await page.getByRole("radio", { name: "Exact dollars" }).check();
  expect(await rbeCells(page, "option-a")).toEqual(["($12,724,060)", "$0", "$0", "($12,724,060)"]);
  await expect(page.getByTestId("total-option-a")).toHaveText("($127,240,600)");
  expect(errors).toEqual([]);
});

test("T-E2E-02 new regulation: the framework's labour example gives $4.4", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: /New regulation/ }).check();
  await fill(page, "pop-count", "1000");
  await page.getByRole("button", { name: "Next: describe the new obligations" }).click();
  await page.getByRole("button", { name: "Add a new administrative cost" }).click();
  const card = page.getByTestId(/^new-obligation-/).first();
  await fill(card, "hours", "2");
  await fill(card, "times", "24");
  await goTo(page, /Results/);
  expect(await rbeCells(page, "option-a")).toEqual(["$4.4", "$0", "$0", "$4.4"]);
  await page.getByRole("radio", { name: "Exact dollars" }).check();
  expect(await rbeCells(page, "option-a")).toEqual(["$4,393,920", "$0", "$0", "$4,393,920"]);
});

test("T-E2E-03 outright removal: the framework's deregulatory example gives ($0.4) | $0 | $0 | ($0.4)", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: /Remove a regulation outright/ }).check();
  await fill(page, "pop-count", "1000");
  await page.getByRole("button", { name: "Next: the current regime" }).click();
  await page.getByRole("button", { name: /Add a substantive compliance cost/ }).click();
  await fill(page.getByTestId(/^current-obligation-/).first(), "unit-cost", "400");
  await goTo(page, /Results/);
  expect(await rbeCells(page, "repeal")).toEqual(["($0.4)", "$0", "$0", "($0.4)"]);
  expect(await rbeCells(page, "status-quo")).toEqual(["$0", "$0", "$0", "$0"]);
});

test("T-E2E-04 inter-jurisdictional: Commonwealth −$10m and states +$2m net to ($8.0)", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: /An inter-jurisdictional reform/ }).check();
  await fill(page, "pop-count", "1000");
  await page.getByRole("button", { name: "Next: the current regime" }).click();
  await page.getByRole("button", { name: /Add a substantive compliance cost/ }).click();
  const current = page.getByTestId(/^current-obligation-/).first();
  await current.getByTestId("obligation-name").fill("Commonwealth requirement");
  await fill(current, "unit-cost", "10000");
  await goTo(page, /Reform options/);
  await page.getByTestId("reform-obligation-Commonwealth requirement").getByRole("radio", { name: "Remove" }).check();
  await page.getByRole("button", { name: "Add a new substantive compliance cost" }).click();
  const added = page.getByTestId(/^new-obligation-/).first();
  await added.getByText("Scope checks (what counts)").click();
  await added.getByLabel("Imposed or removed by").selectOption("stateTerritory");
  await fill(added, "unit-cost", "2000");
  await goTo(page, /Results/);
  expect(await rbeCells(page, "option-a")).toEqual(["($8.0)", "$0", "$0", "($8.0)"]);
});

test("T-E2E-05 faster approvals: a delay cost reform (100 applications, 6 → 3 months, $10,000 a month) gives ($3.0)", async ({ page }) => {
  await page.goto("/");
  await fill(page, "pop-count", "100");
  await page.getByRole("button", { name: "Next: the current regime" }).click();
  await page.getByRole("button", { name: /Add a delay cost/ }).click();
  const current = page.getByTestId(/^current-obligation-/).first();
  await current.getByTestId("obligation-name").fill("Licence approval");
  await fill(current, "approval-delay", "6");
  await fill(current, "net-income", "10000");
  await goTo(page, /Reform options/);
  const ob = page.getByTestId("reform-obligation-Licence approval");
  await ob.getByRole("radio", { name: "Modify" }).check();
  await ob.getByTestId("lever-fasterApproval").check();
  await fill(ob, "approval-delay", "3");
  await goTo(page, /Results/);
  expect(await rbeCells(page, "option-a")).toEqual(["($3.0)", "$0", "$0", "($3.0)"]);
  await expect(page.getByTestId("warnings").first()).toContainText("W-17");
});

test("T-E2E-06 save and load: auto-save, download, open a file, paste a draft", async ({ page }) => {
  await loadExample(page);
  await goTo(page, /Results/);
  expect(await rbeCells(page, "annual")).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);
  expect(await rbeCells(page, "annual-dual-running")).toEqual(["($11.3)", "$0", "$0", "($11.3)"]);
  expect(await rbeCells(page, "repeal")).toEqual(["($14.6)", "$0", "$0", "($14.6)"]);
  await expect(page.getByTestId("comparison")).toBeVisible();

  // Auto-save keeps the proposal across a reload.
  await page.reload();
  await expect(page.locator(".proposal-title")).toContainText("ILLUSTRATIVE");

  // Download, start again, then open the downloaded file.
  await page.goto("/#data");
  const [download] = await Promise.all([page.waitForEvent("download"), page.getByTestId("download").click()]);
  expect(download.suggestedFilename()).toMatch(/\.rbm\.json$/);
  const path = await download.path();
  await page.getByTestId("start-new").click();
  await page.getByTestId("start-new-confirm").click();
  await expect(page.locator(".proposal-title")).toHaveText("Untitled proposal");
  await page.goto("/#data");
  await page.getByTestId("open-file").setInputFiles(path);
  await expect(page.getByText(/Loaded file/)).toBeVisible();
  await goTo(page, /Results/);
  expect(await rbeCells(page, "annual")).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);

  // A pasted draft with an unconfirmed model estimate loads, and the results are marked as a draft.
  await page.goto("/#data");
  const draft = {
    id: "draft",
    title: "Pasted draft (illustrative)",
    populations: [{ id: "biz", label: "Businesses", group: "business", count: 500 }],
    options: [
      {
        id: "option-a",
        name: "Quarterly instead of annual",
        obligations: [
          {
            id: "report",
            name: "Climate report",
            category: "administrative",
            current: { costType: "labour", timing: { type: "ongoing" }, lines: [{ populationId: "biz", labour: { hours: 10, timesPerYear: 1 } }] },
            reformed: { costType: "labour", timing: { type: "ongoing" }, lines: [{ populationId: "biz", labour: { hours: 10, timesPerYear: 4 } }] },
            provenance: { "current.lines.biz.labour.hours": { origin: "modelEstimate", note: "Illustrative guess" } },
          },
        ],
      },
    ],
  };
  await page.getByTestId("paste").fill("Here is the draft:\n```json\n" + JSON.stringify(draft) + "\n```");
  await page.getByTestId("load-paste").click();
  await expect(page.getByTestId("draft-banner")).toContainText("1 input is unconfirmed model estimate");
  await page.getByTestId("paste").fill('{"id": "broken"');
  await page.getByTestId("load-paste").click();
  await expect(page.getByTestId("import-issues")).toBeVisible();

  // Turning auto-save off is reflected in the status bar.
  await page.getByTestId("autosave").uncheck();
  await expect(page.getByTestId("save-status")).toContainText("Auto-save is off");
});

test("T-E2E-07 privacy: no requests leave the app, and the security policy blocks network calls", async ({ page, baseURL }) => {
  const errors = watchErrors(page);
  const requests: string[] = [];
  page.on("request", (r) => requests.push(r.url()));
  await loadExample(page);
  for (const name of [/Proposal/, /Current regime/, /Reform options/, /Results/]) await goTo(page, name);
  await page.getByRole("link", { name: "About" }).click();
  expect(requests.filter((u) => !u.startsWith(baseURL ?? "http://localhost:4173"))).toEqual([]);
  expect(errors).toEqual([]);
  const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
  expect(csp).toContain("connect-src 'none'");
  const attempt = await page.evaluate(() => fetch("https://example.com/").then(() => "sent", () => "blocked"));
  expect(attempt).toBe("blocked");
});

test("T-E2E-08 accessibility: axe finds no WCAG 2.2 A/AA violations on any page", async ({ page }) => {
  await loadExample(page);
  for (const route of ["proposal", "current", "options", "results", "data", "about"]) {
    await page.goto(`/#${route}`);
    await page.locator("main h1").waitFor();
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    const summary = r.violations.map((v) => `${route}: ${v.id} (${v.impact}) ×${v.nodes.length}: ${v.nodes[0]?.target.join(" ")}`);
    expect(summary).toEqual([]);
  }
});

test("T-E2E-09 first visit offers the illustrative example; a proposal copied as text loads back", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await page.getByTestId("first-run").getByRole("button", { name: "Load the illustrative example" }).click();
  await expect(page.getByTestId("first-run")).toHaveCount(0);
  await goTo(page, /Results/);
  expect(await rbeCells(page, "annual")).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);
  // Copy as text (the route that works where downloads are blocked), start again, paste it back.
  await page.goto("/#data");
  await page.getByTestId("copy-text").click();
  await expect(page.getByText(/Copied/)).toBeVisible();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  await page.getByTestId("start-new").click();
  await page.getByTestId("start-new-confirm").click();
  await page.goto("/#data");
  await page.getByTestId("paste").fill(copied);
  await page.getByTestId("load-paste").click();
  await goTo(page, /Results/);
  expect(await rbeCells(page, "annual")).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);
});

