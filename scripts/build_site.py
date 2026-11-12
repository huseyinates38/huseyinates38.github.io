#!/usr/bin/env python3
"""Build the research website using only Python's standard library.

Run from any directory: python scripts/build_site.py
The eleven original root HTML files remain source records. New content lives in
content/expansion.json and this presentation layer. Only _site is published.
"""
from __future__ import annotations
import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
DATA = json.loads((ROOT / 'content/expansion.json').read_text(encoding='utf-8'))
BASE = 'https://huseyinates38.github.io/'
DATE = '12 November 2026'
EMAIL = 'huseyin.ates@ahievran.edu.tr'
NAV = [('Home', 'index.html'), ('Research', 'research.html'), ('People', 'team.html'), ('Publications', 'publications.html'), ('Resources', 'resources.html'), ('Join & Collaborate', 'join.html'), ('About', 'about.html')]
PAGES: dict[str, str] = {}
esc = html.escape


def link(label: str, url: str, cls: str = 'textlink') -> str:
    download = ' download' if url.startswith('downloads/') else ''
    return f'<a class="{cls}" href="{esc(url, quote=True)}"{download}>{esc(label)} <span aria-hidden="true">↗</span></a>'


def hero(kicker: str, title: str, subtitle: str, extra: str = '') -> str:
    return f'<section class="pagehero"><div class="container"><p class="eyebrow">{esc(kicker)}</p><h1>{title}</h1><p class="lead">{subtitle}</p>{extra}</div></section>'


def section(content: str, tone: str = '', id_: str = '') -> str:
    return f'<section class="section {tone}"'+(f' id="{id_}"' if id_ else '')+f'><div class="container">{content}</div></section>'


def card(kicker: str, title: str, text: str, url: str, label: str = 'Explore') -> str:
    return f'<article class="card resource-card"><p class="eyebrow">{esc(kicker)}</p><h3>{esc(title)}</h3><p>{esc(text)}</p>{link(label,url)}</article>'


def note(text: str) -> str:
    return f'<aside class="callout">{text}</aside>'


def action(label: str, url: str, alt: bool = False) -> str:
    return link(label, url, 'btn alt' if alt else 'btn')


def render(name: str, title: str, active: str, content: str, description: str = '') -> None:
    nav = ''.join(f'<a href="{url}"'+(' aria-current="page"' if active == url else '')+f'>{esc(label)}</a>' for label,url in NAV)
    base = '<base href="/">' if name == '404.html' else ''
    robots = '<meta name="robots" content="noindex">' if name == '404.html' else ''
    person = ''
    if name == 'about.html':
        person = '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'Person','name':'Hüseyin Ateş','jobTitle':'Associate Professor of Science Education','url':BASE+'about.html','sameAs':['https://orcid.org/0000-0003-0031-8994'],'affiliation':{'@type':'Organization','name':'Kırşehir Ahi Evran University'}},ensure_ascii=False)+'</script>'
    body = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{base}{robots}
<title>{esc(title)} | Hüseyin Ateş</title><meta name="description" content="{esc(description or title,quote=True)}"><link rel="canonical" href="{BASE+name}">
<meta property="og:title" content="{esc(title,quote=True)} | Hüseyin Ateş"><meta property="og:description" content="{esc(description or title,quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE+name}">
<link rel="stylesheet" href="assets/styles.css?v=2"><link rel="stylesheet" href="assets/v2.css?v=2"><script src="assets/v2.js?v=2" defer></script>{person}</head>
<body><a class="skip-link" href="#main-content">Skip to content</a><div class="strip"><div class="container"><span>Science education · Human-centered AI</span><span>Kırşehir, Türkiye / International research</span></div></div>
<header class="header"><div class="container headrow"><a class="brand" href="index.html" aria-label="Hüseyin Ateş home"><span class="brand-symbol" aria-hidden="true">HA<span>.</span></span><span><strong>Hüseyin Ateş</strong><small>RESEARCH · RESOURCES · PEOPLE</small></span></a><button class="menu-button" type="button" aria-expanded="false" aria-controls="main-navigation">Menu <span aria-hidden="true">☰</span></button><nav class="nav" id="main-navigation" aria-label="Main navigation">{nav}</nav></div></header>
<main id="main-content">{content}</main>
<footer class="footer"><div class="container"><div class="footer-inner"><div><strong>Hüseyin Ateş</strong><p>Human-centered AI, scientific reasoning<br>and self-regulated science learning.</p></div><div class="footer-links">{link('Projects','projects.html')}{link('Research access','open-research.html')}{link('Contact','contact.html')}{link('ORCID','https://orcid.org/0000-0003-0031-8994')}</div></div><div class="footer-bottom"><span>© 2026 · Independent academic website</span><span>{link('Site & resource notes','site-notes.html')} · Updated {DATE}</span></div></div></footer></body></html>'''
    PAGES[name] = title
    (OUT / name).write_text(body, encoding='utf-8')


def original_main(name: str) -> str:
    text = (ROOT / name).read_text(encoding='utf-8')
    m = re.search(r'<main[^>]*>(.*?)</main>', text, re.S)
    if not m:
        raise ValueError('Missing main element: '+name)
    return m.group(1)


def studies_cards() -> str:
    return '<div class="cards">'+''.join(card(s['year']+' / Research brief', s['label'], s['question'], 'study-'+s['slug']+'.html','Read the brief') for s in DATA['studies'])+'</div>'


def resources_cards() -> str:
    return '<div class="cards" id="resource-cards">'+''.join(card('EN / TR · Teaching prototype',r['title'],r['short'],'resource-'+r['slug']+'.html','Open the toolkit') for r in DATA['resources'])+'</div>'


def home() -> None:
    intro = '''<section class="home-hero"><div class="container home-grid"><div><p class="eyebrow">Hüseyin Ateş / Associate Professor of Science Education</p><h1>Learning with AI.<br><em>Thinking for ourselves.</em></h1><p class="lead">How can technology support scientific reasoning without taking over the learner’s judgement? My research connects human-centered AI, feedback design and self-regulated learning.</p><div class="buttonrow">'''+action('Explore the research','research.html')+action('Use the resources','resources.html',True)+'''</div><p class="affiliation">Kırşehir Ahi Evran University · Türkiye</p></div><aside class="hero-panel"><p class="eyebrow">From research to practice</p><h2>Who does the<br><em>thinking?</em></h2><div class="process-row"><span>01</span><div><strong>Make a judgement</strong><p>Start with a claim and its evidence.</p></div></div><div class="process-row"><span>02</span><div><strong>Examine the feedback</strong><p>Compare, question and decide.</p></div></div><div class="process-row"><span>03</span><div><strong>Reason independently</strong><p>Revisit the question without the hint.</p></div></div>'''+link('Try the Feedback Design Explorer','feedback-explorer.html')+'''<p class="micro-note">An illustrative teaching tool, not a validated assessment.</p></aside></div></section>'''
    routes = '<div class="audience-grid">'+''.join(card(k,t,p,u,l) for k,t,p,u,l in [
        ('For researchers','Follow the evidence','Study briefs, methods and routes to research collaboration.','open-research.html','Explore research access'),
        ('For teachers','Bring a question to class','Bilingual planning guides and original reasoning exercises.','practice.html','Find teaching materials'),
        ('For prospective students','Find a research connection','Meet supervised researchers and explore research interests.','join.html','Explore working together')])+'</div>'
    themes = '<div class="sectionhead"><div><p class="eyebrow">Research programme</p><h2>Questions before <em>technologies.</em></h2></div>'+link('All research & projects','research.html')+'</div><div class="cards">'+''.join(card(k,t,p,u) for k,t,p,u in [
        ('01 / Feedback','Human-centered AI','How do feedback designs distribute evaluative work between learners, peers and AI?','research.html#human-centered-ai'),
        ('02 / Learning','Reasoning & self-regulation','What supports evidence-based explanation, revision and independent transfer?','research.html#reasoning'),
        ('03 / Design','Emerging technologies in STEM','How should immersive tools and educational agents be designed and evaluated?','research.html#technologies')])+'</div>'
    content = intro+section(routes,'audience-band')+section(themes,'muted')+section('<div class="sectionhead"><div><p class="eyebrow">Selected research</p><h2>Read the study.<br><em>Understand the boundaries.</em></h2></div>'+link('All publications','publications.html')+'</div>'+studies_cards(),'white')+section('<div class="feature"><div><p class="eyebrow">A research community</p><h2>People, projects<br>and <em>shared questions.</em></h2><p class="lead">Graduate supervision and international scholarly collaboration connect the research programme to different educational contexts.</p><div class="buttonrow">'+action('Meet the people','team.html')+action('Explore funded projects','projects.html',True)+'</div></div><div class="panel"><small>New on the website</small><h3>Human–AI Feedback & Scientific Reasoning Resources</h3><p>Three bilingual teaching guides, short research briefs and an interactive demonstration. Research findings and site-created examples are clearly distinguished.</p>'+link('Explore the resource collection','resources.html')+'</div></div>','muted')
    render('index.html','Research, resources & people','index.html',content,'Human-centered AI, scientific reasoning and self-regulated learning. Research and teaching resources from Hüseyin Ateş.')


def core_pages() -> None:
    for name,title,active in [('research.html','Research','research.html'),('publications.html','Publications','publications.html'),('projects.html','Projects','research.html'),('about.html','About & CV','about.html'),('contact.html','Contact','about.html')]:
        main=original_main(name)
        main=main.replace('Listings are based on my academic CV, updated in October 2026.','Explore linked publisher records and selected research briefs.')
        main=re.sub(r'<p class="center-note">The above list is a CV-based selection.*?</p>','',main,flags=re.S)
        main=re.sub(r'<div class="callout">Funder, project duration.*?</div>','',main,flags=re.S)
        main=main.replace('Each project has its own page with verified grant information and the scope stated in the academic CV.','Explore each project’s question, funding programme and research setting.')
        main=main.replace('Individual appointments to funded projects are not assumed without documentary confirmation.','')
        if name=='research.html':
            main=section('<nav class="subnav" aria-label="Research sections">'+link('Research themes','#human-centered-ai')+link('Funded projects','projects.html')+link('Methods & access','open-research.html')+'</nav>','subsection')+main
        if name=='publications.html':
            end=main.find('</section>')+len('</section>')
            main=main[:end]+section('<p class="eyebrow">Beyond the citation</p><h2>Selected <em>research briefs.</em></h2>'+studies_cards(),'muted')+main[end:]
        if name=='about.html':
            main=main.replace('onclick="window.print()"','data-print')
            main+=section('<p class="eyebrow">Research enquiries</p><h2>Connect through <em>a shared question.</em></h2><div class="buttonrow">'+action('Working with us','join.html')+action('Contact','contact.html',True)+'</div>')
        render(name,title,active,main,title+' — Hüseyin Ateş academic research website.')
    for path in sorted(ROOT.glob('project-*.html')):
        main=original_main(path.name)
        main=main.replace('Funded project (as recorded in academic CV)','Funded project')
        main=main.replace('<dt>Identifier</dt><dd>3501 Career Development Program</dd>','<dt>Programme</dt><dd>3501 Career Development Program</dd>')
        main=re.sub(r'<section class="section white"><div class="container feature"><div><div class="eyebrow">Evidence & outcomes</div>.*?</section>','',main,flags=re.S)
        main=re.sub(r'<div class="callout">Project summaries reflect.*?</div>','',main,flags=re.S)
        main+=section('<div class="feature"><div><p class="eyebrow">Related teaching resources</p><h2>Explore the <em>ideas.</em></h2><p>Site-created teaching guides offer a way to discuss reasoning and self-regulation. They are separate from this project’s study protocol and instruments.</p>'+link('Browse teaching resources','resources.html')+'</div><div class="panel"><small>Project information</small><h3>Research enquiries</h3><p>For protocol, collaboration or research-material enquiries, contact the principal investigator. This page describes the project scope; it does not report unpublished results or advertise participant recruitment.</p>'+link('Contact Hüseyin Ateş','contact.html')+'</div></div>','muted')
        title=html.unescape(re.search(r'<h1>(.*?)</h1>',main,re.S).group(1))
        render(path.name,title,'research.html',main,title+' — funded research project.')


def people() -> None:
    lead='<div class="team-leader"><div class="leader-badge" aria-hidden="true">HA.</div><div><p class="eyebrow">Principal investigator / Research supervisor</p><h2>Hüseyin Ateş, <em>PhD</em></h2><p>Associate Professor of Science Education at Kırşehir Ahi Evran University. Research connects human-centered AI, scientific reasoning, self-regulated learning and emerging technologies in STEM education.</p>'+link('Academic biography & CV','about.html')+'</div></div>'
    body=hero('People / Research Team','Research grows through <em>people.</em>','Meet the graduate researchers, alumni and selected collaborators connected to the research programme.','<nav class="subnav" aria-label="People sections">'+link('Graduate researchers','#graduate-researchers')+link('Alumni','#alumni')+link('Collaborators','#collaborators')+'</nav>')+section(lead,'white','leadership')
    for group,heading,id_ in [('graduate','Graduate researchers','graduate-researchers'),('alumni','Research alumni','alumni'),('collaborators','Selected collaborators','collaborators')]:
        cards=[]
        for p in DATA['people']:
            if p['group']!=group: continue
            url='person-'+p['slug']+'.html'
            cards.append(f'<article class="person-card"><div class="person-top"><span class="person-monogram" aria-hidden="true">{p["initials"]}</span><div><p class="micro-label">{esc(p["role"])}</p><h3>{esc(p["name"])}</h3></div></div><p class="person-topic">{esc(p["topic"])}</p>{link("View research profile",url)}</article>')
            detail=section('<div class="profile-layout"><div class="profile-avatar" aria-hidden="true">'+p['initials']+'</div><div><p class="eyebrow">Research profile</p><h2>'+esc(p['topic'])+'</h2><p class="lead">'+esc(p['description'])+'</p><p>'+esc(p['detail'])+'</p><h3>Explore connected work</h3><div class="profile-links">'+''.join(link(label,u) for label,u in p['links'])+'</div><p class="micro-note">Related-theme links do not imply authorship of a resource or appointment to a project.</p></div></div>','white')
            render(url,p['name'],'team.html',hero(p['role'],esc(p['name']),esc(p['topic']))+detail+section(action('Back to people','team.html',True)),p['name']+' — '+p['topic'])
        explanation='<p class="team-intro">Collaborators are listed separately from supervised researchers and funded-project personnel.</p>' if group=='collaborators' else ''
        body+=section('<p class="eyebrow">'+('Current supervision' if group=='graduate' else 'Research connections')+'</p><h2>'+heading+'</h2>'+explanation+'<div class="people-grid">'+''.join(cards)+'</div>','muted' if group!='alumni' else 'white',id_)
    render('team.html','People & Research Team','team.html',body+section(action('Explore working together','join.html')), 'Graduate researchers, alumni and selected research collaborators.')


def studies() -> None:
    for s in DATA['studies']:
        filename='study-'+s['slug']+'.html'
        bibliography=f'Ateş, H. ({s["year"]}). {s["title"]}. {s["journal"]}. https://doi.org/{s["doi"]}'
        (OUT/'downloads'/('study-'+s['slug']+'.bib')).write_text('@article{Ates'+s['year']+s['slug'].replace('-','')+',\n  author = {Ateş, Hüseyin},\n  title = {'+s['title']+'},\n  year = {'+s['year']+'},\n  doi = {'+s['doi']+'}\n}\n',encoding='utf-8')
        content=hero(s['year']+' / Research brief',esc(s['label'])+' <em>in focus.</em>',esc(s['question']))
        content+=section('<div class="reading-grid"><div class="reading"><p class="eyebrow">Study design</p><p class="lead">'+esc(s['design'])+'</p><h2>Reported <em>findings.</em></h2><p>'+esc(s['finding'])+'</p>'+note('<strong>Scope note · editorial interpretation.</strong> '+esc(s['boundary']))+'<h3>Read the original study</h3><p class="citation">'+esc(bibliography)+'</p><div class="buttonrow">'+action('Publisher / DOI','https://doi.org/'+s['doi'])+action('Citation · BibTeX','downloads/study-'+s['slug']+'.bib',True)+'</div><p class="micro-note">This is an editorial research brief, not the article’s full abstract or a replacement for its methods and results. '+link('Source used for the brief',s['source'])+'</p></div><aside class="panel"><small>Read in Turkish</small><div lang="tr"><h3>Türkçe araştırma özeti</h3><p>'+esc(s['tr'])+'</p></div><hr><h3>Explore the ideas</h3><p>Teaching examples on this website are separate from published study instruments.</p>'+link(s['resource_label'],s['resource'])+'</aside></div>','white')
        render(filename,s['label']+' — research brief','publications.html',content,s['question'])


def resources() -> None:
    intro=hero('Resources / Human–AI feedback & scientific reasoning','Ideas to read.<br>Tools to <em>think with.</em>','Explore bilingual teaching prototypes, research briefs and an interactive feedback example. Each item states what it is—and what it is not.')
    content=intro+section('<div class="sectionhead"><div><p class="eyebrow">Start with an example</p><h2>Feedback Design <em>Explorer.</em></h2></div>'+action('Open the Explorer','feedback-explorer.html')+'</div><p class="lead">Compare direct, reflective and hybrid feedback on the same fictional student response. Switch between English and Turkish. No account, live AI model or student-data upload is involved.</p>','muted')
    content+=section('<div class="sectionhead"><div><p class="eyebrow">Original teaching prototypes / Version 1.0</p><h2>Plan. Question. <em>Reflect.</em></h2></div></div>'+resources_cards(),'white')
    content+=section('<div class="cards">'+card('Research evidence','Read a research brief','Short accounts of selected studies, with source links and scope notes.','practice.html','Browse briefs')+card('Research access','Methods, materials & requests','Distinguish shareable templates from study data and published instruments.','open-research.html','Explore access')+card('For schools','Connect research and practice','Start a conversation about a classroom question or resource adaptation.','join.html#schools','Explore collaboration')+'</div>','muted')
    render('resources.html','Resources & teaching materials','resources.html',content,'Bilingual teaching prototypes and research briefs for feedback, scientific argumentation and self-regulated learning.')
    for r in DATA['resources']:
        controls='<div class="language-control"><label for="resource-language">Reading language / Okuma dili</label><select id="resource-language" data-language-picker><option value="en">English</option><option value="tr">Türkçe</option><option value="all">Both / İkisi</option></select><button type="button" class="buttonprint" data-print>Print / Save as PDF</button></div>'
        body=hero('Teaching prototype / Version 1.0',esc(r['title']),esc(r['short']),'<p class="resource-meta">'+esc(r['audience'])+' · EN / TR · '+DATE+'</p>')
        blocks=''
        for lang in ['en','tr']:
            t=r[lang]
            md='# '+r['title']+'\n\n'+t['title']+'\n\nVersion 1.0 | '+DATE+' | Teaching prototype / Öğretim örneği\n\n'+t['intro']+'\n\n'
            steps=''
            for heading,text in t['sections']:
                steps+='<article class="learning-step"><h3>'+esc(heading)+'</h3><p>'+esc(text)+'</p></article>'
                md+='## '+heading+'\n\n'+text+'\n\n'
            md+='## Worksheet / Çalışma yaprağı\n\n'+t['prompt']+'\n\n'+t['caution']+'\n\nSource: '+BASE+'resource-'+r['slug']+'.html\n\nSite-created prototype, not a validated instrument. No open licence is assigned; contact for redistribution or adaptation. Linked papers have separate terms.\n'
            download='downloads/'+r['slug']+'-'+lang+'.md'
            (OUT/download).write_text(md,encoding='utf-8')
            blocks+='<div data-lang="'+lang+'" lang="'+lang+'"><p class="eyebrow">'+('English' if lang=='en' else 'Türkçe')+'</p><h2>'+esc(t['title'])+'</h2><p class="lead">'+esc(t['intro'])+'</p>'+steps+'<div class="worksheet"><h3>'+('Worksheet prompt' if lang=='en' else 'Çalışma yaprağı')+'</h3><p>'+esc(t['prompt'])+'</p><div class="writing-lines" aria-hidden="true"></div></div>'+note(esc(t['caution']))+'<div class="buttonrow">'+action('Download Markdown · '+lang.upper(),download,True)+'</div></div>'
        body+=section(controls+'<div class="reading resource-reading">'+blocks+'</div>','white')+section('<div class="buttonrow">'+action('Explore feedback examples','feedback-explorer.html')+action('Related research brief',r['related'],True)+'</div><p class="micro-note">'+link('Use, attribution & resource status','site-notes.html#resources')+'</p>','muted')
        render('resource-'+r['slug']+'.html',r['title'],'resources.html',body,r['short'])


def explorer() -> None:
    en={
        'question':'Does more light explain the greater growth?',
        'context':'Fictional observations over one week: plant A receives 4 hours of light and 20 mL of water per day; plant B receives 8 hours and 40 mL. The recorded growth is 2 cm and 5 cm respectively. There is one plant per condition. These numbers are invented for teaching, not research observations.',
        'answer':'More light always makes every plant grow faster because plant B grew more.',
        'direct':('Direct feedback','Your claim goes beyond these observations. Both water and light changed, and each condition contains only one plant. Describe the observed difference without attributing it to light alone; suggest a comparison in which water is held constant.'),
        'reflective':('Reflective feedback','Which conditions changed between A and B? Which observation separates light from water as an explanation? How far can a claim based on one plant per condition extend? Rewrite the claim to match what the observations can support.'),
        'hybrid':('Hybrid sequence','First, identify the strongest and weakest parts of your own claim. Next, ask a peer to identify another possible explanation. Then compare both judgements with this critique: light and water changed together, so their separate effects cannot be determined. Decide which revision you will make and explain why.'),
        'task':'Learner decision: What will you accept, adapt or reject in this feedback—and what evidence supports your decision?',
        'check':'An appropriately limited conclusion describes greater recorded growth for B under combined changes in light and water. It does not identify the causal effect of light alone. A stronger follow-up comparison would hold other relevant conditions constant and use more observations.'
    }
    tr={
        'question':'Daha fazla ışık, daha fazla büyümeyi açıklıyor mu?',
        'context':'Bir haftaya ilişkin kurgusal gözlemler: A bitkisi günde 4 saat ışık ve 20 mL su, B bitkisi 8 saat ışık ve 40 mL su alıyor. Kaydedilen büyüme sırasıyla 2 cm ve 5 cm. Her koşulda yalnızca bir bitki var. Sayılar öğretim amacıyla üretilmiştir; araştırma gözlemi değildir.',
        'answer':'Daha fazla ışık her bitkinin her zaman daha hızlı büyümesini sağlar; çünkü B bitkisi daha fazla büyüdü.',
        'direct':('Doğrudan geri bildirim','İddianız bu gözlemlerin ötesine geçiyor. Hem ışık hem su değişti ve her koşulda tek bitki var. Büyüme farkını yalnızca ışığa bağlamadan betimleyin; suyun sabit tutulduğu bir karşılaştırma önerin.'),
        'reflective':('Yansıtıcı geri bildirim','A ve B arasında hangi koşullar değişti? Hangi gözlem, açıklama olarak ışığı sudan ayırıyor? Her koşulda tek bitkiye dayanan iddia ne kadar genellenebilir? İddianızı gözlemlerin desteklediği sınırlar içinde yeniden yazın.'),
        'hybrid':('Hibrit geri bildirim dizisi','Önce kendi iddianızın güçlü ve zayıf yönlerini belirleyin. Sonra bir akranınızdan alternatif açıklama isteyin. İki değerlendirmeyi şu eleştiriyle karşılaştırın: ışık ve su birlikte değiştiğinden ayrı etkileri belirlenemez. Yapacağınız düzeltmeyi seçin ve gerekçelendirin.'),
        'task':'Öğrenci kararı: Geri bildirimin hangi bölümünü kabul edecek, uyarlayacak veya reddedeceksiniz? Kararınızı hangi kanıt destekliyor?',
        'check':'Sınırları uygun bir sonuç, ışık ve su birlikte değişirken B için daha fazla büyüme kaydedildiğini belirtir. Işığın tek başına nedensel etkisini belirlemez. Daha güçlü bir karşılaştırma diğer ilgili koşulları sabit tutar ve daha fazla gözlem kullanır.'
    }
    controls='<div class="explorer-controls"><div><label for="explorer-language">Language / Dil</label><select id="explorer-language" data-language-picker><option value="en">English</option><option value="tr">Türkçe</option><option value="all">Both / İkisi</option></select></div><div><label for="feedback-mode">Feedback approach / Yaklaşım</label><select id="feedback-mode" data-feedback-picker><option value="direct">Direct / Doğrudan</option><option value="reflective">Reflective / Yansıtıcı</option><option value="hybrid">Hybrid / Hibrit</option><option value="all">Compare all / Tümünü karşılaştır</option></select></div></div>'
    content=hero('Interactive / Teaching prototype','Feedback Design <em>Explorer.</em>','One fictional answer. Three ways to respond. Examine what the learner—not the tool—is asked to do.')
    content+=section(controls+note('This demonstration uses fixed, site-created examples. It does not call an AI service, assess a learner, collect responses or reproduce a published intervention. With JavaScript disabled, all examples remain readable.')+'<div class="explorer-content">'+''.join('<div data-lang="'+lang+'" lang="'+lang+'"><h2>'+esc(d['question'])+'</h2><p>'+esc(d['context'])+'</p><blockquote class="student-answer"><p class="eyebrow">'+('Fictional student response' if lang=='en' else 'Kurgusal öğrenci yanıtı')+'</p><p>'+esc(d['answer'])+'</p></blockquote><div class="feedback-grid">'+''.join('<article class="feedback-card" data-mode="'+mode+'"><p class="eyebrow">'+str(i+1).zfill(2)+'</p><h3>'+esc(d[mode][0])+'</h3><p>'+esc(d[mode][1])+'</p></article>' for i,mode in enumerate(['direct','reflective','hybrid']))+'</div><p class="decision-prompt">'+esc(d['task'])+'</p><details><summary>'+('Reasoning check' if lang=='en' else 'Akıl yürütme kontrolü')+'</summary><p>'+esc(d['check'])+'</p></details></div>' for lang,d in [('en',en),('tr',tr)])+'</div>','white')
    content+=section('<div class="buttonrow">'+action('Use the feedback toolkit','resource-feedback.html')+action('Examine an argument','resource-argumentation.html',True)+'</div><p>These examples illustrate possible choices in feedback design, not evidence that a specific phrasing is superior.</p>','muted')
    render('feedback-explorer.html','Feedback Design Explorer','resources.html',content,'Compare direct, reflective and hybrid feedback in English and Turkish using a fictional science-learning example.')
    (OUT/'downloads/synthetic-plant-example.csv').write_text('example_type,plant,light_hours_per_day,water_ml_per_day,growth_cm_over_week,plants_per_condition\nfictional_teaching_example,A,4,20,2,1\nfictional_teaching_example,B,8,40,5,1\n',encoding='utf-8')


def access_and_join() -> None:
    method_cards='<div class="cards">'+card('Design','Experimental comparisons','Classroom and multisite interventions, repeated observations and delayed outcomes.','research.html')+card('Measurement','Reasoning & revision','Argument evaluation, feedback uptake, transparent coding and construct validation.','publications.html')+card('Modelling','Technology adoption','Theory-driven quantitative modelling and structural equation modelling.','research.html#technologies')+'</div>'
    body=hero('Open Research / Methods & access','Make the research<br><em>traceable.</em>','Explore research methods, distinguish teaching templates from study materials, and find the appropriate route for access enquiries.')
    body+=section(method_cards,'white')+section('<div class="feature"><div><p class="eyebrow">Available on this site</p><h2>Transparent <em>resource status.</em></h2><p>The downloadable materials are original teaching prototypes. No participant dataset, published instrument or preregistration is implied by their availability.</p><div class="profile-links">'+link('Bilingual teaching guides','resources.html')+link('Fictional plant example · CSV','downloads/synthetic-plant-example.csv')+link('Variable documentation template · CSV','downloads/variable-dictionary-template.csv')+'</div></div><div class="panel"><small>Published data-availability statements</small><h3>Access is study-specific.</h3><p>The GenAI feedback and AR–tutoring articles describe restricted research data, with requests subject to the conditions in each publication.</p>'+link('GenAI study statement','https://link.springer.com/article/10.1186/s41239-026-00614-9#data-availability')+link('AR–tutoring statement','https://link.springer.com/article/10.1007/s10639-024-12970-y#data-availability')+'</div></div>','muted')
    body+=section('<div class="reading"><p class="eyebrow">Requesting research material</p><h2>Begin with <em>a clear question.</em></h2><p>Include the publication DOI, the exact material requested, your intended use and institutional affiliation. Please do not send identifiable student records in an initial enquiry. A request does not guarantee access; the relevant study conditions and approvals govern any sharing.</p>'+action('Contact about research access','mailto:'+EMAIL+'?subject=Research%20material%20enquiry')+'</div>','white')
    render('open-research.html','Open Research & methods','research.html',body,'Research methods, teaching-resource status and study-specific data access.')
    (OUT/'downloads/variable-dictionary-template.csv').write_text('variable_name,definition,unit_or_scale,allowed_values,missing_value_rule,source,notes\n',encoding='utf-8')
    join=hero('Join & Collaborate','Start with a<br><em>shared research question.</em>','Research conversations may begin with a classroom challenge, a doctoral interest or a cross-context comparison.')
    for id_,kicker,title,text,items,subject in [
        ('researchers','For researchers','Develop a research connection','Potential conversations can concern feedback design, scientific argumentation, self-regulation or educational technology. Enquiries are welcome; projects and affiliations are agreed individually.',['Your research question and theoretical focus','A relevant publication or existing study','The proposed contribution and context'],'Research collaboration enquiry'),
        ('students','For prospective students','Explore supervision fit','Describe how your interests connect to the research programme. An expression of interest is not an admission decision, a scholarship or an advertised funded position. Formal admission remains subject to university procedures.',['A concise research interest statement','Your academic background and relevant methods experience','The question you would like to discuss'],'Graduate research enquiry'),
        ('schools','For schools & teachers','Bring research into conversation with practice','Start with a question from your teaching context. Resource feedback and discussion do not themselves constitute participation in a study. Any formal research involvement requires a separately agreed process.',['Your teaching context and learning question','The resource or research theme of interest','The kind of discussion or collaboration you are seeking'],'School and teacher collaboration')]:
        join+=section('<div class="feature"><div><p class="eyebrow">'+kicker+'</p><h2>'+title+'</h2><p class="lead">'+text+'</p></div><div class="panel"><small>A useful first message</small><ul>'+''.join('<li>'+esc(x)+'</li>' for x in items)+'</ul>'+action('Open an email enquiry','mailto:'+EMAIL+'?subject='+quote(subject))+'</div></div>','white' if id_!='students' else 'muted',id_)
    join+=section(note('<strong>Before sending.</strong> No application form is hosted here. Email links open your mail application; the website does not send a message automatically. Avoid sending identifiable learner data.'),'muted')
    render('join.html','Join & Collaborate','join.html',join,'Research, graduate supervision and school collaboration enquiries.')


def practice_and_notes() -> None:
    practice=hero('For teachers / Öğretmenler için','Connect research to<br><em>classroom questions.</em>','Read a brief, examine an example and adapt your question to the learners in front of you. Teaching suggestions are separated from reported study findings.')
    practice+=section('<p class="eyebrow">Read in English & Turkish</p><h2>Three studies.<br><em>Three starting points.</em></h2>'+studies_cards(),'white')+section('<p class="eyebrow">Prepare a learning activity</p><h2>Resources for <em>discussion.</em></h2>'+resources_cards(),'muted')+section('<div class="feature"><div><h2>From a classroom question<br>to a <em>research conversation.</em></h2><p>Tell us about the question, the setting and the resource you are exploring. Do not assume that a positive result from one study will carry over unchanged to your own setting.</p>'+action('School & teacher collaboration','join.html#schools')+'</div><aside class="panel" lang="tr"><small>Öğretmenler için</small><h3>Araştırma bulgusu ile öğretim örneğini ayırın.</h3><p>Özetlerde yayımlanmış çalışmaların kapsamı belirtilir. Çalışma yaprakları bu site için hazırlanmış örneklerdir; geçerliği sınanmış ölçekler değildir. Kaynak sayfalarındaki dil seçimiyle Türkçe metne ulaşabilirsiniz.</p></aside></div>','white')
    render('practice.html','For teachers / Öğretmenler için','resources.html',practice,'Bilingual research briefs and original resources for science teachers.')
    notes=hero('About this website','Sources, access &<br><em>resource notes.</em>','A clear distinction between published research, academic profile information and site-created teaching examples.')
    notes+=section('<div class="reading"><h2>Content and attribution</h2><p>Academic appointments, supervision and project records were supplied by Hüseyin Ateş. Selected research briefs link to the publisher or institutional record used for the summary. Briefs are editorial paraphrases, not complete abstracts; interpretive cautions are labelled separately.</p><h2 id="resources">Teaching resources</h2><p>The toolkits, worksheets and fictional examples were prepared for this website with AI-assisted drafting. They are teaching prototypes, not published study instruments, validated scales or evidence of an intervention’s effectiveness. Please review subject accuracy and suitability before use.</p><p>Downloads are provided for reading and evaluation. No open licence is assigned to these prototypes. Contact the site owner before redistribution or adaptation. Linked journal publications retain their own rights and access terms.</p><h2>Privacy and external services</h2><p>This release includes no analytics script, tracking cookie, online application form, live AI API or student-response upload. Interactive controls run in the browser without storing responses. The hosting provider may process technical access information. Following external links or sending email uses another service’s terms.</p><h2>Accessibility</h2><p>The interface includes a skip link, keyboard-operable controls, visible focus indicators, responsive layouts and printable resource views. Examples remain readable without JavaScript. This is not a claim of independent accessibility certification.</p><h2>Corrections and enquiries</h2><p>For an academic-content correction, a resource-use request or an accessibility difficulty, contact '+link(EMAIL,'mailto:'+EMAIL)+'.</p><p class="micro-note">Website content update: '+DATE+'. Resource prototypes: version 1.0.</p></div>','white')
    render('site-notes.html','Site & resource notes','about.html',notes,'Sources, resource status, privacy characteristics and accessibility notes.')
    render('404.html','Page not found','index.html',hero('404','Let’s find the<br><em>right page.</em>','This address is not part of the current website.')+section('<div class="buttonrow">'+action('Go to the homepage','index.html')+action('Browse resources','resources.html',True)+'</div>'))


def main() -> None:
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/'downloads').mkdir(parents=True)
    shutil.copytree(ROOT/'assets',OUT/'assets')
    # Serve system-font fallbacks without third-party font requests.
    styles=OUT/'assets/styles.css'
    styles.write_text(re.sub(r'@import\s+url\([^;]+;','',styles.read_text(encoding='utf-8')),encoding='utf-8')
    home();core_pages();people();studies();resources();explorer();access_and_join();practice_and_notes()
    (OUT/'.nojekyll').touch()
    manifest={'commit':os.environ.get('GITHUB_SHA','local-preview'),'version':DATA['version'],'updated':DATA['updated'],'pages':sorted(PAGES),'page_count':len(PAGES),'downloads':sorted(p.relative_to(OUT).as_posix() for p in (OUT/'downloads').glob('*'))}
    (OUT/'deployment.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+BASE+n+'</loc><lastmod>'+DATA['updated']+'</lastmod></url>' for n in sorted(PAGES) if n!='404.html')+'</urlset>',encoding='utf-8')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n',encoding='utf-8')
    print(f'Built {len(PAGES)} HTML pages and {len(manifest["downloads"])} downloads in {OUT}')

if __name__=='__main__':
    main()
