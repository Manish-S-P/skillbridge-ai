import { useEffect, useState } from "react";

const STEPS = [
  "Reading your resume",
  "Understanding your profile with Gemini",
  "Fetching live jobs from Adzuna",
  "Semantic search in the vector store",
  "Generating match explanations & skill gaps",
];

// The backend runs the whole pipeline in one request, so the steps advance on a
// timer to show the user what is happening.
export default function Progress() {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setCurrent((c) => Math.min(c + 1, STEPS.length - 1)), 2500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card progress">
      <h3>Running the RAG pipeline…</h3>
      <ol className="steps">
        {STEPS.map((step, i) => (
          <li key={step} className={i < current ? "done" : i === current ? "active" : ""}>
            {step}
          </li>
        ))}
      </ol>
    </div>
  );
}
