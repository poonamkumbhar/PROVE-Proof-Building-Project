def generate_recommendations(proof_gaps):
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
        recommendations.append({"skill": skill, "status": status, "recommended_action": action})
    return recommendations
