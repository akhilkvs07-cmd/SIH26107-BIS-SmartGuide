/* SmartGuide browser failsafe: keep a slow/waking backend from making the UI feel stuck. */
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
    }, TIMEOUT_MS + 500);
  });
})();
