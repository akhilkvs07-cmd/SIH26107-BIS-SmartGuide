/* BIS SmartGuide Advanced Features — task-focused STL UX */
(() => {
  const apiBase = () => (typeof window.getSmartGuideApiHost === 'function')
    ? window.getSmartGuideApiHost()
    : 'https://sih26107-bis-smartguide-api.onrender.com';
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const num = x => Number.isFinite(Number(x)) ? Number(x) : null;

  async function call(path, options) {
    const r = await fetch(apiBase() + path, options);
    let d = {};
    try { d = await r.json(); } catch (_) {}
    if (!r.ok) throw new Error(d.error || d.message || `Request failed (${r.status})`);
    return d;
  }

  function resultCard(d, file, product) {
    const dims = d.bounding_box || {};
    const checks = Array.isArray(d.dimensional_checks) ? d.dimensional_checks : [];
    const failed = checks.filter(x => x.pass === false);
    const geometryOk = Number(d.triangle_count || 0) > 0 && !!d.bounding_box;
    const status = failed.length ? 'Review dimensions' : geometryOk ? 'Engineering pre-check passed' : 'Geometry needs review';
    const statusClass = failed.length ? 'warn' : geometryOk ? 'ok' : 'warn';
    const dim = ['x','y','z'].filter(k => dims[k] !== undefined && dims[k] !== null)
      .map(k => `<div class="sg-adv-metric"><small>${k.toUpperCase()} size</small><b>${esc(Number(dims[k]).toFixed(3))}</b></div>`).join('');
    const checkHtml = checks.length ? checks.map(x => `<div class="sg-adv-check ${x.pass === false ? 'bad' : 'good'}"><span>${x.pass === false ? '!' : '✓'}</span><div><b>${esc(String(x.axis || '').toUpperCase())} dimension</b><small>${x.pass === false ? `Measured ${esc(x.measured)} exceeds limit ${esc(x.limit)}` : `Measured ${esc(x.measured)} is within limit ${esc(x.limit)}`}</small></div></div>`).join('') : '<div class="sg-adv-muted">No dimension limits were supplied, so only geometry was inspected.</div>';
    const safeProduct = esc(product || 'your product');
    const standardButton = `<button type="button" class="sg-adv-action primary" onclick="openProduct();">🔎 Find applicable BIS standard</button>`;
    const labButton = `<button type="button" class="sg-adv-action" onclick="openLab();">🧪 Find a testing laboratory</button>`;
    const complianceButton = `<button type="button" class="sg-adv-action" onclick="page && page('compliance',this,'Compliance Center');">✓ Open compliance</button>`;

    return `<div class="sg-adv-stl-result">
      <div class="sg-adv-result-head">
        <div><span class="sg-v9-eyebrow dark">SCAN COMPLETE</span><h3>STL engineering screen</h3><p>${file ? esc(file.name) : 'Uploaded STL file'}</p></div>
        <span class="sg-adv-status ${statusClass}">${statusClass === 'ok' ? '✓' : '⚠'} ${esc(status)}</span>
      </div>
      <div class="sg-adv-summary"><div><b>What SmartGuide checked</b><span>File readability, STL geometry and optional dimension limits.</span></div><div><b>What this does not prove</b><span>BIS conformity, certification, QCO compliance or laboratory acceptance.</span></div></div>
      <div class="sg-adv-metrics"><div class="sg-adv-metric"><small>Format</small><b>${esc(d.format || 'STL')}</b></div><div class="sg-adv-metric"><small>Triangles</small><b>${esc(d.triangle_count || 0)}</b></div><div class="sg-adv-metric"><small>File size</small><b>${esc(Math.round((Number(d.bytes || 0) / 1024) * 10) / 10)} KB</b></div>${dim}</div>
      ${checks.length ? `<div class="sg-adv-section"><h4>Dimension checks</h4>${checkHtml}</div>` : `<div class="sg-adv-section"><h4>Geometry result</h4><div class="sg-adv-check good"><span>✓</span><div><b>STL geometry extracted</b><small>${esc(d.triangle_count || 0)} triangles detected and a bounding box was calculated.</small></div></div></div>`}
      <div class="sg-adv-next"><div><span class="sg-v9-eyebrow dark">NEXT STEP</span><h4>Turn this engineering check into a BIS workflow</h4><p>${product ? `For <b>${safeProduct}</b>, continue by identifying the applicable Indian Standard and then checking testing and compliance requirements.` : 'Add the product type so SmartGuide can connect the CAD check to the applicable Indian Standard.'}</p></div><div class="sg-adv-actions">${standardButton}${labButton}${complianceButton}</div></div>
      <div class="sg-adv-notice"><b>Important:</b> Geometry measurements are engineering pre-checks only. Verify the applicable BIS standard, amendments, QCO and current laboratory scope through official BIS sources before acting.</div>
      <details class="sg-v9-technical"><summary>View technical details</summary><pre>${esc(JSON.stringify(d, null, 2))}</pre></details>
    </div>`;
  }

  window.openSTL = () => {
    const el = $('v8Tool');
    if (!el) return;
    el.innerHTML = `<div class="sg-v9-tool sg-adv-stl-tool"><div class="sg-v9-tool-head"><div><span class="sg-v9-eyebrow">WORKFLOW</span><h2>3D CAD / STL Scanner</h2><p>Check whether an STL file can be read, inspect its geometry, and optionally compare dimensions against limits you provide.</p></div><button class="sg-v9-close" onclick="$('v8Tool').innerHTML=''">✕</button></div>
      <div class="sg-adv-how"><div><span>1</span><b>Upload</b><small>Select an STL file.</small></div><div><span>2</span><b>Screen</b><small>SmartGuide reads the geometry.</small></div><div><span>3</span><b>Act</b><small>Continue to standards and testing.</small></div></div>
      <div class="sg-v9-form sg-adv-stl-form"><label>Product / component <span>Optional</span><input id="v8STLProduct" placeholder="Example: pressure vessel bracket, appliance housing"></label><label>STL file<input id="v8STL" type="file" accept=".stl"></label><div class="sg-adv-dim-title"><b>Optional dimension limits</b><span>Leave blank if you only want a geometry check.</span></div><div class="sg-adv-dim-grid"><label>Max X <input id="v8X" type="number" step="any" placeholder="mm"></label><label>Max Y <input id="v8Y" type="number" step="any" placeholder="mm"></label><label>Max Z <input id="v8Z" type="number" step="any" placeholder="mm"></label></div><button class="sg-v9-run" onclick="runSTL()">🧊 Scan STL</button></div><div id="v8Out"></div></div>`;
    el.scrollIntoView({behavior:'smooth', block:'start'});
  };

  window.runSTL = async () => {
    const out = $('v8Out');
    if (!out) return;
    const file = $('v8STL')?.files?.[0];
    if (!file) { out.innerHTML = '<div class="sg-v9-error"><b>Select an STL file first.</b><p>Choose the CAD/STL file you want SmartGuide to inspect.</p></div>'; return; }
    out.innerHTML = '<div class="sg-v9-loading"><span class="sg-v9-spinner"></span><div><b>Scanning your STL…</b><small>Reading geometry and checking the limits you supplied.</small></div></div>';
    try {
      const fd = new FormData();
      fd.append('file', file);
      const product = $('v8STLProduct')?.value?.trim() || '';
      [['x','v8X'],['y','v8Y'],['z','v8Z']].forEach(([axis,id]) => { const v=$(id)?.value; if(v) fd.append('max_'+axis,v); });
      const d = await call('/v5/stl-scan', {method:'POST', body:fd});
      out.innerHTML = resultCard(d, file, product);
    } catch (e) {
      out.innerHTML = `<div class="sg-v9-error"><b>We could not scan this STL.</b><p>${esc(e.message || e)}</p><small>Make sure the file is a valid ASCII or binary STL and try again.</small></div>`;
    }
  };
})();