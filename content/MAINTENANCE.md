# Maintenance instead of feature growth

## Release 3.1 — 12 November 2026

This is a usability patch, not a new academic-content release. It retains the 36 previous pages and adds one functional site-search page. The 33 downloads and their academic content are preserved. Search indexes existing HTML, the 23 supplied journal entries and the existing public CV/teaching documents.

Changes: Turkish-accent-insensitive publication and site search; AI/GenAI/VR/AR/SRL aliases; shareable filters and language selections in URL fragments; narrower-phone DOI wrapping; file type/size descriptions; keyboard access to horizontal project tables; consistent resource labels; removal of an obsolete Google Fonts import. No analytics, live AI service, application form, cookies or persistent browser storage was added.

## Editing and publishing

Always rebuild from source in this order:

1. `python scripts/build_site.py`
2. `python scripts/build_professional_docs.py`
3. `python scripts/build_v3.py`
4. `python scripts/build_v31.py`
5. `python scripts/verify_v31.py`
6. `python tests/browser_smoke.py`
7. `python scripts/verify_site.py`

Pushes to main execute this pipeline and publish only after successful checks. The final live test compares every generated file with its deployed SHA256. Reports are available in the workflow's website-browser-quality artifact. A build failure leaves the previous deployment intact.

## What merits the next content update

- Owner-approved portraits and photographs with appropriate permissions.
- Actual project status, personnel assignments, sharable protocols and measured results.
- Verified additional publication records; do not call the selected list a complete bibliography.
- Confirmed talks or releases with supporting links or materials.

Do not generate missing findings, funded positions, team assignments or photographs merely to fill space. Do not change resource version 1.1 unless the teaching documents themselves change. The separate Feedback Explorer version is independent of the downloadable packs.

## Review cadence

At a real research milestone, update the corresponding project/publication page and its date. Check the existing weekly link-health reports; distinguish blocked requests from broken links. Review team status at the start of a new academic term. A working site does not need new pages every week.

Automated browser checks are not WCAG certification, academic peer review, privacy-law certification or search-engine indexing confirmation. Domain purchase and Search Console ownership verification still require the relevant account and ownership actions.
