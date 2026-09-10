/* BIS SmartGuide — navigation bridge + V8.5 integration loader. */
(() => {
  'use strict';
  const TARGETS={
    'product intelligence':'Product Intelligence',
    'evidence-backed compliance':'Compliance Center',
    'agentic bis assistant':'AI Assistant'
  };
  function findNav(label){return [...document.querySelectorAll('.nav button')].find(b=>(b.textContent||'').trim().toLowerCase().includes(label.toLowerCase()));}
  function wireCommandCenter(){
    const head=[...document.querySelectorAll('.section-head')].find(x=>/command\s*center/i.test(x.textContent||''));
    if(!head||head.dataset.sgCommandFix==='1')return;
    const grid=head.nextElementSibling;if(!grid||!grid.classList.contains('grid3'))return;
    [...grid.querySelectorAll('.module')].forEach(card=>{
      const title=(card.querySelector('h3')?.textContent||'').trim().toLowerCase();const target=TARGETS[title];const nav=target?findNav(target):null;if(!nav)return;
      card.setAttribute('role','button');card.setAttribute('tabindex','0');card.style.cursor='pointer';
      card.onclick=e=>{if(!e.target.closest('a,button,input,select,textarea'))nav.click()};
      card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();nav.click()}};
    });
    head.dataset.sgCommandFix='1';
  }
  function wireAdvanced(){
    const btn=document.getElementById('v8Nav');if(!btn||btn.dataset.sgAdvancedFix==='1')return;btn.dataset.sgAdvancedFix='1';
    btn.onclick=()=>{if(typeof window.page==='function')window.page('v8',btn,'Advanced Intelligence');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));btn.classList.add('active');setTimeout(()=>{const section=document.getElementById('v8');if(section){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));section.classList.add('active');window.scrollTo({top:0,behavior:'smooth'})}if(typeof window.loadV8Status==='function')window.loadV8Status();},50);};
  }
  function loadUpgrade(){
    if(document.getElementById('sg-v8-upgrade-script'))return;
    const s=document.createElement('script');s.id='sg-v8-upgrade-script';s.src='smartguide-v8-upgrade.js?v=20260910-v85';s.defer=true;document.head.appendChild(s);
  }
  function init(){wireCommandCenter();wireAdvanced();loadUpgrade();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  [300,800,1500].forEach(ms=>setTimeout(init,ms));
})();
