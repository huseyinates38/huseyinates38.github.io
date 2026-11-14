#!/usr/bin/env python3
"""Assistant UI and grounding regressions; mocked inference is explicitly labelled.
Does not claim to validate model quality or execute real GPU inference.
"""
from pathlib import Path
import base64,functools,http.server,json,mimetypes,shutil,threading,sys
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';OFFLINE='--offline' in sys.argv
def inline(name):
 source=SITE/name;s=Soup(source.read_text(),'html.parser')
 base=s.new_tag('base',href='https://assistant-test.invalid/'+name);s.head.insert(0,base)
 for tag in list(s.select('link[rel=stylesheet]')):
  f=(source.parent/urlsplit(tag['href']).path).resolve()
  if f.is_file():
   n=s.new_tag('style');n.string=f.read_text();tag.replace_with(n)
  else:tag.decompose()
 for tag in list(s.select('script[src]')):
  f=(source.parent/urlsplit(tag['src']).path).resolve()
  if f.is_file():del tag['src'];tag.string=f.read_text()
  else:tag.decompose()
 for tag in s.select('img[src]'):
  f=(source.parent/urlsplit(tag['src']).path).resolve()
  if f.is_file():tag['src']='data:'+(mimetypes.guess_type(f.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(f.read_bytes()).decode()
 return str(s)

class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 report={'result':'running','layout_checks':0,'interaction_checks':0,'model_inference':'UI protocol mocked; no claim of real-model inference','errors':[]}
 previews=ROOT/'assistant-previews';previews.mkdir(exist_ok=True)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
   page=browser.new_page(reduced_motion='reduce');page.on('pageerror',lambda error:report['errors'].append(str(error)))
   # No model or external script request may occur merely by visiting or asking in source mode.
   remote=[]
   page.route('**/*',lambda route: route.continue_() if urlsplit(route.request.url).hostname in ('127.0.0.1','localhost') else (remote.append(route.request.url),route.abort())[-1])
   for width in (390,768,1440):
    page.set_viewport_size({'width':width,'height':1050})
    for pre in ('','tr/'):
     page.set_content(inline(pre+'assistant.html'),wait_until='load') if OFFLINE else page.goto(base+pre+'assistant.html',wait_until='networkidle')
     assert page.locator('h1').count()==1
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(pre,width)
     assert page.locator('.ai-launch').count()==0
     assert page.locator('#chat-enable').is_enabled()
     assert page.locator('#chat-consent').is_checked() is False
     assert page.locator('.chat-assistant').count()==1
     assert page.locator('.ai-banner').inner_text().find('Hüseyin Ateş')>=0
     report['layout_checks']+=1
     for q in ('3501','Yeşim Taktat Ateş','zzxx997700unmatched','<img src=x onerror=alert(1)>'):
      page.locator('#chat-question').fill(q);page.locator('#chat-send').click()
      assert page.locator('.chat-user').last.inner_text().find(q)>=0
      assert page.locator('#chat-log img').count()==0
      if q in ('3501','Yeşim Taktat Ateş'):
       assert page.locator('.chat-assistant').last.locator('.chat-sources a').count()>0
      report['interaction_checks']+=1
     page.locator('#chat-clear').click();assert page.locator('.chat-message').count()==1
     page.locator('#chat-question').fill('sen kimsin' if pre else 'who are you');page.locator('#chat-send').click()
     assert ('kendisi değilim' if pre else 'not Hüseyin Ateş himself') in page.locator('.chat-assistant').last.inner_text()
     page.locator('#chat-question').fill('randevu' if pre else 'appointment');page.locator('#chat-send').click()
     assert page.locator('.chat-assistant').last.locator('a[href="contact.html"]').count()==1
     page.locator('#chat-clear').click();page.locator('[data-chat-question]').first.click();assert page.locator('#chat-question').input_value()
     page.locator('#chat-enable').click();assert not page.locator('#chat-consent').is_checked()
     if pre=='tr/' and width in (390,1440):
      page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(previews/f'assistant-{width}.png'),full_page=True)
   assert not any(('web-llm' in x or 'huggingface' in x) for x in remote),remote
   # Transparent fallback when WebGPU isn't supported.
   fallback=browser.new_page();fallback.add_init_script('Object.defineProperty(navigator,"gpu",{value:undefined,configurable:true})')
   fallback.evaluate('Object.defineProperty(navigator,"gpu",{value:undefined,configurable:true})');
   fallback.set_content(inline('assistant.html'),wait_until='load') if OFFLINE else fallback.goto(base+'assistant.html',wait_until='domcontentloaded');fallback.locator('#chat-consent').check();fallback.locator('#chat-enable').click()
   assert 'cannot run' in fallback.locator('#chat-status').inner_text();fallback.close()
   # End-to-end UI protocol with a test-only worker, no production mock switch.
   mock=browser.new_page();mock.on('pageerror',lambda error:report['errors'].append(str(error)))
   mock.add_init_script('Object.defineProperty(navigator,"gpu",{value:{requestAdapter:async()=>({features:new Set(["shader-f16"])})},configurable:true})')
   worker='''self.onmessage=({data})=>{if(data.type==='init')self.postMessage({type:'ready'});if(data.type==='ask'){self.postMessage({type:'token',text:'<think>hidden reasoning</think>Test-only generated answer.'});self.postMessage({type:'done'});}};'''
   mock.route('**/academic-assistant-worker.js',lambda route:route.fulfill(status=200,content_type='text/javascript',body=worker))
   
   if OFFLINE:
    mock.evaluate('Object.defineProperty(navigator,"gpu",{value:{requestAdapter:async()=>({features:new Set(["shader-f16"])})},configurable:true})')
    mock.evaluate("() => { window.Worker=class {postMessage(d){setTimeout(()=>{if(d.type==='init')this.onmessage?.({data:{type:'ready'}});else {this.onmessage?.({data:{type:'token',text:'<think>hidden reasoning</think>Test-only generated answer.'}});this.onmessage?.({data:{type:'done'}});}},10);}terminate(){}}; }")
    mock.set_content(inline('assistant.html'),wait_until='load')
   else:mock.goto(base+'assistant.html',wait_until='domcontentloaded')
   mock.locator('#chat-consent').check();mock.locator('#chat-enable').click()
   mock.wait_for_function('document.querySelector("#chat-mode").textContent.includes("generative")')
   mock.locator('#chat-question').fill('3501');mock.locator('#chat-send').click()
   mock.wait_for_function('document.querySelector("#chat-status").textContent.includes("completed")')
   assert 'Test-only generated answer.' in mock.locator('.chat-assistant').last.inner_text()
   assert 'hidden reasoning' not in mock.locator('#chat-log').inner_text()
   assert mock.locator('.chat-assistant').last.locator('.chat-sources a').count()>0
   mock.locator('#chat-stop').click();assert 'source mode' in mock.locator('#chat-mode').inner_text()
   mock.locator('#chat-clear').click();assert mock.locator('.chat-message').count()==1
   report['interaction_checks']+=8
   mock.close()
   if not OFFLINE:
    # Real package import + model configuration, without downloading model weights.
    probe=browser.new_page();probe.goto(base+'assistant.html',wait_until='domcontentloaded')
    probe.set_default_timeout(90000)
    result=probe.evaluate('''async()=>{const lib=await import('https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.88/lib/index.js');const item=lib.prebuiltAppConfig.model_list.find(m=>m.model_id==='Qwen3-0.6B-q4f16_1-MLC');if(!item||typeof lib.CreateMLCEngine!=='function')throw Error('Missing runtime/model');const response=await fetch('https://huggingface.co/mlc-ai/Qwen3-0.6B-q4f16_1-MLC/resolve/main/mlc-chat-config.json');if(!response.ok)throw Error('Model config unavailable');const cfg=await response.json();return {model:item.model_id,tokenizer:cfg.tokenizer_files.length};}''')
    assert result['tokenizer']>0;report['live_runtime_and_model_config']=result;probe.close()
   browser.close()
  for pre in ('','tr/'):
   s=Soup((SITE/pre/'assistant.html').read_text(),'html.parser')
   kb=json.loads(s.select_one('#assistant-knowledge').string)
   assert len(kb['records'])>100
   assert not any(r['url'].startswith('person-tugce-unsal.html') for r in kb['records'])
   assert any('3501' in r['text'] and 'Yeşim' in r['title'] for r in kb['records'])
   for name in ('index.html','team.html','contact.html'):
    doc=Soup((SITE/pre/name).read_text(),'html.parser');assert doc.select_one('a.ai-launch[href="assistant.html"]')
   assert s.select_one('link[rel="canonical"]')['href'].endswith(pre+'assistant.html')
   assert len(list(SITE.glob('*.html')))==len(list((SITE/'tr').glob('*.html')))==70
   assert (s.select_one('.site-language a[lang="en"]')['href']=='../assistant.html' if pre else s.select_one('.site-language a[lang="tr"]')['href']=='tr/assistant.html')
 finally:server.shutdown()
 assert not report['errors'],report['errors']
 report['result']='passed';(ROOT/'assistant-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
