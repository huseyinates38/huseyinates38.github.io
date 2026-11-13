#!/usr/bin/env python3
"""Bilingual editorial release gates: status, navigation, translation, privacy, linked documents."""
from pathlib import Path
from bs4 import BeautifulSoup as Soup
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site';sys.path.insert(0,str(ROOT/'scripts'))
from verify_site import validate

def main():
  validate()
  m=json.loads((SITE/'deployment.json').read_text())
  assert m['version']=='4.1' and m['languages']==['en','tr'],m
  assert m['language_pairs']==56 and m['page_count']==112,(m['language_pairs'],m['page_count'])
  paths=sorted(p.name for p in SITE.glob('*.html'))
  assert len(paths)==56
  for name in paths:
    en=Soup((SITE/name).read_text(encoding='utf-8'),'html.parser')
    tr=Soup((SITE/'tr'/name).read_text(encoding='utf-8'),'html.parser')
    assert en.html['lang']=='en' and tr.html['lang']=='tr',name
    assert tr.select_one('link[rel="canonical"]')['href'].endswith('tr/'+name),name
    assert en.select_one('link[hreflang="tr"]')['href'].endswith('tr/'+name),name
    assert tr.select_one('link[hreflang="en"]')['href'].endswith('/'+name),name
    assert en.select_one('.site-language a[lang="tr"]')['href']=='tr/'+name,name
    assert tr.select_one('.site-language a[lang="en"]')['href']=='../'+name,name
    assert len(en.select('nav#main-navigation a'))==len(tr.select('nav#main-navigation a'))==7,name
    assert (SITE/'tr'/name).stat().st_size>1000,name
    assert not en.select('img[src*="portrait"],img[src*="IMG_"],img[src*="photo"]'),name
    assert not tr.select('img[src*="portrait"],img[src*="IMG_"],img[src*="photo"]'),name
  p=json.loads((ROOT/'content/research-pipeline.json').read_text())['proposals']
  assert len(p)==7 and sum(x['state']=='submitted' for x in p)==4
  assert sum(x['state']=='planned' for x in p)==2 and sum(x['state']=='not-funded' for x in p)==1
  assert not any(x['slug']=='tubitak-dfg-reasoning' and x['state']!='planned' for x in p)
  assert next(x for x in p if x['slug']=='robot-virtual-agent')['status']=='Not funded · application unsuccessful'
  assert (SITE/'downloads/Huseyin_Ates_Akademik_Ozgecmis_TR.pdf').stat().st_size>20000
  assert (SITE/'downloads/Huseyin_Ates_Akademik_Ozgecmis_TR.docx').stat().st_size>10000
  tr_about=Soup((SITE/'tr/about.html').read_text(),'html.parser')
  assert tr_about.find('a',href='../downloads/Huseyin_Ates_Akademik_Ozgecmis_TR.pdf')
  assert tr_about.find('a',href='../downloads/Huseyin_Ates_Public_Academic_CV.pdf')
  for loc in ('','tr/'):
    count=Soup((SITE/loc/'proposals.html').read_text(),'html.parser')
    assert len(count.select('article.pipeline-card'))==7
    status=Soup((SITE/loc/'project-robot-virtual-agent.html').read_text(),'html.parser').get_text(' ',strip=True)
    assert ('Not funded · application unsuccessful' if loc=='' else 'Desteklenmedi · başvuru kabul edilmedi') in status
  for person in ('omid-noroozi','kazem-banihashem','elena-novak'):
    for loc in ('','tr/'):
      text=Soup((SITE/loc/('person-'+person+'.html')).read_text(),'html.parser').get_text(' ',strip=True)
      assert not any(x in text for x in ['declined a separate COST invitation','did not join the SciEpi-Feedback COST proposal','initial dates were unavailable','farklı bir COST davetini kabul etmedi','kurumsal kısıtlar nedeniyle SciEpi-Feedback','ilk tarihler uygun değildi'])
  pr=Soup((SITE/'projects.html').read_text(),'html.parser')
  assert len(pr.select('#funded-projects .project-summary'))==3
  assert '3501' not in pr.select_one('#funded-projects').get_text()
  for name in ['omid-noroozi','mohammadreza-farrokhnia','kazem-banihashem','elena-novak','guido-makransky','moritz-krell']:
    assert (SITE/('person-'+name+'.html')).is_file()
    assert (SITE/'tr'/('person-'+name+'.html')).is_file()
  team=Soup((SITE/'tr/team.html').read_text(),'html.parser')
  sections=[n.get('id') for n in team.select('main > section[id]')]
  assert sections.index('collaborators')<sections.index('graduate-researchers')
  assert 'Omid Noroozi' in team.get_text() and 'Guido Makransky' in team.get_text()
  dfg=Soup((SITE/'tr/proposal-tubitak-dfg-reasoning.html').read_text(),'html.parser').get_text(' ',strip=True)
  assert 'başvuru yapılmadı' in dfg and 'Krell' in dfg
  protected=['mail.google.com','teams.microsoft.com/meet','Invitation Letter.docx','IMG_3348','IMG_8514','professional_outdoor_business_portrait','/mnt/data/','ghp_']
  for f in SITE.rglob('*'):
    if f.suffix.lower() in ('.html','.json','.js','.md','.txt','.csv','.xml'):
      txt=f.read_text(encoding='utf-8')
      assert not any(x in txt for x in protected),str(f)
  for loc in ('','tr/'):
    s=Soup((SITE/loc/'search.html').read_text(),'html.parser')
    records=json.loads(s.find(id='site-search-data').string)
    assert len(records)>60 and len(records)==len({item['url'] for item in records})
    assert any('moritz-krell' in item['url'] for item in records)
    assert any('tubitak-dfg' in item['url'] for item in records)
    assert all((SITE/loc/item['url']).is_file() for item in records if item['url'].endswith('.html'))
  print('BILINGUAL RELEASE VALIDATED:',len(paths),'EN/TR pairs; 3 supported, 4 submitted, 2 planned, 1 non-funded; privacy and local navigation checked.')

if __name__=='__main__':main()
