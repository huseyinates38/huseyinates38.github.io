#!/usr/bin/env python3
"""Add restrained original illustrations and evidence-grounded highlights to the bilingual static site.
The release intentionally uses NO personal photographs, live feeds, guessed grant outcomes, or fabricated metrics.
This runs after build_team_directory.py so English and Turkish editorial copy is final.
"""
from pathlib import Path
from bs4 import BeautifulSoup as Soup
import json, shutil

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
DATE='2026-11-13'

def fragment(s,html):
    tmp=Soup(html,'html.parser')
    return next((x for x in tmp.contents if getattr(x,'name',None)),None)

def translations(tr):
    return (lambda en,tu: tu if tr else en)

def visual_intro(s,tr,prefix):
    f=translations(tr)
    old=s.select_one('.home-hero .hero-panel')
    if not old:raise RuntimeError('Missing home hero aside')
    visuals=f('A visual interpretation of research in human-centered AI and science education. Not a photograph of a study.','İnsan odaklı yapay zekâ ve fen eğitimi çalışmalarını anlatan temsili bir illüstrasyon; gerçek bir araştırma fotoğrafı değildir.')
    html=f'''<aside class="visual-hero" aria-label="{f('Research illustration','Araştırma illüstrasyonu')}">
    <figure class="visual-hero-figure">
       <img src="{prefix}assets/visuals/research-hero.webp" width="911" height="316" alt="{visuals}" decoding="async" fetchpriority="high"/>
       <figcaption><span class="visual-kicker">{f('THE RESEARCH QUESTION','ARAŞTIRMA SORUSU')}</span><strong>{f('Where does technology help us think more deeply?','Teknoloji, daha derin düşünmeye nasıl katkı sunar?')}</strong><small>{f('Conceptual illustration','Temsili illüstrasyon')}</small></figcaption>
    </figure>
    <div class="visual-hero-note" aria-label="{f('Research directions','Araştırma alanları')}">
       <span><b>01</b>{f('Human-centered AI','İnsan odaklı yapay zekâ')}</span>
       <span><b>02</b>{f('Scientific reasoning','Bilimsel akıl yürütme')}</span>
       <span><b>03</b>{f('Self-regulated learning','Öz düzenlemeli öğrenme')}</span>
    </div></aside>'''
    old.replace_with(fragment(s,html))

def topic_html(tr,prefix):
    f=translations(tr)
    topics=[
      ('ai-feedback.svg',f('Human-centered AI','İnsan odaklı yapay zekâ'),f('How can feedback strengthen the learner’s own judgement?','Geri bildirim, öğrencinin kendi değerlendirme becerisini nasıl güçlendirir?'),'research.html#human-centered-ai'),
      ('scientific-reasoning.svg',f('Scientific reasoning','Bilimsel akıl yürütme'),f('Evidence, explanations and warranted conclusions.','Kanıtlar, açıklamalar ve gerekçelendirilmiş sonuçlar.'),'research.html#reasoning'),
      ('stem-learning.svg',f('STEM learning','STEM eğitimi'),f('Inquiry, emerging technologies and learning design.','Sorgulama, yeni teknolojiler ve öğrenme tasarımı.'),'research.html#technologies')]
    cards=''.join(f'''<a class="visual-topic" href="{href}"><img src="{prefix}assets/visuals/{im}" width="600" height="320" alt="" loading="lazy" decoding="async"/><div class="visual-topic-content"><h3>{title}</h3><p>{desc}</p><span aria-hidden="true">↗</span></div></a>''' for im,title,desc,href in topics)
    return f'''<section class="visual-topics" aria-label="{f('Three research directions','Üç araştırma alanı')}"><div class="container"><div class="visual-section-top"><p class="eyebrow">{f('Explore the research','Araştırma alanlarını keşfedin')}</p><a class="visual-inline-link" href="research.html">{f('All research topics','Tüm araştırma alanları')} <span aria-hidden="true">↗</span></a></div><div class="visual-topic-grid">{cards}</div></div></section>'''

def updates_html(tr,prefix):
    f=translations(tr)
    items=[
        ('conference.svg',f('CONFERENCE · ORAL PRESENTATION','KONFERANS · SÖZLÜ SUNUM'),f('ICCAI 2027: presentation accepted','ICCAI 2027: sözlü sunum kabulü'),f('A science-teacher-education study was accepted for oral presentation at ICCAI 2027 in Seoul. The meeting is scheduled for April 2027.','Fen bilgisi öğretmenliği eğitiminde yapay zekâyı ele alan bildirimiz, Nisan 2027’de Seul’de düzenlenecek ICCAI 2027 için sözlü sunum olarak kabul edildi.'),'conference-iccai-2027.html'),
        ('orbital-inquiry.svg',f('RESEARCH GRANT · 1002-A','ARAŞTIRMA DESTEĞİ · 1002-A'),f('Scientific support for project 226K999','226K999 için bilimsel destek kararı'),f('The TÜBİTAK 1002-A space-pollution problem-solving pilot received a scientific funding decision; contractual procedures are separate.','Uzay kirliliği problem çözme öğretiminde iki pedagojik iskele yaklaşımını karşılaştıran 1002-A projesi için bilimsel destek kararı verildi; sözleşme işlemleri ayrı bir aşamadır.'),'project-space-debris.html'),
        ('open-learning.svg',f('OPEN TEACHING RESOURCES','ÖĞRETİM KAYNAKLARI'),f('Resources for reflective science learning','Fen öğrenimi için öğretim kaynakları'),f('Bilingual sample materials on feedback, scientific argumentation and self-regulated learning; these are teaching prototypes, not validated instruments.','Geri bildirim, bilimsel argümantasyon ve öz düzenlemeli öğrenme için Türkçe–İngilizce örnek materyaller. Bu içerikler öğretim amaçlıdır; geçerliği sınanmış ölçekler değildir.'),'resources.html')]
    cards=''.join(f'''<article class="visual-update"><a href="{href}" class="visual-update-media"><img src="{prefix}assets/visuals/{img}" alt="" width="600" height="320" loading="lazy" decoding="async"/></a><div class="visual-update-body"><span class="visual-update-type">{label}</span><h3><a href="{href}">{title}</a></h3><p>{desc}</p><a class="visual-readmore" href="{href}">{f('Read the record','Ayrıntıları incele')} <span aria-hidden="true">↗</span></a></div></article>''' for img,label,title,desc,href in items)
    return f'''<section class="visual-updates" id="selected-updates" aria-labelledby="visual-updates-title"><div class="container"><div class="visual-updates-heading"><div><p class="eyebrow">{f('November 2026 · Selected highlights','Kasım 2026 · Seçilmiş gelişmeler')}</p><h2 id="visual-updates-title">{f('From research to <em>practice.</em>','Araştırmadan <em>uygulamaya.</em>')}</h2><p>{f('Confirmed milestones and reusable learning materials—not a live news feed.','Doğrulanmış gelişmeler ve kullanılabilir öğretim materyalleri; anlık haber akışı değildir.')}</p></div><a class="visual-inline-link" href="projects.html">{f('Projects and activity','Projeler ve çalışmalar')} <span aria-hidden="true">↗</span></a></div><div class="visual-updates-grid">{cards}</div></div></section>'''

def join_html(tr,prefix):
    f=translations(tr)
    return f'''<section class="visual-join" aria-labelledby="visual-join-title"><div class="container visual-join-inner"><div class="visual-join-copy"><p class="eyebrow">{f('Working together','Birlikte araştırma')}</p><h2 id="visual-join-title">{f('Good research starts with <em>a shared question.</em>','İyi araştırma, <em>ortak bir soruyla</em> başlar.')}</h2><p>{f('Interested in research collaboration, teaching materials or a graduate project? Explore the group and share your interests through the existing form.','Araştırma iş birliği, öğretim materyalleri veya lisansüstü çalışma olanaklarıyla ilgileniyorsanız araştırma grubunu inceleyebilir, ilgi formu aracılığıyla bize ulaşabilirsiniz.')}</p><div class="buttonrow"><a class="btn visual-join-btn" href="https://tally.so/r/Eq51Jr" target="_blank" rel="noopener noreferrer">{f('Research-group interest form','Araştırma grubu ilgi formu')} <span aria-hidden="true">↗</span></a><a class="btn alt visual-join-outline" href="team.html">{f('Meet the people','Araştırma ekibini tanıyın')}</a></div></div><a class="visual-join-qr" href="https://tally.so/r/Eq51Jr" target="_blank" rel="noopener noreferrer" aria-label="{f('Open research group interest form','Araştırma grubu ilgi formunu aç')}"><img src="{prefix}assets/qr/research-group-interest.png" alt="{f('QR code for the research group interest form','Araştırma grubu ilgi formu için QR kodu')}" width="180" height="180" loading="lazy"/><span>{f('Scan to open the form','Formu açmak için okutun')}</span></a></div></section>'''

def research_gallery(tr,prefix):
    f=translations(tr)
    names=[('ai-feedback.svg',f('Feedback','Geri bildirim'),'#human-centered-ai'),('scientific-reasoning.svg',f('Reasoning','Akıl yürütme'),'#reasoning'),('stem-learning.svg',f('STEM','STEM eğitimi'),'#technologies')]
    return '<section class="visual-research-gallery" aria-label="'+f('Research themes','Araştırma temaları')+'"><div class="container"><div class="visual-research-gallery-grid">'+''.join(f'<a href="{href}"><img src="{prefix}assets/visuals/{img}" alt="" width="600" height="320" loading="lazy"/><strong>{label}</strong><span aria-hidden="true">↘</span></a>' for img,label,href in names)+'</div></div></section>'

def decorate(s,name,tr,prefix):
    if name=='index.html':
        visual_intro(s,tr,prefix)
        # Link the already-published interaction rather than inventing an automated chatbot.
        f=translations(tr)
        actions=s.select_one('.home-hero .buttonrow')
        actions.insert_after(fragment(s,'<a class="visual-explorer-link" href="feedback-explorer.html"><span class="visual-explorer-dot" aria-hidden="true"></span>'+f('Interactive example: compare three feedback approaches','Etkileşimli örnek: Üç geri bildirim yaklaşımını karşılaştırın')+' <span aria-hidden="true">↗</span></a>'))
        hero=s.select_one('.home-hero')
        hero.insert_after(fragment(s,topic_html(tr,prefix)))
        # Insert curated updates after the first topic-selection section, before the older featured-research section.
        old_section=s.select_one('main section.section.white')
        if not old_section:raise RuntimeError('Missing homepage publication section')
        old_section.insert_before(fragment(s,updates_html(tr,prefix)))
        last=s.select('main > section')[-1]
        last.insert_before(fragment(s,join_html(tr,prefix)))
        preload=s.new_tag('link',rel='preload',href=prefix+'assets/visuals/research-hero.webp',as_='image')
        preload['as']='image';preload.attrs.pop('as_',None);s.head.append(preload)
        meta=s.new_tag('meta',attrs={'property':'og:image','content':'https://huseyinates38.github.io/assets/visuals/research-hero.webp'})
        s.head.append(meta)
    elif name=='research.html':
        s.select_one('main > section').insert_after(fragment(s,research_gallery(tr,prefix)))
    elif name=='projects.html':
        s.select_one('main > section').insert_after(fragment(s,'<div class="visual-project-separator" aria-hidden="true"></div>'))
    # CSS and JS are progressively enhanced; content remains available without JavaScript.
    css=s.new_tag('link',rel='stylesheet',href=prefix+'assets/visual-story.css?v=4.7');s.head.append(css)
    js=s.new_tag('script',attrs={'src':prefix+'assets/visual-story.js?v=4.7','defer':''});s.head.append(js)

def main():
    for tr in (False,True):
        loc=SITE/('tr' if tr else '')
        prefix='../' if tr else ''
        for name in ['index.html','research.html','projects.html']:
            path=loc/name
            s=Soup(path.read_text(encoding='utf-8'),'html.parser')
            decorate(s,name,tr,prefix)
            path.write_text(str(s),encoding='utf-8')
    for p in (ROOT/'assets/visuals').iterdir():
        dest=SITE/'assets/visuals'/p.name;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,dest)
    for name in ['visual-story.css','visual-story.js']:
        shutil.copy2(ROOT/'assets'/name,SITE/'assets'/name)
    file=SITE/'deployment.json'
    if file.exists():
        x=json.loads(file.read_text());x['version']='4.7';x['visual_assets']='Original conceptual imagery and research illustrations; no personal photographs or fabricated result figures.';file.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
    q=SITE/'quality-report.json'
    if q.exists():
        x=json.loads(q.read_text());x['release']='4.7';x['new_visuals']='Conceptual illustrations and selected confirmed highlights in two languages, no new claims about results.';q.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Visual enhancement 4.7 added to English and Turkish homepage, research and projects.')

if __name__=='__main__':main()
