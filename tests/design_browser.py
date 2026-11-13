#!/usr/bin/env python3
"""Rendered image, layout and locale checks, in addition to interaction regressions."""
from pathlib import Path
from urllib.parse import urlsplit
import base64,functools,http.server,json,mimetypes,re,shutil,sys,threading
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site'
OFFLINE='--offline' in sys.argv
CACHE={}
def uri(p):
    return 'data:'+(mimetypes.guess_type(str(p))[0] or 'application/octet-stream')+';base64,'+base64.b64encode(p.read_bytes()).decode()
def inline(name):
    if name in CACHE:return CACHE[name]
    src=SITE/name;s=Soup(src.read_text(),'html.parser')
    for n in list(s.select('link[rel=stylesheet]')):
        p=(src.parent/urlsplit(n['href']).path).resolve()
        if not p.is_file():n.decompose();continue
        css=p.read_text()
        def replace(m):
            v=m[1];q=(p.parent/urlsplit(v).path).resolve()
            return 'url("'+uri(q)+'")' if not urlsplit(v).scheme and q.is_file() else m[0]
        css=re.sub(r'url\([\'"]?([^\)\'"\s]+)[\'"]?\)',replace,css)
        st=s.new_tag('style');st.string=css;n.replace_with(st)
    for n in s.select('img[src]'):
        p=(src.parent/urlsplit(n['src']).path).resolve()
        if p.is_file():n['src']=uri(p);n['loading']='eager'
    for n in list(s.select('script[src],link[rel=preload],link[rel=preconnect]')):n.decompose()
    CACHE[name]=str(s);return CACHE[name]
def main():
    report={'version':'4.9','offline':OFFLINE,'pages':0,'layout_checks':0,'image_checks':0,'locale_checks':0,'errors':[]}
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
    server=None
    if not OFFLINE:
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(SITE)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}/'
    previews=ROOT/'design-previews';previews.mkdir(exist_ok=True)
    main_pages={'index.html','research.html','projects.html','team.html','publications.html','resources.html','about.html'}
    pages=sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html'));report['pages']=len(pages)
    assert len(pages)==138
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1600,'height':1080},reduced_motion='reduce')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            for width in [390,1024,1600]:
                page.set_viewport_size({'width':width,'height':1080 if width>=1024 else 844})
                for name in pages:
                    path=SITE/name;src=Soup(path.read_text(),'html.parser');lang='tr' if name.startswith('tr/') else 'en'
                    assert src.body.get('data-design-release')=='4.9'
                    assert src.select_one('link[href*="design-system.css"]')
                    hero=src.select_one('img.hero-artwork')
                    assert hero and hero['src'].endswith('hero-'+lang+'.webp'),name
                    assert hero['data-art-language']==lang
                    report['locale_checks']+=1
                    if OFFLINE:page.set_content(inline(name),wait_until='load')
                    else:page.goto(base+name,wait_until='domcontentloaded')
                    page.evaluate('document.querySelectorAll("img").forEach(i=>i.loading="eager")')
                    images=page.evaluate('''async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)));return [...document.images].map(i=>({ok:i.complete&&i.naturalWidth>0,w:i.getBoundingClientRect().width,h:i.getBoundingClientRect().height,src:i.currentSrc}))}''')
                    assert all(i['ok'] for i in images),(name,width,[i['src'] for i in images if not i['ok']])
                    report['image_checks']+=len(images)
                    dims=page.evaluate('({w:innerWidth,sw:document.documentElement.scrollWidth})')
                    assert dims['sw']<=width+1,(name,width,dims)
                    assert page.locator('h1').count()==1,name
                    assert page.locator('body.design-v49').count()==1
                    assert len(src.select('nav.site-language a'))==2
                    if Path(name).name=='index.html':
                        pics=page.locator('.showcase-news-card .showcase-card-img img')
                        assert pics.count()==5,name
                        for im in pics.all():
                            box=im.bounding_box();assert box and box['width']>100 and box['height']>90,(name,box)
                    report['layout_checks']+=1
                    if width in [390,1600] and Path(name).name in main_pages:
                        page.screenshot(path=str(previews/(name.replace('/','-').replace('.html','')+f'-{width}.png')),full_page=False)
            assert not report['errors'],report['errors']
            browser.close()
    finally:
        if server:server.shutdown()
    (ROOT/'design-browser-report.json').write_text(json.dumps(report,indent=2))
    print('DESIGN SYSTEM CHECKS PASSED:',json.dumps(report))
if __name__=='__main__':main()
