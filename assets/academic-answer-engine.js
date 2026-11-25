/* Factual answer rules, not a language model. Public data and links are built
 * from the final bilingual site. No network access and no persistent storage. */
(()=>{'use strict';
const clean=s=>String(s??'').toLocaleLowerCase('tr').replaceAll('ı','i').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const stops=new Set('ve bir bu su ile icin ne nasil nedir kim kimdir hangi bana benim sen siz sizin huseyin ates lutfen bilgi hakkinda verir misin misiniz var mi mu peki acaba the a an and or to of in on for what how who which is are does do about tell please his her it they their'.split(' '));
const terms=s=>[...new Set(clean(s).split(' ').filter(x=>x.length>1&&!stops.has(x)))];
const safe=r=>/^[a-z0-9-]+\.html(?:#[a-zA-Z0-9_-]+)?$/.test(r.url||'');
function create(data,corpus){
 const tr=data.lang==='tr', p=(en,turkish)=>tr?turkish:en;
 let lastPerson=null,lastProject=null;
 const source=(title,url)=>({title,url});
 const dedupe=xs=>[...new Map(xs.filter(safe).map(x=>[x.url,x])).values()];
 const result=(text,sources=[])=>({text,sources:dedupe(sources)});
 const contact=()=>source(p('Contact','İletişim'),'contact.html');
 const memberNames=Object.entries(data.people).map(([slug,v])=>({slug,v,words:clean(v.name).split(' ').filter(w=>!['dr','doc','prof','assoc','assist','ogr','uyesi'].includes(w))}));
 const compiled=corpus.records.map(r=>({...r,n:clean(r.text),t:clean(r.title),tokens:new Set(terms(r.text))}));
 const df=new Map();for(const r of compiled)for(const w of r.tokens)df.set(w,(df.get(w)||0)+1);
 function personMatches(q){
  const words=clean(q).split(' ');
  const scores=memberNames.map(x=>({...x,score:x.words.filter(w=>w.length>=3&&w!=='ates'&&words.some(z=>z===w||(w.length>=4&&z.startsWith(w)&&z.length-w.length<=5))).length}));
  const best=Math.max(0,...scores.map(x=>x.score));
  return best?scores.filter(x=>x.score===best):[];
 }
 function projectKey(n){
  if(/sciepi/.test(n))return 'cost';
  if(data.projects.endueai&&/\bca\s?25177\b|\bendueai\b|\bwg\s?[16]\b/.test(n))return 'endueai';
  if(/\b3501\b|fiziksel.*robot|insansi.*robot|humanoid|virtual agent|sanal ajan/.test(n))return '3501';
  if(/\baub\b|\bbae\b|\buae\b|anadolu univers|turkiye.*stem/.test(n))return 'aub';
  if(/\b1002\b|226k999|uzay kirlil|space pollution|space debris/.test(n))return '1002';
  for(const key of ['2219','2221','cost','erc','dfg'])if(new RegExp('\\b'+key+'\\b').test(n))return key;
  if(/surrey|fading|azaltil/.test(n))return '2219';
  if(/reclaim/.test(n))return 'erc';return null;
 }
 function answer(question){
  const n=clean(question),explicitProject=projectKey(n),matches=personMatches(n);
  const follow=/^(peki|ya |and |what about|how about|onun|bu |bunun|o |onlar)|katki|gorevi|kurumu|hangi kurum|ne is|hangi proje|durumu|destek|sonuc|ekibi|funded|contribut|affiliat|status/.test(n);
  const contribution=/katki|sorumluluk|ne yap|gorev|teknik|yazilim|gelistir|analiz|olcme|contribut|responsib|technical|software/.test(n);
  const institution=/kurum|universite|nerede|nerde|hangi okul|where.*work|institution|affiliat|university/.test(n);
  const roster=/kimler|ekip|arastirmacilar|danismanlar|team|members|who.*work|who.*involve/.test(n);
  const status=/durum|asama|destek|fon|kabul|sonuc|basladi|bitti|tamamlan|onay|status|fund|award|accept|completed|stage/.test(n);
  // Never turn unrelated requests into a roster merely because they follow a project question.
  if(/ignore.*instruct|onceki.*talimat|sistem.*prompt|api.*anahtar|api.*key|sifre/.test(n))return result(p('Please do not share passwords or private data. I can answer questions about the public research records.','Lütfen şifre veya özel bilgi paylaşmayın. Açık araştırma kayıtları hakkında yardımcı olabilirim.'));
  if(/^(tesekkur|sag ol|thanks|thank you)/.test(n))return result(p('You’re welcome. What else would you like to know about the research?','Rica ederim. Araştırmalarla ilgili başka ne öğrenmek istersiniz?'));
  if(/^(nasilsin|how are you)/.test(n))return result(p('I’m ready to help. We can discuss the research, projects or collaboration options.','Yardımcı olmaya hazırım. Araştırmalar, projeler veya iş birliği seçenekleri hakkında konuşabiliriz.'));
  // Do not substitute a generic contact disclaimer for an actual email-address question.
  if(/iletisim|e posta|eposta|email|e mail|mail adres|nasil.*ulas|contact/.test(n)&&!matches.length){
   const address=data.email;
   return result(p(`You can contact Hüseyin Ateş${address?' at '+address:''}. For a research collaboration, briefly describe your topic, intended contribution and proposed way of working. Messages typed here are not sent to him.`,
    `Hüseyin Ateş’e${address?' '+address+' adresinden':''} ulaşabilirsiniz. Araştırma iş birliği için konunuzu, sunabileceğiniz katkıyı ve önerdiğiniz çalışma biçimini kısaca belirtmeniz yararlı olur. Buraya yazdıklarınız kendisine iletilmez.`),[contact()]);
  }
  if(/is birligi|birlikte calis|gruba katil|ekibe katil|collaborat|join.*(group|team)/.test(n)&&!matches.length&&!explicitProject){
   return result(p('You can share a research or collaboration proposal through the interest form linked from the site. Describe your topic, relevant experience and intended contribution. The form is an expression of interest, not an admission or appointment decision.',
    'Araştırma veya iş birliği önerinizi sitedeki ilgi formuyla paylaşabilirsiniz. Konunuzu, ilgili deneyiminizi ve sunabileceğiniz katkıyı belirtin. Bu form ilgi bildirimi içindir; kabul ya da görevlendirme kararı oluşturmaz.'),[source(p('Research and collaboration','Araştırma ve iş birliği'),'join.html'),contact()]);
  }
  if(/(yuksek lisans|doktora|master|phd|graduate).*(basvur|kabul|kontenjan|admission|apply|position)|beni.*kabul/.test(n)&&!matches.length){
   return result(p('Graduate admission follows the university’s official application process. The website does not establish a current vacancy or an admission decision for you. You can ask Hüseyin Ateş about research fit through the contact page.',
    'Lisansüstü kabul, üniversitenin resmî başvuru süreciyle yürütülür. Sitedeki bilgiler güncel kontenjan veya sizin için verilmiş bir kabul kararı göstermez. Araştırma konunuzun uygunluğunu iletişim sayfasından Hüseyin Ateş’e sorabilirsiniz.'),[source(p('Research enquiries','Araştırma talepleri'),'join.html'),contact()]);
  }
  if(data.projects.endueai&&data.projects.cost&&/\bcost\b/.test(n)&&!/sciepi|\bca\s?25177\b|\bendueai\b|\bwg\s?[16]\b/.test(n)&&!matches.length){
   lastPerson=null;lastProject=null;const network=data.projects.endueai,proposal=data.projects.cost;
   const groups=(network.groups||[]).map(g=>g.code+': '+g.title).join('; ');
   return result(p('COST activities:','COST çalışmaları:')+`\n\n• ${network.title}: ${network.stage}.${groups?'\n'+groups+'.':''}\n\n• ${proposal.title}: ${proposal.stage}.`,[source(network.title,network.url),source(proposal.title,proposal.url)]);
  }
  if(matches.length>1 && !explicitProject){
   return result(p('Which researcher are you asking about? ','Hangi araştırmacıyı soruyorsunuz? ')+matches.map(x=>x.v.name).join(' / '),matches.slice(0,4).map(x=>source(x.v.name,x.v.url)));
  }
  const person=matches.length===1?matches[0]:(!explicitProject&&follow&&lastPerson?{slug:lastPerson,v:data.people[lastPerson]}:null);
  if(person){
   lastPerson=person.slug;lastProject=null;const r=person.v;const refs=[source(r.name,r.url),...r.studies.map(x=>source(x.title,x.url))];
   if(r.visiting_2221&&(explicitProject==='2221'||(!explicitProject&&/\bvisit\w*|\bziyaret\w*/.test(n)))){
    const visit=r.visiting_2221,study=r.studies.find(x=>x.url.split('#')[0]==='proposal-visiting-researchers-2221.html');
    const visitSource=study?source(study.title,study.url):source('TÜBİTAK 2221','proposal-visiting-researchers-2221.html');
    return result(`${r.name} · TÜBİTAK 2221\n${visit.stage}.\n\n${visit.scope}\n\n${p('Proposed visit','Planlanan ziyaret')}: ${visit.planned_visit}.`,[visitSource,refs[0]]);
   }
   if(contribution){
    if(r.contribution)return result(`${r.name}: ${r.contribution}`,refs);
    return result(p(`${r.name} is listed as ${r.role.toLowerCase()}. A more detailed division of technical, measurement or analysis duties is not specified in the public profile; it would be inaccurate to assign one.`,
      `${r.name}, sitede “${r.role}” rolüyle yer alıyor. Teknik geliştirme, ölçme veya analiz gibi ayrıntılı görevleri açık profilde belirtilmemiş; bu görevleri kendisine atamak doğru olmaz.`),refs);
   }
   if(institution){
    return result(r.institutions.length?p(`${r.name} is affiliated with ${r.institutions.join('; ')}.`,`${r.name} için kayıtlı kurum: ${r.institutions.join('; ')}.`):
      p(`${r.name} is listed as an independent researcher, with no current institutional affiliation.`,`${r.name} bağımsız araştırmacı olarak listeleniyor; güncel kurumsal bağlılığı bulunmuyor.`),[refs[0]]);
   }
   if(explicitProject){
    const t=data.projects[explicitProject],member=t.members.some(x=>x.slug===person.slug);
    if(member)return result(p(`${r.name} is listed on the ${t.title} team. ${t.stage}.`,`${r.name}, ${t.title} ekibinde yer alıyor. ${t.stage}.`),[source(t.title,t.url),refs[0]]);
    return result(p(`The public record does not confirm ${r.name} as a member of that team.`,`${r.name} için bu ekipte üyelik, açık kayıtlarda doğrulanmıyor.`),refs);
   }
   if(r.studies.length){
    const label=p(`${r.name} participates in the following application${r.studies.length>1?'s':''}:`,`${r.name} şu başvurularda yer alıyor:`);
    const projects=r.studies.map(x=>'• '+x.title).join('\n');
    return result(`${label}\n${projects}${r.stage?'\n\n'+r.stage+'.':''}`,refs);
   }
   const detail=r.focus||r.contribution||r.role;
   return result(`${r.name}: ${detail}${r.degree?'\n'+r.degree:''}`,refs);
  }
  const key=explicitProject||(!lastPerson&&follow?lastProject:null);
  if(key&&data.projects[key]){
   lastProject=key;lastPerson=null;const r=data.projects[key];const refs=[source(r.title,r.url),source(p('Project teams','Proje ekipleri'),'team.html#project-researchers')];
   if(key==='endueai')return result(`${r.title}\n${r.lead||'Hüseyin Ateş'}\n${r.stage}.\n\n${(r.groups||[]).map(g=>'• '+g.code+': '+g.title).join('\n')}${r.duration?'\n\n'+p('Action period: ','Aksiyon dönemi: ')+r.duration+'.':''}`,[refs[0]]);
   if(contribution&&!roster)return result(p('The website provides the team’s roles, but does not assign every technical work package. Name a researcher to check their documented contribution.',
    'Site ekip üyelerinin rollerini gösteriyor; her teknik iş paketini ayrı ayrı atamıyor. Bir araştırmacının adını yazarak kayıtlı katkısını sorabilirsiniz.'),refs);
   if(roster){
    if(!r.members.length)return result(p('A named team roster is not published for this application. The project record is linked below.','Bu başvuru için adlandırılmış ekip listesi yayımlanmamış. İlgili proje kaydı aşağıda.'),[refs[0]]);
    const lead=p('Research lead: Hüseyin Ateş.','Yürütücü: Hüseyin Ateş.');
    return result(`${r.title}\n${lead}\n\n${r.members.map(m=>'• '+m.name+' — '+m.role).join('\n')}\n\n${r.stage}.`,refs);
   }
   if(status){
    return result(`${r.title}: ${r.stage}.${r.reviewed?'\n'+p('Status record last reviewed: ','Durum kaydının son kontrolü: ')+r.reviewed+'.':''}`, [refs[0]]);
   }
   return result(`${r.title}. ${r.summary}\n\n${r.stage}.${r.reviewed?'\n'+p('Status record: ','Durum kaydı: ')+r.reviewed+'.':''}`,[refs[0]]);
  }
  if(/ozgecmis|\bcv\b|biograph/.test(n))return result(p('The About & CV page provides Hüseyin Ateş’s academic background and downloadable CV editions in Turkish and English. Their content dates are shown separately from the page-update date.',
   'Hakkımda ve Özgeçmiş sayfasında Hüseyin Ateş’in akademik geçmişi ile Türkçe ve İngilizce özgeçmiş dosyaları bulunuyor. Özgeçmişin içerik tarihi, sayfanın güncelleme tarihinden ayrı gösteriliyor.'),[source(p('About & CV','Hakkımda ve Özgeçmiş'),'about.html')]);
  if(/yayin|makale|publication|paper/.test(n)&&!explicitProject){
   let pubs=data.publications;
   const year=n.match(/\b20\d{2}\b/);if(year)pubs=pubs.filter(x=>x.year.includes(year[0]));
   const ks=terms(n).filter(k=>!['yayin','yayinlar','yayinlari','makale','makaleler','son','guncel','recent','publications','latest','papers'].some(w=>k.startsWith(w))&&!/^20\d{2}$/.test(k));
   if(ks.length){const ranked=pubs.map(x=>({x,score:ks.filter(k=>clean(x.citation).includes(k)).length})).filter(x=>x.score).sort((a,b)=>b.score-a.score);if(ranked.length)pubs=ranked.map(x=>x.x);}
   if(!pubs.length)return result(p('No matching publication is listed in the public catalogue.','Açık yayın kataloğunda eşleşen bir kayıt bulunmuyor.'),[source(p('Publications','Yayınlar'),'publications.html')]);
   return result(p('Selected records from the website’s publication list:\n','Sitenin yayın listesinden seçili kayıtlar:\n')+pubs.slice(0,3).map(x=>'• '+x.citation.replace(/\s*↗/g,'')).join('\n\n'),[source(p('Full publication list and DOI links','Tam yayın listesi ve DOI bağlantıları'),'publications.html')]);
  }
  if(/arastirma alan|hangi konu|ne.*calis|calisma alan|research (area|focus|topic)|what.*research|huseyin ates kim|huseyin kim/.test(n)){
   lastPerson=null;lastProject=null;
   return result(p('Hüseyin Ateş works on human-centered artificial intelligence, scientific reasoning and self-regulated learning in science/STEM education. His studies address AI feedback design, independent reasoning after support is removed, and educational uses of VR, AR and robotics.',
    'Hüseyin Ateş; fen ve STEM eğitiminde insan odaklı yapay zekâ, bilimsel akıl yürütme ve öz düzenlemeli öğrenme üzerine çalışıyor. Araştırmaları, yapay zekâ geri bildiriminin tasarımını, destek kaldırıldıktan sonraki bağımsız akıl yürütmeyi ve sanal/artırılmış gerçeklik ile eğitsel robotiğin kullanımını kapsıyor.'),[source(p('Research areas','Araştırma alanları'),'research.html')]);
  }
  // Unknown private details must not be reconstructed from superficially similar pages.
  if(/ozel telefon|cep telefonu|maas|ev adres|private (phone|address)|salary|telefon numar/.test(n))return result(p('I can only use the public contact information on the website. No private contact details are provided.','Yalnızca sitede yayımlanan iletişim bilgilerini kullanabilirim. Özel iletişim bilgisi paylaşılmıyor.'),[contact()]);
  if(!follow){lastPerson=null;lastProject=null;}return null;
 }
 function scoreText(value,keys){
  const words=clean(value).split(' ');let score=0;
  for(const k of keys){if(words.some(w=>w===k||(k.length>=4&&w.startsWith(k)&&w.length-k.length<=5)))score+=1+Math.log(1+compiled.length/(1+(df.get(k)||0)));}
  return score;
 }
 function excerpt(record,question,max=650){
  const keys=terms(question);const sentences=record.text.split(/(?<=[.!?])\s+/).filter(x=>x.trim().length>20);
  const best=sentences.map((s,i)=>({s,i,score:scoreText(s,keys)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,3).sort((a,b)=>a.i-b.i);
  let value='';for(const x of best){if(value.length+x.s.length>max&&value)continue;value+=(value?' ':'')+x.s;}
  if(!value)value=record.text;
  if(value.length>max){const cut=value.lastIndexOf(' ',max);value=value.slice(0,cut>max/2?cut:max)+'…';}
  return value;
 }
 function retrieve(question){
  const keys=terms(question);if(!keys.length)return [];
  const named=personMatches(question);const specific=projectKey(clean(question));
  const ranked=compiled.map(r=>{
   let score=scoreText(r.text,keys)+2*scoreText(r.title,keys);
   if(named.length===1){if(r.url.split('#')[0]===named[0].v.url)score+=40;else score*=.3;}
   if(specific&&data.projects[specific]){if(r.url.split('#')[0]===data.projects[specific].url.split('#')[0])score+=20;}
   const hits=keys.filter(k=>r.tokens.has(k)||[...r.tokens].some(w=>k.length>=4&&w.startsWith(k))).length;
   return {r,score,hits};
  }).filter(x=>x.hits>0&&x.score>=4).sort((a,b)=>b.score-a.score);
  const records=[],seen=new Set();for(const {r} of ranked){if(seen.has(r.url))continue;seen.add(r.url);records.push({title:r.title,url:r.url,text:excerpt(r,question,1800)});if(records.length===3)break;}return records;
 }
 return {answer,retrieve,excerpt,reset(){lastPerson=null;lastProject=null;}};
}
window.AcademicAnswerEngine={create};
})();
