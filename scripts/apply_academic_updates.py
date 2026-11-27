#!/usr/bin/env python3
"""Apply reviewed academic deltas to the final EN/TR/DE release.

Run after add_1002_team.py. Only the structured public registries are inputs;
private application files and credentials never enter the website repository.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import shutil
from html import escape as e
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup as Soup
from add_1002_team import normalized, encoded, dom
from build_german import knowledge
from academic_update_exports import update_downloads

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
BASE = 'https://huseyinates38.github.io/'
VISITING_PAGE = 'proposal-visiting-researchers-2221.html'
NETWORK_PAGE = 'research-network.html'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def fragment(value):
    return Soup(value, 'html.parser')


def section(heading, body, id_, cls='section white'):
    return fragment(f'<section class="{cls}" id="{id_}"><div class="container"><h2>{e(heading)}</h2>{body}</div></section>').section


def replace_section(s, new, before=None):
    old = s.select_one('#' + new['id'])
    if old:
        old.replace_with(new)
    elif before:
        before.insert_before(new)
    else:
        s.main.append(new)


def anchor(label, url):
    return f'<a class="textlink" href="{e(url, quote=True)}">{e(label)}</a>'


def record_date(labels, date, display_date=None):
    return f'<p class="academic-record-date">{e(labels["updated"])}: <time datetime="{date}">{e(display_date or labels["date"])}</time></p>'


def add_publication(docs, cfg, lang):
    pub = cfg['publication']; labels = cfg['locales'][lang]
    page = docs['publications.html']
    pub_id = 'publication-' + hashlib.sha256(pub['url'].encode()).hexdigest()[:10]
    for node in list(page.select('.publication')):
        if any(pub['doi'] in a.get('href', '') for a in node.select('a[href]')):
            node.decompose()
    article = fragment(
        f'<article class="publication" id="{pub_id}" data-year="{pub["year"]}" lang="en">'
        f'<div class="year">{pub["year"]}</div><div><h3>{e(pub["title"])}</h3>'
        f'<p>{e(pub["citation_author"])} · <em>{e(pub["journal"])}, {e(pub["volume"])}, Article {e(pub["article_number"])}</em></p>'
        f'<a href="{pub["url"]}" target="_blank" rel="noopener noreferrer">DOI: {pub["doi"]}</a>'
        f'<p class="publication-update" lang="{lang}">{e(labels["publication_issue"])}</p></div></article>').article
    first = page.select_one('.publication')
    if first is None:
        raise ValueError('Missing publication list')
    first.insert_before(article)
    year = page.select_one('#pub-year')
    if not any(text(o) == str(pub['year']) for o in year.select('option')):
        opt = page.new_tag('option', value=str(pub['year'])); opt.string = str(pub['year'])
        year.select_one('option').insert_after(opt)
    count = len(page.select('.publication'))
    page.select_one('#pub-count').string = labels['publication_count'].replace('24', str(count))
    for box in page.select('.v3-box'):
        for n in list(box.find_all(string=True)):
            n.replace_with(re.sub(r'\b23\b', str(count), str(n)))
    for tag in page.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):
        tag['content'] = labels['publication_description'].replace('24', str(count))
    for stat in docs['index.html'].select('.showcase-stat strong'):
        if text(stat) in ('23', '24'):
            stat.string = str(count)
    return pub_id, count


def visiting_page(docs, cfg, visiting, lang):
    labels = cfg['locales'][lang]; v = visiting['locales'][lang]
    s = docs[VISITING_PAGE]
    hero = copy.deepcopy(s.select_one('.pagehero'))
    hero.select_one('h1').string = v['page_title']
    hero.select_one('.lead').string = v['summary']
    pill = hero.select_one('.status-pill')
    pill['class'] = ['status-pill', 'status-submitted']; pill.string = v['status_label']
    s.main.clear(); s.main.append(hero)
    members = []
    for m in visiting['members']:
        members.append(
            f'<article class="visiting-plan-card" id="visit-{m["slug"]}" data-visiting-researcher="{m["slug"]}">'
            f'<span class="status-pill status-submitted">{e(v["status_label"])}</span>'
            f'<h3>{e(m["name"])}</h3><p class="plan-institution">{e(m["institution"][lang])}</p>'
            f'<h4>{e(m["title"][lang])}</h4><p>{e(m["summary"][lang])}</p>'
            f'<p class="plan-visit">{e(v["proposed_visit_label"])}: {e(m["planned_visit"][lang])}</p>'
            f'{anchor(v["profile_label"], m["profile"])}</article>')
    body = (f'<p>{e(labels["host"])}: <strong>{e(visiting["host_name"])}</strong> · '
            f'{e(visiting["host_institution"][lang])}</p><p>{e(v["call_label"])}: {e(visiting["application_call"])}</p>'
            '<div class="visiting-plan-grid">' + ''.join(members) + '</div>' +
            record_date(labels, visiting['reviewed'], v['reviewed_date']) + '<div class="academic-current-links">' +
            anchor(labels['program_link'], visiting['official_program_url']) + anchor(labels['all_proposals'], 'proposals.html') + '</div>')
    s.main.append(section(labels['dossiers_heading'], body, 'visiting-researcher-plans'))
    s.title.string = v['page_title'] + ' | Hüseyin Ateş'
    for meta in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):
        meta['content'] = v['summary']

    # Keep existing proposal categories and unrelated projects intact.
    for name, doc in docs.items():
        if name in ('assistant.html', 'search.html', VISITING_PAGE):
            continue
        for a in list(doc.main.select(f'a[href="{VISITING_PAGE}"]')):
            if name in ['person-' + slug + '.html' for slug in visiting['closed_2027_profile_slugs']]:
                a.decompose(); continue
            card = a.find_parent('article', class_='pipeline-card')
            if card:
                card['data-proposal-state'] = 'submitted'
                card.select_one('.status-pill')['class'] = ['status-pill', 'status-submitted']
                card.select_one('.status-pill').string = v['status_label']
                card.h3.string = v['page_title']
                para = card.h3.find_next_sibling('p')
                if para: para.string = v['summary']
                time = card.select_one('time')
                if time: time['datetime'] = visiting['reviewed']; time.string = v['reviewed_date']
            news = a.find_parent('article', class_='showcase-news-card')
            if news:
                news.select_one('.showcase-card-copy > p').string = labels['four_applications']
                news.select_one('.showcase-status').string = v['status_label']
                for img_link in news.select('.showcase-card-img'):
                    img_link['aria-label'] = 'TÜBİTAK 2221 · ' + labels['four_applications']
            if '2221' in text(a) and not news:
                a.clear(); a.append(v['page_title'])
        # The heading says latest review; retain older dates on the other records.
        if name == 'proposals.html':
            for t in doc.select('.pagehero time'):
                t['datetime'] = visiting['reviewed']; t.string = v['reviewed_date']

    team = docs['team.html']
    for m in visiting['members']:
        profile = docs[m['profile']]
        plan_url = VISITING_PAGE + '#visit-' + m['slug']
        body = (f'<p class="micro-label">{e(v["status_label"])}</p><h3>{e(m["title"][lang])}</h3>'
                f'<p>{e(m["summary"][lang])}</p><p>{e(v["proposed_visit_label"])}: {e(m["planned_visit"][lang])}</p>' +
                anchor(labels['visiting_link'], plan_url))
        replace_section(profile, section(labels['visiting_profile_heading'], body, 'visiting-2221', 'section muted'))
        for card in team.select(f'[data-person="{m["slug"]}"]'):
            for old in card.select('[data-visiting-plan-link]'): old.decompose()
            card.append(fragment(f'<p data-visiting-plan-link="2221">{anchor("TÜBİTAK 2221 · " + v["status_label"], plan_url)}</p>'))


def cost_sections(docs, cfg, lang):
    cost = cfg['cost']; labels = cfg['locales'][lang]
    groups = ''.join(f'<div class="working-group-card"><strong>{e(g["code"])}</strong><p>{e(g["title"][lang])}</p></div>' for g in cost['groups'])
    body = (f'<p class="lead" lang="en">{e(cost["title"])}</p><p><strong>{e(cost["role"][lang])}</strong></p>'
            f'<p>{e(cost["summary"][lang])}</p><div class="working-group-grid">{groups}</div>'
            f'<div class="academic-current-links">{anchor(labels["cost_official"], cost["official_url"])}</div>')
    network = docs[NETWORK_PAGE]
    replace_section(network, section(labels['cost_heading'], body + record_date(labels, cfg['reviewed']), 'cost-endueai'), network.select_one('#network-directory'))
    about_body = (f'<p><strong>{e(cost["role"][lang])}</strong></p><p>{e(cost["summary"][lang])}</p>'
                  f'<div class="academic-current-links">{anchor(labels["cost_link"], NETWORK_PAGE + "#cost-endueai")}</div>')
    replace_section(docs['about.html'], section(labels['cost_heading'], about_body, 'cost-membership', 'section muted'))


def homepage(docs, cfg, visiting, lang, pub_id):
    labels = cfg['locales'][lang]; pub = cfg['publication']; cost = cfg['cost']
    body = '<div class="academic-update-grid">'
    body += (f'<article class="academic-update-card"><p class="micro-label">{e(labels["new_publication"])} · {e(pub["journal"])}</p>'
             f'<h3 lang="en">{e(pub["title"])}</h3><p>{e(pub["summary"][lang])}</p>'
             f'<p class="academic-record-date">{e(labels["publication_issue"])}</p>' + anchor(labels['publication_link'], 'publications.html#' + pub_id) + '</article>')
    body += (f'<article class="academic-update-card"><p class="micro-label">COST · {cost["code"]}</p><h3>{e(labels["cost_heading"])}</h3>'
             f'<p><strong>{e(cost["role"][lang])}</strong></p><p>{e(cost["summary"][lang])}</p>'
             f'<p>{" · ".join(e(g["code"]) + ": " + e(g["title"][lang]) for g in cost["groups"])}</p>' +
             anchor(labels['cost_link'], NETWORK_PAGE + '#cost-endueai') + '</article></div>')
    s = docs['index.html']
    replace_section(s, section(labels['latest_heading'], body, 'latest-academic-updates'), s.select_one('.showcase-news'))


def update_about(docs, cfg, visiting, lang):
    labels = cfg['locales'][lang]; s = docs['about.html']
    cv_link = s.select_one('a[href*="Huseyin_Ates_Public_Academic_CV.pdf"]')
    if cv_link:
        sec = cv_link.find_parent('section')
        sec.select_one('.v3-box > p').string = labels['cv_description']
        for kind in ('page', 'cv'):
            date = sec.select_one(f'[data-record-date="{kind}"] time')
            if date:
                date['datetime'] = visiting['reviewed']; date.string = visiting['locales'][lang]['reviewed_date']


def conference_sections(docs, conference, lang):
    """Add the accepted abstract without treating it as a journal publication."""
    c = conference; loc = c['locales'][lang]
    # Reuse the established conference shell, including responsive navigation.
    s = Soup(str(docs['conference-iccai-2027.html']).replace(
        'conference-iccai-2027.html', c['page']), 'html.parser')
    hero = copy.deepcopy(s.select_one('.pagehero'))
    hero.select_one('.eyebrow').string = loc['eyebrow']
    hero.h1.string = loc['page_title']
    hero.select_one('.lead').string = c['summary'][lang]
    s.main.clear(); s.main.append(hero)
    metadata = ''.join(
        f'<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>'
        for label, value in ((loc['date_label'], c['dates'][lang]),
                             (loc['location_label'], c['location'][lang]),
                             (loc['participant_label'], c['participant'])))
    body = (f'<div class="conference-detail-grid"><div><p class="status-pill status-accepted">{e(c["status"][lang])}</p>'
            f'<h3 class="conference-paper-title" lang="en">{e(c["paper_title"])}</h3>'
            f'<p>{e(loc["scope"])}</p><p class="conference-event-name" lang="en">{e(c["event_title"])}</p></div>'
            f'<aside class="conference-details"><dl>{metadata}</dl></aside></div>'
            f'<div class="academic-current-links">{anchor(loc["publications_link"], "publications.html#accepted-conference-contributions")}'
            f'{anchor(loc["other_conference"], "conference-iccai-2027.html")}</div>')
    s.main.append(section(loc['paper_heading'], body, 'conference-biltek'))
    s.title.string = loc['page_title'] + ' | Hüseyin Ateş'
    for meta in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):
        meta['content'] = c['summary'][lang]
    docs[c['page']] = s

    card = (f'<article class="academic-update-card" data-conference="{c["slug"]}">'
            f'<p class="micro-label">BİLTEK 16 · {e(c["status"][lang])}</p>'
            f'<h3 lang="en">{e(c["paper_title"])}</h3><p>{e(c["dates"][lang])} · {e(c["location"][lang])}</p>'
            f'{anchor(loc["details_link"], c["page"])}</article>')
    home_card = fragment(card).article
    home_card['class'].append('conference-announcement')
    docs['index.html'].select_one('#latest-academic-updates .academic-update-grid').append(home_card)

    # Keep accepted conference work in its own section, outside journal filters.
    iccai = docs['conference-iccai-2027.html']
    iccai_card = (f'<article class="academic-update-card"><p class="micro-label">ICCAI 2027</p>'
                  f'<h3>{e(loc["other_conference"])}</h3>'
                  f'<p lang="en">{e(text(iccai.select_one(".profile-summary p[lang=en]")))}</p>'
                  f'<p>{e(text(iccai.select_one(".conference-date-place")))}</p>'
                  f'{anchor(loc["details_link"], "conference-iccai-2027.html")}</article>')
    replace_section(docs['publications.html'], section(loc['accepted_heading'],
        '<div class="academic-update-grid">' + card + iccai_card + '</div>', 'accepted-conference-contributions', 'section muted'))
    replace_section(docs['about.html'], section(loc['paper_heading'],
        f'<h3 lang="en">{e(c["paper_title"])}</h3><p>{e(c["summary"][lang])}</p>' +
        anchor(loc['details_link'], c['page']), 'biltek-conference', 'section white'))


def update_metadata(s, name, lang, reviewed):
    title = text(s.main.h1); desc = text(s.select_one('.pagehero .lead'))
    if not desc:
        meta = s.select_one('meta[name="description"]'); desc = meta.get('content', '') if meta else ''
    for meta in s.select('meta[property="og:title"],meta[name="twitter:title"]'): meta['content'] = text(s.title)
    for script in s.select('script[type="application/ld+json"]'):
        data = json.loads(script.string or '{}')
        def walk(value):
            if isinstance(value, list): return [walk(v) for v in value]
            if not isinstance(value, dict): return value
            result = {k: walk(v) for k, v in value.items()}
            if result.get('@type') in ('WebPage', 'ProfilePage'):
                result.update(name=title, description=desc, dateModified=reviewed)
            return result
        script.string = encoded(walk(data))


def refresh_derived(docs, cfg, visiting, conference, lang, pub_id):
    labels = cfg['locales'][lang]; v = visiting['locales'][lang]
    assistant = docs['assistant.html']; facts = json.loads(assistant.select_one('#assistant-facts').string)
    facts['projects']['2221'] = {
        'title': v['page_title'], 'url': VISITING_PAGE, 'summary': v['summary'], 'stage': v['status_label'],
        'reviewed': v['reviewed_date'], 'lead': visiting['host_name'], 'duration': v['planned_year'],
        'application_call': visiting['application_call'],
        'members': [{'slug': m['slug'], 'name': m['name'], 'role': m['role'][lang]} for m in visiting['members']],
        'visits': [{'name': m['name'], 'title': m['title'][lang], 'scope': m['summary'][lang], 'planned_visit': m['planned_visit'][lang],
                    'url': VISITING_PAGE + '#visit-' + m['slug']} for m in visiting['members']]
    }
    cost = cfg['cost']
    facts['projects']['endueai'] = {
        'title': labels['cost_heading'], 'url': NETWORK_PAGE + '#cost-endueai', 'summary': cost['summary'][lang],
        'stage': cost['role'][lang], 'reviewed': labels['date'], 'members': [], 'lead': 'Hüseyin Ateş · WG1 / WG6',
        'duration': '2026–2030', 'groups': [{'code': g['code'], 'title': g['title'][lang]} for g in cost['groups']]
    }
    facts.setdefault('conferences', {})[conference['slug']] = {
        'title': conference['event_title'], 'paper_title': conference['paper_title'],
        'url': conference['page'], 'summary': conference['summary'][lang],
        'stage': conference['status'][lang], 'date': conference['dates'][lang],
        'location': conference['location'][lang], 'reviewed': labels['date']
    }
    for m in visiting['members']:
        person = facts['people'][m['slug']]
        person['studies'] = [x for x in person.get('studies', []) if x['url'].split('#')[0] != VISITING_PAGE]
        person['studies'].append({'title': 'TÜBİTAK 2221 · ' + m['title'][lang], 'url': VISITING_PAGE + '#visit-' + m['slug']})
        person['visiting_2221'] = {'stage': v['status_label'], 'planned_visit': m['planned_visit'][lang],
                                 'period_label': v['proposed_visit_label'], 'scope': m['summary'][lang]}
    for slug in visiting['closed_2027_profile_slugs']:
        p = facts['people'].get(slug)
        if p:
            p['studies'] = [x for x in p.get('studies', []) if x['url'].split('#')[0] != VISITING_PAGE]
    facts['publications'] = [{'title': text(a.h3), 'year': text(a.select_one('.year')), 'citation': text(a),
                              'url': 'publications.html#' + a['id']} for a in docs['publications.html'].select('.publication')]
    assistant.select_one('#assistant-facts').string = encoded(facts)
    kb = knowledge(docs)
    kb['language'] = lang
    kb['basis'] = {'en': 'Reviewed public website records.', 'tr': 'Gözden geçirilmiş açık site kayıtları.', 'de': 'Geprüfte öffentliche Website-Einträge.'}[lang]
    # Rebuild narratives as well as structured facts; stale proposal text is removed.
    structured = []
    for p in facts['people'].values():
        structured.append({'title': p['name'], 'url': p['url'], 'text': encoded({k: val for k, val in p.items() if k not in ('name', 'url')})})
    for p in facts['projects'].values():
        structured.append({'title': p['title'], 'url': p['url'], 'text': encoded({k: val for k, val in p.items() if k not in ('title', 'url')})})
    for p in facts.get('conferences', {}).values():
        structured.append({'title': p['title'], 'url': p['url'], 'text': encoded({k: val for k, val in p.items() if k not in ('title', 'url')})})
    kb['records'] = structured + kb['records']
    assistant.select_one('#assistant-knowledge').string = encoded(kb)
    search = docs['search.html'].select_one('#site-search-data'); rows = json.loads(search.string)
    labels_search = {'en': 'Publications & research briefs', 'tr': 'Yayınlar ve araştırma özetleri', 'de': 'Publikationen und Forschungsüberblicke'}
    for r in rows:
        name = r['url'].split('#')[0]
        if name in docs and name not in ('search.html', 'person-tugce-unsal.html') and '#' not in r['url']:
            main = copy.deepcopy(docs[name].main)
            for n in main.select('script,style,button,select'): n.decompose()
            title = text(main.h1); prose = text(main).replace('Tuğçe Ünsal', '')
            r.update(title=title, summary=text(main.select_one('.lead') or main.find('p')).replace('Tuğçe Ünsal', ''), key=normalized(title + ' ' + prose))
    rurl = 'publications.html#' + pub_id
    rows = [r for r in rows if r['url'] != rurl]
    pub = cfg['publication']
    rows.insert(0, {'title': pub['title'], 'url': rurl, 'category': 'publications', 'label': labels_search[lang],
                    'summary': f'{pub["citation_author"]} ({pub["year"]}). {pub["journal"]}, {pub["volume"]}, {pub["article_number"]}.',
                    'key': normalized(' '.join([pub['title'], pub['doi'], pub['journal'], str(pub['year']), pub['summary'][lang]]))})
    rows = [r for r in rows if r['url'] != conference['page']]
    rows.insert(0, {'title': conference['locales'][lang]['page_title'], 'url': conference['page'],
                   'category': 'publications', 'label': conference['locales'][lang]['accepted_heading'],
                   'summary': conference['summary'][lang],
                   'key': normalized(text(docs[conference['page']].main))})
    search.string = encoded(rows)
    return {'records': kb['records'], 'names': list(dict.fromkeys(p['name'] for p in facts['people'].values()))}


def main():
    cfg = json.loads((ROOT / 'content/academic-updates.json').read_text())
    visiting = json.loads((ROOT / 'content/visiting-2221.json').read_text())
    conference = json.loads((ROOT / 'content/conference-biltek-2027.json').read_text())
    release_reviewed = max(cfg['reviewed'], visiting['reviewed'], conference['reviewed'])
    visiting_pages = {VISITING_PAGE, 'index.html', 'proposals.html', 'team.html',
                      'about.html', 'assistant.html', 'search.html',
                      *[m['profile'] for m in visiting['members']]}
    context = json.loads((SITE / 'assets/assistant-context.json').read_text())
    all_docs = {}; all_originals = {}; changed = []
    for lang in ('en', 'tr', 'de'):
        folder = SITE / ('' if lang == 'en' else lang)
        originals = {p.name: p.read_text() for p in folder.glob('*.html')}
        docs = {name: Soup(value, 'html.parser') for name, value in originals.items()}
        pub_id, count = add_publication(docs, cfg, lang)
        visiting_page(docs, cfg, visiting, lang)
        cost_sections(docs, cfg, lang)
        homepage(docs, cfg, visiting, lang, pub_id)
        update_about(docs, cfg, visiting, lang)
        conference_sections(docs, conference, lang)
        bundle = refresh_derived(docs, cfg, visiting, conference, lang, pub_id)
        if lang in context: context[lang] = bundle
        all_docs[lang] = docs; all_originals[lang] = originals

    # Export helpers read final English bibliography; materialize it before export.
    (SITE / 'publications.html').write_text(dom(all_docs['en']['publications.html']))
    exports = update_downloads(cfg['publication'], visiting, cfg['cost'], cfg['reviewed'])
    for asset in ('academic-updates.css', 'academic-answer-engine.js', 'german-guide.js'):
        shutil.copy2(ROOT / 'assets' / asset, SITE / 'assets' / asset)
    for lang, docs in all_docs.items():
        pre = '' if lang == 'en' else '../'; folder = SITE / ('' if lang == 'en' else lang)
        for name, s in docs.items():
            for a in s.select('a[href*="downloads/"]'):
                path = (folder / urlsplit(a['href']).path).resolve()
                if path.is_file() and ('Huseyin_Ates_' in path.name):
                    label = text(a); detail = f'{path.suffix[1:].upper()}, {max(1, round(path.stat().st_size / 1024))} KB'
                    a['title'] = label + ' (' + detail + ')'; a['aria-label'] = a['title']
            for js in s.select('script[src]'):
                asset = urlsplit(js['src']).path.rsplit('/', 1)[-1]
                if asset in ('academic-answer-engine.js', 'german-guide.js'):
                    digest = hashlib.sha256((SITE / 'assets' / asset).read_bytes()).hexdigest()[:12]
                    js['src'] = pre + 'assets/' + asset + '?v=' + digest
            if s.select('#latest-academic-updates,#visiting-researcher-plans,#cost-endueai,#cost-membership,#visiting-2221,#conference-biltek,#accepted-conference-contributions,#biltek-conference'):
                for old in s.select('link[data-academic-updates]'): old.decompose()
                css = s.new_tag('link', rel='stylesheet', href=pre + 'assets/academic-updates.css', attrs={'data-academic-updates': 'true'})
                s.head.append(css)
            if dom(s) != all_originals[lang].get(name):
                reviewed = visiting['reviewed'] if name in visiting_pages else cfg['reviewed']
                update_metadata(s, name, lang, reviewed)
                (folder / name).write_text(dom(s))
                changed.append((folder / name).relative_to(SITE).as_posix())
    payload = {k: val for k, val in context.items() if k != 'revision'}
    context['revision'] = hashlib.sha256(encoded(payload).encode()).hexdigest()[:16]
    (SITE / 'assets/assistant-context.json').write_text(encoded(context))
    service = ROOT / 'assistant-service/data'
    if service.is_dir(): (service / 'knowledge.json').write_text(encoded(context))
    for name in ('deployment.json', 'quality-report.json'):
        path = SITE / name; value = json.loads(path.read_text()); value.pop('files', None)
        value.update(academic_update_date=release_reviewed, selected_publications=count,
                     visiting_2221_applications=len(visiting['members']), assistant_context_revision=context['revision'],
                     accepted_biltek_2027=True)
        if name == 'deployment.json':
            value['pages'] = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html'))
            value['page_count'] = len(value['pages'])
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    sitemap = Soup((SITE / 'sitemap.xml').read_text(), 'xml')
    for row in sitemap.find_all('url'):
        if row.loc and text(row.loc).removeprefix(BASE) in changed:
            if row.lastmod:
                name = text(row.loc).rsplit('/', 1)[-1]
                row.lastmod.string = visiting['reviewed'] if name in visiting_pages else cfg['reviewed']
    existing_urls = {text(n) for n in sitemap.find_all('loc')}
    for lang in ('en', 'tr', 'de'):
        url = BASE + ('' if lang == 'en' else lang + '/') + conference['page']
        if url in existing_urls: continue
        row = sitemap.new_tag('url'); loc = sitemap.new_tag('loc'); loc.string = url; row.append(loc)
        for alt in ('en', 'tr', 'de', 'x-default'):
            href = BASE + ('' if alt in ('en', 'x-default') else alt + '/') + conference['page']
            row.append(sitemap.new_tag('xhtml:link', attrs={'rel': 'alternate', 'hreflang': alt, 'href': href}))
        date = sitemap.new_tag('lastmod'); date.string = conference['reviewed']; row.append(date)
        sitemap.urlset.append(row)
    (SITE / 'sitemap.xml').write_text(str(sitemap))
    report = {'result': 'built', 'reviewed': release_reviewed, 'languages': ['en', 'tr', 'de'],
              'selected_publications': count, 'visiting_2221_applications': len(visiting['members']),
              'accepted_conference': conference['slug'],
              'cost_action': cfg['cost']['code'], 'exports': exports, 'changed_pages': changed}
    (ROOT / 'academic-updates-build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
