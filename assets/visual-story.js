'use strict';
// Accessibility-first progressive enhancement; no analytics, cookies, or network requests.
for (const card of document.querySelectorAll('.visual-update,.visual-topic,.visual-research-gallery-grid a')) {
  card.addEventListener('focusin', () => card.classList.add('is-keyboard-focused'));
  card.addEventListener('focusout', () => card.classList.remove('is-keyboard-focused'));
}
