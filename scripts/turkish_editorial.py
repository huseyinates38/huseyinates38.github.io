#!/usr/bin/env python3
"""Academic Turkish copy edit applied after bilingual content generation.

Preserves original-language titles and bibliographic records. This is public-facing
site copyediting, not translation of academic publications.
"""
from __future__ import annotations
from bs4 import NavigableString
import re

# Verified, meaning-preserving adjustments to artificial/overly literal phrasing.
REPL={
 'İnsan Odaklı Yapay Zekâ ve Geri Bildirim Tasarımı':'İnsan odaklı yapay zekâ ve geri bildirim tasarımı',
 'Bilimsel Akıl Yürütme ve Öz Düzenlemeli Öğrenme':'Bilimsel akıl yürütme ve öz düzenlemeli öğrenme',
 'STEM Eğitiminde Yeni Teknolojiler':'STEM eğitiminde yeni teknolojiler',
 'İnsan–Yapay Zekâ Geri Bildirim Tasarımı Rehberi':'İnsan–yapay zekâ geri bildirim tasarımı rehberi',
 'İnsan–Yapay Zekâ':'İnsan–yapay zekâ',
 'Öz Düzenlemeli Fen Öğrenimi Planlayıcısı':'Öz düzenlemeli fen öğrenimi planlayıcısı',
 'Araştırmanın gerekçesi.':'Araştırmanın gerekçesi',
 'Proje neyi inceliyor?':'Projenin araştırma soruları',
 'Devam eden araştırma iş birliği.':'Devam eden araştırma iş birliği',
 'Editoryal ve uluslararası bağlantılar':'Editoryal çalışmalar ve uluslararası iş birlikleri',
 'Araştırmanın kapsamı.':'Araştırmanın kapsamı',
 'İş birliği ve güncel durum.':'İş birliğinin kapsamı ve güncel durum',
 'Araştırma programını inceleyin':'İlgili araştırma alanları',
 'Görevler paylaşılan ekip listesine göre sunulur. AÜB başvuru ekibindeki roller ayrıca etiketlenmiştir; listelenmek destek kararı alındığı anlamına gelmez.':'Proje ekibindeki görevler, paylaşılan başvuru belgelerindeki sorumluluklara göre belirtilmiştir. Başvuru aşamasındaki ekipler ayrıca gösterilmiştir.',
 'Ülke bilgileri kişinin vatandaşlığını değil, belirtilen kurumun bulunduğu ülkeyi gösterir. Kurum logoları aidiyeti tanıtır; kurumsal onay veya proje desteği anlamına gelmez.':'Ülke bilgileri, araştırmacıların bağlı oldukları kurumların konumlarını göstermektedir. Kurum logoları yalnızca kurumları tanıtmak amacıyla kullanılmıştır.',
 'Doğrudan, yansıtıcı ve hibrit':'Doğrudan, yansıtıcı ve karma',
 'Sınıftaki bir sorudan bilimsel iletişime':'Sınıf uygulamalarından araştırma iş birliğine',
 'Araştırma üzerinden iletişim':'Araştırma ve iş birliği için iletişim',
 'Araştırma iş birlikçileri':'Araştırma ortakları',
 'araştırma iş birlikçileri':'araştırma ortakları',
 'Araştırma bağlantılarını':'Araştırma iş birliklerini',
 'araştırma bağlantılarını':'araştırma iş birliklerini',
 'Araştırma bağlantıları':'Araştırma iş birlikleri',
 'araştırma bağlantıları':'araştırma iş birlikleri',
 'Araştırma bağlantısı':'Araştırma iş birliği',
 'araştırma bağlantısı':'araştırma iş birliği',
 'Akademik bağlantılar':'Akademik iş birlikleri',
 'akademik bağlantılar':'akademik iş birlikleri',
 'Süren akademik bağlantı':'Devam eden araştırma iş birliği',
 'Süren akademik bağlantılar':'Devam eden araştırma iş birlikleri',
 'Akademik araştırma kaydı':'Akademik çalışma',
 'Akademik ilişki':'Akademik iş birliği',
 'Devam Eden Akademik Çalışmalar':'Devam eden akademik çalışmalar',
 'Devam Eden Araştırma İş Birlikleri':'Devam eden araştırma iş birlikleri',
 'Devam Eden Editoryal İş Birliği':'Devam eden editoryal iş birliği',
 'Araştırma yürütücüsü / Tez danışmanı':'Araştırma yürütücüsü ve tez danışmanı',
 'Lisansüstü Araştırmacılar':'Lisansüstü araştırmacılar',
 'Mezun Araştırmacılar':'Mezun araştırmacılar',
 'Proje Araştırmacıları':'Proje araştırmacıları',
 'Araştırmacılar ve Danışmanlar':'Araştırmacılar ve danışmanlar',
 'Ülke ve kurum dizini':'Ülkelere göre kurumlar',
 'Kurumların tamamının resmî proje anlaşması imzaladığı iddia edilmez.':'Kurumlar arasındaki iş birliği biçimleri, ilgili araştırmacı profillerinde belirtilmiştir.',
 'Ortak makaleler, araştırma tasarımı ve bilimsel iletişim alanlarında süren akademik bağlantılar burada toplanmıştır. Kişisel profiller başvuruları, kavramsal çalışmaları ve tamamlanan projeleri ayırır; kurumların tamamının resmî proje anlaşması imzaladığı iddia edilmez.':'Bu bölümde birlikte hazırlanan makaleler, araştırma tasarımı çalışmaları ve geliştirilen ortak araştırma önerileri yer almaktadır. İş birliklerinin kapsamı her araştırmacının profilinde açıklanmıştır.',
 'Ortak makaleler, araştırma tasarımı ve bilimsel iletişim alanlarında süren akademik iş birlikleri burada toplanmıştır. Kişisel profiller başvuruları, kavramsal çalışmaları ve tamamlanan projeleri ayırır; kurumlar arasındaki iş birliği biçimleri, ilgili araştırmacı profillerinde belirtilmiştir.':'Bu bölümde birlikte hazırlanan makaleler, araştırma tasarımı çalışmaları ve geliştirilen ortak araştırma önerileri yer almaktadır. İş birliklerinin kapsamı her araştırmacının profilinde açıklanmıştır.',
 'Araştırma ortakları, proje araştırmacıları ve danışmanlar; ardından lisansüstü araştırmacılar ve mezunlar.':'Araştırma ortakları, proje ekipleri, lisansüstü araştırmacılar ve mezunlarımız bu sayfada bir araya geliyor.',
 'Kırşehir Ahi Evran Üniversitesinde Fen Bilgisi Eğitimi alanında akademisyen.':'Kırşehir Ahi Evran Üniversitesinde Fen Bilgisi Eğitimi alanında görev yapmaktadır.',
 'Yapay zekâyla öğrenmek. Kendi başına düşünmek.':'Yapay zekâ destekli öğrenme ve bağımsız düşünme',
 'Teknoloji, öğrencinin değerlendirme sorumluluğunu devralmadan bilimsel akıl yürütmeyi nasıl destekleyebilir? Araştırmalarım insan odaklı yapay zekâ, geri bildirim tasarımı ve öz düzenlemeli öğrenmeyi bir araya getiriyor.':'Araştırmalarımda, yapay zekâ destekli uygulamaların öğrencilerin bilimsel akıl yürütme ve bağımsız değerlendirme becerilerini nasıl geliştirebileceğini inceliyorum. Çalışmalarımın odağında geri bildirim tasarımı ve öz düzenlemeli öğrenme yer alıyor.',
 'Araştırma, insanlar ve uygulama.':'Araştırmalarımız ve çalışma alanlarımız',
 'Önce sorular, sonra teknolojiler.':'Araştırma sorularımız ve temel yaklaşımlarımız',
 'Düşünmeyi destekleyen kaynaklar':'Öğretim ve araştırma kaynakları',
 'Araştırma ortaklarını, editoryal bağlantıları ve lisansüstü araştırmacıları tanıyın.':'Araştırma ortaklarımızı, editoryal iş birliklerimizi ve lisansüstü araştırmacılarımızı tanıyın.',
 'Araştırma iş birliği, lisansüstü danışmanlık ve okullar ile öğretmenlerle bilimsel iletişim.':'Araştırma iş birlikleri, lisansüstü danışmanlık ve okullarla ortak çalışmalar için iletişime geçebilirsiniz.',
 'İnsanın düşünmesini merkeze alan araştırma.':'Bilimsel düşünmeyi merkeze alan araştırmalar',
 'fen/STEM eğitiminde':'fen ve STEM eğitiminde',
 'Fen/ STEM eğitiminde':'Fen ve STEM eğitiminde',
 'Bu alan; kanıta dayalı bilimsel argümantasyon, sorgulama, geri bildirimi kullanma, gözden geçirme süreçleri ve öz düzenlemeli öğrenmeye odaklanıyor.':'Bu araştırma alanında bilimsel argümantasyon, sorgulamaya dayalı öğrenme, geri bildirimden yararlanma ve öz düzenlemeli öğrenme süreçlerini inceliyorum.',
 'Araştırmalar; sanal ve artırılmış gerçeklik, eğitsel robotik, akıllı öğretim ve oyunlaştırmayı bir araya getiriyor.':'Çalışmalarımda sanal ve artırılmış gerçeklik, eğitsel robotik, akıllı öğretim sistemleri ve oyunlaştırma uygulamalarını ele alıyorum.',
 'Çok merkezli, sınıf temelli ve boylamsal çalışmalar; kümeli karşılaştırmalar ve gecikmeli aktarım sonuçları.':'Çok merkezli ve boylamsal araştırmalar, sınıf içi uygulamalar, küme düzeyinde karşılaştırmalar ve gecikmeli ölçümler.',
 'Belgelenmiş değişkenler, açık analiz kuralları, veri kalitesi kontrolleri ve yeniden üretilebilir yorumlama.':'Açıkça tanımlanan değişkenler, izlenebilir analiz süreçleri, veri kalitesi denetimleri ve tekrarlanabilir araştırma uygulamaları.',
 'Farklı aşamalardaki araştırmalar.':'Araştırma projeleri ve başvurular',
 'Diğer desteklenen projeler .':'Desteklenen araştırma projeleri',
 'Tamamlanan destekli araştırma .':'Tamamlanan araştırma projesi',
 'Devam eden araştırma iş birliği.':'Devam eden araştırma iş birliği',
 'Desteklenen projeler, devam eden araştırma iş birlikleri ve planlanan başvurular durumlarına göre ayrılır.':'Fon desteği alan projeler, tamamlanan araştırmalar, iş birlikleri ve başvurular ayrı başlıklar altında sunulmaktadır.',
 'Bu iki destekli proje için yeni bir tamamlanma bilgisi bildirilmemiştir. Tamamlanan Vietnam bağlantılı BAP projesi aşağıda ayrı sunulmaktadır.':'Desteklenen iki proje aşağıda yer almaktadır. Tamamlanan Vietnam bağlantılı BAP projesi ise ayrı bir bölümde sunulmaktadır.',
 'Burada yeni bir araştırma bulgusu ileri sürülmemektedir.':'',
 'Ölçme aracı uyarlaması ve pilot hazırlığı sürüyor. Çalışmaya katılım, destek kararı alınmasından ayrıdır.':'Ölçme aracının farklı dillere uyarlanması ve pilot araştırma hazırlıkları sürmektedir.',
 'Yayımlanan çıktılar erişime açıldığında bağlantı verilecek. Raporlanmamış sonuç veya tamamlanmış saha çalışması varsayılmaz.':'Çalışmanın yayımlanacak çıktıları ve materyalleri, erişime açıldıkça bu sayfada paylaşılacaktır.',
 'Dört sunulmuş başvuru, iki planlanan araştırma çalışması ve desteklenmeyen bir TÜBİTAK 3501 başvurusu ayrı başvuru kayıtlarında yer almaktadır.':'Başvurusu yapılmış dört öneri, hazırlığı süren iki çalışma ve desteklenmeyen TÜBİTAK 3501 önerisi ayrı ayrı listelenmektedir.',
 'Sınıf içi ve çok merkezli müdahaleler, tekrarlı gözlemler ve gecikmeli sonuç ölçümleri.':'Sınıf içi ve çok merkezli uygulamalar, tekrarlı gözlemler ve gecikmeli sonuç ölçümleri.',
 'Açık bir sorudan başlayın.':'Araştırma materyallerine erişim',
 'Araştırmayı izlenebilir kılmak.':'Araştırma yöntemleri ve açık bilim',
 'Kaynakların niteliği.':'Paylaşılan kaynakların kapsamı',
 'Erişim koşulları çalışmaya özgüdür.':'Araştırma verilerine erişim',
 'Yeniden çalıştırılabilir, sentetik bir örnek':'Örnek veri ve analiz uygulaması',
 'Okunacak fikirler. Düşünmeyi destekleyen araçlar.':'Öğretim ve araştırma kaynakları',
 'Planla. Sorgula. Yansıt.':'Planlama, sorgulama ve yansıtma',
 'Geri Bildirim Tasarımı Keşif Aracı':'Geri Bildirim Tasarımlarını Karşılaştırma Aracı',
 'Geri Bildirim Tasarımı Keşif Aracı.':'Geri Bildirim Tasarımlarını Karşılaştırma Aracı',
 'Bir geri bildirim dizisi planlayın':'Geri bildirim sürecini planlayın',
 'Bilimsel Argümantasyon İnceleme Rehberi':'Bilimsel Argümantasyonu İnceleme Rehberi',
 'GenAI okuryazarlığı':'Üretken yapay zekâ okuryazarlığı',
 'Sınıftaki bir sorudan bilimsel iletişime.':'Sınıftan araştırmaya uzanan iş birliği',
 'Araştırma üzerinden iletişim kuralım.':'Araştırma ve iş birliği için iletişim',
 'Bilimsel iletişim; bir sınıf içi problem, doktora araştırma ilgisi veya farklı bağlamların karşılaştırılmasıyla başlayabilir.':'Yeni bir araştırma iş birliği; sınıfta gözlenen bir sorundan, lisansüstü bir araştırma fikrinden ya da farklı eğitim ortamlarını karşılaştırma gereksiniminden doğabilir.',
 'Bir araştırma bağlantısı geliştirin':'Birlikte araştırma geliştirelim',
 'Danışmanlık uyumunu değerlendirin':'Lisansüstü araştırma olanakları',
 'Araştırma ile uygulamayı buluşturun':'Okullarla ve öğretmenlerle iş birliği',
 'Görüşmeler geri bildirim tasarımı, bilimsel argümantasyon, öz düzenleme veya eğitim teknolojisi üzerine olabilir. İletişim önerilerine açığız; proje ve kurum ilişkileri ayrıca kararlaştırılır.':'Geri bildirim tasarımı, bilimsel argümantasyon, öz düzenlemeli öğrenme ve eğitim teknolojileri alanlarında ortak araştırma önerilerini değerlendirmekten memnuniyet duyarız.',
 'İlgi alanlarınızın araştırma programıyla nasıl örtüştüğünü açıklayın. İlgi bildirmek kabul, burs veya ilan edilmiş ücretli pozisyon anlamına gelmez. Resmî kabul, üniversitenin süreçlerine tabidir.':'Lisansüstü araştırma yapmak istiyorsanız ilgi alanlarınızın çalışma konularımızla ilişkisini ve araştırma deneyiminizi kısaca paylaşabilirsiniz. Başvurular üniversitenin resmî kabul koşullarına tabidir.',
 'Öğretim bağlamınızdaki bir sorudan başlayın. Kaynaklar hakkında geri bildirim vermek veya görüşmek tek başına bir araştırmaya katılım oluşturmaz. Resmî araştırma katılımı ayrıca kararlaştırılan bir süreç gerektirir.':'Sınıfınızda karşılaştığınız öğretim sorunları, geliştirdiğiniz uygulamalar ve araştırma önerileri üzerine birlikte çalışabiliriz.',
 'Araştırma grubu katılım formunu aç':'Araştırma grubuna katılım formuna git',
 'Araştırma grubuyla paylaşmak istediğiniz bir araştırma fikri veya iş birliği öneriniz varsa ilgi formunu doldurabilirsiniz.':'Araştırma grubumuza katılmak ya da ortak çalışma önermek için kısa ilgi formunu doldurabilirsiniz.',
 'Form Tally üzerinden açılır. İlgi bildirmek araştırma grubu üyeliği, burs veya kesin kabul anlamına gelmez.':'Formu göndermek başvurunuzun değerlendirmeye alınmasını sağlar; üyelik veya burs hakkı doğurmaz.',
 'Gizlilik ve dış hizmetler':'Gizlilik ve dış bağlantılar',
 'Kaynaklar, gizlilik ve editoryal yaklaşım.':'Kaynaklar ve yayın ilkeleri',
 'Editoryal iş birliği.':'Editoryal iş birlikleri',
 'Koleksiyonlar ve editoryal iş birliği.':'Editoryal çalışmalar ve özel koleksiyonlar',
 'Görevlerin ayrımı.':'Editoryal görevlerin kapsamı',
 'Araştırma insanlarla gelişir.':'Araştırma ekibi ve iş birlikleri',
 'Uluslararası araştırma bağlantıları.':'Uluslararası araştırma ağı',
 'Paylaşılan 2026–2028 ağ afişleri; COST başvuruları, yayın iş birlikleri, projeler ve görüşmeler kapsamında 22 ülke ve 43 kurumu kapsıyor.':'2026–2028 dönemine ilişkin araştırma ağı afişlerinde, COST başvuruları, ortak yayınlar, projeler ve akademik görüşmeler kapsamında 22 ülkeden 43 kurum yer alıyor.',
 'Paylaşılan iki afişin web için optimize edilmiş gösterimleri.':'Araştırma ağına ilişkin iki afişin web ortamına uyarlanmış sürümleri.',
 'Kurum adları ve 22/43 toplamları paylaşılan afişleri izler.':'Kurum listesi ve sayısal bilgiler, araştırma ağı afişlerinde yer alan kayıtlara dayanmaktadır.',
 'Araştırma zaman çizelgesi':'Araştırma geçmişi',
 'Seçilmiş araştırma soruları, yayınlar ve akademik dönüm noktaları boyunca tarihli bir yolculuk.':'Araştırma konularının, seçilmiş yayınların ve akademik çalışmaların yıllara göre gelişimi.',
 'Görevler ve yayınlardan seçilmiş bir anlatım; eksiksiz kariyer kronolojisi veya araştırmanın gelişimine ilişkin nedensel açıklama değildir.':'Çizelge, akademik çalışmaların ve seçilmiş yayınların başlıca dönüm noktalarını göstermektedir.',
 'Sunulmuş, planlanan ve geliştirilmekte olan.':'Araştırma başvuruları ve hazırlık aşamasındaki çalışmalar',
 'Destek vaadi değil, durum bilgisi':'Başvuruların güncel durumları',
 '7 öneri. Farklı aşamalar.':'Araştırma önerileri ve başvuru durumları',
 'Kurum adları ve 22/43 toplamları paylaşılan afişleri izler. Kişisel profillerdeki ek kurumlar, bu afiş kaydının toplamlarını değiştirmez.':'Kurumlar ve ülke sayıları, 2026–2028 araştırma ağı afişlerinde yer alan bilgiler esas alınarak derlenmiştir. Araştırmacıların kişisel profillerinde başka kurum bağlantıları da bulunabilir.',
}
# Important simplifications: remove habitual draft-editor disclaimers from public copy.
REMOVE_FRAGMENTS=[
 'Öngörülen bitiş tarihleri plan niteliğindedir; kazanılmış derece değildir.',
 'Burada yeni bir araştırma bulgusu ileri sürülmemektedir.',
]


def polish(docs):
    for name, soup in docs.items():
        main=soup.main
        if main is None:continue
        for text_node in list(main.descendants):
            if not isinstance(text_node,NavigableString):continue
            parent=text_node.parent
            if parent is None or parent.name in ('script','style','svg','math'):continue
            # Titles of original publications and citations must remain verbatim.
            if parent.find_parent(attrs={'data-original-language':'en'}) or parent.get('data-original-language')=='en':continue
            if parent.find_parent(attrs={'lang':'en'}) or parent.get('lang')=='en':continue
            val=str(text_node);new=val
            for old, replacement in sorted(REPL.items(),key=lambda x:len(x[0]),reverse=True):
                if old in new:new=new.replace(old,replacement)
            for rem in REMOVE_FRAGMENTS:new=new.replace(rem,'')
            new=re.sub(r'\s+\.', '.', new)
            if new!=val:text_node.replace_with(new)
        # Remove empty paragraphs left by trimming redundant source notes.
        for p in list(main.find_all('p')):
            if not p.get_text(' ',strip=True) and not p.find('img') and not p.get('id') and not p.get('aria-live'):p.decompose()
        # Headings often contain italic children; a literal-string map cannot cover these.
        heading_overrides={
            'index.html':'Yapay zekâ destekli öğrenme ve bağımsız düşünme',
            'research.html':'Bilimsel düşünmeyi merkeze alan araştırmalar',
            'projects.html':'Araştırma projeleri ve başvurular',
            'team.html':'Araştırma ekibi ve iş birlikleri',
            'join.html':'Araştırma iş birliği için iletişime geçin',
            'resources.html':'Öğretim ve araştırma kaynakları',
            'proposals.html':'Araştırma önerileri ve başvuru durumları',
            'editorial.html':'Editoryal çalışmalar ve özel koleksiyonlar',
            'about.html':'Akademik özgeçmiş ve çalışmalar',
            'practice.html':'Araştırmadan sınıf uygulamalarına',
            'contact.html':'Araştırma ve iş birliği için iletişim',
            'research-network.html':'Uluslararası araştırma ağı',
            'research-timeline.html':'Araştırma geçmişi',
            'open-research.html':'Araştırma yöntemleri ve açık bilim',
        }
        if name in heading_overrides:
            oldhead=main.find('h1')
            if oldhead:oldhead.string=heading_overrides[name]
        if name=='projects.html':
            for h in main.select('h2'):
                if h.get_text(' ',strip=True).startswith('Diğer desteklenen projeler'):h.string='Desteklenen araştırma projeleri'
                elif h.get_text(' ',strip=True).startswith('Tamamlanan destekli araştırma'):h.string='Tamamlanan araştırma projesi'
        if name=='proposals.html':
            for h in main.select('h2'):
                if h.get_text(' ',strip=True).startswith('7 öneri'):h.string='Başvuruların aşamalara göre dağılımı'
        for h in main.select('h1,h2,h3'):
            content=h.get_text(' ',strip=True)
            if content.endswith('.') and not content.endswith('...'):
                # Avoid only changing an English title or scientific abbreviation.
                if not h.has_attr('lang') and not h.find_parent(attrs={'lang':'en'}):
                    last=h.find_all(string=True)
                    if last:last[-1].replace_with(str(last[-1]).rstrip().removesuffix('.'))
        # Update Turkish title/metadata after editing, retaining indexed original publication text.
        h1=main.find('h1')
        if h1 and soup.title:
            title=h1.get_text(' ',strip=True)
            soup.title.string=title+' | Hüseyin Ateş'
            for selector in ('meta[property="og:title"]','meta[name="twitter:title"]'):
                node=soup.select_one(selector)
                if node:node['content']=title+' | Hüseyin Ateş'
            lead=main.select_one('.pagehero p.lead') or main.select_one('p.lead')
            if lead:
                summary=lead.get_text(' ',strip=True)[:155]
                for selector in ('meta[name="description"]','meta[property="og:description"]','meta[name="twitter:description"]'):
                    node=soup.select_one(selector)
                    if node:node['content']=summary
    return docs
