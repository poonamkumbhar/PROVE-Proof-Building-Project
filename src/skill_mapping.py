import re

# Define the common skills expected for each target role.
ROLE_SKILLS = {
    "data analyst": ["SQL", "Excel", "Python", "Data Analysis", "Power BI", "Statistics"],
    "junior data analyst": ["SQL", "Excel", "Python", "Data Analysis", "Power BI"],
    "data scientist": ["Python", "SQL", "Statistics", "Machine Learning", "Data Analysis"],
    "backend developer": ["Python", "Java", "SQL", "REST API", "FastAPI"],
    "project manager": ["Project Management", "Planning", "Stakeholder Management"],
}

# Different abbreviations and full names that represent the same skill.
SKILL_ALIASES = {
    # Machine Learning
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",

    # Deep Learning
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",

    # Natural Language Processing
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",

    # Generative AI
    "genai": "Generative AI",
    "gen ai": "Generative AI",
    "generative ai": "Generative AI",
    "generative artificial intelligence": "Generative AI",
}

def normalize_skill(skill):
    # Remove extra spaces from the beginning and end.
    cleaned_skill = skill.strip()

    # Convert abbreviations and full names into one standard name.
    # `casefold()` makes the comparison case-insensitive.
    return SKILL_ALIASES.get(
        cleaned_skill.casefold(),
        cleaned_skill,
    )

def _mentioned(skill, text):
    # Search for the complete skill name inside the text.
    #
    # This prevents incorrect partial matches.
    # For example, "R" should not match the letter "r" inside "report".
    pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

    # Return True if the skill is found; otherwise, return False.
    return bool(re.search(pattern, text, re.IGNORECASE))


def map_skills(
    target_role,
    claimed_skills,
    experience,
    project_description,
    evidence,
    rag_context=None,
):
    # Combine the experience and project description into searchable text.
    source = f"{experience} {project_description}"

    # Get the standard skills expected for the selected role.
    # Return an empty list if the role is not defined.
    role_skills = ROLE_SKILLS.get(target_role.casefold(),[],)

    # Convert abbreviations into standard skill names.
    # Examples:
    # ML -> Machine Learning
    # DL -> Deep Learning
    # NLP -> Natural Language Processing
    # GenAI -> Generative AI
    claimed_skills = [normalize_skill(skill) for skill in claimed_skills]

    # Normalize role skills using the same rules.
    role_skills = [normalize_skill(skill) for skill in role_skills]

    # Add only standards that match the target role or a claimed skill. RAG
    # provides context; the proof-status rules below remain unchanged.
    retrieved_skills = [
        normalize_skill(item["skill"])
        for item in (rag_context or {}).get("sources", [])
        if item.get("skill")
        and (item.get("role_match", 0) > 0 or item.get("claimed_skill_match", False))
    ]
    role_skills.extend(retrieved_skills)

    # Combine claimed skills and role-required skills.
    combined_skills = claimed_skills + role_skills

    # Remove duplicate skills without considering letter case.
    all_skills = list({skill.casefold(): skill for skill in combined_skills}.values())

    # Create a case-insensitive set of claimed skills.
    # This is calculated once instead of inside every loop.
    claimed_skills_lower = {skill.casefold() for skill in claimed_skills}

    # Create an empty list for skill-mapping results.
    mappings = []

    # Check every unique skill.
    for skill in all_skills:
        # Check whether the user claimed this skill.
        claimed = skill.casefold() in claimed_skills_lower

        # Find all abbreviations and names representing this skill.
        skill_names = [alias for alias, standard_name in SKILL_ALIASES.items()
            if standard_name.casefold() == skill.casefold()]

        # Include the standard skill name in the search.
        skill_names.append(skill)

        # Check whether any version of the skill appears
        # in the experience or project description.
        demonstrated = any(_mentioned(skill_name, source) for skill_name in skill_names)

        # True when the user supplied at least one piece of evidence.
        verifiable = bool(evidence)

        if demonstrated and verifiable:
            # The skill is described and evidence is available.
            status = "Proven"
            strength = "Strong"
            level = "L3" 

            reason = ("The skill is described in the work and supporting evidence is available.")

        elif demonstrated:
            # The skill is described, but evidence is unavailable.
            status = "Implied"
            strength = "Moderate"
            level = "L2"

            reason = ("The work describes this skill, but no supporting evidence was supplied.")

        elif claimed:
            # The skill was claimed, but its use was not described.
            status = "Claimed"
            strength = "Weak"
            level = "L1"

            reason = ("The user claimed this skill, but the supplied work does not demonstrate it and no evidence.")

        else:
            # The role expects the skill, but it was not claimed
            # or demonstrated.
            status = "Unproven"
            strength = "None"
            level = "L0"

            reason = ("The target role expects this skill, but it was neither claimed nor demonstrated.")

        # Store the assessment for the current skill.
        mappings.append(
            {
                "skill": skill,
                "level": level,
                "status": status,
                "evidence_strength": strength,
                "evidence_sources": (list(evidence) if demonstrated else []),
                "reason": reason,})
        mappings[-1]["rag_standard"] = next(
            (
                item["standard"]
                for item in (rag_context or {}).get("sources", [])
                if item.get("skill", "").casefold() == skill.casefold()
            ),
            "",
        )

    # Return the completed mapping.
    return mappings
