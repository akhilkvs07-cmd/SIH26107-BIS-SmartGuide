"""BIS SmartGuide Core Product Intelligence Layer.

Implements:
- Typo tolerance and spelling normalization
- 5-Tier product existence classification:
    1. CONFIDENTLY_RECOGNIZED
    2. POSSIBLE_PRODUCT
    3. RELATED_PRODUCT
    4. UNCERTAIN
    5. NON_PRODUCT
- Unknown product category inference and refusal boundaries
- Natural-language product description parsing
- Ambiguity detection and clarifying option generation
"""

import re
from typing import Any, Dict, List, Optional, Tuple

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "what", "which", "with", "my", "our", "can", "do", "does", "about", "tell",
    "me", "please", "product", "used", "use", "manufactured", "manufacturing",
    "made", "we", "make", "producing", "small", "device", "equipment"
}

NON_PRODUCT_TERMS = {
    "happiness", "love", "peace", "anger", "sadness", "freedom", "democracy",
    "python", "javascript", "java", "c++", "software", "code", "algorithm",
    "script", "marketing", "accounting", "service", "consulting", "strategy",
    "idea", "concept", "philosophy", "weather", "music", "song", "movie",
    "blockchain", "crypto", "bitcoin", "nft", "ai model", "neural network",
    "cloud computing", "saas", "law", "legal advice", "management"
}

PHYSICAL_PRODUCT_NOUNS = {
    "stove", "kettle", "iron", "cable", "wire", "helmet", "cooker", "fryer",
    "hob", "plate", "board", "socket", "plug", "switch", "fan", "mixer",
    "grinder", "microwave", "oven", "heater", "geyser", "lamp", "lantern",
    "bulb", "battery", "cell", "refrigerator", "fridge", "washer", "machine",
    "cooler", "conditioner", "steamer", "bottle", "jar", "toy", "bar", "sheet",
    "warmer", "boiler", "cleaner", "purifier", "filter", "generator", "panel",
    "pump", "motor", "pipe", "tube", "valve", "device", "appliance", "box"
}

AMBIGUOUS_TERMS = {
    "heater": {
        "term": "heater",
        "question": "The term 'heater' is broad. Which specific type of heater are you referring to?",
        "options": [
            {"label": "Electric Room Heater / Radiant Heater", "product": "room heater", "standard": "IS 302 (Part 2/Sec 30)"},
            {"label": "Stationary Storage Water Heater (Geyser)", "product": "storage water heater geyser", "standard": "IS 2082"},
            {"label": "Electric Immersion Water Heating Rod", "product": "immersion water heater", "standard": "IS 368"},
            {"label": "Solar Water Heater System", "product": "solar water heater flat plate collector", "standard": "IS 12933"}
        ]
    },
    "fan": {
        "term": "fan",
        "question": "Which type of electric fan are you evaluating?",
        "options": [
            {"label": "Electric Ceiling Fan", "product": "ceiling fan", "standard": "IS 374"},
            {"label": "Table / Pedestal / Desk Fan", "product": "table fan", "standard": "IS 555"}
        ]
    },
    "cooker": {
        "term": "cooker",
        "question": "Which type of cooking equipment do you mean?",
        "options": [
            {"label": "Domestic Pressure Cooker (Aluminium/Steel)", "product": "domestic pressure cooker", "standard": "IS 2347"},
            {"label": "Domestic Gas Stove / LPG Chulha", "product": "domestic gas stove", "standard": "IS 4246"},
            {"label": "Electric Rice Cooker / Liquid Boiler", "product": "electric kettle", "standard": "IS 302 (Part 2/Sec 15)"},
            {"label": "Solar Box Cooker / Warmer", "product": "solar food warmer cooker", "standard": "IS 13129"}
        ]
    },
    "wire": {
        "term": "wire",
        "question": "Which cable or conductor category applies?",
        "options": [
            {"label": "PVC Insulated Cable for Domestic Wiring", "product": "pvc insulated cable", "standard": "IS 694"},
            {"label": "Plugs, Sockets and Extension Cords", "product": "plug and socket outlet smart extension board", "standard": "IS 1293"}
        ]
    },
    "water": {
        "term": "water",
        "question": "What type of water supply or product are you testing?",
        "options": [
            {"label": "Drinking Water (Municipal/Tap Specification)", "product": "drinking water", "standard": "IS 10500"},
            {"label": "Packaged Drinking Water (Bottled/Jar Commercial)", "product": "packaged drinking water", "standard": "IS 14543"}
        ]
    }
}

NL_DESCRIPTIONS = [
    (r"(?:boil|heating)\s+(?:water|liquid|milk|tea)|appliance\s+used\s+to\s+boil\s+water", "electric kettle", "IS 302 (Part 2/Sec 15)"),
    (r"(?:ironing|press(?:ing)?|steam(?:ing)?)\s+(?:clothes|fabric|garment)|clothes\s+iron", "electric iron", "IS 302 (Part 2/Sec 3)"),
    (r"cooking\s+(?:with|using)?\s*(?:gas|lpg)|burn(?:ing)?\s+lpg|gas\s+chulha", "domestic gas stove", "IS 4246"),
    (r"(?:house|household|building|domestic)\s+(?:electrical\s+)?wiring|pvc\s+(?:copper\s+)?(?:wire|cable)", "pvc insulated cable", "IS 694"),
    (r"(?:head\s+protection|rider\s+protection|two\s+wheeler\s+rider|motorcycle\s+riding)", "motorcycle helmet", "IS 4151"),
    (r"(?:cook(?:ing)?\s+under\s+pressure|steam\s+pressure\s+cooker|pressure\s+vessel\s+for\s+food)", "domestic pressure cooker", "IS 2347"),
    (r"(?:hot\s+air\s+fry|oil\s*less\s+fry|air\s+circulation\s+cooking|crispy\s+air\s+cook)", "air fryer toaster grill", "IS 302 (Part 2/Sec 9)"),
    (r"(?:magnetic\s+induction|induction\s+coil\s+cook|electromagnetic\s+hob|smart\s+induction)", "smart induction cooking plate", "IS 302 (Part 2/Sec 6)"),
    (r"(?:multi\s*plug\s+extension|surge\s+protect(?:or|ion)|extension\s+strip|power\s+strip)", "plug and socket outlet smart extension board", "IS 1293"),
    (r"(?:rechargeable\s+emergency|backup\s+light\s+during\s+power\s+cut|emergency\s+lantern)", "rechargeable emergency lamp", "IS 10322 (Part 5/Sec 8)"),
    (r"(?:solar\s+water\s+heat|solar\s+thermal\s+geyser|flat\s+plate\s+solar\s+collector)", "solar water heater flat plate collector", "IS 12933"),
    (r"(?:vertical\s+steam|wrinkle\s+remover\s+for\s+fabric|handheld\s+garment\s+steamer)", "portable garment steamer", "IS 302 (Part 2/Sec 85)"),
    (r"(?:blend(?:ing)?|liquidiz(?:ing)?|grind(?:ing)?\s+spices|food\s+mixer)", "mixer grinder", "IS 4250"),
    (r"(?:keep\s+food\s+warm\s+using\s+solar|solar\s+(?:energy\s+)?food\s+warm|box\s+solar\s+cook)", "solar food warmer cooker", "IS 13129")
]

TYPO_MAP = {
    "gas stve": "gas stove",
    "elec kettle": "electric kettle",
    "electic kettle": "electric kettle",
    "electrik kettle": "electric kettle",
    "electic iron": "electric iron",
    "pvc cabel": "pvc cable",
    "pvc cabl": "pvc cable",
    "hlmet": "helmet",
    "helmit": "helmet",
    "pressur cooker": "pressure cooker",
    "presure cooker": "pressure cooker",
    "indution": "induction",
    "inductin": "induction",
    "indution cooktop": "induction cooktop",
    "smart cooktop": "smart induction cooking plate",
    "smart cooking plate": "smart induction cooking plate",
    "rechargable lamp": "rechargeable emergency lamp",
    "emergeny light": "rechargeable emergency lamp",
    "garment stemer": "garment steamer",
    "watter heater": "water heater",
    "ceeling fan": "ceiling fan",
    "microwav": "microwave oven"
}

def clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())

def normalize_query(text: Any) -> str:
    cleaned = clean_text(text).lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned.replace("-", " "))
    return re.sub(r"\s+", " ", cleaned).strip()

def tokenize(text: Any) -> List[str]:
    return [w for w in normalize_query(text).split() if len(w) > 2 and w not in STOP_WORDS]

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def correct_spelling(query: str) -> str:
    norm = normalize_query(query)
    if norm in TYPO_MAP:
        return TYPO_MAP[norm]
    for typo, correction in TYPO_MAP.items():
        if typo in norm:
            return norm.replace(typo, correction)

    # Word-level Levenshtein correction against physical product nouns
    words = norm.split()
    corrected = []
    changed = False
    for w in words:
        if w in STOP_WORDS:
            corrected.append(w)
            continue
        if len(w) >= 4 and w not in PHYSICAL_PRODUCT_NOUNS:
            best_target = None
            min_d = 999
            for target in PHYSICAL_PRODUCT_NOUNS:
                max_allowed = 1 if len(target) <= 4 else 2
                if abs(len(w) - len(target)) <= max_allowed:
                    d = levenshtein_distance(w, target)
                    if d < min_d and d <= max_allowed:
                        min_d = d
                        best_target = target
            if best_target:
                corrected.append(best_target)
                changed = True
            else:
                corrected.append(w)
        else:
            corrected.append(w)
    if changed:
        return " ".join(corrected)
    return query

class ProductIntelligenceEngine:
    def __init__(self, standards: List[Dict[str, Any]], find_matches_fn):
        self.standards = standards
        self.find_matches = find_matches_fn

    def infer_from_natural_language(self, text: str) -> Optional[Tuple[str, str]]:
        low = text.lower()
        for pattern, product, standard in NL_DESCRIPTIONS:
            if re.search(pattern, low, re.I):
                return product, standard
        return None

    def check_ambiguity(self, query: str) -> Optional[Dict[str, Any]]:
        norm = normalize_query(query)
        words = norm.split()
        if len(words) == 1 and words[0] in AMBIGUOUS_TERMS:
            return AMBIGUOUS_TERMS[words[0]]
        if norm in AMBIGUOUS_TERMS:
            return AMBIGUOUS_TERMS[norm]
        return None

    def is_non_product(self, query: str) -> bool:
        norm = normalize_query(query)
        words = norm.split()
        if not words:
            return True
        if all(w in NON_PRODUCT_TERMS for w in words):
            return True
        if any(w in NON_PRODUCT_TERMS for w in words) and not any(w in PHYSICAL_PRODUCT_NOUNS for w in words):
            if not any(token in norm for token in ["is ", "standard", "bis", "compliance", "test"]):
                return True
        return False

    def is_physical_product_concept(self, query: str) -> bool:
        norm = normalize_query(query)
        words = set(norm.split())
        if words.intersection(PHYSICAL_PRODUCT_NOUNS):
            return True
        for noun in PHYSICAL_PRODUCT_NOUNS:
            if noun in norm:
                return True
        features = ["solar", "electric", "smart", "portable", "automatic", "battery", "thermal", "insulated", "pressure", "steamer", "heater", "warmer"]
        if any(f in norm for f in features):
            return True
        return False

    def infer_category(self, query: str) -> str:
        q = normalize_query(query)
        if any(w in q for w in ["cook", "stove", "chulha", "gas", "fryer", "oven", "microwave", "hob", "grill", "toaster"]):
            return "Kitchen & Cooking Appliances"
        if any(w in q for w in ["water", "geyser", "kettle", "boiler", "immersion"]):
            return "Water Heating & Liquid Appliances"
        if any(w in q for w in ["cable", "wire", "switch", "socket", "plug", "board", "insulation"]):
            return "Electrical Wiring & Distribution Accessories"
        if any(w in q for w in ["laptop", "computer", "tablet", "it", "electronic", "battery", "power bank"]):
            return "Electronics & Information Technology"
        if any(w in q for w in ["solar", "photovoltaic", "collector", "renewable"]):
            return "Solar & Renewable Energy Systems"
        if any(w in q for w in ["fan", "iron", "steamer", "vacuum", "washing", "refrigerator", "cooler"]):
            return "Domestic Household Electrical Appliances"
        if any(w in q for w in ["helmet", "glove", "mask", "boot", "safety", "shield"]):
            return "Personal Protective Equipment"
        return "General Manufactured Product"

    def analyze(self, raw_input: str) -> Dict[str, Any]:
        text = clean_text(raw_input)
        if not text:
            return {
                "classification": "NON_PRODUCT",
                "status": "EMPTY_INPUT",
                "confidence": 0.0,
                "error": "Please provide a product name or description."
            }

        if self.is_non_product(text):
            return {
                "input": text,
                "classification": "NON_PRODUCT",
                "status": "NON_PRODUCT",
                "confidence": 0.0,
                "message": f"'{text}' does not appear to describe a physical manufactured product. BIS SmartGuide focuses on manufactured goods and equipment subject to Indian Standards.",
                "refusal": "Out of physical product scope.",
                "next_actions": ["Search for a physical manufactured product (e.g. Gas Stove, Electric Kettle, PVC Cable, Helmet, Laptop)."]
            }

        ambiguity = self.check_ambiguity(text)
        if ambiguity:
            return {
                "input": text,
                "classification": "UNCERTAIN",
                "status": "AMBIGUOUS_TERM",
                "confidence": 0.50,
                "detected_product": ambiguity["term"],
                "clarification_needed": True,
                "question": ambiguity["question"],
                "options": ambiguity["options"],
                "candidate_standards": [self.find_matches(opt["product"], 1)[0] for opt in ambiguity["options"] if self.find_matches(opt["product"], 1)],
                "next_actions": ["Select one of the specific product categories above to continue compliance screening."]
            }

        corrected = correct_spelling(text)
        spelling_corrected = (normalize_query(corrected) != normalize_query(text))

        nl_inference = self.infer_from_natural_language(corrected)

        matches = self.find_matches(corrected, 6)

        if nl_inference and (not matches or matches[0].get("match_score", 0) < 70):
            inferred_prod, inferred_std = nl_inference
            std_matches = self.find_matches(inferred_prod, 5)
            if std_matches:
                matches = std_matches

        top_score = matches[0].get("match_score", 0) if matches else 0
        top_standard = matches[0] if matches else None

        if top_score >= 80:
            classification = "CONFIDENTLY_RECOGNIZED"
            status_text = "Recognized BIS Product"
            confidence = round(min(0.98, top_score / 100.0), 2)
            explanation = f"Confidently matched with authentic Indian Standard {top_standard.get('standard_number')} ('{top_standard.get('title')}')."
        elif top_score >= 50:
            classification = "RELATED_PRODUCT"
            status_text = "Related Product Category"
            confidence = round(min(0.85, 0.40 + top_score / 200.0), 2)
            explanation = f"The input terminology is related to '{top_standard.get('product')}' governed by {top_standard.get('standard_number')}."
        elif self.is_physical_product_concept(corrected):
            classification = "POSSIBLE_PRODUCT"
            status_text = "Possible Physical Product"
            inferred_cat = self.infer_category(corrected)
            confidence = 0.72
            explanation = (
                f"The description appears to be a legitimate physical product in the '{inferred_cat}' domain. "
                "While not an exact pre-indexed product name, potential candidate standards have been discovered based on category similarities."
            )
        else:
            classification = "UNCERTAIN"
            status_text = "Uncertain Product Scope"
            confidence = 0.35
            explanation = "Insufficient BIS evidence found in the available catalogue to establish exact standard applicability without guessing."

        category = top_standard.get("category") if (top_standard and classification in ["CONFIDENTLY_RECOGNIZED", "RELATED_PRODUCT"]) else self.infer_category(corrected)

        why_reasons = []
        if spelling_corrected:
            why_reasons.append(f"Spelling normalized: '{text}' → '{corrected}'")
        if nl_inference:
            why_reasons.append(f"Natural language understanding inferred intended product: '{nl_inference[0]}'")
        if top_standard and top_standard.get("match_reasons"):
            why_reasons.extend(top_standard.get("match_reasons", [])[:3])
        if classification == "POSSIBLE_PRODUCT":
            why_reasons.append(f"Inferred functional category: {category}")
            why_reasons.append("Retrieved related technological baseline standards")

        next_actions = []
        if classification == "CONFIDENTLY_RECOGNIZED":
            next_actions = [
                f"View standard requirements for {top_standard.get('standard_number')}",
                "Open Compliance Center to evaluate mandatory checks",
                "Review Gazette QCO status and effective notification",
                "Locate BIS recognized testing laboratories"
            ]
        elif classification == "RELATED_PRODUCT":
            next_actions = [
                f"Verify if your model falls within the scope of {top_standard.get('standard_number')}",
                "Check whether specific section amendments apply to your variant",
                "Consult official BIS Standards Portal scope description"
            ]
        elif classification == "POSSIBLE_PRODUCT":
            next_actions = [
                "Review candidate baseline standards (e.g. general safety and thermal rules)",
                "Establish intended operating voltage, power source, and working environment",
                "Verify whether product is an assembly of individually certified components",
                "Check official BIS 'Know Your Standard' portal for recent new notifications"
            ]
        else:
            next_actions = [
                "Provide additional technical details: intended use, power source, and materials",
                "Search by specific component name or BIS IS number",
                "Verify official BIS portal"
            ]

        return {
            "input": text,
            "spelling_corrected": spelling_corrected,
            "corrected_query": corrected if spelling_corrected else None,
            "classification": classification,
            "status": status_text,
            "confidence": confidence,
            "confidence_percentage": int(confidence * 100),
            "detected_product": top_standard.get("product") if top_standard else (nl_inference[0] if nl_inference else text),
            "likely_category": category,
            "explanation": explanation,
            "why_matched": why_reasons,
            "candidate_standards": matches,
            "top_standard": top_standard,
            "next_actions": next_actions,
            "refusal_boundary": (
                None if classification in ["CONFIDENTLY_RECOGNIZED", "RELATED_PRODUCT"] else
                "SmartGuide does not invent or fabricate standards. For novel or non-catalogued goods, consult official BIS technical committee notifications."
            ),
            "trust_notice": "AI-assisted screening only. Does not issue, verify, or grant BIS certification."
        }
