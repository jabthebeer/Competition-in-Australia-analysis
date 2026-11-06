# ABLIS API: why it helps, and what it would save

*Brief for the owner, 6 November 2026 (DECISIONS E-116, decision D3). Facts are from ABLIS's own pages and its public developer documents, read the same day; nothing here has been tested against the API, which needs a key.*

## What ABLIS is

The Australian Business Licence and Information Service is run by the Department of Industry, Science and Resources with the states and territories. In its own words, it is "a centralised information service enabling Australian businesses and business intenders to identify their licencing, compliance and regulatory requirements from all tiers of government" ([ABLIS APIs](https://ablisapi.business.gov.au/)). It covers "state, territory, local and Australian government: licences, permits, approvals, regulations, codes of practice" ([About](https://ablis.business.gov.au/about)). Its data "is curated by the jurisdictions where they keep the data updated" (API developer guide).

## Why it fits our plan

The developer guide ([Word document](https://ablisfiles.business.gov.au/info/ABLIS%20API%20Developers%20User%20Guide.docx), last updated 8 July 2022) describes data organised much as our plan is:

| In ABLIS | In our plan |
|---|---|
| **Business activities**: all of ANZSIC 2006 (Revision 2.0) levels 1–4, plus the ABS's primary activities as "level 5" (codes such as `A011101`), extra activities, and "All Businesses" | The 506 classes and 4,440 primary activities: a direct join, with almost no mapping work |
| **Services**: each a Licence, Code of Practice, Regulatory Obligation, Advisory Material or Support Service | Requirements |
| **Tier of government**: Federal, State, Local; **jurisdictions**: the Commonwealth and each state and territory | The three tiers and the state switch |
| **Geographic polygons**: local government areas (e.g. "Wollongong City Council"), resolved from postcode and suburb | Councils |
| **Business life stage**: Considering, Starting, Operating, Growing, Closing | The page's Start and Exit stages |
| **Business structure**: Company, Co-operative, Incorporated Association, Partnership, Sole Trader, Trust, Other | The legal-form key |
| **Fees**, **organisations** (the administering agency), **resources** (forms), and **illegal business activities** by jurisdiction | Fees, administering bodies, and activities banned in a state |

## What it would save

| Work in the plan | Without ABLIS | With ABLIS |
|---|---|---|
| **Linking licences and obligations to classes** (phases C and D) | For each regime in each jurisdiction (61 × 9 to start, more as new ones are found), find the licences, read their scope and match them to the 4,440 primary activities by judgement | Download the services with their activity and jurisdiction tags, which the jurisdictions have already matched. Then trace each to its law and check a sample, rather than building every match |
| **Councils** (phase E) | Search each sampled council's website and local laws by hand; all ~540 councils are out of reach | Council requirements come tagged by local government area from one source, if the API carries them (see the limits below) |
| **Completeness check** (phase F) | Only business.gov.au's industry guides to check against, and they cover some industries. No full check of the 4,048 class × state cells (506 × 8) is possible | An automatic comparison for every class and state. Only the mismatches need a person to look |
| **Stages, legal form, fees** (the page) | Worked out law by law | Already tagged on each service |

**Rough scale.** This is an illustration, not a measurement; phase B's calibration will give real times. Suppose researching the licences for one class in one state takes 10–20 minutes of in-session work:

- **Without ABLIS:** the 4,048 class × state cells come to roughly 700–1,350 hours.
- **With ABLIS:** the same step becomes a bulk download, plus checking a 5 per cent sample (about 200 cells, roughly 35–70 hours) and the mismatches.

On that assumption, the licence-mapping and completeness steps shrink by about ten to twenty times, and the council layer becomes feasible beyond a sample. The savings are smaller for laws that apply to every business (tax, employment, corporations), which ABLIS lists as "All Businesses" and which phase C handles from the Federal Register anyway.

## What it won't do

- **It is guidance, not law.** Each service still has to be traced to the Act or regulation behind it, with a register ID, before it goes on the page.
- **Council coverage is uncertain.** The developer guide says the API's services are "at the State, and Australian Government level", while the website lists council approvals. Whether local requirements come through the API is the first thing to test once the key arrives.
- **Use and copyright limits.** The API terms say "You must not use the APIs for commercial activities". ABLIS material may be reproduced only unaltered, for non-commercial use, with its source acknowledged ([Copyright](https://ablis.business.gov.au/copyright)). So we use ABLIS to build and check our links and cite it, but we don't republish its text on the site.
- **Quality is not known.** Each jurisdiction keeps its own records up to date, and the developer guide dates from 2022. Phase F reports where ABLIS and the registers disagree, rather than taking ABLIS as right.

## Registering

The form at <https://ablis.business.gov.au/apiregistration> asks for your name, email, organisation and a business case of up to 2,500 characters. You also agree to the terms and confirm you won't use the APIs commercially. Production and test (UAT) access are applied for separately; production is the one we need. When the key arrives, I'll ask for it through a secure form, so it is stored as a secret on this environment and never pasted in chat.

A business case you could paste (about 1,050 characters):

> ALICIA (Australian Legislation Impact on Competition Industry Analysis) is a non-commercial research project on competition and business dynamism in Australia. We are mapping the Australian, state and territory, and local government requirements that apply to businesses in each ANZSIC 2006 class, to show how regulation affects businesses as they start, grow and close, and where requirements differ between states and councils. We would use the ABLIS APIs, read-only, to (1) retrieve the services (licences, codes of practice and regulatory obligations) linked to each ANZSIC business activity and jurisdiction, with their tier of government, business life stage and administering organisation; (2) compare our own mapping, built from the legislation registers, with ABLIS to find requirements we have missed; and (3) cite ABLIS as a source. We will not use the APIs for commercial activities, will not reproduce ABLIS material in altered form, and will acknowledge ABLIS and the jurisdictions. Queries will run in small, rate-limited batches.

## Until the key arrives

Phases A to E go ahead without it, and phase F waits. Phase B designs the schema so ABLIS's activity codes, service IDs, tiers and life stages drop straight in, so nothing has to be redone when the key comes.

## Update, 6 November 2026: what the public site shows

Calibration batch 5 found that ABLIS's public website answers two of the open questions without the API:

- **Councils are covered.** Every capital-city council has outdoor dining, busking and filming permits listed, among them Melbourne, Perth, Adelaide and Hobart, whose own websites refuse automated requests.
- **Each listing gives the legal basis.** A service page states when the permit is needed, its type, its current fees, the Act and the local law or by-law behind it, and the administering agency. For example, Melbourne's outdoor dining permit is under the "Local Government Act 2020 Victoria" and the "Activities Local Law 2024".
- **The scale is known.** The site's sitemap (robots.txt allows it) lists 30,663 service pages:

  | Level | Service pages |
  |---|---|
  | WA | 8,754 |
  | NSW | 7,617 |
  | Victoria | 5,022 |
  | Queensland | 2,903 |
  | SA | 2,582 |
  | Tasmania | 1,846 |
  | Australian Government | 775 |
  | NT | 666 |
  | ACT | 498 |

  This is a first measure of the size of the licence and obligation layer.

The API remains the right route for bulk use. The public pages carry no ANZSIC codes, and ABLIS's copyright allows only unaltered, non-commercial reproduction. So the calibration read only the pages it needed (19 council pages in batch 5 and 40 state pages in batch 4f) and quotes just the first sentence of each description, with attribution.
