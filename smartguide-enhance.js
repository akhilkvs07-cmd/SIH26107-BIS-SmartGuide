/* BIS SmartGuide — V6 integration layer
   Keeps the existing production UI and exposes the Advanced Intelligence workspace.
*/
(() => {
  const API = 'https://sih26107-bis-smartguide-api.onrender.com';
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

  async function api(path, opt = {}) {
    const r = await fetch(API + path, opt);
    let d = {};
    try { d = await r.json(); } catch {}
    if (!r.ok) throw Error(d.error || d.message || 'Backend request failed');
    return d;
  }

  function addNav() {
    const nav = document.querySelector('.nav');
    if (!nav) return;
    if (!$('passportNav')) {
      const b = document.createElement('button');
      b.id = 'passportNav';
      b.innerHTML = '<span>◈</span><span>Compliance Passport</span>';
      b.onclick = () => { if (typeof page === 'function') page('passport', b, 'Compliance Passport'); loadPassportHistory(); };
      nav.appendChild(b);
    }
    const advanced = Array.from(nav.querySelectorAll('button')).find(b => /advanced\s+intelligence/i.test(b.textContent || ''));
    if (advanced && !advanced.__v6bound) {
      advanced.__v6bound = true;
      advanced.onclick = () => {
        addAdvancedPage();
        if (typeof page === 'function') page('advanced', advanced, 'Advanced Intelligence');
        else showAdvancedDirect();
      };
    }
  }

  function addPage() {
    if ($('passport')) return;
    const main = document.querySelector('.content');
    if (!main) return;
    const section = document.createElement('section');
    section.id = 'passport';
    section.className = 'page';
    section.innerHTML = `
      <div class="section-head"><div><h2>Compliance Passport</h2><p>Persistent assessment history, evidence hash and corrective actions.</p></div><span class="status-badge success">● V4 Evidence Layer</span></div>
      <div class="grid4">
        <div class="card stat"><div class="icon">✓</div><strong id="vpCount">—</strong><span>Saved assessments</span></div>
        <div class="card stat"><div class="icon">◈</div><strong id="vpLatest">—</strong><span>Latest score</span></div>
        <div class="card stat"><div class="icon">!</div><strong id="vpRisk">—</strong><span>Latest risk</span></div>
        <div class="card stat"><div class="icon">#</div><strong id="vpEvidence">—</strong><span>Evidence quality</span></div>
      </div>
      <div id="vpOut" class="result"><div class="card loading">Loading saved assessments…</div></div>`;
    main.appendChild(section);
  }

  function addAdvancedPage() {
    if ($('advanced')) return;
    const main = document.querySelector('.content');
    if (!main) return;
    const section = document.createElement('section');
    section.id = 'advanced';
    section.className = 'page';
    section.innerHTML = `
      <div class="section-head"><div><h2>Advanced Intelligence</h2><p>Engineering, verification, laboratory and regulatory intelligence tools.</p></div><span class="status-badge success">● V6 Intelligence Layer</span></div>
      <div class="grid4">
        <div class="card stat"><div class="icon">🔍</div><strong>Product AI</strong><span>Product → ranked BIS standards</span></div>
        <div class="card stat"><div class="icon">✓</div><strong>ISI / CM-L</strong><span>Mark and licence screening</span></div>
        <div class="card stat"><div class="icon">📄</div><strong>Test Reports</strong><span>Extract reported measurements</span></div>
        <div class="card stat"><div class="icon">🧪</div><strong>Lab Matcher</strong><span>Match standard/test to BIS lab scope</span></div>
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card">
          <h3>📐 3D CAD / STL Scanner</h3>
          <p class="muted tiny">Upload an STL model for dimensional engineering screening and candidate-standard guidance.</p>
          <div class="drop" id="stlDrop"><strong>Drop an .STL file here</strong><span class="muted tiny">or choose a model from your computer</span><div style="margin-top:14px"><input id="stlFile" type="file" accept=".stl,model/stl" class="field"></div></div>
          <div class="toolbar" style="margin-top:12px"><button class="btn primary" id="stlScanBtn">Scan STL</button><span class="status-badge warn">Engineering screening only</span></div>
          <div id="stlOut" class="result"></div>
        </div>
        <div class="card">
          <h3>🪪 ISI / CM-L Verification</h3>
          <p class="muted tiny">Detect mark/licence identifiers before official BIS verification.</p>
          <textarea id="markText" class="field" rows="5" placeholder="Paste label text, ISI/CM-L details, manufacturer information…"></textarea>
          <div class="toolbar" style="margin-top:10px"><button class="btn primary" id="markBtn">Screen mark</button><a class="btn ghost" href="https://www.bis.gov.in/" target="_blank" rel="noopener">Official BIS ↗</a></div>
          <div id="markOut" class="result"></div>
        </div>
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>📄 Test Report Intelligence</h3><p class="muted tiny">Paste a report excerpt to extract measurement/value/unit pairs without inventing pass/fail limits.</p><textarea id="testText" class="field" rows="4" placeholder="Example: insulation resistance: 2.5 MΩ"></textarea><input id="testStandard" class="field" style="margin-top:8px" placeholder="Optional IS number"><button class="btn primary" id="testBtn" style="margin-top:10px">Analyze report</button><div id="testOut" class="result"></div></div>
        <div class="card"><h3>🧪 Intelligent Laboratory Matcher</h3><p class="muted tiny">Find candidate standards first, then verify exact test-facility scope in BIS LIMS/laboratory directory.</p><input id="labProduct" class="field" placeholder="Product or test"><input id="labStandard" class="field" style="margin-top:8px" placeholder="IS number (optional)"><button class="btn primary" id="labBtn" style="margin-top:10px">Match laboratory</button><div id="labOut" class="result"></div></div>
      </div>
      <div class="grid3" style="margin-top:16px">
        <div class="card"><h3>📰 Amendment Impact</h3><p class="muted tiny">Screen how a verified amendment could affect requirements, testing, marking and QCO scope.</p><input id="amendmentText" class="field" placeholder="Amendment / notification text"><input id="amendmentProduct" class="field" style="margin-top:8px" placeholder="Product or IS number"><button class="btn primary" id="amendmentBtn" style="margin-top:10px">Assess impact</button><div id="amendmentOut" class="result"></div></div>
        <div class="card"><h3>🏷️ Label / Packaging Check</h3><p class="muted tiny">Screen label fields such as product, manufacturer, model, standard and ratings.</p><textarea id="labelText" class="field" rows="3" placeholder="Paste product label text"></textarea><button class="btn primary" id="labelBtn" style="margin-top:10px">Check label</button><div id="labelOut" class="result"></div></div>
        <div class="card"><h3>📦 Procurement Intelligence</h3><p class="muted tiny">Create a procurement review checklist around standard, QCO, licence scope, test evidence and supplier documents.</p><input id="procProduct" class="field" placeholder="Product"><input id="procHs" class="field" style="margin-top:8px" placeholder="HS code (optional)"><input id="procRaw" class="field" style="margin-top:8px" placeholder="Raw material (optional)"><button class="btn primary" id="procBtn" style="margin-top:10px">Review procurement</button><div id="procOut" class="result"></div></div>
      </div>`;
    main.appendChild(section);
    bindAdvancedActions();
  }

  function showAdvancedDirect(){ addAdvancedPage(); document.querySelectorAll('.page').forEach(p=>p.classList.remove('active')); $('advanced').classList.add('active'); document.querySelectorAll('.nav button').forEach(b=>b.classList.remove('active')); const b=Array.from(document.querySelectorAll('.nav button')).find(x=>/advanced\s+intelligence/i.test(x.textContent||'')); if(b)b.classList.add('active'); }

  function resultBox(target, title, obj) {
    const el=$(target); if(!el)return;
    const pretty=esc(JSON.stringify(obj,null,2));
    el.innerHTML=`<div class="evidence"><div class="evidence-head"><b>${esc(title)}</b><span class="tag green">RESULT</span></div><pre style="white-space:pre-wrap;font-size:11px;line-height:1.5;margin:10px 0 0">${pretty}</pre></div>`;
  }

  function bindAdvancedActions(){
    if($('stlScanBtn') && !$('stlScanBtn').__bound){ $('stlScanBtn').__bound=true; $('stlScanBtn').onclick=scanSTL; }
    if($('markBtn') && !$('markBtn').__bound){ $('markBtn').__bound=true; $('markBtn').onclick=screenMark; }
    if($('testBtn') && !$('testBtn').__bound){ $('testBtn').__bound=true; $('testBtn').onclick=analyzeTest; }
    if($('labBtn') && !$('labBtn').__bound){ $('labBtn').__bound=true; $('labBtn').onclick=matchLab; }
    if($('amendmentBtn') && !$('amendmentBtn').__bound){ $('amendmentBtn').__bound=true; $('amendmentBtn').onclick=impactAmendment; }
    if($('labelBtn') && !$('labelBtn').__bound){ $('labelBtn').__bound=true; $('labelBtn').onclick=checkLabel; }
    if($('procBtn') && !$('procBtn').__bound){ $('procBtn').__bound=true; $('procBtn').onclick=reviewProcurement; }
  }

  async function scanSTL(){
    const f=$('stlFile')?.files?.[0]; if(!f){ $('stlOut').innerHTML='<div class="notice">Choose an .STL file first.</div>'; return; }
    if(!/\.stl$/i.test(f.name)){ $('stlOut').innerHTML='<div class="dangerbox">Only STL files are supported.</div>'; return; }
    $('stlOut').innerHTML='<div class="card loading">Parsing STL geometry…</div>';
    try{ const fd=new FormData(); fd.append('file',f); const d=await api('/v5/stl-scan',{method:'POST',body:fd});
      const dims=d.bounding_box||d.bounding_dimensions||null; const checks=d.dimensional_checks||[];
      $('stlOut').innerHTML=`<div class="evidence"><div class="evidence-head"><b>${esc(d.filename||f.name)}</b><span class="tag amber">${esc(d.status||'ENGINEERING_SCREEN')}</span></div><p class="tiny muted">Triangles: ${esc(d.triangle_count??d.vertex_count??'—')} • SHA-256: ${esc(d.sha256||'not supplied')}</p>${dims?`<div class="report-grid"><div class="report-stat"><b>${Number(dims.x||0).toFixed(3)}</b>X</div><div class="report-stat"><b>${Number(dims.y||0).toFixed(3)}</b>Y</div><div class="report-stat"><b>${Number(dims.z||0).toFixed(3)}</b>Z</div><div class="report-stat"><b>${esc(checks.length||'—')}</b>Checks</div></div>`:''}${checks.length?checks.map(c=>`<div class="checkrow"><span>${c.pass?'✓':'!'}</span><span><b>${esc(c.axis||'dimension')}</b> — measured ${esc(c.measured)} / limit ${esc(c.limit)} ${c.pass?'PASS':'REVIEW'}</span></div>`).join(''):''}<div class="notice" style="margin-top:12px">${esc(d.notice||'This is an engineering pre-check, not a BIS conformity determination.')}</div></div>`;
    }catch(e){ $('stlOut').innerHTML=`<div class="dangerbox"><b>STL scan failed</b><p>${esc(e.message)}</p></div>`; }
  }
  async function screenMark(){ const text=$('markText')?.value.trim(); if(!text){$('markOut').innerHTML='<div class="notice">Paste label/mark information first.</div>';return;} $('markOut').innerHTML='<div class="card loading">Screening mark details…</div>'; try{const d=await api('/v5/verify-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});resultBox('markOut','ISI / CM-L screening',d);}catch(e){resultBox('markOut','Unavailable',{error:e.message});} }
  async function analyzeTest(){ const text=$('testText')?.value.trim(); if(!text){$('testOut').innerHTML='<div class="notice">Paste a report excerpt first.</div>';return;} try{const d=await api('/v5/test-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,standard:$('testStandard')?.value||''})});resultBox('testOut','Test report extraction',d);}catch(e){resultBox('testOut','Unavailable',{error:e.message});} }
  async function matchLab(){ const product=$('labProduct')?.value.trim(), standard=$('labStandard')?.value.trim(); if(!product&&!standard){$('labOut').innerHTML='<div class="notice">Enter a product, test or IS number.</div>';return;} try{const d=await api('/v5/lab-match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product,standard,test:product})});resultBox('labOut','Laboratory matching',d);}catch(e){resultBox('labOut','Unavailable',{error:e.message});} }
  async function impactAmendment(){ const amendment=$('amendmentText')?.value.trim(), product=$('amendmentProduct')?.value.trim(); if(!amendment&&!product){$('amendmentOut').innerHTML='<div class="notice">Enter an amendment or product/IS number.</div>';return;} try{const d=await api('/v5/amendment-impact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amendment,product,standard:product})});resultBox('amendmentOut','Amendment impact screening',d);}catch(e){resultBox('amendmentOut','Unavailable',{error:e.message});} }
  async function checkLabel(){ const text=$('labelText')?.value.trim(); if(!text){$('labelOut').innerHTML='<div class="notice">Paste label text first.</div>';return;} try{const d=await api('/v5/label-check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});resultBox('labelOut','Label screening',d);}catch(e){resultBox('labelOut','Unavailable',{error:e.message});} }
  async function reviewProcurement(){ const product=$('procProduct')?.value.trim(); if(!product){$('procOut').innerHTML='<div class="notice">Enter a product first.</div>';return;} try{const d=await api('/v5/procurement',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product,hs_code:$('procHs')?.value||'',raw_material:$('procRaw')?.value||''})});resultBox('procOut','Procurement review',d);}catch(e){resultBox('procOut','Unavailable',{error:e.message});} }

  async function loadPassportHistory() {
    if (!$('vpOut')) return;
    $('vpOut').innerHTML = '<div class="card loading">Loading saved assessments…</div>';
    try {
      const d = await api('/v4/assessments'); const list = d.assessments || [];
      $('vpCount').textContent = list.length;
      if (list.length) { const latest=list[0]; $('vpLatest').textContent=(latest.score??'—')+'%'; $('vpRisk').textContent=latest.risk||'—'; $('vpEvidence').textContent=latest.evidence_quality||'—'; }
      else $('vpLatest').textContent=$('vpRisk').textContent=$('vpEvidence').textContent='—';
      $('vpOut').innerHTML=list.length?list.map(passportCard).join(''):'<div class="card empty">No saved V4 assessments yet. Run a Compliance Center assessment first.</div>';
    } catch(e){ $('vpOut').innerHTML=`<div class="card dangerbox"><b>V4 evidence layer unavailable</b><p>${esc(e.message)}</p></div>`; }
  }
  function passportCard(a){ const risk=String(a.risk||'').toUpperCase(), cls=risk==='LOW'?'success':risk==='HIGH'?'danger':'warn'; return `<div class="card" style="margin-bottom:12px"><div class="result-top"><div><span class="stdno">${esc(a.standard_number||'Standard not recorded')}</span><h3 style="margin:5px 0">${esc(a.product||'Assessment')}</h3></div><div style="text-align:right"><div class="score">${esc(a.score??'—')}%</div><span class="status-badge ${cls}">${esc(risk||'UNKNOWN')}</span></div></div><p class="muted tiny">${esc(a.status||'')} • ${esc(a.created_at||'')}</p><button class="btn primary" onclick="window.smartGuideOpenPassport('${esc(a.id||a.assessment_id||'')}')">Open passport</button></div>`; }
  async function openPassport(id){ if(!id)return; if(typeof page==='function')page('passport',$('passportNav'),'Compliance Passport'); try{const d=await api('/v4/passport/'+encodeURIComponent(id)); const actions=d.corrective_actions||[]; $('vpOut').innerHTML=`<div class="card"><div class="result-top"><div><span class="tag">COMPLIANCE PASSPORT</span><h2>${esc(d.product||'Assessment')}</h2><p class="muted">Assessment ${esc(d.assessment_id||id)}</p></div><div style="text-align:right"><div class="score">${esc(d.score??'—')}%</div><span class="status-badge ${String(d.risk).toUpperCase()==='LOW'?'success':String(d.risk).toUpperCase()==='HIGH'?'danger':'warn'}">${esc(d.risk||'UNKNOWN')} RISK</span></div></div><div class="report-grid"><div class="report-stat"><b>${esc(d.score??'—')}%</b>Readiness</div><div class="report-stat"><b>${esc(d.status||'—')}</b>Status</div><div class="report-stat"><b>${esc(d.evidence_quality||'—')}</b>Evidence</div><div class="report-stat"><b>${esc(d.standard_number||'—')}</b>Standard</div></div><div class="evidence"><div class="evidence-head"><b>Evidence integrity</b><span class="tag green">HASHED</span></div><p class="tiny muted">Evidence hash: <code>${esc(d.evidence_hash||'—')}</code></p><p class="tiny muted">Created: ${esc(d.created_at||'—')}</p></div><h3>Corrective actions</h3>${actions.length?actions.map(x=>`<div class="checkrow"><span>⚠</span><span><b>${esc(x.priority||'ACTION')}</b> — ${esc(x.action||x)}</span></div>`).join(''):'<div class="successbox">No corrective actions recorded.</div>'}<div class="notice" style="margin-top:14px"><b>Trust boundary:</b> This passport is an auditable prototype assessment. It is not a BIS certificate or proof of active licence status.</div></div>`;}catch(e){$('vpOut').innerHTML=`<div class="card dangerbox"><b>Could not open passport</b><p>${esc(e.message)}</p></div>`;} }
  window.smartGuideOpenPassport=openPassport;

  async function saveV4Assessment(product,checks){try{ return await api('/v4/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product,checks,evidence:{interface:'BIS SmartGuide existing UI',user_confirmed_checks:Object.values(checks).filter(Boolean).length}})});}catch(e){return{error:e.message};}}
  function addV4ResultButton(d){const out=$('compOut');if(!out||!d||d.error)return;const box=document.createElement('div');box.className='card successbox';box.style.marginTop='12px';box.innerHTML=`<b>V4 Evidence Passport created</b><p>${esc(d.status||'Assessment saved')} • ${esc(d.score??'—')}% • ${esc(d.risk||'UNKNOWN')} risk • ${esc(d.evidence_quality||'—')} evidence</p><button class="btn primary" onclick="window.smartGuideOpenPassport('${esc(d.assessment_id)}')">Open Compliance Passport</button>`;out.prepend(box);}
  function patchCompliance(){if(typeof submitCompliance!=='function'||submitCompliance.__v5wrapped)return;const original=submitCompliance;const wrapped=async function(product){const checks={};document.querySelectorAll('#checklist input').forEach(x=>checks[x.dataset.req]=x.checked);const v4=await saveV4Assessment(product,checks);await original(product);if(!v4.error)addV4ResultButton(v4);};wrapped.__v5wrapped=true;window.submitCompliance=wrapped;}
  function patchDocument(){if(typeof doc!=='function'||doc.__v5wrapped)return;const original=doc;const wrapped=async function(){const f=$('file')?.files?.[0];if(!f)return original();try{const fd=new FormData();fd.append('file',f);const d=await api('/v4/document',{method:'POST',body:fd});$('docOut').innerHTML=`<div class="card"><span class="tag green">V4 EXTRACTION</span><h2>${esc(d.filename||f.name)}</h2><p class="muted">${esc(d.characters_extracted||0)} characters extracted</p><h3>Extracted fields</h3><pre style="white-space:pre-wrap">${esc(JSON.stringify(d.extracted_fields||{},null,2))}</pre><h3>Candidate standards</h3>${(d.candidate_standards||[]).map(s=>`<div class="evidence"><b>${esc(s.standard_number)}</b> — ${esc(s.title||s.product||'')}</div>`).join('')||'<p class="muted">No supported candidate found.</p>'}</div>`;}catch(_){return original();}};wrapped.__v5wrapped=true;window.doc=wrapped;}

  function init(){ addNav(); addPage(); patchCompliance(); patchDocument(); setTimeout(()=>{addNav();patchCompliance();patchDocument();},500); }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
