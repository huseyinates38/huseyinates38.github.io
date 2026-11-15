#!/usr/bin/env python3
"""Render complete, explicit project rosters before assistant corpus generation.

The historical builders/tests remain intact. project-rosters.json is the final
membership authority, shared by team cards, project detail cards and profiles.
No membership is inferred from affiliations, publications or arbitrary links.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
CONFIG = ROOT / 'content/project-rosters.json'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value)
                   if unicodedata.category(c) != 'Mn').replace('ı', 'i').lower()


def validate_registry(config):
    ids = set()
    pages = set()
    for project in config['projects']:
        assert re.fullmatch(r'[a-z0-9-]+', project['id'])
        assert re.fullmatch(r'[a-z0-9-]+\.html', project['page'])
        assert project['id'] not in ids and project['page'] not in pages
        ids.add(project['id']); pages.add(project['page'])
        slugs = [m['slug'] for m in project['members']]
        assert slugs and len(slugs) == len(set(slugs)), project['id']
        assert all(re.fullmatch(r'[a-z0-9-]+', slug) for slug in slugs)
        assert all(len(m['role']) == 2 and all(m['role']) for m in project['members'])


def render_card(template, member, lang, project_id):
    card = copy.deepcopy(template)
    # A collaborator's role within one project must not alter their other card.
    card['data-project-member'] = project_id
    label = card.select_one('.micro-label')
    if label is None:
        raise ValueError('Missing role field: ' + member['slug'])
    label.string = member['role'][lang == 'tr']
    # The group's heading carries the shared project/status. Preserve institution
    # marks and links; unique scientific contributions remain on the profile.
    for node in card.select('.relationship-stage,.person-topic'):
        node.decompose()
    for node in card.select('[id]'):
        del node['id']
    card.attrs.pop('hidden', None)
    return card


def update_search(docs):
    node = docs['search.html'].select_one('#site-search-data')
    records = json.loads(node.string)
    for record in records:
        if record['url'] not in docs or record['url'] in ('search.html', 'person-tugce-unsal.html'):
            continue
        main = copy.deepcopy(docs[record['url']].main)
        for extra in main.select('script,style,button,select'):
            extra.decompose()
        title = text(main.h1)
        intro = main.select_one('.lead') or main.find('p')
        record.update(title=title, summary=text(intro).replace('Tuğçe Ünsal', ''),
                      key=normalized(title + ' ' + text(main).replace('Tuğçe Ünsal', '')))
    node.string = json.dumps(records, ensure_ascii=False).replace('<', '\\u003c')


def apply(docs, config, lang):
    team = docs['team.html']
    templates = {}
    for card in team.select('.person-card[data-person]'):
        templates.setdefault(card['data-person'], copy.deepcopy(card))
    membership = {}
    for project in config['projects']:
        group = team.select_one('#project-team-' + project['id'])
        if group is None or project['page'] not in docs:
            raise ValueError('Missing project group/page: ' + project['id'])
        grid = group.select_one('.people-grid')
        if grid is None:
            raise ValueError('Missing people grid: ' + project['id'])
        grid.clear()
        title = text(group.select_one('.project-team-head h3'))
        for member in project['members']:
            slug = member['slug']
            if slug not in templates or 'person-' + slug + '.html' not in docs:
                raise ValueError('Unknown profile: ' + slug)
            grid.append(render_card(templates[slug], member, lang, project['id']))
            membership.setdefault(slug, []).append((project['page'], title))
        # No participant may be relegated to an "also participates" notice.
        for note in group.select('.project-team-note'):
            note.decompose()
        page = docs[project['page']]
        section = page.select_one('#' + project['section_id'])
        if section is None:
            section = page.new_tag('section', attrs={'class': 'section muted', 'id': project['section_id']})
            page.main.append(section)
        section.clear()
        container = page.new_tag('div', attrs={'class': 'container'})
        heading = page.new_tag('h2'); heading.string = project['heading'][lang == 'tr']
        container.append(heading)
        container.append(copy.deepcopy(grid))
        section.append(container)
        # Directory card styles are required on proposal pages as well.
        if not page.select_one('link[href*="team-directory.css"]'):
            css = page.new_tag('link', rel='stylesheet', href=('../' if lang == 'tr' else '') +
                               'assets/team-directory.css?v=' + hashlib.sha256((SITE/'assets/team-directory.css').read_bytes()).hexdigest()[:12])
            design = page.select_one('link[href*="design-system.css"]')
            design.insert_before(css) if design else page.head.append(css)
    # Existing distinct publications/collaborations are retained. Shared people
    # have one profile, with every confirmed project link listed once.
    for slug, studies in membership.items():
        page = docs['person-' + slug + '.html']
        facts = page.select_one('#academic-record .profile-facts')
        if facts is None:
            raise ValueError('Missing academic profile: ' + slug)
        row = facts.select_one('[data-project-record="study"]')
        if row is None:
            row = page.new_tag('div', attrs={'data-project-record': 'study'})
            row.extend([page.new_tag('dt'), page.new_tag('dd')]); facts.append(row)
        row.dt.string = (('İlgili çalışmalar / başvurular' if len(studies)>1 else 'İlgili çalışma / başvuru')
                         if lang == 'tr' else ('Related studies / applications' if len(studies)>1 else 'Related study / application'))
        row.dd.clear()
        for index, (url, title) in enumerate(studies):
            if index:
                row.dd.append(page.new_tag('br'))
            link = page.new_tag('a', href=url); link.string = title; row.dd.append(link)
        # The project link is now in the structured profile; keep other unique
        # works (e.g. Konca's published STEM article) in their original place.
        urls = {url for url, _ in studies}
        for link in list(page.select('#ongoing-research .profile-links a[href]')):
            if link['href'] in urls:
                link.decompose()
    update_search(docs)
    return membership


def verify(docs, config):
    for project in config['projects']:
        expected = [m['slug'] for m in project['members']]
        group = docs['team.html'].select_one('#project-team-' + project['id'])
        actual = [c['data-person'] for c in group.select('.person-card[data-person]')]
        assert actual == expected, (project['id'], actual, expected)
        assert not group.select('.project-team-note')
        section = docs[project['page']].select_one('#' + project['section_id'])
        assert [c['data-person'] for c in section.select('.person-card[data-person]')] == expected
        for slug in expected:
            assert docs['person-'+slug+'.html'].select_one(
                '[data-project-record="study"] a[href="'+project['page']+'"]')
    assert docs['team.html'].select_one('#collaborators [data-person="ahmet-sami-konca"]')
    for s in docs.values():
        if s is docs.get('assistant.html'):
            continue  # The subsequent assistant builders replace their corpus.
        assert 'Ahmet Sami Konca (UAEU) da bu başvuruda görev almaktadır.' not in text(s.main)
        assert 'Ahmet Sami Konca (UAEU) also participates in this proposal.' not in text(s.main)


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    validate_registry(config)
    changed = []
    for lang in ('en','tr'):
        folder = SITE/('tr' if lang=='tr' else '')
        originals = {p.name: p.read_text(encoding='utf-8') for p in folder.glob('*.html')}
        docs = {name: Soup(source,'html.parser') for name,source in originals.items()}
        before = {name: str(doc).replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio=') for name, doc in docs.items()}
        apply(docs,config,lang); verify(docs,config)
        for name, doc in docs.items():
            content = str(doc).replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio=')
            if content != before[name]:
                (folder/name).write_text(content,encoding='utf-8')
                changed.append((folder/name).relative_to(SITE).as_posix())
    sitemap = SITE/'sitemap.xml'
    if sitemap.is_file():
        s = Soup(sitemap.read_text(),'xml')
        for entry in s.find_all('url'):
            if entry.loc and entry.lastmod and urlsplit(entry.loc.string).path.lstrip('/') in changed:
                entry.lastmod.string = config['editorial_updated']
        sitemap.write_text(str(s),encoding='utf-8')
    report = {'result':'passed','languages':['en','tr'],
              'members_per_project':{p['id']:len(p['members']) for p in config['projects']},
              'changed_pages':changed,'funding_status_changed':False}
    (ROOT/'project-roster-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
