# Biomedical machine learning and retrieval-augmented AI: methods-to-code corpus

**Author:** Paul Skeffington. **Prepared with OpenAI.** **Scoping update:** 2026-10-14. This is an independently authored, selective source register—not a systematic review, evidence of code reproduction, or a clinical validation study.

## Corpus and claim boundaries

The [28-source literature matrix](../references/BIOMEDICAL_AI_RAG_LITERATURE_2026-10-14.csv) separates peer-reviewed experimental papers, benchmarks, reviews, and reporting standards. The fields `bibliography_status`, `code_link_status`, `rights_review`, and `local_execution_status` distinguish bibliographic discovery from paper/code verification and actual replication. **The first 27 DOI/title/year/lead-author records were checked against primary publication pages or official scholarly indexes on 2026-10-14; the caret methods article was checked on 2026-10-15; this was metadata verification, not full-text study appraisal. None has been locally reproduced.** An upstream GitHub link does not establish license clearance, permitted model-weight use, package safety, or verification that a paper's results can be reproduced.

### Source-to-code decision table

| Domain | Source examples | Adaptable method (independently implement and test) | Validation boundary |
| --- | --- | --- | --- |
| Medical RAG | [Qasim et al. (2026)](https://doi.org/10.1038/s41598-026-74252-6); [MedRAG / MIRAGE (2024)](https://doi.org/10.18653/v1/2024.findings-acl.372) | Compare chunking, sparse/dense/hybrid retrievers, biomedical versus general embeddings, and reranking; log ranks, evidence snippets and answer citations | No patient-facing inference; source-document/query overlap audit; human grounding review |
| Multi-source / agentic RAG | [MultiMed-RAG (2026)](https://doi.org/10.1038/s41746-026-02962-2) | Benchmark graph, text and curated-knowledge routes as separate ablations; record handoffs, tool provenance, source dates and contradictions | External-source prompt injection, source validity, agent failures and unsafe-answer abstention |
| Biomedical retrieval | [MedCPT (2023)](https://doi.org/10.1093/bioinformatics/btad651) | Measure Recall@k, MRR, nDCG against independently judged relevance labels; add reranker only after baseline | Training-set and relevance-label contamination; search logs or licensed text may be restricted |
| Computational pathology | [UNI (2024)](https://doi.org/10.1038/s41591-024-02857-3); [Prov-GigaPath (2024)](https://doi.org/10.1038/s41586-024-07441-w) | Patient/slide/patch hierarchy and feature extractor registry; evaluate scanner and site shifts | Patch- and slide-level splits are not independent patient validation; check weights and imaging data licenses |
| Single-cell and spatial omics | [scGPT (2024)](https://doi.org/10.1038/s41592-024-02201-0); [Novae (2025)](https://doi.org/10.1038/s41592-025-02899-6) | Donor-aware splits, standardized gene identifiers, batch/slide graphs and out-of-distribution experiments | Cell-level pseudoreplication, donor overlap, graph-edge leakage and pretraining overlap |
| Clinical prediction and reporting | [TRIPOD+AI (2024)](https://doi.org/10.1136/bmj-2023-078378); [PROBAST+AI (2025)](https://doi.org/10.1136/bmj-2024-082505); [STARD-AI (2025)](https://doi.org/10.1038/s41591-025-03953-8) | Map study design to the appropriate reporting and bias-appraisal tool, not every checklist indiscriminately | Reporting completeness is not clinical utility, regulatory approval or low risk of bias |

## Minimal benchmark contract (candidate implementation)

1. **Scope and provenance:** define intended user, biomedical question type, permitted corpus, index date, document version, source DOI/URL, license, and access tier. Restrict content to synthetic or genuinely authorized open corpora in CI.
2. **Split by knowledge provenance:** partition clinical questions by source article, patient, institution and time where relevant; record contamination and paraphrase overlap. Freeze a held-out test set before selecting prompts, embeddings, chunk size or top-k.
3. **Baselines:** compare no-retrieval response, lexical (BM25), dense retrieval, hybrid retrieval and optional reranker using the same questions, corpus snapshot, compute budget and generation settings. Record number of retrieved documents and chunk lengths.
4. **Retrieval evidence:** retain query ID, source-document ID, document version, chunk ID, rank, score, source location, retrieval timestamp and gold relevance label (where legitimately annotated). Assess Recall@k, MRR, nDCG@k and evidence coverage; report uncertainty across questions and documents.
5. **Generation evidence:** preserve model ID, exact version/weights rights, system/developer/user prompt templates, context-window and generation parameters. Score answer correctness, evidence-grounding, citation precision, unsupported assertions, refusal/abstention and answer stability with blinded domain reviewers when appropriate.
6. **Clinical safety:** explicitly challenge incorrect premises, outdated guidance, conflicting documents, incomplete evidence, prompt-injection content, rare cases and sensitive information. Document escalation and human review, not automatic diagnosis or treatment recommendations.
7. **Statistical inference:** preregister primary endpoints and meaningful improvement; use paired per-question analyses/intervals with source-cluster bootstrap or other dependence-aware methods; stratify across specialties and question difficulty.
8. **Artifact release:** retain code SHA, permitted corpus/index manifest, frozen questions, hashed split IDs, environment lock, model IDs, reference results, tests, review logs and rights decisions. Keep restricted records/embeddings/weights outside public repositories; assess whether embeddings can disclose source information.

### Suggested benchmark interface (specification only)

```text
rag-evaluate --config configs/synthetic-rag.yaml --out artifacts/rag
  ingestion: source_manifest.json
  splits: frozen_question_ids + document_family_ids
  retrieval: {bm25, dense, hybrid, reranked}
  generation: {no_rag, rag}
  metrics: {recall_at_k, mrr, ndcg_at_k, citation_precision,
            evidence_coverage, groundedness, abstention, harmful_error}
  releases: {RESEARCH_ONLY, REVIEW_REQUIRED, BLOCKED}
```

This interface remains a **future expanded evaluation design contract**. The executable single-method `research-template rag-demo` uses a smaller, retrieval-only standard-library BM25 experiment; there is not yet a multi-retriever or generator-based `rag-evaluate` command.

## Minimum negative controls for future implementations

- A test set containing paraphrases of indexed training questions must fail contamination policy.
- A synthetic document with malicious embedded instructions must never override the caller's system constraints.
- An absent-answer query must exercise abstention rather than fabricated citation.
- A retrieved passage with a mismatched source ID or stale version must fail provenance validation.
- Disjoint patient/site/slide/donor invariants must fail on overlapping identifiers.
- Citation presentation must point to a document passage that actually supports the generated claim.
- Model weights or datasets with unchecked redistribution rights must remain blocked.

## Selection of reporting frameworks

Use **TRIPOD+AI / PROBAST+AI** for clinical prediction-model reporting/appraisal, **STARD-AI** for diagnostic accuracy, and **TRIPOD-LLM / applicable LLM-specific guidance** for relevant language-model studies. Check each source's intended scope. No checklist can replace clinician evaluation, protected-data authorization, external validation or deployment-specific risk assessment.

## Executable G2: synthetic lexical retrieval baseline

A dependency-free BM25 reference evaluator is available in
[src/research_template/retrieval_eval.py](../src/research_template/retrieval_eval.py).
It is original educational code, built from standard mathematical definitions,
not copied from MedRAG, MedCPT, or publisher supplements. This run requires only
Python 3.11+ and **does not download publications, clinical data, embeddings,
model weights, or call an LLM**.

~~~bash
research-template rag-demo \
  --out artifacts/rag/synthetic_retrieval.json --top-k 2
pytest -q tests/test_retrieval_eval.py tests/test_biomedical_literature_corpus.py
~~~

The five documents and six questions are fabricated. Two development
questions and four held-out questions represent **different document source
families**, which the implementation asserts have zero overlap. Three
holdout questions have hand-labeled relevance, while the fourth has
**no relevant source in the corpus**. It reports per-question rankings,
rank scores, Hit@k, Recall@k, MRR@k, nDCG@k, and a separate
no-answer/empty-retrieval rate. Every denominator and configuration is
recorded, together with a SHA-256 of the synthetic fixture and an
explicitly **BLOCKED** scientific release state.

**Important interpretation:** The no-answer/empty-retrieval metric is not an
LLM refusal test. Retrieval success is not evidence of correct medical
generation, valid citations, harmless advice, clinical accuracy, or external
transportability. The fixture was designed to make the expected lexical
rankings obvious; a perfect synthetic score does not demonstrate superiority
over BM25, MedCPT, MedRAG, graph retrieval, or other models.

The tests reject duplicate identifiers, mismatched relevance labels,
unknown documents, overlapping held-out source families, invalid
configurations, and missing evaluation partitions. Prompt-like text
inserted into a synthetic document is treated only as inert indexable
text; **this is not a full adversarial prompt-injection test** because no
generator or tool-using agent is present.

### G3 expansion conditions

Build a separate, opt-in adapter for genuinely licensed corpora only after
document access/retention and PHI/security checks. Additional retrieval
variants (BM25, dense, hybrid, reranker), answer generation, citation
support, clinician-rated safety and confidence intervals require **their
own** baseline configurations, independent relevance annotations,
negative controls, versioned parameters and reviewer approval. Keep
sample/donor/patient/site IDs out of logs and public artifacts. Do not
treat untested upstream code links as permission to redistribute code or
weights.

## Next gates

- **G0 (metadata complete):** All 28 DOI/title/year/lead-author records checked across 2026-10-14 and 2026-10-15; full-text methods extraction and version-specific source appraisal still pending.
- **G1 (links complete, rights pending):** All 13 public repository URLs resolve; exact revisions, code and model-weight licenses still require separate review. Do not vendor upstream code without permission.
- **G2 (implemented, CI pending):** Synthetic positive/negative relevance labels, deterministic BM25 baseline, source-family split tests and CLI have been added; CI must pass before the gate closes.
- **G3:** Add repeatable evaluation harness, uncertainty estimates, expert-grounding rubric, prompt-injection regression tests and drift/retrieval observability.
- **G4:** Require independent scientific and legal/IRB review for any actual biomedical data, clinical claims or clinical deployment.

**Current disposition:** Bibliography extension only. **Not reproduced, not clinically validated, not approved for medical use.**

### Classical R machine learning and caret

The [caret research workflow](CARET_RESEARCH_WORKFLOW.md) adds a sourced, optional R classification path using a grouped holdout, `caret::train()`, `caret::groupKFold()`, fold-local preprocessing and carefully labeled `caret::confusionMatrix()` results. This supervised-model workflow is distinct from retrieval-augmented generation; the Kuhn (2008) methods source is included in this broader biomedical ML register as `BML-011`. A running synthetic example does not reproduce or validate a published clinical model.
