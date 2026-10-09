/* Gemini feature bridge v2: run the real Gemini BIS agent for V5 workflows.
   Original feature endpoints remain authoritative for structured checks; Gemini
   adds a separately-labelled reasoning layer and never certifies a product. */
(() => {
  if (window.__geminiFeatureBridgeV2) return;
  window.__geminiFeatureBridgeV2 = true;
  const nativeFetch = window.fetch.bind(window);
  const API = 'https://sih26107-bis-smartguide-api.onrender.com';
  const excluded = /\/v5\/(?:feature-status|self-test|health)(?:[/?]|$)/i;
  const isFeatureRequest = (input) => {
    const raw = typeof input === 'string' ? input : (input && input.url) || '';
    try {
      const url = new URL(raw, window.location.href);
      return /\/v5\//i.test(url.pathname) && !excluded.test(url.pathname);
    } catch (_) {
      return /\/v5\//i.test(raw) && !excluded.test(raw);
    }
  };
  const statusPromise = nativeFetch(API + '/api/v8/agent/status', { headers: { 'Accept': 'application/json' } })
    .then((response) => response.ok ? response.json() : null)
    .then((status) => Boolean(status && status.enabled === true))
    .catch(() => false);

  async function getFeatureContext(input, init) {
    const rawUrl = typeof input === 'string' ? input : (input && input.url) || '';
    const method = (init && init.method) || (input && input.method) || 'GET';
    let url;
    try { url = new URL(rawUrl, window.location.href); } catch (_) { url = new URL(window.location.href); }
    const query = {};
    url.searchParams.forEach((value, key) => { query[key] = value.slice(0, 240); });
    let body = {};
    const bodySource = init && init.body;
    if (typeof bodySource === 'string') {
      try { body = JSON.parse(bodySource); } catch (_) { body = { input: bodySource.slice(0, 500) }; }
    } else if (!bodySource && typeof Request !== 'undefined' && input instanceof Request) {
      try {
        const text = await input.clone().text();
        try { body = JSON.parse(text); } catch (_) { body = {}; }
      } catch (_) {}
    } else if (typeof FormData !== 'undefined' && bodySource instanceof FormData) {
      const file = bodySource.get('file');
      if (file && typeof file.name === 'string') body = { filename: file.name };
    }
    const allowed = ['product', 'description', 'query', 'standard', 'hs_code', 'raw_material', 'issue', 'amendment', 'text', 'language', 'role'];
    const context = {};
    for (const key of allowed) {
      if (body[key] !== undefined && body[key] !== null && String(body[key]).trim()) {
        context[key] = String(body[key]).slice(0, key === 'text' || key === 'amendment' ? 700 : 240);
      }
    }
    const combined = { path: url.pathname, method: String(method).toUpperCase(), query, context };
    return 'Assist with this BIS SmartGuide feature request using available evidence. Keep the exact product identity, do not invent standards or certification outcomes, and state uncertainty clearly. Feature context: ' + JSON.stringify(combined);
  }

  function safeAssistant(result) {
    return {
      reply: String(result.reply || ''),
      product: String(result.product || ''),
      standards_status: String(result.standards_status || 'Needs official verification'),
      next_actions: Array.isArray(result.next_actions) ? result.next_actions.slice(0, 5) : [],
      evidence_trail: Array.isArray(result.evidence_trail) ? result.evidence_trail.slice(0, 8) : [],
      source_grounded: result.source_grounded === true,
      web_grounded: result.web_grounded === true,
      agent: result.agent || 'BIS SmartGuide Universal Agent',
      agent_runtime: result.agent_runtime || 'unknown',
      gemini_status: result.gemini_status || 'unknown',
      model: result.model || ''
    };
  }

  function showInsight(assistant, featurePath) {
    if (!assistant || assistant.agent_runtime !== 'gemini-developer-api' || !document.body) return;
    let panel = document.getElementById('sg-gemini-feature-insight');
    if (!panel) {
      panel = document.createElement('aside');
      panel.id = 'sg-gemini-feature-insight';
      panel.setAttribute('role', 'status');
      panel.setAttribute('aria-live', 'polite');
      Object.assign(panel.style, {
        position: 'fixed', right: '18px', bottom: '18px', zIndex: '2147483000',
        width: 'min(390px, calc(100vw - 36px))', maxHeight: '42vh', overflow: 'auto',
        padding: '16px', border: '1px solid #64748b', borderRadius: '14px',
        background: '#101827', color: '#f8fafc', boxShadow: '0 12px 36px rgba(0,0,0,.32)',
        font: '14px/1.45 system-ui, sans-serif'
      });
      const heading = document.createElement('div');
      heading.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;font-weight:700';
      const title = document.createElement('span');
      title.textContent = 'Gemini feature insight';
      const close = document.createElement('button');
      close.type = 'button';
      close.textContent = 'Close';
      close.setAttribute('aria-label', 'Close Gemini feature insight');
      close.style.cssText = 'background:transparent;color:#cbd5e1;border:1px solid #64748b;border-radius:7px;padding:4px 8px;cursor:pointer';
      close.addEventListener('click', () => panel.remove());
      heading.append(title, close);
      const feature = document.createElement('div');
      feature.id = 'sg-gemini-feature-name';
      feature.style.cssText = 'font-size:11px;color:#94a3b8;margin-bottom:8px;overflow-wrap:anywhere';
      const reply = document.createElement('div');
      reply.id = 'sg-gemini-feature-reply';
      reply.style.cssText = 'white-space:pre-wrap;overflow-wrap:anywhere';
      const evidence = document.createElement('div');
      evidence.id = 'sg-gemini-feature-evidence';
      evidence.style.cssText = 'margin-top:10px;font-size:12px;color:#cbd5e1;white-space:pre-wrap;overflow-wrap:anywhere';
      panel.append(heading, feature, reply, evidence);
      document.body.appendChild(panel);
    }
    panel.querySelector('#sg-gemini-feature-name').textContent = featurePath + ' · ' + (assistant.model || 'Gemini');
    panel.querySelector('#sg-gemini-feature-reply').textContent = assistant.reply || 'Gemini returned no additional guidance.';
    const evidence = assistant.evidence_trail || [];
    panel.querySelector('#sg-gemini-feature-evidence').textContent =
      (assistant.source_grounded ? 'Evidence-grounded guidance' : 'Evidence insufficient — verify with official BIS sources') +
      (evidence.length ? '\n\nEvidence trail:\n• ' + evidence.join('\n• ') : '');
  }

  async function attachAssistant(response, assistant) {
    if (!assistant || !response || !/application\/json/i.test(response.headers.get('content-type') || '')) return response;
    let payload;
    try { payload = await response.clone().json(); } catch (_) { return response; }
    const detail = safeAssistant(assistant);
    if (payload && payload.data && typeof payload.data === 'object' && !Array.isArray(payload.data)) {
      payload.data.gemini_assistance = detail;
    } else if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
      payload.gemini_assistance = detail;
    } else {
      return response;
    }
    const headers = new Headers(response.headers);
    headers.delete('content-length');
    headers.delete('content-encoding');
    return new Response(JSON.stringify(payload), { status: response.status, statusText: response.statusText, headers });
  }

  window.fetch = async (input, init = {}) => {
    if (!isFeatureRequest(input) || init.__geminiOrchestrated) return nativeFetch(input, init);
    let assistant = null;
    try {
      if (await statusPromise) {
        const message = await getFeatureContext(input, init);
        const aiResponse = await nativeFetch(API + '/api/v8/agent/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-SmartGuide-Feature-Bridge': 'gemini-v2' },
          body: JSON.stringify({ role: 'general', message })
        });
        if (aiResponse.ok) {
          const result = await aiResponse.json();
          if (result && result.agent_runtime === 'gemini-developer-api') assistant = result;
        }
      }
    } catch (_) {
      // Feature APIs must remain usable if Gemini is unavailable or rate-limited.
    }
    const response = await nativeFetch(input, { ...init, __geminiOrchestrated: true });
    if (!assistant) return response;
    try {
      const enriched = await attachAssistant(response, assistant);
      if (enriched !== response) {
        const raw = typeof input === 'string' ? input : (input && input.url) || String(input);
        showInsight(safeAssistant(assistant), raw.split('?')[0]);
        window.dispatchEvent(new CustomEvent('smartguide:gemini-orchestrated', {
          detail: { feature: raw, assistant: safeAssistant(assistant), timestamp: Date.now() }
        }));
      }
      return enriched;
    } catch (_) {
      return response;
    }
  };
})();