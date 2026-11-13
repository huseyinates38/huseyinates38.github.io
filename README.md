# Hüseyin Ateş — Academic Research Website

Website: https://huseyinates38.github.io/

## Editorial release 4.4 — bilingual research team and affiliation directory

Research collaborators and editorial connections appear above current graduate researchers and alumni. The current record separates two other supported projects and one completed BAP project, seven submitted/planned/non-funded proposal records, an ongoing Türkiye–Colombia study and two distinct editorial initiatives.

**Important correction:** TÜBİTAK 3501 is a proposal without a funding award. It is not included in supported research or the funded-project section of the public CV. ETHE is a collection proposal in development, not an open call or a confirmed Editorial Board appointment. TÜBİTAK 2221 is planned; the separate 2219 proposal with Naomi Winstone is submitted.

The public CV now has three pages in PDF and DOCX. Existing teaching prototypes, citation exports and interactive resources are retained. The 23 listed publications remain a selection, not a complete career bibliography.

## Build the current release

Use Python 3.12, Linux fonts-dejavu-core and the pinned requirements. Font files are not distributed as website assets.

```sh
python -m pip install -r requirements-site.txt -r requirements-browser.txt
python -m playwright install --with-deps chromium
python scripts/release_editorial.py
python scripts/build_bilingual.py
python scripts/build_team_directory.py
python scripts/verify_bilingual.py
python tests/bilingual_browser.py --offline
python scripts/verify_site.py
```

Serve `_site` for preview. **Root HTML files and earlier builders are preserved input templates, not the current deployed pages.** Do not publish them directly or run the historical build sequence alone. The release driver applies the current public editorial records, regenerates the CV, builds the new pages and updates search.

## Editing

- Current people and proposal/editorial CV section: `content/editorial-update.json`.
- Current research-team roster and reviewed institution marks: `content/team-directory.json` and `content/institution-logo-sources.json`.
- Ongoing research-relationship context: `content/ongoing-collaborations.json`.
- The 22-country / 43-institution posters are source-derived graphics. They do not establish formal institutional partnerships.
- Proposal status and public scope: `content/research-pipeline.json`.
- Proposal, editorial and ongoing-study layouts: `scripts/build_v32.py`.
- Existing publications and teaching examples: `content/expansion.json` and source templates.
- Status boundaries and source precedence: `content/EDITORIAL_STATUS.md`.

Private correspondence, journal review-status tables, manuscript-review notes and original invitation documents are not included in the repository or published files. No unaccepted guest, grant award, research result or affiliation is inferred.

## Publication and quality

Pushes to main build, validate and browser-test the site before GitHub Pages deployment. Every published file is then downloaded and checked against its release SHA256. A failing pre-deployment check leaves the previous live site intact. Monday link-health checks retain reports without changing public research content. Automated checks are not WCAG/PDF-UA certification, funding verification or confirmation of journal indexing.
