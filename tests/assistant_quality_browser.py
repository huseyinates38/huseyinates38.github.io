#!/usr/bin/env python3
"""Check actual public-record answers, not model/mock prose or subjective fluency.
No model downloads, API credentials, external requests or real-LLM quality claims.
"""
from pathlib import Path
import functools,http.server,threading,json,shutil,sys,base64,mimetypes
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'; OFFLINE='--offline' in sys.argv

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
    threading.Thread(target=server.serve_forever,daemon=True).start()
    report={'answer_checks':0,'responsive_checks':0,'errors':[],'scope':'Deterministic public-record answers; no real-model generation tested'}
    previews=ROOT/'assistant-quality-previews';previews.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
            page=browser.new_page(reduced_motion='reduce')
            page.on('pageerror',lambda error:report['errors'].append(str(error)))
            remote=[]
            page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(f'http://127.0.0.1:{server.server_port}/') else (remote.append(route.request.url),route.abort())[-1])
            for width in (390,768,1440):
                page.set_viewport_size({'width':width,'height':950})
                for pre in ('tr/',''):
                    tr=bool(pre)
                    if OFFLINE:page.set_content(inline(pre+'assistant.html'),wait_until='load')
                    else:page.goto(f'http://127.0.0.1:{server.server_port}/{pre}assistant.html',wait_until='networkidle')
                    def ask(q):
                        page.locator('#chat-question').fill(q);page.locator('#chat-send').click()
                        report['answer_checks']+=1
                        answer=page.locator('.chat-assistant').last
                        assert answer.locator('.chat-message-text').inner_text().strip(),q
                        return answer
                    def clear():page.locator('#chat-clear').click()
                    a=ask('3501 ekibinde kimler var?' if tr else 'Who is on the 3501 team?')
                    names=['Gökhan İnce','Zeynep Aydemir','Ahmet Salih Şimşek','Serbay Durmaz','İpek Öz','İbrahim Delen','Yeşim Taktat Ateş']
                    assert all(n in a.inner_text() for n in names),a.inner_text()
                    assert ('karar bekleniyor' if tr else 'decision pending') in a.inner_text()
                    assert a.locator('a[href="project-robot-virtual-agent.html"]').count()==1
                    a=ask('Peki destek aldı mı?' if tr else 'What about its funding status?')
                    assert ('karar bekleniyor' if tr else 'decision pending') in a.inner_text(),a.inner_text()
                    assert ('13 Kasım 2026' if tr else '13 November 2026') in a.inner_text()
                    clear()
                    a=ask('Yesim Taktat Ates hangi projelerde?' if tr else 'Which projects involve Yesim Taktat Ates?')
                    assert '3501' in a.inner_text() and ('BAE' if tr else 'UAE') in a.inner_text(),a.inner_text()
                    assert a.locator('a[href="project-robot-virtual-agent.html"]').count()==1
                    assert a.locator('a[href="proposal-turkiye-uae-stem.html"]').count()==1
                    a=ask('Peki hangi kurumda?' if tr else 'What is her affiliation?')
                    assert ('bağımsız araştırmacı' if tr else 'independent researcher') in a.inner_text(),a.inner_text()
                    clear()
                    a=ask('Gökhan İnce teknik geliştirmeyi mi yapıyor?' if tr else 'Does Gökhan İnce do software development?')
                    assert ('belirtilmemiş' if tr else 'not specified') in a.inner_text(),a.inner_text()
                    a=ask('Gökhan hangi üniversitede?' if tr else 'Where does Gökhan work?')
                    assert ('İstanbul Teknik' if tr else 'Istanbul Technical') in a.inner_text()
                    clear()
                    a=ask('Kibar Gül katkısı nedir?' if tr else 'What is Kibar Gül’s contribution?')
                    assert 'STEM' in a.inner_text() and ('etkinlik tasarımı' if tr else 'activity design') in a.inner_text()
                    clear()
                    a=ask('AÜB ekibinde kimler var?' if tr else 'Who is on the AUB team?')
                    assert all(x in a.inner_text() for x in ('Kibar Gül','Naciye Somuncu Demir','Yeşim Taktat Ateş','Ahmet Sami Konca')),a.inner_text()
                    clear()
                    a=ask('E-posta adresiniz nedir?' if tr else 'What is his email address?')
                    assert 'huseyin.ates@ahievran.edu.tr' in a.inner_text(),a.inner_text()
                    a=ask('Nasıl iş birliği önerebilirim?' if tr else 'How can I propose a collaboration?')
                    assert a.locator('a[href="join.html"]').count()==1
                    clear()
                    a=ask('Hüseyin Ateş hangi konularda çalışıyor?' if tr else 'What does Hüseyin Ateş research?')
                    assert ('öz düzenlemeli' if tr else 'self-regulated') in a.inner_text()
                    a=ask('2026 yayınlarını göster' if tr else 'Show his 2026 publications')
                    assert '10.1186/s41239-026-00614-9' in a.inner_text()
                    clear()
                    a=ask('Ahmet hangi kurumda?' if tr else 'Which institution is Ahmet at?')
                    assert 'Ahmet Salih' in a.inner_text() and 'Ahmet Sami' in a.inner_text()
                    clear()
                    a=ask('<img src=x onerror=alert(1)> zzunknown9811')
                    assert page.locator('#chat-log img').count()==0
                    assert ('bulamadım' if tr else 'could not find') in a.inner_text(),a.inner_text()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                    if not OFFLINE:assert page.evaluate('localStorage.length')==0
                    assert page.locator('#chat-consent').is_checked() is False
                    assert page.locator('#chat-enable').is_enabled()
                    report['responsive_checks']+=1
                    if width in (390,1440) and tr:
                        clear();ask('3501 ekibinde kimler var?')
                        page.screenshot(path=str(previews/f'answer-{width}.png'),full_page=True)
            assert not any('web-llm' in x or 'huggingface' in x for x in remote),remote
            # Same answer rules must use changed input records, not fixed example strings.
            changed=page.evaluate('''()=>{const facts=JSON.parse(document.querySelector('#assistant-facts').textContent);facts.projects['3501'].stage='SENTINEL_NEW_STAGE';const corpus=JSON.parse(document.querySelector('#assistant-knowledge').textContent);const qa=AcademicAnswerEngine.create(facts,corpus);return qa.answer('3501 status').text;}''')
            assert 'SENTINEL_NEW_STAGE' in changed
            report['answer_checks']+=1
            browser.close()
    finally:server.shutdown()
    assert not report['errors'],report['errors']
    report['result']='passed';(ROOT/'assistant-quality-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
