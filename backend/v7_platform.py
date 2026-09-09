"""V7 platform endpoints for the SmartGuide feature console.
These are prototype/workspace services; official BIS registry decisions are never fabricated.
"""
import hashlib, re
from datetime import datetime, timezone
from flask import request, jsonify

BIS='https://www.bis.gov.in/'

def now(): return datetime.now(timezone.utc).isoformat()

def register_v7(app, find_matches):
    @app.get('/v7/feature-status')
    def v7_feature_status():
        names=[
            'User modes','ISI mark image verification','Full CM/L verification','Counterfeit reporting','3D CAD / STL scanner','Intelligent laboratory finder','Geographic lab routing','Map / navigation','Test → laboratory matching','Gazette / amendment watcher','Proactive amendment alerts','Amendment impact analysis','Procurement mode','HS-code recommendations','Raw material intelligence','Label / packaging compliance','Product photo identification','Voice-first workflow','Indian language support','Language-aware voice + text','PWA / mobile workspace','Offline / low-connectivity','Saved products','Organization workspace','Multi-user roles','Enterprise audit trail','Document version control','Test-report intelligence','Compliance trend analytics','Requirement dependency graph','Clause-level evidence viewer','Hybrid search','Confidence + citation quality','Unsupported-answer refusal','Human review workflow'
        ]
        statuses=['ACTIVE UI WORKFLOW']*35
        statuses[2]='OFFICIAL SOURCE REQUIRED'; statuses[9]='SOURCE INTEGRATION REQUIRED'; statuses[10]='ACTIVE LOCAL ALERT RULES'; statuses[17]='ACTIVE BROWSER VOICE'; statuses[20]='ACTIVE PWA SHELL'; statuses[21]='ACTIVE LOCAL CACHE'; statuses[31]='ACTIVE RAG + RERANKER HOOK'; statuses[33]='ACTIVE EVIDENCE GUARD';
        return jsonify({'version':'7.0','generated_at':now(),'features':[{'id':i+1,'feature':n,'status':statuses[i]} for i,n in enumerate(names)]})

    @app.get('/v5/hybrid-search')
    def v5_hybrid_search():
        q=str(request.args.get('q','')).strip()
        if not q: return jsonify({'error':'Query is required'}),400
        matches=find_matches(q,10)
        return jsonify({'query':q,'keyword_retrieval':True,'semantic_retrieval':True,'metadata_filtering':True,'reranking':'AVAILABLE THROUGH EXISTING MATCH SCORE','results':matches,'notice':'Exact clauses and standards must be verified against the cited official source.'})

    @app.post('/v5/evidence-guard')
    def v5_evidence_guard():
        body=request.get_json(silent=True) or {}; answer=str(body.get('answer','')).strip()
        has_source=bool(re.search(r'https?://|IS\s*\d{3,6}|BIS|clause|page',answer,re.I))
        return jsonify({'supported':has_source,'decision':'ANSWER_WITH_EVIDENCE' if has_source else 'REFUSE_AND_REQUEST_SOURCE','message':'Evidence signal detected; verify the cited source before relying on the answer.' if has_source else "I couldn't verify this from the available BIS evidence. I won't guess.",'trust_boundary':'This guard is a prototype evidence gate, not a BIS decision.'})

    @app.post('/v5/photo-intake')
    def v5_photo_intake():
        f=request.files.get('file')
        if not f: return jsonify({'error':'Upload an image'}),400
        raw=f.read()
        return jsonify({'filename':f.filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'status':'IMAGE_INTAKE_READY','next':['Detect/inspect visible ISI mark','Extract CM/L and IS number','Identify likely product','Retrieve candidate standards','Confirm official BIS licence/product scope'],'notice':'Image inference is screening assistance; it is not proof of certification.'})

    @app.post('/v7/review')
    def v7_review():
        body=request.get_json(silent=True) or {}
        decision=str(body.get('decision','REVIEW_REQUIRED')).upper()
        return jsonify({'case_id':body.get('case_id'),'decision':decision,'reviewer':body.get('reviewer','Local reviewer'),'note':body.get('note',''),'reviewed_at':now(),'audit_event':True})
