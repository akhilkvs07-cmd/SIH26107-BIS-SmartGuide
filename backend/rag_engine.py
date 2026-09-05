"""Lightweight local RAG engine for BIS SmartGuide.

This prototype intentionally uses only Python's standard library so it is easy
for a student team to run locally. It builds a TF-IDF style vector index over
BIS metadata, prototype requirements, and official BIS resource guidance, then
retrieves the most relevant chunks for a user question.
"""

import math
import re
from collections import Counter

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "how", "i", "in", "is", "it", "of", "on", "or", "that",
    "the", "this", "to", "what", "which", "with", "my", "our", "can", "do",
    "does", "about", "tell", "me", "please", "product", "used", "use"
}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def make_chunks(standards, official_resources):
    chunks = []
    for standard in standards:
        number = standard.get("standard_number", "")
        title = standard.get("title", "")
        product = standard.get("product", "")
        category = standard.get("category", "")
        description = standard.get("description", "")
        requirements = standard.get("requirements", [])
        compliance = standard.get("compliance_text", "")

        text = (
            f"BIS standard {number}. Product: {product}. Title: {title}. "
            f"Category: {category}. Description: {description}. "
            f"Requirements: {', '.join(requirements)}. {compliance}"
        )
        chunks.append({
            "text": text,
            "source_type": "standard_metadata",
            "standard_number": number,
            "title": title,
            "source_url": "https://standards.bis.gov.in/"
        })

        if requirements:
            for requirement in requirements:
                chunks.append({
                    "text": f"For {product} under {number} ({title}), a prototype checklist item is: {requirement}.",
                    "source_type": "prototype_requirement",
                    "standard_number": number,
                    "title": title,
                    "source_url": "https://standards.bis.gov.in/"
                })

    for resource in official_resources:
        chunks.append({
            "text": f"{resource['name']}: {resource['description']}",
            "source_type": "official_resource",
            "standard_number": None,
            "title": resource["name"],
            "source_url": resource["url"]
        })

    # General workflow guidance, deliberately kept high-level.
    chunks.extend([
        {
            "text": "BIS SmartGuide should identify the likely applicable Indian Standard first, then ask the user to verify the latest official BIS standard, amendments, notifications and applicable certification scheme.",
            "source_type": "workflow_guidance",
            "standard_number": None,
            "title": "Standard identification and verification",
            "source_url": "https://www.bis.gov.in/know-your-standard/?lang=en"
        },
        {
            "text": "BIS certification requirements can vary by product, applicable standard and government requirements. A prototype assistant must not present a checklist as an official BIS certification decision.",
            "source_type": "workflow_guidance",
            "standard_number": None,
            "title": "Certification caution",
            "source_url": "https://www.bis.gov.in/apply-for-a-license/?lang=en"
        },
        {
            "text": "For current testing laboratory information, users should consult the official BIS recognized laboratory directory and BIS LIMS.",
            "source_type": "workflow_guidance",
            "standard_number": None,
            "title": "Laboratory guidance",
            "source_url": "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"
        }
    ])
    return chunks


class LocalRAG:
    def __init__(self, standards, official_resources):
        self.chunks = make_chunks(standards, official_resources)
        self.documents = [tokenize(c["text"]) for c in self.chunks]
        self.doc_count = len(self.documents)
        self.df = Counter()
        for tokens in self.documents:
            for token in set(tokens):
                self.df[token] += 1

    def _vector(self, tokens):
        counts = Counter(tokens)
        vector = {}
        for token, count in counts.items():
            if token not in self.df:
                continue
            idf = math.log((1 + self.doc_count) / (1 + self.df[token])) + 1
            vector[token] = (1 + math.log(count)) * idf
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        return {key: value / norm for key, value in vector.items()}

    @staticmethod
    def _cosine(a, b):
        if not a or not b:
            return 0.0
        return sum(value * b.get(key, 0.0) for key, value in a.items())

    def retrieve(self, query, top_k=4):
        q_vector = self._vector(tokenize(query))
        scored = []
        for index, tokens in enumerate(self.documents):
            score = self._cosine(q_vector, self._vector(tokens))
            if score > 0:
                item = dict(self.chunks[index])
                item["relevance"] = round(score * 100, 1)
                scored.append(item)
        scored.sort(key=lambda item: item["relevance"], reverse=True)
        return scored[:top_k]

    def answer(self, query, top_k=4):
        retrieved = self.retrieve(query, top_k)
        if not retrieved:
            return {
                "answer": "I could not find relevant information in the local BIS knowledge base. Please verify the query using the official BIS Standards Portal.",
                "sources": [],
                "retrieved_count": 0,
                "rag": True
            }

        standards = [x for x in retrieved if x.get("standard_number")]
        unique_standards = []
        seen = set()
        for item in standards:
            number = item["standard_number"]
            if number not in seen:
                seen.add(number)
                unique_standards.append(number)

        source_lines = []
        for item in retrieved:
            label = item.get("standard_number") or item.get("title")
            source_lines.append(f"{label} — {item['source_url']}")

        if unique_standards:
            answer = (
                "Based on the retrieved BIS SmartGuide knowledge, the most relevant "
                f"standard reference(s) are {', '.join(unique_standards[:3])}. "
                "These are recommendations for the prototype, not an official BIS certification decision. "
                "Please verify the latest applicable standard, amendments and scheme on BIS before relying on the result."
            )
        else:
            answer = (
                "I found relevant BIS guidance in the local knowledge base. "
                "For a final decision, verify the current requirement directly on the official BIS source."
            )

        return {
            "answer": answer,
            "sources": source_lines,
            "retrieved": retrieved,
            "retrieved_count": len(retrieved),
            "rag": True
        }
