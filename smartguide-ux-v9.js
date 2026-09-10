/* BIS SmartGuide UX v9 — plain-language actions, friendlier cards, mobile polish. */
(() => {
  'use strict';

  const labels = {
    'product ai': ['Find applicable standards →', 'Tell SmartGuide what your product is and get relevant Indian Standards.'],
    'isi / cm-l': ['Verify ISI / CM/L →', 'Check a mark or licence number before you trust the product.'],
    'test reports': ['Check my test report →', 'Upload or review a report and understand what it means.'],
    'lab matcher': ['Find a BIS laboratory →', 'Find suitable testing facilities and get directions.'],
    'qco + amendment': ['Check mandatory requirements →', 'See QCO and amendment information that may affect your product.'],
    '3d cad / stl': ['Check my 3D file →', 'Review product-design information against the available workflow.'],
    'label / packaging': ['Check my label →', 'Review important BIS, marking and packaging information.'],
    'procurement ai': ['Check a product for purchase →', 'Use SmartGuide before buying or approving a product.'],
    'issue report': ['Create a complaint draft →', 'Prepare a structured issue report for submission through official channels.']
  };

  function norm(s) { return String(s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }

  function apply() {
    document.querySelectorAll('.sg-v8-card').forEach(card => {
      const h = card.querySelector('h3');
      const key = norm(h && h.textContent);
      const cfg = labels[key];
      if (!cfg) return;
      const open = card.querySelector('.sg-v8-open');
      if (open) open.textContent = cfg[0];
      const p = card.querySelector('p');
      if (p && (!p.dataset.sgOriginal || /open workflow/i.test(p.textContent))) {
        p.dataset.sgOriginal = p.dataset.sgOriginal || p.textContent;
        p.textContent = cfg[1];
      }
      card.classList.add('sg-friendly-card');
      card.setAttribute('aria-label', cfg[0].replace(/\s*→$/, ''));
    });

    document.querySelectorAll('button, a').forEach(el => {
      const t = norm(el.textContent);
      if (t === 'open workflow →' || t === 'open workflow') {
        el.textContent = 'Get started →';
      }
    });

    const productInput = document.querySelector('#productInput, #product, input[name="product"]');
    if (productInput) {
      productInput.setAttribute('placeholder', 'Try: mobile phone, gas stove, laptop, PVC cable…');
      productInput.setAttribute('aria-label', 'Product name or description');
    }
  }

  function injectStyles() {
    if (document.getElementById('sg-v9-ux-style')) return;
    const s = document.createElement('style');
    s.id = 'sg-v9-ux-style';
    s.textContent = `
      .sg-friendly-card { transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
      .sg-friendly-card:hover { transform: translateY(-2px); }
      .sg-friendly-card .sg-v8-open { font-weight: 950; }
      @media (max-width: 800px) {
        .topbar .lang-global { max-width: 125px; }
        .hero-search, .searchbar, .chatbar { flex-direction: column; }
        .hero-search .btn, .searchbar .btn, .chatbar .btn { width: 100%; }
        .reqs { grid-template-columns: 1fr; }
        .content { padding: 14px; }
        .hero h1 { letter-spacing: -1.5px; }
      }
      .sg-help-strip { margin: 16px 0 4px; padding: 15px 17px; border: 1px solid #d7e6f5; border-radius: 16px; background: linear-gradient(135deg,#fff,#f5faff); display:flex; gap:12px; align-items:center; }
      .sg-help-strip strong { display:block; font-size:13px; }
      .sg-help-strip span { color:#6d7e98; font-size:11px; line-height:1.45; }
      @media (max-width: 600px) { .sg-help-strip { align-items:flex-start; } }
    `;
    document.head.appendChild(s);
  }

  function addHelpStrip() {
    if (document.querySelector('.sg-help-strip')) return;
    const target = document.querySelector('.content');
    if (!target) return;
    const first = target.querySelector('.page.active, .page');
    if (!first) return;
    const strip = document.createElement('div');
    strip.className = 'sg-help-strip';
    strip.innerHTML = '<div aria-hidden="true" style="font-size:20px">💡</div><div><strong>New to BIS compliance?</strong><span>Start with a product, document, label, licence or laboratory task. SmartGuide will guide you step by step.</span></div>';
    first.prepend(strip);
  }

  function boot() { injectStyles(); apply(); addHelpStrip(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  [250, 800, 1600].forEach(ms => setTimeout(boot, ms));
  new MutationObserver(() => apply()).observe(document.documentElement, { childList:true, subtree:true });
})();
