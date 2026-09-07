import { useEffect, useState } from 'react';
import { Activity, Bot, CheckCircle2, ClipboardCheck, FileSearch, History, Home, Link2, Loader2, Search, ShieldCheck, Upload, ExternalLink } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'https://sih26107-bis-smartguide-api.onrender.com';
const tabs = [
  ['home','Overview',Home], ['standard','Standard Finder',Search], ['compliance','Compliance',ClipboardCheck],
  ['scan','Document / Photo',FileSearch], ['verify','CM/L Verify',ShieldCheck], ['history','History',History],
  ['chat','AI Assistant',Bot], ['resources','BIS Resources',Link2]
];
const esc = s => String(s ?? '');

async function api(path, options) {
  const r = await fetch(API + path, options);
  let d = {}; try { d = await r.json(); } catch {}
  if (!r.ok) throw new Error(d.error || 'Request failed');
  return d;
}

function Metric({ value, children }) { return <div className="metric"><b>{value}</b><span>{children}</span></div>; }
function Status({ children, tone='' }) { return <span className={`pill ${tone}`}>{children}</span>; }

export default function App() {
  const [view, setView] = useState('home');
  const [standardQ, setStandardQ] = useState('');
  const [standard, setStandard] = useState(null);
  const [cp, setCp] = useState('gas stove');
  const [reqs, setReqs] = useState([]);
  const [checks, setChecks] = useState({});
  const [assessment, setAssessment] = useState(null);
  const [history, setHistory] = useState([]);
  const [passport, setPassport] = useState(null);
  const [file, setFile] = useState(null);
  const [docResult, setDocResult] = useState(null);
  const [cml, setCml] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState('');

  const go = id => { setView(id); if (id === 'history') loadHistory(); if (id === 'resources') loadResources(); };

  async function findStandard(q = standardQ) {
    if (!q.trim()) return; setStandardQ(q); setView('standard'); setLoading('standard'); setStandard(null);
    try { setStandard(await api('/recommend?product=' + encodeURIComponent(q))); }
    catch (e) { setStandard({ error: e.message }); } finally { setLoading(''); }
  }

  async function loadChecks() {
    if (!cp.trim()) return; setView('compliance'); setLoading('checks');
    try { const d = await api('/check-compliance?product=' + encodeURIComponent(cp)); setReqs(d.found ? d.standard.requirements || [] : []); setChecks({}); setAssessment(d.found ? { standard: d.standard } : { error: 'No matching product.' }); }
    catch (e) { setAssessment({ error: e.message }); } finally { setLoading(''); }
  }

  async function assess() {
    setLoading('assessment');
    try { setAssessment(await api('/v4/assess', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ product:cp, checks, evidence:{ interface:'BIS SmartGuide React', user_confirmed_checks:Object.values(checks).filter(Boolean).length }}) })); }
    catch (e) { setAssessment({ error:e.message }); } finally { setLoading(''); }
  }

  async function analyzeDoc() {
    if (!file) return; setLoading('document'); setDocResult(null); const fd = new FormData(); fd.append('file', file);
    try { setDocResult(await api('/v4/document',{method:'POST',body:fd})); } catch(e) { setDocResult({error:e.message}); } finally { setLoading(''); }
  }

  async function verify() {
    const digits = cml.replace(/\D/g,''); setCml(cml); setLoading('verify');
    setTimeout(() => setLoading(''), 250);
  }

  async function loadHistory() {
    try { const d = await api('/v4/assessments'); setHistory(d.assessments || []); } catch(e) { setHistory([{error:e.message}]); }
  }
  async function openPassport(id) {
    setLoading('passport');
    try { setPassport(await api('/v4/passport/' + encodeURIComponent(id))); setView('history'); }
    catch(e) { setPassport({error:e.message}); } finally { setLoading(''); }
  }
  async function chat() {
    if (!question.trim()) return; setLoading('chat'); setAnswer('Thinking…');
    try { const d=await api('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:question})}); setAnswer((d.reply||d.answer||JSON.stringify(d,null,2))+'\n\nEvidence:\n'+JSON.stringify(d.sources||d.retrieved||[],null,2)); }
    catch(e) { setAnswer(e.message); } finally { setLoading(''); }
  }
  async function loadResources() { try { const d=await api('/resources'); setResources(d.resources||[]); } catch(e) { setResources([{name:'Error',description:e.message,url:'https://www.bis.gov.in/'}]); } }
  useEffect(()=>{loadResources()},[]);

  const tone = r => r==='LOW' ? 'ok' : r==='HIGH' ? 'bad' : 'warn';
  return <div className="app">
    <header className="top"><div><div className="badge">BIS SMARTGUIDE • SOURCE-GROUNDED</div><h1>Compliance Intelligence Cockpit</h1><p>Standards → evidence → compliance → verification → report → history</p></div><div className="badge">SIH 26107 • REACT</div></header>
    <div className="shell">
      <aside className="sidebar"><div className="brand"><div className="brand-mark">B</div><div><strong>BIS SmartGuide</strong><small>Compliance Intelligence</small></div></div><div className="side-label">COMMAND CENTER</div>{tabs.map(([id,label,Icon])=><button key={id} className={view===id?'nav active':'nav'} onClick={()=>go(id)}><Icon size={17}/>{label}</button>)}<div className="sidebar-foot"><Activity size={15}/> API online<br/><small>Source-grounded prototype</small></div></aside>
      <main className="main"><div className="toolbar"><span>Command Center / <b>{tabs.find(t=>t[0]===view)?.[1]}</b></span><span className="live"><i/> System operational</span></div>
        <div className="content">
          {view==='home' && <><section className="hero"><div className="eyebrow">INTELLIGENT STANDARDS NAVIGATION</div><h2>From product idea to verified BIS compliance intelligence.</h2><p>Find applicable standards, build evidence-backed assessments and maintain a transparent compliance trail.</p><div className="hero-search"><input value={standardQ} onChange={e=>setStandardQ(e.target.value)} placeholder="Describe your product… e.g. 2 burner LPG gas stove"/><button className="btn" onClick={()=>findStandard()}>Find standard <Search size={16}/></button></div><div className="chips"><button onClick={()=>findStandard('2 burner LPG gas stove')}>Gas Stove</button><button onClick={()=>findStandard('electric kettle')}>Electric Kettle</button><button onClick={()=>findStandard('electric iron')}>Electric Iron</button><button onClick={()=>findStandard('PVC cable')}>PVC Cable</button></div></section><div className="grid3 metrics"><Metric value="✓">Evidence-grounded retrieval</Metric><Metric value="AI">Explainable product matching</Metric><Metric value="4.0">Compliance intelligence</Metric></div><div className="grid"><Card title="Judge Demo"><p>Enter a real product description. SmartGuide finds candidate standards and explains why they match.</p><button className="btn" onClick={()=>go('standard')}>Open Standard Finder</button></Card><Card title="Trust Layer"><Notice>SmartGuide separates prototype evidence from authoritative BIS sources. It does not issue certification. Current standards, amendments, QCOs, schemes and laboratory scope must be verified through official BIS resources.</Notice></Card></div></>}
          {view==='standard' && <Card title="Applicable Standard Finder"><div className="row"><input className="field" value={standardQ} onChange={e=>setStandardQ(e.target.value)} placeholder="e.g. gas stove, electric iron, helmet"/><button className="btn" onClick={()=>findStandard()}>Search</button></div>{loading==='standard'?<Loader/>:standard?.error?<Bad>{standard.error}</Bad>:standard?.standard?<div className="evidence"><div className="row"><Status>{standard.standard.standard_number}</Status><Status tone="ok">Match {standard.match_score||0}%</Status></div><h3>{esc(standard.standard.title||standard.standard.product)}</h3><p>{esc(standard.standard.description||'Relevant product-standard match found in the prototype catalogue.')}</p><b>Why this match?</b><ul>{(standard.standard.match_reasons||[]).map((x,i)=><li key={i}>{esc(x)}</li>)}</ul><div className="row"><button className="btn" onClick={()=>{setCp(standard.standard.product||standardQ);go('compliance');loadChecks()}}>Open Compliance</button>{standard.standard.official_source&&<a target="_blank" rel="noreferrer" href={standard.standard.official_source}>Official source <ExternalLink size={13}/></a>}</div></div>:<Notice>No result yet. Search for a product to see applicable standards.</Notice>}</Card>}
          {view==='compliance' && <div className="grid"><Card title="Smart Compliance Assessment"><input className="field" value={cp} onChange={e=>setCp(e.target.value)} placeholder="Product name"/><button className="btn" onClick={loadChecks}>Load checklist</button>{loading==='checks'?<Loader/>:reqs.length>0&&<div className="checks"><p><b>{assessment?.standard?.standard_number}</b> — {assessment?.standard?.title}</p>{reqs.map((r,i)=><label className="check" key={i}><input type="checkbox" checked={!!checks[r]} onChange={e=>setChecks({...checks,[r]:e.target.checked})}/>{r}</label>)}<button className="btn" onClick={assess}>Generate evidence-backed assessment</button></div>}</Card><Card title="Assessment Result">{loading==='assessment'?<Loader/>:assessment?.error?<Bad>{assessment.error}</Bad>:assessment?.score!==undefined?<><div className="grid3"><Metric value={`${assessment.score}%`}>Score</Metric><Metric value={assessment.risk}>Risk</Metric><Metric value={assessment.evidence_quality}>Evidence</Metric></div><div className="evidence"><b>{assessment.status}</b><p>Assessment ID: <b>{assessment.assessment_id}</b></p><p>Confidence: {assessment.confidence}</p><h3>Corrective actions</h3><ul>{(assessment.corrective_actions||[]).map((a,i)=><li key={i}><b>{a.priority}</b> — {a.action}</li>)}</ul><button className="btn" onClick={()=>openPassport(assessment.assessment_id)}>Open Compliance Passport</button></div></>:<p className="muted">Load a checklist, mark evidence-backed checks, then assess.</p>}</Card></div>}
          {view==='scan' && <div className="grid"><Card title="Document / Product Photo Intelligence"><div className="drop"><Upload size={28}/><input type="file" accept=".txt,.md,.json,.pdf,.png,.jpg,.jpeg,.webp" onChange={e=>setFile(e.target.files?.[0]||null)}/><p>Upload a specification, certificate, PDF or product photo.</p><button className="btn" onClick={analyzeDoc}>Analyze evidence</button></div></Card><Card title="Extraction">{loading==='document'?<Loader/>:docResult?.error?<Bad>{docResult.error}</Bad>:docResult?<><p><b>{docResult.filename}</b> • {docResult.characters_extracted||0} extracted characters</p><h3>Extracted fields</h3><pre>{JSON.stringify(docResult.extracted_fields||{},null,2)}</pre><h3>Candidate standards</h3>{(docResult.candidate_standards||[]).map((s,i)=><div className="evidence" key={i}><b>{s.standard_number}</b> — {s.title||s.product}</div>)}<Notice>{docResult.notice||'Prototype analysis only.'}</Notice></>:<p className="muted">The V4 engine supports PDF extraction and optional OCR when deployment dependencies are available.</p>}</Card></div>}
          {view==='verify' && <div className="grid"><Card title="ISI / CM/L Verification"><p className="muted">This checks format only; active licence status is confirmed through BIS.</p><input className="field" value={cml} onChange={e=>setCml(e.target.value)} placeholder="7-digit CM/L number"/><button className="btn" onClick={verify}>Validate</button></Card><Card title="Result">{loading==='verify'?<Loader/>:<><Status tone={cml.replace(/\D/g,'').length===7?'ok':'bad'}>{cml.replace(/\D/g,'').length===7?'FORMAT VALID':'FORMAT INVALID'}</Status><p>{cml.replace(/\D/g,'').length===7?'The CM/L format looks valid.':'Prototype expects 7 digits.'}</p><a target="_blank" rel="noreferrer" href="https://www.bis.gov.in/">Open official BIS verification resources <ExternalLink size={13}/></a></>}</Card></div>}
          {view==='history' && <Card title="Assessment History"><div className="row between"><h2>Saved assessments</h2><button className="btn alt" onClick={loadHistory}>Refresh</button></div>{passport&&<div className="evidence passport"><h3>Compliance Passport</h3><div className="grid3"><Metric value={`${passport.score}%`}>Score</Metric><Metric value={passport.risk}>Risk</Metric><Metric value={passport.status}>Status</Metric></div><p><b>Product:</b> {passport.product}</p><p><b>Assessment:</b> {passport.assessment_id}</p><p><b>Evidence hash:</b> <code>{passport.evidence_hash}</code></p><Notice>This passport is an audit trail for the prototype, not a BIS certificate.</Notice></div>}{history.map((a,i)=>a.error?<Bad key={i}>{a.error}</Bad>:<div className="evidence" key={a.id||i}><div className="row"><b>{a.product}</b><Status>{a.standard_number||'—'}</Status><Status tone={tone(a.risk)}>{a.risk}</Status></div><p>Score {a.score}% • {a.status} • {a.created_at}</p><button className="btn alt" onClick={()=>openPassport(a.id)}>View passport</button></div>)}</Card>}
          {view==='chat' && <Card title="BIS AI Assistant"><div className="row"><input className="field" value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask about a BIS standard, certification, hallmarking or labs"/><button className="btn" onClick={chat}>Ask</button></div><pre className="pre">{answer||'Source-grounded assistant output will appear here.'}</pre></Card>}
          {view==='resources' && <Card title="Official BIS Resources"><div className="grid3">{resources.map((r,i)=><div className="evidence" key={i}><h3>{r.name}</h3><p>{r.description}</p><a target="_blank" rel="noreferrer" href={r.url}>Open BIS resource →</a></div>)}</div></Card>}
        </div>
      </main>
    </div>
  </div>
}

function Card({title,children}){return <section className="card"><h2>{title}</h2>{children}</section>}
function Notice({children}){return <div className="notice">{children}</div>}
function Bad({children}){return <div className="badbox">{children}</div>}
function Loader(){return <div className="loader"><Loader2 className="spin" size={18}/> Processing…</div>}
