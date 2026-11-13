#!/usr/bin/env python3
"""Apply the approved screenshot-inspired (but HTML-native) bilingual layout and factual project updates.

Runs after all other website builders.  No fictitious achievement metrics or personal portraits.
"""
from pathlib import Path
from html import escape as e
from bs4 import BeautifulSoup as Soup
import json,re,shutil
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
BASE='https://huseyinates38.github.io/'

def f(tr,en,tu):return tu if tr else en

def code(name):
 return {'ai':'ai','reason':'reason','srl':'srl','stem':'stem','edtech':'edtech'}[name]

def hero(tr):
 h1=f(tr,'Connecting people, technology and <em>science learning.</em>','İnsan, teknoloji ve fen öğrenimi arasında <em>anlamlı bağlar kurmak.</em>')
 intro=f(tr,'Research in human-centered AI, scientific reasoning, self-regulated learning and STEM education—to strengthen learning and teaching.','İnsan odaklı yapay zekâ, bilimsel akıl yürütme, öz düzenlemeli öğrenme ve STEM eğitimi üzerine çalışmalar yürütüyorum. Araştırmalarımda öğrenme süreçlerini ve öğretim uygulamalarını geliştirmeyi amaçlıyorum.')
 return f'''<section class="showcase-hero" aria-labelledby="showcase-title"><div class="showcase-hero-visual" aria-hidden="true"></div><div class="showcase-hero-shade" aria-hidden="true"></div><div class="showcase-wrap showcase-hero-content"><div class="showcase-hero-copy"><p class="showcase-overline">{f(tr,'SCIENCE EDUCATION · HUMAN-CENTERED ARTIFICIAL INTELLIGENCE','FEN EĞİTİMİ · İNSAN ODAKLI YAPAY ZEKÂ')}</p><h1 id="showcase-title">{h1}</h1><p>{intro}</p><div class="showcase-hero-actions"><a class="showcase-btn showcase-btn-main" href="research.html">{f(tr,'Research areas','Araştırma alanlarım')} <span aria-hidden="true">→</span></a><a class="showcase-btn showcase-btn-outline" href="team.html">{f(tr,'Team & collaborations','Ekip ve iş birlikleri')} <span aria-hidden="true">↗</span></a></div></div></div></section>'''

def topics(tr,prefix):
 items=[
  ('ai',f(tr,'Human-centered<br>AI','İnsan odaklı<br>yapay zekâ'),'research.html#human-centered-ai'),
  ('reason',f(tr,'Scientific<br>reasoning','Bilimsel<br>akıl yürütme'),'research.html#reasoning'),
  ('srl',f(tr,'Self-regulated<br>learning','Öz düzenlemeli<br>öğrenme'),'research.html#reasoning'),
  ('stem',f(tr,'STEM<br>education','STEM<br>eğitimi'),'research.html#technologies'),
  ('edtech',f(tr,'Educational<br>technology','Eğitim teknolojileri<br>ve yenilikçi öğrenme'),'research.html#technologies')
 ]
 return '<nav class="showcase-topics" aria-label="'+f(tr,'Research areas','Araştırma alanları')+'"><div class="showcase-wrap showcase-topic-grid">'+''.join(f'<a href="{href}" class="showcase-topic"><span class="showcase-topic-icon"><img src="{prefix}assets/showcase/icon-{key}.svg" alt="" width="52" height="52" decoding="async"/></span><span>{label}</span></a>' for key,label,href in items)+'</div></nav>'

def updates(tr,prefix):
 # Titles/status are kept compact, in meaningful human language, with verified distinctions.
 entries=[
  ('conference','ICCAI 2027',f(tr,'Oral presentation accepted','Sözlü sunum için kabul edildi'),f(tr,'Seoul · 23–26 April 2027','Seul · 23–26 Nisan 2027'),'conference-iccai-2027.html',f(tr,'Conference','Konferans'),'accepted'),
  ('travel','TÜBİTAK 2224-A',f(tr,'Participation-support application submitted','Katılım desteği başvurusu yapıldı'),f(tr,'Funding decision pending','Destek sonucu bekleniyor'),'conference-iccai-2027.html',f(tr,'Application','Başvuru'),'applied'),
  ('visitor','TÜBİTAK 2221',f(tr,'Visiting-scientist application submitted','Konuk bilim insanı başvurusu yapıldı'),f(tr,'Decision pending','Destek sonucu bekleniyor'),'proposal-visiting-researchers-2221.html',f(tr,'Application','Başvuru'),'applied'),
  ('grant','TÜBİTAK 3501',f(tr,'Research proposal submitted','Araştırma projesi başvurusu yapıldı'),f(tr,'Application not funded','Başvuru desteklenmedi'),'project-robot-virtual-agent.html',f(tr,'Proposal','Proje önerisi'),'notfunded'),
  ('orbit','TÜBİTAK 1002-A',f(tr,'Scientific support decision: 226K999','226K999 için bilimsel destek kararı'),f(tr,'Space-pollution problem-solving instruction','Uzay kirliliği problem çözme öğretimi'),'project-space-debris.html',f(tr,'Funded research','Araştırma desteği'),'supported')
 ]
 cards=[]
 for media,title,headline,note,href,typ,status in entries:
  card=f'''<article class="showcase-news-card"><a class="showcase-card-img" href="{href}" aria-label="{e(title+' — '+headline)}"><img src="{prefix}assets/showcase/card-{media}.svg" alt="" width="400" height="230" loading="lazy" decoding="async"/><span class="showcase-card-tag">{typ}</span></a><div class="showcase-card-copy"><h3><a href="{href}">{e(title)}</a></h3><p>{e(headline)}</p><div class="showcase-card-bottom"><span class="showcase-status showcase-status-{status}">{e(note)}</span><a class="showcase-card-go" href="{href}" aria-label="{e(f(tr,'Read more about ','Ayrıntıları görüntüle: ')+title)}"><span aria-hidden="true">→</span></a></div></div></article>'''
  cards.append(card)
 join=f'''<aside class="showcase-join-card"><div class="showcase-join-icon" aria-hidden="true">♧</div><h3>{f(tr,'Want to join our research group?','Çalışma grubuna katılmak ister misiniz?')}</h3><p>{f(tr,'If your interests include science education, artificial intelligence or STEM, we would be glad to hear about your research goals.','Fen eğitimi, yapay zekâ ve STEM alanlarındaki araştırmalara katkı sunmak isterseniz ilgi formundan bize ulaşabilirsiniz.')}</p><a class="showcase-join-cta" href="https://tally.so/r/Eq51Jr" target="_blank" rel="noopener noreferrer">{f(tr,'Research-group form','Başvuru sayfası')} <span aria-hidden="true">↗</span></a><a href="https://tally.so/r/Eq51Jr" class="showcase-join-qr" target="_blank" rel="noopener noreferrer"><img src="{prefix}assets/qr/research-group-interest.png" alt="{f(tr,'QR code for research-group application','Araştırma grubu katılım formuna yönlendiren QR kodu')}" width="110" height="110" loading="lazy"/><span>{f(tr,'Scan to open','QR kodunu okutun')}</span></a></aside>'''
 title=f(tr,'Current <em>highlights</em>','Güncel <em>gelişmeler</em>')
 return f'''<section class="showcase-news" aria-labelledby="showcase-news-heading"><div class="showcase-wrap"><div class="showcase-section-heading"><h2 id="showcase-news-heading">{title}</h2><a href="projects.html">{f(tr,'Explore projects','Tüm projeler')} <span aria-hidden="true">→</span></a></div><div class="showcase-news-layout"><div class="showcase-news-grid">{''.join(cards)}</div>{join}</div></div></section>'''

def stats(tr):
 values=[('23',f(tr,'Selected publications','Seçilmiş yayın')),
         ('2',f(tr,'Completed BAP projects','Tamamlanan BAP projesi')),
         ('4',f(tr,'Master’s alumni','Yüksek lisans mezunu')),
         ('2',f(tr,'Website languages','Site dili')),
         ('5',f(tr,'Research directions','Araştırma başlığı'))]
 icons=['▤','◇','♙','◫','◎']
 return f'<section class="showcase-stats" aria-label="{f(tr,"At a glance","Kısa bilgiler")}"><div class="showcase-wrap showcase-stats-grid">'+''.join(f'<div class="showcase-stat"><span class="showcase-stat-icon" aria-hidden="true">{ico}</span><strong>{n}</strong><span>{label}</span></div>' for (n,label),ico in zip(values,icons))+'</div></section>'

def featured(tr):
 entries=[
  (f(tr,'Generative AI feedback','Üretken yapay zekâ geri bildirimi'),f(tr,'Scientific argumentation and feedback design','Bilimsel argümantasyon ve geri bildirim tasarımı'),'study-genai-feedback.html'),
  (f(tr,'Self-regulated flipped learning','Öz düzenlemeli ters yüz öğrenme'),f(tr,'Self-regulation and science learning performance','Öz düzenleme ve fen öğrenme başarısı'),'study-self-regulated-flipped-learning.html'),
  (f(tr,'Intelligent tutoring & AR','Akıllı öğretim ve artırılmış gerçeklik'),f(tr,'Educational technology and learner support','Eğitim teknolojileri ve öğrenme desteği'),'study-ar-intelligent-tutoring.html')]
 cards=''.join(f'<article><span class="showcase-feature-index">0{i+1}</span><h3>{t}</h3><p>{d}</p><a href="{href}">{f(tr,"Study summary","Araştırma özeti")} <span aria-hidden="true">↗</span></a></article>' for i,(t,d,href) in enumerate(entries))
 return f'<section class="showcase-featured"><div class="showcase-wrap"><div class="showcase-section-heading"><h2>{f(tr,"Selected <em>research</em>","Seçilmiş <em>araştırmalar</em>")}</h2><a href="publications.html">{f(tr,"All publications","Tüm yayınlar")} <span aria-hidden="true">→</span></a></div><div class="showcase-featured-grid">{cards}</div></div></section>'

def home(s,tr):
 main=s.select_one('main')
 if not main:raise AssertionError('Missing main landmark')
 main.clear()
 # Each selected illustration is linked to a functioning information page.
 markup=hero(tr)+topics(tr,'../' if tr else '')+updates(tr,'../' if tr else '')+stats(tr)+featured(tr)
 main.append(Soup(markup,'html.parser'))
 # Strip inherited page layout/visual CSS conflicts by new classes.
 s.title.string=(f(tr,'Hüseyin Ateş | Science Education, AI & Research','Hüseyin Ateş | Fen Eğitimi, Yapay Zekâ ve Araştırma'))
 desc=f(tr,'Research in science education, human-centered artificial intelligence, scientific reasoning, and self-regulated learning.','Fen eğitimi, insan odaklı yapay zekâ, bilimsel akıl yürütme ve öz düzenlemeli öğrenme alanlarında araştırmalar.')
 m=s.select_one('meta[name="description"]')
 if m:m['content']=desc
 for m in s.select('meta[property="og:image"]'):m['content']=BASE+'assets/showcase/hero-studio.webp'
 for m in s.select('meta[property="og:description"]'):m['content']=desc

def simplify(s,tr,name):
 # Remove design/provenance notes intended for the author, without hiding actual statuses.
 patterns=[
  'Acceptance for inclusion in the proceedings is stated in the organiser',
  'This does not mean that the paper has already been published.',
  'Düzenleme kurulunun kabul yazısında bildiri kitabında yayımlanması da öngörülüyor; bildiri henüz yayımlanmış bir çalışma olarak listelenmiyor.',
  'The principal investigator reports this project as completed.',
  'The principal investigator reports',
  'The KAEÜ BAP VR-supported STEM project (EGT.A3.26.001), including the Vietnam-adaptability component, is completed as reported',
  'KAEÜ BAP destekli sanal gerçeklik temelli STEM projesi (EGT.A3.26.001), Vietnam bağlamına uyarlanabilirlik bileşeniyle birlikte',
  'No newly confirmed completion status',
  'Bu iki destekli proje için yeni bir tamamlanma bilgisi',
  'No new research findings are asserted here.',
  'Burada yeni bir araştırma bulgusu ileri sürülmemektedir.',
  'No outcomes or completion status are inferred from the calendar dates.',
  'The diagram describes the research scope, not findings',
  'This project remains completed; the collaboration profile does not reopen the project.',
  'No unreported results or completed fieldwork are inferred.',
  'This page does not report unpublished results',
  'This page describes the project scope; it does not report',
  'The page title is a descriptive study label.',
  'No participant responses, draft instruments or private operational documents are published.',
  'This page does not announce completed international data collection',
  'Status reviewed: 12 November 2026.',
  'These are not currently confirmed funded appointments',
  ]
 # Only individual paragraphs or aside blocks; no stripping across parent sections.
 for t in list(s.main.find_all(['p','aside','small','figcaption'])):
  if t.name=='aside' and not t.get('class') and t.find(['p','a','h3']):continue
  txt=t.get_text(' ',strip=True)
  if not txt:continue
  if any(p in txt for p in patterns):
   if t.name=='p':
    # Keep meaningful project text when appended note follows a substantive sentence.
    replacements=[
      ('The principal investigator reports this project as completed. Its research focus is documented, but findings and a Vietnam-based classroom implementation are not asserted without a public report.',''),
      ('The principal investigator reports this project as completed. The diagram describes the research scope, not findings or a verified classroom intervention in Vietnam.',''),
    ]
    for old,new in replacements:
     if old in txt:txt=txt.replace(old,new)
    if txt.strip() and not any(p in txt for p in patterns) and len(txt)>50:
     t.string=txt;continue
   t.decompose()
 # Explicitly simplify conference body while preserving the actual accepted type, paper id and date.
 if name=='conference-iccai-2027.html':
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if 'Paper ID: YS1001.' in t or 'Bildiri kodu: YS1001.' in t:
    p.string=f(tr,'The conference will be held in Seoul on 23–26 April 2027. Paper code: YS1001.','Konferans 23–26 Nisan 2027 tarihlerinde Seul’de düzenlenecektir. Bildiri kodu: YS1001.')

 def mark_complete(key):
  # Dedicated project detail pages, with no embellished outcomes or backdated dates.
  meta=s.select_one('.project-meta')
  if meta:
   d=meta.select_one('div')
   if d:
    h=d.find('strong');sp=d.find('span')
    if h:h.string=f(tr,'Status','Durum')
    if sp:sp.string=f(tr,'Completed','Tamamlandı')
  for dt in s.select('.project-side dt'):
   if any(z in dt.get_text(' ',strip=True).lower() for z in ['funding status','completion status','destek durumu','tamamlanma durumu']):
    dt.string=f(tr,'Project status','Proje durumu')
    dd=dt.find_next_sibling('dd')
    if dd:dd.string=f(tr,'Completed · KAEÜ BAP','Tamamlandı · KAEÜ BAP')
  for p in list(s.select('main p')):
   t=p.get_text(' ',strip=True)
   if any(x in t for x in ['The principal investigator reports','proje yürütücüsünün','bildirildi','project remains completed','no new research findings','kaynak olarak','göstermez']):
    if len(t)<250:p.decompose()
 if name in ['project-vr-stem-vietnam.html','project-vr-circulatory-system.html']:mark_complete(name)
 # Replace explanatory 'not funded' prose with the simple actual grant outcome for the old 3501.
 if name=='project-robot-virtual-agent.html':
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if t.startswith('Status boundary.') or t.startswith('Statü sınırı.'):
    p.string=f(tr,'The TÜBİTAK 3501 application was submitted but was not funded.','TÜBİTAK 3501 başvurusu yapıldı; desteklenmedi.')

def update_projects(s,tr):
 complete=s.select_one('#completed-projects')
 active=s.select_one('#funded-projects')
 if not complete or not active:raise AssertionError('Missing project grouping')
 if complete.select_one('a[href="project-vr-circulatory-system.html"]') is None:
  card=active.select_one('.project-summary:has(a[href="project-vr-circulatory-system.html"])')
  if card is None:raise AssertionError('Missing circulatory project card')
  card.extract();card['data-project-status']='completed';card['class']=list(dict.fromkeys(card.get('class',[])+['completed-project-card']))
  idx=card.select_one('.project-index')
  if idx:idx.string=f(tr,'PROJECT 04 · COMPLETED','PROJE 04 · TAMAMLANDI')
  complete.select_one('.project-overview-grid').append(card)
 # Hide verbose completion/provenance narratives while keeping both project cards.
 for sec in [complete,active]:
  for child in list(sec.select('.container > p')):child.decompose()
  title=sec.select_one('h2')
  if title:title.clear();title.append(Soup(f(tr,'Completed <em>projects</em>','Tamamlanan <em>projeler</em>') if sec is complete else f(tr,'Supported <em>research</em>','Desteklenen <em>araştırma</em>'),'html.parser'))
 # Change section order: completed two BAP projects together, first.
 complete.extract();active.insert_before(complete)
 # project badge labels
 for c in complete.select('.project-summary'):
  c['data-project-status']='completed'
  idx=c.select_one('.project-index')
  if idx and 'COMPLETED' not in idx.get_text() and 'TAMAMLANDI' not in idx.get_text():
   idx.string=idx.get_text(' ',strip=True).split(' · ')[0]+' · '+f(tr,'COMPLETED','TAMAMLANDI')
 # project filter is under supported and hides only current project; hide it to avoid counter lying about all three.
 panel=active.select_one('.v3-topic-filter')
 if panel:panel.decompose()
 # Header deep link for completed is now prominent.
 for a in s.select('.pagehero a[href="#funded-projects"]'):
  a['href']='#completed-projects';a.string=f(tr,'Completed projects','Tamamlanan projeler')


def header(s,tr,name):
 symbol=s.select_one('.brand-symbol')
 if symbol:
  svg='''<svg class="showcase-mark-svg" viewBox="0 0 64 50" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg"><path d="M32 43C20 34 14 33 3 33V11c14 1 23 6 29 16C38 17 47 12 61 11v22c-11 0-17 1-29 10Z" fill="none" stroke="#0b83c4" stroke-width="3.7" stroke-linejoin="round"/><path d="M32 26V43M18 8l-7-7m20 11V1m15 7 7-7" fill="none" stroke="#0875ad" stroke-width="3.5" stroke-linecap="round"/></svg>'''
  symbol.replace_with(Soup(svg,'html.parser'))
 s.header['class']=list(dict.fromkeys(s.header.get('class',[])+['showcase-header']))
 langnav=s.select_one('.site-language')
 if langnav:
  tr_tag=langnav.select_one('a[lang="tr"]')
  if tr_tag:
   tr_tag.extract();langnav.insert(0,tr_tag)
 for tag in s.select('.site-language a'):
  # The preferred language remains explicit on every page.
  if tag.get('aria-current')=='true':tag['aria-current']='page'
  else:tag.attrs.pop('aria-current',None)


def main():
 for tr in [False,True]:
  local=SITE/('tr' if tr else '')
  prefix='../' if tr else ''
  for file in sorted(local.glob('*.html')):
   s=Soup(file.read_text(encoding='utf-8'),'html.parser')
   name=file.name
   simplify(s,tr,name)
   if name=='index.html':home(s,tr)
   if name=='projects.html':update_projects(s,tr)
   header(s,tr,name)
   if not s.head.select_one('link[href*="showcase.css"]'):
    s.head.append(s.new_tag('link',rel='stylesheet',href=prefix+'assets/showcase.css?v=4.8'))
   file.write_text(str(s),encoding='utf-8')
 # Static assets referenced with language-relative paths in the delivered site.
 for p in (ROOT/'assets/showcase').iterdir():
  target=SITE/'assets/showcase'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 shutil.copy2(ROOT/'assets/showcase.css',SITE/'assets/showcase.css')
 for key in ['deployment.json','quality-report.json']:
  path=SITE/key
  if path.exists():
   j=json.loads(path.read_text());j['version' if key=='deployment.json' else 'release']='4.8';path.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Version 4.8: screenshot-inspired homepage, 5 cards, 2 completed BAP projects, editorial cleanup.')
if __name__=='__main__':main()
