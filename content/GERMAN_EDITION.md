# German edition (DE)

The owner requested a German edition of the existing academic website. `scripts/build_german.py` is an additive FINAL build stage after all EN/TR editorial, roster and assistant passes. It produces 70 German counterparts under `_site/de/`, links all three locales, updates canonical/hreflang metadata and the sitemap, and rebuilds German search and assistant records. Do not edit generated `_site` files.

## Translation source

`content/german/*.tsv` contains reviewed English-source/German-target pairs, separated by one tab. Text is matched after whitespace normalisation. Proper names, original publication titles, identifiers, DOI strings and code examples may deliberately remain unchanged. Conflicting translations fail the build; identical repeated entries are harmless. Any new source prose without a German translation also fails, rather than silently publishing English as German. Export the combined catalog with `python scripts/build_german.py --export-catalog /tmp/translations-de.json`.

Translate new or changed English text in this catalog, review project statuses and source dates, and rerun the final German builder and tests. The expected 70-page coverage is explicit: a change in source-page count requires a corresponding coverage review.

## Scope and preserved records

All 70 HTML pages, navigation, accessibility labels, German search and filter messages are localised. Research article titles/citations and existing English/Turkish downloadable files remain in their source language, with clear German link labels. Existing poster graphics and decorative artwork are retained; the surrounding readable HTML and image alternatives are translated. Academic ranks are not converted into an invented German qualification.

The localisation date is 16 November 2026. It is not a new CV-content review or funding-status verification. Existing application states, documented roles and review dates remain unchanged. In particular, Naomi Winstone remains the proposed academic host for the 2219 application, with no manuscript collaboration attributed to her. The 3501 and AÜB rosters contain seven and four member cards respectively; shared memberships and Ahmet Sami Konca's AÜB membership are retained.

## Interactive behaviour

German-only copies of shared controls preserve the EN/TR behaviour. Search supports German terms and accent-insensitive matching. The EN/TR/DE switch opens the corresponding page and preserves section/filter fragments without storing a language preference.

The German website guide uses translated public facts and deterministic answer rules; it is not a newly activated generative model. No provider credentials, new account or billing are introduced. The German cloud endpoint stays empty unless the service configuration explicitly includes `de` in `supported_languages`; actual German model responses require a separate evaluation before enabling it. The existing exclusion of `person-tugce-unsal.html` from discovery is preserved.

## Validation

Run `python tests/german_browser.py` after the final builder, then the normal `scripts/verify_site.py` and live-file checks. The German test validates all 210 HTML pages and links, all 70 DE layouts at 390/768/1440 pixels, controls, source-language downloads, date preservation, project membership, Naomi's record, search, German guide replies and counterpart navigation. `--offline` inlines assets only for restricted local previews; CI uses actual local HTTP navigation. These checks are not an independent accessibility certification or an LLM-quality benchmark.
