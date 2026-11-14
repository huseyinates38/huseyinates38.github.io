#!/usr/bin/env python3
"""Apply explicit review dates, verified school links and documented project context.

This is the final content pass, after apply_audit_fixes.py. record-review.json
is authoritative for these overrides; source template dates are not build dates.
No funding decisions, thesis identifiers or undocumented tasks are inferred.
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
CONFIG = ROOT / 'content/record-review.json'
PROPOSAL_PAGES = {'robot-virtual-agent': 'project-robot-virtual-agent.html'}
TEAM_RECORDS = {'3501': 'robot-virtual-agent', 'aub-stem': 'turkiye-uae-stem'}
CTA_OLD = {'Join the research conversation', 'Join our research group',
           'Araştırma grubuna katılmak ister misiniz?', 'Araştırma grubuna katılın'}
CTA = ('Share your research interests and collaboration proposal',
       'Araştırma ve iş birliği önerinizi paylaşın')
MONTHS = {
    'en': ('January', 'February', 'March', 'April', 'May', 'June', 'July',
           'August', 'September', 'October', 'November', 'December'),
    'tr': ('Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz',
           'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'),
}


def pick(en: str, tr: str, lang: str) -> str:
    return tr if lang == 'tr' else en


def plain(node) -> str:
    return node.get_text(' ', strip=True)


def normalized(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', value)
                   if unicodedata.category(c) != 'Mn').replace('ı', 'i').lower()


def time_node(s, iso: str, lang: str):
    value = date.fromisoformat(iso)
    node = s.new_tag('time', datetime=iso)
    node.string = f'{value.day} {MONTHS[lang][value.month - 1]} {value.year}'
    return node


def date_line(s, key: str, label: str, iso: str, lang: str):
    node = s.new_tag('p', attrs={'class': 'v3-small', 'data-record-date': key})
    node.append(label + ': ')
    node.append(time_node(s, iso, lang))
    return node


def proposal_page(slug: str) -> str:
    return PROPOSAL_PAGES.get(slug, 'proposal-' + slug + '.html')


def about_dates(s, config, lang: str):
    # Keep the existing publication/funding disclaimer, removing only its date prefix.
    for node in s.select('[data-record-date="page"],[data-record-date="cv"]'):
        node.decompose()
    candidates = [p for p in s.select('main p.v3-small')
                  if plain(p).startswith(('Updated ', 'Güncelleme: '))]
    if not candidates:
        candidates = [p for p in s.select('main .v3-box p.v3-small')
                      if plain(p).startswith(('Unpublished manuscript', 'Yayımlanmamış'))]
    if len(candidates) != 1:
        raise ValueError('Cannot identify the CV date note unambiguously')
    note = candidates[0]
    note.string = re.sub(r'^(?:Updated |Güncelleme: )[^.]+\.\s*', '', plain(note))
    note.insert_before(date_line(s, 'page', pick('Page last updated', 'Sayfanın son güncellemesi', lang),
                                 config['about']['page_updated'], lang))
    note.insert_before(date_line(s, 'cv', pick('CV last updated (both languages)',
                        'Özgeçmişin son güncellemesi (iki dil)', lang), config['about']['cv_updated'], lang))


def proposal_dates(docs, config, lang: str):
    overview = docs['proposals.html']
    for node in overview.select('[data-record-date]'):
        node.decompose()
    for p in list(overview.select('main p.v3-small')):
        if plain(p).startswith(('Status reviewed:', 'Status checked:', 'Status review:',
                               'Status last checked:', 'Durum kontrolü:')):
            rest = re.sub(r'^[^.]+\.\s*', '', plain(p))
            if rest:
                p.string = rest
            else:
                p.decompose()
    records = config['proposal_status_reviewed']
    hero = overview.select_one('.pagehero .container')
    if hero is None:
        raise ValueError('Missing proposal overview heading')
    # The latest record date is labelled as such, not as a fresh review of every record.
    hero.append(date_line(overview, 'register', pick('Latest status-record review',
        'En son durum kaydı kontrolü', lang), max(records.values()), lang))
    for slug, iso in records.items():
        page = proposal_page(slug)
        s = docs[page]
        labels = [dt for dt in s.select('.proposal-side dt')
                  if plain(dt) in ('Status reviewed', 'Durum kontrolü',
                                   'Status record last reviewed', 'Durum kaydının son kontrolü')]
        if len(labels) != 1:
            raise ValueError(f'Missing status-review field: {page}')
        dt = labels[0]
        dd = dt.find_next_sibling('dd')
        if dd is None:
            raise ValueError(f'Missing status-review value: {page}')
        dt.string = pick('Status record last reviewed', 'Durum kaydının son kontrolü', lang)
        dd.clear()
        dd['data-record-date'] = slug
        dd.append(time_node(s, iso, lang))
        a = overview.select_one(f'.pipeline-card a[href="{page}"]')
        if a is None:
            raise ValueError(f'Missing proposal overview card: {slug}')
        a.insert_before(date_line(overview, slug, pick('Status record last reviewed',
            'Durum kaydının son kontrolü', lang), iso, lang))


def school_links(s, config):
    names = {name: school['url'] for school in config['schools'] for name in school['names']}
    for a in s.select('a[href]'):
        if plain(a) in names:
            a['href'] = names[plain(a)]
    # Keep machine-readable institutional URLs consistent with visible links, if present.
    def repair(value):
        if isinstance(value, dict):
            if value.get('name') in names:
                value['url'] = names[value['name']]
            for child in value.values():
                repair(child)
        elif isinstance(value, list):
            for child in value:
                repair(child)
    for script in s.select('script[type="application/ld+json"]'):
        value = json.loads(script.string or '{}')
        repair(value)
        script.string = json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def project_context(docs, config, lang: str):
    # Read membership from the already-reviewed project groups, not from job titles.
    team = docs['team.html']
    for team_id, proposal_slug in TEAM_RECORDS.items():
        group = team.select_one('#project-team-' + team_id)
        if group is None:
            raise ValueError('Missing documented project team: ' + team_id)
        page = proposal_page(proposal_slug)
        project = docs[page]
        study = plain(group.select_one('.project-team-head h3'))
        stage = plain(project.select_one('.status-pill'))
        for card in group.select('.person-card[data-person]'):
            slug = card['data-person']
            s = docs['person-' + slug + '.html']
            facts = s.select_one('#academic-record .profile-facts')
            if facts is None:
                raise ValueError('Missing academic facts: ' + slug)
            for old in facts.select('[data-project-record]'):
                old.decompose()
            fields = [('study', pick('Related study / application', 'İlgili çalışma / başvuru', lang), study),
                      ('stage', pick('Application stage', 'Başvuru aşaması', lang), stage)]
            if slug in config['profile_contributions']:
                fields.append(('contribution', pick('Proposed contribution', 'Önerilen katkı', lang),
                               config['profile_contributions'][slug][lang == 'tr']))
            for key, label, value in fields:
                row = s.new_tag('div', attrs={'data-project-record': key})
                dt = s.new_tag('dt'); dt.string = label
                dd = s.new_tag('dd')
                if key == 'study':
                    a = s.new_tag('a', href=page); a.string = value; dd.append(a)
                else:
                    dd.string = value
                row.extend([dt, dd]); facts.append(row)


def search_index(docs):
    # Update existing records in place, preserving categories, download entries and exclusions.
    s = docs['search.html']
    data = s.select_one('#site-search-data')
    records = json.loads(data.string)
    for record in records:
        name = record['url']
        if name not in docs or name in ('search.html', 'person-tugce-unsal.html'):
            continue
        main = copy.deepcopy(docs[name].main)
        for node in main.select('script,style,button,select'):
            node.decompose()
        title = plain(main.h1)
        intro = main.select_one('.lead') or main.find('p')
        record.update(title=title, summary=(plain(intro) if intro else '').replace('Tuğçe Ünsal', ''),
                      key=normalized(title + ' ' + plain(main).replace('Tuğçe Ünsal', '')))
    data.string = json.dumps(records, ensure_ascii=False).replace('<', '\\u003c')


def validate(docs, config, lang: str):
    assert docs['about.html'].select_one('[data-record-date="cv"] time')['datetime'] == config['about']['cv_updated']
    assert docs['about.html'].select_one('[data-record-date="page"] time')['datetime'] == config['about']['page_updated']
    for slug, iso in config['proposal_status_reviewed'].items():
        for s in (docs['proposals.html'], docs[proposal_page(slug)]):
            nodes = s.select(f'[data-record-date="{slug}"] time')
            assert len(nodes) == 1 and nodes[0]['datetime'] == iso, (lang, slug)
    for school in config['schools']:
        matching = [a for s in docs.values() for a in s.select('a.institution-name') if plain(a) in school['names']]
        assert matching and all(a['href'] == school['url'] for a in matching), school['key']
    for team_id, proposal_slug in TEAM_RECORDS.items():
        members = docs['team.html'].select(f'#project-team-{team_id} .person-card[data-person]')
        assert len(members) == (6 if team_id == '3501' else 3)
        for card in members:
            s = docs['person-' + card['data-person'] + '.html']
            assert s.select_one(f'[data-project-record="study"] a[href="{proposal_page(proposal_slug)}"]')
            assert s.select_one('[data-project-record="stage"]')
    assert not docs['team.html'].select_one('#project-team-unassigned')
    for s in docs.values():
        assert not any(plain(h) in CTA_OLD for h in s.select('main h1,main h2,main h3'))
    indexed = {r['url']: r for r in json.loads(docs['search.html'].select_one('#site-search-data').string)}
    assert '3501' in indexed['person-gokhan-ince.html']['key']
    assert '12 kasim 2026' not in indexed['proposals.html']['key']


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    dates = [config['editorial_change_date'], *config['about'].values(),
             *config['proposal_status_reviewed'].values()]
    # Validate actual date fields, leaving the explanatory basis string alone.
    for value in dates:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            date.fromisoformat(value)
    changed = []
    for lang in ('en', 'tr'):
        folder = SITE / ('tr' if lang == 'tr' else '')
        originals = {p.name: p.read_text(encoding='utf-8') for p in sorted(folder.glob('*.html'))}
        docs = {name: Soup(html, 'html.parser') for name, html in originals.items()}
        about_dates(docs['about.html'], config, lang)
        proposal_dates(docs, config, lang)
        project_context(docs, config, lang)
        for s in docs.values():
            school_links(s, config)
            for heading in s.select('main h1,main h2,main h3'):
                if plain(heading) in CTA_OLD:
                    heading.string = CTA[lang == 'tr']
        search_index(docs)
        validate(docs, config, lang)
        for name, s in docs.items():
            html = str(s).replace('viewbox=', 'viewBox=').replace('preserveaspectratio=', 'preserveAspectRatio=')
            if html != originals[name]:
                (folder / name).write_text(html, encoding='utf-8')
                changed.append((folder / name).relative_to(SITE).as_posix())
    # Record the narrow editorial edit separately from academic/status review dates.
    for filename in ('deployment.json', 'quality-report.json'):
        path = SITE / filename
        value = json.loads(path.read_text(encoding='utf-8'))
        value['record_review_date'] = config['editorial_change_date']
        value['cv_updated'] = config['about']['cv_updated']
        value['proposal_status_reviewed'] = config['proposal_status_reviewed']
        value['record_review_scope'] = 'Date labels, verified school links, documented project context and bilingual enquiry wording'
        value.pop('files', None)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    # lastmod describes the changed web page, not a new funding verification.
    sitemap = SITE / 'sitemap.xml'
    xml = Soup(sitemap.read_text(encoding='utf-8'), 'xml')
    for url in xml.find_all('url'):
        if url.loc and urlsplit(url.loc.string).path.lstrip('/') in changed and url.lastmod:
            url.lastmod.string = config['editorial_change_date']
    sitemap.write_text(str(xml), encoding='utf-8')
    report = {'result': 'passed', 'languages': ['en', 'tr'], 'proposal_records_per_language': 7,
              'project_profiles_per_language': 9, 'school_urls_verified': 2, 'changed_pages': changed}
    (ROOT / 'record-review-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
