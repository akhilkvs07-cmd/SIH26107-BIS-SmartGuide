/* BIS SmartGuide Agent UI — render orchestration JSON safely without replacing the whole panel. */
(() => {
  'use strict';

  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = v => { const n=Number(v); return Number.isFinite(n) ? `${Math.round(Math.max(0,Math.min(1,n))*100)}%` : '—'; };
  const arr = v => Array.isArray(v) ? v : [];

  function build(raw) {
    let parsed;
    try { parsed=JSON.parse(raw); } catch(_) { return null; }
    if (!parsed || typeof parsed !== 'object') return null;
    const d=parsed.data && typeof parsed.data==='object' ? parsed.data : parsed;
    const standards=arr(d.candidate_standards).length ? d.candidate_standards : arr(d.ranked_standards);
    const route=arr(d.route);
    const evidence=arr(parsed.evidence).length ? parsed.evidence : arr(d.retrieved_evidence);
    const requirements=arr(d.requirements);
    const reasons=arr(d.match_reasons);
    const confidence=parsed.confidence ?? d.confidence;
    const product=d.product || d.description || '';
    const source=d.official_source || parsed.source || '';
    const primary=standards[0] || {};
    const primaryNo=primary.standard_number || primary.standard_id || 'No standard identified';
    const primaryTitle=primary.title || primary.description || '';
    const score=primary.match_score ?? primary.relevance ?? null;
    const cards=standards.slice(0,4).map((s,i)=>`<div class="sg-agent-standard"><div class="sg-agent-rank">${i+1}</div><div><b>${esc(s.standard_number||s.standard_id||'Standard')}</b><div>${esc(s.title||s.description||'Candidate standard')}</div></div><strong>${s.match_score!=null?esc(s.match_score)+'%':'—'}</strong></div>`).join('');
    const reqs=requirements.slice(0,6).map(x=>`<span class="sg-agent-chip">${esc(typeof x==='string'?x:(x.name||x.requirement||JSON.stringify(x)))}</span>`).join('');
    const rs=reasons.slice(0,4).map(x=>`<li>${esc(typeof x==='string'?x:JSON.stringify(x))}</li>`).join('');
    const ev=evidence.slice(0,4).map(x=>{const text=x.text||x.evidence_text||x.title||x.standard||x.source||JSON.stringify(x);return `<div class="sg-agent-evidence"><span>Evidence</span><p>${esc(text)}</p></div>`;}).join('');
    const routeHtml=route.length ? `<div class="sg-agent-section"><h4>Recommended workflow</h4><div class="sg-agent-route">${route.map(x=>`<span>${esc(String(x).replace(/[-_]/g,' ').replace(/\b\w/g,c=>c.toUpperCase()))}</span>`).join('<i>→</i>')}</div></div>` : '';
    return { parsed, html:`<div class="sg-agent-result"><div class="sg-agent-result-head"><div><span class="sg-agent-kicker">SOURCE-GROUNDED AGENT</span><h3>SmartGuide routing result</h3><p>${product?`Analysis for <b>${esc(product)}</b>`:'Request analyzed by the SmartGuide orchestration layer.'}</p></div><div class="sg-agent-confidence"><b>${pct(confidence)}</b><small>confidence</small></div></div>${routeHtml}<div class="sg-agent-grid"><div class="sg-agent-panel"><small>PRIMARY STANDARD</small><b>${esc(primaryNo)}</b><p>${esc(primaryTitle)}</p>${score!=null?`<div class="sg-agent-meter"><i style="width:${Math.max(0,Math.min(100,Number(score)||0))}%"></i></div><span>${esc(score)}% match</span>`:''}</div><div class="sg-agent-panel"><small>COMPLIANCE SIGNAL</small><b>${esc(d.qco_order||d.mandatory_status||d.verification_status||'Needs verification')}</b><p>SmartGuide will not treat screening as official certification.</p></div></div>${cards?`<div class="sg-agent-section"><h4>Candidate standards</h4><div class="sg-agent-standards">${cards}</div></div>`:''}${reqs?`<div class="sg-agent-section"><h4>Requirement areas</h4><div class="sg-agent-chips">${reqs}</div></div>`:''}${rs?`<div class="sg-agent-section"><h4>Why this matched</h4><ul class="sg-agent-reasons">${rs}</ul></div>`:''}${ev?`<div class="sg-agent-section"><h4>Evidence trail</h4>${ev}</div>`:''}${source?`<div class="sg-agent-source">Official source: <a href="${esc(source)}" target="_blank" rel="noopener">Open source →</a></div>`:''}<div class="sg-agent-notice">AI-assisted screening only. Verify the current BIS standard, amendments, QCOs and scope against official BIS sources before making a compliance decision.</div><details class="sg-agent-raw"><summary>View raw API response</summary><pre>${esc(JSON.stringify(parsed,null,2))}</pre></details></div>` };
  }

  function scan() {
    const active=[...document.querySelectorAll('h1,h2,h3,h4')].some(h=>/AI Agent orchestration|Source-grounded workflow result/i.test(h.textContent||''));
    if(!active) return;
    for(const pre of [...document.querySelectorAll('pre')]) {
      if(pre.dataset.sgAgentDone==='1') continue;
      const raw=(pre.textContent||'').trim();
      if(!raw.startsWith('{') || !/confidence|candidate_standards|route/.test(raw)) continue;
      const result=build(raw);
      if(!result) continue;
      const wrap=document.createElement('div');
      wrap.className='sg-agent-live-wrap';
      wrap.innerHTML=result.html;
      const details=document.createElement('details');
      details.className='sg-agent-raw-source';
      details.style.display='none';
      pre.dataset.sgAgentDone='1';
      pre.replaceWith(wrap);
      // Preserve the raw response for debugging without destroying surrounding controls.
      details.innerHTML=`<summary>raw</summary><pre>${esc(raw)}</pre>`;
      wrap.appendChild(details);
    }
  }

  const style=document.createElement('style');
  style.textContent=`
    .sg-agent-live-wrap{width:100%;margin-top:12px}.sg-agent-result{background:#fff;border:1px solid #dce6f2;border-radius:16px;padding:18px;color:#10213f}.sg-agent-result-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.sg-agent-result-head h3{margin:4px 0;font-size:18px}.sg-agent-result-head p{margin:0;color:#6d7e98;font-size:12px}.sg-agent-kicker{font-size:9px;font-weight:950;letter-spacing:1.4px;color:#1769e0}.sg-agent-confidence{min-width:78px;text-align:center;background:#eef7ff;border:1px solid #cde5fb;border-radius:13px;padding:9px}.sg-agent-confidence b{display:block;font-size:20px;color:#1769e0}.sg-agent-confidence small{font-size:9px;color:#6d7e98}.sg-agent-section{margin-top:17px}.sg-agent-section h4{margin:0 0 9px;font-size:12px}.sg-agent-route{display:flex;gap:7px;flex-wrap:wrap;align-items:center}.sg-agent-route span{background:#eef5ff;color:#175ba9;border-radius:999px;padding:7px 10px;font-size:10px;font-weight:900}.sg-agent-route i{font-style:normal;color:#8aa0ba}.sg-agent-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:15px}.sg-agent-panel{border:1px solid #dce6f2;border-radius:13px;padding:13px}.sg-agent-panel small{display:block;color:#70819a;font-size:9px;font-weight:900;letter-spacing:.8px}.sg-agent-panel>b{display:block;margin-top:5px;color:#1769e0}.sg-agent-panel p{font-size:11px;color:#6d7e98;line-height:1.45}.sg-agent-meter{height:6px;background:#edf1f6;border-radius:99px;overflow:hidden;margin-top:9px}.sg-agent-meter i{display:block;height:100%;background:#1769e0;border-radius:99px}.sg-agent-panel>span{font-size:9px;color:#6d7e98}.sg-agent-standards{display:grid;gap:7px}.sg-agent-standard{display:grid;grid-template-columns:25px 1fr auto;gap:9px;align-items:center;border:1px solid #dce6f2;border-radius:11px;padding:9px}.sg-agent-rank{width:23px;height:23px;border-radius:7px;background:#eef5ff;color:#1769e0;display:grid;place-items:center;font-size:10px;font-weight:950}.sg-agent-standard b{font-size:11px}.sg-agent-standard div div{font-size:10px;color:#6d7e98;margin-top:2px}.sg-agent-standard>strong{font-size:10px;color:#1769e0}.sg-agent-chips{display:flex;gap:6px;flex-wrap:wrap}.sg-agent-chip{background:#f3f7fc;border:1px solid #dce6f2;border-radius:999px;padding:6px 9px;font-size:9px;color:#536781}.sg-agent-reasons{margin:0;padding-left:18px;color:#536781;font-size:11px;line-height:1.6}.sg-agent-evidence{border-left:3px solid #1769e0;background:#f8fbff;padding:8px 10px;margin:6px 0}.sg-agent-evidence span{font-size:9px;font-weight:900;color:#1769e0}.sg-agent-evidence p{margin:3px 0;font-size:10px;color:#536781}.sg-agent-source{margin-top:14px;font-size:10px;color:#6d7e98}.sg-agent-notice{margin-top:12px;background:#fff8e9;border:1px solid #f1dfb6;color:#72500d;border-radius:10px;padding:9px;font-size:10px;line-height:1.45}.sg-agent-raw{margin-top:12px;font-size:10px;color:#6d7e98}.sg-agent-raw pre{max-height:260px;overflow:auto;background:#0b1428;color:#dce7f7;padding:10px;border-radius:9px;font-size:9px}@media(max-width:700px){.sg-agent-grid{grid-template-columns:1fr}.sg-agent-result-head{flex-direction:column}}
  `;
  document.head.appendChild(style);

  let timer=0;
  const schedule=()=>{clearTimeout(timer);timer=setTimeout(scan,80);};
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',scan); else scan();
  [300,800,1500,3000,6000,10000].forEach(t=>setTimeout(scan,t));
  // Scoped, debounced observer catches results inserted after Route request without touching the rest of the app.
  const observer=new MutationObserver(schedule);
  const startObserver=()=>observer.observe(document.body,{subtree:true,childList:true});
  if(document.body) startObserver(); else document.addEventListener('DOMContentLoaded',startObserver,{once:true});
})();