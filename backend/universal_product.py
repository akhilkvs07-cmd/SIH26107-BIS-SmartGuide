from flask import request, jsonify

# User-language aliases are deliberately kept separate from standards. They help
# retrieval understand common names without pretending that a synonym itself proves
# a standard is applicable.
PRODUCT_ALIASES = {
    'mobile phone': ['mobile phone', 'smartphone', 'cell phone', 'handset', 'mobile handset', 'smart phone'],
    'phone': ['phone', 'mobile phone', 'smartphone', 'cell phone', 'handset'],
    'smartphone': ['smartphone', 'mobile phone', 'cell phone', 'handset'],
    'laptop': ['laptop', 'notebook computer', 'portable computer'],
    'fridge': ['fridge', 'refrigerator'],
    'gas stove': ['gas stove', 'lpg stove', 'gas cooker', 'chulha'],
    'electric kettle': ['electric kettle', 'water kettle', 'electric water boiler'],
    'pvc cable': ['pvc cable', 'pvc wire', 'insulated cable'],
}

# These are retrieval hints, not final applicability decisions. The returned
# workflow always asks the user to verify exact scope/clauses and QCO status.
CORPUS_HINTS = {
    'mobile phone': ['IS/IEC 62368-1: 2023', 'IS 16046 (Part 2)', 'IS 16102 (Part 1 & 2)'],
    'smartphone': ['IS/IEC 62368-1: 2023', 'IS 16046 (Part 2)', 'IS 16102 (Part 1 & 2)'],
    'cell phone': ['IS/IEC 62368-1: 2023', 'IS 16046 (Part 2)', 'IS 16102 (Part 1 & 2)'],
    'handset': ['IS/IEC 62368-1: 2023', 'IS 16046 (Part 2)', 'IS 16102 (Part 1 & 2)'],
}


def _unique(items):
    out, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get('standard_number') or item.get('standard') or item.get('id') or item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _hint_matches(query, find_matches):
    """Use known corpus standard identifiers as a retrieval bridge for common terms."""
    low = query.lower().strip()
    hints = []
    for alias, standards in CORPUS_HINTS.items():
        if alias in low:
            for std in standards:
                try:
                    hints.extend(find_matches(std, 5) or [])
                except Exception:
                    pass
    return _unique(hints)


def register_universal(app, find_matches):
    @app.post('/v7/product-intelligence')
    def universal_product_intelligence():
        body = request.get_json(silent=True) or {}
        product = str(body.get('product', '')).strip()
        description = str(body.get('description', '')).strip()
        query = ' '.join(x for x in (product, description) if x).strip()
        if not query:
            return jsonify({'error': 'Enter a product name or description'}), 400

        expanded = [query]
        low = query.lower()
        for alias, variants in PRODUCT_ALIASES.items():
            if alias in low:
                expanded.extend(variants)

        matches = []
        for candidate in expanded:
            try:
                matches.extend(find_matches(candidate, 10) or [])
            except Exception:
                continue
        matches = _unique(matches)

        # If ordinary lexical retrieval cannot connect a common product name to
        # the indexed corpus, bridge through standards that are already present.
        if not matches:
            matches = _hint_matches(query, find_matches)

        usable = [m for m in matches if isinstance(m, dict)]
        hint_used = bool(usable and any(alias in low for alias in CORPUS_HINTS))
        classification = 'BIS-EVIDENCE-BACKED' if usable else 'INSUFFICIENT-BIS-EVIDENCE'
        response = {
            'query': query,
            'supported': bool(usable),
            'classification': classification,
            'candidate_standards': usable,
            'workflow': [
                'Identify product and scope',
                'Review candidate Indian Standards',
                'Verify exact scope and clauses',
                'Check QCO / certification applicability',
                'Run compliance checks only after requirements are verified'
            ],
            'refusal': None if usable else 'No sufficiently supported BIS match was found in the available corpus. SmartGuide will not guess a standard.',
            'retrieval_note': 'Common product wording was expanded to improve retrieval.' if hint_used else None,
            'trust_boundary': 'Decision support only. This result is not a BIS certification, licence verification, or legal determination.'
        }
        return jsonify(response)
