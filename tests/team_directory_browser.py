#!/usr/bin/env python3
"""Focused browser and content regressions for approved team-directory updates."""
from pathlib import Path
import functools,http.server,threading,json,shutil
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
from docx import Document
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'
def main():
 data=json.loads((ROOT/'content/team-directory.json').read_text())
 assert len(data['network'])==22 and sum(len(row[1]) for row in data['network'])==43
 for loc in ('','tr/'):
  s=Soup((SITE/loc/'team.html').read_text(),'html.parser')
  assert len(s.select('.person-card'))==30
  assert [x.get('data-person') for x in s.select('#project-contributors .person-card')]==['serbay-durmaz','yesim-taktat-ates','ipek-oz','ibrahim-delen']
  assert len(s.select('#graduate-researchers .person-card'))==5
  assert len(s.select('#collaborators .person-card'))==12
  assert not s.select('[data-person="yesim-taktat-ates"] .institution-mark')
  assert s.select_one('[data-person="ipek-oz"] img[src$="meb.png"]')
  for key in ['macedonia','crete']:assert s.select_one('[data-person="georgios-lampropoulos"] img[src$="'+key+'.png"]')
  for person in data['new_people']:
   profile=Soup((SITE/loc/('person-'+person['slug']+'.html')).read_text(),'html.parser')
   assert person['name'] in profile.main.get_text()
  for slug in ['irem-sude-koksal','furkan-ensar-ates']:
   assert '2028' in s.select_one('[data-person="'+slug+'"]').get_text()
 for name in ['Huseyin_Ates_Public_Academic_CV','Huseyin_Ates_Akademik_Ozgecmis_TR']:
  cv=' '.join(x.text for x in Document(SITE/'downloads'/(name+'.docx')).paragraphs)
  assert 'İrem Sude Köksal' in cv and 'Furkan Ensar Ateş' in cv
  assert (SITE/'downloads'/(name+'.pdf')).stat().st_size>20000
 assert len(list((SITE/'assets/institutions').glob('*.png')))==20
 for lang in ('en','tr'):
  assert (SITE/f'assets/network/research-network-{lang}.svg').stat().st_size>20000
  assert (SITE/f'downloads/research-network-{lang}.pdf').stat().st_size>20000
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 report={'release':'4.3','people':30,'countries':22,'institutions':43,'images_loaded':0,'tests':[],'errors':[]}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':390,'height':850});page.on('pageerror',lambda e:report['errors'].append(str(e)))
   for loc in ('','tr/'):
    page.goto(base+loc+'team.html',wait_until='domcontentloaded')
    for img in page.locator('.institution-mark img').all():
     img.scroll_into_view_if_needed();img.evaluate('(n)=>n.decode()');assert img.evaluate('(n)=>n.naturalWidth>0');report['images_loaded']+=1
     assert img.bounding_box()['height']<=55
    page.locator('#people-query').fill('Irem');assert page.locator('.person-card:visible').count()==1
    assert '2028' in page.locator('.person-card:visible').inner_text()
    page.locator('#people-reset').click();assert page.locator('.person-card:visible').count()==30
    page.locator('#people-query').fill('Hollanda' if loc else 'Netherlands');assert page.locator('.person-card:visible').count()==3
    page.goto(base+loc+'research-network.html',wait_until='domcontentloaded')
    poster=page.locator('.network-preview img');poster.scroll_into_view_if_needed();poster.evaluate('(n)=>n.decode()');assert poster.evaluate('(n)=>n.naturalWidth>0')
    assert page.locator('.network-country').count()==22 and page.locator('.network-country li').count()==43
    page.locator('#network-query').fill('Vietnam');assert page.locator('.network-country:visible').count()==1
    assert page.locator('nav.site-language a').count()==2
    report['tests'].append(('Turkish' if loc else 'English')+' names, ordered cards, logo loading, researcher and country filters, poster rendering')
   assert not report['errors'];browser.close()
 finally:server.shutdown()
 (ROOT/'team-directory-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('TEAM DIRECTORY REGRESSIONS PASSED',report)
if __name__=='__main__':main()
