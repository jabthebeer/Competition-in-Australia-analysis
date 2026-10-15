import { describe, expect, it } from "vitest";
import { computeProposal, importDraft, parseProposal } from "../../src/engine/index";
import { illustrativeReform, labour, ob, opt, option, pop, proposal, side } from "./helpers";

// A language-model style draft (ILLUSTRATIVE): structure from the description, hours as an unconfirmed estimate.
const draft = () =>
  proposal([pop("biz", 2000, { provenance: { count: { origin: "description" } } })], [
    option("quarterly", [
      ob("climate-report", "administrative", side("labour", [labour("biz", 10, 1)]), side("labour", [labour("biz", 10, 4)]), {
        provenance: {
          "current.timing.type": { origin: "description" },
          "reformed.lines.biz.labour.timesPerYear": { origin: "description", note: "Quarterly instead of annually" },
          "current.lines.biz.labour.hours": { origin: "modelEstimate", note: "Hours per report: illustrative guess" },
          "reformed.lines.biz.labour.hours": { origin: "modelEstimate" },
        },
      }),
    ]),
  ]);

describe("Provenance labels and draft import (DECISIONS #58-#60)", () => {
  it("T-PROV-01 provenance is stored, never changes the numbers, and unconfirmed model estimates mark results as a draft", () => {
    const withProv = computeProposal(draft());
    const p = draft() as { populations: { provenance?: unknown }[]; options: { obligations: { provenance?: unknown }[] }[] };
    delete p.populations[0]!.provenance;
    delete p.options[0]!.obligations[0]!.provenance;
    const without = computeProposal(p);
    expect(opt(withProv).rbe).toEqual(opt(without).rbe);
    expect(withProv.unconfirmedEstimates.map((e) => e.path)).toEqual(["current.lines.biz.labour.hours", "reformed.lines.biz.labour.hours"]);
    expect(without.unconfirmedEstimates).toEqual([]);
    expect(withProv.assumptions.some((a) => a.item.startsWith("Unconfirmed model estimate"))).toBe(true);
    // Confirming with a source clears the draft state; a "sourced" label without a source is rejected.
    const confirmed = draft() as { options: { obligations: { provenance: Record<string, unknown> }[] }[] };
    for (const k of Object.keys(confirmed.options[0]!.obligations[0]!.provenance)) {
      confirmed.options[0]!.obligations[0]!.provenance[k] = { origin: "sourced", source: { description: "Illustrative survey" } };
    }
    expect(computeProposal(confirmed).unconfirmedEstimates).toEqual([]);
    confirmed.options[0]!.obligations[0]!.provenance["reformed.lines.biz.labour.hours"] = { origin: "sourced" };
    expect(() => parseProposal(confirmed)).toThrow(/needs a source/);
  });

  it("T-DRAFT-01 pasted drafts load from a fenced reply, a bare proposal or a saved file, and problems come back as a list", () => {
    const bare = JSON.stringify(draft());
    const fencedReply = `Here is the draft costing:\n\n\`\`\`json\n${bare}\n\`\`\`\nCheck the hours.`;
    for (const text of [bare, fencedReply, JSON.stringify({ schemaVersion: 1, proposal: draft() }), JSON.stringify({ proposal: draft() })]) {
      const r = importDraft(text);
      expect(r.ok).toBe(true);
      if (r.ok) expect(r.file.proposal.options[0]!.obligations[0]!.id).toBe("climate-report");
    }
    const notJson = importDraft("Sorry, I can't help with that.");
    expect(notJson).toEqual({ ok: false, issues: ["(text): no JSON object found"] });
    const broken = importDraft('{"id": "x", ');
    expect(broken.ok).toBe(false);
    const invalid = importDraft(JSON.stringify({ ...draft(), discountRate: 0.07 }));
    expect(invalid.ok).toBe(false);
    if (!invalid.ok) expect(invalid.issues.join("\n")).toMatch(/discountRate/);
    expect(importDraft(JSON.stringify(illustrativeReform())).ok).toBe(true);
  });
});
