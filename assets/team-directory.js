/* Local-only, literal, accent-insensitive directory filters. */
(()=>{'use strict';
 const tr=document.documentElement.lang==='tr';
 const clean=s=>String(s??'').toLocaleLowerCase('tr').replaceAll('ı','i').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 function install(inputId,selector,countId,groups){
  const q=document.getElementById(inputId);if(!q)return;
  const all=[...document.querySelectorAll(selector)],count=document.getElementById(countId);
  const empty=document.getElementById(inputId==='people-query'?'people-no-results':'network-no-results');
  const update=()=>{const terms=clean(q.value).trim().split(/\s+/).filter(Boolean);let n=0;
   for(const card of all){const value=clean(card.textContent);card.hidden=!terms.every(t=>value.includes(t));if(!card.hidden)n++;}
   if(groups)for(const group of groups)group.hidden=!!terms.length&&![...group.querySelectorAll(selector)].some(card=>!card.hidden);
   if(count)count.textContent=tr?`${n} / ${all.length} kayıt gösteriliyor`:`Showing ${n} of ${all.length} entries`;
   if(empty)empty.hidden=n!==0;
  };
  q.addEventListener('input',update);
  const reset=document.getElementById('people-reset');if(reset&&inputId==='people-query')reset.addEventListener('click',()=>{q.value='';update();q.focus();});update();
 }
 install('people-query','.person-card[data-person]','people-count',[...document.querySelectorAll('main>section')].filter(s=>s.querySelector('.person-card[data-person]')));
 install('network-query','.network-country','network-count',null);
})();
