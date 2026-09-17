import json
import unittest
from unittest.mock import patch

import numpy as np

from src.llm_extraction import extract_evidence_with_llm
from src.models import ProofInput
from src.proof_gaps import detect_proof_gaps
from src.scoring import calculate_evidence_quality
from src.skill_mapping import map_skills
from src.rag_retrieval import RoleSkillRetriever, faiss as faiss_library


# Create a fake LLM message for testing.
class FakeMessage:
    content = json.dumps(
        {
            "actions": ["wrote SQL queries"],
            "tools": ["SQL"],
            "outputs": ["customer dataset"],
            "outcomes": [],
            "demonstrated_skills": ["SQL"],
            "ownership": "High",
            "missing_information": [],
            "unsupported_claims": [],
        }
    )


# Create a fake Ollama response containing the fake message.
class FakeResponse:
    message = FakeMessage()


class CoreTests(unittest.TestCase):

    def test_rag_context_does_not_override_proof_status_rules(self):
        rag_context = {
            "sources": [{
                "skill": "RAG",
                "standard": "Show retrieval and evaluation evidence.",
                "role_match": 1.0,
                "claimed_skill_match": False,
            }]
        }
        mapped = map_skills(
            "GenAI Engineer",
            ["Python"],
            "I created a Python application.",
            "Local application",
            [],
            rag_context,
        )
        by_skill = {item["skill"]: item for item in mapped}
        self.assertEqual(by_skill["RAG"]["status"], "Unproven")
        self.assertEqual(by_skill["RAG"]["rag_standard"], "Show retrieval and evaluation evidence.")

    @unittest.skipIf(faiss_library is None, "FAISS is unavailable")
    def test_faiss_retrieval_and_reranking(self):
        def fake_embedder(texts):
            vectors = []
            for text in texts:
                lowered = text.casefold()
                vectors.append([
                    float("rag" in lowered or "retrieval" in lowered),
                    float("sql" in lowered),
                    float("python" in lowered),
                    0.1,
                ])
            values = np.asarray(vectors, dtype="float32")
            norms = np.linalg.norm(values, axis=1, keepdims=True)
            return values / np.maximum(norms, 1e-8)

        retriever = RoleSkillRetriever(embedder=fake_embedder)
        results = retriever.retrieve(
            "GenAI Engineer RAG retrieval FAISS",
            "GenAI Engineer",
            ["RAG"],
            top_k=3,
        )
        self.assertEqual(results[0]["skill"], "RAG")
        self.assertGreaterEqual(results[0]["rerank_score"], results[1]["rerank_score"])

    @patch(
        "src.llm_extraction.ollama.chat",
        return_value=FakeResponse(),
    )
    def test_successful_extraction(self, _mock):
        # Test valid JSON returned by the local LLM.
        result = extract_evidence_with_llm(
            "Data Analyst",
            ["SQL", "Python"],
            "I wrote SQL queries for sales data.",
            "Created a customer dataset.",
            ["GitHub Repository"],
            "",
            [],
        )

        # The extraction should complete successfully.
        self.assertEqual(
            result["llm_status"],
            "success",
        )

        # SQL is demonstrated because it appears in the experience.
        self.assertIn(
            "SQL",
            result["demonstrated_skills"],
        )

        # Python is only claimed and is not used in the description.
        self.assertNotIn(
            "Python",
            result["demonstrated_skills"],
        )

    @patch("src.llm_extraction.ollama.chat")
    def test_invalid_llm_output(self, mocked):
        # Make the fake LLM return invalid JSON.
        mocked.return_value.message.content = "not-json"

        # Run evidence extraction with the invalid response.
        result = extract_evidence_with_llm(
            "Data Analyst",
            ["Python"],
            "I used Python for data cleaning.",
            "Project details",
            [],
            "",
            [],
        )

        # Invalid JSON should produce a safe fallback result.
        self.assertEqual(
            result["llm_status"],
            "fallback",
        )

        # The simplified extraction function calls Ollama once.
        self.assertEqual(
            mocked.call_count,
            1,
        )

    def test_claimed_and_proven_status(self):
        # Map SQL and Python against the supplied work description.
        mapped = map_skills(
            "Data Analyst",
            ["SQL", "Python"],
            "I wrote SQL queries for a report.",
            "Sales analysis",
            ["GitHub Repository"],
        )

        # Create a simple skill-to-status dictionary.
        statuses = {
            item["skill"]: item["status"]
            for item in mapped
        }

        # SQL is described and has evidence, so it should be Proven.
        self.assertEqual(
            statuses["SQL"],
            "Proven",
        )

        # Python is claimed but not demonstrated.
        self.assertEqual(
            statuses["Python"],
            "Claimed",
        )

    def test_all_proof_statuses_are_possible(self):
        # Create sample data containing all four proof statuses.
        gaps = detect_proof_gaps(
            [
                {
                    "skill": "A",
                    "status": "Proven",
                    "level": "L3",
                    "reason": "r",
                },
                {
                    "skill": "B",
                    "status": "Implied",
                    "level": "L2",
                    "reason": "r",
                },
                {
                    "skill": "C",
                    "status": "Claimed",
                    "level": "L1",
                    "reason": "r",
                },
                {
                    "skill": "D",
                    "status": "Unproven",
                    "level": "L0",
                    "reason": "r",
                },
            ]
        )

        # Collect the proof statuses returned by the function.
        statuses = {
            item["status"]
            for item in gaps
        }

        # Confirm that all required statuses are present.
        self.assertEqual(
            statuses,
            {
                "Proven",
                "Implied",
                "Claimed",
                "Unproven",
            },
        )

    def test_quality_has_seven_dimensions(self):
        # Create valid proof input for score testing.
        data = ProofInput(
            target_role="Data Analyst",
            claimed_skills=["SQL"],
            experience=(
                "I wrote SQL queries for a monthly sales report."
            ),
            project_description="Sales project",
            available_evidence=["Report"],
        )

        # Create sample information that would normally come from the LLM.
        extracted = {
            "actions": ["wrote queries"],
            "outcomes": [],
            "ownership": "High",
            "unsupported_claims": [],
        }

        # Map the claimed skill to its supporting information.
        mapped = map_skills(
            "Data Analyst",
            ["SQL"],
            data.experience,
            data.project_description,
            data.available_evidence,
        )

        # Calculate the evidence-quality scores.
        scores = calculate_evidence_quality(
            data,
            extracted,
            mapped,
        )

        # These seven quality dimensions must be present.
        expected_dimensions = [
            "relevance",
            "depth",
            "ownership",
            "outcome",
            "verifiability",
            "recency",
            "transferability",
        ]

        # Check each required dimension.
        for name in expected_dimensions:
            self.assertIn(name, scores)

    @patch(
        "src.llm_extraction.ollama.chat",
        return_value=FakeResponse(),
    )
    def test_unsupported_percentage(self, _mock):
        # Provide a percentage claim without supporting evidence.
        result = extract_evidence_with_llm(
            "Data Analyst",
            ["SQL"],
            "I used SQL for sales analysis.",
            "Sales project",
            [],
            "Improved conversion by 40%",
            [],
        )

        # Confirm that the unsupported 40% claim is reported.
        self.assertTrue(
            any(
                "40%" in claim
                for claim in result["unsupported_claims"]
            )
        )


# Run the tests when this file is executed directly.
if __name__ == "__main__":
    unittest.main()
