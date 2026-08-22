def detect_proof_gaps(skill_mappings):
    # Convert every skill-mapping result into a proof-gap record.
    # Each record shows the skill, proof status, current level and reason.    
    return [
        {
            "skill": item["skill"],          # Name of the claimed skill.
            "status": item["status"],        # Proof category: Proven, Implied, Claimed or Unproven.
            "current_level": item["level"],  # Current proof-strength level of the skill.
            "why": item["reason"],           # Explanation of why the skill received this status.
        }
        for item in skill_mappings
    ]

