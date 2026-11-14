#!/usr/bin/env python3
"""Literal directory queries, count units, reset and focused profile layout tests."""
from pathlib import Path
import functools,http.server,json,shutil,sys,threading
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from design_browser import inline
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';OFFLINE='--offline' in sys.argv
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 previews=ROOT/'profile-previews';previews.mkdir(exist_ok=True)
 report={'release':'5.2','network_query_checks':0,'network_reset_checks':0,'layout_checks':0,'errors':[]}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
   page=browser.new_page(reduced_motion='reduce')
   page.on('pageerror',lambda e:report['errors'].append(str(e)))
   def load(name):
    if not OFFLINE:page.goto(base+name,wait_until='domcontentloaded');return
    source=SITE/name;s=Soup(source.read_text(),'html.parser');scripts=[]
    for n in s.select('script[src]'):
     f=(source.parent/urlsplit(n['src']).path).resolve()
     if f.is_file():scripts.append(f.read_text())
    page.set_content(inline(name),wait_until='load')
    for code in scripts:page.add_script_tag(content=code)
    page.evaluate('window.scrollTo(0,0)')
   for width in [390,768,1440]:
    page.set_viewport_size({'width':width,'height':950})
    for pre in ['','tr/']:
     load(pre+'research-network.html')
     assert page.locator('.network-country:not([hidden])').count()==22
     assert ('ülke' if pre else 'countries') in page.locator('#network-count').inner_text()
     page.locator('#network-query').fill('Wageningen')
     assert page.locator('.network-country:not([hidden])').count()==1
     assert page.locator('#network-no-results').is_hidden();report['network_query_checks']+=1
     for q in ['__no_matching_country__','[','(','\\','+','*']:
      page.locator('#network-query').fill(q)
      expected=page.evaluate('(q)=>[...document.querySelectorAll(".network-country")].filter(x=>x.textContent.includes(q)).length',q)
      assert page.locator('.network-country:not([hidden])').count()==expected,(pre,q)
      assert page.locator('#network-no-results').is_visible()==(expected==0)
      assert page.locator('#network-count').inner_text().startswith(f'{expected} / 22' if pre else f'Showing {expected} of 22')
      report['network_query_checks']+=1
     page.locator('#network-reset').click()
     assert page.locator('.network-country:not([hidden])').count()==22
     assert page.locator('#network-no-results').is_hidden()
     assert page.locator('#network-query').input_value()=='';report['network_reset_checks']+=1
     for name in ['research-network.html','person-gokhan-ince.html','person-elena-novak.html','person-bui-van-hong.html','person-marc-romero-carbonell.html','team.html','resource-use.html']:
      load(pre+name)
      page.evaluate('document.querySelectorAll("img").forEach(i=>i.loading="eager")')
      page.evaluate('async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))}')
      assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(pre,name,width)
      assert page.locator('h1').count()==1
      if name=='team.html':
       for group_id,expected in [('project-team-aub-stem',3),('project-team-unassigned',3),('project-school-practice',2),('project-advisers',1)]:
        assert page.locator('#'+group_id+' .person-card').count()==expected,(pre,group_id)
       for institution in ['surrey','twente']:
        logo=page.locator('.institution-mark.dark img[src$="'+institution+'.png"]').first
        assert logo.count()==1,(pre,institution)
        assert logo.evaluate('(img)=>getComputedStyle(img.parentElement).backgroundColor')=='rgb(23, 55, 70)',(pre,institution)
        if not OFFLINE:assert logo.evaluate('(img)=>img.complete && img.naturalWidth>0'),(pre,institution)
       if width==1440:
        page.locator('#people-query').fill('Kibar Gül')
        assert page.locator('#project-team-aub-stem').is_visible()
        assert page.locator('#project-team-unassigned').is_hidden()
        page.locator('#people-reset').click()
      report['layout_checks']+=1
      if width in [390,1440] and pre=='tr/' and name in ['person-gokhan-ince.html','person-marc-romero-carbonell.html','resource-use.html']:
       page.evaluate('window.scrollTo(0,0)')
       page.screenshot(path=str(previews/(name[:-5]+'-'+str(width)+'.png')),full_page=True)
   browser.close()
 finally:server.shutdown()
 assert not report['errors'],report['errors']
 report['result']='passed'
 (ROOT/'network-browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
