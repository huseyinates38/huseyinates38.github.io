#!/usr/bin/env python3
"""Content regression checks for the final profile/copy review, 5.2."""
from pathlib import Path
import json,re
from bs4 import BeautifulSoup as Soup
from refine_profile_copy import ROLE_ONLY, COPY, BUI
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'

def read(name): return Soup((SITE/name).read_text(encoding='utf-8'),'html.parser')
def values(s): return {x.dt.get_text(' ',strip=True):x.dd.get_text(' ',strip=True) for x in s.select('#academic-record dl.profile-facts > div')}
def main():
 report={'release':'5.2','languages':[],'profile_pages_checked':0,'result':'running'}
 for pre,tr in [('',False),('tr/',True)]:
  team=read(pre+'team.html')
  for slug in ROLE_ONLY:
   s=read(pre+'person-'+slug+'.html');fields=values(s)
   assert list(fields)==(['Rol'] if tr else ['Role']),(slug,fields)
   assert s.select_one('#academic-record .institution-name') and s.select_one('#academic-record .country-tag')
   assert s.select_one('#academic-record img'),slug
   assert not s.select_one('.pagehero .lead')
   assert 'Project research team' not in s.main.get_text() and 'Proje araştırma ekibi' not in s.main.get_text()
   card=team.select_one('[data-person="'+slug+'"]')
   assert not card.select_one('.relationship-stage') and not card.select_one('.person-topic')
  for slug,data in COPY.items():
   s=read(pre+'person-'+slug+'.html');f=values(s)
   assert f['Güncel aşama' if tr else 'Current stage']==data['stage'][int(tr)]
   assert len(s.select('p[data-profile-contribution]'))==1
   assert len(s.select('#ongoing-research'))==1
   assert s.select_one('#ongoing-research .profile-links a')
   assert s.select_one('#academic-record .profile-facts')
   assert not s.select_one('.pagehero .relationship-stage')
   if slug=='marc-romero-carbonell' and tr:assert 'Üretken yapay zekâ (GenAI)' in s.main.get_text()
  bui=read(pre+'person-bui-van-hong.html')
  assert BUI[int(tr)] in bui.main.get_text()
  assert bui.select_one('#ongoing-research a[href="project-vr-stem-vietnam.html"]')
  assert 'Süren araştırma iş birliği' not in bui.main.get_text()
  assert 'Devam eden araştırma iş birliği' not in bui.main.get_text()
  assert 'Süren araştırma iş birliği' not in team.select_one('[data-person="bui-van-hong"]').get_text()
  assert len(team.select('.person-card a[href="person-ipek-oz.html"]'))==2
  for page in (SITE/pre).glob('person-*.html'):
   s=read(pre+page.name);report['profile_pages_checked']+=1
   f=values(s);focus=f.get('Araştırma odağı' if tr else 'Research focus','');stage=f.get('Güncel aşama' if tr else 'Current stage','')
   assert focus not in ['Project research team','Proje araştırma ekibi']
   assert stage not in ['Research team member','Araştırma ekibi üyesi','Research adviser','Araştırma danışmanı']
  network=read(pre+'research-network.html')
  assert len(network.select('.network-country'))==22
  assert network.select_one('#network-no-results[hidden]') and network.select_one('#network-reset')
  assert ('ülke' if tr else 'countries') in network.select_one('#network-count').get_text()
  paragraphs=[x.get_text(' ',strip=True) for x in network.select('main p') if len(x.get_text(' ',strip=True))>70]
  assert len(paragraphs)==len(set(paragraphs)),pre
  assert 'supplied poster' not in network.main.get_text()
  assert 'supplied team roster' not in team.main.get_text()
  assert len(network.select('main a[href="https://tally.so/r/Eq51Jr"]'))==2
  assert len(network.select('main img[src$="research-group-interest.png"]'))==1
  resource=read(pre+'resource-use.html')
  assert ('Üç tematik öğretim seti' if tr else 'the three thematic teaching sets') in resource.select_one('main .v3-box p').get_text()
  assert resource.select_one('[data-resource-attribution]')
  assert 'Altı öğretim rehberi' not in resource.main.get_text()
  # Existing prototype notices and educational-use restrictions remain in place.
  assert 'Creative Commons' in resource.main.get_text()
  assert ('geçerliği' if tr else 'validated instruments') in resource.main.get_text().lower()
  colombia=read(pre+'project-ai-literacy-colombia.html').select('main > section')[-1]
  assert len(colombia.select('p'))==1
  assert not colombia.select('.callout'), 'Unequal Colombia status disclaimer: '+pre
  assert ('pilot uygulama hazırlıkları' if tr else 'pilot preparation') in colombia.get_text()
  if tr:assert 'Explorer içindeki' not in read(pre+'resource-argumentation.html').main.get_text()
  report['languages'].append('tr' if tr else 'en')
 report['result']='passed'
 (ROOT/'profile-refinement-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
