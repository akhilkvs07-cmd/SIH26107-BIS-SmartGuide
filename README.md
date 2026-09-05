# BIS SmartGuide — SIH 2026 PS 26107

AI-powered intelligent assistant prototype for discovering Indian Standards, analysing product descriptions, checking prototype compliance items, explaining certification workflow, locating BIS laboratory resources, and answering BIS-related questions with source-aware local RAG.

## Architecture

- Frontend: static HTML/CSS/JavaScript (`index.html`)
- Backend: Flask REST API (`backend/app.py`)
- Knowledge layer: local RAG engine (`backend/rag_engine.py`)
- Prototype dataset: `backend/bis_data.json`
- Optional knowledge documents: `backend/documents/`

## Features

1. Product/standard search with ranked matching
2. Natural-language product analysis and attribute extraction
3. Multiple standard recommendations
4. Prototype compliance checklist and scoring
5. Certification workflow guidance
6. BIS laboratory and official-resource links
7. RAG-powered `/chat` assistant with retrieved sources
8. `/rag-search` retrieval inspection endpoint
9. `/rag-rebuild` endpoint to reload local documents
10. Health and API information endpoints

## Run locally

```powershell
cd C:\SIH26107\backend
python -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

Backend: `http://127.0.0.1:5000`

Open the root `index.html` using VS Code Live Server for the frontend.

## RAG knowledge base

Put permitted `.txt`, `.md`, or `.json` reference documents into `backend/documents/`. Restart the backend or POST to `/rag-rebuild` after adding files.

The prototype intentionally separates recommendation from official certification decisions. Always verify current BIS information, amendments, schemes and laboratory scope through BIS sources.

## Important

The bundled demonstration records are prototype data and are not an official BIS certification checklist. The system should be presented as a decision-support prototype, not as a replacement for BIS.
