#!/usr/bin/env python3
"""Build the current editorial release over the preserved v3.1 source templates.
Current status overrides live in content/editorial-update.json and research-pipeline.json.
Never publish the root input templates directly: publish only the validated _site output.
"""
from pathlib import Path
import copy,json
from html import escape as e
import build_site as base
import build_professional_docs as docs
import build_v3
import build_v32
import build_v31

ROOT=Path(__file__).resolve().parents[1]
UPDATE=json.loads((ROOT/'content/editorial-update.json').read_text())


def people():
    leader='<div class="team-leader"><div class="leader-badge" aria-hidden="true">HA.</div><div><p class="eyebrow">Principal investigator / Research supervisor</p><h2>Hüseyin Ateş, <em>PhD</em></h2><p>Associate Professor of Science Education at Kırşehir Ahi Evran University. Research connects human-centered AI, scientific reasoning, self-regulated learning and emerging technologies in STEM education.</p>'+base.link('Academic biography & CV','about.html')+'</div></div>'
    groups=[('collaborators','Research collaborators','collaborators'),('editorial','Editorial collaboration','editorial-collaborators'),('graduate','Graduate researchers','graduate-researchers'),('alumni','Research alumni','alumni')]
    nav='<nav class="subnav" aria-label="People sections">'+''.join(base.link(title,'#'+id_) for _,title,id_ in groups)+'</nav>'
    body=base.hero('People / Research Team','Research grows through <em>people.</em>','Research and editorial collaborators first, followed by current graduate researchers and research alumni.',nav)+base.section(leader,'white','leadership')
    for group,title,id_ in groups:
        cards=[]
        for p in UPDATE['people']:
            if p['group']!=group:continue
            url='person-'+p['slug']+'.html'
            cards.append('<article class="person-card"><div class="person-top"><span class="person-monogram" aria-hidden="true">'+e(p['initials'])+'</span><div><p class="micro-label">'+e(p['role'])+'</p><h3>'+e(p['name'])+'</h3></div></div><p class="person-topic">'+e(p['topic'])+'</p>'+base.link('View profile',url)+'</article>')
            detail=base.section('<div class="profile-layout"><div class="profile-avatar" aria-hidden="true">'+e(p['initials'])+'</div><div><p class="eyebrow">Documented academic connection</p><h2>'+e(p['topic'])+'</h2><p class="lead">'+e(p['description'])+'</p><p>'+e(p['detail'])+'</p><h3>Explore connected work</h3><div class="profile-links">'+''.join(base.link(a,b) for a,b in p['links'])+'</div></div></div>','white')
            base.render(url,p['name'],'team.html',base.hero(p['role'],e(p['name']),e(p['topic']))+detail+base.section(base.action('Back to people','team.html',True)),p['name']+' — '+p['topic'])
        explanation='<p class="team-intro">Collaboration describes the stated research or editorial relationship; it does not imply employment in the same institution or appointment to a funded project.</p>' if group in ['collaborators','editorial'] else ''
        body+=base.section('<p class="eyebrow">'+('Current supervision' if group=='graduate' else 'Academic connections')+'</p><h2>'+e(title)+'</h2>'+explanation+'<div class="people-grid">'+''.join(cards)+'</div>','white' if group in ['editorial','alumni'] else 'muted',id_)
    base.render('team.html','People & Research Team','team.html',body+base.section(base.action('Explore working together','join.html')),'Research collaborators, editorial connections, graduate researchers and alumni.')


def main():
    base.people=people
    base.main()
    # The original CV classification is superseded by the owner's explicit correction.
    docs.CV=copy.deepcopy(docs.CV)
    docs.CV[0]=[(kind,text) for kind,text in docs.CV[0] if 'TÜBİTAK 3501:' not in text]
    for page in docs.CV:
        for i,(kind,text) in enumerate(page):
            if 'This public selection excludes manuscripts under review and proposals awaiting decisions.' in text:
                page[i]=(kind,'This public selection omits unpublished manuscript details. Submitted and planned proposals are listed separately on page 3 and are not funding awards. Publication records: '+base.BASE+'publications.html')
    docs.CV.append([tuple(row) for row in UPDATE['cv_proposals_page']])
    docs.main()
    build_v3.main()
    build_v32.main()
    build_v31.VERSION='3.2'
    original_category=build_v31.category
    build_v31.category=lambda name: ('research','Research & projects') if name in ['proposals.html','editorial.html'] or name.startswith('proposal-') else original_category(name)
    original_fragment=build_v31.fragment
    def current_fragment(text):
        return original_fragment(text.replace('Website release 3.1 focuses on navigation and interface reliability.','Website release 3.2 separates supported projects, ongoing studies, submitted proposals and planned applications, with collaborators shown before graduate researchers.'))
    build_v31.fragment=current_fragment
    build_v31.main()
    print('Editorial release 3.2 prepared. No private correspondence is included.')

if __name__=='__main__':main()
