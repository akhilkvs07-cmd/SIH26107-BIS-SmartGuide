/* SmartGuide browser failsafe v4: protect health checks without aborting slow AI/chat requests. */
(() => {
  'use strict';

  const originalFetch = window.fetch.bind(window);
  const API_HOSTS = ['onrender.com', '127.0.0.1:5000', 'localhost:5000'];
  const HEALTH_TIMEOUT_MS = 12000;
  const API_TIMEOUT_MS = 30000;

  window.fetch = function(input, init = {}) {
    let url = '';
    try { url = typeof input === 'string' ? input : (input && input.url) || ''; } catch (_) {}

    const isApi = API_HOSTS.some(host => url.includes(host)) || /\/health(?:\?|$)/.test(url);
    if (!isApi || typeof AbortController === 'undefined') return originalFetch(input, init);

    // Render's free service can take time to wake and initialize its RAG index.
    // Keep health checks bounded, but give real API requests such as /chat enough time.
    const isHealth = /\/health(?:\?|$)/.test(url);
    const timeout = isHealth ? HEALTH_TIMEOUT_MS : API_TIMEOUT_MS;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    const next = { ...init, signal: controller.signal };
    return originalFetch(input, next).finally(() => clearTimeout(timer));
  };

  const ROLE_LABELS = {
    manufacturer_msme: '🏭 Manufacturer / MSME',
    startup: '🚀 Startup / Innovator',
    importer: '🚢 Importer / Foreign Mfr (FMCS)',
    procurement: '🛒 Procurement / GeM Officer',
    consumer: '🛡️ Consumer / Citizen',
    laboratory: '🔬 Testing Laboratory',
    compliance_pro: '📋 Compliance Consultant',
    general: '🌐 General / Explorer'
  };

  function fixPersonaBanner() {
    const banner = document.getElementById('roleBanner');
    if (!banner) return;

    const text = banner.textContent || '';
    const bad = /\[object Object\]/i.test(text);
    if (bad) {
      const roleId = (document.getElementById('userRoleSelector')?.value || localStorage.getItem('sgUserRole') || 'general');
      const label = ROLE_LABELS[roleId] || ROLE_LABELS.general;
      const badge = banner.querySelector('span');
      if (badge) badge.textContent = 'Active Persona: ' + label;
    }

    banner.style.background = 'rgba(255,255,255,.72)';
    banner.style.borderColor = '#d7e6f5';
    const focus = banner.querySelector('div[style*="margin-top:6px"]');
    if (focus) focus.style.color = '#6d7e98';
    banner.querySelectorAll('.darkghost').forEach(btn => {
      btn.style.background = '#fff';
      btn.style.color = '#155ab2';
      btn.style.borderColor = '#dce6f2';
    });
  }

  window.addEventListener('load', () => {
    setTimeout(() => {
      const badge = document.getElementById('healthBadge');
      const agent = document.getElementById('agent');
      const pill = document.getElementById('onlinePill');
      if (badge && /Checking/i.test(badge.textContent || '')) {
        badge.textContent = '● Backend waking / unavailable';
        badge.className = 'status-badge warn';
      }
      if (agent && agent.textContent === '—') agent.textContent = 'Unavailable';
      if (pill && /System Online/i.test(pill.textContent || '')) pill.textContent = '● UI Ready';
      fixPersonaBanner();
    }, HEALTH_TIMEOUT_MS + 500);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      [700, 1800, 3500, 6000].forEach(ms => setTimeout(fixPersonaBanner, ms));
    });
  } else {
    [700, 1800, 3500, 6000].forEach(ms => setTimeout(fixPersonaBanner, ms));
  }
})();
