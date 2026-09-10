/* SmartGuide browser failsafe v3: keep a slow/waking backend and malformed persona payloads from making the UI feel broken. */
(() => {
  'use strict';

  const originalFetch = window.fetch.bind(window);
  const API_HOSTS = ['onrender.com', '127.0.0.1:5000', 'localhost:5000'];
  const TIMEOUT_MS = 9000;

  window.fetch = function(input, init = {}) {
    let url = '';
    try { url = typeof input === 'string' ? input : (input && input.url) || ''; } catch (_) {}
    const isApi = API_HOSTS.some(host => url.includes(host)) || /\/health(?:\?|$)/.test(url);
    if (!isApi || typeof AbortController === 'undefined') return originalFetch(input, init);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
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

    // v9 makes the hero light; keep the role banner readable in both themes.
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
    }, TIMEOUT_MS + 500);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      [700, 1800, 3500, 6000].forEach(ms => setTimeout(fixPersonaBanner, ms));
    });
  } else {
    [700, 1800, 3500, 6000].forEach(ms => setTimeout(fixPersonaBanner, ms));
  }
})();
