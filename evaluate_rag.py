"""Offline evaluation for FAISS retrieval and reranking."""

import json
from pathlib import Path

from src.rag_retrieval import RoleSkillRetriever


EVALUATION_PATH = Path(__file__).resolve().parent / "data" / "rag_evaluation.json"


def evaluate_rag(evaluation_path=EVALUATION_PATH, top_k=3):
    with open(evaluation_path, encoding="utf-8") as file:
        examples = json.load(file)

    retriever = RoleSkillRetriever()
    top_1_correct = 0
    top_k_correct = 0
    reciprocal_rank_total = 0
    details = []

    for example in examples:
        results = retriever.retrieve(
            example["query"],
            example["target_role"],
            example["claimed_skills"],
            candidate_k=8,
            top_k=top_k,
        )
        retrieved_ids = [item["source_id"] for item in results]
        expected_ids = set(example["expected_source_ids"])
        top_1 = int(bool(retrieved_ids) and retrieved_ids[0] in expected_ids)
        top_k_hit = int(bool(expected_ids.intersection(retrieved_ids)))
        reciprocal_rank = next(
            (1 / rank for rank, source_id in enumerate(retrieved_ids, start=1) if source_id in expected_ids),
            0,
        )
        top_1_correct += top_1
        top_k_correct += top_k_hit
        reciprocal_rank_total += reciprocal_rank
        details.append({
            "id": example["id"],
            "expected": sorted(expected_ids),
            "retrieved": retrieved_ids,
            "top_1_correct": bool(top_1),
            "top_3_success": bool(top_k_hit),
            "reciprocal_rank": round(reciprocal_rank, 4),
        })

    total = len(examples)
    metrics = {
        "total_test_queries": total,
        "top_1_retrieval_accuracy": round(top_1_correct / total, 4),
        "top_3_retrieval_success_rate": round(top_k_correct / total, 4),
        "mean_reciprocal_rank": round(reciprocal_rank_total / total, 4),
    }
    return metrics, details


if __name__ == "__main__":
    metrics, details = evaluate_rag()
    print("\nRAG Evaluation Results")
    print(json.dumps(metrics, indent=2))
    print("\nQueries requiring improvement")
    weak_results = [item for item in details if not item["top_1_correct"]]
    print(json.dumps(weak_results, indent=2))
