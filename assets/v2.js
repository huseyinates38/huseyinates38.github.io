'use strict';
document.documentElement.classList.add('js');
// No network requests, analytics, cookies or persistent browser storage.
const menu = document.querySelector('.menu-button');
const navigation = document.querySelector('#main-navigation');
if (menu && navigation) {
  menu.addEventListener('click', () => {
    const expanded = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(expanded));
    navigation.classList.toggle('open', expanded);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && navigation.classList.contains('open')) {
      navigation.classList.remove('open');
      menu.setAttribute('aria-expanded', 'false');
      menu.focus();
    }
  });
}
for (const button of document.querySelectorAll('[data-print]')) {
  button.addEventListener('click', () => window.print());
}
const language = document.querySelector('[data-language-picker]');
const mode = document.querySelector('[data-feedback-picker]');
function updateExamples() {
  if (language) {
    for (const block of document.querySelectorAll('[data-lang]')) {
      block.hidden = language.value !== 'all' && block.dataset.lang !== language.value;
    }
  }
  if (mode) {
    for (const block of document.querySelectorAll('[data-mode]')) {
      block.hidden = mode.value !== 'all' && block.dataset.mode !== mode.value;
    }
  }
}
if (language) language.addEventListener('change', updateExamples);
if (mode) mode.addEventListener('change', updateExamples);
updateExamples();
const search = document.querySelector('#pub-query');
const year = document.querySelector('#pub-year');
const count = document.querySelector('#pub-count');
if (search && year && count) {
  count.setAttribute('aria-live', 'polite');
  const empty = document.createElement('p');
  empty.className = 'no-results';
  empty.textContent = 'No matching publications. Try another search or select All years.';
  empty.hidden = true;
  count.closest('.toolbar').insertAdjacentElement('afterend', empty);
  const update = () => {
    let total = 0;
    const query = search.value.trim().toLocaleLowerCase();
    for (const publication of document.querySelectorAll('.publication')) {
      const visible = (year.value === 'all' || publication.dataset.year === year.value) && publication.textContent.toLocaleLowerCase().includes(query);
      publication.hidden = !visible;
      if (visible) total += 1;
    }
    count.textContent = total + ' selected publication' + (total === 1 ? '' : 's');
    empty.hidden = total !== 0;
  };
  search.addEventListener('input', update);
  year.addEventListener('change', update);
  update();
}
