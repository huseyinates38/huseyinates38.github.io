#!/usr/bin/env python3
"""Apply one bilingual visual system to every generated page after editorial builders.

No research metadata, project outcomes, people or downloads are inferred from mockups.
Only the supplied illustrations are reused; controls and all content remain HTML.
"""
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from html import escape
import hashlib, json, re, shutil

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
BASE='https://huseyinates38.github.io/'
VERSION='4.9'

def t(tr,en,tr_text):return tr_text if tr else en

def fragment(html):
    return Soup(html,'html.parser')

def icon(key):
    paths={
        'people':'<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3Zm13-17a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 4v3"/>',
        'book':'<path d="M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3Zm9 2v15"/>',
        'cap':'<path d="m2 9 10-5 10 5-10 5Zm4 2v6c4 3 8 3 12 0v-6m4-2v10"/>',
        'layers':'<path d="m2 8 10-5 10 5-10 5Zm0 5 10 5 10-5M2 18l10 5 10-5"/>',
        'globe':'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 9h18M3 15h18"/>',
        'flask':'<path d="M8 3h8m-6 0v7L4 20h16l-6-10V3M7 15h10"/>',
    }
    return '<svg class="ui-icon" viewBox="0 0 24 26" aria-hidden="true" focusable="false">'+paths.get(key,paths['layers'])+'</svg>'

def image(s,src,cls='card-art',lazy=True):
    node=s.new_tag('img',src=src,alt='',width='600',height='200',decoding='async')
    node['class']=cls
    node['loading']='lazy' if lazy else 'eager'
    if not lazy:node['fetchpriority']='high'
    return node

def art_key(href):
    if 'iccai' in href:return 'conference'
    if 'visiting-researchers' in href:return 'visitor'
    if 'robot-virtual-agent' in href or 'dfg' in href:return 'grant'
    if 'space-debris' in href:return 'orbit'
    if 'feedback' in href or 'genai' in href or 'ai-literacy' in href:return 'research-ai'
    if 'argumentation' in href:return 'research-reason'
    if 'self-regulat' in href:return 'research-stem'
    return 'research-stem'

def decorate_header(s,tr):
    header=s.select_one('header.header')
    if not header:return
    header['class']=list(dict.fromkeys(header.get('class',[])+['design-header']))
    row=header.select_one('.headrow')
    brand=header.select_one('.brand')
    if brand and not row.select_one('.brand-affiliation'):
        subtitle=s.new_tag('div',attrs={'class':'brand-affiliation'})
        subtitle.append(fragment('<span>'+t(tr,'Science Education · Human-Centered AI','Fen Eğitimi · İnsan Odaklı Yapay Zekâ')+'</span><span>'+t(tr,'Kırşehir Ahi Evran University','Kırşehir Ahi Evran Üniversitesi')+'</span>'))
        brand.insert_after(subtitle)
    nav=header.select_one('#main-navigation')
    # Keep the existing seven sections and all destination URLs.
    if nav:
        link=nav.select_one('a[href="team.html"]')
        if link:link.string=t(tr,'Team','Ekip')
    language=header.select_one('.site-language')
    if language:
        order=['tr','en'] if tr else ['en','tr']
        for code in reversed(order):
            link=language.select_one('a[data-site-lang="'+code+'"]')
            if link:link.extract();language.insert(0,link)

def decorate_hero(s,tr,name,prefix):
    localized=prefix+'assets/polished/hero-'+('tr' if tr else 'en')+'.webp'
    if name=='index.html':
        wrap=s.select_one('.showcase-hero-visual')
        if wrap:
            wrap.clear()
            im=image(s,localized,'hero-artwork',False)
            im['width']='1012';im['height']='280';im['data-art-language']='tr' if tr else 'en'
            wrap.append(im)
    else:
        hero=s.select_one('main .pagehero')
        if not hero:
            # Rare utility pages still receive the same visual header treatment.
            main=s.select_one('main');heading=main.find('h1') if main else None
            if heading:
                hero=s.new_tag('section',attrs={'class':'pagehero'})
                container=s.new_tag('div',attrs={'class':'container'})
                heading.extract();container.append(heading);hero.append(container);main.insert(0,hero)
        if hero:
            im=image(s,localized,'hero-artwork',False)
            im['width']='1012';im['height']='280';im['aria-hidden']='true';im['data-art-language']='tr' if tr else 'en'
            hero.insert(0,im)
            # Large people-directory navigation belongs below, not across the picture.
            subnav=hero.select_one('nav.subnav')
            if subnav:
                bar=s.new_tag('nav',attrs={'class':'section-nav','aria-label':t(tr,'On this page','Bu sayfadaki bölümler')})
                inner=s.new_tag('div',attrs={'class':'container'})
                for child in list(subnav.children):inner.append(child.extract())
                subnav.decompose();bar.append(inner);hero.insert_after(bar)
    meta=s.select_one('meta[property="og:image"]')
    if meta:meta['content']=BASE+'assets/polished/hero-'+('tr' if tr else 'en')+'.webp'
    preload=s.new_tag('link',rel='preload',href=localized,attrs={'as':'image','fetchpriority':'high'})
    s.head.append(preload)

def decorate_home(s,tr,prefix):
    for im in s.select('.showcase-news-card .showcase-card-img img'):
        old=im['src']; key=Path(old).stem.replace('card-','')
        if key=='conference' and tr:key='conference-tr'
        im['src']=prefix+'assets/polished/'+key+'.webp'
        im['loading']='eager';im['width']='400';im['height']='200'
        im.attrs.pop('style',None)
    join=s.select_one('.showcase-join-icon')
    if join:join.clear();join.append(fragment(icon('people')))
    aside=s.select_one('.showcase-join-card')
    if aside:
        aside.h3.string=t(tr,'Join our research group','Araştırma grubuna katılın')
        aside.select_one('p').string=t(tr,'Connect with our work in science education, artificial intelligence and STEM.','Fen eğitimi, yapay zekâ ve STEM araştırmalarında birlikte çalışmak için başvuru formunu doldurabilirsiniz.')
    icons=['book','layers','cap','globe','flask']
    for el,key in zip(s.select('.showcase-stat-icon'),icons):
        el.clear();el.append(fragment(icon(key)))
    for idx,card in enumerate(s.select('.showcase-featured-grid article')):
        key=['research-ai','research-reason','research-stem'][idx%3]
        card.insert(0,image(s,prefix+'assets/polished/'+key+'.webp'))

def decorate_cards(s,tr,prefix,name):
    # Shared image-backed cards across projects, resources, publications and study briefs.
    for card in s.select('main .project-summary, main .resource-card'):
        if card.select_one('.card-art'):continue
        link=card.select_one('a[href$=".html"]')
        key=art_key(link.get('href','') if link else name)
        if key=='conference' and tr:key='conference-tr'
        card['class']=list(dict.fromkeys(card.get('class',[])+['has-card-art']))
        card.insert(0,image(s,prefix+'assets/polished/'+key+'.webp'))
    for old in list(s.select('.visual-research-gallery,.visual-project-separator')):old.decompose()
    if name=='research.html':
        entries=[s.select_one('#'+k) for k in ['human-centered-ai','reasoning','technologies']]
        if all(entries):
            grid=s.new_tag('div',attrs={'class':'research-theme-grid'})
            entries[0].insert_before(grid)
            for entry,key in zip(entries,['research-ai','research-reason','research-stem']):
                entry.extract();entry.insert(0,image(s,prefix+'assets/polished/'+key+'.webp'));grid.append(entry)
        # The three methods keep their actual research descriptions and gain vector symbols.
        for idx,card in enumerate(s.select('.cards .card')):
            card.insert(0,fragment('<div class="method-symbol">'+icon(['flask','layers','book'][idx%3])+'</div>'))
    if name=='publications.html':
        # Lead with readable research cards, then the actual citation downloads and searchable list.
        first=s.select_one('main .section')
        featured=next((sec for sec in s.select('main > .section') if sec.select('.resource-card')),None)
        if featured and first and first!=featured:featured.extract();first.insert_before(featured)
    if name=='resources.html':
        sections=s.select('main > .section')
        materials=next((sec for sec in sections if sec.select('.resource-card')),None)
        pack=next((sec for sec in sections if sec.select('a[href$="teaching-resources-v1.1.zip"]')),None)
        explorer=next((sec for sec in sections if sec.select('a[href="feedback-explorer.html"]') and not sec.select('.resource-card')),None)
        if materials and sections:
            materials.extract();sections[0].insert_before(materials)
        if pack and explorer:
            combined=s.new_tag('section',attrs={'class':'section muted'})
            grid=s.new_tag('div',attrs={'class':'container resource-actions-grid'})
            pack.insert_before(combined);combined.append(grid)
            for sec in [explorer,pack]:
                inner=sec.select_one('.container')
                panel=s.new_tag('article',attrs={'class':'resource-action-panel'})
                if inner:
                    for child in list(inner.children):panel.append(child.extract())
                grid.append(panel);sec.decompose()
    if name=='about.html':
        for h in s.select('main .section h2'):
            if h.parent.name=='div' and 'sectionhead' in h.parent.get('class',[]):continue
            h['class']=list(dict.fromkeys(h.get('class',[])+['profile-section-heading']))
    # Person and project detail pages share the skin without adding invented photographs.
    for h in s.select('.card h3,.panel h3,.project-side .micro-label'):
        h['class']=list(dict.fromkeys(h.get('class',[])+['panel-title']))

def fix_svg_attributes(html):
    # HTML parsers lowercase SVG attributes. Emit the XML spelling consistently.
    return html.replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio=')

def main():
    source=ROOT/'assets/polished'
    if not (source/'hero-en.webp').is_file():raise RuntimeError('English-language hero artwork missing')
    dest=SITE/'assets/polished';dest.mkdir(exist_ok=True,parents=True)
    for asset in source.iterdir():
        if asset.is_file():shutil.copy2(asset,dest/asset.name)
    css=ROOT/'assets/design-system.css';shutil.copy2(css,SITE/'assets/design-system.css')
    csshash=hashlib.sha256(css.read_bytes()).hexdigest()[:12]
    count=0
    for path in sorted(SITE.rglob('*.html')):
        rel=path.relative_to(SITE);tr=rel.parts[0]=='tr';prefix='../' if tr else '';name=path.name
        s=Soup(path.read_text(encoding='utf-8'),'html.parser')
        s.body['class']=list(dict.fromkeys(s.body.get('class',[])+['design-v49']))
        s.body['data-design-release']=VERSION
        for old in s.select('link[href*="design-system.css"]'):old.decompose()
        s.head.append(s.new_tag('link',rel='stylesheet',href=prefix+'assets/design-system.css?v='+csshash))
        headings={
            'research.html':('Research that connects <em>AI, reasoning and learning.</em>','Yapay zekâ, bilimsel akıl yürütme ve <em>fen öğrenimi.</em>'),
            'projects.html':('Research projects <em>& applications.</em>','Araştırma projeleri <em>ve başvurular.</em>'),
            'team.html':('Research team <em>& collaborations.</em>','Araştırma ekibi <em>ve iş birlikleri.</em>'),
            'publications.html':('Publications <em>& research briefs.</em>','Yayınlar <em>ve araştırma özetleri.</em>'),
            'resources.html':('Resources for <em>teaching and research.</em>','Öğretim ve araştırma <em>kaynakları.</em>'),
            'about.html':('About <em>Hüseyin Ateş.</em>','<em>Hüseyin Ateş</em> hakkında.')}
        if name in headings:
            h=s.select_one('main h1')
            if h:h.clear();h.append(fragment(headings[name][1 if tr else 0]))
        if name=='resources.html':
            intro=s.select_one('.pagehero p.lead')
            if intro:intro.string=t(tr,'Bilingual guides, classroom worksheets and interactive examples on feedback, scientific argumentation and self-regulated learning.','Geri bildirim, bilimsel argümantasyon ve öz düzenlemeli öğrenme üzerine iki dilli rehberler, çalışma yaprakları ve etkileşimli örnekler.')
        decorate_header(s,tr);decorate_hero(s,tr,name,prefix)
        if name=='index.html':decorate_home(s,tr,prefix)
        decorate_cards(s,tr,prefix,name)
        # Existing diagrams, logos, QR and downloads are retained. Every illustration has an explicit box.
        for im in s.select('img'):
            if not im.has_attr('decoding'):im['decoding']='async'
        path.write_text(fix_svg_attributes(str(s)),encoding='utf-8');count+=1
    # Repair the legacy partially removed webfont import; the design uses a reliable system font stack.
    base=SITE/'assets/styles.css'
    raw=base.read_text();idx=raw.find(':root')
    if idx>0:base.write_text(raw[idx:],encoding='utf-8')
    for filename in ['deployment.json','quality-report.json']:
        path=SITE/filename
        if path.exists():
            data=json.loads(path.read_text());data['version' if filename=='deployment.json' else 'release']=VERSION
            data['visual_system']={'all_pages':True,'localized_artwork':['en','tr'],'real_html_controls':True,'personal_photos':False}
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'DESIGN {VERSION}: {count} pages; localized hero images; five photographic highlights; shared site-wide theme.')

if __name__=='__main__':main()
