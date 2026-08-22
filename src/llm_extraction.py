import json

# import regular expression
import re

import ollama
from pydantic import ValidationError

from src.models import ExtractedEvidence


def _fallback(message):
    # Create a safe response when the LLM fails.
    # Instead of stopping the whole application, we return an empty ExtractedEvidence object
    # and store the error/message inside missing_information.

    result = ExtractedEvidence(missing_information=[message]).model_dump()

    # adds a new key called llm_status to the result dictionary, to show that the normal LLM extraction did not succeed
    result["llm_status"] = "fallback"
    return result


def _unsupported_impact(impact, impact_evidence):
    # function that checks whether percentage-based impact claims have supporting evidence.
    numbers = re.findall(r"\b\d+(?:\.\d+)?%", impact or "")

    if numbers and not impact_evidence:
        return [f"{number} is user-reported and has no supplied supporting evidence."
            for number in numbers]

    return []


def extract_evidence_with_llm(
    target_role,
    claimed_skills,
    experience,
    project_information,
    available_evidence,
    impact="",
    impact_evidence=None,
):
    # function that sends the user's career information to a local LLM and returns structured, validated evidence.
    # Use Gemma 2 only for language understanding; Python controls final facts.
    claimed_skills = claimed_skills or []
    available_evidence = available_evidence or []
    impact_evidence = impact_evidence or []

    supplied = {
        "target_role": target_role,
        "claimed_skills": claimed_skills,
        "experience": experience,
        "project_information": project_information,
        "available_evidence": available_evidence,
        "impact": impact,
    }

    prompt = f"""
Extract structured career evidence from the input below.
Use only supplied facts. Never invent tools, achievements, evidence or numbers.
A claimed skill is demonstrated only when the experience/project describes its use.
Ownership must be High, Medium, Low or Unknown.
Put doubtful statements in unsupported_claims and unclear details in missing_information.

INPUT:
{json.dumps(supplied, indent=2)}
"""

    # Create the instructions sent to the local Gemma model.
    # `json.dumps()` converts the supplied dictionary into formatted JSON.
    # `indent=2` makes the JSON easier for the LLM to read.

    try:
        # Send the prompt to the locally installed Ollama application.
        # Use the local Gemma 2 model with approximately 2 billion parameters.
        # Send the prompt as a user message as a list of dictionaries.
        # Ask Ollama to produce JSON matching the ExtractedEvidence.
        # Set temperature to zero for more consistent and less creative output. This is useful because evidence extraction should be factual.
        response = ollama.chat(
            model="gemma2:2b",
            messages=[{"role": "user", "content": prompt}],
            format=ExtractedEvidence.model_json_schema(),
            options={"temperature": 0},
        )

        # Convert the JSON-formatted text into a Python dictionary.
        parsed = json.loads(response.message.content)

        # Validate the dictionary using the ExtractedEvidence Pydantic model. If validation succeeds,
        # convert the validated model back into a dictionary.
        result = ExtractedEvidence.model_validate(parsed).model_dump()
        result["llm_status"] = "success"

    # Handle errors caused by: Invalid JSON or Incorrect Pydantic fields or data types
    # or Invalid values or Unexpected Python data types
    except (json.JSONDecodeError, ValidationError) as error:
        result = _fallback(f"Invalid LLM output: {error}")

    # Handle other problems, such as: Ollama is not running or Gemma model is not installed or
    # a connection problem occurs
    except Exception as error:
        # Create a safe fallback result instead of stopping the application.
        result = _fallback(f"Ollama unavailable: {error}")

    # Apply deterministic Python guardrails after the LLM processing.
    # By "Deterministic", we mean these checks follow fixed rules and do not depend
    # on the LLM's interpretation.

    # Replace the LLM-generated evidence with the exact evidence supplied by the user.
    # This prevents the model from inventing evidence.
    result["evidence"] = list(available_evidence)

    # Combine the experience and project information into one searchable string.
    # `casefold()` converts the text to a case-insensitive form.
    source = f"{experience or ''} {project_information or ''}".casefold()

    # Keep only claimed skills that appear in the experience or project text.
    # This prevents a claimed skill from automatically being considered demonstrated.
    result["demonstrated_skills"] = [skill for skill in claimed_skills if skill.casefold() in source]

    # Get unsupported claims identified by the LLM.
    # Add warnings for percentage impacts without supporting evidence.
    # `result.get("unsupported_claims", [])` safely gets the existing claims.
    # `_unsupported_impact()` identifies unsupported percentage claims.
    result["unsupported_claims"] = (result.get("unsupported_claims", []) + _unsupported_impact(impact, impact_evidence))

    # Return the final validated and Python-controlled evidence dictionary.
    return result
