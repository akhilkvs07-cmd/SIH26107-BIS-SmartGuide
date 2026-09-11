/* SmartGuide Verified Laboratory Router UI
 * Connects the Find Laboratory page to the backend /v8/labs/match endpoint.
 * No synthetic laboratory cards, NABL numbers, contacts or capabilities are generated here.
 */
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
        <p class="muted" style="margin-top:0">Search by product or Indian Standard, choose an origin, and rank official BIS laboratory records by great-circle distance.</p>
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
        <div class="tiny muted" style="margin-top:10px">SmartGuide does not assert NABL accreditation or testing capability unless supported by the official source. Always verify the exact LIMS scope.</div>
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
    const [lat, lon] = document.getElementById('sgLabOrigin').value.split(',').map(Number);
    if (!product && !standard) { results.innerHTML = '<div class="notice"><b>Enter a product or IS number.</b> Example: keyboard, pressure cooker or IS 2347.</div>'; return; }
    results.innerHTML = '<div class="card loading">Finding official laboratory records and calculating proximity…</div>';
    try {
      const params = new URLSearchParams({ product, standard, test: category, lat, lon, limit: '12' });
      const data = await api('/v8/labs/match?' + params.toString());
      render(data, lat, lon);
    } catch (e) {
      results.innerHTML = `<div class="card dangerbox"><b>Laboratory search failed.</b><br>${esc(e.message)}</div>`;
    }
  }

  function render(data, lat, lon) {
    const results = document.getElementById('sgLabResults');
    const rows = data.results || data.labs || data.data?.results || data.data?.labs || [];
    if (!rows.length) {
      results.innerHTML = `<div class="card"><div class="notice"><b>No verified laboratory match was returned.</b><br>${esc(data.message || data.data?.message || 'Try the product name or exact IS number, then verify scope in BIS LIMS.')}</div><div style="margin-top:12px"><a href="https://lims.bis.gov.in/home/search_labs/" target="_blank" rel="noopener">Open official BIS LIMS laboratory search ↗</a></div></div>`;
      return;
    }
    const cards = rows.map((r, i) => {
      const name = r.lab_name || r.name || r.laboratory_name || 'BIS laboratory';
      const address = r.address || '';
      const distance = r.distance_km ?? r.distance ?? null;
      const scope = r.scope_url || r.lims_scope_url || r.view_scope || '';
      const source = r.source_url || r.official_url || 'https://lims.bis.gov.in/home/labs/';
      const maps = r.latitude != null && r.longitude != null ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(lat+','+lon)}&destination=${encodeURIComponent(r.latitude+','+r.longitude)}` : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name+' '+address)}`;
      const contact = r.contact_person || r.contact || '';
      const phone = r.contact_number || r.phone || '';
      const email = r.email || '';
      const validity = r.validity_date || r.validity || '';
      const status = r.status || r.recognition_status || 'BIS source record';
      return `<div class="result-card"><div class="result-top"><div><span class="tag green">${i===0?'NEAREST MATCH':'OFFICIAL SOURCE'}</span><h3 style="margin:9px 0 5px">${esc(name)}</h3><p class="muted tiny">${esc(address)}</p></div><div style="text-align:right">${distance != null ? `<div class="score">${esc(Number(distance).toFixed(2))} km</div><div class="tiny muted">Haversine proximity</div>` : ''}</div></div><div class="tags" style="margin-top:10px"><span class="tag">${esc(status)}</span>${validity?`<span class="tag">Valid: ${esc(validity)}</span>`:''}</div>${contact||phone||email?`<div class="tiny muted" style="margin-top:10px">${contact?`Contact: ${esc(contact)} · `:''}${phone?`Phone: ${esc(phone)} · `:''}${email?`Email: ${esc(email)}`:''}</div>`:''}<div class="toolbar" style="margin-top:12px"><a class="btn primary" href="${maps}" target="_blank" rel="noopener">Get Directions ↗</a>${scope?`<a class="btn ghost" href="${scope}" target="_blank" rel="noopener">View LIMS Scope ↗</a>`:''}<a class="btn ghost" href="${source}" target="_blank" rel="noopener">Official Source ↗</a></div><div class="evidence"><div class="evidence-head"><b>Scope verification</b><small>Do not infer capability from distance alone.</small></div><div class="tiny muted" style="margin-top:5px">Confirm the exact Indian Standard, test facility and current validity in BIS LIMS before sending samples.</div></div></div>`;
    }).join('');
    results.innerHTML = `<div class="section-head"><div><h2>Laboratory matches</h2><p>${rows.length} official-source result${rows.length===1?'':'s'} returned. Ranked by proximity where coordinates are available.</p></div></div>${cards}`;
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
})();
