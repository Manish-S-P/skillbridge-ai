"""SkillBridge AI - Streamlit front end. Run with:  streamlit run app.py"""

import streamlit as st

import rag_pipeline as rag

st.set_page_config(page_title="SkillBridge AI", page_icon="🎯", layout="wide")
st.title("🎯 SkillBridge AI")
st.caption("LLM-powered semantic job matching and skill-gap analysis (RAG)")

with st.sidebar:
    st.header("Settings")
    location = st.text_input("Preferred location (optional)", placeholder="e.g. Bangalore")
    top_k = st.slider("Number of jobs to analyse", 3, 8, 5)

uploaded = st.file_uploader("Upload your resume (PDF)", type="pdf")

if uploaded and st.button("Find matching jobs", type="primary"):
    try:
        with st.status("Running the RAG pipeline...", expanded=True) as status:
            st.write("📄 Reading resume...")
            resume_text = rag.extract_resume_text(uploaded)
            if not resume_text:
                st.error("Couldn't read any text from this PDF (is it a scanned image?).")
                st.stop()

            st.write("🧠 Understanding your profile with Gemini...")
            profile = rag.extract_profile(resume_text)

            st.write(f"🔎 Fetching jobs for: {', '.join(profile['suggested_roles'])}...")
            jobs_df, source = rag.fetch_jobs(profile["suggested_roles"], location)

            st.write(f"📚 Embedding {len(jobs_df)} jobs into the vector store...")
            index = rag.build_index(jobs_df)
            top_jobs = rag.retrieve(rag.profile_to_text(profile), index, jobs_df, k=top_k)

            st.write("✍️ Generating match explanations and skill-gap analysis...")
            analysis = rag.analyze_matches(profile, top_jobs)
            status.update(label="Done!", state="complete", expanded=False)
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.stop()

    # ---- Profile ----
    st.subheader(f"👤 Profile: {profile.get('name', 'Candidate')}")
    st.write(profile.get("summary", ""))
    st.write("**Skills found:** " + ", ".join(profile.get("skills", [])))
    st.caption(f"Experience level: {profile.get('experience_level', '-')} · Job source: {source}")

    # ---- Matches ----
    st.subheader(f"💼 Top {len(top_jobs)} matching jobs")
    by_id = {item.get("job_id"): item for item in analysis}

    for i, job in top_jobs.iterrows():
        info = by_id.get(i + 1, {})
        with st.expander(
            f"{i + 1}. {job['title']} — {job['company']}  |  Match: {job['match_score']}%",
            expanded=(i == 0),
        ):
            st.caption(job["location"])
            st.write(info.get("match_reason", ""))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Skills you have**")
                for s in info.get("matched_skills", []):
                    st.markdown(f"- {s}")
            with col2:
                st.markdown("**❌ Missing skills**")
                for s in info.get("missing_skills", []):
                    st.markdown(f"- {s}")

            st.markdown("**📈 How to improve**")
            for r in info.get("recommendations", []):
                st.markdown(f"- {r}")

            if job.get("url"):
                st.link_button("View / apply", job["url"])
