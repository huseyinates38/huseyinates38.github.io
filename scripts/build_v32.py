#!/usr/bin/env python3
"""Public editorial update: proposal status, collaborations and collection development.
Runs after build_v3.py and before build_v31.py (search indexes the final content).
Private correspondence and attachment contents are not part of this repository.
"""
from __future__ import annotations
import json
from html import escape as e
from pathlib import Path
from bs4 import BeautifulSoup as Soup

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
BASE='https://huseyinates38.github.io/'
DATA=json.loads((ROOT/'content/research-pipeline.json').read_text())
DATE=DATA['status_date']


def frag(text): return Soup(text,'html.parser')
def link(label,url,cls='textlink'): return f'<a class="{cls}" href="{e(url,quote=True)}">{e(label)} <span aria-hidden="true">↗</span></a>'
def links(items): return '<div class="v3-links">'+''.join(link(a,b) for a,b in items)+'</div>'
def section(title,body,tone='',id_=''):
    return f'<section class="section {tone}"'+(f' id="{id_}"' if id_ else '')+f'><div class="container"><h2>{title}</h2>{body}</div></section>'
def hero(kicker,title,description,extra=''):
    return f'<section class="pagehero"><div class="container"><p class="eyebrow">{e(kicker)}</p><h1>{title}</h1><p class="lead">{e(description)}</p>{extra}</div></section>'
def badge(label,state):return f'<span class="status-pill status-{e(state)}">{e(label)}</span>'
def page_url(p):return p.get('page','proposal-'+p['slug']+'.html')


def render(name,title,body,description,active='research.html'):
    s=Soup((SITE/'index.html').read_text(),'html.parser')
    s.title.string=title+' | Hüseyin Ateş'
    for sel,value in [('meta[name="description"]',description),('meta[property="og:title"]',s.title.string),('meta[property="og:description"]',description),('meta[property="og:url"]',BASE+name)]:
        n=s.select_one(sel)
        if n:n['content']=value
    s.select_one('link[rel="canonical"]')['href']=BASE+name
    for n in s.select('script[type="application/ld+json"]'):n.decompose()
    for n in s.select('[aria-current]'):del n['aria-current']
    n=s.select_one(f'#main-navigation a[href="{active}"]')
    if n:n['aria-current']='page'
    s.main.clear();s.main.append(frag(body))
    (SITE/name).write_text(str(s),encoding='utf-8')


def proposal_cards():
    return '<div class="pipeline-grid">'+''.join(
        '<article class="pipeline-card" data-proposal-state="'+p['state']+'">'+badge(p['status'],p['state'])+
        '<p class="micro-label">'+e(p['programme'])+'</p><h3>'+e(p['title'])+'</h3><p>'+e(p['summary'])+'</p>'+link('Read proposal scope',page_url(p))+'</article>'
        for p in DATA['proposals'])+'</div>'


def proposals():
    intro=hero('Research / Proposal pipeline','Submitted, planned<br>& <em>in development.</em>',
      'Research proposals are presented separately from funding awards. Each record identifies whether a proposal has been submitted or remains in development.',
      links([('Supported projects','projects.html#funded-projects'),('Ongoing collaborative study','project-ai-literacy-colombia.html'),('Editorial initiatives','editorial.html')]))
    body=intro+section(str(len(DATA['proposals']))+' proposals. <em>Different stages.</em>',
        '<div class="pipeline-legend"><p><strong>Submitted:</strong> application made; no funding decision announced.</p><p><strong>Planned:</strong> a research concept that has not yet been submitted.</p></div>'+proposal_cards(),'muted')
    body+=section('Status, not a promise of funding',
        '<p class="lead">Proposed durations, host arrangements and research scopes describe applications or plans. They do not establish an awarded grant, confirmed visit or completed research result.</p><p class="v3-small">Status reviewed: 12 November 2026. No private proposal documents or correspondence are made available through these pages.</p>'+links([('Public academic CV','downloads/Huseyin_Ates_Public_Academic_CV.pdf'),('Research enquiries','contact.html')]))
    render('proposals.html','Submitted & planned proposals',body,str(len(DATA['proposals']))+' submitted, planned or non-funded research proposals, clearly separated from supported projects.')
    for p in DATA['proposals']:
        fields=[('Programme',p['programme']),('Current status',p['status']),('Research lead / role',p['lead']),('Proposed duration / visit',p['period']),('Research setting',p['setting']),('Status reviewed','12 November 2026')]
        meta='<dl class="proposal-meta">'+''.join('<dt>'+e(k)+'</dt><dd>'+e(v)+'</dd>' for k,v in fields)+'</dl>'
        body=hero('Research / Proposal pipeline',e(p['title']),p['full_title'],badge(p['status'],p['state']))
        body+=section('Research <em>scope</em>.','<div class="proposal-layout"><div><p class="lead">'+e(p['summary'])+'</p><p>'+e(p['scope'])+'</p>'+links(p['links'])+'</div><aside class="proposal-side">'+meta+'</aside></div>','white')
        body+=section('Collaboration & <em>current position</em>.','<p class="lead">'+e(p['relationship'])+'</p><aside class="callout"><strong>Status boundary.</strong> '+e(p['limits'])+'</aside>','muted')
        body+=section('Explore the research programme',links([('All proposals','proposals.html'),('Supported projects','projects.html#funded-projects'),('People','team.html'),('Contact','contact.html')]))
        render(page_url(p),p['title'],body,p['programme']+' — '+p['status']+'. '+p['summary'])


def collaborative_study():
    title='GenAI Literacy: Türkiye–Colombia'
    body=hero('Research / Ongoing collaboration', 'GenAI literacy.<br><em>A cross-context study.</em>',
       'An ongoing Türkiye–Colombia study of AI literacy and responsible academic use, with instrument adaptation and pilot preparation in progress.',badge('Ongoing study · pilot preparation','ongoing'))
    body+=section('A shared research <em>question</em>.','<div class="proposal-layout"><div><p class="lead">The study examines GenAI literacy and responsible academic use in two university contexts, with a common instrument and coordinated cross-language adaptation.</p><p>The collaboration links conceptual and questionnaire development with English, Turkish and Colombian Spanish adaptation. It also coordinates disciplinary sampling and preparation for cognitive interviews and piloting.</p><p>The page title is a descriptive study label. It is not a registered trial title or a claim of an awarded grant.</p></div><aside class="proposal-side"><dl class="proposal-meta"><dt>Study coordinator</dt><dd>Juan David Murillo Egurrola</dd><dt>Institutional contexts</dt><dd>Universidad Católica de Oriente, Colombia; Kırşehir Ahi Evran University, Türkiye</dd><dt>Current stage</dt><dd>Adaptation and pilot preparation</dd><dt>Funding classification</dt><dd>Ongoing collaboration; no external award listed</dd><dt>Status reviewed</dt><dd>12 November 2026</dd></dl></aside></div>','white')
    roles=[('Juan David Murillo Egurrola','Study coordination and Colombia-site preparation','person-juan-david-murillo-egurrola.html'),('Juan Garzón','Research collaboration and conceptual / methodological development','person-juan-garzon.html'),('Hüseyin Ateş','Methodological contribution and Türkiye-site coordination','about.html'),('Abdulkadir Aydın','Turkish adaptation review and programme-level fieldwork preparation','person-abdulkadir-aydin.html')]
    cards='<div class="pipeline-grid">'+''.join('<article class="pipeline-card"><h3>'+e(n)+'</h3><p>'+e(r)+'</p>'+link('Research profile',u)+'</article>' for n,r,u in roles)+'</div>'
    body+=section('People & documented <em>contributions</em>.',cards+'<p class="v3-small">Content-review contributions also involve Kibar Sungur Gül for the Türkiye context and Edison Ferney Castrillón Ángel for the Colombian context. These are study contributions, not claims of employment or funding.</p>','muted')
    body+=section('Preparation before <em>results</em>.','<p class="lead">The Turkish text has undergone independent human back-translation and reconciliation, and the Colombian Spanish adaptation has been shared. The teams are coordinating the remaining fieldwork arrangements and pilot schedule.</p><aside class="callout">This page does not announce completed international data collection or research findings. Site-specific permissions and scheduling are not assumed to be complete at both institutions. No participant responses, draft instruments or private operational documents are published.</aside>'+links([('Research collaborators','team.html#collaborators'),('Projects & proposals','projects.html')]))
    render('project-ai-literacy-colombia.html',title,body,'Ongoing Türkiye–Colombia collaboration on GenAI literacy and responsible academic use. Instrument adaptation and pilot preparation, not a funded-project award.')


def editorial():
    intro=hero('Academic service / Editorial initiatives','Collections &<br><em>editorial collaboration.</em>',
        'A collection proposal in development and a separate earlier guest-advisory activity. Their statuses and roles are not interchangeable.',links([('ETHE proposal','#ethe'),('Sustainable Environment','#sustainable-environment'),('Editorial connection','person-marc-romero-carbonell.html')]))
    body=intro+section('Learning with GenAI in <em>higher education</em>.',badge('Proposed collection · journal approval pending','planned')+
        '<p class="micro-label">International Journal of Educational Technology in Higher Education · ETHE</p><p class="lead">Hüseyin Ateş and Juan Garzón are developing a thematic-collection proposal in consultation with Marc Romero Carbonell. Its working scope asks how learning changes with GenAI support and what students need to learn in this context.</p><div class="v3-grid"><div><h3>Learning processes</h3><p>Cognition, regulation, effort, retention, transfer and agency when GenAI support is present, reduced or removed.</p></div><div><h3>Student competencies</h3><p>The competencies higher education needs to develop as students learn with generative AI.</p></div><div><h3>Educational redesign</h3><p>Implications for teaching, curriculum and assessment in relation to those competencies.</p></div></div><p>The scope and international guest-editor team are being developed. The final collection title, publication timetable and submission arrangements have not been announced.</p><aside class="callout"><strong>Not an open call.</strong> The collection proposal requires journal approval before it can proceed. This page is not an invitation to submit manuscripts and does not establish an Editorial Board appointment.</aside>'+links([('Juan Garzón','person-juan-garzon.html'),('Marc Romero Carbonell — editorial liaison','person-marc-romero-carbonell.html')]),'white','ethe')
    body+=section('Emerging Technologies for <em>Sustainable Development</em>.',badge('Earlier collection · guest-advisory service','historical')+'<p class="micro-label">Sustainable Environment</p><p class="lead">Guest-advisory collaboration with Juan Garzón for the separate article collection Emerging Technologies for Sustainable Development.</p><p>The earlier call concerned emerging technologies and sustainable development. It is a different editorial activity from the proposed ETHE collection; this website does not announce a currently open submission window or unpublished editorial outcomes.</p>'+links([('Publisher collection information','https://think.taylorandfrancis.com/article_collections/emerging-technologies-for-sustainable-development/'),('Juan Garzón','person-juan-garzon.html')]),'muted','sustainable-environment')
    body+=section('Keep the roles <em>clear</em>.','<p>Research collaboration, guest-advisory service, development of a guest-editor proposal and membership of a journal’s Editorial Board are distinct roles. Only the documented activity is described here.</p><p class="v3-small">Status reviewed: 12 November 2026. Internal candidate discussions and private correspondence are not published.</p>')
    render('editorial.html','Editorial initiatives',body,'ETHE thematic-collection proposal in development and earlier Sustainable Environment guest-advisory collaboration; no currently open call is announced.')


def projects_index():
    existing=Soup((SITE/'projects.html').read_text(),'html.parser')
    cards=existing.select('.project-summary')
    # Keep three funded project records; both BAP studies are complete.
    for c in cards:
        if c.find('a',href='project-robot-virtual-agent.html'):c.decompose()
    cards=[c for c in cards if c.parent]
    assert len(cards)==3,'Supported-project register must exclude the 3501 proposal'
    completed=[c for c in cards if any(c.find('a',href=k) for k in ('project-vr-stem-vietnam.html','project-vr-circulatory-system.html'))]
    other=[c for c in cards if c not in completed]
    assert len(other)==1 and len(completed)==2
    controls='<div class="v3-topic-filter"><label for="project-programme">Supported-project programme</label><select id="project-programme"><option value="all">All programmes</option><option>1002-A</option><option>BAP</option></select><span id="project-filter-status" role="status">3 projects shown</span></div>'
    body=hero('Research / Projects & proposals','Research at<br><em>different stages.</em>','Supported projects, ongoing collaborative research and prospective applications are separated by status.',links([('Supported projects','#funded-projects'),('Ongoing collaboration','#ongoing-collaboration'),('Proposal pipeline','proposals.html'),('Editorial initiatives','editorial.html')]))
    for c in completed:
        c['data-project-status']='completed'
        c['class']=list(dict.fromkeys(c.get('class',[])+['completed-project-card']))
        idx=c.select_one('.project-index')
        if idx: idx.string=idx.get_text(' ',strip=True).split(' · ')[0]+' · COMPLETED'
    body+=section('Completed <em>research projects</em>.','<div class="project-overview-grid">'+''.join(str(c) for c in completed)+'</div>','white','completed-projects')
    body+=section('Supported <em>research project</em>.',controls+'<div class="project-overview-grid">'+''.join(str(c) for c in other)+'</div>','muted','funded-projects')
    body+=section('Ongoing <em>collaborative research</em>.',badge('Study development · not an external grant award','ongoing')+'<div class="feature"><div><h3>Türkiye–Colombia GenAI literacy study</h3><p class="lead">A cross-context collaboration with Juan Garzón and coordinator Juan David Murillo Egurrola, with contributions from Hüseyin Ateş and doctoral researcher Abdulkadir Aydın.</p><p>Instrument adaptation and pilot preparation are ongoing. Study participation is distinguished from a funding award.</p>'+link('Study scope and contributions','project-ai-literacy-colombia.html')+'</div><aside class="panel"><small>Evidence before claims</small><h3>Methodology, adaptation & preparation</h3><p>Published outputs will be linked when available. No unreported results or completed fieldwork are inferred.</p>'+link('Research collaborators','team.html#collaborators')+'</aside></div>','muted','ongoing-collaboration')
    body+=section('Submitted & planned <em>applications</em>.','<p class="lead">Six submitted applications and one research concept in development appear in the separate register.</p>'+proposal_cards()+links([('Full proposal register','proposals.html')]),'white','proposal-pipeline')
    body+=section('Editorial & international <em>connections</em>.','<p>The proposed ETHE thematic collection and earlier Sustainable Environment advisory activity are presented separately from grant-funded research.</p>'+links([('Editorial initiatives','editorial.html'),('Research collaborators','team.html#collaborators'),('Public academic CV','downloads/Huseyin_Ates_Public_Academic_CV.pdf')]),'muted','international-collaborations')
    render('projects.html','Projects & proposals',body,'Two completed BAP projects and one supported 1002-A project, alongside ongoing collaboration and proposal records.')


def enrich_navigation():
    for name in ['index.html','research.html','about.html']:
        s=Soup((SITE/name).read_text(),'html.parser')
        # Add meaningful routes, without expanding the already full top-level menu.
        body=section('Work in progress. <em>Clearly labelled.</em>','<p class="lead">Follow submitted research proposals, current collaborations and editorial initiatives without confusing plans with funding awards.</p>'+links([('Submitted & planned proposals','proposals.html'),('Editorial initiatives','editorial.html'),('Türkiye–Colombia study','project-ai-literacy-colombia.html')]),'muted','work-in-progress')
        s.main.append(frag(body));(SITE/name).write_text(str(s),encoding='utf-8')
    for p in SITE.glob('*.html'):
        s=Soup(p.read_text(),'html.parser')
        foot=s.select_one('.footer-links')
        if foot:
            for label,url in [('Proposal pipeline','proposals.html'),('Editorial initiatives','editorial.html')]:
                if not foot.find('a',href=url):foot.append(frag(link(label,url)))
        s.head.append(s.new_tag('link',attrs={'rel':'stylesheet','href':'assets/v32.css?v=3.2'}))
        replacements={
            'A two-page public academic CV covering appointments, education, funded projects, teaching, supervision and selected publications.':'A three-page public academic CV separating supported projects from submitted proposals, planned applications and editorial initiatives.',
            'Manuscripts under review and applications awaiting decisions are excluded.':'Unpublished manuscript details are omitted. Submitted and planned proposals are separately labelled and are not funding awards.',
            'selected funded work also addresses robotics and STEM learning.':'supported work addresses STEM learning; robot-based environmental learning is a separate proposal without a funding award.',
            'Graduate supervision and international scholarly collaboration connect':'International scholarly collaboration and graduate supervision connect',
            'Explore funded projects':'Projects & proposals'
        }
        for text in list(s.find_all(string=True)):
            revised=str(text)
            for old,new in replacements.items():revised=revised.replace(old,new)
            if revised!=str(text):text.replace_with(revised)
        (SITE/p.name).write_text(str(s),encoding='utf-8')
    # Keep a concise public correction on the site notes, not a dump of private evidence.
    s=Soup((SITE/'site-notes.html').read_text(),'html.parser')
    s.main.append(frag(section('Project-status update · 12 November 2026','<p>The renewed TÜBİTAK 3501 robot–virtual-agent proposal has been submitted and a funding decision is pending. It remains in the proposal register rather than the funded-project list. Submitted research proposals, planned activities and editorial collection proposals have distinct labels.</p><p>Research and editorial collaborators appear above graduate researchers. Private correspondence, invitation letters and draft research instruments are not published.</p>')))
    (SITE/'site-notes.html').write_text(str(s),encoding='utf-8')


def main():
    proposals();collaborative_study();editorial();projects_index();enrich_navigation()
    css=(ROOT/'assets/v32.css').read_text();(SITE/'assets/v32.css').write_text(css)
    manifest=json.loads((SITE/'deployment.json').read_text());manifest['pages']=sorted(p.name for p in SITE.glob('*.html'));manifest['page_count']=len(manifest['pages']);manifest['version']='3.2';manifest.pop('files',None)
    manifest['downloads']=sorted(p.relative_to(SITE).as_posix() for p in (SITE/'downloads').iterdir() if p.is_file())
    (SITE/'deployment.json').write_text(json.dumps(manifest,indent=2))
    urls=''.join('<url><loc>'+BASE+n+'</loc><lastmod>'+DATE+'</lastmod></url>' for n in manifest['pages'] if n not in ['404.html','search.html'])
    (SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>')
    print('Research-status update: 1 supported + 2 completed BAP projects, 7 proposal entries, 1 ongoing international study and 2 editorial initiatives.')

if __name__=='__main__':main()
