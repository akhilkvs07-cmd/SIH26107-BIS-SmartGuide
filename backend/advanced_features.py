"""BIS SmartGuide Advanced Intelligence Layer.

Production-safe, source-grounded workflows for SIH 26107.  The layer performs
local intelligence and engineering screening; it never pretends to be an
official BIS certification or registry decision.
"""
import hashlib, os, re, struct
from datetime import datetime, timezone
from flask import jsonify, request

BIS_QCO = "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en"
BIS_LABS = "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"
BIS_LIMS = "https://lims.bis.gov.in/"
BIS_LIMS_IS = "https://lims.bis.gov.in/home/search_is_number/"
BIS_STANDARDS = "https://standards.bis.gov.in/"
BIS_KYS = "https://www.bis.gov.in/know-your-standard/?lang=en"
BIS_APPLY = "https://www.bis.gov.in/apply-for-a-license/?lang=en"

VERSION = "8.0"

def now():
    return datetime.now(timezone.utc).isoformat()

def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())

def norm(value):
    return clean(value).lower()

def sources():
    return [
        {"name": "BIS Standards Portal", "url": BIS_STANDARDS},
        {"name": "BIS Know Your Standard", "url": BIS_KYS},
        {"name": "BIS QCO / Compulsory Certification", "url": BIS_QCO},
        {"name": "BIS Recognised Laboratories", "url": BIS_LABS},
        {"name": "BIS LIMS", "url": BIS_LIMS},
        {"name": "BIS Licence Guidance", "url": BIS_APPLY},
    ]

def base_result(feature, status="SUCCESS"):
    return {"feature": feature, "layer_version": VERSION, "status": status,
            "generated_at": now(), "sources": sources(),
            "prototype_notice": "AI-assisted screening only. Verify the current applicable BIS standard, amendment, QCO and official registry before acting."}

def require_text(body, field, label):
    value = clean(body.get(field, ""))
    if not value:
        raise ValueError(label + " is required")
    return value

def verify_mark(body):
    text = clean(body.get("text")); licence = clean(body.get("licence"))
    blob = norm(text + " " + licence)
    isi = bool(re.search(r"\bisi\b|\bis\s*[:#-]?\s*\d{3,6}\b", blob))
    cml = bool(re.search(r"\bcm\s*[/\- ]\s*l\b", blob))
    nums = re.findall(r"\bcm\s*[/\- ]\s*l\s*[:#-]?\s*(\d{4,12})\b", blob)
    out = base_result("ISI / CM-L verification", "REQUIRES_OFFICIAL_VERIFICATION")
    out.update({"isi_mark_detected": isi, "cm_l_detected": cml, "cm_l_numbers": nums,
                "checks": ["mark presence", "licence number format", "product/scope match", "manufacturer details", "current licence validity"],
                "official_verification": "Use BIS official verification services before treating a mark or licence as genuine."})
    return out

def label_check(body):
    text = norm(body.get("text"))
    patterns = {
        "product_name": [r"\bproduct\b", r"\bname\b"],
        "manufacturer": [r"manufacturer", r"manufactured by", r"mfg\.?"],
        "model": [r"model(?:\s*(?:no|number))?\b"],
        "standard_reference": [r"\bis\s*[:#-]?\s*\d{3,6}\b", r"indian standard"],
        "mark_or_licence": [r"\bisi\b", r"cm\s*[/\- ]\s*l", r"licen[cs]e", r"registration"],
        "ratings": [r"\b\d+(?:\.\d+)?\s*(?:v|volt|volts|w|watt|watts|a|amp|amps|hz|kg|g|l|litre|liter|ml)\b"],
    }
    detected = {k: any(re.search(p, text) for p in ps) for k, ps in patterns.items()}
    out = base_result("Label / packaging screening", "REVIEW")
    out.update({"fields_detected": detected, "missing_or_unclear": [k for k,v in detected.items() if not v],
                "note": "Required markings vary by product and applicable standard/QCO. This is a screening aid, not a certification decision."})
    return out

def test_report(body):
    text = clean(body.get("text")); standard = clean(body.get("standard"))
    if not text: raise ValueError("Test report text is required")
    measurements=[]
    pattern = re.compile(r"([A-Za-z][A-Za-z0-9 _()/%.-]{1,45}?)\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*([A-Za-z%°µΩ/.-]+)?", re.I)
    for m in pattern.finditer(text):
        try: value=float(m.group(2))
        except ValueError: continue
        measurements.append({"parameter":clean(m.group(1)),"value":value,"unit":m.group(3) or ""})
    out=base_result("Test-report intelligence", "PARSED_NEEDS_STANDARD_LIMITS" if measurements else "NO_MEASUREMENTS_FOUND")
    out.update({"standard":standard or None,"measurements":measurements[:200],"parsed_measurements":len(measurements),
                "sanity_pass_count":sum(x["value"] >= 0 for x in measurements),
                "next_step":"Compare each parameter with the exact limit, test method, tolerance and sampling rule in the applicable standard. The system intentionally does not invent limits."})
    return out

def product_intelligence(body, find_matches):
    description=require_text(body,"description","Product description")
    matches=find_matches(description,8)
    top=matches[0].get("match_score",0) if matches else 0
    out=base_result("Product intelligence", "MATCHED" if matches else "NO_MATCH")
    out.update({"description":description,"ranked_standards":matches,"confidence":round(min(.99,top/100),3),
                "needs_human_review":not matches or top < 60,
                "evidence": ["local BIS standards corpus", "product terminology match"] if matches else []})
    return out

def lab_match(body, find_matches):
    product=clean(body.get("product")); standard=clean(body.get("standard")); test=clean(body.get("test"))
    if not any((product,standard,test)): raise ValueError("Product, IS number or test is required")
    query=standard or product or test
    candidates=find_matches(query,8)
    out=base_result("Laboratory intelligence", "SCOPE_LOOKUP_REQUIRED")
    out.update({"query":{"product":product,"standard":standard,"test":test},"candidate_standards":candidates,
                "official_lab_search":BIS_LIMS_IS,"official_lab_directory":BIS_LABS,
                "matching_rule":"Confirm the exact IS number and test field in current BIS LIMS scope before selecting a laboratory."})
    return out

def amendment_impact(body, find_matches):
    amendment=clean(body.get("amendment")); product=clean(body.get("product")); standard=clean(body.get("standard"))
    if not any((amendment,product,standard)): raise ValueError("Standard, product or amendment text is required")
    query=standard or product or amendment
    candidates=find_matches(query,8)
    text=norm(amendment)
    keywords={"requirements": ["requirement","shall","specification","limit"],"testing": ["test","testing","method","sampling"],"marking": ["marking","label","isi","cm/l"],"qco": ["qco","compulsory","mandatory"],"documentation": ["document","record","report"]}
    impact={k:any(w in text for w in ws) for k,ws in keywords.items()}
    out=base_result("QCO / amendment impact", "IMPACT_SCREENING")
    out.update({"amendment":amendment,"product":product,"standard":standard,"affected_candidates":candidates,
                "detected_impact_areas":[k for k,v in impact.items() if v] or list(impact),
                "verification":"Confirm the latest amendment, effective date and official notification on BIS/Government sources."})
    return out

def _ascii_stl(raw):
    text=raw.decode("utf-8","ignore")
    verts=[]
    for x,y,z in re.findall(r"\bvertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",text,re.I):
        verts.append((float(x),float(y),float(z)))
    return verts

def _binary_stl(raw):
    if len(raw)<84: return []
    try: count=struct.unpack_from("<I",raw,80)[0]
    except struct.error: return []
    expected=84+50*count
    if count==0 or expected>len(raw): return []
    verts=[]; off=84
    for _ in range(count):
        off+=12
        for _ in range(3): verts.append(struct.unpack_from("<fff",raw,off)); off+=12
        off+=2
    return verts

def stl_scan(file_storage, body):
    raw=file_storage.read(); name=os.path.basename(file_storage.filename or "model.stl")
    if not raw: raise ValueError("STL file is empty")
    verts=_ascii_stl(raw) if b"vertex" in raw[:20000].lower() else []
    fmt="ASCII STL"
    if not verts:
        verts=_binary_stl(raw); fmt="Binary STL" if verts else "Unsupported/invalid STL"
    dimensions=None
    if verts:
        dimensions={axis:max(v[i] for v in verts)-min(v[i] for v in verts) for i,axis in enumerate(("x","y","z"))}
    checks=[]
    for axis in ("x","y","z"):
        value=body.get("max_"+axis)
        if value not in (None,"") and dimensions:
            try:
                limit=float(value); measured=dimensions[axis]
                checks.append({"axis":axis,"measured":measured,"limit":limit,"pass":measured<=limit})
            except ValueError: checks.append({"axis":axis,"error":"Invalid dimension limit"})
    out=base_result("3D CAD / STL engineering screen", "ENGINEERING_SCREEN" if verts else "GEOMETRY_PARSE_REQUIRED")
    out.update({"filename":name,"bytes":len(raw),"format":fmt,"triangle_count":len(verts)//3,
                "bounding_box":dimensions,"dimensional_checks":checks,
                "sha256":hashlib.sha256(raw).hexdigest(),
                "note":"Geometry measurements are engineering pre-checks. They do not establish BIS conformity."})
    return out

def procurement(body, find_matches):
    product=clean(body.get("product")); hs=clean(body.get("hs_code")); raw=clean(body.get("raw_material"))
    if not any((product,hs,raw)): raise ValueError("Product, HS code or raw material is required")
    hs_valid=bool(re.fullmatch(r"\d{4,8}",hs)) if hs else None
    matches=find_matches((product+" "+raw).strip(),8) if product or raw else []
    out=base_result("Procurement intelligence", "PROCUREMENT_REVIEW")
    out.update({"product":product,"hs_code":hs or None,"hs_code_format_valid":hs_valid,"raw_material":raw or None,
                "ranked_standards":matches,
                "checks":["applicable Indian Standard","current QCO/mandatory status","licence scope","test evidence","marking","supplier documentation"],
                "note":"HS-code classification and legal/mandatory status must be verified against current official customs/BIS sources."})
    return out

def issue_report(body):
    product=clean(body.get("product")); issue=clean(body.get("issue"))
    if not issue: raise ValueError("Issue description is required")
    seed=product+"|"+issue+"|"+now()
    case="CASE-"+hashlib.sha256(seed.encode()).hexdigest()[:10].upper()
    out=base_result("Issue / counterfeit report", "DRAFT_CREATED")
    out.update({"case_id":case,"product":product,"issue":issue,
                "recommended_evidence":["product photographs","label / ISI / CM-L details","purchase evidence where appropriate","test report if available","manufacturer details"],
                "submission":"This creates a report draft only. User action is required to submit a complaint through official BIS channels."})
    return out

def register(app, find_matches):
    def call(fn):
        try: return jsonify(fn(request.get_json(silent=True) or {}))
        except ValueError as exc: return jsonify({"error":str(exc)}),400
        except Exception as exc: return jsonify({"error":"Workflow failed","details":str(exc)}),500

    @app.post('/v5/verify-mark')
    def v5_verify_mark(): return call(verify_mark)
    @app.post('/v5/label-check')
    def v5_label_check(): return call(label_check)
    @app.post('/v5/test-report')
    def v5_test_report(): return call(test_report)
    @app.post('/v5/product-intelligence')
    def v5_product_intelligence(): return call(lambda b: product_intelligence(b,find_matches))
    @app.get('/v5/lab-match')
    def v5_lab_match():
        try: return jsonify(lab_match(request.args,find_matches))
        except ValueError as exc: return jsonify({"error":str(exc)}),400
    @app.post('/v5/amendment-impact')
    def v5_amendment_impact(): return call(lambda b: amendment_impact(b,find_matches))
    @app.post('/v5/stl-scan')
    def v5_stl_scan():
        f=request.files.get('file')
        if not f: return jsonify({'error':'Upload an STL file'}),400
        try: return jsonify(stl_scan(f,request.form))
        except ValueError as exc: return jsonify({'error':str(exc)}),400
        except Exception as exc: return jsonify({'error':'STL scan failed','details':str(exc)}),500
    @app.post('/v5/procurement')
    def v5_procurement(): return call(lambda b: procurement(b,find_matches))
    @app.post('/v5/issue-report')
    def v5_issue_report(): return call(issue_report)

    @app.get('/v5/feature-status')
    def v5_feature_status():
        features=[
            ('Product → ranked standards','FUNCTIONAL'),('ISI / CM-L screening','FUNCTIONAL'),('Test-report parsing','FUNCTIONAL'),
            ('Laboratory scope workflow','FUNCTIONAL + OFFICIAL LOOKUP'),('QCO / amendment impact screening','FUNCTIONAL'),
            ('ASCII + binary STL scanner','FUNCTIONAL'),('Label / packaging screening','FUNCTIONAL'),('Procurement screening','FUNCTIONAL'),
            ('Issue / counterfeit case drafting','FUNCTIONAL'),('HS-code format screening','FUNCTIONAL'),('Raw-material → standards matching','FUNCTIONAL'),
            ('Evidence / compliance layer','FUNCTIONAL VIA V4'),('Multilingual / voice UI','FUNCTIONAL VIA EXISTING UI'),
            ('Official BIS registry verification','OFFICIAL SOURCE REQUIRED'),('Official complaint submission','USER ACTION REQUIRED'),
            ('BIS certification decision','NEVER AUTOMATED')]
        return jsonify({'version':VERSION,'features':[{'feature':a,'status':b} for a,b in features], 'generated_at':now(),'sources':sources()})

    @app.get('/v5/self-test')
    def v5_self_test():
        tests=[]
        try:
            m=find_matches('electric kettle 1200W',1); tests.append({'name':'standards matcher','ok':bool(m)})
        except Exception as e: tests.append({'name':'standards matcher','ok':False,'error':str(e)})
        for name,fn,payload in [
            ('mark parser',verify_mark,{'text':'ISI IS 302 CM/L-1234567'}),
            ('label parser',label_check,{'text':'Electric Kettle Manufacturer ABC Model EK-1200 IS 302 1200 W 230 V ISI'}),
            ('test parser',test_report,{'text':'Voltage: 230 V Power: 1200 W','standard':'IS 302'}),
            ('issue draft',issue_report,{'product':'kettle','issue':'suspected counterfeit label'}),
        ]:
            try: fn(payload); tests.append({'name':name,'ok':True})
            except Exception as e: tests.append({'name':name,'ok':False,'error':str(e)})
        return jsonify({'version':VERSION,'ok':all(x['ok'] for x in tests),'tests':tests,'generated_at':now()})

    @app.get('/v5/sources')
    def v5_sources(): return jsonify({'sources':sources(),'generated_at':now()})
