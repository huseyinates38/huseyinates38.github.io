#!/usr/bin/env python3
"""Validate generated files and verify the exact live release after deployment."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]/'_site'
class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=set(); self.duplicates=[]; self.h1=0; self.lang=None; self.title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if tag=='title': self.title=True
        if a.get('id'):
            if a['id'] in self.ids:self.duplicates.append(a['id'])
            self.ids.add(a['id'])
        for key in ('src','href'):
            if a.get(key):self.links.append(a[key])

def validate():
    manifest=json.loads((ROOT/'deployment.json').read_text())
    parsed={}; errors=[]
    for name in manifest['pages']:
        document=Document(); text=(ROOT/name).read_text(encoding='utf-8');document.feed(text);parsed[name]=document
        if document.h1!=1 or not document.title or document.lang!='en':errors.append(name+': heading/title/language check')
        if document.duplicates:errors.append(name+': duplicate IDs '+str(document.duplicates))
        if 'id="main-content"' not in text or 'href="team.html"' not in text or 'href="resources.html"' not in text:errors.append(name+': missing navigation or main landmark')
    for name,document in parsed.items():
        for ref in document.links:
            u=urlsplit(ref)
            if u.scheme or u.netloc:continue
            target=(ROOT / (unquote(u.path).lstrip('/') or name)).resolve()
            if target.is_dir():target=target/'index.html'
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():errors.append(name+': missing '+ref);continue
            relative=target.relative_to(ROOT).as_posix()
            if u.fragment and relative in parsed and unquote(u.fragment) not in parsed[relative].ids:errors.append(name+': missing anchor '+ref)
    if errors:raise SystemExit('\n'.join(errors))
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='deployment.json' and not p.name.startswith('.')}
    manifest['files']=files
    (ROOT/'deployment.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'VALIDATED {len(parsed)} HTML pages, {len(manifest["downloads"])} downloads and {len(files)} published files.')

def live():
    expected=json.loads((ROOT/'deployment.json').read_text())
    base=os.environ.get('SITE_URL','https://huseyinates38.github.io/').rstrip('/')+'/'
    revision=expected['commit']
    def fetch(name):
        request=Request(base+name+'?release='+revision,headers={'Cache-Control':'no-cache','User-Agent':'Academic-Site-Release-Check/2.0'})
        with urlopen(request,timeout=20) as response:
            if response.status!=200:raise RuntimeError(f'HTTP {response.status}: {name}')
            return response.read()
    def check(item):
        name,digest=item
        for attempt in range(4):
            try:
                data=fetch(name)
                if hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Content mismatch: '+name)
                return name
            except Exception:
                if attempt==3:raise
                time.sleep(4)
    for attempt in range(6):
        try:
            actual=json.loads(fetch('deployment.json'))
            if actual['commit']!=revision:raise RuntimeError('Older release is still being served')
            break
        except Exception:
            if attempt==5:raise
            time.sleep(5)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(check,expected['files'].items()):print('VERIFIED HTTP 200 + SHA256:',name)
    print('VERIFIED RELEASE:',revision)
    print('LIVE SITE:',base)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
            summary.write(f'## Website v2 published and verified\n\n{base}\n\n{expected["page_count"]} HTML pages; {len(expected["downloads"])} downloads.\n\nEvery published file returned HTTP 200 and matched its release checksum.\n\nCommit: `{revision}`\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    live() if args.live else validate()
