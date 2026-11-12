#!/usr/bin/env python3
"""Reuse the structural gate and add search/version regressions."""
from pathlib import Path
import json
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup as Soup
from verify_v3 import validate

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'

def main():
    validate()
    manifest=json.loads((SITE/'deployment.json').read_text())
    assert manifest['version']=='3.1' and 'search.html' in manifest['pages']
    soup=Soup((SITE/'search.html').read_text(),'html.parser')
    data=json.loads(soup.find(id='site-search-data').string)
    assert len(data)==len({row['url'] for row in data}), 'Duplicate search results'
    for row in data:
        url=urlsplit(row['url']);assert not url.scheme and not url.netloc, 'External URL in local search index'
        target=(SITE/unquote(url.path)).resolve();assert target.is_relative_to(SITE.resolve()) and target.is_file()
        if url.fragment:assert Soup(target.read_text(),'html.parser').find(id=url.fragment), 'Search anchor missing'
    for name in manifest['pages']:
        page=Soup((SITE/name).read_text(),'html.parser')
        assert page.select_one('nav a[href="search.html"]'), name
        for a in page.select('a[href$=".pdf"],a[href$=".docx"]'):
            if a['href'].startswith('downloads/'):assert a.get('aria-label'), 'Download description missing'
    for name in ['resources.html','site-notes.html']:
        text=(SITE/name).read_text();assert 'prototypes / Version 1.0' not in text and 'Resource prototypes: version 1.0.' not in text
    for path in (SITE/'assets').glob('*.css'):assert 'fonts.googleapis.com' not in path.read_text()
    report=json.loads((SITE/'quality-report.json').read_text())
    report['release']='3.1';report['search_records']=len(data)
    report['checks']+=['local search targets and publication anchors','resource version consistency','local font styling','download type and size descriptions']
    (SITE/'quality-report.json').write_text(json.dumps(report,indent=2))
    print(f'STABILISATION GATE PASSED: {len(manifest["pages"])} pages; {len(data)} searchable records.')

if __name__=='__main__':main()
