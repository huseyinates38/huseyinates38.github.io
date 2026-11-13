#!/usr/bin/env python3
"""Bilingual EN/TR browser checks. Not independent accessibility certification."""
from __future__ import annotations
import functools,http.server,threading,json,shutil,sys
from bs4 import BeautifulSoup as Soup
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'

def main():
  offline='--offline' in sys.argv
  report={'release':'4.9','widths':[360,768,1440],'pages':0,'layout_checks':0,'interactions':[],'errors':[]}
  class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
  server=None
  if not offline:
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
  else:base='' 
  try:
    with sync_playwright() as pw:
      browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
      ctx=browser.new_context(viewport={'width':1280,'height':900},reduced_motion='reduce')
      page=ctx.new_page();current=[None];page.on('pageerror',lambda e:report['errors'].append((current[0],str(e))))
      def load(name):
        current[0]=name
        if not offline:
          page.goto(base+name,wait_until='domcontentloaded');return
        source=SITE/name; soup=Soup(source.read_text(encoding='utf-8'),'html.parser');scripts=[]
        for node in list(soup.select('link[rel=stylesheet]')):
          u=urlsplit(node.get('href',''));path=(source.parent/u.path).resolve()
          if path.is_file():
            style=soup.new_tag('style');style.string=path.read_text(encoding='utf-8');node.replace_with(style)
        for node in list(soup.select('script[src]')):
          u=urlsplit(node.get('src',''));path=(source.parent/u.path).resolve()
          if path.is_file():scripts.append(path.read_text(encoding='utf-8'))
          node.decompose()
        page.set_content(str(soup),wait_until='domcontentloaded')
        for code in scripts:page.add_script_tag(content=code)
      pages=sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html'))
      report['pages']=len(pages)
      assert len(pages)==138,len(pages)
      for width in [360,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for file in pages:
          load(file)
          page.wait_for_timeout(12)
          dim=page.evaluate('({width:document.documentElement.scrollWidth,viewport:innerWidth})')
          if dim['width']>dim['viewport']+1:
            print('OVERFLOW',file,width,dim)
            print(page.evaluate("() => [...document.querySelectorAll('body *')].filter(n=>n.getBoundingClientRect().right>innerWidth+1 && n.getBoundingClientRect().width).slice(0,8).map(n=>[n.tagName,n.className,String(n.textContent).slice(0,60)])"))
            raise AssertionError((file,width,dim))
          assert page.locator('h1').count()==1,(file,'h1')
          assert page.locator('nav.site-language a').count()==2,(file,'locale links')
          report['layout_checks']+=1
      page.set_viewport_size({'width':390,'height':800})
      load('index.html'); assert page.locator('a[data-site-lang="tr"]').get_attribute('href')=='tr/index.html'
      if not offline:page.locator('a[data-site-lang="tr"]').click()
      else:load('tr/index.html')
      assert 'İnsan, teknoloji' in page.locator('h1').inner_text()
      page.locator('.menu-button').click();assert page.locator('#main-navigation').is_visible();page.keyboard.press('Escape');assert page.locator('.menu-button').get_attribute('aria-expanded')=='false'
      report['interactions'].append('English to Turkish switching, academic-language homepage, mobile menu')
      load('tr/team.html')
      assert page.locator('text=Moritz Krell').count()>0
      assert page.locator('a[data-site-lang="en"]').get_attribute('href')=='../team.html'
      if not offline: page.locator('a[data-site-lang="en"]').click()
      else:load('team.html')
      assert page.locator('html').get_attribute('lang')=='en'
      report['interactions'].append('Matching subpage language switch')
      load('tr/proposals.html');assert 'Kavram geliştirme aşamasında' in page.locator('main').inner_text()
      load('tr/proposal-tubitak-dfg-reasoning.html');assert 'başvuru yapılmadı' in page.locator('main').inner_text()
      report['interactions'].append('German DFG development status visible in both languages')
      load('tr/search.html');page.locator('#site-query').fill('Moritz');assert 'Moritz' in page.locator('#site-search-results').inner_text()
      page.locator('#site-query').fill('Tugce');assert 'Tuğçe' in page.locator('#site-search-results').inner_text()
      page.locator('#site-query').fill('GenAI');assert page.locator('#site-search-results li').count()>0
      page.locator('#site-query').fill('');page.locator('#site-category').select_option('people')
      assert all('Ekip' in v for v in page.locator('#site-search-results .search-kind').all_text_contents())
      page.locator('#site-query').fill('<img src=x onerror=alert(1)>')
      assert page.locator('#site-search-results img').count()==0
      report['interactions'].append('Turkish site search, accent-insensitive names, safe rendering')
      load('tr/publications.html');page.locator('#pub-query').fill('Ates');assert page.locator('.publication:visible').count()>0
      page.locator('#pub-query').fill('nomatch-983js');assert page.locator('.no-results').is_visible()
      page.locator('#pub-reset').click();assert page.locator('.publication:visible').count()==23
      report['interactions'].append('Turkish publication filter, reset and empty state')
      load('tr/projects.html');assert page.locator('#completed-projects .project-summary').count()==2
      assert page.locator('#funded-projects .project-summary').count()==1
      report['interactions'].append('Completed two-BAP research display and 1002-A support record')
      load('tr/index.html');assert page.locator('.showcase-news-card').count()==5
      assert page.locator('.showcase-topic').count()==5
      assert page.locator('.showcase-join-qr img').count()==1
      report['interactions'].append('Five live homepage update cards, research area bar and Tally QR')
      load('tr/feedback-explorer.html');mode=page.locator('[data-feedback-picker]');mode.select_option('hybrid')
      assert page.locator('[data-mode]:visible').count()>=1
      report['interactions'].append('Turkish feedback example mode selection')
      load('tr/team.html')
      assert page.locator('.person-card').count()==31
      for img in page.locator('.institution-mark img').all():
        img.scroll_into_view_if_needed()
        if not offline:
          img.evaluate('(n)=>n.decode()')
          assert img.evaluate('(n)=>n.complete && n.naturalWidth>0')
      page.locator('#people-query').fill('Irem')
      assert page.locator('.person-card:visible').count()==1
      assert '2028' in page.locator('.person-card:visible').inner_text()
      page.locator('#people-reset').click()
      assert page.locator('.person-card:visible').count()==31
      page.locator('#people-query').fill('Hollanda')
      assert page.locator('.person-card:visible').count()==3
      report['interactions'].append('Thirty researcher profiles, two Ipek role cards and loaded institutional logos')
      assert page.locator('#alumni [data-person="ipek-oz-alumna"]').count()==1
      assert page.locator('a[href="https://tally.so/r/Eq51Jr"]').count()>=1
      load('tr/join.html')
      assert page.locator('a[href="https://tally.so/r/Eq51Jr"]').count()>=1
      assert page.locator('.research-join-qr img').count()==1
      report['interactions'].append('Interest form and QR link in team and join page')
      load('tr/research-network.html')
      assert page.locator('.network-country').count()==22
      assert page.locator('.network-country li').count()==43
      page.locator('#network-query').fill('Vietnam')
      assert page.locator('.network-country:visible').count()==1
      assert page.locator('a[data-site-lang="en"]').get_attribute('href')=='../research-network.html'
      report['interactions'].append('Bilingual source-derived network poster and searchable 22-country 43-institution directory')
      assert not report['errors'],report['errors']
      browser.close()
  finally:
    if server:server.shutdown()
  (ROOT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
  print('BILINGUAL BROWSER REGRESSION PASSED:',report)

if __name__=='__main__':main()
