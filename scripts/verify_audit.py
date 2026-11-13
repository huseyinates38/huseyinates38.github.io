#!/usr/bin/env python3
"""Regression gates for the 13 November bilingual editorial audit."""
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from pypdf import PdfReader
from docx import Document
import csv,json,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'
def doc(path):return Soup((SITE/path).read_text(encoding='utf-8'),'html.parser')
def maintext(path):return doc(path).main.get_text(' ',strip=True)
def main():
 checks=[];paths=sorted(SITE.rglob('*.html'))
 assert len(paths)==138
 for lang in ['en','tr']:
  pre='tr/' if lang=='tr' else '';tr=lang=='tr'
  docs={p.name:doc(pre+p.name) for p in (SITE/pre).glob('*.html')}
  for name,s in docs.items():
   assert s.body.get('data-content-release')=='5.2',(pre,name)
   assert s.select_one('nav#main-navigation a.mobile-search-link[href="search.html"]'),(pre,name)
   if tr:assert s.select_one('.footer-links a[href="../downloads/Huseyin_Ates_Akademik_Ozgecmis_TR.pdf"]'),name
   else:assert s.select_one('.footer-links a[href="downloads/Huseyin_Ates_Public_Academic_CV.pdf"]'),name
   assert s.select_one('meta[property="og:title"]')['content']==s.title.string
   if name!='index.html':assert s.main.h1.get_text(' ',strip=True) in s.title.string,name
   if tr:assert not any(bad in s.main.get_text() for bad in ['iş birliklerindan','iş birlikleridır']),name
  app=docs['proposal-visiting-researchers-2221.html'];title='TÜBİTAK 2221 Konuk Araştırmacı Başvurusu' if tr else 'TÜBİTAK 2221 Visiting-Researcher Application'
  assert app.main.h1.get_text()==title
  assert ('Başvuru sunuldu · karar bekleniyor' if tr else 'Submitted · decision pending') in app.main.get_text(' ',strip=True)
  assert ('planlanan konuk araştırmacı başvuruları' if tr else 'planned visiting-researcher applications') not in app.main.get_text()
  records=json.loads(docs['search.html'].select_one('#site-search-data').string)
  for name in ['team.html','publications.html','proposal-visiting-researchers-2221.html']:
   record=next(r for r in records if r['url']==name)
   assert record['title']==docs[name].main.h1.get_text(' ',strip=True),(lang,name)
  cards=docs['team.html'].select('.person-card[data-person]');assert len(cards)==31
  from refine_profile_copy import NO_STAGE
  assert all(c.select_one('.relationship-stage') for c in cards if c['data-person'] not in NO_STAGE)
  assert all(not c.select_one('.relationship-stage') for c in cards if c['data-person'] in NO_STAGE and not c.find_parent(id='alumni'))
  assert docs['team.html'].select_one('#people-no-results')
  for slug in ['kubra-solmaz','rabia-ates','fatma-gazioglu','ipek-oz']:
   t=docs['person-'+slug+'.html'].main.get_text()
   assert 'Expected completion dates are plans' not in t
   assert '2022' in t or '2023' in t or '2024' in t
  for name,s in docs.items():
   if name.startswith('person-'):assert s.select_one('#academic-record dl.profile-facts'),name
  conf=docs['conference-iccai-2027.html'].main.get_text(' ',strip=True)
  assert ('23–26 Nisan 2027' if tr else '23–26 April 2027') in conf and ('Seul' if tr else 'Seoul') in conf
  assert ('Sözleşme: imza teyidi bulunmuyor.' if tr else 'Contract: no confirmation of signature recorded.') in docs['project-space-debris.html'].select_one('.project-meta').get_text()
  assert ('ilgi formuyla' if tr else 'interest form') in docs['join.html'].main.get_text()
  for name in ['site-notes.html','accessibility.html']:
   txt=docs[name].main.get_text();assert 'Tally' in txt and ('gömülü' if tr else 'embedded') in txt
  txt=docs['accessibility.html'].main.get_text();assert 'WCAG' in txt and 'PDF/UA' in txt
  assert len(docs['index.html'].select('.showcase-stat'))==3
  checks.append(lang+': metadata/search, submitted status, footer, stages, conference, consent wording, mobile access and accessibility notes')
 assert 'ampirik bir araştırma makalesi' in maintext('tr/person-omid-noroozi.html')
 for name,bad in [('tr/project-vr-stem-vietnam.html','araştırmacı profili eklenmesi'),('tr/project-ai-literacy-colombia.html','Sayfa başlığı çalışmayı betimleyen'),('tr/editorial.html','Editör adaylarına ilişkin iç görüşmeler')]:assert bad not in maintext(name)
 assert 'Öğretmenler için' not in maintext('practice.html')
 # PDF and editable Word: entries must sit beneath the submitted heading, not a planned heading.
 for lang,stem in [('en','Huseyin_Ates_Public_Academic_CV'),('tr','Huseyin_Ates_Akademik_Ozgecmis_TR')]:
  reader=PdfReader(SITE/'downloads'/f'{stem}.pdf');assert len(reader.pages)==3
  texts=[p.extract_text() for p in reader.pages];alltext=' '.join(texts);third=texts[2]
  assert '12 November 2026' not in alltext and '12 Nov 2026' not in alltext
  assert all(('13 November 2026' if lang=='en' else '13 Kasım 2026') in t for t in texts)
  assert 'no submitted application' not in alltext and 'Başvurunun sunulduğu veya ziyaretlerin kesinleştiği iddia edilmemektedir.' not in alltext
  header='Submitted proposals' if lang=='en' else 'Sunulmuş başvurular'
  end='Ongoing international research' if lang=='en' else 'Uluslararası araştırma geliştirme'
  submitted=third.split(header,1)[1].split(end,1)[0]
  assert 'TÜBİTAK 2221' in submitted and 'TÜBİTAK 3501' in submitted
  d=Document(SITE/'downloads'/f'{stem}.docx');ptext='\n'.join(p.text for p in d.paragraphs)
  assert 'TÜBİTAK 2221' in ptext.split(header,1)[1].split(end,1)[0]
  assert all('12 Nov' not in p.text for sec in d.sections for p in sec.footer.paragraphs)
  checks.append(lang+': 3-page PDF and DOCX submission groups and update dates')
 # Both downloadable CSVs and the archive agree with the existing Explorer scenario.
 rows=list(csv.DictReader((SITE/'downloads/fictional-plant-data.csv').open()))
 explorer=list(csv.DictReader((SITE/'downloads/synthetic-plant-example.csv').open()))
 for a,b in zip(rows,explorer):
  assert a['group']==b['plant']
  for k in ['light_hours_per_day','water_ml_per_day','growth_cm_over_week','plants_per_condition']:assert a[k]==b[k],k
  assert float(a['final_height_cm'])-float(a['initial_height_cm'])==float(b['growth_cm_over_week'])
 result=subprocess.check_output([sys.executable,str(SITE/'downloads/inspect_synthetic_example.py')],text=True)
 assert 'A: observed growth = 2.0 cm' in result and 'B: observed growth = 5.0 cm' in result
 with zipfile.ZipFile(SITE/'downloads/synthetic-methods-example.zip') as z:assert z.read('fictional-plant-data.csv')==(SITE/'downloads/fictional-plant-data.csv').read_bytes()
 checks.append('Single fictional plant scenario in Explorer, CSVs, Python output and ZIP')
 report={'release':'5.2','html_pages':len(paths),'profile_pages':60,'checks':checks,'result':'passed','limits':'No additional project-specific task assignments inferred for researchers whose source roster only states a role.'}
 (ROOT/'audit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
