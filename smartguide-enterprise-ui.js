/* BIS SmartGuide Enterprise UI interactions — progressive enhancement only */
(() => {
  'use strict';
  const $ = (s, root=document) => root.querySelector(s);
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const navItems = [
    ['Overview','dash','⌂'],['Product Intelligence','intel','◈'],['Standard Finder','finder','⌕'],
    ['Compliance Center','compliance','✓'],['Mandatory / QCO','mandatory','!'],['Certification Roadmap','cert','◆'],
    ['Smart Laboratories','labs','⌬'],['Document Intelligence','docs','▣'],['Compare Standards','compare','⇄'],
    ['Knowledge Graph','graph','⌘'],['Consumer Services','consumer','◇'],['QR / Barcode Scanner','scanner','▣'],
    ['AI Assistant','assistant','◎'],['Report Studio','reports','▤'],['Activity & Analytics','history','◷'],['Advanced Features','v8','✦']
  ];
  function init() {
    const actions = $('.top-actions');
    if (actions && !$('#sgEnterpriseSearch')) {
      const search = document.createElement('button');
      search.id = 'sgEnterpriseSearch'; search.type='button'; search.className='sg-enterprise-action';
      search.setAttribute('aria-label','Open quick navigation'); search.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8"></circle><path d="m16 16 4.2 4.2"></path></svg><span>Quick find</span><small>⌘ K</small>';
      const lang = $('#globalLang'); actions.insertBefore(search, lang || actions.firstChild);
      search.addEventListener('click', openPalette);
    }
    if (actions && !$('#sgEnterpriseTheme')) {
      const theme = document.createElement('button'); theme.id='sgEnterpriseTheme'; theme.type='button';
      theme.className='sg-enterprise-action'; theme.setAttribute('aria-label','Switch between light mode and dark mode');
      const saved = localStorage.getItem('sg-enterprise-theme');
      if (saved === 'dark') document.body.classList.add('sg-enterprise-dark');
      theme.innerHTML = document.body.classList.contains('sg-enterprise-dark') ? '☀ <span>Light mode</span>' : '☾ <span>Dark mode</span>';
      theme.addEventListener('click', () => {
        const dark = document.body.classList.toggle('sg-enterprise-dark');
        localStorage.setItem('sg-enterprise-theme', dark ? 'dark' : 'light');
        theme.innerHTML = dark ? '☀ <span>Light mode</span>' : '☾ <span>Dark mode</span>';
      });
      actions.insertBefore(theme, $('#onlinePill') || null);
    }
    if (!$('#sgCommandBackdrop')) {
      const backdrop=document.createElement('div'); backdrop.id='sgCommandBackdrop'; backdrop.className='sg-command-backdrop';
      backdrop.innerHTML='<div class="sg-command" role="dialog" aria-modal="true" aria-label="Quick navigation"><input id="sgCommandInput" class="sg-command-search" placeholder="Search pages and workflows…" autocomplete="off"><div class="sg-command-label">Navigate to</div><div id="sgCommandItems"></div><div style="padding:10px;color:#8996a8;font-size:10px">Use ↑/↓ to browse · Enter to open · Esc to close</div></div>';
      document.body.appendChild(backdrop);
      backdrop.addEventListener('click',e=>{if(e.target===backdrop)closePalette()});
      $('#sgCommandInput').addEventListener('input',renderCommands);
      $('#sgCommandInput').addEventListener('keydown',e=>{
        const buttons=[...$('#sgCommandItems').querySelectorAll('button')], i=buttons.indexOf(document.activeElement);
        if(e.key==='ArrowDown'){e.preventDefault();buttons[Math.min(i+1,buttons.length-1)]?.focus()}
        if(e.key==='ArrowUp'){e.preventDefault();buttons[Math.max(i-1,0)]?.focus()}
        if(e.key==='Enter' && buttons.length===1){e.preventDefault();buttons[0].click()}
      });
      renderCommands();
    }
    document.addEventListener('keydown',e=>{
      if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openPalette()}
      if(e.key==='Escape')closePalette();
    });
    document.querySelectorAll('.nav button').forEach(btn=>btn.addEventListener('click',()=>{
      if(window.matchMedia('(max-width: 800px)').matches) $('#sidebar')?.classList.remove('open');
    }));
  }
  function renderCommands(){
    const holder=$('#sgCommandItems'), input=$('#sgCommandInput'); if(!holder||!input)return;
    const q=input.value.trim().toLowerCase();
    const filtered=navItems.filter(([name,id])=>(name+' '+id).toLowerCase().includes(q));
    holder.innerHTML=filtered.length ? filtered.map(([name,id,icon])=>'<button class="sg-command-item" type="button" data-page="'+escapeHtml(id)+'"><span>'+escapeHtml(icon+'  '+name)+'</span><small>Open →</small></button>').join('') : '<div style="padding:18px;color:#8290a3;font-size:12px">No matching page found.</div>';
    holder.querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{
      const id=btn.dataset.page, nav=[...document.querySelectorAll('.nav button')].find(b=>b.getAttribute('onclick')?.includes("'"+id+"'"));
      if(typeof window.page==='function') window.page(id,nav||null,navItems.find(x=>x[1]===id)?.[0]||id);
      closePalette();
    }));
  }
  function openPalette(){const back=$('#sgCommandBackdrop');if(!back)return;back.classList.add('open');const input=$('#sgCommandInput');input.value='';renderCommands();setTimeout(()=>input.focus(),0)}
  function closePalette(){const back=$('#sgCommandBackdrop');if(back)back.classList.remove('open')}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();