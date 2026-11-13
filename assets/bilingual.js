/* Academic website EN/TR: accessible local controls; no analytics, storage or server calls. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const lang = document.documentElement.lang === 'tr' ? 'tr' : 'en';
  const ui = {
    en: {
      selected: n => `${n} selected publication${n === 1 ? '' : 's'}`,
      noPubs: 'No matching publications. Try a different search or year.',
      projects: n => `${n} supported project${n === 1 ? '' : 's'} shown`,
      matches: (n,k) => `${n} results · showing ${k}`,
      noMatches: 'No matches. Try another spelling, a shorter phrase or All content.'
    },
    tr: {
      selected: n => `${n} seçilmiş yayın`,
      noPubs: 'Eşleşen yayın yok. Farklı bir arama veya yıl deneyin.',
      projects: n => `${n} desteklenen proje gösteriliyor`,
      matches: (n,k) => `${n} sonuç · ${k} tanesi gösteriliyor`,
      noMatches: 'Sonuç bulunamadı. Farklı bir yazım, daha kısa ifade veya Tüm içerik seçeneğini deneyin.'
    }
  }[lang];
  const norm = input => String(input ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g,'').replace(/ı/g, 'i').toLowerCase();
  const aliases = {
    ai: ['ai','artificial intelligence','yapay zeka'],
    yapay: ['artificial intelligence','yapay zeka','genai'],
    genai: ['genai','generative ai','uretken yapay zeka'],
    vr: ['vr','virtual reality','sanal gerceklik'],
    ar: ['ar','augmented reality','artirilmis gerceklik'],
    srl: ['srl','self-regulated','oz duzenleme'],
    feedback: ['feedback','geri bildirim'],
    argumentation: ['argumentation','argumantasyon','bilimsel gerekce'],
    teacher: ['teacher','ogretmen'],
    student: ['student','ogrenci'],
    cv: ['cv','ozgecmis','curriculum vitae'],
    dfg: ['dfg','tubitak dfg','moritz']
  };
  const contains = (hay, term) => {
    // User input is always literal. Only validated alphabetic abbreviations enter this expression.
    if (/^[a-z]{1,2}$/.test(term)) return new RegExp('(^|[^a-z0-9])'+term+'([^a-z0-9]|$)').test(hay);
    return hay.includes(term);
  };
  const matches = (hay, query) => {
    const n=norm(query).trim(); if(!n) return true;
    if(hay.includes(n)) return true;
    return n.split(/\s+/).every(word => (Object.hasOwn(aliases, word) ? aliases[word] : [word]).some(v=>contains(hay,norm(v))));
  };
  const getState = () => new URLSearchParams(location.hash.includes('=') ? location.hash.substring(1) : '');
  const saveState = state => {
    const p=new URLSearchParams();
    for(const [key,val] of Object.entries(state)) if(val && val!=='all')p.set(key,val);
    try {history.replaceState(null,'',location.pathname+location.search+(p.size?'#'+p.toString():''));}catch(e) { /* file preview */ }
  };
  // The locale link always points to the corresponding page. Keep sharable search/filter state.
  document.querySelectorAll('[data-site-lang]').forEach(a=>a.addEventListener('click',()=>{
    if(location.hash.includes('=')) a.href=a.getAttribute('href').split('#')[0]+location.hash;
  }));
  const menu=document.querySelector('.menu-button'),nav=document.getElementById('main-navigation');
  if(menu && nav){
    const close=()=>{menu.setAttribute('aria-expanded','false');nav.classList.remove('open')};
    menu.addEventListener('click',()=>{const isOpen=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(isOpen));nav.classList.toggle('open',isOpen)});
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open')){close();menu.focus()}});
    nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
  }
  for(const btn of document.querySelectorAll('[data-print]'))btn.addEventListener('click',()=>window.print());
  // The selected-language page contains only its own translated examples.
  const feedback=document.querySelector('[data-feedback-picker]');
  if(feedback){
    const apply=()=>{for(const block of document.querySelectorAll('[data-mode]'))block.hidden=feedback.value!=='all'&&block.dataset.mode!==feedback.value;saveState({mode:feedback.value})};
    const state=getState(),requested=state.get('mode');
    if(requested && Array.from(feedback.options).some(o=>o.value===requested))feedback.value=requested;
    feedback.addEventListener('change',apply);apply();
  }
  const pubQuery=document.getElementById('pub-query'),pubYear=document.getElementById('pub-year');
  if(pubQuery && pubYear){
    const list=[...document.querySelectorAll('.publication')],count=document.getElementById('pub-count'),reset=document.getElementById('pub-reset');
    const empty=document.createElement('p');empty.className='no-results';empty.textContent=ui.noPubs;empty.hidden=true;
    const bar=count?.closest('.toolbar') || pubQuery.parentElement;
    bar?.insertAdjacentElement('afterend',empty);
    if(count)count.setAttribute('aria-live','polite');
    const params=getState(),q=params.get('q'),y=params.get('year');
    if(q)pubQuery.value=q.substring(0,120);
    if(y && [...pubYear.options].some(o=>o.value===y))pubYear.value=y;
    const apply=(store=true)=>{
      let n=0;
      for(const row of list){const good=(pubYear.value==='all'||row.dataset.year===pubYear.value)&&matches(norm(row.textContent),pubQuery.value);row.hidden=!good;if(good)n++;}
      if(count)count.textContent=ui.selected(n);empty.hidden=n>0;
      if(store)saveState({q:pubQuery.value.trim(),year:pubYear.value});
    };
    pubQuery.addEventListener('input',()=>apply());pubYear.addEventListener('change',()=>apply());
    reset?.addEventListener('click',()=>{pubQuery.value='';pubYear.value='all';apply();pubQuery.focus()});
    apply(false);
  }
  const programme=document.getElementById('project-programme');
  if(programme){
    const cards=[...document.querySelectorAll('.project-summary')],status=document.getElementById('project-filter-status');
    const apply=()=>{
      let n=0;
      for(const card of cards){const good=programme.value==='all'||norm(card.textContent).includes(norm(programme.value));card.hidden=!good;if(good)n++;}
      if(status){status.textContent=ui.projects(n);status.setAttribute('aria-live','polite');}
    };
    programme.addEventListener('change',apply);apply();
  }
  const siteQuery=document.getElementById('site-query');
  if(siteQuery){
    const category=document.getElementById('site-category'),status=document.getElementById('site-search-status');
    const results=document.getElementById('site-search-results'),more=document.getElementById('site-search-more');
    const reset=document.getElementById('site-search-reset'),directory=document.getElementById('search-directory');
    const data=document.getElementById('site-search-data');
    let items=[];try{items=JSON.parse(data.textContent)}catch(e){if(status)status.textContent=ui.noMatches;return;}
    let limit=12;
    const params=getState();siteQuery.value=(params.get('q')||'').substring(0,120);
    const cat=params.get('category');if(cat&&category&&[...category.options].some(o=>o.value===cat))category.value=cat;
    const render=(store=true)=>{
      const q=siteQuery.value.trim(),current=category?.value||'all';
      const list=items.filter(x=>(current==='all'||x.category===current)&&matches(norm(x.key),q));
      if(q)list.sort((a,b)=>Number(matches(norm(b.title),q))-Number(matches(norm(a.title),q)));
      const fragment=document.createDocumentFragment();
      for(const item of list.slice(0,limit)){
        const li=document.createElement('li'),kind=document.createElement('p'),heading=document.createElement('h2'),a=document.createElement('a'),p=document.createElement('p');
        kind.className='search-kind';kind.textContent=item.label; a.href=item.url;a.textContent=item.title;heading.append(a);p.textContent=item.summary;
        li.append(kind,heading,p);fragment.append(li);
      }
      results?.replaceChildren(fragment);
      if(status)status.textContent=list.length?ui.matches(list.length,Math.min(limit,list.length)):ui.noMatches;
      if(more)more.hidden=list.length<=limit;
      if(directory)directory.hidden=true;
      if(store)saveState({q,category:current});
    };
    siteQuery.addEventListener('input',()=>{limit=12;render()});
    category?.addEventListener('change',()=>{limit=12;render()});
    reset?.addEventListener('click',()=>{siteQuery.value='';if(category)category.value='all';limit=12;render();siteQuery.focus()});
    more?.addEventListener('click',()=>{const prev=results?.children.length||0;limit+=12;render();results?.children[prev]?.querySelector('a')?.focus()});
    render(false);
  }
})();
