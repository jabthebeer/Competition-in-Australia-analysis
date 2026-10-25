// Writes the bundled costing example and the four other worked examples of plan §8 (P6) to examples/, from the
// published figures each cites (page by page, in the briefs' provenance) and the derived inputs computed here from
// the bundled parameters and the ABS CABEE state panel. Run with: npx tsx scripts/make-worked-examples.ts
// Re-running after a data refresh can move the derived inputs (business splits, exposures); the frozen outputs in
// tests/productivity/frozen/ then need `npm run worked:examples`.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { parseBrief } from "../src/productivity/index";

const tool = join(import.meta.dirname, "..");
const repo = join(tool, "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8"));
type Row = Record<string, string | number | null>;
const rows = (table: string): Row[] => params.tables[table].rows;
const DIVISIONS = "ABCDEFGHIJKLMNOPQRS".split("");
const divisionName = new Map(rows("abs_anzsic.codes").filter((r) => r.level === "division").map((r) => [String(r.code), String(r.name)]));
const ACCESSED = "2026-10-25";

type Source = { description: string; url: string; vintage?: string; accessed: string };
const src = (description: string, url: string, vintage?: string): Source => ({ description, url, ...(vintage ? { vintage } : {}), accessed: ACCESSED });
const sourced = (note: string, source: Source) => ({ origin: "sourced", note, source });
/** A value computed here from sourced data: "sourced", with the computation in the note ("modelEstimate" means a language model's estimate, PB-04). */
const derived = (note: string, source: Source) => ({ origin: "sourced", note, source });
const ABS_CABEE = src("ABS, Counts of Australian Businesses, including Entries and Exits (bundled parameters, abs_cabee_latest)", "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release");
const ABS_CABEE_STATE = src("ABS, Counts of Australian Businesses, including Entries and Exits, data cube 2 by state (data/processed/abs_cabee)", "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits");
const ABS_ASNA = src("ABS, Australian System of National Accounts, 2025-26: capital by industry (bundled parameters, abs_asna.capital)", "https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release");
const ABS_OSCA = src("ABS, OSCA – Occupation Standard Classification for Australia, 2024, Version 1.0", "https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia/2024-version-1-0");
const r2 = (x: number) => Math.round(x * 100) / 100;
const r4 = (x: number) => Math.round(x * 1e4) / 1e4;

function write(name: string, brief: object) {
  parseBrief(brief); // fails loudly if the brief is not valid
  writeFileSync(join(tool, "examples", name), `${JSON.stringify(brief, null, 2)}\n`, "utf8");
  console.log(`Wrote examples/${name}`);
}

// ---- 1. The bundled costing example: banning non-compete clauses (Treasury Impact Analysis, 2026) -----------------

const NC_URL = "https://oia.pmc.gov.au/sites/default/files/posts/2026/09/Impact%20Analysis.pdf";
const NC_PAGE = "https://oia.pmc.gov.au/published-impact-analyses-and-reports/non-compete-clauses-and-other-worker-restraints";
const ia = (loc: string) => src(`Treasury, Impact Analysis: Non-compete clauses and other worker restraints (OIA, published 21 September 2026), ${loc}`, NC_URL, "September 2026");

function noncompete() {
  // IA p. 52: 925,758 employing small businesses and 73,403 medium and large ones (CABEE, 2024-25); Table 6 and p. 52:
  // 20.2% of small businesses use non-compete clauses, 29.75% of those with 20-199 employees, 38.7% of those with 200+.
  const SMALL = 925758;
  const MED_LARGE = 73403;
  // The IA does not split its 73,403: split it by CABEE's counts at June 2024 (the start of 2024-25, latest release).
  const cab = { "20-199": 0, "200+": 0 };
  for (const r of rows("abs_cabee_latest.class_size")) if (r.level === "division" && (r.size_band === "20-199" || r.size_band === "200+")) cab[r.size_band] += Number(r.start);
  const MED = Math.round((MED_LARGE * cab["20-199"]) / (cab["20-199"] + cab["200+"]));
  const LARGE = MED_LARGE - MED;
  const users = { small: Math.round(SMALL * 0.202), medium: Math.round(MED * 0.2975), large: Math.round(LARGE * 0.387) };
  const split = ia("p. 52 (PDF p. 55): 73,403 medium and large businesses, split here by ABS CABEE counts at June 2024");

  const rate = (id: string, label: string, hourly: number, wage: number, who: string) => ({
    id,
    label,
    kind: "work",
    hourly,
    override: {
      justification: `Treasury's rate for ${who}: Glassdoor mean hourly pay of $${wage.toFixed(2)} (IA Table 5), times the RBM's 1.75 on-cost multiplier, which the IA's $38.2 million for small businesses implies (925,758 × 20.2% × 1.5 hours × $77.88 × 1.75)`,
      source: ia("Table 5 and p. 52 (PDF p. 55)"),
    },
  });
  const share = {
    small: "20.2% of employing small businesses use non-compete clauses (IA Table 6)",
    medium: "29.75% of businesses with 20–199 employees use them (IA p. 52, averaging Table 6's 20–49 and 50–199 rows)",
    large: "38.7% of businesses with 200+ employees use them (IA p. 52)",
  } as const;
  const line = (pop: keyof typeof users, hours: number, rateId: string, staff = 1) => ({ populationId: pop, entities: users[pop], labour: { hours, timesPerYear: 1, staff, rateId }, note: share[pop] });
  const option = (id: string, name: string, description: string, hours: number) => {
    const s = ia("Table 4 and pp. 51–53 (PDF pp. 54–56)");
    return {
      id,
      name,
      description,
      transitions: [
        {
          id: "familiarisation-lead",
          name: "Familiarisation with the reforms: the person responsible",
          category: "administrative",
          description:
            "Reading the new requirements and guidance and considering their effect on the business's use of restraint clauses (IA p. 51). Small businesses: a corporate manager or director; medium and large: an HR manager or director.",
          reformed: { costType: "labour", timing: { type: "oneOff", year: 1 }, lines: [line("small", hours, "corporate-manager"), line("medium", hours, "hr-manager"), line("large", hours, "hr-manager")] },
          provenance: Object.fromEntries(
            (["small", "medium", "large"] as const).map((p) => [`reformed.lines.${p}.labour.hours`, sourced(`${hours * 60} minutes, from the UK Department for Business and Trade's impact assessment, as Treasury used`, s)]),
          ),
        },
        {
          id: "familiarisation-hr-assistants",
          name: "Familiarisation with the reforms: three HR administrative assistants",
          category: "administrative",
          reformed: { costType: "labour", timing: { type: "oneOff", year: 1 }, lines: [line("medium", hours, "hr-assistant", 3), line("large", hours, "hr-assistant", 3)] },
        },
      ],
    };
  };

  write("noncompete-ban.brief.json", {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "noncompete-ban",
    meta: {
      title: "Banning non-compete clauses for low- and middle-income workers (2025-26 Budget)",
      summary:
        "Real policy: the ban on non-compete clauses for employees earning below the Fair Work Act high-income threshold, announced on 25 March 2025 with the 2025-26 Budget, and Treasury's preferred option in its Impact Analysis (OIA, 21 September 2026). The reforms apply prospectively, to new and varied employment contracts, from 2027. The burden proposal holds the Impact Analysis's familiarisation costs for Options 2 and 3; the labour lever follows the Productivity Commission's 2024 non-compete simulation, which Treasury cites. Treasury's own GDP figure is the PC's $5.1 billion.",
      jurisdictions: ["CTH"],
      proposalType: "reform",
      startYear: 2027,
      phaseInYears: 7,
      durationYears: 10,
      priceBase: "2025-26",
      source: src("Treasury, Impact Analysis: Non-compete clauses and other worker restraints (Office of Impact Analysis, published 21 September 2026)", NC_PAGE, "September 2026"),
      provenance: {
        startYear: sourced("The reforms apply prospectively from 2027 (IA summary; p. 28). The IA gives the year, not the date.", ia("IA summary and p. 28 (PDF p. 31)")),
        phaseInYears: sourced("Most employees are expected to have a new or varied contract within 5–10 years (IA p. 50); 7 years is that range's midpoint, rounded down to whole years.", ia("p. 50 (PDF p. 53)")),
      },
    },
    scope: {
      industries: DIVISIONS.map((d) => ({
        anzsic: d,
        exposure: 1,
        role: "direct",
        note: `${divisionName.get(d)}${d === "A" ? " (the PC leaves agriculture out of its non-compete simulation, so C8 does too)" : ""}`,
      })),
      sizeBands: ["nonEmploying", "1-4", "5-19", "20-199", "200+"],
      entityTypes: ["private"],
    },
    burden: {
      id: "noncompete-ban-burden",
      title: "Non-compete clauses and other worker restraints: familiarisation costs (Treasury Impact Analysis, 2026)",
      description:
        "The Impact Analysis's regulatory burden estimate (Table 4), rebuilt from its stated inputs (Tables 5 and 6, p. 52). Option 3 reproduces Treasury's $16.3 million; Option 2 comes to about $48.9 million against Treasury's $46.4 million, because Treasury's $7.5 million and $0.7 million for medium and large businesses are less than three times its Option 3 figures although Option 2's time is three times as long (90 minutes against 30).",
      proposalType: "reform",
      durationYears: 10,
      jurisdiction: "commonwealthOnly",
      baseline: "statusQuo",
      rates: {
        work: { hourly: 91.54, base: 52.31, multiplier: 1.75 },
        leisure: { hourly: 41 },
        volunteer: { hourly: 41 },
        custom: [
          rate("corporate-manager", "Corporate manager or director (small businesses)", 136.29, 77.88, "the corporate manager or director who reads the reforms in a small business"),
          rate("hr-manager", "HR manager or director (medium and large businesses)", 115.27, 65.87, "the HR manager or director in a medium or large business"),
          rate("hr-assistant", "HR administrative assistant (medium and large businesses)", 68.2, 38.97, "each of three HR administrative assistants in a medium or large business"),
        ],
      },
      populations: [
        { id: "small", label: "Employing small businesses (1–19 employees)", group: "business", cohort: "small", count: SMALL, source: ia("p. 52 (PDF p. 55), citing ABS Counts of Australian Businesses") },
        {
          id: "medium",
          label: "Medium businesses (20–199 employees)",
          group: "business",
          cohort: "medium",
          count: MED,
          source: split,
          provenance: { count: derived(`The IA's 73,403 medium and large businesses, split by CABEE's June 2024 counts (${cab["20-199"].toLocaleString("en-AU")} with 20–199 employees, ${cab["200+"].toLocaleString("en-AU")} with 200+)`, ABS_CABEE) },
        },
        { id: "large", label: "Large businesses (200 or more employees)", group: "business", cohort: "large", count: LARGE, source: split, provenance: { count: derived("As for medium businesses", ABS_CABEE) } },
      ],
      options: [
        option(
          "option-2-partial-ban",
          "Option 2: partial ban (preferred)",
          "Ban non-compete clauses for employees earning below the Fair Work Act high-income threshold ($183,100), ban co-worker non-solicitation clauses, no-poach and wage-fixing agreements, and limit the remaining restraints (a 6-month limit on non-competes above the threshold; no cascading clauses). 90 minutes of familiarisation (IA Table 5).",
          1.5,
        ),
        option(
          "option-3-full-ban",
          "Option 3: full ban of employment restraints of trade",
          "Ban all post-employment restraints of trade, including non-compete clauses for high-income employees and client non-solicitation clauses. 30 minutes of familiarisation (IA Table 5).",
          0.5,
        ),
      ],
    },
    levers: {
      labour: {
        nonCompetes: { coveredShareChange: { low: -0.2, high: -0.18 } },
        provenance: {
          "nonCompetes.coveredShareChange": sourced(
            "A ban removes the coverage of the one in five workers bound by a non-compete (−0.2, the PC's simulation). Option 2 keeps non-competes, for up to 6 months, above the high-income threshold; Treasury expects it to deliver at least 90% of a full ban's increase in job mobility, so the low end of the change is 90% of −0.2.",
            ia("p. 41 (PDF p. 44)"),
          ),
        },
      },
    },
    competition: {
      categories: { barriers: true, "number-or-type": true, "ability-incentive": true, "prices-market-share": true, "consumer-choice": false },
      alternatives:
        "Option 1, the status quo: the common law restraint of trade doctrine, with the NSW Restraints of Trade Act still applying to NSW contracts. Option 3, a full ban of all employment restraints of trade, including non-competes for high-income employees and client non-solicitation clauses. Treasury preferred Option 2: it is more targeted, leaving businesses able to use reasonable non-competes for high-income employees and client non-solicitation clauses to protect legitimate interests, and so to invest in training and other assets; Option 3's mobility gains would be larger but it would give businesses no flexibility (IA pp. 27 and 62).",
      benefits:
        "Higher wages and job mobility: workers at firms that use non-competes extensively are paid about 4% less (e61), and job mobility could rise by 1–2 percentage points; Option 2 delivers at least 90% of a full ban's increase (IA summary; p. 41). More entrepreneurship and new businesses, knowledge spillovers, lower litigation costs (Option 3 saves up to $17 million a year), and consumer prices about 0.1% lower in the PC's modelling (IA summary; pp. 48–49).",
    },
  });
}

// ---- 2. Automatic mutual recognition of occupational registrations (2021) -----------------------------------------

const PC_MR = src("Productivity Commission (2015), Mutual Recognition Schemes, Research Report", "https://assets.pc.gov.au/inquiries/completed/mutual-recognition-schemes/report/mutual-recognition-schemes.pdf", "September 2015");
const PC_NCP = src("Productivity Commission (2024), National Competition Policy: modelling proposed reforms (study report with appendices)", "https://assets.pc.gov.au/2025-10/competition-analysis-study-report-plus.pdf", "November 2024");

function amr() {
  // PC (2015) p. 171 (PDF p. 185), citing NOLA (2014): the aggregate annual cost of holding multiple licences.
  const groups = [
    { id: "electrical", label: "Electrical licence holders with a licence in a second jurisdiction (aggregate)", industry: "3232", cost: 2.7e6 },
    { id: "plumbing", label: "Plumbing and gasfitting licence holders with a licence in a second jurisdiction (aggregate)", industry: "3231", cost: 1.4e6 },
    { id: "property", label: "Property licence holders with a licence in a second jurisdiction (aggregate)", industry: "6720", cost: 2.3e6 },
  ];
  const cost = src("Productivity Commission (2015), Mutual Recognition Schemes, p. 171 (PDF p. 185), citing NOLA (2014)", PC_MR.url, "September 2015");
  write("worked-amr.brief.json", {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "worked-amr",
    meta: {
      title: "Automatic mutual recognition of occupational registrations (2021)",
      summary:
        "Worked example (P6). Automatic mutual recognition lets a worker registered in one state or territory work in another without a second registration (Mutual Recognition Act 1992, Part 3A, from 1 July 2021). It shows what the tool can and cannot cost: the second registrations' fees are outside the RBE and are a transfer, not a resource cost, and the scheme's mobility effect has no estimate in the evidence library, since the PC's licensing simulation leaves mutual recognition out. The Government's estimate of $2.4 billion over ten years could not be traced to its method.",
      jurisdictions: ["CTH"],
      proposalType: "reform",
      startYear: 2021,
      phaseInYears: 0,
      durationYears: 10,
      priceBase: "2025-26",
      source: PC_MR,
    },
    scope: {
      industries: groups.map((g) => ({ anzsic: g.industry, exposure: 1, role: "direct", note: rows("abs_anzsic.codes").find((r) => r.code === g.industry)?.name })),
      sizeBands: ["nonEmploying", "1-4", "5-19", "20-199", "200+"],
      entityTypes: ["private"],
    },
    burden: {
      id: "worked-amr-burden",
      title: "Automatic mutual recognition: second registrations no longer needed",
      description:
        "The PC's aggregate annual cost of holding a licence in more than one jurisdiction, for the three occupation groups with an estimate (about 5% of licence holders in the eastern mainland states). The cost is the second licences' fees, so it is tagged as a government fee and left out of the RBE (RBM pp. 2, 4); the time to apply is not estimated by the source.",
      proposalType: "reform",
      durationYears: 10,
      jurisdiction: "commonwealthOnly",
      baseline: "statusQuo",
      populations: groups.map((g) => ({ id: g.id, label: g.label, group: "business", industry: g.industry, count: 1, source: cost, provenance: { count: { origin: "entered", note: "One aggregate: the source gives the group's total cost, not the number of holders" } } })),
      options: [
        {
          id: "amr",
          name: "Automatic mutual recognition",
          obligations: [
            {
              id: "second-registration",
              name: "Registration in a second jurisdiction",
              category: "administrative",
              tags: ["governmentFee"],
              levers: ["removeDuplication"],
              current: { costType: "purchase", timing: { type: "ongoing" }, lines: groups.map((g) => ({ populationId: g.id, purchase: { unitCost: g.cost, timesPerYear: 1 } })) },
              reformed: null,
              provenance: Object.fromEntries(groups.map((g) => [`current.lines.${g.id}.purchase.unitCost`, sourced("Aggregate annual cost of holding multiple licences, COAG 2013 estimates as reported by the PC", cost)])),
            },
          ],
        },
      ],
    },
    levers: {
      labour: {
        licensing: { occupations: ["381231", "363131", "363231", "622232"], stringencyChange: 0, mutualRecognition: true },
        provenance: {
          "licensing.stringencyChange": sourced("Mutual recognition leaves each jurisdiction's licensing standard unchanged; the PC's licensing simulation, the source of the C8 elasticity, leaves mutual recognition out of scope", src("Productivity Commission (2024), National Competition Policy: modelling proposed reforms, p. 128 (PDF p. 134)", PC_NCP.url, "November 2024")),
          "licensing.occupations": derived("OSCA 2024: Electrician (General), Plumber (General), Gasfitter, Real Estate Agent", ABS_OSCA),
        },
      },
    },
  });
}

// ---- 3. Mandatory climate-related financial disclosure (Treasury Policy Impact Analysis, 2023) ---------------------

const CRFD_URL = "https://treasury.gov.au/sites/default/files/2024-01/c2024-466491-pia.pdf";
const pia = (loc: string) => src(`Treasury, Policy Impact Analysis: Climate-related financial disclosures (September 2023), ${loc}`, CRFD_URL, "September 2023");

function climate() {
  // Per-entity costs, PIA Tables 7, 10 and 13 (pp. 23–27): transitional (one-off) and ongoing.
  const full = { transitional: 1306847, ongoing: 714032 }; // Options 1 and 1a (reasonable assurance)
  const limited = { transitional: 1306847, ongoing: 681154 }; // Option 1b (limited assurance)
  const group3 = { transitional: 45050, ongoing: 36950 };
  const pops = [
    { id: "group-1", label: "Group 1 entities (two of: revenue $500m+, assets $1bn+, 500+ employees)", count: 729 },
    { id: "group-2", label: "Group 2 entities (two of: revenue $200m+, assets $500m+, 250+ employees)", count: 755 },
    { id: "nger", label: "NGER reporters below the publication threshold", count: 362 },
    { id: "group-3-material", label: "Group 3 entities with material climate risks", count: 228 },
    { id: "group-3", label: "Group 3 entities (two of: revenue $50m+, assets $25m+, 100+ employees)", count: 4555 },
    { id: "status-quo", label: "Entities disclosing voluntarily under the TCFD (aggregate: 343 now, 777 more over ten years)", count: 1 },
  ];
  // Treasury's discounts: Group 2's transitional cost by 20%, NGER reporters' costs by 30% (p. 24).
  const per = (pop: string, c: { transitional: number; ongoing: number }) =>
    pop === "group-2" ? { transitional: c.transitional * 0.8, ongoing: c.ongoing } : pop === "nger" ? { transitional: c.transitional * 0.7, ongoing: c.ongoing * 0.7 } : c;
  const option = (id: string, name: string, description: string, groups: string[], c: typeof full) => {
    const cost = (p: string) => (p.startsWith("group-3") ? group3 : per(p, c));
    return {
      id,
      name,
      description,
      obligations: [
        {
          id: "disclosure",
          name: "Climate-related financial disclosure: ongoing reporting and assurance",
          category: "administrative",
          current: { costType: "purchase", timing: { type: "ongoing" }, lines: [{ populationId: "status-quo", purchase: { unitCost: 249990000, timesPerYear: 1 }, note: "Treasury's status quo: $20.34m of amortised transitional cost plus $229.65m ongoing a year (PIA Table 3, p. 19)" }] },
          reformed: { costType: "purchase", timing: { type: "ongoing" }, lines: groups.map((p) => ({ populationId: p, purchase: { unitCost: r2(cost(p).ongoing), timesPerYear: 1 } })) },
        },
      ],
      transitions: [
        {
          id: "transition",
          name: "Familiarisation, legal review, systems, scenario and scope 3 build, first report and assurance",
          category: "administrative",
          reformed: { costType: "purchase", timing: { type: "oneOff", year: 1 }, lines: groups.map((p) => ({ populationId: p, purchase: { unitCost: r2(cost(p).transitional), timesPerYear: 1 } })) },
        },
      ],
    };
  };
  write("worked-climate-disclosure.brief.json", {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "worked-climate-disclosure",
    meta: {
      title: "Mandatory climate-related financial disclosure (2024)",
      summary:
        "Worked example (P6): a new reporting obligation with size thresholds. Large entities report climate-related risks under Australian sustainability standards, phased in by size: Group 1 from 2024-25, Group 2 from 2026-27 and Group 3 from 2027-28. The burden proposal rebuilds Treasury's regulatory burden estimate for Options 1, 1a and 1b (the recommended option, $1,150.2 million a year) from the Policy Impact Analysis's per-entity costs and entity counts; the thresholds screen the employee tests of each group.",
      jurisdictions: ["CTH"],
      proposalType: "new",
      startYear: 2024,
      phaseInYears: 3,
      durationYears: 10,
      priceBase: "2025-26",
      source: pia("the regulatory burden estimate, pp. 16–29"),
      provenance: { phaseInYears: sourced("Group 1 reports from 2024-25, Group 2 from 2026-27 and Group 3 from 2027-28 (PIA p. 9): full coverage in the fourth year", pia("p. 9")) },
    },
    scope: {
      industries: DIVISIONS.map((d) => ({ anzsic: d, exposure: 1, role: "direct", note: divisionName.get(d) })),
      sizeBands: ["20-199", "200+"],
      entityTypes: ["private"],
    },
    burden: {
      id: "worked-climate-disclosure-burden",
      title: "Climate-related financial disclosure: Treasury's regulatory burden estimate (Policy Impact Analysis, 2023)",
      description:
        "Per-entity costs from PIA Tables 7, 10 and 13, entity counts from pp. 20 and 26, Treasury's discounts (Group 2's transitional cost by 20%, NGER reporters' costs by 30%) and the status quo of voluntary TCFD reporting (Table 3). Transitional costs are one-off, so the RBE spreads them over ten years, as Treasury amortised them. Group 3 under Options 1a and 1b uses Table 12's 228 entities (the text says 278).",
      proposalType: "new",
      durationYears: 10,
      jurisdiction: "commonwealthOnly",
      baseline: "statusQuo",
      populations: pops.map((p) => ({ id: p.id, label: p.label, group: "business", cohort: p.id === "status-quo" ? "all" : "large", count: p.count, source: pia(p.id === "status-quo" ? "Table 3 (p. 19)" : "pp. 20 and 26") })),
      options: [
        option("option-1b", "Option 1b: narrower coverage, limited assurance (recommended)", "Groups 1 and 2, NGER reporters, and Group 3 entities only where their climate risks are material; limited assurance. Treasury: $1,400.19m a year against the status quo's $249.99m (PIA Table 14).", ["group-1", "group-2", "nger", "group-3-material"], limited),
        option("option-1", "Option 1: the consultation design", "All Group 1, 2 and 3 entities and NGER reporters; reasonable assurance. Treasury: $1,636.69m a year (PIA Table 14).", ["group-1", "group-2", "nger", "group-3"], full),
        option("option-1a", "Option 1a: narrower coverage", "As Option 1, with Group 3 reporting only where climate risks are material. Treasury: $1,457.30m a year (PIA Table 14).", ["group-1", "group-2", "nger", "group-3-material"], full),
      ],
    },
    levers: {
      thresholds: [
        { id: "group-1", metric: "employees", change: "introduce", value: 500, costAbovePerYearDollars: limited.ongoing, design: "cliff" },
        { id: "group-2", metric: "employees", change: "introduce", value: 250, costAbovePerYearDollars: limited.ongoing, design: "cliff" },
        { id: "group-3", metric: "employees", change: "introduce", value: 100, costAbovePerYearDollars: group3.ongoing, design: "cliff" },
      ],
    },
  });
}

// ---- 4. EPBC Act reform: the Streamlined Assessment Pathway (2025) --------------------------------------------------

const EPBC = src("DCCEEW, Environmental Law Reform: Certification of Final Report of the EPBC Act Review, Addendum to the Final Report (24 September 2025), Table 1 and Methodology, pp. 1–2", "https://oia.pmc.gov.au/sites/default/files/posts/2025/10/Addendum.pdf", "September 2025");

export const EPBC_DAYS = { low: 20, medium: 141, high: 288 } as const;

function epbc() {
  // DCCEEW: saving = average project value × 7% × days saved ÷ 365 × referrals a year, so the value of the projects
  // assessed each year is the business saving ÷ (7% × days ÷ 365): $441m at 20 days.
  const projectValue = 441 / (0.07 * (EPBC_DAYS.low / 365)); // $ million a year
  const capital = rows("abs_asna.capital");
  const fy = capital.map((r) => String(r.fy)).sort().at(-1)!;
  const market = DIVISIONS.filter((d) => !"OPQ".includes(d));
  const gfcf = capital.filter((r) => r.fy === fy && market.includes(String(r.anzsic))).reduce((s, r) => s + Number(r.gfcf_current), 0);
  const exposure = r4(projectValue / gfcf);
  const note = `Share of investment that passes through the EPBC assessment pathways: DCCEEW's implied value of projects assessed a year, $${Math.round(projectValue).toLocaleString("en-AU")} million ($441m ÷ (7% × 20/365)), over market-sector gross fixed capital formation in ${fy}, $${Math.round(gfcf).toLocaleString("en-AU")} million (ASNA, divisions other than O, P and Q). The same share in every division: DCCEEW does not publish its sectors' values`;
  write("worked-epbc-approvals.brief.json", {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "worked-epbc-approvals",
    meta: {
      title: "EPBC Act reform: the Streamlined Assessment Pathway (2025)",
      summary:
        "Worked example (P6): an approval-time cut for investment. The Environment Protection Reform Bill 2025 adds a Streamlined Assessment Pathway that shortens the statutory assessment and approval period for controlled actions by at least 20 days (DCCEEW's low scenario; 141 and 288 days in its medium and high scenarios, if other reforms cut requests for more information). The tool costs it through C2: the delay raises the user cost of the investment that needs approval. DCCEEW's own estimate is a reduction in delay costs of $445 million a year (low), $3,045 million (medium) and $6,914 million (high).",
      jurisdictions: ["CTH"],
      proposalType: "reform",
      startYear: 2026,
      phaseInYears: 0,
      durationYears: 10,
      priceBase: "2025-26",
      source: EPBC,
      provenance: { startYear: { origin: "entered", note: "Assumed: the addendum gives no commencement date" } },
    },
    scope: {
      industries: market.map((d) => ({ anzsic: d, exposure, role: "direct", note: divisionName.get(d) })),
      sizeBands: ["nonEmploying", "1-4", "5-19", "20-199", "200+"],
      entityTypes: ["private"],
      provenance: Object.fromEntries(market.map((_, i) => [`industries.${i}.exposure`, derived(note, ABS_ASNA)])),
    },
    levers: {
      capital: {
        investmentApprovalDelayChangeMonths: r4((-EPBC_DAYS.low * 12) / 365),
        provenance: { investmentApprovalDelayChangeMonths: sourced("At least 20 days off the 70-day statutory timeframe of the existing pathways (DCCEEW's low scenario), in months (× 12/365)", EPBC) },
      },
    },
  });
}

// ---- 5. Victoria's payroll tax-free threshold, $700,000 to $1 million (2023-24 Budget) ---------------------------

const VIC_BP3 = src("Victorian Budget 2023-24, Budget Paper No. 3: Service Delivery, Table 1.27 and p. 114", "https://s3.ap-southeast-2.amazonaws.com/budgetfiles202324.budget.vic.gov.au/2023-24+State+Budget+-+Service+Delivery.pdf", "May 2023");
const VIC_BP5 = src("Victorian Budget 2023-24, Budget Paper No. 5: Statement of Finances, chapter 4 (payroll tax)", "https://s3.ap-southeast-2.amazonaws.com/budgetfiles202324.budget.vic.gov.au/2023-24+State+Budget+-+Statement+of+Finances.pdf", "May 2023");

function vicPayroll() {
  // Victoria's share of each division's employing businesses at June 2025 (CABEE by state, Jul 2021 to Jun 2025 release).
  const csv = gunzipSync(readFileSync(join(repo, "data", "processed", "abs_cabee", "cabee_class_state_fy.csv.gz"))).toString("utf8").split("\n");
  const head = csv[0]!.split(",");
  const at = (k: string) => head.indexOf(k);
  const division = new Map(rows("abs_anzsic.codes").map((r) => [String(r.code), String(r.division)]));
  const lastFy = csv.slice(1).reduce((m, l) => (l ? Math.max(m, Number(l.split(",")[at("fy")])) : m), 0);
  const tally = new Map<string, { vic: number; all: number; release: string }>();
  for (const l of csv.slice(1)) {
    if (!l) continue;
    const c = l.split(",");
    if (Number(c[at("fy")]) !== lastFy || c[at("measure")] !== "end" || !["1-19", "20-199", "200+"].includes(c[at("band")]!)) continue;
    const d = division.get(c[at("anzsic")]!);
    if (!d) continue;
    const t = tally.get(d) ?? { vic: 0, all: 0, release: c[at("release")]! };
    t.all += Number(c[at("value")]);
    if (c[at("state")] === "VIC") t.vic += Number(c[at("value")]);
    tally.set(d, t);
  }
  const release = [...tally.values()][0]!.release;
  write("worked-vic-payroll-threshold.brief.json", {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "worked-vic-payroll-threshold",
    meta: {
      title: "Victoria's payroll tax-free threshold: $700,000 to $1 million (2023-24 Budget)",
      summary:
        "Worked example (P6): a payroll-tax threshold change. The tax-free threshold rose from $700,000 to $900,000 on 1 July 2024 and to $1 million on 1 July 2025; the threshold is phased out for wages above $3 million (by $1 for every $2) and is nil above $5 million. The rate is 4.85% (metropolitan). Around 6,000 businesses stop paying and more than 26,000 benefit. The Budget's revenue effect, net of the phase-out: +$20.3 million in 2024-25, −$43.6 million in 2025-26 and −$38.7 million in 2026-27.",
      jurisdictions: ["VIC"],
      proposalType: "reform",
      startYear: 2024,
      phaseInYears: 1,
      durationYears: 10,
      priceBase: "2025-26",
      source: VIC_BP3,
      provenance: { phaseInYears: sourced("Two steps: $900,000 from 1 July 2024, $1 million from 1 July 2025", VIC_BP3) },
    },
    scope: {
      industries: DIVISIONS.map((d) => {
        const t = tally.get(d)!;
        return { anzsic: d, exposure: r4(t.vic / t.all), role: "direct", note: divisionName.get(d) };
      }),
      sizeBands: ["1-4", "5-19", "20-199", "200+"],
      entityTypes: ["private"],
      states: ["VIC"],
      provenance: Object.fromEntries(
        DIVISIONS.map((d, i) => {
          const t = tally.get(d)!;
          return [`industries.${i}.exposure`, derived(`Victoria's share of the division's employing businesses at June ${lastFy}: ${t.vic.toLocaleString("en-AU")} of ${t.all.toLocaleString("en-AU")} (ABS CABEE by state, ${release})`, ABS_CABEE_STATE)];
        }),
      ),
    },
    levers: {
      thresholds: [
        {
          id: "tax-free-threshold",
          metric: "payroll",
          change: "move",
          previousValue: 700000,
          value: 1000000,
          costAbovePerYearDollars: { low: 0, high: 14550 },
          design: "taper",
          provenance: {
            costAbovePerYearDollars: sourced("Payroll tax at 4.85% on the first $300,000 of wages above the threshold: $0 just above it, up to $14,550 (the saving the Budget gives for businesses that benefit)", VIC_BP5),
          },
        },
        {
          id: "threshold-phase-out",
          metric: "payroll",
          change: "introduce",
          value: 3000000,
          costAbovePerYearDollars: { low: 0, high: 48500 },
          design: "taper",
          provenance: { costAbovePerYearDollars: sourced("The $1 million deduction is withdrawn by $1 for every $2 of wages above $3 million: from $0 at $3 million to $48,500 of extra tax at $5 million (4.85% × $1 million)", VIC_BP3) },
        },
      ],
    },
  });
}

noncompete();
amr();
climate();
epbc();
vicPayroll();
