## Version 4.8

The Turkish and English homepages now use the owner-approved full-width illustrated hero, five research topics, five editorial cards, functional Tally QR, and factual counters. Vietnam-related STEM and circulatory-system VR BAP projects are both listed as completed. TÜBİTAK 2221 is a submitted application; TÜBİTAK 3501 was submitted but not funded. The build uses `scripts/apply_v48.py` after the bilingual directory/visual steps.

# Hüseyin Ateş — Academic Research Website

Website: https://huseyinates38.github.io/

## Editorial release 4.6 — bilingual academic website

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

## 4.5 research-group updates

- TÜBİTAK 226K999 official title corrected from the 28 August 2026 funding decision (English translation clearly distinguished).
- İpek Öz shown as both project researcher and 2022 MSc alumna.
- Dr. Serbay Durmaz affiliated with Adana Yüreğir Karacaoğlan Ortaokulu.
- A clickable research group form (https://tally.so/r/Eq51Jr) with QR added to People and Join pages.


## 4.6 bilingual editorial and affiliation update

- Georgios Lampropoulos: two affiliations are shown exactly as supplied — Department of Education, University of Nicosia, Cyprus, and Department of Applied Informatics, University of Macedonia, Greece. Previous reference to the University of Crete was withdrawn. A neutral UNIC text mark is used in place of an unverified official logo.
- Removed the pre-send disclaimer from the Join pages while retaining the working Tally interest-form link and QR.
- Added the accepted ICCAI 2027 oral conference contribution (paper YS1001) and separately noted the submitted, as-yet-undecided TÜBİTAK 2224-A conference participation-support application. This is not represented as a funded project, completed presentation or already published paper.
- Applied academic Turkish editing to all translated page types, reducing literal translation patterns and repeated editorial caveats. Original English research titles and citations remain unchanged.

## Visual presentation — November 2026, release 4.7

The homepage now includes an original **conceptual** illustration, linked thematic research graphics, confirmed conference/grant/resource highlights, and a visible entry point to the existing interactive feedback comparison. Research pages contain linked vector illustrations. All content is bilingual. No personal photographs, fabricated study instruments, unverified project outcomes or live-news feed are included.

The GitHub Pages workflow runs `scripts/enhance_visuals.py` **after** bilingual and team-directory generation. The illustrations are owned by this repository under `assets/visuals/`; the hero imagery is conceptual and not a photograph of an empirical research project.
