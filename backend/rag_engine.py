"""Explainable local RAG engine for BIS SmartGuide."""
import json
import math
import os
import re
from collections import Counter

STOP_WORDS={"a","an","and","are","as","at","be","by","for","from","has","have","how","i","in","is","it","of","on","or","that","the","this","to","what","which","with","my","our","can","do","does","about","tell","me","please","product","used","use","manufactured","manufacturing","made"}

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+",str(text or "").lower()) if len(w)>2 and w not in STOP_WORDS]

def chunk_text(text,size=110,overlap=20):
    words=str(text).split(); chunks=[]; step=max(1,size-overlap)
    for start in range(0,len(words),step):
        piece=" ".join(words[start:start+size]).strip()
        if piece: chunks.append(piece)
        if start+size>=len(words): break
    return chunks

def standard_chunks(standards,resources):
    chunks=[]
    for s in standards:
        number=s.get("standard_number",""); title=s.get("title",""); product=s.get("product","")
        base=(f"BIS Indian Standard {number}. Product: {product}. Title: {title}. "
              f"Category: {s.get('category','')}. Description: {s.get('description','')}. "
              f"Requirements: {', '.join(s.get('requirements',[]))}. Compliance information: {s.get('compliance_text','')}")
        for i,piece in enumerate(chunk_text(base)):
            chunks.append({"text":piece,"source_type":"standard_metadata","authority":"BIS portal reference","support_level":"metadata_reference","standard_number":number,"title":title,"source_url":"https://standards.bis.gov.in/","chunk_id":f"{number}-meta-{i}"})
        for i,req in enumerate(s.get("requirements",[])):
            chunks.append({"text":f"Prototype checklist requirement for {product} under {number}: {req}.","source_type":"prototype_requirement","authority":"BIS portal + local prototype record","support_level":"prototype_requirement","standard_number":number,"title":title,"source_url":"https://standards.bis.gov.in/","chunk_id":f"{number}-req-{i}"})
    for r in resources:
        chunks.append({"text":f"{r['name']}: {r['description']}","source_type":"official_resource","authority":"Official BIS resource","support_level":"official_resource","standard_number":None,"title":r["name"],"source_url":r["url"],"chunk_id":"resource-"+re.sub(r"[^a-z0-9]+","-",r["name"].lower()).strip("-")})
    return chunks

class LocalRAG:
    def __init__(self,standards,resources,documents_dir=None):
        self.standards=standards; self.resources=resources; self.documents_dir=documents_dir
        self.chunks=standard_chunks(standards,resources); self._load_documents(); self.documents=[tokenize(c["text"]) for c in self.chunks]
        self.doc_count=len(self.documents); self.df=Counter()
        for tokens in self.documents:
            for token in set(tokens): self.df[token]+=1
    @property
    def chunk_count(self): return len(self.chunks)
    @property
    def document_count(self): return len({c.get("source_url") or c.get("title") for c in self.chunks})
    def _load_documents(self):
        if not self.documents_dir or not os.path.isdir(self.documents_dir): return
        for root,_,files in os.walk(self.documents_dir):
            for filename in files:
                path=os.path.join(root,filename); ext=os.path.splitext(filename)[1].lower()
                if ext not in {".txt",".md",".json"}: continue
                try:
                    with open(path,"r",encoding="utf-8") as f: raw=f.read()
                    if ext==".json": raw=json.dumps(json.loads(raw),ensure_ascii=False,indent=2)
                    for i,piece in enumerate(chunk_text(raw)):
                        self.chunks.append({"text":piece,"source_type":"local_document","authority":"Local knowledge document","support_level":"local_document","standard_number":None,"title":filename,"source_url":f"local://documents/{filename}","chunk_id":f"{filename}-{i}"})
                except (OSError,UnicodeError,json.JSONDecodeError): continue
    def _vector(self,tokens):
        counts=Counter(tokens); vector={}
        for token,count in counts.items():
            if token not in self.df: continue
            idf=math.log((1+self.doc_count)/(1+self.df[token]))+1; vector[token]=(1+math.log(count))*idf
        norm=math.sqrt(sum(v*v for v in vector.values())) or 1.0
        return {k:v/norm for k,v in vector.items()}
    @staticmethod
    def _cosine(a,b): return sum(v*b.get(k,0.0) for k,v in a.items()) if a and b else 0.0
    def retrieve(self,query,top_k=6):
        q_vector=self._vector(tokenize(query)); scored=[]; query_text=str(query or "").lower()
        for index,tokens in enumerate(self.documents):
            score=self._cosine(q_vector,self._vector(tokens)); text_lower=self.chunks[index]["text"].lower(); phrase_bonus=.12 if query_text and query_text in text_lower else 0; final=min(1.0,score+phrase_bonus)
            if final>0:
                item=dict(self.chunks[index]); item["relevance"]=round(final*100,1); scored.append(item)
        scored.sort(key=lambda x:x["relevance"],reverse=True); return scored[:top_k]
    def answer(self,query,top_k=5):
        retrieved=self.retrieve(query,top_k)
        if not retrieved:
            return {"answer":"I could not find supported information in the local BIS knowledge base. Please verify the query using the official BIS Standards Portal.","sources":[],"retrieved":[],"retrieved_count":0,"confidence":0,"support_level":"unsupported","rag":True}
        standards=[]; seen=set()
        for item in retrieved:
            number=item.get("standard_number")
            if number and number not in seen: seen.add(number); standards.append(number)
        confidence=round(sum(x.get("relevance",0) for x in retrieved[:3])/min(3,len(retrieved)),1)
        if standards: answer="Relevant standard references found in the local knowledge base: "+", ".join(standards[:4])+". Verify the latest official BIS standard, amendments and applicable scheme before relying on the result."
        else: answer="Relevant BIS guidance was retrieved from the local knowledge base. Verify the current official BIS source before making a regulatory or certification decision."
        sources=[{"title":x.get("title") or x.get("standard_number"),"url":x.get("source_url"),"authority":x.get("authority"),"support_level":x.get("support_level"),"relevance":x.get("relevance")} for x in retrieved]
        return {"answer":answer,"sources":sources,"retrieved":retrieved,"retrieved_count":len(retrieved),"confidence":confidence,"support_level":"supported_with_verification" if confidence>=35 else "weak_support","rag":True}
