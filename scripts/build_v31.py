#!/usr/bin/env python3
"""Stabilise the generated website without changing academic claims or documents."""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
BASE = 'https://huseyinates38.github.io/'
VERSION = '3.1'

def normalized(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', value) if not unicodedata.combining(c)).replace('ı','i').lower()

def fragment(html: str):
    return Soup(html, 'html.parser')

def category(name: str) -> tuple[str, str]:
    if name.startswith('person-') or name == 'team.html': return 'people', 'People'
    if name.startswith('study-') or name == 'publications.html': return 'publications', 'Research brief' if name.startswith('study-') else 'Publications'
    if name in ['resources.html','practice.html','open-research.html','feedback-explorer.html'] or name.startswith('resource-'): return 'resources', 'Resources & methods'
    if name in ['research.html','research-timeline.html','projects.html'] or name.startswith('project-'): return 'research', 'Research & projects'
    return 'about', 'Profile & site information'

def main() -> None:
    manifest = json.loads((SITE/'deployment.json').read_text(encoding='utf-8'))
    documents = {p.name: Soup(p.read_text(encoding='utf-8'),'html.parser') for p in SITE.glob('*.html') if p.name != 'search.html'}
    for name, soup in documents.items():
        nav = soup.select_one('#main-navigation')
        if nav and not nav.find('a',href='search.html'):
            nav.append(fragment('<a href="search.html" class="search-nav">Search</a>').a)
        footer = soup.select_one('.footer-links')
        if footer and not footer.find('a',href='search.html'):
            footer.append(fragment('<a class="textlink" href="search.html">Search this website ↗</a>').a)
        # All assets are local. The v2 stylesheet already uses system fonts.
        for node in soup.select('[href],[src]'):
            attr = 'src' if node.has_attr('src') else 'href'
            url = urlsplit(node[attr])
            if not url.scheme and url.path.startswith('assets/') and url.path.endswith(('.css','.js')):
                node[attr] = url.path + '?v=' + VERSION
        for file, tag, attrs in [('assets/v31.css','link',{'rel':'stylesheet','href':'assets/v31.css?v='+VERSION}), ('assets/v31.js','script',{'src':'assets/v31.js?v='+VERSION,'defer':''})]:
            if not soup.find(tag,attrs={'href' if tag=='link' else 'src':attrs.get('href',attrs.get('src'))}):soup.head.append(soup.new_tag(tag,attrs=attrs))
        # Align obsolete collection labels; retain version 1.0 of the separate interactive demo.
        if name in ['resources.html','site-notes.html']:
            for text in list(soup.find_all(string=True)):
                if 'Original teaching prototypes / Version 1.0' in text or 'Resource prototypes: version 1.0.' in text:
                    text.replace_with(str(text).replace('Version 1.0','Version 1.1').replace('version 1.0.','version 1.1.'))
        for link in soup.select('a[href]'):
            url = urlsplit(link['href'])
            if not url.scheme and url.path.startswith('downloads/') and url.path.endswith(('.pdf','.docx','.zip')):
                target = SITE/url.path
                if target.is_file():
                    kb = target.stat().st_size/1024
                    size = f'{kb/1024:.1f} MB' if kb>=1024 else f'{max(1,round(kb))} KB'
                    label = link.get_text(' ',strip=True)
                    link['aria-label'] = label + ' (' + url.path.rsplit('.',1)[-1].upper() + ', ' + size + ')'
                    link['title'] = link['aria-label']
                    link['download'] = target.name
        for table in soup.select('.v3-table-wrap'):
            table['tabindex']='0'; table['role']='region'; table['aria-label']='Project comparison table; scroll horizontally on small screens'
        if soup.select_one('[data-language-picker]'):
            control = soup.select_one('.language-control') or soup.select_one('.explorer-controls')
            if control and not soup.find(id='language-status'):
                control.insert_after(fragment('<p id="language-status" role="status" class="sr-status"></p>').p)
        if name=='publications.html':
            toolbar = soup.select_one('.toolbar')
            query = soup.find(id='pub-query')
            query['maxlength']='120';query['aria-describedby']='publication-search-help'
            if toolbar and not soup.find(id='pub-reset'):
                toolbar.append(fragment('<button id="pub-reset" class="search-reset" type="button">Clear filters</button>').button)
                toolbar.insert_after(fragment('<p id="publication-search-help" class="search-help">Search by title, author, journal or DOI. Turkish characters are optional; AI, GenAI, VR, AR and SRL abbreviations are supported. The address preserves your current filter.</p>').p)
            for row in soup.select('.publication'):
                doi = row.select_one('a[href*="doi.org/"]')
                if doi:row['id']='publication-'+hashlib.sha256(doi['href'].encode()).hexdigest()[:10]
    # An unnecessary font import remained in an earlier stylesheet, despite the system-font design.
    for file in (SITE/'assets').glob('*.css'):
        text=file.read_text(encoding='utf-8')
        text=re.sub(r'@import\s+url\([^)]*fonts\.googleapis\.com[^)]*\);\s*','',text)
        file.write_text(text,encoding='utf-8')
    for name in ['v31.js','v31.css']:shutil.copy2(ROOT/'assets'/name,SITE/'assets'/name)
    # Build an index only from published HTML and existing downloads, not invented content.
    records=[]
    favourites=['resources.html','feedback-explorer.html','projects.html','publications.html','team.html','about.html']
    ordered=sorted((n for n in documents if n!='404.html'),key=lambda n:(favourites.index(n) if n in favourites else 99,n))
    for name in ordered:
        soup=documents[name]; main=soup.select_one('main'); cat,label=category(name)
        desc=soup.find('meta',attrs={'name':'description'})
        title=soup.title.get_text().split(' | ')[0]
        text=main.get_text(' ',strip=True) if main else title
        records.append({'title':title,'url':name,'category':cat,'label':label,'summary':desc.get('content','') if desc else text[:190], 'key':normalized(title+' '+text)})
    for row in documents['publications.html'].select('.publication'):
        text=row.get_text(' ',strip=True); title=row.h3.get_text(' ',strip=True)
        records.append({'title':title,'url':'publications.html#'+row['id'],'category':'publications','label':'Journal article · '+row.get('data-year',''),'summary':row.p.get_text(' ',strip=True),'key':normalized(text)})
    seen=set()
    for name in ['about.html','resource-feedback.html','resource-argumentation.html','resource-self-regulation.html']:
        soup=documents[name]
        for link in soup.select('main a[href]'):
            url=link['href']
            if url.startswith('downloads/') and url.endswith(('.pdf','.docx')) and url not in seen:
                seen.add(url); title=soup.title.get_text().split(' | ')[0]+' — '+link.get_text(' ',strip=True)
                records.append({'title':title,'url':url,'category':'about' if name=='about.html' else 'resources','label':'Download · '+url.rsplit('.',1)[-1].upper(),'summary':'Existing public academic CV.' if name=='about.html' else 'Teaching prototype, version 1.1; not a validated assessment or published study instrument.','key':normalized(title+' '+url)})
    search=Soup(str(documents['index.html']),'html.parser')
    search.title.string='Search the website | Hüseyin Ateş'
    description='Find research, people, publications and English–Turkish teaching resources on this website.'
    for node in search.select('meta[name=description],meta[property="og:description"]'):node['content']=description
    for node in search.select('meta[property="og:title"]'):node['content']=search.title.string
    for node in search.select('meta[property="og:url"]'):node['content']=BASE+'search.html'
    search.select_one('link[rel=canonical]')['href']=BASE+'search.html'
    for node in search.select('script[type="application/ld+json"]'):node.decompose()
    robots=search.new_tag('meta',attrs={'name':'robots','content':'noindex,follow'});search.head.append(robots)
    for node in search.select('[aria-current]'):del node['aria-current']
    search.select_one('nav a[href="search.html"]')['aria-current']='page'
    search.main.clear()
    search.main.append(fragment('''<section class="pagehero"><div class="container"><div class="eyebrow">Find your next step</div><h1>Search the <em>website</em>.</h1><p>Research, people and practical resources, in one place.</p></div></section><section class="section"><div class="container"><div class="site-search-controls"><div><label for="site-query">What are you looking for?</label><input type="search" id="site-query" maxlength="120" autocomplete="off" aria-describedby="site-search-help" placeholder="Feedback, VR, Tuğçe, academic CV…"></div><div><label for="site-category">Content type</label><select id="site-category"><option value="all">All content</option><option value="research">Research &amp; projects</option><option value="people">People</option><option value="publications">Publications &amp; briefs</option><option value="resources">Resources &amp; methods</option><option value="about">Profile &amp; site information</option></select></div><button id="site-search-reset" type="button" class="search-reset">Clear search</button></div><p id="site-search-help" class="search-help">Search in English or with Turkish names. Turkish characters are optional. Try “Ates”, “Tugce”, “VR” or “feedback”. Search runs in your browser, with no external search provider, cookies or account. Filters are saved only in the shareable address fragment.</p><p id="site-search-status" role="status" aria-live="polite" aria-atomic="true"></p><ol id="site-search-results" class="search-results" aria-label="Search results"></ol><button id="site-search-more" class="btn" type="button" hidden>Show more results</button><div id="search-directory" class="search-directory"><h2>Browse all pages</h2><p>This directory also works without JavaScript.</p><ul></ul></div></div></section>'''))
    directory=search.select_one('#search-directory ul')
    for record in records:
        if '#' in record['url'] or record['url'].startswith('downloads/'):continue
        item=search.new_tag('li');a=search.new_tag('a',href=record['url']);a.string=record['title'];item.append(a);directory.append(item)
    payload=search.new_tag('script',attrs={'id':'site-search-data','type':'application/json'})
    payload.string=json.dumps(records,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    search.body.append(payload)
    documents['search.html']=search
    for name in ['site-notes.html','accessibility.html']:
        soup=documents[name]
        section=fragment('''<section class="section"><div class="container reading"><h2>Search and interface preferences</h2><p>The search index is built from this website’s published pages and downloads. Search runs locally, without an external search service or browser storage. Publication filters and language choices can be shared through the address fragment. No student responses are collected.</p><p>Website release 3.1 focuses on navigation and interface reliability. Teaching documents remain version 1.1; no new academic result is claimed by this maintenance update.</p><p><a class="textlink" href="search.html">Search the website ↗</a></p></div></section>''')
        soup.main.append(section)
    for name,soup in documents.items():(SITE/name).write_text(str(soup),encoding='utf-8')
    sitemap=Soup((SITE/'sitemap.xml').read_text(),'xml')
    # Search pages are noindex and intentionally not added to the academic sitemap.
    manifest['version']=VERSION;manifest['pages']=sorted(documents);manifest['page_count']=len(documents)
    manifest.pop('files',None)
    (SITE/'deployment.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared release {VERSION}: {len(documents)} pages; {len(records)} search records; teaching documents unchanged.')

if __name__=='__main__':main()
