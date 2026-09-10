/* BIS SmartGuide V8.5 integration layer. Keeps the existing V6/V8 UI and adds real evidence-safe workflows. */
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
  function tool(title, body) {
    const el = $('v8Tool'); if (!el) return;
    el.innerHTML = `<div class="sg-v8-card sg-v8-tool"><div class="section-head"><div><h2>${esc(title)}</h2></div><button class="btn" type="button" onclick="$('v8Tool').innerHTML=''">Close</button></div>${body}</div>`;
    el.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function out(data) { const el=$('v8Out'); if(el) el.innerHTML=`<div class="sg-v8-result-head"><b>Source-grounded workflow result</b><button class="btn ghost" onclick="navigator.clipboard?.writeText(this.closest('.sg-v8-result').querySelector('pre').textContent)">Copy</button></div><pre>${esc(pretty(data))}</pre>`; }
  function loading(){ const el=$('v8Out'); if(el) el.innerHTML='<div class="sg-v8-loading">Running SmartGuide workflow…</div>'; }
  function jsonBody(obj){return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)};}

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
  function init(){addCards();setTimeout(addCards,500);setTimeout(addCards,1500);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
