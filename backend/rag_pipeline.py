"""
SkillBridge AI - RAG pipeline

Flow:
  1. Extract text from the resume PDF
  2. LLM (Gemini) reads the resume -> skills + suitable job roles
  3. Fetch live jobs for those roles from the Adzuna API (fallback: jobs.csv)
  4. RETRIEVE: embed jobs into a FAISS index and find the top-k closest to the resume
  5. AUGMENT + GENERATE: send resume + retrieved jobs to Gemini for reasoning
"""

import hashlib
import html
import json
import os
import re
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import pdfplumber
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR.parent / ".env")  # .env lives in the project root

CACHE_DIR = BASE_DIR / "cache"
FALLBACK_CSV = BASE_DIR / "jobs.csv"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = "all-MiniLM-L6-v2"
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"  # "in" = India

_embedder = None
_gemini_client = None


# ---------------------------------------------------------------------------
# Step 1: Resume text extraction
# ---------------------------------------------------------------------------
def extract_resume_text(pdf_file) -> str:
    """Read all text from an uploaded PDF resume."""
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return text.strip()


# ---------------------------------------------------------------------------
# Gemini helper
# ---------------------------------------------------------------------------
def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def ask_gemini_json(prompt: str):
    """Send a prompt to Gemini and parse its JSON reply."""
    response = _get_gemini().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return json.loads(response.text)


# ---------------------------------------------------------------------------
# Step 2: Understand the resume (LLM call #1)
# ---------------------------------------------------------------------------
PROFILE_PROMPT = """You are a career assistant. Read the resume below and extract a profile.

Return ONLY valid JSON with exactly these keys:
{{
  "name": "candidate name or 'Candidate'",
  "skills": ["list of technical and soft skills found in the resume"],
  "experience_level": "fresher / intern / junior / mid / senior",
  "suggested_roles": ["2 short job titles that best fit this candidate, e.g. 'Data Analyst'"],
  "summary": "2-3 sentence summary of the candidate's background and strengths"
}}

Resume:
\"\"\"
{resume}
\"\"\"
"""


def extract_profile(resume_text: str) -> dict:
    return ask_gemini_json(PROFILE_PROMPT.format(resume=resume_text[:8000]))


def profile_to_text(profile: dict) -> str:
    """Short text version of the profile, used as the retrieval query."""
    return (
        f"Roles: {', '.join(profile.get('suggested_roles', []))}. "
        f"Skills: {', '.join(profile.get('skills', []))}. "
        f"{profile.get('summary', '')}"
    )


# ---------------------------------------------------------------------------
# Step 3: Get real jobs (Adzuna API, with cache + CSV fallback)
# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _fetch_adzuna(role: str, location: str, n: int) -> list[dict]:
    """Call Adzuna for one role. Results are cached to save free-tier requests."""
    CACHE_DIR.mkdir(exist_ok=True)
    key = hashlib.md5(f"{role}|{location}|{n}".lower().encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    params = {
        "app_id": os.getenv("ADZUNA_APP_ID"),
        "app_key": os.getenv("ADZUNA_APP_KEY"),
        "what": role,
        "results_per_page": n,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    resp = requests.get(ADZUNA_URL, params=params, timeout=15)
    resp.raise_for_status()

    jobs = [
        {
            "title": _clean(r.get("title")),
            "company": (r.get("company") or {}).get("display_name", "Unknown"),
            "location": (r.get("location") or {}).get("display_name", ""),
            "description": _clean(r.get("description")),
            "url": r.get("redirect_url", ""),
        }
        for r in resp.json().get("results", [])
    ]
    cache_file.write_text(json.dumps(jobs))
    return jobs


def fetch_jobs(roles: list[str], location: str = "", per_role: int = 25):
    """Return (jobs DataFrame, source label)."""
    if os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"):
        try:
            jobs = []
            for role in roles[:2]:
                jobs += _fetch_adzuna(role, location, per_role)
            df = pd.DataFrame(jobs).drop_duplicates(subset=["title", "company"])
            if not df.empty:
                return df.reset_index(drop=True), "Adzuna (live jobs)"
        except Exception as e:  # network error, quota exhausted, bad key...
            print(f"[warn] Adzuna failed, using fallback CSV: {e}")

    df = pd.read_csv(FALLBACK_CSV).fillna("")
    return df, "Offline dataset (jobs.csv)"


# ---------------------------------------------------------------------------
# Step 4: RETRIEVE - embeddings + FAISS vector search
# ---------------------------------------------------------------------------
def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def build_index(jobs_df: pd.DataFrame):
    """Embed every job and store the vectors in a FAISS index."""
    texts = (jobs_df["title"] + ". " + jobs_df["description"]).tolist()
    vectors = _get_embedder().encode(texts, normalize_embeddings=True)
    index = faiss.IndexFlatIP(vectors.shape[1])  # inner product = cosine (normalized)
    index.add(np.asarray(vectors, dtype="float32"))
    return index


def retrieve(query: str, index, jobs_df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Find the k jobs most semantically similar to the query."""
    q = _get_embedder().encode([query], normalize_embeddings=True)
    scores, ids = index.search(np.asarray(q, dtype="float32"), min(k, len(jobs_df)))
    top = jobs_df.iloc[ids[0]].copy()
    top["match_score"] = (scores[0] * 100).round(1)
    return top.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Step 5: AUGMENT + GENERATE - reasoning over retrieved jobs (LLM call #2)
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """You are a career advisor. Below is a candidate profile and a list of
job postings that were retrieved for them. Use ONLY the information in these job
postings - do not invent requirements that are not mentioned or clearly implied.

Candidate profile:
{profile}

Retrieved jobs:
{jobs}

For EACH job, return ONLY valid JSON: a list of objects with exactly these keys:
[
  {{
    "job_id": <number of the job>,
    "match_reason": "2-3 sentences on why this job suits the candidate",
    "matched_skills": ["skills the candidate already has that this job needs"],
    "missing_skills": ["skills this job needs that the candidate lacks"],
    "recommendations": ["2-3 concrete steps to close the gap (course, project, certification)"]
  }}
]
"""


def analyze_matches(profile: dict, top_jobs: pd.DataFrame) -> list[dict]:
    jobs_text = "\n\n".join(
        f"Job {i + 1}: {row.title} at {row.company} ({row.location})\n"
        f"Description: {row.description[:1500]}"
        for i, row in enumerate(top_jobs.itertuples())
    )
    profile_text = json.dumps(
        {k: profile.get(k) for k in ("skills", "experience_level", "summary")}, indent=2
    )
    return ask_gemini_json(ANALYSIS_PROMPT.format(profile=profile_text, jobs=jobs_text))


# ---------------------------------------------------------------------------
# Full pipeline - called by the API
# ---------------------------------------------------------------------------
def run_pipeline(pdf_file, location: str = "", top_k: int = 5) -> dict:
    resume_text = extract_resume_text(pdf_file)
    if not resume_text:
        raise ValueError("Couldn't read any text from this PDF (is it a scanned image?).")

    profile = extract_profile(resume_text)                                  # LLM call 1
    jobs_df, source = fetch_jobs(profile.get("suggested_roles", []), location)
    index = build_index(jobs_df)                                            # vector store
    top_jobs = retrieve(profile_to_text(profile), index, jobs_df, k=top_k)  # R
    analysis = analyze_matches(profile, top_jobs)                           # A + G (LLM call 2)

    by_id = {item.get("job_id"): item for item in analysis}
    jobs = []
    for i, job in enumerate(top_jobs.to_dict(orient="records")):
        info = by_id.get(i + 1, {})
        jobs.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "url": job.get("url", ""),
            "description": job["description"][:400],
            "match_score": float(job["match_score"]),
            "match_reason": info.get("match_reason", ""),
            "matched_skills": info.get("matched_skills", []),
            "missing_skills": info.get("missing_skills", []),
            "recommendations": info.get("recommendations", []),
        })

    return {
        "profile": profile,
        "source": source,
        "jobs_searched": len(jobs_df),
        "jobs": jobs,
    }
