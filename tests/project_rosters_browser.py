#!/usr/bin/env python3
"""Final rendered-roster tests; run after assistant generation, not its legacy snapshots."""
from pathlib import Path
import base64, functools, http.server, json, mimetypes, shutil, sys, threading
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'
OFFLINE='--offline' in sys.argv
BEFORE_ASSISTANT='--before-assistant' in sys.argv

@functools.lru_cache(maxsize=None)
def inline(name):
    source=SITE/name; doc=Soup(source.read_text(),'html.parser')
    for n in list(doc.select('link[rel=stylesheet]')):
        target=(source.parent/urlsplit(n['href']).path).resolve()
        if target.is_file():
            style=doc.new_tag('style'); style.string=target.read_text(); n.replace_with(style)
        else:
            n.decompose()
    for n in list(doc.select('script[src]')):
        target=(source.parent/urlsplit(n['src']).path).resolve()
        if target.is_file():
            n.attrs.pop('src'); n.string=target.read_text()
        else:
            n.decompose()
    for n in doc.select('img[src]'):
        target=(source.parent/urlsplit(n['src']).path).resolve()
        if target.is_file():
            n['src']='data:'+(mimetypes.guess_type(target.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(target.read_bytes()).decode()
    return str(doc)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    registry=json.loads((ROOT/'content/project-rosters.json').read_text())
    report={'result':'running','layout_checks':0,'filter_checks':0,'languages':['en','tr'],
            'assistant_data_checked':not BEFORE_ASSISTANT,'errors':[]}
    for pre in ('','tr/'):
        team=Soup((SITE/pre/'team.html').read_text(),'html.parser')
        for project in registry['projects']:
            expected=[m['slug'] for m in project['members']]
            g=team.select_one('#project-team-'+project['id'])
            assert [c['data-person'] for c in g.select('.person-card')]==expected
            assert not g.select('.project-team-note,.relationship-stage')
            p=Soup((SITE/pre/project['page']).read_text(),'html.parser')
            s=p.select_one('#'+project['section_id'])
            assert [c['data-person'] for c in s.select('.person-card')]==expected
            assert p.select_one('.status-pill'), 'The application status must remain visible'
            for member in expected:
                person=Soup((SITE/pre/('person-'+member+'.html')).read_text(),'html.parser')
                assert person.select_one('[data-project-record="study"] a[href="'+project['page']+'"]')
        assert len(team.select('[data-person="ahmet-sami-konca"]'))==2
        assert len(team.select('[data-person="yesim-taktat-ates"]'))==2
        assert team.select_one('#collaborators [data-person="ahmet-sami-konca"]')
        assert not team.select_one('#project-team-3501 [data-person="ahmet-sami-konca"]')
        if not BEFORE_ASSISTANT:
            assistant=Soup((SITE/pre/'assistant.html').read_text(),'html.parser')
            facts=json.loads(assistant.select_one('#assistant-facts').string)
            for key,groupid in [('3501','3501'),('aub','aub-stem')]:
                expected=next(p['members'] for p in registry['projects'] if p['id']==groupid)
                slugs=[m['slug'] for m in facts['projects'][key]['members']]
                assert slugs==[m['slug'] for m in expected] and len(slugs)==len(set(slugs))
            assert any(x['url']=='proposal-turkiye-uae-stem.html' for x in facts['people']['ahmet-sami-konca']['studies'])
            knowledge=json.loads(assistant.select_one('#assistant-knowledge').string)
            assert not any('da bu başvuruda görev almaktadır.' in r['text'] or 'also participates in this proposal.' in r['text'] for r in knowledge['records'])
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    previews=ROOT/'project-roster-previews'; previews.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
            page=browser.new_page(reduced_motion='reduce')
            page.on('pageerror',lambda e: report['errors'].append(str(e)))
            for width in (390,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                for pre in ('','tr/'):
                    for name in ['team.html', 'person-ahmet-sami-konca.html']+[project['page'] for project in registry['projects']]:
                        if OFFLINE: page.set_content(inline(pre+name),wait_until='load')
                        else: page.goto(base+pre+name,wait_until='domcontentloaded')
                        page.evaluate('document.querySelectorAll("img").forEach(i=>i.loading="eager")')
                        page.evaluate('async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))}')
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(pre,name,width)
                        assert page.locator('h1').count()==1
                        report['layout_checks']+=1
                        if name=='team.html':
                            card=page.locator('#project-team-aub-stem [data-person="ahmet-sami-konca"]')
                            assert card.count()==1 and card.is_visible()
                            assert card.locator('.institution-name').count()==1
                            assert card.locator('img').evaluate('(i)=>i.complete&&i.naturalWidth>0')
                            assert card.locator('.micro-label').text_content().strip() == ('Araştırmacı' if pre else 'Researcher')
                            assert page.locator('#project-team-aub-stem .project-team-note').count()==0
                            count=page.locator('.person-card').count()
                            page.locator('#people-query').fill('Ahmet Sami Konca')
                            assert page.locator('.person-card:visible').count()==2
                            assert page.locator('#project-team-aub-stem').is_visible()
                            assert page.locator('#collaborators').is_visible()
                            assert page.locator('#project-team-3501').is_hidden()
                            page.locator('#people-query').fill('Yeşim Taktat Ateş')
                            assert page.locator('#project-team-3501').is_visible() and page.locator('#project-team-aub-stem').is_visible()
                            page.locator('#people-reset').click()
                            assert page.locator('.person-card:visible').count()==count
                            report['filter_checks']+=1
                            if pre and width in (390,1440):
                                page.locator('#project-team-aub-stem').screenshot(path=str(previews/f'aub-team-{width}.png'))
            browser.close()
    finally:
        server.shutdown()
    assert not report['errors'],report['errors']
    report['result']='passed'
    (ROOT/'project-roster-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
