# FinSight

FinSight is a financial filing intelligence project that combines a documented multi-agent SEC analysis pipeline with a connected React dashboard. The repository now groups the research pipeline, API layer, and frontend in one structure so the project reads as a single end-to-end system.

## Architecture

- `src/`: core multi-agent RAG pipeline, ingestion flow, vector search, prompts, and the local Gemma LLM engine
- `backend/`: FastAPI service that exposes the frontend-facing analysis API and schema-aligned responses
- `frontend/`: Vite + React analytics dashboard for company, filing, and year-based analysis views
- `tests/`: unit tests for agent routing, ingestion, and vector-store logic
- `Finsight_Master_Project_Documentation.md`: master design and architecture reference

## Tech Stack

- Python, FastAPI, LangGraph, LangChain
- Local Gemma 4 model configuration in `src/llm_engine.py`
- Qdrant-style retrieval pipeline structure under `src/`
- React, TypeScript, Vite, Recharts

## Screenshots

### Dashboard Overview

![FinSight dashboard overview](docs/images/finsight-dashboard-overview.png)

### Analysis View

![FinSight analysis view](docs/images/finsight-analysis-view.png)

### Pipeline Flow

![FinSight pipeline flow](docs/images/finsight-pipeline-flow.png)

## Running Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API server at `http://localhost:8000` and proxies `/api` requests through Vite during development.

## Project Notes

- The local LLM configuration is aligned to the master documentation and uses the Gemma 4 family setting.
- The repository keeps the documented research modules and a web-facing application layer in one codebase.
- `app.py` and `dashboard.py` were removed in favor of the connected web frontend plus API structure.
