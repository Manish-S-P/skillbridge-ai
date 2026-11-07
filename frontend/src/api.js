// Calls the FastAPI backend. In development Vite proxies /api to port 8000.

export async function analyzeResume({ file, location, topK }) {
  const data = new FormData();
  data.append("resume", file);
  data.append("location", location);
  data.append("top_k", topK);

  const res = await fetch("/api/analyze", { method: "POST", body: data });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Server error (${res.status})`);
  }
  return body;
}
