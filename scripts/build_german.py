#!/usr/bin/env python3
"""Add German from the FINAL EN output, then connect EN/TR/DE counterparts.

No automatic translation service, private documents or build-clock review dates.
The reviewed catalog uses UTF-8 TSV files (English source / German text).
--export-catalog writes a combined JSON copy. Untranslated new prose fails the build rather than publishing
English text labelled as German. Run after all existing editorial/assistant gates.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup as Soup, Comment, Doctype

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
BASE='https://huseyinates38.github.io/'
CATALOG=ROOT/'content/german'
DATE='2026-11-16'  # Localisation edit only; never a renewed research-status review.
LOCALES=('en','tr','de')
LABELS={'en':'English','tr':'Türkçe','de':'Deutsch'}

def plain(x): return x.get_text(' ',strip=True) if x else ''
def norm(x): return re.sub(r'\s+',' ',str(x)).strip()
def key(x): return ''.join(c for c in unicodedata.normalize('NFD',x.lower().replace('ß','ss').replace('ı','i')) if unicodedata.category(c)!='Mn')
def fragment(x): return Soup(x,'html.parser')
def encode(x): return json.dumps(x,ensure_ascii=False).replace('<','\\u003c')
def filename(lang,name): return ('' if lang=='en' else lang+'/')+name
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()[:12]

def translation(s, strings, name):
    missing=set()
    heading_overrides={
        'Selected research':'Ausgewählte Forschung',
        'Supported research':'Geförderte Forschung',
        'Completed projects':'Abgeschlossene Projekte',
        'Submitted, planned & in development.':'Eingereicht, geplant und in Entwicklung.',
        'Research scope.':'Forschungsumfang.',
        'Research rationale.':'Forschungsbegründung.',
        'A shared research question.':'Eine gemeinsame Forschungsfrage.',
        'Resources for discussion.':'Materialien für den Austausch.',
        'About Hüseyin Ateş.':'Über Hüseyin Ateş.',
        "Let's connect through research.":'Über Forschung in Kontakt kommen.',
    }
    heading_nodes=[]
    for h in s.select('h1,h2,h3'):
        source=re.sub(r'\s+([.,:;])',r'\1',plain(h))
        if source in heading_overrides:heading_nodes.append((h,heading_overrides[source]))
    for n in list(s.find_all(string=True)):
        if isinstance(n,(Comment,Doctype)) or n.parent.name in ('script','style'): continue
        if n.find_parent(class_='publication') or n.find_parent(class_='citation') or n.find_parent('code') or n.find_parent('pre') or n.find_parent(class_='site-language'): continue
        value=norm(n)
        if not value or not re.search(r'[A-Za-zÀ-ž]',value): continue
        if value not in strings:
            missing.add(value); continue
        original=str(n)
        before=re.match(r'^\s*',original).group()
        after=re.search(r'\s*$',original).group()
        n.replace_with(before+strings[value]+after)
    for tag in s.select('[alt],[title],[aria-label],[placeholder],[data-chat-question]'):
        for attr in ('alt','title','aria-label','placeholder','data-chat-question'):
            if not tag.get(attr): continue
            value=norm(tag[attr])
            if value in strings: tag[attr]=strings[value]
            elif re.search(r'[A-Za-zÀ-ž]',value): missing.add(value)
    if missing: raise ValueError('German translations missing on '+name+': '+json.dumps(sorted(missing),ensure_ascii=False))
    # Original bibliographic titles/citations and source-code examples retain their language.
    for tag in s.select('.publication,.citation,pre,code'):
        tag['lang']='en'
    for tag in s.select('[data-art-language]'):tag['data-art-language']='en'
    # German sentence structure for compound headings, preserving the existing emphasis.
    for h in s.select('h1,h2,h3'):
        value=plain(h)
        repairs={
            'Über mich Hüseyin Ateş.':'Über <em>Hüseyin Ateş.</em>',
            'Forschung umfang':'<em>Forschungsumfang</em>',
            'Forschung begründung':'<em>Forschungsbegründung</em>',
            'Eine gemeinsame Forschungs- frage':'Eine gemeinsame <em>Forschungsfrage</em>',
            'Internationale Forschungs- verbindungen.':'Internationale <em>Forschungsverbindungen.</em>',
            'Geförderte Projekte':'Geförderte <em>Projekte</em>',
            'Materialien für Lehre und Forschung.':'Materialien für <em>Lehre und Forschung.</em>',
        }
        if value in repairs:h.clear();h.append(fragment(repairs[value]))
    for heading,value in heading_nodes:heading.clear();heading.append(value)
    brand=s.select_one('header .brand small')
    if brand:brand.string='NATURWISSENSCHAFTSDIDAKTIK · KI'


def local_urls(s):
    for tag in s.select('[href],[src],[poster]'):
        for attr in ('href','src','poster'):
            if not tag.get(attr):continue
            u=urlsplit(tag[attr])
            if u.scheme or u.netloc:continue
            if u.path.startswith(('assets/','downloads/','tr/','de/')):
                tag[attr]=urlunsplit(('', '', '../'+u.path,u.query,u.fragment))
    # Metadata and language-switch links are handled separately, never by blanket URL rewriting.


def language_links(s,name,lang):
    bar=s.select_one('.site-language')
    if not bar:raise ValueError('Missing language switch: '+name)
    bar.clear();bar['aria-label']={'en':'Language','tr':'Dil','de':'Sprache'}[lang]
    for dest in LOCALES:
        path=filename(dest,name)
        href=path if lang=='en' else ('../'+path if dest!=lang else name)
        a=s.new_tag('a',href=href,attrs={'lang':dest,'hreflang':dest,'data-site-lang':dest,'aria-label':LABELS[dest],'title':LABELS[dest]})
        if dest==lang:a['aria-current']='page'
        a.string=dest.upper();bar.append(a)
    for link in list(s.select('link[rel="alternate"][hreflang]')):link.decompose()
    for dest in (*LOCALES,'x-default'):
        s.head.append(s.new_tag('link',rel='alternate',hreflang=dest,href=BASE+filename('en' if dest=='x-default' else dest,name)))
    for tag in list(s.select('script[data-language-navigation]')):tag.decompose()
    pre='' if lang=='en' else '../'
    s.body.append(s.new_tag('script',src=pre+'assets/language-navigation.js?v='+digest(SITE/'assets/language-navigation.js'),defer='',attrs={'data-language-navigation':'true'}))
    for tag in list(s.select('link[data-german-layout]')):tag.decompose()
    s.head.append(s.new_tag('link',rel='stylesheet',href=pre+'assets/german.css?v='+digest(SITE/'assets/german.css'),attrs={'data-german-layout':'true'}))


def metadata(s,name,strings):
    s.html['lang']='de';s.html['data-site-language']='de'
    canonical=BASE+'de/'+name
    for n in s.select('link[rel="canonical"]'):n['href']=canonical
    intro=s.main.select_one('.lead') or s.main.find('p')
    desc=plain(intro)
    title=plain(s.title)
    for n in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):n['content']=desc
    for n in s.select('meta[property="og:title"],meta[name="twitter:title"]'):n['content']=title
    for n in s.select('meta[property="og:url"]'):n['content']=canonical
    for n in s.select('meta[property="og:locale"]'):n['content']='de_DE'
    for n in s.select('meta[property="og:image"],meta[name="twitter:image"]'):
        if n.get('content','').startswith('assets/'):n['content']=BASE+n['content']
    def walk(x):
        if isinstance(x,list):return [walk(v) for v in x]
        if not isinstance(x,dict):return x
        result={k:walk(v) for k,v in x.items()}
        for k in ('name','description','jobTitle'):
            if isinstance(result.get(k),str):result[k]=strings.get(norm(result[k]),result[k])
        if result.get('@type') in ('WebPage','ProfilePage','WebSite'):
            result['inLanguage']='de'
            if result.get('url','').startswith(BASE):result['url']=BASE+'de/'+result['url'][len(BASE):].removeprefix('de/')
        if result.get('@type')=='WebPage':result.update(url=canonical,name=plain(s.main.h1),description=desc)
        return result
    for tag in s.select('script[type="application/ld+json"]'):
        tag.string=encode(walk(json.loads(tag.string or '{}')))


def getfacts(s):
    return {plain(dt):plain(dt.find_next_sibling('dd')) for dt in s.select('dt') if dt.find_next_sibling('dd')}


def assistant_data(docs, original, strings):
    data=copy.deepcopy(original);data['lang']='de';team=docs['team.html']
    for slug,p in data['people'].items():
        s=docs[p['url']];f=getfacts(s);cards=team.select('[data-person="'+slug+'"]')
        p.update(name=plain(s.main.h1),role=f.get('Rolle') or f.get('Rolle / akademische Beziehung') or (plain(cards[0].select_one('.micro-label')) if cards else plain(s.select_one('.pagehero .eyebrow'))),
            institutions=list(dict.fromkeys(plain(n) for n in s.select('.institution-name'))),
            studies=[{'title':plain(a),'url':a['href']} for a in s.select('[data-project-record="study"] a[href]')],
            stage=f.get('Antragsstatus',f.get('Antragsstatus der Vorhaben',f.get('Aktueller Stand',''))),
            contribution=f.get('Vorgesehener Beitrag') or plain(s.select_one('[data-profile-contribution]')),
            focus=f.get('Forschungsschwerpunkt') or plain(s.select_one('.pagehero p.lead')),
            degree=f.get('Abgeschlossener Studiengang',''))
    for k,p in data['projects'].items():
        s=docs[p['url']];f=getfacts(s)
        p.update(title=plain(s.main.h1),summary=plain(s.select_one('.pagehero .lead')),
                 stage=plain(s.select_one('.pagehero .status-pill')) or strings.get(p['stage'],p['stage']),
                 reviewed=plain(s.select_one('.proposal-side time')),lead=strings.get(p.get('lead',''),p.get('lead','')),
                 duration=f.get('Vorgesehene Dauer / Aufenthalt',''))
        if k=='1002':
            note=s.select_one('#funding-decision-note p')
            if note:p['stage']=plain(note)
        group=team.select_one('#project-team-'+('aub-stem' if k=='aub' else k))
        if group:
            p['members']=[{'name':data['people'][a['data-person']]['name'],'role':plain(a.select_one('.micro-label')),'slug':a['data-person']} for a in group.select('.person-card[data-person]')]
    data['research_topics']=[plain(h) for h in docs['research.html'].select('.research-theme-grid h3')]
    data['research_intro']=plain(docs['research.html'].select_one('.pagehero .lead'))
    data['about']=plain(docs['about.html'].select_one('.pagehero p'))
    return data


def knowledge(docs):
    records=[]
    exclude={'assistant.html','search.html','404.html','accessibility.html','site-notes.html','person-tugce-unsal.html'}
    for name,s in docs.items():
        if name in exclude:continue
        for sec in s.main.select(':scope > section'):
            if sec.get('id') in ('research-interest','ai-assistant-entry'):continue
            n=copy.deepcopy(sec)
            for el in n.select('script,style,button,nav,.hero-artwork,.research-join,.buttonrow'):el.decompose()
            text=plain(n).replace('Tuğçe Ünsal','')
            if len(text)<50:continue
            sid=sec.get('id');url=name+('#'+sid if sid else '')
            # Keep complete project rosters and all shared memberships together.
            if len(text)<=7000:parts=[text]
            else:
                parts=[];part=''
                for sentence in re.split(r'(?<=[.!?])\s+',text):
                    if len(part)+len(sentence)>4500 and part:parts.append(part);part=''
                    part+=(' ' if part else '')+sentence
                if part:parts.append(part)
            for text in parts:records.append({'title':plain(s.main.h1),'url':url,'text':text})
    return {'language':'de','basis':'Öffentliche Website-Einträge; die jeweiligen Prüf- und Inhaltsdaten bleiben unverändert.','records':records}


def search_index(docs, source):
    labels={'research':'Forschung und Projekte','people':'Personen','publications':'Publikationen und Forschungsüberblicke','resources':'Materialien und Methoden','about':'Profil und Website-Informationen'}
    rows=[]
    for row in source:
        r=copy.deepcopy(row);name=r['url']
        if name in docs and name not in ('search.html','person-tugce-unsal.html'):
            m=copy.deepcopy(docs[name].main)
            for n in m.select('script,style,button,select'):n.decompose()
            r.update(title=plain(m.h1),summary=plain(m.select_one('.lead') or m.find('p')),label=labels.get(r.get('category'),'Website'))
            r['key']=key(r['title']+' '+plain(m)).replace(key('Tuğçe Ünsal'),'')
        elif name.startswith('downloads/'):
            r['url']='../'+name;r['label']='Download';r['summary']='Originaldatei · '+('Türkisch' if '-tr.' in name or '_TR.' in name else 'Englisch' if '-en.' in name or 'Huseyin_Ates_' in name else 'Englisch / Türkisch');r['key']=key(r['title']+' '+r['summary'])
        else:continue
        rows.append(r)
    docs['search.html'].select_one('#site-search-data').string=encode(rows)


def prepare_scripts(runtime):
    assets=SITE/'assets'
    # German-only copies: existing EN/TR behaviour remains unchanged.
    s=(assets/'bilingual.js').read_text()
    s=s.replace("const lang = document.documentElement.lang === 'tr' ? 'tr' : 'en';","const lang = 'de';")
    marker='    tr: {'
    if marker not in s:raise ValueError('Bilingual UI dictionary changed')
    s=s.replace(marker,"""    de: {
      selected: n => `${n} ausgewählte Publikation${n === 1 ? '' : 'en'}`,
      noPubs: 'Keine passenden Publikationen. Ändern Sie Suchbegriff oder Jahr.',
      projects: n => `${n} geförderte Projekte angezeigt`,
      matches: (n,k) => `${n} Ergebnisse · ${k} angezeigt`,
      noMatches: 'Keine Treffer. Versuchen Sie eine andere Schreibweise, einen kürzeren Begriff oder Alle Inhalte.'
    },
"""+marker,1)
    s=s.replace(".replace(/ı/g, 'i').toLowerCase()",".replace(/ı/g, 'i').replace(/ß/g,'ss').toLowerCase()")
    s=s.replace('  const aliases = {',"""  const aliases = {
    ki:['ki','ai','kunstliche intelligenz','artificial intelligence'],
    mint:['mint','stem'],
    selbstregulation:['selbstregulation','selbstreguliert','self-regulated'],
    lehrkraft:['lehrkraft','lehrkrafte','teacher'],
    lebenslauf:['lebenslauf','cv','curriculum vitae'],
    ruckmeldung:['ruckmeldung','feedback'],
""",1)
    s=s.replace("['ai','artificial intelligence','yapay zeka']","['ai','ki','kunstliche intelligenz','artificial intelligence','yapay zeka']")
    s=s.replace("['vr','virtual reality','sanal gerceklik']","['vr','virtuelle realität','virtual reality','sanal gerceklik']")
    s=s.replace("['srl','self-regulated','oz duzenleme']","['srl','selbstreguliert','self-regulated','oz duzenleme']")
    (assets/'german-controls.js').write_text(s)
    s=(assets/'team-directory.js').read_text()
    old="count.textContent=tr?`${n} / ${all.length} ${country?'ülke':'kayıt'} gösteriliyor`:`Showing ${n} of ${all.length} ${country?'countries':'entries'}`;"
    if old not in s:raise ValueError('Team counter changed')
    s=s.replace(old,"count.textContent=`${n} von ${all.length} ${country?'Ländern':'Einträgen'} angezeigt`;")
    (assets/'german-directory.js').write_text(s)
    (assets/'german-guide.js').write_bytes((ROOT/'assets/german-guide.js').read_bytes())
    s=(assets/'assistant-conversation.js').read_text()
    old="const tr=document.documentElement.lang==='tr',p=(en,t)=>tr?t:en;"
    if old not in s:raise ValueError('Conversation translation hook changed')
    s=s.replace(old,'const tr=false,DE='+encode(runtime)+',p=(en,t)=>DE[en]??en;')
    s=s.replace("lang:tr?'tr':'en'","lang:'de'")
    s=s.replace('(?:tr\\/)?','(?:(?:tr|de)\\/)?')
    s=s.replace('(merhaba|selam|hello|hi)','(hallo|guten tag|guten morgen|servus|hello|hi)')
    s=s.replace('(sen kimsin|siz kimsiniz|who are you|are you hüseyin)','(wer bist du|wer sind sie|who are you|bist du hüseyin)')
    (assets/'german-conversation.js').write_text(s)
    (assets/'language-navigation.js').write_text("""/* Preserve counterpart page and section/filter state without storing language preferences. */
(()=>{'use strict';document.querySelectorAll('[data-site-lang]').forEach(a=>a.addEventListener('click',()=>{a.href=a.getAttribute('href').split('#')[0]+location.hash;}));})();
""")
    (assets/'german.css').write_bytes((ROOT/'assets/german.css').read_bytes())


def final_js(s):
    replace={'bilingual.js':'german-controls.js','team-directory.js':'german-directory.js','academic-answer-engine.js':'german-guide.js','assistant-conversation.js':'german-conversation.js'}
    for js in s.select('script[src]'):
        name=urlsplit(js['src']).path.rsplit('/',1)[-1]
        if name in replace:
            target=replace[name];js['src']='../assets/'+target+'?v='+digest(SITE/'assets'/target)


def write(s,path):
    path.write_text(str(s).replace('viewbox=','viewBox=').replace('preserveaspectratio=','preserveAspectRatio='),encoding='utf-8')


def load_catalog():
    strings={}
    for path in sorted(CATALOG.glob('*.tsv')):
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line:continue
            source,target=line.split('\t',1)
            if source in strings and strings[source]!=target:raise ValueError('Conflicting German source: '+source)
            strings[source]=target
    return strings


def main():
    strings=load_catalog()
    if len(strings)<1200:raise ValueError('Incomplete German catalog')
    prepare_scripts(json.loads((ROOT/'content/german-runtime.json').read_text()))
    en={p.name:Soup(p.read_text(),'html.parser') for p in sorted(SITE.glob('*.html'))}
    if len(en)!=70:raise ValueError('Review German coverage for changed page count: '+str(len(en)))
    sources=json.loads(en['search.html'].select_one('#site-search-data').string)
    original_facts=json.loads(en['assistant.html'].select_one('#assistant-facts').string)
    de={}
    for name,s in en.items():
        out=copy.deepcopy(s)
        translation(out,strings,name);local_urls(out);metadata(out,name,strings);final_js(out)
        de[name]=out
    search_index(de,sources)
    chat=de['assistant.html']
    chat.select_one('#assistant-facts').string=encode(assistant_data(de,original_facts,strings))
    chat.select_one('#assistant-knowledge').string=encode(knowledge(de))
    # The deployed service currently supports EN/TR only and is inactive. Do not
    # silently send German chats to an unsupported service. Activation requires a
    # separate real-model language evaluation and an explicit supported-languages list.
    cfg=json.loads(chat.select_one('#assistant-service-config').string)
    if 'de' not in cfg.get('supported_languages',[]):cfg['endpoint']=''
    chat.select_one('#assistant-service-config').string=encode(cfg)
    if not cfg.get('endpoint'):
        chat.select_one('#cloud-enable')['disabled']=''
        chat.select_one('#cloud-state').string=strings['Server connection is not configured. Only the website guide is active.']
    folder=SITE/'de';folder.mkdir(exist_ok=True)
    # Avoid obsolete German orphan pages after a future source deletion.
    for p in folder.glob('*.html'):
        if p.name not in de:p.unlink()
    for lang in LOCALES:
        docs=en if lang=='en' else de if lang=='de' else {n:Soup((SITE/'tr'/n).read_text(),'html.parser') for n in en}
        for name,s in docs.items():
            language_links(s,name,lang)
            if lang=='en' and name=='site-notes.html':
                for node in s.main.find_all(string=True):
                    value=norm(node)
                    if value.startswith('Choose English or Türkçe in the header'):
                        node.replace_with('Choose English, Türkçe or Deutsch in the header to open the same page in another language. Each language has its own address, and internal navigation stays in the selected language. Existing English and Turkish addresses remain available.')
                    elif 'retain their original language in both site versions' in value:
                        node.replace_with(value.replace('in both site versions','in all site versions'))
            write(s,SITE/filename(lang,name))
    manifest=json.loads((SITE/'deployment.json').read_text())
    manifest.update(languages=list(LOCALES),language_pairs=len(en),language_sets=len(en),page_count=len(en)*3,
                    pages=sorted(filename(lang,n) for lang in LOCALES for n in en),german_translation_date=DATE)
    manifest.pop('files',None)
    (SITE/'deployment.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    quality=json.loads((SITE/'quality-report.json').read_text());quality.update(languages=list(LOCALES),german_pages=len(de),german_translation_date=DATE)
    (SITE/'quality-report.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
    # Preserve the existing source lastmod values. German lastmod records localisation,
    # not an updated award decision, CV or research activity.
    old=Soup((SITE/'sitemap.xml').read_text(),'xml')
    prior={plain(u.loc):plain(u.lastmod) for u in old.find_all('url') if u.loc and u.lastmod}
    rows=[]
    for name in sorted(en):
        if name in ('404.html','search.html'):continue
        alternates=''.join(f'<xhtml:link rel="alternate" hreflang="{lang}" href="{BASE+filename(lang,name)}"/>' for lang in LOCALES)
        alternates+=f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE+name}"/>'
        for lang in LOCALES:
            url=BASE+filename(lang,name);last=DATE if lang=='de' else prior.get(url,DATE)
            rows.append(f'<url><loc>{url}</loc>{alternates}<lastmod>{last}</lastmod></url>')
    (SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'+''.join(rows)+'</urlset>')
    report={'result':'built','german_pages':len(de),'total_pages':len(en)*3,'translated_catalog_entries':len(strings),'academic_review_dates_changed':False,'original_downloads_preserved':True,'cloud_activated':False}
    (ROOT/'german-build-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export-catalog',type=Path)
    args=parser.parse_args()
    if args.export_catalog:args.export_catalog.write_text(json.dumps({'locale':'de','strings':load_catalog()},ensure_ascii=False,indent=2),encoding='utf-8')
    else:main()
