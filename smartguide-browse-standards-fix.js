/* BIS SmartGuide navigation fix: preserve Browse Standards and restore Compare Standards. */
(() => {
  'use strict';

  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();

  function setLabel(el, label) {
    const span = el.querySelector('span:last-child');
    if (span) span.textContent = label;
    else {
      const text = String(el.textContent || '').trim();
      el.textContent = text.replace(/browse standards?|compare standards?/i, label);
    }
    el.setAttribute('aria-label', label);
  }

  function apply() {
    const navItems = Array.from(document.querySelectorAll('.nav button, .nav a'));
    let browseCount = 0;

    navItems.forEach(el => {
      const text = normalize(el.querySelector('span:last-child')?.textContent || el.textContent);
      if (text === 'browse standards' || text === 'browse standard' || text === 'compare standards' || text === 'compare standard') {
        browseCount += 1;
        // The first item is the real standards browser; the second is Compare Standards.
        setLabel(el, browseCount === 1 ? 'Browse Standards' : 'Compare Standards');
      }
    });

    document.querySelectorAll('h1,h2,h3,h4,.crumb,[data-page-title]').forEach(el => {
      const text = normalize(el.textContent);
      if (text === 'browse standards' || text === 'compare standards' || text === 'compare standard') {
        // Keep page titles consistent with the active navigation item when possible.
        if (text === 'compare standards' || text === 'compare standard') el.textContent = 'Compare Standards';
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
  [300, 1000, 2500, 5000].forEach(ms => setTimeout(apply, ms));
})();
