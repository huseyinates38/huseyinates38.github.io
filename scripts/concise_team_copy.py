#!/usr/bin/env python3
"""Consolidate real shared-team memberships and remove redundant on-page copy."""
from bs4 import BeautifulSoup as Soup

def pick(en, tr, lang):
    return tr if lang == 'tr' else en

def plain(tag):
    return tag.get_text(' ', strip=True) if tag else ''

def polish(docs, config, lang):
    team = docs['team.html']
    groups = {}
    for key in ('3501','aub-stem'):
        el = team.select_one('#project-team-' + key)
        if not el:
            raise ValueError('Missing team ' + key)
        groups[key] = el

    # A shared person appears in both project groups and needs two links in one profile.
    yesim = docs['person-yesim-taktat-ates.html']
    facts = yesim.select_one('#academic-record dl.profile-facts')
    if facts is None:
        raise ValueError('Yeşim profile facts missing')
    existing = facts.select_one('[data-project-record="study"]')
    if not existing:
        raise ValueError('Yeşim profile has no application record')
    dt = existing.select_one('dt')
    dd = existing.select_one('dd')
    dt.string = pick('Related studies / applications','İlgili çalışmalar / başvurular',lang)
    dd.clear()
    ul = yesim.new_tag('ul',attrs={'class':'related-studies'})
    for team_id, url in (('3501','project-robot-virtual-agent.html'), ('aub-stem','proposal-turkiye-uae-stem.html')):
        li = yesim.new_tag('li')
        a = yesim.new_tag('a',href=url)
        a.string = plain(groups[team_id].select_one('.project-team-head h3'))
        li.append(a); ul.append(li)
    dd.append(ul)
    stage= facts.select_one('[data-project-record="stage"]')
    if stage is None:
        raise ValueError('Missing shared application stage')
    stage.dt.string = pick('Application stages','Başvuruların aşaması',lang)
    # Both source applications have the same pending status; show it only once.
    stage.dd.string = plain(docs['proposal-turkiye-uae-stem.html'].select_one('.status-pill'))

    # Project identity is already in the group heading and stage is in the group label.
    for team_id, group in groups.items():
        for card in group.select('.person-card[data-person]'):
            slug=card['data-person']
            role=card.select_one('.micro-label')
            if role:
                raw=plain(role)
                for suffix in (' · TÜBİTAK 3501',' · AÜB proposal team',' · AÜB başvuru ekibi'):
                    raw=raw.replace(suffix,'')
                if slug=='yesim-taktat-ates':
                    raw=pick('Independent researcher','Bağımsız araştırmacı',lang)
                role.string=raw
            for redundant in card.select('.relationship-stage'):
                redundant.decompose()
            if team_id=='3501' or slug=='yesim-taktat-ates':
                for topic in card.select('.person-topic'):
                    topic.decompose()

    # In researcher profiles the same role, focus and current stage often appear twice.
    for name, s in docs.items():
        if not name.startswith('person-'):
            continue
        slug=name[7:-5]
        facts=s.select_one('#academic-record dl.profile-facts')
        hero=s.select_one('main .pagehero')
        if not facts or not hero:
            continue
        eyebrow=hero.select_one('.eyebrow')
        lead=hero.select_one('p.lead')
        group_person=bool(facts.select_one('[data-project-record="study"]'))
        if group_person and lead and (slug in ('yesim-taktat-ates','ipek-oz') or '3501' in plain(lead)):
            lead.decompose(); lead=None
        if slug=='ipek-oz' and eyebrow:
            eyebrow.string=pick('Researcher · Expert teacher','Araştırmacı · Uzman öğretmen',lang)
        if slug=='yesim-taktat-ates' and eyebrow:
            eyebrow.string=pick('Independent researcher','Bağımsız araştırmacı',lang)
        for div in list(facts.find_all('div',recursive=False)):
            label=plain(div.find('dt'))
            value=plain(div.find('dd'))
            if label in ('Current stage','Güncel aşama') and group_person:
                div.decompose()
            elif label in ('Research focus','Araştırma odağı') and (
                (lead and value==plain(lead)) or
                (group_person and (slug in ('ipek-oz','yesim-taktat-ates') or '3501' in value))):
                div.decompose()
            elif label in ('Role / academic relationship','Rol / akademik ilişki') and eyebrow and value==plain(eyebrow):
                div.decompose()
        for b in hero.select('.relationship-stage'):
            b.decompose()
        if group_person:
            links={a['href'] for a in facts.select('[data-project-record="study"] a[href]')}
            for a in list(s.select('.profile-summary a.textlink')):
                if a.get('href') in links:
                    a.decompose()
        # The facts already show the verified affiliation and the documented
        # contribution; the summary paragraph repeats them without new evidence.
        if slug in set(config['profile_contributions']) | {'yesim-taktat-ates','ipek-oz'}:
            intro=s.select_one('.profile-summary p.lead')
            if intro:
                intro.decompose()

    robot=docs['project-robot-virtual-agent.html']
    aub=docs['proposal-turkiye-uae-stem.html']
    for page in (robot,aub):
        layout=page.select_one('.proposal-layout')
        if layout:
            intro=layout.select_one('p.lead')
            if intro and intro.find_next_sibling('p'):
                intro.decompose()
    # The 3501 collaboration subsection repeats the pending status already
    # presented in the hero and the proposal's structured status record.
    for sec in list(robot.select('main > section')):
        h=sec.select_one('h2')
        if h and plain(h) in ('Collaboration & current position','İş birliği ve güncel durum'):
            if sec.select('a[href]'):
                raise ValueError('Unexpected links in duplicate 3501 status subsection')
            sec.decompose()
    # Retain the distinct academic relationship on the AÜB proposal page,
    # but remove its duplicate pending/funding caveat.
    for sec in aub.select('main > section'):
        h=sec.select_one('h2')
        if h and plain(h) in ('Collaboration & current position','İş birliği ve güncel durum'):
            for item in sec.select('aside.callout'):
                item.decompose()
    # The source team notes should no longer repeat the PI and decision stage.
    for page in (team,robot):
        prose=plain(page.main)
        if ('Yürütücü / başvuru sahibi: Hüseyin Ateş. Öneri yeniden sunulmuştur' in prose or
            'Research lead / applicant: Hüseyin Ateş. The proposal has been resubmitted' in prose):
            raise ValueError('Duplicate 3501 project note is still visible')
