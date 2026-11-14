# Explicit record review metadata

`record-review.json` is the single source for the final displayed page/CV dates, per-application status-review dates, and verified school-link overrides. `scripts/apply_record_review.py` runs after the legacy layout/editorial builders; it must remain before validation and publishing in `.github/workflows/pages.yml`.

Do not edit `_site` directly. Older templates and translation snapshots may retain historical date strings or MEB root URLs; this final pass deliberately overrides only their corresponding public fields. The script is idempotent, and refreshes search records and the sitemap for pages it changes.

## Date meaning

- `about.page_updated` records an actual page edit, not a new review of every academic fact.
- `about.cv_updated` must match the content date printed inside both delivered CV editions. The CV files were not rewritten for this label correction.
- `proposal_status_reviewed` is keyed by individual proposal. The imported 2026-11-13 dates come from the existing reviewed application register; they are not new funding determinations. Change a record only after its status is actually rechecked, and retain supporting evidence.
- Do not use `today()`, the build timestamp or the deployment date to renew these fields.

## School links and contributions

Each school override includes the exact institution names, its official MEB school-domain URL, the supporting institutional page and the verification date. A school's name must never be used as a misleading label for the Ministry homepage. The displayed MEB emblem retains its existing explicit alternative text.

Membership and project-stage context are read from the reviewed team/project pages. Specific contribution descriptions are limited to the existing Kibar Gül and Naciye Somuncu Demir application records. Other members retain their documented role; technical development, measurement or analysis duties must not be inferred. No thesis identifier, thesis URL, funded appointment or new partnership is invented.

Run the normal build and checks, including `python tests/record_review_browser.py`. The latter also supports `--offline` for local, fully inlined asset checks in restricted environments. Browser coverage includes both languages, 390/768/1440-pixel widths, date fields, institutional logos and the separate 3501/AÜB groups.
