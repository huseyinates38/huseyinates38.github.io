#!/usr/bin/env python3
"""Clean public navigation and build static EN/TR pairs. No external translation service."""
from __future__ import annotations
import json,re,copy,os,unicodedata
from pathlib import Path
from html import escape
from urllib.parse import urlsplit,urlunsplit
from bs4 import BeautifulSoup as Soup, NavigableString
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'; BASE='https://huseyinates38.github.io/'
DATE='2026-11-13'
def frag(s): return Soup(s,'html.parser')
def norm(s):return re.sub(r'\s+',' ',str(s)).strip()
def section(title,body,tone='white',id_=''):
 return '<section class="section '+tone+'"'+(' id="'+id_+'"' if id_ else '')+'><div class="container"><h2>'+title+'</h2>'+body+'</div></section>'
def links(items):return '<div class="v3-links">'+''.join('<a href="'+b+'">'+a+' <span aria-hidden="true">↗</span></a>' for a,b in items)+'</div>'
def set_html(tag,html):tag.clear();tag.append(frag(html))
def new_home():
 return '''<section class="home-hero"><div class="container home-grid"><div><p class="eyebrow">Hüseyin Ateş · Associate Professor of Science Education</p><h1>Learning with AI.<br/><em>Thinking for ourselves.</em></h1><p class="lead">How can technology support scientific reasoning without taking over the learner’s judgement? My research connects human-centered AI, feedback design and self-regulated learning.</p><p class="affiliation">Kırşehir Ahi Evran University · Türkiye</p><div class="buttonrow"><a class="btn" href="research.html">Explore research <span aria-hidden="true">↗</span></a><a class="btn alt" href="about.html">About &amp; CV <span aria-hidden="true">↗</span></a></div></div><aside class="hero-panel"><p class="eyebrow">Research programme</p><h2>Questions before<br/><em>technologies.</em></h2><div class="process-row"><span>01</span><div><strong>Human-centered AI</strong><p>Feedback, evaluative judgement and learner agency.</p></div></div><div class="process-row"><span>02</span><div><strong>Scientific reasoning</strong><p>Evidence, argumentation and independent transfer.</p></div></div><div class="process-row"><span>03</span><div><strong>Self-regulated learning</strong><p>Planning, monitoring and reflection in science education.</p></div></div></aside></div></section>'''+section('Research, people &amp; <em>practice.</em>', '''<div class="cards"><article class="card"><p class="eyebrow">Research</p><h3>Projects &amp; proposals</h3><p>Explore supported projects, ongoing collaborations and proposals with their current status.</p><a class="textlink" href="projects.html">Explore projects ↗</a></article><article class="card"><p class="eyebrow">People</p><h3>Research connections</h3><p>Meet research collaborators, editorial connections and graduate researchers.</p><a class="textlink" href="team.html">Meet the people ↗</a></article><article class="card"><p class="eyebrow">For teachers</p><h3>Resources to think with</h3><p>English and Turkish teaching guides, working sheets and an interactive feedback example.</p><a class="textlink" href="resources.html">Browse resources ↗</a></article></div>''','muted')+section('Selected <em>research.</em>','''<div class="cards"><article class="card"><p class="eyebrow">2026 · Research brief</p><h3>GenAI feedback design</h3><p>Direct, reflective and hybrid feedback in university science learning.</p><a class="textlink" href="study-genai-feedback.html">Read the brief ↗</a></article><article class="card"><p class="eyebrow">2024 · Research brief</p><h3>Self-regulated flipped learning</h3><p>Self-regulation support and science learning performance.</p><a class="textlink" href="study-self-regulated-flipped-learning.html">Read the brief ↗</a></article><article class="card"><p class="eyebrow">2025 · Research brief</p><h3>AR &amp; intelligent tutoring</h3><p>A combined approach to science instruction and learner support.</p><a class="textlink" href="study-ar-intelligent-tutoring.html">Read the brief ↗</a></article></div>'''+links([('All publications','publications.html')]))+section('Start with a <em>shared question.</em>','''<p class="lead">Research collaboration, postgraduate supervision and conversations with schools and teachers.</p>'''+links([('Working together','join.html'),('Contact','contact.html'),('Editorial initiatives','editorial.html')]),'muted')

def clean(s,name):
 # Keep substantive records and stable URLs; remove duplicated routes and internal release narratives.
 for n in s.select('.strip'):n.decompose()
 if name=='index.html':set_html(s.main,new_home())
 if name in ['research.html','about.html']:
  for n in s.select('#work-in-progress'):n.decompose()
 if name=='research.html':
  n=s.select_one('main > .subsection')
  if n:n.decompose()
  hero=s.select_one('.pagehero .container')
  hero.append(frag(links([('Projects & proposals','projects.html'),('Editorial initiatives','editorial.html'),('Methods & access','open-research.html')])) )
 if name=='projects.html':
  n=s.select_one('#proposal-pipeline .container')
  if n:set_html(n,'<h2>Submitted &amp; <em>planned applications.</em></h2><p class="lead">Six submitted applications and one research concept in development appear in the separate proposal register.</p>'+links([('Full proposal register','proposals.html')]))
 if name=='team.html':
  for n in s.select('.team-intro'):n.decompose()
  n=s.select_one('.pagehero p.lead')
  if n:n.string='Research collaborators and editorial connections, followed by graduate researchers and alumni.'
 if name=='about.html':
  for n in s.select('button.buttonprint'):n.decompose()
 if name.startswith('study-'):
  for n in list(s.main.select('aside [lang=tr]')):
   n.decompose()
  for n in list(s.main.select('aside small, aside hr')):
   if n.name=='hr' or n.get_text(strip=True)=='Read in Turkish':n.decompose()
  for d in list(s.main.select('details')):
   if d.find(attrs={'lang':'tr'}) or 'Read in Turkish' in d.get_text():d.decompose()
  for p in list(s.main.select('.citation')):
   if p.get('id')!='citation-text':p.decompose()
  # Keep one source note, one full citation and the original source links.
  for p in list(s.main.find_all('p')):
   if p.get_text(strip=True).startswith('This is an editorial research brief,'):p.decompose()
 if name=='site-notes.html':
  set_html(s.main,'''<section class="pagehero"><div class="container"><p class="eyebrow">About this website</p><h1>Sources, privacy &amp;<br/><em>editorial practice.</em></h1><p class="lead">How research records, teaching resources and language versions are presented.</p></div></section>'''+section('Research records','<p>Academic profile and project records are supplied by Hüseyin Ateş. Published research links to the original publication. Funded projects, submitted applications and research concepts in development remain clearly separated.</p><p>Research briefs are editorial summaries, not complete abstracts or substitutes for the original methods and results. Article titles and bibliographic citations retain their original language in both site versions.</p>')+section('Teaching resources','<p>The teaching guides, worksheets and fictional examples were prepared for this website with AI-assisted drafting. They are teaching prototypes, not published study instruments or validated scales. Review their scientific accuracy and suitability before use.</p>'+links([('Use & attribution','resource-use.html'),('Teaching resources','resources.html')]),'muted')+section('Privacy &amp; external services','<p>This website has no analytics script, tracking cookie, application form, live AI service or student-response upload. Search and interactive examples run locally in your browser. No search queries or responses are stored by the site.</p><p>The hosting provider may process technical access information. External links and email are subject to the terms of their respective services. Private correspondence and draft application documents are not published.</p>')+section('Languages, access &amp; corrections','<p>Choose English or Türkçe in the header to open the same page in the other language. Each language has its own address, and internal navigation stays in the selected language. Existing English addresses remain available.</p><p>Resource downloads are labelled by language. The public academic CV is available in both English and Turkish in PDF and editable DOCX formats.</p>'+links([('Accessibility','accessibility.html'),('Contact for corrections','contact.html')]),'muted'))
 # Remove transient release dates/status rhetoric where it duplicates a visible status badge.
 for p in list(s.main.select('p')):
  t=p.get_text(' ',strip=True)
  if t in ['Website content update: 12 November 2026. Resource prototypes: version 1.1.']:p.decompose()
 # Header: visible language switch is outside the collapsible navigation, also on mobile.
 active='index.html'
 if name.startswith(('project-','proposal-')) or name in ['projects.html','proposals.html']:active='projects.html'
 elif name.startswith('person-') or name=='team.html':active='team.html'
 elif name.startswith('study-') or name=='publications.html':active='publications.html'
 elif name.startswith('resource-') or name in ['resources.html','practice.html','feedback-explorer.html']:active='resources.html'
 elif name in ['research.html','research-timeline.html','open-research.html','editorial.html']:active='research.html'
 elif name not in ['index.html','404.html','search.html']:active='about.html'
 nav=[('Home','index.html'),('Research','research.html'),('Projects','projects.html'),('People','team.html'),('Publications','publications.html'),('Resources','resources.html'),('About','about.html')]
 header='<div class="container headrow"><a aria-label="Hüseyin Ateş home" class="brand" href="index.html"><span aria-hidden="true" class="brand-symbol">HA<span>.</span></span><span><strong>Hüseyin Ateş</strong><small>SCIENCE EDUCATION · HUMAN-CENTERED AI</small></span></a><div class="header-tools"><nav class="site-language" aria-label="Language"><a href="'+name+'" lang="en" hreflang="en" data-site-lang="en">EN</a><a href="tr/'+name+'" lang="tr" hreflang="tr" data-site-lang="tr">TR</a></nav><a class="header-search" href="search.html" aria-label="Search this website"><svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m15 15 6 6" stroke="currentColor" stroke-width="1.8"/></svg></a><button aria-controls="main-navigation" aria-expanded="false" class="menu-button" type="button">Menu <span aria-hidden="true">☰</span></button></div><nav aria-label="Main navigation" class="nav" id="main-navigation">'+''.join('<a href="'+h+'"'+(' aria-current="page"' if h==active else '')+'>'+label+'</a>' for label,h in nav)+'</nav></div>'
 set_html(s.header,header)
 footer='<div class="container"><div class="footer-inner"><div><strong>Hüseyin Ateş</strong><p>Human-centered AI, scientific reasoning<br/>and self-regulated science learning.</p></div><nav class="footer-links" aria-label="Further information">'+''.join('<a href="'+h+'">'+label+'</a>' for label,h in [('Contact','contact.html'),('Working together','join.html'),('Academic CV · English PDF','downloads/Huseyin_Ates_Public_Academic_CV.pdf'),('ORCID','https://orcid.org/0000-0003-0031-8994')])+'</nav></div><div class="footer-bottom"><span>© 2026 Hüseyin Ateş</span><nav class="footer-utility" aria-label="Website information"><a href="site-notes.html">Privacy & site notes</a><a href="accessibility.html">Accessibility</a><a href="resource-use.html">Resource use</a></nav></div></div>'
 set_html(s.footer,footer)
 # Replace overlapping legacy interaction handlers with one localized controller.
 for n in s.select('script[src]'):n.decompose()
 s.head.append(s.new_tag('script',attrs={'src':'assets/bilingual.js?v=4.0','defer':''}))
 s.head.append(s.new_tag('link',attrs={'rel':'stylesheet','href':'assets/bilingual.css?v=4.0'}))
 # Preserve incoming resource-note anchors after simplifying notes.
 if name=='site-notes.html':
  for sec in s.main.find_all('section'):
   h=sec.find('h2')
   if h and h.get_text()=='Teaching resources':sec['id']='resources'
 # Remove the maintenance-release paragraph from the public accessibility page.
 if name=='accessibility.html':
  for p in list(s.main.find_all('p')):
   if p.get_text().startswith('Website release 3.2 '):p.decompose()
 return s

def choose_language(s,lang):
 for block in list(s.select('[data-lang]')):
  if block.get('data-lang')!=lang:block.decompose()
  else:
   del block['data-lang'];block.attrs.pop('hidden',None);block['lang']=lang
 for ctrl in list(s.select('[data-language-picker]')):
  wrapper=ctrl.parent
  if wrapper.get('class') and 'language-control' in wrapper.get('class',[]):
   for p in list(wrapper.select('[data-print]')):wrapper.insert_after(p.extract())
   wrapper.decompose()
  else:wrapper.decompose()
 for n in s.select('#language-status'):n.decompose()
 if lang=='en':
  for n in s.select('select[data-feedback-picker] option'):
   n.string=n.get_text().split(' / ')[0]
  for n in s.select('label[for="feedback-mode"]'):n.string='Feedback approach'
 return s

# Units are complete inline text blocks. Bibliographic records, identifiers and proper names stay original.
UNIT_TAGS={'h1','h2','h3','h4','h5','p','dt','dd','td','th','figcaption','caption','label','option','button','summary','small','a','span','li','strong','div','aside'}
BLOCK={'div','p','h1','h2','h3','h4','h5','section','article','ul','ol','li','dl','dt','dd','table','td','th','select','label','button','nav','aside','blockquote','details'}
PEOPLE=['Hüseyin Ateş','Juan Garzón','Georgios Lampropoulos','Naomi Winstone','Ahmet Sami Konca','Juan David Murillo Egurrola','Marc Romero Carbonell','Abdulkadir Aydın','Tuğçe Ünsal','Nisa Gül','Kübra Solmaz','Rabia Ateş','Fatma Gazioğlu','İpek Öz']
def skip_node(n):
 for p in [n,*n.parents]:
  if not getattr(p,'name',None):continue
  if p.name in ['script','style','pre','code','svg']:return True
  if p.get('lang')=='tr' and p.name!='html':return True
  classes=p.get('class',[])
  if any(c in classes for c in ['publication','citation','site-language']):return True
  if p.get('id')=='citation-text':return True
 return False
def units(s):
 seen=set()
 for n in s.find_all(UNIT_TAGS):
  if skip_node(n) or any(id(a) in seen for a in n.parents):continue
  if any(x.name in BLOCK for x in n.find_all(True)):continue
  txt=norm(n.get_text(' ',strip=True));key=norm(n.decode_contents())
  if not txt or not re.search('[A-Za-zÀ-ž]',txt):continue
  if txt in PEOPLE or txt in ['HA.','JG','GL','NW','AK','JM','MR','AA','TÜ','NG','KS','RA','FG','İÖ','ORCID','Web of Science','Scopus','Google Scholar','English','Türkçe','EN','TR','GenAI','STEM','BAP','1002-A','TÜBİTAK','TÜBİTAK 3501','Sustainable Environment','International Journal of Educational Technology in Higher Education'] or re.match(r'^(https?://|huseyin\.ates@|\+90)',txt):continue
  if re.fullmatch(r'[0-9\s\-–—.,/()×]+',txt):continue
  seen.add(id(n));yield n,key

def prepared():
 return {p.name:clean(Soup(p.read_text(encoding='utf-8'),'html.parser'),p.name) for p in sorted(SITE.glob('*.html'))}

def extract():
 docs=prepared();entries={};occ={}
 for name,s in docs.items():
  t=choose_language(copy.deepcopy(s),'tr')
  for n,key in units(t):
   entries.setdefault(key,len(entries)+1);occ.setdefault(key,[]).append(name)
 # Page descriptions and titles are human-readable metadata.
 for name,s in docs.items():
  for key in [s.title.string]+[x.get('content','') for x in s.select('meta[name="description"]')]:
   if key:entries.setdefault(norm(key),len(entries)+1);occ.setdefault(norm(key),[]).append(name+' [metadata]')
 out=[{'id':i,'en':k,'pages':list(dict.fromkeys(occ[k]))} for k,i in entries.items()]
 (ROOT/'content/translation-units.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 (ROOT/'translation-review.txt').write_text('\n'.join(str(x['id'])+' | '+x['en'] for x in out))
 print('TRANSLATION UNITS',len(out),'WORDS',sum(len(x['en'].split()) for x in out))


ATTR_TR={
 'Hüseyin Ateş home':'Hüseyin Ateş anasayfa','Main navigation':'Ana menü','Language':'Dil seçimi',
 'Search this website':'Sitede ara','Further information':'Diğer bilgiler','Website information':'Site bilgileri',
 'Research sections':'Araştırma bölümleri','People sections':'Ekip bölümleri','Search results':'Arama sonuçları',
 'Search publications':'Yayınlarda ara','Search titles, authors or journals':'Başlık, yazar veya dergi ara',
 'Filter by publication year':'Yayın yılına göre filtrele','Research, publications, projects, resources…':'Araştırma, yayınlar, projeler, kaynaklar…'
}
def localized_attrs(s,lang):
 if lang!='tr':return
 for n in s.select('[aria-label],[placeholder],[title]'):
  for attr in ['aria-label','placeholder','title']:
   val=n.get(attr)
   if not val:continue
   if val in ATTR_TR:n[attr]=ATTR_TR[val]
   elif n.name=='a' and not n.get('data-site-lang'):
    n.attrs.pop(attr,None) # the translated visible link text supplies its accessible name
 # Existing Turkish teaching blocks already contain reviewed Turkish content.
 for n in s.select('[lang=tr] a'):
  for t in list(n.find_all(string=True)):
   if 'Download Markdown' in str(t):t.replace_with(str(t).replace('Download Markdown','Markdown indir'))
 for n in s.select('.publication'):
  n['lang']='en';n['data-original-language']='en'
 for n in s.select('#citation-text,.citation,pre,code'):
  n['lang']='en'

def translate(s,mapping):
 missing=[]
 for n,key in list(units(s)):
  if key not in mapping:
   missing.append(key);continue
  set_html(n,mapping[key])
 if missing:raise ValueError('Untranslated content: '+json.dumps(missing,ensure_ascii=False))
 return s

def locale_links(s,name,lang,names):
 for n in s.select('[href],[src],[poster]'):
  for attr in ['href','src','poster']:
   value=n.get(attr)
   if not value:continue
   u=urlsplit(value)
   if u.scheme or u.netloc:continue
   path=u.path
   if not path:continue
   # In a static /tr directory HTML peers are relative; shared files are one level up.
   if lang=='tr' and (path.startswith('assets/') or path.startswith('downloads/')):
    n[attr]=urlunsplit(('', '', '../'+path,u.query,u.fragment))
 # Correct language counterparts after shared-file rewriting. Switching retains the page, not just home.
 for a in s.select('[data-site-lang]'):
  target=a['data-site-lang'];a['href']=('../' if lang=='tr' and target=='en' else 'tr/' if lang=='en' and target=='tr' else '')+name
  a['aria-label']='English' if target=='en' else 'Türkçe';a['title']=a['aria-label']
  if target==lang:a['aria-current']='true'
  else:a.attrs.pop('aria-current',None)
 # Old inline resource language fragments remain usable as deep links.
 s.html['lang']=lang;s.html['data-site-language']=lang
 if name=='404.html' and lang=='tr':
  for base_tag in s.select('base[href]'):base_tag.decompose()
 for n in s.select('script#site-search-data'):
  n.string='[]' # replaced with the final, cleaned and translated index below

def public_cv_links(s,name,lang):
 """Add both CV language choices. Original publication titles remain unchanged."""
 if name!='about.html':
  return
 panel=s.select_one('main .v3-box .v3-links')
 if not panel:
  raise RuntimeError('Academic CV links panel missing on about page')
 targets=[('PDF','.pdf'),('DOCX','.docx')]
 for display,ext in reversed(targets):
  file='Huseyin_Ates_Akademik_Ozgecmis_TR'+ext
  href=('../' if lang=='tr' else '')+'downloads/'+file
  label=('Akademik özgeçmiş · Türkçe PDF' if display=='PDF' else 'Düzenlenebilir özgeçmiş · Türkçe DOCX')
  if lang=='en':label=('Turkish academic CV · PDF' if display=='PDF' else 'Turkish academic CV · DOCX')
  a=s.new_tag('a',attrs={'href':href,'download':file,'hreflang':'tr','lang':'tr','aria-label':label})
  a.string=label
  panel.insert(0,a)
 # The footer retains an English-CV link; the Turkish content also has a local CV entry.
 if lang=='tr':
  footer=s.select_one('.footer-links')
  if footer:
   f=s.new_tag('a',attrs={'href':'../downloads/Huseyin_Ates_Akademik_Ozgecmis_TR.pdf','hreflang':'tr'})
   f.string='Akademik özgeçmiş · Türkçe PDF'
   footer.insert(0,f)

def metadata(s,name,lang):
 title=s.main.find('h1').get_text(' ',strip=True)
 if name=='index.html':title='Hüseyin Ateş · Research & Science Education' if lang=='en' else 'Hüseyin Ateş · Araştırma ve Fen Eğitimi'
 else:title+=' | Hüseyin Ateş'
 s.title.string=title
 first=s.main.select_one('.lead') or s.main.find('p')
 desc=first.get_text(' ',strip=True) if first else title
 path=('tr/' if lang=='tr' else '')+name;url=BASE+path
 for selector,value in [('meta[name="description"]',desc),('meta[property="og:title"]',title),('meta[property="og:description"]',desc),('meta[property="og:url"]',url),('meta[property="og:locale"]','tr_TR' if lang=='tr' else 'en_US'),('meta[name="twitter:title"]',title),('meta[name="twitter:description"]',desc)]:
  n=s.select_one(selector)
  if not n:
   prop='property' if 'property=' in selector else 'name';key=selector.split('="')[1].split('"')[0]
   n=s.new_tag('meta',attrs={prop:key});s.head.append(n)
  n['content']=value
 for n in s.select('link[rel="alternate"][hreflang],script[data-locale-schema]'):n.decompose()
 c=s.select_one('link[rel="canonical"]')
 if not c:c=s.new_tag('link',attrs={'rel':'canonical'});s.head.append(c)
 c['href']=url
 for code,dest in [('en',BASE+name),('tr',BASE+'tr/'+name),('x-default',BASE+name)]:
  s.head.append(s.new_tag('link',attrs={'rel':'alternate','hreflang':code,'href':dest}))
 schema={'@context':'https://schema.org','@type':'WebPage','name':title,'description':desc,'inLanguage':lang,'url':url,'isPartOf':{'@type':'WebSite','name':'Hüseyin Ateş','url':BASE}}
 js=s.new_tag('script',attrs={'type':'application/ld+json','data-locale-schema':'true'});js.string=json.dumps(schema,ensure_ascii=False).replace('<','\\u003c');s.head.append(js)

CATEGORIES={
 'en':{'research':'Research & projects','people':'People','publications':'Publications & briefs','resources':'Resources & methods','about':'Profile & site information'},
 'tr':{'research':'Araştırma ve projeler','people':'Ekip','publications':'Yayınlar ve özetler','resources':'Kaynaklar ve yöntemler','about':'Profil ve site bilgileri'}
}
def category(name):
 if name=='team.html' or name.startswith('person-'):return 'people'
 if name=='publications.html' or name.startswith('study-'):return 'publications'
 if name.startswith(('project','proposal','research')) or name=='editorial.html':return 'research'
 if name in ['resources.html','practice.html','feedback-explorer.html','open-research.html'] or name.startswith('resource-'):return 'resources'
 return 'about'
def normalized(text):
 return ''.join(c for c in unicodedata.normalize('NFD',text) if unicodedata.category(c)!='Mn').replace('ı','i').lower()
def build_index(docs,lang):
 index=[]
 for name,s in docs.items():
  if name in ['404.html','search.html','person-tugce-unsal.html']:continue
  m=copy.deepcopy(s.main)
  for n in m.select('script,style,button,select'):n.decompose()
  title=m.find('h1').get_text(' ',strip=True)
  intro=m.select_one('.lead') or m.find('p')
  summary=intro.get_text(' ',strip=True) if intro else ''
  cat=category(name)
  # The search page should not display a student's name as a preset suggestion
  # or directory item. The academic team page and supervision records are unchanged.
  summary=summary.replace('Tuğçe Ünsal','')
  searchable_text=m.get_text(' ',strip=True).replace('Tuğçe Ünsal','')
  index.append({'title':title,'url':name,'summary':summary,'category':cat,'label':CATEGORIES[lang][cat],'key':normalized(title+' '+searchable_text)})
 # Keep all downloadable files discoverable, with explicit document languages.
 for p in sorted((SITE/'downloads').iterdir()):
  if not p.is_file():continue
  name=p.name
  term='Türkçe' if '-tr.' in name or '_TR.' in name else 'English' if '-en.' in name or name.startswith('Huseyin_Ates_') else 'EN / TR'
  if lang=='tr':term=term.replace('English','İngilizce')
  prefix='İndirilebilir dosya' if lang=='tr' else 'Downloadable file'
  index.append({'title':name,'url':('../' if lang=='tr' else '')+'downloads/'+name,'summary':term+' · '+p.suffix[1:].upper(),'category':'resources','label':prefix,'key':normalized(name+' '+term+' '+('özgeçmiş cv' if 'CV' in name else 'kaynak resource öğretim teaching'))})
 s=docs['search.html'];data=s.select_one('#site-search-data')
 if not data:data=s.new_tag('script',attrs={'type':'application/json','id':'site-search-data'});s.main.append(data)
 data.string=json.dumps(index,ensure_ascii=False).replace('<','\\u003c')
 directory=s.select_one('#search-directory')
 if directory:
  header='Tüm sayfalar' if lang=='tr' else 'Browse all pages'
  explanation='Bu dizin JavaScript olmadan da çalışır.' if lang=='tr' else 'This directory also works without JavaScript.'
  set_html(directory,'<h2>'+header+'</h2><p>'+explanation+'</p><ul class="page-directory">'+''.join('<li><a href="'+escape(x['url'],quote=True)+'">'+escape(x['title'])+'</a></li>' for x in index if x['url'].endswith('.html'))+'</ul>')


def main():
 from build_cv_tr import main as build_tr_cv
 build_tr_cv()
 mapping=json.loads((ROOT/'content/translations-tr.json').read_text(encoding='utf-8'))
 docs=prepared();localized={'en':{},'tr':{}}
 for name,source in docs.items():
  for lang in ['en','tr']:
   s=choose_language(copy.deepcopy(source),lang)
   if lang=='tr':translate(s,mapping)
   localized_attrs(s,lang);locale_links(s,name,lang,set(docs));public_cv_links(s,name,lang);metadata(s,name,lang)
   # Public PDFs retain their source language, clearly labelled rather than falsely translated.
   for a in s.select('a[href*="Huseyin_Ates_Public_Academic_CV"]'):
    a['hreflang']='en'
    if lang=='tr':a['title']='İngilizce akademik özgeçmiş'
   localized[lang][name]=s
 for lang in ['en','tr']:
  build_index(localized[lang],lang)
  out=SITE/('tr' if lang=='tr' else '');out.mkdir(exist_ok=True)
  for name,s in localized[lang].items():(out/name).write_text(str(s),encoding='utf-8')
 for name in ['bilingual.css','bilingual.js']:(SITE/'assets'/name).write_bytes((ROOT/'assets'/name).read_bytes())
 manifest=json.loads((SITE/'deployment.json').read_text());manifest.pop('files',None)
 manifest.update(version='4.2',languages=['en','tr'],language_pairs=len(docs),page_count=len(docs)*2,pages=sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html')))
 (SITE/'deployment.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 urls=[]
 for name in sorted(docs):
  if name in ['404.html','search.html']:continue
  for lang in ['en','tr']:
   url=BASE+('tr/' if lang=='tr' else '')+name
   alternate=''.join('<xhtml:link rel="alternate" hreflang="'+code+'" href="'+href+'"/>' for code,href in [('en',BASE+name),('tr',BASE+'tr/'+name),('x-default',BASE+name)])
   urls.append('<url><loc>'+url+'</loc>'+alternate+'<lastmod>'+DATE+'</lastmod></url>')
 (SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'+''.join(urls)+'</urlset>')
 (SITE/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n')
 (SITE/'quality-report.json').write_text(json.dumps({'release':'4.2','languages':['en','tr'],'language_pairs':len(docs),'translation_units':len(mapping),'portrait_files_added':0,'content_statuses':'Existing supported / submitted / planned / non-funded distinctions preserved.','downloads':'Preserved; original English and new Turkish public CV available in PDF and DOCX.','limits':'Automated testing is not independent WCAG certification or research fact verification.'},indent=2))
 print(f'Built {len(docs)} EN/TR page pairs. Existing publication citations and downloads retained; no portrait included.')

if __name__=='__main__':
 import sys
 if '--extract' in sys.argv:extract()
 else:main()
