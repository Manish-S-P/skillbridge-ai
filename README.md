# SkillBridge AI

LLM-powered semantic job matching and skill-gap analysis, using RAG.

## How it works

1. **Upload resume (PDF)**: the text is extracted with `pdfplumber`.
2. **Profile extraction (LLM call 1)**: Gemini returns the candidate's skills, experience level and 2 suitable job roles as JSON.
3. **Fetch real jobs**: the Adzuna API (India) is searched for those roles. Results are cached in `cache/`. If Adzuna fails or no keys are set, the app uses `jobs.csv`.
4. **Retrieve (R)**: jobs are embedded with `all-MiniLM-L6-v2` and stored in a FAISS index. The top-k jobs closest to the resume profile are returned.
5. **Augment + Generate (A + G, LLM call 2)**: Gemini gets the profile plus only the retrieved jobs. For each job it explains the fit and lists matched skills, missing skills and recommendations.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # then put your keys in .env
streamlit run app.py
```

- Gemini key (free): https://aistudio.google.com/apikey
- Adzuna keys (free): https://developer.adzuna.com/

The first run downloads the embedding model (about 90 MB).

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit user interface |
| `rag_pipeline.py` | All pipeline logic (parsing, Adzuna, FAISS, Gemini prompts) |
| `jobs.csv` | Offline fallback dataset (40 sample jobs) |
