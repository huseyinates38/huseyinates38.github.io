#!/usr/bin/env python3
"""Release gate for reviewed publication, COST and visiting-researcher updates.

Default: final HTML, downloads, search/assistant data and real JS answer engines.
--browser: additionally exercise 36 local page loads in Chromium for CI.
No external requests, model downloads or source-building side effects are needed.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import threading
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup as Soup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
CFG = json.loads((ROOT / 'content/academic-updates.json').read_text())
VISITING = json.loads((ROOT / 'content/visiting-2221.json').read_text())
LANGS = ('en', 'tr', 'de')
DOI = '10.1016/j.compedu.2026.105805'
VISITING_PAGE = 'proposal-visiting-researchers-2221.html'
MEMBERS = VISITING['members']
NAMES = [member['name'] for member in MEMBERS]
SLUGS = [member['slug'] for member in MEMBERS]
PRIVATE = re.compile(r'(?:drive\.google\.com/(?:file|drive)|docs\.google\.com/(?:document|spreadsheets|presentation)/d/|1059B\d{8,}|libfile_|file-inline-libfile_)', re.I)
BAD_2221_STATUS = re.compile(r'\bsubmitted\b|\beingereicht\b|başvurusu yapıl|başvuru sunuldu|desteklenmektedir|funding awarded', re.I)
QUESTIONS = {
    'en': {'cost': 'COST activities', 'endueai': 'COST CA25177 ENDUeAI', 'sciepi': 'SciEpi-Feedback status', 'roster': 'Who is on the 2221 team?', 'paper': 'Show 2027 publications', 'kazem_visit': 'Kazem Banihashem visit', 'omid_visit': 'Omid Noroozi 2221 visit dates'},
    'tr': {'cost': 'COST çalışmaları', 'endueai': 'COST CA25177 ENDUeAI', 'sciepi': 'SciEpi-Feedback durumu', 'roster': '2221 ekibinde kimler var?', 'paper': '2027 yayınlarını göster', 'kazem_visit': 'Kazem Banihashem ziyareti', 'omid_visit': 'Omid Noroozi 2221 ziyaret tarihleri'},
    'de': {'cost': 'COST-Aktivitäten', 'endueai': 'COST CA25177 ENDUeAI', 'sciepi': 'SciEpi-Feedback Status', 'roster': 'Wer gehört zum 2221-Team?', 'paper': 'Publikationen 2027', 'kazem_visit': 'Kazem Banihashem Besuch', 'omid_visit': 'Omid Noroozi 2221 Besuchstermine'},
}


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def normalized(value):
    value = value.lower().replace('ı', 'i').replace('ß', 'ss')
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))


def folder(lang):
    return SITE / ('' if lang == 'en' else lang)


@functools.lru_cache(maxsize=None)
def read(path):
    return Soup(Path(path).read_text(encoding='utf-8'), 'html.parser')


def embedded(doc, id_):
    node = doc.find(id=id_)
    assert node is not None, ('missing embedded data', id_)
    return json.loads(node.string or node.get_text())


def publication_dois(doc):
    values = []
    for item in doc.select('.publication'):
        links = item.select('a[href*="doi.org/"]')
        assert len(links) == 1, ('publication DOI links', text(item.h3))
        values.append(links[0]['href'].split('doi.org/', 1)[1].lower())
    assert len(values) == len(set(values)) == 24, ('publication count', len(values))
    return set(values)


def assert_current_2221(value, label):
    assert not BAD_2221_STATUS.search(value), (label, 'incorrect 2221 status')
    assert not re.search(r'Moritz\s+Krell|Elena\s+Novak', value, re.I), (label, 'closed 2027 visitor')
    assert not PRIVATE.search(value), (label, 'private record leaked')


def check_links(doc, source):
    ids = [n['id'] for n in doc.select('[id]')]
    assert len(ids) == len(set(ids)), (source, 'duplicate ID')
    for a in doc.select('a[href]'):
        u = urlsplit(a['href'])
        if u.scheme or u.netloc:
            continue
        target = ((SITE / unquote(u.path).lstrip('/')) if u.path.startswith('/') else
                  (source.parent / unquote(u.path) if u.path else source)).resolve()
        if target.is_dir():
            target /= 'index.html'
        assert target.is_relative_to(SITE.resolve()) and target.is_file(), (source, a['href'])
        if u.fragment and target.suffix == '.html' and '=' not in u.fragment:
            assert read(target).find(id=unquote(u.fragment)), (source, a['href'], 'missing anchor')


def static_checks(report):
    expected_dois = None
    engine_inputs = []
    for lang in LANGS:
        loc, base = CFG['locales'][lang], folder(lang)
        docs = {name: read(base / name) for name in (
            'index.html', 'publications.html', VISITING_PAGE, 'research-network.html',
            'about.html', 'assistant.html', 'search.html', 'proposals.html',
            'proposal-sciepi-feedback.html', 'team.html', 'project-space-debris.html',
            'person-naomi-winstone.html', *[m['profile'] for m in MEMBERS],
            'person-moritz-krell.html', 'person-elena-novak.html')}
        pubs = docs['publications.html']
        dois = publication_dois(pubs)
        if expected_dois is None:
            expected_dois = dois
        assert dois == expected_dois, (lang, 'different DOI catalogue')
        matches = [a for a in pubs.select('.publication') if DOI in str(a)]
        assert len(matches) == 1, (lang, 'new publication duplicated or missing')
        item = matches[0]
        assert item['data-year'] == '2027' and text(item.select_one('.year')) == '2027'
        assert text(item.h3) == CFG['publication']['title']
        assert all(x in text(item) for x in ('Computers & Education', '258', '105805', DOI))
        assert pubs.select_one('#pub-year option[value="2027"]')
        assert re.search(r'\b24\b', text(pubs.select_one('#pub-count')))
        assert docs['index.html'].select_one('a[href="publications.html#' + item['id'] + '"]')
        assert docs['index.html'].select_one('#latest-academic-updates')

        page = docs[VISITING_PAGE]
        assert page.select_one('#visiting-researcher-plans')
        assert text(page.h1) == VISITING['locales'][lang]['page_title']
        cards = page.select('.visiting-plan-card')
        assert [c['data-visiting-researcher'] for c in cards] == SLUGS
        assert len(cards) == 4
        assert_current_2221(text(page.main), (lang, VISITING_PAGE))
        for card, member in zip(cards, MEMBERS):
            assert card['id'] == 'visit-' + member['slug']
            assert text(card.h3) == member['name']
            assert text(card.h4) == member['title'][lang]
            assert text(card.select_one('.status-pill')) == VISITING['locales'][lang]['status_label']
            assert member['institution'][lang] in text(card)
            assert member['summary'][lang] in text(card)
            assert member['planned_visit'][lang] in text(card)
            assert card.select_one('a[href="' + member['profile'] + '"]')
            profile = docs[member['profile']].select_one('#visiting-2221')
            assert profile and member['title'][lang] in text(profile)
            assert_current_2221(text(profile), (lang, member['slug']))
        for slug in VISITING['closed_2027_profile_slugs']:
            assert not docs['person-' + slug + '.html'].select(f'a[href^="{VISITING_PAGE}"]')
        pipeline = [a for a in docs['proposals.html'].select('.pipeline-card') if a.select_one(f'a[href="{VISITING_PAGE}"]')]
        assert len(pipeline) == 1 and pipeline[0]['data-proposal-state'] == 'planned'

        cost = docs['research-network.html'].select_one('#cost-endueai')
        assert cost and all(x in text(cost) for x in ('CA25177', 'ENDUeAI', 'WG1', 'WG6'))
        assert CFG['cost']['role'][lang] in text(cost)
        assert {text(c.strong) for c in cost.select('.working-group-card')} == {'WG1', 'WG6'}
        assert cost.select_one('a[href="' + CFG['cost']['official_url'] + '"]')
        assert docs['about.html'].select_one('#cost-membership')
        assert 'SciEpi' in text(docs['proposal-sciepi-feedback.html'].main)
        assert 'CA25177' not in text(docs['proposal-sciepi-feedback.html'].select_one('.pagehero'))
        for kind in ('page', 'cv'):
            date = docs['about.html'].select_one(f'[data-record-date="{kind}"] time')
            assert date and date['datetime'] == '2026-11-25' and text(date) == loc['date']

        # Protect the earlier roster and editorial corrections after the new final pass.
        assert len(docs['team.html'].select('#project-team-1002 .person-card')) == 4
        project = docs['project-space-debris.html']
        assert len(project.select('#project-1002-team .person-card')) == 4
        assert project.select_one('#funding-decision-note') is None
        assert not re.search(r'Destek kararı kaydı|Funding decision evidence|Nachweis der Förderentscheidung', text(project.main))
        naomi = docs['person-naomi-winstone.html']
        assert '2219' in text(naomi.main) and 'Surrey' in text(naomi.main)
        assert naomi.select_one('a[href="proposal-feedback-fading.html"]')
        assert not re.search(r'manuscript|manuskript|makale|co-author', text(naomi.main), re.I)

        facts = embedded(docs['assistant.html'], 'assistant-facts')
        kb = embedded(docs['assistant.html'], 'assistant-knowledge')
        search = embedded(docs['search.html'], 'site-search-data')
        visit = facts['projects']['2221']
        assert [m['slug'] for m in visit['members']] == SLUGS
        assert [m['name'] for m in visit['members']] == NAMES
        assert visit['stage'] == VISITING['locales'][lang]['status_label']
        assert len(visit['visits']) == 4
        assert_current_2221(json.dumps(visit, ensure_ascii=False), (lang, 'assistant 2221'))
        for member in MEMBERS:
            person = facts['people'][member['slug']]
            links = [s for s in person['studies'] if s['url'].split('#')[0] == VISITING_PAGE]
            assert len(links) == 1 and links[0]['url'].endswith('#visit-' + member['slug'])
            assert person['visiting_2221']['stage'] == visit['stage']
        for slug in VISITING['closed_2027_profile_slugs']:
            assert not any(s['url'].split('#')[0] == VISITING_PAGE for s in facts['people'][slug]['studies'])
        assert facts['projects']['endueai']['stage'] == CFG['cost']['role'][lang]
        assert [g['code'] for g in facts['projects']['endueai']['groups']] == ['WG1', 'WG6']
        assert facts['projects']['cost']['url'] == 'proposal-sciepi-feedback.html'
        assert facts['projects']['endueai']['url'] == 'research-network.html#cost-endueai'
        assert len(facts['publications']) == 24
        assert len([p for p in facts['publications'] if DOI in p['citation']]) == 1
        entries = [r for r in search if r['url'].split('#')[0] == VISITING_PAGE]
        assert entries and all(normalized(n) in ' '.join(r['key'] for r in entries) for n in NAMES)
        assert len([r for r in search if DOI in r['key'] and r['url'].startswith('publications.html#')]) == 1
        for corpus_name, rows in [('search', search), ('assistant', kb['records'])]:
            affected = [r for r in rows if r['url'].split('#')[0] == VISITING_PAGE]
            assert affected, (lang, corpus_name, 'no 2221 record')
            for r in affected:
                assert_current_2221(json.dumps(r, ensure_ascii=False), (lang, corpus_name, r['url']))
            joined = json.dumps(rows, ensure_ascii=False)
            searchable = normalized(joined)
            assert DOI in searchable and 'ca25177' in searchable and all(normalized(n) in searchable for n in NAMES)
            assert not PRIVATE.search(joined), (lang, corpus_name, 'private record')
        for name, doc in docs.items():
            assert not PRIVATE.search(str(doc)), (lang, name, 'private record')
            check_links(doc, base / name)
        engine_name = 'german-guide.js' if lang == 'de' else 'academic-answer-engine.js'
        engine_inputs.append({'lang': lang, 'facts': facts, 'corpus': kb,
                              'script': str(SITE / 'assets' / engine_name), 'questions': QUESTIONS[lang]})
        report['languages'].append(lang)
        report['static_pages'] += len(docs)
    return expected_dois, engine_inputs


def download_checks(expected_dois, report):
    downloads = SITE / 'downloads'
    records = json.loads((downloads / 'publication-records.json').read_text())
    assert len(records) == 24 and {r['doi'].lower() for r in records} == expected_dois
    paper = next(r for r in records if r['doi'].lower() == DOI)
    assert (str(paper['year']), paper['volume'], paper['article_number']) == ('2027', '258', '105805')
    assert paper['title'] == CFG['publication']['title']
    bib = (downloads / 'selected-publications.bib').read_text()
    ris = (downloads / 'selected-publications.ris').read_text()
    bib_dois = re.findall(r'^\s*doi\s*=\s*\{([^}]+)\}', bib, re.M | re.I)
    ris_dois = re.findall(r'^DO\s+-\s+(.+)$', ris, re.M)
    for kind, values in [('BibTeX', bib_dois), ('RIS', ris_dois)]:
        assert len(values) == 24 and {v.lower() for v in values} == expected_dois, kind
        assert values.count(DOI) == 1, (kind, 'duplicate new DOI')
    assert len(re.findall(r'^@article\{', bib, re.M)) == 24
    assert len(re.findall(r'^TY\s+-\s+JOUR$', ris, re.M)) == 24
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'dcterms': 'http://purl.org/dc/terms/'}
    for lang, stem in [('en', 'Huseyin_Ates_Public_Academic_CV'), ('tr', 'Huseyin_Ates_Akademik_Ozgecmis_TR')]:
        date = CFG['locales'][lang]['date']
        pages = [p.extract_text() for p in PdfReader(downloads / (stem + '.pdf')).pages]
        assert len(pages) == 4 and all(date in p for p in pages), (lang, 'CV pages/date')
        all_text = '\n'.join(pages)
        assert DOI in all_text and all(x in all_text for x in ('CA25177', 'WG1', 'WG6'))
        assert all(name in pages[3] for name in NAMES), (lang, 'four visiting CV records')
        assert '2221' not in pages[2], (lang, 'draft visits misclassified on submitted page')
        assert '2221' in pages[3]
        assert not PRIVATE.search(all_text)
        with ZipFile(downloads / (stem + '.docx')) as archive:
            doc = ET.fromstring(archive.read('word/document.xml'))
            body = doc.find('w:body', ns)
            doc_pages = ['']
            for paragraph in body.findall('w:p', ns):
                if paragraph.find('.//w:br[@w:type="page"]', ns) is not None:
                    doc_pages.append('')
                doc_pages[-1] += ' '.join(t.text or '' for t in paragraph.findall('.//w:t', ns)) + '\n'
            assert len(doc_pages) == 4, (lang, 'DOCX page breaks')
            joined = '\n'.join(doc_pages)
            assert DOI in joined and all(x in joined for x in ('CA25177', 'WG1', 'WG6'))
            assert all(name in doc_pages[3] for name in NAMES)
            assert '2221' not in doc_pages[2]
            footer_text = ' '.join(' '.join(t.text or '' for t in ET.fromstring(archive.read(n)).findall('.//w:t', ns))
                                   for n in archive.namelist() if re.fullmatch(r'word/footer\d+\.xml', n))
            assert date in footer_text, (lang, 'DOCX date')
            modified = ET.fromstring(archive.read('docProps/core.xml')).find('dcterms:modified', ns)
            assert modified is not None and modified.text.startswith('2026-11-25')
        report['cv_pages'][lang] = 4
    report['publication_exports'] = 24


def engine_checks(inputs, report):
    node = shutil.which('node') or os.environ.get('CODEX_PRIMARY_RUNTIME_NODE')
    assert node, 'Node is required to check the deployed deterministic answer engines'
    script = r'''
const fs = require('fs'), vm = require('vm');
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = rows.map(row => {
  const sandbox = {window:{}}; vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(row.script, 'utf8'), sandbox, {timeout:5000});
  const engine = sandbox.window.AcademicAnswerEngine.create(row.facts, row.corpus);
  const answers = {};
  for (const [key, question] of Object.entries(row.questions)) {
    engine.reset(); answers[key] = engine.answer(question);
  }
  return {lang:row.lang, answers};
});
process.stdout.write(JSON.stringify(output));
'''
    result = subprocess.run([node, '-e', script], input=json.dumps(inputs, ensure_ascii=False),
                            text=True, capture_output=True, timeout=30, check=True)
    facts_by_language = {row['lang']: row['facts'] for row in inputs}
    for row in json.loads(result.stdout):
        lang, answers = row['lang'], row['answers']
        assert all(a and a.get('text') for a in answers.values()), (lang, answers)
        generic = answers['cost']
        assert {s['url'] for s in generic['sources']} == {'research-network.html#cost-endueai', 'proposal-sciepi-feedback.html'}
        assert all(x in generic['text'] for x in ('CA25177', 'SciEpi', 'WG1', 'WG6'))
        network = answers['endueai']
        assert [s['url'] for s in network['sources']] == ['research-network.html#cost-endueai']
        assert CFG['cost']['role'][lang] in network['text'] and 'SciEpi' not in network['text']
        proposal = answers['sciepi']
        assert [s['url'] for s in proposal['sources']] == ['proposal-sciepi-feedback.html']
        assert 'SciEpi' in proposal['text'] and 'CA25177' not in proposal['text']
        roster = answers['roster']['text']
        assert all(roster.count(name) == 1 for name in NAMES), (lang, roster)
        assert VISITING['locales'][lang]['status_label'] in roster
        assert_current_2221(roster, (lang, 'roster answer'))
        assert DOI in answers['paper']['text'] and '2027' in answers['paper']['text']
        for answer_key, slug in [('kazem_visit', 'kazem-banihashem'), ('omid_visit', 'omid-noroozi')]:
            person = facts_by_language[lang]['people'][slug]
            visit = person['visiting_2221']
            answer = answers[answer_key]
            assert all(visit[field] in answer['text'] for field in ('stage', 'planned_visit', 'scope')), (lang, answer_key, answer)
            assert VISITING_PAGE + '#visit-' + slug in {s['url'] for s in answer['sources']}, (lang, answer_key, 'missing visit source')
            general_stage = person.get('stage', '')
            if general_stage and general_stage != visit['stage']:
                assert general_stage not in answer['text'], (lang, answer_key, 'unrelated general status')
            assert_current_2221(answer['text'], (lang, answer_key))
        report['engine_answers'] += len(answers)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def browser_checks(report):
    from playwright.sync_api import sync_playwright, expect
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(SITE)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as playwright:
            executable = shutil.which('chromium') or shutil.which('google-chrome')
            launch = {'args': ['--no-sandbox']}
            if executable:
                launch['executable_path'] = executable
            browser = playwright.chromium.launch(**launch)
            page = browser.new_page(reduced_motion='reduce')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
            for width in (390, 768, 1440):
                page.set_viewport_size({'width': width, 'height': 1000})
                for lang in LANGS:
                    pre = '' if lang == 'en' else lang + '/'
                    for name in ('publications.html', VISITING_PAGE, 'research-network.html', 'assistant.html'):
                        page.goto(origin + pre + name, wait_until='load')
                        assert page.locator('h1').count() == 1
                        if name == 'publications.html':
                            page.locator('#pub-year').select_option('2027')
                            expect(page.locator('.publication:visible')).to_have_count(1)
                            assert DOI in page.locator('.publication:visible').inner_text()
                            assert re.search(r'\b1\b', page.locator('#pub-count').inner_text())
                            page.locator('#pub-reset').click()
                            expect(page.locator('.publication:visible')).to_have_count(24)
                            report['browser_interactions'] += 2
                        elif name == VISITING_PAGE:
                            assert page.locator('.visiting-plan-card:visible').count() == 4
                        elif name == 'assistant.html':
                            for key in ('cost', 'roster'):
                                page.locator('#chat-clear').click()
                                page.locator('#chat-question').fill(QUESTIONS[lang][key])
                                page.locator('#chat-send').click()
                                answer = page.locator('.chat-assistant').last
                                expect(answer).to_contain_text('CA25177' if key == 'cost' else NAMES[0])
                                value = answer.inner_text()
                                if key == 'cost':
                                    assert all(x in value for x in ('CA25177', 'SciEpi', 'WG1', 'WG6'))
                                    assert answer.locator('a[href="research-network.html#cost-endueai"]').count() == 1
                                    assert answer.locator('a[href="proposal-sciepi-feedback.html"]').count() == 1
                                else:
                                    assert all(n in value for n in NAMES)
                                    assert_current_2221(value, (lang, 'browser roster'))
                                report['browser_interactions'] += 1
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (lang, width, name, 'horizontal overflow')
                        report['browser_page_loads'] += 1
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    assert report['browser_page_loads'] == 36
    assert not report['errors'], report['errors']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true', help='Run the bounded Chromium interaction/layout gate')
    args = parser.parse_args()
    report = {'result': 'running', 'languages': [], 'static_pages': 0, 'cv_pages': {},
              'publication_exports': 0, 'engine_answers': 0, 'browser_page_loads': 0,
              'browser_interactions': 0, 'errors': []}
    dois, inputs = static_checks(report)
    download_checks(dois, report)
    engine_checks(inputs, report)
    if args.browser:
        browser_checks(report)
    report['result'] = 'passed'
    (ROOT / 'academic-updates-test-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
