# This file creates a structured improvement plan for skills that are not yet proven.
#  It recommends deliverables such as a GitHub repository, README, dataset, notebook, dashboard, and outcome report.

def generate_proof_plan(proof_gaps, recommendations):
   
    recommendation_by_skill = {x["skill"]: x["recommended_action"] for x in recommendations}
    plans = []     #  an empty list to store the proof plans.

    # Process every identified proof gap.
    for gap in proof_gaps:

        # if proven skill already has strong evidence, it does not need an improvement plan and hence continue.
        if gap["status"] == "Proven":
            continue

        # Get the name of the skill that needs better proof.
        skill = gap["skill"] 

        # Create a proof plan for the current skill.
        plans.append({
            "proof_gap": skill,
            "current_state": gap["status"], # Current proof status, such as Implied, Claimed or Unproven.
            "why": gap["why"],              # Reason why the skill received its current status.
            "suggested_proof": recommendation_by_skill[skill], # Recommended action for creating stronger proof.
            "deliverables": [   # Files or evidence the user should create.
                "GitHub repository or shareable work file", 
                "README explaining problem, contribution and steps",
                "Dataset or safe sample data",
                "Analysis notebook/script/dashboard",
                "Short findings and outcome report",
            ],
        })
    # Return proof plans for all skills that are not already proven.
    return plans 
