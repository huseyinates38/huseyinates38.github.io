# Academic record maintenance

## Scope and authority

The owner requested daily academic-record monitoring at 06:00 Europe/Istanbul
and publication of verified updates to this repository's existing GitHub Pages
site, in English, Turkish and German. This authorizes routine content updates,
source commits and publication through the existing validated workflow. It does
not authorize messages to collaborators, application submissions or changes to
private source documents. A ChatGPT automation manages the schedule; this file
is execution guidance, not a GitHub scheduled crawler.

Site: https://huseyinates38.github.io/  
Repository: `huseyinates38/huseyinates38.github.io`, branch `main`.

## Identity and sources

- Hüseyin Ateş, Kırşehir Ahi Evran University, Science Education.
- ORCID: https://orcid.org/0000-0003-0031-8994
- Web of Science: https://www.webofscience.com/wos/author/record/AAV-6927-2021
- Scopus: https://www.scopus.com/authid/detail.uri?authorId=57208034648
- Institutional profile: https://unis.ahievran.edu.tr/akademisyen-detay/huseyin.ates
- Publisher pages and their Crossref DOI deposits establish publication metadata.
- COST and TÜBİTAK official pages establish programme/action descriptions.
- Owner-authorized current Google Drive research records establish personal
  application progress and proposed collaborations; read only what is relevant.

**Do not use Google Scholar for searching, metadata, metrics or validation.**
Existing profile navigation is not a monitoring source. Match names using the
identifiers, affiliation and actual author records. Do not add namesakes' work.

Keep acceptance, online publication and issue dates distinct. Deduplicate DOI
records case-insensitively. Only update citations, h-index or indexing statements
from the relevant database actually read, with a measurement date. An inaccessible
Scopus or Web of Science profile is an access limit, not evidence of no change.
Do not bypass access controls or imply a blocked source was checked.

## Current baseline — 25 November 2026

The final, authoritative delta registries are:

- `content/academic-updates.json`: new publication and CA25177 membership.
- `content/visiting-2221.json`: four current visiting-researcher application plans.

These override older values for the same records in historical input templates,
translation catalogs, proposal JSON and CV source arrays. The final pass is
`scripts/apply_academic_updates.py`, after `scripts/add_1002_team.py`. Never publish
the repository-root HTML files; only the validated `_site` output is deployed.

### Publication

DOI `10.1016/j.compedu.2026.105805`, ScienceDirect PII `S0360131526002459`:
sole author Hüseyin Ateş, *Computers & Education*, volume 258, article 105805.
Crossref identifies the March 2027 issue, so the reference year is 2027.
The DOI deposit does not give a published-online date; do not infer it from the
acceptance date. The public scope summary follows the title, without unverified
sample sizes, effect estimates or superiority claims.

Metadata: https://api.crossref.org/works/10.1016/j.compedu.2026.105805

Retain previously added publications on subsequent updates. A new publication
must be appended to the reviewed record set and integrated without overwriting
this record or resetting the selected bibliography to the historical 23 entries.
Keep the original article titles in all languages. Include new years in filters,
and synchronize count labels, BibTeX, RIS, JSON exports and assistant facts.

### COST

https://www.cost.eu/actions/CA25177/ — ENDUeAI, European Network for Developing
and Evaluating the Use of GenAI in Education. Action period 5 October 2026 to
4 October 2030. The owner's CV and supplied announcement establish membership
since November 2026 in WG1 (GenAI Evaluation and Metrics) and WG6 (Pedagogy and
Critical GenAI Literacy). This is working-group membership. Do not infer a
Management Committee appointment or repeat a transient network-wide member count.

Keep ENDUeAI under `facts.projects.endueai`. The separate SciEpi-Feedback proposal
remains under `facts.projects.cost`. Generic COST assistant answers identify both
activities; explicit SciEpi or CA25177 questions select the appropriate record.

### TÜBİTAK 2221

The current four preparation dossiers are Juan Fernando Garzón Álvarez,
Mohammadreza Farrokhnia, Omid Noroozi and Seyyed Kazem Banihashem. The latest
owner-authorized tracking records supersede the earlier generic submitted status.
They establish application preparation, not submission, an award or a completed
visit. Dates remain proposed and funding-dependent. Kazem's source schedules
conflict, so only March 2027 is public until the visit timing is reconciled.

Moritz Krell and Elena Novak are not active members of these four 2027 visit
plans. Preserve their unrelated research profiles and collaborations.

## Update and verify

1. Read the current remote HEAD before editing. Compare the latest evidence with
   the registries and prior successful run. If there is no meaningful change,
   do not commit, republish, advance review dates or send a routine notification.
2. Edit public summaries and statuses only when the evidence supports them. Keep
   application preparation, submission, support decisions and completed visits
   distinct. Do not publish Drive links, raw source documents, private emails,
   signatures, identity data, submission-system IDs, budgets or candidate notes.
3. Use the exact build order in `.github/workflows/pages.yml`. Historical checks
   validate their earlier stage. The final `tests/academic_updates.py --browser`
   gate validates the final multilingual content, exports and assistant behavior.
4. For any newly affected field, update all related public surfaces: main page,
   listing/home highlights, people/proposal relationships, metadata, selected
   citation exports, public CV if affected, search, assistant facts, narrative
   corpus and the EN/TR server context. Keep the inactive cloud service inactive.
5. Run applicable checks, then create a source commit. Use the observed parent
   HEAD and a conditional fast-forward ref update; preserve concurrent edits.
   GitHub's connector supports create_tree, create_commit and update_ref with
   expected_sha. Never force unrelated changes or publish generated input templates.
6. Confirm workflow success and the live-release verification result. Report the
   actual commit and deployment outcome; a saved source change is not yet a live
   release. If blocked, retain safe completed work and state the specific limit.

Preserve the four-member 1002 roster and the removal of the redundant funding
decision section. Preserve Tuğçe Ünsal's established discovery exclusion and
Naomi Winstone's 2219 proposed-host relationship, without adding a manuscript
collaboration. Do not alter unrelated research status dates merely because a
daily check ran.

Public results should be concise and source-linked. Identify unresolved factual
conflicts, access failures and failed publication checks without converting them
into positive or negative academic outcomes.
