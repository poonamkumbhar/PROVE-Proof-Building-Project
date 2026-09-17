import json

import streamlit as st
from pydantic import ValidationError

from src.pipeline import run_proof_pipeline #Import the main Proof Builder pipeline.

# Configure the browser tab and page layout.
st.set_page_config(page_title="PROVE Proof Builder", page_icon="✅", layout="wide")
st.title("PROVE - Proof Builder & Evidence Intelligence")
st.caption("Local Gemma 2 extraction plus FAISS RAG over role/skill standards. Your input stays on your computer.")

# Create a form to collect the user's career information.
with st.form("proof_form"):
    left, right = st.columns(2)    # divide form into 2 columns
    with left:                     # display on left columns, default values are added
        target_role = st.text_input("Target role *", "Junior Data Analyst") 
        target_domain = st.text_input("Target domain", "Retail")
        skills_text = st.text_input("Claimed skills (comma-separated) *", "Python, SQL, Excel")
        
        project_name = st.text_input("Project name", "Sales Data Analysis")
    with right:
        ai_usage = st.selectbox("AI-use declaration", ["None", "AI-assisted", "AI-generated", "AI-dependent"])
        evidence_text = st.text_area("Evidence references/links (one per line)", "Internship Certificate\nGitHub Repository")
        impact_evidence_text = st.text_area("Evidence supporting the impact (one per line)", "")

    project_description = st.text_area("Project description", height=100)
    experience = st.text_area("Experience description *", height=130)
    

    # Submit all form values together.
    submitted = st.form_submit_button("Analyse and build proof", type="primary")

# Run the pipeline only after the user submits the form.
if submitted:

    # Convert the Streamlit form values into a dictionary.
    record = {
        "target_role": target_role,
        "target_domain": target_domain,
         # Split comma-separated skills into a clean list.
        "claimed_skills": [x.strip() for x in skills_text.split(",") if x.strip()],
        "experience": experience,
        "project_name": project_name,
        "project_description": project_description,
        # Convert evidence entered on separate lines into a list.
        "available_evidence": [x.strip() for x in evidence_text.splitlines() if x.strip()],
        # Convert impact evidence entered on separate lines into a list.
        "impact_evidence": [x.strip() for x in impact_evidence_text.splitlines() if x.strip()],
        
        "ai_usage": ai_usage,
    }
    try:
        # Display a loading message while Gemma processes the input.
        with st.spinner("Gemma 2 is extracting evidence..."):
            result = run_proof_pipeline(record)

        # Save the result in session state. This keeps the result available when Streamlit reruns the page.
        st.session_state["result"] = result

        # Inform the user that the artifact was successfully created.
        st.success(f"Proof artifact created: {result['artifact_id']}")

    except ValidationError as error:
        # Display input-validation errors from the Pydantic model.
        st.error(f"Please correct the input: {error}")

    except Exception as error:
        # Display other errors, such as pipeline or database errors.
        st.error(f"Analysis failed: {error}")

# Display results when an artifact exists in session state.
if "result" in st.session_state:
    result = st.session_state["result"]  # Get latest saved result.

    # RAG is shown separately so users can inspect the retrieved sources.
    tabs = st.tabs(["RAG context", "Skill map", "Quality", "Proof gaps", "Proof plan", "Final artifact"])

    with tabs[0]:
        rag = result["rag_context"]
        if rag["status"] == "success":
            st.write(f"Embedding model: {rag['embedding_model']}")
            st.write(f"Retrieval: {rag['retrieval']}")
            st.write(f"Reranking: {rag['reranking']}")
            st.dataframe(rag["sources"], use_container_width=True)
        else:
            st.warning("RAG was unavailable. The original deterministic pipeline continued safely.")
            st.caption(rag.get("message", "Unknown RAG error"))

    with tabs[1]:     # Display skills and their proof statuses.
        st.dataframe(result["skills_demonstrated"], use_container_width=True)

    with tabs[2]:     # Display the overall quality label and score.
        st.metric("Overall evidence quality", 
                  result["evidence_quality"]["overall_label"], 
                  result["evidence_quality"]["overall_score"])
        # Select only numeric dimension scores for the chart. Exclude overall_score because it is already shown above.
        st.bar_chart({
            name: score
            for name, score in result["evidence_quality"].items()
            if isinstance(score, (int, float)) 
            and name != "overall_score"})
        
    with tabs[3]:  # Display weak or missing proof areas.
        st.dataframe(result["proof_gaps"], use_container_width=True)

    with tabs[4]:   # Display one expandable proof plan for each skill.
         for item in result["proof_plan"]:
            title = (
                f"{item['proof_gap']} - "
                f"{item['current_state']}"
            )
            with st.expander(title):
                st.write(item)

    with tabs[5]:      # Display and download the complete artifact.
        st.json(result)            # Convert the final artifact into formatted JSON.

        # Allow the user to download the artifact as a JSON file.
        st.download_button(
            "Download proof artifact (JSON)",
            json.dumps(result, indent=2, ensure_ascii=False),
            file_name=f"proof_artifact_{result['artifact_id']}.json",
            mime="application/json",
        )
