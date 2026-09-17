def create_proof_artifact(data, extracted, skill_mappings, quality, gaps, recommendations, proof_plan, rag_context=None):
    # Create and return the final structured proof artifact.
    return {
        # Use the project name as the title. If the project name is empty, create a title from the target role.
        "title": data.project_name or f"{data.target_role} Proof Artifact",
        "target_role": data.target_role,
        "target_domain": data.target_domain,
        "experience": data.experience,
        "project_description": data.project_description,
        "contribution": extracted.get("actions", []),
        "tools": extracted.get("tools", []),
        "outputs": extracted.get("outputs", []),
        "outcomes": extracted.get("outcomes", []),
        "reported_impact": data.impact,
        "unsupported_claims": extracted.get("unsupported_claims", []),# Store claims that do not have enough supporting evidence.
        "skills_demonstrated": skill_mappings,
        "evidence": data.available_evidence,
        "evidence_quality": quality,
        "proof_gaps": gaps,
        "recommendations": recommendations,
        "proof_plan": proof_plan,
        "rag_context": rag_context or {"status": "not_run", "sources": []},
        "ai_provenance": {                        # Record how AI was used while creating the artifact.
            "declaration": data.ai_usage,         # Store the AI usage declared by the user.
            "llm_model": "gemma2:2b",             # Record the local LLM used by the system.
            "llm_status": extracted.get("llm_status", "unknown"), # Record whether the LLM extraction succeeded or used fallback.
            "note": "AI use is recorded as provenance and is not a negative score.", # Clarify that AI use does not reduce the evidence score.
        },
        "missing_information": extracted.get("missing_information", []), # Store important information missing from the user's input.
    }
