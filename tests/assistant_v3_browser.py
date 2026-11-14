#!/usr/bin/env python3
"""Final UI checks. Server replies are mock fixtures, NOT a model-quality evaluation."""
from pathlib import Path
import functools,http.server,json,threading,shutil,sys,base64,mimetypes
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'
OFFLINE='--offline' in sys.argv
def inline(name, config=None):
 source=SITE/name;s=Soup(source.read_text(),'html.parser')
 base=s.new_tag('base',href='https://huseyinates38.github.io/'+name);s.head.insert(0,base)
 if config is not None:
  s.select_one('#assistant-service-config').string=json.dumps(config)
  for n in s.select('#cloud-enable,#cloud-consent'):n.attrs.pop('disabled',None)
 for tag in list(s.select('link[rel="stylesheet"]')):
  path=(source.parent/urlsplit(tag['href']).path).resolve()
  if path.is_file():node=s.new_tag('style');node.string=path.read_text();tag.replace_with(node)
  else:tag.decompose()
 for tag in list(s.select('script[src]')):
  path=(source.parent/urlsplit(tag['src']).path).resolve()
  if path.is_file():del tag['src'];tag.string=path.read_text()
  else:tag.decompose()
 for tag in s.select('img[src]'):
  path=(source.parent/urlsplit(tag['src']).path).resolve()
  if path.is_file():tag['src']='data:'+(mimetypes.guess_type(path.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(path.read_bytes()).decode()
 return str(s)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 report={'layout_checks':0,'interaction_checks':0,'errors':[],'inference':'mock transport only; real model evaluation not run'}
 previews=ROOT/'assistant-v3-previews';previews.mkdir(exist_ok=True)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
   page=browser.new_page(reduced_motion='reduce');page.on('pageerror',lambda e:report['errors'].append(str(e)))
   requests=[];page.on('request',lambda r:requests.append(r.url))
   for width in (390,768,1440):
    page.set_viewport_size({'width':width,'height':950})
    for pre in ('','tr/'):
     page.set_content(inline(pre+'assistant.html'),wait_until='load') if OFFLINE else page.goto(base+pre+'assistant.html',wait_until='networkidle')
     configured=bool(page.locator('#assistant-service-config').text_content() and json.loads(page.locator('#assistant-service-config').text_content()).get('endpoint'))
     assert page.locator('#cloud-enable').is_disabled() is (not configured)
     assert page.locator('#cloud-consent').is_disabled() is (not configured)
     assert page.locator('h1').count()==1
     assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
     assert page.locator('script[src*="academic-assistant.js"]').count()==0
     page.locator('#chat-question').fill('Yeşim Taktat Ateş hangi projelerde?' if pre else 'Which projects involve Yeşim Taktat Ateş?');page.locator('#chat-send').click()
     assert '3501' in page.locator('.chat-assistant').last.inner_text()
     assert page.locator('.chat-assistant').last.locator('.chat-sources a').count()>=2
     page.locator('#chat-question').fill('Peki hangi kurumda?' if pre else 'What is her affiliation?');page.locator('#chat-send').click()
     assert ('bağımsız' if pre else 'independent') in page.locator('.chat-assistant').last.inner_text().lower()
     page.locator('#chat-question').fill('<img src=x onerror=alert(1)>');page.locator('#chat-send').click();assert page.locator('#chat-log img').count()==0
     page.locator('#chat-clear').click();assert page.locator('.chat-message').count()==1
     report['layout_checks']+=1;report['interaction_checks']+=4
     if pre and width in (390,1440):page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(previews/f'assistant-v3-{width}.png'),full_page=True)
   assert not any('web-llm' in r or 'huggingface' in r or 'api.openai.com' in r for r in requests)
   # Explicitly configured test endpoint. No production mock mode or credential exists.
   mock=browser.new_page();mock.on('pageerror',lambda e:report['errors'].append(str(e)))
   endpoint='https://test-service.invalid/api/chat'
   mock.evaluate("""()=>{window.__posts=[];window.__fail=false;window.fetch=async(url,opts={})=>{if(!opts.method)return new Response(JSON.stringify({ready:true}));window.__posts.push(JSON.parse(opts.body));return window.__fail?new Response(JSON.stringify({error:'not_configured'}),{status:503}):new Response(JSON.stringify({answer:'Bu bir test yanıtıdır.',follow_up:'Hangi sınıf düzeyini düşünüyorsunuz?',kind:'guidance',sources:[{title:'Araştırma',url:'tr/research.html'}]}));};}""")
   mock.set_content(inline('tr/assistant.html',{'endpoint':endpoint,'version':3}),wait_until='load')
   mock.locator('#cloud-enable').click();assert not mock.evaluate('window.__posts')
   mock.locator('#cloud-consent').check();mock.locator('#cloud-enable').click();mock.wait_for_function('document.querySelector("#chat-mode").textContent.includes("sunucu")')
   mock.locator('#chat-question').fill('Fen eğitiminde yapay zekâ ile bir çalışma tasarlamak istiyorum.');mock.locator('#chat-send').click();mock.wait_for_function('document.querySelector("#chat-status").textContent==="Yanıt hazır."')
   assert 'test yanıtıdır' in mock.locator('.chat-assistant').last.inner_text()
   mock.locator('#chat-question').fill('7. sınıf öğrencileri.');mock.locator('#chat-send').click();mock.wait_for_function('document.querySelector("#chat-status").textContent==="Yanıt hazır."')
   posts=mock.evaluate('window.__posts');assert len(posts)==2 and len(posts[-1]['messages'])==3 and posts[-1]['consent'] is True
   mock.evaluate('window.__fail=true');mock.locator('#chat-question').fill('Bir sonraki adım?');mock.locator('#chat-send').click();mock.locator('.chat-retry').wait_for()
   assert 'etkin değil' in mock.locator('.chat-assistant').last.inner_text()
   users=mock.locator('.chat-user').count();mock.evaluate('window.__fail=false');mock.locator('.chat-retry').click();mock.wait_for_function('document.querySelector("#chat-status").textContent==="Yanıt hazır."')
   assert mock.locator('.chat-user').count()==users
   mock.locator('#chat-clear').click();mock.locator('#chat-question').fill('Yeni konuşma.');mock.locator('#chat-send').click();mock.wait_for_function('document.querySelector("#chat-status").textContent==="Yanıt hazır."')
   assert len(mock.evaluate('window.__posts')[-1]['messages'])==1
   mock.locator('#cloud-consent').uncheck();assert 'üretken model değil' in mock.locator('#chat-mode').inner_text()
   report['interaction_checks']+=9
   browser.close()
 finally:server.shutdown()
 assert not report['errors'],report['errors'];report['result']='passed'
 (ROOT/'assistant-v3-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
