/* BIS SmartGuide — navigation fixes
   Makes Command Center cards work and repairs the V6 Advanced Intelligence tab. */
(() => {
  'use strict';
  const TARGETS = {
    'product intelligence': 'Product Intelligence',
    'evidence-backed compliance': 'Compliance Center',
    'agentic bis assistant': 'AI Assistant'
  };

  function wireCommandCenter() {
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
      card.setAttribute('role', 'button'); card.setAttribute('tabindex', '0');
      card.setAttribute('aria-label', `Open ${target}`); card.style.cursor = 'pointer';
      card.addEventListener('click', event => { if (!event.target.closest('a,button,input,select,textarea')) nav.click(); });
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); nav.click(); } });
      card.dataset.sgCommandTarget = target;
    });
    head.dataset.sgCommandFix = '1';
  }

  function wireAdvanced() {
    const btn = document.getElementById('v6Nav');
    if (!btn || btn.dataset.sgAdvancedFix === '1') return;
    btn.dataset.sgAdvancedFix = '1';
    btn.onclick = () => {
      if (typeof window.page === 'function') window.page('v6', btn, 'Advanced Intelligence');
      document.querySelectorAll('.nav button').forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      const section = document.getElementById('v6');
      if (section) { document.querySelectorAll('.page').forEach(x => x.classList.remove('active')); section.classList.add('active'); }
      setTimeout(async () => {
        try {
          const r = await fetch('https://sih26107-bis-smartguide-api.onrender.com/v5/feature-status');
          const d = await r.json(); const list = d.features || [];
          const active = document.getElementById('v6Active'); const status = document.getElementById('v6Status');
          if (active) active.textContent = list.filter(x => String(x.status || '').startsWith('ACTIVE')).length;
          if (status) status.innerHTML = list.map(x => `<div class="sg-v6-card"><span class="sg-v6-badge">${String(x.status || '').replace(/[&<>\"']/g,'')}</span><h3>${String(x.feature || '').replace(/[&<>\"']/g,'')}</h3></div>`).join('');
        } catch (_) {}
      }, 100);
    };
  }

  function wire() { wireCommandCenter(); wireAdvanced(); }
  function init() { wire(); setTimeout(wire, 300); setTimeout(wire, 1000); setTimeout(wire, 1600); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

/* Production V6 loader: guarantees the original V6 workflow console is present
   even when the GitHub Pages integration workflow has not yet rewritten index.html. */
(() => {
  const VERSION = '20260909-v6-5';
  const load = (tag, attrs) => new Promise(resolve => {
    const existing = document.querySelector(`${tag}[data-sg-v6-loader="${attrs.src || attrs.href}"]`);
    if (existing) return resolve();
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v));
    el.onload = resolve; el.onerror = resolve;
    document.head.appendChild(el);
  });
  const boot = async () => {
    await load('link', {rel:'stylesheet', href:`smartguide-v6.css?v=${VERSION}`, 'data-sg-v6-loader':'smartguide-v6.css'});
    await load('script', {src:`smartguide-v6.js?v=${VERSION}`, 'data-sg-v6-loader':'smartguide-v6.js'});
    await load('script', {src:`smartguide-v6-click-fix.js?v=${VERSION}`, 'data-sg-v6-loader':'smartguide-v6-click-fix.js'});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

/* Deployment trigger: V6 test build 2026-09-09 */
