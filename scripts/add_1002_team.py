#!/usr/bin/env python3
"""Publish the source-verified 1002 roster in every final language edition.

Runs after the German/localisation pass. The project page is the public profile
for members without a separate biography; do not invent a title, supervision
relationship, graduation date or new personal page. Existing discovery choices,
funding statements and CV/status-review dates remain unchanged.
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
CONFIG = ROOT / 'content/project-1002-team.json'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value)
                   if unicodedata.category(c) != 'Mn').replace('ı', 'i').replace('ß', 'ss').lower()


def encoded(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def dom(node):
    return str(node).replace('viewbox=', 'viewBox=').replace('preserveaspectratio=', 'preserveAspectRatio=')


def link(s, label, href):
    a = s.new_tag('a', href=href, attrs={'class': 'textlink'})
    a.string = label
    return a


def card(s, member, lang, affiliation, cfg, detail=False):
    labels = cfg['locales'][lang]
    article = s.new_tag('article', attrs={'class': 'person-card', 'data-person': member['slug'],
                                        'data-project-member': '1002'})
    if detail:
        article['id'] = 'member-' + member['slug']
    top = s.new_tag('div', attrs={'class': 'person-top'})
    box = s.new_tag('div')
    role = s.new_tag('p', attrs={'class': 'micro-label'})
    role.string = member['role'][lang]
    name = s.new_tag('h3'); name.string = member['name']
    box.extend([role, name]); top.append(box); article.append(top)
    contribution = s.new_tag('p', attrs={'class': 'person-topic', 'data-member-contribution': '1002'})
    contribution.string = member['contribution'][lang]
    article.append(contribution)
    # All four affiliations are explicitly listed in the ethics application.
    article.append(copy.deepcopy(affiliation))
    if member.get('profile'):
        article.append(link(s, labels['profile_link'], member['profile']))
    elif not detail:
        article.append(link(s, labels['role_link'], cfg['page'] + '#member-' + member['slug']))
    return article


def update_profile(s, member, lang, cfg):
    labels = cfg['locales'][lang]
    facts = s.select_one('#academic-record .profile-facts')
    if facts is None:
        raise ValueError('Missing profile facts: ' + member['slug'])
    study = facts.select_one('[data-project-record="study"]')
    if study is None:
        study = s.new_tag('div', attrs={'data-project-record': 'study'})
        dt = s.new_tag('dt'); dt.string = labels['study_label']
        study.extend([dt, s.new_tag('dd')]); facts.append(study)
    if not study.select_one('a[href="' + cfg['page'] + '"]'):
        if study.dd.contents:
            study.dd.append(s.new_tag('br'))
        study.dd.append(link(s, labels['title'], cfg['page']))
    for old in list(facts.select('[data-1002-contribution]')):
        old.decompose()
    contribution = s.new_tag('div', attrs={'data-1002-contribution': ''})
    dt = s.new_tag('dt'); dt.string = labels['contribution_label']
    dd = s.new_tag('dd'); dd.string = member['contribution'][lang]
    contribution.extend([dt, dd]); facts.append(contribution)


def source_records(docs, facts, cfg, lang):
    """New public records, keeping personal-profile discovery exclusions intact."""
    title = cfg['locales'][lang]['title']
    rows = []
    project = facts['projects']['1002']
    payload = {k: v for k, v in project.items() if k not in ('url', 'title')}
    rows.append({'title': title, 'url': cfg['page'], 'text': encoded(payload)})
    for member in cfg['members']:
        if member.get('discovery_excluded'):
            continue
        person = facts['people'][member['slug']]
        rows.append({'title': member['name'], 'url': person['url'],
                     'text': encoded({k: v for k, v in person.items() if k not in ('name', 'url')})})
    roster = docs[cfg['page']].select_one('#' + cfg['section_id'])
    rows.append({'title': title, 'url': cfg['page'] + '#' + cfg['section_id'], 'text': text(roster)})
    return rows


def replace_records(records, new_records, cfg):
    urls = {r['url'] for r in new_records}
    # Replace structured snapshots for this project and affected people, not
    # unrelated narrative records or their existing publication connections.
    kept = []
    for record in records:
        if record['url'] == cfg['page'] + '#' + cfg['section_id']:
            continue
        if record['url'] in urls and record['text'].lstrip().startswith('{'):
            continue
        kept.append(record)
    return new_records + kept


def apply_locale(docs, cfg, lang):
    labels = cfg['locales'][lang]
    team = docs['team.html']; project = docs[cfg['page']]
    reference = copy.deepcopy(team.select_one('#graduate-researchers [data-person="abdulkadir-aydin"] .affiliation-list'))
    if reference is None or 'ahievran.edu.tr' not in str(reference):
        raise ValueError('Verified university affiliation template missing')
    old = team.select_one('#project-team-1002')
    if old:
        old.decompose()
    group = team.new_tag('div', attrs={'class': 'project-team', 'data-project-team': '',
                                     'id': 'project-team-1002'})
    head = team.new_tag('div', attrs={'class': 'project-team-head'})
    desc = team.new_tag('div')
    micro = team.new_tag('p', attrs={'class': 'micro-label'}); micro.string = cfg['project_code']
    h = team.new_tag('h3'); h.string = labels['title']
    p = team.new_tag('p'); p.string = labels['summary']
    desc.extend([micro, h, p]); head.extend([desc, link(team, labels['project_link'], cfg['page'])])
    grid = team.new_tag('div', attrs={'class': 'people-grid'})
    for member in cfg['members']:
        grid.append(card(team, member, lang, reference, cfg))
    group.extend([head, grid])
    stack = team.select_one('#project-researchers .project-team-stack')
    if stack is None:
        raise ValueError('Project-directory stack missing')
    stack.insert(0, group)
    section = project.select_one('#' + cfg['section_id'])
    if section is None:
        section = project.new_tag('section', attrs={'class': 'section muted', 'id': cfg['section_id']})
        project.main.append(section)
    section.clear()
    container = project.new_tag('div', attrs={'class': 'container'})
    h = project.new_tag('h2'); h.string = labels['heading']; container.append(h)
    grid = project.new_tag('div', attrs={'class': 'people-grid'})
    for member in cfg['members']:
        grid.append(card(project, member, lang, reference, cfg, detail=True))
        if member.get('profile'):
            update_profile(docs[member['profile']], member, lang, cfg)
    container.append(grid); section.append(container)
    if not project.select_one('link[href*="team-directory.css"]'):
        href = ('' if lang == 'en' else '../') + 'assets/team-directory.css'
        css = project.new_tag('link', rel='stylesheet', href=href)
        design = project.select_one('link[href*="design-system.css"]')
        design.insert_before(css) if design else project.head.append(css)

    assistant = docs['assistant.html']
    facts_tag = assistant.select_one('#assistant-facts')
    facts = json.loads(facts_tag.string)
    project_facts = facts['projects']['1002']
    original_stage = project_facts['stage']
    institution = text(reference.select_one('.institution-name'))
    project_facts['members'] = [{'name': m['name'], 'slug': m['slug'], 'role': m['role'][lang]}
                                for m in cfg['members']]
    project_facts['lead'] = cfg['principal_investigator']
    for member in cfg['members']:
        if member.get('discovery_excluded'):
            continue
        url = member.get('profile', cfg['page'] + '#member-' + member['slug'])
        person = facts['people'].setdefault(member['slug'], {
            'name': member['name'], 'url': url, 'role': member['role'][lang],
            'institutions': [institution], 'studies': [], 'stage': '',
            'contribution': '', 'focus': '', 'degree': ''})
        if not any(x['url'] == cfg['page'] for x in person['studies']):
            person['studies'].append({'title': labels['title'], 'url': cfg['page']})
        person['contribution'] = member['contribution'][lang]
    assert project_facts['stage'] == original_stage
    facts_tag.string = encoded(facts)
    additions = source_records(docs, facts, cfg, lang)
    kb = assistant.select_one('#assistant-knowledge')
    knowledge = json.loads(kb.string)
    knowledge['records'] = replace_records(knowledge['records'], additions, cfg)
    kb.string = encoded(knowledge)

    search = docs['search.html'].select_one('#site-search-data')
    records = json.loads(search.string)
    excluded = {m['profile'] for m in cfg['members'] if m.get('discovery_excluded')}
    for record in records:
        if record['url'] not in docs or record['url'] in excluded or record['url'] == 'search.html':
            continue
        main = copy.deepcopy(docs[record['url']].main)
        for extra in main.select('script,style,button,select'):
            extra.decompose()
        title = text(main.h1); intro = main.select_one('.lead') or main.find('p')
        prose = text(main)
        for m in cfg['members']:
            if m.get('discovery_excluded'):
                prose = prose.replace(m['name'], '')
        record.update(title=title, summary=text(intro).replace('Tuğçe Ünsal', ''),
                      key=normalized(title + ' ' + prose))
    search.string = encoded(records)
    return additions, [m['name'] for m in cfg['members'] if not m.get('discovery_excluded')]


def main():
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    slugs = [m['slug'] for m in cfg['members']]
    assert len(slugs) == 4 and len(set(slugs)) == 4
    assert all(re.fullmatch(r'[a-z0-9-]+', slug) for slug in slugs)
    changed = []
    context_path = SITE/'assets/assistant-context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    for lang in cfg['locales']:
        folder = SITE/('' if lang == 'en' else lang)
        originals = {p.name: p.read_text(encoding='utf-8') for p in folder.glob('*.html')}
        docs = {name: Soup(source, 'html.parser') for name, source in originals.items()}
        additions, names = apply_locale(docs, cfg, lang)
        if lang in context:  # Do not activate German cloud service by adding a locale.
            context[lang]['records'] = replace_records(context[lang]['records'], additions, cfg)
            context[lang]['names'] = list(dict.fromkeys(context[lang]['names'] + names))
        for name, doc in docs.items():
            output = dom(doc)
            if output != originals[name]:
                (folder/name).write_text(output, encoding='utf-8')
                changed.append((folder/name).relative_to(SITE).as_posix())
    payload = {k: v for k, v in context.items() if k != 'revision'}
    context['revision'] = hashlib.sha256(encoded(payload).encode()).hexdigest()[:16]
    context_path.write_text(encoded(context), encoding='utf-8')
    for filename in ('deployment.json', 'quality-report.json'):
        path = SITE/filename; info = json.loads(path.read_text(encoding='utf-8'))
        info['project_1002_roster_updated'] = cfg['updated']
        info['assistant_context_revision'] = context['revision']
        info.pop('files', None)
        path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    sitemap = SITE/'sitemap.xml'
    xml = Soup(sitemap.read_text(), 'xml')
    for entry in xml.find_all('url'):
        if entry.loc and entry.lastmod and urlsplit(entry.loc.string).path.lstrip('/') in changed:
            entry.lastmod.string = cfg['updated']
    sitemap.write_text(str(xml), encoding='utf-8')
    report = {'result': 'passed', 'languages': list(cfg['locales']), 'team_members': slugs,
              'principal_investigator': cfg['principal_investigator'], 'new_person_pages': 0,
              'funding_status_changed': False, 'changed_pages': changed}
    (ROOT/'project-1002-build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
