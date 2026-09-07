# BIS SmartGuide — SIH 2026 PS 26107

BIS SmartGuide is an evidence-aware AI assistant for Indian Standards and BIS services. It is designed around SIH26107: natural-language standards discovery, applicable-standard recommendation, certification guidance, consumer assistance, hallmarking/laboratory guidance and multilingual interaction.

## V5 upgrade — Compliance Intelligence Cockpit

The project now includes a dedicated `smartguide-v5.html` demo cockpit that exposes the strongest upgrade path in one judge-friendly workflow:

1. **Applicable Standard Finder** — ranked product/standard matching with match reasons.
2. **Evidence Trail** — retrieved standard/source information and explicit prototype-vs-authoritative evidence separation.
3. **Smart Compliance Assessment** — Pass / Fail / Not checked, score, risk, evidence quality and corrective actions.
4. **Compliance Passport** — persistent assessment ID, evidence hash and assessment history.
5. **Document / Photo Intelligence** — PDF/TXT/MD/JSON extraction plus optional image OCR when deployment dependencies are available.
6. **CM/L workflow** — conservative format validation and official BIS verification hand-off; no fabricated licence status.
7. **Certification guidance** — high-level workflow with official BIS resource links.
8. **BIS laboratory guidance** — official laboratory directory/LIMS hand-off rather than invented availability.
9. **Multilingual AI agent** — existing dependency-light language-aware agent for English, Hindi, Telugu, Kannada and Tamil, with browser voice support in the main UI.
10. **Assessment history** — SQLite-backed saved assessments and corrective-action tracking.
11. **Trust / refusal layer** — insufficient evidence is surfaced instead of inventing a compliance requirement.
12. **Local RAG** — explainable retrieval over the prototype catalogue plus permitted documents in `backend/documents/`.

## Architecture

- Main frontend: static HTML/CSS/JavaScript (`index.html`)
- V5 demo cockpit: `smartguide-v5.html`
- Backend: Flask REST API (`backend/app.py`)
- Production upgrade entrypoint: `backend/app_upgrade.py`
- Compliance intelligence: `backend/compliance_upgrade.py`
- Knowledge layer: `backend/rag_engine.py`
- Agent: `backend/bis_agent.py`
- Prototype dataset: `backend/bis_data.json`
- Local knowledge documents: `backend/documents/`
- Persistent assessment database: `backend/smartguide.db` at runtime

## Important API groups

### Core
- `/health`
- `/search`
- `/recommend`
- `/analyze`
- `/check-product`
- `/mandatory-check`
- `/certification-guide`
- `/labs`
- `/resources`
- `/rag-search`
- `/rag-rebuild`
- `/chat`

### V4/V5 Compliance Intelligence
- `GET /v4/health`
- `POST /v4/assess`
- `POST /v4/document`
- `GET /v4/assessments`
- `GET /v4/assessments/<assessment_id>`
- `PATCH /v4/actions/<action_id>`
- `GET /v4/passport/<assessment_id>`
- `GET /v4/analytics`
- `GET /v4/compare/<assessment_id_a>/<assessment_id_b>`

## Run locally

```powershell
cd C:\SIH26107\backend
python -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

Backend: `http://127.0.0.1:5000`

Open `index.html` with VS Code Live Server for the main application. For the full upgrade demonstration, open `smartguide-v5.html` with Live Server while the backend is running.

## RAG knowledge base

Put permitted `.txt`, `.md`, or `.json` reference documents into `backend/documents/`. Restart the backend or POST to `/rag-rebuild` after adding files. PDF/image extraction is available through the V4 document-intelligence route when the deployment dependencies are installed.

## Trust and compliance boundary

The bundled demonstration records are prototype data and are **not** an official BIS certification checklist. SmartGuide does not issue BIS certificates, guarantee licence status, or invent laboratory availability. Current standards, amendments, QCOs, schemes, licence status and laboratory scope must be verified through official BIS sources before a regulatory decision.
