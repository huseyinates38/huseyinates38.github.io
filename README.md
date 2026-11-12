# Hüseyin Ateş — Academic Research Website

Live site: https://huseyinates38.github.io/

## Website v3

The English-language site includes 36 HTML pages (including the custom error page), bilingual teaching examples, nine individual collaborator/student profiles, four detailed project records, three selected study briefs, a research timeline, resource-use terms and an accessibility statement.

Downloads include a two-page public academic CV in PDF and DOCX, six English/Turkish teaching guides in both formats, BibTeX/RIS citation libraries for the 23 supplied journal entries and an explicitly synthetic Python/data example. The selected bibliography is not presented as the complete career record. No unprovided portrait, experimental protocol or project outcome has been invented.

## Build

Use Python 3.12 and install fonts-dejavu-core on Linux. The font files are installed in the build environment; they are not published as website assets.

```sh
python -m pip install -r requirements-site.txt
python scripts/build_site.py
python scripts/build_professional_docs.py
python scripts/build_v3.py
python scripts/verify_v3.py
python scripts/verify_site.py
```

Preview the generated `_site/index.html` locally, or serve the `_site` folder. The root HTML files are input templates; the published v3 output is generated in `_site`.

## Editing

- Base expansion records: `content/expansion.json` and root HTML templates.
- Public CV and teaching-document layouts: `scripts/build_professional_docs.py`.
- V3 project register, timeline, academic identifiers, metadata and resource links: `scripts/build_v3.py`.
- Content provenance and explicit limitations: `content/V3_EDITORIAL_NOTES.md`.

Rebuild from the first step after changes rather than repeatedly running the enrichment step over an already-enriched `_site` folder.

## Publishing and health checks

Pushes to main run `.github/workflows/pages.yml`. It builds, checks internal navigation and documents, publishes through GitHub Pages, then verifies the release manifest and SHA256 of every live file. No further Pages-setting change is required for this existing site.

`Weekly Website Link Health` runs every Monday and can also be started manually. Its downloadable `website-quality-reports` artifact includes structural and external-link reports. It does not modify or republish website content. HTTP access restrictions and timeouts are reported separately from potentially broken URLs and do not imply invalid publication records.

Automated accessibility checks are not WCAG certification. Research illustrations are conceptual, teaching resources are prototypes, and article metadata does not guarantee search-engine indexing. Custom-domain registration and Search Console ownership verification remain outside this release.
