#!/usr/bin/env python3
"""Focused 5.2 copy edits using only the existing public research records.

Called before shared metadata/search generation. Unknown tasks, research topics
and project assignments are omitted, never inferred from someone's institution.
"""
import re

ROLE_ONLY = {'gokhan-ince', 'zeynep-aydemir', 'ahmet-salih-simsek', 'ibrahim-delen', 'serbay-durmaz'}
NO_STAGE = ROLE_ONLY | {'ipek-oz'}
BUI = ('Ongoing academic contact · completed VR–STEM study',
       'Devam eden akademik iletişim · tamamlanan VR–STEM çalışması')
COPY = {
 'elena-novak': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('AI system design, epistemic vigilance and scientific judgement',
            'Yapay zekâ sistem tasarımı, epistemik dikkat ve bilimsel yargı'),
  'stage': ('Joint manuscript development', 'Ortak makale hazırlığı'),
  'intro': ('Collaborates with Hüseyin Ateş on a manuscript about learners’ evaluation of AI-generated scientific claims.',
            'Hüseyin Ateş ile öğrencilerin yapay zekâ tarafından üretilen bilimsel iddiaları değerlendirmesi üzerine bir makale hazırlamaktadır.'),
  'contribution': ('Elena Novak contributes to the manuscript’s conceptual framework, literature review and critical interpretation. The collaboration examines how the design of generative-AI learning systems relates to epistemic vigilance and independent scientific judgement.',
                   'Elena Novak, makalenin kavramsal çerçevesine, alanyazın taramasına ve eleştirel yorumuna katkı sunmaktadır. Çalışmada, üretken yapay zekâ destekli öğrenme sistemlerinin tasarımı ile epistemik dikkat ve bağımsız bilimsel yargı arasındaki ilişki incelenmektedir.')},
 'juan-garzon': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Educational technology and generative-AI literacy',
            'Eğitim teknolojileri ve üretken yapay zekâ okuryazarlığı'),
  'stage': ('Study design and pilot preparation; collection proposal awaiting approval',
            'Araştırma tasarımı ve pilot hazırlığı; koleksiyon önerisi için onay bekleniyor'),
  'intro': ('Collaborates with Hüseyin Ateş on educational technology research and editorial initiatives.',
            'Hüseyin Ateş ile eğitim teknolojileri araştırmaları ve editoryal çalışmalar yürütmektedir.'),
  'contribution': ('The Türkiye–Colombia study involves research-instrument harmonisation, study design and international coordination. Their collaboration builds on co-authored publications on augmented-reality adoption and flipped-learning readiness. They are also developing a thematic-collection proposal for the International Journal of Educational Technology in Higher Education. Earlier guest-advisory work concerned the separate Sustainable Environment collection, Emerging Technologies for Sustainable Development.',
                   'Türkiye–Kolombiya çalışması; ölçme araçlarının uyarlanmasını, araştırma tasarımını ve uluslararası koordinasyonu kapsamaktadır. İş birliğinin geçmişinde, artırılmış gerçekliğin benimsenmesi ve ters yüz öğrenmeye hazır bulunuşluk üzerine ortak yayınlar bulunmaktadır. International Journal of Educational Technology in Higher Education için bir tematik koleksiyon önerisi de hazırlanmaktadır. Önceki konuk danışmanlık çalışması ise Sustainable Environment dergisindeki Emerging Technologies for Sustainable Development koleksiyonuyla ilgilidir.')},
 'moritz-krell': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Scientific-reasoning task validity and evidence-source judgement',
            'Bilimsel akıl yürütme görevlerinin geçerliği ve kanıt kaynaklarının değerlendirilmesi'),
  'stage': ('Research proposal development · not yet submitted',
            'Araştırma önerisi geliştiriliyor · henüz başvuru yapılmadı'),
  'intro': ('Develops a joint research concept with Hüseyin Ateş on scientific reasoning after AI feedback.',
            'Hüseyin Ateş ile yapay zekâ geri bildirimi sonrasında bilimsel akıl yürütme üzerine bir araştırma önerisi geliştirmektedir.'),
  'contribution': ('The collaboration distinguishes recognising the origin of evidence from using that information to evaluate competing explanations. Text-based and graphical task prototypes are being refined. A TÜBİTAK–DFG bilateral route and coordinated national applications are being considered for the proposed study.',
                   'Çalışmada, kanıtın kaynağını tanıma ile bu bilgiyi rakip açıklamaları değerlendirmede kullanma arasındaki ayrım ele alınmaktadır. Metin ve grafik tabanlı görev prototipleri geliştirilmektedir. Önerilen araştırma için TÜBİTAK–DFG ikili destek yolu ve eşgüdümlü ulusal başvuru seçenekleri değerlendirilmektedir.')},
 'marc-romero-carbonell': {
  'role': ('Editorial collaborator · ETHE', 'Editoryal iş birliği · ETHE'),
  'focus': ('Learning with generative AI, student competencies, teaching and assessment',
            'Üretken yapay zekâ (GenAI) ile öğrenme, öğrenci yeterlikleri, öğretim ve değerlendirme'),
  'stage': ('Collection proposal · journal approval pending',
            'Koleksiyon önerisi · dergi onayı bekleniyor'),
  'intro': ('Provides editorial guidance on a proposed thematic collection developed by Hüseyin Ateş and Juan Garzón.',
            'Hüseyin Ateş ve Juan Garzón’un hazırladığı tematik koleksiyon önerisine editoryal rehberlik sağlamaktadır.'),
  'contribution': ('Discussions with Marc Romero Carbonell concern the scope and international guest-editor team of a proposed collection for the International Journal of Educational Technology in Higher Education. The themes include learning with generative AI, the competencies students need, and the redesign of teaching and assessment.',
                   'Marc Romero Carbonell ile görüşmeler, International Journal of Educational Technology in Higher Education için hazırlanan koleksiyonun kapsamına ve uluslararası konuk editör ekibine odaklanmaktadır. Koleksiyonda üretken yapay zekâyla öğrenme, öğrencilerin ihtiyaç duyduğu yeterlikler ve öğretim ile değerlendirmenin yeniden tasarlanması ele alınmaktadır.')}
}

# Eight additional collaborator profiles follow the same concise, evidence-based layout.
# Statements below consolidate existing public descriptions; no new research roles
# or funding awards are asserted.
COPY.update({
 'omid-noroozi': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Feedback, scientific argument revision and learner control',
            'Geri bildirim, bilimsel argüman revizyonu ve öğrenen kontrolü'),
  'stage': ('Joint manuscript development', 'Ortak makale hazırlığı'),
  'intro': ('Develops an empirical research manuscript with Hüseyin Ateş and MohammadReza Farrokhnia on feedback and revision of scientific arguments.',
            'Hüseyin Ateş ve MohammadReza Farrokhnia ile geri bildirim ve bilimsel argüman revizyonu üzerine ampirik bir araştırma makalesi hazırlamaktadır.'),
  'contribution': ('The collaboration examines feedback processes, learner control and the conceptual framework for revising scientific arguments. Manuscript development and interpretation are continuing. Discussions about possible researcher visits are separate from the manuscript collaboration.',
                   'İş birliğinde geri bildirim süreçleri, öğrenen kontrolü ve bilimsel argümanların yeniden düzenlenmesine ilişkin kavramsal çerçeve ele alınmaktadır. Makalenin geliştirilmesi ve yorumlanmasına yönelik çalışmalar sürmektedir. Olası araştırmacı ziyaretlerine ilişkin görüşmeler, makale iş birliğinden ayrı yürütülmektedir.')},
 'mohammadreza-farrokhnia': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Human–AI feedback and scientific argumentation',
            'İnsan–yapay zekâ geri bildirimi ve bilimsel argümantasyon'),
  'stage': ('Joint manuscript development; COST application decision pending',
            'Ortak makale hazırlığı; COST başvuru kararı bekleniyor'),
  'intro': ('Works with Hüseyin Ateş and Omid Noroozi on a manuscript concerning human–AI feedback and scientific reasoning.',
            'Hüseyin Ateş ve Omid Noroozi ile insan–yapay zekâ geri bildirimi ve bilimsel akıl yürütme üzerine bir makale hazırlamaktadır.'),
  'contribution': ('His collaborative work includes conceptual framing, methodological interpretation and manuscript revision. He also participated as a secondary proposer in the submitted SciEpi-Feedback COST network application, for which a funding decision is pending.',
                   'İş birliği; makalenin kavramsal çerçevesini, yöntemsel yorumunu ve revizyonunu kapsamaktadır. Farrokhnia ayrıca sunulan SciEpi-Feedback COST ağ başvurusuna ikincil önerici olarak katılmıştır. Başvuru için destek kararı beklenmektedir.')},
 'kazem-banihashem': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Retrieval-grounded generative AI, adaptive feedback and argument revision',
            'Kaynak temelli üretken yapay zekâ, uyarlanabilir geri bildirim ve argüman revizyonu'),
  'stage': ('Manuscript revision', 'Makale revizyonu'),
  'intro': ('Collaborates on manuscript development and methodological review concerning generative-AI feedback and scientific argumentation.',
            'Üretken yapay zekâ geri bildirimi ve bilimsel argümantasyon üzerine makale geliştirme ve yöntemsel değerlendirme çalışmalarına katkı sunmaktadır.'),
  'contribution': ('The joint work addresses retrieval-grounded generative AI, adaptive rule-based feedback and scientific argument revision. His contributions include discussion of the manuscript’s methodological positioning, scientific argument and revisions.',
                   'Ortak çalışma, kaynak temelli üretken yapay zekâ, uyarlanabilir kural temelli geri bildirim ve bilimsel argüman revizyonunu ele almaktadır. Katkıları, makalenin yöntemsel konumlandırılmasını, bilimsel gerekçelendirmesini ve revizyonunu değerlendirmeyi kapsamaktadır.')},
 'guido-makransky': {
  'role': ('Research collaboration discussions', 'Araştırma iş birliği görüşmeleri'),
  'focus': ('Immersive science learning and reflective generative-AI scaffolding',
            'Sürükleyici fen öğrenimi ve yansıtıcı üretken yapay zekâ desteği'),
  'stage': ('Research design discussions', 'Araştırma tasarımı görüşmeleri'),
  'intro': ('Discusses the design of research on immersive science learning and reflective generative-AI support with Hüseyin Ateş.',
            'Hüseyin Ateş ile sürükleyici fen öğrenimi ve yansıtıcı üretken yapay zekâ desteğine ilişkin araştırma tasarımını görüşmektedir.'),
  'contribution': ('Current discussions concern a potential manuscript on immersive learning and a possible small pilot comparing reflective scaffolding and the gradual reduction of AI support. The pilot remains a research-design proposal; no implementation or funding is reported.',
                   'Görüşmeler, sürükleyici öğrenme üzerine olası bir makaleyi ve yansıtıcı destekleme ile yapay zekâ desteğinin kademeli azaltılmasını karşılaştırabilecek küçük ölçekli bir pilot tasarımı kapsamaktadır. Pilot çalışma henüz tasarım aşamasındadır; uygulamaya geçildiği veya destek alındığı belirtilmemektedir.')},
 'georgios-lampropoulos': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Flipped learning and evidence-based scientific reasoning',
            'Ters yüz öğrenme ve kanıta dayalı bilimsel akıl yürütme'),
  'stage': ('Ongoing manuscript collaboration', 'Devam eden makale iş birliği'),
  'intro': ('Co-authored a published study on science teachers’ flipped-learning readiness with Hüseyin Ateş and Juan Garzón.',
            'Hüseyin Ateş ve Juan Garzón ile fen öğretmenlerinin ters yüz öğrenmeye hazır bulunuşluğu üzerine yayımlanmış bir çalışmanın ortak yazarıdır.'),
  'contribution': ('The collaboration now also includes developing a manuscript on evidence-based reasoning before AI-provided answers. The earlier peer-reviewed publication and the manuscript in preparation are separate research outputs.',
                   'Devam eden iş birliği, yapay zekânın sunduğu yanıtlardan önce kanıta dayalı akıl yürütmeyi ele alan bir makalenin geliştirilmesini de kapsamaktadır. Daha önce yayımlanan ortak çalışma ile hazırlık aşamasındaki makale ayrı araştırma çıktılarıdır.')},
 'ahmet-sami-konca': {
  'role': ('Research collaborator', 'Araştırma ortağı'),
  'focus': ('Scientific agency in preschool STEM and independent instructional design',
            'Okul öncesi STEM’de bilimsel özne olma ve bağımsız öğretim tasarımı'),
  'stage': ('Joint research; AÜB application decision pending',
            'Ortak araştırma; AÜB başvuru kararı bekleniyor'),
  'intro': ('Co-authored a published study with Hüseyin Ateş on scientific agency in preschool STEM education.',
            'Hüseyin Ateş ile okul öncesi STEM eğitiminde bilimsel özne olma üzerine yayımlanmış bir çalışmanın ortak yazarıdır.'),
  'contribution': ('Their ongoing collaboration includes the submitted AÜB International BAP proposal examining generative-AI guidance for prospective preschool teachers’ independent STEM instructional design. The proposal is awaiting a funding decision and is separate from their published research.',
                   'Süren iş birliği, okul öncesi öğretmen adaylarının bağımsız STEM öğretim tasarımında üretken yapay zekâ rehberliğini inceleyen, sunulmuş AÜB Uluslararası BAP önerisini kapsamaktadır. Öneri için destek kararı beklenmektedir; bu çalışma yayımlanan ortak araştırmadan ayrıdır.')},
 'juan-david-murillo-egurrola': {
  'role': ('Study coordinator', 'Çalışma koordinatörü'),
  'focus': ('Generative-AI literacy and responsible academic use',
            'Üretken yapay zekâ okuryazarlığı ve sorumlu akademik kullanım'),
  'stage': ('Instrument adaptation and pilot preparation',
            'Ölçme aracı uyarlama ve pilot uygulama hazırlığı'),
  'intro': ('Coordinates the Türkiye–Colombia comparative study of generative-AI literacy with Hüseyin Ateş and Juan Garzón.',
            'Hüseyin Ateş ve Juan Garzón ile yürütülen Türkiye–Kolombiya üretken yapay zekâ okuryazarlığı karşılaştırma çalışmasını koordine etmektedir.'),
  'contribution': ('The collaboration covers the research framework, questionnaire refinement, translation reconciliation, discipline-based sampling and preparation for cognitive interviews and piloting. Fieldwork arrangements are still being coordinated; comparative findings are not yet available.',
                   'Çalışmada araştırma çerçevesi, anketin geliştirilmesi, çeviri uzlaştırması, disiplin temelli örnekleme ve bilişsel görüşme ile pilot uygulama hazırlıkları yürütülmektedir. Saha çalışmasının koordinasyonu sürmekte olup henüz karşılaştırmalı bulgular bulunmamaktadır.')},
 'naomi-winstone': {
  'role': ('Research collaborator and proposed academic host',
           'Araştırma ortağı ve önerilen akademik ev sahibi'),
  'focus': ('Feedback processes, evaluative judgement and learner agency',
            'Geri bildirim süreçleri, değerlendirme yargısı ve öğrencinin etkin özne olması'),
  'stage': ('Manuscript development; TÜBİTAK 2219 decision pending',
            'Makale hazırlığı; TÜBİTAK 2219 kararı bekleniyor'),
  'intro': ('Collaborates with Hüseyin Ateş on the conceptual framing and interpretation of a generative-AI research manuscript.',
            'Hüseyin Ateş ile üretken yapay zekâ üzerine bir araştırma makalesinin kavramsal çerçevesini ve yorumlanmasını geliştirmektedir.'),
  'contribution': ('She has also provided a formal invitation to act as academic host for the submitted TÜBİTAK 2219 proposal at the University of Surrey. That proposal examines scheduled fading of AI feedback and independent scientific argumentation. The proposed May 2027–May 2028 visit remains conditional on funding and institutional arrangements, separately from the manuscript collaboration.',
                   'Ayrıca Surrey Üniversitesinde TÜBİTAK 2219 başvurusu kapsamında akademik ev sahipliği için resmî davet sağlamıştır. Önerilen araştırma, yapay zekâ geri bildiriminin kademeli azaltılmasını ve bağımsız bilimsel argümantasyonu incelemektedir. Mayıs 2027–Mayıs 2028 için planlanan ziyaret, makale iş birliğinden ayrı olup destek kararına ve kurumsal düzenlemelere bağlıdır.')}
})

def set_text(node, value):
 if node is not None:
  node.clear(); node.append(value)

def remove(nodes):
 for node in list(nodes): node.decompose()

def pairs(s, replacements):
 for n in list(s.main.find_all(string=True)):
  if n.parent is None or n.parent.name in ('script','style','code','pre'): continue
  old=str(n); new=old
  for a,b in replacements: new=new.replace(a,b)
  if old!=new: n.replace_with(new)

def facts(s, rows):
 box=s.select_one('#academic-record dl.profile-facts')
 assert box is not None
 box.clear()
 for label,value in rows:
  wrapper=s.new_tag('div');dt=s.new_tag('dt');dd=s.new_tag('dd')
  dt.string=label;dd.string=value;wrapper.extend([dt,dd]);box.append(wrapper)

def compact_person(s, slug, tr):
 d=COPY[slug]; i=int(tr)
 set_text(s.select_one('.pagehero .eyebrow'), 'Editorial profile' if slug=='marc-romero-carbonell' else 'Research profile')
 if tr: set_text(s.select_one('.pagehero .eyebrow'), 'Editoryal profil' if slug=='marc-romero-carbonell' else 'Araştırmacı profili')
 set_text(s.select_one('.pagehero .lead'),d['intro'][i])
 remove(s.select('.pagehero .relationship-stage'))
 labels=('Rol','Araştırma odağı','Güncel aşama') if tr else ('Role','Research focus','Current stage')
 facts(s,[(labels[j], d[key][i]) for j,key in enumerate(('role','focus','stage'))])
 layout=s.select_one('.profile-layout')
 assert layout is not None, slug
 links=layout.select_one('.profile-links').extract()
 target=layout.select_one('h2').parent
 target.clear()
 heading=s.new_tag('h2');heading.string=('Editoryal katkı' if tr else 'Editorial contribution') if slug=='marc-romero-carbonell' else ('Araştırma katkısı' if tr else 'Research contribution')
 p=s.new_tag('p',attrs={'class':'lead','data-profile-contribution':'true'});p.string=d['contribution'][i]
 sub=s.new_tag('h3');sub.string='İlgili çalışmalar' if tr else 'Related work'
 target.extend([heading,p,sub,links])
 for old in list(s.select('#ongoing-research')):
  if layout not in old.descendants: old.decompose()
 # Preserve the existing fragment URL at the consolidated contribution section.
 layout.find_parent('section')['id']='ongoing-research'

def limited_person(s,slug,tr):
 role=s.select_one('.pagehero .eyebrow').get_text(' ',strip=True)
 set_text(s.select_one('.pagehero .eyebrow'),'Araştırmacı profili' if tr else 'Research profile')
 remove(s.select('.pagehero .lead, .pagehero .relationship-stage'))
 facts(s,[(('Rol' if tr else 'Role'),role)])
 # Keep the verified institutional identity, logo and country, without duplicating the role.
 summary=s.select_one('.profile-summary')
 if summary:
  institution=summary.select_one('.affiliation-list').extract()
  container=s.select_one('#academic-record .container');container.append(institution)
  summary.find_parent('section').decompose()

def bui(s,tr):
 i=int(tr)
 set_text(s.select_one('.pagehero .eyebrow'),'Akademik iletişim' if tr else 'Academic contact')
 set_text(s.select_one('.pagehero .relationship-stage'),BUI[i])
 facts(s,[(('Rol' if tr else 'Role'), 'Akademik araştırma ortağı' if tr else 'Academic collaborator'),
          (('Araştırma odağı' if tr else 'Research focus'), 'STEM eğitimi ve uluslararası araştırma iş birliği' if tr else 'STEM education and international research collaboration'),
          (('Güncel aşama' if tr else 'Current stage'),BUI[i])])
 summary=s.select_one('.profile-summary')
 summary.find_parent('section')['id']='ongoing-research'
 set_text(summary.select_one('h2'),'Devam eden akademik iletişim' if tr else 'Ongoing academic contact')
 set_text(summary.select_one('p.lead'),
  'Bui Van Hong ile HCM-UTE üzerinden kurulan akademik iletişim sürmektedir. Vietnam bağlamına uyarlanabilirlik bileşenini içeren VR–STEM çalışması tamamlanmıştır.' if tr else
  'Academic contact with Bui Van Hong through HCM-UTE continues. The VR–STEM study, including its adaptability component for the Vietnamese context, is completed.')
 # The older additional section repeats exactly the same relation and project status.
 for sec in list(s.select('main > section')):
  h=sec.select_one('h2')
  if sec is not summary.find_parent('section') and h and h.get_text(' ',strip=True) in ('Ongoing academic connection','Devam eden araştırma iş birliği','Devam eden akademik iletişim'):
   sec.decompose()

def define_genai(s):
 # Expand the first prose occurrence only; leave publication titles and citations intact.
 for n in s.main.find_all(string=True):
  if n.parent.name in ('script','style','code','pre') or n.find_parent('a') or n.find_parent(class_='citation'):continue
  value=str(n)
  if not re.search(r'\bGenAI\b',value):continue
  if re.search(r'(üretken yapay zekâ|üretken yapay zeka)\s*\(GenAI\)',value,re.I):break
  start=re.search(r'\bGenAI\b',value).start()
  expansion='Üretken yapay zekâ (GenAI)' if not value[:start].strip() else 'üretken yapay zekâ (GenAI)'
  n.replace_with(value[:start]+expansion+value[start+5:]);break

def team(s,tr):
 for card in s.select('.person-card[data-person]'):
  slug=card['data-person']
  if slug in ROLE_ONLY:
   remove(card.select('.person-topic,.relationship-stage'))
  if slug=='ipek-oz':
   if card.find_parent(id='alumni'):set_text(card.select_one('.relationship-stage'),'Yüksek lisans tamamlandı · 2022' if tr else 'Master’s degree completed · 2022')
   else:remove(card.select('.relationship-stage'))
  if slug=='bui-van-hong':
   set_text(card.select_one('.micro-label'),'Akademik araştırma ortağı' if tr else 'Academic collaborator')
   set_text(card.select_one('.relationship-stage'),BUI[int(tr)])
  if slug in COPY:set_text(card.select_one('.relationship-stage'),COPY[slug]['stage'][int(tr)])
  if slug=='marc-romero-carbonell' and tr:
   set_text(card.select_one('.person-topic'),'Üretken yapay zekâyla öğrenme üzerine tematik koleksiyon önerisi')
 for p in s.select('main p'):
  if 'Roles follow the supplied team roster.' in p.get_text():
   set_text(p,'AÜB application-team roles are identified separately. The application is awaiting a funding decision.')
  if any(x in p.get_text() for x in ['Roller paylaşılan ekip','Roller, paylaşılan ekip','Roller verilen ekip','Proje ekibindeki görevler, paylaşılan başvuru']):
   set_text(p,'AÜB başvuru ekibinin rolleri ayrı olarak belirtilmiştir. Başvuru için destek kararı beklenmektedir.')

def network(s,tr):
 p=s.select_one('#network-directory > .container > p')
 assert p is not None
 set_text(p,'Dizin, araştırma ağının 2026–2028 dönemine ilişkin görünümünü sunar. Güncel kurum bilgileri ve iş birliğinin türü, kişisel profillerde açıklanır.' if tr else
  'The directory presents a snapshot of the research network for 2026–2028. Current affiliations and types of collaboration are described in individual profiles.')
 pairs(s,[('two supplied posters','two research-network posters'),('supplied posters','research-network posters'),('supplied poster','research-network poster')])
 # Keep one invitation, one form button and one clickable QR; retain the interest form's purpose.
 for sec in list(s.select('main > section')):
  if sec.get('id')!='research-interest' and sec.select_one('a[href="https://tally.so/r/Eq51Jr"]'):sec.decompose()
 invite=s.select_one('#research-interest .research-join > div')
 assert invite is not None
 for p in list(invite.find_all('p',recursive=False)):
  if p.get('class')==['eyebrow'] or p.select_one('a.btn'):continue
  p.decompose()
 h=invite.select_one('h2');p=s.new_tag('p')
 p.string=('Araştırma ilginizi veya ortak çalışma önerinizi Tally üzerindeki ilgi formuyla paylaşabilirsiniz. Lisansüstü kabul işlemleri üniversitenin ayrı resmî başvuru süreciyle yürütülür.' if tr else
  'Share your research interests or a collaboration proposal using the interest form hosted on Tally. Formal graduate admission follows the university’s separate application process.')
 h.insert_after(p)
 tools=s.select_one('#network-directory .directory-tools')
 empty=s.select_one('#network-no-results')
 if empty is None:
  empty=s.new_tag('p',id='network-no-results',attrs={'hidden':'','role':'status'});tools.insert_after(empty)
 empty.string=('Bu aramayla eşleşen ülke bulunamadı. Başka bir ülke veya kurum adı deneyin ya da aramayı temizleyin.' if tr else
  'No countries match this search. Try another country or institution name, or clear the search.')
 if s.select_one('#network-reset') is None:
  reset=s.new_tag('button',id='network-reset',type='button',attrs={'class':'btn alt'});reset.string='Aramayı temizle' if tr else 'Clear search';tools.append(reset)
 count=s.select_one('#network-count');total=len(s.select('.network-country'))
 count.string=f'{total} / {total} ülke gösteriliyor' if tr else f'Showing {total} of {total} countries'

def refine(s,name,tr):
 if name.startswith('person-'):
  slug=name[7:-5]
  if slug in ROLE_ONLY:limited_person(s,slug,tr)
  elif slug in COPY:compact_person(s,slug,tr)
  elif slug=='bui-van-hong':bui(s,tr)
  elif slug=='ipek-oz':
   remove(s.select('.pagehero .relationship-stage'))
   for dt in list(s.select('#academic-record dt')):
    if dt.get_text(' ',strip=True) in ['Current stage','Güncel aşama']:dt.parent.decompose()
  if tr:define_genai(s)
 if name=='team.html':team(s,tr)
 if name in ('team.html','research-network.html'):
  pairs(s,[('Roles follow the supplied team roster. ',''),('supplied posters','research-network posters'),('supplied poster','research-network poster')])
 if name=='research-network.html':network(s,tr)
 if name=='resource-use.html':
  p=s.select_one('main .v3-box p')
  set_text(p,'Üç tematik öğretim seti ve kurgusal bitki örneği, öğretim amacıyla kopyalanabilir ve uyarlanabilir. Her set bir öğretmen rehberi ve bir çalışma yaprağı içerir.' if tr else
   'You may copy and adapt the three thematic teaching sets and the fictional plant example for teaching. Each set contains a teacher guide and a worksheet.')
  attribution=s.new_tag('p');attribution['data-resource-attribution']='true'
  attribution.string=('Hüseyin Ateş’in araştırma sitesine atıf verin, öğretim prototipi açıklamasını koruyun ve yaptığınız değişiklikleri belirtin.' if tr else
  'Acknowledge Hüseyin Ateş’s research website, retain the teaching-prototype notice and identify changes.')
  remove(s.select('p[data-resource-attribution]'));p.insert_after(attribution)
 if name=='resource-argumentation.html' and tr:
  pairs(s,[('Explorer içindeki kurgusal bitki karşılaştırmasında','Keşif aracındaki kurgusal bitki karşılaştırmasında')])
 if name=='project-ai-literacy-colombia.html':
  section=s.select('main > section')[-1]
  remove(section.select('.callout'))
  for p in list(section.select('p')):
   if p.get('class')!=['lead']:p.decompose()
  set_text(section.select_one('p.lead'),
   'Ölçme aracının uyarlanması ve pilot uygulama hazırlıkları sürmektedir. Türkçe metnin bağımsız geri çevirisi ve uzlaştırması tamamlanmış, Kolombiya İspanyolcası uyarlaması paylaşılmıştır. Ekipler saha düzenlemelerini ve pilot uygulama takvimini koordine etmektedir.' if tr else
   'Instrument adaptation and pilot preparation are ongoing. Independent back-translation and reconciliation of the Turkish text are complete, and the Colombian Spanish adaptation has been shared. The teams are coordinating fieldwork arrangements and the pilot schedule.')
