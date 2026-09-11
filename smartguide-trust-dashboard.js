/* BIS SmartGuide Trust Dashboard v1 — verified metrics only, no fabricated telemetry. */
(() => {
  'use strict';
  const API = 'https://sih26107-bis-smartguide-api.onrender.com';
  const BIS = {
    standards: 'https://www.bis.gov.in/know-your-standard/?lang=en',
    compulsory: 'https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en',
    labs: 'https://lims.bis.gov.in/',
    care: 'https://www.bis.gov.in/bis-apps/?lang=en'
  };

  function style() {
    if (document.getElementById('sg-trust-style')) return;
    const s = document.createElement('style'); s.id = 'sg-trust-style';
    s.textContent = `
      .sg-trust-panel{margin-top:22px;background:#fff;border:1px solid #dce6f2;border-radius:20px;padding:20px;box-shadow:0 14px 40px rgba(20,50,90,.07)}
      .sg-trust-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:15px}
      .sg-trust-head h2{margin:0;font-size:19px}.sg-trust-head p{margin:5px 0 0;color:#6d7e98;font-size:12px;line-height:1.5}
      .sg-trust-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:7px 10px;background:#eaf9f2;color:#117451;font-size:10px;font-weight:900;white-space:nowrap}
      .sg-trust-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
      .sg-trust-stat{border:1px solid #e1e8f1;border-radius:14px;padding:14px;background:#f9fbfe}.sg-trust-stat b{display:block;font-size:21px;color:#10213f}.sg-trust-stat span{font-size:10px;color:#6d7e98}.sg-trust-stat small{display:block;margin-top:5px;font-size:9px;color:#8392a6}
      .sg-trust-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.sg-trust-links a{border:1px solid #dce6f2;border-radius:10px;padding:8px 10px;font-size:10px;background:#fff;color:#1769e0}.sg-trust-note{margin-top:14px;padding:11px 13px;border-radius:11px;background:#f5f8fc;color:#536781;font-size:10px;line-height:1.55}
      @media(max-width:800px){.sg-trust-grid{grid-template-columns:1fr 1fr}.sg-trust-head{flex-direction:column}}
    `;
    document.head.appendChild(s);
  }

  async function health() {
    try {
      const r = await fetch(API + '/health', { cache:'no-store' });
      if (!r.ok) throw new Error('health');
      return await r.json();
    } catch (_) { return null; }
  }

  function stat(label, value, detail) {
    return `<div class="sg-trust-stat"><b>${value}</b><span>${label}</span><small>${detail}</small></div>`;
  }

  async function add() {
    if (document.getElementById('sg-trust-panel')) return;
    const page = document.querySelector('#dash') || document.querySelector('.page.active');
    if (!page) return;
    const panel = document.createElement('section'); panel.id='sg-trust-panel'; panel.className='sg-trust-panel';
    panel.innerHTML = `<div class="sg-trust-head"><div><h2>SmartGuide Intelligence & Trust</h2><p>Only verified system metrics and official BIS source links are shown here. No fabricated laboratory telemetry, compliance percentages or fake unit counts.</p></div><span class="sg-trust-badge">● SOURCE-GROUNDED</span></div><div id="sg-trust-grid" class="sg-trust-grid">${stat('Standards indexed','—','Local BIS corpus')} ${stat('RAG evidence chunks','—','Local retrieval layer')} ${stat('Standards loaded','—','Backend health')} ${stat('Agent status','Checking…','Gemini / local fallback')}</div><div class="sg-trust-links"><a href="${BIS.standards}" target="_blank" rel="noopener">BIS Know Your Standard ↗</a><a href="${BIS.compulsory}" target="_blank" rel="noopener">BIS Compulsory Certification ↗</a><a href="${BIS.labs}" target="_blank" rel="noopener">BIS LIMS Laboratories ↗</a><a href="${BIS.care}" target="_blank" rel="noopener">BIS CARE ↗</a></div><div class="sg-trust-note"><b>Trust boundary:</b> SmartGuide provides AI-assisted guidance and evidence retrieval. It does not issue BIS certification. Mandatory status, QCOs, amendments, standards and laboratory scope must be verified against current official BIS information.</div>`;
    page.appendChild(panel);
    const data = await health();
    const grid = panel.querySelector('#sg-trust-grid');
    if (!data) { grid.innerHTML = `${stat('Backend status','Offline','Unable to read /health')} ${stat('Local corpus','Available','Frontend remains usable')} ${stat('Official sources','Linked','BIS verification links')} ${stat('Agent','Fallback','External model unavailable')}`; return; }
    const agent = data.agent || (data.status === 'healthy' ? 'Available' : 'Unknown');
    grid.innerHTML = `${stat('Standards indexed',data.standards_loaded ?? data.std_count ?? '—','Backend health')} ${stat('RAG evidence chunks',data.rag_chunks ?? '—','Local retrieval layer')} ${stat('Documents indexed',data.documents_indexed ?? '—','Backend health')} ${stat('Agent status',data.status === 'healthy' ? agent : 'Degraded',data.agentic_chat ? 'Agentic chat enabled' : 'Local mode')}`;
  }

  function boot(){ style(); setTimeout(add, 700); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
