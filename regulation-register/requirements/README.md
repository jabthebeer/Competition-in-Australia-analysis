# Requirements: how to add them

A requirement is one obligation a law places on a business, in one jurisdiction: register, hold a licence, get an approval, notify, pay, report, keep records, insure, or meet a standard. Each one is a JSON file here, checked by `alicia validate` against the model in `alicia/src/alicia/register/requirements.py` (JSON schema: `../schema/requirement.schema.json`). The coding rules are in [`docs/methods_legislation_links.md`](../../docs/methods_legislation_links.md).

Every requirement added here appears on the website's **Industry lens (beta)** at the next site build, under the industries its reach covers. No code change is needed.

## Where files go

| Tier | Folder | id |
|---|---|---|
| Commonwealth | `cth/` | `cth-<family>` |
| State or territory | `nsw/`, `vic/`, `qld/`, `sa/`, `wa/`, `tas/`, `nt/`, `act/` | `<state>-<family>`, e.g. `qld-food-business-registration` |
| Council | `local/<ABS LGA code>/` | `lga-<code>-council-<family>` |

The `family` is the same obligation across jurisdictions (e.g. `food-business-registration`). It drives the state switch, and a family has at most one requirement per place.

## Steps

1. **Find the obligation.** Sources, in order of preference:
   - the law itself (phases C and D screen each register: methods rule 10);
   - the regulator's guidance;
   - an [ABLIS](https://ablis.business.gov.au) listing, which names the Act and the agency.

   Read ABLIS pages a few at a time, never in bulk. Quote at most the first sentence of a description, unaltered and attributed. Bulk use waits for the API key ([brief](../../docs/ablis_brief.md)).
2. **Read the law's current text** with `alicia/scripts/law_sources.py`. Each source is named by a short spec:

   | Jurisdiction | Spec | Checked as |
   |---|---|---|
   | Commonwealth | `frl:<title id>` (e.g. `frl:C2004A00446`) | `register-text` |
   | NSW, SA | `corpus:<version id>` (find it with `law_sources.py index "<title>"`) | `corpus-copy` |
   | Queensland, Tasmania | `qld:<act id>`, `tas:<act id>` | `register-text` |
   | WA | `wa:<law_aNNN>` | `document` |
   | ACT | `act:<A id>` (e.g. `act:2001-66`) | `document` |
   | NT | `nt:<NAME-IN-URL>` | `document` |
   | Victoria and any web page | `page:<url>` (the Victorian register disallows its documents; use the regulator) | `web-page` |

   ```bash
   cd alicia
   uv run python scripts/law_sources.py look qld:act-2006-003 "must not carry on" "licence"
   uv run python scripts/law_sources.py ablis https://ablis.business.gov.au/service/<state>/<slug>/<id>
   ```

   In a batch script, `clip(spec, start, end, locator, title, publisher)` returns a ready `sources` entry. Its quote is copied from the text, never typed.
3. **Write the file.** Copy a similar requirement (for example `nsw/nsw-home-warranty-insurance.json`) and change it. The fields that matter most:
   - `laws`: each with a `register_id` or `register_url`. A state citing a national law hosted by another state sets `applied: true`.
   - `sources`: the obligation in the law's own words.
   - `triggers`: when it applies. A threshold needs `test`, `value`, `unit`, `as_at` and its own quoted source. Look for values in the regulations and determinations, not just the Act (rule 11).
   - `reach`: which ANZSIC classes it covers (rule 4). Code it once per family across all 506 classes, from a keyword shortlist of class names, definitions and primary activities (`data/processed/anzsic/anzsic2006_classes.json`). Limit it with `activities` (the ABS's exact wording), a `condition` (`"if it sells alcohol"`), `legal_forms`, or `in_states` (Commonwealth only). Each reach quotes its basis.
   - `confidence`: high, medium or low (rule 6). A draft taken from an ABLIS listing alone is medium at most (rule 5a).
   - `assessment` (required): the requirement marked against the [productivity impact framework](../../docs/productivity_framework.md), as every register item is. Mark each of the eight drivers from −2 to +2 against the same market without the requirement, with a one-line reason, and leave a driver out when the effect is small. Then name the main driver (the largest mark), the reach and the confidence. Where the register already assesses the same law, use its marks so the two agree. A small obligation with no material effect has no marks and no main driver; its summary says why.

     ```json
     "assessment": {
       "summary": "Builders need a licence, with qualifications or experience, before contracting for residential building work.",
       "marks": [
         {"driver": "entry-exit", "mark": -1, "reason": "A licence with qualification or experience tests is needed before contracting."},
         {"driver": "labour", "mark": -1, "reason": "Licensing narrows who may contract for building work."}
       ],
       "main_driver": "entry-exit",
       "reach": "sector",
       "confidence": "low",
       "assessed_on": "2026-11-07"
     }
     ```

     The Industry lens places each mark in a column by its driver ([methods](../../docs/industry_lens.md)). Where that would mislead, a mark can name its column with `"positions": ["smaller"]` (or `"entrants"`, `"dominant"`). An example is an entry-exit mark about growing past a tax threshold.
   - `records`: register items about the same law. On the lens, a requirement stands for a *setting* it names, so the two are not listed twice.
4. **Check.**

   ```bash
   cd alicia
   uv run alicia validate                              # model and framework assessment, codes, ABS activity wording, LGA codes, families
   uv run python scripts/check_requirement_quotes.py   # every quote re-found in its source
   uv run python scripts/requirement_links.py          # rebuild the class link table
   uv run pytest -q
   ```

   Then look at the page: `uv run alicia site -o ../site` and open `site/industry-lens.html#class=<code>&state=<STATE>`.
5. **Commit per batch** (a jurisdiction or a family), and update the progress table in [`docs/plan_legislation_links.md`](../../docs/plan_legislation_links.md). Log any family not found in a state as a gap in [`requirement-gaps.json`](../requirement-gaps.json) (rule 12): what was searched, and a status (not found, to draft, not applicable, blocked, not searched). When you draft a requirement for a logged gap, delete the gap; `alicia validate` checks both.

## Starting a new thread

A new session starts without this history. A short brief to paste:

> Continue the legislation register (ALICIA). Read `regulation-register/requirements/README.md`, `docs/methods_legislation_links.md` and the progress table in `docs/plan_legislation_links.md`. Next batch: **[family or jurisdiction]**. Draft requirements from the law's text with `alicia/scripts/law_sources.py`, check them (validate, quote check, links, tests), commit and push, and report what was added, what was not found, and anything that needs my decision.
