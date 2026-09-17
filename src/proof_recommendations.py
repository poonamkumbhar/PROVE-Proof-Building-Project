def generate_recommendations(proof_gaps, rag_context=None):
    standards = {
        item["skill"].casefold(): item
        for item in (rag_context or {}).get("sources", [])
    }
    recommendations = []         # an empty list to store recommendations for every skill.
    for gap in proof_gaps:
        skill, status = gap["skill"], gap["status"]
        if status == "Proven":      # The skill already has strong supporting evidence.
            action = "Keep the evidence ready and add a short verification note."
        elif status == "Implied":   # The experience suggests the skill, but direct proof is still needed.
            action = f"Add a GitHub link, report, screenshot or manager reference showing your {skill} work."
        elif status == "Claimed":    # The skill is claimed, but its practical use has not been demonstrated.
            action = f"Build a small role-relevant project that uses {skill} and document your steps and result."
        else:                         # The skill has not yet been demonstrated or supported.
            action = f"Learn the basics of {skill}, then create one small practical project demonstrating it."

        # Store the skill, its status and its recommended action.
        standard = standards.get(skill.casefold())
        if standard and status != "Proven":
            expected = ", ".join(standard.get("expected_evidence", [])[:3])
            action += f" Role-standard proof to add: {expected}."

        recommendations.append({
            "skill": skill,
            "status": status,
            "recommended_action": action,
            "rag_source_id": standard["source_id"] if standard else None,
        })
    return recommendations
