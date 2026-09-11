/* BIS SmartGuide Advanced Features — user-friendly workflow console v9.0 */
(() => {
  const API = (typeof window.getSmartGuideApiHost === 'function') ? window.getSmartGuideApiHost() : ((location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? (location.port === '5000' ? '' : 'http://127.0.0.1:5000') : 'https://sih26107-bis-smartguide-api.onrender.com');
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const pretty = x => { try { return JSON.stringify(x, null, 2); } catch { return String(x); } };
  const label = x => String(x ?? '').replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());

  async function api(path, opt = {}) {
    const base = (typeof window.getSmartGuideApiHost === 'function') ? window.getSmartGuideApiHost() : API;
    try {
      const r = await fetch(base + path, opt); let d = {}; try { d = await r.json(); } catch {}
      if (!r.ok) throw Error(d.error || d.message || `Request failed (${r.status})`); return d;
    } catch (err) {
      if (base.includes('localhost') || base.includes('127.0.0.1') || base === '') {
        try { const r2 = await fetch('https://sih26107-bis-smartguide-api.onrender.com' + path, opt); let d2={}; try{d2=await r2.json()}catch{} if(!r2.ok) throw Error(d2.error||d2.message||`Remote request failed (${r2.status})`); return d2; } catch (_) {}
      }
      throw err;
    }
  }

  const features = [
    ['product','🔎','Product AI','Find applicable BIS standards from a product description.','Standards','openProduct'],
    ['mark','✓','ISI / CM-L Check','Screen BIS mark and licence references.','Verification','openMark'],
    ['test','📄','Test Report Reader','Extract useful measurements from a test report.','Testing','openTest'],
    ['lab','🧪','Laboratory Finder','Find and verify relevant BIS laboratory scope.','Testing','openLab'],
    ['amendment','📋','QCO & Amendment','Screen likely impact of a QCO or amendment.','Compliance','openAmendment'],
    ['stl','🧊','3D / STL Scanner','Inspect ASCII or binary STL geometry.','Engineering','openSTL'],
    ['label','🏷️','Label Checker','Screen important product marking fields.','Compliance','openLabel'],
    ['procurement','🛒','Procurement Check','Screen product, raw material and HS-code information.','Business','openProcurement'],
    ['issue','⚠️','Issue / Complaint Draft','Prepare a structured issue or counterfeit complaint draft.','Consumer','openIssue']
  ];

  function card(f) { return `<button class="sg-v9-feature" data-feature="${f[0]}" data-category="${f[4]}" onclick="${f[5]}()" type="button"><span class="sg-v9-feature-icon">${f[1]}</span><span class="sg-v9-feature-body"><b>${f[2]}</b><small>${f[3]}</small><em>Open →</em></span></button>`; }

  function page() {
    if ($('v8')) return;
    const m = document.querySelector('.content'); if (!m) return;
    const s = document.createElement('section'); s.id='v8'; s.className='page';
    s.innerHTML = `
      <div class="sg-v9-hero">
        <div><span class="sg-v9-eyebrow">SMARTGUIDE WORKSPACE</span><h1>Advanced Features</h1><p>Choose a task, enter your information, and SmartGuide will return a clear result instead of raw technical output.</p></div>
        <div class="sg-v9-hero-actions"><button class="sg-v9-primary" onclick="openProduct()">🔎 Find a standard</button><button class="sg-v9-secondary" onclick="openLab()">🧪 Find a laboratory</button></div>
      </div>
      <div class="sg-v9-toolbar"><div class="sg-v9-search"><span>⌕</span><input id="v9Search" placeholder="Search a feature…" oninput="filterV9Features(this.value)"></div><div class="sg-v9-tabs"><button class="active" onclick="filterV9Category('All',this)">All</button><button onclick="filterV9Category('Standards',this)">Standards</button><button onclick="filterV9Category('Verification',this)">Verification</button><button onclick="filterV9Category('Testing',this)">Testing</button><button onclick="filterV9Category('Compliance',this)">Compliance</button><button onclick="filterV9Category('Business',this)">Business</button><button onclick="filterV9Category('Consumer',this)">Consumer</button><button onclick="filterV9Category('Engineering',this)">Engineering</button></div></div>
      <div class="sg-v9-section-title"><div><h2>Choose a workflow</h2><p>Each feature opens its own guided form.</p></div><span class="sg-v9-count"><b id="v9FeatureCount">9</b> tools</span></div>
      <div id="v9Features" class="sg-v9-features">${features.map(card).join('')}</div>
      <div id="v8Tool" class="sg-v9-tool-area"></div>
      <div class="sg-v9-health"><div><span class="sg-v9-eyebrow dark">SYSTEM CHECK</span><h2>Is everything working?</h2><p>Run a quick backend check. Results are shown as readable pass/fail cards.</p></div><button class="sg-v9-secondary dark" onclick="runV8SelfTest()">Run system check</button></div>
      <div id="v8SelfTest" class="sg-v9-selftest"></div>
      <footer class="sg-v9-footer">BIS SmartGuide • SIH 2026 • Problem Statement 26107 • Final regulatory decisions remain source-bound to official BIS information.</footer>`;
    m.appendChild(s);
  }

  function tool(title, desc, body) {
    const el=$('v8Tool'); if(!el)return;
    el.innerHTML=`<div class="sg-v9-tool"><div class="sg-v9-tool-head"><div><span class="sg-v9-eyebrow">WORKFLOW</span><h2>${esc(title)}</h2><p>${esc(desc||'Complete the fields below and run the workflow.')}</p></div><button class="sg-v9-close" onclick="$('v8Tool').innerHTML=''">✕</button></div>${body}</div>`;
    el.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function loading(){const o=$('v8Out');if(o)o.innerHTML='<div class="sg-v9-loading"><span class="sg-v9-spinner"></span><div><b>SmartGuide is working…</b><small>Checking the available evidence and preparing your result.</small></div></div>';}
  function fail(e){const o=$('v8Out');if(o)o.innerHTML=`<div class="sg-v9-error"><b>We could not complete this check.</b><p>${esc(e?.message||e)}</p><small>Check that the backend is awake, then try again.</small></div>`;}

  function value(v) { if(v===null||v===undefined||v==='') return '—'; if(typeof v==='object') return pretty(v); return String(v); }
  function result(d) {
    const o=$('v8Out'); if(!o)return;
    if(!d || typeof d!=='object'){o.innerHTML=`<div class="sg-v9-result-card"><b>Result</b><p>${esc(value(d))}</p></div>`;return;}
    const keys=Object.keys(d);
    const title=d.title||d.result_title||d.decision||d.status||'SmartGuide result';
    const confidence=d.confidence;
    const rows=keys.filter(k=>!['evidence','results','laboratories','labs','data','tests','items','features','raw'].includes(k)).slice(0,12);
    let html=`<div class="sg-v9-result-card"><div class="sg-v9-result-top"><div><span class="sg-v9-eyebrow dark">RESULT</span><h3>${esc(label(title))}</h3></div>${confidence!==undefined?`<span class="sg-v9-confidence">${Math.round(Number(confidence)<=1?Number(confidence)*100:Number(confidence))}% confidence</span>`:''}</div><div class="sg-v9-result-grid">`;
    rows.forEach(k=>{const v=d[k]; if(typeof v==='object' || v===undefined) return; html+=`<div class="sg-v9-result-field"><small>${esc(label(k))}</small><b>${esc(value(v))}</b></div>`;});
    html+='</div>';
    const collections=[['evidence','Evidence'],['results','Matches'],['laboratories','Laboratories'],['labs','Laboratories'],['tests','Checks'],['features','Checks'],['items','Items']];
    for(const [k,h] of collections){ if(Array.isArray(d[k])&&d[k].length){ html+=`<div class="sg-v9-list"><h4>${h}</h4>${d[k].slice(0,12).map((x,i)=>{if(typeof x==='object'){const main=x.name||x.feature||x.lab_name||x.title||x.standard||x.product||x.test||`Item ${i+1}`;const sub=x.status||x.description||x.scope_status||x.message||x.reason||'';return `<div class="sg-v9-list-item"><span class="sg-v9-check">${x.ok===false?'!':'✓'}</span><div><b>${esc(main)}</b><small>${esc(value(sub))}</small></div></div>`;}return `<div class="sg-v9-list-item"><span class="sg-v9-check">✓</span><div><b>${esc(x)}</b></div></div>`;}).join('')}</div>`; break; }}
    if(d.notice||d.message||d.hint) html+=`<div class="sg-v9-notice">${esc(d.notice||d.message||d.hint)}</div>`;
    html+=`<details class="sg-v9-technical"><summary>View technical details</summary><pre>${esc(pretty(d))}</pre></details></div>`;
    o.innerHTML=html;
  }
  function post(path, body){loading();return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(result).catch(fail);}

  window.openProduct=()=>tool('Product → standards','Describe the product and SmartGuide will rank candidate Indian Standards.',`<div class="sg-v9-form"><label>Product description<input id="v8Product" placeholder="Example: 1200W household electric kettle with automatic shutoff"></label><button class="sg-v9-run" onclick="runProduct()">🔎 Find applicable standards</button></div><div id="v8Out"></div>`);
  window.runProduct=()=>post('/v5/product-intelligence',{description:$('v8Product').value});
  window.openMark=()=>tool('ISI / CM-L verification','Screen the text on a product mark or licence reference.','<div class="sg-v9-form"><label>Mark / label text<textarea id="v8MarkText" placeholder="Paste the text visible on the product mark…"></textarea></label><label>Licence / CM-L number <input id="v8Licence" placeholder="Optional"></label><button class="sg-v9-run" onclick="runMark()">✓ Check mark</button></div><div id="v8Out"></div>');
  window.runMark=()=>post('/v5/verify-mark',{text:$('v8MarkText').value,licence:$('v8Licence').value});
  window.openTest=()=>tool('Test-report intelligence','Paste a report excerpt and SmartGuide will extract useful measurements without inventing limits.','<div class="sg-v9-form"><label>Applicable IS number <input id="v8Std" placeholder="Optional"></label><label>Test report text<textarea id="v8Report" placeholder="Voltage: 230 V&#10;Power: 1200 W&#10;Leakage current: 0.4 mA"></textarea></label><button class="sg-v9-run" onclick="runTest()">📄 Read test report</button></div><div id="v8Out"></div>');
  window.runTest=()=>post('/v5/test-report',{standard:$('v8Std').value,text:$('v8Report').value});
  window.openLab=()=>tool('Laboratory finder','Enter a product, IS number or test. SmartGuide prepares a scope-aware laboratory lookup.','<div class="sg-v9-form"><label>Product <input id="v8LabProduct" placeholder="Example: keyboard"></label><label>IS number <input id="v8LabStd" placeholder="Example: IS/IEC 62368 : Part 1 (2023)"></label><label>Required test / parameter <input id="v8LabTest" placeholder="Optional test requirement"></label><button class="sg-v9-run" onclick="runLab()">🧪 Find suitable laboratories</button></div><div id="v8Out"></div>');
  window.runLab=async()=>{loading();try{const q=new URLSearchParams({product:$('v8LabProduct').value,standard:$('v8LabStd').value,test:$('v8LabTest').value,limit:'12'});const d=await api('/v5/lab-match?'+q);result(d);if($('v8Out'))$('v8Out').insertAdjacentHTML('beforeend','<div class="sg-v9-action"><b>Official source</b><p>Verify the current testing scope before sending a sample.</p><a target="_blank" rel="noopener" href="https://lims.bis.gov.in/home/search_is_number/">Open BIS LIMS →</a></div>')}catch(e){fail(e)}};
  window.openAmendment=()=>tool('QCO / amendment impact','Paste the amendment or QCO information to screen likely product impact areas.','<div class="sg-v9-form"><label>Standard / IS <input id="v8AmStd" placeholder="IS number"></label><label>Product <input id="v8AmProduct" placeholder="Product name"></label><label>Amendment / QCO text<textarea id="v8AmText" placeholder="Paste the relevant text or summary…"></textarea></label><button class="sg-v9-run" onclick="runAmendment()">📋 Screen impact</button></div><div id="v8Out"></div>');
  window.runAmendment=()=>post('/v5/amendment-impact',{standard:$('v8AmStd').value,product:$('v8AmProduct').value,amendment:$('v8AmText').value});
  window.openSTL=()=>tool('3D CAD / STL scanner','Upload an STL file to inspect its geometry and optional dimension limits.','<div class="sg-v9-form"><label>STL file<input id="v8STL" type="file" accept=".stl"></label><label>Max X dimension<input id="v8X" type="number" step="any" placeholder="Optional"></label><label>Max Y dimension<input id="v8Y" type="number" step="any" placeholder="Optional"></label><label>Max Z dimension<input id="v8Z" type="number" step="any" placeholder="Optional"></label><button class="sg-v9-run" onclick="runSTL()">🧊 Scan STL</button></div><div id="v8Out"></div>');
  window.runSTL=async()=>{loading();try{const f=$('v8STL').files[0];if(!f)return fail(new Error('Please select an STL file.'));const fd=new FormData();fd.append('file',f);[['x','v8X'],['y','v8Y'],['z','v8Z']].forEach(([a,id])=>{if($(id).value)fd.append('max_'+a,$(id).value)});result(await api('/v5/stl-scan',{method:'POST',body:fd}));}catch(e){fail(e)}};
  window.openLabel=()=>tool('Label / packaging checker','Paste the visible label text and SmartGuide will screen key marking fields.','<div class="sg-v9-form"><label>Label / packaging text<textarea id="v8Label" placeholder="Paste label text here…"></textarea></label><button class="sg-v9-run" onclick="runLabel()">🏷️ Check label</button></div><div id="v8Out"></div>');
  window.runLabel=()=>post('/v5/label-check',{text:$('v8Label').value});
  window.openProcurement=()=>tool('Procurement intelligence','Screen a product, raw material and optional HS code before procurement.','<div class="sg-v9-form"><label>Product <input id="v8Proc" placeholder="Product name"></label><label>HS code <input id="v8HS" placeholder="4–8 digits, optional"></label><label>Raw material / component <input id="v8Raw" placeholder="Optional"></label><button class="sg-v9-run" onclick="runProcurement()">🛒 Screen procurement</button></div><div id="v8Out"></div>');
  window.runProcurement=()=>post('/v5/procurement',{product:$('v8Proc').value,hs_code:$('v8HS').value,raw_material:$('v8Raw').value});
  window.openIssue=()=>tool('Issue / counterfeit complaint draft','Create a structured draft you can review before using an official BIS complaint channel.','<div class="sg-v9-form"><label>Product <input id="v8IssueProduct" placeholder="Optional"></label><label>Issue description<textarea id="v8Issue" placeholder="Describe the suspected marking problem, quality issue or safety concern…"></textarea></label><button class="sg-v9-run" onclick="runIssue()">⚠️ Create case draft</button></div><div id="v8Out"></div>');
  window.runIssue=()=>post('/v5/issue-report',{product:$('v8IssueProduct').value,issue:$('v8Issue').value});

  window.runV8SelfTest=async()=>{const el=$('v8SelfTest');if(!el)return;el.innerHTML='<div class="sg-v9-loading"><span class="sg-v9-spinner"></span><div><b>Checking SmartGuide…</b><small>Running the available feature checks.</small></div></div>';try{const d=await api('/v5/self-test');const tests=d.tests||d.features||[];const passed=tests.filter(x=>x.ok===true||String(x.status||'').toUpperCase().includes('PASS')).length;el.innerHTML=`<div class="sg-v9-health-result"><div class="sg-v9-health-summary"><span class="sg-v9-health-icon">${d.ok?'✓':'!'}</span><div><b>${d.ok?'System check passed':'Some checks need attention'}</b><small>${passed} of ${tests.length} checks passed</small></div></div><div class="sg-v9-checks">${tests.map(x=>`<div><span>${x.ok?'✓':'!'}</span><b>${esc(label(x.name||x.feature||'Check'))}</b><small>${x.ok?'Ready':'Needs attention'}</small></div>`).join('')}</div><details class="sg-v9-technical"><summary>Technical details</summary><pre>${esc(pretty(d))}</pre></details></div>`;}catch(e){el.innerHTML=`<div class="sg-v9-error"><b>System check unavailable</b><p>${esc(e.message)}</p></div>`}};

  window.filterV9Features=(q)=>{q=String(q||'').toLowerCase();document.querySelectorAll('.sg-v9-feature').forEach(c=>{c.style.display=(!q||c.innerText.toLowerCase().includes(q))?'flex':'none'});updateCount();};
  window.filterV9Category=(cat,btn)=>{document.querySelectorAll('.sg-v9-tabs button').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.querySelectorAll('.sg-v9-feature').forEach(c=>{c.style.display=(cat==='All'||c.dataset.category===cat)?'flex':'none'});$('v9Search').value='';updateCount();};
  function updateCount(){const n=[...document.querySelectorAll('.sg-v9-feature')].filter(x=>x.style.display!=='none').length;if($('v9FeatureCount'))$('v9FeatureCount').textContent=n;}
  function init(){page();}
  window.loadV8Status=()=>{};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();