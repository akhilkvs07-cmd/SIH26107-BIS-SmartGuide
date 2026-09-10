/* BIS SmartGuide UX v9.4 — task-first language, guided workflows, lab navigation and accessibility. */
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
    'issue report': ['Create a complaint draft →', 'Prepare a structured report for submission through official BIS channels.'],
    'document intelligence': ['Analyze a document →', 'Extract useful product, standard and evidence signals from a document.'],
    'real ocr': ['Run OCR →', 'Extract visible ISI, CM/L, R-number and HUID candidates from an image.'],
    'qr / barcode': ['Scan a code →', 'Decode a QR or barcode and classify the destination or product signal.'],
    'mark verification': ['Verify a mark →', 'Screen ISI / CM-L references and show the verification boundary.'],
    'lab intelligence': ['Find a laboratory →', 'Match a product, standard and test scope to suitable facilities.'],
    'test report ai': ['Analyze a test report →', 'Extract reported measurements without fabricating limits.'],
    'amendment impact': ['Check amendment impact →', 'Review supplied amendment evidence against the selected product or standard.'],
    'agent router': ['Ask SmartGuide →', 'Route your question to the relevant standards, RAG or compliance workflow.'],
    'compliance passport': ['Open compliance passport →', 'Review persistent assessment evidence and traceability.'],
    'pdf reports': ['Generate a report →', 'Create an evidence-aware report from the available SmartGuide results.']
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
      const open = card.querySelector('.sg-v8-open');
      if (cfg) {
        if (open && open.textContent !== cfg[0]) open.textContent = cfg[0];
        const p = card.querySelector('p');
        if (p && p.textContent !== cfg[1]) p.textContent = cfg[1];
        card.classList.add('sg-friendly-card');
        const aria = cfg[0].replace(/\s*→$/, '');
        if (card.getAttribute('aria-label') !== aria) card.setAttribute('aria-label', aria);
      } else if (open && /^open workflow\s*→?$/i.test(open.textContent.trim())) {
        // No feature should expose the old generic placeholder CTA.
        open.textContent = 'Get started →';
        card.classList.add('sg-friendly-card');
      }
    });

    // Also catch workflow labels rendered outside the feature-card selector.
    document.querySelectorAll('.sg-v8-open, button, a').forEach(el => {
      const t = norm(el.textContent);
      if ((t === 'open workflow →' || t === 'open workflow') && el.textContent !== 'Get started →') {
        el.textContent = 'Get started →';
      }
    });

    document.querySelectorAll('.nav button, .nav a').forEach(el => {
      const text = norm(el.textContent);
      Object.keys(navLabels).forEach(k => {
        if (text === k || text.endsWith(k)) {
          const span = el.querySelector('span:last-child');
          if (span && span.textContent !== navLabels[k]) span.textContent = navLabels[k];
        }
      });
    });

    const productInput = document.querySelector('#productInput, #product, input[name="product"], #piProduct');
    if (productInput) {
      const placeholder = 'Try: mobile phone, gas stove, laptop, PVC cable…';
      if (productInput.getAttribute('placeholder') !== placeholder) productInput.setAttribute('placeholder', placeholder);
      productInput.setAttribute('aria-label', 'Product name or description');
    }
  }

  function injectStyles() {
    if (document.getElementById('sg-v92-style')) return;
    const s = document.createElement('style');
    s.id = 'sg-v92-style';
    s.textContent = `
      .sg-friendly-card { transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
      .sg-friendly-card:hover { transform: translateY(-2px); }
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
      const routes = {
        'product-intelligence': 'intel',
        'qco': 'mandatory',
        'documents': 'docs'
      };
      const id = routes[pageName] || pageName;

      if (pageName === 'advanced' && typeof window.openMark === 'function') {
        if (typeof window.page === 'function' && document.getElementById('v8')) {
          window.page('v8', null, 'ISI + CM/L verification');
        }
        setTimeout(() => window.openMark(), 0);
        return;
      }

      const target = document.getElementById(id);
      if (typeof window.page === 'function' && target) {
        window.page(id, null, title);
        return;
      }

      const btn = [...document.querySelectorAll('.nav button, .nav a')]
        .find(b => norm(b.textContent).includes(norm(title)));
      if (btn) { btn.click(); return; }

      if (target) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        target.classList.add('active');
      }
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
    injectStyles();
    applyLabels();
    addHelpStrip();
    addTaskStrip();
    addMapLinks();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  [400,1200,2500,5000].forEach(ms=>setTimeout(boot,ms));
})();
