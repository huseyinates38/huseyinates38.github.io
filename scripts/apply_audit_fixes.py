#!/usr/bin/env python3
"""Final bilingual editorial pass, applied after all layout builders.

Keeps existing research evidence and design; synchronises title metadata/search only
once the final visible content is ready. No unverified project assignments are added.
"""
from pathlib import Path
from html import escape
import hashlib,json,re,shutil
from bs4 import BeautifulSoup as Soup
from build_bilingual import metadata,build_index
from refine_profile_copy import refine
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';VERSION='5.2'
def pair(tr,en,turkish):return turkish if tr else en
def frag(x):return Soup(x,'html.parser')
def text(node,value):
 if node is not None:node.clear();node.append(value)
def paragraph_match(s,needle):return [p for p in s.select('main p') if needle in p.get_text(' ',strip=True)]
def drop_paragraphs(s,needles):
 for p in list(s.select('main p')):
  if any(x in p.get_text(' ',strip=True) for x in needles):p.decompose()
def replace_text(s,pairs):
 for n in list(s.find_all(string=True)):
  if not n.parent or n.parent.name in ['script','style','code','pre']:continue
  original=str(n);new=original
  for a,b in pairs:new=new.replace(a,b)
  if original!=new:n.replace_with(new)
def append_fragment(node,html):node.append(frag(html))

# Stage labels are drawn from the existing public records, not inferred from affiliations.
STAGES={
 'juan-garzon':('Study design and pilot preparation','Araştırma tasarımı ve pilot hazırlığı'),
 'omid-noroozi':('Joint manuscript development','Ortak makale hazırlığı'),
 'mohammadreza-farrokhnia':('Joint manuscript development','Ortak makale hazırlığı'),
 'kazem-banihashem':('Manuscript revision','Makale revizyonu'),
 'elena-novak':('Joint manuscript development','Ortak makale hazırlığı'),
 'guido-makransky':('Research design discussions','Araştırma tasarımı görüşmeleri'),
 'moritz-krell':('Research proposal development','Araştırma önerisi geliştirme'),
 'georgios-lampropoulos':('Ongoing manuscript collaboration','Devam eden makale iş birliği'),
 'naomi-winstone':('Manuscript development · 2219 decision pending','Makale hazırlığı · 2219 kararı bekleniyor'),
 'ahmet-sami-konca':('Joint research · AÜB decision pending','Ortak araştırma · AÜB kararı bekleniyor'),
 'juan-david-murillo-egurrola':('Instrument adaptation and pilot preparation','Ölçme aracı uyarlama ve pilot hazırlığı'),
 'bui-van-hong':('Academic contact · VR–STEM project completed','Akademik iletişim · VR–STEM projesi tamamlandı'),
 'marc-romero-carbonell':('Collection proposal · journal approval pending','Koleksiyon önerisi · dergi onayı bekleniyor'),
 'kibar-gul':('AÜB application team · decision pending','AÜB başvuru ekibi · karar bekleniyor'),
 'naciye-somuncu-demir':('AÜB application team · decision pending','AÜB başvuru ekibi · karar bekleniyor'),
 'yesim-taktat-ates':('AÜB application team · decision pending','AÜB başvuru ekibi · karar bekleniyor'),
 'gokhan-ince':('Research team member','Araştırma ekibi üyesi'),
 'zeynep-aydemir':('Research team member','Araştırma ekibi üyesi'),
 'ahmet-salih-simsek':('Research team member','Araştırma ekibi üyesi'),
 'serbay-durmaz':('Researcher · school practice','Araştırmacı · okul uygulamaları'),
 'ibrahim-delen':('Research adviser','Araştırma danışmanı'),
 'ipek-oz':('Researcher · master’s alumna (2022)','Araştırmacı · yüksek lisans mezunu (2022)'),
 'abdulkadir-aydin':('Doctoral research · expected 2028','Doktora araştırması · beklenen bitiş 2028'),
 'tugce-unsal':('Master’s research · expected 2027','Yüksek lisans araştırması · beklenen bitiş 2027'),
 'nisa-gul':('Master’s research · expected 2027','Yüksek lisans araştırması · beklenen bitiş 2027'),
 'irem-sude-koksal':('Master’s research · expected 2028','Yüksek lisans araştırması · beklenen bitiş 2028'),
 'furkan-ensar-ates':('Master’s research · expected 2028','Yüksek lisans araştırması · beklenen bitiş 2028'),
 'kubra-solmaz':('Master’s degree completed · 2024','Yüksek lisans tamamlandı · 2024'),
 'rabia-ates':('Master’s degree completed · 2023','Yüksek lisans tamamlandı · 2023'),
 'fatma-gazioglu':('Master’s degree completed · 2022','Yüksek lisans tamamlandı · 2022')}
GRAD={'abdulkadir-aydin':('PhD','Doktora','2028'),'tugce-unsal':('Master’s','Yüksek lisans','2027'),'nisa-gul':('Master’s','Yüksek lisans','2027'),'irem-sude-koksal':('Master’s','Yüksek lisans','2028'),'furkan-ensar-ates':('Master’s','Yüksek lisans','2028')}
ALUMNI={'kubra-solmaz':'2024','rabia-ates':'2023','fatma-gazioglu':'2022','ipek-oz':'2022'}
FORM_EN='Share your research interests or a proposal for collaboration using the interest form hosted on Tally. Formal graduate admission follows the university’s separate application process.'
FORM_TR='Araştırma ilginizi veya ortak çalışma önerinizi Tally üzerindeki ilgi formuyla paylaşabilirsiniz. Lisansüstü kabul işlemleri üniversitenin ayrı resmî başvuru süreciyle yürütülür.'

def common(s,name,tr):
 prefix='../' if tr else ''
 replace_text(s,[('iş birliklerindan','iş birliklerinden'),('iş birlikleridır','iş birlikleridir')])
 # Fix metadata later; cache-busted runtime code makes a stale script unlikely.
 for js in s.select('script[src]'):
  filename=js['src'].split('?')[0].split('/')[-1]
  if filename in ['bilingual.js','team-directory.js']:
   digest=hashlib.sha256((ROOT/'assets'/filename).read_bytes()).hexdigest()[:12]
   js['src']=prefix+'assets/'+filename+'?v='+digest
 footer=s.select_one('.footer-links')
 if footer:
  for a in list(footer.select('a[href*="Academic_CV"],a[href*="Akademik_Ozgecmis"]')):a.decompose()
  for label,file,lang in ([('Özgeçmiş · Türkçe PDF','Huseyin_Ates_Akademik_Ozgecmis_TR.pdf','tr'),('CV · English PDF','Huseyin_Ates_Public_Academic_CV.pdf','en')] if tr else [('Academic CV · English PDF','Huseyin_Ates_Public_Academic_CV.pdf','en'),('Özgeçmiş · Türkçe PDF','Huseyin_Ates_Akademik_Ozgecmis_TR.pdf','tr')]):
   a=s.new_tag('a',href=prefix+'downloads/'+file,hreflang=lang);a.string=label;footer.append(a)
 nav=s.select_one('#main-navigation')
 if nav and not nav.select_one('a[href="search.html"]'):
  a=s.new_tag('a',href='search.html',attrs={'class':'mobile-search-link'});a.string=pair(tr,'Search this site','Sitede ara');nav.append(a)
 # A single purpose for the same external form in both languages.
 for p in s.select('main p'):
  t=p.get_text(' ',strip=True)
  if any(x in t for x in ['Sending an expression of interest does not guarantee','İlgi bildirmek araştırma grubu üyeliği','Formu göndermek başvurunuzun değerlendirmeye alınmasını']):text(p,FORM_TR if tr else FORM_EN)
 for a in s.select('a[href="https://tally.so/r/Eq51Jr"]'):
  if a.select_one('img'):continue
  raw=a.get_text(' ',strip=True)
  if raw.startswith('https:'):continue
  text(a,pair(tr,'Research-group interest form','Araştırma grubu ilgi formu'))
 for im in s.select('img[src*="research-group-interest"]'):
  im['alt']=pair(tr,'QR code for the research-group interest form','Araştırma grubu ilgi formuna yönlendiren QR kod')
 # Align ordinary links to the newly named application record.
 for a in s.select('a[href="proposal-visiting-researchers-2221.html"]'):
  if any(v in a.get_text().lower() for v in ['planning','planlaması','proposed visiting','planlanan konuk']):
   text(a,pair(tr,'TÜBİTAK 2221 Visiting-Researcher Application','TÜBİTAK 2221 Konuk Araştırmacı Başvurusu'))


def person(s,slug,tr):
 # Specific unrelated forward-looking disclaimers are removed, not the substantive record.
 if slug in ALUMNI:
  drop_paragraphs(s,['Expected completion dates are plans, not awarded degrees.','Danışmanlık ilişkisi, istihdam veya fonlu projeye atanma anlamına gelmez.'])
 if slug=='omid-noroozi' and tr:
  replace_text(s,[('deneysel bir makale','ampirik bir araştırma makalesi'),('deneysel makale','ampirik araştırma makalesi')])
 if slug not in STAGES:return
 hero=s.select_one('main .pagehero .container')
 if hero and not hero.select_one('.relationship-stage'):
  p=s.new_tag('p',attrs={'class':'relationship-stage'});p.string=STAGES[slug][tr];hero.append(p)
 # Uniform concise record uses only roles, topics and dates already supplied.
 role=s.select_one('.pagehero .eyebrow');topic=s.select_one('.pagehero .lead')
 fields=[(pair(tr,'Role / academic relationship','Rol / akademik ilişki'),role.get_text(' ',strip=True) if role else STAGES[slug][tr]),
         (pair(tr,'Research focus','Araştırma odağı'),topic.get_text(' ',strip=True) if topic else STAGES[slug][tr]),
         (pair(tr,'Current stage','Güncel aşama'),STAGES[slug][tr])]
 if slug in GRAD:
  degree_en,degree_tr,year=GRAD[slug]
  fields=[(pair(tr,'Degree programme','Derece programı'),degree_tr if tr else degree_en),
          (pair(tr,'Supervisor','Danışman'),'Hüseyin Ateş'),
          (pair(tr,'Expected completion','Öngörülen bitiş'),year),
          (pair(tr,'Research focus','Araştırma odağı'),topic.get_text(' ',strip=True) if topic else '')]
  if slug in ['abdulkadir-aydin','irem-sude-koksal','furkan-ensar-ates']:
   fields[-1]=(fields[-1][0],pair(tr,'Thesis topic not yet announced on this profile.','Tez konusu bu profilde henüz duyurulmadı.'))
 if slug in ALUMNI:
  fields.append((pair(tr,'Completed degree','Tamamlanan derece'),pair(tr,'Master’s · ','Yüksek lisans · ')+ALUMNI[slug]))
  fields.append((pair(tr,'Thesis supervisor','Tez danışmanı'),'Hüseyin Ateş'))
 # Reuse any existing record section to avoid duplicate schema panels.
 record=s.select_one('#academic-record')
 if record is None:
  for h in s.select('main h2'):
   if h.get_text(' ',strip=True) in ['Academic research record','Akademik çalışma']:
    record=h.find_parent('section');break
 if record is None:
  record=s.new_tag('section',attrs={'class':'section profile-record-section','id':'academic-record'})
  target=s.select_one('main .pagehero');target.insert_after(record)
 else:record['id']='academic-record';record.clear()
 record.append(frag('<div class="container"><h2>'+pair(tr,'Academic profile','Akademik profil')+'</h2><dl class="profile-facts">'+''.join('<div><dt>'+escape(k)+'</dt><dd>'+escape(v)+'</dd></div>' for k,v in fields)+'</dl></div>'))


def team(s,tr):
 text(s.select_one('.pagehero .lead'),pair(tr,'Researchers working together on science education and human-centered AI, including external collaborators, project advisers, graduate researchers and alumni.','Fen eğitimi ve insan odaklı yapay zekâ üzerine birlikte çalışan araştırmacılar, dış araştırma ortakları, proje danışmanları, lisansüstü araştırmacılar ve mezunlar.'))
 for c in s.select('.person-card[data-person]'):
  slug=c['data-person'];key='ipek-oz' if slug=='ipek-oz-alumna' else slug
  if key in STAGES:
   st=STAGES[key][tr]
   if slug=='ipek-oz-alumna':st=pair(tr,'Master’s degree completed · 2022','Yüksek lisans tamamlandı · 2022')
   p=s.new_tag('p',attrs={'class':'relationship-stage'});p.string=st
   link=c.select_one('a[href^="person-"]');link.insert_before(p) if link else c.append(p)
  if key in ALUMNI and c.find_parent(id='alumni'):
   text(c.select_one('.micro-label'),pair(tr,'Master’s graduate · ','Yüksek lisans mezunu · ')+ALUMNI[key])
 tools=s.select_one('#directory-search .directory-tools')
 if tools:
  empty=s.new_tag('p',attrs={'id':'people-no-results','hidden':'','role':'status'});empty.string=pair(tr,'No matching records. Try a researcher’s name, institution or country, or clear the search.','Eşleşen kayıt bulunamadı. Araştırmacı adı, kurum veya ülke ile arayın ya da aramayı temizleyin.');tools.append(empty)
 # Explain the research network rather than the document-production workflow.
 for p in s.select('main p'):
  t=p.get_text(' ',strip=True)
  if 'supplied posters' in t or 'paylaşılan afiş' in t or 'afiş kaydının' in t:
   if '43' in t or '22' in t:text(p,pair(tr,'The network spans 22 countries and 43 institutions, encompassing manuscript collaboration, research development and scholarly exchange. Current activities are described in the researcher profiles.','Araştırma ağı 22 ülke ve 43 kurumu kapsar; ortak makale hazırlığı, araştırma geliştirme ve akademik iletişimden oluşur. Güncel çalışmalar araştırmacı profillerinde açıklanır.'))


def cleanup(s,name,tr):
 if name.startswith('project-'):
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if t.startswith(('For protocols, collaboration','Protokol, iş birliği veya araştırma materyali talepleri')):
    text(p,pair(tr,'Contact the project lead about the research protocol, materials or collaboration.','Araştırma protokolü, materyaller veya iş birliği için proje yürütücüsüyle iletişime geçebilirsiniz.'))
 if name=='project-vr-stem-vietnam.html':
  drop_paragraphs(s,['araştırmacı profili eklenmesi projenin yeniden başladığı','Proje yürütücüsü çalışmanın tamamlandığını bildirmiştir.','This project remains completed;'])
  # The output has no published results to populate this heading: remove the empty panel.
  for h in list(s.select('main h2')):
   if h.get_text(' ',strip=True) in ['Interpreting the scope .','Interpreting the scope.','Araştırma kapsamını yorumlamak']:
    parent=h.parent
    if not parent.select('p:not(.eyebrow), a, li'):parent.decompose()
 if name=='project-ai-literacy-colombia.html':
  drop_paragraphs(s,['Sayfa başlığı çalışmayı betimleyen bir addır.','Bu sayfa uluslararası veri toplamanın tamamlandığını','Katılımcı yanıtları, taslak ölçme araçları'])
  replace_text(s,[(' These are study contributions, not claims of employment or funding.',''),(' Bunlar çalışmaya katkılardır; istihdam veya destek iddiası değildir.','')])
 if name=='editorial.html':
  drop_paragraphs(s,['Editör adaylarına ilişkin iç görüşmeler','Internal candidate discussions'])
  for h in list(s.select('main h2')):
   if h.get_text(' ',strip=True) in ['Keep the roles clear .','Keep the roles clear.','Görevlerin ayrımı']:
    sec=h.find_parent('section')
    if sec:sec.decompose()
 if name=='conference-iccai-2027.html':
  panel=s.select_one('.profile-summary > div')
  if panel and not panel.select_one('.conference-date-place'):
   p=s.new_tag('p',attrs={'class':'conference-date-place'});p.string=pair(tr,'23–26 April 2027 · Seoul, South Korea. Paper code: YS1001.','23–26 Nisan 2027 · Seul, Güney Kore. Bildiri kodu: YS1001.')
   # Replace a pre-existing date paragraph instead of repeating it.
   old=next((n for n in panel.select('p') if '23–26' in n.get_text()),None)
   if old:old.replace_with(p)
   else:panel.select_one('a').insert_before(p)
 if name=='practice.html' and not tr:
  for n in list(s.select('main [lang="tr"]')):
   sec=n if n.name=='section' else n.find_parent('section')
   if sec:sec.decompose()
  for h in list(s.select('main h2')):
   if 'Araştırma bulgusu ile' in h.get_text():
    sec=h.find_parent('section')
    if sec:sec.decompose()
  replace_text(s,[('For teachers / Öğretmenler için','For teachers')])
  s.main.append(frag('<section class="section muted"><div class="container"><h2>Research findings and teaching examples</h2><p>Research briefs describe published studies. The worksheets are teaching examples created for this site, not validated assessment instruments.</p><a class="textlink" href="tr/practice.html" hreflang="tr">Türkçe sürüm →</a></div></section>'))
 if name=='open-research.html':
  for code in s.select('pre code'):
   raw=code.get_text().replace('A: observed growth = 6.0 cm','A: observed growth = 2.0 cm').replace('B: observed growth = 2.0 cm','B: observed growth = 5.0 cm')
   text(code,raw)
  kit=s.select_one('#methods-kit .v3-box') or s.select_one('#methods-kit .container')
  if kit:
   p=s.new_tag('p',attrs={'class':'scenario-link'});p.string=pair(tr,'This is the same one-week plant example used in the Feedback Design Explorer: A receives 4 hours of light and 20 mL of water per day and grows 2 cm; B receives 8 hours and 40 mL and grows 5 cm.','Bu örnek, Geri Bildirim Tasarımı Keşif Aracı’ndaki bir haftalık bitki senaryosuyla aynıdır: A günde 4 saat ışık ve 20 mL su alır, 2 cm büyür; B günde 8 saat ışık ve 40 mL su alır, 5 cm büyür.');kit.append(p)
 if name in ['project-vr-circulatory-system.html','project-vr-stem-vietnam.html']:
  replace_text(s,[('What the project examines .','Research focus'),('What the project examines.','Research focus'),('Proje neyi inceliyor?','Araştırmanın odağı'),('This university-supported project investigates','This university-supported project investigated'),('fen öğrenimini inceliyor.','fen öğrenimini inceledi.')])
 if name=='project-space-debris.html':
  label=pair(tr,'Scientific support approved · 28 August 2026','Bilimsel destek kararı · 28 Ağustos 2026')
  second=pair(tr,'Contract: no confirmation of signature recorded.','Sözleşme: imza teyidi bulunmuyor.')
  meta=s.select_one('.project-meta')
  if meta:
   new=s.new_tag('div',attrs={'class':'funding-stage'});append_fragment(new,'<strong>'+pair(tr,'Current stage','Güncel aşama')+'</strong><span>'+label+'</span><small>'+second+'</small>');meta.append(new)
  for dt in s.select('.project-side dt'):
   if dt.get_text(strip=True) in ['Funding status','Destek durumu']:
    text(dt,pair(tr,'Current stage','Güncel aşama'));text(dt.find_next_sibling('dd'),label+' · '+second)
 if name=='research.html':replace_text(s,[('Explore the research connections','Connections between research concepts'),('Araştırma iş birliklerini keşfedin','Araştırma kavramları arasındaki ilişkiler')])
 if name=='resource-use.html':
  replace_text(s,[('The six teaching guides, their working sheets','The three thematic teaching sets, each with a guide and a worksheet'),('Altı öğretim rehberi ve çalışma yaprakları','Her biri rehber ve çalışma yaprağı içeren üç öğretim seti')])
 if name=='proposal-visiting-researchers-2221.html':
  for dt in s.select('dt'):
   if dt.get_text(' ',strip=True) in ['Status reviewed','Durum kontrolü']:text(dt.find_next_sibling('dd'),pair(tr,'13 November 2026','13 Kasım 2026'))
 if name=='resources.html':
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if t.startswith(('Six bilingual guides','Aranabilir PDF ve düzenlenebilir Word biçiminde altı')):
    text(p,pair(tr,'Three thematic sets, each containing a teacher guide and a worksheet. Each set is available in English and Turkish, as a PDF and an editable Word document.','Her biri öğretmen rehberi ve çalışma yaprağı içeren üç tematik set. Her setin Türkçe ve İngilizce PDF ve düzenlenebilir Word sürümleri bulunmaktadır.'))
 if name=='resource-argumentation.html' and tr:
  replace_text(s,[('Feedback Explorer','Geri Bildirim Tasarımı Keşif Aracı'),('Feedback Design Explorer','Geri Bildirim Tasarımı Keşif Aracı')])
  for a in s.select('a[href="feedback-explorer.html"]'):text(a,'Geri Bildirim Tasarımı Keşif Aracı →')
 if name in ['about.html','contact.html'] and tr:
  replace_text(s,[('Fen Bilgisi Eğitimi alanında akademisyen','Fen Bilgisi Eğitimi öğretim üyesi')])
 if name in ['team.html','research-network.html']:
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if ('22' in t and '43' in t and ('posters' in t or 'afiş' in t)):
    text(p,pair(tr,'The research network encompasses 43 institutions in 22 countries through publication collaborations, research development, COST proposals and academic exchange. Activities and their current stages are described in the relevant researcher and project profiles.','Araştırma ağı; yayın iş birlikleri, araştırma geliştirme, COST başvuruları ve akademik iletişim yoluyla 22 ülkeden 43 kurumu kapsar. Çalışmalar ve güncel aşamaları, ilgili araştırmacı ve proje sayfalarında açıklanır.'))
   elif 'posters' in t and 'Additional affiliations' in t or 'Kurumlar ve ülke sayıları, 2026–2028' in t:
    text(p,pair(tr,'The directory represents the 2026–2028 research-network overview. Individual profiles describe current affiliations and the type of collaboration.','Dizin, araştırma ağının 2026–2028 dönemine ilişkin görünümünü sunar. Güncel kurum bilgileri ve iş birliğinin türü, kişisel profillerde açıklanır.'))
 if name in ['site-notes.html','accessibility.html']:
  for p in s.select('main p'):
   t=p.get_text(' ',strip=True)
   if ('application form' in t or 'başvuru formu' in t) and any(w in t for w in ['analytics','Analitik','analitik']):
    text(p,pair(tr,'This site has no embedded application form, analytics or tracking cookies. Search and interactive examples run locally and do not store student responses. The research-group interest link opens an external Tally form; information submitted there is handled by that service. GitHub Pages and external services have their own access and privacy practices.','Sitede gömülü başvuru formu, analitik veya izleme çerezi bulunmaz. Arama ve etkileşimli örnekler tarayıcıda çalışır; öğrenci yanıtlarını kaydetmez. Araştırma grubu ilgi formu bağlantısı dışarıdaki Tally formunu açar; orada gönderilen bilgiler ilgili hizmet tarafından işlenir. GitHub Pages ve dış hizmetlerin kendi erişim ve gizlilik uygulamaları vardır.'))
 if name=='index.html':
  for stat in list(s.select('.showcase-stat')):
   if any(v in stat.get_text() for v in ['Website languages','Site dili','Research directions','Araştırma başlığı']):stat.decompose()
  grid=s.select_one('.showcase-stats-grid')
  if grid:grid['class']=grid.get('class',[])+['academic-stats-three']


def main():
 auditcss=ROOT/'assets/audit-fixes.css';shutil.copy2(auditcss,SITE/'assets/audit-fixes.css')
 for name in ['bilingual.js','team-directory.js']:shutil.copy2(ROOT/'assets'/name,SITE/'assets'/name)
 all_docs={}
 for lang in ['en','tr']:
  tr=lang=='tr';folder=SITE/('tr' if tr else '');docs={}
  for path in sorted(folder.glob('*.html')):
   name=path.name;s=Soup(path.read_text(encoding='utf-8'),'html.parser')
   common(s,name,tr);cleanup(s,name,tr)
   if name.startswith('person-'):person(s,name[7:-5],tr)
   if name in ['team.html','research-network.html']:team(s,tr) if name=='team.html' else replace_text(s,[('iş birliklerindan','iş birliklerinden'),('iş birlikleridır','iş birlikleridir')])
   refine(s,name,tr)
   # Titles and sharing metadata are derived from the final, visible content, in both languages.
   metadata(s,name,lang)
   for old in s.select('link[href*="audit-fixes.css"]'):old.decompose()
   csshash=hashlib.sha256(auditcss.read_bytes()).hexdigest()[:12]
   s.head.append(s.new_tag('link',rel='stylesheet',href=('../' if tr else '')+'assets/audit-fixes.css?v='+csshash))
   s.body['data-content-release']=VERSION;docs[name]=s
  build_index(docs,lang)
  for name,s in docs.items():
   html=str(s).replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio=')
   (folder/name).write_text(html,encoding='utf-8')
  all_docs[lang]=docs
 for filename in ['deployment.json','quality-report.json']:
  path=SITE/filename;j=json.loads(path.read_text());j['version' if filename=='deployment.json' else 'release']=VERSION;j['content_review_date']='2026-11-13';j['editorial_audit']='application/CV consistency, bilingual parity, literal search, profile stage labels, mobile access, metadata and teaching-scenario consistency';j.pop('files',None);path.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
 print('AUDIT 5.2: final bilingual copy, shared metadata/search, profile stages and accessible mobile search applied.')
if __name__=='__main__':main()
