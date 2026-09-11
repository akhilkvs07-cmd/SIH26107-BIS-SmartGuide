/* BIS SmartGuide Pro UI polish — presentation layer only */
(function(){
  'use strict';
  const $=s=>document.querySelector(s);
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  function personaLabel(){
    const raw=window.SG_PERSONA||window.smartGuidePersona||window.activePersona||'';
    if(typeof raw==='string' && raw.trim() && raw!=='[object Object]') return raw.trim();
    const select=[...document.querySelectorAll('select')].find(x=>/persona|role|user/i.test((x.id||'')+' '+(x.name||'')));
    const value=select?.selectedOptions?.[0]?.textContent?.trim();
    return value && value!=='[object Object]' ? value : 'Startup / Innovator';
  }
  function fixPersona(){
    document.querySelectorAll('*').forEach(el=>{
      if(el.children.length===0 && el.textContent.includes('ACTIVE PERSONA: [OBJECT OBJECT]')){
        el.textContent='ACTIVE PERSONA: '+personaLabel();
      }
    });
  }
  function addQuickActions(){
    const page=document.querySelector('.page.active')||document.querySelector('.page');
    if(!page || document.getElementById('sgProQuick')) return;
    const hero=page.querySelector('.hero'); if(!hero) return;
    const wrap=document.createElement('div'); wrap.id='sgProQuick'; wrap.className='sg-quick';
    const actions=[
      ['🔎','Find a standard','Start from any product','standard'],
      ['✓','Check compliance','Requirements and evidence','compliance'],
      ['🧪','Find a laboratory','Scope-aware BIS LIMS routing','labs']
    ];
    wrap.innerHTML=actions.map(a=>`<div class="sg-quick-card" data-page="${a[3]}"><div class="sg-quick-icon">${a[0]}</div><div><b>${a[1]}</b><span>${a[2]}</span></div><strong style="margin-left:auto;color:#9aacbf">→</strong></div>`).join('');
    page.insertBefore(wrap,hero);
    wrap.querySelectorAll('.sg-quick-card').forEach(card=>card.addEventListener('click',()=>{
      const key=card.dataset.page;
      if(key==='labs') window.page?.('v8',null,'Find a Laboratory');
      else if(key==='compliance') window.page?.('compliance',null,'Compliance Center');
      else window.page?.('standards',null,'Standard Finder');
    }));
  }
  function addPersonaBar(){
    const hero=document.querySelector('.page.active .hero'); if(!hero||document.getElementById('sgPersonaBar')) return;
    const p=document.createElement('div'); p.id='sgPersonaBar'; p.className='sg-persona';
    p.innerHTML=`<span class="sg-persona-dot"></span><div><b style="font-size:11px">ACTIVE PERSONA: ${esc(personaLabel())}</b><small>Guidance is tailored to your workflow while keeping BIS evidence and official sources visible.</small></div>`;
    const search=hero.querySelector('.hero-search'); if(search) search.insertAdjacentElement('afterend',p); else hero.appendChild(p);
  }
  function polishTopbar(){
    const bar=document.querySelector('.topbar'); if(!bar||bar.dataset.sgPro) return; bar.dataset.sgPro='1';
    const right=bar.querySelector('.top-actions'); if(!right) return;
    const badge=document.createElement('span'); badge.className='pill live'; badge.innerHTML='● System operational';
    right.insertBefore(badge,right.firstChild);
  }
  function run(){fixPersona();addQuickActions();addPersonaBar();polishTopbar();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run();
  setTimeout(run,900);setTimeout(run,2200);setTimeout(run,5000);
})();
