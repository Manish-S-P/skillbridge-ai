"""
SkillBridge AI - FastAPI backend.

Run from the project root:
    uvicorn backend.main:app --reload
API docs: http://127.0.0.1:8000/docs
"""

import io
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from . import rag_pipeline as rag

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
MAX_FILE_MB = 5

app = FastAPI(title="SkillBridge AI", version="1.0")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(
    resume: UploadFile = File(...),
    location: str = Form(""),
    top_k: int = Form(5),
):
    """Upload a resume PDF -> ranked jobs with match explanations and skill gaps."""
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")

    data = resume.file.read()
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (max {MAX_FILE_MB} MB).")

    try:
        return rag.run_pipeline(io.BytesIO(data), location.strip(), max(3, min(top_k, 8)))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:  # e.g. missing API key
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")


# Serve the built React app (after `npm run build` in frontend/).
# During development, run `npm run dev` instead - Vite proxies /api to this server.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
