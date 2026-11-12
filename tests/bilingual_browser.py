#!/usr/bin/env python3
"""Bilingual UI checks. --offline renders inline HTML when browser navigation is unavailable."""
from pathlib import Path
from urllib.parse import urlsplit
import json,threading,http.server,socketserver,argparse,shutil
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';reports=ROOT/'review-v4';reports.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()
class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(SITE),**kw)
    def log_message(self,*a):pass
server=None;BASE='https://huseyinates38.github.io/'
if not args.offline:
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
    threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_address[1]}/'
manifest=json.loads((SITE/'deployment.json').read_text());failures=[];errors=[];checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') if args.offline else None)
    def load(name,width=1440,js=True):
        page=browser.new_page(viewport={'width':width,'height':1000},java_script_enabled=js,reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        if args.offline:
            doc=Soup((SITE/name).read_text(),'html.parser');scripts=[]
            for n in list(doc.select('link[rel=stylesheet]')):
                path=((SITE/name).parent/urlsplit(n['href']).path).resolve()
                style=doc.new_tag('style');style.string=path.read_text();n.replace_with(style)
            for n in list(doc.select('script[src]')):
                scripts.append(((SITE/name).parent/urlsplit(n['src']).path).resolve().read_text());n.decompose()
            base=doc.new_tag('base',attrs={'href':BASE+name});doc.head.insert(0,base)
            page.set_content(str(doc),wait_until='domcontentloaded')
            if js:
                for script in scripts:page.add_script_tag(content=script)
        else:page.goto(BASE+name,wait_until='load')
        return page
    for width in [360,768,1440]:
        for name in manifest['pages']:
            page=load(name,width)
            extent=page.evaluate('({vw:innerWidth,sw:document.documentElement.scrollWidth})')
            if extent['sw']>extent['vw']+2:
                failures.append([name,width,extent]);page.screenshot(path=str(reports/('overflow-'+name.replace('/','-')+'.png')))
            assert page.locator('[data-site-lang="tr"]').is_visible(),(name,width,'TR not visible')
            assert page.locator('[data-site-lang="en"]').is_visible(),(name,width,'EN not visible')
            page.close()
    checks.append('294 rendered layouts; both language links visible at all widths')
    for lang in ['en','tr']:
        prefix='tr/' if lang=='tr' else ''
        page=load(prefix+'index.html',390);page.locator('.menu-button').click()
        assert page.locator('#main-navigation a[href="projects.html"]').is_visible()
        page.keyboard.press('Escape');assert page.locator('.menu-button').get_attribute('aria-expanded')=='false';page.close()
        page=load(prefix+'publications.html',390);page.locator('#pub-query').fill('Ates');assert page.locator('.publication:visible').count()==23
        page.locator('#pub-year').select_option('2026');assert page.locator('.publication:visible').count()==4
        if not args.offline:
            page.reload();assert page.locator('#pub-year').input_value()=='2026'
        page.locator('#pub-reset').click();assert page.locator('.publication:visible').count()==23;page.close()
        page=load(prefix+'search.html',390);page.locator('#site-query').fill('Tugce');assert page.locator('#site-search-results').get_by_text('Tuğçe Ünsal',exact=True).is_visible()
        page.locator('#site-query').fill('geri bildirim');assert page.locator('#site-search-results li').count()>0
        page.locator('#site-query').fill('zzzz-not-found');assert page.locator('#site-search-results li').count()==0
        assert ('Sonuç bulunamadı' if lang=='tr' else 'No matches') in page.locator('#site-search-status').inner_text();page.close()
        page=load(prefix+'projects.html',390);page.locator('#project-programme').select_option('BAP');assert page.locator('[data-programme]:visible').count()==2;page.close()
        page=load(prefix+'feedback-explorer.html',390);page.locator('#feedback-mode').select_option('reflective');assert page.locator('[data-mode]:visible').count()==1
        other='en' if lang=='tr' else 'tr'
        if not args.offline:
            page.locator(f'[data-site-lang="{other}"]').click()
            assert page.locator('html').get_attribute('lang')==other
            assert page.locator('#feedback-mode').input_value()=='reflective'
            assert page.locator('[data-mode]:visible').count()==1
        page.close()
        page=load(prefix+'resource-feedback.html',390);assert not page.locator('[data-language-picker]').count();assert page.locator('[data-print]').count()==1;page.close()
        page=load(prefix+'research.html',390);page.locator('[data-panel]').nth(1).click();assert page.locator('[data-panel]').nth(1).get_attribute('aria-expanded')=='true';page.close()
        checks.append(lang+': menu, accents, year filters, localized search, project filter, feedback and framework passed')
    for name,width,label in [('tr/index.html',1440,'home-tr-desktop'),('tr/index.html',390,'home-tr-mobile'),('index.html',1440,'home-en-desktop'),('tr/team.html',1440,'team-tr-desktop'),('tr/proposals.html',390,'proposals-tr-mobile')]:
        page=load(name,width);page.screenshot(path=str(reports/(label+'.png')),full_page=True);page.close()
    for name in ['tr/index.html','tr/resource-feedback.html','tr/search.html']:
        page=load(name,390,False);assert page.locator('h1').is_visible();assert page.locator('[data-site-lang="en"]').is_visible()
        if name=='tr/search.html':assert page.locator('#search-directory').is_visible()
        page.close()
    browser.close()
if server:server.shutdown()
report={'release':'4.0','mode':'offline-inline-render' if args.offline else 'local-http-browser','pages':len(manifest['pages']),'viewport_widths':[360,768,1440],'rendered_layouts':len(manifest['pages'])*3,'checks':checks,'url_switch_and_reload_tested':not args.offline,'overflow_failures':failures,'javascript_errors':errors,'status':'passed' if not errors and not failures else 'failed'}
(ROOT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
quality=json.loads((SITE/'quality-report.json').read_text());quality['browser_checks']=report
(SITE/'quality-report.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors or failures:raise SystemExit('Browser checks failed')
