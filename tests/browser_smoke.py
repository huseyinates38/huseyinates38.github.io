#!/usr/bin/env python3
"""Rendered regression tests; not WCAG certification or an academic-content audit.
Use --offline for an in-memory preview in environments without browser navigation.
"""
from __future__ import annotations
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import threading
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    manifest=json.loads((SITE/'deployment.json').read_text())
    pages=manifest['pages']; errors=[]; report={'release':'3.1','mode':'offline-inline-preview' if args.offline else 'local-http-browser','layout_checks':0,'interactions':[]}
    assert 'search.html' in pages and len(pages)>=37, 'Search or existing content missing'
    for path in (SITE/'assets').glob('*.css'):
        assert 'fonts.googleapis.com' not in path.read_text(), 'Remote font import remains'
    for name in ['resources.html','site-notes.html']:
        text=(SITE/name).read_text();assert 'prototypes / Version 1.0' not in text and 'Resource prototypes: version 1.0.' not in text
    index_soup=Soup((SITE/'search.html').read_text(),'html.parser')
    records=json.loads(index_soup.find(id='site-search-data').string)
    assert len(records)>=len(pages)-2 and len({r['url'] for r in records})==len(records)
    assert all((SITE/urlsplit(r['url']).path).is_file() for r in records)
    report['search_records']=len(records)
    server=None
    if not args.offline:
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}/'
    def record(value):report['interactions'].append(value)
    with sync_playwright() as pw:
        executable=(shutil.which('chromium') or shutil.which('google-chrome')) if args.offline else None
        browser=pw.chromium.launch(executable_path=executable,args=['--no-sandbox'])
        def load(name,width=1440,javascript=True):
            page=browser.new_page(viewport={'width':width,'height':1000},java_script_enabled=javascript,reduced_motion='reduce')
            page.on('pageerror',lambda error: errors.append(str(error)))
            if args.offline:
                soup=Soup((SITE/name).read_text(),'html.parser'); scripts=[]
                for node in list(soup.select('link[rel=stylesheet]')):
                    style=soup.new_tag('style');style.string=(SITE/urlsplit(node['href']).path).read_text();node.replace_with(style)
                for node in list(soup.select('script[src]')):
                    scripts.append((SITE/urlsplit(node['src']).path).read_text());node.decompose()
                page.set_content(str(soup),wait_until='domcontentloaded')
                if javascript:
                    for script in scripts:page.add_script_tag(content=script)
            else:
                page.goto(base+name,wait_until='load')
            page.wait_for_timeout(60)
            return page
        for width in [360,768,1440]:
            for name in pages:
                page=load(name,width)
                dimensions=page.evaluate('({actual:document.documentElement.scrollWidth, viewport:innerWidth})')
                if dimensions['actual']>dimensions['viewport']+1:
                    print(page.evaluate("() => [...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&e.getBoundingClientRect().width).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,180),width:e.getBoundingClientRect().width}))"))
                    page.screenshot(path=str(ROOT/'overflow-smoke.png'),full_page=True)
                assert dimensions['actual']<=dimensions['viewport']+1,f'Horizontal page overflow: {name}/{width}: {dimensions}'
                assert page.locator('h1').count()==1 and page.locator('main#main-content').count()==1
                assert page.locator('#main-navigation a[href="search.html"]').count()==1
                report['layout_checks']+=1;page.close()
        page=load('publications.html')
        total_publications=page.locator('.publication').count()
        for value in ['Ateş','Ates','ATES']:
            page.locator('#pub-query').fill(value);assert page.locator('.publication:visible').count()==total_publications,value
        page.locator('#pub-query').fill('VR');assert page.locator('.publication:visible').count()>0
        page.locator('#pub-query').fill('Ates');page.locator('#pub-year').select_option('2025')
        expected=page.locator('.publication:visible').count();assert expected==page.locator('.publication[data-year="2025"]').count() and expected>0
        if not args.offline:
            assert 'q=Ates' in page.url and 'year=2025' in page.url
            page.reload();assert page.locator('#pub-query').input_value()=='Ates' and page.locator('.publication:visible').count()==expected
            record('publication filters survive refresh through URL fragment')
        page.locator('#pub-reset').click();assert page.locator('.publication:visible').count()==total_publications
        page.locator('#pub-query').fill('nomatch-315zz');assert page.locator('.no-results').is_visible()
        record('publication accents, abbreviations, combined year filter, reset and empty state');page.close()
        page=load('search.html')
        assert page.locator('#site-search-results>li').count()==12
        page.locator('#site-search-more').click();assert page.locator('#site-search-results>li').count()==24
        page.locator('#site-query').fill('Tugce');assert 'Tuğçe' in page.locator('#site-search-results').inner_text()
        page.locator('#site-query').fill('VR');assert page.locator('#site-search-results>li').count()>0
        page.locator('#site-category').select_option('people');assert page.locator('#site-search-results>li').count()>0
        assert all(t=='People' for t in page.locator('#site-search-results .search-kind').all_text_contents())
        page.locator('#site-search-reset').click();page.locator('#site-query').fill('feedback')
        if not args.offline:
            page.reload();assert page.locator('#site-query').input_value()=='feedback';record('shareable site search survives refresh')
        page.locator('#site-query').fill('<img src=x onerror=alert(1)>');assert page.locator('#site-search-results img').count()==0 and 'No matches' in page.locator('#site-search-status').inner_text()
        page.locator('#site-search-reset').click();page.locator('#site-query').fill('CV')
        assert page.locator('#site-search-results a[href$=".pdf"]').count()>0
        record('site search, Turkish names, category filter, pagination, reset, safe text and CV retrieval')
        if args.offline:page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(ROOT/'search-desktop.png'),full_page=True)
        page.close()
        page=load('feedback-explorer.html',360)
        page.locator('[data-language-picker]').select_option('tr');page.locator('[data-feedback-picker]').select_option('hybrid')
        assert page.locator('[data-lang="en"]').is_hidden() and page.locator('[data-mode]:visible').count()==1
        if not args.offline:
            page.reload();assert page.locator('[data-language-picker]').input_value()=='tr' and page.locator('[data-feedback-picker]').input_value()=='hybrid'
            record('language and feedback mode survive refresh')
        record('Turkish language and feedback mode controls');page.close()
        page=load('index.html',360);page.locator('.menu-button').click();assert page.locator('#main-navigation').is_visible()
        page.keyboard.press('Escape');assert page.locator('.menu-button').get_attribute('aria-expanded')=='false'
        record('mobile navigation opens and closes with Escape');page.close()
        page=load('projects.html',360);page.locator('#project-programme').select_option(index=1);assert page.locator('[data-programme]:visible').count()>0
        record('project filter');page.close()
        for name in ['index.html','resource-feedback.html','search.html']:
            page=load(name,360,javascript=False);assert page.locator('#main-navigation').is_visible()
            if name=='search.html':assert page.locator('#search-directory').is_visible()
            if name=='resource-feedback.html':assert page.locator('[data-lang="tr"]').is_visible()
            page.close()
        record('mobile navigation, bilingual resources and search directory without JavaScript')
        if args.offline:
            for width in [390,1440]:
                page=load('index.html',width);page.screenshot(path=str(ROOT/f'homepage-{width}.png'),full_page=True);page.close()
        browser.close()
    if server:server.shutdown()
    assert not errors,errors
    report['console_errors']=errors
    report['limitations']=['not an independent WCAG certification','not assistive-technology testing','not publication fact checking']
    (ROOT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    quality=json.loads((SITE/'quality-report.json').read_text())
    quality['browser_checks']=report
    (SITE/'quality-report.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
