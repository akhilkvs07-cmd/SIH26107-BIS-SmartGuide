/* SmartGuide Verified Laboratory Router UI */
(function () {
  'use strict';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const api = window.sgApi || (async (path, opts) => {
    const base = window.getSmartGuideApiHost ? window.getSmartGuideApiHost() : 'https://sih26107-bis-smartguide-api.onrender.com';
    const r = await fetch(base + path, opts); const d = await r.json();
    if (!r.ok) throw new Error(d.error || d.message || `HTTP ${r.status}`); return d;
  });

  function init() {
    const out = document.getElementById('labsOut');
    if (!out || document.getElementById('sgLabRouter')) return;
    const panel = document.createElement('div');
    panel.id = 'sgLabRouter';
    panel.innerHTML = `
      <div class="card" style="margin-bottom:16px">
        <span class="tag green">SOURCE-GROUNDED LAB ROUTER</span>
        <h2 style="margin:10px 0 6px">Find a suitable laboratory</h2>
        <p class="muted" style="margin-top:0">Resolve the product to an Indian Standard, match current BIS LIMS scope where available, then rank suitable laboratories by distance.</p>
        <div class="grid2" style="margin-top:14px">
          <div><label class="tiny muted">Product / IS Number</label><input id="sgLabProduct" class="field" placeholder="e.g. keyboard, pressure cooker, IS 2347" /></div>
          <div><label class="tiny muted">Search Origin</label><select id="sgLabOrigin" class="field">
            <option value="28.6139,77.2090">New Delhi</option><option value="19.0760,72.8777">Mumbai</option><option value="12.9716,77.5946">Bengaluru</option><option value="22.5726,88.3639">Kolkata</option><option value="13.0827,80.2707">Chennai</option><option value="17.3850,78.4867">Hyderabad</option><option value="26.9124,75.7873">Jaipur</option><option value="23.0225,72.5714">Ahmedabad</option>
          </select></div>
          <div><label class="tiny muted">Category</label><select id="sgLabCategory" class="field">
            <option value="">All categories</option><option>Drinking Water</option><option>Electrical & Power</option><option>Electronics & IT</option><option>Mechanical</option><option>Chemical</option><option>Textiles</option><option>Food</option><option>Automotive</option>
          </select></div>
          <div><label class="tiny muted">IS Number (optional)</label><input id="sgLabStandard" class="field" placeholder="e.g. IS 2347 (2023)" /></div>
        </div>
        <div class="toolbar" style="margin-top:12px"><button id="sgLabSearch" class="btn primary">Find Laboratories</button><button id="sgLabGps" class="btn ghost" type="button">● Use My GPS Location</button></div>
        <div class="tiny muted" style="margin-top:10px">Scope matches come from BIS LIMS records. Nearby directory records without a confirmed scope are shown separately and never treated as capable solely because they are close.</div>
      </div>
      <div id="sgLabResults"></div>`;
    out.prepend(panel);
    document.getElementById('sgLabSearch').onclick = search;
    document.getElementById('sgLabGps').onclick = gps;
    document.getElementById('sgLabProduct').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });
  }

  async function search() {
    const results = document.getElementById('sgLabResults');
    const product = document.getElementById('sgLabProduct').value.trim();
    const standard = document.getElementById('sgLabStandard').value.trim();
    const category = document.getElementById('sgLabCategory').value.trim();
    const origin = document.getElementById('sgLabOrigin');
    const [lat, lon] = origin.value.split(',').map(Number);
    const city = origin.options[origin.selectedIndex]?.textContent?.trim() || '';
    if (!product && !standard) { results.innerHTML = '<div class="notice"><b>Enter a product or IS number.</b> Example: keyboard, pressure cooker or IS 2347.</div>'; return; }
    results.innerHTML = '<div class="card loading">Resolving the Indian Standard and checking BIS LIMS scope…</div>';
    try {
      const params = new URLSearchParams({ product, standard, test: category, city, lat, lon, limit: '12' });
      const data = await api('/v8/labs/match?' + params.toString());
      render(data, lat, lon);
    } catch (e) {
      results.innerHTML = `<div class="card dangerbox"><b>Laboratory search failed.</b><br>${esc(e.message)}</div>`;
    }
  }

  function render(data, lat, lon) {
    const results = document.getElementById('sgLabResults');
    const rows = data.results || data.labs || data.data?.laboratories || data.data?.results || data.data?.labs || [];
    const limsSearch = data.lims_scope_search || data.data?.official_resources?.bis_lims_is_search || 'https://lims.bis.gov.in/home/search_is_number/';
    if (!rows.length) {
      results.innerHTML = `<div class="card"><div class="notice"><b>No laboratory record was returned.</b><br>${esc(data.message || data.data?.message || 'Try the product name or exact IS number, then verify scope in BIS LIMS.')}</div><div style="margin-top:12px"><a href="${limsSearch}" target="_blank" rel="noopener">Open official BIS LIMS scope search ↗</a></div></div>`;
      return;
    }
    const cards = rows.map((r, i) => {
      const name = r.lab_name || r.name || r.laboratory_name || 'BIS laboratory';
      const address = r.address || '';
      const distance = r.distance_km ?? r.distance ?? null;
      const rlat = r.latitude ?? r.lat;
      const rlon = r.longitude ?? r.lon;
      const scope = r.scope_url || r.lims_scope_url || r.view_scope || limsSearch;
      const source = r.source_url || r.official_url || 'https://lims.bis.gov.in/home/bis_labs/';
      const maps = r.maps_url || (rlat != null && rlon != null ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(lat+','+lon)}&destination=${encodeURIComponent(rlat+','+rlon)}` : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name+' '+address)}`);
      const contact = r.contact_person || r.contact || '';
      const phone = r.contact_number || r.phone || '';
      const email = r.email || '';
      const validity = r.validity_date || r.validity || '';
      const isScopeMatch = r.scope_status === 'LIMS_SCOPE_MATCH';
      const status = isScopeMatch ? 'BIS LIMS SCOPE MATCH' : (r.status || r.recognition_status || r.verification_status || 'BIS LIMS directory record');
      const badge = isScopeMatch ? 'SUITABLE SCOPE MATCH' : (i === 0 ? 'NEAREST DIRECTORY MATCH' : 'OFFICIAL DIRECTORY');
      const scopeStatus = isScopeMatch ? `Scope: ${esc(r.scope_standard || data.resolved_standard?.standard_number || 'matched IS')}` : 'Scope verification required';
      return `<div class="result-card"><div class="result-top"><div><span class="tag ${isScopeMatch?'green':'amber'}">${badge}</span><h3 style="margin:9px 0 5px">${esc(name)}</h3><p class="muted tiny">${esc(address)}</p></div><div style="text-align:right">${distance != null ? `<div class="score">${esc(Number(distance).toFixed(2))} km</div><div class="tiny muted">Haversine distance</div>` : ''}</div></div><div class="tags" style="margin-top:10px"><span class="tag ${isScopeMatch?'green':'amber'}">${esc(status)}</span>${validity?`<span class="tag">Valid: ${esc(validity)}</span>`:''}<span class="tag">${scopeStatus}</span></div>${contact||phone||email?`<div class="tiny muted" style="margin-top:10px">${contact?`Contact: ${esc(contact)} · `:''}${phone?`Phone: ${esc(phone)} · `:''}${email?`Email: ${esc(email)}`:''}</div>`:''}<div class="toolbar" style="margin-top:12px"><a class="btn primary" href="${maps}" target="_blank" rel="noopener">Get Directions ↗</a><a class="btn ghost" href="${scope}" target="_blank" rel="noopener">Open BIS LIMS Scope ↗</a><a class="btn ghost" href="${source}" target="_blank" rel="noopener">Official Source ↗</a></div><div class="evidence ${isScopeMatch?'successbox':'notice'}"><div class="evidence-head"><b>${isScopeMatch?'BIS LIMS scope found':'Scope verification'}</b><small>${isScopeMatch?'Capability still depends on the exact test clauses and current validity.':'Distance does not prove testing capability.'}</small></div><div class="tiny muted" style="margin-top:5px">Verify the exact Indian Standard, test clauses, current validity, capacity and booking availability in BIS LIMS before sending samples.</div></div></div>`;
    }).join('');
    const resolved = data.resolved_standard?.standard_number || data.data?.query?.standard || '';
    const scopeCount = rows.filter(r => r.scope_status === 'LIMS_SCOPE_MATCH').length;
    results.innerHTML = `<div class="section-head"><div><h2>Laboratory matches</h2><p>${rows.length} result${rows.length===1?'':'s'} returned${resolved?` for ${esc(resolved)}`:''}. ${scopeCount ? `<b>${scopeCount} have a BIS LIMS scope match.</b>` : 'No scope-matched record was found in the configured scope layer.'}</p></div></div>${cards}`;
  }

  function gps() {
    if (!navigator.geolocation) { alert('Geolocation is not supported by this browser.'); return; }
    navigator.geolocation.getCurrentPosition(pos => {
      const sel = document.getElementById('sgLabOrigin');
      const value = `${pos.coords.latitude},${pos.coords.longitude}`;
      let opt = [...sel.options].find(o => o.value === value);
      if (!opt) { opt = document.createElement('option'); opt.value=value; opt.textContent='My GPS Location'; sel.appendChild(opt); }
      sel.value=value;
    }, () => alert('Location permission was not granted. Choose a city instead.'));
  }

  function boot(){ init(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  setTimeout(boot, 1000); setTimeout(boot, 3000);
  const observer = new MutationObserver(() => { if (document.getElementById('labsOut')) init(); });
  const startObserver = () => { const out = document.getElementById('labsOut'); if (out) observer.observe(out, { childList: true }); else setTimeout(startObserver, 1000); };
  startObserver();
})();
