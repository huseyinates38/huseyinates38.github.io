/* Website 3.1: local search and shareable, stateless interface preferences. */
(() => {
  'use strict';
  const normalize = value => String(value).normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').replace(/ı/g, 'i').toLowerCase();
  const aliases = {
    ai: ['ai', 'artificial intelligence', 'yapay zeka'],
    genai: ['genai', 'generative ai', 'generative artificial intelligence', 'uretken yapay zeka'],
    vr: ['vr', 'virtual reality', 'sanal gerceklik'],
    ar: ['ar', 'augmented reality', 'artirilmis gerceklik'],
    srl: ['srl', 'self-regulated', 'self regulated', 'oz duzenlem'],
    feedback: ['feedback', 'geri bildirim'],
    teacher: ['teacher', 'ogretmen'],
    robot: ['robot', 'robotics'],
    cv: ['cv', 'curriculum vitae', 'academic profile', 'ozgecmis']
  };
  function contains(text, term) {
    if (/^[a-z]{1,2}$/.test(term)) {
      return new RegExp('(^|[^a-z0-9])' + term + '([^a-z0-9]|$)').test(text);
    }
    return text.includes(term);
  }
  function matches(text, query) {
    const value = normalize(query).trim();
    if (!value) return true;
    if (value.length > 2 && text.includes(value)) return true;
    return value.split(/\s+/).every(word => (aliases[word] || [word]).some(term => contains(text, term)));
  }
  function readState() {
    return new URLSearchParams(location.hash.slice(1).includes('=') ? location.hash.slice(1) : '');
  }
  function saveState(values) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(values)) if (value && value !== 'all') params.set(key, value);
    const suffix = params.size ? '#' + params.toString() : '';
    try { history.replaceState(null, '', location.pathname + location.search + suffix); } catch (_) { /* offline preview */ }
  }
  const siteInput = document.getElementById('site-query');
  if (siteInput) {
    const category = document.getElementById('site-category');
    const status = document.getElementById('site-search-status');
    const list = document.getElementById('site-search-results');
    const more = document.getElementById('site-search-more');
    const reset = document.getElementById('site-search-reset');
    const directory = document.getElementById('search-directory');
    const index = JSON.parse(document.getElementById('site-search-data').textContent);
    let limit = 12;
    const categories = new Set(['all', 'research', 'people', 'publications', 'resources', 'about']);
    function applyState() {
      const state = readState();
      siteInput.value = (state.get('q') || '').slice(0, 120);
      category.value = categories.has(state.get('category')) ? state.get('category') : 'all';
    }
    function render(persist = true) {
      const query = siteInput.value.trim();
      const result = index.filter(item => (category.value === 'all' || item.category === category.value) && matches(item.key, query));
      if (query) result.sort((a, b) => Number(matches(normalize(b.title), query)) - Number(matches(normalize(a.title), query)));
      const fragment = document.createDocumentFragment();
      for (const item of result.slice(0, limit)) {
        const row = document.createElement('li');
        const kind = document.createElement('p'); kind.className = 'search-kind'; kind.textContent = item.label;
        const heading = document.createElement('h2');
        const link = document.createElement('a'); link.href = item.url; link.textContent = item.title; heading.append(link);
        const summary = document.createElement('p'); summary.textContent = item.summary;
        row.append(kind, heading, summary); fragment.append(row);
      }
      list.replaceChildren(fragment);
      status.textContent = result.length ? `${result.length} results · showing ${Math.min(limit, result.length)}` : 'No matches. Try a shorter phrase, another spelling or All content.';
      more.hidden = result.length <= limit;
      directory.hidden = true;
      if (persist) saveState({q: query, category: category.value});
    }
    siteInput.addEventListener('input', () => { limit = 12; render(); });
    category.addEventListener('change', () => { limit = 12; render(); });
    reset.addEventListener('click', () => { siteInput.value = ''; category.value = 'all'; limit = 12; render(); siteInput.focus(); });
    more.addEventListener('click', () => {
      const previous = list.children.length; limit += 12; render();
      list.children[previous]?.querySelector('a')?.focus();
    });
    window.addEventListener('hashchange', () => { applyState(); limit = 12; render(false); });
    applyState(); render(false);
  }
  // The preceding v2 script retains its fallback; this handler supplies the final, accent-aware result.
  const query = document.getElementById('pub-query');
  const year = document.getElementById('pub-year');
  if (query && year) {
    const rows = Array.from(document.querySelectorAll('.publication'));
    const count = document.getElementById('pub-count');
    const reset = document.getElementById('pub-reset');
    const empty = document.querySelector('.no-results');
    function applyState() {
      const state = readState(); query.value = (state.get('q') || '').slice(0,120);
      const candidate = state.get('year') || 'all';
      year.value = Array.from(year.options).some(o => o.value === candidate) ? candidate : 'all';
    }
    function filter(persist = true) {
      let total = 0;
      for (const row of rows) {
        row.hidden = !((year.value === 'all' || row.dataset.year === year.value) && matches(normalize(row.textContent), query.value));
        total += row.hidden ? 0 : 1;
      }
      count.textContent = `${total} selected publication${total === 1 ? '' : 's'}`;
      if (empty) empty.hidden = total !== 0;
      if (persist) saveState({q: query.value.trim(), year: year.value});
    }
    query.addEventListener('input', () => filter());
    year.addEventListener('change', () => filter());
    reset?.addEventListener('click', () => { query.value = ''; year.value = 'all'; filter(); query.focus(); });
    window.addEventListener('hashchange', () => { applyState(); filter(false); });
    applyState(); filter(false);
  }
  const language = document.querySelector('[data-language-picker]');
  const mode = document.querySelector('[data-feedback-picker]');
  if (language) {
    function restore() {
      const state = readState();
      for (const [key, control] of [['lang', language], ['mode', mode]]) {
        if (control && Array.from(control.options).some(o => o.value === state.get(key))) {
          control.value = state.get(key); control.dispatchEvent(new Event('change'));
        }
      }
    }
    restore();
    const status = document.getElementById('language-status');
    function changed(persist = true) {
      if (status) status.textContent = language.value === 'tr' ? 'Türkçe içerik gösteriliyor.' : language.value === 'en' ? 'English content is shown.' : 'English and Turkish content are shown.';
      if (persist) saveState({lang: language.value, mode: mode?.value || ''});
    }
    language.addEventListener('change', () => changed());
    mode?.addEventListener('change', () => changed());
    changed(false);
  }
})();
