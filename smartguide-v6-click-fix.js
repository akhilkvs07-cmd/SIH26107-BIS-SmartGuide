/* BIS SmartGuide V6 — resilient card click bridge. */
(() => {
  const actions = {
    'product ai': 'openProduct',
    'isi / cm-l': 'openMark',
    'test reports': 'openTest',
    'lab matcher': 'openLab',
    'qco + amendment': 'openAmendment',
    '3d cad / stl': 'openSTL',
    'label / packaging': 'openLabel',
    'procurement ai': 'openProcurement',
    'issue report': 'openIssue'
  };
  function wire(){
    document.querySelectorAll('.sg-v6-card').forEach(card => {
      if(card.classList.contains('sg-v6-status-card') || card.dataset.v6ClickFixed) return;
      const heading = card.querySelector('h3');
      const key = (heading?.textContent || '').replace(/\s+/g,' ').trim().toLowerCase();
      const fn = actions[key];
      if(!fn || typeof window[fn] !== 'function') return;
      card.dataset.v6ClickFixed='1';
      card.classList.add('sg-v6-clickable');
      card.setAttribute('role','button');
      card.setAttribute('tabindex','0');
      const open = card.querySelector('.sg-v6-open');
      if(open) open.textContent='Open workflow →';
      const run=()=>window[fn]();
      card.addEventListener('click', e => { if(e.target.closest('button,a,input,textarea,select')) return; run(); });
      card.addEventListener('keydown', e => { if(e.key==='Enter'||e.key===' '){e.preventDefault();run();} });
    });
  }
  const boot=()=>{wire();setTimeout(wire,300);setTimeout(wire,1000);};
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
  new MutationObserver(wire).observe(document.documentElement,{childList:true,subtree:true});
})();
