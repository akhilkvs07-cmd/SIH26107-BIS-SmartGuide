# BIS SmartGuide — SIH 2026 PS 26107

BIS SmartGuide is an evidence-aware AI assistant for Indian Standards and BIS services. It is designed around SIH26107: natural-language standards discovery, applicable-standard recommendation, certification guidance, consumer assistance, laboratory guidance and multilingual interaction.

## V8.5 upgrade — Standards Intelligence + Compliance Platform

The existing Flask + static HTML/CSS/vanilla-JavaScript architecture is preserved. V8.5 adds a shared source-grounded intelligence layer rather than replacing the application.

### Major capabilities

1. **Product Intelligence 2.0** — natural-language product classification, ranked candidate standards, reasons and evidence classification.
2. **Clause-aware RAG contract** — standard/edition/amendment/clause/page/source/hash fields are supported; missing clause metadata is never fabricated.
3. **Document → evidence pipeline** — PDF, TXT, MD, JSON and DOCX extraction plus image OCR when the deployment has the OCR engine available.
4. **Real OCR boundary** — ISI, CM/L, R-number and HUID candidates can be extracted; OCR failure returns an explicit failure/unavailable status rather than synthetic values.
5. **ISI / CM-L / CRS / HUID workflows** — format screening is explicitly separated from official registry verification. No fake VERIFIED result is returned.
6. **Universal QR / Barcode decoding** — real image decoding, URL trust classification and evidence status.
7. **Capability-aware Lab Matcher** — standard/test/city filtering, Google Maps search links, and explicit local-snapshot verification status.
8. **Test Report Intelligence** — measured values are extracted while required limits and pass/fail remain UNVERIFIED until mapped to verified evidence.
9. **Label / Packaging Intelligence** — extracts key fields and reports UNVERIFIED where product-specific mandatory declarations are not source-supported.
10. **Amendment / Gazette architecture** — supplied amendment text can be analysed as inference; live official monitoring is reported unavailable unless connected to a trusted source.
11. **Persona workflows** — Consumer, Manufacturer/MSME, Startup, Importer, Procurement, Compliance Professional, Laboratory and General User.
12. **AI Agent orchestration** — routes requests to product, RAG, verification, laboratory, testing, label and amendment workflows.
13. **Compliance Passport integration** — reuses the existing V4 SQLite assessment history and evidence model.
14. **Professional PDF reports** — report generation includes the SmartGuide decision-support disclaimer.
15. **Consistent API envelope** — status, data, confidence, evidence, source, timestamp and errors.
16. **Security boundaries** — basename-only file handling, extension allow-list, file-size limit, no uploaded-file execution and graceful optional dependency failures.

## Architecture

- Main frontend: static HTML/CSS/JavaScript (`index.html`)
- Existing advanced console: `smartguide-v8.js`
- V8.5 UI integration: `smartguide-v8-upgrade.js`
- Navigation bridge: `command-center-fix.js`
- Backend: Flask REST API (`backend/app.py`)
- Production entrypoint: `backend/app_upgrade.py`
- V4 compliance intelligence: `backend/compliance_upgrade.py`
- V8.5 intelligence layer: `backend/platform_v8.py`
- RAG: `backend/rag_engine.py`
- Agent: `backend/bis_agent.py`
- Product intelligence: `backend/product_intelligence.py`
- Persona engine: `backend/role_engine.py`
- Laboratory directory handoff: `backend/labs_directory.py`
- Standards dataset: `backend/bis_data.json`
- Runtime SQLite database: `backend/smartguide.db`

## V8 API groups

All V8 endpoints are available through both `/v8/...` and `/api/v8/...` because the existing API-prefix middleware is preserved.

- `GET /api/v8/health`
- `POST /api/v8/product-intelligence`
- `GET /api/v8/rag/search`
- `GET /api/v8/rag/clauses`
- `POST /api/v8/document/ingest`
- `POST /api/v8/ocr`
- `POST /api/v8/verify/mark`
- `POST /api/v8/verify/crs`
- `POST /api/v8/verify/huid`
- `POST /api/v8/qr/decode`
- `GET /api/v8/labs/match`
- `POST /api/v8/tests/analyze`
- `POST /api/v8/label/analyze`
- `GET /api/v8/amendments`
- `POST /api/v8/amendments/impact`
- `GET/POST /api/v8/alerts`
- `POST /api/v8/persona`
- `GET /api/v8/evidence`
- `POST /api/v8/agent/orchestrate`
- `POST /api/v8/report/pdf`

Existing `/v4`, `/v5`, `/v8` and core routes remain in place where they are still compatible.

## Run locally

```powershell
cd C:\SIH26107\backend
python -m pip install -r requirements.txt
python app_upgrade.py
```

Backend: `http://127.0.0.1:5000`

Open `index.html` with VS Code Live Server for the main application. The V8.5 integration is loaded into the existing Advanced Features console without a React migration.

## Document / OCR dependencies

`pypdf`, `Pillow`, `python-docx`, `pytesseract`, OpenCV, pyzbar and ReportLab are optional runtime capabilities installed by `requirements.txt`. OCR additionally depends on the Tesseract executable being available in the deployment environment. If it is unavailable, SmartGuide returns `OCR_UNAVAILABLE` and never fabricates text.

## Trust and compliance boundary

The bundled standards catalogue and laboratory records are application data/snapshots, not a live BIS registry. They must not be presented as live verification. Current standards, amendments, QCOs, schemes, licence status, HUID/CRS records and laboratory scope must be verified through official BIS sources before a regulatory decision.

The platform explicitly distinguishes **SOURCE-GROUNDED**, **INFERRED**, **USER-PROVIDED** and **SOURCE_UNAVAILABLE/UNVERIFIED** information. Document analysis does not constitute BIS certification or legal approval. SmartGuide does not issue BIS certificates.

## Deployment

- Frontend: GitHub Pages workflow remains in `.github/workflows/deploy-pages.yml`.
- Backend: Render/Gunicorn deployment remains available through the existing production entrypoint.
- Do not expose secrets in the static frontend. Configure deployment-specific environment variables in the backend service.
