# Hüseyin Ateş — Research, resources & people

Website: https://huseyinates38.github.io/

## Version 2 — 12 November 2026

A responsive academic website with 33 HTML pages (including a custom 404 page), 9 individual researcher/alumni/collaborator profiles, 3 bilingual teaching toolkits, a bilingual Feedback Design Explorer, 3 research briefs, research-access information and collaboration enquiry routes. The original 23-publication selection and four funded-project pages are retained.

The 11 downloads comprise six English/Turkish Markdown worksheets, three BibTeX citations, one explicitly fictional CSV example and one empty variable-dictionary template. Resource pages also offer a browser Print / Save as PDF button. No personal student data, API key, live chatbot, tracking script or external web font is included.

## Editing

- `content/expansion.json`: people, selected research briefs and bilingual toolkit content.
- `scripts/build_site.py`: shared page template, new homepage, Explorer and page composition.
- `assets/v2.css`, `assets/v2.js`: visual design and browser interactions.
- The original root HTML files retain the source records for Research, Publications, Projects, About and Contact. Their main content is cleaned and wrapped in the new common template by the builder. Root `index.html` and `team.html` are legacy records; edit the builder and JSON for the new homepage and People pages.
- Only `_site/` is deployed. Do not switch Pages to branch/root publishing: that would serve the earlier source records rather than the new website.

## Build and test locally

Requires Python 3.10 or later; no third-party Python packages are needed.

```sh
python scripts/build_site.py
python scripts/verify_site.py
python -m http.server --directory _site 8000
```

Then open http://localhost:8000/. The validator checks page titles, language, heading/ID structure, navigation and all local file/anchor links.

## Publishing

GitHub Pages uses the existing **GitHub Actions** source. A push to `main` runs `.github/workflows/pages.yml`, builds the site, validates it, deploys `_site/`, and checks every delivered file against its SHA-256 release checksum. `deployment.json` records the exact deployed commit. A failed build does not replace the previously deployed site.

## Editorial boundaries

Academic profile, supervision and project records come from the owner's supplied CV. The three research briefs use linked publisher/institutional records; limitations inferred editorially are labelled. Toolkits and fictional examples were newly prepared with AI-assisted drafting and are not represented as validated instruments or original experimental materials. No open licence is assigned without a separate decision by the owner. No recruitment offer, project personnel assignment or unpublished result has been invented.

Photos, newly approved project roles, data releases, awards, formal vacancies and field-impact stories should be added only when the owner supplies the relevant approved information.

## Türkçe bakım notu

Yeni içerikleri `content/expansion.json` dosyasından güncelleyebilirsiniz. Ana sayfa ve ortak şablon `scripts/build_site.py` içindedir. Değişiklikler `main` dalına kaydedildiğinde site otomatik oluşturulur ve yayımlanır. Öğretim örnekleri araştırma verisi veya geçerliği sınanmış ölçek olarak sunulmamalıdır. İngilizce ve Türkçe kaynak sürümlerini birlikte güncelleyin.
