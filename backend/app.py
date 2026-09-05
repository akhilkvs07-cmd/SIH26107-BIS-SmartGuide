from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os, re
from datetime import datetime, timezone
from rag_engine import LocalRAG
from bis_agent import BISExpertAgent

app=Flask(__name__); CORS(app)
BASE_DIR=os.path.dirname(os.path.abspath(__file__)); DATA_FILE=os.path.join(BASE_DIR,'bis_data.json'); DOCS_DIR=os.path.join(BASE_DIR,'documents'); os.makedirs(DOCS_DIR,exist_ok=True)
with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
bis_data=data.get('standards',[]) if isinstance(data,dict) else data
OFFICIAL_RESOURCES=[
 {'name':'BIS Standards Portal','description':'Search Indian Standards by number or keyword.','url':'https://standards.bis.gov.in/'},
 {'name':'Know Your Standard','description':'Standards, amendments, notifications, licences and laboratories.','url':'https://www.bis.gov.in/know-your-standard/?lang=en'},
 {'name':'Apply for a BIS Licence','description':'Official product certification guidance.','url':'https://www.bis.gov.in/apply-for-a-license/?lang=en'},
 {'name':'BIS Recognized Laboratories','description':'Current recognized laboratory directory.','url':'https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en'},
 {'name':'BIS LIMS','description':'BIS Laboratory Information Management System.','url':'https://lims.bis.gov.in/'},
 {'name':'Products under Compulsory Certification','description':'Official compulsory certification and QCO information.','url':'https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en'}]
STOP_WORDS={'a','an','and','are','as','at','be','by','for','from','has','have','how','i','in','is','it','of','on','or','that','the','this','to','what','which','with','my','our','can','do','does','about','tell','me','please','product','used','use','manufactured','manufacturing','made'}
SYNONYMS={'fan':['fan','ceiling fan','table fan','electric fan'],'charger':['charger','phone charger','mobile charger','adapter'],'iron':['iron','electric iron','clothes iron'],'stove':['stove','gas stove','gas cooker','gas cooking'],'cable':['cable','wire','pvc cable','insulated cable'],'lamp':['lamp','led','led lamp','light'],'kettle':['kettle','electric kettle'],'mixer':['mixer','mixer grinder','grinder'],'microwave':['microwave','microwave oven'],'heater':['heater','water heater','electric heater','immersion heater'],'socket':['socket','electrical socket','power socket'],'switch':['switch','electrical switch'],'refrigerator':['refrigerator','fridge'],'washing':['washing machine','washer'],'air conditioner':['air conditioner','ac','air conditioning'],'toaster':['toaster','electric toaster'],'rice cooker':['rice cooker','cooker'],'laptop':['laptop','laptops','notebook','notebooks','tablet','tablets','computer','computers','automatic data processing machine']}

def normalize(text): return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9\s]',' ',str(text or '').lower().replace('-',' '))).strip()
def tokenize(text): return [w for w in normalize(text).split() if len(w)>2 and w not in STOP_WORDS]
def searchable(s): return normalize(' '.join([s.get('standard_number',''),s.get('product',''),s.get('title',''),s.get('category',''),s.get('description',''),' '.join(s.get('requirements',[]))]))
def score_standard(query,s):
 q=normalize(query)
 if not q:return 0,[]
 product,title,category,number=map(normalize,[s.get('product',''),s.get('title',''),s.get('category',''),s.get('standard_number','')]); text=searchable(s); words=tokenize(q); score=0; reasons=[]; matched=[]
 if q==product: score+=100; reasons.append('Exact product match')
 elif q in product: score+=65; reasons.append('Product name contains your search')
 if q in title: score+=45; reasons.append('Product matches the standard title')
 if q in category: score+=20; reasons.append('Product matches the category')
 if q==number or q.replace(' ','')==number.replace(' ',''): score+=110; reasons.append('Standard number match')
 for w in words:
  if w in product: score+=22; matched.append(w)
  elif w in title: score+=14; matched.append(w)
  elif w in category: score+=7; matched.append(w)
  elif w in text: score+=4; matched.append(w)
 if matched: reasons.append('Keyword match: '+', '.join(sorted(set(matched))))
 for key,alts in SYNONYMS.items():
  if any(w==key or w in alts for w in words) and any(normalize(a) in text for a in alts): score+=35 if key=='laptop' else 10; reasons.append('Related product terminology detected'); break
 return score,reasons

def find_matches(q,limit=5):
 ranked=[]
 for s in bis_data:
  score,reasons=score_standard(q,s)
  if score:
   x=dict(s); x.update(match_score=min(100,score),raw_match_score=score,match_reasons=reasons[:5]); ranked.append(x)
 ranked.sort(key=lambda x:x['raw_match_score'],reverse=True); return ranked[:limit]

def certification_steps(standard=None):
 name=standard.get('standard_number') if standard else 'the applicable BIS standard'
 return [f'Identify and confirm {name} as the applicable standard.','Review the latest official BIS requirements, amendments, QCOs and applicable scheme.','Check manufacturing infrastructure, process controls, quality control and testing capability.','Arrange applicable testing through an appropriate BIS-recognized/empanelled laboratory where required.','Prepare technical, manufacturing and quality-control documentation.','Submit the applicable BIS application and complete inspection/assessment requirements.','Maintain continuing conformity, testing and records where applicable.']

def detect_product_entities(description):
 matches=find_matches(description,5); best=matches[0] if matches else None; text=normalize(description); attrs=[]
 for p in [r'\b\d+(?:\.\d+)?\s*(?:w|kw|v|kv|a|amp|amps|hz|kg|g|mm|cm|l|litre|liter)\b',r'\b\d+(?:\.\d+)?\s*(?:degree|degrees|c|°c)\b']: attrs+=re.findall(p,text)
 for feature in ['temperature control','adjustable temperature','overheating protection','insulation','household use','gas','electric','portable','automatic','digital','stainless steel','plastic','motor','heating element','water protection','voltage protection','pressure protection']:
  if feature in text: attrs.append(feature)
 return {'input':description,'detected_product':best.get('product') if best else None,'detected_category':best.get('category') if best else None,'attributes':list(dict.fromkeys(attrs)),'recommendations':matches}

def mandatory_assessment(product):
 matches=find_matches(product,1)
 if not matches:return {'found':False,'status':'UNKNOWN','message':'No sufficiently matched product in the prototype knowledge base. Check the official BIS compulsory-certification and QCO pages.'}
 s=matches[0]
 if s.get('scheme'): status='LIKELY WITHIN A COMPULSORY SCHEME'; explanation=f"The local record identifies {s['scheme']} for this product. Confirm the current BIS notification and exact product scope."
 else: status='NEEDS OFFICIAL VERIFICATION'; explanation='The prototype record does not contain verified QCO data for a mandatory/voluntary declaration.'
 return {'found':True,'product':product,'standard':s,'status':status,'explanation':explanation,'official_source':OFFICIAL_RESOURCES[5]['url']}

def compliance_result(product,checks):
 matches=find_matches(product,1)
 if not matches:return {'found':False,'message':'No matching product found.'}
 s=matches[0]; reqs=s.get('requirements',[]); passed=[]; failed=[]; unchecked=[]
 for r in reqs:
  v=checks.get(r)
  if v is True: passed.append(r)
  elif v is False: failed.append(r)
  else: unchecked.append(r)
 total=len(reqs); score=round(len(passed)/total*100) if total else 0; status='Needs Review' if failed else ('Partially Checked' if unchecked else 'Compliant')
 actions=[f'Review and correct: {x}.' for x in failed]
 if unchecked: actions.append('Complete all unchecked requirements before making a final conformity decision.')
 if not actions: actions.append('Maintain evidence and verify the latest official BIS requirements.')
 return {'found':True,'product':product,'standard':s,'score':score,'status':status,'passed':passed,'failed':failed,'not_checked':unchecked,'summary':{'total':total,'passed':len(passed),'failed':len(failed),'not_checked':len(unchecked)},'recommended_actions':actions,'certification_steps':certification_steps(s),'prototype_notice':'Prototype assessment only; it is not an official BIS certification decision.'}

def build_rag(): return LocalRAG(bis_data,OFFICIAL_RESOURCES,DOCS_DIR)
rag=build_rag()
def agent_compliance(message):
 m=find_matches(message,1)
 return {'reply':f"I found {m[0].get('standard_number')}. Open Compliance to run the requirement checklist.",'standard':m[0],'source':m[0].get('official_source') or OFFICIAL_RESOURCES[0]['url']} if m else None
agent=BISExpertAgent(find_matches,rag,OFFICIAL_RESOURCES,certification_steps,agent_compliance)

@app.route('/')
def home(): return jsonify({'message':'BIS SmartGuide Advanced Backend','status':'success','version':'5.0-agent'})
@app.route('/health')
def health(): return jsonify({'status':'healthy','standards_loaded':len(bis_data),'rag_chunks':rag.chunk_count,'documents_indexed':rag.document_count,'agent':agent.name,'agentic_chat':True,'version':'5.0','timestamp':datetime.now(timezone.utc).isoformat()})
@app.route('/standards')
def standards(): return jsonify({'count':len(bis_data),'standards':bis_data})
@app.route('/search')
def search():
 q=request.args.get('q','').strip()
 if not q:return jsonify({'error':'Please provide a search query'}),400
 r=find_matches(q,10); return jsonify({'query':q,'count':len(r),'results':r})
@app.route('/recommend')
def recommend():
 q=request.args.get('product','').strip()
 if not q:return jsonify({'error':'Please enter a product name or description'}),400
 r=find_matches(q,5); return jsonify({'found':bool(r),'message':None if r else 'No matching BIS standard found','standard':r[0] if r else None,'recommendations':r,'match_score':r[0]['match_score'] if r else 0})
@app.route('/analyze',methods=['POST'])
def analyze():
 b=request.get_json(silent=True) or {}; d=str(b.get('description','')).strip()
 if not d:return jsonify({'error':'Product description is required'}),400
 return jsonify(detect_product_entities(d))
@app.route('/recommendations')
def recommendations():
 q=request.args.get('q','').strip(); r=find_matches(q,5) if q else []; return jsonify({'query':q,'recommendations':r,'count':len(r)})
@app.route('/check-compliance')
def check_compliance():
 p=request.args.get('product','').strip()
 if not p:return jsonify({'error':'Please provide a product name'}),400
 return jsonify(compliance_result(p,{}))
@app.route('/check-product',methods=['POST'])
def check_product():
 b=request.get_json(silent=True) or {}; p=str(b.get('product','')).strip(); checks=b.get('checks',{}) or {}
 if not p:return jsonify({'error':'Product name is required'}),400
 return jsonify(compliance_result(p,checks))
@app.route('/mandatory-check')
def mandatory_check():
 p=request.args.get('product','').strip()
 if not p:return jsonify({'error':'Please provide a product name'}),400
 return jsonify(mandatory_assessment(p))
@app.route('/certification-guide')
def certification_guide():
 q=request.args.get('product','').strip(); m=find_matches(q,1) if q else []; s=m[0] if m else None
 return jsonify({'standard':s,'steps':certification_steps(s),'official_resources':OFFICIAL_RESOURCES[1:3],'notice':'Requirements vary by product, standard, QCO and scheme. Verify current BIS instructions.'})
@app.route('/labs')
def labs(): return jsonify({'message':'Use the official BIS recognized laboratory directory and LIMS for current availability.','official_url':OFFICIAL_RESOURCES[3]['url'],'lims_url':OFFICIAL_RESOURCES[4]['url']})
@app.route('/resources')
def resources(): return jsonify({'resources':OFFICIAL_RESOURCES})
@app.route('/rag-search')
def rag_search():
 q=request.args.get('q','').strip()
 if not q:return jsonify({'error':'Please provide a query'}),400
 return jsonify({'query':q,'rag':True,'results':rag.retrieve(q,8)})
@app.route('/rag-rebuild',methods=['POST'])
def rag_rebuild():
 global rag,agent
 rag=build_rag(); agent=BISExpertAgent(find_matches,rag,OFFICIAL_RESOURCES,certification_steps,agent_compliance)
 return jsonify({'success':True,'message':'RAG index rebuilt','rag_chunks':rag.chunk_count,'documents_indexed':rag.document_count,'agent_reloaded':True})
@app.route('/agent-chat',methods=['POST'])
def agent_chat():
 b=request.get_json(silent=True) or {}; m=str(b.get('message','')).strip()
 if not m:return jsonify({'error':'Message is required'}),400
 return jsonify(agent.run(m))
@app.route('/chat',methods=['POST'])
def chat():
 b=request.get_json(silent=True) or {}; m=str(b.get('message','')).strip()
 if not m:return jsonify({'error':'Message is required'}),400
 return jsonify(agent.run(m))
@app.route('/document-analyze',methods=['POST'])
def document_analyze():
 f=request.files.get('file')
 if not f:return jsonify({'error':'Upload a TXT, MD or JSON product/knowledge document.'}),400
 name=os.path.basename(f.filename or 'document.txt'); ext=os.path.splitext(name)[1].lower()
 if ext not in {'.txt','.md','.json'}:return jsonify({'error':'Prototype document analysis currently accepts TXT, MD and JSON files.'}),400
 raw=f.read().decode('utf-8','ignore')
 if ext=='.json':
  try: raw=json.dumps(json.loads(raw),ensure_ascii=False,indent=2)
  except json.JSONDecodeError: pass
 matches=find_matches(raw,5)
 return jsonify({'filename':name,'characters':len(raw),'detected_product':matches[0].get('product') if matches else None,'recommendations':matches,'missing_data_hints':['Rated voltage/power where applicable','Product scope and model/variant','Applicable test evidence','Manufacturer and factory details'],'notice':'Prototype document analysis. It does not certify a product.'})
@app.route('/report',methods=['POST'])
def report():
 b=request.get_json(silent=True) or {}; p=str(b.get('product','')).strip(); result=b.get('result') or compliance_result(p,{})
 if not p:return jsonify({'error':'Product is required'}),400
 return jsonify({'report':{'title':'BIS SmartGuide Compliance Assessment','product':p,'generated_at':datetime.now(timezone.utc).isoformat(),'assessment':result,'sources':OFFICIAL_RESOURCES},'printable':True})
@app.route('/api-info')
def api_info(): return jsonify({'version':'5.0','features':['BIS Standards Intelligence Agent','intent routing','local RAG','smart product identification','compliance dashboard','mandatory/QCO verification workflow','certification guide','laboratory resources','document text analysis','printable compliance report','voice input via browser','official source links'],'endpoints':['/health','/search','/recommend','/analyze','/check-product','/mandatory-check','/certification-guide','/labs','/resources','/rag-search','/rag-rebuild','/agent-chat','/chat','/document-analyze','/report']})
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=True)
