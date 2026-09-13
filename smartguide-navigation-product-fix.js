/* BIS SmartGuide navigation and product-context fix v1.0 */
(() => {
  'use strict';

  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();

  const routeLabels = {
    dash: 'Home',
    intel: 'Product Intelligence',
    standards: 'Browse Standards',
    finder: 'Standard Finder',
    compliance: 'Compliance Center',
    mandatory: 'Mandatory / QCO',
    certification: 'BIS Certification',
    labs: 'Find a Laboratory',
    docs: 'Analyze a Document',
    compare: 'Compare Standards',
    connections: 'Explore Connections',
    consumer: 'Consumer Services',
    qr: 'QR / Barcode',
    assistant: 'AI Assistant',
    reports: 'Report Studio',
    analytics: 'Analytics',
    v8: 'Advanced Features',
    passport: 'Compliance Passport'
  };

  function routeOf(el) {
    const onclick = el.getAttribute('onclick') || '';
    const match = onclick.match(/page\(\s*['"]([^'"]+)['"]/i);
    return match ? match[1] : '';
  }

  function setLabel(el, label) {
    const spans = el.querySelectorAll('span');
    const last = spans.length ? spans[spans.length - 1] : null;
    if (last) last.textContent = label;
    else {
      const icon = el.textContent.trim().match(/^[^A-Za-z0-9]+/);
      el.textContent = `${icon ? icon[0] + ' ' : ''}${label}`;
    }
    el.setAttribute('aria-label', label);
    el.dataset.sgRouteLabel = label;
  }

  function fixNavigation() {
    document.querySelectorAll('.nav button, .nav a').forEach(el => {
      const route = routeOf(el);
      if (route && routeLabels[route]) setLabel(el, routeLabels[route]);
    });

    // Repair legacy duplicate labels by using the actual onclick route, never DOM order.
    document.querySelectorAll('.nav button, .nav a').forEach(el => {
      const text = normalize(el.textContent);
      const route = routeOf(el);
      if (route === 'intel' && (text.includes('browse standards') || text.includes('find standards'))) {
        setLabel(el, 'Product Intelligence');
      }
      if (route === 'standards') setLabel(el, 'Browse Standards');
      if (route === 'compare') setLabel(el, 'Compare Standards');
    });
  }

  function rememberProduct() {
    const selectors = [
      '#productInput', '#product', '#piProduct', '#productDescription',
      'textarea[name="description"]', 'input[name="product"]'
    ];
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(input => {
        if (input.dataset.sgContextBound) return;
        input.dataset.sgContextBound = '1';
        input.addEventListener('input', () => {
          const value = String(input.value || '').trim();
          if (value) {
            try { sessionStorage.setItem('sg_selected_product', value); } catch (_) {}
          }
        });
      });
    });

    const remembered = (() => { try { return sessionStorage.getItem('sg_selected_product') || ''; } catch (_) { return ''; } })();
    if (!remembered) return;
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(input => {
        if (!String(input.value || '').trim()) input.value = remembered;
      });
    });
  }

  function fixPageTitle() {
    const active = document.querySelector('.nav button.active, .nav a.active');
    if (!active) return;
    const route = routeOf(active);
    const label = routeLabels[route];
    if (!label) return;
    const crumb = document.querySelector('.crumb');
    if (crumb && normalize(crumb.textContent) !== normalize(label)) crumb.textContent = label;
  }

  function apply() {
    fixNavigation();
    rememberProduct();
    fixPageTitle();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
  [250, 700, 1500, 3000, 6000].forEach(ms => setTimeout(apply, ms));
})();
