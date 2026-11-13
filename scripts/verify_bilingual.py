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
  assert m['version']=='4.9' and m['languages']==['en','tr'],m
  assert m['language_pairs']==69 and m['page_count']==138,(m['language_pairs'],m['page_count'])
  paths=sorted(p.name for p in SITE.glob('*.html'))
  assert len(paths)==69
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
  assert len(p)==7 and sum(x['state']=='submitted' for x in p)==5
  assert sum(x['state']=='planned' for x in p)==1 and sum(x['state']=='not-funded' for x in p)==1
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
  for loc in ('','tr/'):
    page=Soup((SITE/loc/'project-vr-stem-vietnam.html').read_text(),'html.parser').get_text(' ',strip=True)
    assert ('Completed' if not loc else 'Tamamlandı') in page
    assert '2026–2028' not in page,loc
  from docx import Document
  for name in ['Huseyin_Ates_Public_Academic_CV.docx','Huseyin_Ates_Akademik_Ozgecmis_TR.docx']:
    cv=' '.join(p.text for p in Document(SITE/'downloads'/name).paragraphs)
    assert 'EGT.A3.26.001' in cv and ('Completed' if 'Public' in name else 'Tamamlandı') in cv
    assert '2026–2028 | KAEÜ BAP' not in cv
  for person in ('omid-noroozi','kazem-banihashem','elena-novak'):
    for loc in ('','tr/'):
      text=Soup((SITE/loc/('person-'+person+'.html')).read_text(),'html.parser').get_text(' ',strip=True)
      assert not any(x in text for x in ['declined a separate COST invitation','did not join the SciEpi-Feedback COST proposal','initial dates were unavailable','farklı bir COST davetini kabul etmedi','kurumsal kısıtlar nedeniyle SciEpi-Feedback','ilk tarihler uygun değildi'])
  pr=Soup((SITE/'projects.html').read_text(),'html.parser')
  assert len(pr.select('#funded-projects .project-summary'))==1
  assert len(pr.select('#completed-projects .project-summary'))==2
  assert pr.select_one('#completed-projects a[href="project-vr-stem-vietnam.html"]')
  assert pr.select_one('#completed-projects a[href="project-vr-circulatory-system.html"]')
  assert not pr.select_one('#funded-projects a[href="project-vr-stem-vietnam.html"]')
  assert '3501' not in pr.select_one('#funded-projects').get_text()
  for name in ['omid-noroozi','mohammadreza-farrokhnia','kazem-banihashem','elena-novak','guido-makransky','moritz-krell']:
    assert (SITE/('person-'+name+'.html')).is_file()
    assert (SITE/'tr'/('person-'+name+'.html')).is_file()
  team=Soup((SITE/'tr/team.html').read_text(),'html.parser')
  assert 'Fen Bilgisi Eğitimi Doçenti' not in team.get_text(' ',strip=True)
  assert team.select_one('#collaborators h2').get_text(' ',strip=True)=='Devam eden araştırma iş birlikleri'
  assert 'Naomi Winstone' in team.get_text(' ',strip=True)
  for slug in ('naomi-winstone','elena-novak','guido-makransky','moritz-krell','georgios-lampropoulos','bui-van-hong'):
    for local in ('','tr/'):
      source=(SITE/local/('person-'+slug+'.html')).read_text()
      assert 'ongoing-research' in source or 'Süren akademik bağlantı' in source or 'Devam eden araştırma iş birliği' in source or 'Ongoing academic connection' in source,slug
  assert (SITE/'downloads/research-network-tr.pdf').is_file()
  assert (SITE/'downloads/research-network-en.pdf').is_file()
  sections=[n.get('id') for n in team.select('main > section[id]')]
  assert sections.index('collaborators')<sections.index('graduate-researchers')
  assert 'Omid Noroozi' in team.get_text() and 'Guido Makransky' in team.get_text()
  # Public research group and grant titles must not regress to editor/author notes.
  for prefix in ('','tr/'):
    team_page=Soup((SITE/prefix/'team.html').read_text(encoding='utf-8'),'html.parser')
    alumni=team_page.select_one('#alumni')
    researchers=team_page.select_one('#project-contributors')
    assert alumni and alumni.select_one('[data-person="ipek-oz-alumna"]')
    assert researchers and researchers.select_one('[data-person="ipek-oz"]')
    assert team_page.select_one('a[href="https://tally.so/r/Eq51Jr"]')
    assert team_page.select_one('img[src$="assets/qr/research-group-interest.png"]')
    assert 'İpek Öz araştırmacı olarak da katkı sunuyor ve üst bölümde listeleniyor' not in team_page.get_text(' ',strip=True)
    join_page=Soup((SITE/prefix/'join.html').read_text(encoding='utf-8'),'html.parser')
    assert join_page.select_one('a[href="https://tally.so/r/Eq51Jr"]') and join_page.select_one('img[src$="assets/qr/research-group-interest.png"]')
    project=Soup((SITE/prefix/'project-space-debris.html').read_text(encoding='utf-8'),'html.parser')
    assert ('Uzay Kirliliği Problem Çözme Öğretiminde İki Pedagojik İskele Yaklaşımının Sınıf İçi Pilot Karşılaştırması' if prefix else 'Classroom Pilot Comparison of Two Pedagogical Scaffolding Approaches') in project.select_one('h1').get_text(' ',strip=True)
    serbay=Soup((SITE/prefix/'person-serbay-durmaz.html').read_text(encoding='utf-8'),'html.parser').get_text(' ',strip=True)
    assert ('Karacaoğlan Ortaokulu' if prefix else 'Karacaoğlan Secondary School') in serbay
  assert (SITE/'assets/qr/research-group-interest.png').stat().st_size>1000
  # Verify that editorial visuals exist in both language editions and remain explicitly conceptual.
  for locale in ('','tr/'):
    homepage=Soup((SITE/locale/'index.html').read_text(encoding='utf-8'),'html.parser')
    assert homepage.select_one('.showcase-hero')
    assert len(homepage.select('.showcase-topic'))==5 and len(homepage.select('.showcase-news-card'))==5
    assert homepage.select_one('a[href="https://tally.so/r/Eq51Jr"]')
    assert homepage.select_one('.showcase-join-qr img[src$="research-group-interest.png"]')
    research=Soup((SITE/locale/'research.html').read_text(encoding='utf-8'),'html.parser')
    assert len(research.select('.research-theme-grid .entry'))==3
    projects=Soup((SITE/locale/'projects.html').read_text(encoding='utf-8'),'html.parser')
    assert len(projects.select('.project-summary .card-art'))>=3
  assert (SITE/'assets/visuals/research-hero.webp').stat().st_size>20000
  dfg=Soup((SITE/'tr/proposal-tubitak-dfg-reasoning.html').read_text(),'html.parser').get_text(' ',strip=True)
  assert 'başvuru yapılmadı' in dfg and 'Krell' in dfg
  # English/Turkish institutional affiliations: do not infer outdated University of Crete links.
  for locale in ('','tr/'):
    georgios=Soup((SITE/locale/'person-georgios-lampropoulos.html').read_text(encoding='utf-8'),'html.parser').get_text(' ',strip=True)
    assert 'University of Nicosia' in georgios and 'University of Macedonia' in georgios,locale
    assert 'University of Crete' not in georgios and 'Girit Üniversitesi' not in georgios,locale
    join=Soup((SITE/locale/'join.html').read_text(encoding='utf-8'),'html.parser').get_text(' ',strip=True)
    assert 'Before sending.' not in join and 'Göndermeden önce' not in join,locale
    assert 'Bu sitede başvuru formu yoktur.' not in join,locale
    conf=Soup((SITE/locale/'conference-iccai-2027.html').read_text(encoding='utf-8'),'html.parser').get_text(' ',strip=True)
    assert 'YS1001' in conf and '2224-A' in conf and 'ICCAI 2027' in conf,locale
    assert ('Sözlü sunum için kabul edildi' if locale else 'Accepted for oral presentation') in conf,locale
    about=Soup((SITE/locale/'about.html').read_text(encoding='utf-8'),'html.parser')
    assert about.find('a',href='conference-iccai-2027.html'),locale
    proposals=Soup((SITE/locale/'proposals.html').read_text(encoding='utf-8'),'html.parser')
    assert len(proposals.select('article.pipeline-card'))==7,locale
  # Full Turkish editorial pass: check all public HTML headings, not only team profiles.
  for f in (SITE/'tr').glob('*.html'):
    doc=Soup(f.read_text(encoding='utf-8'),'html.parser')
    if not doc.main:continue
    assert 'Göndermeden önce.' not in doc.main.get_text(' ',strip=True),f.name
    for heading in doc.main.select('h1,h2,h3'):
      txt=heading.get_text(' ',strip=True)
      assert not txt.endswith(' .'),(f.name,txt)
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
  print('BILINGUAL RELEASE VALIDATED:',len(paths),'EN/TR pairs; 1 supported + 2 completed BAP, 5 submitted, 1 planned, 1 non-funded; privacy and navigation checked.')

if __name__=='__main__':main()
