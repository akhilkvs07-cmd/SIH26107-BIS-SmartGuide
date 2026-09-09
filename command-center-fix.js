/* BIS SmartGuide — Command Center navigation fix
   Makes the three dashboard Command Center cards behave like the sidebar navigation. */
(() => {
  'use strict';

  const TARGETS = {
    'product intelligence': 'Product Intelligence',
    'evidence-backed compliance': 'Compliance Center',
    'agentic bis assistant': 'AI Assistant'
  };

  function wire() {
    const heads = [...document.querySelectorAll('.section-head')];
    const head = heads.find(x => /command\s*center/i.test(x.textContent || ''));
    if (!head || head.dataset.sgCommandFix === '1') return;

    const grid = head.nextElementSibling;
    if (!grid || !grid.classList.contains('grid3')) return;

    const navButtons = [...document.querySelectorAll('.nav button')];
    const findNav = label => navButtons.find(b => (b.textContent || '').trim().toLowerCase().includes(label.toLowerCase()));

    [...grid.querySelectorAll('.module')].forEach(card => {
      const title = (card.querySelector('h3')?.textContent || '').trim().toLowerCase();
      const target = TARGETS[title];
      if (!target) return;
      const nav = findNav(target);
      if (!nav) return;

      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.setAttribute('aria-label', `Open ${target}`);
      card.style.cursor = 'pointer';
      card.addEventListener('click', event => {
        if (event.target.closest('a,button,input,select,textarea')) return;
        nav.click();
      });
      card.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          nav.click();
        }
      });
      card.dataset.sgCommandTarget = target;
    });

    head.dataset.sgCommandFix = '1';
  }

  function init() {
    wire();
    setTimeout(wire, 300);
    setTimeout(wire, 1000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
