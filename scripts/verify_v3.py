#!/usr/bin/env python3
"""Static release gate and optional DOI/link health report.
No automated test claims full WCAG or academic-content validation.
"""
from pathlib import Path
import argparse, concurrent.futures, csv, hashlib, json, re, sys, zipfile
from urllib.parse import urlsplit, unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup as Soup

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'

def validate():
    errors=[];pages={}
    for p in SITE.glob('*.html'):
        s=Soup(p.read_text(),'html.parser');pages[p.name]=s
        if len(s.select('h1'))!=1:errors.append(p.name+': expected exactly one h1')
        if not s.select_one('main#main-content'):errors.append(p.name+': missing main landmark')
        if not s.title or not s.html.get('lang'):errors.append(p.name+': missing title or language')
        ids=[a['id'] for a in s.select('[id]')]
        if len(ids)!=len(set(ids)):errors.append(p.name+': duplicate IDs')
        for img in s.select('img'):
            if not img.has_attr('alt'):errors.append(p.name+': missing image alternative')
        for inp in s.select('input:not([type="hidden"]),select,textarea'):
            if not (inp.get('aria-label') or inp.get('aria-labelledby') or inp.get('id') and s.find('label',attrs={'for':inp['id']})):errors.append(p.name+': unlabelled form control')
        for button in s.select('button'):
            if not (button.get_text(strip=True) or button.get('aria-label')):errors.append(p.name+': unlabelled button')
        for selector in ['link[rel="canonical"]','link[rel="icon"]','meta[property="og:image"]','meta[name="description"]']:
            if not s.select_one(selector):errors.append(p.name+': missing '+selector)
        for script in s.select('script[type="application/ld+json"]'):
            try:json.loads(script.string or script.get_text())
            except ValueError:errors.append(p.name+': invalid structured data')
    for name,s in pages.items():
        for tag in s.select('[href],[src]'):
            u=urlsplit(tag.get('href') or tag.get('src'))
            if u.scheme or u.netloc:continue
            target=(SITE/(unquote(u.path).lstrip('/') or name)).resolve()
            if target.is_dir():target=target/'index.html'
            if not target.is_relative_to(SITE.resolve()) or not target.is_file():errors.append(name+': broken link '+u.geturl());continue
            rel=target.relative_to(SITE.resolve()).as_posix()
            if u.fragment and rel in pages and not pages[rel].find(id=unquote(u.fragment)):errors.append(name+': absent anchor '+u.geturl())
    for p in (SITE/'downloads').glob('*.docx'):
        try:
            with zipfile.ZipFile(p) as z:
                if z.testzip() or 'word/document.xml' not in z.namelist():errors.append(p.name+': invalid DOCX')
        except zipfile.BadZipFile:errors.append(p.name+': invalid archive')
    for p in (SITE/'downloads').glob('*.pdf'):
        if not p.read_bytes().startswith(b'%PDF-') or p.stat().st_size<3000:errors.append(p.name+': invalid PDF')
    for name in ['study-genai-feedback.html','study-self-regulated-flipped-learning.html','study-ar-intelligent-tutoring.html']:
        for key in ['citation_title','citation_author','citation_publication_date','citation_journal_title','citation_doi']:
            if not pages[name].find('meta',attrs={'name':key}):errors.append(name+': missing '+key)
    if errors:raise SystemExit('\n'.join(errors))
    report={'release':'3.0','checked':'2026-11-12','pages':len(pages),'downloads':len(list((SITE/'downloads').iterdir())),'checks':['local files and anchors','heading and main landmarks','control labels','image alternatives','canonical and sharing metadata','JSON-LD syntax','PDF and DOCX signatures','article citation metadata'],'limitations':['not independent WCAG certification','not PDF/UA certification','not publication indexing confirmation','not validation of teaching prototypes']}
    (SITE/'quality-report.json').write_text(json.dumps(report,indent=2))
    print('V3 RELEASE GATE PASSED:',json.dumps(report))

def link_audit():
    """Report, do not conflate access restrictions or timeouts with broken DOI records."""
    links=set()
    for p in SITE.glob('*.html'):
        s=Soup(p.read_text(),'html.parser')
        links.update(a['href'] for a in s.select('a[href]') if a['href'].startswith('https://'))
    def check(url):
        try:
            req=Request(url,headers={'User-Agent':'Academic-site-link-audit/3.0'},method='HEAD')
            with urlopen(req,timeout=15) as response:
                return {'url':url,'status':response.status,'result':'reachable','resolved':response.geturl()}
        except HTTPError as exc:
            label='access-restricted-or-rate-limited' if exc.code in [401,403,429] else 'requires-manual-review'
            return {'url':url,'status':exc.code,'result':label}
        except Exception as exc:return {'url':url,'status':None,'result':'inconclusive','detail':type(exc).__name__}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,sorted(links)))
    report=ROOT/'link-audit.json';report.write_text(json.dumps(results,indent=2))
    print('External link report:',len(results),'URLs; review link-audit.json. Restricted responses are not classified as invalid publications.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--links',action='store_true');args=parser.parse_args()
    link_audit() if args.links else validate()
