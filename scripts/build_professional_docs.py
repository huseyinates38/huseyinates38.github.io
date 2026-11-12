#!/usr/bin/env python3
"""Produce editable and print-ready public documents from approved site content.
No original research data, unpublished manuscripts or pending proposals are included.
"""
from pathlib import Path
import re
from html import escape
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
OUT = SITE / 'downloads'
BASE = 'https://huseyinates38.github.io/'
NAVY, TEAL = '153746', '187886'
TERMS = ('Classroom-use permission: the site-created teaching prototypes may be copied and '
         'adapted for teaching with acknowledgement of this website, retention of the prototype '
         'notice and a clear indication of changes. Public republication, commercial distribution '
         'and uses of third-party content require separate permission. No validation or endorsement is implied.')
TERMS_TR = ('Sınıf içi kullanım izni: Bu siteye özgü öğretim örnekleri, siteye atıf yapılması, '
            'prototip uyarısının korunması ve değişikliklerin belirtilmesi koşuluyla öğretim için '
            'çoğaltılabilir ve uyarlanabilir. Herkese açık yeniden yayımlama, ticari dağıtım ve '
            'üçüncü taraf içerikleri için ayrıca izin gerekir. Geçerlik veya onay iddiası içermez.')
CV = [
 [('title','Hüseyin Ateş, PhD'),('subtitle','Associate Professor of Science Education'),
  ('p','Department of Science Education, Faculty of Education | Kırşehir Ahi Evran University, Türkiye'),
  ('small','huseyin.ates@ahievran.edu.tr | ORCID 0000-0003-0031-8994'),
  ('small',BASE+' | Public academic CV · 12 November 2026'),
  ('h','Research profile'),
  ('p','Research on human-centered artificial intelligence, scientific reasoning and self-regulated learning, including feedback design, teachers’ technology adoption and experimental instructional research. Principal supervision of master’s and doctoral research.'),
  ('h','Academic and administrative appointments'),
  ('p','2023–present | Associate Professor, Department of Science Education, Kırşehir Ahi Evran University.'),
  ('p','2026–present | Deputy Director, Directorate of Research and Development, Kırşehir Ahi Evran University.'),
  ('p','2023 | Visiting Associate Professor, South-West University “Neofit Rilski”, Bulgaria (Erasmus+ Lecturer Mobility).'),
  ('p','2012–2023 | Research Assistant, Department of Science Education, Kırşehir Ahi Evran University.'),
  ('h','Education'),
  ('p','2019 | PhD, Elementary Education, Middle East Technical University, Türkiye (English-medium programme).'),
  ('p','2013 | MS, Science Education, Erciyes University, Türkiye.'),
  ('p','2011 | BA, Science Education, Erzincan University, Türkiye.'),
  ('h','Selected funded research · Principal Investigator'),
  ('p','2026–2029 | TÜBİTAK 3501: Physical humanoid social robot versus screen-based virtual agent in AI-supported self-regulated environmental learning. Mixed-methods study with an active control condition among middle school students.'),
  ('p','2026–2027 | TÜBİTAK 1002-A, 226K999: Classroom pilot comparison of two pedagogical scaffolding approaches in space-debris problem-solving instruction.'),
  ('p','2026–2028 | KAEÜ BAP, EGT.A3.26.001: VR-supported STEM instruction, achievement, STEM attitudes and technology acceptance in Türkiye; adaptability to the Vietnamese educational context.'),
  ('p','2025–2026 | KAEÜ BAP, EGT.A3.25.001: VR-supported learning in the circulatory-system unit; student achievement, self-efficacy and classroom engagement.')],
 [('title','Research, supervision & service'),('subtitle','Hüseyin Ateş · Public academic CV'),
  ('h','Graduate supervision'),
  ('p','Ongoing PhD: Abdulkadir Aydın (expected 2028). Ongoing MSc: Tuğçe Ünsal and Nisa Gül (expected mid-2027).'),
  ('p','Completed MSc: Kübra Solmaz (2024), Rabia Ateş (2023), Fatma Gazioğlu (2022) and İpek Öz (2022).'),
  ('h','Selected teaching'),
  ('p','Graduate: Educational Technology and Digital Pedagogy; Science Education and Technology Integration; Research Methods in Education; Quantitative Data Analysis; Qualitative Data Analysis; Ethics in Education and Research.'),
  ('p','Undergraduate: Science Teaching; Science Learning and Teaching Approaches; Out-of-School Learning Environments; Nature and History of Science; Astronomy; Teaching Practice.'),
  ('h','Academic leadership and recognition'),
  ('p','Service on university research-project evaluation, academic appointments and research-incentive committees. Member of ESERA since 2015.'),
  ('p','University research awards: First Prize, Educational Sciences (2025, 2026); First Prize, Young Scientist – Educational Sciences (2023, 2024); First Prize, Young Scientist – Social, Humanities and Sports Sciences (2022).'),
  ('h','Methods and software'),
  ('p','Experimental and longitudinal research; multisite and classroom-based interventions; scientific argumentation and revision coding; structural equation modelling; scale adaptation and validation. R/RStudio, SPSS, AMOS and VOSviewer.'),
  ('h','Selected publications'),
  ('p','Ateş, H. (2026). Human-centered GenAI feedback design in higher education: A multisite experiment on direct, reflective, and hybrid approaches to scientific argumentation. International Journal of Educational Technology in Higher Education, 23, 38. DOI: 10.1186/s41239-026-00614-9'),
  ('p','Ateş, H. (2025). Integrating augmented reality into intelligent tutoring systems to enhance science education outcomes. Education and Information Technologies, 30(4), 4435–4470. DOI: 10.1007/s10639-024-12970-y'),
  ('p','Ateş, H. (2024). Designing a self-regulated flipped learning approach to promote students’ science learning performance. Educational Technology & Society, 27(1), 65–83. DOI: 10.30191/ETS.202401_27(1).RP05'),
  ('small','This public selection excludes manuscripts under review and proposals awaiting decisions. Publication details, project periods and appointments follow the supplied academic CV. Further records: '+BASE+'publications.html')]
]


def fonts():
    folder = Path('/usr/share/fonts/truetype/dejavu')
    for name, file in [('SiteSans','DejaVuSans.ttf'),('SiteSans-Bold','DejaVuSans-Bold.ttf')]:
        path=folder/file
        if not path.exists(): raise FileNotFoundError('Install fonts-dejavu-core: '+str(path))
        if name not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(name,str(path)))
    pdfmetrics.registerFontFamily('SiteSans',normal='SiteSans',bold='SiteSans-Bold')


def new_doc(title,lang):
    d=Document(); sec=d.sections[0]
    sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
    sec.top_margin=Inches(.65); sec.bottom_margin=Inches(.6)
    sec.left_margin=sec.right_margin=Inches(.7)
    style=d.styles['Normal']; style.font.name='DejaVu Sans'; style.font.size=Pt(9.5)
    style.font.color.rgb=RGBColor.from_string(NAVY)
    style.paragraph_format.space_after=Pt(5);style.paragraph_format.line_spacing=1.12
    for name,size in [('Title',23),('Subtitle',11),('Heading 1',11.5)]:
        st=d.styles[name];st.font.name='DejaVu Sans';st.font.size=Pt(size)
        st.font.color.rgb=RGBColor.from_string(TEAL if name=='Heading 1' else NAVY)
        st.paragraph_format.space_before=Pt(10 if name=='Heading 1' else 0)
        st.paragraph_format.space_after=Pt(5)
    d.core_properties.title=title;d.core_properties.author='Hüseyin Ateş'
    d.core_properties.subject='Public academic resource; 12 November 2026'
    d.core_properties.language='tr-TR' if lang=='tr' else 'en-GB'
    header=sec.header.paragraphs[0]; header.text='HÜSEYİN ATEŞ  /  RESEARCH & LEARNING'
    header.style=d.styles['Caption']; header.runs[0].font.size=Pt(8)
    footer=sec.footer.paragraphs[0];footer.text='huseyinates38.github.io   |   12 Nov 2026   |   '
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    footer.runs[0].font.size=Pt(8)
    return d


def pdf_footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(HexColor('#D4E0DE'))
    canvas.line(45,40,A4[0]-45,40);canvas.setFont('SiteSans',7.5)
    canvas.setFillColor(HexColor('#536A72'))
    canvas.drawString(45,27,'huseyinates38.github.io  |  12 November 2026')
    canvas.drawRightString(A4[0]-45,27,str(doc.page));canvas.restoreState()


def export_document(stem,pages,title,lang='en'):
    """Each content page maps to a fixed page break in both formats."""
    d=new_doc(title,lang)
    styles={
      'title':ParagraphStyle('t',fontName='SiteSans-Bold',fontSize=22,leading=27,textColor=HexColor('#'+NAVY),spaceAfter=9),
      'subtitle':ParagraphStyle('s',fontName='SiteSans',fontSize=10.5,leading=15,textColor=HexColor('#'+TEAL),spaceAfter=9),
      'h':ParagraphStyle('h',fontName='SiteSans-Bold',fontSize=11,leading=15,textColor=HexColor('#'+TEAL),spaceBefore=10,spaceAfter=5,keepWithNext=True),
      'p':ParagraphStyle('p',fontName='SiteSans',fontSize=9.4,leading=13.8,textColor=HexColor('#'+NAVY),spaceAfter=5),
      'small':ParagraphStyle('sm',fontName='SiteSans',fontSize=7.8,leading=11,textColor=HexColor('#536A72'),spaceAfter=7),
    }
    story=[]
    for idx,blocks in enumerate(pages):
        if idx:d.add_page_break();story.append(PageBreak())
        for typ,text in blocks:
            if typ=='space':
                p=d.add_paragraph(' ');p.paragraph_format.space_after=Pt(float(text))
                story.append(Spacer(1,float(text)+12));continue
            para=d.add_paragraph(text,style={'title':'Title','subtitle':'Subtitle','h':'Heading 1'}.get(typ,'Normal'))
            if typ=='small':
                for r in para.runs:r.font.size=Pt(8)
            story.append(Paragraph(escape(text),styles[typ]))
    d.save(OUT/(stem+'.docx'))
    pdf=SimpleDocTemplate(str(OUT/(stem+'.pdf')),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=42,bottomMargin=52,title=title,author='Hüseyin Ateş')
    pdf.build(story,onFirstPage=pdf_footer,onLaterPages=pdf_footer)


def resource(stem):
    path=OUT/(stem+'.md');raw=path.read_text(encoding='utf-8');lang=stem[-2:]
    title=raw.splitlines()[0][2:]
    if lang=='tr':
        title={'feedback':'İnsan–Yapay Zekâ Geri Bildirim Tasarımı','argumentation':'Bilimsel Argümantasyon İnceleme Rehberi','self-regulation':'Öz Düzenlemeli Fen Öğrenme Planlayıcısı'}[stem[:-3]]
    paras=re.split(r'\n\s*\n',raw.strip())
    guide=[('title',title),('subtitle','Öğretmen rehberi · Sürüm 1.1 · Türkçe' if lang=='tr' else 'Teacher guide · Version 1.1 · English')]
    for p in paras[3:]:
        if p.startswith('## Worksheet'):break
        if p.startswith('## '):guide.append(('h',p[3:]))
        elif not p.startswith(('Version','Source:')):guide.append(('p',p))
    source=BASE+'resource-'+stem[:-3]+'.html'
    guide.append(('small',source))
    guide.append(('small','Bu site için hazırlanmış öğretim prototipi; geçerliği sınanmış bir ölçme aracı değildir.' if lang=='tr' else 'A site-created teaching prototype; not a validated measure or a published study instrument.'))
    worksheet=[('title','Çalışma yaprağı' if lang=='tr' else 'Planning worksheet'),('subtitle',title),('p','Tarih: __________________  Konu / görev: __________________' if lang=='tr' else 'Date: __________________  Topic / task: __________________')]
    questions={
      'feedback':(['Independent task and success criteria','First judgement: strength, uncertainty, revision priority','Feedback comment and relevant criterion','Accept, adapt or reject? State the evidence for your decision','Revision and later independent check'],['Bağımsız görev ve başarı ölçütleri','İlk değerlendirme: güçlü yön, belirsizlik, düzeltme önceliği','Geri bildirim yorumu ve ilgili ölçüt','Kabul, uyarlama veya ret? Kararınızın kanıtını belirtin','Düzeltme ve sonraki bağımsız kontrol']),
      'argumentation':(['Claim and its scope','Observations that support the claim','Reasoning connecting observations and conclusion','Alternative explanations and missing evidence','Proposed revision and reason'],['İddia ve kapsamı','İddiayı destekleyen gözlemler','Gözlemleri sonuca bağlayan gerekçelendirme','Alternatif açıklamalar ve eksik kanıt','Önerilen düzeltme ve gerekçesi']),
      'self-regulation':(['Goal and criteria before the task','Plan: strategy, resources and anticipated difficulty','During the task: evidence of progress','Decision to keep or change the strategy','After the task: reflection and next independent task'],['Görev öncesi hedef ve ölçütler','Plan: strateji, kaynaklar ve beklenen güçlük','Görev sırasında: ilerleme kanıtı','Stratejiyi sürdürme veya değiştirme kararı','Görev sonrası değerlendirme ve sonraki bağımsız görev'])
    }[stem[:-3]][lang=='tr']
    for q in questions:worksheet.extend([('h',q),('space','35')])
    worksheet.append(('small',TERMS_TR if lang=='tr' else TERMS))
    export_document(stem,[guide,worksheet],title,lang)
    raw=raw.replace('Version 1.0','Version 1.1').replace('No open licence is assigned; contact for redistribution or adaptation. Linked papers have separate terms.',TERMS_TR if lang=='tr' else TERMS)
    path.write_text(raw,encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True);fonts()
    export_document('Huseyin_Ates_Public_Academic_CV',CV,'Hüseyin Ateş — Public academic CV')
    for kind in ['feedback','argumentation','self-regulation']:
        for lang in ['en','tr']:resource(kind+'-'+lang)
    print('Created public CV and six bilingual teaching documents in PDF and DOCX.')

if __name__=='__main__':main()
