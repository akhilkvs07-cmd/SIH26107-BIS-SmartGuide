/* BIS SmartGuide Advanced Intelligence V8 — resilient card click bridge. */
(() => {
  'use strict';
  const actions = {
    'product ai': 'openProduct',
    'isi / cm-l': 'openMark',
    'test reports': 'openTest',
    'lab matcher': 'openLab',
    'qco + amendment': 'openAmendment',
    '3d cad / stl': 'openSTL',
    'label / packaging': 'openLabel',
    'procurement ai': 'openProcurement',
    'issue report': 'openIssue'
  };

  function wire() {
    document.querySelectorAll('.sg-v8-card').forEach(card => {
      if (card.classList.contains('sg-v8-status-card') || card.dataset.v8ClickFixed) return;
      const heading = card.querySelector('h3');
      const key = (heading?.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
      const fn = actions[key];
      if (!fn || typeof window[fn] !== 'function') return;

      card.dataset.v8ClickFixed = '1';
      card.classList.add('sg-v8-clickable');
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      const open = card.querySelector('.sg-v8-open');
      if (open) open.textContent = 'Get started →';

      const run = () => window[fn]();
      card.addEventListener('click', e => {
        if (e.target.closest('button,a,input,textarea,select')) return;
        run();
      });
      card.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          run();
        }
      });
    });
  }

  function boot() {
    wire();
    [300, 1000, 2000].forEach(ms => setTimeout(wire, ms));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  // No MutationObserver: this bridge must never continuously rescan a changing DOM.
})();
