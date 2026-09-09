/* SmartGuide navigation hardening — makes Advanced Intelligence cards directly clickable. */
(()=>{
'use strict';
const run=(fn)=>{try{if(typeof window[fn]==='function')window[fn]();else console.warn('SmartGuide action missing:',fn)}catch(e){console.error('SmartGuide navigation error:',e)}};
const wire=()=>{
  // V6 console: make the entire feature card open its workflow, not only the small button.
  const v6Actions=['openProduct','openMark','openTest','openLab','openAmendment','openSTL','openLabel','openProcurement','openIssue'];
  document.querySelectorAll('#v6 .sg-v6-card').forEach((card,i)=>{
    if(card.dataset.sgNavWired||i>=v6Actions.length)return;
    card.dataset.sgNavWired='1';
    card.setAttribute('role','button');
    card.tabIndex=0;
    card.addEventListener('click',e=>{
      if(e.target.closest('button,a,input,textarea,select'))return;
      run(v6Actions[i]);
    });
    card.addEventListener('keydown',e=>{
      if((e.key==='Enter'||e.key===' ')&&!e.target.closest('button,input,textarea,select')){e.preventDefault();run(v6Actions[i])}
    });
  });
  // V7 console: make each numbered feature card itself open its workflow.
  document.querySelectorAll('#sg7 .sg7-card').forEach((card,i)=>{
    if(card.dataset.sgNavWired)return;
    card.dataset.sgNavWired='1';
    card.setAttribute('role','button');
    card.tabIndex=0;
    card.addEventListener('click',e=>{
      if(e.target.closest('button,a,input,textarea,select'))return;
      if(typeof window.sg7Open==='function')window.sg7Open(i);
    });
    card.addEventListener('keydown',e=>{
      if((e.key==='Enter'||e.key===' ')&&!e.target.closest('button,input,textarea,select')){e.preventDefault();if(typeof window.sg7Open==='function')window.sg7Open(i)}
    });
  });
};
const boot=()=>{wire();new MutationObserver(wire).observe(document.body,{childList:true,subtree:true})};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
