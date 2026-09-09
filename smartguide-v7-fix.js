/* V7 runtime fixes: use the V7 status endpoint and connect image/review workflows. */
(()=>{
'use strict';
const API='https://sih26107-bis-smartguide-api.onrender.com';
const $=id=>document.getElementById(id);
const show=x=>{const o=$('sg7Result');if(o)o.textContent=JSON.stringify(x,null,2)};
async function api(path,opt={}){const r=await fetch(API+path,opt);let d={};try{d=await r.json()}catch{}if(!r.ok)throw Error(d.error||d.message||'Request failed');return d}
const oldOpen=window.sg7Open;
window.sg7Open=function(i){if(i==='status'){oldOpen(i);setTimeout(async()=>{try{show(await api('/v7/feature-status'))}catch(e){show({error:e.message})}},50);return}oldOpen(i)};
window.sg7Photo=async()=>{try{const f=$('photo')?.files?.[0];if(!f)return show({error:'Select an image'});const fd=new FormData();fd.append('file',f);show(await api('/v5/photo-intake',{method:'POST',body:fd}))}catch(e){show({error:e.message})}};
window.sg7PhotoProduct=async()=>{try{const f=$('prodPhoto')?.files?.[0];if(!f)return show({error:'Select a product image'});const fd=new FormData();fd.append('file',f);show(await api('/v5/photo-intake',{method:'POST',body:fd}))}catch(e){show({error:e.message})}};
window.sg7Review=async()=>{try{show(await api('/v7/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_id:$('reviewCase').value,decision:$('reviewDecision').value,note:$('reviewNote').value,reviewer:'Local reviewer'})}))}catch(e){show({error:e.message})}};
})();
