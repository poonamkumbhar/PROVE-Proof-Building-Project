"""Local RAG retrieval for curated role and skill standards.

RAG enriches role expectations and recommendations. It never decides whether
evidence is Proven, Implied, Claimed or Unproven, and it never calculates the
existing evidence-quality scores.
"""

import json
import os
import re
from pathlib import Path

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    import ollama
except ImportError:
    ollama = None


KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "data" / "role_skill_standards.json"
EMBEDDING_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")


def _tokens(text):
    return set(re.findall(r"[a-z0-9+#.]+", str(text).casefold()))


def _document_text(document):
    return " ".join([
        document["title"],
        " ".join(document.get("roles", [])),
        document["skill"],
        document["standard"],
        " ".join(document.get("expected_evidence", [])),
        " ".join(document.get("keywords", [])),
    ])


def _normalise(vectors):
    vectors = np.asarray(vectors, dtype="float32")
    faiss.normalize_L2(vectors)
    return vectors


class RoleSkillRetriever:
    """Create an in-memory FAISS index and rerank retrieved standards."""

    def __init__(self, knowledge_path=KNOWLEDGE_PATH, embedding_model=EMBEDDING_MODEL, embedder=None):
        if faiss is None:
            raise RuntimeError("faiss-cpu is not installed. Run: python -m pip install -r requirements.txt")
        if ollama is None and embedder is None:
            raise RuntimeError("The ollama Python package is not installed.")

        self.embedding_model = embedding_model
        self.embedder = embedder or self._ollama_embed
        with open(knowledge_path, encoding="utf-8") as file:
            self.documents = json.load(file)

        document_vectors = self.embedder([_document_text(item) for item in self.documents])
        self.index = faiss.IndexFlatIP(document_vectors.shape[1])
        self.index.add(document_vectors)

    def _ollama_embed(self, texts):
        response = ollama.embed(model=self.embedding_model, input=texts)
        values = response.get("embeddings") if isinstance(response, dict) else response.embeddings
        if not values:
            raise ValueError("Ollama returned no embeddings.")
        return _normalise(values)

    def retrieve(self, query, target_role, claimed_skills, candidate_k=8, top_k=4):
        query_vector = self.embedder([query])
        candidate_k = min(candidate_k, len(self.documents))
        similarities, indices = self.index.search(query_vector, candidate_k)

        role = target_role.casefold().strip()
        claimed = {item.casefold().strip() for item in claimed_skills}
        query_tokens = _tokens(query)
        results = []

        for semantic_score, index in zip(similarities[0], indices[0]):
            document = self.documents[int(index)]
            document_tokens = _tokens(_document_text(document))
            overlap = len(query_tokens & document_tokens) / max(1, len(query_tokens))
            role_match = max(
                (1.0 if role == item.casefold() else 0.6 if role in item.casefold() or item.casefold() in role else 0.0)
                for item in document.get("roles", [""])
            )
            skill_match = 1.0 if document["skill"].casefold() in claimed else 0.0
            rerank_score = 0.65 * float(semantic_score) + 0.15 * overlap + 0.12 * role_match + 0.08 * skill_match

            results.append({
                "source_id": document["id"],
                "title": document["title"],
                "skill": document["skill"],
                "standard": document["standard"],
                "expected_evidence": document.get("expected_evidence", []),
                "semantic_score": round(float(semantic_score), 4),
                "rerank_score": round(rerank_score, 4),
                "role_match": round(role_match, 2),
                "claimed_skill_match": bool(skill_match),
            })

        return sorted(results, key=lambda item: item["rerank_score"], reverse=True)[:top_k]


_RETRIEVER = None


def retrieve_role_skill_context(data):
    """Retrieve standards and fail safely if local RAG is unavailable."""
    global _RETRIEVER
    query = " ".join([
        data.target_role,
        data.target_domain,
        " ".join(data.claimed_skills),
        data.experience,
        data.project_description,
    ])
    try:
        if _RETRIEVER is None:
            _RETRIEVER = RoleSkillRetriever()
        sources = _RETRIEVER.retrieve(query, data.target_role, data.claimed_skills)
        return {
            "status": "success",
            "embedding_model": EMBEDDING_MODEL,
            "retrieval": "FAISS cosine similarity",
            "reranking": "semantic + token overlap + role match + skill match",
            "sources": sources,
        }
    except Exception as error:
        return {
            "status": "fallback",
            "embedding_model": EMBEDDING_MODEL,
            "retrieval": "unavailable",
            "reranking": "not run",
            "sources": [],
            "message": str(error),
        }
