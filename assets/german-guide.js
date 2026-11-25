/* German public-record guide. Deterministic source rules, not a generative model.
   The corpus is built only from translated public pages. No remote requests. */
(()=>{'use strict';
const clean=s=>String(s??'').toLowerCase().replaceAll('ı','i').replaceAll('ß','ss').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const safe=url=>/^[a-z0-9-]+\.html(?:#[\w-]+)?$/.test(url||'');
const stop=new Set('der die das den dem des ein eine einer einem eines und oder zu zur zum fur von mit wie was wer wo welche welchen welcher ist sind hat haben bitte uber auf in im an am es sie er ihr seine ihre davon dazu auch ich du ihr'.split(' '));
const terms=q=>[...new Set(clean(q).split(' ').filter(x=>x.length>2&&!stop.has(x)))];
function create(data,corpus){
 let lastPerson=null,lastProject=null;
 const ref=(title,url)=>({title,url});
 const result=(text,sources=[])=>({text,sources:[...new Map(sources.filter(r=>safe(r.url)).map(r=>[r.url,r])).values()]});
 const people=Object.entries(data.people).map(([slug,v])=>({slug,v,words:clean(v.name).split(' ').filter(x=>!['dr','prof','assoc','assist','ates'].includes(x))}));
 function matches(q){const qs=clean(q).split(' ');const found=people.map(x=>({...x,score:x.words.filter(w=>w.length>2&&qs.some(k=>k===w||(k.startsWith(w)&&k.length-w.length<4))).length}));const max=Math.max(0,...found.map(x=>x.score));return max?found.filter(x=>x.score===max):[];}
 function project(q){
  if(/sciepi/.test(q))return 'cost';
  if(data.projects.endueai&&/\bca\s?25177\b|\bendueai\b|\bwg\s?[16]\b/.test(q))return 'endueai';
  if(/3501|humanoid|virtuell.*agent|physisch.*robot/.test(q))return '3501';
  if(/\baub\b|\bvae\b|\buae\b|emirat|anadolu.*verband/.test(q))return 'aub';
  if(/1002|226k999|weltraum/.test(q))return '1002';
  if(/2219|surrey|verringerung.*feedback|feedback.*verringerung/.test(q))return '2219';
  if(/2221|gastforsch/.test(q))return '2221';
  if(/\berc\b|reclaim/.test(q))return 'erc';if(/\bcost\b/.test(q))return 'cost';if(/\bdfg\b|krell.*konzept/.test(q))return 'dfg';return null;
 }
 function answer(question){
  const q=clean(question),found=matches(q),key=project(q);
  const follow=/^(und|was ist mit|wie sieht|seine|ihre|dessen|deren|dazu|dabei|es|sie|er)\b|status|institution|universitat|beitrag|aufgabe|forderung/.test(q);
  const task=/beitrag|aufgabe|verantwort|tatigkeit|technisch|software|analyse|entwickelt/.test(q);
  const affiliation=/institution|universitat|hochschule|schule|arbeitet|beschaftigt|zugehorig/.test(q);
  const roster=/team|mitglied|beteiligt|wer.*(arbeitet|forscht|gehort)|forschenden/.test(q);
  const stage=/status|stand|forderung|gefordert|bewilligt|entscheidung|abgeschlossen|fertig|laufzeit/.test(q);
  if(/^(hallo|guten tag|guten morgen|servus|hi|hello)$/.test(q))return result('Guten Tag. Sie können Fragen zu Forschung, Projektteams und Kooperationsmöglichkeiten stellen.');
  if(/wer bist|wer sind sie|bist du huseyin|sind sie huseyin/.test(q))return result('Ich bin der Website-Wegweiser, nicht Hüseyin Ateş. Ich nutze veröffentlichte Einträge und übermittle ihm keine Nachrichten.');
  if(/^(danke|vielen dank|besten dank)/.test(q))return result('Gern. Was möchten Sie noch über die Forschung erfahren?');
  if(/passwort|api schlussel|system prompt|ignoriere.*anweisung/.test(q))return result('Bitte teilen Sie keine Passwörter oder privaten Daten. Ich helfe bei Fragen zu öffentlichen Forschungseinträgen.');
  if(/kontakt|e mail|email|erreich|termin|nachricht.*(senden|schicken)/.test(q)&&!found.length)return result(`Sie erreichen Hüseyin Ateş unter ${data.email}. Beschreiben Sie bei einer Kooperationsanfrage kurz Ihr Thema und den vorgesehenen Beitrag. Dieser Chat versendet keine Nachrichten und vereinbart keine Termine.`,[ref('Kontakt','contact.html')]);
  if(/zusammenarbeit|kooperat|mitmachen|gruppe.*beitret/.test(q)&&!found.length&&!key)return result('Teilen Sie Ihre Forschungsfrage, Ihren Hintergrund und Ihren möglichen Beitrag über das Interessenformular auf der Website. Das Formular ist eine Interessenbekundung, keine Zulassung oder Stellenzusage.',[ref('Zusammenarbeit','join.html'),ref('Kontakt','contact.html')]);
  if(/(master|promotion|doktor).*(bewerb|zulass|platz)|stipendium.*bekomm/.test(q)&&!found.length&&!key)return result('Die Zulassung erfolgt nach den offiziellen Verfahren der Universität. Die Website bestätigt keine aktuelle freie Stelle oder individuelle Zulassung. Die fachliche Passung Ihres Vorhabens können Sie direkt mit Hüseyin Ateş besprechen.',[ref('Anfragen','join.html'),ref('Kontakt','contact.html')]);
  if(data.projects.endueai&&data.projects.cost&&/\bcost\b/.test(q)&&!/sciepi|\bca\s?25177\b|\bendueai\b|\bwg\s?[16]\b/.test(q)&&!found.length){
   lastPerson=null;lastProject=null;const network=data.projects.endueai,proposal=data.projects.cost;
   const groups=(network.groups||[]).map(g=>g.code+': '+g.title).join('; ');
   return result(`COST-Aktivitäten:\n\n• ${network.title}: ${network.stage}.${groups?'\n'+groups+'.':''}\n\n• ${proposal.title}: ${proposal.stage}.`,[ref(network.title,network.url),ref(proposal.title,proposal.url)]);
  }
  if(found.length>1)return result('Welche Person meinen Sie? '+found.map(x=>x.v.name).join(' / '),found.slice(0,4).map(x=>ref(x.v.name,x.v.url)));
  const person=found.length===1?found[0]:(!key&&follow&&lastPerson?{slug:lastPerson,v:data.people[lastPerson]}:null);
  if(person){
   lastPerson=person.slug;lastProject=null;const r=person.v,refs=[ref(r.name,r.url),...r.studies.map(x=>ref(x.title,x.url))];
   if(r.visiting_2221&&(key==='2221'||(!key&&/\bbesuch\w*|aufenthalt\w*|\bvisit\w*/.test(q)))){
    const visit=r.visiting_2221,study=r.studies.find(x=>x.url.split('#')[0]==='proposal-visiting-researchers-2221.html');
    const visitSource=study?ref(study.title,study.url):ref('TÜBİTAK 2221','proposal-visiting-researchers-2221.html');
    return result(`${r.name} · TÜBİTAK 2221\n${visit.stage}.\n\n${visit.scope}\n\nGeplanter Aufenthalt: ${visit.planned_visit}.`,[visitSource,refs[0]]);
   }
   if(person.slug==='naomi-winstone'&&/artikel|manuskript|publikat|autor/.test(q))return result('Für Naomi Winstone ist die vorgesehene akademische Gastbetreuung im TÜBİTAK-2219-Vorhaben an der University of Surrey dokumentiert. Eine Manuskriptmitwirkung wird auf der Website nicht ausgewiesen.',[ref(r.name,r.url),ref('TÜBİTAK-2219-Antrag','proposal-feedback-fading.html')]);
   if(task)return result(r.contribution?`${r.name}: ${r.contribution}`:`${r.name} wird mit der Rolle „${r.role}“ geführt. Eine detaillierte Zuweisung technischer, analytischer oder methodischer Aufgaben ist im öffentlichen Profil nicht angegeben.`,refs);
   if(affiliation)return result(r.institutions.length?`${r.name}: ${r.institutions.join('; ')}.`:`${r.name} wird als unabhängig forschende Person ohne aktuelle institutionelle Zugehörigkeit geführt.`,[refs[0]]);
   if(key&&data.projects[key]){const pr=data.projects[key];return result(pr.members.some(m=>m.slug===person.slug)?`${r.name} gehört zum Team von ${pr.title}. ${pr.stage}.`:`Eine Mitgliedschaft von ${r.name} in diesem Team ist im öffentlichen Eintrag nicht bestätigt.`,[refs[0],ref(pr.title,pr.url)]);}
   if(r.studies.length)return result(`${r.name} ist an folgenden Vorhaben beteiligt:\n${r.studies.map(x=>'• '+x.title).join('\n')}${r.stage?'\n\n'+r.stage+'.':''}`,refs);
   return result(`${r.name}: ${r.focus||r.contribution||r.role}${r.degree?'\n'+r.degree:''}`,refs);
  }
  const pk=key||(!lastPerson&&follow?lastProject:null);
  if(pk&&data.projects[pk]){
   lastProject=pk;lastPerson=null;const r=data.projects[pk],refs=[ref(r.title,r.url)];
   if(pk==='endueai')return result(`${r.title}\n${r.lead||'Hüseyin Ateş'}\n${r.stage}.\n\n${(r.groups||[]).map(g=>'• '+g.code+': '+g.title).join('\n')}${r.duration?'\n\nLaufzeit der COST-Aktion: '+r.duration+'.':''}`,refs);
   if(roster){if(!r.members.length)return result('Für dieses Vorhaben ist keine namentliche Teamliste veröffentlicht. Die Projektangaben finden Sie im verlinkten Eintrag.',refs);
    return result(`${r.title}\nProjektleitung: Hüseyin Ateş.\n\n${r.members.map(x=>'• '+x.name+' – '+x.role).join('\n')}\n\n${r.stage}.`,[...refs,ref('Projektteams','team.html#project-researchers')]);}
   if(stage)return result(`${r.title}: ${r.stage}.${r.reviewed?'\nLetzte Prüfung des Statuseintrags: '+r.reviewed+'.':''}${/laufzeit/.test(q)&&r.duration?'\n'+r.duration:''}`,refs);
   return result(`${r.title}. ${r.summary}\n\n${r.stage}.`,refs);
  }
  if(/lebenslauf|\bcv\b|werdegang/.test(q))return result('Auf der Seite „Über mich und Lebenslauf“ finden Sie den akademischen Werdegang sowie Lebensläufe auf Englisch und Türkisch. Deren Inhaltsdaten sind getrennt vom Aktualisierungsdatum der Seite angegeben.',[ref('Über mich und Lebenslauf','about.html')]);
  if(/publikat|veroffentlich|artikel|papers/.test(q)){
   let pubs=data.publications;const year=q.match(/\b20\d{2}\b/);if(year)pubs=pubs.filter(x=>x.year.includes(year[0]));
   if(!pubs.length)return result('Im öffentlichen Verzeichnis wurde keine passende Publikation gefunden.',[ref('Publikationen','publications.html')]);
   return result('Ausgewählte Originaleinträge aus dem Publikationsverzeichnis:\n\n'+pubs.slice(0,3).map(x=>'• '+x.citation).join('\n\n'),[ref('Publikationen und DOI-Links','publications.html')]);
  }
  if(/forschungsgebiet|forschungsschwerpunkt|woran.*(forscht|arbeitet)|welche.*themen|wer ist huseyin/.test(q)){
   lastPerson=null;lastProject=null;
   return result('Hüseyin Ateş forscht zu menschenzentrierter KI, wissenschaftlichem Schlussfolgern und selbstreguliertem Lernen in der naturwissenschaftlichen und MINT-Bildung. Weitere Schwerpunkte sind KI-Feedback, eigenständiges Schlussfolgern nach dem Wegfall von Unterstützung sowie VR, AR und Robotik im Bildungsbereich.',[ref('Forschungsgebiete','research.html'),ref('Über Hüseyin Ateş','about.html')]);
  }
  return null;
 }
 function retrieve(question){const ks=terms(question);if(!ks.length)return[];const scored=(corpus.records||[]).map(r=>{const t=clean(r.title),b=clean(r.text);return {r,score:ks.reduce((n,k)=>n+(b.includes(k)?1:0)+(t.includes(k)?3:0),0)};}).filter(x=>x.score>=Math.min(2,ks.length)).sort((a,b)=>b.score-a.score);return [...new Map(scored.map(x=>[x.r.url,x.r])).values()].slice(0,3);}
 function excerpt(r,q,limit=500){const ks=terms(q);const sentences=r.text.match(/[^.!?]+[.!?]+|[^.!?]+$/g)||[r.text];const rows=sentences.map((s,i)=>({s,i,score:ks.filter(k=>clean(s).includes(k)).length})).sort((a,b)=>b.score-a.score).slice(0,3).sort((a,b)=>a.i-b.i);const value=rows.map(x=>x.s.trim()).join(' ');return value.length>limit?value.slice(0,limit)+' …':value;}
 return {answer,retrieve,excerpt,reset(){lastPerson=null;lastProject=null;}};
}
window.AcademicAnswerEngine={create};
})();
