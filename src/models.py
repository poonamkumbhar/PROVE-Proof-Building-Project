# Enum creates a fixed collection of proof-status values.
from enum import Enum

# BaseModel creates structured data models.
# Field provides defaults and basic validation.
from pydantic import BaseModel, Field, field_validator


class ProofStatus(str, Enum):
    # possible evidence-proof categories.
    PROVEN = "Proven"
    IMPLIED = "Implied"
    CLAIMED = "Claimed"
    UNPROVEN = "Unproven"

class Project(BaseModel):
    # Store the name and description of a project.
    name: str = ""
    description: str = ""

class CandidateEvidence(BaseModel):
    # Unique ID, role the candidate applied for, target domain, skills, work experience, project information,
    # existing proof, such as reports, certificates or GitHub links, measurable result, such as
    #  "Reduced processing time by 20%", and explains how AI was used in the candidate's work.

    id: str
    target_role: str
    target_domain: str
    claimed_skills: list[str]
    experience: str
    project: Project
    evidence: list[str] = Field(default_factory=list)
    impact: str = ""
    ai_usage: str = "None"


class ProofInput(BaseModel):
    # Target role must contain at least two characters.
    target_role: str = Field(min_length=2)

    # Use "General" when no specific domain is provided.
    target_domain: str = "General"

    # The user must provide at least one claimed skill.
    claimed_skills: list[str] = Field(min_length=1)

    # The experience description must contain at least ten characters.
    experience: str = Field(min_length=10)

    # Project fields are optional.
    project_name: str = ""
    project_description: str = ""

    # Evidence provided by the user.
    available_evidence: list[str] = Field(default_factory=list)

    # Measurable result claimed by the user.
    impact: str = ""

    # Evidence supporting the measurable impact.
    impact_evidence: list[str] = Field(default_factory=list)

    # The date is optional, so it can be a string or None.
    experience_date: str | None = None

    # Explains whether AI was used.
    ai_usage: str = "None"

    @field_validator("claimed_skills")
    @classmethod
    def clean_skills(cls, skills):
        # Remove blank values and extra spaces from skills.
        cleaned_skills = [skill.strip() for skill in skills if skill.strip()]

        # Reject the input if no valid skill remains.
        if not cleaned_skills:
            raise ValueError("Enter at least one claimed skill.")

        return cleaned_skills


class ExtractedEvidence(BaseModel):
    # Actions performed by the candidate.
    actions: list[str] = Field(default_factory=list)

    # Tools or technologies used by the candidate.
    tools: list[str] = Field(default_factory=list)

    # Items created by the candidate, such as reports or dashboards.
    outputs: list[str] = Field(default_factory=list)

    # Results achieved through the candidate's work.
    outcomes: list[str] = Field(default_factory=list)

    # Skills supported by the experience or project description.
    demonstrated_skills: list[str] = Field(default_factory=list)

    # Candidate's level of ownership.
    ownership: str = "Unknown"

    # Information that was not clearly provided.
    missing_information: list[str] = Field(default_factory=list)

    # Claims that do not have enough supporting evidence.
    unsupported_claims: list[str] = Field(default_factory=list)

    @field_validator("ownership")
    @classmethod
    def clean_ownership(cls, value):
        # Convert the value to text and remove extra spaces.
        # `title()` converts values such as "high" into "High".
        cleaned_value = str(value).strip().title()

        # Accept only the four allowed ownership values.
        if cleaned_value in {"High", "Medium", "Low", "Unknown"}:
            return cleaned_value

        # Use "Unknown" when the LLM returns an unexpected value.
        return "Unknown"