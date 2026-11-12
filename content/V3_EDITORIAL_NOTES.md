# Website v3: content boundaries and maintenance

Release date: 12 November 2026.

## Source-derived records
The supplied six-page academic CV is the source for appointments, education, supervision, awards and four funded project records. Only the 23 selected journal entries actually supplied are exported. Manuscripts under review, pending grant applications and unverified citation metrics are excluded from the public CV.

Academic profile URLs were checked against the university's directory: https://unis.ahievran.edu.tr/akademisyen-detay/calismalar/huseyin.ates . Google Scholar profile ID: LytA1bkAAAAJ. External profiles remain independently maintained.

## Editorial and teaching additions
Research overview diagrams and the interactive framework are conceptual reading guides, not experimental protocols, path models or claimed empirical findings. The timeline is a selective editorial chronology. Prototypes are AI-assisted site teaching material, not validated measures or original intervention materials from a paper.

The six English/Turkish guides and synthetic example have a limited classroom-use permission with source acknowledgement, retained prototype notices and an indication of changes. No blanket Creative Commons or open-source licence has been applied to the website, CV, papers, portraits or third-party content. Public republication and commercial distribution require separate permission.

## Known omissions
No portrait or project photograph has been manufactured or republished. Additional verified team biography, complete bibliography, actual study protocols, up-to-date project phases and permitted seminar recordings have not been supplied. Domain registration, DNS changes, Search Console verification and changes to the owner's external academic accounts have not been performed.

Article citation metadata has been added to three editorial study briefs. This does not establish Google Scholar indexing: these pages are not the complete author-written abstracts or article texts.

## Testing scope
Local browser tests covered 36 HTML pages at 1440 and 390 pixel widths, project filtering, publication search/year filtering, resource language switching, framework controls, mobile-menu Escape handling and the keyboard skip link. No horizontal page overflow or console errors were found in those tested layouts. All seven generated PDF/DOCX documents were rendered and visually inspected at two pages each.

Automated checks are not full WCAG 2.2 certification, an independent screen-reader audit, PDF/UA conformance or validation of educational effectiveness. See accessibility.html in the generated site.

## Build order
1. python scripts/build_site.py
2. python scripts/build_professional_docs.py
3. python scripts/build_v3.py
4. python scripts/verify_v3.py
5. python scripts/verify_site.py

The last step writes checksums into deployment.json. After publication, python scripts/verify_site.py --live compares every live file with those checksums. Do not edit generated _site files as permanent source changes.
