# RAG, Hallucination Controls and Evaluation

## Where hallucinations can occur

| Risk point | Example | Control used |
| --- | --- | --- |
| Gemma extraction | Invented tool, action or outcome | Temperature 0, schema-constrained JSON, Pydantic validation and deterministic replacement of evidence/skills |
| Numeric impact | Treating an unsupported 40% improvement as verified | Unsupported-percentage guardrail and impact-evidence check |
| Skill mapping | Treating a claimed skill as demonstrated | Existing Python keyword/alias rules decide Proven, Implied, Claimed or Unproven |
| RAG retrieval | Retrieving an unrelated role standard | FAISS candidate search followed by role, skill and token-aware reranking |
| Recommendation | Suggestion not supported by a standard | Recommendation stores the retrieved `rag_source_id` and uses its expected-evidence list |
| Dependency failure | Missing FAISS/Ollama causing a broken app | RAG returns `fallback`; the original pipeline continues unchanged |

## RAG position in the pipeline

```text
Input
  -> Gemma extraction
  -> Pydantic validation
  -> RAG query
  -> nomic-embed-text embeddings
  -> FAISS retrieval
  -> deterministic reranking
  -> existing skill mapping
  -> existing seven-dimensional scoring
  -> proof gaps
  -> grounded recommendations
  -> proof plan
  -> final artifact and SQLite
```

RAG is an enrichment layer. It cannot promote evidence to Proven, create evidence, replace the four proof statuses or directly calculate quality scores.

## Retrieval and reranking

The local knowledge base is `data/role_skill_standards.json`. FAISS retrieves eight candidates with cosine similarity. The reranker returns the best four using:

- 65% semantic similarity
- 15% token overlap
- 12% target-role match
- 8% claimed-skill match

Every retrieved item includes a source ID, semantic score and rerank score for traceability.

## Evaluation

`data/rag_evaluation.json` contains 25 manually labelled queries. Each query has one or more expected source IDs. Run:

```powershell
ollama pull nomic-embed-text
python evaluate_rag.py
```

The script reports:

- **Top-1 Retrieval Accuracy (Hit Rate@1):** percentage of queries where the first result is correct.
- **Top-3 Retrieval Success Rate (Hit Rate@3):** percentage where a correct result appears in the first three.
- **Mean Reciprocal Rank (MRR):** how close the first correct result is to rank one.

Do not publish metric values until the script has been run locally. The automated tests prove implementation behavior; the labelled dataset measures retrieval quality.

## Evaluation limitations and next tests

- Expand beyond 25 queries.
- Add paraphrases, misspellings, implicit skills and irrelevant queries.
- Keep a held-out test set that is not used while tuning reranker weights.
- Compare FAISS-only ranking with FAISS plus reranking before claiming improvement.
- Manually rate recommendation relevance, groundedness, specificity and actionability from 1 to 5.
