"""BIS SmartGuide V6 advanced intelligence layer.

This module adds practical prototype workflows around verification, testing,
laboratories, product engineering, amendments, workspaces and auditability.
It deliberately labels decisions that require live BIS verification instead of
pretending that a local prototype is an official BIS registry.
"""
import os, re, hashlib
from datetime import datetime, timezone
from flask import request, jsonify

BIS_QCO = "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en"
BIS_LABS = "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"
BIS_LIMS = "https://lims.bis.gov.in/"
BIS_STANDARDS = "https://standards.bis.gov.in/"
BIS_KYS = "https://www.bis.gov.in/know-your-standard/?lang=en"
BIS_APPLY = "https://www.bis.gov.in/apply-for-a-license/?lang=en"

def now(): return datetime.now(timezone.utc).isoformat()
def norm(x): return re.sub(r"\s+", " ", str(x or "").strip().lower())

def source_pack():
    return [
        {"name":"BIS Standards Portal","url":BIS_STANDARDS},
        {"name":"Know Your Standard","url":BIS_KYS},
        {"name":"BIS QCO / Compulsory Certification","url":BIS_QCO},
        {"name":"BIS Recognised Laboratories","url":BIS_LABS},
        {"name":"BIS LIMS","url":BIS_LIMS},
        {"name":"Apply for BIS Licence","url":BIS_APPLY},
    ]

def verify_mark(body):
    text=str(body.get("text","")); licence=str(body.get("licence","")); blob=norm(text+" "+licence)
    has_isi=bool(re.search(r"\bisi\b|is\s*\d{3,6}",blob)); has_cml=bool(re.search(r"\b(?:cm\/l|cm-l|cm l)\b",blob))
    nums=re.findall(r"\b(?:cm\/l|cm-l|cm l)\s*[:#-]?\s*([0-9]{4,12})\b",blob)
    return {"status":"REQUIRES_OFFICIAL_VERIFICATION","isi_mark_detected":has_isi,"cm_l_detected":has_cml,"cm_l_numbers":nums,"checks":["Mark presence and formatting","Licence/registration validity","Scope/product coverage","Manufacturer details"],"official_verification":"Use official BIS genuineness/licence services before accepting a product as certified.","sources":source_pack(),"generated_at":now()}

def label_check(body):
    text=norm(body.get("text","")); required={"product_name":["product","name"],"manufacturer":["manufacturer","manufactured by","mfg"],"model":["model","model no","model number"],"standard_reference":["is ","indian standard","standard"],"mark_or_licence":["isi","cm/l","licence","license","registration"],"ratings":["v","volt","w","watt","kg","capacity","hz"]}
    result={k:any(v in text for v in vals) for k,vals in required.items()}; missing=[k for k,ok in result.items() if not ok]
    return {"status":"REVIEW","fields_detected":result,"missing_or_unclear":missing,"notice":"Label checks are screening assistance only; product-specific marking rules must be verified against the applicable Indian Standard, product manual and QCO.","sources":source_pack(),"generated_at":now()}

def test_report(body):
    text=str(body.get("text","")); standard=str(body.get("standard","")); measurements=[]
    for m in re.finditer(r"([A-Za-z][A-Za-z0-9 _/-]{1,35})\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*([A-Za-z%°/]+)?",text): measurements.append({"parameter":m.group(1).strip(),"value":float(m.group(2)),"unit":m.group(3) or ""})
    return {"standard":standard or None,"measurements":measurements[:100],"parsed_measurements":len(measurements),"sanity_pass_count":sum(1 for x in measurements if x["value"]>=0),"status":"PARSED_NEEDS_STANDARD_LIMITS" if measurements else "NO_MEASUREMENTS_FOUND","next_step":"Compare every reported parameter against the exact limits, test method and sampling rules in the applicable standard/product manual.","notice":"The parser does not invent pass/fail limits.","sources":source_pack(),"generated_at":now()}

def lab_match(body,find_matches):
    product=str(body.get("product","")).strip(); standard=str(body.get("standard"," ")).strip(); test=str(body.get("test"," ")).strip(); q=standard or product or test; matches=find_matches(q,5) if q else []
    return {"query":{"product":product,"standard":standard,"test":test},"candidate_standards":matches,"lab_matching":{"status":"OFFICIAL_SCOPE_LOOKUP_REQUIRED","rule":"Match the exact IS/test facility scope in the current BIS laboratory directory/LIMS.","lims":BIS_LIMS,"directory":BIS_LABS},"sources":source_pack(),"generated_at":now()}

def product_intelligence(body,find_matches):
    description=str(body.get("description","")).strip(); matches=find_matches(description,8) if description else []; top=matches[0].get("match_score",0) if matches else 0
    return {"description":description,"ranked_standards":matches,"confidence":min(.99,top/100),"evidence":["local standards corpus match","keyword/product terminology match"] if matches else [],"needs_human_review":not matches or top<60,"sources":source_pack(),"generated_at":now()}

def amendment_impact(body,find_matches):
    amendment=str(body.get("amendment"," ")).strip(); product=str(body.get("product"," ")).strip(); standard=str(body.get("standard"," ")).strip(); q=standard or product or amendment; matches=find_matches(q,5) if q else []
    return {"status":"IMPACT_SCREENING","amendment":amendment,"product":product,"standard":standard,"affected_candidates":matches,"impact_areas":["requirements","testing","marking","technical documentation","QCO applicability","lab scope"],"verification":"Confirm the latest amendment and effective date on official BIS/Government sources.","sources":source_pack(),"generated_at":now()}

def stl_scan(file_storage,body):
    raw=file_storage.read(); name=os.path.basename(file_storage.filename or "model.stl"); text=raw.decode("utf-8","ignore"); verts=[]
    if text.lstrip().lower().startswith("solid"):
        for x,y,z in re.findall(r"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",text,re.I): verts.append((float(x),float(y),float(z)))
    triangles=len(verts)//3; dimensions=None
    if verts: dimensions={"x":max(v[0] for v in verts)-min(v[0] for v in verts),"y":max(v[1] for v in verts)-min(v[1] for v in verts),"z":max(v[2] for v in verts)-min(v[2] for v in verts)}
    expected={axis:body.get(f"max_{axis}") for axis in ("x","y","z") if body.get(f"max_{axis}") not in (None,"")}; checks=[]
    if dimensions:
        for axis,limit in expected.items():
            try: checks.append({"axis":axis,"measured":dimensions[axis],"limit":float(limit),"pass":dimensions[axis]<=float(limit)})
            except (TypeError,ValueError): pass
    return {"filename":name,"bytes":len(raw),"format":"ASCII STL" if verts else "STL/unsupported geometry parser","triangle_count":triangles,"bounding_box":dimensions,"dimensional_checks":checks,"status":"ENGINEERING_SCREEN" if verts else "GEOMETRY_PARSE_REQUIRED","notice":"This is an engineering pre-check, not a BIS conformity determination. Standard-specific tolerances must be supplied and verified.","sha256":hashlib.sha256(raw).hexdigest(),"generated_at":now()}

def procurement(body,find_matches):
    product=str(body.get("product","")).strip(); hs=str(body.get("hs_code","")).strip(); raw=str(body.get("raw_material","")).strip(); matches=find_matches(product+" "+raw,5) if product or raw else []
    return {"product":product,"hs_code":hs or None,"raw_material":raw or None,"standards":matches,"checks":["applicable Indian Standard","QCO/mandatory status","manufacturer licence scope","test evidence","marking","supplier documentation"],"status":"PROCUREMENT_REVIEW","notice":"HS-code and supplier decisions require verification against current customs/QCO/product scope data.","sources":source_pack(),"generated_at":now()}

def report_issue(body):
    issue=str(body.get("issue","")).strip(); product=str(body.get("product","")).strip(); issue_id="CASE-"+hashlib.sha256((issue+product+now()).encode()).hexdigest()[:10].upper()
    return {"case_id":issue_id,"status":"DRAFT_REPORT","product":product,"issue":issue,"recommended_evidence":["product photos","label/ISI/CM-L details","purchase proof where appropriate","test report if available","manufacturer details"],"notice":"This creates a structured draft for reporting; it does not submit a complaint to BIS automatically.","sources":source_pack(),"created_at":now()}

def register(app,find_matches):
    @app.post('/v5/verify-mark')
    def v5_verify_mark(): return jsonify(verify_mark(request.get_json(silent=True) or {}))
    @app.post('/v5/label-check')
    def v5_label_check(): return jsonify(label_check(request.get_json(silent=True) or {}))
    @app.post('/v5/test-report')
    def v5_test_report(): return jsonify(test_report(request.get_json(silent=True) or {}))
    @app.get('/v5/lab-match')
    def v5_lab_match(): return jsonify(lab_match(request.args,find_matches))
    @app.post('/v5/product-intelligence')
    def v5_product_intelligence(): return jsonify(product_intelligence(request.get_json(silent=True) or {},find_matches))
    @app.post('/v5/amendment-impact')
    def v5_amendment_impact(): return jsonify(amendment_impact(request.get_json(silent=True) or {},find_matches))
    @app.post('/v5/stl-scan')
    def v5_stl_scan():
        f=request.files.get('file')
        if not f: return jsonify({'error':'Upload an STL file'}),400
        return jsonify(stl_scan(f,request.form))
    @app.post('/v5/procurement')
    def v5_procurement(): return jsonify(procurement(request.get_json(silent=True) or {},find_matches))
    @app.post('/v5/issue-report')
    def v5_issue_report(): return jsonify(report_issue(request.get_json(silent=True) or {}))
    @app.get('/v5/feature-status')
    def v5_feature_status():
        features=[('MSME / manufacturer workspace','ACTIVE'),('ISI + CM/L verification','ACTIVE'),('Counterfeit / issue reporting','ACTIVE'),('3D CAD / STL engineering scanner','ACTIVE'),('Test-report intelligence','ACTIVE'),('Intelligent laboratory matching','ACTIVE'),('QCO / amendment monitoring hooks','ACTIVE'),('Amendment impact analysis','ACTIVE'),('Procurement intelligence','ACTIVE'),('HS-code assisted screening','ACTIVE'),('Raw-material → standard intelligence','ACTIVE'),('Product description → ranked standards','ACTIVE'),('Label / packaging compliance screening','ACTIVE'),('Clause/evidence workflow','ACTIVE VIA V4'),('Compliance passport / audit trail','ACTIVE VIA V4'),('Multilingual UI / voice hooks','ACTIVE IN EXISTING UI'),('Offline/mobile-ready API surface','READY'),('Hybrid retrieval architecture','READY FOR RERANKER'),('Human review workflow','ACTIVE VIA REVIEW STATUS'),('Organization / multi-user workspace','READY FOR AUTH PROVIDER'),('Live BIS registry verification','OFFICIAL SOURCE REQUIRED'),('Live Gazette watcher','SOURCE INTEGRATION REQUIRED'),('Official complaint submission','USER ACTION REQUIRED'),('BIS certification decision','NEVER AUTOMATED')]
        return jsonify({'version':'6.0','generated_at':now(),'features':[{'feature':a,'status':b} for a,b in features],'sources':source_pack()})
    @app.get('/v5/sources')
    def v5_sources(): return jsonify({'sources':source_pack(),'generated_at':now()})
