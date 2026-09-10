/* BIS SmartGuide V8.6 integration layer. Keeps the existing V6/V8 UI and adds polished evidence-safe workflows. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const pretty = x => { try { return JSON.stringify(x, null, 2); } catch { return String(x); } };
  const host = () => typeof window.getSmartGuideApiHost === 'function' ? window.getSmartGuideApiHost() : ((location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://127.0.0.1:5000' : 'https://sih26107-bis-smartguide-api.onrender.com');
  async function api(path, options={}) {
    const res = await fetch(host() + path, options);
    let data = {}; try { data = await res.json(); } catch {}
    if (!res.ok) throw new Error(data.error || data.message || `Request failed (${res.status})`);
    return data;
  }
  function injectStyles(){
    if(document.getElementById('sg-v86-style')) return;
    const s=document.createElement('style'); s.id='sg-v86-style'; s.textContent=`
      .sg-v86-summary{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;padding:18px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(135deg,#f8fbff,#fff);margin-bottom:12px}
      .sg-v86-kicker{font-size:10px;text-transform:uppercase;letter-spacing:1.4px;color:#6f86a4;font-weight:950}.sg-v86-summary h3{margin:5px 0 7px;font-size:20px}.sg-v86-summary p{margin:0;color:var(--muted);font-size:12px;line-height:1.55}
      .sg-v86-score{text-align:center;min-width:105px}.sg-v86-score b{display:block;font-size:30px;color:var(--blue);line-height:1}.sg-v86-score span{display:block;margin-top:5px;color:var(--muted);font-size:10px;font-weight:850}
      .sg-v86-meter{height:7px;background:#e9eef5;border-radius:99px;overflow:hidden;margin-top:12px}.sg-v86-meter i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),#45b0ff);border-radius:99px}
      .sg-v86-standard{border:1px solid var(--line);border-radius:15px;padding:16px;margin:10px 0;background:#fff}.sg-v86-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.sg-v86-no{color:var(--blue);font-weight:950;font-size:13px}.sg-v86-title{font-size:15px;font-weight:900;margin-top:4px}.sg-v86-score-small{font-size:20px;font-weight:950;color:var(--blue);white-space:nowrap}.sg-v86-standard p{margin:8px 0;color:var(--muted);font-size:12px;line-height:1.5}.sg-v86-reasons{display:grid;gap:5px;margin:10px 0}.sg-v86-reason{font-size:11px;color:#536781}.sg-v86-reason:before{content:'✓';color:var(--success);font-weight:950;margin-right:7px}.sg-v86-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.sg-v86-btn{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:9px;padding:7px 10px;font-size:10px;font-weight:900}.sg-v86-btn.primary{background:var(--blue);color:#fff;border-color:var(--blue)}
      .sg-v86-empty{padding:20px;border:1px solid #f1dfb6;background:#fff8e9;border-radius:14px}.sg-v86-empty h3{margin:0 0 7px;font-size:15px}.sg-v86-empty p{margin:5px 0;color:#72500d;font-size:12px;line-height:1.55}.sg-v86-suggestions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.sg-v86-chip{border:1px solid #cde5fb;background:#eef7ff;color:#24527f;border-radius:999px;padding:7px 10px;font-size:10px;font-weight:900;cursor:pointer}
      .sg-v86-evidence{margin-top:12px;padding:13px;border:1px solid #cfe1f5;background:#f8fbff;border-radius:13px}.sg-v86-evidence b{font-size:11px}.sg-v86-evidence div{margin-top:5px;color:var(--muted);font-size:10px;line-height:1.5}.sg-v86-raw{margin-top:10px}.sg-v86-raw summary{cursor:pointer;color:#6d7e98;font-size:10px;font-weight:850}.sg-v86-raw pre{margin-top:7px;max-height:260px;overflow:auto;background:#0b1428;color:#dce7f5;border-radius:11px;padding:12px;font-size:10px}
      @media(max-width:650px){.sg-v86-summary{grid-template-columns:1fr}.sg-v86-score{text-align:left}.sg-v86-top{flex-direction:column}.sg-v86-score-small{font-size:17px}}
    `; document.head.appendChild(s);
  }
  function tool(title, body) {
    const el = $('v8Tool'); if (!el) return;
    el.innerHTML = `<div class="sg-v8-card sg-v8-tool"><div class="section-head"><div><h2>${esc(title)}</h2></div><button class="btn" type="button" onclick="$('v8Tool').innerHTML=''">Close</button></div>${body}</div>`;
    el.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function rawOut(data) { const el=$('v8Out'); if(el) el.innerHTML=`<div class="sg-v8-result-head"><b>Source-grounded workflow result</b><button class="btn ghost" onclick="navigator.clipboard?.writeText(this.closest('.sg-v8-result').querySelector('pre').textContent)">Copy</button></div><pre>${esc(pretty(data))}</pre>`; }
  function out(data) { if(!renderProductIntelligence(data)) rawOut(data); }
  function loading(){ const el=$('v8Out'); if(el) el.innerHTML='<div class="sg-v8-loading">Running SmartGuide workflow…</div>'; }
  function jsonBody(obj){return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)};}

  function renderProductIntelligence(data){
    if(!data || !(data.feature==='Product intelligence' || Array.isArray(data.ranked_standards))) return false;
    injectStyles();
    const el=$('v8Out'); if(!el) return false;
    const list=Array.isArray(data.ranked_standards)?data.ranked_standards:[];
    const q=data.description || data.query || data.product || 'Product';
    const confidence=Number(data.confidence);
    const pct=Number.isFinite(confidence)?Math.round(Math.max(0,Math.min(1,confidence))*100):0;
    const status=String(data.status||'').toUpperCase();
    const matched=list.length>0 && status!=='NO_MATCH';
    const sourceNames=(data.sources||[]).map(s=>s && (s.name||s.title)).filter(Boolean).slice(0,4);
    let html=`<div class="sg-v86-summary"><div><div class="sg-v86-kicker">Product intelligence</div><h3>${esc(q)}</h3><p>${matched?'Potentially applicable BIS standards ranked using the available SmartGuide evidence.':'No sufficiently supported standard was found in the current SmartGuide corpus. This is a search limitation, not a certification decision.'}</p>${pct?`<div class="sg-v86-meter"><i style="width:${pct}%"></i></div>`:''}</div><div class="sg-v86-score"><b>${pct}%</b><span>${matched?'confidence':'confidence'}</span></div></div>`;
    if(matched){
      list.slice(0,6).forEach((s,i)=>{
        const scoreRaw=Number(s.match_score ?? s.score ?? s.raw_match_score);
        const score=Number.isFinite(scoreRaw)?Math.round(scoreRaw>1?scoreRaw:scoreRaw*100):null;
        const title=s.title || s.name || 'Applicable standard candidate';
        const no=s.standard_number || s.number || 'Standard number unavailable';
        const reasons=Array.isArray(s.match_reasons)?s.match_reasons:(Array.isArray(s.reasons)?s.reasons:[]);
        const source=s.official_source || s.source_url || s.source;
        html+=`<div class="sg-v86-standard"><div class="sg-v86-top"><div><div class="sg-v86-no">${esc(no)}</div><div class="sg-v86-title">${esc(title)}</div></div>${score!==null?`<div class="sg-v86-score-small">${score}%</div>`:''}</div>`;
        if(s.description) html+=`<p>${esc(s.description)}</p>`;
        if(score!==null) html+=`<div class="sg-v86-meter"><i style="width:${Math.max(0,Math.min(100,score))}%"></i></div>`;
        if(reasons.length) html+=`<div class="sg-v86-reasons">${reasons.slice(0,5).map(r=>`<div class="sg-v86-reason">${esc(typeof r==='string'?r:(r.reason||r.text||JSON.stringify(r)))}</div>`).join('')}</div>`;
        html+=`<div class="sg-v86-actions">${source?`<a class="sg-v86-btn" href="${esc(source)}" target="_blank" rel="noopener">Open source ↗</a>`:''}<button class="sg-v86-btn primary" type="button" onclick="window.sgUseStandard?.(${JSON.stringify(no)})">Use for compliance</button></div></div>`;
      });
    } else {
      const suggestions=['mobile phone','smartphone','cellular phone','mobile device'];
      html+=`<div class="sg-v86-empty"><h3>We couldn't confidently match this product</h3><p>Try a more specific product description. <b>“mobile”</b> is broad and may not map to a single BIS product category in the current corpus.</p><div class="sg-v86-suggestions">${suggestions.map(x=>`<button class="sg-v86-chip" type="button" onclick="window.sgRetryProduct?.(${JSON.stringify(x)})">${esc(x)}</button>`).join('')}</div></div>`;
    }
    if(sourceNames.length) html+=`<div class="sg-v86-evidence"><b>Evidence sources</b><div>${sourceNames.map(esc).join(' · ')}</div></div>`;
    const notice=data.prototype_notice || data.notice || 'AI-assisted screening only. Verify the current applicable BIS standard, amendment, QCO and official registry before acting.';
    html+=`<div class="notice" style="margin-top:12px">${esc(notice)}</div>`;
    html+=`<details class="sg-v86-raw"><summary>Developer details</summary><pre>${esc(pretty(data))}</pre></details>`;
    el.innerHTML=html;
    return true;
  }

  window.sgUseStandard = standard => {
    const input=document.querySelector('#complianceProduct,#productInput,#compliance-product,input[name="product"]');
    if(input){input.value=standard; input.dispatchEvent(new Event('input',{bubbles:true}));}
    const btn=[...document.querySelectorAll('button')].find(b=>/run compliance|check compliance|analy[sz]e compliance/i.test(b.textContent||''));
    if(btn) btn.click();
  };
  window.sgRetryProduct = async product => {
    const el=$('v8Out'); if(el) el.innerHTML='<div class="sg-v8-loading">Searching the BIS standards corpus…</div>';
    try{out(await api('/v8/product-intelligence',jsonBody({query:product})));}catch(e){rawOut({error:e.message});}
  };

  // Catch Product Intelligence results produced by the legacy UI as well as V8 workflows.
  function observeLegacyResults(){
    const root=document.body; if(!root || root.dataset.sgV86Observer==='1')return;
    root.dataset.sgV86Observer='1';
    const observer=new MutationObserver(()=>{
      const pre=document.querySelector('#v8Out pre'); if(!pre || pre.dataset.sgV86Done==='1')return;
      const text=pre.textContent||''; if(!text.includes('ranked_standards') && !text.includes('"feature": "Product intelligence"'))return;
      try{const data=JSON.parse(text); if(renderProductIntelligence(data)) pre.dataset.sgV86Done='1';}catch{}
    });
    observer.observe(root,{subtree:true,childList:true,characterData:true});
  }

  window.sgOpenDocument = () => tool('Document → clause → evidence', `<div class="sg-v8-form"><input id="sgDoc" type="file" accept=".pdf,.txt,.md,.json,.doc,.docx,.png,.jpg,.jpeg,.webp" class="full"><p class="sg-v8-muted">PDF/TXT/MD/JSON/DOCX extraction and image OCR are attempted with no synthetic fallback.</p><button class="btn primary" onclick="sgRunDocument()">Ingest document</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunDocument = async () => { loading(); const f=$('sgDoc')?.files?.[0]; if(!f) return out({error:'Select a document or image.'}); const fd=new FormData(); fd.append('file',f); try{out(await api('/api/v8/document/ingest',{method:'POST',body:fd}));}catch(e){out({error:e.message});} };

  window.sgOpenOCR = () => tool('Photo intelligence / OCR', `<div class="sg-v8-form"><input id="sgOCR" type="file" accept="image/png,image/jpeg,image/webp" class="full"><p class="sg-v8-muted">Detects text and candidate IS / CM-L / R-number / HUID strings. Detection is not verification.</p><button class="btn primary" onclick="sgRunOCR()">Run real OCR</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunOCR = async () => { loading(); const f=$('sgOCR')?.files?.[0]; if(!f) return out({error:'Select an image.'}); const fd=new FormData(); fd.append('file',f); try{out(await api('/api/v8/ocr',{method:'POST',body:fd}));}catch(e){out({error:e.message});} };

  window.sgOpenQR = () => tool('Universal QR / Barcode', `<div class="sg-v8-form"><input id="sgQR" type="file" accept="image/png,image/jpeg,image/webp" class="full"><p class="sg-v8-muted">Decodes QR/barcode content, classifies official-BIS-looking URLs, and never trusts arbitrary destinations automatically.</p><button class="btn primary" onclick="sgRunQR()">Decode</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunQR = async () => { loading(); const f=$('sgQR')?.files?.[0]; if(!f) return out({error:'Select a QR/barcode image.'}); const fd=new FormData(); fd.append('file',f); try{out(await api('/api/v8/qr/decode',{method:'POST',body:fd}));}catch(e){out({error:e.message});} };

  window.sgOpenVerify = () => tool('ISI / CM-L / CRS / HUID verification', `<div class="sg-v8-form"><select id="sgVerifyType"><option value="mark">ISI / CM-L</option><option value="crs">CRS R-number</option><option value="huid">HUID</option></select><input id="sgVerifyValue" class="full" placeholder="Paste the mark, number, or label text"><button class="btn primary" onclick="sgRunVerify()">Screen & verify</button><p class="sg-v8-muted">Format detection is separated from official verification. If the official registry is unavailable, SmartGuide returns SOURCE_UNAVAILABLE.</p></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunVerify = async () => { loading(); const type=$('sgVerifyType').value, text=$('sgVerifyValue').value; const path=type==='mark'?'/api/v8/verify/mark':type==='crs'?'/api/v8/verify/crs':'/api/v8/verify/huid'; try{out(await api(path,jsonBody({text})));}catch(e){out({error:e.message});} };

  window.sgOpenLabs = () => tool('Capability-aware laboratory matcher', `<div class="sg-v8-form"><input id="sgLabProduct" placeholder="Product"><input id="sgLabStd" placeholder="IS number"><input id="sgLabTest" placeholder="Required test / parameter"><input id="sgLabCity" placeholder="City / state (optional)"><button class="btn primary" onclick="sgRunLabs()">Match laboratories</button><p class="sg-v8-muted">Distance is not claimed unless location comparison is actually performed. Local lab records are explicitly marked as an unverified snapshot.</p></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunLabs = async () => { loading(); const q=new URLSearchParams({product:$('sgLabProduct').value,standard:$('sgLabStd').value,test:$('sgLabTest').value,city:$('sgLabCity').value}); try{out(await api('/api/v8/labs/match?'+q));}catch(e){out({error:e.message});} };

  window.sgOpenTestReport = () => tool('Test report intelligence', `<div class="sg-v8-form"><input id="sgTestFile" type="file" accept=".pdf,.txt,.md,.json,.docx,.png,.jpg,.jpeg,.webp" class="full"><input id="sgTestStd" placeholder="IS number (optional)"><textarea id="sgTestText" class="full" placeholder="Or paste report text: Voltage: 230 V\nPower: 1200 W"></textarea><button class="btn primary" onclick="sgRunTestReport()">Analyze report</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunTestReport = async () => { loading(); try{const f=$('sgTestFile')?.files?.[0]; let result; if(f){const fd=new FormData();fd.append('file',f);fd.append('standard',$('sgTestStd').value);result=await api('/api/v8/tests/analyze',{method:'POST',body:fd});}else result=await api('/api/v8/tests/analyze',jsonBody({standard:$('sgTestStd').value,text:$('sgTestText').value}));out(result);}catch(e){out({error:e.message});} };

  window.sgOpenAmendments = () => tool('Amendment / Gazette intelligence', `<div class="sg-v8-form"><input id="sgAmStd" placeholder="IS number"><input id="sgAmProduct" placeholder="Product"><textarea id="sgAmText" class="full" placeholder="Paste the official amendment/QCO text you want analysed"></textarea><button class="btn primary" onclick="sgRunAmendment()">Analyze supplied amendment</button><p class="sg-v8-muted">Live Gazette monitoring is not claimed unless an official source integration is connected.</p></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunAmendment = async () => { loading(); try{out(await api('/api/v8/amendments/impact',jsonBody({standard:$('sgAmStd').value,product:$('sgAmProduct').value,amendment:$('sgAmText').value})));}catch(e){out({error:e.message});} };

  window.sgOpenAgent = () => tool('AI Agent orchestration', `<div class="sg-v8-form"><select id="sgAgentRole"><option value="general">General</option><option value="manufacturer_msme">Manufacturer / MSME</option><option value="startup">Startup</option><option value="importer">Importer</option><option value="procurement">Procurement</option><option value="consumer">Consumer</option><option value="compliance_pro">Compliance Professional</option><option value="laboratory">Laboratory</option></select><textarea id="sgAgentMsg" class="full" placeholder="Example: I manufacture electric kettles. What should I check before selling them?"></textarea><button class="btn primary" onclick="sgRunAgent()">Route request</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunAgent = async () => { loading(); try{out(await api('/api/v8/agent/orchestrate',jsonBody({role:$('sgAgentRole').value,message:$('sgAgentMsg').value})));}catch(e){out({error:e.message});} };

  window.sgOpenPassport = () => tool('Compliance Passport & evidence', `<div class="sg-v8-form"><input id="sgPassport" placeholder="Assessment ID (e.g. BIS-XXXXXXXXXX)"><button class="btn primary" onclick="sgRunPassport()">Open passport</button><p class="sg-v8-muted">Uses the existing V4 persistent assessment history and evidence model.</p></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunPassport = async () => { loading(); const id=$('sgPassport').value.trim(); if(!id)return out({error:'Assessment ID is required.'}); try{out(await api('/v4/passport/'+encodeURIComponent(id)));}catch(e){out({error:e.message});} };

  window.sgOpenReportPDF = () => tool('Professional PDF report', `<div class="sg-v8-form"><input id="sgRepProduct" placeholder="Product"><input id="sgRepStd" placeholder="Standard"><input id="sgRepStatus" placeholder="Compliance status"><input id="sgRepScore" type="number" placeholder="Score"><textarea id="sgRepEvidence" class="full" placeholder="Evidence JSON is optional"></textarea><button class="btn primary" onclick="sgRunReportPDF()">Generate PDF</button></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.sgRunReportPDF = async () => { const evidence=[]; try{const raw=$('sgRepEvidence').value.trim(); if(raw)evidence.push(...JSON.parse(raw));}catch{return out({error:'Evidence must be valid JSON array.'});} const payload={product:$('sgRepProduct').value,standard:$('sgRepStd').value,status:$('sgRepStatus').value,score:$('sgRepScore').value,evidence}; try{const res=await fetch(host()+'/api/v8/report/pdf',jsonBody(payload)); if(!res.ok)throw Error('PDF generation failed'); const blob=await res.blob(); const url=URL.createObjectURL(blob); const a=document.createElement('a');a.href=url;a.download='bis-smartguide-report.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000); if($('v8Out'))$('v8Out').innerHTML='<div class="sg-v8-result"><b>PDF generated successfully.</b><p class="sg-v8-muted">The report includes the SmartGuide decision-support disclaimer.</p></div>';}catch(e){out({error:e.message});} };

  function addCards(){
    const grid=document.querySelector('#v8 .sg-v8-grid'); if(!grid || grid.dataset.sgUpgrade==='1')return;
    const cards=[['📄','Document Intelligence','PDF, DOCX, text and image → extraction → clauses → evidence','sgOpenDocument'],['🔠','Real OCR','Read labels, ISI, CM/L, R-number and HUID candidates','sgOpenOCR'],['▦','QR / Barcode','Decode and classify destination trust','sgOpenQR'],['🛡️','Mark Verification','Separate format screening from official verification','sgOpenVerify'],['🧪','Lab Intelligence','Match standard/test scope and expose verification status','sgOpenLabs'],['🧾','Test Report AI','Extract measurements without fabricating limits','sgOpenTestReport'],['📜','Amendment Impact','Analyse supplied amendment evidence safely','sgOpenAmendments'],['🤖','Agent Router','Route product, RAG, verification, lab and testing workflows','sgOpenAgent'],['🛡','Compliance Passport','Open persistent assessment evidence','sgOpenPassport'],['📑','PDF Reports','Generate professional evidence-aware reports','sgOpenReportPDF']];
    cards.forEach(c=>{const b=document.createElement('button');b.type='button';b.className='sg-v8-card sg-v8-feature';b.onclick=window[c[3]];b.innerHTML=`<span class="sg-v8-icon">${c[0]}</span><h3>${c[1]}</h3><p>${c[2]}</p><span class="sg-v8-open">Open workflow →</span>`;grid.appendChild(b);});
    grid.dataset.sgUpgrade='1';
  }
  function init(){injectStyles();addCards();setTimeout(addCards,500);setTimeout(addCards,1500);setTimeout(observeLegacyResults,200);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();