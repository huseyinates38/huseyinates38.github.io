#!/usr/bin/env python3
"""Refresh public citation exports and CVs after the final academic update pass.

This helper deliberately does not call ``build_v3.publication_tools``: that
historical builder also rewrites study citations by their original list index.
Only the final English publication list is read here. Historical source CVs
remain untouched; the current, source-verified records are applied in memory.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from bs4 import BeautifulSoup
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from pypdf import PdfReader

import build_professional_docs as documents

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
DOWNLOADS = SITE / 'downloads'


def _text(node):
    return node.get_text(' ', strip=True) if node else ''


def _localized(value, lang):
    return value[lang] if isinstance(value, dict) else str(value)


def _date_label(reviewed, lang):
    value = date.fromisoformat(reviewed)
    months = (
        ('January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December')
        if lang == 'en' else
        ('Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz',
         'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık')
    )
    return f'{value.day} {months[value.month - 1]} {value.year}'


def _citation(publication):
    return (
        f"{publication['citation_author']} ({publication['year']}). "
        f"{publication['title']}. {publication['journal']}, "
        f"{publication['volume']}, {publication['article_number']}. "
        f"https://doi.org/{publication['doi']}"
    )


def _bibliography(publication):
    """Regenerate exports without touching existing HTML or research briefs."""
    page = BeautifulSoup((SITE / 'publications.html').read_text(encoding='utf-8'),
                         'html.parser')
    records, seen = [], set()
    for item in page.select('.publication'):
        doi_anchor = item.select_one('a[href*="doi.org/"]')
        if not doi_anchor:
            raise ValueError('Publication without a DOI: ' + _text(item.select_one('h3')))
        doi = doi_anchor['href'].split('doi.org/', 1)[1].strip()
        if doi.lower() in seen:
            raise ValueError('Duplicate publication DOI: ' + doi)
        seen.add(doi.lower())
        author_text = _text(item.select_one('p')).split(' · ', 1)[0]
        authors = re.findall(r'[^,]+,\s*(?:[A-ZÇŞİĞÖÜ]\.\s*)+',
                             author_text.replace(' & ', ' ').replace('&', ''))
        authors = [author.strip(' ,') for author in authors]
        if not authors:
            raise ValueError('Cannot preserve publication authors: ' + author_text)
        record = {
            'title': _text(item.select_one('h3')),
            'authors': authors,
            'author_text': author_text,
            'year': str(item['data-year']),
            'journal': _text(item.select_one('em')),
            'doi': doi,
        }
        if doi.lower() == publication['doi'].lower():
            # Keep the publisher's issue year distinct from its online date.
            record.update(
                title=publication['title'],
                authors=[publication['citation_author']],
                author_text=publication['citation_author'],
                year=str(publication['year']),
                journal=f"{publication['journal']}, {publication['volume']}, Article {publication['article_number']}",
                volume=str(publication['volume']),
                article_number=str(publication['article_number']),
                publisher_url=publication['publisher_url'],
            )
        records.append(record)
    if publication['doi'].lower() not in seen:
        raise ValueError('Add the new publication to the final HTML before exporting it')

    # Existing reference-manager keys must not change meaning when the new paper
    # is inserted at the top of the public list.
    old_keys = {}
    previous = DOWNLOADS / 'selected-publications.bib'
    if previous.exists():
        for key, body in re.findall(r'@article\{([^,]+),\s*(.*?)(?=\n@article|\Z)',
                                    previous.read_text(encoding='utf-8'), re.S):
            match = re.search(r'\bdoi\s*=\s*\{([^}]+)\}', body, re.I)
            if match:
                old_keys[match.group(1).lower()] = key.strip()

    bib, ris = [], []
    for record in records:
        doi = record['doi']
        key = old_keys.get(doi.lower(), 'Ates' + record['year'] +
                           hashlib.sha256(doi.encode()).hexdigest()[:8])
        fields = [
            ('title', record['title']),
            ('author', ' and '.join(record['authors'])),
            ('year', record['year']),
            ('journal', record['journal'].split(',', 1)[0]),
        ]
        if record.get('volume'):
            fields.append(('volume', record['volume']))
        if record.get('article_number'):
            fields.append(('pages', record['article_number']))
        fields.extend([('doi', doi), ('url', 'https://doi.org/' + doi)])
        bib.append('@article{' + key + ',\n' + ',\n'.join(
            '  ' + name + ' = {' + value + '}' for name, value in fields) + '\n}')
        lines = ['TY  - JOUR', 'TI  - ' + record['title']]
        lines.extend('AU  - ' + author for author in record['authors'])
        lines.extend(['PY  - ' + record['year'],
                      'JO  - ' + record['journal'].split(',', 1)[0]])
        if record.get('volume'):
            lines.append('VL  - ' + record['volume'])
        if record.get('article_number'):
            lines.append('SP  - ' + record['article_number'])
        lines.extend(['DO  - ' + doi, 'UR  - https://doi.org/' + doi, 'ER  - '])
        ris.append('\n'.join(lines))
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    (DOWNLOADS / 'selected-publications.bib').write_text('\n\n'.join(bib) + '\n', encoding='utf-8')
    (DOWNLOADS / 'selected-publications.ris').write_text('\n\n'.join(ris) + '\n', encoding='utf-8')
    (DOWNLOADS / 'publication-records.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return records


def _baseline_cv_pages():
    """Capture the final directory CV builder, including later roster corrections.

    Reading only the historical CV constants loses supervision records added by
    ``sync_cv``. Its established transformations are reused without writing any
    intermediate downloads or changing the old builders.
    """
    from build_team_directory import sync_cv
    originals = {}
    export = documents.export_document

    def capture(stem, pages, title, lang='en'):
        originals[lang] = copy.deepcopy(pages)

    documents.export_document = capture
    try:
        sync_cv()
    finally:
        documents.export_document = export
    if set(originals) != {'en', 'tr'}:
        raise ValueError('The final CV builder must supply both English and Turkish')
    return originals


def _cv_pages(publication, visiting, cost, reviewed, lang, baseline, conference):
    """Retain approved CV content while keeping four draft visits separate."""
    pages = copy.deepcopy(baseline[lang])
    if len(pages) != 3:
        raise ValueError('Review CV page structure before applying the academic update')

    current_date = _date_label(reviewed, lang)
    for index, page in enumerate(pages):
        clean = []
        for kind, value in page:
            if index == 2 and 'TÜBİTAK 2221' in value:
                continue
            value = value.replace('13 November 2026', current_date).replace('13 Kasım 2026', current_date)
            if value.startswith(('This public selection excludes manuscripts', 'This public selection omits unpublished',
                                 'Unpublished manuscripts are omitted.')):
                value = ('Publication records: ' + documents.BASE + 'publications.html. '
                         'Submitted applications and proposed visits are listed separately on pages 3 and 4.')
            elif value.startswith('Bu seçki yayımlanmamış makale ayrıntılarını içermez.'):
                value = ('Yayınlar: ' + documents.BASE + 'tr/publications.html. '
                         'Sunulmuş başvurular ve planlanan ziyaretler 3. ve 4. sayfalarda ayrı listelenmiştir.')
            clean.append((kind, value))
        pages[index] = clean

    selected_heading = 'Selected publications' if lang == 'en' else 'Seçilmiş hakemli yayınlar'
    selected = next(i for i, (kind, value) in enumerate(pages[1])
                    if kind == 'h' and value == selected_heading)
    pages[1].insert(selected + 1, ('p', _citation(publication)))

    service_heading = ('Academic leadership and recognition' if lang == 'en'
                       else 'Akademik hizmet ve ödüller')
    service = next(i for i, (kind, value) in enumerate(pages[1])
                   if kind == 'h' and value == service_heading)
    membership = (
        f"November 2026–present | Working Group Member, COST Action {cost['code']} "
        f"{cost['acronym']} ({_localized(cost['title'], 'en')}). "
        'WG1: GenAI Evaluation and Metrics; WG6: Pedagogy and Critical GenAI Literacy.'
        if lang == 'en' else
        f"Kasım 2026–günümüz | COST {cost['code']} {cost['acronym']} Aksiyonu çalışma grubu üyesi. "
        'WG1: Üretken yapay zekânın değerlendirilmesi ve ölçütler; '
        'WG6: Pedagoji ve eleştirel üretken yapay zekâ okuryazarlığı.'
    )
    pages[1].insert(service + 1, ('p', membership))

    # Keep the crowded teaching/publication page readable, without dropping the
    # methods paragraph or reducing its existing font size.
    methods_heading = 'Methods and software' if lang == 'en' else 'Araştırma yöntemleri ve yazılımlar'
    methods = next(i for i, (kind, value) in enumerate(pages[1])
                   if kind == 'h' and value == methods_heading)
    end = next((i for i in range(methods + 1, len(pages[1])) if pages[1][i][0] == 'h'), len(pages[1]))
    pages[0].extend(pages[1][methods:end])
    del pages[1][methods:end]

    title = 'Research visits & conferences' if lang == 'en' else 'Araştırma ziyaretleri ve kongreler'
    intro = (
        'TÜBİTAK 2221 | Four applications in preparation. Host researcher: Hüseyin Ateş, '
        'Kırşehir Ahi Evran University. Proposed visits are planned for 2027 and are subject to funding approval.'
        if lang == 'en' else
        'TÜBİTAK 2221 | Dört başvuru hazırlığında. Ev sahibi araştırmacı: Hüseyin Ateş, '
        'Kırşehir Ahi Evran Üniversitesi. Ziyaretler 2027 için planlanıyor ve destek kararına bağlı.'
    )
    visit_page = [('title', title), ('subtitle', 'Hüseyin Ateş · ' + current_date), ('p', intro)]
    for member in visiting['members']:
        visit_page.extend([
            ('h', member['name']),
            ('p', _localized(member['institution'], lang) + '. ' + _localized(member['title'], lang) + '.'),
            ('small', _localized(member['planned_visit'], lang)),
        ])
    visit_page.append(('small', ('Public research plans: ' if lang == 'en' else 'Araştırma planları: ') +
                       documents.BASE + ('' if lang == 'en' else 'tr/') + 'proposal-visiting-researchers-2221.html'))
    visit_page.extend([
        ('h', 'Accepted conference contributions' if lang == 'en' else 'Kabul edilen kongre bildirileri'),
        ('p', conference['paper_title'] + '.'),
        ('p', conference['event_title'] + '. ' + _localized(conference['dates'], lang) + '; ' +
         _localized(conference['location'], lang) + '. ' + _localized(conference['status'], lang) + '.'),
        ('small', ('Conference record: ' if lang == 'en' else 'Kongre kaydı: ') +
         documents.BASE + ('' if lang == 'en' else 'tr/') + conference['page']),
    ])
    pages.append(visit_page)
    return pages


@contextmanager
def _dated_export(reviewed):
    """Use the established document design with current, consistent date fields."""
    old_new_doc = documents.new_doc
    old_footer, old_footer_tr = documents.pdf_footer, documents.pdf_footer_tr
    old_out = documents.OUT

    def new_doc(title, lang):
        doc = old_new_doc(title, lang)
        label = _date_label(reviewed, lang)
        doc.core_properties.subject = 'Public academic CV; ' + label
        doc.core_properties.modified = datetime.fromisoformat(reviewed)
        # Word's inherited Title style contains a blue bottom border which the
        # established PDF layout does not use. Keep titles typographic in both.
        title_properties = doc.styles['Title'].element.find(qn('w:pPr'))
        if title_properties is not None:
            border = title_properties.find(qn('w:pBdr'))
            if border is not None:
                title_properties.remove(border)
        doc.styles['Title'].font.underline = False
        for section in doc.sections:
            footer = section.footer.paragraphs[0]
            footer.clear()
            footer.add_run('huseyinates38.github.io   |   ' + label + '   |   ').font.size = Pt(8)
            field = OxmlElement('w:fldSimple')
            field.set(qn('w:instr'), 'PAGE')
            footer._p.append(field)
        return doc

    def footer_for(lang):
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(documents.HexColor('#D4E0DE'))
            canvas.line(45, 40, documents.A4[0] - 45, 40)
            canvas.setFont('SiteSans', 7.5)
            canvas.setFillColor(documents.HexColor('#536A72'))
            canvas.drawString(45, 27, 'huseyinates38.github.io  |  ' + _date_label(reviewed, lang))
            canvas.drawRightString(documents.A4[0] - 45, 27, str(doc.page))
            canvas.restoreState()
        return footer

    documents.OUT = DOWNLOADS
    documents.new_doc = new_doc
    documents.pdf_footer = footer_for('en')
    documents.pdf_footer_tr = footer_for('tr')
    try:
        yield
    finally:
        documents.OUT = old_out
        documents.new_doc = old_new_doc
        documents.pdf_footer, documents.pdf_footer_tr = old_footer, old_footer_tr


def update_downloads(publication, visiting, cost, reviewed='2026-11-25'):
    """Write the seven updated public downloads and return a small build report.

    Run only after all three final HTML editions have been updated. The caller
    owns page metadata/search refresh and the subsequent release checksum pass.
    """
    date.fromisoformat(reviewed)
    if str(visiting.get('program')) != '2221' or visiting.get('status_code') != 'in_preparation':
        raise ValueError('Review the CV classifications for a changed 2221 status')
    if len(visiting['members']) != 4 or len({m['slug'] for m in visiting['members']}) != 4:
        raise ValueError('The current update requires four distinct 2221 dossiers')
    if cost['code'] != 'CA25177' or cost.get('member_since') != '2026-11':
        raise ValueError('Review the COST service dates for a different action or membership period')
    records = _bibliography(publication)
    conference = json.loads((ROOT / 'content/conference-biltek-2027.json').read_text(encoding='utf-8'))
    stems = {
        'en': 'Huseyin_Ates_Public_Academic_CV',
        'tr': 'Huseyin_Ates_Akademik_Ozgecmis_TR',
    }
    pages = {}
    documents.fonts()
    baseline = _baseline_cv_pages()
    with _dated_export(reviewed):
        for lang, stem in stems.items():
            blocks = _cv_pages(publication, visiting, cost, reviewed, lang, baseline, conference)
            documents.export_document(
                stem, blocks,
                'Hüseyin Ateş — Public academic CV' if lang == 'en' else 'Hüseyin Ateş — Akademik Özgeçmiş',
                lang=lang,
            )
            reader = PdfReader(DOWNLOADS / (stem + '.pdf'))
            pages[lang] = len(reader.pages)
            if pages[lang] != 4:
                raise ValueError(f'Review {lang} CV layout: expected 4 pages, rendered {pages[lang]}')
            for page in reader.pages:
                if _date_label(reviewed, lang) not in page.extract_text():
                    raise ValueError(f'Missing current {lang} CV footer date')
    return {
        'reviewed': reviewed,
        'publication_count': len(records),
        'cv_pages': pages,
        'downloads': ['selected-publications.bib', 'selected-publications.ris', 'publication-records.json'] +
                     [stem + extension for stem in stems.values() for extension in ('.pdf', '.docx')],
    }
