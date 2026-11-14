#!/usr/bin/env python3
"""Final assistant upgrade. Exports only already-public data; never activates paid use."""
from pathlib import Path
import json, re, shutil, hashlib, unicodedata
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'
def main():
 config=json.loads((ROOT/'content/assistant-service.json').read_text())
 endpoint=config.get('endpoint','')
 if endpoint:
  u=urlsplit(endpoint)
  assert u.scheme=='https' and u.hostname and u.path=='/api/chat' and not u.query and not u.fragment and not u.username and not u.password
 bundle={};controller=ROOT/'assets/assistant-conversation.js'
 shutil.copy2(controller,SITE/'assets/assistant-conversation.js')
 digest=hashlib.sha256(controller.read_bytes()).hexdigest()[:12]
 for lang in ('en','tr'):
  tr=lang=='tr';folder=SITE/('tr' if tr else '');file=folder/'assistant.html'
  s=Soup(file.read_text(),'html.parser');pick=lambda en,t:t if tr else en
  kb=json.loads(s.select_one('#assistant-knowledge').string)
  facts=json.loads(s.select_one('#assistant-facts').string)
  records=[]
  for person in facts['people'].values():
   info={k:v for k,v in person.items() if k not in ('url','name') and v}
   records.append({'title':person['name'],'url':person['url'],'text':json.dumps(info,ensure_ascii=False)})
  for project in facts['projects'].values():
   records.append({'title':project['title'],'url':project['url'],'text':json.dumps({k:v for k,v in project.items() if k not in ('url','title')},ensure_ascii=False)})
  records.extend(kb['records'])
  records=[r for r in records if not r['url'].startswith('person-tugce-unsal.html')]
  names=[re.sub(r'^(?:(?:Doç|Dr|Prof|Assoc|Assist|Öğr|Üyesi)\.?\s*)+','',p['name']) for p in facts['people'].values() if not p['url'].startswith('person-tugce-unsal.html')]
  bundle[lang]={'records':records,'names':names}
  for el in s.select('script[src*="academic-assistant.js"],script[src*="assistant-conversation.js"],#assistant-service-config'):
   el.decompose()
  data=s.new_tag('script',id='assistant-service-config',type='application/json');data.string=json.dumps({'version':3,'endpoint':endpoint}).replace('<','\\u003c');s.body.append(data)
  js=s.new_tag('script',src=('../' if tr else '')+'assets/assistant-conversation.js?v='+digest,defer='');s.body.append(js)
  s.select_one('#academic-chat').attrs.pop('data-worker',None)
  s.select_one('.ai-banner strong').string=pick('This interface is not Hüseyin Ateş himself.','Bu arayüz Hüseyin Ateş’in kendisi değildir.')
  s.select_one('.pagehero .eyebrow').string=pick('Academic website · conversation and guide','Akademik site · sohbet ve rehber')
  s.select_one('#chat-question')['maxlength']='2000'
  s.select_one('.chat-compose-row small').string=pick('Enter: send · Shift+Enter: new line · 2,000 characters','Enter: gönder · Shift+Enter: yeni satır · 2.000 karakter')
  s.select_one('#chat-mode').string=pick('Website guide · not a generative model','Site rehberi · üretken model değil')
  for a in s.select('.chat-ai-link'):a.decompose()
  aside=s.select_one('.ai-side');aside.clear()
  title=pick('AI conversation connection','Yapay zekâ sohbet bağlantısı')
  state=pick('Server connection is not configured. Only the website guide is active.','Sunucu bağlantısı henüz yapılandırılmadı. Şu an yalnızca site rehberi çalışıyor.') if not endpoint else pick('Enable to converse with the server-side model.','Sunucudaki modelle konuşmak için etkinleştirin.')
  consent=pick('I agree to send my question and recent conversation to the model provider (OpenAI). Do not share sensitive information.','Sorumu ve yakın konuşma geçmişini model sağlayıcısına (OpenAI) göndermeyi kabul ediyorum. Hassas bilgi paylaşmayın.')
  aside.append(Soup(f'<section><h2>{title}</h2><p id="cloud-state">{state}</p><label><input type="checkbox" id="cloud-consent"/> <span>{consent}</span></label><button type="button" id="cloud-enable">'+pick('Enable AI conversation','Yapay zekâ sohbetini aç')+'</button></section>','html.parser'))
  if not endpoint:s.select_one('#cloud-enable')['disabled']='';s.select_one('#cloud-consent')['disabled']=''
  examples=[pick('Who is on the 3501 team?','3501 ekibinde kimler var?'),pick('Which projects involve Yeşim Taktat Ateş?','Yeşim Taktat Ateş hangi projelerde?'),pick('How can I contact Hüseyin Ateş?','Hüseyin Ateş’e nasıl ulaşabilirim?')]
  example=s.new_tag('section');h=s.new_tag('h2');h.string=pick('Questions about the site','Site hakkında sorular');example.append(h)
  for question in examples:
   b=s.new_tag('button',type='button',attrs={'class':'ai-example','data-chat-question':question});b.string=question;example.append(b)
  aside.append(example)
  privacy=pick('Guide mode uses website records and predefined rules; it is not generative AI. The old small local model is no longer used. Remote conversation starts only after consent and requires an active service. This site does not save chats; hosting and provider data policies also apply. Clearing removes local history, not data already processed by a provider.','Rehber modu site kayıtları ve önceden tanımlanmış kurallarla çalışır; üretken yapay zekâ değildir. Eski küçük yerel model artık kullanılmaz. Sunucu sohbeti yalnızca onayla ve etkin hizmetle başlar. Bu site konuşmaları kaydetmez; barındırma ve model sağlayıcısının veri politikaları ayrıca geçerlidir. Temizleme, yerel geçmişi siler; sağlayıcıya daha önce gönderilen veriyi geri almaz.')
  aside.append(Soup('<section><h2>'+pick('Privacy and limits','Gizlilik ve sınırlar')+'</h2><p>'+privacy+'</p><a href="contact.html">'+pick('Contact directly','Doğrudan iletişim')+'</a></section>','html.parser'))
  s.select_one('.pagehero .lead').string=pick('Ask about the public research records. Generative conversation is available only when its server connection is enabled.','Açık araştırma kayıtları hakkında sorun. Üretken sohbet yalnızca sunucu bağlantısı etkinleştirildiğinde kullanılabilir.')
  desc=pick('Academic website guide with optional, authorised server-side conversation.','İsteğe bağlı ve yetkilendirilmiş sunucu sohbetiyle akademik site rehberi.')
  for meta in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):meta['content']=desc
  for ld in s.select('script[type="application/ld+json"]'):
   obj=json.loads(ld.string or '{}');obj['description']=desc;ld.string=json.dumps(obj,ensure_ascii=False).replace('<','\\u003c')
  file.write_text(str(s),encoding='utf-8')
  # Keep site-wide privacy text consistent with the replacement assistant.
  for name in ('site-notes.html','accessibility.html'):
   path=folder/name;doc=Soup(path.read_text(),'html.parser');note=doc.select_one('#assistant-privacy-note p')
   if note:note.string=privacy
   path.write_text(str(doc),encoding='utf-8')
 bundle['revision']=hashlib.sha256(json.dumps(bundle,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
 (SITE/'assets/assistant-context.json').write_text(json.dumps(bundle,ensure_ascii=False),encoding='utf-8')
 service=ROOT/'assistant-service/data';service.mkdir(parents=True,exist_ok=True)
 (service/'knowledge.json').write_text(json.dumps(bundle,ensure_ascii=False),encoding='utf-8')
 # Update existing search entries; no extra indexing of excluded people.
 for lang in ('en','tr'):
  folder=SITE/('tr' if lang=='tr' else '');path=folder/'search.html';doc=Soup(path.read_text(),'html.parser');data=doc.select_one('#site-search-data');rows=json.loads(data.string)
  for row in rows:
   if row['url'] in ('assistant.html','site-notes.html','accessibility.html'):
    page=Soup((folder/row['url']).read_text(),'html.parser');main=page.main
    for hidden in main.select('script,style'):hidden.decompose()
    row['summary']=main.select_one('.lead').get_text(' ',strip=True) if main.select_one('.lead') else row.get('summary','')
    row['key']=''.join(c for c in unicodedata.normalize('NFD',main.get_text(' ',strip=True)) if unicodedata.category(c)!='Mn').replace('ı','i').lower()
  data.string=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c');path.write_text(str(doc),encoding='utf-8')
 for name in ('deployment.json','quality-report.json'):
  path=SITE/name;value=json.loads(path.read_text());value.pop('files',None);value['assistant_mode']='server-ready; source guide until authorised';value['assistant_context_revision']=bundle['revision'];path.write_text(json.dumps(value,ensure_ascii=False,indent=2))
 print('ASSISTANT V3 BUILT: cloud configured =',bool(endpoint),'revision =',bundle['revision'])
if __name__=='__main__':main()
