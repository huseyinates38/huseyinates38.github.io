#!/usr/bin/env python3
"""Search punctuation, stale-result, mobile access and content-regression tests."""
from pathlib import Path
from urllib.parse import urlsplit
import functools,http.server,threading,shutil,json,sys
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';OFFLINE='--offline' in sys.argv
sys.path.insert(0,str(ROOT/'tests'));from design_browser import inline

def main():
 report={'release':'5.1','offline':OFFLINE,'search_cases':0,'publication_cases':0,'mobile_search_checks':0,'result':'running','errors':[]}
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=None
 if not OFFLINE:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
   page.on('pageerror',lambda e:report['errors'].append(str(e)))
   def load(name):
    if not OFFLINE:page.goto(base+name,wait_until='domcontentloaded');return
    source=SITE/name;s=Soup(source.read_text(),'html.parser');scripts=[]
    for n in s.select('script[src]'):
     p=(source.parent/urlsplit(n['src']).path).resolve()
     if p.is_file():scripts.append(p.read_text())
    page.set_content(inline(name),wait_until='load')
    for code in scripts:page.add_script_tag(content=code)
   for pre in ['','tr/']:
    load(pre+'search.html');page.locator('#site-query').fill('Noroozi');assert page.locator('#site-search-results li').count()>0
    for query in ['[',']','(',')','\\','+','*','?','.','a[','{','^','$','__proto__','constructor']:
     page.locator('#site-query').fill(query)
     expected=page.evaluate('(q)=>JSON.parse(document.querySelector("#site-search-data").textContent).filter(x=>x.key.includes(q)).length',query)
     assert page.locator('#site-search-results li').count()==min(expected,12),(pre,query,expected)
     if expected==0:assert page.locator('#site-search-more').is_hidden()
     report['search_cases']+=1
    page.locator('#site-query').fill('Noroozi');assert page.locator('#site-search-results li').count()>0
    load(pre+'publications.html');page.locator('#pub-query').fill('Ates');assert page.locator('.publication:not([hidden])').count()>0
    for query in ['[',']','(','\\','+','*','?', '__proto__','constructor']:
     page.locator('#pub-query').fill(query)
     expected=page.evaluate('(q)=>[...document.querySelectorAll(".publication")].filter(x=>x.textContent.includes(q)).length',query)
     assert page.locator('.publication:not([hidden])').count()==expected,(pre,query,expected)
     report['publication_cases']+=1
    for name in ['index.html','team.html','publications.html','resources.html']:
     load(pre+name);page.locator('.menu-button').click();assert page.locator('#main-navigation a.mobile-search-link').is_visible()
     assert page.locator('#main-navigation a.mobile-search-link').get_attribute('href')=='search.html';report['mobile_search_checks']+=1
    load(pre+'team.html');page.locator('#people-query').fill('zzzz-unmatched-researcher');assert page.locator('#people-no-results').is_visible();assert page.locator('.person-card[data-person]:not([hidden])').count()==0
    page.locator('#people-reset').click();assert page.locator('#people-no-results').is_hidden();assert page.locator('.person-card[data-person]:not([hidden])').count()==31
    for key in ['guido-makransky','bui-van-hong','marc-romero-carbonell']:assert page.locator(f'[data-person="{key}"] .relationship-stage').count()==1
    page.set_viewport_size({'width':1600,'height':1080});load(pre+'index.html')
    assert page.locator('.showcase-news-card .showcase-card-img img').count()==5
    assert all(page.locator('.showcase-news-card .showcase-card-img img').nth(i).evaluate('(e)=>getComputedStyle(e).objectFit')=='contain' for i in range(5))
    page.set_viewport_size({'width':390,'height':844})
   assert not report['errors'],report['errors'];browser.close()
 finally:
  if server:server.shutdown()
 report['result']='passed';(ROOT/'audit-browser-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
