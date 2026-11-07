const STAGES = [
  { num: "1", title: "Parse", text: "Text is extracted from your PDF resume." },
  { num: "2", title: "Understand", text: "Gemini extracts your skills and suitable roles." },
  { num: "3", title: "Fetch", text: "Live jobs for those roles are pulled from Adzuna." },
  { num: "R", title: "Retrieve", text: "Jobs are embedded into FAISS; the closest ones to your profile are found.", key: true },
  { num: "A+G", title: "Reason", text: "Gemini explains each match, missing skills and next steps — using only the retrieved jobs.", key: true },
];

export default function HowItWorks() {
  return (
    <section id="how" className="container how">
      <h2>How it works</h2>
      <p className="muted center">Retrieval-Augmented Generation (RAG) keeps the LLM grounded in real job data.</p>
      <div className="pipeline">
        {STAGES.map((s) => (
          <div key={s.title} className={`stage${s.key ? " key" : ""}`}>
            <span className="num">{s.num}</span>
            <h4>{s.title}</h4>
            <p>{s.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
