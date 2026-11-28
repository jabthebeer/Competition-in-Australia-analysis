# Pilot: every council in Western Australia

*Subplan of [`plan_councils.md`](plan_councils.md), 28 November 2026. Draft: compiled by AI-assisted desk research; not yet checked.*

## Why WA

On 28 November 2026 the owner chose to pilot full council coverage in one state now (decision D4), rather than wait for the ABLIS API key or cover every council at once.

WA is the pilot state for 3 reasons:

- Every WA local law is published in the Government Gazette, and every Gazette since 1996 can be read online as text. This is the only state where we can list all of a state's council laws.
- Most WA councils use the same model wording, so one clause pattern finds the same permit in many councils.
- 3 WA sample councils (Perth, Busselton and Victoria Plains) are already done, so the method is tested.

Queensland was the other option. Its local laws database refuses automated searches, so its councils cannot be listed.

## Scope

- **Councils:** all 137 WA local governments (139 ABS areas, less the codes for no usual address and for migratory, offshore and shipping).
- **Families:** the 8 families in [`council_variation.md`](council_variation.md). In WA, caravan parks are licensed under the Caravan Parks and Camping Grounds Act 1995, so that family is one state requirement, not 137 council ones (methods rule 7).
- **Out of scope:** planning-scheme controls, fees, and local laws that bind residents rather than businesses (dogs, cats, fencing, standing orders).

## Method

1. **E-8. List the laws.** Read every Gazette from 1996 to 2026 (about 7,000 issues) and keep the text of those that publish a local law. For each council, list the local laws made, amended and repealed, and work out which are in force today. The list goes in `data/processed/legislation/wa_local_laws.csv`, with the Gazette number and page for each.
2. **E-9. Find the permits.** Search each law in force for the permit clause of each family. The model laws use set wording (for example "A person shall not without a permit … conduct a stall"), so a pattern finds most clauses. Each match is read and quoted by hand before it is filed.
3. **E-10. File the requirements.** File one requirement for each council and family found, under the methods rules for councils. Each quotes the clause and gives its Gazette link. Fill in the council-by-family table for every WA council, with "not found" where the laws in force hold no such clause.
4. **E-11. Check and report.** Check every quote against its source, rebuild the generated files, update the variation note with WA's frequencies, and run the 3 checks.

## What it adds

- About 400 to 600 council requirements, from the share of sample councils that had each family. This would roughly treble the council layer.
- The first measure of how often each version of a requirement occurs across a whole state, which the 18-council sample could not give.

## Limits

- **As made, not as amended.** The Gazette prints each law as made and each amendment separately. WA publishes no consolidated local laws. Requirements are medium confidence, as Perth's are, unless the council's own consolidated copy is read too.
- **Laws in force.** Working out what is in force depends on reading every repeal notice correctly. A missed repeal would file a law that no longer applies. A sample is checked against council websites where they can be reached.
- **Copyright.** Gazettes are State of WA copyright. The register keeps short quotes and summaries only, in line with the data legality review of 28 November 2026.
- **Effort.** Several working sessions. Each batch is committed and opened as a PR on its own.

## Progress

- **E-8 to E-10 done 28 Nov 2026 (E-368).** All 6,968 Gazettes from 1996 to 2026 read. 4,279 local laws listed for 134 councils, 328 taken as in force, and 811 permit clauses found in 109 councils. 414 requirements filed, all medium confidence. Results in [`council_variation.md`](council_variation.md).
- **E-11 still to do:**
  - check a sample against the councils' own consolidated copies, where their websites can be reached;
  - read the amendments behind 176 requirements;
  - look again at the 20 councils with no local law found, and the 10 drafts held back.

## Decision numbers

E-367 records D4 and this plan. Batches E-8 to E-11 take E-368 to E-371.
