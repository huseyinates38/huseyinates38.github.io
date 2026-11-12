# Hüseyin Ateş — Academic Research Website

Live site: https://huseyinates38.github.io/

## Website 3.1: usable, searchable and maintained

37 HTML pages (including search and the custom error page), 33 downloadable files, nine individual collaborator/student profiles, four project records, three research briefs, a research timeline and bilingual teaching examples.

The public CV is available as PDF and DOCX. Six English/Turkish teaching guides have PDF and DOCX versions. The citation library contains 23 selected CV-supplied publications; it is not represented as the complete career record. Teaching examples remain prototypes, not validated instruments.

### Maintenance release

- Sitewide local search across pages, individual publication links and existing PDF/DOCX downloads.
- Turkish-accent-insensitive publication search and AI/GenAI/VR/AR/SRL aliases.
- Publication filters and language choices retained in shareable URL fragments, without cookies or browser storage.
- Narrow-phone DOI reflow, keyboard-accessible project tables and descriptive download labels.
- Consistent resource version labels and removal of obsolete external font loading.
- Rendered Chromium regression tests before publication, followed by exact live-file checksums.

No unprovided portrait, research finding, project membership or grant outcome has been invented. Custom-domain registration and Search Console ownership verification remain outside this release.

## Build

Use Python 3.12 and Linux fonts-dejavu-core. Font files are build dependencies and are not distributed as site assets.

```sh
python -m pip install -r requirements-site.txt -r requirements-browser.txt
python -m playwright install --with-deps chromium
python scripts/build_site.py
python scripts/build_professional_docs.py
python scripts/build_v3.py
python scripts/build_v31.py
python scripts/verify_v31.py
python tests/browser_smoke.py
python scripts/verify_site.py
```

Serve `_site` for local preview. Root HTML files are source templates, not the deployed output. Rebuild from the first step rather than repeatedly applying enrichment scripts to already-enriched output.

## Editing

- Base research and resource records: `content/expansion.json` and root HTML templates.
- Documents: `scripts/build_professional_docs.py`.
- Project register, identity and citation metadata: `scripts/build_v3.py`.
- Search and usability refinement: `scripts/build_v31.py`, `assets/v31.js`, `assets/v31.css`.
- Editorial checks and next-update criteria: `content/MAINTENANCE.md` and `content/V3_EDITORIAL_NOTES.md`.

## Publication and quality

Pushes to main build, validate and test the site before GitHub Pages deployment. After deployment, all live files must return HTTP 200 and match their release SHA256. The `website-browser-quality` workflow artifact retains browser and structural reports. A failing pre-deployment test leaves the previous live site intact.

Weekly Website Link Health continues on Mondays without changing site content. Restricted HTTP responses and timeouts are inconclusive, not proof that a publication is invalid. Browser and structural tests are not independent WCAG/PDF-UA certification or academic fact verification.
