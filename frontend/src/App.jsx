import { useState } from "react";
import { analyzeResume } from "./api";
import Header from "./components/Header";
import Hero from "./components/Hero";
import UploadForm from "./components/UploadForm";
import Progress from "./components/Progress";
import ProfileCard from "./components/ProfileCard";
import JobCard from "./components/JobCard";
import HowItWorks from "./components/HowItWorks";

export default function App() {
  // status: "idle" | "loading" | "done"
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(params) {
    setError("");
    setStatus("loading");
    try {
      const data = await analyzeResume(params);
      setResult(data);
      setStatus("done");
      setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
      setStatus("idle");
    }
  }

  function reset() {
    setResult(null);
    setStatus("idle");
    document.getElementById("upload")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <Header />
      <main>
        <Hero />

        <section id="upload" className="container">
          {status === "idle" && <UploadForm onSubmit={handleSubmit} error={error} />}
          {status === "loading" && <Progress />}
        </section>

        {status === "done" && result && (
          <section id="results" className="container">
            <ProfileCard profile={result.profile} />
            <div className="results-head">
              <h2>Top matching jobs</h2>
              <button className="btn btn-ghost" onClick={reset}>
                Analyse another resume
              </button>
            </div>
            <p className="muted source-line">
              Searched {result.jobs_searched} jobs · Source: {result.source}
            </p>
            {result.jobs.map((job, i) => (
              <JobCard key={`${job.title}-${job.company}-${i}`} job={job} rank={i + 1} defaultOpen={i === 0} />
            ))}
          </section>
        )}

        <HowItWorks />
      </main>
      <footer className="footer">
        <div className="container">
          SkillBridge AI · LLM course project · React, FastAPI, FAISS, Sentence-Transformers &amp; Gemini
        </div>
      </footer>
    </>
  );
}
