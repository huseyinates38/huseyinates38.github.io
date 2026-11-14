#!/usr/bin/env python3
"""Publish a bilingual, opt-in, on-device academic assistant on static Pages.

Runs after all existing editorial passes. No API key, remote prompt endpoint,
analytics or chat persistence is used. The knowledge corpus comes exclusively
from the final public HTML, never from private attachments or email.
"""
from __future__ import annotations
import copy, hashlib, json, re, shutil
from pathlib import Path
from html import escape
from bs4 import BeautifulSoup as Soup

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
BASE='https://huseyinates38.github.io/'
ASSETS=('academic-assistant.js','academic-assistant-worker.js','academic-assistant.css')
EXCLUDE={'assistant.html','search.html','404.html','accessibility.html','site-notes.html'}

def pair(lang,en,tr): return tr if lang=='tr' else en

def text(node): return node.get_text(' ',strip=True) if node else ''

def normalized(value):
 import unicodedata
 return ''.join(c for c in unicodedata.normalize('NFD',value) if unicodedata.category(c)!='Mn').replace('ı','i').lower()

def corpus(docs,lang):
 records=[]
 for name,s in sorted(docs.items()):
  if name in EXCLUDE or not s.main: continue
  # Match the existing public site's choice to exclude this student's profile from discovery.
  if name=='person-tugce-unsal.html': continue
  title=text(s.main.h1)
  for n,section in enumerate(s.main.select(':scope > section')):
   if section.get('id') in ('research-interest','ai-assistant-entry'): continue
   section=copy.deepcopy(section)
   for extra in section.select('script,style,button,nav,.hero-artwork,.research-join,.buttonrow'):extra.decompose()
   paragraph=text(section).replace('Tuğçe Ünsal','')
   if len(paragraph)<50:continue
   # Put the whole academic facts block together, so shared team memberships are not split.
   if len(paragraph)<=1800: pieces=[paragraph]
   else:
    sentences=re.split(r'(?<=[.!?])\s+',paragraph);pieces=[];part=''
    for sentence in sentences:
     if len(part)+len(sentence)>1450 and part:pieces.append(part);part=''
     part+=((' ' if part else '')+sentence)
    if part:pieces.append(part)
   for part in pieces:
    # Large repeated people/network lists are better served by their individual profiles.
    if len(part)>2200:part=part[:2200]
    sid=section.get('id')
    url=name+('#'+sid if sid and re.fullmatch(r'[a-zA-Z0-9_-]+',sid) else '')
    records.append({'title':title,'url':url,'text':part})
 return {'language':lang,'basis':'Public website records; dates remain those shown in each source.','records':records}

def interface(lang,prefix):
 t=lambda en,tr:pair(lang,en,tr)
 examples=[t('What does Hüseyin Ateş research?','Hüseyin Ateş hangi konularda çalışıyor?'),
           t('Who is on the TÜBİTAK 3501 team?','TÜBİTAK 3501 ekibinde kimler var?'),
           t('Which projects involve Yeşim Taktat Ateş?','Yeşim Taktat Ateş hangi projelerde?'),
           t('How can I propose a collaboration?','Nasıl iş birliği önerebilirim?')]
 return f'''<section class="pagehero"><div class="container"><p class="eyebrow">{t('AI · Academic conversation','Yapay zekâ · Akademik sohbet')}</p><h1>{t('Ask the research assistant','Araştırma asistanına sorun')}</h1><p class="lead">{t('Explore Hüseyin Ateş’s research, projects and collaboration opportunities through a conversation.','Hüseyin Ateş’in araştırmaları, projeleri ve iş birliği olanakları hakkında sorularınızı yazın.')}</p></div></section>
<section class="section"><div class="container ai-layout" id="academic-chat" data-worker="{prefix}assets/academic-assistant-worker.js">
<div class="ai-card"><div class="ai-banner"><p><strong>{t('An AI assistant, not Hüseyin Ateş himself.','Bu bölüm Hüseyin Ateş’in kendisi değil, yapay zekâ asistanıdır.')}</strong> {t('Messages are not delivered to him. For a personal reply, use','Mesajlarınız kendisine iletilmez. Kişisel yanıt için')} <a href="contact.html">{t('direct contact','doğrudan iletişim')}</a>.</p></div>
<div class="chat-toolbar"><span id="chat-mode" class="chat-mode">{t('Website source mode','Site kaynakları modu')}</span><a class="chat-ai-link" href="#ai-model-options">{t('Enable AI','Yapay zekâyı aç')}</a><div><button id="chat-stop" type="button" hidden>{t('Stop','Durdur')}</button> <button id="chat-clear" type="button">{t('Clear conversation','Sohbeti temizle')}</button></div></div>
<div id="chat-log" class="chat-log" role="log" aria-label="{t('Conversation','Sohbet')}" aria-live="polite" aria-relevant="additions text" tabindex="0"></div>
<form id="chat-form" class="chat-compose"><label for="chat-question">{t('Your question','Sorunuz')}</label><textarea id="chat-question" name="question" rows="3" maxlength="1200" required autocomplete="off" placeholder="{t('Ask about a research topic, project or working together…','Araştırma konusu, proje veya iş birliği hakkında sorun…')}"></textarea><div class="chat-compose-row"><small>{t('Enter: send · Shift+Enter: new line · 1,200 characters','Enter: gönder · Shift+Enter: yeni satır · 1.200 karakter')}</small><button id="chat-send" type="submit">{t('Send','Gönder')} →</button></div></form>
<p id="chat-status" class="chat-status" role="status" aria-live="polite">{t('Preparing sources…','Kaynaklar hazırlanıyor…')}</p><noscript><p>{t('JavaScript is required for chat. The','Sohbet için JavaScript gerekir.')} <a href="search.html">{t('site directory','site dizini')}</a> {t('and contact page remain available.','ve iletişim sayfası kullanılabilir.')}</p></noscript></div>
<aside class="ai-side" aria-label="{t('Chat options','Sohbet seçenekleri')}"><section id="ai-model-options"><h2>{t('Generate an answer','Üretken yanıtları açın')}</h2><p>{t('The small AI model runs on your device. It requires a compatible WebGPU browser, substantial memory and an initial download of approximately 400 MB. It may be slow or unavailable on some devices.','Küçük yapay zekâ modeli cihazınızda çalışır. Uyumlu WebGPU tarayıcısı, yeterli bellek ve ilk kullanımda yaklaşık 400 MB indirme gerekir. Bazı cihazlarda yavaş çalışabilir veya açılamayabilir.')}</p><label><input id="chat-consent" type="checkbox"> <span>{t('I agree to download the model and use my device for generation.','Modelin indirilmesini ve cihazımda yanıt üretilmesini kabul ediyorum.')}</span></label><button type="button" id="chat-enable">{t('Start on-device AI','Cihaz içi yapay zekâyı başlat')}</button><progress id="chat-progress" max="1" hidden aria-label="{t('Model preparation','Model hazırlığı')}"></progress><p>{t('Without the model, the chat shows relevant website excerpts rather than generated answers.','Model açılmadan sohbet, üretilmiş yanıt yerine ilgili site kayıtlarından alıntılar gösterir.')}</p></section>
<section><h2>{t('Try a question','Örnek sorular')}</h2>{''.join('<button type="button" class="ai-example" data-chat-question="'+escape(q,quote=True)+'">'+escape(q)+'</button>' for q in examples)}</section>
<section><h2>{t('Privacy and accuracy','Gizlilik ve doğruluk')}</h2><p>{t('Conversation text stays in this open tab and is not saved by this site. Do not enter private or sensitive information. AI can make mistakes; consult the linked records for decisions and dates.','Sohbet metni bu açık sekmede kalır; site tarafından kaydedilmez. Özel veya hassas bilgi yazmayın. Yapay zekâ hata yapabilir; karar ve tarihleri bağlantılı kayıtlardan kontrol edin.')}</p><details><summary>{t('Model and network use','Model ve ağ kullanımı')}</summary><p>{t('Qwen3 0.6B / WebLLM. After consent, program and model files are downloaded from jsDelivr, Hugging Face and MLC’s GitHub-hosted model library. Those services receive normal download requests, not your chat text. Model files may be cached on your device. This is not ChatGPT or a personal message service.','Qwen3 0.6B / WebLLM. Onaydan sonra program ve model dosyaları jsDelivr, Hugging Face ve MLC’nin GitHub üzerindeki model kitaplığından indirilir. Bu hizmetler normal indirme isteklerini alır; sohbet metninizi almaz. Model dosyaları cihazınızda önbelleğe alınabilir. Bu bölüm ChatGPT veya kişisel mesajlaşma hizmeti değildir.')}</p></details><a href="contact.html">{t('Contact Hüseyin Ateş directly','Hüseyin Ateş ile doğrudan iletişim')} →</a></section></aside>
</div></section>'''

def metadata(s,lang):
 title=pair(lang,'Ask the research assistant','Araştırma asistanına sorun')
 desc=pair(lang,'A clearly labelled on-device AI assistant for Hüseyin Ateş’s public academic website.','Hüseyin Ateş’in açık akademik sitesindeki bilgileri kullanan, cihaz üzerinde çalışan yapay zekâ asistanı.')
 url=BASE+('tr/' if lang=='tr' else '')+'assistant.html'
 s.title.string=title+' | Hüseyin Ateş'
 for node in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):node['content']=desc
 for node in s.select('meta[property="og:title"],meta[name="twitter:title"]'):node['content']=s.title.string
 for node in s.select('meta[property="og:url"]'):node['content']=url
 for node in s.select('link[rel="canonical"]'):node['href']=url
 for node in s.select('link[rel="alternate"][hreflang]'):node['href']=BASE+('tr/' if node['hreflang']=='tr' else '')+'assistant.html'
 for node in s.select('.site-language a'):
  dest=node.get('data-site-lang') or node.get('lang');node['href']=('assistant.html' if dest==lang else ('../assistant.html' if lang=='tr' else 'tr/assistant.html'))
 for node in s.select('#main-navigation [aria-current]'):del node['aria-current']
 for node in s.select('script[type="application/ld+json"]'):node.decompose()
 schema=s.new_tag('script',type='application/ld+json');schema.string=json.dumps({'@context':'https://schema.org','@type':'WebPage','name':title,'description':desc,'inLanguage':lang,'url':url},ensure_ascii=False);s.head.append(schema)
 return title,desc

def main():
 for name in ASSETS:shutil.copy2(ROOT/'assets'/name,SITE/'assets'/name)
 csshash=hashlib.sha256((ROOT/'assets/academic-assistant.css').read_bytes()).hexdigest()[:12]
 jshash=hashlib.sha256((ROOT/'assets/academic-assistant.js').read_bytes()).hexdigest()[:12]
 total=0
 for lang in ('en','tr'):
  pre='../' if lang=='tr' else '';folder=SITE/('tr' if lang=='tr' else '')
  docs={p.name:Soup(p.read_text(encoding='utf-8'),'html.parser') for p in sorted(folder.glob('*.html'))}
  knowledge=corpus(docs,lang)
  s=copy.deepcopy(docs['contact.html']);s.main.clear();s.main.append(Soup(interface(lang,pre),'html.parser'))
  title,desc=metadata(s,lang)
  for node in s.select('script[src*="academic-assistant"],link[href*="academic-assistant"],.ai-launch'):node.decompose()
  data=s.new_tag('script',id='assistant-knowledge',type='application/json');data.string=json.dumps(knowledge,ensure_ascii=False).replace('<','\\u003c');s.main.append(data)
  js=s.new_tag('script',src=pre+'assets/academic-assistant.js?v='+jshash,defer='');s.body.append(js)
  docs['assistant.html']=s
  for name,doc in docs.items():
   for old in doc.select('link[href*="academic-assistant.css"],.ai-launch,[data-ai-entry]'):old.decompose()
   doc.head.append(doc.new_tag('link',rel='stylesheet',href=pre+'assets/academic-assistant.css?v='+csshash))
   foot=doc.select_one('.footer-links')
   if foot and not foot.select_one('a[href="assistant.html"]'):
    link=doc.new_tag('a',href='assistant.html');link.string=pair(lang,'AI assistant','Yapay zekâ asistanı');foot.append(link)
   if name!='assistant.html':
    link=doc.new_tag('a',href='assistant.html',attrs={'class':'ai-launch','aria-label':pair(lang,'Open the AI research assistant','Yapay zekâ araştırma asistanını aç')});link.string=pair(lang,'Ask the assistant','Asistana sorun');doc.body.append(link)
   if name in ('index.html','contact.html'):
    entry=doc.new_tag('section',attrs={'class':'section','id':'ai-assistant-entry','data-ai-entry':''})
    entry.append(Soup('<div class="container"><div class="ai-callout"><div><p class="eyebrow">'+pair(lang,'AI academic assistant','Yapay zekâ araştırma asistanı')+'</p><h2>'+pair(lang,'Start with a question','Bir soruyla başlayın')+'</h2><p>'+pair(lang,'Ask about the research and projects. AI-generated guidance is separate from personal correspondence.','Araştırmalar ve projeler hakkında sorun. Yapay zekâ desteği, kişisel yazışmadan ayrıdır.')+'</p></div><a class="btn" href="assistant.html">'+pair(lang,'Open conversation','Sohbeti aç')+' →</a></div></div>','html.parser'))
    doc.main.append(entry)
   if name in ('site-notes.html','accessibility.html'):
    for old in doc.select('#assistant-privacy-note'):old.decompose()
    note=doc.new_tag('section',attrs={'class':'section','id':'assistant-privacy-note'})
    note.append(Soup('<div class="container"><h2>'+pair(lang,'AI assistant','Yapay zekâ asistanı')+'</h2><p>'+pair(lang,'The optional academic assistant runs generation on the visitor’s compatible device. Chat text is not submitted to the website owner or an AI API and is not stored by this site. Model and program downloads contact third-party hosting services only after explicit consent. Downloaded model files may remain in browser cache. Website-source mode, keyboard controls, visible AI labelling and direct contact are available; generated answers may be wrong.','İsteğe bağlı akademik asistan, uyumlu ziyaretçi cihazında yanıt üretir. Sohbet metni site sahibine veya bir yapay zekâ API hizmetine gönderilmez; bu site tarafından kaydedilmez. Model ve program indirmeleri yalnızca açık onaydan sonra üçüncü taraf barındırma hizmetlerine bağlanır. İndirilen model dosyaları tarayıcı önbelleğinde kalabilir. Site kaynakları modu, klavye kontrolleri, görünür yapay zekâ etiketi ve doğrudan iletişim seçeneği sunulur; üretilen yanıtlar yanlış olabilir.')+'</p></div>','html.parser'))
    doc.main.append(note)
  search=docs['search.html'].select_one('#site-search-data');records=json.loads(search.string)
  records=[r for r in records if r.get('url')!='assistant.html']
  records.append({'title':title,'url':'assistant.html','summary':desc,'category':'about','label':pair(lang,'Profile & site information','Profil ve site bilgileri'),'key':normalized(title+' '+desc+' sohbet chat yapay zekâ artificial intelligence')})
  search.string=json.dumps(records,ensure_ascii=False).replace('<','\\u003c')
  directory=docs['search.html'].select_one('#search-directory ul')
  if directory and not directory.select_one('a[href="assistant.html"]'):
   li=docs['search.html'].new_tag('li');a=docs['search.html'].new_tag('a',href='assistant.html');a.string=title;li.append(a);directory.append(li)
  for name,doc in docs.items():(folder/name).write_text(str(doc).replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio='),encoding='utf-8')
  total+=len(docs)
  print(lang,'assistant public source chunks:',len(knowledge['records']))
 for filename in ('deployment.json','quality-report.json'):
  path=SITE/filename;j=json.loads(path.read_text());j.pop('files',None);j['assistant']={'inference':'opt-in on-device WebLLM 0.2.88 / Qwen3-0.6B','no_api_key':True,'remote_chat_requests':False,'languages':['en','tr']};j['page_count']=total;j['language_pairs']=total//2
  if filename=='deployment.json':j['pages']=sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html'))
  path.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
 sitemap=SITE/'sitemap.xml';xml=Soup(sitemap.read_text(),'xml')
 for old in list(xml.find_all('url')):
  if old.loc and old.loc.string in (BASE+'assistant.html',BASE+'tr/assistant.html'):old.decompose()
 for pre in ('','tr/'):
  node=xml.new_tag('url');loc=xml.new_tag('loc');loc.string=BASE+pre+'assistant.html';node.append(loc)
  for code,prefix in (('en',''),('tr','tr/'),('x-default','')):node.append(xml.new_tag('xhtml:link',attrs={'rel':'alternate','hreflang':code,'href':BASE+prefix+'assistant.html'}))
  xml.urlset.append(node)
 sitemap.write_text(str(xml),encoding='utf-8')
 print('Assistant published in EN/TR; page count:',total)

if __name__=='__main__':main()
