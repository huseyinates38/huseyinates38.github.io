#!/usr/bin/env python3
"""Responsive regression test for the explicit record-review pass."""
from pathlib import Path
import base64, functools, http.server, json, mimetypes, re, shutil, sys, threading
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as Soup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
OFFLINE = '--offline' in sys.argv

@functools.lru_cache(maxsize=None)
def inline(name):
    source = SITE / name
    s = Soup(source.read_text(encoding='utf-8'), 'html.parser')
    for tag in list(s.select('link[rel="stylesheet"]')):
        target = (source.parent / urlsplit(tag['href']).path).resolve()
        if target.is_file():
            style = s.new_tag('style'); style.string = target.read_text(); tag.replace_with(style)
        else:
            tag.decompose()
    for tag in list(s.select('script[src]')):
        target = (source.parent / urlsplit(tag['src']).path).resolve()
        if target.is_file():
            del tag['src']; tag.string = target.read_text()
        else:
            tag.decompose()
    for tag in s.select('img[src]'):
        target = (source.parent / urlsplit(tag['src']).path).resolve()
        if target.is_file():
            mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            tag['src'] = 'data:' + mime + ';base64,' + base64.b64encode(target.read_bytes()).decode()
    return str(s)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(SITE)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    report = {'layout_checks': 0, 'record_checks': 0, 'errors': []}
    names = ['index.html', 'about.html', 'proposals.html', 'team.html',
             'person-gokhan-ince.html', 'person-serbay-durmaz.html',
             'person-ipek-oz.html', 'person-kibar-gul.html', 'project-robot-virtual-agent.html']
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'), args=['--no-sandbox'])
            page = browser.new_page(reduced_motion='reduce')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            for width in (390, 768, 1440):
                page.set_viewport_size({'width': width, 'height': 950})
                for pre in ('', 'tr/'):
                    for name in names:
                        if OFFLINE:
                            page.set_content(inline(pre + name), wait_until='load')
                        else:
                            page.goto(base + pre + name, wait_until='domcontentloaded')
                        page.evaluate('document.querySelectorAll("img").forEach(img => img.loading = "eager")')
                        page.evaluate('async () => { await Promise.all([...document.images].map(img => img.decode().catch(() => null))); }')
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (pre, name, width)
                        assert page.locator('h1').count() == 1
                        report['layout_checks'] += 1
                        if name == 'about.html':
                            assert page.locator('[data-record-date="page"] time').get_attribute('datetime') == '2026-11-14'
                            assert page.locator('[data-record-date="cv"] time').get_attribute('datetime') == '2026-11-13'
                        if name == 'proposals.html':
                            assert page.locator('.pipeline-card [data-record-date] time').count() == 7
                        if name.startswith('person-'):
                            assert page.locator('[data-project-record="study"] a').count() == 1
                            assert page.locator('[data-project-record="stage"]').count() == 1
                        if name == 'team.html':
                            for key in ('surrey', 'twente'):
                                logo = page.locator(f'.institution-mark.dark img[alt*="{key.title()}"]').first
                                assert logo.evaluate('(img) => img.complete && img.naturalWidth > 0')
                                assert logo.evaluate('(img) => getComputedStyle(img.parentElement).backgroundColor') == 'rgb(23, 55, 70)'
                            assert page.locator('#project-team-3501 .person-card').count() == 6
                            assert page.locator('#project-team-aub-stem .person-card').count() == 3
                        report['record_checks'] += 1
            browser.close()
    finally:
        server.shutdown()
    assert not report['errors'], report['errors']
    report['result'] = 'passed'
    (ROOT / 'record-review-browser-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
