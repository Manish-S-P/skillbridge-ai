"""
Retrieval evaluation for the paper (Table II).

Compares a keyword baseline (TF-IDF) with semantic retrieval
(all-MiniLM-L6-v2 + FAISS) on the offline dataset backend/jobs.csv.

Run from the project root (with the venv active):
    python evaluation/evaluate_retrieval.py
"""

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parent.parent
K = 5

jobs = pd.read_csv(ROOT / "backend" / "jobs.csv").fillna("")
job_texts = (jobs["title"] + ". " + jobs["description"]).tolist()
profiles = json.loads((Path(__file__).parent / "test_profiles.json").read_text())


def rank_tfidf(query: str) -> list[int]:
    vec = TfidfVectorizer(stop_words="english")
    job_m = vec.fit_transform(job_texts)
    q = vec.transform([query])
    scores = (job_m @ q.T).toarray().ravel()  # TF-IDF rows are L2-normalised -> cosine
    return list(np.argsort(-scores))


model = SentenceTransformer("all-MiniLM-L6-v2")
job_vecs = model.encode(job_texts, normalize_embeddings=True).astype("float32")
index = faiss.IndexFlatIP(job_vecs.shape[1])
index.add(job_vecs)


def rank_semantic(query: str) -> list[int]:
    q = model.encode([query], normalize_embeddings=True).astype("float32")
    _, ids = index.search(q, len(job_texts))
    return list(ids[0])


def metrics(ranking: list[int], relevant: set[int]) -> tuple[float, float]:
    top_k = ranking[:K]
    recall = len([i for i in top_k if i in relevant]) / len(relevant)
    rr = next((1 / (pos + 1) for pos, i in enumerate(ranking) if i in relevant), 0.0)
    return recall, rr


results = {"Keyword baseline (TF-IDF)": [], "Semantic (MiniLM + FAISS)": []}
title_to_idx = {t: i for i, t in enumerate(jobs["title"])}

print(f"{'Profile':<28}{'TF-IDF R@5':>12}{'Semantic R@5':>14}")
for p in profiles:
    relevant = {title_to_idx[t] for t in p["relevant"]}
    kw = metrics(rank_tfidf(p["profile"]), relevant)
    se = metrics(rank_semantic(p["profile"]), relevant)
    results["Keyword baseline (TF-IDF)"].append(kw)
    results["Semantic (MiniLM + FAISS)"].append(se)
    print(f"{p['name']:<28}{kw[0]:>12.2f}{se[0]:>14.2f}")

print(f"\nResults over {len(profiles)} profiles, {len(jobs)} jobs (put these in Table II):")
print(f"{'Method':<30}{'Recall@5':>10}{'MRR':>8}")
for name, vals in results.items():
    arr = np.array(vals)
    print(f"{name:<30}{arr[:, 0].mean():>10.3f}{arr[:, 1].mean():>8.3f}")
