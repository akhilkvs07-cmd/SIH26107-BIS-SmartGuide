from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# LOAD BIS DATA
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "bis_data.json")

with open(DATA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

bis_data = data["standards"]


# --------------------------------------------------
# TEXT NORMALIZATION
# --------------------------------------------------

def normalize(text):
    """
    Converts text into a simple searchable format.
    Example:
    'Electric Fan' -> 'electric fan'
    """
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# --------------------------------------------------
# PRODUCT MATCHING
# --------------------------------------------------

def find_best_match(product):

    product = normalize(product)

    if not product:
        return None, 0

    search_words = product.split()

    best_match = None
    best_score = 0

    for standard in bis_data:

        standard_product = normalize(
            standard.get("product", "")
        )

        title = normalize(
            standard.get("title", "")
        )

        category = normalize(
            standard.get("category", "")
        )

        description = normalize(
            standard.get("description", "")
        )

        standard_number = normalize(
            standard.get("standard_number", "")
        )

        # Everything searchable
        searchable_text = " ".join([
            standard_product,
            title,
            category,
            description,
            standard_number
        ])

        score = 0

        # ------------------------------------------
        # EXACT PRODUCT MATCH
        # ------------------------------------------

        if product == standard_product:
            score += 100

        # ------------------------------------------
        # PRODUCT PHRASE MATCH
        # ------------------------------------------

        elif product in standard_product:
            score += 60

        # ------------------------------------------
        # TITLE MATCH
        # ------------------------------------------

        if product in title:
            score += 40

        # ------------------------------------------
        # CATEGORY MATCH
        # ------------------------------------------

        if product in category:
            score += 20

        # ------------------------------------------
        # INDIVIDUAL WORD MATCHING
        # ------------------------------------------

        for word in search_words:

            # Ignore very short words
            if len(word) <= 2:
                continue

            if word in standard_product:
                score += 20

            elif word in title:
                score += 10

            elif word in category:
                score += 5

            elif word in searchable_text:
                score += 3

        # ------------------------------------------
        # KEEP BEST MATCH
        # ------------------------------------------

        if score > best_score:
            best_score = score
            best_match = standard

    return best_match, best_score


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "message": "BIS SmartGuide Backend is running",
        "status": "success"
    })


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# ALL STANDARDS
# --------------------------------------------------

@app.route("/standards")
def standards():

    return jsonify({
        "count": len(bis_data),
        "standards": bis_data
    })


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if not query:

        return jsonify({
            "error": "Please provide a search query"
        }), 400

    query = normalize(query)

    results = []

    for standard in bis_data:

        searchable_text = normalize(" ".join([
            standard.get("standard_number", ""),
            standard.get("product", ""),
            standard.get("title", ""),
            standard.get("category", ""),
            standard.get("description", "")
        ]))

        if query in searchable_text:

            results.append(standard)

    return jsonify({

        "query": query,

        "count": len(results),

        "results": results

    })


# --------------------------------------------------
# SMART RECOMMENDATION
# --------------------------------------------------

@app.route("/recommend", methods=["GET"])
def recommend():

    product = request.args.get("product", "").strip()

    if not product:

        return jsonify({
            "error": "Please enter a product name"
        }), 400

    best_match, score = find_best_match(product)

    if best_match is None or score == 0:

        return jsonify({

            "found": False,

            "message": "No matching BIS standard found"

        })

    return jsonify({

        "found": True,

        "standard": best_match,

        "match_score": score,

        "prototype_notice":
            "This system is a prototype demonstration. "
            "Verify applicable requirements against official BIS documentation."

    })


# --------------------------------------------------
# CHECK COMPLIANCE
# --------------------------------------------------

@app.route("/check-compliance", methods=["GET"])
def check_compliance():

    product = request.args.get("product", "").strip()

    if not product:

        return jsonify({

            "error": "Please provide a product name"

        }), 400

    best_match, score = find_best_match(product)

    if best_match is None:

        return jsonify({

            "found": False,

            "message": "No matching BIS standard found"

        })

    return jsonify({

        "found": True,

        "standard": best_match,

        "match_score": score

    })


# --------------------------------------------------
# COMPLIANCE CHECKER
# --------------------------------------------------

@app.route("/check-product", methods=["POST"])
def check_product():

    data = request.get_json()

    if not data:

        return jsonify({

            "error": "No data received"

        }), 400

    product = data.get("product", "").strip()

    checks = data.get("checks", {})

    if not product:

        return jsonify({

            "error": "Product name is required"

        }), 400

    # Find best matching standard
    matched_standard, match_score = find_best_match(product)

    if matched_standard is None:

        return jsonify({

            "found": False,

            "message": "No matching BIS standard found"

        })

    requirements = matched_standard.get(
        "requirements",
        []
    )

    passed = []
    failed = []
    not_checked = []

    # ------------------------------------------
    # CHECK EACH REQUIREMENT
    # ------------------------------------------

    for requirement in requirements:

        value = checks.get(requirement)

        if value is True:

            passed.append(requirement)

        elif value is False:

            failed.append(requirement)

        else:

            not_checked.append(requirement)

    total_requirements = len(requirements)

    # ------------------------------------------
    # CALCULATE SCORE
    # ------------------------------------------

    if total_requirements > 0:

        score = round(
            (len(passed) / total_requirements) * 100
        )

    else:

        score = 0

    # ------------------------------------------
    # DETERMINE STATUS
    # ------------------------------------------

    if failed:

        status = "Needs Review"

    elif not_checked:

        status = "Partially Checked"

    else:

        status = "Compliant"

    # ------------------------------------------
    # RESPONSE
    # ------------------------------------------

    return jsonify({

        "found": True,

        "product": product,

        "standard": matched_standard,

        "match_score": match_score,

        "score": score,

        "status": status,

        "passed": passed,

        "failed": failed,

        "not_checked": not_checked,

        "summary": {

            "total": total_requirements,

            "passed": len(passed),

            "failed": len(failed),

            "not_checked": len(not_checked)

        },

        "compliance_text":
            matched_standard.get(
                "compliance_text",
                "Verify against official BIS documentation."
            ),

        "prototype_notice":
            "This is a prototype compliance assessment "
            "and does not represent official BIS certification."

    })


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )