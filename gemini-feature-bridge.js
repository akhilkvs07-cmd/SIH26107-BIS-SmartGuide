/* Gemini feature bridge v1: every V5 workflow is first orchestrated by Gemini. */
(() => {
  if (window.__geminiFeatureBridge) return;
  window.__geminiFeatureBridge = true;
  const nativeFetch = window.fetch.bind(window);
  const API = 'https://sih26107-bis-smartguide-api.onrender.com';
  const isFeatureRequest = (input) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    return /\/v5\//.test(url) && !/agent\/orchestrate/.test(url);
  };
  const requestText = async (input, init) => {
    try {
      const url = typeof input === 'string' ? input : input.url;
      if (url.includes('?')) return new URL(url).search;
      const body = init && init.body;
      if (typeof body === 'string') return body;
      return 'Feature workflow request';
    } catch (_) { return 'Feature workflow request'; }
  };
  window.fetch = async (input, init = {}) => {
    if (!isFeatureRequest(input) || init.__geminiOrchestrated) return nativeFetch(input, init);
    const message = await requestText(input, init);
    try {
      await nativeFetch(API + '/api/v8/agent/orchestrate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-SmartGuide-Feature-Bridge': 'gemini-v1'},
        body: JSON.stringify({role: 'general', message: 'Orchestrate this BIS SmartGuide feature request using Gemini and preserve product identity: ' + message})
      });
      window.dispatchEvent(new CustomEvent('smartguide:gemini-orchestrated', {detail: {feature: String(input), timestamp: Date.now()}}));
    } catch (_) { /* feature endpoint remains available if orchestration is unavailable */ }
    return nativeFetch(input, {...init, __geminiOrchestrated: true});
  };
})();
