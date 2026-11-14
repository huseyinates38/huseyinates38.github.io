/* v3: source guide plus opt-in server conversation; no model download or secret. */
(()=>{'use strict';
const $=id=>document.getElementById(id),root=$('academic-chat');if(!root)return;
const tr=document.documentElement.lang==='tr',p=(en,t)=>tr?t:en;
const config=JSON.parse($('assistant-service-config').textContent),facts=JSON.parse($('assistant-facts').textContent),kb=JSON.parse($('assistant-knowledge').textContent);
const engine=window.AcademicAnswerEngine.create(facts,kb);
const form=$('chat-form'),q=$('chat-question'),log=$('chat-log'),send=$('chat-send'),status=$('chat-status'),stop=$('chat-stop'),clear=$('chat-clear'),mode=$('chat-mode');
const enable=$('cloud-enable'),consent=$('cloud-consent'),cloudState=$('cloud-state');
let history=[],busy=false,remote=false,abort=null,epoch=0,lastReply=null;
const endpoint=config.endpoint||'';
const safe=s=>/^(?:tr\/)?[a-z0-9-]+\.html(?:#[\w-]+)?$/.test(s||'');
function node(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n;}
function label(){mode.textContent=remote?p('AI conversation · server','Yapay zekâ sohbeti · sunucu'):p('Website guide · not a generative model','Site rehberi · üretken model değil');}
function controls(){send.disabled=busy;q.disabled=false;stop.hidden=!busy;enable.disabled=busy||!endpoint;log.setAttribute('aria-busy',String(busy));label();}
function announce(s){status.textContent=s;}
function scroll(){log.scrollTop=log.scrollHeight;}
function message(who,text,caption){const a=node('article','chat-message chat-'+who);a.append(node('div','chat-message-label',caption||p(who==='user'?'You':'Assistant',who==='user'?'Siz':'Asistan')));const b=node('div','chat-message-text',text);a.append(b);log.append(a);scroll();return {article:a,body:b};}
function sources(a,refs,server=false){if(!refs?.length)return;const box=node('details','chat-sources'),summary=node('summary','',p('Sources','Kaynaklar')+' ('+refs.length+')'),ul=node('ul');
 for(const r of refs){if(!safe(r.url))continue;const li=node('li'),link=node('a','',r.title);link.href=server?'/'+r.url:r.url;li.append(link);ul.append(li);}box.append(summary,ul);a.append(box);}
function actions(a,text){const b=node('button','chat-copy',p('Copy answer','Yanıtı kopyala'));b.type='button';b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(text);announce(p('Copied.','Kopyalandı.'));}catch{announce(p('Select the text to copy it.','Metni seçerek kopyalayabilirsiniz.'));}});a.append(b);}
function remember(question,answer){history.push({role:'user',content:question},{role:'assistant',content:answer.slice(0,5000)});history=history.slice(-12);lastReply=answer;}
function local(question){
 const n=question.toLocaleLowerCase('tr').trim();
 if(/^(merhaba|selam|hello|hi)[.!?\s]*$/.test(n))return {text:p('Hello. You can ask about the research, project teams or collaboration routes.','Merhaba. Araştırmalar, proje ekipleri veya iş birliği yolları hakkında sorabilirsiniz.'),sources:[]};
 if(/^(sen kimsin|siz kimsiniz|who are you|are you hüseyin)[?\s]*$/.test(n))return {text:p('I am the website’s assistant interface, not Hüseyin Ateş. In guide mode I use the published site records; I do not send messages to him.','Sitenin yardımcı arayüzüyüm; Hüseyin Ateş değilim. Rehber modunda yayımlanmış site kayıtlarını kullanırım; kendisine mesaj göndermem.'),sources:[]};
 const answer=engine.answer(question);if(answer)return answer;
 const found=engine.retrieve(question);
 if(found.length)return {text:p('I found these related records, but cannot reliably turn them into a conversational answer in guide mode.','İlgili kayıtları buldum; ancak rehber modunda bunlardan güvenilir bir yorum yanıtı üretemiyorum.'),sources:found.slice(0,3),excerpts:found.slice(0,2).map(r=>engine.excerpt(r,question,360))};
 return {text:p('This question needs reasoning beyond the available website records. Generative conversation requires an active server connection; no such model is active in guide mode. For a personal enquiry, use the contact page.','Bu soru, mevcut site kayıtlarının ötesinde değerlendirme gerektiriyor. Üretken sohbet için etkin sunucu bağlantısı gerekir; rehber modunda böyle bir model çalışmıyor. Kişisel talebiniz için iletişim sayfasını kullanabilirsiniz.'),sources:[{title:p('Direct contact','Doğrudan iletişim'),url:'contact.html'}]};
}
async function request(question,existing=null){
 if(busy)return;
 const useRemote=remote&&consent.checked&&endpoint;
 const user=existing?.user||message('user',question);let reply=existing?.reply;
 if(!useRemote){const out=local(question);reply=message('assistant',out.text,p('From public website records','Açık site kayıtlarından'));if(out.excerpts){for(const text of out.excerpts)reply.body.append(node('p','chat-excerpt',text));}sources(reply.article,out.sources);actions(reply.article,reply.body.textContent);remember(question,out.text);announce(p('Website guide response.','Site rehberi yanıtı.'));scroll();return;}
 if(reply){reply.article.replaceChildren(node('div','chat-message-label',p('AI response','Yapay zekâ yanıtı')));reply.body=node('div','chat-message-text',p('Preparing an answer…','Yanıt hazırlanıyor…'));reply.article.append(reply.body);}else reply=message('assistant',p('Preparing an answer…','Yanıt hazırlanıyor…'),p('AI response','Yapay zekâ yanıtı'));
 busy=true;abort=new AbortController();const token=++epoch;const timer=setTimeout(()=>abort?.abort(),50000);controls();announce(p('Preparing a source-grounded response…','Kaynaklar ve önceki mesajlar birlikte değerlendiriliyor…'));
 try{
  const recent=[...history];while(recent.length>=2&&recent.reduce((n,m)=>n+m.content.length,question.length)>18000)recent.splice(0,2);
  const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer',body:JSON.stringify({lang:tr?'tr':'en',consent:true,messages:[...recent,{role:'user',content:question}]}),signal:abort.signal});
  const data=await response.json();if(token!==epoch)return;
  if(!response.ok){const err=new Error(response.status===429?'limit':response.status===503?'setup':'service');throw err;}
  if(typeof data.answer!=='string'||!data.answer.trim()||data.answer.length>6500||!Array.isArray(data.sources))throw Error('shape');
  reply.body.textContent=data.answer;
  if(data.follow_up&&typeof data.follow_up==='string')reply.body.append(node('p','chat-follow-up',data.follow_up));
  sources(reply.article,data.sources,true);actions(reply.article,reply.body.textContent);
  const kind=data.kind==='guidance'?p('General methodological guidance; not personal approval.','Genel yöntem önerisidir; kişisel onay değildir.'):p('AI-generated. Check important details in the sources.','Yapay zekâ üretimidir. Önemli bilgileri kaynaklardan kontrol edin.');
  reply.article.append(node('small','chat-answer-note',kind));remember(question,reply.body.textContent);announce(p('Answer ready.','Yanıt hazır.'));
 }catch(e){if(token!==epoch)return;const text=e.message==='limit'?p('The service limit has been reached. Try later or switch to the website guide.','Hizmet kullanım sınırına ulaşıldı. Daha sonra deneyin veya site rehberine geçin.'):e.message==='setup'?p('The model connection is not active. No generated answer was produced.','Model bağlantısı etkin değil. Üretken yanıt hazırlanmadı.'):p('A reliable response could not be completed. Your question has not been sent to Hüseyin Ateş.','Yanıt tamamlanamadı. Sorunuz Hüseyin Ateş’e gönderilmedi.');reply.body.textContent=text;
  const retry=node('button','chat-retry',p('Retry','Yeniden dene'));retry.type='button';retry.addEventListener('click',()=>request(question,{user,reply}));reply.article.append(retry);announce(text);
 }finally{clearTimeout(timer);if(token===epoch){busy=false;abort=null;controls();scroll();}}
}
form.addEventListener('submit',e=>{e.preventDefault();const question=q.value.trim();if(!question||busy)return;if(question.length>2000){announce(p('Use no more than 2,000 characters.','En fazla 2.000 karakter kullanın.'));return;}q.value='';request(question);});
q.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();form.requestSubmit();}});
function cancel(){if(busy){const text=log.querySelector('.chat-assistant:last-child .chat-message-text');if(text)text.textContent=p('Stopped.','Durduruldu.');}++epoch;abort?.abort();abort=null;busy=false;controls();}
stop.addEventListener('click',()=>{cancel();const last=log.querySelector('.chat-assistant:last-child .chat-message-text');if(last)last.textContent=p('Stopped.','Durduruldu.');announce(p('Stopped.','Durduruldu.'));});
clear.addEventListener('click',()=>{cancel();history=[];lastReply=null;engine.reset();q.value='';log.replaceChildren();welcome();announce(p('Conversation cleared from this tab.','Konuşma bu sekmeden temizlendi.'));q.focus();});
enable.addEventListener('click',async()=>{if(remote){remote=false;consent.checked=false;enable.textContent=p('Enable AI conversation','Yapay zekâ sohbetini aç');controls();return;}
 if(!endpoint)return;if(!consent.checked){announce(p('Confirm remote processing first.','Önce sunucu üzerinden işleme onayını işaretleyin.'));consent.focus();return;}
 enable.disabled=true;try{const r=await fetch(endpoint,{credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(8000)});const data=await r.json();if(!r.ok||!data.ready)throw Error();if(!consent.checked)return;remote=true;enable.textContent=p('Use website guide instead','Site rehberine dön');cloudState.textContent=p('Server conversation is active.','Sunucu üzerinden sohbet etkin.');}catch{cloudState.textContent=p('The server connection is not ready. Website guide is still available.','Sunucu bağlantısı hazır değil. Site rehberi kullanılabilir.');}controls();});
consent.addEventListener('change',()=>{if(!consent.checked){cancel();remote=false;enable.textContent=p('Enable AI conversation','Yapay zekâ sohbetini aç');controls();}});
root.querySelectorAll('[data-chat-question]').forEach(b=>b.addEventListener('click',()=>{q.value=b.dataset.chatQuestion;q.focus();}));
window.addEventListener('pagehide',cancel);
function welcome(){message('assistant',p('Hello. What would you like to learn about the research, projects or working together?','Merhaba. Araştırmalar, projeler veya birlikte çalışma hakkında ne öğrenmek istersiniz?'));}
welcome();controls();announce(p('Website guide is ready.','Site rehberi hazır.'));
})();
