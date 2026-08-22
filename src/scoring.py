from datetime import date, datetime #Used to calculate how old the experience is.

def _cap(value):
    # Keep a score between 0 and 100. Round final value to 2 decimal places
    return round(max(0, min(100, value)), 2)

def calculate_evidence_quality(data, extracted, skill_mappings):
    # Combine the experience and project description, and count the total number of words.
    words = len(f"{data.experience} {data.project_description}".split())

    # Count the number of mapped skills. Use 1 when the list is empty to prevent division by zero.
    mapped_count = len(skill_mappings) or 1

    # Count skills that have Proven or Implied status.
    supported = sum(x["status"] in {"Proven", "Implied"} for x in skill_mappings)

    #------ 1. Relevance score calculation ------------------
    # Calculate the percentage of claimed skills that are supported.
    relevance = _cap(100 * supported / mapped_count)

    #------ 2. Depth score calculation ------------------
    # Give points for:
    # - Providing basic information
    # - Describing actions
    # - Providing a detailed experience/project description
    depth = _cap(25 + len(extracted.get("actions", [])) * 15 + min(words, 40))
 
    #------ 3. Ownership  score calculation ------------------
    # Convert the extracted ownership level into a numeric score.
    ownership = {"High": 100, "Medium": 70, "Low": 40, "Unknown": 25}.get(extracted.get("ownership", "Unknown"), 25)

    #------ 4. Outcome  score calculation ------------------
    # Give a higher score when the LLM identifies project outcomes.
    if extracted.get("outcomes"):
        outcome = 75
    else:
        outcome = 30    

    # Limit the outcome score when unsupported claims are present.
    if extracted.get("unsupported_claims"):
        outcome = min(outcome, 45)

    #------ 5. Verifiability  score calculation ------------------
    # Give points for:
    # - General evidence, such as GitHub links and reports
    # - Evidence that directly supports an impact claim
    verifiability = _cap(len(data.available_evidence) * 30 + len(data.impact_evidence) * 20)

    #------ 6. Recency  score calculation ------------------
    # Use a neutral score when no experience date is available.
    recency = 50
    if data.experience_date:
        try:      
            # Convert the date string into a Python date. Calculate approximately how many years ago it occurred.      
            years = (date.today() - datetime.strptime(data.experience_date, "%Y-%m-%d").date()).days / 365.25

            # Recent experience receives a higher score.
            # Give a higher score to more recent experience.
            if years <= 1:
                recency = 100
            elif years <= 2:
                recency = 85
            elif years <= 3:
                recency = 70
            elif years <= 5:
                recency = 55
            else:
                recency = 35
                    
        except ValueError:
            recency = 50    # Use the neutral score if the date format is invalid.

    #------ 7. Transferability  score calculation ------------------
    # List common skills that are useful across many roles and industries.
    general_tools = {"python", "sql", "excel", "statistics", "communication", "project management"}

    # Collect demonstrated skills with Proven or Implied status.
    # `casefold()` makes skill comparison case-insensitive.
    demonstrated = {x["skill"].casefold() for x in skill_mappings if x["status"] in {"Proven", "Implied"}}

    # Find demonstrated skills that are useful across different roles. Start at 40 and add 15 points for each transferable skill.
    transferability = _cap(40 + len(demonstrated & general_tools) * 15)

    # Store all seven quality scores in one dictionary.
    scores = {
        "relevance": relevance,
        "depth": depth,
        "ownership": ownership,
        "outcome": outcome,
        "verifiability": verifiability,
        "recency": recency,
        "transferability": transferability,
    }
    # Calculate the average of the seven quality dimensions.
    scores["overall_score"] = round(sum(scores.values()) / 7, 2)

    # Convert the overall numeric score into an easy-to-read label.
    overall_score = scores["overall_score"]
    if overall_score >= 75:
        scores["overall_label"] = "Strong"
    elif overall_score >= 50:
        scores["overall_label"] = "Moderate"
    else:
        scores["overall_label"] = "Weak"

    # Return all individual scores, the overall score and its label.    
    return scores
