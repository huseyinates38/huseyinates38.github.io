#!/usr/bin/env python3
"""Extend the existing bilingual site with approved affiliations and research-network records."""
from pathlib import Path
from html import escape as e
import copy,json,shutil,re,base64,lzma,hashlib
from bs4 import BeautifulSoup as Soup
from build_bilingual import metadata,build_index
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';BASE='https://huseyinates38.github.io/'
DATA=json.loads((ROOT/'content/team-directory.json').read_text())
ONGOING=json.loads((ROOT/'content/ongoing-collaborations.json').read_text())
NEW={p['slug']:p for p in DATA['new_people']}
FORM_URL='https://tally.so/r/Eq51Jr'
OFFICIAL_1002_TITLE_TR='Uzay Kirliliği Problem Çözme Öğretiminde İki Pedagojik İskele Yaklaşımının Sınıf İçi Pilot Karşılaştırması'
OFFICIAL_1002_TITLE_EN='Classroom Pilot Comparison of Two Pedagogical Scaffolding Approaches to Space-Pollution Problem Solving'

AFF={**DATA['affiliations'],**{k:v['institutions'] for k,v in NEW.items()}}
LABELS={
 'collaborators':('Ongoing research collaborations','Devam Eden Araştırma İş Birlikleri'),
 'project-researchers':('Project researchers','Proje Araştırmacıları'),
 'project-contributors':('Research practitioners & advisers','Araştırmacılar ve Danışmanlar'),
 'editorial-collaborators':('Ongoing editorial collaboration','Devam Eden Editoryal İş Birliği'),
 'graduate-researchers':('Graduate researchers','Lisansüstü Araştırmacılar'),
 'alumni':('Research alumni','Mezun Araştırmacılar')}

def pick(value,lang):return value[lang=='tr']
def fragment(html):return Soup(html,'html.parser')
def sethtml(node,html):node.clear();node.append(fragment(html))
def country(code,lang):
 return '<span class="country-tag"><span aria-hidden="true">'+''.join(chr(127397+ord(c)) for c in code)+'</span> '+e(pick(DATA['countries'][code],lang))+'</span>'
def affiliations(keys,lang,alumni=False):
 if not keys:return '<div class="affiliation-list"><p class="independent-label">'+pick(('Independent researcher · no institutional affiliation','Bağımsız araştırmacı · kurumsal bağlılığı yok'),lang)+'</p></div>'
 parts=[]
 for key in keys:
  ins=DATA['institutions'][key];logo=ins.get('logo',key);path=SITE/'assets/institutions'/f'{logo}.png'
  label=pick(ins['names'],lang);alt=pick(ins.get('logo_label',[label+' logo',label+' logosu']),lang)
  prefix='../' if lang=='tr' else ''
  if ins.get('text_mark') and not path.is_file():
   # Clearly typeset institution name instead of inventing a purported official logo.
   image='<span class="institution-mark institution-text-mark" aria-label="'+e(label)+'">'+e(ins['text_mark'])+'</span>'
  else:
   if not path.is_file():raise FileNotFoundError('Reviewed institutional mark missing: '+str(path))
   image=f'<span class="institution-mark'+(' dark' if ins.get('dark') else '')+f'"><img src="{prefix}assets/institutions/{logo}.png" alt="{e(alt)}" width="120" height="54" loading="lazy" decoding="async"/></span>'
  context=pick(('Degree institution','Mezun olunan kurum'),lang) if alumni else pick(('Institution','Kurum'),lang)
  parts.append(f'<div class="affiliation-item">{image}<div><span class="affiliation-kind">{context}</span><a href="{e(ins["url"])}" class="institution-name">{e(label)}</a>{country(ins["country"],lang)}</div></div>')
 return '<div class="affiliation-list">'+''.join(parts)+'</div>'
def section(body,id_='',tone='white'):
 return f'<section class="section {tone}"'+(f' id="{id_}"' if id_ else '')+'><div class="container">'+body+'</div></section>'
def link(label,url,cls='textlink'):return f'<a class="{cls}" href="{e(url)}">{e(label)} <span aria-hidden="true">↗</span></a>'
def asset(s,lang):
 prefix='../' if lang=='tr' else ''
 if not s.select_one('link[href$="team-directory.css"]'):s.head.append(s.new_tag('link',attrs={'rel':'stylesheet','href':prefix+'assets/team-directory.css'}))
 if not s.select_one('script[src$="team-directory.js"]'):s.body.append(s.new_tag('script',attrs={'src':prefix+'assets/team-directory.js','defer':''}))
def shell(template,name,lang,body):
 s=copy.deepcopy(template);sethtml(s.main,body);s.html['lang']=lang
 for a in s.select('.site-language a'):
  dest=a.get('lang')
  # A local same-language URL and a matching cross-language URL.
  a['href']=('tr/'+name if lang=='en' else name) if dest=='tr' else (name if lang=='en' else '../'+name)
 for n in s.select('script[type="application/ld+json"]'):n.decompose()
 asset(s,lang);metadata(s,name,lang)
 return s

def new_card(p,lang):
 title=(pick(p.get('titles',['','']),lang)+' '+p['name']).strip()
 return fragment('<article class="person-card"><div class="person-top"><div><p class="micro-label">'+e(pick(p['role'],lang))+'</p><h3>'+e(title)+'</h3></div></div><p class="person-topic">'+e(pick(p['topic'],lang))+'</p>'+affiliations(p['institutions'],lang)+link(pick(('View profile','Profili incele'),lang),'person-'+p['slug']+'.html')+'</article>').article

def new_profile(p,lang,template):
 name='person-'+p['slug']+'.html'; title=(pick(p.get('titles',['','']),lang)+' '+p['name']).strip()
 body='<section class="pagehero"><div class="container"><p class="eyebrow">'+e(pick(p['role'],lang))+'</p><h1>'+e(title)+'</h1><p class="lead">'+e(pick(p['topic'],lang))+'</p></div></section>'
 body+=section('<div class="profile-summary"><div><h2>'+pick(('Academic connection','Akademik ilişki'),lang)+'</h2><p class="lead">'+e(pick(p['description'],lang))+'</p>'+''.join(link(pick(x[:2],lang),x[2]) for x in p.get('links',[]))+'</div><aside>'+affiliations(p['institutions'],lang)+'</aside></div>')
 if p['slug'] in ONGOING:
  paragraphs=''.join('<p>'+e(t)+'</p>' for t in ONGOING[p['slug']][lang])
  body+=section('<h2>'+pick(('Ongoing academic connection','Süren akademik bağlantı'),lang)+'</h2>'+paragraphs,'muted')
 if p['slug']=='ipek-oz':
  body+=section('<h2>'+pick(('Completed master’s degree','Tamamlanan yüksek lisans'),lang)+'</h2><p>'+pick(('Master’s degree in 2022 under the supervision of Hüseyin Ateş. The thesis investigated science teachers’ intention to use distance-education tools with structural equation modelling.','Hüseyin Ateş danışmanlığındaki yüksek lisans derecesini 2022’de tamamladı. Tez çalışmasında fen öğretmenlerinin uzaktan eğitim araçlarını kullanma niyetini yapısal eşitlik modellemesiyle inceledi.'),lang)+'</p>'+affiliations(['kaeu'],lang,alumni=True),'ipek-masters','muted')
 body+=section(link(pick(('Back to the research team','Araştırma ekibine dön'),lang),'team.html','btn alt'))
 return shell(template,name,lang,body)

def enhance_profiles(docs,lang):
 for slug,keys in AFF.items():
  name='person-'+slug+'.html'
  if name not in docs or slug in NEW:continue
  s=docs[name];asset(s,lang)
  container=s.select_one('.pagehero .container');container.append(fragment(affiliations(keys,lang,slug in ['kubra-solmaz','rabia-ates','fatma-gazioglu'])))
  if slug=='georgios-lampropoulos':
   # Remove outdated source narrative that still mentions University of Crete.
   for prior_note in list(s.main.find_all('p')):
    narrative=prior_note.get_text(' ',strip=True)
    if ('University of Crete' in narrative or 'Girit Üniversitesi' in narrative):prior_note.decompose()
   eyebrow=container.select_one('.eyebrow');eyebrow.string=pick(('Research collaborator · Academic affiliations','Araştırma ortağı · Akademik kurumlar'),lang)
   georgios_affiliations=(
    '<ul><li><strong>Department of Education, University of Nicosia</strong> · 2417 Nicosia, Cyprus</li><li><strong>Department of Applied Informatics, School of Information Sciences, University of Macedonia</strong> · 54636 Thessaloniki, Greece</li></ul>',
    '<ul><li><strong>University of Nicosia, Department of Education</strong> · Lefkoşa 2417, Kıbrıs</li><li><strong>University of Macedonia, School of Information Sciences, Department of Applied Informatics</strong> · Selanik 54636, Yunanistan</li></ul>'
   )
   s.main.append(fragment(section('<h2>'+pick(('Academic affiliations','Akademik kurumlar'),lang)+'</h2>'+pick(georgios_affiliations,lang))))
   for ld in s.select('script[type="application/ld+json"]'):
    try:
     obj=json.loads(ld.string or '{}')
     if obj.get('@type')=='Person':obj['affiliation']=[{'@type':'CollegeOrUniversity','name':DATA['institutions'][k]['names'][0]} for k in keys];ld.string=json.dumps(obj,ensure_ascii=False)
    except ValueError:pass
  if slug in ONGOING:
   paragraphs=''.join('<p>'+e(t)+'</p>' for t in ONGOING[slug][lang])
   heading=pick(('Ongoing academic work','Devam Eden Akademik Çalışmalar'),lang)
   s.main.append(fragment(section('<h2>'+heading+'</h2>'+paragraphs,'ongoing-research','muted')))
  metadata(s,name,lang)



def research_interest(lang,compact=False):
 prefix='../' if lang=='tr' else ''
 lead=pick(('Join the research conversation','Araştırma grubuna katılmak ister misiniz?'),lang)
 body=pick(('Have a research idea or an interest in working with the group? Share it using the research-group interest form.','Araştırma grubuyla paylaşmak istediğiniz bir araştırma fikri veya iş birliği öneriniz varsa ilgi formunu doldurabilirsiniz.'),lang)
 label=pick(('Open the research-group interest form','Araştırma grubu katılım formunu aç'),lang)
 note=pick(('The form opens on Tally. Sending an expression of interest does not guarantee research-group membership, funding or admission.','Form Tally üzerinden açılır. İlgi bildirmek araştırma grubu üyeliği, burs veya kesin kabul anlamına gelmez.'),lang)
 qralt=pick(('QR code to open the research-group interest form','Araştırma grubu katılım formunu açan QR kod'),lang)
 return section('<div class="research-join"><div><p class="eyebrow">'+pick(('Research group · Open enquiry','Araştırma grubu · Katılım formu'),lang)+'</p><h2>'+lead+'</h2><p>'+body+'</p><p>'+link(label,FORM_URL,'btn')+'</p><p class="join-form-url"><a href="'+FORM_URL+'" target="_blank" rel="noopener noreferrer">'+FORM_URL+'</a></p><p class="v3-small">'+note+'</p></div><a class="research-join-qr" href="'+FORM_URL+'" target="_blank" rel="noopener noreferrer" aria-label="'+qralt+'"><img src="'+prefix+'assets/qr/research-group-interest.png" alt="'+qralt+'" width="220" height="220" loading="lazy" decoding="async"/><span>'+pick(('Scan or click','Tara veya tıkla'),lang)+'</span></a></div>','research-interest','white')

def network_intro(lang,full=False):
 url='research-network.html';prefix='../' if lang=='tr' else ''
 heading=pick(('A network of research connections','Araştırma bağlantılarından oluşan bir ağ'),lang)
 text=pick(('The supplied 2026–2028 network posters cover 22 countries and 43 institutions, across COST proposals, publication collaborations, projects and exploratory discussions. These are individual academic connections, not a claim that all institutions are formal or funded partners.','Paylaşılan 2026–2028 ağ afişleri; COST başvuruları, yayın iş birlikleri, projeler ve görüşmeler kapsamında 22 ülke ve 43 kurumu kapsıyor. Bunlar bireysel akademik bağlantılardır; tüm kurumların resmî veya fonlanan proje ortağı olduğu anlamına gelmez.'),lang)
 stats='<div class="network-stats"><div><strong>22</strong><span>'+pick(('countries','ülke'),lang)+'</span></div><div><strong>43</strong><span>'+pick(('institutions','kurum'),lang)+'</span></div><div><strong>2026–2028</strong><span>'+pick(('poster reference period','afişin referans dönemi'),lang)+'</span></div></div>'
 img=f'<a href="{prefix}assets/network/research-network-{lang}.svg" class="network-preview" target="_blank" rel="noopener"><img src="{prefix}assets/network/research-network-{lang}.svg" alt="'+pick(('Research-network poster with 22 countries and 43 institutions; the complete readable list follows on the network page.','22 ülke ve 43 kurumu gösteren araştırma ağı afişi; okunabilir kurum listesi ağ sayfasında yer alır.'),lang)+'" width="1440" height="1017" loading="lazy" decoding="async"/><span>'+pick(('Open the poster at full size ↗','Afişi tam boyutta aç ↗'),lang)+'</span></a>'
 if not full:return section('<div class="network-callout"><div><p class="eyebrow">'+pick(('International academic network','Uluslararası akademik ağ'),lang)+'</p><h2>'+heading+'</h2>'+stats+'<p>'+text+'</p>'+link(pick(('Explore the collaboration network','İş birliği ağını incele'),lang),url,'btn')+'</div>'+img+'</div>','research-network','muted')
 return '<section class="pagehero"><div class="container"><p class="eyebrow">'+pick(('Research group / International connections','Çalışma grubu / Uluslararası bağlantılar'),lang)+'</p><h1>'+pick(('International research<br/><em>connections.</em>','Uluslararası araştırma<br/><em>bağlantıları.</em>'),lang)+'</h1><p class="lead">'+text+'</p>'+stats+'</div></section>'+section(img+'<div class="buttonrow">'+link(pick(('English poster · PDF','İngilizce afiş · PDF'),lang),prefix+'downloads/research-network-en.pdf','btn alt')+link(pick(('Turkish poster · PDF','Türkçe afiş · PDF'),lang),prefix+'downloads/research-network-tr.pdf','btn alt')+'</div><p class="v3-small">'+pick(('Web-optimised renderings of the two supplied posters. The poster period is not the grant period of every activity. Current funding and completion statuses remain on the project pages.','Paylaşılan iki afişin web için optimize edilmiş gösterimleri. Afişteki dönem, her faaliyetin destek süresi değildir. Güncel destek ve tamamlanma durumları ilgili proje sayfalarında korunur.'),lang)+'</p>')


def network_page(template,lang):
 parts=[]
 for code,names in DATA['network']:
  display=names
  if lang=='en' and code=='TR':display=['Kırşehir Ahi Evran University','Atatürk University','Nevşehir Hacı Bektaş Veli University','Tokat Gaziosmanpaşa University','Istanbul Technical University (ITU)','Boğaziçi University','Marmara University','Istanbul Okan University']
  parts.append('<article class="network-country"><h3>'+country(code,lang)+'</h3><ul>'+''.join('<li>'+e(n)+'</li>' for n in display)+'</ul></article>')
 legend='<div class="network-legend">'+''.join('<span>'+e(pick(x,lang))+'</span>' for x in [('COST proposal','COST başvurusu'),('Publication collaborations','Yayın iş birlikleri'),('Projects / proposals','Projeler / başvurular'),('Proposal / discussion','Başvuru / görüşme')])+'</div>'
 search='<label for="network-query">'+pick(('Find a country or institution','Ülke veya kurum ara'),lang)+'</label><input id="network-query" type="search" placeholder="'+pick(('Country or institution name','Ülke veya kurum adı'),lang)+'"/><p id="network-count" aria-live="polite"></p>'
 body=network_intro(lang,True)+section('<h2>'+pick(('Country & institution directory','Ülke ve kurum dizini'),lang)+'</h2>'+legend+'<p>'+pick(('Names and the 22/43 totals follow the supplied posters. Additional affiliations on individual profiles do not change this poster snapshot.','Kurum adları ve 22/43 toplamları paylaşılan afişleri izler. Kişisel profillerdeki ek kurumlar, bu afiş kaydının toplamlarını değiştirmez.'),lang)+'</p><div class="directory-tools">'+search+'</div><div class="network-country-grid">'+''.join(parts)+'</div>','network-directory','muted')
 body+=section('<h2>'+pick(('Start a conversation','Birlikte çalışma için iletişim'),lang)+'</h2><p>'+pick(('The form linked in the supplied poster is hosted by Tally. Opening it leaves this website; information is submitted only when you choose to send the form.','Paylaşılan afişteki form Tally üzerinde barındırılıyor. Bağlantı bu siteden ayrılır; bilgiler ancak formu göndermeyi seçtiğinizde iletilir.'),lang)+'</p><div class="buttonrow">'+link(pick(('Research-group interest form','Çalışma grubu ilgi formu'),lang),'https://tally.so/r/Eq51Jr','btn')+link(pick(('Research team','Araştırma ekibi'),lang),'team.html','btn alt')+'</div>')
 body+=research_interest(lang)
 return shell(template,'research-network.html',lang,body)


def team_page(docs,lang):
 s=docs['team.html'];asset(s,lang);cards={};groups={k:[] for k in LABELS}
 for gid in ['collaborators','editorial-collaborators','graduate-researchers','alumni']:
  for card in s.select('#'+gid+' article.person-card'):
   a=card.select_one('a[href^="person-"]');slug=a['href'][7:-5]
   if slug in NEW:continue
   card=copy.deepcopy(card)
   for n in card.select('.person-monogram'):n.decompose()
   role=card.select_one('.micro-label');role.string=role.get_text(' ',strip=True).split(' · ')[0]
   if slug=='georgios-lampropoulos':role.string=pick(('Research collaborator · Postdoctoral researcher','Araştırma ortağı · Doktora sonrası araştırmacı'),lang)
   elif gid=='collaborators' and slug in ONGOING:role.string=pick(('Ongoing academic collaboration','Devam eden akademik iş birliği'),lang)
   elif gid=='editorial-collaborators' and slug in ONGOING:role.string=pick(('Ongoing editorial collaboration','Devam eden editoryal iş birliği'),lang)
   card.select_one('.textlink').insert_before(fragment(affiliations(AFF[slug],lang,gid=='alumni')))
   card['data-person']=slug;cards[slug]=card;groups[gid].append(slug)
 for p in NEW.values():
  card=new_card(p,lang);card['data-person']=p['slug'];cards[p['slug']]=card;groups[p['group']].append(p['slug'])
 leader=copy.deepcopy(s.select_one('#leadership'))
 leader.select_one('.team-leader').append(fragment(affiliations(['kaeu'],lang)))
  # Current academic rank already appears above; avoid repeating 'Doçenti' in the Turkish bio.
 for ptag in leader.select('.team-leader p'):
  if lang=='tr' and 'Fen Bilgisi Eğitimi Doçenti' in ptag.get_text():
   ptag.string=ptag.get_text().replace('Fen Bilgisi Eğitimi Doçenti','Fen Bilgisi Eğitimi alanında akademisyen')
 for el in leader.select('.leader-badge'):el.decompose()
 nav='<nav class="subnav" aria-label="'+pick(('People sections','Ekip bölümleri'),lang)+'">'+''.join(link(pick(label,lang),'#'+gid) for gid,label in LABELS.items())+link(pick(('International network','Uluslararası ağ'),lang),'research-network.html')+'</nav>'
 body='<section class="pagehero"><div class="container"><p class="eyebrow">'+pick(('People / Research connections','Ekip / Araştırma bağlantıları'),lang)+'</p><h1>'+pick(('Research grows through <em>people.</em>','Araştırma <em>insanlarla</em> gelişir.'),lang)+'</h1><p class="lead">'+pick(('Research collaborators, project researchers and advisers, followed by graduate researchers and alumni.','Araştırma ortakları, proje araştırmacıları ve danışmanlar; ardından lisansüstü araştırmacılar ve mezunlar.'),lang)+'</p>'+nav+'</div></section>'+str(leader)
 body+=section('<div class="directory-tools"><label for="people-query">'+pick(('Find a researcher, institution or country','Araştırmacı, kurum veya ülke ara'),lang)+'</label><input id="people-query" type="search"/><button type="button" id="people-reset">'+pick(('Clear search','Aramayı temizle'),lang)+'</button><p id="people-count" aria-live="polite"></p></div><p class="v3-small">'+pick(('Countries refer to the location of the stated institution, not nationality. Institutional marks identify affiliations; they do not imply institutional endorsement or funding.','Ülke bilgileri kişinin vatandaşlığını değil, belirtilen kurumun bulunduğu ülkeyi gösterir. Kurum logoları aidiyeti tanıtır; kurumsal onay veya proje desteği anlamına gelmez.'),lang)+'</p>','directory-search')
 for i,(gid,title) in enumerate(LABELS.items()):
  intro=''
  if gid=='collaborators':intro='<p>'+pick(('Ongoing joint manuscripts, research design and scholarly communication are grouped here; individual profiles distinguish submitted proposals, conceptual work and completed projects. These entries are not an assertion that every institution has signed a project agreement.','Ortak makaleler, araştırma tasarımı ve bilimsel iletişim alanlarında süren akademik bağlantılar burada toplanmıştır. Kişisel profiller başvuruları, kavramsal çalışmaları ve tamamlanan projeleri ayırır; kurumların tamamının resmî proje anlaşması imzaladığı iddia edilmez.'),lang)+'</p>'
  if gid=='project-researchers':intro='<p>'+pick(('Roles follow the supplied team roster. AÜB application-team roles are labelled separately; inclusion is not a statement of a funding award.','Görevler paylaşılan ekip listesine göre sunulur. AÜB başvuru ekibindeki roller ayrıca etiketlenmiştir; listelenmek destek kararı alındığı anlamına gelmez.'),lang)+'</p>'
  if gid=='alumni':
   intro='<p>'+pick(('Completed master’s degrees supervised by Hüseyin Ateş.','Hüseyin Ateş danışmanlığında tamamlanan yüksek lisans tezleri.'),lang)+'</p>'
   ipek_role=pick(('Master’s graduate · 2022','Yüksek lisans mezunu · 2022'),lang)
   ipek_topic=pick(('Distance education and technology adoption','Uzaktan eğitim ve teknoloji benimseme'),lang)
   ipek='<article class="person-card" data-person="ipek-oz-alumna"><div class="person-top"><div><p class="micro-label">'+ipek_role+'</p><h3>İpek Öz</h3></div></div><p class="person-topic">'+ipek_topic+'</p>'+affiliations(['kaeu'],lang,alumni=True)+link(pick(('View master’s alumna profile','Yüksek lisans mezunu profilini incele'),lang),'person-ipek-oz.html')+'</article>'
   groups[gid].append('ipek-oz-alumna');cards['ipek-oz-alumna']=fragment(ipek).article
  block='<h2>'+pick(title,lang)+'</h2>'+intro+'<div class="people-grid">'+''.join(str(cards[slug]) for slug in groups[gid])+'</div>'
  body+=section(block,gid,'muted' if i%2==0 else 'white')
 body+=research_interest(lang)+network_intro(lang)
 sethtml(s.main,body);metadata(s,'team.html',lang)
 return len(cards)-('ipek-oz-alumna' in cards)


def sync_cv():
 import build_professional_docs as d
 en=copy.deepcopy(d.CV)
 en[0]=[(k,t) for k,t in en[0] if 'TÜBİTAK 3501:' not in t]
 en.append([tuple(x) for x in json.loads((ROOT/'content/editorial-update.json').read_text())['cv_proposals_page']])
 en=[[ (k,(t.replace('space-debris problem-solving instruction','space-pollution problem solving') if 'TÜBİTAK 1002-A, 226K999' in t else t)) for k,t in pg ] for pg in en]
 for page in en:
  for i,(k,t) in enumerate(page):
   if t.startswith('Ongoing PhD:'):page[i]=(k,'Ongoing PhD: Abdulkadir Aydın (expected 2028). Ongoing MSc: Tuğçe Ünsal and Nisa Gül (expected 2027); İrem Sude Köksal and Furkan Ensar Ateş (expected 2028).')
   elif 'This public selection excludes manuscripts under review and proposals awaiting decisions.' in t:page[i]=(k,'Unpublished manuscripts are omitted. Submitted, planned and unsuccessful applications are listed separately, not as funding awards.')
   elif 'Public academic CV ·' in t:page[i]=(k,t.replace('12 November 2026','13 November 2026'))
 tr=json.loads((ROOT/'content/cv-tr.json').read_text())
 for page in tr:
  for row in page:
   if 'Tuğçe Ünsal' in row[1] and 'Nisa Gül' in row[1]:row[1]+=' İrem Sude Köksal ve Furkan Ensar Ateş: devam eden yüksek lisans, beklenen bitiş 2028.'
 d.fonts();d.export_document('Huseyin_Ates_Public_Academic_CV',en,'Hüseyin Ateş — Public Academic CV',lang='en')
 d.export_document('Huseyin_Ates_Akademik_Ozgecmis_TR',tr,'Hüseyin Ateş — Akademik Özgeçmiş',lang='tr')



def fix_1002_titles(docs,lang):
 # The TÜBİTAK 226K999 decision letter of 28 August 2026 is authoritative.
 # Display title is corrected after localization to prevent stale translation-map overrides.
 pairs=(
  [('Uzay Enkazı Problem Çözme Öğretiminde İki Pedagojik Destekleme Yaklaşımının Sınıf İçi Pilot Karşılaştırması',OFFICIAL_1002_TITLE_TR),
   ('Uzay Enkazı Problem Çözme Öğretimi','Uzay Kirliliği Problem Çözme Öğretimi'),
   ('Uzay Enkazı Problemlerini Çözme','Uzay Kirliliği Problemlerini Çözme'),
   ('uzay enkazı','uzay kirliliği'),('Uzay enkazı','Uzay kirliliği'),
   ('pedagojik destekleme','pedagojik iskele'),('Pedagojik Destekleme','Pedagojik İskele')]
  if lang=='tr' else
  [('A Classroom Pilot Comparison of Two Pedagogical Scaffolding Approaches in Space-Debris Problem-Solving Instruction',OFFICIAL_1002_TITLE_EN),
   ('Space-Debris Problem-Solving Instruction','Space-Pollution Problem Solving'),
   ('Space-Debris Problem-Solving','Space-Pollution Problem Solving'),
   ('Space-debris problem-solving','Space-pollution problem solving'),
   ('space-debris','space-pollution'),('Space-debris','Space-pollution')])
 for name,doc in docs.items():
  if name=='person-ipek-oz.html':continue
  for node in list(doc.find_all(string=True)):
   if node.parent and node.parent.name in ('script','style'):continue
   old=str(node);new=old
   for a,b in pairs:new=new.replace(a,b)
   if new!=old:node.replace_with(new)
  for node in doc.find_all(['meta']):
   for attr in ['content']:
    if node.get(attr):
     val=node[attr]
     for a,b in pairs:val=val.replace(a,b)
     node[attr]=val
  if name=='project-space-debris.html':
   # Exact project title is shown as the main heading; public-facing study summary stays concise.
   hero=doc.select_one('.pagehero h1')
   if hero:hero.string=OFFICIAL_1002_TITLE_TR if lang=='tr' else OFFICIAL_1002_TITLE_EN
   subtitle=doc.select_one('.pagehero p.lead')
   if subtitle:subtitle.string=pick(('TÜBİTAK 1002-A · Project 226K999 · Classroom pilot in science education',
       'TÜBİTAK 1002-A · Proje 226K999 · Fen eğitiminde sınıf içi pilot çalışma'),lang)
   # Keep conceptual schematic but remove explanatory placeholders or working-note style prose.
   for ptag in list(doc.select('p')):
    val=ptag.get_text(' ',strip=True)
    if 'The labels A and B are explanatory placeholders' in val or 'A ve B açıklayıcı yer tutuculardır' in val:
     ptag.string=pick(('A classroom pilot that compares two pedagogical scaffolding approaches.',
         'İki pedagojik iskele yaklaşımını karşılaştıran sınıf içi pilot çalışma.'),lang)
   metadata(doc,name,lang)

def main():
 target=SITE/'assets/institutions';target.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'assets/institutions').glob('*.png'):shutil.copy2(p,target/p.name)
 for name in ['team-directory.css','team-directory.js']:shutil.copy2(ROOT/'assets'/name,SITE/'assets'/name)
 (SITE/'assets/qr').mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'assets/qr/research-group-interest.png',SITE/'assets/qr/research-group-interest.png')
 # Optimised source-derived vectors share a compact archive; no private input files are copied.
 packed=''.join(p.read_text().strip() for p in sorted((ROOT/'content').glob('network-posters-*.b64')))
 assert hashlib.sha256(packed.encode()).hexdigest()=='66bf789cb01045a9afb1d6d191de0c809863db3d0b25b8760b3ae76434389dcc', 'Poster transfer checksum mismatch'
 posters=json.loads(lzma.decompress(base64.b64decode(packed)))
 (SITE/'assets/network').mkdir(exist_ok=True)
 import cairosvg
 for name,svg in posters.items():
  (SITE/'assets/network'/name).write_text(svg)
  cairosvg.svg2pdf(bytestring=svg.encode(),write_to=str(SITE/'downloads'/name.replace('.svg','.pdf')))
 sync_cv()
 localized={}
 for lang in ['en','tr']:
  folder=SITE/('tr' if lang=='tr' else '')
  docs={p.name:Soup(p.read_text(),'html.parser') for p in folder.glob('*.html')}
  template=copy.deepcopy(docs['person-georgios-lampropoulos.html'])
  for slug,p in NEW.items():docs['person-'+slug+'.html']=new_profile(p,lang,template)
  enhance_profiles(docs,lang);num=team_page(docs,lang)
  docs['research-network.html']=network_page(template,lang)
  # Accurate current supervision also appears in the biography.
  s=docs['about.html']
  for span in s.select('li span'):
   if 'Tuğçe Ünsal' in span.get_text() and 'Nisa Gül' in span.get_text():span.string=pick(('Tuğçe Ünsal and Nisa Gül (expected 2027); İrem Sude Köksal and Furkan Ensar Ateş (expected 2028).','Tuğçe Ünsal ve Nisa Gül (beklenen bitiş: 2027); İrem Sude Köksal ve Furkan Ensar Ateş (beklenen bitiş: 2028).'),lang)
  s=docs['join.html']
  for aside in list(s.main.select('aside.callout')):
   note=aside.get_text(' ',strip=True)
   if any(term in note for term in ('Before sending.', 'Göndermeden önce.', 'No application form is hosted here.', 'Bu sitede başvuru formu yoktur.', 'For research-group enquiries', 'Araştırma grubuna yönelik talepler')):
    block=aside.find_parent('section')
    if block and len(block.select('aside'))==1:block.decompose()
    else:aside.decompose()
  s.main.append(fragment(research_interest(lang)))
  # Conference acceptance is distinct from the TÜBİTAK 2224-A participation-support application.
  conf_title=pick(('ICCAI 2027 — accepted conference contribution','ICCAI 2027 — kabul edilen konferans bildirisi'),lang)
  conf_eyebrow=pick(('Conference contribution and participation-support application','Konferans bildirisi ve katılım desteği başvurusu'),lang)
  paper_title='Calibrated Epistemic-Move Detection and Just-in-Time Scaffolding with Retrieval-Augmented Language Models: An Intelligent Agent for Science Teacher Education'
  conf_body='<section class="pagehero"><div class="container"><p class="eyebrow">'+conf_eyebrow+'</p><h1>'+conf_title+'</h1><p class="lead">'+pick(('The conference organisers confirmed acceptance of paper YS1001 for oral presentation at ICCAI 2027.','ICCAI 2027 düzenleme kurulu, YS1001 kodlu bildirinin sözlü sunum için kabul edildiğini bildirdi.'),lang)+'</p></div></section>'
  conf_body+=section('<div class="profile-summary"><div><h2>'+pick(('Accepted contribution','Kabul edilen bildiri'),lang)+'</h2><p lang="en"><em>'+paper_title+'</em></p><p>'+pick(('Paper ID: YS1001. The 13th International Conference on Computing and Artificial Intelligence (ICCAI 2027) is scheduled for 23–26 April 2027 in Seoul, South Korea. Acceptance for inclusion in the proceedings is stated in the organiser’s letter; this does not mean that the paper has already been published.','Bildiri kodu: YS1001. 13. International Conference on Computing and Artificial Intelligence (ICCAI 2027), 23–26 Nisan 2027 tarihlerinde Güney Kore’nin Seul kentinde düzenlenecek. Düzenleme kurulunun kabul yazısında bildiri kitabında yayımlanması da öngörülüyor; bildiri henüz yayımlanmış bir çalışma olarak listelenmiyor.'),lang)+'</p>'+link(pick(('Conference website','Konferansın resmî sitesi'),lang),'https://www.iccai.net/')+'</div><aside class="project-side"><p class="micro-label">'+pick(('Conference status','Konferans durumu'),lang)+'</p><p>'+pick(('Accepted for oral presentation · scheduled for 2027','Sözlü sunum için kabul edildi · 2027 için planlandı'),lang)+'</p></aside></div>')
  conf_body+=section('<h2>'+pick(('TÜBİTAK 2224-A participation-support application','TÜBİTAK 2224-A katılım desteği başvurusu'),lang)+'</h2><p>'+pick(('An application for international scientific-event participation support was submitted for this conference under the TÜBİTAK 2224-A programme, as reported by the applicant. An award decision has not been confirmed; the activity is not presented as funded.','Bu konferansa katılım için TÜBİTAK 2224-A Yurt Dışı Bilimsel Etkinliklere Katılımı Destekleme Programı kapsamında başvuru yapıldı. Destek sonucu henüz doğrulanmadı; başvuru, kazanılmış burs veya fon olarak gösterilmiyor.'),lang)+'</p>'+link(pick(('TÜBİTAK 2224-A programme','TÜBİTAK 2224-A programı'),lang),'https://tubitak.gov.tr/tr/destekler/bilimsel-etkinlik/etkinliklere-katilma-destekleri/2224-yurt-disi-bilimsel-etkinliklere-katilimi-destekleme-programi'),'conference-funding','muted')
  docs['conference-iccai-2027.html']=shell(template,'conference-iccai-2027.html',lang,conf_body)
  activity_link=link(pick(('ICCAI 2027 conference contribution and 2224-A application','ICCAI 2027 bildirisi ve 2224-A başvurusu'),lang),'conference-iccai-2027.html')
  docs['about.html'].main.append(fragment(section('<h2>'+pick(('Academic events and conference contributions','Bilimsel etkinlikler ve konferans bildirileri'),lang)+'</h2><p>'+pick(('The conference contribution and participation-support application are recorded separately from research grants.','Kabul edilen konferans bildirileri ve katılım desteği başvuruları, araştırma projeleriyle karıştırılmadan sunulmaktadır.'),lang)+'</p>'+activity_link,'academic-events','muted')))
  docs['proposals.html'].main.append(fragment(section('<h2>'+pick(('International conference participation support','Uluslararası bilimsel etkinlik katılım desteği'),lang)+'</h2><p>'+pick(('TÜBİTAK 2224-A is an event-participation support application and is not included in the seven research-proposal records above.','TÜBİTAK 2224-A, bilimsel etkinliğe katılım desteği başvurusudur; yukarıda yer alan yedi araştırma önerisi kaydına dâhil değildir.'),lang)+'</p>'+activity_link,'conference-support')))
  # Proposed team membership stays attached to the submitted AÜB application.
  s=docs['proposal-turkiye-uae-stem.html'];s.main.append(fragment(section('<h2>'+pick(('Proposed research team','Önerilen araştırma ekibi'),lang)+'</h2><p>'+pick(('Team listed in the supplied application: Hüseyin Ateş (coordinator), Kibar Gül (NEVÜ), Naciye Somuncu Demir (TOGÜ), Ahmet Sami Konca (UAEU), and independent researcher Yeşim Taktat Ateş. The application status is unchanged.','Paylaşılan başvurudaki ekip: Hüseyin Ateş (yürütücü), Kibar Gül (NEVÜ), Naciye Somuncu Demir (TOGÜ), Ahmet Sami Konca (UAEU) ve bağımsız araştırmacı Yeşim Taktat Ateş. Başvurunun değerlendirme durumu değişmemiştir.'),lang)+'</p>'+link(pick(('People and affiliations','Ekip ve kurumlar'),lang),'team.html#project-researchers'),'proposal-team')))
  # Scientific funding decision for 1002-A project, without asserting a signed contract.
  s=docs['project-space-debris.html']
  s.main.append(fragment(section('<h2>'+pick(('Funding decision evidence','Destek kararı kaydı'),lang)+'</h2><p>'+pick(('The TÜBİTAK SOBAG decision letter dated 28 August 2026 confirms a positive scientific funding decision for project 226K999. The letter also describes separate financial and contracting procedures, and does not by itself establish that the project contract has been signed.','28 Ağustos 2026 tarihli TÜBİTAK SOBAG karar yazısı, 226K999 numaralı proje için olumlu bilimsel destek kararını doğruluyor. Yazı mali değerlendirme ve sözleşme işlemlerini ayrıca tanımlıyor; tek başına proje sözleşmesinin imzalandığını göstermez.'),lang)+'</p>','funding-decision-note','muted')))
  s=docs['project-vr-stem-vietnam.html'];s.main.append(fragment(section('<h2>'+pick(('Research connection in Vietnam','Vietnam’daki araştırma bağlantısı'),lang)+'</h2>'+link('Bui Van Hong · HCM-UTE','person-bui-van-hong.html')+'<p>'+pick(('This project remains completed; the collaboration profile does not reopen the project.','Proje tamamlanmış durumdadır; araştırmacı profili eklenmesi projenin yeniden başladığı anlamına gelmez.'),lang)+'</p>')))
  docs['research.html'].main.append(fragment(section('<h2>'+pick(('International research network','Uluslararası araştırma ağı'),lang)+'</h2>'+link(pick(('22 countries · 43 institutions','22 ülke · 43 kurum'),lang),'research-network.html'))))
  fix_1002_titles(docs,lang)
  if lang=='tr':
   from turkish_editorial import polish
   polish(docs)
  build_index(docs,lang)
  for name,s in docs.items():(folder/name).write_text(str(s))
  localized[lang]=docs
 manifest=json.loads((SITE/'deployment.json').read_text());manifest.pop('files',None)
 manifest.update(version='4.6',language_pairs=len(localized['en']),page_count=len(localized['en'])*2,pages=sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html')),downloads=sorted(p.name for p in (SITE/'downloads').iterdir() if p.is_file()),updated='2026-11-13')
 (SITE/'deployment.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 urls=[]
 for name in sorted(localized['en']):
  if name in ['404.html','search.html']:continue
  for lang in ['en','tr']:
   alts=''.join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{BASE}{prefix}{name}"/>' for code,prefix in [('en',''),('tr','tr/'),('x-default','')])
   urls.append(f'<url><loc>{BASE}'+('tr/' if lang=='tr' else '')+name+'</loc>'+alts+'<lastmod>2026-11-13</lastmod></url>')
 (SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'+''.join(urls)+'</urlset>')
 (SITE/'quality-report.json').write_text(json.dumps({'release':'4.6','language_pairs':len(localized['en']),'people_profiles':num,'countries_in_source_posters':22,'institutions_in_source_posters':43,'photos_added':0,'limits':'Countries identify institutional location; logos are not endorsements. Proposal and completed-project statuses are preserved.'},indent=2))
 print('TEAM DIRECTORY BUILT',num,'profiles;',manifest['page_count'],'pages')

if __name__=='__main__':main()
