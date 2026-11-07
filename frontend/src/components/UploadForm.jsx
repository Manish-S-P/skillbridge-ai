import { useState } from "react";

const MAX_MB = 5;

export default function UploadForm({ onSubmit, error }) {
  const [file, setFile] = useState(null);
  const [location, setLocation] = useState("");
  const [topK, setTopK] = useState("5");
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState("");

  function pickFile(f) {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setLocalError("Please choose a PDF file.");
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setLocalError(`File is too large (max ${MAX_MB} MB).`);
      return;
    }
    setLocalError("");
    setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files[0]);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (file) onSubmit({ file, location: location.trim(), topK });
  }

  const shownError = localError || error;
  const zoneClass = ["dropzone", dragging && "drag", file && "has-file"].filter(Boolean).join(" ");

  return (
    <form className="card upload-card" onSubmit={handleSubmit}>
      <label
        className={zoneClass}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input type="file" accept="application/pdf" hidden onChange={(e) => pickFile(e.target.files[0])} />
        <div className="drop-icon">📄</div>
        <p className="drop-title">{file ? file.name : "Drag & drop your resume here"}</p>
        <p className="muted">
          {file ? `${(file.size / 1024).toFixed(0)} KB · click to change` : `or click to browse · PDF only · max ${MAX_MB} MB`}
        </p>
      </label>

      <div className="form-row">
        <div className="field">
          <label htmlFor="location">
            Preferred location <span className="muted">(optional)</span>
          </label>
          <input id="location" type="text" placeholder="e.g. Bangalore" value={location} onChange={(e) => setLocation(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="topk">Jobs to analyse</label>
          <select id="topk" value={topK} onChange={(e) => setTopK(e.target.value)}>
            <option value="3">3</option>
            <option value="5">5</option>
            <option value="8">8</option>
          </select>
        </div>
      </div>

      <button type="submit" className="btn btn-primary" disabled={!file}>
        Find matching jobs
      </button>
      {shownError && <p className="error">{shownError}</p>}
    </form>
  );
}
