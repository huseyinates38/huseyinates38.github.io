#!/usr/bin/env python3
"""Final three-language roster, source parity and browser checks for TÜBİTAK 1002."""
from __future__ import annotations
import functools
import base64
import mimetypes
import sys
import http.server
import json
import shutil
import threading
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT/'_site'
CFG = json.loads((ROOT/'content/project-1002-team.json').read_text())
SLUGS = [m['slug'] for m in CFG['members']]
NAMES = [m['name'] for m in CFG['members']]
OFFLINE = '--offline' in sys.argv


@functools.lru_cache(maxsize=None)
def inline(name):
    path = SITE/name
    s = Soup(path.read_text(), 'html.parser')
    for tag in list(s.select('link[rel=stylesheet]')):
        f = (path.parent/urlsplit(tag['href']).path).resolve()
        if f.is_file():
            new = s.new_tag('style'); new.string=f.read_text(); tag.replace_with(new)
        else:
            tag.decompose()
    for tag in list(s.select('script[src]')):
        f = (path.parent/urlsplit(tag['src']).path).resolve()
        if f.is_file():
            del tag['src']; tag.string=f.read_text()
        else:
            tag.decompose()
    for tag in s.select('img[src]'):
        f = (path.parent/urlsplit(tag['src']).path).resolve()
        if f.is_file():
            tag['src']='data:'+(mimetypes.guess_type(f.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(f.read_bytes()).decode()
    return str(s)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def static_checks():
    report = {'result': 'running', 'languages': list(CFG['locales']), 'rosters': 0,
              'layout_checks': 0, 'interaction_checks': 0, 'errors': []}
    for lang in CFG['locales']:
        folder = SITE/('' if lang=='en' else lang)
        docs = {p.name: Soup(p.read_text(), 'html.parser') for p in folder.glob('*.html')}
        assert len(docs) == 70
        for name, s in docs.items():
            ids = [n['id'] for n in s.select('[id]')]
            assert len(ids) == len(set(ids)), (lang, name, 'duplicate id')
        team = docs['team.html'].select_one('#project-team-1002')
        project = docs[CFG['page']].select_one('#'+CFG['section_id'])
        for node in (team, project):
            assert [x['data-person'] for x in node.select('.person-card')] == SLUGS
            assert len(node.select('.institution-mark img[src*="kaeu.png"]')) == 4
            assert not node.select('.project-team-note')
            report['rosters'] += 1
        for member in CFG['members']:
            detail = project.select_one('#member-'+member['slug'])
            assert member['contribution'][lang] in detail.get_text()
            if member.get('profile'):
                s = docs[member['profile']]
                assert s.select_one('[data-project-record="study"] a[href="'+CFG['page']+'"]')
                assert member['contribution'][lang] in s.select_one('[data-1002-contribution]').get_text()
        assert len(docs['team.html'].select('#project-team-3501 .person-card')) == 7
        assert len(docs['team.html'].select('#project-team-aub-stem .person-card')) == 4
        naomi = docs['person-naomi-winstone.html'].main.get_text(' ',strip=True).lower()
        assert not any(w in naomi for w in ('manuscript','makale','manuskript'))
        assert '2219' in naomi and 'surrey' in naomi
        facts = json.loads(docs['assistant.html'].select_one('#assistant-facts').string)
        assert [m['slug'] for m in facts['projects']['1002']['members']] == SLUGS
        assert '2026' in facts['projects']['1002']['stage']
        assert facts['projects']['1002']['lead'] == CFG['principal_investigator']
        for member in CFG['members']:
            if not member.get('discovery_excluded'):
                f = facts['people'][member['slug']]
                assert f['contribution'] == member['contribution'][lang]
                assert any(x['url']==CFG['page'] for x in f['studies'])
        assert 'tugce-unsal' not in facts['people']
        search = json.loads(docs['search.html'].select_one('#site-search-data').string)
        assert not any(r['url']=='person-tugce-unsal.html' for r in search)
        assert any('mercan oz' in r['key'] and r['url']==CFG['page'] for r in search)
        for name in ('team.html',CFG['page'],'person-abdulkadir-aydin.html','person-tugce-unsal.html'):
            for a in docs[name].select('a[href]'):
                u=urlsplit(a['href'])
                if u.scheme or u.netloc:continue
                target=(folder/(unquote(u.path) or name)).resolve()
                if target.is_dir():target=target/'index.html'
                assert target.is_file(),(lang,name,a['href'])
                if u.fragment and target.suffix=='.html':
                    dest=Soup(target.read_text(),'html.parser')
                    assert dest.find(id=unquote(u.fragment)),(lang,name,a['href'])
    return report


def main():
    report=static_checks()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    previews=ROOT/'project-1002-previews';previews.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
            page=browser.new_page(reduced_motion='reduce')
            page.on('pageerror',lambda error: report['errors'].append(str(error)))
            page.route('**/*',lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
            for width in (390,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                for lang in CFG['locales']:
                    pre='' if lang=='en' else lang+'/'
                    for name in ('team.html',CFG['page'],'person-abdulkadir-aydin.html','person-tugce-unsal.html','assistant.html','search.html'):
                        page.set_content(inline(pre+name),wait_until='load') if OFFLINE else page.goto(base+pre+name,wait_until='domcontentloaded')
                        assert page.locator('h1').count()==1
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(lang,width,name)
                        report['layout_checks']+=1
                        if name=='team.html':
                            assert page.locator('#project-team-1002 .person-card').count()==4
                            page.locator('#people-query').fill('Mercan Oz')
                            assert page.locator('#project-team-1002').is_visible()
                            assert page.locator('#project-team-3501').is_hidden()
                            assert page.locator('#project-team-aub-stem').is_hidden()
                            page.locator('#people-reset').click()
                            if lang=='tr' and width in (390,1440):
                                page.locator('#project-team-1002').scroll_into_view_if_needed()
                                page.evaluate('document.querySelectorAll("img").forEach(x=>x.loading="eager")')
                                page.evaluate('async()=>{await Promise.all([...document.images].map(x=>x.decode().catch(()=>null)))}')
                                page.locator('#project-team-1002').screenshot(path=str(previews/f'1002-team-{width}.png'))
                            report['interaction_checks']+=3
                        if name=='assistant.html':
                            question={'en':'Who is on the 1002 team?','tr':'1002 ekibinde kimler var?','de':'Wer gehört zum 1002-Team?'}[lang]
                            page.locator('#chat-question').fill(question);page.locator('#chat-send').click()
                            answer=page.locator('.chat-assistant').last
                            assert all(n in answer.inner_text() for n in NAMES),answer.inner_text()
                            assert answer.locator('a[href="project-space-debris.html"]').count()>=1
                            page.locator('#chat-clear').click()
                            question={'en':'What is Mercan Öz’s contribution?','tr':'Mercan Öz katkısı nedir?','de':'Welche Aufgaben hat Mercan Öz?'}[lang]
                            page.locator('#chat-question').fill(question);page.locator('#chat-send').click()
                            assert CFG['members'][2]['contribution'][lang] in page.locator('.chat-assistant').last.inner_text()
                            report['interaction_checks']+=2
            browser.close()
    finally:
        server.shutdown()
    assert not report['errors'],report['errors']
    report['result']='passed'
    (ROOT/'project-1002-test-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
