/* BIS SmartGuide Advanced Features — rebuilt workflow console v8.2. */
(() => {
  const API = (typeof window.getSmartGuideApiHost === 'function')
    ? window.getSmartGuideApiHost()
    : ((location.hostname === 'localhost' || location.hostname === '127.0.0.1')
      ? (location.port === '5000' ? '' : 'http://127.0.0.1:5000')
      : (location.protocol === 'file:' ? 'http://127.0.0.1:5000' : (location.origin && !location.origin.includes('github.io') ? location.origin : 'https://sih26107-bis-smartguide-api.onrender.com')));
  const $=id=>document.getElementById(id);
  const esc=x=>String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const pretty=x=>{try{return JSON.stringify(x,null,2)}catch{return String(x)}};
  async function api(path,opt={}){
    const base = (typeof window.getSmartGuideApiHost === 'function') ? window.getSmartGuideApiHost() : API;
    const url = base + path;
    try {
      const r = await fetch(url, opt);
      let d = {}; try { d = await r.json(); } catch {}
      if (!r.ok) throw Error(d.error || d.message || `Request failed (${r.status})`);
      return d;
    } catch (err) {
      if (base.includes('127.0.0.1') || base.includes('localhost') || base === '') {
        const fbUrl = 'https://sih26107-bis-smartguide-api.onrender.com' + path;
        try {
          const r2 = await fetch(fbUrl, opt);
          let d2 = {}; try { d2 = await r2.json(); } catch {}
          if (!r2.ok) throw Error(d2.error || d2.message || `Remote request failed (${r2.status})`);
          return d2;
        } catch (fbErr) {}
      }
      throw err;
    }
  }
  function card(icon,title,desc,fn){return `<button class="sg-v8-card sg-v8-feature" onclick="${fn}()" type="button"><span class="sg-v8-icon">${icon}</span><h3>${title}</h3><p>${desc}</p><span class="sg-v8-open">Open workflow →</span></button>`}
  function page(){
    if($('v8'))return;
    const m=document.querySelector('.content');
    if(!m)return;
    const s=document.createElement('section');
    s.id='v8'; s.className='page';
    s.innerHTML=`
      <div class="section-head"><div><h2>Advanced Features</h2><p>Source-grounded workflows for product intelligence, verification, testing, laboratories, engineering and reporting.</p></div><span class="sg-v8-badge">ADVANCED V8.2</span></div>
      <div class="sg-v8-kpis"><div class="sg-v8-kpi"><b id="v8Active">—</b><span class="sg-v8-muted">Functional workflows</span></div><div class="sg-v8-kpi"><b>V4 + V8</b><span class="sg-v8-muted">Evidence + intelligence</span></div><div class="sg-v8-kpi"><b>6</b><span class="sg-v8-muted">Official BIS sources</span></div><div class="sg-v8-kpi"><b>0</b><span class="sg-v8-muted">Automated certificates</span></div></div>
      <div class="sg-v8-grid">
        ${card('🔎','Product AI','Rank applicable standards from a product description','openProduct')}
        ${card('✓','ISI / CM-L','Screen marks and licence references','openMark')}
        ${card('📄','Test Reports','Extract measurements without inventing limits','openTest')}
        ${card('🧪','Lab Matcher','Prepare exact IS/test scope lookup','openLab')}
        ${card('📋','QCO + Amendment','Screen likely impact areas','openAmendment')}
        ${card('🧊','3D CAD / STL','Scan ASCII and binary STL geometry','openSTL')}
        ${card('🏷️','Label / Packaging','Screen key marking fields','openLabel')}
        ${card('🛒','Procurement AI','Screen product, raw material and HS format','openProcurement')}
        ${card('⚠️','Issue Report','Create a structured complaint draft','openIssue')}
      </div>
      <div class="sg-v8-section"><div class="section-head"><div><h2>Live feature status</h2><p class="sg-v8-muted">Functional means the workflow is implemented. Official BIS decisions remain source-bound.</p></div><button class="btn ghost" type="button" onclick="runV8SelfTest()">Run self-test</button></div><div id="v8Status" class="sg-v8-grid"><div class="sg-v8-card">Loading…</div></div><div id="v8SelfTest" class="sg-v8-result"></div></div>
      <div id="v8Tool" class="sg-v8-output"></div>
      <footer class="sg-v8-context">BIS SmartGuide • SIH 2026 • Problem Statement 26107 • Prototype intelligence layer — verify final requirements with official BIS sources.</footer>`;
    m.appendChild(s);
  }
  function tool(title,body){const el=$('v8Tool');if(!el)return;el.innerHTML=`<div class="sg-v8-card sg-v8-tool"><div class="section-head"><div><h2>${title}</h2></div><button class="btn" type="button" onclick="$('v8Tool').innerHTML=''">Close</button></div>${body}</div>`;el.scrollIntoView({behavior:'smooth',block:'start'})}
  function output(d){const out=$('v8Out');if(out)out.innerHTML=`<div class="sg-v8-result-head"><b>Workflow result</b><button class="btn ghost" type="button" onclick="navigator.clipboard?.writeText(this.closest('.sg-v8-result').querySelector('pre').textContent)">Copy</button></div><pre>${esc(pretty(d))}</pre>`}
  function loading(){if($('v8Out'))$('v8Out').innerHTML='<div class="sg-v8-loading">Running SmartGuide analysis…</div>'}
  function fail(e){output({error:e?.message||String(e),hint:'Check backend health and retry.'})}
  window.openProduct=()=>tool('Product → ranked standards',`<div class="sg-v8-form"><textarea id="v8Product" class="full" placeholder="Example: 1200W stainless-steel electric kettle for household use with automatic shutoff"></textarea><div><button class="btn primary" onclick="runProduct()">Rank standards</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runProduct=async()=>{loading();try{output(await api('/v5/product-intelligence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:$('v8Product').value})}))}catch(e){fail(e)}};
  window.openMark=()=>tool('ISI + CM/L verification',`<div class="sg-v8-form"><textarea id="v8MarkText" class="full" placeholder="Paste label/licence text"></textarea><input id="v8Licence" placeholder="Licence / CM-L number (optional)"><div><button class="btn primary" onclick="runMark()">Screen mark</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runMark=async()=>{loading();try{output(await api('/v5/verify-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('v8MarkText').value,licence:$('v8Licence').value})}))}catch(e){fail(e)}};
  window.openTest=()=>tool('Test-report intelligence',`<div class="sg-v8-form"><input id="v8Std" placeholder="Applicable IS number (optional)"><textarea id="v8Report" class="full" placeholder="Voltage: 230 V\nPower: 1200 W\nLeakage current: 0.4 mA"></textarea><div><button class="btn primary" onclick="runTest()">Parse report</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runTest=async()=>{loading();try{output(await api('/v5/test-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({standard:$('v8Std').value,text:$('v8Report').value})}))}catch(e){fail(e)}};
  window.openLab=()=>tool('Intelligent laboratory workflow',`<div class="sg-v8-form"><input id="v8LabProduct" placeholder="Product"><input id="v8LabStd" placeholder="IS number"><input id="v8LabTest" class="full" placeholder="Required test / parameter"><div><button class="btn primary" onclick="runLab()">Prepare lab lookup</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runLab=async()=>{loading();try{const q=new URLSearchParams({product:$('v8LabProduct').value,standard:$('v8LabStd').value,test:$('v8LabTest').value});const d=await api('/v5/lab-match?'+q);output(d);$('v8Out').insertAdjacentHTML('afterbegin','<div class="sg-v8-map"><b>Official BIS LIMS lookup</b><p>Use the returned IS number and test scope in the official BIS LIMS directory.</p><a class="btn ghost" target="_blank" rel="noopener" href="https://lims.bis.gov.in/home/search_is_number/">Open BIS LIMS →</a></div>')}catch(e){fail(e)}};
  window.openAmendment=()=>tool('QCO / amendment impact',`<div class="sg-v8-form"><input id="v8AmStd" placeholder="Standard / IS"><input id="v8AmProduct" placeholder="Product"><textarea id="v8AmText" class="full" placeholder="Paste amendment or QCO text/summary"></textarea><div><button class="btn primary" onclick="runAmendment()">Analyze impact</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runAmendment=async()=>{loading();try{output(await api('/v5/amendment-impact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({standard:$('v8AmStd').value,product:$('v8AmProduct').value,amendment:$('v8AmText').value})}))}catch(e){fail(e)}};
  window.openSTL=()=>tool('3D CAD / STL engineering scanner',`<div class="sg-v8-form"><input id="v8STL" type="file" accept=".stl" class="full"><input id="v8X" type="number" step="any" placeholder="Max X dimension (optional)"><input id="v8Y" type="number" step="any" placeholder="Max Y dimension (optional)"><input id="v8Z" type="number" step="any" placeholder="Max Z dimension (optional)"><div><button class="btn primary" onclick="runSTL()">Scan STL</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runSTL=async()=>{loading();try{const f=$('v8STL').files[0];if(!f)return output({error:'Select an STL file'});const fd=new FormData();fd.append('file',f);[['x','v8X'],['y','v8Y'],['z','v8Z']].forEach(([a,id])=>{if($(id).value)fd.append('max_'+a,$(id).value)});output(await api('/v5/stl-scan',{method:'POST',body:fd}))}catch(e){fail(e)}};
  window.openLabel=()=>tool('Label / packaging screening',`<div class="sg-v8-form"><textarea id="v8Label" class="full" placeholder="Paste label/package text"></textarea><div><button class="btn primary" onclick="runLabel()">Check label</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runLabel=async()=>{loading();try{output(await api('/v5/label-check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('v8Label').value})}))}catch(e){fail(e)}};
  window.openProcurement=()=>tool('Procurement intelligence',`<div class="sg-v8-form"><input id="v8Proc" placeholder="Product"><input id="v8HS" placeholder="HS code (4–8 digits, optional)"><input id="v8Raw" class="full" placeholder="Raw material / component"><div><button class="btn primary" onclick="runProcurement()">Screen procurement</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runProcurement=async()=>{loading();try{output(await api('/v5/procurement',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:$('v8Proc').value,hs_code:$('v8HS').value,raw_material:$('v8Raw').value})}))}catch(e){fail(e)}};
  window.openIssue=()=>tool('Issue / counterfeit report draft',`<div class="sg-v8-form"><input id="v8IssueProduct" placeholder="Product (optional)"><textarea id="v8Issue" class="full" placeholder="Describe the suspected issue, marking problem or safety concern"></textarea><div><button class="btn primary" onclick="runIssue()">Create case draft</button></div></div><div id="v8Out" class="sg-v8-result"></div>`);
  window.runIssue=async()=>{loading();try{output(await api('/v5/issue-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:$('v8IssueProduct').value,issue:$('v8Issue').value})}))}catch(e){fail(e)}};

  // Keep developer JSON out of the user-facing console. The backend still returns
  // the complete self-test payload; the UI now renders a concise health summary.
  window.runV8SelfTest=async()=>{
    const el=$('v8SelfTest');
    if(el)el.innerHTML='<div class="sg-v8-loading">Running backend self-test…</div>';
    try{
      const d=await api('/v5/self-test');
      const tests=Array.isArray(d.tests)?d.tests:[];
      const passed=tests.filter(t=>t && t.ok).length;
      const failed=tests.length-passed;
      const status=d.ok!==false && failed===0;
      if(el){
        el.innerHTML=`
          <div class="sg-v8-selftest ${status?'is-good':'is-bad'}">
            <div class="sg-v8-selftest-head">
              <div>
                <span class="sg-v8-badge">${status?'SELF-TEST PASSED':'SELF-TEST NEEDS ATTENTION'}</span>
                <h3>${status?'All backend checks are healthy':'Some backend checks need attention'}</h3>
                <p>${passed} of ${tests.length} checks passed${failed?` • ${failed} failed`:''}.</p>
              </div>
              <div class="sg-v8-selftest-score">${passed}/${tests.length}</div>
            </div>
            <div class="sg-v8-selftest-list">
              ${tests.map(t=>`<div class="sg-v8-selftest-row"><span class="sg-v8-test-dot ${t.ok?'ok':'bad'}">${t.ok?'✓':'!'}</span><span>${esc(t.name||'Backend check')}</span><b>${t.ok?'PASS':'CHECK'}</b></div>`).join('')}
            </div>
            <div class="sg-v8-selftest-meta">Backend health check completed${d.generated_at?` • ${esc(new Date(d.generated_at).toLocaleString())}`:''}</div>
          </div>`;
      }
    }catch(e){
      if(el)el.innerHTML=`<div class="sg-v8-selftest is-bad"><span class="sg-v8-badge">SELF-TEST UNAVAILABLE</span><h3>Could not reach the backend</h3><p>${esc(e.message||'Backend request failed')}</p></div>`;
    }
  };
  async function loadStatus(){try{const d=await api('/v5/feature-status');const a=d.features||[];if($('v8Active'))$('v8Active').textContent=a.filter(x=>String(x.status).startsWith('FUNCTIONAL')).length;if($('v8Status'))$('v8Status').innerHTML=a.map(x=>`<div class="sg-v8-card sg-v8-status-card"><span class="sg-v8-badge">${esc(x.status)}</span><h3>${esc(x.feature)}</h3></div>`).join('')}catch(e){if($('v8Status'))$('v8Status').innerHTML='<div class="sg-v8-card sg-v8-warn"><b>Backend unavailable</b><p>'+esc(e.message)+'</p></div>'}}
  window.loadV8Status=loadStatus;
  function init(){page();loadStatus();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();