"""Explainable local RAG engine for BIS SmartGuide.

Indexes authentic Indian Standards, QCOs, testing parameters, and local documents.
Provides BM25/TF-IDF cosine similarity search with source provenance.
"""

import json
import math
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "what", "which", "with", "my", "our", "can", "do", "does", "about", "tell",
    "me", "please", "product", "used", "use", "manufactured", "manufacturing", "made"
}

def tokenize(text: Any) -> List[str]:
    return [
        w for w in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if len(w) > 2 and w not in STOP_WORDS
    ]

def chunk_text(text: str, size: int = 120, overlap: int = 20) -> List[str]:
    words = str(text).split()
    chunks = []
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        piece = " ".join(words[start:start + size]).strip()
        if piece:
            chunks.append(piece)
        if start + size >= len(words):
            break
    return chunks

def build_standard_chunks(standards: List[Dict[str, Any]], resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    for s in standards:
        num = s.get("standard_number", "")
        title = s.get("title", "")
        prod = s.get("product", "")
        cat = s.get("category", "")
        desc = s.get("description", "")
        syns = ", ".join(s.get("synonyms", []))
        reqs = s.get("requirements", [])
        qco = s.get("qco_order", "")
        scheme = s.get("scheme", "")
        tests = s.get("testing_parameters", [])
        url = s.get("official_source", "https://standards.bis.gov.in/")

        overview = (
            f"Indian Standard {num}: {title}. Product: {prod}. Synonyms: {syns}. Category: {cat}. "
            f"Certification Scheme: {scheme}. Mandatory QCO: {qco}. Description: {desc}"
        )
        for i, piece in enumerate(chunk_text(overview)):
            chunks.append({
                "text": piece,
                "source_type": "standard_overview",
                "authority": "BIS Official Standard Specification",
                "support_level": "authoritative_standard",
                "standard_number": num,
                "title": title,
                "source_url": url,
                "chunk_id": f"{num}-meta-{i}"
            })

        for i, r in enumerate(reqs):
            chunks.append({
                "text": f"Standard {num} ({title}) technical requirement for {prod}: {r}. Under scheme: {scheme}.",
                "source_type": "technical_requirement",
                "authority": "BIS Standard Technical Clause",
                "support_level": "authoritative_clause",
                "standard_number": num,
                "title": title,
                "source_url": url,
                "chunk_id": f"{num}-req-{i}"
            })

        for i, t in enumerate(tests):
            chunks.append({
                "text": f"Prescribed laboratory test method for {prod} under {num}: {t}.",
                "source_type": "laboratory_test_method",
                "authority": "BIS Testing Protocol & LIMS Parameter",
                "support_level": "test_protocol",
                "standard_number": num,
                "title": title,
                "source_url": "https://lims.bis.gov.in/",
                "chunk_id": f"{num}-test-{i}"
            })

        if qco:
            chunks.append({
                "text": f"Mandatory Regulatory Status for {prod} ({num}): Governed by {qco}. Effective date: {s.get('effective_date', 'In effect')}.",
                "source_type": "qco_gazette_order",
                "authority": "Central Government Quality Control Order (QCO)",
                "support_level": "gazette_regulation",
                "standard_number": num,
                "title": title,
                "source_url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en",
                "chunk_id": f"{num}-qco"
            })

    for r in resources:
        chunks.append({
            "text": f"Official BIS Service '{r['name']}': {r['description']}",
            "source_type": "official_resource",
            "authority": "Bureau of Indian Standards Portal",
            "support_level": "official_resource",
            "standard_number": None,
            "title": r["name"],
            "source_url": r["url"],
            "chunk_id": "res-" + re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")
        })

    return chunks

class LocalRAG:
    def __init__(self, standards: List[Dict[str, Any]], resources: List[Dict[str, Any]], documents_dir: Optional[str] = None):
        self.standards = standards
        self.resources = resources
        self.documents_dir = documents_dir
        self.chunks = build_standard_chunks(standards, resources)
        self._load_documents()
        self.documents = [tokenize(c["text"]) for c in self.chunks]
        self.doc_count = len(self.documents)
        self.df = Counter()
        for tokens in self.documents:
            for token in set(tokens):
                self.df[token] += 1

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def document_count(self) -> int:
        return len({c.get("source_url") or c.get("title") for c in self.chunks})

    def _load_documents(self):
        if not self.documents_dir or not os.path.isdir(self.documents_dir):
            return
        for root, _, files in os.walk(self.documents_dir):
            for filename in files:
                path = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext not in {".txt", ".md", ".json"}:
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        raw = f.read()
                    if ext == ".json":
                        raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
                    for i, piece in enumerate(chunk_text(raw)):
                        self.chunks.append({
                            "text": piece,
                            "source_type": "local_document",
                            "authority": "Local Knowledge Document",
                            "support_level": "local_document",
                            "standard_number": None,
                            "title": filename,
                            "source_url": f"local://documents/{filename}",
                            "chunk_id": f"{filename}-{i}"
                        })
                except (OSError, UnicodeError, json.JSONDecodeError):
                    continue

    def _vector(self, tokens: List[str]) -> Dict[str, float]:
        counts = Counter(tokens)
        vector = {}
        for token, count in counts.items():
            if token not in self.df:
                continue
            idf = math.log((1 + self.doc_count) / (1 + self.df[token])) + 1
            vector[token] = (1 + math.log(count)) * idf
        norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
        return {k: v / norm for k, v in vector.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        return sum(v * b.get(k, 0.0) for k, v in a.items())

    def retrieve(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        tokens = tokenize(query)
        if not tokens:
            return []
        q_vector = self._vector(tokens)
        scored = []
        q_low = str(query or "").lower().strip()

        for index, doc_tokens in enumerate(self.documents):
            score = self._cosine(q_vector, self._vector(doc_tokens))
            text_low = self.chunks[index]["text"].lower()
            phrase_bonus = 0.15 if q_low and q_low in text_low else 0.0
            final = min(1.0, score + phrase_bonus)
            if final > 0.05:
                item = dict(self.chunks[index])
                item["relevance"] = round(final * 100, 1)
                scored.append(item)

        scored.sort(key=lambda x: x["relevance"], reverse=True)
        return scored[:top_k]

    def answer(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        retrieved = self.retrieve(query, top_k)
        if not retrieved or retrieved[0].get("relevance", 0) < 18:
            return {
                "answer": "I could not find sufficient BIS evidence in the available standards repository for this query. Please consult the official BIS Standards Portal (standards.bis.gov.in) directly.",
                "sources": [],
                "retrieved": [],
                "retrieved_count": 0,
                "confidence": 0.0,
                "support_level": "unsupported",
                "rag": True
            }

        standards = []
        seen = set()
        for item in retrieved:
            num = item.get("standard_number")
            if num and num not in seen:
                seen.add(num)
                standards.append(num)

        top_relevance = retrieved[0].get("relevance", 0)
        confidence = round(min(0.98, top_relevance / 100.0), 2)

        if standards:
            answer = (
                f"Relevant Indian Standard reference(s) identified: {', '.join(standards[:3])}. "
                f"Requirements cover safety, performance, and testing specifications. "
                f"Always verify current amendments and notification scope on official BIS sources."
            )
        else:
            answer = (
                "Relevant BIS guidance retrieved from knowledge base records. "
                "Consult the official BIS website before making certification decisions."
            )

        sources = [
            {
                "title": x.get("title") or x.get("standard_number") or "BIS Document",
                "url": x.get("source_url"),
                "authority": x.get("authority"),
                "support_level": x.get("support_level"),
                "relevance": x.get("relevance")
            }
            for x in retrieved
        ]

        return {
            "answer": answer,
            "sources": sources,
            "retrieved": retrieved,
            "retrieved_count": len(retrieved),
            "confidence": confidence,
            "support_level": "supported_with_verification" if confidence >= 0.40 else "weak_support",
            "rag": True
        }
