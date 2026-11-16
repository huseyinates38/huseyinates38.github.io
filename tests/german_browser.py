#!/usr/bin/env python3
"""Final German locale tests: real public-record replies, layouts and all links.
No claim of real LLM generation or independent accessibility certification.
"""
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from urllib.parse import urlsplit,unquote
import functools,http.server,threading,json,re,shutil,hashlib,sys,base64,mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'
OFFLINE='--offline' in sys.argv
@functools.lru_cache(maxsize=None)
def inline(name):
    source=SITE/name;s=read(source)
    s.head.insert(0,s.new_tag('base',href='https://german-test.invalid/'+name))
    for tag in list(s.select('link[rel=stylesheet]')):
        path=(source.parent/urlsplit(tag['href']).path).resolve()
        if path.is_file():
            new=s.new_tag('style');new.string=path.read_text();tag.replace_with(new)
        else:tag.decompose()
    for tag in list(s.select('script[src]')):
        path=(source.parent/urlsplit(tag['src']).path).resolve()
        if path.is_file():
            del tag['src'];tag.attrs.pop('defer',None);tag.string=path.read_text();tag.extract();s.body.append(tag)
        else:tag.decompose()
    for tag in s.select('img[src]'):
        path=(source.parent/urlsplit(tag['src']).path).resolve()
        if path.is_file():tag['src']='data:'+(mimetypes.guess_type(path.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(path.read_bytes()).decode()
    return str(s)


def read(p):return Soup(p.read_text(encoding='utf-8'),'html.parser')
def text(x):return x.get_text(' ',strip=True) if x else ''
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    report={'result':'running','html_pages':0,'layout_checks':0,'interactive_checks':0,'german_pages':70,'live_model_inference':False,'offline_preview':OFFLINE,'errors':[]}
    names=sorted(p.name for p in SITE.glob('*.html'))
    assert len(names)==70
    parsed={}
    for pre,lang in [('', 'en'),('tr/','tr'),('de/','de')]:
        for name in names:
            path=SITE/(pre+name);s=read(path);parsed[pre+name]=s
            assert s.html['lang']==lang,(pre,name)
            assert len(s.select('h1'))==1
            assert s.select_one('link[rel="canonical"]')['href'].endswith('/'+pre+name),(pre,name)
            language=s.select('.site-language a');assert {a['lang'] for a in language}=={'de','en','tr'}
            assert len(s.select('.site-language [aria-current="page"]'))==1
            assert s.select_one('.site-language [aria-current="page"]')['lang']==lang
            assert {a['hreflang'] for a in s.select('link[rel="alternate"][hreflang]')}=={'en','tr','de','x-default'}
            ids=[n['id'] for n in s.select('[id]')];assert len(ids)==len(set(ids)),(pre,name,'duplicate IDs')
            report['html_pages']+=1
    for name,s in parsed.items():
        for tag in s.select('[href],[src]'):
            for attr in ('href','src'):
                value=tag.get(attr,'');u=urlsplit(value)
                if not value or u.scheme or u.netloc:continue
                p=((SITE/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (SITE/name).parent/unquote(u.path) if u.path else SITE/name).resolve()
                if p.is_dir():p=p/'index.html'
                assert p.is_relative_to(SITE.resolve()) and p.is_file(),(name,value)
                relative=p.relative_to(SITE).as_posix()
                if u.fragment and relative in parsed and '=' not in u.fragment:
                    assert parsed[relative].find(id=unquote(u.fragment)),(name,value,'missing anchor')
    manifest=json.loads((SITE/'deployment.json').read_text());assert manifest['page_count']==210 and manifest['languages']==['en','tr','de']
    # Public evidence and source-language downloads must not be altered by localisation.
    for name in ('about.html','proposals.html','proposal-feedback-fading.html'):
        en=parsed[name];de=parsed['de/'+name]
        assert [t['datetime'] for t in en.select('time[datetime]')]==[t['datetime'] for t in de.select('time[datetime]')]
    for src,dest in zip(parsed['publications.html'].select('.publication'),parsed['de/publications.html'].select('.publication')):
        assert text(src)==text(dest)
    for name in names:
        original=[a['href'].split('downloads/',1)[1] for a in parsed[name].select('a[href]') if 'downloads/' in a['href']]
        german=[a['href'].split('downloads/',1)[1] for a in parsed['de/'+name].select('a[href]') if 'downloads/' in a['href']]
        assert original==german,name
    naomi=parsed['de/person-naomi-winstone.html'];assert '2219' in text(naomi.main) and 'Gastgeberin' in text(naomi.main)
    assert not re.search(r'Manuskript|Makale|co-author',text(naomi.main),re.I)
    assert naomi.select_one('a[href="proposal-feedback-fading.html"]')
    team=parsed['de/team.html'];assert len(team.select('#project-team-3501 .person-card'))==7 and len(team.select('#project-team-aub-stem .person-card'))==4
    assert team.select_one('#project-team-aub-stem [data-person="ahmet-sami-konca"]')
    assert len(parsed['de/person-yesim-taktat-ates.html'].select('[data-project-record="study"] a'))==2
    index=json.loads(parsed['de/search.html'].select_one('#site-search-data').string)
    knowledge=json.loads(parsed['de/assistant.html'].select_one('#assistant-knowledge').string)
    facts=json.loads(parsed['de/assistant.html'].select_one('#assistant-facts').string)
    assert not any('person-tugce-unsal' in r['url'] for r in index+knowledge['records'])
    assert facts['lang']=='de' and len(facts['projects']['aub']['members'])==4
    assert 'Manuscript' not in facts['people']['naomi-winstone']['stage']
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
    previews=ROOT/'german-previews';previews.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
            page=browser.new_page(reduced_motion='reduce');page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
            def load(name):
                if OFFLINE:page.set_content(inline('de/'+name),wait_until='load')
                else:page.goto(base+'de/'+name,wait_until='domcontentloaded')
            for width in (390,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                for name in names:
                    load(name)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,width,'overflow',page.evaluate('document.documentElement.scrollWidth'))
                    report['layout_checks']+=1
                for name in ('index.html','team.html','assistant.html'):
                    if width in (390,1440):
                        load(name);page.evaluate('document.querySelectorAll("img").forEach(x=>x.loading="eager")')
                        page.evaluate('async()=>await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))')
                        page.screenshot(path=str(previews/f'{name[:-5]}-{width}.png'),full_page=True)
                load('team.html');page.locator('#people-query').fill('Yesim');assert page.locator('.person-card:visible').count()==2
                assert 'Einträgen' in page.locator('#people-count').inner_text();page.locator('#people-reset').click()
                assert page.locator('.person-card:visible').count()==len(team.select('.person-card'))
                for institution in ('Surrey','Twente'):
                    logo=page.locator(f'.institution-mark.dark img[alt*="{institution}"]').first
                    assert logo.evaluate('(n)=>getComputedStyle(n.parentElement).backgroundColor')=='rgb(23, 55, 70)'
                page.locator('#people-query').fill('Naomi');assert '2219' in page.locator('.person-card:visible').inner_text()
                load('research-network.html');page.locator('#network-query').fill('Deutschland');assert page.locator('.network-country:visible').count()==1
                assert 'Ländern' in page.locator('#network-count').inner_text()
                load('search.html');page.locator('#site-query').fill('selbstreguliert');assert page.locator('#site-search-results li').count()>0
                assert 'Ergebnisse' in page.locator('#site-search-status').inner_text()
                page.locator('#site-query').fill('zz-not-found-83219');assert 'Keine Treffer' in page.locator('#site-search-status').inner_text()
                page.locator('#site-search-reset').click();assert page.locator('#site-query').input_value()==''
                load('publications.html');page.locator('#pub-year').select_option('2026');assert page.locator('.publication:visible').count()>0
                assert 'ausgewählte' in page.locator('#pub-count').inner_text();page.locator('#pub-reset').click();assert page.locator('.publication:visible').count()==23
                load('feedback-explorer.html');page.locator('[data-feedback-picker]').select_option('reflective');assert page.locator('[data-mode]:visible').count()==1
                page.locator('[data-feedback-picker]').select_option('all');assert page.locator('[data-mode]:visible').count()==3
                load('assistant.html');assert page.locator('#cloud-enable').is_disabled()
                def ask(q):
                    page.locator('#chat-question').fill(q);page.locator('#chat-send').click()
                    answer=page.locator('.chat-assistant').last
                    return answer.inner_text()
                a=ask('Wer gehört zum 3501-Team?');assert all(x in a for x in ('Gökhan İnce','Yeşim Taktat Ateş','İbrahim Delen')) and 'Entscheidung' in a
                a=ask('Und wurde es gefördert?');assert '13. November 2026' in a and 'Entscheidung' in a
                page.locator('#chat-clear').click()
                a=ask('An welchen Projekten ist Yeşim Taktat Ateş beteiligt?');assert '3501' in a and 'VAE' in a
                a=ask('Und wo arbeitet sie?');assert 'unabhängig' in a
                page.locator('#chat-clear').click()
                a=ask('Ist Naomi Winstone an einem Artikel beteiligt?');assert 'nicht ausgewiesen' in a and '2219' in a
                page.locator('#chat-clear').click()
                a=ask('Wer gehört zum AÜB-Team?');assert 'Ahmet Sami Konca' in a and 'Naciye' in a
                a=ask('<img src=x onerror=alert(1)> zzunknown123');assert page.locator('#chat-log img').count()==0
                page.locator('#chat-clear').click();assert page.locator('.chat-message').count()==1
                if not OFFLINE:assert page.evaluate('localStorage.length')==0
                if width==390:
                    page.locator('.menu-button').click();assert page.locator('#main-navigation').is_visible()
                report['interactive_checks']+=21
            # Real route switching runs in CI; offline previews cannot navigate locally.
            if not OFFLINE:
                page.goto(base+'de/team.html#project-team-aub-stem',wait_until='domcontentloaded')
                page.locator('.site-language a[lang="tr"]').click()
                assert page.url.endswith('/tr/team.html#project-team-aub-stem')
                page.locator('.site-language a[lang="de"]').click();assert page.url.endswith('/de/team.html#project-team-aub-stem')
            browser.close()
    finally:server.shutdown()
    assert not report['errors'],report['errors']
    report['result']='passed';(ROOT/'german-test-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
