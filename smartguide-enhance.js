/* BIS SmartGuide — V5 integration layer
   Keeps the existing production UI and adds the V4 evidence/compliance workflow.
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
    if (!nav || $('passportNav')) return;
    const b = document.createElement('button');
    b.id = 'passportNav';
    b.innerHTML = '<span>◈</span><span>Compliance Passport</span>';
    b.onclick = () => { if (typeof page === 'function') page('passport', b, 'Compliance Passport'); loadPassportHistory(); };
    nav.appendChild(b);
  }

  function addPage() {
    if ($('passport')) return;
    const main = document.querySelector('.content');
    if (!main) return;
    const section = document.createElement('section');
    section.id = 'passport';
    section.className = 'page';
    section.innerHTML = `
      <div class="section-head">
        <div><h2>Compliance Passport</h2><p>Persistent assessment history, evidence hash and corrective actions.</p></div>
        <span class="status-badge success">● V4 Evidence Layer</span>
      </div>
      <div class="grid4">
        <div class="card stat"><div class="icon">✓</div><strong id="vpCount">—</strong><span>Saved assessments</span></div>
        <div class="card stat"><div class="icon">◈</div><strong id="vpLatest">—</strong><span>Latest score</span></div>
        <div class="card stat"><div class="icon">!</div><strong id="vpRisk">—</strong><span>Latest risk</span></div>
        <div class="card stat"><div class="icon">#</div><strong id="vpEvidence">—</strong><span>Evidence quality</span></div>
      </div>
      <div id="vpOut" class="result"><div class="card loading">Loading saved assessments…</div></div>
    `;
    main.appendChild(section);
  }

  function passportCard(a) {
    const risk = String(a.risk || '').toUpperCase();
    const cls = risk === 'LOW' ? 'success' : risk === 'HIGH' ? 'danger' : 'warn';
    return `<div class="card" style="margin-bottom:12px">
      <div class="result-top">
        <div><span class="stdno">${esc(a.standard_number || 'Standard not recorded')}</span><h3 style="margin:5px 0">${esc(a.product || 'Assessment')}</h3></div>
        <div style="text-align:right"><div class="score">${esc(a.score ?? '—')}%</div><span class="status-badge ${cls}">${esc(risk || 'UNKNOWN')}</span></div>
      </div>
      <p class="muted tiny">${esc(a.status || '')} • ${esc(a.created_at || '')}</p>
      <div class="toolbar">
        <button class="btn primary" onclick="window.smartGuideOpenPassport('${esc(a.id || a.assessment_id || '')}')">Open passport</button>
      </div>
    </div>`;
  }

  async function loadPassportHistory() {
    if (!$('vpOut')) return;
    $('vpOut').innerHTML = '<div class="card loading">Loading saved assessments…</div>';
    try {
      const d = await api('/v4/assessments');
      const list = d.assessments || [];
      $('vpCount').textContent = list.length;
      if (list.length) {
        const latest = list[0];
        $('vpLatest').textContent = (latest.score ?? '—') + '%';
        $('vpRisk').textContent = latest.risk || '—';
        $('vpEvidence').textContent = latest.evidence_quality || '—';
      } else {
        $('vpLatest').textContent = $('vpRisk').textContent = $('vpEvidence').textContent = '—';
      }
      $('vpOut').innerHTML = list.length ? list.map(passportCard).join('') : '<div class="card empty">No saved V4 assessments yet. Run a Compliance Center assessment first.</div>';
    } catch (e) {
      $('vpOut').innerHTML = `<div class="card dangerbox"><b>V4 evidence layer unavailable</b><p>${esc(e.message)}</p></div>`;
    }
  }

  async function openPassport(id) {
    if (!id) return;
    if (typeof page === 'function') page('passport', $('passportNav'), 'Compliance Passport');
    try {
      const d = await api('/v4/passport/' + encodeURIComponent(id));
      const actions = d.corrective_actions || [];
      $('vpOut').innerHTML = `<div class="card">
        <div class="result-top"><div><span class="tag">COMPLIANCE PASSPORT</span><h2>${esc(d.product || 'Assessment')}</h2><p class="muted">Assessment ${esc(d.assessment_id || id)}</p></div><div style="text-align:right"><div class="score">${esc(d.score ?? '—')}%</div><span class="status-badge ${String(d.risk).toUpperCase()==='LOW'?'success':String(d.risk).toUpperCase()==='HIGH'?'danger':'warn'}">${esc(d.risk || 'UNKNOWN')} RISK</span></div></div>
        <div class="report-grid">
          <div class="report-stat"><b>${esc(d.score ?? '—')}%</b>Readiness</div>
          <div class="report-stat"><b>${esc(d.status || '—')}</b>Status</div>
          <div class="report-stat"><b>${esc(d.evidence_quality || '—')}</b>Evidence</div>
          <div class="report-stat"><b>${esc(d.standard_number || '—')}</b>Standard</div>
        </div>
        <div class="evidence"><div class="evidence-head"><b>Evidence integrity</b><span class="tag green">HASHED</span></div><p class="tiny muted">Evidence hash: <code>${esc(d.evidence_hash || '—')}</code></p><p class="tiny muted">Created: ${esc(d.created_at || '—')}</p></div>
        <div class="section-head"><div><h3>Corrective actions</h3></div></div>
        ${actions.length ? actions.map(x => `<div class="checkrow"><span>⚠</span><span><b>${esc(x.priority || 'ACTION')}</b> — ${esc(x.action || x)}</span></div>`).join('') : '<div class="successbox">No corrective actions recorded.</div>'}
        <div class="notice" style="margin-top:14px"><b>Trust boundary:</b> This passport is an auditable prototype assessment. It is not a BIS certificate or proof of active licence status.</div>
      </div>`;
    } catch (e) {
      $('vpOut').innerHTML = `<div class="card dangerbox"><b>Could not open passport</b><p>${esc(e.message)}</p></div>`;
    }
  }

  async function saveV4Assessment(product, checks) {
    try {
      const d = await api('/v4/assess', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ product, checks, evidence: { interface: 'BIS SmartGuide existing UI', user_confirmed_checks: Object.values(checks).filter(Boolean).length } })
      });
      return d;
    } catch (e) {
      return { error: e.message };
    }
  }

  function addV4ResultButton(d) {
    const out = $('compOut');
    if (!out || !d || d.error) return;
    const id = d.assessment_id;
    const box = document.createElement('div');
    box.className = 'card successbox';
    box.style.marginTop = '12px';
    box.innerHTML = `<b>V4 Evidence Passport created</b><p>${esc(d.status || 'Assessment saved')} • ${esc(d.score ?? '—')}% • ${esc(d.risk || 'UNKNOWN')} risk • ${esc(d.evidence_quality || '—')} evidence</p><button class="btn primary" onclick="window.smartGuideOpenPassport('${esc(id)}')">Open Compliance Passport</button>`;
    out.prepend(box);
  }

  window.smartGuideOpenPassport = openPassport;

  // Wrap the existing compliance action without destroying its current UI.
  function patchCompliance() {
    if (typeof submitCompliance !== 'function' || submitCompliance.__v5wrapped) return;
    const original = submitCompliance;
    const wrapped = async function(product) {
      const checks = {};
      document.querySelectorAll('#checklist input').forEach(x => checks[x.dataset.req] = x.checked);
      const v4 = await saveV4Assessment(product, checks);
      await original(product);
      if (!v4.error) addV4ResultButton(v4);
    };
    wrapped.__v5wrapped = true;
    window.submitCompliance = wrapped;
  }

  // Make the existing Document AI prefer the persistent V4 extraction endpoint.
  function patchDocument() {
    if (typeof doc !== 'function' || doc.__v5wrapped) return;
    const original = doc;
    const wrapped = async function() {
      const f = $('file')?.files?.[0];
      if (!f) return original();
      try {
        const fd = new FormData(); fd.append('file', f);
        const d = await api('/v4/document', {method:'POST', body:fd});
        $('docOut').innerHTML = `<div class="card"><span class="tag green">V4 EXTRACTION</span><h2>${esc(d.filename || f.name)}</h2><p class="muted">${esc(d.characters_extracted || 0)} characters extracted</p><h3>Extracted fields</h3><pre class="pre" style="white-space:pre-wrap">${esc(JSON.stringify(d.extracted_fields || {}, null, 2))}</pre><h3>Candidate standards</h3>${(d.candidate_standards||[]).map(s=>`<div class="evidence"><b>${esc(s.standard_number)}</b> — ${esc(s.title || s.product || '')}</div>`).join('') || '<p class="muted">No supported candidate found.</p>'}<div class="notice" style="margin-top:12px">${esc(d.notice || 'Prototype extraction only. Verify official BIS sources.')}</div></div>`;
      } catch (_) {
        return original();
      }
    };
    wrapped.__v5wrapped = true;
    window.doc = wrapped;
  }

  function init() {
    addNav(); addPage();
    patchCompliance(); patchDocument();
    setTimeout(() => { patchCompliance(); patchDocument(); }, 500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
