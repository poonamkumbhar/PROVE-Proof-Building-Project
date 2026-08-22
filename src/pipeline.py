from src.llm_extraction import extract_evidence_with_llm
from src.models import ProofInput
from src.proof_artifact import create_proof_artifact
from src.proof_gaps import detect_proof_gaps
from src.proof_plan import generate_proof_plan
from src.proof_recommendations import generate_recommendations
from src.scoring import calculate_evidence_quality
from src.skill_mapping import map_skills
from src.storage import save_artifact


def run_proof_pipeline(record=None, **kwargs):
    # Run the complete Proof Builder pipeline.

    # If individual keyword values are supplied, treat them as the input record.
    if record is None:
        record = kwargs

    # Validate the input unless it is already a ProofInput object.
    if not isinstance(record, ProofInput):
        record = ProofInput.model_validate(record)

    # Extract actions, tools, outputs and outcomes using the local LLM.
    extracted = extract_evidence_with_llm(
        record.target_role,
        record.claimed_skills,
        record.experience,
        record.project_description,
        record.available_evidence,
        record.impact,
        record.impact_evidence,
    )

    # Check how strongly each claimed skill is supported.
    skills = map_skills(
        record.target_role,
        record.claimed_skills,
        record.experience,
        record.project_description,
        record.available_evidence,
    )

    # Calculate evidence-quality scores.
    quality = calculate_evidence_quality(record, extracted, skills)

    # Find missing or weak evidence.
    gaps = detect_proof_gaps(skills)

    # Recommend ways to improve weak evidence.
    recommendations = generate_recommendations(gaps)

    # Create a step-by-step proof plan.
    plan = generate_proof_plan(gaps, recommendations)

    # Combine all results into the final proof artifact.
    artifact = create_proof_artifact(
        record,
        extracted,
        skills,
        quality,
        gaps,
        recommendations,
        plan,
    )

    # Save the artifact and store its ID.
    artifact["artifact_id"] = save_artifact(artifact)

    # Return the completed result.
    return artifact