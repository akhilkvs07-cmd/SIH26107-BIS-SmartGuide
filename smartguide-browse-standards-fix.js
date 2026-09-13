/* BIS SmartGuide navigation fix: rename Compare Standards to Browse Standards. */
(() => {
  'use strict';
  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();
  function apply() {
    document.querySelectorAll('.nav button, .nav a').forEach(el => {
      const span = el.querySelector('span:last-child');
      const text = normalize(span ? span.textContent : el.textContent);
      if (text === 'compare' || text === 'compare standards' || text === 'compare standard') {
        if (span) span.textContent = 'Browse Standards';
        else el.textContent = el.textContent.replace(/compare standards?/i, 'Browse Standards');
        el.setAttribute('aria-label', 'Browse Standards');
      }
    });
    document.querySelectorAll('h1,h2,h3,h4,.crumb,[data-page-title]').forEach(el => {
      if (/^compare standards?$/i.test(String(el.textContent || '').trim())) {
        el.textContent = 'Browse Standards';
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply); else apply();
  [300, 1000, 2500, 5000].forEach(ms => setTimeout(apply, ms));
})();
