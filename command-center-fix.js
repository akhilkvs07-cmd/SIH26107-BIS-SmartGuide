/* BIS SmartGuide — navigation fixes
   Keeps Command Center cards working and guarantees the V8 Advanced Intelligence tab. */
(() => {
  'use strict';
  const API='https://sih26107-bis-smartguide-api.onrender.com';
  const TARGETS = {
    'product intelligence': 'Product Intelligence',
    'evidence-backed compliance': 'Compliance Center',
    'agentic bis assistant': 'AI Assistant'
  };

  function ensureV8Script() {
    if (document.getElementById('v8Nav') || typeof window.openProduct === 'function') return;
    if (document.querySelector('script[data-sg-v8-fallback="1"]')) return;
    const s=document.createElement('script');
    s.src='smartguide-v8.js?v=20260910-v8-final';
    s.dataset.sgV8Fallback='1';
    s.onload=()=>setTimeout(wireAdvanced,100);
    document.body.appendChild(s);
  }

  function ensureAdvancedButton() {
    const nav=document.querySelector('.nav');
    if (!nav || document.getElementById('v8Nav')) return;
    const b=document.createElement('button');
    b.id='v8Nav';
    b.type='button';
    b.innerHTML='<span>✦</span><span>Advanced Intelligence</span>';
    b.setAttribute('aria-label','Open Advanced Intelligence');
    b.style.order='999';
    b.onclick=async()=>{
      ensureV8Script();
      if (typeof window.page === 'function') window.page('v8',b,'Advanced Intelligence');
      document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      setTimeout(()=>{
        const section=document.getElementById('v8');
        if(section){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));section.classList.add('active');section.scrollIntoView({behavior:'smooth',block:'start'});}
        loadStatus();
      },250);
    };
    nav.appendChild(b);
  }

  function wireCommandCenter() {
    const heads = [...document.querySelectorAll('.section-head')];
    const head = heads.find(x => /command\s*center/i.test(x.textContent || ''));
    if (!head || head.dataset.sgCommandFix === '1') return;
    const grid = head.nextElementSibling;
    if (!grid || !grid.classList.contains('grid3')) return;
    const navButtons = [...document.querySelectorAll('.nav button')];
    const findNav = label => navButtons.find(b => (b.textContent || '').trim().toLowerCase().includes(label.toLowerCase()));
    [...grid.querySelectorAll('.module')].forEach(card => {
      const title = (card.querySelector('h3')?.textContent || '').trim().toLowerCase();
      const target = TARGETS[title];
      if (!target) return;
      const nav = findNav(target);
      if (!nav) return;
      card.setAttribute('role', 'button'); card.setAttribute('tabindex', '0');
      card.setAttribute('aria-label', `Open ${target}`); card.style.cursor = 'pointer';
      card.addEventListener('click', event => { if (!event.target.closest('a,button,input,select,textarea')) nav.click(); });
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); nav.click(); } });
      card.dataset.sgCommandTarget = target;
    });
    head.dataset.sgCommandFix = '1';
  }

  function wireAdvanced() {
    ensureAdvancedButton();
    const btn = document.getElementById('v8Nav');
    if (!btn) return;
    if (btn.dataset.sgAdvancedFix !== '1') {
      btn.dataset.sgAdvancedFix = '1';
      btn.onclick = () => {
        ensureV8Script();
        if (typeof window.page === 'function') window.page('v8', btn, 'Advanced Intelligence');
        document.querySelectorAll('.nav button').forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        setTimeout(() => {
          const section = document.getElementById('v8');
          if (section) { document.querySelectorAll('.page').forEach(x => x.classList.remove('active')); section.classList.add('active'); }
          loadStatus();
        }, 200);
      };
    }
  }

  async function loadStatus(){
    try{
      const r=await fetch(API+'/v5/feature-status');
      const d=await r.json(); const list=d.features||[];
      const active=document.getElementById('v8Active'); const status=document.getElementById('v8Status');
      if(active) active.textContent=list.filter(x=>String(x.status||'').startsWith('FUNCTIONAL')).length;
      if(status) status.innerHTML=list.map(x=>`<div class="sg-v8-card"><span class="sg-v8-badge">${String(x.status||'').replace(/[&<>\"']/g,'')}</span><h3>${String(x.feature||'').replace(/[&<>\"']/g,'')}</h3></div>`).join('');
    }catch(_){ }
  }

  function wire(){ ensureV8Script(); ensureAdvancedButton(); wireCommandCenter(); wireAdvanced(); }
  function init(){ wire(); setTimeout(wire,300); setTimeout(wire,1000); setTimeout(wire,1800); setTimeout(wire,3000); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
