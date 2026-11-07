import { useState } from "react";
import Chips from "./Chips";

const isSafeUrl = (url) => /^https?:\/\//i.test(url || "");

export default function JobCard({ job, rank, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const score = Math.max(0, Math.min(100, job.match_score));

  return (
    <div className={`card job-card${open ? " open" : ""}`}>
      <button type="button" className="job-top" onClick={() => setOpen(!open)} aria-expanded={open}>
        <div className="job-rank">{rank}</div>
        <div className="job-info">
          <h3>{job.title}</h3>
          <p className="muted">
            {job.company}
            {job.location && ` · ${job.location}`}
          </p>
        </div>
        <div className="job-score">
          <div className="score-num">{score.toFixed(0)}%</div>
          <div className="score-bar">
            <span style={{ width: `${score}%` }} />
          </div>
        </div>
        <span className="chevron">▾</span>
      </button>

      {open && (
        <div className="job-body">
          <p className="reason">{job.match_reason}</p>
          <div className="cols">
            <div>
              <h4>✅ Skills you have</h4>
              <Chips items={job.matched_skills} variant="good" />
            </div>
            <div>
              <h4>❌ Missing skills</h4>
              <Chips items={job.missing_skills} variant="bad" />
            </div>
          </div>
          <h4>📈 How to improve</h4>
          <ul className="recs">
            {(job.recommendations || []).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
          <div className="job-actions">
            <span className="muted desc">{job.description.slice(0, 160)}…</span>
            {isSafeUrl(job.url) && (
              <a className="btn btn-apply" href={job.url} target="_blank" rel="noopener noreferrer">
                View &amp; apply
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
