#!/usr/bin/env python3
"""Check bilingual equivalence, critical status boundaries, links and privacy."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import json
from bs4 import BeautifulSoup as Soup
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';BASE='https://huseyinates38.github.io/'
manifest=json.loads((SITE/'deployment.json').read_text());names=sorted(p.name for p in SITE.glob('*.html'))
assert manifest['language_pairs']==len(names)==49
assert len(manifest['pages'])==98
assert len(manifest['downloads'])==33
for name in names:
    for lang in ['en','tr']:
        rel=('tr/' if lang=='tr' else '')+name
        s=Soup((SITE/rel).read_text(),'html.parser')
        assert s.html['lang']==lang,(rel,'wrong lang')
        assert len(s.select('main h1'))==1,(rel,'h1')
        assert not s.select('img'),(rel,'photo was not requested')
        for code,expected in [('en',BASE+name),('tr',BASE+'tr/'+name),('x-default',BASE+name)]:
            assert s.select_one(f'link[hreflang="{code}"]')['href']==expected,(rel,code)
        assert s.select_one('[rel=canonical]')['href']==BASE+rel
        for code in ['en','tr']:
            a=s.select_one(f'[data-site-lang="{code}"]');assert a
            assert urljoin(BASE+rel,a['href'])==BASE+('tr/' if code=='tr' else '')+name
        for a in s.select('a[href]'):
            u=urlsplit(a['href'])
            if u.scheme or u.netloc or a.has_attr('data-site-lang'):continue
            if u.path.endswith('.html'):
                resolved=urljoin(BASE+rel,a['href'])
                assert ('/tr/' in resolved)==(lang=='tr'),(rel,'language leak',a['href'])
        for sc in s.select('script[src]'):
            assert 'bilingual.js' in sc['src'],(rel,'legacy handlers')
        assert 'professional_outdoor_business_portrait' not in str(s)
for prefix in ['','tr/']:
    s=Soup((SITE/(prefix+'projects.html')).read_text(),'html.parser')
    assert len(s.select('[data-programme]'))==3
    assert not s.select_one('#funded-projects').find('a',href='project-robot-virtual-agent.html')
    proposal=Soup((SITE/(prefix+'proposals.html')).read_text(),'html.parser')
    assert len(proposal.select('[data-proposal-state]'))==6
    assert len(proposal.select('[data-proposal-state="submitted"]'))==4
    # Retain collaborator-first order.
    people=(SITE/(prefix+'team.html')).read_text()
    assert people.index('id="collaborators"')<people.index('id="graduate-researchers"')
    assert all(x in people for x in ['Georgios Lampropoulos','Naomi Winstone','Juan Garzón'])
    pubs=Soup((SITE/(prefix+'publications.html')).read_text(),'html.parser')
    assert len(pubs.select('.publication'))==23
    search=Soup((SITE/(prefix+'search.html')).read_text(),'html.parser')
    data=json.loads(search.select_one('#site-search-data').string)
    assert len(data)==80,(prefix,len(data))
for name in ['project-robot-virtual-agent.html','proposal-feedback-fading.html','editorial.html']:
    s=Soup((SITE/name).read_text(),'html.parser')
    assert any(term in s.main.get_text().lower() for term in ['no funding award','decision pending','approval pending'])
report=json.loads((SITE/'quality-report.json').read_text());report['static_bilingual_checks']='passed'
(SITE/'quality-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASS: 49 EN/TR page pairs, reciprocal language links, stable statuses, 23 unchanged publication records, 33 downloads, no photo.')
