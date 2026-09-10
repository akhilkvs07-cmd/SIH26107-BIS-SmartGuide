/* BIS SmartGuide UX v9.1 — task-first language, guided workflows, lab navigation and accessibility. */
(() => {
  'use strict';

  const labels = {
    'product ai': ['Find applicable standards →', 'Describe your product and SmartGuide will rank relevant Indian Standards.'],
    'isi / cm-l': ['Verify ISI / CM/L →', 'Check a mark or licence number and see what can be verified.'],
    'test reports': ['Check my test report →', 'Upload a report and understand the standards, results and gaps.'],
    'lab matcher': ['Find a BIS laboratory →', 'Match your standard or product to suitable testing facilities.'],
    'qco + amendment': ['Check mandatory requirements →', 'See whether QCOs or amendments may affect your product.'],
    '3d cad / stl': ['Check my 3D file →', 'Review available product-design information before compliance testing.'],
    'label / packaging': ['Check my label →', 'Review important BIS marking and packaging information.'],
    'procurement ai': ['Check a product before buying →', 'Screen standards, certification evidence and test information before approval.'],
    'issue report': ['Create a complaint draft →', 'Prepare a structured report for submission through official BIS channels.']
  };

  const navLabels = {
    'overview': 'Home',
    'product intelligence': 'Find Standards',
    'standards': 'Browse Standards',
    'compliance': 'Check Compliance',
    'mandatory / qco': 'Mandatory / QCO',
    'certification': 'BIS Certification',
    'laboratories': 'Find a Laboratory',
    'document ai': 'Analyze a Document',
    'compare': 'Compare Standards',
    'knowledge graph': 'Explore Connections',
    'hallmarking': 'Hallmarking',
    'ai agent': 'Ask SmartGuide',
    'reports': 'My Reports',
    'analytics': 'Analytics'
  };

  function norm(s) { return String(s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }

  function applyLabels() {
    document.querySelectorAll('.sg-v8-card').forEach(card => {
      const h = card.querySelector('h3');
      const key = norm(h && h.textContent);
      const cfg = labels[key];
      if (!cfg) return;
      const open = card.querySelector('.sg-v8-open');
      if (open) open.textContent = cfg[0];
      const p = card.querySelector('p');
      if (p) p.textContent = cfg[1];
      card.classList.add('sg-friendly-card');
      card.setAttribute('aria-label', cfg[0].replace(/\s*→$/, ''));
    });

    document.querySelectorAll('button, a').forEach(el => {
      const t = norm(el.textContent);
      if (t === 'open workflow →' || t === 'open workflow') el.textContent = 'Get started →';
    });

    document.querySelectorAll('.nav button, .nav a').forEach(el => {
      const text = norm(el.textContent);
      Object.keys(navLabels).forEach(k => {
        if (text === k || text.endsWith(k)) {
          const span = el.querySelector('span:last-child');
          if (span) span.textContent = navLabels[k];
        }
      });
    });

    const productInput = document.querySelector('#productInput, #product, input[name="product"], #piProduct');
    if (productInput) {
      productInput.setAttribute('placeholder', 'Try: mobile phone, gas stove, laptop, PVC cable…');
      productInput.setAttribute('aria-label', 'Product name or description');
    }
  }

  function injectStyles() {
    if (document.getElementById('sg-v91-style')) return;
    const s = document.createElement('style');
    s.id = 'sg-v91-style';
    s.textContent = `
      .sg-friendly-card { transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
      .sg-friendly-card:hover { transform: translateY(-2px); }
      .sg-friendly-card .sg-v8-open { font-weight: 800; }
      .sg-task-grid { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0; }
      .sg-task { display:flex;flex-direction:column;gap:7px;text-align:left;padding:16px;border:1px solid #dce6f2;border-radius:16px;background:#fff;cursor:pointer;box-shadow:0 3px 14px rgba(24,45,74,.05); }
      .sg-task:hover,.sg-task:focus-visible { transform:translateY(-2px);box-shadow:0 8px 22px rgba(24,45,74,.10);outline:none; }
      .sg-task .icon { font-size:22px; }
      .sg-task strong { font-size:13px; }
      .sg-task small { color:#70819a;font-size:11px;line-height:1.45; }
      .sg-help-strip { margin:16px 0 4px;padding:15px 17px;border:1px solid #d7e6f5;border-radius:16px;background:linear-gradient(135deg,#fff,#f5faff);display:flex;gap:12px;align-items:center; }
      .sg-help-strip strong { display:block;font-size:13px; }
      .sg-help-strip span { color:#6d7e98;font-size:11px;line-height:1.45; }
      .sg-lab-actions { display:flex;gap:8px;flex-wrap:wrap;margin-top:10px; }
      .sg-map-btn { text-decoration:none !important;display:inline-flex;align-items:center;gap:6px; }
      @media (max-width:900px) { .sg-task-grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
      @media (max-width:600px) {
        .sg-task-grid{grid-template-columns:1fr;}
        .topbar .lang-global{max-width:125px;}
        .hero-search,.searchbar,.chatbar{flex-direction:column;}
        .hero-search .btn,.searchbar .btn,.chatbar .btn{width:100%;}
        .reqs{grid-template-columns:1fr;}
        .content{padding:14px;}
        .hero h1{letter-spacing:-1.5px;}
        .sg-help-strip{align-items:flex-start;}
      }
    `;
    document.head.appendChild(s);
  }

  function go(pageName, title) {
    try {
      if (typeof window.page === 'function') { window.page(pageName, null, title); return; }
      const btn = [...document.querySelectorAll('.nav button')].find(b => norm(b.textContent).includes(norm(title)));
      if (btn) btn.click();
    } catch (_) {}
  }

  function addTaskStrip() {
    if (document.querySelector('.sg-task-grid')) return;
    const target = document.querySelector('.content');
    if (!target) return;
    const first = target.querySelector('.page.active, .page');
    if (!first) return;

    const grid = document.createElement('div');
    grid.className = 'sg-task-grid';
    const tasks = [
      ['🔎','Find a standard','I have a product and need the applicable IS.','product-intelligence','Find Standards'],
      ['✓','Verify ISI / CM/L','I want to check a licence or product mark.','advanced','ISI / CM-L'],
      ['🧪','Find a laboratory','I need a suitable testing facility.','labs','Find a Laboratory'],
      ['📄','Analyze a document','I have a PDF, report or image to understand.','documents','Analyze a Document'],
      ['⚖️','Check mandatory rules','I want to know about QCO or mandatory status.','qco','Mandatory / QCO'],
      ['💬','Ask SmartGuide','I have a BIS question and want guided help.','assistant','Ask SmartGuide']
    ];
    tasks.forEach(([icon,title,desc,pageName,pageTitle]) => {
      const b = document.createElement('button');
      b.type='button'; b.className='sg-task';
      b.innerHTML=`<span class="icon" aria-hidden="true">${icon}</span><strong>${title} →</strong><small>${desc}</small>`;
      b.addEventListener('click',()=>go(pageName,pageTitle));
      grid.appendChild(b);
    });
    first.prepend(grid);
  }

  function addHelpStrip() {
    if (document.querySelector('.sg-help-strip')) return;
    const target = document.querySelector('.content');
    if (!target) return;
    const first = target.querySelector('.page.active, .page');
    if (!first) return;
    const strip = document.createElement('div');
    strip.className='sg-help-strip';
    strip.innerHTML='<div aria-hidden="true" style="font-size:20px">💡</div><div><strong>New to BIS compliance?</strong><span>Start with a product, document, label, licence or laboratory task. SmartGuide will guide you step by step and show its evidence.</span></div>';
    first.prepend(strip);
  }

  function addMapLinks() {
    // Enhance laboratory result cards without claiming live location or live lab availability.
    document.querySelectorAll('[data-lab-address], .lab-card, .laboratory-card').forEach(card => {
      if (card.querySelector('.sg-map-btn')) return;
      const address = card.getAttribute('data-lab-address') || card.querySelector('.address')?.textContent;
      if (!address) return;
      const a = document.createElement('a');
      a.className='btn ghost sg-map-btn'; a.target='_blank'; a.rel='noopener';
      a.href='https://www.google.com/maps/dir/?api=1&destination='+encodeURIComponent(address.trim());
      a.textContent='🗺 Get directions';
      const actions = card.querySelector('.sg-lab-actions') || card;
      actions.appendChild(a);
    });
  }

  function boot() {
    injectStyles(); applyLabels(); addHelpStrip(); addTaskStrip(); addMapLinks();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  [250,800,1600,3000].forEach(ms=>setTimeout(boot,ms));
  new MutationObserver(()=>{ applyLabels(); addMapLinks(); }).observe(document.documentElement,{childList:true,subtree:true});
})();
