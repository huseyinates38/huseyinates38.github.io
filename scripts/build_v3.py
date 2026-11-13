#!/usr/bin/env python3
"""Enhance the approved v2 site; run after build_site.py and build_professional_docs.py."""
from pathlib import Path
from html import escape as e
import csv, io, json, re, shutil, zipfile
from bs4 import BeautifulSoup as Soup
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'; DL=SITE/'downloads'; BASE='https://huseyinates38.github.io/'
DATE='2026-11-12'; VERSION='3.0'
INSTITUTION='https://unis.ahievran.edu.tr/akademisyen/huseyin.ates'
PROFILES=[('Institutional profile',INSTITUTION),('ORCID','https://orcid.org/0000-0003-0031-8994'),('Google Scholar','https://scholar.google.com/citations?user=LytA1bkAAAAJ&hl=en'),('Web of Science','https://www.webofscience.com/wos/author/record/AAV-6927-2021'),('Scopus','https://www.scopus.com/authid/detail.uri?authorId=57208034648')]
CSS='''
/* v3: publication-ready identity, resources and evidence navigation */
:root{--teal:#146671;--muted:#49616a}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #95501e;outline-offset:4px}
html{scroll-padding-top:110px}button,a.btn,select{min-height:44px}button{font:inherit}.v3-box{background:#fff;border:1px solid #c8d9d4;padding:26px;margin:24px 0}.v3-box h2,.v3-box h3{margin-top:0}.v3-links{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}.v3-links a{display:inline-flex;align-items:center;min-height:44px;padding:9px 13px;border:1px solid #a8c2bd;background:#fff;color:#155d68;font-size:13px;font-weight:700;text-decoration:none}.v3-links a:hover{background:#edf5f1}.v3-small{font-size:12px!important;line-height:1.65;color:#49616a}.v3-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.v3-grid>div{border:1px solid #c8d9d4;padding:22px;background:#fff;min-width:0}.v3-grid h3{font-size:20px}.v3-flow{padding:28px;border:1px solid #bfd3cd;background:#eef5f1;margin:28px 0}.v3-flow ol{list-style:none;padding:0;margin:20px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.v3-flow li{padding:20px;background:white;border-top:3px solid #187886}.v3-flow li strong{display:block;margin-bottom:8px}.v3-flow small{display:block}.v3-frame button{border:1px solid #8eaaa5;background:#fff;padding:14px 18px;color:#153746;cursor:pointer}.v3-frame button[aria-expanded=true]{background:#153746;color:#fff}.v3-frame article{padding:22px;background:#edf5f1;margin-top:16px}.v3-frame article h3{margin-top:0}.v3-frame p{max-width:900px}.v3-timeline{list-style:none;margin:25px 0;padding:0;border-left:2px solid #b6cbc5}.v3-timeline li{padding:0 0 32px 28px;position:relative}.v3-timeline li:before{content:'';position:absolute;left:-7px;top:7px;width:12px;height:12px;border-radius:50%;background:#187886}.v3-timeline time{display:block;color:#146671;font-weight:700}.v3-table-wrap{overflow-x:auto}.v3-table{width:100%;border-collapse:collapse;min-width:660px;font-size:14px}.v3-table th,.v3-table td{padding:15px;text-align:left;vertical-align:top;border-bottom:1px solid #c8d9d4}.v3-table th{background:#edf5f1}.v3-badge{display:inline-block;padding:4px 9px;background:#e6f1eb;color:#155d68;font-size:12px;font-weight:700}.v3-identity{padding:20px 0;border-top:1px solid #c8d9d4;border-bottom:1px solid #c8d9d4}.v3-meta{display:grid;grid-template-columns:150px 1fr;gap:10px;margin:20px 0}.v3-meta dt{font-weight:700}.v3-meta dd{margin:0}.v3-code{padding:20px;background:#153746;color:#fff;overflow:auto;font-size:13px;line-height:1.7}.v3-topic-filter{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:20px 0}.v3-topic-filter label{font-weight:700}.v3-topic-filter select{font:inherit;padding:10px;border:1px solid #9eb7b3}.v3-status{padding:10px 14px;background:#f0f5f1;font-size:13px}.v3-print-note{margin-top:24px;border-top:1px solid #c8d9d4;padding-top:12px}.nav a{min-height:44px;display:inline-flex;align-items:center}.micro-label,.eyebrow{color:#146671!important}.footer{color:#e0ecea}.footer>.v3-links{margin:20px auto 0}.v3-identity{grid-column:1/-1}.v3-fontless{font-family:Arial,sans-serif}
@media(max-width:750px){.v3-grid,.v3-flow ol{grid-template-columns:1fr}.v3-meta{grid-template-columns:1fr}.v3-box{padding:20px}.v3-links a{flex:1 1 130px;justify-content:center}.v3-timeline li{padding-left:20px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important;animation:none!important}}
@media print{.v3-links,.v3-topic-filter,.v3-frame>div{display:none!important}.v3-grid{display:block}.v3-box,.v3-flow{break-inside:avoid}.v3-frame article[hidden]{display:block!important}}
'''
JS='''
'use strict';
// Local, stateless UI only. No analytics, cookies, external API or response uploads.
for(const area of document.querySelectorAll('[data-framework]')){
 const buttons=area.querySelectorAll('[data-panel]');
 const panels=area.querySelectorAll('article[id]');
 const show=id=>{for(const p of panels)p.hidden=p.id!==id;for(const b of buttons)b.setAttribute('aria-expanded',String(b.dataset.panel===id));};
 for(const b of buttons)b.addEventListener('click',()=>show(b.dataset.panel));
 if(buttons.length)show(buttons[0].dataset.panel);
}
const filter=document.querySelector('#project-programme');
if(filter){const cards=document.querySelectorAll('[data-programme]');const status=document.querySelector('#project-filter-status');const apply=()=>{let count=0;for(const c of cards){c.hidden=filter.value!=='all'&&c.dataset.programme!==filter.value;if(!c.hidden)count++;}status.textContent=count+' projects shown';};filter.addEventListener('change',apply);apply();}
for(const b of document.querySelectorAll('[data-copy-citation]'))b.addEventListener('click',async()=>{const target=document.getElementById(b.dataset.copyCitation);const status=document.getElementById('copy-citation-status');try{await navigator.clipboard.writeText(target.textContent);status.textContent='Citation copied.';}catch(_){status.textContent='Select and copy the citation text above.';}});
'''

def load(name):return Soup((SITE/name).read_text(encoding='utf-8'),'html.parser')
def save(name,s): (SITE/name).write_text(str(s),encoding='utf-8')
def fragment(text):return Soup(text,'html.parser')
def links(items):return '<div class="v3-links">'+''.join(f'<a href="{e(url)}">{e(label)}</a>' for label,url in items)+'</div>'
def box(title,body):return '<div class="v3-box"><h2>'+title+'</h2>'+body+'</div>'
def section(title,body):return '<section class="section"><div class="container">'+box(title,body)+'</div></section>'
def append_main(name,html):
 s=load(name);s.main.append(fragment(html));save(name,s)
def add_after_hero(name,html):
 s=load(name);first=s.main.find('section',recursive=False);first.insert_after(fragment(html));save(name,s)
def newpage(name,title,summary,body):
 s=load('about.html');s.title.string=title+' | Hüseyin Ateş, PhD'
 for m in s.head.select('meta[name="description"]'):m['content']=summary
 
 for current in s.select('[aria-current]'):del current['aria-current']
 s.main.clear();s.main.append(fragment('<section class="pagehero"><div class="container"><div class="eyebrow">Research / Resources</div><h1>'+e(title)+'</h1><p>'+e(summary)+'</p></div></section>'+body));save(name,s)


def identity():
 cv=[('Academic CV · PDF','downloads/Huseyin_Ates_Public_Academic_CV.pdf'),('Editable CV · DOCX','downloads/Huseyin_Ates_Public_Academic_CV.docx')]
 content='<p>A two-page public academic CV covering appointments, education, funded projects, teaching, supervision and selected publications.</p>'+links(cv)+'<p class="v3-small">Updated 12 November 2026. Manuscripts under review and applications awaiting decisions are excluded.</p>'+links(PROFILES)
 add_after_hero('about.html',section('Academic identity & downloadable CV',content))
 add_after_hero('contact.html',section('Academic profiles',links(PROFILES)))
 s=load('index.html');hero=s.select_one('.home-hero .container')
 # Add a compact identity strip, preserving the first-screen layout.
 if hero:hero.append(fragment('<div class="v3-identity"><strong>Hüseyin Ateş, PhD</strong> · Kırşehir Ahi Evran University'+links([cv[0],PROFILES[1],PROFILES[2],('Research timeline','research-timeline.html')])+'</div>'))
 save('index.html',s)


def teaching():
 for kind in ['feedback','argumentation','self-regulation']:
  name='resource-'+kind+'.html';s=load(name)
  formats=[]
  for lang,label in [('en','English'),('tr','Türkçe')]:
   formats.extend([(label+' · PDF','downloads/'+kind+'-'+lang+'.pdf'),(label+' · DOCX','downloads/'+kind+'-'+lang+'.docx')])
  first=s.main.find('section',recursive=False)
  first.insert_after(fragment(section('Print-ready & editable materials',links(formats)+'<p class="v3-small">Each file contains a teacher guide and a separate working sheet. Version 1.1; teaching prototypes, not validated instruments.</p>'+links([('Classroom-use terms','resource-use.html')]))))
  for t in list(s.find_all(string=True)):
   if t.parent.name not in ('script','style') and 'Version 1.0' in t:t.replace_with(str(t).replace('Version 1.0','Version 1.1'))
  save(name,s)
 add_after_hero('resources.html',section('A complete classroom resource pack','<p>Six bilingual guides and working sheets, available as searchable PDFs and editable Word files. Choose one resource below or download the full teaching pack.</p>'+links([('Teaching pack · ZIP','downloads/teaching-resources-v1.1.zip'),('Usage & attribution','resource-use.html'),('Methods & example code','open-research.html#methods-kit')])+ '<p class="v3-small">All examples are site-created prototypes. There is no student-data upload and no live AI service.</p>'))
 # Correct the earlier overly restrictive wording consistently, including markdown downloads.
 for name in ['site-notes.html']:
  s=load(name)
  for p in s.find_all('p'):
   if 'No open licence' in p.get_text():
    p.clear();p.append(fragment('Site-created teaching prototypes may be copied and adapted for teaching with source acknowledgement, retention of the prototype notice and a statement of changes. <a href="resource-use.html">Read the scoped classroom-use terms</a>. Journal publications, portraits, logos and third-party material are not covered.'))
  save(name,s)
 newpage('resource-use.html','Resource use & attribution','Clear permissions for site-created teaching examples; separate rights for research publications.',section('Classroom-use permission','<p>The six teaching guides, their working sheets and the fictional plant example may be copied and adapted for teaching. Acknowledge Hüseyin Ateş’s research website, retain the teaching-prototype notice and identify changes.</p><p>Public republication and commercial distribution require separate permission. This is a limited educational-use permission, not a Creative Commons licence or a licence to the entire website. The CV, journal articles, third-party material and any future photographs are excluded.</p><p>These materials were prepared for the website with AI-assisted drafting. They are not validated instruments and must not be represented as a published study’s original intervention materials. Review scientific accuracy, language and learner suitability before use.</p>')+section('Suggested acknowledgement','<p>Adapted from “Human–AI Feedback & Scientific Reasoning Resources”, Hüseyin Ateş research website, version 1.1, 12 November 2026. Changes: [describe]. Teaching prototype; not a validated assessment.</p>'+links([('Return to resources','resources.html'),('Permission enquiries','mailto:huseyin.ates@ahievran.edu.tr')])))
 files=[p for p in DL.iterdir() if p.suffix in ('.md','.pdf','.docx') and any(p.name.startswith(k+'-') for k in ['feedback','argumentation','self-regulation'])]
 with zipfile.ZipFile(DL/'teaching-resources-v1.1.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.name)
  z.writestr('READ_ME.txt','Bilingual teaching prototypes. Each PDF and DOCX has a teacher guide and working sheet. Not validated instruments. Terms: '+BASE+'resource-use.html')


def publication_tools():
 s=load('publications.html');records=[]
 for item in s.select('.publication'):
  title=item.h3.get_text(' ',strip=True);author_text=item.select_one('p').get_text(' ',strip=True).split(' · ')[0]
  journal=item.select_one('em').get_text(' ',strip=True)
  doi=next(a['href'].split('doi.org/')[1] for a in item.select('a[href]') if 'doi.org/' in a['href'])
  # The CV uses initials; preserve exactly rather than guess co-authors' full names.
  authors=re.findall(r'[^,]+,\s*(?:[A-ZÇŞİĞÖÜ]\.\s*)+',author_text.replace(' & ',' ').replace('&',''))
  authors=[a.strip(' ,') for a in authors]
  records.append(dict(title=title,authors=authors,author_text=author_text,year=item['data-year'],journal=journal,doi=doi))
 bib=[];ris=[]
 for i,r in enumerate(records,1):
  bib.append('@article{AtesLibrary'+str(i)+',\n  title = {'+r['title']+'},\n  author = {'+' and '.join(r['authors'])+'},\n  year = {'+r['year']+'},\n  journal = {'+r['journal'].split(',')[0]+'},\n  doi = {'+r['doi']+'}\n}')
  ris.append('\n'.join(['TY  - JOUR','TI  - '+r['title']]+['AU  - '+a for a in r['authors']]+['PY  - '+r['year'],'JO  - '+r['journal'].split(',')[0],'DO  - '+r['doi'],'UR  - https://doi.org/'+r['doi'],'ER  - ']))
 (DL/'selected-publications.bib').write_text('\n\n'.join(bib),encoding='utf-8');(DL/'selected-publications.ris').write_text('\n\n'.join(ris),encoding='utf-8')
 (DL/'publication-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 body='<p>Export all '+str(len(records))+' publications listed here to a reference manager. This remains a selected bibliography, not a claim to reproduce the entire career record.</p>'+links([('BibTeX library','downloads/selected-publications.bib'),('RIS library','downloads/selected-publications.ris'),('Institutional publication record',INSTITUTION),('Google Scholar profile',PROFILES[2][1])])
 s.main.find('section',recursive=False).insert_after(fragment(section('Citation library & wider publication record',body)));save('publications.html',s)
 studies=[('study-genai-feedback.html',0,'International Journal of Educational Technology in Higher Education','23','','38',''),('study-ar-intelligent-tutoring.html',4,'Education and Information Technologies','30','4','4435','4470'),('study-self-regulated-flipped-learning.html',11,'Educational Technology & Society','27','1','65','83')]
 for name,idx,journal,volume,issue,first,last in studies:
  s=load(name);r=records[idx]
  tags={'citation_title':r['title'],'citation_author':'Hüseyin Ateş','citation_publication_date':r['year'],'citation_journal_title':journal,'citation_volume':volume,'citation_doi':r['doi']}
  if issue:tags['citation_issue']=issue
  if first:tags['citation_firstpage']=first
  if last:tags['citation_lastpage']=last
  for key,val in tags.items():s.head.append(s.new_tag('meta',attrs={'name':key,'content':val}))
  # These are editorial briefs: link the original paper rather than inventing a full abstract.
  block=section('Cite the original research','<p id="citation-text">'+e(r['author_text']+' ('+r['year']+'). '+r['title']+'. '+r['journal']+'. https://doi.org/'+r['doi'])+'</p><button type="button" data-copy-citation="citation-text">Copy citation</button><p id="copy-citation-status" role="status" class="v3-small"></p><p class="v3-small">This page is an editorial research brief, not the complete author-written abstract or full article. Full publication text and access conditions are available from the publisher.</p>')
  s.main.append(fragment(block));save(name,s)
 return records


PROJECTS=[
 ('project-robot-virtual-agent.html','3501','2026–2029','Physical agent vs. virtual agent',['Physical humanoid robot','Screen-based virtual agent','Active control condition'],'Mixed-methods comparison in middle-school environmental learning. These are the comparison conditions stated in the project title, not a randomisation or recruitment diagram.'),
 ('project-space-debris.html','1002-A','2026–2027','Space-debris scaffolding',['Scaffolding approach A','Classroom problem-solving context','Scaffolding approach B'],'A classroom pilot comparing two scaffolding approaches. The labels A and B are explanatory placeholders; intervention specifications are not published here.'),
 ('project-vr-stem-vietnam.html','BAP','Completed','VR-supported STEM instruction',['VR-supported STEM in Türkiye','Achievement, attitudes, acceptance','Adaptability to Vietnam'],'Scope of the completed VR-supported STEM research project.'),
 ('project-vr-circulatory-system.html','BAP','Completed','Circulatory-system learning',['Virtual-reality science learning','Circulatory-system unit','Achievement, self-efficacy, engagement'],'Scope of the completed VR-supported science learning project.')]

def projects():
 s=load('projects.html')
 for i,c in enumerate(s.select('.project-summary')):c['data-programme']=PROJECTS[i][1]
 grid=s.select_one('.project-overview-grid')
 grid.insert_before(fragment('<div class="v3-topic-filter"><label for="project-programme">Funding programme</label><select id="project-programme"><option value="all">All programmes</option><option>3501</option><option>1002-A</option><option>BAP</option></select><span id="project-filter-status" role="status">4 projects shown</span></div>'))
 status='<p>Funding and project periods are listed separately from study progress. Recruitment, data collection, analysis and completion are not inferred where no current project update has been supplied.</p><div class="v3-table-wrap"><table class="v3-table"><caption>Selected project register · 12 November 2026</caption><thead><tr><th scope="col">Project</th><th scope="col">Programme</th><th scope="col">Period</th><th scope="col">Record</th></tr></thead><tbody>'
 for name,prog,period,title,arms,note in PROJECTS:status+=f'<tr><th scope="row"><a href="{name}">{title}</a></th><td>{prog}</td><td>{period}</td><td>Funded project; current phase not published</td></tr>'
 status+='</tbody></table></div>';s.main.append(fragment(section('Project register & evidence status',status)));save('projects.html',s)
 for name,prog,period,title,arms,note in PROJECTS:
  s=load(name);diagram='<div class="v3-flow"><h2>Research overview</h2><ol>'+''.join('<li><strong>'+e(a)+'</strong></li>' for a in arms)+'</ol><p class="v3-small">'+e(note)+'</p></div>'
  s.main.find('section',recursive=False).insert_after(fragment('<section class="section"><div class="container">'+diagram+'</div></section>'))
  for dt in s.select('dt'):
   if dt.get_text(strip=True)=='Identifier' and dt.find_next_sibling('dd') and '3501' in dt.find_next_sibling('dd').get_text():dt.string='Programme'
  save(name,s)


def timeline_and_framework():
 milestones=[('2019','Doctoral foundation','PhD in Elementary Education, Middle East Technical University.','about.html'),('2020','Environmental behaviour','Published work connects planned behaviour and value-identity-personal-norm perspectives.','https://doi.org/10.1016/j.spc.2020.07.006'),('2023','Academic appointment & technology adoption','Associate professorship begins; selected research addresses augmented-reality adoption in science courses.','https://doi.org/10.1007/s10639-022-11239-6'),('2024','Self-regulated science learning','A study examines self-regulation within flipped science learning.','study-self-regulated-flipped-learning.html'),('2025','Augmented reality & tutoring','Research investigates augmented reality integrated with intelligent tutoring.','study-ar-intelligent-tutoring.html'),('2026','Human–AI feedback & independent reasoning','Multisite comparison of feedback designs and delayed AI-free transfer; selected funded work also addresses robotics and STEM learning.','study-genai-feedback.html')]
 timeline='<ol class="v3-timeline">'+''.join(f'<li><time>{y}</time><h2>{title}</h2><p>{text}</p><a href="{url}">Related record →</a></li>' for y,title,text,url in milestones)+'</ol><p class="v3-small">An editorial selection of appointments and publications, not a comprehensive career chronology or a causal account of research development.</p>'
 newpage('research-timeline.html','Research timeline','A dated route through selected research questions, publications and academic milestones.',section('From research questions to evidence',timeline))
 blocks=[('reasoning','Scientific reasoning','What makes a claim warranted? Examine evidence, explanatory alternatives and the limits of a conclusion.','resource-argumentation.html'),('regulation','Self-regulated learning','Who monitors progress and decides how to revise? Make planning, checking and reflection explicit.','resource-self-regulation.html'),('feedback','Human–AI feedback','What evaluative work remains with the learner? Compare external suggestions against criteria before accepting, adapting or rejecting them.','resource-feedback.html')]
 framework='<div class="v3-frame" data-framework><div class="v3-links">'+''.join(f'<button type="button" data-panel="framework-{k}" aria-controls="framework-{k}" aria-expanded="true">{title}</button>' for k,title,text,url in blocks)+'</div>'+''.join(f'<article id="framework-{k}"><h3>{title}</h3><p>{text}</p><a href="{url}">Explore associated resources →</a></article>' for k,title,text,url in blocks)+'</div><p class="v3-small">A conceptual reading guide to the research programme, not a validated causal model or an assessment instrument.</p>'
 append_main('research.html',section('Explore the research connections',framework)+section('Follow the programme over time',links([('Research timeline','research-timeline.html'),('Funded project register','projects.html'),('Methods & resources','open-research.html')])))
 append_main('about.html',section('Selected research milestones',links([('View research timeline','research-timeline.html')])))


def methods():
 code='''"""Synthetic comparison: descriptive quantities only, not an intervention analysis."""\nimport csv\nfrom pathlib import Path\n\nrows = list(csv.DictReader((Path(__file__).parent / 'fictional-plant-data.csv').open()))\nfor row in rows:\n    gain = float(row['final_height_cm']) - float(row['initial_height_cm'])\n    print(f"{row['group']}: observed growth = {gain:.1f} cm")\nprint('Both light and water differ. These fictional observations do not isolate either effect.')\nassert len(rows) == 2\n'''
 (DL/'inspect_synthetic_example.py').write_text(code,encoding='utf-8')
 (DL/'fictional-plant-data.csv').write_text('group,light_hours_per_day,water_ml_per_day,initial_height_cm,final_height_cm,growth_cm_over_week,plants_per_condition\nA,4,20,10,12,2,1\nB,8,40,10,15,5,1\n',encoding='utf-8')
 (DL/'methods-example-README.txt').write_text('Educational demonstration only. The values are fictional, not study observations. This is the same one-week example used by the Feedback Design Explorer: A receives 4 h of light and 20 mL of water per day and grows 2 cm; B receives 8 h and 40 mL and grows 5 cm. Each group contains one plant; both start at 10 cm. Run with Python 3: python inspect_synthetic_example.py. Group A and B differ on two conditions; their growth difference cannot identify the effect of light alone. No inferential statistics or reliability estimates are computed. Terms: '+BASE+'resource-use.html',encoding='utf-8')
 with zipfile.ZipFile(DL/'synthetic-methods-example.zip','w',zipfile.ZIP_DEFLATED) as z:
  for fn in ['inspect_synthetic_example.py','fictional-plant-data.csv','methods-example-README.txt','variable-dictionary-template.csv']:z.write(DL/fn,fn)
 append_main('open-research.html','<section class="section" id="methods-kit"><div class="container">'+box('A reproducible, synthetic example','<p>Download a small Python example, an explicitly fictional dataset, a data-dictionary template and instructions. The code reports descriptive growth only and demonstrates why changing both light and water prevents a single-factor causal conclusion.</p>'+links([('Methods example · ZIP','downloads/synthetic-methods-example.zip'),('Python source','downloads/inspect_synthetic_example.py'),('Fictional data · CSV','downloads/fictional-plant-data.csv')])+'<pre class="v3-code"><code>python inspect_synthetic_example.py\n# A: observed growth = 2.0 cm\n# B: observed growth = 5.0 cm\n# No single-factor causal effect is identified.</code></pre><p class="v3-small">This is not a participant dataset, research analysis script, preregistration or validated coding protocol.</p>')+'</div></section>')


def people_records():
 entries={
 'person-abdulkadir-aydin.html':[('Academic relationship','Doctoral supervision'),('Principal supervisor','Hüseyin Ateş'),('Expected completion','2028')],
 'person-tugce-unsal.html':[('Academic relationship','Master’s supervision'),('Research focus','Zimmerman-based self-regulation support in scenario-based science learning'),('Expected completion','Mid-2027')],
 'person-nisa-gul.html':[('Academic relationship','Master’s supervision'),('Research focus','Science teachers’ intentions to use humanoid robots for environmental topics'),('Framework stated in thesis title','GETAMEL'),('Expected completion','Mid-2027')],
 'person-kubra-solmaz.html':[('Academic relationship','Completed master’s supervision'),('Completion year','2024'),('Research focus','Teachers’ intentions regarding AI-based augmented reality in science classes')],
 'person-rabia-ates.html':[('Academic relationship','Completed master’s supervision'),('Completion year','2023'),('Research focus','A conceptual model of teachers’ intentions to use VR in science teaching')],
 'person-fatma-gazioglu.html':[('Academic relationship','Completed master’s supervision'),('Completion year','2022'),('Research focus','Teachers’ self-efficacy beliefs toward science education')],
 'person-ipek-oz.html':[('Academic relationship','Completed master’s supervision'),('Completion year','2022'),('Method stated in thesis title','Structural equation modelling'),('Research focus','Teachers’ intentions to use distance-education tools')]
 }
 for name,fields in entries.items():
  rows='<dl class="v3-meta">'+''.join('<dt>'+e(k)+'</dt><dd>'+e(v)+'</dd>' for k,v in fields)+'</dl>'
  append_main(name,section('Academic research record',rows+'<p class="v3-small">Expected completion dates are plans, not awarded degrees. Supervision does not establish employment or assignment to a funded project.</p>'+links([('Supervisor’s public CV','downloads/Huseyin_Ates_Public_Academic_CV.pdf'),('Research methods & materials','open-research.html')])))


def branding():
 assets=SITE/'assets';fontdir=Path('/usr/share/fonts/truetype/dejavu')
 image=Image.new('RGB',(1200,630),'#f6f7f1');d=ImageDraw.Draw(image)
 d.rectangle((0,0,1200,20),fill='#153746');d.rectangle((790,20,1200,630),fill='#dfece6')
 def text(x,y,t,size,bold=False,color='#153746'):d.text((x,y),t,font=ImageFont.truetype(str(fontdir/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size),fill=color)
 text(68,84,'HÜSEYİN ATEŞ',44,True);text(70,151,'SCIENCE EDUCATION · HUMAN–AI LEARNING',17,True,'#146671')
 text(68,245,'Learning with AI.',45);text(68,309,'Thinking for ourselves.',45)
 text(70,506,'Research  /  People  /  Teaching resources',21);text(70,556,'huseyinates38.github.io',19,False,'#49616a')
 for y,num,label in [(160,'01','Reason'),(295,'02','Evaluate'),(430,'03','Revise')]:
  d.rounded_rectangle((830,y-18,1136,y+76),radius=2,fill='white');text(850,y,num,25,True,'#146671');text(925,y+2,label,23)
 image.save(assets/'social-card.png',optimize=True)
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#153746"/><text x="32" y="42" text-anchor="middle" font-family="Arial,sans-serif" font-size="28" font-weight="bold" fill="white">HA</text><circle cx="51" cy="49" r="3" fill="#e6ad7c"/></svg>'
 (assets/'favicon.svg').write_text(svg,encoding='utf-8')
 icon=Image.new('RGB',(128,128),'#153746');di=ImageDraw.Draw(icon);di.text((14,36),'HA',font=ImageFont.truetype(str(fontdir/'DejaVuSans-Bold.ttf'),58),fill='white');icon.save(assets/'favicon.png')
 (assets/'v3.css').write_text(CSS,encoding='utf-8');(assets/'v3.js').write_text(JS,encoding='utf-8')


def accessibility_page():
 body='<p>The interface is designed for keyboard operation, visible focus, responsive reflow and reduced-motion preferences. Downloadable PDFs contain searchable text; DOCX files use headings. The HTML resource pages remain the primary reading alternative.</p><p>Release checks inspect local links, heading counts, labelled controls, image alternatives, metadata and generated files. Automated checks cannot establish complete WCAG conformance. PDF/UA tagging and an independent screen-reader audit have not been completed.</p><p>Report access difficulties to <a href="mailto:huseyin.ates@ahievran.edu.tr">huseyin.ates@ahievran.edu.tr</a>, including the page address, device and assistive technology.</p>'
 newpage('accessibility.html','Accessibility & site quality','Access features, testing scope and a direct route for reporting problems.',section('Access without overclaiming',body)+section('Privacy & external services','<p>No analytics, advertising, tracking cookies, application form or live AI API is installed. Interactive controls run locally and do not store student responses. GitHub Pages and any external pages you follow have their own technical-access and privacy practices.</p>'+links([('Sources and content notes','site-notes.html'),('Resource-use terms','resource-use.html')])) )


def global_updates():
 same=[u for _,u in PROFILES]
 for path in SITE.glob('*.html'):
  s=load(path.name)
  # Remove stale publisher metadata from cloned pages, retaining article tags only on actual briefs.
  if not path.name.startswith('study-'):
   for tag in s.head.select('meta[name^="citation_"]'):tag.decompose()
  for tag in s.head.select('link[rel="canonical"],meta[property^="og:"],meta[name="twitter:card"]'):tag.decompose()
  s.head.append(s.new_tag('link',rel='canonical',href=BASE+path.name))
  for prop,val in [('og:type','website'),('og:description',s.head.find('meta',attrs={'name':'description'})['content']),('og:url',BASE+path.name),('og:title',s.title.get_text()),('og:image',BASE+'assets/social-card.png'),('og:image:width','1200'),('og:image:height','630'),('og:image:alt','Hüseyin Ateş — Learning with AI. Thinking for ourselves.')]:s.head.append(s.new_tag('meta',attrs={'property':prop,'content':val}))
  s.head.append(s.new_tag('meta',attrs={'name':'twitter:card','content':'summary_large_image'}))
  s.head.append(s.new_tag('link',rel='icon',href='assets/favicon.svg',type='image/svg+xml'))
  s.head.append(s.new_tag('link',rel='apple-touch-icon',href='assets/favicon.png'))
  s.head.append(s.new_tag('link',rel='stylesheet',href='assets/v3.css'))
  script=s.new_tag('script',src='assets/v3.js',defer='');s.head.append(script)
  if path.name=='about.html':
   graph={'@context':'https://schema.org','@type':'ProfilePage','mainEntity':{'@type':'Person','name':'Hüseyin Ateş','jobTitle':'Associate Professor of Science Education','affiliation':{'@type':'CollegeOrUniversity','name':'Kırşehir Ahi Evran University'},'url':BASE+'about.html','sameAs':same}}
   tag=s.new_tag('script',type='application/ld+json');tag.string=json.dumps(graph,ensure_ascii=False);s.head.append(tag)
  for a in s.select('a[target="_blank"]'):a['rel']=['noopener','noreferrer']
  if s.footer:
   s.footer.append(fragment('<div class="container v3-links"><a href="research-timeline.html">Research timeline</a><a href="accessibility.html">Accessibility</a><a href="resource-use.html">Resource use</a><a href="downloads/Huseyin_Ates_Public_Academic_CV.pdf">Academic CV · PDF</a></div>'))
  save(path.name,s)
 # Local fonts prevent third-party requests and avoid distributing any font files.
 for css in (SITE/'assets').glob('*.css'):
  text=css.read_text();text=re.sub(r"@import\s+url\([^;]+;",'',text)
  css.write_text(text,encoding='utf-8')
 manifest=json.loads((SITE/'deployment.json').read_text());manifest.update(version=VERSION,updated=DATE,pages=sorted(p.name for p in SITE.glob('*.html')),downloads=sorted(p.relative_to(SITE).as_posix() for p in DL.iterdir() if p.is_file()))
 manifest['page_count']=len(manifest['pages']);manifest.pop('files',None)
 (SITE/'deployment.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 urls=''.join('<url><loc>'+BASE+p+'</loc><lastmod>'+DATE+'</lastmod></url>' for p in manifest['pages'] if p!='404.html')
 (SITE/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>',encoding='utf-8')
 print('Website v3:',manifest['page_count'],'pages and',len(manifest['downloads']),'downloads')


def main():
 identity();teaching();publication_tools();projects();timeline_and_framework();methods();people_records();branding();accessibility_page();global_updates()

if __name__=='__main__':main()
