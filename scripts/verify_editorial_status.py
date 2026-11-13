#!/usr/bin/env python3
"""Regression gate for the owner's funding-status correction and public privacy boundary."""
from pathlib import Path
import json,re
from bs4 import BeautifulSoup as Soup
from docx import Document
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'

def main():
    from verify_v3 import validate
    validate()
    manifest=json.loads((SITE/'deployment.json').read_text())
    assert manifest['version']=='3.2'
    s=Soup((SITE/'projects.html').read_text(),'html.parser')
    funded=s.find(id='funded-projects')
    assert funded and len(funded.select('.project-summary'))==2
    assert len(s.select('#completed-projects .project-summary'))==1
    assert '3501' not in funded.get_text() and not funded.find('a',href='project-robot-virtual-agent.html')
    proposals=json.loads((ROOT/'content/research-pipeline.json').read_text())['proposals']
    assert len(proposals)==7 and sum(p['state']=='submitted' for p in proposals)==4
    assert sum(p['state']=='planned' for p in proposals)==2 and sum(p['state']=='not-funded' for p in proposals)==1
    for p in proposals:
        name=p.get('page','proposal-'+p['slug']+'.html');page=Soup((SITE/name).read_text(),'html.parser')
        assert p['status'] in page.main.get_text(),name
        assert p['programme'] in page.main.get_text(),name
    robot=Soup((SITE/'project-robot-virtual-agent.html').read_text(),'html.parser')
    assert 'Proposal · no funding award' in robot.main.get_text()
    assert '2026–2029' not in robot.main.get_text()
    people=Soup((SITE/'team.html').read_text(),'html.parser')
    order=[x.get('id') for x in people.select('main > section[id]')]
    assert order.index('collaborators')<order.index('editorial-collaborators')<order.index('graduate-researchers')<order.index('alumni')
    for name in ['georgios-lampropoulos','naomi-winstone','juan-david-murillo-egurrola','marc-romero-carbonell']:
        assert (SITE/('person-'+name+'.html')).is_file()
    editorial=Soup((SITE/'editorial.html').read_text(),'html.parser')
    assert 'journal approval pending' in editorial.find(id='ethe').get_text()
    assert 'Not an open call.' in editorial.find(id='ethe').get_text()
    cv='\n'.join(p.text for p in Document(SITE/'downloads/Huseyin_Ates_Public_Academic_CV.docx').paragraphs)
    supported=cv.split('Selected funded research')[1].split('Research, supervision')[0]
    assert '3501' not in supported
    assert 'TÜBİTAK 3501' in cv and 'TÜBİTAK 2221' in cv and 'Naomi Winstone' in cv
    assert 'Submitted proposals · Funding decisions pending' in cv
    # Public content must not contain source-message IDs, private mail URLs, invitation attachments,
    # journal candidate deliberations, private proposal identifiers or meeting credentials.
    forbidden=['mail.google.com','teams.microsoft.com/meet','Invitation Letter.docx']
    for p in SITE.rglob('*'):
        if p.suffix in ['.html','.json','.js','.md','.txt','.csv','.py']:
            text=p.read_text(encoding='utf-8')
            assert not any(x in text for x in forbidden),'Private source data in '+str(p)
            assert not re.search(r'SEP-\d{6,}',text),'Internal proposal reference in '+str(p)
    from urllib.parse import urlsplit,unquote
    search=Soup((SITE/'search.html').read_text(),'html.parser')
    records=json.loads(search.find(id='site-search-data').string)
    assert len(records)==len({r['url'] for r in records})
    for r in records:
        u=urlsplit(r['url']);p=(SITE/unquote(u.path)).resolve()
        assert not u.scheme and p.is_relative_to(SITE.resolve()) and p.is_file()
        if u.fragment:assert Soup(p.read_text(),'html.parser').find(id=unquote(u.fragment))
    for key in ['proposals.html','editorial.html','proposal-feedback-fading.html','person-georgios-lampropoulos.html']:
        assert any(r['url']==key for r in records),key
    if (SITE/'quality-report.json').is_file():
        q=json.loads((SITE/'quality-report.json').read_text());q['release']='3.2';q['search_records']=len(records);q['checks']+=['3501 excluded from awarded funding and public CV funded section','submitted vs planned proposal classification','collaborators precede graduate researchers','private source identifiers excluded from published content'];(SITE/'quality-report.json').write_text(json.dumps(q,indent=2))
    print('EDITORIAL STATUS GATE: 2 other supported + 1 completed; 4 submitted, 2 planned and 1 non-funded proposal; people order and privacy checks passed.')

if __name__=='__main__':main()
