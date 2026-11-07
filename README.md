# SkillBridge AI

**An LLM-powered semantic job matching and skill-gap analysis system.**

Upload a resume and SkillBridge AI finds real job openings that fit your skills. It ranks them by semantic similarity and uses an LLM to explain each match, list your missing skills and recommend how to close the gaps.

Built with **Retrieval-Augmented Generation (RAG)**: the LLM reasons only over real jobs retrieved from a vector store, so it doesn't invent jobs or requirements.

## Architecture

```
  React frontend (Vite)
        │  POST /api/analyze  (resume PDF)
        ▼
  FastAPI backend
        │
        ├─ 1. Extract text from PDF ............ pdfplumber
        ├─ 2. Understand profile (LLM call 1) .. Gemini → skills, roles (JSON)
        ├─ 3. Fetch live jobs .................. Adzuna API (fallback: jobs.csv)
        ├─ 4. RETRIEVE ......................... sentence-transformers + FAISS → top-k jobs
        └─ 5. AUGMENT + GENERATE (LLM call 2) .. Gemini → match reason, matched / missing
                                                 skills, recommendations
        │
        ▼
  Ranked jobs, match %, skill gaps and an improvement plan in the UI
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite |
| Backend | FastAPI (Python) |
| LLM | Google Gemini (free tier) |
| Embeddings | `sentence-transformers` – all-MiniLM-L6-v2 |
| Vector store | FAISS |
| Job data | Adzuna Jobs API (India) + offline fallback dataset |
| Resume parsing | pdfplumber |

## Project structure

```
skillbridge-ai/
├── backend/
│   ├── main.py            # FastAPI app: /api/analyze, /api/health
│   ├── rag_pipeline.py    # the full RAG pipeline (steps 1–5)
│   └── jobs.csv           # offline fallback job dataset
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js         # calls the backend
│   │   ├── index.css
│   │   └── components/    # Header, Hero, UploadForm, Progress,
│   │                      # ProfileCard, JobCard, Chips, HowItWorks
│   ├── index.html
│   ├── package.json
│   └── vite.config.js     # proxies /api → backend in dev
├── requirements.txt
└── .env.example
```

## Setup

**Requirements:** Python 3.10+ and Node.js 18+.

### 1. API keys

```bash
cp .env.example .env
```

Fill in `.env`:
- `GEMINI_API_KEY`: free from https://aistudio.google.com/apikey
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`: free from https://developer.adzuna.com/

Without Adzuna keys, the app uses the offline `jobs.csv` dataset instead. `.env` is git-ignored, so never commit your keys.

### 2. Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The backend runs on http://127.0.0.1:8000, with API docs at `/docs`. The first run downloads the embedding model (about 90 MB).

### 3. Frontend

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173**.

### Single-server mode (optional, e.g. for a demo)

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app
```

Then open **http://127.0.0.1:8000**. FastAPI serves the built React app.

## API

`POST /api/analyze` (multipart form)

| Field | Type | Description |
|---|---|---|
| `resume` | file | Resume PDF (max 5 MB) |
| `location` | string | Optional city filter, e.g. `Bangalore` |
| `top_k` | int | Number of jobs to analyse (3–8, default 5) |

The response contains `profile`, `source`, `jobs_searched` and `jobs[]`. Each job has `match_score`, `match_reason`, `matched_skills`, `missing_skills` and `recommendations`.

## Notes and limitations

- Adzuna returns a **shortened** job description, so skill-gap analysis is based on that snippet.
- Adzuna results are cached in `backend/cache/` to save free-tier requests. Run one search before a live demo.
- If Gemini reports that the model is unavailable, change `GEMINI_MODEL` in `.env`.

## Future scope

- Multiple job sources (LinkedIn, Naukri, Internshala via official APIs)
- Hybrid ranking (semantic score + skill overlap + experience fit)
- Chat mode: "What should I learn to become a data analyst?"
- Saving profiles and tracking progress over time
