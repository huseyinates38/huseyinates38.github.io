#!/usr/bin/env python3
"""Question-specific public-record answers, built after the assistant UI gates.
No private sources, provider credentials, external prompt calls or automatic model
loading. Scripted factual answers are visibly distinct from experimental generation.
"""
from pathlib import Path
import hashlib, json, re, shutil
from bs4 import BeautifulSoup as Soup

ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'_site'

def text(el): return el.get_text(' ',strip=True) if el else ''
def facts(s):
    result={}
    for dt in s.select('dt'):
        dd=dt.find_next_sibling('dd')
        if dd: result[text(dt)]=text(dd)
    return result

def field(values,*keys):
    return next((values[k] for k in keys if k in values),'')

def records(docs,lang):
    team=docs['team.html']; persons={}; projects={}
    for name,s in docs.items():
        if not name.startswith('person-') or name=='person-tugce-unsal.html': continue
        f=facts(s); slug=name[7:-5]
        people=team.select(f'[data-person="{slug}"]')
        role=field(f,'Rol','Role','Role / academic relationship','Rol / akademik ilişki')
        if not role: role=text(people[0].select_one('.micro-label')) if people else text(s.select_one('.pagehero .eyebrow'))
        affiliations=list(dict.fromkeys(text(a) for a in s.select('.institution-name')))
        studies=[{'title':text(a),'url':a['href']} for a in s.select('[data-project-record="study"] a[href]')]
        # Store public contribution fields only, never infer a task from a job title.
        contribution=field(f,'Önerilen katkı','Proposed contribution') or text(s.select_one('[data-profile-contribution]'))
        persons[slug]={'name':text(s.main.h1),'url':name,'role':role,'institutions':affiliations,
                      'studies':studies,'stage':field(f,'Başvuru aşaması','Başvuruların aşaması','Application stage','Application stages','Güncel aşama','Current stage'),
                      'contribution':contribution,'focus':field(f,'Araştırma odağı','Research focus') or text(s.select_one('.pagehero p.lead')),
                      'degree':field(f,'Tamamlanan derece','Completed degree')}
    for key,page in [('3501','project-robot-virtual-agent.html'),('aub','proposal-turkiye-uae-stem.html'),
                     ('1002','project-space-debris.html'),('2219','proposal-feedback-fading.html'),
                     ('2221','proposal-visiting-researchers-2221.html'),('cost','proposal-sciepi-feedback.html'),
                     ('erc','proposal-reclaim.html'),('dfg','proposal-tubitak-dfg-reasoning.html')]:
        s=docs[page]; f=facts(s); group=team.select_one('#project-team-'+('aub-stem' if key=='aub' else key))
        people=[]
        if group:
            for p in group.select('.person-card[data-person]'):
                slug=p['data-person']; person=persons[slug]
                people.append({'name':person['name'],'role':text(p.select_one('.micro-label')),'slug':slug})
            # AÜB's additional reviewed member appears as a profile link in its note.
            for a in group.select('.project-team-note a[href^="person-"]'):
                slug=a['href'][7:-5]
                if slug in persons and not any(x['slug']==slug for x in people):
                    people.append({'name':persons[slug]['name'],'role':'Araştırmacı' if lang=='tr' else 'Researcher','slug':slug})
        date=s.select_one('.proposal-side time')
        status=text(s.select_one('.pagehero .status-pill')) or field(f,'Destek durumu','Funding status','Güncel durum','Current status')
        if key=='1002':
            status=text(s.select_one('.project-meta .funding-stage span'))
            if not status:raise ValueError('Missing 1002 funding stage in public project metadata')
        projects[key]={'title':text(s.main.h1),'url':page,'summary':text(s.select_one('.pagehero p.lead')),
                       'stage':status,'reviewed':text(date),'members':people,
                       'lead':field(f,'Araştırma sorumlusu / rol','Research lead / role','Lead / role','Principal investigator'),
                       'duration':field(f,'Önerilen süre / ziyaret','Proposed duration / visit')}
    research=docs['research.html']; publications=[]
    for p in docs['publications.html'].select('.publication'):
        publications.append({'title':text(p.select_one('h3')),'year':text(p.select_one('.year')),
                             'citation':text(p),'url':'publications.html'})
    contact=docs['contact.html']
    emails=list(dict.fromkeys(a['href'][7:].split('?')[0] for a in contact.select('a[href^="mailto:"]')))
    return {'lang':lang,'people':persons,'projects':projects,'email':emails[0] if emails else '',
            'publications':publications,'research_topics':[text(h) for h in research.select('.research-theme-grid h3')],
            'research_intro':text(research.select_one('.pagehero .lead')),
            'about':text(docs['about.html'].select_one('.pagehero p'))}

def patch_js(source):
    marker='/* question-specific public-record answer layer */'
    if marker in source:return source
    source=source.replace("const input=$('chat-question')", "const quality=window.AcademicAnswerEngine?.create(JSON.parse($('assistant-facts').textContent),corpus);\n const input=$('chat-question')",1)
    source=source.replace('function retrieve(question){','function retrieve(question){\n  if(quality)return quality.retrieve(question);',1)
    anchor="  const contact=/"
    if anchor not in source:raise ValueError('Submit hook not found')
    insertion="""  const answer=quality?.answer(q);
  if(answer){
   const m=message('assistant',answer.text,pick('Website record answer','Site kayıtlarından yanıt'));
   refs(m.article,answer.sources||[]);announce(pick('Answer completed from public records.','Yanıt açık site kayıtlarından hazırlandı.'));scroll();return;
  }
"""
    source=source.replace(anchor,insertion+anchor,1)
    source=source.replace("  for(const r of records.slice(0,2)){m.body.append(el('p','chat-excerpt',r.text.slice(0,780)+(r.text.length>780?'…':'')));}",
        "  for(const r of records.slice(0,2)){m.body.append(el('p','chat-excerpt',quality?quality.excerpt(r,question):r.text.slice(0,780)));}",1)
    source=source.replace("const contextual=q.length<70&&state.history.length?", "const contextual=!quality&&q.length<70&&state.history.length?",1)
    source=source.replace("Reply in ${language} in 3–6 short sentences.","Reply naturally in ${language}. Start with a direct answer; use only the detail the question requires. Do not repeat titles, role labels or disclaimers. Use a complete roster when asked for a team, not an incomplete sample.")
    source=source.replace('r.text.slice(0,1100)', '(quality?quality.excerpt(r,state.lastQuestion,1800):r.text.slice(0,1100))')
    source=source.replace("state.history=[];state.reply=null", "state.history=[];quality?.reset();state.reply=null")
    source=source.replace("pick('Website source mode','Site kaynakları modu')", "pick('Website record answers','Site kayıtlarından yanıt')")
    return marker+'\n'+source

def main():
    shutil.copy2(ROOT/'assets/academic-answer-engine.js',SITE/'assets/academic-answer-engine.js')
    mainjs=SITE/'assets/academic-assistant.js'; mainjs.write_text(patch_js(mainjs.read_text()),encoding='utf-8')
    js_hash=hashlib.sha256(mainjs.read_bytes()).hexdigest()[:12]
    engine_hash=hashlib.sha256((ROOT/'assets/academic-answer-engine.js').read_bytes()).hexdigest()[:12]
    counts={}
    for lang in ('en','tr'):
        folder=SITE/('tr' if lang=='tr' else ''); pre='../' if lang=='tr' else ''
        docs={p.name:Soup(p.read_text(),'html.parser') for p in folder.glob('*.html')}
        s=docs['assistant.html']; data=records(docs,lang);counts[lang]=len(data['people'])
        for old in s.select('#assistant-facts,script[src*="academic-answer-engine"]'):old.decompose()
        tag=s.new_tag('script',id='assistant-facts',type='application/json');tag.string=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
        main=s.select_one('script[src*="academic-assistant.js"]');main['src']=pre+'assets/academic-assistant.js?v='+js_hash
        main.insert_before(tag)
        engine=s.new_tag('script',src=pre+'assets/academic-answer-engine.js?v='+engine_hash,defer='');main.insert_before(engine)
        options=s.select_one('#ai-model-options')
        options.h2.string='Deneysel üretken mod' if lang=='tr' else 'Experimental generation'
        notice=s.new_tag('p',attrs={'class':'chat-answer-note','data-quality-disclosure':''})
        notice.string=('Ekip, proje ve iletişim yanıtları doğrulanmış site kayıtlarından hazırlanır; bunlar model üretimi değildir. Aşağıdaki küçük model yalnızca diğer sorular için deneysel bir seçenektir; yanıt kalitesi sınırlıdır.' if lang=='tr' else
                       'Team, project and contact answers are composed from verified website records, not generated by a model. The small model below is an experimental option for other questions; answer quality is limited.')
        for old in options.select('[data-quality-disclosure]'):old.decompose()
        options.h2.insert_after(notice)
        link=s.select_one('.chat-ai-link');link.string='Deneysel mod' if lang=='tr' else 'Experimental mode'
        s.select_one('#chat-mode').string='Site kayıtlarından yanıt' if lang=='tr' else 'Website record answers'
        # Replace the old "excerpts only" promise, now obsolete for structured records.
        for p in options.select('p'):
            if text(p).startswith(('Model açılmadan sohbet','Without the model, the chat')):
                p.string=('Model olmadan da ekip, proje, araştırma ve iletişim sorularına kaynaklı yanıt alabilirsiniz. Bu yanıtlar site verileri ve önceden yazılmış yanıt kurallarıyla hazırlanır.' if lang=='tr' else
                          'Team, project, research and contact questions can be answered without the model. These answers use website data and predefined response rules.')
        (folder/'assistant.html').write_text(str(s),encoding='utf-8')
    report={'result':'built','profile_records':counts,'model_changed':False,'generated_answer_quality_validated':False,
            'method':'structured public data with explicit question routing; sentence-ranked retrieval fallback'}
    (ROOT/'assistant-quality-build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
if __name__=='__main__':main()
