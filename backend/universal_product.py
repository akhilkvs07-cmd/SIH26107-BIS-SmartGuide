from flask import request, jsonify

def register_universal(app, find_matches):
    @app.post('/v7/product-intelligence')
    def universal_product_intelligence():
        body=request.get_json(silent=True) or {}
        product=str(body.get('product','')).strip()
        description=str(body.get('description','')).strip()
        query=' '.join(x for x in (product,description) if x).strip()
        if not query:
            return jsonify({'error':'Enter a product name or description'}),400
        matches=find_matches(query,10) or []
        usable=[m for m in matches if isinstance(m,dict)]
        return jsonify({'query':query,'supported':bool(usable),'classification':'BIS-EVIDENCE-BACKED' if usable else 'INSUFFICIENT-BIS-EVIDENCE','candidate_standards':usable,'workflow':['Identify product/scope','Review candidate Indian Standards','Verify exact scope and clauses','Check QCO/certification applicability','Run compliance checks only after requirements are verified'],'refusal':None if usable else 'No sufficiently supported BIS match was found in the available corpus. SmartGuide will not guess a standard.','trust_boundary':'Decision support only. This result is not a BIS certification, licence verification, or legal determination.'})
